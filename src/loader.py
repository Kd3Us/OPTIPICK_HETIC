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