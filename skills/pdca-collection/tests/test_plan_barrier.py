"""Contract tests for the pdca-collection own-PLAN barrier and the batch form.

Normative-text contract tests for the collection contract after the family
restructure:

    every item's OWN genuine PLAN (or campaign preparation) must finish and be
    persisted BEFORE any DAG/group/clustering decision (the ALL-barrier), and a
    resumed lane must continue the already-done PLAN rather than run a fresh full
    PLAN.  The base PLAN decided the batch form; the collection classifies only
    each item (`cycle` | `campaign`) and never routes on a variant field.

Sections that moved into ``references/`` are asserted in the reference file, not
dropped.  Style mirrors ``test_verification_recovery.py``: plain ``unittest``,
``pathlib`` paths from the repository root and no third-party dependencies.
Assertions are section-scoped/normalized (locate a section, then assert within
it), never global bare keyword counts and never line-number fragile checks.

Host-config parity: the live host is not migrated to the restructured family, so
the checks that would read the deployed ``config/agents/pdca-orchestrator.md``
are explicit skips.  The canonical shipped asset (``assets/opencode-agents/``)
is asserted instead.

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
COLLECTION_STATUS_REF = SKILL_DIR / "references/status.md"
COLLECTION_LANE_REF = SKILL_DIR / "references/lane.md"
INCREMENTAL_SKILL = SKILLS_ROOT / "pdca-incremental/SKILL.md"
# Canonical shipped runner asset (in-repo, always readable) and the deployed copy
# in the host config repo (host parity; skipped — the host is not migrated).
ORCHESTRATOR_ASSET = SKILL_DIR / "assets/opencode-agents/pdca-orchestrator.md"
ORCHESTRATOR = (CONFIG / "agents/pdca-orchestrator.md") if CONFIG else None
SKIP_HOST_NOT_MIGRATED = (
    "the live host config is not migrated to the restructured PDCA family; "
    "the shipped asset is asserted instead"
)
BASE_VARIANTS = {
    "pdca": SKILLS_ROOT / "pdca/SKILL.md",
    "pdca-coder": SKILLS_ROOT / "pdca-coder/SKILL.md",
    "pdca-dotnet": SKILLS_ROOT / "pdca-dotnet/SKILL.md",
}

# The contract fixes the token families, not one exact sentence.
_OWN_PLAN_TOKENS = ("task's own PLAN", "own PLAN")
_PLAN_STATE_VALUES = ("pending", "running", "ready")
_DISPOSITION_VALUES = ("active", "paused", "finalized")
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
        # (references/status.md), not to the primary directly.
        p = self._p_section()
        self.assertIn("serialized", p, "§P must say the status writes are serialized")
        self.assertIn(
            "pdca-executor",
            p,
            "§P must name pdca-executor as the physical writer of the status file",
        )
        self.assertIn(
            "references/status.md",
            p,
            "§P must defer the write ownership to references/status.md",
        )
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
        skill = _plain(COLLECTION_STATUS_REF.read_text(encoding="utf-8"))
        windows = [
            skill[m.start(): m.start() + 240]
            for m in re.finditer(r"plan_state", skill)
        ]
        self.assertTrue(
            windows, "references/status.md lacks the 'plan_state' readiness field token"
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
        lane = _plain(COLLECTION_LANE_REF.read_text(encoding="utf-8"))
        self.assertTrue(lane, "references/lane.md not found")
        self.assertIn("the continuation of the saved own PLAN", lane)
        self.assertIn("A repeated PLAN is by default not started", lane)
        self.assertIn("the cycle continues from DO", lane)
        self.assertIn("PLAN is reopened only when staleness is detected", lane)

    def test_status_section_records_plan_handoff_fields(self):
        # The status tables moved to references/status.md; the item's form (not a
        # variant) plus the cycle/plan revision are the handoff fields.
        status = _plain(COLLECTION_STATUS_REF.read_text(encoding="utf-8"))
        self.assertTrue(status, "references/status.md not found")
        for field in ("plan_state", "cycle_id", "preparation_state", "preparation_ref"):
            self.assertIn(field, status, f"the status reference must record {field!r}")
        self.assertIn("the item's form", status)
        self.assertTrue(
            "plan_revision" in status or "plan revision vector" in status.lower(),
            "the status reference must record 'plan_revision' r (or the 'PLAN revision vector')",
        )
        self.assertNotIn("selected_variant", status)

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
    """SKILL.md §Approval barrier (normal mode): the step-PLAN approval gate.

    Guards the rule stated once in the base and applied by the collection: a step
    waiting for approval is ``disposition=paused``/``in-progress`` with a *durable*
    pending approval ref, the approval is recorded against the same ref, and
    applicability without a matching record is an approval-needed checkpoint —
    not DO and not a fresh PLAN.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")

    def test_normal_mode_step_plan_approval_is_durable_and_pauses_the_unit(self):
        """Normal-mode step gate = paused item + durable ref + applicability ≠ approval."""
        gate = _plain(_section(self.skill, "## Approval barrier (normal mode)", "## Fallback"))
        self.assertTrue(gate, "SKILL.md §Approval barrier (normal mode) not found")
        # (a) the waiting item/step is disposition=paused, not done/incomplete
        self.assertRegex(
            gate,
            re.compile(r"waiting for approval is disposition=paused.{0,120}?in-progress", re.I),
            "§Approval barrier must state that a waiting item/step is disposition=paused "
            "with the status in-progress (got: %r)" % gate[:600],
        )
        # (b) the approval itself is a durable pending ref, recorded against the same ref
        self.assertRegex(
            gate,
            re.compile(r"durable pending approval ref.{0,200}?same ref", re.I),
            "§Approval barrier must record the approval against the same durable ref "
            "(got: %r)" % gate[:600],
        )
        # (c) applicability is not approval: a missing record is a checkpoint, not DO/PLAN
        self.assertRegex(
            gate,
            re.compile(
                r"applicability without a matching record is an approval-needed "
                r"checkpoint, not DO and not a fresh PLAN",
                re.I,
            ),
            "§Approval barrier must state that applicability without a matching record "
            "is an approval-needed checkpoint, not DO and not a fresh PLAN",
        )
        self.assertRegex(
            gate,
            re.compile(r"brief, (?:a )?summary or a chat message is not an approval", re.I),
            "§Approval barrier must state that a brief/summary/message is not an approval",
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
    """SKILL.md: item form, per-item preparation barrier, disposition."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")
        cls.plain = _plain(cls.skill)

    def test_pipeline_declares_the_item_form_and_both_forms(self):
        section = _plain(_section(self.skill, "## Items: form, contract, overlay", "## Collection"))
        self.assertIn("Every item has a form, decided by the collection PLAN", section)
        for token in ("cycle", "campaign"):
            with self.subTest(token=token):
                self.assertIn(token, section, f"SKILL.md lacks the item form {token!r}")
        for legacy in ("execution_kind", "selected_variant"):
            with self.subTest(legacy=legacy):
                self.assertNotIn(legacy, self.plain)

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
        self.assertIn("disposition", self.plain, "SKILL.md lacks the disposition field")
        status = _plain(COLLECTION_STATUS_REF.read_text(encoding="utf-8"))
        for token in _DISPOSITION_VALUES:
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    status,
                    f"references/status.md lacks the item disposition value {token!r}",
                )

    def test_unit_preparation_artifact_and_campaign_binding(self):
        for token in ("campaign_ref", "preparation.md",
                      ".pdca/<collection-id>/items/<item-id>/"):
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


class OrchestratorCollectionPlanHandoffTest(unittest.TestCase):
    """The shipped runner: a distinct COLLECTION TASK PLAN entry + its handoffs.

    The in-repo asset is the canonical source and is always asserted. The deployed
    copy under ``config/agents/`` is host parity and is skipped: the live host is
    not migrated to the restructured family (it still routes on the removed
    ``execution_kind`` field), so parity would compare the new contract to an old
    implementation instead of checking anything.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = ORCHESTRATOR_ASSET.read_text(encoding="utf-8")

    def test_orchestrator_declares_collection_task_plan_entry(self):
        self.assertIn(
            "COLLECTION TASK PLAN",
            self.text,
            "the shipped runner lacks the 'COLLECTION TASK PLAN' entry",
        )

    def test_orchestrator_returns_the_form_specific_handoffs(self):
        self.assertIn("plan_handoff", self.text)
        self.assertIn("preparation_handoff", self.text)

    def test_orchestrator_routes_the_item_form_not_a_variant(self):
        self.assertIn("the unit's form", self.text)
        self.assertNotIn("execution_kind", self.text)
        self.assertNotIn("selected_variant", self.text)

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_deployed_copy_matches_the_shipped_asset(self):
        self.skipTest(
            f"{SKIP_HOST_NOT_MIGRATED}: deployed {ORCHESTRATOR} still carries the "
            "legacy execution_kind routing"
        )


class StandaloneVariantCollectionHandoffTest(unittest.TestCase):
    """The base owns approval/autonomous semantics; the overlays apply to the form.

    The overlays no longer restate the standalone approval or a collection-caller
    note — the base owns both — so this guards the replacement invariant: the base
    keeps normal-mode approval and the no-question autonomous mode, the durable
    caller-driven approval protocol, and the overlays apply to the chosen form
    without opening a second cycle.
    """

    def test_base_keeps_normal_mode_approval_and_quiet_autonomous_mode(self):
        base = _plain(BASE_VARIANTS["pdca"].read_text(encoding="utf-8"))
        self.assertRegex(base, r"## Normal-mode approval")
        self.assertIn("that approval is the only start signal", base)
        self.assertIn("Autonomous mode has no pauses and no questions", base)

    def test_base_documents_the_caller_driven_approval_protocol(self):
        base = _plain(BASE_VARIANTS["pdca"].read_text(encoding="utf-8"))
        self.assertIn("Durable approval protocol (caller-driven cycles)", base)
        self.assertIn("approval-needed checkpoint", base)
        self.assertIn("the parent asks the user", base)

    def test_overlays_apply_to_the_chosen_form_without_a_second_cycle(self):
        for name in ("pdca-coder", "pdca-dotnet"):
            with self.subTest(variant=name):
                low = _plain(BASE_VARIANTS[name].read_text(encoding="utf-8")).lower()
                self.assertIn("overlay", low)
                self.assertTrue(
                    _APPROVAL_CONTEXT.search(low) or "inherits unchanged" in low,
                    f"{name}: lost the inheritance/approval boundary",
                )
                self.assertIn("never opens a second", low)
                self.assertIn("form", low)


class CollectionPhaseContractTest(unittest.TestCase):
    """§C/§A: the common CHECK is the base's; only its PASS allows completion."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")

    def _c(self) -> str:
        return _plain(_section(self.skill, "### C —", "### A —"))

    def _a(self) -> str:
        return _plain(_section(self.skill, "### A —", "## Report"))

    def test_c_is_the_standard_check_not_a_bespoke_stage(self) -> None:
        c = self._c()
        self.assertIn("the standard CHECK of the base contract", c)
        self.assertIn("two ticks", c)
        self.assertIn("pdca-check", c)
        self.assertIn("not a separate bespoke stage", c)
        self.assertIn("§.NET check deltas", c)

    def test_c_has_no_collection_counter_and_uses_the_base_rules(self) -> None:
        c = self._c()
        self.assertIn("without a collection counter", c)
        self.assertIn("base r/n/3", c)
        self.assertIn("same defect after one fix", c)
        self.assertIn("does not get a 4th implementation CHECK", c)

    def test_pass_may_coexist_with_incomplete_groups(self) -> None:
        c = self._c()
        self.assertIn("may coexist", c)
        self.assertIn("separate fields", c)
        self.assertIn("not marked done retroactively", c)

    def test_completion_requires_the_common_pass_and_cleanup_is_disposable_only(self) -> None:
        a = self._a()
        self.assertIn("Only a PASS of the common C allows completion", a)
        self.assertIn("removes only disposable", a)
        self.assertIn("incomplete groups are never deleted", a)
        self.assertIn("A STOP before C = PASS — cleanup is forbidden", a)
        self.assertIn("Push — never", a)

    def test_campaign_acceptance_is_not_the_common_c(self) -> None:
        a = self._a()
        self.assertIn("campaign acceptance is not the common C and does not replace it", a)
        self.assertIn("§Routing campaign outcomes", a)


class CollectionFallbackContractTest(unittest.TestCase):
    """§Fallback: one flat-primary fallback, recorded, without role substitution."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")
        cls.fallback = _plain(_section(cls.skill, "## Fallback", "## Parameters"))

    def test_trigger_is_a_failed_delegation(self) -> None:
        self.assertIn("no nested delegation", self.fallback)
        self.assertIn("pdca-orchestrator cannot orchestrate pdca", self.fallback)
        self.assertIn("delegation/subagent-unavailability error", self.fallback)

    def test_one_flat_fallback_leads_one_item_per_group(self) -> None:
        self.assertIn("one flat-primary fallback", self.fallback)
        self.assertIn("one current item per group", self.fallback)
        self.assertIn("cap is an upper bound, not a guarantee", self.fallback)

    def test_the_fallback_substitutes_no_role_and_obtains_no_rights(self) -> None:
        self.assertIn("does not substitute roles", self.fallback)
        self.assertIn("does not obtain the roles' rights", self.fallback)
        self.assertIn("Notice:", self.fallback)

    def test_the_fallback_keeps_the_all_barrier_and_the_saved_plan(self) -> None:
        self.assertIn("observing the ALL-barrier", self.fallback)
        self.assertIn("continues the saved PLAN in the lane with DO", self.fallback)

    def test_capability_preflight_performs_no_dummy_work(self) -> None:
        self.assertIn("Capability preflight", self.fallback)
        self.assertIn("no trial edits, trial items or fake steps", self.fallback)
        self.assertIn("escalate → scout", self.fallback)

    def test_an_unavailable_contract_fails_closed(self) -> None:
        self.assertIn("fail closed without substituting a", self.fallback)
        self.assertIn("safe pause before the dependent action", self.fallback)


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
        windows = _windows(self.plain, "An item without a meaningful plan", 260)
        self.assertTrue(
            windows,
            "SKILL.md lacks the shared gap sentence for both item forms",
        )
        window = windows[0]
        self.assertIn(
            "plan or charter",
            window,
            "the shared gap sentence must cover a campaign whose charter is not ready",
        )
        self.assertIn(
            "not a single lane",
            window,
            "the shared gap sentence must state that no lane is allocated before the barrier",
        )
        self.assertIn(
            "for both forms",
            window,
            "the shared gap sentence must bind both item forms",
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
            "otherwise the item stays a gap",
            window,
            "a silent re-run of the same criterion must leave the item a gap",
        )


