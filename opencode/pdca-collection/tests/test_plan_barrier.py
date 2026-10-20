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
    python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_DIR.parent

# Host config (agents/profiles/AGENTS.md) lives in the `opencode-config` repo, not in this one.
# Point at it with OPENCODE_CONFIG_REPO to enable host-parity checks; they skip by default.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"

COLLECTION_SKILL = SKILL_DIR / "SKILL.md"
ORCHESTRATOR = (CONFIG / "agents/pdca-orchestrator.md") if CONFIG else None
BASE_VARIANTS = {
    "pdca": SKILLS_ROOT / "pdca/SKILL.md",
    "pdca-coder": SKILLS_ROOT / "pdca-coder/SKILL.md",
    "pdca-dotnet": SKILLS_ROOT / "pdca-dotnet/SKILL.md",
}

# The contract fixes the token families, not one exact sentence.
_OWN_PLAN_TOKENS = ("собственный PLAN", "собственного PLAN")
_PLAN_STATE_VALUES = ("pending", "running", "ready")
_APPROVAL_CONTEXT = re.compile(r"approv\w*|апрув", re.I)


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

    def test_p_section_allows_parallel_plans(self):
        # The barrier constrains the START of DAG/lanes, not the order of PLANs.
        p = self._p_section()
        self.assertIn(
            "параллельно",
            p,
            "§P must state that the units' own PLANs run in parallel",
        )
        self.assertIn(
            "plan_cap",
            p,
            "§P must name the PLAN concurrency ceiling 'plan_cap'",
        )
        self.assertIn(
            "а не про их последовательность",
            p,
            "§P must state that the barrier is about readiness, not PLAN order",
        )
        self.assertIn(
            "одним блоком",
            p,
            "§P must say the PLAN dispatches go out in one batch, not one by one",
        )

    def test_parallel_planning_does_not_fix_the_schedule(self):
        # Parallel PLANs must not be read as parallel lanes: code overlap is
        # resolved by clustering, and a sequential chain in one group is normal.
        p = self._p_section()
        self.assertIn(
            "не фиксирует расписание",
            p,
            "§P must state that a parallel PLAN does not fix the schedule",
        )
        self.assertIn(
            "пересекающ",
            p.lower(),
            "§P must state that intersecting footprints are resolved by clustering",
        )
        self.assertIn(
            "одну группу",
            p,
            "§P must state that overlapping units land in one group",
        )
        self.assertIn(
            "заявляет",
            p,
            "§P must state that a PLAN declares the footprint instead of reserving it",
        )

    def test_footprint_reservation_is_a_claim_not_a_lock(self):
        # The reservation must stay a real reservation (used by clustering), while
        # parallel planning must not be blocked by it.
        p = self._p_section()
        self.assertIn(
            "резервац",
            p.lower(),
            "§P must keep the footprint reservation concept",
        )
        self.assertIn(
            "не блокировк",
            p.lower(),
            "§P must say the reservation is a claim, not a lock",
        )
        self.assertNotIn(
            "ничего не бронирует",
            p.lower(),
            "§P must not deny the reservation: clustering relies on it",
        )

    def test_status_writes_are_serialized_not_single_owner(self):
        # One writer at a time, but the physical write belongs to pdca-executor
        # (§Статус), not to the primary directly.
        p = self._p_section()
        self.assertIn("сериализуется", p, "§P must say the status writes are serialized")
        self.assertIn(
            "pdca-executor",
            p,
            "§P must name pdca-executor as the physical writer of the status file",
        )
        self.assertIn("§Статус", p, "§P must defer the write ownership to §Статус")
        self.assertNotIn(
            "пишет один владелец",
            p,
            "§P must not claim the primary is the only writer",
        )

    def test_parameters_declare_plan_concurrency(self):
        params = _plain(_section(self.skill, "## Параметры", "## Связь с базовым PDCA"))
        self.assertTrue(params, "SKILL.md §Параметры section not found")
        self.assertIn(
            "Потолок параллелизма PLAN",
            params,
            "§Параметры must declare a separate PLAN concurrency cap",
        )
        self.assertIn("plan_cap", params, "§Параметры must name 'plan_cap'")
        self.assertIn(
            "лейнов",
            params,
            "§Параметры must keep the lane cap distinct from the PLAN cap",
        )
        self.assertIn(
            "хоста",
            params,
            "§Параметры must bound plan_cap by the host's real parallelism",
        )

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


