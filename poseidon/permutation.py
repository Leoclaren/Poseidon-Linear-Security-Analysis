"""
Poseidon1 permutation over BN254.

Round structure:
  Full round:    S-box on ALL coordinates → add constants → linear layer
  Partial round: S-box on coordinate 0 ONLY → add constants → linear layer
"""

from .field import Fp
from .matrices import matrix_mul, MATRIX_NAMES, MDS_MATRIX
from .constants import round_constants


class PoseidonPermutation:
    """
    Poseidon1 permutation.

    Parameters
    ----------
    t    : state width (default 3)
    r_f  : number of full rounds (default 8)
    r_p  : number of partial rounds (default 57 for t=3, BN254)
    alpha: S-box exponent (default 5 for BN254)
    matrix: 'mds' | 'identity' | 'circulant'  — linear layer for partial rounds
    mds_matrix: override the full-round matrix (default MDS_MATRIX)
    """

    def __init__(
        self,
        t: int = 3,
        r_f: int = 8,
        r_p: int = 57,
        alpha: int = 5,
        matrix: str = "mds",
        partial_matrix=None,
        full_matrix=None,
    ):
        self.t = t
        self.r_f = r_f
        self.r_p = r_p
        self.alpha = alpha

        self.full_matrix = full_matrix if full_matrix is not None else MDS_MATRIX
        if partial_matrix is not None:
            self.partial_matrix = partial_matrix
        elif matrix in MATRIX_NAMES:
            self.partial_matrix = MATRIX_NAMES[matrix]
        else:
            raise ValueError(f"Unknown matrix: {matrix}. Choose from {list(MATRIX_NAMES)}")

        self.matrix_name = matrix
        self.constants = round_constants(t, r_f, r_p)

    def _get_constants(self, round_idx: int):
        base = round_idx * self.t
        return self.constants[base : base + self.t]

    def _sbox_full(self, state):
        return [x**self.alpha for x in state]

    def _sbox_partial(self, state):
        return [state[0] ** self.alpha] + list(state[1:])

    def _add_constants(self, state, round_idx):
        c = self._get_constants(round_idx)
        return [state[i] + c[i] for i in range(self.t)]

    def permute(self, state: list, trace: bool = False) -> list:
        """
        Apply the full Poseidon1 permutation.

        Parameters
        ----------
        state : list of t Fp elements
        trace : if True, return (output, round_states) for debugging

        Returns
        -------
        list of t Fp elements (or tuple if trace=True)
        """
        state = [Fp(x) for x in state]
        half_f = self.r_f // 2
        total = self.r_f + self.r_p
        round_states = [list(state)] if trace else None

        for r in range(total):
            if r < half_f or r >= half_f + self.r_p:
                # Full round
                state = self._sbox_full(state)
                state = self._add_constants(state, r)
                state = matrix_mul(self.full_matrix, state)
            else:
                # Partial round
                state = self._sbox_partial(state)
                state = self._add_constants(state, r)
                state = matrix_mul(self.partial_matrix, state)

            if trace:
                round_states.append(list(state))

        if trace:
            return state, round_states
        return state

    def permute_partial_only(self, state: list, trace: bool = False) -> list:
        """
        Apply ONLY the partial rounds (no full rounds).
        Useful for isolating the attack surface.
        """
        state = [Fp(x) for x in state]
        round_states = [list(state)] if trace else None

        for r in range(self.r_p):
            state = self._sbox_partial(state)
            state = self._add_constants(state, r)
            state = matrix_mul(self.partial_matrix, state)
            if trace:
                round_states.append(list(state))

        if trace:
            return state, round_states
        return state
