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
