"""Static contract guards for the universal domain-neutral `pdca` skill.

These tests read the *runtime surface* as text and assert the retained,
domain-neutral PDCA rules are present in the operative sections (state machine,
counters, the phase progress mirror, transition gates, generic phase contracts, normal /
autonomous modes, durable status, recovery, escalation, evidence-over-assertion,
generic operating constraints).  They validate the skill *implementation*; they
are not an instruction that end users must write code or tests.

The runtime surface is exactly:

* ``opencode/pdca/SKILL.md``
* ``opencode/pdca/assets/agents/*.md``
* ``opencode/pdca/assets/diagram/*``
* optionally the four host agents ``<host>/config/agents/pdca-{planner,executor,check,escalate}.md``
  (the RUNNER is the shared host agent ``<host>/config/agents/pdca-orchestrator.md``, not scanned
  here); these live in the separate ``opencode-config`` repo and are hidden behind
  ``OPENCODE_CONFIG_REPO``

The ``tests/`` directory itself is deliberately **not** scanned.

The last class is a forbidden-token guard: it scans the runtime surface for the
domain/stack tokens and asserts zero occurrences, and that no runtime file
carries a ``model:`` field.

Run:
    python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]

SKILL_PATH = SKILL_DIR / "SKILL.md"
ASSET_AGENTS = SKILL_DIR / "assets/agents"
DIAGRAM = SKILL_DIR / "assets/diagram"

# Host config (agents/profiles/AGENTS.md/skills-keep) lives in the `opencode-config` repo,
# not in this one. Point at it with OPENCODE_CONFIG_REPO to enable host-parity checks;
# they skip by default.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"

# The runner is host-facing routing glue: it must name the family's variants
# (`pdca-coder`/`pdca-dotnet`) and the stack they cover. It is exempt from the
# domain/stack token scan; the exemption is pinned to exactly this file.
RUNNER_ASSET = SKILL_DIR / "assets/agents/pdca-orchestrator.md"
SCAN_EXEMPT = frozenset((RUNNER_ASSET,))

# Word-boundary (where applicable) domain/stack tokens that must never appear
# in the universal runtime surface.
FORBIDDEN_WORDS = (
    "coding",
    "code",
    "dotnet",
    "python",
    "roslyn",
    "build",
    "lint",
    "tdd",
    "coverage",
    "xml",
    "analyzer",
    "solid",
    "benchmark",
    "perf",
    "worktree",
    "debug",
    "regression",
    "docfx",
    "pdca-coder",
    "pdca-dotnet",
    "pdca-security-auditor",
)
# Tokens whose punctuation makes a word boundary awkward; matched literally.
FORBIDDEN_LITERALS = (".net", "c#")


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
            keys[m.group(1)] = m.group(2).strip().strip('"')
    return keys


def runtime_files() -> list:
    files = [SKILL_PATH]
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


def scan_forbidden() -> list:
    hits = []
    for path in runtime_files():
        try:
            text = read(path)
        except OSError:
            continue
        for token in FORBIDDEN_WORDS:
            if boundary_regex(token).search(text):
                hits.append((str(path), token))
        low = text.lower()
        for token in FORBIDDEN_LITERALS:
            if token in low:
                hits.append((str(path), token))
    return hits


class ContractConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)
        cls.fm = parse_frontmatter(frontmatter_block(cls.skill_raw))
        cls.counters = norm(between(cls.skill_raw, "## State machine", "### Phase progress mirror"))
        cls.mirror = norm(between(cls.skill_raw, "### Phase progress mirror", "### DO → PLAN candidate"))
        cls.gates = norm(between(cls.skill_raw, "### Transition gates", "## Phase contracts"))
        cls.gate3 = norm(between(cls.skill_raw, "3. **CHECK → ACT**", "4. **ACT → EXIT**"))
        cls.status = norm(
            between(cls.skill_raw, "## Durable status", "## Evidence over assertion")
        )

    # --- frontmatter ------------------------------------------------------

    def test_frontmatter_has_exactly_name_and_description(self):
        self.assertEqual({"name", "description", "metadata", "disable-model-invocation"}, set(self.fm))

    def test_name_is_pdca(self):
        self.assertEqual("pdca", self.fm.get("name"))

    def test_no_model_binding_in_frontmatter(self):
        self.assertNotRegex(frontmatter_block(self.skill_raw), r"(?m)^\s*model\s*:")

    def test_description_is_nonempty_and_domain_neutral(self):
        desc = self.fm.get("description", "")
        self.assertTrue(desc.strip())
        lowered = desc.lower()
        for token in FORBIDDEN_WORDS + FORBIDDEN_LITERALS:
            self.assertNotIn(token, lowered, "description leaks %r" % token)

    # --- required sections ------------------------------------------------

    def test_required_sections_present(self):
        raw = self.skill_raw
        for anchor in (
            "## State machine",
            "### Phase progress mirror (status file only)",
            "### Transition gates",
            "## Phase contracts",
            "## Normal and autonomous modes",
            "## Durable status",
            "## Evidence over assertion",
            "## Recovery after compaction and drift",
            "## Escalation",
            "## Generic operating constraints",
        ):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, raw)

    # --- phase contracts --------------------------------------------------

    def test_phase_contracts_are_present(self):
        for token in (
            "**PLAN** returns",
            "**DO** reports",
            "**CHECK** is independent",
            "**ACT** finalizes only a result",
            "**STOP** is a **separate terminal outcome**",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.skill_raw)

    # --- counters N / r / n -----------------------------------------------

    def test_three_counters_described(self):
        self.assertIn("Three counters, do not mix them", self.counters)
        self.assertIn("cycle number", self.counters)
        self.assertIn("Plan revision r", self.counters)
        self.assertIn("iteration n/3", self.counters)
        self.assertIn("new revision resets n to 1", self.counters)

    # --- transition gates -------------------------------------------------

    def test_gates_encode_no_fourth_rule(self):
        self.assertIn("no 4th", self.skill.lower())
        self.assertIn("no 4th", norm(between(
            self.skill_raw, "## Escalation", "## Generic operating constraints")).lower())

    def test_gate_check_to_act_requires_all_criteria_met(self):
        self.assertIn("all criteria met on actual evidence", self.gate3)
        self.assertIn("no criterion is unmet/unverified", self.gate3)

    def test_stop_is_a_separate_terminal_outcome_not_act_success(self):
        self.assertIn("separate terminal path", self.gates)
        self.assertIn("without a false PASS or ACT-success", self.gates)
        stop = norm(between(self.skill_raw, "**STOP** is a **separate terminal outcome**", "## Normal and autonomous modes"))
        self.assertIn("not the ACT phase and not a green gate", stop)

    # --- the status file is the only progress mirror ----------------------

    def test_status_file_is_the_only_progress_mirror(self):
        self.assertIn("Progress lives only in the cycle status file", self.mirror)
        self.assertIn("no separate todo or sidebar mirror", self.mirror)
        self.assertIn("a second mirror only creates divergence", self.mirror)
        self.assertIn(".pdca/status/<task>-<N>.md", self.skill)
        self.assertIn(".pdca/status/<task>-<N>.md", self.status)

    # --- durable status counters/history ----------------------------------

    def test_durable_status_carries_counters_and_history(self):
        # The mandatory durable-state fields live in the cycle-status-file content.
        section = norm(between(
            self.skill_raw, "### Cycle status file", "### Message for the next session"
        ))
        for token in ("Current cycle N", "Plan revision r", "Attempt n", "Defect history"):
            with self.subTest(token=token):
                self.assertIn(token, section)


class ForbiddenTokenGuardTest(unittest.TestCase):
    """Zero matches for all domain/stack tokens anywhere on the runtime surface."""

    def test_only_the_runner_is_exempt_from_the_token_scan(self):
        self.assertEqual({RUNNER_ASSET}, set(SCAN_EXEMPT))
        self.assertTrue(RUNNER_ASSET.is_file(), "runner asset missing")
        scanned = set(runtime_files())
        self.assertNotIn(RUNNER_ASSET, scanned)
        self.assertEqual(set(ASSET_AGENTS.glob("*.md")) - scanned, {RUNNER_ASSET})

    def test_no_forbidden_token_in_runtime_surface(self):
        hits = scan_forbidden()
        self.assertEqual([], hits, "forbidden tokens found: %r" % hits)

    def test_no_model_field_in_any_runtime_file(self):
        offenders = []
        for path in runtime_files():
            try:
                text = read(path)
            except OSError:
                continue
            if re.search(r"(?m)^\s*model\s*:", text):
                offenders.append(str(path))
        self.assertEqual([], offenders, "model: found in %r" % offenders)

    def test_detector_catches_a_rejected_sample(self):
        self.assertTrue(boundary_regex("roslyn").search("uses Roslyn here"))
        self.assertTrue(boundary_regex("code").search("write code"))
        self.assertFalse(boundary_regex("code").search("encoding"))
        self.assertFalse(boundary_regex("xml").search("xmlns"))

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_scan_is_limited_to_expected_files(self):
        # Host briefs are the .NET-flavoured mirrors of the pdca-dotnet assets and
        # are deliberately out of scope: the guard protects the universal surface
        # shipped by this skill (SKILL.md, its assets, the diagram sources).
        scanned = {str(p) for p in runtime_files()}
        self.assertIn(str(SKILL_PATH), scanned)
        self.assertNotIn(str(CONFIG / "agents/pdca-planner.md"), scanned)
        self.assertNotIn("tests", str(SKILL_PATH))
        for p in scanned:
            self.assertNotIn("/tests/", p)


class RuntimeContractEvidenceTest(unittest.TestCase):
    """K3/K9 evidence: the runtime SKILL.md text literally encodes the
    phase progress mirror rule, the normal-mode start signal, and the four
    generic operating constraints.  Clear, named, file-text assertions only."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(SKILL_PATH)
        cls.skill = norm(cls.raw)

    # --- K3: phase progress mirror is the status file ---------------------

    def test_phase_progress_mirror_is_the_status_file_only(self):
        self.assertIn("Progress lives only in the cycle status file", self.skill)
        self.assertIn("no separate todo or sidebar mirror", self.skill)
        self.assertIn("a second mirror only creates divergence", self.skill)
        self.assertIn("the status file wins", self.skill)

    def test_phase_progress_mirror_same_turn_and_reconcile(self):
        self.assertIn("Same turn", self.skill)
        self.assertIn("the executor updates the status file in the same turn", self.skill)
        self.assertIn("Reconcile each turn", self.skill)
        self.assertIn("never from memory", self.skill)
        self.assertIn("nothing changed", self.skill)

    # --- K3: normal-mode explicit start signal ---------------------------

    def test_normal_mode_requires_plan_approval(self):
        self.assertIn(
            "Normal mode requires the user's approval of the plan after it is on disk",
            self.skill,
        )
        self.assertIn("the only start signal", self.skill)
        self.assertIn("no keyword is required", self.skill)
        self.assertIn("non-committal reply is not an approval", self.skill)

    # --- K9: four generic operating constraints --------------------------

    def test_constraint_authority_and_permission_boundary(self):
        self.assertIn("Authority and permission boundaries", self.skill)
        self.assertIn("Never bypass, escalate around or spoof a permission", self.skill)
        self.assertIn("a denied action is denied, not worked around", self.skill)

    def test_constraint_untrusted_content_and_injection_distinction(self):
        self.assertIn("Trusted instructions vs untrusted content", self.skill)
        self.assertIn("untrusted and is the lowest priority", self.skill)
        self.assertIn("Injection defense", self.skill)

    def test_constraint_credential_confidentiality(self):
        self.assertIn("Credential confidentiality", self.skill)
        self.assertIn(
            "Never print, copy or upload the contents of secret material",
            self.skill,
        )
        self.assertIn("never the value", self.skill)

    def test_constraint_user_authorization_and_no_permission_bypass(self):
        self.assertIn(
            "User authorization for consequential or external actions",
            self.skill,
        )
        self.assertIn("Autonomous mode does not manufacture approval", self.skill)
        self.assertIn("Never bypass permissions to make progress", self.skill)


