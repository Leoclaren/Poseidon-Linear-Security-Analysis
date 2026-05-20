# BN254 scalar field
# p = 21888242871839275222246405745257275088548364400416034343698204186575808495617

P = 21888242871839275222246405745257275088548364400416034343698204186575808495617


class Fp(int):
    """Element of F_p (BN254 scalar field). Arithmetic is always mod p."""

    def __new__(cls, value):
        return super().__new__(cls, int(value) % P)

    def __add__(self, other):
        return Fp(int(self) + int(other))

    def __radd__(self, other):
        return Fp(int(other) + int(self))

    def __sub__(self, other):
        return Fp(int(self) - int(other))

    def __rsub__(self, other):
        return Fp(int(other) - int(self))

    def __mul__(self, other):
        return Fp(int(self) * int(other))

    def __rmul__(self, other):
        return Fp(int(other) * int(self))

    def __pow__(self, exp, mod=None):
        return Fp(pow(int(self), int(exp), P))

    def __neg__(self):
        return Fp(P - int(self))

    def __repr__(self):
        return f"Fp({int(self)})"

    def is_zero(self):
        return int(self) == 0
