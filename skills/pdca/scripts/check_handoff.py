"""Materialize the CHECK dispatch from the installed skill and a cycle-owned brief."""
import argparse
from pathlib import Path
import re
import json
from report_ref import pin


BASE = Path(__file__).resolve().parents[1]


def section(path, heading):
    text = path.read_bytes()
    headings = list(re.finditer(rb"^(#{1,6}) (.+?)\r?$", text, re.M))
    hits = [i for i, h in enumerate(headings) if h[2].decode() == heading]
    if len(hits) != 1:
        raise ValueError(f"missing or ambiguous heading: {path.name}: {heading}")
    i = hits[0]
    end = next((h.start() for h in headings[i+1:] if len(h[1]) <= len(headings[i][1])), len(text))
    return text[headings[i].start():end]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("candidate", "retrospective"))
    p.add_argument("brief", type=Path, help="completed brief under the cycle evidence root")
    p.add_argument("--section", action="append", default=[], metavar="SKILL:HEADING")
    args = p.parse_args()
    brief = args.brief.resolve()
    root = Path.cwd() / ".pdca"
    if not brief.is_relative_to(root) or root.is_symlink():
        p.error("brief must be inside the workspace .pdca directory")
    parts = [(BASE / "references/check.md").read_bytes()]
    if args.mode == "retrospective":
        if args.section:
            p.error("retrospectives take no candidate overlay sections")
        parts.append(section(BASE / "references/act.md", "Retrospective (mandatory, ACT)"))
    for selector in args.section:
        skill, _, heading = selector.partition(":")
        if skill not in ("pdca-coder", "pdca-dotnet"):
            p.error(f"unknown overlay: {skill}")
        parts.append(section(BASE.parent / skill / "SKILL.md", heading))
    body = brief.read_bytes()
    if not body.strip():
        p.error("empty brief")
    parts += [b"## Cycle brief", f"mode: {args.mode}".encode(), body, b"<!-- end CHECK handoff -->\n"]
    # Publish the pointer only after every section has been resolved and written.
    print(json.dumps(pin(brief.parent, b"\n\n".join(parts), "check")))


if __name__ == "__main__":
    main()
