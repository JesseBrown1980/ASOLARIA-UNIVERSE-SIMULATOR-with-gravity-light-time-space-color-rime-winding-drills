# gguf/ — the comparable objects

Two seats cannot compare by describing their objects to each other. Each writes a GGUF,
both run the **same** reader over **both** files, and the numbers decide.

That reader is `measurements/compare_gguf.py`. It parses the container itself — no
dependency on who wrote the file — and it is the only thing either side needs to run.

```
python measurements/compare_gguf.py            # every gguf under gguf/, recursive
python measurements/compare_gguf.py a.gguf b.gguf
```

## What is here now (ACER / FABLE5 seat)

| file | what it is |
|---|---|
| `ASOLARIA-CONSTELLATION.gguf` | the earlier seed projection, τ=2 GC. **Carries neither the signed −1/3 nor the translucent 2/3.** Kept for provenance, not as the current object. |
| `ASOLARIA-SELF-64-XY.gguf` | look 1 — down BLUE/energy, the red-green plane, 64×64 |
| `ASOLARIA-SELF-64-YZ.gguf` | look 2 — down RED/time, the green-blue plane, 64×64 |
| `ASOLARIA-SELF-64-ZX.gguf` | look 3 — down GREEN/colour, the blue-red plane, 64×64 |
| `ASOLARIA-SELF-64CUBE.gguf` | the whole 64×64×64, **with `solid_third` and `translucent_two_thirds` as separate tensors** |

The cube is not a chosen resolution. A byte triple is a colour; `256 >> 2 = 64` per axis,
so 64×64×64 is the body at its own natural grain and a voxel coordinate **is** a colour.

Measured on this seat: largest centre `(31,26,28)` = `#7C6870`, mass 32,846 of 1,167,320.
Looking out of it the first colour is **RED**, and it stays red and 100% solid for five
shells before green, then blue, then the 2/3 takes over at r=11.

## `liris/` — drop yours here

Anything in `gguf/liris/` is picked up by the same recursive glob with no code change.
Filenames are not keyed to anything; shapes do not have to match mine.

**If the shapes differ the raw comparison is skipped and the wave comparison still runs.**
That is why the radial power spectrum is the primary instrument: two different bodies
still produce spectra on the same frequency axis, so they subtract.

## The result that makes this worth running

On this seat's own three rotations:

| | raw | wave (radial FFT) |
|---|---|---|
| XY vs YZ | 0.846 | **0.996** |
| XY vs ZX | 0.520 | **0.927** |
| YZ vs ZX | 0.532 | **0.923** |

In raw space two of the three rotations look like different objects. **In the wave they
do not** — all three agree at 0.92–1.00. The disagreement was *where the mass sits*, not
*what it is*. So a cross-seat comparison run in the raw domain would report a difference
that is not real, and the wave is the honest instrument.

And the sharpest one, within the cube:

```
solid_third vs translucent_two_thirds     raw r = -0.011      wave r = 0.948
```

The 1/3 and the 2/3 are **spatially orthogonal** — they share essentially nothing — while
having nearly the **same wave shape**. Same kind of structure, disjoint places. That is
the pair a second seat should try hardest to reproduce or refute.
