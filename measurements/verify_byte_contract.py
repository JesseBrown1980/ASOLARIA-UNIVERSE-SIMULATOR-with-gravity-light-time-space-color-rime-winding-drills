#!/usr/bin/env python3
"""Verify the repository's byte-exact publication contract.

The verifier is read-only unless ``--receipt`` is supplied.  It deliberately
hashes files as byte streams: large GGUF payloads are never loaded into memory.
Output is HBP tuple text (``json=0``), suitable for the hot Asolaria lane.

Checks:
  * LF-only publication surfaces: .gitattributes, *.hbp, *.sha256, *.md
  * every SHA-256 sidecar and its target
  * missing and dangling sidecars for GGUF/HBI/HBP artifacts
  * index Git blob bytes versus raw worktree bytes
  * hydrated Git-LFS payload SHA-256 and size versus its pointer
  * byte counts for every GGUF and HBI
  * one deterministic inventory root over every worktree file

``--skip-git`` keeps the filesystem, sidecar, binary and inventory gates usable
from WSL or a copied tree that has no usable Git metadata.  In that mode the
Git gate is explicitly SKIPPED, never reported as a clean zero.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Iterator, NamedTuple


SCHEMA = "ASOLARIA-BYTE-CONTRACT-V1"
HASH_CHUNK = 8 * 1024 * 1024
LF_NAMES = {".gitattributes"}
LF_SUFFIXES = {".hbp", ".sha256", ".md"}
SIDECAR_SUFFIXES = {".gguf", ".hbi", ".hbp"}
BINARY_COUNT_SUFFIXES = {".gguf", ".hbi"}
SIDECAR_RE = re.compile(
    r"^([0-9a-fA-F]{64})(?:[ \t]+[*]?(.+?))?[ \t]*$"
)
LFS_OID_RE = re.compile(r"^oid sha256:([0-9a-f]{64})$", re.MULTILINE)
LFS_SIZE_RE = re.compile(r"^size ([0-9]+)$", re.MULTILINE)
LFS_VERSION = "version https://git-lfs.github.com/spec/v1"


def quoted(value: object) -> str:
    """Percent-escape tuple delimiters without changing ordinary paths."""

    text = str(value)
    return (
        text.replace("%", "%25")
        .replace("|", "%7C")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def row(record_type: str, **fields: object) -> str:
    parts = [record_type]
    parts.extend(f"{key}={quoted(value)}" for key, value in fields.items())
    parts.append("json=0")
    return "|".join(parts)


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def inside(root: Path, path: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def iter_files(root: Path, excluded: set[Path]) -> Iterator[Path]:
    """Yield regular files without following directory symlinks or .git."""

    excluded_resolved = {p.resolve(strict=False) for p in excluded}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        base = Path(dirpath)
        for name in sorted(filenames):
            path = base / name
            if name == ".git" or path.resolve(strict=False) in excluded_resolved:
                continue
            if path.is_file():
                yield path


class DigestCache:
    """Streaming SHA-256 cache keyed by resolved path, size and mtime."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, int, int], str] = {}

    def sha256(self, path: Path) -> str:
        stat = path.stat()
        key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        digest = hashlib.sha256()
        with path.open("rb", buffering=0) as handle:
            while True:
                block = handle.read(HASH_CHUNK)
                if not block:
                    break
                digest.update(block)
        value = digest.hexdigest()
        self._cache[key] = value
        return value


def stream_lf_state(path: Path) -> tuple[int, int, int]:
    """Return (CR byte count, LF byte count, final-byte-is-LF)."""

    cr_count = 0
    lf_count = 0
    last = b""
    with path.open("rb", buffering=0) as handle:
        while True:
            block = handle.read(HASH_CHUNK)
            if not block:
                break
            cr_count += block.count(b"\r")
            lf_count += block.count(b"\n")
            last = block[-1:]
    return cr_count, lf_count, int(last == b"\n")


class GitEntry(NamedTuple):
    mode: str
    oid: str
    stage: int
    path: str


