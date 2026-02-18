<<<<<<< HEAD
"""
JSON data loading utilities.

Functions:
    load_warehouse  -- load warehouse configuration
    load_products   -- load product list
    load_agents     -- load agents (robots, humans, carts)
    load_orders     -- load customer orders
    load_all_data   -- load all data in one call
"""

import json
from typing import List, Dict
from pathlib import Path

from .models import (
    Warehouse, Zone, Location, Product, Agent, Robot, Human, Cart,
    Order, OrderItem
)


def load_warehouse(filepath: str) -> Warehouse:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    entry = Location(data['entry_point'][0], data['entry_point'][1])

    zones = {}
    for zone_id, zone_data in data['zones'].items():
        coords = [Location(x, y) for x, y in zone_data['coords']]
        zones[zone_id] = Zone(
            name=zone_data['name'],
            type=zone_data['type'],
            coords=coords,
            restrictions=zone_data.get('restrictions', [])
        )

    return Warehouse(
        width=data['dimensions']['width'],
        height=data['dimensions']['height'],
        entry_point=entry,
        zones=zones
    )


def load_products(filepath: str) -> List[Product]:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    products = []
    for item in data:
        location = Location(item['location'][0], item['location'][1])
        products.append(Product(
            id=item['id'],
            name=item['name'],
            category=item['category'],
            weight=item['weight'],
            volume=item['volume'],
            location=location,
            frequency=item['frequency'],
            fragile=item['fragile'],
            incompatible_with=item.get('incompatible_with', [])
        ))

    return products


def load_agents(filepath: str) -> List[Agent]:
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
            raise ValueError(f"Unknown agent type: {agent_type}")

        agents.append(agent)

    return agents


def load_orders(filepath: str, products: List[Product]) -> List[Order]:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    products_dict = {p.id: p for p in products}

    orders = []
    for item in data:
        order_items = []
        for order_item_data in item['items']:
            product_id = order_item_data['product_id']
            order_items.append(OrderItem(
                product_id=product_id,
                quantity=order_item_data['quantity'],
                product=products_dict.get(product_id)
            ))

        order = Order(
            id=item['id'],
            received_time=item['received_time'],
            deadline=item['deadline'],
            priority=item['priority'],
            items=order_items
        )
        order.calculate_totals()
        orders.append(order)

    return orders


def load_all_data(data_dir: str = 'data') -> Dict:
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
=======
import json
from datetime import datetime, timedelta
from src.constraints import validate_allocation, get_final_delivery_time

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # 1. Chargement
    products_list = load_json('data/products.json')
    orders = load_json('data/orders.json')
    agents = load_json('data/agents.json')
    warehouse = load_json('data/warehouse.json')
    
    products_dict = {p['id']: p for p in products_list}

    #  DEFINITION DES COÛTS (par minute ou par mission)
    # On définit une priorité : Robot (0) < Chariot (1) < Humain (2)
    cost_priority = {"robot": 0, "cart": 1, "human": 2}
    
    #  INITIALISATION DU TEMPS POUR CHAQUE AGENT
    # Tous les agents commencent à l'heure de la première commande (ex: 08:00)
    for agent in agents:
        agent['available_at'] = "08:00" 

    # Trier les agents par coût (le moins cher en premier)
    agents.sort(key=lambda x: cost_priority.get(x['type'], 99))

    print(" Début de l'optimisation par coût et temps...\n")

    results = []

    for order in orders:
        order_id = order['id']
        order_received = order['received_time']
        
        order_products = [products_dict[item['product_id']] for item in order['items'] if item['product_id'] in products_dict]

        allocated = False
        
        # On teste les agents (déjà triés par coût)
        for agent in agents:
            # --- GESTION DU TEMPS ---
            # L'agent ne peut commencer que s'il a fini sa tâche précédente 
            # ET que la commande est arrivée.
            start_work_time = max(agent['available_at'], order_received)
            
            # On crée une copie temporaire de la commande avec la nouvelle heure de début
            # pour que get_final_delivery_time calcule correctement l'arrivée
            temp_order = order.copy()
            temp_order['received_time'] = start_work_time

            # --- VALIDATION ---
            success, errors = validate_allocation(agent, temp_order, order_products, warehouse)

            if success:
                # Calcul de l'heure de fin pour mettre à jour l'agent
                finish_time = get_final_delivery_time(agent, temp_order, products_dict, warehouse)
                
                print(f" Commande {order_id} -> {agent['id']} ({agent['type']}) | Finit à: {finish_time}")
                
                # Mise à jour de la disponibilité de l'agent pour la prochaine commande
                agent['available_at'] = finish_time
                
                results.append({
                    "order_id": order_id,
                    "agent_id": agent['id'],
                    "finish_time": finish_time
                })
                allocated = True
                break 
        
        if not allocated:
            print(f" Commande {order_id} : Impossible d'allouer (Coût/Temps/Contraintes)")

    print(f"\n Optimisation terminée : {len(results)}/{len(orders)} commandes planifiées.")

if __name__ == "__main__":
    main()
>>>>>>> emery
