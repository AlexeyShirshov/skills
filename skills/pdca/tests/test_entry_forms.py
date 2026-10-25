"""Entry-and-forms guards: the base's one PLAN decides the form, and nothing else does.

The retired architecture had a separate `pdca-entry` umbrella skill with a routing table
that classified a task and handed it to a contract, plus an orchestrator agent that loaded
the contract named in `selected_variant`.  The family now has **one** entry — the base
`pdca` — and its **single PLAN** returns the form together with the plan:

* ordinary cycle — the method and the volume are known and bounded;
* incremental — the method or the volume is unknown, or the next action depends on
  knowledge not obtained yet;
* collection — a list of independent goals.

What this module protects:

* there is no second classifier, no routing table and no `pdca-entry`;
* the discriminators are the ones written in the base (§Forms), including the explicit
  rule that **data dependency is not uncertainty**;
* a confirmation of the same plan is not a second PLAN, and an explicitly named contract
  is a constraint the PLAN works inside.

Text only: no model and no cycle is executed.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

FAMILY = Path(__file__).resolve().parents[2]

BASE = FAMILY / "pdca/SKILL.md"
BASE_ASSETS = FAMILY / "pdca/assets/opencode-agents"
FAMILY_SKILLS = ("pdca", "pdca-coder", "pdca-collection", "pdca-dotnet", "pdca-incremental")
NON_ENTRY = FAMILY_SKILLS[1:]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.replace("`", "").replace("*", "").split())


def between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i:j] if j >= 0 else text[i:]


class NoUmbrellaTest(unittest.TestCase):
    """`pdca-entry` is deleted, and nothing in the family still points at it."""

    def test_pdca_entry_does_not_exist(self):
        self.assertFalse((FAMILY / "pdca-entry").exists(), "pdca-entry must stay deleted")
        shipped = sorted(p.parent.name for p in FAMILY.glob("pdca*/SKILL.md"))
        self.assertEqual(sorted(FAMILY_SKILLS), shipped)

    def test_no_surface_points_at_pdca_entry(self):
        offenders = []
        for name in FAMILY_SKILLS:
            root = FAMILY / name
            for path in [root / "SKILL.md"]:
                if "pdca-entry" in read(path):
                    offenders.append(str(path.relative_to(FAMILY)))
            for sub in ("references", "assets"):
                directory = root / sub
                if not directory.is_dir():
                    continue
                for path in sorted(directory.rglob("*.md")):
                    if "pdca-entry" in read(path):
                        offenders.append(str(path.relative_to(FAMILY)))
        self.assertEqual([], offenders, "retired umbrella still referenced: %r" % offenders)

    def test_no_routing_table_in_the_family(self):
        for name in FAMILY_SKILLS:
            text = read(FAMILY / name / "SKILL.md")
            with self.subTest(skill=name):
                self.assertNotIn("Routing decision", text)
                self.assertNotIn("selected_variant", text)
                self.assertNotIn("execution_kind", text)


class OnePlanTest(unittest.TestCase):
    """The driver gathers facts and dispatches one planner call — it does not classify."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(BASE)
        cls.base = norm(cls.raw)
        cls.entry = norm(between(cls.raw, "## Entry: one PLAN decides the form",
                                 "## Roles and host requirements"))
        cls.planner = norm(read(BASE_ASSETS / "pdca-planner.md"))

    def test_driver_does_not_classify_and_does_not_plan(self):
        self.assertIn("The driver does not classify and does not plan", self.entry)
        self.assertIn("It gathers the minimum facts needed to plan", self.entry)
        self.assertIn("hands the task to the configured pdca-planner once", self.entry)

    def test_no_cheap_semantic_classifier(self):
        self.assertIn("There is no cheap semantic classifier", self.entry)
        self.assertIn("no second PLAN on the same content", self.entry)

    def test_a_confirmation_is_not_a_new_plan(self):
        self.assertIn("A confirmation or restatement of the same plan is not a new PLAN", self.entry)

    def test_the_single_plan_returns_form_overlay_step_and_claims(self):
        for token in (
            "the form of execution",
            "the overlay",
            "the nearest useful step",
            "the carrying claims",
            "the effort estimate/accounting",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.entry)

    def test_the_planner_asset_owns_the_form_decision(self):
        self.assertIn("Form and first step (cycle start)", self.planner)
        self.assertIn("At cycle start you make the family's single strategic decision", self.planner)
        self.assertIn("Form.", self.planner)
        self.assertIn("Overlay.", self.planner)
        self.assertIn("Nearest useful step.", self.planner)

    def test_a_blocker_is_a_whole_goal_decision_not_a_second_classification(self):
        self.assertIn("A step that turns out to be an ordinary bounded task", norm(read(
            FAMILY / "pdca-incremental/SKILL.md")))
        self.assertIn("A genuine strategy change follows the base", norm(read(
            FAMILY / "pdca-incremental/SKILL.md")))


