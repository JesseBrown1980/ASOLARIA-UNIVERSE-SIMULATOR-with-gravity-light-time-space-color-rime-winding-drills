import unittest

from compare_relic_metatag_generations import (
    CRITERIA,
    PROFILES,
    best_profile,
    ranked_profiles,
    render_comparison,
)


class RelicGenerationComparisonTests(unittest.TestCase):
    def test_profiles_cover_old_new_relic_and_combined(self):
        self.assertEqual(
            {profile.name for profile in PROFILES},
            {
                "OLD_STATIC_2024",
                "EVOLVABLE_METATAG_V2",
                "RELIC_REDISCOVERY_V1",
                "RELIC_TEMPORAL_METATAG_V2_COMBINED",
            },
        )

    def test_criteria_are_unique_and_equal_weight(self):
        self.assertEqual(len(CRITERIA), len(set(CRITERIA)))
        for profile in PROFILES:
            self.assertTrue(profile.features <= set(CRITERIA))

    def test_combined_model_is_unique_goal_scoped_winner(self):
        winner = best_profile()
        self.assertEqual(winner.name, "RELIC_TEMPORAL_METATAG_V2_COMBINED")
        self.assertEqual(winner.score, len(CRITERIA))
        self.assertGreater(winner.score, ranked_profiles()[1].score)

    def test_comparison_preserves_limits_and_json0(self):
        output = render_comparison()
        self.assertIn("universal_best_claim=0", output)
        self.assertIn("physical_universe_claim=0", output)
        self.assertIn("routing_authority=IS", output)
        self.assertTrue(all(row.endswith("json=0") for row in output.splitlines()))


if __name__ == "__main__":
    unittest.main()
