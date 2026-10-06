"""Static routing/structure guards for the pdca-coder skill.

Structural only: these tests parse the role-asset frontmatter and assert each
role carries a `# tier:` label (no `model:`).  They never execute a model or the
live PDCA cycle, so they prove structure, not behavior.

Run:
    python3 -m unittest discover -s config/skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PDCA_DIR = REPO / "config/skills/pdca-coder"
SKILL = PDCA_DIR / "SKILL.md"
ASSET_AGENTS = PDCA_DIR / "assets/agents"

ROLE_TIER = {
    "planner": "medium",
    "coder": "cheap",
    "check": "medium",
    "scout": "cheap",
    "escalate": "strong",
    "security-auditor": "medium",
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
        planner = frontmatter(ASSET_AGENTS / "planner.md")["permission"]
        check = frontmatter(ASSET_AGENTS / "check.md")["permission"]
        coder = frontmatter(ASSET_AGENTS / "coder.md")["permission"]
        scout = frontmatter(ASSET_AGENTS / "scout.md")["permission"]
        escalate = frontmatter(ASSET_AGENTS / "escalate.md")["permission"]
        sec = frontmatter(ASSET_AGENTS / "security-auditor.md")["permission"]

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
        self.assertEqual({"scout"}, allowed)
        self.assertEqual("deny", sec.get("*"))


class LensSelectionWordingTest(unittest.TestCase):
    def test_lenses_are_selected_per_task(self):
        skill = norm(read(SKILL))
        self.assertIn("PLAN selects the toolchain and lenses", skill)
        self.assertIn("selected by PLAN for each", skill)
        self.assertIn("explicit generic-role path", skill)
        self.assertIn("missing optional lens", skill)

    def test_no_mandatory_stack_lens_wording(self):
        skill = read(SKILL).lower()
        self.assertNotIn(STACK_LENS, skill)
        self.assertNotIn("mandatory stack", skill)
        self.assertNotIn("stack-specific specialist is mandatory", skill)


if __name__ == "__main__":
    unittest.main()
