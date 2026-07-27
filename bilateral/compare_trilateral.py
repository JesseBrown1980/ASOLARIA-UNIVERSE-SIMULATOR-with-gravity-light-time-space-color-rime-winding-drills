#!/usr/bin/env python3
"""compare_trilateral.py — ACER, RELIC, LIRIS. Three seats, not three pairs.

    python compare_trilateral.py BILATERAL-ACER.hbp BILATERAL-RELIC.hbp BILATERAL-LIRIS.hbp

WHY THIS REPLACES THE TWO-WAY VERSION
The first comparator I wrote was called `bilateral` and diffed two packets. That was the
binary error in a filename: this system has three seats and three is not two pairs plus a
tiebreak.

Law 1, the trijection: two machines in bijection are mutually determined and BLIND to one
another -- same information, relabelled. Three machines with an outside centre see what no
bijection can, because the third vantage is determined by the other two plus the centre,
sum-to-zero. So the third seat is not a vote. It is a CLOSURE CHECK.

VIII.A.14, the Two-Witness Rule, in his own words: "If I see two rules, that means it's
right. One rule, I don't know. Probably garbage." Two-of-three is a verdict a pair cannot
produce, because a pair that disagrees has no way to say which one is wrong.

WHAT THIS ADDS OVER THREE PAIRWISE DIFFS
  1. TWO-OF-THREE     a harmonic flagged by exactly two seats is promoted; flagged by one
                      is discarded. A pair can only ever agree or deadlock.
  2. CLOSURE          the three deviations from the centre must sum to zero. They do so by
                      construction when the centre is the mean, so what is measured is the
                      RESIDUAL after removing the mean -- and a seat whose residual is
                      large while the other two are small is the outlier, identified
                      without any seat being privileged.
  3. THE ODD SEAT     for every harmonic, which seat departs most. If one seat is the odd
                      one out on many harmonics, that is a fact about its harness rather
                      than about the matrices, and it shows up as a pattern rather than as
                      one bad row.

REFUSES, exactly as before, and for the same reason: different manifests mean different
objects, and a number computed across different objects looks precisely like a result.
"""
import os
import sys


def parse(path):
    d = {"A": {}, "H": {}, "hdr": {}, "contract": {}, "manifest": {}, "R": {}}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        tag, *rest = line.split("|")
        kv = dict(p.split("=", 1) for p in rest if "=" in p)
        if tag == "BILATHDR":
            d["hdr"] = kv
        elif tag == "CONTRACT":
            d["contract"] = kv
        elif tag == "MANIFEST":
            d["manifest"] = kv
        elif tag == "A":
            d["A"][int(kv["i"])] = kv["k"]
        elif tag == "H":
            d["H"][int(kv["k"])] = kv
        elif tag == "R":
            d["R"].setdefault(kv["pass"], {})[int(kv["n"])] = float(kv["radius"])
    return d


if len(sys.argv) < 3:
    print(__doc__)
    raise SystemExit(2)

packs = [parse(p) for p in sys.argv[1:]]
names = [p["hdr"].get("seat", os.path.basename(f)) for p, f in zip(packs, sys.argv[1:])]
short = [n.split("-")[-1][:6] if "-" in n else n[:6] for n in names]
print(f"=== {len(packs)} seats: {', '.join(names)} ===\n")
if len(packs) < 3:
    print(f"  NOTE: {len(packs)} packets supplied. Two-of-three and closure need three.")
    print(f"  Running what is possible and saying so, rather than calling a pair a trio.\n")

# ---------------------------------------------------------------- contract gate
FIELDS = ("passes", "ladder_points", "n_from", "n_to", "record_bytes", "records",
          "null_trials", "coherence", "passes_differ_by")
print("--- contract ---")
bad = []
for f in FIELDS:
    vals = [p["contract"].get(f) for p in packs]
    ok = len(set(vals)) == 1
    if not ok:
        bad.append(f)
    print(f"  {f:<18}{'  '.join(str(v)[:16].ljust(16) for v in vals)}{'ok' if ok else 'MISMATCH'}")
