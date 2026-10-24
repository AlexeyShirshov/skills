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
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
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
_OWN_PLAN_TOKENS = ("task's own PLAN", "own PLAN")
_PLAN_STATE_VALUES = ("pending", "running", "ready")
_APPROVAL_CONTEXT = re.compile(r"approv\w*", re.I)


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
        self.assertIn("barrier", p, "§P lacks the 'barrier' concept")

    def test_p_section_allows_parallel_plans(self):
        # The barrier constrains the START of DAG/lanes, not the order of PLANs.
        p = self._p_section()
        self.assertIn(
            "in parallel",
            p,
            "§P must state that the units' own PLANs run in parallel",
        )
        self.assertIn(
            "plan_cap",
            p,
            "§P must name the PLAN concurrency ceiling 'plan_cap'",
        )
        self.assertIn(
            "not about their sequence",
            p,
            "§P must state that the barrier is about readiness, not PLAN order",
        )
        self.assertIn(
            "as one block",
            p,
            "§P must say the PLAN dispatches go out in one batch, not one by one",
        )

    def test_parallel_planning_does_not_fix_the_schedule(self):
        # Parallel PLANs must not be read as parallel lanes: code overlap is
        # resolved by clustering, and a sequential chain in one group is normal.
        p = self._p_section()
        self.assertIn(
            "does not fix the schedule",
            p,
            "§P must state that a parallel PLAN does not fix the schedule",
        )
        self.assertIn(
            "overlap",
            p.lower(),
            "§P must state that intersecting footprints are resolved by clustering",
        )
        self.assertIn(
            "one group",
            p,
            "§P must state that overlapping units land in one group",
        )
        self.assertIn(
            "declares",
            p,
            "§P must state that a PLAN declares the footprint instead of reserving it",
        )

    def test_footprint_reservation_is_a_claim_not_a_lock(self):
        # The reservation must stay a real reservation (used by clustering), while
        # parallel planning must not be blocked by it.
        p = self._p_section()
        self.assertIn(
            "reservation",
            p.lower(),
            "§P must keep the footprint reservation concept",
        )
        self.assertIn(
            "not a lock",
            p.lower(),
            "§P must say the reservation is a claim, not a lock",
        )
        self.assertNotIn(
            "reserves nothing",
            p.lower(),
            "§P must not deny the reservation: clustering relies on it",
        )

    def test_status_writes_are_serialized_not_single_owner(self):
        # One writer at a time, but the physical write belongs to pdca-executor
        # (§Collection status), not to the primary directly.
        p = self._p_section()
        self.assertIn("serialized", p, "§P must say the status writes are serialized")
        self.assertIn(
            "pdca-executor",
            p,
            "§P must name pdca-executor as the physical writer of the status file",
        )
        self.assertIn("§Collection status", p, "§P must defer the write ownership to §Collection status")
        self.assertNotIn(
            "a single owner writes",
            p,
            "§P must not claim the primary is the only writer",
        )

    def test_parameters_declare_plan_concurrency(self):
        params = _plain(_section(self.skill, "## Parameters", "## Relation to the base PDCA"))
        self.assertTrue(params, "SKILL.md §Parameters section not found")
        self.assertIn(
            "PLAN parallelism ceiling",
            params,
            "§Parameters must declare a separate PLAN concurrency cap",
        )
        self.assertIn("plan_cap", params, "§Parameters must name 'plan_cap'")
        self.assertIn(
            "lanes",
            params,
            "§Parameters must keep the lane cap distinct from the PLAN cap",
        )
        self.assertIn(
            "host",
            params,
            "§Parameters must bound plan_cap by the host's real parallelism",
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
        lane = _plain(_section(self.skill, "## Lane", "## Git model"))
        self.assertTrue(lane, "SKILL.md §Lane (## Lane) section not found")
        self.assertIn("PLAN", lane, "§Lane no longer refers to PLAN")
        self.assertRegex(
            lane,
            re.compile(r"saved"),
            "§Lane must resume the already-done PLAN via 'saved ...' wording",
        )

    def test_status_section_records_plan_handoff_fields(self):
        status = _plain(_section(self.skill, "## Collection status", "## Report"))
        self.assertTrue(status, "SKILL.md §Collection status section not found")
        for field in ("plan_state", "cycle_id", "selected_variant"):
            self.assertIn(field, status, f"§Collection status must record {field!r}")
        self.assertTrue(
            "plan_revision" in status or "plan revision vector" in status.lower(),
            "§Collection status must record 'plan_revision' r (or the 'PLAN revision vector')",
        )

    def test_skill_still_forbids_automatic_recluster(self):
        # preservation guard: the new barrier must not re-enable automatic
        # relaning after lanes start.
        low = _plain(self.skill).lower()
        self.assertIn("recluster", low, "collection SKILL lost the no-recluster token")
        self.assertIn("rerun", low, "collection SKILL lost the no-rerun token")
        self.assertRegex(
            low,
            re.compile(r"automatic\w*\s+(rerun|remerge|recluster|reset|revert)"),
            "collection SKILL must still forbid automatic "
            "rerun/remerge/recluster/reset/revert",
        )


class StepPlanApprovalContractTest(unittest.TestCase):
    """SKILL.md §Lane: the normal-mode step-PLAN approval gate (AC06).

    Guards the rule written in §"Lane driver and campaign": every real step runs its
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
        lane = _plain(_section(self.skill, "## Lane", "## Stale PLAN"))
        self.assertTrue(lane, "SKILL.md §Lane (## Lane) section not found")
        # (a) normal mode ties the step PLAN approval to a *durable* pending ref
        self.assertRegex(
            lane,
            re.compile(r"normal mode.{0,400}?durable\s+pending\s+approval\s+ref", re.I),
            "§Lane must state that in normal mode the step PLAN approval is recorded "
            "as a durable pending approval ref (got: %r)" % lane[:600],
        )
        # (b) the current unit is paused for the duration of that approval
        self.assertRegex(
            lane,
            re.compile(r"pending\s+approval\s+ref.{0,200}?disposition=paused", re.I),
            "§Lane must state that the current unit gets disposition=paused at the "
            "step approval gate (got: %r)" % lane[:600],
        )
        # (c) the step brief is not the step's PLAN
        self.assertRegex(
            lane,
            re.compile(r"step\s+brief\s+does\s+not\s+replace\s+the\s+plan", re.I),
            "§Lane must state explicitly that the step brief does not replace the "
            "step's PLAN ('The step brief does not replace the PLAN')",
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
    r"(?i)(requires?|mandatory).{0,80}(Status:\s*running|runtime status)"
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
            "is not" in state or "does not equal" in state,
            "the 'preparation_state' paragraph must state that readiness ('ready') "
            "is not completion (needs 'is not' or 'does not equal'): "
            f"{state!r}",
        )

    def test_preparation_ref_is_single_authoritative(self):
        refs = _windows(self.plain, "preparation_ref", 200)
        self.assertTrue(refs, "SKILL.md has no 'preparation_ref' field")
        self.assertTrue(
            any("single" in window for window in refs),
            "SKILL.md must call 'preparation_ref' the single authoritative binding "
            f"(stem 'single' within 200 chars): {refs!r}",
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
                    "immediately" in low,
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


class CollectionPlanGapTest(unittest.TestCase):
    """SKILL.md: a failed own PLAN/preparation is a gap, never a `ready` placeholder.

    The ALL-barrier is all-or-nothing: one unplannable unit keeps the DAG, the groups
    and the lane allocation from starting, so no early DO is possible for any unit.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")
        cls.plain = _plain(cls.skill)

    def test_unplannable_unit_is_a_gap_without_a_ready_placeholder(self):
        barrier = _plain(
            _section(self.skill, "3. **ALL-barrier.**", "4. **Clustering")
        )
        self.assertTrue(barrier, "SKILL.md §P.3 ALL-barrier not found")
        self.assertIn(
            "gap",
            barrier,
            "§P.3 must call a unit without a meaningful plan a 'gap'",
        )
        self.assertIn(
            "is not marked with a ready placeholder",
            barrier,
            "§P.3 must forbid a 'ready' placeholder for a unit whose plan is impossible",
        )
        self.assertIn(
            "the barrier is not passed",
            barrier,
            "§P.3 must state that the barrier is not passed while the gap stands",
        )
        self.assertIn(
            "early DO is forbidden",
            barrier,
            "§P.3 must forbid an early DO while the barrier is open",
        )

    def test_gap_keeps_lanes_unallocated(self):
        d = _plain(_section(self.skill, "### D —", "### C —"))
        self.assertTrue(d, "SKILL.md §D section not found")
        self.assertIn(
            "only after the ALL-barrier",
            d,
            "§D must allocate lanes only after the ALL-barrier",
        )
        self.assertIn(
            "Before that step they do not exist",
            d,
            "§D must state that no lane exists before the barrier",
        )

    def test_gap_stands_for_campaign_preparation_too(self):
        windows = _windows(self.plain, "A unit without a meaningful plan", 260)
        self.assertTrue(
            windows,
            "SKILL.md lacks the shared gap sentence for both execution kinds",
        )
        window = windows[0]
        self.assertIn(
            "frame",
            window,
            "the shared gap sentence must cover a campaign whose frame is not ready",
        )
        self.assertIn(
            "not a single lane",
            window,
            "the shared gap sentence must state that no lane is allocated before the barrier",
        )
        self.assertIn(
            "for both kinds",
            window,
            "the shared gap sentence must bind both execution kinds",
        )

    def test_reentry_requires_evidence_or_a_new_oracle(self):
        windows = _windows(self.plain, "mandatory input of the own PLAN", 400)
        self.assertTrue(
            windows,
            "SKILL.md must make the previous terminal reason a required PLAN input",
        )
        window = windows[0]
        self.assertIn(
            "the evidence is now obtainable",
            window,
            "re-entry must prove the failed evidence is now obtainable",
        )
        self.assertIn(
            "redefines the oracle",
            window,
            "re-entry must either prove the evidence or re-scope the oracle",
        )
        self.assertIn(
            "otherwise the task stays a gap",
            window,
            "a silent re-run of the same criterion must leave the unit a gap",
        )


class CollectionUnitKindOwnershipTest(unittest.TestCase):
    """SKILL.md + runner: the collection PLAN owns `execution_kind`; the runner never infers it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")
        cls.plain = _plain(cls.skill)

    def test_collection_plan_decides_execution_kind_before_dispatch(self):
        p = _plain(_section(self.skill, "### P —", "### D —"))
        self.assertTrue(p, "SKILL.md §P section not found")
        windows = [
            window
            for window in _windows(p, "execution_kind", 320)
            if "decided by the collection PLAN" in window
        ]
        self.assertTrue(
            windows,
            "SKILL.md must state that the collection PLAN (`pdca-planner`) decides "
            "each unit's `execution_kind`",
        )
        window = windows[0]
        for token in (
            "pdca-planner",
            "before the per-kind dispatch",
            "passes the ready value",
            "does not infer it from the task text",
        ):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    window,
                    f"the `execution_kind` ownership sentence lost {token!r}",
                )

    def test_runner_never_classifies_the_task(self):
        runner = SKILL_DIR / "assets/agents/pdca-orchestrator.md"
        text = _plain(runner.read_text(encoding="utf-8"))
        for token in (
            "never classifies the task",
            "you do not infer it",
            "execution_kind",
        ):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    text,
                    f"the runner prompt must refuse to classify the task: {token!r} missing",
                )

    def test_unknown_execution_kind_fails_closed(self):
        windows = _windows(self.plain, "legacy files", 280)
        self.assertTrue(windows, "SKILL.md lost the legacy `execution_kind` rule")
        window = windows[0]
        for token in (
            "unknown execution_kind value",
            "fail closed",
            "not a guess",
        ):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    window,
                    f"an unknown `execution_kind` must fail closed: {token!r} missing",
                )


class CollectionPostBarrierUnitTest(unittest.TestCase):
    """SKILL.md: a campaign/unit accepted after the barrier never mutates the DAG silently."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")
        cls.revision = _plain(
            _section(cls.skill, "## Stale PLAN", "### Surface reservation")
        )

    def test_new_campaign_after_the_barrier_needs_explicit_replan(self):
        self.assertTrue(
            self.revision,
            "SKILL.md §Stale PLAN and schedule revision not found",
        )
        for token in (
            "A new campaign or a new unit after the barrier",
            "does not mutate the DAG silently",
            "explicit collection replan/reapprove",
            "in normal mode — the user",
            "The old identities, statuses and evidence are preserved",
            "there is no automatic recluster",
        ):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    self.revision,
                    f"the post-barrier unit rule lost {token!r}",
                )

    def test_schedule_revision_window_is_before_lanes_only(self):
        self.assertIn(
            "A change before the lanes start",
            self.revision,
            "the pre-lane revision window must stay named",
        )
        self.assertIn(
            "the only allowed revision window",
            self.revision,
            "the pre-lane window must stay the only allowed schedule revision",
        )
        self.assertIn(
            "After the lanes start",
            self.revision,
            "the post-lane prohibition must stay named",
        )
        self.assertIn(
            "forbidden",
            self.revision,
            "automatic rerun/remerge/recluster must stay forbidden after lanes start",
        )


if __name__ == "__main__":
    unittest.main()
