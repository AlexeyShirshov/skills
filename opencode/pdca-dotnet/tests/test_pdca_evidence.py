#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stdlib unittest suite for ``scripts/pdca_evidence.py``.

Run from the skill directory::

    python3 -m unittest discover -s tests -p 'test_pdca_evidence.py'

Every test builds a disposable Git repository under ``tempfile.mkdtemp(prefix="pdca-evidence-")``
at runtime and removes it afterwards; the real repository history is never touched.
"""

import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pdca_evidence as pdca  # noqa: E402
import pdca_evidence_harness as harness  # noqa: E402

CASES = {case["name"]: case for case in harness.load_cases()["cases"]}


class FixtureCase(unittest.TestCase):
    """Base: a disposable repo + contract + evidence file per test."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pdca-evidence-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.fx = harness.build_fixture(self.root)

    # --- helpers ---------------------------------------------------------
    def generate(self, contract=None, output=None):
        return pdca.main(
            [
                "generate",
                "--repo", self.fx["repo"],
                "--contract", contract or self.fx["contract"],
                "--output", output or self.fx["output"],
            ]
        )

    def lint(self, manifest=None, scope=None):
        args = ["lint", "--repo", self.fx["repo"], "--manifest", manifest or self.fx["manifest"]]
        if scope:
            args += ["--scope-root", scope]
        return pdca.main(args)

    def lint_capture(self, **kwargs):
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = self.lint(**kwargs)
        return rc, buf.getvalue()

    def apply_case(self, name):
        harness.apply_mutation(CASES[name], self.fx)

    def edit_manifest(self, mutator, path=None):
        path = path or self.fx["manifest"]
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
        mutator(data)
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)

    def results_dir(self):
        manifest = harness.load_manifest(self.fx)
        return os.path.dirname(os.path.join(self.fx["output"], manifest["rows"][0]["result"]))

    def reset_publication(self):
        """Remove the manifest + generations so a fresh generation can run (keeps evidence)."""
        manifest = self.fx["manifest"]
        if os.path.exists(manifest):
            os.remove(manifest)
        shutil.rmtree(os.path.join(self.fx["output"], "generations"), ignore_errors=True)

    def write_contract(self, name, mutator):
        with open(self.fx["contract"], "r", encoding="utf-8") as stream:
            contract = json.load(stream)
        mutator(contract)
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(contract, stream, indent=2, sort_keys=True)
        return path

    def generate_quiet(self, contract=None):
        with contextlib.redirect_stderr(io.StringIO()):
            return self.generate(contract=contract)

    @staticmethod
    def read_bytes(path):
        with open(path, "rb") as stream:
            return stream.read()


class CleanGenerationTests(FixtureCase):
    def test_generate_rc0(self):
        self.assertEqual(self.generate(), 0)
        self.assertTrue(os.path.isfile(self.fx["manifest"]))
        manifest = harness.load_manifest(self.fx)
        self.assertEqual(manifest["tree"], manifest["tree_binding"])
        self.assertEqual(manifest["contract_rv"], 2)
        self.assertEqual(manifest["supersedes"], {"rv": 1, "artifacts": "none"})
        self.assertEqual(self.lint(), 0)

    def test_generate_returns_manifest_path(self):
        returned = pdca.generate(self.fx["repo"], self.fx["contract"], self.fx["output"])
        self.assertEqual(returned, self.fx["manifest"])

    def test_idempotent_generation(self):
        self.assertEqual(self.generate(), 0)
        first = harness.publication_digest(self.fx)
        self.assertEqual(self.generate(), 0)
        second = harness.publication_digest(self.fx)
        self.assertEqual(first, second)

    def test_receipts_repeat_tree_and_binding(self):
        self.assertEqual(self.generate(), 0)
        manifest = harness.load_manifest(self.fx)
        for row in manifest["rows"]:
            with open(os.path.join(self.fx["output"], row["result"]), "r", encoding="utf-8") as fh:
                receipt = json.load(fh)
            self.assertEqual(receipt["tree"], manifest["tree"])
            self.assertEqual(receipt["tree_binding"], manifest["tree"])

    def test_manifest_validates_with_validate_inner_loop(self):
        self.assertEqual(self.generate(), 0)
        sys.path.insert(0, SCRIPTS)
        import validate_inner_loop

        with open(self.fx["manifest"], "r", encoding="utf-8") as stream:
            manifest = json.load(stream)
        self.assertEqual(validate_inner_loop.validate_manifest(manifest), [])


