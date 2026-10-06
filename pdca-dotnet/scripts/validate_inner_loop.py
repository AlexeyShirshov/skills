#!/usr/bin/env python3
"""validate_inner_loop.py — fail-closed gate for the PDCA inner-loop test scope.

The PDCA contract requires DO to run only the *affected*, filtered test subset
during the inner loop and to reserve one comprehensive sweep for the DO->CHECK
boundary.  This helper validates the two JSON artifacts that make that
enforceable:

  * a **brief** scope, produced before dispatch to `coder`;
  * a **report** (brief + `executions`), produced before CHECK passes.

It never executes any supplied command: it only inspects the recorded argument
arrays.  A violation is printed as a `FAIL: ` line and exits 2.  A usage error,
unreadable file or malformed JSON prints `ERROR: ` and exits 1.  Exit 0 means
valid.

Schema (one JSON object)
-----------------------
Top level:  ``unit`` (nonempty str), ``scope`` (obj), optional ``amendments``
(list), and for ``report`` also ``executions`` (nonempty list).

``scope``: ``projects`` (nonempty list[nonempty str]); ``selectors`` (nonempty
list[nonempty str]); ``files`` (list[str], may be empty); ``rationale``
(nonempty str); ``rebuild`` ("affected" | "none"); ``boundary`` (nonempty str).
A docs-only scope (no ``.cs``/``.fs``/``.vb`` file) must not claim
``rebuild == "affected"`` (fictitious rebuild).

``amendments`` item: ``reason`` (nonempty str), ``added_selectors`` (nonempty
list[nonempty str]), ``validated_before_run`` (bool).

``executions`` item: ``command`` (nonempty list[str]), ``phase`` ("inner" |
"boundary"), ``source_revision`` / ``artifact_revision`` (nonempty str),
``exit_code`` (int, bool rejected), ``selected_count`` (int >= 1, bool
rejected) — the number of tests the run actually selected; a zero/missing
count is rejected for every execution, including boundary sweeps and
non-dotnet commands.

Examples
--------
  # validate the mandatory DO scope before dispatch
  validate_inner_loop.py brief /tmp/scope.json

  # validate scope + execution evidence before CHECK
  validate_inner_loop.py report /tmp/evidence.json

  # exit 0 = valid, 2 = violation(s), 1 = usage / unreadable / malformed JSON
  validate_inner_loop.py report /tmp/evidence.json; echo $?
"""
from __future__ import annotations

import argparse
import json
import sys

# Selectors that silently select a whole project/solution are never a valid
# affected subset (rule 3).
BROAD_SELECTORS = {"", "*", "*.*", "all", "All"}

# Extensions that make a changed file a compiled input (rule 12).
COMPILED_EXT = (".cs", ".fs", ".vb")

# Shell wrappers and flags whose presence means the real command cannot be
# verified statically (rule 7).
SHELL_TOKENS = {"sh", "bash", "zsh", "pwsh", "powershell"}
SHELL_FLAGS = {"-c", "-Command"}
COMPOUND_TOKENS = ("&&", "||", ";", "|", ">", "<", "$(")


class _UsageError(Exception):
    """Raised for usage errors, unreadable files and malformed JSON."""


