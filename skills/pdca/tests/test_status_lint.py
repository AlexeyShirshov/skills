"""Behavioural tests for `scripts/status_lint.py`.

The lint is the mechanical half of the durable status file: it proves the record is
machine-readable, complete for its stage and consistent with itself (counters, claim rows,
the frozen progress-log shape). It judges nothing about the conclusions — that stays with CHECK.

These tests execute the script as the executor would, against a throw-away checkout.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_status_lint.py' -v
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts/status_lint.py"
SKILL = HERE.parent
REFERENCE = (SKILL / "references/plan.md").read_text(encoding="utf-8")
ACT = (SKILL / "references/act.md").read_text(encoding="utf-8")
BRIEF = (SKILL / "assets/briefs/act.md").read_text(encoding="utf-8")

OPEN_CYCLE = """# PDCA status — demo (cycle 1)

## Plan (r1)

Goal: demo. Carrying claims C1 and C2; units S1/P1 are not claims.

## Durable state

- Current cycle N: 1
- Plan revision r: 1
- Attempt n: 1
- rv: 1
- Form: cycle
- Overlay: coder
- Mode: autonomous
- Status: in-progress
- Phase: DO

## Carrying claims

| id | claim | status |
|---|---|---|
| C1 | the thing works | open |
| C2 | rune-based | open |

## Progress log

2026-10-26T06:00:00Z | PLAN | revision r1 | iteration 1/3 | PLAN ready (autonomous) | `.pdca/status/demo-1.md`
2026-10-26T06:01:00Z | DO | revision r1 | iteration 1/3 | DO started | `.pdca/status/demo-1.md`
"""

CLOSED_CYCLE = """# PDCA status — demo (cycle 1)

## Plan (r1)

Goal: demo. Carrying claims C1.

## Durable state

- Current cycle N: 1
- Plan revision r: 1
- Attempt n: 1
- rv: 1
- Form: cycle
- Overlay: coder
- Mode: autonomous
- Status: done
- Phase: EXIT

## Carrying claims

| id | claim | status |
|---|---|---|
| C1 | the thing works | met |

## Progress log

2026-10-26T06:00:00Z | PLAN | revision r1 | iteration 1/3 | PLAN ready (autonomous) | `.pdca/status/demo-1.md`
2026-10-26T06:10:00Z | CHECK | revision r1 | iteration 1/3 | CHECK accepted | `.pdca/status/demo-1.md`

## Done/Verified

C1 met.

## Next plan

No further cycle.

## Changed artefacts

