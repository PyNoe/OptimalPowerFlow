"""
Analysis — Visualisations du dispatch OPF et des prix nodaux (LMP).

4 graphes:
    1. Merit Order Curve (courbe d'offre par ordre de coût)
    2. LMP par noeud (barres)
    3. Utilisation des lignes (barres)
    4. Sensibilité: LMP & dispatch vs demande (multi-scénario)
"""

import numpy as np
import matplotlib.pyplot as plt
from opf_engine import solve_opf


# Données des générateurs (pour le merit order)
GENERATORS = [
    {"name": "G1 (Thermal)", "node": "A", "cost": 40, "capacity": 100},
    {"name": "G2 (Gas)", "node": "B", "cost": 50, "capacity": 80},
]


def plot_merit_order(ax):
    """
    Graphe 1: Merit Order Curve.
    Empile les générateurs par coût croissant pour montrer
    la courbe d'offre agrégée du marché.
    """
    # Trier par coût croissant
    sorted_gens = sorted(GENERATORS, key=lambda g: g["cost"])

    x_start = 0
    colors = ["#2196F3", "#FF9800"]
    for i, gen in enumerate(sorted_gens):
        ax.barh(
            0, gen["capacity"], left=x_start, height=0.5,
            color=colors[i], edgecolor="black", linewidth=0.8,
            label=f"{gen['name']} — {gen['cost']} €/MWh"
        )
        ax.text(
            x_start + gen["capacity"] / 2, 0,
            f"{gen['cost']}€", ha="center", va="center",
            fontweight="bold", fontsize=11,
        )
        x_start += gen["capacity"]

    ax.set_xlim(0, 200)
    ax.set_xlabel("Cumulative Capacity (MW)")
    ax.set_title("Merit Order Curve")
    ax.set_yticks([])
    ax.axvline(x=120, color="red", linestyle="--", linewidth=1.5, label="Demand = 120 MW")
    ax.legend(loc="upper right", fontsize=8)


def plot_lmp_bars(ax, results):
    """
    Graphe 2: LMP à chaque noeud.
    Met en évidence la différence de prix due à la congestion.
    """
    nodes = list(results["lmp"].keys())
    lmps = list(results["lmp"].values())
    colors = ["#2196F3", "#FF9800", "#F44336"]

    bars = ax.bar(nodes, lmps, color=colors, edgecolor="black", linewidth=0.8, width=0.5)

    for bar, val in zip(bars, lmps):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1f}€", ha="center", va="bottom", fontweight="bold")

    ax.set_ylabel("LMP (€/MWh)")
    ax.set_title("Locational Marginal Prices")
    ax.set_ylim(0, max(lmps) * 1.3)

    # Annoter la congestion si LMP_C > LMP_A
    if results["lmp"]["C"] > results["lmp"]["A"]:
        ax.annotate(
            "Congestion\npremium",
            xy=(2, results["lmp"]["A"]),
            xytext=(2.4, results["lmp"]["A"] + 3),
            fontsize=8, color="red",
            arrowprops=dict(arrowstyle="->", color="red"),
        )


def plot_line_usage(ax, results):
    """
    Graphe 3: Utilisation des lignes de transmission (%).
    """
    lines = list(results["line_usage"].keys())
    usage = list(results["line_usage"].values())
    capacities = [80, 60]
    flows = [results["P_G1"], results["P_G2"]]

    colors = ["#F44336" if u >= 99 else "#4CAF50" for u in usage]
    bars = ax.bar(lines, usage, color=colors, edgecolor="black", linewidth=0.8, width=0.5)

    for bar, u, f, cap in zip(bars, usage, flows, capacities):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{f:.0f}/{cap} MW\n({u:.0f}%)", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Usage (%)")
    ax.set_title("Transmission Line Usage")
    ax.set_ylim(0, 130)
    ax.axhline(y=100, color="red", linestyle="--", linewidth=1, alpha=0.7, label="Thermal limit")
    ax.legend(fontsize=8)


