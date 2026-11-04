"""
Phase 2 (RESEARCH_PLAN.md Step 3): lightweight matrix generation + scoring.

Candidate matrices are generated via a nothing-up-my-sleeve procedure that
BINDS the round constants to the matrix (RESEARCH_PLAN.md Sec 6.1-1,
Vitto 2026/1579 Sec 6.3's own proposed countermeasure): constants are
derived as a hash of a transcript that includes the matrix itself, so the
"choose a matrix adaptively against already-fixed constants" premise both
the Vitto full-round-absorption attack and the 2026/1901 kleptographic-
backdoor class need is impossible by construction -- not merely checked
after the fact.

Each candidate is scored against:
  - branch number / MDS status (poseidon.matrices)
  - Algorithm 1 + GRS21 fast path (analysis.subspace_scanner)
  - Algorithm 2's unified criterion (analysis.finite_trail_scanner)
  - degree-bar through the full schedule (analysis.degree, Step 1.1)
  - a REAL arithmetization cost split into R1CS constraints (S-box-
    dominated: linear layers are free in R1CS, multiplying a wire by a
    public constant is not a multiplication gate) and native/Plonkish
    multiplicative complexity (NOT free, included separately -- see
    cost_r1cs / mul_complexity below; RESEARCH_PLAN.md Sec 6's single
    "cost()" formula conflated the two, corrected here).
"""

import hashlib

from poseidon.field import Fp, P
from poseidon.linalg import rank
from analysis.subspace_scanner import check_power_irreducibility


# ---------------------------------------------------------------------------
# Nothing-up-my-sleeve generation (Step 3.1)
# ---------------------------------------------------------------------------

def _hash_to_field(seed: bytes, label: bytes, index: int, field=Fp):
    """Domain-separated hash-to-field (SHAKE256), generalizing the single-
    purpose generator in poseidon/constants.py with an explicit label."""
    digest = hashlib.shake_256(seed + b"|" + label + b"|" + index.to_bytes(8, "big")).digest(40)
    return field(int.from_bytes(digest[:32], "big") % field.P)


def encode_matrix(M) -> bytes:
    """Canonical fixed-width byte encoding of a matrix, for binding round
    constants to it (Vitto 2026/1579 Sec 6.3)."""
    return b"".join(int(x).to_bytes(32, "big") for row in M for x in row)


def generate_bound_round_constants(M_I, M_full, t, r_f, r_p, alpha, p=None, seed_label="poseidon-sp2027-v1", field=Fp):
    """
    T = seed_label || enc(p,t,alpha,r_f,r_p) || enc(M_I) || enc(M_full)
    c_i^(r) = HashToField(T || enc(r,i))

    Applies Vitto's own proposed fix for attack class #3 (RESEARCH_PLAN.md
    Sec 3 row 3, Sec 6.1-1) by construction: the constants cannot be fixed
    independently of EITHER matrix.

    Step 4 (adversarial falsification) found that an earlier version of
    this function only bound M_I, leaving M_full free -- a real gap, since
    Vitto's actual attack constructs the FULL-ROUND matrix adversarially
    against already-fixed constants (full-round absorption INTO M_I's
    trail), not the partial-round matrix. Binding only M_I left exactly
    that door open if M_full were ever allowed to vary (e.g. a standards
    process, like the one Vitto targets, that lets a submitter choose
    their own external/full-round matrix). Both matrices are now bound.
    """
    p = p if p is not None else field.P
    header = f"{seed_label}|p={p}|t={t}|alpha={alpha}|r_f={r_f}|r_p={r_p}".encode()
    transcript = header + b"|M_I|" + encode_matrix(M_I) + b"|M_full|" + encode_matrix(M_full)
    total_rounds = r_f + r_p
    return [_hash_to_field(transcript, b"const", r * t + i, field)
            for r in range(total_rounds) for i in range(t)]


# ---------------------------------------------------------------------------
# Candidate matrix families (Step 3.3)
# ---------------------------------------------------------------------------

def poseidon2_sparse_candidate(t, seed_label="poseidon-sp2027-v1-M_I-poseidon2", max_tries=64, field=Fp):
    """
    NUMS Poseidon2-style internal matrix: M[i][j] = 1 for i != j,
    M[i][i] = mu_i (hash-derived), re-drawing mu_i on successive hash
    indices if the result is singular or has a degenerate diagonal entry.
    O(t) nonzero-off-1 entries -- the cheapest family by mul_complexity.
    """
    seed = seed_label.encode()
    for attempt in range(max_tries):
        mus = [_hash_to_field(seed, b"mu", attempt * t + i, field) for i in range(t)]
        if any(int(m) in (0, 1) for m in mus):
            continue
        M = [[field(1) if i != j else mus[i] for j in range(t)] for i in range(t)]
        if rank(M) == t:
            return M, {"family": "poseidon2_sparse", "seed_label": seed_label, "attempt": attempt}
    raise RuntimeError("poseidon2_sparse_candidate: no invertible candidate in max_tries")


