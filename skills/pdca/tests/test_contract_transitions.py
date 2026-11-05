"""Contract guards for the PDCA state machine, the PLAN/DO split and the forms.

These tests assert the *semantics* the family settled on, not prose snapshots:

* DO has exactly two outcomes — a completed candidate (→ CHECK) and "cannot finish"
  (→ ACT); there is no DO → PLAN path, not even through a candidate classifier;
* CHECK is mandatory only to accept a completed result; ACT finalizes both the
  accepted result and the honest `blocked`/`incomplete`/STOP outcome, and STOP is
  not a path beside ACT;
* PLAN defines the result contract and never prescribes DO's implementation
  actions or CHECK's verification method; the base reference no longer freezes
  implementation or verification commands;
* the incremental and collection forms inherit the base common contract instead of
  shipping a copied standalone contract, and the legacy copies are gone.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_contract_transitions.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
BASE = SKILLS / "pdca"
SKILL = BASE / "SKILL.md"
PLAN_REF = BASE / "references/plan.md"
ASSETS = BASE / "assets/opencode-agents"
FORMS = {
    "pdca-incremental": SKILLS / "pdca-incremental",
    "pdca-collection": SKILLS / "pdca-collection",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


def headings(path: Path) -> list[str]:
    return [
        re.sub(r"^[#]+\s+", "", line).replace("`", "").strip()
        for line in read(path).splitlines()
        if re.match(r"^#{2,4}\s+", line)
    ]


class StateMachineTest(unittest.TestCase):
    def test_state_machine_declares_the_current_transitions(self) -> None:
        block = norm(read(SKILL))
        for edge in (
            "DO → ACT (cannot finish)",
            "CHECK → DO (defect)",
            "CHECK → PLAN (contract)",
            "CHECK → ACT (STOP)",
            "PLAN → ACT (criteria undetermined | goal not measurable | requested result infeasible | requested result already established)",
        ):
            with self.subTest(edge=edge):
                self.assertIn(norm(edge), block)

    def test_no_do_to_plan_path_survives(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("**only CHECK returns to PLAN** (never DO)", skill)
        self.assertIn("does not rewrite the plan", skill)
        self.assertIn("does not return to PLAN", skill)
        # The planner's own transition rule lives in its phase reference, not in the agent asset.
        plan = norm(read(PLAN_REF))
        self.assertIn("DO never returns to PLAN", plan)
        self.assertIn("Only CHECK can send a contract defect back here", plan)
        planner = norm(read(ASSETS / "pdca-planner.md"))
        self.assertIn("plan_reference_path", planner)
        self.assertIn("§Output contract", planner)

    def test_check_is_mandatory_only_for_a_completed_result(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("**CHECK is mandatory to accept a completed result**", skill)
        self.assertIn(
            "never runs on a candidate DO reports as blocked or incomplete", skill
        )
        self.assertIn("a blocker report is not `done`", skill)

    def test_act_finalizes_both_outcomes_and_stop_is_an_act_outcome(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("**ACT finalizes**", skill)
        self.assertIn("STOP** is an **ACT outcome**", skill)
        self.assertNotIn("a **separate terminal path**", skill)
        self.assertIn("no bypass of the no-4th rule", skill)

    def test_do_failure_goes_to_act_with_residual_requirements(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("**DO → ACT** — DO cannot finish under the approved contract", skill)
        self.assertIn("residual `unmet`/`unverified` requirements", skill)
        self.assertIn("with no `PASS`, no `done` and no credit", skill)


class PlanDoesNotChooseActionsTest(unittest.TestCase):
    def test_plan_defines_the_result_contract_only(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn(
            "It prescribes neither implementation actions or a step-by-step DO", skill
        )
        self.assertIn("the executor chooses the implementation", skill)
        self.assertIn("nor verification methods, evidence sources or commands", skill)

    def test_plan_reference_scopes_itself_to_the_result_contract(self) -> None:
        plan = norm(read(PLAN_REF))
        self.assertIn(
            "does not prescribe a manifest row, an evidence source, a verification method or a script",
            plan,
        )
        self.assertIn("no pre-DO condition depends on them", plan)
        self.assertIn("no field and no instruction in this file names a verification procedure", plan)
        self.assertIn("DO chooses the implementation", plan)

    def test_do_handoff_carries_no_frozen_verification_procedure(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("no frozen verification procedure", skill)
        self.assertIn("Choosing, validating and running the verification is CHECK's work", skill)

    def test_planner_and_executor_assets_carry_the_scope(self) -> None:
        planner = norm(read(ASSETS / "pdca-planner.md"))
        plan = norm(read(PLAN_REF))
        executor = norm(read(ASSETS / "pdca-executor.md"))
        # The planner reads the procedure from its reference; the reference states the split.
        self.assertIn("plan_reference_path", planner)
        self.assertIn("PLAN fixes the **result contract**", plan)
        self.assertIn("DO chooses the implementation", plan)
        self.assertIn("Do not freeze a command, selector, test strategy or manifest row", plan)
        self.assertIn("DO's own implementation actions and commands are your choice", executor)

    def test_plan_lint_is_documented_as_a_verification_lint(self) -> None:
        script = norm(read(BASE / "scripts/plan_lint.py"))
        self.assertIn("Static contract lint for a PDCA plan's frozen verification commands", script)
        self.assertIn("It never prescribes, freezes or forbids the implementation", script)


class InheritanceTest(unittest.TestCase):
    """The forms inherit the base common contract; the copied contracts are gone."""

    def test_legacy_common_contract_copies_are_gone(self) -> None:
        for name, root in FORMS.items():
            with self.subTest(form=name):
                self.assertFalse(
                    (root / "references/common-contract.md").exists(),
                    f"{name} still ships a copied common contract",
                )
                self.assertFalse(
                    (root / "references").exists(),
                    f"{name} still ships a local references directory",
                )

    def test_each_form_declares_inheritance_from_the_base(self) -> None:
        for name, root in FORMS.items():
            with self.subTest(form=name):
                skill = norm(read(root / "SKILL.md"))
                self.assertIn("inherit", skill.lower())
                self.assertIn("../pdca/SKILL.md", skill)
                self.assertIn("§Common cycle contract", skill)
                self.assertIn("skip", skill)
                self.assertIn("classification", skill)

    REQUIRED = {
        "pdca-incremental": (
            "Inheritance: the base contract is the single source of the shared rules",
            "Campaign goal and measurement",
            "Campaign invariants",
            "Campaign status",
            "Campaign cycle",
            "Step boundary",
            "Stop",
            "Strategic revision and recovery",
        ),
        "pdca-collection": (
            "Inheritance",
            "Batch terminology",
            "Items and execution ownership",
            "Capability preflight",
            "Collection (P / D / C / A)",
            "Lane execution and schedule revision",
            "Collection status record",
            "Approval barrier (normal mode)",
            "Fallback",
        ),
    }

    def test_form_sections_are_present(self) -> None:
        for name, sections in self.REQUIRED.items():
            known = headings(FORMS[name] / "SKILL.md")
            for section in sections:
                with self.subTest(form=name, section=section):
                    self.assertIn(section, known, f"{name} lacks §{section}")

    def test_forms_do_not_restate_the_common_counters(self) -> None:
        # Form-local numeric rules would drift from the base. They may name the
        # counters by reference, but not define a second budget or threshold.
        for name, root in FORMS.items():
            with self.subTest(form=name):
                skill = norm(read(root / "SKILL.md"))
                self.assertIn("§State machine and counters", skill)
                self.assertNotIn("four counters, do not mix them", skill.lower())
                self.assertNotIn("n/3 is the", skill.lower())

    def test_common_contract_citations_resolve(self) -> None:
        """Every contract citation must name a real section of its target."""
        problems: list[str] = []
        for name, root in FORMS.items():
            for path in sorted([root / "SKILL.md"]):
                text = read(path)
                for lineno, line in enumerate(text.splitlines(), 1):
                    for match in re.finditer(r"§([^\n`§]+)", line):
                        tail = match.group(1)
                        target = self._target(path, line[: match.start()])
                        if target is None or not target.is_file():
                            continue
                        if not self._in_scope(target):
                            continue
                        cleaned = self._clean(tail)
                        if cleaned is None:
                            continue
                        if not self._matches(cleaned, headings(target)):
                            problems.append(
                                f"{path.relative_to(SKILLS)}:{lineno}: "
                                f"§{cleaned!r} not in {target.name}"
                            )
        self.assertEqual([], problems, "\n".join(problems))

    @staticmethod
    def _in_scope(target: Path) -> bool:
        resolved = target.resolve()
        return (SKILLS / "pdca") in resolved.parents or resolved == SKILL

    @staticmethod
    def _clean(tail: str) -> str | None:
        cleaned = tail.strip().lstrip("`'\"( ").strip()
        cleaned = re.split(r",|;|\)|:|\s—\s", cleaned)[0].strip()
        cleaned = re.sub(r"\s+(gate\s+)?\d+$", "", cleaned).strip(" `'\"().")
        if not cleaned or re.fullmatch(r"[A-Z](\d+(\.\d+)?)?", cleaned):
            return None  # prose shorthand (§C, §D.3), not a section name
        return cleaned

    @staticmethod
    def _matches(cleaned: str, known: list[str]) -> bool:
        for candidate in known:
            if cleaned == candidate:
                return True
            if candidate.startswith(cleaned) and len(cleaned) >= 4:
                return True
            if cleaned.startswith(candidate) and len(candidate) >= 6:
                return True
        return False

    @staticmethod
    def _target(path: Path, before: str) -> Path | None:
        """Nearest target before the `§`: a cited file, else the current skill."""
        paths = list(re.finditer(r"`([^`]*?\.md)`", before))
        if paths:
            return (path.parent / paths[-1].group(1)).resolve()
        return path


class CampaignFailureSemanticsTest(unittest.TestCase):
    """A failed step blocks the campaign; it never reboots or credits itself."""

    def setUp(self) -> None:
        self.skill = norm(read(FORMS["pdca-incremental"] / "SKILL.md"))

    def test_failed_step_is_blocked_and_not_credited(self) -> None:
        for phrase in (
            "the step is **not credited**",
            "the campaign is **blocked**",
            "neither reboots the step, nor erases history, nor earns an increment, nor advances to the next step",
            "no accepted increment, no auto-replan",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.skill)

    def test_stop_table_keeps_the_blocked_row_honest(self) -> None:
        self.assertIn(
            "the current step's DO cannot finish under the contract", self.skill
        )
        self.assertIn(
            "cause, evidence, residual requirements; no accepted increment, no auto-replan",
            self.skill,
        )

    def test_pause_is_not_a_terminal_status(self) -> None:
        self.assertIn("disposition: paused", self.skill)
        self.assertIn("A pause is not an outcome and not a terminal status", self.skill)

    def test_step_boundary_is_one_planner_call(self) -> None:
        self.assertIn("**one** planner call decides", self.skill)
        # The decision procedure and its accounting are the planner's phase reference.
        self.assertIn("references/plan.md` §Step boundary", self.skill)
        plan = norm(read(PLAN_REF))
        self.assertIn("separate DECIDE → brief → STOP turns on unchanged content are a repeated PLAN", plan)
        self.assertIn("1 + number of steps", plan)


if __name__ == "__main__":
    unittest.main()
