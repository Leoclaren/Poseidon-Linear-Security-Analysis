# BN254 scalar field (default) + a generic prime-field factory
#
# RESEARCH_PLAN.md Sec 6.3 "smaller native fields" lever: every field-aware
# module in this repo (linalg.py, polynomial.py, matrices.py, constants.py,
# matrix_search.py) used to import the module-level P directly, hardcoding
# BN254 everywhere. make_field() lets us build a field class bound to ANY
# prime; the other modules now derive the prime from the field CLASS of the
# data they're handed (type(x).P) instead of importing a global P, so they
# work unmodified for any field -- this module is the only one that needs
# to know about a specific prime by name.

def make_field(prime: int, name: str = "Fp"):
    """Build a field class F_prime, usable exactly like the original
    hardcoded Fp (same int-subclass, same operators), bound to `prime`."""

    class _Fp(int):
        P = prime

        def __new__(cls, value):
            return super().__new__(cls, int(value) % cls.P)

        def __add__(self, other):
            return self.__class__(int(self) + int(other))

        def __radd__(self, other):
            return self.__class__(int(other) + int(self))

        def __sub__(self, other):
            return self.__class__(int(self) - int(other))

        def __rsub__(self, other):
            return self.__class__(int(other) - int(self))

        def __mul__(self, other):
            return self.__class__(int(self) * int(other))

        def __rmul__(self, other):
            return self.__class__(int(other) * int(self))

        def __pow__(self, exp, mod=None):
            return self.__class__(pow(int(self), int(exp), self.P))

        def __neg__(self):
            return self.__class__(self.P - int(self))

        def __repr__(self):
            return f"{self.__class__.__name__}({int(self)})"

        def is_zero(self):
            return int(self) == 0

    _Fp.__name__ = name
    _Fp.__qualname__ = name
    return _Fp


# BN254 scalar field (p = 21888242871839275222246405745257275088548364400416034343698204186575808495617)
# -- kept as the default export so every pre-existing `from poseidon.field
# import Fp, P` call site is completely unaffected.
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617
Fp = make_field(P, "Fp")

# KoalaBear (p = 2^31 - 2^24 + 1), used by Vitto 2026/1579's concrete
# instance and the SoK 2026/1931's small-field benchmark set -- the
# standard "small field" reference point for RESEARCH_PLAN.md Sec 6.3.
P_KOALABEAR = 2130706433
FpKoalaBear = make_field(P_KOALABEAR, "FpKoalaBear")

# Goldilocks (p = 2^64 - 2^32 + 1), the SoK's 64-bit reference point.
P_GOLDILOCKS = 18446744069414584321
FpGoldilocks = make_field(P_GOLDILOCKS, "FpGoldilocks")
