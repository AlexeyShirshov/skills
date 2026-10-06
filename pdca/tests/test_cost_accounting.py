"""Cost-accounting guards for the universal `pdca` skill.

These tests import the read-only aggregation script as a module and feed it a
small, secret-free, in-memory fixture: the known universal roles plus one unknown
role.  They assert the generic classification (unknown stays explicitly
`unclassified`, no name-prefix inference), that no session is dropped, that the
per-group totals reconcile with the overall totals, and that the session-tree
walk resolves a root plus its descendants.

Run:
    python3 -m unittest discover -s config/skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SCRIPT = REPO / "config/skills/pdca/scripts/pdca_cost.py"
PROFILES = REPO / "config/profiles"
AGENTS = REPO / "config/agents"

# Universal roles -> phase (the generic `classify` table).
ROLE_PHASE = {
    "pdca-orchestrator": "orchestrator",
    "pdca-planner": "PLAN",
    "pdca-executor": "DO",
    "pdca-check": "CHECK",
    "pdca-escalate": "ESCALATE",
}
# Model (basename) -> tier, as derived from profiles + `# tier:` labels.
MODEL_TIER = {
    "gpt-6.1-sol": "medium",
    "claude-sonnet-5-5": "strong",
    "deepseek-flash": "cheap",
}
UNKNOWN_ROLE = "mystery-role"


def load_module():
    spec = importlib.util.spec_from_file_location("pdca_cost_under_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(index, agent, cost=1.0, parent=None, model=None):
    """A minimal, secret-free session record (same keys as a session row)."""
    return {
        "id": "s%d" % index,
        "parent": parent,
        "agent": agent,
        "title": agent,
        "model": model,
        "cost": cost,
        "ti": 1,
        "to": 1,
        "tr": 0,
        "tcr": 0,
        "tcw": 0,
        "t": 0,
    }


class CostAccountingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()
        cls.records = [
            record(i, agent, cost=0.25 * (i + 1))
            for i, agent in enumerate(list(ROLE_PHASE) + [UNKNOWN_ROLE])
        ]

    def test_module_loads(self):
        self.assertTrue(hasattr(self.mod, "summarize"))
        self.assertTrue(hasattr(self.mod, "UNCLASSIFIED"))

    def test_known_roles_classify_to_expected_phases(self):
        for role, phase in ROLE_PHASE.items():
            with self.subTest(role=role):
                self.assertEqual(phase, self.mod.classify(role))
                self.assertNotEqual(self.mod.UNCLASSIFIED, self.mod.phase_of(role))

    def test_models_derive_expected_tiers(self):
        tiers = self.mod.load_tiers(str(PROFILES), str(AGENTS))
        for model, tier in MODEL_TIER.items():
            with self.subTest(model=model):
                self.assertEqual(tier, tiers.get(model))

    def test_tier_grouping_uses_the_resolved_table(self):
        self.mod.TIERS.update(self.mod.load_tiers(str(PROFILES), str(AGENTS)))
        records = [
            record(0, "pdca-executor", model="deepseek-flash"),
            record(1, "pdca-planner", model="gpt-6.1-sol"),
            record(2, "pdca-escalate", model="claude-sonnet-5-5"),
        ]
        result = self.mod.summarize(records, "tier")
        self.assertEqual({"cheap", "medium", "strong"}, set(result["groups"]))

    def test_unknown_role_is_unclassified_not_dropped(self):
        self.assertEqual(self.mod.UNCLASSIFIED, self.mod.phase_of(UNKNOWN_ROLE))
        self.assertEqual(self.mod.UNCLASSIFIED, self.mod.classify(UNKNOWN_ROLE))

    def test_no_agent_name_prefix_inference(self):
        # A name that merely looks like a known family is not inferred.
        self.assertEqual(self.mod.UNCLASSIFIED, self.mod.classify("pdca-coder"))
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("startswith((", source)

    def test_unclassified_bucket_is_present_in_summary(self):
        result = self.mod.summarize(self.records, "phase")
        self.assertIn(self.mod.UNCLASSIFIED, result["groups"])
        self.assertEqual(1, result["groups"][self.mod.UNCLASSIFIED][0])

    def test_totals_reconcile_across_groups(self):
        result = self.mod.summarize(self.records, "phase")
        sessions = sum(acc[0] for acc in result["groups"].values())
        cost = round(sum(acc[1] for acc in result["groups"].values()), 9)
        self.assertEqual(len(self.records), result["total_sessions"])
        self.assertEqual(len(self.records), sessions)
        self.assertEqual(round(sum(r["cost"] for r in self.records), 9), result["total_cost"])
        self.assertEqual(result["total_cost"], cost)

    def test_every_group_key_is_a_known_phase_or_unclassified(self):
        result = self.mod.summarize(self.records, "phase")
        allowed = set(self.mod.PHASE_ORDER)
        for key in result["groups"]:
            self.assertIn(key, allowed)

    def test_store_from_records_walks_descendants(self):
        records = [
            record(0, "pdca-orchestrator", cost=1.0),
            record(1, "scout", cost=2.0, parent="s0"),
            record(2, "pdca-executor", cost=4.0, parent="s0"),
            record(3, "pdca-check", cost=8.0, parent="s2"),
        ]
        store = self.mod.Store.from_records(records)
        try:
            self.assertEqual({"s0", "s1", "s2", "s3"}, set(store.descendants("s0")))
            result = self.mod.summarize(store.sessions(), "phase")
            self.assertEqual(4, result["total_sessions"])
            self.assertEqual(15.0, result["total_cost"])
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
