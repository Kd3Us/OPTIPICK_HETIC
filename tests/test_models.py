"""
Tests unitaires pour les modèles de base.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Location, Product, Agent, Robot, Human, Cart, Order, OrderItem


class TestLocation:
    """Tests pour la classe Location."""
    
    def test_location_creation(self):
        """Test de création d'une location."""
        loc = Location(5, 3)
        assert loc.x == 5
        assert loc.y == 3
    
    def test_location_equality(self):
        """Test d'égalité entre locations."""
        loc1 = Location(2, 3)
        loc2 = Location(2, 3)
        loc3 = Location(2, 4)
        
        assert loc1 == loc2
        assert loc1 != loc3
    
    def test_manhattan_distance(self):
        """Test du calcul de distance de Manhattan."""
        loc1 = Location(0, 0)
        loc2 = Location(3, 4)
        
        assert loc1.distance_to(loc2) == 7  # |3-0| + |4-0| = 7
    
    def test_manhattan_distance_same_location(self):
        """Test distance entre même position."""
        loc = Location(5, 5)
        assert loc.distance_to(loc) == 0
    
    def test_location_hash(self):
        """Test que les locations peuvent être dans un set."""
        loc1 = Location(1, 2)
        loc2 = Location(1, 2)
        loc3 = Location(2, 3)
        
        locations = {loc1, loc2, loc3}
        assert len(locations) == 2  # loc1 et loc2 sont identiques


class TestProduct:
    """Tests pour la classe Product."""
    
    def test_product_creation(self):
        """Test de création d'un produit."""
        loc = Location(5, 3)
        product = Product(
            id="P001",
            name="Laptop",
            category="electronics",
            weight=2.5,
            volume=8.0,
            location=loc,
            frequency="high",
            fragile=True,
            incompatible_with=["P002"]
        )
        
        assert product.id == "P001"
        assert product.weight == 2.5
        assert product.fragile is True
    
    def test_product_compatibility_ok(self):
        """Test de compatibilité entre produits compatibles."""
        p1 = Product("P001", "A", "cat1", 1.0, 1.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat2", 1.0, 1.0, Location(1, 1), "high", False, [])
        
        assert p1.is_compatible_with(p2) is True
    
    def test_product_compatibility_incompatible(self):
        """Test d'incompatibilité entre produits."""
        p1 = Product("P001", "A", "cat1", 1.0, 1.0, Location(0, 0), "high", False, ["P002"])
        p2 = Product("P002", "B", "cat2", 1.0, 1.0, Location(1, 1), "high", False, [])
        
        assert p1.is_compatible_with(p2) is False
    
    def test_product_compatibility_bidirectional(self):
        """Test que l'incompatibilité est bidirectionnelle."""
        p1 = Product("P001", "A", "cat1", 1.0, 1.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat2", 1.0, 1.0, Location(1, 1), "high", False, ["P001"])
        
        assert p1.is_compatible_with(p2) is False
        assert p2.is_compatible_with(p1) is False


class TestAgent:
    """Tests pour les classes Agent."""
    
    def test_robot_creation(self):
        """Test de création d'un robot."""
        robot = Robot(
            id="R1",
            capacity_weight=20,
            capacity_volume=30,
            speed=2.0,
            cost_per_hour=5,
            restrictions={'no_fragile': True, 'no_zones': ['C']}
        )
        
        assert robot.id == "R1"
        assert robot.type == "robot"
        assert robot.capacity_weight == 20
    
    def test_human_creation(self):
        """Test de création d'un humain."""
        human = Human(
            id="H1",
            capacity_weight=35,
            capacity_volume=50,
            speed=1.5,
            cost_per_hour=25
        )
        
        assert human.id == "H1"
        assert human.type == "human"
    
    def test_agent_can_carry_ok(self):
        """Test que l'agent peut porter le produit."""
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "Test", "cat", 5.0, 10.0, Location(0, 0), "high", False, [])
        
        assert agent.can_carry(product, quantity=1) is True
    
    def test_agent_can_carry_weight_exceeded(self):
        """Test dépassement de capacité en poids."""
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "Heavy", "cat", 25.0, 10.0, Location(0, 0), "high", False, [])
        
        assert agent.can_carry(product, quantity=1) is False
    
    def test_agent_can_carry_volume_exceeded(self):
        """Test dépassement de capacité en volume."""
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        product = Product("P001", "Bulky", "cat", 5.0, 40.0, Location(0, 0), "high", False, [])
        
        assert agent.can_carry(product, quantity=1) is False
    
    def test_robot_cannot_carry_fragile(self):
        """Test que le robot refuse les objets fragiles."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_fragile': True})
        fragile_product = Product("P001", "Glass", "cat", 2.0, 5.0, Location(0, 0), "high", True, [])
        
        assert robot.can_carry(fragile_product) is False
    
    def test_robot_cannot_carry_too_heavy_item(self):
        """Test que le robot refuse les objets > 10kg."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'max_item_weight': 10})
        heavy_product = Product("P001", "Heavy", "cat", 15.0, 5.0, Location(0, 0), "high", False, [])
        
        assert robot.can_carry(heavy_product) is False
    
    def test_robot_can_access_zone_ok(self):
        """Test que le robot peut accéder à une zone autorisée."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_zones': ['C']})
        
        assert robot.can_access_zone('A') is True
        assert robot.can_access_zone('B') is True
    
    def test_robot_cannot_access_restricted_zone(self):
        """Test que le robot ne peut pas accéder à une zone interdite."""
        robot = Robot("R1", 20, 30, 2.0, 5, {'no_zones': ['C']})
        
        assert robot.can_access_zone('C') is False
    
    def test_cart_operational_with_human(self):
        """Test qu'un chariot avec humain est opérationnel."""
        cart = Cart("C1", 50, 80, 1.2, 3, {'requires_human': True})
        human = Human("H1", 35, 50, 1.5, 25)
        
        cart.assigned_human = human
        assert cart.is_operational() is True
    
    def test_cart_not_operational_without_human(self):
        """Test qu'un chariot sans humain n'est pas opérationnel."""
        cart = Cart("C1", 50, 80, 1.2, 3, {'requires_human': True})
        
        assert cart.is_operational() is False
    
    def test_agent_reset_load(self):
        """Test de réinitialisation de la charge."""
        agent = Robot("R1", 20, 30, 2.0, 5, {})
        agent.current_load_weight = 10.0
        agent.current_load_volume = 15.0
        
        agent.reset_load()
        
        assert agent.current_load_weight == 0.0
        assert agent.current_load_volume == 0.0
        assert len(agent.current_products) == 0


