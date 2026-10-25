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
            "the stop-loss budget",
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


if __name__ == "__main__":
    unittest.main()
