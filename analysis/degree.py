"""
Algebraic-degree tracking for Poseidon1 partial rounds.

This module tracks an upper bound on the algebraic degree per coordinate
through partial rounds. It implements a conservative (standard) degree
propagation model:

  - S-box (coord 0): degree[0] <- degree[0] * alpha
  - Add constants: no effect
  - Linear layer M: degree'[i] = max_{j : M[i][j] != 0} degree[j]

The module exposes
  - track_algebraic_degree(matrix_name, t, r_p, alpha)
  - compare_matrices_degree(...)

Note: degrees tracked are symbolic upper-bounds (fast). Exact polynomial
expansion over F_p is possible but expensive; this is sufficient for
comparative experiments across matrices and t.
"""

from poseidon.permutation import PoseidonPermutation
from poseidon.matrices import get_matrix, MATRIX_NAMES


def track_algebraic_degree(matrix_name: str, t: int = 3, r_p: int = 10, alpha: int = 5,
                           initial_support=None):
    """
    Track algebraic-degree upper bounds for partial rounds,
    respecting possible invariant subspaces.

    initial_support: list/tuple of length t indicating which coordinates
                     start with non-zero difference (default: last coordinate only,
                     matching the Δ = (0,...,0,δ) used in the paper).
    """
    from poseidon.matrices import get_matrix

    M = get_matrix(matrix_name, t)

    # Default: difference only on the last coordinate (as in the paper experiments)
    if initial_support is None:
        initial_support = [0] * (t - 1) + [1]

    # degree[i] = current upper bound on algebraic degree of coordinate i
    deg = [1 if s else 0 for s in initial_support]
    history = [(0, list(deg), max(deg) if any(deg) else 0)]

    for r in range(1, r_p + 1):
        # S-box only increases degree if coord 0 currently has non-zero degree
        # (i.e., the differential can be non-zero there)
        if deg[0] > 0:
            deg[0] = deg[0] * alpha

        # Linear layer: new_deg[i] = max of deg[j] over support of row i
        new_deg = []
        for i in range(t):
            maxdeg = 0
            for j in range(t):
                if int(M[i][j]) != 0 and deg[j] > maxdeg:
                    maxdeg = deg[j]
            new_deg.append(maxdeg)

        deg = new_deg
        history.append((r, list(deg), max(deg) if any(deg) else 0))

    return history


def compare_matrices_degree(matrix_names=None, t=3, r_p=10, alpha=5):
    if matrix_names is None:
        matrix_names = list(MATRIX_NAMES.keys())
    out = {}
    for name in matrix_names:
        out[name] = track_algebraic_degree(name, t=t, r_p=r_p, alpha=alpha)
    return out
