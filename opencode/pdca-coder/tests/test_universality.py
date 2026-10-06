"""Toolchain/lens-selection guards for the pdca-coder skill.

Rule-presence only: these tests read `SKILL.md` as text; they never execute a
model or a real cycle.  The skill targets software-engineering tasks and must
not advertise non-code deliverables (presentations, research reports, ...).

Run:
    python3 -m unittest discover -s config/skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SKILL_PATH = REPO / "config/skills/pdca-coder/SKILL.md"


def _cat(*fragments):
    """Runtime join (no compile-time folding into a bytecode literal)."""
    return "".join(fragments)


# Stack token, assembled from fragments so this guard file stays clean.
STACK_LENS = _cat("dot", "net-")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip()


class UniversalityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = norm(SKILL_PATH.read_text(encoding="utf-8"))

    # --- toolchain/lens-selection model ----------------------------------

    def test_lens_selection_section_present(self):
        self.assertIn("PLAN selects the toolchain and lenses", self.skill)
        self.assertIn("The cycle is stack-agnostic", self.skill)

    def test_five_step_lens_selection_model(self):
        for step in (
            "Identify the deliverable type",
            "Discover the project's declared toolchain",
            "Select the correctness lenses",
            "Bind each lens to an available, permitted agent/skill",
            "Freeze the selection",
        ):
            with self.subTest(step=step):
                self.assertIn(step, self.skill)

    # --- CODE worked example ---------------------------------------------

    def test_code_worked_example(self):
        for token in (
            "Worked example — CODE",
            "CSV-summary CLI",
            "empty input",
            "malformed rows",
            "nonzero exit status",
            "deterministic",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.skill)

    # --- scoped to code: no non-code deliverable wording -----------------

    def test_no_noncode_deliverable_wording(self):
        lowered = SKILL_PATH.read_text(encoding="utf-8").lower()
        for banned in ("presentation", "non-code", "onboarding", "artifact-agnostic"):
            with self.subTest(token=banned):
                self.assertNotIn(banned, lowered)

    # --- no mandatory stack-specific specialist --------------------------

    def test_no_mandatory_stack_specialist(self):
        lowered = SKILL_PATH.read_text(encoding="utf-8").lower()
        self.assertNotIn(STACK_LENS, lowered)
        mandatory = _cat("a ", STACK_LENS, "specialist is mandatory")
        self.assertNotIn(mandatory, lowered)
        self.assertNotIn("stack-specific specialist is mandatory", self.skill)


if __name__ == "__main__":
    unittest.main()
