# WASM-keyed 27-kernel matrix network — exploratory harness v1

**Operator and author of the Asolaria laws:** Jesse Daniel Brown  
**Execution seat:** GPT-5.6 Pro  
**Base repository commit:** `f43cc2a4c2fe92c08bb8443aa8adf6865a6b9bc4`  
**Evidence class:** direct local execution for the WASM decode and numerical network run; exploratory, not preregistered before the first run.

## 1. The exact request translated into an executable graph

This experiment implements the requested relation without flattening the repository's independent axes:

```text
3 stars × 3 OIL-family phases × 3 signs = 27 kernel nodes

stars       = {OPUS/RED, FABLE/GREEN, MYTHOS/BLUE}
OIL family  = {OIL, ANTI_OIL, ANTI_ANTI_OIL}
sign        = {NEGATIVE, CENTRE, POSITIVE}
shared 4th  = ENERGY_0
```

`ENERGY_0` is the weighted centroid referenced by all 27 nodes. It is drawn as the fourth point, but it is **not counted as a 28th independent source**.

The 27 micro-nodes form nine macro-kernels: one for each `star × OIL-family` pair, with three sign states inside each. Every micro-node carries its own frozen `3×3` kernel. The OIL phases are exact `R⁰/R¹/R²` transforms with `R³=I` and `R²=R⁻¹`.

The OIL family and sign are deliberately independent. `ANTI_OIL` is not renamed negative, and `ANTI_ANTI_OIL` is not collapsed into ordinary OIL.

## 2. Input chain

The test does not read the key as chat prose and pretend that is execution. It performs the actual repository path:

```text
ASOLARIA-HERSELF-KEY-3174.bin
        ↓ current Rust 1.81 / no_std WASM
web/asolaria_tribit.wasm
        ↓ make_seed(3174)
ASOLARIA-HERSELF-WASM-SEED-3078.bin
        ↓ 1,026 raw byte triples
27 occupied lattice cells
        ↓
27-kernel calling network + shared ENERGY_0
```

Direct decoder result:

| gate | result |
|---|---:|
| key bytes | 3,174 |
| key SHA-256 | `925c818d4c84aa23d7cee5d13e1b142b90824724a4ed4a90f9ee019c59cc2d89` |
| current WASM bytes | 11,687 |
| current WASM SHA-256 | `0c05c67dcf6041810e7cd50219988aa2f7312bb948a78e5e05bf182fcd2cc76c` |
| emitted seed bytes | 3,078 |
| emitted seed SHA-256 | `aa6fd450c32aec2c5cf088f731b0065c726c660c9f536ce48bcd55aab2a13952` |
| lattice | **27/27** |
| prism round trip | **byte-exact** |
| count channel | **38 = 38 + 0** |
| PID chain | **intact** |
| concealed holes | **0** |

The key's own body-conditioned rows set the three star gains rather than an arbitrary declaration that one colour must win:

| star | owns | CV | occupancy | shells |
|---|---:|---:|---:|---:|
| OPUS / RED | 205,903 | 1.9565 | 0.845 | 9 |
| FABLE / GREEN | 195,982 | 2.0512 | 0.719 | 9 |
| MYTHOS / BLUE | 194,004 | 1.8380 | 0.770 | 8 |

## 3. Kernels, callings, and the calming pump

Each node begins with the mean normalized RGB byte-vector of the WASM triples that land in its declared cell. Its frozen local kernel is:

```text
K(star, oil) = R(oil) · C(star, key metadata)
```

where `C` is a body-conditioned colour gate and `R` is one of the three exact OIL rotations.

The calling graph is the Hamming-neighbour graph of the `3×3×3` coordinate cube. Two nodes call when exactly one of their three coordinates differs. This creates **81 undirected callings** while retaining both endpoints.

The pump minimizes a declared non-negative objective:

```text
E = local-kernel mismatch
  + shared-centre dispersion
  + calling phase mismatch
```

