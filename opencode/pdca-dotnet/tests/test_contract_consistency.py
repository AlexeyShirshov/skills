"""Static regression guards for the pdca-dotnet contract consistency task.

These tests read the contract files as *text* and assert that the Task 1 rules
are present in the operative sections (and that contradictory old rules are
gone).  They are rule-presence guards, **not** behavioral proof: they do not
execute a model and do not prove that an agent follows the contract.  Behavioral
scenario review is a separate step.

Run:
    python3 -m unittest discover -s opencode/pdca-dotnet/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_PATH = SKILL_DIR / "SKILL.md"
ASSET_BRIEFS = [
    SKILL_DIR / f"assets/agents/{name}.md"
    for name in ("pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate")
]
# Host config (agents/profiles/AGENTS.md/README) lives in the `opencode-config` repo, not in this
# one. Point at it with OPENCODE_CONFIG_REPO to enable host-parity checks; they skip by default.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_ROOT = HOST_REPO  # host repo root, for its README
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"
SKIP_README = (
    "host README is not EN yet — the checks assert its EN wording and skip until "
    "an EN edition of opencode-config/README.md exists"
)
CONFIG_AGENTS = (CONFIG / "agents") if CONFIG else None
# Host briefs carry the same prefixed ids as the published assets; only the shared
# gatherer/implementer still live in the host as `scout`/`coder`.
CONFIG_BRIEFS = [
    CONFIG_AGENTS / f"{name}.md"
    for name in ("pdca-planner", "coder", "pdca-check", "pdca-escalate")
] if CONFIG_AGENTS else []
# Asset stem -> canonical contract branch, for the shared contract branches.
CANON = {
    "pdca-planner": "planner", "pdca-executor": "coder", "pdca-check": "check",
    "pdca-escalate": "escalate", "pdca-scout": "scout",
    "pdca-security-auditor": "security-auditor",
}
# Task 2: the seven published EN assets and the tier each must carry (no `model:`).
PUBLISHED_ASSETS = [
    SKILL_DIR / f"assets/agents/{name}.md"
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
# Task 3: cross-artifact label sources (host README + diagram source) and the
# non-executable scenario matrix.  These are text/JSON presence guards only.
# The host README differs from this (skills) repo's own README, so it stays gated.
README_PATH = (HOST_ROOT / "README.md") if HOST_ROOT else None
DIAGRAM_DIR = SKILL_DIR / "assets/diagram"
GEN_PDCA_PATH = DIAGRAM_DIR / "gen_pdca.py"
SCENARIOS_PATH = SKILL_DIR / "tests/scenarios.md"
# Host plan document (docs/superpowers/plans lives in the `opencode-config` repo).
PLAN_PATH = (
    HOST_ROOT / "docs/superpowers/plans/2026-10-01-pdca-consistency-plan.md"
) if HOST_ROOT else None


def norm(text: str) -> str:
    """Collapse whitespace (incl. line wraps) and drop backticks/format noise."""
    text = text.replace("`", "").replace("*", "")
    return re.sub(r"\s+", " ", text)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def is_en(path: Path) -> bool:
    """True when the file carries no Cyrillic (language read from the content).

    The contract, the published assets and the host briefs are EN-only, so this
    is no longer a branch selector.  It gates the *host README* checks: that
    README is a Russian-only host artifact today, and the guards below may only
    assert its EN wordings once an EN edition exists (they skip otherwise).
    """
    return not re.search("[\\u0400-\\u04FF]", read(path))


def readme_is_en() -> bool:
    """True when the host README exists and is EN.

    The host README is a Russian-only artifact today, so every guard that
    asserts its wording is gated on this and skips (with a clear reason) until an
    EN edition lands — rather than silently passing against a language it cannot
    read.
    """
    return bool(HOST_AVAILABLE and README_PATH and README_PATH.is_file()) and is_en(README_PATH)


def between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i:j] if j >= 0 else text[i:]


class ContractConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)
        # The counter block is the State machine intro before the progress mirror.
        cls.counters = norm(between(cls.skill_raw, "## State machine", "### Phase progress mirror"))
        cls.mirror = norm(
            between(cls.skill_raw, "### Phase progress mirror", "Transition gates:")
        )
        cls.status_file = norm(
            between(cls.skill_raw, "### Cycle status file", "### Message for the next session")
        )
        cls.gate2 = norm(between(cls.skill_raw, "2. **DO → CHECK**", "3. **CHECK → ACT**"))
        cls.check_streams = norm(
            between(cls.skill_raw, "### Parallel CHECK streams", "Then follows the checklist")
        )
        cls.escalation = norm(
            between(cls.skill_raw, "### Escalation (`pdca-escalate`)", "## PLAN: design checklist")
        )
        cls.autonomous = norm(
            between(cls.skill_raw, "## Autonomous mode", "## Red flags")
        )
        cls.gate1 = norm(between(cls.skill_raw, "1. **PLAN → DO**", "2. **DO → CHECK**"))
        cls.red_flags = norm(
            between(cls.skill_raw, "## Red flags (self-check)", "### Cycle failure modes")
        )
        cls.host = norm(
            between(
                cls.skill_raw,
                "## Host requirements (roles → agents)",
                "## Orchestrator role",
            )
        )
        cls.orchestrator = norm(
            between(cls.skill_raw, "## Orchestrator role", "## State machine")
        )
        cls.gate3 = norm(between(cls.skill_raw, "3. **CHECK → ACT**", "4. **ACT → EXIT**"))
        # Canonical gate-2/unit definition now lives in §Cycle status file → "Unit states".
        cls.unit_states = norm(
            between(cls.skill_raw, "**Unit states**", "In parallel-worktree mode")
        )

    # --- revision `r` counter semantics ---------------------------------

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
        self.assertIn("there is no 4th", self.counters)

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
        self.assertIn("pdca-escalate before the second fix", self.escalation)

    def test_no_arbitrary_replan_cap(self):
        self.assertIn("No cap on revisions", self.counters)

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
        self.assertIn("unresolved work prevents gate 2", self.gate2)

    def test_rejected_candidate_resumes_original_d(self):
        self.assertIn("rejected candidate resumes the original D", self.gate2)

    def test_superseded_replacement_mapping_required(self):
        # Mapping is required for an *actual replacement*; an additive prerequisite
        # gets none (see FinalFixGuardTest). Not weakened: the mapping stays required.
        self.assertIn("superseded→replacement", self.skill)
        self.assertIn("actual scope replacement", self.skill)
        # Actual replacement *requires* the explicit mapping; additive gets none.
        self.assertIn(
            "requires an explicit <superseded unit> → <replacement> mapping",
            self.skill,
        )
        self.assertIn("not superseded, no mapping", self.skill)

    # --- the status file is the only progress mirror ----------------------

    def test_progress_mirror_is_status_file_only(self):
        self.assertIn("Progress lives only in the cycle status file", self.mirror)
        self.assertIn("no separate todo or sidebar mirror", self.mirror)
        self.assertIn("a second mirror only creates divergence", self.mirror)

    def test_parallel_units_tracked_in_status_file(self):
        self.assertIn("DO units/streams table", self.status_file)
        self.assertIn("no separate todo or sidebar mirror", self.mirror)

    def test_aggregate_d_closes_on_gate2(self):
        self.assertIn(
            "aggregate D: closes by that same gate-2 definition", self.status_file
        )
        self.assertIn(
            "every active non-superseded unit done and every DO stream closed/verified",
            self.status_file,
        )

    # --- gate 1 transition + red-flag section (fix round 1) --------------

    def test_gate1_activates_single_aggregate_d_not_first_d(self):
        # The gate-1 "When starting DO" transition records the one aggregate
        # `D:` in the status file (units tracked there), not "the first `D:`".
        self.assertIn("phase transition in the status file", self.gate1)
        self.assertIn("single D: in progress", self.gate1)
        self.assertIn("P: closed", self.gate1)
        self.assertNotIn("the first D:", self.gate1)
        self.assertIn(
            "Progress lives only in the cycle status file", self.mirror
        )

    def test_redflag_attempt_scoped_to_same_revision_not_global(self):
        # Red flags name the deviation (next attempt instead of escalate); the
        # exact revision-scoped counter rules are canonical in §State machine /
        # §Escalation, to which the red flag points.
        self.assertIn("I made a next attempt instead of pdca-escalate", self.red_flags)
        self.assertIn("third failed CHECK of the same revision", self.counters)
        self.assertIn("there is no 4th", self.counters)
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
        # The rule is carried by the named heading, not by a numeric line pointer.
        self.assertIn("### PLAN owns the quality of the plan", self.skill_raw)
        self.assertIn(
            "A weak statement raises PLAN's burden", self.skill
        )  # essence kept, not the old parenthetical

    def test_four_unconditional_check_streams(self):
        self.assertIn("Four unconditional streams", self.check_streams)
        self.assertNotIn("Three unconditional streams", self.check_streams)

    # --- escalation wording scoped to a revision -------------------------

    def test_escalation_same_defect_scoped_and_revision_aware(self):
        self.assertIn("same revision", self.escalation)
        self.assertIn("same defect came back after one fix", self.escalation)
        self.assertNotIn("after the 3rd failed iteration", self.escalation)

    def test_autonomous_escalation_revision_aware(self):
        self.assertIn("escalation counter is unchanged", self.autonomous)
        self.assertIn("same revision", self.escalation)

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
        # The host briefs and the published assets share the prefixed ids; one
        # canonical stem selects the contract branch.  Both are EN-only.
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

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_config_briefs_mirror_scoped_contract(self):
        for path in CONFIG_BRIEFS:
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

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_escalator_briefs_revision_scoped_host_brief(self):
        with self.subTest(path=str(CONFIG_BRIEFS[3])):
            self._assert_escalator_brief_revision_scoped(CONFIG_BRIEFS[3])

    # --- Task 2: autonomous mode is question-free -------------------------

    def test_autonomous_mode_has_no_ask_user_instruction(self):
        # No user exists in autonomous mode: no question may be posed at all.
        self.assertNotIn("Ask a question", self.autonomous)
        self.assertNotIn("ask the user", self.autonomous)
        self.assertIn("No questions at all, ever", self.autonomous)

    def test_autonomous_blocker_routed_through_planner_or_escalate_to_stop(self):
        self.assertIn("pdca-planner", self.autonomous)
        self.assertIn("pdca-escalate", self.autonomous)
        self.assertIn("STOP", self.autonomous)
        self.assertIn("no question", self.autonomous)

    def test_autonomous_covers_missing_criteria_and_unavailable_resource(self):
        # A missing acceptance criterion / unavailable resource must be covered by
        # the question-free route, not by asking.
        self.assertIn("missing acceptance criteria", self.autonomous)
        self.assertIn("ambiguity", self.autonomous)
        self.assertIn("unavailable resource", self.autonomous)

    def test_gate1_ask_instruction_scoped_to_normal_mode(self):
        # The gate-1 ask-user instruction must be explicitly normal-mode only.
        self.assertNotRegex(self.gate1, r"acceptance criteria\s*—\s*ask, do not guess")
        self.assertIn("Normal mode with no acceptance criteria", self.gate1)
        self.assertIn("autonomous → route through pdca-planner/pdca-escalate", self.gate1)

    def test_normal_mode_retains_questions_and_approval(self):
        self.assertIn("the user's approval of the plan", self.gate1)
        self.assertIn("Normal mode", self.gate1)
        self.assertIn("ask the user", self.gate1)
        self.assertIn(
            "DO starts only after the user approves the plan in the normal mode", self.skill
        )

    # --- Task 2: DO-candidate fourth branch + trigger 5 -------------------

    def test_escalation_trigger5_low_confidence_without_externalness(self):
        self.assertIn("low confidence", self.escalation)
        self.assertIn("without established externalness", self.escalation)
        # The old "only if outside-cycle confirmed" local restriction must be gone.
        self.assertNotIn("pdca-escalate is called only if", self.escalation)
        self.assertIn("provisional candidate", self.escalation)

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

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_planner_four_way_classification_includes_insufficient_evidence_host_brief(self):
        with self.subTest(path=str(CONFIG_BRIEFS[0])):
            self._assert_planner_classification(CONFIG_BRIEFS[0])

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

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_planner_response_format_has_confidence_and_classification_slot_host_brief(self):
        with self.subTest(path=str(CONFIG_BRIEFS[0])):
            self._assert_planner_response_format(CONFIG_BRIEFS[0])

    # --- Task 2: primary is a dispatcher incl. architect ------------------

    def test_orchestrator_is_cheap_only_dispatcher(self):
        # Cheap-only: only an effective-cheap primary drives the cycle; a
        # medium/strong primary (incl. architect) is explicitly excluded.
        self.assertIn("dispatcher, not a reader and not a decider", self.orchestrator)
        self.assertIn("Cheap primary only", self.orchestrator)
        self.assertIn(
            "medium/strong primary (e.g. architect) does not drive the cycle",
            self.orchestrator,
        )
        self.assertIn("never authors a plan", self.orchestrator)
        self.assertIn("never reads files", self.orchestrator)
        self.assertIn(
            "Both the initial PLAN and any replan belong to pdca-planner",
            self.orchestrator,
        )
        self.assertNotIn("every primary", self.orchestrator)

    def test_primary_wording_not_build_only(self):
        # The orchestrator is named by effective tier ("cheap orchestrator"), not
        # tied to one agent name; `build` is only the default shorthand.
        self.assertGreaterEqual(self.skill.count("cheap orchestrator"), 3)
        self.assertIn("build is the shorthand throughout", self.skill)
        self.assertNotIn("the orchestrator (primary)", self.skill)

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_architect_outside_cycle_and_central_cheap_dispatcher(self):
        # Architect is a universal decision primary, not a PDCA-specific role: the
        # PDCA paragraph was deliberately removed from its body. The cheap-only
        # dispatch rule is owned centrally by config/AGENTS.md and the pdca-dotnet
        # SKILL, not by the architect prompt. Assertions keep the architect identity
        # and pin the rule where it now lives (full normalized clauses, not mere
        # keyword co-occurrence). The host contract and briefs are EN-only.
        architect = CONFIG_AGENTS / "architect.md"
        raw = read(architect)
        body = norm(between(raw, "# architect", "## Skills"))
        self.assertTrue(body, "architect body not found")
        # No PDCA-specific role and no dispatcher wording.
        self.assertNotRegex(
            body.lower(),
            r"inside pdca|outside pdca"
            r"|dispatcher, not the plan author"
            r"|dispatcher",
        )
        # Meaningful universal statements from the body (not permission allow-list).
        self.assertIn("deciding medium-tier primary", body.lower())
        self.assertIn("scout only (cheap tier)", body.lower())
        self.assertIn("coder only (cheap tier)", body.lower())
        self.assertIn("brainstorming", body.lower())
        # The cheap-only exclusion and the no-widen rule are authoritative centrally
        # (config/AGENTS.md tier routing) — they must not be restored into the
        # architect prose. The central file is EN-only too.
        central = norm(read(CONFIG / "AGENTS.md")).lower()
        for phrase in (
            "cheap orchestrator",
            "medium/strong primary",
            "does not dispatch the cycle",
            "rights of expensive roles are never widened",
        ):
            self.assertIn(phrase, central)

    def test_skill_owns_cheap_only_orchestration_architect_excluded(self):
        # The SKILL owns cheap-only orchestration; architect is excluded, never an
        # "every primary" dispatcher.
        self.assertIn("cheap-only", self.skill.lower())
        self.assertIn(
            "you are a dispatcher, not a reader and not a decider",
            self.orchestrator.lower(),
        )
        self.assertIn("cheap primary only", self.orchestrator.lower())
        self.assertIn(
            "medium/strong primary (e.g. architect) does not drive the cycle",
            self.orchestrator.lower(),
        )
        self.assertIn(
            "the cheap orchestrator never authors a plan",
            self.orchestrator.lower(),
        )
        self.assertIn(
            "both the initial plan and any replan belong to pdca-planner",
            self.orchestrator.lower(),
        )
        self.assertNotIn("every primary", self.orchestrator.lower())

    # --- Task 2: host-profile binding + tier labels (no model:) -----------

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
        self.assertIn("never a model: field in the role markdown", self.host)
        # Fallback limited by actual host permissions; denials never bypassed.
        self.assertIn("must never bypass the deny", self.host)

    # --- Task 2 fix round 1: user-go boundary + authority invocation ------

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

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_planner_plan_disk_paragraph_scopes_user_approval_to_normal_mode_host_brief(self):
        with self.subTest(path=str(CONFIG_BRIEFS[0])):
            self._assert_planner_plan_disk_paragraph(CONFIG_BRIEFS[0])

    def test_plan_authority_invocation_unambiguous(self):
        # The cheap orchestrator forwards the request/evidence; planner authors the
        # plan; coder writes. No "every primary incl architect" authority wording.
        section = norm(between(
            self.skill_raw,
            "Starting a cycle and the",
            "## Economics",
        ))
        self.assertTrue(section, "authority invocation paragraph not found")
        self.assertNotIn("the orchestrator (primary) formulates the P: task", section)
        self.assertIn(
            "cheap orchestrator forwards the request and gathered evidence", section
        )
        self.assertIn("formulates the P: task/plan", section)
        self.assertIn("pdca-executor writes", section)
        self.assertIn("belong to pdca-planner", section)
        self.assertNotIn("every primary", section)
        self.assertNotIn("architect", section)

    def test_cycle_quickref_marks_approval_normal_mode_only(self):
        cycle = norm(between(
            self.skill_raw,
            "Cycle: `PLAN",
            "Progress is recorded",
        ))
        self.assertTrue(cycle, "cycle quickref line not found")
        self.assertIn("normal mode", cycle)
        self.assertIn("autonomous", cycle)


class TwoPathContractTest(unittest.TestCase):
    """D5 guards: the normal vs autonomous path contract.

    Scoped to the operative SKILL sections (the two-path paragraph, §Autonomous
    mode, §Host requirements).  Rule-presence only: reads Markdown text and never
    executes a model or the subagent tool, so it proves the wording, not behavior.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.two_paths = norm(
            between(cls.skill_raw, "**Two paths, one contract.**", "**Project overlay.**")
        )
        cls.autonomous = norm(
            between(cls.skill_raw, "## Autonomous mode", "## Red flags")
        )
        cls.host = norm(
            between(
                cls.skill_raw,
                "## Host requirements (roles → agents)",
                "## Orchestrator role",
            )
        )

    def test_skill_names_both_paths_normal_drives_autonomous_dispatches(self):
        # Normal: the primary drives the cycle; autonomous: it dispatches the whole
        # cycle to pdca-orchestrator as a subagent (does not drive it itself).
        self.assertIn("normal mode you drive the cycle yourself", self.two_paths)
        self.assertIn(
            "autonomous mode you do not drive the cycle yourself", self.two_paths
        )
        self.assertIn(
            "dispatch the whole cycle to the cheap pdca-orchestrator subagent",
            self.two_paths,
        )

    def test_autonomous_path_carries_cycle_brief_and_compact_summary(self):
        # A cycle brief goes in; a summary of at most 8 lines comes out.
        self.assertIn("cycle brief", self.autonomous)
        self.assertIn("≤8", self.autonomous)
        self.assertIn("summary", self.autonomous)
        self.assertIn("subagent dispatch", self.autonomous)

    def test_flat_primary_fallback_when_orchestrator_unavailable(self):
        # Agent absent / nested delegation forbidden or too shallow -> flat primary.
        self.assertIn("fall back to the flat primary", self.autonomous)
        self.assertIn("nested delegation", self.autonomous)
        self.assertIn("subagent dispatch to pdca-orchestrator fails", self.autonomous)
        self.assertIn("delegation forbidden", self.autonomous)

    def test_setup_allowlist_includes_pdca_orchestrator(self):
        self.assertIn("pdca-orchestrator (autonomous delegation)", self.host)