class FormsDiscriminatorsTest(unittest.TestCase):
    """The three forms and their boundary cases, exactly as the base states them."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(BASE)
        cls.forms_raw = between(cls.raw, "### Forms", "## Roles and host requirements")
        cls.forms = norm(cls.forms_raw).lower()

    def test_ordinary_cycle_is_known_and_bounded(self):
        self.assertIn("ordinary cycle — the method and the volume are sufficiently known and bounded",
                      self.forms)

    def test_data_dependency_is_not_uncertainty(self):
        self.assertIn("passing one operation's result into another", self.forms)
        self.assertIn("known branchings with a fixed bounded volume, are data dependency, not uncertainty",
                      self.forms)
        self.assertIn("mere output→input chaining and a known algorithm with a fixed volume are not incremental",
                      self.forms)

    def test_incremental_is_unknown_method_or_volume_or_next_action_choice(self):
        self.assertIn("the method is unknown or the volume is unknown", self.forms)
        self.assertIn("the composition/choice of the next actions genuinely depends on knowledge not yet obtained",
                      self.forms)

    def test_collection_is_a_list_of_independent_goals(self):
        self.assertIn("a list of independent goals (not an internal split of one goal)", self.forms)
        self.assertIn("each item gets its own form by these same rules", self.forms)
        self.assertIn("a batch may be heterogeneous", self.forms)
        self.assertIn("a single-lane collection is the normal case, not a degradation", self.forms)

    def test_a_probe_is_allowed_before_the_form_is_settled(self):
        self.assertIn("a bounded probe is allowed and the form is refined from what it returns", self.forms)
        self.assertIn("a probe is not a separate cycle", self.forms)
        self.assertIn("uncertainty is no reason to imagine", self.forms)

    def test_explicit_user_preference_is_a_constraint(self):
        self.assertIn("an explicit user preference of form is respected as a constraint", self.forms)
        self.assertIn("the PLAN works inside it and does not silently re-route",
                      norm(between(self.raw, "## Entry: one PLAN decides the form",
                                   "## Roles and host requirements")))
        for name in FAMILY_SKILLS:
            with self.subTest(contract=name):
                self.assertIn(name, self.raw)

    def test_auxiliary_code_does_not_reclassify_the_goal(self):
        self.assertIn("Auxiliary code does not reclassify the goal", norm(self.raw))
        self.assertIn("does not apply the coder/.NET overlay to the whole campaign", norm(self.raw))

    def test_no_form_is_decided_by_an_overlay_or_a_form_contract(self):
        # Each non-entry contract states its own refusal in its own words; all four must
        # deny classification, because the single PLAN already decided.
        denial = re.compile(r"(never classifies|does not classify)")
        for name in NON_ENTRY:
            text = norm(read(FAMILY / name / "SKILL.md")).lower()
            with self.subTest(skill=name):
                self.assertRegex(text, denial)
        self.assertIn("does not classify the task", norm(read(FAMILY / "pdca-incremental/SKILL.md")))
        self.assertIn("does not classify the batch", norm(read(FAMILY / "pdca-collection/SKILL.md")))
        self.assertIn("never classifies, never re-plans",
                      norm(read(FAMILY / "pdca-coder/SKILL.md")).lower())
        self.assertIn("never classifies, never re-plans",
                      norm(read(FAMILY / "pdca-dotnet/SKILL.md")).lower())


class DecisionTableTest(unittest.TestCase):
    """The base names exactly one execution contract per decided form."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(BASE)
        start = cls.raw.index("| Decided form | Execution contract | Owner |")
        cls.table = cls.raw[start:cls.raw.index("### Forms")]
        cls.rows = [
            [norm(cell) for cell in line.strip().strip("|").split("|")]
            for line in cls.table.splitlines()
            if line.strip().startswith("|") and "---" not in line
        ]

    def test_table_has_one_row_per_form(self):
        self.assertEqual(4, len(self.rows) - 1, "expected one row per decided form")
        self.assertEqual(["Decided form", "Execution contract", "Owner"], self.rows[0])

    def test_ordinary_cycle_is_the_base_itself(self):
        forms = {row[0]: row for row in self.rows[1:]}
        self.assertIn("ordinary cycle", forms)
        self.assertIn("this skill", forms["ordinary cycle"][1])

    def test_forms_and_overlays_map_to_their_contracts(self):
        forms = {row[0]: row for row in self.rows[1:]}
        self.assertIn("pdca-incremental", forms["incremental campaign"][1])
        self.assertIn("pdca-collection", forms["collection"][1])
        overlay_row = forms["coder / .NET overlay"][1]
        self.assertIn("pdca-coder", overlay_row)
        self.assertIn("pdca-dotnet", overlay_row)
        self.assertIn("applied to the chosen form", overlay_row)

    def test_the_owner_is_named_for_every_row(self):
        for row in self.rows[1:]:
            with self.subTest(form=row[0]):
                self.assertTrue(row[2], "no owner named for %r" % row[0])

    def test_campaign_control_and_cycle_control_are_contexts(self):
        base = norm(self.raw)
        self.assertIn("campaign-control is a context of that role, not a new role", base)
        self.assertIn("cycle-control", base)
        self.assertIn("Two contexts, never mixed", base)


