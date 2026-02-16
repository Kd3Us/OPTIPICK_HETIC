"""
Fonctions utilitaires pour OptiPick.
"""

from typing import List
from .models import Location, Agent, Order


def calculate_total_distance(locations: List[Location], start: Location = None) -> float:
    """
    Calcule la distance totale d'un parcours.
    
    Args:
        locations: Liste d'emplacements à visiter
        start: Point de départ (optionnel)
        
    Returns:
        Distance totale
    """
    if not locations:
        return 0.0
    
    total = 0.0
    current = start if start else locations[0]
    
    for loc in locations:
        total += current.distance_to(loc)
        current = loc
    
    # Retour au point de départ si fourni
    if start:
        total += current.distance_to(start)
    
    return total


def calculate_agent_cost(agent: Agent, time_minutes: float) -> float:
    """
    Calcule le coût d'utilisation d'un agent.
    
    Args:
        agent: Agent
        time_minutes: Temps d'utilisation en minutes
        
    Returns:
        Coût en euros
    """
    time_hours = time_minutes / 60
    return agent.cost_per_hour * time_hours


def estimate_order_distance(order: Order, entry_point: Location) -> float:
    """
    Estime la distance pour préparer une commande.
    
    Args:
        order: Commande
        entry_point: Point d'entrée de l'entrepôt
        
    Returns:
        Distance estimée
    """
    locations = order.get_unique_locations()
    return calculate_total_distance(locations, entry_point)