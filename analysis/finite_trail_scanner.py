"""
Algorithm 2 (RESEARCH_PLAN.md Step 2.2, Sec 4's unified criterion): a
general scanner for the two structural weaknesses Algorithm 1
(analysis/subspace_scanner.py) does NOT cover, sibling module to it.

Where Algorithm 1 only looks at the partial-round matrix M_I restricted to
the unactivated coordinates (M_W) and only finds INFINITE invariant
subspace trails, Algorithm 2 adds:

  (b) The finite-trail dimension profile of M_I (Vitto 2026/1579's
      K_r(M) -- finite_trail_space in poseidon/linalg.py): informational,
      since every linear layer unavoidably has one; what matters is
      whether it is reachable, which is a joint matrix+constants question
      left to Phase 2/3's adversarial search, not re-derived here (see
      RESEARCH_PLAN.md Step 1.2's scope note).

  (c) Large/structured eigenspaces of the FULL-ROUND matrix M_full --
      generalizes Merz & Rodriguez Garcia 2026/306's finding (their
      P_(t/4) kron M_4 has an unconstrained (t/4-1)*4-dimensional
      eigenspace at eigenvalue 1) WITHOUT assuming a tensor/Kronecker
      structure: find every eigenvalue of M_full that lies in F_p, and
      flag any eigenspace whose dimension meets or exceeds t/4 -- the
      exact threshold the paper's own countermeasure targets (their fix
      works precisely when c>=t/4 or d>=t/4).

A candidate (M_I, M_full, round_constants) "passes" Sec 4's unified
criterion only if Algorithm 1 is SECURE (or the stronger
SECURE_NO_PROPER_SUBSPACE) AND no suspicious full-round eigenspace exists.
"""

from poseidon.field import Fp
from poseidon.linalg import finite_trail_space, characteristic_polynomial, nullspace, poly_eval_matrix
from poseidon.polynomial import squarefree_radical, factor_squarefree, deg
from analysis.subspace_scanner import analyze_subspace


def finite_trail_profile(M_I, max_r=None):
    """
    dim K_r(M_I) for r = 0..max_r (default t-1), plus whether it matches
    "maximal partial-round rank growth" (dim K_r(M_I) == t-r exactly,
    Vitto Eq. 4) -- informational baseline, not itself a vulnerability.
    """
    t = len(M_I)
    if max_r is None:
        max_r = t - 1
    profile = {r: len(finite_trail_space(M_I, r)) for r in range(max_r + 1)}
    maximal_rank_growth = all(profile[r] == max(t - r, 0) for r in profile)
    return {"dimension_profile": profile, "maximal_rank_growth": maximal_rank_growth}


def invariant_subspaces(M_full):
    """
    Every M_full-invariant subspace found via the SAME primary-decomposition
    technique Algorithm 1 uses on M_W (ker(f_i(M)) for each irreducible
    factor f_i of the characteristic polynomial), applied here to the FULL
    matrix directly.

    Earlier version of this function only searched single-eigenvalue
    eigenspaces (roots of the characteristic polynomial in F_p). That is
    NOT general enough: for M_eps = P (x) M_4, (P (x) M_4)(v (x) w) =
    (Pv) (x) (M_4 w) -- for v an eigenvector of P (eigenvalue 1), this
    stays inside the 12-dimensional subspace {v' (x) w : v' in
    Eigenspace_P(1), w in F^4} for EVERY w (an invariant subspace), but
    v (x) w is only a single-eigenvalue EIGENVECTOR when w is also an
    eigenvector of M_4 -- a much smaller (dimension-3, confirmed by direct
    computation) subset. The eigenvalue-only search found dimension 3 and
    missed the actual dimension-12 exploitable structure entirely. Using
    the full irreducible-factor kernel (as below) catches it, because the
    12-dim subspace IS ker(f(M_eps)) for f = the minimal polynomial of
    M_full restricted to it, which the characteristic-polynomial
    factorization surfaces directly without needing to know the tensor
    structure in advance.
    """
    radical = squarefree_radical(characteristic_polynomial(M_full))
    subspaces = []
    for f_i in factor_squarefree(radical):
        basis = nullspace(poly_eval_matrix(f_i, M_full))
        if basis:
            subspaces.append({"factor_degree": deg(f_i), "dimension": len(basis), "basis": basis})
    return subspaces