ENTRY_RULES = (
    "form: UNDECIDED",
    "not a fourth context/role",
    "cycle/campaign stay with the same controller",
    "handed by reference",
    "references/plan.md",
)


def entry_gaps(text: str) -> list:
    """Scoped phrase check used only to prove the guard reacts to a mutation."""
    flat = norm(text)
    return [rule for rule in ENTRY_RULES if rule not in flat]


class FreshEntryTest(unittest.TestCase):
    """A fresh request starts unclassified; only the one PLAN decides the form."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(BASE)
        cls.entry = norm(between(cls.raw, "## Entry: one PLAN decides the form",
                                 "## Roles and host requirements"))
        cls.forms = norm(between(cls.raw, "### Forms", "## Roles and host requirements"))
        cls.plan = norm(read(FAMILY / "pdca/references/plan.md"))

    def test_fresh_entry_is_contract_pdca_and_form_undecided(self):
        self.assertIn("contract: pdca", self.entry)
        self.assertIn("form: UNDECIDED", self.entry)

    def test_one_deliverable_does_not_preselect_the_cycle_or_a_context(self):
        self.assertIn("one deliverable is not form=cycle", self.entry)
        self.assertIn("no cycle-control/campaign-control is named before PLAN", self.entry)

    def test_entry_is_the_existing_dispatcher_not_a_fourth_context(self):
        self.assertIn("existing-dispatcher stage", self.entry)
        self.assertIn("not a fourth context/role", self.entry)

    def test_read_denied_planner_receives_discriminator_rules_not_names(self):
        self.assertIn("references/plan.md", self.entry)
        self.assertIn("Entry routing and bounded continuations", self.entry)
        self.assertIn("form discriminators themselves", self.plan)
        self.assertIn("names alone are not enough for a read-denied planner", self.plan)

    def test_cycle_and_campaign_controller_adopt_their_context_without_a_second_plan(self):
        self.assertIn("cycle/campaign stay with the same controller", self.entry)
        self.assertIn("same controller (cycle-control / campaign-control)", self.plan)

    def test_collection_is_handed_to_the_existing_cheap_primary_owner(self):
        self.assertIn("A chosen collection is handed by reference to the cheap primary/collection "
                      "owner", self.entry)
        for token in (
            "does not become the batch owner",
            "does not self-delegate",
            "collection-lane stays an existing caller-dispatched lane",
            "per-item/lane",
            "single-lane batch is normal",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.plan)

    def test_missing_method_and_volume_rationale_is_an_incomplete_plan(self):
        self.assertIn("A missing method/volume rationale is an incomplete PLAN", self.entry)
        self.assertIn("clarified with the same planner", self.entry)
        self.assertIn("no r/n bump", self.entry)
        self.assertIn("routing follows it, not a driver choice", self.entry)
        self.assertIn("never bumps r/n", self.plan)
        self.assertIn("not automatically incremental or a STOP", self.plan)

    def test_form_known_no_plan_and_resume_rules_live_in_the_reference(self):
        self.assertIn("form-known dispatch that genuinely has no plan of its own", self.plan)
        self.assertIn("persisted plan_handoff/resume is never re-planned", self.plan)
        self.assertIn("no new state file, schema or counter", self.plan)

    def test_entry_guard_reacts_to_a_preselected_form(self):
        sample = self.raw.replace("`form: UNDECIDED`", "`form=cycle`")
        self.assertEqual([], entry_gaps(self.raw))
        self.assertIn("form: UNDECIDED", entry_gaps(sample))

    def test_one_deliverable_is_not_a_known_method(self):
        self.assertIn("One deliverable is not a known method", self.forms)
        self.assertIn("does not establish the method; name the justified method and bound",
                      self.forms)

    def test_assumptions_bound_calculation_but_do_not_prove_a_mechanism(self):
        self.assertIn("Permissible assumptions may bound a calculation-only result", self.forms)
        self.assertIn("do not evidence a decision-critical mechanism", self.forms)
        self.assertIn("Do not make every design task incremental", self.plan)

    def test_choice_probe_precedes_dependent_work_and_validation_is_not_exploration(self):
        self.assertIn("A choice probe opens its decision with an observable outcome", self.plan)
        self.assertIn("before dependent work is fixed", self.plan)
        self.assertIn("validating a known method is legitimate", self.plan)
        self.assertIn("bounded probe is allowed and the form is refined", self.forms)


class PlannerFormRationaleTest(unittest.TestCase):
    """The planner asset binds the form decision to method/volume or missing knowledge."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = norm(read(BASE_ASSETS / "pdca-planner.md"))

    def test_form_reason_names_method_and_volume_or_missing_knowledge(self):
        self.assertIn("which method is already justified and how the volume is bounded", self.planner)
        self.assertIn("which missing knowledge decides the next action", self.planner)

    def test_one_deliverable_and_assumptions_do_not_make_the_method_known(self):
        self.assertIn("one finished result, one file or a known desired format is not by itself a "
                      "known method", self.planner)
        self.assertIn("do not make every design task incremental", self.planner)
        self.assertIn("validating an already-known method is legitimate", self.planner)

    def test_probe_authorization_names_decision_outcomes_and_evidence(self):
        for token in (
            "authorize one bounded probe",
            "name the open decision, the observable outcomes and the evidence that closes it",
            "leave the form undecided until its facts refine this same pending PLAN",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.planner)

    def test_plan_selects_the_approach_and_do_develops_the_deliverable(self):
        for token in (
            "PLAN chooses the approach; DO develops the deliverable",
            "does not pre-write the final artefact",
            "solve every unresolved downstream choice",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.planner)

    def test_incremental_first_step_resolves_the_leading_unknown(self):
        self.assertIn("first step resolves the leading unknown", self.planner)
        self.assertIn("later work stays conditional, not a full speculative backlog", self.planner)
        self.assertIn("Do not change to incremental merely to excuse a larger plan", self.planner)

    def test_verification_choice_replaces_mandatory_bespoke_checking(self):
        self.assertIn("Verification choice", self.planner)
        self.assertIn("Independent manual observation or a focused recomputation can be enough",
                      self.planner)
        self.assertIn('"verifiable evidence" does not mandate a new executable checker', self.planner)
        self.assertIn("concrete reason why existing or manual means are insufficient", self.planner)

    def test_command_contract_is_conditional_on_an_actual_command(self):
        self.assertIn("Command contract (only for commands the plan freezes)", self.planner)
        self.assertIn("do not invent a command line", self.planner)

    def test_bounded_continuations_do_not_expand_the_planner_call_cap(self):
        for token in (
            "successful path 1 + number of steps",
            "bounded same-pending-PLAN continuations",
            "The count is recorded state, not a task limit",
            "no hidden exempt calls",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.planner)


if __name__ == "__main__":
    unittest.main()
