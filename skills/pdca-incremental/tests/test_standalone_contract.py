"""The incremental form inherits the base common contract instead of copying it.

`pdca-incremental` may be invoked directly, so it must load the base common rules
with it and skip only the entry classification. These guards keep the inheritance
honest, keep the campaign sections present, and keep the campaign-specific failure
semantics: a DO that cannot finish terminates the step blocked, with no credit, no
CHECK detour, no planner continuation and no next step.

Run:
    python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
FAMILY = SKILL_DIR.parent
SKILL = SKILL_DIR / "SKILL.md"
BASE = FAMILY / "pdca/SKILL.md"
SIBLING = FAMILY / "pdca-collection/SKILL.md"

CAMPAIGN_SECTIONS = (
    "Inheritance: the base contract is the single source of the shared rules",
    "When to use",
    "Probe, increment and step",
    "Campaign goal and measurement",
    "Step and counters",
    "Campaign invariants",
    "Campaign status",
    "Preparation record",
    "Baseline record",
    "Checkpoint",
    "Campaign cycle",
    "0. Bootstrap (once)",
    "1. Discovery (before each step)",
    "2. Step brief",
    "3. Step execution",
    "Step boundary",
    "Acceptance and carry-over",
    "Claims and veto",
    "Stop",
    "Effort accounting and safety",
    "Strategic revision and recovery",
    "Economics and sizing",
    "Red flags (campaign-specific)",
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


class InheritanceLoadTest(unittest.TestCase):
    def test_no_local_common_contract_copy(self) -> None:
        self.assertFalse((SKILL_DIR / "references/common-contract.md").exists())
        self.assertFalse((SKILL_DIR / "references/status.md").exists())
        self.assertFalse((SKILL_DIR / "references").exists())

    def test_the_form_declares_inheritance_and_direct_load(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("The **common cycle contract**", skill)
        self.assertIn("in `../pdca/SKILL.md`", skill)
        self.assertIn("inherits", skill.lower())
        self.assertIn(
            "A direct load — the user named `pdca-incremental` — loads the base common rules and **skips the entry classification**",
            skill,
        )
        self.assertIn("../pdca/SKILL.md", read(SKILL))

    def test_campaign_sections_are_present(self) -> None:
        known = headings(SKILL)
        for section in CAMPAIGN_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, known, f"incremental skill lacks §{section}")

    def test_the_form_does_not_restate_the_common_counters(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("§State machine and counters", skill)
        self.assertNotIn("four counters, do not mix them", skill.lower())

    def test_shared_rules_are_referenced_not_copied(self) -> None:
        skill = norm(read(SKILL))
        for token in (
            "roles, permissions and tiers",
            "normal/autonomous modes and the approval protocol",
            "safety, effort, recovery, workspace and status bookkeeping",
            "base recovery rules apply",
            "the original task is immutable here too",
        ):
            with self.subTest(token=token):
                self.assertIn(token.lower(), skill.lower())

    def test_campaign_contract_citations_resolve(self) -> None:
        problems: list[str] = []
        known = headings(SKILL) + headings(BASE)
        for path in [SKILL]:
            for lineno, line in enumerate(read(path).splitlines(), 1):
                for match in re.finditer(r"§([^\n`§]+)", line):
                    name = re.split(r",|;|\)|:|\s—\s", match.group(1))[0].strip(" `'\"().")
                    if not name or re.fullmatch(r"[A-Z](\d+(\.\d+)?)?", name):
                        continue
                    if not any(
                        name == heading
                        or (heading.startswith(name) and len(name) >= 4)
                        or (name.startswith(heading) and len(heading) >= 4)
                        for heading in known
                    ):
                        problems.append(f"{path.name}:{lineno}: §{name!r}")
        self.assertEqual([], problems, "\n".join(problems))


class CampaignFailureSemanticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = norm(read(SKILL))

    def test_no_do_to_plan_detour_in_the_campaign(self) -> None:
        self.assertNotIn("DO → PLAN", read(SKILL))
        self.assertIn("goes straight `DO → ACT`", self.skill)
        self.assertIn("is not a planner decision and not a CHECK", self.skill)

    def test_failed_step_is_blocked_and_not_credited(self) -> None:
        for phrase in (
            "the step is **not credited**",
            "the campaign is **blocked** with that residual work",
            "neither reboots the step, nor erases history, nor earns an increment, nor advances to the next step",
            "no accepted increment, no auto-replan",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.skill)

    def test_stop_table_keeps_the_blocked_row_honest(self) -> None:
        stop = read(SKILL).split("## Stop", 1)[1].split("\n## ", 1)[0]
        self.assertIn("the current step's DO cannot finish under the contract", stop)
        self.assertIn("no accepted increment", stop)
        self.assertIn("Every non-`met` row is finalized **in ACT**", stop)

    def test_campaign_rules_survive_the_common_rules(self) -> None:
        for rule in (
            "One credited increment per step",
            "no rule demands a second increment",
            "### Step boundary",
            "disposition: paused",
            "the whole-goal CHECK",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.skill)


if __name__ == "__main__":
    unittest.main()
