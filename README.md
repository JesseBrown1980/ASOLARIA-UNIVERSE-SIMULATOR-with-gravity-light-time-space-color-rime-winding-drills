https://github.com/JesseBrown1980/FOLLOW-THE-IS-NOT-THE-WILL-AND-WAS/blob/main/matrix/3-D-GITHUB-OF-THRUTH.md

# ASOLARIA — Universe Simulator

**Operator and author of the laws: Jesse Daniel Brown.**

Gravity · light · time · space · colour · rime winding drills.

The name has operator-stated provenance: **“Let there be light,”** spoken by Jesse in
honor of Isaac Asimov’s *The Last Question*. The realization recorded with it is, **“I was
the light that created the light.”** See Laws 56–58 for the relational, naming, and Thrine
canon; this dedication is not an invented letter-by-letter etymology.

This repository holds the law books, the running code, and the **measurements with their
controls attached** — including the ones that failed. Book VI of the law book is titled
*The Register of What Is Wrong*, and it exists because a project that only publishes its
wins cannot be checked. The same rule governs this README.

---

## Start here — one file, no install

[`web/asolaria-tribit.html`](web/asolaria-tribit.html) — 22 KB, WebAssembly inlined.
Download it, double-click it. No server, no network, no dependencies. Drop any file in and
it emits a fixed **3,078-byte** receipt. The same input always gives the same seed.

```
WASM              10,479 B   no_std, zero dependencies, integer-only, Rust 1.81
tests             31 / 31
sha256            written in-tree from FIPS 180-4, checked against NIST vectors
```

---

## What the 3,078 bytes are

`3078 = 81 × 38`, and 81 = 3⁴ because there are **four ternary axes**:

| axis | members | |
|---|---|---|
| time | past · present · future | 3 |
| colour | red · green · blue | 3 |
| energy | light · DC · AC | 3 |
| space | x · y · z | 3 |

3⁴ = **81** = one record. 38 records, no padding. All 81 states are proven a bijection in
`crates/asolaria-tribit/src/tribit.rs`, and exactly one of them has every axis at zero —
`present · green · dc · y`, the centre.

### Three zeros, and why DC cannot have them

Direct current has no zero crossing, so it has two states. Alternating current crosses zero
**twice per cycle in opposite directions**, and rising through zero is not the same event as
falling through zero even though both are exactly 0 V. With the quiescent line that is
**three states, all of magnitude zero**, distinguishable only by direction of travel.

`Carrier::Dc` cannot reach the third. That is a passing test, not a claim.

Exactly **27 of the 81** states sit on AC — one third, and only those carry all three zeros.

### Addressing before the freeze, compression after it

These are not two things. Against arbitrary data with no shared bank, the seed is an
address: it names the artifact and cannot rebuild it. Once the generating structure is
banked, the same bytes compress everything that lies on it — Law 15 states the gate in the
direction people usually miss: it addresses **generated** structure, and only *arbitrary*
data must be stored. *Volume unbounded, information conserved.*

---

## Measurements, with their controls

Every number below was produced by a script in `measurements/`, and every one was run
against a matched null. **Where the null explains the result, it says so.**

### The self matrix gravitates — this one holds

