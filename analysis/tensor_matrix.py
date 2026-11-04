"""
Step 1.4 of the S&P2027 plan (RESEARCH_PLAN.md Sec 9): replicate the
mechanism behind Merz & Rodriguez Garcia 2026/306's round-skipping attack
on Poseidon2(b)'s tensor-structured external-round matrix, and confirm
their proposed free fix (swap the Kronecker factor order) actually breaks
the specific eigenvector shape the attack needs.

Background (paper Sec 2.2, 2026-306.pdf): Poseidon2(b)'s external-round
matrix is M_eps = P_{t/4} (x) M_4, where P_m = I + J (diagonal 2,
off-diagonal 1 -- J is the all-ones matrix) and M_4 is a fixed 4x4 MDS
matrix. P_m has eigenvalue 1 on the (m-1)-dimensional subspace of vectors
summing to zero (e.g. v=(1,-1,0,...,0)): J v = 0, so P_m v = v + 0 = v.

Tensoring that eigenvector with an ARBITRARY length-4 vector q gives a
whole (m-1)*4-dimensional family of vectors of the form
  (q, -q, 0, 0, ..., 0)   [contiguous quadruple blocks]
that M_eps fixes EXACTLY (eigenvalue 1, no degree growth at all across a
full round) -- this is the "(X,-X)" unconstrained subspace the paper's
round-skipping attacks exploit. The paper's proposed countermeasure
(Sec 6): swap the Kronecker factor order, M_eps_bar = M_4 (x) P_{t/4}.
Same multiplication cost (same factors, just reordered up to a
permutation of indices), but the same contiguous-block (q,-q,0,...,0)
shape no longer lines up with an eigenvector of the swapped tensor -- this
module demonstrates that directly by matrix-vector multiplication.
"""

from poseidon.field import Fp
from poseidon.linalg import kron
from poseidon.matrices import matrix_mul


def mul_complexity_tensor(t, field=Fp):
    """
    Real fast-algorithm multiplicative complexity of applying the SAFE-order
    tensor-structured external matrix M_eps_bar = M_4 (x) P_(t/4), computed
    the way real implementations actually do it (verified against Plonky3's
    own `mds_light_permutation`, RESEARCH_PLAN.md Step 5.9): apply M_4 to
    each of t/4 four-wide blocks, then an OUTER circulant mix that is pure
    addition (every P_(t/4) entry is 1 or 2 -- P_(t/4)'s own mul_complexity
    is 0) -- not poseidon.matrix_search.mul_complexity's generic "count
    non-{0,1} entries of the fully-expanded t x t matrix", which badly
    UNDERSTATES a tensor matrix's real cost advantage (confirmed in Step
    5.11: naive expanded-entry count for t=16 is 184, the real fast-
    algorithm cost is 40 -- 4.6x apart).
    """
    if t % 4 != 0:
        raise ValueError("t must be a multiple of 4 for the Poseidon2(b) tensor structure")
    from poseidon.matrix_search import mul_complexity
    blocks = t // 4
    return blocks * mul_complexity(m4_matrix(field=field))


def p_matrix(m, field=Fp):
    """
    P_m = I + J (diagonal 2, off-diagonal 1). Eigenvalue m+1 on the
    all-ones vector; eigenvalue 1 on the (m-1)-dim subspace of vectors
    summing to zero (e.g. (1,-1,0,...,0)) -- this is the low-weight
    eigenstructure Merz & Rodriguez Garcia 2026/306 Sec 2.2 exploits.
    """
    return [[field(2) if i == j else field(1) for j in range(m)] for i in range(m)]


def m4_matrix(field=Fp):
    """The paper's concrete 4x4 MDS matrix used for every M_4 factor (Sec 2.2)."""
    return [
        [field(5), field(7), field(1), field(3)],
        [field(4), field(6), field(1), field(1)],
        [field(1), field(3), field(5), field(7)],
        [field(1), field(1), field(4), field(6)],
    ]


def external_matrices(t, field=Fp):
    """Return (M_eps, M_eps_swapped) = (P_(t/4) kron M4, M4 kron P_(t/4))."""
    if t % 4 != 0:
        raise ValueError("t must be a multiple of 4 (Poseidon2(b) quadruple structure)")
    m = t // 4
    P_m = p_matrix(m, field=field)
    M4 = m4_matrix(field=field)
    return kron(P_m, M4), kron(M4, P_m)


