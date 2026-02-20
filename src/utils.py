from typing import List
from .models import Location, Agent, Order


def calculate_total_distance(locations: List[Location], start: Location = None) -> float:
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
    return agent.cost_per_hour * (time_minutes / 60)


def estimate_order_distance(order: Order, entry_point: Location) -> float:
    return calculate_total_distance(order.get_unique_locations(), entry_point)


def calculate_travel_time(distance: float, speed: float) -> float:
    if speed <= 0:
        return float('inf')
    return distance / speed / 60


def calculate_picking_time(num_products: int) -> float:
    return num_products * 0.5


def calculate_total_route_time(distance: float, speed: float, num_products: int) -> float:
    return calculate_travel_time(distance, speed) + calculate_picking_time(num_products)


def format_time(minutes: float) -> str:
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h:02d}:{m:02d}"


def export_to_json(data, filepath: str):
    import json
    from pathlib import Path
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_from_json(filepath: str):
    import json
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)