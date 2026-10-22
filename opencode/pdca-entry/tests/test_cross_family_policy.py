"""Cross-family regression guard for the twelve reconciled PDCA policies.

Each test names a concrete scenario and checks the *same* decision in every
contract that has to agree: entry, incremental, collection, cycle base and the
shared runner.  The negative assertions are deliberate: they pin the removed
old clauses (built-in role substitutes, unit-level campaign variant, CHECK
writing the manifest, the `>=2 disjoint footprints` entry rule, patch-only
git fallback) so a future edit cannot silently restore them.

Run from the repository root:
    python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILLS = REPO / "opencode"
ENTRY = SKILLS / "pdca-entry/SKILL.md"
INCREMENTAL = SKILLS / "pdca-incremental/SKILL.md"
COLLECTION = SKILLS / "pdca-collection/SKILL.md"
BASE = SKILLS / "pdca/SKILL.md"
CODER = SKILLS / "pdca-coder/SKILL.md"
DOTNET = SKILLS / "pdca-dotnet/SKILL.md"
RUNNER = SKILLS / "pdca/assets/agents/pdca-orchestrator.md"
COLLECTION_RUNNER = SKILLS / "pdca-collection/assets/agents/pdca-orchestrator.md"
CHECK_ASSETS = (
    SKILLS / "pdca/assets/agents/pdca-check.md",
    SKILLS / "pdca-coder/assets/agents/pdca-check.md",
    SKILLS / "pdca-dotnet/assets/agents/pdca-check.md",
)
RUNNER_COPIES = tuple(
    SKILLS / name / "assets/agents/pdca-orchestrator.md"
    for name in ("pdca", "pdca-coder", "pdca-dotnet", "pdca-entry",
                 "pdca-incremental", "pdca-collection")
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flat(path: Path) -> str:
    return re.sub(r"\s+", " ", read(path))


def section(text: str, heading: str) -> str:
    """Return one heading's body, flattened, up to the next heading of any level."""
    heading = re.sub(r"^#{1,6}[ \t]+", "", heading)
    match = re.search(
        r"(?m)^#{1,6}[ \t]+" + re.escape(heading) + r"[ \t]*\r?\n(.*?)(?=^#{1,6}[ \t]+|\Z)",
        text,
        re.S,
    )
    if match is None:
        raise AssertionError(f"section not found: {heading!r}")
    return re.sub(r"\s+", " ", match.group(1))


def assert_absent(test: unittest.TestCase, source: str, *phrases: str) -> None:
    for phrase in phrases:
        with test.subTest(removed=phrase):
            test.assertNotIn(re.sub(r"\s+", " ", phrase), source,
                             f"obsolete clause came back: {phrase!r}")


class RoutingScenarios(unittest.TestCase):
    """Scenario: three independent tasks, one lane / one shared footprint."""

    def test_batch_with_independent_goals_is_collection_even_with_one_lane(self) -> None:
        entry = flat(ENTRY)
        self.assertIn("independent tasks with their own goals", entry)
        self.assertIn("parallelism is optional", entry)
        inc = flat(INCREMENTAL)
        self.assertIn("independent goals", inc)
        self.assertIn("even with one footprint/one lane", inc)
        self.assertIn("property of the schedule", inc)
        # The old entry rule (>=2 disjoint footprints) is gone.
        assert_absent(self, inc,
                      "≥2 непересекающихся footprint",
                      "≥2 non-intersecting footprints")

    def test_one_shared_goal_with_unknown_path_is_incremental(self) -> None:
        inc = flat(INCREMENTAL)
        self.assertIn("one shared goal/metric", inc)
        self.assertIn("information-dependent", inc)
        self.assertIn("one shared verifiable goal/metric", inc)


