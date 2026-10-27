"""Contract guards for the PDCA state machine, the PLAN/DO split and the standalone forms.

These tests assert the *semantics* the family settled on, not prose snapshots:

* DO has exactly two outcomes — a completed candidate (→ CHECK) and "cannot finish"
  (→ ACT); there is no DO → PLAN path, not even through a candidate classifier;
* CHECK is mandatory only to accept a completed result; ACT finalizes both the
  accepted result and the honest `blocked`/`incomplete`/STOP outcome, and STOP is
  not a path beside ACT;
* PLAN defines the result contract and never prescribes DO's implementation
  actions, steps or commands; the frozen command set is the verification
  (acceptance-evidence) set and the machine lint is scoped to it;
* the incremental and collection forms ship a self-contained common contract, so
  neither needs the base SKILL loaded first, and the two copies do not drift.

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
PLAN_LINT = BASE / "scripts/plan_lint.py"
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
    def test_state_machine_declares_the_four_transitions(self) -> None:
        block = norm(read(SKILL))
        for edge in (
            "CHECK → DO   (implementation defect)",
            "CHECK → PLAN (contract/acceptance defect)",
            "DO → ACT     (cannot finish: blocked / incomplete / STOP)",
        ):
            with self.subTest(edge=edge):
                self.assertIn(norm(edge), block)

    def test_no_do_to_plan_candidate_classifier_survives(self) -> None:
        self.assertNotIn("DO → PLAN candidate", read(SKILL))
        self.assertIn("no direct DO → PLAN", read(SKILL))
        # The planner asset must not accept a DO-originated candidate either.
        planner = norm(read(ASSETS / "pdca-planner.md"))
        self.assertIn("DO never returns to PLAN", planner)
        self.assertIn("There is no DO → PLAN path", planner)

    def test_check_is_mandatory_only_for_a_completed_result(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn(
            "CHECK is mandatory to accept a completed result", skill
        )
        self.assertIn("it is not run for a candidate that DO already reports as blocked", skill)
        # DO → CHECK requires every active unit `done` with evidence.
        self.assertIn("A blocker report is **not** `done`", norm(read(SKILL)))

    def test_act_finalizes_both_outcomes_and_stop_is_an_act_outcome(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("**ACT finalizes** either the accepted result", skill)
        self.assertIn("STOP is an **ACT outcome**", skill)
        self.assertNotIn("a **separate terminal path**", skill)
        # Gate 6 is the honest finalization, not a bypass of the no-4th rule.
        self.assertIn("without bypassing the no-4th rule", skill)

    def test_do_failure_goes_to_act_with_residual_requirements(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn(
            "the driver goes **straight to ACT** (gate 3)", skill
        )
        self.assertIn("residual `unmet`/`unverified` requirements", skill)
        self.assertIn("No `PASS`, no `done`, no credit", skill)


class PlanDoesNotChooseActionsTest(unittest.TestCase):
    def test_plan_defines_the_result_contract_only(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("It does **not** prescribe implementation actions", skill)
        self.assertIn("the executor chooses the implementation", skill)

    def test_plan_reference_scopes_the_command_contract_to_verification(self) -> None:
        plan = norm(read(PLAN_REF))
        self.assertIn("**Scope — verification commands only.**", plan)
        self.assertIn("never freezes, prescribes or lints the implementation actions", plan)
        self.assertIn("implementation commands are not listed there, are not linted", plan)
        self.assertIn("**verification** command", plan)

    def test_gate_one_validates_verification_commands_only(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("every frozen **verification** command", skill)
        self.assertIn("never DO's implementation actions", skill)

    def test_planner_and_executor_assets_carry_the_scope(self) -> None:
        planner = norm(read(ASSETS / "pdca-planner.md"))
        executor = norm(read(ASSETS / "pdca-executor.md"))
        self.assertIn("never the steps or commands of DO's implementation", planner)
        self.assertIn("verification commands the plan freezes", planner)
        self.assertIn("DO's own implementation actions and commands are your choice", executor)

    def test_plan_lint_is_documented_as_a_verification_lint(self) -> None:
        script = norm(read(PLAN_LINT))
        self.assertIn("Static contract lint for a PDCA plan's frozen verification commands", script)
        self.assertIn("It never prescribes, freezes or forbids the implementation", script)


class StandaloneFormsTest(unittest.TestCase):
    REQUIRED = (
        "Entry and control mode",
        "Forms",
        "One loop",
        "Transition gates",
        "Roles and tiers",
        "Counters and history",
        "Claims and veto",
        "Evidence over assertion",
        "Verification",
        "Workspace and durable status",
        "Strategic revision and recovery",
        "Escalation and guardrails",
        "Effort and time policy",
        "Security and operating constraints",
        "Red flags (self-check)",
    )

    def contracts(self) -> dict[str, Path]:
        return {name: root / "references/common-contract.md" for name, root in FORMS.items()}

    def test_every_form_ships_a_common_contract(self) -> None:
        for name, path in self.contracts().items():
            with self.subTest(form=name):
                self.assertTrue(path.is_file(), f"{name} has no references/common-contract.md")

    def test_the_two_copies_do_not_drift(self) -> None:
        copies = self.contracts()
        incremental = copies["pdca-incremental"].read_bytes()
        collection = copies["pdca-collection"].read_bytes()
        self.assertEqual(incremental, collection, "common-contract copies diverged")

    def test_required_sections_are_present(self) -> None:
        for name, path in self.contracts().items():
            known = headings(path)
            for section in self.REQUIRED:
                with self.subTest(form=name, section=section):
                    self.assertIn(section, known, f"{name} common contract lacks §{section}")

    def test_common_contract_enumerates_the_six_gates(self) -> None:
        text = norm(read(self.contracts()["pdca-incremental"]))
        for gate in (
            "1. **PLAN → DO**",
            "2. **DO → CHECK**",
            "3. **DO → ACT**",
            "4. **CHECK → ACT**",
            "5. **ACT → EXIT**",
            "6. **ACT → STOP**",
        ):
            with self.subTest(gate=gate):
                self.assertIn(gate, text)

    def test_common_contract_carries_verification_rules(self) -> None:
        text = norm(read(self.contracts()["pdca-incremental"]))
        for rule in (
            "`met | unmet | unverified`",
            "The absence of a check is NOT a pass",
            "carrying claims",
            "forbids PASS and final `done`",
            "correction routing",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, text)

    def test_each_form_declares_it_does_not_need_the_base(self) -> None:
        for name, root in FORMS.items():
            with self.subTest(form=name):
                skill = norm(read(root / "SKILL.md"))
                self.assertIn("self-contained", skill.lower())
                self.assertIn(
                    "loading the base `../pdca/SKILL.md` first is not required", skill
                )

    def test_common_contract_citations_resolve(self) -> None:
        """Every contract citation must name a real section of its target.

        Scoped to the copied common contract and the base package references the
        forms cite; prose shorthand such as `§D.3` for a phase sub-block of the
        collection contract is not a section citation and is skipped.
        """
        problems: list[str] = []
        for name, root in FORMS.items():
            for path in sorted(
                [root / "SKILL.md", *sorted((root / "references").glob("*.md"))]
            ):
                text = read(path)
                for lineno, line in enumerate(text.splitlines(), 1):
                    for match in re.finditer(r"§([^\n`§]+)", line):
                        tail = match.group(1)
                        target = self._target(path, line[: match.start()])
                        if target is None or not target.is_file():
                            continue
                        if not self._in_scope(target, root):
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
    def _in_scope(target: Path, root: Path) -> bool:
        resolved = target.resolve()
        if resolved.name == "common-contract.md":
            return True
        return (SKILLS / "pdca") in resolved.parents

    @staticmethod
    def _clean(tail: str) -> str | None:
        cleaned = tail.strip().lstrip("`'\"( ").strip()
        cleaned = re.split(r",|;|\)|:|\s—\s", cleaned)[0].strip()
        cleaned = re.sub(r"\s+gate\s+\d+$", "", cleaned).strip(" `'\"().")
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
        """Nearest target before the `§`: the common contract or a cited file."""
        marker = max(
            before.rfind("common contract"), before.rfind("common-contract.md")
        )
        paths = list(re.finditer(r"`([^`]*?\.md)`", before))
        if paths and paths[-1].start() > marker:
            return (path.parent / paths[-1].group(1)).resolve()
        if marker >= 0:
            return path.parent / "references/common-contract.md"
        return None


if __name__ == "__main__":
    unittest.main()
