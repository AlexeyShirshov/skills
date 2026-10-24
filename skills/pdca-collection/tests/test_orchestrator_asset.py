"""The cheap child-cycle dispatcher ships with the skill.

The `pdca-collection` runner (`pdca-orchestrator`) is a portable asset, not a host
artifact: a fresh install must be able to run collection groups without writing
its own dispatcher. These guards are structural only — they parse the asset
frontmatter; they never execute an agent.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSET = SKILL_DIR / "assets/opencode-agents/pdca-orchestrator.md"
FAMILY_ROLES = (
    "pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate",
    "pdca-scout", "pdca-security-auditor",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RunnerAssetTest(unittest.TestCase):
    def test_runner_asset_is_shipped(self):
        self.assertTrue(ASSET.is_file(), "assets/opencode-agents/pdca-orchestrator.md missing")
        raw = read(ASSET)
        self.assertRegex(raw, r"(?m)^name: pdca-orchestrator\s*$")
        self.assertRegex(raw, r"(?m)^mode: subagent\s*$")

    def test_runner_is_cheap_and_carries_no_model(self):
        raw = read(ASSET)
        self.assertRegex(raw, r"(?m)^# tier: cheap\s*$")
        self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    def test_runner_is_a_dispatcher_not_a_worker(self):
        raw = read(ASSET)
        self.assertRegex(raw, r"(?m)^\s*edit: deny\s*$")
        self.assertRegex(raw, r"(?m)^\s*(bash|shell): deny\s*$")
        self.assertRegex(raw, r"(?m)^\s*write: deny\s*$")

    def test_runner_dispatches_every_family_role(self):
        raw = read(ASSET)
        for role in FAMILY_ROLES:
            with self.subTest(role=role):
                self.assertRegex(raw, r"(?m)^\s*%s: allow\s*$" % re.escape(role))

    def test_runner_keeps_the_subagent_default_deny(self):
        raw = read(ASSET)
        self.assertRegex(raw, r'(?ms)^\s*task:\n\s+"?\*"?:\s*deny$')

    def test_runner_declares_execution_kind_and_the_lane_mode(self):
        # AC01/AC11: one canonical runner serves both execution kinds; the mode is
        # an explicit field, never a second agent layer.
        raw = read(ASSET)
        for token in ("execution_kind", "collection-lane", "step orchestrator"):
            with self.subTest(token=token):
                self.assertIn(token, raw, f"asset lacks the mode token {token!r}")
        self.assertIn("dispatch", raw)
        self.assertTrue(
            "fail closed" in raw or "fail-closed" in raw,
            "asset must fail closed (or fail-closed) on an unknown execution kind",
        )

    def test_runner_adds_no_agent_layers_and_keeps_the_family_roles(self):
        raw = read(ASSET)
        self.assertIn(
            "execution_kind",
            raw,
            "the mode field and the no-extra-layer rule are one boundary (AC01)",
        )
        for layer in ("campaign-agent", "cycle-agent"):
            with self.subTest(layer=layer):
                self.assertNotIn(layer, raw, f"asset must not add the layer {layer!r}")
        self.assertNotRegex(raw, r"(?m)^\s*model\s*:")
        for role in ("pdca-planner", "pdca-executor", "pdca-check",
                     "pdca-escalate", "pdca-scout"):
            with self.subTest(role=role):
                self.assertIn(role, raw)


if __name__ == "__main__":
    unittest.main()
