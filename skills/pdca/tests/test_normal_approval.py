"""Retained contract of `SKILL.md` §Normal-mode approval after the trim.

The section stays authoritative but compact: every behavioural rule survives —
the normal-mode gate, the caller-driven approval ref, the autonomous exemption —
and a byte/word cap keeps the prose from re-expanding. Checks are on the
contract (who approves, what is bound, where a mismatch goes), not on a
particular wording.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
HEADING = "### Normal-mode approval"

# The trimmed section is ~967 bytes / 133 words; the cap leaves room for a
# wording correction, not for a return of the removed exposition.
MAX_BYTES = 1000
MAX_WORDS = 140


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str) -> str:
    start = text.index(HEADING)
    end = text.index("\n### ", start + len(HEADING))
    return text[start:end]


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


class NormalApprovalSectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = section(read(SKILL))
        self.text = flat(self.raw)

    def test_heading_and_two_paragraph_shape(self) -> None:
        self.assertEqual(1, read(SKILL).count(HEADING))
        body = self.raw.split(HEADING, 1)[1].strip()
        paragraphs = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
        self.assertEqual(2, len(paragraphs), "the section is two paragraphs, not an essay")

    def test_the_gate_admits_only_explicit_approval(self) -> None:
        """Plan saved first, then an explicit approval; nothing else starts DO."""
        self.assertLess(self.text.index("before do"), self.text.index("explicit approval"))
        self.assertIn("saves the plan in status", self.text)
        for token in (
            "requested/delivered results",
            "credits `pdca-planner`",
            "§effort and time policy",
            "are not approval",
            "until approval only status may be created or edited",
            "not a result mismatch",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.text)
        self.assertRegex(self.text, r"plan-terminal outcomes go to act")

    def test_caller_driven_approval_binds_the_exact_cycle(self) -> None:
        self.assertIn("the parent obtains approval, never the delegated driver", self.text)
        for token in (
            "pending ref",
            "task/`cycle_id`",
            "`n`",
            "`r`",
            "criteria",
            "`plan_handoff` carries it",
            "against that ref resumes the same cycle/step",
            "fresh ref",
            "fresh approval",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.text)
        self.assertRegex(
            self.text,
            r"missing/mismatched approval (returns|is) an approval-needed checkpoint",
        )
        self.assertIn("not do or fresh plan", self.text)

    def test_autonomous_mode_keeps_no_plan_gate(self) -> None:
        self.assertRegex(self.text, r"no approval slots(/|\s+and\s+no\s+)gate")
        self.assertIn("environment/user-required approvals", self.text)

    def test_no_cutoff_rule_is_duplicated_here(self) -> None:
        """§Effort and time policy owns the cutoff; the gate only points at it."""
        self.assertIn("§effort and time policy", self.text)
        self.assertNotIn("cutoff", self.text)

    def test_section_stays_compact(self) -> None:
        self.assertLessEqual(len(self.raw.encode("utf-8")), MAX_BYTES,
                             "§Normal-mode approval re-expanded past the trim budget")
        self.assertLessEqual(len(self.raw.split()), MAX_WORDS,
                             "§Normal-mode approval re-expanded past the trim budget")


if __name__ == "__main__":
    unittest.main()
