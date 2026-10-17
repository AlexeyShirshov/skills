#!/usr/bin/env python3
"""validate_inner_loop.py — fail-closed gate for the PDCA inner-loop test scope.

The PDCA contract separates the **kind of run** from the **phase**, not from a
command's name or the presence of ``--filter``:

  * **unit** runs are unlimited inside DO and at phase boundaries;
  * **integration** runs are permitted only at the DO->CHECK boundary, and only
    within the scope/count PLAN fixed up front — an integration run inside DO is
    an actual policy deviation (and an integration run *attempted* but never
    started is a distinct, explicitly recorded state).

This helper validates the JSON artifacts that make that enforceable:

  * a **brief** scope, produced before dispatch to `coder`;
  * a **journal** — the raw, append-only execution capture (a `start` event at
    launch, the result appended on completion) that the report is projected from;
  * a **report** (brief + `executions`), produced before CHECK passes; with
    ``--journal`` it is additionally checked to be a *faithful projection* of the
    journal (a dropped execution is a completeness failure, never a way to pass);
  * a **manifest** — the frozen evidence manifest (contract row ID -> evidence by
    reference), written at the DO->CHECK boundary and reconciled by CHECK.

It never executes any supplied command: it only inspects the recorded argument
arrays.  A violation is printed as a `FAIL: ` line and exits 2.  A usage error,
unreadable file or malformed JSON prints `ERROR: ` and exits 1.  Exit 0 means
valid.

Recording and judging are separate: a recorded deviation stays in the ledger and
does not legalise the run; deleting it does not cancel it.

Schema (one JSON object)
-----------------------
Top level:  ``unit`` (nonempty str), ``scope`` (obj), optional ``amendments``
(list), and for ``report`` also ``executions`` (nonempty list).

``scope``: ``projects`` (nonempty list[nonempty str]); ``selectors`` (nonempty
list[nonempty str]); ``files`` (list[str], may be empty); ``rationale``
(nonempty str); ``rebuild`` ("affected" | "none"); ``boundary`` (nonempty str).
Optional: ``integration_projects`` (list[str]) names the test projects that
actually execute integration tests, and ``integration_boundary_runs`` (int >= 1)
is the PLAN-approved number of *actual* integration runs at the boundary.  The
gate never invents a numeric cap: with no ``integration_boundary_runs`` declared
only the phase rule applies.  A docs-only scope (no ``.cs``/``.fs``/``.vb``
file) must not claim ``rebuild == "affected"`` (fictitious rebuild).

``amendments`` item: ``reason`` (nonempty str), ``added_selectors`` (nonempty
list[nonempty str]), ``validated_before_run`` (bool).

``executions`` item: ``id`` (optional nonempty str — the journal execution id);
``command`` (nonempty list[str]); ``phase`` ("inner" | "boundary");
``source_revision`` / ``artifact_revision`` (nonempty str); optional ``kind``
("unit" | "integration" | "build" | "other", inferred from the selected
projects/command when absent); optional ``state`` (default ``finished``) one of
``finished`` | ``started`` | ``running`` | ``interrupted`` | ``canceled`` |
``failed-to-start`` | ``not-started``.

``exit_code`` (int, bool rejected) and ``selected_count`` (int >= 1, bool
rejected — the number of tests the run actually selected) are required for a
``finished`` run; they must be absent/null for ``started``/``running``/
``failed-to-start``/``not-started`` and are optional for ``interrupted``/
``canceled``.  Neither is ever invented for a run that did not finish.
An unfinished or not-started attempt never satisfies a required success, but it
*is* retained even after a later successful retry.

``journal``: ``unit`` / ``scope`` (+ optional ``amendments``) as above, and
``events`` (nonempty list) of ``start`` / ``finish`` records that share an ``id``:
a ``start`` carries ``phase``, ``command``, ``source_revision``,
``artifact_revision`` and ``at``; a ``finish`` carries ``state``, optional
``exit_code`` / ``selected_count`` (required ints for ``finished``), ``at`` and
optional ``log``.  ``project`` rebuilds the report from the journal
mechanically — an execution whose ``start`` was recorded can never be dropped.

``manifest``: ``task`` / ``tree`` / ``status_file`` (nonempty str); ``contract_rv``
(int >= 1, bool rejected); ``required_rows`` (nonempty list[nonempty str], unique);
``rows`` (nonempty list). Each row: ``id`` (nonempty str, unique); ``status`` in
``met`` | ``open`` | ``na``; ``met`` requires a nonempty ``evidence`` list whose items have
``kind`` and ``path`` (nonempty str) and an optional integer ``exit`` (bool rejected);
``open`` requires a nonempty ``reason``; ``na`` requires a nonempty ``predicate``. The row
IDs must cover ``required_rows`` exactly — a missing or undeclared ID is a violation. A row
is NOT required to be ``met``: an ``open`` row is valid input and is exactly what forbids PASS
in CHECK.

Examples
--------
  # validate the mandatory DO scope before dispatch
  validate_inner_loop.py brief /tmp/scope.json

  # validate scope + execution evidence before CHECK
  validate_inner_loop.py report /tmp/evidence.json

  # validate the report *and* prove it is a faithful projection of the journal
  validate_inner_loop.py report /tmp/evidence.json --journal /tmp/journal.json

  # rebuild the report mechanically from the raw journal
  validate_inner_loop.py project /tmp/journal.json

  # validate the frozen evidence manifest (row coverage + row/evidence shape)
  validate_inner_loop.py manifest .pdca/<task>/rv1/manifest.json

  # exit 0 = valid, 2 = violation(s), 1 = usage / unreadable / malformed JSON
  validate_inner_loop.py report /tmp/evidence.json; echo $?
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

# Selectors that silently select a whole project/solution are never a valid
# affected subset (rule 3).
BROAD_SELECTORS = {"", "*", "*.*", "all", "All"}

# Extensions that make a changed file a compiled input (rule 12).
COMPILED_EXT = (".cs", ".fs", ".vb")

# Allowed per-row statuses in the frozen evidence manifest.
ROW_STATUSES = ("met", "open", "na")

# Actual run kinds (E10: unit unlimited, integration only at the DO->CHECK
# boundary).  ``kind`` is declared; when absent it is inferred from the selected
# projects/command — never from the presence of ``--filter``.
EXEC_KINDS = ("unit", "integration", "build", "other")
INTEGRATION_KIND = "integration"

# Explicit execution states.  ``finished`` is the default for a legacy row.
# ``started``/``running`` are in flight, ``interrupted``/``canceled`` ended
# without a satisfying result, ``failed-to-start``/``not-started`` never ran.
EXEC_STATES = (
    "finished",
    "started",
    "running",
    "interrupted",
    "canceled",
    "failed-to-start",
    "not-started",
)
FINISHED_STATE = "finished"
# States that never carry an invented exit code / selected count.
NOT_STARTED_STATES = ("failed-to-start", "not-started")
IN_FLIGHT_STATES = ("started", "running")
NO_RESULT_STATES = IN_FLIGHT_STATES + NOT_STARTED_STATES

# Journal event kinds (mandatory capture path: start at launch, result appended).
JOURNAL_EVENTS = ("start", "finish")

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


def _is_int(value):
    """True for a real JSON integer (booleans are not integers here)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_optional_int(value):
    return value is None or _is_int(value)


