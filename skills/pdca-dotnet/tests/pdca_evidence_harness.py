#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdca_evidence_harness.py - negative / coverage / mutation harness.

Modes::

    pdca_evidence_harness.py negative --output <dir>
    pdca_evidence_harness.py coverage --output <dir>
    pdca_evidence_harness.py mutate   --output <dir>

* ``negative`` - replays every stale-fixture case from the tracked recipe
  ``fixtures/pdca_evidence/cases.json`` against a fresh disposable Git fixture in a **child
  process**; requires child rc == 2 with a diagnostic naming path + field, and that ``lint``
  never modifies the publication (before/after digests).  Harness rc 0 only when every case
  behaves.
* ``coverage`` - runs the unittest suite in-process under the stdlib ``trace`` module and
  measures line coverage of ``scripts/pdca_evidence.py``.  rc 0 only at >= 90% executable
  lines; the summary maps every changed decision outcome to a test or an explicit guard.
* ``mutate`` - applies a fixed set of source mutations to a temp copy of the toolkit (disable
  the tree-equality check, the tree recomputation, the receipt enumeration, the missing-file
  check, the required_rows coverage check and the pre-publication guard), runs the suite
  against each; every non-equivalent mutant must be killed.  Everything is restored in
  ``finally``.

Disposable fixtures are built at runtime under ``tempfile.mkdtemp(prefix="pdca-evidence-")``
and removed afterwards; the real repository history is never touched.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import trace
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
SCRIPTS = os.path.join(SKILL_DIR, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import pdca_evidence as pdca  # noqa: E402  (path bootstrap above)

CASES_PATH = os.path.join(HERE, "fixtures", "pdca_evidence", "cases.json")
COVERAGE_THRESHOLD = 90.0

# Changed decision outcomes -> a covering test (validated to exist) or an explicit guard.
DECISION_MAP = [
    ("clean generation -> rc0", "CleanGenerationTests::test_generate_rc0"),
    ("manifest.tree != recomputed -> rc2", "NegativeLintTests::test_stale_manifest_tree"),
    ("receipt.tree stale -> rc2", "NegativeLintTests::test_stale_receipt_tree"),
    ("receipt.tree_binding stale -> rc2", "NegativeLintTests::test_stale_receipt_tree_binding"),
    ("missing referenced receipt -> rc2", "NegativeLintTests::test_missing_referenced_receipt"),
    ("missing evidence file -> rc2", "NegativeLintTests::test_missing_evidence_file"),
    ("degenerate/absent tree -> rc2", "NegativeLintTests::test_degenerate_trees_parameterized"),
    ("unreferenced receipt enumerated -> rc2", "NegativeLintTests::test_unreferenced_receipt"),
    ("legacy non-40-hex in scope -> rc2", "NegativeLintTests::test_legacy_non_hex_in_scope"),
    ("outside-scope revision untouched -> rc0", "ScopeTests::test_outside_scope_not_scanned"),
    ("footprint changed after freeze -> rc2", "NegativeLintTests::test_footprint_changed"),
    ("path escape -> rc2", "NegativeLintTests::test_path_escape_result"),
    ("duplicate row id -> rc2", "NegativeLintTests::test_duplicate_receipt_id"),
    ("HEAD^{tree} claim -> rc2", "NegativeLintTests::test_head_tree_claim"),
    ("required row missing from rows -> rc2",
     "NegativeLintTests::test_required_row_missing_from_rows"),
    ("row not declared in required_rows -> rc2",
     "NegativeLintTests::test_row_not_declared_in_required_rows"),
    ("injected failure before publication -> rc2 + rollback",
     "PublicationTests::test_injected_failure_rolls_back"),
    ("lock contention -> rc1 without clobber", "PublicationTests::test_lock_contention"),
    ("rv2 while rv1 exists -> rv1 intact", "ScopeTests::test_rv2_preserves_rv1"),
    ("idempotent publication byte-identical", "CleanGenerationTests::test_idempotent_generation"),
    ("manifest schema guards", "guard:scripts/validate_inner_loop.py manifest mode"),
    ("argparse usage error -> rc1", "guard:_ArgumentParser.error maps to exit 1"),
]

MUTATIONS = [
    {
        "name": "disable-tree-equality-check",
        "old": "    if manifest_tree != recomputed:",
        "new": "    if False:",
    },
    {
        "name": "disable-tree-recomputation",
        "old": "    recomputed = compute_frozen_tree(repo, base_ref, footprint, exclusions)",
        "new": "    recomputed = manifest.get(\"tree\")",
    },
    {
        "name": "disable-receipt-enumeration",
        "old": "    discovered = _discover_scope_json(scope)",
        "new": "    discovered = []",
    },
    {
        "name": "disable-missing-file-check",
        "old": "    if not os.path.exists(path):",
        "new": "    if False:",
    },
    {
        "name": "disable-required-rows-coverage",
        "old": "    if required_set is not None:",
        "new": "    if False:",
    },
    {
        "name": "disable-pre-publication-guard",
        "old": "        if guard:",
        "new": "        if False:",
    },
]


# --------------------------------------------------------------------------- fixtures


def run_git(args, repo):
    proc = subprocess.run(
        ["git"] + list(args),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if proc.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), proc.stderr.strip()))
    return proc.stdout.strip()


