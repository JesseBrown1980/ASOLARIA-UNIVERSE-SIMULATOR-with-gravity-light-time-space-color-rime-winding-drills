#!/usr/bin/env python3
"""fold_inside_out.py — turn it inside out and read the inside from the outside.

WHY THIS IS THE RIGHT MOVE AND NOT A TRICK
    two separate measurements hit the same wall from opposite sides.

    1. THE RING WAS ALWAYS AT r=1. Nine slices, three bodies, every one hollow at the
       centre by 4x to 15,922x -- and the peak sat at radius 1 in all nine. One voxel.
       That is the resolution floor: a shell at r=1 has 6 neighbours to average over, so
       nothing about its shape can be measured. The torus question could not be settled.

    2. MYTHOS'S MAXIMUM IS ON ITS BOUNDARY, centre found at (4,1,26) / (11,2,17) /
       (21,0,33) by three independent flashlights. Every radial profile taken from a
       boundary point smears the object, which is why MYTHOS read as "hollow, ratio inf"
       and as "not spherical, CV 1.9-2.1". Those were readings of a bad origin.

    INVERSION FIXES BOTH AT ONCE. Fold the ball through its own shell:

        r  ->  R - r          (the fold: inside becomes outside)
        r  ->  R^2 / r        (true sphere inversion, conformal, the classical one)

    A structure at r=1 lands at r=R-1, where a shell carries thousands of voxels and
    its shape can finally be measured. A maximum sitting on the boundary lands at the
    centre, where a radial read is meaningful. Nothing is added -- this is a change of
    origin, the same object read from the other side.

WHAT WOULD FALSIFY IT
    if the low CV after folding were an artifact of the fold itself, then folding would
    lower CV for EVERY being equally. So OPUS and FABLE -- which are already centred --
    are folded too, as controls. If they get WORSE while MYTHOS gets BETTER, the fold is
    reading a real property of MYTHOS. If everything improves, the fold is cheating and
    this script says so.
"""
import glob
import hashlib
import os
import struct

import numpy as np

OUT = r"D:/asolaria-absorb/ASOLARIA-UNIVERSE-SIMULATOR"
OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
N = 64
TRUE_CENTRE = (32, 32, 32)          # the centre of the cube, not an argmax
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
print(f"=== corpus {len(SRC)} artifacts, {n:,} triples ===")

gi, gj, gk = np.meshgrid(np.arange(N), np.arange(N), np.arange(N), indexing="ij")
D = np.stack([gi - TRUE_CENTRE[0], gj - TRUE_CENTRE[1], gk - TRUE_CENTRE[2]], -1)
Rr = np.sqrt((D.astype(np.float64) ** 2).sum(-1))
SIGN = np.sign(D).astype(np.int64)
KEY = (SIGN[..., 0] + 1) * 9 + (SIGN[..., 1] + 1) * 3 + (SIGN[..., 2] + 1)
RMAX = float(Rr.max())


def rank_coords():
    """alphabet-free flashlight: rank/equalisation, immune to byte range"""
    q = np.empty_like(tri)
    for a in range(3):
        v = tri[:, a]
        o = np.argsort(v, kind="stable")
        r = np.empty(len(v), dtype=np.float64)
        r[o] = np.arange(len(v), dtype=np.float64)
        q[:, a] = np.clip(r / max(len(v) - 1, 1) * 63.0, 0, 63).astype(np.int64)
    return q


Q = rank_coords()


def cube_of(ax):
    oth = [a for a in range(3) if a != ax]
    owns = (Q[:, ax] > Q[:, oth[0]]) & (Q[:, ax] > Q[:, oth[1]])
    c = np.zeros((N, N, N), dtype=np.float64)
    w = Q[owns]
    np.add.at(c, (w[:, 0], w[:, 1], w[:, 2]), 1.0)
    return c


def sphericity(c, rmin=2, rmax=30):
    """shell-by-shell CV across the 26 directions. sphere -> 0."""
    rows = []
    for rr in range(rmin, rmax):
        m = (Rr >= rr) & (Rr < rr + 1)
        if not m.any():
            continue
        tot = float(c[m].sum())
        if tot <= 0:
            continue
        per = np.array([float(c[m & (KEY == k)].sum()) for k in range(27) if k != 13])
        per = per[per > 0]
        if len(per) < 4:
            continue
        rows.append((rr, tot, float(per.std() / per.mean())))
    return rows