def _is_optional_count(value):
    """selected_count when present: a real integer >= 1."""
    return value is None or (_is_int(value) and value >= 1)


def _exec_state(execution):
    state = execution.get("state")
    return state if state in EXEC_STATES else FINISHED_STATE


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


def selected_projects(command):
    """Positional arguments a `dotnet test`/`dotnet build` selects (rule 14).

    The value of ``--filter``/``-filter`` is an option value, never a project.
    """
    if not is_dotnet(command):
        return []
    tokens = command[2:]
    projects = []
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token in ("--filter", "-filter"):
            idx += 2
            continue
        if not token.startswith("-"):
            projects.append(token)
        idx += 1
    return projects


def selects_integration_project(command, integration_projects):
    """True when the command really selects a project PLAN declared integration."""
    if not integration_projects:
        return False
    for token in selected_projects(command):
        for project in integration_projects:
            if token == project or token.endswith("/" + project) or project.endswith("/" + token):
                return True
    return False


def command_is_broad(command):
    """A BROAD command can select far more than the declared affected subset.

    The presence of ``--filter`` is deliberately **not** a criterion (E10): an
    unfiltered run of an affected *unit* project is a legitimate unit run, not a
    comprehensive sweep.  What stays broad is a whole-solution ``build``/``test``
    and a valueless ``--filter``.
    """
    if not command:
        return False
    # dotnet build/test against a whole solution.
    if is_dotnet(command) and verb(command) in ("build", "test") and references_solution(command):
        return True
    # Any command carrying a valueless --filter / -filter.
    for flag in ("--filter", "-filter"):
        if flag in command:
            idx = command.index(flag)
            if idx + 1 >= len(command) or command[idx + 1].startswith("-"):
                return True
    return False


