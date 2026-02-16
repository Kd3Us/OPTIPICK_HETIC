"""
Point d'entrée principal du système OptiPick.
"""

from src.loader import load_all_data
from src.models import Robot, Human, Cart
from src.allocation import GreedyAllocation, print_allocation_summary
from src.routing import RouteOptimizer, print_route_summary


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
    
    # Affichage des statistiques
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
    
    # ALLOCATION
    print("-" * 70)
    print("🎯 ALLOCATION DES COMMANDES")
    print("-" * 70)
    
    allocator = GreedyAllocation(warehouse)
    result = allocator.allocate(agents, orders)
    
    print_allocation_summary(result, agents)
    
    # OPTIMISATION DES TOURNÉES (TSP)
    print("\n" + "-" * 70)
    print("🗺️  OPTIMISATION DES TOURNÉES (TSP)")
    print("-" * 70)
    print("Calcul des routes optimales avec OR-Tools...")
    
    optimizer = RouteOptimizer(warehouse)
    routes = optimizer.optimize_all_routes(agents)
    
    print_route_summary(routes)
    
    # Sauvegarder les résultats
    save_results(result, routes)
    
    print("\n✅ Jour 3 terminé : Optimisation TSP")
    print("=" * 70)


def save_results(allocation_result: dict, routes: list):
    """Sauvegarde les résultats dans results/"""
    import json
    from pathlib import Path
    
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Sauvegarder l'allocation
    with open(results_dir / 'allocation_results.json', 'w', encoding='utf-8') as f:
        json.dump(allocation_result, f, indent=2, ensure_ascii=False)
    
    # Sauvegarder les routes (convertir les Location en dict)
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
    
    # Calculer et sauvegarder les métriques
    metrics = {
        'allocation': {
            'total_orders': allocation_result['total_orders'],
            'assigned_orders': allocation_result['assigned_orders'],
            'failed_orders': allocation_result['failed_orders'],
            'success_rate': allocation_result['assigned_orders'] / allocation_result['total_orders'] * 100
        },
        'routing': {
            'total_distance': sum(r['total_distance'] for r in routes),
            'total_time_minutes': sum(r['total_time_minutes'] for r in routes),
            'total_cost_euros': sum(r['total_cost_euros'] for r in routes),
            'agents_used': len(routes)
        }
    }
    
    with open(results_dir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans {results_dir}/")


if __name__ == "__main__":
    main()