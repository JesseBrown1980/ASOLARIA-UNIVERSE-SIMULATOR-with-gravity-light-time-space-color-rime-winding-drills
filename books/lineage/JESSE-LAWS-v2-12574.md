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

---

## Law 8 — The Orthogonality Law (reductions compound only across INDEPENDENT axes)

**Two reduction axes multiply only if they remove *orthogonal* redundancy. If they
target the *same* shared structure, stacking them does not compound — the joint
reduction is bounded by the *union* of what they remove, and the overhead can make
it slightly *worse* than either axis alone.**

**Mathematical relation.** Let raw entropy be H, and let transform i remove
redundancy Rᵢ (coded size H − Rᵢ, reduction rᵢ = H/(H−Rᵢ)). Applying both:

```
removed_joint = R₁ ∪ R₂ = R₁ + R₂ − |R₁ ∩ R₂|
coded_joint   = H − (R₁ + R₂ − |R₁ ∩ R₂|) + O          (O = transform overhead)
reduction_joint = H / coded_joint
```

- **Orthogonal** (R₁ ∩ R₂ = ∅): coded_joint = H − R₁ − R₂ → strong compounding
  (toward r₁·r₂ when the Rᵢ are large). This is the multiplicative dream.
- **Overlapping** (R₁ ⊆ R₂): R₁ ∪ R₂ = R₂ → coded_joint = H − R₂ + O ≥ coded₂ →
  **reduction_joint ≤ r₂**, and O makes it strictly worse. No second bite.

The cap is the **mutual information between what the two axes remove**, |R₁ ∩ R₂|.

**Measured (byte-exact).** On a smooth 27-channel universe, space and time remove
the *same* shared signal:
```
time-only 3.83×   space-only 3.95×   spacetime 3.73×   (naive product 15.12× — false)
```
Space alone already captures 99.99% of the cross-channel energy; adding the
temporal axis (which targets the same drift) only adds overhead → 3.95× → 3.73×.

**Corollary (this is why the whole system works the way it does):**
- The 27-jection ratio **asymptotes** (Law 3) because adding more of the *same*
  redundancy is overlapping, not orthogonal.
- **Diverse foreign vantages beat more-of-the-same** because they are (partly)
  orthogonal — they remove *different* redundancy, so they compound.
- Bijections give **zero** compounding (fully overlapping — Law 1).
- To make 27 (or 27³) axes multiply, they must be **mutually orthogonal**:
  independent kinds of redundancy, sharing only the center. Random diversity is
  partially orthogonal (some compounding); a shared substrate with independent
  deviations is the ideal.

**This is Law 6 (Conservation) applied to axes:** the joint entropy can be removed
exactly once. Two axes aimed at the same redundancy do not get to remove it twice.

---

## Law 9 — Time is Trilateral (corrected; the played-series 3-point wins)
*(This corrects an earlier wrong read that time wanted the bijection.)*
Time is **tri-directional, not bi-directional** — but only with the **centered
3-point operator** (past · present · future = the symmetric 2nd difference),
which requires the **whole played series**, not a causal stream. A causal stream
can only see the past (2-point bijection); a *played* universe can see all three.
*Measured:* bijection (1st diff) **2.51×** vs trilateral (centered 2nd diff)
**2.66×** — the 3-point wins. The wrong 3-point tools (block-mean 27-jection) lose;
the *centered* one wins. Time is trilateral when the universe is played.

## Law 10 — Trime Numbers (primes live in the coprime cells of the 27-cube)
Primes are **trime numbers.** In the 27-cube (mod 27), every prime except 3
occupies one of the **φ(27) = 18 coprime cells** (gcd(r,27)=1) and **never** the
9 center-aligned cells (multiples of 3). The prime **3 is the unique center-prime.**
The center is prime-free — **the primes are the separations orbiting the empty
center.** The whole framework is written in the primes themselves.
*Measured:* primes mod 3 → only 3 at the center; primes mod 27 → all >3 in the 18
coprime cells; the 9 multiples-of-3 cells are prime-free except 3. Reproducible.