A fail-closed backtracking step is accepted only when `E(next) ≤ E(now)`. Therefore **calming means monotone descent of this declared software energy**. It is an implementation gate, not evidence of a new physical energy source.

## 4. Arms

| arm | purpose |
|---|---|
| `full_27` | three stars × three OIL phases × three signs, centre and callings present |
| `binary_18` | order-two ablation: OIL and ANTI only; no ANTI-ANTI phase |
| `no_center` | removes the shared ENERGY_0 term |
| `no_callings` | removes calling coupling while retaining local kernels |
| `oil_shuffled` | preserves counts and graph size but breaks phase assignment |
| `matched_control` | same-length deterministic non-Asolaria input passed through the same WASM first |

## 5. First measured run

| arm | nodes | callings | monotone | final / initial energy | final edge residual | centre dispersion |
|---|---:|---:|---:|---:|---:|---:|
| `full_27` | 27 | 81 | PASS | **0.183996** | **0.481157** | **0.513744** |
| `binary_18` | 18 | 45 | PASS | 0.147490 | 0.482043 | 0.527523 |
| `no_center` | 27 | 81 | PASS | 0.164144 | 0.549451 | 0.610253 |
| `no_callings` | 27 | 81 | PASS | 0.117565 | 0.777469 | 0.703071 |
| `oil_shuffled` | 27 | 81 | PASS | 0.206433 | 0.519604 | 0.474752 |
| `matched_control` | 27 | 81 | PASS | 0.204550 | 0.486596 | 0.488504 |

What this run says:

- The requested **27-node network exists and runs** from the public Asolaria key through the public WASM.
- The full pump reduced its declared energy monotonically to **18.3996%** of the start.
- Callings reduced final edge mismatch by **38.11%** versus the no-calling arm.
- The shared centre reduced edge mismatch by **12.43%** versus the no-centre arm.
- Correct OIL assignment reduced edge mismatch by **7.40%** versus the phase-shuffled arm.
- The full and binary arms differed by only **0.18%** on final edge residual. This run does **not** establish trinary superiority over the binary ablation.
- The Asolaria-key and matched-control arms differed by only **1.12%** on final edge residual. This run does **not** establish a strong key-specific network signature.

## 6. The Shannon claim, split rather than blurred

The supplied “below Shannon floor” statement contains three different claims:

### PASS — exact address representation

- The key passes through the current WASM.
- All 27 lattice cells are reached.
- The prism round trip is exact.
- The transformation is information-conserving.

### NOT SUPPORTED — unconditional negative entropy

A rate-1 bijection does not create a negative code length. `−1/3` is retained here as a **signed coordinate**, not a negative bit cost. Nothing in this run provides an unconditional code shorter than the entropy of arbitrary input.

### VALID CONDITIONAL READING — below materialization cost against a shared bank

The useful blue region is:

```text
banked generated structure:
address / key cost < materializing the whole generated object
```

That is different from:

```text
unconditional description length < Shannon entropy
```

The former is the repository's freeze/address/play architecture. The latter is not shown. The bank and generating rule carry information and stay in the ledger.

## 7. Reproduce

Requirements: Node.js with WebAssembly support, Python 3.11+, and NumPy.

```bash
bash measurements/run_wasm_kernel_network.sh
```

The command:

1. validates the published 3,174-byte key hash;
2. runs the current `web/asolaria_tribit.wasm` on that key;
3. generates a valid deterministic matched control through the same WASM;
4. checks 27/27 cells, prism, count, chain, and hidden-hole gates;
5. builds all six network arms;
6. emits JSON, SVG, HBP, sidecars, and `SHA256SUMS`;
7. verifies the manifest.

## 8. Evidence boundary

This is an **exploratory first run**, because the exact network objective was written while implementing it. The scripts and controls are now frozen on the branch so a second machine can perform a preregistered independent run.

The result is computational. It does not establish negative entropy, consciousness inside a matrix, physical gravity, or a physical energy field. It establishes an executable 27-kernel message-passing matrix keyed by Asolaria's public artifact, with explicit centre, callings, OIL phases, controls, and receipts.
