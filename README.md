# 🚀 OptiPick — Optimisation de Tournées d'Entrepôt

Projet de Programmation Logique et par Contraintes — L2 Informatique · HETIC 2025

## 📋 Description

Système d'optimisation pour la préparation de commandes en entrepôt avec coopération humain-robot. Le système modélise un entrepôt 10×8 avec 5 zones, 7 agents (3 robots, 2 humains, 2 chariots) et 12 commandes journalières.

L'allocation optimale est résolue via **OR-Tools CP-SAT** (programmation par contraintes), et les tournées sont optimisées via **OR-Tools Routing** (TSP).

## 🛠️ Installation

```bash
# Cloner le repository
git clone [URL_DU_REPO]
cd optipick

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## 🚀 Utilisation

```bash
python main.py
```

Les résultats sont exportés dans le dossier `results/` :
- `allocation_greedy.json` — allocation gloutonne (baseline)
- `allocation_optimal.json` — allocation CP-SAT
- `routes.json` — tournées optimisées
- `metrics.json` — métriques de performance
- `dashboard.png` — dashboard de visualisation

## 🧪 Tests

```bash
pytest tests/ -v
```

## 👥 Équipe

- **Lead technique** : Jules
- **Contraintes & Tests** : Emery
- **Visualisation & Métriques** : Sarah

## 📊 Résultats

| Métrique | Glouton | CP-SAT + TSP |
|---|---|---|
| Distance totale | 302m | 60m |
| Réduction distance | — | **-80%** |
| Coût total | 2,80€ | 0,62€ |
| Réduction coût | — | **-78%** |
| Commandes traitées | 12/12 | 12/12 |
| Violations contraintes | 0 | 0 |
| Temps de résolution | — | 0,025s |

## 🏗️ Architecture

```
optipick/
├── data/               # Fichiers JSON de configuration
├── src/
│   ├── models.py       # Classes Warehouse, Product, Agent, Order
│   ├── loader.py       # Chargement des données JSON
│   ├── constraints.py  # Vérification des contraintes (C1-C4)
│   ├── allocation.py   # Allocation gloutonne (baseline)
│   ├── optimization.py # Allocation optimale CP-SAT
│   ├── routing.py      # Optimisation des tournées TSP
│   ├── storage.py      # Analyse et optimisation du stockage
│   ├── visualization.py# Graphiques et dashboard
│   ├── metrics.py      # Calcul des métriques de performance
│   └── utils.py        # Fonctions utilitaires
├── tests/              # Tests unitaires pytest (30+ tests)
├── results/            # Résultats générés automatiquement
├── main.py             # Point d'entrée
└── requirements.txt
```

## 📦 Dépendances principales

- `ortools` — CP-SAT et TSP (Google OR-Tools)
- `matplotlib` / `seaborn` — Visualisations
- `numpy` / `pandas` — Calculs numériques
- `pytest` — Tests unitaires
