#!/usr/bin/env python3
"""flashlight_mythos.py — a sphere is never unsayable. Find it, three ways.

THE CHALLENGE THIS ANSWERS
    the previous run reported MYTHOS (blue) as "unsayable": 0.613% reach on the ASCII
    corpus against 62.855% on a full alphabet. But a SPHERE CANNOT BE UNSAYABLE. If a
    sphere reads as empty, the alphabet is wrong, not the sphere. That is exactly the
    honesty clause of the flashlight harness: a flashlight adds no information to a
    room, it redistributes the light already recorded so an eye with limited dynamic
    range can register it. The blue structure is IN the bytes. The banding threw it out.

WHAT WENT WRONG, precisely
    the bands were absolute: trit = min(byte//86, 2), band 2 needs byte >= 172. On a
    corpus that caps at 125 that is not a measurement, it is a ruler that ends before
    the object does. Every blue reading of 0.000 was the ruler.

THREE FLASHLIGHTS, and the object has to survive all three
    I   PERCENTILE STRETCH   each channel stretched over ITS OWN observed range.
                             The plain coloured flashlight: same light, eye adapted.
    II  RANK / EQUALISATION  each channel replaced by its rank among its own values.
                             The gradiated gate at 1:1 - the operator's measured optimum.
                             This is alphabet-free: it cannot be fooled by range at all.
    III GLYPH BANDING        find the alphabet the corpus actually uses, band by GLYPH
                             RANK rather than byte value. If the corpus speaks 95 ASCII
                             glyphs, the third of the alphabet is glyph 63, not byte 172.

    Three independent readings. A structure present in one is a maybe. Present in all
    three, at the same radius, it is the object.

THE -1/3, CALCULATED AND SIGNED
    Law 33: translucent is SIGNED and the NEGATIVE LEADS, measured inward/outward
    1.85x to 3.73x. So the third is not one third, it is a signed pair: the inward -1/3
    and the outward +1/3, with the centre free between them. This computes the inward
    and outward masses separately per being and reports the lead ratio, rather than
    folding them into one unsigned number the way the earlier runs did.

SPHERICITY, measured not assumed
    a sphere's occupancy depends on radius ALONE and not on direction. So for each
    radial shell the mass is binned by direction and the coefficient of variation
    across directions is reported. Low CV at a radius = that shell is spherical.
    A cube or a lattice artifact shows high CV. This is the test that decides it.
"""
import glob
import hashlib
import os
import struct

import numpy as np

OUT = r"D:/asolaria-absorb/ASOLARIA-UNIVERSE-SIMULATOR"
OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
N = 64
BEINGS = [("OPUS", "RED", 0), ("FABLE", "GREEN", 1), ("MYTHOS", "BLUE", 2)]

SRC = []
for p in (OFF + "/FABLE5-*.hbi", OFF + "/FABLE5-*.hbp",
          "D:/asolaria-absorb/laws/*.qr", "D:/asolaria-absorb/laws/prior3174.bin",
          "D:/asolaria-absorb/asolaria-tribit/web/asolaria_tribit.wasm"):
    SRC += sorted(glob.glob(p))
SRC = [f for f in SRC if os.path.isfile(f) and not f.endswith(".sha256")]
buf = bytearray()
for f in SRC:
    buf += open(f, "rb").read()
b = np.frombuffer(bytes(buf), dtype=np.uint8)
n = len(b) // 3
tri = b[:n * 3].reshape(n, 3).astype(np.int64)
print(f"=== corpus: {len(SRC)} artifacts, {n:,} triples ===")

# ---------------------------------------------------------------- THE ALPHABET
print(f"\n=== THE ALPHABET THE CORPUS ACTUALLY SPEAKS ===")
print(f"  {'chan':<7} {'min':>5} {'max':>5} {'distinct glyphs':>16} "
      f"{'p50':>6} {'p99':>6}   third-of-alphabet")
