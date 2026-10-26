"""Static contract guards for the base `pdca` skill (entry + base cycle).

Two things changed with the family architecture and are encoded here:

* the **base** ``skills/pdca/SKILL.md`` is now the single public entry *and* the base
  cycle (entry/one-PLAN form decision, overlays, roles/host requirements, control
  modes and the campaign owner, lens/probe/increment, the step boundary, the state
  machine and counters, gates 1–5, the generic phase contracts, claims and veto,
  evidence over assertion, workspace/durable status, budgets, strategic revision,
  recovery, escalation, constraints, red flags, normal-mode approval);
* the **phase detail** moved to ``references/{plan,check,act}.md`` — plan fields and
  the command contract, the evidence matrix and the veto, the ACT/status template.

The runtime surface stays the SKILL plus its role assets and the diagram sources; the
``tests/`` directory itself is deliberately not scanned. The last class is a
domain/stack-token guard, re-scoped: the base **names** the overlays (it has to — it
selects them) but must carry **no** domain obligation, no concrete toolchain command
and no domain-specific process gate.

Everything here is rule-presence/absence over the text; no test executes a model or a
real cycle.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
FAMILY = SKILL_DIR.parent
BASE = SKILL_DIR / "SKILL.md"
REFERENCES = SKILL_DIR / "references"
ASSET_AGENTS = SKILL_DIR / "assets/opencode-agents"
DIAGRAM = SKILL_DIR / "assets/diagram"

# Host config lives in the `opencode-config` repo, not in this one; host-parity checks
# skip unless OPENCODE_CONFIG_REPO is set. The live host is **not** migrated to the
# family architecture yet, so every host-facing assertion in this suite is a skip.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"
SKIP_HOST_NOT_MIGRATED = (
    "live host is not migrated to the family architecture (it still ships the variant-routing "
    "orchestrator and the full-copy role briefs); host parity is re-enabled after deployment"
)

# The runner is the one asset that names the whole family and the optional domain
# specialists: it *dispatches*, it is not part of the neutral contract. The exemption is
# pinned to exactly this file.
RUNNER_ASSET = ASSET_AGENTS / "pdca-orchestrator.md"
SCAN_EXEMPT = frozenset((RUNNER_ASSET,))

# Concrete toolchain/tool tokens: a domain-neutral base never needs one of these, in any
# section. "coverage"/"build"/"test" are *not* here — the base legitimately speaks about
# the cost of a verifier in generic words; the obligation itself is what must not appear.
FORBIDDEN_WORDS = (
    "python",
    "pytest",
    "cargo",
    "npm",
    "nuget",
    "msbuild",
    "coverlet",
    "stryker",
    "docfx",
    "lint",
    "tdd",
    "xml",
    "analyzer",
    "solid",
    "benchmark",
    "perf",
    "worktree",
    "debug",
    "regression",
    "pdca-security-auditor",
    "dotnet-",
)
# Tokens whose punctuation makes a word boundary awkward; matched literally.
# `plan-lint` left this list when `plan_lint.py` became a family-wide gate (§Machine
# projection in `references/plan.md`): it is a projection check, not a stack linter.
FORBIDDEN_LITERALS = ("asp.net", "validate_inner_loop",
                      ".csproj", ".slnx", ".sln", "dotnet test", "dotnet build")

# The base must *name* the overlays and the forms to select them. Those mentions are
# confined to the contexts below; anywhere else a stack word is an obligation that does
# not belong in a domain-neutral contract. Each exception is a named section with the
# reason it is legitimate.
CONFINED_TOKENS = ("code", "coding", ".net", "c#", "roslyn", "dotnet", "pdca-coder", "pdca-dotnet")
CONFINED_CONTEXTS = frozenset(
    (
        "PREAMBLE",                      # the frontmatter description advertises the entry
        "Entry: one PLAN decides the form",   # the decision table names the chosen contract
        "Forms",                         # "auxiliary code does not reclassify the goal"
        "Overlays",                      # the overlays are defined and inherited here
        "Red flags (self-check)",        # "I applied the coder/.NET overlay to a whole campaign…"
        "Plan fields (gate 1)",          # the declared overlay value is "none/coder/coder+.NET"
        "Form and first step (cycle start)",  # the planner asset's own overlay decision
    )
)

# Size limits: hard ceiling for every contract/overlay, hard ceiling for a reference file,
# and the compact-core ceiling that holds the base near its design target.
SKILL_HARD_LIMIT = 50 * 1024
REFERENCE_HARD_LIMIT = 45 * 1024
# The design target for the base is ≤ 35 KiB; it now sits just under 40 KiB. This is a
# *growth* ceiling, not the contract target: it is deliberately not raised in passing.
BASE_COMPACT_CEILING = 40 * 1024

REQUIRED_SECTIONS = (
    "## Entry: one PLAN decides the form",
    "### Forms",
    "## Roles and host requirements",
    "## Control modes and the campaign owner",
    "## Lens: probe, increment and step",
    "## State machine and counters",
    "### Phase progress mirror",
    "### DO → PLAN candidate",
    "## Transition gates",
    "## Phase contracts (generic)",
    "### Claims and veto",
    "## Evidence over assertion",
    "## Workspace and durable status",
    "## Effort and time policy",
    "## Overlays",
    "## Strategic revision",
    "## Recovery",
    "## Escalation (`pdca-escalate`)",
    "## Generic operating constraints",
    "## Red flags (self-check)",
    "## Normal-mode approval",
    "## References",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip()


def between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i:j] if j >= 0 else text[i:]


def section_of(text: str, position: int) -> str:
    """Heading a character offset belongs to (``PREAMBLE`` before the first ``##``)."""
    context = "PREAMBLE"
    for match in re.finditer(r"(?m)^(#{2,3})\s+(.*)$", text):
        if match.start() > position:
            break
        context = match.group(2).replace("`", "").strip()
    return context


def frontmatter_block(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end >= 0 else ""


def parse_frontmatter(block: str) -> dict:
    keys: dict = {}
    for line in block.splitlines():
        if not line.strip() or line.startswith(" ") or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
        if match:
            keys[match.group(1)] = match.group(2).strip().strip('"')
    return keys


def runtime_files() -> list:
    files = [BASE]
    files += sorted(p for p in REFERENCES.glob("*.md") if p.is_file())
    if ASSET_AGENTS.is_dir():
        files += sorted(
            p for p in ASSET_AGENTS.glob("*.md")
            if p.is_file() and p not in SCAN_EXEMPT
        )
    if DIAGRAM.is_dir():
        files += sorted(p for p in DIAGRAM.iterdir() if p.is_file())
    return files


def boundary_regex(token: str) -> "re.Pattern":
    return re.compile(r"(?<!\w)%s(?!\w)" % re.escape(token), re.IGNORECASE)


# `plan_lint.py` and its `PLAN-LINT` receipt row are family-wide artifacts of the command
# projection, not a stack-linter obligation. They are masked before the word scan so the
# `lint` guard keeps its meaning for prose ("run a linter", "dotnet format --verify").
FAMILY_ARTIFACTS = re.compile(r"plan[-_]lint", re.IGNORECASE)


def scan_forbidden() -> list:
    hits = []
    for path in runtime_files():
        try:
            text = read(path)
        except OSError:
            continue
        scanned = FAMILY_ARTIFACTS.sub("plan-projection", text)
        for token in FORBIDDEN_WORDS:
            if boundary_regex(token).search(scanned):
                hits.append((str(path), token))
        low = text.lower()
        for token in FORBIDDEN_LITERALS:
            if token in low:
                hits.append((str(path), token))
    return hits


def confined_hits() -> list:
    """Domain mentions of the base/references that sit outside an overlay-naming context."""
    hits = []
    assets = [p for p in sorted(ASSET_AGENTS.glob("*.md")) if p not in SCAN_EXEMPT]
    for path in [BASE] + sorted(REFERENCES.glob("*.md")) + assets:
        text = read(path)
        for token in CONFINED_TOKENS:
            for match in boundary_regex(token).finditer(text):
                context = section_of(text, match.start())
                if context in CONFINED_CONTEXTS:
                    continue
                line = " ".join(text[max(0, match.start() - 60):match.start() + 60].split())
                hits.append((str(path), token, context, line))
    return hits


def markdown_links(text: str) -> list:
    """Every path-shaped reference the contract points at (`references/x.md`, `../y/SKILL.md`)."""
    return re.findall(r"`((?:\.\./|references/)[\w./-]+\.md)`", text)


class PhraseAssertions(unittest.TestCase):
    """Compare Markdown phrases without emphasis or line-wrap noise."""

    def assertPhrase(self, needle: str, haystack: str, msg: str | None = None) -> None:
        super().assertIn(norm(needle), norm(haystack), msg)


class ContractConsistencyTest(PhraseAssertions):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(BASE)
        cls.skill = norm(cls.raw)
        cls.fm = parse_frontmatter(frontmatter_block(cls.raw))
        cls.counters = norm(between(cls.raw, "## State machine and counters", "### Phase progress mirror"))
        cls.mirror = norm(between(cls.raw, "### Phase progress mirror", "### DO → PLAN candidate"))
        cls.gates = norm(between(cls.raw, "## Transition gates", "## Phase contracts"))
        cls.gate1 = norm(between(cls.raw, "1. **PLAN → DO**", "2. **DO → CHECK**"))
        cls.gate3 = norm(between(cls.raw, "3. **CHECK → ACT**", "4. **ACT → EXIT**"))
        cls.gate4 = norm(between(cls.raw, "4. **ACT → EXIT**", "5. **STOP finalization**"))
        cls.gate5 = norm(between(cls.raw, "5. **STOP finalization**", "**You cannot skip CHECK"))
        cls.entry = norm(between(cls.raw, "## Entry: one PLAN decides the form", "## Roles and host requirements"))
        cls.forms = norm(between(cls.raw, "### Forms", "## Roles and host requirements"))
        cls.lens = norm(between(cls.raw, "## Lens: probe, increment and step", "## State machine and counters"))
        cls.claims = norm(between(cls.raw, "### Claims and veto", "## Evidence over assertion"))
        cls.status = norm(between(cls.raw, "## Workspace and durable status", "## Budgets"))
        cls.overlays = norm(between(cls.raw, "## Overlays", "## Strategic revision"))
        cls.approval = norm(between(cls.raw, "## Normal-mode approval", "## References"))
        cls.plan_ref = read(REFERENCES / "plan.md")
        cls.check_ref = read(REFERENCES / "check.md")
        cls.act_ref = read(REFERENCES / "act.md")

    # --- frontmatter ------------------------------------------------------

    def test_frontmatter_has_exactly_name_and_description(self):
        # The base is the advertised entry: no manual-only flags, no metadata block.
        self.assertEqual({"name", "description"}, set(self.fm))

    def test_name_is_pdca(self):
        self.assertEqual("pdca", self.fm.get("name"))

    def test_base_is_model_invocable(self):
        block = frontmatter_block(self.raw)
        self.assertNotRegex(block, r"(?m)^disable-model-invocation\s*:")
        self.assertNotRegex(block, r"(?m)^\s*autoinvoke\s*:")
        self.assertNotIn("opencode/autoinvoke", block)

    def test_no_model_binding_in_frontmatter(self):
        self.assertNotRegex(frontmatter_block(self.raw), r"(?m)^\s*model\s*:")

    def test_description_is_nonempty_and_advertises_the_form_decision(self):
        desc = self.fm.get("description", "")
        self.assertTrue(desc.strip())
        low = desc.lower()
        self.assertPhrase("single entry", low)
        for form in ("ordinary cycle", "incremental", "collection"):
            with self.subTest(form=form):
                self.assertPhrase(form, low)
        for token in ("overlay", "probe", "veto"):
            with self.subTest(token=token):
                self.assertPhrase(token, low)

    # --- required sections ------------------------------------------------

    def test_required_sections_present(self):
        for anchor in REQUIRED_SECTIONS:
            with self.subTest(anchor=anchor):
                self.assertPhrase(anchor, self.raw)

    def test_section_order_matches_the_cycle(self):
        # The contract reads top-down as the cycle runs; a section that drifts out of order
        # is a sign the file was merged without restructuring.
        order = [
            "## Entry: one PLAN decides the form",
            "## Roles and host requirements",
            "## Control modes and the campaign owner",
            "## Lens: probe, increment and step",
            "## State machine and counters",
            "## Transition gates",
            "## Phase contracts (generic)",
            "## Evidence over assertion",
            "## Workspace and durable status",
            "## Recovery",
            "## Escalation (`pdca-escalate`)",
            "## Red flags (self-check)",
            "## Normal-mode approval",
        ]
        positions = [self.raw.index(anchor) for anchor in order]
        self.assertEqual(sorted(positions), positions, "sections are out of cycle order")

    # --- entry: one PLAN decides the form ---------------------------------

    def test_driver_does_not_classify(self):
        self.assertPhrase("The driver does not classify and does not plan", self.entry)
        self.assertPhrase("There is no cheap semantic classifier", self.entry)
        self.assertPhrase("no second PLAN on the same content", self.entry)
        self.assertPhrase("A confirmation or restatement of the same plan is not a new PLAN", self.entry)

    def test_one_planner_call_decides_form_overlay_and_step(self):
        self.assertPhrase("hands the task to the configured pdca-planner once", self.entry)
        for token in (
            "the form of execution",
            "the overlay",
            "the nearest useful step",
            "the carrying claims",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.entry)

    def test_explicit_contract_is_a_constraint(self):
        # Naming `pdca` is family entry, not a form constraint; a named form/overlay is.
        self.assertPhrase("Naming `pdca` is entry to this family, not a form", self.entry)
        self.assertPhrase("is a constraint", self.entry)
        self.assertPhrase("does not silently re-route", self.entry)
        for name in ("`pdca-coder`", "`pdca-dotnet`", "`pdca-collection`", "`pdca-incremental`"):
            with self.subTest(name=name):
                self.assertPhrase(name, self.raw)

    def test_entry_passes_the_plan_by_reference(self):
        self.assertPhrase(
            "the driver loads exactly one execution contract and passes the plan to it by reference",
            self.entry,
        )

    def test_form_discriminators(self):
        for token in (
            "the method and the volume are sufficiently known and bounded",
            "are data dependency, not uncertainty",
            "the method is unknown or the volume is unknown",
            "Mere output→input chaining and a known algorithm with a fixed volume are not incremental",
            "a list of independent goals (not an internal split of one goal)",
            "a single-lane collection is the normal case, not a degradation",
            "a bounded probe is allowed and the form is refined from what it returns",
            "An explicit user preference of form is respected as a constraint",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.forms)

    def test_auxiliary_code_does_not_reclassify_a_goal(self):
        self.assertPhrase("Auxiliary code does not reclassify the goal", self.skill)
        self.assertPhrase("does not turn the whole goal into a coding task", self.skill)

    # --- roles and host requirements --------------------------------------

    def test_roles_table_and_cheap_orchestration(self):
        self.assertPhrase("Orchestration is cheap-only", self.skill)
        self.assertPhrase("by effective tier, not by agent name", self.skill)
        self.assertPhrase("does not drive the cycle", self.skill)
        for role in ("pdca-scout", "pdca-planner", "pdca-executor", "pdca-check",
                     "pdca-escalate", "pdca-orchestrator"):
            with self.subTest(role=role):
                self.assertPhrase(role, self.skill)

    def test_tier_labels_and_no_model_ids(self):
        self.assertPhrase("Each asset carries only a `# tier:` label", self.skill)
        self.assertPhrase("Model bindings come from the **host profile's `agent` block**", self.skill)
        self.assertPhrase("never a model-id field in a role markdown", self.skill)

    def test_missing_role_is_a_resource_blocker_not_a_silent_run(self):
        self.assertPhrase("resource blocker", self.skill)
        self.assertPhrase("never a silent run", self.skill)

    # --- control modes and the campaign owner -----------------------------

    def test_two_control_modes(self):
        self.assertPhrase("Normal mode keeps the existing control", self.skill)
        self.assertPhrase("the user approves each step/cycle plan", self.skill)
        self.assertPhrase("Autonomous mode has no pauses and no questions", self.skill)

    def test_campaign_owner_is_a_context_not_a_new_role(self):
        self.assertPhrase("campaign-control is a **context** of that role, not a new role", self.skill)
        self.assertPhrase("Two contexts, never mixed", self.skill)
        self.assertPhrase("A separate cycle-control is **not** spawned per campaign step", self.skill)
        self.assertPhrase("starts the next step **only on the planner's decision**", self.skill)

    # --- lens, probe, increment, step boundary ---------------------------

    def test_probe_increment_and_step(self):
        for token in (
            "**Probe** — a bounded computation/measurement/action inside one step",
            "A tool call does not start a new PLAN and does not owe a CHECK",
            "**Increment** — a completed opening of the chosen part/question",
            "Several cheap related probes may form **one** increment",
            "the whole project may not be inflated into",
            "is a **knowledge increment**",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.lens)

    def test_step_boundary_is_one_planner_call(self):
        self.assertPhrase("**Step boundary — one planner call**", self.lens)
        self.assertPhrase("Total planner calls: successful path", self.lens)
        self.assertPhrase("1 + number of steps", self.lens)
        self.assertPhrase("A **separate final check does not count as a", self.lens)
        self.assertPhrase("Separate DECIDE → brief → STOP turns on the same content are a repeated PLAN", self.lens)

    def test_step_boundary_pre_sets_the_stop_condition(self):
        self.assertPhrase("final-check brief with a pre-set", self.lens)
        self.assertPhrase("completion condition", self.lens)
        self.assertPhrase("without a new planner call", self.lens)
        self.assertPhrase("routing a pre-approved decision, not its own verdict", self.lens)
        # The worked example pins the arithmetic: initial PLAN + one boundary decision.
        self.assertPhrase("two calls", self.lens)

    def test_step_boundary_keeps_the_step_identity(self):
        self.assertPhrase("Revision updates the working plan and result under the **same step identity**", self.lens)
        self.assertPhrase("the step number does not grow without", self.lens)
        self.assertPhrase("the independent CHECK is never rewritten to `met`", self.lens)
        self.assertPhrase("A new step resets no counter or history", self.lens)

    # --- counters N / r / n / rv ------------------------------------------

    def test_four_counters_described(self):
        self.assertPhrase("Three counters, do not mix them", self.counters)
        self.assertPhrase("cycle number", self.counters)
        self.assertPhrase("Plan revision r", self.counters)
        self.assertPhrase("iteration n/3", self.counters)
        self.assertPhrase("Contract revision rv", self.counters)
        self.assertPhrase("a new revision resets n to 1", self.counters)
        self.assertPhrase("There is no global n/3 on every loop-back", self.counters)

    def test_cycle_number_grows_only_in_act(self):
        self.assertPhrase("grows **only in ACT**", self.counters)
        self.assertPhrase("Loop-backs never change", self.counters)

    def test_revision_is_only_a_genuine_revised_plan(self):
        self.assertPhrase("grows only when pdca-planner **actually issued a revised", self.counters)
        self.assertPhrase("A rejected candidate or a clarification with the plan unchanged is **not** a revision", self.counters)
        self.assertPhrase("No revision, step or measurement total caps the task", self.counters)

    def test_no_fourth_attempt(self):
        self.assertPhrase("After the **third failed CHECK of the same revision**", self.counters)
        self.assertPhrase("pdca-escalate** before a fourth", self.counters)
        self.assertPhrase("no 4th", self.skill.lower())

    # --- transition gates -------------------------------------------------

    def test_gate_1_requires_the_mandatory_fields(self):
        for token in (
            "only if the planner's answer contains **all mandatory fields**",
            "goal/expected result",
            "declared **form** and overlay",
            "constraints",
            "assumptions",
            "acceptance criteria **each with",
            "a verification method",
            "**carrying claims with IDs**",
            "risks and stop conditions",
            "effort estimate",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.gate1)
        self.assertPhrase("references/plan.md", self.gate1)
        self.assertPhrase("the user's approval", self.gate1)

    def test_gate_1_requires_form_rationale_and_verification_choice(self):
        for token in (
            "form rationale",
            "justified method + bound",
            "the missing knowledge that decides the next action",
            "verification choice",
            "a bespoke checker also needs its reason and bound",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.gate1)

    def test_gate_1_fields_are_carried_by_reference_on_resume_or_replan(self):
        phase = norm(between(self.raw, "## Phase contracts (generic)", "### Claims and veto"))
        self.assertPhrase("gate-1 fields above (definitions there)", phase)
        self.assertPhrase("still-valid rationale and verification choice are carried by reference",
                          phase)
        self.assertPhrase("not re-authored/re-classified", phase)

    def test_red_flag_points_to_the_full_gate_1_list(self):
        section = norm(between(self.raw, "## Red flags (self-check)", "## Normal-mode approval"))
        self.assertPhrase("the full Gate 1 list in §Transition gates", section)
        self.assertPhrase("mandatory plan field", section)

    def test_planner_cap_treats_bounded_continuations_as_same_pending_plan(self):
        for token in (
            "successful path 1 + number of steps",
            "bounded same-pending-PLAN continuations",
            "accounting entries, not a quota",
            "no hidden exempt calls",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.lens)

    def test_gate_2_blocker_is_not_done(self):
        gate2 = norm(between(self.raw, "2. **DO → CHECK**", "3. **CHECK → ACT**"))
        self.assertPhrase("`D:` units are `done` with recorded", gate2)
        self.assertPhrase("A blocker report is **not** `done`", gate2)
        self.assertPhrase("a rejected candidate resumes the original `D`", gate2)

    def test_gate_3_requires_all_criteria_and_the_veto(self):
        self.assertPhrase("all criteria `met` on **actual", self.gate3)
        self.assertPhrase("evidence", self.gate3)
        self.assertPhrase("no carrying claim is `confirmed`/`unverified` against it", self.gate3)
        self.assertPhrase("A separate final CHECK of the whole goal is required for", self.gate3)

    def test_gate_4_is_bookkeeping_only(self):
        self.assertPhrase("ACT is bookkeeping only", self.gate4)
        self.assertPhrase("no product/test/checked artifact changed after the accepted CHECK snapshot", self.gate4)

    def test_stop_is_a_separate_terminal_outcome_not_act_success(self):
        self.assertPhrase("a **separate terminal path**, not a green gate", self.gate5)
        self.assertPhrase("without a false PASS or ACT-success", self.gate5)
        self.assertPhrase("without bypassing the no-4th rule", self.gate5)
        stop = norm(between(self.raw, "**STOP** is a separate terminal outcome", "### Claims and veto"))
        self.assertPhrase("not the ACT phase and not a green gate", stop)

    def test_check_and_act_cannot_be_skipped(self):
        self.assertPhrase("You cannot skip CHECK. You cannot close the cycle without ACT.", self.skill)

    # --- unit states and additive prerequisites ---------------------------

    def test_unit_states_and_additive_prerequisite(self):
        self.assertPhrase("pending | running | blocked | done | superseded", self.skill)
        self.assertPhrase("the original unit stays active (`blocked`), its", self.skill)
        self.assertPhrase("not `superseded`, no mapping", self.skill)
        self.assertPhrase("requires an explicit", self.skill)
        self.assertPhrase("mapping carrying all original criteria and residual work", self.skill)

    # --- claims and veto --------------------------------------------------

    def test_carrying_claims_are_separate_from_rubric_axes(self):
        self.assertPhrase("The PLAN lists **carrying claims**", self.claims)
        self.assertPhrase("separately from quality-rubric axes", self.claims)
        self.assertPhrase("demoting a carrying claim is a plan revision by `pdca-planner`", self.claims)

    def test_veto_blocks_pass_at_any_rubric_score(self):
        self.assertPhrase("forbids PASS and final `done` at", self.claims)
        self.assertPhrase("any rubric score", self.claims)
        self.assertPhrase("blocks a STOP with `done`", self.claims)

    def test_veto_has_exactly_three_removal_paths(self):
        self.assertPhrase("Removing the block has exactly three paths", self.claims)
        for token in ("fix and re-check", "objective refutation with evidence reproduced by a non-author",
                      "narrowing of the result inside the original goal"):
            with self.subTest(path=token):
                self.assertPhrase(token, self.claims)
        self.assertPhrase("Moving the finding to \"next step\" does **not** remove the block", self.claims)
        self.assertPhrase("The model may not weaken the original goal", self.claims)

    def test_check_reference_carries_the_veto(self):
        ref = norm(self.check_ref)
        self.assertPhrase("Carrying claims and the veto", ref)
        self.assertPhrase("forbids PASS and final `done` at", ref)
        self.assertPhrase("A finding that touches a mandatory criterion but is bound to no ID counts as", ref)
        self.assertPhrase("`unverified`", ref)

    # --- evidence over assertion -----------------------------------------

    def test_evidence_chain_is_rerun_observe_judge(self):
        section = norm(between(self.raw, "## Evidence over assertion", "## Workspace and durable status"))
        self.assertPhrase("The cycle closes only on fresh evidence, never an assertion", section)
        self.assertPhrase("The driver does not inspect evidence itself", section)
        for role in ("**Re-run — `pdca-executor`", "**Observe — `pdca-scout`", "**Judge — `pdca-check`"):
            with self.subTest(role=role):
                self.assertPhrase(role, section)
        self.assertPhrase("A report ≠ a result", section)
        for marker in ('"should work"', '"probably"', '"looks correct"', '"it\'s obvious"'):
            with self.subTest(marker=marker):
                self.assertPhrase(marker, section)

    # --- the status file is the only progress mirror ----------------------

    def test_status_file_is_the_only_progress_mirror(self):
        self.assertPhrase("Progress is recorded in one place", self.counters)
        self.assertPhrase("the cycle status file", self.counters)
        self.assertPhrase("There is no separate todo or sidebar mirror", self.counters)
        self.assertPhrase(".pdca/status/<task>-<N>.md", self.status)
        self.assertPhrase("the status file wins", self.mirror)

    def test_phase_progress_mirror_same_turn_and_reconcile(self):
        self.assertPhrase("Same turn", self.mirror)
        self.assertPhrase("the executor updates the status file in the same turn", self.mirror)
        self.assertPhrase("never batched", self.mirror)
        self.assertPhrase("Reconcile each turn", self.mirror)
        self.assertPhrase("State Rot", self.mirror)
        self.assertPhrase("never from memory", self.mirror)

    def test_workspace_root_and_single_writer(self):
        self.assertPhrase("Everything this skill writes lives under **one** project-local root", self.status)
        self.assertPhrase("`.pdca/`", self.status)
        self.assertPhrase("**Every write is by `pdca-executor`**", self.status)
        self.assertPhrase("planner, check, escalate and the driver have no file", self.status)
        self.assertPhrase("Append-only log; history is never silently deleted", self.status)

    def test_status_lifetime_and_no_storage_limitation(self):
        self.assertPhrase("Lifetime:", self.status)
        self.assertPhrase("never deleted", self.status)
        self.assertPhrase("No permitted persistent storage", self.status)
        self.assertPhrase("Timestamps", self.status)
        self.assertPhrase("never written by hand", self.status)

    def test_durable_status_carries_counters_and_history(self):
        # The mandatory durable-state fields live in the ACT reference's status-file content.
        section = norm(between(self.act_ref, "## Status file", "## Message for the next session"))
        for token in ("Current cycle N", "Plan revision r", "Attempt n", "Defect history"):
            with self.subTest(token=token):
                self.assertPhrase(token, section)
        self.assertPhrase("append-only, one line per event", section)
        self.assertPhrase("<UTC time> | <phase> | revision r | iteration n/3 | <event> | <evidence pointer>", section)

    # --- budgets, overlays, strategic revision ---------------------------

    def test_effort_policy_forbids_autonomous_cutoffs(self):
        section = norm(between(self.raw, "## Effort and time policy", "## Overlays"))
        self.assertPhrase("No autonomous cutoff", section)
        self.assertPhrase("estimate is not a stop condition", section)
        self.assertPhrase("Work ends on an accepted result", section)
        self.assertPhrase("Failed candidates or incomplete evidence are not blockers", section)
        self.assertPhrase("plan approval is not that opt-in", section)
        self.assertPhrase("persists as the same cutoff across normal-mode resume/replan", section)
        self.assertPhrase("No-4th and recurrence stay per defect", section)

    def test_overlays_are_differences_not_a_second_cycle(self):
        self.assertPhrase("`pdca-coder` is the generic programming **overlay**", self.overlays)
        self.assertPhrase("`pdca-dotnet` **inherits** coder", self.overlays)
        self.assertPhrase("an overlay contains only the differences from the base", self.overlays)
        self.assertPhrase("without a duplicate PLAN or a second state machine", self.overlays)
        self.assertPhrase("Specialised knowledge is loaded **only for the current step**", self.overlays)
        self.assertPhrase("Overlay inheritance is preserved", self.overlays)

    def test_strategic_revision_is_controlled_re_evaluation(self):
        section = norm(between(self.raw, "## Strategic revision", "## Recovery"))
        self.assertPhrase("controlled re-evaluation on new facts", section)
        self.assertPhrase("not by an unconditional second classification", section)
        self.assertPhrase("resetting counters or history to bypass limits are forbidden", section)

    # --- recovery and escalation -----------------------------------------

    def test_recovery_order_and_campaign_recovery(self):
        section = norm(between(self.raw, "## Recovery", "## Escalation"))
        self.assertPhrase("The status file is the source of truth", section)
        self.assertPhrase("Recovery order:", section)
        self.assertPhrase("Campaign recovery", section)
        self.assertPhrase("Recovered after compaction", section)
        self.assertPhrase("counters and the defect history are not reset", section)

    def test_escalation_triggers_and_routing(self):
        section = norm(between(self.raw, "## Escalation", "## Generic operating constraints"))
        self.assertPhrase("second tier for hard", section)
        self.assertPhrase("same defect", section)
        self.assertPhrase("came back after one fix", section)
        self.assertPhrase("third failed CHECK of the same revision", section)
        self.assertPhrase("The decision routes; the driver does not re-decide", section)
        self.assertPhrase("cannot waive the gates, the no-4th rule, scope, security", section)
        self.assertPhrase("A rename/reword, a session reset or a rejected candidate cannot", section)

    # --- constraints, red flags, approval --------------------------------

    def test_generic_operating_constraints(self):
        section = norm(between(self.raw, "## Generic operating constraints", "## Red flags"))
        for token in (
            "Authority and permission boundaries",
            "Never bypass, escalate around or spoof a permission",
            "a denied action is denied",
            "Trusted instructions vs untrusted content",
            "untrusted and lowest priority",
            "Injection defense",
            "Credential confidentiality",
            "Never print, copy or upload secret material",
            "never the value",
            "User authorization for consequential or external actions",
            "Never bypass permissions",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, section)

    def test_red_flags_are_immediate_stops_with_the_excuse_table(self):
        section = norm(between(self.raw, "## Red flags (self-check)", "## Normal-mode approval"))
        self.assertPhrase("Immediate-stop signals", section)
        self.assertPhrase("stop, name the deviation, return to the", section)
        self.assertPhrase("I edit files (incl. the status file) or run commands myself instead of `pdca-executor`", section)
        self.assertPhrase("I read artefacts/logs/status files myself instead of a `pdca-scout`", section)
        self.assertPhrase("I decide the plan, the form, the overlay or the verdict myself", section)
        self.assertPhrase("I classify the task before the planner's PLAN", section)
        self.assertPhrase("I demand a complete up-front plan", section)
        self.assertPhrase("I let a rubric score or a threshold margin compensate", section)
        self.assertPhrase("Excuses (the model justifies the deviation) → reality", section)

    def test_normal_mode_requires_plan_approval(self):
        self.assertPhrase("that approval is the **only start signal**", self.approval)
        self.assertPhrase("A question, a change request or a non-committal reply is not an approval", self.approval)
        self.assertPhrase("Without approval nothing is created or edited **except the status file**", self.approval)

    def test_durable_approval_protocol(self):
        self.assertPhrase("Durable approval protocol (caller-driven cycles)", self.approval)
        self.assertPhrase("never obtains or assumes approval", self.approval)
        self.assertPhrase("durable **pending approval ref**", self.approval)
        self.assertPhrase("stale plan gets a genuine revision and a", self.approval)
        self.assertPhrase("approval-needed checkpoint", self.approval)
        self.assertPhrase("Autonomous mode has no approval slots and no plan-approval gate", self.approval)

    # --- references: existence, pointers, size ---------------------------

    def test_references_exist_and_are_named(self):
        for name in ("plan.md", "check.md", "act.md"):
            with self.subTest(reference=name):
                self.assertTrue((REFERENCES / name).is_file(), "references/%s missing" % name)
                self.assertPhrase("references/%s" % name, self.raw)

    def test_references_load_at_phase_start(self):
        section = norm(between(self.raw, "## References", "\Z"))
        self.assertPhrase("Phase detail is loaded **at the start of its phase**, not up front", section)
        self.assertPhrase("50 KiB / 2000 lines", section)

    def test_every_contract_path_pointer_resolves(self):
        # A dangling pointer is a rule the reader can never load: walk the whole family.
        problems = []
        for path in sorted(FAMILY.glob("pdca*/SKILL.md")):
            text = read(path)
            for target in markdown_links(text):
                resolved = (path.parent / target).resolve()
                if not resolved.is_file():
                    problems.append("%s -> %s" % (path.relative_to(FAMILY), target))
        self.assertEqual([], problems, "dangling contract pointers: %r" % problems)

    def test_reference_size_limits(self):
        for path in sorted(FAMILY.glob("pdca*/references/*.md")):
            with self.subTest(reference=str(path.relative_to(FAMILY))):
                self.assertLess(path.stat().st_size, REFERENCE_HARD_LIMIT)

    def test_contract_size_limits(self):
        for path in sorted(FAMILY.glob("pdca*/SKILL.md")):
            with self.subTest(contract=str(path.relative_to(FAMILY))):
                self.assertLess(path.stat().st_size, SKILL_HARD_LIMIT, "over the 50 KiB hard limit")

    def test_base_holds_its_compact_core(self):
        # Design target for the base is ≤ 35 KiB; the protocol-complete core now sits just
        # under 40 KiB, so this guard holds the *growth* at that ceiling rather than lowering it.
        size = BASE.stat().st_size
        self.assertLessEqual(size, BASE_COMPACT_CEILING, "base grew past its compact-core ceiling")

    def test_reference_files_are_not_restatements_of_the_base(self):
        # Phase detail was extracted *out* of the base: the two must not carry the same
        # long paragraphs, or the extraction was cosmetic.
        base_paragraphs = _paragraphs(self.raw)
        for path in sorted(REFERENCES.glob("*.md")):
            duplicated = base_paragraphs & _paragraphs(read(path))
            with self.subTest(reference=path.name):
                self.assertEqual(set(), duplicated, "reference restates base paragraphs")


def _paragraphs(text: str, minimum: int = 40) -> set:
    out = set()
    for chunk in re.split(r"\n\s*\n", text):
        flat = " ".join(chunk.split())
        if len(flat) >= minimum:
            out.add(flat)
    return out


class ForbiddenTokenGuardTest(PhraseAssertions):
    """Zero domain/toolchain obligations on the runtime surface; overlay names confined."""

    def test_only_the_runner_is_exempt_from_the_token_scan(self):
        self.assertEqual({RUNNER_ASSET}, set(SCAN_EXEMPT))
        self.assertTrue(RUNNER_ASSET.is_file(), "runner asset missing")
        scanned = set(runtime_files())
        self.assertNotIn(RUNNER_ASSET, scanned)
        self.assertEqual(set(ASSET_AGENTS.glob("*.md")) - scanned, {RUNNER_ASSET})

    def test_no_forbidden_token_in_runtime_surface(self):
        hits = scan_forbidden()
        self.assertEqual([], hits, "forbidden tokens found: %r" % hits)

    def test_domain_mentions_are_confined_to_overlay_naming(self):
        hits = confined_hits()
        self.assertEqual(
            [],
            hits,
            "a domain mention outside an overlay-naming section is an obligation the neutral "
            "base must not carry: %r" % (hits,),
        )

    def test_no_model_field_in_any_runtime_file(self):
        offenders = []
        for path in runtime_files():
            text = read(path)
            if re.search(r"(?m)^\s*model\s*:", text):
                offenders.append(str(path))
        self.assertEqual([], offenders, "model: found in %r" % offenders)

    def test_no_model_id_anywhere_in_the_runtime_surface(self):
        pattern = re.compile(r"(?i)\b(opus|sonnet|haiku|gpt-4|gpt-5|deepseek-|claude-3|gemini-\d)")
        offenders = [str(p) for p in runtime_files() if pattern.search(read(p))]
        self.assertEqual([], offenders, "model id found in %r" % offenders)

    def test_detector_catches_a_rejected_sample(self):
        self.assertTrue(boundary_regex("roslyn").search("uses Roslyn here"))
        self.assertTrue(boundary_regex("code").search("write code"))
        self.assertFalse(boundary_regex("code").search("encoding"))
        self.assertFalse(boundary_regex("xml").search("xmlns"))

    def test_confined_detector_catches_a_domain_obligation(self):
        sample = "# t\n\n## Budgets\n\nThe plan runs `dotnet test` per change.\n"
        self.assertEqual(
            [("Budgets", "dotnet")],
            [(section_of(sample, m.start()), "dotnet")
             for m in boundary_regex("dotnet").finditer(sample)],
        )
        allowed = "# t\n\n## Overlays\n\n`pdca-dotnet` inherits coder.\n"
        self.assertEqual(
            [("Overlays",)],
            [(section_of(allowed, m.start()),)
             for m in boundary_regex("dotnet").finditer(allowed)],
        )

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST_NOT_MIGRATED)
    def test_scan_is_limited_to_expected_files(self):
        scanned = {str(p) for p in runtime_files()}
        self.assertIn(str(BASE), scanned)
        self.assertNotIn(str(CONFIG / "agents/pdca-planner.md"), scanned)
        for path in scanned:
            self.assertNotIn("/tests/", path)


class AuditGateBoundaryTest(PhraseAssertions):
    """#238 guards: the PASS gate is BINDING/APPLICABLE, extra audit rows are diagnostic.

    The rules moved into `references/plan.md` (frozen manifest) with the base keeping the
    pointer. Rule-presence only: it proves the wording, not the behavior.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.plan_raw = read(REFERENCES / "plan.md")
        cls.plan = norm(cls.plan_raw)
        cls.base = norm(read(BASE))

    def test_gate_replaced_with_binding_applicable(self):
        self.assertPhrase("No PASS while any BINDING/APPLICABLE", self.plan)

    def test_old_absolute_gate_is_gone(self):
        self.assertNotIn("No PASS while any `required` entry is `open`", self.plan_raw)
        self.assertNotIn("No PASS while any `required` entry is `open`", read(BASE))

    def test_append_only_disposition_section_present(self):
        self.assertPhrase("Binding/applicability disposition (append-only)", self.plan_raw)
        self.assertPhrase("diagnostic_nonbinding", self.plan_raw)
        self.assertPhrase("never rewritten", self.plan_raw)
        self.assertPhrase("excluded from the set of binding acceptance blockers", self.plan)

    def test_exclusion_is_not_a_loophole(self):
        self.assertPhrase("not a loophole", self.plan)
        self.assertPhrase("stays **binding**", self.plan)
        self.assertPhrase("fail/re-gather/STOP route", self.plan)
        self.assertPhrase("source-copy mismatch", self.plan)

    def test_plan_may_not_invent_audit_hard_gates(self):
        self.assertPhrase("diagnostic notes", self.plan)

    def test_base_keeps_the_veto_pointer(self):
        # The veto detail lives in the CHECK reference; the phase contract must point at it.
        check = norm(between(read(BASE), "**CHECK** is independent", "**ACT** finalizes"))
        self.assertPhrase("Details and the veto: `references/check.md`", check)


class PlanScopeAndVerificationEconomyTest(PhraseAssertions):
    """PLAN selects the approach; DO develops it; verification stays proportionate.

    Rule-presence only: this pins the contract wording, not a model's behaviour.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.plan_raw = read(REFERENCES / "plan.md")
        cls.plan = norm(cls.plan_raw)
        cls.planner = norm(read(ASSET_AGENTS / "pdca-planner.md"))

    def test_form_reason_names_method_and_volume_or_missing_knowledge(self):
        for token in (
            "the method already justified and how the volume is bounded",
            "the missing knowledge that decides the next action",
            "one finished result, one file or a known format is not by itself a known method",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.plan)

    def test_plan_selects_the_approach_and_do_develops_the_deliverable(self):
        for token in (
            "PLAN chooses the approach; DO develops the deliverable",
            "does not pre-write the final artefact or solve every unresolved downstream choice",
            "the first step resolves the leading unknown",
            "later work stays conditional on its result rather than a full speculative backlog",
            "one increment may finish the goal",
            "Do not change to incremental merely to excuse a larger plan",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.plan)

    def test_verification_economy_allows_manual_observation_and_recomputation(self):
        for token in (
            "verification choice",
            "Independent manual observation or a focused recomputation can be sufficient",
            '"verifiable evidence" does not require a new executable checker',
            "why existing means and manual checking of the carrying claims are insufficient",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.plan)

    def test_verification_economy_preserves_genuine_required_gates(self):
        self.assertPhrase(
            "a genuine required test, security or carrying-veto gate is never waived",
            self.plan,
        )

    def test_command_contract_rows_are_conditional_on_an_actual_command(self):
        for token in (
            "conditional on an actual command",
            "does not invent a command line",
            "A plan whose decisive command cannot produce a valid result",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.plan)

    def test_planner_output_carries_form_reason_and_verification_choice(self):
        for token in (
            "Form and overlay with a one-line reason naming the justified method and volume bound",
            "Command contract — only for commands the plan actually freezes",
            "Verification choice",
            "why existing or manual means are insufficient and its bound",
        ):
            with self.subTest(token=token):
                self.assertPhrase(token, self.planner)


class HelperStagingPrerequisiteTest(PhraseAssertions):
    """§Helper staging: an explicit mechanical first step before any helper command.

    Producer: `pdca-executor`; when: before the first helper command; source: the
    selected package's `scripts/`; destination: the project `.pdca/scripts/` as
    byte-identical copies. A missing original is a resource blocker — no generated
    substitute, no run from the installed skill directory.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = read(REFERENCES / "plan.md")
        cls.plan_flat = norm(cls.plan)
        cls.executor = norm(read(ASSET_AGENTS / "pdca-executor.md"))

    def test_staging_section_exists_with_source_destination_and_evidence(self):
        self.assertPhrase("## Helper staging", self.plan)
        for token in (
            "byte-identical copies",
            "stdlib only",
            "into `.pdca/scripts/`",
            "before the first helper",
            "records the source package path",
        ):
            with self.subTest(token=token):
                self.assertPhrase(norm(token), self.plan_flat)

    def test_missing_source_is_a_blocker_not_a_substitute(self):
        self.assertPhrase("is a **resource blocker**", self.plan_flat)
        self.assertPhrase("never generates a substitute", self.plan_flat)
        self.assertPhrase("never runs a helper from the installed skill directory", self.plan_flat)

    def test_project_fork_must_be_declared(self):
        self.assertPhrase("A project fork of", self.plan_flat)
        self.assertPhrase("must be declared", self.plan_flat)

    def test_executor_asset_carries_the_same_duty(self):
        self.assertPhrase("helper", self.executor)
        self.assertPhrase(".pdca/scripts", self.executor)
        self.assertPhrase("installed skill directory", self.executor)


class ManifestGateTest(PhraseAssertions):
    """The evidence index is a gate, not a habit: CHECK reconciles the pinned manifest, and a
    missing one is a re-gather rather than an implementation defect.

    Rule-presence only: this pins the contract wording, not a model's behaviour.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.check = norm(read(REFERENCES / "check.md"))
        cls.check_asset = norm(read(ASSET_AGENTS / "pdca-check.md"))
        cls.plan = norm(read(REFERENCES / "plan.md"))

    def test_check_reference_opens_the_manifest_first(self):
        self.assertPhrase("## Frozen manifest", self.check)
        self.assertPhrase("opens it first", self.check)
        self.assertPhrase("prose tables and the author's summary are not a substitute", self.check)
        self.assertPhrase("missing required report, not an implementation defect", self.check)
        self.assertPhrase("does not grow n/3", self.check)

    def test_check_role_carries_the_same_gate(self):
        self.assertPhrase("Open the pinned manifest.json first", self.check_asset)
        self.assertPhrase("does not grow n/3", self.check_asset)

    def test_brief_carries_the_plan_by_reference(self):
        self.assertPhrase("by reference", self.check_asset)
        self.assertPhrase("a brief that restates the plan tables adds no reach", self.check)

    def test_plan_makes_the_projection_mandatory(self):
        self.assertPhrase("ships no projection is a PLAN defect", self.plan)
        self.assertPhrase("until it exists there is no candidate to check", self.plan)

    def test_plan_requires_the_manifest_before_the_candidate(self):
        self.assertPhrase("no manifest is not reported as a candidate", self.plan)


class CheckObservationGateTest(PhraseAssertions):
    """CHECK is dispatched on a manifest and a non-author observation, not on a reading tour.

    A check that re-reads the whole evidence tree pays for the verdict twice; and for a deliverable
    outside `.pdca/**` it has no legal read at all, which is how a result gets moved out of the path
    the goal names. Rule-presence only: this pins the contract wording, not a model's behaviour.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_skill = read(BASE)
        cls.skill = norm(cls.raw_skill)
        cls.check = norm(read(REFERENCES / "check.md"))
        cls.plan = norm(read(REFERENCES / "plan.md"))
        cls.check_asset_raw = read(ASSET_AGENTS / "pdca-check.md")
        cls.check_asset = norm(cls.check_asset_raw)
        cls.orch = norm(read(ASSET_AGENTS / "pdca-orchestrator.md"))
        cls.check_brief = norm(read(SKILL_DIR / "assets/briefs/check.md"))
        cls.scout_brief = norm(read(SKILL_DIR / "assets/briefs/scout.md"))

    def test_gate_requires_manifest_and_observation_before_check(self):
        gate = norm(between(self.raw_skill, "2. **DO → CHECK**", "3. **CHECK → ACT**"))
        self.assertPhrase("frozen manifest.json exists with a row per required ID", gate)
        self.assertPhrase("observation pack", gate)
        self.assertPhrase("re-gather, not a CHECK round", gate)

    def test_observation_is_mandatory_for_every_check(self):
        self.assertPhrase("required for every CHECK, not only for a probe", self.skill)
        self.assertPhrase("observed / assumed / unverified", self.skill)
        self.assertPhrase("never moved to fit the scope", self.skill)

    def test_check_reads_targeted_and_never_the_product(self):
        self.assertPhrase("Read economy", self.check_asset)
        self.assertPhrase("targeted", self.check_asset)
        self.assertPhrase("never moved into", self.check_asset)
        self.assertPhrase("re-check after a bounded repair judges the delta", self.check_asset)
        self.assertPhrase("observation pack is mandatory for every step and every re-check", self.check)

    def test_check_role_grants_a_scoped_grep(self):
        self.assertRegex(self.check_asset_raw, r'(?m)^  grep:\n    "\.pdca/\*\*": allow$')
        self.assertIn('"*": deny', self.check_asset_raw, "the scoped allow-list stays default-deny")

    def test_orchestrator_has_the_check_dispatch_gate(self):
        self.assertPhrase("CHECK dispatch gate", self.orch)
        self.assertPhrase("observation pack", self.orch)
        self.assertPhrase("names no path outside that scope", self.orch)
        self.assertPhrase("does not grow n/3", self.orch)

    def test_plan_pins_the_manifest_and_the_deliverable_path(self):
        self.assertPhrase("gate-1 field", self.plan)
        self.assertPhrase("observation route", self.plan)
        self.assertPhrase("deliverable keeps the path the goal names", self.plan)
        self.assertPhrase("changed goal", self.plan)

    def test_briefs_carry_the_pack_and_the_read_scope(self):
        self.assertPhrase("observation pack", self.check_brief)
        self.assertPhrase("read scope", self.check_brief)
        self.assertPhrase("is in scope", self.scout_brief)
        self.assertPhrase("the checker cannot read it", self.scout_brief)

    def test_executor_records_the_pack_and_never_moves_the_result(self):
        executor = norm(read(ASSET_AGENTS / "pdca-executor.md"))
        self.assertPhrase("Observation pack and manifest", executor)
        self.assertPhrase("kind: observation", executor)
        self.assertPhrase("is not a cosmetic anchor", executor)


class BriefScopeTest(PhraseAssertions):
    """The brief points at the frozen plan; it does not re-type it.

    A second copy of the criteria in the brief drifts from the status file and, being the document
    the executor is told to obey, wins over it. Only what must be literal stays literal.
    """

    LITERAL = ("footprint", "prohibitions", "capture", "argv")

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = norm(read(BASE))
        cls.do_brief = norm(read(SKILL_DIR / "assets/briefs/do.md"))
        cls.check_brief = norm(read(SKILL_DIR / "assets/briefs/check.md"))
        cls.orch = norm(read(ASSET_AGENTS / "pdca-orchestrator.md"))

    def test_base_sends_the_plan_by_reference(self):
        self.assertPhrase("the plan by reference", self.skill)
        self.assertPhrase("stay in the status file, which the executor and the checker read", self.skill)
        self.assertPhrase("second copy of the plan", self.skill)

    def test_base_names_the_literal_parts(self):
        self.assertPhrase("Only what must be literal travels", self.skill)
        for token in self.LITERAL:
            with self.subTest(token=token):
                self.assertPhrase(token, self.skill)

    def test_do_brief_no_longer_retypes_the_criteria(self):
        self.assertNotIn("criteria rows this DO serves", self.do_brief)
        self.assertPhrase("by reference", self.do_brief)
        self.assertPhrase("literal only", self.do_brief)
        for token in self.LITERAL:
            with self.subTest(token=token):
                self.assertPhrase(token, self.do_brief)

    def test_check_brief_does_not_restate_the_rows(self):
        self.assertNotIn("criteria rows verbatim", self.check_brief)
        self.assertPhrase("by reference", self.check_brief)
        self.assertPhrase("rows live in the status file", self.check_brief)

    def test_orchestrator_calls_the_plan_a_pointer(self):
        self.assertPhrase("The plan itself travels as a pointer", self.orch)
        self.assertPhrase("second copy that drifts from the status file", self.orch)


class CaptureShapeTest(PhraseAssertions):
    """A run leaves three artifacts: the exit status and both streams are evidence, not prose.

    Rule-presence only: this pins the contract wording, not a model's behaviour.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = norm(read(REFERENCES / "plan.md"))
        cls.check = norm(read(REFERENCES / "check.md"))
        cls.coder = norm(read(FAMILY / "pdca-coder/SKILL.md"))
        cls.dotnet = norm(read(FAMILY / "pdca-dotnet/SKILL.md"))
        cls.dotnet_plan = norm(read(FAMILY / "pdca-dotnet/references/plan.md"))

    def test_plan_contract_declares_the_capture(self):
        self.assertPhrase("capture is declared", self.plan)
        self.assertPhrase("<stem>.out, <stem>.err, <stem>.rc", self.plan)
        self.assertPhrase("cannot be told apart from a run that never started", self.plan)

    def test_no_overlay_prescribes_a_merged_stream(self):
        for name, text in (("coder", self.coder), ("dotnet", self.dotnet),
                           ("dotnet/references/plan.md", self.dotnet_plan)):
            with self.subTest(doc=name):
                self.assertNotIn("2>&1 | tee", text, "a merged capture is not evidence")

    def test_coder_overlay_states_the_three_artifacts(self):
        self.assertPhrase("Every run leaves three artifacts, not one log", self.coder)
        self.assertPhrase("cmd > <stem>.out 2> <stem>.err", self.coder)
        self.assertPhrase("read from <stem>.rc", self.coder)

    def test_check_reads_the_artifact_not_the_value_field(self):
        self.assertPhrase("the manifest's value/exit fields point at evidence", self.check)


class BriefTemplateTest(PhraseAssertions):
    """Every dispatch has a filled-to-shape brief; the evidence slots cannot be silently dropped."""

    ROLES = {"scout": "facts wanted", "plan": "form discriminators", "do": "capture",
             "check": "manifest", "act": "Bookkeeping only"}

    def test_every_cycle_role_has_a_small_template(self):
        for role, anchor in self.ROLES.items():
            path = SKILL_DIR / "assets/briefs" / ("%s.md" % role)
            with self.subTest(role=role):
                self.assertTrue(path.is_file(), "missing brief template for %s" % role)
                self.assertLessEqual(path.stat().st_size, 4096, "brief template grew past one screen")
                self.assertPhrase(anchor, norm(read(path)))

    def test_do_template_carries_the_evidence_slots(self):
        text = norm(read(SKILL_DIR / "assets/briefs/do.md"))
        for token in ("<stem>.out", "<stem>.rc", "manifest", "commands.json", "plan_lint"):
            with self.subTest(token=token):
                self.assertPhrase(token, text)

    def test_orchestrator_points_at_the_templates(self):
        agent = norm(read(ASSET_AGENTS / "pdca-orchestrator.md"))
        self.assertPhrase("assets/briefs/", agent)
        self.assertPhrase("missing mandatory slot", agent)


if __name__ == "__main__":
    unittest.main()
