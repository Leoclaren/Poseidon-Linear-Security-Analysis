"""
Differential Distinguisher for Poseidon1 partial rounds.

For a non-MDS partial-round matrix, any difference Δ ∈ V produces a
100% deterministic output difference regardless of the actual input.
This is a catastrophic failure of differential security:
  - uniform random cipher: each (Δ_in, Δ_out) pair has probability ~1/p
  - non-MDS Poseidon1 partial rounds: probability = 1 for the predicted Δ_out

This module:
  1. Measures output difference bias across many input pairs (fixed Δ_in)
  2. Runs a chosen-difference attack showing the attacker can predict Δ_out
  3. Compares differential probability tables: non-MDS vs MDS
"""

import random
from poseidon.field import Fp, P
from poseidon.matrices import matrix_mul, MATRIX_NAMES
from poseidon.permutation import PoseidonPermutation
from attacks.linear_collapse import matrix_pow


class DifferentialDistinguisher:
    """
    Measures and exploits differential predictability in Poseidon1 partial rounds.
    """

    def __init__(self, t: int = 3, r_p: int = 6, alpha: int = 5, matrix: str = "identity"):
        self.t = t
        self.r_p = r_p
        self.alpha = alpha
        self.matrix_name = matrix
        self.M = MATRIX_NAMES[matrix]
        self.perm = PoseidonPermutation(t=t, r_f=0, r_p=r_p, alpha=alpha, matrix=matrix)
        self.rng = random.Random(1337)

    def _random_input(self):
        return [Fp(self.rng.randint(1, P - 1)) for _ in range(self.t)]

    def _output_diff(self, base, delta):
        perturbed = [Fp(int(base[i]) + int(delta[i])) for i in range(self.t)]
        out_a = self.perm.permute_partial_only(base)
        out_b = self.perm.permute_partial_only(perturbed)
        return tuple(int(Fp(int(out_b[i]) - int(out_a[i]))) for i in range(self.t))

    def _linear_predict(self, delta: list) -> tuple:
        """Predict output diff purely via M^r_p · delta (no permutation call)."""
        Mr = matrix_pow(self.M, self.r_p)
        predicted = matrix_mul(Mr, delta)
        return tuple(int(x) for x in predicted)

    def measure_bias(self, delta_val: int = 4, n_samples: int = 50) -> dict:
        """
        For n_samples random inputs A, compute output diff with Δ=(0,…,0,delta_val).
        Count unique output differences — ideal cipher: n_samples unique; non-MDS: 1 unique.
        """
        delta = [Fp(0)] * (self.t - 1) + [Fp(delta_val)]
        predicted = self._linear_predict(delta)

        output_diffs = []
        for _ in range(n_samples):
            base = self._random_input()
            diff = self._output_diff(base, delta)
            output_diffs.append(diff)

        unique = set(output_diffs)
        all_match_prediction = all(d == predicted for d in output_diffs)

        return {
            "matrix": self.matrix_name,
            "delta_val": delta_val,
            "n_samples": n_samples,
            "unique_output_diffs": len(unique),
            "fully_predictable": len(unique) == 1 and all_match_prediction,
            "predicted_diff": predicted,
            "sample_diffs": [list(d) for d in output_diffs[:5]],  # first 5 for display
        }

    def chosen_difference_attack(self, delta_val: int = 4, n_pairs: int = 10) -> dict:
        """
        Full chosen-difference attack:
          1. Attacker picks Δ = (0, …, 0, delta_val) ∈ V
          2. Predicts output diff via M^r_p · Δ (no oracle)
          3. Verifies against actual permutation outputs
        """
        delta = [Fp(0)] * (self.t - 1) + [Fp(delta_val)]
        predicted = self._linear_predict(delta)

        pairs = []
        correct_count = 0
        for i in range(n_pairs):
            base = self._random_input()
            actual = self._output_diff(base, delta)
            correct = actual == predicted
            if correct:
                correct_count += 1
            pairs.append({
                "idx": i,
                "input_a": [int(x) for x in base],
                "predicted": list(predicted),
                "actual": list(actual),
                "correct": correct,
            })

        return {
            "matrix": self.matrix_name,
            "delta_val": delta_val,
            "predicted_diff": list(predicted),
            "n_pairs": n_pairs,
            "correct_count": correct_count,
            "success_rate": correct_count / n_pairs,
            "pairs": pairs,
        }

    def differential_probability_table(self, deltas: list = None) -> dict:
        """
        For a list of input differences, compute output differences and
        show whether each is fixed (non-MDS) or varies (MDS/secure).

        deltas: list of (coord, value) pairs — e.g. [(-1, 4), (0, 1), (1, 3)]
        """
        if deltas is None:
            deltas = [(-1, 1), (-1, 4), (-1, 100), (0, 1), (1, 7)]

        table = []
        for (coord, val) in deltas:
            delta = [Fp(0)] * self.t
            delta[coord % self.t] = Fp(val)

            # Collect output diffs from 10 random inputs
            diffs_seen = set()
            for _ in range(10):
                base = self._random_input()
                d = self._output_diff(base, delta)
                diffs_seen.add(d)

            predicted = self._linear_predict(delta)
            table.append({
                "delta_in": [int(x) for x in delta],
                "unique_out_diffs": len(diffs_seen),
                "is_deterministic": len(diffs_seen) == 1,
                "linear_prediction": list(predicted),
                "coord0_in_delta": int(delta[0]) != 0,
            })

        return {
            "matrix": self.matrix_name,
            "table": table,
        }
