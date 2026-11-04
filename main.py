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
  scan      : Algorithm 1 — deterministic invariant subspace scanner (poly factorization)
  degree    : track the algebraic degree upper bound (deg-bar) across partial rounds

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
from poseidon.matrices import MATRIX_NAMES, get_matrix_set, branch_number
from poseidon.constants import round_constants
from attacks.invariant_subspace import run_attack_demo, InvariantSubspaceAttack
from attacks.scenarios import list_scenarios, run_scenario, SCENARIOS
from attacks.security_proof import SecurityProver
from attacks.linear_collapse import LinearCollapseAttack
from attacks.differential import DifferentialDistinguisher
from attacks.zero_sum import ZeroSumDistinguisher
from analysis.diffusion import compare_matrices
from analysis.statistics import compute_stats
from analysis.degree import (
    compare_matrices_degree, activation_round,
    unactivated_degree_trace_full_schedule, expected_vs_actual_degree,
)
from analysis.subspace_scanner import analyze_matrix_family, check_power_irreducibility
from analysis.finite_trail_scanner import unified_criterion, finite_trail_profile, scan_full_round_matrix
from poseidon.field import make_field
from attacks.midpoint_reset import find_closing_amplitude, run_attack, check_bound_matrix_immune


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
        delta_val=args.delta, verbose=True, matrix=args.matrix,
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

    for name, M in get_matrix_set(args.t).items():
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
    base = [Fp(1), Fp(2), Fp(3)]

    print(f"\n  Coset sum over {args.coset_size} elements of V = {{(0,0,x)}}:")
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
# Subcommand: scan  (Algorithm 1 — AnalyzeSubspace)
# ---------------------------------------------------------------------------

def cmd_scan(args):
    _print_separator("═")
    print(f"INVARIANT SUBSPACE SCANNER (Algorithm 1)  —  t={args.t}, r_p={args.r_p}")
    _print_separator("═")
    print("  Minimal/characteristic polynomial decomposition of M_W + coset check")
    print("  against the round constants (deterministic, no random sampling).")
    if args.grs21:
        print(f"  --grs21: also running the GRS21 multi-power irreducibility fast path")
        print(f"  (chi_(M_W^i) irreducible for some i in 1..{4 * (args.t - 1)}).")
    print()

    check_powers = 4 * (args.t - 1) if args.grs21 else None
    results = analyze_matrix_family(args.t, r_p=args.r_p, check_powers=check_powers)
    for name, r in results.items():
        status = r["status"]
        print(f"  [{status:26s}] {name:12s} | invariant subspace dim = {r['dimension']}")
        if status == "VULNERABLE":
            print(f"               factor (low-degree first) = {r['factor']}")
            for v in r["basis"]:
                print(f"               basis vector = {v}")
        if status == "SECURE_NO_PROPER_SUBSPACE":
            first_true = next(i for i, ok in r["grs21_check"]["per_power"].items() if ok)
            print(f"               chi_(M_W^{first_true}) is irreducible -> no nontrivial "
                  f"invariant subspace of ANY dimension (GRS21)")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: finite_scan  (Algorithm 2 -- unified criterion, RESEARCH_PLAN.md Sec 4)
# ---------------------------------------------------------------------------

def cmd_finite_scan(args):
    _print_separator("═")
    print(f"FINITE TRAIL / FULL-ROUND SCANNER (Algorithm 2)  —  t={args.t}")
    _print_separator("═")
    print("  (b) finite-trail dimension profile of M_I (Vitto's unavoidable baseline)")
    print("  (c) invariant-subspace contiguous-zero-run scan of the full-round matrix")
    print("      (generalizes Merz & Rodriguez Garcia's tensor-structure finding)\n")

    matrices = get_matrix_set(args.t)
    M_full = matrices[args.full_matrix]
    flat_constants = round_constants(args.t, 0, args.r_p)
    rounds = [flat_constants[i * args.t:(i + 1) * args.t] for i in range(args.r_p)]

    full_report = scan_full_round_matrix(M_full, suspicious_run_threshold=args.run_threshold)
    print(f"  Full-round matrix '{args.full_matrix}': any_suspicious="
          f"{full_report['any_suspicious']}  (threshold={full_report['suspicious_run_threshold']}, "
          f"{full_report['num_invariant_subspaces_found']} invariant subspaces found)")
    for s in full_report["subspaces"]:
        flag = "SUSPICIOUS" if s["suspicious"] else "ok        "
        print(f"    [{flag}] dim={s['subspace_dimension']:2d}  "
              f"min_weight={s['min_basis_vector_weight']:3d}  "
              f"max_contiguous_zero_run={s['max_contiguous_zero_run']:3d}")
    print()

    for name, M_I in matrices.items():
        r = unified_criterion(M_I, M_full, rounds, check_powers=args.grs21_power,
                               suspicious_run_threshold=args.run_threshold)
        verdict = "PASS" if r["passed"] else "FAIL"
        print(f"  [{verdict}] {name:12s} | infinite_trail={r['infinite_trail_check']['status']:26s} | "
              f"finite_trail_profile={r['finite_trail_profile']['dimension_profile']} "
              f"(maximal_rank_growth={r['finite_trail_profile']['maximal_rank_growth']})")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: degree  (algebraic degree upper bound, deg-bar)
