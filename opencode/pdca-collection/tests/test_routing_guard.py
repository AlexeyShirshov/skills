"""Collection is a batch of independent goals, not a parallelism-only contract.

The entry skill chooses `pdca-collection` for a list of independent tasks. Parallelism is an
execution mode: with one group or `cap = 1` the collection degrades to a single sequential lane
instead of changing contracts. These guards pin that boundary so the "≥2 disjoint footprints"
rule is not misread as an entry condition.
"""

from __future__ import annotations

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"


class RoutingGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = " ".join(SKILL.read_text(encoding="utf-8").split())

    def test_parallelism_is_not_an_entry_condition(self):
        self.assertIn("Параллелизм — не условие входа", self.text)

    def test_one_group_or_cap_one_degrades_to_a_single_lane(self):
        self.assertIn("cap = 1", self.text)
        self.assertIn("деградация к одному лейну", self.text)
        self.assertIn("Не создавай фиктивные группы", self.text)

    def test_groups_are_an_execution_mode(self):
        self.assertIn("группы — способ исполнения, не условие входа", self.text)


if __name__ == "__main__":
    unittest.main()
