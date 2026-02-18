"""
Global allocation optimisation via OR-Tools CP-SAT.
Assigns all orders to agents while minimising cost and respecting
all hard constraints simultaneously.
"""

from typing import List, Dict, Tuple
from ortools.sat.python import cp_model
import time

from .models import Agent, Order, Warehouse, Robot, Human, Cart
from .constraints import ConstraintChecker


def get_real_cost(agent: Agent) -> float:
    """
    Return the real hourly cost of an agent.
    A cart requires a human operator, so its real cost = cart + human rate.
    """
    if isinstance(agent, Cart) and agent.assigned_human is not None:
        return agent.cost_per_hour + agent.assigned_human.cost_per_hour
    return agent.cost_per_hour


class OptimalAllocator:

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        self.checker = ConstraintChecker(warehouse)

    def allocate(self, agents: List[Agent], orders: List[Order],
                 max_time_seconds: int = 30) -> Dict:

        # Reset agents cleanly
        for agent in agents:
            agent.current_load_weight = 0.0
            agent.current_load_volume = 0.0
            agent.current_products = []
            agent.assigned_orders = []

        # Auto-pair carts with humans
        free_humans = [a for a in agents if isinstance(a, Human)]
        for cart in [a for a in agents if isinstance(a, Cart)]:
            if cart.assigned_human is None and free_humans:
                cart.assigned_human = free_humans.pop(0)

        # Only use agents that can actually operate
        operational_agents = []
        for agent in agents:
            if isinstance(agent, Cart):
                if agent.is_operational():
                    operational_agents.append(agent)
            else:
                operational_agents.append(agent)

        n_agents = len(operational_agents)
        n_orders = len(orders)

        model = cp_model.CpModel()

        # Decision variables: assign[i][j] == 1 iff order i goes to agent j
        assign = {
            (i, j): model.NewBoolVar(f'assign_o{i}_a{j}')
            for i in range(n_orders)
            for j in range(n_agents)
        }

        # Each order assigned to exactly one agent
        for i in range(n_orders):
            model.Add(sum(assign[(i, j)] for j in range(n_agents)) == 1)

        # Capacity constraints
        for j, agent in enumerate(operational_agents):
            model.Add(
                sum(assign[(i, j)] * int(orders[i].total_weight * 100)
                    for i in range(n_orders))
                <= int(agent.capacity_weight * 100)
            )
            model.Add(
                sum(assign[(i, j)] * int(orders[i].total_volume * 100)
                    for i in range(n_orders))
                <= int(agent.capacity_volume * 100)
            )

        # Robot-specific hard constraints: ban infeasible (robot, order) pairs
        for j, agent in enumerate(operational_agents):
            if isinstance(agent, Robot):
                for i, order in enumerate(orders):
                    feasible, _ = self.checker.check_robot_restrictions(agent, order)
                    if not feasible:
                        model.Add(assign[(i, j)] == 0)

        # Objective: minimise total REAL cost (carts cost cart + human rate)
        objective_terms = []
        for j, agent in enumerate(operational_agents):
            real_cost = int(get_real_cost(agent) * 100)
            for i in range(n_orders):
                objective_terms.append(assign[(i, j)] * real_cost)

        model.Minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_seconds
        solver.parameters.log_search_progress = False

        start_time = time.time()
        status = solver.Solve(model)
        solve_time = time.time() - start_time

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            successful = []
            for i in range(n_orders):
                for j in range(n_agents):
                    if solver.Value(assign[(i, j)]) == 1:
                        order = orders[i]
                        agent = operational_agents[j]
                        agent.assigned_orders.append(order)
                        agent.current_load_weight += order.total_weight
                        agent.current_load_volume += order.total_volume
                        for item in order.items:
                            if item.product:
                                for _ in range(item.quantity):
                                    agent.current_products.append(item.product)
                        order.assigned_agent = agent
                        successful.append({
                            'order_id': order.id,
                            'agent_id': agent.id,
                            'agent_type': agent.type
                        })

            return {
                'status': 'optimal' if status == cp_model.OPTIMAL else 'feasible',
                'successful': successful,
                'failed': [],
                'total_orders': n_orders,
                'assigned_orders': len(successful),
                'failed_orders': 0,
                'solve_time_seconds': solve_time,
                'objective_value': solver.ObjectiveValue()
            }

        return {
            'status': 'infeasible',
            'successful': [],
            'failed': [{'order_id': o.id, 'reason': 'No solution found'} for o in orders],
            'total_orders': n_orders,
            'assigned_orders': 0,
            'failed_orders': n_orders,
            'solve_time_seconds': solve_time,
            'objective_value': None
        }


class OrderBatcher:
    """Groups compatible orders to reduce total travel distance."""

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        self.checker = ConstraintChecker(warehouse)

    def can_batch_orders(self, order1: Order, order2: Order, agent: Agent) -> Tuple[bool, str]:
        combined_weight = order1.total_weight + order2.total_weight
        combined_volume = order1.total_volume + order2.total_volume

        if combined_weight > agent.capacity_weight:
            return False, "Weight capacity exceeded"
        if combined_volume > agent.capacity_volume:
            return False, "Volume capacity exceeded"

        all_products = [
            item.product
            for order in (order1, order2)
            for item in order.items
            if item.product
        ]
        ok, msg = self.checker.check_product_compatibility(all_products)
        if not ok:
            return False, f"Product incompatibility: {msg}"

        return True, "OK"

    def find_batchable_orders(self, orders: List[Order], agent: Agent) -> List[List[Order]]:
        batches = []
        used_orders = set()

        for i, order1 in enumerate(orders):
            if order1.id in used_orders:
                continue
            batch = [order1]
            used_orders.add(order1.id)

            for j, order2 in enumerate(orders):
                if i == j or order2.id in used_orders:
                    continue
                can_add = all(
                    self.can_batch_orders(existing, order2, agent)[0]
                    for existing in batch
                )
                if can_add:
                    batch_weight = sum(o.total_weight for o in batch) + order2.total_weight
                    batch_volume = sum(o.total_volume for o in batch) + order2.total_volume
                    if batch_weight <= agent.capacity_weight and batch_volume <= agent.capacity_volume:
                        batch.append(order2)
                        used_orders.add(order2.id)

            batches.append(batch)

        return batches

    def calculate_batching_benefit(self, batch: List[Order]) -> float:
        """Estimated distance saved by processing orders together (metres)."""
        if len(batch) <= 1:
            return 0.0

        separate_distance = sum(
            self.warehouse.entry_point.distance_to(loc) * 2
            for order in batch
            for loc in order.get_unique_locations()
        )

        combined_locations = set(
            loc
            for order in batch
            for loc in order.get_unique_locations()
        )
        combined_distance = sum(
            self.warehouse.entry_point.distance_to(loc) * 2
            for loc in combined_locations
        )

        return separate_distance - combined_distance