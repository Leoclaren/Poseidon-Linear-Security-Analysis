"""
Statistical overview: branch numbers, diffusion, attack vulnerability summary.
"""

from poseidon.matrices import MATRIX_NAMES, branch_number
from poseidon.permutation import PoseidonPermutation
from poseidon.field import Fp
from .diffusion import track_diffusion


def compute_stats(t: int = 3, r_p: int = 6, alpha: int = 5, delta_val: int = 4) -> dict:
    """
    Compute a summary statistics dict for all known matrices.

    Returns
    -------
    dict mapping matrix_name -> {
        branch_number, is_mds, rounds_to_full_diffusion,
        final_diffusion, vulnerable
    }
    """
    stats = {}
    for name, M in MATRIX_NAMES.items():
        bn = branch_number(M)
        is_mds = bn >= t + 1

        diffusion_trace = track_diffusion(
            name, t=t, r_p=r_p, alpha=alpha,
            delta_coord=-1, delta_val=delta_val,
        )

        # Round at which diffusion first reaches 1.0
        rounds_to_full = None
        for r, d in diffusion_trace:
            if d >= 1.0:
                rounds_to_full = r
                break

        final_d = diffusion_trace[-1][1]

        stats[name] = {
            "branch_number": bn,
            "is_mds": is_mds,
            "rounds_to_full_diffusion": rounds_to_full,
            "final_diffusion": final_d,
            "vulnerable": not is_mds,
        }

    return stats
