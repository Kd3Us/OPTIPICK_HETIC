"""
Module de vérification des contraintes du système OptiPick.

Contraintes dures (obligatoires) :
- C1 : Capacité des agents (poids et volume)
- C2 : Incompatibilités de produits
- C3 : Restrictions des robots (zones, fragiles, poids)
- C4 : Chariots nécessitent un humain
- C5 : Respect des deadlines
- C6 : Complétude des commandes
"""

from typing import List, Tuple, Optional
from .models import Agent, Product, Order, Warehouse, Robot, Human, Cart, Location


class ConstraintChecker:
    """Classe pour vérifier toutes les contraintes du système."""
    
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
    
    # ========================================================================
    # C1 : CAPACITÉ DES AGENTS
    # ========================================================================
    
    def check_capacity(self, agent: Agent, order: Order) -> Tuple[bool, str]:
        """
        Vérifie si l'agent a la capacité de transporter la commande.
        
        Args:
            agent: Agent à vérifier
            order: Commande à transporter
            
        Returns:
            (True/False, message d'erreur)
        """
        # Calculer la charge actuelle + nouvelle commande
        total_weight = agent.current_load_weight + order.total_weight
        total_volume = agent.current_load_volume + order.total_volume
        
        # Vérifier poids
        if total_weight > agent.capacity_weight:
            return False, (f"Dépassement de capacité en poids : "
                          f"{total_weight:.2f}kg > {agent.capacity_weight}kg")
        
        # Vérifier volume
        if total_volume > agent.capacity_volume:
            return False, (f"Dépassement de capacité en volume : "
                          f"{total_volume:.2f}dm³ > {agent.capacity_volume}dm³")
        
        return True, "OK"
    
    # ========================================================================
    # C2 : INCOMPATIBILITÉS DE PRODUITS
    # ========================================================================
    
    def check_product_compatibility(self, products: List[Product]) -> Tuple[bool, str]:
        """
        Vérifie que tous les produits sont compatibles entre eux.
        
        Args:
            products: Liste de produits à vérifier
            
        Returns:
            (True/False, message d'erreur)
        """
        for i, p1 in enumerate(products):
            for p2 in products[i+1:]:
                if not p1.is_compatible_with(p2):
                    return False, (f"Produits incompatibles : {p1.id} ({p1.category}) "
                                  f"et {p2.id} ({p2.category})")
        
        return True, "OK"
    
    def check_order_compatibility(self, order: Order) -> Tuple[bool, str]:
        """
        Vérifie qu'une commande ne contient pas de produits incompatibles.
        
        Args:
            order: Commande à vérifier
            
        Returns:
            (True/False, message d'erreur)
        """
        products = [item.product for item in order.items if item.product]
        return self.check_product_compatibility(products)
    
    def check_agent_load_compatibility(self, agent: Agent) -> Tuple[bool, str]:
        """
        Vérifie que les produits actuellement chargés sont compatibles.
        
        Args:
            agent: Agent dont on vérifie la charge
            
        Returns:
            (True/False, message d'erreur)
        """
        return self.check_product_compatibility(agent.current_products)
    
    # ========================================================================
    # C3 : RESTRICTIONS DES ROBOTS
    # ========================================================================
    
    def check_robot_restrictions(self, robot: Robot, order: Order) -> Tuple[bool, str]:
        """
        Vérifie que le robot peut traiter la commande (zones, fragiles, poids).
        
        Args:
            robot: Robot à vérifier
            order: Commande à traiter
            
        Returns:
            (True/False, message d'erreur)
        """
        if not isinstance(robot, Robot):
            return True, "OK"  # Pas un robot, pas de restrictions
        
        # Vérifier les zones
        for item in order.items:
            if item.product:
                product = item.product
                zone = self.warehouse.get_zone_at(product.location)
                
                if not robot.can_access_zone(zone):
                    return False, (f"Robot ne peut pas accéder à la zone {zone} "
                                  f"(produit {product.id})")
        
        # Vérifier les objets fragiles
        if robot.restrictions.get('no_fragile', False):
            for item in order.items:
                if item.product and item.product.fragile:
                    return False, f"Robot ne peut pas transporter d'objets fragiles ({item.product.id})"
        
        # Vérifier le poids individuel des items
        max_item_weight = robot.restrictions.get('max_item_weight', float('inf'))
        for item in order.items:
            if item.product and item.product.weight > max_item_weight:
                return False, (f"Produit {item.product.id} trop lourd : "
                              f"{item.product.weight}kg > {max_item_weight}kg")
        
        return True, "OK"
    
    # ========================================================================
    # C4 : CHARIOTS NÉCESSITENT UN HUMAIN
    # ========================================================================
    
    def check_cart_assignment(self, cart: Cart) -> Tuple[bool, str]:
        """
        Vérifie qu'un chariot a un humain assigné.
        
        Args:
            cart: Chariot à vérifier
            
        Returns:
            (True/False, message d'erreur)
        """
        if not isinstance(cart, Cart):
            return True, "OK"  # Pas un chariot
        
        if not cart.is_operational():
            return False, f"Chariot {cart.id} nécessite un humain assigné"
        
        return True, "OK"
    
    def can_assign_human_to_cart(self, human: Human, cart: Cart) -> Tuple[bool, str]:
        """
        Vérifie si un humain peut être assigné à un chariot.
        
        Args:
            human: Humain à assigner
            cart: Chariot cible
            
        Returns:
            (True/False, message d'erreur)
        """
        if not isinstance(human, Human):
            return False, "L'agent n'est pas un humain"
        
        if not isinstance(cart, Cart):
            return False, "L'agent n'est pas un chariot"
        
        # Vérifier que l'humain n'est pas déjà assigné à un autre chariot
        if human.assigned_cart is not None and human.assigned_cart != cart:
            return False, f"Humain {human.id} déjà assigné au chariot {human.assigned_cart.id}"
        
        # Vérifier que le chariot n'a pas déjà un autre humain
        if cart.assigned_human is not None and cart.assigned_human != human:
            return False, f"Chariot {cart.id} déjà assigné à l'humain {cart.assigned_human.id}"
        
        return True, "OK"
    
    # ========================================================================
    # C5 : RESPECT DES DEADLINES
    # ========================================================================
    
    def check_deadline_feasible(self, agent: Agent, order: Order, 
                                current_time_minutes: int = 0) -> Tuple[bool, str]:
        """
        Vérifie si l'agent peut terminer la commande avant la deadline.
        
        Args:
            agent: Agent qui va traiter la commande
            order: Commande à traiter
            current_time_minutes: Temps actuel en minutes depuis minuit
            
        Returns:
            (True/False, message d'erreur)
        """
        # Temps disponible
        deadline_minutes = self._time_to_minutes(order.deadline)
        available_time = deadline_minutes - current_time_minutes
        
        # Estimer le temps nécessaire
        # Distance moyenne estimée : somme des distances entre emplacements + retour
        locations = order.get_unique_locations()
        if not locations:
            return True, "OK"
        
        # Estimation simple : distance totale depuis l'entrée vers chaque emplacement
        total_distance = 0
        for loc in locations:
            total_distance += self.warehouse.entry_point.distance_to(loc)
        
        # Temps de déplacement (en minutes) + temps de ramassage (30s par produit)
        travel_time = (total_distance / agent.speed) / 60  # Convertir en minutes
        picking_time = len(order.items) * 0.5  # 30 secondes par item
        total_time = travel_time + picking_time
        
        if total_time > available_time:
            return False, (f"Temps insuffisant : {total_time:.1f}min nécessaires, "
                          f"{available_time:.1f}min disponibles")
        
        return True, "OK"
    
    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convertit une heure 'HH:MM' en minutes depuis minuit."""
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    
    # ========================================================================
    # VÉRIFICATION GLOBALE
    # ========================================================================
    
    def can_assign_order(self, agent: Agent, order: Order, 
                        current_time_minutes: int = 0) -> Tuple[bool, List[str]]:
        """
        Vérifie toutes les contraintes pour assigner une commande à un agent.
        
        Args:
            agent: Agent candidat
            order: Commande à assigner
            current_time_minutes: Temps actuel
            
        Returns:
            (True/False, liste des erreurs)
        """
        errors = []
        
        # C1 : Capacité
        ok, msg = self.check_capacity(agent, order)
        if not ok:
            errors.append(f"[C1 Capacité] {msg}")
        
        # C2 : Incompatibilités dans la commande
        ok, msg = self.check_order_compatibility(order)
        if not ok:
            errors.append(f"[C2 Incompatibilité] {msg}")
        
        # C3 : Restrictions robots
        if isinstance(agent, Robot):
            ok, msg = self.check_robot_restrictions(agent, order)
            if not ok:
                errors.append(f"[C3 Restrictions Robot] {msg}")
        
        # C4 : Chariot nécessite humain
        if isinstance(agent, Cart):
            ok, msg = self.check_cart_assignment(agent)
            if not ok:
                errors.append(f"[C4 Chariot] {msg}")
        
        # C5 : Deadline
        ok, msg = self.check_deadline_feasible(agent, order, current_time_minutes)
        if not ok:
            errors.append(f"[C5 Deadline] {msg}")
        
        return len(errors) == 0, errors
    
    def validate_solution(self, agents: List[Agent], orders: List[Order]) -> Tuple[bool, List[str]]:
        """
        Valide une solution complète (toutes les allocations).
        
        Args:
            agents: Liste des agents avec leurs assignments
            orders: Liste des commandes
            
        Returns:
            (True/False, liste des erreurs)
        """
        errors = []
        
        # Vérifier que toutes les commandes sont assignées (C6)
        assigned_orders = set()
        for agent in agents:
            for order in agent.assigned_orders:
                assigned_orders.add(order.id)
        
        for order in orders:
            if order.id not in assigned_orders:
                errors.append(f"[C6 Complétude] Commande {order.id} non assignée")
        
        # Vérifier les contraintes pour chaque agent
        for agent in agents:
            for order in agent.assigned_orders:
                ok, agent_errors = self.can_assign_order(agent, order)
                if not ok:
                    errors.extend([f"Agent {agent.id}: {err}" for err in agent_errors])
        
        return len(errors) == 0, errors


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def are_products_compatible(p1: Product, p2: Product) -> bool:
    """Vérifie si deux produits sont compatibles."""
    return p1.is_compatible_with(p2)


def can_products_share_cart(products: List[Product]) -> bool:
    """Vérifie si une liste de produits peut partager un chariot."""
    checker = ConstraintChecker(None)
    ok, _ = checker.check_product_compatibility(products)
    return ok