"""
Tests unitaires pour le module utils.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Location, Product, Order, OrderItem, Agent, Robot
from src.utils import calculate_total_distance, calculate_agent_cost, estimate_order_distance


class TestUtils:
    """Tests pour les fonctions utilitaires."""
    
    def test_calculate_total_distance_empty(self):
        """Test distance avec liste vide."""
        distance = calculate_total_distance([])
        assert distance == 0.0
    
    def test_calculate_total_distance_single_location(self):
        """Test distance avec un seul emplacement."""
        loc = Location(5, 3)
        distance = calculate_total_distance([loc])
        assert distance == 0.0
    
    def test_calculate_total_distance_multiple_locations(self):
        """Test distance avec plusieurs emplacements."""
        locations = [
            Location(0, 0),
            Location(3, 0),
            Location(3, 4)
        ]
        
        distance = calculate_total_distance(locations)
        # (0,0) -> (3,0) = 3
        # (3,0) -> (3,4) = 4
        # Total = 7
        assert distance == 7.0
    
    def test_calculate_total_distance_with_start(self):
        """Test distance avec point de départ spécifié."""
        start = Location(0, 0)
        locations = [Location(3, 0), Location(3, 4)]
        
        distance = calculate_total_distance(locations, start)
        # (0,0) -> (3,0) = 3
        # (3,0) -> (3,4) = 4
        # (3,4) -> (0,0) = 7
        # Total = 14
        assert distance == 14.0
    
    def test_calculate_agent_cost(self):
        """Test calcul du coût d'un agent."""
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        
        # 30 minutes = 0.5 heure
        # Coût = 0.5 × 5€/h = 2.5€
        cost = calculate_agent_cost(robot, 30)
        
        assert cost == 2.5
    
    def test_calculate_agent_cost_zero_time(self):
        """Test coût avec temps zéro."""
        robot = Robot("R1", 20, 30, 2.0, 5, {})
        cost = calculate_agent_cost(robot, 0)
        assert cost == 0.0
    
    def test_estimate_order_distance(self):
        """Test estimation de distance pour une commande."""
        entry = Location(0, 0)
        
        p1 = Product("P001", "A", "cat", 1.0, 1.0, Location(3, 0), "high", False, [])
        p2 = Product("P002", "B", "cat", 1.0, 1.0, Location(3, 4), "high", False, [])
        
        item1 = OrderItem("P001", 1, p1)
        item2 = OrderItem("P002", 1, p2)
        
        order = Order("O001", "08:00", "10:00", "standard", items=[item1, item2])
        
        distance = estimate_order_distance(order, entry)
        
        # Au minimum : distance vers chaque emplacement
        assert distance > 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])