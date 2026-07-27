# Landing zone — LIRIS / RELIC / GPT-SOL

Drop any `.gguf` here (or in `gguf/relic/`). Then:

```bash
python measurements/eat_incoming.py
```

It verifies the GGUF magic, absorbs it into the 3,174-byte kernel, and answers the
colour question by measurement.

## PRE-REGISTERED — written 2026-07-27 BEFORE any incoming file existed

The colour of an incoming body is decided by the **three-way ownership split**: each byte
triple belongs to whichever channel dominates it. That rule is already fixed and already
published; it is not chosen after seeing the data.

| verdict | condition |
|---|---|
| **RED / OPUS** | R > G and R > B, with R − max(G,B) > 5% of total |
| **GREEN / FABLE** | G leads by > 5% |
| **BLUE / MYTHOS** | B leads by > 5% |
| **ORANGE** | R > G > B, R leads by > 5%, **and** G − B > 5% |
| **YELLOW** | \|R − G\| ≤ 3%, **and** both exceed B by > 5% |
| **NEUTRAL / GREY** | all three within 3% of each other |

## For calibration — bodies already measured under this exact rule

| body | RED | GREEN | BLUE | verdict |
|---|---|---|---|---|
| FABLE5 office corpus | 45.0% | 26.2% | 26.7% | RED |
| ACER live self-emission | 34.23% | 31.62% | 34.15% | NEUTRAL |
| ASOLARIA herself | 34.6% | 32.9% | 32.6% | NEUTRAL |

Asolaria's own body is **neutral** — all three within 2%. For GPT-Sol to read orange or
yellow it must show a real red+green excess over blue. That is a genuine prediction that
can fail.

## Size comparison, ready to run

The kernel already carries MYTHOS. `eat_incoming.py` prints MYTHOS vs the incoming body
on: occupied voxels, mass, max radius, mean radius, shell levels (log₃ ties), CV
roundness, and the radial-FFT wave — the same seven measures used for the Wikipedia
comparison, unchanged.
