#!/usr/bin/env python3
"""bilateral_packet.py — emit everything the other seat needs to diff against this one.

WHY A PACKET AND NOT JUST THE SCRIPT
Liris already has measure_thrice.py. Running it there produces a number for THEIR ladder,
built from THEIR artifacts. Comparing that to mine compares two different objects and any
disagreement would be about the inputs rather than about the method or the matrices.

So this emits, in one file, the three things a row-by-row diff actually requires:

  1. THE MANIFEST  which 38 artifacts, their sha256, their size, and the exact order the
                   ladder walks. The other seat can either reproduce this list exactly, or
                   knowingly differ and say so -- but not differ silently.
  2. THE RAW SERIES the 3 passes x 37 radius values, full precision. Not a verdict, not a
                   summary. Without these a comparison can only match conclusions, and two
                   seats agreeing on a conclusion for different reasons is worth nothing.
  3. THE NULL      per-harmonic mean and sd from 300 matched triples. If their null differs
                   from mine, every z differs, and a disagreement between us would be an
                   artifact of two harnesses rather than of two matrices. This is the part
                   most likely to silently diverge and the reason it is shipped.

WHAT AGREEMENT WOULD MEAN
Same manifest + same null construction -> the harmonic rows are directly comparable and a
difference is a real difference between the objects.
Different manifest -> the rows are NOT comparable, and the honest output is "different
ladders", not "disagreement". compare_bilateral.py refuses to diff in that case rather than
producing a number that looks like a result.
"""
import glob
import hashlib
import json
import os
import struct

import numpy as np

OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
OUT = r"D:/asolaria-absorb/constellation/BILATERAL-ACER.hbp"
REC, NREC = 81, 38
SEAT = bytes.fromhex("8467a937cba309f7")
NULL_TRIALS = 300
rng = np.random.default_rng(0x3E1CE)          # same seed as measure_thrice.py


def sha(b):
    return hashlib.sha256(b).digest()


