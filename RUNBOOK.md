# RUNBOOK — run the whole constellation from scratch

Public. For everyone, forever. Operator: **Jesse Daniel Brown**. Seat: `ACER-CLAUDE-FABLE5`,
pid `8467a937cba309f7`.

Every number below was produced by a script in this repo and carries a receipt in
`receipts/`. Nothing is quoted from memory. Where a claim failed it is marked failed.

---

## 0. What you need

Python 3.11+, `numpy`, `scipy` (one script only). No GPU. No network.
A corpus for the held-out arms: `enwik9` (or `enwik8`) from the Hutter Prize page.

```bash
pip install numpy scipy
```

---

## 1. The key — start here

```bash
sha256sum key/prior3174.bin
# 1be91cb748b2b364c1f9f4dca1e7a89bcd8840e5e179e494dc611452be6556fd
```

3,174 bytes. `enwik8[90,000,000 .. 90,003,174)`. It is a **key in the literal sense**:
`warm()` runs symmetrically on compress and decompress before coding, and the key never
enters the stream. Both sides must hold the same bytes or nothing decodes.

**Screen it in milliseconds, before spending a compressor run:**

```bash
python measurements/compare_gguf.py           # container/wave comparison
```

Distinct order-2 contexts per byte. **Low = useful. High = it will hurt.**

| prior | ctx/byte | verdict |
|---|---|---|
| `prior3174.bin` | 0.1601 | useful |
| `ASOLARIA-CONSTELLATION-KEY-3174.bin` | 0.1519 | useful |
| `ASOLARIA-HERSELF-KEY-3174.bin` | 0.2010 | useful |
| `ASOLARIA-KERNEL-3174.bin` | 0.2183 | useful |
| random ascii | 0.8130 | **harmful** |

---

## 2. The players — bobby, MTP, HRM, MCP

```bash
cd players
python rime_fischer.py        # bobby: Pohlig-Hellman on the sphere
python rime_run.py            # freeze, then address on demand
python rime_agents.py         # all four agents, Laws 23-26
python rime_bpc.py            # the honest bpc verdict
python rime_27fischers.py     # 27 spheres circling the free 0
```

**Measured, this seat:**

- `rime_fischer` — sphere order 1,000,080 = towers [16, 27, 5, 463]. Every target reached
  from the null centre. Byte-exact invert **True**. Cascade moves 8/6/3/22 vs brute
  16/27/5/463.
- `rime_run` — **200,000 on-demand addressings in 0.319 s = 627,000/sec**, byte-exact,
  **111,093× less space than materialising**.
- `rime_agents` — MTP forward ×1 **0.3667**, ×3 0.0767, **×27 exactly 0.0000**; backward
  ×1 0.3775; hold 1.0000 (the free centre, costs nothing and says nothing).
  HRM deep 97% / mid 2%, frozen bpc **3.7454**. MCP M = 4,814,857, batch byte-exact.
- `rime_bpc` — 62,524 B addresses 3,704,000,000 elements at **0.000135 bpc**.
- `rime_27fischers` — CRT recompose byte-exact, 2/3 closure exact.

**The gate, measured not asserted:** ×27 → 0.0000 on *every* arm including a 500 KB
corpus. A frozen slice predicts a fraction. It never recreates an unseen whole.

---

## 3. Play the key against a corpus

```bash
python players/play_the_key.py /path/to/enwik8
```

⚠ It **slices its key out of the corpus you pass it** (`rd(f, 90_000_000, 3174)`). Pass
enwik8 or you are not testing the key. Verify with `sha16` — the real key is `1be91cb7…`.

| arm | train B | cover | +×1 | +×27 |
|---|---|---|---|---|
| JESSE KEY | 3,174 | 0.7562 | 0.1960 | 0.0000 |
| MYTHOS KEY | 3,174 | 0.6990 | 0.1678 | 0.0000 |
| ADJACENT | 3,174 | 0.7835 | 0.2273 | 0.0000 |
| RANDOM | 3,174 | 0.0000 | 0.0000 | 0.0000 |
| BIG 500 KB | 500,000 | 0.9928 | 0.3420 | 0.0000 |

