import unittest

from relic_temporal_metatags import (
    CENTER_SIGN,
    CENTER_VALUE,
    CURRENT_UTTERANCE_ORDER,
    FREE_CENTER,
    Z_LEVELS,
    RelicWaveMetatag,
    anchor,
    best_form,
    center_at_z,
    exponent,
    multiplier,
    render,
    recovery_rows,
    waves,
)


class RelicTemporalMetatagTests(unittest.TestCase):
    def test_relic_sequence_matches_published_results(self):
        self.assertEqual(
            [anchor(level) for level in range(5)],
            [27, 243, 6561, 531441, 129140163],
        )
        self.assertEqual([multiplier(level) for level in range(4)], [9, 27, 81, 243])

    def test_closed_form_matches_recurrence_without_sample_bound(self):
        for level in range(100):
            self.assertEqual(anchor(level) * multiplier(level), anchor(level + 1))
            self.assertEqual(waves(level)[-1], anchor(level + 1))

    def test_closed_form_exponents(self):
        self.assertEqual([exponent(level) for level in range(5)], [3, 5, 8, 12, 17])

    def test_temporal_form_matrix(self):
        self.assertEqual(best_form("SINGULAR", "PRESENT"), "IS")
        self.assertEqual(best_form("PLURAL", "PRESENT"), "ARE")
        self.assertEqual(best_form("SINGULAR", "PAST"), "WAS")
        self.assertEqual(best_form("PLURAL", "PAST"), "WERE")
        self.assertEqual(best_form("SINGULAR", "FUTURE"), "WILL_BE")
        self.assertEqual(best_form("PLURAL", "FUTURE"), "WILL_BE")

    def test_levels_keep_distinct_temporal_identities(self):
        self.assertEqual(RelicWaveMetatag(3, 4).form, "WAS")
        self.assertEqual(RelicWaveMetatag(4, 4).form, "IS")
        self.assertEqual(RelicWaveMetatag(5, 4).form, "WILL_BE")

    def test_content_address_is_stable_and_state_specific(self):
        first = RelicWaveMetatag(4, 4)
        same = RelicWaveMetatag(4, 4)
        moved = RelicWaveMetatag(4, 5)
        self.assertEqual(first.pid, same.pid)
        self.assertNotEqual(first.pid, moved.pid)

    def test_behcs_projection_is_60d_and_bounded(self):
        values = RelicWaveMetatag(4, 4).behcs_tuple_60d
        self.assertEqual(len(values), 60)
        self.assertTrue(all(0 <= value < 1024 for value in values))

    def test_free_center_and_hbp_boundary_are_preserved(self):
        output = render(current_level=4, future_levels=2)
        self.assertIn("center=C", output)
        self.assertIn("center_value=1", output)
        self.assertIn("center_at_every_z=1", output)
        self.assertIn("terminal_axis=Z", output)
        self.assertIn("after_z=END_0", output)
        self.assertIn("then=NEXT_IS", output)
        self.assertIn("logical_instant_observation=1", output)
        self.assertIn("physical_instant_transport=UNVERIFIED", output)
        self.assertIn("bidirectional=0", output)
        self.assertIn("reverse=0", output)
        self.assertIn("round_trip=0", output)
        self.assertIn("exchange=0", output)
        self.assertIn("winner=IS", output)
        self.assertIn("winner=ARE", output)
        self.assertIn("winner=WAS", output)
        self.assertIn("winner=WERE", output)
        self.assertIn("winner=WILL_BE", output)
        self.assertNotIn("{\"", output)
        self.assertTrue(all(row.endswith("json=0") for row in output.splitlines()))

    def test_center_is_one_at_every_z_without_axis_exchange(self):
        for z in (*Z_LEVELS, -999, 999, "ANY_Z"):
            self.assertEqual(center_at_z(z), CENTER_VALUE)
        self.assertEqual(CENTER_VALUE, 1)

    def test_center_sign_preserves_new_utterance(self):
        self.assertEqual(CENTER_SIGN, ("HBI", "HBP", "SHA", "SH", "HASH"))
        self.assertEqual(CURRENT_UTTERANCE_ORDER, CENTER_SIGN)

    def test_snow_blow_recovery_is_fail_closed_and_non_destructive(self):
        output = "\n".join(recovery_rows())
        self.assertIn("ZERO_CONTAMINATED_ACTIVE_RUNTIME", output)
        self.assertIn("forensic_preserve=1", output)
        self.assertIn("offline_physical_disk=1", output)
        self.assertIn("restore_requires_hash=1", output)
        self.assertIn("restore_requires_signature=1", output)
        self.assertIn("reopen_requires_canary_pass=1", output)
        self.assertIn("destructive_wipe=0", output)
        self.assertIn("clean_backup_wipe=0", output)
        self.assertIn("auto_execute=0", output)
        self.assertIn("bidirectional_injected=0", output)

    def test_invalid_coordinates_fail_closed(self):
        with self.assertRaises(ValueError):
            RelicWaveMetatag(-1, 0)
        with self.assertRaises(ValueError):
            best_form("SINGULAR", "MAYBE")


if __name__ == "__main__":
    unittest.main()