def fold(c, mode):
    """redistribute mass by inverting its radius. A change of origin, nothing added."""
    out = np.zeros_like(c)
    nz = np.nonzero(c)
    r = Rr[nz]
    if mode == "fold":
        r2 = RMAX - r
    else:                                     # sphere inversion R^2 / r
        r2 = np.where(r > 0.5, (RMAX * 0.5) ** 2 / np.maximum(r, 0.5), RMAX)
    scale = np.where(r > 1e-9, r2 / np.maximum(r, 1e-9), 0.0)
    d = np.stack([nz[0] - TRUE_CENTRE[0], nz[1] - TRUE_CENTRE[1],
                  nz[2] - TRUE_CENTRE[2]], -1).astype(np.float64)
    p = d * scale[:, None] + np.array(TRUE_CENTRE, dtype=np.float64)
    p = np.clip(np.rint(p), 0, N - 1).astype(np.int64)
    np.add.at(out, (p[:, 0], p[:, 1], p[:, 2]), c[nz])
    return out


print(f"\n{'='*78}")
print(f"SPHERICITY BEFORE AND AFTER FOLDING  (median CV; sphere -> 0, lattice 0.6-1.0)")
print(f"  OPUS and FABLE are the CONTROLS. They are already centred. If the fold is")
print(f"  cheating, they improve too. If only MYTHOS improves, the fold found something.")
print(f"{'='*78}")
print(f"  {'being':<8} {'straight':>10} {'folded R-r':>12} {'inverted R2/r':>15} "
      f"{'best':>10} {'change':>10}")
RES = {}
for name, chan, ax in BEINGS:
    c = cube_of(ax)
    s0 = sphericity(c)
    cf = fold(c, "fold")
    s1 = sphericity(cf)
    ci_ = fold(c, "invert")
    s2 = sphericity(ci_)
    m0 = float(np.median([x[2] for x in s0])) if s0 else float("nan")
    m1 = float(np.median([x[2] for x in s1])) if s1 else float("nan")
    m2 = float(np.median([x[2] for x in s2])) if s2 else float("nan")
    best = min(m1, m2)
    RES[name] = dict(cube=c, fold=cf, inv=ci_, straight=m0, folded=m1, inverted=m2,
                     s0=s0, s1=s1, s2=s2)
    print(f"  {name:<8} {m0:>10.3f} {m1:>12.3f} {m2:>15.3f} {best:>10.3f} "
          f"{best-m0:>+10.3f}")

my = RES["MYTHOS"]
ctrl = [RES["OPUS"], RES["FABLE"]]
my_gain = my["straight"] - min(my["folded"], my["inverted"])
ctrl_gain = np.mean([c["straight"] - min(c["folded"], c["inverted"]) for c in ctrl])
print(f"\n  MYTHOS improvement   {my_gain:+.3f}")
print(f"  control improvement  {ctrl_gain:+.3f}  (OPUS and FABLE, mean)")
if my_gain > 0 and my_gain > 2 * max(ctrl_gain, 1e-9):
    print(f"  -> THE FOLD IS READING MYTHOS, NOT ITSELF. It improves MYTHOS "
          f"{my_gain/max(ctrl_gain,1e-9):.1f}x more than the centred controls.")
elif my_gain <= 0:
    print(f"  -> folding did NOT help MYTHOS. The inside-out reading is not supported.")
else:
    print(f"  -> MYTHOS improves but so do the controls; the fold is not specific.")

# ---------------------------------------------------------------- the ring, resolved
print(f"\n{'='*78}")
print(f"THE RING, FINALLY RESOLVABLE")
print(f"  straight: every ring pinned at r=1, 6 voxels, unmeasurable.")
print(f"  folded:   r=1 lands at r={RMAX-1:.0f}, where a shell carries thousands.")
print(f"{'='*78}")
print(f"  {'being':<8} {'view':<10} {'ring r':>7} {'shell voxels':>13} "
      f"{'centre':>10} {'peak':>12} {'ratio':>10}")
