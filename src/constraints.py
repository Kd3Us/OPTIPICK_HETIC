from datetime import datetime, timedelta
from typing import List, Tuple

# 1. Capacité
def check_capacity(agent, products: list) -> Tuple[bool, str]:
    total_weight = sum(product["weight"] for product in products)
    total_volume = sum(product["volume"] for product in products)

    if total_weight > agent["capacity_weight"]:
        return False, "capacité de poids dépassée"
    if total_volume > agent["capacity_volume"]:
        return False, "capacité de volume dépassée"
    return True, ""

# 2. Incompatibilités (avec correction de la casse)
def check_incompatibilities(products: list) -> Tuple[bool, str]:
    for i in range(len(products)):
        for j in range(i + 1, len(products)):
            p_a = products[i]
            p_b = products[j]

            id_a = str(p_a["id"]).upper()
            id_b = str(p_b["id"]).upper()
            incomp_a = [str(x).upper() for x in p_a.get("incompatible_with", [])]
            incomp_b = [str(x).upper() for x in p_b.get("incompatible_with", [])]

            if id_a in incomp_b or id_b in incomp_a:
                return False, f"Produit {id_a} incompatible avec {id_b}"
    return True, ""

# 3. Restrictions Robot
def check_rebot_restructions(robot, product_list: list, warehouse_data) -> Tuple[bool, str]:
    forbidden_coords = warehouse_data["zones"]["C"]["coords"]
    restrictions = robot.get("restrictions", {})
    no_zones = restrictions.get("no_zones", [])
    no_fragile = restrictions.get("no_fragile", False)
    max_item_weight = restrictions.get("max_item_weight", None)

    for p in product_list:
        if p["location"] in forbidden_coords:
            return False, f"Robot {robot['id']} interdit en Zone C"
        if p.get("zone") in no_zones:
            return False, f"Zone {p['zone']} interdite pour {robot['id']}"
        if no_fragile and p.get("fragile", False):
            return False, f"Robot {robot['id']} ne peut pas transporter de produit fragile {p['id']}"
        if max_item_weight is not None and p.get("weight", 0) > max_item_weight:
            return False, f"Produit {p['id']} dépasse le poids max autorisé"
    return True, ""

# 4. Assignation Chariot
def check_cart_assigment(cart, human):
    restrictions = cart.get('restrictions', {})
    requires_human = restrictions.get('requires_human', True)
    if requires_human and human is None:
        return False, f"{cart['id']} nécessite un humain"
    return True, ""

# 5. Calculs de distance et temps
def calculate_dist(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def get_total_path_distance(order, products_dict, warehouse_data):
    entry = warehouse_data["entry_point"]
    total_dist = 0
    current_pos = entry
    for item in order["items"]:
        product_pos = products_dict[item["product_id"]]["location"]
        total_dist += calculate_dist(current_pos, product_pos)
        current_pos = product_pos
    total_dist += calculate_dist(current_pos, entry)
    return total_dist

def get_final_delivery_time(agent, order, products_dict, warehouse_data):
    distance = get_total_path_distance(order, products_dict, warehouse_data)
    travel_time = distance / agent["speed"]
    picking_time = sum(item["quantity"] for item in order["items"]) * 30
    duration_minutes = (travel_time + picking_time) / 60
    
    start_time = datetime.strptime(order["received_time"], "%H:%M")
    end_time = start_time + timedelta(minutes=duration_minutes)
    return end_time.strftime("%H:%M")

# 6. Validation Globale
def validate_allocation(agent, order, products, warehouse_data, human=None) -> Tuple[bool, List[str]]:
    errors = []
    
    # On crée un dictionnaire local pour les fonctions de calcul
    products_dict = {p["id"]: p for p in products}

    # Capacité
    is_cap_ok, cap_msg = check_capacity(agent, products)
    if not is_cap_ok: errors.append(cap_msg)

    # Incompatibilités
    is_inc_ok, inc_msg = check_incompatibilities(products)
    if not is_inc_ok: errors.append(inc_msg)

    # Restrictions par type
    if agent.get("type") == "robot":
        is_rob_ok, rob_msg = check_rebot_restructions(agent, products, warehouse_data)
        if not is_rob_ok: errors.append(rob_msg)
    elif agent.get("type") == "cart":
        is_cart_ok, cart_msg = check_cart_assigment(agent, human)
        if not is_cart_ok: errors.append(cart_msg)

    # Deadline
    final_time_str = get_final_delivery_time(agent, order, products_dict, warehouse_data)
    if final_time_str > order["deadline"]:
        errors.append(f"Deadline dépassée : {final_time_str} > {order['deadline']}")

    return len(errors) == 0, errors