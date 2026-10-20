"""Collection is a batch of independent goals, not a parallelism-only contract.

The entry skill chooses `pdca-collection` for a list of independent tasks. Parallelism is an
execution mode: with one group or `cap = 1` the collection degrades to a single sequential lane
instead of changing contracts. These guards pin that boundary so the "≥2 disjoint footprints"
rule is not misread as an entry condition.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"


class RoutingGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = SKILL.read_text(encoding="utf-8")
        self.text = " ".join(self.raw.split())

    def test_parallelism_is_not_an_entry_condition(self):
        self.assertIn("Параллелизм — не условие входа", self.text)

    def test_one_group_or_cap_one_degrades_to_a_single_lane(self):
        self.assertIn("cap = 1", self.text)
        self.assertIn("деградация к одному лейну", self.text)
        self.assertIn("Не создавай фиктивные группы", self.text)

    def test_groups_are_an_execution_mode(self):
        self.assertIn("группы — способ исполнения, не условие входа", self.text)

    def test_reservation_covers_the_whole_task(self):
        # A resource reservation is taken for the whole task and serialized; it is
        # never narrowed to the first steps.
        for stem in ("резервац", "всю задачу", "сериализ", "непересечен"):
            with self.subTest(stem=stem):
                self.assertIn(
                    stem, self.text,
                    f"SKILL.md lacks the reservation stem {stem!r}",
                )
        for line in self.raw.splitlines():
            with self.subTest(line=line.strip()[:80]):
                self.assertIsNone(
                    re.search(r"(?i)(только|лишь).{0,40}(первые|первых).{0,20}шаг", line),
                    "SKILL.md must not allow reserving only the first steps: "
                    f"{line!r}",
                )

    def test_reservation_is_renegotiated_before_any_recluster(self):
        for stem in ("пересогласован", "поверхност"):
            with self.subTest(stem=stem):
                self.assertIn(
                    stem, self.text,
                    f"SKILL.md lacks the boundary stem {stem!r}",
                )
        low = self.text.lower()
        self.assertIn("recluster", low,
                      "collection SKILL lost the no-recluster token")
        self.assertIn("резервац", low,
                      "reservation and recluster must be stated together")


if __name__ == "__main__":
    unittest.main()