# ---------------------------------------------------------------------------

def cmd_degree(args):
    _print_separator("═")
    print(f"ALGEBRAIC DEGREE UPPER BOUND  —  t={args.t}, r_p={args.r_p}, alpha={args.alpha}")
    _print_separator("═")

    traces = compare_matrices_degree(args.t, r_p=args.r_p, alpha=args.alpha)
    matrix_set = get_matrix_set(args.t)

    header = f"{'Round':>7}  " + "  ".join(f"{n:>15}" for n in traces)
    print(header)
    _print_separator()
    for r in range(args.r_p + 1):
        row = f"{r:>7}  " + "  ".join(f"{traces[n][r]:>15}" for n in traces)
        print(row)

    print()
    for name, M in matrix_set.items():
        act1 = activation_round(M, args.t, args.r_p, args.alpha, coord=1)
        act_last = activation_round(M, args.t, args.r_p, args.alpha, coord=args.t - 1)
        s1 = "never (frozen)" if act1 is None else f"round {act1}"
        s_last = "never (frozen)" if act_last is None else f"round {act_last}"
        print(f"  {name:12s} | coordinate-1 activation: {s1:15s} | coordinate-{args.t-1} (last) activation: {s_last}")

    if args.full:
        _print_separator()
        print(f"\n  Full schedule (r_f={args.r_f} full + r_p={args.r_p} partial + full), "
              f"full-round matrix = mds:")
        full_matrix = matrix_set["mds"]
        for name, M in matrix_set.items():
            trace = unactivated_degree_trace_full_schedule(full_matrix, M, args.t, args.r_f, args.r_p, args.alpha)
            r = expected_vs_actual_degree(full_matrix, M, args.t, args.r_f, args.r_p, args.alpha)
            print(f"    {name:12s} | after full prefix (round {args.r_f//2}): {trace[args.r_f//2]:>10} | "
                  f"expected={r['expected']:.3e}  achieved={r['achieved_upper_bound']:.3e}  ratio={r['collapse_ratio']}")
        print("\n  Note: this is a worst-case upper bound (deg-bar) — it cannot by itself show")
        print("  Vitto 2026/1579's degree COLLAPSE (3^10 vs 3^28), which relies on real symbolic")
        print("  cancellation along a constructed constrained-input family, not a generic bound.")
        print("  It CAN and does show full-round degree saturation (round 4 above), confirming the")
        print("  full-round prefix already maximizes the naive bound before the partial rounds start.")

    _print_separator("═")


# ---------------------------------------------------------------------------
# Subcommand: midpoint_reset  (Jo 2026/1760 replication + Step 3.1 binding test)
# ---------------------------------------------------------------------------

