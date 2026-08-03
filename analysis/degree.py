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


def track_algebraic_degree(matrix_name: str, t: int = 3, r_p: int = 10, alpha: int = 5):
    """Track algebraic-degree upper bounds for partial rounds.

    Returns a list of tuples: (round_index, degree_vector, max_degree)
    where round_index runs from 0 (initial) to r_p.
    """
    # Build a PoseidonPermutation to reuse matrix selection logic; but fall
    # back to get_matrix if permutation doesn't expose the chosen matrix.
    perm = PoseidonPermutation(t=t, r_f=0, r_p=r_p, alpha=alpha, matrix=matrix_name)
    try:
        M = perm.partial_matrix
    except Exception:
        M = get_matrix(matrix_name, t)

    # degrees: start as 1 (each output is linear in its own input)
    deg = [1] * t
    history = [(0, list(deg), max(deg))]

    for r in range(1, r_p + 1):
        # S-box on coord 0 increases degree multiplicatively
        deg[0] = deg[0] * alpha

        # Apply linear layer: new_deg[i] = max_j deg[j] where M[i][j] != 0
        new_deg = []
        for i in range(t):
            maxdeg = 0
            for j in range(t):
                if int(M[i][j]) != 0:
                    if deg[j] > maxdeg:
                        maxdeg = deg[j]
            new_deg.append(maxdeg)

        deg = new_deg
        history.append((r, list(deg), max(deg)))

    return history


def compare_matrices_degree(matrix_names=None, t=3, r_p=10, alpha=5):
    if matrix_names is None:
        matrix_names = list(MATRIX_NAMES.keys())
    out = {}
    for name in matrix_names:
        out[name] = track_algebraic_degree(name, t=t, r_p=r_p, alpha=alpha)
    return out
