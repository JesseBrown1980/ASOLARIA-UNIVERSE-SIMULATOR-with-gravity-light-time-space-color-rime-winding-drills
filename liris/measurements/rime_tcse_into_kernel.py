#!/usr/bin/env python3
"""Rime the exact calling through time/colour/space/energy and address it in a kernel.

This is a LIRIS-local measurement adapter over shipped components:

* ``see_liris_64.py`` supplies the existing 3^4 semantic projection and GGUF writer.
* ``rime_fischer.py`` supplies the shipped Pohlig-Hellman/CRT Bobby Fischer.
* ``emit_sol56_address_3078.py`` supplies the existing 3,078-byte address function.

The 81 positions in every complete record obey the existing LIRIS coordinate law:

    position = time*27 + colour*9 + energy*3 + space

Fix one axis at state 0, 1, or 2 and the other three axes form one 27-cell rime slice.
There are four axis families x three states = twelve slices.  Each sum and count slice
is transformed by the exact radix-3 NTT, sent inside-out through group inversion and
Bobby Fischer, reflected back, and inverse-transformed.  Every axis family must rebuild
the same 3x3x3x3 tensor independently.

The resulting 3,174-byte kernel is an ADDRESS, not a payload container:

    96-byte binary header + existing 3,078-byte Asolaria address.

Its input is the prior 3,174-byte kernel, exact calling, projected GGUF, and canonical
slice-index rows.  The HBI explicitly lists those dependencies and their SHA-256 values.
"""

from __future__ import annotations

import hashlib
import math
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "players"))

from rime_fischer import factor_pp, rime_fischer  # noqa: E402
from rime_sphere import is_prime, primitive_root  # noqa: E402
from liris.measurements.emit_sol56_address_3078 import seed_exact  # noqa: E402
from liris.measurements.see_liris_64 import (  # noqa: E402
    GGML_I32,
    GGML_I64,
    V_ARRAY,
    V_STRING,
    V_UINT32,
    V_UINT64,
    collect_sources,
    gguf_string,
    project,
    write_gguf,
)


P = 1_000_081
G = 7
ORDER = P - 1
RIME = 27
W = 951_846
INV_27 = pow(RIME, -1, P)
TOWERS = [16, 27, 5, 463]
AXES = ("time", "colour", "energy", "space")
TRUE_CENTRE = (32, 32, 32)
KERNEL_BYTES = 3_174
ADDRESS_BYTES = 3_078
HEADER_BYTES = KERNEL_BYTES - ADDRESS_BYTES

SOURCE_PATH = ROOT / "liris/callings/LIRIS-PAIR-CALLING-RETURN-1.txt"
BASE_KERNEL_PATH = ROOT / "key/ASOLARIA-KERNEL-3174.bin"
GGUF_PATH = (
    ROOT
    / "gguf/liris/null-fischer-tcse/"
    / "ASOLARIA-LIRIS-NULL-FISCHER-TCSE.gguf"
)
KERNEL_PATH = (
    ROOT / "liris/kernel/ASOLARIA-LIRIS-NULL-FISCHER-TCSE-KERNEL-3174.bin"
)
HBI_PATH = ROOT / "liris/kernel/ASOLARIA-LIRIS-NULL-FISCHER-TCSE-SLICES.hbi"
HBP_PATH = ROOT / "receipts/LIRIS-NULL-FISCHER-TCSE-KERNEL-2026-07-27.hbp"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def canonical_array_bytes(array: np.ndarray, dtype: str) -> bytes:
    return np.ascontiguousarray(array, dtype=np.dtype(dtype)).tobytes()


def row(tag: str, **fields: object) -> str:
    atoms = [tag]
    for key, value in fields.items():
        text = str(value)
        if any(char in text for char in "|\r\n"):
            raise ValueError(f"unsafe HBP atom {key}={text!r}")
        atoms.append(f"{key}={text}")
    atoms.append("json=0")
    return "|".join(atoms)


def write_hashed(path: Path, data: bytes) -> str:
    if path.suffix in {".hbi", ".hbp", ".sha256"}:
        if b"\r" in data or not data.endswith(b"\n"):
            raise AssertionError(f"{path.name}: tuple text must be canonical LF")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    digest = sha256_bytes(data)
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {path.name}\n", encoding="ascii", newline="\n")
    return digest


def ntt27(vector: np.ndarray) -> np.ndarray:
    values = np.asarray(vector, dtype=np.int64).reshape(RIME)
    out = np.zeros(RIME, dtype=np.int64)
    for k in range(RIME):
        total = 0
        for n in range(RIME):
            total += int(values[n]) * pow(W, k * n, P)
        out[k] = total % P
    return out