Only the status file.
"""


class StatusLintCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="status-lint-"))
        self.repo = self.tmp / "repo"
        (self.repo / ".pdca/status").mkdir(parents=True)

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, text: str, name: str = "demo-1.md") -> Path:
        path = self.repo / ".pdca/status" / name
        path.write_text(text, encoding="utf-8")
        return path

    def run_lint(self, status: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--repo", str(self.repo),
             "--status", str(status), *extra],
            capture_output=True, text=True, timeout=120,
        )

    def payload(self, status: Path) -> dict:
        result = self.run_lint(status, "--json")
        return json.loads(result.stdout)


class LintTest(StatusLintCase):
    def test_open_cycle_passes_and_writes_a_receipt(self) -> None:
        status = self.write(OPEN_CYCLE)
        receipt = self.repo / ".pdca/demo/rv1/status_lint.txt"
        result = self.run_lint(status, "--receipt", str(receipt))
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("result: ok", result.stdout)
        self.assertIn("cycle=1 revision=1 attempt=1 rv=1", result.stdout)
        self.assertTrue(receipt.is_file())
        text = receipt.read_text(encoding="utf-8")
        self.assertIn("status: .pdca/status/demo-1.md", text)
        self.assertNotIn(str(self.repo), text, "receipt must stay repo-relative")

    def test_closed_cycle_passes(self) -> None:
        status = self.write(CLOSED_CYCLE)
        self.assertEqual(0, self.run_lint(status).returncode)

    def test_closed_cycle_without_closing_sections_is_a_violation(self) -> None:
        text = CLOSED_CYCLE.split("## Done/Verified")[0]
        result = self.run_lint(self.write(text))
        self.assertEqual(2, result.returncode)
        for section in ("Done/Verified", "Next plan", "Changed artefacts"):
            self.assertIn("S002", result.stdout, section)

    def test_iteration_typo_is_caught(self) -> None:
        for bad in ("iteration n=3", "iteration n/3", "iteration 4/3"):
            with self.subTest(bad=bad):
                text = OPEN_CYCLE.replace("iteration 1/3", bad, 1)
                result = self.run_lint(self.write(text))
                self.assertEqual(2, result.returncode)
                self.assertIn("S006", result.stdout)

    def test_log_pointer_is_required_and_phase_is_known(self) -> None:
        text = OPEN_CYCLE.replace(
            "2026-10-26T06:01:00Z | DO | revision r1 | iteration 1/3 | DO started | `.pdca/status/demo-1.md`",
            "2026-10-26T06:01:00Z | START | revision r1 | iteration 1/3 | DO started",
        )
        result = self.run_lint(self.write(text))
        self.assertEqual(2, result.returncode)
        self.assertIn("S006", result.stdout)

    def test_missing_section_counter_and_bad_state_values(self) -> None:
        cases = {
            "## Progress log": "S002",
            "- rv: 1\n": "S003",
            "Status: in-progress": "S004",
            "Phase: DO": "S004",
        }
        replacements = {
            "## Progress log": "## Journal",
            "- rv: 1\n": "",
            "Status: in-progress": "Status: finished",
            "Phase: DO": "Phase: DOING",
        }
        for needle, code in cases.items():
            with self.subTest(needle=needle):
                text = OPEN_CYCLE.replace(needle, replacements[needle])
                result = self.run_lint(self.write(text))
                self.assertEqual(2, result.returncode)
                self.assertIn(code, result.stdout)

    def test_claim_named_by_the_plan_needs_a_row(self) -> None:
        text = OPEN_CYCLE.replace("Carrying claims C1 and C2", "Carrying claims C1, C2 and C3")
        result = self.run_lint(self.write(text))
        self.assertEqual(2, result.returncode)
        self.assertIn("claim `C3`", result.stdout)

    def test_unit_ids_are_not_mistaken_for_claims(self) -> None:
        # the fixture already names S1/P1 in the plan; no S/P row exists and none is expected
        status = self.write(OPEN_CYCLE)
        data = self.payload(status)
        self.assertEqual(0, data["violations"], data)

    def test_exit_with_open_status_is_a_warning_only(self) -> None:
        text = CLOSED_CYCLE.replace("Status: done", "Status: in-progress")
        result = self.run_lint(self.write(text))
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("warnings: 1", result.stdout)

    def test_shell_artefact_is_a_warning(self) -> None:
        text = OPEN_CYCLE.replace("Goal: demo.", "Goal: demo, step $\\to$ done.")
        result = self.run_lint(self.write(text))
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("shell artefact", result.stdout)

    def test_event_restating_the_file_count_is_a_violation(self) -> None:
        # "15 sections, 9 log lines" is stale the moment the next event is appended; the receipt
        # carries the counts, the line carries the pointer.
        text = OPEN_CYCLE.replace(
            "DO started",
            "gate: status_lint check exit 0 (15 sections, 9 log lines, 0 violations)",
        )
        result = self.run_lint(self.write(text))
        self.assertEqual(2, result.returncode)
        self.assertIn("S007", result.stdout)
        self.assertIn("STATUS-LINT receipt", result.stdout)

    def test_event_without_a_derived_count_passes(self) -> None:
        text = OPEN_CYCLE.replace("DO started", "DO started with the plan folded in")
        self.assertEqual(0, self.run_lint(self.write(text)).returncode)

    def test_fenced_plan_copy_does_not_shadow_a_section(self) -> None:
        # The plan copied into `## Plan` carries its own `## Carrying claims — …`; a heading inside
        # a fence is body text, so the real claims table is the one that is read.
        text = OPEN_CYCLE.replace(
            "Goal: demo. Carrying claims C1 and C2; units S1/P1 are not claims.",
            "Goal: demo.\n\n````markdown\n# demo plan\n\n## Carrying claims — отдельно от качества\n\n"
            "| K9 | plan-local | pending |\n````",
        )
        result = self.run_lint(self.write(text))
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("claims: 2 (C1, C2)", result.stdout)

    def test_bullet_prefixed_log_line_is_tolerated(self) -> None:
        # A markdown list bullet is decoration; the frozen shape starts at the timestamp.
        text = OPEN_CYCLE.replace("2026-10-26T06:01:00Z | DO |",
                                  "- 2026-10-26T06:01:00Z | DO |")
        self.assertEqual(0, self.run_lint(self.write(text)).returncode)

    def test_schema_subcommand_prints_the_matching_semantics(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "schema"], capture_output=True, text=True, timeout=120
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("heading inside a fenced block", result.stdout)
        self.assertIn("[A-Z]", result.stdout)
        self.assertIn("leading `- ` bullet is tolerated", result.stdout)

    def test_schema_subcommand_prints_the_durable_shape(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "schema"], capture_output=True, text=True, timeout=120
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("## Progress log", result.stdout)
        self.assertIn("iteration <n>/3", result.stdout)
        self.assertIn("current cycle n", result.stdout)

    def test_operational_errors_are_exit_one(self) -> None:
        missing = self.repo / ".pdca/status/nope.md"
        self.assertEqual(1, self.run_lint(missing).returncode)
        empty = self.write("", name="empty.md")
        self.assertEqual(1, self.run_lint(empty).returncode)


class DocumentationTest(unittest.TestCase):
    def test_plan_reference_documents_the_lint(self) -> None:
        for phrase in (
            "Status lint: `status_lint.py`",
            "status_lint.py check --repo",
            "status_lint.py schema",
            "fenced block is body text",
            "a leading list",
            "`STATUS-LINT`",
            "Exit codes `0` ok, `2` violation",
            "iteration <n>/3",
            "restates the file's own log-line count",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, REFERENCE)

    def test_act_reference_and_brief_carry_the_receipt(self) -> None:
        self.assertIn("status lint", ACT.lower())
        self.assertIn("status lint", BRIEF.lower())


if __name__ == "__main__":
    unittest.main()
