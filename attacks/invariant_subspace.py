"""
Invariant Subspace Trail Attack on Poseidon1 partial rounds.

When the partial-round matrix M is non-MDS, the subspace
  V = { (0, 0, x) | x in F_p }
is invariant under every partial round, meaning any difference
Delta = (0, 0, delta) never activates the S-box. The R_p partial
rounds then collapse to a purely linear map — no nonlinear security.
"""

from poseidon.field import Fp
from poseidon.permutation import PoseidonPermutation
from poseidon.matrices import matrix_mul, weight, branch_number, get_matrix


class InvariantSubspaceAttack:
    """
    Demonstrates the invariant subspace trail on Poseidon1 partial rounds.

    An attacker who knows that Delta = (0, 0, delta) at input can predict
    the full output difference through all R_p partial rounds without knowing
    any constants or the key — because no nonlinearity is ever engaged.
    """

    def __init__(self, t: int = 3, r_p: int = 6, alpha: int = 5, matrix: str = "identity"):
        self.t = t
        self.r_p = r_p
        self.alpha = alpha
        self.matrix_name = matrix
        self.M = get_matrix(matrix, t)
        self.perm = PoseidonPermutation(t=t, r_f=0, r_p=r_p, alpha=alpha, matrix=matrix)

    def check_invariant_subspace(self, delta_val: int = 4) -> dict:
        """
        Check whether V = {(0,0,x)} is invariant under self.M.
        Returns dict with per-round difference and whether coord-0 was ever activated.
        """
        delta = [Fp(0)] * (self.t - 1) + [Fp(delta_val)]
        results = []
        coord0_activations = 0

        current = list(delta)
        for r in range(self.r_p):
            results.append({
                "round": r,
                "diff_in": [int(x) for x in current],
                "coord0_nonzero": int(current[0]) != 0,
            })
            if int(current[0]) != 0:
                coord0_activations += 1
            # Apply linear layer only (constants don't affect differences)
            current = matrix_mul(self.M, current)

        results.append({
            "round": self.r_p,
            "diff_in": [int(x) for x in current],
            "coord0_nonzero": int(current[0]) != 0,
        })
        if int(current[0]) != 0:
            coord0_activations += 1

        return {
            "matrix": self.matrix_name,
            "branch_number": branch_number(self.M),
            "is_mds": branch_number(self.M) >= self.t + 1,
            "invariant_subspace_holds": coord0_activations == 0,
            "coord0_activations": coord0_activations,
            "per_round": results,
        }

    def attack_predict_output_diff(self, input_a: list, delta_val: int = 4) -> dict:
        """
        Given input A and difference delta = (0,0,delta_val), show that:
        - B = A + delta gives a predictable output difference
        - The difference is computed WITHOUT evaluating the permutation
          (purely via linear prediction)

        Returns both actual and linearly-predicted output differences.
        """
        input_b = list(input_a)
        input_b[-1] = Fp(int(input_a[-1]) + delta_val)

        # Actual permutation outputs
        out_a = self.perm.permute_partial_only(input_a)
        out_b = self.perm.permute_partial_only(input_b)
        actual_diff = [Fp(int(out_b[i]) - int(out_a[i])) for i in range(self.t)]

        # Linear prediction: apply M^r_p to (0, 0, delta_val)
        predicted = [Fp(0)] * (self.t - 1) + [Fp(delta_val)]
        for _ in range(self.r_p):
            predicted = matrix_mul(self.M, predicted)

        correct = all(int(actual_diff[i]) == int(predicted[i]) for i in range(self.t))

        return {
            "input_a": [int(x) for x in input_a],
            "input_b": [int(input_b[i]) for i in range(self.t)],
            "actual_output_diff": [int(x) for x in actual_diff],
            "predicted_output_diff": [int(x) for x in predicted],
            "prediction_correct": correct,
        }


def run_attack_demo(t: int = 3, r_p: int = 6, alpha: int = 5, delta_val: int = 4, verbose: bool = True) -> dict:
    """
    Run the invariant subspace attack demo comparing MDS vs non-MDS matrices.
    Returns a results dict suitable for analysis/plotting.
    """
    results = {}

    for name in ["mds", "identity", "circulant"]:
        atk = InvariantSubspaceAttack(t=t, r_p=r_p, alpha=alpha, matrix=name)
        subspace_result = atk.check_invariant_subspace(delta_val=delta_val)

        input_a = [Fp(i + 1) for i in range(t)]
        prediction_result = atk.attack_predict_output_diff(input_a, delta_val=delta_val)

        results[name] = {
            "subspace": subspace_result,
            "prediction": prediction_result,
        }

        if verbose:
            print(f"\n{'='*60}")
            print(f"Matrix: {name.upper()}")
            print(f"  Branch number : {subspace_result['branch_number']}")
            print(f"  Is MDS        : {subspace_result['is_mds']}")
            print(f"  Invariant V   : {subspace_result['invariant_subspace_holds']}")
            print(f"  Coord-0 activations across {r_p} rounds: {subspace_result['coord0_activations']}")
            print(f"  Prediction correct: {prediction_result['prediction_correct']}")
            if not subspace_result["is_mds"]:
                print(f"  [VULNERABLE] Output diff predictable without evaluating permutation!")
            else:
                print(f"  [SECURE] MDS diffusion breaks invariant subspace.")

    return results
