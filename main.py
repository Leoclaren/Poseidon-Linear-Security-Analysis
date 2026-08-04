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
  scenario  : run a named predefined attack scenario (use --list to see all)
  prove     : formally prove or disprove security of a matrix
  collapse  : show R_p partial rounds collapse to M^R_p on invariant subspace
  differential : measure output difference bias (non-MDS = 100% predictable)
  zerosum   : run zero-sum distinguisher over a coset of the invariant subspace

Examples
--------
  python main.py permute --input 1 2 3 --matrix mds
  python main.py permute --input 1 2 3 --matrix identity --partial-only
  python main.py attack --r_p 6 --delta 4
  python main.py diffusion --r_p 10
  python main.py stats
  python main.py branch
  python main.py scenario --list
  python main.py scenario --name classic_invariant
  python main.py scenario --name prove_all
  python main.py prove --matrix identity
  python main.py prove --matrix mds
  python main.py collapse --matrix identity --r_p 6
  python main.py differential --matrix identity --r_p 6 --delta 4
  python main.py zerosum --matrix identity --r_p 6
"""

import argparse
import sys
from poseidon.field import Fp
from poseidon.permutation import PoseidonPermutation
from poseidon.matrices import get_matrix, branch_number
from attacks.invariant_subspace import run_attack_demo, InvariantSubspaceAttack
from attacks.scenarios import list_scenarios, run_scenario, SCENARIOS
from attacks.security_proof import SecurityProver
from attacks.linear_collapse import LinearCollapseAttack
from attacks.differential import DifferentialDistinguisher
from attacks.zero_sum import ZeroSumDistinguisher
from analysis.diffusion import compare_matrices
from analysis.statistics import compute_stats

MATRIX_CHOICES = ["mds", "identity", "circulant", "poseidon2"]


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

    for name in MATRIX_CHOICES:
        M = get_matrix(name, args.t)
        bn = branch_number(M)
        is_mds = bn >= args.t + 1
        marker = "[MDS]    " if is_mds else "[non-MDS]"
        print(f"  {marker} {name:12s} : B(M) = {bn}")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: scenario
# ---------------------------------------------------------------------------

def cmd_scenario(args):
    if args.list:
        by_cat = list_scenarios()
        _print_separator("═")
        print("PREDEFINED ATTACK SCENARIOS")
        _print_separator("═")
        for cat, scenarios in by_cat.items():
            print(f"\n  [{cat.upper()}]")
            for s in scenarios:
                print(f"    {s['name']:30s}  {s['description']}")
        _print_separator("═")
        return

    if not args.name:
        print("Error: provide --name <scenario> or --list")
        sys.exit(1)

    _print_separator("═")
    meta = SCENARIOS.get(args.name)
    if not meta:
        print(f"Unknown scenario '{args.name}'. Run with --list to see all.")
        sys.exit(1)
    print(f"SCENARIO: {args.name}")
    print(f"  {meta['description']}")
    _print_separator("═")
    run_scenario(args.name, verbose=True)
    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: prove
# ---------------------------------------------------------------------------

def cmd_prove(args):
    _print_separator("═")
    print(f"FORMAL SECURITY PROOF  —  matrix: {args.matrix}")
    _print_separator("═")

    prover = SecurityProver(t=args.t, matrix=args.matrix)
    result = prover.prove_or_disprove()

    print(f"\n  VERDICT: {result['verdict']}\n")
    for step in result["proof_steps"]:
        print(f"  {step}")

    if result.get("counterexample"):
        ce = result["counterexample"]
        _print_separator()
        print(f"  Counterexample  Δ_in = {ce['delta_in']}")
        print(f"  Invariant subspace coordinates: {ce['invariant_subspace_coords']}")
        print(f"  coord-0 ever nonzero across 6 rounds: {ce['coord0_ever_nonzero']}")
        if args.trace:
            print("\n  Round trace:")
            for entry in ce["trace"]:
                print(f"    round {entry['round']:2d}  diff={entry['diff']}  coord0={entry['coord0']}")

    if args.scan:
        _print_separator()
        print("\n  Exhaustive difference scan (weight ≤ 2):")
        scan = prover.exhaustive_difference_scan(max_weight=2)
        print(f"  Checked: {scan['total_checked']} | Dangerous: {scan['dangerous_count']} | "
              f"Safe: {scan['safe_count']} | Verdict: {scan['verdict']}")
        if scan["dangerous"]:
            print("  Dangerous diffs (M·Δ has coord-0 = 0):")
            for d in scan["dangerous"][:5]:
                print(f"    Δ={d['delta']}  M·Δ={d['image']}")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: collapse
# ---------------------------------------------------------------------------

def cmd_collapse(args):
    _print_separator("═")
    print(f"LINEAR COLLAPSE ATTACK  —  matrix: {args.matrix}  r_p={args.r_p}")
    _print_separator("═")

    atk = LinearCollapseAttack(t=args.t, r_p=args.r_p, alpha=args.alpha, matrix=args.matrix)

    print(f"\n  Effective map M^{args.r_p} (row 0):")
    print(f"    {atk.show_effective_map()[0]}")
    print(f"\n  Verifying {args.samples} random input pairs...")
    result = atk.verify_collapse(delta_val=args.delta, n_samples=args.samples)
    print(f"  Predicted diff: {result['predicted_diff']}")
    print(f"  All samples match linear prediction: {result['all_correct']}")

    for s in result["samples"]:
        match = "OK" if s["correct"] else "MISMATCH"
        print(f"    [{match}] input={[x for x in s['input'][:2]]}... "
              f"actual={s['actual_diff'][:2]}... predicted={s['predicted_diff'][:2]}...")

    if args.track:
        _print_separator()
        print(f"\n  M^r coord-0 behavior for r=1..{args.r_p}:")
        track = atk.track_map_power(max_r=args.r_p)
        for r, v in track.items():
            status = "coord-0=0 (S-box dormant)" if v["coord0_zero"] else "coord-0≠0 (S-box engaged)"
            print(f"    r={r:2d}  {status}  image(e_last)={v['image_of_e_last']}")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: differential
# ---------------------------------------------------------------------------

def cmd_differential(args):
    _print_separator("═")
    print(f"DIFFERENTIAL DISTINGUISHER  —  matrix: {args.matrix}  r_p={args.r_p}")
    _print_separator("═")

    d = DifferentialDistinguisher(t=args.t, r_p=args.r_p, alpha=args.alpha, matrix=args.matrix)

    print(f"\n  Measuring bias over {args.samples} random input pairs (δ={args.delta})...")
    bias = d.measure_bias(delta_val=args.delta, n_samples=args.samples)
    print(f"  Unique output diffs: {bias['unique_output_diffs']} / {bias['n_samples']}")
    print(f"  Fully predictable  : {bias['fully_predictable']}")
    print(f"  Predicted diff     : {list(bias['predicted_diff'])[:3]}")
    print(f"  Sample diffs (first 3):")
    for i, diff in enumerate(bias["sample_diffs"][:3]):
        print(f"    [{i}] {diff}")

    if args.table:
        _print_separator()
        print(f"\n  Differential probability table:")
        tbl = d.differential_probability_table()
        header = f"  {'Δ_in':25s} {'unique_out':>10} {'det?':>6} {'coord0_in_Δ':>12}"
        print(header)
        _print_separator()
        for row in tbl["table"]:
            print(f"  {str(row['delta_in']):25s} {row['unique_out_diffs']:>10} "
                  f"{'YES' if row['is_deterministic'] else 'no':>6} "
                  f"{'YES' if row['coord0_in_delta'] else 'no':>12}")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: zerosum
# ---------------------------------------------------------------------------

def cmd_zerosum(args):
    _print_separator("═")
    print(f"ZERO-SUM DISTINGUISHER  —  matrix: {args.matrix}  r_p={args.r_p}")
    _print_separator("═")

    z = ZeroSumDistinguisher(
        t=args.t, r_p=args.r_p, alpha=args.alpha, matrix=args.matrix, r_f=args.r_f
    )

    base = [Fp(i + 1) for i in range(args.t)]
    print(f"\n  Coset sum over {args.coset_size} elements of V:")
    result = z.check_coset_sum(base=base, coset_size=args.coset_size)
    print(f"  All coord-0 outputs equal : {result['all_coord0_equal']}")
    print(f"  coord-0 values            : {result['coord0_values']}")

    if args.trials > 0:
        _print_separator()
        print(f"\n  Running {args.trials} random-base trials...")
        r = z.run_distinguisher(n_trials=args.trials)
        print(f"  All trials trivially distinguishable: {r['all_trials_trivially_distinguishable']}")
        for t_ in r["trials"]:
            print(f"    trial {t_['trial']}: unique coord-0 values = {t_['unique_coord0_values']}")

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

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--t",     type=int, default=3,  help="State width (default 3)")
    shared.add_argument("--r_f",   type=int, default=8,  help="Full rounds (default 8)")
    shared.add_argument("--r_p",   type=int, default=57, help="Partial rounds (default 57)")
    shared.add_argument("--alpha", type=int, default=5,  help="S-box exponent (default 5)")
    shared.add_argument("--delta", type=int, default=4,  help="Difference value (default 4)")

    sub = parser.add_subparsers(dest="command", required=True)

    # permute
    p_perm = sub.add_parser("permute", parents=[shared], help="Run Poseidon1 permutation")
    p_perm.add_argument("--input", nargs="+", type=int, default=[1, 2, 3],
                        help="Input state (space-separated integers)")
    p_perm.add_argument("--matrix", choices=MATRIX_CHOICES, default="mds",
                        help="Matrix for partial rounds")
    p_perm.add_argument("--partial-only", action="store_true",
                        help="Only run partial rounds (no full rounds)")
    p_perm.add_argument("--trace", action="store_true",
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

    # scenario
    p_sc = sub.add_parser("scenario", parents=[shared],
                          help="Run a predefined attack scenario")
    p_sc.add_argument("--name", type=str, default=None, help="Scenario name to run")
    p_sc.add_argument("--list", action="store_true", help="List all available scenarios")
    p_sc.set_defaults(func=cmd_scenario)

    # prove
    p_pv = sub.add_parser("prove", parents=[shared],
                          help="Formally prove or disprove security of a matrix")
    p_pv.add_argument("--matrix", choices=MATRIX_CHOICES, default="mds",
                      help="Matrix to analyze")
    p_pv.add_argument("--scan", action="store_true",
                      help="Also run exhaustive difference scan (weight ≤ 2)")
    p_pv.add_argument("--trace", action="store_true",
                      help="Print per-round counterexample trace")
    p_pv.set_defaults(func=cmd_prove)

    # collapse
    p_cl = sub.add_parser("collapse", parents=[shared],
                          help="Show partial rounds collapse to M^R_p on invariant subspace")
    p_cl.add_argument("--matrix", choices=MATRIX_CHOICES, default="identity",
                      help="Matrix for partial rounds")
    p_cl.add_argument("--samples", type=int, default=5,
                      help="Number of random input pairs to verify")
    p_cl.add_argument("--track", action="store_true",
                      help="Track M^r coord-0 behavior for each r")
    p_cl.set_defaults(func=cmd_collapse)

    # differential
    p_df = sub.add_parser("differential", parents=[shared],
                          help="Measure output difference bias (non-MDS = 100% predictable)")
    p_df.add_argument("--matrix", choices=MATRIX_CHOICES, default="identity",
                      help="Matrix for partial rounds")
    p_df.add_argument("--samples", type=int, default=20,
                      help="Number of random input pairs")
    p_df.add_argument("--table", action="store_true",
                      help="Print full differential probability table")
    p_df.set_defaults(func=cmd_differential)

    # zerosum
    p_zs = sub.add_parser("zerosum", parents=[shared],
                          help="Run zero-sum distinguisher over coset of invariant subspace")
    p_zs.add_argument("--matrix", choices=MATRIX_CHOICES, default="identity",
                      help="Matrix for partial rounds")
    p_zs.add_argument("--coset-size", type=int, default=6, dest="coset_size",
                      help="Number of coset elements to sum")
    p_zs.add_argument("--trials", type=int, default=3,
                      help="Number of random-base trials (0 to skip)")
    p_zs.set_defaults(func=cmd_zerosum, r_f=0)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()