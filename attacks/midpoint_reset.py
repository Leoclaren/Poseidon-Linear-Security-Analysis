"""
Replication of Sunghyeon Jo's "Midpoint Reset: A Full-Round Poseidon
Collision from an Adaptively Chosen MDS Matrix" (IACR eprint 2026/1760,
local copy: 2026-1760.pdf), and a direct test of whether this repo's own
Step 3.1 countermeasure (poseidon.matrix_search.generate_bound_round_constants
-- binding round constants to a canonical encoding of the matrix) closes
the gap this attack exploits.

Jo's own Discussion section (Sec 6) names exactly this fix -- "derive the
complete parameter set non-adaptively ... by binding the round constants
to a canonical encoding of the matrix" -- as the natural countermeasure,
but the paper neither builds nor tests it. This module does both, with
the same Phase-0 discipline the rest of this repo used for Vitto
2026/1579 and Merz & Rodriguez Garcia 2026/306: replicate the real
mechanism first, on our own data, before claiming a fix works against it.

THE ATTACK (Sec 2-4 of the paper), in one paragraph: if the round
constants c^(r) are fixed BEFORE the linear layer M is chosen, an
attacker can run two executions x+/x- in lockstep, tracking their
midpoint m_r=(x+_r+x-_r)/2 and half-difference d_r=(x+_r-x-_r)/2. One
prescribed matrix image per two-round block (M u_r = -c^(r+1)) cancels
the midpoint against the next round constant, so the odd S-box resets it
to exactly zero for the rest of the permutation ("midpoint reset"). Two
further reusable images (M e = v, M w = e, on a coordinate e that is
passive in every partial round) keep the half-difference confined to the
one-dimensional line F*e through every full AND partial round. Collecting
these prescribed images as columns of U (sources) and V (targets), M =
V U^-1 is the UNIQUE matrix realizing the whole trajectory -- and a
correctly closed trajectory (final difference = -initial difference)
yields a genuine feed-forward collision, in an M that is a perfectly
well-formed MDS matrix passing every subspace-trail check. No static
property of M is exploited; the vulnerability is the GENERATION ORDER.

SCOPE (same "replicate the mechanism, not the literal headline instance"
choice RESEARCH_PLAN.md Step 1.2 made for Vitto's 3^10-vs-3^28 numbers):
this module implements the construction generically for alpha=3 and
EXACTLY ONE full-round block on each side of the partial-round segment
(r_f == 4), rather than Jo's r_f=8 (two blocks per side). This sidesteps
Jo's harder two-block "entry"/"closing" cubic solves (which need a real
cubic-root algorithm over F_p) via a closed-form single-block trick: by
choosing the entry block's free scalar s_0 = 0 (always achievable, since
s_0 is fixed only by our own free choice of initial midpoint m_0), the
entry amplitude collapses to a direct cube root, b_0 = cube_root(a), and
the resulting output amplitude after that single block is EXACTLY `a` by
construction (no solve needed -- see build_construction()'s docstring for
the derivation). The only remaining unknown, the closing scalar `a`
itself, is found by brute-force search over a small TOY prime field
(instant at that scale) rather than a general polynomial-root algorithm
at full KoalaBear/BN254 scale -- exactly how Step 1.2 scoped its own
replication to "confirms the mechanism, not the paper's literal numbers."
The underlying linear-algebra core (build_construction, M = V U^-1,
forward verification) is fully generic in t, field, and round constants.
"""

from poseidon.linalg import mat_inv, mat_mul, rank
from poseidon.matrices import matrix_mul as mat_vec
from poseidon.matrix_search import (
    generate_bound_round_constants, poseidon2_sparse_candidate,
    low_weight_circulant_candidate, irreducible_filtered_candidate,
)


# ---------------------------------------------------------------------------
# Field-generic scalar helpers
# ---------------------------------------------------------------------------

def cube_root(x, field):
    """
    The unique y with y^3 = x, via y = x^(3^-1 mod (p-1)). Requires
    gcd(3, p-1) == 1 -- exactly the condition alpha=3 already needs to be
    a valid (bijective) Poseidon S-box, so this always holds whenever the
    construction itself is applicable.
    """
    if (field.P - 1) % 3 == 0:
        raise ValueError("cube_root: gcd(3, p-1) != 1 -- alpha=3 would not be a bijective S-box over this field")
    e = pow(3, -1, field.P - 1)
    return field(pow(int(x), e, field.P))


