# S-box Cost Comparison: Power Map, Flystel, Power-Residue, Lookup-Table

## Scope note on sourcing

Direct PDF access to eprint.iacr.org/2022/840 (Anemoi), eprint.iacr.org/2025/926 (Polocolo), and eprint.iacr.org/2026/1931 (SoK) was blocked by Cloudflare bot-protection for every fetch method tried (direct WebFetch, curl with browser UA, r.jina.ai proxy) — all returned HTTP 403 or a CAPTCHA page. Where the primary PDF could not be read directly, numbers below come from (a) a WebFetch-cached PDF of the **original Poseidon paper** (eprint 2019/458, successfully retrieved), (b) a WebFetch-cached PDF of **Clémence Bouvier's own "Anemoi and Jive" zkProof 2022 presentation** (she is a co-author of the Anemoi paper; slides hosted at her Inria page, who.paris.inria.fr), and (c) search-engine-surfaced excerpts of the Anemoi/Polocolo/SoK abstracts and a Zellic blog post. Anything sourced only via a search-engine summary (not a document I opened directly) is flagged as such.

---

## Key Question 1: Anemoi Flystel S-box — construction and Plonk gate cost; does any source report R1CS cost?

### Takeaway
Flystel is a Feistel/butterfly-style S-box built from two quadratic functions and a permutation, with an "open" (high-degree) and CCZ-equivalent "closed" (low-degree) representation. Exact, absolute Plonk-gate and R1CS-constraint counts for Anemoi at multiple widths **are** reported — not just in the ePrint paper (which I could not open directly) but in the paper authors' own zkProof 2022 conference slides, which I retrieved and read in full.

