"""The in-skill agent prompt: complete, single-source, and wired into the skill and the docs.

`npx skills add` copies a skill directory and nothing else — it has no post-install hook and no
notion of a host subagent — so the role agents are never installed by the CLI.  The automation lives
inside the skill instead: the base `pdca` preflights the roles before its first dispatch and, when
one does not resolve, hands the user `assets/install-agents-prompt.md`, which ships with the skill
and covers the copy, the tier bindings and the verification for OpenCode and Claude Code.

These guards keep that prompt honest:

* every role shipped in `assets/opencode-agents/` is named in it, so a new role cannot be forgotten;
* it keeps the facts a host adapter needs — both OpenCode roots, both OpenCode config forms, the
  Claude Code roots and frontmatter — and the refusal rules (no invented `model:`, no invented keys);
* the Claude Code tool allowlist per role is parsed from the shipped table and checked for the
  boundaries that matter: a read-only PLAN/CHECK, a shell only where the role needs it, and `Agent`
  exactly on the two delegating roles;
* it exists once, in the base skill (the overlays are mirrors, not second sources);
* `SKILL.md` points at it and stops before work instead of substituting a missing role;
* the install docs point at it, so nobody hunts for a copy command.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "skills/pdca"
PROMPT = SKILL / "assets/install-agents-prompt.md"
ROLE_DIR = SKILL / "assets/opencode-agents"

DOCS = ("README.md", "docs/install.md", "docs/ru/install.md", "docs/install-prompt.md")

# `| `pdca-scout` | cheap | `Read, Grep, Glob, Bash` |` — the Claude Code mapping table.
TABLE_ROW = re.compile(r"^\s*\|\s*`(pdca-[a-z-]+)`\s*\|\s*([a-z]+)\s*\|\s*`([^`]*)`\s*\|\s*$", re.M)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


class PromptAssetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(PROMPT.is_file(), "missing %s" % PROMPT)
        self.raw = read(PROMPT)
        self.text = norm(self.raw)
        self.table = {
            role: [tool.strip() for tool in tools.split(",") if tool.strip()]
            for role, _tier, tools in TABLE_ROW.findall(self.raw)
        }

    def test_prompt_is_a_copy_paste_block(self) -> None:
        blocks = re.findall(r"```[a-z]*\n(.*?)```", self.raw, re.S)
        self.assertGreaterEqual(len(blocks), 2, "expected a Context block and a prompt block")
        self.assertIn("You are installing or refreshing", self.raw)

    def test_every_shipped_role_is_named(self) -> None:
        roles = sorted(path.stem for path in ROLE_DIR.glob("*.md"))
        self.assertTrue(roles, "no role assets found in %s" % ROLE_DIR)
        missing = [role for role in roles if role not in self.text]
        self.assertEqual([], missing, "install prompt omits roles: %s" % ", ".join(missing))

    def test_specialist_is_sourced_from_the_overlay(self) -> None:
        self.assertIn("pdca-security-auditor", self.text)
        self.assertIn("pdca-coder", self.text)
        self.assertIn("pdca-dotnet", self.text)

    def test_host_roots_are_present(self) -> None:
        for root in ("~/.config/opencode/agents", ".opencode/agents", "~/.claude/agents"):
            with self.subTest(root=root):
                self.assertIn(root, self.text)

    def test_both_opencode_config_forms_are_present(self) -> None:
        for token in (
            "experimental.subagent_depth",
            "subagent_depth",
            "permission.task",
            '"pdca-*": "allow"',
            "action `subagent`",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_tier_bindings_are_covered_for_both_hosts(self) -> None:
        for token in ("cheap = pdca-scout", "medium = pdca-planner", "strong = pdca-escalate"):
            with self.subTest(token=token):
                self.assertIn(token, self.text)
        # OpenCode: a commented JSONC profile map, edited as text
        self.assertIn("profiles/", self.text)
        self.assertIn("JSONC", self.text)
        self.assertRegex(self.text, r"keep every comment")
        # Claude Code: the model field of the translated file is the binding
        self.assertIn("There is no separate profile map", self.text)
        self.assertIn("CLAUDE_CODE_SUBAGENT_MODEL_FORCE", self.text)
        self.assertIn("an alias (sonnet, opus, haiku, fable)", self.text)

    def test_codex_schema_is_covered(self) -> None:
        for token in (
            "$CODEX_HOME/agents",
            ".codex/agents",
            "developer_instructions",
            "features.shell_tool = false",
            "model_reasoning_effort",
            "escape every backslash",
            "has no permission map",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_codex_does_not_invent_a_depth_key(self) -> None:
        self.assertIn("has no nesting-depth key", self.text)
        self.assertIn("agents.max_spawn_depth", self.text)
        self.assertIn("Do not invent it", self.text)
        # the custom agent file cannot override the parent's sandbox/provider
        self.assertIn("cannot set `sandbox_mode`", self.text)
        self.assertIn("ignores them there", self.text)

    def test_claude_nesting_and_verification_are_covered(self) -> None:
        for token in (
            "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH",
            "`Agent` (older builds call it `Task`",
            "claude plugin validate",
            "`/tasks` shows the model",
            "`/agents` lists the subagents",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_claude_keeps_no_opencode_frontmatter(self) -> None:
        # A leftover permission map would look enforced while Claude Code ignores it.
        self.assertIn("Drop `mode`, `permission`, `permissions` and `steps`", self.text)
        self.assertIn("unknown fields silently", self.text)
        self.assertIn("would inherit every tool", self.text)

    def test_refusal_rules_are_present(self) -> None:
        self.assertIn("no `model:` in a shipped role file", self.text)
        self.assertIn("Do not invent anything", self.text)
        self.assertRegex(self.text, r"stop and ask")
        self.assertIn("back it up first", self.text)

    def test_the_prompt_has_one_home(self) -> None:
        copies = sorted(
            path.relative_to(REPO).as_posix()
            for path in REPO.glob("skills/pdca*/assets/install-agents-prompt.md")
        )
        self.assertEqual(["skills/pdca/assets/install-agents-prompt.md"], copies)


class ClaudeToolTableTest(unittest.TestCase):
    """The parsed table is the source of the translated `tools:` lists."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(PROMPT)
        cls.table = {
            role: set(tool.strip() for tool in tools.split(",") if tool.strip())
            for role, _tier, tools in TABLE_ROW.findall(cls.raw)
        }
        cls.tiers = {
            role: tier for role, tier, _tools in TABLE_ROW.findall(cls.raw)
        }

    def test_table_covers_every_shipped_role(self) -> None:
        shipped = sorted(
            {
                path.stem
                for path in REPO.glob("skills/pdca*/assets/opencode-agents/*.md")
            }
        )
        self.assertEqual(shipped, sorted(self.table))

    def test_read_only_roles_have_no_shell_and_no_write(self) -> None:
        for role in ("pdca-planner", "pdca-check", "pdca-security-auditor"):
            with self.subTest(role=role):
                tools = self.table[role]
                self.assertIn("Read", tools)
                self.assertFalse(tools & {"Bash", "Edit", "Write", "Agent"}, sorted(tools))

    def test_executor_can_work(self) -> None:
        self.assertTrue(
            {"Read", "Write", "Edit", "Bash"}.issubset(self.table["pdca-executor"]),
            sorted(self.table["pdca-executor"]),
        )

    def test_scout_keeps_its_read_only_shell(self) -> None:
        tools = self.table["pdca-scout"]
        self.assertIn("Bash", tools)
        self.assertFalse(tools & {"Edit", "Write", "Agent"}, sorted(tools))

    def test_driver_dispatches_without_working(self) -> None:
        tools = self.table["pdca-orchestrator"]
        self.assertIn("Agent", tools)
        self.assertFalse(tools & {"Bash", "Edit", "Write"}, sorted(tools))

    def test_only_the_two_delegating_roles_may_spawn(self) -> None:
        spawning = sorted(role for role, tools in self.table.items() if "Agent" in tools)
        self.assertEqual(["pdca-escalate", "pdca-orchestrator"], spawning)

    def test_tiers_match_the_role_contract(self) -> None:
        self.assertEqual(
            {
                "pdca-scout": "cheap",
                "pdca-executor": "cheap",
                "pdca-orchestrator": "cheap",
                "pdca-planner": "medium",
                "pdca-check": "medium",
                "pdca-security-auditor": "medium",
                "pdca-escalate": "strong",
            },
            self.tiers,
        )


