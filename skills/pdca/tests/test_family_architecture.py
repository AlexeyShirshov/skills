"""Family architecture guards: one entry, two overlays, two forms — no copies.

The family used to ship `pdca-coder` and `pdca-dotnet` as *complete* contracts (full
copies of the state machine, gates, counters and approval rules), and a separate
`pdca-entry` umbrella owned the routing table.  That is gone:

* `pdca` is the **single public entry** and the **base cycle** — its one PLAN decides the
  form (ordinary cycle / incremental / collection) and the overlay;
* `pdca-coder` is the programming **overlay** and `pdca-dotnet` **inherits** coder — an
  overlay carries only its differences and never a second cycle;
* `pdca-incremental` and `pdca-collection` are **forms**, not overlays and not second
  cycles.

This module replaces the old full-copy parity guard (`test_variant_parity.py`): the real
hazard is no longer "a rule fixed in one copy and forgotten in the other" — it is a block
of the base being **re-declared** in an overlay, which silently forks the contract again.

Rule-presence/absence only: it reads the contract files as text, never executes a model.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

FAMILY = Path(__file__).resolve().parents[2]  # the `skills/` directory

BASE_SKILL = "pdca"
OVERLAYS = ("pdca-coder", "pdca-dotnet")
FORMS = ("pdca-incremental", "pdca-collection")
FAMILY_SKILLS = (BASE_SKILL,) + OVERLAYS + FORMS

BASE = FAMILY / "pdca/SKILL.md"
CODER = FAMILY / "pdca-coder/SKILL.md"
DOTNET = FAMILY / "pdca-dotnet/SKILL.md"

# The blocks that belong to the base and may not be re-declared by an overlay or a form.
# A paragraph-level copy is the measurable form of "re-declared": one-line reminders
# ("the base list still governs") are shorter than this threshold and stay legal.
PARAGRAPH_MIN = 40

# Coder blocks the .NET overlay inherits instead of repeating. The three shared titles are
# legitimate deltas (the .NET file has its own "when it applies", composition table and
# references).
INHERITED_CODER_BLOCKS = frozenset(
    (
        "## When it applies",
        "## Composition",
        "## References",
    )
)

# Routing enums of the retired architecture: the form is decided by the planner's single
# PLAN, so no contract names a variant or an execution kind any more.
RETIRED_ROUTING_TOKENS = ("selected_variant", "execution_kind")

CONTRACT_SURFACE = tuple(
    ["SKILL.md", "references", "assets", "scripts"]
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.replace("`", "").replace("*", "").split())


def frontmatter_block(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end >= 0 else ""


def frontmatter_flat(text: str) -> dict:
    """Flat view of the frontmatter: both ``key: value`` and nested ``key.sub``."""
    block = frontmatter_block(text)
    flat: dict = {}
    stack: list = [("", -1)]
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, value = raw.strip().partition(":")
        key = key.strip().strip('"').strip("'")
        while stack and indent <= stack[-1][1]:
            stack.pop()
        prefix = stack[-1][0]
        full = ("%s.%s" % (prefix, key)) if prefix else key
        value = value.strip().strip('"').strip("'")
        if value == "":
            stack.append((full, indent))
        else:
            flat[full] = value
    return flat


def headings(text: str) -> set:
    return {
        line.rstrip()
        for line in text.splitlines()
        if re.match(r"^#{2,3} ", line)
    }


def paragraphs(text: str, minimum: int = PARAGRAPH_MIN) -> set:
    out = set()
    for chunk in re.split(r"\n\s*\n", text):
        flat = " ".join(chunk.split())
        if len(flat) >= minimum:
            out.add(flat)
    return out


def contract_files(skill: str) -> list:
    """Every shipped contract artefact of one skill (tests are other streams' surface)."""
    root = FAMILY / skill
    files = [root / "SKILL.md"]
    for sub in CONTRACT_SURFACE[1:]:
        directory = root / sub
        if directory.is_dir():
            files += sorted(p for p in directory.rglob("*") if p.is_file())
    return [p for p in files if "__pycache__" not in p.parts]


class FamilyShapeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = read(BASE)
        cls.skills = {
            name: read(FAMILY / name / "SKILL.md") for name in FAMILY_SKILLS
        }

    def test_exactly_five_skills(self):
        shipped = sorted(p.parent.name for p in FAMILY.glob("pdca*/SKILL.md"))
        self.assertEqual(sorted(FAMILY_SKILLS), shipped)
        self.assertFalse((FAMILY / "pdca-entry").exists(), "pdca-entry must stay deleted")

    def test_every_skill_declares_name_and_description(self):
        for name, text in self.skills.items():
            data = frontmatter_flat(text)
            with self.subTest(skill=name):
                self.assertEqual(name, data.get("name"), "name must match the directory")
                self.assertTrue(data.get("description", "").strip(), "description missing")

    def test_only_the_base_is_model_invocable(self):
        base = frontmatter_flat(self.base)
        self.assertNotIn("disable-model-invocation", base)
        self.assertNotIn("metadata.opencode/autoinvoke", base)
        for name in OVERLAYS + FORMS:
            data = frontmatter_flat(self.skills[name])
            with self.subTest(skill=name):
                self.assertEqual("true", data.get("disable-model-invocation"))
                self.assertEqual("false", data.get("metadata.opencode/autoinvoke"))

    def test_base_is_the_single_public_entry(self):
        self.assertIn("single entry", norm(self.base).lower())
        for name in OVERLAYS + FORMS:
            desc = norm(frontmatter_flat(self.skills[name]).get("description", "")).lower()
            with self.subTest(skill=name):
                self.assertNotIn("single entry", desc)
                self.assertTrue(
                    "user-invoked" in desc or "loaded by the base" in desc,
                    "a non-entry contract must declare how it is reached",
                )

    def test_base_names_the_forms_and_the_overlays(self):
        for name in OVERLAYS + FORMS:
            with self.subTest(name=name):
                self.assertIn(name, self.base)
        self.assertIn("ordinary cycle", norm(self.base))
        self.assertIn("incremental", self.base)
        self.assertIn("collection", self.base)

    def test_family_load_order_points_back_to_the_base(self):
        for name in OVERLAYS + FORMS:
            with self.subTest(skill=name):
                self.assertIn("../pdca/SKILL.md", self.skills[name])

    def test_overlay_inheritance_chain(self):
        coder = norm(self.skills["pdca-coder"])
        dotnet = norm(self.skills["pdca-dotnet"])
        self.assertIn("This is an overlay, not a cycle", coder)
        self.assertIn("The base ../pdca/SKILL.md first, then this file", coder)
        self.assertIn("This is an overlay, not a cycle", dotnet)
        self.assertIn("Inheritance chain", dotnet)
        self.assertIn("The base ../pdca/SKILL.md first", dotnet)
        self.assertIn("then ../pdca-coder/SKILL.md (the programming overlay), then this file", dotnet)

    def test_forms_are_forms_not_overlays(self):
        incremental = norm(self.skills["pdca-incremental"]).lower()
        collection = norm(self.skills["pdca-collection"]).lower()
        self.assertIn("this is a form contract, not an overlay and not a second cycle", incremental)
        self.assertIn("the state machine, gates, roles, counters", incremental)
        self.assertIn("are the base's and are not restated here", incremental)
        self.assertIn("the base is not duplicated or overridden here", collection)
        self.assertIn("does not classify the batch", collection)
        self.assertIn("has no routing table of its own", collection)
        for name in FORMS:
            with self.subTest(skill=name):
                self.assertNotIn("this is an overlay", norm(self.skills[name]).lower())

    def test_the_inherited_contract_wins_on_a_conflict(self):
        coder = norm(self.skills["pdca-coder"]).lower()
        dotnet = norm(self.skills["pdca-dotnet"]).lower()
        self.assertIn("if this file and the base disagree on a base rule, the base wins", coder)
        self.assertIn("if this file and the base or the coder overlay disagree on their rules, they win", dotnet)


class NoRedeclarationTest(unittest.TestCase):
    """An overlay/form carries differences only; the base blocks stay in one place."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_raw = read(BASE)
        cls.base_paragraphs = paragraphs(cls.base_raw)
        cls.base_headings = headings(cls.base_raw)

    def test_no_contract_restates_a_base_paragraph(self):
        offenders = {}
        for name in OVERLAYS + FORMS:
            duplicated = self.base_paragraphs & paragraphs(read(FAMILY / name / "SKILL.md"))
            if duplicated:
                offenders[name] = sorted(duplicated)[:3]
        self.assertEqual({}, offenders, "a non-base contract re-declares a base block")

    def test_no_contract_redeclares_the_base_state_machine_counters_or_gates(self):
        # The base headings that own the shared machinery. A form may have its own
        # "Red flags"/"Recovery"/"Budgets" *delta* section, so this asserts on the blocks
        # the base owns by name and on the rule bodies below.
        owned = {
            "## State machine and counters",
            "### Phase progress mirror",
            "### DO → PLAN candidate",
            "## Transition gates",
            "## Phase contracts (generic)",
            "### Claims and veto",
            "## Roles and host requirements",
            "## Normal-mode approval",
            "## Generic operating constraints",
            "## Strategic revision",
            "## Overlays",
            "## Entry: one PLAN decides the form",
        }
        problems = {}
        for name in OVERLAYS + FORMS:
            text = read(FAMILY / name / "SKILL.md")
            hits = sorted(owned & headings(text))
            if hits:
                problems[name] = hits
        self.assertEqual({}, problems, "a non-base contract re-declares a base block")

    def test_no_contract_restates_the_counters_or_the_gate_list(self):
        rule_bodies = (
            "Three counters, do not mix them",
            "You cannot skip CHECK. You cannot close the cycle without ACT.",
            "1. PLAN → DO",
            "2. DO → CHECK",
        )
        for name in OVERLAYS + FORMS:
            text = norm(read(FAMILY / name / "SKILL.md"))
            for body in rule_bodies:
                with self.subTest(skill=name, body=body):
                    self.assertNotIn(norm(body), text)

    def test_dotnet_does_not_redeclare_the_coder_overlay(self):
        coder_headings = headings(read(CODER)) - INHERITED_CODER_BLOCKS
        dotnet_headings = headings(read(DOTNET))
        leaked = sorted(coder_headings & dotnet_headings)
        self.assertEqual([], leaked, "pdca-dotnet repeats coder sections instead of inheriting")

    def test_dotnet_declares_only_its_own_blocks(self):
        dotnet_headings = headings(read(DOTNET))
        for section in (
            "### Canonical command forms (frozen; do not reinvent per plan)",
            "### Roslyn-first for C# symbols",
            "### .NET specialists (gather-only)",
            "### Completeness gate at PLAN",
        ):
            with self.subTest(section=section):
                self.assertIn(section, dotnet_headings)


class NoVariantRoutingTest(unittest.TestCase):
    """The retired routing enums (`selected_variant`, `execution_kind`) are gone."""

    def test_no_routing_enum_in_the_contract_surface(self):
        hits = []
        for name in FAMILY_SKILLS:
            for path in contract_files(name):
                text = read(path)
                for token in RETIRED_ROUTING_TOKENS:
                    if token in text:
                        hits.append((str(path.relative_to(FAMILY)), token))
        self.assertEqual([], hits, "retired routing enums came back: %r" % (hits,))

    def test_no_umbrella_routing_table(self):
        base = read(BASE)
        for phrase in ("Routing decision", "routing table of the family", "precedence table"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, base)
        self.assertNotIn("pdca-entry", base)

    def test_only_the_planner_decides_the_form(self):
        base = norm(read(BASE)).lower()
        self.assertIn("the driver does not classify and does not plan", base)
        self.assertIn("there is no cheap semantic classifier", base)


class ReachabilityTest(unittest.TestCase):
    """Every form and overlay is reachable *from the base* — one entry, no orphans."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_raw = read(BASE)
        cls.base = norm(cls.base_raw)

    def test_decision_table_names_every_contract(self):
        table = self.base_raw[
            self.base_raw.index("| Decided form | Execution contract | Owner |"):
            self.base_raw.index("### Forms")
        ]
        rows = [line for line in table.splitlines() if line.startswith("|") and "---" not in line]
        self.assertEqual(5, len(rows), "expected header + one row per decided form")
        for name in FORMS + OVERLAYS:
            with self.subTest(contract=name):
                self.assertIn(name, table)
        self.assertIn("this skill", table)

    def test_each_contract_is_selected_by_the_plan_not_by_a_driver_table(self):
        self.assertIn("After that PLAN the driver loads exactly one execution contract", self.base)
        self.assertIn("and passes the plan to it by reference", self.base)

    def test_overlays_are_applied_to_a_form(self):
        self.assertIn("applied to the chosen form", self.base)
        self.assertIn("an overlay adds facts, never a second cycle", self.base)

    def test_forms_are_reachable_without_an_overlay(self):
        forms = norm(self.base_raw[
            self.base_raw.index("### Forms"):self.base_raw.index("## Roles and host requirements")
        ]).lower()
        self.assertIn("ordinary cycle", forms)
        self.assertIn("incremental", forms)
        self.assertIn("collection", forms)


if __name__ == "__main__":
    unittest.main()
