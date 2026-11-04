"""
Polynomial arithmetic and factorization over F_p, for ANY prime p
(RESEARCH_PLAN.md Sec 6.3: no longer hardcoded to BN254 -- every function
infers the field from the Fp-typed coefficients it's handed, `type(x)`,
instead of importing a module-level P, so the same code runs unmodified
over KoalaBear, Goldilocks, etc.).

Implements squarefree reduction + Cantor-Zassenhaus factorization
(distinct-degree factorization followed by equal-degree splitting), used by
the Algorithm 1 invariant-subspace scanner to decompose the characteristic
polynomial of the restricted linear layer M_W into irreducible factors —
the "minimal polynomial decomposition" step of the paper's methodology.

Polynomials are represented as lists of Fp coefficients, lowest degree first.
"""

import random


def trim(poly):
    poly = list(poly)
    while len(poly) > 1 and int(poly[-1]) == 0:
        poly.pop()
    return poly


def deg(poly):
    poly = trim(poly)
    if len(poly) == 1 and int(poly[0]) == 0:
        return -1
    return len(poly) - 1


def is_zero(poly):
    return deg(poly) == -1


def poly_add(a, b):
    field = type(a[0]) if a else type(b[0])
    n = max(len(a), len(b))
    a = list(a) + [field(0)] * (n - len(a))
    b = list(b) + [field(0)] * (n - len(b))
    return trim([a[i] + b[i] for i in range(n)])


def poly_sub(a, b):
    field = type(a[0]) if a else type(b[0])
    n = max(len(a), len(b))
    a = list(a) + [field(0)] * (n - len(a))
    b = list(b) + [field(0)] * (n - len(b))
    return trim([a[i] - b[i] for i in range(n)])


def poly_mul(a, b):
    a, b = trim(a), trim(b)
    field = type(a[0])
    if is_zero(a) or is_zero(b):
        return [field(0)]
    res = [field(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if int(ai) == 0:
            continue
        for j, bj in enumerate(b):
            res[i + j] = res[i + j] + ai * bj
    return trim(res)


def poly_divmod(a, b):
    a, b = trim(a), trim(b)
    if is_zero(b):
        raise ZeroDivisionError("polynomial division by zero")
    field = type(b[-1])
    db = deg(b)
    inv_lead = field(pow(int(b[-1]), field.P - 2, field.P))
    rem = list(a)
    quotient = [field(0)] * max(deg(a) - db + 1, 1)
    while deg(rem) >= db and not is_zero(rem):
        shift = deg(rem) - db
        coef = rem[-1] * inv_lead
        quotient[shift] = coef
        for i, bc in enumerate(b):
            rem[shift + i] = rem[shift + i] - coef * bc
        rem = trim(rem)
    return trim(quotient), trim(rem)


def poly_mod(a, m):
    return poly_divmod(a, m)[1]


def poly_gcd(a, b):
    a, b = trim(a), trim(b)
    while not is_zero(b):
        _, r = poly_divmod(a, b)
        a, b = b, r
    if not is_zero(a):
        field = type(a[-1])
        inv = field(pow(int(a[-1]), field.P - 2, field.P))
        a = [c * inv for c in a]
    return trim(a)


def poly_pow(base, exponent):
    """base^exponent, unbounded degree (no modulus) — the symbolic S-box."""
    field = type(base[0])
    result = [field(1)]
    base = list(base)
    e = exponent
    while e > 0:
        if e & 1:
            result = poly_mul(result, base)
        base = poly_mul(base, base)
        e >>= 1
    return result


def poly_pow_mod(base, exponent, modulus):
    field = type(base[0]) if base else type(modulus[0])
    result = [field(1)]
    base = poly_mod(base, modulus)
    e = exponent
    while e > 0:
        if e & 1:
            result = poly_mod(poly_mul(result, base), modulus)
        base = poly_mod(poly_mul(base, base), modulus)
        e >>= 1
    return result


def derivative(poly):
    poly = trim(poly)
    field = type(poly[0])
    if deg(poly) <= 0:
        return [field(0)]
    return trim([poly[i] * field(i) for i in range(1, len(poly))])


def make_monic(poly):
    poly = trim(poly)
    if is_zero(poly):
        return poly
    field = type(poly[-1])
    inv = field(pow(int(poly[-1]), field.P - 2, field.P))
    return [c * inv for c in poly]


def squarefree_radical(poly):
    """
    rad(f) = f / gcd(f, f'), monic — divides out repeated roots.

    The identity matrix's characteristic polynomial (x-1)^(t-1) is the
    prototypical case: its radical is just (x-1), and feeding that single
    linear factor back into ker(f_i(M)) (evaluated at the ORIGINAL matrix,
    not the radical) still recovers the full invariant eigenspace.
    """
    poly = make_monic(poly)
    g = poly_gcd(poly, derivative(poly))
    if deg(g) <= 0:
        return poly
    radical, _ = poly_divmod(poly, g)
    return make_monic(radical)


def _random_poly(max_deg_exclusive, rng, field):
    coeffs = [field(rng.randrange(field.P)) for _ in range(max_deg_exclusive)]
    return trim(coeffs)


def distinct_degree_factorization(f):
    """
    Split a squarefree, monic polynomial f into (degree, h_d) pairs, where
    h_d is the product of all irreducible factors of f having degree d.
    """
    f = make_monic(f)
    field = type(f[0])
    n = deg(f)
    x = [field(0), field(1)]
    h = [field(0), field(1)]  # x^(p^0) = x
    remaining = f
    factors = []
    d = 0
    while deg(remaining) > 0 and d < n:
        d += 1
        h = poly_pow_mod(h, field.P, f)  # x^(p^d) mod f, built up cumulatively
        g = poly_gcd(poly_sub(h, x), remaining)
        if deg(g) > 0:
            factors.append((d, g))
            remaining, _ = poly_divmod(remaining, g)
    return factors


def equal_degree_factorization(g, d, rng=None):
    """
    Cantor-Zassenhaus random splitting: break g (a product of irreducible
    factors all of degree d) into the individual irreducible factors.
    """
    rng = rng or random.Random(0xC0FFEE)
    g = make_monic(g)
    field = type(g[0])
    exponent = (field.P ** d - 1) // 2

    def split(poly):
        poly = make_monic(poly)
        m = deg(poly)
        if m <= 0:
            return []
        if m == d:
            return [poly]
        while True:
            a = _random_poly(m, rng, field)
            if deg(a) <= 0:
                continue
            gcd1 = poly_gcd(a, poly)
            if 0 < deg(gcd1) < m:
                left, _ = poly_divmod(poly, gcd1)
                return split(gcd1) + split(left)
            b = poly_pow_mod(a, exponent, poly)
            b_minus_1 = poly_sub(b, [field(1)])
            gcd2 = poly_gcd(b_minus_1, poly)
            if 0 < deg(gcd2) < m:
                left, _ = poly_divmod(poly, gcd2)
                return split(gcd2) + split(left)
            # unlucky draw (probability <= 1/2) — retry with a new random a

    return split(g)


def factor_squarefree(f):
    """Full irreducible factorization of a squarefree, monic polynomial over F_p."""
    f = make_monic(f)
    if deg(f) <= 0:
        return []
    factors = []
    for d, g in distinct_degree_factorization(f):
        factors.extend(equal_degree_factorization(g, d))
    return factors