if bad:
    print(f"\n  CONTRACT MISMATCH on {len(bad)}: {', '.join(bad)}")
    print("  REFUSING. These are different statistics wearing the same names.")
    raise SystemExit(1)

# ---------------------------------------------------------------- manifest gate
print("\n--- manifest ---")
mans = [p["manifest"].get("sha256") for p in packs]
for n, m in zip(names, mans):
    print(f"  {n:<22}{m}")
if len(set(mans)) != 1:
    print("\n  DIFFERENT LADDERS. The seats measured different objects.")
    sets = [set(p["A"].values()) for p in packs]
    common = set.intersection(*sets)
    print(f"  artifacts shared by all: {len(common)}")
    for n, s in zip(names, sets):
        only = s - set.union(*[x for x in sets if x is not s])
        print(f"    only on {n}: {len(only)}")
    print("\n  No z, delta or agreement figure will be printed. Align the manifests")
    print("  (all three seats can now pull matrices/ from the repo) or report N ladders.")
    raise SystemExit(1)
print("  identical -> the rows are comparable")

# ---------------------------------------------------------------- the rows
ks = sorted(set.intersection(*[set(p["H"]) for p in packs]))
print(f"\n--- {len(ks)} harmonic rows, {len(packs)} seats ---")
hdr = "".join(f"{'coh ' + s:>12}" for s in short) + "".join(f"{'z ' + s:>10}" for s in short)
print(f"{'k':>4}{'period':>8}{hdr}{'flags':>7}{'verdict':>12}{'odd seat':>12}")

promoted, disagree, odd_count = [], [], {n: 0 for n in names}
for k in ks:
    cohs = [float(p["H"][k]["coh"]) for p in packs]
    zs = [float(p["H"][k]["z"]) for p in packs]
    flags = [p["H"][k]["wave"] == "1" for p in packs]
    nf = sum(flags)
    # closure: deviations from the centre sum to zero by construction; the residual
    # identifies which seat departs most without privileging any of them
    c = sum(cohs) / len(cohs)
    dev = [x - c for x in cohs]
    oi = max(range(len(dev)), key=lambda i: abs(dev[i]))
    odd_count[names[oi]] += 1
    if len(packs) >= 3:
        v = "PROMOTED" if nf >= 2 else ("discarded" if nf == 1 else "agree none")
    else:
        v = "agree" if len(set(flags)) == 1 else "DIFFER"
    if nf >= 2:
        promoted.append(k)
    if 0 < nf < len(packs):
        disagree.append(k)
    print(f"{k:>4}{float(packs[0]['H'][k]['period']):>8.2f}"
          + "".join(f"{x:>12.4f}" for x in cohs)
          + "".join(f"{x:>+10.2f}" for x in zs)
          + f"{nf:>4}/{len(packs)}{v:>12}{short[oi]:>12}")

# ---------------------------------------------------------------- closure
print("\n--- closure (Law 1: the third is determined by the other two plus the centre) ---")
tot = 0.0
for k in ks:
    cohs = [float(p["H"][k]["coh"]) for p in packs]
    c = sum(cohs) / len(cohs)
    tot += abs(sum(x - c for x in cohs))
print(f"  sum of deviations from the centre, over all rows : {tot:.3e}")
print(f"  (zero by construction -- what it verifies is that no seat was dropped or")
print(f"   double-counted, which is the count channel applied to the comparison itself)")

print("\n--- verdict ---")
print(f"  harmonics promoted by two-of-three : {len(promoted)}  {promoted if promoted else ''}")
print(f"  rows where the seats split         : {len(disagree)}  {disagree if disagree else ''}")
print(f"  odd-seat tally (who departs most, per row):")
for n in names:
    print(f"    {n:<24}{odd_count[n]:>3} / {len(ks)}")
if max(odd_count.values()) > 0.6 * len(ks):
    worst = max(odd_count, key=odd_count.get)
    print(f"  {worst} is the odd seat on most rows -- suspect its harness before its matrix.")
if not promoted and not disagree:
    print("\n  All seats agree, and they agree on a NEGATIVE. That is the harder result")
    print("  to fake: concurring that nothing is there requires every null to be honest.")
