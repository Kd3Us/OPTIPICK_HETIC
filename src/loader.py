"""
Module de chargement des données JSON.

Fonctions principales :
- load_warehouse : Charge la configuration de l'entrepôt
- load_products : Charge la liste des produits
- load_agents : Charge les agents (robots, humains, chariots)
- load_orders : Charge les commandes
"""

import json
from typing import List, Dict
from pathlib import Path

from .models import (
    Warehouse, Zone, Location, Product, Agent, Robot, Human, Cart,
    Order, OrderItem
)


def load_warehouse(filepath: str) -> Warehouse:
    """
    Charge la configuration de l'entrepôt depuis un fichier JSON.
    
    Args:
        filepath: Chemin vers warehouse.json
        
    Returns:
        Objet Warehouse configuré
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Point d'entrée
    entry = Location(data['entry_point'][0], data['entry_point'][1])
    
    # Zones
    zones = {}
    for zone_id, zone_data in data['zones'].items():
        coords = [Location(x, y) for x, y in zone_data['coords']]
        zones[zone_id] = Zone(
            name=zone_data['name'],
            type=zone_data['type'],
            coords=coords,
            restrictions=zone_data.get('restrictions', [])
        )
    
    warehouse = Warehouse(
        width=data['dimensions']['width'],
        height=data['dimensions']['height'],
        entry_point=entry,
        zones=zones
    )
    
    return warehouse


def load_products(filepath: str) -> List[Product]:
    """
    Charge la liste des produits depuis un fichier JSON.
    
    Args:
        filepath: Chemin vers products.json
        
    Returns:
        Liste d'objets Product
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = []
    for item in data:
        location = Location(item['location'][0], item['location'][1])
        product = Product(
            id=item['id'],
            name=item['name'],
            category=item['category'],
            weight=item['weight'],
            volume=item['volume'],
            location=location,
            frequency=item['frequency'],
            fragile=item['fragile'],
            incompatible_with=item.get('incompatible_with', [])
        )
        products.append(product)
    
    return products


def load_agents(filepath: str) -> List[Agent]:
    """
    Charge les agents depuis un fichier JSON.
    
    Args:
        filepath: Chemin vers agents.json
        
    Returns:
        Liste d'objets Agent (Robot, Human, Cart)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    agents = []
    for item in data:
        agent_type = item['type']
        
        if agent_type == 'robot':
            agent = Robot(
                id=item['id'],
                capacity_weight=item['capacity_weight'],
                capacity_volume=item['capacity_volume'],
                speed=item['speed'],
                cost_per_hour=item['cost_per_hour'],
                restrictions=item.get('restrictions', {})
            )
        elif agent_type == 'human':
            agent = Human(
                id=item['id'],
                capacity_weight=item['capacity_weight'],
                capacity_volume=item['capacity_volume'],
                speed=item['speed'],
                cost_per_hour=item['cost_per_hour'],
                restrictions=item.get('restrictions', {})
            )
        elif agent_type == 'cart':
            agent = Cart(
                id=item['id'],
                capacity_weight=item['capacity_weight'],
                capacity_volume=item['capacity_volume'],
                speed=item['speed'],
                cost_per_hour=item['cost_per_hour'],
                restrictions=item.get('restrictions', {})
            )
        else:
            raise ValueError(f"Type d'agent inconnu : {agent_type}")
        
        agents.append(agent)
    
    return agents


def load_orders(filepath: str, products: List[Product]) -> List[Order]:
    """
    Charge les commandes depuis un fichier JSON.
    
    Args:
        filepath: Chemin vers orders.json
        products: Liste des produits (pour faire le lien)
        
    Returns:
        Liste d'objets Order
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Créer un dictionnaire produit_id -> Product pour lookup rapide
    products_dict = {p.id: p for p in products}
    
    orders = []
    for item in data:
        # Créer les items de commande
        order_items = []
        for order_item_data in item['items']:
            product_id = order_item_data['product_id']
            quantity = order_item_data['quantity']
            
            order_item = OrderItem(
                product_id=product_id,
                quantity=quantity,
                product=products_dict.get(product_id)
            )
            order_items.append(order_item)
        
        # Créer la commande
        order = Order(
            id=item['id'],
            received_time=item['received_time'],
            deadline=item['deadline'],
            priority=item['priority'],
            items=order_items
        )
        
        # Calculer totaux
        order.calculate_totals()
        
        orders.append(order)
    
    return orders


def load_all_data(data_dir: str = 'data') -> Dict:
    """
    Charge toutes les données en une seule fois.
    
    Args:
        data_dir: Répertoire contenant les fichiers JSON
        
    Returns:
        Dictionnaire avec les clés : warehouse, products, agents, orders
    """
    data_path = Path(data_dir)
    
    warehouse = load_warehouse(str(data_path / 'warehouse.json'))
    products = load_products(str(data_path / 'products.json'))
    agents = load_agents(str(data_path / 'agents.json'))
    orders = load_orders(str(data_path / 'orders.json'), products)
    
    return {
        'warehouse': warehouse,
        'products': products,
        'agents': agents,
        'orders': orders
    }