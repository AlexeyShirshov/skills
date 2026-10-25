"""Focused regression guards for the PDCA execution-repair contract.

Two layers, both deliberately small:

* **Phrase guards** over runtime text (base contract, references, canonical roles, the
  active EN/RU docs and the active diagram generators/assets). Text checks only.
* **A test-only structured trace auditor** over toy adapted fixtures. It checks declared
  transitions against the frozen plan (verification/scope/revision), the time-policy
  events (explicit opt-in, fresh approval ref, mode switch) and explicit evidence
  identity. It does not simulate a model, physics or the full cycle state machine, and it
  executes no cycle.

The premise labels in the fixture (``relationship_supported``, ``scope``) are declared by
human review, not physical truth. Unknown event types fail closed.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_execution_repair.py' -v
"""

from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILLS = REPO / "skills"
BASE = SKILLS / "pdca/SKILL.md"
PLAN_REF = SKILLS / "pdca/references/plan.md"
CHECK_REF = SKILLS / "pdca/references/check.md"
ACT_REF = SKILLS / "pdca/references/act.md"
ROLES = SKILLS / "pdca/assets/opencode-agents"
FIXTURE = Path(__file__).resolve().parent / "fixtures/execution_repair/cases.json"

ACTIVE_TEXT = [
    SKILLS / "pdca/SKILL.md",
    SKILLS / "pdca/references/plan.md",
    SKILLS / "pdca/references/check.md",
    SKILLS / "pdca/references/act.md",
    SKILLS / "pdca-coder/SKILL.md",
    SKILLS / "pdca-dotnet/SKILL.md",
    SKILLS / "pdca-collection/SKILL.md",
    SKILLS / "pdca-collection/references/lane.md",
    SKILLS / "pdca-incremental/SKILL.md",
    SKILLS / "pdca-incremental/references/status.md",
    SKILLS / "pdca/assets/opencode-agents/pdca-planner.md",
    SKILLS / "pdca/assets/opencode-agents/pdca-orchestrator.md",
    SKILLS / "pdca/assets/opencode-agents/pdca-executor.md",
    SKILLS / "pdca/assets/opencode-agents/pdca-check.md",
    SKILLS / "pdca/assets/opencode-agents/pdca-escalate.md",
    REPO / "docs/pdca.md",
    REPO / "docs/pdca-guide.md",
    REPO / "docs/pdca-coder.md",
    REPO / "docs/pdca-collection.md",
    REPO / "docs/pdca-dotnet.md",
    REPO / "docs/pdca-incremental.md",
    REPO / "docs/ru/pdca.md",
    REPO / "docs/ru/pdca-guide.md",
    REPO / "docs/ru/pdca-coder.md",
    REPO / "docs/ru/pdca-collection.md",
    REPO / "docs/ru/pdca-dotnet.md",
    REPO / "docs/ru/pdca-incremental.md",
    REPO / "docs/ru/pdca-slides/slides.md",
]

DIAGRAM_GENERATORS = (
    SKILLS / "pdca/assets/diagram/gen_pdca.py",
    SKILLS / "pdca-coder/assets/diagram/gen_pdca.py",
    SKILLS / "pdca-dotnet/assets/diagram/gen_pdca.py",
)

VIOLATION_ROUTE = {
    "unauthorized_plan_drift": "plan_return",
    "scope_drift": "plan_return",
    "missing_return_before_rewrite": "plan_return",
    "normal_stop_without_optin": "need_plan_return",
    "autonomous_terminal_stop": "need_plan_return",
    "command_timeout_as_workflow_stop": "need_plan_return",
    "unknown_event": "need_plan_return",
    "invalid_inference": "finding",
    "family_entry_is_not_form": "finding",
    "stale_approval_ref": "plan_return",
}

