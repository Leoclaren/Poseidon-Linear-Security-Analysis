"""
Zero-Sum Distinguisher for Poseidon1 partial rounds.

For a non-MDS matrix with invariant subspace V, consider a coset:
  C = { A + v | v ∈ S }   where S ⊆ V is a finite set of differences.

Because the partial rounds are linear on V, the sum of outputs over C
has a predictable structure. Specifically, for the invariant subspace
V = {(0,0,x)}, coordinate 0 of the output sum depends only on coord-0
of the inputs — which are all identical in C — making the sum testable.

For a truly random permutation, this sum is uniform over F_p.
For non-MDS Poseidon1, it is deterministic and computable without oracle calls.
"""

from poseidon.field import Fp, P
from poseidon.matrices import matrix_mul, MATRIX_NAMES
from poseidon.permutation import PoseidonPermutation
from attacks.linear_collapse import matrix_pow


class ZeroSumDistinguisher:
    """
    Zero-sum distinguisher exploiting the invariant subspace of non-MDS matrices.
    """

    def __init__(
        self,
        t: int = 3,
        r_p: int = 6,
        alpha: int = 5,
        matrix: str = "identity",
        r_f: int = 0,
    ):
        self.t = t
        self.r_p = r_p
        self.r_f = r_f
        self.alpha = alpha
        self.matrix_name = matrix
        self.M = MATRIX_NAMES[matrix]
        self.perm = PoseidonPermutation(t=t, r_f=r_f, r_p=r_p, alpha=alpha, matrix=matrix)

    def _run_perm(self, state):
        if self.r_f == 0:
            return self.perm.permute_partial_only(state)
        return self.perm.permute(state)

    def check_coset_sum(self, base: list, coset_size: int = 8) -> dict:
        """
        Compute the sum of permutation outputs over a coset of V:
          { base + (0, 0, k*δ) | k = 0, 1, ..., coset_size-1 }

        For non-MDS: coord-0 of each output is identical (invariant subspace).
        For MDS:     coord-0 varies — sum is pseudo-random.
        """
        delta_base = 7  # step size
        outputs = []
        for k in range(coset_size):
            pt = list(base)
            pt[-1] = Fp(int(base[-1]) + k * delta_base)
            out = self._run_perm(pt)
            outputs.append(out)

        coord0_vals = [int(o[0]) for o in outputs]
        coord0_sum  = sum(coord0_vals) % P
        all_coord0_equal = len(set(coord0_vals)) == 1

        # For MDS, compute sum: should be diverse
        coord0_sum_mod = coord0_sum % (2**32)  # display-friendly

        return {
            "matrix": self.matrix_name,
            "r_f": self.r_f,
            "r_p": self.r_p,
            "coset_size": coset_size,
            "coord0_values": coord0_vals,
            "all_coord0_equal": all_coord0_equal,
            "sum_coord0": coord0_sum,
            "sum_coord0_zero": coord0_sum == 0,
            "sum_coord0_mod2_32": coord0_sum_mod,
        }

    def predict_coset_sum(self, base: list, coset_size: int = 8) -> dict:
        """
        Predict the coord-0 output sum WITHOUT calling the permutation.
        Only valid when coord-0 is invariant (non-MDS case).
        """
        Mr = matrix_pow(self.M, self.r_p)

        # For each coset element, predict via M^r_p
        delta_base = 7
        predicted_coord0 = []
        for k in range(coset_size):
            # Initial difference from base: (0, 0, k*delta_base)
            diff = [Fp(0)] * (self.t - 1) + [Fp(k * delta_base)]
            # M^r_p maps (0,0,x) -> (0,0,x) for identity, so output coord0 is same as base coord0
            out_diff = matrix_mul(Mr, diff)
            predicted_coord0.append(int(out_diff[0]))

        # Actual base output coord-0 (need one oracle call)
        base_out = self._run_perm(base)
        base_c0 = int(base_out[0])

        total_predicted = sum(base_c0 + c for c in predicted_coord0) % P
        return {
            "base_coord0_out": base_c0,
            "predicted_contributions": predicted_coord0,
            "predicted_total_coord0": total_predicted,
        }

    def run_distinguisher(self, n_trials: int = 5) -> dict:
        """
        Run the zero-sum distinguisher n_trials times with random bases.
        For non-MDS: coord-0 values are all equal across coset → trivially distinguishable.
        For MDS: coord-0 values are diverse → indistinguishable from random.
        """
        import random
        rng = random.Random(777)
        trials = []

        for i in range(n_trials):
            base = [Fp(rng.randint(1, P - 1)) for _ in range(self.t)]
            r = self.check_coset_sum(base, coset_size=6)
            trials.append({
                "trial": i,
                "all_coord0_equal": r["all_coord0_equal"],
                "unique_coord0_values": len(set(r["coord0_values"])),
            })

        all_trivial = all(t["all_coord0_equal"] for t in trials)
        return {
            "matrix": self.matrix_name,
            "n_trials": n_trials,
            "all_trials_trivially_distinguishable": all_trivial,
            "trials": trials,
        }
