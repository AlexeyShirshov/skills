"""The in-skill agent prompt: complete, single-source, and wired into the skill and the docs.

`npx skills add` copies a skill directory and nothing else — it has no post-install hook and no
notion of a host subagent — so the role agents are never installed by the CLI.  The automation lives
inside the skill instead: the base `pdca` preflights the roles before its first dispatch and, when
one does not resolve, hands the user `assets/install-agents-prompt.md`.  The mechanical conversion is
generated and checked in (`claude-agents/`, `codex-agents/`, guarded by
`test_host_agent_artifacts.py`), so the prompt only copies files and binds models.

These guards keep that prompt honest:

* every role shipped in any package is named in it, so a new role cannot be forgotten;
* it keeps the facts a host adapter needs — the three shipped sets, the roots, both OpenCode config
  forms, the Claude Code and Codex model-binding rules — and the refusal rules;
* it copies the shipped set instead of translating at install time;
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

DOCS = ("README.md", "docs/install.md", "docs/ru/install.md", "docs/install-prompt.md")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


def shipped_roles() -> list[str]:
    return sorted(
        {path.stem for path in REPO.glob("skills/pdca*/assets/opencode-agents/*.md")}
    )


class PromptAssetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(PROMPT.is_file(), "missing %s" % PROMPT)
        self.raw = read(PROMPT)
        self.text = norm(self.raw)

    def test_prompt_is_a_copy_paste_block(self) -> None:
        blocks = re.findall(r"```[a-z]*\n(.*?)```", self.raw, re.S)
        self.assertGreaterEqual(len(blocks), 2, "expected a Context block and a prompt block")
        self.assertIn("You are installing or refreshing", self.raw)

    def test_every_shipped_role_is_named(self) -> None:
        roles = shipped_roles()
        self.assertTrue(roles)
        missing = [role for role in roles if role not in self.text]
        self.assertEqual([], missing, "install prompt omits roles: %s" % ", ".join(missing))

    def test_specialist_is_sourced_from_the_overlay(self) -> None:
        self.assertIn("pdca-security-auditor", self.text)
        self.assertIn("pdca-coder", self.text)
        self.assertIn("pdca-dotnet", self.text)

    def test_the_three_shipped_sets_are_named(self) -> None:
        for folder in ("opencode-agents", "claude-agents", "codex-agents"):
            with self.subTest(folder=folder):
                self.assertIn(folder, self.text)

    def test_host_roots_are_present(self) -> None:
        for root in (
            "~/.config/opencode/agents",
            ".opencode/agents",
            "~/.claude/agents",
            "$CODEX_HOME/agents",
            ".codex/agents",
        ):
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

    def test_tier_bindings_are_covered_for_every_host(self) -> None:
        for token in ("cheap = pdca-scout", "medium = pdca-planner", "strong = pdca-escalate"):
            with self.subTest(token=token):
                self.assertIn(token, self.text)
        # OpenCode: a commented JSONC profile map, edited as text
        self.assertIn("profiles/", self.text)
        self.assertIn("JSONC", self.text)
        self.assertRegex(self.text, r"keep every comment")
        # Claude Code: the model field of the copied file is the binding
        self.assertIn("There is no separate profile map", self.text)
        self.assertIn("CLAUDE_CODE_SUBAGENT_MODEL_FORCE", self.text)
        self.assertIn("an alias (sonnet, opus, haiku, fable)", self.text)
        # Codex: model and effort keys in the TOML file
        self.assertIn("model_reasoning_effort", self.text)
        self.assertIn("[agents] default_subagent_model", self.text)

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

    def test_codex_schema_is_covered(self) -> None:
        for token in (
            "developer_instructions",
            "features.shell_tool = false",
            "model_reasoning_effort",
            "has no per-agent edit switch",
            "cannot set `sandbox_mode`",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.text)
        self.assertIn("has no nesting-depth key", self.text)
        self.assertIn("agents.max_spawn_depth", self.text)
        self.assertIn("Do not invent it", self.text)

    def test_the_prompt_copies_instead_of_translating(self) -> None:
        self.assertIn("Copy every file of the host's set unchanged", self.text)
        self.assertIn("Do not translate, rewrite, reformat", self.text)
        self.assertNotIn("write a translated copy", self.text)
        # the generator owns the conversion, and the prompt says what a refresh must re-apply
        self.assertIn("must re-apply `model`", self.text)

    def test_refusal_rules_are_present(self) -> None:
        self.assertIn("no `model:` in a copied file", self.text)
        self.assertIn("Do not invent anything", self.text)
        self.assertRegex(self.text, r"stop and ask")
        self.assertIn("back it up first", self.text)

    def test_the_prompt_has_one_home(self) -> None:
        copies = sorted(
            path.relative_to(REPO).as_posix()
            for path in REPO.glob("skills/pdca*/assets/install-agents-prompt.md")
        )
        self.assertEqual(["skills/pdca/assets/install-agents-prompt.md"], copies)


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
        for token in ("~/.config/opencode", ".opencode/agents", "~/.claude", "tools:"):
            with self.subTest(token=token):
                self.assertNotIn(token, self.skill)


class DocsPointerTest(unittest.TestCase):
    def test_install_docs_point_at_the_shipped_prompt(self) -> None:
        for rel in DOCS:
            with self.subTest(doc=rel):
                self.assertIn("install-agents-prompt.md", read(REPO / rel))

    def test_docs_explain_why_it_is_a_prompt(self) -> None:
        english = norm(read(REPO / "docs/install.md"))
        russian = norm(read(REPO / "docs/ru/install.md"))
        self.assertRegex(english, r"prompt, not an installer script|prompt and not a script")
        self.assertIn("Промпт, а не скрипт установки", russian)

    def test_install_docs_describe_the_generated_sets(self) -> None:
        for rel in ("docs/install.md", "docs/ru/install.md"):
            with self.subTest(doc=rel):
                text = norm(read(REPO / rel))
                self.assertIn("claude-agents", text)
                self.assertIn("codex-agents", text)
                self.assertIn("gen_host_agents.py", text)

    def test_install_docs_describe_the_claude_adapter(self) -> None:
        for rel in ("docs/install.md", "docs/ru/install.md"):
            with self.subTest(doc=rel):
                text = norm(read(REPO / rel))
                self.assertIn("CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH", text)
                self.assertIn("pdca-orchestrator", text)

    def test_install_docs_describe_the_codex_adapter(self) -> None:
        for rel in ("docs/install.md", "docs/ru/install.md"):
            with self.subTest(doc=rel):
                text = norm(read(REPO / rel))
                self.assertIn("developer_instructions", text)
                self.assertIn(".codex/agents", text)
                self.assertIn("features.shell_tool", text)


if __name__ == "__main__":
    unittest.main()
