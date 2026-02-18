import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import metrics, visualization

# --- Données factices pour les métriques ---
all_routes = {
    "robot_1": [{"distance": 10, "time": 5}, {"distance": 15, "time": 7}],
    "humain_1": [{"distance": 8, "time": 4}, {"distance": 12, "time": 6}],
    "chariot_1": [{"distance": 20, "time": 10}]
}

agents_usage_time = {
    "robot_1": {"time": 12, "hourly_cost": 15},
    "humain_1": {"time": 10, "hourly_cost": 12},
    "chariot_1": {"time": 10, "hourly_cost": 20}
}

agents = [
    {"id": "robot_1"},
    {"id": "humain_1"},
    {"id": "chariot_1"}
]

# --- Tests métriques ---
total_distance = metrics.calculate_total_distance(all_routes)
total_time = metrics.calculate_total_time(all_routes)
total_cost = metrics.calculate_total_cost(agents_usage_time)
utilization = metrics.calculate_agent_utilization(agents, all_routes, total_time)
load_stddev = metrics.calculate_load_balance_stddev([12, 10, 10])

print("Distance totale:", total_distance)
print("Temps total:", total_time)
print("Coût total:", total_cost)
print("Utilisation des agents (%):", utilization)
print("Écart-type des temps:", load_stddev)

# --- Visualisation ---
warehouse = {"width": 10, "height": 8}
products = [
    {"x": 1, "y": 2, "zone": "A", "name": "Produit 1"},
    {"x": 3, "y": 5, "zone": "B", "name": "Produit 2"},
    {"x": 7, "y": 1, "zone": "C", "name": "Produit 3"},
]

visualization.plot_warehouse(warehouse, products)
visualization.plot_agent_utilization(utilization)

# --- Comparaison distances ---
scenarios_distance = {
    "Glouton": 120,
    "TSP": 95,
    "CP-SAT": 80,
    "Batching": 90
}
visualization.plot_distance_comparison(scenarios_distance)

# --- Breakdown coûts ---
agents_costs = {
    "robot_1": 200,
    "humain_1": 150,
    "chariot_1": 100
}
visualization.plot_cost_breakdown(agents_costs)

# --- Comparaison temps ---
scenarios_time = {
    "Glouton": 45,
    "TSP": 38,
    "CP-SAT": 30,
    "Batching": 35
}
visualization.plot_time_comparison(scenarios_time)

