"""Docs "claim → source" maps: section anchors must resolve, line numbers only in the preamble.

The articles cite skill files as `skills/<skill>/SKILL.md §Heading` (or `§A · §B`) instead of
line ranges, so edits to a skill do not silently rot the maps.  A numeric reference is
allowed only for the short file preamble (before the first `##` heading), where there is no
section to name.

Two scopes are deliberate:

* **dated design records** under `docs/superpowers/{specs,plans}/` describe a moment in time
  (they legitimately cite a skill that has since been deleted) and are not claims about the
  current tree;
* the **architecture facts** asserted here are only the stable ones — single entry, forms,
  overlays/specialized skills, the mandatory-requirement veto and the step boundary — because the
  articles are rewritten in a separate stream.  Everything else is covered by the contract guards,
  not by prose snapshots.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARCHIVE = ("docs/superpowers/specs/", "docs/superpowers/plans/")


def in_scope(path: Path) -> bool:
    rel = path.relative_to(REPO).as_posix()
    return (
        "pdca-slides" not in path.parts
        and "dist" not in path.parts
        and not rel.startswith(ARCHIVE)
    )


DOCS = [p for p in sorted(REPO.glob("docs/**/*.md")) if in_scope(p)]

CITATION = re.compile(r"`(skills/[a-z-]+/SKILL\.md)([^`]*)`")
NUMBERS = re.compile(r"^\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*$")

# A bare `> 2` / `>= 2` / `≥ 2` depth value is not proof that the host supports the
# delegation chain: the claim must be replaced by a verification-status statement.
DEPTH_CLAIM = re.compile(r"[>≥]=?\s*2")
DEPTH_MARKERS = re.compile(r"subagent_depth|глубин", re.I)
INSTALL_FILES = ("docs/install.md", "docs/ru/install.md", "docs/install-prompt.md")
VERIFICATION_STATUS = {
    "docs/install.md": ("verification status", "unverified"),
    "docs/install-prompt.md": ("verification status", "unverified"),
    "docs/ru/install.md": ("не проверен", "prerequisite", "невыполнен", "verification status"),
}
ARTICLE_PAIRS = (
    ("docs/pdca-collection.md", "docs/ru/pdca-collection.md"),
    ("docs/pdca-guide.md", "docs/ru/pdca-guide.md"),
    ("docs/pdca-incremental.md", "docs/ru/pdca-incremental.md"),
    ("docs/install.md", "docs/ru/install.md"),
)

# The stable architecture facts of the family, per article: the entry article and the
# README must state them; the step boundary is asserted where it is *the* subject.
ARCHITECTURE_FACTS = {
    "docs/pdca.md": ("only entry", "form", "incremental campaign", "overlay",
                     "specialized skill", "STOP is an **act outcome**"),
    "docs/ru/pdca.md": ("единственный вход", "форма", "инкрементальная", "оверлей",
                        "специализированный скилл"),
    "README.md": ("only entry", "overlay", "specialized skill"),
    "docs/pdca-incremental.md": ("step boundary", "§Step boundary"),
    "docs/ru/pdca-incremental.md": ("§Step boundary",),
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


def headings(skill: Path) -> list[tuple[int, str]]:
    """(line, text) for every `##`/`###` heading, backticks stripped."""
    out: list[tuple[int, str]] = []
    for number, line in enumerate(skill.read_text(encoding="utf-8").splitlines(), 1):
        match = re.match(r"^(#{2,4})\s+(.*)$", line)
        if match:
            out.append((number, match.group(2).replace("`", "").strip()))
    return out


class DocsSourceMapTest(unittest.TestCase):
    def test_every_citation_resolves_to_a_section_or_a_preamble_line(self) -> None:
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
                        problems.append(f"{doc}: {skill_name} has no section §{anchor!r}")
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
    def _split(tail: str, doc: Path, skill_name: str, problems: list[str]) -> tuple[list[str], str]:
        """` §A · §B`, `:22-28` or `:8-9 · §A` → (anchors, numbers).

        Both shapes are legitimate: a preamble line range with no section to name, and a
        range *plus* the section that now carries the rule.
        """
        numbers = ""
        body = tail
        if body.startswith(":"):
            after = body[1:]
            numbers, _, rest = after.partition(" · ")
            body = rest.strip()
        elif ", :" in body:
            body, numbers = body.rsplit(", :", 1)
        if body and not body.startswith("§"):
            problems.append(f"{doc}: unparsable citation {skill_name}{tail!r}")
            return [], numbers
        anchors = [part.lstrip("§").strip() for part in body.split(" · ")] if body else []
        if numbers and not NUMBERS.match(numbers):
            problems.append(f"{doc}: unparsable line range {skill_name}:{numbers}")
        return anchors, numbers

    def test_the_map_is_not_empty(self) -> None:
        # A resolver over zero citations would pass silently.
        total = sum(len(CITATION.findall(d.read_text(encoding="utf-8"))) for d in DOCS)
        self.assertGreater(total, 100, "the articles must keep citing the contracts")


class ArchitectureFactsTest(unittest.TestCase):
    """The articles carry the stable architecture facts, not only the anchors."""

    def test_articles_state_the_architecture(self) -> None:
        for rel, anchors in ARCHITECTURE_FACTS.items():
            text = read(REPO / rel).lower()
            for anchor in anchors:
                with self.subTest(doc=rel, anchor=anchor):
                    self.assertIn(anchor.lower(), text)

    def test_no_article_still_routes_through_pdca_entry(self) -> None:
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            with self.subTest(doc=str(doc.relative_to(REPO))):
                self.assertNotIn("pdca-entry", text)
                self.assertNotIn("selected_variant", text)


class CompositionDocsTest(unittest.TestCase):
    """Composition is documented in both languages and install claims stay honest."""

    def test_incremental_article_exists_in_both_languages(self) -> None:
        for rel in ("docs/pdca-incremental.md", "docs/ru/pdca-incremental.md"):
            with self.subTest(doc=rel):
                self.assertTrue((REPO / rel).is_file(), "%s missing" % rel)

    def test_article_pairs_exist(self) -> None:
        for en, ru in ARTICLE_PAIRS:
            with self.subTest(pair=en):
                self.assertTrue((REPO / en).is_file(), "%s missing" % en)
                self.assertTrue((REPO / ru).is_file(), "%s missing" % ru)

    def test_readme_says_a_collection_may_contain_a_campaign(self) -> None:
        sentences = [
            s for s in re.split(r"(?<=[.!?])\s+", norm(read(REPO / "README.md")))
            if re.search(r"\bcollections?\b", s, re.I)
            and re.search(r"\bcampaigns?\b", s, re.I)
        ]
        self.assertTrue(sentences,
                        "README must say that a collection may contain campaign units")

    def test_install_docs_do_not_claim_a_bare_depth_is_enough(self) -> None:
        problems: list[str] = []
        for rel in INSTALL_FILES:
            text = read(REPO / rel)
            for marker in DEPTH_MARKERS.finditer(text):
                window = text[max(0, marker.start() - 120):marker.end() + 120]
                if DEPTH_CLAIM.search(window):
                    line = text.count("\n", 0, marker.start()) + 1
                    problems.append("%s:%d treats a bare depth value as sufficient" % (rel, line))
        self.assertEqual([], problems, "\n".join(problems))

    def test_install_docs_state_verification_status(self) -> None:
        for rel, tokens in VERIFICATION_STATUS.items():
            with self.subTest(doc=rel):
                low = read(REPO / rel).lower()
                self.assertTrue(any(token in low for token in tokens),
                                "%s must state its verification status/prerequisite" % rel)


class OverlayDocsTest(unittest.TestCase):
    """The two overlays are documented as overlays — the copy model is gone."""

    PAIRS = (
        "docs/pdca-coder.md", "docs/ru/pdca-coder.md",
        "docs/pdca-dotnet.md", "docs/ru/pdca-dotnet.md",
    )

    def test_overlay_articles_state_inheritance(self) -> None:
        for rel in self.PAIRS:
            text = norm(read(REPO / rel)).lower()
            with self.subTest(doc=rel):
                self.assertTrue(
                    "overlay" in text or "оверлей" in text,
                    "the article must present the skill as an overlay",
                )
                self.assertNotIn("pdca-entry", text)

    def test_dotnet_article_names_the_coder_inheritance(self) -> None:
        for rel in ("docs/pdca-dotnet.md", "docs/ru/pdca-dotnet.md"):
            text = norm(read(REPO / rel)).lower()
            with self.subTest(doc=rel):
                self.assertIn("pdca-coder", text)


if __name__ == "__main__":
    unittest.main()
