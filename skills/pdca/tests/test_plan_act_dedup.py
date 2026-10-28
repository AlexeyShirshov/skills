"""Regression guards: the inline PLAN/ACT sections are caller contracts, not procedure.

Each phase's procedure and payload live once in its own reference (`plan.md` for
`pdca-planner`, `act.md` for `pdca-executor`); the base keeps reader boundary, transitions
with their gates, and who decides.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
BASE = SKILL_DIR / "SKILL.md"
PLAN_REFERENCE = SKILL_DIR / "references/plan.md"
ACT_REFERENCE = SKILL_DIR / "references/act.md"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


def raw_section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


BASE_TEXT = BASE.read_text(encoding="utf-8")
PLAN = norm(raw_section(BASE_TEXT, "#### PLAN", "#### DO"))
ACT = norm(raw_section(BASE_TEXT, "#### ACT", "### Evidence over assertion"))
PLAN_RAW = raw_section(BASE_TEXT, "#### PLAN", "#### DO")
ACT_RAW = raw_section(BASE_TEXT, "#### ACT", "### Evidence over assertion")


def check_present(case: unittest.TestCase, body: str, tokens: tuple[str, ...]) -> None:
    for token in tokens:
        with case.subTest(token=token):
            case.assertIn(token, body)


def check_absent(case: unittest.TestCase, body: str, tokens: tuple[str, ...]) -> None:
    for token in tokens:
        with case.subTest(token=token):
            case.assertNotIn(token, body)


def paragraph(prefix: str) -> str:
    for part in re.split(r"\n\s*\n", BASE_TEXT):
        if norm(part).startswith(prefix):
            return norm(part)
    raise AssertionError("no paragraph starting with %r" % prefix)

class PlanContractTest(unittest.TestCase):
    def test_reference_is_planner_read_from_the_base_path(self) -> None:
        check_present(self, PLAN, (
            "exact absolute path", "this base contract", "never from the loaded form contract",
            "plan_reference_path", "references/plan.md is pdca-planner only",
            "driver neither reads, inlines nor forwards",
            "never part of a do, check or pdca-escalate dispatch",
            "forwarded and recorded unchanged",
        ))

    def test_plan_prescribes_no_implementation_or_verification(self) -> None:
        check_present(self, PLAN, (
            "prescribes neither implementation actions or a step-by-step do",
            "the executor chooses the implementation",
            "nor verification methods, evidence sources or commands",
            "choosing, validating and running the verification is check's work",
        ))

    def test_do_handoff_keeps_its_gate(self) -> None:
        check_present(self, PLAN, (
            "only when that plan is complete", "no frozen verification procedure",
            "user's approval",
        ))

    def test_do_start_is_logged_and_an_indeterminate_criterion_routes_to_act(self) -> None:
        body = paragraph("plan → do")
        check_present(self, body, ("logs do started", "indeterminate criterion blocks do",
                                   "routes plan → act"))

    def test_terminal_labels_are_inline_but_their_payloads_are_not(self) -> None:
        check_present(self, PLAN, (
            "acceptance criteria cannot be determined",
            "original task is infeasible under the stated constraints",
            "requested result already established", "no mandatory escalation detour",
            "no substitute deliverable", "act finalizes without",
        ))
        check_absent(self, PLAN, (
            "carries the missing information", "carries cause and evidence",
            "carries the result, its derivation",
        ))
        reference = norm(PLAN_REFERENCE.read_text(encoding="utf-8"))
        check_present(self, reference, (
            "## terminal plan outcomes", "state-dependent",
            "one failed candidate is not proof", "never a ready placeholder",
            "missing mandatory coverage", "instead of a ready plan or do",
        ))


class ActContractTest(unittest.TestCase):
    def test_reader_boundary_and_authority(self) -> None:
        check_present(self, ACT, (
            "references/act.md", "status-file creation", "every status write",
            "no separate subagent role", "never its own verdict or approval",
            "changes no product, test or checked artifact",
        ))

    def test_exit_and_stop_gates(self) -> None:
        check_present(self, ACT, (
            "after an accepted check", "untouched accepted snapshot", "act outcome",
            "originating phase", "no permitted continuation", "no false pass",
            "no bypass of the no-4th rule",
        ))

    def test_terminal_closure_late_work_and_no_side_path(self) -> None:
        check_present(self, ACT, (
            "without do, check", "mandatory expert detour", "absence of an independent check",
            "goes back to do and a final check", "never beside it",
        ))

    def test_stop_grounds_and_payloads_live_only_in_the_reference(self) -> None:
        check_absent(self, ACT, ("refused required approval", "consultation alone", "defect history", "counters"))
        reference = norm(ACT_REFERENCE.read_text(encoding="utf-8"))
        check_present(self, reference, (
            "when stop is the outcome", "refused required approval", "no new plan",
        ))


class SectionBudgetTest(unittest.TestCase):
    # Trimmed: PLAN ~2315 B, ACT ~1217 B; the caps leave ~8% for a wording fix.
    MAX_PLAN_BYTES = 2500
    MAX_ACT_BYTES = 1350

    def test_sections_stay_caller_contracts(self) -> None:
        self.assertLessEqual(len(PLAN_RAW.encode("utf-8")), self.MAX_PLAN_BYTES)
        self.assertLessEqual(len(ACT_RAW.encode("utf-8")), self.MAX_ACT_BYTES)

    def test_phase_headings_keep_their_order(self) -> None:
        order = [BASE_TEXT.index(h) for h in ("#### PLAN", "#### DO", "#### CHECK", "#### ACT")]
        self.assertEqual(sorted(order), order)


if __name__ == "__main__":
    unittest.main()