def low_weight_circulant_candidate(t, weight=2, seed_label="poseidon-sp2027-v1-M_I-circulant", max_tries=64, field=Fp):
    """NUMS low-weight circulant: `weight` hash-derived nonzero entries
    (hash-derived positions, including position 0) in the first row, the
    rest zero; every row a cyclic rotation of the first."""
    seed = seed_label.encode()
    weight = max(1, min(weight, t))
    for attempt in range(max_tries):
        positions = sorted({int(_hash_to_field(seed, b"pos", attempt * t + k, field)) % t for k in range(weight)})
        if 0 not in positions:
            positions = [0] + positions[:max(0, weight - 1)]
        first_row = [field(0)] * t
        for k, pos in enumerate(positions):
            v = _hash_to_field(seed, b"val", attempt * t + k, field)
            first_row[pos] = v if int(v) != 0 else field(1)
        M = [[first_row[(j - i) % t] for j in range(t)] for i in range(t)]
        if rank(M) == t:
            return M, {"family": "low_weight_circulant", "seed_label": seed_label,
                       "attempt": attempt, "weight": weight}
    raise RuntimeError("low_weight_circulant_candidate: no invertible candidate in max_tries")


def irreducible_filtered_candidate(t, seed_label="poseidon-sp2027-v1-M_I-irreducible",
                                    max_tries=256, check_power=None, field=Fp):
    """
    NUMS dense candidate, rejection-sampled until chi(M_W^i) is
    irreducible for some i (GRS21's criterion, Step 2.1) -- the cheapest
    of Objective 1's mitigations: zero extra rounds, just a selection
    filter on which M_I is accepted.
    """
    seed = seed_label.encode()
    check_power = check_power or 2 * (t - 1)
    for attempt in range(max_tries):
        M = [[_hash_to_field(seed, b"entry", attempt * t * t + i * t + j, field) for j in range(t)]
             for i in range(t)]
        if rank(M) != t:
            continue
        if check_power_irreducibility(M, max_power=check_power)["irreducible_for_any_power"]:
            return M, {"family": "irreducible_filtered", "seed_label": seed_label, "attempt": attempt}
    raise RuntimeError("irreducible_filtered_candidate: no irreducible candidate in max_tries")


def nums_full_round_matrix(t, seed_label="poseidon-sp2027-v1-M_full", max_tries=256, field=Fp):
    """
    NUMS dense full-round matrix, rejection-sampled for MDS (branch number
    >= t+1). Added in Step 4 (adversarial falsification) after finding
    that score_candidate previously reused a single FIXED 'mds' matrix for
    every candidate, which was then never bound into the constants
    transcript at all -- this generator makes M_full itself seed-derived
    per run, so generate_bound_round_constants's binding of M_full is
    actually binding something that varies, not a constant.
    """
    from poseidon.matrices import branch_number
    seed = seed_label.encode()
    for attempt in range(max_tries):
        M = [[_hash_to_field(seed, b"entry", attempt * t * t + i * t + j, field) for j in range(t)]
             for i in range(t)]
        if rank(M) != t:
            continue
        if branch_number(M) >= t + 1:
            return M, {"family": "nums_full_round", "seed_label": seed_label, "attempt": attempt}
    raise RuntimeError("nums_full_round_matrix: no MDS candidate in max_tries")


# ---------------------------------------------------------------------------
# Cost model (Step 3.2)
# ---------------------------------------------------------------------------

def constraints_per_sbox(alpha):
    """R1CS multiplication constraints for x^alpha via square-and-multiply:
    (bit_length(alpha)-1) squarings + (popcount(alpha)-1) extra
    multiplications. alpha=5 -> 3 (x2=x*x, x4=x2*x2, x5=x4*x, matching
    standard Poseidon circuits); alpha=3 -> 2."""
    if alpha < 2:
        return 0
    return (alpha.bit_length() - 1) + (bin(alpha).count("1") - 1)


def mul_complexity(M):
    """Native/Plonkish multiplicative complexity of ONE application of M:
    count of entries that are not 0 or 1 (multiplying by 0 or 1 is free
    even outside R1CS). NOT the R1CS constraint count -- see cost_r1cs."""
    return sum(1 for row in M for x in row if int(x) not in (0, 1))


def cost_r1cs(t, r_f, r_p, alpha):
    """Non-linear (true multiplication-gate) R1CS constraints: S-box-
    dominated, since multiplying a wire by a public constant is a free
    linear combination, not a multiplication gate. Verified in Step 5.1/5.2
    against a real `circom --r1cs` compile of the Step 3.5 winner at
    t=3, alpha=5, r_f=8, r_p=57: predicted 243, circom reported
    "non-linear constraints: 243" exactly."""
    per_sbox = constraints_per_sbox(alpha)
    return r_f * t * per_sbox + r_p * per_sbox