class NegativeLintTests(FixtureCase):
    def _expect_violation(self, case_name, marker):
        self.assertEqual(self.generate(), 0)
        self.apply_case(case_name)
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2, "case %s: %s" % (case_name, err))
        self.assertIn(marker, err)

    def test_stale_manifest_tree(self):
        self._expect_violation("stale-manifest-tree", "field tree:")

    def test_stale_manifest_tree_binding(self):
        self._expect_violation("stale-manifest-tree-binding", "field tree_binding:")

    def test_stale_receipt_tree(self):
        self._expect_violation("stale-receipt-tree", "field tree:")

    def test_stale_receipt_tree_binding(self):
        self._expect_violation("stale-receipt-tree-binding", "field tree_binding:")

    def test_missing_referenced_receipt(self):
        self._expect_violation("missing-referenced-receipt", "field rows[1].result:")

    def test_missing_evidence_file(self):
        self._expect_violation("missing-evidence-file", "field evidence[0].path:")

    def test_unreferenced_receipt(self):
        self._expect_violation("unreferenced-receipt-stale-tree", "field tree:")

    def test_legacy_non_hex_in_scope(self):
        self._expect_violation("legacy-non-40-hex-receipt", "malformed tree")

    def test_footprint_changed(self):
        self._expect_violation("footprint-changed-after-freeze", "recomputed frozen tree")

    def test_path_escape_result(self):
        self._expect_violation("path-escape-result", "path escapes allowed root")

    def test_duplicate_receipt_id(self):
        self._expect_violation("duplicate-receipt-id", "duplicate row id")

    def test_head_tree_claim(self):
        self._expect_violation("head-tree-equality-claim", "HEAD^{tree} equality")

    def test_degenerate_trees_parameterized(self):
        for case_name, marker in (
            ("degenerate-empty-tree", "degenerate tree: empty string"),
            ("degenerate-zero-tree", "degenerate tree: zero hash"),
            ("malformed-tree", "malformed tree: not 40-hex"),
            ("absent-tree-key", "tree key absent"),
        ):
            with self.subTest(case=case_name):
                self.reset_publication()
                self.assertEqual(self.generate(), 0)
                self.apply_case(case_name)
                rc, err = self.lint_capture()
                self.assertEqual(rc, 2)
                self.assertIn(marker, err)

    def test_unresolvable_tree(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda data: data.__setitem__("tree", "a" * 40))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("not resolvable", err)

    def test_manifest_tree_method_negation_not_a_claim(self):
        self.assertEqual(self.generate(), 0)
        self.assertEqual(self.lint(), 0)

    def test_head_tree_claim_in_list(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda data: data.__setitem__("exclusions", ["HEAD^{tree}"]))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("HEAD^{tree} equality", err)

    def test_manifest_top_level_not_object(self):
        self.assertEqual(self.generate(), 0)
        with open(self.fx["manifest"], "w", encoding="utf-8") as stream:
            stream.write(json.dumps([1, 2, 3]))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("top-level JSON must be an object", err)

    def test_malformed_receipt_json(self):
        self.assertEqual(self.generate(), 0)
        path = os.path.join(self.results_dir(), "N2.json")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("{ not json")
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("malformed JSON", err)

    def test_absolute_evidence_path(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d["rows"][0]["evidence"][0].__setitem__("path", "/etc/passwd"))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("absolute path not allowed", err)

    def test_empty_evidence_path_and_kind(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d["rows"][0]["evidence"][0].__setitem__("path", ""))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("must be a non-empty string", err)

    def test_evidence_item_not_object(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d["rows"][0].__setitem__("evidence", ["x"]))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("evidence entry must be an object", err)

    def test_met_row_empty_evidence(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d["rows"][0].__setitem__("evidence", []))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("non-empty evidence list", err)

    def test_duplicate_manifest_row_id(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d["rows"][1].__setitem__("id", "N1"))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("duplicate row id", err)

    def test_required_row_missing_from_rows(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(
            lambda d: d.__setitem__("rows", [r for r in d["rows"] if r["id"] != "N2"])
        )
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("required row missing from manifest: 'N2'", err)

    def test_row_not_declared_in_required_rows(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("required_rows", ["N1", "N3"]))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("manifest row not declared in required_rows: 'N2'", err)

    def test_required_rows_missing(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.pop("required_rows"))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("required_rows must be a nonempty list", err)

    def test_required_rows_not_list(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("required_rows", {}))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("required_rows must be a nonempty list", err)

    def test_required_rows_empty(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("required_rows", []))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("required_rows must be a nonempty list", err)

    def test_required_rows_non_string(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("required_rows", ["N1", "", "N3"]))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("required_rows entries must be non-empty strings", err)

    def test_required_rows_duplicate(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("required_rows", ["N1", "N1", "N2"]))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("required_rows contains duplicate ids", err)

    def test_manifest_base_ref_missing(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.pop("base_ref"))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("base_ref must be a non-empty string", err)

    def test_manifest_footprint_missing(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.pop("footprint"))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("footprint must be a non-empty list", err)

    def test_manifest_exclusions_not_list(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("exclusions", "x"))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("exclusions must be a list", err)

    def test_manifest_rows_not_list(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("rows", {}))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("rows must be a list", err)

    def test_manifest_row_not_object(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("rows", ["x"]))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("row must be an object", err)

    def test_manifest_tree_not_string(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("tree", 123))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("tree must be a string", err)

    def test_recompute_failure_bad_base_ref(self):
        self.assertEqual(self.generate(), 0)
        self.edit_manifest(lambda d: d.__setitem__("base_ref", "no-such-ref-xyz"))
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("cannot recompute frozen tree", err)

    def test_receipt_missing_id(self):
        self.assertEqual(self.generate(), 0)
        path = os.path.join(self.results_dir(), "N3.json")
        with open(path, "w", encoding="utf-8") as stream:
            json.dump({"status": "na", "tree": harness.load_manifest(self.fx)["tree"]}, stream)
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertIn("receipt id must be a non-empty string", err)


class ScopeTests(FixtureCase):
    def test_outside_scope_not_scanned(self):
        self.assertEqual(self.generate(), 0)
        outside = os.path.join(os.path.dirname(self.fx["output"]), "rv0")
        os.makedirs(outside)
        outside_manifest = os.path.join(outside, "manifest.json")
        with open(outside_manifest, "w", encoding="utf-8") as stream:
            json.dump({"task": "TEST", "tree": "1.0.9", "status_file": "x"}, stream)
        before = self.read_bytes(outside_manifest)
        self.assertEqual(self.lint(), 0)
        self.assertEqual(self.read_bytes(outside_manifest), before)
        # The sibling is genuinely invalid when explicitly selected.
        rc, err = self.lint_capture(manifest=outside_manifest, scope=outside)
        self.assertEqual(rc, 2)
        self.assertIn("malformed tree", err)

    def test_rv2_preserves_rv1(self):
        self.assertEqual(self.generate(), 0)
        rv1_digest = harness.publication_digest(self.fx)
        rv2_output = os.path.join(self.fx["repo"], "artifacts", "pdca", "TEST", "rv2")
        contract = self.write_contract(
            "rv2-contract.json",
            lambda c: (c.__setitem__("path", "artifacts/pdca/TEST/rv2"),
                       c.__setitem__("supersedes", {"rv": 1, "artifacts": "none"})),
        )
        self.assertEqual(self.generate(contract=contract, output=rv2_output), 0)
        self.assertEqual(harness.publication_digest(self.fx), rv1_digest)
        with open(os.path.join(rv2_output, "manifest.json"), "r", encoding="utf-8") as stream:
            rv2 = json.load(stream)
        self.assertEqual(rv2["supersedes"], {"rv": 1, "artifacts": "none"})
        self.assertEqual(self.lint(manifest=os.path.join(rv2_output, "manifest.json")), 0)

    def test_preflight_stale_refuses_to_regenerate(self):
        self.assertEqual(self.generate(), 0)
        before = self.read_bytes(self.fx["manifest"])
        with open(os.path.join(self.fx["repo"], "tool.py"), "w", encoding="utf-8") as stream:
            stream.write("x = 99\n")
        rc, err = self.lint_capture()
        self.assertEqual(rc, 2)
        self.assertEqual(self.generate(), 2)
        self.assertEqual(self.read_bytes(self.fx["manifest"]), before)


class AttemptSnapshotTests(FixtureCase):
    """Operational recipe: same contract, new attempt => fresh child output, prior retained."""

    def _attempt(self, name):
        return os.path.join(self.fx["output"], "attempts", name)

    def _generate_cli(self, output):
        return harness.run_cli(
            ["generate", "--repo", ".", "--contract", self.fx["contract"],
             "--output", output],
            self.fx["repo"],
        )

    def _lint_cli(self, manifest):
        return harness.run_cli(
            ["lint", "--repo", ".", "--manifest", manifest],
            self.fx["repo"],
        )

    def test_same_contract_new_attempt_uses_fresh_child_and_preserves_prior(self):
        first = self._attempt("c1-r1-n1")
        second = self._attempt("c1-r1-n2")

        rc, _out, err = self._generate_cli(first)
        self.assertEqual(rc, 0, err)
        first_manifest = os.path.join(first, "manifest.json")
        with open(first_manifest, "r", encoding="utf-8") as stream:
            first_doc = json.load(stream)
        self.assertEqual(first_doc["contract_rv"], 2)
        self.assertEqual(self._lint_cli(first_manifest)[0], 0)

        first_digest = harness.publication_digest({"output": first})
        first_bytes = self.read_bytes(first_manifest)

        # The product changes under the same contract revision.
        with open(os.path.join(self.fx["repo"], "tool.py"), "w", encoding="utf-8") as stream:
            stream.write("x = 3\n")

        # Re-using the old child must hit the helper's stale preflight refusal.
        rc, _out, err = self._generate_cli(first)
        self.assertEqual(rc, 2)
        self.assertIn("preflight: existing evidence is stale", err)
        self.assertEqual(self.read_bytes(first_manifest), first_bytes)
        self.assertEqual(harness.publication_digest({"output": first}), first_digest)

        # A fresh child generates and lints; the prior snapshot stays intact.
        rc, _out, err = self._generate_cli(second)
        self.assertEqual(rc, 0, err)
        second_manifest = os.path.join(second, "manifest.json")
        with open(second_manifest, "r", encoding="utf-8") as stream:
            second_doc = json.load(stream)
        self.assertEqual(second_doc["contract_rv"], 2)
        self.assertNotEqual(first_doc["tree"], second_doc["tree"])
        self.assertEqual(self._lint_cli(second_manifest)[0], 0)
        self.assertEqual(self.read_bytes(first_manifest), first_bytes)
        self.assertEqual(harness.publication_digest({"output": first}), first_digest)

    def test_next_cycle_same_rv_uses_distinct_child_and_preserves_prior(self):
        cycle_one = self._attempt("c1-r1-n1")
        cycle_two = self._attempt("c2-r1-n1")

        rc, _out, err = self._generate_cli(cycle_one)
        self.assertEqual(rc, 0, err)
        first_manifest = os.path.join(cycle_one, "manifest.json")
        with open(first_manifest, "r", encoding="utf-8") as stream:
            first_doc = json.load(stream)
        first_bytes = self.read_bytes(first_manifest)
        first_digest = harness.publication_digest({"output": cycle_one})

        # Same task, same rv/r/n, next cycle N+1: a distinct child, not a collision.
        rc, _out, err = self._generate_cli(cycle_two)
        self.assertEqual(rc, 0, err)
        second_manifest = os.path.join(cycle_two, "manifest.json")
        with open(second_manifest, "r", encoding="utf-8") as stream:
            second_doc = json.load(stream)
        self.assertNotEqual(cycle_one, cycle_two)
        self.assertTrue(os.path.isfile(second_manifest))
        self.assertEqual(first_doc["contract_rv"], second_doc["contract_rv"])
        self.assertEqual(first_doc["tree"], second_doc["tree"])
        self.assertEqual(self._lint_cli(first_manifest)[0], 0)
        self.assertEqual(self._lint_cli(second_manifest)[0], 0)
        self.assertEqual(self.read_bytes(first_manifest), first_bytes)
        self.assertEqual(harness.publication_digest({"output": cycle_one}), first_digest)


class PublicationTests(FixtureCase):
    def test_injected_failure_rolls_back(self):
        os.environ[pdca.FAIL_BEFORE_PUBLISH_ENV] = "1"
        self.addCleanup(os.environ.pop, pdca.FAIL_BEFORE_PUBLISH_ENV, None)
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = self.generate()
        self.assertEqual(rc, 2)
        self.assertIn("injected pre-publication failure", buf.getvalue())
        self.assertFalse(os.path.exists(self.fx["manifest"]))
        generations = os.path.join(self.fx["output"], "generations")
        leftover = [
            os.path.join(dirpath, name)
            for dirpath, _dirs, names in os.walk(generations)
            for name in names
        ]
        self.assertEqual(leftover, [])
        self.assertFalse(os.path.exists(os.path.join(self.fx["output"], ".pdca-evidence.lock")))

    def test_injected_failure_preserves_prior_publication(self):
        self.assertEqual(self.generate(), 0)
        prior_digest = harness.publication_digest(self.fx)
        prior_manifest = self.read_bytes(self.fx["manifest"])
        contract = self.write_contract(
            "changed-contract.json",
            lambda c: c["rows"][0].__setitem__("predicate", "different"),
        )
        os.environ[pdca.FAIL_BEFORE_PUBLISH_ENV] = "1"
        self.addCleanup(os.environ.pop, pdca.FAIL_BEFORE_PUBLISH_ENV, None)
        with contextlib.redirect_stderr(io.StringIO()):
            rc = self.generate(contract=contract)
        self.assertEqual(rc, 2)
        self.assertEqual(self.read_bytes(self.fx["manifest"]), prior_manifest)
        self.assertEqual(harness.publication_digest(self.fx), prior_digest)

    def test_lock_contention(self):
        os.makedirs(self.fx["output"], exist_ok=True)
        lock = os.path.join(self.fx["output"], ".pdca-evidence.lock")
        with open(lock, "w", encoding="utf-8") as stream:
            stream.write("held\n")
        self.assertEqual(self.generate(), 1)
        self.assertTrue(os.path.exists(lock))
        self.assertFalse(os.path.exists(self.fx["manifest"]))
        os.remove(lock)

    def test_lock_released_after_success(self):
        self.assertEqual(self.generate(), 0)
        self.assertFalse(os.path.exists(os.path.join(self.fx["output"], ".pdca-evidence.lock")))


class UsageTests(FixtureCase):
    def test_argparse_usage_error_exit_1(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                pdca.main(["generate"])
        self.assertEqual(ctx.exception.code, 1)

    def test_missing_manifest_operational_error(self):
        rc, _err = self.lint_capture(manifest=os.path.join(self.root, "nope.json"))
        self.assertEqual(rc, 1)

    def test_contract_top_level_not_object(self):
        path = os.path.join(self.root, "c.json")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(json.dumps([1, 2]))
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_malformed_json(self):
        path = os.path.join(self.root, "bad.json")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("{ bad")
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_missing_key(self):
        path = self.write_contract("missing.json", lambda c: c.pop("issue"))
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_footprint_overlaps_exclusion(self):
        path = self.write_contract(
            "overlap.json", lambda c: c.__setitem__("footprint", ["artifacts/x"])
        )
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_empty_footprint(self):
        path = self.write_contract("emptyfp.json", lambda c: c.__setitem__("footprint", []))
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_duplicate_required_rows(self):
        path = self.write_contract(
            "dupreq.json", lambda c: c.__setitem__("required_rows", ["N1", "N1"])
        )
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_duplicate_row_ids(self):
        path = self.write_contract(
            "duprows.json", lambda c: c["rows"][1].__setitem__("id", "N1")
        )
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_required_row_without_definition(self):
        path = self.write_contract(
            "nodef.json", lambda c: c.__setitem__("required_rows", ["N1", "N9"])
        )
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_rows_not_list(self):
        path = self.write_contract("rowsnotlist.json", lambda c: c.__setitem__("rows", {}))
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_required_rows_not_list(self):
        path = self.write_contract(
            "reqnotlist.json", lambda c: c.__setitem__("required_rows", {})
        )
        self.assertEqual(self.generate_quiet(contract=path), 1)

    def test_contract_bad_base_ref(self):
        path = self.write_contract(
            "badbase.json", lambda c: c.__setitem__("base_ref", "no-such-ref-xyz")
        )
        self.assertEqual(self.generate_quiet(contract=path), 1)


class MinimumManifestTests(FixtureCase):
    """The documented minimum manifest is genuinely usable by *both* mechanical gates.

    §"Frozen evidence manifest" of ``SKILL.md`` states the joint requirement of
    ``validate_inner_loop.py manifest`` (row/evidence shape + coverage) and
    ``pdca_evidence.py lint`` (frozen-tree binding).  A hand-written minimum built from
    that list must pass both, every *required* field must be rejected by its owning gate
    when omitted, and the optional metadata (``tree_binding``/``tree_method``) must be
    accepted both present and absent.  The document is not a second schema source: the
    guard below mirrors the two helpers, not a new contract.
    """

    SKILL = os.path.join(os.path.dirname(HERE), "SKILL.md")

    def _minimum(self):
        footprint = ["tool.py", "notes.md"]
        exclusions = ["artifacts/**"]
        tree = pdca.compute_frozen_tree(self.fx["repo"], self.fx["base"], footprint, exclusions)
        return {
            "task": "TEST",
            "status_file": "docs/specs/status/DTEST.md",
            "contract_rv": 1,
            "tree": tree,
            "base_ref": self.fx["base"],
            "footprint": footprint,
            "exclusions": exclusions,
            "required_rows": ["N1", "N2"],
            "rows": [
                {
                    "id": "N1",
                    "status": "met",
                    "evidence": [{"kind": "log", "path": "notes.md", "exit": 0}],
                },
                {"id": "N2", "status": "open", "reason": "not observed yet"},
            ],
        }

    def _write_minimum(self, mutate=None):
        directory = os.path.join(self.root, "minimum")
        os.makedirs(directory, exist_ok=True)
        manifest = self._minimum()
        if mutate:
            mutate(manifest)
        path = os.path.join(directory, "manifest.json")
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True)
        return path

    @staticmethod
    def _shape_gate():
        """The other tracked helper: row/evidence shape + coverage (never the tree)."""
        sys.path.insert(0, SCRIPTS)
        import validate_inner_loop

        return validate_inner_loop.validate_manifest

    def test_documented_minimum_passes_both_gates(self):
        path = self._write_minimum()
        rc, err = self.lint_capture(manifest=path)
        self.assertEqual(rc, 0, err)
        with open(path, "r", encoding="utf-8") as stream:
            self.assertEqual(self._shape_gate()(json.load(stream)), [])

    def test_optional_metadata_is_accepted_present_or_absent(self):
        path = self._write_minimum()
        self.assertEqual(self.lint(manifest=path), 0)
        with open(path, "r", encoding="utf-8") as stream:
            self.assertEqual(self._shape_gate()(json.load(stream)), [])

        def add_optional(data):
            data["tree_binding"] = data["tree"]
            data["tree_method"] = pdca.TREE_METHOD

        path = self._write_minimum(add_optional)
        self.assertEqual(self.lint(manifest=path), 0)
        with open(path, "r", encoding="utf-8") as stream:
            self.assertEqual(self._shape_gate()(json.load(stream)), [])

    def test_omitting_a_required_field_is_rejected_by_its_gate(self):
        # field -> (lint rejects, shape gate rejects)
        for field, lint_rejects, shape_rejects in (
            ("task", False, True),
            ("status_file", False, True),
            ("contract_rv", False, True),
            ("tree", True, True),
            ("base_ref", True, False),
            ("footprint", True, False),
            ("exclusions", True, False),
            ("required_rows", True, True),
            ("rows", True, True),
        ):
            with self.subTest(field=field):
                path = self._write_minimum(lambda data, key=field: data.pop(key))
                rc, _err = self.lint_capture(manifest=path)
                self.assertEqual(rc == 2, lint_rejects,
                                 "%s: lint rejected=%s, expected %s"
                                 % (field, rc == 2, lint_rejects))
                with open(path, "r", encoding="utf-8") as stream:
                    violations = self._shape_gate()(json.load(stream))
                self.assertEqual(bool(violations), shape_rejects,
                                 "%s: shape gate violations=%r" % (field, violations))

    def test_tree_binding_when_present_must_equal_the_frozen_tree(self):
        path = self._write_minimum(
            lambda data: data.__setitem__("tree_binding", "a" * 40)
        )
        rc, err = self.lint_capture(manifest=path)
        self.assertEqual(rc, 2)
        self.assertIn("manifest tree_binding != tree", err)

    def test_absolute_and_traversing_evidence_paths_are_rejected(self):
        for value, marker in (
            ("/etc/passwd", "absolute path not allowed"),
            ("../../etc/passwd", "path escapes allowed root"),
        ):
            with self.subTest(path=value):
                path = self._write_minimum(
                    lambda data, bad=value: data["rows"][0]["evidence"][0].__setitem__(
                        "path", bad
                    )
                )
                rc, err = self.lint_capture(manifest=path)
                self.assertEqual(rc, 2, err)
                self.assertIn(marker, err)

    def test_skill_minimum_content_names_the_joint_required_fields(self):
        with open(self.SKILL, "r", encoding="utf-8") as stream:
            text = stream.read()
        start = text.index("Minimum content")
        end = text.index("**No PASS while any BINDING/APPLICABLE `required_rows`", start)
        block = re.sub(r"\s+", " ", text[start:end])
        for token in (
            "`task`",
            "`status_file`",
            "`contract_rv`",
            "`tree`",
            "`base_ref`",
            "`footprint`",
            "`exclusions`",
            "`required_rows`",
            "`rows[]`",
        ):
            with self.subTest(token=token):
                self.assertIn(token, block)
        # Responsibility is split between the two helpers, not claimed for the lint alone.
        self.assertIn("`validate_inner_loop.py manifest`", block)
        self.assertIn("`pdca_evidence.py lint`", block)
        self.assertNotIn("lint gate below is authoritative", block)
        # Optional metadata is not presented as a gate requirement.
        optional = block[block.index("Optional metadata"):]
        self.assertIn("`tree_binding`", optional)
        self.assertIn("`tree_method`", optional)
        self.assertIn("may be omitted", optional)
        # The old prose permitted an absolute evidence path the helper safely denies.
        self.assertNotIn("repo-relative/absolute", block)
        self.assertIn("repo-relative and contained in the repository", block)


if __name__ == "__main__":
    unittest.main()
