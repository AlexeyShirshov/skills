"""Regression guards: role assets are thin adapters over the phase references.

An agent asset carries the role's identity, its permissions, the transport that delivers the
authoritative contract and the shape of its return. The **procedure and the result requirements**
live once in the phase reference (``plan.md`` for PLAN, ``check.md`` for CHECK, ``act.md`` for the
status/ACT work, ``escalate.md`` for the consultation) or in the loaded form contract. Repeating a
procedure in the agent creates a second contract that drifts.

What is pinned here:

* the planner and checker agents no longer inline the phase procedure or its output contract;
* the PLAN result has no unit decomposition — execution units are DO's;
* every delegate receives its authoritative contract through a transport its permissions allow
  (the plan-reference path, the inline CHECK contract, the ``act.md`` read, the skill load, the
  escalation protocol), not through a widened allowlist or a dead pointer.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
FAMILY = SKILL_DIR.parent
ASSETS = SKILL_DIR / "assets/opencode-agents"
PLAN_REF = SKILL_DIR / "references/plan.md"
CHECK_REF = SKILL_DIR / "references/check.md"
ACT_REF = SKILL_DIR / "references/act.md"
ESCALATE_REF = SKILL_DIR / "references/escalate.md"
BASE = SKILL_DIR / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.replace("`", "").replace("*", "").split())


def frontmatter(path: Path) -> str:
    text = read(path)
    end = text.find("\n---", 3)
    return text[3:end]


def read_grants(path: Path) -> set[str]:
    """The `read:` allow entries of the V1 `permission:` map."""
    block = re.search(r"^  read:\n((?:    .*\n)+)", frontmatter(path), re.MULTILINE)
    return set(re.findall(r'"([^"]+)":\s*allow', block.group(1))) if block else set()


class ThinAdapterTest(unittest.TestCase):
    def test_planner_agent_delegates_the_procedure_to_plan_reference(self) -> None:
        body = norm(read(ASSETS / "pdca-planner.md"))
        self.assertIn("plan_reference_path", body)
        self.assertIn("references/plan.md §Output contract", body)
        for moved in (
            "## Form and first step",
            "## What you do",
            "## Step boundary",
            "## Calibration",
            "## Plan hygiene",
            "## Output contract",
            "Decompose into units",
            "Unit decomposition",
        ):
            with self.subTest(moved=moved):
                self.assertNotIn(moved, body, "the planner copies the plan procedure again")

    def test_checker_agent_delegates_the_procedure_to_the_inline_contract(self) -> None:
        body = norm(read(ASSETS / "pdca-check.md"))
        self.assertIn("complete contents", body)
        self.assertIn("references/check.md", body)
        self.assertIn("§Verdict and routing", body)
        for moved in ("## Procedure", "## Output contract", "## What CHECK receives"):
            with self.subTest(moved=moved):
                self.assertNotIn(moved, body, "the checker copies the CHECK procedure again")

    def test_executor_defers_the_status_procedure_to_act_reference(self) -> None:
        body = norm(read(ASSETS / "pdca-executor.md"))
        self.assertIn("references/act.md §Status file", body)
        self.assertIn("references/act.md §Git state", body)
        self.assertIn("references/act.md §Durable state", body)
        # The skeleton, its ordering and the counter effects are act.md/base material.
        self.assertNotIn("`## Progress log` last", read(ASSETS / "pdca-executor.md"))
        self.assertNotIn("fixed heading order", body)

    def test_escalate_agent_does_not_restate_the_counters(self) -> None:
        text = read(ASSETS / "pdca-escalate.md")
        body = norm(text)
        self.assertIn("references/escalate.md", body)
        self.assertIn("whose protocol the driver passes with the brief", body)
        # The live values are transport, not a rule the role re-derives from a file it cannot
        # locate: N, r, n/3 and the defect history arrive in the brief as inputs.
        self.assertIn("(N, r, n/3) and the defect history arrive in that brief", body)
        self.assertIn("this role applies no threshold of its own", body)
        # No copied threshold procedure next to the single owner.
        for copied in (
            "third failed check",
            "bound to the plan revision",
            "a new revision resets n to 1",
            "grows only for a revised plan",
        ):
            with self.subTest(copied=copied):
                self.assertNotIn(copied, body.lower())
        # The pointer must still resolve: the named reference hands the counters to the
        # base section that owns them, so the thin asset is not pointing at nothing.
        escalate = norm(read(ESCALATE_REF))
        self.assertIn(
            "the attempt budget and same-defect threshold are defined once in "
            "../SKILL.md §State machine and counters",
            escalate,
        )
        self.assertIn("### State machine and counters", read(BASE))
        self.assertIn("§State machine and counters", read(ESCALATE_REF))

    def test_orchestrator_does_not_mirror_the_collection_lane_rules(self) -> None:
        body = norm(read(ASSETS / "pdca-orchestrator.md"))
        self.assertIn("the lane rules are the loaded pdca-collection contract's", body)
        self.assertIn("Load that contract by exact ID", body)
        self.assertNotIn("mirror of the", body)
        self.assertNotIn("the group is stopped", body)
        self.assertNotIn("A plan-terminal task is not a group stop", body)


class PlanHasNoUnitsTest(unittest.TestCase):
    def test_plan_output_contract_excludes_unit_decomposition(self) -> None:
        plan = norm(read(PLAN_REF))
        self.assertIn("never contains a unit decomposition", plan)
        self.assertNotIn("Decompose into units", plan)
        self.assertNotIn("Unit decomposition with dependencies", plan)

    def test_no_shared_role_asset_returns_plan_units(self) -> None:
        for path in sorted(ASSETS.glob("*.md")):
            with self.subTest(asset=path.name):
                body = read(path)
                self.assertNotIn("Decompose into units", body)
                self.assertNotIn("Unit decomposition", body)

    def test_units_are_do_state_in_the_status_skeleton(self) -> None:
        act = read(ACT_REF)
        plan_bullet = act[act.index("- **§PLAN record**"):act.index("- **§DO result**")]
        do_bullet = act[act.index("- **§DO result**"):act.index("- **§CHECK record**")]
        self.assertNotIn("execution units", plan_bullet.lower())
        self.assertIn("DO execution units", do_bullet)

    def test_coder_status_metadata_is_do_owned(self) -> None:
        coder = read(FAMILY / "pdca-coder/SKILL.md")
        self.assertIn("execution-unit metadata is DO's", coder)
        self.assertNotIn("unit decomposition metadata", coder)
        self.assertNotIn("under `## PLAN record` where the base prescribes it", coder)


class ContractTransportTest(unittest.TestCase):
    """Every delegate reaches its own contract through permissions it actually has."""

    def test_planner_reads_the_plan_reference_by_path(self) -> None:
        planner = read(ASSETS / "pdca-planner.md")
        self.assertIn('"*/pdca/references/plan.md": allow', planner)
        self.assertIn("plan_reference_path", planner)
        self.assertIn("resource blocker", norm(planner))
        self.assertIn("## Entry and first step", read(PLAN_REF))
        self.assertIn("## Step boundary", read(PLAN_REF))
        self.assertIn("## Output contract", read(PLAN_REF))

    def test_check_receives_the_complete_contract_inline_and_cannot_read_it(self) -> None:
        checker = read(ASSETS / "pdca-check.md")
        self.assertIn("inlined by the driver", checker)
        self.assertIn("no permission to read the installed reference", checker)
        # Its scoped read stays .pdca/** — no reference-directory grant was added.
        self.assertNotIn("references/check.md\": allow", checker)
        self.assertIn("complete contents inline", norm(read(CHECK_REF)))
        self.assertIn("explicit blocker", norm(read(CHECK_REF)))

    def test_executor_reaches_its_status_reference_within_its_permissions(self) -> None:
        executor = read(ASSETS / "pdca-executor.md")
        self.assertIn("references/act.md", executor)
        # The executor has edit/bash and no narrowed read; it resolves the reference from the
        # loaded package's base directory instead of receiving a copied procedure.
        self.assertIn("resolve it from the skill base directory", norm(executor))

    def test_escalate_gets_its_protocol_from_the_driver(self) -> None:
        self.assertIn("protocol the driver passes with the brief", norm(read(ASSETS / "pdca-escalate.md")))
        self.assertIn("the driver reads this file before dispatch", norm(read(ESCALATE_REF)))

    def test_orchestrator_loads_the_active_contract_by_exact_id(self) -> None:
        runner = norm(read(ASSETS / "pdca-orchestrator.md"))
        self.assertIn("Load a contract through the host's skill mechanism by exact ID", runner)
        self.assertIn("fail closed", runner.lower())

    def test_base_plan_section_routes_the_plan_reference_uninlined(self) -> None:
        base = norm(read(BASE))
        self.assertIn("references/plan.md is pdca-planner only", base)
        self.assertIn("driver neither reads, inlines nor forwards it", base)


class TransportPermissionTest(unittest.TestCase):
    """The declared transport of each contract is one the role's permissions allow.

    A pointer the role cannot open is a dead pointer; a read grant nobody declared is a widened
    allowlist. Both sides are checked together, so a "thin" adapter cannot buy its brevity with an
    unreachable source.
    """

    def test_planner_declares_exactly_the_plan_reference(self) -> None:
        planner = ASSETS / "pdca-planner.md"
        self.assertEqual({"*/pdca/references/plan.md"}, read_grants(planner))
        self.assertIn('"*": deny', frontmatter(planner))
        body = norm(read(planner))
        self.assertIn("plan_reference_path", body)
        self.assertIn("It is the only file you read", body)

    def test_plan_reference_is_self_sufficient(self) -> None:
        # The planner reads one file: a mandatory norm delegated to a sibling would be unreachable.
        plan = read(PLAN_REF)
        self.assertNotIn("../", plan)
        self.assertNotIn("SKILL.md", plan)
        for heading in ("## Entry and first step", "## Step boundary", "## Output contract"):
            with self.subTest(heading=heading):
                self.assertIn(heading, plan)

    def test_executor_reaches_act_reference_with_its_unrestricted_read(self) -> None:
        executor = ASSETS / "pdca-executor.md"
        self.assertNotIn("read:", frontmatter(executor), "the executor must keep an open read")
        body = norm(read(executor))
        self.assertIn("references/act.md §Status file", body)
        self.assertIn("resolve it from the skill base directory", body)

    def test_check_cannot_read_its_reference_so_it_arrives_inline(self) -> None:
        checker = ASSETS / "pdca-check.md"
        self.assertEqual({".pdca/**"}, read_grants(checker))
        body = norm(read(checker))
        self.assertIn("complete contents", body)
        self.assertIn("inlined by the driver", body)
        self.assertIn("no permission to read the installed reference", body)
        # The driver declares the same transport: whole contract, no path.
        self.assertIn(
            "no path and no instruction to read it", norm(read(SKILL_DIR / "references/driver.md"))
        )

    def test_orchestrator_reaches_the_skill_and_the_driver_reference(self) -> None:
        runner = ASSETS / "pdca-orchestrator.md"
        self.assertNotIn("read:", frontmatter(runner), "the skill directory must stay readable")
        self.assertRegex(frontmatter(runner), r'(?m)^  skill:\n    "\*": allow')
        body = norm(read(runner))
        self.assertIn("Load a contract through the host's skill mechanism by exact ID", body)
        self.assertIn("read references/driver.md in full", body)

    def test_escalate_receives_its_protocol_because_it_cannot_load_a_skill(self) -> None:
        escalate = ASSETS / "pdca-escalate.md"
        self.assertRegex(frontmatter(escalate), r'(?m)^  skill:\n    "\*": deny')
        self.assertIn(
            "protocol the driver passes with the brief", norm(read(escalate))
        )


class SingleOwnerTest(unittest.TestCase):
    """A form or policy block has one home; the adapter/reference does not fork it."""

    def test_forms_and_effort_policy_stay_in_the_base(self) -> None:
        base = read(BASE)
        self.assertEqual(1, base.count("\n### Forms\n"))
        self.assertEqual(1, base.count("\n### Effort and time policy\n"))
        plan = read(PLAN_REF)
        for copied in ("\n### Forms", "\n## Forms", "\n### Effort and time policy"):
            with self.subTest(copied=copied):
                self.assertNotIn(copied, plan)
        # The plan keeps only its own obligation under that policy.
        self.assertIn("effort estimate", norm(plan))

    def test_driver_reference_holds_mechanics_not_a_phase_procedure(self) -> None:
        driver = read(SKILL_DIR / "references/driver.md")
        for heading in (
            "## Procedure",
            "## Output contract",
            "## Plan fields",
            "## Step boundary",
            "## Verdict and routing",
            "## Status file",
            "## Grounds",
        ):
            with self.subTest(heading=heading):
                self.assertNotIn("\n" + heading, driver)
        self.assertLessEqual(len(driver.splitlines()), 120, "the driver grew into a contract")

    def test_driver_points_at_the_owners(self) -> None:
        driver = norm(read(SKILL_DIR / "references/driver.md"))
        for owner in (
            "plan.md",
            "§Normal-mode approval",
            "§State machine and counters",
            "§Workspace and durable status",
            "pdca-collection",
            "pdca-incremental",
            "check.md",
            "escalate.md",
        ):
            with self.subTest(owner=owner):
                self.assertIn(owner, driver)

    def test_every_shared_asset_stays_a_thin_adapter(self) -> None:
        # The orchestrator was 434 lines when it carried every loaded contract's procedure; a
        # role asset names its owner and its transport instead of re-growing into one.
        for path in sorted(ASSETS.glob("*.md")):
            with self.subTest(asset=path.name):
                self.assertLessEqual(len(read(path).splitlines()), 210)


if __name__ == "__main__":
    unittest.main()
