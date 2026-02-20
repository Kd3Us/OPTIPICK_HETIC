"""
Route optimisation using OR-Tools TSP solver.
Also provides a lightweight Nearest-Neighbour fallback and a
CollisionDetector to identify and resolve agent path conflicts.

Aisle-aware routing: agents navigate to the aisle pick point adjacent to
each rack location, rather than cutting through rack cells directly.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from .models import Agent, Order, Location, Warehouse
from .utils import calculate_total_distance


class RouteOptimizer:

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse

    def _pick_point(self, location: Location) -> Location:
        if self.warehouse.aisles:
            return self.warehouse.get_pick_point(location)
        return location

    def create_distance_matrix(self, locations: List[Location]) -> np.ndarray:
        n = len(locations)
        matrix = np.zeros((n, n), dtype=int)
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = locations[i].distance_to(locations[j])
        return matrix

    def solve_tsp(self, locations: List[Location], start_index: int = 0) -> Tuple[List[int], float]:
        if len(locations) <= 1:
            return [0], 0.0
        if len(locations) == 2:
            return [0, 1, 0], locations[0].distance_to(locations[1]) * 2

        distance_matrix = self.create_distance_matrix(locations)
        manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, start_index)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            return distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        search_params = pywrapcp.DefaultRoutingSearchParameters()
        search_params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_params.time_limit.seconds = 2

        solution = routing.SolveWithParameters(search_params)

        if solution:
            route = []
            total_distance = 0
            index = routing.Start(0)
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                prev_index = index
                index = solution.Value(routing.NextVar(index))
                total_distance += routing.GetArcCostForVehicle(prev_index, index, 0)
            route.append(manager.IndexToNode(index))
            return route, float(total_distance)

        route = list(range(len(locations))) + [start_index]
        total_distance = calculate_total_distance(locations, locations[start_index])
        return route, total_distance

    def optimize_agent_route(self, agent: Agent, orders: List[Order]) -> Dict:
        if not orders:
            return {
                'agent_id': agent.id,
                'agent_type': agent.type,
                'orders': [],
                'route': [],
                'total_distance': 0,
                'travel_time_minutes': 0,
                'picking_time_minutes': 0,
                'total_time_minutes': 0,
                'total_cost_euros': 0,
                'locations_visited': 0
            }

        all_pick_points = [self.warehouse.entry_point]
        pick_point_to_products: Dict[Location, List[Dict]] = {
            self.warehouse.entry_point: []
        }

        for order in orders:
            for item in order.items:
                if not item.product:
                    continue
                pick_pt = self._pick_point(item.product.location)
                if pick_pt not in all_pick_points:
                    all_pick_points.append(pick_pt)
                    pick_point_to_products[pick_pt] = []
                pick_point_to_products[pick_pt].append({
                    'order_id': order.id,
                    'product': item.product,
                    'quantity': item.quantity
                })

        optimal_route, total_distance = self.solve_tsp(all_pick_points, start_index=0)

        detailed_route = []
        cumulative = 0
        for idx in optimal_route:
            location = all_pick_points[idx]
            detailed_route.append({
                'location': location,
                'products': pick_point_to_products.get(location, []),
                'cumulative_distance': cumulative
            })
            if len(detailed_route) < len(optimal_route):
                next_loc = all_pick_points[optimal_route[len(detailed_route)]]
                cumulative += location.distance_to(next_loc)

        total_items = sum(len(order.items) for order in orders)
        picking_time = total_items * 0.5
        travel_time = (total_distance / agent.speed) / 60
        total_time = travel_time + picking_time
        total_cost = (total_time / 60) * agent.cost_per_hour

        return {
            'agent_id': agent.id,
            'agent_type': agent.type,
            'orders': [o.id for o in orders],
            'route': detailed_route,
            'total_distance': total_distance,
            'travel_time_minutes': travel_time,
            'picking_time_minutes': picking_time,
            'total_time_minutes': total_time,
            'total_cost_euros': total_cost,
            'locations_visited': len(all_pick_points) - 1
        }

    def optimize_all_routes(self, agents: List[Agent]) -> List[Dict]:
        results = []
        for agent in agents:
            if agent.assigned_orders:
                results.append(self.optimize_agent_route(agent, agent.assigned_orders))
        return results


class NearestNeighborTSP:

    @staticmethod
    def solve(locations: List[Location], start: Location) -> Tuple[List[Location], float]:
        if not locations:
            return [start], 0.0

        unvisited = set(locations)
        route = [start]
        current = start
        total_distance = 0

        while unvisited:
            nearest = min(unvisited, key=lambda loc: current.distance_to(loc))
            total_distance += current.distance_to(nearest)
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest

        total_distance += current.distance_to(start)
        route.append(start)

        return route, total_distance


class CollisionDetector:
    """
    Detects and resolves spatial conflicts between agent routes.

    Strategy:
    - Build a timeline of (agent, time_step, location) events.
    - Flag any two agents occupying the same cell at the same time.
    - Resolve conflicts by adding a small departure delay to the
      lower-priority agent (robots yield to humans/carts).
    """

    def __init__(self, time_step: float = 1.0):
        self.time_step = time_step

    def _build_timeline(self, route_info: Dict) -> List[Tuple[float, Location]]:
        route = route_info.get('route', [])
        if not route:
            return []

        timeline = []
        current_time = 0.0
        travel_time_total = max(route_info.get('travel_time_minutes', 1), 0.001)
        total_distance = max(route_info.get('total_distance', 1), 0.001)
        speed_cells_per_min = total_distance / travel_time_total

        for i in range(len(route) - 1):
            loc_a = route[i]['location']
            loc_b = route[i + 1]['location']
            dist = loc_a.distance_to(loc_b)

            n_products = len(route[i]['products'])
            dwell = n_products * 0.5
            timeline.append((current_time, loc_a))
            current_time += dwell

            travel_time = dist / max(speed_cells_per_min, 0.001)
            steps = max(int(travel_time / self.time_step), 1)
            for s in range(1, steps + 1):
                frac = s / steps
                interp_x = round(loc_a.x + frac * (loc_b.x - loc_a.x))
                interp_y = round(loc_a.y + frac * (loc_b.y - loc_a.y))
                timeline.append((current_time + frac * travel_time, Location(interp_x, interp_y)))
            current_time += travel_time

        if route:
            timeline.append((current_time, route[-1]['location']))

        return timeline

    def detect_collisions(self, route_results: List[Dict]) -> List[Dict]:
        """
        Detect all space-time conflicts between agents.
        Returns a list of conflict dicts: agent_a, agent_b, time_minutes, location.
        """
        timelines: Dict[str, List[Tuple[float, Location]]] = {}
        for r in route_results:
            timelines[r['agent_id']] = self._build_timeline(r)

        conflicts = []
        agent_ids = list(timelines.keys())

        for i in range(len(agent_ids)):
            for j in range(i + 1, len(agent_ids)):
                a_id = agent_ids[i]
                b_id = agent_ids[j]
                tl_a = timelines[a_id]
                tl_b = timelines[b_id]

                a_positions: Dict[int, Location] = {
                    int(t / self.time_step): loc for t, loc in tl_a
                }
                for t, loc in tl_b:
                    bucket = int(t / self.time_step)
                    if bucket in a_positions and a_positions[bucket] == loc:
                        conflicts.append({
                            'agent_a': a_id,
                            'agent_b': b_id,
                            'time_minutes': round(t, 2),
                            'location': loc
                        })
                        break

        return conflicts

    def resolve_with_delays(self, route_results: List[Dict],
                            delay_minutes: float = 2.0) -> List[Dict]:
        """
        Resolve conflicts by delaying lower-priority agents.
        Priority: human > cart > robot.
        """
        conflicts = self.detect_collisions(route_results)
        if not conflicts:
            return route_results

        priority = {'human': 0, 'cart': 1, 'robot': 2}
        agents_to_delay = set()

        for conflict in conflicts:
            type_a = next((r['agent_type'] for r in route_results
                           if r['agent_id'] == conflict['agent_a']), 'robot')
            type_b = next((r['agent_type'] for r in route_results
                           if r['agent_id'] == conflict['agent_b']), 'robot')

            if priority.get(type_a, 99) >= priority.get(type_b, 99):
                agents_to_delay.add(conflict['agent_a'])
            else:
                agents_to_delay.add(conflict['agent_b'])

        updated = []
        for r in route_results:
            if r['agent_id'] in agents_to_delay:
                r = dict(r)
                r['travel_time_minutes'] = r.get('travel_time_minutes', 0) + delay_minutes
                r['total_time_minutes'] = r.get('total_time_minutes', 0) + delay_minutes
                cost_per_min = (r.get('total_cost_euros', 0) /
                                max(r.get('total_time_minutes', 1) - delay_minutes, 0.001) / 60)
                r['total_cost_euros'] = cost_per_min * r['total_time_minutes'] * 60
            updated.append(r)

        return updated

    def print_collision_report(self, conflicts: List[Dict]):
        print("\n" + "=" * 60)
        print("COLLISION REPORT")
        print("=" * 60)
        if not conflicts:
            print("  Aucun conflit detecte.")
        else:
            print(f"  {len(conflicts)} conflit(s) detecte(s) :")
            for c in conflicts:
                print(f"  - {c['agent_a']} vs {c['agent_b']} "
                      f"@ t={c['time_minutes']}min "
                      f"en {c['location']}")
        print("=" * 60)


def print_route_summary(routes: List[Dict]):
    print("\n" + "=" * 60)
    print("ROUTE SUMMARY")
    print("=" * 60)

    total_distance = 0.0
    total_time = 0.0
    total_cost = 0.0

    for info in routes:
        print(f"\nAgent {info['agent_id']} ({info['agent_type']})")
        print(f"  Orders          : {', '.join(info['orders'])}")
        print(f"  Stops           : {info['locations_visited']}")
        print(f"  Distance        : {info['total_distance']:.1f}m")
        print(f"  Travel time     : {info['travel_time_minutes']:.1f}min")
        print(f"  Picking time    : {info['picking_time_minutes']:.1f}min")
        print(f"  Total time      : {info['total_time_minutes']:.1f}min")
        print(f"  Cost            : {info['total_cost_euros']:.2f}EUR")

        route_preview = " -> ".join(
            str(step['location']) for step in info['route'][:5]
        )
        if len(info['route']) > 5:
            route_preview += " -> ..."
        print(f"  Route           : {route_preview}")

        total_distance += info['total_distance']
        total_time += info['total_time_minutes']
        total_cost += info['total_cost_euros']

    print("\n" + "-" * 60)
    print(f"Total distance  : {total_distance:.1f}m")
    print(f"Total time      : {total_time:.1f}min  ({total_time / 60:.1f}h)")
    print(f"Total cost      : {total_cost:.2f}EUR")
    print("=" * 60)