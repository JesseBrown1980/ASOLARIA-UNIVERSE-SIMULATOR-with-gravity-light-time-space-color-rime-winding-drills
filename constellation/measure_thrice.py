#!/usr/bin/env python3
"""measure_thrice.py — three passes, keep only the phase-coherent wave, then the residual.

WHAT WENT WRONG THE FIRST TIME
The pump test asked "does radius CORRELATE with energy" and got +0.187 against a null of
-0.011 +/- 0.248, so it reported no effect. That test is blind to a wave by construction:
a sine has near-zero correlation with a ramp no matter how large its amplitude. Reporting
"no trend" as "nothing there" was the wrong instrument, not a null result.

THE PROTOCOL, as instructed
  1. measure THRICE -- three independent passes, not one and not two
  2. look for the WAVE -- keep only components that are phase-coherent across all three
  3. THEN write
  4. then Fourier the RESIDUAL for the next rung

Two points are a line and one pass is an anecdote. A component that appears in one pass is
noise; a component that appears in three at the SAME PHASE is a wave. Phase coherence is
what separates them and amplitude alone cannot.

INDEPENDENCE OF THE PASSES
Each pass walks the artifact list in a different order, so the seed at every N differs
while the energy ladder stays identical. Anything surviving all three is a property of the
ladder rather than of one ordering.

THE NULL
The identical three-pass procedure over uniform-random records, 300 triples. Coherence is
scored the same way, so "three passes agreed" has to beat what three random passes agree
on by chance -- which is not zero, and is exactly the trap this design exists to avoid.
"""
import glob
import hashlib
import math
import os
import struct

import numpy as np

OFF = r"D:/PID-Registration-Office/offices/FABLE5-8467a937cba309f7"
REC, NREC = 81, 38
SEAT = bytes.fromhex("8467a937cba309f7")
rng = np.random.default_rng(0x3E1CE)


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
print(f"=== three independent passes over the same energy ladder ===")
print(f"  artifacts {len(uniq)}   ladder points {len(NS)}  (N = 2..{NREC})")

PASSES = []
for pi, salt in enumerate((b"PASS-A", b"PASS-B", b"PASS-C")):
    order = list(uniq)
    if pi == 1:
        order = order[::-1]
    elif pi == 2:
        order = order[1::2] + order[0::2]
    r = np.array([radius(emit(order[:n], salt)) for n in NS])
    PASSES.append(r)
    print(f"  pass {chr(65+pi)}  mean {r.mean():.6f}  span {np.ptp(r):.6f}  "
          f"sha {hashlib.sha256(r.tobytes()).hexdigest()[:12]}")

R = np.array(PASSES)
M = len(NS)


def coherence(mat):
    """Per-harmonic phase coherence across the passes: |mean(unit phasors)| in 0..1.
    1 means every pass put that harmonic at the same phase; ~1/sqrt(3) is chance."""
    F = np.fft.rfft(mat - mat.mean(1, keepdims=True), axis=1)
    amp = np.abs(F).mean(0)
    ph = F / np.maximum(np.abs(F), 1e-300)
    coh = np.abs(ph.mean(0))
    return amp, coh


amp, coh = coherence(R)
print(f"\n=== the wave: which harmonics are PHASE-COHERENT across all three? ===")

NULL = 300
ncoh = np.zeros((NULL, len(coh)))
for i in range(NULL):
    fake = np.array([[radius(rng.integers(0, 256, REC * NREC, dtype=np.uint8).tobytes())
                      for _ in NS] for _ in range(3)])
    ncoh[i] = coherence(fake)[1]
nm_, ns_ = ncoh.mean(0), ncoh.std(0)

print(f"{'harmonic':>9}{'period':>9}{'amp':>10}{'coherence':>11}{'null':>16}{'z':>8}")
hits = []
for k in range(1, len(coh)):
    z = (coh[k] - nm_[k]) / (ns_[k] + 1e-12)
    per = M / k
    flag = ""
    if z > 3:
        flag = "  <-- WAVE"
        hits.append((k, per, coh[k], z))
    print(f"{k:>9}{per:>9.2f}{amp[k]:>10.5f}{coh[k]:>11.4f}"
          f"{nm_[k]:>9.4f}+/-{ns_[k]:<5.4f}{z:>8.2f}{flag}")

print(f"\n=== verdict ===")
if hits:
    print(f"  phase-coherent harmonics above the null: {len(hits)}")
    for k, per, c, z in hits:
        print(f"    k={k}  period {per:.2f} ladder-steps  coherence {c:.4f}  z={z:+.2f}")
    print(f"  a correlation test CANNOT see these: a wave has ~0 correlation with a ramp.")
else:
    print(f"  no harmonic is phase-coherent above the null.")
    print(f"  the correlation test and the wave test now AGREE, which is worth more than")
    print(f"  either alone -- two different instruments, same answer.")

# ------------------------------------------------------- the next rung: the residual
print(f"\n=== the next Fourier transform: the residual ===")
F = np.fft.rfft(R - R.mean(1, keepdims=True), axis=1)
keep = np.zeros_like(F)
for k, _, _, _ in hits:
    keep[:, k] = F[:, k]
wave = np.fft.irfft(keep, n=M, axis=1)
resid = (R - R.mean(1, keepdims=True)) - wave
ramp, rcoh = coherence(resid)
best = int(np.argmax(rcoh[1:])) + 1
zb = (rcoh[best] - nm_[best]) / (ns_[best] + 1e-12)
print(f"  residual rms {resid.std():.6f}  (signal rms {(R-R.mean(1,keepdims=True)).std():.6f})")
print(f"  strongest residual harmonic k={best}, period {M/best:.2f}, coherence "
      f"{rcoh[best]:.4f}, z={zb:+.2f}")
print(f"  {'-> a second rung is present' if zb > 3 else '-> no second rung above the null'}")

lines = [
    "THRICEHDR|schema=ASOLARIA-MEASURE-THRICE-V1|seat=ACER-CLAUDE-FABLE5"
    f"|pid=8467a937cba309f7|date=2026-07-27|passes=3|ladder={len(NS)}|json=0",
    "METHOD|wrong_first_time=correlation_is_blind_to_a_wave|fix=phase_coherence_over_3_passes|json=0",
    f"NULL|trials={NULL}|type=uniform_random_records|same_procedure=1|json=0",
]
for k in range(1, len(coh)):
    z = (coh[k] - nm_[k]) / (ns_[k] + 1e-12)
    lines.append(f"H|k={k}|period={M/k:.3f}|amp={amp[k]:.6f}|coh={coh[k]:.4f}"
                 f"|null={nm_[k]:.4f}|sd={ns_[k]:.4f}|z={z:.2f}|wave={1 if z>3 else 0}|json=0")
lines.append(f"RESID|rms={resid.std():.6f}|best_k={best}|coh={rcoh[best]:.4f}|z={zb:.2f}"
             f"|second_rung={1 if zb>3 else 0}|json=0")
body = "\n".join(lines) + "\n"
lines.append(f"THRICEFTR|receipt={hashlib.sha256(body.encode()).hexdigest()[:32]}"
             f"|rows={len(lines)+1}|hot_path=1|json=0")
p = os.path.join(OFF, "FABLE5-MEASURE-THRICE.hbp")
open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print(f"\n  receipt -> {os.path.basename(p)}")