class CampaignPreparationScenarios(unittest.TestCase):
    """Scenario: a collection unit whose execution_kind is campaign."""

    def test_campaign_prepares_a_frame_not_a_cycle_plan(self) -> None:
        runner = flat(RUNNER)
        self.assertIn("execution_kind=campaign", runner)
        self.assertIn("immutable preparation document", runner)
        self.assertIn("preparation_handoff", runner)
        self.assertIn("no unit-level `selected_variant`", runner)
        col = flat(COLLECTION)
        self.assertIn("A unit-level `selected_variant` is **not** required at the barrier", col)
        self.assertIn("preparation_handoff", col)
        self.assertIn("The baseline, the runtime status, the plans of future steps", col)

    def test_lane_carries_prep_refs_and_caller_selection_rule(self) -> None:
        col = flat(COLLECTION)
        self.assertIn("`preparation_ref`/`campaign_ref` and **the dispatching rule", col)
        self.assertIn("stack rule", col)
        self.assertIn("persisted in the durable record of the step **before** the step", col)
        # The old "step's selected_variant" input field is gone.
        self.assertNotIn("the step's `selected_variant` and dispatch rule", flat(RUNNER))


class ResumeScenarios(unittest.TestCase):
    """Scenario: a lane continues a task whose PLAN was persisted in phase P."""

    def test_resume_keeps_identity_and_does_not_replan(self) -> None:
        runner = flat(RUNNER)
        self.assertIn("Resume from a persisted `plan_handoff`", runner)
        self.assertIn("same** cycle identity", runner)
        self.assertIn("`N`, `r`,", runner)
        self.assertIn("unconditional second PLAN", runner)
        self.assertIn("DO → CHECK → ACT", runner)
        col = flat(COLLECTION)
        self.assertIn("the same `selected_variant`/N/`r`/`n`", col)
        self.assertIn("through the roles", col)

    def test_all_six_runner_copies_are_identical(self) -> None:
        canonical = read(RUNNER)
        for path in RUNNER_COPIES:
            with self.subTest(copy=path.parents[2].name):
                self.assertEqual(canonical, read(path))


class ApprovalScenarios(unittest.TestCase):
    """Scenario: normal-mode step waits for the user; compaction intervenes."""

    def test_durable_approval_binds_cycle_revision_and_criteria(self) -> None:
        runner = flat(RUNNER)
        protocol = section(read(RUNNER), "## Normal-mode approval protocol")
        self.assertIn("durable pending approval ref", runner)
        self.assertIn("task/`cycle_id`", protocol)
        self.assertIn("cycle `N`", protocol)
        self.assertIn("plan revision `r`", protocol)
        self.assertIn("acceptance criteria set", protocol)
        self.assertIn("never obtains user approval", runner)
        self.assertIn("same cycle/step", runner)
        self.assertIn("not `done` and not `incomplete`", runner)
        col = flat(COLLECTION)
        self.assertIn("Approval protocol (normal mode)", col)
        self.assertIn("durable pending approval ref", col)
        inc = flat(INCREMENTAL)
        self.assertIn("Normal mode: the step approval", inc)

    def test_blanket_no_interactive_cycles_wording_is_gone(self) -> None:
        assert_absent(self, flat(RUNNER),
                      "Do not drive interactive (approval-gated) cycles",
                      "Do not drive interactive")


class RepairAndMetScenarios(unittest.TestCase):
    """Scenario: an increment fails, one repair succeeds, then verify runs."""

    def test_repair_advances_the_last_accepted_baseline_once(self) -> None:
        inc = flat(INCREMENTAL)
        self.assertIn("the last **accepted** baseline", inc)
        self.assertIn("only once", inc)
        self.assertIn("its delta is not credited", inc)
        self.assertIn("`verify` does not move the baseline", inc)

    def test_met_needs_the_goal_and_all_due_verify(self) -> None:
        inc = flat(INCREMENTAL)
        self.assertIn("all **due** mandatory `verify`", inc)
        self.assertIn("current accepted snapshot", inc)
        self.assertIn("baseline already satisfies the goal", inc)
        assert_absent(self, inc,
                      "предикат истинен на принятом замере; единственный успех")