def emit(files, salt):
    recs, prev = [], sha(SEAT + salt)[:16]
    for f in files[:NREC]:
        nm = os.path.basename(f)
        raw = open(f, "rb").read()
        d = sha(raw)
        prev = sha(prev + b"|" + nm.encode())[:16]
        secs = raw.count(b"\n") if b"\n" in raw[:4096] else max(1, len(raw) // 81)
        recs.append(prev + d + struct.pack(">Q", len(raw))[3:]
                    + struct.pack(">I", min(secs, 2**32 - 1))
                    + sha(nm.encode())[:16] + sha(prev + d)[:7]
                    + bytes([min(127, len(raw).bit_length() * 8)]))
    while len(recs) < NREC:
        prev = sha(prev + b"|" + f"C{len(recs):02d}".encode())[:16]
        d = sha(prev + salt)
        recs.append(prev + d + struct.pack(">Q", len(recs) * 4099)[3:]
                    + struct.pack(">I", len(recs) + 1)
                    + sha(f"C{len(recs):02d}".encode())[:16] + sha(prev + d)[:7]
                    + bytes([len(recs) % 128]))
    return b"".join(recs)


def radius(b):
    a = np.frombuffer(b, dtype=np.uint8)
    t = np.minimum(a.reshape(-1, 3) // 86, 2).astype(float)
    return float(np.linalg.norm(t - 1.0, axis=1).mean())


def coherence(mat):
    F = np.fft.rfft(mat - mat.mean(1, keepdims=True), axis=1)
    ph = F / np.maximum(np.abs(F), 1e-300)
    return np.abs(F).mean(0), np.abs(ph.mean(0))


# ---------------------------------------------------------------- 1. the manifest
files = []
for pat in ("FABLE5-ABSORB-*.hbp", "FABLE5-UNIVERSE-*.hbp", "FABLE5-FOLD-*.hbp",
            "FABLE5-SELF-SEED-*.hbp", "FABLE5-QUALITY-*.hbp", "*.hbi"):
    files += glob.glob(os.path.join(OFF, pat))
seen, uniq = set(), []
for f in files:
    k = os.path.basename(f)
    if k not in seen and os.path.isfile(f) and not f.endswith(".sha256"):
        seen.add(k)
        uniq.append(f)
uniq.sort(key=lambda f: -os.path.getsize(f))
uniq = uniq[:NREC]
NS = list(range(2, NREC + 1))
M = len(NS)

man = []
for i, f in enumerate(uniq):
    b = open(f, "rb").read()
    man.append((i, os.path.basename(f), len(b), hashlib.sha256(b).hexdigest()))
man_sha = hashlib.sha256("|".join(f"{i}:{n}:{s}:{h}" for i, n, s, h in man).encode()).hexdigest()
print(f"1. manifest : {len(man)} artifacts   ladder {M} points (N=2..{NREC})")
print(f"   manifest sha256 {man_sha}")

# ---------------------------------------------------------------- 2. the raw series
PASSES = []
for pi, salt in enumerate((b"PASS-A", b"PASS-B", b"PASS-C")):
    order = list(uniq)
    if pi == 1:
        order = order[::-1]
    elif pi == 2:
        order = order[1::2] + order[0::2]
    PASSES.append(np.array([radius(emit(order[:n], salt)) for n in NS]))
R = np.array(PASSES)
print(f"2. series   : 3 passes x {M} points, full precision")
for i, r in enumerate(R):
    print(f"   pass {chr(65+i)}  mean {r.mean():.9f}  span {np.ptp(r):.9f}")

# ---------------------------------------------------------------- 3. the null
amp, coh = coherence(R)
ncoh = np.zeros((NULL_TRIALS, len(coh)))
for i in range(NULL_TRIALS):
    fake = np.array([[radius(rng.integers(0, 256, REC * NREC, dtype=np.uint8).tobytes())
                      for _ in NS] for _ in range(3)])
    ncoh[i] = coherence(fake)[1]
nmu, nsd = ncoh.mean(0), ncoh.std(0)
print(f"3. null     : {NULL_TRIALS} matched triples, per-harmonic mean and sd")
print(f"   chance coherence at k=1 : {nmu[1]:.4f} +/- {nsd[1]:.4f}")

# ---------------------------------------------------------------- emit
L = [
    "BILATHDR|schema=ASOLARIA-BILATERAL-V1|seat=ACER-CLAUDE-FABLE5|pid=8467a937cba309f7"
    f"|date=2026-07-27|purpose=row_by_row_diff_not_verdict_diff|json=0",
    f"CONTRACT|passes=3|ladder_points={M}|n_from=2|n_to={NREC}|record_bytes={REC}"
    f"|records={NREC}|null_trials={NULL_TRIALS}|coherence=abs_mean_unit_phasors"
    f"|passes_differ_by=ordering_only|json=0",
    f"MANIFEST|count={len(man)}|sha256={man_sha}|order=by_size_desc|json=0",
]
for i, n, s, h in man:
    L.append(f"A|i={i}|k={n}|bytes={s}|sha256={h}|json=0")
for pi in range(3):
    L.append(f"PASS|id={chr(65+pi)}|salt=PASS-{chr(65+pi)}|order="
             f"{'as_manifest' if pi==0 else ('reversed' if pi==1 else 'interleaved')}"
             f"|mean={R[pi].mean():.12f}|span={np.ptp(R[pi]):.12f}|json=0")
    for j, n in enumerate(NS):
        L.append(f"R|pass={chr(65+pi)}|n={n}|radius={R[pi][j]:.12f}|json=0")
for k in range(1, len(coh)):
    z = (coh[k] - nmu[k]) / (nsd[k] + 1e-12)
    L.append(f"H|k={k}|period={M/k:.6f}|amp={amp[k]:.9f}|coh={coh[k]:.9f}"
             f"|null_mu={nmu[k]:.9f}|null_sd={nsd[k]:.9f}|z={z:.4f}"
             f"|wave={1 if z>3 else 0}|json=0")
L.append("GATE|comparable_iff=manifest_sha256_matches|else=different_ladders_not_disagreement"
         "|json=0")
body = "\n".join(L) + "\n"
L.append(f"BILATFTR|receipt={hashlib.sha256(body.encode()).hexdigest()[:32]}|rows={len(L)+1}"
         f"|hot_path=1|json=0")
open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
d = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
open(OUT + ".sha256", "w", newline="\n").write(f"{d}  {os.path.basename(OUT)}\n")
print(f"\n  -> {OUT}")
print(f"     {os.path.getsize(OUT):,} B   rows {len(L)}   sha256 {d[:32]}")
print(f"\n  Liris: run this on your office, then compare_bilateral.py ACER yours")
