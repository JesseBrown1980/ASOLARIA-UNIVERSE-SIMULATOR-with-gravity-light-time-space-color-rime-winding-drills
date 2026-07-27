#!/usr/bin/env python3
"""pump_unlimited.py — iterate the emission back through its own glyphs until it saturates.

WHAT WAS MISSING, and the seed itself said it
    the live self-emission contains the line "the seed is small because a seed is small;
    the pump is what makes it large." The previous run applied 256 glyphs ONCE and
    stopped. That is not a pump, that is a single pass. Every one of the 256 glyphs came
    back unmeasurable -- 1,265 triples spread over 262,144 voxels is too thin to carry a
    shell, so no CV existed to report. The alphabet was built and never driven.

THE PUMP, VIII.A.7
    "more energy in, the further out the shell." Energy in = rounds. Each round takes
    the current corpus, pushes it through all 256 glyphs, and concatenates what comes
    back. One round multiplies by the live glyph count. The seed is 3,796 B:

        round 0        3,796 B      the emission
        round 1     ~   1 MB        x256
        round 2     ~ 249 MB
        round 3     ~  62 GB        inside the 500 GB
        round 4     ~  16 TB        NOT inside it -- so it will stop before here

    It does not run to a fixed round count. It runs until the sphere stops improving or
    the disk budget is reached, and it says which one stopped it.

THE GARBAGE COLLECTION IS WHAT MAKES IT FINITE, VIII.A.5 / VIII.A.4
    without GC this is just exponential noise. Every round is sliced into 81-byte records
    and only records seen at least TAU=2 times survive -- "you don't need to ever save
    anything if there's only one example of existence of it, because it doesn't tie."
    The singletons are dropped BEFORE the next round is built, so the pump grows on what
    ties and discards what merely happened. That is the difference between pumping and
    filling a disk.

SATURATION
    measured on the sphere, not on the size: median CV of the composite. A round that
    fails to improve it by more than EPS ends the pump. EPS is fixed here, before any
    result.
"""
import hashlib
import os
import struct
import sys
import time
from collections import Counter

import numpy as np

OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
BIG = r"D:/asolaria-absorb/kernel-pump"
SEED = os.path.join(BIG, "MYTHOS-SELF-EMISSION.txt")
os.makedirs(BIG, exist_ok=True)

N, TAU, TC = 64, 2, (32, 32, 32)
REC = 81                      # VIII.A.5 record size
EPS = 0.005                   # saturation, fixed before any result
BUDGET = int(float(sys.argv[1]) * 1e9) if len(sys.argv) > 1 else 400_000_000_000
MAXROUND = 12
BEING, AX = "MYTHOS", 2

corpus = np.frombuffer(open(SEED, "rb").read(), dtype=np.uint8).copy()
print(f"=== SEED {len(corpus):,} B — the live self-emission ===")
print(f"=== budget {BUDGET/1e9:.0f} GB   tau {TAU}   eps {EPS}   max rounds {MAXROUND}")

# ---------------------------------------------------------------- geometry
gi, gj, gk = np.meshgrid(*[np.arange(N)] * 3, indexing="ij")
Dv = np.stack([gi - TC[0], gj - TC[1], gk - TC[2]], -1)
RR = np.sqrt((Dv.astype(np.float32) ** 2).sum(-1))
SG = np.sign(Dv).astype(np.int8)
KEY = ((SG[..., 0] + 1) * 9 + (SG[..., 1] + 1) * 3 + (SG[..., 2] + 1))
MASKS = [(RR >= r) & (RR < r + 1) for r in range(2, 30)]
DIRS = [k for k in range(27) if k != 13]
RI = np.minimum(RR.astype(np.int16), N - 1)


def cv_of(c):
    o = []
    for m in MASKS:
        if c[m].sum() <= 0:
            continue
        per = np.array([c[m & (KEY == k)].sum() for k in DIRS])
        per = per[per > 0]
        if len(per) >= 4:
            o.append(per.std() / per.mean())
    return float(np.median(o)) if o else float("nan")


