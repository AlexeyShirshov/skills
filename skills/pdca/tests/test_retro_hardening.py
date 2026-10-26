"""Regression guard for the hardening added after the 13–23 October 2026 run.

That run produced a measurable pattern: about half of the accepted units needed
a replan, and most of those replans came from the plan's own execution contract
(a selector that matched nothing yet exited 0, a command forbidden in the phase,
an evidence location that could not be recomputed, a mutation harness that did
not run) rather than from the product.  Two thirds of acceptances carried
recorded exceptions, and the same exception classes repeated across units.

After the family redesign these rules live **once** in the base contract and its
phase references; the coder and .NET overlays inherit them and must not copy
them.  This module pins both facts.  It is a *presence* guard over the runtime
text, like the other presence guards; it does not execute a cycle.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

FAMILY = Path(__file__).resolve().parents[2]  # the `skills/` directory

BASE = FAMILY / "pdca/SKILL.md"
BASE_PLAN = FAMILY / "pdca/references/plan.md"
BASE_CHECK = FAMILY / "pdca/references/check.md"
BASE_ACT = FAMILY / "pdca/references/act.md"
CODER = FAMILY / "pdca-coder/SKILL.md"
DOTNET = FAMILY / "pdca-dotnet/SKILL.md"
COLLECTION = FAMILY / "pdca-collection/SKILL.md"
COLLECTION_LANE = FAMILY / "pdca-collection/references/lane.md"

BASE_AGENTS = FAMILY / "pdca/assets/opencode-agents"
CODER_AGENTS = FAMILY / "pdca-coder/assets/opencode-agents"
DOTNET_AGENTS = FAMILY / "pdca-dotnet/assets/opencode-agents"


def norm(text: str) -> str:
    """Collapse whitespace and drop markdown emphasis, as the other guards do."""
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class BaseContractHardeningTest(unittest.TestCase):
    """The base phase references carry the hardening rules as operative text."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(BASE_PLAN)
        cls.text = norm(cls.raw)

    def test_new_sections_exist(self) -> None:
        heads = {
            line.rstrip()
            for line in self.raw.splitlines()
            if re.match(r"^#{2,3} ", line)
        }
        for section in (
            "## Plan command contract (PLAN close)",
            "## Vacuous and expected-negative runs",
            "## Recorded exceptions: catalog and repetition threshold",
            "## Re-anchoring at DO entry",
            "## Proportional planning and effort policy",
            "## One evidence location binding",
        ):
            with self.subTest(section=section):
                self.assertIn(section, heads)

    def test_plan_command_contract_items(self) -> None:
        for phrase in (
            "validated before gate 1",
            "selector resolves",
            "argument vector survives the harness",
            "phase is legal",
            "expected outcome is declared",
            "A violation is a PLAN defect",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(norm(phrase), self.text)

    def test_vacuous_run_is_a_failure(self) -> None:
        self.assertIn(
            "A run that discovers or selects zero targets is a failed run",
            self.text,
        )
        self.assertIn("expected-negative", self.text)

    def test_exception_catalog_and_threshold(self) -> None:
        for cls in (
            "environment/infrastructure",
            "tooling incompatibility",
            "scope/resource policy",
            "historical provenance",
        ):
            with self.subTest(exception_class=cls):
                self.assertIn(cls, self.text)
        self.assertIn("three or more units of one campaign", self.text)
        self.assertIn("systemic defect", self.text)

    def test_reanchor_and_proportionality(self) -> None:
        self.assertIn("cosmetic drift", self.text)
        self.assertIn("semantic drift", self.text)
        self.assertIn("bounded probe", self.text)
        base = norm(read(BASE))
        self.assertIn("No autonomous cutoff", base)
        self.assertIn("estimate is not a stop condition", base)

    def test_single_evidence_binding(self) -> None:
        self.assertIn("the same checkout the checks run in", self.text)


class OverlayInheritanceHardeningTest(unittest.TestCase):
    """The shared hardening rules are inherited, never copied into the overlays."""

    # Headings that belong to the base references; an overlay repeating them is drift.
    BASE_ONLY_SECTIONS = (
        "## Plan command contract (PLAN close)",
        "## Vacuous and expected-negative runs",
        "## Recorded exceptions: catalog and repetition threshold",
        "## Re-anchoring at DO entry",
        "## Proportional planning and effort policy",
    )

    def test_overlays_point_at_the_base_references(self) -> None:
        for name, path in (("pdca-coder", CODER), ("pdca-dotnet", DOTNET)):
            text = norm(read(path))
            with self.subTest(overlay=name):
                self.assertIn("../pdca/references/plan.md", text)

    def test_overlays_do_not_repeat_the_base_hardening_sections(self) -> None:
        for name, path in (("pdca-coder", CODER), ("pdca-dotnet", DOTNET)):
            raw = read(path)
            for section in self.BASE_ONLY_SECTIONS:
                with self.subTest(overlay=name, section=section):
                    self.assertNotIn(section, raw)

    def test_overlays_do_not_restate_the_carrying_rules(self) -> None:
        for name, path in (("pdca-coder", CODER), ("pdca-dotnet", DOTNET)):
            text = norm(read(path))
            for phrase in (
                "A run that discovers or selects zero targets is a failed run",
                "three or more units of one campaign is a systemic defect",
            ):
                with self.subTest(overlay=name, phrase=phrase):
                    self.assertNotIn(norm(phrase), text)


class DotnetHardeningTest(unittest.TestCase):
    """The .NET overlay keeps its concrete command forms and evidence rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = norm(read(DOTNET))

    def test_dotnet_carries_the_concrete_command_forms(self) -> None:
        for phrase in (
            "Canonical command forms",
            "fully-qualified",
            "0 selected is failure",
            "controlled-mutant fallback",
            "skip budget applied only to the complete sweep",
            "CRLF preserved",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(norm(phrase), self.text)

    def test_dotnet_names_its_inheritance_chain(self) -> None:
        self.assertIn("../pdca/SKILL.md", self.text)
        self.assertIn("../pdca-coder/SKILL.md", self.text)


class CollectionHardeningTest(unittest.TestCase):
    """The batch contract treats width, host budget and additions explicitly."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = norm(read(COLLECTION))
        cls.lane = norm(read(COLLECTION_LANE))

    def test_width_and_host_budget(self) -> None:
        self.assertIn("Width is an objective, not a by-product", self.text)
        self.assertIn("host budget", self.text)
        self.assertIn("Minimise the largest serialized group", self.text)

    def test_scope_additions_consume_capacity(self) -> None:
        self.assertIn("silently jump ahead of ready items", self.lane)

    def test_own_plan_keeps_plan_hygiene(self) -> None:
        self.assertIn(
            "a batch, not a licence to skip plan hygiene",
            self.text,
        )
        self.assertIn("validates its command contract", self.text)


class RoleBriefHardeningTest(unittest.TestCase):
    """The role briefs carry the enforcement duties, not only the contract."""

    def test_planner_carries_plan_hygiene(self) -> None:
        self.assertIn("Plan hygiene (mandatory, checked at gate 1)", norm(read(BASE_AGENTS / "pdca-planner.md")))
        self.assertIn("Command contract", norm(read(DOTNET_AGENTS / "pdca-planner.md")))
        self.assertIn("Command contract", norm(read(CODER_AGENTS / "pdca-planner.md")))

    def test_check_carries_exception_discipline(self) -> None:
        for agents in (BASE_AGENTS, CODER_AGENTS, DOTNET_AGENTS):
            with self.subTest(package=str(agents)):
                text = norm(read(agents / "pdca-check.md"))
                self.assertIn("Exception discipline", text)
                self.assertIn("systemic defect", text)

    def test_executor_refuses_vacuous_runs(self) -> None:
        for agents in (BASE_AGENTS, CODER_AGENTS, DOTNET_AGENTS):
            with self.subTest(package=str(agents)):
                text = norm(read(agents / "pdca-executor.md"))
                self.assertIn("vacuous run is a failure", text)


if __name__ == "__main__":
    unittest.main()
