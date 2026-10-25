"""Static routing/structure guards for the pdca-coder skill.

Structural only: these tests parse the role-asset frontmatter and assert each
role carries a `# tier:` label (no `model:`).  They never execute a model or the
live PDCA cycle, so they prove structure, not behavior.

Run:
    python3 -m unittest discover -s skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"
ASSET_AGENTS = SKILL_DIR / "assets/opencode-agents"

ROLE_TIER = {
    "pdca-planner": "medium",
    "pdca-executor": "cheap",
    "pdca-check": "medium",
    "pdca-scout": "cheap",
    "pdca-escalate": "strong",
    "pdca-security-auditor": "medium",
}

def _cat(*fragments):
    """Runtime join (no compile-time folding into a bytecode literal)."""
    return "".join(fragments)


# The stack token that must never be required as a mandatory lens.
STACK_LENS = _cat("dot", "net-")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip()


def _parse_block(block: str) -> dict:
    """Tiny indentation parser for the flat/sub-map frontmatter subset used here."""
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


class RoleAssetTest(unittest.TestCase):
    def test_six_assets_exist(self):
        for name in ROLE_TIER:
            with self.subTest(role=name):
                self.assertTrue((ASSET_AGENTS / ("%s.md" % name)).exists())

    def test_each_asset_has_tier_label_and_no_model(self):
        for name, tier in ROLE_TIER.items():
            with self.subTest(role=name):
                raw = read(ASSET_AGENTS / ("%s.md" % name))
                self.assertRegex(raw, r"(?m)^# tier: %s\s*$" % tier)
                self.assertNotRegex(raw, r"(?m)^\s*#\s*model\s*:")

    def test_permission_blocks_are_wellformed(self):
        for name in ROLE_TIER:
            with self.subTest(role=name):
                data = frontmatter(ASSET_AGENTS / ("%s.md" % name))
                self.assertIn("permission", data)
                self.assertIsInstance(data["permission"], dict)
                self.assertTrue(data["permission"])

    def test_permission_roles_stay_narrow(self):
        planner = frontmatter(ASSET_AGENTS / "pdca-planner.md")["permission"]
        check = frontmatter(ASSET_AGENTS / "pdca-check.md")["permission"]
        coder = frontmatter(ASSET_AGENTS / "pdca-executor.md")["permission"]
        scout = frontmatter(ASSET_AGENTS / "pdca-scout.md")["permission"]
        escalate = frontmatter(ASSET_AGENTS / "pdca-escalate.md")["permission"]
        sec = frontmatter(ASSET_AGENTS / "pdca-security-auditor.md")["permission"]

        self.assertEqual("deny", planner.get("*"))
        self.assertNotIn("task", planner)
        self.assertEqual("deny", check.get("*"))
        self.assertNotIn("task", check)
        self.assertEqual("allow", coder.get("edit"))
        self.assertEqual("allow", coder.get("bash"))
        self.assertEqual("deny", scout.get("edit"))
        self.assertEqual("deny", scout.get("task"))
        self.assertEqual("deny", escalate.get("*"))
        self.assertEqual("deny", escalate["task"].get("*"))
        allowed = {k for k, v in escalate["task"].items() if v == "allow"}
        self.assertEqual({"pdca-scout"}, allowed)
        self.assertEqual("deny", sec.get("*"))

    def test_check_may_read_only_the_cycle_evidence(self):
        # The description and §CHECK promise a scoped read of the cycle's own evidence
        # (status + frozen manifest), never product code — the permissions must grant it.
        check = frontmatter(ASSET_AGENTS / "pdca-check.md")["permission"]
        self.assertEqual("deny", check.get("*"))
        for tool in ("read", "glob", "list"):
            with self.subTest(tool=tool):
                self.assertIn(tool, check)
                allowed = {k for k, v in check[tool].items() if v == "allow"}
                self.assertEqual({".pdca/**"}, allowed)
        self.assertNotIn("bash", check)
        self.assertNotIn("edit", check)
        self.assertNotIn("write", check)


class LensSelectionWordingTest(unittest.TestCase):
    def test_lenses_are_selected_per_task(self):
        skill = norm(read(SKILL))
        self.assertIn("the toolchain and the review lenses are selected by PLAN", skill)
        self.assertIn("selected by PLAN for each", skill)
        self.assertIn("explicit generic-role path", skill)
        self.assertIn("missing optional lens", skill)

    def test_no_mandatory_stack_lens_wording(self):
        skill = read(SKILL).lower()
        self.assertNotIn(STACK_LENS, skill)
        self.assertNotIn("mandatory stack", skill)
        self.assertNotIn("stack-specific specialist is mandatory", skill)


RUNNER_ASSET = ASSET_AGENTS / "pdca-orchestrator.md"
# Assembled at runtime: the stack-token guard must not match this test file.
DOTNET_LENS = _cat("dot", "net-*")
DOCS_SPECIALIST = _cat("doc", "fx-specialist")


class RunnerAssetTest(unittest.TestCase):
    """The cheap child-cycle dispatcher ships with the skill."""

    def test_runner_asset_is_shipped(self):
        self.assertTrue(RUNNER_ASSET.is_file(), "assets/opencode-agents/pdca-orchestrator.md missing")
        data = frontmatter(RUNNER_ASSET)
        self.assertEqual("pdca-orchestrator", data.get("name"))
        self.assertEqual("subagent", data.get("mode"))

    def test_runner_is_cheap_and_carries_no_model(self):
        raw = read(RUNNER_ASSET)
        self.assertRegex(raw, r"(?m)^# tier: cheap\s*$")
        self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    def test_runner_is_a_dispatcher(self):
        perm = frontmatter(RUNNER_ASSET)["permission"]
        self.assertEqual("deny", perm.get("edit"))
        self.assertEqual("deny", perm.get("bash"))
        allowed = {k for k, v in perm["task"].items() if v == "allow"}
        self.assertEqual(
            {"pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate",
             "pdca-scout", "pdca-security-auditor", DOCS_SPECIALIST, DOTNET_LENS},
            allowed,
        )


if __name__ == "__main__":
    unittest.main()
