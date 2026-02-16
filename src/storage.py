"""
Module d'optimisation du stockage des produits.

Analyse les patterns de commandes et propose une réorganisation
de l'entrepôt pour minimiser les distances futures.
"""

from typing import List, Dict, Tuple
from collections import defaultdict, Counter
import numpy as np

from .models import Product, Order, Warehouse, Location


class StorageOptimizer:
    """Optimise le placement des produits dans l'entrepôt."""
    
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
    
    def analyze_product_frequency(self, orders: List[Order]) -> Dict[str, int]:
        """
        Analyse la fréquence de commande de chaque produit.
        
        Args:
            orders: Historique de commandes
            
        Returns:
            Dictionnaire {product_id: nombre_de_fois_commandé}
        """
        frequency = Counter()
        
        for order in orders:
            for item in order.items:
                if item.product:
                    frequency[item.product.id] += item.quantity
        
        return dict(frequency)
    
    def analyze_product_affinity(self, orders: List[Order]) -> Dict[Tuple[str, str], int]:
        """
        Calcule l'affinité entre produits (combien de fois commandés ensemble).
        
        Args:
            orders: Historique de commandes
            
        Returns:
            Dictionnaire {(product_id1, product_id2): co-occurrences}
        """
        affinity = defaultdict(int)
        
        for order in orders:
            product_ids = [item.product.id for item in order.items if item.product]
            
            # Compter les paires
            for i, p1 in enumerate(product_ids):
                for p2 in product_ids[i+1:]:
                    # Normaliser l'ordre pour éviter les doublons
                    pair = tuple(sorted([p1, p2]))
                    affinity[pair] += 1
        
        return dict(affinity)
    
    def get_top_products(self, frequencies: Dict[str, int], n: int = 20) -> List[str]:
        """
        Retourne les n produits les plus commandés.
        
        Args:
            frequencies: Dictionnaire de fréquences
            n: Nombre de produits à retourner
            
        Returns:
            Liste de product_ids triée par fréquence décroissante
        """
        sorted_products = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in sorted_products[:n]]
    
    def propose_reorganization(self, products: List[Product], 
                              orders: List[Order]) -> Dict[str, Location]:
        """
        Propose une nouvelle organisation de l'entrepôt.
        
        Règles :
        1. Produits fréquents près de l'entrée
        2. Produits affinitaires proches les uns des autres
        3. Respecter les contraintes de zones (alimentaire, chimie, etc.)
        
        Args:
            products: Liste de produits actuels
            orders: Historique de commandes
            
        Returns:
            Dictionnaire {product_id: nouvelle_location}
        """
        # Analyser les fréquences
        frequencies = self.analyze_product_frequency(orders)
        affinities = self.analyze_product_affinity(orders)
        
        # Créer un dictionnaire de produits par catégorie
        products_by_category = defaultdict(list)
        for product in products:
            products_by_category[product.category].append(product)
        
        # Nouvelle disposition
        new_locations = {}
        
        # Obtenir tous les emplacements disponibles par zone
        available_locations = {}
        for zone_id, zone in self.warehouse.zones.items():
            # Trier les emplacements par distance à l'entrée
            sorted_locs = sorted(
                zone.coords,
                key=lambda loc: self.warehouse.entry_point.distance_to(loc)
            )
            available_locations[zone_id] = sorted_locs
        
        # Mapping catégorie → zone préférée
        category_to_zone = {
            'electronics': 'A',
            'book': 'B',
            'food': 'C',
            'chemical': 'D',
            'textile': 'E'
        }
        
        # Pour chaque catégorie, placer les produits
        for category, prods in products_by_category.items():
            zone_id = category_to_zone.get(category, 'E')
            
            # Trier les produits de cette catégorie par fréquence
            prods_sorted = sorted(
                prods,
                key=lambda p: frequencies.get(p.id, 0),
                reverse=True
            )
            
            # Assigner les emplacements (les plus fréquents d'abord)
            locs = available_locations[zone_id]
            for i, product in enumerate(prods_sorted):
                if i < len(locs):
                    new_locations[product.id] = locs[i]
                else:
                    # Pas assez de place, garder l'emplacement actuel
                    new_locations[product.id] = product.location
        
        return new_locations
    
    def calculate_improvement(self, products: List[Product], orders: List[Order],
                             new_locations: Dict[str, Location]) -> Dict[str, float]:
        """
        Calcule l'amélioration apportée par la réorganisation.
        
        Args:
            products: Liste de produits
            orders: Commandes de test
            new_locations: Nouvelle disposition proposée
            
        Returns:
            Dictionnaire avec les métriques avant/après
        """
        # Calculer distance moyenne actuelle
        current_distance = 0.0
        for order in orders:
            for loc in order.get_unique_locations():
                current_distance += self.warehouse.entry_point.distance_to(loc)
        
        current_avg = current_distance / len(orders) if orders else 0
        
        # Calculer distance moyenne avec nouvelle disposition
        products_dict = {p.id: p for p in products}
        new_distance = 0.0
        
        for order in orders:
            for item in order.items:
                if item.product:
                    new_loc = new_locations.get(item.product.id, item.product.location)
                    new_distance += self.warehouse.entry_point.distance_to(new_loc)
        
        new_avg = new_distance / len(orders) if orders else 0
        
        improvement = ((current_avg - new_avg) / current_avg * 100) if current_avg > 0 else 0
        
        return {
            'current_total_distance': current_distance,
            'new_total_distance': new_distance,
            'current_avg_distance': current_avg,
            'new_avg_distance': new_avg,
            'improvement_percent': improvement,
            'distance_saved': current_distance - new_distance
        }


def print_storage_analysis(frequencies: Dict[str, int], 
                          affinities: Dict[Tuple[str, str], int],
                          products: List[Product]):
    """Affiche l'analyse du stockage."""
    
    print("\n" + "=" * 70)
    print(" " * 22 + "ANALYSE DU STOCKAGE")
    print("=" * 70)
    
    # Top produits
    print("\n📊 Top 10 produits les plus commandés :")
    products_dict = {p.id: p for p in products}
    top_products = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for i, (pid, count) in enumerate(top_products, 1):
        product = products_dict.get(pid)
        if product:
            distance = product.location.distance_to(Location(0, 0))
            print(f"  {i}. {product.name} ({pid})")
            print(f"     Commandé {count} fois, Distance entrée: {distance}m")
    
    # Top affinités
    print("\n🔗 Top 10 paires de produits souvent commandés ensemble :")
    top_affinities = sorted(affinities.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for i, ((p1, p2), count) in enumerate(top_affinities, 1):
        prod1 = products_dict.get(p1)
        prod2 = products_dict.get(p2)
        if prod1 and prod2:
            dist = prod1.location.distance_to(prod2.location)
            print(f"  {i}. {prod1.name} + {prod2.name}")
            print(f"     Co-commandés {count} fois, Distance: {dist}m")
    
    print("=" * 70)