class AuditGateBoundaryTest(unittest.TestCase):
    """#238 guards: the PASS gate is BINDING/APPLICABLE, extra audit rows are diagnostic.

    Rule-presence only (reads Markdown text; never executes a model), so it proves
    the wording, not the behavior.
    """

    MANIFEST_ENTRY = "required"

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)

    def test_gate_replaced_with_binding_applicable(self):
        # The gate line may wrap in the raw Markdown; compare normalised text.
        self.assertIn("No PASS while any BINDING/APPLICABLE", self.skill)

    def test_old_absolute_gate_is_gone(self):
        self.assertNotIn(
            "No PASS while any `%s` entry is `open`" % self.MANIFEST_ENTRY,
            self.skill_raw,
        )

    def test_append_only_disposition_section_present(self):
        self.assertIn("Binding/applicability disposition (append-only)", self.skill_raw)
        self.assertIn("diagnostic_nonbinding", self.skill_raw)
        self.assertIn("never rewritten", self.skill_raw)
        self.assertIn("excluded from the set of binding acceptance blockers", self.skill)

    def test_exclusion_is_not_a_loophole(self):
        self.assertIn("not a loophole", self.skill)
        self.assertIn("stays binding", self.skill)
        self.assertIn("fail/re-gather/STOP route", self.skill)
        self.assertIn("source-copy mismatch", self.skill)

    def test_plan_may_not_invent_audit_hard_gates(self):
        self.assertIn("diagnostic notes", self.skill)


