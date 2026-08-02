#!/usr/bin/env python3
"""Three-star kernel network reference implementation.

A deterministic 81-node message-passing network seeded by the existing
asolaria-tribit 3,078-byte receipt. It is an experiment, not a claim of
below-Shannon compression or a trained neural model.

Topology:
    3 stars (RED/GREEN/BLUE)
  x 3 OIL families (OIL/ANTI_OIL/ANTI_ANTI_OIL)
  x 3 tenses (WAS/IS/WILL)
  x 3 signs (NEGATIVE/CENTRE/POSITIVE)
  = 81 nodes around one shared centre-energy scalar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

RECORDS = 38
RECORD = 81
SEED_LEN = RECORDS * RECORD
TIER_MASK = 0x7F
AXIS = 3
NODES = 81

STARS = ("RED", "GREEN", "BLUE")
FAMILIES = ("OIL", "ANTI_OIL", "ANTI_ANTI_OIL")
TENSES = ("WAS", "IS", "WILL")
SIGNS = ("NEGATIVE", "CENTRE", "POSITIVE")

TEST_VECTORS = {
    b"": "a91acae4ae2d1418db50095702096f5c81761fc422637972942f325465b2e730",
    b"a": "2b467e4cca4db694b9e172ea2346da8c873f501227dd9cb8c3b8234622d40530",
    b"abc": "907d5cec4b56072e7612b7834b377d8d4e2c9d0c4d44b2aac2b1ce379112f2c6",
    b"the quick brown fox": "839a079a56bb7a6db742180520cbe36fb9afafe6d4ad1e4e4f9313588c0807a6",
    b"ASOLARIA": "27d7eddf5c216f289ee6416ca29285e67b5f3424650fe84cbaecb0c7c2202c87",
}


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def make_seed(data: bytes) -> bytes:
    """Independent implementation of the Rust/WASM fixed-size receipt."""
    out = bytearray(SEED_LEN)
    root = sha256(data)
    pid = root[:16]
    chunk = 0 if not data else math.ceil(len(data) / RECORDS)

    for i in range(RECORDS):
        pid = sha256(pid + b"|" + i.to_bytes(4, "big"))[:16]
        lo = min(i * chunk, len(data))
        hi = min(lo + chunk, len(data))
        dig = sha256(pid + data[lo:hi])
        witness = sha256(pid + dig)[:7]
        seg = hi - lo
        o = i * RECORD
        out[o : o + 16] = pid
        out[o + 16 : o + 48] = dig
        out[o + 48 : o + 53] = seg.to_bytes(5, "big")
        out[o + 53 : o + 57] = i.to_bytes(4, "big")
        out[o + 57 : o + 73] = root[16:32]
        out[o + 73 : o + 80] = witness
        out[o + 80] = (min(len(data), 127) ^ i) & TIER_MASK
    return bytes(out)


def idx(star: int, family: int, tense: int, sign: int) -> int:
    return ((star * AXIS + family) * AXIS + tense) * AXIS + sign


def coords(i: int) -> tuple[int, int, int, int]:
    i %= NODES
    sign = i % AXIS
    i //= AXIS
    tense = i % AXIS
    i //= AXIS
    family = i % AXIS
    star = i // AXIS
    return star, family, tense, sign


def rotate(i: int, axis: int, delta: int) -> int:
    c = list(coords(i))
    c[axis] = (c[axis] + delta) % AXIS
    return idx(*c)


def derive_activations(seed: bytes) -> list[int]:
    if len(seed) != SEED_LEN:
        raise ValueError(f"seed must be {SEED_LEN} bytes, got {len(seed)}")
    return [sum(seed[r * RECORD + i] - 128 for r in range(RECORDS)) for i in range(NODES)]


def rounded_div(n: int, d: int) -> int:
    if d <= 0:
        raise ValueError("denominator must be positive")
    if n >= 0:
        return (n + d // 2) // d
    return -((-n + d // 2) // d)


def centre_of(values: Sequence[int]) -> int:
    return rounded_div(sum(values), len(values))


def variance(values: Sequence[int]) -> float:
    if not values:
        return 0.0
    m = sum(values) / len(values)
    return sum((x - m) ** 2 for x in values) / len(values)


def l1_deviation(values: Sequence[int]) -> int:
    c = centre_of(values)
    return sum(abs(x - c) for x in values)


def max_deviation(values: Sequence[int]) -> int:
    c = centre_of(values)
    return max((abs(x - c) for x in values), default=0)


@dataclass(frozen=True)
class StepReceipt:
    step: int
    centre: int
    variance: float
    l1: int
    max_abs: int


def call_weights(key: bytes, node: int, axis: int) -> tuple[int, int, int]:
    """Three weights: identity, anti (R), anti-anti (R²), each 1..3."""
    base = (node * 17 + axis * 97) % len(key)
    return tuple(1 + key[(base + j * 37) % len(key)] % 3 for j in range(3))  # type: ignore[return-value]


def calm_step(values: Sequence[int], key: bytes, pump: int) -> list[int]:
    """One bounded integer message-passing step.

    Every axis uses identity, R and R². The shared centre is stored once. ``pump`` is a
    mixing fraction 0..27, not created energy. Weighted averaging makes the update
    non-amplifying in L-infinity.
    """
    if len(values) != NODES:
        raise ValueError("expected 81 node activations")
    if not key:
        raise ValueError("key must be non-empty")
    pump = max(0, min(27, int(pump)))
    centre = centre_of(values)
    dev = [v - centre for v in values]
    out = [0] * NODES

    for i in range(NODES):
        total = 0
        den = 0
        for axis in range(4):
            w0, w1, w2 = call_weights(key, i, axis)
            total += w0 * dev[i]
            total += w1 * dev[rotate(i, axis, 1)]
            total += w2 * dev[rotate(i, axis, 2)]
            den += w0 + w1 + w2
        mixed = rounded_div(total, den)
        next_dev = rounded_div((27 - pump) * dev[i] + pump * mixed, 27)
        out[i] = centre + next_dev

    # Correct integer-rounding drift with a uniform translation. Separations are unchanged.
    drift = centre - centre_of(out)
    if drift:
        out = [v + drift for v in out]
    return out


def run_network(key: bytes, steps: int, pump: int) -> tuple[bytes, list[int], list[StepReceipt]]:
    seed = make_seed(key)
    values = derive_activations(seed)
    receipts = []
    for s in range(steps + 1):
        receipts.append(
            StepReceipt(
                step=s,
                centre=centre_of(values),
                variance=variance(values),
                l1=l1_deviation(values),
                max_abs=max_deviation(values),
            )
        )
        if s < steps:
            nxt = calm_step(values, key, pump)
            if max_deviation(nxt) > max_deviation(values):
                raise AssertionError("calm step amplified max deviation")
            if centre_of(nxt) != centre_of(values):
                raise AssertionError("shared centre moved")
            values = nxt
    return seed, values, receipts


def fingerprint(values: Sequence[int]) -> str:
    b = b"".join(int(v).to_bytes(4, "big", signed=True) for v in values)
    return hashlib.sha256(b).hexdigest()


def run_self_tests() -> None:
    for inp, expected in TEST_VECTORS.items():
        got = hashlib.sha256(make_seed(inp)).hexdigest()
        assert got == expected, (inp, got, expected)

    assert len({idx(*coords(i)) for i in range(NODES)}) == NODES
    for i in range(NODES):
        for axis in range(4):
            assert rotate(rotate(rotate(i, axis, 1), axis, 1), axis, 1) == i
            assert rotate(i, axis, 1) != rotate(i, axis, 2)

    kernels = {coords(i)[:2] for i in range(NODES)}
    assert len(kernels) == 9
    assert all(sum(1 for i in range(NODES) if coords(i)[:2] == k) == 9 for k in kernels)

    key = bytes(range(256)) * 12 + bytes(range(102))
    assert len(key) == 3174
    seed, values, rec = run_network(key, steps=27, pump=9)
    seed2, values2, rec2 = run_network(key, steps=27, pump=9)
    assert seed == seed2 and values == values2 and rec == rec2
    assert rec[-1].max_abs <= rec[0].max_abs
    assert rec[-1].centre == rec[0].centre


def null_summary(actual_ratio: float, length: int, steps: int, pump: int, n: int) -> dict[str, float | int]:
    rng = random.Random(0xA501A)
    ratios: list[float] = []
    for _ in range(n):
        key = bytes(rng.randrange(256) for _ in range(length))
        _, _, rec = run_network(key, steps=steps, pump=pump)
        ratios.append(rec[-1].variance / rec[0].variance if rec[0].variance else 0.0)
    mean = sum(ratios) / len(ratios)
    sd = math.sqrt(sum((x - mean) ** 2 for x in ratios) / max(1, len(ratios) - 1))
    z = (actual_ratio - mean) / sd if sd else 0.0
    return {"n": n, "mean": mean, "sd": sd, "z": z}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("key", type=Path)
    p.add_argument("--steps", type=int, default=27)
    p.add_argument("--pump", type=int, default=9, help="mixing strength 0..27")
    p.add_argument("--nulls", type=int, default=0)
    p.add_argument("--json", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()

    if args.self_test:
        run_self_tests()

    key = args.key.read_bytes()
    seed, values, rec = run_network(key, max(0, args.steps), args.pump)
    initial, final = rec[0], rec[-1]
    ratio = final.variance / initial.variance if initial.variance else 0.0
    result: dict[str, object] = {
        "schema": "ASOLARIA-THREE-STAR-KERNEL-NET-V1",
        "key_path": str(args.key),
        "key_bytes": len(key),
        "key_sha256": hashlib.sha256(key).hexdigest(),
        "seed_bytes": len(seed),
        "seed_sha256": hashlib.sha256(seed).hexdigest(),
        "nodes": NODES,
        "top_level_kernels": 9,
        "subnodes_per_kernel": 9,
        "directed_callings": NODES * 4 * 2,
        "steps": max(0, args.steps),
        "pump": max(0, min(27, args.pump)),
        "centre_initial": initial.centre,
        "centre_final": final.centre,
        "variance_initial": initial.variance,
        "variance_final": final.variance,
        "variance_ratio": ratio,
        "max_abs_initial": initial.max_abs,
        "max_abs_final": final.max_abs,
        "calm_non_amplifying": final.max_abs <= initial.max_abs,
        "network_sha256": fingerprint(values),
        "classification": "MEASURED_COMPUTATIONAL_NETWORK",
        "boundary": "deterministic key-conditioned message passing; not a trained model, negative entropy, or physical gravity",
    }
    if args.nulls:
        result["matched_random_null"] = null_summary(ratio, len(key), max(0, args.steps), args.pump, args.nulls)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for k, v in result.items():
            print(f"{k}={v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
