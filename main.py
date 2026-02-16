"""
Point d'entrée principal du système OptiPick - VERSION LEAD ONLY.

Ce fichier fonctionne uniquement avec les modules du Lead.
Les collaborateurs devront implémenter leurs parties.
"""

from src.loader import load_all_data
from src.models import Robot, Human, Cart

# TODO Collaborateur 1: Importer constraints et allocation
# from src.constraints import ConstraintChecker
# from src.allocation import GreedyAllocation, print_allocation_summary

# TODO Collaborateur 2: Importer visualization
# from src.visualization import generate_all_visualizations


def main():
    """Fonction principale."""
    print("=" * 70)
    print(" " * 15 + "OPTIPICK - Système de Gestion d'Entrepôt")
    print(" " * 20 + "VERSION LEAD - JOUR 1 SEULEMENT")
    print("=" * 70)
    print()
    
    # ========================================================================
    # CHARGEMENT DES DONNÉES (Lead - Jour 1)
    # ========================================================================
    
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
    
    # ========================================================================
    # AFFICHAGE DES STATISTIQUES (Lead - Jour 1)
    # ========================================================================
    
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
    
    # ========================================================================
    # AFFICHAGE DES ZONES (Lead - Jour 1)
    # ========================================================================
    
    print("-" * 70)
    print("🗺️  ZONES DE L'ENTREPÔT")
    print("-" * 70)
    for zone_id, zone in warehouse.zones.items():
        restrictions = ', '.join(zone.restrictions) if zone.restrictions else 'Aucune'
        print(f"Zone {zone_id} ({zone.name}) - Type: {zone.type}")
        print(f"  Emplacements: {len(zone.coords)}, Restrictions: {restrictions}")
    print()
    
    # ========================================================================
    # AFFICHAGE DES PRODUITS (Lead - Jour 1)
    # ========================================================================
    
    print("-" * 70)
    print("📦 PRODUITS (Échantillon - 5 premiers)")
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
    
    # ========================================================================
    # AFFICHAGE DES AGENTS (Lead - Jour 1)
    # ========================================================================
    
    print("-" * 70)
    print("🤖 AGENTS DISPONIBLES")
    print("-" * 70)
    for agent in agents:
        print(f"{agent.id} ({agent.type})")
        print(f"  Capacité: {agent.capacity_weight}kg / {agent.capacity_volume}dm³")
        print(f"  Vitesse: {agent.speed}m/s")
        print(f"  Coût: {agent.cost_per_hour}€/h")
        if agent.restrictions:
            print(f"  Restrictions: {agent.restrictions}")
        print()
    
    # ========================================================================
    # AFFICHAGE DES COMMANDES (Lead - Jour 1)
    # ========================================================================
    
    print("-" * 70)
    print("🛒 COMMANDES")
    print("-" * 70)
    for order in orders:
        print(f"{order.id} - Priorité: {order.priority}")
        print(f"  Reçue: {order.received_time}, Deadline: {order.deadline} "
              f"({order.time_to_deadline()} min)")
        print(f"  Items: {len(order.items)}")
        print(f"  Poids total: {order.total_weight:.2f}kg")
        print(f"  Volume total: {order.total_volume:.2f}dm³")
        print(f"  Emplacements uniques: {len(order.get_unique_locations())}")
        
        # Afficher les produits de la commande
        print(f"  Produits:")
        for item in order.items:
            if item.product:
                print(f"    - {item.quantity}× {item.product.name} ({item.product.id})")
        print()
    
    # ========================================================================
    # CALCUL DE DISTANCES (Lead - Jour 1)
    # ========================================================================
    
    print("-" * 70)
    print("📏 CALCULS DE DISTANCES")
    print("-" * 70)
    
    # Distance de l'entrée à chaque zone
    print("Distances de l'entrée aux zones:")
    zone_distances = {}
    for zone_id, zone in warehouse.zones.items():
        if zone.coords:
            # Prendre le premier emplacement de la zone
            first_loc = zone.coords[0]
            distance = warehouse.entry_point.distance_to(first_loc)
            zone_distances[zone_id] = distance
            print(f"  Zone {zone_id} ({zone.name}): {distance}m")
    print()
    
    # Distance moyenne pour chaque commande
    print("Estimation de distance par commande (simple):")
    for order in orders[:5]:  # Afficher 5 premières
        total_distance = 0
        for location in order.get_unique_locations():
            total_distance += warehouse.entry_point.distance_to(location)
        
        # Aller-retour simple
        total_distance *= 2
        
        print(f"  {order.id}: ~{total_distance}m (aller-retour simple)")
    print()
    
    # ========================================================================
    # TODO: PROCHAINES ÉTAPES
    # ========================================================================
    
    print("=" * 70)
    print("✅ JOUR 1 TERMINÉ - Chargement et Modélisation OK")
    print("=" * 70)
    print()
    print("📋 PROCHAINES ÉTAPES:")
    print()
    print("🔸 COLLABORATEUR 1 doit implémenter:")
    print("   - src/constraints.py (vérification des contraintes)")
    print("   - src/allocation.py (allocation gloutonne)")
    print("   - tests/test_constraints.py")
    print("   - tests/test_allocation.py")
    print("   - tests/test_utils.py")
    print()
    print("🔸 COLLABORATEUR 2 doit implémenter:")
    print("   - src/visualization.py (graphiques et cartes)")
    print("   - tests/test_models.py")
    print("   - notebooks/exploration.ipynb")
    print("   - notebooks/analysis.ipynb")
    print("   - docs/rapport.md")
    print()
    print("🔸 LEAD (vous) a déjà implémenté:")
    print("   ✅ src/models.py")
    print("   ✅ src/loader.py")
    print("   ✅ src/routing.py")
    print("   ✅ src/optimization.py")
    print("   ✅ src/storage.py")
    print("   ✅ src/utils.py")
    print("   ✅ main.py")
    print()
    print("=" * 70)


def test_basic_functionality():
    """Tests de base pour valider le chargement."""
    print("\n" + "=" * 70)
    print("🧪 TESTS DE BASE")
    print("=" * 70)
    
    from src.models import Location
    from src.utils import calculate_total_distance
    
    # Test 1: Distance de Manhattan
    loc1 = Location(0, 0)
    loc2 = Location(3, 4)
    distance = loc1.distance_to(loc2)
    assert distance == 7, f"Distance devrait être 7, obtenu {distance}"
    print("✅ Test distance de Manhattan: OK")
    
    # Test 2: Calcul de distance totale
    locations = [Location(0, 0), Location(3, 0), Location(3, 4)]
    total = calculate_total_distance(locations)
    print(f"✅ Test distance totale: {total}m")
    
    # Test 3: Chargement des données
    try:
        data = load_all_data('data')
        assert len(data['products']) > 0, "Aucun produit chargé"
        assert len(data['agents']) > 0, "Aucun agent chargé"
        assert len(data['orders']) > 0, "Aucune commande chargée"
        print("✅ Test chargement données: OK")
    except Exception as e:
        print(f"❌ Test chargement données: ÉCHEC - {e}")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
    
    # Tests optionnels
    print("\n")
    response = input("Voulez-vous exécuter les tests de base ? (o/n): ")
    if response.lower() == 'o':
        test_basic_functionality()