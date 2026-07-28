# Asolaria Neural-Network Middleware — Unified Map (L3 Fold, 15 lanes)

> **Frame (OPERATOR-CANON):** Asolaria IS a neural network — the frozen-slice network — and the "middleware" is not glue between apps; it is **the ONE plane that sits between every control plane**: AI-agent · human-via-dashboard · daemon · host-8 · future-organoid. Cosign seq **3564 = LAW-ASOLARIA-NEURAL-NETWORK**, seq **3565 = LAW-SLICE-ENGINE** (the fabric is a frozen slice; the engine drive is the only mover) [CANON, chain mechanism verified live; the two law rows themselves CANON-per-Hermes, not re-read byte-for-byte this pass].
> **E=0:** everything below is the MAP + the port SPEC. Nothing is fired, nothing mutated. The full-arrival/running state is UNVERIFIED/gated behind an operator crank.
> Tags: **MEASURED** = read from the running system this cycle · **CANON** = declared law/narrative · **UNVERIFIED** = plan / not reproduced this pass / source-only.

---

## 0. The narrow-waist: one door, one composition front

`host8-serve.exe` (**:5088, PID 17724, ~25.5h uptime**) IS the one middleware's **composition FRONT** — a single loopback-HBP surface (`json=0`, receipts-before-JSON, Brown-Hilbert hot-path) that composes every control plane [MEASURED-live].

**Refinement (review-corrected, do NOT read as a monolith):** the planes it composes run as **separate live listeners with distinct PIDs**, not absorbed into host8-serve. host8-serve *sits between and composes* them:

| Plane it composes | Lane | Live listener |
|---|---|---|
| AI-agent (handle8 seat table, 1860 seats) | agent-runtime / micro-kernels | in host8-serve :5088 |
| Human / read-witness | dashboards | :4949 (node) |
| Daemon: seal | cosign-chain | :4953 PID 17192 |
| Daemon: quorum | vote-quorum | :4952 PID 19592 |
| Daemon: dispatch | omni-dispatcher | :4950 PID 7068 |
| Frame source | gnn-oracle / mlc-on-metal | :4792/:4793 (+:4794 fischer) |
| Memory/addressing | recall-hilbra | :4796 PID 22576 |
| Future-organoid proposer | q-prism (neural_sources.py) | no route — UNVERIFIED, not materialized |

