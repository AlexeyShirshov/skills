"""Docs "claim → source" maps: section anchors must resolve, line numbers only in the preamble.

The articles cite skill files as `opencode/<skill>/SKILL.md §Heading` (or
`§A · §B`) instead of line ranges, so edits to a skill do not silently rot the
maps.  A numeric reference is allowed only for the short file preamble (before
the first `##` heading), where there is no section to name.

Run:
    python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DOCS = [
    p
    for p in sorted(REPO.glob("docs/**/*.md"))
    if "pdca-slides" not in p.parts and "dist" not in p.parts
]

CITATION = re.compile(r"`(opencode/[a-z-]+/SKILL\.md)([^`]*)`")
NUMBERS = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")


def headings(skill: Path) -> list[tuple[int, str]]:
    """(line, text) for every `##`/`###` heading, backticks stripped."""
    out: list[tuple[int, str]] = []
    for number, line in enumerate(skill.read_text(encoding="utf-8").splitlines(), 1):
        match = re.match(r"^(#{2,3})\s+(.*)$", line)
        if match:
            out.append((number, match.group(2).replace("`", "").strip()))
    return out


class DocsSourceMapTest(unittest.TestCase):
    def test_citations_are_sections_or_preamble_lines(self) -> None:
        problems: list[str] = []
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            for citation in CITATION.finditer(text):
                skill_name, tail = citation.group(1), citation.group(2).strip()
                skill = REPO / skill_name
                if not skill.is_file():
                    problems.append(f"{doc}: missing file {skill_name}")
                    continue
                anchors, numbers = self._split(tail, doc, skill_name, problems)
                known = {name for _, name in headings(skill)}
                for anchor in anchors:
                    if anchor not in known:
                        problems.append(
                            f"{doc}: {skill_name} has no section §{anchor!r}"
                        )
                if numbers:
                    first = headings(skill)
                    limit = first[0][0] if first else 10**9
                    for part in numbers.split(","):
                        start = int(part.split("-")[0])
                        if start >= limit:
                            problems.append(
                                f"{doc}: {skill_name}:{part} is past the preamble — "
                                f"cite the section instead"
                            )
        self.assertEqual([], problems, "\n".join(problems))

    @staticmethod
    def _split(
        tail: str, doc: Path, skill_name: str, problems: list[str]
    ) -> tuple[list[str], str]:
        """` §A · §B, :22-28` → (["A", "B"], "22-28")."""
        numbers = ""
        body = tail
        if ", :" in body:
            body, numbers = body.rsplit(", :", 1)
        elif body.startswith(":"):
            numbers, body = body[1:], ""
        if body and not body.startswith("§"):
            problems.append(f"{doc}: unparsable citation {skill_name}{tail!r}")
            return [], numbers
        anchors = [part.lstrip("§").strip() for part in body.split(" · ")] if body else []
        if numbers and not NUMBERS.match(numbers):
            problems.append(f"{doc}: unparsable line range {skill_name}:{numbers}")
        return anchors, numbers


if __name__ == "__main__":
    unittest.main()
