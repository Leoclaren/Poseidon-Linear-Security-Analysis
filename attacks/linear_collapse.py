"""
Linear Collapse Attack on Poseidon1 partial rounds.

When the input difference Δ lies in an invariant subspace V of M,
the full sequence of R_p partial rounds reduces to a single linear map:
  Δ_out = M^R_p · Δ_in

This module:
  1. Computes M^r explicitly (matrix power mod p)
  2. Verifies that partial round traces match M^r · Δ for any Δ ∈ V
  3. Tracks how the effective map evolves as r increases
"""

from poseidon.field import Fp, P
from poseidon.matrices import matrix_mul, MATRIX_NAMES
from poseidon.permutation import PoseidonPermutation


def matrix_pow(M: list, r: int) -> list:
    """Compute M^r over F_p via repeated squaring."""
    t = len(M)
    # Identity matrix
    result = [[Fp(1) if i == j else Fp(0) for j in range(t)] for i in range(t)]
    base = [list(row) for row in M]
    while r > 0:
        if r % 2 == 1:
            result = mat_mul_mat(result, base, t)
        base = mat_mul_mat(base, base, t)
        r //= 2
    return result


def mat_mul_mat(A: list, B: list, t: int) -> list:
    """Multiply two t×t matrices over F_p."""
    return [
        [sum(A[i][k] * B[k][j] for k in range(t)) for j in range(t)]
        for i in range(t)
    ]


class LinearCollapseAttack:
    """
    Demonstrates that R_p partial rounds = M^R_p on the invariant subspace.

    The attacker does NOT need to evaluate the permutation at all —
    just multiply by M^R_p once.
    """

    def __init__(self, t: int = 3, r_p: int = 6, alpha: int = 5, matrix: str = "identity"):
        self.t = t
        self.r_p = r_p
        self.alpha = alpha
        self.matrix_name = matrix
        self.M = MATRIX_NAMES[matrix]
        self.perm = PoseidonPermutation(t=t, r_f=0, r_p=r_p, alpha=alpha, matrix=matrix)
        self.M_power = matrix_pow(self.M, r_p)

    def apply_power(self, delta: list) -> list:
        """Apply M^r_p to a difference vector."""
        return matrix_mul(self.M_power, delta)

    def verify_collapse(self, delta_val: int = 4, n_samples: int = 5) -> dict:
        """
        For n_samples random inputs A, verify that:
          permute(A + Δ) - permute(A) == M^r_p · Δ
        where Δ = (0, …, 0, delta_val) ∈ V.
        """
        import random
        delta = [Fp(0)] * (self.t - 1) + [Fp(delta_val)]
        predicted = self.apply_power(delta)

        samples = []
        rng = random.Random(42)

        for i in range(n_samples):
            base_input = [Fp(rng.randint(1, P - 1)) for _ in range(self.t)]
            perturbed   = list(base_input)
            perturbed[-1] = Fp(int(base_input[-1]) + delta_val)

            out_a = self.perm.permute_partial_only(base_input)
            out_b = self.perm.permute_partial_only(perturbed)
            actual_diff = [Fp(int(out_b[j]) - int(out_a[j])) for j in range(self.t)]

            correct = all(int(actual_diff[j]) == int(predicted[j]) for j in range(self.t))
            samples.append({
                "idx": i,
                "input": [int(x) for x in base_input],
                "actual_diff": [int(x) for x in actual_diff],
                "predicted_diff": [int(x) for x in predicted],
                "correct": correct,
            })

        all_correct = all(s["correct"] for s in samples)
        return {
            "matrix": self.matrix_name,
            "r_p": self.r_p,
            "delta_val": delta_val,
            "predicted_diff": [int(x) for x in predicted],
            "n_samples": n_samples,
            "all_correct": all_correct,
            "map_computed": True,
            "effective_map_row0": [int(x) for x in self.M_power[0]],
            "samples": samples,
        }

    def track_map_power(self, max_r: int = 10) -> dict:
        """
        Compute M^r for r = 1..max_r and track whether M^r[0][*] has any
        nonzero entry in the last column (coord-0 would activate for Δ=(0,0,x)).
        """
        results = {}
        for r in range(1, max_r + 1):
            Mr = matrix_pow(self.M, r)
            # Apply to (0,0,1)
            test = [Fp(0)] * (self.t - 1) + [Fp(1)]
            out = matrix_mul(Mr, test)
            coord0_zero = int(out[0]) == 0
            results[r] = {
                "Mr_row0": [int(x) for x in Mr[0]],
                "image_of_e_last": [int(x) for x in out],
                "coord0_zero": coord0_zero,
            }
        return results

    def show_effective_map(self) -> list:
        """Return M^r_p as a human-readable list of lists of ints."""
        return [[int(x) for x in row] for row in self.M_power]