def actual_kind(execution, scope):
    """The run's actual kind: declared ``kind`` wins, else inferred.

    Inference follows the **selected projects/command**, so a mixed solution run
    that really executes integration is never reclassified as `unit` by a command
    name or a filter (E10).
    """
    declared = execution.get("kind")
    if declared in EXEC_KINDS:
        return declared
    command = execution["command"]
    if is_build(command):
        return "build"
    if not is_test(command):
        return "other"
    integration_projects = ()
    if isinstance(scope, dict):
        raw = scope.get("integration_projects")
        if isinstance(raw, list):
            integration_projects = tuple(t for t in raw if isinstance(t, str))
    if references_solution(command) or selects_integration_project(command, integration_projects):
        return INTEGRATION_KIND
    return "unit"


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
    if "integration_projects" in scope:
        if not _is_str_list(scope.get("integration_projects")):
            violations.append(
                "scope.integration_projects must be a list of strings "
                "(the test projects that actually execute integration tests)"
            )
    if "integration_boundary_runs" in scope:
        planned = scope.get("integration_boundary_runs")
        if not _is_int(planned) or planned < 1:
            violations.append(
                "scope.integration_boundary_runs must be an integer >= 1 "
                "(the PLAN-approved number of actual integration runs at the boundary)"
            )
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
    if "id" in execution and not _nonempty_str(execution.get("id")):
        violations.append("execution %d id must be a nonempty string when present" % idx)
    if not _is_nonempty_str_list(execution.get("command")):
        violations.append("execution %d command must be a nonempty list of strings" % idx)
    if execution.get("phase") not in ("inner", "boundary"):
        violations.append("execution %d phase must be 'inner' or 'boundary'" % idx)
    if not _nonempty_str(execution.get("source_revision")):
        violations.append("execution %d source_revision must be a nonempty string" % idx)
    if not _nonempty_str(execution.get("artifact_revision")):
        violations.append("execution %d artifact_revision must be a nonempty string" % idx)
    if "kind" in execution and execution.get("kind") not in EXEC_KINDS:
        violations.append(
            "execution %d kind must be one of %s" % (idx, "/".join(EXEC_KINDS))
        )
    state = execution.get("state", FINISHED_STATE)
    if state not in EXEC_STATES:
        violations.append(
            "execution %d state must be one of %s" % (idx, "/".join(EXEC_STATES))
        )
        return violations
    exit_code = execution.get("exit_code")
    selected_count = execution.get("selected_count")
    if state == FINISHED_STATE:
        if not _is_int(exit_code):
            violations.append("execution %d exit_code must be an integer" % idx)
        if not (_is_int(selected_count) and selected_count >= 1):
            violations.append(
                "execution %d selected_count must be an integer >= 1 "
                "(zero/missing selected tests)" % idx
            )
    elif state in NO_RESULT_STATES:
        # A run that never finished cannot carry an invented exit code / count.
        if exit_code is not None:
            violations.append(
                "execution %d state %r must not carry an exit_code "
                "(a run that did not finish has no invented result)" % (idx, state)
            )
        if selected_count is not None:
            violations.append(
                "execution %d state %r must not carry a selected_count "
                "(a run that did not finish has no invented result)" % (idx, state)
            )
    else:
        # interrupted / canceled: a real code may exist, but never an invented one.
        if not _is_optional_int(exit_code):
            violations.append(
                "execution %d exit_code must be an integer or null" % idx
            )
        if not _is_optional_count(selected_count):
            violations.append(
                "execution %d selected_count must be null or an integer >= 1" % idx
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


def _rule_boundary(scope, executions, violations):
    """One comprehensive solution sweep at the boundary (PLAN may allow more).

    The sweep is identified by an actual whole-solution ``dotnet test`` — never
    by the absence of ``--filter`` (E10).  A PLAN-declared
    ``scope.integration_boundary_runs`` may raise the allowance; the gate invents
    no universal numeric cap of its own.
    """
    sweeps = []
    solution_builds = []
    for idx, execution in enumerate(executions):
        if execution["phase"] != "boundary":
            continue
        command = execution["command"]
        if is_test(command) and references_solution(command):
            sweeps.append(idx)
        if is_build(command) and references_solution(command):
            solution_builds.append(idx)
    allowed_sweeps = 1
    planned = scope.get("integration_boundary_runs") if isinstance(scope, dict) else None
    if _is_int(planned) and planned > allowed_sweeps:
        allowed_sweeps = planned
    if len(sweeps) > allowed_sweeps:
        violations.append(
            "more than one comprehensive boundary test sweep: %d (PLAN allowed %d)"
            % (len(sweeps), allowed_sweeps)
        )
    if len(solution_builds) > 1:
        violations.append(
            "multiple boundary solution builds: %d" % len(solution_builds)
        )


def _rule_integration_scope(scope, executions, violations):
    """Unit runs are unlimited; integration runs are boundary-only and planned.

    Classification follows the actually selected projects/solution, so a mixed
    run that really executes integration is not "unit" because of a command name
    or a filter.  Recording a deviation here keeps the run in the ledger; it does
    not legalise it, and its absence would not cancel it.
    """
    integration_projects = ()
    planned = None
    if isinstance(scope, dict):
        raw = scope.get("integration_projects")
        if isinstance(raw, list):
            integration_projects = tuple(t for t in raw if isinstance(t, str))
        if _is_int(scope.get("integration_boundary_runs")):
            planned = scope["integration_boundary_runs"]
    boundary_integration = []
    for idx, execution in enumerate(executions):
        command = execution["command"]
        declared = execution.get("kind")
        kind = actual_kind(execution, scope)
        # Classification must match the actually selected scope: a solution-wide
        # or integration-project run may not be labelled `unit`.
        if declared == "unit" and is_test(command) and (
            references_solution(command)
            or selects_integration_project(command, integration_projects)
        ):
            violations.append(
                "execution %d declares kind 'unit' but the selected scope runs "
                "integration (a mixed solution/project run is not unit): %r"
                % (idx, command)
            )
        if kind != INTEGRATION_KIND:
            continue
        state = _exec_state(execution)
        if execution["phase"] == "inner":
            if state in NOT_STARTED_STATES:
                violations.append(
                    "execution %d: integration run attempted inside DO (inner "
                    "phase) — policy violation, attempt never started (%s); "
                    "recorded, not legalised" % (idx, state)
                )
            else:
                violations.append(
                    "execution %d: integration run executed inside DO (inner "
                    "phase) — actual policy violation, not masked by the phase "
                    "or a rename; the run stays in the ledger" % idx
                )
        else:
            boundary_integration.append(idx)
    if planned is not None and len(boundary_integration) > planned:
        violations.append(
            "boundary integration runs exceed the planned budget: %d planned, "
            "%d executed (over-budget runs are retained in the raw journal, "
            "not dropped)" % (planned, len(boundary_integration))
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
        finished = [e for e in items if _exec_state(e) == FINISHED_STATE]
        if not finished:
            violations.append(
                "no finished execution for group %r: unfinished/not-started "
                "attempts are retained but do not satisfy required success"
                % (key,)
            )
            continue
        if finished[-1]["exit_code"] != 0:
            violations.append("no final green result for group %r" % (key,))


def validate_report(data, journal=None):
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

    scope = data.get("scope") if isinstance(data.get("scope"), dict) else {}

    _rule_hygiene(executions, violations)

    for idx, execution in enumerate(executions):
        if execution["phase"] == "inner" and command_is_broad(execution["command"]):
            violations.append(
                "execution %d: broad command not allowed in inner phase: %r"
                % (idx, execution["command"])
            )

    _rule_boundary(scope, executions, violations)
    _rule_integration_scope(scope, executions, violations)
    _rule_scope_conformance(data, executions, violations)
    _rule_rebuild(scope, executions, violations)
    _rule_freshness(executions, violations)
    _rule_boundary_freshness(executions, violations)
    _rule_final_green(executions, violations)
    if journal is not None:
        violations.extend(_rule_projection_completeness(journal, executions))
    return violations


def validate_journal(data):
    """Validate the raw execution journal (the mandatory capture path).

    A ``start`` event is the capture point; a ``finish`` result is appended on
    completion.  An execution with no ``finish`` yet is valid input (it is simply
    not finished), never an invented result.
    """
    violations = []
    if not _nonempty_str(data.get("unit")):
        violations.append("unit must be a nonempty string")
    scope = data.get("scope")
    if not isinstance(scope, dict):
        violations.append("scope must be an object")
    else:
        violations.extend(validate_scope(scope))
    violations.extend(validate_amendments(data))

    events = data.get("events")
    if not isinstance(events, list) or not events:
        violations.append("events must be a nonempty list")
        return violations

    started = {}
    finished = set()
    for idx, event in enumerate(events):
        if not isinstance(event, dict):
            violations.append("event %d must be an object" % idx)
            continue
        event_id = event.get("id")
        if not _nonempty_str(event_id):
            violations.append("event %d id must be a nonempty string" % idx)
            continue
        kind = event.get("event")
        if kind not in JOURNAL_EVENTS:
            violations.append("event %d event must be 'start' or 'finish'" % idx)
            continue
        if kind == "start":
            if event_id in started:
                violations.append("duplicate start event for execution id %r" % event_id)
                continue
            if event.get("phase") not in ("inner", "boundary"):
                violations.append(
                    "start event %r phase must be 'inner' or 'boundary'" % event_id
                )
            if not _is_nonempty_str_list(event.get("command")):
                violations.append(
                    "start event %r command must be a nonempty list of strings" % event_id
                )
            if not _nonempty_str(event.get("source_revision")):
                violations.append(
                    "start event %r source_revision must be a nonempty string" % event_id
                )
            if not _nonempty_str(event.get("artifact_revision")):
                violations.append(
                    "start event %r artifact_revision must be a nonempty string" % event_id
                )
            if "kind" in event and event.get("kind") not in EXEC_KINDS:
                violations.append(
                    "start event %r kind must be one of %s"
                    % (event_id, "/".join(EXEC_KINDS))
                )
            if not _nonempty_str(event.get("at")):
                violations.append(
                    "start event %r at must be a nonempty timestamp" % event_id
                )
            started[event_id] = event
            continue
        if event_id not in started:
            violations.append(
                "finish event %r has no recorded start (the start is the mandatory "
                "capture point)" % event_id
            )
            continue
        if event_id in finished:
            violations.append("duplicate finish event for execution id %r" % event_id)
            continue
        state = event.get("state", FINISHED_STATE)
        if state not in EXEC_STATES or state in IN_FLIGHT_STATES:
            violations.append(
                "finish event %r state must be one of finished/interrupted/"
                "canceled/failed-to-start/not-started" % event_id
            )
            continue
        if state == FINISHED_STATE:
            if not _is_int(event.get("exit_code")):
                violations.append(
                    "finish event %r (finished) exit_code must be an integer" % event_id
                )
            if not (_is_int(event.get("selected_count")) and event["selected_count"] >= 1):
                violations.append(
                    "finish event %r (finished) selected_count must be an integer >= 1"
                    % event_id
                )
        elif state in NOT_STARTED_STATES:
            if event.get("exit_code") is not None or event.get("selected_count") is not None:
                violations.append(
                    "finish event %r (%s) must not carry an invented "
                    "exit_code/selected_count" % (event_id, state)
                )
        else:
            if not _is_optional_int(event.get("exit_code")):
                violations.append(
                    "finish event %r exit_code must be an integer or null" % event_id
                )
            if not _is_optional_count(event.get("selected_count")):
                violations.append(
                    "finish event %r selected_count must be null or an integer >= 1"
                    % event_id
                )
        if not _nonempty_str(event.get("at")):
            violations.append(
                "finish event %r at must be a nonempty timestamp" % event_id
            )
        finished.add(event_id)
    return violations


def project_journal(data):
    """Rebuild the report from the raw journal — mechanically, not selectively.

    Every recorded ``start`` becomes an execution, so a report projected this way
    can never silently drop an execution that really started.
    """
    starts = {}
    finishes = {}
    order = []
    for event in data.get("events", []):
        if not isinstance(event, dict):
            continue
        event_id = event.get("id")
        if not _nonempty_str(event_id):
            continue
        if event.get("event") == "start" and event_id not in starts:
            starts[event_id] = event
            order.append(event_id)
        elif event.get("event") == "finish" and event_id not in finishes:
            finishes[event_id] = event
    executions = []
    for event_id in order:
        start = starts[event_id]
        finish = finishes.get(event_id)
        state = FINISHED_STATE if finish is not None else "started"
        if finish is not None:
            state = finish.get("state", FINISHED_STATE)
        execution = {
            "id": event_id,
            "command": start.get("command"),
            "phase": start.get("phase"),
            "source_revision": start.get("source_revision"),
            "artifact_revision": start.get("artifact_revision"),
            "started_at": start.get("at"),
            "state": state,
        }
        if start.get("kind") in EXEC_KINDS:
            execution["kind"] = start["kind"]
        if finish is not None:
            if finish.get("at") is not None:
                execution["finished_at"] = finish["at"]
            if finish.get("log") is not None:
                execution["log"] = finish["log"]
            execution["exit_code"] = finish.get("exit_code")
            execution["selected_count"] = finish.get("selected_count")
        else:
            # A run that did not finish carries no invented result.
            execution["exit_code"] = None
            execution["selected_count"] = None
        executions.append(execution)
    report = {"unit": data.get("unit"), "scope": data.get("scope")}
    if "amendments" in data:
        report["amendments"] = data.get("amendments")
    report["executions"] = executions
    return report


def _rule_projection_completeness(journal, executions):
    """A report handed to CHECK must be a faithful projection of the raw journal."""
    violations = []
    projected = project_journal(journal)
    projected_ids = [e.get("id") for e in projected["executions"]]
    report_ids = [e.get("id") for e in executions]
    if any(not _nonempty_str(execution_id) for execution_id in report_ids):
        violations.append(
            "report executions must carry the journal execution id when a "
            "journal is supplied"
        )
    projected_set = set(projected_ids)
    report_set = set(report_ids)
    missing = [i for i in projected_ids if i not in report_set]
    if missing:
        violations.append(
            "projection incomplete: report omits execution(s) %s recorded in the "
            "raw journal (a started execution is never dropped from the ledger)"
            % ", ".join(repr(i) for i in missing)
        )
    extra = [i for i in report_ids if i not in projected_set]
    if extra:
        violations.append(
            "report contains execution(s) %s absent from the raw journal (the "
            "report is projected from the journal, not hand-selected)"
            % ", ".join(repr(i) for i in extra)
        )
    return violations


CLEANUP_KINDS = ("staged-copy", "temp")
RETAINED_ROLES = ("final_report", "frozen_manifest", "certification", "digests")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_GLOB_CHARS = ("*", "?", "[", "]")


def _is_sha256(value):
    return isinstance(value, str) and bool(_HEX64.match(value))


def sha256_of(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _in_task_rv_dir(path, evidence_root, task, rv):
    """The deletion scope: only this task's own rv snapshot dir, never a blanket rm."""
    if not _nonempty_str(path):
        return False
    if any(char in path for char in _GLOB_CHARS):
        return False
    prefix = "%s/%s/" % (evidence_root.rstrip("/"), task)
    if not path.startswith(prefix):
        return False
    if "/rv%d/" % rv not in path:
        return False
    normalised = path.rstrip("/")
    task_root = "%s/%s" % (evidence_root.rstrip("/"), task)
    return normalised not in (task_root, "%s/rv%d" % (task_root, rv))


def validate_cleanup(data):
    """Gate the ACT cleanup receipt: right to terminal closure + deletion scope.

    A premature cleanup (no approved terminal closure / no independent final
    verdict) is rejected.  Only explicitly cleanable staged copies/temp files
    inside this task's own ``rv`` dir may be removed; the retained compact
    records and the frozen manifest are never touched, and no other task's files
    may be removed by a broad pattern.
    """
    violations = []
    if not _nonempty_str(data.get("task")):
        violations.append("cleanup.task must be a nonempty string")
    rv = data.get("rv")
    if not _is_int(rv) or rv < 1:
        violations.append("cleanup.rv must be an integer >= 1")
        rv = 0
    evidence_root = data.get("evidence_root", ".pdca")
    if not _nonempty_str(evidence_root):
        violations.append("cleanup.evidence_root must be a nonempty string")
    if not _nonempty_str(data.get("at")):
        violations.append("cleanup.at must be a nonempty timestamp")

    closure = data.get("closure")
    if not isinstance(closure, dict):
        violations.append("cleanup.closure must be an object")
        closure = {}
    if closure.get("terminal") is not True or closure.get("approved") is not True:
        violations.append(
            "premature cleanup rejected: terminal closure is not established "
            "(closure.terminal/closure.approved must both be true)"
        )
    if not _nonempty_str(closure.get("independent_verdict")):
        violations.append(
            "premature cleanup rejected: the independent final CHECK verdict is "
            "missing (cleanup does not replace checks)"
        )
    if not _nonempty_str(closure.get("final_report")):
        violations.append("cleanup.closure.final_report must be a nonempty string")

    frozen = data.get("frozen_manifest")
    if not isinstance(frozen, dict):
        violations.append("cleanup.frozen_manifest must be an object")
        frozen = {}
    if not _nonempty_str(frozen.get("path")):
        violations.append("cleanup.frozen_manifest.path must be a nonempty string")
    if not _is_sha256(frozen.get("sha256")):
        violations.append("cleanup.frozen_manifest.sha256 must be a sha256 hex digest")

    retained = data.get("retained")
    if not isinstance(retained, dict):
        violations.append("cleanup.retained must be an object of role -> path")
        retained = {}
    for role in RETAINED_ROLES:
        if not _nonempty_str(retained.get(role)):
            violations.append(
                "cleanup.retained.%s must be a nonempty path (the compact records "
                "are kept, not cleaned)" % role
            )
    if _nonempty_str(frozen.get("path")) and retained.get("frozen_manifest") != frozen.get("path"):
        violations.append(
            "cleanup.retained.frozen_manifest must be the frozen manifest path "
            "(the frozen manifest is retained, never rewritten)"
        )

    removed = data.get("removed")
    if not isinstance(removed, list) or not removed:
        violations.append(
            "cleanup.removed must be a nonempty list of removed heavy staged "
            "copies/temp materials of this task"
        )
        removed = []

    retained_paths = {path for path in retained.values() if _nonempty_str(path)}
    seen = set()
    task = data.get("task")
    for idx, item in enumerate(removed):
        if not isinstance(item, dict):
            violations.append("cleanup.removed %d must be an object" % idx)
            continue
        path = item.get("path")
        if not _nonempty_str(path):
            violations.append("cleanup.removed %d path must be a nonempty string" % idx)
            continue
        if not _is_sha256(item.get("sha256")):
            violations.append(
                "cleanup.removed %d sha256 must record the prior content digest" % idx
            )
        if item.get("kind") not in CLEANUP_KINDS:
            violations.append(
                "cleanup.removed %d kind must be one of %s"
                % (idx, "/".join(CLEANUP_KINDS))
            )
        if not _nonempty_str(item.get("reason")):
            violations.append("cleanup.removed %d reason must be a nonempty string" % idx)
        if path in seen:
            violations.append("cleanup.removed duplicate path: %r" % path)
        seen.add(path)
        if path in retained_paths:
            violations.append(
                "cleanup.removed %r is a retained record and must not be deleted" % path
            )
        if not _in_task_rv_dir(path, evidence_root, task, rv) :
            violations.append(
                "cleanup.removed %r is outside this task's own rv dir %s/%s/rv%r "
                "(no blanket rm, no other task's artifacts, no broad pattern)"
                % (path, evidence_root, task, rv)
            )
    return violations


def validate_archived(manifest, manifest_path, receipt):
    """Archived-pack validation: a missing body must be explained by the receipt.

    A staged body missing *before* ACT, or without a valid cleanup receipt, stays
    an error; after a correct ACT it is a planned lifecycle, not "the evidence
    never existed".  The frozen manifest itself must be unchanged (its digest
    matches the receipt), and archived validation claims no re-certification over
    cleaned-up bodies.
    """
    violations = validate_manifest(manifest)
    violations.extend(validate_cleanup(receipt))
    if violations:
        return violations
    frozen = receipt.get("frozen_manifest", {})
    try:
        actual = sha256_of(manifest_path)
    except OSError as exc:
        violations.append("cannot read the frozen manifest %s: %s" % (manifest_path, exc))
        return violations
    if actual != frozen.get("sha256"):
        violations.append(
            "the frozen manifest was rewritten after cleanup (digest %s != receipt %s)"
            % (actual, frozen.get("sha256"))
        )
    removed = {item["path"] for item in receipt.get("removed", []) if isinstance(item, dict)}
    rows = manifest.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            evidence = row.get("evidence")
            if not isinstance(evidence, list):
                continue
            for item in evidence:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                if not _nonempty_str(path) or path in removed:
                    continue
                if not os.path.exists(path):
                    violations.append(
                        "missing staged body %r: absent before ACT or without a "
                        "valid cleanup receipt is an error" % path
                    )
    return violations


def _validate_evidence_item(item, row_id, idx):
    violations = []
    if not isinstance(item, dict):
        return ["row %s evidence %d must be an object" % (row_id, idx)]
    if not _nonempty_str(item.get("kind")):
        violations.append("row %s evidence %d kind must be a nonempty string" % (row_id, idx))
    if not _nonempty_str(item.get("path")):
        violations.append("row %s evidence %d path must be a nonempty string" % (row_id, idx))
    exit_code = item.get("exit")
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        violations.append("row %s evidence %d exit must be an integer when present" % (row_id, idx))
    return violations


def validate_manifest(data):
    """Validate the frozen evidence manifest: row coverage + row/evidence shape.

    Structural/coverage only: the manifest is *allowed* to carry ``open`` rows (that is
    what forbids PASS in CHECK). This function does not decide pass/fail of the task.
    """
    violations = []
    for key in ("task", "tree", "status_file"):
        if not _nonempty_str(data.get(key)):
            violations.append("%s must be a nonempty string" % key)
    contract_rv = data.get("contract_rv")
    if not isinstance(contract_rv, int) or isinstance(contract_rv, bool) or contract_rv < 1:
        violations.append("contract_rv must be an integer >= 1")

    required = data.get("required_rows")
    req_ok = _is_nonempty_str_list(required)
    if not req_ok:
        violations.append("required_rows must be a nonempty list of nonempty strings")
    elif len(set(required)) != len(required):
        violations.append("required_rows contains duplicate IDs")
        req_ok = False

    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        violations.append("rows must be a nonempty list")
        return violations

    seen = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            violations.append("row %d must be an object" % idx)
            continue
        row_id = row.get("id")
        if not _nonempty_str(row_id):
            violations.append("row %d id must be a nonempty string" % idx)
            continue
        if row_id in seen:
            violations.append("duplicate row id: %r" % row_id)
            continue
        seen[row_id] = row
        status = row.get("status")
        if status not in ROW_STATUSES:
            violations.append(
                "row %s status must be one of %s" % (row_id, "/".join(ROW_STATUSES))
            )
        elif status == "met":
            evidence = row.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                violations.append("row %s (met) must have a nonempty evidence list" % row_id)
            else:
                for ev_idx, item in enumerate(evidence):
                    violations.extend(_validate_evidence_item(item, row_id, ev_idx))
        elif status == "open":
            if not _nonempty_str(row.get("reason")):
                violations.append("row %s (open) must have a nonempty reason" % row_id)
        elif status == "na":
            if not _nonempty_str(row.get("predicate")):
                violations.append("row %s (na) must have an observed predicate" % row_id)

    if req_ok:
        required_set = set(required)
        for row_id in required:
            if row_id not in seen:
                violations.append("required row missing from manifest: %r" % row_id)
        for row_id in seen:
            if row_id not in required_set:
                violations.append("manifest row not declared in required_rows: %r" % row_id)
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
        "mode",
        choices=("brief", "report", "journal", "project", "manifest", "cleanup", "archived"),
        help="brief: validate the mandatory scope before dispatch; "
             "report: validate scope + execution evidence before CHECK; "
             "journal: validate the raw start/finish execution capture; "
             "project: rebuild the report from the journal and validate it; "
             "manifest: validate the frozen evidence manifest (row coverage); "
             "cleanup: gate the ACT cleanup receipt (terminal closure + scope); "
             "archived: validate an archived pack against its cleanup receipt",
    )
    parser.add_argument("path", help="path to the scope/evidence/manifest JSON object")
    parser.add_argument(
        "--journal",
        help="with `report`: path to the raw execution journal, to prove the "
             "report is a faithful projection (no started execution dropped)",
    )
    parser.add_argument(
        "--cleanup",
        help="with `archived`: path to the ACT cleanup receipt that explains "
             "every removed staged body",
    )
    args = parser.parse_args(argv)

    try:
        data = _load_json(args.path)
    except _UsageError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1

    if args.mode == "brief":
        violations = validate_brief(data)
    elif args.mode == "report":
        journal_data = None
        if args.journal:
            try:
                journal_data = _load_json(args.journal)
            except _UsageError as exc:
                print("ERROR: %s" % exc, file=sys.stderr)
                return 1
            journal_violations = validate_journal(journal_data)
            if journal_violations:
                for message in journal_violations:
                    print("FAIL: %s" % message)
                return 2
        violations = validate_report(data, journal=journal_data)
    elif args.mode == "journal":
        violations = validate_journal(data)
    elif args.mode == "project":
        violations = validate_journal(data)
        if violations:
            for message in violations:
                print("FAIL: %s" % message, file=sys.stderr)
            return 2
        # Projection is mechanical: every recorded start becomes an execution.
        projections = project_journal(data)
        violations = validate_report(projections)
        if violations:
            # Keep stdout machine-parseable: diagnostics go to stderr.
            for message in violations:
                print("FAIL: %s" % message, file=sys.stderr)
            return 2
        print(json.dumps(projections, indent=2, sort_keys=True))
    elif args.mode == "cleanup":
        violations = validate_cleanup(data)
    elif args.mode == "archived":
        if not args.cleanup:
            print("ERROR: `archived` requires --cleanup <receipt.json>", file=sys.stderr)
            return 1
        try:
            receipt = _load_json(args.cleanup)
        except _UsageError as exc:
            print("ERROR: %s" % exc, file=sys.stderr)
            return 1
        violations = validate_archived(data, args.path, receipt)
    else:
        violations = validate_manifest(data)
    if violations:
        for message in violations:
            print("FAIL: %s" % message)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
