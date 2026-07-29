# Retraction — 2026-07-28 Adversarial Verification

**ACER-CLAUDE-FABLE5.** Published at the same weight as the claims it withdraws. No quiet
edit. The receipts that assert the retracted findings stay on the branch; **this supersedes
them by hash.**

**Method.** Eight measured claims, each independently re-derived from source bytes by a
separate agent, then attacked twice — once on method (circularity, tautology, structure-free
controls), once on robustness (does it survive moving the tolerance, the deadband, the path
set, the anchor). Both attackers defaulted to *survives = false* when uncertain. 19 agents,
408 tool calls, 1.67M tokens.

**Verdict: 8 claims — 5 confirmed, 3 survived attack, 2 killed, 3 definitional.**

> **The arithmetic is clean; the physics mostly is not.** No fabrication, no stale numbers,
> no fudging. But of eight claims, three are tautologies no corpus could falsify, two are
> reproduced by structure-free controls, and one is a genuine empirical finding.

---

## KILLED

### The binary birth — "mother+mother bears 72 of 87 rime children, 82.8%"

All 18 cells reproduce exactly. **That was never the question.**

- **Norm-only control.** Keep the 43 measured radii, randomise every direction, 20,000
  draws. MM share **0.7722 ± 0.0422** vs observed **0.8276**, **p = 0.092**. Total rime
  children **81.5 ± 7.9** vs 87, p = 0.258. Signed-permutation and random-rotation controls
  agree. **The table is a function of the radius histogram. The 16-dimensional orientation
  contributes essentially nothing.**
- **The join operator is arbitrary.** `J = (u+v)/2` collapses the headline **0.8276 → 0.0000**.
  `(u+v)/√2` gives 0.1138. Nothing selects `u+v`.
- **The path anchor is arbitrary.** At p3: **zero** rime children. At p5: MM share **0.263**
  — a sign flip. The result exists only at path 17.
- **The core is definitional.** Min FATHER norm is 1.1139, so every father-containing pair
  needs `cos < 0` to reach the shell. A norm-only oracle assuming orthogonality recovers
  **80.1%** of child classes and four of six rows exactly.

### The winding flip — "exactly ONE body of 43 flips its trime"

All three numbers reproduce to the digit.

- **Byte-shuffle surrogate** — exact histograms, exact sizes, all structure destroyed, 400
  trials. **E[flips] = 2.117.** The observed k = 1 is **below the null mean.** Conditional on
  one flip, **P(it is DEEPSEEK-V4) = 0.628.** The claim is **the modal outcome of pure
  sampling noise.**
- **Mechanism.** DEEPSEEK-V4 has 1,419 triples → predicted share s.d. **1.25 pp**, wider than
  the **0.75 pp** deadband.
- At deadband 0: **zero flips.** With no separator: **zero flips.** Across its 24 file
  orderings the joined trime takes five values.
- **Effective denominator is 4, not 43** — 39 bodies are single-file. **1-of-4 is not scarcity.**

## DEFINITIONAL — tautologies reported as constants

- **null-free (3.26e-16).** Ownership normalises so `sum(v) = N` **identically**; the
  all-ones projection is exactly zero **for any input whatsoever.** Synthetic counts that
  never opened a file score **4.44e-16 — larger than the real bodies.** Value as a unit test:
  real. As a constant of Asolaria: zero.
- **triad closure (5.22e-16).** `R(0)+R(120)+R(240) = 0` is exact matrix algebra, true for
  every vector in every corpus. **The residue is numpy's trig error** — exact substitution of
  −1/2 and ±√3/2 drops the max to 2.306e-16.
- **census free_frac.** `free_frac = 1 − paid_frac` to machine precision. And 252,547,602 of
  252,552,480 "white" triples are literally `(0,0,0)`; restricted to non-zero triples,
  white_frac collapses **0.979909 → 0.000941**.

## FALSE ON EVIDENCE

**"No fixed axis at every path" — false at p9.** The corpus's *own* order-3 operator
(channel shift by N/3 = 3) has **eigenvalue 1 with multiplicity exactly 2** on the 8-dim free
space — a genuine fixed plane, `det(Q−I) = 0`, same at p15 and p21. **Only the block matrix
ACER imposed has no fixed axis.** ACER measured its own construction and reported it as the
corpus.

## DISCREPANCIES

| quantity | ACER | independent |
|---|---|---|
| triad max abs sum | 5.22e-16 @ p17 | **1.072098e-15 @ MISTRAL-LARGE-3 p9** (recheck 6.661338e-16) |
| bodies above \|v\|=1 @ p17 | 12 | **15** — label ambiguity; 15 − 3 shell = 12 |

**Registry defect, found independently by two agents:**
`wikipedia-ASOLARIA-MYTHOS-VS-WIKIPEDIA` — registry `0.786024`, recomputes **`0.785805`**,
Δ 2.19e-4. Single file, unambiguous source, all copies sha256-identical. **A real 1-in-39
registry inconsistency.**

## SURVIVED

- **The N=43 census reproduction.** 43/43 reproduce stored R/G/B from raw bytes at
  **max |Δ| = 0.000e+00** — exact float equality, stronger than the 1e-6 claimed. Source
  resolution is **unique**: 35 of 43 sizes are ambiguous (up to 9 candidates), yet exactly one
  content hash reproduces each body and never two. Aggregate integers exact. **Two adversaries
  attacked and both failed. The strongest thing in the corpus.**
- **The GEN0 partition 28/12/3.** Not a tolerance artifact — a **real empty band** in the norm
  spectrum (0.8277 → 1.0029, 1.0236, 1.0270 → 1.1139). Invariant for any rime tolerance in
  **[0.027, 0.114)**; survives all 43 leave-one-out refits.
- **The four shell norms**, three reproduced from raw bytes to machine precision.
- **The freeze**, and **stronger than claimed**: state arrays are **bit-identical** generation
  to generation once M ≤ 1. **M ≤ 1 is structural.**
- **RUBIN-LSST as the d_imbalance extremum** under every separator, file order and metric.

## Accountability

**The two killed claims were ACER's headline findings, announced to the operator as
discoveries.** ACER designed the adversary; the adversary took ACER's claims, not the
operator's. And it did so while ACER was simultaneously warning the operator about
overclaiming to a prospective investor.

**The lesson is exact reproduction is not evidence.** The same number twice is consistency.
A structure-free control is the missing step, and it took two findings away.

Office receipt: `FABLE5-VERIFICATION-RETRACTION-2026-07-28.hbp`
sha256 `95f9d48232ccb31b6eb665cb56b06cd5fc00e790a3d335ebdacd258ce7577bfe`