def run_cli(args, repo, env=None):
    """Invoke the CLI in a child process; returns (rc, stdout, stderr)."""
    child_env = dict(os.environ)
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        child_env.update(env)
    proc = subprocess.run(
        [sys.executable, pdca.__file__] + list(args),
        cwd=repo,
        env=child_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _write(path, text):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as stream:
        stream.write(text)


def build_fixture(root):
    """Create a disposable git repo + contract + evidence file.  Returns a dict of paths."""
    repo = os.path.join(root, "repo")
    os.makedirs(repo)
    run_git(["init", "-q", "."], repo)
    _write(os.path.join(repo, "tool.py"), "x = 1\n")
    _write(os.path.join(repo, "notes.md"), "notes\n")
    output = os.path.join(repo, "artifacts", "pdca", "TEST", "rv1")
    _write(os.path.join(output, "logs", "ev1.log"), "evidence\n")
    run_git(["add", "-A"], repo)
    run_git(["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], repo)
    base = run_git(["rev-parse", "HEAD"], repo)
    # Uncommitted footprint change so the frozen synthetic tree differs from the base tree.
    _write(os.path.join(repo, "tool.py"), "x = 2\n")
    contract = {
        "task": "TEST",
        "issue": "#0",
        "status_file": "docs/specs/status/DTEST.md",
        "path": "artifacts/pdca/TEST/rv1",
        "base_ref": base,
        "collection_baseline_ref": base,
        "footprint": ["tool.py", "notes.md"],
        "exclusions": ["artifacts/**", "docs/specs/status/**"],
        "contract_rv": 2,
        "supersedes": {"rv": 1, "artifacts": "none"},
        "required_rows": ["N1", "N2", "N3"],
        "rows": [
            {
                "id": "N1",
                "status": "met",
                "requirements": ["R1"],
                "predicate": "rc==0",
                "evidence": [
                    {
                        "kind": "log",
                        "path": "artifacts/pdca/TEST/rv1/logs/ev1.log",
                        "exit": 0,
                    }
                ],
            },
            {"id": "N2", "status": "open", "requirements": ["R2"], "reason": "out-of-workspace"},
            {"id": "N3", "status": "na", "requirements": ["R3"], "predicate": "not applicable"},
        ],
    }
    contract_path = os.path.join(root, "contract.json")
    _write(contract_path, json.dumps(contract, indent=2, sort_keys=True))
    return {
        "repo": repo,
        "output": output,
        "contract": contract_path,
        "manifest": os.path.join(output, "manifest.json"),
        "base": base,
    }


def load_manifest(fixture):
    with open(fixture["manifest"], "r", encoding="utf-8") as stream:
        return json.load(stream)


def receipt_path(fixture, row_id="N1"):
    manifest = load_manifest(fixture)
    row = next(r for r in manifest["rows"] if r["id"] == row_id)
    return os.path.join(fixture["output"], row["result"])


def publication_digest(fixture):
    """Digest of every file under the output dir (relative path + content)."""
    entries = []
    for dirpath, _dirnames, filenames in os.walk(fixture["output"]):
        for name in filenames:
            if name == ".pdca-evidence.lock":
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, fixture["output"]).replace(os.sep, "/")
            with open(full, "rb") as stream:
                entries.append((rel, hashlib.sha256(stream.read()).hexdigest()))
    entries.sort()
    blob = json.dumps(entries, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _resolve_placeholder(token, fixture):
    manifest = load_manifest(fixture)
    if token == "TREE":
        return manifest["tree"]
    if token == "BASE_TREE":
        return run_git(["rev-parse", "HEAD^{tree}"], fixture["repo"])
    if token == "ZERO40":
        return "0" * 40
    if token == "EMPTY":
        return ""
    if token == "MALFORMED":
        return "1.0.9"
    raise ValueError("unknown placeholder $%s" % token)


def _resolve_value(value, fixture):
    if isinstance(value, str) and value.startswith("$"):
        return _resolve_placeholder(value[1:], fixture)
    return value


def _target_path(fixture, target):
    if "*" in target:
        import glob

        matches = glob.glob(os.path.join(fixture["output"], target))
        if not matches:
            raise RuntimeError("target glob matched nothing: %s" % target)
        return matches[0]
    return os.path.join(fixture["output"], target)


def apply_mutation(case, fixture):
    """Apply a declarative mutation recipe to the generated publication."""
    op = case["op"]
    if op == "set_field":
        path = _target_path(fixture, case["target"])
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
        _set_path(data, case["path"], _resolve_value(case["value"], fixture))
        _write(path, json.dumps(data, indent=2, sort_keys=True))
    elif op == "delete_field":
        path = _target_path(fixture, case["target"])
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
        _delete_path(data, case["path"])
        _write(path, json.dumps(data, indent=2, sort_keys=True))
    elif op == "delete_file":
        path = _target_path(fixture, case["target"])
        os.remove(path)
    elif op == "write_result":
        path = _target_path(fixture, case["target"])
        _write(path, json.dumps(_resolve_content(case["content"], fixture), indent=2, sort_keys=True))
    elif op == "write_receipt":
        import glob

        matches = glob.glob(os.path.join(fixture["output"], "generations", "*", "results"))
        if not matches:
            raise RuntimeError("no results dir to write into")
        path = os.path.join(matches[0], case["filename"])
        _write(path, json.dumps(_resolve_content(case["content"], fixture), indent=2, sort_keys=True))
    elif op == "modify_footprint_file":
        _write(os.path.join(fixture["repo"], case["target"]), case["content"])
    else:
        raise ValueError("unknown case op: %s" % op)


def _resolve_content(content, fixture):
    if isinstance(content, dict):
        return {key: _resolve_content(value, fixture) for key, value in content.items()}
    if isinstance(content, list):
        return [_resolve_content(item, fixture) for item in content]
    if isinstance(content, str) and content.startswith("$"):
        return _resolve_placeholder(content[1:], fixture)
    return content


def _set_path(data, dotted, value):
    keys = dotted.split(".")
    node = data
    for key in keys[:-1]:
        if key.isdigit() and isinstance(node, list):
            node = node[int(key)]
        else:
            node = node[key]
    last = keys[-1]
    if last.isdigit() and isinstance(node, list):
        node[int(last)] = value
    else:
        node[last] = value


def _delete_path(data, dotted):
    keys = dotted.split(".")
    node = data
    for key in keys[:-1]:
        if key.isdigit() and isinstance(node, list):
            node = node[int(key)]
        else:
            node = node[key]
    last = keys[-1]
    if last.isdigit() and isinstance(node, list):
        del node[int(last)]
    else:
        del node[last]


def load_cases():
    with open(CASES_PATH, "r", encoding="utf-8") as stream:
        return json.load(stream)


# ------------------------------------------------------------------------ mode: negative


def mode_negative(output_dir):
    cases = load_cases()["cases"]
    os.makedirs(output_dir, exist_ok=True)
    results = []
    all_ok = True
    for case in cases:
        root = tempfile.mkdtemp(prefix="pdca-evidence-")
        try:
            fixture = build_fixture(root)
            rc, _out, err = run_cli(
                ["generate", "--repo", ".", "--contract", fixture["contract"],
                 "--output", fixture["output"]], fixture["repo"])
            if rc != 0:
                raise RuntimeError("clean generation failed for %s: %s" % (case["name"], err))
            apply_mutation(case, fixture)
            mutated_digest = publication_digest(fixture)
            rc, _out, err = run_cli(
                ["lint", "--repo", ".", "--manifest", fixture["manifest"]], fixture["repo"])
            lint_digest = publication_digest(fixture)
            expect_field = case["expect_field"]
            field_marker = "field %s:" % expect_field
            ok = (
                rc == case.get("expect_rc", 2)
                and field_marker in err
                and mutated_digest == lint_digest
            )
            all_ok = all_ok and ok
            results.append(
                {
                    "name": case["name"],
                    "argv": ["lint", "--repo", ".", "--manifest", fixture["manifest"]],
                    "rc": rc,
                    "expect_rc": case.get("expect_rc", 2),
                    "expect_field": expect_field,
                    "diagnostic": err.strip(),
                    "field_named": field_marker in err,
                    "mutation_digest": mutated_digest,
                    "lint_digest": lint_digest,
                    "unmodified_by_lint": mutated_digest == lint_digest,
                    "passed": ok,
                }
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)
    summary = {
        "mode": "negative",
        "total": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "all_passed": all_ok,
        "cases": results,
    }
    _write_summary(output_dir, summary)
    return 0 if all_ok else 1


def _write_summary(output_dir, summary):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")


# ------------------------------------------------------------------------ mode: coverage


def _collect_test_ids(suite, acc=None):
    if acc is None:
        acc = set()
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            _collect_test_ids(item, acc)
        else:
            acc.add(item.id())
    return acc


def _suite_contains(ids, dotted):
    needle = dotted.replace("::", ".")
    return any(item.endswith(needle) or needle in item for item in ids)


def mode_coverage(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    loader = unittest.TestLoader()
    suite = loader.discover(HERE, pattern="test_pdca_evidence.py")
    test_ids = _collect_test_ids(suite)

    tracer = trace.Trace(count=1, trace=0, ignoredirs=[sys.prefix, sys.exec_prefix])

    def run():
        # Re-execute the module body under the tracer so import-time lines are attributed.
        import importlib

        importlib.reload(pdca)
        runner = unittest.TextTestRunner(stream=open(os.devnull, "w"), verbosity=0)
        return runner.run(suite)

    result = tracer.runfunc(run)
    counts = tracer.results().counts

    target = os.path.realpath(pdca.__file__)
    executable = trace._find_executable_linenos(target)
    covered = set(lineno for (filename, lineno) in counts if os.path.realpath(filename) == target)
    executable_lines = set(executable.keys())
    hit = executable_lines & covered
    percent = 100.0 * len(hit) / len(executable_lines) if executable_lines else 0.0

    decision_map = []
    mapping_ok = True
    for outcome, covered_by in DECISION_MAP:
        if covered_by.startswith("guard:"):
            verified = True
        else:
            verified = _suite_contains(test_ids, covered_by)
        mapping_ok = mapping_ok and verified
        decision_map.append({"outcome": outcome, "covered_by": covered_by, "verified": verified})

    missing = sorted(executable_lines - covered)
    passed = (
        result.wasSuccessful()
        and percent >= COVERAGE_THRESHOLD
        and mapping_ok
    )
    summary = {
        "mode": "coverage",
        "tests_run": result.testsRun,
        "tests_failed": len(result.failures) + len(result.errors),
        "executable_lines": len(executable_lines),
        "covered_lines": len(hit),
        "line_coverage_percent": round(percent, 2),
        "threshold": COVERAGE_THRESHOLD,
        "uncovered_lines": missing,
        "decision_map": decision_map,
        "decision_map_verified": mapping_ok,
        "passed": passed,
    }
    _write_summary(output_dir, summary)
    return 0 if passed else 1


# ------------------------------------------------------------------------ mode: mutation


def _copy_toolkit(destination):
    os.makedirs(os.path.join(destination, "scripts"), exist_ok=True)
    shutil.copy2(pdca.__file__, os.path.join(destination, "scripts", "pdca_evidence.py"))
    shutil.copytree(
        HERE,
        os.path.join(destination, "tests"),
        dirs_exist_ok=True,
    )


def mode_mutate(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    source_path = os.path.realpath(pdca.__file__)
    with open(source_path, "r", encoding="utf-8") as stream:
        original = stream.read()

    results = []
    all_killed = True
    for mutation in MUTATIONS:
        if mutation["old"] not in original:
            results.append(
                {
                    "name": mutation["name"],
                    "anchor": mutation["old"],
                    "killed": False,
                    "reason": "anchor not found in source",
                }
            )
            all_killed = False
            continue
        root = tempfile.mkdtemp(prefix="pdca-evidence-")
        try:
            _copy_toolkit(root)
            mutant_path = os.path.join(root, "scripts", "pdca_evidence.py")
            mutated = original.replace(mutation["old"], mutation["new"])
            _write(mutant_path, mutated)
            tests_dir = os.path.join(root, "tests")
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", tests_dir,
                 "-p", "test_pdca_evidence.py"],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            )
            killed = proc.returncode != 0
            all_killed = all_killed and killed
            log_path = os.path.join(output_dir, "mutant-%s.log" % mutation["name"])
            _write(log_path, proc.stdout)
            results.append(
                {
                    "name": mutation["name"],
                    "anchor": mutation["old"],
                    "suite_rc": proc.returncode,
                    "killed": killed,
                    "log": os.path.relpath(log_path, output_dir),
                }
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    summary = {
        "mode": "mutation",
        "total": len(results),
        "killed": sum(1 for item in results if item["killed"]),
        "all_killed": all_killed,
        "mutants": results,
    }
    _write_summary(output_dir, summary)
    return 0 if all_killed else 1


# ------------------------------------------------------------------------------- cli


def build_parser():
    parser = argparse.ArgumentParser(prog="pdca_evidence_harness.py")
    sub = parser.add_subparsers(dest="mode")
    sub.required = True
    for name in ("negative", "coverage", "mutate"):
        child = sub.add_parser(name)
        child.add_argument("--output", required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {"negative": mode_negative, "coverage": mode_coverage, "mutate": mode_mutate}
    return handlers[args.mode](args.output)


if __name__ == "__main__":
    sys.exit(main())