class SkillWiringTest(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = norm(read(SKILL / "SKILL.md"))

    def test_skill_points_at_the_prompt(self) -> None:
        self.assertIn("assets/install-agents-prompt.md", self.skill)

    def test_preflight_stops_instead_of_substituting(self) -> None:
        self.assertIn("stop before any work", self.skill)
        self.assertIn("do not install agents silently", self.skill)
        self.assertIn("is a **resource blocker**", self.skill)
        # the preflight is a lookup, never work of its own
        self.assertIn("never a probe task", self.skill)

    def test_skill_stays_host_agnostic(self) -> None:
        self.assertNotIn("~/.config/opencode", self.skill)
        self.assertNotIn(".opencode/agents", self.skill)
        self.assertNotIn("~/.claude", self.skill)
        self.assertNotIn("tools:", self.skill)


class DocsPointerTest(unittest.TestCase):
    def test_install_docs_point_at_the_shipped_prompt(self) -> None:
        for rel in DOCS:
            with self.subTest(doc=rel):
                self.assertIn("install-agents-prompt.md", read(REPO / rel))

    def test_docs_explain_why_it_is_a_prompt(self) -> None:
        english = norm(read(REPO / "docs/install.md"))
        russian = norm(read(REPO / "docs/ru/install.md"))
        self.assertRegex(english, r"prompt, not an installer script")
        self.assertIn("Промпт, а не скрипт установки", russian)

    def test_install_docs_describe_the_codex_adapter(self) -> None:
        for rel in ("docs/install.md", "docs/ru/install.md"):
            with self.subTest(doc=rel):
                text = norm(read(REPO / rel))
                self.assertIn("developer_instructions", text)
                self.assertIn(".codex/agents", text)
                self.assertIn("features.shell_tool", text)

    def test_install_docs_describe_the_claude_adapter(self) -> None:
        for rel in ("docs/install.md", "docs/ru/install.md"):
            with self.subTest(doc=rel):
                text = norm(read(REPO / rel))
                self.assertIn("CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH", text)
                self.assertIn("pdca-orchestrator", text)


if __name__ == "__main__":
    unittest.main()
