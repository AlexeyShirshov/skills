"""The cheap child-cycle dispatcher ships with the skill.

`pdca-incremental` delegates every step to `pdca-orchestrator`; the runner is a
portable asset, not a host artifact, so a fresh install can run a campaign.
Structural guards only: they parse the asset frontmatter and never execute an
agent.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
ASSET = SKILL_DIR / "assets/agents/pdca-orchestrator.md"
FAMILY_ROLES = (
    "pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate",
    "pdca-scout", "pdca-security-auditor",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RunnerAssetTest(unittest.TestCase):
    def test_runner_asset_is_shipped(self):
        self.assertTrue(ASSET.is_file(), "assets/agents/pdca-orchestrator.md missing")
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


if __name__ == "__main__":
    unittest.main()
