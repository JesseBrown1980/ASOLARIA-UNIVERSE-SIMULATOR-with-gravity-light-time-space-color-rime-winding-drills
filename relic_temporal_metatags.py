"""Relic Rediscovery wave landings matched to the universe metatag grammar.

This is a deterministic simulation/addressing model.  Its coordinates are logical;
they are not particle measurements or evidence of a physical universe.
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass


SCHEMA = "ASOLARIA_RELIC_TEMPORAL_METATAG_V1"
FREE_CENTER = "C"
CENTER_VALUE = 1
Z_LEVELS = ("-1/3", "0", "+1/3")
END_ZERO = 0
TERMINAL_AXIS = "Z"
ROTATIONAL_CLOSURE = "X_TO_Y_TO_Z_TO_END_0_TO_NEXT_IS"
CENTER_SIGN = ("HBI", "HBP", "SHA", "SH", "HASH")
CURRENT_UTTERANCE_ORDER = CENTER_SIGN
SNOW_BLOW_STAGES = (
    "DETECT_POISON",
    "ISOLATE_RUNTIME_AND_PORTS",
    "PRESERVE_FORENSIC_RESIDUE",
    "ZERO_CONTAMINATED_ACTIVE_RUNTIME",
    "VERIFY_SIGNED_COLOR_DISK",
    "REPLENISH_FRESH_RUNTIME",
    "CANARY_TEST",
    "ADMIT_NEXT_IS",
)
MATH_STATUS = "PROVEN_BY_INDUCTION_FOR_ALL_N_GE_0"
FORMS = ("IS", "ARE", "WAS", "WERE", "WILL_BE")


def _nonnegative(value: int, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")


def center_at_z(_z: object) -> int:
    """C remains one for every structure and every Z coordinate."""
    return CENTER_VALUE


def exponent(level: int) -> int:
    _nonnegative(level, "level")
    return 3 + level * (level + 3) // 2


def anchor(level: int) -> int:
    return 3 ** exponent(level)


def multiplier(level: int) -> int:
    _nonnegative(level, "level")
    return 3 ** (level + 2)


def waves(level: int) -> tuple[int, ...]:
    start = anchor(level)
    return tuple(start * 3**step for step in range(1, level + 3))


def temporal_relation(level: int, current_level: int) -> str:
    _nonnegative(level, "level")
    _nonnegative(current_level, "current_level")
    if level < current_level:
        return "PAST"
    if level == current_level:
        return "PRESENT"
    return "FUTURE"


def best_form(number: str, relation: str) -> str:
    """Select tense without exchanging grammatical number or temporal identity."""
    if number not in {"SINGULAR", "PLURAL"}:
        raise ValueError("number must be SINGULAR or PLURAL")
    if relation == "PRESENT":
        return "IS" if number == "SINGULAR" else "ARE"
    if relation == "PAST":
        return "WAS" if number == "SINGULAR" else "WERE"
    if relation == "FUTURE":
        return "WILL_BE"
    raise ValueError("relation must be PAST, PRESENT, or FUTURE")


@dataclass(frozen=True)
class RelicWaveMetatag:
    level: int
    current_level: int

    def __post_init__(self) -> None:
        _nonnegative(self.level, "level")
        _nonnegative(self.current_level, "current_level")

    @property
    def relation(self) -> str:
        return temporal_relation(self.level, self.current_level)

    @property
    def form(self) -> str:
        return best_form("SINGULAR", self.relation)

    @property
    def simulation_status(self) -> str:
        return {
            "PAST": "WAS_SIMULATED_CHECKED",
            "PRESENT": "IS_SIMULATED_CHECKED",
            "FUTURE": "WILL_BE_NOT_YET_SIMULATED",
        }[self.relation]

    @property
    def state_text(self) -> str:
        return "|".join(
            (
                f"schema={SCHEMA}",
                f"level={self.level}",
                f"current_level={self.current_level}",
                f"center={FREE_CENTER}",
                f"center_value={CENTER_VALUE}",
                f"terminal_axis={TERMINAL_AXIS}",
                f"end_zero={END_ZERO}",
                f"closure={ROTATIONAL_CLOSURE}",
                f"center_sign={'_'.join(CENTER_SIGN)}",
                f"exponent={exponent(self.level)}",
                f"outward={anchor(self.level)}",
                f"multiplier={multiplier(self.level)}",
                f"relation={self.relation}",
                f"form={self.form}",
                f"math={MATH_STATUS}",
                f"simulation={self.simulation_status}",
            )
        )

    @property
    def pid(self) -> str:
        return "RLC-" + hashlib.sha256(self.state_text.encode("utf-8")).hexdigest()[:16]

    @property
    def behcs_tuple_60d(self) -> tuple[int, ...]:
        digest = hashlib.sha256(self.state_text.encode("utf-8")).digest()
        return tuple(
            (digest[index % len(digest)] * ((index + 1) % 7 + 1)) % 1024
            for index in range(60)
        )

    def hbp_row(self) -> str:
        behcs = "_".join(str(value) for value in self.behcs_tuple_60d)
        return (
            f"RELICTAG|pid={self.pid}|level={self.level}|center={FREE_CENTER}|"
            f"center_value={CENTER_VALUE}|center_invariant=1|"
            f"terminal_axis={TERMINAL_AXIS}|end_zero={END_ZERO}|"
            f"closure={ROTATIONAL_CLOSURE}|logical_instant_observation=1|"
            f"physical_instant_transport=UNVERIFIED|bidirectional=0|reverse=0|"
            f"round_trip=0|exchange=0|center_sign={'_'.join(CENTER_SIGN)}|"
            f"utterance_order={'_'.join(CURRENT_UTTERANCE_ORDER)}|"
            f"outward={anchor(self.level)}|exponent={exponent(self.level)}|"
            f"waves_to_next={self.level + 2}|multiplier_to_next={multiplier(self.level)}|"
            f"relation={self.relation}|form={self.form}|math={MATH_STATUS}|"
            f"simulation={self.simulation_status}|behcs60={behcs}|json=0"
        )


def verdict_rows() -> tuple[str, ...]:
    contexts = (
        ("singular_current_formula", "SINGULAR", "PRESENT"),
        ("plural_current_test_results", "PLURAL", "PRESENT"),
        ("singular_prior_landing", "SINGULAR", "PAST"),
        ("plural_prior_landings", "PLURAL", "PAST"),
        ("future_unmaterialized_landing", "SINGULAR", "FUTURE"),
    )
    rows = []
    for context, number, relation in contexts:
        winner = best_form(number, relation)
        rows.append(
            f"FORMVERDICT|context={context}|number={number}|relation={relation}|"
            f"winner={winner}|candidates={'_'.join(FORMS)}|identity_exchange=0|json=0"
        )
    rows.append(
        "ROUTINGVERDICT|question=which_form_leads_current_simulation_truth|winner=IS|"
        "reason=present_singular_authority|are=present_plural|was_were=provenance|"
        "will_be=prediction|tense_changes_math=0|json=0"
    )
    rows.append(
        "CLOSUREVERDICT|axis_path=X_TO_Y_TO_Z|terminal_axis=Z|after_z=END_0|"
        "then=NEXT_IS|center_at_every_z=1|mode=CONTINUED_ROTATION|"
        "logical_instant_observation=1|physical_instant_transport=UNVERIFIED|"
        "bidirectional=0|reverse=0|round_trip=0|exchange=0|json=0"
    )
    rows.append(
        "CENTERSIGN|center=C|value=1|members=HBI_HBP_SHA_SH_HASH|"
        "utterance_order=HBI_HBP_SHA_SH_HASH|transport_chain_inferred=0|json=0"
    )
    return tuple(rows)


def recovery_rows() -> tuple[str, ...]:
    """Describe recovery policy without executing isolation, deletion, or restore."""
    return (
        "SNOWBLOW|meaning=SAFE_POISON_RECOVERY|"
        f"stages={'_TO_'.join(SNOW_BLOW_STAGES)}|auto_execute=0|json=0",
        "RECOVERYBOUNDARY|zero_scope=CONTAMINATED_ACTIVE_RUNTIME_ONLY|"
        "destructive_wipe=0|clean_backup_wipe=0|forensic_preserve=1|"
        "offline_physical_disk=1|restore_requires_hash=1|restore_requires_signature=1|"
        "color_state=SIGNED_RESTORE_METADATA|json=0",
        "PORTRECOVERY|affected_ports=ISOLATED|reopen_requires_clean_rebuild=1|"
        "reopen_requires_canary_pass=1|allowlist=1|least_privilege=1|"
        "bidirectional_injected=0|json=0",
    )


def render(current_level: int, future_levels: int) -> str:
    _nonnegative(current_level, "current_level")
    _nonnegative(future_levels, "future_levels")
    rows = [
        f"RELICMETA|schema={SCHEMA}|current_level={current_level}|"
        f"future_levels={future_levels}|center={FREE_CENTER}|center_value={CENTER_VALUE}|"
        f"terminal_axis={TERMINAL_AXIS}|end_zero={END_ZERO}|math={MATH_STATUS}|json=0"
    ]
    rows.extend(
        RelicWaveMetatag(level, current_level).hbp_row()
        for level in range(current_level + future_levels + 1)
    )
    rows.extend(verdict_rows())
    rows.extend(recovery_rows())
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-level", type=int, default=4)
    parser.add_argument("--future-levels", type=int, default=2)
    args = parser.parse_args()
    print(render(args.current_level, args.future_levels))


if __name__ == "__main__":
    main()
