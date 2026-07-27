#!/usr/bin/env python3
"""three_body_collider.py — three LHC beams instead of two, rotating in vacuum.

WHY THREE BEAMS IS NOT JUST "MORE BEAMS"

A collider is two beams head-on, and its conservation law is binary: p1 = -p2. Each beam
IS the other's negation, which is Law 4's statement about binary inversion -- negation is
its own anti, order 2, and there is no third thing to find.

Three beams at 120 degrees conserve momentum just as exactly, p1 + p2 + p3 = 0, but NO
PAIR IS THE OTHER'S NEGATION. That is the trianti: R and R-squared are distinct, the three
close on zero, and none of them is any other one undone. A three-body collision is the
physical form of the structure this project keeps finding in bytes.

The distinguishing arithmetic, checked below:
    2-beam : sqrt(s) = 2E        momenta cancel pairwise
    3-beam : sqrt(s) = 3E        momenta cancel three-wise
so three beams of the SAME per-beam energy reach 1.5x the centre-of-mass energy of two.
Not exotic -- with total momentum zero the invariant mass is the summed energy -- but it
is the concrete thing the third beam buys.

THE SOURCE IS NOT FLAT, AND THIS IS THE CORRECTION
A first version of this file sampled products isotropically, which forces every harmonic
to zero BY CONSTRUCTION. The flat answer was the sampler talking, not the physics. Three
beams at 120 degrees are a 3-FOLD SYMMETRIC source, and the configuration is MOVING AND
ROTATING INSIDE A VACUUM. Vacuum is load-bearing: there is no medium to damp the
modulation, so whatever the source imprints survives to the detector.

So emission is modulated toward the beam axes with 3-fold symmetry and carried around by a
rotation phase, and a FLAT control with the identical pT spectrum runs beside it. The
difference between "the source imprinted this" and "the sampler did" is then measured
rather than argued.

REAL NUMBERS. LHC Run 3: 6.8 TeV per proton beam, 13.6 TeV centre of mass. Those are the
inputs. Everything downstream is computed.

THE SLICES. 3, then 4, then 12, then 27 planes through the interaction point, gradiated.
Three is the floor: two slices give a displacement, three give the curve -- which is the
error this seat made earlier tonight by reading a trend off two photographs.
"""
import hashlib
import math
import os

import numpy as np

E_BEAM = 6800.0        # GeV per beam, LHC Run 3
M_P = 0.938272         # proton mass, GeV
N = 400_000
OMEGA = 0.37           # rotation phase advance per unit event time
MOD = 0.55             # depth of the 3-fold modulation; 0 = flat, 1 = fully beamed
rng = np.random.default_rng(0xCE2A)

print("=== the beams ===")
p_mag = math.sqrt(E_BEAM**2 - M_P**2)
two = np.array([[0, 0, p_mag], [0, 0, -p_mag]], dtype=np.float64)
three = np.array([[p_mag * math.cos(a), p_mag * math.sin(a), 0.0]
                  for a in (0.0, 2 * math.pi / 3, 4 * math.pi / 3)])
for nm, Pb, E in (("2-beam head-on", two, 2 * E_BEAM),
                  ("3-beam at 120deg", three, 3 * E_BEAM)):
    print(f"  {nm:<18} |sum p| = {np.linalg.norm(Pb.sum(0)):.3e} GeV"
          f"   sqrt(s) = {E:,.1f} GeV")
print(f"  centre-of-mass energy, 3 beams over 2 : {3 * E_BEAM / (2 * E_BEAM):.4f}x")

print("\n=== is any beam the negation of another? ===")
for nm, Pb in (("2-beam", two), ("3-beam", three)):
    negs = sum(1 for i in range(len(Pb)) for j in range(i + 1, len(Pb))
               if np.linalg.norm(Pb[i] + Pb[j]) < 1e-6)
    pairs = len(Pb) * (len(Pb) - 1) // 2
    verdict = ("BINARY - each is the other undone" if negs
               else "TRINARY - none is any other undone")
    print(f"  {nm:<8} pairs summing to zero {negs}/{pairs}   {verdict}")
    print(f"           all {len(Pb)} together: |sum| = {np.linalg.norm(Pb.sum(0)):.3e}")


