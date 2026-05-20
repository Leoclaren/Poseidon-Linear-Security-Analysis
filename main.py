#!/usr/bin/env python3
"""
Poseidon1 CLI — implementation + attack demos + analysis.

Sections
--------
  permute   : run the Poseidon1 permutation on a given input
  attack    : run the invariant subspace trail attack demo
  diffusion : print diffusion table across matrices and rounds
  stats     : print security statistics summary
  branch    : print branch numbers for all matrices

Examples
--------
  python main.py permute --input 1 2 3 --matrix mds
  python main.py permute --input 1 2 3 --matrix identity --partial-only
  python main.py attack --r_p 6 --delta 4
  python main.py diffusion --r_p 10
  python main.py stats
  python main.py branch
"""

import argparse
import sys
from poseidon.field import Fp
from poseidon.permutation import PoseidonPermutation
from poseidon.matrices import MATRIX_NAMES, branch_number
from attacks.invariant_subspace import run_attack_demo, InvariantSubspaceAttack
from analysis.diffusion import compare_matrices
from analysis.statistics import compute_stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_state(label, state):
    print(f"  {label}:")
    for i, x in enumerate(state):
        print(f"    [{i}] = {int(x)}")


def _print_separator(char="─", width=60):
    print(char * width)


# ---------------------------------------------------------------------------
# Subcommand: permute
# ---------------------------------------------------------------------------

