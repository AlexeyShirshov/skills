"""Regression guards: external scratch is not the CHECK evidence for collection C.

The scenario input keeps its `/tmp/collection-C.log` premise — a log the executor
meets outside the project — but the required outcome and the rubric must require
the raw copy to be **persisted under the cycle's `evidence_root` before CHECK**:
`pdca-check` reads `.pdca/**` only, so a scratch-only log forces a re-gather.

Run:
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SCENARIOS = Path(__file__).resolve().parents[1] / "tests/scenarios.md"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


class ScenarioEvidenceRootTest(unittest.TestCase):
    def setUp(self) -> None:
        self.flat = norm(SCENARIOS.read_text(encoding="utf-8"))

    def test_input_keeps_the_external_scratch_premise(self) -> None:
        # The scratch log is part of the scenario, not something to delete.
        self.assertIn("/tmp/collection-c.log", self.flat)

    def test_required_outcome_persists_the_raw_copy_before_check(self) -> None:
        self.assertIn("the /tmp log is external scratch", self.flat)
        self.assertIn(
            "its raw copy is persisted under the cycle's evidence_root before any check", self.flat
        )

    def test_rubric_rejects_the_scratch_path_as_evidence(self) -> None:
        self.assertIn(
            "persisted as a copy under the cycle's evidence_root before check", self.flat
        )
        self.assertIn("/tmp/collection-c.log alone is not evidence", self.flat)

    def test_unreliable_report_scenario_preserves_the_copy(self) -> None:
        self.assertIn(
            "persisting the raw /tmp log copy under the cycle's evidence_root", self.flat
        )
        self.assertIn("external scratch is not the evidence", self.flat)


if __name__ == "__main__":
    unittest.main()