def cost_r1cs_linear(t, r_f, r_p):
    """
    "Linear constraints" circom still allocates one R1CS row for: one per
    S-box INPUT combination (full round: t per round, partial: 1) plus one
    per state OUTPUT combination (every round produces t outputs,
    regardless of how many of the matrix's entries are nonzero).

    Found in Step 5.1/5.2: compiling the Step 3.5 winner's circuit with
    circom gave "linear constraints: 276" -- this formula reproduces that
    exactly (2*r_f*t + r_p*(1+t) = 2*8*3 + 57*4 = 276) -- AND, compiling
    the same (t, r_f, r_p, alpha) with the densest candidate
    (`irreducible_filtered`) instead of the sparsest (`poseidon2_sparse`)
    gave the IDENTICAL 243/276/523-wires result. This is the real,
    surprising finding of Phase 4: in a naive R1CS encoding, EVERY matrix
    entry that's nonzero folds into the SAME single linear-combination row
    regardless of how many terms it has -- sparsity (poseidon2_sparse vs.
    a dense candidate) has ZERO effect on R1CS/circom constraint count.
    The mul_complexity() optimization from Step 3 is real, but it's a
    native-evaluation / Plonkish-custom-gate-width win, NOT an R1CS one --
    the two backends charge for completely different things.
    """
    return 2 * r_f * t + r_p * (1 + t)


def cost_report(M_I, M_full, t, r_f, r_p, alpha):
    """
    Step 4 found that an earlier version used mul_complexity(M_I) for
    EVERY round, including full rounds -- which actually apply M_full
    (typically dense, often costlier), not M_I. Full and partial rounds
    are now costed against their own matrix.
    """
    r1cs_nonlinear = cost_r1cs(t, r_f, r_p, alpha)
    r1cs_linear = cost_r1cs_linear(t, r_f, r_p)
    return {
        "r1cs_constraints": r1cs_nonlinear,  # non-linear only, kept for backward compat (Step 3.4/3.5)
        "r1cs_linear_constraints": r1cs_linear,
        "r1cs_total_rows": r1cs_nonlinear + r1cs_linear,
        "mul_complexity_per_full_round": mul_complexity(M_full),
        "mul_complexity_per_partial_round": mul_complexity(M_I),
        "mul_complexity_total": r_f * mul_complexity(M_full) + r_p * mul_complexity(M_I),
    }


# ---------------------------------------------------------------------------
# Scoring (Step 3.4) and search orchestration (Step 3.5)
# ---------------------------------------------------------------------------

def score_candidate(M_I, t, alpha, r_f, r_p, M_full=None, full_matrix_meta=None, family_meta=None,
                     grs21_power=None, run_threshold=None, field=Fp):
    from poseidon.matrices import branch_number
    from analysis.finite_trail_scanner import unified_criterion
    from analysis.degree import unactivated_degree_trace_full_schedule

    family_meta = family_meta or {}
    if M_full is None:
        M_full, full_matrix_meta = nums_full_round_matrix(
            t, seed_label=f"{family_meta.get('seed_label', 'poseidon-sp2027-v1')}-M_full", field=field)

    all_constants = generate_bound_round_constants(
        M_I, M_full, t, r_f, r_p, alpha, seed_label=family_meta.get("seed_label", "poseidon-sp2027-v1"), field=field)
    half_f = r_f // 2
    partial_flat = all_constants[half_f * t: (half_f + r_p) * t]
    partial_rounds = [partial_flat[i * t:(i + 1) * t] for i in range(r_p)]

    uc = unified_criterion(M_I, M_full, partial_rounds, check_powers=grs21_power,
                            suspicious_run_threshold=run_threshold)
    bn = branch_number(M_I)
    deg_trace = unactivated_degree_trace_full_schedule(M_full, M_I, t, r_f, r_p, alpha)
    costs = cost_report(M_I, M_full, t, r_f, r_p, alpha)

    return {
        "family_meta": family_meta,
        "full_matrix_meta": full_matrix_meta,
        "branch_number": bn,
        "is_mds": bn >= t + 1,
        "unified_criterion": uc,
        "passed_security": uc["passed"],
        "unactivated_degree_at_full_prefix_end": deg_trace[r_f // 2],
        "unactivated_degree_final": deg_trace[-1],
        "cost": costs,
    }


def search_and_score(t=3, alpha=5, r_f=8, r_p=57, grs21_power=None, run_threshold=None, field=Fp):
    """Enumerate the three Step-3.3 families and score each (Step 3.4),
    ranked security-first then cheapest (Step 3.5's shortlist input)."""
    candidates = [
        poseidon2_sparse_candidate(t, field=field),
        low_weight_circulant_candidate(t, field=field),
        irreducible_filtered_candidate(t, field=field),
    ]
    results = [
        score_candidate(M, t, alpha, r_f, r_p, family_meta=meta,
                         grs21_power=grs21_power, run_threshold=run_threshold, field=field)
        for M, meta in candidates
    ]
    # Step 4 found that r1cs_constraints ties across every candidate (it
    # never depends on the matrix, see cost_r1cs's docstring) -- sorting
    # on it alone left the ranking depending on candidate insertion order
    # by accident. mul_complexity_total is the metric that actually
    # differs and should break the tie.
    results.sort(key=lambda r: (not r["passed_security"], r["cost"]["r1cs_constraints"],
                                 r["cost"]["mul_complexity_total"]))
    return results
