#!/usr/bin/env python3
"""Emit and verify the verbatim rule inventory of the base `pdca` skill.

The inventory is a **projection**, never a second source of truth: every table row is one
sentence copied from ``skills/pdca/SKILL.md``, in the order it appears, with its line range.
The document keeps the generated block between two markers, and ``--check`` compares that
block with a fresh extraction, so a contract edit cannot leave the inventory silently stale.

Each row also carries **practice** from ``skills/pdca/assets/rule-evidence.json``: a documented
incident (``источник``) or a counterfactual (``контрфакт``). Entries are keyed by the sha1 of the
rule text, not by ``R-NNN``: a reworded rule loses its practice and ``--check`` fails until the
evidence is reviewed. Citations must be durable — a commit, an in-repo **git-tracked** file, or a
``nextorm:`` status record; an untracked run artefact is rejected.

Usage::

    python3 skills/pdca/scripts/skill_rule_inventory.py            # check (default)
    python3 skills/pdca/scripts/skill_rule_inventory.py --check
    python3 skills/pdca/scripts/skill_rule_inventory.py --fix

Exit codes: 0 = inventory matches, 1 = drifted / markers missing, 2 = usage or IO error.
Output carries no timestamps and no absolute paths, so it is stable in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "skills/pdca/SKILL.md"
DOC = REPO / "docs/ru/pdca-rules.md"
EVIDENCE = REPO / "skills/pdca/assets/rule-evidence.json"
BEGIN = "<!-- rules:begin -->"
END = "<!-- rules:end -->"

KINDS = {"src": "источник", "cf": "контрфакт", "both": "источник"}

ABBREV = ("e.g.", "i.e.", "cf.", "vs.", "no.", "Nos.", "Art.", "Fig.", "etc.", "approx.",
          "resp.", "incl.", "Ref.", "Sec.")


def _scrub_frontmatter(lines: list[str]) -> tuple[list[str], int]:
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1:], i + 1
    return lines, 0


def _blocks(lines: list[str]):
    """(kind, section, [(lineno, text)]) — kind in para|bullet|table|code."""
    blocks: list[tuple[str, tuple[int, str], list[tuple[int, str]]]] = []
    section: tuple[int, str] = (1, "(preamble)")
    buf: list[tuple[int, str]] = []
    kind: str | None = None
    in_code = False

    def flush() -> None:
        nonlocal buf, kind
        if buf:
            blocks.append((kind or "para", section, buf))
        buf, kind = [], None

    for idx, raw in enumerate(lines):
        lineno = idx + 1
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                blocks.append(("code", section, buf))
                buf, kind, in_code = [], None, False
            else:
                flush()
                in_code, kind = True, "code"
            continue
        if in_code:
            buf.append((lineno, line))
            continue

        if not stripped:
            flush()
            continue
        if stripped.startswith("#"):
            flush()
            level = len(stripped) - len(stripped.lstrip("#"))
            section = (level, stripped.lstrip("#").strip())
            continue
        if stripped.startswith("|"):
            flush()
            if not set(stripped) <= set("|-: "):
                blocks.append(("table", section, [(lineno, stripped)]))
            continue
        if re.match(r"^(\s*)([-*]|\d+[a-z]?\.)\s+", line):
            flush()
            kind = "bullet"
            buf.append((lineno, line))
            continue
        kind = kind or "para"
        buf.append((lineno, line))
    flush()
    return blocks


def _join(block: list[tuple[int, str]]) -> tuple[str, list[int]]:
    """Join wrapped lines; return the text and the source line of every character."""
    text: list[str] = []
    linemap: list[int] = []
    for j, (lineno, line) in enumerate(block):
        stripped = line.strip()
        if j == 0:
            stripped = re.sub(r"^([-*]|\d+[a-z]?\.)\s+", "", stripped)
        else:
            glue = "" if text and text[-1].endswith(("/", "-")) else " "
            if glue:
                text.append(glue)
                linemap.append(linemap[-1] if linemap else lineno)
        text.append(stripped)
        linemap.extend([lineno] * len(stripped))
    return "".join(text), linemap


def _sentences(text: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    start = 0
    for i, ch in enumerate(text):
        if ch not in ".?!":
            continue
        nxt = text[i + 1:i + 2]
        if nxt and nxt not in " \n":
            continue
        if any(text[:i + 1].endswith(a) for a in ABBREV):
            continue
        if ch == "." and i + 1 < len(text) and text[i + 1].isdigit():
            continue
        if not re.match(r"\s+([A-Za-zА-Яа-яЁё(`*\"«])", text[i + 1:]):
            continue
        out.append((start, i))
        start = i + 1
    if text[start:].strip():
        out.append((start, len(text) - 1))
    return out


def _cell(text: str) -> str:
    return text.replace("|", "\\|").strip()


def _section_heading(section: tuple[int, str]) -> str:
    level, title = section
    if level <= 1:
        return "### §Вступление (h1 скилла)"
    return "%s §%s" % ("#" * (level + 1), title)


def _sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def load_evidence() -> dict[str, dict]:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise ValueError("unsupported evidence schema: %r" % (data.get("schema"),))
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise ValueError("evidence entries must be an object")
    return entries


def _tracked(path: str) -> bool:
    """A citation must survive the working tree: only git-tracked files are durable."""
    try:
        done = subprocess.run(["git", "-C", str(REPO), "ls-files", "--error-unmatch", path],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return done.returncode == 0


def _ref_problem(ref: str) -> str | None:
    """None if the citation is well-formed and, for in-repo paths, durable."""
    if not ref:
        return None
    if ref.startswith("nextorm:"):
        path = ref[len("nextorm:"):].split(":", 1)[0]
        if not path.startswith("docs/"):
            return "external citation must point into docs/: %s" % ref
        return None
    if ref.startswith("commit:"):
        sha = ref.split(":", 1)[1]
        if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
            return "bad commit sha: %s" % ref
        return None
    path = ref.split(":", 1)[0]
    if not path or path.startswith("/"):
        return "internal citation must be repo-relative: %s" % ref
    if not (REPO / path).is_file():
        return "cited path does not exist: %s" % ref
    if not _tracked(path):
        return "cited path is not tracked (a local run artefact is not durable): %s" % ref
    return None


def practice_cell(entry: dict | None) -> str:
    if entry is None:
        return "**нет подтверждения**"
    kind = entry.get("kind")
    if kind not in KINDS:
        return "**неверный вид: %r**" % (kind,)
    text = _cell(entry.get("practice", ""))
    ref = entry.get("ref", "")
    label = KINDS[kind]
    body = "%s: %s" % (label, text)
    if ref:
        body += " `%s`" % ref
    return body


def render(source: Path, entries: dict[str, dict] | None = None,
           problems: list[str] | None = None,
           used: set[str] | None = None) -> str:
    """The generated block, without the markers."""
    if entries is None:
        entries = load_evidence()
    raw = source.read_text(encoding="utf-8").splitlines()
    lines, offset = _scrub_frontmatter(raw)
    rows: list[tuple[tuple[int, str], str, int, int, str]] = []
    for kind, section, block in _blocks(lines):
        block = [(n + offset, t) for n, t in block]
        if kind == "code":
            code_lines = [(n, t) for n, t in block if not t.strip().startswith("```")]
            if code_lines:
                rows.append((section, "код", code_lines[0][0], code_lines[-1][0],
                             "<br>".join(_cell(t) for _, t in code_lines)))
            continue
        text, linemap = _join(block)
        if kind == "table":
            rows.append((section, "табл", block[0][0], block[0][0], _cell(text)))
            continue
        label = "пункт" if kind == "bullet" else "абз"
        for a, b in _sentences(text):
            chunk = text[a:b + 1].strip()
            if not chunk:
                continue
            lo = linemap[a]
            hi = linemap[min(b, len(linemap) - 1)]
            rows.append((section, label, lo, hi, _cell(chunk)))

    blank = sum(1 for line in lines if not line.strip())
    headings = sum(1 for line in lines if line.strip().startswith("#"))
    table_rows = sum(1 for line in lines if line.strip().startswith("|")
                     and not set(line.strip()) <= set("|-: "))
    table_sep = sum(1 for line in lines if line.strip().startswith("|")
                    and set(line.strip()) <= set("|-: "))
    fences = sum(1 for line in lines if line.strip().startswith("```"))
    prose = len(lines) - blank - headings - table_rows - table_sep - fences
    sentences = sum(1 for row in rows if row[1] in ("абз", "пункт"))
    table_cells = sum(1 for row in rows if row[1] == "табл")
    code_blocks = sum(1 for row in rows if row[1] == "код")

    out = ["### Состав источника", "", "| Что | Количество |", "|---|---:|",
           "| Всего строк в `SKILL.md` | %d |" % len(raw),
           "| Служебные (frontmatter) | %d |" % offset,
           "| Пустые | %d |" % blank,
           "| Заголовки | %d |" % headings,
           "| Строки исходных таблиц (плюс %d разделител%s) | %d + %d |"
           % (table_sep, "ь" if table_sep == 1 else "я", table_rows, table_sep),
           "| Ограды блоков кода | %d |" % fences,
           "| Строки прозы | %d |" % prose,
           "| **Предложений в прозе** | **%d** |" % sentences,
           "| Строк исходных таблиц в инвентаре | %d |" % table_cells,
           "| Блоков кода в инвентаре | %d |" % code_blocks,
           "| **Строк в инвентаре** | **%d** |" % len(rows),
           "| С источником (документированный случай) | %d |" % sum(
               1 for row in rows if entries.get(_sha(row[4]), {}).get("ref")),
           "| С контрфактом | %d |" % sum(
               1 for row in rows if _sha(row[4]) in entries
               and not entries[_sha(row[4])].get("ref")),
           "| Без подтверждения | %d |" % sum(
               1 for row in rows if _sha(row[4]) not in entries)]

    current: tuple[int, str] | None = None
    for number, (section, kind, lo, hi, text) in enumerate(rows, 1):
        if section != current:
            current = section
            out += ["", _section_heading(section), "",
                    "| ID | Строка | Вид | Правило (verbatim) | Практика (источник или контрфакт) |",
                    "|---|---|---|---|---|"]
        loc = str(lo) if lo == hi else "%d–%d" % (lo, hi)
        entry = entries.get(_sha(text))
        if used is not None:
            used.add(_sha(text))
        if entry is None and problems is not None:
            problems.append("R-%03d: no practice entry (sha1 %s): %s"
                            % (number, _sha(text), text[:70]))
        if entry is not None and problems is not None:
            if entry.get("kind") not in KINDS:
                problems.append("R-%03d: bad kind %r" % (number, entry.get("kind")))
            problem = _ref_problem(entry.get("ref", ""))
            if problem:
                problems.append("R-%03d: %s" % (number, problem))
            if not entry.get("practice", "").strip():
                problems.append("R-%03d: empty practice" % number)
        out.append("| R-%03d | %s | %s | %s | %s |"
                   % (number, loc, kind, text, practice_cell(entry)))
    return "\n".join(out).strip("\n") + "\n"


def extract(doc_text: str) -> str | None:
    if BEGIN not in doc_text or END not in doc_text:
        return None
    body = doc_text.split(BEGIN, 1)[1].split(END, 1)[0]
    return body.strip("\n") + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="verify the inventory (default)")
    group.add_argument("--fix", action="store_true", help="regenerate the inventory")
    args = parser.parse_args()

    for path in (SOURCE, DOC, EVIDENCE):
        if not path.is_file():
            print("error: missing %s" % path.relative_to(REPO), file=sys.stderr)
            return 2

    try:
        entries = load_evidence()
    except (ValueError, json.JSONDecodeError) as exc:
        print("error: %s: %s" % (EVIDENCE.relative_to(REPO), exc), file=sys.stderr)
        return 2

    problems: list[str] = []
    used: set[str] = set()
    fresh = render(SOURCE, entries, problems, used)
    for sha in sorted(set(entries) - used):
        problems.append("orphan evidence entry sha1 %s (id %s): no rule carries it"
                        % (sha[:12], entries[sha].get("id", "?")))
    doc = DOC.read_text(encoding="utf-8")
    current = extract(doc)
    if current is None:
        print("error: %s: markers %s / %s not found" % (DOC.relative_to(REPO), BEGIN, END),
              file=sys.stderr)
        return 2
    if args.fix:
        if current != fresh:
            DOC.write_text(doc.split(BEGIN, 1)[0] + BEGIN + "\n" + fresh + END
                           + doc.split(END, 1)[1], encoding="utf-8")
            print("fixed: %s" % DOC.relative_to(REPO))
        if problems:
            for problem in problems:
                print("error: %s" % problem, file=sys.stderr)
            return 1
        return 0
    if current != fresh:
        print("error: drift: %s does not match %s — run --fix"
              % (DOC.relative_to(REPO), SOURCE.relative_to(REPO)), file=sys.stderr)
        return 1
    if problems:
        for problem in problems:
            print("error: %s" % problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
