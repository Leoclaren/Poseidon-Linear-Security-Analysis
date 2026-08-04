"""
Poseidon1 permutation over BN254.

Round structure:
  Full round:    S-box on ALL coordinates → add constants → linear layer
  Partial round: S-box on coordinate 0 ONLY → add constants → linear layer
"""

from .field import Fp
from .matrices import matrix_mul, get_matrix, identity_matrix
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

        # full_matrix: try to get an MDS matrix of the appropriate size when needed
        if full_matrix is not None:
            self.full_matrix = full_matrix
        else:
            try:
                # Always ask the matrix module for an 'mds' matrix of size t.
                # For t==3 this returns the fixed example; for larger t it runs
                # the finder (randomized search) and returns a suitable matrix.
                self.full_matrix = get_matrix('mds', t)
            except Exception:
                # fallback to identity of size t to avoid size mismatches
                self.full_matrix = identity_matrix(t)

        # partial_matrix: obtain a t x t matrix for the given name
        if partial_matrix is not None:
            self.partial_matrix = partial_matrix
        else:
            try:
                self.partial_matrix = get_matrix(matrix, t)
            except Exception:
                # Backwards-compatibility: allow passing an explicit matrix object
                if isinstance(matrix, list):
                    self.partial_matrix = matrix
                else:
                    raise ValueError(
                        f"Unknown matrix: {matrix}. Choose from 'mds','identity','circulant','poseidon2' or provide a t-sized matrix"
                    )

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
