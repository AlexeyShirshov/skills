"""Helper staging: an empty project workspace does not make an installed helper unavailable."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

class SkillDisambiguationTest(unittest.TestCase):
    def test_driver_reference_rejects_treating_an_empty_workspace_copy_as_unavailable(self) -> None:
        driver = REPO / "skills/pdca/references/driver.md"
        text = " ".join(driver.read_text(encoding="utf-8").split())
        for token in (
            "An overlay's helper lives in that overlay's `scripts/`",
            "`.pdca/scripts/` starts empty",
            "stages byte-identical copies",
            "never a substitute-check, waiver or `Notice:` ground",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
