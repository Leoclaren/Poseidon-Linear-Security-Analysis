"""
MDS and non-MDS matrices for the Poseidon1 partial-round linear layer,
generalized to arbitrary state width t (t = 3 used to match the CLAUDE.md
worked proof verbatim; t = 4, 5, ... generated from the same constructions
used by the paper's multi-width experiments) AND, since RESEARCH_PLAN.md
Sec 6.3, to any prime field via the `field=` parameter (default: BN254).
"""

from .field import Fp


def identity_matrix(t, field=Fp):
    """t x t identity matrix. Branch number = 2 for any t — always non-MDS."""
    return [[field(1) if i == j else field(0) for j in range(t)] for i in range(t)]


def cauchy_mds_matrix(t, field=Fp):
    """
    Cauchy matrix construction: M[i][j] = 1 / (x_i - y_j), with
    x_i = i+1, y_j = t+1+j (two disjoint, pairwise-distinct index sets).

    Every square submatrix of a Cauchy matrix is nonsingular, so M is MDS
    (branch number t+1) for any t over any field large enough that
    x_i != y_j for all i, j (true for every field this repo uses, including
    small ones like KoalaBear, since t << p). This is the standard way to
    obtain an explicit MDS matrix for widths where no hand-picked benchmark
    (like the t=3 case below) exists.
    """
    xs = [i + 1 for i in range(t)]
    ys = [t + 1 + j for j in range(t)]
    M = []
    for i in range(t):
        row = []
        for j in range(t):
            denom = (xs[i] - ys[j]) % field.P
            row.append(field(pow(denom, field.P - 2, field.P)))
        M.append(row)
    return M


def poseidon2_style_matrix(t, field=Fp):
    """
    Sparse, diagonal-dominant, bandwidth-1 (tridiagonal) non-MDS matrix in
    the spirit of the Poseidon2 internal matrix for partial rounds:
    diagonal = (2, 2, ..., 2, t), off-diagonal (bandwidth 1) = 1.

    For t=3 this is exactly the paper's example matrix [[2,1,0],[1,2,1],[0,1,3]].
    """
    M = [[field(0)] * t for _ in range(t)]
    for i in range(t):
        M[i][i] = field(t) if i == t - 1 else field(2)
        if i + 1 < t:
            M[i][i + 1] = field(1)
            M[i + 1][i] = field(1)
    return M


def circulant_non_mds_matrix(t, field=Fp):
    """Sparse circulant non-MDS matrix: row i = row 0 rotated right by i."""
    first_row = [field(1), field(1)] + [field(0)] * (t - 2)
    return [[first_row[(j - i) % t] for j in range(t)] for i in range(t)]


# ---------------------------------------------------------------------------
# t = 3 benchmark matrices — kept as explicit literals (rather than the
# general constructions above) so the worked examples in CLAUDE.md and the
# paper's concrete t=3 example remain reproducible verbatim.
# ---------------------------------------------------------------------------

MDS_MATRIX = [
    [Fp(2),  Fp(3),  Fp(5)],
    [Fp(7),  Fp(11), Fp(13)],
    [Fp(17), Fp(19), Fp(23)],
]

IDENTITY_MATRIX = identity_matrix(3)

CIRCULANT_NON_MDS = circulant_non_mds_matrix(3)

# Paper's concrete Poseidon2-style t=3 matrix: [[2,1,0],[1,2,1],[0,1,3]]
POSEIDON2_STYLE_MATRIX = poseidon2_style_matrix(3)


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
    field = type(M[0][0])
    best = float("inf")
    for mask in range(1, 2 ** t):
        delta = [field(1) if (mask >> i) & 1 else field(0) for i in range(t)]
        Mdelta = matrix_mul(M, delta)
        score = weight(delta) + weight(Mdelta)
        if score < best:
            best = score
    return best


def get_matrix_set(t: int, field=Fp) -> dict:
    """
    Return the {name: matrix} family of partial-round linear layers for a
    given state width t and field. For t=3 over the default BN254 field
    this returns the exact benchmark matrices used throughout CLAUDE.md /
    the paper; for other widths, or any other field (e.g. field=FpKoalaBear,
    RESEARCH_PLAN.md Sec 6.3), it returns the general constructions above,
    which follow the same design pattern (Cauchy MDS, tridiagonal
    Poseidon2-style, circulant, identity) so the multi-width/multi-field
    analysis is reproducible.
    """
    if t == 3 and field is Fp:
        return {
            "mds": MDS_MATRIX,
            "identity": IDENTITY_MATRIX,
            "circulant": CIRCULANT_NON_MDS,
            "poseidon2": POSEIDON2_STYLE_MATRIX,
        }
    return {
        "mds": cauchy_mds_matrix(t, field),
        "identity": identity_matrix(t, field),
        "circulant": circulant_non_mds_matrix(t, field),
        "poseidon2": poseidon2_style_matrix(t, field),
    }


# Backward-compatible default (t=3) matrix registry — most call sites that
# predate multi-width support still default to t=3 and import this name.
MATRIX_NAMES = get_matrix_set(3)