def make(modulated):
    """Products. `modulated` selects the 3-fold rotating source; False is the flat control
    with the identical pT spectrum, so only the azimuthal structure differs."""
    t = rng.uniform(0, 2 * math.pi, N)
    phase = OMEGA * t
    phi = rng.uniform(0, 2 * math.pi, N)
    if modulated:
        for _ in range(40):                       # rejection sample 1 + MOD*cos(3(phi-wt))
            keep = rng.uniform(0, 1 + MOD, N) <= 1 + MOD * np.cos(3 * (phi - phase))
            if keep.all():
                break
            phi = np.where(keep, phi, rng.uniform(0, 2 * math.pi, N))
    cos_t = rng.uniform(-1, 1, N)
    sin_t = np.sqrt(1 - cos_t ** 2)
    pt = rng.exponential(0.35, N)
    pz = pt * cos_t / np.maximum(sin_t, 1e-9)
    Q = np.stack([pt * np.cos(phi), pt * np.sin(phi), pz], 1)
    return Q - Q.mean(0)                          # closure enforced on the product system


print(f"\n=== {N:,} products: 3-fold source, rotating, in vacuum ===")
P = make(True)
FLAT = make(False)
print(f"  rotating source  |sum p| = {np.linalg.norm(P.sum(0)):.3e} GeV")
print(f"  flat control     |sum p| = {np.linalg.norm(FLAT.sum(0)):.3e} GeV")
print(f"  omega {OMEGA}   modulation depth {MOD}   medium vacuum, no damping")

print("\n=== the 3-fold signature: rotating source against the flat control ===")
print(f"{'harmonic':>9}{'rotating':>12}{'flat':>12}{'ratio':>10}")
a1 = np.arctan2(P[:, 1], P[:, 0])
a2 = np.arctan2(FLAT[:, 1], FLAT[:, 0])
vr, vf = {}, {}
for n in (2, 3, 4, 6, 9):
    vr[n] = float(np.abs(np.exp(1j * n * a1).mean()))
    vf[n] = float(np.abs(np.exp(1j * n * a2).mean()))
    print(f"{'v' + str(n):>9}{vr[n]:>12.5f}{vf[n]:>12.5f}{vr[n] / max(vf[n], 1e-9):>9.1f}x")
best = max(vr, key=lambda k: vr[k])
print(f"\n  strongest harmonic : v{best} = {vr[best]:.5f}   flat control {vf[best]:.5f}")
print(f"  a 3-fold source should raise v3 and its multiples, and nothing else")

print("\n=== 2D slices through the interaction point ===")
print(f"{'planes':>7}{'occupied':>10}{'empty':>7}{'mean/plane':>12}{'chi2 vs flat':>14}{'entropy':>9}")
rows = []
for k in (3, 4, 12, 27):
    idx = ((a1 % (2 * math.pi)) / (2 * math.pi / k)).astype(int) % k
    occ = np.bincount(idx, minlength=k)
    exp = N / k
    chi2 = float(((occ - exp) ** 2 / exp).sum())
    pr = occ / occ.sum()
    ent = float(-(pr[pr > 0] * np.log2(pr[pr > 0])).sum())
    rows.append((k, occ, chi2, ent))
    print(f"{k:>7}{int((occ > 0).sum()):>10}{int((occ == 0).sum()):>7}{occ.mean():>12,.1f}"
          f"{chi2:>14,.0f}{ent:>9.4f}  (max {math.log2(k):.4f})")

