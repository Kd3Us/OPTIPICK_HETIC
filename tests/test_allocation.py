"""
Tests unitaires pour le module allocation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Robot, Human, Product, Order, OrderItem, Location, Warehouse, Zone
from src.allocation import GreedyAllocation


class TestGreedyAllocation:
    """Tests pour l'allocation gloutonne."""
    
    def setup_method(self):
        """Setup avant chaque test."""
        zones = {
            'A': Zone('Electronics', 'electronics', [Location(1, 1), Location(2, 1)], []),
            'C': Zone('Food', 'food', [Location(8, 1)], ['robots_forbidden'])
        }
        self.warehouse = Warehouse(10, 8, Location(0, 0), zones)
    
    def test_allocation_single_order_robot(self):
        """Test allocation d'une commande simple à un robot."""
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        agents = [robot]
        
        p1 = Product("P001", "USB", "electronics", 0.5, 1.0, Location(1, 1), "high", False, [])
        item = OrderItem("P001", 2, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        order.calculate_totals()
        orders = [order]
        
        allocator = GreedyAllocation(self.warehouse)
        result = allocator.allocate(agents, orders)
        
        assert result['assigned_orders'] == 1
        assert result['failed_orders'] == 0
    
    def test_allocation_robot_preferred(self):
        """Test que les robots sont utilisés en priorité (moins chers)."""
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        human = Human("H1", 35, 50, 1.5, 25)
        agents = [robot, human]
        
        p1 = Product("P001", "Mouse", "electronics", 0.3, 1.0, Location(1, 1), "high", False, [])
        item = OrderItem("P001", 1, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        order.calculate_totals()
        orders = [order]
        
        allocator = GreedyAllocation(self.warehouse)
        result = allocator.allocate(agents, orders)
        
        # Le robot devrait être choisi
        assert robot.assigned_orders[0].id == "O001"
    
    def test_allocation_robot_cannot_fragile(self):
        """Test que les objets fragiles vont aux humains."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True})
        human = Human("H1", 35, 50, 1.5, 25)
        agents = [robot, human]
        
        p1 = Product("P001", "Glass", "electronics", 1.0, 2.0, Location(1, 1), "high", True, [])
        item = OrderItem("P001", 1, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        order.calculate_totals()
        orders = [order]
        
        allocator = GreedyAllocation(self.warehouse)
        result = allocator.allocate(agents, orders)
        
        # L'humain devrait avoir la commande
        assert human.assigned_orders[0].id == "O001"
    
    def test_allocation_express_priority(self):
        """Test que les commandes express sont traitées en premier."""
        robot = Robot("R1", 5, 10, 2.0, 5, {})  # Petite capacité
        agents = [robot]
        
        p1 = Product("P001", "A", "cat", 3.0, 5.0, Location(1, 1), "high", False, [])
        
        # Commande standard
        item1 = OrderItem("P001", 1, p1)
        order_standard = Order("O001", "08:00", "12:00", "standard", items=[item1])
        order_standard.calculate_totals()
        
        # Commande express
        item2 = OrderItem("P001", 1, p1)
        order_express = Order("O002", "08:00", "10:00", "express", items=[item2])
        order_express.calculate_totals()
        
        orders = [order_standard, order_express]  # Standard en premier dans la liste
        
        allocator = GreedyAllocation(self.warehouse)
        result = allocator.allocate(agents, orders)
        
        # L'express devrait être assignée en premier
        assert robot.assigned_orders[0].id == "O002"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])