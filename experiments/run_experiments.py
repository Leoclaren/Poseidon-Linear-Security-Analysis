#!/usr/bin/env python3
"""
Batch experiments for Poseidon1: run tests for t = 4..8 and collect results and plots.

Usage:
    python experiments/run_experiments.py

Outputs:
    - results/t{t}.json for each t
    - results/summary.json aggregated summary
    - figures/dashboard_t{t}.png for each t (requires matplotlib)

This script is deterministic for t in 3..8 because poseidon.matrices provides
precomputed deterministic MDS matrices (Cauchy-based). For larger t the
matrix finder may be randomized and slower.
"""

import json
import os
import random
from pathlib import Path

# Make runs deterministic where possible
random.seed(0)

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT.parent / "results"
FIGURES = ROOT.parent / "figures"
RESULTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)

TS = [4, 5, 6, 7, 8]
R_P = 6   # short test; increase as needed
ALPHA = 5
DELTA = 4

summary = {}

for t in TS:
    print(f"Running experiments for t={t}...")
    res = {"t": t, "r_p": R_P, "alpha": ALPHA}

    # 1) Matrix / branch checks
    try:
        from poseidon.matrices import get_matrix, branch_number
        M_mds = get_matrix("mds", t)
        bn_mds = branch_number(M_mds)
        res["mds_branch_number"] = int(bn_mds)
        res["mds_is_mds"] = bn_mds >= t + 1
    except Exception as e:
        res["mds_error"] = str(e)

    try:
        M_identity = get_matrix("identity", t)
        res["identity_branch_number"] = int(branch_number(M_identity))
    except Exception as e:
        res["identity_error"] = str(e)

    try:
        M_circ = get_matrix("circulant", t)
        res["circulant_branch_number"] = int(branch_number(M_circ))
    except Exception as e:
        res["circulant_error"] = str(e)

    # 2) Invariant subspace demo (if available)
    try:
        from attacks.invariant_subspace import run_attack_demo
        atk = run_attack_demo(t=t, r_p=R_P, alpha=ALPHA, delta_val=DELTA, verbose=False)
        # compact results
        compact = {}
        for name, info in atk.items():
            compact[name] = {
                "invariant_holds": info["subspace"]["invariant_subspace_holds"],
                "coord0_activations": int(info["subspace"]["coord0_activations"]),
                "prediction_correct": bool(info["prediction"]["prediction_correct"]),
            }
        res["invariant_attack"] = compact
    except Exception as e:
        res["invariant_attack_error"] = str(e)

    # 3) Compute stats (if available)
    try:
        from analysis.statistics import compute_stats
        stats = compute_stats(t=t, r_p=R_P, alpha=ALPHA, delta_val=DELTA)
        # reduce to serializable values
        small_stats = {}
        for name, s in stats.items():
            small_stats[name] = {
                "branch_number": int(s.get("branch_number", -1)),
                "is_mds": bool(s.get("is_mds", False)),
                "rounds_to_full_diffusion": s.get("rounds_to_full_diffusion"),
                "final_diffusion": float(s.get("final_diffusion", 0.0)),
                "vulnerable": bool(s.get("vulnerable", False)),
            }
        res["stats"] = small_stats
    except Exception as e:
        res["stats_error"] = str(e)

    # 4) Save per-t JSON
    out_path = RESULTS / f"t{t}.json"
    with open(out_path, "w") as f:
        json.dump(res, f, indent=2)
    print(f"Wrote: {out_path}")

    summary[f"t{t}"] = res

    # 5) Generate plot dashboard image for this t (if matplotlib available)
    try:
        import plot as plotmod
        img_path = FIGURES / f"dashboard_t{t}.png"
        plotmod.plot_all(t=t, r_p=R_P, alpha=ALPHA, delta_val=DELTA, save=str(img_path))
        print(f"Saved dashboard plot: {img_path}")
    except Exception as e:
        print(f"Plot generation skipped/failed for t={t}: {e}")
        summary[f"t{t}"]["plot_error"] = str(e)

# Write aggregated summary
with open(RESULTS / "summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("All experiments done.")
