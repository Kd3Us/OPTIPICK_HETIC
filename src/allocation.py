from typing import List, Dict
from .models import Agent, Robot, Human, Cart, Order, Warehouse
from .constraints import ConstraintChecker


class GreedyAllocation:

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        self.checker = ConstraintChecker(warehouse)

    def _agent_priority(self, agent: Agent) -> int:
        # robots first (cheapest), then carts, then humans
        return {'robot': 0, 'cart': 1, 'human': 2}.get(agent.type, 99)

    def _order_priority(self, order: Order):
        # express before standard, then tightest deadline
        return (0 if order.priority == 'express' else 1, order.time_to_deadline())

    def allocate(self, agents: List[Agent], orders: List[Order]) -> Dict:
        for agent in agents:
            agent.reset_load()

        sorted_orders = sorted(orders, key=self._order_priority)
        sorted_agents = sorted(agents, key=self._agent_priority)

        successful = []
        failed = []

        for order in sorted_orders:
            assigned = False
            for agent in sorted_agents:
                # carts need a human — auto-pair with first free one
                if isinstance(agent, Cart) and agent.assigned_human is None:
                    free_human = next(
                        (a for a in sorted_agents if isinstance(a, Human) and not a.assigned_orders),
                        None
                    )
                    if free_human:
                        agent.assigned_human = free_human

                ok, _ = self.checker.can_assign_order(agent, order)
                if ok:
                    agent.assigned_orders.append(order)
                    agent.current_load_weight += order.total_weight
                    agent.current_load_volume += order.total_volume
                    for item in order.items:
                        if item.product:
                            agent.current_products.extend([item.product] * item.quantity)
                    order.assigned_agent = agent
                    successful.append({'order_id': order.id, 'agent_id': agent.id, 'agent_type': agent.type})
                    assigned = True
                    break

            if not assigned:
                failed.append({'order_id': order.id, 'reason': 'No compatible agent available'})

        return {
            'total_orders': len(orders),
            'assigned_orders': len(successful),
            'failed_orders': len(failed),
            'successful': successful,
            'failed': failed
        }


def print_allocation_summary(result: Dict, agents: List[Agent]):
    print("\n" + "=" * 60)
    print("ALLOCATION SUMMARY")
    print("=" * 60)
    print(f"  Total     : {result['total_orders']}")
    print(f"  Assigned  : {result['assigned_orders']}")
    print(f"  Failed    : {result['failed_orders']}")

    print("\nPer-agent:")
    for agent in agents:
        orders_str = ', '.join(o.id for o in agent.assigned_orders) or 'none'
        print(
            f"  {agent.id:4s} ({agent.type:5s})  "
            f"{agent.current_load_weight:.1f}kg/{agent.capacity_weight}kg  "
            f"{agent.current_load_volume:.1f}dm3/{agent.capacity_volume}dm3  "
            f"orders: {orders_str}"
        )

    if result['failed']:
        print("\nFailed:")
        for f in result['failed']:
            print(f"  {f['order_id']} - {f['reason']}")
    print("=" * 60)