"""Tests for the greedy allocation algorithm."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.models import Robot, Human, Product, Order, OrderItem, Location, Warehouse, Zone
from src.allocation import GreedyAllocation


@pytest.fixture
def warehouse():
    zones = {
        'A': Zone('Electronics', 'electronics', [Location(1, 1), Location(2, 1)], []),
        'C': Zone('Food', 'food', [Location(8, 1)], ['robots_forbidden'])
    }
    return Warehouse(10, 8, Location(0, 0), zones)


class TestGreedyAllocation:

    def test_single_order_assigned(self, warehouse):
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "USB", "electronics", 0.5, 1.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 2, product)])
        order.calculate_totals()

        result = GreedyAllocation(warehouse).allocate([robot], [order])

        assert result['assigned_orders'] == 1
        assert result['failed_orders'] == 0

    def test_robot_preferred_over_human(self, warehouse):
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        human = Human("H1", 35, 50, 1.5, 25)
        product = Product("P001", "Mouse", "electronics", 0.3, 1.0, Location(1, 1), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, product)])
        order.calculate_totals()

        GreedyAllocation(warehouse).allocate([robot, human], [order])

        assert len(robot.assigned_orders) == 1
        assert len(human.assigned_orders) == 0

    def test_fragile_falls_back_to_human(self, warehouse):
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True})
        human = Human("H1", 35, 50, 1.5, 25)
        product = Product("P001", "Glass", "electronics", 1.0, 2.0, Location(1, 1), "high", True, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, product)])
        order.calculate_totals()

        GreedyAllocation(warehouse).allocate([robot, human], [order])

        assert len(human.assigned_orders) == 1

    def test_express_order_assigned_first(self, warehouse):
        robot = Robot("R1", 5, 10, 2.0, 5, {})
        product = Product("P001", "A", "cat", 3.0, 5.0, Location(1, 1), "high", False, [])

        order_standard = Order("O001", "08:00", "12:00", "standard",
                               items=[OrderItem("P001", 1, product)])
        order_standard.calculate_totals()

        order_express = Order("O002", "08:00", "10:00", "express",
                              items=[OrderItem("P001", 1, product)])
        order_express.calculate_totals()

        # Pass standard first in list; express should still win the agent
        GreedyAllocation(warehouse).allocate([robot], [order_standard, order_express])

        assert robot.assigned_orders[0].id == "O002"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])