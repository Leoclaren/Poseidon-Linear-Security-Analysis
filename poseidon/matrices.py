"""
MDS and non-MDS matrices for the Poseidon linear layer (t=3).
"""

from .field import Fp

# MDS matrix from CLAUDE.md benchmark — branch number >= 4 (MDS for t=3)
MDS_MATRIX = [
    [Fp(2),  Fp(3),  Fp(5)],
    [Fp(7),  Fp(11), Fp(13)],
    [Fp(17), Fp(19), Fp(23)],
]

# Non-MDS: identity matrix — branch number = 2 < 4
IDENTITY_MATRIX = [
    [Fp(1), Fp(0), Fp(0)],
    [Fp(0), Fp(1), Fp(0)],
    [Fp(0), Fp(0), Fp(1)],
]

# Circulant non-MDS example: keeps coord-0 contribution zero from certain diffs
CIRCULANT_NON_MDS = [
    [Fp(1), Fp(1), Fp(0)],
    [Fp(0), Fp(1), Fp(1)],
    [Fp(1), Fp(0), Fp(1)],
]


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
    Checks all 2^t - 1 binary support patterns as representative differences.
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


MATRIX_NAMES = {
    "mds": MDS_MATRIX,
    "identity": IDENTITY_MATRIX,
    "circulant": CIRCULANT_NON_MDS,
}
