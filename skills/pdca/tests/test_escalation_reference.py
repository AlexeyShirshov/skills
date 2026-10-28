"""Regression guards: the escalation protocol is a lazily loaded reference.

The base contract keeps the docs-anchor heading and a short trigger/pointer section; the
protocol itself lives in ``pdca/references/escalate.md``, which the driver reads before the
dispatch and passes with the expert input.  Routine PLAN/CHECK paths never load it.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
BASE = SKILL_DIR / "SKILL.md"
ESCALATE_REFERENCE = SKILL_DIR / "references/escalate.md"
ESCALATION_HEADING = "### Escalation — expert review (`pdca-escalate`)"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


def section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


def escalation_section() -> str:
    return section(read(BASE), "### Escalation — expert review", "### Generic operating constraints")


class BasePointerTest(unittest.TestCase):
    """The base keeps the anchor and routes the protocol lazily."""

    def test_docs_anchor_heading_is_preserved(self) -> None:
        self.assertIn(ESCALATION_HEADING, read(BASE))

    def test_section_stays_short(self) -> None:
        self.assertLessEqual(len(escalation_section().encode("utf-8")), 800)

    def test_section_requires_read_before_dispatch_and_input_inclusion(self) -> None:
        body = norm(escalation_section())
        for token in (
            "references/escalate.md",
            "before dispatching pdca-escalate",
            "driver must read",
            "protocol with the question and evidence",
            "not a phase or extra attempt",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_the_long_block_is_no_longer_inline(self) -> None:
        body = norm(escalation_section())
        for token in (
            "recommended disposition",
            "fresh user approval",
            "returns to the phase that asked",
            "reused, not re-gathered",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, body)

    def test_routine_paths_do_not_load_the_escalation_reference(self) -> None:
        text = read(BASE)
        for start, end in (("#### PLAN", "#### DO"), ("#### CHECK", "#### ACT")):
            with self.subTest(section=start):
                self.assertNotIn("references/escalate.md", section(text, start, end))


class ReferenceTest(unittest.TestCase):
    """The reference holds the detailed protocol and its delivery rule."""

    def test_reference_exists_and_states_its_delivery(self) -> None:
        body = norm(read(ESCALATE_REFERENCE))
        for token in ("driver reads this file before dispatch", "expert input"):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_reference_preserves_the_detailed_contract(self) -> None:
        body = norm(read(ESCALATE_REFERENCE))
        for token in (
            "ambiguous requirement",
            "attempt budget",
            "same-defect threshold",
            "irreversible",
            "risk assessment",
            "low-confidence",
            "narrow question",
            "reused, not re-gathered",
            "read-only",
            "recommended disposition",
            "does not accept in place of",
            "returns to the phase that asked",
            "fresh user approval",
            "no extra attempt",
            "never waives",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_reference_qualifies_its_cross_references_into_the_base(self) -> None:
        body = norm(read(ESCALATE_REFERENCE))
        for token in ("../skill.md", "§state machine and counters", "§phase contracts"):
            with self.subTest(token=token):
                self.assertIn(token, body)


class ReferencesBulletTest(unittest.TestCase):
    """The References list advertises the file without disturbing check→act."""

    def test_escalation_bullet_follows_check_and_act(self) -> None:
        text = read(BASE)
        check = text.index("- `references/check.md`")
        act = text.index("- `references/act.md`", check)
        escalate = text.index("- `references/escalate.md`", act)
        self.assertGreater(act, check)
        self.assertGreater(escalate, act)
        self.assertNotIn("escalate.md", text[check:act], "must stay outside the check bullet")

    def test_bullet_says_the_driver_reads_it_before_dispatch(self) -> None:
        text = read(BASE)
        start = text.index("- `references/escalate.md`")
        bullet = norm(text[start:text.index("\n\n", start)])
        for token in ("driver", "read before expert dispatch", "protocol with the input"):
            with self.subTest(token=token):
                self.assertIn(token, bullet)


if __name__ == "__main__":
    unittest.main()