class TestOrder:
    """Tests pour la classe Order."""
    
    def test_order_creation(self):
        """Test de création d'une commande."""
        order = Order(
            id="O001",
            received_time="08:00",
            deadline="10:00",
            priority="express",
            items=[]
        )
        
        assert order.id == "O001"
        assert order.priority == "express"
    
    def test_order_calculate_totals(self):
        """Test du calcul des totaux."""
        p1 = Product("P001", "A", "cat", 2.0, 5.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 3.0, 7.0, Location(1, 1), "high", False, [])
        
        item1 = OrderItem(product_id="P001", quantity=2, product=p1)
        item2 = OrderItem(product_id="P002", quantity=1, product=p2)
        
        order = Order("O001", "08:00", "10:00", "standard", items=[item1, item2])
        order.calculate_totals()
        
        assert order.total_weight == 7.0  # 2*2 + 3*1
        assert order.total_volume == 17.0  # 2*5 + 1*7
    
    def test_order_get_unique_locations(self):
        """Test récupération des emplacements uniques."""
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        p3 = Product("P003", "C", "cat", 1.0, 1.0, Location(2, 2), "high", False, [])
        
        item1 = OrderItem("P001", 1, p1)
        item2 = OrderItem("P002", 1, p2)
        item3 = OrderItem("P003", 1, p3)
        
        order = Order("O001", "08:00", "10:00", "standard", items=[item1, item2, item3])
        locations = order.get_unique_locations()
        
        assert len(locations) == 2  # Seulement 2 emplacements uniques
    
    def test_order_time_to_deadline(self):
        """Test du calcul du temps disponible."""
        order = Order("O001", "08:00", "10:30", "standard", items=[])
        
        assert order.time_to_deadline() == 150  # 2h30 = 150 minutes
    
    def test_order_has_incompatibilities_false(self):
        """Test commande sans incompatibilités."""
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        
        item1 = OrderItem("P001", 1, p1)
        item2 = OrderItem("P002", 1, p2)
        
        order = Order("O001", "08:00", "10:00", "standard", items=[item1, item2])
        
        assert order.has_incompatibilities() is False
    
    def test_order_has_incompatibilities_true(self):
        """Test commande avec incompatibilités."""
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(0, 0), "high", False, ["P002"])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(1, 1), "high", False, [])
        
        item1 = OrderItem("P001", 1, p1)
        item2 = OrderItem("P002", 1, p2)
        
        order = Order("O001", "08:00", "10:00", "standard", items=[item1, item2])
        
        assert order.has_incompatibilities() is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])