def run_git(
    root: Path, args: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git_entries(root: Path) -> list[GitEntry]:
    proc = run_git(root, ["ls-files", "-s", "-z"])
    result: list[GitEntry] = []
    for record in proc.stdout.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode_b, oid_b, stage_b = meta.split(b" ", 2)
        result.append(
            GitEntry(
                mode_b.decode("ascii"),
                oid_b.decode("ascii"),
                int(stage_b),
                raw_path.decode("utf-8", "surrogateescape"),
            )
        )
    return result


def git_blob_prefix(root: Path, oid: str, maximum: int = 1024) -> bytes | None:
    size_proc = run_git(root, ["cat-file", "-s", oid], check=False)
    if size_proc.returncode != 0:
        return None
    try:
        size = int(size_proc.stdout.strip())
    except ValueError:
        return None
    if size > maximum:
        return b""
    blob_proc = run_git(root, ["cat-file", "blob", oid], check=False)
    return blob_proc.stdout if blob_proc.returncode == 0 else None


def parse_lfs_pointer(blob: bytes) -> tuple[str, int] | None:
    try:
        text = blob.decode("ascii").replace("\r\n", "\n")
    except UnicodeDecodeError:
        return None
    if not text.startswith(LFS_VERSION + "\n"):
        return None
    oid_match = LFS_OID_RE.search(text)
    size_match = LFS_SIZE_RE.search(text)
    if oid_match is None or size_match is None:
        return None
    return oid_match.group(1), int(size_match.group(1))


def raw_worktree_blob_oid(root: Path, git_path: str) -> tuple[str | None, str]:
    proc = run_git(
        root, ["hash-object", "--no-filters", "--", git_path], check=False
    )
    if proc.returncode != 0:
        return None, proc.stderr.decode("utf-8", "replace").strip()
    return proc.stdout.decode("ascii", "replace").strip(), ""


def resolve_sidecar_target(
    root: Path, sidecar: Path, token: str | None
) -> Path:
    if token is None or not token.strip():
        return sidecar.with_suffix("")
    token_path = Path(token.strip())
    if token_path.is_absolute():
        return token_path
    local = sidecar.parent / token_path
    if local.exists():
        return local
    repo_relative = root / token_path
    if repo_relative.exists():
        return repo_relative
    return local


def inventory_root(
    root: Path, files: Iterable[Path], digests: DigestCache
) -> tuple[str, int, int]:
    """Hash sorted path/size/content-hash records into one inventory root."""

    root_hash = hashlib.sha256()
    count = 0
    total_bytes = 0
    for path in sorted(files, key=lambda p: rel(root, p).encode("utf-8")):
        relative = rel(root, path)
        size = path.stat().st_size
        digest = digests.sha256(path)
        relative_bytes = relative.encode("utf-8", "surrogateescape")
        root_hash.update(str(len(relative_bytes)).encode("ascii"))
        root_hash.update(b":")
        root_hash.update(relative_bytes)
        root_hash.update(b"\0")
        root_hash.update(str(size).encode("ascii"))
        root_hash.update(b"\0")
        root_hash.update(digest.encode("ascii"))
        root_hash.update(b"\n")
        count += 1
        total_bytes += size
    return root_hash.hexdigest(), count, total_bytes


def receipt_bytes(rows: list[str]) -> bytes:
    return ("\n".join(rows) + "\n").encode("utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="worktree root (default: current directory)",
    )
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="skip Git/index/LFS checks; filesystem gates still run",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when any required gate fails",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="write the LF HBP output here and seal it with .sha256",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    requested_root = args.root.resolve()
    output_rows: list[str] = []
    errors = 0
    warnings = 0

    if not requested_root.is_dir():
        print(
            row(
                "BYTECONTRACTFATAL",
                status="FAIL",
                reason="root_not_directory",
                root=requested_root,
            )
        )
        return 2

    root = requested_root
    git_available = not args.skip_git
    if git_available:
        top = run_git(root, ["rev-parse", "--show-toplevel"], check=False)
        if top.returncode != 0:
            output_rows.append(
                row(
                    "GITGATE",
                    status="FAIL",
                    reason="not_a_git_worktree",
                    detail=top.stderr.decode("utf-8", "replace").strip(),
                )
            )
            errors += 1
            git_available = False
        else:
            candidate = Path(
                top.stdout.decode("utf-8", "surrogateescape").strip()
            ).resolve()
            if candidate != root:
                root = candidate

    excluded: set[Path] = set()
    receipt_path: Path | None = None
    sidecar_path: Path | None = None
    if args.receipt is not None:
        receipt_path = (
            args.receipt
            if args.receipt.is_absolute()
            else root / args.receipt
        ).resolve()
        sidecar_path = Path(str(receipt_path) + ".sha256")
        if not inside(root, receipt_path) or not inside(root, sidecar_path):
            print(
                row(
                    "BYTECONTRACTFATAL",
                    status="FAIL",
                    reason="receipt_outside_root",
                    receipt=receipt_path,
                )
            )
            return 2
        excluded.update({receipt_path, sidecar_path})

    files = list(iter_files(root, excluded))
    digest_cache = DigestCache()
    output_rows.insert(
        0,
        row(
            "BYTECONTRACTHDR",
            schema=SCHEMA,
            seat="LIRIS",
            status="MEASURED_LOCAL",
            root=root,
            strict=int(args.strict),
            git=int(git_available),
            receipt_excluded=(
                rel(root, receipt_path) if receipt_path is not None else "none"
            ),
        ),
    )

    # LF-only publication surfaces.
    lf_files = [
        path
        for path in files
        if path.name in LF_NAMES or path.suffix.lower() in LF_SUFFIXES
    ]
    for path in sorted(lf_files, key=lambda p: rel(root, p)):
        try:
            cr_count, lf_count, final_lf = stream_lf_state(path)
            ok = cr_count == 0
            output_rows.append(
                row(
                    "LFGATE",
                    path=rel(root, path),
                    bytes=path.stat().st_size,
                    cr_bytes=cr_count,
                    lf_bytes=lf_count,
                    final_lf=final_lf,
                    ok=int(ok),
                    status="MEASURED",
                )
            )
            if not ok:
                errors += 1
        except OSError as exc:
            output_rows.append(
                row(
                    "LFGATE",
                    path=rel(root, path),
                    ok=0,
                    status="FAIL",
                    reason=exc.__class__.__name__,
                )
            )
            errors += 1

    # SHA sidecars and missing/dangling relationships.
    referenced_targets: set[Path] = set()
    sidecars = sorted(
        (p for p in files if p.suffix.lower() == ".sha256"),
        key=lambda p: rel(root, p),
    )
    for sidecar in sidecars:
        valid_rows = 0
        try:
            with sidecar.open("r", encoding="utf-8", newline="") as handle:
                lines = handle.read().splitlines()
        except (OSError, UnicodeError) as exc:
            output_rows.append(
                row(
                    "SIDECARGATE",
                    sidecar=rel(root, sidecar),
                    ok=0,
                    status="FAIL",
                    reason=exc.__class__.__name__,
                )
            )
            errors += 1
            continue
        for number, text in enumerate(lines, 1):
            if not text.strip() or text.lstrip().startswith("#"):
                continue
            match = SIDECAR_RE.match(text)
            if match is None:
                output_rows.append(
                    row(
                        "SIDECARGATE",
                        sidecar=rel(root, sidecar),
                        line=number,
                        ok=0,
                        status="FAIL",
                        reason="malformed_sha256_row",
                    )
                )
                errors += 1
                continue
            valid_rows += 1
            expected = match.group(1).lower()
            target = resolve_sidecar_target(root, sidecar, match.group(2))
            target_resolved = target.resolve(strict=False)
            if not inside(root, target_resolved):
                output_rows.append(
                    row(
                        "SIDECARGATE",
                        sidecar=rel(root, sidecar),
                        line=number,
                        target=target,
                        ok=0,
                        status="FAIL",
                        reason="target_outside_root",
                    )
                )
                errors += 1
                continue
            referenced_targets.add(target_resolved)
            if not target.is_file():
                output_rows.append(
                    row(
                        "SIDECARGATE",
                        sidecar=rel(root, sidecar),
                        line=number,
                        target=rel(root, target),
                        expected=expected,
                        ok=0,
                        status="FAIL",
                        reason="dangling_target",
                    )
                )
                errors += 1
                continue
            try:
                actual = digest_cache.sha256(target)
                ok = actual == expected
                output_rows.append(
                    row(
                        "SIDECARGATE",
                        sidecar=rel(root, sidecar),
                        line=number,
                        target=rel(root, target),
                        bytes=target.stat().st_size,
                        expected=expected,
                        actual=actual,
                        ok=int(ok),
                        status="MEASURED",
                    )
                )
                if not ok:
                    errors += 1
            except OSError as exc:
                output_rows.append(
                    row(
                        "SIDECARGATE",
                        sidecar=rel(root, sidecar),
                        line=number,
                        target=rel(root, target),
                        ok=0,
                        status="FAIL",
                        reason=exc.__class__.__name__,
                    )
                )
                errors += 1
        if valid_rows == 0:
            output_rows.append(
                row(
                    "SIDECARGATE",
                    sidecar=rel(root, sidecar),
                    ok=0,
                    status="FAIL",
                    reason="no_digest_rows",
                )
            )
            errors += 1

    sealed_targets = sorted(
        (
            path
            for path in files
            if path.suffix.lower() in SIDECAR_SUFFIXES
            and not path.name.endswith(".sha256")
        ),
        key=lambda p: rel(root, p),
    )
    for target in sealed_targets:
        if target.resolve(strict=False) not in referenced_targets:
            expected_sidecar = Path(str(target) + ".sha256")
            output_rows.append(
                row(
                    "SIDECARMISSING",
                    target=rel(root, target),
                    expected_sidecar=rel(root, expected_sidecar),
                    ok=0,
                    status="MEASURED",
                )
            )
            errors += 1

    # Binary byte census.  A count is a byte count, not a parsed semantic claim.
    for path in sorted(
        (p for p in files if p.suffix.lower() in BINARY_COUNT_SUFFIXES),
        key=lambda p: rel(root, p),
    ):
        try:
            output_rows.append(
                row(
                    "BINARYBYTES",
                    path=rel(root, path),
                    kind=path.suffix.lower().lstrip(".").upper(),
                    bytes=path.stat().st_size,
                    sha256=digest_cache.sha256(path),
                    status="MEASURED",
                )
            )
        except OSError as exc:
            output_rows.append(
                row(
                    "BINARYBYTES",
                    path=rel(root, path),
                    ok=0,
                    status="FAIL",
                    reason=exc.__class__.__name__,
                )
            )
            errors += 1

    # Git raw-byte and LFS hydration gates.
    if git_available:
        try:
            entries = git_entries(root)
        except (OSError, subprocess.CalledProcessError, ValueError) as exc:
            output_rows.append(
                row(
                    "GITGATE",
                    status="FAIL",
                    ok=0,
                    reason=exc.__class__.__name__,
                )
            )
            errors += 1
            entries = []
        for entry in entries:
            if entry.stage != 0:
                output_rows.append(
                    row(
                        "GITBLOB",
                        path=entry.path,
                        stage=entry.stage,
                        ok=0,
                        status="FAIL",
                        reason="unmerged_index_stage",
                    )
                )
                errors += 1
                continue
            path = root / Path(entry.path)
            if entry.mode not in {"100644", "100755"}:
                output_rows.append(
                    row(
                        "GITBLOB",
                        path=entry.path,
                        mode=entry.mode,
                        status="SKIPPED_NONREGULAR",
                    )
                )
                warnings += 1
                continue
            if not path.is_file():
                output_rows.append(
                    row(
                        "GITBLOB",
                        path=entry.path,
                        index_oid=entry.oid,
                        ok=0,
                        status="FAIL",
                        reason="tracked_worktree_file_missing",
                    )
                )
                errors += 1
                continue
            prefix = git_blob_prefix(root, entry.oid)
            if prefix is None:
                output_rows.append(
                    row(
                        "GITBLOB",
                        path=entry.path,
                        index_oid=entry.oid,
                        ok=0,
                        status="FAIL",
                        reason="index_blob_unreadable",
                    )
                )
                errors += 1
                continue
            pointer = parse_lfs_pointer(prefix) if prefix else None
            if pointer is not None:
                expected_sha, expected_size = pointer
                try:
                    actual_size = path.stat().st_size
                    actual_sha = digest_cache.sha256(path)
                    hydrated = not (
                        actual_size == len(prefix)
                        and path.read_bytes() == prefix
                    )
                    ok = (
                        hydrated
                        and actual_size == expected_size
                        and actual_sha == expected_sha
                    )
                    output_rows.append(
                        row(
                            "LFSPAYLOAD",
                            path=entry.path,
                            pointer_oid=entry.oid,
                            expected_sha256=expected_sha,
                            actual_sha256=actual_sha,
                            expected_bytes=expected_size,
                            actual_bytes=actual_size,
                            hydrated=int(hydrated),
                            ok=int(ok),
                            status="MEASURED",
                        )
                    )
                    if not ok:
                        errors += 1
                except OSError as exc:
                    output_rows.append(
                        row(
                            "LFSPAYLOAD",
                            path=entry.path,
                            pointer_oid=entry.oid,
                            ok=0,
                            status="FAIL",
                            reason=exc.__class__.__name__,
                        )
                    )
                    errors += 1
                continue
            actual_oid, detail = raw_worktree_blob_oid(root, entry.path)
            ok = actual_oid == entry.oid
            output_rows.append(
                row(
                    "GITBLOB",
                    path=entry.path,
                    mode=entry.mode,
                    index_oid=entry.oid,
                    worktree_oid=actual_oid or "unreadable",
                    raw_bytes_equal=int(ok),
                    ok=int(ok),
                    status="MEASURED" if actual_oid is not None else "FAIL",
                    reason=detail if detail else "none",
                )
            )
            if not ok:
                errors += 1
    else:
        output_rows.append(
            row(
                "GITGATE",
                status="SKIPPED",
                reason="skip_git_requested"
                if args.skip_git
                else "git_metadata_unavailable",
                ok="NA",
            )
        )

    # Inventory root is over the pre-receipt worktree.  The requested receipt and
    # its sidecar are excluded explicitly to avoid a self-referential hash.
    try:
        root_digest, file_count, byte_count = inventory_root(
            root, files, digest_cache
        )
        output_rows.append(
            row(
                "INVENTORYROOT",
                algorithm=(
                    "sha256(sorted(len(path):path NUL bytes NUL sha256 LF))"
                ),
                files=file_count,
                bytes=byte_count,
                sha256=root_digest,
                receipt_excluded=int(receipt_path is not None),
                status="MEASURED",
            )
        )
    except OSError as exc:
        output_rows.append(
            row(
                "INVENTORYROOT",
                ok=0,
                status="FAIL",
                reason=exc.__class__.__name__,
            )
        )
        errors += 1

    verdict = "PASS" if errors == 0 else "FAIL"
    output_rows.append(
        row(
            "BYTECONTRACTEND",
            verdict=verdict,
            errors=errors,
            warnings=warnings,
            files=len(files),
            strict=int(args.strict),
            status="MEASURED_LOCAL",
        )
    )

    payload = receipt_bytes(output_rows)
    sys.stdout.buffer.write(payload)

    if receipt_path is not None and sidecar_path is not None:
        try:
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_bytes(payload)
            receipt_sha = hashlib.sha256(payload).hexdigest()
            sidecar_payload = (
                f"{receipt_sha}  {receipt_path.name}\n".encode("ascii")
            )
            sidecar_path.write_bytes(sidecar_payload)
        except OSError as exc:
            print(
                row(
                    "RECEIPTWRITE",
                    receipt=receipt_path,
                    ok=0,
                    status="FAIL",
                    reason=exc.__class__.__name__,
                ),
                file=sys.stderr,
            )
            return 2

    if args.strict and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
