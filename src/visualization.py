"""
Module de visualisation pour OptiPick.

Crée des graphiques et visualisations de l'entrepôt,
des tournées et des métriques.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path

from .models import Warehouse, Agent, Product, Location


class WarehouseVisualizer:
    """Visualise l'entrepôt et les tournées."""
    
    def __init__(self, warehouse: Warehouse):
        self.warehouse = warehouse
        
        # Couleurs pour les zones
        self.zone_colors = {
            'A': '#FFE5B4',  # Electronics - beige
            'B': '#B4D7FF',  # Books - bleu clair
            'C': '#FFB4B4',  # Food - rouge clair
            'D': '#FFD700',  # Chemical - jaune
            'E': '#B4FFB4',  # Textile - vert clair
        }
    
    def plot_warehouse(self, products: List[Product] = None, 
                      save_path: str = None, show: bool = True):
        """
        Dessine la carte de l'entrepôt avec les zones et produits.
        
        Args:
            products: Liste de produits à afficher
            save_path: Chemin pour sauvegarder l'image
            show: Afficher le graphique
        """
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Dessiner la grille
        for x in range(self.warehouse.width + 1):
            ax.axvline(x, color='gray', linewidth=0.5, alpha=0.3)
        for y in range(self.warehouse.height + 1):
            ax.axhline(y, color='gray', linewidth=0.5, alpha=0.3)
        
        # Dessiner les zones
        for zone_id, zone in self.warehouse.zones.items():
            color = self.zone_colors.get(zone_id, '#CCCCCC')
            
            for location in zone.coords:
                rect = patches.Rectangle(
                    (location.x, location.y), 1, 1,
                    linewidth=1, edgecolor='black',
                    facecolor=color, alpha=0.6
                )
                ax.add_patch(rect)
        
        # Dessiner l'entrée
        entry = self.warehouse.entry_point
        entry_circle = plt.Circle(
            (entry.x + 0.5, entry.y + 0.5), 0.4,
            color='red', alpha=0.8, zorder=5
        )
        ax.add_patch(entry_circle)
        ax.text(entry.x + 0.5, entry.y + 0.5, 'E', 
               ha='center', va='center', fontsize=12, 
               fontweight='bold', color='white')
        
        # Dessiner les produits
        if products:
            for product in products:
                loc = product.location
                
                # Couleur selon la fréquence
                freq_colors = {
                    'very_high': 'darkred',
                    'high': 'red',
                    'medium': 'orange',
                    'low': 'yellow'
                }
                color = freq_colors.get(product.frequency, 'gray')
                
                # Marqueur
                marker = 'D' if product.fragile else 'o'
                ax.plot(loc.x + 0.5, loc.y + 0.5, marker=marker,
                       color=color, markersize=8, zorder=3)
                
                # Label (ID du produit)
                ax.text(loc.x + 0.5, loc.y + 0.3, product.id,
                       ha='center', va='top', fontsize=6)
        
        # Légende des zones
        legend_elements = [
            patches.Patch(facecolor=self.zone_colors[z], 
                         edgecolor='black', 
                         label=f'Zone {z} ({self.warehouse.zones[z].name})')
            for z in self.zone_colors.keys()
        ]
        legend_elements.append(
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor='darkred', markersize=8,
                      label='Produit (fréquence)')
        )
        legend_elements.append(
            plt.Line2D([0], [0], marker='D', color='w',
                      markerfacecolor='gray', markersize=8,
                      label='Fragile')
        )
        
        ax.legend(handles=legend_elements, loc='upper left', 
                 bbox_to_anchor=(1.02, 1))
        
        ax.set_xlim(0, self.warehouse.width)
        ax.set_ylim(0, self.warehouse.height)
        ax.set_aspect('equal')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title('Carte de l\'Entrepôt OptiPick', fontsize=16, fontweight='bold')
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Carte sauvegardée : {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def plot_route(self, route_info: Dict, products: List[Product],
                   save_path: str = None, show: bool = True):
        """
        Dessine une tournée spécifique sur la carte.
        
        Args:
            route_info: Information de tournée
            products: Liste de produits
            save_path: Chemin de sauvegarde
            show: Afficher
        """
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Dessiner l'entrepôt de base
        for zone_id, zone in self.warehouse.zones.items():
            color = self.zone_colors.get(zone_id, '#CCCCCC')
            for location in zone.coords:
                rect = patches.Rectangle(
                    (location.x, location.y), 1, 1,
                    linewidth=1, edgecolor='black',
                    facecolor=color, alpha=0.3
                )
                ax.add_patch(rect)
        
        # Extraire la route
        route = route_info['route']
        
        # Dessiner le chemin
        for i in range(len(route) - 1):
            loc1 = route[i]['location']
            loc2 = route[i + 1]['location']
            
            ax.arrow(
                loc1.x + 0.5, loc1.y + 0.5,
                loc2.x - loc1.x, loc2.y - loc1.y,
                head_width=0.3, head_length=0.2,
                fc='blue', ec='blue', alpha=0.6,
                length_includes_head=True, zorder=2
            )
        
        # Numéroter les étapes
        for i, step in enumerate(route):
            loc = step['location']
            ax.plot(loc.x + 0.5, loc.y + 0.5, 'o',
                   markersize=15, color='red' if i == 0 else 'green',
                   zorder=4)
            ax.text(loc.x + 0.5, loc.y + 0.5, str(i),
                   ha='center', va='center', fontsize=10,
                   fontweight='bold', color='white', zorder=5)
        
        ax.set_xlim(0, self.warehouse.width)
        ax.set_ylim(0, self.warehouse.height)
        ax.set_aspect('equal')
        ax.invert_yaxis()
        
        agent_id = route_info['agent_id']
        distance = route_info['total_distance']
        cost = route_info['total_cost_euros']
        
        ax.set_title(f'Tournée Agent {agent_id}\n'
                    f'Distance: {distance:.1f}m | Coût: {cost:.2f}€',
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Tournée sauvegardée : {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def plot_all_routes(self, routes: List[Dict], products: List[Product],
                       save_path: str = None, show: bool = True):
        """Dessine toutes les tournées sur une seule carte."""
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Entrepôt de base
        for zone_id, zone in self.warehouse.zones.items():
            color = self.zone_colors.get(zone_id, '#CCCCCC')
            for location in zone.coords:
                rect = patches.Rectangle(
                    (location.x, location.y), 1, 1,
                    linewidth=1, edgecolor='black',
                    facecolor=color, alpha=0.2
                )
                ax.add_patch(rect)
        
        # Couleurs pour différents agents
        agent_colors = ['blue', 'green', 'purple', 'orange', 'brown']
        
        # Dessiner chaque route
        for idx, route_info in enumerate(routes):
            color = agent_colors[idx % len(agent_colors)]
            route = route_info['route']
            
            for i in range(len(route) - 1):
                loc1 = route[i]['location']
                loc2 = route[i + 1]['location']
                
                ax.arrow(
                    loc1.x + 0.5, loc1.y + 0.5,
                    loc2.x - loc1.x, loc2.y - loc1.y,
                    head_width=0.2, head_length=0.15,
                    fc=color, ec=color, alpha=0.5,
                    length_includes_head=True, zorder=2
                )
            
            # Marqueur pour le premier point de chaque agent
            first_loc = route[0]['location']
            ax.plot(first_loc.x + 0.5, first_loc.y + 0.5, 'o',
                   markersize=12, color=color, zorder=4,
                   label=f"{route_info['agent_id']}")
        
        ax.set_xlim(0, self.warehouse.width)
        ax.set_ylim(0, self.warehouse.height)
        ax.set_aspect('equal')
        ax.invert_yaxis()
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
        ax.set_title('Toutes les Tournées Optimisées', 
                    fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Vue d'ensemble sauvegardée : {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()


class MetricsDashboard:
    """Crée un dashboard de métriques."""
    
    @staticmethod
    def plot_comparison(greedy_metrics: Dict, optimal_metrics: Dict,
                       save_path: str = None, show: bool = True):
        """Compare les métriques Greedy vs Optimal."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Comparaison Greedy vs Optimal (CP-SAT)', 
                    fontsize=16, fontweight='bold')
        
        # Distance
        ax = axes[0, 0]
        categories = ['Greedy', 'Optimal']
        distances = [greedy_metrics['distance'], optimal_metrics['distance']]
        bars = ax.bar(categories, distances, color=['#FF6B6B', '#4ECDC4'])
        ax.set_ylabel('Distance (m)')
        ax.set_title('Distance Totale')
        for bar, val in zip(bars, distances):
            ax.text(bar.get_x() + bar.get_width()/2, val + 1,
                   f'{val:.1f}m', ha='center', va='bottom', fontweight='bold')
        
        # Coût
        ax = axes[0, 1]
        costs = [greedy_metrics['cost'], optimal_metrics['cost']]
        bars = ax.bar(categories, costs, color=['#FF6B6B', '#4ECDC4'])
        ax.set_ylabel('Coût (€)')
        ax.set_title('Coût Total')
        for bar, val in zip(bars, costs):
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.1,
                   f'{val:.2f}€', ha='center', va='bottom', fontweight='bold')
        
        # Temps
        ax = axes[1, 0]
        times = [greedy_metrics['time'], optimal_metrics['time']]
        bars = ax.bar(categories, times, color=['#FF6B6B', '#4ECDC4'])
        ax.set_ylabel('Temps (min)')
        ax.set_title('Temps Total')
        for bar, val in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.2,
                   f'{val:.1f}min', ha='center', va='bottom', fontweight='bold')
        
        # Amélioration en pourcentage
        ax = axes[1, 1]
        improvements = [
            ((greedy_metrics['distance'] - optimal_metrics['distance']) / 
             greedy_metrics['distance'] * 100),
            ((greedy_metrics['cost'] - optimal_metrics['cost']) / 
             greedy_metrics['cost'] * 100),
            ((greedy_metrics['time'] - optimal_metrics['time']) / 
             greedy_metrics['time'] * 100)
        ]
        metrics_names = ['Distance', 'Coût', 'Temps']
        bars = ax.barh(metrics_names, improvements, color='#95E1D3')
        ax.set_xlabel('Amélioration (%)')
        ax.set_title('Gains de l\'Optimisation')
        for bar, val in zip(bars, improvements):
            ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                   f'{val:.1f}%', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Dashboard sauvegardé : {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    @staticmethod
    def plot_agent_utilization(agents: List[Agent],
                              save_path: str = None, show: bool = True):
        """Visualise l'utilisation des agents."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Agents actifs
        active_agents = [a for a in agents if a.assigned_orders]
        agent_names = [a.id for a in active_agents]
        
        # Utilisation en poids
        weight_usage = [
            (a.current_load_weight / a.capacity_weight * 100)
            for a in active_agents
        ]
        
        colors = ['#FF6B6B' if isinstance(a, type) and 'Robot' in str(type(a)) 
                 else '#4ECDC4' if 'Human' in str(type(a))
                 else '#95E1D3'
                 for a in active_agents]
        
        bars = ax1.barh(agent_names, weight_usage, color=colors)
        ax1.set_xlabel('Utilisation (%)')
        ax1.set_title('Utilisation de la Capacité (Poids)')
        ax1.axvline(100, color='red', linestyle='--', alpha=0.5)
        
        for bar, val in zip(bars, weight_usage):
            ax1.text(val + 2, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}%', va='center')
        
        # Nombre de commandes par agent
        order_counts = [len(a.assigned_orders) for a in active_agents]
        bars = ax2.bar(agent_names, order_counts, color=colors)
        ax2.set_ylabel('Nombre de commandes')
        ax2.set_title('Commandes par Agent')
        
        for bar, val in zip(bars, order_counts):
            ax2.text(bar.get_x() + bar.get_width()/2, val + 0.1,
                    str(val), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Utilisation agents sauvegardée : {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()


def generate_all_visualizations(warehouse: Warehouse, products: List[Product],
                                routes_greedy: List[Dict], routes_optimal: List[Dict],
                                agents_greedy: List[Agent], agents_optimal: List[Agent],
                                output_dir: str = 'results'):
    """Génère toutes les visualisations."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("\n🎨 Génération des visualisations...")
    
    viz = WarehouseVisualizer(warehouse)
    
    # 1. Carte de l'entrepôt
    viz.plot_warehouse(
        products=products,
        save_path=str(output_path / 'warehouse_map.png'),
        show=False
    )
    
    # 2. Toutes les routes (Greedy)
    if routes_greedy:
        viz.plot_all_routes(
            routes_greedy, products,
            save_path=str(output_path / 'routes_greedy.png'),
            show=False
        )
    
    # 3. Toutes les routes (Optimal)
    if routes_optimal:
        viz.plot_all_routes(
            routes_optimal, products,
            save_path=str(output_path / 'routes_optimal.png'),
            show=False
        )
    
    # 4. Comparaison métriques
    greedy_metrics = {
        'distance': sum(r['total_distance'] for r in routes_greedy),
        'cost': sum(r['total_cost_euros'] for r in routes_greedy),
        'time': sum(r['total_time_minutes'] for r in routes_greedy)
    }
    optimal_metrics = {
        'distance': sum(r['total_distance'] for r in routes_optimal),
        'cost': sum(r['total_cost_euros'] for r in routes_optimal),
        'time': sum(r['total_time_minutes'] for r in routes_optimal)
    }
    
    MetricsDashboard.plot_comparison(
        greedy_metrics, optimal_metrics,
        save_path=str(output_path / 'comparison_dashboard.png'),
        show=False
    )
    
    # 5. Utilisation agents (Optimal)
    MetricsDashboard.plot_agent_utilization(
        agents_optimal,
        save_path=str(output_path / 'agent_utilization.png'),
        show=False
    )
    
    print(f"✅ {5} visualisations générées dans {output_dir}/")