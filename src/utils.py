"""
Utility functions for OptiPick.
"""

from typing import List
from .models import Location, Agent, Order


def calculate_total_distance(locations: List[Location], start: Location = None) -> float:
    """
    Total path distance across a list of locations.
    If start is provided, the path begins and ends there.
    """
    if not locations:
        return 0.0

    total = 0.0
    current = start if start else locations[0]

    for loc in locations:
        total += current.distance_to(loc)
        current = loc

    if start:
        total += current.distance_to(start)

    return total


def calculate_agent_cost(agent: Agent, time_minutes: float) -> float:
    """Cost in euros for an agent active for time_minutes."""
    return agent.cost_per_hour * (time_minutes / 60)


def estimate_order_distance(order: Order, entry_point: Location) -> float:
    """Estimated pick distance for one order, starting from entry_point."""
    locations = order.get_unique_locations()
    return calculate_total_distance(locations, entry_point)