"""
Module d'allocation des commandes aux agents.

Stratégies :
- Greedy : Allocation gloutonne simple (First-Fit)
- Priority : Priorisation par urgence
"""

from typing import List, Dict, Optional, Tuple
from .models import Agent, Order, Robot, Human, Cart, Warehouse
from .constraints import ConstraintChecker


class AllocationStrategy:
    """Classe de base pour les stratégies d'allocation."""
    
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        self.checker = ConstraintChecker(warehouse)
    
    def allocate(self, agents: List[Agent], orders: List[Order]) -> Dict[str, any]:
        """
        Alloue les commandes aux agents.
        
        Returns:
            Dictionnaire avec les résultats
        """
        raise NotImplementedError


class GreedyAllocation(AllocationStrategy):
    """
    Allocation gloutonne (First-Fit).
    
    Stratégie :
    1. Trier les commandes par priorité puis deadline
    2. Pour chaque commande, assigner au premier agent valide
    3. Prioriser les robots (moins chers)
    """
    
    def allocate(self, agents: List[Agent], orders: List[Order]) -> Dict[str, any]:
        """Allocation gloutonne des commandes."""
        
        # Réinitialiser tous les agents
        for agent in agents:
            agent.reset_load()
        
        # Trier les commandes : express d'abord, puis par deadline
        sorted_orders = sorted(orders, 
                              key=lambda o: (0 if o.priority == 'express' else 1, 
                                           o.deadline))
        
        # Trier les agents : robots d'abord (moins chers), puis humains, puis chariots
        agent_priority = {Robot: 1, Human: 2, Cart: 3}
        sorted_agents = sorted(agents, 
                              key=lambda a: (agent_priority.get(type(a), 4), 
                                           a.cost_per_hour))
        
        # Résultats
        successful_assignments = []
        failed_assignments = []
        
        # Allouer chaque commande
        for order in sorted_orders:
            assigned = False
            
            for agent in sorted_agents:
                # Vérifier toutes les contraintes
                can_assign, errors = self.checker.can_assign_order(agent, order)
                
                if can_assign:
                    # Assigner la commande
                    agent.assigned_orders.append(order)
                    agent.current_load_weight += order.total_weight
                    agent.current_load_volume += order.total_volume
                    
                    # Ajouter les produits à la charge
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
                    
                    assigned = True
                    break
            
            if not assigned:
                # Trouver pourquoi aucun agent ne peut prendre cette commande
                all_errors = []
                for agent in sorted_agents:
                    _, errors = self.checker.can_assign_order(agent, order)
                    all_errors.append(f"{agent.id}: {', '.join(errors)}")
                
                failed_assignments.append({
                    'order_id': order.id,
                    'reasons': all_errors
                })
        
        return {
            'successful': successful_assignments,
            'failed': failed_assignments,
            'total_orders': len(orders),
            'assigned_orders': len(successful_assignments),
            'failed_orders': len(failed_assignments)
        }


class PriorityAllocation(AllocationStrategy):
    """
    Allocation avec priorité stricte.
    
    Les commandes express sont traitées en priorité absolue.
    """
    
    def allocate(self, agents: List[Agent], orders: List[Order]) -> Dict[str, any]:
        """Allocation par priorité."""
        
        # Séparer les commandes express et standard
        express_orders = [o for o in orders if o.priority == 'express']
        standard_orders = [o for o in orders if o.priority == 'standard']
        
        # Utiliser l'allocation gloutonne pour chaque groupe
        greedy = GreedyAllocation(self.warehouse)
        
        # Allouer les express d'abord
        result_express = greedy.allocate(agents, express_orders)
        
        # Puis les standard
        result_standard = greedy.allocate(agents, standard_orders)
        
        # Combiner les résultats
        return {
            'successful': result_express['successful'] + result_standard['successful'],
            'failed': result_express['failed'] + result_standard['failed'],
            'total_orders': len(orders),
            'assigned_orders': result_express['assigned_orders'] + result_standard['assigned_orders'],
            'failed_orders': result_express['failed_orders'] + result_standard['failed_orders'],
            'express_assigned': result_express['assigned_orders'],
            'standard_assigned': result_standard['assigned_orders']
        }


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def print_allocation_summary(result: Dict, agents: List[Agent]):
    """Affiche un résumé de l'allocation."""
    
    print("\n" + "=" * 70)
    print(" " * 25 + "RÉSUMÉ DE L'ALLOCATION")
    print("=" * 70)
    
    print(f"\n📊 Statistiques globales :")
    print(f"  Total commandes : {result['total_orders']}")
    print(f"  ✅ Assignées : {result['assigned_orders']} "
          f"({result['assigned_orders']/result['total_orders']*100:.1f}%)")
    print(f"  ❌ Échecs : {result['failed_orders']}")
    
    if 'express_assigned' in result:
        print(f"\n  Express assignées : {result['express_assigned']}")
        print(f"  Standard assignées : {result['standard_assigned']}")
    
    print(f"\n👥 Utilisation des agents :")
    for agent in agents:
        if agent.assigned_orders:
            utilization = (agent.current_load_weight / agent.capacity_weight * 100)
            print(f"  {agent.id} ({agent.type}) : "
                  f"{len(agent.assigned_orders)} commandes, "
                  f"{agent.current_load_weight:.2f}/{agent.capacity_weight}kg "
                  f"({utilization:.1f}%)")
    
    if result['failed']:
        print(f"\n❌ Commandes non assignées :")
        for fail in result['failed']:
            print(f"  {fail['order_id']} :")
            for reason in fail['reasons'][:2]:  # Afficher 2 raisons max
                print(f"    - {reason}")
    
    print("=" * 70)