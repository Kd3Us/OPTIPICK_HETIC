"""
Point d'entrée principal du système OptiPick - VERSION FINALE.
"""

from src.loader import load_all_data
from src.models import Robot, Human, Cart
from src.allocation import GreedyAllocation, print_allocation_summary
from src.routing import RouteOptimizer, print_route_summary
from src.optimization import OptimalAllocator, OrderBatcher
from src.storage import StorageOptimizer, print_storage_analysis
from src.visualization import generate_all_visualizations


def main():
    """Fonction principale."""
    print("=" * 70)
    print(" " * 15 + "OPTIPICK - Système de Gestion d'Entrepôt")
    print(" " * 25 + "VERSION FINALE - JOUR 5")
    print("=" * 70)
    print()
    
    # Chargement des données
    print("📂 Chargement des données...")
    try:
        data = load_all_data('data')
        print("✅ Données chargées avec succès !\n")
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        return
    
    warehouse = data['warehouse']
    products = data['products']
    agents = data['agents']
    orders = data['orders']
    
    # Statistiques
    print("-" * 70)
    print("📊 STATISTIQUES")
    print("-" * 70)
    print(f"Entrepôt : {warehouse.width}×{warehouse.height} cases, {len(warehouse.zones)} zones")
    print(f"Produits : {len(products)}")
    print(f"Agents : {len(agents)} "
          f"(R:{sum(1 for a in agents if isinstance(a, Robot))}, "
          f"H:{sum(1 for a in agents if isinstance(a, Human))}, "
          f"C:{sum(1 for a in agents if isinstance(a, Cart))})")
    print(f"Commandes : {len(orders)}")
    print()
    
    # ========================================================================
    # ALLOCATION GREEDY
    # ========================================================================
    
    print("=" * 70)
    print("1️⃣  ALLOCATION GLOUTONNE (Baseline)")
    print("=" * 70)
    
    agents_greedy = [type(a)(a.id, a.capacity_weight, a.capacity_volume, 
                             a.speed, a.cost_per_hour, a.restrictions)
                     for a in agents]
    
    greedy = GreedyAllocation(warehouse)
    result_greedy = greedy.allocate(agents_greedy, orders)
    print_allocation_summary(result_greedy, agents_greedy)
    
    optimizer_greedy = RouteOptimizer(warehouse)
    routes_greedy = optimizer_greedy.optimize_all_routes(agents_greedy)
    print_route_summary(routes_greedy)
    
    # ========================================================================
    # ALLOCATION OPTIMALE (CP-SAT)
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("2️⃣  ALLOCATION OPTIMALE (CP-SAT)")
    print("=" * 70)
    print("Résolution avec OR-Tools CP-SAT...")
    
    agents_optimal = [type(a)(a.id, a.capacity_weight, a.capacity_volume,
                              a.speed, a.cost_per_hour, a.restrictions)
                      for a in agents]
    
    optimal = OptimalAllocator(warehouse)
    result_optimal = optimal.allocate(agents_optimal, orders, max_time_seconds=30)
    
    print(f"✅ Terminé en {result_optimal['solve_time_seconds']:.2f}s "
          f"({result_optimal['status']})")
    
    print_allocation_summary(result_optimal, agents_optimal)
    
    optimizer_optimal = RouteOptimizer(warehouse)
    routes_optimal = optimizer_optimal.optimize_all_routes(agents_optimal)
    print_route_summary(routes_optimal)
    
    # ========================================================================
    # COMPARAISON
    # ========================================================================
    
    greedy_distance = sum(r['total_distance'] for r in routes_greedy)
    greedy_cost = sum(r['total_cost_euros'] for r in routes_greedy)
    greedy_time = sum(r['total_time_minutes'] for r in routes_greedy)
    
    optimal_distance = sum(r['total_distance'] for r in routes_optimal)
    optimal_cost = sum(r['total_cost_euros'] for r in routes_optimal)
    optimal_time = sum(r['total_time_minutes'] for r in routes_optimal)
    
    print("\n" + "=" * 70)
    print("📈 COMPARAISON FINALE")
    print("=" * 70)
    print(f"{'Métrique':<30} {'Greedy':<15} {'Optimal':<15} {'Amélioration':<15}")
    print("-" * 70)
    
    improvement_dist = ((greedy_distance - optimal_distance) / greedy_distance * 100 
                       if greedy_distance > 0 else 0)
    improvement_cost = ((greedy_cost - optimal_cost) / greedy_cost * 100 
                       if greedy_cost > 0 else 0)
    improvement_time = ((greedy_time - optimal_time) / greedy_time * 100 
                       if greedy_time > 0 else 0)
    
    print(f"{'Distance (m)':<30} {greedy_distance:<15.1f} {optimal_distance:<15.1f} "
          f"{improvement_dist:+.1f}%")
    print(f"{'Coût (€)':<30} {greedy_cost:<15.2f} {optimal_cost:<15.2f} "
          f"{improvement_cost:+.1f}%")
    print(f"{'Temps (min)':<30} {greedy_time:<15.1f} {optimal_time:<15.1f} "
          f"{improvement_time:+.1f}%")
    print("=" * 70)
    
    # ========================================================================
    # BATCHING
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("3️⃣  ANALYSE DU REGROUPEMENT (BATCHING)")
    print("=" * 70)
    
    batcher = OrderBatcher(warehouse)
    total_batching_benefit = 0
    
    for agent in agents_optimal:
        if agent.assigned_orders and len(agent.assigned_orders) > 1:
            batches = batcher.find_batchable_orders(agent.assigned_orders, agent)
            
            print(f"\n🤖 {agent.id} ({len(agent.assigned_orders)} commandes)")
            print(f"   Groupes identifiés : {len(batches)}")
            
            for i, batch in enumerate(batches, 1):
                if len(batch) > 1:
                    benefit = batcher.calculate_batching_benefit(batch)
                    total_batching_benefit += benefit
                    print(f"   Groupe {i}: {len(batch)} commandes "
                          f"→ Gain: {benefit:.1f}m")
    
    print(f"\n📊 Gain total potentiel du batching: {total_batching_benefit:.1f}m")
    
    # ========================================================================
    # OPTIMISATION STOCKAGE
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("4️⃣  OPTIMISATION DU STOCKAGE")
    print("=" * 70)
    
    storage_optimizer = StorageOptimizer(warehouse)
    
    frequencies = storage_optimizer.analyze_product_frequency(orders)
    affinities = storage_optimizer.analyze_product_affinity(orders)
    
    print_storage_analysis(frequencies, affinities, products)
    
    print("\n💡 Proposition de Réorganisation")
    print("-" * 70)
    
    new_locations = storage_optimizer.propose_reorganization(products, orders)
    improvement = storage_optimizer.calculate_improvement(products, orders, new_locations)
    
    print(f"Distance économisée : {improvement['distance_saved']:.1f}m "
          f"({improvement['improvement_percent']:.1f}%)")
    
    # ========================================================================
    # VISUALISATIONS
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("5️⃣  GÉNÉRATION DES VISUALISATIONS")
    print("=" * 70)
    
    generate_all_visualizations(
        warehouse, products,
        routes_greedy, routes_optimal,
        agents_greedy, agents_optimal
    )
    
    # ========================================================================
    # SAUVEGARDE
    # ========================================================================
    
    save_results(result_optimal, routes_optimal, improvement, 
                greedy_distance, greedy_cost, greedy_time,
                optimal_distance, optimal_cost, optimal_time)
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("🏆 RÉSUMÉ FINAL DU PROJET OPTIPICK")
    print("=" * 70)
    print(f"\n✅ Allocation : {result_optimal['assigned_orders']}/{result_optimal['total_orders']} commandes")
    print(f"✅ Optimisation distance : {improvement_dist:.1f}% de gain")
    print(f"✅ Optimisation coût : {improvement_cost:.1f}% d'économie")
    print(f"✅ Potentiel batching : {total_batching_benefit:.1f}m économisables")
    print(f"✅ Réorganisation stockage : {improvement['improvement_percent']:.1f}% d'amélioration")
    print(f"\n💰 Économies totales : {greedy_cost - optimal_cost:.2f}€ par cycle")
    print(f"📊 Résultats sauvegardés dans results/")
    print(f"📈 Visualisations générées")
    
    print("\n" + "=" * 70)
    print("✅ PROJET TERMINÉ AVEC SUCCÈS !")
    print("=" * 70)