class ApprovalGateAndFallbackGuardTest(unittest.TestCase):
    """D8 negative guards: the normal-mode approval gate and the no-silent-bypass fallback.

    Rule-presence only.  These read Markdown text and never execute a model.
    Each guard pins a *short tokens* phrase whose removal (or whose flip in the
    opposite section) makes the assertion fail, so the guard is negative in
    direction: deleting the approval clause, requiring an approval in autonomous
    mode, or dropping the "not a silent run" clause turns a test red.  Scoped to
    the operative SKILL sections with short tokens (`approval`, `normal`,
    `autonomous`, `pause`, `Notice:`) rather than brittle full sentences.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)
        cls.gate1 = norm(between(cls.skill_raw, "1. **PLAN → DO**", "2. **DO → CHECK**"))
        cls.state_machine = norm(
            between(cls.skill_raw, "## State machine", "### Phase progress mirror")
        )
        cls.autonomous = norm(
            between(cls.skill_raw, "## Autonomous mode", "## Red flags")
        )
        cls.host = norm(
            between(
                cls.skill_raw,
                "## Host requirements (roles → agents)",
                "## Orchestrator role",
            )
        )

    # --- approval gate: mandatory in normal mode, absent in autonomous ------

    def test_normal_mode_requires_explicit_approval_before_do(self):
        # Normal path: DO is gated on an explicit user approval of the plan.
        # Removing the clause from gate 1 or the approval section breaks this test.
        self.assertIn("the user's approval of the plan", self.gate1)
        self.assertIn("Normal mode", self.gate1)
        self.assertIn(
            "DO starts only after the user approves the plan in the normal mode", self.skill
        )
        # The state-machine cycle line still names the normal-mode plan approval.
        self.assertIn("normal mode: the user reads and approves the plan", self.state_machine)

    def test_autonomous_mode_has_no_approval_and_no_pause(self):
        # Autonomous path: no approval, no pause. If autonomous began
        # requiring an approval, the negated clauses would disappear.
        self.assertIn("no approval and no invitation", self.autonomous)
        self.assertIn("no approval request", self.autonomous)
        self.assertIn("without approval pauses", self.autonomous)
        self.assertNotIn("explicit go", self.autonomous)
        self.assertNotIn("approval is required", self.autonomous)

    def test_gate1_excludes_autonomous_from_the_approval_requirement(self):
        # The gate-1 approval requirement must explicitly carve out autonomous mode.
        self.assertIn(
            "except in autonomous mode, where no approval is required", self.gate1
        )

    # --- fallback: explicit marking, never a silent bypass ----------------

    def test_flat_primary_fallback_is_explicit_and_noticed(self):
        # Falling back = drive the cycle yourself AND record it (`Notice:`).
        self.assertIn("fall back to the flat primary", self.autonomous)
        self.assertIn("drive the cycle yourself", self.autonomous)
        self.assertIn("fallback", self.autonomous)
        self.assertIn("Notice:", self.autonomous)

    def test_no_silent_run_without_a_required_role(self):
        # An unavailable required role is a resource blocker: no substitute and no
        # silent execution without the role. Dropping that clause turns this test red.
        self.assertIn("resource blocker", self.host)
        self.assertIn("never execute silently without the role", self.host)
        self.assertIn("must never bypass the deny", self.host)
        self.assertIn("Notice:", self.host)
        self.assertNotRegex(self.host, r"(?i)run silently without")
        self.assertNotIn("without the role is acceptable", self.host)


class CrossArtifactLabelGuardTest(unittest.TestCase):
    """Task 3 guards: README summary + diagram label sources + scenario matrix.

    Rule-presence only.  These read JSON/text; they never execute a model, the
    real PDCA cycle, or a production state machine, and therefore do not prove
    runnable behavior.  Behavioral validation is the independent A–I review.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.gen = read(GEN_PDCA_PATH)
        # The README summary guards below read the *host* README (this repo's own
        # README has different content) and are host-gated.
        cls.readme = read(README_PATH) if HOST_AVAILABLE else ""
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

    # --- README concise summary (host README — gated on an EN edition) -----

    @unittest.skipUnless(readme_is_en(), SKIP_README)
    def test_readme_scoped_attempts_no_brittle_line_count(self):
        self.assertNotIn("~1460", self.readme)
        self.assertNotRegex(self.readme, r"contract\s+(of\s+)?~?\d+\s+lines")
        self.assertIn("detailed contract", self.readme)
        self.assertIn("n/3", self.readme)
        self.assertIn("revision", self.readme)
        self.assertNotIn("max. 3 iterations", self.readme)

    @unittest.skipUnless(readme_is_en(), SKIP_README)
    def test_readme_single_active_phase_and_no_questions(self):
        self.assertIn("exactly one active", self.readme)
        self.assertRegex(self.readme, r"no questions|without questions")

    @unittest.skipUnless(readme_is_en(), SKIP_README)
    def test_readme_assets_tier_labels_not_model(self):
        self.assertNotIn("empty `model:`", self.readme)
        self.assertIn("# tier:", self.readme)

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

    Intended-norm red: before the final-fix edits these assertions fail because the
    normative clauses are absent, not because of import/path errors.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)
        cls.gate2 = norm(between(cls.skill_raw, "2. **DO → CHECK**", "3. **CHECK → ACT**"))
        cls.gate3 = norm(between(cls.skill_raw, "3. **CHECK → ACT**", "4. **ACT → EXIT**"))
        cls.status_file = norm(
            between(cls.skill_raw, "### Cycle status file", "### Message for the next session")
        )
        cls.recovery = norm(
            between(cls.skill_raw, "## Recovery after compaction", "## Evidence over assertion")
        )
        cls.keep_check = norm(
            between(
                cls.skill_raw,
                "**Keep CHECK within one approved PLAN.**",
                "### Parallel CHECK streams",
            )
        )
        cls.autonomous = norm(between(cls.skill_raw, "## Autonomous mode", "## Red flags"))
        cls.escalation = norm(
            between(cls.skill_raw, "### Escalation (`pdca-escalate`)", "## PLAN: design checklist")
        )
        cls.check_streams = norm(
            between(cls.skill_raw, "### Parallel CHECK streams", "Then follows the checklist")
        )
        # Canonical gate-2/unit definition now lives in §Cycle status file → "Unit states".
        cls.unit_states = norm(
            between(cls.skill_raw, "**Unit states**", "In parallel-worktree mode")
        )
        cls.planner_en = norm(read(ASSET_BRIEFS[0]))
        # The host briefs / host README / host plan live in the `opencode-config`
        # repo; the guards that read them are host-gated (empty string otherwise).
        # The host `pdca-*` briefs mirror the EN assets, the legacy `coder` brief is
        # RU, so the host guards match either wording.
        cls.planner_host = norm(read(CONFIG_BRIEFS[0])) if HOST_AVAILABLE else ""
        cls.coder_en = norm(read(ASSET_BRIEFS[1]))
        cls.coder_host = norm(read(CONFIG_BRIEFS[1])) if HOST_AVAILABLE else ""
        cls.check_en = norm(read(ASSET_BRIEFS[2]))
        cls.check_host = norm(read(CONFIG_BRIEFS[2])) if HOST_AVAILABLE else ""
        cls.scout_en = norm(read(SKILL_DIR / "assets/agents/pdca-scout.md"))
        cls.scenarios = read(SCENARIOS_PATH)
        cls.plan = norm(read(PLAN_PATH)) if HOST_AVAILABLE else ""
        cls.readme = norm(read(README_PATH)) if HOST_AVAILABLE else ""

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
        self.assertIn("candidate analysis", self.skill)
        self.assertIn("never completes", self.skill)

    def test_planner_and_coder_briefs_distinguish_additive_from_replacement(self):
        self.assertIn("additive", self.planner_en)
        self.assertIn("additive", self.coder_en)

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_host_briefs_distinguish_additive_from_replacement(self):
        # The host `pdca-planner` and `coder` briefs mirror the EN assets.
        self.assertRegex(self.planner_host, r"(?i)additive")
        self.assertRegex(self.coder_host, r"(?i)additive")

    def test_scenarios_split_b_into_additive_and_replacement(self):
        self.assertIn("B1", self.scenarios)
        self.assertIn("B2", self.scenarios)
        # "Additive" is capitalized in the table/heading; case-insensitive compare.
        self.assertIn("additive", self.scenarios.lower())

    # --- F3: gate 2 "closed" single definition ----------------------------

    def test_gate2_closed_means_active_units_and_streams(self):
        self.assertIn("every active non-superseded unit done", self.unit_states)
        self.assertIn("every DO stream closed/verified", self.unit_states)
        self.assertIn("superseded never counts as done", self.unit_states)

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
            "circular",
            "self mapping",
        ):
            self.assertIn(phrase, self.unit_states)
        self.assertIn("pending/blocked replacement", self.unit_states)
        self.assertIn("gate 2 rejected", self.unit_states)

    def test_aggregate_d_completion_derives_single_definition(self):
        self.assertIn(
            "aggregate D: closes by that same gate-2 definition", self.unit_states
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

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_host_coder_brief_mandates_durable_state_and_defect_history(self):
        # The host `coder` brief mirrors the EN asset.
        self.assertRegex(self.coder_host, r"(?i)defect history")
        # The durable-state field name is literal in both.
        self.assertIn("Plan revision r", self.coder_host)

    def test_check_brief_carries_r_n_and_defect_history_as_history_only(self):
        self.assertIn("defect history", self.check_en)
        self.assertIn("revision r", self.check_en)
        self.assertIn("not evidence for the current CHECK", self.check_en)
        self.assertIn("current full aggregated report", self.check_en)

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_host_check_brief_carries_defect_history(self):
        # The host `pdca-check` brief mirrors the EN asset.
        self.assertRegex(self.check_host, r"(?i)defect history")

    def test_scout_brief_can_report_status_snapshot_and_defect_history(self):
        self.assertIn("defect history", self.scout_en)

    # --- narrow discovered completions ------------------------------------

    def test_security_failed_check_counts_as_failed_check_of_revision(self):
        self.assertIn("failed CHECK of the current revision", self.check_streams)
        self.assertIn("triggered security failure", self.check_streams)
        # The same rule is mirrored in §Escalation (ordinary, shared counters).
        self.assertIn(
            "Every failed CHECK of the current revision counts", self.escalation
        )
        self.assertIn(
            "ordinary security finding is an ordinary failed stream", self.escalation
        )

    def test_exhausted_revision_no_fourth_attempt_even_after_escalate(self):
        self.assertIn(
            "exhausted revision r gets no 4th attempt even after pdca-escalate",
            self.escalation,
        )

    def test_continue_only_via_genuinely_revised_remediation_plan(self):
        self.assertIn("genuinely revised remediation plan", self.escalation)
        self.assertIn("rename/reword", self.escalation)
        self.assertIn("session reset", self.escalation)
        self.assertIn("cannot manufacture a new revision", self.escalation)

    def test_missing_required_report_is_regathered_not_project_defect(self):
        self.assertIn("missing required report", self.escalation)
        self.assertIn("re-gathered", self.escalation)

    def test_escalation_decision_routed_by_orchestrator_when_not_exhausted(self):
        # Decision, not a recommendation: escalate decides, the cheap orchestrator
        # only routes (no semantic re-selection).
        self.assertIn("non-exhausted attempt", self.escalation)
        self.assertIn("decision applies to the current plan", self.escalation)
        self.assertIn("implementation under the current plan", self.escalation)
        self.assertIn("pdca-executor", self.escalation)
        self.assertNotIn("recommendation", self.escalation)
        self.assertIn(
            "Execute an pdca-escalate decision by routing, never by re-deciding", self.skill
        )

    def test_autonomous_stop_conditional_not_after_every_escalate(self):
        self.assertIn("the stop stays conditional", self.autonomous)
        self.assertIn(
            "not stopped automatically after every successful escalation",
            self.escalation,
        )

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

    # --- F2/F7: no dedicated primary plan; build is default alias --------

    def test_no_dedicated_primary_plan_required(self):
        # No dedicated primary plan author: the cheap orchestrator routes, planner
        # owns the PLAN (initial and every replan).
        self.assertIn("the PLAN decision always belongs to pdca-planner", self.skill)
        self.assertIn("The cheap orchestrator never authors a plan", self.skill)
        self.assertIn(
            "Both the initial PLAN and any replan belong to pdca-planner", self.skill
        )

    def test_build_is_default_shorthand_for_cheap_primary(self):
        # `build` is only the default cheap-orchestrator shorthand, not a claim
        # that any primary (incl. medium/strong) drives the cycle.
        self.assertIn("build is the shorthand throughout", self.skill)
        self.assertIn("the host's primary", self.skill)
        self.assertNotIn("any primary", self.skill)
        self.assertIn("effective host-profile tier is cheap", self.skill)

    # --- artifact: source change (incl label-only) allows delivery --------
    # (the plan document and the README summary are host artifacts → gated)

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_plan_delivery_condition_is_source_change_incl_labels(self):
        self.assertIn("including a label-only change", self.plan)
        self.assertIn("approved spec supersedes the stale structure-only wording", self.plan)

    @unittest.skipUnless(readme_is_en(), SKIP_README)
    def test_readme_sync_row_follows_source_change_condition(self):
        self.assertIn("including a label-only change", self.readme)

    def test_scenarios_have_no_nonexistent_escalation_security_fail_link(self):
        self.assertNotIn("§Escalation (security fail)", self.scenarios)
        self.assertNotIn("§Escalation (security-fail)", self.scenarios)


class AuditGateBoundaryTest(unittest.TestCase):
    """#238 guards: the PASS gate is BINDING/APPLICABLE, extra audit rows are diagnostic.

    Rule-presence only (reads Markdown text; never executes a model), so it proves
    the wording, not the behavior.  The behavioral pressure scenarios live in
    ``tests/scenarios.md`` (A–H) and must not be reported as executed from here.
    """

    MANIFEST_ENTRY = "required_rows"

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)

    def test_gate_replaced_with_binding_applicable(self):
        # The gate line may wrap in the raw Markdown; compare normalised text.
        self.assertIn("No PASS while any BINDING/APPLICABLE", self.skill)

    def test_old_absolute_gate_is_gone(self):
        # The old absolute prohibition must not survive anywhere in the contract.
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

    def test_completeness_gate_is_binding_qualified(self):
        gate = norm(between(
            self.skill_raw,
            "### CHECK completeness gate",
            "## Debugging (loop-back CHECK → DO)",
        ))
        self.assertTrue(gate, "CHECK completeness gate section not found")
        self.assertIn("binding/applicable", gate.lower())
        self.assertNotIn("any open row forbids PASS", gate)

    def test_reviewer_evidence_pack_present(self):
        # #235 (E07): the changed registry full bodies are staged inside the
        # allowed roots, with a source-side receipt — not a diffstat-only pack.
        pack = norm(between(
            self.skill_raw,
            "### Reviewer evidence pack",
            "## CHECK: audit checklist",
        ))
        self.assertTrue(pack, "reviewer evidence pack section not found")
        self.assertIn("stages the full bodies", pack)
        self.assertIn("copy, not a move", pack)
        self.assertIn("source identity", pack)
        self.assertIn("content equality", pack)
        self.assertIn("Roslyn resolution runs in that source-side gather", pack)
        self.assertIn("row-level result/reason", pack)
        self.assertIn("evidence open/blocked", pack)
        self.assertIn("not a proof of execution-time", pack)

    def test_execution_policy_and_journal_present(self):
        # #235 (E10): unit unlimited, integration boundary-only, mandatory capture.
        section = norm(between(
            self.skill_raw,
            "### Execution journal and the unit/integration policy",
            "### Worktree sub-tasks of one cycle",
        ))
        self.assertTrue(section, "execution journal section not found")
        self.assertIn("not on the number of report entries", section)
        self.assertIn("not a unit-vs-integration criterion", section)
        self.assertIn("no separate universal numeric cap", section)
        self.assertIn("projected from that journal", section)
        self.assertIn("omits a started execution is rejected", section)
        self.assertIn("failed-to-start", section)
        self.assertIn("never invented", section)
        self.assertIn("blocked/unresolved", section)

    def test_act_cleanup_receipt_present(self):
        # #235 (g/l): the terminal-closure cleanup is gated by a machine-checkable
        # receipt; premature cleanup is rejected and the manifest is immutable.
        section = norm(between(
            self.skill_raw,
            "### ACT cleanup receipt",
            "### Message for the next session",
        ))
        self.assertTrue(section, "ACT cleanup receipt section not found")
        self.assertIn("machine-checkable receipt", section)
        self.assertIn("premature cleanup", section)
        self.assertIn("prior hashes", section)
        self.assertIn("frozen manifest is not rewritten", section)
        self.assertIn("planned lifecycle", section)

    def test_validator_exposes_the_new_subcommands(self):
        script = read(SKILL_DIR / "scripts/validate_inner_loop.py")
        for mode in ("journal", "project", "cleanup", "archived"):
            self.assertIn('"%s"' % mode, script, "validator missing mode %r" % mode)
        self.assertIn("--journal", script)
        self.assertIn("--cleanup", script)


if __name__ == "__main__":
    unittest.main()
