"""
Algorithm 1 (AnalyzeSubspace) from the paper: a deterministic invariant
subspace trail detector based on minimal/characteristic polynomial
decomposition of the restricted linear layer M_W, plus a coset check
against the round constants — as opposed to the brute-force axis-aligned
coordinate search in attacks/security_proof.py or randomized sampling.

Pipeline, matching the pseudocode of Algorithm 1:
  1. M_W <- M restricted to coordinates {1, ..., t-1}  (the unactivated
     hyperspace W; the S-box only ever touches coordinate 0).
  2. Factorize det(K*I - M_W)  (via its squarefree radical, so repeated
     roots such as the identity matrix's (K-1)^(t-1) are still handled).
  3. For each irreducible factor f_i, take V_i = ker(f_i(M_W)).
  4. Keep V_i only if the FULL matrix M maps it into itself (it never
     leaks into coordinate 0).
  5. Keep it only if every round constant, restricted to {1, ..., t-1},
     stays inside the corresponding coset of V_i.
  6. If both hold, an infinite invariant subspace trail exists -> VULNERABLE.
     Otherwise -> SECURE (no infinite trail; this does NOT rule out the
     finite activation delays measured separately by analysis/diffusion.py
     and analysis/degree.py).
"""

from poseidon.field import Fp
from poseidon.matrices import get_matrix_set, matrix_mul
from poseidon.constants import round_constants
from poseidon.linalg import characteristic_polynomial, poly_eval_matrix, nullspace, in_span, mat_mul, identity
from poseidon.polynomial import squarefree_radical, factor_squarefree, make_monic, deg


def _restrict_to_W(M):
    """M_W: M restricted to coordinates 1..t-1 (drop row 0 and column 0)."""
    return [row[1:] for row in M[1:]]


def _lift(vector_w):
    """Prepend a 0 for coordinate 0 to a vector living in the W-subspace."""
    field = type(vector_w[0])
    return [field(0)] + list(vector_w)


def is_irreducible(poly):
    """
    True iff `poly` (as a single polynomial, not just its squarefree
    radical) is irreducible over F_p: no repeated roots/factors (its
    radical has the same degree as itself) AND the radical factors into
    exactly one piece of that same degree.
    """
    poly = make_monic(poly)
    d = deg(poly)
    if d <= 0:
        return False
    radical = squarefree_radical(poly)
    if deg(radical) != d:
        return False  # poly = (something)^k, k>1 -- not irreducible as a whole
    factors = factor_squarefree(radical)
    return len(factors) == 1 and deg(factors[0]) == d


def check_power_irreducibility(M, max_power=None):
    """
    GRS21 sufficient criterion (Grassi, Rechberger, Schofnegger, ToSC
    2021(2) -- the same "sufficient minimal-polynomial branch" Vitto
    2026/1579 Sec 6.1 runs through powers 1..4t): check whether
    chi_{M_W^i} is irreducible of full degree (t-1) for i=1..max_power.

    If TRUE for even a single power i, M_W has NO nontrivial proper
    invariant subspace at all under M_W (not just none axis-aligned,
    unlike the brute-force search in attacks/security_proof.py) -- any
    such subspace would also be invariant under M_W^i, and an invariant
    subspace of a linear map whose characteristic polynomial is
    irreducible would give a nontrivial factor of an irreducible
    polynomial, a contradiction. This does NOT by itself rule out finite
    subspace trails reachable via full-round absorption (RESEARCH_PLAN.md
    Sec 3 row 3) -- it only rules out infinite/axis-aligned-style trails,
    same scope as Algorithm 1.

    Default max_power = 2*(t-1), GRS21's own range; pass 4*(t-1) to match
    the stronger check Vitto's concrete matrices pass (Eq. 37).
    """
    M_W = _restrict_to_W(M)
    n = len(M_W)
    if n == 0:
        return {"irreducible_for_any_power": False, "per_power": {}}
    if max_power is None:
        max_power = 2 * n

    per_power = {}
    Mi = identity(n, field=type(M_W[0][0]))
    for i in range(1, max_power + 1):
        Mi = mat_mul(M_W, Mi)
        per_power[i] = is_irreducible(characteristic_polynomial(Mi))

    return {
        "irreducible_for_any_power": any(per_power.values()),
        "per_power": per_power,
    }


def analyze_subspace(M, round_constants_list=None, check_powers=None):
    """
    Run Algorithm 1 on a single partial-round matrix M.

    Parameters
    ----------
    M : t x t matrix (list of lists of Fp)
    round_constants_list : optional list of per-round constant vectors
        (each of length t); if omitted, step 5 (the coset check) is skipped.
    check_powers : optional max_power for check_power_irreducibility; if
        given, run the cheap GRS21 multi-power check FIRST and short-circuit
        to a distinct SECURE_NO_PROPER_SUBSPACE verdict (stronger than plain
        SECURE: proven no nontrivial invariant subspace of ANY dimension
        exists, not just none found by the factor loop below) before
        falling through to the general factor-decomposition search.

    Returns
    -------
    dict with keys: status ("VULNERABLE" | "SECURE" |
    "SECURE_NO_PROPER_SUBSPACE"), factor (the irreducible polynomial that
    produced the trail, or None), basis (the invariant subspace basis,
    lifted to the full t-dim space), dimension.
    """
    if check_powers is not None:
        power_check = check_power_irreducibility(M, max_power=check_powers)
        if power_check["irreducible_for_any_power"]:
            return {
                "status": "SECURE_NO_PROPER_SUBSPACE",
                "factor": None, "basis": [], "dimension": 0,
                "grs21_check": power_check,
            }

    M_W = _restrict_to_W(M)
    charpoly = characteristic_polynomial(M_W)
    radical = squarefree_radical(charpoly)
    irreducible_factors = factor_squarefree(radical)

    for f_i in irreducible_factors:
        F_i = poly_eval_matrix(f_i, M_W)
        kernel_basis_w = nullspace(F_i)
        if not kernel_basis_w:
            continue

        lifted_basis = [_lift(v) for v in kernel_basis_w]

        images = [matrix_mul(M, v) for v in lifted_basis]
        full_matrix_invariant = all(in_span(lifted_basis, img) for img in images)
        if not full_matrix_invariant:
            continue

        if round_constants_list is not None:
            coset_ok = all(
                in_span(kernel_basis_w, list(c[1:])) for c in round_constants_list
            )
            if not coset_ok:
                continue

        return {
            "status": "VULNERABLE",
            "factor": [int(c) for c in f_i],
            "basis": [[int(x) for x in v] for v in lifted_basis],
            "dimension": len(lifted_basis),
        }

    return {"status": "SECURE", "factor": None, "basis": [], "dimension": 0}


def analyze_matrix_family(t, r_p=10, matrix_names=None, check_powers=None):
    """Run Algorithm 1 over the standard matrix family for a given width t."""
    matrices = get_matrix_set(t)
    if matrix_names is None:
        matrix_names = list(matrices)

    flat_constants = round_constants(t, 0, r_p)
    rounds = [flat_constants[i * t:(i + 1) * t] for i in range(r_p)]

    return {
        name: analyze_subspace(matrices[name], rounds, check_powers=check_powers)
        for name in matrix_names
    }
