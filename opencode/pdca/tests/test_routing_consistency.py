"""Static routing/structure guards for the universal `pdca` skill.

Structural only: these tests parse the role frontmatter/permission blocks, the
host profiles, the curated-skill list and AGENTS.md; they never execute a model
or the live cycle.

They prove: the four host roles exist, match their asset mirrors byte-for-byte,
carry only a `# tier:` label (never a `model:` field), and keep the intended
narrow permissions; the profiles bind the four new roles to the expected tier
models while leaving the existing keys intact; the shared RUNNER
`pdca-orchestrator` is asserted separately; the integration is additive.

Run:
    python3 -m unittest discover -s config/skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

SKILL = REPO / "config/skills/pdca/SKILL.md"
ASSET_AGENTS = REPO / "config/skills/pdca/assets/agents"
HOST_DIR = REPO / "config/agents"
PROFILES = REPO / "config/profiles"
SKILLS_KEEP = REPO / "config/skills-keep.txt"
AGENTS_MD = REPO / "config/AGENTS.md"
ORCHESTRATOR = REPO / "config/agents/pdca-orchestrator.md"

ROLE_TIER = {
    "pdca-planner": "medium",
    "pdca-check": "medium",
    "pdca-escalate": "strong",
    "pdca-executor": "cheap",
}

DEEPSEEK_NEW = {
    "pdca-planner": {"model": "opencode/gpt-6.1-sol", "variant": "high"},
    "pdca-check": {"model": "opencode/gpt-6.1-sol", "variant": "high"},
    "pdca-escalate": {"model": "opencode/claude-sonnet-5-5"},
    "pdca-executor": {"model": "deepseek/deepseek-flash"},
}
DEEPSEEK_EXISTING = {
    "architect": {"model": "opencode/gpt-6.1-sol", "variant": "high"},
    "planner": {"model": "opencode/gpt-6.1-sol", "variant": "high"},
    "check": {"model": "opencode/gpt-6.1-sol", "variant": "high"},
    "escalate": {"model": "opencode/claude-sonnet-5-5"},
    "security-auditor": {"model": "opencode/gpt-6.1-sol", "variant": "high"},
    "coder": {"model": "deepseek/deepseek-flash"},
    "scout": {"model": "deepseek/deepseek-flash"},
    "pdca-orchestrator": {"model": "deepseek/deepseek-flash"},
}
GP_EXISTING = (
    "architect", "planner", "check", "escalate", "security-auditor",
    "coder", "scout", "pdca-orchestrator",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_block(block: str) -> dict:
    """Tiny indentation parser for the flat/nested frontmatter subset used here."""
    root: dict = {}
    stack: list = [(-1, root)]
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, val = raw.strip().partition(":")
        key = key.strip().strip('"').strip("'")
        val = val.strip().strip('"').strip("'")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if val == "":
            stack[-1][1][key] = {}
            stack.append((indent, stack[-1][1][key]))
        else:
            stack[-1][1][key] = val
    return root


def frontmatter(path: Path) -> dict:
    text = read(path)
    if not text.startswith("---"):
        raise AssertionError("%s: no frontmatter" % path)
    end = text.find("\n---", 3)
    return _parse_block(text[3:end])


def load_jsonc(path: Path) -> dict:
    text = read(path)
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("//")]
    text = re.sub(r",(\s*[}\]])", r"\1", "\n".join(lines))
    return json.loads(text)


def allow_keys(mapping: dict) -> set:
    return {k for k, v in mapping.items() if v == "allow"}


class RoleParityTest(unittest.TestCase):
    def test_four_host_agents_exist(self):
        for name in ROLE_TIER:
            with self.subTest(role=name):
                self.assertTrue((HOST_DIR / ("%s.md" % name)).is_file())

    def test_frontmatter_name_equals_filename_stem(self):
        for name in ROLE_TIER:
            with self.subTest(role=name):
                data = frontmatter(HOST_DIR / ("%s.md" % name))
                self.assertEqual(name, data.get("name"))

    def test_each_role_carries_expected_tier_and_no_model(self):
        for name, tier in ROLE_TIER.items():
            with self.subTest(role=name):
                raw = read(HOST_DIR / ("%s.md" % name))
                self.assertRegex(raw, r"(?m)^# tier: %s\s*$" % tier)
                self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    def test_exactly_four_assets_with_same_names(self):
        assets = sorted(p.name for p in ASSET_AGENTS.glob("*.md"))
        expected = sorted("%s.md" % n for n in ROLE_TIER)
        self.assertEqual(expected, assets)

    def test_assets_are_byte_identical_to_host(self):
        for name in ROLE_TIER:
            with self.subTest(role=name):
                self.assertEqual(
                    read(HOST_DIR / ("%s.md" % name)),
                    read(ASSET_AGENTS / ("%s.md" % name)),
                    "%s host/asset differ" % name,
                )


class PermissionRoutingTest(unittest.TestCase):
    def test_planner_and_check_are_default_deny(self):
        for name in ("pdca-planner", "pdca-check"):
            with self.subTest(role=name):
                perm = frontmatter(HOST_DIR / ("%s.md" % name))["permission"]
                self.assertEqual("deny", perm.get("*"))

    def test_escalate_only_allows_scout(self):
        perm = frontmatter(HOST_DIR / "pdca-escalate.md")["permission"]
        task = perm["task"]
        self.assertEqual("deny", task.get("*"))
        self.assertEqual({"scout"}, allow_keys(task))


class ProfileBindingTest(unittest.TestCase):
    def test_deepseek_new_role_bindings(self):
        cfg = load_jsonc(PROFILES / "deepseek.jsonc")
        agents = cfg["agent"]
        for role, expected in DEEPSEEK_NEW.items():
            with self.subTest(role=role):
                self.assertEqual(expected, agents.get(role))

    def test_deepseek_existing_keys_unchanged(self):
        agents = load_jsonc(PROFILES / "deepseek.jsonc")["agent"]
        for role, expected in DEEPSEEK_EXISTING.items():
            with self.subTest(role=role):
                self.assertEqual(expected, agents.get(role))

    def test_gp_new_roles_and_existing_keys(self):
        agents = load_jsonc(PROFILES / "gp.jsonc")["agent"]
        for role in list(DEEPSEEK_NEW) + list(GP_EXISTING):
            with self.subTest(role=role):
                self.assertEqual({"model": "opencode-go/kimi-k3"}, agents.get(role))


class AdditiveIntegrationTest(unittest.TestCase):
    def test_skills_keep_has_pdca_and_pdca_coder(self):
        lines = {
            ln.strip() for ln in read(SKILLS_KEEP).splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        }
        self.assertIn("pdca", lines)
        self.assertIn("pdca-coder", lines)

    def test_agents_md_has_explicit_pdca_and_keeps_old_triggers(self):
        text = read(AGENTS_MD)
        self.assertIn("skill pdca", text)
        self.assertIn("pdca-coder", text)
        self.assertIn("pdca-dotnet", text)


class OrchestratorVariantSelectionTest(unittest.TestCase):
    """The shared cheap driver `pdca-orchestrator` picks the cycle variant per task."""

    UNIVERSAL_ROLES = ("pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate")

    def test_orchestrator_exists(self):
        self.assertTrue(ORCHESTRATOR.is_file())

    def test_orchestrator_task_allowlist_covers_universal_roles(self):
        perm = frontmatter(ORCHESTRATOR)["permission"]
        task = perm["task"]
        self.assertEqual("deny", task.get("*"))
        for role in self.UNIVERSAL_ROLES:
            with self.subTest(role=role):
                self.assertEqual("allow", task.get(role))


class SkillFrontmatterTest(unittest.TestCase):
    def test_skill_frontmatter_name_is_pdca(self):
        text = read(SKILL)
        end = text.find("\n---", 3)
        data = _parse_block(text[3:end])
        self.assertEqual("pdca", data.get("name"))


if __name__ == "__main__":
    unittest.main()