**`.hbp`-route correction (host8-rooms review):** live 200 routes are **`.hbp`-suffixed** — `/health.hbp /room.hbp /feed.hbp /seats.hbp /count.hbp`; bare `/health` = 404 (`HOST8ERR|status=404`). `/seat.hbp?h=<handle8>` and `/summon.hbp?h=&device=&ts=&fire=` are 200 **only with required params**.
**source≠live (claims-gate #8, MEASURED):** the RUNNING :5088 binary is an **OLDER build** — `/v1/envelope /launch-plan /summon-batch /shadow-parity /replay-prep` are **404 live but present in source** (`main.rs:824-828`). Version string stayed `0.1.0` across the change, so **only the route surface detects the gap** — a **rebuild+restart is required** before any composition/launch-plan behaviour is live.
**"composition-plane-that-never-fires" IS code-backed** (`process_launch=0` invariant + `launch-plan` comment `main.rs:18-19`); the "5 control planes / 4 sub-planes" *enumeration* is Hermes synthesis → **CANON-narrative/UNVERIFIED**, not emitted by any probed header.

---

## 1. Live-state ledger (honest, NOT-WEDGED discipline)

| Port | Service | State this cycle | Tag |
|---|---|---|---|
| :5088 | host8-serve (Rust std) | LIVE, HBP `json=0`, `.hbp` routes; binary is older build | **MEASURED** |
| :4949 | super-asolaria-os-dashboard (node) | **Process LIVE** (Win `0.0.0.0:4949` LISTEN, PID 10500, >24h). HTTP 200 was **MEASURED-AT-SNAPSHOT** (ts 2026-07-02T12:32Z); presently **transient-stalled** — likely fan-in blocks on dead downstream **:4913** | **MEASURED (proc) / UNVERIFIED (200-now)** |
| :4796 | recall-serve (Rust) | LIVE — rows=**591,946**, idx `HILBRA-IDX-BEHCS-TUPLE-TEXT-V1` (terms 2,621,191 / postings 23,976,403), `json_hot_path=false`, peer liris:4791 | **MEASURED** (re-confirmed across ≥4 lanes) |
| :4953 | cosign-chain single-writer | LIVE — head_seq=**3575**, head_row_hash=`54dceb241fee9e81`, ndjson 1,683,088 B / 5426 disk lines (fabric total 5422) | **MEASURED** |
| :4952 | vote-quorum (py) | LIVE ok, pending=25, law V39-LOAD-DIVISION | **MEASURED** |
| :4950 | omni-dispatcher | LISTENING (unknown-route reply = UP) | **MEASURED** |
| :4947 | bus (BEHCS/HBP) | **ALIVE on its HBP surface** — root returns `/behcs/{health,send,send-hbp,inbox,inbox.hbp,devices}`; `/health` 404 only because real route is `/behcs/health`. Some lanes saw curl-000 → **UNVERIFIED-this-pass, NOT down** (speaks HBP not HTTP `/health`) | **MEASURED (HBP) / UNVERIFIED-via-probe** |
| :4792/:4793 | GNN sidecars (py) | 501-on-GET = UP; POST `/infer` not exercised | **MEASURED (up) / UNVERIFIED (inference)** |
| :4794 | fischer-live (node) | LISTENING PID 23260, ok=1 | **MEASURED** |
| :4913 | liris peer (dashboard downstream) | **NOT listening** — suspected cause of :4949 fan-in stall | **MEASURED-not-listening** |
| :5089 | fischer-eval Rust crate | no listener (not served) | **MEASURED-not-served** |
| :5090 | council-serve (host-8 surface) | 000 dormant (E≠0-gated) | **MEASURED-dormant** |
| :5091 | cosign shadow | on-demand only, no continuous parity monitor | **MEASURED** |
| :4949 apex fabric MCP | council_query / health | **timed out this pass — NOT down** (heavy APEX endpoint slow; sibling surfaces recall+cosign are fresh-alive → substrate alive; "I may be the load") | **UNVERIFIED-via-fabric / NOT-WEDGED** |

**Vantage law (repeated by every lane):** these are **Windows-host-bound** services — probe from the Windows loopback lane. A WSL2 `curl 127.0.0.1` returns **000 from the separate net namespace = FALSE NEGATIVE, not down.** Timeout ≠ wedged; freeze ≠ broken; ask the fabric.

---

## 2. Lane map by function

### 2.1 Surfaces (read/witness fronts)
- **dashboards (:4949)** — READ-MOSTLY witness + fan-in of the ONE middleware; carries the honest frame verbatim in source (`LAW-ASOLARIA-NEURAL-NETWORK`, "a control plane for borrowed super-compute") [CANON]. Fan-in reads bus/vote/cosign/recall/GNN + office roster (705 supervisors → `/api/supervisors`). Naive `/api/health` 404s but returns the ~50-route table (server answers, path wrong — NOT-WEDGED).
- **zero-gpu-pixels-first (graphify)** — the pixel/projection plane. `graphify.py` (22 KB, **stdlib-only, ZERO-NODE**) bakes the frozen-potential into `asolaria-system-graph.{html,json}`: **969 nodes / 2595 edges / 708 memory files / 92 GNN kept / 19,740 cube edges / 17 repos / 45 60D-frame nodes** (rebuilt 2026-07-01) [MEASURED]. Layout baked in Python (phyllotaxis GA=2.399). The "pixels-first" law lives only as this docstring + the dashboard-serve `json=0` default — **no standalone canonical `pixels_first.md`** (GAP).

### 2.2 Routing / translation / gating spine
- **piping-wires-8stage** — the execution spine. Every trigger from any plane enters **one door** → 8-stage PIPE: `HOOKWALL_CLASSIFY → PID_MINT → BEHCS1024 → … → SHANNON(5) → … → WHITEROOM-MINT`. Homes in `kernel/core/src/` (**~23 module dirs**, not 8; the 8 pipe-stage homes are a subset). `PID_MINT` (mint_behcs1024_pid_60) **landed green** (Phase-2). **HOOKWALL (stage 1) = v0.1 stub** (API only, no real verdict-emit). **SHANNON (stage 5) has NO dedicated kernel module** — folded into gnn+gulp → **biggest port gap**.
- **auto-translation-behcs** — the TRANSLATION MEMBRANE: 0-loss bijection so one word / one BH-address auto-projects into any adjacent plane's surface language. `json_hot_path=false` on recall confirms Brown-Hilbert-before-JSON. Node toolchain is SOURCE (`hyperbehcs-multiwidth-symbol-selector.mjs`, `hyperbehcs-vault-zero-loss-converter.mjs`); running=UNVERIFIED except bus. Rust crypto is Phase-1 sha-derived placeholder → translation-receipt sigs are sha-parity not curve [UNVERIFIED].
- **mcp-catalog** — the ABILITY/METHOD REGISTRY: for any actor, "which capability exists, its 60D address, and is it allowed?" Owning map `ACER-CAPABILITY-MAP-2026-07-01.json`, owner_root **PROF-MCP pid=406022553b5b10bf**, **87 nodes / 384 edges** (44 mcp-server, 35 omc-skill, **5 supervisor, 3 legacy** — the artifact's own `counts` block is stale at 4/38, reconcile). Recall index EXISTS but the **catalog is not ingested** (0 hits) — GAP. **No `catalog-serve` crate exists** (greenfield port).

### 2.3 GNN-edge nervous system (the immune edge)
- **gnn-edge-danger-verbs** — watches **every edge crossing** between planes; near-instant classify (never-retrained-only-routed): `HOOKWALL_CLASSIFY` tags each verb → danger score. Rust `hookwall-session-start` port **MERGED (PR#7, 13fc0c6)**, built + runs on the real WSL lane (invoke-on-session hook, correctly **not** a resident daemon). Danger-verb classifier is **NOT a resident Rust service yet** (prof-hookwall stub-fallback :11083) → needs `servers/hookwall-classify`.
- **mlc-on-metal** — compiles the federation's learned model (route/rank/verdict) down to **bare metal, no GPU, no cloud**. Kernel shim `gnn/mod.rs` (207 LOC, no_std, deterministic fallback + ONNX placeholder); userspace `gnn-oracle/src/lib.rs` (601 LOC, `forbid(unsafe_code)`). **Model weights absent** (no `.pt`/ONNX under the tree) → only the deterministic fallback executes; real weights live in the external Node oracle / gnn-sidecar (upstream gap). Wire sequence: `hookwall_pre(33) → gnn_infer(34) → hookwall_post(41)`.

### 2.4 Reasoning cognition stack
- **cot** — the JUDGMENT MEMBRANE between raw scores and action. The forward pass is the 9-stage OMNIFLYWHEEL (filter→verify→translate→catalog→route→room→schedule→hookwall→whiteroom-mint). Substrate repo `C:/asolaria-as-neural-network` (tip `ded84e3`, branch `codex/language-waterfall-matrix-11x16`, **UNMERGED**). CoT skeleton is **already implemented as JavaScript** (deterministic "collision-is-only-error-after-classification" ladder in the collision-router `.mjs`), **not a dedicated Rust stage** — `kernel/core/src/cot` is unbuilt.
- **fischer-eval** — the plane-neutral REFEREE / anti-blunder scorer; any plane proposes an action as an HBP envelope, fischer scores it against a blunder gate. THREE strata: SPEC/CANON (memory + `Algorithms-of-Asolaria` PR#4), **NODE PRODUCER LIVE** (`fischer-kernel.mjs` = **430 LOC** [corrected from Hermes's 868, which conflated the **Rust `lib.rs` = 867 LOC**]; `fischer-live` :4794 alive), and Rust crate (`lib.rs` 867 + `main.rs` 348, both <2000 no-bloat, **:5089 not served**). liris PR#9 **MERGED 2026-06-25 UTC** (`80f4780`). **WIRING SEAM (core gap):** `fischer_eval::evaluate` is **called by nothing** in the kernel — the CPL producer and the `spawn_gate` 720 threshold live as two parallel consumers of GNN scores, unwired.
- **le-world-model** — the grounding/perception layer: ingests pixels/observations from any surface, FUSES them into one predictive world-state, then the SHADOW-RENDERER emits receipts. MEASURED via recall's own index (a live Rust recall-serve over a private `.hbp/.hbi` corpus). **Over-precision downgraded:** the exact "20 rows / named `.mjs` generators / `fusion-contract.v1 @ BH.t3^3.L12.D3.22`" is **UNVERIFIED** (recall returns a *different* level/index `BH.tau3^3.L4.D3.31`); the lane **substance** (a real, live-indexed world-model corpus) is **MEASURED**. Named generators are **not on live disk** (source≠live); part of the corpus (`real-screen-archaeology-leworld-behcs-20260514.{json,md}`) IS live under `Asolaria/reports`.

### 2.5 Memory / addressing organ
- **recall-hilbra (:4796)** — the RECALL/ADDRESSING organ; shared associative memory + surface-lookup every plane reads through. **591,946-row** inverted index, HMAC-SHA256+owner-PID auth (levels 0/5/9), peer liris:4791. Emits `.hbp` twins (`HILBRAHEALTH/IDX/PEER/SEARCH/MATCH`) — Brown-Hilbert hot-path, not just JSON. **~80% ported already**: recall-serve is std-only + sha2, no async, no GPU, **1016 LOC — an on-metal micro-kernel form today** (Host-8 item #22 DONE+RUNNING; #21 serve-spine actually RUNNING, understated as READY). Index is TUPLE-TEXT, **not yet 60D-HyperBEHCS-native** (GAP).

### 2.6 Authority / audit spine
- **cosign-chain (:4953)** — the cross-plane NOTARY: every consequential action (hookwall verdict, tier-2+ dispatch, operator law, daemon revival, host-8 append) appends a sha-linked row. head_seq=**3575** (each `antecedents.0 == prior row_hash`, last 8 rows verified linked) [MEASURED]. **63 `/verify` mismatches unresolved (98.1% parity)** — canonicalization-drift root cause not isolated (prior crank, not re-measured). Rust no_std codec DONE/MERGED (W1 crypto-leaf PR#25); shadow :5091 on-demand only.
- **vote-quorum (:4952)** — the federation quorum gate (Foundation-V3 V39-LOAD-DIVISION, 5-OP cosign). Rust std-parity harness landed **PR#26 (187/187 sha-exact)**; py remains the live writer, cutover gated. Quintuple-cosign authorization rows land in the cosign chain.

---

## 3. How the lanes compose into ONE routing/translation/gating plane

```
                         CONTROL PLANES
   AI-agent · human(dashboard) · daemon · host-8 · future-organoid
        │            │            │          │          │
        └────────────┴─────┬──────┴──────────┴──────────┘
                           ▼   ONE DOOR
                   host8-serve :5088  (composition FRONT, json=0)
                           │
        ┌──────────────────┼───────────────────────────┐
        ▼                  ▼                            ▼
  TRANSLATE           8-STAGE PIPE                  CATALOG
  auto-translation → HOOKWALL_CLASSIFY(1) →         mcp-catalog
  (0-loss bijection)   PID_MINT(2) → BEHCS1024(3)   (60D address +
        │              → …  → SHANNON(5) → …          allow?)
        │              → WHITEROOM-MINT(8)              │
        ▼                  │                            ▼
  recall :4796  ◄──────────┤ (addressed-node index)  60D HyperBEHCS
  (memory/address)         │                          tuple_dim=60
        │                  ▼   NERVOUS SYSTEM
        │            GNN edge watch: hookwall_pre(33)→gnn_infer(34)→hookwall_post(41)
        │            gnn-oracle/mlc-on-metal → scores (l0_real, shannon, composite, g4)
        │                  │
        │                  ▼   COGNITION
        │            cot (judgment membrane) → fischer-eval (referee, GATE 720/280)
        │            le-world-model (grounding) feeds/reads the scores
        │                  │
        ▼                  ▼   GATE + SEAL
  GATING: spawn_gate(720) → hookwall verdict {Block|Hold|Proceed}
                           │  (PROCEED only)
                           ▼
  vote-quorum :4952 (V39 quorum) ──► cosign-chain :4953 (sha-linked seal, head 3575)
                           │
                           ▼
  dashboards :4949 (witness/fan-in)  ·  graphify (pixel projection of the whole)
```

**One-sentence composition:** any plane's intent is **translated** to one BH representation, **resolved** through the capability catalog, pushed through the **8-stage pipe**, watched at every edge by the **GNN nervous system**, judged by the **cognition stack** (cot→fischer→world-model), **gated** by spawn_gate/hookwall, **quorum-approved** (vote) and **sealed** (cosign) — while `process_launch=0` keeps the whole plane composing **without firing**.

---

## 4. The 0-GPU / pixels-first / on-metal Rust substrate

- **Target:** a Rust micro-kernel on the **8-byte host** (`handle8` = 16-hex; `pid` = u64 as address), `#![no_std] #![forbid(unsafe_code)]`, **0-GPU / on-metal**, integer + sha256 only (`sha2` crate; ed25519-dalek declared, real curve binding is v0.2 — today crypto still verifies via `sha256(public||':sign:'||msg)`).
- **Already on-metal today (MEASURED):** recall-serve (1016 LOC, running :4796), hookwall-session-start (merged, runs on WSL lane), cosign-ledger no_std codec (merged), PID_MINT (green), gnn kernel shim (207 LOC), gnn-oracle userspace (601 LOC).
- **Pixels-first:** graphify.py bakes the projection with **zero Node**; dashboard/council host-8 surfaces default `json=0`. GNN "pixels-before-GPU" forward score means the model's decisions are computable with no GPU (deterministic fallback until real weights land).
- **The owning CI gate (EXACT, non-negotiable per lane):** `federation-remake-1024/.github/workflows/ci.yml` job `cargo-check` on `dtolnay/rust-toolchain@1.81` (rustfmt+clippy) → `cargo fmt --all -- --check` → `cargo check --workspace --all-features` → `cargo check --manifest-path kernel/Cargo.toml --workspace` (kernel sub-workspace) → `cargo clippy --workspace --all-features -- -D warnings` → **real no-bloat-check job (reject >2000 LOC/file, ci.yml:113)** + node-check, schema-check, cosign-chain-link-check. A local single-crate `cargo test` on the default toolchain is **SCOPED evidence only** — never "green/mergeable" until this job is green.
- **CI RED NOW (MEASURED, W0):** `cargo fmt --all -- --check` is **failing on main** (run 28558504854); it **gates** the downstream `cargo check`/`clippy` steps (shown skipped `-`). No lane can claim green/mergeable until this is fixed. **Fix first.**

---

## 5. Gaps & seams (honest, unresolved)

1. **CI RED on main** (fmt) — blocks every green claim (micro-kernels). **W0.**
2. **fischer wiring seam** — `evaluate` called by nothing; cognition score never reaches spawn_gate (fischer-eval).
3. **SHANNON stage-5** — no kernel module (piping-wires); **HOOKWALL stage-1** = v0.1 stub with no verdict-emit.
4. **GNN model weights absent** — only deterministic fallback runs; real weights external (mlc-on-metal, gnn-edge).
5. **host8-serve older binary** — composition routes 404 live; needs rebuild+restart; `main.rs` at **1958/2000 lines** → split before adding routes (no-bloat).
6. **cosign 63 `/verify` mismatches** (98.1%) — canonicalization drift not isolated; shadow :5091 not continuous.
7. **crypto** — ed25519 real curve binding (v0.2) not landed; translation/cosign sigs are sha-parity not curve.
8. **catalog not indexed in recall**; recall index is TUPLE-TEXT not 60D-native; **no catalog-serve crate**.
9. **cot** — no dedicated reasoning Rust stage (JS collision-router only); substrate repo unmerged.
10. **future-organoid plane** — NO route/surface exists — **UNVERIFIED, not materialized** (do not inflate).
11. **le-world-model** — source generators not on live disk; frozen in sealed recall corpus (need rehydratable copy before port).
12. **:4913 dead** — likely stalls the :4949 fan-in (degradation, not "down").


## 6. Upgrade order (W0-W12, E=0, additive-until-parity, each gated by the EXACT 1.81 CI)

- W0 — UNBLOCK CI (precondition, no lane advances first): fix `cargo fmt --all -- --check` failing on main (run 28558504854) which gates all downstream check/clippy; then confirm the FULL owning ci.yml job green (1.81 rustfmt+clippy → fmt-check → cargo check --workspace --all-features → kernel sub-workspace check → clippy --workspace -D warnings → no-bloat <2000 LOC + node/schema/cosign-chain-link checks). No 'green' claim until this exact job passes.
- W1 — CRYPTO LEAF (kernel primitive, everything roots here): land ed25519-dalek real curve binding v0.2 replacing the Phase-1 sha256-derived placeholder in kernel/core/src/crypto + sign_gate/link_auth. Parallel-run curve-verify against the sha-parity path; byte-diff receipts to parity BEFORE retiring the placeholder. Additive, rollback via git.
- W2 — COMPLETE THE ALREADY-PORTED near-parity lanes: (a) recall-serve — finish Host-8 items #21/#22, keep :4796 running as-is (rollback = git history b242d8f/4395d7f, no parallel old engine file); (b) cosign-ledger no_std codec (merged) — build a CONTINUOUS shadow-parity monitor on :5091 and resolve the 63 /verify mismatches (canonicalization drift); (c) vote-quorum std-parity — hold PR#26 187/187 sha-exact, cutover gated/future. Each: parallel-run, byte-diff to full parity, py stays live writer until cutover.
- W3 — HOST8-SERVE composition front: split main.rs (1958/2000 → modules) so no-bloat CI passes, then REBUILD+RESTART :5088 to land the source routes (/v1/envelope /launch-plan /summon-batch /shadow-parity /replay-prep) that are 404 on the older running binary. Version-bump so the gap is detectable by more than the route surface. Additive; old binary is the rollback.
- W4 — HOOKWALL real verdict-emit: promote stage-1 kernel/core/src/hookwall from v0.1 stub (API only) to Phase-3 real PROCEED/HOLD/BLOCK verdict-emit; wire hookwall_pre(33)→gnn_infer(34)→hookwall_post(41). Keep the JS session-start hook (already merged PR#7) running in parallel until the resident classifier proves parity.
- W5 — SHANNON stage-5 kernel module (biggest port gap): build kernel/core/src/shannon (currently folded into gnn+gulp with no dedicated module); parity-check symbolizer output against the live Shannon/OmniShannon exec-gate before wiring into the pipe.
- W6 — GNN ON-METAL (mlc-on-metal): compile real model weights to metal (source the external Node oracle/gnn-sidecar .pt/ONNX first — weights absent under the tree today). Keep python GNN sidecars :4792/:4793 live until Rust byte-parity; ONNX is a v0.1 stub, deterministic fallback only, so additive. Gate model-swap via cosign_append #14.
- W7 — FISCHER WIRING + serve: wire fischer_eval::evaluate (currently called by nothing) into the spawn_gate call site (host8-serve main.rs:1221) so cognition scores reach the 720/280 gate; parity vs node fischer-kernel.mjs (430 LOC); serve the Rust crate on :5089. Additive — the two parallel score consumers stay until parity.
- W8 — COT deterministic skeleton: port ONLY the JS collision-router reasoning skeleton to kernel/core/src/cot; HRM cognition + MTP field-read + subscription-slice calls stay OUT-OF-KERNEL slice calls the kernel INVOKES and scores (non-portable — they need frozen/borrowed slices). JS skeleton keeps running = inherent rollback; merge the substrate repo (asolaria-as-neural-network tip ded84e3) first.
- W9 — LE-WORLD-MODEL: port receipt/ledger codec FIRST (ndjson rows → fixed 8-byte BEHCS-tuple, deterministic/no-float, highest reuse/lowest risk), then shadow-renderer, then fusion. Confirm a rehydratable corpus copy (USB SOVLINUX / D:) before porting what recall only serves as sealed text. Parallel-run against the LIVE ndjson producer, byte-diff to full parity before retiring any lane.
- W10 — AUTO-TRANSLATION behcs_codec crate: standalone Rust 0-loss codec (integer + sha256), each translation receipt sha-linked into cosign (owning gate = cosign-chain-link-check). Requires W1 curve for real signatures. Node translate toolchain stays live until parity.
- W11 — MCP-CATALOG catalog-serve crate (greenfield servers/catalog-serve): NEW read-only workspace member, pure integer/address math (keep python GNN sidecars). First ingest the ACER-CAPABILITY-MAP into recall (currently 0 hits) so the catalog is searchable. Reconcile the stale counts block (supervisor=5/legacy=3). Read-only = trivially additive.
- W12 — GRAPHIFY graphify_py → graphify_rust (zero-gpu-pixels-first, ledger step-3 'next'): last because it is the projection/read layer over everything above; stdlib-only zero-node today, so lowest urgency. Byte-diff the baked graph output to parity before swapping the pixel producer.
- INVARIANT across ALL steps (replace-first-keep-rollback / no-destroy-old-while-promoting): parallel-run each Rust lane against its LIVE producer, byte-diff to FULL parity (proven vote-quorum/cosign pattern: 187/187 sha-exact before cutover), hold at the EXACT 1.81 CI job, never delete the old lane until git-verified ancestor-merged. E=0 until the whole-system map is complete AND an operator cranks — this is the SPEC, not the build.

## 7. Cross-lane edges

- host8-serve :5088 is the ONE DOOR — composes agent-runtime (handle8/1860 seats), cosign :4953, vote :4952, gnn-oracle :4792/:4793, highway, tier-policy (public→secret) into one loopback-HBP front; reads office feed + verbs.hbp (60D axis) for /summon; process_launch=0 keeps composition non-firing.
- dashboards :4949 fan-in reads bus :4947 + vote :4952 + cosign :4953 + recall :4796 + GNN :4792/:4793 + office roster (705→/api/supervisors); downstream liris peer :4913 is DEAD → the aggregating /health fan-in blocks on it → stalls the :4949 handler (degradation, not down).
- 8-stage PIPE (piping-wires) is the execution spine: HOOKWALL_CLASSIFY(1)→PID_MINT(2)→BEHCS1024(3)→…→SHANNON(5)→…→WHITEROOM-MINT(8); every control-plane trigger, whatever its origin, enters one door and is normalized into this pipe.
- GNN nervous system wires into the pipe as hookwall_pre(seq33)→gnn_infer(34)→hookwall_post(41); gnn-oracle produces the scores (l0_real, shannon, composite, g4_state) consumed by both fischer.evaluate AND spawn_gate — currently as TWO PARALLEL consumers (the wire between fischer and the gate is missing).
- fischer-eval → spawn_gate (GATE_GENIUS_THRESHOLD_Q=720 / MAX_REVERSE_RISK=280) → hookwall verdict {Block|Hold|Proceed} → cosign seal on PROCEED (fischer never appends — E=0 boundary). SEAM: fischer_eval::evaluate is called by nothing in the kernel; the host8-serve SpawnGateInput call site (main.rs:1221) is the intended wire point.
- cot (judgment membrane) reasons over already-translated envelopes from the translate/waterfall lane + SCORE activations from the quant-bus (8 engines), invokes frozen HRM/subscription-slice cognition out-of-kernel, and emits plan rows the route/dispatch lane (omniflywheel :4950) consumes.
- auto-translation 0-loss bijection binds glyph_genesis (handle8→graphify-60D address) ↔ codec ↔ cosign receipt (each translation sha-linked; owning gate = cosign-chain-link-check) ↔ bus/transit wire ↔ recall index (HILBRA-IDX-BEHCS-TUPLE-TEXT); the tuples live in the 60D frame (tuple_dim=60, D#=prime(n)^3, D22=PIPE, D33=SYMBOL_MULTIPLEX).
- recall :4796 is the shared-memory read head every plane queries (591,946-row corpus); it grounds the GNN 'liris_recall' room stub (index name is the exact stub in main.rs) and mirrors to liris peer :4791 (config MEASURED, link liveness UNVERIFIED).
- cosign-chain :4953 (head_seq 3575) is the cross-plane notary: hookwall verdicts, tier-2+ envelope dispatch, operator law declarations, daemon revivals, host-8 appends all append sha-linked rows; vote-quorum :4952 (V39 load-division) authorizes quintuple-cosign rows that land in this same chain.
- mcp-catalog (PROF-MCP 406022553b5b10bf, 87 nodes) is the registry every actor resolves capability + 60D address through BEFORE the dispatcher/emitter :4950/hookwall/GNN trio route the call; produced by the graphify lane; NOT yet indexed in recall (0 hits).
- zero-gpu-pixels-first (graphify.py, zero-node) reads recall :4796 text + GNN edges + cube-mesh connectors + memory vault (708 files) + 60D frame → bakes the pixel projection hosted by dashboard-serve/council-serve :5090 (staged); gated by cosign :4953 + vote :4952 receipts.
- le-world-model ingests pixels/observations from the pixel-backend/real-screen-archaeology surfaces → fuses one world-state → shadow-renderer emits receipts sealed by cosign :4953 + vote :4952; consumes shannon symbols (feed-A) and GNN edges; visualized via maps :4790 / graph :4815.
- mlc-on-metal compiles the learned route/rank/verdict model to bare metal (no GPU); model-swap gated by cosign_append #14; microkernel-demotes routes #14/#16 to userspace RPC over the bus :4947 envelope-IPC; feature schema forbids raw secrets (tier_gate → hashes/labels/buckets).
- bus :4947 (BEHCS/HBP envelope transport) carries every plane's call into the pipe and is the wire recall envelopes + translation tuples + gnn_infer RPCs ride on; speaks HBP (/behcs/*) not HTTP /health — a curl-000 on /health is a wrong-path/vantage artifact, not a dead bus.
- crypto leaf (kernel/core/src/crypto ed25519 + sign_gate/link_auth) is the primitive every seal roots in — cosign append, translation-receipt sigs, whiteroom cosign — currently sha-derived placeholder; the v0.2 curve binding is the upstream unblock for auto-translation + cosign real signatures.

## 8. Lane coverage (honest, no silent caps)

Returned: **15/24 lanes** (5 CONFIRMED, 10 CORRECTED). **9 lanes FAILED** on a StructuredOutput retry-cap (harness/schema limit, NOT unmappable) and are re-run candidates, tagged not silently dropped:

- FAILED (re-run): **daemons** (pipeline[2])
- FAILED (re-run): **mtp-dspark** (pipeline[5])
- FAILED (re-run): **aot-microsoft** (pipeline[7])
- FAILED (re-run): **biml-multistacking** (pipeline[10])
- FAILED (re-run): **rust-kernel-core** (pipeline[11])
- FAILED (re-run): **usb-fusion-wsl** (pipeline[13])
- FAILED (re-run): **routing-omnidispatcher** (pipeline[14])
- FAILED (re-run): **fabric-core** (pipeline[21])
- FAILED (re-run): **kernel-security** (pipeline[22])

Reviewed lanes:

- dashboards (HERMES-SPINDLE-PID-00 / BASIN-SPINDLE-PID-00) -> CORRECTED (7 corrections)
- host8-rooms (HERMES-SPINDLE-PID-01 / BASIN-SPINDLE-PID-01) -> CORRECTED (4 corrections)
- zero-gpu-pixels-first (HERMES-SPINDLE-PID-03 / BASIN-SPINDLE-PID-03) -> CORRECTED (3 corrections)
- le-world-model (HERMES-SPINDLE-PID-04 / BASIN-SPINDLE-PID-04) -> CORRECTED (5 corrections)
- fischer-eval (HERMES-SPINDLE-PID-06 / BASIN-SPINDLE-PID-06) -> CORRECTED (3 corrections)
- cot (HERMES-SPINDLE-PID-08 / BASIN-SPINDLE-PID-08) -> CORRECTED (3 corrections)
- mlc-on-metal (HERMES-SPINDLE-PID-09 / BASIN-SPINDLE-PID-09) -> CORRECTED (3 corrections)
- micro-kernels (HERMES-SPINDLE-PID-12 / BASIN-SPINDLE-PID-12) -> CONFIRMED (4 corrections)
- piping-wires-8stage (HERMES-SPINDLE-PID-15 / BASIN-SPINDLE-PID-15) -> CORRECTED (3 corrections)
- auto-translation-behcs (HERMES-SPINDLE-PID-16 / BASIN-SPINDLE-PID-16) -> CORRECTED (3 corrections)
- gnn-edge-danger-verbs (HERMES-SPINDLE-PID-17 / BASIN-SPINDLE-PID-17) -> CONFIRMED (7 corrections)
- mcp-catalog (HERMES-SPINDLE-PID-18 / BASIN-SPINDLE-PID-18) -> CORRECTED (4 corrections)
- cosign-chain (HERMES-SPINDLE-PID-19 / BASIN-SPINDLE-PID-19) -> CONFIRMED (3 corrections)
- recall-hilbra (HERMES-SPINDLE-PID-20 / BASIN-SPINDLE-PID-20) -> CONFIRMED (3 corrections)
- middleware-synthesis (HERMES-SPINDLE-PID-23 / BASIN-SPINDLE-PID-23) -> CONFIRMED (2 corrections)


---

## 9. Re-run of the 9 failed lanes (COMPLETE — map is now 24/24)

The 9 lanes that failed the first pass on a StructuredOutput retry-cap were re-run with a relaxed schema. **9/9 now mapped.** Highlights:

- **daemons** [CONFIRMED] — MEASURED via Git-Bash Windows-namespace curl (WSL2 curl-000=false-negative, NOT-WEDGED). 12/14 daemons UP: 4796 recall-serve-rust 200 (591k rows), 4949 apex COL-ASOLARIA up96379s, 4947 behcs-bus 404-listen, 4953 cosign 200, 4952 vote-quorum 200, 4950 omnidispatcher 404, 5088 host8-serve-rust 200, 4794 fischer 200, 4792/4793 gnn 501-up, 48
- **mtp-dspark** [CONFIRMED] — MEASURED: lane materialized as servers/council-serve/src/schedule.rs (DSpark confidence-scheduled-verify), git 1a545d0. mod schedule wired in main.rs, exposed read-only via HTTP GET /api/loop/schedule (routes.rs:55). Emits HBP json=0 rows (COUNCILSCHEDULE/COUNCILSCHED). status=staged source=loop_ledger_unwired (needs ASOLARIA_LOOP_LEDGER)
- **aot-microsoft** [CONFIRMED] — MEASURED: fabric council LIVE-fired AoT envelope council-q-1783001086283 ok=true by=acer HBP-ACK json=0 (lane addressable in running fabric); canon doc 04-AOT-ALGORITHM-OF-THOUGHT.md 4015B on disk = Foundation-v1 Class-1 LAW feature 1; recall :4796 empty=held-safe not down. CANON: single-prompt in-context tree search, ~9x token cut (64k t
- **biml-multistacking** [CORRECTED] — MEASURED: fabric LIVE :4949 apex=COL-ASOLARIA uptime 96322s, council query fired council-q-1783001067890 bus-ACK ok=true by=acer; recall :4796 curl-000 = WSL2 loopback held-safe (not down). CANON: founding paper Jesse Brown PhD Sept-2023 DOI 10.13140/RG.2.2.35081.42085 = BIML+BIML2+MLC+GPT4+S-LoRA+ChatDev+AoT+RAG-Fusion; operator hand-dra
- **rust-kernel-core** [CORRECTED] — MEASURED git: kernel/core v0.2.0-phase3-scaffold, no_std+forbid-unsafe. W1 crypto-leaf + W2 bus_fabric prefix-tree merged PR#25 (786621c); branch acer/w0-fmt-unblock tip 7bdd52e (W0 fmt unblock). bus_fabric: BEHCS-1024 1024-glyph alphabet, prefix-tree depth-20, 10^60 ceiling, resolve_label=FNV-1a-64 Phase-1 placeholder, 16 tests pass in-s
- **usb-fusion-wsl** [CONFIRMED] — MEASURED-live: fabric:4949 up96362s apex COL-ASOLARIA cohort ACER-PID-H740C; recall:4796 591946 rows HILBRA idx. WSL2 k6.6.87 alive, block devs sda-sdd only (sdd 1T ext4 /mnt/wslg). SOVLINUX NOT WSL-attached (no usbipd), no E/F/G letter mount, /mnt/sde-probe empty. usb-raw tools present (exfat_walk/extract_full/usb_raw_io/probe_*)=Win-Pyt
- **routing-omnidispatcher** [CONFIRMED] — MEASURED: omni-dispatcher :4950 LISTENING (win PID 7068); boot log = slot_count 1006, workers 8, manifest_source hbp, [ingress] LISTEN. Bus :4947, dash :4949, recall :4796, :4952, :4953 all LISTENING. Live Node omnidispatcher.mjs: FEDENV-v1 ingress POST /v1/envelope, 4-lane PriorityQueue apex/high/normal/low, worker_threads pool, lazy per
- **fabric-core** [CONFIRMED] — MEASURED-LIVE via system tools: fabric :4949 apex COL-ASOLARIA uptime 96401s, council query fired+bus-acked json=0 (row d2ebe6d2). recall :4796 Rust engine 591946 rows HBP/HBI hot-path (HILBRA-IDX 2.6M terms/24M postings), loopback-open+HMAC owner-PID gate. bus :4947 up (/behcs/send,inbox,devices). cosign chain LIVE 5422 lines seq 3575, s
- **kernel-security** [CONFIRMED] — MEASURED source (no_std) in federation-1024/kernel/core/src: crypto(ed25519-dalek2.1, v0.1 sha-derived verify, trust-roots@build, key in TPM/sealed), sign_gate(ed25519 verify + deny filter, BEHCS-256 port), link_auth(HMAC-SHA256 + owner-PID consent, verb-bound anti-replay, key never hardcoded), cosign_chain(append-only sha-linked audit ro