class ActScenarios(unittest.TestCase):
    """Scenario: ACT discovers a missing test after CHECK already passed."""

    def test_act_is_bookkeeping_only_in_coder_and_dotnet(self) -> None:
        for path in (CODER, DOTNET):
            text = flat(path)
            with self.subTest(skill=path.parent.name):
                self.assertIn("no product/test/checked artifact", text)
                self.assertIn("ACT is bookkeeping", text)
                self.assertIn("AGENTS.md/registry update is bookkeeping-only", text)
                self.assertIn("ACT does **not** add or edit tests", text)
        self.assertIn("bookkeeping and finalization only", flat(BASE))

    def test_old_gate4_mutation_clause_is_gone(self) -> None:
        for path in (CODER, DOTNET):
            assert_absent(self, flat(path),
                          "AGENTS.md/registries/tests are updated and verified",
                          "AGENTS.md/registries/tests are updated")


class RoleScenarios(unittest.TestCase):
    """Scenario: a required role is absent; no built-in substitute is allowed."""

    def test_required_roles_are_resource_blockers(self) -> None:
        for path in (CODER, DOTNET):
            text = flat(path)
            with self.subTest(skill=path.parent.name):
                self.assertIn("| GATHER (facts) | `pdca-scout` | read-only, cheap | resource blocker |", text)
                self.assertIn("| PLAN (decisions) | `pdca-planner` | read-only, no delegation | resource blocker |", text)
                self.assertTrue(
                    "not a reason to substitute a built-in" in text
                    or "never substitute a built-in" in text
                )
                self.assertNotIn("built-in fallback is acceptable", text)
                self.assertNotIn("run on them", text)

    def test_flat_fallback_keeps_parallel_independent_groups(self) -> None:
        col = flat(COLLECTION)
        self.assertIn("Independent groups keep the allowed parallelism", col)
        self.assertIn("up to `cap` groups at a time", col)
        self.assertIn("sequentially", col)
        self.assertIn("**one** flat-primary fallback", col)
        assert_absent(self, col, "one lane at a time")


class CheckWriteScenarios(unittest.TestCase):
    """Scenario: CHECK finds a non-binding audit row; the manifest must be written once."""

    def test_check_returns_an_instruction_the_executor_writes(self) -> None:
        for path in CHECK_ASSETS:
            text = flat(path)
            with self.subTest(asset=path.parents[2].name):
                self.assertIn("append instruction", text)
                self.assertIn("pdca-executor", text)
                self.assertIn("never writes", text)
        for path in (BASE, CODER, DOTNET):
            text = flat(path)
            with self.subTest(skill=path.parent.name):
                self.assertIn("CHECK never writes", text)
                self.assertIn("append instruction", text)

    def test_old_check_self_write_wording_is_gone(self) -> None:
        for path in (*CHECK_ASSETS, BASE, CODER, DOTNET):
            assert_absent(self, flat(path),
                          "CHECK appends an explicit",
                          "append a disposition to the same manifest")


class ManifestScenarios(unittest.TestCase):
    """Scenario: CHECK -> DO under an unchanged plan, then a re-gather."""

    def test_new_attempt_gets_a_new_immutable_generation(self) -> None:
        for path in (BASE, CODER, DOTNET):
            text = flat(path)
            with self.subTest(skill=path.parent.name):
                self.assertIn("evidence generation", text)
                self.assertIn("task/N/r/n", text)
                self.assertIn("CHECK → DO", text)
                self.assertIn("new immutable generation", text)
        self.assertIn("Helper compatibility", flat(DOTNET))
        for path in (BASE, CODER, DOTNET):
            assert_absent(self, flat(path), "new manifest version")


class NewCampaignScenarios(unittest.TestCase):
    """Scenario: the user changes the coverage threshold mid-campaign."""

    def test_changed_goal_or_recipe_is_a_new_campaign(self) -> None:
        inc = flat(INCREMENTAL)
        self.assertIn("A change of the **goal, recipe, threshold or floor**", inc)
        self.assertIn("a new campaign with a new baseline", inc)
        col = flat(COLLECTION)
        self.assertIn("A change of the **goal, measurement recipe, threshold or floor**", col)
        self.assertIn("NEW CAMPAIGN", col.upper())
        self.assertIn("compatible with the unchanged", col)

    def test_preparation_revision_does_not_absorb_a_goal_change(self) -> None:
        col = flat(COLLECTION)
        self.assertIn("is not a revision", col)
        self.assertIn("the old immutable revisions are not rewritten", col)
        self.assertNotIn(
            "not a \"refinement\": that is `pdca-planner` and the applicable approval, "
            "then a **new immutable revision** of the preparation document",
            col,
        )


