import json
import numpy as np

def calculate_total_distance(all_routes):
    """
    Calcule la distance totale parcourue par tous les agents.
    
    Args:
        all_routes (dict): {agent_id: list of routes}, chaque route = dict avec 'distance'
    
    Returns:
        float: distance totale
    """
    total_distance = 0
    for agent_routes in all_routes.values():
        for route in agent_routes:
            total_distance += route.get("distance", 0)
    return total_distance


def calculate_total_time(all_routes):
    """
    Calcule le temps total (makespan) pour toutes les routes.
    
    Args:
        all_routes (dict): {agent_id: list of routes}, chaque route = dict avec 'time'
    
    Returns:
        float: temps max parmi tous les agents
    """
    max_time = 0
    for agent_routes in all_routes.values():
        agent_time = sum(route.get("time", 0) for route in agent_routes)
        if agent_time > max_time:
            max_time = agent_time
    return max_time


def calculate_total_cost(agents_usage_time):
    """
    Calcule le coût total selon le temps d'utilisation des agents et leur coût horaire.
    
    Args:
        agents_usage_time (dict): {agent_id: {"time": float, "hourly_cost": float}}
    
    Returns:
        float: coût total
    """
    total_cost = 0
    for info in agents_usage_time.values():
        total_cost += info.get("time", 0) * info.get("hourly_cost", 0)
    return total_cost


def calculate_agent_utilization(agents, routes, total_time):
    """
    Calcule le pourcentage d'utilisation de chaque agent.
    
    Args:
        agents (list): liste d'agents avec 'id'
        routes (dict): {agent_id: list of routes}, chaque route = dict avec 'time'
        total_time (float): durée totale de référence
    
    Returns:
        dict: {agent_id: % utilisation}
    """
    utilization = {}
    for agent in agents:
        agent_id = agent["id"]
        active_time = sum(route.get("time", 0) for route in routes.get(agent_id, []))
        utilization[agent_id] = round((active_time / total_time) * 100, 2)
    return utilization


def calculate_load_balance_stddev(agents_times):
    """
    Calcule l'écart-type des temps des agents (équilibre de charge).
    
    Args:
        agents_times (list or array): temps utilisés par chaque agent
    
    Returns:
        float: écart-type
    """
    return float(np.std(agents_times))


# --- Export JSON ---
def export_allocation_results(allocation, filepath="results/allocation_results.json"):
    """Sauvegarde allocation en JSON."""
    with open(filepath, "w") as f:
        json.dump(allocation, f, indent=4)


def export_routes(routes, filepath="results/routes.json"):
    """Sauvegarde routes en JSON."""
    with open(filepath, "w") as f:
        json.dump(routes, f, indent=4)


def export_metrics(metrics_dict, filepath="results/metrics.json"):
    """Sauvegarde dictionnaire de métriques en JSON."""
    with open(filepath, "w") as f:
        json.dump(metrics_dict, f, indent=4)

