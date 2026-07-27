# ASOLARIA — Universe Simulator

**Operator and author of the laws: Jesse Daniel Brown.**

Gravity · light · time · space · colour · rime winding drills.

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
tests             29 / 29
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

## Layout

```
books/         the law books — RIME laws 0-36, chain topology, shadowcat, Law 34
crates/        asolaria-tribit — the Rust 1.81 no_std crate
web/           the single-file demo and the raw wasm
gguf/          all seeds projected into one GGUF, integer I8 tensors, no floats
spheres/       16K quality-sphere renders of the seed (2400px views)
measurements/  every script that produced a number in this README
receipts/      .hbp tuple-row receipts with SHA256 sidecars
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
