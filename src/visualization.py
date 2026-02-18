import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path

ZONE_COLORS = {"A": "#4C8BF5", "B": "#34A853", "C": "#EA4335", "D": "#FBBC05", "E": "#9C27B0"}
AGENT_COLORS = {"robot": "#4C8BF5", "human": "#34A853", "cart": "#FF6D00"}
AISLE_COLOR = "#F0F0F0"
RACK_ALPHA = 0.35


def _agent_color(agent_id: str) -> str:
    if agent_id.upper().startswith('R'):
        return AGENT_COLORS["robot"]
    if agent_id.upper().startswith('H'):
        return AGENT_COLORS["human"]
    return AGENT_COLORS["cart"]


def _parse_location(loc) -> Tuple[float, float]:
    """Parse a location into (x+0.5, y+0.5) for cell-centre rendering.
    Accepts either a '(x, y)' string or a Location object with .x / .y attributes.
    """
    if isinstance(loc, str):
        loc = loc.strip().strip('()')
        x, y = map(int, loc.split(','))
    else:
        x, y = loc.x, loc.y
    return x + 0.5, y + 0.5


def _draw_base_grid(ax, width: int, height: int, zones_coords: Dict = None,
                    aisle_rows: List[int] = None):
    """Draw warehouse background: grey racks, white aisles, coloured zone cells."""
    if aisle_rows is None:
        aisle_rows = [2, 5]

    # 1. Full grey background (rack areas are non-navigable)
    ax.add_patch(mpatches.Rectangle(
        (0, 0), width, height,
        facecolor='#E0E0E0', edgecolor='none', zorder=0
    ))

    # 2. Aisle rows in white (navigable corridors)
    for y in aisle_rows:
        ax.add_patch(mpatches.Rectangle(
            (0, y), width, 1,
            facecolor='#FFFFFF', edgecolor='none', zorder=1
        ))
    # Entry/exit column (x=0) also navigable
    ax.add_patch(mpatches.Rectangle(
        (0, 0), 1, height,
        facecolor='#FFFFFF', edgecolor='none', zorder=1
    ))

    # 3. Zone rack cells coloured
    if zones_coords:
        for zone_id, coords in zones_coords.items():
            color = ZONE_COLORS.get(zone_id, "#CCCCCC")
            for (cx, cy) in coords:
                ax.add_patch(mpatches.Rectangle(
                    (cx, cy), 1, 1,
                    facecolor=color, alpha=0.6, edgecolor='none', zorder=2
                ))

    # 4. Grid lines
    for x in range(width + 1):
        ax.axvline(x, color='#AAAAAA', linewidth=0.4, zorder=3)
    for y in range(height + 1):
        ax.axhline(y, color='#AAAAAA', linewidth=0.4, zorder=3)

    ax.scatter([0.5], [0.5], marker='*', s=300, c='orange', zorder=7)

    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_aspect('equal')

def _l_path(x1: float, y1: float, x2: float, y2: float,
            aisle_ys: List[float] = None) -> Tuple[List[float], List[float]]:
    """
    Build a Manhattan path from (x1,y1) to (x2,y2) that stays in navigable
    corridors (aisle rows and the entry column x=0).
    Path strategy:
      - move vertically within entry column (x=0.5) to reach the target aisle
      - move horizontally along that aisle to x2
      - move vertically to y2
    This guarantees the line never cuts through rack cells.
    """
    if aisle_ys is None:
        aisle_ys = [2.5, 5.5]

    def nearest(y):
        return min(aisle_ys, key=lambda a: abs(a - y))

    a = nearest(y2)  # target aisle for the horizontal segment

    # already on same aisle row — pure horizontal
    if abs(y1 - a) < 0.01 and abs(y2 - a) < 0.01:
        return [x1, x2], [y1, y2]

    # go via entry column: x1->0.5 along aisle, down/up to a, across, then to y2
    if abs(y1 - a) < 0.01:
        # start is already on the aisle
        return [x1, x2, x2], [y1, y1, y2]

    # general: drop/rise to entry col, travel to aisle, cross, reach dest
    entry_x = 0.5
    xs = [x1, entry_x, entry_x, x2, x2]
    ys = [y1,      y1,       a,  a, y2]
    return xs, ys


def _build_zones_coords(warehouse) -> Dict:
    """Extract zone coord lists from a Warehouse object for background rendering."""
    zones_coords = {}
    for zone_id, zone in warehouse.zones.items():
        zones_coords[zone_id] = [(loc.x, loc.y) for loc in zone.coords]
    return zones_coords


# ── NEW: individual agent route ────────────────────────────────────────────

