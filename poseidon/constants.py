"""
Deterministic round constants for Poseidon1 (BN254, t=3).
Generated via a simple SHAKE-256 squeeze so they are reproducible.
"""

import hashlib
from .field import Fp, P


def _generate_constants(n: int, seed: bytes = b"poseidon1-bn254-t3") -> list:
    """Generate n field elements deterministically from seed."""
    shake = hashlib.shake_256(seed)
    digest = shake.digest(n * 40)  # 40 bytes >> 254 bits, enough for rejection
    constants = []
    offset = 0
    generated = 0
    while generated < n:
        chunk = int.from_bytes(digest[offset : offset + 32], "big")
        constants.append(Fp(chunk % P))
        offset += 32
        generated += 1
        if offset + 32 > len(digest):
            # Extend if needed (rare for small n)
            shake = hashlib.shake_256(seed + generated.to_bytes(4, "big"))
            digest = shake.digest((n - generated + 1) * 40)
            offset = 0
    return constants


def round_constants(t: int, r_f: int, r_p: int) -> list:
    """
    Return round constants as a flat list of t*(r_f + r_p) Fp elements.
    Indexed by round then coordinate.
    """
    total_rounds = r_f + r_p
    return _generate_constants(t * total_rounds)
