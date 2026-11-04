"""
Deterministic round constants for Poseidon1 (default: BN254, t=3; any
field via `field=`, RESEARCH_PLAN.md Sec 6.3).
Generated via a simple SHAKE-256 squeeze so they are reproducible.
"""

import hashlib
from .field import Fp


def _generate_constants(n: int, seed: bytes = b"poseidon1-bn254-t3", field=Fp) -> list:
    """Generate n field elements deterministically from seed."""
    shake = hashlib.shake_256(seed)
    digest = shake.digest(n * 40)  # 40 bytes >> any field size used here, enough for rejection
    constants = []
    offset = 0
    generated = 0
    while generated < n:
        chunk = int.from_bytes(digest[offset : offset + 32], "big")
        constants.append(field(chunk % field.P))
        offset += 32
        generated += 1
        if offset + 32 > len(digest):
            # Extend if needed (rare for small n)
            shake = hashlib.shake_256(seed + generated.to_bytes(4, "big"))
            digest = shake.digest((n - generated + 1) * 40)
            offset = 0
    return constants


def round_constants(t: int, r_f: int, r_p: int, field=Fp) -> list:
    """
    Return round constants as a flat list of t*(r_f + r_p) field elements.
    Indexed by round then coordinate.
    """
    total_rounds = r_f + r_p
    if field is Fp:
        seed = b"poseidon1-bn254-t3"  # unchanged, byte-for-byte backward compatible
    else:
        seed = f"poseidon1-{field.__name__}-t{t}".encode()
    return _generate_constants(t * total_rounds, seed=seed, field=field)