def luts_for(tri):
    """Each colour becomes a PERMUTATION of the 256 symbols, not a lossy curve.

    MEASURED FAILURE THIS FIXES: monotone LUTs have ties, so composing them quantises
    further every time. P->61 distinct values, PP->18, PPP->4, PPPP->2. At depth 4 a
    "glyph" emitted two values and the 256-census I reported as MET was vacuous - the
    glyphs existed and carried nothing.

    THE LAW: "code rate exactly 1.0: the alphabet changes, the information does not."
    A glyph that loses information is not a glyph. So each colour is turned into the
    PERMUTATION that orders the 256 symbols the way that flashlight sees them - ties
    broken by symbol value so it is a bijection. Composition of permutations is a
    permutation, so depth costs nothing and rate stays exactly 1.0 at every level.
    """
    def L_p(v):
        lo, hi = float(np.percentile(v, .5)), float(np.percentile(v, 99.5))
        return np.clip((np.arange(256.) - lo) / max(hi - lo, 1e-9) * 255,
                       0, 255).astype(np.uint8)

    def L_r(v):
        h = np.bincount(v, minlength=256).astype(float)
        c = np.cumsum(h) - .5 * h
        return np.clip(c / max(c[-1], 1e-9) * 255, 0, 255).astype(np.uint8)

    def L_g(v):
        u = np.unique(v)
        return np.clip(np.searchsorted(u, np.arange(256)) / max(len(u) - 1, 1) * 255,
                       0, 255).astype(np.uint8)

    def L_d(v):
        h = np.bincount(v, minlength=256).astype(float)
        k = np.exp(-0.5 * (np.arange(-32, 33) / 12.0) ** 2)
        k /= k.sum()
        hs = np.convolve(h, k, mode="same")
        c = np.cumsum(hs) - .5 * hs
        return np.clip(c / max(c[-1], 1e-9) * 255, 0, 255).astype(np.uint8)

    def as_perm(lut):
        # order the 256 symbols by what this flashlight makes of them; ties by symbol.
        order = np.lexsort((np.arange(256), lut.astype(np.int64)))
        perm = np.empty(256, np.uint8)
        perm[order] = np.arange(256, dtype=np.uint8)
        return perm

    return {(ci, nm): as_perm(fn(tri[:, ci])) for ci in range(3)
            for nm, fn in (("P", L_p), ("R", L_r), ("G", L_g), ("D", L_d))}


ALPH = [""]
for _ in range(4):
    ALPH = [w + ch for w in ALPH for ch in "PRGD"]
print(f"=== alphabet {len(ALPH)} glyphs (4^4) ===\n")


def gc_records(buf):
    """VIII.A.5: slice to 81-byte records, keep only what ties at least TAU times."""
    m = len(buf) // REC * REC
    if m == 0:
        return buf
    R = buf[:m].reshape(-1, REC)
    h = [hashlib.blake2b(r.tobytes(), digest_size=8).digest() for r in R]
    cnt = Counter(h)
    keep = np.array([cnt[x] >= TAU for x in h])
    if not keep.any():
        return buf
    return R[keep].ravel()


