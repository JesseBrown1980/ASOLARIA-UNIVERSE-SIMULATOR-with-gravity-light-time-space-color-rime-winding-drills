# Jesse Brown's Laws of the Trijection and the 27-jection

Operator/author of the laws: **Jesse Daniel Brown.** Sealed 2026-07-21.
Every law below is **byte-exact and reproducible** — independently replicated to
the digit by outside readers. That reproducibility is not a footnote; it is the
proof. Integer-only throughout (float-drift-free; any CPU, any language, any
Rust version reproduces identical bytes).

Reference implementations (this folder):
`trijection.py` · `njection.py` · `nested_cascade.py` · `trianti.py` · `wave_test.py`

---

## Law 0 — The Center is Free
For any set of vantages that share a center, the **center (centroid) costs
nothing.** It is the fixed point of the entire symmetry group {N, R, R²} — the
one point that moves under no inversion and no anti-inversion. Only the
**separations** are paid.
*Measured:* free-center zero-trit fraction ≥ 0.90; in the wave frame **99.993%
of all energy sits in the center (DC)**, the separations are faint overtones.

## Law 1 — The Trijection, not the Bijection
Two machines in **bijection** are mutually determined and blind to one another —
they carry the same information relabeled. **Three machines with an outside
center** see what no bijection can: the **third vantage is free**, determined by
the other two plus the center (sum-to-zero). Trinary ≠ binary.
*Measured:* bijection pair transfers within **0.05 bpc** (blind); trijection on
aligned vantages saves **−3.58 bpc**, restore=OK.

## Law 2 — The 27-jection (Rule of 3, Rule of 27)
27 = 3³. **N universes sharing one omniverse-center reduce to 1 grand center +
(N−1) separations + the Nth free.** The **flat** 27-jection — one grand center,
the lowest-variance estimate of the shared signal — **beats the nested cascade.**
One outside viewer seeing all 27 at once beats a hierarchy each seeing only 3.
*Measured:* flat 27-jection **3.92×** vs nested 3.70×; both restore=OK.

## Law 3 — Reduce by as Many Machines as You Add (the 1/N amortization)
Each added universe costs **only its own separation** from the shared center. The
shared center's **per-machine cost falls as 1/N.** Spend one universe to get the
universe.
*Measured:* shared-center cost/machine **9,840 → 1.5** from 3 → 27³ machines
(a **6,600×** drop). The compression *ratio* asymptotes (~4.5×); the **per-node
substrate cost collapses without bound** — that is the scale win.

## Law 4 — The Anti-Inversion is the Trianti (order 3, and distinct)
Binary inversion is **order 2** (negation, self-inverse — its own anti). Trinary
inversion is the **order-3 rotation R**, and its anti-inversion is the **distinct
counter-rotation R² (the "trianti")** — because R ≠ R⁻¹. The three rotations
R⁰ + R¹ + R² = 1/3 + 1/3 + 1/3 **close to unity** (the pie): R · R⁻¹ = identity.
*Verified byte-exact on all 27 cells.*

## Law 5 — The Wave is the Roots of Unity (the FFT law)
**Nesting the tripling three times IS a radix-3 Fourier transform.** The three
states of balanced ternary in the complex plane are the **cube roots of unity**
{1, ω, ω²} — 120° apart, **summing to zero**, which *is* "the three separations
sum to the center." The **free center is the DC component** (k=0 Fourier
coefficient = the mean = the still point of the wave). The three rungs are the
three FFT stages; going up, free-center → 1 and separation → 0.
*Measured:* 3/9/27 roots sum to 0 (≤2.6e-15); DC = grand center exactly; rung
free-center climbs 0.900 → 0.942 → 0.963.

## Law 6 — Conservation (why it is byte-exact everywhere)
Every transform is a **lossless change of basis (rate 1.0)** — re-relation, not
sub-entropy compression. The **joint entropy of the whole system is paid exactly
once and conserved.** Nothing is created from nothing; the reduction is the
refusal to pay for the shared center N−1 extra times. **This conservation is
precisely why any machine reproduces it byte-exact** — the law travels because it
takes nothing that wasn't already there.

## Law 7 — The Shared-Center Gate (the law is falsifiable)
The reduction fires **only** when the vantages genuinely share a center —
separate universes of **one** omniverse. Independent universes (no shared center)
**do not reduce.** This gate is what makes the laws testable, and therefore real.
*Measured control:* 27 independent sources → **0.96× (expands)**, restore=OK.

---

## The one-sentence system
> N separate universes that share one omniverse-center collapse to that center
> (free — it is the DC of the wave and the fixed point of the ternary symmetry)
> plus each universe's small separation; the per-node cost of the shared center
> falls as 1/N; it is byte-exact on any CPU because it conserves the joint
> entropy exactly — spend one universe to get the universe.

Reproduce all laws: run each script in this folder. Same inputs → identical bytes.
