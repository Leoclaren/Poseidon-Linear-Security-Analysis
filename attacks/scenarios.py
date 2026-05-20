"""
Predefined attack scenarios for Poseidon1 partial rounds.

Each scenario targets a specific vulnerability or security property.
Run them by name via:  python main.py scenario --name <name>
List all:             python main.py scenario --list
"""

from poseidon.field import Fp
from poseidon.matrices import MATRIX_NAMES

# ---------------------------------------------------------------------------
# Scenario registry
# ---------------------------------------------------------------------------

SCENARIOS = {}

def scenario(name, description, category):
    """Decorator to register a scenario function."""
    def decorator(fn):
        SCENARIOS[name] = {
            "name": name,
            "description": description,
            "category": category,
            "fn": fn,
        }
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Category: Invariant Subspace
# ---------------------------------------------------------------------------

@scenario(
    "classic_invariant",
    "Classic (0,0,δ) invariant subspace trail — the core vulnerability of non-MDS partial rounds.",
    "invariant_subspace",
)
def classic_invariant(verbose=True):
    from attacks.invariant_subspace import InvariantSubspaceAttack
    results = {}
    for matrix in ["identity", "circulant", "mds"]:
        atk = InvariantSubspaceAttack(t=3, r_p=6, alpha=5, matrix=matrix)
        r = atk.check_invariant_subspace(delta_val=4)
        results[matrix] = r
        if verbose:
            status = "VULNERABLE" if r["invariant_subspace_holds"] else "RESISTANT"
            print(f"  [{status}] {matrix:12s} | B(M)={r['branch_number']} | "
                  f"coord-0 activations={r['coord0_activations']}/6 rounds")
    return results


@scenario(
    "large_delta",
    "Same invariant subspace attack but with δ=10^9 — shows vulnerability is field-magnitude independent.",
    "invariant_subspace",
)
def large_delta(verbose=True):
    from attacks.invariant_subspace import InvariantSubspaceAttack
    results = {}
    for matrix in ["identity", "circulant", "mds"]:
        atk = InvariantSubspaceAttack(t=3, r_p=6, alpha=5, matrix=matrix)
        r = atk.check_invariant_subspace(delta_val=10**9)
        results[matrix] = r
        if verbose:
            status = "VULNERABLE" if r["invariant_subspace_holds"] else "RESISTANT"
            print(f"  [{status}] {matrix:12s} | δ=10^9 | "
                  f"coord-0 activations={r['coord0_activations']}/6 rounds")
    return results


@scenario(
    "multi_delta",
    "Run invariant subspace for δ ∈ {1, 2, 4, 100, 10^6} — all produce the same vulnerability pattern.",
    "invariant_subspace",
)
def multi_delta(verbose=True):
    from attacks.invariant_subspace import InvariantSubspaceAttack
    deltas = [1, 2, 4, 100, 10**6]
    results = {}
    for delta in deltas:
        atk = InvariantSubspaceAttack(t=3, r_p=6, alpha=5, matrix="identity")
        r = atk.check_invariant_subspace(delta_val=delta)
        results[delta] = r
        if verbose:
            status = "INVARIANT HOLDS" if r["invariant_subspace_holds"] else "broken"
            print(f"  δ={delta:<10} | {status} | coord-0 activations={r['coord0_activations']}")
    return results


@scenario(
    "subspace_e1",
    "Attack using e_1 = (0,δ,0) — tests which coordinate subspaces are invariant.",
    "invariant_subspace",
)
def subspace_e1(verbose=True):
    from poseidon.matrices import matrix_mul
    results = {}
    for name, M in MATRIX_NAMES.items():
        # Try delta in coord 1 only
        delta = [Fp(0), Fp(7), Fp(0)]
        current = list(delta)
        coord0_hits = 0
        for _ in range(6):
            current = matrix_mul(M, current)
            if int(current[0]) != 0:
                coord0_hits += 1
        results[name] = coord0_hits
        if verbose:
            status = "coord-0 NEVER hit" if coord0_hits == 0 else f"coord-0 hit {coord0_hits}x"
            print(f"  {name:12s} | Δ=(0,7,0) | {status}")
    return results


# ---------------------------------------------------------------------------
# Category: Linear Collapse
# ---------------------------------------------------------------------------

