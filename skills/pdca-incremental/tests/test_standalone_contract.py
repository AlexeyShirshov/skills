"""The incremental contract is standalone: its common rules ship with it.

`pdca-incremental` may be invoked directly, so it must not need the base
`pdca` SKILL loaded first. These guards keep the local common contract complete
(gates, roles, counters, claims, evidence, verification, status, approval,
recovery, escalation, effort, security) and keep the campaign-specific failure
semantics honest: a DO that cannot finish terminates the step blocked, with no
credit, no CHECK detour, no planner continuation and no next step.

Run:
    python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_standard*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
FAMILY = SKILL_DIR.parent
SKILL = SKILL_DIR / "SKILL.md"
CONTRACT = SKILL_DIR / "references/common-contract.md"
SIBLING = FAMILY / "pdca-collection/references/common-contract.md"

REQUIRED_SECTIONS = (
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


class StandaloneLoadTest(unittest.TestCase):
    def test_contract_ships_with_the_form(self) -> None:
        self.assertTrue(CONTRACT.is_file(), "references/common-contract.md missing")
        self.assertGreater(len(read(CONTRACT).splitlines()), 150, "the copy is a stub, not a contract")

    def test_required_sections_are_present(self) -> None:
        known = headings(CONTRACT)
        for section in REQUIRED_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, known, f"common contract lacks §{section}")

    def test_copies_are_identical_across_forms(self) -> None:
        self.assertTrue(SIBLING.is_file(), "collection copy missing")
        self.assertEqual(
            CONTRACT.read_bytes(), SIBLING.read_bytes(), "common-contract copies diverged"
        )

    def test_the_skill_declares_the_load_order_without_the_base(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("loading the base `../pdca/SKILL.md` first is not required", skill)
        self.assertIn("This file, then `references/common-contract.md`", skill)
        self.assertIn("the base `../pdca/SKILL.md` is optional deeper detail", skill)

    def test_the_contract_carries_the_gates_and_counters(self) -> None:
        contract = norm(read(CONTRACT))
        for token in (
            "1. **PLAN → DO**",
            "2. **DO → CHECK**",
            "3. **DO → ACT**",
            "4. **CHECK → ACT**",
            "5. **ACT → EXIT**",
            "6. **ACT → STOP**",
            "`n/3`",
            "no 4th attempt",
            "defect key",
            "`Pending approval ref`",
            "Never bypass, escalate around or spoof a permission",
        ):
            with self.subTest(token=token):
                self.assertIn(token, contract)

    def test_the_contract_reuses_sibling_helpers_by_explicit_path(self) -> None:
        contract = norm(read(CONTRACT))
        self.assertIn("reused **by explicit path**", contract)
        self.assertIn("../../pdca/scripts/plan_lint.py", contract)

    def test_common_contract_citations_resolve(self) -> None:
        problems: list[str] = []
        for path in [SKILL, *sorted((SKILL_DIR / "references").glob("*.md"))]:
            for lineno, line in enumerate(read(path).splitlines(), 1):
                if "common contract" not in line and "common-contract.md" not in line:
                    continue
                for match in re.finditer(r"§([^\n`§]+)", line):
                    name = re.split(r",|;|\)|:|\s—\s", match.group(1))[0].strip(" `'\"().")
                    if not name:
                        continue
                    if not any(
                        name == heading
                        or (heading.startswith(name) and len(name) >= 4)
                        or (name.startswith(heading) and len(heading) >= 4)
                        for heading in headings(CONTRACT)
                    ):
                        problems.append(f"{path.name}:{lineno}: §{name!r}")
        self.assertEqual([], problems, "\n".join(problems))


class CampaignFailureSemanticsTest(unittest.TestCase):
    def test_no_do_to_plan_detour_in_the_campaign(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("A DO that **cannot finish** makes no CHECK and no planner detour", skill)
        self.assertIn("it goes `DO → ACT`", skill)
        self.assertNotIn("DO → PLAN", read(SKILL))

    def test_failed_step_is_blocked_and_not_credited(self) -> None:
        skill = norm(read(SKILL))
        for phrase in (
            "The step is **not credited**",
            "the campaign is **blocked** with that residual work",
            "a DO failure never earns an accepted increment",
            "never auto-replans",
            "never advances to the next step",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)

    def test_stop_table_keeps_the_blocked_row_honest(self) -> None:
        stop = read(SKILL).split("## Stop", 1)[1].split("\n## ", 1)[0]
        self.assertIn("the DO of the current step cannot finish under the contract", stop)
        self.assertIn("no accepted increment", stop)
        self.assertIn("Every non-`met` row is finalized **in ACT**", stop)

    def test_campaign_rules_survive_the_common_rules(self) -> None:
        # The bounded-cycle rules are not allowed to flatten the campaign layer.
        skill = norm(read(SKILL))
        for rule in (
            "One credited increment per step",
            "no rule demands a second increment",
            "## Step boundary",
            "disposition=paused",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, skill)


if __name__ == "__main__":
    unittest.main()