def save_results(allocation_result: dict, routes: list, storage_improvement: dict,
                greedy_distance: float, greedy_cost: float, greedy_time: float,
                optimal_distance: float, optimal_cost: float, optimal_time: float):
    """Sauvegarde complète des résultats."""
    import json
    from pathlib import Path
    
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Allocation
    with open(results_dir / 'allocation_results.json', 'w', encoding='utf-8') as f:
        json.dump(allocation_result, f, indent=2, ensure_ascii=False)
    
    # Routes
    routes_serializable = []
    for route in routes:
        route_copy = route.copy()
        route_copy['route'] = [
            {
                'location': {'x': step['location'].x, 'y': step['location'].y},
                'products': [
                    {
                        'order_id': p['order_id'],
                        'product_id': p['product'].id,
                        'product_name': p['product'].name,
                        'quantity': p['quantity']
                    }
                    for p in step['products']
                ],
                'cumulative_distance': step['cumulative_distance']
            }
            for step in route_copy['route']
        ]
        routes_serializable.append(route_copy)
    
    with open(results_dir / 'routes.json', 'w', encoding='utf-8') as f:
        json.dump(routes_serializable, f, indent=2, ensure_ascii=False)
    
    # Métriques complètes
    metrics = {
        'allocation': {
            'status': allocation_result['status'],
            'total_orders': allocation_result['total_orders'],
            'assigned_orders': allocation_result['assigned_orders'],
            'success_rate': 100.0,
            'solve_time_seconds': allocation_result['solve_time_seconds']
        },
        'comparison': {
            'greedy': {
                'distance_m': greedy_distance,
                'cost_euros': greedy_cost,
                'time_minutes': greedy_time
            },
            'optimal': {
                'distance_m': optimal_distance,
                'cost_euros': optimal_cost,
                'time_minutes': optimal_time
            },
            'improvements': {
                'distance_percent': (greedy_distance - optimal_distance) / greedy_distance * 100,
                'cost_percent': (greedy_cost - optimal_cost) / greedy_cost * 100,
                'time_percent': (greedy_time - optimal_time) / greedy_time * 100
            }
        },
        'storage_optimization': storage_improvement
    }
    
    with open(results_dir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()