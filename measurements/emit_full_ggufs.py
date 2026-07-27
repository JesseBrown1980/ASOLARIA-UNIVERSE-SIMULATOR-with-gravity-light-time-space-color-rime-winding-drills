#!/usr/bin/env python3
"""emit_full_ggufs.py — write the FULL pumped GGUF for all three beings.

The pump run kept only the winner's stage data and deleted the other two temp files,
so OPUS shipped complete and FABLE and MYTHOS did not. This re-emits all three on the
identical ladder so the trilateral compare has three full objects rather than one full
and two summaries.

Identical to pump_mythos_sphere.py in every parameter -- same flashlights, same LUT
composition, same tau=2 per-stage GC, same level-4 stop (3+9+27+81 = 120 stages, plus
the composite = 121 tensors). Nothing is retuned; this is the same measurement, kept.
"""
import glob
import hashlib
import os
import struct
import time

import numpy as np

OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
BIG = r"D:/asolaria-absorb/kernel-pump"
os.makedirs(BIG, exist_ok=True)
N, TAU, TC = 64, 2, (32, 32, 32)
BEINGS = [("OPUS", "RED", 0), ("FABLE", "GREEN", 1), ("MYTHOS", "BLUE", 2)]

SRC = []
for p in (OFF + "/FABLE5-*.hbi", OFF + "/FABLE5-*.hbp",
          "D:/asolaria-absorb/laws/*.qr", "D:/asolaria-absorb/laws/prior3174.bin",
          "D:/asolaria-absorb/asolaria-tribit/web/asolaria_tribit.wasm"):
    SRC += sorted(glob.glob(p))
SRC = [f for f in SRC if os.path.isfile(f) and not f.endswith(".sha256")]
raw = np.frombuffer(b"".join(open(f, "rb").read() for f in SRC), dtype=np.uint8)
n = len(raw) // 3
tri = raw[:n * 3].reshape(n, 3)
print(f"=== corpus {len(SRC)} artifacts  {n:,} triples ===")


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


BASE = [("P", L_p), ("R", L_r), ("G", L_g)]
LUT = {(c, nm): fn(tri[:, c]) for c in range(3) for nm, fn in BASE}


def comp(c, w):
    o = np.arange(256, dtype=np.uint8)
    for ch in w:
        o = LUT[(c, ch)][o]
    return o


gi, gj, gk = np.meshgrid(*[np.arange(N)] * 3, indexing="ij")
D = np.stack([gi - TC[0], gj - TC[1], gk - TC[2]], -1)
RR = np.sqrt((D.astype(np.float32) ** 2).sum(-1))
S = np.sign(D).astype(np.int8)
KEY = ((S[..., 0] + 1) * 9 + (S[..., 1] + 1) * 3 + (S[..., 2] + 1))
MASKS = [(RR >= r) & (RR < r + 1) for r in range(2, 30)]
DIRS = [k for k in range(27) if k != 13]


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


def stage(w, ax):
    q = np.empty((n, 3), np.uint8)
    for c in range(3):
        q[:, c] = comp(c, w)[tri[:, c]]
    q >>= 2
    ot = [a for a in range(3) if a != ax]
    ow = (q[:, ax] > q[:, ot[0]]) & (q[:, ax] > q[:, ot[1]])
    cc = np.zeros((N, N, N), np.float32)
    ww = q[ow]
    np.add.at(cc, (ww[:, 0], ww[:, 1], ww[:, 2]), np.float32(1.))
    return cc * (cc >= TAU)


WORDS = []
for lv in (1, 2, 3, 4):
    cur = [""]
    for _ in range(lv):
        cur = [x + ch for x in cur for ch, _ in BASE]
    WORDS += cur
print(f"=== ladder {len(WORDS)} stages (3+9+27+81) + composite = {len(WORDS)+1} tensors")

GG, V_U32, V_STR, F32, AL = 0x46554747, 4, 8, 0, 32


def ss(x):
    e = x.encode()
    return struct.pack("<Q", len(e)) + e


for name, chan, ax in BEINGS:
    t0 = time.time()
    path = os.path.join(BIG, f"ASOLARIA-{name}-SPHERE-PUMPED.gguf")
    tmp = os.path.join(BIG, f"_{name}.dat")
    composite = np.zeros((N, N, N), np.float32)
    tens, off, best, bw = [], 0, float("inf"), ""
    with open(tmp, "wb") as fh:
        for w in WORDS:
            c = stage(w, ax)
            composite += c
            fh.write(c.tobytes())
            tens.append((f"stage_{w}", off))
            off += c.nbytes
            v = cv_of(c)
            if v == v and v < best:
                best, bw = v, w
    kvs = [("general.architecture", V_STR, ss("asolaria-pumped-sphere")),
           ("general.name", V_STR, ss(f"ASOLARIA-{name}-SPHERE-PUMPED")),
           ("asolaria.seat", V_STR, ss("ACER")),
           ("asolaria.being", V_STR, ss(name)),
           ("asolaria.channel", V_STR, ss(chan)),
           ("asolaria.ladder", V_STR,
            ss("3 singles + 9 pairs = 12, then 27 triples, then 81 quads; "
               "flashlight LUT composition")),
           ("asolaria.gc", V_STR, ss(f"VIII.A.5 two-thirds, tau={TAU}, per stage")),
           ("asolaria.best_composition", V_STR, ss(bw)),
           ("asolaria.best_cv", V_STR, ss(f"{best:.6f}")),
           ("asolaria.composite_cv", V_STR, ss(f"{cv_of(composite):.6f}")),
           ("asolaria.true_centre", V_STR, ss("32,32,32"))]
    meta, nkv = b"", 0
    for k, t, p in kvs:
        meta += ss(k) + struct.pack("<I", t) + p
        nkv += 1
    allt = tens + [("composite", off)]
    ti = b""
    for tn, o_ in allt:
        ti += ss(tn) + struct.pack("<I", 3)
        for d_ in (N, N, N):
            ti += struct.pack("<Q", d_)
        ti += struct.pack("<I", F32) + struct.pack("<Q", int(o_))
    head = struct.pack("<IIQQ", GG, 3, len(allt), nkv) + meta + ti
    head += b"\0" * ((-len(head)) % AL)
    h = hashlib.sha256()
    with open(path, "wb") as o:
        o.write(head)
        h.update(head)
        with open(tmp, "rb") as f:
            while True:
                ch = f.read(8 << 20)
                if not ch:
                    break
                o.write(ch)
                h.update(ch)
        cb = np.ascontiguousarray(composite, np.float32).tobytes()
        o.write(cb)
        h.update(cb)
    os.remove(tmp)
    dg = h.hexdigest()
    sz = os.path.getsize(path)
    open(path + ".sha256", "w", newline="\n").write(
        f"{dg}  {os.path.basename(path)}\n")
    print(f"  {os.path.basename(path):<40} {sz:>12,} B  "
          f"{sz*8/1e9:.3f} Gb  best {bw} CV {best:.4f}  sha {dg[:16]}  "
          f"{time.time()-t0:.0f}s")
print("\nall three full GGUFs written to", BIG)
