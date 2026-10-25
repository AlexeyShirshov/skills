"""Scenario gate tests for validate_inner_loop.py.

The gate itself is exercised as a subprocess (`sys.executable` +
`subprocess.run`) against JSON fixtures written to a temporary directory.  The
module's internals are deliberately not imported, so these tests also prove the
documented CLI contract (argv, exit codes, `FAIL:`/`ERROR:` output) and that no
supplied command is ever executed.

Run:
    python3 -m unittest discover -s skills/pdca-dotnet/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts/validate_inner_loop.py"
SKILL = SKILL_DIR / "SKILL.md"
# The .NET text is an overlay: the executable inner-loop wiring lives in SKILL.md
# plus the phase references it loads, so the contract corpus is the union.
REFERENCE_DIR = SKILL_DIR / "references"
SELECTOR = "FullyQualifiedName~Foo.Tests.BarTests"
SELECTOR_2 = "FullyQualifiedName~Shared.Tests.ContractTests"
SEL_A = "FullyQualifiedName~Foo.Tests.A"
SEL_B = "FullyQualifiedName~Foo.Tests.B"
SEL_OR = SEL_A + "|" + SEL_B
SEL_AND = SEL_A + "&" + SEL_B


def run_gate(mode, payload=None, raw=None):
    """Write the payload (or raw text) and run the gate; return the process."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "input.json"
        if raw is not None:
            path.write_text(raw, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), mode, str(path)],
            capture_output=True,
            text=True,
        )


