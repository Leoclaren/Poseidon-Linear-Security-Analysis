"""
Step 1.2 of the S&P2027 plan (RESEARCH_PLAN.md Sec 9): exact symbolic
replication of Vitto 2026/1579's Lemma 1 ("finite-trail space") degree
freeze, as a sanity check before building the general Algorithm 2 scanner.

analysis/degree.py's deg-bar is a worst-case UPPER BOUND and was shown
(Step 1.1) to be too coarse to see any collapse (ratio always 1.0). This
module instead tracks the EXACT polynomial degree in a single symbolic
variable X, for a one-parameter input family state(X) = c + X*d, using
real polynomial arithmetic over F_p (poseidon.polynomial), not a bound.

Two checks:
  1. verify_lemma1_freeze: pick d in the finite-trail space K_r(M)
     (poseidon.linalg.finite_trail_space) and confirm the active
     coordinate's degree genuinely stays frozen for r partial rounds, then
     jumps at round r — the mechanism Vitto's attack exploits once a family
     is *inside* the trail.
  2. check_no_accidental_landing: run an ARBITRARY (non-adaptively chosen)
     direction through a few full rounds and confirm the degree grows as
     expected (alpha per round, no freeze) — i.e. landing inside a trail
     does not happen by accident for a generic/non-adaptive full-round
     matrix, which is exactly why the "bind constants to the matrix"
     countermeasure (RESEARCH_PLAN.md Sec 6.1-1) closes the attack: without
     deliberately engineering the matrix against known constants (Vitto's
     Sec 3), there is nothing here for an attacker to exploit.
"""

from poseidon.field import Fp
from poseidon.linalg import finite_trail_space
from poseidon.matrices import get_matrix_set
from poseidon.constants import round_constants
from poseidon.polynomial import poly_add, poly_mul, poly_pow, deg, trim


def _scalar_poly_mul(c, poly):
    field = type(poly[0])
    if int(c) == 0:
        return [field(0)]
    return trim([field(int(c) * int(x)) for x in poly])


def _linear_layer_symbolic(M, state_polys):
    t = len(M)
    field = type(state_polys[0][0])
    out = []
    for i in range(t):
        acc = [field(0)]
        for j in range(t):
            if int(M[i][j]) == 0:
                continue
            acc = poly_add(acc, _scalar_poly_mul(M[i][j], state_polys[j]))
        out.append(acc)
    return out


def _add_constants_symbolic(state_polys, consts):
    return [poly_add(state_polys[i], [consts[i]]) for i in range(len(state_polys))]


def run_partial_rounds_symbolic(M, state_polys, r_p, alpha, constants_flat):
    """
    Run r_p partial rounds on a symbolic state (list of t polynomials in X).
    Returns (final_state, entering_degrees) where entering_degrees[r] is the
    EXACT degree in X of coordinate 0 immediately BEFORE round r's S-box
    (deg <= 0 means X-independent, i.e. the S-box sees only a constant).
    """
    t = len(state_polys)
    state = list(state_polys)
    entering_degrees = []
    for r in range(r_p):
        entering_degrees.append(deg(state[0]))
        state = [poly_pow(state[0], alpha)] + list(state[1:])
        c = constants_flat[r * t:(r + 1) * t]
        state = _add_constants_symbolic(state, c)
        state = _linear_layer_symbolic(M, state)
    return state, entering_degrees


def run_full_rounds_symbolic(M, state_polys, r_f, alpha, constants_flat):
    """Same as run_partial_rounds_symbolic but the S-box hits every coordinate."""
    t = len(state_polys)
    state = list(state_polys)
    entering_degrees = []
    for r in range(r_f):
        entering_degrees.append(max(deg(p) for p in state))
        state = [poly_pow(p, alpha) for p in state]
        c = constants_flat[r * t:(r + 1) * t]
        state = _add_constants_symbolic(state, c)
        state = _linear_layer_symbolic(M, state)
    return state, entering_degrees


def verify_lemma1_freeze(t=3, alpha=5, matrix_name="mds", extra_rounds=2, field=Fp):
    """
    Pick the largest r such that K_r(M) != {0}, take a basis vector d, and
    run state(X) = c + X*d through r + extra_rounds partial rounds,
    recording the EXACT entering degree of coordinate 0 each round.

    Expected (Lemma 1): entering_degrees[0..r-1] == 0 (frozen — the S-box
    sees only a constant for the first r rounds), entering_degrees[r] > 0
    (the trail ends, X-dependence reaches the active coordinate).
    """
    M = get_matrix_set(t, field=field)[matrix_name]

    r_used, basis = 0, []
    for r in range(t - 1, 0, -1):
        b = finite_trail_space(M, r)
        if b:
            r_used, basis = r, b
            break

    if r_used == 0:
        return {"matrix": matrix_name, "max_finite_trail_dim": 0,
                "note": "No nonzero finite trail found for r in [1, t-1]."}

    d = basis[0]
    c = [field(i + 1) for i in range(t)]
    state0 = [[c[i], d[i]] for i in range(t)]  # poly = c[i] + d[i]*X

    r_test = r_used + extra_rounds
    consts = round_constants(t, 0, r_test, field=field)
    _, entering_degrees = run_partial_rounds_symbolic(M, state0, r_test, alpha, consts)

    frozen_rounds = sum(1 for deg_r in entering_degrees[:r_used] if deg_r <= 0)
    jump_confirmed = entering_degrees[r_used] > 0 if len(entering_degrees) > r_used else None

    return {
        "matrix": matrix_name,
        "t": t, "alpha": alpha,
        "finite_trail_dim_used": r_used,
        "entering_degrees": entering_degrees,
        "frozen_for_predicted_rounds": frozen_rounds == r_used,
        "jump_at_predicted_round": jump_confirmed,
    }


def check_no_accidental_landing(t=3, alpha=5, full_matrix_name="mds",
                                 partial_matrix_name="mds", r_f_prefix=2, field=Fp):
    """
    Run an ARBITRARY, non-adaptively-chosen direction d through r_f_prefix
    full rounds (using the standard, not adversarially-tuned, full-round
    matrix) and check whether the resulting state's active-coordinate
    degree matches the naive expectation alpha^round (no freeze) at every
    step — i.e. confirms full-round absorption does not happen for free
    against a non-adaptive matrix/constants pair.
    """
    M_full = get_matrix_set(t, field=field)[full_matrix_name]
    c = [field(i + 1) for i in range(t)]
    d = [field(0)] * (t - 1) + [field(1)]
    state0 = [[c[i], d[i]] for i in range(t)]

    consts = round_constants(t, r_f_prefix, 0, field=field)
    final_state, entering_degrees = run_full_rounds_symbolic(M_full, state0, r_f_prefix, alpha, consts)

    expected = [alpha ** r for r in range(r_f_prefix)]
    matches_naive_growth = entering_degrees == expected

    return {
        "full_matrix": full_matrix_name,
        "r_f_prefix": r_f_prefix,
        "entering_degrees": entering_degrees,
        "naive_expected": expected,
        "matches_naive_growth_no_freeze": matches_naive_growth,
        "final_degree": max(deg(p) for p in final_state),
    }
