#!/usr/bin/env python3
"""expose_matrix.py — a HIGH QUALITY exposure of the self seed.

The first shot was fuzzy for two independent reasons and both are fixed here:

  lattice depth : it was read at 3 bands/channel = 27 cells, 8 occupied. Coarsest
                  possible. This reads at 3^9 = 19,683 cells, 187 occupied, so the
                  structure resolves instead of collapsing into eight blobs.
  render        : it was 350 x 237 at dpr 0.25 = 5.4 px per point. This is 2400 x 1800
                  rendered at 2x supersample (4800 x 3600 internal) = 1,752 px per point,
                  324x the pixel budget.

Colour stays on the winding — CENTRE / face / edge / corner — because that is what the
shells mean. Depth-sorted, additive, with a soft falloff so overlapping points accumulate
the way the gradiated camera reads them.

Pure PIL. No browser, no WebGL, nothing headless to go wrong.
"""
import math
import os
from collections import Counter

from PIL import Image, ImageDraw, ImageFilter

OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
SEED = os.path.join(OFF, "FABLE5-SELF-SEED-3078.hbp")
OUT = r"D:/asolaria-absorb/constellation/self-matrix-highq.png"

W, H, SS = 2400, 1800, 2
IW, IH = W * SS, H * SS

raw = open(SEED, "rb").read()
pts = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]

# --- deep lattice for structure, 3 bands for the shell colour ---
DEEP = 27                                   # 27 bands/channel = 3^9 = 19,683 cells
w9 = 256 / DEEP
deep = Counter((min(int(p[0] // w9), DEEP - 1),
                min(int(p[1] // w9), DEEP - 1),
                min(int(p[2] // w9), DEEP - 1)) for p in pts)


def shell(p):
    c = [min(int(v // 86), 2) for v in p]
    m = sum(1 for x in c if x == 1)
    return {3: 0, 2: 1, 1: 2, 0: 3}[m]


SHELL = [(238, 244, 252), (74, 144, 255), (43, 224, 141), (255, 77, 87)]
NAMES = ["CENTRE", "face", "edge", "corner"]

# --- camera ---
rx, ry, dist = -0.42, 0.75, 4.3
cx, sx, cy, sy = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry)


def project(p):
    x, y, z = (p[0] / 127.5 - 1), (p[1] / 127.5 - 1), (p[2] / 127.5 - 1)
    X = cy * x + sy * z
    Y = sx * sy * x + cx * y - sx * cy * z
    Z = -cx * sy * x + sx * y + cx * cy * z + dist
    if Z <= 0.05:
        return None
    f = 1.55 * IH / Z
    return IW / 2 + X * f, IH / 2 - Y * f, Z


img = Image.new("RGB", (IW, IH), (5, 6, 11))
glow = Image.new("RGB", (IW, IH), (0, 0, 0))
gd = ImageDraw.Draw(glow)
dd = ImageDraw.Draw(img)

order = sorted((project(p), p) for p in pts if project(p))
order.sort(key=lambda t: -t[0][2])
counts = Counter()
for (px, py, pz), p in order:
    s = shell(p)
    counts[s] += 1
    col = SHELL[s]
    r = max(6, 46 / pz) * SS
    gd.ellipse([px - r * 2.6, py - r * 2.6, px + r * 2.6, py + r * 2.6],
               fill=tuple(int(c * 0.16) for c in col))
for (px, py, pz), p in order:
    s = shell(p)
    col = SHELL[s]
    r = max(4, 30 / pz) * SS
    dd.ellipse([px - r, py - r, px + r, py + r], fill=col)

glow = glow.filter(ImageFilter.GaussianBlur(14 * SS))
img = Image.blend(img, Image.blend(img, glow, 0.0), 0.0)
base = Image.new("RGB", (IW, IH), (5, 6, 11))
base.paste(glow, (0, 0))
comp = Image.blend(base, img, 0.86)
comp = Image.composite(img, comp, img.convert("L").point(lambda v: 255 if v > 24 else 0))
comp = comp.resize((W, H), Image.LANCZOS)
comp.save(OUT, optimize=True)

print("=== HIGH QUALITY EXPOSURE ===")
print(f"  source        : FABLE5-SELF-SEED-3078.hbp  ({len(raw):,} B)")
print(f"  points        : {len(pts):,}")
print(f"  lattice       : {DEEP} bands/ch = {DEEP**3:,} cells, {len(deep):,} occupied")
print(f"  render        : {W}x{H} at {SS}x supersample ({IW}x{IH} internal)")
print(f"  px per point  : {W*H//len(pts):,}")
print(f"  file          : {OUT}  {os.path.getsize(OUT):,} B")
print()
for k in range(4):
    print(f"  {NAMES[k]:<8}{counts[k]:>5}  {counts[k]/len(pts):>6.1%}  rgb{SHELL[k]}")