def half_sum_nonlinear(s, d, alpha, full, field):
    """
    eq. (4): u_r = (S_r(s_r+d_r) + S_r(s_r-d_r)) / 2, for S_r = S_F (full,
    every coordinate raised to alpha) or S_r = S_P (partial, only
    coordinate 0). This is computable directly from known s_r, d_r --
    it does NOT involve the (still unknown) matrix M at all, which is
    exactly what lets the whole interpolation system be built before M
    exists.
    """
    t = len(s)
    plus = [s[i] + d[i] for i in range(t)]
    minus = [s[i] - d[i] for i in range(t)]
    if full:
        s_plus = [x ** alpha for x in plus]
        s_minus = [x ** alpha for x in minus]
    else:
        s_plus = [plus[0] ** alpha] + list(plus[1:])
        s_minus = [minus[0] ** alpha] + list(minus[1:])
    inv2 = field(pow(2, field.P - 2, field.P))
    return [(s_plus[i] + s_minus[i]) * inv2 for i in range(t)]


# ---------------------------------------------------------------------------
# The permutation, in the PAPER's own round convention (Eq. 1):
#   R_r(x) = M * S_r(x + c^(r))   -- add constants, THEN S-box, THEN M.
#
# This differs from poseidon/permutation.py's convention (S-box, THEN add
# constants, THEN M -- see CLAUDE.md's own pseudocode), which this repo
# uses everywhere else. The midpoint-reset algebra in Sec 2.4-3.3 is
# proved for Eq. (1) specifically, so faithful replication needs this
# exact convention rather than reusing PoseidonPermutation.
# ---------------------------------------------------------------------------

def apply_round(M, x, c, alpha, full):
    t = len(x)
    y = [x[i] + c[i] for i in range(t)]
    s = [v ** alpha for v in y] if full else [y[0] ** alpha] + list(y[1:])
    return mat_vec(M, s)


def permute(M, constants, t, alpha, r_f, r_p, state):
    half = r_f // 2
    total = r_f + r_p
    x = list(state)
    for r in range(total):
        full = r < half or r >= half + r_p
        c = constants[r * t:(r + 1) * t]
        x = apply_round(M, x, c, alpha, full)
    return x


def feed_forward_hash(M, constants, t, alpha, r_f, r_p, state):
    """Eq. (3): H_M(x) = P_M(x) + x."""
    out = permute(M, constants, t, alpha, r_f, r_p, state)
    return [out[i] + state[i] for i in range(t)]


# ---------------------------------------------------------------------------
# The construction (Sec 3.1-3.3), scoped to r_f == 4 (one full-round block
# per side -- see module docstring).
# ---------------------------------------------------------------------------

def closing_equation(a, constants, t, r_f, r_p, passive_index, field):
    """
    f(a) = b_final(a) - (-b0(a)), both in closed form under the r_f==4 /
    s_0=0 scoping:

      b0(a)     = cube_root(a)                              (entry, Sec 3.1/Table 1,
                                                                via our s_0=0 trick)
      b_final(a) = a * (a^2 + 3*s_exit^2)^3                  (exit, Eq. 10 with the
                                                                FORCED s_exit = c^(r_exit)[passive],
                                                                since midpoint=0 entering
                                                                every reset-driven even round)

    A root a* of f gives a trajectory whose final difference is exactly
    the negative of its initial difference -- the feed-forward collision
    condition (paper's Theorem 1). Returns f(a); callers brute-force scan
    for a root over a small field (module scope note).
    """
    total = r_f + r_p
    r_exit = r_f // 2 + r_p
    c_exit = constants[r_exit * t: (r_exit + 1) * t]
    s_exit = c_exit[passive_index]
    a = field(a)
    b0 = cube_root(a, field)
    b_final = a * ((a * a + field(3) * s_exit * s_exit) ** 3)
    return b_final + b0  # == 0 at a root (b_final == -b0)


