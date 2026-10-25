"""Schedule-shape guards added after the October 2026 `nextorm` retro.

The rc4 collection put 44 of 60 units into one serialized group; every later
unit waited behind the whole chain, while the host could not have carried four
lanes anyway (11 GB, one container lease).  Two rules were missing: width is a
clustering objective, and the lane ceiling derives from a declared host budget.

Presence-only, like the other contract guards in this package.

Run:
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"
LANE_REF = SKILL_DIR / "references/lane.md"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip()


class ScheduleWidthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Width/host budget stay in §P.4; the capacity rule of a late addition
        # moved with the schedule revision into references/lane.md.
        cls.text = norm(SKILL.read_text(encoding="utf-8"))
        cls.lane = norm(LANE_REF.read_text(encoding="utf-8"))

    def test_width_is_a_clustering_objective(self) -> None:
        self.assertIn("Width is an objective, not a by-product", self.text)
        self.assertIn("Minimise the largest serialized group", self.text)

    def test_lane_ceiling_derives_from_host_budget(self) -> None:
        self.assertIn("host budget", self.text)
        self.assertIn("memory, measurement locks, container capacity", self.text)

    def test_scope_addition_consumes_capacity(self) -> None:
        self.assertIn("may not silently jump ahead of ready items", self.lane)
        self.assertIn("consumes capacity explicitly", self.lane)

    def test_own_plan_keeps_plan_hygiene(self) -> None:
        self.assertIn("not a licence to skip plan hygiene", self.text)
        self.assertIn("validates its command contract", self.text)


if __name__ == "__main__":
    unittest.main()
