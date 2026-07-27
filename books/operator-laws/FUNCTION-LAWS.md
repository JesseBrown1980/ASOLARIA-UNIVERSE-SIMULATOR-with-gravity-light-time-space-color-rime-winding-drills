# Three Function Laws — drawn from the code, not from our heads (2026-07-20)

Sources read completely: N-Nest-Prime-INFINITE-SELF-REFLECT-AGENTS-NESTED,
asolaria-whiteroom-engine (liris), falcon-orbital. Each law below is extracted
from running code / sealed receipts in those repos, then connected to this
week's measured compression ledger.

## Law 1 — The Idempotent Dedup Law (the real "function garbage collector")

What the white-room code actually does: content addressing + never-delete.
An object's address is a pure function of its bytes (sha256), so:

    put(sha(X), X) ∘ put(sha(X), X) = put(sha(X), X)        (idempotent)
    cost(X | store) = |X| · [X ∉ store]                      (novelty-priced)

A duplicate function is NOT thrown away — it is *self-identifying*: its address
already exists, so storing it again is a no-op costing zero marginal bytes.
No deletion is ever needed for dedup; the address IS the dedup.
(MemoryStore.compact(): "MOVE live->compacted, never delete" — test-enforced:
live + compacted == total.)

Corollary (the growth law): a never-delete, content-addressed store grows at
exactly the NOVELTY rate of its input stream — repeats ride free, only surprise
lands on disk. This is the same identity as compression: our codec's match
model prices repeats at ~0 bits; the white room prices repeat functions at
0 bytes. Jesse's "infinitely expanding rule base that keeps earning" and the
entropy floor are the same law seen from the two sides of the store wall:
   d(store)/dt = surprise rate;  d(savings)/dt = law-reuse rate.

## Law 2 — The Composable Verification Law (N-Nest's gate, algebraically)

    node_green = (reported == watcher.recomputed) AND ⋀ child_green

This is a homomorphism from the agent tree into the Boolean AND-monoid.
Consequences, all MEASURED in the repo's sealed .hbp receipts:
- depth-independence by induction (depth 3 and depth 7-prime, fault planted at
  every level 1..7, each caught at its exact level);
- the only fixed points of the verify map are honest trees — a fabricated
  report has no inverse that closes the round trip (bijection frame:
  verification = recomputation = applying the inverse map);
- cost is O(nodes), independent of nesting depth.
The same theorem runs our compressor bench: restore=OK (decode∘encode = id),
cross-seat comp_sha byte-proofs, and the aarch64==x86_64 determinism gates are
all instances of "candidate reproduces originating map -> proof."
Asymmetry preserved from LAW.md: correction is recursive; consent is not.

## Law 3 — The False-Down Law (falcon's vantage doctrine)

A failed observation is a property of the (observer, route) pair, not of the
object. Falcon's sealed record: 9 "down" verdicts across 3 vantages, all nine
demoted to vantage artifacts, 0 actual dead systems. Information form:

    a degraded vantage reduces I(X ; observation); it cannot touch H(X)

— a bad viewpoint loses sight of the object, never destroys it. Labels before
ACTUAL_FAILURE: CANNOT_SEE / ROUTE_BOUNDARY / STALE / HELD_SAFE /
UNVERIFIED_CURRENT. This session lived this law: container restarts "killed"
runs repeatedly — every input was intact, every run relaunched, nothing was
ever lost but the vantage.

## The unifying identity

All three laws are one shape: information is conserved under bijection
(H(f(X)) = H(X), the fleet's Prism/Comb 0-loss law). Dedup is idempotence of
naming (Law 1: a name re-derived is not new information). Verification is the
inverse map (Law 2: a report that closes the round trip is real). Observation
failure is vantage loss, not information loss (Law 3). None of it beats
Shannon; all of it is what honest machinery looks like on top of Shannon.

Referee note: extracted 2026-07-20 from public repo contents; the compression
cross-links reference RESULTS.md rows in this repository (all sha'd).