class GitScenarios(unittest.TestCase):
    """Scenario: multi-group run with an explicit no-commit request; then revocation."""

    def test_multi_group_no_commit_is_a_preflight_blocker(self) -> None:
        col = flat(COLLECTION)
        self.assertIn("preflight blocker before worktree/lane allocation", col)
        self.assertIn("The absence of authorization is **not** an authorization", col)
        self.assertIn("one group", col.lower())
        self.assertIn("safe stop", col.lower())

    def test_old_patch_only_fallback_is_gone(self) -> None:
        col = flat(COLLECTION)
        assert_absent(self, col,
                      "Without authorization there are no commits and no merge",
                      "there are no commits and no merge; the deny is not bypassed",
                      "without it — a patch fallback")
        guide = flat(REPO / "docs/pdca-guide.md")
        assert_absent(self, guide,
                      "Without permission there are no commits or merges",
                      "the group proceeds without them")


class IncrementKindScenarios(unittest.TestCase):
    """Text guard: an increment fails and an accepted repair advances the baseline."""

    def test_increment_is_not_the_only_baseline_mover(self) -> None:
        inc = read(INCREMENTAL)
        step_kinds = section(inc, "### 3.1. Step kinds: increment, repair, verify")
        self.assertNotIn("only it moves", step_kinds.lower())
        self.assertIn("`increment` or an accepted `repair`", step_kinds)
        self.assertIn("exactly once", step_kinds)
        self.assertIn("`verify` does not move the baseline", step_kinds)

    def test_docs_state_repair_moves_the_baseline_once(self) -> None:
        for path, repair_phrase, verify_phrase in (
            (REPO / "docs/pdca-incremental.md",
             "A `repair` advances the baseline from the last accepted baseline once",
             "`verify` does not move the baseline"),
            (REPO / "docs/ru/pdca-incremental.md",
             "`repair` двигает baseline от последнего принятого baseline один раз",
             "`verify` baseline не двигает"),
        ):
            text = flat(path)
            with self.subTest(doc=path.name):
                self.assertIn(repair_phrase, text)
                self.assertIn(verify_phrase, text)
                assert_absent(self, text, "Только он двигает", "only it moves")


class ContractScopeScenarios(unittest.TestCase):
    """Text guard: campaign preparation starts before any step variant exists."""

    def test_selected_variant_is_scoped_to_cycle_or_step(self) -> None:
        runner = read(RUNNER)
        contract = section(runner, "## Contract")
        self.assertIn("New/resumed cycle", contract)
        self.assertIn("concrete campaign step", contract)
        self.assertIn("Campaign preparation / lane entry", contract)
        self.assertIn("no unit-level `selected_variant`", contract)
        self.assertIn("not an error", contract)
        self.assertIn("incremental campaign contract by exact ID", contract)
        self.assertIn("dispatch selection rule", contract)
        self.assertNotIn(
            "The cycle contract is **given, not chosen**: the dispatch carries it as `selected_variant`",
            contract,
        )

    def test_input1_and_input3_agree_on_campaign_preparation(self) -> None:
        runner = read(RUNNER)
        input1 = section(runner, "## Input 1 — `COLLECTION TASK PLAN` (phase P of a collection)")
        input3 = section(
            runner,
            "## Input 3 — `execution_kind=campaign`: campaign state machine, inline (collection-lane)",
        )
        for name, body in (("Input 1", input1), ("Input 3", input3)):
            with self.subTest(section=name):
                self.assertIn("no unit-level `selected_variant`", body)
                self.assertIn("exact ID", body)
                self.assertIn("dispatch selection rule", body)
                self.assertIn("incremental", body.lower())
        self.assertIn("not an error", input1 + " " + input3)
        self.assertIn("baseline and runtime before the first step DO", input1)
        self.assertIn(
            "concrete step's own PLAN and variant after that step is selected", input1
        )
        self.assertNotIn(
            "they belong after the barrier and after the campaign's own per-step PLAN", input1
        )


