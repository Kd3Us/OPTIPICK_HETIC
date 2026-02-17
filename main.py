"""
OptiPick entry point.

Currently covers Day 1 scope only: data loading and display.

Pending collaborator work:
    Collaborator 1 -- src/constraints.py, src/allocation.py
    Collaborator 2 -- src/visualization.py

Integrate their modules once delivered by updating the imports
and the TODO sections below.
"""

from src.loader import load_all_data
from src.models import Robot, Human, Cart

# TODO (after Collaborator 1): uncomment and wire in
# from src.constraints import ConstraintChecker
# from src.allocation import GreedyAllocation, print_allocation_summary

# TODO (after Collaborator 2): uncomment and wire in
# from src.visualization import generate_all_visualizations


def main():
    print("=" * 60)
    print("OptiPick - Warehouse Management Optimisation")
    print("Day 1 - Data loading")
    print("=" * 60)

    print("\nLoading data...")
    try:
        data = load_all_data('data')
    except Exception as exc:
        print(f"Failed to load data: {exc}")
        return

    warehouse = data['warehouse']
    products = data['products']
    agents = data['agents']
    orders = data['orders']

    print(f"  Warehouse : {warehouse.width}x{warehouse.height}")
    print(f"  Zones     : {len(warehouse.zones)}")
    print(f"  Products  : {len(products)}")
    print(f"  Agents    : {len(agents)}"
          f"  (robots: {sum(1 for a in agents if isinstance(a, Robot))},"
          f"  humans: {sum(1 for a in agents if isinstance(a, Human))},"
          f"  carts: {sum(1 for a in agents if isinstance(a, Cart))})")
    print(f"  Orders    : {len(orders)}")

    print("\nZones:")
    for zone_id, zone in warehouse.zones.items():
        restr = ', '.join(zone.restrictions) if zone.restrictions else 'none'
        print(f"  {zone_id} ({zone.name})  slots={len(zone.coords)}  restrictions={restr}")

    print("\nOrders:")
    for order in orders:
        print(
            f"  {order.id}  priority={order.priority}"
            f"  deadline={order.deadline}"
            f"  {order.time_to_deadline()}min"
            f"  {order.total_weight:.1f}kg / {order.total_volume:.1f}dm3"
            f"  ({len(order.items)} items)"
        )

    print("\nDistance from entry per zone:")
    for zone_id, zone in warehouse.zones.items():
        if zone.coords:
            dist = warehouse.entry_point.distance_to(zone.coords[0])
            print(f"  Zone {zone_id} ({zone.name}): {dist}m")

    # TODO (after Collaborator 1): replace the block below with allocation + summary
    # allocator = GreedyAllocation(warehouse)
    # result = allocator.allocate(agents, orders)
    # print_allocation_summary(result, agents)

    # TODO (after Collaborator 2): generate visualisations
    # generate_all_visualizations(warehouse, agents, orders, result, routes)


if __name__ == "__main__":
    main()