"""Static regression guards for the pdca-coder overlay contract.

The PDCA family was restructured: `skills/pdca/SKILL.md` is the single public entry
and the **base cycle** (entry/form, roles, control modes, state machine, counters,
gates, phase contracts, claims/veto, evidence, status file, budgets, recovery,
escalation, constraints, red flags, approval); `skills/pdca-coder/` is the
**programming overlay** that adds code-specific deltas only and inherits the rest.

The guards below therefore read every rule where it canonically lives:

* a retained base rule -> `../pdca/SKILL.md` / `../pdca/references/*.md` (the same
  assertions as before the split; only the anchor/literal was adapted where the
  wording moved);
* overlay-only content -> this skill's `SKILL.md` / `references/*.md`;
* architecture -> the declared inheritance chain, the absence of duplicated base
  blocks, the host size limits, `# tier:` labels only (never `model:`), and no
  routing-enum tokens anywhere in the family.

They are rule-presence guards, **not** behavioral proof: no model and no live
cycle is executed. The last class is a **forbidden-token** guard: it scans every
file under `skills/pdca-coder/` for the nine stack tokens (built from concatenated
fragments so this file itself stays clean) and asserts each has zero matches.

Run:
    python3 -m unittest discover -s skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

# This repo IS the published-skills repo: the skill lives at
# `skills/pdca-coder/`, i.e. one level above this `tests/` directory.
SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_PATH = SKILL_DIR / "SKILL.md"
# The base cycle the overlay inherits (`skills/pdca/`).
BASE_DIR = SKILL_DIR.parent / "pdca"
BASE_SKILL = BASE_DIR / "SKILL.md"
BASE_PLAN = BASE_DIR / "references/plan.md"
BASE_ACT = BASE_DIR / "references/act.md"
# The .NET overlay that inherits this one.
DOTNET_DIR = SKILL_DIR.parent / "pdca-dotnet"
FAMILY_DIRS = (BASE_DIR, SKILL_DIR, DOTNET_DIR)
# Overlay-local phase reference (its plan/check references are only named).
CODER_ACT = SKILL_DIR / "references/act.md"

# The host truncates a loaded file at 50 KiB / 2000 lines; the main contract is
# additionally targeted at <= 35 KiB so the phase references stay loadable.
HOST_LIMIT_BYTES = 50 * 1024
HOST_LIMIT_LINES = 2000
MAIN_TARGET_BYTES = 35 * 1024


def _cat(*fragments):
    """Join fragments at runtime so the compiler cannot fold them into one
    literal constant (a folded literal would leak into the ``.pyc`` bytecode
    and make the real recursive scan match a compiled artifact)."""
    return "".join(fragments)


def forbidden_tokens():
    """The nine stack tokens, assembled from fragments (never literal here)."""
    return [
        _cat("dot", "net-"),
        _cat("doc", "fx"),
        _cat("x", "unit"),
        _cat("t", "unit"),
        _cat("CS", "1591"),
        _cat("Treat", "Warnings", "AsErrors"),
        _cat("Test", "containers"),
        _cat("EF", " ", "Core"),
        _cat("c", "sharp"),
    ]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    """Collapse whitespace (incl. line wraps) and drop backticks/format noise."""
    text = text.replace("`", "").replace("*", "")
    return re.sub(r"\s+", " ", text)


def between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i:j] if j >= 0 else text[i:]


def frontmatter_block(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end >= 0 else ""


def parse_frontmatter(block: str) -> dict:
    keys: dict = {}
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
        if m:
            keys[m.group(1)] = m.group(2).strip()
    return keys


def headings(path: Path) -> list:
    """All level-2 Markdown headings of a file, in order."""
    return re.findall(r"(?m)^##\s+(.+?)\s*$", read(path))


def all_headings(path: Path) -> str:
    """Every level-2/3 heading of a file, newline-joined (substring match)."""
    return "\n".join(re.findall(r"(?m)^#{2,3}\s+(.+?)\s*$", read(path)))


# The runner is a dispatcher: its permission block allowlists the .NET lens
# agents it may dispatch. Exempt it from the stack-token guard; the exemption is
# pinned to exactly this file in the test below.
RUNNER_ASSET = SKILL_DIR / "assets/opencode-agents/pdca-orchestrator.md"
SCAN_EXEMPT = frozenset((RUNNER_ASSET,))


def scan_tree(root: Path, patterns) -> list:
    hits = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.resolve() in {p.resolve() for p in SCAN_EXEMPT}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        low = text.lower()
        hits.extend((str(path), p) for p in patterns if p.lower() in low)
    return hits


class OverlayArchitectureTest(unittest.TestCase):
    """The overlay inherits the base instead of copying it.

    Rule-presence only: these guards read Markdown text and file sizes, so they
    prove the structure of the contract, not the behavior of a model.
    """

    # Sections the base owns; an overlay must not re-declare them.
    BASE_OWNED = (
        "State machine",
        "Transition gates",
        "Phase progress mirror",
        "Control modes and the campaign owner",
        "Roles and host requirements",
        "Claims and veto",
        "Evidence over assertion",
        "Effort and time policy",
        "Recovery",
        "Escalation",
        "Normal-mode approval",
    )
    # The overlay's own section skeleton: deltas only.
    ALLOWED_HEADINGS = {
        "When it applies",
        "Toolchain and lenses",
        "Code-specific plan deltas",
        "Code-specific check deltas",
        "Code-specific do/act deltas",
        "Composition",
        "References",
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)
        cls.base = norm(read(BASE_SKILL))

    # --- inheritance chain -------------------------------------------------

    def test_overlay_declares_the_base_as_its_parent(self):
        self.assertIn("This is an overlay, not a cycle", self.skill)
        self.assertIn("The base ../pdca/SKILL.md first, then this file", self.skill)
        self.assertIn("base wins", self.skill)
        self.assertIn("This file only adds", self.skill)

    def test_overlay_declares_one_plan_state_machine_and_status_file(self):
        self.assertIn("One PLAN, one state machine, one status file", self.skill)
        self.assertIn("never opens a second cycle, a second gate set", self.skill)
        self.assertIn("no PLAN of its own, no state machine, no second status file", self.skill)

    def test_base_names_both_overlays_and_the_inheritance(self):
        # The base contract is the place that declares the overlay chain.
        self.assertIn("pdca-coder is the generic programming overlay", self.base)
        self.assertIn("pdca-dotnet inherits coder", self.base)
        self.assertIn("overlay contains only the differences from the base", self.base)
        self.assertIn("without a duplicate PLAN or a second state machine", self.base)

    # --- no duplicate base blocks -----------------------------------------

    def test_overlay_does_not_redeclare_base_sections(self):
        ours = all_headings(SKILL_PATH)
        base_owned = all_headings(BASE_SKILL)
        for name in self.BASE_OWNED:
            with self.subTest(section=name):
                self.assertNotIn(
                    name,
                    ours,
                    "overlay re-declares the base section %r instead of inheriting it" % name,
                )
                self.assertIn(
                    name,
                    base_owned,
                    "the base no longer owns %r — the overlay contract changed" % name,
                )

    def test_overlay_section_skeleton_is_deltas_only(self):
        self.assertEqual(self.ALLOWED_HEADINGS, set(headings(SKILL_PATH)))

    def test_inherited_counters_are_not_redefined_locally(self):
        self.assertIn("inherits unchanged — no local counters", self.skill)
        self.assertIn("no execution-variant enum of its own", self.skill)
        # The counter *definitions* stay in the base; only the inheritance row may
        # mention the counter names here.
        self.assertNotIn("starts at 1", self.skill)
        self.assertNotIn("new revision resets n to 1", self.skill)

    def test_composition_table_maps_every_inherited_area_to_the_base(self):
        raw = between(self.skill_raw, "## Composition", "**Code-specific red flags**")
        rows = [
            line for line in raw.splitlines()
            if line.startswith("|") and "---" not in line
        ]
        self.assertTrue(rows, "composition table not found")
        rows = rows[1:]  # drop the header row
        self.assertEqual(15, len(rows), "every base area needs a composition row")
        for row in rows:
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            with self.subTest(row=cells[0]):
                self.assertEqual(2, len(cells))
                self.assertTrue(
                    cells[1].startswith("inherits"),
                    "%r is not declared as inheritance: %r" % (cells[0], cells[1]),
                )
        composition = norm(raw)
        for area in (
            "Entry, one PLAN, forms",
            "Roles and host requirements",
            "Gate 1",
            "Gate 3",
            "Claims and veto",
            "Effort accounting",
            "Recovery",
            "Escalation",
        ):
            with self.subTest(area=area):
                self.assertIn(area, composition)

    # --- host limits -------------------------------------------------------

    def test_every_skill_and_reference_is_under_the_host_limit(self):
        docs = sorted(SKILL_DIR.rglob("*.md"))
        self.assertTrue(docs, "no Markdown contract found")
        for path in docs:
            with self.subTest(path=str(path.relative_to(SKILL_DIR))):
                size = path.stat().st_size
                lines = len(read(path).splitlines())
                self.assertLessEqual(size, HOST_LIMIT_BYTES, "%s exceeds the 50 KiB host limit" % path)
                self.assertLessEqual(lines, HOST_LIMIT_LINES, "%s exceeds 2000 lines" % path)

    def test_main_file_stays_within_the_35_kib_target(self):
        size = SKILL_PATH.stat().st_size
        self.assertLessEqual(size, MAIN_TARGET_BYTES, "SKILL.md is %d bytes (> 35 KiB)" % size)
        self.assertGreater(size, 1024, "SKILL.md looks truncated: %d bytes" % size)

    def test_every_referenced_reference_file_exists(self):
        text = read(SKILL_PATH)
        referenced = set(re.findall(r"\.\./pdca[\w/-]*\.md", text))
        referenced |= {
            "references/" + name for name in re.findall(r"references/([\w-]+\.md)", text)
        }
        self.assertTrue(referenced, "SKILL.md references no phase contract")
        for rel in sorted(referenced):
            if rel.startswith("references/"):
                target = SKILL_DIR / rel
            else:
                target = (SKILL_DIR / rel).resolve()
            with self.subTest(reference=rel):
                self.assertTrue(target.is_file(), "dangling reference: %s" % rel)

    # --- tier labels only, never a model id --------------------------------

    def test_no_model_field_anywhere_in_the_overlay(self):
        for path in sorted(SKILL_DIR.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                text = read(path)
            except (UnicodeDecodeError, OSError):
                continue
            with self.subTest(path=str(path.relative_to(SKILL_DIR))):
                self.assertNotRegex(text, r"(?m)^\s*#?\s*model\s*:", "%s pins a model id" % path)

    def test_assets_carry_only_a_tier_label(self):
        assets = sorted((SKILL_DIR / "assets/opencode-agents").glob("*.md"))
        self.assertTrue(assets, "no role assets found")
        for path in assets:
            with self.subTest(asset=path.name):
                self.assertRegex(read(path), r"(?m)^# tier: (cheap|medium|strong)\s*$")

    def test_no_routing_enum_tokens_in_the_family(self):
        # The single-PLAN architecture has no cheap classifier, no
        # `selected_variant` and no `execution_kind` enum anywhere.
        tokens = (_cat("selected", "_variant"), _cat("execution", "_kind"))
        for root in FAMILY_DIRS:
            for path in sorted(root.rglob("*.md")):
                text = read(path)
                for token in tokens:
                    with self.subTest(path=str(path), token=token):
                        self.assertNotIn(token, text)


class ContractConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)
        cls.fm = parse_frontmatter(frontmatter_block(cls.skill_raw))
        # Base cycle: the retained rules now live here.
        cls.base_raw = read(BASE_SKILL)
        cls.base = norm(cls.base_raw)
        cls.base_plan_raw = read(BASE_PLAN)
        cls.base_plan = norm(cls.base_plan_raw)
        cls.base_act_raw = read(BASE_ACT)
        cls.base_act = norm(cls.base_act_raw)
        cls.counters = norm(between(cls.base_raw, "## State machine and counters",
                                    "### Phase progress mirror"))
        cls.mirror = norm(between(cls.base_raw, "### Phase progress mirror",
                                  "### DO → PLAN candidate"))
        cls.status_file = norm(between(cls.base_act_raw, "## Status file",
                                       "## Message for the next session"))
        cls.autonomous = norm(between(cls.base_raw, "## Roles and host requirements",
                                     "## Lens: probe")) + " " + norm(
            between(cls.base_raw, "## Control modes and the campaign owner", "## Lens: probe"))
        cls.escalation = norm(
            between(cls.base_raw, "## Escalation (`pdca-escalate`)",
                    "## Generic operating constraints")
        )
        cls.evidence = norm(
            between(cls.base_raw, "## Evidence over assertion", "## Workspace and durable status")
        )
        cls.claims = norm(
            between(cls.base_raw, "### Claims and veto", "## Evidence over assertion")
        )
        cls.recovery = norm(
            between(cls.base_raw, "## Recovery", "## Escalation (`pdca-escalate`)")
        )
        cls.injection = norm(
            between(cls.base_raw, "## Generic operating constraints", "## Red flags (self-check)")
        )
        cls.gate1 = norm(between(cls.base_raw, "1. **PLAN → DO**", "2. **DO → CHECK**"))
        cls.gate2 = norm(between(cls.base_raw, "2. **DO → CHECK**", "3. **CHECK → ACT**"))
        cls.gate3 = norm(between(cls.base_raw, "3. **CHECK → ACT**", "4. **ACT → EXIT**"))
        cls.gate4 = norm(
            between(cls.base_raw, "4. **ACT → EXIT**",
                    "**You cannot skip CHECK. You cannot close the cycle without ACT.**")
        )
        # Overlay-local sections.
        cls.plan_deltas = norm(
            between(cls.skill_raw, "## Code-specific plan deltas",
                    "### Language and correctness anti-patterns")
        )
        cls.check_deltas = norm(
            between(cls.skill_raw, "## Code-specific check deltas",
                    "## Code-specific do/act deltas")
        )
        cls.do_act = norm(
            between(cls.skill_raw, "## Code-specific do/act deltas", "## Composition")
        )
        cls.do_streams = norm(
            between(cls.skill_raw, "### Parallel DO streams", "### Worktree sub-tasks")
        )
        cls.worktree = norm(
            between(cls.skill_raw, "### Worktree sub-tasks", "### Status, ACT and handoff")
        )

    # --- frontmatter ------------------------------------------------------

    def test_frontmatter_has_exactly_name_and_description(self):
        self.assertEqual({"name", "description", "metadata", "disable-model-invocation"}, set(self.fm))
        self.assertEqual("pdca-coder", self.fm["name"])
        self.assertNotIn("model", self.fm)

    def test_description_is_coding_and_stack_agnostic(self):
        desc = self.fm["description"].lower()
        for token in ("overlay", "programming", "code"):
            self.assertIn(token, desc)
        self.assertIn("pdca-coder", desc)
        for banned in ("any task", "presentation", "research", "non-code"):
            self.assertNotIn(banned, desc)
        # The stack-agnostic scope the description used to spell out moved into
        # §When it applies when the text was shortened to an overlay description.
        when = norm(between(self.skill_raw, "## When it applies", "## Toolchain and lenses"))
        self.assertIn("Software work in any stack", when)
        self.assertIn("The overlay is stack-agnostic", when)

    def test_no_model_binding_in_frontmatter(self):
        block = frontmatter_block(self.skill_raw)
        self.assertNotRegex(block, r"(?m)^\s*model\s*:")

    # --- state machine, phases, counters, loop-back -----------------------

    def test_state_machine_has_all_phases(self):
        for phase in ("PLAN", "DO", "CHECK", "ACT"):
            self.assertIn(phase, self.counters)

    def test_three_counters_described(self):
        self.assertIn("Three counters", self.counters)
        self.assertIn("cycle number", self.counters)
        self.assertIn("Plan revision r", self.counters)
        self.assertIn("iteration n/3", self.counters)
        self.assertIn("starts at 1", self.counters)
        self.assertIn("new revision resets n to 1", self.counters)
        self.assertIn("no global n/3 on every loop-back", self.counters)

    def test_loopback_description_present(self):
        self.assertIn("DO → PLAN", self.counters)
        self.assertIn("loop-back", self.base.lower())

    # --- transition gates 1-4 with key conditions -------------------------

    def test_gate1_conditions(self):
        for token in ("acceptance criteria", "verification method", "carrying claims",
                      "form", "effort estimate", "the user's approval"):
            self.assertIn(token, self.gate1)
        self.assertIn("Normal mode with no acceptance criteria", self.gate1)
        self.assertIn("autonomous → route through", self.gate1)

    def test_gate1_also_requires_the_code_decisions(self):
        for token in ("test strategy", "docs plan", "performance-measurement decision",
                      "reconnaissance decision", "unit execution mode",
                      "toolchain/lens selection"):
            self.assertIn(token, self.plan_deltas)
        self.assertIn("a silent skip fails gate 1", self.plan_deltas)

    def test_gate2_conditions(self):
        self.assertIn("all active, non-superseded D: units are done", self.gate2)
        self.assertIn("recorded evidence", self.gate2)
        self.assertIn("blocker report is not done", self.gate2)
        # A code unit/stream is `done` under the same rule, and the evidence is a
        # real run (exit status + numbers + log path), never a report.
        self.assertIn("a code unit/stream is done only under the same rule", self.skill)
        self.assertIn("Every run: exit status", self.skill)

    def test_gate3_conditions(self):
        self.assertIn("all criteria met", self.gate3)
        self.assertIn("cross-part consistency", self.gate3)
        self.assertIn("Four unconditional streams plus security when triggered",
                      self.check_deltas)
        self.assertIn("gate 3 needs all green", self.check_deltas)

    def test_gate4_conditions(self):
        self.assertIn("status file is finalized", self.gate4)
        self.assertIn("no product/test/checked artifact changed", self.gate4)
        self.assertIn("AGENTS.md", self.do_act)

    # --- the status file is the only progress mirror ----------------------

    def test_progress_mirror_rules(self):
        self.assertIn("Progress is recorded in one place", self.counters)
        self.assertIn("the cycle status file", self.counters)
        self.assertIn("source of truth", self.counters)
        self.assertIn("no separate todo or sidebar mirror", self.counters)
        self.assertIn("executor updates the status file in the same turn", self.mirror)
        self.assertIn("Reconcile each turn", self.mirror)
        self.assertIn("never from memory", self.mirror)

    # --- autonomous mode: delegation, fallback, Notice --------------------

    def test_autonomous_delegation_and_fallback(self):
        self.assertIn("pdca-orchestrator", self.autonomous)
        self.assertIn("delegates to the existing cheap pdca-orchestrator", self.autonomous)
        self.assertIn("fall back to the flat cheap primary", self.autonomous)
        self.assertIn("nested delegation", self.autonomous)
        self.assertIn("Notice:", self.autonomous)

    # --- escalation: triggers, scoping, no-4th, route-don't-re-decide -----

    def test_escalation_triggers_and_counter_scope(self):
        self.assertIn("Triggers:", self.escalation)
        self.assertIn("scoped to the current revision r", self.escalation)
        self.assertIn("new revision at n=1", self.escalation)
        self.assertIn("third failed CHECK of the same revision", self.escalation)
        self.assertIn("same defect", self.escalation)

    def test_escalation_no_fourth_attempt(self):
        self.assertIn("there is no 4th attempt", self.escalation)
        self.assertIn("no 4th attempt even after", self.escalation)

    def test_escalation_is_routed_not_re_decided(self):
        self.assertIn("The decision routes; the driver does not re-decide", self.escalation)
        self.assertIn("carries it out solely by routing", self.escalation)
        self.assertIn("genuinely revised remediation plan", self.escalation)

    # --- claims and veto --------------------------------------------------

    def test_carrying_claims_are_a_veto(self):
        self.assertIn("carrying claims", self.claims)
        self.assertIn("confirmed or unverified", self.claims)
        self.assertIn("forbids PASS and final done", self.claims)
        self.assertIn("narrowing of the result", self.claims)

    # --- evidence, recovery, instruction priority/injection ---------------

    def test_evidence_over_assertion(self):
        self.assertIn("fresh evidence", self.evidence)
        self.assertIn("exit status", self.evidence)
        self.assertIn("log path", self.evidence)
        self.assertIn("A report ≠ a result", self.evidence)
        # Code-specific: the regression test is red <-> green, both runs reported.
        self.assertIn("A regression test is red↔green", self.skill)

    def test_recovery_after_compaction(self):
        self.assertIn("status file is the source of truth", self.recovery)
        self.assertIn("revision r", self.recovery)
        self.assertIn("attempt n/3", self.recovery)
        self.assertIn("reconstruct the state", self.recovery)
        self.assertIn("Recovered after compaction", self.recovery)

    def test_instruction_priority_and_injection_defense(self):
        self.assertIn("safety and confidentiality invariants", self.injection)
        self.assertIn("explicit user request", self.injection)
        self.assertIn("Injection defense", self.injection)
        self.assertIn("tell the user, do not execute", self.injection)
        self.assertIn("Credential confidentiality", self.injection)
        self.assertIn("secret material", self.injection)

    # --- status file, parallel DO streams, worktree template --------------

    def test_cycle_status_file_schema(self):
        self.assertIn(".pdca/status/<task>-<N>.md", self.status_file)
        self.assertIn("Progress log", self.status_file)
        self.assertIn("Current cycle N", self.status_file)
        self.assertIn("Plan revision r", self.status_file)
        self.assertIn("Attempt n", self.status_file)
        self.assertIn("Defect history", self.status_file)

    def test_parallel_do_streams(self):
        self.assertIn("test then code", self.do_streams)
        self.assertIn("docs later", self.do_streams)
        self.assertIn("prose documentation", self.do_streams)
        self.assertIn("no TDD ordering", self.skill)

    def test_worktree_sub_task_template(self):
        self.assertIn("absolute paths", self.worktree)
        self.assertIn("commits to its own branch", self.worktree)
        self.assertIn("push never happens", self.worktree)
        template = norm(between(read(CODER_ACT),
                                "## Worktree sub-tasks of one cycle",
                                "## Debugging (loop-back"))
        self.assertTrue(template, "worktree template moved out of references/act.md")
        for token in ("Work ONLY in worktree", "git -C", "never push", "absolute paths"):
            self.assertIn(token, template)


class ForbiddenTokenGuardTest(unittest.TestCase):
    """Zero matches for all nine stack tokens anywhere in the pdca-coder tree."""

    def test_no_forbidden_token_in_any_pdca_file(self):
        hits = scan_tree(SKILL_DIR, forbidden_tokens())
        self.assertEqual([], hits, "forbidden tokens found: %r" % hits)

    def test_only_the_runner_is_exempt_from_the_stack_scan(self):
        self.assertEqual({RUNNER_ASSET}, set(SCAN_EXEMPT))
        self.assertTrue(RUNNER_ASSET.is_file(), "runner asset missing")
        hits = [p for p, _ in scan_tree(SKILL_DIR, forbidden_tokens())]
        self.assertNotIn(str(RUNNER_ASSET), hits)

    def test_detector_catches_a_rejected_sample(self):
        patterns = forbidden_tokens()
        rejected = _cat("prefix ", "dot", "net-", " suffix")
        clean = "a perfectly ordinary sentence"
        self.assertTrue(any(p.lower() in rejected.lower() for p in patterns))
        self.assertFalse(any(p.lower() in clean.lower() for p in patterns))

    def test_all_nine_patterns_are_scanned(self):
        self.assertEqual(9, len(forbidden_tokens()))


class AuditGateBoundaryTest(unittest.TestCase):
    """#238 guards: the PASS gate is BINDING/APPLICABLE, extra audit rows are diagnostic.

    The rule is a base rule and now lives in `../pdca/references/plan.md`
    (§Frozen evidence manifest); the overlay inherits it. Rule-presence only
    (reads Markdown text; never executes a model), so it proves the wording, not
    the behavior.
    """

    MANIFEST_ENTRY = "required"

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_plan_raw = read(BASE_PLAN)
        cls.base_plan = norm(cls.base_plan_raw)
        cls.frozen = norm(
            between(cls.base_plan_raw, "## Frozen evidence manifest",
                    "## One evidence location binding")
        )

    def test_gate_replaced_with_binding_applicable(self):
        # The gate line may wrap in the raw Markdown; compare normalised text.
        self.assertIn("No PASS while any BINDING/APPLICABLE", self.frozen)

    def test_old_absolute_gate_is_gone(self):
        self.assertNotIn(
            "No PASS while any `%s` entry is `open`" % self.MANIFEST_ENTRY,
            self.base_plan_raw,
        )

    def test_append_only_disposition_section_present(self):
        self.assertIn("Binding/applicability disposition (append-only)", self.base_plan_raw)
        self.assertIn("diagnostic_nonbinding", self.base_plan_raw)
        self.assertIn("never rewritten", self.base_plan_raw)
        self.assertIn("excluded from the set of binding acceptance blockers", self.base_plan)

    def test_exclusion_is_not_a_loophole(self):
        self.assertIn("not a loophole", self.frozen)
        self.assertIn("stays binding", self.frozen)
        self.assertIn("fail/re-gather/STOP route", self.frozen)
        self.assertIn("source-copy mismatch", self.frozen)

    def test_plan_may_not_invent_audit_hard_gates(self):
        self.assertIn("diagnostic notes", self.frozen)


if __name__ == "__main__":
    unittest.main()