class ApprovalResumeScenarios(unittest.TestCase):
    """Text guard: a gated DO resumes after approval; the saved plan is stale."""

    def test_runner_never_starts_gated_do_without_recorded_approval(self) -> None:
        runner = read(RUNNER)
        self.assertIn("never starts a gated DO without the matching recorded approval", runner)
        self.assertNotIn("never starts a gated DO:", runner)

    def test_approval_ref_and_resume_bind_task_cycle_and_applicability(self) -> None:
        protocol = section(read(RUNNER), "## Normal-mode approval protocol")
        self.assertIn("task/`cycle_id`", protocol)
        self.assertIn("applicability check", protocol)
        self.assertIn("fresh approval", protocol)
        self.assertIn("stale approval never authorizes it", protocol)
        self.assertIn("does not unconditionally replan", protocol)
        self.assertNotIn("Approval resume never triggers a replan", protocol)

    def test_runner_stale_resume_requires_fresh_approval(self) -> None:
        resume = section(
            read(RUNNER),
            "## Input 2 — `execution_kind=cycle`: one full cycle or a resumed cycle",
        )
        self.assertIn("normal-mode approval protocol", resume)
        self.assertIn("fresh approval", resume)
        self.assertNotIn("and only then DO starts", resume)

    def test_contracts_agree_on_fresh_approval_after_stale_plan(self) -> None:
        for path, fresh, applicability, no_unconditional in (
            (COLLECTION, "fresh", "applicability", "does not do an unconditional replan"),
            (INCREMENTAL, "fresh", "applicability", "does not do an unconditional replan"),
            (BASE, "fresh approval", "applicability", "neither unconditionally replans"),
            (CODER, "fresh approval", "applicability", "does not unconditionally replan"),
            (DOTNET, "fresh approval", "applicability", "does not unconditionally replan"),
        ):
            text = flat(path)
            with self.subTest(contract=path.parent.name):
                self.assertIn(fresh, text)
                self.assertIn(applicability, text.lower())
                self.assertIn(no_unconditional, text)
        assert_absent(self, flat(COLLECTION),
                      "without a replan and without a new step")


class CollectionUnitKindScenarios(unittest.TestCase):
    """Text guard: a campaign unit is dispatched before it has a step variant."""

    def test_typed_barrier_and_per_unit_disposition(self) -> None:
        col = read(COLLECTION)
        plan = section(col, "### P — per-task PLANs, the barrier, clustering")
        self.assertIn(
            "The initial `execution_kind` of every unit is decided by the collection PLAN",
            plan,
        )
        self.assertIn("the requirement of its kind", plan)
        self.assertIn("`preparation_state=ready`", plan)
        self.assertIn("`plan_state=ready`", plan)
        self.assertIn("The units' PLANs are independent and run in parallel", plan)
        self.assertNotIn(
            "until the own PLAN of **all** tasks without exception is ready", plan
        )

        status = section(col, "## Collection status")
        self.assertIn("per-unit `disposition`", status)
        self.assertIn("an explicit field of **both** forms, `cycle` and `campaign`", status)
        self.assertIn("`campaign_ref`", status)
        self.assertIn("optional before the baseline bootstrap", status)


