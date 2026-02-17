import matplotlib.pyplot as plt

ZONE_COLORS = {"A": "blue", "B": "green", "C": "red", "D": "yellow", "E": "purple"}


# =====================================================
# WAREHOUSE DE BASE
# =====================================================
def plot_warehouse(warehouse, products, save_path=None):
    fig, ax = plt.subplots(figsize=(10, 8))
    width, height = warehouse["width"], warehouse["height"]

    for x in range(width + 1):
        ax.axvline(x, color='gray', linewidth=0.5)
    for y in range(height + 1):
        ax.axhline(y, color='gray', linewidth=0.5)

    for zone, color in ZONE_COLORS.items():
        zone_cells = [(p["x"], p["y"]) for p in products if p["zone"] == zone]
        if zone_cells:
            xs, ys = zip(*zone_cells)
            ax.scatter(xs, ys, c=color, label=f"Zone {zone}", s=100)

    ax.scatter([0], [0], marker="*", s=200, c="orange", label="Entrée")

    ax.set_xlim(-1, width)
    ax.set_ylim(-1, height)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Warehouse Layout")
    ax.legend()
    ax.set_aspect('equal')

    if save_path:
        plt.savefig(save_path)
    plt.show()


# =====================================================
# UTILISATION AGENTS
# =====================================================
def plot_agent_utilization(utilization_dict, save_path=None):
    agent_ids = list(utilization_dict.keys())
    percentages = list(utilization_dict.values())

    colors = []
    for agent_id in agent_ids:
        if "robot" in agent_id.lower():
            colors.append("skyblue")
        elif "humain" in agent_id.lower():
            colors.append("lightgreen")
        else:
            colors.append("orange")

    fig, ax = plt.subplots(figsize=(8, len(agent_ids)*0.5 + 2))
    ax.barh(agent_ids, percentages, color=colors)

    for i, v in enumerate(percentages):
        ax.text(v + 1, i, f"{v}%", va='center')

    ax.set_xlabel("% Utilisation")
    ax.set_title("Utilisation des agents (%)")

    if save_path:
        plt.savefig(save_path)
    plt.show()


# =====================================================
# VISUALISATION ROUTES AVANCÉES
# =====================================================
def get_agent_color(agent_id):
    if "robot" in agent_id.lower():
        return "blue"
    elif "humain" in agent_id.lower():
        return "green"
    else:
        return "orange"


# -------------------------------------------------
# ROUTE SIMPLE
# -------------------------------------------------
def plot_route(warehouse, route, agent_id, save_path=None):
    fig, ax = plt.subplots(figsize=(8, 6))
    width, height = warehouse["width"], warehouse["height"]

    for x in range(width + 1):
        ax.axvline(x, color='lightgray', linewidth=0.5)
    for y in range(height + 1):
        ax.axhline(y, color='lightgray', linewidth=0.5)

    color = get_agent_color(agent_id)

    xs = [p["x"] for p in route]
    ys = [p["y"] for p in route]

    ax.plot(xs, ys, marker='o', color=color)

    for i, (x, y) in enumerate(zip(xs, ys)):
        ax.text(x, y, str(i + 1))

    for i in range(len(xs) - 1):
        ax.annotate(
            "",
            xy=(xs[i+1], ys[i+1]),
            xytext=(xs[i], ys[i]),
            arrowprops=dict(arrowstyle="->", color=color)
        )

    ax.set_title(f"Route de {agent_id}")
    ax.set_xlim(-1, width)
    ax.set_ylim(-1, height)
    ax.set_aspect("equal")

    if save_path:
        plt.savefig(save_path)
    plt.show()


