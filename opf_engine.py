"""
OPF Engine — 3-Node Optimal Power Flow Solver
==============================================
Résout le dispatch économique avec contraintes de transmission
et extrait les prix nodaux (LMP) via les variables duales.

Topologie:
    Node A (G1: 40€/MWh, 0-100 MW) --Line A→C (max 80 MW)--> Node C (Load)
    Node B (G2: 50€/MWh, 0-80 MW)  --Line B→C (max 60 MW)--> Node C (Load)

Formulation nodale:
    On introduit des variables de flux (F_AC, F_BC) et une balance
    par nœud. Le dual de chaque balance = LMP de ce nœud.

    Variables: x = [P_G1, P_G2, F_AC, F_BC]

    min  40*P_G1 + 50*P_G2

    s.t. Balance A:  P_G1 - F_AC         = 0        (dual → LMP_A)
         Balance B:  P_G2        - F_BC   = 0        (dual → LMP_B)
         Balance C:        F_AC  + F_BC   = demand   (dual → LMP_C)
         F_AC <= 80   (capacité ligne A→C)
         F_BC <= 60   (capacité ligne B→C)
         0 <= P_G1 <= 100
         0 <= P_G2 <= 80
         F_AC, F_BC >= 0
"""

import numpy as np
from scipy.optimize import linprog


def solve_opf(demand: float) -> dict:
    """
    Résout le problème d'Optimal Power Flow pour une demande donnée.

    Variables de décision: x = [P_G1, P_G2, F_AC, F_BC]

    Parameters
    ----------
    demand : float
        Demande en MW au noeud C.

    Returns
    -------
    dict avec les clés:
        - "P_G1": production G1 (MW)
        - "P_G2": production G2 (MW)
        - "total_cost": coût total (€)
        - "lmp": dict des prix nodaux {"A": ..., "B": ..., "C": ...}
        - "line_usage": dict d'utilisation des lignes (%)
    """

    # =========================================================================
    # Vecteur de coût — on minimise le coût de production
    # =========================================================================
    # x = [P_G1, P_G2, F_AC, F_BC]
    # Seuls les générateurs ont un coût, pas les flux
    c = np.array([40, 50, 0, 0])

    # =========================================================================
    # Contraintes d'égalité — Balance de puissance PAR NOEUD
    # =========================================================================
    # C'est la clé : une balance par nœud permet d'extraire les LMPs
    # directement via les duals.
    #
    #              P_G1  P_G2  F_AC  F_BC
    # Balance A: [  1     0    -1     0  ] = 0    (production = flux sortant)
    # Balance B: [  0     1     0    -1  ] = 0    (production = flux sortant)
    # Balance C: [  0     0     1     1  ] = demand (flux entrant = demande)
    A_eq = np.array([
        [1, 0, -1,  0],   # Noeud A: P_G1 = F_AC
        [0, 1,  0, -1],   # Noeud B: P_G2 = F_BC
        [0, 0,  1,  1],   # Noeud C: F_AC + F_BC = demand
    ])
    b_eq = np.array([0, 0, demand])

    # =========================================================================
    # Contraintes d'inégalité — Limites de transmission
    # =========================================================================
    #              P_G1  P_G2  F_AC  F_BC
    # Ligne A→C: [  0     0     1     0  ] <= 80
    # Ligne B→C: [  0     0     0     1  ] <= 60
    A_ub = np.array([
        [0, 0, 1, 0],   # F_AC <= 80
        [0, 0, 0, 1],   # F_BC <= 60
    ])
    b_ub = np.array([80, 60])

    # =========================================================================
    # Bornes des variables
    # =========================================================================
    bounds = [
        (0, 100),   # P_G1: 0-100 MW
        (0, 80),    # P_G2: 0-80 MW
        (0, None),  # F_AC >= 0
        (0, None),  # F_BC >= 0
    ]

    # =========================================================================
    # Résolution du LP
    # =========================================================================
    result = linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        raise RuntimeError(f"Le solveur a échoué: {result.message}")

    P_G1, P_G2, F_AC, F_BC = result.x

    # =========================================================================
    # Extraction des LMPs — directement via les duals des balances nodales
    # =========================================================================
    # Chaque contrainte de balance a un dual = LMP du nœud correspondant.
    # Le dual répond à : "si la demande à ce nœud augmente de 1 MW,
    # de combien le coût total augmente-t-il ?"
    #
    # result.eqlin.marginals = [dual_A, dual_B, dual_C]
    lmp_a = result.eqlin.marginals[0]
    lmp_b = result.eqlin.marginals[1]
    lmp_c = result.eqlin.marginals[2]

    lmp = {"A": lmp_a, "B": lmp_b, "C": lmp_c}

    # =========================================================================
    # Calcul de l'utilisation des lignes (%)
    # =========================================================================
    line_usage = {
        "A->C": (F_AC / 80) * 100,
        "B->C": (F_BC / 60) * 100,
    }

    return {
        "P_G1": P_G1,
        "P_G2": P_G2,
        "total_cost": result.fun,
        "lmp": lmp,
        "line_usage": line_usage,
    }
