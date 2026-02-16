"""
Tests unitaires pour le module constraints.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Robot, Human, Cart, Product, Order, OrderItem, Location, Warehouse, Zone
from src.constraints import ConstraintChecker


class TestConstraintChecker:
    """Tests pour le vérificateur de contraintes."""
    
    def setup_method(self):
        """Setup avant chaque test."""
        # Créer un entrepôt simple
        zones = {
            'A': Zone('Electronics', 'electronics', [Location(1, 1)], []),
            'C': Zone('Food', 'food', [Location(8, 1)], ['robots_forbidden'])
        }
        self.warehouse = Warehouse(10, 8, Location(0, 0), zones)
        self.checker = ConstraintChecker(self.warehouse)
    
    def test_check_capacity_ok(self):
        """Test capacité respectée."""
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        
        p1 = Product("P001", "A", "cat", 5.0, 10.0, Location(1, 1), "high", False, [])
        item = OrderItem("P001", 2, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        order.calculate_totals()
        
        ok, msg = self.checker.check_capacity(agent, order)
        
        assert ok is True
        assert msg == "OK"
    
    def test_check_capacity_weight_exceeded(self):
        """Test dépassement de poids."""
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        
        p1 = Product("P001", "Heavy", "cat", 15.0, 5.0, Location(1, 1), "high", False, [])
        item = OrderItem("P001", 2, p1)  # 2x15 = 30kg > 20kg
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        order.calculate_totals()
        
        ok, msg = self.checker.check_capacity(agent, order)
        
        assert ok is False
        assert "poids" in msg.lower()
    
    def test_check_capacity_volume_exceeded(self):
        """Test dépassement de volume."""
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        
        p1 = Product("P001", "Bulky", "cat", 5.0, 20.0, Location(1, 1), "high", False, [])
        item = OrderItem("P001", 2, p1)  # 2x20 = 40dm³ > 30dm³
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        order.calculate_totals()
        
        ok, msg = self.checker.check_capacity(agent, order)
        
        assert ok is False
        assert "volume" in msg.lower()
    
    def test_check_product_compatibility_ok(self):
        """Test produits compatibles."""
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        
        ok, msg = self.checker.check_product_compatibility([p1, p2])
        
        assert ok is True
    
    def test_check_product_compatibility_incompatible(self):
        """Test produits incompatibles."""
        p1 = Product("P001", "A", "chemical", 1.0, 1.0, Location(0, 0), "high", False, ["P002"])
        p2 = Product("P002", "B", "food", 1.0, 1.0, Location(1, 1), "high", False, [])
        
        ok, msg = self.checker.check_product_compatibility([p1, p2])
        
        assert ok is False
        assert "incompatibles" in msg.lower()
    
    def test_check_robot_restrictions_fragile(self):
        """Test restriction robot sur objets fragiles."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True})
        
        p1 = Product("P001", "Glass", "cat", 2.0, 5.0, Location(1, 1), "high", True, [])
        item = OrderItem("P001", 1, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        
        ok, msg = self.checker.check_robot_restrictions(robot, order)
        
        assert ok is False
        assert "fragile" in msg.lower()
    
    def test_check_robot_restrictions_zone(self):
        """Test restriction robot sur zones interdites."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_zones': ['C']})
        
        p1 = Product("P001", "Milk", "food", 1.0, 1.0, Location(8, 1), "high", False, [])
        item = OrderItem("P001", 1, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        
        ok, msg = self.checker.check_robot_restrictions(robot, order)
        
        assert ok is False
        assert "zone" in msg.lower()
    
    def test_check_robot_restrictions_heavy_item(self):
        """Test restriction robot sur objets lourds."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'max_item_weight': 10})
        
        p1 = Product("P001", "Heavy", "cat", 15.0, 5.0, Location(1, 1), "high", False, [])
        item = OrderItem("P001", 1, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        
        ok, msg = self.checker.check_robot_restrictions(robot, order)
        
        assert ok is False
        assert "lourd" in msg.lower()
    
    def test_check_cart_assignment_ok(self):
        """Test chariot avec humain assigné."""
        cart = Cart("C1", 50, 80, 1.2, 3, {'requires_human': True})
        human = Human("H1", 35, 50, 1.5, 25)
        cart.assigned_human = human
        
        ok, msg = self.checker.check_cart_assignment(cart)
        
        assert ok is True
    
    def test_check_cart_assignment_failed(self):
        """Test chariot sans humain."""
        cart = Cart("C1", 50, 80, 1.2, 3, {'requires_human': True})
        
        ok, msg = self.checker.check_cart_assignment(cart)
        
        assert ok is False
        assert "humain" in msg.lower()
    
    def test_can_assign_order_success(self):
        """Test assignation réussie."""
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        
        p1 = Product("P001", "USB", "electronics", 0.1, 0.5, Location(1, 1), "high", False, [])
        item = OrderItem("P001", 2, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        order.calculate_totals()
        
        ok, errors = self.checker.can_assign_order(robot, order)
        
        assert ok is True
        assert len(errors) == 0
    
    def test_can_assign_order_multiple_violations(self):
        """Test assignation avec plusieurs violations."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True, 'no_zones': ['C']})
        
        p1 = Product("P001", "Glass", "food", 25.0, 5.0, Location(8, 1), "high", True, [])
        item = OrderItem("P001", 1, p1)
        order = Order("O001", "08:00", "10:00", "standard", items=[item])
        order.calculate_totals()
        
        ok, errors = self.checker.can_assign_order(robot, order)
        
        assert ok is False
        assert len(errors) > 1  # Plusieurs erreurs


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])