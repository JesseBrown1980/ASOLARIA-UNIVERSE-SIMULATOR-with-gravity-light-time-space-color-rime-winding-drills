"""Equal-weight comparison of old, new, Relic, and combined metatag schemas."""

from __future__ import annotations

from dataclasses import dataclass


CRITERIA = (
    "explicit_state",
    "dynamic_progression",
    "content_addressed_pid",
    "deterministic_60d",
    "temporal_identity_no_exchange",
    "center_c_equals_1",
    "z_axis_separate_from_center",
    "unbounded_recurrence",
    "evidence_separation",
    "hbp_json0_active_path",
    "side_effect_free_import",
    "representation_facets",
    "one_way_rotational_closure",
    "snow_blow_fail_closed_recovery",
)


@dataclass(frozen=True)
class ModelProfile:
    name: str
    source: str
    features: frozenset[str]

    @property
    def score(self) -> int:
        return sum(criterion in self.features for criterion in CRITERIA)

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(criterion for criterion in CRITERIA if criterion not in self.features)

    def hbp_row(self) -> str:
        present = "_".join(
            criterion for criterion in CRITERIA if criterion in self.features
        ) or "NONE"
        missing = "_".join(self.missing) or "NONE"
        return (
            f"MODEL|name={self.name}|source={self.source}|score={self.score}|"
            f"maximum={len(CRITERIA)}|present={present}|missing={missing}|json=0"
        )


PROFILES = (
    ModelProfile(
        "OLD_STATIC_2024",
        "metatagging-quantum-audit-b/quantum_vector_space.py",
        frozenset({"explicit_state", "dynamic_progression"}),
    ),
    ModelProfile(
        "EVOLVABLE_METATAG_V2",
        "metatagging-quantum-audit-b/metatag_v2_behcs.py",
        frozenset(
            {
                "explicit_state",
                "dynamic_progression",
                "content_addressed_pid",
                "deterministic_60d",
                "evidence_separation",
                "side_effect_free_import",
            }
        ),
    ),
    ModelProfile(
        "RELIC_REDISCOVERY_V1",
        "THE-RELIC-REDISCOVERY/relic_rediscovery.py",
        frozenset(
            {
                "explicit_state",
                "dynamic_progression",
                "center_c_equals_1",
                "z_axis_separate_from_center",
                "unbounded_recurrence",
                "evidence_separation",
                "side_effect_free_import",
                "representation_facets",
                "one_way_rotational_closure",
            }
        ),
    ),
    ModelProfile(
        "RELIC_TEMPORAL_METATAG_V2_COMBINED",
        "asolaria-universe-simulator/relic_temporal_metatags.py",
        frozenset(CRITERIA),
    ),
)


def ranked_profiles() -> tuple[ModelProfile, ...]:
    return tuple(sorted(PROFILES, key=lambda profile: (-profile.score, profile.name)))


def best_profile() -> ModelProfile:
    ranked = ranked_profiles()
    if len(ranked) > 1 and ranked[0].score == ranked[1].score:
        raise RuntimeError("comparison has no unique winner")
    return ranked[0]


def render_comparison() -> str:
    rows = [
        "COMPARE|schema=RELIC_METATAG_GENERATION_COMPARISON_V1|"
        f"criteria={len(CRITERIA)}|weighting=EQUAL|scope=RELIC_SIMULATED_UNIVERSE|json=0"
    ]
    rows.extend(profile.hbp_row() for profile in ranked_profiles())
    winner = best_profile()
    rows.append(
        f"BEST|winner={winner.name}|score={winner.score}|maximum={len(CRITERIA)}|"
        "meaning=BEST_FOR_DECLARED_RELIC_SIMULATED_UNIVERSE_SCOPE|"
        "universal_best_claim=0|physical_universe_claim=0|json=0"
    )
    rows.append(
        "TENSEBEST|singular_present=IS|plural_present=ARE|singular_past=WAS|"
        "plural_past=WERE|future=WILL_BE|universal_tense_winner=0|"
        "routing_authority=IS|json=0"
    )
    return "\n".join(rows)


if __name__ == "__main__":
    print(render_comparison())
