"""
Main — Lance le scénario OPF et affiche l'analyse des résultats.
"""

import pandas as pd
from opf_engine import solve_opf


def print_results(results: dict, demand: float):
    """Affiche les résultats du dispatch et les LMPs."""

    print("=" * 60)
    print(f"  OPF Results — Demand: {demand} MW")
    print("=" * 60)

    # =========================================================================
    # Tableau de dispatch
    # =========================================================================
    # Crée un DataFrame pandas avec les colonnes:
    #   Generator | Node | Production (MW) | Cost (€/MWh) | Revenue (€)
    #
    # Hint:
    #   - G1 est au noeud A, coût 40€/MWh
    #   - G2 est au noeud B, coût 50€/MWh
    #   - Revenue = Production * LMP du noeud du générateur
    #     (les générateurs sont payés au LMP de leur noeud)

    dispatch_data = pd.DataFrame([
        {
            "Generator": "G1",
            "Node": "A",
            "Production (MW)": results["P_G1"],
            "Cost (€/MWh)": 40,
            "Revenue (€)": results["P_G1"] * results["lmp"]["A"],
        },
        {
            "Generator": "G2",
            "Node": "B",
            "Production (MW)": results["P_G2"],
            "Cost (€/MWh)": 50,
            "Revenue (€)": results["P_G2"] * results["lmp"]["B"],
        },
    ])
    print("\n--- Dispatch ---")
    print(dispatch_data.to_string(index=False))

    # =========================================================================
    # Tableau d'utilisation des lignes
    # =========================================================================
    # Crée un DataFrame avec les colonnes:
    #   Line | Flow (MW) | Capacity (MW) | Usage (%)
    #
    # Hint: les flux sont P_G1 pour A→C et P_G2 pour B→C

    lines_data = pd.DataFrame([
        {
            "Line": "A→C",
            "Flow (MW)": results["P_G1"],
            "Capacity (MW)": 80,
            "Usage (%)": results["line_usage"]["A->C"],
        },
        {
            "Line": "B→C",
            "Flow (MW)": results["P_G2"],
            "Capacity (MW)": 60,
            "Usage (%)": results["line_usage"]["B->C"],
        }
    ])
    print("\n--- Transmission Lines ---")
    print(lines_data.to_string(index=False))

    # =========================================================================
    # Tableau des LMPs
    # =========================================================================
    # Crée un DataFrame avec les colonnes:
    #   Node | LMP (€/MWh)

    lmp_data = pd.DataFrame([
        {"Node": "A", "LMP (€/MWh)": results["lmp"]["A"]},
        {"Node": "B", "LMP (€/MWh)": results["lmp"]["B"]},
        {"Node": "C", "LMP (€/MWh)": results["lmp"]["C"]},
    ])
    print("\n--- Locational Marginal Prices (LMP) ---")
    print(lmp_data.to_string(index=False))

    # =========================================================================
    # Analyse économique
    # =========================================================================
    # Affiche:
    #   - Le coût total de production
    #   - Le coût payé par le consommateur (= demand * LMP_C)
    #   - La "congestion rent" (= ce que le consommateur paie - ce que les
    #     générateurs reçoivent). C'est le revenu de congestion capturé par
    #     le gestionnaire du réseau (TSO).
    #
    # Hint: si LMP_C > LMP_A, il y a une rente de congestion.

    print("\n--- Economic Analysis ---")


    total_cost = results["total_cost"]
    print(f"  Total generation cost: {total_cost:.2f} €")

    consumer_payment = demand * results["lmp"]["C"]
    print(f"  Consumer payment:      {consumer_payment:.2f} €")

    congestion_rent = consumer_payment - total_cost
    print(f"  Congestion rent:       {congestion_rent:.2f} €")

    # =========================================================================
    # Explication de la congestion
    # =========================================================================
    # Écris un message qui explique POURQUOI le LMP à C est plus élevé que
    # le LMP à A quand la ligne A→C est congestionnée.
    #
    # Réfléchis en termes de:
    #   - Merit order: quel générateur est le moins cher ?
    #   - Sans contrainte réseau, que se passerait-il ?
    #   - Avec la contrainte, pourquoi G2 doit-il produire ?
    #   - Quel est le "marginal unit" au noeud C ?

    print("\n--- Congestion Analysis ---")
    print("  Explanation: The LMP at node C is higher than at node A because line A→C is congested. This means that the flow from A to C is limited by the capacity of this line. As a result, the marginal generator at node C must be more expensive than the marginal generator at node A. The LMP reflects the cost of supplying power at each node, considering both generation costs and transmission constraints.")


if __name__ == "__main__":
    DEMAND = 120  # MW

    results = solve_opf(DEMAND)
    print_results(results, DEMAND)
