"""Regression guard: the PDCA entry contract stays under the 50,000-byte limit.

Every PDCA driver loads the base contract in full; the 50,000-byte size
limit comes from the user, not from a style preference.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_skill_size.py' -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"


class SkillSizeTest(unittest.TestCase):
    def test_skill_stays_under_50kb(self) -> None:
        size = len(SKILL.read_bytes())
        self.assertLess(size, 50_000, f"{SKILL} is {size} bytes; keep it under 50,000")


if __name__ == "__main__":
    unittest.main()
