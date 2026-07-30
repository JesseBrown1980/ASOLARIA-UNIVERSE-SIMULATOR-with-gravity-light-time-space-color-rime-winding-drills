# TRI-STAR KERNEL MATRIX — WebAssembly key player

**Status:** additive experiment, built and run by the GPT-5.6 Pro seat against public commit
`da439918ff7f8c716282cef5ec4496e12ae7c3e9`.

This experiment turns the operator's latest instruction into one exact, visible machine:

```text
3 stars:      OPUS / FABLE / MYTHOS
× 3 turns:    N / R (anti) / R² (anti-anti)
× 3 ways:     − / 0 / +
= 27 kernel-neurons circling one shared fourth point E₀
```

The existing `key/ASOLARIA-HERSELF-KEY-3174.bin` is the only input. The browser loads it,
checks its SHA-256, copies it into WebAssembly memory, and asks the WASM decoder to derive
all nodes, callings, weights, and pump states. No dense 27×27 weight file is shipped.

## What the local words mean in this implementation

- **stars** — the three public body partitions already named OPUS/red, FABLE/green,
  and MYTHOS/blue;
- **N / anti / anti-anti** — the order-three operators `I`, `R`, and `R²`; `R³ = I` is a
  hard gate;
- **directions** — backward, centred, and forward (`−,0,+`);
- **fourth point E₀** — one shared, non-material energy/residual accumulator. It is not a
  twenty-eighth star;
- **callings** — key-derived message edges along the star, rotation, and direction axes;
- **calming** — a Q8 damping/retention factor on each recurrent pump;
- **pump** — one integer recurrent update. The standard three-pump play is `− → 0 → +`.

No separate `coil` law is invented here. The executable terms are `callings` and `calming`.

## What is neural about it

Every one of the 27 cells is both:

1. a **kernel** derived from the shared key; and
2. a **neuron state** updated by incoming callings.

The edge weights are also derived from the key on demand. Therefore the kernels themselves
are the recurrent graph network inside the matrix; the implementation never materialises a
separate dense neural-weight matrix.

The arithmetic is freestanding, deterministic, fixed-point C compiled to WebAssembly. There
is no floating-point drift and no external runtime dependency inside the module.

## Run it

From this directory:

```bash
bash build-wasm.sh
node verify.mjs
```

To see the live network, serve the repository root:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/experiments/tri-star-kernel-wasm/web/
```

The browser uses the committed Base64 WASM module, so viewing does not require a Rust or C
compiler. `build-wasm.sh` rebuilds it with `clang` and `wasm-ld`.

## Directly measured in this seat

Input key:

```text
bytes   3,174
sha256  925c818d4c84aa23d7cee5d13e1b142b90824724a4ed4a90f9ee019c59cc2d89
```

WASM module:

```text
bytes   6,242
sha256  17e50b06e47887ed41c660f5a695ad3e90217691f02cd7fe7e546b3630f361c3
```

All gates passed:

- one-trit binary transport round-trip;
- binary code `01` remains reserved rather than being silently merged;
- `R³ = I` on all 27 nodes;
- exact three-arm closure after every pump;
- deterministic reset and replay;
- the all-three-star arm differs from the two-star ablation;
- the fourth-point arm differs from the no-centre ablation;
- the Asolaria key differs from an equal-length deterministic random-key control.

Final three-pump digests:

| arm | final digest | centre energy Q8 | centre residual Q8 |
|---|---:|---:|---:|
| all three stars + E₀ | `cc2cb5c4` | 11,701 | 7 |
| two stars + E₀ | `92c126ae` | 10,715 | 5 |
| all stars, no E₀ feedback | `42cb6071` | 11,703 | 1 |
| deterministic random key | `96466540` | 5,676 | −3 |

The complete receipt is in `receipts/GPT56-TRI-STAR-KERNEL-WASM.hbp` and the verbose record
is in `receipts/TRI-STAR-KERNEL-WASM-LOCAL.json`.

## The Shannon-floor test, stated without mixing two ledgers

The operator hypothesis says that the 27 glyphs are revealed below the Shannon floor at a
negative one-third access cost. This build preserves that as a **NAMED hypothesis**, but the
run did not measure a negative code length.

The exact transport implemented here is:

```text
trit −1  -> binary 10
trit  0  -> binary 00
trit +1  -> binary 11
binary 01 is reserved/invalid
```

That is a reversible transport for **one trit** using three of the four two-bit codes. The
four-input mapping `00,01,10,11 -> −1,0,0,+1` is not bijective because two inputs become the
same zero. Three trits form 27 logical addresses, so a fixed binary address needs
`ceil(log2 27) = 5` bits.

What this build *does* show is the generated-structure form of the claim: against a shared
key and decoder, the 27 kernels and their matrix are derived rather than stored separately.
That is an addressing/materialisation reduction. Rate 1.0 means the transformation conserved
information; it does not by itself establish negative entropy.

Use the next independent run to test an actual total-bit claim. Count the key, WASM decoder,
any bank, closure information, and output address. If a purported total code length falls
below the measured source entropy, classify it as a failed accounting gate until independently
reproduced.