def plot_agent_route(route_info: Dict, warehouse_dims: Dict,
                     zones_coords: Dict = None,
                     save_path: Optional[str] = None):
    """
    Plot one agent's optimised route through the warehouse aisles.

    route_info    : one element from route_results (RouteOptimizer output)
    warehouse_dims: {"width": 10, "height": 8}
    zones_coords  : {"A": [(x, y), ...], ...}  for background colouring
    """
    width  = warehouse_dims.get("width", 10)
    height = warehouse_dims.get("height", 8)
    agent_id   = route_info['agent_id']
    agent_type = route_info['agent_type']
    color = _agent_color(agent_id)

    fig, ax = plt.subplots(figsize=(12, 8))
    _draw_base_grid(ax, width, height, zones_coords)

    steps  = route_info['route']
    coords = [_parse_location(s['location']) for s in steps]
    aisle_ys = [2.5, 5.5]

    # Draw each segment via aisle corridors (L-shaped paths, never through racks)
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        px, py = _l_path(x1, y1, x2, y2, aisle_ys)
        ax.plot(px, py, '-', color=color, linewidth=2.2, alpha=0.85, zorder=4)
        ax.annotate(
            "", xy=(px[-1], py[-1]), xytext=(px[-2], py[-2]),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6),
            zorder=5
        )

    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]

    for i, (step, (x, y)) in enumerate(zip(steps, coords)):
        loc = step['location']
        is_entry = (str(loc).replace(' ', '') == '(0,0)')
        ax.scatter([x], [y], c=color, s=200 if is_entry else 80,
                   marker='*' if is_entry else 'o',
                   zorder=6, edgecolors='white', linewidths=0.8)

        if step.get('products') and not is_entry:
            pids = list({
                p.get('product_id') if isinstance(p.get('product_id'), str)
                else (p['product'].id if hasattr(p.get('product'), 'id') else '')
                for p in step['products']
            })
            label = '\n'.join(pids[:3]) + ('+' if len(pids) > 3 else '')
            ax.annotate(
                label, (x, y),
                xytext=(6, 6), textcoords='offset points',
                fontsize=6.5, color='#333333',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7, ec='none')
            )

        ax.annotate(
            str(i), (x, y),
            xytext=(-10, 4), textcoords='offset points',
            fontsize=7, fontweight='bold', color=color
        )

    orders_str = ', '.join(route_info['orders'])
    ax.set_title(
        f"Tournée {agent_id} ({agent_type})  —  "
        f"{route_info['locations_visited']} stops  |  "
        f"{route_info['total_distance']:.0f}m  |  "
        f"{route_info['total_time_minutes']:.1f}min  |  "
        f"{route_info['total_cost_euros']:.2f}€\n"
        f"Commandes : {orders_str}",
        fontweight='bold', fontsize=10
    )

    legend_items = []
    if zones_coords:
        for z in zones_coords:
            if z in ZONE_COLORS:
                legend_items.append(
                    mpatches.Patch(color=ZONE_COLORS[z], alpha=RACK_ALPHA, label=f"Zone {z}")
                )
    legend_items.append(mpatches.Patch(color=AISLE_COLOR, label='Allée'))
    legend_items.append(plt.Line2D([0], [0], color=color, lw=2, label='Trajet'))
    ax.legend(handles=legend_items, loc='upper right', fontsize=8)

    fig.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ── NEW: all optimised routes on one map ───────────────────────────────────

def plot_all_routes_optimised(route_results: List[Dict], warehouse_dims: Dict,
                               zones_coords: Dict = None,
                               save_path: Optional[str] = None):
    """Overlay all agents' optimised routes on a single warehouse map."""
    width  = warehouse_dims.get("width", 10)
    height = warehouse_dims.get("height", 8)

    fig, ax = plt.subplots(figsize=(14, 9))
    _draw_base_grid(ax, width, height, zones_coords)

    for route_info in route_results:
        agent_id = route_info['agent_id']
        color    = _agent_color(agent_id)
        steps    = route_info['route']
        coords   = [_parse_location(s['location']) for s in steps]
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]

        label_done = False
        aisle_ys = [2.5, 5.5]
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            px, py = _l_path(x1, y1, x2, y2, aisle_ys)
            lbl = f"{agent_id} ({route_info['total_distance']:.0f}m)" if not label_done else None
            ax.plot(px, py, '-', color=color, linewidth=1.8, alpha=0.75,
                    zorder=4, label=lbl)
            ax.annotate("", xy=(px[-1], py[-1]), xytext=(px[-2], py[-2]),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2, alpha=0.7),
                        zorder=5)
            label_done = True
        ax.scatter(xs, ys, c=color, s=40, zorder=6)

    ax.set_title(
        "Toutes les tournées optimisées (TSP + CP-SAT)\n"
        "Les agents se déplacent uniquement dans les allées (y=2 et y=5)",
        fontweight='bold'
    )
    ax.legend(loc='upper right', fontsize=9)
    fig.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ── NEW: greedy vs optimised side-by-side ─────────────────────────────────

