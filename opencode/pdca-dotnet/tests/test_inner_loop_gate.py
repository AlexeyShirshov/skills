"""Scenario gate tests for validate_inner_loop.py.

The gate itself is exercised as a subprocess (`sys.executable` +
`subprocess.run`) against JSON fixtures written to a temporary directory.  The
module's internals are deliberately not imported, so these tests also prove the
documented CLI contract (argv, exit codes, `FAIL:`/`ERROR:` output) and that no
supplied command is ever executed.

Run:
    python3 -m unittest discover -s opencode/pdca-dotnet/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_ROOT = HOST_REPO  # host repo root, for its README
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"
CONFIG_AGENTS = (CONFIG / "agents") if CONFIG else None

SCRIPT = SKILL_DIR / "scripts/validate_inner_loop.py"
SKILL = SKILL_DIR / "SKILL.md"
EN_CODER = SKILL_DIR / "assets/agents/pdca-executor.md"
# The RU coder brief is a host artifact (config/agents) and needs the host repo.
RU_CODER = CONFIG_AGENTS / "coder.md" if CONFIG_AGENTS else None

SELECTOR = "FullyQualifiedName~Foo.Tests.BarTests"
SELECTOR_2 = "FullyQualifiedName~Shared.Tests.ContractTests"


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
        bad = exec_(["dotnet", "test", "proj", "--filter", SELECTOR])
        del bad["selected_count"]
        proc = run_gate("report", valid_report(scope=docs_scope(), executions=[bad]))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("selected_count", output(proc))

    def test_zero_selected_count_rejected(self):
        # A nonempty selector that runtime-matched zero tests is rejected.
        proc = run_gate("report", valid_report(
            scope=docs_scope(),
            executions=[
                exec_(["dotnet", "test", "proj", "--filter", SELECTOR], selected_count=0)
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
            executions=[exec_(["dotnet", "test", "proj", "--filter", "*"])],
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
            executions=[exec_(["dotnet", "test", "proj", "--filter", SELECTOR_2])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_silent_widening_rejected(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[exec_(["dotnet", "test", "proj", "--filter", SELECTOR_2])],
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
            executions=[exec_(["dotnet", "test", "proj", "--filter", SELECTOR_2])],
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
            executions=[exec_(["dotnet", "test", "proj", "--filter", SELECTOR])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_docs_only_fictitious_rebuild_rejected(self):
        # GAP 2: a docs-only scope (no compiled file) must not claim an
        # affected rebuild.
        report = valid_report(
            scope=valid_scope(files=["docs/notes.md"], rebuild="affected"),
            executions=[exec_(["dotnet", "build", "proj"])],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("fictitious rebuild for docs-only scope", output(proc))

    def test_release_options_preserved_rc0(self):
        report = valid_report(
            scope=docs_scope(),
            executions=[
                exec_(
                    ["dotnet", "test", "proj", "-c", "Release",
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
                    ["dotnet", "test", "proj", "-c", "Debug", "--filter", SELECTOR]
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
                    ["dotnet", "test", "proj", "-c", "Release",
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
                exec_(["dotnet", "test", "proj", "--filter", SELECTOR], code=1),
                exec_(["dotnet", "test", "proj", "--filter", SELECTOR], code=0),
            ],
        )
        proc = run_gate("report", report)
        self.assertEqual(proc.returncode, 0, output(proc))

    def test_missing_exit_code_rejected(self):
        bad = exec_(["dotnet", "test", "proj", "--filter", SELECTOR])
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
            executions=[exec_(["dotnet", "test", "proj", "--filter", SELECTOR], code=1)],
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
                    ["dotnet", "test", "proj", "--filter", SELECTOR], phase="boundary"
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
                exec_(["dotnet", "build", "proj"], phase="boundary", source="r2", artifact="r1")
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
                exec_(["dotnet", "build", "proj", "&&", "dotnet", "build", "proj"])
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
                    ["dotnet", "test", "proj", "--filter", SELECTOR],
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
                    ["dotnet", "test", "proj", "--filter", SELECTOR], source=""
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
                    ["dotnet", "test", "proj", "--filter", SELECTOR], artifact=""
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
                    ["dotnet", "test", "proj", "--filter", SELECTOR], code=True
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
                    ["dotnet", "test", "proj", "--filter", SELECTOR],
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
            ["dotnet", "test", "proj", "-filter"],
            ["dotnet", "test", "proj", "--filter"],
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
    """Contract-wiring guards: the SKILL must carry the executable inner-loop gate.

    Rule-presence only, tied to real content: reads the sibling ``SKILL.md`` as
    text (path relative to this test file) and asserts the validator wiring is
    stated.  It never executes a model or the PDCA cycle.
    """

    @classmethod
    def setUpClass(cls):
        cls.raw = SKILL.read_text(encoding="utf-8")
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
            "integration runs happen only at the do → check boundary", text
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
                "without it the orchestrator must NOT dispatch the brief", ""
            )
        )

    def test_negative_check_fail_not_warn_removed_detected(self):
        self._assert_mutation_detected(
            self.raw.replace("never warns", "sometimes warns")
        )

    def test_negative_boundary_once_removed_detected(self):
        self._assert_mutation_detected(
            self.raw.replace(
                "Integration runs happen only at the DO → CHECK boundary",
                "Integration runs may happen anywhere in the cycle",
            )
        )

    def test_negative_unit_unlimited_removed_detected(self):
        # The phrase wraps across lines in the raw Markdown; mutate it as written.
        self._assert_mutation_detected(
            self.raw.replace("Unit runs are\n  unlimited**", "Unit runs are\n  capped**")
        )

    def test_negative_test_scope_phrase_removed_detected(self):
        self._assert_mutation_detected(
            re.sub(r"(?i)test scope", "test may", self.raw)
        )


class _CoderParityMixin:
    """Shared D3 inner-loop bullet guards for the coder bodies in ``ANCHORS``.

    Rule-presence only: reads the coder Markdown bodies as text (paths resolved
    relative to this test file / the host repo) and asserts the standalone bullet
    is present, that it sits between the Evidence and Git bullets, and that it
    encodes the key concepts with wording-robust RU+EN regexes.  It never
    executes an agent or the cycle.
    """

    # Stable bold prefixes introduced by D3 (RU and EN wording).
    ANCHORS: dict = {}
    EVIDENCE: dict = {}

    @classmethod
    def setUpClass(cls):
        cls.texts = {
            path: path.read_text(encoding="utf-8") for path in cls.ANCHORS
        }

    def _bullet(self, text, path):
        """Return the inner-loop bullet text from its anchor to the next item."""
        anchor = self.ANCHORS[path]
        rest = text[text.index(anchor):]
        match = re.search(r"\n(?=- \*\*|#{1,6}\s)", rest)
        return rest[: match.start()] if match else rest

    def assert_parity(self, texts):
        """Assert both bodies carry the anchor, concepts and Evidence→Git order."""
        for path, anchor in self.ANCHORS.items():
            self.assertIn(anchor, texts[path])
        for path in self.ANCHORS:
            bullet = self._bullet(texts[path], path).lower()
            # affected subset (RU поднабор/затронут / EN affected/subset)
            self.assertRegex(bullet, r"affected|затронут|поднабор|subset")
            # both run kinds are named and distinguished (E10)
            self.assertRegex(bullet, r"unit")
            self.assertRegex(bullet, r"integration|интеграц")
            # the filter is explicitly NOT the classification criterion
            self.assertRegex(bullet, r"filter|фильтр")
            # stream / DO→CHECK boundary for integration
            self.assertRegex(bullet, r"boundary|границ")
            # prohibition of the whole solution (a whole *unit project* run is legal)
            self.assertRegex(bullet, r"whole solution|всё решение")
            # the ledger is projected from the raw journal
            self.assertRegex(bullet, r"journal|журнал")
        for path in self.ANCHORS:
            text = texts[path]
            evidence = text.index(self.EVIDENCE[path])
            anchor = text.index(self.ANCHORS[path])
            git = text.index("**Git.**")
            self.assertLess(evidence, anchor)
            self.assertLess(anchor, git)

    def test_both_bodies_carry_the_inner_loop_bullet(self):
        self.assert_parity(self.texts)

    def test_bullet_concepts_affected_filter_boundary_no_whole_project(self):
        self.assert_parity(self.texts)

    def test_bullet_sits_between_evidence_and_git(self):
        self.assert_parity(self.texts)

    def test_negative_dropped_inner_loop_anchor_detected(self):
        # Dropping one body's inner-loop anchor must make the parity check fail,
        # proving it is load-bearing (not presence-only decoration).
        mutated = dict(self.texts)
        mutated[EN_CODER] = mutated[EN_CODER].replace("**Inner loop", "**Inner work")
        self.assertNotEqual(mutated[EN_CODER], self.texts[EN_CODER])
        with self.assertRaises(AssertionError):
            self.assert_parity(mutated)


class CoderParityTests(_CoderParityMixin, unittest.TestCase):
    """D3 guards: the published EN coder asset carries the inner-loop bullet.

    The RU host body (``config/agents/coder.md``) lives in the `opencode-config`
    repo, so the two-body RU+EN parity guards are host-gated in
    ``HostCoderParityTests`` below.
    """

    ANCHORS = {EN_CODER: "**Inner loop"}
    EVIDENCE = {EN_CODER: "Evidence, not claims"}


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class HostCoderParityTests(_CoderParityMixin, unittest.TestCase):
    """D3 guards: both coder bodies (EN asset + RU host brief) stay in parity."""

    ANCHORS = {EN_CODER: "**Inner loop", RU_CODER: "**Внутренний цикл"}
    EVIDENCE = {
        EN_CODER: "Evidence, not claims",
        RU_CODER: "Доказательства, а не заявления",
    }


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
        manifest_path = Path(tmp) / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        receipt = CleanupReceiptTests().receipt()
        receipt["frozen_manifest"] = {
            "path": "manifest.json",
            "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        }
        receipt["retained"]["frozen_manifest"] = "manifest.json"
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


if __name__ == "__main__":
    unittest.main()