# -------------------------------------------------
# TOUTES LES ROUTES
# -------------------------------------------------
def plot_all_routes(warehouse, all_routes, save_path=None):
    fig, ax = plt.subplots(figsize=(8, 6))
    width, height = warehouse["width"], warehouse["height"]

    for x in range(width + 1):
        ax.axvline(x, color='lightgray', linewidth=0.5)
    for y in range(height + 1):
        ax.axhline(y, color='lightgray', linewidth=0.5)

    for agent_id, route in all_routes.items():
        color = get_agent_color(agent_id)
        xs = [p["x"] for p in route]
        ys = [p["y"] for p in route]

        ax.plot(xs, ys, marker='o', alpha=0.7, label=agent_id, color=color)

    ax.legend()
    ax.set_title("Toutes les tournées")
    ax.set_xlim(-1, width)
    ax.set_ylim(-1, height)
    ax.set_aspect("equal")

    if save_path:
        plt.savefig(save_path)
    plt.show()


# -------------------------------------------------
# COMPARAISON AVANT / APRÈS
# -------------------------------------------------
def plot_route_comparison(warehouse, route_before, route_after, agent_id, save_path=None):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    width, height = warehouse["width"], warehouse["height"]
    color = get_agent_color(agent_id)

    for ax, route, title in zip(
        axes,
        [route_before, route_after],
        ["Avant optimisation", "Après optimisation"]
    ):
        for x in range(width + 1):
            ax.axvline(x, color='lightgray', linewidth=0.5)
        for y in range(height + 1):
            ax.axhline(y, color='lightgray', linewidth=0.5)

        xs = [p["x"] for p in route]
        ys = [p["y"] for p in route]

        ax.plot(xs, ys, marker='o', color=color)
        ax.set_title(title)
        ax.set_xlim(-1, width)
        ax.set_ylim(-1, height)
        ax.set_aspect("equal")

    fig.suptitle(f"Comparaison route - {agent_id}")

    if save_path:
        plt.savefig(save_path)
    plt.show()


# =====================================================
# GRAPHIQUES DE COMPARAISON
# =====================================================

# -------------------------------------------------
# COMPARAISON DES DISTANCES
# -------------------------------------------------
def plot_distance_comparison(scenarios_dict, save_path=None):
    """
    scenarios_dict = {
        "Glouton": 120,
        "TSP": 95,
        "CP-SAT": 80,
        "Batching": 90
    }
    """
    scenarios = list(scenarios_dict.keys())
    distances = list(scenarios_dict.values())

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(scenarios, distances)

    # Affichage valeur sur chaque barre
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height,
            f"{height}",
            ha='center',
            va='bottom'
        )

    ax.set_title("Comparaison des distances (m)")
    ax.set_ylabel("Distance (m)")

    if save_path:
        plt.savefig(save_path)

    plt.show()


# -------------------------------------------------
# RÉPARTITION DES COÛTS
# -------------------------------------------------
def plot_cost_breakdown(agents_costs, save_path=None):
    """
    agents_costs = {
        "robot_1": 200,
        "humain_1": 150,
        "chariot_1": 100
    }
    """
    labels = list(agents_costs.keys())
    values = list(agents_costs.values())

    colors = []
    for agent in labels:
        if "robot" in agent.lower():
            colors.append("skyblue")
        elif "humain" in agent.lower():
            colors.append("lightgreen")
        else:
            colors.append("orange")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(labels, values, color=colors)

    # Afficher valeurs
    for i, v in enumerate(values):
        ax.text(i, v, f"{v}", ha='center', va='bottom')

    ax.set_title("Répartition des coûts par agent")
    ax.set_ylabel("Coût")

    if save_path:
        plt.savefig(save_path)

    plt.show()


# -------------------------------------------------
# COMPARAISON DES TEMPS
# -------------------------------------------------
def plot_time_comparison(scenarios_dict, save_path=None):
    """
    scenarios_dict = {
        "Glouton": 45,
        "TSP": 38,
        "CP-SAT": 30,
        "Batching": 35
    }
    """
    scenarios = list(scenarios_dict.keys())
    times = list(scenarios_dict.values())

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(scenarios, times)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height,
            f"{height}",
            ha='center',
            va='bottom'
        )

    ax.set_title("Comparaison des temps")
    ax.set_ylabel("Temps")

    if save_path:
        plt.savefig(save_path)

    plt.show()

