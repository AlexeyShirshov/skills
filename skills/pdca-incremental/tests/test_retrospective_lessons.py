"""Regression guards: per-step ACT retrospective in incremental campaigns.

The campaign form inherits the base skeleton demoted under each step, so its
#### Lessons learned is pending at step creation and finished in ACT, including
a terminal STOP.  No new role, log, phase or counter is introduced.

Run:
    python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"
DOC = SKILL_DIR.parents[1] / "docs/pdca-incremental.md"
DOC_RU = SKILL_DIR.parents[1] / "docs/ru/pdca-incremental.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


class IncrementalRetrospectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(SKILL)
        self.body = norm(self.text)

    def test_per_step_act_runs_the_base_retrospective(self) -> None:
        for token in (
            "per-step act, including a terminal stop, runs the same configured pdca-check retrospective",
            "demoted #### lessons learned",
            "pending at step creation",
            "finished in act",
            "same campaign file",
            "no new role, log, phase or counter",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_shared_event_log_remains_single(self) -> None:
        for token in (
            "base status skeleton",
            "demoted under that step's record",
            "exactly one event log",
            "never a second chronology",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)


class IncrementalDocsTest(unittest.TestCase):
    """Both languages document the demoted per-step retrospective."""

    def test_docs_carry_the_step_lesson(self) -> None:
        for path in (DOC, DOC_RU):
            body = norm(read(path))
            with self.subTest(path=path.name):
                self.assertIn("#### lessons learned", body)
                self.assertIn("check: not run", body)
                self.assertIn("retrospective", body)


if __name__ == "__main__":
    unittest.main()
