#!/usr/bin/env python3
"""Address the LIRIS callable-function matrix as gradiated stars on shell levels.

This is the LIRIS counterpart to ``measurements/pump_mythos_sphere.py``, but it
does not copy that script's measurement defects.

SUBJECT
    The input is the current LIRIS callable-function manifest produced from the
    runtime tool surface.  It is labelled ``gpt-5.6-sol``.  It is not model
    weights, emitted artifacts, or a GPT-6 manifest.

COORDINATES AND POPULATIONS
    The manifest's 64-D feature vectors are reduced with the exact deterministic
    PCA implementation in ``see_function_matrix_64.py``.  The three PCA
    coordinates are quantized once to 0..255.  Red/green/blue ownership is
    frozen from the *untransformed continuous coordinates*: a function belongs
    to the coordinate that strictly dominates; exact ties are the free register.
    P/R/G flashlights may move a function, but cannot change which population
    owns it.  That prevents three views from becoming three relabelled objects.

STARS AND FOUR AXES
    A projected function is a star, not a character in a flat 256-glyph
    alphabet.  Its stable identity is the manifest ordinal.  The manifest
    ordinal is also the exact TIME coordinate that the earlier byte-triple
    projection discarded.  The remaining three projection channels are stored
    beside it as the provisional colour/energy/space coordinates:

        (time, colour, energy, space)
        = (manifest ordinal, PCA0 byte, PCA1 byte, PCA2 byte)

    That PCA-to-semantics binding is DESIGN, not canon.  It is declared in the
    GGUF and receipt so another seat can replace it without changing identity.
    Each star also carries its occupied integer shell about the true geometric
    centre.  Shells emerge from measured positions; this program does not use a
    flat alphabet census as a proxy for shell population.

FLASHLIGHT ADDRESSING
    P/R/G remain named gradiated flashlight views, and levels 1..4 retain the
    complete 3, 9, 27 and 81 word codebook.  A word is encoded reversibly as a
    base-3 address with an explicit level, and is decoded before use.  The V2
    implementation instead composed lossy coordinate LUTs; at depth four those
    LUTs could collapse the coordinate alphabet to two values while the census
    still reported success.  That path is disabled.

    V4 derives a reversible spatial map from the measured gradients.  For each
    PCA channel and P/R/G LUT, values 0..255 are stable-sorted by
    ``(lut[value], value)``.  The permutation advances around that complete
    gradient order by the coprime step P=1, R=3 or G=9.  Every permutation and
    inverse is stored in the GGUF, committed by SHA-256, and every composed
    level-1..4 word must restore the base coordinate exactly.  This makes the
    spatial mapping data-derived and walkable without calling it canon or
    physical geometry.

MEASUREMENT
    Word tensors are un-GC'd one-unit-per-star voxel occupancies.  At each
    depth, the program fails closed unless every owned identity appears exactly
    once in every word, every word round-trips through the base-3 codebook, and
    total star addresses equal population_count * 3**depth.  Four shell-mass
    tensors record which shell levels are occupied and how much addressed
    energy reaches each shell.  Four distinct-source-count tensors prove that
    ties come from at least two source identities, never repeated views of one
    source.  Four pairs of tie/singleton tensors retain both sides of tau=2;
    only the tied partitions are pumped into the measured composite.  Raw-word
    CV and RPR are descriptive and never control
    saturation.  Display smoothing is generated only for the small slice GGUF
    and is explicitly separate.

    Sphericity is measured from the fixed geometric centre (31.5,31.5,31.5).
    Voxel directions are assigned to equal-area Fibonacci bins, not the biased
    26 sign bins.  Each directional mass is divided by the synthetic perfect
    lattice-shell count for the same radius, so grid sampling is calibrated
    away.  A synthetic complete shell is measured and written to the receipt.

OUTPUT
    One full standard GGUF v3 per population.  A fixed 144-byte STARV3 record
    preserves identity SHA, parent-manifest SHA, exact time index, base
    coordinate, owner, shell, name commitment, source signature and token
    count.  The record bytes are stored losslessly as standard GGML I8 bytes,
    alongside a four-axis star tensor, per-star shell levels, the reversible
    word codebook, per-star P/R/G gradients, all 120 raw word tensors, four
    shell-mass tensors, four tie/singleton pairs, and the final tied composite.
    Time, axes, gradients, codebook and temporal ledgers are exact GGML I64.
    Count fields use a streaming uint64 cube and are range-checked into compact
    standard GGML I32 tensors; no count is converted through floating point.
    Tensor dimensions are reversed in the GGUF descriptors as required by
    GGUF.  A small GGUF per population carries exact-centre interpolated raw
    cuts plus display-only smoothing.
    Every GGUF and the HBP receipt receives a SHA-256 sidecar.

BOUNDARIES
    Evidence is LIRIS_LOCAL_MEASURED only after this program is run.  The
    operator mapping ``negative_third=GPT6`` is preserved as operator input,
    but no GPT-6 callable-function manifest is present here, so Sol data is
    never relabelled GPT-6.  Physical gravity and a physical/topological torus
    remain UNVERIFIED.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import BinaryIO, Iterable

import numpy as np


N = 64
CENTRE = 31.5
TAU = 2
SATURATION_EPS = 0.005
LEVELS = (1, 2, 3, 4)
FIBONACCI_DIRECTION_COUNT = 26
MIN_ACTIVE_DIRECTIONS = 4
SHELL_MIN = 2
SHELL_MAX = 30  # complete shells fit inside a 64^3 cube around 31.5
ALIGNMENT = 32
GGML_F32 = 0
GGML_I8 = 24
GGML_I32 = 26
GGML_I64 = 27
GGUF_VERSION = 3
V_UINT32, V_STRING, V_ARRAY = 4, 8, 9
BASE_FLASHLIGHTS = ("P", "R", "G")
FLASHLIGHT_DIGIT = {letter: index for index, letter in enumerate(BASE_FLASHLIGHTS)}
FLASHLIGHT_STEP = {"P": 1, "R": 3, "G": 9}
DESIGN_STATUS = "V4_DESIGN_UNTIL_EXECUTED"
EXECUTED_GEOMETRY_CLASS = "LIRIS_DESIGN_MEASURED"
SPATIAL_FLASHLIGHT_MAPPING = "REVERSIBLE_DATA_DERIVED_GRADIENT_ORDER_V4"
STAR_AXIS_BINDING = (
    "time=manifest_ordinal_u64_exact;"
    "colour=pca0_u8_design;energy=pca1_u8_design;space=pca2_u8_design"
)
STARV3_RECORD_BYTES = 144
STARV3_FLAGS = 0b1101  # design axes, reversible V4 map, embedded bank, GPT6 absent
POPULATIONS = (
    ("SELF", "RED", 0),
    ("ANTI_FABLE", "GREEN", 1),
    ("ANTI_ANTI_MYTHOS", "BLUE", 2),
)


def row(record: str, **fields: object) -> str:
    return "|".join(
        [record, *(f"{key}={value}" for key, value in fields.items()), "json=0"]
    )


def ftext(value: float) -> str:
    return "nan" if not math.isfinite(value) else f"{value:.12f}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 << 20):
            digest.update(block)
    return digest.hexdigest()


def write_sidecar(path: Path, digest: str) -> None:
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="ascii", newline="\n"
    )


def load_function_projector() -> ModuleType:
    """Load the owning PCA/parser without requiring a Python package layout."""

    path = Path(__file__).with_name("see_function_matrix_64.py")
    spec = importlib.util.spec_from_file_location("liris_see_function_matrix_64", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load owning projector: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def quantize_pca_coordinates(coords: np.ndarray) -> np.ndarray:
    """Map the projector's fixed [-0.82,+0.82] PCA radius to byte coordinates."""

    normalized = np.clip(coords / 0.82, -1.0, 1.0)
    return np.rint((normalized + 1.0) * 127.5).astype(np.uint8)


def frozen_owners(coords: np.ndarray) -> np.ndarray:
    """Freeze strict-dominance membership before any flashlight is applied."""

    owners = np.full(len(coords), -1, dtype=np.int8)
    for channel in range(3):
        others = [index for index in range(3) if index != channel]
        mask = (coords[:, channel] > coords[:, others[0]]) & (
            coords[:, channel] > coords[:, others[1]]
        )
        owners[mask] = channel
    return owners