def _is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def cmd_midpoint_reset(args):
    _print_separator("═")
    print("MIDPOINT RESET — Jo 2026/1760 replication + Step 3.1 binding test")
    _print_separator("═")
    t, alpha, r_f, r_p = args.t, 3, 4, args.r_p
    print(f"  toy field search from p={args.toy_prime}, t={t}, alpha=3, r_f=4, r_p={r_p}")
    print("  (scope note: this replication covers alpha=3, r_f=4 — one full-round")
    print("   block per side — and a small toy prime, not Jo's literal r_f=8/")
    print("   KoalaBear instance; see attacks/midpoint_reset.py's module docstring.)\n")

    # Whether the single-block-per-side construction admits a closing
    # amplitude depends on the specific round constants (a nontrivial
    # algebraic equation in one unknown, Sec 4's "admits a family of
    # parameter choices" -- not every instance in that family has a toy-
    # scale root). Scan forward from --toy_prime for one that does,
    # exactly the kind of search Jo's own Sec 4 describes doing for their
    # concrete KoalaBear instance.
    print("  [Part 1] Replicating the attack against UNPROTECTED (unbound) constants...")
    field = None
    a = None
    p = args.toy_prime
    tried = 0
    while tried < 50:
        if _is_prime(p) and (p - 1) % 3 != 0:
            tried += 1
            cand_field = make_field(p, "FpToyCLI")
            cand_constants = round_constants(t, r_f, r_p, field=cand_field)
            cand_a = find_closing_amplitude(cand_constants, t, r_f, r_p, passive_index=1, field=cand_field)
            if cand_a is not None:
                field, a, constants = cand_field, cand_a, cand_constants
                break
        p += 2
    if a is None:
        print(f"    no closing amplitude found after scanning {tried} toy primes from {args.toy_prime}")
        field = make_field(args.toy_prime, "FpToyCLI")
    else:
        print(f"    found at toy prime p={field.P} (scanned {tried} candidates)")
        result = run_attack(constants, t, alpha, r_f, r_p, field, passive_index=1,
                             search_a=False, fixed_a=a)
        print(f"    closing amplitude a*={a}  collision_found={result['collision_found']}")
        if result["collision_found"]:
            print(f"    x+={[int(v) for v in result['x_plus']]}")
            print(f"    x-={[int(v) for v in result['x_minus']]}")
            print(f"    H(x+)=H(x-)={[int(v) for v in result['H_x_plus']]}")

    print("\n  [Part 2] Does binding constants to the matrix (Step 3.1,")
    print("           poseidon.matrix_search.generate_bound_round_constants) close this gap?")
    print(f"           Scanning all {field.P - 1} nonzero amplitudes against an honestly")
    print("           NUMS-generated, already-bound (M, c) pair...")
    immune = check_bound_matrix_immune(t, alpha, r_f, r_p, field, passive_index=1,
                                        seed_label=args.seed_label)
    verdict = "IMMUNE" if immune["immune"] else "VULNERABLE"
    print(f"    [{verdict}] family={immune['M_family']}  consistent_a_found={immune['consistent_a_found']}")

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
    # NOTE: --r_f is deliberately NOT here. argparse's `parents=` reuses the
    # same Action OBJECT across every subparser built from it, so an earlier
    # bug (`p_zs.set_defaults(func=cmd_zerosum, r_f=0)` below) was silently
    # mutating --r_f's default to 0 for EVERY subcommand, not just zerosum
    # (verified: `sub.add_parser(..., parents=[shared])._actions` for --r_f
    # `is` the same object across all subparsers). Each subparser below adds
    # its own --r_f instead, so a per-command default can never leak.
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--t",     type=int, default=3,  help="State width (default 3)")
    shared.add_argument("--r_p",   type=int, default=57, help="Partial rounds (default 57)")
    shared.add_argument("--alpha", type=int, default=5,  help="S-box exponent (default 5)")
    shared.add_argument("--delta", type=int, default=4,  help="Difference value (default 4)")

    def _add_rf(subparser, default=8):
        subparser.add_argument("--r_f", type=int, default=default,
                                help=f"Full rounds (default {default})")

    sub = parser.add_subparsers(dest="command", required=True)

    # permute
    p_perm = sub.add_parser("permute", parents=[shared], help="Run Poseidon1 permutation")
    _add_rf(p_perm)
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
    _add_rf(p_atk)
    p_atk.add_argument("--matrix", choices=list(MATRIX_NAMES), default=None,
                       help="Restrict the demo to a single matrix (default: compare all four)")
    p_atk.add_argument("--verbose", action="store_true",
                       help="Print per-round subspace membership")
    p_atk.set_defaults(func=cmd_attack)

    # diffusion
    p_diff = sub.add_parser("diffusion", parents=[shared], help="Print diffusion table")
    _add_rf(p_diff)
    p_diff.set_defaults(func=cmd_diffusion)

    # stats
    p_stat = sub.add_parser("stats", parents=[shared], help="Print security statistics")
    _add_rf(p_stat)
    p_stat.set_defaults(func=cmd_stats)

    # branch
    p_br = sub.add_parser("branch", parents=[shared], help="Print branch numbers")
    _add_rf(p_br)
    p_br.set_defaults(func=cmd_branch)

    # scenario
    p_sc = sub.add_parser("scenario", parents=[shared],
                           help="Run a predefined attack scenario")
    _add_rf(p_sc)
    p_sc.add_argument("--name", type=str, default=None,
                      help="Scenario name to run")
    p_sc.add_argument("--list", action="store_true",
                      help="List all available scenarios")
    p_sc.set_defaults(func=cmd_scenario)

    # prove
    p_pv = sub.add_parser("prove", parents=[shared],
                           help="Formally prove or disprove security of a matrix")
    _add_rf(p_pv)
    p_pv.add_argument("--matrix", choices=list(MATRIX_NAMES), default="mds",
                      help="Matrix to analyze")
    p_pv.add_argument("--scan",  action="store_true",
                      help="Also run exhaustive difference scan (weight ≤ 2)")
    p_pv.add_argument("--trace", action="store_true",
                      help="Print per-round counterexample trace")
    p_pv.set_defaults(func=cmd_prove)

    # collapse
    p_cl = sub.add_parser("collapse", parents=[shared],
                           help="Show partial rounds collapse to M^R_p on invariant subspace")
    _add_rf(p_cl)
    p_cl.add_argument("--matrix",  choices=list(MATRIX_NAMES), default="identity",
                      help="Matrix for partial rounds")
    p_cl.add_argument("--samples", type=int, default=5,
                      help="Number of random input pairs to verify")
    p_cl.add_argument("--track",   action="store_true",
                      help="Track M^r coord-0 behavior for each r")
    p_cl.set_defaults(func=cmd_collapse)

    # differential
    p_df = sub.add_parser("differential", parents=[shared],
                           help="Measure output difference bias (non-MDS = 100% predictable)")
    _add_rf(p_df)
    p_df.add_argument("--matrix",  choices=list(MATRIX_NAMES), default="identity",
                      help="Matrix for partial rounds")
    p_df.add_argument("--samples", type=int, default=20,
                      help="Number of random input pairs")
    p_df.add_argument("--table",   action="store_true",
                      help="Print full differential probability table")
    p_df.set_defaults(func=cmd_differential)

    # zerosum
    p_zs = sub.add_parser("zerosum", parents=[shared],
                           help="Run zero-sum distinguisher over coset of invariant subspace")
    _add_rf(p_zs, default=0)  # default partial-only, to isolate the invariant-subspace effect
    p_zs.add_argument("--matrix",     choices=list(MATRIX_NAMES), default="identity",
                      help="Matrix for partial rounds")
    p_zs.add_argument("--coset-size", type=int, default=6, dest="coset_size",
                      help="Number of coset elements to sum")
    p_zs.add_argument("--trials",     type=int, default=3,
                      help="Number of random-base trials (0 to skip)")
    p_zs.set_defaults(func=cmd_zerosum)

    # scan (Algorithm 1)
    p_scan = sub.add_parser("scan", parents=[shared],
                             help="Run the Algorithm 1 invariant-subspace scanner "
                                  "(minimal polynomial decomposition + coset check)")
    _add_rf(p_scan)
    p_scan.add_argument("--grs21", action="store_true",
                        help="Also run the cheap GRS21 multi-power irreducibility fast path")
    p_scan.set_defaults(func=cmd_scan)

    # finite_scan (Algorithm 2)
    p_fscan = sub.add_parser("finite_scan", parents=[shared],
                              help="Run the Algorithm 2 unified criterion "
                                   "(finite-trail profile + full-round invariant-subspace scan)")
    p_fscan.add_argument("--full-matrix", choices=list(MATRIX_NAMES), default="mds", dest="full_matrix",
                         help="Matrix to use for full rounds (default mds)")
    p_fscan.add_argument("--run-threshold", type=int, default=None, dest="run_threshold",
                         help="Suspicious contiguous-zero-run length (default t//4)")
    p_fscan.add_argument("--grs21-power", type=int, default=None, dest="grs21_power",
                         help="Max power for the GRS21 fast path in Algorithm 1 (default: skip it)")
    p_fscan.set_defaults(func=cmd_finite_scan)

    # degree
    p_deg = sub.add_parser("degree", parents=[shared],
                            help="Track the algebraic degree upper bound (deg-bar) per round")
    _add_rf(p_deg)
    p_deg.add_argument("--full", action="store_true",
                       help="Also track the degree-bar through the full-round prefix/suffix "
                            "(Step 1.1 of RESEARCH_PLAN.md), not just the partial rounds")
    p_deg.set_defaults(func=cmd_degree)

    # midpoint_reset (Jo 2026/1760 replication + Step 3.1 binding test)
    p_mr = sub.add_parser("midpoint_reset",
                           help="Replicate Jo 2026/1760's full-round collision and test "
                                "whether Step 3.1's constant-binding closes it")
    p_mr.add_argument("--t", type=int, default=6, help="State width (default 6; needs L+2<=t)")
    p_mr.add_argument("--r_p", type=int, default=4, help="Partial rounds (default 4)")
    p_mr.add_argument("--toy_prime", type=int, default=10007,
                       help="Small toy prime field (default 10007; must have gcd(3,p-1)=1)")
    p_mr.add_argument("--seed_label", type=str, default="poseidon-sp2027-v1-midpoint-reset-test",
                       help="NUMS seed label for Part 2's bound matrix")
    p_mr.set_defaults(func=cmd_midpoint_reset)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
