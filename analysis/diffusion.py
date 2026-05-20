"""
Diffusion analysis for Poseidon1 partial rounds.

Diffusion coefficient D(r) = fraction of coordinates that are non-zero
in the difference after r rounds, given an initial difference Delta.
"""

from poseidon.field import Fp
from poseidon.permutation import PoseidonPermutation
from poseidon.matrices import MATRIX_NAMES


def diffusion_coefficient(state_diff: list) -> float:
    """Fraction of non-zero coordinates in the difference vector."""
    t = len(state_diff)
    nonzero = sum(1 for x in state_diff if int(x) != 0)
    return nonzero / t


def track_diffusion(
    matrix_name: str,
    t: int = 3,
    r_p: int = 6,
    alpha: int = 5,
    delta_coord: int = -1,
    delta_val: int = 4,
) -> list:
    """
    Track diffusion D(r) over r_p partial rounds for a given matrix.

    Parameters
    ----------
    matrix_name : matrix to use for partial rounds
    t           : state width
    r_p         : number of partial rounds
    alpha       : S-box exponent
    delta_coord : index of the coordinate carrying the initial difference (-1 = last)
    delta_val   : magnitude of the initial difference

    Returns
    -------
    List of (round, D(r)) pairs, length r_p+1
    """
    perm = PoseidonPermutation(t=t, r_f=0, r_p=r_p, alpha=alpha, matrix=matrix_name)

    # Build two inputs differing only in delta_coord
    base = [Fp(i + 1) for i in range(t)]
    perturbed = list(base)
    coord = delta_coord % t
    perturbed[coord] = Fp(int(base[coord]) + delta_val)

    _, trace_base = perm.permute_partial_only(base, trace=True)
    _, trace_pert = perm.permute_partial_only(perturbed, trace=True)

    diffusion = []
    for r, (s_base, s_pert) in enumerate(zip(trace_base, trace_pert)):
        diff = [Fp(int(s_pert[i]) - int(s_base[i])) for i in range(t)]
        diffusion.append((r, diffusion_coefficient(diff)))

    return diffusion


def compare_matrices(
    matrices: list = None,
    t: int = 3,
    r_p: int = 6,
    alpha: int = 5,
    delta_coord: int = -1,
    delta_val: int = 4,
) -> dict:
    """
    Compare diffusion across multiple matrices.

    Returns
    -------
    dict mapping matrix_name -> list of (round, D(r))
    """
    if matrices is None:
        matrices = list(MATRIX_NAMES.keys())

    return {
        name: track_diffusion(
            name, t=t, r_p=r_p, alpha=alpha,
            delta_coord=delta_coord, delta_val=delta_val,
        )
        for name in matrices
    }
