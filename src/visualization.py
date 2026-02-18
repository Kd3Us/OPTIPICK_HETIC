import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

ZONE_COLORS = {"A": "#4C8BF5", "B": "#34A853", "C": "#EA4335", "D": "#FBBC05", "E": "#9C27B0"}
AGENT_COLORS = {"robot": "#4C8BF5", "human": "#34A853", "cart": "#FF6D00"}


def _agent_color(agent_id: str) -> str:
    if agent_id.upper().startswith('R'):
        return AGENT_COLORS["robot"]
    if agent_id.upper().startswith('H'):
        return AGENT_COLORS["human"]
    return AGENT_COLORS["cart"]


def plot_warehouse(warehouse: Dict, products: List[Dict], save_path: Optional[str] = None):
    width, height = warehouse["width"], warehouse["height"]
    fig, ax = plt.subplots(figsize=(12, 9))

    for x in range(width + 1):
        ax.axvline(x, color='#CCCCCC', linewidth=0.5)
    for y in range(height + 1):
        ax.axhline(y, color='#CCCCCC', linewidth=0.5)

    for zone, color in ZONE_COLORS.items():
        pts = [(p["x"], p["y"]) for p in products if p.get("zone") == zone]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, c=color, s=120, zorder=3, label=f"Zone {zone}")

    ax.scatter([0], [0], marker="*", s=300, c="orange", zorder=4, label="Entree")
    ax.set_xlim(-0.5, width)
    ax.set_ylim(-0.5, height)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Plan de l'entrepot OptiPick", fontweight='bold')
    ax.legend(loc='upper right')
    ax.set_aspect('equal')
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_agent_utilization(utilization_dict: Dict, save_path: Optional[str] = None):
    agents = list(utilization_dict.keys())
    pcts = list(utilization_dict.values())
    colors = [_agent_color(a) for a in agents]

    fig, ax = plt.subplots(figsize=(9, max(3, len(agents) * 0.7 + 1.5)))
    bars = ax.barh(agents, pcts, color=colors)
    for bar, pct in zip(bars, pcts):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{pct}%", va='center', fontsize=10)
    ax.set_xlim(0, 115)
    ax.set_xlabel("Utilisation (%)")
    ax.set_title("Utilisation des agents", fontweight='bold')
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_route(warehouse: Dict, route: List[Dict], agent_id: str, save_path: Optional[str] = None):
    width, height = warehouse["width"], warehouse["height"]
    color = _agent_color(agent_id)

    fig, ax = plt.subplots(figsize=(10, 7))
    for x in range(width + 1):
        ax.axvline(x, color='#DDDDDD', linewidth=0.4)
    for y in range(height + 1):
        ax.axhline(y, color='#DDDDDD', linewidth=0.4)

    xs = [p["x"] for p in route]
    ys = [p["y"] for p in route]
    ax.plot(xs, ys, '-', color=color, linewidth=1.5, alpha=0.7)
    ax.scatter(xs, ys, c=color, s=80, zorder=4)

    for i, (x, y) in enumerate(zip(xs, ys)):
        ax.annotate(str(i + 1), (x, y), xytext=(5, 5), textcoords="offset points", fontsize=8)

    for i in range(len(xs) - 1):
        ax.annotate("", xy=(xs[i+1], ys[i+1]), xytext=(xs[i], ys[i]),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.2))

    ax.set_xlim(-0.5, width)
    ax.set_ylim(-0.5, height)
    ax.set_title(f"Tournee de {agent_id}", fontweight='bold')
    ax.set_aspect('equal')
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_all_routes(warehouse: Dict, all_routes: Dict, save_path: Optional[str] = None):
    width, height = warehouse["width"], warehouse["height"]

    fig, ax = plt.subplots(figsize=(12, 9))
    for x in range(width + 1):
        ax.axvline(x, color='#DDDDDD', linewidth=0.4)
    for y in range(height + 1):
        ax.axhline(y, color='#DDDDDD', linewidth=0.4)

    for agent_id, route in all_routes.items():
        xs = [p["x"] for p in route]
        ys = [p["y"] for p in route]
        ax.plot(xs, ys, '-o', color=_agent_color(agent_id), linewidth=1.5,
                alpha=0.75, markersize=6, label=agent_id)

    ax.scatter([0], [0], marker="*", s=250, c="orange", zorder=5, label="Entree")
    ax.set_xlim(-0.5, width)
    ax.set_ylim(-0.5, height)
    ax.legend(loc='upper right')
    ax.set_title("Toutes les tournees", fontweight='bold')
    ax.set_aspect('equal')
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_route_comparison(warehouse: Dict, route_before: List[Dict], route_after: List[Dict],
                          agent_id: str, save_path: Optional[str] = None):
    width, height = warehouse["width"], warehouse["height"]
    color = _agent_color(agent_id)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    for ax, route, title in zip(axes, [route_before, route_after], ["Avant", "Apres"]):
        for x in range(width + 1):
            ax.axvline(x, color='#DDDDDD', linewidth=0.4)
        for y in range(height + 1):
            ax.axhline(y, color='#DDDDDD', linewidth=0.4)
        xs = [p["x"] for p in route]
        ys = [p["y"] for p in route]
        dist = sum(abs(xs[i+1]-xs[i]) + abs(ys[i+1]-ys[i]) for i in range(len(xs)-1))
        ax.plot(xs, ys, '-o', color=color, linewidth=1.5, markersize=6)
        ax.set_title(f"{title} - distance: {dist:.0f}m", fontweight='bold')
        ax.set_xlim(-0.5, width)
        ax.set_ylim(-0.5, height)
        ax.set_aspect('equal')

    fig.suptitle(f"Comparaison de route - {agent_id}", fontweight='bold')
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_distance_comparison(scenarios_dict: Dict, save_path: Optional[str] = None):
    labels = list(scenarios_dict.keys())
    values = list(scenarios_dict.values())
    colors = plt.cm.Set2(np.linspace(0, 1, len(labels)))

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, values, color=colors)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01, f"{h:.0f}m",
                ha='center', va='bottom', fontsize=10)
    ax.set_title("Comparaison des distances", fontweight='bold')
    ax.set_ylabel("Distance (m)")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_time_comparison(scenarios_dict: Dict, save_path: Optional[str] = None):
    labels = list(scenarios_dict.keys())
    values = list(scenarios_dict.values())
    colors = plt.cm.Set2(np.linspace(0, 1, len(labels)))

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, values, color=colors)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01, f"{h:.0f}min",
                ha='center', va='bottom', fontsize=10)
    ax.set_title("Comparaison des temps", fontweight='bold')
    ax.set_ylabel("Temps (min)")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_cost_breakdown(agents_costs: Dict, save_path: Optional[str] = None):
    labels = list(agents_costs.keys())
    values = list(agents_costs.values())
    colors = [_agent_color(a) for a in labels]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, values, color=colors)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                f"{v:.2f}EUR", ha='center', va='bottom', fontsize=10)
    ax.set_title("Couts par agent", fontweight='bold')
    ax.set_ylabel("Cout (EUR)")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_product_frequency(frequency_dict: Dict, top_n: int = 10, save_path: Optional[str] = None):
    items = sorted(frequency_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    if not items:
        return
    labels, values = zip(*items)

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.5 + 1)))
    ax.barh(labels, values, color="#4C8BF5")
    ax.set_xlabel("Quantite commandee")
    ax.set_title(f"Top {top_n} produits", fontweight='bold')
    ax.invert_yaxis()
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_zone_traffic(traffic_dict: Dict, save_path: Optional[str] = None):
    zones = list(traffic_dict.keys())
    counts = list(traffic_dict.values())
    colors = [ZONE_COLORS.get(z, "#888888") for z in zones]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(zones, counts, color=colors)
    for bar, c in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                str(c), ha='center', va='bottom', fontsize=10)
    ax.set_title("Trafic par zone", fontweight='bold')
    ax.set_ylabel("Nombre de visites")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def create_zone_heatmap(warehouse: Dict, visit_counts: Dict, save_path: Optional[str] = None):
    import seaborn as sns
    width, height = warehouse["width"], warehouse["height"]
    grid = np.zeros((height, width))
    for (x, y), count in visit_counts.items():
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = count

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(grid, annot=True, fmt='.0f', cmap="YlOrRd",
                linewidths=0.5, linecolor='#CCCCCC', ax=ax)
    ax.set_title("Heatmap des zones visitees", fontweight='bold')
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def create_dashboard(allocation: Dict, route_results: List[Dict], metrics: Dict,
                     warehouse: Dict, save_path: str = "results/dashboard.png"):
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle("OptiPick - Dashboard", fontsize=15, fontweight='bold')

    per_agent = metrics.get('per_agent', {})
    agent_ids = list(per_agent.keys())
    colors = [_agent_color(a) for a in agent_ids]
    total_time = metrics.get('makespan_minutes', 1) or 1

    # utilisation
    ax = axes[0][0]
    if agent_ids:
        utils = [round(per_agent[a]['time_minutes'] / total_time * 100, 1) for a in agent_ids]
        bars = ax.barh(agent_ids, utils, color=colors)
        for bar, pct in zip(bars, utils):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"{pct}%", va='center', fontsize=9)
        ax.set_xlim(0, 120)
    ax.set_title("Utilisation des agents", fontweight='bold')

    # cost pie
    ax = axes[0][1]
    if agent_ids:
        costs = [per_agent[a]['cost_euros'] for a in agent_ids]
        if sum(costs) > 0:
            ax.pie(costs, labels=agent_ids, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.set_title("Repartition des couts", fontweight='bold')

    # distance per agent
    ax = axes[0][2]
    if agent_ids:
        dists = [per_agent[a]['distance'] for a in agent_ids]
        bars = ax.bar(agent_ids, dists, color=colors)
        for bar, d in zip(bars, dists):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                    f"{d:.0f}m", ha='center', va='bottom', fontsize=9)
    ax.set_ylabel("Distance (m)")
    ax.set_title("Distance par agent", fontweight='bold')

    # time per agent
    ax = axes[1][0]
    if agent_ids:
        times = [per_agent[a]['time_minutes'] for a in agent_ids]
        bars = ax.bar(agent_ids, times, color=colors)
        for bar, t in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                    f"{t:.1f}min", ha='center', va='bottom', fontsize=9)
    ax.set_ylabel("Temps (min)")
    ax.set_title("Temps par agent", fontweight='bold')

    # key metrics table
    ax = axes[1][1]
    ax.axis('off')
    data = [
        ["Distance totale", f"{metrics.get('total_distance_m', 0):.1f} m"],
        ["Cout total", f"{metrics.get('total_cost_euros', 0):.2f} EUR"],
        ["Makespan", f"{metrics.get('makespan_minutes', 0):.1f} min"],
        ["Equilibrage sigma", f"{metrics.get('load_balance_stddev', 0):.2f}"],
        ["Commandes OK", str(allocation.get('assigned_orders', 0))],
        ["Commandes echouees", str(allocation.get('failed_orders', 0))],
    ]
    tbl = ax.table(cellText=data, colLabels=["Indicateur", "Valeur"],
                   loc='center', cellLoc='left')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.2, 1.8)
    ax.set_title("Metriques cles", fontweight='bold')

    # orders per agent
    ax = axes[1][2]
    if agent_ids:
        n_orders = [len(per_agent[a]['orders']) for a in agent_ids]
        bars = ax.bar(agent_ids, n_orders, color=colors)
        for bar, n in zip(bars, n_orders):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                    str(n), ha='center', va='bottom', fontsize=10)
    ax.set_ylabel("Nombre de commandes")
    ax.set_title("Commandes par agent", fontweight='bold')

    fig.tight_layout()
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return save_path