class StepPlanApprovalContractTest(unittest.TestCase):
    """SKILL.md §Лейн: the normal-mode step-PLAN approval gate (AC06).

    Guards the rule written in §"Драйвер лейна и кампания": every real step runs its
    own full PLAN of its variant before DO, and in normal mode that plan is approved
    per the active contract through a *durable* pending approval ref while the current
    unit takes ``disposition=paused``; the step brief neither replaces the PLAN nor
    counts as an approval.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")

    def test_normal_mode_step_plan_approval_is_durable_and_pauses_the_unit(self):
        """AC06: normal-mode step gate = durable pending approval ref + paused unit + brief ≠ PLAN."""
        lane = _plain(_section(self.skill, "## Лейн", "## Неактуальный"))
        self.assertTrue(lane, "SKILL.md §Лейн (## Лейн) section not found")
        # (a) normal mode ties the step PLAN approval to a *durable* pending ref
        self.assertRegex(
            lane,
            re.compile(r"normal mode.{0,400}?durable\s+pending\s+approval\s+ref", re.I),
            "§Лейн must state that in normal mode the step PLAN approval is recorded "
            "as a durable pending approval ref (got: %r)" % lane[:600],
        )
        # (b) the current unit is paused for the duration of that approval
        self.assertRegex(
            lane,
            re.compile(r"pending\s+approval\s+ref.{0,200}?disposition=paused", re.I),
            "§Лейн must state that the current unit gets disposition=paused at the "
            "step approval gate (got: %r)" % lane[:600],
        )
        # (c) the step brief is not the step's PLAN
        self.assertRegex(
            lane,
            re.compile(r"бриф\w*\s+шага\s+plan\s+не\s+подменя", re.I),
            "§Лейн must state explicitly that the step brief does not replace the "
            "step's PLAN ('Бриф шага PLAN не подменяет')",
        )


def _windows(text: str, token: str, radius: int) -> list[str]:
    """Every window of ``radius`` characters on both sides of ``token``."""
    return [
        text[max(0, m.start() - radius): m.end() + radius]
        for m in re.finditer(re.escape(token), text)
    ]


# A barrier may not demand a runtime status: readiness is a persisted field, not a
# live `Status: running` mirror.
_RUNTIME_STATUS_REQUIREMENT = re.compile(
    r"(?i)(требует|обязателен).{0,80}(Status:\s*running|runtime-статус)"
)


class CollectionUnitPreparationBarrierTest(unittest.TestCase):
    """SKILL.md: `execution_kind`, per-unit preparation barrier, disposition (AC03/05/14)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")
        cls.plain = _plain(cls.skill)

    def test_pipeline_declares_execution_kind_and_both_kinds(self):
        for token in ("execution_kind", "cycle", "campaign"):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    self.plain,
                    f"SKILL.md lacks the execution-kind token {token!r}",
                )

    def test_preparation_state_gates_dispatch_on_ready(self):
        for token in ("plan_state", "preparation_state", "preparation_ref", "@r"):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    self.plain,
                    f"SKILL.md lacks the preparation-barrier field {token!r}",
                )
        state = next(
            (w for w in _windows(self.plain, "preparation_state", 400) if w),
            "",
        )
        self.assertTrue(state, "SKILL.md has no 'preparation_state' statement")
        for value in ("pending", "ready", "met"):
            with self.subTest(value=value):
                self.assertIn(
                    value, state, f"'preparation_state' statement omits {value!r}"
                )

    def test_preparation_state_is_readiness_not_completion(self):
        state = next(
            (w for w in _windows(self.plain, "preparation_state", 400) if w),
            "",
        )
        self.assertTrue(state, "SKILL.md has no 'preparation_state' statement")
        self.assertTrue(
            "не является" in state or "не равно" in state,
            "the 'preparation_state' paragraph must state that readiness ('ready') "
            "is not completion (needs 'не является' or 'не равно'): "
            f"{state!r}",
        )

    def test_preparation_ref_is_single_authoritative(self):
        refs = _windows(self.plain, "preparation_ref", 200)
        self.assertTrue(refs, "SKILL.md has no 'preparation_ref' field")
        self.assertTrue(
            any("единственн" in window for window in refs),
            "SKILL.md must call 'preparation_ref' the single authoritative binding "
            f"(stem 'единственн' within 200 chars): {refs!r}",
        )

    def test_unit_disposition_values_are_declared(self):
        for token in ("disposition", "active", "paused", "finalized"):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    self.plain,
                    f"SKILL.md lacks the unit disposition token {token!r}",
                )

    def test_unit_preparation_artifact_and_campaign_binding(self):
        for token in ("campaign_ref", "preparation.md",
                      ".pdca/<collection-id>/units/<unit-id>/"):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    self.plain,
                    f"SKILL.md lacks the per-unit preparation token {token!r}",
                )

    def test_barrier_ready_names_both_execution_kinds(self):
        for token in ("barrier-ready", "baseline bootstrap", "change-producing DO"):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    self.plain,
                    f"SKILL.md lacks the barrier token {token!r}",
                )
        # negative: the barrier must not require a live runtime status
        for line in self.skill.splitlines():
            with self.subTest(line=line[:80]):
                self.assertIsNone(
                    _RUNTIME_STATUS_REQUIREMENT.search(line),
                    "SKILL.md must not require a runtime status at the barrier: "
                    f"{line!r}",
                )


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class OrchestratorCollectionPlanHandoffTest(unittest.TestCase):
    """pdca-orchestrator.md: a distinct COLLECTION TASK PLAN entry + plan_handoff."""

    @classmethod
    def setUpClass(cls) -> None:
        assert ORCHESTRATOR is not None
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

    def test_variants_keep_standalone_approval_and_autonomous_immediate(self):
        for name, path in BASE_VARIANTS.items():
            with self.subTest(variant=name):
                low = _plain(path.read_text(encoding="utf-8")).lower()
                self.assertTrue(
                    _APPROVAL_CONTEXT.search(low),
                    f"{name}: lost the explicit normal-mode plan-approval "
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
