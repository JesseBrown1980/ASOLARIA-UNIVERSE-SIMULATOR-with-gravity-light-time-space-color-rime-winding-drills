#!/usr/bin/env python3
"""Emit the exact 3,078-byte asolaria-tribit seed for a complete file.

This is the Liris Python parity adapter for
``crates/asolaria-tribit/src/lib.rs::seed``.  The output is only the canonical
38 x 81-byte seed.  It deliberately carries no HBP, HBI, SH, QR, or source
payload: without the separately banked source it is an address/receipt.

Usage:
    py -3.14 measurements/seed_file.py <input> <output>
    py -3.14 measurements/seed_file.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import BinaryIO, Iterable
from urllib.parse import quote


IMPLEMENTATION = "python_liris_parity"
RECORDS = 38
RECORD_BYTES = 81
SEED_BYTES = RECORDS * RECORD_BYTES
TIER_MASK = 0x7F
IO_BLOCK_BYTES = 1 << 20
U40_MASK = (1 << 40) - 1


# Every literal SHA-256 expectation currently present in the Rust crate.
NIST_SHA256_VECTORS: tuple[tuple[bytes, str], ...] = (
    (
        b"",
        "e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855",
    ),
    (
        b"abc",
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad",
    ),
    (
        b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
        "248d6a61d20638b8e5c026930c3e6039"
        "a33ce45964ff2167f6ecedd419db06c1",
    ),
)

RUST_SEED_VECTORS: tuple[tuple[str, bytes, str], ...] = (
    (
        "empty",
        b"",
        "a91acae4ae2d1418db50095702096f5c"
        "81761fc422637972942f325465b2e730",
    ),
    (
        "a",
        b"a",
        "2b467e4cca4db694b9e172ea2346da8c"
        "873f501227dd9cb8c3b8234622d40530",
    ),
    (
        "abc",
        b"abc",
        "907d5cec4b56072e7612b7834b377d8d"
        "4e2c9d0c4d44b2aac2b1ce379112f2c6",
    ),
    (
        "quick_brown_fox",
        b"the quick brown fox",
        "839a079a56bb7a6db742180520cbe36fb"
        "9afafe6d4ad1e4e4f9313588c0807a6",
    ),
    (
        "ASOLARIA",
        b"ASOLARIA",
        "27d7eddf5c216f289ee6416ca29285e6"
        "7b5f3424650fe84cbaecb0c7c2202c87",
    ),
)


class SeedFileError(RuntimeError):
    """Fail-closed input, parity, or output verification failure."""


def _tuple_value(value: object) -> str:
    """Percent-encode tuple delimiters and control characters."""

    return quote(str(value), safe="/:._-")


def _emit(kind: str, fields: Iterable[tuple[str, object]], *, stream: object = sys.stdout) -> None:
    body = "|".join(f"{key}={_tuple_value(value)}" for key, value in fields)
    print(f"{kind}|{body}|json=0", file=stream, flush=True)


def _sha256(*parts: bytes) -> bytes:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part)
    return digest.digest()


def _next_pid(pid: bytes, index: int) -> bytes:
    return _sha256(pid, b"|", index.to_bytes(4, "big"))[:16]


def _record(
    *,
    pid: bytes,
    digest: bytes,
    segment_bytes: int,
    index: int,
    root: bytes,
    total_bytes: int,
) -> bytes:
    witness = _sha256(pid, digest)[:7]
    tier = (min(total_bytes, 127) ^ index) & TIER_MASK
    record = b"".join(
        (
            pid,
            digest,
            (segment_bytes & U40_MASK).to_bytes(5, "big"),
            index.to_bytes(4, "big"),
            root[16:32],
            witness,
            bytes((tier,)),
        )
    )
    if len(record) != RECORD_BYTES:
        raise SeedFileError(f"internal record length {len(record)} != {RECORD_BYTES}")
    return record


def seed_bytes(data: bytes) -> bytes:
    """Reference in-memory implementation of the Rust ``seed(&[u8])`` bytes."""

    root = _sha256(data)
    pid = root[:16]
    total = len(data)
    chunk = 0 if total == 0 else (total + RECORDS - 1) // RECORDS
    records: list[bytes] = []

    for index in range(RECORDS):
        pid = _next_pid(pid, index)
        lo = min(index * chunk, total)
        hi = min(lo + chunk, total)
        digest = _sha256(pid, data[lo:hi])
        records.append(
            _record(
                pid=pid,
                digest=digest,
                segment_bytes=hi - lo,
                index=index,
                root=root,
                total_bytes=total,
            )
        )

    seed = b"".join(records)
    if len(seed) != SEED_BYTES:
        raise SeedFileError(f"internal seed length {len(seed)} != {SEED_BYTES}")
    return seed


def _identity(info: os.stat_result) -> tuple[int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _require_regular(info: os.stat_result, role: str) -> None:
    if not stat.S_ISREG(info.st_mode):
        raise SeedFileError(f"{role} is not a regular file")


def _scan_complete(handle: BinaryIO) -> tuple[bytes, int]:
    digest = hashlib.sha256()
    total = 0
    while True:
        block = handle.read(IO_BLOCK_BYTES)
        if not block:
            break
        digest.update(block)
        total += len(block)
    return digest.digest(), total


def _update_exact(
    handle: BinaryIO,
    digest: object,
    mirror: object,
    expected: int,
) -> int:
    remaining = expected
    consumed = 0
    while remaining:
        block = handle.read(min(IO_BLOCK_BYTES, remaining))
        if not block:
            raise SeedFileError(
                f"input ended early after {consumed} of {expected} segment bytes"
            )
        digest.update(block)
        mirror.update(block)
        consumed += len(block)
        remaining -= len(block)
    return consumed


def seed_path(input_path: Path) -> tuple[bytes, int, str]:
    """Seed a regular file using two complete, mutually verified read passes."""

    resolved = input_path.resolve(strict=True)

    with resolved.open("rb", buffering=0) as source:
        before = os.fstat(source.fileno())
        _require_regular(before, "input")
        root, total = _scan_complete(source)
        after = os.fstat(source.fileno())

    if _identity(before) != _identity(after):
        raise SeedFileError("input metadata changed during first complete read")
    if total != before.st_size:
        raise SeedFileError(f"first read covered {total} bytes, stat reported {before.st_size}")

    chunk = 0 if total == 0 else (total + RECORDS - 1) // RECORDS
    pid = root[:16]
    records: list[bytes] = []
    reread_root = hashlib.sha256()
    reread_total = 0

    with resolved.open("rb", buffering=0) as source:
        reread_before = os.fstat(source.fileno())
        _require_regular(reread_before, "input")
        if _identity(reread_before) != _identity(after):
            raise SeedFileError("input was replaced or changed between complete reads")

        for index in range(RECORDS):
            pid = _next_pid(pid, index)
            lo = min(index * chunk, total)
            hi = min(lo + chunk, total)
            segment_bytes = hi - lo
            segment_digest = hashlib.sha256()
            segment_digest.update(pid)
            reread_total += _update_exact(
                source,
                segment_digest,
                reread_root,
                segment_bytes,
            )
            digest = segment_digest.digest()
            records.append(
                _record(
                    pid=pid,
                    digest=digest,
                    segment_bytes=segment_bytes,
                    index=index,
                    root=root,
                    total_bytes=total,
                )
            )

        if source.read(1):
            raise SeedFileError("input grew beyond the first complete read")
        reread_after = os.fstat(source.fileno())

    if _identity(reread_before) != _identity(reread_after):
        raise SeedFileError("input metadata changed during verification reread")
    if reread_total != total:
        raise SeedFileError(f"verification reread covered {reread_total} of {total} bytes")
    if reread_root.digest() != root:
        raise SeedFileError("input SHA-256 changed between complete reads")

    seed = b"".join(records)
    if len(seed) != SEED_BYTES:
        raise SeedFileError(f"internal seed length {len(seed)} != {SEED_BYTES}")
    return seed, total, root.hex()


def _read_seed_exact(path: Path) -> bytes:
    with path.open("rb", buffering=0) as handle:
        info = os.fstat(handle.fileno())
        _require_regular(info, "output")
        data = handle.read(SEED_BYTES + 1)
        if len(data) != SEED_BYTES:
            raise SeedFileError(f"output reread length {len(data)} != {SEED_BYTES}")
        if handle.read(1):
            raise SeedFileError("output reread found trailing bytes")
        return data


def write_seed_verified(output_path: Path, seed: bytes, input_path: Path) -> Path:
    """Atomically replace the destination after temporary and final reread checks."""

    if len(seed) != SEED_BYTES:
        raise SeedFileError(f"refusing to write noncanonical seed length {len(seed)}")

    raw_output = output_path.expanduser().absolute()
    if raw_output.is_symlink():
        raise SeedFileError("refusing a symbolic-link output")
    parent = raw_output.parent.resolve(strict=True)
    if not parent.is_dir():
        raise SeedFileError("output parent is not a directory")
    output = (parent / raw_output.name).resolve(strict=False)
    if output.exists():
        if not output.is_file():
            raise SeedFileError("output exists and is not a regular file")
        if os.path.samefile(input_path.resolve(strict=True), output):
            raise SeedFileError("input and output resolve to the same file")

    fd, temporary_name = tempfile.mkstemp(
        dir=parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    installed = False
    try:
        with os.fdopen(fd, "wb", buffering=0) as handle:
            written = handle.write(seed)
            if written != SEED_BYTES:
                raise SeedFileError(f"temporary write covered {written} of {SEED_BYTES} bytes")
            handle.flush()
            os.fsync(handle.fileno())

        if _read_seed_exact(temporary) != seed:
            raise SeedFileError("temporary output reread did not match generated seed")

        os.replace(temporary, output)
        installed = True

        if _read_seed_exact(output) != seed:
            raise SeedFileError("installed output reread did not match generated seed")
        return output
    finally:
        if not installed:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _cells_reached(seed: bytes) -> int:
    seen: set[int] = set()
    for offset in range(0, len(seed) - 2, 3):
        a, b, c = (min(value // 86, 2) for value in seed[offset : offset + 3])
        seen.add(a * 9 + b * 3 + c)
    return len(seen)


def _verify_chain(seed: bytes) -> bool:
    if len(seed) < SEED_BYTES:
        return False
    for index in range(1, RECORDS):
        previous_pid = seed[(index - 1) * RECORD_BYTES : (index - 1) * RECORD_BYTES + 16]
        expected = _next_pid(previous_pid, index)
        actual = seed[index * RECORD_BYTES : index * RECORD_BYTES + 16]
        if actual != expected:
            return False
    return True


def self_test() -> int:
    for payload, expected in NIST_SHA256_VECTORS:
        actual = _sha256(payload).hex()
        if actual != expected:
            raise SeedFileError(
                f"NIST SHA-256 vector mismatch: expected {expected}, got {actual}"
            )

    for name, payload, expected in RUST_SEED_VECTORS:
        seed = seed_bytes(payload)
        actual = hashlib.sha256(seed).hexdigest()
        if actual != expected:
            raise SeedFileError(
                f"Rust seed vector {name} mismatch: expected {expected}, got {actual}"
            )
        if len(seed) != SEED_BYTES or _cells_reached(seed) != 27 or not _verify_chain(seed):
            raise SeedFileError(f"Rust seed vector {name} failed structural checks")
        _emit(
            "SEEDSELFTESTVECTOR",
            (
                ("ok", 1),
                ("implementation", IMPLEMENTATION),
                ("vector", name),
                ("input_bytes", len(payload)),
                ("complete_input", 1),
                ("seed_bytes", len(seed)),
                ("seed_sha256", actual),
                ("expected_seed_sha256", expected),
                ("cells", 27),
                ("chain_verify", "PASS"),
            ),
        )

    sizes = (0, 1, 81, 3078, 100_000, (1 << 20) + 1)
    largest_seed_sha256 = ""
    with tempfile.TemporaryDirectory(prefix="seed-file-self-test-") as directory:
        base = Path(directory)
        for size in sizes:
            pattern = bytes(range(256))
            payload = (pattern * ((size + len(pattern) - 1) // len(pattern)))[:size]
            source = base / f"input-{size}.bin"
            source.write_bytes(payload)
            streamed, observed_bytes, observed_sha256 = seed_path(source)
            expected = seed_bytes(payload)
            if observed_bytes != size or observed_sha256 != hashlib.sha256(payload).hexdigest():
                raise SeedFileError(f"complete-input accounting failed at {size} bytes")
            if streamed != expected:
                raise SeedFileError(f"streaming parity failed at {size} bytes")
            largest_seed_sha256 = hashlib.sha256(streamed).hexdigest()

        output = base / "verified.seed"
        installed = write_seed_verified(output, streamed, source)
        if _read_seed_exact(installed) != streamed:
            raise SeedFileError("final self-test output reread failed")

    _emit(
        "SEEDSELFTEST",
        (
            ("ok", 1),
            ("implementation", IMPLEMENTATION),
            ("nist_vectors", len(NIST_SHA256_VECTORS)),
            ("rust_seed_vectors", len(RUST_SEED_VECTORS)),
            ("file_sizes", ",".join(str(size) for size in sizes)),
            ("over_1mib", 1),
            ("complete_input", 1),
            ("seed_bytes", SEED_BYTES),
            ("seed_sha256", largest_seed_sha256),
            ("reread_verify", "PASS"),
        ),
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Emit the exact 3,078-byte asolaria-tribit seed for a complete regular file."
        )
    )
    parser.add_argument("--self-test", action="store_true", help="run embedded Rust-vector parity tests")
    parser.add_argument("input", nargs="?", type=Path, help="complete input artifact")
    parser.add_argument("output", nargs="?", type=Path, help="3,078-byte seed output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.self_test:
        if args.input is not None or args.output is not None:
            raise SeedFileError("--self-test does not accept input or output paths")
        return self_test()
    if args.input is None or args.output is None:
        raise SeedFileError("expected: seed_file.py <input> <output>")

    input_path = args.input.expanduser()
    seed, input_bytes, input_sha256 = seed_path(input_path)
    output = write_seed_verified(args.output, seed, input_path)
    seed_sha256 = hashlib.sha256(seed).hexdigest()
    _emit(
        "SEEDFILE",
        (
            ("ok", 1),
            ("implementation", IMPLEMENTATION),
            ("input_bytes", input_bytes),
            ("input_sha256", input_sha256),
            ("complete_input", 1),
            ("seed_bytes", len(seed)),
            ("seed_sha256", seed_sha256),
            ("records", RECORDS),
            ("record_bytes", RECORD_BYTES),
            ("reread_verify", "PASS"),
        ),
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, SeedFileError, ValueError) as error:
        _emit(
            "SEEDFILE",
            (
                ("ok", 0),
                ("implementation", IMPLEMENTATION),
                ("complete_input", 0),
                ("error", type(error).__name__),
                ("detail", str(error)),
            ),
            stream=sys.stderr,
        )
        raise SystemExit(1)