def plot_sensitivity(ax_dispatch, ax_lmp):
    """
    Graphe 4: Analyse de sensibilité — comment le dispatch et les LMPs
    évoluent quand la demande varie.
    """
    demands = np.arange(10, 170, 5)
    p_g1_list, p_g2_list = [], []
    lmp_a_list, lmp_b_list, lmp_c_list = [], [], []

    for d in demands:
        try:
            r = solve_opf(d)
            p_g1_list.append(r["P_G1"])
            p_g2_list.append(r["P_G2"])
            lmp_a_list.append(r["lmp"]["A"])
            lmp_b_list.append(r["lmp"]["B"])
            lmp_c_list.append(r["lmp"]["C"])
        except RuntimeError:
            # Demande infaisable (trop élevée)
            p_g1_list.append(np.nan)
            p_g2_list.append(np.nan)
            lmp_a_list.append(np.nan)
            lmp_b_list.append(np.nan)
            lmp_c_list.append(np.nan)

    # Dispatch vs demande
    ax_dispatch.stackplot(
        demands, p_g1_list, p_g2_list,
        labels=["G1 (40€/MWh)", "G2 (50€/MWh)"],
        colors=["#2196F3", "#FF9800"], alpha=0.8,
    )
    ax_dispatch.axvline(x=80, color="gray", linestyle=":", alpha=0.5)
    ax_dispatch.annotate("Line A→C saturates", xy=(80, 40), fontsize=7, color="gray")
    ax_dispatch.set_xlabel("Demand (MW)")
    ax_dispatch.set_ylabel("Production (MW)")
    ax_dispatch.set_title("Dispatch vs Demand")
    ax_dispatch.legend(loc="upper left", fontsize=8)

    # LMP vs demande
    ax_lmp.plot(demands, lmp_a_list, "o-", label="LMP Node A", color="#2196F3", markersize=3)
    ax_lmp.plot(demands, lmp_b_list, "s-", label="LMP Node B", color="#FF9800", markersize=3)
    ax_lmp.plot(demands, lmp_c_list, "^-", label="LMP Node C", color="#F44336", markersize=3)
    ax_lmp.axvline(x=80, color="gray", linestyle=":", alpha=0.5)
    ax_lmp.annotate("Congestion starts", xy=(80, 42), fontsize=7, color="gray")
    ax_lmp.set_xlabel("Demand (MW)")
    ax_lmp.set_ylabel("LMP (€/MWh)")
    ax_lmp.set_title("LMP vs Demand")
    ax_lmp.legend(fontsize=8)


def run_analysis():
    """Lance l'analyse complète avec les 4 graphes."""
    results = solve_opf(120)

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle("OPF Analysis — 3-Node Network (Demand = 120 MW)", fontsize=14, fontweight="bold")

    # Layout: 3 lignes
    #   Ligne 1: merit order (large)
    #   Ligne 2: LMP bars + line usage
    #   Ligne 3: sensitivity dispatch + sensitivity LMP
    gs = fig.add_gridspec(3, 2, hspace=0.45, wspace=0.3)

    ax_merit = fig.add_subplot(gs[0, :])
    ax_lmp = fig.add_subplot(gs[1, 0])
    ax_lines = fig.add_subplot(gs[1, 1])
    ax_sens_dispatch = fig.add_subplot(gs[2, 0])
    ax_sens_lmp = fig.add_subplot(gs[2, 1])

    plot_merit_order(ax_merit)
    plot_lmp_bars(ax_lmp, results)
    plot_line_usage(ax_lines, results)
    plot_sensitivity(ax_sens_dispatch, ax_sens_lmp)

    plt.savefig("opf_analysis.png", dpi=150, bbox_inches="tight")
    print("Figure saved: opf_analysis.png")
    plt.show()


if __name__ == "__main__":
    run_analysis()
