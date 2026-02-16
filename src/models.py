"""
Module de modélisation des entités du système OptiPick.

Classes principales :
- Location : Représente une position (x, y) dans l'entrepôt
- Product : Produit avec ses caractéristiques
- Agent : Classe parent pour tous les agents (Robot, Human, Cart)
- Order : Commande client avec liste de produits
- Warehouse : Structure de l'entrepôt avec zones
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Location:
    """Représente une position dans l'entrepôt."""
    x: int
    y: int
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        if not isinstance(other, Location):
            return False
        return self.x == other.x and self.y == other.y
    
    def distance_to(self, other: 'Location') -> int:
        """Calcule la distance de Manhattan vers une autre position."""
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def __repr__(self):
        return f"({self.x}, {self.y})"


@dataclass
class Product:
    """Représente un produit dans l'entrepôt."""
    id: str
    name: str
    category: str
    weight: float  # kg
    volume: float  # dm³
    location: Location
    frequency: str  # "low", "medium", "high", "very_high"
    fragile: bool
    incompatible_with: List[str] = field(default_factory=list)
    
    def is_compatible_with(self, other: 'Product') -> bool:
        """Vérifie si ce produit est compatible avec un autre."""
        return (other.id not in self.incompatible_with and 
                self.id not in other.incompatible_with)
    
    def __repr__(self):
        return f"Product({self.id}: {self.name})"


@dataclass
class Agent:
    """Classe parent pour tous les agents (Robot, Human, Cart)."""
    id: str
    type: str  # "robot", "human", "cart"
    capacity_weight: float  # kg
    capacity_volume: float  # dm³
    speed: float  # m/s
    cost_per_hour: float  # €/h
    restrictions: Dict = field(default_factory=dict)
    
    # État de l'agent
    current_load_weight: float = 0.0
    current_load_volume: float = 0.0
    current_products: List[Product] = field(default_factory=list)
    assigned_orders: List['Order'] = field(default_factory=list)
    
    def can_carry(self, product: Product, quantity: int = 1) -> bool:
        """Vérifie si l'agent peut transporter le produit."""
        total_weight = self.current_load_weight + (product.weight * quantity)
        total_volume = self.current_load_volume + (product.volume * quantity)
        
        # Vérification capacité
        if total_weight > self.capacity_weight or total_volume > self.capacity_volume:
            return False
        
        return True
    
    def can_access_zone(self, zone: str) -> bool:
        """Vérifie si l'agent peut accéder à une zone."""
        no_zones = self.restrictions.get('no_zones', [])
        return zone not in no_zones
    
    def reset_load(self):
        """Réinitialise la charge de l'agent."""
        self.current_load_weight = 0.0
        self.current_load_volume = 0.0
        self.current_products = []
        self.assigned_orders = []
    
    def __repr__(self):
        return f"{self.type.capitalize()}({self.id})"


class Robot(Agent):
    """Robot autonome avec restrictions spécifiques."""
    
    def __init__(self, id: str, capacity_weight: float, capacity_volume: float,
                 speed: float, cost_per_hour: float, restrictions: Dict):
        super().__init__(
            id=id,
            type="robot",
            capacity_weight=capacity_weight,
            capacity_volume=capacity_volume,
            speed=speed,
            cost_per_hour=cost_per_hour,
            restrictions=restrictions
        )
    
    def can_carry(self, product: Product, quantity: int = 1) -> bool:
        """Vérifie les restrictions spécifiques aux robots."""
        # Vérification capacité de base
        if not super().can_carry(product, quantity):
            return False
        
        # Robots ne peuvent pas transporter d'objets fragiles
        if self.restrictions.get('no_fragile', False) and product.fragile:
            return False
        
        # Robots ne peuvent pas transporter d'objets trop lourds individuellement
        max_item_weight = self.restrictions.get('max_item_weight', float('inf'))
        if product.weight > max_item_weight:
            return False
        
        return True


class Human(Agent):
    """Préparateur humain sans restrictions."""
    
    def __init__(self, id: str, capacity_weight: float, capacity_volume: float,
                 speed: float, cost_per_hour: float, restrictions: Dict = None):
        super().__init__(
            id=id,
            type="human",
            capacity_weight=capacity_weight,
            capacity_volume=capacity_volume,
            speed=speed,
            cost_per_hour=cost_per_hour,
            restrictions=restrictions or {}
        )
        self.assigned_cart: Optional['Cart'] = None


