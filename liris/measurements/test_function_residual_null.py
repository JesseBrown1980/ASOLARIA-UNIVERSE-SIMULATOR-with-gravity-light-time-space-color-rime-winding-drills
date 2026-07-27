#!/usr/bin/env python3
"""Test the RGB-dominance populations outside the three axes that define them.

The 64^3 visualization is constructed from the top three principal components.
Spatial separation inside those same components is therefore partly guaranteed.
This gate removes those three components and asks whether the fixed 42/47/65
owner populations still carry structure in the remaining 61-dimensional
residual.  Exact population sizes are preserved in every permutation.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np

from see_function_matrix_64 import (
    deterministic_pca,
    disjoint_beings,
    parse_function_matrix,
)


def row(record: str, **fields: object) -> str:
    return "|".join([record, *(f"{k}={v}" for k, v in fields.items()), "json=0"])


def pseudo_f(values: np.ndarray, labels: np.ndarray) -> float:
    groups = np.unique(labels)
    grand = values.mean(axis=0)
    ss_between = 0.0
    ss_within = 0.0
    for group in groups:
        subset = values[labels == group]
        mean = subset.mean(axis=0)
        ss_between += len(subset) * float(np.sum((mean - grand) ** 2))
        ss_within += float(np.sum((subset - mean) ** 2))
    df_between = len(groups) - 1
    df_within = len(values) - len(groups)
    return (ss_between / df_between) / max(ss_within / df_within, 1e-30)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--trials", type=int, default=9999)
    parser.add_argument("--seed", type=int, default=0x524553494455414C)
    args = parser.parse_args()

    names, features_i16, _tokens, _signatures = parse_function_matrix(args.manifest)
    coords, loadings, explained = deterministic_pca(features_i16)
    owners, _fields = disjoint_beings(coords)
    active = owners >= 0
    labels = owners[active]

    features = features_i16.astype(np.float64) / 32767.0
    centred = features - features.mean(axis=0, keepdims=True)
    residual = centred - (centred @ loadings.T) @ loadings
    residual = residual[active]

    observed_f = pseudo_f(residual, labels)
    distance2 = np.sum((residual[:, None, :] - residual[None, :, :]) ** 2, axis=2)
    np.fill_diagonal(distance2, np.inf)
    nearest = np.argmin(distance2, axis=1)
    observed_nn = float(np.mean(labels == labels[nearest]))

    rng = np.random.default_rng(args.seed)
    null_f = np.empty(args.trials, dtype=np.float64)
    null_nn = np.empty(args.trials, dtype=np.float64)
    for trial in range(args.trials):
        shuffled = rng.permutation(labels)
        null_f[trial] = pseudo_f(residual, shuffled)
        null_nn[trial] = float(np.mean(shuffled == shuffled[nearest]))

    def stats(name: str, observed: float, null: np.ndarray) -> str:
        mean = float(null.mean())
        sd = float(null.std(ddof=1))
        z = (observed - mean) / sd if sd else float("nan")
        p = (1 + int(np.count_nonzero(null >= observed))) / (len(null) + 1)
        quantiles = np.quantile(null, [0.025, 0.5, 0.975])
        return row(
            "METRIC",
            name=name,
            observed=f"{observed:.12f}",
            null_mean=f"{mean:.12f}",
            null_sd=f"{sd:.12f}",
            null_q025=f"{quantiles[0]:.12f}",
            null_q500=f"{quantiles[1]:.12f}",
            null_q975=f"{quantiles[2]:.12f}",
            z=f"{z:.6f}",
            empirical_p_high=f"{p:.6f}",
            clears_001=int(p <= 0.01),
        )

    rows = [
        row(
            "RESNULLHDR",
            schema="ASOLARIA-LIRIS-FUNCTION-RESIDUAL-NULL-V1",
            class_="LIRIS_LOCAL_MEASURED",
            seat="LIRIS",
            subject="runtime_callable_function_surface",
            functions=len(names),
            active=len(labels),
            dimensions_total=64,
            dimensions_removed=3,
            residual_array_columns=residual.shape[1],
            residual_subspace_rank=residual.shape[1] - loadings.shape[0],
            red=int(np.count_nonzero(labels == 0)),
            green=int(np.count_nonzero(labels == 1)),
            blue=int(np.count_nonzero(labels == 2)),
            trials=args.trials,
            seed=args.seed,
        ).replace("class_=", "class="),
        row(
            "INPUT",
            path=args.manifest.as_posix(),
            sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
            pca_explained_removed=f"{explained.sum():.12f}",
        ),
        stats("residual_pseudo_f", observed_f, null_f),
        stats("residual_nearest_same_owner", observed_nn, null_nn),
    ]
    p_f = (1 + int(np.count_nonzero(null_f >= observed_f))) / (len(null_f) + 1)
    p_nn = (1 + int(np.count_nonzero(null_nn >= observed_nn))) / (len(null_nn) + 1)
    rows.extend(
        [
            row(
                "VERDICT",
                residual_population_structure=(
                    "MEASURED" if min(p_f, p_nn) <= 0.01 else "NOT_DETECTED"
                ),
                criterion="at_least_one_preregistered_residual_metric_p_le_0.01",
            ),
            row(
                "BOUNDARY",
                spatial_cube_separation="PARTLY_CONSTRUCTED_BY_TOP3_PCA_DOMINANCE",
                residual_gate="OUTSIDE_DEFINING_AXES",
                physical_gravity="UNVERIFIED",
                gpt6_callable_manifest="ABSENT",
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
            "RESNULL",
            class_="LIRIS_LOCAL_MEASURED",
            pseudo_f=f"{observed_f:.6f}",
            nearest_same_owner=f"{observed_nn:.6f}",
            p_f=f"{p_f:.6f}",
            p_nn=f"{p_nn:.6f}",
            receipt_sha256=digest,
        ).replace("class_=", "class=")
    )


if __name__ == "__main__":
    main()