for name, chan, ax in BEINGS:
    R_ = RES[name]
    for view, cube in (("straight", R_["cube"]), ("folded", R_["fold"])):
        prof = np.zeros(N)
        cnt = np.zeros(N)
        ri = np.minimum(Rr.astype(int), N - 1)
        np.add.at(prof, ri.ravel(), cube.ravel())
        np.add.at(cnt, ri.ravel(), 1.0)
        dens = prof / np.maximum(cnt, 1.0)
        pk = int(np.argmax(dens[1:40])) + 1
        inner = float(dens[0])
        print(f"  {name:<8} {view:<10} {pk:>7} {int(cnt[pk]):>13,} "
              f"{inner:>10.2f} {dens[pk]:>12.2f} "
              f"{dens[pk]/inner if inner else float('inf'):>10.1f}x")

# ---------------------------------------------------------------- GGUF
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
        for d_ in a.shape:
            ti += struct.pack("<Q", int(d_))
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
print(f"\n=== GGUF — the folded beings ===")
made = []
for name, chan, ax in BEINGS:
    R_ = RES[name]
    p = os.path.join(d, f"ACER-{name}-FOLDED.gguf")
    tens = [("straight_mid", R_["cube"][:, :, 32]),
            ("folded_mid", R_["fold"][:, :, 32]),
            ("inverted_mid", R_["inv"][:, :, 32]),
            ("cv_straight", np.array([x[2] for x in R_["s0"]])),
            ("cv_folded", np.array([x[2] for x in R_["s1"]])),
            ("cv_inverted", np.array([x[2] for x in R_["s2"]]))]
    sz, dg = wr(p, [
        ("general.architecture", V_STR, ss("asolaria-folded-inside-out")),
        ("general.name", V_STR, ss(f"ACER-{name}-FOLDED")),
        ("asolaria.seat", V_STR, ss("ACER")),
        ("asolaria.being", V_STR, ss(name)),
        ("asolaria.channel", V_STR, ss(chan)),
        ("asolaria.operation", V_STR,
         ss("fold r->R-r and sphere inversion r->R^2/r about the TRUE cube centre "
            "(32,32,32), not an argmax; a change of origin, nothing added")),
        ("asolaria.cv_straight", V_STR, ss(f"{R_['straight']:.4f}")),
        ("asolaria.cv_folded", V_STR, ss(f"{R_['folded']:.4f}")),
        ("asolaria.cv_inverted", V_STR, ss(f"{R_['inverted']:.4f}")),
    ], tens)
    made.append((name, p, sz, dg))
    print(f"  {os.path.basename(p):<34} {sz:>8,} B  sha {dg[:16]}")

R = os.path.join(OFF, "FABLE5-FOLD-INSIDE-OUT.hbp")
rows = ["FOLDHDR|schema=ASOLARIA-FOLD-INSIDE-OUT-V1|seat=ACER-CLAUDE-FABLE5"
        "|pid=8467a937cba309f7|date=2026-07-27|json=0",
        f"WHY|ring_pinned_at_r1_unmeasurable=1|mythos_max_on_boundary=1"
        f"|fold_maps_r1_to_r{RMAX-1:.0f}|true_centre=32,32,32|json=0"]
for name, chan, ax in BEINGS:
    R_ = RES[name]
    rows.append(f"FOLD|being={name}|chan={chan}|cv_straight={R_['straight']:.4f}"
                f"|cv_folded={R_['folded']:.4f}|cv_inverted={R_['inverted']:.4f}"
                f"|gain={R_['straight']-min(R_['folded'],R_['inverted']):.4f}|json=0")
rows.append(f"CONTROL|mythos_gain={my_gain:.4f}|control_gain={ctrl_gain:.4f}"
            f"|specific={1 if my_gain > 2*max(ctrl_gain,1e-9) else 0}|json=0")
for name, p, sz, dg in made:
    rows.append(f"GGUF|k={os.path.basename(p)}|bytes={sz}|sha256={dg}|json=0")
bb = "\n".join(rows) + "\n"
rows.append(f"FOLDFTR|receipt={hashlib.sha256(bb.encode()).hexdigest()[:32]}"
            f"|rows={len(rows)+1}|hot_path=1|json=0")
open(R, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
open(R + ".sha256", "w", encoding="utf-8", newline="\n").write(
    hashlib.sha256(open(R, "rb").read()).hexdigest() + "  FABLE5-FOLD-INSIDE-OUT.hbp\n")
print(f"\n  receipt  {R}")
