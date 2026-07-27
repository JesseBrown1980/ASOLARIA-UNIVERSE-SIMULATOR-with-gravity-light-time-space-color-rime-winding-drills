#!/usr/bin/env python3
"""compare_gguf.py — read any GGUFs and compare their waves.

WHY THIS EXISTS
    Two seats cannot compare by describing their objects to each other. They compare by
    each writing a GGUF and both running the SAME reader over both files. This is that
    reader. It has no dependency on who made the file or what made it -- it parses the
    container, pulls the tensors, and measures.

WHAT IT MEASURES, in order
    1. the container      tensors, dims, type, and every asolaria.* key present
    2. the mass           total, mean, occupancy -- is there anything in it at all
    3. THE WAVE           2D FFT of each plane, magnitude, radially averaged into a
                          1D power spectrum. This is the comparable object: two seats
                          with different bodies still produce spectra on the same axis,
                          so the spectra can be subtracted. Wave comparison is the whole
                          point -- it is what makes the collision measurable rather than
                          asserted.
    4. pairwise           pearson + cosine on raw tensors of equal shape, and separately
                          on the radial spectra, which compare even when shapes differ.

USAGE
    python compare_gguf.py                      # every gguf in ../gguf
    python compare_gguf.py a.gguf b.gguf ...    # explicit set

WHEN LIRIS SENDS HERS
    drop her .gguf into gguf/ and re-run with no arguments. Nothing here is keyed to my
    filenames; her file is parsed by the same code path as mine and lands in the same
    tables. If her tensor shapes differ from mine the raw comparison is skipped and the
    spectral comparison still runs, which is the reason the spectrum is the primary
    instrument and not the raw bytes.
"""
import glob
import os
import struct
import sys

import numpy as np

# ---------------------------------------------------------------- GGUF reader
GGUF_MAGIC = 0x46554747
(T_U8, T_I8, T_U16, T_I16, T_U32, T_I32, T_F32, T_BOOL, T_STR, T_ARR,
 T_U64, T_I64, T_F64) = range(13)
_SCALAR = {T_U8: "<B", T_I8: "<b", T_U16: "<H", T_I16: "<h", T_U32: "<I",
           T_I32: "<i", T_F32: "<f", T_BOOL: "<?", T_U64: "<Q", T_I64: "<q",
           T_F64: "<d"}
# ggml type -> (numpy dtype, bytes per element). Only the unquantised ones; a quantised
# tensor is reported as opaque rather than silently mis-read.
_GGML = {0: (np.float32, 4), 1: (np.float16, 2), 24: (np.int8, 1), 25: (np.int16, 2),
         26: (np.int32, 4), 27: (np.int64, 8), 28: (np.float64, 8), 30: (np.uint8, 1)}


class Reader:
    def __init__(self, b):
        self.b, self.o = b, 0

    def raw(self, n):
        v = self.b[self.o:self.o + n]
        self.o += n
        return v

    def sc(self, t):
        f = _SCALAR[t]
        n = struct.calcsize(f)
        return struct.unpack(f, self.raw(n))[0]

    def st(self):
        n = struct.unpack("<Q", self.raw(8))[0]
        return self.raw(n).decode("utf-8", "replace")

    def val(self, t):
        if t == T_STR:
            return self.st()
        if t == T_ARR:
            et = struct.unpack("<I", self.raw(4))[0]
            n = struct.unpack("<Q", self.raw(8))[0]
            return [self.val(et) for _ in range(n)]
        return self.sc(t)