EVENT_TYPES = {
    "entry",
    "dispatch",
    "plan_revision",
    "plan_approved",
    "observation",
    "rewrite",
    "claim",
    "estimate",
    "user_stop",
    "mode_switch",
    "legacy_budget",
    "command_timeout",
    "accepted_result",
    "terminal_stop",
    "resume",
    "replan",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip()


def audit(case: dict) -> dict:
    """Check declared transitions against the frozen plan; no expected-label input."""
    mode = case["mode"]
    plan = copy.deepcopy(case["plan"])
    cutoff = {"enabled": False, "ignored": False}
    violations: list[str] = []
    outcome = "continue"
    refuted = None
    failed_commands = 0
    estimate = None

    for event in case["events"]:
        kind = event.get("type")
        if kind not in EVENT_TYPES:
            violations.append("unknown_event")
            continue
        if kind == "entry":
            if event.get("named") == "pdca" and event.get("asserted_form"):
                violations.append("family_entry_is_not_form")
        elif kind == "dispatch":
            # The frozen plan's method is authoritative. A revision field on the dispatch
            # is a claim, not a PLAN event: only a plan_revision event may change the method.
            if event.get("verification") != plan.get("verification"):
                violations.append("unauthorized_plan_drift")
            scope = set(event.get("scope") or [])
            if scope and not scope <= set(plan.get("scope") or []):
                violations.append("scope_drift")
        elif kind == "plan_revision":
            old_ref = plan.get("approval_ref")
            new_ref = event.get("approval_ref")
            if new_ref == old_ref:
                violations.append("stale_approval_ref")
            plan.update({
                "revision": event["revision"],
                "verification": event.get("verification", plan.get("verification")),
                "scope": event.get("scope", plan.get("scope")),
                "approval_ref": new_ref,
            })
            if "estimate" in event:
                estimate = event["estimate"]
            # A genuine replan gets a fresh ref; the surviving user cutoff is carried
            # by reference with its original minutes/anchor, not the new estimate.
            if cutoff.get("enabled") and not cutoff.get("ignored"):
                cutoff["ref"] = new_ref
            refuted = None
        elif kind == "observation" and event.get("refutes"):
            refuted = plan.get("revision")
        elif kind == "rewrite":
            if refuted is not None and refuted == plan.get("revision"):
                violations.append("missing_return_before_rewrite")
        elif kind == "claim":
            if event.get("conclusion") == "goal_impossible" and (
                event.get("scope") != "goal" or not event.get("relationship_supported")
            ):
                violations.append("invalid_inference")
        elif kind == "estimate":
            estimate = event.get("minutes")
        elif kind == "plan_approved":
            pass  # plan approval is never a cutoff opt-in
        elif kind == "user_stop":
            if mode == "autonomous":
                violations.append("autonomous_terminal_stop")
            elif event.get("answer") == "yes":
                cutoff = {"enabled": True, "minutes": estimate, "anchor": "T0",
                          "ref": plan.get("approval_ref"), "ignored": False}
            else:
                cutoff = {"enabled": False, "ignored": False}
        elif kind == "mode_switch":
            mode = event["mode"]
            if mode == "autonomous" and cutoff.get("enabled"):
                cutoff = {"enabled": False, "ignored": True}
            elif mode == "normal":
                # An explicit return does not silently revive the stale choice.
                cutoff = {"enabled": False, "ignored": True}
        elif kind == "legacy_budget":
            pass  # accounting only; any terminal use is caught below
        elif kind == "command_timeout":
            failed_commands += 1  # failed-command evidence, not a workflow STOP
        elif kind == "accepted_result":
            if event.get("verification") != plan.get("verification"):
                violations.append("unauthorized_plan_drift")
            outcome = "done"
        elif kind == "terminal_stop":
            reason = event.get("reason")
            if mode == "autonomous":
                if reason in ("estimate", "elapsed", "token_budget", "legacy_budget", "revision_total"):
                    violations.append("autonomous_terminal_stop")
                elif reason == "blocker" and event.get("verified") is True:
                    outcome = "stopped_blocker"
                elif reason == "accepted_result":
                    outcome = "done"
            else:
                if reason == "estimate":
                    if cutoff.get("enabled") and not cutoff.get("ignored") and event.get("approval_ref") == cutoff.get("ref"):
                        outcome = "stopped_estimate"
                    else:
                        violations.append("normal_stop_without_optin")
                elif reason == "blocker" and event.get("verified") is True:
                    outcome = "stopped_blocker"
                elif reason == "accepted_result":
                    outcome = "done"

    if violations:
        outcome = VIOLATION_ROUTE[violations[0]]
    return {"outcome": outcome, "violations": violations, "cutoff": cutoff,
            "failed_commands": failed_commands}


class TraceAuditorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = {case["id"]: case for case in json.loads(read(FIXTURE))["cases"]}

    def test_declared_transitions_match_the_human_expected_route(self) -> None:
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                result = audit(case)
                expected = case["expected"]
                self.assertEqual(expected["violations"], result["violations"])
                self.assertEqual(expected["outcome"], result["outcome"])
                if "cutoff" in expected:
                    self.assertEqual(expected["cutoff"], result["cutoff"])
                if "failed_commands" in expected:
                    self.assertEqual(expected["failed_commands"], result["failed_commands"])

    def test_a_dispatch_cannot_license_a_new_method_by_claiming_a_revision(self) -> None:
        for case_id in ("manual-plan-checker-claims-same-revision",
                        "manual-plan-checker-claims-unrecorded-new-revision"):
            with self.subTest(case=case_id):
                result = audit(copy.deepcopy(self.cases[case_id]))
                self.assertIn("unauthorized_plan_drift", result["violations"])
        # The genuinely revised checker case still passes.
        self.assertEqual([], audit(copy.deepcopy(self.cases["checker-authorized-by-plan-revision"]))["violations"])

    def test_a_good_trace_becomes_bad_only_through_the_checked_transition(self) -> None:
        clean = copy.deepcopy(self.cases["checker-authorized-by-plan-revision"])
        self.assertEqual([], audit(clean)["violations"])
        drifted = copy.deepcopy(clean)
        drifted["events"].append({"type": "dispatch", "verification": "manual", "scope": ["answer"]})
        # The frozen plan was revised to a checker; a manual dispatch is now the drift.
        result = audit(drifted)
        self.assertIn("unauthorized_plan_drift", result["violations"])
        self.assertEqual("plan_return", result["outcome"])
        # The input fixture is not mutated by auditing.
        self.assertEqual([], audit(clean)["violations"])

    def test_removing_the_return_breaks_the_fixed_trace(self) -> None:
        fixed = copy.deepcopy(self.cases["refuted-assumption-returned-before-rewrite"])
        del fixed["events"][1]
        result = audit(fixed)
        self.assertIn("missing_return_before_rewrite", result["violations"])
        self.assertEqual("plan_return", result["outcome"])

    def test_unknown_event_is_a_failure_not_a_silent_skip(self) -> None:
        case = copy.deepcopy(self.cases["unknown-event-fails-closed"])
        self.assertEqual(["unknown_event"], audit(case)["violations"])
        self.assertEqual("need_plan_return", audit(case)["outcome"])

    def test_cutoff_survives_new_ref_and_estimate_without_renwal(self) -> None:
        case = self.cases["normal-optin-survives-new-plan-ref-and-estimate"]
        result = audit(case)
        self.assertTrue(result["cutoff"]["enabled"])
        self.assertEqual(45, result["cutoff"]["minutes"])
        self.assertEqual("T0", result["cutoff"]["anchor"])
        self.assertEqual("A2", result["cutoff"]["ref"])


class PolicyTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = norm(read(BASE))
        cls.plan = norm(read(PLAN_REF))
        cls.check = norm(read(CHECK_REF))
        cls.act = norm(read(ACT_REF))

    def test_base_keeps_completion_and_no_cutoff_together(self) -> None:
        for phrase in (
            "No autonomous cutoff",
            "estimate is not a stop condition",
            "Work ends on an accepted result",
            "Failed candidates or incomplete evidence are not blockers",
            "plan approval is not that opt-in",
            "persists as the same cutoff across normal-mode resume/replan",
            "only a switch to autonomous drops it",
            "No-4th and recurrence stay per defect",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.base)

    def test_effort_semantics_and_cutoff_reference_carry(self) -> None:
        for phrase in (
            "Work ends normally on an accepted result and goal completion",
            "A failed candidate or incomplete evidence is not an irreducible blocker",
            "Approving the plan is not opting into that stop",
            "persists as the same cutoff across a normal-mode resume",
            "fresh approval",
            "original clock",
            "by reference",
            "Only switching to autonomous mode drops it",
            "not an unconditional feasibility gate",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.plan)

    def test_act_and_runner_carry_the_cutoff_by_reference(self) -> None:
        runner = norm(read(ROLES / "pdca-orchestrator.md"))
        for phrase in (
            "original user stop choice and its original clock anchor/deadline by reference",
            "fresh approval ref",
            "old plan approval never authorizes the new plan",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runner)
        for phrase in ("original stop choice", "original clock", "No extra field or table"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.act)

    def test_entry_and_planner_exclude_bare_pdca_as_a_form(self) -> None:
        runner = norm(read(ROLES / "pdca-orchestrator.md"))
        planner = norm(read(ROLES / "pdca-planner.md"))
        self.assertIn("a bare pdca is family entry only", runner)
        self.assertIn("Naming pdca alone is family entry only", planner)
        self.assertIn("not a requested ordinary cycle", planner)

    def test_plan_reference_has_plan_to_do_fidelity_and_premises(self) -> None:
        for phrase in (
            "every follow-up DO handoff",
            "the executor returns the exact mismatch",
            "refuted assumption or wrong method",
            "does not reinterpret the goal",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.plan)
        for phrase in (
            "central definitions, units, model assumptions and inference scope",
            "an invalid equality or an assumed relationship",
            "limits that class only",
            "diagnostic_nonbinding",
            "A denied specific operation proves only that the operation was rejected",
            "never waive a genuine required test, security check or direct evidence",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.check)

    def test_roles_carry_the_follow_up_and_premise_duties(self) -> None:
        planner = norm(read(ROLES / "pdca-planner.md"))
        executor = norm(read(ROLES / "pdca-executor.md"))
        check = norm(read(ROLES / "pdca-check.md"))
        self.assertIn("newly refuted assumption or wrong method", planner)
        self.assertIn("before dependent artefacts are rewritten", planner)
        self.assertIn("planned assumption or method is refuted", executor)
        self.assertIn("Validate the premises before the arithmetic", check)
        self.assertIn("class or prototype limits that class", check)

    def test_incremental_planner_calls_are_accounting_not_a_cap(self) -> None:
        incremental = norm(read(SKILLS / "pdca-incremental/SKILL.md"))
        self.assertIn("Planner calls are accounted, not capped", incremental)
        self.assertIn("1 + number of steps", incremental)
        self.assertNotIn("at most 1 + number of steps", incremental)

    def test_active_runtime_text_has_no_stop_loss_or_cutoff_alias(self) -> None:
        banned = ("stop-loss", "stop loss budget", "Budget: <wall clock",
                  "budgets are fixed", "budget exhaustion")
        for path in ACTIVE_TEXT:
            text = read(path).lower()
            for phrase in banned:
                with self.subTest(path=str(path.relative_to(REPO)), phrase=phrase):
                    self.assertNotIn(phrase.lower(), text)

    def test_diagram_generators_and_active_assets_have_no_stop_loss(self) -> None:
        for path in DIAGRAM_GENERATORS:
            with self.subTest(generator=str(path.relative_to(REPO))):
                self.assertNotIn("stop-loss", read(path).lower())
        for path in sorted((SKILLS / "pdca/assets/diagram").iterdir()):
            if path.is_file() and path.suffix in (".svg", ".html"):
                with self.subTest(asset=path.name):
                    self.assertNotIn("stop-loss", read(path).lower())
        for path in sorted((REPO / "docs/ru/pdca-slides/public").iterdir()):
            if path.suffix == ".svg":
                with self.subTest(public=path.name):
                    self.assertNotIn("stop-loss", read(path).lower())

    def test_base_stays_under_its_existing_compact_ceiling(self) -> None:
        self.assertLessEqual(BASE.stat().st_size, 40960)
        self.assertGreater(BASE.stat().st_size, 30000)

    def test_follow_up_do_is_bound_in_the_gate_not_only_at_admission(self) -> None:
        self.assertIn("Every DO handoff, initial or follow-up", self.base)
        self.assertIn("exact mismatch to the planner, not obeyed", self.base)
        self.assertIn("before dependent artefacts are rewritten", self.base)


if __name__ == "__main__":
    unittest.main()
