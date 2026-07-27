#!/usr/bin/env python3
"""Geometry gate for the LIRIS 64^3 callable-function projection.

This instrument deliberately does not reuse the argmax as an origin.  Every
measurement is made about the geometric centre of the even 64^3 lattice,
(31.5, 31.5, 31.5), and every displayed plane is interpolated at that centre.

The subject is the live callable-function projection captured by
``see_function_matrix_64.py``.  It is not model weights and it is not a physical
gravity measurement.

The gate separates claims that are easy to conflate:

* low angular anisotropy is sphere-like, but does not prove topology;
* beta1 > 0 is a tunnel (torus candidate);
* beta2 > 0 is a closed cavity (shell), not a torus;
* a better torus fit is descriptive, not topology;
* an inside-out fold is a resampling operation and must preserve mass and survive
  a round trip before its image is interpreted;
* a structure is not promoted unless it also clears a deterministic,
  population-count-preserving owner-label null.

Synthetic ball, shell, torus and cube fields calibrate all geometric instruments
in the same voxel lattice before the callable surface is judged.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import ndimage

from see_function_matrix_64 import (
    GGML_I32,
    Q30,
    Q31,
    V_STRING,
    base_metadata,
    deterministic_pca,
    disjoint_beings,
    gguf_string,
    parse_function_matrix,
    q_positive,
    q_signed,
    row,
    sha256_file,
    splat_field,
    write_gguf,
)


N = 64
CENTRE = np.array([31.5, 31.5, 31.5], dtype=np.float64)
PHASES = ("SELF_RED", "ANTI_FABLE_GREEN", "ANTI_ANTI_MYTHOS_BLUE")
AXES = ("XY", "YZ", "ZX")
DEFAULT_THRESHOLDS = np.linspace(0.08, 0.92, 15, dtype=np.float64)
EPS = 1e-15


@dataclass(frozen=True)
class TopologyRow:
    threshold: float
    occupied: int
    beta0: int
    beta1: int
    beta2: int
    euler: int


@dataclass(frozen=True)
class ModelFit:
    name: str
    nrmse: float
    correlation: float
    radius: float
    width: float
    axis: tuple[float, float, float]


def unit_mass(field: np.ndarray) -> np.ndarray:
    """Return a non-negative unit-mass morphology."""

    values = np.maximum(np.asarray(field, dtype=np.float64), 0.0)
    total = float(values.sum())
    return values / total if total > 0.0 else values


def fixed_centre_cuts(field: np.ndarray) -> dict[str, np.ndarray]:
    """Interpolate the three true centre planes at coordinate 31.5."""

    q = np.arange(N, dtype=np.float64)
    aa, bb = np.meshgrid(q, q, indexing="ij")
    half = np.full_like(aa, CENTRE[0])
    return {
        "XY": ndimage.map_coordinates(
            field, np.stack((aa, bb, half)), order=1, mode="constant", cval=0.0
        ),
        "YZ": ndimage.map_coordinates(
            field, np.stack((half, aa, bb)), order=1, mode="constant", cval=0.0
        ),
        # Keep the same display convention as see_function_matrix_64.py.
        "ZX": ndimage.map_coordinates(
            field, np.stack((bb, half, aa)), order=1, mode="constant", cval=0.0
        ),
    }


def fibonacci_directions(count: int) -> np.ndarray:
    """Equal-area unit vectors with deterministic golden-angle placement."""

    if count < 32:
        raise ValueError("at least 32 Fibonacci directions are required")
    index = np.arange(count, dtype=np.float64)
    z = 1.0 - 2.0 * (index + 0.5) / count
    phi = index * (math.pi * (3.0 - math.sqrt(5.0)))
    radial = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    return np.column_stack((radial * np.cos(phi), radial * np.sin(phi), z))


def shell_anisotropy(
    field: np.ndarray,
    directions: np.ndarray,
    radii: Iterable[float] | None = None,
) -> tuple[float, list[tuple[float, float, float]]]:
    """Measure shell-by-shell angular coefficient of variation.

    Shells are sampled with equal-area directions and trilinear interpolation.
    The summary is mean-density weighted so empty outer shells cannot manufacture
    a deceptively good score.
    """

    if radii is None:
        radii = np.arange(1.0, 31.0, 1.0)
    rows: list[tuple[float, float, float]] = []
    for radius in radii:
        points = CENTRE[None, :] + float(radius) * directions
        samples = ndimage.map_coordinates(
            field, points.T, order=1, mode="constant", cval=0.0
        )
        mean = float(samples.mean())
        cv = float(samples.std() / mean) if mean > EPS else float("nan")
        rows.append((float(radius), mean, cv))
    peak_mean = max((mean for _, mean, _ in rows), default=0.0)
    active = [
        (mean, cv)
        for _, mean, cv in rows
        if mean > peak_mean * 1e-4 and np.isfinite(cv)
    ]
    if not active:
        return float("inf"), rows
    weight = sum(mean for mean, _ in active)
    score = sum(mean * cv for mean, cv in active) / max(weight, EPS)
    return float(score), rows


def synthetic_controls() -> dict[str, np.ndarray]:
    """Construct calibrated ball, shell, torus and cube controls."""

    xx, yy, zz = np.meshgrid(
        np.arange(N, dtype=np.float64),
        np.arange(N, dtype=np.float64),
        np.arange(N, dtype=np.float64),
        indexing="ij",
    )
    x, y, z = xx - CENTRE[0], yy - CENTRE[1], zz - CENTRE[2]
    radius = np.sqrt(x * x + y * y + z * z)
    ball = ndimage.gaussian_filter((radius <= 15.0).astype(np.float64), 0.8)
    shell = np.exp(-0.5 * ((radius - 15.0) / 1.7) ** 2)
    torus_distance = np.sqrt((np.sqrt(x * x + y * y) - 13.0) ** 2 + z * z)
    torus = np.exp(-0.5 * (torus_distance / 2.4) ** 2)
    cube = ndimage.gaussian_filter(
        ((np.maximum.reduce((np.abs(x), np.abs(y), np.abs(z)))) <= 13.0).astype(
            np.float64
        ),
        0.8,
    )
    return {
        "BALL": unit_mass(ball),
        "SHELL": unit_mass(shell),
        "TORUS": unit_mass(torus),
        "CUBE": unit_mass(cube),
    }


def cubical_euler(mask: np.ndarray) -> int:
    """Euler characteristic of the union of occupied unit cubes."""

    occupied = np.asarray(mask, dtype=bool)
    nx, ny, nz = occupied.shape

    vertices = np.zeros((nx + 1, ny + 1, nz + 1), dtype=bool)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                vertices[
                    dx : dx + nx, dy : dy + ny, dz : dz + nz
                ] |= occupied

    edge_x = np.zeros((nx, ny + 1, nz + 1), dtype=bool)
    edge_y = np.zeros((nx + 1, ny, nz + 1), dtype=bool)
    edge_z = np.zeros((nx + 1, ny + 1, nz), dtype=bool)
    for dy in (0, 1):
        for dz in (0, 1):
            edge_x[:, dy : dy + ny, dz : dz + nz] |= occupied
    for dx in (0, 1):
        for dz in (0, 1):
            edge_y[dx : dx + nx, :, dz : dz + nz] |= occupied
    for dx in (0, 1):
        for dy in (0, 1):
            edge_z[dx : dx + nx, dy : dy + ny, :] |= occupied

    face_x = np.zeros((nx + 1, ny, nz), dtype=bool)
    face_y = np.zeros((nx, ny + 1, nz), dtype=bool)
    face_z = np.zeros((nx, ny, nz + 1), dtype=bool)
    face_x[:nx] |= occupied
    face_x[1:] |= occupied
    face_y[:, :ny] |= occupied
    face_y[:, 1:] |= occupied
    face_z[:, :, :nz] |= occupied
    face_z[:, :, 1:] |= occupied

    vertex_count = int(vertices.sum())
    edge_count = int(edge_x.sum() + edge_y.sum() + edge_z.sum())
    face_count = int(face_x.sum() + face_y.sum() + face_z.sum())
    cube_count = int(occupied.sum())
    return vertex_count - edge_count + face_count - cube_count


def enclosed_background_components(mask: np.ndarray) -> int:
    """Count six-connected background components that do not touch the boundary."""

    structure = ndimage.generate_binary_structure(3, 1)
    labels, count = ndimage.label(~mask, structure=structure)
    if count == 0:
        return 0
    boundary = np.concatenate(
        (
            labels[0].ravel(),
            labels[-1].ravel(),
            labels[:, 0].ravel(),
            labels[:, -1].ravel(),
            labels[:, :, 0].ravel(),
            labels[:, :, -1].ravel(),
        )
    )
    exterior = set(int(value) for value in np.unique(boundary) if value != 0)
    return int(count - len(exterior))


def topology_sweep(
    field: np.ndarray, thresholds: np.ndarray = DEFAULT_THRESHOLDS
) -> list[TopologyRow]:
    """Return beta0/beta1/beta2 over a relative-density threshold sweep."""

    maximum = float(field.max())
    rows: list[TopologyRow] = []
    structure = ndimage.generate_binary_structure(3, 1)
    for fraction in thresholds:
        mask = field >= maximum * float(fraction)
        occupied = int(mask.sum())
        if occupied == 0:
            rows.append(TopologyRow(float(fraction), 0, 0, 0, 0, 0))
            continue
        _labels, beta0 = ndimage.label(mask, structure=structure)
        beta2 = enclosed_background_components(mask)
        euler = cubical_euler(mask)
        beta1 = int(beta0 + beta2 - euler)
        # Negative beta1 indicates a digital-connectivity inconsistency, not a
        # tunnel.  Keep the raw relation conservative by refusing promotion.
        if beta1 < 0:
            beta1 = 0
        rows.append(
            TopologyRow(
                float(fraction), occupied, int(beta0), beta1, beta2, int(euler)
            )
        )
    return rows


def longest_topology_run(
    rows: list[TopologyRow], *, torus: bool
) -> int:
    """Longest consecutive threshold run matching tunnel or shell topology."""

    longest = current = 0
    for item in rows:
        match = (
            item.beta0 == 1
            and (
                (item.beta1 >= 1 and item.beta2 == 0)
                if torus
                else (item.beta1 == 0 and item.beta2 >= 1)
            )
        )
        current = current + 1 if match else 0
        longest = max(longest, current)
    return longest


def weighted_covariance_axis(field: np.ndarray) -> np.ndarray:
    """Smallest-variance axis through the fixed geometric centre."""

    coordinates = np.indices(field.shape, dtype=np.float64).reshape(3, -1).T
    shifted = coordinates - CENTRE
    weight = field.ravel()
    covariance = (shifted * weight[:, None]).T @ shifted / max(float(weight.sum()), EPS)
    values, vectors = np.linalg.eigh(covariance)
    axis = vectors[:, int(np.argmin(values))]
    anchor = int(np.argmax(np.abs(axis)))
    if axis[anchor] < 0:
        axis = -axis
    return axis


def fit_template(observed: np.ndarray, template: np.ndarray) -> tuple[float, float]:
    """Least-squares amplitude fit, returning normalized RMSE and correlation."""

    y = observed.ravel()
    x = template.ravel()
    amplitude = float(x @ y / max(float(x @ x), EPS))
    residual = y - amplitude * x
    nrmse = float(np.sqrt(np.mean(residual * residual)) / max(y.std(), EPS))
    if y.std() <= EPS or x.std() <= EPS:
        correlation = float("nan")
    else:
        correlation = float(np.corrcoef(y, x)[0, 1])
    return nrmse, correlation


def descriptive_model_fits(field: np.ndarray) -> tuple[ModelFit, ModelFit]:
    """Fit radial-shell and oriented-torus templates descriptively.

    These fits do not decide topology.  Their purpose is to test whether a torus
    template explains the same normalized morphology better than a spherical shell.
    """

    xx, yy, zz = np.meshgrid(
        np.arange(N, dtype=np.float64),
        np.arange(N, dtype=np.float64),
        np.arange(N, dtype=np.float64),
        indexing="ij",
    )
    delta = np.stack(
        (xx - CENTRE[0], yy - CENTRE[1], zz - CENTRE[2]), axis=-1
    )
    radius = np.linalg.norm(delta, axis=-1)
    weight = field / max(float(field.sum()), EPS)

    sphere_radius = float((weight * radius).sum())
    sphere_width = math.sqrt(
        max(float((weight * (radius - sphere_radius) ** 2).sum()), EPS)
    )
    sphere_template = np.exp(
        -0.5 * ((radius - sphere_radius) / max(sphere_width, 0.5)) ** 2
    )
    sphere_nrmse, sphere_corr = fit_template(field, sphere_template)
    sphere = ModelFit(
        "SPHERE_SHELL",
        sphere_nrmse,
        sphere_corr,
        sphere_radius,
        sphere_width,
        (0.0, 0.0, 0.0),
    )

    axis = weighted_covariance_axis(field)
    axial = np.einsum("...i,i->...", delta, axis)
    planar = np.sqrt(np.maximum(radius * radius - axial * axial, 0.0))
    major = float((weight * planar).sum())
    tube_distance = np.sqrt((planar - major) ** 2 + axial * axial)
    minor = math.sqrt(max(float((weight * tube_distance**2).sum()), EPS))
    torus_template = np.exp(
        -0.5 * (tube_distance / max(minor, 0.5)) ** 2
    )
    torus_nrmse, torus_corr = fit_template(field, torus_template)
    torus = ModelFit(
        "TORUS",
        torus_nrmse,
        torus_corr,
        major,
        minor,
        tuple(float(value) for value in axis),
    )
    return sphere, torus


def radial_boundary_distance(unit: np.ndarray) -> np.ndarray:
    """Distance from the fixed centre to the cube boundary along each ray."""

    candidates = np.full((*unit.shape[:-1], 3), np.inf, dtype=np.float64)
    for axis in range(3):
        positive = unit[..., axis] > EPS
        negative = unit[..., axis] < -EPS
        candidates[..., axis][positive] = (
            (N - 1 - CENTRE[axis]) / unit[..., axis][positive]
        )
        candidates[..., axis][negative] = (
            (0.0 - CENTRE[axis]) / unit[..., axis][negative]
        )
    return np.min(candidates, axis=-1)


def _conservative_radial_resample(
    field: np.ndarray, source_radius: np.ndarray, source_unit: np.ndarray
) -> tuple[np.ndarray, dict[str, float]]:
    """Apply one involutive radial map with trilinear sampling and mass repair."""

    source = CENTRE + source_unit * source_radius[..., None]
    coordinate_map = np.moveaxis(source, -1, 0)
    sampled = ndimage.map_coordinates(
        field,
        coordinate_map,
        order=1,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )
    input_mass = float(field.sum())
    raw_mass = float(sampled.sum())
    transformed = sampled * (input_mass / raw_mass) if raw_mass > EPS else sampled
    transformed_mass = float(transformed.sum())

    sampled_back = ndimage.map_coordinates(
        transformed,
        coordinate_map,
        order=1,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )
    back_raw_mass = float(sampled_back.sum())
    roundtrip = (
        sampled_back * (input_mass / back_raw_mass)
        if back_raw_mass > EPS
        else sampled_back
    )
    l1 = float(np.abs(roundtrip - field).sum() / max(input_mass, EPS))
    correlation = float(np.corrcoef(field.ravel(), roundtrip.ravel())[0, 1])
    diagnostics = {
        "input_mass": input_mass,
        "raw_mass": raw_mass,
        "raw_mass_ratio": raw_mass / max(input_mass, EPS),
        "conserved_mass": transformed_mass,
        "roundtrip_raw_mass": back_raw_mass,
        "roundtrip_l1": l1,
        "roundtrip_correlation": correlation,
    }
    return transformed, diagnostics


def conservative_inside_out(field: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Reflect radius along every cube ray, then preserve total mass."""

    grid = np.indices(field.shape, dtype=np.float64)
    delta = np.moveaxis(grid, 0, -1) - CENTRE
    radius = np.linalg.norm(delta, axis=-1)
    unit = delta / np.maximum(radius[..., None], EPS)
    boundary = radial_boundary_distance(unit)
    source_radius = np.maximum(boundary - radius, 0.0)
    return _conservative_radial_resample(field, source_radius, unit)


