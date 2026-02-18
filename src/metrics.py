import json
import numpy as np
from typing import List, Dict
from pathlib import Path


def calculate_total_distance(all_routes: Dict) -> float:
    total = 0.0
    for agent_routes in all_routes.values():
        for route in agent_routes:
            total += route.get("distance", 0)
    return total


def calculate_total_time(all_routes: Dict) -> float:
    max_time = 0.0
    for agent_routes in all_routes.values():
        t = sum(r.get("time", 0) for r in agent_routes)
        if t > max_time:
            max_time = t
    return max_time


def calculate_total_cost(agents_usage_time: Dict) -> float:
    return sum(
        info.get("time", 0) * info.get("hourly_cost", 0)
        for info in agents_usage_time.values()
    )


def calculate_agent_utilization(agents: List[Dict], routes: Dict, total_time: float) -> Dict:
    if total_time == 0:
        return {a["id"]: 0.0 for a in agents}
    return {
        agent["id"]: round(
            sum(r.get("time", 0) for r in routes.get(agent["id"], [])) / total_time * 100, 2
        )
        for agent in agents
    }


def calculate_load_balance_stddev(agents_times: List[float]) -> float:
    return float(np.std(agents_times))


def build_metrics_from_route_results(route_results: List[Dict]) -> Dict:
    if not route_results:
        return {}
    per_agent = {
        r['agent_id']: {
            'type': r['agent_type'],
            'distance': r['total_distance'],
            'time_minutes': r['total_time_minutes'],
            'cost_euros': r['total_cost_euros'],
            'orders': r['orders'],
            'locations_visited': r['locations_visited']
        }
        for r in route_results
    }
    times = [r['total_time_minutes'] for r in route_results]
    return {
        'total_distance_m': sum(r['total_distance'] for r in route_results),
        'total_cost_euros': sum(r['total_cost_euros'] for r in route_results),
        'makespan_minutes': max(times),
        'load_balance_stddev': float(np.std(times)) if len(times) > 1 else 0.0,
        'per_agent': per_agent
    }


def export_allocation_results(allocation: Dict, filepath: str = "results/allocation_results.json"):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(allocation, f, indent=2)


def export_routes(routes: List[Dict], filepath: str = "results/routes.json"):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    serialisable = []
    for r in routes:
        entry = {k: v for k, v in r.items() if k != 'route'}
        entry['route'] = [
            {
                'location': str(step['location']),
                'cumulative_distance': step['cumulative_distance'],
                'products': [
                    {'order_id': p['order_id'], 'product_id': p['product'].id, 'quantity': p['quantity']}
                    for p in step['products']
                ]
            }
            for step in r.get('route', [])
        ]
        serialisable.append(entry)
    with open(filepath, "w") as f:
        json.dump(serialisable, f, indent=2)


def export_metrics(metrics_dict: Dict, filepath: str = "results/metrics.json"):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(metrics_dict, f, indent=2)


def print_metrics_summary(metrics: Dict):
    print("\n" + "=" * 60)
    print("METRICS")
    print("=" * 60)
    print(f"  Distance   : {metrics.get('total_distance_m', 0):.1f} m")
    print(f"  Cost       : {metrics.get('total_cost_euros', 0):.2f} EUR")
    print(f"  Makespan   : {metrics.get('makespan_minutes', 0):.1f} min")
    print(f"  Balance σ  : {metrics.get('load_balance_stddev', 0):.2f}")
    if 'per_agent' in metrics:
        print()
        for agent_id, info in metrics['per_agent'].items():
            print(
                f"  {agent_id:4s} ({info['type']:5s})  "
                f"{info['distance']:.1f}m  "
                f"{info['time_minutes']:.1f}min  "
                f"{info['cost_euros']:.2f}EUR  "
                f"[{', '.join(info['orders'])}]"
            )
    print("=" * 60)