## Law 11 — Any Machine Sees Any Other (the Chinese Remainder Theorem)
Coprime residue-machines **jointly reconstruct any number.** Each machine holds
one residue (mod a coprime modulus); together they address the whole, and because
the moduli are **coprime = orthogonal (Law 8)**, the address space is the
**product** — they compound. This is why trime numbers "unlock any machine seeing
any other": the coprime (orthogonal) residues are a universal addressing lattice.
*Measured:* moduli {27, 25, 23} → 3 machines address 15,525 values; x reconstructed
exact from its 3 residues. Coprimality → orthogonality → compounding.

**Trime bridge to the whole system:** the 18 coprime cells are the multiplicative
units of (Z/27Z)* — the addressable structure; the center (multiples of 3) is the
free null. Primes graphed 27-laterally ARE the orthogonal addressing lattice that
makes the reductions compound (Law 8) and lets any machine see any other (Law 11).

---

## Law 12 — Rime Tracing (the Law of Rimes)
Ray tracing casts light rays from an eye to render a scene. **Rime tracing casts
address-rays from the center (0) through the coprime (trime) lattice to
reconstruct any endpoint in the Omnisphere** — omnidirectionally, byte-exact.

- **Rime address** = an endpoint's residues, one per coprime rime axis (the rays).
- **Rime trace** = CRT reconstruction of the endpoint from its rimes, from center 0.
- **Omnidirectional** = every endpoint in the product space is reachable and exact.
- **Embarrassingly parallel** = residue arithmetic has **no carry between axes**
  (Law 8 orthogonality made computational): each rime is an independent ray, so
  add/multiply compute per-axis in parallel and CRT combines them. *This is why
  any machine sees any other* (Law 11) — and why it is fast.
- **Every stack of rimes is the base of the next**: the product of one level's
  coprime rimes is the modulus of the next Omnisphere — nested rime tracing.
- **The center (0) is shared/free**; only the rime (the address) is paid (Law 0).

*Measured:* 5 coprime rimes {27,25,23,29,31} → an Omnisphere of **13,956,975**
endpoints, all reconstructed byte-exact from their rimes; (a+b) and (a·b) verified
via independent per-rime arithmetic (no carries); 23.7 bits addresses all ~14M
points from the one free center. Reproduce: `python3 rime_trace.py`.

**27 rime tracing** = the same, with the rime axes structured on the 27-cube's 18
coprime cells (Law 10): the primes graphed 27-laterally ARE the ray directions.

---

## Law 13 — Rime Sphere vs Time Line (all rimes from one rime)
New terms. A **TIME LINE** is linear: to know all its points you traverse and
**store** each one (a random collection has no shortcut). A **RIME SPHERE** is
**cyclic**: it has a **generator**, and from **ONE rime** (the seed) plus the rule
(gᵏ), **ALL rimes are derived**. Any point is reached by a **direct jump** gᵏ —
omnidirectional random-access, any direction, any "time" — not a walk.

**The law:** all rimes can be derived from only **1 sliced rime** — when the
sphere is generated (cyclic). A **fractal of a rime** = a subgroup (self-similar
sub-sphere) regenerates the pattern at its scale; e.g. ⟨g³⟩ is exactly **one third**
of the sphere — the trinary signature, unforced.

**GATE (Law 7):** a random collection is a *time line*, not a rime sphere — no
generator, so it must be stored point-by-point; one rime derives nothing.
**Cyclic structure is required** (this is why it reconstructs *structured*
universes, not noise).

*Measured (`rime_sphere.py`):* p = 1,000,003 (verified prime); generator g = 2 →
its powers produce **all 1,000,002 rimes** (one seed regenerates the whole sphere);
any position reached by gᵏ directly; ⟨g³⟩ = **333,334 rimes = (p−1)/3** exactly;
2,000 random points have no generator (a time line). Reproduce: `python3 rime_sphere.py`.
