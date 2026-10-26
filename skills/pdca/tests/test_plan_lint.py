"""Behavioural tests for `scripts/plan_lint.py`.

The lint is the mechanical half of the "plan command contract": it reads the
machine projection of a plan's commands and fails the plan when a decisive
command cannot produce a valid result (a selector that matches nothing, an
integration run planned as inner work, a solution build on a constrained host,
an evidence path outside the binding checkout, a green run allowed to select
zero).

These tests execute the script as the executor would, against a throw-away
fixture checkout.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_plan_lint.py' -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts/plan_lint.py"
FIXTURES = HERE / "fixtures/plan_lint"
REPO = FIXTURES / "repo"


class PlanLintCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="plan-lint-"))
        self.repo = self.tmp / "repo"
        shutil.copytree(REPO, self.repo)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_plan(self, name: str = "ok.json", data: dict | None = None) -> Path:
        if data is None:
            raw = (FIXTURES / name).read_text(encoding="utf-8")
            raw = raw.replace("__REPO__", str(self.repo))
            data = json.loads(raw)
        else:
            data = json.loads(json.dumps(data).replace("__REPO__", str(self.repo)))
        path = self.tmp / name
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def run_lint(self, plan: Path, mode: str = "check", *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), mode, "--repo", str(self.repo),
             "--commands", str(plan), "--json", *extra],
            capture_output=True, text=True, timeout=120,
        )

    @staticmethod
    def payload(result: subprocess.CompletedProcess) -> dict:
        return json.loads(result.stdout)

    def messages(self, result: subprocess.CompletedProcess) -> str:
        data = self.payload(result)
        return "\n".join(
            "%s: %s: %s" % (item["id"], item["field"], item["message"])
            for item in data["violations"]
        )


class CheckTest(PlanLintCase):
    def test_valid_plan_passes_and_writes_a_receipt(self) -> None:
        plan = self.write_plan()
        receipt = self.tmp / "plan-lint.json"
        result = self.run_lint(plan, "check", "--receipt", str(receipt))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(self.payload(result)["ok"])
        self.assertEqual(3, self.payload(result)["checked"])
        self.assertTrue(receipt.is_file())
        self.assertTrue(json.loads(receipt.read_text(encoding="utf-8"))["ok"])

    def test_short_method_selector_is_rejected(self) -> None:
        result = self.run_lint(self.write_plan("bad_method.json"))
        self.assertEqual(2, result.returncode)
        text = self.messages(result)
        self.assertIn("not fully-qualified", text)
        self.assertIn("min_selected", text)

    def test_integration_run_as_inner_work_is_rejected(self) -> None:
        result = self.run_lint(self.write_plan("bad_phase.json"))
        self.assertEqual(2, result.returncode)
        text = self.messages(result)
        self.assertIn("integration run planned as inner work", text)
        self.assertIn("timeout_s", text)

    def test_solution_build_is_rejected_against_the_budget(self) -> None:
        result = self.run_lint(self.write_plan("bad_build.json"))
        self.assertEqual(2, result.returncode)
        text = self.messages(result)
        self.assertIn("solution/root build forbidden", text)
        self.assertIn("max_lanes", text)

    def test_argv_shape_shell_wrapper_operator_and_placeholder(self) -> None:
        result = self.run_lint(self.write_plan("bad_argv.json"))
        self.assertEqual(2, result.returncode)
        text = self.messages(result)
        self.assertIn("argv array, not a shell string", text)
        self.assertIn("shell wrapper", text)
        self.assertIn("shell operator", text)
        self.assertIn("unexpanded placeholder", text)

    def test_expected_outcome_rules(self) -> None:
        result = self.run_lint(self.write_plan("bad_expected.json"))
        self.assertEqual(2, result.returncode)
        text = self.messages(result)
        self.assertIn("expected_identity", text)
        self.assertIn("zero selected is a failure", text)

    def test_evidence_root_must_be_the_contract_root(self) -> None:
        # A plan that pins `.pdca/evidence/<task>` has drifted from the base
        # contract root `.pdca/<task>/rv<k>`; the projection is the place to catch it.
        data = json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
        data["evidence_root"] = ".pdca/evidence/T906"
        result = self.run_lint(self.write_plan(data=data))
        self.assertEqual(2, result.returncode)
        self.assertIn("must be the contract root", self.messages(result))

    def test_evidence_root_accepts_the_contract_shape(self) -> None:
        data = json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
        data["evidence_root"] = ".pdca/levenshtein-1/rv2"
        result = self.run_lint(self.write_plan(data=data))
        self.assertNotIn("must be the contract root", self.messages(result))

    def test_evidence_binding_and_checkout_mismatch(self) -> None:
        result = self.run_lint(self.write_plan("bad_evidence.json"))
        self.assertEqual(2, result.returncode)
        text = self.messages(result)
        self.assertIn("not the linted root", text)
        self.assertIn("escapes the linted checkout", text)
        self.assertIn("escapes the repository root", text)

    def test_duplicate_ids_unknown_covers_and_uncovered_units(self) -> None:
        result = self.run_lint(self.write_plan("bad_units.json"))
        self.assertEqual(2, result.returncode)
        text = self.messages(result)
        self.assertIn("duplicate command id", text)
        self.assertIn("unknown unit id", text)
        self.assertIn("unit has no command/evidence owner", text)

    def test_units_sharing_one_verification_get_a_warning_not_a_violation(self) -> None:
        # A "stream" whose only proof is the shared suite is not a unit: the lint says so, but the
        # plan stays admissible — the overlay decides the dispatch count.
        raw = (FIXTURES / "ok.json").read_text(encoding="utf-8").replace("__REPO__", str(self.repo))
        data = json.loads(raw)
        data["units"] = ["code", "tests", "docs"]
        for command in data["commands"]:
            command["covers"] = ["code", "tests", "docs"]
        plan = self.write_plan("shared_units.json", data)
        result = self.run_lint(plan)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        payload = self.payload(result)
        self.assertEqual([], payload["violations"])
        self.assertTrue(
            any("has no command of its own" in warning for warning in payload["warnings"]),
            payload["warnings"],
        )

    def test_malformed_json_is_an_operational_error(self) -> None:
        plan = self.tmp / "broken.json"
        plan.write_text("{ not json", encoding="utf-8")
        result = self.run_lint(plan)
        self.assertEqual(1, result.returncode)

    def test_unknown_selector_target_is_reported(self) -> None:
        data = json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
        data["commands"][2]["argv"][-1] = "Proj.Tests.NoSuchTests"
        result = self.run_lint(self.write_plan(data=data))
        self.assertEqual(2, result.returncode)
        self.assertIn("not found", self.messages(result))

    def test_selector_casing_is_tolerated(self) -> None:
        # Reflection reports the declared casing, runners match case-insensitively;
        # a lowercase selector is not the short-name defect.
        data = json.loads((FIXTURES / "ok.json").read_text(encoding="utf-8"))
        data["commands"][2]["argv"][-1] = "proj.tests.SampleTests"
        result = self.run_lint(self.write_plan(data=data))
        self.assertEqual(0, result.returncode, self.messages(result))


class ProbeTest(PlanLintCase):
    def mutation_doc(self, probe: list[str]) -> dict:
        return {
            "task": "T910",
            "plan_r": 1,
            "commands": [
                {
                    "id": "M",
                    "phase": "inner",
                    "kind": "mutation",
                    "argv": ["dotnet", "stryker", "-f", "stryker-config.json"],
                    "expected": "informational",
                    "timeout_s": 600,
                    "harness_probe": probe,
                }
            ],
        }

    def test_probe_binary_allow_list(self) -> None:
        result = self.run_lint(self.write_plan(data=self.mutation_doc(["bash", "-c", "true"])))
        self.assertEqual(2, result.returncode)
        self.assertIn("allow-list", self.messages(result))

    def test_probe_runs_a_whitelisted_command(self) -> None:
        result = self.run_lint(self.write_plan(data=self.mutation_doc(["git", "--version"])), "probe")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        data = self.payload(result)
        self.assertEqual(1, data["probes_executed"])
        self.assertEqual(0, data["probes"][0]["exit"])

    def test_probe_failure_is_a_violation_with_its_exit(self) -> None:
        plan = self.write_plan(data=self.mutation_doc(
            ["git", "rev-parse", "--verify", "definitely-not-a-ref-xyz"]))
        result = self.run_lint(plan, "probe")
        self.assertEqual(2, result.returncode)
        self.assertIn("probe failed", self.messages(result))


class SkillWiringTest(unittest.TestCase):
    """The base plan reference names the helper and the receipt row.

    The bulky command contract lives in `references/plan.md`; the base keeps only the
    pointer, so the wiring is asserted over that reference.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (HERE.parent / "SKILL.md").read_text(encoding="utf-8")
        cls.plan_reference = (HERE.parent / "references/plan.md").read_text(encoding="utf-8")
        cls.corpus = cls.skill + "\n" + cls.plan_reference
        cls.scenarios = (HERE / "scenarios.md").read_text(encoding="utf-8")

    def test_skill_documents_the_projection_and_cli(self) -> None:
        for phrase in (
            "Machine projection: `commands.json` and `plan_lint.py`",
            "plan_lint.py check --repo",
            "plan_lint.py probe",
            "`PLAN-LINT`",
            "Exit codes `0` ok, `2` violation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.corpus)

    def test_scenario_covers_a_failing_projection(self) -> None:
        self.assertIn("R9. Машинная проекция плана не проходит проверку", self.scenarios)
        self.assertIn("`plan_lint.py check` выходит с `2`", self.scenarios)


if __name__ == "__main__":
    unittest.main()