def plot_greedy_vs_optimised(greedy_result: Dict, route_results: List[Dict],
                              warehouse_dims: Dict, zones_coords: Dict = None,
                              greedy_total_dist: float = 0,
                              save_path: Optional[str] = None):
    """Side-by-side: greedy allocation sketch vs optimised TSP+CP-SAT routes."""
    width  = warehouse_dims.get("width", 10)
    height = warehouse_dims.get("height", 8)

    greedy_agents = list({a['agent_id'] for a in greedy_result.get('successful', [])})
    palette = plt.cm.Set1(np.linspace(0, 0.9, max(len(greedy_agents), 1)))
    greedy_colors = {aid: palette[i] for i, aid in enumerate(greedy_agents)}

    fig, axes = plt.subplots(1, 2, figsize=(20, 9))

    # ── LEFT: Greedy ──────────────────────────────────────────────────────
    ax = axes[0]
    _draw_base_grid(ax, width, height, zones_coords)

    agent_orders: Dict[str, List[str]] = {}
    for s in greedy_result.get('successful', []):
        agent_orders.setdefault(s['agent_id'], []).append(s['order_id'])

    # For each greedy agent, draw the optimised route path in greedy colour
    # (greedy doesn't produce its own route; we use pick-point positions)
    for agent_id, order_ids in agent_orders.items():
        color = greedy_colors.get(agent_id, 'gray')
        route_match = next((r for r in route_results if r['agent_id'] == agent_id), None)
        if route_match is None:
            continue
        steps  = route_match['route']
        coords = [_parse_location(s['location']) for s in steps]
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        aisle_ys = [2.5, 5.5]
        label_done = False
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]; x2, y2 = coords[i+1]
            px, py = _l_path(x1, y1, x2, y2, aisle_ys)
            lbl = f"{agent_id} ({len(order_ids)} cmd)" if not label_done else None
            ax.plot(px, py, '-', color=color, linewidth=1.6, alpha=0.75, zorder=4, label=lbl)
            label_done = True
        ax.scatter(xs, ys, c=color, s=35, zorder=6)

    ax.set_title(
        f"Allocation Gloutonne\nDistance estimée : {greedy_total_dist:.0f}m",
        fontweight='bold', fontsize=11
    )
    ax.legend(loc='upper right', fontsize=8)

    # ── RIGHT: Optimised ──────────────────────────────────────────────────
    ax = axes[1]
    _draw_base_grid(ax, width, height, zones_coords)
    opt_total = sum(r['total_distance'] for r in route_results)

    for route_info in route_results:
        agent_id = route_info['agent_id']
        color    = _agent_color(agent_id)
        steps    = route_info['route']
        coords   = [_parse_location(s['location']) for s in steps]
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]

        aisle_ys = [2.5, 5.5]
        label_done = False
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]; x2, y2 = coords[i+1]
            px, py = _l_path(x1, y1, x2, y2, aisle_ys)
            lbl = f"{agent_id} ({route_info['total_distance']:.0f}m)" if not label_done else None
            ax.plot(px, py, '-', color=color, linewidth=1.8, alpha=0.8, zorder=4, label=lbl)
            ax.annotate("", xy=(px[-1], py[-1]), xytext=(px[-2], py[-2]),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.3, alpha=0.7),
                        zorder=5)
            label_done = True
        ax.scatter(xs, ys, c=color, s=45, zorder=6)

    reduction = ((greedy_total_dist - opt_total) / greedy_total_dist * 100
                 if greedy_total_dist > 0 else 0)
    ax.set_title(
        f"TSP + CP-SAT Optimisé\n"
        f"Distance totale : {opt_total:.0f}m  (−{reduction:.0f}% vs glouton)",
        fontweight='bold', fontsize=11
    )
    ax.legend(loc='upper right', fontsize=8)

    fig.suptitle("Comparaison Glouton vs Optimisé", fontsize=14, fontweight='bold')
    fig.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ── Unchanged helpers ──────────────────────────────────────────────────────