### Cited Findings
- Flystel construction (open Flystel H): `x ← x − Q_γ(y)`, `y ← y − E⁻¹(x)`, `x ← x + Q_δ(y)`, `u ← x, v ← y`; closed Flystel: `R_γ(y,v) = E(y−v) + Q_γ(y)`, `R_δ(y,v) = E(y−v) + Q_δ(v)`, where `Q_γ = βx² + γ`, `Q_δ = βx² + δ` (commonly `β=g` a generator, `γ=0`, `δ=g⁻¹`), and the open/closed forms are CCZ-equivalent with identical differential/linear properties — [search-engine synthesis citing eprint.iacr.org/2022/840](https://eprint.iacr.org/2022/840.pdf) and [cryptography.academy/papers/anemoi-2022](https://cryptography.academy/papers/anemoi-2022/) (I could not open the primary PDF directly to re-verify the exact symbol layout; treat as a close paraphrase, not a verbatim quote).
- From Clémence Bouvier's zkProof 2022 slides ("Anemoi and Jive: New Arithmetization-Oriented tools for Plonk-based applications," slides at who.paris.inria.fr/Clemence.Bouvier/presentation-zkproof-2022.pdf, retrieved and read directly) — **"Constraint comparison for Rescue–Prime, Poseidon, Griffin and Anemoi (s=128) for standard arithmetization, without optimization"**, security level s=128, m = number of parallel Flystel/S-box instances (≈ state width):

  **α = 3:**
  | m | Rescue′ R1CS | Poseidon R1CS | Griffin R1CS | Anemoi R1CS | Rescue′ Plonk | Poseidon Plonk | Griffin Plonk | Anemoi Plonk | Rescue′ AIR | Poseidon AIR | Griffin AIR | Anemoi AIR |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | 2 | 208 | 198 | – | **76** | 312 | 380 | – | **173** | 156 | 300 | – | **114** |
  | 4 | 224 | 232 | 112 | **96** | 560 | 1336 | 291 | **220** | 168 | 348 | 168 | **144** |
  | 6 | 216 | 264 | – | **120** | 756 | 3024 | – | **320** | 162 | 396 | – | **180** |
  | 8 | 256 | 296 | 176 | **160** | 1152 | 5448 | 635 | **456** | 192 | 480 | 264 | **240** |

  **α = 5:**
  | m | Rescue′ R1CS | Poseidon R1CS | Griffin R1CS | Anemoi R1CS | Rescue′ Plonk | Poseidon Plonk | Griffin Plonk | Anemoi Plonk | Rescue′ AIR | Poseidon AIR | Griffin AIR | Anemoi AIR |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | 2 | 240 | 216 | – | **95** | 320 | 344 | – | **192** | 200 | 360 | – | **190** |
  | 4 | 264 | 264 | 110 | **120** | 528 | 1032 | 253 | **244** | 220 | 440 | 220 | **240** |
  | 6 | 288 | 315 | – | **150** | 768 | 2265 | – | **350** | 240 | 540 | – | **300** |
  | 8 | 384 | 363 | 162 | **200** | 1280 | 4003 | 543 | **496** | 320 | 640 | 360 | **400** |

  — [Bouvier, "Anemoi and Jive," zkProof 2022 presentation](https://who.paris.inria.fr/Clemence.Bouvier/presentation-zkproof-2022.pdf) (retrieved in full; also cross-references https://ia.cr/2022/840 and https://ia.cr/2022/1487 for the paper itself).
- **This directly answers "does it report R1CS cost": yes** — e.g., Anemoi at m=8, α=3 costs 160 R1CS constraints vs. Poseidon's 296 and Rescue-Prime's 256 — roughly the "factor of 2 improvement over Poseidon and Rescue in R1CS constraints" figure also stated on the project's own site — [anemoi-hash.github.io](https://anemoi-hash.github.io/).
- Same slide deck, "Comparison for PlonK (with optimizations)" table, s=128, including Reinforced Concrete, with 3-wire and 4-wire Plonk configurations:
  | Hash | m | Constraints (3 wires) | Constraints (4 wires) |
  |---|---|---|---|
  | Poseidon | 2 | 88 | 82 |
  | Poseidon | 3 | 110 | 98 |
  | Reinforced Concrete | 2 | 236 | 174 |
  | Reinforced Concrete | 3 | 378 | 267 |
  | Rescue-Prime | 3 | 252 | 168 |
  | Griffin | 3 | 125 | 111 |
  | AnemoiJive | 2 | 79 (51 with an additional quadratic custom gate for x^α) | 58 |
  — [Bouvier, zkProof 2022 slides](https://who.paris.inria.fr/Clemence.Bouvier/presentation-zkproof-2022.pdf), slide "Some Motivation": headline claim "AnemoiJive: 51 constraints vs. Poseidon: 110 constraints," i.e. "up to 54% improvement over highly optimized Poseidon" in Plonk.
- Native (non-ZK) 2-to-1 compression timings for a 12-8 state over the Goldilocks-like field (p = 2⁶⁴−2³²+1, s=128): Rescue-Prime-12-8: 11.39 µs; Poseidon-12-8: 1.93 µs; Griffin-12-8: 3.13 µs; Anemoi-8: 3.93 µs — [same slides](https://who.paris.inria.fr/Clemence.Bouvier/presentation-zkproof-2022.pdf). (Native speed, not arithmetization cost — included for completeness/context, and to flag that Anemoi's ZK-circuit efficiency comes at a native-speed cost relative to Poseidon.)

### Inferences
- The Plonk-gate advantage of Anemoi's Flystel over Poseidon's power-map S-box grows sharply with state width under "standard, unoptimized" arithmetization (m=8, α=3: 456 vs. 5448 — more than 10x), but narrows a lot once Poseidon itself is heavily optimized with custom gates (110 vs. 51 constraints at the small-m "optimized" comparison) — so the "up to 54%" headline is the optimized-vs-optimized comparison, not the raw-vs-raw one.
- Because a conference-slide source (not the archival paper text) was the only one I could open directly, treat the exact table values as authors'-own numbers but double-check against the eprint 2022/840 PDF directly when it becomes accessible, since slide decks occasionally use rounded or illustrative figures.

### Gaps
- Could not open eprint.iacr.org/2022/840 directly (Cloudflare 403 on every method tried), so I cannot independently verify the slide numbers against the camera-ready paper text, nor extract any additional tables (e.g. Jive-mode-specific costs) that may only appear in the full paper and not the slides.
- No follow-up paper found (beyond the SoK, see Key Question 4) that re-derives or disputes Anemoi's R1CS numbers independently of the authors' own reporting.

---

## Key Question 2: Polocolo power-residue S-box — construction, exact Plonk gate counts at t=3/t=8, and R1CS cost

### Takeaway
The power-residue S-box construction was obtained, and one concrete absolute Plonk-gate number was found (14 gates for the S-box itself at modulus m=1024, vs. 94 for Reinforced Concrete's Bar function), but the paper's own **Table 2 absolute gate totals** for full permutations at t=3 and t=8 could not be retrieved — every route to the full PDF (direct, curl with browser UA, proxy, ResearchGate, Springer) was blocked. Only the headline percentages (21% vs. Anemoi at t=8; 24% vs. Reinforced Concrete at t=3) are confirmed; absolute totals are a gap.

### Cited Findings
- Power-residue S-box definition: `S(x) = x⁻¹ · T[(x/p)_m]`, where `(x/p)_m` denotes the m-th power residue symbol, computed as `x^((p−1)/m)`, and `T` is a lookup table of size `m+1` — [Zellic blog, "Introducing Polocolo: A ZK-Friendly Hash Function for PLONK with Lookup (Part 1)"](https://www.zellic.io/blog/introducing-polocolo/).
- "Polocolo requires 21% less Plonk gates compared to Anemoi" at t=8, and "24% less Plonk gates than Reinforced Concrete" at t=3 — [eprint.iacr.org/2025/926 abstract](https://eprint.iacr.org/2025/926) (abstract-page text, confirmed by multiple independent search snippets); full paper also published as [EUROCRYPT 2025, Advances in Cryptology, pp. 303–332 / Springer DOI 10.1007/978-3-031-91134-7_11](https://dl.acm.org/doi/10.1007/978-3-031-91134-7_11).
- The Polocolo S-box itself "requires only 14 Plonk gates" when the lookup-table parameter m=1024, "significantly fewer than 94 gates required for the Bar function from Reinforced Concrete" — [Zellic blog](https://www.zellic.io/blog/introducing-polocolo/). (This is a per-S-box-call figure, not a full-permutation total at t=3/t=8 — do not conflate the two.)
- The Zellic blog post independently confirms the Reinforced Concrete "Bar function... accounts for approximately 75% of the constraints in the PlonKup" — same figure also found independently via web search of other sources (see Key Question 3) — [Zellic blog](https://www.zellic.io/blog/introducing-polocolo/).
- A search snippet (not independently re-verified against the primary text) states the EUROCRYPT 2025 paper contains "Table 2: The number of Plonk gates required for ZK-friendly hash functions," confirming such a table exists in the paper, but the absolute values inside it were not retrievable through any search-engine excerpt — [search result summary, no direct URL for the table content itself].

### Inferences
- Combining the one hard number available (14 gates for the Polocolo S-box at m=1024 vs. 94 for Reinforced Concrete's Bar) with the headline "24% less than Reinforced Concrete at t=3" suggests the per-S-box efficiency gain (14 vs. 94, an 85% reduction) is much larger than the full-permutation gain (24%) — implying Polocolo's linear layer, round count, or other components eat into the S-box-level savings once a full t=3 permutation is assembled. This is an inference, not a reported fact — the paper's own round-count and full-permutation breakdown would be needed to confirm.

### Gaps
- **No absolute Plonk gate totals for Polocolo at t=3 or t=8 were found** (only percentages and the single S-box-only data point). The paper's Table 2 almost certainly has these numbers; I was blocked from eprint.iacr.org/2025/926.pdf (403), the ResearchGate mirror (403), and the Springer chapter page (redirected to a paywalled login). Someone with direct access to the PDF (or an institutional Springer/ACM login) should extract Table 2 directly.
- No R1CS cost was found anywhere for Polocolo — the abstract and every source consulted frame the design specifically around Plonk/PlonKup lookup arguments, and none mention an R1CS variant. This is plausibly because the power-residue S-box's lookup table `T[(x/p)_m]` has no natural non-lookup-backend representation, but I found no explicit statement to this effect in the paper (gap, not a confirmed design limitation).
- Could not confirm whether the paper or any follow-up gives a plain Plonk-gate count *without* lookup-argument support (i.e., Polocolo compiled to a lookup-free Plonk backend) — the whole point of the design appears to be that it requires a lookup-capable backend (same category as Reinforced Concrete/Monolith; see Key Question 3), but this should be confirmed against the paper text.

---

## Key Question 3: Reinforced Concrete / Monolith lookup-table S-box — cost structure and backend compatibility

### Takeaway
Both Reinforced Concrete (CCS 2022) and Monolith are confirmed to require a lookup-argument-capable proof system (Plookup/Halo2-style lookups) to realize their claimed efficiency; they are not naturally compatible with plain R1CS/Groth16, since their core nonlinear step maps field elements through literal lookup tables rather than polynomial constraints. Reinforced Concrete's "Bars" layer (the lookup-based S-box layer) is reported to consume about 75% of total PlonKup constraints, and at t=3 its full-permutation Plonk-gate cost (with optimizations) is 236–378 depending on wire count, per Bouvier's slide table above.

### Cited Findings
- Reinforced Concrete is "the first lookup-based ZK-friendly hash function," presented at CCS 2022, and "exploits the advantages of lookup-equipped proof systems," suitable for membership proofs and verifiable computation — [web search summary of Reinforced Concrete, CCS 2022](https://repository.ubn.ru.nl/bitstream/handle/2066/287472/287472.pdf?sequence=1) (direct PDF access blocked, 403; summary derived from search-indexed content).
- "Out of the 15 layers in Reinforced Concrete, only one is the Bars layer, yet it still accounts for 75% of the constraints in the PlonKup" — [search result, context: Lookup Argument discussion referencing Reinforced Concrete](https://eprint.iacr.org/2025/1876.pdf) ("SoK: Lookup Table Arguments"), independently corroborated by the Zellic Polocolo blog post's identical "75% of constraints in PlonKup" claim about the Bar function — [Zellic blog](https://www.zellic.io/blog/introducing-polocolo/).
- Reinforced Concrete structure: 7-round permutation `RCπ` fixed at state size 3 (triples `(x1,x2,x3)`), composed of three layers: **Concrete** (MDS-matrix linear layer + round constants), **Bricks** (a degree-5 non-linear permutation structurally similar to Griffin's `G(·)`, defined as `(x1^d, x2(x1²+αx1+β1), x3(x2²+α2 x2+β2))`), and **Bars** (per-element `Bar(x) = Comp(Sbox(Decomp(x)))`, i.e. decompose the field element into small chunks, apply an S-box via lookup table to each chunk, recompose) — [HashEmAll / "Gotta Hash 'Em All" paper, arXiv:2501.18780](https://arxiv.org/pdf/2501.18780) (PDF retrieved and read directly).
- "Lookup Tables" class hash functions (Reinforced Concrete, Monolith) "only work with proof systems that support table lookups, such as Plookup and Arya," and "one of the limitations of RC is that it can only achieve peak performance when operating over a proof system that supports lookup functions" — [arXiv:2501.18780, "Gotta Hash 'Em All"](https://arxiv.org/pdf/2501.18780) (direct read). This is an explicit, direct statement that Reinforced Concrete is **not naturally compatible with plain R1CS/Groth16** — it needs a lookup-argument backend (Plookup-style, which includes Halo2's lookup argument machinery; also referenced generically for STARK-style AIR backends that support lookups).
- Monolith: "the first arithmetization-oriented hash function with native performance comparable to SHA3-256, while still being competitive inside SNARK/STARK circuits," and "outperforms Poseidon in a circuit using the Merkle tree prover in the Plonky2 framework" — [web search summary, Monolith / Horizen Labs](https://hackmd.io/@aiv768/r1w-NfPyMl) and [Horizen Labs Medium post, "Introducing Monolith"](https://medium.com/@horizenlabs-tech/introducing-monolith-for-faster-hashing-in-zk-settings-6980f406af0e).
- Key structural distinction for Monolith vs. Reinforced Concrete/Tip5: "Monolith relies on the new 'lookup argument' to speed up its computation, and in contrast to other lookup-oriented schemes like Reinforced Concrete or Tip5, the lookup table is not actually stored in the software implementation, and instead simple CPU-friendly instructions are used" — [web search summary](https://hackmd.io/@aiv768/r1w-NfPyMl) (native/plaintext-side implementation detail, not a circuit-cost number, but relevant to why Monolith's lookup argument differs from Reinforced Concrete's).
- Monolith benchmark in Plonky2 (a STARK-style, lookup-argument-capable backend): Monolith-64-sponge: 3.49 ms proving / 0.63 ms verification / 113 kB proof size, vs. Poseidon: 6.23 ms proving / 1.12 ms verification / 70 kB proof size — i.e. "Monolith proofs are approximately 60% larger than Poseidon proofs," a size/speed trade-off — [web search summary citing Monolith ToSC paper benchmarks](https://tosc.iacr.org/index.php/ToSC/en/article/download/11810/11315/12843).

### Inferences
- Both Reinforced Concrete and Monolith are explicitly positioned as requiring lookup-argument support (Plookup/Halo2-style lookup arguments, or STARK/Plonky2-style lookup-capable AIR); neither has a published, efficient R1CS/Groth16 circuit — their "cost" is better expressed in lookup-argument "rows"/constraints than classic R1CS multiplication counts. This matches the task's hypothesis that lookup-based S-boxes are backend-gated rather than backend-agnostic.
- The 75%-of-constraints figure for Reinforced Concrete's Bars layer, even inside a lookup-capable PlonKup backend, suggests the lookup argument's own overhead (not the lookup table size) dominates — reinforcing why Polocolo's redesign (far fewer gates per S-box: 14 vs. 94) targeted exactly this layer.

### Gaps
- No exact lookup-argument "row count" or "constraint count" number (as opposed to the 75%-of-total qualitative figure) was retrieved from the Reinforced Concrete paper itself — the CCS 2022 paper PDF was blocked (403) at the only mirror found (Radboud repository). A reader with direct paper access should pull the exact PlonKup row/constraint counts for the Bars layer at t=3.
- No explicit per-backend breakdown was found distinguishing which lookup-argument-capable systems (Halo2 vs. Plonky2/STARKs vs. others) Reinforced Concrete itself has been benchmarked on — the clearest direct benchmark numbers found were for Monolith in Plonky2, not for Reinforced Concrete in Halo2 specifically.
- Could not find a citable, exact statement of whether Reinforced Concrete/Monolith *can* be compiled to R1CS at all (even inefficiently) or whether the lookup step is fundamentally inexpressible without a lookup argument (e.g. would require unrolling the full table as a giant disjunction of equality constraints) — sources state it "only works with" or "can only achieve peak performance" with lookup-capable systems, which is suggestive but not a hard impossibility claim for R1CS compatibility in the abstract.

---

## Key Question 4: Is there a 2025–2026 SoK/survey tabulating S-box costs across backends? (eprint 2026/1931 specifically)

### Takeaway
Yes — "SoK: Zero-Knowledge Friendly Hash Functions over Prime Fields" (Bouvier, Grassi, Koschatko, Rechberger, Schmid, Steiner, Wu, Yan; eprint 2026/1931) is confirmed to exist and, per its own abstract, explicitly analyzes constructions "across different arithmetization styles (R1CS, AIR, PLONK), both theoretically by deriving the underlying constraint or gate counts, and empirically through extensive benchmarks" — exactly the kind of comparison table requested. However, the PDF itself was inaccessible (Cloudflare 403 on every retrieval method tried), so the actual table contents, numbers, and structure could not be extracted for this note.

### Cited Findings
- Paper identified: "SoK: Zero-Knowledge Friendly Hash Functions over Prime Fields," authors Clémence Bouvier, Lorenzo Grassi, Katharina Koschatko, Christian Rechberger, Fabian Schmid, Matthias Johann Steiner, Zhuo Wu, Hailun Yan — [eprint.iacr.org/2026/1931](https://eprint.iacr.org/2026/1931).
- Abstract states the paper "conduct[s] a systematic survey" covering "both algorithmic design paradigms and modes of operation for ZK-friendly hash functions," and "analyze[s] each construction across different arithmetization styles (R1CS, AIR, PLONK), both theoretically, by deriving the underlying constraint or gate counts, and empirically, through extensive benchmarks" — [eprint.iacr.org/2026/1931 abstract](https://eprint.iacr.org/2026/1931) (abstract page successfully fetched; full PDF was not).
- Notably, this SoK shares an author (Clémence Bouvier) with the Anemoi paper, which is consistent with — and lends extra credibility to — the Anemoi R1CS/Plonk/AIR numbers reported from her zkProof 2022 slides under Key Question 1; it is plausible (not confirmed) that this SoK's tables reuse or extend that same comparison methodology.

### Inferences
- Given the shared authorship with Anemoi and the explicit framing (R1CS/AIR/PLONK, theoretical + empirical), this SoK is very likely the single best source for the comparison table requested by this research task, once accessible — it should be prioritized for direct retrieval before finalizing any report built on this topic.

### Gaps
- **Could not retrieve the actual comparison table, numbers, or structure** from eprint 2026/1931 — direct PDF fetch (403), curl with browser user-agent (403), and r.jina.ai proxy (CAPTCHA page, no bypass) were all tried and all failed against IACR's Cloudflare bot protection. This is the single largest gap in this research: the report-writer should flag that a very likely ideal source exists but was not readable in this pass, and recommend a follow-up attempt (e.g., via a logged-in browser session, institutional access, or waiting for the Cloudflare challenge to lift) to pull Table numbers directly.
- Since the paper is dated 2026 (very recent — within the current month per today's date context), no secondary mirrors (arXiv cross-post, ResearchGate, Google cache, Semantic Scholar full text) were found; it may simply not yet be mirrored anywhere else.

---

## Key Question 5: Power-map S-box (x³/x⁵) — citable R1CS cost formula, and separately the Plonkish/custom-gate cost

### Takeaway
The hypothesized R1CS formula — `floor(log2(α))` squarings + `(popcount(α)−1)` extra multiplications — is **confirmed exactly** by the original Poseidon paper for α=3 (2 constraints) and α=5 (3 constraints), and the paper also gives the inverse S-box's R1CS cost (3 constraints: 1 for the non-zero case, 2 more for the zero case). Plonkish/custom-gate costs are reported separately and differ from the R1CS counts (notably because a single Plonk/TurboPlonk custom gate can fuse a squaring with surrounding affine operations) — confirmed via the Anemoi authors' own comparison tables, which show e.g. Poseidon α=3 needing only 110 (3-wire) / 98 (4-wire) Plonk constraints per S-box-call context at small m once heavily optimized with a custom gate, versus the much larger "standard, unoptimized" Plonk counts (e.g. 5448 at m=8).

### Cited Findings
- Direct quote from the original Poseidon paper (Grassi, Khovratovich, Rechberger, Roy, Schofnegger, eprint 2019/458, Section 6.2.1 "Groth16"): "It is easy to see that the S-box x³ is represented by 2 constraints, the S-box x⁵ by 3 constraints... and the S-box 1/x by 3 constraints (1 for the non-zero case, and two more for the zero case)" — [POSEIDON: A New Hash Function for Zero-Knowledge Proof Systems, eprint.iacr.org/2019/458](https://eprint.iacr.org/2019/458.pdf) (PDF retrieved and read directly). This exactly matches the hypothesized formula: α=3 → `floor(log2 3)=1` squaring + `(popcount(3)−1)=1` extra multiplication = 2; α=5 → `floor(log2 5)=2` squarings + `(popcount(5)−1)=1` extra multiplication = 3.
- The same paper gives aggregate per-round-type R1CS formulas for a full Poseidon permutation (not just the S-box in isolation): "2tR_F + 2R_P constraints for x³-Poseidon_π" and analogous "3tR_F+3R_P"-style formulas are given for x⁵ and x⁻¹ variants (where t = state width, R_F = number of full rounds, R_P = number of partial rounds) — [eprint.iacr.org/2019/458, Section 6.2.1](https://eprint.iacr.org/2019/458.pdf) (direct read; exact coefficients for the x⁵ and x⁻¹ cases appeared in the extracted text as "3tR_{N−2M}^{F}+3R_P" style expressions, with some OCR/extraction noise around subscripts — the α=3 case, `2tR_F+2R_P`, is the cleanly extracted one).
- Concrete R1CS constraint counts for full permutations at various state widths (m, acting as a proxy for t) and both α=3 and α=5, from the Anemoi-authors' comparison table (see Key Question 1 table in full): e.g. Poseidon α=3: m=2→198, m=4→232, m=6→264, m=8→296 constraints; Poseidon α=5: m=2→216, m=4→264, m=6→315, m=8→363 constraints — [Bouvier, zkProof 2022 slides](https://who.paris.inria.fr/Clemence.Bouvier/presentation-zkproof-2022.pdf) (direct read). These are full-permutation totals (S-box + linear layer + round constants across all rounds), not just the per-S-box cost, and should not be confused with the 2-constraint/3-constraint S-box-only figures above.
- Plonk (plonkish) gate costs for the *same* full permutations, standard/unoptimized arithmetization, from the same slide table: Poseidon α=3: m=2→380, m=4→1336, m=6→3024, m=8→5448; Poseidon α=5: m=2→344, m=4→1032, m=6→2265, m=8→4003 — [Bouvier, zkProof 2022 slides](https://who.paris.inria.fr/Clemence.Bouvier/presentation-zkproof-2022.pdf). Note the Plonk counts are dramatically larger than R1CS counts for Poseidon in the *unoptimized* case (e.g. m=8, α=3: 5448 Plonk vs. 296 R1CS) — this is the opposite relationship from what a custom-gate-friendly Plonkish system would ideally achieve, and reflects that a vanilla Plonk compiler (without a dedicated power-map custom gate) represents each R1CS-style quadratic constraint fairly directly, without being able to "fuse" multiple squarings per gate.
- Once a Plonk/TurboPlonk compiler is specifically optimized with "a separate polynomial for each S-box line" and gets "rid of wire layout polynomials," the same slide deck's "optimized" table shows Poseidon at only 110 constraints (3-wire) / 98 constraints (4-wire) for m=3, and 88/82 for m=2 — i.e. the optimized Plonk cost becomes comparable to or below the unoptimized-Plonk-to-R1CS ratio, confirming that **Plonkish custom gates can fuse a multiplication with surrounding affine/addition operations in one gate**, materially changing the cost relative to raw R1CS counting — [Bouvier, zkProof 2022 slides](https://who.paris.inria.fr/Clemence.Bouvier/presentation-zkproof-2022.pdf); the Poseidon paper itself separately describes this optimization approach in Section 6.2.3 ("PLONK"): "Define a separate polynomial for each S-box line... Get rid of wire layout polynomials... Express round transitions as a system of affine equations," reporting the optimized PLONK compiler makes "only (w+11)R point multiplications for a single permutation call" (w = width-related parameter, R = round count) — [eprint.iacr.org/2019/458, Section 6.2.3](https://eprint.iacr.org/2019/458.pdf) (direct read).

### Inferences
- The user's hypothesized R1CS formula is correct and now has a primary, quoted citation (the original Poseidon paper itself, not a secondary source) — this should be stated with full confidence in the final report.
- The R1CS-vs-Plonk relationship is backend/compiler-dependent, not just alpha-dependent: the *same* S-box (Poseidon's x^5) can cost 3 R1CS constraints but anywhere from ~4003–5448 "naive Plonk gates" (unoptimized, full permutation, large m) down to ~82–110 "optimized Plonk gates" (small m, custom gate), so any report citing a single "Plonk cost" number for a power-map S-box must specify whether it assumes a dedicated custom gate or a generic/naive Plonk compilation — these differ by roughly one to two orders of magnitude in the data gathered here.

### Gaps
- Could not retrieve the exact OCR-clean coefficients for the x⁵ and x⁻¹ full-permutation R1CS formulas from the Poseidon paper (subscript/superscript text extraction was garbled around "R_F", "R_P", "N−2M" terms) — only the α=3 formula (`2tR_F + 2R_P`) extracted cleanly. A reader with the actual PDF open (rather than pdftotext-extracted text) should re-verify the exact x⁵ and x⁻¹ formulas directly from Table/Section 6.2.1 of eprint 2019/458.
- No citable, exact "Plonk gate cost formula" (as a function of α alone, analogous to the R1CS `floor(log2 α) + popcount(α) − 1` formula) was found — all Plonk numbers gathered are either full-permutation totals (confounding S-box cost with round count and linear-layer cost) or qualitative statements about custom-gate fusion, not a clean per-S-box Plonk-gate formula parameterized by α alone.