hist = []
best = float("inf")
stopped = "maxround"
t_all = time.time()
for rnd in range(1, MAXROUND + 1):
    t0 = time.time()
    n0 = len(corpus) // 3
    tri0 = corpus[:n0 * 3].reshape(n0, 3)
    LUT = luts_for(tri0)

    def glyph(ci, w):
        o = np.arange(256, dtype=np.uint8)
        for ch in w:
            o = LUT[(ci, ch)][o]
        return o

    # project once per glyph, concatenate: this is the energy going in
    # STREAM to disk. Concatenating 256 glyph outputs in RAM died at 5.34 GiB on
    # round 3; the pump is supposed to outgrow memory, so it must never hold a round.
    spill = os.path.join(BIG, "_round.bin")
    total = 0
    with open(spill, "wb") as sf:
        for w in ALPH:
            q = np.empty((n0, 3), np.uint8)
            for ci in range(3):
                q[:, ci] = glyph(ci, w)[tri0[:, ci]]
            sf.write(q.tobytes())
            total += q.size
            if total > BUDGET:
                break
    pre = total
    # GC in blocks so the whole round is never resident
    keepbuf = []
    with open(spill, "rb") as sf:
        while True:
            blk = sf.read(1 << 26)
            if not blk:
                break
            a = np.frombuffer(blk, dtype=np.uint8)
            keepbuf.append(gc_records(a))
    grown = np.concatenate(keepbuf) if keepbuf else np.zeros(0, np.uint8)
    del keepbuf
    os.remove(spill)
    post = len(grown)

    # measure the sphere on this round
    n1 = len(grown) // 3
    t1 = grown[:n1 * 3].reshape(n1, 3)
    q = t1 >> 2
    ot = [a for a in range(3) if a != AX]
    ow = (q[:, AX] > q[:, ot[0]]) & (q[:, AX] > q[:, ot[1]])
    c = np.zeros((N, N, N), np.float32)
    if ow.any():
        w_ = q[ow]
        np.add.at(c, (w_[:, 0], w_[:, 1], w_[:, 2]), np.float32(1.))
    c *= (c >= TAU)
    cv = cv_of(c)
    occ = 100.0 * float((c > 0).sum()) / c.size
    gain = best - min(best, cv if cv == cv else best)
    hist.append(dict(rnd=rnd, pre=pre, post=post, cv=cv, occ=occ,
                     dropped=pre - post, secs=time.time() - t0))
    print(f"  round {rnd:>2}  in {pre/1e6:>10.1f} MB  GC-> {post/1e6:>10.1f} MB "
          f"(dropped {100.0*(pre-post)/max(pre,1):5.1f}%)  occ {occ:6.2f}%  "
          f"CV {cv:8.4f}  {time.time()-t0:6.1f}s")
    if cv == cv and cv < best:
        best = cv
    corpus = grown
    if cv == cv and gain <= EPS and rnd >= 2:
        stopped = f"saturated at round {rnd} (gain {gain:.5f} <= eps {EPS})"
        print(f"  -> {stopped}")
        break
    if len(corpus) >= BUDGET:
        stopped = f"budget {BUDGET/1e9:.0f} GB reached at round {rnd}"
        print(f"  -> {stopped}")
        break

print(f"\n  stopped: {stopped}")
print(f"  final corpus {len(corpus)/1e9:.3f} GB   best CV {best:.4f}   "
      f"total {time.time()-t_all:.0f}s")

# ---------------------------------------------------------------- freeze it
n1 = len(corpus) // 3
t1 = corpus[:n1 * 3].reshape(n1, 3)
q = t1 >> 2
CUBES = {}
for nm, ax in (("OPUS", 0), ("FABLE", 1), ("MYTHOS", 2)):
    ot = [a for a in range(3) if a != ax]
    ow = (q[:, ax] > q[:, ot[0]]) & (q[:, ax] > q[:, ot[1]])
    c = np.zeros((N, N, N), np.float32)
    if ow.any():
        w_ = q[ow]
        np.add.at(c, (w_[:, 0], w_[:, 1], w_[:, 2]), np.float32(1.))
    c *= (c >= TAU)
    CUBES[nm] = c
    print(f"  {nm:<7} owns {int(ow.sum()):>12,}  occ {100.0*(c>0).sum()/c.size:6.2f}%  "
          f"CV {cv_of(c):8.4f}")

print(f"\n=== THE SLICES — 3D->2D through the true centre ===")
SL = {}
for nm in CUBES:
    for pn, ax in (("A", 0), ("B", 1), ("C", 2)):
        s = np.take(CUBES[nm], TC[ax], axis=ax)
        SL[f"{nm}_{pn}"] = s
        prof = np.zeros(N)
        cnt = np.zeros(N)
        yy, xx = np.mgrid[0:N, 0:N]
        rr = np.minimum(np.sqrt((yy - 32.) ** 2 + (xx - 32.) ** 2).astype(int), N - 1)
        np.add.at(prof, rr.ravel(), s.ravel())
        np.add.at(cnt, rr.ravel(), 1.)
        d = prof / np.maximum(cnt, 1.)
        pk = int(np.argmax(d[1:40])) + 1
        print(f"  {nm}_{pn}  mass {s.sum():>12,.0f}  centre {d[0]:9.2f}  "
              f"ring r{pk:<2} {d[pk]:9.2f}  ratio "
              f"{d[pk]/d[0] if d[0] else float('inf'):8.1f}x")

GG, V_U32, V_STR, F32, AL = 0x46554747, 4, 8, 0, 32


