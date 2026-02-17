import pytest 
from src.constraints import (
    check_capacity,
    check_incompatibilities,
    calculate_dist,
    get_total_path_distance
)

# --- TEST 1 : LA CAPACITÉ ---
def test_capacity_ok(): # Corrigé 'text' en 'test'
    agent = {"capacity_weight": 50, "capacity_volume": 100}
    products = [
        {"weight": 10, "volume": 20},
        {"weight": 5, "volume": 10}
    ]
    valide, msg = check_capacity(agent, products)
    assert valide is True

def test_capacity_trop_lourd():
    agent = {"capacity_weight": 10, "capacity_volume": 100}
    products = [{"weight": 15, "volume": 5}] # 15kg > 10kg
    valide, msg = check_capacity(agent, products)
    assert valide is False
    # Vérifie que ton code dans constraints.py écrit bien "poids" avec un S
    assert "poids" in msg.lower()

# --- TEST 2 : INCOMPATIBILITÉS ---
def test_incompatbilities_detectees():
    products = [
        {"id": "p11", "incompatible_with": ["p15"]},
        {"id": "P15", "incompatible_with": ["P11"]}
    ]
    valide, msg = check_incompatibilities(products)
    assert valide is False
    assert "incompatible" in msg.lower() # Ajout de .lower() par sécurité

# --- TEST 3 : LA DISTANCE DE MANHATTAN ---
def test_calcul_distance_simple():
    # Distance entre [0,0] et [3,4] : |0-3| + |0-4| = 7
    assert calculate_dist([0, 0], [3, 4]) == 7

def test_distance_totale_parcours():
    # Simulation d'une commande
    order = {"items": [{"product_id": "P1"}]}
    # Simulation du dictionnaire de produits
    products_dict = {"P1": {"location": [2, 3]}}
    # Simulation du warehouse
    warehouse = {"entry_point": [0, 0]}
    
    # Parcours : [0,0] -> [2,3] -> [0,0]
    # Distances : (2+3) + (2+3) = 10
    total = get_total_path_distance(order, products_dict, warehouse)
    assert total == 10