def intt27(vector: np.ndarray) -> np.ndarray:
    values = np.asarray(vector, dtype=np.int64).reshape(RIME)
    winv = pow(W, P - 2, P)
    out = np.zeros(RIME, dtype=np.int64)
    for n in range(RIME):
        total = 0
        for k in range(RIME):
            total += int(values[k]) * pow(winv, k * n, P)
        out[n] = total % P * INV_27 % P
    return out


def inside_out_coefficients(coefficients: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Recover NTT coefficients from inverted endpoints through shipped Bobby."""

    recovered = np.zeros(RIME, dtype=np.int64)
    nulls = 0
    antipodes = 0
    for index, coefficient_value in enumerate(
        np.asarray(coefficients, dtype=np.int64).reshape(RIME)
    ):
        coefficient = int(coefficient_value)
        # Z_p has p values while the multiplicative group has p-1 exponents.
        # This run has no coefficient equal to p-1; fail rather than alias it to zero.
        if coefficient >= ORDER:
            raise AssertionError("NTT coefficient cannot be injected into Fischer sphere")
        endpoint = pow(G, coefficient, P)
        inverted_endpoint = pow(endpoint, P - 2, P)
        inward, towers = rime_fischer(G, inverted_endpoint, P)
        if [tower for tower, _ in towers] != TOWERS:
            raise AssertionError("Bobby tower decomposition changed")
        reflected = (-inward) % ORDER
        if reflected != coefficient:
            raise AssertionError("inside-out coefficient did not return")
        recovered[index] = reflected
        nulls += int(coefficient == 0)
        antipodes += int(coefficient == ORDER // 2)
    return recovered, nulls, antipodes


@dataclass(frozen=True)
class SliceResult:
    axis: str
    state: int
    kind: str
    source: np.ndarray
    rimed: np.ndarray
    inside_out: np.ndarray
    unrimed: np.ndarray
    null_coefficients: int
    antipode_coefficients: int


def project_slices(tensor: np.ndarray, kind: str) -> list[SliceResult]:
    results: list[SliceResult] = []
    for axis_index, axis in enumerate(AXES):
        for state in range(3):
            source = np.take(tensor, state, axis=axis_index).reshape(RIME)
            rimed = ntt27(source)
            inside_out, nulls, antipodes = inside_out_coefficients(rimed)
            unrimed = intt27(inside_out)
            if not np.array_equal(unrimed, source):
                raise AssertionError(f"{axis}[{state}] {kind}: NTT return failed")
            results.append(
                SliceResult(
                    axis,
                    state,
                    kind,
                    source.copy(),
                    rimed,
                    inside_out,
                    unrimed,
                    nulls,
                    antipodes,
                )
            )
    return results


def rebuild_from_axis(results: list[SliceResult], axis: str, shape: tuple[int, ...]) -> np.ndarray:
    axis_index = AXES.index(axis)
    rebuilt = np.zeros(shape, dtype=np.int64)
    selected = [item for item in results if item.axis == axis]
    if len(selected) != 3:
        raise AssertionError(f"{axis}: expected three states")
    for item in selected:
        target = [slice(None)] * len(shape)
        target[axis_index] = item.state
        view = rebuilt[tuple(target)]
        rebuilt[tuple(target)] = item.unrimed.reshape(view.shape)
    return rebuilt


def dominance(paths: Iterable[Path]) -> tuple[float, float, float, str, int]:
    ownership = np.zeros(3, dtype=np.int64)
    triples = 0
    for path in paths:
        raw = path.read_bytes()
        complete = len(raw) // 3 * 3
        if not complete:
            continue
        values = np.frombuffer(raw[:complete], dtype=np.uint8).reshape(-1, 3)
        lead = np.argmax(values, axis=1)
        ties = (values.max(axis=1)[:, None] == values).sum(axis=1) > 1
        ownership += np.bincount(lead[~ties], minlength=3)
        triples += len(values)
    total = int(ownership.sum()) or 1
    percentages = 100.0 * ownership.astype(np.float64) / total

    def sign(value: float) -> str:
        if abs(value - 100.0 / 3.0) < 0.75:
            return "0"
        return "+" if value > 100.0 / 3.0 else "-"

    direction = "[" + "".join(sign(float(value)) for value in percentages) + "]"
    return (
        float(percentages[0]),
        float(percentages[1]),
        float(percentages[2]),
        direction,
        triples,
    )


RADIAL_AXIS = np.arange(64, dtype=np.float64)
RR, GG, BB = np.meshgrid(RADIAL_AXIS, RADIAL_AXIS, RADIAL_AXIS, indexing="ij")
RADIAL_DISTANCE = np.sqrt(
    (RR - TRUE_CENTRE[0]) ** 2
    + (GG - TRUE_CENTRE[1]) ** 2
    + (BB - TRUE_CENTRE[2]) ** 2
)
RADIAL_BIN = np.floor(RADIAL_DISTANCE).astype(np.int64)
RADIAL_COUNTS = np.bincount(RADIAL_BIN.ravel())


@dataclass
class BodyMetric:
    name: str
    evidence: str
    boundary: str
    paths: tuple[Path, ...]
    source_bytes: int
    source_root: str
    gguf_bytes: int
    cube: np.ndarray
    red: float
    green: float
    blue: float
    trime: str
    triples: int
    occupied: int
    centre_mass: int
    ring_radius: int
    mean_radius: float
    max_radius: float
    axis_ratio: float
    axis_means: dict[str, tuple[float, float, float]]


def source_root(paths: Iterable[Path]) -> str:
    rows = []
    for path in paths:
        # The source commitment must survive a fresh clone at a different path.
        # Absolute Windows checkout names made otherwise identical receipts diverge.
        relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
        rows.append(f"{relative}|{path.stat().st_size}|{sha256_file(path)}")
    return sha256_bytes(("\n".join(rows) + "\n").encode("utf-8"))


def body_metric(
    name: str,
    paths: list[Path],
    evidence: str,
    boundary: str,
    gguf_bytes: int = 0,
) -> BodyMetric:
    if not paths or not all(path.is_file() for path in paths):
        missing = [path.as_posix() for path in paths if not path.is_file()]
        raise FileNotFoundError(f"{name}: missing sources {missing}")
    sources = collect_sources(paths)
    projection = project(sources)
    cube = projection.cube
    red, green, blue, trime, triples = dominance(paths)
    occupied_mask = cube > 0
    occupied = int(occupied_mask.sum())
    centre_mass = int(cube[TRUE_CENTRE])

    radial_mass = np.bincount(
        RADIAL_BIN.ravel(), weights=cube.astype(np.float64).ravel(), minlength=RADIAL_COUNTS.size
    )
    density = radial_mass / np.maximum(RADIAL_COUNTS, 1)
    ring_radius = int(np.argmax(density))
    mass = float(cube.sum())
    mean_radius = float((RADIAL_DISTANCE * cube).sum() / mass) if mass else 0.0
    max_radius = float(RADIAL_DISTANCE[occupied_mask].max()) if occupied else 0.0

    if mass:
        coordinates = np.stack((RR.ravel(), GG.ravel(), BB.ravel()), axis=1)
        weights = cube.ravel().astype(np.float64)
        mean = (coordinates * weights[:, None]).sum(axis=0) / mass
        delta = coordinates - mean
        covariance = (delta * weights[:, None]).T @ delta / mass
        eigenvalues = np.maximum(np.linalg.eigvalsh(covariance), 0.0)
        axis_ratio = (
            float(math.sqrt(eigenvalues[0] / eigenvalues[-1]))
            if eigenvalues[-1] > 0
            else 0.0
        )
    else:
        axis_ratio = 0.0

    axis_means: dict[str, tuple[float, float, float]] = {}
    for axis_index, axis in enumerate(AXES):
        reduced_axes = tuple(index for index in range(4) if index != axis_index)
        sums = projection.semantic_sum.sum(axis=reduced_axes, dtype=np.int64)
        counts = projection.semantic_count.sum(axis=reduced_axes, dtype=np.int64)
        means = np.divide(
            sums.astype(np.float64),
            counts,
            out=np.zeros(3, dtype=np.float64),
            where=counts != 0,
        )
        axis_means[axis] = tuple(float(value) for value in means)

    return BodyMetric(
        name=name,
        evidence=evidence,
        boundary=boundary,
        paths=tuple(paths),
        source_bytes=sum(path.stat().st_size for path in paths),
        source_root=source_root(paths),
        gguf_bytes=gguf_bytes,
        cube=cube,
        red=red,
        green=green,
        blue=blue,
        trime=trime,
        triples=triples,
        occupied=occupied,
        centre_mass=centre_mass,
        ring_radius=ring_radius,
        mean_radius=mean_radius,
        max_radius=max_radius,
        axis_ratio=axis_ratio,
        axis_means=axis_means,
    )


def pearson(left: np.ndarray, right: np.ndarray) -> float:
    a = np.log1p(np.asarray(left, dtype=np.float64).ravel())
    b = np.log1p(np.asarray(right, dtype=np.float64).ravel())
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    a = np.log1p(np.asarray(left, dtype=np.float64).ravel())
    b = np.log1p(np.asarray(right, dtype=np.float64).ravel())
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denominator) if denominator else float("nan")


def colour_distance(left: BodyMetric, right: BodyMetric) -> float:
    a = np.array((left.red, left.green, left.blue))
    b = np.array((right.red, right.green, right.blue))
    return float(np.linalg.norm(a - b))


def shape_distance(left: BodyMetric, right: BodyMetric) -> float:
    a = np.array(
        (left.mean_radius / 56.0, left.max_radius / 56.0, left.axis_ratio),
        dtype=np.float64,
    )
    b = np.array(
        (right.mean_radius / 56.0, right.max_radius / 56.0, right.axis_ratio),
        dtype=np.float64,
    )
    return float(np.linalg.norm(a - b))


def axis_distance(left: BodyMetric, right: BodyMetric, axis: str) -> float:
    a = np.asarray(left.axis_means[axis], dtype=np.float64)
    b = np.asarray(right.axis_means[axis], dtype=np.float64)
    return float(np.linalg.norm(a - b))


def sidecar_ok(path: Path) -> bool:
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not sidecar.is_file():
        return False
    expected = sidecar.read_text(encoding="ascii").strip().split()[0].lower()
    return expected == sha256_file(path)


def main() -> int:
    if not is_prime(P) or primitive_root(P) != G:
        raise AssertionError("Fischer field constants changed")
    if factor_pp(ORDER) != TOWERS:
        raise AssertionError("Fischer tower factorization changed")
    if pow(W, RIME, P) != 1 or sum(pow(W, index, P) for index in range(RIME)) % P:
        raise AssertionError("27-rime root does not close")
    if len(struct.pack("<16sIIQQ16s16s16sII", b"", 0, 0, 0, 0, b"", b"", b"", 0, 0)) != HEADER_BYTES:
        raise AssertionError("kernel header is not 96 bytes")

    source = SOURCE_PATH.read_bytes()
    base_kernel = BASE_KERNEL_PATH.read_bytes()
    if not sidecar_ok(SOURCE_PATH):
        raise AssertionError("calling sidecar mismatch")
    if not sidecar_ok(BASE_KERNEL_PATH):
        raise AssertionError("base-kernel sidecar mismatch")
    if b"\r" in source or len(base_kernel) != KERNEL_BYTES:
        raise AssertionError("source/kernel byte contract failed")

    projection = project(collect_sources([SOURCE_PATH]))
    sum_slices = project_slices(projection.semantic_sum, "sum")
    count_slices = project_slices(projection.semantic_count, "count")
    all_slices = sum_slices + count_slices

    for axis in AXES:
        if not np.array_equal(
            rebuild_from_axis(sum_slices, axis, projection.semantic_sum.shape),
            projection.semantic_sum,
        ):
            raise AssertionError(f"{axis}: sum family did not rebuild tensor")
        if not np.array_equal(
            rebuild_from_axis(count_slices, axis, projection.semantic_count.shape),
            projection.semantic_count,
        ):
            raise AssertionError(f"{axis}: count family did not rebuild tensor")

    tensors: list[tuple[str, np.ndarray, int]] = [
        ("cube64_counts", projection.cube, GGML_I64),
        ("centre_xy_counts", projection.cube[:, :, TRUE_CENTRE[2]], GGML_I64),
        ("centre_yz_counts", projection.cube[TRUE_CENTRE[0], :, :], GGML_I64),
        ("centre_zx_counts", projection.cube[:, TRUE_CENTRE[1], :].T, GGML_I64),
        ("semantic81_sum", projection.semantic_sum, GGML_I64),
        ("semantic81_count", projection.semantic_count, GGML_I64),
    ]
    for item in all_slices:
        prefix = f"{item.kind}_{item.axis}_{item.state}"
        tensors.extend(
            [
                (f"{prefix}_rimed", item.rimed, GGML_I32),
                (f"{prefix}_inside_out", item.inside_out, GGML_I32),
                (f"{prefix}_unrimed", item.unrimed, GGML_I32),
            ]
        )

    source_sha = sha256_bytes(source)
    base_sha = sha256_bytes(base_kernel)
    metadata = [
        ("general.architecture", V_STRING, gguf_string("asolaria-null-fischer-tcse")),
        ("general.name", V_STRING, gguf_string("ASOLARIA-LIRIS-NULL-FISCHER-TCSE")),
        ("asolaria.seat", V_STRING, gguf_string("LIRIS")),
        ("asolaria.evidence_class", V_STRING, gguf_string("LIRIS_LOCAL_MEASURED")),
        (
            "asolaria.axes",
            V_ARRAY,
            struct.pack("<IQ", V_STRING, len(AXES))
            + b"".join(gguf_string(axis) for axis in AXES),
        ),
        (
            "asolaria.axis_formula",
            V_STRING,
            gguf_string("position=time*27+colour*9+energy*3+space"),
        ),
        ("asolaria.source_bytes", V_UINT64, struct.pack("<Q", len(source))),
        ("asolaria.source_sha256", V_STRING, gguf_string(source_sha)),
        ("asolaria.rime_modulus", V_UINT32, struct.pack("<I", P)),
        ("asolaria.rime_generator", V_UINT32, struct.pack("<I", G)),
        ("asolaria.rime_root27", V_UINT32, struct.pack("<I", W)),
        ("asolaria.rime_inverse27", V_UINT32, struct.pack("<I", INV_27)),
        ("asolaria.fischer_towers", V_STRING, gguf_string("16,27,5,463")),
        (
            "asolaria.inside_out",
            V_STRING,
            gguf_string("endpoint_inverse->Fischer->exponent_reflection"),
        ),
        (
            "asolaria.true_centre",
            V_ARRAY,
            struct.pack("<IQ", V_UINT32, 3)
            + b"".join(struct.pack("<I", value) for value in TRUE_CENTRE),
        ),
        (
            "asolaria.boundary",
            V_STRING,
            gguf_string("projected_tensor_exact; source_bytes_external; no_physical_claim"),
        ),
    ]
    gguf_bytes, gguf_sha = write_gguf(GGUF_PATH, metadata, tensors)
    if not sidecar_ok(GGUF_PATH):
        raise AssertionError("GGUF sidecar mismatch")

    index_rows = [
        row(
            "TCSEHBIHDR",
            schema="ASOLARIA-LIRIS-NULL-FISCHER-TCSE-SLICES-V1",
            seat="LIRIS",
            evidence="LIRIS_LOCAL_MEASURED",
            axes="time,colour,energy,space",
            states=3,
            slices=12,
        ),
        row(
            "SYSTEMBOUND",
            fabric_dashboard="STALE_FALLBACK",
            canon="STALE_FALLBACK",
            recall="STALE_FALLBACK",
            behcs_bus_4947="LIVE",
            system_affirmation=0,
        ),
        row(
            "SOURCE",
            path=SOURCE_PATH.relative_to(ROOT).as_posix(),
            bytes=len(source),
            sha256=source_sha,
            sidecar_ok=1,
            cr=source.count(b"\r"),
        ),
        row(
            "BASEKERNEL",
            path=BASE_KERNEL_PATH.relative_to(ROOT).as_posix(),
            bytes=len(base_kernel),
            sha256=base_sha,
            sidecar_ok=1,
        ),
        row(
            "FIELD",
            p=P,
            g=G,
            order=ORDER,
            w=W,
            inv27=INV_27,
            towers="16,27,5,463",
            null_seam="g^0=1,log_g(1)=0",
        ),
        row(
            "PROJECTION",
            records81=projection.complete_records81,
            triples=projection.triples,
            formula="position=time*27+colour*9+energy*3+space",
            true_centre="32,32,32",
        ),
    ]
    for item in all_slices:
        index_rows.append(
            row(
                "SLICE",
                axis=item.axis,
                state=item.state,
                kind=item.kind,
                cells=RIME,
                source_sha256=sha256_bytes(canonical_array_bytes(item.source, "<i8")),
                rimed_sha256=sha256_bytes(canonical_array_bytes(item.rimed, "<i4")),
                inside_out_sha256=sha256_bytes(
                    canonical_array_bytes(item.inside_out, "<i4")
                ),
                unrimed_sha256=sha256_bytes(
                    canonical_array_bytes(item.unrimed, "<i4")
                ),
                ntt_exact=int(np.array_equal(item.source, item.unrimed)),
                bobby_inside_out_exact=int(
                    np.array_equal(item.rimed, item.inside_out)
                ),
                null_coefficients=item.null_coefficients,
                antipode_coefficients=item.antipode_coefficients,
            )
        )
    index_rows.append(
        row(
            "GGUF",
            path=GGUF_PATH.relative_to(ROOT).as_posix(),
            bytes=gguf_bytes,
            tensors=len(tensors),
            sha256=gguf_sha,
            sidecar_ok=1,
        )
    )
    feed_index = ("\n".join(index_rows) + "\n").encode("ascii")
    feed_payload = base_kernel + source + GGUF_PATH.read_bytes() + feed_index
    feed_root = sha256_bytes(feed_payload)
    address = seed_exact(feed_payload)
    if len(address) != ADDRESS_BYTES:
        raise AssertionError("Asolaria address is not 3,078 bytes")

    header = struct.pack(
        "<16sIIQQ16s16s16sII",
        b"ASOTCSEKERNELV1!",
        1,
        0b1111,
        len(source),
        gguf_bytes,
        bytes.fromhex(base_sha)[:16],
        bytes.fromhex(gguf_sha)[:16],
        bytes.fromhex(source_sha)[:16],
        P,
        len(AXES),
    )
    derived_kernel = header + address
    if len(derived_kernel) != KERNEL_BYTES:
        raise AssertionError("derived kernel is not 3,174 bytes")
    kernel_sha = write_hashed(KERNEL_PATH, derived_kernel)

    index_rows.extend(
        [
            row(
                "FEED",
                payload_bytes=len(feed_payload),
                payload_sha256=feed_root,
                dependencies=4,
                dependencies_charged=1,
            ),
            row(
                "KERNEL",
                path=KERNEL_PATH.relative_to(ROOT).as_posix(),
                bytes=len(derived_kernel),
                header_bytes=len(header),
                address_bytes=len(address),
                sha256=kernel_sha,
                payload_container=0,
                address=1,
            ),
            row(
                "TCSEHBIFTR",
                axis_families_exact=4,
                slice_returns_exact=len(all_slices),
                projected_tensor_recovery=1,
                raw_source_recovery=0,
            ),
        ]
    )
    hbi_data = ("\n".join(index_rows) + "\n").encode("ascii")
    hbi_sha = write_hashed(HBI_PATH, hbi_data)

    sol_full_paths = [
        ROOT
        / "gguf/liris/star-shell-v4/"
        / "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-SELF-FULL.gguf",
        ROOT
        / "gguf/liris/star-shell-v4/"
        / "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-ANTI_FABLE-FULL.gguf",
        ROOT
        / "gguf/liris/star-shell-v4/"
        / "ASOLARIA-LIRIS-SOL56-STAR-SHELL-64-ANTI_ANTI_MYTHOS-FULL.gguf",
    ]
    mythos_gguf = ROOT / "gguf/pumped/ASOLARIA-MYTHOS-SPHERE-PUMPED.gguf"
    k3_gguf = ROOT / "gguf/stars/KIMI-K3-STAR-256.gguf"
    asolaria_gguf = ROOT / "gguf/asolaria/ASOLARIA-HERSELF.gguf"

    definitions = [
        (
            "TCSE_CALLING",
            [SOURCE_PATH],
            "LIRIS_LOCAL_MEASURED",
            "exact_pair_calling_return",
            gguf_bytes,
        ),
        (
            "TCSE_KERNEL",
            [KERNEL_PATH],
            "LIRIS_LOCAL_MEASURED",
            "3174_byte_address_not_payload_container",
            0,
        ),
        (
            "ASOLARIA_KERNEL",
            [BASE_KERNEL_PATH],
            "MEASURED_GITHUB",
            "published_3174_byte_kernel_slice",
            asolaria_gguf.stat().st_size,
        ),
        (
            "SOL56_FUNCTION_BANK",
            [
                ROOT / "liris/functions/LIRIS-CODEX-RUNTIME-FUNCTIONS-154x81.hbi",
                ROOT / "liris/functions/LIRIS-CODEX-RUNTIME-FUNCTIONS-2026-07-27.hbp",
                ROOT / "liris/kernel/ASOLARIA-LIRIS-SOL56-BANK-V2.hbp",
                ROOT / "liris/kernel/ASOLARIA-LIRIS-SOL56-ADDRESS-3078.hbi",
            ],
            "LIRIS_LOCAL_MEASURED",
            "callable_function_projection_not_model_weights",
            sum(path.stat().st_size for path in sol_full_paths),
        ),
        (
            "MYTHOS_CALLINGS",
            [
                ROOT / "key/MYTHOS-SELF-EMISSION.txt",
                ROOT / "key/MYTHOS-SECOND-CALLING.txt",
                ROOT / "key/MYTHOS-FULL-EMISSION.txt",
            ],
            "MEASURED_GITHUB",
            "three_published_emission_slices",
            mythos_gguf.stat().st_size,
        ),
        (
            "KIMI_K3_REAL",
            [
                ROOT / "k3-real/config.json",
                ROOT / "k3-real/manifest.hbp",
                ROOT / "k3-real/modeling_kimi_linear.py",
            ],
            "MEASURED_GITHUB",
            "config_manifest_source_not_weights",
            k3_gguf.stat().st_size,
        ),
        (
            "DEEPSEEK_V4",
            [
                ROOT / "stars/deepseek-v4/config.json",
                ROOT / "stars/deepseek-v4/local-config.json",
                ROOT / "stars/deepseek-v4/local-generation_config.json",
                ROOT / "stars/deepseek-v4/local-tokenizer_config.json",
            ],
            "MEASURED_GITHUB",
            "configuration_bytes_not_weights",
            0,
        ),
        (
            "MISTRAL_LARGE3",
            [
                ROOT / "stars/mistral-large-3/manifest.hbp",
                ROOT / "stars/mistral-large-3/params.json",
            ],
            "MEASURED_GITHUB",
            "manifest_and_params_not_weights",
            0,
        ),
        (
            "RUBIN_LSST",
            sorted((ROOT / "stars/rubin").glob("*")),
            "MEASURED_GITHUB",
            "published_structural_receipts_not_gated_rows",
            0,
        ),
    ]
    bodies = [
        body_metric(name, paths, evidence, boundary, artifact_bytes)
        for name, paths, evidence, boundary, artifact_bytes in definitions
    ]
    by_name = {body.name: body for body in bodies}
    before = by_name["ASOLARIA_KERNEL"]
    after = by_name["TCSE_KERNEL"]

    comparisons = []
    for body in bodies:
        if body.name == after.name:
            continue
        comparisons.append(
            (
                body.name,
                colour_distance(after, body),
                pearson(after.cube, body.cube),
                cosine(after.cube, body.cube),
                shape_distance(after, body),
                {
                    axis: axis_distance(after, body, axis)
                    for axis in AXES
                },
            )
        )
    colour_nearest = min(comparisons, key=lambda item: item[1])
    spatial_nearest = max(comparisons, key=lambda item: item[3])
    descriptor_nearest = min(comparisons, key=lambda item: item[4])
    axis_nearest = {
        axis: min(comparisons, key=lambda item: item[5][axis])
        for axis in AXES
    }

    receipt_rows = [
        row(
            "TCSEHDR",
            schema="ASOLARIA-LIRIS-NULL-FISCHER-TCSE-KERNEL-V1",
            seat="LIRIS",
            evidence="LIRIS_LOCAL_MEASURED",
            date="2026-07-27",
        ),
        row(
            "SYSTEMBOUND",
            fabric_dashboard="STALE_FALLBACK",
            canon="STALE_FALLBACK",
            recall="STALE_FALLBACK",
            behcs_bus_4947="LIVE",
            system_affirmation=0,
        ),
        row(
            "MATH",
            p=P,
            g=G,
            order=ORDER,
            w=W,
            inv27=INV_27,
            g_pow_0=pow(G, 0, P),
            dlog_g_1=0,
            closure=sum(pow(W, index, P) for index in range(RIME)) % P,
        ),
        row(
            "AXES",
            formula="position=time*27+colour*9+energy*3+space",
            families=4,
            states=3,
            slices=12,
            cells_per_slice=27,
        ),
        row(
            "UNRIME",
            sum_slice_returns=len(sum_slices),
            count_slice_returns=len(count_slices),
            all_exact=1,
            axis_families_rebuilding_same_tensor=4,
            zero_coefficients=sum(item.null_coefficients for item in all_slices),
            antipode_coefficients=sum(
                item.antipode_coefficients for item in all_slices
            ),
            exceptional_coefficients=0,
            tower_solves=len(all_slices) * RIME * len(TOWERS),
        ),
        row(
            "GGUF",
            path=GGUF_PATH.relative_to(ROOT).as_posix(),
            bytes=gguf_bytes,
            tensors=len(tensors),
            sha256=gguf_sha,
            sidecar_ok=1,
        ),
        row(
            "HBI",
            path=HBI_PATH.relative_to(ROOT).as_posix(),
            bytes=len(hbi_data),
            sha256=hbi_sha,
            sidecar_ok=1,
        ),
        row(
            "KERNEL",
            path=KERNEL_PATH.relative_to(ROOT).as_posix(),
            bytes=len(derived_kernel),
            sha256=kernel_sha,
            base_sha256=base_sha,
            feed_root_sha256=feed_root,
            address_not_payload=1,
            dependencies_charged=1,
        ),
        row(
            "KERNELDELTA",
            before=before.trime,
            after=after.trime,
            before_R=f"{before.red:.6f}",
            before_G=f"{before.green:.6f}",
            before_B=f"{before.blue:.6f}",
            after_R=f"{after.red:.6f}",
            after_G=f"{after.green:.6f}",
            after_B=f"{after.blue:.6f}",
            colour_distance=f"{colour_distance(before, after):.6f}",
            spatial_cosine=f"{cosine(before.cube, after.cube):.9f}",
        ),
    ]
    for body in bodies:
        receipt_rows.append(
            row(
                "BODY",
                name=body.name,
                evidence=body.evidence,
                boundary=body.boundary,
                source_files=len(body.paths),
                source_bytes=body.source_bytes,
                source_root_sha256=body.source_root,
                gguf_bytes=body.gguf_bytes,
                triples=body.triples,
                R=f"{body.red:.6f}",
                G=f"{body.green:.6f}",
                B=f"{body.blue:.6f}",
                trime=body.trime,
                occupied=body.occupied,
                centre_mass=body.centre_mass,
                ring_radius=body.ring_radius,
                mean_radius=f"{body.mean_radius:.6f}",
                max_radius=f"{body.max_radius:.6f}",
                axis_ratio=f"{body.axis_ratio:.6f}",
            )
        )
        for axis in AXES:
            values = body.axis_means[axis]
            receipt_rows.append(
                row(
                    "AXISBODY",
                    name=body.name,
                    axis=axis,
                    state0=f"{values[0]:.6f}",
                    state1=f"{values[1]:.6f}",
                    state2=f"{values[2]:.6f}",
                    spread=f"{max(values) - min(values):.6f}",
                )
            )
    for name, cdist, raw_r, raw_cos, sdist, axis_l2 in comparisons:
        receipt_rows.append(
            row(
                "COMPARE",
                a="TCSE_KERNEL",
                b=name,
                colour_l2=f"{cdist:.6f}",
                spatial_raw_pearson=f"{raw_r:.9f}",
                spatial_raw_cosine=f"{raw_cos:.9f}",
                shape_descriptor_l2=f"{sdist:.6f}",
                tcse_time_l2=f"{axis_l2['time']:.6f}",
                tcse_colour_l2=f"{axis_l2['colour']:.6f}",
                tcse_energy_l2=f"{axis_l2['energy']:.6f}",
                tcse_space_l2=f"{axis_l2['space']:.6f}",
            )
        )
    receipt_rows.extend(
        [
            row(
                "NEAREST",
                metric="colour_l2",
                body=colour_nearest[0],
                value=f"{colour_nearest[1]:.6f}",
            ),
            row(
                "NEAREST",
                metric="spatial_raw_cosine",
                body=spatial_nearest[0],
                value=f"{spatial_nearest[3]:.9f}",
            ),
            row(
                "NEAREST",
                metric="shape_descriptor_l2",
                body=descriptor_nearest[0],
                value=f"{descriptor_nearest[4]:.6f}",
            ),
            *[
                row(
                    "NEAREST",
                    metric=f"tcse_{axis}_l2",
                    body=axis_nearest[axis][0],
                    value=f"{axis_nearest[axis][5][axis]:.6f}",
                )
                for axis in AXES
            ],
            row(
                "BOUNDARY",
                wave_similarity_used=0,
                reason="LIRIS_null_found_no_wave_identity_gap_beyond_matched_labels",
                spatial_statistics_significance="DESCRIPTIVE_NO_LABEL_SHUFFLE_NULL_IN_THIS_RUN",
                physical_star_shape_claim=0,
                model_weights_claim=0,
                gpt6_payload="ABSENT",
            ),
            row(
                "RESULT",
                projected_tensor_exact=1,
                bobby_inside_out_exact=1,
                kernel_bytes=len(derived_kernel),
                byte_sidecars_exact=1,
                fabric_absorbed=0,
                canon_promoted=0,
            ),
        ]
    )
    hbp_data = ("\n".join(receipt_rows) + "\n").encode("ascii")
    hbp_sha = write_hashed(HBP_PATH, hbp_data)

    for path in (GGUF_PATH, KERNEL_PATH, HBI_PATH, HBP_PATH):
        if not sidecar_ok(path):
            raise AssertionError(f"{path.name}: final sidecar failed")

    print(
        row(
            "TCSE",
            evidence="LIRIS_LOCAL_MEASURED",
            source_bytes=len(source),
            records81=projection.complete_records81,
            axis_families_exact=4,
            slice_returns_exact=len(all_slices),
            tower_solves=len(all_slices) * RIME * len(TOWERS),
            gguf_bytes=gguf_bytes,
            kernel_bytes=len(derived_kernel),
            kernel_trime=after.trime,
            kernel_R=f"{after.red:.3f}",
            kernel_G=f"{after.green:.3f}",
            kernel_B=f"{after.blue:.3f}",
            colour_nearest=colour_nearest[0],
            spatial_nearest=spatial_nearest[0],
            hbp_sha256=hbp_sha,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