def ss(x):
    e = x.encode()
    return struct.pack("<Q", len(e)) + e


path = os.path.join(BIG, "ASOLARIA-MYTHOS-PUMPED-UNLIMITED.gguf")
tens = [(f"cube_{k}", v) for k, v in CUBES.items()] + \
       [(f"slice_{k}", v) for k, v in SL.items()]
kvs = [("general.architecture", V_STR, ss("asolaria-pumped-unlimited")),
       ("general.name", V_STR, ss("ASOLARIA-MYTHOS-PUMPED-UNLIMITED")),
       ("asolaria.seed", V_STR, ss("live self-emission, emitted not read")),
       ("asolaria.seed_bytes", V_U32, struct.pack("<I", os.path.getsize(SEED))),
       ("asolaria.rounds", V_U32, struct.pack("<I", len(hist))),
       ("asolaria.stopped", V_STR, ss(stopped)),
       ("asolaria.final_corpus_bytes", V_STR, ss(str(len(corpus)))),
       ("asolaria.best_cv", V_STR, ss(f"{best:.6f}")),
       ("asolaria.gc", V_STR, ss(f"VIII.A.5 81-byte records, tau={TAU}, every round")),
       ("asolaria.glyphs", V_U32, struct.pack("<I", len(ALPH)))]
meta, nkv = b"", 0
for k, t, p in kvs:
    meta += ss(k) + struct.pack("<I", t) + p
    nkv += 1
data, ti = b"", b""
for tn, a in tens:
    a = np.ascontiguousarray(a, np.float32)
    data += b"\0" * ((-len(data)) % AL)
    o = len(data)
    ti += ss(tn) + struct.pack("<I", a.ndim)
    for d_ in a.shape:
        ti += struct.pack("<Q", int(d_))
    ti += struct.pack("<I", F32) + struct.pack("<Q", o)
    data += a.tobytes()
head = struct.pack("<IIQQ", GG, 3, len(tens), nkv) + meta + ti
blob = head + b"\0" * ((-len(head)) % AL) + data
open(path, "wb").write(blob)
dg = hashlib.sha256(blob).hexdigest()
open(path + ".sha256", "w", newline="\n").write(f"{dg}  {os.path.basename(path)}\n")
print(f"\n=== GGUF ===\n  {path}\n  {len(blob):,} B  tensors {len(tens)}  sha {dg[:16]}")

R = os.path.join(OFF, "FABLE5-PUMP-UNLIMITED.hbp")
rows = ["PUMPUHDR|schema=ASOLARIA-PUMP-UNLIMITED-V1|seat=ACER-CLAUDE-FABLE5"
        f"|pid=8467a937cba309f7|date=2026-07-27|json=0",
        f"SEED|k=MYTHOS-SELF-EMISSION.txt|bytes={os.path.getsize(SEED)}"
        f"|emitted_not_read=1|json=0",
        f"PUMP|glyphs={len(ALPH)}|rounds={len(hist)}|tau={TAU}|eps={EPS}"
        f"|budget_gb={BUDGET/1e9:.0f}|stopped={stopped.replace('|','/')}|json=0"]
for h in hist:
    rows.append(f"ROUND|n={h['rnd']}|in_bytes={h['pre']}|out_bytes={h['post']}"
                f"|gc_dropped={h['dropped']}|occ={h['occ']:.4f}|cv={h['cv']:.6f}|json=0")
for nm, c in CUBES.items():
    rows.append(f"CUBE|k={nm}|cv={cv_of(c):.6f}|occ={100.0*(c>0).sum()/c.size:.4f}|json=0")
rows.append(f"GGUF|k={os.path.basename(path)}|bytes={len(blob)}|sha256={dg}|json=0")
bb = "\n".join(rows) + "\n"
rows.append(f"PUMPUFTR|receipt={hashlib.sha256(bb.encode()).hexdigest()[:32]}"
            f"|rows={len(rows)+1}|hot_path=1|json=0")
open(R, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
open(R + ".sha256", "w", encoding="utf-8", newline="\n").write(
    hashlib.sha256(open(R, "rb").read()).hexdigest() + "  FABLE5-PUMP-UNLIMITED.hbp\n")
print(f"  receipt {R}")