def run_gate_with_journal(payload, journal):
    """Run `report <payload> --journal <journal>`; return the process."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "report.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        journal_path = Path(tmp) / "journal.json"
        journal_path.write_text(json.dumps(journal), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "report",
                str(path),
                "--journal",
                str(journal_path),
            ],
            capture_output=True,
            text=True,
        )


def output(proc):
    return proc.stdout + proc.stderr


def valid_scope(**overrides):
    scope = {
        "projects": ["tests/Foo.Tests.csproj"],
        "selectors": [SELECTOR],
        "files": ["src/Foo/Bar.cs"],
        "rationale": "covers the changed Bar behavior",
        "rebuild": "affected",
        "boundary": "D1-D2 boundary",
    }
    scope.update(overrides)
    return scope


def docs_scope(**overrides):
    return valid_scope(files=["docs/notes.md"], rebuild="none", **overrides)


def valid_brief(**overrides):
    brief = {"unit": "D1", "scope": valid_scope()}
    brief.update(overrides)
    return brief


def exec_(command, phase="inner", source="r1", artifact="r1", code=0, **overrides):
    execution = {
        "command": command,
        "phase": phase,
        "source_revision": source,
        "artifact_revision": artifact,
        "exit_code": code,
        "selected_count": 5,
    }
    execution.update(overrides)
    return execution


def valid_report(executions=None, scope=None, amendments=None):
    report = {"unit": "D1", "scope": scope if scope is not None else valid_scope()}
    report["executions"] = executions if executions is not None else [
        exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
        exec_(
            ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build", "--filter", SELECTOR]
        ),
    ]
    if amendments is not None:
        report["amendments"] = amendments
    return report


class BriefGateTests(unittest.TestCase):
    def test_valid_brief_rc0(self):
        proc = run_gate("brief", valid_brief())
        self.assertEqual(proc.returncode, 0, output(proc))
        self.assertNotIn("FAIL:", output(proc))

    def test_missing_unit_rejected(self):
        brief = valid_brief()
        del brief["unit"]
        proc = run_gate("brief", brief)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("unit", output(proc))

    def test_empty_projects_rejected(self):
        proc = run_gate("brief", valid_brief(scope=valid_scope(projects=[])))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("projects", output(proc))

    def test_empty_selector_rejected(self):
        proc = run_gate("brief", valid_brief(scope=valid_scope(selectors=[""])))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("selectors", output(proc))

    def test_star_selector_rejected(self):
        proc = run_gate("brief", valid_brief(scope=valid_scope(selectors=["*"])))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("broad selector", output(proc))

    def test_empty_rationale_rejected(self):
        proc = run_gate("brief", valid_brief(scope=valid_scope(rationale="")))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("rationale", output(proc))

    def test_bad_rebuild_rejected(self):
        proc = run_gate("brief", valid_brief(scope=valid_scope(rebuild="full")))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("rebuild", output(proc))

    def test_empty_boundary_rejected(self):
        proc = run_gate("brief", valid_brief(scope=valid_scope(boundary="")))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("boundary", output(proc))

    def test_malformed_json_rc1(self):
        proc = run_gate("brief", raw="{not json")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ERROR:", output(proc))
        self.assertNotIn("FAIL:", output(proc))

    def test_non_object_json_rc1(self):
        proc = run_gate("brief", raw="[]")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ERROR:", output(proc))

    def test_bad_argv_rc1(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "bogus", "x.json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ERROR:", output(proc))

    def test_files_not_list_rejected(self):
        proc = run_gate("brief", valid_brief(scope=valid_scope(files="src/Foo/Bar.cs")))
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("scope.files must be a list of strings", output(proc))

    def test_amendments_not_list_rejected(self):
        proc = run_gate("brief", valid_brief(amendments="not-a-list"))
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("amendments must be a list", output(proc))

    def test_amendment_not_object_rejected(self):
        proc = run_gate("brief", valid_brief(amendments=["not-an-object"]))
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("amendment 0 must be an object", output(proc))

    def test_amendment_reason_invalid_rejected(self):
        proc = run_gate(
            "brief",
            valid_brief(amendments=[{
                "reason": "",
                "added_selectors": [SELECTOR_2],
                "validated_before_run": True,
            }]),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("reason must be a nonempty string", output(proc))

    def test_amendment_added_selectors_invalid_rejected(self):
        for added in ([], [""], "not-a-list"):
            with self.subTest(added=added):
                proc = run_gate(
                    "brief",
                    valid_brief(amendments=[{
                        "reason": "shared contract widening",
                        "added_selectors": added,
                        "validated_before_run": True,
                    }]),
                )
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("FAIL:", proc.stdout)
                self.assertIn("added_selectors", output(proc))

    def test_amendment_added_selector_broad_rejected(self):
        proc = run_gate(
            "brief",
            valid_brief(amendments=[{
                "reason": "shared contract widening",
                "added_selectors": ["*"],
                "validated_before_run": True,
            }]),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("added selector is broad", output(proc))

    def test_amendment_validated_before_run_not_bool_rejected(self):
        for value in ("yes", None, 1):
            with self.subTest(value=value):
                proc = run_gate(
                    "brief",
                    valid_brief(amendments=[{
                        "reason": "shared contract widening",
                        "added_selectors": [SELECTOR_2],
                        "validated_before_run": value,
                    }]),
                )
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("FAIL:", proc.stdout)
                self.assertIn("validated_before_run must be a boolean", output(proc))

    def test_empty_unit_string_rejected(self):
        proc = run_gate("brief", valid_brief(unit=""))
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("unit must be a nonempty string", output(proc))

    def test_non_dict_scope_rejected(self):
        proc = run_gate("brief", valid_brief(scope="not-an-object"))
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("scope must be an object", output(proc))

    def test_unreadable_input_path_rc1(self):
        # A path that exists but is a directory: open() raises OSError, which
        # must surface as ERROR: / exit 1 (never FAIL: / exit 2).
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "brief", tmp],
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 1, output(proc))
        self.assertIn("ERROR:", output(proc))
        self.assertNotIn("FAIL:", output(proc))


class ReportGateTests(unittest.TestCase):
    def test_valid_filtered_dotnet_test_rc0(self):
        proc = run_gate("report", valid_report())
        self.assertEqual(proc.returncode, 0, output(proc))
        self.assertNotIn("FAIL:", output(proc))

    def test_valid_filtered_python_command_rc0(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["pytest", "-k", "x"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_missing_scope_rejected(self):
        report = valid_report()
        del report["scope"]
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("scope", output(proc))

    def test_null_scope_rejected(self):
        # `scope` present but null must be rejected structurally (a `FAIL:`
        # naming scope), not only latched by a downstream execution rule.
        report = valid_report()
        report["scope"] = None
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("scope must be an object", output(proc))
        brief = run_gate("brief", {**valid_brief(), "scope": None})
        self.assertEqual(brief.returncode, 2, output(brief))
        self.assertIn("FAIL:", brief.stdout)
        self.assertIn("scope must be an object", output(brief))

    def test_zero_selected_tests_rejected(self):
        # An empty/absent selector is still rejected at the scope level,
        # independent of the runtime count (GAP 1 keeps this brief rejection).
        proc = run_gate("report", valid_report(scope=docs_scope(selectors=[])))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("selectors", output(proc))

    def test_selected_count_positive_rc0(self):
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
            exec_(
                ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build", "--filter", SELECTOR],
                selected_count=12,
            ),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_missing_selected_count_rejected(self):
        bad = exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR])
        del bad["selected_count"]
        proc = run_gate("report", valid_report(scope=docs_scope(), executions=[bad]))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("selected_count", output(proc))

    def test_zero_selected_count_rejected(self):
        # A nonempty selector that runtime-matched zero tests is rejected.
        proc = run_gate("report", valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], selected_count=0)
            ],
        ))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("selected_count", output(proc))
        self.assertIn("zero/missing selected tests", output(proc))

    def test_default_selector_rejected(self):
        proc = run_gate("report", valid_report(scope=docs_scope(selectors=["All"])))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("broad selector", output(proc))

    def test_unfiltered_unit_project_inner_allowed(self):
        # E10: the presence/absence of `--filter` is NOT a unit-vs-integration
        # criterion.  An unfiltered run of an affected *unit* project inside DO
        # is a legitimate unit run (unlimited), not a comprehensive sweep.
        report = valid_report(
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj"]),
            ]
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))
        self.assertNotIn("FAIL:", output(proc))

    def test_whole_solution_build_inner_rejected(self):
        report = valid_report(
            executions=[exec_(["dotnet", "build", "Foo.slnx"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("broad", output(proc))

    def test_whole_solution_test_inner_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "Foo.slnx"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("broad", output(proc))

    def test_all_selecting_filter_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", "*"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("out of scope", output(proc))

    def test_repeated_solution_build_inner_rejected(self):
        report = valid_report(
            executions=[
                exec_(["dotnet", "build", "Foo.slnx"]),
                exec_(["dotnet", "build", "Foo.slnx"]),
            ]
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("broad", output(proc))

    def test_shared_contract_widening_validated_amendment_rc0(self):
        report = valid_report(
            scope=docs_scope(),
            amendments=[
                {
                    "reason": "shared contract affects an extra suite",
                    "added_selectors": [SELECTOR_2],
                    "validated_before_run": True,
                }
            ],
            executions=[exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR_2])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_silent_widening_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR_2])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("silent widening", output(proc))

    def test_amendment_after_execution_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            amendments=[
                {
                    "reason": "added after the fact",
                    "added_selectors": [SELECTOR_2],
                    "validated_before_run": False,
                }
            ],
            executions=[exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR_2])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("amendment", output(proc))

    def test_fresh_affected_build_then_no_build_rc0(self):
        proc = run_gate("report", valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
            exec_(
                ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build", "--filter", SELECTOR]
            ),
        ]))
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_stale_no_build_source_mismatch_rejected(self):
        report = valid_report(
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build", "--filter", SELECTOR],
                    source="r2",
                    artifact="r1",
                ),
            ]
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("stale --no-build", output(proc))

    def test_stale_no_build_no_matching_prior_build_rejected(self):
        report = valid_report(
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build", "--filter", SELECTOR],
                    source="r2",
                    artifact="r2",
                ),
            ]
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("stale --no-build", output(proc))

    def test_docs_only_no_build_rc0(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_docs_only_fictitious_rebuild_rejected(self):
        # GAP 2: a docs-only scope (no compiled file) must not claim an
        # affected rebuild.
        report = valid_report(
            scope=valid_scope(files=["docs/notes.md"], rebuild="affected"),
            executions=[exec_(["dotnet", "build", "tests/Foo.Tests.csproj"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("fictitious rebuild for docs-only scope", output(proc))

    def test_release_options_preserved_rc0(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "-c", "Release",
                     "--framework", "net8.0", "--filter", SELECTOR]
                )
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_debug_options_preserved_rc0(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "-c", "Debug", "--filter", SELECTOR]
                )
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_build_configuration_flag_preserved_rc0(self):
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj", "-c", "Debug"]),
            exec_(
                ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build",
                 "-c", "Release", "--filter", SELECTOR]
            ),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_selector_mismatch_with_options_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "-c", "Release",
                     "--filter", "FullyQualifiedName~Unrelated"]
                )
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("out of scope", output(proc))

    def test_intermediate_failure_then_final_green_rc0(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], code=1),
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], code=0),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_missing_exit_code_rejected(self):
        bad = exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR])
        del bad["exit_code"]
        report = valid_report(scope=docs_scope(), executions=[bad])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("exit_code", output(proc))

    def test_integration_project_inner_rejected(self):
        # E10 (c): an integration run *inside DO* is an actual policy violation —
        # recorded in the ledger, not masked by the phase or a rename.
        report = valid_report(
            scope=valid_scope(integration_projects=["tests/Integration.Tests.csproj"]),
            executions=[
                exec_(["dotnet", "build", "tests/Integration.Tests.csproj"]),
                exec_(["dotnet", "test", "tests/Integration.Tests.csproj"]),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("inside DO", output(proc))

    def test_missing_final_green_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], code=1)],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no final green", output(proc))

    def test_one_boundary_sweep_rc0(self):
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
            exec_(
                ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build", "--filter", SELECTOR]
            ),
            exec_(["dotnet", "build", "Foo.slnx"], phase="boundary"),
            exec_(["dotnet", "test", "Foo.slnx"], phase="boundary"),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_two_boundary_sweeps_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "Foo.slnx"], phase="boundary"),
                exec_(["dotnet", "test", "Foo.slnx"], phase="boundary"),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("more than one", output(proc))

    def test_filtered_boundary_integration_rc0(self):
        # A legitimate affected integration test run directly at the boundary
        # must be accepted (D1 fix); "fabricated boundary" is no longer a
        # category — a broad per-edit run in the inner phase is rule 9.
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], phase="boundary"
                )
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))
        self.assertNotIn("FAIL:", output(proc))

    def test_comprehensive_boundary_and_inner_broad_rejected(self):
        # Proxies for the removed "fabricated boundary" rule:
        # (a) a broad/comprehensive test command in `inner` is rejected.
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "Foo.slnx"], phase="inner")],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("broad", output(proc))

    def test_filtered_boundary_does_not_consume_sweep_cap(self):
        # A filtered boundary test plus one comprehensive sweep is still a
        # single comprehensive sweep (rc 0).
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
            exec_(
                ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build",
                 "--filter", SELECTOR], phase="boundary"
            ),
            exec_(["dotnet", "test", "Foo.slnx"], phase="boundary"),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_stale_boundary_evidence_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"], phase="boundary", source="r2", artifact="r1")
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("boundary", output(proc))

    def test_compound_wrapper_bash_c_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["bash", "-c", "dotnet test proj --filter " + SELECTOR])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("shell wrapper", output(proc))

    def test_compound_ampersand_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj", "&&", "dotnet", "build", "tests/Foo.Tests.csproj"])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("shell wrapper", output(proc))

    def test_execution_not_object_rejected(self):
        proc = run_gate("report", valid_report(executions=["not-an-object"]))
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("execution 0 must be an object", output(proc))

    def test_execution_command_invalid_rejected(self):
        for command in ([], [123], ["dotnet", 42]):
            with self.subTest(command=command):
                proc = run_gate(
                    "report",
                    valid_report(scope=docs_scope(), executions=[exec_(command)]),
                )
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("FAIL:", proc.stdout)
                self.assertIn("command must be a nonempty list of strings", output(proc))

    def test_execution_phase_invalid_rejected(self):
        proc = run_gate(
            "report",
            valid_report(
                scope=docs_scope(),
                executions=[exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR],
                    phase="middle",
                )],
            ),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("phase must be 'inner' or 'boundary'", output(proc))

    def test_execution_source_revision_invalid_rejected(self):
        proc = run_gate(
            "report",
            valid_report(
                scope=docs_scope(),
                executions=[exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], source=""
                )],
            ),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("source_revision must be a nonempty string", output(proc))

    def test_execution_artifact_revision_invalid_rejected(self):
        proc = run_gate(
            "report",
            valid_report(
                scope=docs_scope(),
                executions=[exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], artifact=""
                )],
            ),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("artifact_revision must be a nonempty string", output(proc))

    def test_exit_code_bool_rejected(self):
        # bool is an int subclass, so it must be rejected explicitly.
        proc = run_gate(
            "report",
            valid_report(
                scope=docs_scope(),
                executions=[exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], code=True
                )],
            ),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("exit_code must be an integer", output(proc))

    def test_selected_count_bool_rejected(self):
        proc = run_gate(
            "report",
            valid_report(
                scope=docs_scope(),
                executions=[exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR],
                    selected_count=True,
                )],
            ),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("selected_count must be an integer", output(proc))

    def test_multiple_boundary_solution_builds_rejected(self):
        proc = run_gate(
            "report",
            valid_report(
                scope=docs_scope(),
                executions=[
                    exec_(["dotnet", "build", "Foo.slnx"], phase="boundary"),
                    exec_(["dotnet", "build", "Foo.slnx"], phase="boundary"),
                ],
            ),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("multiple boundary solution builds", output(proc))

    def test_compiled_files_rebuild_not_affected_rejected(self):
        proc = run_gate("report", valid_report(scope=valid_scope(rebuild="none")))
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn(
            "compiled files changed but scope.rebuild is not 'affected'",
            output(proc),
        )

    def test_compiled_files_no_build_before_inner_test_rejected(self):
        proc = run_gate(
            "report",
            valid_report(executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR])
            ]),
        )
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn(
            "no affected dotnet build before the first inner dotnet test",
            output(proc),
        )

    def test_valueless_dash_filter_is_broad_rejected(self):
        # A dangling -filter/--filter selects the whole project (broad, rule 9).
        # The `-filter` spelling is not handled by the non-test guard at :147,
        # so this also locks the asymmetry: a `dotnet test` dangling filter is
        # caught by the dotnet-test rule, a non-test dangling `--filter` is not.
        for command in (
            ["dotnet", "test", "tests/Foo.Tests.csproj", "-filter"],
            ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter"],
            ["vstest", "--filter"],
        ):
            with self.subTest(command=command):
                proc = run_gate(
                    "report",
                    valid_report(scope=docs_scope(), executions=[exec_(command)]),
                )
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("FAIL:", proc.stdout)
                self.assertIn("broad", output(proc))

    def test_malformed_input_rc1(self):
        proc = run_gate("report", raw="{broken")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ERROR:", output(proc))


def _norm(text):
    """Collapse whitespace, drop markdown noise, lowercase (wording-robust)."""
    text = text.replace("`", "").replace("*", "")
    return re.sub(r"\s+", " ", text).lower()


class ContractWiringTests(unittest.TestCase):
    """Contract-wiring guards: the contract must carry the executable inner-loop gate.

    Rule-presence only, tied to real content: reads the sibling ``SKILL.md`` plus the
    phase references it loads (the .NET overlay keeps the bulky gate text in
    ``references/plan.md`` / ``references/check.md``) and asserts the validator
    wiring is stated.  It never executes a model or the PDCA cycle.
    """

    @classmethod
    def setUpClass(cls):
        cls.raw = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [SKILL] + sorted(REFERENCE_DIR.glob("*.md"))
        )
        cls.text = _norm(cls.raw)

    def assert_contract_wired(self, skill_text):
        """Assert every executable inner-loop gate clause is present in SKILL text.

        The same helper is fed a *mutated* copy by the negative tests below, so
        these wiring checks are load-bearing rather than decorative.
        """
        text = _norm(skill_text)
        # validator script referenced, with both subcommands
        self.assertIn("validate_inner_loop.py", text)
        self.assertRegex(text, r"validate_inner_loop\.py brief")
        self.assertRegex(text, r"validate_inner_loop\.py report")
        # mandatory structured `test scope` field
        self.assertIn("test scope", text)
        self.assertRegex(
            text,
            r"must[^.]{0,120}test scope"
            r"|test scope[^.]{0,160}(mandatory|must|required)",
        )
        # dispatch-refusal for an incomplete brief
        self.assertRegex(
            text,
            r"(without it|missing|incomplete)[^.]{0,80}(must not|never|refuse)"
            r"[^.]{0,80}dispatch"
            r"|must not dispatch[^.]{0,120}(brief|test scope)",
        )
        # CHECK FAIL (not warn) for a whole-project/solution inner loop
        self.assertRegex(
            text,
            r"whole[- ](project|solution)[^.]{0,200}(fail|reject)"
            r"|fail[^.]{0,200}whole[- ](project|solution)",
        )
        self.assertIn("never warns", text)
        # E10: integration is boundary-only; unit runs are unlimited and the
        # filter is not the classification criterion.
        self.assertIn(
            "integration runs happen at the do → check boundary", text
        )
        self.assertIn("unit runs are unlimited", text)

    def test_skill_references_the_validator_script(self):
        self.assert_contract_wired(self.raw)

    def test_skill_requires_a_structured_test_scope_brief_field(self):
        self.assert_contract_wired(self.raw)

    def test_skill_refuses_dispatch_of_an_incomplete_brief(self):
        self.assert_contract_wired(self.raw)

    def test_check_fails_not_warns_for_a_whole_project_inner_loop(self):
        self.assert_contract_wired(self.raw)

    def test_boundary_sweep_runs_once(self):
        self.assert_contract_wired(self.raw)

    def test_skill_references_both_validator_subcommands(self):
        self.assert_contract_wired(self.raw)

    # --- negative tests: a broken SKILL must make the wiring helper fail ---

    def _assert_mutation_detected(self, mutated):
        self.assertNotEqual(mutated, self.raw, "mutation had no effect")
        with self.assertRaises(AssertionError):
            self.assert_contract_wired(mutated)

    def test_negative_dispatch_refusal_removed_detected(self):
        self._assert_mutation_detected(
            self.raw.replace(
                "without it the driver must NOT dispatch the brief", ""
            )
        )

    def test_negative_check_fail_not_warn_removed_detected(self):
        self._assert_mutation_detected(
            self.raw.replace("never warns", "sometimes warns")
        )

    def test_negative_boundary_once_removed_detected(self):
        self._assert_mutation_detected(
            self.raw.replace(
                "integration runs\n  happen at the DO → CHECK boundary",
                "integration runs may happen anywhere in the cycle",
            )
        )

    def test_negative_unit_unlimited_removed_detected(self):
        # The phrase wraps across lines in the raw Markdown; mutate it as written.
        self._assert_mutation_detected(
            self.raw.replace("Unit runs are unlimited", "Unit runs are capped")
        )

    def test_negative_test_scope_phrase_removed_detected(self):
        self._assert_mutation_detected(
            re.sub(r"(?i)test scope", "test may", self.raw)
        )


class InnerLoopDocsTest(unittest.TestCase):
    """D3 guards: the .NET overlay docs carry the inner-loop obligation.

    The shared executor asset is domain-neutral by design; the .NET-specific
    inner-loop gate lives in this overlay's phase references.  Each guard is
    scoped to its normative section, so dropping one load-bearing obligation
    fails the test instead of being masked by a keyword elsewhere in the docs.
    """

    PLAN_START = "## Inner-loop gate: `test scope`, journal, report"
    PLAN_END = "## .NET test strategy deltas"
    ACT_START = "## Execution journal and the unit/integration policy"
    ACT_END = "### DO report: test evidence"

    @classmethod
    def setUpClass(cls):
        cls.plan_raw = (REFERENCE_DIR / "plan.md").read_text(encoding="utf-8")
        cls.act_raw = (REFERENCE_DIR / "act.md").read_text(encoding="utf-8")
        cls.plan = cls.section(cls.plan_raw, cls.PLAN_START, cls.PLAN_END)
        cls.act = cls.section(cls.act_raw, cls.ACT_START, cls.ACT_END)

    @staticmethod
    def section(text, start, end):
        begin = text.find(start)
        if begin < 0:
            raise AssertionError("section not found: %s" % start)
        stop = text.find(end, begin + len(start))
        if stop < 0:
            raise AssertionError("section end not found: %s" % end)
        return text[begin:stop]

    @staticmethod
    def clean(text):
        text = text.replace("`", "").replace("*", "")
        return re.sub(r"\s+", " ", text)

    def assert_inner_loop_contract(self, plan, act):
        plan = self.clean(plan)
        act = self.clean(act)
        for obligation in (
            # affected unit subset
            "mandatory structured test scope",
            "affected test project(s)",
            # the filter is not the classification criterion
            "presence of --filter is not a unit-vs-integration criterion",
            # one DO → CHECK boundary for integration
            "single DO → CHECK comprehensive sweep point",
            # no whole-solution inner loop
            "whole solution in the inner loop",
            # the report is derived from the raw journal
            "reconciled against it with --journal",
        ):
            self.assertIn(obligation, plan)
        for obligation in (
            # unit work is unlimited; integration is boundary-only
            "Unit tests are unlimited inside DO",
            "The presence or absence of --filter is not a unit-vs-integration criterion",
            "permitted at the DO → CHECK boundary",
            # ledger projected from the raw journal, and omissions fail
            "projected from that journal",
            "omits a started execution is rejected",
        ):
            self.assertIn(obligation, act)

    def test_scoped_sections_carry_the_inner_loop_contract(self):
        self.assertTrue(self.plan.strip(), "plan inner-loop section missing")
        self.assertTrue(self.act.strip(), "act journal section missing")
        self.assert_inner_loop_contract(self.plan, self.act)

    def test_each_obligation_is_load_bearing(self):
        # Delete one obligation at a time from its scoped section; the contract
        # check must fail rather than pass on a keyword elsewhere in the docs.
        cases = (
            ("plan", self.plan, "`test scope`", "test may"),
            ("plan", self.plan, "affected test project(s)", "affected test"),
            ("plan", self.plan, "unit-vs-integration criterion",
             "unit-or-integration criterion"),
            ("plan", self.plan, "DO → CHECK comprehensive sweep point", "sweep point"),
            ("plan", self.plan, "whole solution", "whole project"),
            ("plan", self.plan, "reconciled against it with `--journal`",
             "compared with a hand-written report"),
            ("act", self.act, "unlimited inside DO",
             "capped inside DO"),
            ("act", self.act, "unit-vs-integration criterion",
             "unit-or-integration criterion"),
            ("act", self.act, "DO → CHECK boundary",
             "cycle boundary"),
            ("act", self.act, "**projected from that journal**",
             "selected by the author"),
            ("act", self.act, "omits a started execution",
             "includes every started execution"),
        )
        for label, base, old, new in cases:
            with self.subTest(target=label, obligation=old[:60]):
                mutated = base.replace(old, new)
                self.assertNotEqual(mutated, base, "mutation had no effect")
                plan = mutated if label == "plan" else self.plan
                act = mutated if label == "act" else self.act
                with self.assertRaises(AssertionError):
                    self.assert_inner_loop_contract(plan, act)



class IntegrationPolicyTests(unittest.TestCase):
    """E10 policy: unit unlimited, integration boundary-only and planned.

    The run kind is classified by the actually selected projects/solution, never
    by the presence of ``--filter``.  These are behavioral gate tests: they run
    the real CLI as a subprocess and assert its exit code and `FAIL:` lines.
    """

    def test_multiple_unfiltered_unit_runs_inside_do_allowed(self):
        # (b) Multiple unfiltered unit runs inside DO and at the boundary are
        # allowed without artificial namespace filters.
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
            exec_(["dotnet", "test", "tests/Foo.Tests.csproj"]),
            exec_(["dotnet", "test", "tests/Foo.Tests.csproj"]),
            exec_(["dotnet", "test", "tests/Foo.Tests.csproj"]),
            exec_(["dotnet", "test", "tests/Foo.Tests.csproj"], phase="boundary"),
            exec_(["dotnet", "test", "tests/Foo.Tests.csproj"], phase="boundary"),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_integration_inside_do_detected_and_recorded(self):
        # (c) Integration inside DO is detected as an actual policy violation and
        # the execution record still exists (the gate reports, never deletes).
        report = valid_report(
            scope=valid_scope(integration_projects=["tests/Integration.Tests.csproj"]),
            executions=[
                exec_(["dotnet", "build", "tests/Integration.Tests.csproj"]),
                exec_(["dotnet", "test", "tests/Integration.Tests.csproj"]),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("execution 1", output(proc))
        self.assertIn("executed inside DO", output(proc))

    def test_integration_attempt_not_started_is_a_distinct_state(self):
        # (j) A pre-run policy check distinguishes an attempt violation
        # (failed-to-start, no invented fact) from an executed violation.
        report = valid_report(
            scope=valid_scope(integration_projects=["tests/Integration.Tests.csproj"]),
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                exec_(
                    ["dotnet", "test", "tests/Integration.Tests.csproj"],
                    state="failed-to-start",
                    exit_code=None,
                    selected_count=None,
                ),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("attempt never started", output(proc))
        self.assertNotIn("executed inside DO", output(proc))

    def test_mixed_solution_run_is_not_unit_by_command_name(self):
        # (d) A mixed solution run that really runs integration is classified
        # correctly, and may not be relabelled `unit` to escape the boundary rule.
        report = valid_report(
            executions=[
                exec_(["dotnet", "test", "Foo.slnx"], kind="unit"),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not unit", output(proc))

    def test_boundary_integration_reflects_planned_count(self):
        # (d) The boundary integration reflects the planned scope/count; an extra
        # actual run is a visible deviation, not a silent exemption.
        scope = valid_scope(
            integration_projects=["tests/Integration.Tests.csproj"],
            integration_boundary_runs=1,
        )
        report = valid_report(scope=scope, executions=[
            exec_(["dotnet", "build", "tests/Integration.Tests.csproj"]),
            exec_(["dotnet", "test", "tests/Integration.Tests.csproj"], phase="boundary"),
            exec_(["dotnet", "test", "tests/Integration.Tests.csproj"], phase="boundary"),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("exceed the planned budget", output(proc))

    def test_no_invented_numeric_cap_without_a_planned_count(self):
        # The gate invents no universal numeric cap: without a declared plan
        # count, only the phase rule constrains integration runs.
        report = valid_report(
            scope=valid_scope(integration_projects=["tests/Integration.Tests.csproj"]),
            executions=[
                exec_(["dotnet", "build", "tests/Integration.Tests.csproj"]),
                exec_(["dotnet", "test", "tests/Integration.Tests.csproj"], phase="boundary"),
                exec_(["dotnet", "test", "tests/Integration.Tests.csproj"], phase="boundary"),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))


class ExecutionStateTests(unittest.TestCase):
    """(e)/(k): every started execution is recorded; unfinished ≠ success."""

    def test_unfinished_attempt_does_not_carry_invented_result(self):
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
            exec_(
                ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR],
                state="canceled",
                exit_code=None,
                selected_count=None,
            ),
        ])
        proc = run_gate("report", report)
        # The canceled attempt is retained but cannot satisfy required success.
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no finished execution", output(proc))

    def test_canceled_attempt_retained_after_successful_retry(self):
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
            exec_(
                ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR],
                state="interrupted",
                exit_code=None,
                selected_count=None,
            ),
            exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR]),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_not_started_state_may_not_carry_a_result(self):
        report = valid_report(executions=[
            exec_(
                ["dotnet", "build", "tests/Foo.Tests.csproj"],
                state="not-started",
                exit_code=0,
                selected_count=5,
            ),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("must not carry an exit_code", output(proc))

    def test_unknown_state_rejected(self):
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"], state="done"),
        ])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("state must be one of", output(proc))


class JournalProjectionTests(unittest.TestCase):
    """(j): the report is projected from the raw journal, never hand-selected."""

    @staticmethod
    def journal(events):
        return {"unit": "D1", "scope": valid_scope(), "events": events}

    @staticmethod
    def start(event_id, phase="inner", command=None, kind=None):
        event = {
            "id": event_id,
            "event": "start",
            "phase": phase,
            "command": command or ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR],
            "source_revision": "r1",
            "artifact_revision": "r1",
            "at": "2026-10-16T00:00:00Z",
        }
        if kind is not None:
            event["kind"] = kind
        return event

    @staticmethod
    def finish(event_id, state="finished", code=0, count=5):
        return {
            "id": event_id,
            "event": "finish",
            "state": state,
            "exit_code": code,
            "selected_count": count,
            "at": "2026-10-16T00:01:00Z",
        }

    def test_journal_validation_accepts_start_finish(self):
        data = self.journal([
            self.start("e1"),
            self.finish("e1"),
        ])
        proc = run_gate("journal", data)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_finish_without_start_rejected(self):
        data = self.journal([self.finish("e1")])
        proc = run_gate("journal", data)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no recorded start", output(proc))

    def test_project_rebuilds_every_started_execution(self):
        data = self.journal([
            self.start("e1", command=["dotnet", "build", "tests/Foo.Tests.csproj"]),
            self.finish("e1"),
            self.start("e2"),
            self.finish("e2"),
        ])
        proc = run_gate("project", data)
        self.assertEqual(proc.returncode, 0, output(proc))
        projected = json.loads(proc.stdout)
        self.assertEqual([e["id"] for e in projected["executions"]], ["e1", "e2"])

    def test_projection_omitting_a_started_execution_is_rejected(self):
        # (e)/(j) The measurable completeness test: a projection that drops a
        # started execution is a completeness failure, not a way to pass.
        data = self.journal([
            self.start("e1", command=["dotnet", "build", "tests/Foo.Tests.csproj"]),
            self.finish("e1"),
            self.start("e2"),
            self.finish("e2"),
        ])
        projected = json.loads(run_gate("project", data).stdout)
        projected["executions"] = [projected["executions"][0]]  # silently drop e2
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = Path(tmp) / "journal.json"
            journal_path.write_text(json.dumps(data), encoding="utf-8")
            proc = run_gate("report", projected)
            self.assertEqual(proc.returncode, 0, output(proc))
            # ... but reconciling it against the raw journal exposes the omission.
            full = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "report",
                    str(self._write(tmp, "report.json", projected)),
                    "--journal",
                    str(journal_path),
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(full.returncode, 2)
        self.assertIn("projection incomplete", output(full))

    @staticmethod
    def _write(tmp, name, payload):
        path = Path(tmp) / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_report_execution_absent_from_journal_rejected(self):
        data = self.journal([
            self.start("e1", command=["dotnet", "build", "tests/Foo.Tests.csproj"]),
            self.finish("e1"),
        ])
        report = valid_report(executions=[
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"], id="e1"),
            exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR], id="e9"),
        ])
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = self._write(tmp, "journal.json", data)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "report",
                    str(self._write(tmp, "report.json", report)),
                    "--journal",
                    str(journal_path),
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("absent from the raw journal", output(proc))


class CleanupReceiptTests(unittest.TestCase):
    """(g)/(l): the ACT cleanup receipt is machine-checked, premature cleanup fails."""

    TASK = "D235"
    EVIDENCE_ROOT = "artifacts/pdca"

    def receipt(self, **overrides):
        receipt = {
            "task": self.TASK,
            "rv": 1,
            "evidence_root": self.EVIDENCE_ROOT,
            "at": "2026-10-16T00:00:00Z",
            "closure": {
                "terminal": True,
                "approved": True,
                "independent_verdict": "pass",
                "final_report": "artifacts/pdca/D235/rv1/final-report.md",
            },
            "frozen_manifest": {"path": "artifacts/pdca/D235/rv1/manifest.json", "sha256": "a" * 64},
            "retained": {
                "final_report": "artifacts/pdca/D235/rv1/final-report.md",
                "frozen_manifest": "artifacts/pdca/D235/rv1/manifest.json",
                "certification": "artifacts/pdca/D235/rv1/check-receipt.json",
                "digests": "artifacts/pdca/D235/rv1/pack-receipt.json",
            },
            "removed": [
                {
                    "path": "artifacts/pdca/D235/rv1/review-pack/src/Foo/Bar.cs",
                    "sha256": "b" * 64,
                    "kind": "staged-copy",
                    "reason": "heavy staged body; the compact records are retained",
                }
            ],
        }
        receipt.update(overrides)
        return receipt

    def test_valid_receipt_rc0(self):
        proc = run_gate("cleanup", self.receipt())
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_premature_cleanup_rejected(self):
        receipt = self.receipt()
        receipt["closure"] = dict(receipt["closure"], terminal=False, approved=False)
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("premature cleanup rejected", output(proc))

    def test_missing_independent_verdict_rejected(self):
        receipt = self.receipt()
        receipt["closure"] = dict(receipt["closure"], independent_verdict="")
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("independent final CHECK verdict", output(proc))

    def test_removing_a_retained_record_rejected(self):
        receipt = self.receipt()
        receipt["removed"] = [
            {
                "path": "artifacts/pdca/D235/rv1/manifest.json",
                "sha256": "c" * 64,
                "kind": "staged-copy",
                "reason": "clean it",
            }
        ]
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("retained record", output(proc))

    def test_deleting_another_task_or_a_broad_pattern_rejected(self):
        for path in (
            "artifacts/pdca/D218/rv1/staged/Foo.cs",
            "artifacts/pdca/D235",
            "artifacts/pdca/D235/rv1",
            "artifacts/pdca/D235/rv1/*",
        ):
            with self.subTest(path=path):
                receipt = self.receipt()
                receipt["removed"] = [
                    {"path": path, "sha256": "c" * 64, "kind": "temp", "reason": "x"}
                ]
                proc = run_gate("cleanup", receipt)
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("outside this task's own rv dir", output(proc))

    def test_absent_prior_hash_rejected(self):
        receipt = self.receipt()
        receipt["removed"][0]["sha256"] = "not-a-digest"
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("prior content digest", output(proc))


class ArchivedPackTests(unittest.TestCase):
    """(l): a missing body is an error unless a valid receipt explains its removal."""

    def _fixture(self, tmp):
        import hashlib

        root = Path(tmp) / "artifacts/pdca/D235/rv1"
        body = root / "review-pack/src/Foo/Bar.cs"
        body.parent.mkdir(parents=True, exist_ok=True)
        body.write_text("class Bar {}\n", encoding="utf-8")
        rel_body = "artifacts/pdca/D235/rv1/review-pack/src/Foo/Bar.cs"
        manifest = {
            "task": "D235",
            "tree": "abc123",
            "status_file": "docs/specs/status/D235-1.md",
            "contract_rv": 1,
            "required_rows": ["E07"],
            "rows": [
                {
                    "id": "E07",
                    "status": "met",
                    "evidence": [{"kind": "staged-body", "path": rel_body}],
                }
            ],
        }
        # The frozen manifest is a protected record of this task's own rv dir, so
        # the fixture keeps it there (the receipt path is canonical and contained).
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        rel_manifest = "artifacts/pdca/D235/rv1/manifest.json"
        receipt = CleanupReceiptTests().receipt()
        receipt["frozen_manifest"] = {
            "path": rel_manifest,
            "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        }
        receipt["retained"]["frozen_manifest"] = rel_manifest
        receipt["removed"][0]["path"] = rel_body
        receipt["removed"][0]["sha256"] = hashlib.sha256(body.read_bytes()).hexdigest()
        receipt_path = Path(tmp) / "cleanup.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        return manifest_path, receipt_path, body

    def test_body_present_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, receipt_path, _ = self._fixture(tmp)
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "archived", str(manifest_path),
                 "--cleanup", str(receipt_path)],
                capture_output=True, text=True, cwd=tmp,
            )
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_cleaned_body_explained_by_receipt_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, receipt_path, body = self._fixture(tmp)
            body.unlink()
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "archived", str(manifest_path),
                 "--cleanup", str(receipt_path)],
                capture_output=True, text=True, cwd=tmp,
            )
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_unexplained_missing_body_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, receipt_path, body = self._fixture(tmp)
            body.unlink()
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["removed"][0]["path"] = "artifacts/pdca/D235/rv1/review-pack/src/Other.cs"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "archived", str(manifest_path),
                 "--cleanup", str(receipt_path)],
                capture_output=True, text=True, cwd=tmp,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("missing staged body", output(proc))

    def test_rewritten_frozen_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path, receipt_path, _ = self._fixture(tmp)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["tree"] = "rewritten"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "archived", str(manifest_path),
                 "--cleanup", str(receipt_path)],
                capture_output=True, text=True, cwd=tmp,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("rewritten after cleanup", output(proc))


class ProjectionFaithfulnessTests(unittest.TestCase):
    """Fix 1: `report --journal` reconciles values, not only execution ids.

    The journal is authoritative: the report unit/scope and every journal-derived
    execution field must match the mechanical projection.  A faithful projection
    still passes; a rewritten result/argv/phase/revision, an invented amendment or
    a reordered/duplicated row is rejected.
    """

    @staticmethod
    def journal():
        return {
            "unit": "D1",
            "scope": valid_scope(),
            "events": [
                {
                    "id": "e1",
                    "event": "start",
                    "phase": "inner",
                    "command": ["dotnet", "build", "tests/Foo.Tests.csproj"],
                    "source_revision": "r1",
                    "artifact_revision": "r1",
                    "at": "2026-10-22T10:00:00Z",
                },
                {
                    "id": "e1",
                    "event": "finish",
                    "state": "finished",
                    "exit_code": 0,
                    "selected_count": 5,
                    "at": "2026-10-22T10:00:20Z",
                    "log": "artifacts/pdca/D1/rv1/logs/e1.log",
                },
                {
                    "id": "e2",
                    "event": "start",
                    "phase": "inner",
                    "command": [
                        "dotnet",
                        "test",
                        "tests/Foo.Tests.csproj",
                        "--no-build",
                        "--filter",
                        SELECTOR,
                    ],
                    "source_revision": "r1",
                    "artifact_revision": "r1",
                    "at": "2026-10-22T10:00:21Z",
                },
                {
                    "id": "e2",
                    "event": "finish",
                    "state": "finished",
                    "exit_code": 0,
                    "selected_count": 7,
                    "at": "2026-10-22T10:00:35Z",
                    "log": "artifacts/pdca/D1/rv1/logs/e2.log",
                },
            ],
        }

    def faithful_report(self):
        proc = run_gate("project", self.journal())
        self.assertEqual(proc.returncode, 0, output(proc))
        return json.loads(proc.stdout)

    def assert_projection_rejected(self, report, *needles):
        proc = run_gate_with_journal(report, self.journal())
        self.assertEqual(proc.returncode, 2, output(proc))
        text = output(proc)
        self.assertIn("projection mismatch", text)
        for needle in needles:
            self.assertIn(needle, text)
        return proc

    def test_exact_faithful_projection_passes(self):
        proc = run_gate_with_journal(self.faithful_report(), self.journal())
        self.assertEqual(proc.returncode, 0, output(proc))
        self.assertNotIn("projection mismatch", output(proc))

    def test_legacy_finished_state_omission_is_canonicalised(self):
        # `state` defaults to finished for a legacy row, exactly as the
        # projection's explicit "finished" value.
        report = self.faithful_report()
        for execution in report["executions"]:
            execution.pop("state")
        proc = run_gate_with_journal(report, self.journal())
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_provenance_omission_does_not_fabricate_a_result(self):
        # The report schema does not mandate journal timestamps/log; omitting
        # provenance cannot fabricate a result, so it stays valid ...
        report = self.faithful_report()
        for execution in report["executions"]:
            for field in ("started_at", "finished_at", "log"):
                execution.pop(field, None)
        proc = run_gate_with_journal(report, self.journal())
        self.assertEqual(proc.returncode, 0, output(proc))
        # ... while a *rewritten* provenance value is a projection mismatch.

    def test_rewritten_exit_code_rejected(self):
        report = self.faithful_report()
        report["executions"][0]["exit_code"] = 1
        self.assert_projection_rejected(report, "exit_code")

    def test_rewritten_selected_count_rejected(self):
        report = self.faithful_report()
        report["executions"][1]["selected_count"] = 8
        self.assert_projection_rejected(report, "selected_count")

    def test_rewritten_state_rejected(self):
        report = self.faithful_report()
        report["executions"][0]["state"] = "canceled"
        self.assert_projection_rejected(report, "state")

    def test_rewritten_command_rejected(self):
        report = self.faithful_report()
        report["executions"][1]["command"] = [
            "dotnet",
            "test",
            "tests/Other.Tests.csproj",
            "--no-build",
            "--filter",
            SELECTOR,
        ]
        self.assert_projection_rejected(report, "command")

    def test_boundary_move_rejected(self):
        report = self.faithful_report()
        report["executions"][0]["phase"] = "boundary"
        self.assert_projection_rejected(report, "phase")

    def test_rewritten_source_revision_rejected(self):
        report = self.faithful_report()
        report["executions"][1]["source_revision"] = "r2"
        self.assert_projection_rejected(report, "source_revision")

    def test_rewritten_artifact_revision_rejected(self):
        report = self.faithful_report()
        report["executions"][0]["artifact_revision"] = "r2"
        self.assert_projection_rejected(report, "artifact_revision")

    def test_rewritten_log_rejected(self):
        report = self.faithful_report()
        report["executions"][1]["log"] = "artifacts/pdca/D1/rv1/logs/other.log"
        self.assert_projection_rejected(report, "log")

    def test_rewritten_started_at_rejected(self):
        report = self.faithful_report()
        report["executions"][0]["started_at"] = "2026-10-22T11:00:00Z"
        self.assert_projection_rejected(report, "started_at")

    def test_report_unit_rewrite_rejected(self):
        report = self.faithful_report()
        report["unit"] = "D2"
        self.assert_projection_rejected(report, "unit")

    def test_report_scope_rewrite_rejected(self):
        report = self.faithful_report()
        report["scope"] = valid_scope(selectors=[SELECTOR, SELECTOR_2])
        self.assert_projection_rejected(report, "scope")

    def test_invented_validated_amendment_rejected(self):
        # A report may not legalise a selector with an amendment the journal
        # never recorded.
        report = self.faithful_report()
        report["amendments"] = [
            {
                "reason": "invented after the fact",
                "added_selectors": [SELECTOR_2],
                "validated_before_run": True,
            }
        ]
        self.assert_projection_rejected(report, "amendments")

    def test_duplicate_report_execution_rejected(self):
        report = self.faithful_report()
        report["executions"].append(json.loads(json.dumps(report["executions"][1])))
        self.assert_projection_rejected(report, "duplicate execution id")

    def test_reordered_projection_rejected(self):
        report = self.faithful_report()
        report["executions"].reverse()
        self.assert_projection_rejected(report, "order differs")

    def test_report_execution_without_id_rejected(self):
        report = self.faithful_report()
        report["executions"][0].pop("id")
        proc = run_gate_with_journal(report, self.journal())
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("must carry the journal execution id", output(proc))

    def test_canceled_run_reported_as_finished_success_rejected(self):
        journal = self.journal()
        journal["events"][3] = {
            "id": "e2",
            "event": "finish",
            "state": "canceled",
            "exit_code": None,
            "selected_count": None,
            "at": "2026-10-22T10:00:35Z",
        }
        fabricated = {
            "unit": "D1",
            "scope": valid_scope(),
            "executions": [
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"], id="e1"),
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build",
                     "--filter", SELECTOR],
                    id="e2",
                    selected_count=7,
                ),
            ],
        }
        proc = run_gate_with_journal(fabricated, journal)
        self.assertEqual(proc.returncode, 2, output(proc))
        text = output(proc)
        self.assertIn("projection mismatch", text)
        self.assertIn("state", text)
        self.assertIn("exit_code", text)

    def test_canceled_run_faithful_projection_is_not_a_projection_mismatch(self):
        journal = self.journal()
        journal["events"][3] = {
            "id": "e2",
            "event": "finish",
            "state": "canceled",
            "exit_code": None,
            "selected_count": None,
            "at": "2026-10-22T10:00:35Z",
        }
        faithful = {
            "unit": "D1",
            "scope": valid_scope(),
            "executions": [
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"], id="e1"),
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build",
                     "--filter", SELECTOR],
                    id="e2",
                    state="canceled",
                    exit_code=None,
                    selected_count=None,
                ),
            ],
        }
        proc = run_gate_with_journal(faithful, journal)
        # The canceled attempt is retained but cannot satisfy success; the
        # projection itself is faithful.
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no finished execution", output(proc))
        self.assertNotIn("projection mismatch", output(proc))

    def test_null_result_omission_for_unfinished_run_is_canonicalised(self):
        journal = self.journal()
        journal["events"][3] = {
            "id": "e2",
            "event": "finish",
            "state": "canceled",
            "exit_code": None,
            "selected_count": None,
            "at": "2026-10-22T10:00:35Z",
        }
        faithful = {
            "unit": "D1",
            "scope": valid_scope(),
            "executions": [
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"], id="e1"),
                {
                    "id": "e2",
                    "command": ["dotnet", "test", "tests/Foo.Tests.csproj",
                                "--no-build", "--filter", SELECTOR],
                    "phase": "inner",
                    "source_revision": "r1",
                    "artifact_revision": "r1",
                    "state": "canceled",
                },
            ],
        }
        proc = run_gate_with_journal(faithful, journal)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertNotIn("projection mismatch", output(proc))

    def test_started_but_never_finished_reported_as_success_rejected(self):
        journal = self.journal()
        journal["events"] = journal["events"][:3]  # e2 started, no finish
        fabricated = {
            "unit": "D1",
            "scope": valid_scope(),
            "executions": [
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"], id="e1"),
                exec_(
                    ["dotnet", "test", "tests/Foo.Tests.csproj", "--no-build",
                     "--filter", SELECTOR],
                    id="e2",
                    selected_count=7,
                ),
            ],
        }
        proc = run_gate_with_journal(fabricated, journal)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("projection mismatch", output(proc))
        self.assertIn("state", output(proc))

    def test_kind_rewrite_rejected(self):
        journal = self.journal()
        journal["events"][0]["kind"] = "build"
        proc = run_gate("project", journal)
        self.assertEqual(proc.returncode, 0, output(proc))
        report = json.loads(proc.stdout)
        report["executions"][0]["kind"] = "other"
        proc = run_gate_with_journal(report, journal)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("projection mismatch", output(proc))
        self.assertIn("kind", output(proc))


class CleanupPathScopeTests(unittest.TestCase):
    """Fix 2: cleanup paths are canonical, portable and inside the exact rv dir.

    The receipt is only data (no filesystem deletion), so these controls never
    create or remove a file: a legitimate inside path is accepted even when it
    does not exist, while traversal/absolute/Windows/mixed-separator spellings and
    neighbour/root/glob targets are rejected.
    """

    def receipt(self, path, task="D235", evidence_root="artifacts/pdca"):
        receipt = CleanupReceiptTests().receipt()
        receipt["task"] = task
        receipt["evidence_root"] = evidence_root
        receipt["removed"] = [
            {"path": path, "sha256": "c" * 64, "kind": "temp", "reason": "staged body"}
        ]
        return receipt

    def assert_rejected(self, path, needle="outside this task's own rv dir"):
        proc = run_gate("cleanup", self.receipt(path))
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn(needle, output(proc))

    def test_traversal_to_neighbour_rejected(self):
        self.assert_rejected("artifacts/pdca/D235/rv1/../../D999/rv9/secret.txt")

    def test_traversal_that_normalises_inside_rejected(self):
        # Even a `..` that resolves back inside is not a canonical receipt path.
        self.assert_rejected("artifacts/pdca/D235/rv1/staged/../copy.bin")

    def test_absolute_path_rejected(self):
        self.assert_rejected("/etc/passwd")

    def test_windows_absolute_path_rejected(self):
        self.assert_rejected("C:\\pdca\\D235\\rv1\\secret.txt")

    def test_mixed_separator_traversal_rejected(self):
        self.assert_rejected("artifacts/pdca/D235/rv1\\..\\D999\\rv9\\secret.txt")

    def test_backslash_path_rejected(self):
        self.assert_rejected("artifacts/pdca/D235/rv1\\staged\\copy.bin")

    def test_direct_neighbour_rejected(self):
        self.assert_rejected("artifacts/pdca/D999/rv9/secret.txt")

    def test_task_root_rv_root_and_glob_rejected(self):
        for path in (
            "artifacts/pdca/D235",
            "artifacts/pdca/D235/rv1",
            "artifacts/pdca/D235/rv1/*",
        ):
            with self.subTest(path=path):
                self.assert_rejected(path)

    def test_prefix_neighbour_and_other_rv_rejected(self):
        for path in (
            "artifacts/pdca/D235X/rv1/staged/copy.bin",
            "artifacts/pdca/D235/rv10/staged/copy.bin",
        ):
            with self.subTest(path=path):
                self.assert_rejected(path)

    def test_legit_inside_path_accepted_without_the_file_existing(self):
        proc = run_gate(
            "cleanup",
            self.receipt("artifacts/pdca/D235/rv1/staged/deep/copy.bin"),
        )
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_legit_inside_path_with_default_evidence_root_accepted(self):
        receipt = self.receipt(".pdca/D235/rv1/staged/copy.bin", evidence_root=".pdca")
        receipt["closure"]["final_report"] = ".pdca/D235/rv1/final-report.md"
        receipt["frozen_manifest"]["path"] = ".pdca/D235/rv1/manifest.json"
        for role in receipt["retained"]:
            receipt["retained"][role] = ".pdca/D235/rv1/%s.json" % role
        receipt["retained"]["frozen_manifest"] = ".pdca/D235/rv1/manifest.json"
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_one_traversal_among_legit_paths_rejected(self):
        receipt = self.receipt("artifacts/pdca/D235/rv1/staged/copy.bin")
        receipt["removed"].append(
            {
                "path": "artifacts/pdca/D235/rv1/../../D999/rv9/secret.txt",
                "sha256": "d" * 64,
                "kind": "temp",
                "reason": "second removal",
            }
        )
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("outside this task's own rv dir", output(proc))

    def test_malformed_task_identifier_rejected(self):
        for task in ("../D235", "D/235", "D 235", ".hidden"):
            with self.subTest(task=task):
                receipt = self.receipt(
                    "artifacts/pdca/D235/rv1/staged/copy.bin", task=task
                )
                proc = run_gate("cleanup", receipt)
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("portable task identifier", output(proc))

    def test_empty_task_rejected(self):
        receipt = self.receipt("artifacts/pdca/D235/rv1/staged/copy.bin", task="")
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("cleanup.task", output(proc))

    def test_retained_traversal_rejected(self):
        receipt = self.receipt("artifacts/pdca/D235/rv1/staged/copy.bin")
        receipt["retained"]["final_report"] = (
            "artifacts/pdca/D235/rv1/../../D999/rv9/final-report.md"
        )
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("cleanup.retained.final_report", output(proc))

    def test_retained_neighbour_rejected(self):
        receipt = self.receipt("artifacts/pdca/D235/rv1/staged/copy.bin")
        receipt["retained"]["certification"] = "artifacts/pdca/D999/rv9/check.json"
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("cleanup.retained.certification", output(proc))

    def test_frozen_manifest_outside_rv_rejected(self):
        receipt = self.receipt("artifacts/pdca/D235/rv1/staged/copy.bin")
        receipt["frozen_manifest"]["path"] = "artifacts/pdca/D235/rv1/../rv2/manifest.json"
        receipt["retained"]["frozen_manifest"] = "artifacts/pdca/D235/rv1/../rv2/manifest.json"
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("frozen_manifest", output(proc))

    def test_frozen_manifest_not_the_retained_one_rejected(self):
        receipt = self.receipt("artifacts/pdca/D235/rv1/staged/copy.bin")
        receipt["frozen_manifest"]["path"] = "artifacts/pdca/D235/rv1/other.json"
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("retained.frozen_manifest", output(proc))

    def test_removing_a_retained_record_rejected(self):
        receipt = self.receipt("artifacts/pdca/D235/rv1/final-report.md")
        proc = run_gate("cleanup", receipt)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("retained record", output(proc))


class InnerCommandScopeTests(unittest.TestCase):
    """Fix 3: the actual command scope is enforced, independently of `kind`."""

    INTEGRATION = "tests/Integration.Tests.csproj"

    def scope(self, **overrides):
        return valid_scope(integration_projects=[self.INTEGRATION], **overrides)

    def integration_executions(self, kind=None):
        executions = [
            exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
            exec_(["dotnet", "test", self.INTEGRATION]),
        ]
        if kind is not None:
            executions[1]["kind"] = kind
        return executions

    def test_kind_other_cannot_launder_an_integration_test(self):
        report = valid_report(
            scope=self.scope(), executions=self.integration_executions(kind="other")
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("does not override the actual scope", output(proc))
        self.assertIn("inside DO", output(proc))

    def test_kind_build_cannot_launder_an_integration_test(self):
        report = valid_report(
            scope=self.scope(), executions=self.integration_executions(kind="build")
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("does not override the actual scope", output(proc))
        self.assertIn("inside DO", output(proc))

    def test_kind_unit_over_integration_project_rejected(self):
        report = valid_report(
            scope=self.scope(), executions=self.integration_executions(kind="unit")
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("not unit", output(proc))
        self.assertIn("inside DO", output(proc))

    def test_kind_integration_inner_rejected(self):
        report = valid_report(
            scope=self.scope(),
            executions=self.integration_executions(kind="integration"),
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("inside DO", output(proc))

    def test_bare_inner_test_rejected(self):
        report = valid_report(scope=docs_scope(), executions=[exec_(["dotnet", "test"])])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no explicit project target", output(proc))

    def test_bare_inner_build_rejected(self):
        report = valid_report(scope=docs_scope(), executions=[exec_(["dotnet", "build"])])
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no explicit project target", output(proc))

    def test_bare_inner_test_with_configuration_rejected(self):
        # `Release` is the value of `-c`, not a project target.
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "-c", "Release"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no explicit project target", output(proc))

    def test_bare_inner_test_with_no_build_rejected(self):
        report = valid_report(
            scope=docs_scope(), executions=[exec_(["dotnet", "test", "--no-build"])]
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no explicit project target", output(proc))

    def test_out_of_scope_test_project_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Other.Tests.csproj",
                       "--filter", SELECTOR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("project out of scope", output(proc))

    def test_out_of_scope_build_project_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "build", "tests/Other.Tests.csproj"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("project out of scope", output(proc))

    def test_scoped_project_inner_allowed(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                       "--filter", SELECTOR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_project_identity_normalisation_allowed(self):
        # Lexical normalisation only: `./` and a redundant in-repo `..` are the
        # same path.  Case is deliberately NOT normalised (see the case-mismatch
        # regression below): the old case-folded identity blessed a different
        # file on a case-sensitive filesystem.
        for token in (
            "./tests/Foo.Tests.csproj",
            "tests/./Foo.Tests.csproj",
            "tests/../tests/Foo.Tests.csproj",
        ):
            with self.subTest(token=token):
                report = valid_report(
                    scope=docs_scope(),
                    executions=[
                        exec_(["dotnet", "test", token, "--filter", SELECTOR])
                    ],
                )
                proc = run_gate("report", report)
                self.assertEqual(proc.returncode, 0, output(proc))

    def test_project_identity_case_mismatch_rejected(self):
        # Deliberate change: identity is exact-case after lexical normalisation.
        # The report carries no filesystem case policy, so on Linux a differently
        # cased path may be a different file outside the affected subset; the gate
        # fails closed instead of inferring a case-insensitive filesystem from the
        # verification host.
        for token in (
            "tests/foo.tests.csproj",     # lowercase filename
            "Tests/Foo.Tests.csproj",     # cased directory
            "tests/Foo.Tests.CSPROJ",     # cased extension
        ):
            with self.subTest(token=token):
                report = valid_report(
                    scope=docs_scope(),
                    executions=[
                        exec_(["dotnet", "test", token, "--filter", SELECTOR])
                    ],
                )
                proc = run_gate("report", report)
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("project out of scope", output(proc))

    def test_lowercase_scope_and_lowercase_command_allowed(self):
        # Positive control: a scope that explicitly declares the lowercase
        # project accepts the identical lowercase command (author and execution
        # use the same case).
        report = valid_report(
            scope=docs_scope(projects=["tests/foo.tests.csproj"]),
            executions=[
                exec_(["dotnet", "test", "tests/foo.tests.csproj",
                       "--filter", SELECTOR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_integration_identity_is_exact_case(self):
        # The integration comparator is the same exact-case identity: a
        # differently cased path is a distinct declared project, not the
        # protected integration project.
        scope = valid_scope(
            projects=[
                "tests/Foo.Tests.csproj",
                "tests/Integration.Tests.csproj",
                "tests/integration.tests.csproj",
            ],
            integration_projects=["tests/Integration.Tests.csproj"],
        )
        exact = valid_report(
            scope=scope,
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                exec_(["dotnet", "test", "tests/Integration.Tests.csproj"]),
            ],
        )
        proc = run_gate("report", exact)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("inside DO", output(proc))

        differently_cased = valid_report(
            scope=scope,
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                exec_(["dotnet", "test", "tests/integration.tests.csproj"]),
            ],
        )
        proc = run_gate("report", differently_cased)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_escaping_or_unportable_project_rejected(self):
        for token in (
            "../Foo.Tests.csproj",
            "tests/../../Foo.Tests.csproj",
            "/abs/tests/Foo.Tests.csproj",
            "C:/tests/Foo.Tests.csproj",
            "tests\\Foo.Tests.csproj",
        ):
            with self.subTest(token=token):
                report = valid_report(
                    scope=docs_scope(),
                    executions=[exec_(["dotnet", "test", token])],
                )
                proc = run_gate("report", report)
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("not a provable portable", output(proc))

    def test_same_basename_in_another_directory_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "tests/Other/Foo.Tests.csproj"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("project out of scope", output(proc))

    def test_option_value_is_not_a_project_target(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj",
                       "-c", "Release"])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_project_option_form_allowed(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "--project", "tests/Foo.Tests.csproj",
                       "--filter", SELECTOR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_project_equals_form_allowed(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "--project=tests/Foo.Tests.csproj",
                       "--filter", SELECTOR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_filter_equals_form_is_checked_against_scope(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                       "--filter=" + SELECTOR_2])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("out of scope", output(proc))

    def test_filter_equals_in_scope_allowed(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                       "--filter=" + SELECTOR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_empty_filter_equals_is_broad(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj", "--filter="])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("broad", output(proc))

    def test_runner_arguments_after_double_dash_are_not_projects(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                       "--filter", SELECTOR, "--", "--foo", "bar"])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_non_test_dotnet_command_preserved(self):
        report = valid_report(
            scope=docs_scope(), executions=[exec_(["dotnet", "restore"])]
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_integration_project_build_only_inner_allowed(self):
        report = valid_report(
            scope=self.scope(),
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                exec_(["dotnet", "build", self.INTEGRATION]),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_integration_project_boundary_test_allowed(self):
        report = valid_report(
            scope=self.scope(),
            executions=[
                exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                exec_(["dotnet", "test", self.INTEGRATION], phase="boundary"),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_out_of_scope_project_is_not_legalised_by_a_selector_amendment(self):
        report = valid_report(
            scope=docs_scope(),
            amendments=[
                {
                    "reason": "shared contract widening",
                    "added_selectors": [SELECTOR_2],
                    "validated_before_run": True,
                }
            ],
            executions=[
                exec_(["dotnet", "test", "tests/Other.Tests.csproj",
                       "--filter", SELECTOR_2])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("project out of scope", output(proc))

    def test_integration_project_normalized_spelling_inner_rejected(self):
        # Classification and membership use the same lexical identity: `./` and
        # `//` spellings of the declared integration project are still that
        # project, so an inner run is a policy violation, not a unit run.
        scope = valid_scope(integration_projects=[self.INTEGRATION])
        for token in (
            self.INTEGRATION,
            "tests/./Integration.Tests.csproj",
            "tests//Integration.Tests.csproj",
        ):
            with self.subTest(token=token):
                report = valid_report(
                    scope=scope,
                    executions=[
                        exec_(["dotnet", "build", "tests/Foo.Tests.csproj"]),
                        exec_(["dotnet", "test", token]),
                    ],
                )
                proc = run_gate("report", report)
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("inside DO", output(proc))

    def test_unit_project_normalized_spelling_allowed(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests//Foo.Tests.csproj",
                       "--filter", SELECTOR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_blame_crash_dump_type_value_is_not_a_project(self):
        # Official VSTest option: `--blame-crash-dump-type <full|mini>` takes a
        # value, so the value is never a positional project target.
        for value in ("full", "mini"):
            with self.subTest(value=value):
                report = valid_report(
                    scope=docs_scope(),
                    executions=[
                        exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                               "--blame-crash-dump-type", value,
                               "--filter", SELECTOR])
                    ],
                )
                proc = run_gate("report", report)
                self.assertEqual(proc.returncode, 0, output(proc))

    def test_blame_crash_dump_type_without_a_project_is_bare(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "--blame-crash-dump-type", "full"])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no explicit project target", output(proc))


class FinalGreenIdentityTests(unittest.TestCase):
    """Finding 3: final green is grouped by the actual project identity."""

    PROJECT_A = "tests/A.Tests.csproj"
    PROJECT_B = "tests/B.Tests.csproj"

    def scope(self):
        return docs_scope(projects=[self.PROJECT_A, self.PROJECT_B])

    def test_option_order_permutation_is_the_same_group(self):
        report = valid_report(
            scope=self.scope(),
            executions=[
                exec_(["dotnet", "test", "-c", "Release",
                       self.PROJECT_A, "--filter", SELECTOR], code=1),
                exec_(["dotnet", "test", self.PROJECT_A, "-c", "Release",
                       "--filter", SELECTOR], code=0),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_same_project_red_then_green_allowed(self):
        report = valid_report(
            scope=self.scope(),
            executions=[
                exec_(["dotnet", "test", self.PROJECT_A,
                       "--filter", SELECTOR], code=1),
                exec_(["dotnet", "test", self.PROJECT_A,
                       "--filter", SELECTOR], code=0),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_different_projects_with_the_same_filter_do_not_hide_red(self):
        report = valid_report(
            scope=self.scope(),
            executions=[
                exec_(["dotnet", "test", self.PROJECT_A,
                       "--filter", SELECTOR], code=1),
                exec_(["dotnet", "test", self.PROJECT_B,
                       "--filter", SELECTOR], code=0),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no final green", output(proc))

    def test_different_projects_without_filter_do_not_hide_red(self):
        report = valid_report(
            scope=self.scope(),
            executions=[
                exec_(["dotnet", "test", self.PROJECT_A], code=1),
                exec_(["dotnet", "test", self.PROJECT_B], code=0),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no final green", output(proc))

    def test_multi_project_command_does_not_absorb_a_red_single_project(self):
        report = valid_report(
            scope=self.scope(),
            executions=[
                exec_(["dotnet", "test", self.PROJECT_A], code=1),
                exec_(["dotnet", "test", self.PROJECT_A, self.PROJECT_B],
                      code=0),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no final green", output(proc))


class JournalFinishOrderTests(unittest.TestCase):
    """Finding 6: terminal green follows the journal's finish-event order."""

    COMMAND = ["dotnet", "test", "tests/Foo.Tests.csproj", "--filter", SELECTOR]

    def journal(self, finishes):
        events = [
            {
                "id": "e1",
                "event": "start",
                "phase": "inner",
                "command": list(self.COMMAND),
                "source_revision": "r1",
                "artifact_revision": "r1",
                "at": "2026-10-22T10:00:00Z",
            },
            {
                "id": "e2",
                "event": "start",
                "phase": "inner",
                "command": list(self.COMMAND),
                "source_revision": "r1",
                "artifact_revision": "r1",
                "at": "2026-10-22T10:00:01Z",
            },
        ]
        for event_id, code in finishes:
            events.append(
                {
                    "id": event_id,
                    "event": "finish",
                    "state": "finished",
                    "exit_code": code,
                    "selected_count": 5,
                    "at": "2026-10-22T10:00:02Z",
                }
            )
        return {"unit": "D1", "scope": docs_scope(), "events": events}

    @staticmethod
    def report(e1_code, e2_code):
        return {
            "unit": "D1",
            "scope": docs_scope(),
            "executions": [
                exec_(list(JournalFinishOrderTests.COMMAND), id="e1", code=e1_code),
                exec_(list(JournalFinishOrderTests.COMMAND), id="e2", code=e2_code),
            ],
        }

    def test_last_completion_red_rejects_despite_start_order(self):
        # e2 finished green first, then e1 finished red: the terminal result of
        # the group is red, so a start-order projection may not pass.
        journal = self.journal([("e2", 0), ("e1", 1)])
        proc = run_gate("project", journal)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no final green", output(proc))

        proc = run_gate_with_journal(self.report(1, 0), journal)
        self.assertEqual(proc.returncode, 2, output(proc))
        self.assertIn("no final green", output(proc))

    def test_serialized_red_then_green_passes(self):
        journal = self.journal([("e1", 1), ("e2", 0)])
        proc = run_gate("project", journal)
        self.assertEqual(proc.returncode, 0, output(proc))

        proc = run_gate_with_journal(self.report(1, 0), journal)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_journal_mode_does_not_judge_terminal_green(self):
        journal = self.journal([("e2", 0), ("e1", 1)])
        proc = run_gate("journal", journal)
        self.assertEqual(proc.returncode, 0, output(proc))


