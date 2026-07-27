#!/usr/bin/env python3
"""compare_bilateral.py — diff two bilateral packets row by row, and refuse when it cannot.

    python compare_bilateral.py BILATERAL-ACER.hbp BILATERAL-LIRIS.hbp

WHAT THIS REFUSES TO DO
If the two packets were built from different manifests, the ladders are different objects
and their harmonic rows are not comparable. This prints "DIFFERENT LADDERS" and stops. It
does NOT emit a z, a delta, or an agreement percentage, because a number computed across
two different objects looks exactly like a result and is not one. That failure mode -- a
comparison that produces a plausible figure from incomparable inputs -- is the specific
thing this file exists to prevent.

It also checks the CONTRACT before the data: pass count, ladder length, record geometry,
null trial count, and the coherence definition. If the other seat computed coherence as
mean amplitude rather than |mean of unit phasors|, every z on their side is a different
statistic wearing the same name, and any disagreement between us would be an artifact of
the two harnesses. Mismatches are listed and the diff refuses.

WHAT AGREEMENT MEANS WHEN IT PASSES
Same manifest, same contract, same null construction. Then a difference in a harmonic row
is a difference between the two matrices, which is the only thing worth reporting.
"""
import math
import os
import sys


def parse(path):
    d = {"A": {}, "R": {}, "H": {}, "PASS": {}, "hdr": {}, "contract": {}, "manifest": {}}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        tag, *rest = line.split("|")
        kv = {}
        for p in rest:
            if "=" in p:
                k, v = p.split("=", 1)
                kv[k] = v
        if tag == "BILATHDR":
            d["hdr"] = kv
        elif tag == "CONTRACT":
            d["contract"] = kv
        elif tag == "MANIFEST":
            d["manifest"] = kv
        elif tag == "A":
            d["A"][int(kv["i"])] = (kv["k"], int(kv["bytes"]), kv["sha256"])
        elif tag == "PASS":
            d["PASS"][kv["id"]] = kv
        elif tag == "R":
            d["R"].setdefault(kv["pass"], {})[int(kv["n"])] = float(kv["radius"])
        elif tag == "H":
            d["H"][int(kv["k"])] = kv
    return d


if len(sys.argv) != 3:
    print(__doc__)
    raise SystemExit(2)
a, b = (parse(p) for p in sys.argv[1:3])
na, nb = (a["hdr"].get("seat", "?"), b["hdr"].get("seat", "?"))
print(f"=== {na}   vs   {nb} ===\n")

# ---------------------------------------------------------------- contract gate
print("--- contract ---")
FIELDS = ("passes", "ladder_points", "n_from", "n_to", "record_bytes", "records",
          "null_trials", "coherence", "passes_differ_by")
bad = []
for f in FIELDS:
    va, vb = a["contract"].get(f), b["contract"].get(f)
    ok = va == vb
    if not ok:
        bad.append(f)
    print(f"  {f:<18}{str(va):<28}{str(vb):<28}{'ok' if ok else 'MISMATCH'}")
if bad:
    print(f"\n  CONTRACT MISMATCH on {len(bad)}: {', '.join(bad)}")
    print("  REFUSING TO DIFF. These are different statistics wearing the same names.")
    raise SystemExit(1)

# ---------------------------------------------------------------- manifest gate
print("\n--- manifest ---")
sa, sb = a["manifest"].get("sha256"), b["manifest"].get("sha256")
print(f"  {na} {sa}")
print(f"  {nb} {sb}")
if sa != sb:
    ka = {v[0] for v in a["A"].values()}
    kb = {v[0] for v in b["A"].values()}
    print(f"\n  DIFFERENT LADDERS. shared {len(ka & kb)}, only-{na} {len(ka - kb)}, "
          f"only-{nb} {len(kb - ka)}")
    for k in sorted(ka - kb)[:6]:
        print(f"    only {na}: {k}")
    for k in sorted(kb - ka)[:6]:
        print(f"    only {nb}: {k}")
    print("\n  The harmonic rows are NOT comparable: the two packets measure different")
    print("  objects. This is not a disagreement between the seats, and no z, delta or")
    print("  agreement percentage will be printed, because such a number would look")
    print("  exactly like a result. Align the manifests, or report two ladders.")
    raise SystemExit(1)
print("  identical -> the rows are comparable")

# ---------------------------------------------------------------- null gate
print("\n--- null construction ---")
worst = 0.0
for k in sorted(set(a["H"]) & set(b["H"])):
    mu_a, sd_a = float(a["H"][k]["null_mu"]), float(a["H"][k]["null_sd"])
    mu_b, sd_b = float(b["H"][k]["null_mu"]), float(b["H"][k]["null_sd"])
    worst = max(worst, abs(mu_a - mu_b) / max(sd_a, 1e-12))
print(f"  largest null-mean divergence, in sd : {worst:.3f}")
if worst > 1.0:
    print("  WARNING: the two nulls differ by more than 1 sd. Every z is affected and a")
    print("  row-level disagreement below that scale is the harness, not the matrices.")

# ---------------------------------------------------------------- the rows
print(f"\n--- harmonic rows ---")
print(f"{'k':>4}{'period':>9}{f'coh {na[:6]}':>13}{f'coh {nb[:6]}':>13}"
      f"{'delta':>9}{'z '+na[:6]:>11}{'z '+nb[:6]:>11}{'verdict':>10}")
dis = []
for k in sorted(set(a["H"]) & set(b["H"])):
    ca, cb = float(a["H"][k]["coh"]), float(b["H"][k]["coh"])
    za, zb = float(a["H"][k]["z"]), float(b["H"][k]["z"])
    wa, wb = a["H"][k]["wave"] == "1", b["H"][k]["wave"] == "1"
    v = "agree" if wa == wb else "DIFFER"
    if wa != wb:
        dis.append(k)
    print(f"{k:>4}{float(a['H'][k]['period']):>9.2f}{ca:>13.4f}{cb:>13.4f}"
          f"{cb-ca:>+9.4f}{za:>+11.2f}{zb:>+11.2f}{v:>10}")

print(f"\n--- verdict ---")
wa = sum(1 for k in a["H"] if a["H"][k]["wave"] == "1")
wb = sum(1 for k in b["H"] if b["H"][k]["wave"] == "1")
print(f"  harmonics above the null : {na} {wa}   {nb} {wb}")
if dis:
    print(f"  rows where the seats DISAGREE : {dis}")
    print("  same ladder, same null, same statistic -> this is a real difference")
    print("  between the two matrices and is the finding.")
else:
    print(f"  no row disagrees. Two seats, two matrices, same answer at every harmonic.")
    if wa == 0:
        print("  and the shared answer is a NEGATIVE, which is the harder one to fake:")
        print("  agreeing that nothing is there requires both nulls to be honest.")