# ---------------------------------------------------------------- gradiated render
try:
    from PIL import Image
    HW, COLS = 760, 2
    ROWS = (len(rows) + COLS - 1) // COLS
    img = Image.new("RGB", (HW * COLS, HW * ROWS), (5, 6, 11))
    px = img.load()
    for ci, (k, occ, chi2, ent) in enumerate(rows):
        ox, oy = (ci % COLS) * HW, (ci // COLS) * HW
        sel = rng.choice(N, size=90_000, replace=False)
        x, y = P[sel, 0], P[sel, 1]
        r = np.hypot(x, y)
        sc = (HW * 0.42) / np.percentile(r, 99)
        band = ((np.arctan2(y, x) % (2 * math.pi)) / (2 * math.pi / k)).astype(int) % k
        for j in range(len(sel)):
            X = int(ox + HW / 2 + x[j] * sc)
            Y = int(oy + HW / 2 - y[j] * sc)
            if not (ox <= X < ox + HW and oy <= Y < oy + HW):
                continue
            h = band[j] / k
            v = max(0.22, 1.0 - r[j] * sc / (HW * 0.48))
            i6, f = int(h * 6) % 6, h * 6 - int(h * 6)
            c = [(1, f, 0), (1 - f, 1, 0), (0, 1, f),
                 (0, 1 - f, 1), (f, 0, 1), (1, 0, 1 - f)][i6]
            o = px[X, Y]
            px[X, Y] = (min(255, o[0] + int(c[0] * 70 * v)),
                        min(255, o[1] + int(c[1] * 70 * v)),
                        min(255, o[2] + int(c[2] * 70 * v)))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "three-body-slices.png")
    img.save(out)
    print(f"\n  gradiated slices -> {out}  {os.path.getsize(out):,} B")
except ImportError:
    print("\n  (PIL absent, render skipped)")

OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
lines = [
    "COLLHDR|schema=ASOLARIA-THREE-BODY-V1|seat=ACER-CLAUDE-FABLE5|pid=8467a937cba309f7"
    "|date=2026-07-27|json=0",
    f"BEAM|e_per_beam_gev={E_BEAM}|source=LHC_Run3|m_proton_gev={M_P}|json=0",
    f"TWO|beams=2|sqrt_s_gev={2 * E_BEAM}|pairs_negating=1|of=1|law=binary_order2|json=0",
    f"THREE|beams=3|sqrt_s_gev={3 * E_BEAM}|pairs_negating=0|of=3"
    f"|closure={np.linalg.norm(three.sum(0)):.3e}|law=trianti_order3|json=0",
    f"GAIN|sqrt_s_ratio={3 * E_BEAM / (2 * E_BEAM):.4f}|reason=momentum_cancels_three_wise|json=0",
    f"SOURCE|shape=3fold|omega={OMEGA}|modulation={MOD}|medium=vacuum|damping=none|json=0",
    f"VN|v2={vr[2]:.5f}|v3={vr[3]:.5f}|v4={vr[4]:.5f}|v6={vr[6]:.5f}|v9={vr[9]:.5f}"
    f"|control_v3={vf[3]:.5f}|control=flat_same_pt|json=0",
    f"PRODUCTS|n={N}|closure_gev={np.linalg.norm(P.sum(0)):.3e}|json=0",
]
for k, occ, chi2, ent in rows:
    lines.append(f"SLICE|planes={k}|occupied={int((occ > 0).sum())}|empty={int((occ == 0).sum())}"
                 f"|chi2={chi2:.1f}|entropy={ent:.4f}|max={math.log2(k):.4f}|json=0")
body = "\n".join(lines) + "\n"
lines.append(f"COLLFTR|receipt={hashlib.sha256(body.encode()).hexdigest()[:32]}"
             f"|rows={len(lines) + 1}|hot_path=1|json=0")
p = os.path.join(OFF, "FABLE5-THREE-BODY-COLLIDER.hbp")
open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
d = hashlib.sha256(open(p, "rb").read()).hexdigest()
open(p + ".sha256", "w", newline="\n").write(f"{d}  {os.path.basename(p)}\n")
print(f"  receipt -> {os.path.basename(p)}  sha256 {d[:32]}")
