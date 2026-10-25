"""Contract tests for the pdca-incremental skill text.

After the family restructure `pdca-incremental` is the incremental **form contract**, not a
second cycle: the base `pdca` PLAN already decided the form, the overlay and the first step,
and this file adds only what a campaign adds — the campaign unit and its credit, the shared
campaign state, the step boundary bookkeeping, the baseline bootstrap and the stop rules.

These tests pin those invariants to the normative text so an edit cannot silently turn the
skill back into a self-classifying router, a collection (parallel batch) or a single cycle
(fixed plan). The state machine, gates, roles, counters (`N`/`r`/`n`/`rv`), approval,
escalation, budgets, security and recovery stay the base's and are asserted against the base
only where a cross-contract guard needs it.

Style follows the sibling suites: plain ``unittest``, ``pathlib`` paths and section-scoped
assertions (locate a section, then assert within it), never global bare keyword counts.

Run:
    python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_DIR.parent
SKILL = SKILL_DIR / "SKILL.md"
STATUS_REF = SKILL_DIR / "references/status.md"
BASE = SKILLS_ROOT / "pdca/SKILL.md"
COLLECTION = SKILLS_ROOT / "pdca-collection/SKILL.md"
COLLECTION_REFS = SKILLS_ROOT / "pdca-collection/references"
ORCHESTRATOR = SKILL_DIR / "assets/opencode-agents/pdca-orchestrator.md"

# The host truncates tool output at 50 KiB / 2000 lines: every contract must stay below it.
HOST_LIMIT_BYTES = 50 * 1024
HOST_LIMIT_LINES = 2000


def _plain(text: str) -> str:
    """Normalize markdown emphasis/backticks and whitespace for semantic asserts."""
    return " ".join(text.replace("**", "").replace("`", "").replace("«", '"').replace("»", '"').split())


def _section(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        raise AssertionError(f"section start not found: {start!r}")
    j = text.find(end, i + len(start))
    if j < 0:
        raise AssertionError(f"section end not found: {end!r} (after {start!r})")
    return text[i:j]


def _windows(text: str, token: str, radius: int) -> list[str]:
    """Every window of ``radius`` characters on both sides of ``token``."""
    return [
        text[max(0, m.start() - radius): m.end() + radius]
        for m in re.finditer(re.escape(token), text)
    ]


class FrontmatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")
        self.head = self.text.split("---", 2)[1]

    def test_name_matches_directory(self) -> None:
        self.assertIn(f"name: {SKILL_DIR.name}\n", self.head)

    def test_description_names_the_form_role_and_the_owner(self) -> None:
        description = " ".join(self.head.split("description:", 1)[1].split())
        self.assertIn("explicitly names", description)
        self.assertIn("pdca-orchestrator", description)
        self.assertIn("incremental campaign", description.lower())
        self.assertIn("form", description)
        # loaded by the base PLAN; only an explicit user naming forces it
        self.assertIn("Loaded by the base PLAN", description)

    def test_contract_is_not_auto_advertised(self) -> None:
        self.assertIn("opencode/autoinvoke: false", self.head)
        self.assertIn("disable-model-invocation: true", self.head)


class FormNotASecondCycleTests(unittest.TestCase):
    """§Form, not a second cycle: the base PLAN already decided; no own routing table."""

    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Form, not a second cycle", "## Ownership")
        self.base = _plain(BASE.read_text(encoding="utf-8"))

    def test_the_base_plan_already_decided_form_overlay_and_first_step(self) -> None:
        self.assertIn("The base PLAN already decided", self.section)
        for token in ("the form", "the overlay", "first useful step"):
            with self.subTest(token=token):
                self.assertIn(token, self.section)

    def test_it_does_not_classify_and_keeps_no_routing_table(self) -> None:
        self.assertIn("does not classify the task", self.section)
        self.assertIn("keeps no routing table of its own", self.section)
        self.assertIn("never runs a second PLAN on the same content", self.section)

    def test_the_discriminator_is_owned_by_the_base_forms_section(self) -> None:
        self.assertIn(
            "The discriminator between an ordinary cycle, a campaign and a collection lives in "
            "../pdca/SKILL.md §Forms and is owned there",
            self.section,
        )
        # the base really carries that discriminator: three forms, independently defined
        forms = _section(self.base, "### Forms", "## Roles and host requirements")
        for form in ("Ordinary cycle", "Incremental", "Collection"):
            with self.subTest(form=form):
                self.assertIn(form, forms)
        self.assertIn("the method is unknown or the volume is unknown", forms)
        self.assertIn("independent goals", forms)

    def test_the_form_conditions_are_stated_without_a_router(self) -> None:
        for token in (
            "the method is unknown",
            "the volume is unknown",
            "knowledge not yet obtained",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.section)

    def test_an_explicit_user_choice_is_a_constraint(self) -> None:
        self.assertIn("The user's explicit choice of this contract is a constraint", self.section)
        self.assertIn("do not silently re-route", self.section)

    def test_decomposition_is_an_output_not_an_input(self) -> None:
        self.assertIn("Decomposition is an output, not an input", self.section)
        self.assertIn("A collection makes decomposition an input", self.section)
        self.assertIn("the step *is* the decomposition chosen after the previous result", self.section)
        self.assertIn("a queue of candidates, never a campaign plan", self.section)

    def test_a_bounded_step_stays_in_the_campaign(self) -> None:
        self.assertIn("does not leave the campaign on its own", self.section)
        self.assertIn("does not change the form", self.section)
        self.assertIn("§Strategic revision", self.section)


class OwnershipTests(unittest.TestCase):
    """§Ownership: campaign-control is a context of the cheap orchestrator, one writer."""

    def setUp(self) -> None:
        self.raw = SKILL.read_text(encoding="utf-8")
        self.text = _plain(self.raw)
        self.section = _section(self.text, "## Ownership", "## Campaign invariants")

    def test_campaign_control_is_a_context_not_a_new_role(self) -> None:
        self.assertIn(
            "campaign-control is a context of the existing cheap pdca-orchestrator, not a new role",
            self.section,
        )
        self.assertIn("§Control modes and the campaign owner", self.section)

    def test_the_owner_holds_the_campaign_state(self) -> None:
        for token in (
            "the durable campaign status",
            "the shared counters",
            "the accumulated knowledge",
            "the effort accounting",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.section)

    def test_steps_run_inline_without_recursion(self) -> None:
        self.assertIn("executes each step's cycle inline in its own session", self.section)
        self.assertIn(
            "without recursively spawning a new pdca-orchestrator per step or per tool call",
            self.section,
        )

    def test_the_next_step_is_the_planners_decision(self) -> None:
        self.assertIn("starts the next step only on the planner's decision", self.section)
        self.assertIn("at the step boundary", self.section)

    def test_the_owner_does_not_decide_judge_or_waive(self) -> None:
        self.assertIn("does not classify the task", self.section)
        self.assertIn("does not replan", self.section)
        self.assertIn("does not judge in place of pdca-check", self.section)
        self.assertIn("cannot waive a gate, a counter or a permission", self.section)

    def test_a_step_is_not_handed_to_cycle_control(self) -> None:
        self.assertIn(
            "A step's cycle is not handed to a separate cycle-control controller", self.section
        )
        self.assertIn("the campaign's sequence belongs to this one context", self.section)

    def test_normal_mode_keeps_per_step_user_approval(self) -> None:
        self.assertIn("the user approves each step's plan", self.section)
        self.assertIn("The primary does not take on campaign-control semantics", self.section)
        self.assertIn("approval-needed checkpoint", self.section)
        self.assertIn("never DO", self.section)
        self.assertIn("never a fresh PLAN", self.section)
        self.assertIn("Autonomous mode has no approval slots and no questions", self.section)

    def test_a_campaign_item_has_one_designated_writer(self) -> None:
        self.assertIn("One designated existing cheap controller owns its campaign state", self.section)
        self.assertIn("no competing writers", self.section)
        self.assertIn("gains no extra rights from being composed", self.section)


class CampaignInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.invariants = _section(self.text, "## Campaign invariants", "### Threshold calibration")

    def test_the_ten_invariants_are_numbered(self) -> None:
        for number in range(1, 11):
            with self.subTest(number=number):
                self.assertRegex(self.invariants, rf"(?:^|\s){number}\. [A-Z]")

    def test_goal_and_recipe_are_fixed_and_a_change_is_a_new_campaign(self) -> None:
        self.assertIn("The goal and the measurement recipe are fixed at the start", self.invariants)
        self.assertIn("The goal predicate, the unit of measurement, the denominator", self.invariants)
        self.assertIn("it is a new campaign with a new baseline", self.invariants)
        self.assertIn("backfill is forbidden", self.invariants)

    def test_one_credited_increment_per_step(self) -> None:
        self.assertIn("One credited increment per step", self.invariants)
        self.assertIn("knowledge increment", self.invariants)
        self.assertIn("A repeat without new knowledge earns nothing", self.invariants)

    def test_one_increment_may_close_the_whole_campaign(self) -> None:
        self.assertIn("no rule demands a second increment", self.invariants)
        self.assertIn(
            "one increment that satisfies the goal and passes the check ends the campaign",
            self.invariants,
        )

    def test_a_metric_and_floor_are_a_specialisation_not_a_universal_gate(self) -> None:
        self.assertIn("the metric and the floor are a specialisation, not a universal gate", self.invariants)

    def test_a_result_is_kept_not_retried_for_luck(self) -> None:
        self.assertIn("A result is kept, not retried for luck", self.invariants)
        self.assertIn("exactly one credited measurement per step", self.invariants)
        self.assertIn("objective invalidity", self.invariants)
        self.assertIn("A red measurement stays red in the record", self.invariants)

    def test_the_chain_advances_on_accepted_state_only(self) -> None:
        self.assertIn("The chain advances on accepted state", self.invariants)
        self.assertIn("never a forecast, never an intermediate value", self.invariants)
        self.assertIn("No accepted step, no next step", self.invariants)

    def test_one_step_one_lane_and_no_recursion(self) -> None:
        self.assertIn("One step at a time, one lane, no recursion", self.invariants)
        self.assertIn("A campaign is never nested inside a campaign", self.invariants)
        self.assertIn("a collection is never nested inside a campaign", self.invariants)

    def test_discovery_feeds_but_the_planner_decides(self) -> None:
        self.assertIn("Discovery feeds, the planner decides", self.invariants)
        self.assertIn("fresh gap map", self.invariants)
        self.assertIn("ranked seed", self.invariants)
        self.assertIn("the decision on the next step stays with pdca-planner", self.invariants)

    def test_state_carries_over(self) -> None:
        self.assertIn("State carries over", self.invariants)
        for token in (
            "deferred register with triggers",
            "blocked arms",
            "open tickets",
            "accepted knowledge",
            "protected/foreign changes",
            "the effort accounting",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.invariants)
        self.assertIn('"We forgot" is not a status', self.invariants)

    def test_conservative_accounting_excludes_foreign_work(self) -> None:
        self.assertIn("Conservative accounting", self.invariants)
        self.assertIn("Foreign and protected changes are excluded from the credit", self.invariants)
        self.assertIn("denominator drift is explained separately", self.invariants)

    def test_a_pause_is_not_an_outcome(self) -> None:
        self.assertIn("A pause is not an outcome", self.invariants)
        self.assertIn("disposition=paused", self.invariants)
        self.assertIn("the campaign stays open", self.invariants)
        self.assertIn("does not reset N/r/n", self.invariants)
        self.assertIn("a final unsuccessful outcome is explicit", self.invariants)

    def test_only_an_accepted_step_is_committed_and_only_when_allowed(self) -> None:
        self.assertIn("Only an accepted step is committed, and only when allowed", self.invariants)
        self.assertIn("Auto-commit is not a right of the skill", self.invariants)
        self.assertIn("Commit policy: auto | none", self.invariants)
        self.assertIn("git add <paths>", self.invariants)
        self.assertIn("not -A", self.invariants)
        self.assertIn("push — never", self.invariants)
        self.assertIn(
            "campaign completion and unit finalization are different events", self.invariants
        )


class ThresholdCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(
            self.text, "### Threshold calibration", "## Campaign status"
        )

    def test_a_threshold_without_a_baseline_is_provisional(self) -> None:
        self.assertIn("marked provisional", self.section)
        self.assertIn("§Plan fields", self.section)

    def test_revising_it_is_a_supersede_not_a_goal_change(self) -> None:
        self.assertIn(
            "Revising it on measurement is a supersede record with the reason and the evidence",
            self.section,
        )
        self.assertIn("not a goal change and not a new campaign", self.section)

    def test_red_and_on_baseline_is_asserted_by_measurement(self) -> None:
        self.assertIn(
            '"Red and on baseline" is asserted by measurement, never by assumption',
            self.section,
        )


class CampaignStatusTests(unittest.TestCase):
    """§Campaign status + references/status.md (the template moved to the reference)."""

    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Campaign status", "## Campaign cycle")
        self.ref_raw = STATUS_REF.read_text(encoding="utf-8")
        self.ref = _plain(self.ref_raw)

    def test_one_file_is_the_source_of_truth(self) -> None:
        self.assertIn("One file is the campaign's source of truth", self.section)
        self.assertIn(".pdca/status/<campaign>.md", self.section)
        self.assertIn("never move it out of the workspace root", self.section)

    def test_the_file_holds_runtime_only_with_no_second_mirror(self) -> None:
        self.assertIn("It holds runtime only", self.section)
        self.assertIn("there is no separate todo", self.section)

    def test_the_owner_composes_and_the_executor_writes(self) -> None:
        self.assertIn("The physical write is pdca-executor's on explicit dispatch", self.section)
        self.assertIn("the owner does not write files", self.section)

    def test_the_campaign_file_carries_its_own_fields(self) -> None:
        for token in (
            "the accepted steps and their credit",
            "the increment unit and its expected observable",
            "the accepted knowledge register",
            "the deferred rows with triggers",
            "the checkpoint of the last step boundary",
            "the commit policy",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.section)

    def test_the_base_schema_and_counters_stay_in_force(self) -> None:
        self.assertIn("The base schema is unchanged and applies as written", self.section)
        self.assertIn("append-only progress log", self.section)
        self.assertIn("Current cycle N", self.section)
        self.assertIn("Plan revision r", self.section)
        self.assertIn("Attempt n", self.section)
        self.assertIn("A step boundary is one logged event", self.section)

    def test_the_reference_is_linked_and_ships_the_template(self) -> None:
        self.assertIn("references/status.md has the full template", self.section)
        self.assertTrue(STATUS_REF.is_file(), "references/status.md is missing")
        for block in (
            "Status:",
            "Goal:",
            "Recipe:",
            "Allowed surface:",
            "Increment unit:",
            "Floor:",
            "Target:",
            "Preparation ref:",
            "Commit policy: none | auto",
            "Effort accounting:",
            "Current step:",
            "Baseline evidence:",
            "Next-step seed:",
            "Accepted knowledge:",
            "Deferred:",
            "Blockers:",
            "Protected/foreign:",
            "Checkpoint:",
            "Pending approval ref:",
            "Approval record:",
            "Stop verdict:",
        ):
            with self.subTest(block=block):
                self.assertIn(block, self.ref_raw)

    def test_the_step_table_is_append_only_and_carries_the_credit(self) -> None:
        self.assertIn(
            "| step | basis | target | accepted | credited | verdict | commit | evidence |",
            self.ref,
        )
        self.assertIn("The step table is append-only", self.ref)
        self.assertIn("a revised step is the same row under the same identity", self.ref)
        self.assertIn("a step that is never accepted stays not accepted", self.ref)

    def test_the_reference_field_rules_are_present(self) -> None:
        for token in (
            "is the accepted state of the previous step",
            "names what earned the increment",
            "is the independent pdca-check verdict",
            "Checkpoint is written at every step boundary",
            "Divergence between the status and the evidence: the evidence wins",
            "The knowledge register is append-only as a fact history",
            "A pause does not reset N/r/n",
            "Commit policy: none means no campaign step commits",
            "the file is finalized and kept",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.ref)

    def test_the_reference_holds_the_preparation_document_and_bootstrap_records(self) -> None:
        for token in (
            "## Preparation document",
            "the goal predicate and the measurement recipe",
            "a provisional mark on every threshold that has no measured baseline",
            "the candidate list for the first step",
            "the carrying claims and the definition of done",
            "the effort accounting (accounting only, no autonomous cap) and the commit policy",
            "A change to any of it is a new revision of the document",
            "The document is never copied into the status",
            "## Baseline bootstrap record",
            "with the same recipe that will accept steps",
            "The baseline is not a step",
            "## Checkpoint",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.ref)


class CampaignCycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.cycle = _section(self.text, "## Campaign cycle", "## Step boundary")

    def test_the_plan_phase_has_two_owners_and_no_separate_do(self) -> None:
        self.assertIn("pdca-scout gathers facts", self.cycle)
        self.assertIn("pdca-planner decides", self.cycle)
        self.assertIn("Both are PLAN; neither is a separate DO", self.cycle)

    def test_bootstrap_has_three_distinct_operations(self) -> None:
        boot = _section(self.cycle, "### 0. Bootstrap", "### 1. Discovery")
        self.assertIn("Three operations that do not substitute for each other", boot)
        self.assertIn("Preparation record", boot)
        self.assertIn("Baseline bootstrap", boot)
        self.assertIn("Change-producing DO", boot)
        self.assertIn("no runtime status is created", boot)

    def test_the_baseline_is_captured_with_the_accepting_recipe_and_is_not_a_step(self) -> None:
        boot = _section(self.cycle, "### 0. Bootstrap", "### 1. Discovery")
        self.assertIn("captured with the recipe that will accept steps", boot.lower().replace(
            "captured with the recipe", "captured with the recipe"))
        self.assertIn("it consumes no step, earns no credit and changes no product", boot)
        self.assertIn("target = baseline + floor", boot)
        self.assertIn("Status: running", boot)

    def test_bootstrap_fixes_the_goal_recipe_surface_and_a_short_candidate_list(self) -> None:
        boot = _section(self.cycle, "### 0. Bootstrap", "### 1. Discovery")
        self.assertIn("the goal predicate and the recipe", boot)
        self.assertIn("the allowed surface", boot)
        self.assertIn("short list of candidates", boot)
        self.assertIn("not a plan for the whole volume", boot)

    def test_an_inapplicable_recipe_returns_to_the_planner_and_the_approval(self) -> None:
        boot = _section(self.cycle, "### 0. Bootstrap", "### 1. Discovery")
        self.assertIn("this is a return to pdca-planner and the active approval", boot.lower())
        self.assertIn("never a silent restatement of the criteria", boot)

    def test_a_satisfying_baseline_closes_without_a_dummy_increment(self) -> None:
        boot = _section(self.cycle, "### 0. Bootstrap", "### 1. Discovery")
        self.assertIn("If the baseline already satisfies the goal", boot)
        self.assertIn("no dummy increment is created", boot)
        self.assertIn("the campaign can close", boot)

    def test_discovery_is_read_only_and_not_the_step_plan(self) -> None:
        discovery = _section(self.cycle, "### 1. Discovery", "### 2. Step brief")
        self.assertIn("pdca-scout (cheap, read-only)", discovery)
        self.assertIn("fresh gap map", discovery)
        self.assertIn("does not rank for the planner's decision", discovery)
        self.assertIn("does not write a brief", discovery)
        self.assertIn("The result is the next-step seed in the status", discovery)
        self.assertIn("Discovery is not the step's PLAN", discovery)

    def test_the_step_brief_carries_six_blocks(self) -> None:
        brief = _section(self.cycle, "### 2. Step brief", "### 3. Step execution")
        for block in (
            "1. GOAL:",
            "2. CURRENT STATE:",
            "3. HARD CONSTRAINTS:",
            "4. SCOPE:",
            "5. ACCEPTANCE:",
            "6. TARGETS:",
        ):
            with self.subTest(block=block):
                self.assertIn(block, brief)
        self.assertIn("Six is a lower bound, not a format", brief)
        self.assertIn("A project overlay may extend the blocks, never shorten them", brief)
        self.assertIn("The step's plan is a full plan of that step", brief)
        self.assertIn("not a plan of the campaign", brief)

    def test_the_brief_carries_the_commit_policy_and_the_credit_rule(self) -> None:
        brief = _section(self.cycle, "### 2. Step brief", "### 3. Step execution")
        self.assertIn("Commit policy", brief)
        self.assertIn("only the accepted step", brief)
        self.assertIn("push forbidden always", brief)
        self.assertIn("what counts as a valid increment", brief)

    def test_step_execution_is_the_base_cycle_under_the_base_gates(self) -> None:
        step = _section(self.text, "### 3. Step execution", "## Step boundary")
        self.assertIn("The step runs the base cycle", step)
        self.assertIn("PLAN (r, rv) → DO → CHECK → ACT", step)
        self.assertIn("The form is never re-decided per step", step)
        self.assertIn("the overlay never opens a second PLAN or a second status", step)
        self.assertIn("this is a loop-back inside the step", step)
        self.assertIn("not \"a next step with a shortfall\"", step)
        self.assertIn("A red result is kept", step)


class StepBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Step boundary", "## Acceptance and carry-over")

    def test_one_planner_call_decides_and_emits_one_brief_or_stop(self) -> None:
        self.assertIn("one planner call decides", self.section)
        self.assertIn("in the same turn, emits either a brief or a STOP", self.section)
        self.assertIn("§Lens, \"step boundary — one planner call\"", self.section.replace(
            "§Lens, \"step boundary", "§Lens, \"step boundary"))

    def test_accept_revise_and_new_step_are_distinct(self) -> None:
        for token in ("accept the increment", "revise/reject the same step", "a new step"):
            with self.subTest(token=token):
                self.assertIn(token, self.section)
        self.assertIn("The step number does not grow without acceptance", self.section)

    def test_revising_keeps_the_same_identity(self) -> None:
        self.assertIn("a corrected brief of the same step identity", self.section)
        self.assertIn("the independent CHECK is never rewritten to met", self.section)
        self.assertIn("no increment is credited for bypassing a failed CHECK", self.section)

    def test_a_failed_step_has_a_blast_radius_of_one_step(self) -> None:
        self.assertIn("A failed step never closes the rest of the campaign by itself", self.section)
        self.assertIn("the blast radius is one step", self.section)
        self.assertIn("the route stays the planner's", self.section)

    def test_a_new_step_preserves_history_budgets_and_attempts(self) -> None:
        self.assertIn("history, counters and accounting are preserved", self.section)
        self.assertIn("every actual cost and attempt counts", self.section)
        self.assertIn(
            "an unaccepted red step is never converted into extra accepted progress", self.section
        )

    def test_a_separate_final_check_adds_no_planner_call(self) -> None:
        self.assertIn("A separate final check adds no planner call", self.section)
        self.assertIn("pre-set STOP condition", self.section)
        self.assertIn("without a new planner call", self.section)
        self.assertIn("routing a pre-approved decision, not its own verdict", self.section)
        self.assertIn("a non-PASS is a planner loop-back", self.section)

    def test_the_planner_call_accounting_is_one_plus_steps_without_a_cap(self) -> None:
        self.assertIn("Planner calls are accounted, not capped", self.section)
        self.assertIn("the successful path is 1 + number of steps", self.section)
        self.assertIn("genuine revisions", self.section)
        self.assertIn("Separate DECIDE → brief → STOP turns on the same content are a repeated PLAN", self.section)
        self.assertIn("two calls", self.section)

    def test_stop_with_met_needs_the_whole_goal_check(self) -> None:
        self.assertIn("STOP with met/limited requires the whole-goal CHECK", self.section)
        self.assertIn("unreachable requires the proven remainder", self.section)


class AcceptanceAndCarryOverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Acceptance and carry-over", "## Stop")

    def test_verdict_route_and_write_have_three_owners(self) -> None:
        self.assertIn("The verdict is pdca-check's", self.section)
        self.assertIn("the route is pdca-planner's at the boundary", self.section)
        self.assertIn("the physical write is pdca-executor's", self.section)
        self.assertIn("ACCEPT and the route do not merge", self.section)
        self.assertIn("the reviewer must not choose the next step", self.section)

    def test_the_step_table_is_appended_and_keeps_red_rows(self) -> None:
        self.assertIn("append the row to the step table", self.section)
        self.assertIn("Accepted rows are append-only", self.section)
        self.assertIn("a revised step stays the same row under the same identity", self.section)
        self.assertIn("a step that is never accepted stays not accepted", self.section)

    def test_the_basis_advances_with_knowledge_when_that_is_the_credit(self) -> None:
        self.assertIn("Advance the basis", self.section)
        self.assertIn("a knowledge increment advances it with knowledge, not with an invented number", self.section)

    def test_the_commit_is_scoped_and_never_a_push(self) -> None:
        self.assertIn("commit only the accepted step's paths", self.section)
        self.assertIn("record the tip in the commit cell", self.section)
        self.assertIn("push never", self.section)
        self.assertIn("record no commit and the reason", self.section)
        self.assertIn("not in the commit", self.section)

    def test_the_knowledge_register_is_an_append_only_fact_history(self) -> None:
        self.assertIn("The knowledge register is an append-only fact history", self.section)
        self.assertIn("An accepted conclusion may be superseded with a reason", self.section)
        self.assertIn("nothing is backfilled", self.section)
        self.assertIn("the working result and the fact history are different things", self.section)


class StopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Stop", "## Verification")

    def test_the_stop_table_has_the_five_outcomes(self) -> None:
        for status in ("met", "unreachable", "blocked", "stopped", "limited"):
            with self.subTest(status=status):
                self.assertIn(f"| {status} |", self.section)

    def test_met_is_the_only_success_and_needs_the_whole_goal_check(self) -> None:
        self.assertIn("met is the only success", self.section)
        self.assertIn("the campaign record's done", self.section)
        self.assertIn("needs the whole-goal CHECK", self.section)
        self.assertIn("a set of accepted increments and PASS on every mechanical row does not prove the whole goal", self.section)

    def test_the_claims_veto_outranks_a_rubric_score(self) -> None:
        self.assertIn(
            "never compensates a confirmed/unverified finding against a carrying claim", self.section
        )
        self.assertIn("§Claims and veto", self.section)

    def test_limited_is_a_narrowing_inside_the_original_goal(self) -> None:
        self.assertIn("limited is a narrowing inside the original goal, never a weakened goal", self.section)
        self.assertIn("in normal mode the user approves it", self.section)

    def test_unreachable_is_proven_with_numbers(self) -> None:
        self.assertIn("unreachable is proven with numbers", self.section)
        self.assertIn("never declared from fatigue", self.section)

    def test_blocked_and_stopped_do_not_pretend_to_close_the_chain(self) -> None:
        self.assertIn("the chain does not pretend to be closed", self.section)
        self.assertIn("continues from the last accepted basis", self.section)
        self.assertIn("invariant 9 decides whether the campaign is paused or finally closed", self.section)


class VerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Verification", "## Effort accounting and safety")

    def test_a_step_check_is_local_and_the_whole_goal_check_is_separate(self) -> None:
        self.assertIn("A step check is local", self.section)
        self.assertIn("The whole-goal check is separate", self.section)
        self.assertIn("§Local and whole-goal checks", self.section)

    def test_not_per_probe(self) -> None:
        self.assertIn("Not per probe", self.section)
        self.assertIn("several related probes in one increment give one CHECK", self.section)
        self.assertIn("a tool call starts no PLAN and owes no CHECK", self.section)

    def test_no_second_judge_by_default(self) -> None:
        self.assertIn("No second judge by default", self.section)
        self.assertIn("a margin over the rubric threshold", self.section)
        self.assertIn("an unresolved finding against a carrying claim", self.section)

    def test_no_bespoke_verifier_for_completeness(self) -> None:
        self.assertIn("No bespoke verifier \"for completeness\"", self.section)
        self.assertIn("§Verification economy", self.section)

    def test_credit_does_not_replace_the_check(self) -> None:
        self.assertIn("Credit does not replace the check", self.section)
        self.assertIn("an unconfirmed claim is unverified, never met", self.section)


class BudgetAndSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Effort accounting and safety", "## Economics and sizing")

    def test_no_autonomous_cutoff_and_explicit_normal_opt_in(self) -> None:
        self.assertIn("There is no autonomous cutoff", self.section)
        self.assertIn("no legacy/plan/resume budget is revived", self.section)
        self.assertIn("An accepted whole goal closes the campaign normally", self.section)
        self.assertIn("verified irreducible blocker for the agreed goal", self.section)
        self.assertIn("failed candidate or incomplete evidence alone is not a blocker", self.section)
        self.assertIn("the same cutoff", self.section)
        self.assertIn("persists across a normal-mode resume or genuine replan", self.section)
        self.assertIn("only a switch to autonomous drops it", self.section)

    def test_the_base_safety_rules_are_not_relaxed(self) -> None:
        self.assertIn("The no-4th-pass rule, security/permissions boundaries", self.section)
        self.assertIn("this contract does not relax them", self.section)
        self.assertIn("No new universal minutes or costs", self.section)

    def test_the_commit_policy_is_the_only_campaign_specific_permission(self) -> None:
        self.assertIn("the commit policy of invariant 10 is the only campaign-specific permission", self.section)
        self.assertIn("push is never part of it", self.section)


class EconomicsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Economics and sizing", "## Red flags")

    def test_a_step_has_a_fixed_price(self) -> None:
        self.assertIn("A step has a fixed price", self.section)
        self.assertIn("An increment cheaper than that price does not pay off", self.section)

    def test_an_oversized_step_is_bad(self) -> None:
        self.assertIn("An oversized step is bad too", self.section)
        self.assertIn("its PLAN is written blind", self.section)

    def test_the_number_of_steps_is_not_planned(self) -> None:
        self.assertIn("The number of steps is not planned", self.section)
        self.assertIn('"ten steps" is a consequence, never a goal', self.section)

    def test_the_last_step_takes_the_whole_remainder(self) -> None:
        self.assertIn("The last step takes the whole remainder", self.section)
        self.assertIn("2×floor", self.section)
        self.assertIn("never \"the floor, because it is easier\"", self.section)


class RedFlagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.flags = _section(self.text, "## Red flags", "## Recovery")

    def test_campaign_specific_red_flags_are_present(self) -> None:
        for token in (
            "I wrote a forecast or an intermediate value into the accepted column",
            "repeated a failed measurement for a nicer number",
            "I moved the threshold, the denominator or a filter",
            "I ran two increments in parallel",
            "I declared met on a step-local or partial check",
            "I let DECIDE turn into a second planner call",
            "I built a \"full plan\" or a projected backlog before acting",
            "I demanded a second increment after the goal was satisfied and checked",
            "I let a rubric score or a threshold margin outvote a carrying-claim finding",
            "I repeated an accepted step after a controller loss, or reset a counter or the history",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.flags)

    def test_the_base_flag_list_still_governs(self) -> None:
        self.assertIn("The base list still governs", self.flags)


class RecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.section = _section(self.text, "## Recovery", "## References")

    def test_a_checkpoint_is_recorded_at_every_step_boundary(self) -> None:
        self.assertIn("A checkpoint is recorded at every step boundary", self.section)
        for token in (
            "the accepted basis",
            "the current step",
            "the counters",
            "the remaining accounting",
            "the next-step seed",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.section)

    def test_accepted_steps_are_never_repeated_and_counters_are_not_reset(self) -> None:
        self.assertIn("Accepted steps are never repeated", self.section)
        self.assertIn("N/r/n, the accounting and the defect history are not reset", self.section)
        self.assertIn("the work continues from the last checkpoint", self.section)

    def test_a_context_exhaustion_is_a_handover_to_the_same_role(self) -> None:
        self.assertIn("a planned handover to a new session of the same cheap pdca-orchestrator", self.section)
        self.assertIn("not a new role and not a second writer", self.section)

    def test_missing_evidence_is_re_measured_not_restored_from_memory(self) -> None:
        self.assertIn("A result whose evidence is missing is not accepted", self.section)
        self.assertIn("re-measured by the recipe, never restored from memory", self.section)


class ReferenceIntegrityTests(unittest.TestCase):
    def test_every_referenced_file_exists(self) -> None:
        raw = SKILL.read_text(encoding="utf-8")
        paths = set(re.findall(r"`(\.\./[^`]*?SKILL\.md|references/[a-z]+\.md)`", raw))
        self.assertIn("references/status.md", paths)
        self.assertIn("../pdca/SKILL.md", paths)
        for rel in sorted(paths):
            with self.subTest(path=rel):
                self.assertTrue((SKILL_DIR / rel).is_file(), f"dangling reference: {rel}")

    def test_each_phase_reference_of_the_family_exists(self) -> None:
        for rel in (
            "../pdca/references/plan.md",
            "../pdca/references/check.md",
            "../pdca/references/act.md",
        ):
            with self.subTest(path=rel):
                self.assertTrue((SKILL_DIR / rel).is_file())

    def test_the_reference_list_names_the_load_points(self) -> None:
        text = _plain(SKILL.read_text(encoding="utf-8"))
        refs = _section(text, "## References", text[-200:])
        self.assertIn("references/status.md", refs)
        self.assertIn("Load at bootstrap and at every status write", refs)
        self.assertIn("the base: one PLAN and the forms", refs)
        self.assertIn("50 KiB / 2000 lines", refs)


class ArchitectureGuardTests(unittest.TestCase):
    """The restructured family: form naming, one owner, one increment may close, veto."""

    def setUp(self) -> None:
        self.raw = SKILL.read_text(encoding="utf-8")
        self.text = _plain(self.raw)
        self.base_raw = BASE.read_text(encoding="utf-8")
        self.collection_raw = COLLECTION.read_text(encoding="utf-8")

    CONTRACT_FILES = (
        BASE,
        SKILL,
        STATUS_REF,
        COLLECTION,
        COLLECTION_REFS / "lane.md",
        COLLECTION_REFS / "status.md",
    )

    def test_no_legacy_routing_fields_in_any_contract(self) -> None:
        # `selected_variant` / `execution_kind` were the old router; the form
        # (`cycle` | `campaign`) + contract + overlay replaced them entirely.
        for path in self.CONTRACT_FILES:
            with self.subTest(path=str(path)):
                raw = path.read_text(encoding="utf-8")
                self.assertNotIn("selected_variant", raw)
                self.assertNotIn("execution_kind", raw)

    def test_the_contract_names_the_form_the_base_decided(self) -> None:
        self.assertIn("## Form, not a second cycle", self.text)
        self.assertIn("One PLAN chose the form (incremental)", self.text)
        self.assertIn("The base PLAN already decided", self.text)
        # the base entry table routes the decided form to this contract
        self.assertIn("| incremental campaign | `pdca-incremental` |", self.base_raw)
        self.assertIn("cheap `pdca-orchestrator` in campaign-control", self.base_raw)

    def test_the_collection_names_the_item_form_and_contract(self) -> None:
        section = _plain(_section(
            self.collection_raw, "## Items: form, contract, overlay", "## Collection (P / D / C / A)"
        ))
        self.assertIn("Every item has a form, decided by the collection PLAN", section)
        self.assertIn("`cycle` — one cycle of the chosen contract+overlay", self.collection_raw)
        self.assertIn("`campaign` — one incremental campaign", self.collection_raw)
        self.assertIn("The item carries no contract/overlay", section.replace("no **contract/overlay**", "no contract/overlay"))

    def test_campaign_ownership_has_no_competing_writers(self) -> None:
        self.assertIn("no competing writers", self.text)
        base = _plain(self.base_raw)
        self.assertIn("no competing writers", base)
        collection = _plain(self.collection_raw)
        self.assertIn("No competing writers", collection)
        self.assertIn("the collection owner never writes or advances a campaign", collection)
        # the runner asset is the same cheap orchestrator, not an extra agent
        asset = ORCHESTRATOR.read_text(encoding="utf-8")
        self.assertIn("campaign-control", asset)
        self.assertNotIn("campaign-agent", asset)
        self.assertNotIn("cycle-agent", asset)

    def test_one_increment_may_close_the_campaign(self) -> None:
        self.assertIn("one increment that satisfies the goal and passes the check ends the campaign", self.text)
        self.assertIn("no rule demands a second increment", self.text)
        stop = _section(self.text, "## Stop", "## Verification")
        self.assertIn("met is the only success", stop)

    def test_the_claims_veto_and_the_whole_goal_check_are_present(self) -> None:
        stop = _section(self.text, "## Stop", "## Verification")
        self.assertIn("needs the whole-goal CHECK", stop)
        self.assertIn("against a carrying claim", stop)
        verification = _section(self.text, "## Verification", "## Effort accounting and safety")
        self.assertIn("The whole-goal check is separate", verification)
        base = _plain(self.base_raw)
        self.assertIn("Claims and veto", base)
        self.assertIn("A confirmed or unverified finding against a carrying claim forbids PASS", base)

    def test_every_contract_stays_under_the_host_limit(self) -> None:
        for path in self.CONTRACT_FILES:
            with self.subTest(path=str(path)):
                raw = path.read_bytes()
                self.assertLess(
                    len(raw), HOST_LIMIT_BYTES,
                    f"{path} is {len(raw)} bytes, over the {HOST_LIMIT_BYTES}-byte host limit",
                )
                self.assertLess(
                    len(raw.decode("utf-8").splitlines()), HOST_LIMIT_LINES,
                    f"{path} is over the {HOST_LIMIT_LINES}-line host limit",
                )


class RunnerAssetContractTests(unittest.TestCase):
    """The shipped runner mirrors the form vocabulary of the contracts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = ORCHESTRATOR.read_text(encoding="utf-8")
        cls.text = _plain(cls.raw)

    def test_runner_declares_the_three_contexts(self) -> None:
        for context in ("cycle-control", "campaign-control", "collection-lane"):
            with self.subTest(context=context):
                self.assertIn(context, self.text)

    def test_runner_holds_the_campaign_inline(self) -> None:
        self.assertIn("inline in your own session", self.text)
        self.assertIn("The next step starts only on the planner's decision", self.text)

    def test_runner_never_classifies_or_routes_the_form(self) -> None:
        self.assertIn("never classify the task, choose the form or pick an overlay", self.text)
        self.assertIn("fail closed", self.text)

    def test_runner_records_the_stop_from_a_pre_approved_condition(self) -> None:
        self.assertIn("record the STOP without a new planner call", self.text)
        self.assertIn("routing a pre-approved decision, not your own verdict", self.text)


if __name__ == "__main__":
    unittest.main()
