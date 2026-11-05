#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdca_evidence.py - atomic PDCA evidence generator + strict scoped lint.

Implements the mechanical side of the skill's "Versioned evidence contract".  Standard
library only (Python 3.8+); no pytest, no pyproject, no third-party dependency.

Two subcommands::

    generate --repo <root> --contract <contract.json> --output <dir>
    lint     --repo <root> --manifest <manifest.json> [--scope-root <dir>]

``generate`` resolves a *frozen synthetic tree* (see ``TREE_METHOD`` below), writes one
immutable receipt per required row under
``<output>/generations/<content-digest>/results/<row-id>.json`` and finally replaces the
root ``<output>/manifest.json`` atomically (``os.replace`` from a temp file in the same
directory).  It never invents executions and never turns an ``open`` row into ``met``.

``lint`` recomputes the frozen tree with the same recipe and requires
``manifest.tree == recomputed == every receipt's tree == every receipt's tree_binding``.
It also requires the manifest's ``required_rows`` and ``rows[]`` to cover each other
exactly: a required row without a row entry and a row entry not declared in
``required_rows`` are both violations.  It enumerates *every* ``*.json`` under the selected
revision's ``generations/**/results/`` (recursively, including unreferenced ones) plus
``results/``/``receipts/`` directories when present.  The lint targets exactly one
explicitly selected revision directory (default: the manifest's own directory); unrelated
historical revisions are never scanned or modified.

Exit codes: ``0`` success; ``2`` validation violation (diagnostic names offending path +
field); ``1`` usage/operational error.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
ZERO40 = "0" * 40

# Written verbatim into the manifest ("tree_method").
TREE_METHOD = (
    "Synthetic tree: seed an isolated index with `git read-tree <base_ref>^{tree}`, "
    "run `git add -A -- <recorded footprint paths>` using the evaluated contents, then "
    "`git write-tree`. `.pdca/**` is excluded from the "
    "overlay, not removed from the base tree. Reconcile by repeating this recipe; after ACT, "
    "use committed footprint contents. The resulting tree is not asserted to equal "
    "`HEAD^{tree}`."
)

DEFAULT_EXCLUSIONS = (".pdca/**",)

# Environment hook used only by tests to simulate a pre-publication candidate-check failure.
FAIL_BEFORE_PUBLISH_ENV = "PDCA_EVIDENCE_FAIL_BEFORE_PUBLISH"


class EvidenceError(Exception):
    """Base error; ``exit_code`` is the process status to report."""

    exit_code = 1


class UsageError(EvidenceError):
    """Usage or operational error (bad arguments, git/IO failure) -> exit 1."""

    exit_code = 1


class Violation(EvidenceError):
    """Validation violation -> exit 2.  Carries human-readable diagnostics."""

    exit_code = 2

    def __init__(self, diagnostics):
        if isinstance(diagnostics, str):
            diagnostics = [diagnostics]
        self.diagnostics = list(diagnostics)
        super(Violation, self).__init__("; ".join(self.diagnostics))


class Diags(object):
    """Collect ``"path: field <name>: message"`` diagnostics."""

    def __init__(self):
        self.items = []

    def add(self, path, field, message):
        self.items.append("%s: field %s: %s" % (path, field, message))

    def __bool__(self):
        return bool(self.items)

    __nonzero__ = __bool__


# --------------------------------------------------------------------------- git helpers


def _git(args, repo, env=None):
    """Run git in ``repo``; raise ``UsageError`` on non-zero status."""
    proc = subprocess.run(
        ["git"] + list(args),
        cwd=repo,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if proc.returncode != 0:
        raise UsageError(
            "git %s failed (%d): %s"
            % (" ".join(args), proc.returncode, proc.stderr.strip())
        )
    return proc.stdout.strip()


def _git_type(repo, object_id):
    """Return the ``git cat-file -t`` type for ``object_id`` or ``None``."""
    proc = subprocess.run(
        ["git", "cat-file", "-t", object_id],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def resolve_base_tree(repo, base_ref):
    """Resolve ``<base_ref>^{tree}`` to a full tree object id."""
    if not base_ref or not isinstance(base_ref, str):
        raise UsageError("base_ref must be a non-empty string")
    tree = _git(["rev-parse", "%s^{tree}" % base_ref], repo)
    if not HEX40_RE.match(tree):
        raise UsageError("could not resolve a tree for base_ref %r: %r" % (base_ref, tree))
    return tree


def _under_exclusion(path, exclusions):
    """Return the exclusion pattern that covers ``path``, else ``None``."""
    candidate = path.rstrip("/")
    for pattern in exclusions or ():
        base = pattern.rstrip("*").rstrip("/")
        if base and (candidate == base or candidate.startswith(base + "/")):
            return pattern
    return None


def validate_footprint(footprint, exclusions):
    """Reject an empty footprint or one overlapping an exclusion."""
    if not footprint:
        raise UsageError("contract footprint must be a non-empty list")
    for path in footprint:
        if not isinstance(path, str) or not path:
            raise UsageError("footprint entries must be non-empty strings: %r" % (path,))
        hit = _under_exclusion(path, exclusions)
        if hit is not None:
            raise UsageError("footprint path %r is covered by exclusion %r" % (path, hit))


def compute_frozen_tree(repo, base_ref, footprint, exclusions):
    """Frozen synthetic tree: isolated index <- base tree, overlay footprint, write-tree."""
    validate_footprint(footprint, exclusions)
    base_tree = resolve_base_tree(repo, base_ref)
    handle, index_path = tempfile.mkstemp(prefix="pdca-evidence-index-")
    os.close(handle)
    os.unlink(index_path)
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = index_path
    try:
        _git(["read-tree", base_tree], repo, env)
        _git(["add", "-A", "--"] + list(footprint), repo, env)
        tree = _git(["write-tree"], repo, env)
    finally:
        if os.path.exists(index_path):
            try:
                os.remove(index_path)
            except OSError:
                pass
    if not HEX40_RE.match(tree):
        raise UsageError("git write-tree returned an invalid object id: %r" % (tree,))
    return tree


# ------------------------------------------------------------------------ json / fs utils


def canonical_bytes(obj):
    """Deterministic JSON bytes: sorted keys, fixed indent, UTF-8, trailing newline."""
    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False)
    return text.encode("utf-8") + b"\n"


def _write_atomic(path, data):
    """Write ``data`` to ``path`` via a temp file in the same directory + os.replace."""
    directory = os.path.dirname(os.path.abspath(path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    handle, tmp = tempfile.mkstemp(dir=directory, prefix=".tmp-pdca-")
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


def _parse_json_file(path):
    """Parse a JSON object file.  Malformed JSON is a violation (exit 2)."""
    try:
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
    except OSError as exc:
        raise UsageError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise Violation(["%s: field <json>: malformed JSON: %s" % (path, exc)])
    if not isinstance(data, dict):
        raise Violation(["%s: field <json>: top-level JSON must be an object" % (path,)])
    return data


def _load_json_object(path, label):
    try:
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
    except OSError as exc:
        raise UsageError("cannot read %s (%s): %s" % (label, path, exc))
    except ValueError as exc:
        raise UsageError("malformed JSON in %s (%s): %s" % (label, path, exc))
    if not isinstance(data, dict):
        raise UsageError("top-level JSON of %s must be an object" % (label,))
    return data


def _nonempty_str(value):
    return isinstance(value, str) and value != ""


def _resolve_under(root, rel, doc_path, field, diags):
    """Resolve ``rel`` under ``root``; reject escapes, ``..`` escapes and out-of-root symlinks."""
    if not _nonempty_str(rel):
        diags.add(doc_path, field, "path must be a non-empty string")
        return None
    if os.path.isabs(rel):
        diags.add(doc_path, field, "absolute path not allowed: %s" % (rel,))
        return None
    joined = os.path.join(root, rel)
    real_root = os.path.realpath(root)
    real = os.path.realpath(joined)
    if real != real_root and not real.startswith(real_root + os.sep):
        diags.add(doc_path, field, "path escapes allowed root (%s): %s" % (root, rel))
        return None
    return joined


def _check_file_exists(path, doc_path, field, diags):
    if not os.path.exists(path):
        diags.add(doc_path, field, "missing file: %s" % (path,))


def _check_tree_value(repo, doc_path, field, value, diags):
    """Validate a tree-shaped field: present, 40-hex, not degenerate, resolvable."""
    if value is None:
        diags.add(doc_path, field, "tree key absent")
        return False
    if not isinstance(value, str):
        diags.add(doc_path, field, "tree must be a string, got %s" % (type(value).__name__,))
        return False
    if value == "":
        diags.add(doc_path, field, "degenerate tree: empty string")
        return False
    if value == ZERO40:
        diags.add(doc_path, field, "degenerate tree: zero hash (40 zeros)")
        return False
    if not HEX40_RE.match(value):
        diags.add(doc_path, field, "malformed tree: not 40-hex (%r)" % (value,))
        return False
    actual = _git_type(repo, value)
    if actual != "tree":
        diags.add(
            doc_path, field, "tree not resolvable by 'git cat-file -t' (%r -> %r)" % (value, actual)
        )
        return False
    return True


HEAD_TREE_RE = re.compile(r"HEAD\^?\{?tree\}?")
HEAD_TREE_CLAIM_KEYS = ("head_tree", "head_commit_tree", "equals_head_tree")


def _check_no_head_tree_claim(doc, doc_path, diags):
    """Reject any claim that the frozen tree equals ``HEAD^{tree}`` (except the negation)."""
    for key in HEAD_TREE_CLAIM_KEYS:
        if key in doc:
            diags.add(doc_path, key, "claim of HEAD^{tree} equality is forbidden")
    for key, value in doc.items():
        if key == "tree_method":
            continue
        if isinstance(value, str) and HEAD_TREE_RE.search(value):
            diags.add(doc_path, key, "claim of HEAD^{tree} equality is forbidden")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and HEAD_TREE_RE.search(item):
                    diags.add(doc_path, key, "claim of HEAD^{tree} equality is forbidden")
                    break


def _discover_scope_json(scope):
    """Every ``*.json`` under ``generations/**/results/`` plus ``results``/``receipts`` dirs."""
    found = []
    generations = os.path.join(scope, "generations")
    if os.path.isdir(generations):
        for dirpath, _dirnames, filenames in os.walk(generations):
            if os.path.basename(dirpath) != "results":
                continue
            for name in filenames:
                if name.endswith(".json"):
                    found.append(os.path.join(dirpath, name))
    for extra in ("results", "receipts"):
        base = os.path.join(scope, extra)
        if os.path.isdir(base):
            for dirpath, _dirnames, filenames in os.walk(base):
                for name in filenames:
                    if name.endswith(".json"):
                        found.append(os.path.join(dirpath, name))
    return found


# ------------------------------------------------------------------------------- lint


def _lint_receipt(repo, scope, receipt_path, recomputed, diags, seen_row_ids):
    try:
        receipt = _parse_json_file(receipt_path)
    except Violation as violation:
        diags.items.extend(violation.diagnostics)
        return
    row_id = receipt.get("id")
    if not _nonempty_str(row_id):
        diags.add(receipt_path, "id", "receipt id must be a non-empty string")
    elif row_id in seen_row_ids:
        diags.add(
            receipt_path,
            "id",
            "duplicate row id %r (already defined in %s)" % (row_id, seen_row_ids[row_id]),
        )
    else:
        seen_row_ids[row_id] = receipt_path

    _check_tree_value(repo, receipt_path, "tree", receipt.get("tree"), diags)
    _check_tree_value(repo, receipt_path, "tree_binding", receipt.get("tree_binding"), diags)
    if recomputed is not None and receipt.get("tree") != recomputed:
        diags.add(receipt_path, "tree", "receipt tree != recomputed frozen tree")
    if receipt.get("tree_binding") != receipt.get("tree"):
        diags.add(receipt_path, "tree_binding", "tree_binding != tree")

    if receipt.get("status") == "met":
        evidence = receipt.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            diags.add(receipt_path, "evidence", "met receipt must carry a non-empty evidence list")
        else:
            _lint_evidence(repo, receipt_path, evidence, diags)
    _check_no_head_tree_claim(receipt, receipt_path, diags)


def _lint_evidence(repo, doc_path, evidence, diags):
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            diags.add(doc_path, "evidence[%d]" % index, "evidence entry must be an object")
            continue
        for key in ("kind", "path"):
            if not _nonempty_str(item.get(key)):
                diags.add(
                    doc_path, "evidence[%d].%s" % (index, key), "must be a non-empty string"
                )
        resolved = _resolve_under(
            repo, item.get("path"), doc_path, "evidence[%d].path" % index, diags
        )
        if resolved is not None:
            _check_file_exists(resolved, doc_path, "evidence[%d].path" % index, diags)


def _lint_manifest_doc(repo, manifest_path, manifest, scope, diags):
    manifest_tree = manifest.get("tree")
    _check_tree_value(repo, manifest_path, "tree", manifest_tree, diags)
    if "tree_binding" in manifest and manifest.get("tree_binding") != manifest_tree:
        diags.add(manifest_path, "tree_binding", "manifest tree_binding != tree")

    base_ref = manifest.get("base_ref")
    footprint = manifest.get("footprint")
    exclusions = manifest.get("exclusions")
    if not _nonempty_str(base_ref):
        diags.add(manifest_path, "base_ref", "base_ref must be a non-empty string")
    if not isinstance(footprint, list) or not footprint:
        diags.add(manifest_path, "footprint", "footprint must be a non-empty list")
    if not isinstance(exclusions, list):
        diags.add(manifest_path, "exclusions", "exclusions must be a list")
        exclusions = []

    recomputed = None
    if _nonempty_str(base_ref) and isinstance(footprint, list) and footprint:
        try:
            recomputed = _recompute_from_manifest(repo, manifest)
        except UsageError as exc:
            diags.add(manifest_path, "base_ref", "cannot recompute frozen tree: %s" % (exc,))

    if recomputed is not None:
        _guard_tree_equality(manifest_tree, recomputed, diags, manifest_path)

    _check_no_head_tree_claim(manifest, manifest_path, diags)

    required = manifest.get("required_rows")
    required_set = None
    if not isinstance(required, list) or not required:
        diags.add(manifest_path, "required_rows", "required_rows must be a nonempty list")
        required = []
    elif not all(_nonempty_str(item) for item in required):
        diags.add(
            manifest_path, "required_rows", "required_rows entries must be non-empty strings"
        )
        required = []
    elif len(set(required)) != len(required):
        diags.add(manifest_path, "required_rows", "required_rows contains duplicate ids")
        required = []
    else:
        required_set = set(required)

    rows = manifest.get("rows")
    seen_row_ids = {}
    if not isinstance(rows, list):
        diags.add(manifest_path, "rows", "rows must be a list")
        rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            diags.add(manifest_path, "rows[%d]" % index, "row must be an object")
            continue
        row_id = row.get("id")
        if _nonempty_str(row_id):
            if row_id in seen_row_ids:
                diags.add(manifest_path, "rows[%d].id" % index, "duplicate row id %r" % (row_id,))
            else:
                seen_row_ids[row_id] = manifest_path
        if row.get("status") == "met":
            evidence = row.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                diags.add(
                    manifest_path,
                    "rows[%d].evidence" % index,
                    "met row must carry a non-empty evidence list",
                )
            else:
                _lint_evidence(repo, manifest_path, evidence, diags)
        result = row.get("result")
        if result is not None:
            resolved = _resolve_under(
                scope, result, manifest_path, "rows[%d].result" % index, diags
            )
            if resolved is not None:
                _check_file_exists(resolved, manifest_path, "rows[%d].result" % index, diags)

    if required_set is not None:
        for row_id in required:
            if row_id not in seen_row_ids:
                diags.add(
                    manifest_path,
                    "required_rows",
                    "required row missing from manifest: %r" % (row_id,),
                )
        for row_id in seen_row_ids:
            if row_id not in required_set:
                diags.add(
                    manifest_path,
                    "rows",
                    "manifest row not declared in required_rows: %r" % (row_id,),
                )

    discovered = _discover_scope_json(scope)
    seen_receipt_ids = {}
    for receipt_path in discovered:
        _lint_receipt(repo, scope, receipt_path, recomputed, diags, seen_receipt_ids)


def _recompute_from_manifest(repo, manifest):
    base_ref = manifest.get("base_ref")
    footprint = manifest.get("footprint") or []
    exclusions = manifest.get("exclusions") or []
    recomputed = compute_frozen_tree(repo, base_ref, footprint, exclusions)
    return recomputed


def _guard_tree_equality(manifest_tree, recomputed, diags, manifest_path):
    if manifest_tree != recomputed:
        diags.add(
            manifest_path,
            "tree",
            "manifest tree %r != recomputed frozen tree %r" % (manifest_tree, recomputed),
        )


def lint(repo, manifest_path, scope_root=None):
    """Lint one selected revision directory; raise ``Violation`` on any inconsistency."""
    repo = os.path.abspath(repo)
    manifest_path = os.path.abspath(manifest_path)
    scope = os.path.abspath(scope_root) if scope_root else os.path.dirname(manifest_path)
    if not os.path.isfile(manifest_path):
        raise UsageError("manifest not found: %s" % (manifest_path,))
    diags = Diags()
    try:
        manifest = _parse_json_file(manifest_path)
    except Violation as violation:
        raise Violation(violation.diagnostics)
    _lint_manifest_doc(repo, manifest_path, manifest, scope, diags)
    if diags:
        raise Violation(diags.items)
    return []


# --------------------------------------------------------------------------- generate


def _build_receipt(row, tree):
    status = row.get("status")
    receipt = {
        "id": row.get("id"),
        "status": status,
        "requirements": list(row.get("requirements") or []),
        "predicate": row.get("predicate", ""),
        "tree": tree,
        "tree_binding": tree,
        "evidence": list(row.get("evidence") or []) if status == "met" else [],
    }
    if status == "open":
        receipt["reason"] = row.get("reason", "")
    return receipt


def _build_manifest_row(row, result_path):
    manifest_row = {
        "id": row.get("id"),
        "status": row.get("status"),
        "requirements": list(row.get("requirements") or []),
        "predicate": row.get("predicate", ""),
        "result": result_path,
    }
    if row.get("status") == "met":
        manifest_row["evidence"] = list(row.get("evidence") or [])
    if row.get("status") == "open":
        manifest_row["reason"] = row.get("reason", "")
    return manifest_row


def _verify_candidate_before_publish(candidate, manifest_path):
    """Pre-publication guard: validate the complete candidate, honour the test injection."""
    diags = Diags()
    for row_id in candidate["required_rows"]:
        if row_id not in candidate["receipts"]:
            diags.add(manifest_path, "rows", "missing receipt for required row %r" % (row_id,))
    if os.environ.get(FAIL_BEFORE_PUBLISH_ENV):
        diags.add(manifest_path, "candidate", "injected pre-publication failure (test hook)")
    return diags


def generate(repo, contract_path, output_dir):
    """Generate receipts + manifest atomically; raise ``Violation``/``UsageError``."""
    repo = os.path.abspath(repo)
    output_dir = os.path.abspath(output_dir)
    contract = _load_json_object(contract_path, "contract")

    for key in ("task", "issue", "status_file", "path", "base_ref"):
        if not _nonempty_str(contract.get(key)):
            raise UsageError("contract.%s must be a non-empty string" % key)
    footprint = contract.get("footprint")
    exclusions = contract.get("exclusions") or list(DEFAULT_EXCLUSIONS)
    validate_footprint(footprint, exclusions)
    rows = contract.get("rows")
    if not isinstance(rows, list) or not rows:
        raise UsageError("contract.rows must be a non-empty list")
    required_rows = contract.get("required_rows")
    if not isinstance(required_rows, list) or not required_rows:
        raise UsageError("contract.required_rows must be a non-empty list")
    if len(set(required_rows)) != len(required_rows):
        raise UsageError("contract.required_rows contains duplicate ids")
    row_ids = [row.get("id") for row in rows]
    if len(set(row_ids)) != len(row_ids):
        raise UsageError("contract.rows contains duplicate ids")
    for row_id in required_rows:
        if row_id not in row_ids:
            raise UsageError("required row %r has no row definition" % (row_id,))

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    lock_path = os.path.join(output_dir, ".pdca-evidence.lock")
    try:
        lock_handle = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except OSError as exc:
        raise UsageError(
            "another writer holds the evidence lock %s: %s" % (lock_path, exc)
        )
    created_generations = []
    try:
        os.write(lock_handle, b"pdca-evidence lock\n")
        os.close(lock_handle)

        # Preflight lint of existing evidence BEFORE regeneration; never silently repaired.
        manifest_path = os.path.join(output_dir, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                lint(repo, manifest_path, scope_root=output_dir)
            except Violation as violation:
                raise Violation(
                    ["preflight: existing evidence is stale"] + violation.diagnostics
                )

        tree = compute_frozen_tree(repo, contract["base_ref"], footprint, exclusions)

        receipts = {}
        for row in rows:
            receipts[row["id"]] = _build_receipt(row, tree)

        diags = Diags()
        for row in rows:
            if row.get("status") == "met":
                _lint_evidence(
                    repo,
                    os.path.join(output_dir, "inputs", "contract.json"),
                    row.get("evidence") or [],
                    diags,
                )
        if diags:
            raise Violation(diags.items)

        digest = hashlib.sha256(
            canonical_bytes({"rows": {rid: receipts[rid] for rid in sorted(receipts)}})
        ).hexdigest()
        generation_dir = os.path.join(output_dir, "generations", digest)
        if not os.path.isdir(generation_dir):
            created_generations.append(generation_dir)
        results_dir = os.path.join(generation_dir, "results")
        for row_id in sorted(receipts):
            _write_atomic(
                os.path.join(results_dir, row_id + ".json"),
                canonical_bytes(receipts[row_id]),
            )

        manifest_rows = []
        for row_id in required_rows:
            row = next(row for row in rows if row.get("id") == row_id)
            result_rel = os.path.join(
                "generations", digest, "results", row_id + ".json"
            ).replace(os.sep, "/")
            manifest_rows.append(_build_manifest_row(row, result_rel))

        manifest = {
            "task": contract["task"],
            "issue": contract["issue"],
            "status_file": contract["status_file"],
            "path": contract["path"],
            "base_ref": contract["base_ref"],
            "collection_baseline_ref": contract.get("collection_baseline_ref"),
            "tree": tree,
            "tree_binding": tree,
            "tree_method": TREE_METHOD,
            "footprint": list(footprint),
            "exclusions": list(exclusions),
            "git_head": _git(["rev-parse", "HEAD"], repo),
            "contract_rv": int(contract.get("contract_rv", 1)),
            "supersedes": contract.get("supersedes", {"rv": 1, "artifacts": "none"}),
            "required_rows": list(required_rows),
            "rows": manifest_rows,
        }

        candidate = {
            "required_rows": list(required_rows),
            "receipts": receipts,
            "tree": tree,
        }
        guard = _verify_candidate_before_publish(candidate, manifest_path)
        if guard:
            raise Violation(guard.items)

        _write_atomic(manifest_path, canonical_bytes(manifest))
    except BaseException:
        for generation_dir in created_generations:
            if os.path.isdir(generation_dir):
                shutil.rmtree(generation_dir, ignore_errors=True)
        raise
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass
    return manifest_path


# ------------------------------------------------------------------------------- cli


class _ArgumentParser(argparse.ArgumentParser):
    """argparse with a usage-error exit code of 1 (not the default 2)."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("ERROR: %s\n" % (message,))
        raise SystemExit(UsageError.exit_code)


def build_parser():
    parser = _ArgumentParser(
        prog="pdca_evidence.py",
        description="Atomic PDCA evidence generator + strict scoped lint.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    gen = sub.add_parser("generate", help="generate receipts + manifest atomically")
    gen.add_argument("--repo", required=True, help="repository root")
    gen.add_argument("--contract", required=True, help="contract JSON path")
    gen.add_argument("--output", required=True, help="evidence output directory (rv<k>)")

    lin = sub.add_parser("lint", help="lint one selected revision directory")
    lin.add_argument("--repo", required=True, help="repository root")
    lin.add_argument("--manifest", required=True, help="manifest JSON path")
    lin.add_argument(
        "--scope-root",
        default=None,
        help="revision directory to scan (default: the manifest's own directory)",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            generate(args.repo, args.contract, args.output)
        elif args.command == "lint":
            lint(args.repo, args.manifest, args.scope_root)
    except Violation as violation:
        for diagnostic in violation.diagnostics:
            sys.stderr.write("VIOLATION: %s\n" % (diagnostic,))
        return Violation.exit_code
    except EvidenceError as error:
        sys.stderr.write("ERROR: %s\n" % (error,))
        return error.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
