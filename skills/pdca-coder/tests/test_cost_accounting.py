"""Cost-accounting guards for the pdca-coder skill.

These tests import the read-only aggregation script as a module and feed it a
small, secret-free, in-memory fixture: the known generic roles plus one unknown
role.  They assert the generic classification (unknown stays explicitly
`unclassified`), that no session is dropped, and that the per-group totals
reconcile with the overall totals.

Run:
    python3 -m unittest discover -s skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
import os
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts/pdca_cost.py"

# The generic roles the skill names.  All must classify.
KNOWN_ROLES = (
    "pdca-scout",
    "pdca-executor",
    "pdca-planner",
    "pdca-check",
    "pdca-escalate",
    "pdca-security-auditor",
    "pdca-orchestrator",
)
UNKNOWN_ROLE = "mystery-role"


def load_module():
    spec = importlib.util.spec_from_file_location("pdca_cost_under_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(index, agent, cost=1.0, parent=None):
    """A minimal, secret-free session record (same keys as a session row)."""
    return {
        "id": "s%d" % index,
        "parent": parent,
        "agent": agent,
        "title": agent,
        "model": None,
        "cost": cost,
        "ti": 1,
        "to": 1,
        "tr": 0,
        "tcr": 0,
        "tcw": 0,
        "t": 0,
    }


# The exact column set the Store selects, so a fixture table is a real table, not an approximation.
SESSION_COLUMNS = (
    "id text, parent_id text, agent text, title text, model text, cost real, "
    "tokens_input int, tokens_output int, tokens_reasoning int, "
    "tokens_cache_read int, tokens_cache_write int, time_created int"
)


class CostAccountingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()
        cls.records = [
            record(i, agent, cost=0.25 * (i + 1))
            for i, agent in enumerate(KNOWN_ROLES + (UNKNOWN_ROLE,))
        ]

    def test_module_loads(self):
        self.assertTrue(hasattr(self.mod, "summarize"))
        self.assertTrue(hasattr(self.mod, "UNCLASSIFIED"))

    def test_known_roles_classify(self):
        for role in KNOWN_ROLES:
            with self.subTest(role=role):
                self.assertNotEqual(self.mod.UNCLASSIFIED, self.mod.phase_of(role))

    def test_unknown_role_is_unclassified_not_dropped(self):
        self.assertEqual(self.mod.UNCLASSIFIED, self.mod.phase_of(UNKNOWN_ROLE))

    def test_unclassified_bucket_is_present_in_summary(self):
        result = self.mod.summarize(self.records, "phase")
        self.assertIn(self.mod.UNCLASSIFIED, result["groups"])
        unknown_acc = result["groups"][self.mod.UNCLASSIFIED]
        self.assertEqual(1, unknown_acc[0])

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

    def test_unpriced_sessions_are_flagged_not_silently_zero(self):
        # A model without a catalogue price reports cost=0 while spending real tokens: the summary
        # must count it and say the total understates the run.
        records = [record(0, "pdca-planner", cost=0.0), record(1, "pdca-executor", cost=0.25)]
        result = self.mod.summarize(records, "phase")
        self.assertEqual(1, result["unpriced"]["sessions"])
        self.assertEqual(2, result["total_sessions"])
        self.assertEqual(0.25, result["total_cost"])

    def test_store_reads_the_live_v2_table_when_present(self):
        # The harness writes `session_v2`; the legacy `session` froze at the migration. Reading the
        # legacy table makes every current run invisible ("task not found").
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "t.db")
            con = sqlite3.connect(db)
            for table in ("session", "session_v2"):
                con.execute("create table %s (%s)" % (table, SESSION_COLUMNS))
            legacy = "('old', NULL, 'legacy', 'legacy', NULL, 1.0, 1, 1, 0, 0, 0, 0)"
            live = "('new', NULL, 'pdca-check', 'live', NULL, 2.0, 1, 1, 0, 0, 0, 0)"
            con.execute("insert into session values " + legacy)
            con.execute("insert into session_v2 values " + live)
            con.commit()
            con.close()
            store = self.mod.Store(db)
            try:
                self.assertEqual(["new"], [s["id"] for s in store.sessions()])
            finally:
                store.close()

    def test_store_from_records_walks_descendants(self):
        records = [
            record(0, "build", cost=1.0),
            record(1, "pdca-scout", cost=2.0, parent="s0"),
            record(2, "pdca-executor", cost=4.0, parent="s0"),
        ]
        store = self.mod.Store.from_records(records)
        try:
            self.assertEqual({"s0", "s1", "s2"}, set(store.descendants("s0")))
            result = self.mod.summarize(store.sessions(), "phase")
            self.assertEqual(3, result["total_sessions"])
            self.assertEqual(7.0, result["total_cost"])
        finally:
            store.close()

    def test_no_agent_name_prefix_inference(self):
        # A name that merely looks like a known family is not inferred; the table
        # is exact and anything else is unclassified.
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIsInstance(source, str)
        # The only prefix use is the jsonc comment stripper; no agent-name
        # family/prefix inference remains (no multi-prefix tuple check).
        self.assertNotIn("startswith((", source)
        self.assertEqual(self.mod.UNCLASSIFIED, self.mod.phase_of("special-envoy"))
        self.assertEqual("?", self.mod.model_id(None))


if __name__ == "__main__":
    unittest.main()
