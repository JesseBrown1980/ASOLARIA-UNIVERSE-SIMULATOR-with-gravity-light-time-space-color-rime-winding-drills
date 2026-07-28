from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BOOKS = ROOT / "books"
CANONICAL_LAWS = BOOKS / "COMBINED-BOOK-OF-LAWS.md"
CANONICAL_MIRROR = BOOKS / "COMBINED-BOOK-OF-LAWS-622823.md"
LAW_47 = BOOKS / "LAW-47-THE-UNIVERSE-TEACHES-THE-GLYPHS-TO-SPEAK.md"
OLD_SPEECH_LAW_45 = BOOKS / "LAW-45-THE-UNIVERSE-TEACHES-THE-GLYPHS-TO-SPEAK.md"
ARCHAEOLOGY = BOOKS / "archaeology" / "WORDPRESS-CORPUS-CHRONOLOGY.md"
HISTORY_INDEX = BOOKS / "history" / "WORDPRESS-PUBLICATION-HISTORY-2011-2026.md"
TITOR_DOSSIER = BOOKS / "history" / "JOHN-TITOR-C204-SOURCE-DOSSIER.md"
CROSSWALK = (
    ROOT
    / "docs"
    / "WORDPRESS-OPERATOR-PUBLICATION-CHRONOLOGY-CROSSWALK-2011-2026.md"
)
REGISTRATION_RECEIPT = (
    ROOT
    / "receipts"
    / "LIRIS-WORDPRESS-PID-REGISTRATION-REQUEST-2026-07-28.hbp"
)
HANDOFF_RECEIPT = (
    ROOT
    / "receipts"
    / "LIRIS-TO-ACER-TO-RELIC-WORDPRESS-TRIDIRECTIONAL-HANDOFF-2026-07-28.hbp"
)


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def law_section(text: str, number: int) -> str:
    match = re.search(
        rf"(?ms)^### Law {number}\b.*?(?=^### Law \d+\b|\Z)",
        text,
    )
    if match is None:
        raise AssertionError(f"Law {number} section not found")
    return match.group(0)


def hbp_row(text: str, row_type: str) -> dict[str, str]:
    rows = [line for line in text.splitlines() if line.startswith(f"{row_type}|")]
    if len(rows) != 1:
        raise AssertionError(
            f"expected exactly one {row_type} row, found {len(rows)}"
        )
    fields: dict[str, str] = {}
    for item in rows[0].split("|")[1:]:
        if "=" not in item:
            raise AssertionError(f"malformed {row_type} field: {item!r}")
        key, value = item.split("=", 1)
        fields[key] = value
    return fields


class WordPressLawIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.canonical = read_text(CANONICAL_LAWS)
        cls.crosswalk = read_text(CROSSWALK)

    def test_laws_37_through_53_are_unique_and_ordered(self):
        headings = [
            int(value)
            for value in re.findall(r"(?m)^### Law (\d+)\b", self.canonical)
            if 37 <= int(value) <= 53
        ]
        expected = list(range(37, 54))
        self.assertEqual(headings, expected)
        self.assertEqual(len(headings), len(set(headings)))

    def test_canonical_mirror_has_byte_parity(self):
        self.assertEqual(CANONICAL_MIRROR.read_bytes(), CANONICAL_LAWS.read_bytes())

    def test_law_47_standalone_replaces_old_speech_law_45_filename(self):
        self.assertTrue(LAW_47.is_file())
        self.assertIn(
            "# Law 47 — The Universe Teaches the Glyphs to Speak",
            read_text(LAW_47),
        )
        self.assertFalse(OLD_SPEECH_LAW_45.exists())

    def test_archaeology_preserves_acer_ancestor_and_liris_successor(self):
        archaeology = read_text(ARCHAEOLOGY)
        self.assertIn("ACER PARTIAL ANCESTOR", archaeology)
        self.assertIn("Acer read 26 distinct posts", archaeology)
        self.assertIn("LIRIS successor census", archaeology)
        self.assertIn("33/33 published posts directly fetched by ID", archaeology)

    def test_crosswalk_has_complete_denominator_without_raw_contact_fields(self):
        self.assertIn("33/33 published posts returned HTTP 200", self.crosswalk)
        self.assertIn(
            "contact fields, and profile data",
            self.crosswalk,
        )
        self.assertIn(
            "no raw payload, article body, contact field, profile",
            self.crosswalk,
        )

        lower = self.crosswalk.lower()
        for raw_marker in (
            '"email":',
            '"phone":',
            '"contact":',
            "email=",
            "phone=",
            "contact=",
            "mailto:",
            "tel:",
        ):
            self.assertNotIn(raw_marker, lower)
        self.assertIsNone(
            re.search(
                r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
                self.crosswalk,
                re.IGNORECASE,
            )
        )
        self.assertIsNone(
            re.search(
                r"(?<!\d)(?:\+\d{1,3}[\s.-])?\(?\d{2,3}\)?"
                r"[\s.-]\d{3,4}[\s.-]\d{4}(?!\d)",
                self.crosswalk,
            )
        )

    def test_activation_polarity_is_distinct_from_relational_cycle(self):
        self.assertIn(
            "Mutual zero/one and the relational cycle are different ledgers",
            self.crosswalk,
        )
        self.assertIn(
            "`0 <-> 1` is the activation polarity and `1 -> 2 -> 3 -> 0` is the",
            self.crosswalk,
        )
        self.assertIn("relational/generative cycle", self.crosswalk)

    def test_rgb_light_derives_yellow_and_keeps_cmy_cmyk_separate(self):
        law_45 = law_section(self.canonical, 45)
        self.assertIn(
            "Yellow is not an emitted/computer-light primary",
            law_45,
        )
        self.assertIn(
            "COLOUR|basis=RGB|order=RED_GREEN_BLUE|"
            "yellow=DERIVED_RED_PLUS_GREEN|json=0",
            law_45,
        )
        self.assertIn("CMY/CMYK context", law_45)
        self.assertIn("Pigment, ink, and material subtraction remain a separate", law_45)

    def test_phased_roles_and_route_specific_order_are_preserved(self):
        law_47 = law_section(self.canonical, 47)
        law_52 = law_section(self.canonical, 52)
        expected_roles = (
            "PHASE|name=FOLDER_ROOM|role=CATALOG_OR_EXECUTOR",
            "PHASE|name=WATCHER|role=OBSERVE_TRIGGER_AND_CHANGE",
            "PHASE|name=READER|role=RESOLVE_ADDRESS_CONTEXT_AND_BODY",
            "PHASE|name=DISPATCHER|role=BIND_VERB_TO_AUTHORIZED_EXECUTOR",
        )
        for role in expected_roles:
            self.assertIn(role, law_47)
        self.assertIn(
            "PHASESET|members=FOLDER_WATCHER_READER_DISPATCHER_"
            "EXECUTOR_RECEIPT_GC|order=ROUTE_SPECIFIC|none_alone=1|json=0",
            law_52,
        )

    def test_wordpress_history_pointer_index_exists(self):
        history = read_text(HISTORY_INDEX)
        self.assertIn("33/33", history)
        self.assertIn("ACER_PARTIAL_ANCESTOR", history)
        self.assertIn(
            "WORDPRESS-OPERATOR-PUBLICATION-CHRONOLOGY-CROSSWALK-2011-2026.md",
            history,
        )
        self.assertIn("current_runtime_claim=0", history)
        self.assertIn("raw_bodies=0", history)

    def test_john_titor_dossier_preserves_patent_boundary(self):
        dossier = read_text(TITOR_DOSSIER)
        self.assertIn("ANALYSIS_COMPARISON_TARGET_ONLY", dossier)
        self.assertIn("Marlin B. Pohlman", dossier)
        self.assertIn("2004-10-01", dossier)
        self.assertIn("2006-04-06", dossier)
        self.assertIn("2008-03-13", dossier)
        self.assertIn("MEASURED_CURRENT_ARCHIVE_MIRROR", dossier)
        self.assertIn("time-travel-paradoxes/14274", dossier)
        self.assertIn("not a John Titor patent", dossier)
        self.assertIn("not proof of a working device", dossier)
        self.assertIn("Neither `d` nor `epsilon` is supplied", dossier)
        self.assertIn("physical_validity_claim=0", dossier)

    def test_registration_request_is_held_if_present(self):
        if not REGISTRATION_RECEIPT.exists():
            self.skipTest(
                "TEMPORARY: registration-request receipt is not present yet"
            )
        receipt = read_text(REGISTRATION_RECEIPT)
        self.assertEqual(
            hbp_row(receipt, "PIDREGREQ")["status"],
            "HELD_FOR_ACER_REGISTRAR",
        )
        office_rule = hbp_row(receipt, "PIDOFFICERULE")
        self.assertEqual(office_rule["registrar_owner"], "ACER_PID_OFFICE")
        self.assertEqual(office_rule["incoming_drop_performed"], "0")
        boundary = hbp_row(receipt, "BOUNDARY")
        self.assertEqual(boundary["not_final_office_receipt"], "1")
        self.assertEqual(boundary["live_incoming_mutated"], "0")
        action = hbp_row(receipt, "ACTION")
        for field in ("mint", "launch", "fire", "apply", "runtime_authority"):
            self.assertEqual(action[field], "0")
        verify = hbp_row(receipt, "VERIFY")
        self.assertEqual(verify["acer_registrar"], "PENDING")
        self.assertEqual(verify["relic"], "PENDING_AFTER_BILATERAL")

    def test_tridirectional_handoff_is_held_with_relic_pending_if_present(self):
        if not HANDOFF_RECEIPT.exists():
            self.skipTest(
                "TEMPORARY: tridirectional handoff receipt is not present yet"
            )
        receipt = read_text(HANDOFF_RECEIPT)
        self.assertEqual(
            hbp_row(receipt, "TRIHANDOFF")["status"],
            "HELD_PENDING_BILATERAL_RETURN",
        )
        action = hbp_row(receipt, "ACTION")
        for field in (
            "send_external",
            "bridge_execute",
            "mint",
            "fire",
            "apply",
            "runtime_authority",
        ):
            self.assertEqual(action[field], "0")
        gate = hbp_row(receipt, "GATE")
        self.assertEqual(gate["liris"], "PASS")
        self.assertEqual(gate["acer_reverse"], "PENDING")
        self.assertEqual(gate["relic_third"], "PENDING")
        self.assertEqual(gate["tridirectional_complete"], "0")

    def test_integrated_text_artifacts_are_lf_only(self):
        for path in (
            CANONICAL_LAWS,
            CANONICAL_MIRROR,
            CROSSWALK,
            HISTORY_INDEX,
            TITOR_DOSSIER,
            Path(__file__),
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                data = path.read_bytes()
                self.assertNotIn(b"\r", data)
                self.assertTrue(data.endswith(b"\n"))


if __name__ == "__main__":
    unittest.main()
