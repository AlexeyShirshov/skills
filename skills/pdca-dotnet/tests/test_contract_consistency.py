"""Static regression guards for the pdca-dotnet overlay contract.

The PDCA family was restructured into **one base cycle plus overlays**:

* `skills/pdca/SKILL.md` — the single public entry and the base cycle (entry/form,
  roles, control modes, state machine, counters, gates, phase contracts,
  claims/veto, evidence, status file, budgets, recovery, escalation, constraints,
  red flags, approval), with `references/{plan,check,act}.md`;
* `skills/pdca-coder/SKILL.md` — the generic programming overlay (inherits base);
* `skills/pdca-dotnet/SKILL.md` — **this** .NET overlay, which inherits base **and**
  coder and adds only .NET deltas, with `references/{plan,check,act}.md`.

The guards below read every rule where it canonically lives: a retained base rule in
`../pdca/**`, an inherited code rule in `../pdca-coder/**`, .NET-specific content in
this skill's `SKILL.md` / `references/**`, and the architecture (inheritance chain,
no duplicated blocks, host limits, `# tier:` only) over the files themselves. They
are rule-presence guards, **not** behavioral proof: they do not execute a model and
do not prove that an agent follows the contract. Behavioral scenario review is a
separate step.

Run:
    python3 -m unittest discover -s skills/pdca-dotnet/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_PATH = SKILL_DIR / "SKILL.md"
# Inheritance chain: base cycle -> coder overlay -> this .NET overlay.
BASE_DIR = SKILL_DIR.parent / "pdca"
CODER_DIR = SKILL_DIR.parent / "pdca-coder"
BASE_SKILL = BASE_DIR / "SKILL.md"
BASE_PLAN = BASE_DIR / "references/plan.md"
BASE_ACT = BASE_DIR / "references/act.md"
CODER_SKILL = CODER_DIR / "SKILL.md"
CODER_PLAN = CODER_DIR / "references/plan.md"
CODER_CHECK = CODER_DIR / "references/check.md"
DOTNET_PLAN = SKILL_DIR / "references/plan.md"
DOTNET_CHECK = SKILL_DIR / "references/check.md"
DOTNET_ACT = SKILL_DIR / "references/act.md"
ASSET_AGENTS = SKILL_DIR / "assets/opencode-agents"
ASSET_BRIEFS = [
    ASSET_AGENTS / f"{name}.md"
    for name in ("pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate")
]
# Asset stem -> canonical contract branch, for the shared contract branches.
CANON = {
    "pdca-planner": "planner", "pdca-executor": "coder", "pdca-check": "check",
    "pdca-escalate": "escalate", "pdca-scout": "scout",
    "pdca-security-auditor": "security-auditor",
}
# Task 2: the seven published EN assets and the tier each must carry (no `model:`).
PUBLISHED_ASSETS = [
    ASSET_AGENTS / f"{name}.md"
    for name in ("pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate",
                 "pdca-scout", "pdca-security-auditor", "pdca-orchestrator")
]
ROLE_TIER = {
    "pdca-orchestrator": "cheap",
    "pdca-planner": "medium",
    "pdca-executor": "cheap",
    "pdca-check": "medium",
    "pdca-escalate": "strong",
    "pdca-scout": "cheap",
    "pdca-security-auditor": "medium",
}
# Task 3: cross-artifact label sources (diagram source) and the non-executable
# scenario matrix.  These are text/JSON presence guards only.
DIAGRAM_DIR = SKILL_DIR / "assets/diagram"
GEN_PDCA_PATH = DIAGRAM_DIR / "gen_pdca.py"
SCENARIOS_PATH = SKILL_DIR / "tests/scenarios.md"
RUNNER_ASSET = ASSET_AGENTS / "pdca-orchestrator.md"

# The host truncates a loaded file at 50 KiB / 2000 lines; the main contract of an
# overlay is additionally targeted at <= 35 KiB so its phase references stay loadable.
HOST_LIMIT_BYTES = 50 * 1024
HOST_LIMIT_LINES = 2000
MAIN_TARGET_BYTES = 35 * 1024


def norm(text: str) -> str:
    """Collapse whitespace (incl. line wraps) and drop backticks/format noise."""
    text = text.replace("`", "").replace("*", "")
    return re.sub(r"\s+", " ", text)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i:j] if j >= 0 else text[i:]


def headings(path: Path) -> list:
    """All level-2 Markdown headings of a file, in order."""
    return re.findall(r"(?m)^##\s+(.+?)\s*$", read(path))


def all_headings(path: Path) -> str:
    """Every level-2/3 heading of a file, newline-joined (substring match)."""
    return "\n".join(re.findall(r"(?m)^#{2,3}\s+(.+?)\s*$", read(path)))


class OverlayArchitectureTest(unittest.TestCase):
    """The .NET text is an overlay on the base cycle and on the coder overlay.

    Rule-presence and file-size guards only: they read Markdown text, so they prove
    the structure of the contract, not the behavior of a model.
    """

    # Sections the base owns (the .NET overlay must not re-declare them).
    BASE_OWNED = (
        "State machine",
        "Transition gates",
        "Phase progress mirror",
        "Control modes and the campaign owner",
        "Roles and host requirements",
        "Claims and veto",
        "Evidence over assertion",
        "Budgets",
        "Recovery",
        "Escalation",
        "Normal-mode approval",
    )
    # Sections the coder overlay owns and this one inherits.
    CODER_OWNED = (
        "Toolchain and lenses",
        "Code-specific plan deltas",
        "Code-specific check deltas",
        "Code-specific do/act deltas",
    )
    ALLOWED_HEADINGS = {
        "When it applies",
        ".NET toolchain and commands",
        ".NET plan deltas",
        ".NET check deltas",
        ".NET do/act deltas",
        "Composition",
        "References",
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)

    # --- inheritance chain -------------------------------------------------

    def test_declares_base_then_coder_then_itself(self):
        chain = norm(between(self.skill_raw, "**Inheritance chain.**", "**One PLAN"))
        self.assertIn("The base ../pdca/SKILL.md first", chain)
        self.assertIn("then ../pdca-coder/SKILL.md (the programming overlay), then this file", chain)
        self.assertIn("../pdca-incremental/SKILL.md", chain)
        self.assertIn("../pdca-collection/SKILL.md", chain)

    def test_parent_contracts_win_and_the_overlay_only_adds(self):
        self.assertIn("This is an overlay, not a cycle", self.skill)
        self.assertIn("If this file and the base or the coder overlay disagree on their rules, they win", self.skill)
        self.assertIn("This file only adds .NET facts, tools and the required relevant evidence", self.skill)
        self.assertIn("One PLAN, one state machine, one status file", self.skill)
        self.assertIn("never opens a second cycle, a second gate set or a second durable state", self.skill)

    def test_base_declares_the_dotnet_inheritance(self):
        base = norm(read(BASE_SKILL))
        self.assertIn("pdca-dotnet inherits coder", base)
        self.assertIn("overlay inheritance is preserved", base.lower())

    # --- no duplicated parent blocks --------------------------------------

    def test_does_not_redeclare_base_sections(self):
        ours = all_headings(SKILL_PATH)
        base_owned = all_headings(BASE_SKILL)
        for name in self.BASE_OWNED:
            with self.subTest(section=name):
                self.assertNotIn(
                    name, ours,
                    "the .NET overlay re-declares the base section %r instead of inheriting it" % name,
                )
                self.assertIn(
                    name, base_owned,
                    "the base no longer owns %r — the inheritance contract changed" % name,
                )

    def test_does_not_redeclare_coder_sections(self):
        ours = all_headings(SKILL_PATH)
        coder_owned = all_headings(CODER_SKILL)
        for name in self.CODER_OWNED:
            with self.subTest(section=name):
                self.assertNotIn(
                    name, ours,
                    "the .NET overlay re-declares the coder section %r instead of inheriting it" % name,
                )
                self.assertIn(
                    name, coder_owned,
                    "the coder overlay no longer owns %r — the inheritance contract changed" % name,
                )

    def test_section_skeleton_is_dotnet_deltas_only(self):
        self.assertEqual(self.ALLOWED_HEADINGS, set(headings(SKILL_PATH)))

    def test_roslyn_first_section_is_dotnet_specific(self):
        section = norm(between(self.skill_raw, "### Roslyn-first for C# symbols",
                               "### .NET specialists"))
        self.assertTrue(section, "Roslyn-first section missing")
        for token in ("the only way to answer a C# symbol question",
                      "rg/grep/glob/sed are never a symbol tool",
                      "tools.roslyn", 'solution: "/abs/path/App.slnx"'):
            self.assertIn(token, section)

    def test_composition_table_attributes_every_area_to_its_contract(self):
        raw = between(self.skill_raw, "## Composition", "The overlay adds **no**")
        rows = [
            line for line in raw.splitlines()
            if line.startswith("|") and "---" not in line
        ]
        self.assertTrue(rows, "composition table not found")
        rows = rows[1:]  # drop the header row
        sources = []
        for row in rows:
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            with self.subTest(row=cells[0]):
                self.assertEqual(3, len(cells))
                sources.append(cells[1])
                if cells[1] in ("base", "coder"):
                    self.assertTrue(
                        cells[2].startswith("inherits"),
                        "%r must be inherited, not redefined: %r" % (cells[0], cells[2]),
                    )
                else:
                    self.assertEqual("this file", cells[1])
                    self.assertTrue(cells[2].startswith("adds"), cells[2])
        self.assertEqual({"base", "coder", "this file"}, set(sources))
        self.assertEqual(1, sources.count("this file"), "exactly one group of .NET additions")
        self.assertEqual(len(rows) - 1, len(sources) - sources.count("this file"))

    # --- host limits -------------------------------------------------------

    def test_every_file_of_the_overlay_is_under_the_host_limit(self):
        docs = sorted(SKILL_DIR.rglob("*.md"))
        self.assertTrue(docs, "no Markdown contract found")
        for path in docs:
            with self.subTest(path=str(path.relative_to(SKILL_DIR))):
                self.assertLessEqual(path.stat().st_size, HOST_LIMIT_BYTES)
                self.assertLessEqual(len(read(path).splitlines()), HOST_LIMIT_LINES)

    def test_main_file_stays_within_the_35_kib_target(self):
        size = SKILL_PATH.stat().st_size
        self.assertLessEqual(size, MAIN_TARGET_BYTES, "SKILL.md is %d bytes (> 35 KiB)" % size)
        self.assertGreater(size, 1024, "SKILL.md looks truncated: %d bytes" % size)

    def test_every_referenced_contract_file_exists(self):
        referenced = set(re.findall(r"\.\./pdca[\w/-]*\.md", self.skill_raw))
        referenced |= {
            "references/" + name
            for name in re.findall(r"references/([\w-]+\.md)", self.skill_raw)
        }
        self.assertTrue(referenced, "SKILL.md references no phase contract")
        for rel in sorted(referenced):
            target = SKILL_DIR / rel if rel.startswith("references/") else (SKILL_DIR / rel).resolve()
            with self.subTest(reference=rel):
                self.assertTrue(target.is_file(), "dangling reference: %s" % rel)

    def test_parent_references_are_named_alongside_every_phase(self):
        section = norm(between(self.skill_raw, "## References", "###"))
        if not section:
            section = norm(self.skill_raw[self.skill_raw.index("## References"):])
        for name in ("plan", "check", "act"):
            with self.subTest(phase=name):
                self.assertIn("../pdca/references/%s.md" % name, section)
                self.assertIn("../pdca-coder/references/%s.md" % name, section)

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

    def test_every_asset_carries_a_tier_label(self):
        assets = sorted(ASSET_AGENTS.glob("*.md"))
        self.assertTrue(assets, "no role assets shipped")
        for path in assets:
            with self.subTest(asset=path.name):
                self.assertRegex(read(path), r"(?m)^# tier: (cheap|medium|strong)\s*$")

    def test_no_routing_enum_tokens_in_the_chain(self):
        # One PLAN decides form/overlay: no `selected_variant`, no `execution_kind`.
        tokens = ("selected" + "_variant", "execution" + "_kind")
        for root in (BASE_DIR, CODER_DIR, SKILL_DIR):
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
        # Base cycle: the retained rules now live in ../pdca/.
        cls.base_raw = read(BASE_SKILL)
        cls.base = norm(cls.base_raw)
        cls.base_plan_raw = read(BASE_PLAN)
        cls.base_plan = norm(cls.base_plan_raw)
        cls.base_act_raw = read(BASE_ACT)
        cls.base_act = norm(cls.base_act_raw)
        cls.coder_raw = read(CODER_SKILL)
        cls.coder = norm(cls.coder_raw)
        cls.coder_check_raw = read(CODER_CHECK)
        cls.coder_check = norm(cls.coder_check_raw)
        # Base slices.
        cls.counters = norm(between(cls.base_raw, "## State machine and counters",
                                    "### Phase progress mirror"))
        cls.mirror = norm(between(cls.base_raw, "### Phase progress mirror",
                                  "### DO → PLAN candidate"))
        cls.status_file = norm(between(cls.base_act_raw, "## Status file",
                                       "## Message for the next session"))
        cls.unit_states = norm(between(cls.base_act_raw, "**Unit states**",
                                       "**Content — a brief handoff"))
        cls.gate1 = norm(between(cls.base_raw, "1. **PLAN → DO**", "2. **DO → CHECK**"))
        cls.gate2 = norm(between(cls.base_raw, "2. **DO → CHECK**", "3. **CHECK → ACT**"))
        cls.gate3 = norm(between(cls.base_raw, "3. **CHECK → ACT**", "4. **ACT → EXIT**"))
        cls.gate4 = norm(
            between(cls.base_raw, "4. **ACT → EXIT**",
                    "**You cannot skip CHECK. You cannot close the cycle without ACT.**")
        )
        cls.red_flags = norm(between(cls.base_raw, "## Red flags (self-check)",
                                     "## Normal-mode approval"))
        cls.host = norm(between(cls.base_raw, "## Roles and host requirements",
                                "## Control modes and the campaign owner"))
        cls.orchestrator_section = norm(
            between(cls.base_raw, "## Control modes and the campaign owner", "## Lens")
        )
        cls.orchestrator = cls.orchestrator_section + " " + norm(read(RUNNER_ASSET))
        cls.autonomous = cls.host + " " + cls.orchestrator_section + " " + norm(
            between(cls.base_raw, "## Normal-mode approval", "## References")
        )
        cls.escalation = norm(
            between(cls.base_raw, "## Escalation (`pdca-escalate`)",
                    "## Generic operating constraints")
        )
        cls.recovery = norm(
            between(cls.base_raw, "## Recovery", "## Escalation (`pdca-escalate`)")
        )
        cls.evidence = norm(
            between(cls.base_raw, "## Evidence over assertion", "## Workspace and durable status")
        )
        cls.keep_check = norm(
            between(cls.coder_check_raw, "## Keep CHECK within one approved PLAN",
                    "## Parallel CHECK streams")
        )
        # Overlay slices.
        cls.check_streams = norm(
            between(cls.coder_raw, "## Code-specific check deltas",
                    "## Code-specific do/act deltas")
        ) + " " + norm(between(cls.skill_raw, "## .NET check deltas", "## .NET do/act deltas"))
        cls.dotnet_deltas = norm(
            between(cls.skill_raw, "## .NET plan deltas", "### Completeness gate at PLAN")
        )

    # --- revision `r` counter semantics (base) ---------------------------

    def test_three_counters_defined_not_two(self):
        self.assertIn("Three counters", self.counters)
        self.assertNotIn("Two counters", self.counters)

    def test_plan_revision_counter_definition(self):
        self.assertIn("Plan revision r", self.counters)
        self.assertIn("starts at 1", self.counters)
        self.assertIn("only when pdca-planner actually issued a revised plan", self.counters)

    def test_plan_to_do_starts_at_one(self):
        self.assertIn("PLAN(r) → DO starts at 1", self.counters)

    def test_check_to_do_increments_and_third_check_escalates(self):
        self.assertIn("CHECK → DO increments", self.counters)
        self.assertIn("third failed CHECK of the same revision", self.counters)
        self.assertIn("pdca-escalate before a fourth", self.counters)
        # The counter block names the fourth attempt as forbidden; the rule itself
        # is canonically worded in §Escalation.
        self.assertIn("before a fourth", self.counters)
        self.assertIn("there is no 4th", self.escalation)

    def test_plan_returns_do_not_consume_attempts_and_new_revision_resets(self):
        self.assertIn("do not consume the next revision's attempts", self.counters)
        self.assertIn("new revision resets n to 1", self.counters)

    def test_rejected_candidate_not_new_revision_no_reset(self):
        self.assertIn("rejected candidate", self.counters)
        self.assertIn("is not a revision: no bump, no attempt reset", self.counters)

    def test_replan_does_not_erase_same_defect_history(self):
        self.assertIn("same-defect history is not erased by a replan", self.counters)
        # The same-defect trigger itself is canonical in §Escalation (counters point there).
        self.assertIn("same defect came back after one fix", self.escalation)
        self.assertIn("escalate before the second fix", self.escalation)

    def test_replan_cap_is_the_declared_stop_loss_budget(self):
        # A universal "N revisions" cap would be an unplanned extra rule; the bound
        # is the plan's own stop-loss budget, fixed at gate 1 and never renewed.
        self.assertNotIn("No cap on revisions", self.counters)
        self.assertNotIn("maximum of 3 revisions", self.base)
        self.assertIn("stop-loss budget", self.counters)
        self.assertIn("maximum revisions", self.counters)
        self.assertIn("never to an unplanned extra attempt", self.counters)
        budgets = norm(between(self.base_raw, "## Budgets", "## Overlays"))
        self.assertIn("are not renewed", budgets)

    def test_no_global_iteration_on_every_loopback(self):
        self.assertNotIn("grows on every loop-back", self.counters)
        self.assertIn("no global n/3 on every loop-back", self.counters)

    # --- unfinished D / blocker retention / superseded mapping -----------

    def test_gate2_blocker_report_not_done_and_retained(self):
        self.assertIn("blocker report is not done", self.gate2)
        self.assertIn("unfinished work stays blocked/pending", self.gate2)
        self.assertIn("every closed D: is in the status file", self.gate2)

    def test_gate2_pending_blocked_prevents_gate(self):
        self.assertIn("blocked/pending", self.gate2)
        # Gate 2 closes only on done units with recorded evidence.
        self.assertIn("all active, non-superseded D: units are done", self.gate2)
        self.assertIn("recorded evidence", self.gate2)

    def test_rejected_candidate_resumes_original_d(self):
        self.assertIn("rejected candidate resumes the original D", self.gate2)

    def test_superseded_replacement_mapping_required(self):
        # Mapping is required for an *actual replacement*; an additive prerequisite
        # gets none (see FinalFixGuardTest). Not weakened: the mapping stays required.
        self.assertIn("superseded→replacement", self.base_act)
        self.assertIn("actual scope replacement", self.base)
        self.assertIn(
            "requires an explicit <superseded unit> → <replacement> mapping",
            self.base,
        )
        self.assertIn("not superseded, no mapping", self.base)

    # --- the status file is the only progress mirror ----------------------

    def test_progress_mirror_is_status_file_only(self):
        self.assertIn("Progress is recorded in one place", self.counters)
        self.assertIn("the cycle status file", self.counters)
        self.assertIn("source of truth", self.counters)
        self.assertIn("no separate todo or sidebar mirror", self.counters)

    def test_parallel_units_tracked_in_status_file(self):
        self.assertIn("DO units table", self.status_file)
        self.assertIn("no separate todo or sidebar mirror", self.counters)
        # Code rows (per-unit/stream table) are added by the coder overlay, not
        # redefined here.
        self.assertIn("per-unit/stream table", self.coder)

    def test_aggregate_d_closes_on_gate2(self):
        self.assertIn(
            "The aggregate D: closes when every active, non-superseded unit is done", self.unit_states
        )
        self.assertIn("superseded never counts as done", self.unit_states)

    # --- gate 1 transition + red-flag section (fix round 1) --------------

    def test_gate1_records_the_transition_in_the_status_file(self):
        # Gate 1 writes the plan to the status file and records the DO transition
        # there (units are tracked in that one file), not "the first `D:`".
        self.assertIn("the plan written to the status file", self.gate1)
        self.assertIn("the executor logs DO started", self.gate1)
        self.assertIn("records the transition", self.gate1)
        self.assertNotIn("the first D:", self.gate1)
        self.assertIn("Progress is recorded in one place", self.counters)

    def test_redflag_attempt_scoped_to_same_revision_not_global(self):
        # Red flags name the deviation (next attempt instead of escalate); the
        # exact revision-scoped counter rules are canonical in §State machine /
        # §Escalation, to which the red flag points.
        self.assertIn("I made a next attempt instead of pdca-escalate", self.red_flags)
        self.assertIn("third failed CHECK of the same revision", self.counters)
        self.assertIn("before a fourth", self.counters)
        self.assertIn("there is no 4th", self.escalation)
        self.assertIn("history persists across revisions", self.escalation)
        self.assertNotIn("4th iteration in general", self.red_flags)

    def test_unit_state_schema_with_replacement(self):
        self.assertIn("Unit states", self.status_file)
        for state in ("pending", "running", "blocked", "done", "superseded"):
            self.assertIn(state, self.status_file)
        self.assertIn("superseded unit", self.status_file)

    # --- status file journal / replan ------------------------------------

    def test_status_file_journal_template_carries_revision(self):
        self.assertIn("<UTC time> | <phase> | revision r | iteration n/3 | <event>",
                      self.status_file)

    def test_replan_records_outgoing_failed_attempt(self):
        self.assertIn("outgoing failed attempt", self.status_file)

    # --- same-scope cleanup ----------------------------------------------

    def test_numeric_757_replaced_with_heading_pointer(self):
        self.assertNotIn(":757", self.skill_raw)
        self.assertNotIn(":757", read(CODER_PLAN))
        # The rule is carried by the named heading, not by a numeric line pointer.
        self.assertIn("## PLAN owns the quality of the plan", read(CODER_PLAN))
        self.assertIn("A weak statement", norm(read(CODER_PLAN)))  # essence kept

    def test_four_unconditional_check_streams(self):
        self.assertIn("Four unconditional streams", self.check_streams)
        self.assertNotIn("Three unconditional streams", self.check_streams)

    # --- escalation wording scoped to a revision -------------------------

    def test_escalation_same_defect_scoped_and_revision_aware(self):
        self.assertIn("same revision", self.escalation)
        self.assertIn("same defect came back after one fix", self.escalation)
        self.assertNotIn("after the 3rd failed iteration", self.escalation)

    def test_autonomous_escalation_revision_aware(self):
        # Autonomous mode does not suspend the contract, so the escalation counter
        # stays revision-scoped exactly as in normal mode.
        constraints = norm(between(self.base_raw, "## Generic operating constraints",
                                   "## Red flags (self-check)"))
        self.assertIn("Always in force in both modes", constraints)
        self.assertIn("autonomous mode does not suspend them", constraints)
        self.assertIn("scoped to the current revision r", self.escalation)

    # --- briefs mirror the rules (scoped to each brief's operative clause) --
    # Assert key *relationships* inside the operative section, not a bare
    # keyword anywhere. EN and RU wordings are both accepted.

    def _scoped(self, path: Path, start: str, end: str) -> str:
        chunk = between(read(path), start, end)
        self.assertTrue(chunk, f"{path}: section {start!r}..{end!r} not found")
        return norm(chunk)

    def _assert_patterns(self, text: str, label: str, patterns) -> None:
        for pat in patterns:
            self.assertRegex(text, pat, f"{label}: missing /{pat}/")

    def _assert_brief_contract(self, path: Path) -> None:
        # The published assets use prefixed ids; one canonical stem selects the
        # contract branch.  The assets are EN-only.
        name = CANON.get(path.stem, path.stem)
        if name == "coder":
            status = self._scoped(
                path,
                "Status file.",
                "Unfinished work",
            )
            self.assertRegex(status, r"revision r\s*\|\s*iteration n/3")
            retention = self._scoped(
                path,
                "Unfinished work",
                "Evidence, not claims",
            )
            self._assert_patterns(retention, f"pdca-executor retention {path}", [
                r"gate 2",
                r"rejected candidate",
                r"original `?D`?",
                r"superseded",
            ])
        elif name == "planner":
            step = self._scoped(path, "10.", "11.")
            self._assert_patterns(step, f"pdca-planner step10 {path}", [
                r"revised plan",
                r"increments the revision",
                r"resets the attempt n to 1",
                r"rejected candidate",
                r"not a new revision",
                r"does not reset the attempts",
                r"superseded",
            ])
        elif name == "check":
            step = self._scoped(path, "5.", "6.")
            self._assert_patterns(step, f"pdca-check item5 {path}", [
                r"third failed CHECK of the same revision",
                r"same defect",
                r"persists across revisions",
            ])
        elif name == "escalate":
            para = self._scoped(
                path,
                "The counter is scoped",
                "## What you do",
            )
            self._assert_patterns(para, f"pdca-escalate counter {path}", [
                r"PLAN\(r\) → DO",
                r"n=1",
                r"third failed CHECK of the same revision",
                r"same defect",
                r"does not erase",
            ])
        else:
            self.fail(f"unexpected brief {path}")

    def test_asset_briefs_mirror_scoped_contract(self):
        for path in ASSET_BRIEFS:
            with self.subTest(path=path.name):
                self._assert_brief_contract(path)

    def _assert_escalator_brief_revision_scoped(self, path: Path) -> None:
        para = self._scoped(
            path,
            "The counter is scoped",
            "## What you do",
        )
        self.assertRegex(
            para,
            r"third failed CHECK of the same revision",
        )

    def test_escalator_briefs_revision_scoped(self):
        with self.subTest(path=str(ASSET_BRIEFS[3])):
            self._assert_escalator_brief_revision_scoped(ASSET_BRIEFS[3])

    # --- autonomous mode is question-free (base) -------------------------

    def test_autonomous_mode_has_no_ask_user_instruction(self):
        # No user exists in autonomous mode: no question may be posed at all there.
        self.assertNotIn("Ask a question", self.autonomous)
        self.assertNotIn("ask the user", self.orchestrator_section)
        self.assertIn("no pauses and no questions", self.autonomous)
        self.assertIn("has no approval slots and no plan-approval gate", self.autonomous)

    def test_autonomous_blocker_routed_through_planner_or_escalate_to_stop(self):
        self.assertIn("pdca-planner", self.autonomous)
        self.assertIn("pdca-escalate", self.autonomous)
        self.assertIn("resource blocker", self.autonomous)
        self.assertIn("Notice:", self.autonomous)
        # The question-free route ends in a planner/escalate decision and a STOP.
        self.assertIn("autonomous → route through planner/escalate and STOP", self.gate1)

    def test_autonomous_covers_missing_criteria_and_unavailable_resource(self):
        # A missing acceptance criterion / unavailable resource is covered by the
        # question-free route, not by asking.
        self.assertIn("Normal mode with no acceptance criteria", self.gate1)
        self.assertIn("route through planner/escalate and STOP", self.gate1)
        self.assertIn("required-but-unavailable role is a resource blocker", self.autonomous)
        self.assertIn("ambiguous", self.escalation)

    def test_gate1_ask_instruction_scoped_to_normal_mode(self):
        # The gate-1 ask-user instruction must be explicitly normal-mode only.
        self.assertNotRegex(self.gate1, r"acceptance criteria\s*—\s*ask, do not guess")
        self.assertIn("Normal mode with no acceptance criteria", self.gate1)
        self.assertIn("autonomous → route through planner/escalate", self.gate1)

    def test_normal_mode_retains_questions_and_approval(self):
        self.assertIn("the user's approval", self.gate1)
        self.assertIn("Normal mode", self.gate1)
        self.assertIn("ask the user", self.gate1)
        approval = norm(between(self.base_raw, "## Normal-mode approval", "## References"))
        self.assertIn("that approval is the only start signal", approval)

    # --- DO-candidate fourth branch + trigger 5 ---------------------------

    def test_escalation_trigger5_low_confidence_without_externalness(self):
        self.assertIn("low confidence", self.escalation)
        self.assertIn("without established externalness", self.escalation)
        # The old "only if outside-cycle confirmed" local restriction must be gone.
        self.assertNotIn("pdca-escalate is called only if", self.escalation)
        candidate = norm(between(self.base_raw, "### DO → PLAN candidate", "## Transition gates"))
        self.assertIn("provisional candidate", candidate)

    def _assert_planner_classification(self, path: Path) -> None:
        step = self._scoped(path, "10.", "11.")
        self._assert_patterns(step, f"pdca-planner classification {path}", [
            r"insufficient evidence",
            r"pdca-scout|scout",
            r"low confidence",
            r"trigger 5",
            r"even without",
        ])

    def test_planner_four_way_classification_includes_insufficient_evidence(self):
        with self.subTest(path=str(ASSET_BRIEFS[0])):
            self._assert_planner_classification(ASSET_BRIEFS[0])

    def _assert_planner_response_format(self, path: Path) -> None:
        resp = self._scoped(
            path,
            "## Response format",
            "A missing item",
        )
        self._assert_patterns(resp, f"pdca-planner response {path}", [
            r"(?i)confidence and gaps",
            r"(?i)classif",
        ])

    def test_planner_response_format_has_confidence_and_classification_slot(self):
        with self.subTest(path=str(ASSET_BRIEFS[0])):
            self._assert_planner_response_format(ASSET_BRIEFS[0])

    # --- primary is a cheap dispatcher -----------------------------------

    def test_orchestrator_is_cheap_only_dispatcher(self):
        # Cheap-only: only an effective-cheap primary drives the cycle; a
        # medium/strong primary is explicitly excluded, and the runner never
        # plans/judges/edits on its own.
        self.assertIn("Orchestration is cheap-only", self.host)
        self.assertIn("medium/strong primary does not drive the cycle", self.host)
        self.assertIn("The driver does not classify and does not plan", self.base)
        self.assertIn("not a reader, not a decider and not a worker", self.orchestrator)
        self.assertIn("You never plan, never judge, never escalate on your own", self.orchestrator)
        self.assertIn("never classify the task, choose the form or pick an overlay",
                      self.orchestrator)
        self.assertNotIn("every primary", self.orchestrator)

    def test_primary_wording_is_by_effective_tier_not_agent_name(self):
        # The driver is named by effective host-profile tier, never tied to one
        # agent name and never "any primary".
        self.assertIn("by effective tier, not by agent name", self.base)
        self.assertIn("effective host-profile tier is cheap", self.base)
        self.assertIn("flat cheap primary", self.base)
        self.assertNotIn("the orchestrator (primary)", self.base)
        self.assertNotIn("any primary", self.base)

    def test_skill_owns_cheap_only_orchestration_expensive_primary_excluded(self):
        self.assertIn("cheap-only", self.base.lower())
        self.assertIn("medium/strong primary does not drive the cycle", self.base)
        self.assertIn("the cheap pdca-orchestrator it dispatches", self.base)
        self.assertIn("does not classify semantically, does not replan", self.base)

    # --- host-profile binding + tier labels (no model:) -------------------

    def test_published_assets_have_tier_labels_not_model(self):
        for path in PUBLISHED_ASSETS:
            with self.subTest(path=path.name):
                self.assertIn(path.stem, ROLE_TIER)
                raw = read(path)
                self.assertNotRegex(raw, r"(?m)^\s*#\s*model:")
                self.assertRegex(
                    raw, rf"(?m)^# tier: {ROLE_TIER[path.stem]}\s*$"
                )

    def test_host_requirements_bind_models_via_profile_not_markdown(self):
        self.assertNotIn("uncomment and fill in model:", self.host)
        self.assertIn("host profile", self.host)
        self.assertIn("never a model-id field in a role markdown", self.host)
        # Fallback limited by actual host permissions; denials never bypassed.
        self.assertIn("must never be bypassed", self.host)

    # --- user-go boundary + authority invocation -------------------------

    def _assert_planner_plan_disk_paragraph(self, path: Path) -> None:
        para = self._scoped(
            path,
            "11. Take into account",
            "## Boundaries",
        )
        self._assert_patterns(para, f"pdca-planner plan-disk {path}", [
            r"(?i)normal mode",
            r"(?i)user approves|user's approval",
            r"(?i)autonomous mode",
            r"(?i)no question|no questions",
            r"(?i)no waiting",
            r"(?i)gate-1|gate 1",
        ])

    def test_planner_plan_disk_paragraph_scopes_user_approval_to_normal_mode(self):
        # The planner sub-brief's "plan goes to disk" paragraph must scope the user
        # approval to the normal mode and state the autonomous no-approval/no-question path.
        with self.subTest(path=str(ASSET_BRIEFS[0])):
            self._assert_planner_plan_disk_paragraph(ASSET_BRIEFS[0])

    def test_plan_authority_invocation_unambiguous(self):
        # The driver forwards the request/evidence; the planner authors the single
        # PLAN; the executor writes. No "every primary" authority wording.
        entry = norm(between(self.base_raw, "## Entry: one PLAN decides the form", "### Forms"))
        workspace = norm(between(self.base_raw, "## Workspace and durable status", "## Budgets"))
        self.assertTrue(entry, "entry section not found")
        self.assertIn("The driver does not classify and does not plan", entry)
        self.assertIn("hands the task to the configured pdca-planner once", entry)
        self.assertIn("The driver does not classify and does not plan", self.base)
        self.assertIn("Every write is by pdca-executor", workspace)
        self.assertNotIn("every primary", entry + workspace)

    def test_cycle_quickref_marks_approval_normal_mode_only(self):
        cycle = norm(between(self.base_raw, "Cycle: `PLAN", "Progress is recorded"))
        self.assertTrue(cycle, "cycle quickref line not found")
        self.assertIn("normal mode: the user reads and approves the plan", cycle)
        # Autonomous mode has no approval pause at all.
        self.assertIn("no pauses and no questions", self.orchestrator_section)


class TwoPathContractTest(unittest.TestCase):
    """Normal vs autonomous path contract.

    Scoped to the base operative sections (control modes, roles) and the shipped
    runner asset.  Rule-presence only: reads Markdown text and never executes a
    model or the subagent tool, so it proves the wording, not behavior.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_raw = read(BASE_SKILL)
        cls.control = norm(
            between(cls.base_raw, "## Control modes and the campaign owner", "## Lens")
        )
        cls.host = norm(
            between(cls.base_raw, "## Roles and host requirements",
                    "## Control modes and the campaign owner")
        )
        cls.runner = norm(read(RUNNER_ASSET))

    def test_skill_names_both_paths_normal_drives_autonomous_dispatches(self):
        # Normal: the cheap primary drives the cycle; autonomous: it delegates to
        # pdca-orchestrator instead of driving it itself.
        self.assertIn("a flat cheap primary drives", self.control)
        self.assertIn("the cheap primary delegates to the existing cheap pdca-orchestrator",
                      self.control)
        self.assertIn("cycle-control", self.runner)
        self.assertIn("campaign-control", self.runner)

    def test_autonomous_path_carries_cycle_brief_and_compact_summary(self):
        # A dispatch goes in; a compact summary of at most 8 lines comes out.
        self.assertIn("compact summary (≤8 lines)", self.runner)
        self.assertIn("durable summary", self.control)
        self.assertIn("subagent allowlist", self.host)

    def test_flat_primary_fallback_when_orchestrator_unavailable(self):
        # Agent absent / nested delegation forbidden or too shallow -> flat primary.
        self.assertIn("fall back to the flat cheap primary", self.host)
        self.assertIn("nested delegation", self.host)
        self.assertIn("pdca-orchestrator is unavailable", self.host)
        self.assertIn("delegation forbidden", self.host)

    def test_setup_allowlist_includes_pdca_orchestrator(self):
        self.assertIn("pdca-orchestrator", self.host)
        self.assertIn("allow nested delegation so the runner may delegate", self.host)
        self.assertIn("A runner that drives a child cycle needs the same allowlist", self.host)


