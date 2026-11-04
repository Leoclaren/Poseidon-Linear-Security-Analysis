"""
Step 5.1 (RESEARCH_PLAN.md): generate a real circom circuit for a given
(M_I, M_full, round constants) permutation instance, so circom itself --
not our own cost_r1cs()/cost_r1cs_linear() formulas -- counts the R1CS
constraints. The whole point is to catch a formula bug the way Steps 2-4
kept catching bugs: by checking against an independent ground truth.

Usage
-----
    python circuits/generate_poseidon_circuit.py --family poseidon2_sparse --out circuits/out/poseidon2_sparse.circom
    circom circuits/out/poseidon2_sparse.circom --r1cs --sym

The circuit is fully unrolled (one signal per round per coordinate) and
all matrix entries / round constants are baked in as literal field
constants -- circom needs compile-time values, and we already have exact
ones from poseidon.matrix_search.

Result recorded in RESEARCH_PLAN.md Sec 9 Step 5: at t=3, alpha=5, r_f=8,
r_p=57, circom reports "non-linear constraints: 243" (matches
cost_r1cs() exactly) and "linear constraints: 276" (matches
cost_r1cs_linear() exactly) -- for BOTH the sparsest (poseidon2_sparse)
and densest (irreducible_filtered) candidates, identically. Matrix
sparsity has zero effect on R1CS circuit size in this encoding; see
cost_r1cs_linear()'s docstring for why.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from poseidon.matrix_search import (
    poseidon2_sparse_candidate, low_weight_circulant_candidate, irreducible_filtered_candidate,
    nums_full_round_matrix, generate_bound_round_constants,
)

FAMILIES = {
    "poseidon2_sparse": poseidon2_sparse_candidate,
    "low_weight_circulant": low_weight_circulant_candidate,
    "irreducible_filtered": irreducible_filtered_candidate,
}


def generate_circuit_source(M_I, M_full, constants, t, alpha, r_f, r_p, template_name):
    half_f = r_f // 2
    total_rounds = r_f + r_p

    def fmt(x):
        return str(int(x))

    lines = ["pragma circom 2.0.0;", ""]
    lines.append("template SBoxAlpha() {")
    lines.append("    signal input in;")
    lines.append("    signal output out;")
    # Correct left-to-right binary (square-and-multiply) exponentiation,
    # generated at codegen time. A first, simpler attempt here ("square
    # until cur_exp >= alpha, then multiply once by `in`") was WRONG: for
    # alpha=5 it squared three times (overshooting to in^8) then multiplied
    # by `in` to get in^9, not in^5, while also costing 4 constraints
    # instead of 3 -- found by comparing circom's own reported constraint
    # count (324) against cost_r1cs()'s prediction (243) and not matching.
    bits = bin(alpha)[2:]
    acc_name, counter = "in", 0
    for bit in bits[1:]:
        counter += 1
        sq_name = f"t{counter}"
        lines.append(f"    signal {sq_name};")
        lines.append(f"    {sq_name} <== {acc_name} * {acc_name};")
        acc_name = sq_name
        if bit == "1":
            counter += 1
            mul_name = f"t{counter}"
            lines.append(f"    signal {mul_name};")
            lines.append(f"    {mul_name} <== {acc_name} * in;")
            acc_name = mul_name
    lines.append(f"    out <== {acc_name};")
    lines.append("}")
    lines.append("")

    lines.append(f"template {template_name}() {{")
    lines.append(f"    signal input in[{t}];")
    lines.append(f"    signal output out[{t}];")
    lines.append(f"    signal state[{total_rounds + 1}][{t}];")
    lines.append(f"    for (var i = 0; i < {t}; i++) {{ state[0][i] <== in[i]; }}")
    lines.append(f"    component sbox[{total_rounds}][{t}];")
    lines.append("")

    for r in range(total_rounds):
        is_full = r < half_f or r >= half_f + r_p
        M = M_full if is_full else M_I
        c = constants[r * t:(r + 1) * t]
        lines.append(f"    // round {r} [{'full' if is_full else 'partial'}]")
        if is_full:
            for i in range(t):
                lines.append(f"    sbox[{r}][{i}] = SBoxAlpha();")
                lines.append(f"    sbox[{r}][{i}].in <== state[{r}][{i}] + {fmt(c[i])};")
            sbox_terms = [f"sbox[{r}][{j}].out" for j in range(t)]
        else:
            lines.append(f"    sbox[{r}][0] = SBoxAlpha();")
            lines.append(f"    sbox[{r}][0].in <== state[{r}][0] + {fmt(c[0])};")
            sbox_terms = [f"sbox[{r}][0].out"] + [f"(state[{r}][{j}] + {fmt(c[j])})" for j in range(1, t)]

        for i in range(t):
            row_terms = [f"{fmt(int(M[i][j]))} * {sbox_terms[j]}" for j in range(t) if int(M[i][j]) != 0]
            expr = " + ".join(row_terms) if row_terms else "0"
            lines.append(f"    state[{r + 1}][{i}] <== {expr};")
        lines.append("")

    lines.append(f"    for (var i = 0; i < {t}; i++) {{ out[i] <== state[{total_rounds}][i]; }}")
    lines.append("}")
    lines.append("")
    lines.append(f"component main = {template_name}();")
    return "\n".join(lines)


def main():
    from poseidon.field import Fp, FpKoalaBear, FpGoldilocks

    FIELDS = {"bn254": Fp, "koalabear": FpKoalaBear, "goldilocks": FpGoldilocks}

    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=list(FAMILIES), default="poseidon2_sparse")
    ap.add_argument("--field", choices=list(FIELDS), default="bn254",
                     help="RESEARCH_PLAN.md Sec 6.3: which native field to generate the matrix/"
                          "constants in. Constraint COUNT is structural (field-independent), so "
                          "circom always compiles with its own default bn128 prime regardless -- "
                          "use --field only to generate matrix/constants matching a real smaller-"
                          "field deployment target; compile with `circom --prime goldilocks` "
                          "separately if you need field-correctness verified too (circom has no "
                          "native KoalaBear prime).")
    ap.add_argument("--t", type=int, default=3)
    ap.add_argument("--alpha", type=int, default=5)
    ap.add_argument("--r_f", type=int, default=8)
    ap.add_argument("--r_p", type=int, default=57)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    field = FIELDS[args.field]

    M_I, meta_I = FAMILIES[args.family](args.t, field=field)
    M_full, meta_full = nums_full_round_matrix(args.t, seed_label=f"{meta_I['seed_label']}-M_full", field=field)
    constants = generate_bound_round_constants(M_I, M_full, args.t, args.r_f, args.r_p, args.alpha,
                                                seed_label=meta_I["seed_label"], field=field)

    template_name = f"Poseidon1T{args.t}_{args.family}"
    source = generate_circuit_source(M_I, M_full, constants, args.t, args.alpha, args.r_f, args.r_p, template_name)

    out_path = args.out or f"circuits/out/{args.family}.circom"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(source)
    print(f"wrote {out_path}")
    print(f"M_I family: {meta_I}")
    print(f"M_full family: {meta_full}")


if __name__ == "__main__":
    main()