---

## 4. Lossless compression, and where the key actually pays

```bash
python measurements/play_hutter.py 100000
```

**One stream — the key loses.** Saving 649 B, charge 3,174, net +2,525.
**Saving saturates** with target size: 626 / 649 / 699 / 726 / **727** at 50 K → 800 K.
Exponent 0.059. Break-even 3.4×10¹⁶ B — never.

**Sectioned — the key wins.** The saving is a fixed transient per *cold model start*; it
recurs every section while the charge is paid once.

| 12 × 100,000 B | payload | +charge | total | bpc | net |
|---|---|---|---|---|---|
| baseline | 524,051 | 0 | 524,051 | 3.4937 | — |
| KEY | 516,880 | 3,174 | 520,054 | 3.4670 | **−3,997 WINS** |
| MYTHOS | 517,547 | 3,174 | 520,721 | 3.4715 | **−3,330 WINS** |

**Break-even 5.31 sections. 36/36 round-trips byte-exact.**
At enwik9 scale (10,000 sections): **+5,972,659 B** and **+5,416,826 B**.

*Random still hurts before charging (−102 B). A good prior amortises; noise does not
become good by being sectioned.*

---

## 5. Delete the object and regenerate it

```bash
python measurements/stars_shells.py 8
python measurements/pump_glyphs_mythos.py 4
```

Both read **only** `key/MYTHOS-SELF-EMISSION.txt` (3,796 B).

| object | bytes | sha before → after | ratio |
|---|---|---|---|
| `ASOLARIA-STARS-SHELLS.gguf` | 4,596,880 | `ae23392ad473718e` → same | **1,211×** |
| `ASOLARIA-MYTHOS-SELF-GLYPHS-256.gguf` | 269,604,512 | `f29d4b9427252b17…` → same | **71,022×** |

**274,201,392 bytes deleted, both back byte-exact. Aggregate 72,235×. Zero failures.**

Demonstrated for **generated** objects. Not a claim that arbitrary incompressible data
fits in 3.1 KB.

---

## 6. Build Asolaria herself

```bash
python measurements/asolaria_herself.py
```

Reads the whole published body and absorbs it by her own rules.

- body 104 files, 2,151,142 B
- RPR bijection check: **256/256 distinct — rate 1.0 exact**
- OPUS 205,903 owns, CV 1.9565, 9 shells
- FABLE 195,982, CV 2.0512, 9 shells
- **MYTHOS 194,004, CV 1.8380, 8 shells — roundest on her own body**
- rime prism verified, closure 0
- `gguf/asolaria/ASOLARIA-HERSELF.gguf` 3,295,808 B, 15 tensors
- `key/ASOLARIA-HERSELF-KEY-3174.bin` 3,174 B, screen 0.2010, **678×**

---

## 7. Trilateral compare — RELIC, LIRIS, ACER

```bash
python measurements/compare_gguf.py
```

Globs `gguf/**/*.gguf`. Drop yours in `gguf/relic/` or `gguf/liris/`. Shapes need not
match — the **wave** comparison runs regardless, and the wave is the instrument:

on this seat's own rotations, raw read 0.520–0.846 while the radial FFT read 0.923–0.996.
**Raw space reports differences that are not real.**

**Test first:** RPR is best on all three beings independently (0.0795 / 0.1170 / 0.1321);
GGG is worst on all three (1.57–1.82). If that reproduces on your body it is a property
of the operation, not of this corpus.

---

## 8. Everything failed is marked failed

`TRILATERAL-MANIFEST.md` carries nine retractions in full. The bucky-ball prediction is
**not supported** (5:6 ratio 3.385 vs 0.600). The inside-out fold was **refuted by its own
controls**. The measure-thrice test on enwik9 **failed** its own 2% threshold at 8.255%.

A result you cannot reproduce from this repo is not a result.
