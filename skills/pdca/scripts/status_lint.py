#!/usr/bin/env python3
"""Static lint for a PDCA durable status file.

Reads the Markdown status file under ``.pdca/status/`` and answers one question: *is the durable
record machine-readable, complete for its stage and consistent with itself?*  It does not run the
cycle and does not judge whether the recorded conclusions are true — that stays with CHECK.

What it proves:

* the required sections exist (the plan core always; the closing sections once the cycle closes);
* the durable-state block carries every counter and a legal ``Status``/``Phase``;
* every claim ID named by the plan has a row in the carrying-claims table;
* every progress-log line matches the frozen shape
  ``<UTC> | <phase> | revision r<n> | iteration <n>/3 | <event> | <pointer>``; a leading list
  bullet is decoration and is tolerated;
* no event restates the number of this file's log lines (``9 log lines``): such a line goes stale
  with the next append, so the receipt carries the counts and the line carries the pointer.

A ``##`` heading inside a fenced block is body text, never a section: the plan document copied into
``## Plan`` carries its own headings, and none of them may shadow a required section.

The shape check is what catches a hand-edited log: ``iteration n=3``, ``revision 1``, a missing
pointer, a shell-escaped arrow left by ``sed``.

Usage::

    python3 .pdca/scripts/status_lint.py check --repo . --status .pdca/status/<task>-<N>.md \
        --receipt <evidence-dir>/status_lint.txt
    python3 .pdca/scripts/status_lint.py schema     # the durable-status shape, no file needed

Exit codes: ``0`` ok, ``2`` violation, ``1`` usage/IO — the same convention as ``plan_lint.py``.
Output carries no timestamps and no absolute paths, so it is stable in CI.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VERSION = 1

OPEN_SECTIONS = ("Plan", "Durable state", "Carrying claims", "Progress log")
CLOSED_SECTIONS = ("Done/Verified", "Next plan", "Changed artefacts")

STATUS_VALUES = {"pending", "in-progress", "blocked", "stopped", "done", "incomplete"}
PHASE_VALUES = {"PLAN", "DO", "CHECK", "ACT", "EXIT"}
TERMINAL_STATUS = {"done", "stopped", "blocked", "incomplete"}

# key aliases in the durable-state block, normalised (lowercase, single spaces)
STATE_KEYS = {
    "cycle": ("current cycle n", "cycle n", "cycle"),
    "revision": ("plan revision r", "revision r"),
    "attempt": ("attempt n", "attempt"),
    "rv": ("rv",),
    "form": ("form",),
    "overlay": ("overlay",),
    "mode": ("mode",),
    "status": ("status",),
    "phase": ("phase",),
}

LOG_LINE = re.compile(
    r"^(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \| "
    r"(?P<phase>[A-Z]+) \| "
    r"revision r=?(?P<revision>\d+) \| "
    r"iteration (?P<iteration>\d)/(?P<total>\d) \| "
    r"(?P<event>.+?) \| (?P<pointer>.+)$"
)
CLAIM_ID = re.compile(r"\b([A-Z]\d+)\b")
TABLE_ROW = re.compile(r"^\|\s*(?P<id>[A-Z]\d+)\s*\|(?P<rest>.*)\|$")
STATE_LINE = re.compile(r"^\s*[-*]\s*\**\s*(?P<key>[^:*|]+?)\s*\**\s*:\s*(?P<value>.+?)\s*$")
STATE_ROW = re.compile(r"^\|\s*(?P<key>[^|]+?)\s*\|\s*(?P<value>[^|]+?)\s*\|")
SHELL_ARROW = re.compile(r"\$\\(?:to|rightarrow|Rightarrow)\$|\\to\\")
# A count of the status file itself inside an event is stale by construction: the next append
# changes it.  The lint receipt carries the counts; the log line carries the pointer.
STALE_COUNTER = re.compile(r"\b\d+\s+log lines?\b", re.IGNORECASE)


class Violations:
    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []
        self.warnings: list[str] = []

    def add(self, where: str, code: str, message: str) -> None:
        self.items.append(("%s %s" % (code, where), message))

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def __bool__(self) -> bool:
        return bool(self.items)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


FENCE = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})(?P<info>.*)$")


def split_sections(text: str) -> dict[str, list[str]]:
    """Map ``## <Heading>`` -> body lines, keeping the heading order.

    Headings inside a fenced block are body text: the verbatim plan copy carries its own ``##``
    headings, and a section of the plan may never shadow a required section of the status.
    """
    sections: dict[str, list[str]] = {}
    current: str | None = None
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if marker:
            run = marker.group("marker")
            if fence is None:
                fence = (run[0], len(run))
            elif (run[0] == fence[0] and len(run) >= fence[1]
                  and not marker.group("info").strip()):
                fence = None
            if current is not None:
                sections[current].append(line)
            continue
        if fence is None:
            match = re.match(r"^##\s+(?P<title>.+?)\s*$", line)
            if match and not line.startswith("###"):
                current = match.group("title")
                sections.setdefault(current, [])
                continue
        if current is not None:
            sections[current].append(line)
    return sections


def find_section(sections: dict[str, list[str]], prefix: str) -> list[str] | None:
    for title, body in sections.items():
        if title == prefix or title.startswith(prefix + " ") or title.startswith(prefix + " —"):
            return body
    return None


def parse_state(body: list[str]) -> dict[str, str]:
    state: dict[str, str] = {}
    for raw in body:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = STATE_LINE.match(line) or STATE_ROW.match(line)
        if not match:
            continue
        key = re.sub(r"\s+", " ", match.group("key").strip().strip("*`")).lower()
        value = match.group("value").strip().strip("*`")
        for canonical, aliases in STATE_KEYS.items():
            if key in aliases and canonical not in state:
                state[canonical] = value
    return state


def lint(text: str, where: str) -> tuple[Violations, dict]:
    v = Violations()
    sections = split_sections(text)
    facts: dict = {"sections": sorted(sections), "claims": [], "log_lines": 0, "state": {}}

    state_body = find_section(sections, "Durable state")
    state = parse_state(state_body or [])
    facts["state"] = state

    # stage: closed once the cycle records a terminal status or EXIT
    phase = state.get("phase", "").upper()
    status = state.get("status", "").lower()
    closed = phase == "EXIT" or status in TERMINAL_STATUS

    required = list(OPEN_SECTIONS) + (list(CLOSED_SECTIONS) if closed else [])
    for name in required:
        if find_section(sections, name) is None:
            v.add(where, "S002", "missing required section `## %s`" % name)

    for canonical in ("cycle", "revision", "attempt", "rv", "form", "overlay", "mode", "status", "phase"):
        if canonical not in state:
            v.add(where, "S003", "durable state misses `%s`" % canonical)
        elif not state[canonical]:
            v.add(where, "S003", "durable state has an empty `%s`" % canonical)

    if status and status not in STATUS_VALUES:
        v.add(where, "S004", "`Status: %s` is not one of %s" % (status, ", ".join(sorted(STATUS_VALUES))))
    if phase and phase not in PHASE_VALUES:
        v.add(where, "S004", "`Phase: %s` is not one of %s" % (phase, ", ".join(sorted(PHASE_VALUES))))
    if phase == "EXIT" and status and status not in TERMINAL_STATUS:
        v.warn("`Phase: EXIT` with a non-terminal `Status: %s`" % status)

    # claims: plan mentions -> claims table rows
    claims_body = find_section(sections, "Carrying claims")
    rows: dict[str, str] = {}
    if claims_body is not None:
        for raw in claims_body:
            match = TABLE_ROW.match(raw.strip())
            if match:
                cells = [cell.strip() for cell in match.group("rest").split("|")]
                rows[match.group("id")] = " | ".join(cell for cell in cells if cell)
                if not rows[match.group("id")]:
                    v.add(where, "S005", "claim `%s` has an empty status" % match.group("id"))
    if not rows:
        v.add(where, "S005", "no claim rows in `## Carrying claims`")
    facts["claims"] = sorted(rows)

    plan_body = find_section(sections, "Plan") or []
    # only the prefixes the claims table itself uses count as claim IDs (S1/P1 are unit IDs)
    prefixes = {cid.rstrip("0123456789") for cid in rows} or {"C"}
    mentioned = {
        m.group(1)
        for line in plan_body
        for m in CLAIM_ID.finditer(line)
        if m.group(1).rstrip("0123456789") in prefixes
    }
    for cid in sorted(mentioned - set(rows)):
        v.add(where, "S005", "claim `%s` is named by the plan but has no claims row" % cid)

    # progress log shape
    log_body = find_section(sections, "Progress log")
    if log_body is not None:
        for offset, raw in enumerate(log_body, start=1):
            line = raw.rstrip()
            stripped = line.strip()
            if not stripped or FENCE.match(stripped) or stripped.startswith("#"):
                continue
            if " | " not in stripped:
                continue  # prose in the section is not a log line
            facts["log_lines"] += 1
            match = LOG_LINE.match(re.sub(r"^[-*]\s+", "", stripped))
            if not match:
                v.add(where, "S006", "progress-log line does not match the frozen shape: %r" % stripped[:120])
                continue
            if match.group("phase") not in PHASE_VALUES:
                v.add(where, "S006", "unknown log phase %r" % match.group("phase"))
            if match.group("total") != "3":
                v.add(where, "S006", "iteration denominator must be 3, got %r" % match.group("total"))
            elif match.group("iteration") not in ("1", "2", "3"):
                v.add(where, "S006", "iteration must be 1..3, got %r" % match.group("iteration"))
            stale = STALE_COUNTER.search(match.group("event"))
            if stale:
                v.add(where, "S007",
                      "progress-log event restates this file's own count (%r): it goes stale with the "
                      "next append — point at the STATUS-LINT receipt instead"
                      % stale.group(0))

    if SHELL_ARROW.search(text):
        v.warn("possible shell artefact: an escaped arrow (`$\\to$`) is left in the text")

    return v, facts


def schema_text() -> str:
    """The durable-status shape, derived from the constants the lint enforces."""
    order = ("cycle", "revision", "attempt", "rv", "form", "overlay", "mode", "status", "phase")
    lines = [
        "PDCA durable status shape (status_lint v%d)" % VERSION,
        "",
        "sections (open cycle): " + ", ".join("## %s" % s for s in OPEN_SECTIONS),
        "sections (closed cycle): " + ", ".join("## %s" % s for s in CLOSED_SECTIONS),
        "durable state keys: " + ", ".join(STATE_KEYS[key][0] for key in order),
        "status values: " + ", ".join(sorted(STATUS_VALUES)),
        "phase values: " + ", ".join(sorted(PHASE_VALUES)),
        "section match: a title equals the name or starts with `<name> ` / `<name> —`; a `##`",
        "  heading inside a fenced block is body text, not a section",
        "claims rows: `| <ID> | <claim> | <status> |`, ID = [A-Z]\\d+, one per claim ID the plan names",
        "progress log line (column 0; a leading `- ` bullet is tolerated):",
        "  <UTC> | <PHASE> | revision r<n> | iteration <n>/3 | <event> | <pointer>",
        "  <event> carries no count of this file's log lines: the receipt carries them",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static lint for a PDCA durable status file")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("schema", help="print the durable-status shape and exit")

    check = sub.add_parser("check", help="validate the status file")
    check.add_argument("--repo", default=".", help="binding checkout (default: cwd)")
    check.add_argument("--status", required=True, help="status file, repo-relative or absolute")
    check.add_argument("--receipt", help="write the receipt here")
    check.add_argument("--json", action="store_true", help="machine-readable result on stdout")

    args = parser.parse_args(argv)
    if args.command == "schema":
        sys.stdout.write(schema_text())
        return 0
    if args.command != "check":
        return 1

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print("error: --repo is not a directory: %s" % args.repo, file=sys.stderr)
        return 1

    status_path = Path(args.status)
    if not status_path.is_absolute():
        status_path = repo / status_path
    try:
        rel = status_path.resolve().relative_to(repo)
    except ValueError:
        rel = status_path
    try:
        text = _read(status_path)
    except OSError as exc:
        print("error: cannot read %s: %s" % (rel, exc.strerror or exc), file=sys.stderr)
        return 1
    if not text.strip():
        print("error: %s is empty" % rel, file=sys.stderr)
        return 1

    v, facts = lint(text, str(rel))
    state = facts["state"]
    summary = {
        "ok": not v,
        "status_file": str(rel),
        "sections": facts["sections"],
        "state": state,
        "claims": facts["claims"],
        "log_lines": facts["log_lines"],
        "violations": len(v.items),
        "warnings": len(v.warnings),
    }

    lines = [
        "status-lint v%d" % VERSION,
        "status: %s" % rel,
        "result: %s" % ("ok" if not v else "violation"),
        "sections: %d" % len(facts["sections"]),
        "state: %s" % " ".join(
            "%s=%s" % (key, state.get(key, "?"))
            for key in ("cycle", "revision", "attempt", "rv", "form", "overlay", "mode", "status", "phase")
        ),
        "claims: %d (%s)" % (len(facts["claims"]), ", ".join(facts["claims"]) or "-"),
        "log lines: %d" % facts["log_lines"],
        "violations: %d" % len(v.items),
        "warnings: %d" % len(v.warnings),
    ]
    for code, message in v.items:
        lines.append("  " + code + ": " + message)
    for warning in v.warnings:
        lines.append("  W: " + warning)
    receipt = "\n".join(lines) + "\n"

    if args.receipt:
        try:
            Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
            Path(args.receipt).write_text(receipt, encoding="utf-8")
        except OSError as exc:
            print("error: cannot write receipt: %s" % (exc.strerror or exc), file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps({**summary, "messages": [code + ": " + message for code, message in v.items],
                          "warning_messages": v.warnings}, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(receipt)

    return 2 if v else 0


if __name__ == "__main__":
    raise SystemExit(main())
