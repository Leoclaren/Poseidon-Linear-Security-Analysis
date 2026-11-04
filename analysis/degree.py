"""
Algebraic degree upper-bound tracking for Poseidon1 partial rounds
(Section III-D / Figure 3 of the paper: the deg-bar metric).

deg[i] over-approximates the algebraic degree (as a polynomial in the
permutation's input) of state coordinate i after each partial round:
  - the S-box multiplies coordinate 0's degree by alpha;
  - the linear layer's sparsity pattern determines which coordinates can
    inherit that boosted degree (output coordinate i depends on input
    coordinate j's degree only if M[i][j] != 0).

Because this ignores possible algebraic cancellations, it is a cheap
UPPER BOUND on the true degree (deg-bar), not the exact degree — exactly
the quantity the paper plots in Figure 3.
"""

from poseidon.matrices import get_matrix_set


def track_degree_full_schedule(M_full, M_partial, t, r_f, r_p, alpha, initial_degree=None):
    """
    Per-coordinate degree upper bound across the FULL permutation schedule
    (Step 1.1 of the S&P2027 plan, RESEARCH_PLAN.md §9): r_f//2 full rounds,
    then r_p partial rounds, then r_f//2 full rounds — mirroring exactly the
    round schedule in poseidon.permutation.PoseidonPermutation.permute().

    Unlike track_degree (partial-round-only), a full round's S-box multiplies
    EVERY coordinate's degree by alpha (not just coordinate 0), using
    M_full for the linear layer instead of M_partial. This is what Vitto
    2026/1579's "full-round absorption" claim needs to be checked against:
    does an unactivated coordinate's degree stay frozen (or grow slower than
    alpha^round) through the full-round prefix, not just the partial rounds?

    Returns a list of length (r_f + r_p + 1) of length-t degree-bound lists,
    one entry per round boundary (index 0 = before round 0).
    """
    deg = list(initial_degree) if initial_degree is not None else [1] * t
    history = [list(deg)]
    half_f = r_f // 2
    total = r_f + r_p

    for r in range(total):
        is_full = r < half_f or r >= half_f + r_p
        if is_full:
            sbox_deg = [d * alpha for d in deg]
            M = M_full
        else:
            sbox_deg = [deg[0] * alpha] + deg[1:]
            M = M_partial
        new_deg = []
        for i in range(t):
            contributions = [sbox_deg[j] for j in range(t) if int(M[i][j]) != 0]
            new_deg.append(max(contributions) if contributions else 0)
        deg = new_deg
        history.append(list(deg))

    return history


def unactivated_degree_trace_full_schedule(M_full, M_partial, t, r_f, r_p, alpha):
    """
    Max degree-bound over coordinates {1,...,t-1} per round across the full
    schedule (full-round prefix + partial rounds + full-round suffix) — the
    full-schedule analogue of unactivated_degree_trace, used to check
    whether the full-round prefix itself "absorbs" an unactivated coordinate
    into growth before the partial rounds even start.
    """
    history = track_degree_full_schedule(M_full, M_partial, t, r_f, r_p, alpha)
    return [max(degs[1:]) for degs in history]


def expected_vs_actual_degree(M_full, M_partial, t, r_f, r_p, alpha):
    """
    Compare the naive expected total degree alpha^(r_f+r_p) (every round
    assumed to engage every coordinate) against our degree-bar upper bound
    on the output's coordinate-0 degree after the full schedule — the
    comparison Vitto 2026/1579 reports as 3^28 (expected) vs 3^10 (achieved)
    for his KoalaBear instance.
    """
    history = track_degree_full_schedule(M_full, M_partial, t, r_f, r_p, alpha)
    expected = alpha ** (r_f + r_p)
    achieved = max(history[-1])
    return {
        "expected": expected,
        "achieved_upper_bound": achieved,
        "collapse_ratio": None if achieved == 0 else expected / achieved,
    }


def track_degree(M, t, r_p, alpha, initial_degree=None):
    """
    Per-coordinate degree upper bound after r = 0, 1, ..., r_p partial
    rounds. Returns a list of length r_p + 1 of length-t lists.
    """
    deg = list(initial_degree) if initial_degree is not None else [1] * t
    history = [list(deg)]

    for _ in range(r_p):
        sbox_deg = [deg[0] * alpha] + deg[1:]
        new_deg = []
        for i in range(t):
            contributions = [sbox_deg[j] for j in range(t) if int(M[i][j]) != 0]
            new_deg.append(max(contributions) if contributions else 0)
        deg = new_deg
        history.append(list(deg))

    return history


def max_degree_trace(M, t, r_p, alpha):
    """Max over ALL coordinates (including coord 0 itself) of the degree
    upper bound, per round. Coordinate 0 self-feeds the S-box every round
    for every matrix in the standard family, so this trace is dominated by
    coordinate 0 and is identical across matrices — use
    `unactivated_degree_trace` to see the Figure-3 phenomenon instead."""
    return [max(degs) for degs in track_degree(M, t, r_p, alpha)]


def unactivated_degree_trace(M, t, r_p, alpha):
    """
    Max over the UNACTIVATED coordinates {1, ..., t-1} of the degree upper
    bound, per round — this is the quantity plotted in Figure 3: it stays
    frozen at 1 forever under the identity matrix, grows immediately under
    a dense MDS matrix, and shows a systematic one-or-more-round delay
    under the Poseidon2-style sparse matrix.
    """
    history = track_degree(M, t, r_p, alpha)
    return [max(degs[1:]) for degs in history]


def activation_round(M, t, r_p, alpha, coord=0):
    """
    First round at which `coord`'s degree upper bound exceeds its initial
    value — i.e. the S-box cascade has reached that coordinate. Returns
    None if it never does within r_p rounds (frozen / persistent subspace).
    """
    history = track_degree(M, t, r_p, alpha)
    base = history[0][coord]
    for r, degs in enumerate(history):
        if degs[coord] > base:
            return r
    return None


def compare_matrices_degree(t, r_p=10, alpha=5, matrix_names=None):
    """Unactivated-coordinate degree-bar trace for every matrix in the
    standard family at width t (the quantity plotted in Figure 3)."""
    matrices = get_matrix_set(t)
    if matrix_names is None:
        matrix_names = list(matrices)
    return {
        name: unactivated_degree_trace(matrices[name], t, r_p, alpha)
        for name in matrix_names
    }
