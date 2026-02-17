"""Tests for core data models."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.models import Location, Product, Agent, Robot, Human, Cart, Order, OrderItem


class TestLocation:

    def test_creation(self):
        loc = Location(5, 3)
        assert loc.x == 5
        assert loc.y == 3

    def test_equality(self):
        assert Location(2, 3) == Location(2, 3)
        assert Location(2, 3) != Location(2, 4)

    def test_manhattan_distance(self):
        assert Location(0, 0).distance_to(Location(3, 4)) == 7

    def test_distance_same_location(self):
        assert Location(5, 5).distance_to(Location(5, 5)) == 0

    def test_hashable(self):
        locations = {Location(1, 2), Location(1, 2), Location(2, 3)}
        assert len(locations) == 2


class TestProduct:

    def test_creation(self):
        product = Product("P001", "Laptop", "electronics", 2.5, 8.0,
                          Location(5, 3), "high", True, ["P002"])
        assert product.id == "P001"
        assert product.weight == 2.5
        assert product.fragile is True

    def test_compatible(self):
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        assert p1.is_compatible_with(p2) is True

    def test_incompatible_explicit(self):
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, ["P002"])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        assert p1.is_compatible_with(p2) is False

    def test_incompatible_bidirectional(self):
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, ["P001"])
        assert p1.is_compatible_with(p2) is False
        assert p2.is_compatible_with(p1) is False


class TestAgent:

    def test_robot_creation(self):
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True, 'no_zones': ['C']})
        assert robot.id == "R1"
        assert robot.type == "robot"

    def test_human_creation(self):
        human = Human("H1", 35, 50, 1.5, 25)
        assert human.id == "H1"
        assert human.type == "human"

    def test_can_carry_ok(self):
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "Test", "cat", 5.0, 10.0, Location(0, 0), "high", False, [])
        assert agent.can_carry(product, quantity=1) is True

    def test_can_carry_weight_exceeded(self):
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "Heavy", "cat", 25.0, 10.0, Location(0, 0), "high", False, [])
        assert agent.can_carry(product, quantity=1) is False

    def test_can_carry_volume_exceeded(self):
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "Bulky", "cat", 5.0, 40.0, Location(0, 0), "high", False, [])
        assert agent.can_carry(product, quantity=1) is False

    def test_robot_rejects_fragile(self):
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True})
        product = Product("P001", "Glass", "cat", 2.0, 5.0, Location(0, 0), "high", True, [])
        assert robot.can_carry(product) is False

    def test_robot_rejects_overweight_item(self):
        robot = Robot("R1", 20, 30, 2.0, 5, {'max_item_weight': 10})
        product = Product("P001", "Heavy", "cat", 15.0, 5.0, Location(0, 0), "high", False, [])
        assert robot.can_carry(product) is False

    def test_robot_zone_access_allowed(self):
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_zones': ['C']})
        assert robot.can_access_zone('A') is True
        assert robot.can_access_zone('B') is True

    def test_robot_zone_access_denied(self):
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_zones': ['C']})
        assert robot.can_access_zone('C') is False

    def test_cart_operational_with_human(self):
        cart = Cart("C1", 50, 80, 1.2, 3, {'requires_human': True})
        cart.assigned_human = Human("H1", 35, 50, 1.5, 25)
        assert cart.is_operational() is True

    def test_cart_not_operational_without_human(self):
        cart = Cart("C1", 50, 80, 1.2, 3, {'requires_human': True})
        assert cart.is_operational() is False

    def test_reset_load(self):
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        agent.current_load_weight = 10.0
        agent.current_load_volume = 15.0
        agent.reset_load()
        assert agent.current_load_weight == 0.0
        assert agent.current_load_volume == 0.0
        assert agent.current_products == []


class TestOrder:

    def test_creation(self):
        order = Order("O001", "08:00", "10:00", "express", items=[])
        assert order.id == "O001"
        assert order.priority == "express"

    def test_calculate_totals(self):
        p1 = Product("P001", "A", "cat", 2.0, 5.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 3.0, 7.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 2, p1), OrderItem("P002", 1, p2)])
        order.calculate_totals()
        assert order.total_weight == 7.0   # 2*2 + 1*3
        assert order.total_volume == 17.0  # 2*5 + 1*7

    def test_unique_locations(self):
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        p3 = Product("P003", "C", "cat", 1.0, 1.0, Location(2, 2), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, p1), OrderItem("P002", 1, p2),
                             OrderItem("P003", 1, p3)])
        assert len(order.get_unique_locations()) == 2

    def test_time_to_deadline(self):
        order = Order("O001", "08:00", "10:30", "standard", items=[])
        assert order.time_to_deadline() == 150

    def test_no_incompatibilities(self):
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, p1), OrderItem("P002", 1, p2)])
        assert order.has_incompatibilities() is False

    def test_has_incompatibilities(self):
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, ["P002"])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, p1), OrderItem("P002", 1, p2)])
        assert order.has_incompatibilities() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])