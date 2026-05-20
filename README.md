# Poseidon1 — Linear Layer Security Analysis

Research implementation proving that **non-MDS matrices in Poseidon1 partial rounds are NOT okay**.

The project demonstrates an invariant subspace trail attack that breaks the differential security of Poseidon1 when its partial-round linear layer is replaced with a non-MDS matrix.

---

## Table of Contents

- [Background](#background)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [CLI Reference](#cli-reference)
  - [permute](#permute)
  - [attack](#attack)
  - [diffusion](#diffusion)
  - [stats](#stats)
  - [branch](#branch)
- [Plots](#plots)
- [Matrices](#matrices)
- [Security Result](#security-result)

---

## Background

Poseidon1 is a ZK-friendly hash function operating over a prime field F_p (BN254, p ≈ 2²⁵⁴).
Each **partial round** applies:

```
1. S-box on coordinate 0 only:  x_0 ← x_0^α
2. Add round constants:          x_i ← x_i + c_i
3. Linear layer:                 state ← M · state
```

The linear layer matrix `M` must be **MDS** (Maximum Distance Separable) to guarantee that any
input difference eventually reaches coordinate 0 and activates the S-box. If `M` is non-MDS,
there exists a non-zero difference that never activates the S-box — all partial rounds collapse
to a linear map and differential security is lost.

---

## Project Structure

```
poseidon/
├── poseidon/                    # Core implementation
│   ├── __init__.py
│   ├── field.py                 # F_p arithmetic (BN254 scalar field)
│   ├── matrices.py              # MDS, identity, circulant + branch_number()
│   ├── constants.py             # Deterministic round constants (SHAKE-256)
│   └── permutation.py          # PoseidonPermutation class
│
├── attacks/                     # Attack demonstrations
│   ├── __init__.py
│   └── invariant_subspace.py   # Invariant subspace trail attack
│
├── analysis/                    # Analysis tools
│   ├── __init__.py
│   ├── diffusion.py             # Round-by-round diffusion tracking
│   └── statistics.py           # Security statistics summary
│
├── main.py                      # CLI entry point
├── plot.py                      # Matplotlib visualizations
└── requirements.txt
```

---

## Installation

Python 3.10+ required.

```bash
git clone <repo>
cd poseidon
pip install -r requirements.txt
```

No external dependencies beyond `matplotlib` and `numpy` — all field arithmetic is pure Python.

---

## CLI Reference

All commands go through `main.py`. Run with `--help` at any level for options.

```
python main.py <command> [options]
```

### Global options (available on every subcommand)

| Flag | Default | Description |
|------|---------|-------------|
| `--t` | 3 | State width |
| `--r_f` | 8 | Number of full rounds |
| `--r_p` | 57 | Number of partial rounds |
| `--alpha` | 5 | S-box exponent (5 for BN254) |
| `--delta` | 4 | Initial difference value for attack/diffusion |

---

### `permute`

Run the Poseidon1 permutation on a given input state.

```bash
python main.py permute [--input N N N] [--matrix mds|identity|circulant]
                       [--partial-only] [--trace]
```

| Flag | Description |
|------|-------------|
| `--input` | Space-separated input coordinates (default: `1 2 3`) |
| `--matrix` | Matrix to use for partial rounds |
| `--partial-only` | Skip full rounds, run only partial rounds |
| `--trace` | Print the state after every single round |

**Examples:**

```bash
# Full permutation with MDS matrix
python main.py permute --input 1 2 3 --matrix mds

# Partial rounds only, identity matrix, with round trace
python main.py permute --input 1 2 3 --matrix identity --partial-only --trace --r_p 6

# Custom input with 4 partial rounds and trace
python main.py permute --input 100 200 300 --matrix mds --partial-only --trace --r_p 4
```

---

### `attack`

Demonstrate the invariant subspace trail attack across all three matrices.

For each matrix, the attack:
1. Checks whether `V = {(0, 0, x)}` is invariant under all partial rounds
2. Verifies that the output difference is **linearly predictable** without evaluating the permutation
3. Reports how many rounds activate coordinate 0 (the S-box position)

```bash
python main.py attack [--r_p N] [--delta N] [--verbose]
```

| Flag | Description |
|------|-------------|
| `--r_p` | Number of partial rounds to trace |
| `--delta` | Difference magnitude (placed in last coordinate) |
| `--verbose` | Print per-round subspace membership for each matrix |

**Examples:**

```bash
# Basic attack demo (6 partial rounds)
python main.py attack --r_p 6 --delta 4

# Verbose: see per-round coord-0 activation status
python main.py attack --r_p 6 --delta 4 --verbose

# Larger delta value
python main.py attack --r_p 10 --delta 999
```

**Output interpretation:**
- `Invariant V: True` — subspace never broken → attack succeeds → **VULNERABLE**
- `Prediction correct: True` — attacker can predict output diff without the permutation
- `Coord-0 activations: 0` — S-box never engaged across all partial rounds

---

### `diffusion`

Print a round-by-round diffusion table comparing all matrices.

Diffusion coefficient `D(r)` = fraction of coordinates that are non-zero in the difference
after `r` rounds, given initial difference `Δ = (0, …, 0, delta)`.

```bash
python main.py diffusion [--r_p N] [--delta N]
```

**Example:**

```bash
python main.py diffusion --r_p 6 --delta 4
```

```
Round              mds         identity        circulant
────────────────────────────────────────────────────────
    0             0.3333           0.3333           0.3333
    1             1.0000           0.3333           0.6667
    2             1.0000           0.3333           1.0000
    ...
```

- MDS reaches `D=1.0` (full diffusion) at round 1
- Identity stays at `D=0.333` forever — S-box never engaged

---

### `stats`

Print a security statistics summary for all matrices.

```bash
python main.py stats [--r_p N] [--delta N]
```

**Example:**

```bash
python main.py stats --r_p 6
```

```
[SECURE    ] mds       | B(M)= 4 | MDS=True  | full_diff_round=    1 | final_D=1.000
[VULNERABLE] identity  | B(M)= 2 | MDS=False | full_diff_round=Never | final_D=0.333
[VULNERABLE] circulant | B(M)= 3 | MDS=False | full_diff_round=    2 | final_D=1.000
```

---

### `branch`

Print the branch number for all available matrices and whether they meet the MDS threshold.

```bash
python main.py branch [--t N]
```

**Example:**

```bash
python main.py branch
```

```
t=3  |  MDS threshold = t+1 = 4

[MDS]     mds       : B(M) = 4
[non-MDS] identity  : B(M) = 2
[non-MDS] circulant : B(M) = 3
```

A matrix is MDS iff `B(M) ≥ t + 1`.

---

## Plots

Visualizations are in `plot.py`. Run with `--help` for all options.

```bash
python plot.py --mode <mode> [options]
```

| Mode | Description |
|------|-------------|
| `diffusion` | Line chart of D(r) per round for each matrix |
| `branch` | Bar chart of branch numbers with MDS threshold line |
| `stats` | Color-coded summary table |
| `all` | 4-panel dashboard combining all of the above |

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--mode` | `all` | Which plot to render |
| `--t` | 3 | State width |
| `--r_p` | 10 | Number of partial rounds |
| `--alpha` | 5 | S-box exponent |
| `--delta` | 4 | Initial difference value |
| `--save` | _(show)_ | Save to file path instead of opening a window |

**Examples:**

```bash
# Full dashboard, open in window
python plot.py --mode all

# Diffusion plot, 10 rounds, save to PNG
python plot.py --mode diffusion --r_p 10 --save diffusion.png

# Branch number chart
python plot.py --mode branch

# Stats table with custom params
python plot.py --mode stats --r_p 6 --delta 99 --save stats.png

# Full dashboard saved to file
python plot.py --mode all --r_p 10 --save dashboard.png
```

---

## Matrices

Three matrices are implemented, selectable via `--matrix`:

| Name | Description | B(M) | MDS (t=3)? |
|------|-------------|------|------------|
| `mds` | Benchmark MDS matrix from the proof | 4 | Yes |
| `identity` | Identity matrix I₃ | 2 | No |
| `circulant` | Circulant non-MDS example | 3 | No |

The MDS matrix used:

```
M = [ 2   3   5 ]
    [ 7  11  13 ]
    [17  19  23 ]
```

Applying `M` to `(0, 0, δ)` yields `(5δ, 13δ, 23δ)` — all coordinates activated immediately.
The identity matrix applied to `(0, 0, δ)` yields `(0, 0, δ)` — coordinate 0 never changes.

---

## Security Result

**Non-MDS is NOT okay in Poseidon1 partial rounds.**

For any non-MDS matrix `M` with branch number `B(M) < t+1`, there exists a non-zero subspace
`V ⊂ F_p^t` that is invariant under every partial round. Any difference `Δ ∈ V` never reaches
the S-box position, reducing all `R_p` partial rounds to a sequence of linear maps.

An attacker can:
1. Choose any pair of inputs `A`, `B` with `A - B ∈ V`
2. Predict the full output difference through all partial rounds **without evaluating the permutation**
3. Exploit this to mount differential attacks on the partial round sequence

The MDS property is **necessary**, not just sufficient:

- **MDS** ⟹ `B(M) ≥ t+1` ⟹ every nonzero difference activates coord-0 within one round ⟹ no invariant subspace
- **non-MDS** ⟹ `B(M) < t+1` ⟹ invariant subspace exists ⟹ partial rounds are linear in that subspace
