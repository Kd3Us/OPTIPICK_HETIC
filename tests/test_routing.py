"""
Tests unitaires pour le module routing.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Location, Warehouse
from src.routing import RouteOptimizer, NearestNeighborTSP


def test_distance_matrix():
    """Test de création de matrice de distances."""
    locations = [
        Location(0, 0),
        Location(3, 0),
        Location(3, 4),
        Location(0, 4)
    ]
    
    warehouse = Warehouse(10, 8, Location(0, 0))
    optimizer = RouteOptimizer(warehouse)
    
    matrix = optimizer.create_distance_matrix(locations)
    
    # Vérifier quelques distances
    assert matrix[0][1] == 3  # (0,0) → (3,0) = 3
    assert matrix[0][2] == 7  # (0,0) → (3,4) = 3+4 = 7
    assert matrix[1][2] == 4  # (3,0) → (3,4) = 4
    
    print("✅ Test matrice de distances OK")


def test_simple_tsp():
    """Test TSP sur un cas simple."""
    # Carré de 4 points
    locations = [
        Location(0, 0),  # Start
        Location(5, 0),
        Location(5, 5),
        Location(0, 5)
    ]
    
    warehouse = Warehouse(10, 10, locations[0])
    optimizer = RouteOptimizer(warehouse)
    
    route, distance = optimizer.solve_tsp(locations, start_index=0)
    
    print(f"Route: {route}")
    print(f"Distance: {distance}")
    
    # La distance optimale devrait être le périmètre : 5+5+5+5 = 20
    assert distance == 20
    print("✅ Test TSP simple OK")


def test_nearest_neighbor():
    """Test de l'heuristique du plus proche voisin."""
    start = Location(0, 0)
    locations = [
        Location(1, 0),
        Location(2, 0),
        Location(2, 1),
        Location(1, 1)
    ]
    
    route, distance = NearestNeighborTSP.solve(locations, start)
    
    print(f"Route NN: {[str(loc) for loc in route]}")
    print(f"Distance NN: {distance}")
    
    assert len(route) == len(locations) + 2  # start + locations + retour
    print("✅ Test Nearest Neighbor OK")


if __name__ == "__main__":
    print("=" * 70)
    print("Tests du module routing")
    print("=" * 70)
    
    test_distance_matrix()
    test_simple_tsp()
    test_nearest_neighbor()
    
    print("\n" + "=" * 70)
    print("✅ Tous les tests passent !")
    print("=" * 70)