class ApprovalGateAndFallbackGuardTest(unittest.TestCase):
    """Negative guards: the normal-mode approval gate and the no-silent-bypass fallback.

    Rule-presence only.  These read Markdown text and never execute a model.
    Each guard pins a *short tokens* phrase whose removal (or whose flip in the
    opposite section) makes the assertion fail, so the guard is negative in
    direction: deleting the approval clause, requiring an approval in autonomous
    mode, or dropping the "not a silent run" clause turns a test red.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_raw = read(BASE_SKILL)
        cls.base = norm(cls.base_raw)
        cls.gate1 = norm(between(cls.base_raw, "1. **PLAN → DO**", "2. **DO → CHECK**"))
        cls.state_machine = norm(
            between(cls.base_raw, "## State machine and counters", "### Phase progress mirror")
        )
        cls.control = norm(
            between(cls.base_raw, "## Control modes and the campaign owner", "## Lens")
        )
        cls.approval = norm(between(cls.base_raw, "## Normal-mode approval", "## References"))
        cls.host = norm(
            between(cls.base_raw, "## Roles and host requirements",
                    "## Control modes and the campaign owner")
        )

    # --- approval gate: mandatory in normal mode, absent in autonomous ------

    def test_normal_mode_requires_explicit_approval_before_do(self):
        # Normal path: DO is gated on an explicit user approval of the plan.
        # Removing the clause from gate 1 or the approval section breaks this test.
        self.assertIn("the user's approval", self.gate1)
        self.assertIn("normal mode", self.gate1)
        self.assertIn("that approval is the only start signal", self.approval)
        # The state-machine cycle line still names the normal-mode plan approval.
        self.assertIn("normal mode: the user reads and approves the plan", self.state_machine)

    def test_autonomous_mode_has_no_approval_and_no_pause(self):
        # Autonomous path: no approval, no pause. If autonomous began
        # requiring an approval, the negated clauses would disappear.
        self.assertIn("no pauses and no questions", self.control)
        self.assertIn("has no approval slots and no plan-approval gate", self.approval)
        self.assertNotIn("explicit go", self.control)
        self.assertNotIn("approval is required", self.control)

    def test_gate1_excludes_autonomous_from_the_approval_requirement(self):
        # The gate-1 approval requirement must explicitly carve out autonomous mode.
        self.assertIn("in normal mode, the user's approval", self.gate1)
        self.assertIn("autonomous → route through planner/escalate and STOP", self.gate1)

    # --- fallback: explicit marking, never a silent bypass ----------------

    def test_flat_primary_fallback_is_explicit_and_noticed(self):
        # Falling back = the flat cheap primary drives AND the host records it
        # (`Notice:`), never silently.
        self.assertIn("fall back to the flat cheap primary", self.host)
        self.assertIn("a flat cheap primary drives", self.control)
        self.assertIn("fallback", self.control)
        self.assertIn("Notice:", self.control)

    def test_no_silent_run_without_a_required_role(self):
        # An unavailable required role is a resource blocker: no substitute and no
        # silent execution without the role. Dropping that clause turns this test red.
        self.assertIn("resource blocker", self.host)
        self.assertIn("never a silent run without the role", self.host)
        self.assertIn("must never be bypassed", self.host)
        self.assertIn("Notice:", self.host)
        self.assertNotRegex(self.host, r"(?i)run silently without")
        self.assertNotIn("without the role is acceptable", self.host)


class CrossArtifactLabelGuardTest(unittest.TestCase):
    """Task 3 guards: diagram label sources + scenario matrix.

    Rule-presence only.  These read JSON/text; they never execute a model, the
    real PDCA cycle, or a production state machine, and therefore do not prove
    runnable behavior.  Behavioral validation is the independent A–I review.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.gen = read(GEN_PDCA_PATH)
        cls.scenarios = read(SCENARIOS_PATH)

    def test_gen_pdca_labels_revision_scoped(self):
        for token in ("CHECK(r)", "n+1", "r+1", "repeat"):
            self.assertIn(token, self.gen, f"gen_pdca.py missing {token!r}")
        # Stale labels (the old revision-agnostic wording) must not come back.
        for stale in ("3rd iteration", "same defect ×2", "different — ×3"):
            self.assertNotIn(stale, self.gen, f"gen_pdca.py stale {stale!r}")

    def test_gen_pdca_preserves_replan_and_do_plan_edges(self):
        # No topology redesign: the CHECK → PLAN and DO → PLAN returns remain.
        self.assertIn("wrong plan", self.gen)
        self.assertIn("new precondition/blocker", self.gen)

    # --- scenario matrix --------------------------------------------------

    def test_scenarios_matrix_covers_a_to_j(self):
        # B is deliberately split into B1 (additive prerequisite) and B2 (actual
        # replacement); every other case keeps its single-letter heading. H–J are
        # the cheap-only / security-report / escalation-decision cases.
        for letter in "ACDEFGHIJ":
            self.assertIn(f"## {letter}.", self.scenarios,
                          f"scenarios.md missing case {letter}")
        self.assertIn("## B1.", self.scenarios, "scenarios.md missing case B1")
        self.assertIn("## B2.", self.scenarios, "scenarios.md missing case B2")
        for column in ("Input", "Required outcome", "Operative sources"):
            self.assertIn(column, self.scenarios)

    def test_scenarios_matrix_covers_autonomous_delegation_and_fallback(self):
        # D5: the autonomous-delegation (K) and flat-primary-fallback (L) cases.
        for letter in "KL":
            self.assertIn(f"## {letter}.", self.scenarios,
                          f"scenarios.md missing case {letter}")

    def test_scenarios_matrix_is_labeled_not_claiming_execution(self):
        # The matrix is for independent reasoning; it must not claim that any
        # agent/model actually executed the scenarios.
        self.assertIn("not proof", self.scenarios)
        self.assertIn("ever ran", self.scenarios)


