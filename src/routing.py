"""
Module d'optimisation des tournées (TSP - Traveling Salesman Problem).

Utilise OR-Tools pour calculer le chemin optimal de visite des emplacements.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from .models import Agent, Order, Location, Warehouse
from .utils import calculate_total_distance


class RouteOptimizer:
    """Optimise les tournées des agents avec OR-Tools."""
    
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
    
    def create_distance_matrix(self, locations: List[Location]) -> np.ndarray:
        """
        Crée une matrice de distances entre toutes les positions.
        
        Args:
            locations: Liste de positions
            
        Returns:
            Matrice numpy de distances (Manhattan)
        """
        n = len(locations)
        matrix = np.zeros((n, n), dtype=int)
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = locations[i].distance_to(locations[j])
        
        return matrix
    
    def solve_tsp(self, locations: List[Location], start_index: int = 0) -> Tuple[List[int], float]:
        """
        Résout le TSP pour une liste de positions.
        
        Args:
            locations: Liste de positions à visiter
            start_index: Index de la position de départ
            
        Returns:
            (ordre de visite, distance totale)
        """
        if len(locations) <= 1:
            return [0], 0.0
        
        if len(locations) == 2:
            return [0, 1, 0], locations[0].distance_to(locations[1]) * 2
        
        # Créer la matrice de distances
        distance_matrix = self.create_distance_matrix(locations)
        
        # Créer le gestionnaire de données
        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix),
            1,  # Nombre de véhicules (1 agent)
            start_index  # Dépôt (point de départ)
        )
        
        # Créer le modèle de routage
        routing = pywrapcp.RoutingModel(manager)
        
        # Fonction de coût (distance)
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Paramètres de recherche
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 2
        
        # Résoudre
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            # Extraire la route
            route = []
            total_distance = 0
            index = routing.Start(0)
            
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route.append(node)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
            
            # Ajouter le dernier nœud
            route.append(manager.IndexToNode(index))
            
            return route, float(total_distance)
        else:
            # Pas de solution trouvée, utiliser l'ordre d'origine
            route = list(range(len(locations))) + [start_index]
            total_distance = calculate_total_distance(locations, locations[start_index])
            return route, total_distance
    
    def optimize_agent_route(self, agent: Agent, orders: List[Order]) -> Dict:
        """
        Optimise la tournée d'un agent pour un ensemble de commandes.
        
        Args:
            agent: Agent dont on optimise la tournée
            orders: Commandes assignées à cet agent
            
        Returns:
            Dictionnaire avec la route optimisée et les métriques
        """
        if not orders:
            return {
                'agent_id': agent.id,
                'orders': [],
                'route': [],
                'total_distance': 0,
                'total_time': 0,
                'total_cost': 0
            }
        
        # Collecter tous les emplacements uniques
        all_locations = [self.warehouse.entry_point]  # Commencer à l'entrée
        location_to_products = {self.warehouse.entry_point: []}
        
        for order in orders:
            for location in order.get_unique_locations():
                if location not in all_locations:
                    all_locations.append(location)
                    location_to_products[location] = []
                
                # Associer les produits à leur emplacement
                for item in order.items:
                    if item.product and item.product.location == location:
                        location_to_products[location].append({
                            'order_id': order.id,
                            'product': item.product,
                            'quantity': item.quantity
                        })
        
        # Résoudre le TSP
        optimal_route, total_distance = self.solve_tsp(all_locations, start_index=0)
        
        # Créer la route détaillée
        detailed_route = []
        for idx in optimal_route:
            location = all_locations[idx]
            products_at_location = location_to_products.get(location, [])
            
            detailed_route.append({
                'location': location,
                'products': products_at_location,
                'cumulative_distance': 0  # Sera calculé ci-dessous
            })
        
        # Calculer les distances cumulatives
        cumulative = 0
        for i in range(len(detailed_route)):
            detailed_route[i]['cumulative_distance'] = cumulative
            if i < len(detailed_route) - 1:
                cumulative += detailed_route[i]['location'].distance_to(
                    detailed_route[i + 1]['location']
                )
        
        # Calculer les métriques
        total_items = sum(len(order.items) for order in orders)
        picking_time = total_items * 0.5  # 30 secondes par item
        travel_time = (total_distance / agent.speed) / 60  # minutes
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
            'locations_visited': len(all_locations) - 1  # -1 pour exclure l'entrée
        }
    
    def optimize_all_routes(self, agents: List[Agent]) -> List[Dict]:
        """
        Optimise les tournées de tous les agents.
        
        Args:
            agents: Liste des agents avec commandes assignées
            
        Returns:
            Liste des résultats d'optimisation
        """
        results = []
        
        for agent in agents:
            if agent.assigned_orders:
                result = self.optimize_agent_route(agent, agent.assigned_orders)
                results.append(result)
        
        return results


class NearestNeighborTSP:
    """
    Heuristique du plus proche voisin pour le TSP.
    Alternative plus simple à OR-Tools.
    """
    
    @staticmethod
    def solve(locations: List[Location], start: Location) -> Tuple[List[Location], float]:
        """
        Résout le TSP avec l'heuristique du plus proche voisin.
        
        Args:
            locations: Emplacements à visiter
            start: Point de départ
            
        Returns:
            (route optimale, distance totale)
        """
        if not locations:
            return [start], 0.0
        
        unvisited = set(locations)
        route = [start]
        current = start
        total_distance = 0
        
        while unvisited:
            # Trouver le plus proche voisin non visité
            nearest = min(unvisited, key=lambda loc: current.distance_to(loc))
            distance = current.distance_to(nearest)
            
            route.append(nearest)
            total_distance += distance
            unvisited.remove(nearest)
            current = nearest
        
        # Retour au point de départ
        total_distance += current.distance_to(start)
        route.append(start)
        
        return route, total_distance


def print_route_summary(routes: List[Dict]):
    """Affiche un résumé des tournées optimisées."""
    
    print("\n" + "=" * 70)
    print(" " * 22 + "TOURNÉES OPTIMISÉES")
    print("=" * 70)
    
    total_distance = 0
    total_time = 0
    total_cost = 0
    
    for route_info in routes:
        agent_id = route_info['agent_id']
        agent_type = route_info['agent_type']
        
        print(f"\n🚀 Agent {agent_id} ({agent_type})")
        print(f"  Commandes : {', '.join(route_info['orders'])}")
        print(f"  Emplacements à visiter : {route_info['locations_visited']}")
        print(f"  Distance totale : {route_info['total_distance']:.1f}m")
        print(f"  Temps de trajet : {route_info['travel_time_minutes']:.1f}min")
        print(f"  Temps de ramassage : {route_info['picking_time_minutes']:.1f}min")
        print(f"  Temps total : {route_info['total_time_minutes']:.1f}min")
        print(f"  Coût : {route_info['total_cost_euros']:.2f}€")
        
        # Afficher la route (simplifié)
        print(f"  Route : ", end="")
        route_str = " → ".join([
            f"{step['location']}"
            for step in route_info['route'][:5]  # Afficher les 5 premiers
        ])
        if len(route_info['route']) > 5:
            route_str += " → ..."
        print(route_str)
        
        total_distance += route_info['total_distance']
        total_time += route_info['total_time_minutes']
        total_cost += route_info['total_cost_euros']
    
    print("\n" + "-" * 70)
    print("📊 TOTAUX")
    print("-" * 70)
    print(f"Distance totale : {total_distance:.1f}m")
    print(f"Temps total : {total_time:.1f}min ({total_time/60:.1f}h)")
    print(f"Coût total : {total_cost:.2f}€")
    print("=" * 70)