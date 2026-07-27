#!/usr/bin/env python3
"""Emit and verify the byte-exact 3,078-byte Sol 5.6 bank address.

This is an ADDRESS/RECIPE, not a container for model weights or function bodies.
The recoverable object is the ordered bank manifest plus every byte-exact member it
names.  The address uses the existing Rust ``asolaria-tribit`` seed contract without
changing a byte:

    38 records x 81 bytes = 3,078 bytes

Each record is:

    16 B chained pid | 32 B digest | 5 B segment length | 4 B index
    | 16 B root suffix | 7 B witness | 1 B tier

The manifest closes four things independently:

* version: schema, bank, decoder-contract and codebook versions;
* decoder: Rust source/toolchain plus the compiled deterministic WASM;
* codebook: the exact 154 x 81-byte callable-function HBI;
* data: an ordered list of GGUF projections and true centre-plane slices.

The final 3,078-byte address binds the complete manifest.  Verification requires the
manifest and bank members, deliberately: 3,078 bytes do not contain the raw functions,
raw model weights, or multi-megabyte GGUF tensors.

Evidence boundary:

* subject: LIRIS-local Sol 5.6 callable-function projection;
* raw model weights: not present;
* GPT-6 Ultra: MISSING_REQUIRED_INPUT, relabel_sol=0.

No floats, JSON, random state, timestamps, absolute paths, or platform line endings
enter the contract.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


RECORDS = 38
RECORD_BYTES = 81
ADDRESS_BYTES = RECORDS * RECORD_BYTES
FUNCTION_RECORDS = 154
FUNCTION_RECORD_BYTES = 81
FUNCTION_CODEBOOK_BYTES = FUNCTION_RECORDS * FUNCTION_RECORD_BYTES

SCHEMA = "ASOLARIA-SOL56-BANK-V2"
BANK_VERSION = "2"
DECODER_CONTRACT_VERSION = "ASOLARIA-TRIBIT-SEED-V1"
CODEBOOK_VERSION = "LIRIS-CALLABLE-FUNCTIONS-154X81-V1"
ADDRESS_BASENAME = "ASOLARIA-LIRIS-SOL56-ADDRESS-3078.hbi"
MANIFEST_BASENAME = "ASOLARIA-LIRIS-SOL56-BANK-V2.hbp"

# This text pins the algorithm independently of source formatting.  The Rust source and
# WASM are also bank members, so both the abstract contract and its concrete decoder close.
DECODER_CONTRACT = (
    b"ASOLARIA-TRIBIT-SEED-V1\n"
    b"records=38\n"
    b"record_bytes=81\n"
    b"root=sha256(manifest_bytes)\n"
    b"prev_pid=root[0:16] before record 0\n"
    b"record_pid[i]=sha256(prev_pid||0x7c||u32be(i))[0:16];prev_pid=record_pid[i]\n"
    b"chunk=ceil(len(manifest_bytes)/38),empty=0\n"
    b"digest[i]=sha256(pid[i]||manifest_segment[i])\n"
    b"layout=pid16,digest32,segment_u40be,index_u32be,root_suffix16,witness7,tier1\n"
    b"witness[i]=sha256(pid[i]||digest[i])[0:7]\n"
    b"tier[i]=(min(len(manifest_bytes),127)^i)&0x7f\n"
)
DECODER_CONTRACT_SHA256 = hashlib.sha256(DECODER_CONTRACT).hexdigest()


@dataclass(frozen=True)
class MemberSpec:
    role: str
    path: str


@dataclass(frozen=True)
class MeasuredMember:
    ordinal: int
    role: str
    path: str
    byte_count: int
    sha256: str


# Order is semantic and therefore explicit.  Do not sort this tuple.  Reordering changes
# the bank identity and is rejected by verification against this declared order.
DEFAULT_MEMBERS: tuple[MemberSpec, ...] = (
    MemberSpec("decoder_crate_manifest", "crates/asolaria-tribit/Cargo.toml"),
    MemberSpec("decoder_toolchain", "crates/asolaria-tribit/rust-toolchain.toml"),
    MemberSpec("decoder_source_lib", "crates/asolaria-tribit/src/lib.rs"),
    MemberSpec("decoder_source_tribit", "crates/asolaria-tribit/src/tribit.rs"),
    MemberSpec("decoder_wasm", "web/asolaria_tribit.wasm"),
    MemberSpec(
        "function_codebook_hbi",
        "liris/functions/LIRIS-CODEX-RUNTIME-FUNCTIONS-154x81.hbi",
    ),
    MemberSpec(
        "function_surface_hbp",
        "liris/functions/LIRIS-CODEX-RUNTIME-FUNCTIONS-2026-07-27.hbp",
    ),
    MemberSpec(
        "projection_universe_gguf",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-UNIVERSE.gguf",
    ),
    MemberSpec(
        "projection_geometry_gguf",
        "gguf/liris/SOL56-ULTRA-FUNCTION-GEOMETRY-64.gguf",
    ),
    MemberSpec(
        "projection_colour_atlas_gguf",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-COLOUR-QR-ATLAS.gguf",
    ),
    MemberSpec(
        "slice_p0_xy",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P0-XY.gguf",
    ),
    MemberSpec(
        "slice_p0_yz",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P0-YZ.gguf",
    ),
    MemberSpec(
        "slice_p0_zx",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P0-ZX.gguf",
    ),
    MemberSpec(
        "slice_p1_xy",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P1-XY.gguf",
    ),
    MemberSpec(
        "slice_p1_yz",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P1-YZ.gguf",
    ),
    MemberSpec(
        "slice_p1_zx",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P1-ZX.gguf",
    ),
    MemberSpec(
        "slice_p2_xy",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P2-XY.gguf",
    ),
    MemberSpec(
        "slice_p2_yz",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P2-YZ.gguf",
    ),
    MemberSpec(
        "slice_p2_zx",
        "gguf/liris/ASOLARIA-LIRIS-SOL56-FUNCTION-64-P2-ZX.gguf",
    ),
    MemberSpec(
        "pump_v4_source",
        "liris/measurements/pump_function_sphere_64.py",
    ),
    MemberSpec(
        "pump_v4_receipt_hbp",
        "receipts/LIRIS-SOL56-STAR-SHELL-V4-2026-07-27.hbp",
    ),
    MemberSpec(
        "pump_v4_receipt_sha256",
        "receipts/LIRIS-SOL56-STAR-SHELL-V4-2026-07-27.hbp.sha256",
    ),
    MemberSpec(
        "pump_v4_self_full_gguf",
        "gguf/liris/star-shell-v4/"
        "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-SELF-FULL.gguf",
    ),
    MemberSpec(
        "pump_v4_self_centre_slices_gguf",
        "gguf/liris/star-shell-v4/"
        "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-SELF-CENTRE-SLICES.gguf",
    ),
    MemberSpec(
        "pump_v4_anti_fable_full_gguf",
        "gguf/liris/star-shell-v4/"
        "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-ANTI_FABLE-FULL.gguf",
    ),
    MemberSpec(
        "pump_v4_anti_fable_centre_slices_gguf",
        "gguf/liris/star-shell-v4/"
        "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-ANTI_FABLE-CENTRE-SLICES.gguf",
    ),
    MemberSpec(
        "pump_v4_anti_anti_mythos_full_gguf",
        "gguf/liris/star-shell-v4/"
        "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-ANTI_ANTI_MYTHOS-FULL.gguf",
    ),
    MemberSpec(
        "pump_v4_anti_anti_mythos_centre_slices_gguf",
        "gguf/liris/star-shell-v4/"
        "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-ANTI_ANTI_MYTHOS-CENTRE-SLICES.gguf",
    ),
)

V4_GGUF_ROLES: tuple[str, ...] = (
    "pump_v4_self_full_gguf",
    "pump_v4_self_centre_slices_gguf",
    "pump_v4_anti_fable_full_gguf",
    "pump_v4_anti_fable_centre_slices_gguf",
    "pump_v4_anti_anti_mythos_full_gguf",
    "pump_v4_anti_anti_mythos_centre_slices_gguf",
)
V4_BANK_ROLES: tuple[str, ...] = (
    "pump_v4_source",
    "pump_v4_receipt_hbp",
    "pump_v4_receipt_sha256",
    *V4_GGUF_ROLES,
)


class ContractError(ValueError):
    """The bank, manifest, or address violates the pinned byte contract."""


def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _clean_atom(value: str, label: str) -> str:
    if not value or any(char in value for char in "|\r\n="):
        raise ContractError(f"{label} is not a safe HBP atom: {value!r}")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ContractError(f"{label} must be ASCII: {value!r}") from exc
    return value


def _row(tag: str, fields: Iterable[tuple[str, object]]) -> bytes:
    _clean_atom(tag, "row tag")
    parts = [tag]
    for key, raw_value in fields:
        _clean_atom(key, "field name")
        value = _clean_atom(str(raw_value), f"value for {key}")
        parts.append(f"{key}={value}")
    return ("|".join(parts) + "\n").encode("ascii")


def _inside_root(root: Path, relative: str) -> Path:
    normalized = Path(relative)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ContractError(f"bank member must be a safe relative path: {relative}")
    resolved_root = root.resolve()
    resolved = (resolved_root / normalized).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ContractError(f"bank member escapes the bank root: {relative}") from exc
    return resolved


def measure_members(
    root: Path, specs: Sequence[MemberSpec] = DEFAULT_MEMBERS
) -> tuple[MeasuredMember, ...]:
    roles: set[str] = set()
    paths: set[str] = set()
    measured: list[MeasuredMember] = []
    for ordinal, spec in enumerate(specs):
        role = _clean_atom(spec.role, "member role")
        relative = spec.path.replace("\\", "/")
        _clean_atom(relative, "member path")
        if role in roles:
            raise ContractError(f"duplicate bank role: {role}")
        if relative in paths:
            raise ContractError(f"duplicate bank path: {relative}")
        roles.add(role)
        paths.add(relative)
        path = _inside_root(root, relative)
        if not path.is_file():
            raise ContractError(f"missing bank member {ordinal}: {relative}")
        measured.append(
            MeasuredMember(
                ordinal=ordinal,
                role=role,
                path=relative,
                byte_count=path.stat().st_size,
                sha256=sha256_file(path),
            )
        )
    if not measured:
        raise ContractError("bank must contain at least one member")
    return tuple(measured)


def member_row(member: MeasuredMember) -> bytes:
    return _row(
        "SOL56BANKMEMBER",
        (
            ("ordinal", f"{member.ordinal:04d}"),
            ("role", member.role),
            ("path", member.path),
            ("bytes", member.byte_count),
            ("sha256", member.sha256),
            ("required", 1),
            ("json", 0),
        ),
    )


def verify_v4_closure(root: Path, by_role: dict[str, MeasuredMember]) -> str:
    """Cross-check the executed V4 receipt, its sidecar, source, and six GGUFs."""

    absent = [role for role in V4_BANK_ROLES if role not in by_role]
    if absent:
        raise ContractError(f"V4 bank lacks required roles: {','.join(absent)}")

    source = by_role["pump_v4_source"]
    source_bytes = _inside_root(root, source.path).read_bytes()
    if b"ASOLARIA-LIRIS-FUNCTION-PUMP-64-V4-REVERSIBLE-SPATIAL" not in source_bytes:
        raise ContractError("pump source does not declare the V4 reversible-spatial schema")

    receipt = by_role["pump_v4_receipt_hbp"]
    receipt_bytes = _inside_root(root, receipt.path).read_bytes()
    if not receipt_bytes.startswith(
        b"PUMPFUN64HDR|schema=ASOLARIA-LIRIS-FUNCTION-PUMP-64-V4-REVERSIBLE-SPATIAL|"
    ):
        raise ContractError("V4 receipt header is absent or not byte-exact")
    if b"geometry_class_after_execution=LIRIS_DESIGN_MEASURED" not in receipt_bytes:
        raise ContractError("V4 receipt does not carry the post-execution measurement row")
    if b"sol_relabelled_as_gpt6=0" not in receipt_bytes:
        raise ContractError("V4 receipt does not preserve the GPT-6 relabel boundary")

    receipt_sidecar = by_role["pump_v4_receipt_sha256"]
    sidecar_bytes = _inside_root(root, receipt_sidecar.path).read_bytes()
    try:
        sidecar_parts = sidecar_bytes.decode("ascii").strip().split()
    except UnicodeDecodeError as exc:
        raise ContractError("V4 receipt sidecar is not ASCII") from exc
    expected_sidecar = [receipt.sha256, Path(receipt.path).name]
    if sidecar_parts != expected_sidecar:
        raise ContractError(
            "V4 receipt sidecar does not close the receipt: "
            f"expected={expected_sidecar!r} got={sidecar_parts!r}"
        )

    for role in V4_GGUF_ROLES:
        member = by_role[role]
        if not member.path.startswith("gguf/liris/star-shell-v4/"):
            raise ContractError(f"{role} is not in the V4-only bank directory")
        needle = (
            f"path={member.path}|bytes={member.byte_count}|sha256={member.sha256}|"
        ).encode("ascii")
        if needle not in receipt_bytes:
            raise ContractError(f"V4 receipt does not close {role}")

    return hashlib.sha256(
        b"".join(bytes.fromhex(by_role[role].sha256) for role in V4_BANK_ROLES)
    ).hexdigest()


def build_manifest(
    root: Path, specs: Sequence[MemberSpec] = DEFAULT_MEMBERS
) -> tuple[bytes, tuple[MeasuredMember, ...]]:
    measured = measure_members(root, specs)
    by_role = {member.role: member for member in measured}
    required_roles = {
        "decoder_crate_manifest",
        "decoder_toolchain",
        "decoder_source_lib",
        "decoder_source_tribit",
        "decoder_wasm",
        "function_codebook_hbi",
        "function_surface_hbp",
        "projection_universe_gguf",
        "projection_geometry_gguf",
        "projection_colour_atlas_gguf",
    } | set(V4_BANK_ROLES)
    absent = sorted(required_roles - by_role.keys())
    if absent:
        raise ContractError(f"bank lacks required roles: {','.join(absent)}")

    codebook = by_role["function_codebook_hbi"]
    if codebook.byte_count != FUNCTION_CODEBOOK_BYTES:
        raise ContractError(
            "callable-function codebook is not exactly "
            f"{FUNCTION_RECORDS}x{FUNCTION_RECORD_BYTES}: "
            f"{codebook.byte_count} bytes"
        )

    v4_bank_root = verify_v4_closure(root, by_role)

    decoder_roles = (
        "decoder_crate_manifest",
        "decoder_toolchain",
        "decoder_source_lib",
        "decoder_source_tribit",
        "decoder_wasm",
    )
    decoder_preimage = b"".join(
        bytes.fromhex(by_role[role].sha256) for role in decoder_roles
    )
    decoder_bank_root = hashlib.sha256(decoder_preimage).hexdigest()

    header = _row(
        "SOL56BANKHDR",
        (
            ("schema", SCHEMA),
            ("bank_version", BANK_VERSION),
            ("seat", "LIRIS"),
            ("model_surface", "SOL_5_6_ULTRA"),
            ("subject", "CALLABLE_FUNCTION_PROJECTION"),
            ("members", len(measured)),
            ("ordering", "DECLARED_ORDINAL"),
            ("address_records", RECORDS),
            ("record_bytes", RECORD_BYTES),
            ("address_bytes", ADDRESS_BYTES),
            ("raw_functions", 0),
            ("raw_model_weights", 0),
            ("executed_v4_members", len(V4_BANK_ROLES)),
            ("defective_v1_full_included", 0),
            ("defective_v3_full_included", 0),
            ("json", 0),
        ),
    )
    boundary = _row(
        "SOL56BANKBOUNDARY",
        (
            ("evidence", "LIRIS_LOCAL_MEASURED"),
            ("address_semantics", "RECIPE_NOT_CONTAINER"),
            ("raw_model_weights", "MISSING_REQUIRED_INPUT"),
            ("gpt6_ultra", "MISSING_REQUIRED_INPUT"),
            ("relabel_sol", 0),
            ("json", 0),
        ),
    )
    decoder = _row(
        "SOL56BANKDECODER",
        (
            ("contract_version", DECODER_CONTRACT_VERSION),
            ("contract_sha256", DECODER_CONTRACT_SHA256),
            ("bank_members_sha256", decoder_bank_root),
            ("rust_version", "1.81"),
            ("integer_only", 1),
            ("float_fields", 0),
            ("json", 0),
        ),
    )
    codebook_row = _row(
        "SOL56BANKCODEBOOK",
        (
            ("version", CODEBOOK_VERSION),
            ("member_ordinal", f"{codebook.ordinal:04d}"),
            ("records", FUNCTION_RECORDS),
            ("record_bytes", FUNCTION_RECORD_BYTES),
            ("bytes", codebook.byte_count),
            ("sha256", codebook.sha256),
            ("json", 0),
        ),
    )
    v4_row = _row(
        "SOL56BANKV4",
        (
            ("schema", "ASOLARIA-LIRIS-FUNCTION-PUMP-64-V4-REVERSIBLE-SPATIAL"),
            ("members", len(V4_BANK_ROLES)),
            ("full_ggufs", 3),
            ("centre_slice_ggufs", 3),
            ("bank_members_sha256", v4_bank_root),
            ("executed_receipt", 1),
            ("defective_v1_full_included", 0),
            ("defective_v3_full_included", 0),
            ("json", 0),
        ),
    )
    rows = b"".join(member_row(member) for member in measured)
    member_root = hashlib.sha256(rows).hexdigest()
    preclose = header + boundary + decoder + codebook_row + v4_row + rows
    close = _row(
        "SOL56BANKCLOSE",
        (
            ("member_root_sha256", member_root),
            ("preclose_sha256", hashlib.sha256(preclose).hexdigest()),
            ("decoder_contract_sha256", DECODER_CONTRACT_SHA256),
            ("codebook_sha256", codebook.sha256),
            ("members", len(measured)),
            ("complete", 1),
            ("json", 0),
        ),
    )
    manifest = preclose + close
    if b"\r" in manifest or not manifest.endswith(b"\n"):
        raise AssertionError("manifest must be canonical LF tuple text")
    return manifest, measured


def seed_exact(data: bytes) -> bytes:
    """Independent Python implementation of ``asolaria_tribit::seed``."""

    root = sha256_bytes(data)
    pid = root[:16]
    chunk = 0 if not data else (len(data) + RECORDS - 1) // RECORDS
    out = bytearray(ADDRESS_BYTES)

    for index in range(RECORDS):
        pid = sha256_bytes(pid + b"|" + index.to_bytes(4, "big"))[:16]
        lo = min(index * chunk, len(data))
        hi = min(lo + chunk, len(data))
        digest = sha256_bytes(pid + data[lo:hi])
        witness = sha256_bytes(pid + digest)
        segment = hi - lo
        offset = index * RECORD_BYTES
        out[offset : offset + 16] = pid
        out[offset + 16 : offset + 48] = digest
        out[offset + 48 : offset + 53] = segment.to_bytes(8, "big")[3:8]
        out[offset + 53 : offset + 57] = index.to_bytes(4, "big")
        out[offset + 57 : offset + 73] = root[16:32]
        out[offset + 73 : offset + 80] = witness[:7]
        out[offset + 80] = (min(len(data), 127) ^ index) & 0x7F
    return bytes(out)


def cells_reached(data: bytes) -> int:
    seen: set[int] = set()
    for offset in range(0, len(data) - 2, 3):
        bands = tuple(min(data[offset + axis] // 86, 2) for axis in range(3))
        seen.add(bands[0] * 9 + bands[1] * 3 + bands[2])
    return len(seen)


def parse_row(line: bytes) -> tuple[str, dict[str, str]]:
    try:
        parts = line.decode("ascii").split("|")
    except UnicodeDecodeError as exc:
        raise ContractError("manifest must be ASCII tuple text") from exc
    tag = parts[0]
    fields: dict[str, str] = {}
    for item in parts[1:]:
        if "=" not in item:
            raise ContractError(f"malformed HBP field: {item!r}")
        key, value = item.split("=", 1)
        if key in fields:
            raise ContractError(f"duplicate HBP field {key!r}")
        fields[key] = value
    return tag, fields


def parse_manifest(manifest: bytes) -> list[tuple[str, dict[str, str]]]:
    if b"\r" in manifest or not manifest.endswith(b"\n"):
        raise ContractError("manifest is not canonical LF-terminated bytes")
    lines = manifest[:-1].split(b"\n")
    rows = [parse_row(line) for line in lines]
    if len(rows) < 6:
        raise ContractError("manifest is truncated")
    if rows[0][0] != "SOL56BANKHDR" or rows[-1][0] != "SOL56BANKCLOSE":
        raise ContractError("manifest header/closure rows are missing")
    return rows


def _expect(fields: dict[str, str], key: str, expected: object) -> None:
    got = fields.get(key)
    if got != str(expected):
        raise ContractError(f"{key}: expected {expected!r}, got {got!r}")


def verify_manifest(
    root: Path,
    manifest: bytes,
    expected_specs: Sequence[MemberSpec] = DEFAULT_MEMBERS,
) -> tuple[MeasuredMember, ...]:
    rows = parse_manifest(manifest)
    header = rows[0][1]
    _expect(header, "schema", SCHEMA)
    _expect(header, "bank_version", BANK_VERSION)
    _expect(header, "address_records", RECORDS)
    _expect(header, "record_bytes", RECORD_BYTES)
    _expect(header, "address_bytes", ADDRESS_BYTES)
    _expect(header, "raw_functions", 0)
    _expect(header, "raw_model_weights", 0)
    _expect(header, "ordering", "DECLARED_ORDINAL")
    _expect(header, "executed_v4_members", len(V4_BANK_ROLES))
    _expect(header, "defective_v1_full_included", 0)
    _expect(header, "defective_v3_full_included", 0)

    boundary_rows = [fields for tag, fields in rows if tag == "SOL56BANKBOUNDARY"]
    if len(boundary_rows) != 1:
        raise ContractError("manifest must carry exactly one evidence boundary")
    boundary = boundary_rows[0]
    _expect(boundary, "address_semantics", "RECIPE_NOT_CONTAINER")
    _expect(boundary, "gpt6_ultra", "MISSING_REQUIRED_INPUT")
    _expect(boundary, "relabel_sol", 0)
    _expect(boundary, "raw_model_weights", "MISSING_REQUIRED_INPUT")

    decoder_rows = [fields for tag, fields in rows if tag == "SOL56BANKDECODER"]
    codebook_rows = [fields for tag, fields in rows if tag == "SOL56BANKCODEBOOK"]
    v4_rows = [fields for tag, fields in rows if tag == "SOL56BANKV4"]
    if len(decoder_rows) != 1 or len(codebook_rows) != 1 or len(v4_rows) != 1:
        raise ContractError("manifest decoder/codebook/V4 closure is not unique")
    decoder = decoder_rows[0]
    codebook = codebook_rows[0]
    v4 = v4_rows[0]
    _expect(decoder, "contract_version", DECODER_CONTRACT_VERSION)
    _expect(decoder, "contract_sha256", DECODER_CONTRACT_SHA256)
    _expect(decoder, "rust_version", "1.81")
    _expect(decoder, "integer_only", 1)
    _expect(decoder, "float_fields", 0)
    _expect(codebook, "version", CODEBOOK_VERSION)
    _expect(codebook, "records", FUNCTION_RECORDS)
    _expect(codebook, "record_bytes", FUNCTION_RECORD_BYTES)
    _expect(codebook, "bytes", FUNCTION_CODEBOOK_BYTES)
    _expect(
        v4,
        "schema",
        "ASOLARIA-LIRIS-FUNCTION-PUMP-64-V4-REVERSIBLE-SPATIAL",
    )
    _expect(v4, "members", len(V4_BANK_ROLES))
    _expect(v4, "full_ggufs", 3)
    _expect(v4, "centre_slice_ggufs", 3)
    _expect(v4, "executed_receipt", 1)
    _expect(v4, "defective_v1_full_included", 0)
    _expect(v4, "defective_v3_full_included", 0)

    member_fields = [fields for tag, fields in rows if tag == "SOL56BANKMEMBER"]
    if len(member_fields) != len(expected_specs):
        raise ContractError(
            f"member count changed: expected {len(expected_specs)}, "
            f"got {len(member_fields)}"
        )
    parsed_members: list[MeasuredMember] = []
    for ordinal, (fields, expected) in enumerate(zip(member_fields, expected_specs)):
        _expect(fields, "ordinal", f"{ordinal:04d}")
        _expect(fields, "role", expected.role)
        _expect(fields, "path", expected.path.replace("\\", "/"))
        _expect(fields, "required", 1)
        try:
            byte_count = int(fields["bytes"])
            bytes.fromhex(fields["sha256"])
        except (KeyError, ValueError) as exc:
            raise ContractError(f"member {ordinal} has invalid bytes/hash fields") from exc
        if len(fields["sha256"]) != 64:
            raise ContractError(f"member {ordinal} SHA-256 is not 32 bytes")
        parsed_members.append(
            MeasuredMember(
                ordinal=ordinal,
                role=fields["role"],
                path=fields["path"],
                byte_count=byte_count,
                sha256=fields["sha256"],
            )
        )

    actual_members = measure_members(root, expected_specs)
    if tuple(parsed_members) != actual_members:
        for expected, actual in zip(parsed_members, actual_members):
            if expected != actual:
                raise ContractError(
                    "bank member changed: "
                    f"ordinal={expected.ordinal} role={expected.role} "
                    f"manifest_bytes={expected.byte_count} actual_bytes={actual.byte_count} "
                    f"manifest_sha256={expected.sha256} actual_sha256={actual.sha256}"
                )
        raise ContractError("bank member set changed")

    member_blob = b"".join(member_row(member) for member in parsed_members)
    close = rows[-1][1]
    _expect(close, "member_root_sha256", hashlib.sha256(member_blob).hexdigest())
    _expect(close, "decoder_contract_sha256", DECODER_CONTRACT_SHA256)
    _expect(close, "members", len(parsed_members))
    _expect(close, "complete", 1)

    close_line = manifest.rstrip(b"\n").split(b"\n")[-1] + b"\n"
    preclose = manifest[: -len(close_line)]
    _expect(close, "preclose_sha256", hashlib.sha256(preclose).hexdigest())

    by_role = {member.role: member for member in parsed_members}
    _expect(v4, "bank_members_sha256", verify_v4_closure(root, by_role))
    codebook_member = by_role["function_codebook_hbi"]
    _expect(codebook, "member_ordinal", f"{codebook_member.ordinal:04d}")
    _expect(codebook, "sha256", codebook_member.sha256)
    _expect(close, "codebook_sha256", codebook_member.sha256)

    decoder_roles = (
        "decoder_crate_manifest",
        "decoder_toolchain",
        "decoder_source_lib",
        "decoder_source_tribit",
        "decoder_wasm",
    )
    decoder_preimage = b"".join(
        bytes.fromhex(by_role[role].sha256) for role in decoder_roles
    )
    _expect(
        decoder,
        "bank_members_sha256",
        hashlib.sha256(decoder_preimage).hexdigest(),
    )

    rebuilt, _ = build_manifest(root, expected_specs)
    if manifest != rebuilt:
        raise ContractError("manifest is not the canonical byte serialization")
    return tuple(parsed_members)


def verify_address(
    root: Path,
    manifest: bytes,
    address: bytes,
    expected_specs: Sequence[MemberSpec] = DEFAULT_MEMBERS,
) -> tuple[MeasuredMember, ...]:
    members = verify_manifest(root, manifest, expected_specs)
    if len(address) != ADDRESS_BYTES:
        raise ContractError(
            f"address length is {len(address)}, expected exactly {ADDRESS_BYTES}"
        )
    expected_address = seed_exact(manifest)
    if address != expected_address:
        raise ContractError("address does not match the byte-exact bank manifest")

    root_hash = sha256_bytes(manifest)
    for index in range(RECORDS):
        offset = index * RECORD_BYTES
        if address[offset + 53 : offset + 57] != index.to_bytes(4, "big"):
            raise ContractError(f"address record index {index} is corrupt")
        if address[offset + 57 : offset + 73] != root_hash[16:32]:
            raise ContractError(f"address record root binding {index} is corrupt")
        pid = address[offset : offset + 16]
        digest = address[offset + 16 : offset + 48]
        if address[offset + 73 : offset + 80] != sha256_bytes(pid + digest)[:7]:
            raise ContractError(f"address witness {index} is corrupt")
    return members


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def sidecar_bytes(path: Path, data: bytes) -> bytes:
    return f"{hashlib.sha256(data).hexdigest()}  {path.name}\n".encode("ascii")


def emit(root: Path, output_dir: Path) -> tuple[Path, Path]:
    manifest, _ = build_manifest(root)
    address = seed_exact(manifest)
    verify_address(root, manifest, address)

    address_path = output_dir / ADDRESS_BASENAME
    manifest_path = output_dir / MANIFEST_BASENAME
    _atomic_write(address_path, address)
    _atomic_write(manifest_path, manifest)
    _atomic_write(
        address_path.with_name(address_path.name + ".sha256"),
        sidecar_bytes(address_path, address),
    )
    _atomic_write(
        manifest_path.with_name(manifest_path.name + ".sha256"),
        sidecar_bytes(manifest_path, manifest),
    )
    verify_address(root, manifest_path.read_bytes(), address_path.read_bytes())
    return address_path, manifest_path


def _must_fail(label: str, action: object) -> None:
    try:
        if callable(action):
            action()
    except ContractError:
        return
    raise AssertionError(f"negative self-test did not fail: {label}")


def self_test(root: Path) -> tuple[bytes, bytes, tuple[MeasuredMember, ...]]:
    vectors = (
        (b"", "a91acae4ae2d1418db50095702096f5c81761fc422637972942f325465b2e730"),
        (b"a", "2b467e4cca4db694b9e172ea2346da8c873f501227dd9cb8c3b8234622d40530"),
        (b"abc", "907d5cec4b56072e7612b7834b377d8d4e2c9d0c4d44b2aac2b1ce379112f2c6"),
        (
            b"the quick brown fox",
            "839a079a56bb7a6db742180520cbe36fb9afafe6d4ad1e4e4f9313588c0807a6",
        ),
        (
            b"ASOLARIA",
            "27d7eddf5c216f289ee6416ca29285e67b5f3424650fe84cbaecb0c7c2202c87",
        ),
    )
    for payload, expected in vectors:
        address = seed_exact(payload)
        assert len(address) == ADDRESS_BYTES
        assert cells_reached(address) == 27
        actual = hashlib.sha256(address).hexdigest()
        assert actual == expected, (payload, actual, expected)

    live_manifest, live_members = build_manifest(root)
    live_address = seed_exact(live_manifest)
    assert build_manifest(root)[0] == live_manifest
    assert seed_exact(live_manifest) == live_address
    verify_address(root, live_manifest, live_address)
    assert len(live_address) == ADDRESS_BYTES
    assert len(live_address) % RECORD_BYTES == 0
    assert b"gpt6_ultra=MISSING_REQUIRED_INPUT" in live_manifest
    assert b"relabel_sol=0" in live_manifest
    assert b"raw_model_weights=MISSING_REQUIRED_INPUT" in live_manifest
    assert b"schema=ASOLARIA-SOL56-BANK-V2" in live_manifest
    assert b"executed_v4_members=9" in live_manifest
    assert b"defective_v1_full_included=0" in live_manifest
    assert b"defective_v3_full_included=0" in live_manifest

    with tempfile.TemporaryDirectory(prefix="asolaria-sol56-address-test-") as temp_name:
        temp_root = Path(temp_name)
        for ordinal, spec in enumerate(DEFAULT_MEMBERS):
            path = _inside_root(temp_root, spec.path)
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = (
                f"TESTBANK|ordinal={ordinal:04d}|role={spec.role}|json=0\n".encode(
                    "ascii"
                )
            )
            if spec.role == "function_codebook_hbi":
                payload = bytes((index * 73 + 19) & 0xFF for index in range(
                    FUNCTION_CODEBOOK_BYTES
                ))
            path.write_bytes(payload)

        test_source = _inside_root(
            temp_root, next(spec.path for spec in DEFAULT_MEMBERS
                            if spec.role == "pump_v4_source")
        )
        test_source.write_bytes(
            b"SCHEMA=ASOLARIA-LIRIS-FUNCTION-PUMP-64-V4-REVERSIBLE-SPATIAL\n"
        )
        test_by_role = {
            spec.role: _inside_root(temp_root, spec.path) for spec in DEFAULT_MEMBERS
        }
        receipt_lines = [
            b"PUMPFUN64HDR|schema=ASOLARIA-LIRIS-FUNCTION-PUMP-64-V4-REVERSIBLE-SPATIAL|json=0\n",
            b"OPERATOR_MAPPING|negative_third=GPT6|gpt6_manifest=ABSENT|sol_relabelled_as_gpt6=0|json=0\n",
        ]
        for role in V4_GGUF_ROLES:
            path = test_by_role[role]
            relative = next(spec.path for spec in DEFAULT_MEMBERS if spec.role == role)
            receipt_lines.append(
                (
                    f"GGUF|role={role}|path={relative}|bytes={path.stat().st_size}"
                    f"|sha256={sha256_file(path)}|json=0\n"
                ).encode("ascii")
            )
        receipt_lines.append(
            b"BOUNDARY|geometry_class_after_execution=LIRIS_DESIGN_MEASURED|json=0\n"
        )
        test_receipt = test_by_role["pump_v4_receipt_hbp"]
        test_receipt.write_bytes(b"".join(receipt_lines))
        test_sidecar = test_by_role["pump_v4_receipt_sha256"]
        test_sidecar.write_bytes(
            (
                f"{sha256_file(test_receipt)}  {test_receipt.name}\n"
            ).encode("ascii")
        )

        test_manifest, _ = build_manifest(temp_root)
        test_address = seed_exact(test_manifest)
        verify_address(temp_root, test_manifest, test_address)

        reordered_specs = list(DEFAULT_MEMBERS)
        reordered_specs[0], reordered_specs[1] = (
            reordered_specs[1],
            reordered_specs[0],
        )
        reordered_manifest, _ = build_manifest(temp_root, reordered_specs)
        reordered_address = seed_exact(reordered_manifest)
        assert reordered_address != test_address
        _must_fail(
            "reordered bank",
            lambda: verify_address(
                temp_root, reordered_manifest, reordered_address, DEFAULT_MEMBERS
            ),
        )

        tampered_path = _inside_root(temp_root, DEFAULT_MEMBERS[7].path)
        original = tampered_path.read_bytes()
        tampered_path.write_bytes(original + b"\x00")
        _must_fail(
            "tampered bank member",
            lambda: verify_address(temp_root, test_manifest, test_address),
        )
        tampered_path.write_bytes(original)
        verify_address(temp_root, test_manifest, test_address)

        missing_path = _inside_root(temp_root, DEFAULT_MEMBERS[-1].path)
        missing_bytes = missing_path.read_bytes()
        missing_path.unlink()
        _must_fail(
            "missing bank member",
            lambda: verify_address(temp_root, test_manifest, test_address),
        )
        missing_path.write_bytes(missing_bytes)
        verify_address(temp_root, test_manifest, test_address)

        corrupt_address = bytearray(test_address)
        corrupt_address[RECORD_BYTES + 17] ^= 0x01
        _must_fail(
            "tampered address",
            lambda: verify_address(temp_root, test_manifest, bytes(corrupt_address)),
        )

    return live_manifest, live_address, live_members


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def print_measurement(
    manifest: bytes, address: bytes, members: Sequence[MeasuredMember], mode: str
) -> None:
    bank_bytes = sum(member.byte_count for member in members)
    print(
        "SOL56ADDRRUN"
        f"|mode={mode}"
        "|evidence=LIRIS_LOCAL_MEASURED"
        f"|schema={SCHEMA}"
        f"|members={len(members)}"
        f"|bank_bytes={bank_bytes}"
        f"|manifest_bytes={len(manifest)}"
        f"|address_bytes={len(address)}"
        f"|records={RECORDS}"
        f"|record_bytes={RECORD_BYTES}"
        f"|cells={cells_reached(address)}"
        f"|manifest_sha256={hashlib.sha256(manifest).hexdigest()}"
        f"|address_sha256={hashlib.sha256(address).hexdigest()}"
        "|raw_functions=0"
        "|raw_model_weights=0"
        "|gpt6_ultra=MISSING_REQUIRED_INPUT"
        "|relabel_sol=0"
        "|json=0"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit/verify the exact 38x81-byte Sol 5.6 bank address."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=default_root(),
        help="repository/bank root (default: inferred from this script)",
    )
    parser.add_argument(
        "--emit-dir",
        type=Path,
        help="write the HBI address, HBP bank manifest, and SHA-256 sidecars",
    )
    parser.add_argument(
        "--verify-address",
        type=Path,
        help="verify an existing 3,078-byte address",
    )
    parser.add_argument(
        "--verify-manifest",
        type=Path,
        help="manifest paired with --verify-address",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run Rust cross-vectors plus reorder/tamper/missing-member gates",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()

    try:
        if bool(args.verify_address) != bool(args.verify_manifest):
            raise ContractError(
                "--verify-address and --verify-manifest must be provided together"
            )
        if args.self_test:
            manifest, address, members = self_test(root)
            print_measurement(manifest, address, members, "SELF_TEST_PASS")
        elif args.verify_address and args.verify_manifest:
            manifest = args.verify_manifest.read_bytes()
            address = args.verify_address.read_bytes()
            members = verify_address(root, manifest, address)
            print_measurement(manifest, address, members, "VERIFY_PASS")
        else:
            manifest, members = build_manifest(root)
            address = seed_exact(manifest)
            verify_address(root, manifest, address)
            print_measurement(manifest, address, members, "DRY_RUN_PASS")

        if args.emit_dir:
            address_path, manifest_path = emit(root, args.emit_dir.resolve())
            print(
                "SOL56ADDREMIT"
                f"|address={address_path.as_posix()}"
                f"|manifest={manifest_path.as_posix()}"
                "|verified=1"
                "|json=0"
            )
    except (ContractError, OSError, AssertionError) as exc:
        print(
            "SOL56ADDRFAIL"
            f"|error={type(exc).__name__}"
            f"|detail={str(exc).replace('|', '/').replace(chr(10), ' ')}"
            "|json=0",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