class FinalFixGuardTest(unittest.TestCase):
    """Final fix wave (review findings F2-F7 + the narrow discovered completions).

    Rule-presence only: reads Markdown/JSON text; never executes a model, the real
    PDCA cycle or a production state machine, and therefore proves no behavior.

    After the overlay split a retained rule is read where it canonically lives:
    the unit/status/defect rules in `../pdca/references/act.md`, the counter and
    escalation rules in `../pdca/SKILL.md`, and the "one approved PLAN" session
    rule in the coder overlay's `references/check.md`.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)
        cls.base_raw = read(BASE_SKILL)
        cls.base = norm(cls.base_raw)
        cls.base_act_raw = read(BASE_ACT)
        cls.base_act = norm(cls.base_act_raw)
        cls.base_plan_raw = read(BASE_PLAN)
        cls.gate2 = norm(between(cls.base_raw, "2. **DO → CHECK**", "3. **CHECK → ACT**"))
        cls.gate3 = norm(between(cls.base_raw, "3. **CHECK → ACT**", "4. **ACT → EXIT**"))
        cls.status_file = norm(between(cls.base_act_raw, "## Status file",
                                       "## Message for the next session"))
        cls.unit_states = norm(between(cls.base_act_raw, "**Unit states**",
                                       "**Content — a brief handoff"))
        cls.recovery = norm(
            between(cls.base_raw, "## Recovery", "## Escalation (`pdca-escalate`)")
        )
        cls.escalation = norm(
            between(cls.base_raw, "## Escalation (`pdca-escalate`)",
                    "## Generic operating constraints")
        )
        cls.candidate = norm(between(cls.base_raw, "### DO → PLAN candidate",
                                     "## Transition gates"))
        cls.check_streams = norm(
            between(read(CODER_SKILL), "## Code-specific check deltas",
                    "## Code-specific do/act deltas")
        ) + " " + norm(between(cls.skill_raw, "## .NET check deltas", "## .NET do/act deltas"))
        cls.keep_check = norm(
            between(read(CODER_CHECK), "## Keep CHECK within one approved PLAN",
                    "## Parallel CHECK streams")
        )
        cls.planner_en = norm(read(ASSET_BRIEFS[0]))
        cls.coder_en = norm(read(ASSET_BRIEFS[1]))
        cls.check_en = norm(read(ASSET_BRIEFS[2]))
        cls.scout_en = norm(read(ASSET_AGENTS / "pdca-scout.md"))
        cls.scenarios = read(SCENARIOS_PATH)

    # --- F4: additive prerequisite != replacement -------------------------

    def test_additive_prerequisite_is_not_a_replacement(self):
        self.assertIn("additive prerequisite adds a new active unit", self.unit_states)
        self.assertIn("not superseded, no mapping", self.unit_states)

    def test_additive_keeps_original_active_criteria_unchanged_no_mapping(self):
        self.assertIn("the original stays active", self.unit_states)
        self.assertIn("criteria and remainder unchanged", self.unit_states)
        self.assertIn("not superseded, no mapping", self.unit_states)

    def test_actual_replacement_requires_mapping_and_carries_criteria(self):
        self.assertIn("actual scope replacement", self.unit_states)
        self.assertIn("replacements are tracked active", self.unit_states)
        self.assertIn(
            "carry all original criteria and residual work", self.unit_states
        )

    def test_candidate_analysis_never_completes_d(self):
        self.assertIn("candidate analysis", self.candidate)
        self.assertIn("never completes", self.candidate)

    def test_planner_and_coder_briefs_distinguish_additive_from_replacement(self):
        self.assertIn("additive", self.planner_en)
        self.assertIn("additive", self.coder_en)

    def test_scenarios_split_b_into_additive_and_replacement(self):
        self.assertIn("B1", self.scenarios)
        self.assertIn("B2", self.scenarios)
        # "Additive" is capitalized in the table/heading; case-insensitive compare.
        self.assertIn("additive", self.scenarios.lower())

    # --- F3: gate 2 "closed" single definition ----------------------------

    def test_gate2_closed_means_active_units_and_streams(self):
        self.assertIn("every active, non-superseded unit is done", self.unit_states)
        self.assertIn("superseded never counts as done", self.unit_states)
        # The code side adds its streams under the same rule.
        self.assertIn("a code unit/stream is done only under the same rule",
                      norm(read(CODER_SKILL)))

    def test_gate2_replacement_chain_resolves_to_active_done_covering_criteria(self):
        self.assertIn(
            "replacement chain must resolve to active done units covering the preserved criteria",
            self.unit_states,
        )

    def test_gate2_rejects_missing_mapping_replacement_orphan_circular_self(self):
        for phrase in (
            "missing mapping",
            "mapping/replacement",
            "orphan",
            "circular/self mapping",
        ):
            self.assertIn(phrase, self.unit_states)
        self.assertIn("pending blocked replacement", self.unit_states)
        self.assertIn("gate 2 rejected", self.unit_states)

    def test_aggregate_d_completion_derives_single_definition(self):
        self.assertIn(
            "The aggregate D: closes when every active, non-superseded unit is done",
            self.unit_states,
        )

    # --- F6: durable state + defect history -------------------------------

    def test_status_schema_has_mandatory_durable_state_fields(self):
        for field in ("Current cycle N", "Plan revision r", "Attempt n", "Defect history"):
            self.assertIn(field, self.status_file)

    def test_defect_history_fields_are_explicit(self):
        for field in (
            "defect key",
            "observed revisions/attempts",
            "applied fix count",
            "evidence/log pointers",
            "last recurrence",
            "escalation outcome",
        ):
            self.assertIn(field, self.status_file)

    def test_check_failure_fix_loopback_records_kind_and_fix_count(self):
        self.assertIn("defect key and applied fix count", self.status_file)

    def test_recovery_loads_r_n_units_and_defect_history(self):
        self.assertIn("defect history", self.recovery)
        self.assertIn("revision r", self.recovery)
        self.assertIn("attempt n/3", self.recovery)

    def test_coder_briefs_mandate_durable_state_and_defect_history(self):
        self.assertIn("defect history", self.coder_en)
        self.assertIn("Plan revision r", self.coder_en)

    def test_check_brief_carries_r_n_and_defect_history_as_history_only(self):
        self.assertIn("defect history", self.check_en)
        self.assertIn("revision r", self.check_en)
        self.assertIn("not evidence for the current CHECK", self.check_en)
        self.assertIn("current full aggregated report", self.check_en)

    def test_scout_brief_can_report_status_snapshot_and_defect_history(self):
        self.assertIn("defect history", self.scout_en)

    # --- narrow discovered completions ------------------------------------

    def test_security_failed_check_counts_as_failed_check_of_revision(self):
        self.assertIn("failed CHECK of the current revision", self.check_streams)
        self.assertIn("triggered security failure", self.check_streams)
        # The ordinary, shared counters are stated in §Escalation; the code overlay
        # adds the security rule (ordinary finding = ordinary failed stream, only a
        # hard trade-off escalates).
        self.assertIn(
            "Every failed CHECK of the current revision counts", self.escalation
        )
        self.assertIn(
            "ordinary security finding is an ordinary failed stream", norm(read(CODER_SKILL))
        )
        self.assertIn(
            "only a hard security trade-off escalates immediately",
            norm(read(DOTNET_CHECK)),
        )

    def test_exhausted_revision_no_fourth_attempt_even_after_escalate(self):
        self.assertIn(
            "An exhausted revision gets no 4th attempt even after escalation",
            self.escalation,
        )

    def test_continue_only_via_genuinely_revised_remediation_plan(self):
        self.assertIn("genuinely revised remediation plan", self.escalation)
        self.assertIn("rename/reword", self.escalation)
        self.assertIn("session reset", self.escalation)
        self.assertIn("cannot manufacture a revision", self.escalation)

    def test_missing_required_report_is_regathered_not_project_defect(self):
        self.assertIn("missing required report", self.escalation)
        self.assertIn("re-gathered", self.escalation)

    def test_escalation_decision_routed_by_orchestrator_when_not_exhausted(self):
        # Decision, not a recommendation: escalate decides, the cheap driver
        # only routes (no semantic re-selection).
        self.assertIn("The decision routes; the driver does not re-decide", self.escalation)
        self.assertIn("carries it out solely by routing", self.escalation)
        self.assertIn("implementation under the current plan", self.escalation)
        self.assertIn("pdca-executor", self.escalation)
        self.assertNotIn("recommendation", self.escalation)

    def test_autonomous_stop_conditional_not_after_every_escalate(self):
        self.assertIn("If escalation yields no actionable revised plan — STOP", self.escalation)
        self.assertNotIn("stopped automatically", self.escalation)
        self.assertIn("no pauses and no questions", self.base)

    # --- F5: session/task_id hygiene independence -------------------------

    def test_session_task_id_reset_does_not_reset_r_n_or_defect_history(self):
        # A new CHECK session / lost task_id never resets the durable counters.
        self.assertIn("reset task_id", self.keep_check.lower())
        self.assertIn("never resets r, n or the defect history", self.keep_check)
        self.assertIn("they live in the status file", self.keep_check)

    def test_unchanged_plan_spans_criteria_design_actions_dependencies(self):
        self.assertIn(
            "Unchanged PLAN means criteria, design decision, DO tasks/actions and dependencies are all unchanged",
            self.keep_check,
        )
        self.assertIn(
            "not the same iteration number, and not unchanged criteria/design while the actions changed",
            self.keep_check,
        )

    # --- F2/F7: no dedicated primary plan; effective-tier wording --------

    def test_no_dedicated_primary_plan_required(self):
        # No dedicated primary plan author: the driver only routes, the planner
        # owns the single PLAN (initial and any revision).
        self.assertIn("The driver does not classify and does not plan", self.base)
        self.assertIn("There is no cheap semantic classifier", self.base)
        self.assertIn("hands the task to the configured pdca-planner once", self.base)
        self.assertIn("does not classify semantically, does not replan", self.base)

    def test_build_is_default_shorthand_for_cheap_primary(self):
        # The driver is the effective-cheap tier of the host profile, never a
        # claim that any primary drives the cycle.
        self.assertIn("by effective tier, not by agent name", self.base)
        self.assertIn("effective host-profile tier is cheap", self.base)
        self.assertNotIn("any primary", self.base)

    def test_scenarios_have_no_nonexistent_escalation_security_fail_link(self):
        self.assertNotIn("§Escalation (security fail)", self.scenarios)
        self.assertNotIn("§Escalation (security-fail)", self.scenarios)


class AuditGateBoundaryTest(unittest.TestCase):
    """#238 guards: the PASS gate is BINDING/APPLICABLE, extra audit rows are diagnostic.

    Rule-presence only (reads Markdown text; never executes a model), so it proves
    the wording, not the behavior.  The .NET overlay keeps the frozen-manifest and
    disposition contract in `references/plan.md` and the completeness gate in
    `references/check.md`; the behavioral pressure scenarios live in
    ``tests/scenarios.md`` (A238–H238) and must not be reported as executed from here.
    """

    MANIFEST_ENTRY = "required_rows"

    @classmethod
    def setUpClass(cls) -> None:
        cls.plan_raw = read(DOTNET_PLAN)
        cls.plan = norm(cls.plan_raw)
        cls.check_raw = read(DOTNET_CHECK)
        cls.check = norm(cls.check_raw)
        cls.frozen = norm(
            between(cls.plan_raw, "### Frozen evidence manifest",
                    "### Mechanical evidence pipeline")
        ) + " " + norm(
            between(cls.plan_raw, "### Binding/applicability disposition (append-only)",
                    "### Contract revision")
        )
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)

    def test_gate_replaced_with_binding_applicable(self):
        # The gate line may wrap in the raw Markdown; compare normalised text.
        self.assertIn("No PASS while any BINDING/APPLICABLE", self.frozen)

    def test_old_absolute_gate_is_gone(self):
        # The old absolute prohibition must not survive anywhere in the contract.
        self.assertNotIn(
            "No PASS while any `%s` entry is `open`" % self.MANIFEST_ENTRY,
            self.plan_raw + self.check_raw + self.skill_raw,
        )

    def test_append_only_disposition_section_present(self):
        self.assertIn("Binding/applicability disposition (append-only)", self.plan_raw)
        self.assertIn("diagnostic_nonbinding", self.plan_raw)
        self.assertIn("never rewritten", self.plan_raw)
        self.assertIn("excluded from the set of binding acceptance blockers", self.frozen)

    def test_exclusion_is_not_a_loophole(self):
        self.assertIn("not a loophole", self.frozen)
        self.assertIn("stays binding", self.frozen)
        self.assertIn("fail/re-gather/STOP route", self.frozen)
        self.assertIn("source-copy mismatch", self.frozen)

    def test_plan_may_not_invent_audit_hard_gates(self):
        # The PLAN-side rule (in the overlay) and its classification path (CHECK).
        self.assertIn("diagnostic note", self.skill)
        self.assertIn("PLAN does not invent audit hard gates", self.skill)
        self.assertIn("diagnostic notes", self.check)

    def test_completeness_gate_is_binding_qualified(self):
        gate = norm(between(
            self.check_raw,
            "## CHECK completeness gate",
            "## Optional-null/default smell",
        ))
        self.assertTrue(gate, "CHECK completeness gate section not found")
        self.assertIn("binding/applicable", gate.lower())
        self.assertNotIn("any open row forbids PASS", gate)

    def test_reviewer_evidence_pack_present(self):
        # #235 (E07): the changed registry full bodies are staged inside the
        # allowed roots, with a source-side receipt — not a diffstat-only pack.
        pack = norm(between(
            self.plan_raw,
            "## Reviewer evidence pack",
            "## Evidence helper discipline",
        ))
        self.assertTrue(pack, "reviewer evidence pack section not found")
        for token in (
            "stages the full bodies",
            "copy, not a move",
            "source identity",
            "content equality",
            "Roslyn resolution runs in that source-side gather",
            "row-level result/reason",
            "evidence open/blocked",
            "not a proof of execution-time",
        ):
            with self.subTest(token=token):
                self.assertIn(token, pack)

    def test_execution_policy_and_journal_present(self):
        # #235 (E10): unit unlimited, integration boundary-only, mandatory capture.
        section = norm(between(
            read(DOTNET_ACT),
            "## Execution journal and the unit/integration policy",
            "### DO report: test evidence",
        ))
        self.assertTrue(section, "execution journal section not found")
        for token in (
            "not on the number of report entries",
            "not a unit-vs-integration criterion",
            "no separate universal numeric cap",
            "projected from that journal",
            "omits a started execution is rejected",
            "failed-to-start",
            "never invented",
            "blocked/unresolved",
        ):
            with self.subTest(token=token):
                self.assertIn(token, section)

    def test_act_cleanup_receipt_present(self):
        # #235 (g/l): the terminal-closure cleanup is gated by a machine-checkable
        # receipt; premature cleanup is rejected and the manifest is immutable.
        section = norm(between(
            read(DOTNET_ACT),
            "## ACT cleanup receipt",
            "## Status-file additions",
        ))
        self.assertTrue(section, "ACT cleanup receipt section not found")
        for token in (
            "machine-checkable receipt",
            "premature cleanup",
            "prior hashes",
            "frozen manifest is not rewritten",
            "planned lifecycle",
        ):
            with self.subTest(token=token):
                self.assertIn(token, section)

    def test_validator_exposes_the_new_subcommands(self):
        script = read(SKILL_DIR / "scripts/validate_inner_loop.py")
        for mode in ("journal", "project", "cleanup", "archived"):
            self.assertIn('"%s"' % mode, script, "validator missing mode %r" % mode)
        self.assertIn("--journal", script)
        self.assertIn("--cleanup", script)


if __name__ == "__main__":
    unittest.main()
