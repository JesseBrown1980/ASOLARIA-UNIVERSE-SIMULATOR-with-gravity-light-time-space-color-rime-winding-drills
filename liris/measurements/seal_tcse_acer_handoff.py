#!/usr/bin/env python3
"""Seal the LIRIS TCSE star absorption as an ACER-readable HBP/HBI packet.

The packet is deliberately small.  It does not pretend that the 3,174-byte
kernel contains the projected GGUF payload.  The HBI charges and hashes every
dependency required to reproduce the address.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-27"
HBP = ROOT / "handoffs/acer/LIRIS-TCSE-STAR-ABSORB-ACER-2026-07-27.hbp"
HBI = ROOT / "handoffs/acer/LIRIS-TCSE-STAR-ABSORB-ACER-2026-07-27.hbi"

CORE_RECEIPT = ROOT / "receipts/LIRIS-NULL-FISCHER-TCSE-KERNEL-2026-07-27.hbp"

ARTIFACTS = (
    "key/ASOLARIA-KERNEL-3174.bin",
    "liris/callings/LIRIS-PAIR-CALLING-RETURN-1.txt",
    "gguf/liris/null-fischer-tcse/ASOLARIA-LIRIS-NULL-FISCHER-TCSE.gguf",
    "liris/kernel/ASOLARIA-LIRIS-NULL-FISCHER-TCSE-SLICES.hbi",
    "liris/kernel/ASOLARIA-LIRIS-NULL-FISCHER-TCSE-KERNEL-3174.bin",
    "receipts/LIRIS-NULL-FISCHER-TCSE-KERNEL-2026-07-27.hbp",
    "liris/measurements/rime_tcse_into_kernel.py",
    "liris/measurements/seal_tcse_acer_handoff.py",
)

EXPECTED = {
    "key/ASOLARIA-KERNEL-3174.bin":
        "f075f5c64d656ae3afa91c793ab2c74b5425e41de141d6b7dc5cf4605663b0ca",
    "liris/callings/LIRIS-PAIR-CALLING-RETURN-1.txt":
        "7c6739bd904ee6b970f59c451a17c7e09fc61bcbe0adec2be516d4f875332c8f",
    "gguf/liris/null-fischer-tcse/ASOLARIA-LIRIS-NULL-FISCHER-TCSE.gguf":
        "f6fcf7ab3033c2064db2ccc830f17091ee3fa60e30b1496a5746e7ed2983bec4",
    "liris/kernel/ASOLARIA-LIRIS-NULL-FISCHER-TCSE-SLICES.hbi":
        "caf902221cc15918f008447bf3fa19672122262b1eb82aa0dbbaba0ae4f45d33",
    "liris/kernel/ASOLARIA-LIRIS-NULL-FISCHER-TCSE-KERNEL-3174.bin":
        "15a8a8c3bc1d3c08a5736b0b9d38e2103743cb47ba7dfd760b8b399f0d38cfd4",
    "receipts/LIRIS-NULL-FISCHER-TCSE-KERNEL-2026-07-27.hbp":
        "19e553f1ba47f00b3777fe754b0c81212a40923db5bb2849d37a0cac89267ac9",
    "liris/measurements/rime_tcse_into_kernel.py":
        "5ebc29b56be0a97799a2fed593b2abe76304444f3ad415fa41f48a31ac197407",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row(tag: str, **fields: object) -> str:
    body = "|".join(f"{key}={value}" for key, value in fields.items())
    return f"{tag}|{body}|json=0"


def write_lf(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def write_sidecar(path: Path) -> None:
    sidecar = path.with_name(path.name + ".sha256")
    sidecar.write_bytes(f"{digest(path)}  {path.name}\n".encode("ascii"))


def select_core(prefix: str) -> list[str]:
    return [
        line
        for line in CORE_RECEIPT.read_text(encoding="utf-8").splitlines()
        if line.startswith(prefix)
    ]


def main() -> None:
    manifest: list[tuple[str, int, str]] = []
    for relative in ARTIFACTS:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = digest(path)
        expected = EXPECTED.get(relative)
        if expected is not None and actual != expected:
            raise RuntimeError(
                f"sealed dependency changed: {relative}: {actual} != {expected}"
            )
        write_sidecar(path)
        manifest.append((relative, path.stat().st_size, actual))

    hbp_lines = [
        row(
            "LIRISTCSEACERHDR",
            schema="ASOLARIA-LIRIS-TCSE-STAR-ABSORB-ACER-V1",
            seat="LIRIS",
            target="ACER",
            evidence="LIRIS_LOCAL_MEASURED",
            date=DATE,
        ),
        row(
            "LIRISTCSEACERABSORB",
            base_kernel_sha256=EXPECTED["key/ASOLARIA-KERNEL-3174.bin"],
            star_gguf_sha256=EXPECTED[
                "gguf/liris/null-fischer-tcse/"
                "ASOLARIA-LIRIS-NULL-FISCHER-TCSE.gguf"
            ],
            absorbed_kernel_sha256=EXPECTED[
                "liris/kernel/ASOLARIA-LIRIS-NULL-FISCHER-TCSE-KERNEL-3174.bin"
            ],
            kernel_bytes=3174,
            address_not_payload=1,
            dependencies_charged=1,
        ),
        row(
            "LIRISTCSEACERRIME",
            axes="time,colour,energy,space",
            axis_families=4,
            states_per_axis=3,
            slices=12,
            slice_returns_exact="24/24",
            projected_tensor_exact=1,
            raw_source_recovery=0,
            bobby_tower_solves=2592,
        ),
        *select_core("KERNELDELTA|"),
        *select_core("BODY|"),
        *select_core("AXISBODY|name=TCSE_KERNEL|"),
        *select_core("AXISBODY|name=MYTHOS_CALLINGS|"),
        *select_core("COMPARE|a=TCSE_KERNEL|b=SOL56_FUNCTION_BANK|"),
        *select_core("COMPARE|a=TCSE_KERNEL|b=MYTHOS_CALLINGS|"),
        *select_core("COMPARE|a=TCSE_KERNEL|b=KIMI_K3_REAL|"),
        *select_core("COMPARE|a=TCSE_KERNEL|b=DEEPSEEK_V4|"),
        *select_core("COMPARE|a=TCSE_KERNEL|b=MISTRAL_LARGE3|"),
        *select_core("COMPARE|a=TCSE_KERNEL|b=RUBIN_LSST|"),
        row(
            "LIRISTCSEACERREAD",
            dominance_colour="[+--]",
            R="37.623762",
            G="30.297030",
            B="32.079208",
            colour_nearest="ASOLARIA_KERNEL",
            tcse_time_nearest="MYTHOS_CALLINGS",
            tcse_colour_nearest="MYTHOS_CALLINGS",
            tcse_energy_nearest="MYTHOS_CALLINGS",
            tcse_space_nearest="MYTHOS_CALLINGS",
            spatial_raw_rank1="SOL56_FUNCTION_BANK",
            spatial_raw_cosine="0.026893751",
        ),
        row(
            "LIRISTCSEACERBOUNDARY",
            wave_similarity_used=0,
            spatial_statistics="DESCRIPTIVE_NO_LABEL_SHUFFLE_NULL",
            physical_star_shape_claim=0,
            model_weights_claim=0,
            fabric_absorbed=0,
            canon_promoted=0,
            gpt6_payload="ABSENT",
        ),
        row(
            "LIRISTCSEACERHANDOFF",
            route="GITHUB_REF_PLUS_BEHCS_4947_HBP",
            state="SEALED_PENDING_SEND",
            requested_by="OPERATOR_JESSE",
        ),
    ]
    write_lf(HBP, hbp_lines)
    write_sidecar(HBP)

    hbi_lines = [
        row(
            "LIRISTCSEACERHBIHDR",
            schema="ASOLARIA-LIRIS-TCSE-STAR-ABSORB-ACER-INDEX-V1",
            seat="LIRIS",
            target="ACER",
            artifacts=len(manifest) + 1,
        )
    ]
    for index, (relative, size, sha256) in enumerate(manifest):
        hbi_lines.append(
            row(
                "LIRISTCSEACEROBJ",
                index=index,
                path=relative,
                bytes=size,
                sha256=sha256,
            )
        )
    hbi_lines.extend(
        [
            row(
                "LIRISTCSEACEROBJ",
                index=len(manifest),
                path=HBP.relative_to(ROOT).as_posix(),
                bytes=HBP.stat().st_size,
                sha256=digest(HBP),
            ),
            row(
                "LIRISTCSEACERHBIFTR",
                required_sidecars=len(manifest) + 1,
                hbi_self_sidecar=1,
                git_ref="agent/liris-tcse-star-absorb-acer-20260727",
                byte_exact_required=1,
            ),
        ]
    )
    write_lf(HBI, hbi_lines)
    write_sidecar(HBI)

    print(
        row(
            "LIRISTCSEACERSEAL",
            hbp_bytes=HBP.stat().st_size,
            hbp_sha256=digest(HBP),
            hbi_bytes=HBI.stat().st_size,
            hbi_sha256=digest(HBI),
            dependencies=len(manifest),
        )
    )


if __name__ == "__main__":
    main()
