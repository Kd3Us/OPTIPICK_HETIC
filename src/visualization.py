import matplotlib.pyplot as plt

ZONE_COLORS = {"A": "blue", "B": "green", "C": "red", "D": "yellow", "E": "purple"}

def plot_warehouse(warehouse, products, save_path=None):
    """
    Visualisation du warehouse et des produits.
    
    Args:
        warehouse (dict): dimensions {'width': int, 'height': int}
        products (list): [{'x': int, 'y': int, 'zone': str, 'name': str}]
        save_path (str, optional): chemin pour sauvegarder la figure
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    width, height = warehouse["width"], warehouse["height"]
    
    # Grille
    for x in range(width + 1):
        ax.axvline(x, color='gray', linewidth=0.5)
    for y in range(height + 1):
        ax.axhline(y, color='gray', linewidth=0.5)
    
    # Colorier zones
    for zone, color in ZONE_COLORS.items():
        zone_cells = [(p["x"], p["y"]) for p in products if p["zone"] == zone]
        if zone_cells:
            xs, ys = zip(*zone_cells)
            ax.scatter(xs, ys, c=color, label=f"Zone {zone}", s=100)
    
    # Entrée
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


def plot_agent_utilization(utilization_dict, save_path=None):
    """
    Diagramme en barres horizontales de l'utilisation des agents.
    
    Args:
        utilization_dict (dict): {agent_id: % utilisation}
        save_path (str, optional): chemin pour sauvegarder
    """
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
    
    # Ajouter pourcentage sur chaque barre
    for i, v in enumerate(percentages):
        ax.text(v + 1, i, f"{v}%", va='center')
    
    ax.set_xlabel("% Utilisation")
    ax.set_title("Utilisation des agents (%)")
    
    if save_path:
        plt.savefig(save_path)
    plt.show()