def read_gguf(path):
    b = open(path, "rb").read()
    r = Reader(b)
    magic, ver, n_ten, n_kv = struct.unpack("<IIQQ", r.raw(24))
    if magic != GGUF_MAGIC:
        raise ValueError(f"{path}: not a GGUF (magic {magic:#x})")
    kv = {}
    for _ in range(n_kv):
        k = r.st()
        t = struct.unpack("<I", r.raw(4))[0]
        kv[k] = r.val(t)
    tens = []
    for _ in range(n_ten):
        name = r.st()
        nd = struct.unpack("<I", r.raw(4))[0]
        dims = [struct.unpack("<Q", r.raw(8))[0] for _ in range(nd)]
        gt = struct.unpack("<I", r.raw(4))[0]
        off = struct.unpack("<Q", r.raw(8))[0]
        tens.append((name, dims, gt, off))
    align = int(kv.get("general.alignment", 32))
    base = r.o + ((-r.o) % align)
    out = {}
    for name, dims, gt, off in tens:
        if gt not in _GGML:
            out[name] = ("opaque", dims, gt, None)
            continue
        dt, esz = _GGML[gt]
        n = 1
        for d in dims:
            n *= int(d)
        arr = np.frombuffer(b, dtype=dt, count=n, offset=base + off)
        # GGUF stores dims fastest-first; reverse for C order
        out[name] = ("ok", dims, gt, arr.reshape(tuple(int(x) for x in reversed(dims))))
    return {"path": path, "version": ver, "kv": kv, "tensors": out, "bytes": len(b)}


# ---------------------------------------------------------------- the wave
def radial_spectrum(a, nbins=32):
    """2D FFT -> magnitude -> radial average. The comparable wave.

    A plane from one seat and a plane from another seat have different content but the
    same frequency axis, so these two curves subtract. That is what makes it a
    measurement rather than a description.
    """
    a = np.asarray(a, dtype=np.float64)
    if a.ndim == 1:
        n = int(np.sqrt(a.size))
        if n * n == a.size:
            a = a.reshape(n, n)
        else:                                   # 1D body: use the 1D spectrum directly
            F = np.abs(np.fft.rfft(a - a.mean()))
            idx = np.linspace(0, len(F) - 1, nbins).astype(int)
            v = F[idx]
            return v / (v.sum() or 1.0)
    if a.ndim > 2:
        a = a.reshape(a.shape[0], -1)
    F = np.abs(np.fft.fftshift(np.fft.fft2(a - a.mean())))
    h, w = F.shape
    cy, cx = h / 2.0, w / 2.0
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    rmax = rr.max()
    bins = np.minimum((rr / rmax * nbins).astype(int), nbins - 1)
    out = np.zeros(nbins)
    cnt = np.zeros(nbins)
    np.add.at(out, bins.ravel(), F.ravel())
    np.add.at(cnt, bins.ravel(), 1.0)
    out = out / np.maximum(cnt, 1.0)
    s = out.sum()
    return out / (s if s else 1.0)


def pear(a, b):
    a, b = np.asarray(a, float).ravel(), np.asarray(b, float).ravel()
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def cosine(a, b):
    a, b = np.asarray(a, float).ravel(), np.asarray(b, float).ravel()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na and nb else float("nan")


# ---------------------------------------------------------------- main
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
files = args if args else sorted(glob.glob(os.path.join(HERE, "..", "gguf", "**", "*.gguf"),
                                           recursive=True))
if not files:
    print("no gguf found")
    sys.exit(1)

docs = []
print("=" * 78)
print("THE CONTAINERS")
print("=" * 78)
for f in files:
    try:
        d = read_gguf(f)
    except Exception as e:
        print(f"  {os.path.basename(f):<34} UNREADABLE: {type(e).__name__}: {e}")
        continue
    docs.append(d)
    name = d["kv"].get("general.name", "?")
    arch = d["kv"].get("general.architecture", "?")
    print(f"\n  {os.path.basename(f)}")
    print(f"    v{d['version']}  {d['bytes']:,} B   arch={arch}   name={name}")
    for k, v in sorted(d["kv"].items()):
        if k.startswith("asolaria."):
            s = str(v)
            print(f"      {k:<40} {s[:70]}")
    for tn, (st, dims, gt, arr) in d["tensors"].items():
        if st != "ok":
            print(f"      tensor {tn:<28} dims={dims} ggml={gt} OPAQUE")
            continue
        a = arr.astype(np.float64)
        nz = int((a != 0).sum())
        print(f"      tensor {tn:<28} dims={list(map(int,dims))} "
              f"mass={a.sum():,.0f} mean={a.mean():.3f} "
              f"occ={100.0*nz/a.size:.1f}%")

