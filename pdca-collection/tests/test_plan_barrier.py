"""RED contract tests for the pdca-collection own-PLAN barrier (P1).

Normative-text contract tests for the change described in
``docs/superpowers/specs/2026-10-06-pdca-collection-plan-barrier-design.md`` and
``docs/superpowers/plans/2026-10-06-pdca-collection-plan-barrier-plan.md``:

    every task's OWN genuine PLAN must finish and be persisted BEFORE any
    DAG/group/clustering decision (the ALL-barrier), and a resumed lane must
    continue the already-done PLAN rather than run a fresh full PLAN.

Style mirrors ``test_verification_recovery.py``: plain ``unittest``, ``pathlib``
paths from the repository root and no third-party dependencies.  Assertions are
section-scoped/normalized (locate a section, then assert within it), never global
bare keyword counts and never line-number fragile checks.

At P1 these tests are intentionally RED: the new contract markers do not exist
yet.  They must fail on the missing NEW contract text, not on syntax/typos.

Run:
    python3 -m unittest discover -s config/skills/pdca-collection/tests -p 'test_plan_barrier.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

COLLECTION_SKILL = REPO / "config/skills/pdca-collection/SKILL.md"
ORCHESTRATOR = REPO / "config/agents/pdca-orchestrator.md"
BASE_VARIANTS = {
    "pdca": REPO / "config/skills/pdca/SKILL.md",
    "pdca-coder": REPO / "config/skills/pdca-coder/SKILL.md",
    "pdca-dotnet": REPO / "config/skills/pdca-dotnet/SKILL.md",
}

# The contract fixes the token families, not one exact sentence.
_OWN_PLAN_TOKENS = ("собственный PLAN", "собственного PLAN")
_PLAN_STATE_VALUES = ("pending", "running", "ready")
_GO_CONTEXT = re.compile(r"go\s*/\s*го|го\s*/\s*go", re.I)


def _plain(text: str) -> str:
    """Normalize markdown emphasis/backticks and whitespace for semantic asserts."""
    return " ".join(text.replace("**", "").replace("`", "").split())


def _section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    end = text.find(end_marker, start + len(start_marker))
    return text[start:] if end == -1 else text[start:end]


class CollectionOwnPlanBarrierContractTest(unittest.TestCase):
    """SKILL.md: own PLAN before DAG, ALL-barrier, plan_state, lane, status."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")

    def _p_section(self) -> str:
        sec = _section(self.skill, "### P —", "### D —")
        self.assertTrue(sec, "SKILL.md §P (### P —) section not found")
        return _plain(sec)

    def test_p_section_task_own_plan_precedes_dag(self):
        p = self._p_section()
        own_idx = min(
            (i for i in (p.find(tok) for tok in _OWN_PLAN_TOKENS) if i != -1),
            default=-1,
        )
        self.assertNotEqual(
            -1,
            own_idx,
            "§P does not contain the task's own PLAN token "
            f"({' / '.join(_OWN_PLAN_TOKENS)})",
        )
        dag_idx = p.find("DAG")
        self.assertNotEqual(-1, dag_idx, "§P no longer mentions DAG")
        self.assertLess(
            own_idx,
            dag_idx,
            "§P must state the task's own PLAN before the first DAG mention: "
            f"own-PLAN at {own_idx}, DAG at {dag_idx}",
        )

    def test_p_section_declares_all_barrier(self):
        p = self._p_section()
        self.assertIn("ALL-barrier", p, "§P lacks the 'ALL-barrier' token")
        self.assertIn("барьер", p, "§P lacks the Russian 'барьер' concept")

    def test_plan_state_values_declared(self):
        skill = _plain(self.skill)
        windows = [
            skill[m.start(): m.start() + 240]
            for m in re.finditer(r"plan_state", skill)
        ]
        self.assertTrue(
            windows, "SKILL.md lacks the 'plan_state' readiness field token"
        )
        ok = any(
            all(value in window for value in _PLAN_STATE_VALUES)
            for window in windows
        )
        self.assertTrue(
            ok,
            "SKILL.md must declare plan_state values pending/running/ready, got: "
            f"{windows!r}",
        )

    def test_lane_section_resumes_saved_plan_not_fresh_full_plan(self):
        lane = _plain(_section(self.skill, "## Лейн", "## Git-модель"))
        self.assertTrue(lane, "SKILL.md §Лейн (## Лейн) section not found")
        self.assertIn("PLAN", lane, "§Лейн no longer refers to PLAN")
        self.assertRegex(
            lane,
            re.compile(r"сохранённ"),
            "§Лейн must resume the already-done PLAN via 'сохранённ...' wording",
        )

    def test_status_section_records_plan_handoff_fields(self):
        status = _plain(_section(self.skill, "## Статус коллекции", "## Отчёт"))
        self.assertTrue(status, "SKILL.md §Статус коллекции section not found")
        for field in ("plan_state", "cycle_id", "selected_variant"):
            self.assertIn(field, status, f"§Статус must record {field!r}")
        self.assertTrue(
            "plan_revision" in status or "вектор ревизий plan" in status.lower(),
            "§Статус must record 'plan_revision' r (or 'вектор ревизий PLAN')",
        )

    def test_skill_still_forbids_automatic_recluster(self):
        # preservation guard: the new barrier must not re-enable automatic
        # relaning after lanes start.
        low = _plain(self.skill).lower()
        self.assertIn("recluster", low, "collection SKILL lost the no-recluster token")
        self.assertIn("rerun", low, "collection SKILL lost the no-rerun token")
        self.assertRegex(
            low,
            re.compile(r"автоматическ\w*\s+(rerun|remerge|recluster|reset|revert)"),
            "collection SKILL must still forbid automatic "
            "rerun/remerge/recluster/reset/revert",
        )


class OrchestratorCollectionPlanHandoffTest(unittest.TestCase):
    """pdca-orchestrator.md: a distinct COLLECTION TASK PLAN entry + plan_handoff."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = ORCHESTRATOR.read_text(encoding="utf-8")

    def test_orchestrator_declares_collection_task_plan_entry(self):
        self.assertIn(
            "COLLECTION TASK PLAN",
            self.text,
            "pdca-orchestrator.md lacks the 'COLLECTION TASK PLAN' entry",
        )

    def test_orchestrator_returns_plan_handoff(self):
        self.assertIn(
            "plan_handoff",
            self.text,
            "pdca-orchestrator.md lacks the 'plan_handoff' result token",
        )


class StandaloneVariantCollectionHandoffTest(unittest.TestCase):
    """Base variants keep standalone semantics AND gain a collection caller note."""

    def test_variants_keep_standalone_go_and_autonomous_immediate(self):
        for name, path in BASE_VARIANTS.items():
            with self.subTest(variant=name):
                low = _plain(path.read_text(encoding="utf-8")).lower()
                self.assertTrue(
                    _GO_CONTEXT.search(low),
                    f"{name}: lost the explicit normal-mode 'go'/'го' confirmation "
                    f"context",
                )
                self.assertTrue(
                    "немедленн" in low or "immediately" in low,
                    f"{name}: lost the standalone-autonomous immediate-start token",
                )

    def test_variants_document_collection_caller_handoff(self):
        for name, path in BASE_VARIANTS.items():
            with self.subTest(variant=name):
                low = _plain(path.read_text(encoding="utf-8")).lower()
                self.assertTrue(
                    "collection caller" in low,
                    f"{name}: missing the collection caller handoff note "
                    f"('collection caller')",
                )


if __name__ == "__main__":
    unittest.main()
