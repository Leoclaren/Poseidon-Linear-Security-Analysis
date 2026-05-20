# Simplifying the linear layer in partial rounds
"""
Poseidon1 Cryptanalytic Verification Engine
Optimized for BN254 Scalar Field Modulus:
r = 21888242871839275222246405745257275088548364400416034343698204186575808495617
(0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001)

This engine implements the automated subspace trail discovery and differential
avalanche tracking formulated in the Methodology.
"""

import math

# BN254 Curve Scalar Field Modulus (r)
BN254_PRIME = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001

class FiniteField:
    """Implements basic arithmetic over the cryptographic prime field F_p."""
    def __init__(self, p=BN254_PRIME):
        self.p = p

    def add(self, a, b): return (a + b) % self.p
    def sub(self, a, b): return (a - b) % self.p
    def mul(self, a, b): return (a * b) % self.p
    def exp(self, base, exp): return pow(base, exp, self.p)

    def invert(self, a):
        if a == 0: raise ZeroDivisionError("Cannot invert zero over F_p.")
        return pow(a, self.p - 2, self.p)

class PoseidonPermutation:
    """Simulates intermediate state transitions of Poseidon1 partial rounds."""
    def __init__(self, width, alpha, matrix, constants, field):
        self.t = width
        self.alpha = alpha
        self.matrix = matrix          # Expected 2D list [t][t]
        self.constants = constants    # Expected 2D list [num_rounds][t]
        self.field = field

    def apply_partial_sbox(self, state):
        """Executes the non-linear transformation restricted strictly to coordinate 0."""
        res = list(state)
        res[0] = self.field.exp(res[0], self.alpha)
        # Coordinates 1 to t-1 act as identity transformations
        return res

    def inject_constants(self, state, round_idx):
        """Applies affine translation via the round constant vector."""
        return [self.field.add(state[i], self.constants[round_idx][i]) for i in range(self.t)]

    def apply_linear_layer(self, state):
        """Multiplies the linear layer matrix by the internal state vector."""
        new_state = [0] * self.t
        for i in range(self.t):
            s = 0
            for j in range(self.t):
                prod = self.field.mul(self.matrix[i][j], state[j])
                s = self.field.add(s, prod)
            new_state[i] = s
        return new_state

    def transition_partial_round(self, state, round_idx):
        """Executes a single structural step inside the partial round sequence."""
        sbox_out = self.apply_partial_sbox(state)
        const_out = self.inject_constants(sbox_out, round_idx)
        return self.apply_linear_layer(const_out)

class CryptanalyticTracker:
    """Tracks avalanche propagation dynamics and quantifies structural leakage coefficients."""
    def __init__(self, permutation):
        self.perm = permutation
        self.field = permutation.field

    def calculate_diffusion_coefficient(self, diff_vector):
        """Computes the generalized Hamming weight mapping active differences over F_p."""
        return sum(1 for x in diff_vector if x != 0)

    def execute_differential_tracking(self, base_state, input_diff, total_rounds):
        """Traces the structural divergence between two parallel evaluation tracks."""
        state_a = list(base_state)
        state_b = [self.field.add(base_state[i], input_diff[i]) for i in range(self.perm.t)]

        history = []

        # Initial tracking prior to round execution
        init_diff = [self.field.sub(state_b[i], state_a[i]) for i in range(self.perm.t)]
        history.append({
            "round": 0,
            "diff_vector": init_diff,
            "diffusion_coeff": self.calculate_diffusion_coefficient(init_diff)
        })

        for r in range(total_rounds):
            state_a = self.perm.transition_partial_round(state_a, r)
            state_b = self.perm.transition_partial_round(state_b, r)

            current_diff = [self.field.sub(state_b[i], state_a[i]) for i in range(self.perm.t)]
            coeff = self.calculate_diffusion_coefficient(current_diff)

            history.append({
                "round": r + 1,
                "diff_vector": current_diff,
                "diffusion_coeff": coeff
            })

        return history

def demonstrate_vulnerability_paradigms():
    """Generates the underlying data matrices for the security analysis comparison."""
    ff = FiniteField()
    width = 3
    alpha = 5
    num_rounds = 5

    # Mocking round constants for testing (non-zero entries)
    mock_constants = [[100 * (r+1) + i for i in range(width)] for r in range(num_rounds)]

    # 1. Naive Non-MDS Paradigm (Identity Matrix Layer - Severe Subspace Isolation)
    identity_matrix = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ]

    # 2. Secure Benchmark Paradigm (Dense MDS Matrix Layer)
    mds_matrix = [
        [2, 3, 5],
        [7, 11, 13],
        [17, 19, 23]
    ]

    # Initialize environments
    perm_naive = PoseidonPermutation(width, alpha, identity_matrix, mock_constants, ff)
    perm_secure = PoseidonPermutation(width, alpha, mds_matrix, mock_constants, ff)

    tracker_naive = CryptanalyticTracker(perm_naive)
    tracker_secure = CryptanalyticTracker(perm_secure)

    # Base state and localized input difference restricted to coordinate index 2 (un-activated subspace)
    base_state = [5, 5, 5]
    localized_diff = [0, 0, 4]

    print("="*80)
    print("EXECUTING POSEIDON1 CRYPTANALYTIC TRACKER OVER BN254 SCALAR FIELD")
    print("="*80)

    print("\n[+] TRACK A: NAIVE NON-MDS PARADIGM (IDENTITY LAYER)")
    history_naive = tracker_naive.execute_differential_tracking(base_state, localized_diff, num_rounds)
    for step in history_naive:
        print(f" Round {step['round']} | Diff Vector: {step['diff_vector']} | D(R): {step['diffusion_coeff']}/3")

    print("\n[+] TRACK B: SECURE BENCHMARK PARADIGM (DENSE MDS LAYER)")
    history_secure = tracker_secure.execute_differential_tracking(base_state, localized_diff, num_rounds)
    for step in history_secure:
        print(f" Round {step['round']} | Diff Vector: [Truncated for Log] | D(R): {step['diffusion_coeff']}/3")
    print("="*80)

if __name__ == "__main__":
    demonstrate_vulnerability_paradigms()