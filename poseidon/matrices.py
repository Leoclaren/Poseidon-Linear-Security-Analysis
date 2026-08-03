"""
MDS and non-MDS matrices for Poseidon partial rounds.

This module now supports generating matrices for arbitrary t (small sizes used
in experiments). It provides helper generators for:
  - identity matrix
  - circulant non-MDS
  - a Poseidon2-like sparse matrix (one dense column / row)
  - an MDS matrix finder (random search for a matrix with B(M) >= t+1)

It also exposes get_matrix(name, t) to obtain a matrix suitable for the
requested state width t.
"""

from .field import Fp
import random

# --- Fixed MDS example for t=3 (kept for reproducibility) ---------------------
MDS_MATRIX_T3 = [
    [Fp(2),  Fp(3),  Fp(5)],
    [Fp(7),  Fp(11), Fp(13)],
    [Fp(17), Fp(19), Fp(23)],
]

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
    Construct a Poseidon2-like sparse matrix for experiments.
    Typical Poseidon2 sparse structure: many diagonal 1s with one column/row
    dense. We implement a canonical construction:
      - start with identity
      - choose a nonzero dense column (col 0) with small coefficients
      - optionally tweak first row to be dense as well

    This is not the official Poseidon2 constants, but reproduces the sparse
    / partially-dense structure for comparative experiments.
    """
    M = [[Fp(1) if i == j else Fp(0) for j in range(t)] for i in range(t)]
    # Dense first column (nonzero values)
    for i in range(t):
        if i == 0:
            M[i][0] = Fp(3)
        else:
            M[i][0] = Fp(2 + (i % 3))
    # Make first row denser as well
    for j in range(1, t):
        M[0][j] = Fp(1 + (j % 5))
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


# --- Top-level accessor -----------------------------------------------------

def get_matrix(name: str, t: int):
    """
    Return a t x t matrix (list of lists of Fp) for the given name.

    Supported names:
      - 'mds'      : attempt to produce an MDS matrix for given t
      - 'identity' : identity matrix of size t
      - 'circulant': circulant non-MDS example
      - 'poseidon2' : Poseidon2-like sparse matrix for experiments
    """
    name = name.lower()
    if name == "mds":
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