def plot_warehouse(warehouse: Dict, products: List[Dict], save_path: Optional[str] = None):
    width, height = warehouse["width"], warehouse["height"]
    zones_coords = {}
    for p in products:
        z = p.get("zone")
        if z:
            zones_coords.setdefault(z, []).append((p["x"], p["y"]))

    fig, ax = plt.subplots(figsize=(13, 9))
    _draw_base_grid(ax, width, height, zones_coords)

    legend_patches = [
        mpatches.Patch(color=ZONE_COLORS[z], alpha=RACK_ALPHA, label=f"Zone {z} (racks)")
        for z in ZONE_COLORS if z in zones_coords
    ]
    legend_patches.append(mpatches.Patch(color=AISLE_COLOR, label="Allées (circulation)"))
    ax.set_title(
        "Plan de l'entrepôt OptiPick\n(agents se déplacent uniquement dans les allées)",
        fontweight='bold'
    )
    ax.legend(handles=legend_patches, loc='upper right', fontsize=8)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_agent_utilization(utilization_dict: Dict, save_path: Optional[str] = None):
    agents = list(utilization_dict.keys())
    pcts   = list(utilization_dict.values())
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
    ax.set_title("Comparaison des distances (allées uniquement)", fontweight='bold')
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
    ax.set_title("Coûts par agent", fontweight='bold')
    ax.set_ylabel("Coût (EUR)")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_product_frequency(frequency_dict: Dict, top_n: int = 10,
                            save_path: Optional[str] = None):
    items = sorted(frequency_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    if not items:
        return
    labels, values = zip(*items)
    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.5 + 1)))
    ax.barh(labels, values, color="#4C8BF5")
    ax.set_xlabel("Quantité commandée")
    ax.set_title(f"Top {top_n} produits", fontweight='bold')
    ax.invert_yaxis()
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_zone_traffic(traffic_dict: Dict, save_path: Optional[str] = None):
    zones  = list(traffic_dict.keys())
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


def create_zone_heatmap(warehouse: Dict, visit_counts: Dict,
                         save_path: Optional[str] = None):
    import seaborn as sns
    width, height = warehouse["width"], warehouse["height"]
    grid = np.zeros((height, width))
    for (x, y), count in visit_counts.items():
        if 0 <= x < width and 0 <= y < height:
            grid[y][x] = count
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(grid, annot=True, fmt='.0f', cmap="YlOrRd",
                linewidths=0.5, linecolor='#CCCCCC', ax=ax)
    ax.set_title("Heatmap des pick points visités (allées)", fontweight='bold')
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def create_dashboard(allocation: Dict, route_results: List[Dict], metrics: Dict,
                     warehouse: Dict, save_path: str = "results/dashboard.png"):
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle("OptiPick – Dashboard", fontsize=15, fontweight='bold')

    per_agent  = metrics.get('per_agent', {})
    agent_ids  = list(per_agent.keys())
    colors     = [_agent_color(a) for a in agent_ids]
    total_time = metrics.get('makespan_minutes', 1) or 1

    ax = axes[0][0]
    if agent_ids:
        utils = [round(per_agent[a]['time_minutes'] / total_time * 100, 1) for a in agent_ids]
        bars = ax.barh(agent_ids, utils, color=colors)
        for bar, pct in zip(bars, utils):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"{pct}%", va='center', fontsize=9)
        ax.set_xlim(0, 120)
    ax.set_title("Utilisation des agents", fontweight='bold')

    ax = axes[0][1]
    if agent_ids:
        costs = [per_agent[a]['cost_euros'] for a in agent_ids]
        if sum(costs) > 0:
            ax.pie(costs, labels=agent_ids, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.set_title("Répartition des coûts", fontweight='bold')

    ax = axes[0][2]
    if agent_ids:
        dists = [per_agent[a]['distance'] for a in agent_ids]
        bars = ax.bar(agent_ids, dists, color=colors)
        for bar, d in zip(bars, dists):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                    f"{d:.0f}m", ha='center', va='bottom', fontsize=9)
    ax.set_ylabel("Distance allées (m)")
    ax.set_title("Distance par agent", fontweight='bold')

    ax = axes[1][0]
    if agent_ids:
        times = [per_agent[a]['time_minutes'] for a in agent_ids]
        bars = ax.bar(agent_ids, times, color=colors)
        for bar, t in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                    f"{t:.1f}min", ha='center', va='bottom', fontsize=9)
    ax.set_ylabel("Temps (min)")
    ax.set_title("Temps par agent", fontweight='bold')

    ax = axes[1][1]
    ax.axis('off')
    data = [
        ["Distance totale (allées)", f"{metrics.get('total_distance_m', 0):.1f} m"],
        ["Coût total",               f"{metrics.get('total_cost_euros', 0):.2f} EUR"],
        ["Makespan",                 f"{metrics.get('makespan_minutes', 0):.1f} min"],
        ["Équilibrage sigma",        f"{metrics.get('load_balance_stddev', 0):.2f}"],
        ["Commandes OK",             str(allocation.get('assigned_orders', 0))],
        ["Commandes échouées",       str(allocation.get('failed_orders', 0))],
    ]
    tbl = ax.table(cellText=data, colLabels=["Indicateur", "Valeur"],
                   loc='center', cellLoc='left')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1.2, 1.8)
    ax.set_title("Métriques clés", fontweight='bold')

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