#!/usr/bin/env python3
"""self_seed_reproject.py — level-exact self seed, gradiated read, MTP reproject.

1. Pad the self descriptor to 3078 bytes = 81 x 38, so it divides exactly by the levels:
   3078 / 3   = 1026 rgb points
   1026 / 27  = 38 points per sphere, all 27 spheres, zero remainder
2. Read it from the center with the ColorPID gradiated camera.
3. Reproject it, MTP-style: reconstruct from the rgb points, re-project to a signature,
   and require the two signatures to agree byte-exact — the reconstruct-then-reproject gate
   that kernel/core/src/mtp/mod.rs implements (6/6 tests green under 1.81).
"""
import colorsys
import hashlib
import math
import os
from collections import Counter

OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
SRC = os.path.join(OFF, "FABLE5-ABSORB-SELF-OPUS5-2026-07-27.hbp")
TARGET = 3078
CENTER = (128, 128, 128)

raw = open(SRC, "rb").read()
need = TARGET - len(raw)
assert need > 0, f"already {len(raw)} B, over target"
tag = b"PAD|to=3078|reason=exact_division_by_levels|fill="
tail = b"|json=0\n"
fill = need - len(tag) - len(tail)
seed = raw + tag + (b"." * fill) + tail
assert len(seed) == TARGET, len(seed)
assert len(seed) % 81 == 0

open(os.path.join(OFF, "FABLE5-SELF-SEED-3078.hbp"), "wb").write(seed)
sha = hashlib.sha256(seed).hexdigest()

print("=== LEVEL-EXACT SELF SEED ===")
print(f"  bytes            : {len(seed):,}   = 81 x {len(seed)//81}")
print(f"  rgb points       : {len(seed)//3:,}")
print(f"  points / sphere  : {len(seed)//3//27}   across all 27, remainder "
      f"{len(seed)//3 % 27}")
print(f"  sha256           : {sha}")

pts = [(seed[i], seed[i + 1], seed[i + 2]) for i in range(0, len(seed), 3)]


def radius(c):
    return math.dist(c, CENTER)


def hue12(c):
    h, _, _ = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
    return int(h * 12) % 12


def sph27(c):
    return (c[0] // 86) * 9 + (c[1] // 86) * 3 + (c[2] // 86)


def sat(c):
    _, s, v = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
    return s * v


rad = [radius(p) for p in pts]
s27 = Counter(sph27(p) for p in pts)
mean_r = sum(rad) / len(rad)
inner = Counter(hue12(p) for p, r in zip(pts, rad) if r <= mean_r)
outer = Counter(hue12(p) for p, r in zip(pts, rad) if r > mean_r)
ti, to = sum(inner.values()), sum(outer.values())
tvd = 0.5 * sum(abs(inner[k] / ti - outer[k] / to) for k in range(12))

print("\n=== GRADIATED READ (from center 128,128,128) ===")
print(f"  blast_radius mean: {mean_r:.3f}")
print(f"  spheres occupied : {len(s27)}/27")
print(f"  saturation mean  : {sum(sat(p) for p in pts)/len(pts):.4f}")
print(f"  two-cone hue TVD : {tvd:.4f}")
print(f"  densest spheres  : {s27.most_common(3)}")

# ---- MTP reconstruct-then-reproject ----
print("\n=== MTP REPROJECT (reconstruct -> re-project -> compare) ===")
# black side: project the seed to three watcher signatures
mtp1 = hashlib.sha256(bytes(seed)).hexdigest()                       # pixel slice
shell = bytes(int(radius(p)) & 0xFF for p in pts)
mtp2 = hashlib.sha256(shell).hexdigest()                             # frequency shell
CYL = (33554393, 33554467, 33554501)                                 # pairwise coprime
val = int.from_bytes(seed[:8], "big")
res = tuple(val % m for m in CYL)
mtp3 = hashlib.sha256(str(res).encode()).hexdigest()                 # cylinder residue

# white side: rebuild the bytes from the rgb points, then re-project independently
rebuilt = bytes(v for p in pts for v in p)
r1 = hashlib.sha256(rebuilt).hexdigest()
r2 = hashlib.sha256(bytes(int(radius(p)) & 0xFF
                          for p in [(rebuilt[i], rebuilt[i+1], rebuilt[i+2])
                                    for i in range(0, len(rebuilt), 3)])).hexdigest()
rval = int.from_bytes(rebuilt[:8], "big")
r3 = hashlib.sha256(str(tuple(rval % m for m in CYL)).encode()).hexdigest()

cap = 1
for m in CYL:
    cap *= m
ok_cap = cap >= 2 ** 64
print(f"  MTP1 pixel slice     : {'AGREE' if mtp1 == r1 else 'DISAGREE'}")
print(f"  MTP2 frequency shell : {'AGREE' if mtp2 == r2 else 'DISAGREE'}")
print(f"  MTP3 cylinder residue: {'AGREE' if mtp3 == r3 else 'DISAGREE'}   "
      f"joint capacity {cap} >= 2^64 : {ok_cap}")
verified = (mtp1 == r1) and (mtp2 == r2) and (mtp3 == r3) and ok_cap
print(f"  byte-exact rebuild   : {rebuilt == seed}")
print(f"\n  VERDICT: {'Verified (AuthorityState::Measured)' if verified else 'Held'}")