@scenario(
    "linear_collapse",
    "Show that R_p partial rounds collapse to M^R_p on the invariant subspace — pure linear map.",
    "linear_collapse",
)
def linear_collapse(verbose=True):
    from attacks.linear_collapse import LinearCollapseAttack
    atk = LinearCollapseAttack(t=3, r_p=6, alpha=5, matrix="identity")
    r = atk.verify_collapse(delta_val=4, n_samples=5)
    if verbose:
        print(f"  Matrix: identity | r_p=6 | δ=4")
        print(f"  Effective map M^6 computed: {r['map_computed']}")
        print(f"  All {r['n_samples']} samples match linear prediction: {r['all_correct']}")
        for s in r["samples"]:
            print(f"    input={s['input'][:2]}... | match={s['correct']}")
    return r


@scenario(
    "collapse_vs_rounds",
    "Track how the effective linear map M^r evolves — identity collapses earlier than MDS.",
    "linear_collapse",
)
def collapse_vs_rounds(verbose=True):
    from attacks.linear_collapse import LinearCollapseAttack
    results = {}
    for matrix in ["identity", "circulant", "mds"]:
        atk = LinearCollapseAttack(t=3, r_p=10, alpha=5, matrix=matrix)
        r = atk.track_map_power(max_r=10)
        results[matrix] = r
        if verbose:
            print(f"  {matrix:12s} | coord-0 stays 0 for rounds: "
                  f"{[rr for rr, v in r.items() if v['coord0_zero']]}")
    return results


# ---------------------------------------------------------------------------
# Category: Differential
# ---------------------------------------------------------------------------

@scenario(
    "differential_bias",
    "Measure output difference bias: for non-MDS the output diff is 100% deterministic.",
    "differential",
)
def differential_bias(verbose=True):
    from attacks.differential import DifferentialDistinguisher
    results = {}
    for matrix in ["identity", "circulant", "mds"]:
        d = DifferentialDistinguisher(t=3, r_p=6, alpha=5, matrix=matrix)
        r = d.measure_bias(delta_val=4, n_samples=20)
        results[matrix] = r
        if verbose:
            print(f"  {matrix:12s} | unique output diffs: {r['unique_output_diffs']} / {r['n_samples']} "
                  f"| predictable={r['fully_predictable']}")
    return results


@scenario(
    "differential_chosen",
    "Chosen-difference attack: attacker picks Δ ∈ V and recovers output diff without oracle calls.",
    "differential",
)
def differential_chosen(verbose=True):
    from attacks.differential import DifferentialDistinguisher
    d = DifferentialDistinguisher(t=3, r_p=6, alpha=5, matrix="identity")
    r = d.chosen_difference_attack(delta_val=13, n_pairs=5)
    if verbose:
        print(f"  Matrix=identity | r_p=6 | δ=13")
        print(f"  Attack success rate: {r['success_rate']*100:.0f}%")
        for p in r["pairs"]:
            print(f"    pair #{p['idx']}: predicted={p['predicted'][:2]}... | "
                  f"correct={p['correct']}")
    return r


@scenario(
    "differential_mds_resistance",
    "Show MDS resists chosen-difference: output diffs are diverse, prediction fails.",
    "differential",
)
def differential_mds_resistance(verbose=True):
    from attacks.differential import DifferentialDistinguisher
    d_mds  = DifferentialDistinguisher(t=3, r_p=6, alpha=5, matrix="mds")
    d_none = DifferentialDistinguisher(t=3, r_p=6, alpha=5, matrix="identity")
    r_mds  = d_mds.measure_bias(delta_val=4, n_samples=20)
    r_none = d_none.measure_bias(delta_val=4, n_samples=20)
    if verbose:
        print(f"  MDS     | unique output diffs: {r_mds['unique_output_diffs']:>2} | "
              f"predictable={r_mds['fully_predictable']}")
        print(f"  identity| unique output diffs: {r_none['unique_output_diffs']:>2} | "
              f"predictable={r_none['fully_predictable']}")
        print(f"  => MDS produces diverse output diffs (secure); identity is deterministic (broken)")
    return {"mds": r_mds, "identity": r_none}


# ---------------------------------------------------------------------------
# Category: Zero-Sum
# ---------------------------------------------------------------------------

