"""Contract guards for existing-test compatibility in the pdca-coder overlay."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


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


if __name__ == "__main__":
    unittest.main()
