"""
Point d'entrée principal du système OptiPick.
"""

from src.loader import load_all_data
from src.models import Robot, Human, Cart
from src.allocation import GreedyAllocation, print_allocation_summary


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
    
    print("\n✅ Jour 2 terminé : Allocation avec contraintes")
    print("=" * 70)


if __name__ == "__main__":
    main()