class _ArgumentParser(argparse.ArgumentParser):
    """argparse variant that reports usage errors as exit 1 (not 2)."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, "ERROR: %s\n" % message)


def _is_str(value):
    return isinstance(value, str)


def _nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


def _is_str_list(value):
    return isinstance(value, list) and all(_is_str(item) for item in value)


def _is_nonempty_str_list(value):
    return (
        isinstance(value, list)
        and len(value) > 0
        and all(_nonempty_str(item) for item in value)
    )


def is_dotnet(command):
    return bool(command) and command[0] == "dotnet"


def verb(command):
    return command[1] if len(command) > 1 else None


def filter_present(command):
    return "--filter" in command or "-filter" in command


def filter_value(command):
    """Return the filter value, or None when absent / missing its value."""
    for flag in ("--filter", "-filter"):
        if flag in command:
            idx = command.index(flag)
            if idx + 1 < len(command) and not command[idx + 1].startswith("-"):
                return command[idx + 1]
            return None
    return None


def is_build(command):
    return is_dotnet(command) and verb(command) == "build"


def is_test(command):
    return is_dotnet(command) and verb(command) == "test"


def references_solution(command):
    return any(token.endswith((".sln", ".slnx")) for token in command)


def command_is_broad(command):
    """A BROAD command can select far more than the declared affected subset."""
    if not command:
        return False
    # dotnet build/test against a whole solution.
    if is_dotnet(command) and verb(command) in ("build", "test") and references_solution(command):
        return True
    # dotnet test without an effective filter.
    if is_test(command) and (not filter_present(command) or filter_value(command) in (None, "")):
        return True
    # Any command carrying a valueless --filter.
    if "--filter" in command:
        idx = command.index("--filter")
        if idx + 1 >= len(command) or command[idx + 1].startswith("-"):
            return True
    return False


def validate_scope(scope):
    violations = []
    if not _is_nonempty_str_list(scope.get("projects")):
        violations.append("scope.projects must be a nonempty list of nonempty strings")
    selectors = scope.get("selectors")
    if not _is_nonempty_str_list(selectors):
        violations.append("scope.selectors must be a nonempty list of nonempty strings")
    else:
        for selector in selectors:
            if selector in BROAD_SELECTORS:
                violations.append("broad selector is not allowed: %r" % selector)
    if not _is_str_list(scope.get("files")):
        violations.append("scope.files must be a list of strings")
    elif scope.get("rebuild") == "affected":
        files = scope.get("files")
        compiled = any(
            isinstance(name, str) and name.endswith(COMPILED_EXT) for name in files
        )
        if not compiled:
            violations.append(
                "fictitious rebuild for docs-only scope: "
                "no compiled file in scope.files but rebuild == 'affected'"
            )
    if not _nonempty_str(scope.get("rationale")):
        violations.append("scope.rationale must be a nonempty string")
    if scope.get("rebuild") not in ("affected", "none"):
        violations.append("scope.rebuild must be 'affected' or 'none'")
    if not _nonempty_str(scope.get("boundary")):
        violations.append("scope.boundary must be a nonempty string")
    return violations


def validate_amendments(data):
    violations = []
    if "amendments" not in data:
        return violations
    amendments = data.get("amendments")
    if not isinstance(amendments, list):
        return ["amendments must be a list"]
    for idx, amendment in enumerate(amendments):
        if not isinstance(amendment, dict):
            violations.append("amendment %d must be an object" % idx)
            continue
        if not _nonempty_str(amendment.get("reason")):
            violations.append("amendment %d reason must be a nonempty string" % idx)
        added = amendment.get("added_selectors")
        if not _is_nonempty_str_list(added):
            violations.append(
                "amendment %d added_selectors must be a nonempty list of nonempty strings" % idx
            )
        elif isinstance(added, list):
            for selector in added:
                if selector in BROAD_SELECTORS:
                    violations.append(
                        "amendment %d added selector is broad: %r" % (idx, selector)
                    )
        if not isinstance(amendment.get("validated_before_run"), bool):
            violations.append(
                "amendment %d validated_before_run must be a boolean" % idx
            )
    return violations


def validate_brief(data):
    violations = []
    if "unit" not in data:
        violations.append("missing required key: unit")
    elif not _nonempty_str(data.get("unit")):
        violations.append("unit must be a nonempty string")
    if "scope" not in data:
        violations.append("missing required key: scope")
    scope = data.get("scope")
    if "scope" in data and not isinstance(scope, dict):
        violations.append("scope must be an object")
    elif isinstance(scope, dict):
        violations.extend(validate_scope(scope))
    violations.extend(validate_amendments(data))
    return violations


def validate_execution(execution, idx):
    violations = []
    if not isinstance(execution, dict):
        return ["execution %d must be an object" % idx]
    if not _is_nonempty_str_list(execution.get("command")):
        violations.append("execution %d command must be a nonempty list of strings" % idx)
    if execution.get("phase") not in ("inner", "boundary"):
        violations.append("execution %d phase must be 'inner' or 'boundary'" % idx)
    if not _nonempty_str(execution.get("source_revision")):
        violations.append("execution %d source_revision must be a nonempty string" % idx)
    if not _nonempty_str(execution.get("artifact_revision")):
        violations.append("execution %d artifact_revision must be a nonempty string" % idx)
    exit_code = execution.get("exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        violations.append("execution %d exit_code must be an integer" % idx)
    selected_count = execution.get("selected_count")
    if (
        not isinstance(selected_count, int)
        or isinstance(selected_count, bool)
        or selected_count < 1
    ):
        violations.append(
            "execution %d selected_count must be an integer >= 1 "
            "(zero/missing selected tests)" % idx
        )
    return violations


def _identity(execution):
    """Grouping key: phase + filter-or-project identity (rule 14)."""
    command = execution["command"]
    phase = execution["phase"]
    if is_test(command):
        value = filter_value(command)
        if filter_present(command) and value not in (None, ""):
            return (phase, "filter", value)
        project = next((t for t in command[2:] if not t.startswith("-")), "")
        return (phase, "project", project)
    return (phase, "cmd", tuple(command))


def _rule_hygiene(executions, violations):
    for idx, execution in enumerate(executions):
        command = execution["command"]
        # `-c`/`-Command` are only shell-invocation flags when the command is
        # itself launched by a shell; in `dotnet test ... -c Release` the token
        # is a legitimate configuration flag and must not be rejected (D1 fix).
        shell_invocation = bool(command) and command[0] in SHELL_TOKENS
        unsafe = any(
            token in SHELL_TOKENS
            or (shell_invocation and token in SHELL_FLAGS)
            or any(part in token for part in COMPOUND_TOKENS)
            or "`" in token
            for token in command
        )
        if unsafe:
            violations.append(
                "execution %d uses a shell wrapper/compound command: %r" % (idx, command)
            )


def _rule_boundary(executions, violations):
    broad_sweeps = []
    solution_builds = []
    for idx, execution in enumerate(executions):
        if execution["phase"] != "boundary":
            continue
        command = execution["command"]
        if is_test(command):
            # Filtered boundary tests are legitimate (an affected integration
            # test run directly at the boundary); only unfiltered/solution-wide
            # sweeps count against the single-comprehensive-sweep cap (D1 fix).
            if not (filter_present(command) and filter_value(command) not in (None, "")):
                broad_sweeps.append(idx)
        if is_build(command) and references_solution(command):
            solution_builds.append(idx)
    if len(broad_sweeps) > 1:
        violations.append(
            "more than one comprehensive boundary test sweep: %d" % len(broad_sweeps)
        )
    if len(solution_builds) > 1:
        violations.append(
            "multiple boundary solution builds: %d" % len(solution_builds)
        )


def _rule_scope_conformance(data, executions, violations):
    scope = data.get("scope") if isinstance(data.get("scope"), dict) else {}
    allowed = set()
    raw_selectors = scope.get("selectors")
    if isinstance(raw_selectors, list):
        allowed.update(raw_selectors)
    unvalidated = set()
    amendments = data.get("amendments")
    if isinstance(amendments, list):
        for amendment in amendments:
            if not isinstance(amendment, dict):
                continue
            added = amendment.get("added_selectors")
            if not isinstance(added, list):
                continue
            if amendment.get("validated_before_run") is True:
                allowed.update(added)
            else:
                unvalidated.update(added)
    for idx, execution in enumerate(executions):
        command = execution["command"]
        if not (is_test(command) and filter_present(command)):
            continue
        value = filter_value(command)
        if value in (None, ""):
            continue
        if value in unvalidated:
            violations.append(
                "execution %d: amendment selector used after execution "
                "(validated_before_run=false): %r" % (idx, value)
            )
        elif value not in allowed:
            violations.append(
                "execution %d: filter out of scope / silent widening: %r" % (idx, value)
            )


def _rule_rebuild(scope, executions, violations):
    files = scope.get("files") if isinstance(scope.get("files"), list) else []
    compiled = any(
        isinstance(name, str) and name.endswith(COMPILED_EXT) for name in files
    )
    if not compiled:
        return
    if scope.get("rebuild") != "affected":
        violations.append("compiled files changed but scope.rebuild is not 'affected'")
    first_inner_test = None
    for idx, execution in enumerate(executions):
        if execution["phase"] == "inner" and is_test(execution["command"]):
            first_inner_test = idx
            break
    if first_inner_test is None:
        return
    built_before = any(
        is_build(execution["command"]) for execution in executions[:first_inner_test]
    )
    if not built_before:
        violations.append(
            "no affected dotnet build before the first inner dotnet test"
        )


def _rule_freshness(executions, violations):
    for idx, execution in enumerate(executions):
        command = execution["command"]
        if not (is_test(command) and "--no-build" in command):
            continue
        if execution["source_revision"] != execution["artifact_revision"]:
            violations.append(
                "execution %d: stale --no-build artifact "
                "(source_revision != artifact_revision)" % idx
            )
            continue
        matched = any(
            is_build(prior["command"])
            and prior["artifact_revision"] == execution["artifact_revision"]
            for prior in executions[:idx]
        )
        if not matched:
            violations.append(
                "execution %d: stale --no-build artifact "
                "(no prior build with matching artifact_revision)" % idx
            )


def _rule_boundary_freshness(executions, violations):
    for idx, execution in enumerate(executions):
        if execution["phase"] != "boundary":
            continue
        if execution["source_revision"] != execution["artifact_revision"]:
            violations.append(
                "execution %d: stale boundary evidence "
                "(source_revision != artifact_revision)" % idx
            )


def _rule_final_green(executions, violations):
    groups = {}
    for execution in executions:
        groups.setdefault(_identity(execution), []).append(execution)
    for key, items in groups.items():
        if items[-1]["exit_code"] != 0:
            violations.append("no final green result for group %r" % (key,))


def validate_report(data):
    violations = validate_brief(data)
    executions = data.get("executions")
    if "executions" not in data:
        violations.append("missing required key: executions")
        return violations
    if not isinstance(executions, list) or not executions:
        violations.append("executions must be a nonempty list")
        return violations

    structural = []
    for idx, execution in enumerate(executions):
        structural.extend(validate_execution(execution, idx))
    if structural:
        return violations + structural

    _rule_hygiene(executions, violations)

    for idx, execution in enumerate(executions):
        if execution["phase"] == "inner" and command_is_broad(execution["command"]):
            violations.append(
                "execution %d: broad command not allowed in inner phase: %r"
                % (idx, execution["command"])
            )

    _rule_boundary(executions, violations)
    _rule_scope_conformance(data, executions, violations)

    scope = data.get("scope") if isinstance(data.get("scope"), dict) else {}
    _rule_rebuild(scope, executions, violations)
    _rule_freshness(executions, violations)
    _rule_boundary_freshness(executions, violations)
    _rule_final_green(executions, violations)
    return violations


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise _UsageError("cannot read %s: %s" % (path, exc)) from exc
    except ValueError as exc:
        raise _UsageError("malformed JSON in %s: %s" % (path, exc)) from exc
    if not isinstance(data, dict):
        raise _UsageError("top-level JSON must be an object")
    return data


def main(argv=None):
    parser = _ArgumentParser(
        prog="validate_inner_loop.py",
        description="Validate the PDCA inner-loop test scope/evidence gate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "mode", choices=("brief", "report"),
        help="brief: validate the mandatory scope before dispatch; "
             "report: validate scope + execution evidence before CHECK",
    )
    parser.add_argument("path", help="path to the scope/evidence JSON object")
    args = parser.parse_args(argv)

    try:
        data = _load_json(args.path)
    except _UsageError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1

    violations = validate_brief(data) if args.mode == "brief" else validate_report(data)
    if violations:
        for message in violations:
            print("FAIL: %s" % message)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
