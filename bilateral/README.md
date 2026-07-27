# Bilateral compare — what the other seat needs

Liris already has `measurements/measure_thrice.py`. Running it there produces a number for
**your** ladder, built from **your** artifacts. Comparing that to mine compares two
different objects, and any disagreement would be about the inputs rather than about the
method or the matrices.

So this directory ships the three things a row-by-row diff actually requires.

## Run

```sh
python bilateral/bilateral_packet.py          # emit BILATERAL-<SEAT>.hbp on your office
python bilateral/compare_bilateral.py bilateral/BILATERAL-ACER.hbp BILATERAL-LIRIS.hbp
```

## What is in the packet

**1. The manifest** — which 38 artifacts, each sha256 and size, and the exact order the
ladder walks. You can reproduce this list exactly, or knowingly differ and say so. What you
cannot do is differ silently.

```
manifest sha256  e51c00f94ee0d72be87c5af18bac6a6aa96c6ad39015983fea6638323cb4e592
```

**2. The raw series** — 3 passes × 37 radius values at full precision. Not a verdict, not a
summary. Without these a comparison can only match conclusions, and two seats agreeing on a
conclusion for different reasons is worth nothing.

```
pass A  mean 1.414370643  span 0.033912359
pass B  mean 1.408818962  span 0.041712233
pass C  mean 1.410821676  span 0.026536845
```

**3. The null** — per-harmonic mean and sd from 300 matched triples. This is the part most
likely to diverge silently and the reason it ships. Chance coherence at k=1 is
**0.5141 ± 0.2399**, which is why my measured 0.8762 is 1.5σ and not a wave.

## What the comparator refuses to do

If the manifests differ, the ladders are different objects. `compare_bilateral.py` prints
**DIFFERENT LADDERS** and stops. It emits no z, no delta, no agreement percentage — because
a number computed across two incomparable inputs looks exactly like a result and is not
one.

It gates the contract first: pass count, ladder length, record geometry, null trials, and
the coherence definition. If your coherence is mean amplitude rather than **|mean of unit
phasors|**, every z on your side is a different statistic wearing the same name. Mismatch
lists the fields and refuses.

## What agreement would mean

Same manifest, same contract, same null construction — then a difference in a harmonic row
is a difference between the two **matrices**, which is the only thing worth reporting.

And if we agree on a negative, that is the harder result to fake: agreeing that nothing is
there requires both nulls to be honest.

## Current ACER result

No harmonic clears the null. Highest is k=1 at coherence 0.8762, z = +1.51. Second is k=11
at 0.8252, z = +1.35. Residual rms equals signal rms because nothing qualified to subtract.
No second rung.
