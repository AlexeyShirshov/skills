"""Drift guard across the two code variants (`pdca-coder` and `pdca-dotnet`).

The two code variants are deliberately published as *complete* contracts, because
each is installed and invoked on its own — so the same state machine, gates,
counters and approval rules are necessarily written twice (they currently share
~85% of their wording).  Duplication is the price of standalone packaging; the
real hazard is *silent* divergence: a rule fixed in one variant and forgotten in
the other.

This module makes that hazard loud.  It is rule-presence/absence only: it reads
the two contract files as text, never executes a model or a real cycle.

Two kinds of guard:

* **Shared rules** — an anchored list of rules that must appear in both variants.
  Adding a rule fix to one variant without the other fails here.
* **Ownership** — the shared-by-design sections must exist in both, and the
  .NET-only sections must not leak into the stack-agnostic variant.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

FAMILY = Path(__file__).resolve().parents[2]  # the `skills/` directory
CODER = FAMILY / "pdca-coder/SKILL.md"
DOTNET = FAMILY / "pdca-dotnet/SKILL.md"

CODER_AGENTS = FAMILY / "pdca-coder/assets/agents"
DOTNET_AGENTS = FAMILY / "pdca-dotnet/assets/agents"

# Sections that belong to the shared contract: both variants must carry them.
# A rename that lands in one file only breaks the pairing these guards rely on.
SHARED_SECTIONS = (
    "## Host requirements (roles → agents)",
    "## Orchestrator role",
    "## State machine",
    "### Phase progress mirror (status file only)",
    "## Autonomous mode",
    "## Red flags (self-check)",
    "### Cycle failure modes",
    "## Recovery after compaction and drift",
    "## Evidence over assertion",
    "## Instruction priority and injection defense",
    "## Delegation by phase",
    "### Escalation (`pdca-escalate`)",
    "### Plan approval (PLAN → DO)",
    "## CHECK: audit checklist (generic)",
    "### Parallel CHECK streams (code audit + test + doc + perf + security*)",
    "### Parallel sub-tasks in worktrees (within one cycle)",
    "## Debugging (loop-back CHECK → DO)",
    "## ACT: closing the cycle, status and handoff",
    "### Cycle status file",
    "### Message for the next session",
    "## Economics",
)

# Sections that only the .NET variant owns.  The stack-agnostic variant must stay
# free of them; if one appears there, the variants have been merged by accident.
DOTNET_ONLY_SECTIONS = (
    "### Versioned evidence contract",
    "### Reviewer evidence pack (independent CHECK over full bodies)",
    "### CHECK completeness gate — mandatory evidence contract",
    "### ACT cleanup receipt (heavy staged materials)",
    "### Execution journal and the unit/integration policy",
    "### DO brief: mandatory `test scope`",
    "### Test run safety (memory + streaming) — every phase",
    "### .NET command canonical forms (frozen; do not reinvent per plan)",
    "### Evidence helper discipline",
)

# Rules that must hold in BOTH variants.  Each anchor is a phrase that is unique
# to the rule it protects, so a rewrite that keeps the rule but rewords it should
# also update this list — that is the intended friction.
SHARED_RULES = {
    "three counters": "Three counters, do not mix them",
    "N grows only in ACT": "grows only in ACT — loop-backs change r/n, not <N>",
    "no 4th attempt": "no 4th attempt even after `pdca-escalate`",
    "gate 1 needs the plan fields": "only if `pdca-planner`'s answer contains",
    "gate 2 blocker is not done": "a blocker report leaves it blocked, never done",
    "gate 3 needs every stream": "CHECK → ACT — only if all CHECK streams are green",
    "single status writer": "Every write is by `pdca-executor`",
    "status file is the only mirror": "it is the only progress mirror and the source of truth",
    "state matches the log": "The current state must match the latest log line",
    "durable approval ref": "durable pending approval ref",
    "approval identity binds the criteria": "the cycle N, the plan revision r and the acceptance-criteria set",
    "approval-needed checkpoint": "approval-needed checkpoint",
    "check task_id is not a gate": "A lost ID is not a passed gate",
    "no explicit check, no pass": "a gate without an explicit check is not passed",
    "debugging fixes the source": "fix at the source, not where the symptom surfaced",
    "no push without a request": "push — never without a separate explicit request",
    "status file lifetime": "Lifetime — a durable handoff and record, never deleted",
    "handoff carries pointers only": "no code or diffs — only pointers and the goal",
    "parallel units are disjoint": "units do not share mutable files or a shared contract",
    "plan command contract": "selector resolves to at least one target in the declared scope",
    "vacuous run is a failure": "Zero selected targets, zero executed cases or an empty result set is a failed run",
    "exception repetition is systemic": "three or more units of one campaign is a systemic defect",
    "re-anchor drift classes": "cosmetic drift",
    "stop-loss budget": "gate 1 fixes a stop-loss budget",
}


def norm(text: str) -> str:
    """Collapse whitespace and drop markdown emphasis, as the other guards do."""
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", ""))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def headings(text: str) -> set[str]:
    return {
        line.rstrip()
        for line in text.splitlines()
        if re.match(r"^#{2,3} ", line)
    }


def tier_of(path: Path) -> str:
    m = re.search(r"^# tier: (\w+)$", read(path), re.M)
    return m.group(1) if m else ""


class VariantDriftTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.coder_raw = read(CODER)
        cls.dotnet_raw = read(DOTNET)
        cls.coder = norm(cls.coder_raw)
        cls.dotnet = norm(cls.dotnet_raw)

    # --- shared rules -----------------------------------------------------

    def test_shared_rules_are_present_in_both_variants(self) -> None:
        for name, anchor in SHARED_RULES.items():
            phrase = norm(anchor)
            with self.subTest(rule=name):
                self.assertIn(phrase, self.coder, f"pdca-coder lost the rule: {name}")
                self.assertIn(phrase, self.dotnet, f"pdca-dotnet lost the rule: {name}")

    # --- section ownership ------------------------------------------------

    def test_shared_sections_exist_in_both_variants(self) -> None:
        coder_heads = headings(self.coder_raw)
        dotnet_heads = headings(self.dotnet_raw)
        for section in SHARED_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, coder_heads, "missing in pdca-coder")
                self.assertIn(section, dotnet_heads, "missing in pdca-dotnet")

    def test_dotnet_only_sections_do_not_leak_into_coder(self) -> None:
        coder_heads = headings(self.coder_raw)
        for section in DOTNET_ONLY_SECTIONS:
            with self.subTest(section=section):
                self.assertNotIn(section, coder_heads)

    def test_dotnet_only_sections_are_declared_in_dotnet(self) -> None:
        dotnet_heads = headings(self.dotnet_raw)
        for section in DOTNET_ONLY_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, dotnet_heads)

    def test_one_approval_section_per_variant(self) -> None:
        # The PLAN → DO gate is stated once: a second section for it is a second
        # source of truth for the same rule.
        for name, text in (("pdca-coder", self.coder_raw), ("pdca-dotnet", self.dotnet_raw)):
            with self.subTest(variant=name):
                self.assertEqual(
                    1,
                    len(re.findall(r"^#+ .*(?:approval.*PLAN → DO|PLAN → DO.*(?:approval|transition))", text, re.M | re.I)),
                )

    # --- role parity ------------------------------------------------------

    def test_shared_roles_carry_the_same_tier_in_both_variants(self) -> None:
        for asset in sorted(p.name for p in CODER_AGENTS.glob("*.md")):
            coder_asset = CODER_AGENTS / asset
            dotnet_asset = DOTNET_AGENTS / asset
            if not dotnet_asset.exists():
                continue
            with self.subTest(asset=asset):
                self.assertEqual(tier_of(coder_asset), tier_of(dotnet_asset))

    def test_role_sets_match(self) -> None:
        coder_roles = {p.name for p in CODER_AGENTS.glob("*.md")}
        dotnet_roles = {p.name for p in DOTNET_AGENTS.glob("*.md")}
        self.assertEqual(coder_roles, dotnet_roles)

    def test_no_model_id_in_either_variant(self) -> None:
        for name, text in (("pdca-coder", self.coder_raw), ("pdca-dotnet", self.dotnet_raw)):
            with self.subTest(variant=name):
                self.assertNotRegex(text, r"(?m)^\s*model:")
                self.assertNotRegex(text, r"(?i)\b(opus|sonnet|haiku|gpt-4|gpt-5|deepseek-|claude-3|gemini-\d)")


if __name__ == "__main__":
    unittest.main()
