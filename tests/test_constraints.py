<<<<<<< HEAD
"""Tests for constraint checking logic."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.models import Robot, Human, Cart, Product, Order, OrderItem, Location, Warehouse, Zone
from src.constraints import ConstraintChecker


@pytest.fixture
def warehouse():
    zones = {
        'A': Zone('Electronics', 'electronics', [Location(1, 1)], []),
        'C': Zone('Food', 'food', [Location(8, 1)], ['robots_forbidden'])
    }
    return Warehouse(10, 8, Location(0, 0), zones)


@pytest.fixture
def checker(warehouse):
    return ConstraintChecker(warehouse)


class TestCapacity:

    def test_within_capacity(self, checker):
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "A", "cat", 5.0, 10.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 2, product)])
        order.calculate_totals()
        ok, msg = checker.check_capacity(agent, order)
        assert ok is True

    def test_weight_exceeded(self, checker):
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "Heavy", "cat", 15.0, 5.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 2, product)])
        order.calculate_totals()
        ok, msg = checker.check_capacity(agent, order)
        assert ok is False
        assert "weight" in msg.lower()

    def test_volume_exceeded(self, checker):
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "Bulky", "cat", 5.0, 20.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 2, product)])
        order.calculate_totals()
        ok, msg = checker.check_capacity(agent, order)
        assert ok is False
        assert "volume" in msg.lower()


class TestProductCompatibility:

    def test_compatible(self, checker):
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        ok, _ = checker.check_product_compatibility([p1, p2])
        assert ok is True

    def test_incompatible(self, checker):
        p1 = Product("P001", "A", "chemical", 1.0, 1.0, Location(0, 0), "high", False, ["P002"])
        p2 = Product("P002", "B", "food", 1.0, 1.0, Location(1, 1), "high", False, [])
        ok, msg = checker.check_product_compatibility([p1, p2])
        assert ok is False
        assert "incompatible" in msg.lower()


class TestRobotRestrictions:

    def test_fragile_rejected(self, checker):
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True})
        product = Product("P001", "Glass", "cat", 2.0, 5.0, Location(1, 1), "high", True, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, product)])
        ok, msg = checker.check_robot_restrictions(robot, order)
        assert ok is False
        assert "fragile" in msg.lower()

    def test_forbidden_zone_rejected(self, checker):
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_zones': ['C']})
        product = Product("P001", "Milk", "food", 1.0, 1.0, Location(8, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, product)])
        ok, msg = checker.check_robot_restrictions(robot, order)
        assert ok is False
        assert "zone" in msg.lower()

    def test_overweight_item_rejected(self, checker):
        robot = Robot("R1", 20, 30, 2.0, 5, {'max_item_weight': 10})
        product = Product("P001", "Heavy", "cat", 15.0, 5.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, product)])
        ok, msg = checker.check_robot_restrictions(robot, order)
        assert ok is False
        assert "heavy" in msg.lower()


class TestCartAssignment:

    def test_with_human(self, checker):
        cart = Cart("C1", 50, 80, 1.2, 3, {'requires_human': True})
        cart.assigned_human = Human("H1", 35, 50, 1.5, 25)
        ok, _ = checker.check_cart_assignment(cart)
        assert ok is True

    def test_without_human(self, checker):
        cart = Cart("C1", 50, 80, 1.2, 3, {'requires_human': True})
        ok, msg = checker.check_cart_assignment(cart)
        assert ok is False
        assert "human" in msg.lower()


class TestCanAssignOrder:

    def test_successful_assignment(self, checker):
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "USB", "electronics", 0.1, 0.5, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 2, product)])
        order.calculate_totals()
        ok, errors = checker.can_assign_order(robot, order)
        assert ok is True
        assert errors == []

    def test_multiple_violations(self, checker):
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True, 'no_zones': ['C']})
        product = Product("P001", "Glass", "food", 25.0, 5.0, Location(8, 1), "high", True, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, product)])
        order.calculate_totals()
        ok, errors = checker.can_assign_order(robot, order)
        assert ok is False
        assert len(errors) > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
=======
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
>>>>>>> emery
