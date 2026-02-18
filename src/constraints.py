from typing import List, Tuple
from .models import Agent, Robot, Human, Cart, Product, Order, Warehouse


class ConstraintChecker:

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse

    def check_capacity(self, agent: Agent, order: Order) -> Tuple[bool, str]:
        new_weight = agent.current_load_weight + order.total_weight
        new_volume = agent.current_load_volume + order.total_volume
        if new_weight > agent.capacity_weight:
            return False, f"Weight capacity exceeded: {new_weight:.1f}kg > {agent.capacity_weight}kg"
        if new_volume > agent.capacity_volume:
            return False, f"Volume capacity exceeded: {new_volume:.1f}dm3 > {agent.capacity_volume}dm3"
        return True, ''

    def check_product_compatibility(self, products: List[Product]) -> Tuple[bool, str]:
        for i, p1 in enumerate(products):
            for p2 in products[i + 1:]:
                if not p1.is_compatible_with(p2):
                    return False, f"Products incompatible: {p1.id} and {p2.id}"
        return True, ''

    def check_robot_restrictions(self, robot: Robot, order: Order) -> Tuple[bool, str]:
        no_zones = robot.restrictions.get('no_zones', [])
        no_fragile = robot.restrictions.get('no_fragile', False)
        max_item_weight = robot.restrictions.get('max_item_weight', float('inf'))

        for item in order.items:
            if not item.product:
                continue
            product = item.product
            zone_id = self.warehouse.get_zone_at(product.location)
            if zone_id and zone_id in no_zones:
                return False, f"Robot {robot.id} cannot enter zone {zone_id} (product {product.id})"
            if no_fragile and product.fragile:
                return False, f"Robot {robot.id} cannot carry fragile product {product.id}"
            if product.weight > max_item_weight:
                return False, f"Item {product.id} too heavy for robot {robot.id}"
        return True, ''

    def check_cart_assignment(self, cart: Cart) -> Tuple[bool, str]:
        if cart.restrictions.get('requires_human', False) and cart.assigned_human is None:
            return False, f"Cart {cart.id} requires an assigned human"
        return True, ''

    def can_assign_order(self, agent: Agent, order: Order) -> Tuple[bool, List[str]]:
        errors = []

        ok, msg = self.check_capacity(agent, order)
        if not ok:
            errors.append(msg)

        products = [item.product for item in order.items if item.product]
        ok, msg = self.check_product_compatibility(products)
        if not ok:
            errors.append(msg)

        # check against what's already on the agent
        ok, msg = self.check_product_compatibility(agent.current_products + products)
        if not ok:
            errors.append(f"Incompatible with agent's current load: {msg}")

        if isinstance(agent, Robot):
            ok, msg = self.check_robot_restrictions(agent, order)
            if not ok:
                errors.append(msg)

        if isinstance(agent, Cart):
            ok, msg = self.check_cart_assignment(agent)
            if not ok:
                errors.append(msg)

        return len(errors) == 0, errors