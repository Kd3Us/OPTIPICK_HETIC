"""
Point d'entrée principal du système OptiPick.
"""

from src.loader import load_all_data
from src.models import Robot, Human, Cart


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
    print(f"Zones : {len(warehouse.zones)}")
    print(f"Produits : {len(products)}")
    print(f"Agents : {len(agents)}")
    print(f"  - Robots : {sum(1 for a in agents if isinstance(a, Robot))}")
    print(f"  - Humains : {sum(1 for a in agents if isinstance(a, Human))}")
    print(f"  - Chariots : {sum(1 for a in agents if isinstance(a, Cart))}")
    print(f"Commandes : {len(orders)}")
    print()
    
    # Affichage des zones
    print("-" * 70)
    print("🗺️  ZONES DE L'ENTREPÔT")
    print("-" * 70)
    for zone_id, zone in warehouse.zones.items():
        restrictions = ', '.join(zone.restrictions) if zone.restrictions else 'Aucune'
        print(f"Zone {zone_id} ({zone.name}) - Type: {zone.type}")
        print(f"  Emplacements: {len(zone.coords)}, Restrictions: {restrictions}")
    print()
    
    # Affichage de quelques produits
    print("-" * 70)
    print("📦 PRODUITS (Échantillon)")
    print("-" * 70)
    for product in products[:5]:
        zone = warehouse.get_zone_at(product.location)
        print(f"{product.id}: {product.name}")
        print(f"  Catégorie: {product.category}, Poids: {product.weight}kg, "
              f"Volume: {product.volume}dm³")
        print(f"  Emplacement: {product.location} (Zone {zone})")
        print(f"  Fragile: {'Oui' if product.fragile else 'Non'}, "
              f"Fréquence: {product.frequency}")
        if product.incompatible_with:
            print(f"  Incompatible avec: {', '.join(product.incompatible_with[:3])}")
        print()
    
    # Affichage des commandes
    print("-" * 70)
    print("🛒 COMMANDES")
    print("-" * 70)
    for order in orders[:5]:
        print(f"{order.id} - Priorité: {order.priority}")
        print(f"  Reçue: {order.received_time}, Deadline: {order.deadline} "
              f"({order.time_to_deadline()} min)")
        print(f"  Items: {len(order.items)}, "
              f"Poids total: {order.total_weight:.2f}kg, "
              f"Volume total: {order.total_volume:.2f}dm³")
        print(f"  Emplacements uniques: {len(order.get_unique_locations())}")
        print()
    
    print("=" * 70)
    print("✅ Test de chargement terminé avec succès !")
    print("=" * 70)


if __name__ == "__main__":
    main()