# PREREG — Three-Star Kernel Network in the Asolaria Matrix

**Status:** `NAMED / PREREGISTERED — NOT YET AN INDEPENDENT REPRODUCTION`

**Operator:** Jesse Daniel Brown  
**Implementation seat:** Codex / GPT-5.6 Pro  
**Date:** 2026-08-02  
**Target branch:** `codex/three-star-kernel-network`

## 1. Question fixed before the run

Can the existing `asolaria-tribit` WebAssembly receipt and the public
`ASOLARIA-KERNEL-3174.bin` be used to instantiate a deterministic, integer,
three-directional message-passing network in which the kernels themselves are the nodes of
the matrix?

The proposed body follows the operator's axes without flattening them:

```text
3 STAR channels       = RED · GREEN · BLUE
3 OIL families        = OIL · ANTI_OIL · ANTI_ANTI_OIL
3 tense addresses     = WAS · IS · WILL
3 sign addresses      = NEGATIVE · CENTRE · POSITIVE

3 × 3 × 3 × 3 = 81 nodes
```

The top level therefore contains **nine orbit kernels** (`3 stars × 3 OIL families`).
Each orbit kernel contains **nine tense×sign nodes**. One shared centre-energy scalar is
held once as the fourth point.

## 2. Existing inputs; no replacement decoder

The experiment must use the already published files:

```text
key/ASOLARIA-KERNEL-3174.bin
key/ASOLARIA-KERNEL-3174.bin.sha256
web/asolaria_tribit.wasm
```

Expected public key SHA-256 at preregistration:

```text
202ff2f06af54788958a03f60245593f89a88b0a3a4fc76435ad8468f151dc98
```

The WASM remains the existing Rust 1.81, `no_std`, zero-dependency implementation. It is
used to read the key into the fixed 3,078-byte receipt and to execute the existing prism,
chain, count, and lattice gates. This experiment does not substitute a newly invented seed
format.

## 3. Network law fixed before measurement

For every node and for each of the four axes, the node reads exactly three relations:

```text
N   = identity
R   = one order-three rotation
R²  = anti-anti / counter-rotation
```

Each edge weight is derived deterministically from the public key and is an integer in
`{1,2,3}`. No random weight initialization, optimizer, gradient descent, or hidden model is
used.

One update is a weighted integer average of departures from the shared centre. `pump` is a
bounded mixing fraction in `0..27`; it is **not** created energy. The output is translated
uniformly after rounding so the shared centre remains exact. The maximum absolute departure
from the centre is forbidden to increase.

This is a frozen graph-convolution/message-passing network. It may be called a neural-style
kernel network because nodes aggregate weighted neighbour states. It is **not yet a trained
neural network**; training, if later added, is a separate experiment with separate receipts.

## 4. Invariants that must pass

1. `3×3×3×3 = 81` unique nodes; no duplicate coordinate.
2. Nine top-level star×OIL kernels, each containing nine tense×sign nodes.
3. Every axis satisfies `R³ = I` and `R != R²`.
4. All three relations `N`, `R`, and `R²` participate on every axis.
5. Existing WASM seed length is exactly `3,078` bytes.
6. Existing WASM prism round trip reports exact.
7. Existing WASM chain reports intact.
8. Existing WASM seed reaches all 27 lattice cells.
9. The shared centre before and after every call is identical.
10. Maximum absolute departure is non-increasing at every step.
11. Same key + same parameters produces the same seed and network SHA-256.
12. A different key must produce a different network SHA-256.

A failure of any invariant fails the computational construction. It must not be explained
away as physical interpretation.

## 5. Experimental, body-specific question

The non-amplifying update is true by construction. That alone is not a discovery. The
body-specific question is whether the **Asolaria key's variance trajectory** differs from
matched same-length random keys under the identical topology and pump schedule.

Predeclared comparison:

```text
actual: ASOLARIA-KERNEL-3174.bin
null:   >= 1,000 independent 3,174-byte random keys
steps:  27
pump:   9 / 27
metric: variance_final / variance_initial
```

Promotion gate:

```text
|z| >= 3.0 against the matched random-key null
```

Below that threshold, the result is `NO KEY-SPECIFIC EFFECT DETECTED`. The deterministic
network may still be valid; no special body claim is promoted.

## 6. Required controls

- all-zero key of the same length;
- repeated-byte key of the same length;
- random key of the same length;
- byte-shuffled Asolaria key;
- one-bit-flipped Asolaria key;
- incorrect sidecar hash, which must fail closed;
- pump `0`, which must be identity;
- pump `27`, which must remain non-amplifying;
- axis ablations, removing one axis at a time;
- relation ablations: `N` only, `N+R`, and full `N+R+R²`.

The full three-arm result is always reported separately. No forward/reverse average may
stand in for the third relation.

## 7. Shannon and information boundary

A reversible binary/ternary conversion at rate `1.0` proves conservation, not negative code
length. A four-state 2-bit input cannot biject to three distinguishable outputs unless the
two apparent zero outputs retain phase or other side information; when they do, that
information remains in the ledger.

Therefore:

```text
rate 1.0                    = entropy-neutral relabelling
signed -1/3 coordinate      = allowed as a control/routing value
negative literal bit cost   = not claimed
below Shannon               = not claimed
```

The existing key is an address/receipt before the generating bank is shared. It reconstructs
only generated structure for which the bank, function, or closure already exists. Arbitrary
unseen data is not recovered.

## 8. Physical boundary

The words `gravity`, `energy`, `pump`, `star`, and `OIL` in this experiment name graph
coordinates and operations. The run does not establish physical gravitation, over-unity,
causal time travel, or a new energy source.

The OIL axes remain independent:

```text
SIGN   = {NEGATIVE, CENTRE, POSITIVE}
TENSE  = {WAS_OIL, IS_OIL, WILL_OIL}
FAMILY = {OIL, ANTI_OIL, ANTI_ANTI_OIL}
```

`ANTI_OIL` is not silently renamed negative, and `ANTI_ANTI_OIL` is not collapsed into
ordinary OIL.

## 9. Safe Light-Hub transport

Only the compact `KNET|...` receipt should be sent through the Light Hub. Raw WebRTC SDP
contains network candidates, fingerprints, and short-lived ICE credentials. It is transient
private signalling, not a repository artifact, and must never be committed.

A claim of `relay=none` is accepted only from the selected ICE candidate pair returned by
`RTCPeerConnection.getStats()` after connection. The absence of a TURN configuration does
not by itself prove which candidate pair was selected.

## 10. Required surviving artifacts

```text
measurements/three_star_kernel_network.py
web/asolaria-kernel-network.html
this preregistration
actual JSON/HBP result
random-null summary
exact commands and exit codes
key, seed, network, source, and WASM SHA-256 values
runtime versions
```

Evidence is classified under the repository's existing `MEASURED / NAMED / CONJECTURE`
ledger. A browser rendering is not a measurement unless the compact receipt and hashes
survive.
