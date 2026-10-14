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
    python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]

SKILL = SKILL_DIR / "SKILL.md"
ASSET_AGENTS = SKILL_DIR / "assets/agents"

# Host config (agents/profiles/AGENTS.md/skills-keep) lives in the `opencode-config` repo,
# not in this one. Point at it with OPENCODE_CONFIG_REPO to enable host-parity checks;
# they skip by default.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"

HOST_DIR = (CONFIG / "agents") if CONFIG else None
PROFILES = (CONFIG / "profiles") if CONFIG else None
SKILLS_KEEP = (CONFIG / "skills-keep.txt") if CONFIG else None
AGENTS_MD = (CONFIG / "AGENTS.md") if CONFIG else None
ORCHESTRATOR = (CONFIG / "agents/pdca-orchestrator.md") if CONFIG else None

ROLE_TIER = {
    "pdca-planner": "medium",
    "pdca-check": "medium",
    "pdca-escalate": "strong",
    "pdca-executor": "cheap",
}
# The skill also ships the shared gatherer `scout` as a portable asset (flat name,
# cheap tier) alongside the four cycle roles.
ASSET_TIER = dict(ROLE_TIER, scout="cheap")

# The universal roles mirror the host roles' routing: `pdca-<role>` binds the
# same model/variant as its host counterpart. Asserted against the profiles
# themselves, so the shared skill names no concrete model id.
PDCA_MIRROR = {
    "pdca-planner": "planner",
    "pdca-check": "check",
    "pdca-escalate": "escalate",
    "pdca-executor": "coder",
}
HOST_ROLES = (
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
    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_four_host_agents_exist(self):
        for name in ROLE_TIER:
            with self.subTest(role=name):
                self.assertTrue((HOST_DIR / ("%s.md" % name)).is_file())

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_frontmatter_name_equals_filename_stem(self):
        for name in ROLE_TIER:
            with self.subTest(role=name):
                data = frontmatter(HOST_DIR / ("%s.md" % name))
                self.assertEqual(name, data.get("name"))

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_each_role_carries_expected_tier_and_no_model(self):
        for name, tier in ROLE_TIER.items():
            with self.subTest(role=name):
                raw = read(HOST_DIR / ("%s.md" % name))
                self.assertRegex(raw, r"(?m)^# tier: %s\s*$" % tier)
                self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    def test_assets_are_the_four_roles_plus_scout(self):
        assets = sorted(p.name for p in ASSET_AGENTS.glob("*.md"))
        expected = sorted("%s.md" % n for n in ASSET_TIER)
        self.assertEqual(expected, assets)

    def test_each_asset_carries_expected_tier_and_no_model(self):
        for name, tier in ASSET_TIER.items():
            with self.subTest(role=name):
                path = ASSET_AGENTS / ("%s.md" % name)
                self.assertTrue(path.is_file(), "%s missing" % name)
                self.assertEqual(name, frontmatter(path).get("name"))
                raw = read(path)
                self.assertRegex(raw, r"(?m)^# tier: %s\s*$" % tier)
                self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_assets_match_host_except_external_directory(self):
        # The portable asset mirrors the host agent's body and settings, but must
        # not carry the host-specific `external_directory` (local-env paths).
        for name in ROLE_TIER:
            with self.subTest(role=name):
                host = read(HOST_DIR / ("%s.md" % name))
                asset = read(ASSET_AGENTS / ("%s.md" % name))
                self.assertEqual(
                    host.split("\n---\n", 1)[1],
                    asset.split("\n---\n", 1)[1],
                    "%s host/asset body differ" % name,
                )
                hperm = frontmatter(HOST_DIR / ("%s.md" % name))["permission"]
                aperm = frontmatter(ASSET_AGENTS / ("%s.md" % name))["permission"]
                self.assertNotIn("external_directory", aperm)
                self.assertEqual(
                    {k: v for k, v in hperm.items() if k != "external_directory"},
                    {k: v for k, v in aperm.items() if k != "external_directory"},
                    "%s host/asset settings differ" % name,
                )


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
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


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class ProfileBindingTest(unittest.TestCase):
    def test_deepseek_pdca_roles_mirror_host_routing(self):
        agents = load_jsonc(PROFILES / "deepseek.jsonc")["agent"]
        for role, host in PDCA_MIRROR.items():
            with self.subTest(role=role):
                spec = agents.get(role)
                self.assertIsInstance(spec, dict)
                self.assertTrue(spec.get("model"), "%s has no model" % role)
                self.assertEqual(spec.get("model"), (agents.get(host) or {}).get("model"))
                self.assertEqual(spec.get("variant"), (agents.get(host) or {}).get("variant"))

    def test_deepseek_existing_roles_keep_a_model(self):
        agents = load_jsonc(PROFILES / "deepseek.jsonc")["agent"]
        for role in HOST_ROLES:
            with self.subTest(role=role):
                self.assertTrue((agents.get(role) or {}).get("model"), "%s has no model" % role)

    def test_gp_roles_keep_a_model(self):
        agents = load_jsonc(PROFILES / "gp.jsonc")["agent"]
        for role in list(PDCA_MIRROR) + list(HOST_ROLES):
            with self.subTest(role=role):
                self.assertTrue((agents.get(role) or {}).get("model"), "%s has no model" % role)


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
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


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
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