def _max_contiguous_zero_run(vec):
    """Longest run of consecutive zero coordinates, wrapping around the end
    (CICO's zero-prefix constraint can sit anywhere once we also consider
    cyclic/sponge framing, so check all rotations, not just position 0)."""
    t = len(vec)
    doubled = [int(x) == 0 for x in vec] * 2
    best = run = 0
    for i, is_zero in enumerate(doubled):
        if i >= t and i - t >= best:
            break
        run = run + 1 if is_zero else 0
        best = max(best, run)
    return min(best, t)


def scan_full_round_matrix(M_full, suspicious_run_threshold=None):
    """
    Generalizes Merz & Rodriguez Garcia 2026/306's tensor-structure finding
    to an arbitrary full-round matrix, without assuming any Kronecker
    structure in advance: find every M_full-invariant subspace (via
    invariant_subspaces) and flag any whose basis contains a vector with a
    CONTIGUOUS run of zero coordinates at or above `suspicious_run_threshold`
    (default t//4, matching the CICO-c/d parameter the paper's own fix
    targets).

    IMPORTANT, found empirically while building this: raw eigenspace/weight
    alone is NOT enough to distinguish a vulnerable matrix from its fixed
    counterpart. M_eps = P_(t/4) kron M_4 and the countermeasure
    M_eps_bar = M_4 kron P_(t/4) are permutation-similar (the "perfect
    shuffle" permutation), so they have IDENTICAL eigenvalues, dimensions,
    and even identical weight distributions -- swapping the factor order
    does not remove any low-weight eigenvector, it only PERMUTES which
    coordinates are zero. Verified directly: M_eps has a weight-8
    eigenvector with zeros at contiguous positions [8..15]; M_eps_bar has a
    weight-8 eigenvector too, but with zeros scattered at [2,3,6,7,10,11,
    14,15] -- same count, no long contiguous run. The exploit specifically
    needs a CONTIGUOUS run (to match CICO's "first c coordinates" prefix
    constraint), which is exactly why the swap works -- so this scanner
    checks contiguous-run length, not just weight or dimension, or it
    cannot tell the two matrices apart (an earlier version of this function
    did exactly that and incorrectly reported both as safe).
    """
    # NOTE on the default threshold: t//4 is Merz & Rodriguez Garcia's own
    # CICO-c/d >= t/4 fix criterion, meaningful for Poseidon2(b)'s quadruple
    # ("t divisible by 4") design. At small/non-quadruple widths (e.g. the
    # t=3 Poseidon1-style matrices elsewhere in this repo) t//4 rounds down
    # to <=1, making the check flag almost any structural zero -- overly
    # conservative, not wrong, but callers targeting a specific CICO-k
    # should pass an explicit suspicious_run_threshold matching their own k.
    t = len(M_full)
    threshold = suspicious_run_threshold if suspicious_run_threshold is not None else max(1, t // 4)
    report = []
    for s in invariant_subspaces(M_full):
        weights = [sum(1 for x in v if int(x) != 0) for v in s["basis"]]
        runs = [_max_contiguous_zero_run(v) for v in s["basis"]]
        report.append({
            "factor_degree": s["factor_degree"],
            "subspace_dimension": s["dimension"],
            "min_basis_vector_weight": min(weights) if weights else 0,
            "max_contiguous_zero_run": max(runs) if runs else 0,
            "suspicious": bool(runs) and max(runs) >= threshold,
        })
    return {
        "t": t,
        "suspicious_run_threshold": threshold,
        "num_invariant_subspaces_found": len(report),
        "subspaces": report,
        "any_suspicious": any(r["suspicious"] for r in report),
    }


def unified_criterion(M_I, M_full, round_constants_list=None, check_powers=None,
                       suspicious_run_threshold=None):
    """
    RESEARCH_PLAN.md Sec 4's unified criterion as one combined report:
    passes only if Algorithm 1 finds no infinite invariant subspace in
    M_I, AND Algorithm 2 finds no suspicious (long contiguous zero run)
    invariant subspace in M_full. The finite-trail profile is included
    for the record but does not by itself fail a candidate (every matrix
    has one).
    """
    infinite_trail_check = analyze_subspace(M_I, round_constants_list, check_powers=check_powers)
    finite_profile = finite_trail_profile(M_I)
    full_round_check = scan_full_round_matrix(M_full, suspicious_run_threshold=suspicious_run_threshold)

    passed = (
        infinite_trail_check["status"] in ("SECURE", "SECURE_NO_PROPER_SUBSPACE")
        and not full_round_check["any_suspicious"]
    )
    return {
        "passed": passed,
        "infinite_trail_check": infinite_trail_check,
        "finite_trail_profile": finite_profile,
        "full_round_eigenspace_check": full_round_check,
    }