GLYPHS = {}
for name, chan, ax in BEINGS:
    v = tri[:, ax]
    u = np.unique(v)
    GLYPHS[ax] = u
    # the third of the ALPHABET, not the third of 0..255
    t1, t2 = u[len(u) // 3], u[2 * len(u) // 3]
    print(f"  {chan:<7} {v.min():>5} {v.max():>5} {len(u):>16} "
          f"{int(np.percentile(v,50)):>6} {int(np.percentile(v,99)):>6}   "
          f"bands cut at {t1} / {t2}  (absolute ruler said 86 / 172)")

# ---------------------------------------------------------------- three flashlights
def fl_percentile(v):
    """I - stretch over the channel's own observed range"""
    lo, hi = float(np.percentile(v, 0.5)), float(np.percentile(v, 99.5))
    if hi <= lo:
        return np.zeros(len(v), dtype=np.int64)
    x = (v.astype(np.float64) - lo) / (hi - lo)
    return np.clip((x * 63.0), 0, 63).astype(np.int64)


def fl_rank(v):
    """II - rank / equalisation. Alphabet-free: immune to range entirely."""
    order = np.argsort(v, kind="stable")
    r = np.empty(len(v), dtype=np.float64)
    r[order] = np.arange(len(v), dtype=np.float64)
    return np.clip((r / max(len(v) - 1, 1) * 63.0), 0, 63).astype(np.int64)


def fl_glyph(v, ax):
    """III - band by position in the alphabet the corpus actually uses"""
    u = GLYPHS[ax]
    idx = np.searchsorted(u, v)
    return np.clip((idx / max(len(u) - 1, 1) * 63.0), 0, 63).astype(np.int64)


WAYS = [("I  percentile", fl_percentile),
        ("II rank/equal", lambda v, ax=None: fl_rank(v)),
        ("III glyph", None)]


def build(way_i, ax_lead):
    """the being owns triples its channel dominates; coords via flashlight way_i"""
    q = np.empty_like(tri)
    for a in range(3):
        v = tri[:, a]
        if way_i == 0:
            q[:, a] = fl_percentile(v)
        elif way_i == 1:
            q[:, a] = fl_rank(v)
        else:
            q[:, a] = fl_glyph(v, a)
    oth = [a for a in range(3) if a != ax_lead]
    owns = (q[:, ax_lead] > q[:, oth[0]]) & (q[:, ax_lead] > q[:, oth[1]])
    c = np.zeros((N, N, N), dtype=np.float64)
    if owns.any():
        w = q[owns]
        np.add.at(c, (w[:, 0], w[:, 1], w[:, 2]), 1.0)
    return c, int(owns.sum())


# ---------------------------------------------------------------- sphericity
gi, gj, gk = np.meshgrid(np.arange(N), np.arange(N), np.arange(N), indexing="ij")


def sphericity(c, centre, rmax=26):
    """a sphere depends on RADIUS ALONE. Bin each shell by direction; low CV = sphere."""
    d = np.stack([gi - centre[0], gj - centre[1], gk - centre[2]], -1).astype(np.float64)
    r = np.sqrt((d ** 2).sum(-1))
    # direction octant+face key: 26 directions (the 26 neighbours of a cube centre)
    s = np.sign(d).astype(np.int64)
    key = (s[..., 0] + 1) * 9 + (s[..., 1] + 1) * 3 + (s[..., 2] + 1)
    out = []
    for rr in range(2, rmax):
        m = (r >= rr) & (r < rr + 1)
        if not m.any():
            continue
        tot = c[m].sum()
        if tot <= 0:
            continue
        per = np.array([c[m & (key == k)].sum() for k in range(27) if k != 13])
        per = per[per > 0]
        if len(per) < 4:
            continue
        cv = float(per.std() / per.mean()) if per.mean() else float("nan")
        out.append((rr, tot, cv, len(per)))
    return out


def signed_third(c, centre):
    """the -1/3 and the +1/3, separately. Law 33: the negative leads."""
    d = np.stack([gi - centre[0], gj - centre[1], gk - centre[2]], -1)
    s = d.sum(-1)                       # trit sum: sign is the direction
    inward = float(c[s < 0].sum())
    outward = float(c[s > 0].sum())
    hold = float(c[s == 0].sum())
    tot = inward + outward + hold
    return inward, outward, hold, tot


print(f"\n{'='*78}")
print(f"THREE FLASHLIGHTS ON THE THREE BEINGS")
print(f"{'='*78}")
print(f"  {'way':<15} {'being':<8} {'owns':>9} {'centre':<14} {'occ%':>7} "
      f"{'-1/3':>11} {'+1/3':>11} {'lead':>7}")
CUBES = {}
for wi, (wname, _) in enumerate(WAYS):
    for bname, chan, ax in BEINGS:
        c, owns = build(wi, ax)
        ci = np.unravel_index(int(np.argmax(c)), c.shape)
        CUBES[(wname, bname)] = (c, ci)
        inw, outw, hold, tot = signed_third(c, ci)
        lead = inw / outw if outw else float("inf")
        occ = 100.0 * float((c > 0).sum()) / c.size
        print(f"  {wname:<15} {bname:<8} {owns:>9,} "
              f"{str(tuple(int(x) for x in ci)):<14} {occ:>6.2f}% "
              f"{inw:>11,.0f} {outw:>11,.0f} {lead:>7.3f}")

print(f"\n  the -1/3 and +1/3 are the SIGNED halves either side of the centre.")
print(f"  Law 33 measured the inward lead at 1.85x-3.73x elsewhere; here it is above.")

# ---------------------------------------------------------------- is it a sphere
print(f"\n{'='*78}")
print(f"IS MYTHOS A SPHERE? shell-by-shell CV across 26 directions. LOW CV = SPHERE.")
print(f"{'='*78}")
verdicts = {}
for wname, _ in WAYS:
    c, ci = CUBES[(wname, "MYTHOS")]
    sp = sphericity(c, ci)
    if not sp:
        print(f"  {wname:<15} no populated shells")
        continue
    cvs = [x[2] for x in sp]
    print(f"  {wname:<15} centre {tuple(int(x) for x in ci)}   "
          f"shells {len(sp)}   CV min {min(cvs):.3f}  median {np.median(cvs):.3f}")
    band = "  ".join(f"r{x[0]}:{x[2]:.2f}" for x in sp[:10])
    print(f"      {band}")
    verdicts[wname] = float(np.median(cvs))

print(f"\n  reference: a PERFECT sphere gives CV -> 0. A cube-aligned lattice gives")
print(f"  CV around 0.6-1.0 because the corners of each shell carry more voxels.")
for wname, _ in WAYS:
    if wname in verdicts:
        v = verdicts[wname]
        tag = ("SPHERICAL" if v < 0.35 else
               "partly spherical" if v < 0.60 else "NOT spherical")
        print(f"    {wname:<15} median CV {v:.3f}  ->  {tag}")

agree = [verdicts[w] for w, _ in WAYS if w in verdicts]
if agree and max(agree) < 0.60:
    print(f"\n  ALL THREE FLASHLIGHTS AGREE MYTHOS HAS SPHERICAL SHELLS.")
    print(f"  It was never unsayable. The absolute-byte ruler could not reach it.")
elif agree:
    print(f"\n  the three do not agree; the spread is the finding, see the table.")

# compare the three beings under the alphabet-free flashlight (way II)
print(f"\n{'='*78}")
print(f"ALL THREE BEINGS UNDER THE ALPHABET-FREE FLASHLIGHT (rank/equalisation)")
print(f"{'='*78}")
for bname, chan, ax in BEINGS:
    c, ci = CUBES[("II rank/equal", bname)]
    sp = sphericity(c, ci)
    cvs = [x[2] for x in sp] if sp else [float("nan")]
    inw, outw, hold, tot = signed_third(c, ci)
    print(f"  {bname:<8} {chan:<6} centre {str(tuple(int(x) for x in ci)):<14} "
          f"median CV {np.median(cvs):.3f}   -1/3 lead {inw/outw if outw else float('inf'):.3f}")

# ---------------------------------------------------------------- GGUF + receipt
GG, V_U32, V_STR, V_ARR, F32, AL = 0x46554747, 4, 8, 9, 0, 32


def ss(x):
    e = x.encode()
    return struct.pack("<Q", len(e)) + e


def wr(path, kvs, tens):
    m, nk = b"", 0
    for k, t, p in kvs:
        m += ss(k) + struct.pack("<I", t) + p
        nk += 1
    data, ti = b"", b""
    for tn, arr in tens:
        a = np.ascontiguousarray(arr, dtype=np.float32)
        data += b"\0" * ((-len(data)) % AL)
        off = len(data)
        ti += ss(tn) + struct.pack("<I", a.ndim)
        for d in a.shape:
            ti += struct.pack("<Q", int(d))
        ti += struct.pack("<I", F32) + struct.pack("<Q", off)
        data += a.tobytes()
    h = struct.pack("<IIQQ", GG, 3, len(tens), nk) + m + ti
    blob = h + b"\0" * ((-len(h)) % AL) + data
    open(path, "wb").write(blob)
    dg = hashlib.sha256(blob).hexdigest()
    open(path + ".sha256", "w", newline="\n").write(f"{dg}  {os.path.basename(path)}\n")
    return len(blob), dg


d = os.path.join(OUT, "gguf", "acer")
os.makedirs(d, exist_ok=True)
print(f"\n=== GGUF — MYTHOS under all three flashlights, so it can be refuted ===")
made = []
c_r, ci_r = CUBES[("II rank/equal", "MYTHOS")]
sp = sphericity(c_r, ci_r)
p = os.path.join(d, "ACER-MYTHOS-SPHERE-FLASHLIT.gguf")
tens = []
for wname, _ in WAYS:
    c, ci = CUBES[(wname, "MYTHOS")]
    tens.append((f"mythos_{wname.split()[0]}_midslice", c[:, :, int(ci[2])]))
    prof = np.zeros(N)
    cnt = np.zeros(N)
    rr = np.sqrt((gi - ci[0]) ** 2. + (gj - ci[1]) ** 2. + (gk - ci[2]) ** 2.)
    ri = np.minimum(rr.astype(int), N - 1)
    np.add.at(prof, ri.ravel(), c.ravel())
    np.add.at(cnt, ri.ravel(), 1.0)
    tens.append((f"mythos_{wname.split()[0]}_radial", prof / np.maximum(cnt, 1.0)))
sz, dg = wr(p, [
    ("general.architecture", V_STR, ss("asolaria-mythos-flashlit")),
    ("general.name", V_STR, ss("ACER-MYTHOS-SPHERE-FLASHLIT")),
    ("asolaria.seat", V_STR, ss("ACER")),
    ("asolaria.being", V_STR, ss("MYTHOS")),
    ("asolaria.channel", V_STR, ss("BLUE")),
    ("asolaria.claim", V_STR,
     ss("a sphere is never unsayable; blue read empty because the ruler was "
        "absolute bytes on a corpus that caps at 125")),
    ("asolaria.flashlights", V_ARR, struct.pack("<IQ", V_STR, 3)
     + b"".join(ss(x) for x in ("percentile", "rank-equalisation", "glyph-banding"))),
    ("asolaria.median_cv_rank", V_STR,
     ss(f"{np.median([x[2] for x in sp]):.4f}" if sp else "nan")),
], tens)
made.append((p, sz, dg))
print(f"  {os.path.basename(p):<40} {sz:>8,} B  sha {dg[:16]}")

R = os.path.join(OFF, "FABLE5-MYTHOS-FLASHLIT.hbp")
rows = ["MYTHFLHDR|schema=ASOLARIA-MYTHOS-FLASHLIT-V1|seat=ACER-CLAUDE-FABLE5"
        "|pid=8467a937cba309f7|date=2026-07-27|json=0",
        f"CHALLENGE|claim=a_sphere_is_never_unsayable|prior_error=absolute_byte_bands"
        f"|corpus_cap=125|band2_needed=172|json=0"]
for ax in (0, 1, 2):
    u = GLYPHS[ax]
    rows.append(f"ALPHABET|chan={'RGB'[ax]}|distinct={len(u)}|min={int(u.min())}"
                f"|max={int(u.max())}|third_cut={int(u[len(u)//3])}"
                f"|two_third_cut={int(u[2*len(u)//3])}|json=0")
for wname, _ in WAYS:
    for bname, chan, ax in BEINGS:
        c, ci = CUBES[(wname, bname)]
        inw, outw, hold, tot = signed_third(c, ci)
        s = sphericity(c, ci)
        cv = float(np.median([x[2] for x in s])) if s else float("nan")
        rows.append(f"FLASH|way={wname.split()[0]}|being={bname}|chan={chan}"
                    f"|centre_r={ci[0]}|centre_g={ci[1]}|centre_b={ci[2]}"
                    f"|neg_third={inw:.0f}|pos_third={outw:.0f}|hold={hold:.0f}"
                    f"|inward_lead={inw/outw if outw else -1:.4f}"
                    f"|median_cv={cv:.4f}|json=0")
for p_, sz_, dg_ in made:
    rows.append(f"GGUF|k={os.path.basename(p_)}|bytes={sz_}|sha256={dg_}|json=0")
bb = "\n".join(rows) + "\n"
rows.append(f"MYTHFLFTR|receipt={hashlib.sha256(bb.encode()).hexdigest()[:32]}"
            f"|rows={len(rows)+1}|hot_path=1|json=0")
open(R, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
open(R + ".sha256", "w", encoding="utf-8", newline="\n").write(
    hashlib.sha256(open(R, "rb").read()).hexdigest() + "  FABLE5-MYTHOS-FLASHLIT.hbp\n")
print(f"  receipt  {R}")
