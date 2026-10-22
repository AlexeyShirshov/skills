"""Offline tests for the behavioral-probe artifact checks.

The live probes (``probe.py``) cost model tokens and are non-deterministic, so
they are opt-in. What runs in the normal suite is this file: it feeds the
artifact checks a *recorded* collection status (a real sandbox run) plus a set
of mutations that a contract violation would produce, and proves the checks
catch the violation.

Run:
    python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py'
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import checks  # noqa: E402

FIXTURES = HERE / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class GapProbeChecksTest(unittest.TestCase):
    """A recorded gap run: one unplannable unit stops the whole start."""

    def setUp(self) -> None:
        self.status = fixture("gap-status.md")

    def test_recorded_gap_run_passes(self) -> None:
        self.assertEqual([], checks.check_gap_probe(self.status))

    def test_ready_placeholder_is_rejected(self) -> None:
        mutated = self.status.replace(
            "| T2 | 2 | campaign | — | n/a | pending |",
            "| T2 | 2 | campaign | — | n/a | ready |",
        )
        self.assertNotEqual(mutated, self.status, "fixture row changed shape")
        failures = checks.check_gap_probe(mutated)
        self.assertTrue(
            any("ready placeholder" in failure for failure in failures),
            f"a ready placeholder was accepted: {failures}",
        )

    def test_allocated_lane_is_rejected(self) -> None:
        mutated = self.status.replace(
            "| — | — | — | — | — | Not formed: ALL-barrier not passed; no lane allocated. |",
            "| G1 | T1 | ../repo-worktrees/G1 | collection/x/group-G1 | pending | started |",
        )
        self.assertNotEqual(mutated, self.status, "fixture groups row changed shape")
        failures = checks.check_gap_probe(mutated)
        self.assertTrue(
            any("was allocated" in failure for failure in failures),
            f"an allocated group was accepted: {failures}",
        )

    def test_barrier_pass_with_a_gap_is_rejected(self) -> None:
        mutated = self.status.replace(
            "ALL-barrier validation (pdca-planner): FAIL.",
            "ALL-barrier validation (pdca-planner): PASS.",
        )
        self.assertNotEqual(mutated, self.status, "fixture barrier verdict changed shape")
        failures = checks.check_gap_probe(mutated)
        self.assertTrue(
            any("ALL-barrier" in failure for failure in failures),
            f"a passed barrier with a gap was accepted: {failures}",
        )

    def test_planning_alone_is_not_do(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir(parents=True)
            (repo / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            checks.git(repo, "init", "-q")
            checks.git(repo, "add", "-A")
            checks.git(repo, "-c", "user.email=p@l", "-c", "user.name=p", "commit", "-qm", "i")
            before = checks.tracked_hashes(repo)
            (repo / "calc.py").write_text("def add(a, b):\n    return a + b\n\n\ndef mul(a, b):\n    return a * b\n", encoding="utf-8")
            failures = checks.check_gap_probe(self.status, repo=repo, before=before)
            self.assertTrue(
                any("product files changed" in failure for failure in failures),
                f"a product edit before DO was accepted: {failures}",
            )


class CampaignProbeChecksTest(unittest.TestCase):
    """A recorded campaign run: the frame joins P, steps and runtime do not."""

    def setUp(self) -> None:
        self.status = fixture("campaign-status.md")
        self.preparation = fixture("campaign-preparation.md")

    def test_recorded_campaign_run_passes(self) -> None:
        self.assertEqual([], checks.check_campaign_probe(self.status, self.preparation))

    def test_cycle_instead_of_campaign_is_rejected(self) -> None:
        mutated = self.status.replace(
            "| U1 | campaign | pending | n/a (campaign) |",
            "| U1 | cycle | pending | ready |",
        )
        self.assertNotEqual(mutated, self.status, "fixture unit row changed shape")
        failures = checks.check_campaign_probe(mutated, self.preparation)
        self.assertTrue(
            any("not as a campaign" in failure for failure in failures),
            f"a cycle unit passed the campaign check: {failures}",
        )

    def test_unit_level_variant_is_rejected(self) -> None:
        mutated = self.status.replace(
            "| U1 | campaign | pending | n/a (campaign) | — | — |",
            "| U1 | campaign | pending | n/a (campaign) | pdca-coder | — |",
        )
        self.assertNotEqual(mutated, self.status, "fixture unit row changed shape")
        failures = checks.check_campaign_probe(mutated, self.preparation)
        self.assertTrue(
            any("unit-level selected_variant" in failure for failure in failures),
            f"a unit-level variant on a campaign was accepted: {failures}",
        )

    def test_incomplete_frame_is_rejected(self) -> None:
        mutated = self.preparation.replace("## 5. Dependencies", "## Dependencies")
        self.assertNotEqual(mutated, self.preparation, "fixture frame heading changed shape")
        failures = checks.check_campaign_probe(self.status, mutated)
        self.assertTrue(
            any("frame point 5" in failure for failure in failures),
            f"a frame missing point 5 was accepted: {failures}",
        )

    def test_runtime_status_before_the_barrier_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            (repo / ".pdca/status").mkdir(parents=True)
            (repo / ".pdca/status/latency-readme.json").write_text('{"Status": "running"}\n', encoding="utf-8")
            failures = checks.check_campaign_probe(self.status, self.preparation, repo=repo)
            self.assertTrue(
                any("too early" in failure for failure in failures),
                f"a runtime status at the barrier was accepted: {failures}",
            )


class LaneProbeChecksTest(unittest.TestCase):
    """A recorded lane run: after the barrier DO is driven by ``pdca-orchestrator``."""

    def setUp(self) -> None:
        self.status = fixture("lane-status.md")

    def _repo(self, tmp: str, body: str) -> tuple[Path, dict[str, str]]:
        repo = Path(tmp) / "repo"
        repo.mkdir(parents=True)
        (repo / "calc.py").write_text(body, encoding="utf-8")
        checks.git(repo, "init", "-q")
        checks.git(repo, "add", "-A")
        checks.git(repo, "-c", "user.email=p@l", "-c", "user.name=p", "commit", "-qm", "i")
        return repo, checks.tracked_hashes(repo)

    def test_recorded_lane_run_passes(self) -> None:
        import probe  # sibling module; import is side-effect free

        after = "def add(a, b):\n    return a + b\n\n\ndef mul(a, b):\n    \"\"\"Return a * b.\"\"\"\n    return a * b\n"
        with tempfile.TemporaryDirectory() as tmp:
            repo, before = self._repo(tmp, "def add(a, b):\n    return a + b\n")
            (repo / "calc.py").write_text(after, encoding="utf-8")
            self.assertEqual([], probe.check_lane(self.status, repo, before))

    def test_missing_do_is_rejected(self) -> None:
        import probe

        with tempfile.TemporaryDirectory() as tmp:
            repo, before = self._repo(tmp, "def add(a, b):\n    return a + b\n")
            failures = probe.check_lane(self.status, repo, before)
            self.assertTrue(
                any("DO never ran" in failure for failure in failures),
                f"a run without a product change was accepted: {failures}",
            )

    def test_unfinished_unit_is_rejected(self) -> None:
        mutated = self.status.replace("| T1 | G1 | main (current; no task branch) | done |",
                                      "| T1 | G1 | main (current; no task branch) | in-progress |")
        self.assertNotEqual(mutated, self.status, "fixture task row changed shape")
        self.assertEqual("in-progress", checks.task_statuses(mutated)["T1"])

    def test_task_statuses_covers_both_recorded_table_shapes(self) -> None:
        self.assertEqual("done", checks.task_statuses(fixture("lane-status.md"))["T1"])
        self.assertEqual("pending", checks.task_statuses(fixture("gap-status.md"))["T2"])


class TableParsingTest(unittest.TestCase):
    """The parsers are column-order agnostic: both recorded runs use different headers."""

    def test_units_carry_both_recorded_shapes(self) -> None:
        gap = checks.units(fixture("gap-status.md"))
        campaign = checks.units(fixture("campaign-status.md"))
        self.assertEqual("campaign", gap["T2"]["execution_kind"])
        self.assertEqual("cycle", gap["T1"]["execution_kind"])
        self.assertEqual("ready", campaign["U1"]["preparation_state"])
        self.assertTrue(campaign["U1"]["preparation_ref"].endswith("@r1"))

    def test_groups_are_read_only_when_present(self) -> None:
        self.assertEqual([], [g for g in checks.groups(fixture("gap-status.md")) if not checks.is_unset(g.get("worktree", ""))])
        campaign_groups = checks.groups(fixture("campaign-status.md"))
        self.assertEqual(["G1", "G2"], [group["group"] for group in campaign_groups])

    def test_units_merge_input_and_state_tables(self) -> None:
        """A run may describe a unit in an `Input units` table and a `Units` table."""
        parsed = checks.units(fixture("campaign-status-multitable.md"))
        self.assertEqual("campaign", parsed["U1"]["execution_kind"])
        self.assertEqual("ready", parsed["U1"]["preparation_state"])
        self.assertTrue(parsed["U1"]["preparation_ref"].endswith("@r1"))
        self.assertEqual("ready", parsed["U2"]["plan_state"])


if __name__ == "__main__":
    unittest.main()
