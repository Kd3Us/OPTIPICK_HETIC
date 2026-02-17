"""
Storage optimisation: analyses order history to propose a
product layout that reduces average pick distances.
"""

from typing import List, Dict, Tuple
from collections import defaultdict, Counter
import numpy as np

from .models import Product, Order, Warehouse, Location


class StorageOptimizer:

    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse

    def analyze_product_frequency(self, orders: List[Order]) -> Dict[str, int]:
        """Count how many times each product has been ordered."""
        frequency: Counter = Counter()
        for order in orders:
            for item in order.items:
                if item.product:
                    frequency[item.product.id] += item.quantity
        return dict(frequency)

    def analyze_product_affinity(self, orders: List[Order]) -> Dict[Tuple[str, str], int]:
        """Count how often product pairs appear in the same order."""
        affinity: Dict[Tuple[str, str], int] = defaultdict(int)
        for order in orders:
            product_ids = [item.product.id for item in order.items if item.product]
            for i, p1 in enumerate(product_ids):
                for p2 in product_ids[i + 1:]:
                    pair = tuple(sorted([p1, p2]))
                    affinity[pair] += 1
        return dict(affinity)

    def get_top_products(self, frequencies: Dict[str, int], n: int = 20) -> List[str]:
        sorted_items = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in sorted_items[:n]]

    def propose_reorganization(self, products: List[Product],
                               orders: List[Order]) -> Dict[str, Location]:
        """
        Suggest new product locations based on frequency and affinity.

        Rules:
          1. High-frequency products placed closest to entry point.
          2. Products with high affinity placed in adjacent slots.
          3. Zone constraints respected (food stays in C, chemicals in D).
        """
        frequencies = self.analyze_product_frequency(orders)

        products_by_category: Dict[str, List[Product]] = defaultdict(list)
        for product in products:
            products_by_category[product.category].append(product)

        available_locations: Dict[str, List[Location]] = {}
        for zone_id, zone in self.warehouse.zones.items():
            available_locations[zone_id] = sorted(
                zone.coords,
                key=lambda loc: self.warehouse.entry_point.distance_to(loc)
            )

        category_to_zone = {
            'electronics': 'A',
            'book': 'B',
            'food': 'C',
            'chemical': 'D',
            'textile': 'E'
        }

        new_locations: Dict[str, Location] = {}

        for category, prods in products_by_category.items():
            zone_id = category_to_zone.get(category, 'E')
            prods_sorted = sorted(
                prods, key=lambda p: frequencies.get(p.id, 0), reverse=True
            )
            slots = available_locations[zone_id]
            for i, product in enumerate(prods_sorted):
                new_locations[product.id] = slots[i] if i < len(slots) else product.location

        return new_locations

    def calculate_improvement(self, products: List[Product], orders: List[Order],
                              new_locations: Dict[str, Location]) -> Dict[str, float]:
        """Compare total pick distance before and after reorganisation."""
        current_distance = sum(
            self.warehouse.entry_point.distance_to(loc)
            for order in orders
            for loc in order.get_unique_locations()
        )
        current_avg = current_distance / len(orders) if orders else 0.0

        new_distance = sum(
            self.warehouse.entry_point.distance_to(
                new_locations.get(item.product.id, item.product.location)
            )
            for order in orders
            for item in order.items
            if item.product
        )
        new_avg = new_distance / len(orders) if orders else 0.0

        improvement = ((current_avg - new_avg) / current_avg * 100) if current_avg > 0 else 0.0

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
    products_dict = {p.id: p for p in products}

    print("\n" + "=" * 60)
    print("STORAGE ANALYSIS")
    print("=" * 60)

    print("\nTop 10 most ordered products:")
    top_products = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:10]
    for rank, (pid, count) in enumerate(top_products, 1):
        product = products_dict.get(pid)
        if product:
            distance = product.location.distance_to(Location(0, 0))
            print(f"  {rank:2}. {product.name} ({pid})")
            print(f"      ordered {count}x  |  distance from entry: {distance}m")

    print("\nTop 10 most co-ordered product pairs:")
    top_affinities = sorted(affinities.items(), key=lambda x: x[1], reverse=True)[:10]
    for rank, ((p1, p2), count) in enumerate(top_affinities, 1):
        prod1 = products_dict.get(p1)
        prod2 = products_dict.get(p2)
        if prod1 and prod2:
            dist = prod1.location.distance_to(prod2.location)
            print(f"  {rank:2}. {prod1.name} + {prod2.name}")
            print(f"      co-ordered {count}x  |  shelf distance: {dist}m")

    print("=" * 60)