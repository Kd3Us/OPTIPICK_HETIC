from pathlib import Path

from src.loader import load_all_data
from src.models import Robot, Human, Cart
from src.allocation import GreedyAllocation, print_allocation_summary
from src.optimization import OptimalAllocator
from src.routing import RouteOptimizer, CollisionDetector, print_route_summary
from src.storage import StorageOptimizer
from src.metrics import (
    build_metrics_from_route_results, export_allocation_results,
    export_routes, export_metrics, print_metrics_summary
)
from src.visualization import (
    create_dashboard, plot_agent_utilization, plot_distance_comparison,
    plot_cost_breakdown, plot_zone_traffic, plot_product_frequency
)

Path("results").mkdir(exist_ok=True)


def main():
    print("OptiPick - Optimisation de Tournees d'Entrepot\n")

    # chargement
    data = load_all_data('data')
    warehouse = data['warehouse']
    products  = data['products']
    agents    = data['agents']
    orders    = data['orders']

    robots = [a for a in agents if isinstance(a, Robot)]
    humans = [a for a in agents if isinstance(a, Human)]
    carts  = [a for a in agents if isinstance(a, Cart)]

    print(f"Entrepot {warehouse.width}x{warehouse.height} | "
          f"{len(products)} produits | "
          f"{len(robots)} robots, {len(humans)} humains, {len(carts)} chariots | "
          f"{len(orders)} commandes\n")

    # allocation gloutonne (baseline)
    print("--- Allocation gloutonne ---")
    greedy_result = GreedyAllocation(warehouse).allocate(agents, orders)
    print_allocation_summary(greedy_result, agents)

    greedy_total_dist = sum(
        warehouse.entry_point.distance_to(loc) * 2
        for a in agents
        for o in a.assigned_orders
        for loc in o.get_unique_locations()
    )
    export_allocation_results(greedy_result, "results/allocation_greedy.json")

    # allocation optimale CP-SAT
    print("\n--- Allocation CP-SAT ---")
    optimal_result = OptimalAllocator(warehouse).allocate(agents, orders, max_time_seconds=30)
    print(f"Statut: {optimal_result['status']} | "
          f"{optimal_result['assigned_orders']}/{optimal_result['total_orders']} commandes | "
          f"{optimal_result['solve_time_seconds']:.1f}s")
    export_allocation_results(optimal_result, "results/allocation_optimal.json")

    # optimisation des tournees TSP
    print("\n--- Tournees TSP ---")
    route_results = RouteOptimizer(warehouse).optimize_all_routes(agents)
    print_route_summary(route_results)
    optimal_total_dist = sum(r['total_distance'] for r in route_results)
    export_routes(route_results, "results/routes.json")

    # détection et résolution des collisions
    print("\n--- Collisions ---")
    detector = CollisionDetector(time_step=1.0)
    conflicts = detector.detect_collisions(route_results)
    detector.print_collision_report(conflicts)

    if conflicts:
        print("Résolution des conflits par délais...")
        route_results = detector.resolve_with_delays(route_results)
        conflicts_after = detector.detect_collisions(route_results)
        print(f"Conflits restants apres resolution : {len(conflicts_after)}")
        export_routes(route_results, "results/routes_resolved.json")

    # analyse du stockage
    print("\n--- Analyse du stockage ---")
    storage = StorageOptimizer(warehouse)
    frequencies  = storage.analyze_product_frequency(orders)
    zone_traffic = storage.analyze_zone_traffic(orders)
    new_locations = storage.propose_reorganization(products, orders)
    improvement  = storage.calculate_improvement(products, orders, new_locations)

    print(f"Distance avg actuelle  : {improvement['current_avg_distance']:.1f}m")
    print(f"Distance avg optimisee : {improvement['new_avg_distance']:.1f}m")
    print(f"Gain estime            : {improvement['improvement_percent']:.1f}%")

    # metriques
    print("\n--- Metriques ---")
    metrics = build_metrics_from_route_results(route_results)
    print_metrics_summary(metrics)
    export_metrics(metrics, "results/metrics.json")

    # visualisations
    print("\n--- Visualisations ---")
    wh_dict = {"width": warehouse.width, "height": warehouse.height}

    if metrics.get('per_agent'):
        total_t = metrics.get('makespan_minutes', 1) or 1
        util = {a: round(info['time_minutes'] / total_t * 100, 1)
                for a, info in metrics['per_agent'].items()}
        plot_agent_utilization(util, "results/agent_utilization.png")

    plot_distance_comparison(
        {"Glouton": round(greedy_total_dist, 1), "TSP+CP-SAT": round(optimal_total_dist, 1)},
        "results/distance_comparison.png"
    )

    if metrics.get('per_agent'):
        plot_cost_breakdown(
            {a: round(info['cost_euros'], 2) for a, info in metrics['per_agent'].items()},
            "results/cost_breakdown.png"
        )

    if zone_traffic:
        plot_zone_traffic(zone_traffic, "results/zone_traffic.png")

    products_dict = {p.id: p for p in products}
    freq_names = {products_dict[pid].name: count for pid, count in frequencies.items()
                  if pid in products_dict}
    plot_product_frequency(freq_names, top_n=10, save_path="results/product_frequency.png")

    create_dashboard(
        allocation=optimal_result,
        route_results=route_results,
        metrics=metrics,
        warehouse=wh_dict,
        save_path="results/dashboard.png"
    )
    print("Graphiques exportes dans results/")

    # resume
    print(f"\n{'='*50}")
    print(f"Commandes traitees : {optimal_result['assigned_orders']}/{optimal_result['total_orders']}")
    print(f"Distance totale    : {metrics.get('total_distance_m', 0):.1f} m")
    print(f"Cout total         : {metrics.get('total_cost_euros', 0):.2f} EUR")
    print(f"Makespan           : {metrics.get('makespan_minutes', 0):.1f} min")
    print(f"Gain stockage      : {improvement['improvement_percent']:.1f}%")
    print(f"Conflits detectes  : {len(conflicts)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()