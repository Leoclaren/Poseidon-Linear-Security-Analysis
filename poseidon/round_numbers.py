"""
Round-number security bounds from the original Poseidon paper (Grassi,
Khovratovich, Rechberger, Roy, Schofnegger, "POSEIDON: A New Hash Function
for Zero-Knowledge Proof Systems", USENIX Security 2021, eprint 2019/458),
read directly from the primary-source PDF on 2026-11-03.

RESEARCH_PLAN.md Step 5.4 found that our own tooling (analysis/
subspace_scanner.py, analysis/finite_trail_scanner.py) only checks
ALGEBRAIC subspace-trail-style security for R_F/R_P -- it has no concept
of STATISTICAL (differential/linear) security, which is what actually
lower-bounds R_F in the original design (Eq. 2 below). Reusing a published
R_F for a different (t, field) pair without re-checking this bound is
unsound -- this module implements the check so we stop doing that.
"""

import math


def statistical_min_R_F(M: int, log2_p: float, t: int, alpha: int, margin: int = 2) -> dict:
    """
    eprint 2019/458 Eq. (2) ("Differential/Linear Distinguishers", Sec
    5.5.1): the number of full rounds R_F that COULD be attacked by the
    statistical (differential/linear) attacks considered is bounded by

        R_F < 6   if M <= (floor(log2(p)) - C) * (t + 1)
        R_F < 10  otherwise

    where C = 2 for S(x) = 1/x, and C = log2(alpha - 1) for S(x) = x^alpha
    (so C=1 for alpha=3, C=2 for alpha=5 -- "at least 6 rounds with full
    S-box layers are necessary to provide security against the statistical
    attacks we consider", same section). The paper then adds an arbitrary
    +2 full-round margin (Sec 5.4) on top of this minimum.

    Cross-validated against the paper's own worked examples (Propositions
    5.1-5.3, all BN254-scale, alpha=5): POSEIDON-80/128/256 all give
    bound=6, final R_F=8 -- matches Table 1's R_F=8 for every listed
    instance exactly.

    Returns {"bound": 6 or 10, "min_R_F": bound + margin}. Pass margin=0
    to get the bare (no safety-margin) minimum.
    """
    C = 2 if alpha == -1 else math.log2(alpha - 1)
    threshold = (math.floor(log2_p) - C) * (t + 1)
    bound = 6 if M <= threshold else 10
    return {"bound": bound, "min_R_F": bound + margin, "threshold": threshold, "C": C}