class HelperStagingPrerequisiteTest(unittest.TestCase):
    """§Skill workspace: helper staging is an explicit mechanical first step.

    Producer: `pdca-executor`; when: before the first helper command, including the
    PLAN brief validation; source: the selected installed package's `scripts/`;
    destination: the project `.pdca/scripts/` as byte-identical copies. A missing
    original is a resource blocker — no generated substitute, no run from the
    installed skill directory.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = norm(read(SKILL_PATH))
        cls.executor = norm(read(ASSET_AGENTS / "pdca-executor.md"))

    def test_staging_names_producer_when_source_and_destination(self):
        self.assertIn("Staging is the first mechanical step", self.skill)
        self.assertIn("pdca-executor stages the helpers", self.skill)
        self.assertIn("first helper command of a cycle", self.skill)
        self.assertIn("PLAN brief validation", self.skill)
        self.assertIn("selected installed package", self.skill)
        self.assertIn("into .pdca/scripts/", self.skill)
        self.assertIn("byte-identical copies", self.skill)

    def test_staging_is_a_declared_prerequisite_not_an_unplanned_edit(self):
        self.assertIn("explicitly allowed brief/PLAN prerequisite", self.skill)
        self.assertIn("not an unplanned edit outside the plan", self.skill)
        self.assertIn("no separate P: task", self.skill)
        self.assertIn("only helpers actually shipped and required", self.skill)

    def test_missing_source_is_a_blocker_not_a_substitute(self):
        self.assertIn("resource blocker", self.skill)
        self.assertIn("never generates a substitute helper", self.skill)
        self.assertIn("never runs a helper command from the installed skill directory", self.skill)

    def test_executor_asset_carries_the_same_duty(self):
        self.assertIn("Helper staging is an allowed prerequisite", self.executor)
        self.assertIn("resource blocker", self.executor)
        self.assertIn("never run a helper from the installed skill directory", self.executor)


if __name__ == "__main__":
    unittest.main()