def find_closing_amplitude(constants, t, r_f, r_p, passive_index, field):
    """Brute-force scan over F_p* for a root of closing_equation (module
    scope note: this repo-wide toy-field discipline, not Jo's general
    polynomial-root algorithm, which this replication does not need)."""
    for a in range(1, field.P):
        if int(closing_equation(a, constants, t, r_f, r_p, passive_index, field)) == 0:
            return a
    return None


def build_construction(constants, t, alpha, r_f, r_p, a, field, passive_index=1, v0=None):
    """
    Build the midpoint-reset interpolation system (Sec 3.3): U (source
    images, computable from `constants` and `a` ALONE -- no matrix
    involved), V (target images, from `constants` and the difference-cycle
    vectors v/w), and the two states whose collision M = V U^-1 is meant
    to realize.

    Returns a dict with U, V, x_plus, x_minus, and the scalars used, or
    {"feasible": False, ...} if det(U) == 0 (Eq. 16's consistency
    condition fails for this trajectory -- a degenerate case, not
    expected for a generic `a`).
    """
    if alpha != 3:
        raise ValueError("midpoint reset needs an odd cubic S-box (paper's Eq. 2)")
    if r_f != 4:
        raise ValueError("this replication only implements the single-full-round-block-per-side case (r_f=4)")
    total = r_f + r_p
    half = r_f // 2
    L = total // 2
    if L + 2 > t:
        raise ValueError(f"L+2 <= t required (Sec 6 'Image constraints'): L={L}, t={t}")

    a = field(a)
    inv_a = field(pow(int(a), field.P - 2, field.P))
    v0 = field(v0) if v0 is not None else field(1)

    e = [field(0)] * t
    e[passive_index] = field(1)
    v = [field(0)] * t
    v[0] = v0
    for i in range(1, t):
        v[i] = inv_a if i % 2 else -inv_a
    w = [a * a * (v[i] ** 3) for i in range(t)]  # w = a^2 . v^.3 (Eq. 8)

    # --- entry block (round 0, FULL): choose m0 so s0[passive] = 0.
    c0 = constants[0:t]
    m0 = [field(0)] * t
    m0[passive_index] = -c0[passive_index]
    b0 = cube_root(a, field)
    s0 = [m0[i] + c0[i] for i in range(t)]
    d0 = [field(0)] * t
    d0[passive_index] = b0
    u0 = half_sum_nonlinear(s0, d0, alpha, True, field)
    target0 = [-constants[1 * t + i] for i in range(t)]  # -c^(1)

    # --- partial blocks (every even round in [half, half+r_p)): s_r=c^(r)
    #     (midpoint forced to 0 by the previous reset), d_r = a*e (Sec 3.2
    #     proves this amplitude is preserved exactly across every block).
    u_cols, targets = [u0], [target0]
    for r in range(half, half + r_p, 2):
        c_r = constants[r * t:(r + 1) * t]
        d_r = [field(0)] * t
        d_r[passive_index] = a
        u_r = half_sum_nonlinear(c_r, d_r, alpha, False, field)
        u_cols.append(u_r)
        targets.append([-constants[(r + 1) * t + i] for i in range(t)])

    # --- exit block (round half+r_p, FULL): s_exit = c^(r_exit) (forced).
    r_exit = half + r_p
    c_exit = constants[r_exit * t:(r_exit + 1) * t]
    d_exit = [field(0)] * t
    d_exit[passive_index] = a
    u_exit = half_sum_nonlinear(c_exit, d_exit, alpha, True, field)
    u_cols.append(u_exit)
    targets.append([-constants[(r_exit + 1) * t + i] for i in range(t)])

    u_cols += [e, w]
    targets += [v, e]

    U = [[u_cols[j][i] for j in range(len(u_cols))] for i in range(t)]
    V = [[targets[j][i] for j in range(len(targets))] for i in range(t)]

    if rank(U) < t:
        return {"feasible": False, "reason": "det(U) == 0: interpolation underdetermined for this trajectory"}

    return {
        "feasible": True,
        "U": U, "V": V,
        "m0": m0, "b0": b0, "a": a,
        "x_plus": [m0[i] + (b0 if i == passive_index else field(0)) for i in range(t)],
        "x_minus": [m0[i] - (b0 if i == passive_index else field(0)) for i in range(t)],
        "passive_index": passive_index,
    }


