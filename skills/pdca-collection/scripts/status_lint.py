#!/usr/bin/env python3
"""Structural lint for a collection status file — the queue is data.

The queue lives in the Markdown tables of `.pdca/status/collection-<slug>.md`
(groups, items/tasks, units, decisions).  Ad-hoc edits break that data in two
ways this lint catches mechanically:

* a raw ``|`` inside a note splits the row into extra cells;
* a note wrapped onto a second line truncates the row and the table.

So the shape rules are: every data row carries exactly as many cells as **its
own** header, one physical line per record, and every status cell starts with a
value of its enumeration.  The lint is header-driven, not schema-fixed: the
header of each table is the schema for its rows, and only the enumerations and a
small required set of columns are pinned.

One optional typed column carries the PLAN-terminal projection: ``terminal`` is
``execution`` (the default when the column is absent or the cell is a placeholder,
so legacy records stay valid) or one of the three terminal causes.  A plan-terminal
row must stay ``incomplete``, must not be ``plan_state=ready`` and must record
``attempts=0``: a terminal resolution is neither readiness nor done and consumes
no attempt.  A plan-terminal row fails closed when the table has no ``status``
column to prove that ``incomplete``, and when the row's form is explicitly
``campaign`` — a campaign's established step goes to independent CHECK.

Usage::

    python3 .pdca/scripts/status_lint.py .pdca/status/collection-<slug>.md [...]
    python3 .pdca/scripts/status_lint.py --json <status-file>

Exit codes: ``0`` ok, ``2`` violation, ``1`` usage/operational error — the same
convention as the base ``plan_lint.py`` and ``pdca_evidence.py``.

The lint reads text only: it never writes, never repairs a row and never decides
a status.  A violation means the write is rejected and the writer repairs the
row in the same turn.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VERSION = 2

ITEM_STATUS = ("pending", "in-progress", "done", "incomplete")
GROUP_STATUS = ITEM_STATUS + ("merged",)
PLAN_STATE = ("pending", "running", "ready")
PREPARATION_STATE = ("pending", "ready")
DISPOSITION = ("active", "paused", "finalized")
#: ``execution`` (default) or one of the three PLAN-terminal causes.
TERMINAL = (
    "execution",
    "criteria-undetermined",
    "infeasible",
    "already-established",
)
PLAN_TERMINAL = TERMINAL[1:]

#: A cell that states "not set" rather than a state value.
PLACEHOLDERS = ("—", "–", "-", "n/a", "na", "none", "not set", "unset", "tbd", "empty")

_SEPARATOR = re.compile(r"^:?-+:?$")
_LEADING_WORD = re.compile(r"[a-z][a-z0-9_\-]*")


class Violation:
    def __init__(self, line: int, message: str) -> None:
        self.line = line
        self.message = message

    def as_dict(self) -> dict:
        return {"line": self.line, "message": self.message}


# --------------------------------------------------------------------------- #
# Markdown tables
# --------------------------------------------------------------------------- #


def cells(line: str) -> list[str]:
    """Cells of one physical table line; a raw ``|`` inside a note splits here."""
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip() for cell in text.split("|")]


def is_row(line: str) -> bool:
    return line.strip().startswith("|")


def is_separator(line: str) -> bool:
    if not is_row(line):
        return False
    parts = cells(line)
    return bool(parts) and all(_SEPARATOR.match(part) for part in parts)


def tables(lines: list[str]):
    """Yield ``(header_line, header_cells, separator_line, sep_cells, rows, tail)``.

    ``rows`` is a list of ``(line_number, cells)``; the table ends at the first
    line that is not a table row, which is exactly how a wrapped note truncates
    it.  ``tail`` is that terminating line number (or ``None`` at end of file).
    """
    index, total = 0, len(lines)
    while index < total - 1:
        if is_row(lines[index]) and is_separator(lines[index + 1]):
            header_line, header = index + 1, cells(lines[index])
            separator_line, separator = index + 2, cells(lines[index + 1])
            cursor = index + 2
            rows: list[tuple[int, list[str]]] = []
            while cursor < total and is_row(lines[cursor]):
                rows.append((cursor + 1, cells(lines[cursor])))
                cursor += 1
            tail = cursor + 1 if cursor < total else None
            yield header_line, header, separator_line, separator, rows, tail
            index = cursor
        else:
            index += 1


def truncates_table(lines: list[str], tail: int | None) -> bool:
    """A non-blank line glued to the last row: a note that wrapped out of the table.

    Headings and a new table are legal followers; prose without a blank line is
    not — a table row must stay one physical line.
    """
    if tail is None:
        return False
    text = lines[tail - 1].strip()
    return bool(text) and not is_row(text) and not text.startswith("#")


# --------------------------------------------------------------------------- #
# Column vocabulary
# --------------------------------------------------------------------------- #


def names_of(header: list[str]) -> list[str]:
    return [re.sub(r"\s+", " ", name.strip().lower()) for name in header]


def status_columns(names: list[str]) -> list[int]:
    """``status`` and qualified forms (``task status``, ``unit status``)."""
    return [
        index
        for index, name in enumerate(names)
        if name == "status" or name.endswith(" status")
    ]


def has(names: list[str], *keys: str) -> bool:
    return any(any(key in name for key in keys) for name in names)


def column(names: list[str], *keys: str) -> int | None:
    for index, name in enumerate(names):
        if any(key in name for key in keys):
            return index
    return None


def classify(names: list[str]) -> str:
    """``groups`` | ``items`` | ``units`` | ``other`` — the table's role.

    Recognition does not depend on the columns a broken table may have lost: the
    id/group columns identify the queue tables, and the required-column rule then
    reports the loss.
    """
    state = has(names, "plan_state", "preparation_state")
    if has(names, "worktree") and has(names, "group"):
        return "groups"
    if has(names, "group") and status_columns(names):
        return "items"
    if has(names, "form") and (state or status_columns(names)):
        return "units"
    return "other"


def leading(value: str) -> str:
    match = _LEADING_WORD.match(value.strip().lower())
    return match.group(0) if match else ""


def is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return not lowered or lowered.startswith(PLACEHOLDERS)


def attempts_violation(value: str, label: str) -> str | None:
    text = value.strip()
    if is_placeholder(text):
        return None
    if not re.fullmatch(r"\d+", text):
        return "%s %r is not a non-negative integer" % (label, text)
    return None


def state_violation(value: str, allowed: tuple[str, ...], label: str) -> str | None:
    lowered = value.strip().lower()
    if not lowered:
        return None
    if lowered.startswith(PLACEHOLDERS):
        return None
    word = leading(lowered)
    if word in allowed:
        return None
    return "%s %r is not one of: %s" % (label, value.strip(), " | ".join(allowed))


# --------------------------------------------------------------------------- #
# Lint
# --------------------------------------------------------------------------- #


def lint_text(text: str) -> tuple[list[Violation], int, int]:
    lines = text.splitlines()
    violations: list[Violation] = []
    table_count = row_count = 0

    for header_line, header, separator_line, separator, rows, tail in tables(lines):
        table_count += 1
        row_count += len(rows)
        names = names_of(header)

        if truncates_table(lines, tail):
            violations.append(
                Violation(
                    tail,
                    "this line follows the last table row without a blank line: a note "
                    "wrapped onto the next line truncates the table — one record per line",
                )
            )

        if len(separator) != len(header):
            violations.append(
                Violation(
                    separator_line,
                    "table separator has %d cells, header has %d"
                    % (len(separator), len(header)),
                )
            )

        for line_number, row in rows:
            if len(row) != len(header):
                violations.append(
                    Violation(
                        line_number,
                        "row has %d cells, header has %d — a raw '|' inside a note "
                        "splits the row, a note wrapped onto the next line truncates it"
                        % (len(row), len(header)),
                    )
                )
                continue

            identity = row[0].strip() if row else ""
            if not identity:
                violations.append(
                    Violation(line_number, "empty %r cell: every row states its id"
                              % (header[0].strip() or "id",))
                )

        kind = classify(names)
        if kind == "other":
            continue

        if kind == "groups":
            for key in ("group", "worktree", "branch", "ref"):
                if not has(names, key):
                    violations.append(
                        Violation(header_line, "groups table has no %r column" % key)
                    )
        elif kind == "items":
            for key in ("group", "plan_state"):
                if not has(names, key):
                    violations.append(
                        Violation(header_line, "items table has no %r column" % key)
                    )
            if not has(names, "branch", "worktree"):
                violations.append(
                    Violation(header_line, "items table has no 'branch' column")
                )
        elif kind == "units":
            if not has(names, "form"):
                violations.append(
                    Violation(header_line, "units table has no 'form' column")
                )

        if not rows and kind != "other":
            violations.append(
                Violation(header_line, "%s table has a header and no data rows" % kind)
            )

        identity_name = names[0] if names else "id"
        if identity_name in ("group", "task", "item", "id", "unit", "step"):
            seen: dict[str, int] = {}
            for line_number, row in rows:
                if len(row) != len(header):
                    continue
                identity = row[0].strip()
                if not identity:
                    continue
                if identity in seen:
                    violations.append(
                        Violation(
                            line_number,
                            "duplicate %s %r (first at line %d)"
                            % (identity_name, identity, seen[identity]),
                        )
                    )
                else:
                    seen[identity] = line_number

        statuses = status_columns(names)
        for index in statuses:
            allowed = GROUP_STATUS if kind == "groups" else ITEM_STATUS
            label = header[index].strip() or "status"
            for line_number, row in rows:
                if index < len(row):
                    message = state_violation(row[index], allowed, label)
                    if message:
                        violations.append(Violation(line_number, message))

        for key, allowed in (
            ("plan_state", PLAN_STATE),
            ("preparation_state", PREPARATION_STATE),
            ("disposition", DISPOSITION),
        ):
            index = column(names, key)
            if index is None:
                continue
            for line_number, row in rows:
                if index < len(row):
                    message = state_violation(row[index], allowed, key)
                    if message:
                        violations.append(Violation(line_number, message))

        if kind in ("items", "units"):
            terminal_index = column(names, "terminal")
            attempts_index = column(names, "attempts")
            plan_index = column(names, "plan_state")
            status_index = statuses[0] if statuses else None
            for line_number, row in rows:
                if len(row) != len(header):
                    continue
                identity = row[0].strip() or "?"
                cause = "execution"
                if terminal_index is not None:
                    cause = leading(row[terminal_index]) or "execution"
                    message = state_violation(row[terminal_index], TERMINAL, "terminal")
                    if message:
                        violations.append(Violation(line_number, message))
                if cause not in PLAN_TERMINAL:
                    if attempts_index is not None:
                        message = attempts_violation(row[attempts_index], "attempts")
                        if message:
                            violations.append(Violation(line_number, message))
                    continue
                if attempts_index is None:
                    violations.append(
                        Violation(
                            line_number,
                            "plan-terminal item %r has no 'attempts' column: a terminal "
                            "resolution consumes no attempt, record attempts 0" % identity,
                        )
                    )
                elif row[attempts_index].strip() != "0":
                    violations.append(
                        Violation(
                            line_number,
                            "plan-terminal item %r records attempts %r: no attempt is "
                            "consumed (0)" % (identity, row[attempts_index].strip()),
                        )
                    )
                if status_index is None:
                    violations.append(
                        Violation(
                            line_number,
                            "plan-terminal item %r has no 'status' column: a terminal "
                            "resolution is recorded as 'incomplete' and the record cannot "
                            "be checked without that column" % identity,
                        )
                    )
                elif leading(row[status_index]) != "incomplete":
                    violations.append(
                        Violation(
                            line_number,
                            "plan-terminal item %r is %r, not 'incomplete': a terminal "
                            "resolution is neither done nor credit"
                            % (identity, row[status_index].strip()),
                        )
                    )
                form_index = next(
                    (
                        index
                        for index, name in enumerate(names)
                        if name == "form" or name.endswith(" form")
                    ),
                    None,
                )
                if form_index is not None and leading(row[form_index]) == "campaign":
                    violations.append(
                        Violation(
                            line_number,
                            "plan-terminal item %r has form 'campaign': a campaign's "
                            "established step goes to an independent CHECK, not to a "
                            "plan-terminal resolution" % identity,
                        )
                    )
                if plan_index is not None:
                    plan_value = row[plan_index]
                    if leading(plan_value) != "pending" and not is_placeholder(plan_value):
                        violations.append(
                            Violation(
                                line_number,
                                "plan-terminal item %r has plan_state %r: a terminal "
                                "resolution is not a ready plan"
                                % (identity, plan_value.strip()),
                            )
                        )

    return violations, table_count, row_count


def lint_file(path: Path) -> tuple[list[Violation], int, int]:
    text = path.read_text(encoding="utf-8")
    return lint_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="status_lint.py",
        description="Lint the tables of a collection status file (the queue).",
    )
    parser.add_argument("files", nargs="+", help="status file(s) to lint")
    parser.add_argument("--json", action="store_true", help="print a JSON result")
    parser.add_argument("--version", action="version", version="status-lint %d" % VERSION)
    args = parser.parse_args(argv)

    results = []
    failed = False
    for name in args.files:
        path = Path(name)
        try:
            violations, table_count, row_count = lint_file(path)
        except OSError as exc:
            print("status-lint: %s" % exc, file=sys.stderr)
            return 1
        failed = failed or bool(violations)
        results.append(
            {
                "file": str(path),
                "tables": table_count,
                "rows": row_count,
                "violations": [item.as_dict() for item in violations],
            }
        )

    if args.json:
        print(json.dumps({"ok": not failed, "version": VERSION, "files": results}, indent=2))
    else:
        for result in results:
            if result["violations"]:
                for item in result["violations"]:
                    print("FAIL: %s:%d: %s" % (result["file"], item["line"], item["message"]))
            else:
                print(
                    "status-lint: OK (%s: %d tables, %d rows)"
                    % (result["file"], result["tables"], result["rows"])
                )
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