@scenario(
    "zero_sum",
    "Zero-sum distinguisher: sum of outputs over a coset of V is constant for non-MDS.",
    "zero_sum",
)
def zero_sum(verbose=True):
    from attacks.zero_sum import ZeroSumDistinguisher
    results = {}
    for matrix in ["identity", "circulant", "mds"]:
        z = ZeroSumDistinguisher(t=3, r_p=6, alpha=5, matrix=matrix)
        r = z.check_coset_sum(base=[Fp(1), Fp(2), Fp(3)], coset_size=5)
        results[matrix] = r
        if verbose:
            print(f"  {matrix:12s} | coset sum coord-0 zero={r['sum_coord0_zero']} "
                  f"| sum={r['sum_coord0'] % (10**6)} (mod 10^6)")
    return results


@scenario(
    "zero_sum_full_rounds",
    "Zero-sum over full permutation (with full rounds) — shows full rounds partially recover security.",
    "zero_sum",
)
def zero_sum_full_rounds(verbose=True):
    from attacks.zero_sum import ZeroSumDistinguisher
    results = {}
    for matrix in ["identity", "mds"]:
        z_partial = ZeroSumDistinguisher(t=3, r_p=6, alpha=5, matrix=matrix, r_f=0)
        z_full    = ZeroSumDistinguisher(t=3, r_p=6, alpha=5, matrix=matrix, r_f=4)
        rp = z_partial.check_coset_sum(base=[Fp(5), Fp(7), Fp(11)], coset_size=5)
        rf = z_full.check_coset_sum(base=[Fp(5), Fp(7), Fp(11)], coset_size=5)
        results[matrix] = {"partial_only": rp, "with_full_rounds": rf}
        if verbose:
            print(f"  {matrix:12s} | partial-only sum-zero={rp['sum_coord0_zero']} | "
                  f"with-full-rounds sum-zero={rf['sum_coord0_zero']}")
    return results


# ---------------------------------------------------------------------------
# Category: Security Proof
# ---------------------------------------------------------------------------

@scenario(
    "prove_mds",
    "Formally prove MDS is secure: find ALL potential invariant coordinate subspaces, show none exist.",
    "proof",
)
def prove_mds(verbose=True):
    from attacks.security_proof import SecurityProver
    p = SecurityProver(t=3, matrix="mds")
    r = p.prove_or_disprove()
    if verbose:
        _print_verdict(r)
    return r


@scenario(
    "disprove_identity",
    "Formally disprove identity matrix security: produce explicit invariant subspace + counterexample.",
    "proof",
)
def disprove_identity(verbose=True):
    from attacks.security_proof import SecurityProver
    p = SecurityProver(t=3, matrix="identity")
    r = p.prove_or_disprove()
    if verbose:
        _print_verdict(r)
    return r


@scenario(
    "disprove_circulant",
    "Formally disprove circulant matrix security: find invariant subspace and demonstrate attack.",
    "proof",
)
def disprove_circulant(verbose=True):
    from attacks.security_proof import SecurityProver
    p = SecurityProver(t=3, matrix="circulant")
    r = p.prove_or_disprove()
    if verbose:
        _print_verdict(r)
    return r


@scenario(
    "prove_all",
    "Run the security prover on ALL matrices and show a comparison verdict table.",
    "proof",
)
def prove_all(verbose=True):
    from attacks.security_proof import SecurityProver
    results = {}
    for name in MATRIX_NAMES:
        p = SecurityProver(t=3, matrix=name)
        r = p.prove_or_disprove()
        results[name] = r
        if verbose:
            verdict = r["verdict"]
            print(f"  {name:12s} | {verdict}")
    return results


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _print_verdict(r):
    print(f"  Matrix   : {r['matrix']}")
    print(f"  Verdict  : {r['verdict']}")
    for step in r["proof_steps"]:
        print(f"    {step}")
    if r.get("counterexample"):
        ce = r["counterexample"]
        print(f"  Counterexample:")
        print(f"    Δ_in  = {ce['delta_in']}")
        print(f"    Δ_out = {ce['delta_out']}")
        print(f"    coord-0 ever nonzero: {ce['coord0_ever_nonzero']}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_scenarios():
    """Return list of all registered scenarios grouped by category."""
    by_cat = {}
    for s in SCENARIOS.values():
        by_cat.setdefault(s["category"], []).append(s)
    return by_cat


def run_scenario(name: str, verbose: bool = True):
    """Run a scenario by name. Returns result dict."""
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{name}'. Use --list to see available scenarios.")
    return SCENARIOS[name]["fn"](verbose=verbose)
