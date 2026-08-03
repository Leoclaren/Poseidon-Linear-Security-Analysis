"""
Matplotlib visualizations for Poseidon1 analysis.

Usage:
    python plot.py --mode diffusion --r_p 10
    python plot.py --mode branch
    python plot.py --mode stats
    python plot.py --mode degree
    python plot.py --mode all
"""

import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from analysis.diffusion import compare_matrices
from analysis.statistics import compute_stats
from analysis.degree import compare_matrices_degree
from poseidon.matrices import MATRIX_NAMES, branch_number, get_matrix


COLORS = {
    "mds": "#2ecc71",        # green  = secure
    "identity": "#e74c3c",   # red    = vulnerable
    "circulant": "#e67e22",  # orange = non-MDS
    "poseidon2": "#3498db",  # blue   = Poseidon2-like
}

LABELS = {
    "mds": "MDS (secure)",
    "identity": "Identity / non-MDS (vulnerable)",
    "circulant": "Circulant / non-MDS",
    "poseidon2": "Poseidon2-like (sparse)",
}


# ---------------------------------------------------------------------------
# Plot 1: Diffusion coefficient over rounds
# ---------------------------------------------------------------------------

def plot_diffusion(t=3, r_p=10, alpha=5, delta_val=4, matrices=None, save=None):
    data = compare_matrices(t=t, r_p=r_p, alpha=alpha, delta_val=delta_val)

    fig, ax = plt.subplots(figsize=(9, 5))
    for name, trace in data.items():
        rounds = [x[0] for x in trace]
        diff   = [x[1] for x in trace]
        color = COLORS.get(name, None)
        label = LABELS.get(name, name)
        ax.plot(rounds, diff, marker="o", linewidth=2,
                color=color, label=label)

    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="Full diffusion (D=1)")
    ax.set_xlabel("Round", fontsize=12)
    ax.set_ylabel("Diffusion coefficient D(r)", fontsize=12)
    ax.set_title(
        f"Diffusion over {r_p} partial rounds  |  t={t}, α={alpha}, Δ=(0,…,0,{delta_val})",
        fontsize=13,
    )
    ax.set_ylim(-0.05, 1.15)
    ax.set_xticks(range(r_p + 1))
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=150)
        print(f"Saved: {save}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Plot 1b: Algebraic degree over rounds
# ---------------------------------------------------------------------------

def plot_degree(t=3, r_p=10, alpha=5, matrices=None, save=None):
    if matrices is None:
        matrices = list(MATRIX_NAMES.keys()) + ["poseidon2"]
    data = compare_matrices_degree(matrix_names=matrices, t=t, r_p=r_p, alpha=alpha)

    fig, ax = plt.subplots(figsize=(9, 5))
    for name, history in data.items():
        rounds = [h[0] for h in history]
        maxdeg = [h[2] for h in history]
        color = COLORS.get(name, None)
        label = LABELS.get(name, name)
        ax.plot(rounds, maxdeg, marker='o', linewidth=2, color=color, label=label)

    ax.set_xlabel('Round', fontsize=12)
    ax.set_ylabel('Max algebraic degree (upper bound)', fontsize=12)
    ax.set_title(f'Algebraic degree growth over partial rounds  |  t={t}, α={alpha}', fontsize=13)
    ax.set_xticks(range(r_p + 1))
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=150)
        print(f"Saved: {save}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Plot 2: Branch numbers bar chart
# ---------------------------------------------------------------------------

def plot_branch_numbers(t=3, save=None):
    names = list(MATRIX_NAMES.keys())
    # include poseidon2 label for plotting even if not in MATRIX_NAMES
    if 'poseidon2' not in names:
        names.append('poseidon2')
    bns   = [branch_number(MATRIX_NAMES[n]) if n in MATRIX_NAMES else None for n in names]
    threshold = t + 1

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(
        [LABELS.get(n, n) for n in names],
        [bn if bn is not None else 0 for bn in bns],
        color=[COLORS.get(n, '#cccccc') for n in names],
        edgecolor="black",
        linewidth=0.8,
    )
    ax.axhline(threshold, color="steelblue", linestyle="--", linewidth=2,
               label=f"MDS threshold (t+1 = {threshold})")

    for bar, bn in zip(bars, bns):
        val = bn if bn is not None else 'n/a'
        ax.text(bar.get_x() + bar.get_width() / 2, (bn if bn is not None else 0) + 0.05,
                str(val), ha="center", va="bottom", fontsize=12, fontweight="bold")

    ax.set_ylabel("Branch number B(M)", fontsize=12)
    ax.set_title(f"Branch numbers  |  t={t}", fontsize=13)
    ax.set_ylim(0, max([x for x in (bns + [threshold]) if x is not None]) + 1.5)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=150)
        print(f"Saved: {save}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Plot 3: Statistics table / heatmap
# ---------------------------------------------------------------------------

def plot_stats_overview(t=3, r_p=6, alpha=5, delta_val=4, save=None):
    stats = compute_stats(t=t, r_p=r_p, alpha=alpha, delta_val=delta_val)

    names  = list(stats.keys())
    metrics = ["branch_number", "is_mds", "rounds_to_full_diffusion", "final_diffusion", "vulnerable"]
    nice   = ["Branch #", "Is MDS?", "Rounds → full diff.", "Final D(r)", "Vulnerable?"]

    cell_text = []
    cell_colors = []
    for name in names:
        s = stats[name]
        row = [
            str(s["branch_number"]),
            "YES" if s["is_mds"] else "NO",
            str(s["rounds_to_full_diffusion"]) if s["rounds_to_full_diffusion"] is not None else "Never",
            f"{s['final_diffusion']:.2f}",
            "YES" if s["vulnerable"] else "NO",
        ]
        vuln = s["vulnerable"]
        row_colors = []
        for i, val in enumerate(row):
            if metrics[i] in ("is_mds", "vulnerable"):
                if val == "YES" and metrics[i] == "is_mds":
                    row_colors.append("#d5f5e3")
                elif val == "NO" and metrics[i] == "is_mds":
                    row_colors.append("#fadbd8")
                elif val == "YES" and metrics[i] == "vulnerable":
                    row_colors.append("#fadbd8")
                else:
                    row_colors.append("#d5f5e3")
            elif metrics[i] == "rounds_to_full_diffusion":
                row_colors.append("#d5f5e3" if val not in ("Never", "None") else "#fadbd8")
            else:
                row_colors.append("white")
        cell_text.append(row)
        cell_colors.append(row_colors)

    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis("off")
    table = ax.table(
        cellText=cell_text,
        rowLabels=[LABELS[n] for n in names],
        colLabels=nice,
        cellColours=cell_colors,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.4, 1.8)

    ax.set_title(
        f"Security overview  |  t={t}, r_p={r_p}, α={alpha}",
        fontsize=13, pad=20,
    )
    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=150)
        print(f"Saved: {save}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Plot 4: Combined dashboard
# ---------------------------------------------------------------------------

def plot_all(t=3, r_p=10, alpha=5, delta_val=4, save=None):
    data  = compare_matrices(t=t, r_p=r_p, alpha=alpha, delta_val=delta_val)
    stats = compute_stats(t=t, r_p=r_p, alpha=alpha, delta_val=delta_val)

    fig = plt.figure(figsize=(14, 9))
    fig.suptitle(
        f"Poseidon1 Partial Round Analysis  |  t={t}, α={alpha}, r_p={r_p}, Δ val={delta_val}",
        fontsize=14, fontweight="bold",
    )

    # --- subplot 1: diffusion curves ---
    ax1 = fig.add_subplot(2, 2, 1)
    for name, trace in data.items():
        rounds = [x[0] for x in trace]
        diff   = [x[1] for x in trace]
        ax1.plot(rounds, diff, marker="o", linewidth=2,
                 color=COLORS.get(name), label=LABELS.get(name, name))
    ax1.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax1.set_title("Diffusion D(r) per round")
    ax1.set_xlabel("Round"); ax1.set_ylabel("D(r)")
    ax1.set_ylim(-0.05, 1.15)
    ax1.legend(fontsize=8); ax1.grid(True, alpha=0.3)

    # --- subplot 2: branch numbers ---
    ax2 = fig.add_subplot(2, 2, 2)
    names = list(MATRIX_NAMES.keys())
    bns   = [branch_number(MATRIX_NAMES[n]) for n in names]
    ax2.bar([n for n in names], bns, color=[COLORS.get(n) for n in names],
            edgecolor="black", linewidth=0.8)
    ax2.axhline(t + 1, color="steelblue", linestyle="--", linewidth=2,
                label=f"MDS threshold = {t+1}")
    ax2.set_title("Branch Numbers")
    ax2.set_ylabel("B(M)"); ax2.set_ylim(0, max(bns) + 2)
    ax2.legend(fontsize=8); ax2.grid(axis="y", alpha=0.3)
    for i, (n, bn) in enumerate(zip(names, bns)):
        ax2.text(i, bn + 0.1, str(bn), ha="center", fontweight="bold")

    # --- subplot 3: final diffusion bar ---
    ax3 = fig.add_subplot(2, 2, 3)
    final_d = [stats[n]["final_diffusion"] for n in names]
    ax3.bar(names, final_d, color=[COLORS.get(n) for n in names],
            edgecolor="black", linewidth=0.8)
    ax3.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax3.set_title(f"Final diffusion after {r_p} partial rounds")
    ax3.set_ylabel("D(r_p)"); ax3.set_ylim(0, 1.2)
    ax3.grid(axis="y", alpha=0.3)
    for i, (n, d) in enumerate(zip(names, final_d)):
        ax3.text(i, d + 0.02, f"{d:.2f}", ha="center", fontweight="bold")

    # --- subplot 4: vulnerability legend ---
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis("off")
    rows = []
    for n in names:
        s = stats[n]
        rows.append([
            n,
            str(s["branch_number"]),
            "MDS" if s["is_mds"] else "non-MDS",
            "Never" if s["rounds_to_full_diffusion"] is None else str(s["rounds_to_full_diffusion"]),
            "VULN" if s["vulnerable"] else "OK",
        ])
    colors_table = []
    for n in names:
        vuln = stats[n]["vulnerable"]
        colors_table.append(
            [COLORS.get(n, 'white'), "white", "#fadbd8" if not stats[n]["is_mds"] else "#d5f5e3",
             "#fadbd8" if stats[n]["rounds_to_full_diffusion"] is None else "#d5f5e3",
             "#fadbd8" if vuln else "#d5f5e3"]
        )
    tbl = ax4.table(
        cellText=rows,
        colLabels=["Matrix", "B(M)", "MDS?", "Full diff@", "Status"],
        cellColours=colors_table,
        cellLoc="center", loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.2, 1.6)
    ax4.set_title("Summary")

    fig.tight_layout()
    if save:
        fig.savefig(save, dpi=150)
        print(f"Saved: {save}")
    else:
        plt.show()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Poseidon1 analysis plots")
    parser.add_argument("--mode", choices=["diffusion", "branch", "stats", "all", "degree"],
                        default="all", help="Which plot to show")
    parser.add_argument("--t", type=int, default=3, help="State width")
    parser.add_argument("--r_p", type=int, default=10, help="Number of partial rounds")
    parser.add_argument("--alpha", type=int, default=5, help="S-box exponent")
    parser.add_argument("--delta", type=int, default=4, help="Initial difference value")
    parser.add_argument("--matrices", nargs="+", default=None,
                        help="List of matrix names to compare (default: all known)")
    parser.add_argument("--save", type=str, default=None,
                        help="Save figure to file instead of showing")
    args = parser.parse_args()

    matrices = args.matrices if args.matrices is not None else None
    kwargs = dict(t=args.t, r_p=args.r_p, alpha=args.alpha, delta_val=args.delta, save=args.save, matrices=matrices)

    if args.mode == "diffusion":
        plot_diffusion(**kwargs)
    elif args.mode == "degree":
        # degree plot uses "delta" only indirectly; keep args for parity
        plot_degree(t=args.t, r_p=args.r_p, alpha=args.alpha, matrices=matrices, save=args.save)
    elif args.mode == "branch":
        plot_branch_numbers(t=args.t, save=args.save)
    elif args.mode == "stats":
        plot_stats_overview(t=args.t, r_p=args.r_p, alpha=args.alpha, delta_val=args.delta, save=args.save)
    elif args.mode == "all":
        plot_all(t=args.t, r_p=args.r_p, alpha=args.alpha, delta_val=args.delta, save=args.save)


if __name__ == "__main__":
    main()
