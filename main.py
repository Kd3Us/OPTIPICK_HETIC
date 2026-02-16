"""
Point d'entrée principal du système OptiPick.
"""

from src.loader import load_all_data
from src.models import Robot, Human, Cart
from src.allocation import GreedyAllocation, print_allocation_summary
from src.routing import RouteOptimizer, print_route_summary
from src.optimization import OptimalAllocator, OrderBatcher
from src.storage import StorageOptimizer, print_storage_analysis


def main():
    """Fonction principale."""
    print("=" * 70)
    print(" " * 20 + "OPTIPICK - Système de Gestion d'Entrepôt")
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
    print(f"Entrepôt : {warehouse.width}×{warehouse.height} cases")
    print(f"Produits : {len(products)}")
    print(f"Agents : {len(agents)} "
          f"(R:{sum(1 for a in agents if isinstance(a, Robot))}, "
          f"H:{sum(1 for a in agents if isinstance(a, Human))}, "
          f"C:{sum(1 for a in agents if isinstance(a, Cart))})")
    print(f"Commandes : {len(orders)}")
    print()
    
    # ========================================================================
    # COMPARAISON : GREEDY vs OPTIMAL
    # ========================================================================
    
    print("-" * 70)
    print("⚖️  COMPARAISON DES STRATÉGIES D'ALLOCATION")
    print("-" * 70)
    
    # Stratégie 1 : Greedy
    print("\n1️⃣  Allocation Gloutonne (Greedy)")
    print("-" * 70)
    
    agents_copy = [type(a)(a.id, a.capacity_weight, a.capacity_volume, 
                           a.speed, a.cost_per_hour, a.restrictions)
                   for a in agents]
    
    greedy = GreedyAllocation(warehouse)
    result_greedy = greedy.allocate(agents_copy, orders)
    print_allocation_summary(result_greedy, agents_copy)
    
    optimizer_greedy = RouteOptimizer(warehouse)
    routes_greedy = optimizer_greedy.optimize_all_routes(agents_copy)
    
    greedy_distance = sum(r['total_distance'] for r in routes_greedy)
    greedy_cost = sum(r['total_cost_euros'] for r in routes_greedy)
    
    print(f"\n📊 Résumé Greedy:")
    print(f"  Distance totale: {greedy_distance:.1f}m")
    print(f"  Coût total: {greedy_cost:.2f}€")
    
    # Stratégie 2 : Optimal (CP-SAT)
    print("\n" + "=" * 70)
    print("2️⃣  Allocation Optimale (CP-SAT)")
    print("-" * 70)
    print("Résolution avec OR-Tools CP-SAT (max 30s)...")
    
    agents_copy2 = [type(a)(a.id, a.capacity_weight, a.capacity_volume,
                            a.speed, a.cost_per_hour, a.restrictions)
                    for a in agents]
    
    optimal = OptimalAllocator(warehouse)
    result_optimal = optimal.allocate(agents_copy2, orders, max_time_seconds=30)
    
    print(f"✅ Résolution terminée en {result_optimal['solve_time_seconds']:.2f}s")
    print(f"   Statut: {result_optimal['status']}")
    
    print_allocation_summary(result_optimal, agents_copy2)
    
    optimizer_optimal = RouteOptimizer(warehouse)
    routes_optimal = optimizer_optimal.optimize_all_routes(agents_copy2)
    
    optimal_distance = sum(r['total_distance'] for r in routes_optimal)
    optimal_cost = sum(r['total_cost_euros'] for r in routes_optimal)
    
    print(f"\n📊 Résumé Optimal:")
    print(f"  Distance totale: {optimal_distance:.1f}m")
    print(f"  Coût total: {optimal_cost:.2f}€")
    
    # Comparaison
    print("\n" + "=" * 70)
    print("📈 COMPARAISON FINALE")
    print("=" * 70)
    print(f"{'Métrique':<30} {'Greedy':<15} {'Optimal':<15} {'Gain':<15}")
    print("-" * 70)
    print(f"{'Distance (m)':<30} {greedy_distance:<15.1f} {optimal_distance:<15.1f} "
          f"{greedy_distance - optimal_distance:+.1f}m")
    print(f"{'Coût (€)':<30} {greedy_cost:<15.2f} {optimal_cost:<15.2f} "
          f"{greedy_cost - optimal_cost:+.2f}€")
    
    improvement_distance = ((greedy_distance - optimal_distance) / greedy_distance * 100 
                           if greedy_distance > 0 else 0)
    improvement_cost = ((greedy_cost - optimal_cost) / greedy_cost * 100 
                       if greedy_cost > 0 else 0)
    
    print(f"{'Amélioration':<30} {improvement_distance:<15.1f}% {improvement_cost:<15.1f}%")
    print("=" * 70)
    
    # ========================================================================
    # BATCHING
    # ========================================================================
    
    print("\n" + "-" * 70)
    print("📦 ANALYSE DU REGROUPEMENT DE COMMANDES (BATCHING)")
    print("-" * 70)
    
    batcher = OrderBatcher(warehouse)
    
    for agent in agents_copy2:
        if agent.assigned_orders and len(agent.assigned_orders) > 1:
            batches = batcher.find_batchable_orders(agent.assigned_orders, agent)
            
            print(f"\n🤖 Agent {agent.id}:")
            print(f"  Commandes: {len(agent.assigned_orders)}")
            print(f"  Groupes possibles: {len(batches)}")
            
            for i, batch in enumerate(batches, 1):
                if len(batch) > 1:
                    benefit = batcher.calculate_batching_benefit(batch)
                    print(f"  Groupe {i}: {[o.id for o in batch]} "
                          f"(gain estimé: {benefit:.1f}m)")
    
    # ========================================================================
    # OPTIMISATION DU STOCKAGE
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("🗃️  OPTIMISATION DU STOCKAGE")
    print("=" * 70)
    
    storage_optimizer = StorageOptimizer(warehouse)
    
    # Analyser les patterns
    frequencies = storage_optimizer.analyze_product_frequency(orders)
    affinities = storage_optimizer.analyze_product_affinity(orders)
    
    print_storage_analysis(frequencies, affinities, products)
    
    # Proposer réorganisation
    print("\n" + "-" * 70)
    print("💡 PROPOSITION DE RÉORGANISATION")
    print("-" * 70)
    
    new_locations = storage_optimizer.propose_reorganization(products, orders)
    improvement = storage_optimizer.calculate_improvement(products, orders, new_locations)
    
    print(f"\n📊 Simulation avant/après réorganisation:")
    print(f"  Distance totale actuelle: {improvement['current_total_distance']:.1f}m")
    print(f"  Distance totale nouvelle: {improvement['new_total_distance']:.1f}m")
    print(f"  Distance économisée: {improvement['distance_saved']:.1f}m "
          f"({improvement['improvement_percent']:.1f}%)")
    
    # Sauvegarder les résultats
    save_results(result_optimal, routes_optimal, improvement)
    
    print("\n✅ Jour 4 terminé : Optimisation globale & Stockage")
    print("=" * 70)


def save_results(allocation_result: dict, routes: list, storage_improvement: dict):
    """Sauvegarde les résultats dans results/"""
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
    
    # Métriques
    metrics = {
        'allocation': {
            'status': allocation_result['status'],
            'total_orders': allocation_result['total_orders'],
            'assigned_orders': allocation_result['assigned_orders'],
            'failed_orders': allocation_result['failed_orders'],
            'success_rate': allocation_result['assigned_orders'] / allocation_result['total_orders'] * 100,
            'solve_time_seconds': allocation_result['solve_time_seconds']
        },
        'routing': {
            'total_distance': sum(r['total_distance'] for r in routes),
            'total_time_minutes': sum(r['total_time_minutes'] for r in routes),
            'total_cost_euros': sum(r['total_cost_euros'] for r in routes),
            'agents_used': len(routes)
        },
        'storage_optimization': storage_improvement
    }
    
    with open(results_dir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans {results_dir}/")


if __name__ == "__main__":
    main()