"""Tests for metrics calculation and visualization functions."""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from unittest.mock import patch
from src.metrics import (
    calculate_total_distance,
    calculate_total_time,
    calculate_total_cost,
    calculate_agent_utilization,
    calculate_load_balance_stddev,
    build_metrics_from_route_results
)


@pytest.fixture
def sample_routes():
    return {
        "R1": [{"distance": 10, "time": 5}, {"distance": 15, "time": 7}],
        "H1": [{"distance": 8, "time": 4}, {"distance": 12, "time": 6}],
        "C1": [{"distance": 20, "time": 10}]
    }


@pytest.fixture
def sample_agents():
    return [{"id": "R1"}, {"id": "H1"}, {"id": "C1"}]


@pytest.fixture
def sample_usage():
    return {
        "R1": {"time": 12, "hourly_cost": 5},
        "H1": {"time": 10, "hourly_cost": 25},
        "C1": {"time": 10, "hourly_cost": 3}
    }


@pytest.fixture
def sample_route_results():
    return [
        {
            'agent_id': 'R1',
            'agent_type': 'robot',
            'total_distance': 25.0,
            'total_time_minutes': 12.0,
            'total_cost_euros': 1.0,
            'orders': ['O001', 'O002'],
            'locations_visited': 4
        },
        {
            'agent_id': 'H1',
            'agent_type': 'human',
            'total_distance': 20.0,
            'total_time_minutes': 20.0,
            'total_cost_euros': 8.33,
            'orders': ['O003'],
            'locations_visited': 3
        }
    ]


class TestCalculateTotalDistance:

    def test_sums_all_distances(self, sample_routes):
        result = calculate_total_distance(sample_routes)
        assert result == 65.0  # 10+15+8+12+20

    def test_empty_routes(self):
        result = calculate_total_distance({})
        assert result == 0.0

    def test_single_agent(self):
        routes = {"R1": [{"distance": 30, "time": 5}]}
        assert calculate_total_distance(routes) == 30.0


class TestCalculateTotalTime:

    def test_returns_max_agent_time(self, sample_routes):
        result = calculate_total_time(sample_routes)
        assert result == 12.0  # R1 has 5+7=12, H1 has 4+6=10, C1 has 10

    def test_empty_routes(self):
        assert calculate_total_time({}) == 0.0

    def test_single_agent(self):
        routes = {"R1": [{"distance": 10, "time": 8}]}
        assert calculate_total_time(routes) == 8.0


class TestCalculateTotalCost:

    def test_cost_calculation(self, sample_usage):
        result = calculate_total_cost(sample_usage)
        # R1: 12*5=60, H1: 10*25=250, C1: 10*3=30 => 340
        assert result == 340.0

    def test_empty_usage(self):
        assert calculate_total_cost({}) == 0.0


class TestCalculateAgentUtilization:

    def test_utilization_percentages(self, sample_agents, sample_routes):
        total_time = calculate_total_time(sample_routes)
        result = calculate_agent_utilization(sample_agents, sample_routes, total_time)
        assert "R1" in result
        assert "H1" in result
        assert "C1" in result
        assert result["R1"] == 100.0  # R1 has max time

    def test_zero_total_time(self, sample_agents, sample_routes):
        result = calculate_agent_utilization(sample_agents, sample_routes, 0)
        for v in result.values():
            assert v == 0.0


class TestCalculateLoadBalanceStddev:

    def test_balanced(self):
        assert calculate_load_balance_stddev([10, 10, 10]) == 0.0

    def test_unbalanced(self):
        result = calculate_load_balance_stddev([0, 0, 30])
        assert result > 0

    def test_single_agent(self):
        assert calculate_load_balance_stddev([15]) == 0.0


class TestBuildMetricsFromRouteResults:

    def test_structure(self, sample_route_results):
        metrics = build_metrics_from_route_results(sample_route_results)
        assert 'total_distance_m' in metrics
        assert 'total_cost_euros' in metrics
        assert 'makespan_minutes' in metrics
        assert 'load_balance_stddev' in metrics
        assert 'per_agent' in metrics

    def test_total_distance(self, sample_route_results):
        metrics = build_metrics_from_route_results(sample_route_results)
        assert metrics['total_distance_m'] == 45.0  # 25 + 20

    def test_makespan_is_max(self, sample_route_results):
        metrics = build_metrics_from_route_results(sample_route_results)
        assert metrics['makespan_minutes'] == 20.0  # max(12, 20)

    def test_empty_results(self):
        metrics = build_metrics_from_route_results([])
        assert metrics == {}

    def test_per_agent_keys(self, sample_route_results):
        metrics = build_metrics_from_route_results(sample_route_results)
        assert 'R1' in metrics['per_agent']
        assert 'H1' in metrics['per_agent']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])