# ---- the waves
# A FILE-LEVEL wave is computed for every document by concatenating its tensors. That is
# the object two seats compare, because it exists no matter how differently the two
# bodies are shaped inside. Per-tensor waves are also reported, but only for documents
# small enough to read; a 146-tensor corpus is summarised by its file wave.
TENSOR_DETAIL_MAX = 8
print("\n" + "=" * 78)
print("THE WAVE — radial power spectrum, 32 bins")
print("=" * 78)
file_waves, tensor_waves, raw = {}, {}, {}
for d in docs:
    base = os.path.basename(d["path"])
    oks = [(tn, arr) for tn, (st, _, _, arr) in d["tensors"].items() if st == "ok"]
    if not oks:
        continue
    file_waves[base] = radial_spectrum(
        np.concatenate([a.astype(np.float64).ravel() for _, a in oks]))
    for tn, arr in oks:
        tensor_waves[f"{base}::{tn}"] = radial_spectrum(arr)
        raw[f"{base}::{tn}"] = arr

print("\n  FILE WAVES — the cross-seat instrument")
for base, w in file_waves.items():
    head = " ".join(f"{x:.4f}" for x in w[:8])
    print(f"    {base:<38} peak@{int(np.argmax(w)):<3} "
          f"centroid={float((np.arange(len(w))*w).sum()):6.3f}  [{head} ...]")

for d in docs:
    base = os.path.basename(d["path"])
    mine = [k for k in tensor_waves if k.startswith(base + "::")]
    if len(mine) > TENSOR_DETAIL_MAX:
        print(f"\n  {base}: {len(mine)} tensors — per-tensor detail suppressed, "
              f"file wave above stands for it")
        continue
    if not mine:
        continue
    print(f"\n  {base} — per tensor")
    for k in mine:
        w = tensor_waves[k]
        head = " ".join(f"{x:.4f}" for x in w[:8])
        print(f"    {k.split('::')[1]:<30} peak@{int(np.argmax(w)):<3} "
              f"centroid={float((np.arange(len(w))*w).sum()):6.3f}  [{head} ...]")

# ---- pairwise, file level first
print("\n" + "=" * 78)
print("PAIRWISE — file level (this is the one that compares across seats)")
print("=" * 78)
fk = list(file_waves)
print(f"  {'pair':<62} {'spec r':>8} {'spec cos':>9}")
for i in range(len(fk)):
    for j in range(i + 1, len(fk)):
        a, b = fk[i], fk[j]
        sa = a.replace("ASOLARIA-", "").replace(".gguf", "")
        sb = b.replace("ASOLARIA-", "").replace(".gguf", "")
        print(f"  {sa+' vs '+sb:<62} "
              f"{pear(file_waves[a], file_waves[b]):8.5f} "
              f"{cosine(file_waves[a], file_waves[b]):9.5f}")

small = [k for k in tensor_waves
         if sum(1 for x in tensor_waves if x.startswith(k.split('::')[0] + '::'))
         <= TENSOR_DETAIL_MAX]
if len(small) > 1:
    print("\n" + "=" * 78)
    print("PAIRWISE — tensor level, small documents only; raw where shapes match")
    print("=" * 78)
    print(f"  {'pair':<62} {'spec r':>8} {'raw r':>9}")
    for i in range(len(small)):
        for j in range(i + 1, len(small)):
            a, b = small[i], small[j]
            rr = pear(raw[a], raw[b]) if raw[a].shape == raw[b].shape else float("nan")
            rs = f"{rr:9.5f}" if rr == rr else "  shape-differ"
            sa = f"{a.split('::')[0].replace('ASOLARIA-SELF-','').replace('.gguf','')}::{a.split('::')[1]}"
            sb = f"{b.split('::')[0].replace('ASOLARIA-SELF-','').replace('.gguf','')}::{b.split('::')[1]}"
            print(f"  {sa+' vs '+sb:<62} {pear(tensor_waves[a], tensor_waves[b]):8.5f} {rs}")

print("\n" + "=" * 78)
print("READING IT")
print("=" * 78)
print("  spec r near 1.000  -> same wave shape: the two objects are the same kind of")
print("                        thing measured from different places.")
print("  spec r low         -> genuinely different structure, not noise, because the")
print("                        radial spectrum has already averaged the noise out.")
print("  raw r blank        -> shapes differ, so only the wave is comparable. That is")
print("                        the expected case across two seats and is not a failure.")
