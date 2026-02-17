"""
Route optimisation using OR-Tools TSP solver.
Also provides a lightweight Nearest-Neighbour fallback.
"""

from typing import List, Dict, Tuple
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from .models import Agent, Order, Location, Warehouse
from .utils import calculate_total_distance


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

        # Fallback: original order
        route = list(range(len(locations))) + [start_index]
        total_distance = calculate_total_distance(locations, locations[start_index])
        return route, total_distance

    def optimize_agent_route(self, agent: Agent, orders: List[Order]) -> Dict:
        if not orders:
            return {
                'agent_id': agent.id,
                'orders': [],
                'route': [],
                'total_distance': 0,
                'total_time': 0,
                'total_cost': 0
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
                'cumulative_distance': 0
            })

        cumulative = 0
        for i in range(len(detailed_route)):
            detailed_route[i]['cumulative_distance'] = cumulative
            if i < len(detailed_route) - 1:
                cumulative += detailed_route[i]['location'].distance_to(
                    detailed_route[i + 1]['location']
                )

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
            'locations_visited': len(all_locations) - 1
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