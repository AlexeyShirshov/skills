"""The collection contract is standalone and its non-PASS ACT is honest.

`pdca-collection` may be invoked directly, so its common rules ship locally. The
batch layer on top must keep the campaign/item machinery (barrier, lanes, per-item
forms) and must never turn an `incomplete` terminal outcome into a success:
non-PASS ACT preserves lanes, worktrees, branches and patches and performs no
cleanup.

Run:
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_standalone_contract.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
FAMILY = SKILL_DIR.parent
SKILL = SKILL_DIR / "SKILL.md"
CONTRACT = SKILL_DIR / "references/common-contract.md"
SIBLING = FAMILY / "pdca-incremental/references/common-contract.md"

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
        self.assertTrue(SIBLING.is_file(), "incremental copy missing")
        self.assertEqual(
            CONTRACT.read_bytes(), SIBLING.read_bytes(), "common-contract copies diverged"
        )

    def test_the_skill_is_self_contained(self) -> None:
        skill = norm(read(SKILL))
        self.assertIn("This contract is **self-contained**", skill)
        self.assertIn("loading the base `../pdca/SKILL.md` first is not required", skill)
        self.assertIn("the base `../pdca/SKILL.md` is optional deeper detail", skill)

    def test_no_do_to_plan_and_act_finalizes_non_pass(self) -> None:
        contract = norm(read(CONTRACT))
        self.assertIn("There is no DO → PLAN", contract)
        self.assertIn("**STOP is an ACT outcome**", contract)
        skill = norm(read(SKILL))
        self.assertIn("a `blocked`/`incomplete`/`STOP` outcome is finalized by the same ACT", skill)

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
                    if not self._targets_contract(line[: match.start()]):
                        continue
                    if not any(
                        name == heading
                        or (heading.startswith(name) and len(name) >= 4)
                        or (name.startswith(heading) and len(heading) >= 4)
                        for heading in headings(CONTRACT)
                    ):
                        problems.append(f"{path.name}:{lineno}: §{name!r}")
        self.assertEqual([], problems, "\n".join(problems))

    @staticmethod
    def _targets_contract(before: str) -> bool:
        """True when the nearest `§` target is the local common contract."""
        marker = max(before.rfind("common contract"), before.rfind("common-contract.md"))
        if marker < 0:
            return False
        cited = list(re.finditer(r"`([^`]*?\.md)`", before))
        return not cited or cited[-1].start() < marker


class IncompleteActTest(unittest.TestCase):
    def test_no_pass_means_no_success_and_no_cleanup(self) -> None:
        act = norm(read(SKILL).split("### A — completion", 1)[1].split("\n## ", 1)[0])
        for phrase in (
            "**Only a PASS of the common `C`** allows the success",
            "no success path",
            "**A STOP or any non-`PASS` termination — cleanup and merging are forbidden.**",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, act)

    def test_incomplete_lanes_are_preserved(self) -> None:
        act = norm(read(SKILL).split("### A — completion", 1)[1].split("\n## ", 1)[0])
        self.assertIn("**`incomplete` groups are never deleted**", act)
        self.assertIn("refs and patch paths are preserved", act)
        self.assertIn("stays **`unverified`**", act)

    def test_incomplete_groups_are_never_merged(self) -> None:
        batch = norm(read(SKILL))
        self.assertIn("**An `incomplete` group is never merged**", batch)
        self.assertIn("`incomplete` stays `incomplete` and never `merged`", batch)

    def test_batch_layer_is_not_flattened_into_a_single_cycle(self) -> None:
        skill = norm(read(SKILL))
        for rule in (
            "### P — per-item PLANs, the barrier, clustering",
            "**ALL-barrier.**",
            "### D — infrastructure, tracking, merge",
            "### C — verification (the standard CHECK)",
            "A campaign item has **no item-level contract**",
            "`references/lane.md`",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, skill)


if __name__ == "__main__":
    unittest.main()
