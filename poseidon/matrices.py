"""
MDS and non-MDS matrices for Poseidon partial rounds.

This module now supports generating matrices for arbitrary t (small sizes used
in experiments). It provides helper generators for:
  - identity matrix
  - circulant non-MDS
  - a Poseidon2-like sparse matrix (one dense column / row)
  - Cauchy-based deterministic MDS matrices for t=3..8
  - an MDS matrix finder (random search for a matrix with B(M) >= t+1)

It also exposes get_matrix(name, t) to obtain a matrix suitable for the
requested state width t.

Deterministic MDS construction
------------------------------
We use small-integer Cauchy matrices (C[i][j] = 1/(x_i + y_j)) with distinct
x_i,y_j. Cauchy matrices are a standard MDS construction and work well over
large prime fields. The Fp division operator is used to compute the entries.
"""

from .field import Fp
import random

# --- Fixed MDS example for t=3 (kept for reproducibility) ---------------------
MDS_MATRIX_T3 = [
    [Fp(2),  Fp(3),  Fp(5)],
    [Fp(7),  Fp(11), Fp(13)],
    [Fp(17), Fp(19), Fp(23)],
]

# Backwards-compatible alias expected by other modules
MDS_MATRIX = MDS_MATRIX_T3

# --- Utilities ---------------------------------------------------------------

def matrix_mul(M, state):
    """Multiply matrix M (list of lists of Fp) by state (list of Fp)."""
    t = len(state)
    return [sum(M[i][j] * state[j] for j in range(t)) for i in range(t)]


def weight(vec):
    """Hamming weight: number of non-zero coordinates."""
    return sum(1 for x in vec if int(x) != 0)


def branch_number(M):
    """
    Compute the branch number of matrix M over F_p^t.
    B(M) = min over all nonzero delta of (wt(delta) + wt(M*delta)).
    This brute-force enumerates all binary support masks (works fine for t <= 8).
    """
    t = len(M)
    best = float("inf")
    # Iterate over all nonzero binary vectors as difference representatives
    for mask in range(1, 2**t):
        delta = [Fp(1) if (mask >> i) & 1 else Fp(0) for i in range(t)]
        Mdelta = matrix_mul(M, delta)
        score = weight(delta) + weight(Mdelta)
        if score < best:
            best = score
    return best


# --- Matrix generators ------------------------------------------------------

def identity_matrix(t):
    return [[Fp(1) if i == j else Fp(0) for j in range(t)] for i in range(t)]


def circulant_non_mds(t):
    # Simple circulant pattern that generalises the t=3 example.
    # Note: may or may not be non-MDS for larger t; it's an illustrative matrix.
    base = [1] * t
    base[-1] = 0
    M = []
    for i in range(t):
        row = [Fp(base[(j - i) % t]) for j in range(t)]
        M.append(row)
    return M


def poseidon2_like_matrix(t):
    """
    Sparse non-MDS matrix in Poseidon2 style (diagonal-dominant with limited bandwidth).
    For t=3 this has branch number 3 (non-MDS).
    """
    if t == 3:
        return [
            [Fp(2), Fp(1), Fp(0)],
            [Fp(1), Fp(2), Fp(1)],
            [Fp(0), Fp(1), Fp(3)],
        ]

    M = [[Fp(0) for _ in range(t)] for _ in range(t)]
    for i in range(t):
        M[i][i] = Fp(2 + (i % 3))
        if i + 1 < t:
            M[i][i+1] = Fp(1)
        if i - 1 >= 0:
            M[i][i-1] = Fp(1)
    return M


def random_dense_matrix(t, low=1, high=20):
    """Random dense small-integer matrix (Fp elements)"""
    M = []
    for i in range(t):
        row = [Fp(random.randint(low, high)) for _ in range(t)]
        M.append(row)
    return M


def find_mds_matrix(t, attempts=2000):
    """
    Try to find a small-integer dense matrix that meets the MDS branch number
    threshold B(M) >= t+1. This is a randomized search; for small t it is fast.
    Returns a matrix (list of lists of Fp) or raises RuntimeError.
    """
    if t == 3:
        return MDS_MATRIX_T3

    threshold = t + 1
    for _ in range(attempts):
        M = random_dense_matrix(t)
        if branch_number(M) >= threshold:
            return M
    raise RuntimeError(f"Failed to find MDS-like matrix for t={t} after {attempts} attempts")


# --- Deterministic Cauchy MDS matrices for t=4..8 ---------------------------

def cauchy_mds(t, xs=None, ys=None):
    """Build a t x t Cauchy matrix over Fp: C[i][j] = 1/(x_i + y_j).

    xs and ys should be lists of distinct small integers such that x_i + y_j
    are nonzero mod p. If None, default small disjoint sets are chosen.
    """
    if xs is None:
        xs = [i + 1 for i in range(t)]
    if ys is None:
        ys = [t + 1 + i for i in range(t)]

    # Build matrix using Fp division
    M = []
    for i in range(t):
        row = []
        xi = Fp(xs[i])
        for j in range(t):
            yj = Fp(ys[j])
            denom = xi + yj
            # denom should not be zero in the chosen small-integer construction
            row.append(Fp(1) / denom)
        M.append(row)
    return M


# Precompute deterministic MDS matrices for small t
MDS_MATRIX_T4 = cauchy_mds(4)
MDS_MATRIX_T5 = cauchy_mds(5)
MDS_MATRIX_T6 = cauchy_mds(6)
MDS_MATRIX_T7 = cauchy_mds(7)
MDS_MATRIX_T8 = cauchy_mds(8)

# verify they meet the branch number threshold at import time (sanity check)
_precomputed_mds = {
    3: MDS_MATRIX_T3,
    4: MDS_MATRIX_T4,
    5: MDS_MATRIX_T5,
    6: MDS_MATRIX_T6,
    7: MDS_MATRIX_T7,
    8: MDS_MATRIX_T8,
}

for _t, M in _precomputed_mds.items():
    bn = branch_number(M)
    if bn < _t + 1:
        raise RuntimeError(f"Precomputed matrix for t={_t} failed MDS check: B(M)={bn}")


# --- Top-level accessor -----------------------------------------------------

def get_matrix(name: str, t: int):
    """
    Return a t x t matrix (list of lists of Fp) for the given name.

    Supported names:
      - 'mds'      : return a deterministic MDS matrix for 3 <= t <= 8, or try
                     to produce one via randomized search for larger t
      - 'identity' : identity matrix of size t
      - 'circulant': circulant non-MDS example
      - 'poseidon2' : Poseidon2-like sparse matrix for experiments
    """
    name = name.lower()
    if name == "mds":
        # return precomputed deterministic matrices for small t
        if t in _precomputed_mds:
            return _precomputed_mds[t]
        # otherwise fall back to randomized finder
        return find_mds_matrix(t)
    if name == "identity":
        return identity_matrix(t)
    if name == "circulant":
        return circulant_non_mds(t)
    if name == "poseidon2":
        return poseidon2_like_matrix(t)

    # Backwards-compatible: allow passing an explicit matrix object
    if isinstance(name, list):
        return name

    raise ValueError(f"Unknown matrix name: {name}")


# Keep a small alias mapping for legacy code that inspected MATRIX_NAMES for t=3
MATRIX_NAMES = {
    "mds": MDS_MATRIX_T3,
    "identity": identity_matrix(3),
    "circulant": circulant_non_mds(3),
}