def build_x_neg_x_vector(t, q):
    """
    The exact attack-shape vector: contiguous quadruple block 0 = q, block
    1 = -q, every other block zero -- v=(1,-1,0,...,0) tensored with q.
    """
    if t % 4 != 0 or len(q) != 4:
        raise ValueError("t must be a multiple of 4 and q must have length 4")
    field = type(q[0])
    vec = [field(0)] * t
    for i in range(4):
        vec[i] = q[i]
        vec[4 + i] = -q[i]
    return vec


def _is_block_x_neg_x(vec, t):
    """
    True iff vec (length t) has the (w, -w, 0, ..., 0) contiguous-block
    shape: first 4 entries = w, next 4 = -w, everything after that zero.
    NOTE: for a Kronecker eigenvector v (x) q of M_eps = P (x) M4 with P v
    = lambda*v, the output is lambda*(v (x) (M4 q)) -- the SUBSPACE {v (x)
    w : w in F^4} is invariant, but the vector itself is only an exact
    FIXED POINT when lambda=1 (true here) -- the inner w changes to M4*q
    each round. So the right membership test is "still has this block
    shape", not literal equality to the input.
    """
    if len(vec) != t:
        return False
    block0, block1, rest = vec[0:4], vec[4:8], vec[8:]
    matches_neg = all(int(block0[i]) == int(-block1[i]) for i in range(4))
    rest_zero = all(int(x) == 0 for x in rest)
    return matches_neg and rest_zero


def demo_full_round_survival(t=16, alpha=5, n_rounds=4, q=(1, 2, 3, 4)):
    """
    Push the (q,-q,0,...,0) vector through n_rounds FULL rounds (S-box on
    every coordinate, then M_eps) and confirm the block shape survives
    every single round -- for ODD alpha, (-w)^alpha = -(w^alpha)
    componentwise, so the S-box alone preserves the shape; combined with
    demo_eigenvector_structure's result that M_eps also preserves it, the
    whole family survives full rounds indefinitely at ZERO degree cost --
    the actual "free lunch" the paper's round-skipping attacks spend.
    """
    M_eps, _ = external_matrices(t)
    state = build_x_neg_x_vector(t, [Fp(x) for x in q])
    per_round = []
    for r in range(n_rounds):
        sbox_out = [x ** alpha for x in state]
        shape_after_sbox = _is_block_x_neg_x(sbox_out, t)
        state = matrix_mul(M_eps, sbox_out)
        shape_after_mix = _is_block_x_neg_x(state, t)
        per_round.append({"round": r, "survives_sbox": shape_after_sbox, "survives_M_eps": shape_after_mix})
    return {
        "t": t, "alpha": alpha, "n_rounds": n_rounds,
        "per_round": per_round,
        "survives_all_rounds": all(p["survives_sbox"] and p["survives_M_eps"] for p in per_round),
    }


def demo_eigenvector_structure(t=16, q=(1, 2, 3, 4)):
    """
    Build the (X,-X,0,...,0) vector and push it through both M_eps and the
    swapped M_eps_bar. Because P_m's eigenvalue-1 eigenspace is tensored
    with an ARBITRARY inner vector, M_eps maps the (q,-q,0,...,0) subspace
    back into ITSELF (output = (M4 q, -(M4 q), 0,...,0): same block shape,
    inner vector transformed by M4 but the block structure survives
    exactly, round after round, at zero degree cost -- the "free lunch"
    the attack exploits). The swapped matrix is expected to NOT preserve
    that specific contiguous-block shape, confirming the countermeasure.
    """
    q = [Fp(x) for x in q]
    M_eps, M_eps_swapped = external_matrices(t)
    vec = build_x_neg_x_vector(t, q)

    out_eps = matrix_mul(M_eps, vec)
    out_swapped = matrix_mul(M_eps_swapped, vec)

    subspace_survives_eps = _is_block_x_neg_x(out_eps, t)
    subspace_survives_swapped = _is_block_x_neg_x(out_swapped, t)

    return {
        "t": t,
        "input_(X,-X,0,...)": [int(x) for x in vec],
        "M_eps_output": [int(x) for x in out_eps],
        "M_eps_output_still_(w,-w,0,...)_shape": subspace_survives_eps,
        "M_eps_swapped_output": [int(x) for x in out_swapped],
        "M_eps_swapped_output_still_(w,-w,0,...)_shape": subspace_survives_swapped,
        "countermeasure_confirmed": subspace_survives_eps and not subspace_survives_swapped,
    }
