"""Regression guards: dispatch economy — persist once, then reference exactly.

The invariant task, criteria, constraints, prohibitions and commit policy are persisted
once, verbatim, in the durable `.pdca` record; later PLAN/DO/CHECK/escalate briefs carry
exact references (path, section, revision) plus only the phase deltas and the
`evidence_root`, instead of re-pasting unchanged blocks.  This must not become a lossy
summary: the reference stands for the complete readable original, and CHECK still gets
the full base CHECK contract inline and reads the staged candidate itself.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
BASE = SKILL_DIR / "SKILL.md"
ORCHESTRATOR = SKILL_DIR / "assets/opencode-agents/pdca-orchestrator.md"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start + len(start_marker))
    return norm(text[start:end])


class TransportBoundaryTest(unittest.TestCase):
    """The four transport seams: base load order, form ownership, brief, read scope.

    Each guard pairs the caller's handoff with the owner's requirement, so a stale copy on
    either side fails instead of merely a renamed literal.
    """

    def setUp(self) -> None:
        self.base = norm(read(BASE))
        self.driver_raw = read(SKILL_DIR / "references/driver.md")
        self.driver = norm(self.driver_raw)
        self.runner_raw = read(ORCHESTRATOR)
        self.runner = norm(self.runner_raw)
        self.plan = norm(read(SKILL_DIR / "references/plan.md"))
        self.escalate = norm(read(SKILL_DIR / "references/escalate.md"))

    def test_the_base_entry_contract_is_loaded_before_the_form_contract(self) -> None:
        load = section(self.runner_raw, "## What you load", "## The three execution contexts")
        self.assertIn("first, in every context: the base entry contract", load)
        self.assertIn("base directory its load result returns", load)
        self.assertIn("a form contract never supplies it", load)
        self.assertIn("a campaign preparation loads it before the incremental contract", load)
        self.assertLess(
            load.index("first, in every context: the base entry contract"),
            load.index("campaign preparation / lane entry"),
        )
        self.assertIn("never derive that directory from the form", load)
        # The driver resolves its own reference against that same directory, never a guess.
        self.assertIn("base directory its load result returns", self.driver)

    def test_the_loader_may_read_every_reference_it_is_told_to_open(self) -> None:
        front = self.runner_raw.split("---", 2)[1]
        self.assertNotIn("read:", front, "the skill directory must stay readable")
        self.assertRegex(front, r'(?m)^  skill:\n    "\*": allow')
        for name in ("driver.md", "check.md", "escalate.md"):
            with self.subTest(name=name):
                self.assertTrue((SKILL_DIR / "references" / name).is_file())
                self.assertIn("`references/%s`" % name, read(BASE))

    def test_the_handoff_carries_the_plan_reference_not_a_form_text(self) -> None:
        call = section(self.driver_raw, "2. One `pdca-planner` call", "3. The returned plan")
        self.assertIn("plan_reference_path", call)
        self.assertIn("only form/overlay discriminator is plan.md", call)
        self.assertIn("no copy of the base §forms routing table", call)
        self.assertNotIn("discriminator text itself", self.driver)
        # The discriminators exist once, in the file the planner actually reads.
        for token in ("sufficiently known and bounded", "list of independent goals"):
            with self.subTest(token=token):
                self.assertIn(token, self.plan)
                self.assertNotIn(token, self.driver)
        forms = section(read(BASE), "### Forms", "The planner defines criteria")
        self.assertIn("routing only", forms)
        for row in ("| bounded execution | cycle |", "| incremental execution | incremental |",
                    "| collection | collection |"):
            with self.subTest(row=row):
                self.assertIn(row, forms)
        entry = section(
            read(SKILL_DIR / "references/plan.md"), "## Entry and first step", "### Gap closure"
        )
        for machine in ("cycle when", "incremental when", "collection for"):
            with self.subTest(machine=machine):
                self.assertIn(machine, entry)

    def test_the_escalation_brief_carries_the_protocol_and_its_required_inputs(self) -> None:
        bullet = section(self.driver_raw, "- **ESCALATE**", "- **Status work**")
        self.assertIn("complete contents inline", bullet)
        self.assertIn("escalate.md §input and permissions", bullet)
        protocol = section(
            read(SKILL_DIR / "references/escalate.md"),
            "## Input and permissions",
            "## Conclusion and limits",
        )
        required = (
            "narrow question", "original task", "criteria", "result",
            "reused, not re-gathered", "already tried", "attempts",
            "defect history", "applied fixes", "constraints", "n/3",
        )
        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, protocol, "the protocol must require the input")
                self.assertIn(item, bullet, "the transport must deliver what it requires")
        # The counter procedure is the base's, already loaded by the driver; no waiver.
        self.assertIn("already loaded by the driver", bullet)
        self.assertIn("no discretion to waive it", bullet)
        self.assertIn("no discretion to waive the counter rule", self.escalate)

    def test_the_expert_role_points_at_the_protocol_instead_of_a_second_list(self) -> None:
        agent = norm(read(SKILL_DIR / "assets/opencode-agents/pdca-escalate.md"))
        self.assertIn("references/escalate.md", agent)
        self.assertIn("every item its §input and permissions requires", agent)
        self.assertIn("(n, r, n/3) and the defect history arrive in that brief", agent)
        self.assertIn("applies no threshold of its own", agent)
        for copied in ("acceptance criterion in play", "pre-gathered pdca-scout evidence pack"):
            with self.subTest(copied=copied):
                self.assertNotIn(copied, agent, "the role copies a partial input list again")

    def test_the_driver_read_scope_is_one_owner_that_matches_its_obligations(self) -> None:
        roles = section(read(BASE), "| Role | Agent |", "ACT is finalized")
        self.assertIn("references/driver.md §read scope", roles)
        self.assertIn("single owner", self.base)
        escalation = section(
            read(BASE), "### Escalation — expert review", "### Generic operating constraints"
        )
        self.assertIn("driver.md §read scope", escalation)
        self.assertIn("references/escalate.md", escalation)
        self.assertIn("built from the inputs that protocol requires", escalation)
        scope = section(self.driver_raw, "## Read scope", "## Routed, not taken")
        for item in (
            "references/driver.md", "references/check.md", "references/escalate.md",
            "status files", "step-boundary", "recovery",
        ):
            with self.subTest(item=item):
                self.assertIn(item, scope)
        # REPORT-compare reads the executor's report, never its status file.
        self.assertIn("from the executor's report", scope)
        self.assertIn("never from reading the file", scope)
        self.assertNotIn("assigned status files and the one reference it must inline", self.base)


if __name__ == "__main__":
    unittest.main()
