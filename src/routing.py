"""
Route optimisation using OR-Tools TSP solver.
Also provides a lightweight Nearest-Neighbour fallback.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from .models import Agent, Order, Location, Warehouse
from .utils import calculate_total_distance

PICKING_TIME_PER_ITEM = 30  # seconds per product picked
START_STAGGER_SECONDS = 10  # délai de départ entre agents


class RouteOptimizer:

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse

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

        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix), 1, start_index
        )
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

    def _compute_timestamps(self, detailed_route: List[Dict], agent: Agent,
                            start_offset: float = 0.0) -> List[Dict]:
        current_time = start_offset

        for i, step in enumerate(detailed_route):
            if i == 0:
                step['arrival_time_seconds'] = round(start_offset, 2)
            else:
                prev_loc = detailed_route[i - 1]['location']
                distance = prev_loc.distance_to(step['location'])
                travel_time = distance / agent.speed
                current_time += travel_time
                step['arrival_time_seconds'] = round(current_time, 2)

            n_items = sum(p['quantity'] for p in step['products'])
            picking_duration = n_items * PICKING_TIME_PER_ITEM
            step['picking_duration_seconds'] = picking_duration
            step['departure_time_seconds'] = round(current_time + picking_duration, 2)
            step['is_picking'] = n_items > 0
            current_time += picking_duration

        return detailed_route

    def optimize_agent_route(self, agent: Agent, orders: List[Order],
                             start_offset: float = 0.0) -> Dict:
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

        all_locations = [self.warehouse.entry_point]
        location_to_products = {self.warehouse.entry_point: []}

        for order in orders:
            for location in order.get_unique_locations():
                if location not in all_locations:
                    all_locations.append(location)
                    location_to_products[location] = []
                for item in order.items:
                    if item.product and item.product.location == location:
                        location_to_products[location].append({
                            'order_id': order.id,
                            'product': item.product,
                            'quantity': item.quantity
                        })

        optimal_route, total_distance = self.solve_tsp(all_locations, start_index=0)

        detailed_route = []
        for idx in optimal_route:
            location = all_locations[idx]
            detailed_route.append({
                'location': location,
                'products': location_to_products.get(location, []),
                'cumulative_distance': 0,
                'arrival_time_seconds': 0.0,
                'departure_time_seconds': 0.0,
                'picking_duration_seconds': 0.0,
                'is_picking': False
            })

        cumulative = 0
        for i in range(len(detailed_route)):
            detailed_route[i]['cumulative_distance'] = cumulative
            if i < len(detailed_route) - 1:
                cumulative += detailed_route[i]['location'].distance_to(
                    detailed_route[i + 1]['location']
                )

        detailed_route = self._compute_timestamps(detailed_route, agent, start_offset)

        total_items = sum(len(order.items) for order in orders)
        picking_time = total_items * 0.5
        travel_time = (total_distance / agent.speed) / 60
        total_time = travel_time + picking_time + (start_offset / 60)
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
            'locations_visited': len(all_locations) - 1,
            'start_offset_seconds': start_offset
        }

    def optimize_all_routes(self, agents: List[Agent]) -> List[Dict]:
        """Optimise les routes avec départs échelonnés pour limiter les conflits."""
        results = []
        active_agents = [a for a in agents if a.assigned_orders]
        for idx, agent in enumerate(active_agents):
            offset = idx * START_STAGGER_SECONDS
            results.append(self.optimize_agent_route(agent, agent.assigned_orders,
                                                     start_offset=offset))
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


# ---------------------------------------------------------------------------
# Détection et résolution de collisions (Multi-Agent Path Finding simplifié)
# ---------------------------------------------------------------------------

class CollisionDetector:
    """
    Détecte et résout les conflits de position entre agents en mouvement.

    Règles :
      - Le point d'entrée (0,0) est une zone libre : pas de conflit possible.
      - Deux agents en picking au même rayon simultanément : acceptable.
      - Edge conflict uniquement entre deux agents tous les deux en mouvement.
      - Agent ayant terminé sa tournée : plus dans l'entrepôt.
    """

    def __init__(self, time_step: float = 1.0):
        self.time_step = time_step

    def _build_timeline(self, route_result: Dict) -> List[Tuple[float, float, Location, bool]]:
        return [
            (
                step['arrival_time_seconds'],
                step['departure_time_seconds'],
                step['location'],
                step.get('is_picking', False)
            )
            for step in route_result['route']
        ]

    def _finish_time(self, timeline: List) -> float:
        return timeline[-1][1] if timeline else 0.0

    def _state_at(self, timeline: List, finish: float,
                  t: float) -> Optional[Tuple[Location, bool]]:
        if t > finish:
            return None
        for i, (arrival, departure, loc, picking) in enumerate(timeline):
            if arrival <= t <= departure:
                return (loc, picking)
            if i + 1 < len(timeline):
                next_arrival = timeline[i + 1][0]
                if departure < t < next_arrival:
                    return (timeline[i + 1][2], False)
        return None

    def detect_collisions(self, route_results: List[Dict]) -> List[Dict]:
        if not route_results:
            return []

        entry = None
        for r in route_results:
            if r['route']:
                entry = r['route'][0]['location']
                break

        timelines = {}
        finish_times = {}
        for r in route_results:
            tl = self._build_timeline(r)
            timelines[r['agent_id']] = tl
            finish_times[r['agent_id']] = self._finish_time(tl)

        max_time = max(finish_times.values()) if finish_times else 0.0
        agent_ids = list(timelines.keys())
        conflicts = []

        # Vertex conflicts
        t = 0.0
        while t <= max_time:
            states = {
                aid: self._state_at(timelines[aid], finish_times[aid], t)
                for aid in agent_ids
            }
            for i, a1 in enumerate(agent_ids):
                for a2 in agent_ids[i + 1:]:
                    s1, s2 = states[a1], states[a2]
                    if s1 is None or s2 is None:
                        continue
                    loc1, picking1 = s1
                    loc2, picking2 = s2
                    if loc1 != loc2 or loc1 == entry:
                        continue
                    if picking1 and picking2:
                        continue  # picking simultané sur le même rayon : acceptable
                    conflicts.append({
                        'type': 'vertex',
                        'time': round(t, 1),
                        'agents': [a1, a2],
                        'location': loc1
                    })
            t += self.time_step

        # Edge conflicts — uniquement entre agents en mouvement
        t = 0.0
        while t + self.time_step <= max_time:
            t_next = t + self.time_step
            for i, a1 in enumerate(agent_ids):
                for a2 in agent_ids[i + 1:]:
                    s1_now  = self._state_at(timelines[a1], finish_times[a1], t)
                    s1_next = self._state_at(timelines[a1], finish_times[a1], t_next)
                    s2_now  = self._state_at(timelines[a2], finish_times[a2], t)
                    s2_next = self._state_at(timelines[a2], finish_times[a2], t_next)

                    if None in (s1_now, s1_next, s2_now, s2_next):
                        continue

                    l1_now, p1_now = s1_now
                    l1_next, _     = s1_next
                    l2_now, p2_now = s2_now
                    l2_next, _     = s2_next

                    if p1_now or p2_now:
                        continue  # agent immobile : pas de croisement possible

                    if l1_now == l2_next and l2_now == l1_next and l1_now != entry:
                        conflicts.append({
                            'type': 'edge',
                            'time': round(t, 1),
                            'agents': [a1, a2],
                            'location': None
                        })
            t += self.time_step

        # Dédoublonnage : un conflit par (type, agents, fenêtre de 5s)
        unique = []
        seen = set()
        for c in conflicts:
            key = (c['type'], tuple(sorted(c['agents'])), int(c['time'] / 5))
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return unique

    def resolve_with_delays(self, route_results: List[Dict]) -> List[Dict]:
        """
        Résolution itérative par délais.
        Si la résolution augmente le nombre de conflits, on abandonne et on
        garde la version avec le moins de conflits.
        """
        results_by_id = {r['agent_id']: r for r in route_results}
        delay = START_STAGGER_SECONDS
        max_iterations = 50

        initial_conflicts = self.detect_collisions(list(results_by_id.values()))
        best_count = len(initial_conflicts)
        best_state = {aid: {
            'route': [step.copy() for step in r['route']],
            'total_time_minutes': r['total_time_minutes']
        } for aid, r in results_by_id.items()}

        for _ in range(max_iterations):
            conflicts = self.detect_collisions(list(results_by_id.values()))
            vertex_conflicts = [c for c in conflicts if c['type'] == 'vertex']

            if not vertex_conflicts:
                break

            # Sauvegarder le meilleur état observé
            if len(conflicts) < best_count:
                best_count = len(conflicts)
                best_state = {aid: {
                    'route': [step.copy() for step in r['route']],
                    'total_time_minutes': r['total_time_minutes']
                } for aid, r in results_by_id.items()}

            conflict = vertex_conflicts[0]
            agent_to_delay = conflict['agents'][1]
            conflict_time = conflict['time']

            if agent_to_delay not in results_by_id:
                continue

            for step in results_by_id[agent_to_delay]['route']:
                if step['arrival_time_seconds'] >= conflict_time:
                    step['arrival_time_seconds']   = round(step['arrival_time_seconds'] + delay, 2)
                    step['departure_time_seconds'] = round(step['departure_time_seconds'] + delay, 2)

            route = results_by_id[agent_to_delay]['route']
            if route:
                results_by_id[agent_to_delay]['total_time_minutes'] = round(
                    route[-1]['departure_time_seconds'] / 60, 2
                )

        # Vérifier si la résolution a empiré les choses
        final_conflicts = self.detect_collisions(list(results_by_id.values()))
        if len(final_conflicts) > best_count:
            # Restaurer le meilleur état observé
            for aid, state in best_state.items():
                results_by_id[aid]['route'] = state['route']
                results_by_id[aid]['total_time_minutes'] = state['total_time_minutes']
            print(f"  Resolution abandonnee : retour au meilleur etat ({best_count} conflits)")

        return list(results_by_id.values())

    def print_collision_report(self, conflicts: List[Dict]):
        print("\n" + "=" * 60)
        print("COLLISION REPORT")
        print("=" * 60)

        if not conflicts:
            print("  Aucun conflit detecte.")
            print("=" * 60)
            return

        vertex_conflicts = [c for c in conflicts if c['type'] == 'vertex']
        edge_conflicts   = [c for c in conflicts if c['type'] == 'edge']

        print(f"  Conflits vertex : {len(vertex_conflicts)}")
        print(f"  Conflits arete  : {len(edge_conflicts)}")
        print()

        for c in conflicts[:20]:
            agents_str = " vs ".join(c['agents'])
            loc_str = str(c['location']) if c['location'] else "croisement"
            print(f"  [{c['type']:6s}]  t={c['time']:6.1f}s  {agents_str}  @{loc_str}")

        if len(conflicts) > 20:
            print(f"  ... et {len(conflicts) - 20} autres (non affiches)")

        print("=" * 60)


def print_route_summary(routes: List[Dict]):
    print("\n" + "=" * 60)
    print("ROUTE SUMMARY")
    print("=" * 60)

    total_distance = 0.0
    total_time = 0.0
    total_cost = 0.0

    for info in routes:
        offset = info.get('start_offset_seconds', 0)
        offset_str = f" (depart +{offset:.0f}s)" if offset > 0 else ""
        print(f"\nAgent {info['agent_id']} ({info['agent_type']}){offset_str}")
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