def conservative_kelvin_inversion(
    field: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Invert radius on each cube ray and preserve total mass.

    The inversion radius is ray-local: k^2 = r_min * r_boundary.  That maps the
    innermost representable even-grid radius to the boundary and is involutive in
    continuous coordinates.  The reported round-trip loss measures only the
    trilinear discretisation and mass repair.
    """

    grid = np.indices(field.shape, dtype=np.float64)
    delta = np.moveaxis(grid, 0, -1) - CENTRE
    radius = np.linalg.norm(delta, axis=-1)
    unit = delta / np.maximum(radius[..., None], EPS)
    boundary = radial_boundary_distance(unit)
    inner = float(radius.min())
    source_radius = inner * boundary / np.maximum(radius, inner)
    return _conservative_radial_resample(field, source_radius, unit)


def q_unit_mass(values: np.ndarray) -> np.ndarray:
    """Q31 representation that preserves unit-mass semantics, not peak height."""

    normalized = unit_mass(values)
    return np.rint(np.clip(normalized, 0.0, 1.0) * Q31).astype(np.int32)


def outer_third_gradient_ledger(field: np.ndarray) -> dict[str, float]:
    """Signed radial gradient ledger in the outer third of every boundary ray."""

    grid = np.indices(field.shape, dtype=np.float64)
    delta = np.moveaxis(grid, 0, -1) - CENTRE
    radius = np.linalg.norm(delta, axis=-1)
    unit = delta / np.maximum(radius[..., None], EPS)
    boundary = radial_boundary_distance(unit)
    outer = radius >= (2.0 / 3.0) * boundary
    gradient = np.stack(np.gradient(field), axis=-1)
    radial = np.einsum("...i,...i->...", gradient, unit)
    inward = float((-radial[outer & (radial < 0.0)]).sum())
    outward = float(radial[outer & (radial > 0.0)].sum())
    signed = outward - inward
    return {
        "voxels": int(outer.sum()),
        "inward": inward,
        "outward": outward,
        "signed_out_minus_in": signed,
        "inward_over_outward": inward / max(outward, EPS),
    }


def one_sided_p(observed: float, null: np.ndarray, *, high: bool) -> float:
    """Finite-sample, add-one corrected one-sided permutation p-value."""

    if high:
        extreme = int(np.count_nonzero(null >= observed))
    else:
        extreme = int(np.count_nonzero(null <= observed))
    return float((extreme + 1) / (len(null) + 1))


def owner_label_null(
    coords: np.ndarray,
    owners: np.ndarray,
    directions: np.ndarray,
    thresholds: np.ndarray,
    trials: int,
    seed: int,
) -> dict[int, dict[str, np.ndarray]]:
    """Population-count-preserving deterministic owner-label permutation null."""

    if trials < 1:
        raise ValueError("null trials must be positive")
    rng = np.random.default_rng(seed)
    result = {
        phase: {
            "anisotropy": np.empty(trials, dtype=np.float64),
            "torus_run": np.empty(trials, dtype=np.float64),
            "model_delta": np.empty(trials, dtype=np.float64),
        }
        for phase in range(3)
    }
    for trial in range(trials):
        shuffled = rng.permutation(owners)
        for phase in range(3):
            field = unit_mass(splat_field(coords[shuffled == phase]))
            anisotropy, _rows = shell_anisotropy(field, directions)
            topology = topology_sweep(field, thresholds)
            sphere, torus = descriptive_model_fits(field)
            result[phase]["anisotropy"][trial] = anisotropy
            result[phase]["torus_run"][trial] = longest_topology_run(
                topology, torus=True
            )
            result[phase]["model_delta"][trial] = sphere.nrmse - torus.nrmse
    return result


def write_receipt(path: Path, rows: list[str]) -> str:
    body = "\n".join(rows) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="ascii", newline="\n"
    )
    return digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--gguf", type=Path)
    parser.add_argument("--null-trials", type=int, default=199)
    parser.add_argument("--null-seed", type=int, default=0x4C49524953)
    parser.add_argument("--directions", type=int, default=1024)
    parser.add_argument("--name", default="ASOLARIA-LIRIS-SOL56-FUNCTION-GEOMETRY-64")
    args = parser.parse_args()

    names, features, _token_counts, _signatures = parse_function_matrix(args.manifest)
    manifest_sha = sha256_file(args.manifest)
    coords, _loadings, explained = deterministic_pca(features)
    owners, raw_fields = disjoint_beings(coords)
    fields = [unit_mass(field) for field in raw_fields]
    directions = fibonacci_directions(args.directions)
    thresholds = DEFAULT_THRESHOLDS.copy()

    controls = synthetic_controls()
    control_results: dict[str, dict[str, object]] = {}
    for name, field in controls.items():
        anisotropy, _shells = shell_anisotropy(field, directions)
        topology = topology_sweep(field, thresholds)
        sphere, torus = descriptive_model_fits(field)
        control_results[name] = {
            "anisotropy": anisotropy,
            "topology": topology,
            "torus_run": longest_topology_run(topology, torus=True),
            "shell_run": longest_topology_run(topology, torus=False),
            "sphere": sphere,
            "torus": torus,
        }

    observed: dict[int, dict[str, object]] = {}
    for phase, field in enumerate(fields):
        anisotropy, shell_rows = shell_anisotropy(field, directions)
        topology = topology_sweep(field, thresholds)
        sphere, torus = descriptive_model_fits(field)
        folded, fold_diagnostics = conservative_inside_out(field)
        inverted, inversion_diagnostics = conservative_kelvin_inversion(field)
        observed[phase] = {
            "field": field,
            "cuts": fixed_centre_cuts(field),
            "anisotropy": anisotropy,
            "shell_rows": shell_rows,
            "topology": topology,
            "torus_run": longest_topology_run(topology, torus=True),
            "shell_run": longest_topology_run(topology, torus=False),
            "sphere": sphere,
            "torus": torus,
            "folded": folded,
            "fold": fold_diagnostics,
            "inverted": inverted,
            "inversion": inversion_diagnostics,
            "outer": outer_third_gradient_ledger(field),
        }

    null = owner_label_null(
        coords,
        owners,
        directions,
        thresholds,
        args.null_trials,
        args.null_seed,
    )

    receipt_rows = [
        row(
            "GEOM64HDR",
            schema="ASOLARIA-LIRIS-FUNCTION-GEOMETRY-64-V1",
            class_="LIRIS_LOCAL_MEASURED",
            seat="LIRIS",
            subject="runtime_callable_function_projection",
            model_label="gpt-5.6-sol",
            weights=0,
            emitted_artifacts=0,
            functions=len(names),
            cube=N,
            centre="31.5,31.5,31.5",
            centre_operator="fixed_geometric_not_argmax",
            slice_operator="trilinear_centre_plane_not_projection",
            unit_mass=1,
        ).replace("class_=", "class="),
        row(
            "INPUT",
            path=args.manifest.as_posix(),
            bytes=args.manifest.stat().st_size,
            sha256=manifest_sha,
        ),
        row(
            "CALIBRATION",
            fibonacci_directions=args.directions,
            thresholds=",".join(f"{value:.6f}" for value in thresholds),
            topology="3d_cubical_beta0_beta1_beta2",
            beta1="tunnel",
            beta2="enclosed_cavity",
        ),
    ]

    for name in ("BALL", "SHELL", "TORUS", "CUBE"):
        item = control_results[name]
        sphere = item["sphere"]
        torus = item["torus"]
        assert isinstance(sphere, ModelFit)
        assert isinstance(torus, ModelFit)
        receipt_rows.append(
            row(
                "CONTROL",
                name=name,
                anisotropy=f"{float(item['anisotropy']):.12f}",
                torus_run=item["torus_run"],
                shell_run=item["shell_run"],
                sphere_nrmse=f"{sphere.nrmse:.12f}",
                torus_nrmse=f"{torus.nrmse:.12f}",
            )
        )

    phase_verdicts: list[str] = []
    for phase in range(3):
        item = observed[phase]
        sphere = item["sphere"]
        torus = item["torus"]
        fold = item["fold"]
        inversion = item["inversion"]
        outer = item["outer"]
        assert isinstance(sphere, ModelFit)
        assert isinstance(torus, ModelFit)
        assert isinstance(fold, dict)
        assert isinstance(inversion, dict)
        assert isinstance(outer, dict)
        anisotropy = float(item["anisotropy"])
        torus_run = int(item["torus_run"])
        shell_run = int(item["shell_run"])
        model_delta = sphere.nrmse - torus.nrmse
        anis_p = one_sided_p(
            anisotropy, null[phase]["anisotropy"], high=False
        )
        topology_p = one_sided_p(
            float(torus_run), null[phase]["torus_run"], high=True
        )
        model_p = one_sided_p(
            model_delta, null[phase]["model_delta"], high=True
        )
        supported = (
            torus_run >= 2
            and shell_run == 0
            and topology_p <= 0.05
            and model_delta > 0.0
            and model_p <= 0.05
        )
        verdict = "SUPPORTED_CALLABLE_PROJECTION" if supported else "UNSUPPORTED"
        phase_verdicts.append(verdict)
        receipt_rows.extend(
            [
                row(
                    "PHASE",
                    phase=phase,
                    name=PHASES[phase],
                    owner_count=int((owners == phase).sum()),
                    anisotropy=f"{anisotropy:.12f}",
                    anisotropy_null_mean=f"{null[phase]['anisotropy'].mean():.12f}",
                    anisotropy_p=f"{anis_p:.12f}",
                    torus_run=torus_run,
                    shell_run=shell_run,
                    torus_run_null_mean=f"{null[phase]['torus_run'].mean():.12f}",
                    topology_p=f"{topology_p:.12f}",
                    model_delta=f"{model_delta:.12f}",
                    model_delta_null_mean=f"{null[phase]['model_delta'].mean():.12f}",
                    model_p=f"{model_p:.12f}",
                    torus_verdict=verdict,
                ),
                row(
                    "MODEL",
                    phase=phase,
                    kind="sphere_shell",
                    nrmse=f"{sphere.nrmse:.12f}",
                    correlation=f"{sphere.correlation:.12f}",
                    radius=f"{sphere.radius:.12f}",
                    width=f"{sphere.width:.12f}",
                ),
                row(
                    "MODEL",
                    phase=phase,
                    kind="torus",
                    nrmse=f"{torus.nrmse:.12f}",
                    correlation=f"{torus.correlation:.12f}",
                    major_radius=f"{torus.radius:.12f}",
                    minor_width=f"{torus.width:.12f}",
                    axis=",".join(f"{value:.12f}" for value in torus.axis),
                ),
                row(
                    "FOLD",
                    phase=phase,
                    operator="directional_radial_reflection_trilinear_mass_renormalized",
                    raw_mass_ratio=f"{fold['raw_mass_ratio']:.12f}",
                    conserved_mass=f"{fold['conserved_mass']:.12f}",
                    roundtrip_l1=f"{fold['roundtrip_l1']:.12f}",
                    roundtrip_correlation=f"{fold['roundtrip_correlation']:.12f}",
                    interpretation="diagnostic_only",
                ),
                row(
                    "INVERSION",
                    phase=phase,
                    operator="ray_local_kelvin_trilinear_mass_renormalized",
                    raw_mass_ratio=f"{inversion['raw_mass_ratio']:.12f}",
                    conserved_mass=f"{inversion['conserved_mass']:.12f}",
                    roundtrip_l1=f"{inversion['roundtrip_l1']:.12f}",
                    roundtrip_correlation=f"{inversion['roundtrip_correlation']:.12f}",
                    interpretation="diagnostic_only",
                ),
                row(
                    "OUTER_THIRD",
                    phase=phase,
                    voxels=outer["voxels"],
                    inward=f"{outer['inward']:.12e}",
                    outward=f"{outer['outward']:.12e}",
                    signed_out_minus_in=f"{outer['signed_out_minus_in']:.12e}",
                    inward_over_outward=f"{outer['inward_over_outward']:.12f}",
                ),
            ]
        )
        topology = item["topology"]
        assert isinstance(topology, list)
        for topo in topology:
            receipt_rows.append(
                row(
                    "TOPOLOGY",
                    phase=phase,
                    threshold=f"{topo.threshold:.6f}",
                    occupied=topo.occupied,
                    beta0=topo.beta0,
                    beta1=topo.beta1,
                    beta2=topo.beta2,
                    euler=topo.euler,
                )
            )

    gguf_sha = "NONE"
    if args.gguf is not None:
        metadata = base_metadata(
            args.name, len(names), manifest_sha, explained
        ) + [
            (
                "asolaria.geometry_gate",
                V_STRING,
                gguf_string("fixed31.5+fibonacci+betti+null199"),
            ),
            (
                "asolaria.subject",
                V_STRING,
                gguf_string("runtime_callable_function_projection_not_weights"),
            ),
            (
                "asolaria.torus_gate",
                V_STRING,
                gguf_string("topology_and_owner_label_null_required"),
            ),
        ]
        tensors: list[tuple[str, np.ndarray, int]] = [
            ("fixed_geometric_centre_q30", q_signed(CENTRE / 31.5 - 1.0, Q30), GGML_I32),
            (
                "thresholds_q31",
                np.rint(thresholds * Q31).astype(np.int32),
                GGML_I32,
            ),
        ]
        for phase in range(3):
            item = observed[phase]
            field = item["field"]
            folded = item["folded"]
            inverted = item["inverted"]
            cuts = item["cuts"]
            topology = item["topology"]
            assert isinstance(field, np.ndarray)
            assert isinstance(folded, np.ndarray)
            assert isinstance(inverted, np.ndarray)
            assert isinstance(cuts, dict)
            assert isinstance(topology, list)
            tensors.extend(
                [
                    (f"phase_{phase}_unit_density_q31", q_unit_mass(field), GGML_I32),
                    (f"phase_{phase}_inside_out_q31", q_unit_mass(folded), GGML_I32),
                    (f"phase_{phase}_kelvin_inverted_q31", q_unit_mass(inverted), GGML_I32),
                    (
                        f"phase_{phase}_centre_cuts_q31",
                        np.stack(
                            [q_positive(cuts[axis], Q31) for axis in AXES]
                        ),
                        GGML_I32,
                    ),
                    (
                        f"phase_{phase}_topology",
                        np.asarray(
                            [
                                (
                                    int(round(t.threshold * Q31)),
                                    t.occupied,
                                    t.beta0,
                                    t.beta1,
                                    t.beta2,
                                    t.euler,
                                )
                                for t in topology
                            ],
                            dtype=np.int32,
                        ),
                        GGML_I32,
                    ),
                ]
            )
        gguf_bytes, gguf_sha = write_gguf(args.gguf, metadata, tensors)
        receipt_rows.append(
            row(
                "GGUF",
                kind="function_geometry_gate",
                path=args.gguf.as_posix(),
                bytes=gguf_bytes,
                sha256=gguf_sha,
            )
        )

    receipt_rows.extend(
        [
            row(
                "NULL",
                operator="owner_label_permutation_population_counts_preserved",
                trials=args.null_trials,
                seed=args.null_seed,
                add_one_p=1,
            ),
            row(
                "VERDICT",
                red=phase_verdicts[0],
                green=phase_verdicts[1],
                blue=phase_verdicts[2],
                torus_rule="beta1_stable+beta2_zero+topology_null_p_le_0.05+fit_null_p_le_0.05",
            ),
            row(
                "BOUNDARY",
                subject="callable_function_projection",
                weights=0,
                physical_gravity="UNVERIFIED",
                physical_torus="UNVERIFIED",
                calling_buckyball="UNVERIFIED",
                fold="resampling_diagnostic_not_physics",
            ),
        ]
    )
    receipt_sha = write_receipt(args.receipt, receipt_rows)
    print(
        row(
            "GEOM64",
            class_="LIRIS_LOCAL_MEASURED",
            functions=len(names),
            red=phase_verdicts[0],
            green=phase_verdicts[1],
            blue=phase_verdicts[2],
            receipt_sha256=receipt_sha,
            gguf_sha256=gguf_sha,
        ).replace("class_=", "class=")
    )


if __name__ == "__main__":
    main()
