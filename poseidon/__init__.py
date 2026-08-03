from .field import Fp
# Backwards-compatible exports: the codebase expects MDS_MATRIX and IDENTITY_MATRIX
from .matrices import (
    MDS_MATRIX_T3,
    identity_matrix,
    matrix_mul,
    branch_number,
    MATRIX_NAMES,
    get_matrix,
)

MDS_MATRIX = MDS_MATRIX_T3
IDENTITY_MATRIX = identity_matrix(3)

# Re-export commonly-used helpers
__all__ = [
    "Fp",
    "MDS_MATRIX",
    "IDENTITY_MATRIX",
    "matrix_mul",
    "branch_number",
    "MATRIX_NAMES",
    "get_matrix",
]

from .permutation import PoseidonPermutation
from .constants import round_constants

# Add permutation and constants to __all__ as well
__all__.extend(["PoseidonPermutation", "round_constants"])