class BootstrapMetScenarios(unittest.TestCase):
    """Text guard: the bootstrap baseline already satisfies the goal."""

    def test_red_verify_does_not_auto_become_unreachable(self) -> None:
        stop = section(read(INCREMENTAL), "### 5. Stop decision")
        self.assertIn("independent `pdca-check`", stop)
        self.assertIn("not self-accept", stop)
        self.assertIn("not automatically", stop)
        self.assertIn("`repair`/`blocked`", stop)
        self.assertNotIn("или `unreachable`, если обязательный `verify` не проходит", stop)

    def test_docs_do_not_derive_unreachable_from_a_red_verify(self) -> None:
        for path, obsolete in (
            (REPO / "docs/pdca-incremental.md",
             "(or `unreachable` if the mandatory `verify` fails)"),
            (REPO / "docs/ru/pdca-incremental.md",
             "(или `unreachable`, если обязательный `verify` не проходит)"),
        ):
            text = flat(path)
            with self.subTest(doc=path.name):
                assert_absent(self, text, obsolete)
                self.assertIn("pdca-check", text)


class PostBarrierTopologyScenarios(unittest.TestCase):
    """Text guard: a new campaign is accepted after the barrier and the lanes started."""

    def test_new_unit_after_barrier_requires_explicit_replan(self) -> None:
        section_text = section(
            read(COLLECTION), "## Stale PLAN and schedule revision"
        )
        self.assertIn("A new campaign or a new unit after the barrier", section_text)
        self.assertIn("explicit collection replan/reapprove", section_text)
        self.assertIn(
            "The old identities, statuses and evidence are preserved", section_text
        )
        self.assertIn("there is no automatic `recluster`", section_text)
        self.assertIn("stop/scope", section_text)


class RoutingTableScenarios(unittest.TestCase):
    """Text guard: independent goals share one footprint; a known plan is already whole."""

    def test_shared_footprint_alone_is_not_an_incremental_signal(self) -> None:
        row_two = next(
            line for line in read(ENTRY).splitlines() if line.startswith("| 2 |")
        )
        self.assertNotIn("footprint", row_two)
        self.assertIn("no whole-volume plan", row_two)
        assert_absent(self, flat(ENTRY),
                      "or all tasks serve one shared metric/footprint")
        self.assertIn("single shared goal whose whole plan is already known is one cycle",
                      flat(ENTRY))

    def test_no_contradictory_campaign_row_for_independent_goals(self) -> None:
        choosing = section(read(INCREMENTAL), "## When to choose")
        choose_collection = "one common stream without per-item acceptance"
        choose_collection_2 = "independent goals, but all items"
        self.assertNotIn(choose_collection, choosing)
        self.assertNotIn(choose_collection_2, choosing)
        self.assertIn("the plan for the whole volume is known and this is one task", choosing)


class EvidenceAttemptScenarios(unittest.TestCase):
    """Text guard: a same-contract implementation fix changes the product snapshot."""

    def test_attempt_child_recipe_is_operational_in_all_cycle_contracts(self) -> None:
        for path in (BASE, CODER, DOTNET):
            text = flat(path)
            with self.subTest(contract=path.parent.name):
                self.assertIn("attempts/c<N>-r<r>-n<n>/", text)
                self.assertIn("`c<N>` is the cycle", text)
                self.assertIn("fresh child", text)
                self.assertIn("authoritative", text)
                self.assertIn("DO→CHECK", text)
                self.assertIn("prior manifests are retained", text)
                self.assertIn("`rv` changes only with the criteria/contract", text)
                assert_absent(self, text,
                              "default `<evidence-dir>`: `.pdca/<task>/rv<k>/`")

    def test_dotnet_drift_keeps_rv_for_same_criteria(self) -> None:
        text = flat(DOTNET)
        assert_absent(self, text,
                      "gets a new `rv`/receipt/check",
                      "a drift invalidates the previous verdict and the current revision")
        self.assertIn("not automatically a new `rv`", text)
        self.assertIn("planned CHECK → DO", text)


class ResourceRuleScenarios(unittest.TestCase):
    """Text guard: a required role is unavailable in dotnet."""

    def test_dotnet_resource_rule_is_one_clear_sentence(self) -> None:
        text = flat(DOTNET)
        self.assertEqual(text.count("never execute silently without the role"), 1)
        self.assertNotIn("It is **not a silent run without the role**", text)


if __name__ == "__main__":
    unittest.main()
