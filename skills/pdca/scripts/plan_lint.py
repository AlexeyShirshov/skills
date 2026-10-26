#!/usr/bin/env python3
"""Static contract lint for a PDCA plan's frozen commands.

Reads the machine projection of a plan's command block (``commands.json``),
never the Markdown status file, and answers one question: *can this plan's
decisive commands produce a valid result in this environment?*  It does not
run the planned work and it does not judge whether the rows prove the goal.

Four subcommands:

``schema`` print the projection schema below and exit — the shape an executor
           needs, without reading this file's source.

``fork-attempt`` copy a frozen projection into the next attempt child, rewriting
           only the ``attempts/<old>`` path segment; text-level, so the file's
           formatting and every other value survive byte-for-byte.

``check``  static only (the gate-1 form): schema, argv shape, phase/scope
           legality, build scope against the declared host budget, selector
           resolution against the project sources, expected outcome, evidence
           binding, the one-decisive-row-per-criterion mapping, unit coverage.
           Seconds, no containers, no network.

``probe``  additionally runs each command's ``harness_probe`` argv (a cheap,
           non-mutating invocation proving the harness accepts it), restricted
           to an allow-list of binaries and a timeout.  Never runs the planned
           command itself.

Exit codes: ``0`` ok, ``2`` violation, ``1`` usage/operational error — the same
convention as ``pdca_evidence.py``.

Input schema (all paths repo-relative unless stated)::

    {
      "task": "T256",
      "plan_r": 1,
      "checkout": "/abs/path/to/binding/checkout",   # optional, must equal --repo
      "evidence_root": ".pdca/T256/rv1",             # optional
      "host_budget": {"max_lanes": 2, "max_solution_builds": 0},
      "integration_boundary_runs": 1,
      "units": ["D1", "D2"],                          # optional
      "criteria": ["C1", "C2"],                       # optional; the plan's required criterion ids
      "commands": [
        {
          "id": "RED",
          "phase": "boundary",                       # inner | boundary | any
          "kind": "integration",                     # unit|integration|build|mutation|docs|other
          "argv": ["dotnet", "run", "--project", "tests/Proj", "--",
                   "-class", "Proj.Tests.SampleTests"],
          "cwd": ".",                                # optional, default repo root
          "env": {"DOCKER_HOST": "..."},             # optional; a cache/home/temp area stays out
                                                     # of evidence_root (GOCACHE, HOME, TMPDIR, ...)
          "expected": "expected-negative",           # green | expected-negative | informational
          "expected_identity": "assertion in Does_Thing",
          "min_selected": 1,
          "log": ".pdca/T256/rv1/attempts/c1-r1-n1/red.log",
          "timeout_s": 600,
          "covers": ["D1"],
          "decisive": ["C2"],                        # criterion ids this row decides (one row each)
          "identity": ["tests/Proj/Proj.csproj"],    # required on a decisive row: the inputs it
                                                     # consumes; DO writes <stem>.identity with their
                                                     # SHA-256 before the run
          "harness_probe": ["dotnet", "--version"],  # mutation only (or "fallback")
          "fallback": "controlled-mutants"
        }
      ]
    }

``decisive`` names the criteria a row decides: exactly one row decides a
criterion, the rest stay pointers.  A row may decide several criteria; an
``informational`` row and a row without a capture stem decide none, and an
empty ``decisive`` array is the same as omitting the key.  ``identity`` binds a
decisive row's capture to the sources it consumed, so a frozen snapshot hash and
a capture artefact resolve to the same bytes; a declared input that does not exist
yet is a warning, because DO creates it and the capture step is what must find it.

Run from the project root::

    python3 .pdca/scripts/plan_lint.py check --repo . --commands <commands.json>
    python3 .pdca/scripts/plan_lint.py probe --repo . --commands <commands.json> [--only RED]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = 1

PHASES = ("inner", "boundary", "any")
KINDS = ("unit", "integration", "build", "mutation", "docs", "other")
EXPECTED = ("green", "expected-negative", "informational")

SHELLS = {"sh", "bash", "zsh", "dash", "cmd", "cmd.exe", "powershell", "pwsh"}
PROBE_BINARIES = {"dotnet", "dotnet.exe", "git", "python3", "python", "go", "gofmt"}
SHELL_TOKENS = {"|", "||", "&&", ";", ">", ">>", "<", "2>&1", "2>", "&>", "1>"}

SELECTOR_FLAGS = ("-class", "--class", "-method", "--method", "--filter", "-filter")
PATH_FLAGS = ("--repo", "--output", "--manifest", "--scope-root", "--results", "--logs")

# A cache, home or temp area is a working by-product, never evidence.  Pointed inside the evidence
# root it buries the frozen artefacts under thousands of files (one Go build cache is ~1k files /
# tens of MB), and every later role that lists the root has to fight it.
CACHE_ENV_KEYS = (
    "HOME", "TMPDIR", "XDG_CACHE_HOME",
    "GOCACHE", "GOPATH", "GOMODCACHE", "GOTMPDIR",
    "DOTNET_CLI_HOME", "MSBUILDUSERHOMEDIR", "NUGET_PACKAGES",
    "PIP_CACHE_DIR", "npm_config_cache", "YARN_CACHE_FOLDER",
    "CARGO_HOME", "RUSTUP_HOME", "GRADLE_USER_HOME", "MAVEN_CONFIG",
)

# The `schema` subcommand prints the projection schema out of the module docstring, so the shape
# an executor needs has one home and cannot drift from the lint that enforces it.
SCHEMA_START = "Input schema"
SCHEMA_END = "Run from the project root"

# The base contract fixes the evidence root: `.pdca/<task>/rv<k>` (kebab task slug,
# criteria/contract revision). A plan that pins any other directory has drifted.
EVIDENCE_ROOT_RE = re.compile(r"^\.pdca/[A-Za-z0-9][\w.-]*/rv\d+$")

PLACEHOLDER_VAR = re.compile(r"^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$")
PLACEHOLDER_ANGLE = re.compile(r"^<[^<>]+>$")

TYPE_DECL = re.compile(r"\b(?:class|record(?:\s+struct)?|struct|interface|enum)\s+([A-Za-z_]\w*)")
METHOD_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
NAMESPACE_DECL = re.compile(r"\bnamespace\s+([\w.]+)")


class UsageError(Exception):
    """Operational error (bad CLI, unreadable input, malformed JSON)."""


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _inside(root: str, child: str) -> bool:
    root = os.path.realpath(root)
    child = os.path.abspath(child)
    try:
        return os.path.commonpath([root, child]) == root
    except ValueError:  # different drives
        return False


def _resolve(base: str, raw: str) -> str:
    return os.path.normpath(raw if os.path.isabs(raw) else os.path.join(base, raw))


class Violations:
    def __init__(self) -> None:
        self.items: list[dict] = []
        self.warnings: list[str] = []

    def add(self, ident: str, field: str, message: str) -> None:
        self.items.append({"id": ident, "field": field, "message": message})

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def sorted(self) -> list[dict]:
        return sorted(self.items, key=lambda v: (v["id"], v["field"], v["message"]))


def load(path: str) -> dict:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise UsageError("cannot read %s: %s" % (path, exc)) from exc
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UsageError("%s is not valid JSON: %s" % (path, exc)) from exc
    if not isinstance(doc, dict):
        raise UsageError("%s must contain a JSON object" % path)
    return doc


# ── argv ────────────────────────────────────────────────────────────────────


def check_argv(ident: str, argv, v: Violations, *, field: str = "argv") -> list[str]:
    """Validate the argv shape and return the tokens (possibly empty on error)."""
    if not isinstance(argv, list) or not argv:
        v.add(ident, field, "must be a non-empty JSON array of strings (argv, not a shell string)")
        return []
    if not all(isinstance(t, str) for t in argv):
        v.add(ident, field, "every token must be a string")
        return []
    if len(argv) == 1 and re.search(r"\s", argv[0]):
        v.add(ident, field, "single token contains whitespace — pass an argv array, not a shell string")
    if Path(argv[0]).name.lower() in SHELLS:
        v.add(ident, field, "shell wrapper %r is not allowed — pass the argv array directly" % argv[0])
    for token in argv:
        if PLACEHOLDER_VAR.match(token) or PLACEHOLDER_ANGLE.match(token):
            v.add(ident, field, "unexpanded placeholder %r" % token)
        if token in SHELL_TOKENS:
            v.add(ident, field, "shell operator %r is not allowed in argv (capture via `log`)" % token)
        if re.search(r"\s", token) and re.search(r"(;|&&|\|\||[<>])", token):
            v.add(ident, field, "compound command in a single token %r" % token[:60])
    return argv


def _flag_values(tokens: list[str], flags: tuple) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for i, token in enumerate(tokens):
        if token in flags and i + 1 < len(tokens):
            found.append((token, tokens[i + 1]))
        elif "=" in token:
            head, _, tail = token.partition("=")
            if head in flags:
                found.append((head, tail))
    return found


# ── selectors ───────────────────────────────────────────────────────────────


def scan_project(project_dir: Path) -> tuple[set, set, set]:
    types: set[str] = set()
    methods: set[str] = set()
    namespaces: set[str] = set()
    if not project_dir.is_dir():
        return types, methods, namespaces
    for path in project_dir.rglob("*.cs"):
        parts = set(path.parts)
        if "obj" in parts or "bin" in parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        types.update(TYPE_DECL.findall(text))
        methods.update(METHOD_CALL.findall(text))
        namespaces.update(NAMESPACE_DECL.findall(text))
    return types, methods, namespaces


def _project_path(tokens: list[str], cwd: str) -> Path | None:
    for i, token in enumerate(tokens):
        if token in ("--project", "-p") and i + 1 < len(tokens):
            return Path(_resolve(cwd, tokens[i + 1]))
        if token.endswith(".csproj"):
            return Path(_resolve(cwd, token))
    # `dotnet test <dir>` / `dotnet run --project <dir>`: a positional project
    # directory is a valid target and must resolve the selector too.
    for token in tokens[2:]:
        if token.startswith("-"):
            continue
        candidate = Path(_resolve(cwd, token))
        if candidate.is_dir() and list(candidate.glob("*.csproj")):
            return candidate
        if candidate.suffix == ".csproj":
            return candidate
    return None


def _project_dir(tokens: list[str], cwd: str) -> Path | None:
    path = _project_path(tokens, cwd)
    if path is None:
        return None
    return path if path.is_dir() else path.parent


def check_selectors(ident: str, tokens: list[str], cwd: str, v: Violations) -> None:
    selectors = [(flag, value) for flag, value in _flag_values(tokens, SELECTOR_FLAGS)]
    if not selectors:
        return
    if not tokens or Path(tokens[0]).name.lower() not in ("dotnet", "dotnet.exe"):
        v.add(ident, "selector", "selector flag on a non-dotnet command cannot be resolved")
        return
    project = _project_dir(tokens, cwd)
    if project is None:
        v.add(ident, "selector", "selector present but no project (--project or *.csproj) to resolve it against")
        return
    types, methods, namespaces = scan_project(project)
    if not types and not methods:
        v.add(ident, "selector", "project sources %s yielded no types/methods" % project)
        return
    # Reflection reports the declared casing, but runner selectors are matched
    # case-insensitively in practice; compare folded to avoid a false positive.
    types_folded = {name.lower() for name in types}
    methods_folded = {name.lower() for name in methods}
    namespaces_folded = {name.lower() for name in namespaces}

    for flag, value in selectors:
        if flag in ("-class", "--class"):
            if "." not in value:
                v.add(ident, "selector",
                      "class %r is not fully-qualified — a short name can select 0 and exit 0" % value)
                continue
            prefix, short = value.rsplit(".", 1)
            if short.lower() not in types_folded:
                v.add(ident, "selector", "class %r not found in %s" % (short, project))
            elif prefix.lower() not in namespaces_folded:
                v.add(ident, "selector", "namespace %r not found in %s" % (prefix, project))
        elif flag in ("-method", "--method"):
            name = value.split("(", 1)[0]
            if "." not in name:
                v.add(ident, "selector",
                      "method %r is not fully-qualified — a short name can select 0 and exit 0" % value)
                continue
            segments = name.split(".")
            method = segments[-1]
            if method.lower() not in methods_folded:
                v.add(ident, "selector", "method %r not found in %s" % (method, project))
            if len(segments) >= 2:
                owner = segments[-2]
                if owner.lower() not in types_folded:
                    v.add(ident, "selector", "method owner %r not found in %s" % (owner, project))
        elif flag in ("--filter", "-filter"):
            match = re.search(r"FullyQualifiedName=([^|&()]+)", value)
            if match:
                exact = match.group(1).strip()
                if "." not in exact and "*" not in exact and "?" not in exact:
                    v.add(ident, "selector",
                          "FullyQualifiedName exact %r has no namespace — it can select 0" % exact)


# ── build scope ─────────────────────────────────────────────────────────────


def is_solution_build(tokens: list[str], cwd: str) -> bool:
    if len(tokens) < 2:
        return False
    if Path(tokens[0]).name.lower() not in ("dotnet", "dotnet.exe") or tokens[1] != "build":
        return False
    rest = tokens[2:]
    if any(t.lower().endswith((".sln", ".slnx")) for t in rest):
        return True
    positionals = [t for t in rest if not t.startswith("-")]
    if any(t.lower().endswith(".csproj") for t in positionals):
        return False
    for token in positionals:
        candidate = Path(_resolve(cwd, token))
        if candidate.is_dir() and list(candidate.glob("*.csproj")):
            return False
    # No explicit project: the CLI builds the solution/project in cwd.  Only a
    # cwd that itself holds exactly one project is a project build.
    if len(list(Path(cwd).glob("*.csproj"))) == 1 and not list(Path(cwd).glob("*.sln*")):
        return False
    return True


# ── main lint ───────────────────────────────────────────────────────────────


def lint(doc: dict, repo: str) -> tuple[Violations, int]:
    v = Violations()
    repo = os.path.realpath(repo)

    task = doc.get("task")
    if not isinstance(task, str) or not task.strip():
        v.add("-", "task", "must be a non-empty string")
    if not _is_int(doc.get("plan_r")) or doc.get("plan_r") < 1:
        v.add("-", "plan_r", "must be an integer >= 1")

    checkout = doc.get("checkout")
    if checkout is not None:
        if not isinstance(checkout, str) or not checkout.strip():
            v.add("-", "checkout", "must be a non-empty string when present")
        elif os.path.realpath(checkout) != repo:
            v.add("-", "checkout",
                  "checkout %r is not the linted root %r — lint against the binding checkout" % (checkout, repo))

    evidence_root = doc.get("evidence_root")
    if evidence_root is not None:
        if not isinstance(evidence_root, str) or not evidence_root.strip():
            v.add("-", "evidence_root", "must be a non-empty string when present")
            evidence_root = None
        else:
            root_rel = evidence_root.replace(os.sep, "/").strip("/")
            if not EVIDENCE_ROOT_RE.match(root_rel):
                v.add("-", "evidence_root",
                      "must be the contract root `.pdca/<task>/rv<k>`, got %r" % evidence_root)
            evidence_root = _resolve(repo, evidence_root)
            if not _inside(repo, evidence_root):
                v.add("-", "evidence_root", "escapes the repository root")
                evidence_root = None

    budget = doc.get("host_budget") or {}
    max_lanes = budget.get("max_lanes") if isinstance(budget, dict) else None
    max_solution = budget.get("max_solution_builds") if isinstance(budget, dict) else None
    if max_lanes is not None and (not _is_int(max_lanes) or max_lanes < 1):
        v.add("-", "host_budget.max_lanes", "must be an integer >= 1")
        max_lanes = None
    if max_solution is not None and (not _is_int(max_solution) or max_solution < 0):
        v.add("-", "host_budget.max_solution_builds", "must be an integer >= 0")
        max_solution = None
    if budget and not isinstance(budget, dict):
        v.add("-", "host_budget", "must be an object")

    declared_runs = doc.get("integration_boundary_runs")
    if declared_runs is not None and (not _is_int(declared_runs) or declared_runs < 0):
        v.add("-", "integration_boundary_runs", "must be an integer >= 0")
        declared_runs = None

    units = doc.get("units")
    unit_ids: list[str] = []
    if units is not None:
        if not isinstance(units, list):
            v.add("-", "units", "must be an array")
            units = None
        else:
            for idx, unit in enumerate(units):
                uid = unit.get("id") if isinstance(unit, dict) else unit
                if not isinstance(uid, str) or not uid.strip():
                    v.add("-", "units[%d]" % idx, "must be a string or an object with a non-empty id")
                elif uid in unit_ids:
                    v.add("-", "units[%d]" % idx, "duplicate unit id %r" % uid)
                else:
                    unit_ids.append(uid)

    commands = doc.get("commands")
    if not isinstance(commands, list) or not commands:
        v.add("-", "commands", "must be a non-empty array")
        return v, 0

    criteria = doc.get("criteria")
    criteria_ids: list[str] = []
    if criteria is not None:
        if not isinstance(criteria, list) or not all(
            isinstance(c, str) and c.strip() for c in criteria
        ):
            v.add("-", "criteria", "must be an array of non-empty criterion ids")
        else:
            for cid in criteria:
                cid = cid.strip()
                if cid in criteria_ids:
                    v.add("-", "criteria", "duplicate criterion id %r" % cid)
                else:
                    criteria_ids.append(cid)

    seen_ids: set[str] = set()
    integration_runs = 0
    solution_builds = 0
    covered: set[str] = set()
    covers_declared: list[tuple[str, str]] = []
    covers_by_command: dict[str, set[str]] = {}
    decisive_by_criterion: dict[str, list[str]] = {}
    missing_identity: dict[str, list[str]] = {}

    for idx, cmd in enumerate(commands):
        if not isinstance(cmd, dict):
            v.add("#%d" % (idx + 1), "command", "must be an object")
            continue
        ident = cmd.get("id")
        if not isinstance(ident, str) or not ident.strip():
            ident = "#%d" % (idx + 1)
            v.add(ident, "id", "must be a non-empty string")
        elif ident in seen_ids:
            v.add(ident, "id", "duplicate command id")
        else:
            seen_ids.add(ident)
        if re.search(r"\s", ident):
            v.add(ident, "id", "must not contain whitespace")

        phase = cmd.get("phase")
        if phase not in PHASES:
            v.add(ident, "phase", "must be one of %s" % ", ".join(PHASES))
            phase = None
        kind = cmd.get("kind")
        if kind not in KINDS:
            v.add(ident, "kind", "must be one of %s" % ", ".join(KINDS))
            kind = None

        cwd_raw = cmd.get("cwd", ".")
        if not isinstance(cwd_raw, str) or not cwd_raw.strip():
            v.add(ident, "cwd", "must be a non-empty string")
            cwd = repo
        else:
            cwd = _resolve(repo, cwd_raw)
            if not _inside(repo, cwd):
                v.add(ident, "cwd", "escapes the repository root")
                cwd = repo
            elif not os.path.isdir(cwd):
                v.add(ident, "cwd", "%r is not a directory" % cwd_raw)
                cwd = repo

        argv = cmd.get("argv")
        tokens = check_argv(ident, argv, v)
        if tokens and kind == "integration" and phase == "inner":
            v.add(ident, "phase", "integration run planned as inner work — integration belongs to the boundary")
        if tokens and kind == "integration" and phase == "any":
            v.add(ident, "phase", "integration run must declare phase 'boundary', not 'any'")
        if tokens and kind == "integration" and phase == "boundary":
            integration_runs += 1

        if tokens:
            check_selectors(ident, tokens, cwd, v)
            if is_solution_build(tokens, cwd):
                solution_builds += 1
                if max_solution == 0:
                    v.add(ident, "build", "solution/root build forbidden (host_budget.max_solution_builds=0)")
                elif max_solution is not None and solution_builds > max_solution:
                    v.add(ident, "build",
                          "solution/root build exceeds host_budget.max_solution_builds=%d" % max_solution)
                if max_lanes is not None and max_lanes > 1:
                    v.add(ident, "build",
                          "solution/root build planned while max_lanes=%d (concurrent lanes cannot carry it)" % max_lanes)
                if max_solution is None and max_lanes is None:
                    v.warn("%s: solution/root build without a declared host_budget" % ident)

        expected = cmd.get("expected")
        if expected not in EXPECTED:
            v.add(ident, "expected", "must be one of %s" % ", ".join(EXPECTED))
            expected = None
        identity = cmd.get("expected_identity")
        if expected == "expected-negative":
            if not isinstance(identity, str) or not identity.strip():
                v.add(ident, "expected_identity",
                      "required for expected-negative (the declared failure identity)")
        elif identity is not None and not isinstance(identity, str):
            v.add(ident, "expected_identity", "must be a string when present")

        minimum = cmd.get("min_selected")
        if minimum is None:
            minimum = 1 if kind in ("unit", "integration") and expected in ("green", "expected-negative") else 0
        if not _is_int(minimum) or minimum < 0:
            v.add(ident, "min_selected", "must be an integer >= 0")
        elif kind in ("unit", "integration") and expected in ("green", "expected-negative") and minimum < 1:
            v.add(ident, "min_selected",
                  "a %s run needs min_selected >= 1 — zero selected is a failure" % expected)

        timeout = cmd.get("timeout_s")
        if timeout is not None and (not _is_int(timeout) or not 1 <= timeout <= 86400):
            v.add(ident, "timeout_s", "must be an integer between 1 and 86400")
        if kind == "integration" and timeout is None:
            v.add(ident, "timeout_s", "required for an integration run (a hang must fail fast)")

        log = cmd.get("log")
        if log is not None:
            if not isinstance(log, str) or not log.strip():
                v.add(ident, "log", "must be a non-empty string when present")
            elif os.path.isabs(log) or ".." in Path(log).parts:
                if not _inside(repo, _resolve(repo, log)):
                    v.add(ident, "log", "escapes the repository root")

        env = cmd.get("env")
        if env is not None:
            if not isinstance(env, dict):
                v.add(ident, "env", "must be an object of string values")
            else:
                for key, value in env.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        v.add(ident, "env", "every env key and value must be a string")
                        continue
                    if key not in CACHE_ENV_KEYS or not evidence_root:
                        continue
                    resolved = _resolve(repo, value)
                    if _inside(evidence_root, resolved):
                        v.add(ident, "env",
                              "%s %r points a cache/home/temp area inside the evidence root — "
                              "the root holds evidence only; name it outside the checkout" % (key, value))
                    elif _inside(repo, resolved):
                        v.warn("%s: %s lives inside the checkout and becomes untracked noise; name it "
                               "outside the checkout" % (ident, key))

        covers = cmd.get("covers")
        if covers is not None:
            if not isinstance(covers, list) or not all(isinstance(c, str) for c in covers):
                v.add(ident, "covers", "must be an array of unit ids")
            else:
                covered.update(covers)
                covers_declared.extend((ident, c) for c in covers)
                covers_by_command.setdefault(ident, set()).update(covers)

        identity_inputs = cmd.get("identity")
        identity_ok = False
        if identity_inputs is not None:
            if (not isinstance(identity_inputs, list) or not identity_inputs
                    or not all(isinstance(p, str) and p.strip() for p in identity_inputs)):
                v.add(ident, "identity", "must be a non-empty array of repo-relative input paths")
            else:
                identity_ok = True
                for raw in identity_inputs:
                    resolved = _resolve(repo, raw)
                    if not _inside(repo, resolved):
                        v.add(ident, "identity", "path %r escapes the linted checkout" % raw)
                        identity_ok = False
                    elif not os.path.exists(resolved):
                        missing_identity.setdefault(raw, []).append(ident)

        decisive = cmd.get("decisive")
        if decisive is not None:
            if not isinstance(decisive, list) or not all(
                isinstance(c, str) and c.strip() for c in decisive
            ):
                v.add(ident, "decisive", "must be an array of criterion ids")
            elif decisive:
                for cid in decisive:
                    decisive_by_criterion.setdefault(cid.strip(), []).append(ident)
                if expected == "informational":
                    v.add(ident, "decisive", "an `informational` row cannot decide a criterion")
                if not isinstance(log, str) or not log.strip():
                    v.add(ident, "decisive", "a decisive row needs a capture stem (`log`)")
                if not identity_ok:
                    v.add(ident, "decisive",
                          "a decisive row declares `identity` — the inputs the run consumes — so its "
                          "capture binds to the frozen snapshot instead of resting on the author's word")

        probe = cmd.get("harness_probe")
        fallback = cmd.get("fallback")
        if kind == "mutation":
            if probe is None and not (isinstance(fallback, str) and fallback.strip()):
                v.add(ident, "harness_probe",
                      "a mutation run needs a harness_probe or a declared fallback")
            if probe is not None:
                probe_tokens = check_argv(ident, probe, v, field="harness_probe")
                if probe_tokens and Path(probe_tokens[0]).name.lower() not in PROBE_BINARIES:
                    v.add(ident, "harness_probe",
                          "probe binary %r is not in the allow-list %s"
                          % (probe_tokens[0], sorted(PROBE_BINARIES)))
        elif probe is not None:
            v.add(ident, "harness_probe", "only a mutation run may declare a harness_probe")

        for flag, value in _flag_values(tokens, PATH_FLAGS):
            resolved = _resolve(cwd, value)
            if not _inside(repo, resolved):
                v.add(ident, flag, "path %r escapes the linted checkout %r" % (value, repo))
            elif flag == "--repo" and os.path.realpath(resolved) != repo:
                v.add(ident, flag,
                      "names %r while the binding checkout is %r" % (resolved, repo))
            if evidence_root and flag in ("--output", "--manifest", "--scope-root"):
                if not _inside(evidence_root, resolved):
                    v.add(ident, flag, "path %r is outside evidence_root %r" % (value, evidence_root))

    if declared_runs is not None and integration_runs != declared_runs:
        v.add("-", "integration_boundary_runs",
              "declared %d but %d integration boundary runs are planned" % (declared_runs, integration_runs))

    # One row decides a criterion.  A plan whose prose calls T2, T3 and T4 decisive for the same
    # criterion has drifted from the package rule; the projection is where that becomes checkable.
    for cid, idents in sorted(decisive_by_criterion.items()):
        if len(idents) > 1:
            v.add(cid, "decisive",
                  "decided by %d rows (%s) — exactly one row decides a criterion, the rest are pointers"
                  % (len(idents), ", ".join(sorted(idents))))
        if criteria_ids and cid not in criteria_ids:
            v.add(cid, "decisive", "names a criterion the projection does not declare in `criteria`")
    for cid in criteria_ids:
        if cid not in decisive_by_criterion:
            v.add(cid, "decisive", "no row declares it decisive")
    if decisive_by_criterion and not criteria_ids:
        v.warn("commands.json marks decisive rows but declares no `criteria`: the one-row-per-criterion "
               "rule cannot be checked against the plan's criteria")

    # One line per path, not per (command, path): B and T name the same sources, and a receipt with
    # the same sentence eleven times buries the six facts it carries.
    for raw in sorted(missing_identity):
        idents = ", ".join(sorted(set(missing_identity[raw])))
        v.warn("identity input %r does not exist yet (named by %s) — the capture step fails if it "
               "stays missing" % (raw, idents))

    if covers_declared and not unit_ids:
        v.warn("`covers` declared without `units`: covers names units; the plan's criteria belong in "
               "`criteria` and `decisive`")

    if unit_ids:
        for ident, unit in covers_declared:
            if unit not in unit_ids:
                v.add(ident, "covers", "unknown unit id %r" % unit)
        missing = [u for u in unit_ids if u not in covered]
        for unit in missing:
            v.add(unit, "covers", "unit has no command/evidence owner")
        # Parallel DO dispatches follow units, never files: a unit covered only by commands shared
        # with other units has no verification of its own, so it is not a separate dispatch.
        if len(unit_ids) > 1:
            for unit in unit_ids:
                own = any(units == {unit} for units in covers_by_command.values())
                if own:
                    continue
                v.warn(
                    "unit %r has no command of its own: parallel DO units need their own covering "
                    "command, otherwise they are one dispatch (pdca-coder §Parallel DO streams)" % unit
                )

    return v, len(commands)


# ── probe ───────────────────────────────────────────────────────────────────


def run_probes(doc: dict, repo: str, only: set[str], timeout_cap: int) -> tuple[Violations, int, list]:
    v = Violations()
    results: list[dict] = []
    commands = doc.get("commands") if isinstance(doc.get("commands"), list) else []
    executed = 0
    for cmd in commands:
        if not isinstance(cmd, dict):
            continue
        ident = cmd.get("id") if isinstance(cmd.get("id"), str) else "?"
        if only and ident not in only:
            continue
        probe = cmd.get("harness_probe")
        if not isinstance(probe, list) or not probe or not all(isinstance(t, str) for t in probe):
            continue
        tokens = probe
        binary = Path(tokens[0]).name.lower()
        if binary not in PROBE_BINARIES:
            # static lint already reported the allow-list violation; do not run it
            # and do not duplicate the diagnostic here.
            continue
        cwd = cmd.get("cwd", ".")
        cwd_path = _resolve(repo, cwd) if isinstance(cwd, str) and cwd.strip() else repo
        if not _inside(repo, cwd_path) or not os.path.isdir(cwd_path):
            v.add(ident, "cwd", "probe cwd is not an existing directory inside the checkout")
            continue
        env = os.environ.copy()
        overrides = cmd.get("env")
        if isinstance(overrides, dict):
            env.update({str(k): str(val) for k, val in overrides.items()})
        timeout = max(1, min(timeout_cap, cmd.get("timeout_s") if _is_int(cmd.get("timeout_s")) else timeout_cap))
        started = None
        try:
            completed = subprocess.run(
                tokens, cwd=cwd_path, env=env, shell=False,
                capture_output=True, text=True, timeout=timeout,
            )
            rc = completed.returncode
            tail = (completed.stderr or completed.stdout or "").strip().splitlines()[-1:] or [""]
        except subprocess.TimeoutExpired:
            rc = None
            tail = ["timed out after %ds" % timeout]
        except OSError as exc:
            rc = None
            tail = [str(exc)]
        executed += 1
        results.append({"id": ident, "argv": tokens, "exit": rc, "note": tail[0][:200]})
        if rc != 0:
            v.add(ident, "harness_probe", "probe failed (exit %s): %s" % (rc, tail[0][:160]))
    return v, executed, results


# ── CLI ─────────────────────────────────────────────────────────────────────


def schema_text() -> str:
    """The projection schema, extracted from the module docstring (one home, no drift)."""
    doc = (__doc__ or "").strip()
    start = doc.find(SCHEMA_START)
    end = doc.find(SCHEMA_END)
    if start == -1 or end <= start:
        return doc + "\n"
    return doc[start:end].rstrip() + "\n"


def emit(v: Violations, checked: int, as_json: bool, receipt: str, extra: dict) -> None:
    payload = {
        "tool": "plan_lint",
        "version": VERSION,
        "ok": not v.items,
        "checked": checked,
        "violations": v.sorted(),
        "warnings": v.warnings,
    }
    payload.update(extra)
    if receipt:
        try:
            parent = os.path.dirname(os.path.abspath(receipt))
            if parent:
                os.makedirs(parent, exist_ok=True)
            tmp = receipt + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, sort_keys=True)
                fh.write("\n")
            os.replace(tmp, receipt)
        except OSError as exc:
            raise UsageError("cannot write receipt %s: %s" % (receipt, exc)) from exc
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for item in payload["violations"]:
        print("%s: %s: %s" % (item["id"], item["field"], item["message"]))
    for warning in payload["warnings"]:
        print("warning: %s" % warning)
    if payload["ok"]:
        print("plan-lint: OK (%d commands checked)" % checked)


ATTEMPT_RE = re.compile(r"c\d+-r\d+-n\d+")


def fork_attempt(args) -> int:
    """Rewrite the ``attempts/<old>`` segment of a frozen projection into the new attempt child.

    Text-level substitution: the projection's formatting and every other value survive, and the
    result must still parse as JSON.  A projection that carries no reference to the old attempt, or
    one where a reference survives, is refused rather than silently half-rewritten.
    """
    for flag, value in (("--from", args.old), ("--to", args.new)):
        if not ATTEMPT_RE.fullmatch(value):
            print("plan-lint: %s %r is not an attempt name like c1-r1-n2" % (flag, value),
                  file=sys.stderr)
            return 2
    if args.old == args.new:
        print("plan-lint: --from and --to name the same attempt", file=sys.stderr)
        return 2
    source = Path(args.commands)
    if not source.is_file():
        print("plan-lint: %s does not exist" % source, file=sys.stderr)
        return 2
    destination = Path(args.output)
    if destination.exists() and not args.force:
        print("plan-lint: %s exists; pass --force to overwrite" % destination, file=sys.stderr)
        return 2
    token_old = "attempts/%s" % args.old
    raw = source.read_text(encoding="utf-8")
    count = raw.count(token_old)
    if not count:
        print("plan-lint: no %r reference in %s" % (token_old, source), file=sys.stderr)
        return 2
    forked = raw.replace(token_old, "attempts/%s" % args.new)
    if token_old in forked:
        print("plan-lint: a %r reference survived the rewrite" % token_old, file=sys.stderr)
        return 2
    try:
        json.loads(forked)
    except json.JSONDecodeError as exc:
        print("plan-lint: the forked projection is not valid JSON: %s" % exc, file=sys.stderr)
        return 2
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(forked, encoding="utf-8")
    print("forked: %s -> %s (%d path reference(s) rewritten)" % (source, destination, count))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plan_lint.py",
        description="Static contract lint for a PDCA plan's frozen commands.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("schema", help="print the commands.json schema and exit")

    fork = sub.add_parser(
        "fork-attempt",
        help="copy a frozen projection into the next attempt child (path segment only)",
    )
    fork.add_argument("--commands", required=True, help="the frozen projection to copy")
    fork.add_argument("--output", required=True, help="the new attempt child's projection")
    fork.add_argument("--from", dest="old", required=True, help="attempt segment to replace, e.g. c1-r1-n1")
    fork.add_argument("--to", dest="new", required=True, help="new attempt segment, e.g. c1-r1-n2")
    fork.add_argument("--force", action="store_true", help="overwrite an existing projection")

    for name, help_text in (
        ("check", "static validation (gate 1)"),
        ("probe", "static validation plus each harness probe"),
    ):
        proto = sub.add_parser(name, help=help_text)
        proto.add_argument("--repo", required=True, help="binding checkout (the linted root)")
        proto.add_argument("--commands", required=True, help="commands.json projection")
        proto.add_argument("--receipt", default="", help="write the JSON receipt here")
        proto.add_argument("--json", action="store_true", help="print the JSON result")
        if name == "probe":
            proto.add_argument("--only", default="", help="comma-separated command ids")
            proto.add_argument("--timeout", type=int, default=120, help="per-probe timeout (s)")

    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            sys.stdout.write(schema_text())
            return 0
        if args.command == "fork-attempt":
            return fork_attempt(args)
        repo = os.path.realpath(args.repo)
        if not os.path.isdir(repo):
            raise UsageError("--repo %r is not a directory" % args.repo)
        doc = load(args.commands)
        violations, checked = lint(doc, repo)
        extra: dict = {}
        if args.command == "probe":
            only = {item.strip() for item in args.only.split(",") if item.strip()}
            probe_v, executed, results = run_probes(doc, repo, only, max(1, args.timeout))
            violations.items.extend(probe_v.items)
            violations.warnings.extend(probe_v.warnings)
            extra = {"probes_executed": executed, "probes": results}
        emit(violations, checked, args.json, args.receipt, extra)
        return 0 if not violations.items else 2
    except UsageError as exc:
        print("plan-lint: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
