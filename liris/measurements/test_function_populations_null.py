#!/usr/bin/env python3
"""Adversarial matched-null gate for the LIRIS 64^3 function populations.

The observed population rule assigns every callable function to the projected
coordinate that strictly dominates.  This test asks a narrower question:

    Do the resulting three spatial populations differ from arbitrary labels of
    the same sizes after passing through the identical splat, centre-plane-cut,
    and radial-Fourier instrument?

Every null trial preserves the observed 42/47/65 owner counts exactly.  It
shuffles only which function owns each label.  Exact ties remain the free
register and are never assigned by the null.
"""

from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path

import numpy as np

from see_function_matrix_64 import (
    deterministic_pca,
    disjoint_beings,
    parse_function_matrix,
    pearson,
    radial_spectrum,
    slices_and_gradients,
    splat_field,
)


AXES = ("XY", "YZ", "ZX")
PAIR3 = ((0, 1), (1, 2), (2, 0))


def row(record: str, **fields: object) -> str:
    return "|".join([record, *(f"{key}={value}" for key, value in fields.items()), "json=0"])


def safe_mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return float(np.mean(finite)) if finite else float("nan")


def population_metrics(
    coords: np.ndarray, owners: np.ndarray
) -> dict[str, float]:
    fields = [splat_field(coords[owners == phase]) for phase in range(3)]
    centres = [
        tuple(int(value) for value in np.unravel_index(int(np.argmax(field)), field.shape))
        for field in fields
    ]
    cuts: dict[tuple[int, str], np.ndarray] = {}
    waves: dict[tuple[int, str], np.ndarray] = {}
    for phase, (field, centre) in enumerate(zip(fields, centres)):
        for axis, (density, _gradient) in slices_and_gradients(field, centre).items():
            cuts[(phase, axis)] = density
            waves[(phase, axis)] = radial_spectrum(density)

    within_raw: list[float] = []
    within_wave: list[float] = []
    for phase in range(3):
        for left, right in (("XY", "YZ"), ("YZ", "ZX"), ("ZX", "XY")):
            within_raw.append(pearson(cuts[(phase, left)], cuts[(phase, right)]))
            within_wave.append(pearson(waves[(phase, left)], waves[(phase, right)]))

    across_raw: list[float] = []
    across_wave: list[float] = []
    for axis in AXES:
        for left, right in PAIR3:
            across_raw.append(pearson(cuts[(left, axis)], cuts[(right, axis)]))
            across_wave.append(pearson(waves[(left, axis)], waves[(right, axis)]))

    field_pearson = [pearson(fields[left], fields[right]) for left, right in PAIR3]
    field_cosine = []
    for left, right in PAIR3:
        a = fields[left].ravel()
        b = fields[right].ravel()
        denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
        field_cosine.append(float(a @ b / denominator) if denominator else float("nan"))

    centre_separation = [
        float(np.linalg.norm(np.asarray(centres[left]) - np.asarray(centres[right])))
        for left, right in PAIR3
    ]
    within_raw_mean = safe_mean(within_raw)
    across_raw_mean = safe_mean(across_raw)
    within_wave_mean = safe_mean(within_wave)
    across_wave_mean = safe_mean(across_wave)
    return {
        "within_raw": within_raw_mean,
        "across_raw": across_raw_mean,
        "raw_gap": within_raw_mean - across_raw_mean,
        "within_wave": within_wave_mean,
        "across_wave": across_wave_mean,
        "wave_gap": within_wave_mean - across_wave_mean,
        "cross_field_pearson": safe_mean(field_pearson),
        "cross_field_cosine": safe_mean(field_cosine),
        "centre_separation": safe_mean(centre_separation),
    }