def percentile_lut(values: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(values.astype(np.float64), (0.5, 99.5))
    if hi <= lo:
        return np.zeros(256, dtype=np.uint8)
    scaled = (np.arange(256, dtype=np.float64) - lo) / (hi - lo)
    return np.rint(np.clip(scaled, 0.0, 1.0) * 255.0).astype(np.uint8)


def midrank_lut(values: np.ndarray) -> np.ndarray:
    """Tie-aware empirical mid-CDF over the complete byte alphabet."""

    histogram = np.bincount(values, minlength=256).astype(np.float64)
    total = float(histogram.sum())
    if total <= 0:
        return np.zeros(256, dtype=np.uint8)
    midrank = np.cumsum(histogram) - 0.5 * histogram
    return np.rint(np.clip(midrank / total, 0.0, 1.0) * 255.0).astype(np.uint8)


def glyph_lut(values: np.ndarray) -> np.ndarray:
    """Rank the distinct glyphs; absent values map to their insertion rank."""

    unique = np.unique(values)
    if len(unique) <= 1:
        return np.zeros(256, dtype=np.uint8)
    ranks = np.searchsorted(unique, np.arange(256), side="left")
    ranks = np.clip(ranks, 0, len(unique) - 1)
    return np.rint(ranks / (len(unique) - 1) * 255.0).astype(np.uint8)


def build_luts(coords_u8: np.ndarray) -> dict[tuple[int, str], np.ndarray]:
    constructors = {"P": percentile_lut, "R": midrank_lut, "G": glyph_lut}
    return {
        (channel, letter): constructor(coords_u8[:, channel])
        for channel in range(3)
        for letter, constructor in constructors.items()
    }


def require_closure(condition: bool, detail: str) -> None:
    """Fail closed before a corrupt or identity-dropping GGUF can be sealed."""

    if not condition:
        raise RuntimeError(f"FAIL_CLOSED|detail={detail}|json=0")


def encode_word(word: str) -> int:
    """Encode a fixed-level P/R/G word as an exact base-3 integer."""

    code = 0
    for letter in word:
        require_closure(letter in FLASHLIGHT_DIGIT, f"unknown_flashlight_{letter}")
        code = code * 3 + FLASHLIGHT_DIGIT[letter]
    return code


def decode_word(level: int, code: int) -> str:
    """Inverse of :func:`encode_word`; level is part of the address."""

    require_closure(level >= 1, "word_level_below_one")
    require_closure(0 <= code < 3**level, "word_code_out_of_range")
    digits = ["P"] * level
    remaining = int(code)
    for index in range(level - 1, -1, -1):
        remaining, digit = divmod(remaining, 3)
        digits[index] = BASE_FLASHLIGHTS[digit]
    require_closure(remaining == 0, "word_decode_remainder")
    return "".join(digits)


def word_codebook() -> tuple[np.ndarray, str]:
    """Return exact [level, code, global ordinal] rows and their commitment."""

    rows: list[tuple[int, int, int]] = []
    text_rows: list[str] = []
    ordinal = 0
    for level in LEVELS:
        words = words_at(level)
        require_closure(len(words) == 3**level, f"word_count_level_{level}")
        for word in words:
            code = encode_word(word)
            require_closure(decode_word(level, code) == word, f"word_roundtrip_{word}")
            rows.append((level, code, ordinal))
            text_rows.append(f"{level}|{code}|{ordinal}|{word}\n")
            ordinal += 1
    require_closure(ordinal == 120, "word_codebook_not_120")
    tensor = np.asarray(rows, dtype=np.int64)
    digest = hashlib.sha256("".join(text_rows).encode("ascii")).hexdigest()
    return tensor, digest


def build_spatial_maps(
    luts: dict[tuple[int, str], np.ndarray]
) -> tuple[np.ndarray, np.ndarray, str]:
    """Derive full-cycle P/R/G permutations from each measured gradient order."""

    permutations = np.empty((3, 3, 256), dtype=np.uint8)
    inverses = np.empty_like(permutations)
    alphabet = np.arange(256, dtype=np.uint8)
    for channel in range(3):
        for letter_index, letter in enumerate(BASE_FLASHLIGHTS):
            lut = luts[(channel, letter)]
            order = np.asarray(
                sorted(range(256), key=lambda value: (int(lut[value]), value)),
                dtype=np.uint8,
            )
            require_closure(
                np.array_equal(np.sort(order), alphabet),
                f"gradient_order_not_permutation_{channel}_{letter}",
            )
            step = FLASHLIGHT_STEP[letter]
            require_closure(math.gcd(step, 256) == 1, f"non_coprime_step_{letter}")
            permutation = np.empty(256, dtype=np.uint8)
            permutation[order] = np.roll(order, -step)
            inverse = np.empty(256, dtype=np.uint8)
            inverse[permutation] = alphabet
            require_closure(
                np.array_equal(np.sort(permutation), alphabet),
                f"spatial_map_not_permutation_{channel}_{letter}",
            )
            require_closure(
                np.array_equal(inverse[permutation], alphabet)
                and np.array_equal(permutation[inverse], alphabet),
                f"spatial_map_inverse_{channel}_{letter}",
            )
            # A coprime step on a 256-member order is one complete cycle.
            cursor = 0
            visited: set[int] = set()
            for _ in range(256):
                require_closure(cursor not in visited, f"short_cycle_{channel}_{letter}")
                visited.add(cursor)
                cursor = int(permutation[cursor])
            require_closure(cursor == 0 and len(visited) == 256, f"full_cycle_{channel}_{letter}")
            permutations[channel, letter_index] = permutation
            inverses[channel, letter_index] = inverse
    payload = (
        b"ASOLARIA-SPATIAL-MAP-V4\0"
        + permutations.tobytes()
        + inverses.tobytes()
    )
    return permutations, inverses, hashlib.sha256(payload).hexdigest()


def addressed_coordinates(
    coords_u8: np.ndarray,
    word: str,
    permutations: np.ndarray,
    inverses: np.ndarray,
) -> np.ndarray:
    """Apply one reversible gradient-order permutation per word letter."""

    code = encode_word(word)
    require_closure(decode_word(len(word), code) == word, f"address_roundtrip_{word}")
    addressed = coords_u8.copy()
    for letter in word:
        letter_index = FLASHLIGHT_DIGIT[letter]
        for channel in range(3):
            addressed[:, channel] = permutations[
                channel, letter_index, addressed[:, channel]
            ]
    restored = addressed.copy()
    for letter in reversed(word):
        letter_index = FLASHLIGHT_DIGIT[letter]
        for channel in range(3):
            restored[:, channel] = inverses[
                channel, letter_index, restored[:, channel]
            ]
    require_closure(
        np.array_equal(restored, coords_u8), f"composed_spatial_roundtrip_{word}"
    )
    return addressed


def star_gradients(
    coords_u8: np.ndarray, luts: dict[tuple[int, str], np.ndarray]
) -> np.ndarray:
    """Record P/R/G gradiated views without composing or moving coordinates."""

    columns = []
    for letter in BASE_FLASHLIGHTS:
        for channel in range(3):
            columns.append(luts[(channel, letter)][coords_u8[:, channel]])
    gradients = np.stack(columns, axis=1).astype(np.int64)
    require_closure(np.all((gradients >= 0) & (gradients <= 255)), "gradient_range")
    return gradients


def words_at(level: int) -> list[str]:
    return [
        "".join(letters)
        for letters in itertools.product(BASE_FLASHLIGHTS, repeat=level)
    ]


def validate_manifest_rows(
    path: Path,
    names: list[str],
    token_counts: list[int],
    signatures: list[str],
) -> str:
    """Prove manifest ordinal -> name/signature/token recovery byte-for-byte."""

    recovered: list[tuple[int, str, int, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("FUNCTION|"):
            continue
        fields: dict[str, str] = {}
        for item in line.split("|")[1:]:
            if "=" in item:
                key, value = item.split("=", 1)
                fields[key] = value
        recovered.append(
            (
                int(fields["index"]),
                fields["name"],
                int(fields["tokens"]),
                fields["sig32"],
            )
        )
    require_closure(len(recovered) == len(names), "manifest_function_count")
    for ordinal, (index, name, tokens, signature) in enumerate(recovered):
        require_closure(index == ordinal, f"manifest_index_{ordinal}")
        require_closure(name == names[ordinal], f"manifest_name_{ordinal}")
        require_closure(tokens == token_counts[ordinal], f"manifest_tokens_{ordinal}")
        require_closure(
            signature == signatures[ordinal], f"manifest_signature_{ordinal}"
        )
    canonical = "".join(
        f"{index}|{name}|{tokens}|{signature}\n"
        for index, name, tokens, signature in recovered
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def star_identity_sha(
    manifest_sha: str, index: int, name: str, signature: str
) -> bytes:
    canonical = f"{manifest_sha}|{index}|{name}|{signature}".encode("utf-8")
    return hashlib.sha256(canonical).digest()


def build_starv3_records(
    manifest_sha: str,
    names: list[str],
    token_counts: list[int],
    signatures: list[str],
    coords_u8: np.ndarray,
    owners: np.ndarray,
    geometry: ShellGeometry,
) -> tuple[np.ndarray, str, np.ndarray]:
    """Build and immediately decode-gate fixed 144-byte STARV3 records."""

    parent_sha = bytes.fromhex(manifest_sha)
    require_closure(len(parent_sha) == 32, "parent_sha_not_32")
    positions = (coords_u8 >> 2).astype(np.intp)
    shell_levels = geometry.shell[
        positions[:, 0], positions[:, 1], positions[:, 2]
    ].astype(np.uint32)
    records: list[bytes] = []
    for index, name in enumerate(names):
        signature = signatures[index]
        require_closure(len(signature) == 8, f"sig32_width_{index}")
        require_closure(index <= np.iinfo(np.uint64).max, f"time_u64_{index}")
        require_closure(int(shell_levels[index]) <= np.iinfo(np.uint16).max, f"shell_u16_{index}")
        require_closure(0 <= int(token_counts[index]) <= np.iinfo(np.uint32).max, f"tokens_u32_{index}")
        record = bytearray()
        record.extend(b"ASOSTAR3")
        record.extend(struct.pack("<I", 3))
        record.extend(struct.pack("<Q", index))
        record.extend(struct.pack("<b", int(owners[index])))
        record.extend(bytes(int(value) for value in coords_u8[index]))
        record.extend(struct.pack("<H", int(shell_levels[index])))
        record.extend(struct.pack("<H", STARV3_FLAGS))
        record.extend(struct.pack("<I", int(token_counts[index])))
        identity = star_identity_sha(manifest_sha, index, name, signature)
        record.extend(identity)
        record.extend(parent_sha)
        record.extend(hashlib.sha256(name.encode("utf-8")).digest())
        record.extend(bytes.fromhex(signature))
        record.extend(b"\0" * 12)
        require_closure(len(record) == STARV3_RECORD_BYTES, f"starv3_size_{index}")

        # Decode immediately.  The sealed output is refused if source/name/path
        # recovery through (parent manifest SHA, time index) does not close.
        require_closure(record[:8] == b"ASOSTAR3", f"starv3_magic_{index}")
        require_closure(struct.unpack_from("<I", record, 8)[0] == 3, "starv3_version")
        require_closure(
            struct.unpack_from("<Q", record, 12)[0] == index,
            f"starv3_time_{index}",
        )
        require_closure(
            struct.unpack_from("<b", record, 20)[0] == int(owners[index]),
            f"starv3_owner_{index}",
        )
        require_closure(
            record[21:24] == bytes(int(value) for value in coords_u8[index]),
            f"starv3_coords_{index}",
        )
        require_closure(
            struct.unpack_from("<H", record, 24)[0] == int(shell_levels[index]),
            f"starv3_shell_{index}",
        )
        require_closure(
            struct.unpack_from("<H", record, 26)[0] == STARV3_FLAGS,
            f"starv3_flags_{index}",
        )
        require_closure(
            struct.unpack_from("<I", record, 28)[0] == int(token_counts[index]),
            f"starv3_tokens_{index}",
        )
        require_closure(record[32:64] == identity, f"starv3_identity_{index}")
        require_closure(record[64:96] == parent_sha, f"starv3_parent_{index}")
        require_closure(
            record[96:128] == hashlib.sha256(name.encode("utf-8")).digest(),
            f"starv3_name_{index}",
        )
        require_closure(record[128:132] == bytes.fromhex(signature), f"starv3_sig_{index}")
        require_closure(
            record[132:144] == b"\0" * 12,
            f"starv3_reserved_{index}",
        )
        records.append(bytes(record))

    blob = b"".join(records)
    require_closure(
        len(blob) == len(names) * STARV3_RECORD_BYTES, "starv3_blob_size"
    )
    tensor = np.frombuffer(blob, dtype=np.uint8).copy().reshape(
        len(names), STARV3_RECORD_BYTES
    )
    require_closure(
        tensor.tobytes() == blob,
        "starv3_raw_byte_recovery",
    )
    return tensor, hashlib.sha256(blob).hexdigest(), shell_levels


def embedded_bank_tensors(
    manifest_path: Path, features_i16: np.ndarray
) -> tuple[np.ndarray, str, np.ndarray, str]:
    """Embed the original manifest and exact little-endian 64D i16 source bytes."""

    manifest_blob = manifest_path.read_bytes()
    manifest_tensor = np.frombuffer(manifest_blob, dtype=np.uint8).copy()
    require_closure(manifest_tensor.tobytes() == manifest_blob, "manifest_embed_roundtrip")
    normalized_features = np.ascontiguousarray(features_i16, dtype="<i2")
    require_closure(
        normalized_features.ndim == 2 and normalized_features.shape[1] == 64,
        "feature_bank_shape",
    )
    feature_blob = normalized_features.tobytes()
    feature_tensor = np.frombuffer(feature_blob, dtype=np.uint8).copy().reshape(
        normalized_features.shape[0], 64, 2
    )
    require_closure(feature_tensor.tobytes() == feature_blob, "feature_embed_roundtrip")
    recovered = np.frombuffer(feature_tensor.tobytes(), dtype="<i2").reshape(
        normalized_features.shape
    )
    require_closure(
        np.array_equal(recovered, normalized_features), "feature_i16_roundtrip"
    )
    return (
        manifest_tensor,
        hashlib.sha256(manifest_blob).hexdigest(),
        feature_tensor,
        hashlib.sha256(feature_blob).hexdigest(),
    )


def ordered_temporal_signal(
    features_i16: np.ndarray, coords_u8: np.ndarray
) -> tuple[np.ndarray, str]:
    """Exact DESIGN view ordered by manifest time, never a time-bin census.

    Columns are manifest time index, integer L1 feature energy, and the signed
    colour/energy/space coordinate change from the preceding manifest star.
    The first delta is exactly zero.  This is a derived view, not a canon
    physical time or hue assignment.
    """

    count = len(coords_u8)
    time = np.arange(count, dtype=np.int64)
    energy = np.abs(features_i16.astype(np.int64)).sum(axis=1, dtype=np.int64)
    delta = np.zeros((count, 3), dtype=np.int64)
    if count > 1:
        delta[1:] = coords_u8[1:].astype(np.int64) - coords_u8[:-1].astype(np.int64)
    signal = np.column_stack((time, energy, delta)).astype(np.int64)
    require_closure(
        np.array_equal(signal[:, 0], time), "temporal_manifest_order"
    )
    require_closure(
        int(np.count_nonzero(signal[0, 2:])) == 0 if count else True,
        "temporal_origin_delta",
    )
    blob = np.ascontiguousarray(signal, dtype="<i8").tobytes()
    return signal, hashlib.sha256(blob).hexdigest()


def raw_word_stage(
    transformed_u8: np.ndarray, owners: np.ndarray, population: int
) -> tuple[np.ndarray, int, int]:
    """One un-GC'd unit per owned function for one flashlight word."""

    positions = (transformed_u8[owners == population] >> 2).astype(np.intp)
    stage = np.zeros((N, N, N), dtype=np.uint64)
    if len(positions):
        np.add.at(stage, (positions[:, 0], positions[:, 1], positions[:, 2]), 1.0)
    raw_nonzero = int(np.count_nonzero(stage))
    return stage, len(positions), raw_nonzero


def accumulate_distinct_sources(
    source_sets: dict[int, set[int]],
    addressed_u8: np.ndarray,
    source_ids: np.ndarray,
) -> None:
    """Accumulate source identities per voxel; repeated views add no new tie."""

    positions = (addressed_u8[source_ids] >> 2).astype(np.intp)
    flat = np.ravel_multi_index(
        (positions[:, 0], positions[:, 1], positions[:, 2]), (N, N, N)
    )
    for source_id, voxel in zip(source_ids, flat, strict=True):
        source_sets.setdefault(int(voxel), set()).add(int(source_id))


def distinct_source_cube(source_sets: dict[int, set[int]]) -> np.ndarray:
    cube = np.zeros((N, N, N), dtype=np.uint64)
    flat = cube.ravel()
    for voxel, sources in source_sets.items():
        flat[voxel] = len(sources)
    return cube


@dataclass(frozen=True)
class ShellGeometry:
    shell: np.ndarray
    direction: np.ndarray
    calibration_counts: np.ndarray
    shell_voxels: np.ndarray
    directions: np.ndarray


def fibonacci_directions(count: int) -> np.ndarray:
    index = np.arange(count, dtype=np.float64)
    z = 1.0 - 2.0 * (index + 0.5) / count
    radius = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    angle = index * (math.pi * (3.0 - math.sqrt(5.0)))
    return np.stack((radius * np.cos(angle), radius * np.sin(angle), z), axis=1)


def build_shell_geometry(direction_count: int) -> ShellGeometry:
    grid = np.indices((N, N, N), dtype=np.float64)
    dx = grid[0] - CENTRE
    dy = grid[1] - CENTRE
    dz = grid[2] - CENTRE
    radius = np.sqrt(dx * dx + dy * dy + dz * dz)
    shell = np.floor(radius).astype(np.int16)
    vectors = np.stack((dx.ravel(), dy.ravel(), dz.ravel()), axis=1)
    lengths = np.linalg.norm(vectors, axis=1)
    unit = vectors / np.maximum(lengths[:, None], 1e-15)
    directions = fibonacci_directions(direction_count)
    direction = np.empty(len(unit), dtype=np.int16)
    # Chunking keeps the transient dot-product matrix bounded.
    for start in range(0, len(unit), 32768):
        stop = min(start + 32768, len(unit))
        direction[start:stop] = np.argmax(unit[start:stop] @ directions.T, axis=1)
    direction = direction.reshape((N, N, N))
    calibration_counts = np.zeros(
        (SHELL_MAX + 1, direction_count), dtype=np.float64
    )
    shell_voxels = np.zeros(SHELL_MAX + 1, dtype=np.int64)
    for shell_index in range(SHELL_MIN, SHELL_MAX + 1):
        mask = shell == shell_index
        calibration_counts[shell_index] = np.bincount(
            direction[mask], minlength=direction_count
        )
        shell_voxels[shell_index] = int(np.count_nonzero(mask))
    return ShellGeometry(
        shell=shell,
        direction=direction,
        calibration_counts=calibration_counts,
        shell_voxels=shell_voxels,
        directions=directions,
    )


def sphericity(
    field: np.ndarray, geometry: ShellGeometry
) -> tuple[float, int, list[tuple[int, float, int, float]]]:
    """Calibrated equal-area directional CV, shell by shell.

    The synthetic-shell count in each Fibonacci direction is the denominator.
    Consequently a complete unit-density lattice shell measures CV=0 even when
    its finite voxel counts differ slightly between equal-area directions.
    """

    records: list[tuple[int, float, int, float]] = []
    for shell_index in range(SHELL_MIN, SHELL_MAX + 1):
        shell_mask = geometry.shell == shell_index
        total = float(field[shell_mask].sum())
        if total <= 0:
            continue
        mass = np.bincount(
            geometry.direction[shell_mask],
            weights=field[shell_mask].astype(np.float64),
            minlength=len(geometry.directions),
        )
        expected = geometry.calibration_counts[shell_index]
        valid = expected > 0
        density = np.zeros_like(mass)
        density[valid] = mass[valid] / expected[valid]
        active = int(np.count_nonzero(density[valid] > 0))
        if active < MIN_ACTIVE_DIRECTIONS:
            continue
        values = density[valid]
        mean = float(values.mean())
        if mean <= 0:
            continue
        cv = float(values.std() / mean)
        records.append((shell_index, cv, active, total))
    if not records:
        return float("nan"), 0, []
    return float(np.median([record[1] for record in records])), len(records), records


def perfect_shell_calibration(geometry: ShellGeometry) -> tuple[float, int]:
    perfect = np.zeros((N, N, N), dtype=np.float32)
    mask = (geometry.shell >= SHELL_MIN) & (geometry.shell <= SHELL_MAX)
    perfect[mask] = 1.0
    value, used, _records = sphericity(perfect, geometry)
    return value, used


def ring_measure(field: np.ndarray, geometry: ShellGeometry) -> tuple[int, float, float]:
    profile = np.zeros(SHELL_MAX + 1, dtype=np.float64)
    for shell_index in range(0, SHELL_MAX + 1):
        mask = geometry.shell == shell_index
        count = int(np.count_nonzero(mask))
        if count:
            profile[shell_index] = float(field[mask].sum()) / count
    ring_radius = int(np.argmax(profile[1:])) + 1
    centre_mask = geometry.shell == 0  # the eight voxels surrounding 31.5^3
    centre_value = float(field[centre_mask].mean())
    return ring_radius, centre_value, float(profile[ring_radius])


def gaussian_kernel(sigma: float) -> np.ndarray:
    radius = max(1, int(math.ceil(3.0 * sigma)))
    axis = np.arange(-radius, radius + 1, dtype=np.float64)
    kernel = np.exp(-(axis * axis) / (2.0 * sigma * sigma))
    return kernel / kernel.sum()


def smooth_display(field: np.ndarray, sigma: float) -> np.ndarray:
    """Separable display-only smoothing; never used by the measurement."""

    result = field.astype(np.float64, copy=True)
    kernel = gaussian_kernel(sigma)
    radius = len(kernel) // 2
    for axis in range(3):
        padded = np.pad(
            result,
            [(radius, radius) if item == axis else (0, 0) for item in range(3)],
            mode="constant",
        )
        result = sum(
            weight
            * np.take(
                padded,
                np.arange(N) + offset,
                axis=axis,
            )
            for offset, weight in enumerate(kernel)
        )
    maximum = float(result.max())
    return (result / maximum).astype(np.float32) if maximum else result.astype(np.float32)


def centre_cuts(field: np.ndarray) -> dict[str, np.ndarray]:
    """Interpolate the exact 31.5 centre plane from voxel planes 31 and 32."""

    return {
        "XY": 0.5 * (field[:, :, 31] + field[:, :, 32]),
        "YZ": 0.5 * (field[31, :, :] + field[32, :, :]),
        "ZX": 0.5 * (field[:, 31, :].T + field[:, 32, :].T),
    }


def gguf_string(value: str) -> bytes:
    encoded = value.encode("utf-8")
    return struct.pack("<Q", len(encoded)) + encoded


def gguf_kv(key: str, kind: int, payload: bytes) -> bytes:
    return gguf_string(key) + struct.pack("<I", kind) + payload


def metadata_base(
    name: str,
    manifest_sha: str,
    function_count: int,
    population: str,
    channel: str,
    population_count: int,
    perfect_cv: float,
    direction_count: int,
) -> list[tuple[str, int, bytes]]:
    return [
        ("general.architecture", V_STRING, gguf_string("asolaria-function-pump64")),
        ("general.name", V_STRING, gguf_string(name)),
        ("asolaria.seat", V_STRING, gguf_string("LIRIS")),
        ("asolaria.evidence_class", V_STRING, gguf_string(EXECUTED_GEOMETRY_CLASS)),
        ("asolaria.model_label", V_STRING, gguf_string("gpt-5.6-sol")),
        (
            "asolaria.subject",
            V_STRING,
            gguf_string("runtime_callable_function_surface_not_weights_not_artifacts"),
        ),
        (
            "asolaria.operator_mapping",
            V_STRING,
            gguf_string("negative_third=GPT6"),
        ),
        (
            "asolaria.gpt6_manifest",
            V_STRING,
            gguf_string("ABSENT_DO_NOT_RELABEL_SOL"),
        ),
        ("asolaria.population", V_STRING, gguf_string(population)),
        ("asolaria.channel", V_STRING, gguf_string(channel)),
        ("asolaria.functions", V_UINT32, struct.pack("<I", function_count)),
        (
            "asolaria.population_functions",
            V_UINT32,
            struct.pack("<I", population_count),
        ),
        ("asolaria.cube", V_UINT32, struct.pack("<I", N)),
        ("asolaria.gc_tau", V_UINT32, struct.pack("<I", TAU)),
        (
            "asolaria.saturation_eps",
            V_STRING,
            gguf_string(f"{SATURATION_EPS:.6f}"),
        ),
        (
            "asolaria.flashlights",
            V_STRING,
            gguf_string(
                "P=percentile_gradient;R=midrank_gradient;G=distinct_rank_gradient"
            ),
        ),
        ("asolaria.mechanics_status", V_STRING, gguf_string(DESIGN_STATUS)),
        ("asolaria.star_semantics", V_STRING, gguf_string("gradiated_stars_on_shell_levels")),
        ("asolaria.star_axes", V_STRING, gguf_string(STAR_AXIS_BINDING)),
        (
            "asolaria.star_axis_binding_status",
            V_STRING,
            gguf_string("DESIGN_NOT_CANON"),
        ),
        (
            "asolaria.spatial_flashlight_mapping",
            V_STRING,
            gguf_string(SPATIAL_FLASHLIGHT_MAPPING),
        ),
        (
            "asolaria.identity_address",
            V_STRING,
            gguf_string(
                "embedded_parent_manifest_sha256+u64_manifest_time_index;"
                "no_external_path_dependency"
            ),
        ),
        (
            "asolaria.starv3_record",
            V_STRING,
            gguf_string(
                "fixed_144_bytes;time=u64;xyz=3xu8;stored_as_standard_ggml_i8_raw_bytes"
            ),
        ),
        (
            "asolaria.temporal_signal",
            V_STRING,
            gguf_string(
                "DESIGN_ORDERED_PER_MANIFEST_STAR;time_i64;feature_l1_energy_i64;"
                "signed_colour_energy_space_delta_i64;not_time_bins"
            ),
        ),
        (
            "asolaria.embedded_bank",
            V_STRING,
            gguf_string("original_manifest_bytes+source_64D_i16_le_bytes;roundtrip_gated"),
        ),
        (
            "asolaria.owner_rule",
            V_STRING,
            gguf_string("frozen_base_strict_dominance;ties=free"),
        ),
        (
            "asolaria.measurement_field",
            V_STRING,
            gguf_string(
                "star_identity_ledgers;120_raw_word_occupancies;"
                "4_distinct_source_count;4_level_ties;4_level_singletons;"
                "4_shell_mass;composite_of_ties"
            ),
        ),
        (
            "asolaria.gc_scope",
            V_STRING,
            gguf_string(
                "tie_requires_at_least_2_distinct_source_ids_per_voxel;"
                "repeated_word_views_from_one_source_rejected;"
                "ties_plus_singletons_equals_raw_energy"
            ),
        ),
        (
            "asolaria.tensor_layout",
            V_STRING,
            gguf_string(
                "12_star_bank_map_ledgers_plus_120_raw_words_plus_4_shell_mass_plus_"
                "4_distinct_source_count_plus_4_ties_plus_4_singletons_plus_"
                "1_tied_composite"
            ),
        ),
        (
            "asolaria.exact_tensor_types",
            V_STRING,
            gguf_string(
                "manifest_feature_starv3_permutation_inverse_bytes=GGML_I8;"
                "time_axes_gradients_codebook_temporal=GGML_I64;"
                "count_cubes=range_checked_GGML_I32"
            ),
        ),
        (
            "asolaria.saturation_driver",
            V_STRING,
            gguf_string(
                "function_geometry_diagnostic_only;"
                "never_canon_or_physical_sphere_promotion"
            ),
        ),
        (
            "asolaria.known_defect_v1",
            V_STRING,
            gguf_string("per_word_tau2_emptied_154_function_body_all_cv_nan"),
        ),
        (
            "asolaria.known_defect_v2",
            V_STRING,
            gguf_string(
                "lossy_deep_lut_coordinate_composition_collapsed_alphabet;"
                "vacuous_flat_256_census"
            ),
        ),
        (
            "asolaria.known_defect_v3",
            V_STRING,
            gguf_string(
                "identity_exact_but_missing_spatial_map_caused_distinct_source_ties_zero;"
                "all_composite_cv_nan;receipt_preserved"
            ),
        ),
        (
            "asolaria.centre",
            V_ARRAY,
            struct.pack("<IQ", V_STRING, 3)
            + b"".join(gguf_string("31.5") for _ in range(3)),
        ),
        (
            "asolaria.sphericity",
            V_STRING,
            gguf_string(
                f"fibonacci_equal_area_{direction_count};"
                f"synthetic_shell_cv={ftext(perfect_cv)}"
            ),
        ),
        ("asolaria.manifest_sha256", V_STRING, gguf_string(manifest_sha)),
        ("asolaria.physical_gravity", V_STRING, gguf_string("UNVERIFIED")),
        (
            "asolaria.torus",
            V_STRING,
            gguf_string("UNVERIFIED_REQUIRES_PERSISTENT_BETA1_NOT_RADIAL_HOLE"),
        ),
    ]


@dataclass
class TensorSpec:
    name: str
    shape: tuple[int, ...]
    kind: int
    offset: int


@dataclass
class PopulationRun:
    name: str
    channel: str
    index: int
    function_count: int
    spool: Path
    tensors: list[TensorSpec]
    composite: np.ndarray
    level_rows: list[dict[str, object]]
    stage_rows: list[dict[str, object]]
    raw_best_word: str | None
    raw_best_cv: float
    raw_rpr_cv: float
    best_level: int | None
    best_level_cv: float
    saturated_at: int | None
    composite_cv: float
    composite_shells: int
    ring_radius: int
    centre_value: float
    ring_value: float
    star_record_sha256: str
    four_axis_sha256: str
    gradient_sha256: str
    occupied_shells: tuple[int, ...]
    codebook_sha256: str
    identity_closure: bool
    manifest_bank_sha256: str
    feature_bank_sha256: str
    temporal_signal_sha256: str
    spatial_map_sha256: str


def align_stream(stream: BinaryIO) -> int:
    padding = (-stream.tell()) % ALIGNMENT
    if padding:
        stream.write(b"\0" * padding)
    return stream.tell()


def write_spool_tensor(
    stream: BinaryIO,
    tensors: list[TensorSpec],
    name: str,
    array: np.ndarray,
    kind: int,
) -> None:
    """Append one standard GGUF tensor payload with exact dtype gating."""

    offset = align_stream(stream)
    if kind == GGML_F32:
        normalized = np.ascontiguousarray(array, dtype="<f4")
    elif kind == GGML_I8:
        raw = np.ascontiguousarray(array, dtype=np.uint8)
        normalized = raw.view(np.int8)
        require_closure(
            normalized.view(np.uint8).tobytes() == raw.tobytes(),
            f"i8_raw_byte_roundtrip_{name}",
        )
    elif kind == GGML_I32:
        require_closure(np.all(array >= 0), f"negative_count_tensor_{name}")
        maximum = int(array.max()) if array.size else 0
        require_closure(maximum <= np.iinfo(np.int32).max, f"i32_overflow_{name}")
        normalized = np.ascontiguousarray(array, dtype="<i4")
        require_closure(
            np.array_equal(normalized.astype(np.uint64), array.astype(np.uint64)),
            f"i32_roundtrip_{name}",
        )
    elif kind == GGML_I64:
        minimum = int(array.min()) if array.size else 0
        maximum = int(array.max()) if array.size else 0
        require_closure(minimum >= np.iinfo(np.int64).min, f"i64_underflow_{name}")
        require_closure(maximum <= np.iinfo(np.int64).max, f"i64_overflow_{name}")
        normalized = np.ascontiguousarray(array, dtype="<i8")
        require_closure(
            np.array_equal(normalized, array),
            f"i64_roundtrip_{name}",
        )
    else:
        raise ValueError(f"unsupported tensor kind {kind}: {name}")
    stream.write(normalized.tobytes())
    tensors.append(
        TensorSpec(name=name, shape=normalized.shape, kind=kind, offset=offset)
    )


def pump_population(
    output_dir: Path,
    coords_u8: np.ndarray,
    owners: np.ndarray,
    geometry: ShellGeometry,
    star_records: np.ndarray,
    star_shell_levels: np.ndarray,
    all_gradients: np.ndarray,
    codebook_tensor: np.ndarray,
    codebook_sha256: str,
    spatial_permutations: np.ndarray,
    spatial_inverses: np.ndarray,
    spatial_map_sha256: str,
    manifest_bank: np.ndarray,
    manifest_bank_sha256: str,
    feature_bank: np.ndarray,
    feature_bank_sha256: str,
    temporal_signal: np.ndarray,
    temporal_signal_sha256: str,
    name: str,
    channel: str,
    population: int,
) -> PopulationRun:
    spool = output_dir / f".{name.lower()}.stage-data.tmp"
    tensors: list[TensorSpec] = []
    stage_rows: list[dict[str, object]] = []
    level_rows: list[dict[str, object]] = []
    composite = np.zeros((N, N, N), dtype=np.uint64)
    raw_best_cv = float("inf")
    raw_best_word: str | None = None
    raw_rpr_cv = float("nan")
    best_level_cv = float("inf")
    best_level: int | None = None
    saturated_at: int | None = None

    owned_ids = np.flatnonzero(owners == population).astype(np.int64)
    population_shells = star_shell_levels[owned_ids]
    occupied_shells = tuple(int(value) for value in np.unique(population_shells))
    all_ids = np.arange(len(coords_u8), dtype=np.int64)
    star_axes = np.column_stack(
        (
            all_ids,
            coords_u8[:, 0],
            coords_u8[:, 1],
            coords_u8[:, 2],
        )
    ).astype(np.int64)
    identity_tensor = all_ids.astype(np.int64)
    owned_identity_tensor = owned_ids.astype(np.int64)
    shell_tensor = star_shell_levels.astype(np.int64)
    population_records = star_records
    population_gradients = all_gradients
    require_closure(len(np.unique(owned_ids)) == len(owned_ids), f"identity_unique_{name}")
    require_closure(
        np.array_equal(identity_tensor, all_ids),
        f"identity_i64_exact_{name}",
    )
    require_closure(
        np.array_equal(star_axes[:, 0].astype(np.int64), all_ids),
        f"time_axis_exact_{name}",
    )
    star_record_sha256 = hashlib.sha256(
        population_records.astype(np.uint8).tobytes()
    ).hexdigest()
    four_axis_sha256 = hashlib.sha256(
        np.ascontiguousarray(star_axes, dtype="<i8").tobytes()
    ).hexdigest()
    gradient_sha256 = hashlib.sha256(
        np.ascontiguousarray(population_gradients, dtype="<i8").tobytes()
    ).hexdigest()
    identity_closure = True

    with spool.open("wb") as stream:
        write_spool_tensor(
            stream, tensors, "star_identity_manifest_index_u64_domain", identity_tensor, GGML_I64
        )
        write_spool_tensor(
            stream,
            tensors,
            "population_owned_manifest_index",
            owned_identity_tensor,
            GGML_I64,
        )
        write_spool_tensor(
            stream,
            tensors,
            "star_axes_time_colour_energy_space_design",
            star_axes,
            GGML_I64,
        )
        write_spool_tensor(
            stream, tensors, "star_shell_level", shell_tensor, GGML_I64
        )
        write_spool_tensor(
            stream,
            tensors,
            "starv3_record_bytes_exact_144",
            population_records,
            GGML_I8,
        )
        write_spool_tensor(
            stream,
            tensors,
            "star_gradients_prg_by_projection_channel",
            population_gradients,
            GGML_I64,
        )
        write_spool_tensor(
            stream,
            tensors,
            "flashlight_word_codebook_level_code_ordinal",
            codebook_tensor,
            GGML_I64,
        )
        write_spool_tensor(
            stream,
            tensors,
            "spatial_flashlight_permutation_u8_raw",
            spatial_permutations,
            GGML_I8,
        )
        write_spool_tensor(
            stream,
            tensors,
            "spatial_flashlight_inverse_u8_raw",
            spatial_inverses,
            GGML_I8,
        )
        write_spool_tensor(
            stream,
            tensors,
            "ordered_temporal_signal_time_energy_colour_delta_design",
            temporal_signal,
            GGML_I64,
        )
        write_spool_tensor(
            stream,
            tensors,
            "embedded_original_manifest_bytes",
            manifest_bank,
            GGML_I8,
        )
        write_spool_tensor(
            stream,
            tensors,
            "embedded_source_features_i16_le_bytes",
            feature_bank,
            GGML_I8,
        )
        for level in LEVELS:
            prior_best_level_cv = best_level_cv
            level_raw = np.zeros((N, N, N), dtype=np.uint64)
            level_owned = 0
            identity_hits = np.zeros(len(coords_u8), dtype=np.uint16)
            source_sets: dict[int, set[int]] = {}
            for word in words_at(level):
                code = encode_word(word)
                require_closure(
                    decode_word(level, code) == word,
                    f"word_codebook_population_{name}_{word}",
                )
                transformed = addressed_coordinates(
                    coords_u8, word, spatial_permutations, spatial_inverses
                )
                accumulate_distinct_sources(source_sets, transformed, owned_ids)
                stage, owned, raw_nonzero = raw_word_stage(
                    transformed, owners, population
                )
                require_closure(owned == len(owned_ids), f"owned_count_{name}_{word}")
                require_closure(
                    int(stage.sum(dtype=np.uint64)) == len(owned_ids),
                    f"stage_star_count_{name}_{word}",
                )
                identity_hits[owned_ids] += 1
                raw_cv, raw_shell_count, _shell_rows = sphericity(stage, geometry)
                if word == "RPR":
                    raw_rpr_cv = raw_cv
                if math.isfinite(raw_cv) and raw_cv < raw_best_cv:
                    raw_best_cv = raw_cv
                    raw_best_word = word
                level_raw += stage
                write_spool_tensor(
                    stream,
                    tensors,
                    f"raw_word_l{level}_{word}",
                    stage,
                    GGML_I32,
                )
                stage_rows.append(
                    {
                        "population": name,
                        "level": level,
                        "word": word,
                        "word_code": code,
                        "raw_cv": raw_cv,
                        "raw_shells": raw_shell_count,
                        "owned": owned,
                        "raw_nonzero": raw_nonzero,
                        "mass": float(stage.sum()),
                        "identity_closure": 1,
                    }
                )
                level_owned += owned
            expected_hits = 3**level
            require_closure(
                np.all(identity_hits[owned_ids] == expected_hits),
                f"identity_multiplicity_{name}_level_{level}",
            )
            require_closure(
                int(np.count_nonzero(identity_hits[owners != population])) == 0,
                f"foreign_identity_hit_{name}_level_{level}",
            )
            star_addresses = int(identity_hits.sum(dtype=np.uint64))
            expected_addresses = len(owned_ids) * expected_hits
            require_closure(
                star_addresses == expected_addresses,
                f"star_address_count_{name}_level_{level}",
            )
            require_closure(
                level_owned == expected_addresses,
                f"level_owned_count_{name}_level_{level}",
            )
            require_closure(
                int(level_raw.sum(dtype=np.uint64)) == expected_addresses,
                f"level_energy_count_{name}_level_{level}",
            )
            level_raw_nonzero = int(np.count_nonzero(level_raw))
            distinct_sources = distinct_source_cube(source_sets)
            require_closure(
                int(distinct_sources.max()) <= len(owned_ids) if len(owned_ids) else int(distinct_sources.max()) == 0,
                f"distinct_source_bound_{name}_level_{level}",
            )
            tie_mask = distinct_sources >= TAU
            level_ties = np.where(tie_mask, level_raw, 0).astype(np.uint64)
            level_singletons = level_raw - level_ties
            require_closure(
                np.array_equal(level_ties + level_singletons, level_raw),
                f"gc_partition_{name}_level_{level}",
            )
            level_kept_nonzero = int(np.count_nonzero(level_ties))
            level_singleton_nonzero = int(np.count_nonzero(level_singletons))
            rejected_self_repeat_mask = (level_raw >= TAU) & (distinct_sources < TAU)
            rejected_self_repeat_voxels = int(np.count_nonzero(rejected_self_repeat_mask))
            rejected_self_repeat_mass = int(
                level_raw[rejected_self_repeat_mask].sum(dtype=np.uint64)
            )
            level_cv, level_shells, _ = sphericity(level_ties, geometry)
            if math.isfinite(level_cv) and level_cv < best_level_cv:
                best_level_cv = level_cv
                best_level = level
            composite += level_ties
            max_shell = int(geometry.shell.max())
            shell_mass = np.zeros(max_shell + 1, dtype=np.uint64)
            np.add.at(shell_mass, geometry.shell.ravel(), level_raw.ravel())
            require_closure(
                int(shell_mass.sum(dtype=np.uint64)) == expected_addresses,
                f"shell_energy_count_{name}_level_{level}",
            )
            level_occupied_shells = tuple(
                int(value) for value in np.flatnonzero(shell_mass)
            )
            write_spool_tensor(
                stream,
                tensors,
                f"level_{level}_star_shell_mass",
                shell_mass,
                GGML_I32,
            )
            write_spool_tensor(
                stream,
                tensors,
                f"level_{level}_distinct_source_count",
                distinct_sources,
                GGML_I32,
            )
            write_spool_tensor(
                stream,
                tensors,
                f"level_{level}_distinct_source_ties_tau{TAU}",
                level_ties,
                GGML_I32,
            )
            write_spool_tensor(
                stream,
                tensors,
                f"level_{level}_distinct_sources_lt_tau{TAU}",
                level_singletons,
                GGML_I32,
            )
            composite_cv, composite_shells, _ = sphericity(composite, geometry)
            if math.isfinite(prior_best_level_cv) and math.isfinite(level_cv):
                gain = prior_best_level_cv - min(prior_best_level_cv, level_cv)
            else:
                gain = float("inf")
            if (
                saturated_at is None
                and level >= 2
                and math.isfinite(gain)
                and gain <= SATURATION_EPS
            ):
                saturated_at = level
            level_rows.append(
                {
                    "population": name,
                    "level": level,
                    "words": 3**level,
                    "level_gc_cv": level_cv,
                    "level_gc_shells": level_shells,
                    "best_level_so_far": best_level or 0,
                    "best_level_cv_so_far": best_level_cv,
                    "gain": gain,
                    "composite_cv": composite_cv,
                    "composite_shells": composite_shells,
                    "owned_total": level_owned,
                    "star_addresses": star_addresses,
                    "expected_addresses": expected_addresses,
                    "identity_closure": 1,
                    "occupied_shells": level_occupied_shells,
                    "raw_nonzero_total": level_raw_nonzero,
                    "kept_nonzero_total": level_kept_nonzero,
                    "singleton_nonzero_total": level_singleton_nonzero,
                    "distinct_source_voxels": int(np.count_nonzero(distinct_sources)),
                    "max_distinct_sources": int(distinct_sources.max()),
                    "rejected_self_repeat_voxels": rejected_self_repeat_voxels,
                    "rejected_self_repeat_mass": rejected_self_repeat_mass,
                    "energy_partition_closure": 1,
                    "raw_mass": float(level_raw.sum()),
                    "tie_mass": float(level_ties.sum()),
                    "singleton_mass": float(level_singletons.sum()),
                }
            )

        write_spool_tensor(
            stream,
            tensors,
            "composite_four_level_tied_partitions",
            composite,
            GGML_I32,
        )

    composite_cv, composite_shells, _ = sphericity(composite, geometry)
    ring_radius, centre_value, ring_value = ring_measure(composite, geometry)
    return PopulationRun(
        name=name,
        channel=channel,
        index=population,
        function_count=int(np.count_nonzero(owners == population)),
        spool=spool,
        tensors=tensors,
        composite=composite,
        level_rows=level_rows,
        stage_rows=stage_rows,
        raw_best_word=raw_best_word,
        raw_best_cv=raw_best_cv,
        raw_rpr_cv=raw_rpr_cv,
        best_level=best_level,
        best_level_cv=best_level_cv,
        saturated_at=saturated_at,
        composite_cv=composite_cv,
        composite_shells=composite_shells,
        ring_radius=ring_radius,
        centre_value=centre_value,
        ring_value=ring_value,
        star_record_sha256=star_record_sha256,
        four_axis_sha256=four_axis_sha256,
        gradient_sha256=gradient_sha256,
        occupied_shells=occupied_shells,
        codebook_sha256=codebook_sha256,
        identity_closure=identity_closure,
        manifest_bank_sha256=manifest_bank_sha256,
        feature_bank_sha256=feature_bank_sha256,
        temporal_signal_sha256=temporal_signal_sha256,
        spatial_map_sha256=spatial_map_sha256,
    )


def descriptor(spec: TensorSpec) -> bytes:
    dimensions = tuple(reversed(spec.shape))
    output = bytearray(gguf_string(spec.name))
    output.extend(struct.pack("<I", len(dimensions)))
    for dimension in dimensions:
        output.extend(struct.pack("<Q", int(dimension)))
    output.extend(struct.pack("<I", spec.kind))
    output.extend(struct.pack("<Q", spec.offset))
    return bytes(output)


def write_streamed_gguf(
    path: Path,
    metadata: list[tuple[str, int, bytes]],
    tensors: list[TensorSpec],
    spool: Path,
) -> tuple[int, str]:
    meta = b"".join(gguf_kv(key, kind, payload) for key, kind, payload in metadata)
    descriptions = b"".join(descriptor(spec) for spec in tensors)
    header = struct.pack(
        "<4sIQQ", b"GGUF", GGUF_VERSION, len(tensors), len(metadata)
    )
    header += meta + descriptions
    header += b"\0" * ((-len(header)) % ALIGNMENT)
    digest = hashlib.sha256()
    with path.open("wb") as target:
        target.write(header)
        digest.update(header)
        with spool.open("rb") as source:
            while block := source.read(8 << 20):
                target.write(block)
                digest.update(block)
    hexdigest = digest.hexdigest()
    write_sidecar(path, hexdigest)
    return path.stat().st_size, hexdigest


def write_small_gguf(
    path: Path,
    metadata: list[tuple[str, int, bytes]],
    tensors: Iterable[tuple[str, np.ndarray]],
) -> tuple[int, str]:
    data = bytearray()
    specs: list[TensorSpec] = []
    for name, array in tensors:
        data.extend(b"\0" * ((-len(data)) % ALIGNMENT))
        offset = len(data)
        normalized = np.ascontiguousarray(array, dtype="<f4")
        data.extend(normalized.tobytes())
        specs.append(TensorSpec(name, normalized.shape, GGML_F32, offset))
    meta = b"".join(gguf_kv(key, kind, payload) for key, kind, payload in metadata)
    descriptions = b"".join(descriptor(spec) for spec in specs)
    header = struct.pack(
        "<4sIQQ", b"GGUF", GGUF_VERSION, len(specs), len(metadata)
    )
    header += meta + descriptions
    header += b"\0" * ((-len(header)) % ALIGNMENT)
    blob = header + bytes(data)
    path.write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    write_sidecar(path, digest)
    return len(blob), digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument(
        "--name", default="ASOLARIA-LIRIS-SOL56-FUNCTION-SPHERE-64"
    )
    parser.add_argument("--display-sigma", type=float, default=1.25)
    parser.add_argument(
        "--fibonacci-directions", type=int, default=FIBONACCI_DIRECTION_COUNT
    )
    args = parser.parse_args()
    if args.fibonacci_directions < 8:
        raise ValueError("at least eight equal-area directions are required")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    projector = load_function_projector()
    names, features_i16, token_counts, signatures = projector.parse_function_matrix(
        args.manifest
    )
    coords, _loadings, explained = projector.deterministic_pca(features_i16)
    coords_u8 = quantize_pca_coordinates(coords)
    owners = frozen_owners(coords)
    require_closure(
        len(owners)
        == sum(int(np.count_nonzero(owners == value)) for value in (-1, 0, 1, 2)),
        "owner_partition",
    )
    luts = build_luts(coords_u8)
    all_gradients = star_gradients(coords_u8, luts)
    spatial_permutations, spatial_inverses, spatial_map_sha256 = build_spatial_maps(
        luts
    )
    geometry = build_shell_geometry(args.fibonacci_directions)
    perfect_cv, perfect_shells = perfect_shell_calibration(geometry)
    manifest_sha = sha256_file(args.manifest)
    manifest_recovery_sha = validate_manifest_rows(
        args.manifest, names, token_counts, signatures
    )
    codebook_tensor, codebook_sha256 = word_codebook()
    star_records, starv3_sha256, star_shell_levels = build_starv3_records(
        manifest_sha,
        names,
        token_counts,
        signatures,
        coords_u8,
        owners,
        geometry,
    )
    (
        manifest_bank,
        manifest_bank_sha256,
        feature_bank,
        feature_bank_sha256,
    ) = embedded_bank_tensors(args.manifest, features_i16)
    require_closure(
        manifest_bank_sha256 == manifest_sha,
        "embedded_manifest_sha_matches_parent",
    )
    temporal_signal, temporal_signal_sha256 = ordered_temporal_signal(
        features_i16, coords_u8
    )

    runs: list[PopulationRun] = []
    outputs: list[dict[str, object]] = []
    try:
        for population_name, channel, population_index in POPULATIONS:
            run = pump_population(
                args.output_dir,
                coords_u8,
                owners,
                geometry,
                star_records,
                star_shell_levels,
                all_gradients,
                codebook_tensor,
                codebook_sha256,
                spatial_permutations,
                spatial_inverses,
                spatial_map_sha256,
                manifest_bank,
                manifest_bank_sha256,
                feature_bank,
                feature_bank_sha256,
                temporal_signal,
                temporal_signal_sha256,
                population_name,
                channel,
                population_index,
            )
            require_closure(
                run.star_record_sha256 == starv3_sha256,
                f"starv3_gguf_tensor_recovery_{population_name}",
            )
            require_closure(
                run.codebook_sha256 == codebook_sha256,
                f"codebook_commitment_{population_name}",
            )
            require_closure(
                run.manifest_bank_sha256 == manifest_sha,
                f"manifest_bank_commitment_{population_name}",
            )
            require_closure(
                run.feature_bank_sha256 == feature_bank_sha256,
                f"feature_bank_commitment_{population_name}",
            )
            require_closure(
                run.temporal_signal_sha256 == temporal_signal_sha256,
                f"temporal_signal_commitment_{population_name}",
            )
            require_closure(
                run.spatial_map_sha256 == spatial_map_sha256,
                f"spatial_map_commitment_{population_name}",
            )
            runs.append(run)
            stem = f"{args.name}-{population_name}"
            metadata = metadata_base(
                stem,
                manifest_sha,
                len(names),
                population_name,
                channel,
                run.function_count,
                perfect_cv,
                args.fibonacci_directions,
            )
            metadata.extend(
                [
                    (
                        "asolaria.starv3_sha256",
                        V_STRING,
                        gguf_string(run.star_record_sha256),
                    ),
                    (
                        "asolaria.four_axis_sha256",
                        V_STRING,
                        gguf_string(run.four_axis_sha256),
                    ),
                    (
                        "asolaria.gradient_sha256",
                        V_STRING,
                        gguf_string(run.gradient_sha256),
                    ),
                    (
                        "asolaria.embedded_manifest_sha256",
                        V_STRING,
                        gguf_string(run.manifest_bank_sha256),
                    ),
                    (
                        "asolaria.embedded_feature_i16_sha256",
                        V_STRING,
                        gguf_string(run.feature_bank_sha256),
                    ),
                    (
                        "asolaria.temporal_signal_sha256",
                        V_STRING,
                        gguf_string(run.temporal_signal_sha256),
                    ),
                    (
                        "asolaria.word_codebook_sha256",
                        V_STRING,
                        gguf_string(run.codebook_sha256),
                    ),
                    (
                        "asolaria.spatial_map_sha256",
                        V_STRING,
                        gguf_string(run.spatial_map_sha256),
                    ),
                    (
                        "asolaria.identity_closure",
                        V_UINT32,
                        struct.pack("<I", int(run.identity_closure)),
                    ),
                    (
                        "asolaria.occupied_shell_levels",
                        V_STRING,
                        gguf_string(",".join(str(value) for value in run.occupied_shells)),
                    ),
                    (
                        "asolaria.raw_word_best",
                        V_STRING,
                        gguf_string(run.raw_best_word or "NONE"),
                    ),
                    (
                        "asolaria.raw_word_best_cv",
                        V_STRING,
                        gguf_string(ftext(run.raw_best_cv)),
                    ),
                    (
                        "asolaria.raw_rpr_cv",
                        V_STRING,
                        gguf_string(ftext(run.raw_rpr_cv)),
                    ),
                    (
                        "asolaria.rpr_wins_raw_word_only",
                        V_UINT32,
                        struct.pack("<I", int(run.raw_best_word == "RPR")),
                    ),
                    (
                        "asolaria.best_level",
                        V_UINT32,
                        struct.pack("<I", run.best_level or 0),
                    ),
                    (
                        "asolaria.best_level_gc_cv",
                        V_STRING,
                        gguf_string(ftext(run.best_level_cv)),
                    ),
                    (
                        "asolaria.saturated_at",
                        V_UINT32,
                        struct.pack("<I", run.saturated_at or 0),
                    ),
                    (
                        "asolaria.complete_ladder",
                        V_STRING,
                        gguf_string(
                            "12_star_bank_map_ledgers_plus_120_raw_words_plus_4_shell_mass_"
                            "plus_4_distinct_sources_plus_4_ties_plus_4_singletons_"
                            "plus_composite_written"
                        ),
                    ),
                ]
            )
            full_path = args.output_dir / f"{stem}-FULL.gguf"
            full_bytes, full_sha = write_streamed_gguf(
                full_path, metadata, run.tensors, run.spool
            )

            display = smooth_display(run.composite, args.display_sigma)
            raw_cuts = centre_cuts(run.composite)
            display_cuts = centre_cuts(display)
            slice_path = args.output_dir / f"{stem}-CENTRE-SLICES.gguf"
            slice_tensors: list[tuple[str, np.ndarray]] = []
            for axis in ("XY", "YZ", "ZX"):
                slice_tensors.append((f"raw_{axis}", raw_cuts[axis]))
                slice_tensors.append((f"display_smoothed_{axis}", display_cuts[axis]))
            slice_metadata = metadata + [
                (
                    "asolaria.slice_operator",
                    V_STRING,
                    gguf_string(
                        "linear_interpolation_of_voxel_planes_31_and_32_at_true_31.5"
                    ),
                ),
                (
                    "asolaria.display_smoothing",
                    V_STRING,
                    gguf_string(
                        f"gaussian_sigma={args.display_sigma};display_only_not_measurement"
                    ),
                ),
            ]
            slice_bytes, slice_sha = write_small_gguf(
                slice_path, slice_metadata, slice_tensors
            )
            outputs.append(
                {
                    "population": population_name,
                    "kind": "full",
                    "path": full_path,
                    "bytes": full_bytes,
                    "sha256": full_sha,
                }
            )
            outputs.append(
                {
                    "population": population_name,
                    "kind": "centre_slices",
                    "path": slice_path,
                    "bytes": slice_bytes,
                    "sha256": slice_sha,
                }
            )
    finally:
        for run in runs:
            if run.spool.exists():
                run.spool.unlink()

    receipt_rows = [
        row(
            "PUMPFUN64HDR",
            schema="ASOLARIA-LIRIS-FUNCTION-PUMP-64-V4-REVERSIBLE-SPATIAL",
            class_=EXECUTED_GEOMETRY_CLASS,
            seat="LIRIS",
            model_label="gpt-5.6-sol",
            subject="runtime_callable_function_surface",
            functions=len(names),
            coordinates="deterministic_pca_quantized_0_255",
            cube=N,
            tau=TAU,
            saturation_eps=SATURATION_EPS,
            mechanics_status=DESIGN_STATUS,
        ).replace("class_=", "class="),
        row(
            "AUTHORITY",
            fabric="STALE_FALLBACK_AT_IMPLEMENTATION_TIME",
            measurement="LIRIS_LOCAL_ONLY_AFTER_EXECUTION",
            canon="NOT_UPGRADED_BY_THIS_SCRIPT",
        ),
        row(
            "KNOWN_DEFECT",
            version="V1",
            name="per_word_tau2_emptied_154_function_body",
            observed="all_best_and_composite_cv_nan",
            correction="preserve_raw_words_then_gc_once_per_level",
        ),
        row(
            "KNOWN_DEFECT",
            version="V2",
            name="lossy_deep_lut_coordinate_composition",
            observed="alphabet_collapsed_while_flat_256_census_reported_met",
            correction="reversible_level_plus_base3_word_address_and_immutable_star_identity",
        ),
        row(
            "KNOWN_DEFECT",
            version="V3",
            name="identity_exact_missing_spatial_map",
            observed="distinct_source_ties_zero_all_composite_cv_nan",
            correction="data_derived_full_cycle_gradient_order_permutation_and_inverse",
            prior_receipt="PRESERVED_AS_EVIDENCE",
        ),
        row(
            "INPUT",
            path=args.manifest.as_posix(),
            bytes=args.manifest.stat().st_size,
            sha256=manifest_sha,
            recovery_sha256=manifest_recovery_sha,
            recovery_gate="manifest_sha256_plus_time_index_to_name_sig32_tokens",
            pca_explained_0=f"{explained[0]:.12f}",
            pca_explained_1=f"{explained[1]:.12f}",
            pca_explained_2=f"{explained[2]:.12f}",
        ),
        row(
            "OPERATOR_MAPPING",
            negative_third="GPT6",
            status="OPERATOR_OBSERVED",
            gpt6_manifest="ABSENT",
            sol_relabelled_as_gpt6=0,
        ),
        row(
            "STARV3",
            status=DESIGN_STATUS,
            record_bytes=STARV3_RECORD_BYTES,
            records=len(names),
            bytes=len(names) * STARV3_RECORD_BYTES,
            sha256=starv3_sha256,
            identity="sha256(parent_manifest_sha256|time_index|name|sig32)",
            parent="manifest_sha256",
            time_type="u64",
            xyz_type="3xu8",
            source_recovery="embedded_parent_manifest_sha256+u64_time_index",
            fail_closed=1,
        ),
        row(
            "EMBEDDED_BANK",
            manifest_bytes=len(manifest_bank),
            manifest_sha256=manifest_bank_sha256,
            feature_rows=features_i16.shape[0],
            feature_dimensions=features_i16.shape[1],
            feature_encoding="little_endian_i16_raw_bytes",
            feature_bytes=feature_bank.size,
            feature_sha256=feature_bank_sha256,
            external_path_dependency=0,
            roundtrip_gate=1,
        ),
        row(
            "STAR_AXES",
            semantics="time,colour,energy,space",
            binding=STAR_AXIS_BINDING,
            binding_class="DESIGN",
            star_form="gradiated_colour_in_space_time_energy",
            emergence="occupied_shell_levels_not_flat_alphabet_count",
        ),
        row(
            "TEMPORAL_SIGNAL",
            status="DESIGN_DERIVED_VIEW",
            order="one_row_per_manifest_ordinal_not_count_per_time_bin",
            columns="time_i64,feature_l1_energy_i64,delta_colour_i64,delta_energy_i64,delta_space_i64",
            rows=len(temporal_signal),
            sha256=temporal_signal_sha256,
        ),
        row(
            "WORD_CODEBOOK",
            alphabet="P,R,G",
            encoding="level_plus_base3_code",
            words=120,
            sha256=codebook_sha256,
            roundtrip_gate=1,
            spatial_mapping=SPATIAL_FLASHLIGHT_MAPPING,
        ),
        row(
            "SPATIAL_MAP",
            status="DESIGN_DATA_DERIVED_REVERSIBLE",
            derivation="stable_sort_by_lut_value_then_byte;advance_coprime_steps_P1_R3_G9",
            maps="3_channels_x_3_flashlights_x_256",
            permutation_and_inverse=1,
            sha256=spatial_map_sha256,
            composed_word_roundtrip_levels="1,2,3,4",
        ),
        row(
            "POPULATIONS",
            rule="base_continuous_strict_dominance_frozen_across_all_views",
            self_red=int(np.count_nonzero(owners == 0)),
            anti_fable_green=int(np.count_nonzero(owners == 1)),
            anti_anti_mythos_blue=int(np.count_nonzero(owners == 2)),
            ties_free=int(np.count_nonzero(owners < 0)),
            partition_exact=int(len(owners) == sum(np.count_nonzero(owners == k) for k in (-1, 0, 1, 2))),
        ),
        row(
            "FLASHLIGHTS",
            P="percentile_gradient_view",
            R="tie_aware_midrank_gradient_view",
            G="distinct_rank_gradient_view",
            ladder="3,9,27,81",
            compose="DISABLED_LOSSY_V2",
            address="reversible_level_plus_base3_word",
            spatial_effect=SPATIAL_FLASHLIGHT_MAPPING,
        ),
        row(
            "MEASUREMENT",
            field="120_raw_one_unit_per_star_address_occupancies",
            gc="tau2_distinct_source_ids_per_voxel_repeated_self_views_rejected_ties_plus_singletons_equals_raw",
            pump="four_level_tied_partitions_into_composite",
            tensor_layout="12_star_bank_map_ledgers_plus_120_raw_plus_4_shell_mass_plus_4_distinct_source_plus_4_ties_plus_4_singletons_plus_composite",
            saturation_driver="best_level_wide_calibrated_cv_only",
            promotion_gate="FUNCTION_GEOMETRY_DIAGNOSTIC_ONLY_NOT_CANON_NOT_PHYSICAL",
            centre="31.5,31.5,31.5",
            directions=args.fibonacci_directions,
            direction_operator="equal_area_fibonacci_nearest",
            shell_calibration="synthetic_complete_lattice_shell_direction_density",
            perfect_shell_cv=ftext(perfect_cv),
            perfect_shells=perfect_shells,
            display_smoothing_excluded=1,
            count_cube="streaming_uint64_accumulator_written_as_range_checked_standard_ggml_i32",
            topology="torus_requires_persistent_beta1_radial_hole_is_insufficient",
        ),
    ]
    for run in runs:
        receipt_rows.append(
            row(
                "BEING",
                k=run.name,
                channel=run.channel,
                functions=run.function_count,
                raw_best_word=run.raw_best_word or "NONE",
                raw_best_cv=ftext(run.raw_best_cv),
                raw_rpr_cv=ftext(run.raw_rpr_cv),
                rpr_wins_raw_only=int(run.raw_best_word == "RPR"),
                best_level=run.best_level or 0,
                best_level_gc_cv=ftext(run.best_level_cv),
                saturated_at=run.saturated_at or 0,
                composite_cv=ftext(run.composite_cv),
                composite_shells=run.composite_shells,
                ring_r=run.ring_radius,
                centre_value=f"{run.centre_value:.12f}",
                ring_value=f"{run.ring_value:.12f}",
                identity_closure=int(run.identity_closure),
                starv3_sha256=run.star_record_sha256,
                four_axis_sha256=run.four_axis_sha256,
                gradient_sha256=run.gradient_sha256,
                codebook_sha256=run.codebook_sha256,
                spatial_map_sha256=run.spatial_map_sha256,
                embedded_manifest_sha256=run.manifest_bank_sha256,
                embedded_feature_sha256=run.feature_bank_sha256,
                temporal_signal_sha256=run.temporal_signal_sha256,
                occupied_shells=",".join(str(value) for value in run.occupied_shells),
            )
        )
        for level in run.level_rows:
            receipt_rows.append(
                row(
                    "LEVEL",
                    being=run.name,
                    level=level["level"],
                    words=level["words"],
                    level_gc_cv=ftext(float(level["level_gc_cv"])),
                    level_gc_shells=level["level_gc_shells"],
                    best_level_so_far=level["best_level_so_far"],
                    best_level_cv_so_far=ftext(float(level["best_level_cv_so_far"])),
                    gain=ftext(float(level["gain"])),
                    composite_cv=ftext(float(level["composite_cv"])),
                    composite_shells=level["composite_shells"],
                    star_addresses=level["star_addresses"],
                    expected_addresses=level["expected_addresses"],
                    identity_closure=level["identity_closure"],
                    occupied_shells=",".join(
                        str(value) for value in level["occupied_shells"]
                    ),
                    raw_nonzero_total=level["raw_nonzero_total"],
                    kept_nonzero_total=level["kept_nonzero_total"],
                    singleton_nonzero_total=level["singleton_nonzero_total"],
                    distinct_source_voxels=level["distinct_source_voxels"],
                    max_distinct_sources=level["max_distinct_sources"],
                    rejected_self_repeat_voxels=level["rejected_self_repeat_voxels"],
                    rejected_self_repeat_mass=level["rejected_self_repeat_mass"],
                    energy_partition_closure=level["energy_partition_closure"],
                    raw_mass=f"{float(level['raw_mass']):.6f}",
                    tie_mass=f"{float(level['tie_mass']):.6f}",
                    singleton_mass=f"{float(level['singleton_mass']):.6f}",
                )
            )
        for stage in run.stage_rows:
            receipt_rows.append(
                row(
                    "RAW_WORD",
                    being=run.name,
                    level=stage["level"],
                    word=stage["word"],
                    word_code=stage["word_code"],
                    raw_cv=ftext(float(stage["raw_cv"])),
                    raw_shells=stage["raw_shells"],
                    owned=stage["owned"],
                    raw_nonzero=stage["raw_nonzero"],
                    gc_applied=0,
                    identity_closure=stage["identity_closure"],
                    mass=f"{float(stage['mass']):.6f}",
                )
            )
    for output in outputs:
        receipt_rows.append(
            row(
                "GGUF",
                population=output["population"],
                kind=output["kind"],
                path=Path(output["path"]).as_posix(),
                bytes=output["bytes"],
                sha256=output["sha256"],
            )
        )
    receipt_rows.append(
        row(
            "BOUNDARY",
            physical_gravity="UNVERIFIED",
            physical_or_topological_torus="UNVERIFIED",
            torus_gate="persistent_beta1_required_radial_hole_insufficient",
            sphere="FUNCTION_GEOMETRY_DIAGNOSTIC_ONLY_NOT_CANON_NOT_PHYSICAL",
            gpt6_comparison="PENDING_GPT6_CALLABLE_FUNCTION_MANIFEST",
            spatial_flashlight_mapping=SPATIAL_FLASHLIGHT_MAPPING,
            geometry_class_after_execution=EXECUTED_GEOMETRY_CLASS,
            colour_energy_space_canon_binding="UNVERIFIED_DESIGN_PCA_CHANNEL_BINDING_ONLY",
            source_bank="EMBEDDED_MANIFEST_AND_64D_I16_FEATURE_BYTES",
            model_weights=0,
        )
    )
    body = "\n".join(receipt_rows) + "\n"
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(body, encoding="utf-8", newline="\n")
    receipt_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    write_sidecar(args.receipt, receipt_sha)

    diagnostic_lowest = min(
        runs,
        key=lambda run: (
            run.best_level_cv if math.isfinite(run.best_level_cv) else float("inf")
        ),
    )
    print(
        row(
            "PUMPFUN64",
            class_=EXECUTED_GEOMETRY_CLASS,
            model_label="gpt-5.6-sol",
            diagnostic_lowest_cv_population=diagnostic_lowest.name,
            channel=diagnostic_lowest.channel,
            best_level=diagnostic_lowest.best_level or 0,
            best_level_gc_cv=ftext(diagnostic_lowest.best_level_cv),
            raw_best_word=diagnostic_lowest.raw_best_word or "NONE",
            raw_rpr_cv=ftext(diagnostic_lowest.raw_rpr_cv),
            rpr_wins_raw_only=int(diagnostic_lowest.raw_best_word == "RPR"),
            sphere_promotion="FUNCTION_GEOMETRY_DIAGNOSTIC_ONLY",
            full_ggufs=3,
            slice_ggufs=3,
            tensors_per_full_gguf=len(diagnostic_lowest.tensors),
            receipt_sha256=receipt_sha,
            gpt6_manifest="ABSENT",
            starv3_sha256=starv3_sha256,
            spatial_mapping=SPATIAL_FLASHLIGHT_MAPPING,
        ).replace("class_=", "class=")
    )


if __name__ == "__main__":
    main()