class ShellHygieneTests(unittest.TestCase):
    """Fix 4: an operator inside an argv value is not a shell command."""

    def test_vstest_or_filter_allowed(self):
        report = valid_report(
            scope=docs_scope(selectors=[SEL_OR]),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                       "--filter", SEL_OR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_vstest_or_filter_equals_form_allowed(self):
        report = valid_report(
            scope=docs_scope(selectors=[SEL_OR]),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                       "--filter=" + SEL_OR])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_vstest_and_filter_allowed(self):
        report = valid_report(
            scope=docs_scope(selectors=[SEL_AND]),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                       "--filter", SEL_AND])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_logger_value_with_semicolon_allowed(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "tests/Foo.Tests.csproj",
                       "--filter", SELECTOR,
                       "--logger", "console;verbosity=detailed"])
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_shell_wrapper_rejected(self):
        for command in (
            ["bash", "-c", "dotnet test tests/Foo.Tests.csproj"],
            ["sh", "-c", "dotnet test tests/Foo.Tests.csproj"],
            ["pwsh", "-Command", "dotnet test tests/Foo.Tests.csproj"],
            ["powershell", "-Command", "dotnet test tests/Foo.Tests.csproj"],
        ):
            with self.subTest(command=command):
                report = valid_report(scope=docs_scope(), executions=[exec_(command)])
                proc = run_gate("report", report)
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("shell wrapper", output(proc))

    def test_absolute_shell_wrapper_rejected(self):
        # An absolute/Windows path to the same executable is the same wrapper;
        # the canonical basename is checked across `/`, `\` and `.exe`.
        for command in (
            ["/bin/bash", "-c", "dotnet test tests/Foo.Tests.csproj"],
            ["/bin/sh", "-c", "dotnet test tests/Foo.Tests.csproj"],
            ["C:\\Windows\\System32\\cmd.exe", "/c",
             "dotnet test tests/Foo.Tests.csproj"],
            ["/usr/bin/pwsh", "-Command",
             "dotnet test tests/Foo.Tests.csproj"],
        ):
            with self.subTest(command=command):
                report = valid_report(scope=docs_scope(), executions=[exec_(command)])
                proc = run_gate("report", report)
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("shell wrapper", output(proc))

    def test_standalone_operator_token_rejected(self):
        for operator in ("|", "||", "&&", ";", "&", ">", ">>", "<"):
            with self.subTest(operator=operator):
                command = ["dotnet", "test", "tests/Foo.Tests.csproj",
                           operator, "out.log"]
                report = valid_report(scope=docs_scope(), executions=[exec_(command)])
                proc = run_gate("report", report)
                self.assertEqual(proc.returncode, 2, output(proc))
                self.assertIn("shell wrapper", output(proc))


class SkillBriefExampleTest(unittest.TestCase):
    """The brief example in SKILL.md must itself pass the gate.

    The planner builds the DO brief from this example; a doc/schema drift here
    surfaces only at DO start, as a fail-closed STOP.  The guard below closes
    the loop: extract the example and run it through the real validator.
    """

    REFERENCE = REFERENCE_DIR / "plan.md"

    @staticmethod
    def _example() -> dict:
        text = SkillBriefExampleTest.REFERENCE.read_text(encoding="utf-8")
        section = text.index("### Mandatory `test scope` envelope")
        start = text.index("```json", section)
        body_start = text.index("\n", start) + 1
        end = text.index("```", body_start)
        return json.loads(text[body_start:end])

    def test_example_is_a_brief_not_a_bare_scope(self):
        payload = self._example()
        self.assertIn("unit", payload)
        self.assertIn("scope", payload)
        self.assertNotIn("projects", payload, "scope fields must be nested under `scope`")

    def test_example_passes_the_brief_gate(self):
        payload = self._example()
        proc = run_gate("brief", payload)
        self.assertEqual(0, proc.returncode, output(proc))
        self.assertNotIn("FAIL:", output(proc))


if __name__ == "__main__":
    unittest.main()
