"""
Module d'optimisation globale avec OR-Tools CP-SAT.

Optimise l'allocation commandes → agents en prenant en compte
toutes les contraintes simultanément.
"""

from typing import List, Dict, Tuple, Optional
from ortools.sat.python import cp_model
import time

from .models import Agent, Order, Product, Warehouse, Robot, Human, Cart
from .constraints import ConstraintChecker


class OptimalAllocator:
    """Optimise l'allocation avec CP-SAT."""
    
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        self.checker = ConstraintChecker(warehouse)
        self.model = None
        self.solver = None
    
    def allocate(self, agents: List[Agent], orders: List[Order], 
                 max_time_seconds: int = 30) -> Dict:
        """
        Alloue les commandes aux agents de manière optimale.
        
        Args:
            agents: Liste des agents disponibles
            orders: Liste des commandes à assigner
            max_time_seconds: Temps maximum de résolution
            
        Returns:
            Dictionnaire avec les résultats
        """
        # Réinitialiser les agents
        for agent in agents:
            agent.reset_load()
        
        n_agents = len(agents)
        n_orders = len(orders)
        
        # Créer le modèle
        model = cp_model.CpModel()
        
        # ====================================================================
        # VARIABLES DE DÉCISION
        # ====================================================================
        
        # assign[i][j] = 1 si la commande i est assignée à l'agent j
        assign = {}
        for i in range(n_orders):
            for j in range(n_agents):
                assign[(i, j)] = model.NewBoolVar(f'assign_o{i}_a{j}')
        
        # load_weight[j] = poids total porté par l'agent j
        load_weight = {}
        for j in range(n_agents):
            load_weight[j] = model.NewIntVar(
                0, 
                int(agents[j].capacity_weight * 100),  # Multiplier par 100 pour gérer les décimales
                f'load_weight_a{j}'
            )
        
        # load_volume[j] = volume total porté par l'agent j
        load_volume = {}
        for j in range(n_agents):
            load_volume[j] = model.NewIntVar(
                0,
                int(agents[j].capacity_volume * 100),
                f'load_volume_a{j}'
            )
        
        # ====================================================================
        # CONTRAINTES
        # ====================================================================
        
        # C1 : Chaque commande doit être assignée à exactement un agent
        for i in range(n_orders):
            model.Add(sum(assign[(i, j)] for j in range(n_agents)) == 1)
        
        # C2 : Contraintes de capacité (poids)
        for j in range(n_agents):
            model.Add(
                load_weight[j] == sum(
                    assign[(i, j)] * int(orders[i].total_weight * 100)
                    for i in range(n_orders)
                )
            )
            model.Add(load_weight[j] <= int(agents[j].capacity_weight * 100))
        
        # C3 : Contraintes de capacité (volume)
        for j in range(n_agents):
            model.Add(
                load_volume[j] == sum(
                    assign[(i, j)] * int(orders[i].total_volume * 100)
                    for i in range(n_orders)
                )
            )
            model.Add(load_volume[j] <= int(agents[j].capacity_volume * 100))
        
        # C4 : Restrictions des robots
        for j in range(n_agents):
            agent = agents[j]
            if isinstance(agent, Robot):
                for i in range(n_orders):
                    order = orders[i]
                    
                    # Vérifier si le robot peut traiter cette commande
                    can_assign, _ = self.checker.check_robot_restrictions(agent, order)
                    
                    if not can_assign:
                        # Interdire cette assignation
                        model.Add(assign[(i, j)] == 0)
        
        # C5 : Incompatibilités de produits (simplifié)
        for i in range(n_orders):
            if orders[i].has_incompatibilities():
                # Cette commande ne peut pas être combinée avec d'autres
                # On pourrait ajouter des contraintes plus sophistiquées ici
                pass
        
        # ====================================================================
        # FONCTION OBJECTIF
        # ====================================================================
        
        # Objectif : Minimiser le coût total
        # Coût = priorité aux robots (moins chers) + équilibrage de charge
        
        objective_terms = []
        
        # Terme 1 : Pénaliser l'utilisation d'humains (plus chers)
        for j in range(n_agents):
            agent = agents[j]
            cost_factor = int(agent.cost_per_hour)
            
            for i in range(n_orders):
                objective_terms.append(assign[(i, j)] * cost_factor * 100)
        
        # Terme 2 : Équilibrage de charge (minimiser l'écart-type)
        # Simplifié : pénaliser les agents sous-utilisés
        for j in range(n_agents):
            # Bonus si l'agent est bien utilisé
            objective_terms.append(-load_weight[j])
        
        model.Minimize(sum(objective_terms))
        
        # ====================================================================
        # RÉSOLUTION
        # ====================================================================
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_seconds
        solver.parameters.log_search_progress = False
        
        start_time = time.time()
        status = solver.Solve(model)
        solve_time = time.time() - start_time
        
        # ====================================================================
        # EXTRACTION DE LA SOLUTION
        # ====================================================================
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Assigner les commandes
            successful_assignments = []
            
            for i in range(n_orders):
                for j in range(n_agents):
                    if solver.Value(assign[(i, j)]) == 1:
                        order = orders[i]
                        agent = agents[j]
                        
                        # Assigner
                        agent.assigned_orders.append(order)
                        agent.current_load_weight += order.total_weight
                        agent.current_load_volume += order.total_volume
                        
                        for item in order.items:
                            if item.product:
                                for _ in range(item.quantity):
                                    agent.current_products.append(item.product)
                        
                        order.assigned_agent = agent
                        
                        successful_assignments.append({
                            'order_id': order.id,
                            'agent_id': agent.id,
                            'agent_type': agent.type
                        })
            
            return {
                'status': 'optimal' if status == cp_model.OPTIMAL else 'feasible',
                'successful': successful_assignments,
                'failed': [],
                'total_orders': n_orders,
                'assigned_orders': len(successful_assignments),
                'failed_orders': 0,
                'solve_time_seconds': solve_time,
                'objective_value': solver.ObjectiveValue()
            }
        else:
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
    """Regroupe des commandes compatibles pour optimiser les tournées."""
    
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        self.checker = ConstraintChecker(warehouse)
    
    def can_batch_orders(self, order1: Order, order2: Order, agent: Agent) -> Tuple[bool, str]:
        """
        Vérifie si deux commandes peuvent être groupées pour un agent.
        
        Args:
            order1, order2: Commandes à grouper
            agent: Agent qui traiterait le groupe
            
        Returns:
            (True/False, raison)
        """
        # Vérifier la capacité
        total_weight = order1.total_weight + order2.total_weight
        total_volume = order1.total_volume + order2.total_volume
        
        if total_weight > agent.capacity_weight:
            return False, "Dépassement de capacité en poids"
        
        if total_volume > agent.capacity_volume:
            return False, "Dépassement de capacité en volume"
        
        # Vérifier les incompatibilités entre produits des deux commandes
        all_products = []
        for order in [order1, order2]:
            for item in order.items:
                if item.product:
                    all_products.append(item.product)
        
        ok, msg = self.checker.check_product_compatibility(all_products)
        if not ok:
            return False, f"Incompatibilités : {msg}"
        
        # Vérifier les deadlines (prendre la plus stricte)
        min_deadline = min(
            self.checker._time_to_minutes(order1.deadline),
            self.checker._time_to_minutes(order2.deadline)
        )
        
        # Estimer si c'est faisable
        # (Simplification : on suppose que oui si les contraintes précédentes passent)
        
        return True, "OK"
    
    def find_batchable_orders(self, orders: List[Order], agent: Agent) -> List[List[Order]]:
        """
        Trouve des groupes de commandes qui peuvent être traitées ensemble.
        
        Args:
            orders: Liste de commandes
            agent: Agent pour lequel on groupe
            
        Returns:
            Liste de groupes (chaque groupe est une liste de commandes)
        """
        batches = []
        used_orders = set()
        
        for i, order1 in enumerate(orders):
            if order1.id in used_orders:
                continue
            
            batch = [order1]
            used_orders.add(order1.id)
            
            # Chercher des commandes compatibles
            for j, order2 in enumerate(orders):
                if i != j and order2.id not in used_orders:
                    # Tester si on peut ajouter order2 au batch
                    can_add = True
                    
                    for order_in_batch in batch:
                        ok, _ = self.can_batch_orders(order_in_batch, order2, agent)
                        if not ok:
                            can_add = False
                            break
                    
                    if can_add:
                        # Vérifier la capacité totale du batch
                        total_weight = sum(o.total_weight for o in batch) + order2.total_weight
                        total_volume = sum(o.total_volume for o in batch) + order2.total_volume
                        
                        if (total_weight <= agent.capacity_weight and 
                            total_volume <= agent.capacity_volume):
                            batch.append(order2)
                            used_orders.add(order2.id)
            
            batches.append(batch)
        
        return batches
    
    def calculate_batching_benefit(self, batch: List[Order]) -> float:
        """
        Calcule le gain de distance en groupant des commandes.
        
        Args:
            batch: Groupe de commandes
            
        Returns:
            Gain estimé en mètres
        """
        if len(batch) <= 1:
            return 0.0
        
        # Distance si traitées séparément
        separate_distance = 0.0
        for order in batch:
            for loc in order.get_unique_locations():
                separate_distance += self.warehouse.entry_point.distance_to(loc) * 2  # Aller-retour
        
        # Distance si traitées ensemble
        all_locations = set()
        for order in batch:
            all_locations.update(order.get_unique_locations())
        
        combined_distance = 0.0
        for loc in all_locations:
            combined_distance += self.warehouse.entry_point.distance_to(loc) * 2
        
        return separate_distance - combined_distance