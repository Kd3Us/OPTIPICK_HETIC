"""Tests for TSP route optimisation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.models import Location, Warehouse
from src.routing import RouteOptimizer, NearestNeighborTSP


@pytest.fixture
def warehouse():
    return Warehouse(10, 8, Location(0, 0))


class TestDistanceMatrix:

    def test_values(self, warehouse):
        locations = [
            Location(0, 0), Location(3, 0),
            Location(3, 4), Location(0, 4)
        ]
        matrix = RouteOptimizer(warehouse).create_distance_matrix(locations)
        assert matrix[0][1] == 3   # (0,0) -> (3,0)
        assert matrix[0][2] == 7   # (0,0) -> (3,4)
        assert matrix[1][2] == 4   # (3,0) -> (3,4)


class TestSolveTSP:

    def test_square_perimeter(self, warehouse):
        locations = [
            Location(0, 0), Location(5, 0),
            Location(5, 5), Location(0, 5)
        ]
        route, distance = RouteOptimizer(warehouse).solve_tsp(locations, start_index=0)
        # Optimal tour = perimeter = 20
        assert distance == 20.0

    def test_single_location(self, warehouse):
        route, distance = RouteOptimizer(warehouse).solve_tsp([Location(3, 3)], start_index=0)
        assert distance == 0.0


class TestNearestNeighbor:

    def test_route_length(self, warehouse):
        start = Location(0, 0)
        locations = [
            Location(1, 0), Location(2, 0),
            Location(2, 1), Location(1, 1)
        ]
        route, distance = NearestNeighborTSP.solve(locations, start)
        # route = start + all locations + start
        assert len(route) == len(locations) + 2

    def test_distance_positive(self, warehouse):
        start = Location(0, 0)
        locations = [Location(3, 0), Location(3, 4)]
        _, distance = NearestNeighborTSP.solve(locations, start)
        assert distance > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])