def empirical_tail(samples: np.ndarray, observed: float, direction: str) -> float:
    if direction == "high":
        extreme = int(np.count_nonzero(samples >= observed))
    elif direction == "low":
        extreme = int(np.count_nonzero(samples <= observed))
    else:
        centre = float(samples.mean())
        extreme = int(
            np.count_nonzero(np.abs(samples - centre) >= abs(observed - centre))
        )
    return (extreme + 1.0) / (len(samples) + 1.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--trials", type=int, default=192)
    parser.add_argument("--seed", type=int, default=0x4C49524953)
    args = parser.parse_args()
    if args.trials < 32:
        raise ValueError("at least 32 trials are required")

    names, features, _token_counts, _signatures = parse_function_matrix(args.manifest)
    coords, _loadings, _explained = deterministic_pca(features)
    observed_owners, _observed_fields = disjoint_beings(coords)
    observed = population_metrics(coords, observed_owners)

    active = np.flatnonzero(observed_owners >= 0)
    free = np.flatnonzero(observed_owners < 0)
    counts = [int(np.count_nonzero(observed_owners == phase)) for phase in range(3)]
    label_template = np.concatenate(
        [np.full(count, phase, dtype=np.int8) for phase, count in enumerate(counts)]
    )
    if len(label_template) != len(active):
        raise AssertionError("null template does not preserve the active population")

    metric_names = tuple(observed)
    null = {name: np.empty(args.trials, dtype=np.float64) for name in metric_names}
    rng = np.random.default_rng(args.seed)
    for trial in range(args.trials):
        owners = np.full(len(names), -1, dtype=np.int8)
        owners[active] = rng.permutation(label_template)
        if not np.array_equal(np.flatnonzero(owners < 0), free):
            raise AssertionError("free-register membership moved in a null trial")
        measured = population_metrics(coords, owners)
        for name in metric_names:
            null[name][trial] = measured[name]
        if (trial + 1) % 24 == 0:
            print(f"NULL_PROGRESS|done={trial + 1}|total={args.trials}|json=0")

    directions = {
        "within_raw": "two",
        "across_raw": "two",
        "raw_gap": "high",
        "within_wave": "two",
        "across_wave": "two",
        "wave_gap": "high",
        "cross_field_pearson": "low",
        "cross_field_cosine": "low",
        "centre_separation": "high",
    }
    rows = [
        row(
            "FUN64NULLHDR",
            schema="ASOLARIA-LIRIS-FUNCTION-MATRIX-64-NULL-V1",
            class_="LIRIS_LOCAL_MEASURED",
            seat="LIRIS",
            subject="runtime_callable_function_surface",
            null="owner_label_shuffle_exact_population_counts",
            functions=len(names),
            red=counts[0],
            green=counts[1],
            blue=counts[2],
            ties_free=len(free),
            trials=args.trials,
            seed=args.seed,
        ).replace("class_=", "class="),
        row(
            "INPUT",
            path=args.manifest.as_posix(),
            bytes=args.manifest.stat().st_size,
            sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        ),
    ]
    significant = {}
    for name in metric_names:
        samples = null[name]
        mean = float(samples.mean())
        sd = float(samples.std(ddof=1))
        z = (observed[name] - mean) / sd if sd else float("nan")
        p = empirical_tail(samples, observed[name], directions[name])
        significant[name] = bool(p <= 0.01)
        rows.append(
            row(
                "METRIC",
                name=name,
                observed=f"{observed[name]:.12f}",
                null_mean=f"{mean:.12f}",
                null_sd=f"{sd:.12f}",
                z=f"{z:.6f}",
                direction=directions[name],
                empirical_p=f"{p:.6f}",
                clears_001=int(significant[name]),
            )
        )

    spatial_clear = (
        significant["cross_field_cosine"]
        or significant["cross_field_pearson"]
        or significant["centre_separation"]
    )
    wave_clear = significant["wave_gap"]
    rows.extend(
        [
            row(
                "VERDICT",
                population_partition="EXACT_BY_CONSTRUCTION",
                spatial_geometry_beyond_matched_labels=(
                    "MEASURED" if spatial_clear else "NOT_DETECTED"
                ),
                wave_identity_gap_beyond_matched_labels=(
                    "MEASURED" if wave_clear else "NOT_DETECTED"
                ),
            ),
            row(
                "BOUNDARY",
                physical_gravity="UNVERIFIED",
                model_weights=0,
                emitted_artifacts=0,
                subject_scope="callable_function_manifest_projection_only",
                null_scope="fixed_coordinates_fixed_counts_random_ownership",
            ),
        ]
    )
    body = "\n".join(rows) + "\n"
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(body, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    args.receipt.with_suffix(args.receipt.suffix + ".sha256").write_text(
        f"{digest}  {args.receipt.name}\n", encoding="ascii", newline="\n"
    )
    print(
        row(
            "FUN64NULL",
            class_="LIRIS_LOCAL_MEASURED",
            trials=args.trials,
            spatial_geometry=(
                "MEASURED" if spatial_clear else "NOT_DETECTED"
            ),
            wave_identity_gap=(
                "MEASURED" if wave_clear else "NOT_DETECTED"
            ),
            receipt_sha256=digest,
        ).replace("class_=", "class=")
    )


if __name__ == "__main__":
    main()
