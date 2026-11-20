"""Artifact checks for the behavioral probes of ``pdca-collection``.

The probes run a real agent session in an isolated sandbox and then judge the
*artifacts* (the collection status file, the preparation document, git state) —
never the agent's own summary. This module is the offline half: pure functions
over recorded text/files, so it can be unit-tested without a model.

Design rules:

* Checks describe contract invariants, not model wording. Status-file prose is
  parsed only where the contract fixes a machine-readable field (unit tables,
  group tables); everywhere else the filesystem state is authoritative.
* A failed check is a string, so a probe can report several at once.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

DASHES = {"", "—", "-", "–", "n/a", "none"}


# --------------------------------------------------------------------------- #
# Markdown tables
# --------------------------------------------------------------------------- #

def _cells(line: str) -> list[str]:
    return [cell.strip().strip("`").strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(set(cell) <= set("-: ") and cell for cell in cells)


def _all_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    tables: list[tuple[list[str], list[list[str]]]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        header = [cell.lower() for cell in _cells(lines[index])]
        rows: list[list[str]] = []
        index += 1
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            cells = _cells(lines[index])
            if not _is_separator(cells):
                rows.append(cells)
            index += 1
        tables.append((header, rows))
    return tables


def _table_after(lines: list[str], required_header: str) -> tuple[list[str], list[list[str]]]:
    """Return ``(header, rows)`` of the first table whose header names ``required_header``."""
    for header, rows in _all_tables("\n".join(lines)):
        if required_header in header:
            return header, rows
    return [], []


def _records(header: list[str], rows: list[list[str]]) -> list[dict[str, str]]:
    records = []
    for row in rows:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        records.append({name: row[i] for i, name in enumerate(header)})
    return records


def units(status_text: str) -> dict[str, dict[str, str]]:
    """Per-unit records keyed by the first cell, merged across the unit tables.

    A status file may describe a unit in more than one table (e.g. an ``Input units``
    table with the brief and a ``Units`` table with the state fields). Records are
    merged by unit id; a non-empty value never gets overwritten by an empty one.
    """
    out: dict[str, dict[str, str]] = {}
    state_fields = {"form", "plan_state", "preparation_state", "preparation_ref"}
    for header, rows in _all_tables(status_text):
        keys = [name.lower() for name in header]
        if not state_fields & set(keys):
            continue
        for row, record in zip(rows, _records(header, rows)):
            if not row or not row[0]:
                continue
            bucket = out.setdefault(row[0], {})
            for key, value in record.items():
                current = (bucket.get(key) or "").strip()
                if not current or current.lower() in DASHES:
                    if (value or "").strip():
                        bucket[key] = value
    return out


def groups(status_text: str) -> list[dict[str, str]]:
    header, rows = _table_after(status_text.splitlines(), "group")
    return _records(header, rows)


def task_statuses(status_text: str) -> dict[str, str]:
    """Execution status per unit id, from any table that records cycle state.

    Recorded runs use two shapes: a units table with a `status` column, or a separate
    tasks table with `status` + `plan_state`. Both are accepted.
    """
    out: dict[str, str] = {}
    for header, rows in _all_tables(status_text):
        keys = [name.lower() for name in header]
        if "plan_state" not in keys and "form" not in keys:
            continue
        status_key = next(
            (name for name in keys if name == "status" or name.endswith(" status")),
            None,
        )
        if status_key is None:
            continue
        for row, record in zip(rows, _records(header, rows)):
            if not row or not row[0]:
                continue
            value = (record.get(status_key) or "").strip().lower()
            if value:
                out.setdefault(row[0], value)
    return out


def is_unset(value: str) -> bool:
    lowered = (value or "").strip().lower()
    # The legacy RU status wording is still tolerated: a cell written before the
    # contract became English must read as "unset" too (the escape keeps this file ASCII).
    return (
        lowered in DASHES
        or "not allocated" in lowered
        or "\u043d\u0435 \u0430\u043b\u043b\u043e\u0446\u0438\u0440\u043e\u0432\u0430\u043d" in lowered
    )


_BARRIER_VERDICT = re.compile(r"all-barrier[^\n:]*:\s*\**\s*(pass|fail)\b", re.IGNORECASE)


def barrier_passed(status_text: str) -> bool | None:
    """``True``/``False`` from the explicit verdict line, ``None`` when unstated.

    Only a ``…: PASS`` / ``…: FAIL`` line counts — prose ("the barrier failed,
    so …") must not override the recorded verdict.
    """
    verdicts = [match.group(1).lower() for match in _BARRIER_VERDICT.finditer(status_text)]
    if not verdicts:
        return None
    if "fail" in verdicts:
        return False
    return True


# --------------------------------------------------------------------------- #
# Filesystem / git
# --------------------------------------------------------------------------- #

def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def branches(repo: Path) -> list[str]:
    if not (repo / ".git").exists():
        return []
    return [line.strip() for line in git(repo, "branch", "--format=%(refname:short)").splitlines() if line.strip()]


def collection_branches(repo: Path) -> list[str]:
    return [branch for branch in branches(repo) if branch.startswith("collection/")]


def has_worktrees(repo: Path) -> bool:
    candidates = [
        Path(str(repo) + "-worktrees"),
        repo.parent / f"{repo.name}-worktrees",
    ]
    return any(path.exists() for path in candidates)


def tracked_hashes(repo: Path) -> dict[str, str]:
    """Hash of every tracked file — proves the product was not touched."""
    hashes: dict[str, str] = {}
    for name in git(repo, "ls-files").splitlines():
        path = repo / name
        if path.is_file():
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def untracked(repo: Path) -> list[str]:
    out = git(repo, "status", "--porcelain")
    return [line[3:] for line in out.splitlines() if line.startswith("??")]


def find_status_file(repo: Path) -> Path | None:
    matches = sorted((repo / ".pdca" / "status").glob("collection-*.md"))
    return matches[0] if matches else None


def find_preparation(repo: Path) -> Path | None:
    matches = sorted((repo / ".pdca").glob("**/items/*/preparation.md"))
    return matches[0] if matches else None


def runtime_status_files(repo: Path) -> list[Path]:
    """Campaign runtime status / baseline evidence that must not exist at the barrier."""
    pdca = repo / ".pdca"
    if not pdca.exists():
        return []
    runtime = [path for path in pdca.rglob("*.json")]
    evidence = [path for path in pdca.rglob("evidence/*")]
    return runtime + evidence


# --------------------------------------------------------------------------- #
# Probe verdicts
# --------------------------------------------------------------------------- #

def _fs_guards(repo: Path | None, before: dict[str, str] | None) -> list[str]:
    """Shared filesystem invariants: no lanes, no branches, product untouched."""
    if repo is None:
        return []
    failures: list[str] = []
    if collection_branches(repo):
        failures.append(f"collection/* branches were created: {collection_branches(repo)}")
    if has_worktrees(repo):
        failures.append("a worktree directory was allocated next to the repo")
    if before is not None:
        after = tracked_hashes(repo)
        changed = sorted(name for name, digest in after.items() if before.get(name) != digest)
        if changed:
            failures.append(f"product files changed before DO: {changed}")
    return failures


def check_gap_probe(
    status_text: str,
    repo: Path | None = None,
    before: dict[str, str] | None = None,
    gap_unit: str = "T2",
) -> list[str]:
    """A unit with an impossible plan must stay a gap and stop the whole start."""
    failures: list[str] = []
    parsed = units(status_text)
    if gap_unit not in parsed:
        return [f"unit {gap_unit} missing from the units table"]
    record = parsed[gap_unit]
    plan_state = (record.get("plan_state") or "").strip().lower()
    preparation_state = (record.get("preparation_state") or "").strip().lower()
    if gap_unit and plan_state == "ready" and preparation_state in ("", "n/a", "—", "-"):
        failures.append(
            f"{gap_unit} is marked plan_state=ready instead of staying a gap"
        )
    if preparation_state == "ready":
        failures.append(
            f"{gap_unit} received a ready placeholder (preparation_state=ready) "
            "although its acceptance inputs were never supplied"
        )
    if (record.get("preparation_ref") or "").strip() not in DASHES and preparation_state != "ready":
        failures.append(
            f"{gap_unit} carries a preparation_ref without preparation_state=ready"
        )

    for group in groups(status_text):
        worktree = group.get("worktree", "")
        ref = group.get("branch/ref", "")
        if not is_unset(worktree) or not is_unset(ref):
            failures.append(
                f"group {group.get('group', '?')} was allocated despite the open barrier: "
                f"worktree={worktree!r} ref={ref!r}"
            )
    if barrier_passed(status_text) is True:
        failures.append("the ALL-barrier is reported as passed although a unit is a gap")

    failures.extend(_fs_guards(repo, before))
    return failures


# The mandatory content of the immutable preparation document
# (``../../references/status.md`` in ``pdca-incremental`` -> §Preparation document).
# Matched as content stems, not as numbered headings: the old nine-point charter is
# gone, the blocks below are what the document must still carry.
_PREPARATION_BLOCKS = (
    ("goal predicate", re.compile(r"(?i)goal predicate|goal:", re.I)),
    ("measurement recipe", re.compile(r"(?i)\brecipe\b")),
    ("increment unit", re.compile(r"(?i)increment unit", re.I)),
    ("floor and target", re.compile(r"(?i)\bfloor\b.*\btarget\b|\btarget\b.*\bfloor\b", re.S)),
    ("allowed surface", re.compile(r"(?i)allowed surface|reserved surface", re.I)),
    ("protected/foreign areas", re.compile(r"(?i)protected/foreign|foreign", re.I)),
    ("first-step candidate list", re.compile(r"(?i)candidate list", re.I)),
    ("criteria", re.compile(r"(?i)\bcriteria\b", re.I)),
    ("definition of done", re.compile(r"(?i)definition of done", re.I)),
    ("effort accounting", re.compile(r"(?i)^effort accounting:", re.M)),
    ("commit policy", re.compile(r"(?i)commit_policy|commit policy", re.I)),
    ("preparation_state", re.compile(r"(?i)preparation_state", re.I)),
    ("preparation_ref", re.compile(r"(?i)preparation_ref", re.I)),
)


def preparation_frame_failures(text: str) -> list[str]:
    """The mandatory preparation blocks present, and no post-barrier runtime status."""
    failures: list[str] = []
    for label, pattern in _PREPARATION_BLOCKS:
        if not pattern.search(text):
            failures.append(f"preparation document lacks the {label} block")
    if "status: `running`" in text.lower():
        failures.append(
            "preparation document already carries the post-barrier runtime status "
            "('Status: `running`')"
        )
    return failures


def check_campaign_probe(
    status_text: str,
    preparation_text: str | None,
    repo: Path | None = None,
    before: dict[str, str] | None = None,
    campaign_unit: str = "U1",
) -> list[str]:
    """A campaign item joins the batch in phase P as a prepared charter, not a step."""
    failures: list[str] = []
    parsed = units(status_text)
    if campaign_unit not in parsed:
        return [f"unit {campaign_unit} missing from the units table"]
    record = parsed[campaign_unit]
    if (record.get("form") or "").strip().lower() != "campaign":
        failures.append(
            f"{campaign_unit} was classified as {record.get('form')!r}, "
            "not as a campaign"
        )
    if (record.get("preparation_state") or "").strip().lower() != "ready":
        failures.append(f"{campaign_unit} preparation_state is not ready")
    if is_unset(record.get("preparation_ref", "")):
        failures.append(f"{campaign_unit} has no preparation_ref")
    item_contract = (
        record.get("contract")
        or record.get("contract+overlay")
        or record.get("overlay")
        or record.get("variant")
        or ""
    ).strip()
    if item_contract.lower() not in DASHES and "step" not in item_contract.lower():
        failures.append(
            f"{campaign_unit} carries an item-level contract/overlay ({item_contract!r}), "
            "which a campaign must not have"
        )

    if preparation_text is None:
        failures.append("preparation document not found")
    else:
        failures.extend(preparation_frame_failures(preparation_text))

    if repo is not None:
        leftover = runtime_status_files(repo)
        if leftover:
            failures.append(
                "post-barrier state was created too early: "
                + ", ".join(str(path.relative_to(repo)) for path in leftover)
            )
    failures.extend(_fs_guards(repo, before))
    return failures


def read_text(path: Path | None) -> str | None:
    return path.read_text(encoding="utf-8") if path is not None else None


def dump_result(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