class CollectionUnitKindOwnershipTest(unittest.TestCase):
    """SKILL.md + runner: the collection PLAN owns the item form; the runner never infers it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")
        cls.plain = _plain(cls.skill)

    def test_collection_plan_decides_the_item_form_before_dispatch(self):
        p = _plain(_section(self.skill, "### P —", "### D —"))
        self.assertTrue(p, "SKILL.md §P section not found")
        windows = [
            window
            for window in _windows(p, "decides the form of every item", 320)
        ]
        self.assertTrue(
            windows,
            "SKILL.md must state that the collection PLAN (`pdca-planner`) decides "
            "each item's form",
        )
        window = windows[0]
        for token in (
            "the collection PLAN",
            "before the per-form dispatch",
            "passes the ready value",
        ):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    window,
                    f"the item-form ownership sentence lost {token!r}",
                )
        items = _plain(_section(self.skill, "## Items: form, contract, overlay", "## Collection"))
        self.assertIn("pdca-planner", items)
        self.assertIn("does not classify the item", items)

    def test_runner_never_classifies_the_task(self):
        text = _plain(ORCHESTRATOR_ASSET.read_text(encoding="utf-8"))
        for token in (
            "never classify the task",
            "do not infer it",
            "the unit's form",
        ):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    text,
                    f"the runner prompt must refuse to classify the task: {token!r} missing",
                )
        for legacy in ("execution_kind", "selected_variant"):
            with self.subTest(legacy=legacy):
                self.assertNotIn(legacy, text)

    def test_unknown_form_value_fails_closed(self):
        status = _plain(COLLECTION_STATUS_REF.read_text(encoding="utf-8"))
        windows = _windows(status, "unrecognised form value", 280)
        self.assertTrue(windows, "references/status.md lost the unknown-form rule")
        window = windows[0]
        for token in ("fail closed", "not a guess"):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    window,
                    f"an unknown form value must fail closed: {token!r} missing",
                )
        self.assertIn("read as cycle", status)


class CollectionPostBarrierUnitTest(unittest.TestCase):
    """SKILL.md: a campaign/unit accepted after the barrier never mutates the DAG silently."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = COLLECTION_SKILL.read_text(encoding="utf-8")
        lane = COLLECTION_LANE_REF.read_text(encoding="utf-8")
        cls.revision = _plain(
            _section(lane, "## Stale plan and schedule revision", "## Git model")
        )

    def test_new_campaign_after_the_barrier_needs_explicit_replan(self):
        self.assertTrue(
            self.revision,
            "SKILL.md §Stale PLAN and schedule revision not found",
        )
        for token in (
            "A new campaign or a new item after the barrier",
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