class Cart(Agent):
    """Chariot semi-autonome nécessitant un humain."""
    
    def __init__(self, id: str, capacity_weight: float, capacity_volume: float,
                 speed: float, cost_per_hour: float, restrictions: Dict):
        super().__init__(
            id=id,
            type="cart",
            capacity_weight=capacity_weight,
            capacity_volume=capacity_volume,
            speed=speed,
            cost_per_hour=cost_per_hour,
            restrictions=restrictions
        )
        self.assigned_human: Optional[Human] = None
    
    def is_operational(self) -> bool:
        """Un chariot ne peut fonctionner que si un humain lui est assigné."""
        return self.assigned_human is not None


@dataclass
class OrderItem:
    """Item d'une commande (produit + quantité)."""
    product_id: str
    quantity: int
    product: Optional[Product] = None  # Sera rempli lors du chargement


@dataclass
class Order:
    """Commande client à préparer."""
    id: str
    received_time: str  # Format "HH:MM"
    deadline: str  # Format "HH:MM"
    priority: str  # "standard" ou "express"
    items: List[OrderItem] = field(default_factory=list)
    
    # Calculés
    total_weight: float = 0.0
    total_volume: float = 0.0
    
    # Allocation
    assigned_agent: Optional[Agent] = None
    
    def calculate_totals(self):
        """Calcule le poids et volume total de la commande."""
        self.total_weight = sum(item.product.weight * item.quantity 
                               for item in self.items if item.product)
        self.total_volume = sum(item.product.volume * item.quantity 
                               for item in self.items if item.product)
    
    def get_all_products(self) -> List[Tuple[Product, int]]:
        """Retourne la liste de tous les produits avec quantités."""
        return [(item.product, item.quantity) for item in self.items if item.product]
    
    def get_unique_locations(self) -> List[Location]:
        """Retourne la liste des emplacements uniques à visiter."""
        locations = set()
        for item in self.items:
            if item.product:
                locations.add(item.product.location)
        return list(locations)
    
    def has_incompatibilities(self) -> bool:
        """Vérifie si la commande contient des produits incompatibles."""
        products = [item.product for item in self.items if item.product]
        for i, p1 in enumerate(products):
            for p2 in products[i+1:]:
                if not p1.is_compatible_with(p2):
                    return True
        return False
    
    def time_to_deadline(self) -> int:
        """Retourne le temps disponible en minutes."""
        # Format simplifié : on suppose que tout se passe le même jour
        received_h, received_m = map(int, self.received_time.split(':'))
        deadline_h, deadline_m = map(int, self.deadline.split(':'))
        
        received_minutes = received_h * 60 + received_m
        deadline_minutes = deadline_h * 60 + deadline_m
        
        return deadline_minutes - received_minutes
    
    def __repr__(self):
        return f"Order({self.id}, {len(self.items)} items, priority={self.priority})"


@dataclass
class Zone:
    """Zone de l'entrepôt."""
    name: str
    type: str
    coords: List[Location]
    restrictions: List[str] = field(default_factory=list)
    
    def contains(self, location: Location) -> bool:
        """Vérifie si une position est dans cette zone."""
        return location in self.coords


@dataclass
class Warehouse:
    """Structure de l'entrepôt."""
    width: int
    height: int
    entry_point: Location
    zones: Dict[str, Zone] = field(default_factory=dict)
    
    def get_zone_at(self, location: Location) -> Optional[str]:
        """Retourne l'identifiant de la zone à une position donnée."""
        for zone_id, zone in self.zones.items():
            if zone.contains(location):
                return zone_id
        return None
    
    def get_zone_type(self, location: Location) -> Optional[str]:
        """Retourne le type de zone à une position donnée."""
        zone_id = self.get_zone_at(location)
        if zone_id:
            return self.zones[zone_id].type
        return None
    
    def __repr__(self):
        return f"Warehouse({self.width}×{self.height}, {len(self.zones)} zones)"