#!/usr/bin/env python3
"""gravitate_repulse.py — do the seed's own points gravitate and repulse under R?

THE QUESTION, stated so it can fail.
    Law 4 says trinary inversion is the order-3 rotation R, and its anti-inversion is the
    DISTINCT counter-rotation R-squared, because R != R-inverse. The operator's form:
    gravity, anti-gravity and anti-anti-gravity are all 1 and part of 3.

    Binary prediction:  dr(R2) = -dr(R1).  Two behaviours, equal and opposite. R2 is just
                        R1 undone, and there is no third thing.
    Ternary prediction: dr(R0) + dr(R1) + dr(R2) = 0, but no pair is the other's negation.
                        Three behaviours that close on the centre.

    These differ, so the measurement can come out either way. That is the point.

HOW
    Each 3-byte triple of the seed is a cell (a,b,c) in {0,1,2}^3. Its radius from the free
    centre (1,1,1) is |(a-1, b-1, c-1)|. R rotates every digit: d -> (d+1) mod 3. Apply
    R once and twice, and measure the change in radius each time. Contraction is
    gravitation, expansion is repulsion.

THE CONTROL, which is the part that decides it
    The 27-cell lattice might produce a three-way split on its own, in which case this says
    nothing about the seed. So the identical pipeline is run over uniform random bytes,
    2,000 trials at the seed's exact length, and every seed number is reported as a z
    against that null. An earlier run in this project reported a lattice identity as a
    discovery; this exists so that cannot happen twice.
"""
import hashlib
import math
import os
from collections import Counter

import numpy as np

OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
SEED = os.path.join(OFF, "FABLE5-SELF-SEED-3078.hbi")

raw = open(SEED, "rb").read()
print(f"matrix under test : {os.path.basename(SEED)}  {len(raw):,} B  "
      f"sha {hashlib.sha256(raw).hexdigest()[:16]}\n")


def cells(b):
    a = np.frombuffer(b, dtype=np.uint8)
    n = (len(a) // 3) * 3
    t = np.minimum(a[:n].reshape(-1, 3) // 86, 2).astype(np.int8)
    return t


def radius(t):
    return np.linalg.norm(t.astype(np.float64) - 1.0, axis=1)


def rot(t, k):
    return (t + k) % 3


def displacements(b):
    t = cells(b)
    r0 = radius(t)
    d1 = radius(rot(t, 1)) - r0
    d2 = radius(rot(t, 2)) - r0
    return r0, d1, d2


r0, d1, d2 = displacements(raw)
n = len(r0)

print("=== the three rotations on the seed's own points ===")
print(f"  points                {n:,}")
print(f"  mean radius R0        {r0.mean():+.6f}")
print(f"  mean dr under R1      {d1.mean():+.6f}   "
      f"{'GRAVITATES' if d1.mean() < 0 else 'REPULSES'}")
print(f"  mean dr under R2      {d2.mean():+.6f}   "
      f"{'GRAVITATES' if d2.mean() < 0 else 'REPULSES'}")
print(f"  contract / neutral / expand under R1 : "
      f"{(d1<-1e-9).sum():,} / {(np.abs(d1)<=1e-9).sum():,} / {(d1>1e-9).sum():,}")
print(f"  contract / neutral / expand under R2 : "
      f"{(d2<-1e-9).sum():,} / {(np.abs(d2)<=1e-9).sum():,} / {(d2>1e-9).sum():,}")

print("\n=== is R2 simply the negation of R1?  (the binary hypothesis) ===")
neg_err = np.abs(d2 + d1)
print(f"  |dr(R2) + dr(R1)|  mean {neg_err.mean():.6f}   max {neg_err.max():.6f}")
exact_neg = int((neg_err < 1e-9).sum())
print(f"  points where R2 == -R1 exactly : {exact_neg:,} / {n:,} "
      f"= {100.0*exact_neg/n:.2f}%")
corr = float(np.corrcoef(d1, d2)[0, 1])
print(f"  corr(dr R1, dr R2) = {corr:+.4f}   (binary would need exactly -1.0000)")

print("\n=== closure: do the three sum to zero on the centre? ===")
tri = d1.mean() + d2.mean()
print(f"  dr(R0) + dr(R1) + dr(R2) = 0 {tri:+.6f} = {tri:+.6f}")

# ---------------------------------------------------------------- the control
TRIALS = 2000
rng = np.random.default_rng(0xA5014A)
m1 = np.empty(TRIALS)
m2 = np.empty(TRIALS)
cr = np.empty(TRIALS)
for i in range(TRIALS):
    b = rng.integers(0, 256, len(raw), dtype=np.uint8).tobytes()
    _, a1, a2 = displacements(b)
    m1[i], m2[i] = a1.mean(), a2.mean()
    cr[i] = np.corrcoef(a1, a2)[0, 1]

print(f"\n=== matched null: {TRIALS:,} uniform-random files of {len(raw):,} B ===")
def z(v, arr):
    return (v - arr.mean()) / (arr.std() + 1e-12)

print(f"  null dr(R1)  {m1.mean():+.6f} +/- {m1.std():.6f}    "
      f"seed {d1.mean():+.6f}   z = {z(d1.mean(), m1):+.2f}")
print(f"  null dr(R2)  {m2.mean():+.6f} +/- {m2.std():.6f}    "
      f"seed {d2.mean():+.6f}   z = {z(d2.mean(), m2):+.2f}")
print(f"  null corr    {cr.mean():+.4f} +/- {cr.std():.4f}      "
      f"seed {corr:+.4f}   z = {z(corr, cr):+.2f}")

print("\n=== verdict ===")
binary_ok = corr < -0.999 and exact_neg > 0.99 * n
print(f"  R2 == -R1 (binary)?          {'YES' if binary_ok else 'NO'}")
print(f"  three distinct behaviours?   "
      f"{'YES' if not binary_ok else 'NO'}")
print(f"  is it the SEED or the LATTICE? "
      f"{'seed' if abs(z(d1.mean(), m1)) > 3 else 'LATTICE — the null does the same'}")