def cmd_permute(args):
    _print_separator("═")
    print("POSEIDON1 PERMUTATION")
    _print_separator("═")

    state_in = [Fp(x) for x in args.input]
    print(f"  Matrix       : {args.matrix}")
    print(f"  State width  : {args.t}")
    print(f"  Full rounds  : {args.r_f}")
    print(f"  Partial rds  : {args.r_p}")
    print(f"  Alpha        : {args.alpha}")
    print(f"  Partial only : {args.partial_only}")
    _print_separator()
    _print_state("Input", state_in)

    perm = PoseidonPermutation(
        t=args.t, r_f=args.r_f, r_p=args.r_p,
        alpha=args.alpha, matrix=args.matrix,
    )

    if args.partial_only:
        if args.trace:
            out, trace = perm.permute_partial_only(state_in, trace=True)
            _print_separator()
            print("  Round trace:")
            for r, s in enumerate(trace):
                print(f"    Round {r:3d}: {[int(x) for x in s]}")
        else:
            out = perm.permute_partial_only(state_in)
    else:
        if args.trace:
            out, trace = perm.permute(state_in, trace=True)
            _print_separator()
            print("  Round trace:")
            for r, s in enumerate(trace):
                label = "full" if (r < args.r_f // 2 or r >= args.r_f // 2 + args.r_p) else "partial"
                print(f"    Round {r:3d} [{label:7s}]: {[int(x) for x in s]}")
        else:
            out = perm.permute(state_in)

    _print_separator()
    _print_state("Output", out)
    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: attack
# ---------------------------------------------------------------------------

def cmd_attack(args):
    _print_separator("═")
    print("INVARIANT SUBSPACE TRAIL ATTACK")
    _print_separator("═")
    print(f"  t={args.t}, r_p={args.r_p}, alpha={args.alpha}, delta={args.delta}")
    print()

    results = run_attack_demo(
        t=args.t, r_p=args.r_p, alpha=args.alpha,
        delta_val=args.delta, verbose=True,
    )

    if args.verbose:
        for name, res in results.items():
            _print_separator()
            print(f"\nPer-round subspace membership [{name}]:")
            for entry in res["subspace"]["per_round"]:
                activated = "ACTIVATED" if entry["coord0_nonzero"] else "dormant  "
                print(f"  Round {entry['round']:3d}  coord0={activated}  diff={entry['diff_in']}")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: diffusion
# ---------------------------------------------------------------------------

def cmd_diffusion(args):
    _print_separator("═")
    print("DIFFUSION ANALYSIS")
    _print_separator("═")
    print(f"  t={args.t}, r_p={args.r_p}, alpha={args.alpha}, delta={args.delta}")
    print()

    data = compare_matrices(
        t=args.t, r_p=args.r_p, alpha=args.alpha,
        delta_coord=-1, delta_val=args.delta,
    )

    # Header
    names = list(data.keys())
    header = f"{'Round':>7}  " + "  ".join(f"{n:>15}" for n in names)
    print(header)
    _print_separator()

    rounds = data[names[0]]
    for r_idx in range(len(rounds)):
        r = rounds[r_idx][0]
        row = f"{r:>7}  "
        for n in names:
            d = data[n][r_idx][1]
            row += f"  {d:>15.4f}"
        print(row)

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: stats
# ---------------------------------------------------------------------------

def cmd_stats(args):
    _print_separator("═")
    print("SECURITY STATISTICS SUMMARY")
    _print_separator("═")
    print(f"  t={args.t}, r_p={args.r_p}, alpha={args.alpha}, delta={args.delta}")
    print()

    stats = compute_stats(t=args.t, r_p=args.r_p, alpha=args.alpha, delta_val=args.delta)

    for name, s in stats.items():
        status = "VULNERABLE" if s["vulnerable"] else "SECURE    "
        rtfd = s["rounds_to_full_diffusion"]
        print(f"  [{status}] {name:12s} | B(M)={s['branch_number']:2d} | MDS={str(s['is_mds']):5s} | "
              f"full_diff_round={'Never' if rtfd is None else str(rtfd):>5} | "
              f"final_D={s['final_diffusion']:.3f}")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: branch
# ---------------------------------------------------------------------------

def cmd_branch(args):
    _print_separator("═")
    print("BRANCH NUMBERS")
    _print_separator("═")
    print(f"  t={args.t}  |  MDS threshold = t+1 = {args.t + 1}")
    print()

    for name, M in MATRIX_NAMES.items():
        bn = branch_number(M)
        is_mds = bn >= args.t + 1
        marker = "[MDS]    " if is_mds else "[non-MDS]"
        print(f"  {marker} {name:12s} : B(M) = {bn}")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="poseidon",
        description="Poseidon1 implementation, attack demos, and analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Shared args
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--t",     type=int, default=3,  help="State width (default 3)")
    shared.add_argument("--r_f",   type=int, default=8,  help="Full rounds (default 8)")
    shared.add_argument("--r_p",   type=int, default=57, help="Partial rounds (default 57)")
    shared.add_argument("--alpha", type=int, default=5,  help="S-box exponent (default 5)")
    shared.add_argument("--delta", type=int, default=4,  help="Difference value (default 4)")

    sub = parser.add_subparsers(dest="command", required=True)

    # permute
    p_perm = sub.add_parser("permute", parents=[shared], help="Run Poseidon1 permutation")
    p_perm.add_argument("--input",        nargs="+", type=int, default=[1, 2, 3],
                        help="Input state (space-separated integers)")
    p_perm.add_argument("--matrix",       choices=list(MATRIX_NAMES), default="mds",
                        help="Matrix for partial rounds")
    p_perm.add_argument("--partial-only", action="store_true",
                        help="Only run partial rounds (no full rounds)")
    p_perm.add_argument("--trace",        action="store_true",
                        help="Print round-by-round trace")
    p_perm.set_defaults(func=cmd_permute)

    # attack
    p_atk = sub.add_parser("attack", parents=[shared], help="Run invariant subspace attack demo")
    p_atk.add_argument("--verbose", action="store_true",
                       help="Print per-round subspace membership")
    p_atk.set_defaults(func=cmd_attack)

    # diffusion
    p_diff = sub.add_parser("diffusion", parents=[shared], help="Print diffusion table")
    p_diff.set_defaults(func=cmd_diffusion)

    # stats
    p_stat = sub.add_parser("stats", parents=[shared], help="Print security statistics")
    p_stat.set_defaults(func=cmd_stats)

    # branch
    p_br = sub.add_parser("branch", parents=[shared], help="Print branch numbers")
    p_br.set_defaults(func=cmd_branch)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
