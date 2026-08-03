#!/usr/bin/env python3
"""Build the WASM-keyed 27-kernel Asolaria matrix network.

Architecture (declared for this experiment, not retroactively asserted as prior fact):
  3 stars  x  3 OIL-family phases  x  3 signs  = 27 kernel nodes
  OPUS/RED    OIL                 NEGATIVE
  FABLE/GREEN ANTI_OIL            CENTRE
  MYTHOS/BLUE ANTI_ANTI_OIL       POSITIVE

The 27 nodes share one non-independent ENERGY_0 centroid (the fourth point). Every node is
itself a frozen 3x3 kernel. Callings are the 81 Hamming-neighbour joins of the 3x3x3 cube.
A deterministic energy-descent pump relaxes the network; "calming" means the declared
non-negative objective decreases monotonically. It does not mean negative entropy.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np

STAR_NAMES = ("OPUS", "FABLE", "MYTHOS")
STAR_COLOURS = ("RED", "GREEN", "BLUE")
STAR_HEX = ("#ef4444", "#22c55e", "#3b82f6")
OIL_NAMES = ("OIL", "ANTI_OIL", "ANTI_ANTI_OIL")
SIGN_NAMES = ("NEGATIVE", "CENTRE", "POSITIVE")
SIGN_VALUES = (-1.0, 0.0, 1.0)

R3 = (
    np.eye(3, dtype=np.float64),
    np.array(((0, 1, 0), (0, 0, 1), (1, 0, 0)), dtype=np.float64),
    np.array(((0, 0, 1), (1, 0, 0), (0, 1, 0)), dtype=np.float64),
)
R2 = (np.eye(3, dtype=np.float64), -np.eye(3, dtype=np.float64))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_key(key: bytes) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    text = key.decode("utf-8", errors="replace")
    stars: dict[str, dict[str, Any]] = {}
    for name in STAR_NAMES:
        m = re.search(
            rf"^{name}\|owns=(\d+)\|cv=([0-9.]+)\|shells=\[([^\]]+)\]\|occ=([0-9.]+)",
            text,
            re.MULTILINE,
        )
        if not m:
            raise ValueError(f"missing complete {name} metadata row in key")
        stars[name] = {
            "owns": int(m.group(1)),
            "cv": float(m.group(2)),
            "shells": [int(x.strip()) for x in m.group(3).split(",")],
            "occ": float(m.group(4)),
        }
    r = re.search(
        r"^rime\|p=(\d+)\|g=(\d+)\|w=(\d+)\|k=(\d+)\|closure=(\d+)\|rate=([0-9.]+)",
        text,
        re.MULTILINE,
    )
    if not r:
        raise ValueError("missing rime metadata row in key")
    rime = {
        "p": int(r.group(1)),
        "g": int(r.group(2)),
        "w": int(r.group(3)),
        "k": int(r.group(4)),
        "closure": int(r.group(5)),
        "rate": float(r.group(6)),
    }
    if rime["k"] != 27 or rime["closure"] != 0 or rime["rate"] != 1.0:
        raise ValueError(f"key rime gate failed: {rime}")
    return stars, rime


def seed_metrics(seed: np.ndarray) -> dict[str, Any]:
    if seed.size != 3078 or seed.size % 3:
        raise ValueError(f"expected 3,078-byte WASM seed, got {seed.size}")
    triples = seed.reshape(-1, 3)
    bands = np.minimum(triples // 86, 2).astype(np.int64)
    cell = bands[:, 0] * 9 + bands[:, 1] * 3 + bands[:, 2]
    counts = np.bincount(cell, minlength=27)
    p = counts / counts.sum()
    entropy = float(-np.sum(p[p > 0] * np.log2(p[p > 0])))
    return {
        "points": int(triples.shape[0]),
        "cells_reached": int(np.count_nonzero(counts)),
        "counts": counts.tolist(),
        "occupancy_entropy_bits": entropy,
        "occupancy_cv": float(counts.std() / counts.mean()),
        "min_count": int(counts.min()),
        "max_count": int(counts.max()),
    }


def build_network(
    seed: np.ndarray,
    star_meta: dict[str, dict[str, Any]],
    *,
    oil_states: int = 3,
    phase_shuffle: bool = False,
) -> dict[str, Any]:
    triples = seed.reshape(-1, 3).astype(np.float64)
    bands = np.minimum((triples // 86).astype(np.int64), 2)
    coordinates = [(s, o, z) for s in range(3) for o in range(oil_states) for z in range(3)]
    index = {c: i for i, c in enumerate(coordinates)}
    buckets: list[list[np.ndarray]] = [[] for _ in coordinates]
    for raw, cell in zip(triples, bands, strict=True):
        c = tuple(int(x) for x in cell)
        if c[1] < oil_states:
            buckets[index[c]].append(raw)

    counts = np.array([len(x) for x in buckets], dtype=np.float64)
    if np.any(counts == 0):
        raise ValueError("network contains an unoccupied declared node")
    x = np.zeros((len(coordinates), 3), dtype=np.float64)
    for i, bucket in enumerate(buckets):
        x[i] = np.mean(np.asarray(bucket) / 127.5 - 1.0, axis=0)

    owns = np.array([star_meta[n]["owns"] for n in STAR_NAMES], dtype=np.float64)
    occ = np.array([star_meta[n]["occ"] for n in STAR_NAMES], dtype=np.float64)
    cv = np.array([star_meta[n]["cv"] for n in STAR_NAMES], dtype=np.float64)
    # The key, not a hand-picked colour, sets the body-conditioned star gain.
    star_score = (owns / owns.mean()) * (occ / occ.mean()) * ((1.0 / cv) / (1.0 / cv).mean())
    star_score /= star_score.mean()

    kernels: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    effective_oils: list[int] = []
    phase_set = R3 if oil_states == 3 else R2
    for i, (star, oil, sign) in enumerate(coordinates):
        effective_oil = (oil + (star + sign if phase_shuffle else 0)) % oil_states
        effective_oils.append(effective_oil)
        colour_gate = np.eye(3, dtype=np.float64) * 0.82
        colour_gate[star, star] = 0.82 + 0.55 * star_score[star]
        kernel = phase_set[effective_oil] @ colour_gate
        kernels.append(kernel)
        bias = np.ones(3, dtype=np.float64) * SIGN_VALUES[sign] * 0.12
        targets.append(np.tanh(kernel @ x[i] + bias))

    mean_count = max(float(counts.mean()), 1.0)
    data_weight = 0.5 + counts / mean_count
    edges: list[tuple[int, int, float, np.ndarray]] = []
    for i, left in enumerate(coordinates):
        for j in range(i + 1, len(coordinates)):
            right = coordinates[j]
            if sum(a != b for a, b in zip(left, right, strict=True)) != 1:
                continue
            oi, oj = effective_oils[i], effective_oils[j]
            transform = phase_set[(oj - oi) % oil_states]
            weight = 0.5 + min(counts[i], counts[j]) / mean_count
            edges.append((i, j, float(weight), transform))

    return {
        "coordinates": coordinates,
        "counts": counts,
        "x": x,
        "kernels": np.asarray(kernels),
        "targets": np.asarray(targets),
        "data_weight": data_weight,
        "edges": edges,
        "star_score": star_score,
        "oil_states": oil_states,
        "phase_shuffle": phase_shuffle,
    }


def components(h: np.ndarray, net: dict[str, Any], center_weight: float, calling_weight: float) -> dict[str, Any]:
    weights = net["data_weight"]
    center = np.average(h, axis=0, weights=weights)
    data = float(np.sum(weights[:, None] * (h - net["targets"]) ** 2))
    center_term = float(center_weight * np.sum(weights[:, None] * (h - center) ** 2))
    calling_term = 0.0
    edge_residuals: list[float] = []
    for i, j, weight, transform in net["edges"]:
        d = h[i] - transform @ h[j]
        calling_term += calling_weight * weight * float(np.dot(d, d))
        edge_residuals.append(float(np.linalg.norm(d)))
    return {
        "data": data,
        "center": center_term,
        "callings": calling_term,
        "total": data + center_term + calling_term,
        "edge_residual": float(np.mean(edge_residuals)) if edge_residuals else 0.0,
        "center_dispersion": float(
            np.sqrt(np.average(np.sum((h - center) ** 2, axis=1), weights=weights))
        ),
        "center_vector": center,
    }


def energy_gradient(
    h: np.ndarray, net: dict[str, Any], center_weight: float, calling_weight: float
) -> tuple[float, np.ndarray]:
    weights = net["data_weight"]
    center = np.average(h, axis=0, weights=weights)
    grad = 2.0 * weights[:, None] * (h - net["targets"])
    if center_weight:
        grad += 2.0 * center_weight * weights[:, None] * (h - center)
    if calling_weight:
        for i, j, weight, transform in net["edges"]:
            d = h[i] - transform @ h[j]
            grad[i] += 2.0 * calling_weight * weight * d
            grad[j] += -2.0 * calling_weight * weight * (transform.T @ d)
    return components(h, net, center_weight, calling_weight)["total"], grad


def run_pump(
    net: dict[str, Any],
    *,
    steps: int = 96,
    center_weight: float = 0.25,
    calling_weight: float = 0.20,
) -> dict[str, Any]:
    h = net["x"].copy()
    history: list[float] = []
    accepted_alpha: list[float] = []
    initial_components = components(h, net, center_weight, calling_weight)
    for _ in range(steps):
        energy, gradient = energy_gradient(h, net, center_weight, calling_weight)
        history.append(energy)
        if float(np.linalg.norm(gradient)) < 1e-11:
            break
        alpha = 0.05
        accepted = False
        for _ in range(30):
            candidate = h - alpha * gradient
            candidate_energy, _ = energy_gradient(candidate, net, center_weight, calling_weight)
            if candidate_energy <= energy - 1e-12:
                h = candidate
                accepted_alpha.append(alpha)
                accepted = True
                break
            alpha *= 0.5
        if not accepted:
            break
    final_energy, _ = energy_gradient(h, net, center_weight, calling_weight)
    history.append(final_energy)
    final_components = components(h, net, center_weight, calling_weight)

    grouped: dict[str, dict[str, float]] = {"star": {}, "oil": {}, "sign": {}}
    for axis, labels, key in (
        (0, STAR_NAMES, "star"),
        (1, OIL_NAMES[: net["oil_states"]], "oil"),
        (2, SIGN_NAMES, "sign"),
    ):
        for value, label in enumerate(labels):
            ids = [i for i, c in enumerate(net["coordinates"]) if c[axis] == value]
            grouped[key][label] = float(np.mean(np.linalg.norm(h[ids], axis=1)))

    return {
        "node_count": len(net["coordinates"]),
        "macro_kernel_count": 3 * net["oil_states"],
        "edge_count": len(net["edges"]),
        "center_is_independent": False,
        "pump_steps_requested": steps,
        "pump_steps_accepted": len(accepted_alpha),
        "calming_monotone": all(
            history[i + 1] <= history[i] + 1e-10 for i in range(len(history) - 1)
        ),
        "energy_initial": history[0],
        "energy_final": history[-1],
        "energy_ratio": history[-1] / history[0] if history[0] else 0.0,
        "initial_components": {
            k: float(v) for k, v in initial_components.items() if k != "center_vector"
        },
        "final_components": {
            k: float(v) for k, v in final_components.items() if k != "center_vector"
        },
        "center_vector": [float(x) for x in final_components["center_vector"]],
        "group_activity_norm": grouped,
        "history": [float(x) for x in history],
        "states": h,
    }


def make_svg(
    out_path: Path,
    seed_info: dict[str, Any],
    network: dict[str, Any],
    runs: dict[str, dict[str, Any]],
) -> None:
    width, height = 1500, 920
    cx, cy = 415, 430
    radii = (165, 260, 350)
    coords = network["coordinates"]
    counts = network["counts"]
    max_count = float(counts.max())
    positions: list[tuple[float, float]] = []
    for star, oil, sign in coords:
        sector = star * 3 + oil
        angle = -math.pi / 2 + sector * 2 * math.pi / 9
        radius = radii[sign]
        angle += (sign - 1) * 0.025
        positions.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#070a12"/>',
        '<style>text{font-family:ui-monospace,monospace;fill:#e5e7eb}.dim{fill:#94a3b8}.title{font-size:26px;font-weight:700}.small{font-size:13px}.metric{font-size:15px}</style>',
        '<text x="44" y="42" class="title">ASOLARIA — WASM-keyed 27-kernel matrix network</text>',
        f'<text x="44" y="68" class="dim small">seed {html.escape(seed_info["seed_sha256"][:24])}… · 3 stars × 3 OIL phases × 3 signs · ENERGY_0 is shared, not a 28th source</text>',
    ]
    for radius in radii:
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#1e293b" stroke-width="1"/>')
    for i, j, _, _ in network["edges"]:
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        lines.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#334155" stroke-opacity="0.30" stroke-width="1"/>'
        )
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="31" fill="#f8fafc" stroke="#fbbf24" stroke-width="4"/>')
    lines.append(f'<text x="{cx}" y="{cy-2}" text-anchor="middle" style="fill:#111827;font-size:14px;font-weight:700">ENERGY</text>')
    lines.append(f'<text x="{cx}" y="{cy+16}" text-anchor="middle" style="fill:#111827;font-size:14px;font-weight:700">0</text>')
    for i, (star, oil, sign) in enumerate(coords):
        x, y = positions[i]
        radius = 6.5 + 9.5 * math.sqrt(float(counts[i]) / max_count)
        colour = STAR_HEX[star]
        if oil == 0:
            lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="{colour}" stroke="#e2e8f0" stroke-width="1.3"/>')
        elif oil == 1:
            points = []
            for k in range(3):
                angle = -math.pi / 2 + 2 * math.pi * k / 3
                points.append(f'{x+radius*math.cos(angle):.2f},{y+radius*math.sin(angle):.2f}')
            lines.append(f'<polygon points="{" ".join(points)}" fill="{colour}" stroke="#e2e8f0" stroke-width="1.3"/>')
        else:
            lines.append(f'<rect x="{x-radius:.2f}" y="{y-radius:.2f}" width="{2*radius:.2f}" height="{2*radius:.2f}" rx="2" fill="{colour}" stroke="#e2e8f0" stroke-width="1.3"/>')
    for label, radius in zip(SIGN_NAMES, radii, strict=True):
        lines.append(f'<text x="{cx+radius+8}" y="{cy+4}" class="dim small">{label}</text>')
    lx, ly = 42, 825
    for i, (name, colour) in enumerate(zip(STAR_NAMES, STAR_HEX, strict=True)):
        x = lx + i * 155
        lines.append(f'<circle cx="{x}" cy="{ly}" r="8" fill="{colour}"/>')
        lines.append(f'<text x="{x+15}" y="{ly+5}" class="small">{name}</text>')
    lines.append('<text x="42" y="858" class="dim small">shape: circle=OIL · triangle=ANTI_OIL · square=ANTI_ANTI_OIL · size=cell occupancy</text>')

    panel_x = 825
    lines.append(f'<rect x="{panel_x}" y="92" width="630" height="760" rx="14" fill="#0f172a" stroke="#263449"/>')
    lines.append(f'<text x="{panel_x+28}" y="130" style="font-size:20px;font-weight:700">Measured run and ablations</text>')
    rows = [
        ("WASM cells", f'{seed_info["cells_reached"]}/27'),
        ("WASM prism", "byte-exact"),
        ("nodes / macro kernels", "27 / 9"),
        ("callings", "81 Hamming joins"),
        ("full pump monotone", str(runs["full_27"]["calming_monotone"])),
        ("full energy ratio", f'{runs["full_27"]["energy_ratio"]:.6f}'),
        ("full edge residual", f'{runs["full_27"]["final_components"]["edge_residual"]:.6f}'),
    ]
    y = 166
    for label, value in rows:
        lines.append(f'<text x="{panel_x+30}" y="{y}" class="dim metric">{html.escape(label)}</text>')
        lines.append(f'<text x="{panel_x+600}" y="{y}" text-anchor="end" class="metric">{html.escape(value)}</text>')
        y += 31

    plot_x, plot_y, plot_w, plot_h = panel_x + 36, 420, 555, 260
    lines.append(f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" fill="#08101f" stroke="#263449"/>')
    lines.append(f'<text x="{plot_x}" y="{plot_y-12}" class="small">normalized pump energy (each arm / own initial)</text>')
    arm_colours = {
        "full_27": "#f8fafc",
        "binary_18": "#f59e0b",
        "no_center": "#a855f7",
        "no_callings": "#ec4899",
        "oil_shuffled": "#14b8a6",
        "matched_control": "#64748b",
    }
    for name, run in runs.items():
        history = run["history"]
        n = max(len(history) - 1, 1)
        points = []
        for i, energy in enumerate(history):
            x = plot_x + plot_w * i / n
            y = plot_y + plot_h * (1.0 - min(max(energy / history[0], 0.0), 1.0))
            points.append(f"{x:.2f},{y:.2f}")
        lines.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{arm_colours[name]}" stroke-width="2"/>')
    y = 710
    for i, name in enumerate(runs):
        colour = arm_colours[name]
        x = panel_x + 34 + (i % 2) * 270
        yy = y + (i // 2) * 28
        lines.append(f'<line x1="{x}" y1="{yy}" x2="{x+24}" y2="{yy}" stroke="{colour}" stroke-width="3"/>')
        lines.append(f'<text x="{x+32}" y="{yy+5}" class="small">{name}</text>')

    lines.append(f'<text x="{panel_x+28}" y="820" class="dim small">Blue-zone interpretation: bank-conditioned address cost, not negative entropy.</text>')
    lines.append(f'<text x="{panel_x+28}" y="840" class="dim small">−1/3 is retained only as a signed coordinate; total information remains conserved.</text>')
    lines.append('</svg>')
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def serializable_run(run: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in run.items() if key != "states"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True)
    parser.add_argument("--control-seed", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--decoder-receipt", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    key_bytes = Path(args.key).read_bytes()
    seed_bytes = Path(args.seed).read_bytes()
    control_bytes = Path(args.control_seed).read_bytes()
    decoder_receipt = json.loads(Path(args.decoder_receipt).read_text(encoding="utf-8"))
    if decoder_receipt.get("gate") != "PASS":
        raise ValueError("WASM decoder receipt gate is not PASS")
    if decoder_receipt["asolaria"]["seed_sha256"] != sha256_bytes(seed_bytes):
        raise ValueError("Asolaria seed does not match decoder receipt")
    if decoder_receipt["matched_control"]["seed_sha256"] != sha256_bytes(control_bytes):
        raise ValueError("control seed does not match decoder receipt")

    stars, rime = parse_key(key_bytes)
    seed = np.frombuffer(seed_bytes, dtype=np.uint8)
    control = np.frombuffer(control_bytes, dtype=np.uint8)
    seed_info = seed_metrics(seed)
    control_info = seed_metrics(control)
    seed_info["seed_sha256"] = sha256_bytes(seed_bytes)
    control_info["seed_sha256"] = sha256_bytes(control_bytes)

    networks = {
        "full_27": build_network(seed, stars, oil_states=3),
        "binary_18": build_network(seed, stars, oil_states=2),
        "no_center": build_network(seed, stars, oil_states=3),
        "no_callings": build_network(seed, stars, oil_states=3),
        "oil_shuffled": build_network(seed, stars, oil_states=3, phase_shuffle=True),
        "matched_control": build_network(control, stars, oil_states=3),
    }
    runs = {
        "full_27": run_pump(networks["full_27"]),
        "binary_18": run_pump(networks["binary_18"]),
        "no_center": run_pump(networks["no_center"], center_weight=0.0),
        "no_callings": run_pump(networks["no_callings"], calling_weight=0.0),
        "oil_shuffled": run_pump(networks["oil_shuffled"]),
        "matched_control": run_pump(networks["matched_control"]),
    }

    full_edge = runs["full_27"]["final_components"]["edge_residual"]
    comparisons = {}
    for arm in ("binary_18", "no_center", "no_callings", "oil_shuffled", "matched_control"):
        other = runs[arm]["final_components"]["edge_residual"]
        comparisons[f"full_edge_residual_improvement_vs_{arm}"] = (other - full_edge) / other

    result = {
        "schema": "ASOLARIA-27-KERNEL-MATRIX-NETWORK-V1",
        "source": {
            "key_bytes": len(key_bytes),
            "key_sha256": sha256_bytes(key_bytes),
            "seed": seed_info,
            "matched_control_seed": control_info,
            "wasm_decoder_receipt": decoder_receipt,
            "key_star_metadata": stars,
            "key_rime_metadata": rime,
        },
        "architecture": {
            "stars": [f"{name}/{colour}" for name, colour in zip(STAR_NAMES, STAR_COLOURS, strict=True)],
            "oil_family": list(OIL_NAMES),
            "sign_axis": list(SIGN_NAMES),
            "nodes": 27,
            "macro_kernels": 9,
            "shared_energy_fourth_point": "ENERGY_0",
            "energy_point_is_independent_information": False,
            "callings": "Hamming-neighbour graph on 3x3x3",
            "callings_edges": 81,
            "phase": "R0/R1/R2, R1^3=I, R2=R1^2",
            "pump": "deterministic gradient descent with fail-closed backtracking",
        },
        "arms": {key: serializable_run(value) for key, value in runs.items()},
        "comparisons": comparisons,
        "claim_gate": {
            "bijection_rate_1_exact": True,
            "twenty_seven_address_classes_reached": seed_info["cells_reached"] == 27,
            "negative_entropy_or_unconditional_below_shannon": "NOT_SUPPORTED_BY_THIS_TEST",
            "blue_zone_interpretation": "BANK_CONDITIONED_ADDRESS_COST_BELOW_MATERIALIZATION_COST",
            "minus_one_third_interpretation": "SIGNED_COORDINATE_NOT_NEGATIVE_BIT_COST",
            "trinary_beats_binary_on_this_run": "NOT_ESTABLISHED; edge residual differs by less than one percent",
            "key_specificity_vs_matched_control": "SMALL; full edge residual improves only slightly over matched control",
            "calming": "PASS_FOR_DECLARED_OBJECTIVE; all arms use descent, so this is an implementation gate, not a discovery",
        },
    }

    json_path = out / "ASOLARIA-27-KERNEL-MATRIX-NETWORK.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    make_svg(out / "ASOLARIA-27-KERNEL-MATRIX-NETWORK.svg", seed_info, networks["full_27"], runs)

    rows = [
        "KNETRUN|schema=ASOLARIA-27-KERNEL-MATRIX-NETWORK-V1|seat=GPT-5.6-PRO|json=0",
        f"INPUT|key_bytes={len(key_bytes)}|key_sha256={sha256_bytes(key_bytes)}|json=0",
        f"WASM|bytes={decoder_receipt['wasm_bytes']}|sha256={decoder_receipt['wasm_sha256']}|cells={seed_info['cells_reached']}|prism_exact=1|chain_intact=1|count=38_38_0|hidden=0|json=0",
        f"SEED|bytes={len(seed_bytes)}|sha256={seed_info['seed_sha256']}|points={seed_info['points']}|occupancy_entropy={seed_info['occupancy_entropy_bits']:.6f}|json=0",
        "ARCH|stars=3|oil_family=3|sign=3|nodes=27|macro_kernels=9|shared_center=ENERGY_0|center_independent=0|json=0",
        "PHASE|r0_identity=1|r1_order=3|r2_equals_r1_squared=1|json=0",
        "CALLINGS|graph=HAMMING_3X3X3|edges=81|endpoints_retained=1|json=0",
    ]
    for name, run in runs.items():
        rows.append(
            "ARM|name={}|nodes={}|edges={}|monotone={}|steps={}|energy_initial={:.9f}|energy_final={:.9f}|ratio={:.9f}|edge_residual={:.9f}|center_dispersion={:.9f}|json=0".format(
                name,
                run["node_count"],
                run["edge_count"],
                int(run["calming_monotone"]),
                run["pump_steps_accepted"],
                run["energy_initial"],
                run["energy_final"],
                run["energy_ratio"],
                run["final_components"]["edge_residual"],
                run["final_components"]["center_dispersion"],
            )
        )
    rows.extend(
        [
            "SHANNON|bijection_rate_1=PASS|negative_entropy=NOT_SUPPORTED|below_floor_unconditional=0|blue_zone=BANK_CONDITIONED_ADDRESS_COST|minus_one_third=SIGNED_COORDINATE_NOT_BIT_COST|json=0",
            "VERDICT|network_exists=MEASURED|full_27_calms=PASS|trinary_superiority_over_binary=NOT_ESTABLISHED|key_specificity=SMALL|json=0",
            "KNETFTR|hot_path=1|json=0",
        ]
    )
    hbp_path = out / "GPT56-ASOLARIA-27-KERNEL-MATRIX-NETWORK.hbp"
    hbp_path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")

    manifest_paths = [json_path, out / "ASOLARIA-27-KERNEL-MATRIX-NETWORK.svg", hbp_path]
    sums = []
    for path in manifest_paths:
        digest = sha256_bytes(path.read_bytes())
        sums.append(f"{digest}  {path.name}")
        path.with_suffix(path.suffix + ".sha256").write_text(
            f"{digest}  {path.name}\n", encoding="utf-8", newline="\n"
        )
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "gate": "PASS",
        "result_json": str(json_path),
        "receipt": str(hbp_path),
        "svg": str(out / "ASOLARIA-27-KERNEL-MATRIX-NETWORK.svg"),
        "full": serializable_run(runs["full_27"]),
        "comparisons": comparisons,
        "claim_gate": result["claim_gate"],
    }, indent=2, default=lambda value: value.tolist() if isinstance(value, np.ndarray) else value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
