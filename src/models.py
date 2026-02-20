"""
Core data models for the OptiPick system.

Classes:
    Location   -- (x, y) grid position
    Product    -- warehouse product with attributes
    Agent      -- base class for all agents (Robot, Human, Cart)
    Order      -- customer order with item list
    Warehouse  -- warehouse structure with zones and aisles
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Location:
    x: int
    y: int

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False
        return self.x == other.x and self.y == other.y

    def distance_to(self, other: 'Location') -> int:
        """Manhattan distance to another location."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __repr__(self):
        return f"({self.x}, {self.y})"


@dataclass
class Product:
    id: str
    name: str
    category: str
    weight: float
    volume: float
    location: Location
    frequency: str
    fragile: bool = False
    incompatible_with: List[str] = field(default_factory=list)

    def is_compatible_with(self, other: 'Product') -> bool:
        """Bidirectional incompatibility check."""
        return (other.id not in self.incompatible_with and
                self.id not in other.incompatible_with)

    def __repr__(self):
        return f"Product({self.id}: {self.name})"


@dataclass
class Agent:
    id: str
    type: str
    capacity_weight: float
    capacity_volume: float
    speed: float
    cost_per_hour: float
    restrictions: Dict = field(default_factory=dict)

    current_load_weight: float = 0.0
    current_load_volume: float = 0.0
    current_products: List[Product] = field(default_factory=list)
    assigned_orders: List['Order'] = field(default_factory=list)

    def can_carry(self, product: Product, quantity: int = 1) -> bool:
        total_weight = self.current_load_weight + (product.weight * quantity)
        total_volume = self.current_load_volume + (product.volume * quantity)
        return total_weight <= self.capacity_weight and total_volume <= self.capacity_volume

    def can_access_zone(self, zone: str) -> bool:
        no_zones = self.restrictions.get('no_zones', [])
        return zone not in no_zones

    def reset_load(self):
        self.current_load_weight = 0.0
        self.current_load_volume = 0.0
        self.current_products = []
        self.assigned_orders = []

    def __repr__(self):
        return f"{self.type.capitalize()}({self.id})"


class Robot(Agent):
    def __init__(self, id: str, capacity_weight: float, capacity_volume: float,
                 speed: float, cost_per_hour: float, restrictions: Dict):
        super().__init__(
            id=id, type="robot",
            capacity_weight=capacity_weight, capacity_volume=capacity_volume,
            speed=speed, cost_per_hour=cost_per_hour, restrictions=restrictions
        )

    def can_carry(self, product: Product, quantity: int = 1) -> bool:
        if not super().can_carry(product, quantity):
            return False
        if self.restrictions.get('no_fragile', False) and product.fragile:
            return False
        max_item_weight = self.restrictions.get('max_item_weight', float('inf'))
        if product.weight > max_item_weight:
            return False
        return True


class Human(Agent):
    def __init__(self, id: str, capacity_weight: float, capacity_volume: float,
                 speed: float, cost_per_hour: float, restrictions: Dict = None):
        super().__init__(
            id=id, type="human",
            capacity_weight=capacity_weight, capacity_volume=capacity_volume,
            speed=speed, cost_per_hour=cost_per_hour, restrictions=restrictions or {}
        )
        self.assigned_cart: Optional['Cart'] = None


class Cart(Agent):
    def __init__(self, id: str, capacity_weight: float, capacity_volume: float,
                 speed: float, cost_per_hour: float, restrictions: Dict):
        super().__init__(
            id=id, type="cart",
            capacity_weight=capacity_weight, capacity_volume=capacity_volume,
            speed=speed, cost_per_hour=cost_per_hour, restrictions=restrictions
        )
        self.assigned_human: Optional[Human] = None

    def is_operational(self) -> bool:
        return self.assigned_human is not None


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    product: Optional[Product] = None


@dataclass
class Order:
    id: str
    received_time: str
    deadline: str
    priority: str
    items: List[OrderItem] = field(default_factory=list)

    total_weight: float = 0.0
    total_volume: float = 0.0
    assigned_agent: Optional[Agent] = None

    def calculate_totals(self):
        self.total_weight = sum(
            item.product.weight * item.quantity
            for item in self.items if item.product
        )
        self.total_volume = sum(
            item.product.volume * item.quantity
            for item in self.items if item.product
        )

    def get_all_products(self) -> List[Tuple[Product, int]]:
        return [(item.product, item.quantity) for item in self.items if item.product]

    def get_unique_locations(self) -> List[Location]:
        locations = set()
        for item in self.items:
            if item.product:
                locations.add(item.product.location)
        return list(locations)

    def has_incompatibilities(self) -> bool:
        products = [item.product for item in self.items if item.product]
        for i, p1 in enumerate(products):
            for p2 in products[i + 1:]:
                if not p1.is_compatible_with(p2):
                    return True
        return False

    def time_to_deadline(self) -> int:
        """Returns available time in minutes."""
        received_h, received_m = map(int, self.received_time.split(':'))
        deadline_h, deadline_m = map(int, self.deadline.split(':'))
        return (deadline_h * 60 + deadline_m) - (received_h * 60 + received_m)

    def __repr__(self):
        return f"Order({self.id}, {len(self.items)} items, priority={self.priority})"


@dataclass
class Zone:
    name: str
    type: str
    coords: List[Location]
    restrictions: List[str] = field(default_factory=list)

    def contains(self, location: Location) -> bool:
        return location in self.coords


@dataclass
class Warehouse:
    width: int
    height: int
    entry_point: Location
    zones: Dict[str, Zone] = field(default_factory=dict)
    aisles: List[Location] = field(default_factory=list)

    def is_aisle(self, location: Location) -> bool:
        """Check if a location is a navigable aisle cell."""
        return location in self.aisles

    def get_pick_point(self, product_location: Location) -> Location:
        """
        Return the nearest aisle cell adjacent to a rack location.
        Agents navigate to this pick point to collect the product,
        rather than entering the rack itself.
        """
        if not self.aisles:
            return product_location

        aisle_set = set(self.aisles)
        # Check the 4 cardinal neighbours of the product location
        neighbours = [
            Location(product_location.x - 1, product_location.y),
            Location(product_location.x + 1, product_location.y),
            Location(product_location.x, product_location.y - 1),
            Location(product_location.x, product_location.y + 1),
        ]
        aisle_neighbours = [loc for loc in neighbours if loc in aisle_set]
        if aisle_neighbours:
            # Return the aisle neighbour closest to the entry point
            return min(aisle_neighbours, key=lambda loc: self.entry_point.distance_to(loc))

        # Fallback: nearest aisle cell by Manhattan distance
        return min(self.aisles, key=lambda loc: product_location.distance_to(loc))

    def get_zone_at(self, location: Location) -> Optional[str]:
        for zone_id, zone in self.zones.items():
            if zone.contains(location):
                return zone_id
        return None

    def get_zone_type(self, location: Location) -> Optional[str]:
        zone_id = self.get_zone_at(location)
        if zone_id:
            return self.zones[zone_id].type
        return None

    def __repr__(self):
        return (f"Warehouse({self.width}x{self.height}, "
                f"{len(self.zones)} zones, "
                f"{len(self.aisles)} aisle cells)")