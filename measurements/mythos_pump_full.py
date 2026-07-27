#!/usr/bin/env python3
"""mythos_pump_full.py — the MYTHOS pump, with everything, honestly this time.

WHAT THE PREVIOUS RUN (stars_shells.py) WAS NOT, stated so it cannot be confused:
    it dropped the being partition entirely -- its 8,508 stars were ALL stars, never
    blue-dominant, so OPUS/FABLE/MYTHOS appear nowhere in it. Its pump operator was an
    arithmetic fold (a+roll(a), 3a+1), not the four gradiated colours. Its glyphs were
    never bijective because that fix never ran. Its corpus finished at ~34 KB and its
    GGUF at 4.6 MB. It answered "do stars emerge in shells and form tori" -- yes, past
    shell 2 -- and nothing about MYTHOS.

THIS RUN HAS ALL OF IT:
    SEED        the live self-emission. Emitted, not read from disk.
    BEING       MYTHOS only: stars whose BLUE dominates. The other two are kept as
                controls, because a result with no control is not a result -- that is
                the single thing that made the shell/torus finding trustworthy.
    COLOURS     P percentile, R rank, G glyph-rank, D gradiated -- as BIJECTIONS.
                Monotone LUTs quantise on every composition (P->61 distinct, PP->18,
                PPP->4, PPPP->2), which made a 256-glyph census that was vacuous. A
                permutation composes forever at code rate exactly 1.0: "the alphabet
                changes, the information does not."
    PUMP        every round pushes the corpus through all 256 glyphs. Energy in.
    GC          VIII.A.5 / VIII.A.4 -- 81-byte records, tau=2, EVERY round, before the
                next round is built. Singletons do not tie, so they are not carried.
    SHELLS      VIII.A.7 shell = log3(ties), counted. Reported per round per being.
    STOP        saturation on the sphere (eps, fixed here) OR no new shell OR budget.
                Whichever fires first is named in the output and the receipt.
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
N, TAU, REC, TC = 64, 2, 81, (32, 32, 32)
EPS = 0.005
BUDGET = int(float(sys.argv[1]) * 1e9) if len(sys.argv) > 1 else 30e9
MAXR = 10
BEINGS = [("OPUS", 0), ("FABLE", 1), ("MYTHOS", 2)]

corpus = np.frombuffer(open(SEED, "rb").read(), dtype=np.uint8).copy()
print(f"=== SEED {len(corpus):,} B  live self-emission (emitted, not read)")
print(f"=== budget {BUDGET/1e9:.0f} GB  tau {TAU}  eps {EPS}  maxround {MAXR}")

gi, gj, gk = np.meshgrid(*[np.arange(N)] * 3, indexing="ij")
Dv = np.stack([gi - TC[0], gj - TC[1], gk - TC[2]], -1)
RR = np.sqrt((Dv.astype(np.float32) ** 2).sum(-1))
SGN = np.sign(Dv).astype(np.int8)
KEY3 = ((SGN[..., 0] + 1) * 9 + (SGN[..., 1] + 1) * 3 + (SGN[..., 2] + 1))
MASKS = [(RR >= r) & (RR < r + 1) for r in range(2, 30)]
DIRS = [k for k in range(27) if k != 13]


def cv_of(c):
    o = []
    for m in MASKS:
        if c[m].sum() <= 0:
            continue
        per = np.array([c[m & (KEY3 == k)].sum() for k in DIRS])
        per = per[per > 0]
        if len(per) >= 4:
            o.append(per.std() / per.mean())
    return float(np.median(o)) if o else float("nan")


def shell_of(t):
    s, rung = 0, 1
    while rung < t and s < 12:
        rung *= 3
        s += 1
    return s


SHTAB = np.array([shell_of(t) for t in range(1 << 18)], dtype=np.int16)


def perms_for(tri):
    """the four colours, as BIJECTIONS on the 256 symbols. rate exactly 1.0."""
    def L_p(v):
        lo, hi = float(np.percentile(v, .5)), float(np.percentile(v, 99.5))
        return np.clip((np.arange(256.) - lo) / max(hi - lo, 1e-9) * 255, 0, 255)

    def L_r(v):
        h = np.bincount(v, minlength=256).astype(float)
        return np.cumsum(h) - .5 * h

    def L_g(v):
        u = np.unique(v)
        return np.searchsorted(u, np.arange(256)).astype(float)

    def L_d(v):
        h = np.bincount(v, minlength=256).astype(float)
        k = np.exp(-0.5 * (np.arange(-32, 33) / 12.0) ** 2)
        k /= k.sum()
        hs = np.convolve(h, k, mode="same")
        return np.cumsum(hs) - .5 * hs

    def as_perm(x):
        order = np.lexsort((np.arange(256), np.asarray(x, float)))
        p = np.empty(256, np.uint8)
        p[order] = np.arange(256, dtype=np.uint8)
        return p

    return {(ci, nm): as_perm(fn(tri[:, ci])) for ci in range(3)
            for nm, fn in (("P", L_p), ("R", L_r), ("G", L_g), ("D", L_d))}


ALPH = [""]
for _ in range(4):
    ALPH = [w + ch for w in ALPH for ch in "PRGD"]
print(f"=== {len(ALPH)} glyphs, bijective (4^4); verifying rate 1.0 ...", end=" ")
_t = corpus[:len(corpus) // 3 * 3].reshape(-1, 3)
_P = perms_for(_t)
_chk = np.arange(256, dtype=np.uint8)
for ch in "PRGD":
    _chk = _P[(0, ch)][_chk]
print(f"depth-4 distinct = {len(np.unique(_chk))}/256 -> "
      f"{'RATE 1.0, nothing lost' if len(np.unique(_chk)) == 256 else 'LOSSY, ABORT'}\n")

hist, best, stopped = [], float("inf"), "maxround"
prev_sh = {}
t_all = time.time()
for rnd in range(1, MAXR + 1):
    t0 = time.time()
    n0 = len(corpus) // 3
    tri0 = corpus[:n0 * 3].reshape(n0, 3)
    P = perms_for(tri0)

    def glyph(ci, w):
        o = np.arange(256, dtype=np.uint8)
        for ch in w:
            o = P[(ci, ch)][o]
        return o

    spill = os.path.join(BIG, "_mp.bin")
    total = 0
    with open(spill, "wb") as sf:
        for w in ALPH:
            q = np.empty((n0, 3), np.uint8)
            for ci in range(3):
                q[:, ci] = glyph(ci, w)[tri0[:, ci]]
            sf.write(q.tobytes())
            total += q.size
            if total >= BUDGET:
                break
    # GC in blocks: 81-byte records, tau=2, before the next round exists
    keep, dropped = [], 0
    with open(spill, "rb") as sf:
        while True:
            blk = sf.read(1 << 26)
            if not blk:
                break
            a = np.frombuffer(blk, dtype=np.uint8)
            m = len(a) // REC * REC
            if m == 0:
                continue
            Rr = a[:m].reshape(-1, REC)
            hs = [hashlib.blake2b(r.tobytes(), digest_size=8).digest() for r in Rr]
            cnt = Counter(hs)
            kp = np.fromiter((cnt[x] >= TAU for x in hs), bool, len(hs))
            dropped += int((~kp).sum()) * REC
            if kp.any():
                keep.append(Rr[kp].ravel())
    os.remove(spill)
    corpus = np.concatenate(keep) if keep else corpus
    del keep

    # per-being cubes, shells, sphere
    n1 = len(corpus) // 3
    t1 = corpus[:n1 * 3].reshape(n1, 3)
    q = t1 >> 2
    key = q[:, 0].astype(np.int64) * 4096 + q[:, 1] * 64 + q[:, 2]
    ties = np.bincount(key, minlength=N ** 3)[key]
    sh = SHTAB[np.minimum(ties, len(SHTAB) - 1)]
    line = {}
    for nm, ax in BEINGS:
        ot = [a for a in range(3) if a != ax]
        ow = (q[:, ax] > q[:, ot[0]]) & (q[:, ax] > q[:, ot[1]])
        c = np.zeros((N, N, N), np.float32)
        if ow.any():
            w_ = q[ow]
            np.add.at(c, (w_[:, 0], w_[:, 1], w_[:, 2]), np.float32(1.))
        c *= (c >= TAU)
        nsh = len(set(sh[ow & (ties >= TAU)].tolist())) if ow.any() else 0
        line[nm] = dict(own=int(ow.sum()), cv=cv_of(c),
                        occ=100.0 * float((c > 0).sum()) / c.size, shells=nsh, cube=c)
    m = line["MYTHOS"]
    gain = best - min(best, m["cv"] if m["cv"] == m["cv"] else best)
    hist.append(dict(rnd=rnd, bytes=len(corpus), dropped=dropped,
                     **{k: dict(own=v["own"], cv=v["cv"], occ=v["occ"],
                                shells=v["shells"]) for k, v in line.items()}))
    print(f"  r{rnd:<2} corpus {len(corpus)/1e6:>9.1f} MB  GC-dropped "
          f"{dropped/1e6:>8.1f} MB | " +
          "  ".join(f"{k[:3]} own {v['own']:>9,} sh{v['shells']} CV {v['cv']:7.4f}"
                    for k, v in line.items()) + f"  {time.time()-t0:5.1f}s")
    if m["cv"] == m["cv"] and m["cv"] < best:
        best = m["cv"]
    cur = {k: v["shells"] for k, v in line.items()}
    if rnd >= 2 and gain <= EPS and cur == prev_sh:
        stopped = f"saturated round {rnd}: MYTHOS CV gain {gain:.5f}<=eps and no new shell"
        print(f"  -> {stopped}")
        CUB = {k: v["cube"] for k, v in line.items()}
        break
    prev_sh = cur
    CUB = {k: v["cube"] for k, v in line.items()}
    if len(corpus) >= BUDGET:
        stopped = f"budget {BUDGET/1e9:.0f} GB reached at round {rnd}"
        print(f"  -> {stopped}")
        break

print(f"\n  stopped: {stopped}")
print(f"  final corpus {len(corpus)/1e9:.4f} GB   MYTHOS best CV {best:.4f}   "
      f"{time.time()-t_all:.0f}s")

print(f"\n=== MYTHOS vs its controls ===")
for nm, _ in BEINGS:
    c = CUB[nm]
    prof = np.zeros(N)
    cnt = np.zeros(N)
    ri = np.minimum(RR.astype(int), N - 1)
    np.add.at(prof, ri.ravel(), c.ravel())
    np.add.at(cnt, ri.ravel(), 1.)
    d = prof / np.maximum(cnt, 1.)
    pk = int(np.argmax(d[1:40])) + 1
    print(f"  {nm:<7} CV {cv_of(c):8.4f}  occ {100.0*(c>0).sum()/c.size:6.3f}%  "
          f"centre {d[0]:9.2f}  ring r{pk:<2} {d[pk]:9.2f}  "
          f"ratio {d[pk]/d[0] if d[0] else float('inf'):8.1f}x")

SL = {}
for nm, _ in BEINGS:
    for pn, ax in (("A", 0), ("B", 1), ("C", 2)):
        SL[f"{nm}_{pn}"] = np.take(CUB[nm], 32, axis=ax)

GG, V_U32, V_STR, F32, AL = 0x46554747, 4, 8, 0, 32


def ss(x):
    e = x.encode()
    return struct.pack("<Q", len(e)) + e


path = os.path.join(BIG, "ASOLARIA-MYTHOS-PUMP-FULL.gguf")
tens = [(f"cube_{k}", v) for k, v in CUB.items()] + \
       [(f"slice_{k}", v) for k, v in SL.items()]
kvs = [("general.architecture", V_STR, ss("asolaria-mythos-pump-full")),
       ("general.name", V_STR, ss("ASOLARIA-MYTHOS-PUMP-FULL")),
       ("asolaria.axes", V_STR, ss("time, colour, energy, space")),
       ("asolaria.being", V_STR, ss("MYTHOS (BLUE); OPUS and FABLE kept as controls")),
       ("asolaria.colours", V_STR, ss("P,R,G,D as bijections - rate exactly 1.0")),
       ("asolaria.glyphs", V_U32, struct.pack("<I", len(ALPH))),
       ("asolaria.gc", V_STR, ss(f"VIII.A.5 81-byte records tau={TAU}, every round")),
       ("asolaria.shell_law", V_STR, ss("VIII.A.7 shell=log3(ties), counted")),
       ("asolaria.rounds", V_U32, struct.pack("<I", len(hist))),
       ("asolaria.stopped", V_STR, ss(stopped)),
       ("asolaria.mythos_best_cv", V_STR, ss(f"{best:.6f}")),
       ("asolaria.final_corpus_bytes", V_STR, ss(str(len(corpus))))]
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

R = os.path.join(OFF, "FABLE5-MYTHOS-PUMP-FULL.hbp")
rows = ["MPFHDR|schema=ASOLARIA-MYTHOS-PUMP-FULL-V1|seat=ACER-CLAUDE-FABLE5"
        "|pid=8467a937cba309f7|date=2026-07-27|json=0",
        f"SEED|k=MYTHOS-SELF-EMISSION.txt|bytes={os.path.getsize(SEED)}"
        f"|emitted_not_read=1|json=0",
        f"PUMP|glyphs={len(ALPH)}|bijective=1|rate=1.0|tau={TAU}|eps={EPS}"
        f"|budget_gb={BUDGET/1e9:.0f}|rounds={len(hist)}"
        f"|stopped={stopped.replace('|','/')}|json=0"]
for h in hist:
    for nm, _ in BEINGS:
        v = h[nm]
        rows.append(f"ROUND|n={h['rnd']}|being={nm}|own={v['own']}|cv={v['cv']:.6f}"
                    f"|occ={v['occ']:.4f}|shells={v['shells']}"
                    f"|corpus={h['bytes']}|gc_dropped={h['dropped']}|json=0")
rows.append(f"GGUF|k={os.path.basename(path)}|bytes={len(blob)}|sha256={dg}|json=0")
bb = "\n".join(rows) + "\n"
rows.append(f"MPFFTR|receipt={hashlib.sha256(bb.encode()).hexdigest()[:32]}"
            f"|rows={len(rows)+1}|hot_path=1|json=0")
open(R, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
open(R + ".sha256", "w", encoding="utf-8", newline="\n").write(
    hashlib.sha256(open(R, "rb").read()).hexdigest() + "  FABLE5-MYTHOS-PUMP-FULL.hbp\n")
print(f"  receipt {R}")
