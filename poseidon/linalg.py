"""
Generic linear algebra over F_p, for ANY prime p (RESEARCH_PLAN.md Sec 6.3:
the field is no longer hardcoded to BN254 -- every function below either
takes no field-typed data (identity()) and defaults to the BN254 Fp for
backward compatibility, or infers the field from the data it's handed
(`type(M[0][0])`), so the exact same code runs unmodified over KoalaBear,
Goldilocks, or any other make_field() prime.

Used by the Algorithm 1 invariant-subspace scanner (analysis/subspace_scanner.py)
to compute the characteristic polynomial of the restricted linear layer M_W,
evaluate polynomials at a matrix, and extract kernels/spans via Gaussian
elimination.
"""

from .field import Fp


def identity(n, field=Fp):
    return [[field(1) if i == j else field(0) for j in range(n)] for i in range(n)]


def mat_mul(A, B):
    rows, inner, cols = len(A), len(B), len(B[0])
    return [[sum(A[i][k] * B[k][j] for k in range(inner)) for j in range(cols)] for i in range(rows)]


def mat_add(A, B):
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def scalar_mul(c, A):
    return [[c * A[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def mat_pow(M, r):
    n = len(M)
    result = identity(n)
    base = [list(row) for row in M]
    while r > 0:
        if r & 1:
            result = mat_mul(result, base)
        base = mat_mul(base, base)
        r >>= 1
    return result


def trace(M):
    return sum(M[i][i] for i in range(len(M)))


def characteristic_polynomial(M):
    """
    Coefficients [c_0, c_1, ..., c_{n-1}, c_n=1] of det(xI - M) = sum_k c_k x^k,
    via the Faddeev-LeVerrier recursion:
        M_0 = 0,  c_n = 1
        M_k = M * M_{k-1} + c_{n-k+1} * I
        c_{n-k} = -(1/k) * trace(M * M_k)
    which holds over any field (division is by k = 1..n, invertible mod the
    large prime P).
    """
    n = len(M)
    field = type(M[0][0])
    I = identity(n, field)
    c = [None] * (n + 1)
    c[n] = field(1)
    Mk = [[field(0)] * n for _ in range(n)]  # M_0 = 0
    for k in range(1, n + 1):
        Mk = mat_add(mat_mul(M, Mk), scalar_mul(c[n - k + 1], I))
        inv_k = field(pow(k, field.P - 2, field.P))
        c[n - k] = -(trace(mat_mul(M, Mk)) * inv_k)
    return c


def poly_eval_matrix(coeffs, M):
    """Evaluate a polynomial (list of Fp coefficients, low degree first) at matrix M."""
    n = len(M)
    field = type(M[0][0])
    result = [[field(0)] * n for _ in range(n)]
    Mk = identity(n, field)
    for c in coeffs:
        if int(c) != 0:
            result = mat_add(result, scalar_mul(c, Mk))
        Mk = mat_mul(Mk, M)
    return result


def rref(matrix):
    """
    Row-reduce `matrix` (list of rows, each a list of Fp) over F_p.
    Returns (reduced_matrix, pivot_columns).
    """
    mat = [list(row) for row in matrix]
    if not mat:
        return mat, []
    field = type(mat[0][0])
    rows, cols = len(mat), len(mat[0])
    pivot_row = 0
    pivot_cols = []
    for col in range(cols):
        pivot = None
        for r in range(pivot_row, rows):
            if int(mat[r][col]) != 0:
                pivot = r
                break
        if pivot is None:
            continue
        mat[pivot_row], mat[pivot] = mat[pivot], mat[pivot_row]
        inv = field(pow(int(mat[pivot_row][col]), field.P - 2, field.P))
        mat[pivot_row] = [x * inv for x in mat[pivot_row]]
        for r in range(rows):
            if r != pivot_row and int(mat[r][col]) != 0:
                factor = mat[r][col]
                mat[r] = [mat[r][c] - factor * mat[pivot_row][c] for c in range(cols)]
        pivot_cols.append(col)
        pivot_row += 1
        if pivot_row == rows:
            break
    return mat, pivot_cols


def rank(matrix):
    if not matrix:
        return 0
    _, pivots = rref(matrix)
    return len(pivots)


def nullspace(matrix):
    """Basis (list of vectors) for the right nullspace {v : matrix @ v = 0}."""
    if not matrix:
        return []
    field = type(matrix[0][0])
    cols = len(matrix[0])
    red, pivot_cols = rref(matrix)
    free_cols = [c for c in range(cols) if c not in pivot_cols]
    basis = []
    for free in free_cols:
        vec = [field(0)] * cols
        vec[free] = field(1)
        for i, pc in enumerate(pivot_cols):
            vec[pc] = -red[i][free]
        basis.append(vec)
    return basis


def kron(A, B):
    """
    Kronecker (tensor) product of two matrices over F_p. Used to build
    Poseidon2(b)-style external-round matrices M_eps = P_{t/4} (x) M_4
    (Merz & Rodriguez Garcia 2026/306, Sec 2.2; RESEARCH_PLAN.md Step 1.4).
    """
    ra, ca = len(A), len(A[0])
    rb, cb = len(B), len(B[0])
    field = type(A[0][0])
    result = [[field(0)] * (ca * cb) for _ in range(ra * rb)]
    for i in range(ra):
        for j in range(ca):
            if int(A[i][j]) == 0:
                continue
            for k in range(rb):
                for l in range(cb):
                    result[i * rb + k][j * cb + l] = A[i][j] * B[k][l]
    return result


def finite_trail_space(M, r):
    """
    K_r(M) = intersection_{j=0}^{r-1} ker(e_0^T M^j)  (Vitto 2026/1579, Eq. 2;
    RESEARCH_PLAN.md Step 1.3).

    The subspace of directions d such that, for a family state(X) = c + X*d
    entering the partial rounds, the active (coordinate-0) S-box input stays
    X-independent for the next r partial rounds — i.e. the "finite trail"
    every linear layer unavoidably has (dim K_r(M) >= t-r; Eq. 4 shows
    equality, dim K_r(M) = t-r, when M has "maximal partial-round rank
    growth"). K_0(M) is the whole space (no constraint yet).

    Implementation: e_0^T M^j is row 0 of M^j, a row (functional) vector;
    v is in the kernel of that functional iff row_0(M^j) . v == 0. Stacking
    rows 0..r-1 of M^0, M^1, ..., M^(r-1) and taking the right nullspace
    gives exactly K_r(M).
    """
    n = len(M)
    field = type(M[0][0])
    if r <= 0:
        return identity(n, field)
    rows = []
    Mj = identity(n, field)
    for _ in range(r):
        rows.append(list(Mj[0]))
        Mj = mat_mul(M, Mj)
    return nullspace(rows)


def finite_trail_space_sequence(M, active_coords):
    """
    Generalizes finite_trail_space to a per-round ACTIVE-COORDINATE
    sequence instead of always coordinate 0 (RESEARCH_PLAN.md Step 5.6,
    testing the "rotate which lane carries the S-box" idea flagged but
    never tried in Sec 6.1-6):

        K = { v : for each round j, (active_coords[j])-th coordinate of
              M^j v is zero }

    finite_trail_space(M, r) is exactly this with active_coords = [0]*r.
    With a rotating schedule (e.g. active_coords[j] = j % t), each
    constraint comes from a DIFFERENT row of M^j instead of always row 0,
    which should generically be a more diverse (less redundant) set of
    constraints -- the question this function exists to answer
    empirically is whether that makes dim K shrink to 0 faster than the
    fixed-position design, i.e. whether rotation could let R_P be smaller
    for the same trail-length guarantee.
    """
    n = len(M)
    field = type(M[0][0])
    if not active_coords:
        return identity(n, field)
    rows = []
    Mj = identity(n, field)
    for pos in active_coords:
        rows.append(list(Mj[pos]))
        Mj = mat_mul(M, Mj)
    return nullspace(rows)


def mat_inv(M):
    """
    Inverse of a square matrix M over its own field, via Gauss-Jordan
    elimination on the augmented [M | I] matrix (reusing rref()). Raises
    ValueError if M is singular.

    Added for attacks/midpoint_reset.py (Jo 2026/1760's "M = V U^-1"
    interpolation step, RESEARCH_PLAN.md Step 7): nothing in this repo
    previously needed a general matrix inverse (scoring/scanning only ever
    needed rank/nullspace/characteristic polynomial).
    """
    n = len(M)
    field = type(M[0][0])
    aug = [list(M[i]) + [field(1) if i == j else field(0) for j in range(n)] for i in range(n)]
    red, pivots = rref(aug)
    if len(pivots) != n:
        raise ValueError("mat_inv: matrix is singular")
    return [row[n:] for row in red]


def in_span(basis_vectors, vector):
    """Whether `vector` lies in the span of `basis_vectors` (rank trick)."""
    if not basis_vectors:
        return all(int(x) == 0 for x in vector)
    r1 = rank(basis_vectors)
    r2 = rank(basis_vectors + [list(vector)])
    return r1 == r2
