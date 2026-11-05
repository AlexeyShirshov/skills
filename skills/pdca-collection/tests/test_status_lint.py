"""Behavioural tests for `scripts/status_lint.py` — the queue as data.

The queue is the collection status file; its tables are the data the agent writes
by hand.  The lint exists because two ad-hoc edits broke it the same way twice: a
raw ``|`` inside a note split the row into extra cells, and a note wrapped onto a
second line truncated the table.  These tests execute the script as
`pdca-executor` would, against throw-away fixtures.

Run:
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_status_lint.py' -v
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts/status_lint.py"
FIXTURES = HERE / "fixtures/status_lint"
RECORDED = HERE / "behavioral" / "fixtures"


def run(*files: Path, json_output: bool = False) -> subprocess.CompletedProcess:
    argv = [sys.executable, str(SCRIPT), *map(str, files)]
    if json_output:
        argv.append("--json")
    return subprocess.run(argv, capture_output=True, text=True, timeout=120)


class StructureTest(unittest.TestCase):
    def test_a_complete_queue_passes(self) -> None:
        result = run(FIXTURES / "queue-ok.md")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("4 tables, 5 rows", result.stdout)

    def test_recorded_runs_pass_unchanged(self) -> None:
        """The lint must fit every recorded status file, not a private schema."""
        recorded = sorted(RECORDED.glob("*.md"))
        self.assertTrue(recorded)
        for path in recorded:
            with self.subTest(path=path.name):
                result = run(path)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_json_reports_counts_and_no_violations(self) -> None:
        result = run(FIXTURES / "queue-ok.md", json_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(4, payload["files"][0]["tables"])
        self.assertEqual([], payload["files"][0]["violations"])


class BrokenRowTest(unittest.TestCase):
    def assert_violation(self, name: str, *phrases: str) -> None:
        result = run(FIXTURES / name)
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, result.stdout)

    def test_a_raw_pipe_in_a_note_adds_cells(self) -> None:
        self.assert_violation(
            "queue-pipe.md",
            "row has 11 cells, header has 9",
            "a raw '|' inside a note splits the row",
        )

    def test_a_wrapped_note_truncates_the_table(self) -> None:
        self.assert_violation(
            "queue-wrapped.md",
            "a note wrapped onto the next line truncates the table",
            "one record per line",
        )

    def test_a_short_separator_is_reported(self) -> None:
        self.assert_violation("queue-separator.md", "table separator has 8 cells, header has 9")

    def test_an_unknown_status_fails_with_the_enumeration(self) -> None:
        self.assert_violation(
            "queue-enum.md",
            "status 'finished' is not one of: pending | in-progress | done | incomplete",
        )

    def test_a_duplicate_id_is_reported(self) -> None:
        self.assert_violation("queue-duplicate.md", "duplicate unit 'U1' (first at line 7)")

    def test_a_lost_required_column_is_reported(self) -> None:
        self.assert_violation("queue-missing-column.md", "items table has no 'plan_state' column")


class PlanTerminalTest(unittest.TestCase):
    """The optional typed `terminal` column: a PLAN-terminal row is a resolution.

    Assertions stay on the executable result — exit code, the JSON `ok` flag and the
    line numbers of the reported violations — so a rewording of a diagnostic is not a
    test failure while a changed accept/reject decision still is.
    """

    def run_json(self, name: str) -> tuple[subprocess.CompletedProcess, dict]:
        result = run(FIXTURES / name, json_output=True)
        return result, json.loads(result.stdout or "{}")

    def assert_rejected(self, name: str, line: int, needle: str) -> None:
        result, payload = self.run_json(name)
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertFalse(payload["ok"], payload)
        violations = payload["files"][0]["violations"]
        self.assertEqual(1, len(violations), violations)
        self.assertEqual(line, violations[0]["line"], violations)
        self.assertIn(needle, violations[0]["message"], violations)

    def assert_accepted(self, name: str, rows: int) -> None:
        result, payload = self.run_json(name)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual([], payload["files"][0]["violations"], payload)
        self.assertEqual(rows, payload["files"][0]["rows"], payload)

    def test_terminal_items_pass_in_first_middle_and_last_position(self) -> None:
        # T1 first, T3 middle, T5 last; execution rows in between stay `done`.
        self.assert_accepted("queue-plan-terminal.md", 6)

    def test_a_recorded_execution_failure_stays_valid(self) -> None:
        self.assert_accepted("queue-execution-failure.md", 5)

    def test_a_terminal_resolution_must_not_be_done(self) -> None:
        self.assert_rejected("queue-terminal-done.md", 7, "'done'")

    def test_a_terminal_resolution_must_not_be_plan_ready(self) -> None:
        self.assert_rejected("queue-terminal-ready.md", 7, "'ready'")

    def test_a_terminal_resolution_consumes_no_attempt(self) -> None:
        self.assert_rejected("queue-terminal-attempts.md", 7, "'1'")

    def test_a_terminal_resolution_requires_the_attempts_column(self) -> None:
        self.assert_rejected("queue-terminal-no-attempts.md", 7, "'attempts'")

    def test_a_terminal_row_without_a_status_column_fails_closed(self) -> None:
        # A missing status column used to skip the "must stay incomplete" check.
        self.assert_rejected("queue-terminal-no-status.md", 10, "'status'")

    def test_a_terminal_row_on_a_campaign_form_fails_closed(self) -> None:
        self.assert_rejected("queue-terminal-campaign.md", 10, "'campaign'")

    def test_an_unknown_terminal_value_fails_with_the_enumeration(self) -> None:
        self.assert_rejected("queue-terminal-unknown.md", 7, "criteria-undetermined | infeasible")

    def test_legacy_rows_without_the_column_keep_the_execution_default(self) -> None:
        self.assert_accepted("queue-ok.md", 5)


class CapsTest(unittest.TestCase):
    """Caps are recorded, not inherited silently: default 4, a lowering needs a reason.

    The defect this pins: an entry plan that never names ``plan_cap`` used to end
    up sequential because the driver read "absent" as the safe value 1.  Silence
    now means the contract default 4, and a real host limit must be written down.
    """

    def run_json(self, name: str) -> tuple[subprocess.CompletedProcess, dict]:
        result = run(FIXTURES / name, json_output=True)
        return result, json.loads(result.stdout or "{}")

    def test_recorded_caps_pass(self) -> None:
        result, payload = self.run_json("queue-caps-ok.md")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(5, payload["files"][0]["rows"], payload)

    def test_a_form_without_caps_is_rejected_not_read_as_one(self) -> None:
        result, payload = self.run_json("queue-caps-missing.md")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        violations = payload["files"][0]["violations"]
        self.assertEqual(2, len(violations), violations)
        self.assertEqual({4}, {item["line"] for item in violations}, violations)
        joined = " ".join(item["message"] for item in violations)
        for needle in ("plan_cap", "lane_cap", "never a serialized 1"):
            with self.subTest(needle=needle):
                self.assertIn(needle, joined)

    def test_a_lowering_without_a_reason_is_rejected(self) -> None:
        result, payload = self.run_json("queue-caps-low-unreasoned.md")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        violations = payload["files"][0]["violations"]
        self.assertEqual(1, len(violations), violations)
        self.assertEqual(5, violations[0]["line"], violations)
        self.assertIn("cap_reason", violations[0]["message"], violations)

    def test_a_reasoned_lowering_passes(self) -> None:
        result, payload = self.run_json("queue-caps-low-reasoned.md")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(5, payload["files"][0]["rows"], payload)

    def test_a_non_integer_cap_is_rejected(self) -> None:
        result, payload = self.run_json("queue-caps-bad.md")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        violations = payload["files"][0]["violations"]
        self.assertEqual(1, len(violations), violations)
        self.assertIn("not a positive integer", violations[0]["message"], violations)


class OperatorTest(unittest.TestCase):
    def test_a_missing_file_is_a_usage_error(self) -> None:
        result = run(FIXTURES / "does-not-exist.md")
        self.assertEqual(1, result.returncode)
        self.assertIn("status-lint:", result.stderr)

    def test_several_files_are_all_reported(self) -> None:
        result = run(FIXTURES / "queue-ok.md", FIXTURES / "queue-enum.md")
        self.assertEqual(2, result.returncode)
        self.assertIn("queue-ok.md", result.stdout)
        self.assertIn("queue-enum.md", result.stdout)
        self.assertIn("FAIL:", result.stdout)


if __name__ == "__main__":
    unittest.main()
