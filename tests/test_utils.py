"""Tests for utility functions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.models import Location, Product, Order, OrderItem, Robot
from src.utils import calculate_total_distance, calculate_agent_cost, estimate_order_distance


class TestCalculateTotalDistance:

    def test_empty_list(self):
        assert calculate_total_distance([]) == 0.0

    def test_single_location(self):
        assert calculate_total_distance([Location(5, 3)]) == 0.0

    def test_multiple_locations_no_start(self):
        locations = [Location(0, 0), Location(3, 0), Location(3, 4)]
        # (0,0)->(3,0)=3  (3,0)->(3,4)=4  total=7
        assert calculate_total_distance(locations) == 7.0

    def test_with_start_includes_return(self):
        start = Location(0, 0)
        locations = [Location(3, 0), Location(3, 4)]
        # (0,0)->(3,0)=3  (3,0)->(3,4)=4  (3,4)->(0,0)=7  total=14
        assert calculate_total_distance(locations, start) == 14.0


class TestCalculateAgentCost:

    def test_standard_cost(self):
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        # 30min = 0.5h  -> 0.5 * 5 = 2.5 EUR
        assert calculate_agent_cost(robot, 30) == 2.5

    def test_zero_time(self):
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        assert calculate_agent_cost(robot, 0) == 0.0


class TestEstimateOrderDistance:

    def test_positive_distance(self):
        entry = Location(0, 0)
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(3, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(3, 4), "high", False, [])
        order = Order("O001", "08:00", "10:00", "standard",
                      items=[OrderItem("P001", 1, p1), OrderItem("P002", 1, p2)])
        assert estimate_order_distance(order, entry) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])