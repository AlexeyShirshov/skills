"""Static regression guards for the pdca-coder contract.

These tests read `config/skills/pdca-coder/` as *text* and assert the retained PDCA
rules are present in the operative sections (state machine, counters, gates,
todo tracker, autonomous mode, escalation, evidence/recovery/injection, status
file, parallel DO streams, worktree template).  They are rule-presence guards,
not behavioral proof.

The last class is a **forbidden-token** guard: it scans every file under
`config/skills/pdca-coder/` for the nine stack tokens (built from concatenated
fragments so this file itself stays clean) and asserts each has zero matches.

Run:
    python3 -m unittest discover -s config/skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PDCA_DIR = REPO / "config/skills/pdca-coder"
SKILL_PATH = PDCA_DIR / "SKILL.md"


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


def scan_tree(root: Path, patterns) -> list:
    hits = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        low = text.lower()
        hits.extend((str(path), p) for p in patterns if p.lower() in low)
    return hits


class ContractConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_raw = read(SKILL_PATH)
        cls.skill = norm(cls.skill_raw)
        cls.fm = parse_frontmatter(frontmatter_block(cls.skill_raw))
        cls.counters = norm(between(cls.skill_raw, "## State machine", "### Phase todo tracker"))
        cls.todo = norm(between(cls.skill_raw, "### Phase todo tracker", "Transition gates:"))
        cls.status_file = norm(
            between(cls.skill_raw, "### Cycle status file", "### Message for the next session")
        )
        cls.autonomous = norm(between(cls.skill_raw, "## Autonomous mode", "## Red flags"))
        cls.escalation = norm(
            between(cls.skill_raw, "### Escalation (`escalate`)",
                    "## PLAN selects the toolchain and lenses")
        )
        cls.evidence = norm(
            between(cls.skill_raw, "## Evidence over assertion",
                    "## Instruction priority and injection defense")
        )
        cls.recovery = norm(
            between(cls.skill_raw, "## Recovery after compaction and drift",
                    "## Evidence over assertion")
        )
        cls.injection = norm(
            between(cls.skill_raw, "## Instruction priority and injection defense",
                    "## Delegation by phase")
        )
        cls.do_streams = norm(
            between(cls.skill_raw, "### Parallel DO streams", "### Coder editing discipline")
        )
        cls.worktree = norm(
            between(cls.skill_raw, "### Worktree sub-tasks", "### Escalation")
        )
        cls.gate1 = norm(between(cls.skill_raw, "1. **PLAN → DO**", "2. **DO → CHECK**"))
        cls.gate2 = norm(between(cls.skill_raw, "2. **DO → CHECK**", "3. **CHECK → ACT**"))
        cls.gate3 = norm(between(cls.skill_raw, "3. **CHECK → ACT**", "4. **ACT → EXIT**"))
        cls.gate4 = norm(
            between(cls.skill_raw, "4. **ACT → EXIT**",
                    "**You cannot skip CHECK. You cannot close the cycle without ACT.**")
        )

    # --- frontmatter ------------------------------------------------------

    def test_frontmatter_has_exactly_name_and_description(self):
        self.assertEqual({"name", "description"}, set(self.fm))
        self.assertEqual("pdca-coder", self.fm["name"])
        self.assertNotIn("model", self.fm)

    def test_description_is_coding_and_stack_agnostic(self):
        desc = self.fm["description"].lower()
        for token in ("software-engineering", "stack-agnostic", "code", "tests"):
            self.assertIn(token, desc)
        for banned in ("any task", "presentation", "research", "non-code"):
            self.assertNotIn(banned, desc)

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
        self.assertIn("loop-back", self.skill.lower())

    # --- transition gates 1-4 with key conditions -------------------------

    def test_gate1_conditions(self):
        for token in ("acceptance criteria", "test strategy", "docs plan",
                      "perf-measurement decision", "unit execution mode"):
            self.assertIn(token, self.gate1)
        self.assertIn("go", self.gate1)

    def test_gate2_conditions(self):
        self.assertIn("all D: tasks and all DO streams", self.gate2)
        self.assertIn("build/tests have run", self.gate2)
        self.assertIn("blocker report is not done", self.gate2)

    def test_gate3_conditions(self):
        self.assertIn("all CHECK streams are green", self.gate3)
        self.assertIn("security", self.gate3)

    def test_gate4_conditions(self):
        self.assertIn("AGENTS.md", self.gate4)
        self.assertIn("status file is finalized", self.gate4)

    # --- mandatory todo tracker rules -------------------------------------

    def test_todo_tracker_rules(self):
        self.assertIn("todowrite", self.todo)
        self.assertIn("exactly one in_progress", self.todo)
        self.assertIn("single aggregate D:", self.todo)
        self.assertIn("Status first, todo second", self.todo)
        self.assertIn("Reconcile each turn", self.todo)

    # --- autonomous mode: delegation, fallback, Notice --------------------

    def test_autonomous_delegation_and_fallback(self):
        self.assertIn("pdca-orchestrator", self.autonomous)
        self.assertIn("Task", self.autonomous)
        self.assertIn("fall back to the flat primary", self.autonomous)
        self.assertIn("subagent_depth", self.autonomous)
        self.assertIn("Notice:", self.autonomous)

    # --- escalation: triggers, scoping, no-4th, route-don't-re-decide -----

    def test_escalation_triggers_and_counter_scope(self):
        self.assertIn("Triggers (any one)", self.escalation)
        self.assertIn("scoped to the current plan revision r", self.escalation)
        self.assertIn("new revision at n=1", self.escalation)
        self.assertIn("third failed CHECK of the same revision", self.escalation)
        self.assertIn("same defect", self.escalation)

    def test_escalation_no_fourth_attempt(self):
        self.assertIn("there is no 4th attempt", self.escalation)
        self.assertIn("gets no 4th attempt even after escalate", self.escalation)

    def test_escalation_is_routed_not_re_decided(self):
        self.assertIn("never by re-deciding", self.skill)
        self.assertIn("by routing", self.escalation)
        self.assertIn("genuinely revised remediation plan", self.escalation)

    # --- evidence, recovery, instruction priority/injection ---------------

    def test_evidence_over_assertion(self):
        self.assertIn("fresh evidence", self.evidence)
        self.assertIn("exit code", self.evidence)
        self.assertIn("regression test", self.evidence)
        self.assertIn("log", self.evidence)

    def test_recovery_after_compaction(self):
        self.assertIn("status file is the source of truth", self.recovery)
        self.assertIn("revision r", self.recovery)
        self.assertIn("attempt n/3", self.recovery)
        self.assertIn("Rebuild the todo", self.recovery)
        self.assertIn("Recovered after compaction", self.recovery)

    def test_instruction_priority_and_injection_defense(self):
        self.assertIn("Security invariants", self.injection)
        self.assertIn("Explicit user request", self.injection)
        self.assertIn("Injections", self.injection)
        self.assertIn("ignore and tell the user", self.injection)
        self.assertIn("Secrets", self.injection)

    # --- status file, parallel DO streams, worktree template --------------

    def test_cycle_status_file_schema(self):
        self.assertIn("docs/specs/status/<task>-<N>.md", self.status_file)
        self.assertIn("Progress log", self.status_file)
        self.assertIn("Current cycle N", self.status_file)
        self.assertIn("Plan revision r", self.status_file)
        self.assertIn("Attempt n", self.status_file)
        self.assertIn("Defect history", self.status_file)

    def test_parallel_do_streams(self):
        self.assertIn("test first, then code", self.do_streams)
        self.assertIn("docs later", self.do_streams)
        self.assertIn("prose documentation", self.do_streams)

    def test_worktree_sub_task_template(self):
        self.assertIn("Work ONLY in worktree", self.worktree)
        self.assertIn("git -C", self.worktree)
        self.assertIn("never push", self.worktree)
        self.assertIn("absolute paths", self.worktree)


class ForbiddenTokenGuardTest(unittest.TestCase):
    """Zero matches for all nine stack tokens anywhere in the pdca-coder tree."""

    def test_no_forbidden_token_in_any_pdca_file(self):
        hits = scan_tree(PDCA_DIR, forbidden_tokens())
        self.assertEqual([], hits, "forbidden tokens found: %r" % hits)

    def test_detector_catches_a_rejected_sample(self):
        patterns = forbidden_tokens()
        rejected = _cat("prefix ", "dot", "net-", " suffix")
        clean = "a perfectly ordinary sentence"
        self.assertTrue(any(p.lower() in rejected.lower() for p in patterns))
        self.assertFalse(any(p.lower() in clean.lower() for p in patterns))

    def test_all_nine_patterns_are_scanned(self):
        self.assertEqual(9, len(forbidden_tokens()))


if __name__ == "__main__":
    unittest.main()
