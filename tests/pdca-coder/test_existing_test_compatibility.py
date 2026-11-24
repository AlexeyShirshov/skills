"""Contract guards for existing-test compatibility in the pdca-coder overlay."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[2] / "skills"
SKILL = SKILLS / "pdca-coder/SKILL.md"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


def heading_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == heading),
        None,
    )
    if start is None:
        raise AssertionError(f"missing heading: {heading}")
    level = len(heading) - len(heading.lstrip("#"))
    end = next(
        (
            index for index in range(start + 1, len(lines))
            if lines[index].startswith("#")
            and len(lines[index]) - len(lines[index].lstrip("#")) <= level
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


class ExistingTestCompatibilityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.contract = normalize(heading_section(cls.skill, "## Existing-test compatibility"))

    def test_default_mode_is_backward_compatible_and_baseline_persists(self) -> None:
        for rule in (
            "compatibility mode is independent of normal/autonomous control mode",
            "unless the user explicitly selects non-backward-compatible, use backward-compatible",
            "an absent or unclear choice, autonomy, and general plan approval do not authorize changes to existing tests",
            "the baseline is the unit and integration tests present when the user task starts",
            "preserve that same baseline through retries, replans and step cycles of the same task",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.contract)

    def test_authorization_is_bounded_and_new_tests_are_allowed(self) -> None:
        for rule in (
            "do not change, delete, skip, disable or weaken them",
            "directly or indirectly through fixtures, shared helpers, snapshots or configuration",
            "adding tests is allowed, including in an existing file, while leaving its baseline tests unchanged",
            "explicit user consent authorizes only the named tests and agreed change scope",
            "it does not switch modes or permit further changes",
            "only the user's explicit non-backward-compatible choice selects that mode",
            "it does not relax acceptance or quality criteria",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.contract)

    def test_unapproved_existing_test_change_stops_do(self) -> None:
        for rule in (
            "if the requested result cannot be achieved in backward-compatible mode without an existing-test change outside explicit consent",
            "stop do before making that change",
            "return cannot finish through the base do→act route with the cause, evidence, affected tests and exact user decision needed",
            "act records stop under its contract",
            "no autonomous workaround or escalation can waive this boundary",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.contract)

    def test_unapproved_public_contract_change_stops_compatible_do(self) -> None:
        for rule in (
            "in backward-compatible mode, a required change to an existing public signature, format or guaranteed observable behavior needs explicit user authorization",
            "a clear instruction in the task itself can authorize that change",
            "in this mode, permission to change the public contract does not cover existing-test edits",
            "test authorization does not cover public-contract changes",
            "additive work that preserves existing guarantees does not need this extra decision",
            "use the same stop as soon as a required, unauthorized public-contract change is established, before changing the contract",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.contract)

    def test_incompatible_mode_authorizes_both_changes_without_repeat_confirmation(self) -> None:
        self.assertIn(
            "the choice authorizes changes to the existing public contract and baseline tests "
            "within the task scope without separate confirmation",
            self.contract,
        )
        self.assertIn("or override an explicit preservation requirement", self.contract)

    def test_mode_baseline_and_permission_travel_and_check_verifies(self) -> None:
        for rule in (
            "plan records the mode, a reference to the task-start baseline, and the source and exact scope of any explicit permission",
            "then passes them unchanged to do",
            "do preserves them and passes them with the candidate identity and evidence to check",
            "check evaluates a baseline comparison produced in place",
            "not the test files or a copied diff",
            "cover each existing-test change against the selected mode and explicit permission",
            "a missing baseline or authorization is not proof of permission or a pass",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.contract)

    def test_status_uses_base_record_and_lists_required_details(self) -> None:
        for rule in (
            "in the existing base status record, reference the baseline and record the mode and its authorization basis",
            "in backward-compatible mode also record any explicit user consent and its scope",
            "in non-backward-compatible mode, name each changed existing test, the nature of its change and the reason",
            "preserve these records across retries, replans and step cycles of the same task",
            "use the base status shape: no new schema, section or status file",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.contract)

    def test_phase_entry_points_reach_the_authoritative_section(self) -> None:
        entry_points = (
            "## Code-specific plan deltas",
            "## Code-specific check deltas",
            "### Parallel DO streams",
            "### Status, ACT and handoff additions",
        )
        for start in entry_points:
            with self.subTest(phase=start):
                content = normalize(heading_section(self.skill, start))
                self.assertIn("existing-test compatibility", content)


class CompatibilityDecisionRoutingTest(unittest.TestCase):
    def test_terminal_plan_reports_the_actual_conflict_without_inventing_criteria_or_edits(self) -> None:
        plan = (SKILLS / "pdca/references/plan.md").read_text(encoding="utf-8")
        terminal = normalize(heading_section(plan, "## Terminal PLAN outcomes"))
        for rule in (
            "return the applicable terminal outcome rather than a ready plan",
            "an explicit non-backward-compatible choice already authorizes in-scope contract and test changes",
            "distinguish an uncovered preservation requirement from a proven need to change behavior or a test",
            "return the decision needed to the driver; plan does not solicit it",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, terminal)

    def test_primary_asks_for_a_scoped_choice_without_bypassing_the_stop(self) -> None:
        act = (SKILLS / "pdca/references/act.md").read_text(encoding="utf-8")
        decision = normalize(heading_section(act, "### User decision on compatibility"))
        for rule in (
            "when a plan or do report says compatibility needs a user decision, record the outcome as usual",
            "the primary asks the user directly in the dialogue language, in either control mode",
            "wait for explicit user instruction before dispatching the affected work again",
            "lead with the choice, not with stop",
            "keep the existing contract, behavior and tests, and revise or clarify the task requirements",
            "approve the specific change needed for the requested result",
            "ask only for authorization still missing",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, decision)

        driver = (SKILLS / "pdca/references/driver.md").read_text(encoding="utf-8")
        routed = normalize(heading_section(driver, "## Routed, not taken"))
        self.assertIn("relay act's compatibility question to your caller; the primary asks the user", routed)

    def test_collection_reaches_the_same_user_decision_without_changing_queue_rules(self) -> None:
        collection = (SKILLS / "pdca-collection/SKILL.md").read_text(encoding="utf-8")
        report = normalize(heading_section(collection, "## Report"))
        for rule in (
            "relay it to the primary with the item id",
            "#user-decision-on-compatibility",
            "the barrier and lane rules still govern the other items",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, report)


if __name__ == "__main__":
    unittest.main()
