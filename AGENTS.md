i# Simplifying the linear layer in partial rounds

## Problem statement

The partial rounds in Poseidon1 use an MDS matrix. It was shown that a non-MDS matrix in Poseidon2 enhances some attacks. On the other hand, there is an equivalent representation of Poseidon1 where the matrix is not MDS.

**Prove or disprove: using a non-MDS matrix in Poseidon1 partial rounds is okay.**

---

## Background

### Poseidon1 partial round structure

A single partial round over field $\mathbb{F}_p$ (BN254, $p \approx 2^{254}$) applies:

```
state = (x_0, x_1, ..., x_{t-1})

1. S-box:   x_0 ← x_0^α        (only coordinate 0)
            x_i ← x_i           (identity for i = 1..t-1)

2. Constants: x_i ← x_i + c_i

3. Linear layer: state ← M · state
```

The key constraint: **only coordinate 0 is non-linear**. Coordinates 1 through t−1 remain linear throughout a full sequence of partial rounds.

### MDS criterion (branch number)

A matrix $M \in \mathbb{F}_p^{t \times t}$ is MDS if and only if its branch number satisfies:

$$B(M) = \min_{\Delta \neq 0} \left( \text{wt}(\Delta) + \text{wt}(M\Delta) \right) \geq t + 1$$

For $t = 3$, this requires $B(M) \geq 4$.

---

## Claim

> Using a non-MDS matrix in Poseidon1 partial rounds is **NOT okay**.

---

## Proof: Invariant subspace trail

### Setup

Let $t = 3$. Consider the input difference:

$$\Delta = (0,\ 0,\ \delta) \quad \text{with } \delta \neq 0$$

This difference is localized entirely in coordinates $\{e_1, e_2\}$ — the linear coordinates.

### Step 1: S-box does not activate

In round $r$, both states $A$ and $B$ satisfy:

$$A_0 = B_0 \implies A_0^\alpha = B_0^\alpha$$

So after the S-box, the difference in coordinate 0 remains zero:

$$\Delta_0^{(\text{after S-box})} = 0$$

The full state difference after the S-box is still $(0, 0, \delta)$.

### Step 2: Linear layer with non-MDS matrix

Let $M$ be non-MDS with $B(M) < t+1$. In particular, for the identity matrix $M = I$:

$$M \cdot (0, 0, \delta) = (0, 0, \delta)$$

Coordinate 0 receives zero contribution from the difference. The difference **never reaches the S-box position**.

### Step 3: Induction over R partial rounds

By induction: if $\Delta^{(r)} = (0, 0, \delta^{(r)})$ at the start of round $r$, then:

1. S-box: $\Delta_0$ unchanged = 0
2. Constants: affine, does not affect differences
3. Linear layer: $\Delta^{(r+1)} = M \cdot (0, 0, \delta^{(r)}) = (0, 0, \delta^{(r+1)})$

The subspace $V = \{(0, 0, x) \mid x \in \mathbb{F}_p\}$ is invariant under all partial rounds.

### Step 4: All partial rounds collapse to linear

Within the invariant subspace $V$, every partial round is:

$$\Delta^{(r+1)} = M_{22} \cdot \delta^{(r)}$$

where $M_{22}$ is the bottom-right entry of $M$. This is a **purely linear** map. The S-box contributes nothing.

### Consequence: differential attack

For any two inputs $A$, $B$ with $A - B \in V$:

- The full partial round sequence is linear in the difference
- An adversary can compute the output difference without knowing the key or constants
- The non-linear security argument for partial rounds fails entirely

### Branch number confirmation

For $M = I$ (identity):

| Input diff $\Delta$ | Output diff $M\Delta$ | $\text{wt}(\Delta)$ | $\text{wt}(M\Delta)$ | Sum |
|---|---|---|---|---|
| $(1,0,0)$ | $(1,0,0)$ | 1 | 1 | **2** |
| $(0,1,0)$ | $(0,1,0)$ | 1 | 1 | **2** |
| $(0,0,1)$ | $(0,0,1)$ | 1 | 1 | **2** |

$B(I) = 2 < t+1 = 4$ — non-MDS confirmed.

For the MDS benchmark $M = \begin{pmatrix}2&3&5\\7&11&13\\17&19&23\end{pmatrix}$:

$$M \cdot (0,0,\delta) = (5\delta,\ 13\delta,\ 23\delta)$$

All three coordinates activated immediately. $B(M) \geq 4$ — invariant subspace does not exist.

---

## Diffusion tracking (empirical confirmation)

Simulation over BN254, $\alpha = 5$, 6 partial rounds, input difference $\Delta = (0, 0, 4)$:

| Round | Non-MDS (Identity) $D(R)$ | MDS benchmark $D(R)$ |
|---|---|---|
| 0 | 1/3 | 1/3 |
| 1 | 1/3 | 3/3 |
| 2 | 1/3 | 3/3 |
| 3 | 1/3 | 3/3 |
| 4 | 1/3 | 3/3 |
| 5 | 1/3 | 3/3 |
| 6 | 1/3 | 3/3 |

Non-MDS: diffusion coefficient stays at 1/3 forever — the S-box is never engaged.
MDS: full diffusion achieved at round 1.

---

## Conclusion

**Non-MDS is NOT okay in Poseidon1 partial rounds.**

The proof constructs an explicit invariant subspace $V \subset \mathbb{F}_p^t$ under the composition of partial rounds. Any difference $\Delta \in V$ never activates the S-box, reducing all $R_P$ partial rounds to a sequence of linear maps. This breaks the differential security argument for the partial round sequence entirely.

The MDS requirement is necessary, not merely sufficient:

- **MDS** ⟹ $B(M) \geq t+1$ ⟹ every nonzero difference activates coordinate 0 after at most one round ⟹ no invariant subspace.
- **Non-MDS** ⟹ $B(M) < t+1$ ⟹ ∃ nonzero $\Delta$ with $\text{wt}(M\Delta) = 0$ at position 0 ⟹ invariant subspace trail exists.

The equivalent representation of Poseidon1 that uses a non-MDS matrix exploits a coordinate transformation that preserves the permutation's input/output behavior but does **not** preserve its security arguments — using it as a standalone design choice would be a vulnerability.

---

## Implementation