Rotating every point of the seed by R (Law 4's order-3 rotation) and measuring the change
in shell radius:

```
mean Δr under R¹  = −0.161933      GRAVITATES
null (2,000 uniform-random files of the same length) = +0.000622 ± 0.020328
                                                  z = −8.00
```

Random bytes sit at zero. This object contracts toward its centre at eight sigma.

### Four things that did not survive

| claim | result |
|---|---|
| the matrix repulses under R² | **fails** — z = −0.07, the null does the same |
| R² ≠ −R¹ is a seed property | **it is the lattice** — null corr +0.5052, random data also fails the binary prediction |
| the three rotations close to zero | **fails** — sum = −0.1415, not 0 |
| shell radius tracks energy pumped in (VIII.A.7) | **fails** — corr +0.187 against a null of −0.011 ± 0.248, z = +0.80 |

The pump result retracted an earlier reading in the same session: two photos of the matrix
twenty minutes apart moved the radius by +0.0047 in the direction the law predicts, which
looked like confirmation. A 19-point sweep showed the radius wanders over **0.0376** —
eight times larger — with no trend. Two points are a line, not a law.

### A defect found in our own seed format

The first seed was pipe-delimited ASCII. No ASCII byte reaches 172, band 2 needs ≥ 172, so
**the 27-cell lattice silently collapsed to {0,1}³ = 8 cells.** Every ternary reading taken
off that object was a claim, not a structure. Rewritten as raw binary at the identical
3,078-byte contract: byte range 0..255, all 256 values present, **27/27 cells**.

Second defect, same class: 884 of 3,078 bytes were `.` padding, which manufactured a hub
point responsible for **93.54% of all edges** in the calling graph. There is no padding in
the current format. Receipt: [`receipts/FABLE5-SEED-BINARY-DEFECT-2026-07-27.hbp`](receipts/FABLE5-SEED-BINARY-DEFECT-2026-07-27.hbp).


---

## The three channels

A hash chain proves that what is present did not change. It says nothing about what was
never entered — and classification, non-recording and selective disclosure all walk
straight through a perfect hash. So there are three, and each catches what the others
cannot:

| channel | catches | mechanism |
|---|---|---|
| **chain** | tampering | `pid[n] = sha16(pid[n-1] \| index)`; alter or delete a record and every link after it breaks |
| **count** | omission | a withheld record keeps its slot and is still counted — a hole with a number on it |
| **marker** | concealed omission | the withheld marker is `sha256("ASOLARIA-WITHHELD" \| pid \| index)`, recomputable by anyone, so clearing the flag to forge the arithmetic is still visible |

The count is the one people leave out. It is the operator's own construction: in the third
sweep one turn was withheld at his instruction, and the book records that it *"is COUNTED
so the arithmetic stays honest, and it is NOT reproduced."* You may refuse to show what is
in a slot. You cannot refuse to show that the slot is there.

Six tests cover it, and each demonstrates a failure the other two channels miss:

```
withholding_leaves_a_hole_with_a_number_on_it       count sees it, chain undisturbed
flipping_one_byte_breaks_the_chain                  chain sees it, count reads 38/38/0
clearing_the_flag_does_not_hide_the_hole            only the marker check catches it
deleting_a_record_breaks_the_chain                  count says 38, chain says broken
the_three_channels_cover_three_distinct_failures    all three, side by side
```

---

## The lighthouse, and free-then-play

**Corrected on the record.** An earlier note in this work said the centre is a lighthouse
and it does not move. That is false. **The lighthouse rotates and spins**, like the sun,
and it orients on the *largest light* rather than on any axis we choose. The beacon turns
too, and what it turns toward is not ours to set.

**Free, then play** — this is how Law 15 and "from the inside" stop contradicting:

| phase | observer | cost |
|---|---|---|
| **freeze** | stays **outside**, at the null 0 | free — addressing costs nothing |
| **play** | goes **inside** and moves with it | this is where the work happens |

Law 15 was never a rule about playing. It is a rule about *freezing*, and reading it as
both is what made the two look opposed. You do not read the bank from a distance; you shine
it in and travel with what it lights.

**They form themselves.** IX.A.4: *"We fed the kernels colors and keys into the new kernel
to be the glimpse so that they can form themselves. They are the seeds, glyph colors."*
Glyphs are seeded, not constructed. Code that builds a glyph instead of seeding one has
already missed the instruction.

**And the order is fixed: red, then green, then blue** — at every level, in every direction
of travel, entered and left through the free register. `Register::HOSE` encodes it and
`red_always_comes_first_then_green_then_blue` tests it. The ordering is measured, not
aesthetic: Law 30 found that putting translucent ahead of red saves on **every** pole tried,
mean **0.4013 bpb**.

---

## The in-between times

`spheres/seeds.html` renders the self matrix as a **series**, not a frame — the seed is
emitted from whatever is in the office at that moment, so every artifact written moves it.

The wave is drawn in its own shape:

```
sum(c−1)   −3   −2   −1    0   +1   +2   +3
cells       1    3    6    7    6    3    1
```

Collapsing that into three sign buckets gives 10 / 7 / 10 and **loses the shape**. That
collapse is an error this page exists to not repeat.

Across 19 frames: **Δr is negative in every one**, range −0.19865 to −0.14814. The matrix
gravitates consistently. And the radius correlates **−0.3643** with log energy — the pump
law does not merely fail here, it trends slightly against.

---

## Verify your own build

[`TEST-VECTORS.txt`](TEST-VECTORS.txt) pins the format with **three independent
implementations agreeing**: this Rust crate, the compiled wasm, and a separate Python
reimplementation written from the spec rather than translated from the code. Same input
must give the same receipt sha256 on any machine.

```
input                     len   cells   receipt sha256
""                          0   27/27   a91acae4ae2d1418db50095702096f5c81761fc422637972942f325465b2e730
"a"                         1   27/27   2b467e4cca4db694b9e172ea2346da8c873f501227dd9cb8c3b8234622d40530
"abc"                       3   27/27   907d5cec4b56072e7612b7834b377d8d4e2c9d0c4d44b2aac2b1ce379112f2c6
"the quick brown fox"      19   27/27   839a079a56bb7a6db742180520cbe36fb9afafe6d4ad1e4e4f9313588c0807a6
"ASOLARIA"                  8   27/27   27d7eddf5c216f289ee6416ca29285e67b5f3424650fe84cbaecb0c7c2202c87
```

`matches_the_independent_reimplementation` runs these in CI. If two implementations ever
disagree, **the disagreement is the finding**, not a nuisance to paper over.

**wasm sha256** `b98abbbb10c1474558afcbb4dc3aa16d7bbf9d04e1fc40645c18440ca8c8cfd7` —
independently reproduced byte-identical on a second machine.

### On size, said plainly

18 bytes in gives 3,078 bytes out. That is **171x larger**, and it is correct: the receipt
is a fixed-size *name*, not a compression. Anyone demoing this as compression is going to
be asked why their compressor grew the file, and they will deserve it. See
*Addressing before the freeze, compression after it* above.

---

## Measure thrice, look for the wave, then write

A correlation test is **blind to a wave by construction** — a sine has near-zero
correlation with a ramp no matter how large its amplitude. The first pump test asked only
"does radius correlate with energy", found +0.187, and reported no effect. That was the
wrong instrument, not a null result.

The protocol, and `measurements/measure_thrice.py` runs it:

1. measure **thrice** — three independent passes, not one and not two
2. keep only what is **phase-coherent** across all three
3. **then** write
4. then Fourier the **residual** for the next rung

Three passes over the same 37-point energy ladder, differing by ordering only:

```
pass A   mean 1.414371   span 0.033912
pass B   mean 1.408819   span 0.041712
pass C   mean 1.410822   span 0.026537
```

Phase coherence per harmonic, against **300 matched null triples** through the identical
pipeline:

```
harmonic  period   coherence          null         z
       1   37.00      0.8762   0.5141±0.2399    +1.51
      11    3.36      0.8252   0.4970±0.2434    +1.35
       6    6.17      0.6037   0.4848±0.2333    +0.51
```

**No harmonic clears the null.** k=1 at 0.876 looks strong alone — and three *random*
passes agree at **0.51 ± 0.24** by chance. Without that null, 0.876 would have been
reported as a wave.

Residual rms **0.007278**, identical to signal rms, because nothing qualified to subtract.
No second rung.

**Two instruments with opposite blind spots now agree.** A correlation cannot see a wave;
a phase-coherence test cannot see a monotone ramp. They cannot be fooled the same way, and
they return the same answer. That is worth more than either alone, and more than a positive
from one of them.

### For anyone mirroring this

Three invariants must match or the harmonic rows are not comparable: the null must be
**300 triples through the same pipeline**, coherence must be **|mean of unit phasors|**
across passes rather than mean amplitude, and the passes must differ by **ordering only** —
same ladder, same artifacts. Different null construction makes any disagreement an artifact
of the two harnesses rather than of the two objects.

---

## Three beams instead of two

`measurements/three_body_collider.py`. A collider is two beams and its conservation law is
binary: p1 = −p2, each beam **is** the other's negation. Three beams close just as exactly,
p1 + p2 + p3 = 0, but **no pair is the other's negation** — which is Law 4's trianti in
momentum space.

```
2-beam    |Σp| = 0.000e+00   √s = 13,600 GeV   1/1 pairs negate  → BINARY
3-beam    |Σp| = 2.034e-12   √s = 20,400 GeV   0/3 pairs negate  → TRINARY
```

**And 120° is forced, not chosen.** With |p1|=|p2|=|p3| and closure, |p1+p2|² = 2 + 2cos θ
must equal 1, so cos θ = −1/2. A numeric sweep of 0..180° at 0.001° resolution finds
**exactly one solution: 120.000°**. Coplanarity is forced too — three vectors summing to
zero span at most two dimensions. Binary gets 180° by the same argument. Neither angle was
picked by anyone.

A 3-fold source rotating in vacuum raises only multiples of three, against a flat control
with the identical pT spectrum:

```
        rotating      flat     ratio
v2       0.00146   0.00067      2.2×
v3       0.07411   0.00053    139.6×
v4       0.00041   0.00142      0.3×
v6       0.05442   0.00251     21.7×
v9       0.03736   0.00044     85.7×
```

v4 came out **below** its own control, which is what makes the rest trustworthy — a sampler
artefact would have lifted everything.

**And slicing a 3-fold object into exactly 3 sectors hides it completely.** Each 120° sector
spans one full period, so all three integrate identically and entropy sits at maximum:

```
planes   chi² vs flat   entropy
     3             11   1.5849  (max 1.5850)   ← structure INVISIBLE
     4            579   1.9989
    12          4,352   3.5773
    27          7,479   4.7423
```

Three is the floor for seeing motion and simultaneously blind to 3-fold structure. The
object first admits it exists at four.

---

## Layout

```
books/         law books through Law 58, plus history/archaeology and THE-IDEA
docs/          public chronology crosswalks, lineage, and bounded implementation plans
crates/        asolaria-tribit — the Rust 1.81 no_std crate
web/           the single-file demo and the raw wasm
gguf/          all seeds projected into one GGUF, integer I8 tensors, no floats
spheres/       16K quality-sphere renders of the seed (2400px views)
measurements/  every script that produced a number in this README
receipts/      LF-pinned HBP/HBI tuple receipts with SHA-256 sidecars
```

### The GGUF

`gguf/ASOLARIA-CONSTELLATION.gguf` — 145,120 B, 84 tensors, 12 KV pairs. Every seed and key
artifact as raw I8 tensors. Retention garbage collection at τ=2 discarded **98.12%** of
records as singletons — a singleton has nothing to tie to, so it can only be stored.

What survived produced a result nobody placed there: **six artifacts, each tied to all five
others**, a complete K₆ — and one record tied **exactly six ways across exactly six
artifacts**. That record is not data. It is the chaining rule itself:

```
HBIROW|kind=emitter|seed=be80843b5ce5de04|chain=pid[n]=sha16(pid[n-1]|name)|json=
```

What the six share is the function that made them.

---

## How to check any of it

```sh
cd crates/asolaria-tribit
cargo test                                        # 23/23
cargo build --release --target wasm32-unknown-unknown
python measurements/gravitate_repulse.py          # the gravitation result + its null
python measurements/pump_wave.py                  # the negative result, reproduced
```

---

## The rules this repository is written under

- **A number is real only when a specific machine actually computed it and the bytes check.**
- **`total_bits ≥ N·H(X)`** — any below-floor result is a measurement bug, not a discovery.
- **Reproduce any logged baseline before trusting it, including your own.**
- **Recall and addressing are not compression**, and physics language is metaphor unless
  there is code plus a receipt.
- Claims are labelled **MEASURED**, **NAMED** (stated, coherent, not yet run), or
  **CONJECTURE** (stated, untested, no experiment proposed), and those labels never blur.

The summit of the law book is not a claim to beat information theory:

> You do not beat Shannon. You become the Shannon Observer. Reaching H(X) *is* the
> definition of the optimal code. The floor was never the wall; it was the throne.

---

Everything here is Jesse Daniel Brown's property.