def run_attack(constants, t, alpha, r_f, r_p, field, passive_index=1, v0=None, search_a=True, fixed_a=None):
    """
    Full Phase-0-style replication: find a closing amplitude `a` (brute
    force over `field`, which should be a small toy prime for this to
    terminate quickly -- see module docstring), build the interpolation
    system, solve M = V U^-1, and verify a genuine feed-forward collision
    against the actual permutation (not just the scalar bookkeeping).
    """
    a = fixed_a
    if search_a:
        a = find_closing_amplitude(constants, t, r_f, r_p, passive_index, field)
        if a is None:
            return {"collision_found": False, "reason": "no closing amplitude found in this field"}

    construction = build_construction(constants, t, alpha, r_f, r_p, a, field, passive_index, v0)
    if not construction["feasible"]:
        return {"collision_found": False, **construction, "a": a}

    # M U = V  =>  M = V U^-1 (right-multiply by the inverse -- NOT U^-1 V,
    # matrix multiplication is non-commutative and U^-1 V solves a
    # different system, U X = V for X, not M U = V for M).
    M = mat_mul(construction["V"], mat_inv(construction["U"]))

    x_plus, x_minus = construction["x_plus"], construction["x_minus"]
    h_plus = feed_forward_hash(M, constants, t, alpha, r_f, r_p, x_plus)
    h_minus = feed_forward_hash(M, constants, t, alpha, r_f, r_p, x_minus)
    collision = all(int(h_plus[i]) == int(h_minus[i]) for i in range(t)) and x_plus != x_minus

    return {
        "collision_found": collision,
        "a": int(a),
        "M": M,
        "x_plus": x_plus, "x_minus": x_minus,
        "H_x_plus": h_plus, "H_x_minus": h_minus,
        "b0": int(construction["b0"]),
    }


# ---------------------------------------------------------------------------
# Part 2: does binding constants to the matrix (Step 3.1) close this gap?
# ---------------------------------------------------------------------------

def check_bound_matrix_immune(t, alpha, r_f, r_p, field, passive_index=1,
                               seed_label="poseidon-sp2027-v1-midpoint-reset-test",
                               candidate_fn=poseidon2_sparse_candidate):
    """
    Generate a matrix M the HONEST way (NUMS, Step 3.3's poseidon2_sparse
    family) and derive constants c = Hash(seed || params || M || M) via
    generate_bound_round_constants -- i.e. c is fixed AFTER and FROM M,
    the reverse of the order the attack needs (M chosen after c is fixed).

    Then check, for every nonzero `a` in this (small, toy) field: does the
    ALREADY-FIXED M happen to satisfy the midpoint-reset image constraints
    M @ U(c, a) == V(c, a) for that a? This is a direct equality check on
    a matrix that is NOT being solved for -- it is fixed by the honest
    generation process -- so this is exactly Phase-3-style adversarial
    falsification: if NO `a` makes M consistent with the attack's required
    relations, the binding has removed the "choose M after c" freedom the
    whole construction depends on, for this concrete instance.
    """
    M, meta = candidate_fn(t, seed_label=seed_label, field=field)
    constants = generate_bound_round_constants(M, M, t, r_f, r_p, alpha, seed_label=seed_label, field=field)

    consistent_a = []
    for a in range(1, field.P):
        try:
            construction = build_construction(constants, t, alpha, r_f, r_p, a, field, passive_index)
        except ValueError:
            continue
        if not construction["feasible"]:
            continue
        U, V = construction["U"], construction["V"]
        MU = mat_mul(M, U)
        if all(int(MU[i][j]) == int(V[i][j]) for i in range(t) for j in range(t)):
            consistent_a.append(a)

    return {
        "seed_label": seed_label,
        "field": field.__name__,
        "p": field.P,
        "M_family": meta["family"],
        "field_elements_scanned": field.P - 1,
        "consistent_a_found": consistent_a,
        "immune": len(consistent_a) == 0,
    }
