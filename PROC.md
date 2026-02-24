# PROC: Optimal Power Flow (OPF) & Nodal Pricing Simulator

## Context & Goal
Implement a 3-node Power Market simulator in Python. The goal is to solve a Dispatch problem (Minimizing total cost) while respecting physical transmission constraints (Thermal limits) and extracting Locational Marginal Prices (LMP) via shadow prices (dual variables).

## 1. System Topology
- **Node A:** Generator G1 (Thermal). Cost: 40€/MWh. Capacity: 0-100 MW.
- **Node B:** Generator G2 (Gas). Cost: 50€/MWh. Capacity: 0-80 MW.
- **Node C:** Load (Consumer). Demand: 120 MW.
- **Lines:**
    - Line A -> C: Max Capacity = 80 MW.
    - Line B -> C: Max Capacity = 60 MW.
    - (Ignore line losses for V1).

## 2. Mathematical Formulation
- **Objective:** Min Σ (Cost_i * P_i)
- **Constraints:**
    - Power Balance: P_G1 + P_G2 = Demand_C
    - Generation Limits: 0 ≤ P_Gi ≤ P_max_i
    - Transmission Limits: Flux(A->C) ≤ 80 ; Flux(B->C) ≤ 60

## 3. Implementation Instructions (Python)
- **Engine:** Use `scipy.optimize.linprog` (Method: 'highs') to solve the Linear Programming problem.
- **Dual Variables (LMPs):** Since `scipy` provides the shadow prices of constraints in the result object, extract the marginal cost of the "Power Balance" constraint at each node.
- **Output Requirements:**
    1. A summary table showing P_G1, P_G2, and Line usage (%).
    2. The calculated **LMP** at each node (A, B, C).
    3. A clear explanation in the logs: Why is the price at Node C higher than at Node A? (Hint: Congestion on line A-C).

## 4. Code Structure
- `opf_engine.py`: Contains the `solve_opf(demand)` function.
- `main.py`: Runs the 120 MW scenario and prints the analysis.
- `requirements.txt`: Include `scipy`, `numpy`, and `pandas`.

## 5. Verification Case
- If Demand = 120 MW:
    - G1 should produce 80 MW (limited by Line A-C).
    - G2 should produce 40 MW (to cover the rest).
    - LMP at Node C should be 50€/MWh (Price of the marginal unit G2).