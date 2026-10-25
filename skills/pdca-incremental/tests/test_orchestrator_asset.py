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

    def test_runner_declares_the_form_and_the_family_contexts(self):
        # One canonical runner serves every form; `form=cycle` / `form=campaign`
        # and the overlay are explicit inputs, never a second agent layer.
        raw = read(ASSET)
        for token in ("form=cycle", "form=campaign", "overlay",
                      "campaign-control", "cycle-control", "collection-lane"):
            with self.subTest(token=token):
                self.assertIn(token, raw, f"asset lacks the scope token {token!r}")
        self.assertIn("dispatch", raw)
        self.assertTrue(
            "fail closed" in raw or "fail-closed" in raw,
            "asset must fail closed on an unresolvable contract",
        )

    def test_runner_carries_no_legacy_routing_fields(self):
        raw = read(ASSET)
        for legacy in ("execution_kind", "selected_variant"):
            with self.subTest(legacy=legacy):
                self.assertNotIn(
                    legacy, raw,
                    f"the asset still routes on the removed field {legacy!r}",
                )

    def test_runner_holds_the_campaign_inline_and_routes_the_stop(self):
        raw = read(ASSET)
        self.assertIn("inline in your own session", raw)
        self.assertIn("The next step starts **only on the planner's decision**", raw)
        self.assertIn("record the STOP **without a new planner call**", raw)

    def test_runner_invents_no_baseline_at_preparation(self):
        raw = read(ASSET)
        self.assertRegex(raw, r"Do \*\*not\*\*\s+require or invent a baseline")
        self.assertIn("preparation_handoff", raw)

    def test_runner_adds_no_agent_layers_and_keeps_the_family_roles(self):
        raw = read(ASSET)
        self.assertIn(
            "campaign-control",
            raw,
            "the campaign context and the no-extra-layer rule are one boundary",
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
