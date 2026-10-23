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

# A bare `> 2` / `>= 2` / `≥ 2` depth value is not proof that the host supports the
# delegation chain: the claim must be replaced by a verification-status statement.
DEPTH_CLAIM = re.compile(r"[>≥]=?\s*2")
DEPTH_MARKERS = re.compile(r"subagent_depth|глубин", re.I)
INSTALL_FILES = ("docs/install.md", "docs/ru/install.md", "docs/install-prompt.md")
ARTICLE_PAIRS = (
    ("docs/pdca-collection.md", "docs/ru/pdca-collection.md"),
    ("docs/pdca-guide.md", "docs/ru/pdca-guide.md"),
    ("docs/install.md", "docs/ru/install.md"),
)
VERIFICATION_STATUS = {
    "docs/install.md": ("verification status", "unverified"),
    "docs/install-prompt.md": ("verification status", "unverified"),
    "docs/ru/install.md": ("не проверен", "prerequisite", "невыполнен"),
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


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


class DocsFreshnessTest(unittest.TestCase):
    """The prose must carry the plan-close rules, not only cite their sections.

    Section anchors prove the map resolves; they do not prove the article still
    describes the contract.  These anchors are deliberately few and stable.
    """

    REQUIRED = {
        "docs/pdca.md": (
            "plan command contract", "stop-loss", "expected-negative",
            "One evidence location binding",
        ),
        "docs/ru/pdca.md": (
            "контракт команд", "stop-loss", "expected-negative",
            "Единая привязка доказательств",
        ),
        "docs/pdca-guide.md": (
            "plan-command validation receipt", "zero-target run",
            "Re-anchoring at DO entry",
        ),
        "docs/ru/pdca-guide.md": (
            "квитанция валидации команд", "ноль", "Re-anchor на входе",
        ),
        "docs/pdca-dotnet.md": ("PLAN-LINT", "commands.json"),
        "docs/ru/pdca-dotnet.md": ("PLAN-LINT", "commands.json"),
        "docs/ru/pdca-slides/slides.md": (
            "stop-loss", "Re-anchor", "expected-negative",
        ),
    }

    def test_articles_carry_the_plan_close_rules(self) -> None:
        for rel, anchors in self.REQUIRED.items():
            text = read(REPO / rel).lower()
            for anchor in anchors:
                with self.subTest(doc=rel, anchor=anchor):
                    self.assertIn(anchor.lower(), text)


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
        self.assertTrue(
            sentences,
            "README must say that a collection may contain campaign units",
        )

    def test_install_docs_do_not_claim_a_bare_depth_is_enough(self) -> None:
        problems: list[str] = []
        for rel in INSTALL_FILES:
            text = read(REPO / rel)
            for marker in DEPTH_MARKERS.finditer(text):
                window = text[max(0, marker.start() - 120):marker.end() + 120]
                if DEPTH_CLAIM.search(window):
                    line = text.count("\n", 0, marker.start()) + 1
                    problems.append(
                        "%s:%d treats a bare depth value as sufficient" % (rel, line)
                    )
        self.assertEqual([], problems, "\n".join(problems))

    def test_install_docs_state_verification_status(self) -> None:
        for rel, tokens in VERIFICATION_STATUS.items():
            with self.subTest(doc=rel):
                low = read(REPO / rel).lower()
                self.assertTrue(
                    any(token in low for token in tokens),
                    "%s must state its verification status/prerequisite" % rel,
                )


# AC16 post-hoc guard: the *new* composition sections of the contracts/runner must stay
# domain-agnostic.  Only composition-bearing headings are sliced (heading → next heading
# of the same level); the pre-existing variant-routing rows that name concrete stacks as
# contract inputs (e.g. `.NET/C#` → `pdca-dotnet`) are outside these slices by design.
COMPOSITION_SECTIONS = {
    "opencode/pdca-collection/SKILL.md": (
        ("###", "Collection units and the execution form"),
        ("###", "P — per-task PLANs, the barrier, clustering"),
        ("###", "Surface reservation and its extension"),
    ),
    "opencode/pdca-incremental/SKILL.md": (
        ("##", "Campaign invariants"),
        ("##", "Campaign status file"),
        ("###", "0. Bootstrap"),
    ),
    "opencode/pdca/assets/agents/pdca-orchestrator.md": (
        ("##", "Contract"),
        ("##", "Input 1"),
        ("##", "Input 2"),
        ("##", "Input 3"),
    ),
}
# The RU side of the composition documentation stays Russian by design (`docs/ru` is not
# translated), so the domain-neutral vocabulary is still checked in Russian there.
RU_COMPOSITION_SECTIONS = {
    "docs/ru/pdca-collection.md": (("##", "7. Композиция"),),
}
RU_VOCABULARY = ("цель", "свидетельств", "критери", "поверхност", "зависимост", "ресурс")
EN_VOCABULARY = ("goal", "evidence", "criteria", "surface", "dependencies", "resources")
DOMAIN_TOKENS = (".NET", "dotnet", "performance", "coverage", "NuGet", "ASP.NET")


def heading_slice(text: str, hashes: str, title: str) -> str:
    """Slice from a `##`/`###` heading to the next heading of the same or higher level."""
    lines = text.splitlines()
    start = -1
    for index, line in enumerate(lines):
        match = re.match(r"^(#{2,3})\s+(.*)$", line)
        if not match or match.group(1) != hashes:
            continue
        if match.group(2).replace("`", "").strip().startswith(title):
            start = index
            break
    if start == -1:
        return ""
    level = len(hashes)
    for index in range(start + 1, len(lines)):
        match = re.match(r"^(#{2,3})\s+", lines[index])
        if match and len(match.group(1)) <= level:
            return "\n".join(lines[start:index])
    return "\n".join(lines[start:])


class CompositionDomainNeutralityTest(unittest.TestCase):
    """AC16: the new composition sections stay domain-agnostic (neutral vocabulary, no domain examples).

    Post-hoc guard: the composition text already landed, so this passes on the working
    tree and its intended red state was demonstrated against `HEAD` (see `red-green.md`).
    """

    def test_composition_sections_use_neutral_vocabulary_and_no_domain_examples(self):
        problems: list[str] = []
        ru_tokens: set[str] = set()
        en_tokens: set[str] = set()
        for rel, sections in COMPOSITION_SECTIONS.items():
            text = read(REPO / rel)
            # Every contract and the runner now speak the EN vocabulary; the RU side of
            # the composition documentation is checked separately below.
            vocabulary = EN_VOCABULARY
            seen = en_tokens
            for hashes, title in sections:
                body = heading_slice(text, hashes, title)
                if not body:
                    problems.append(
                        "%s: composition heading %s %r not found — the guard cannot "
                        "silently skip a missing section" % (rel, hashes, title)
                    )
                    continue
                low = body.lower()
                for token in DOMAIN_TOKENS:
                    if token.lower() in low:
                        offset = low.index(token.lower())
                        problems.append(
                            "%s: domain example %r inside §%s (slice line %d)"
                            % (rel, token, title, body[:offset].count("\n") + 1)
                        )
                seen.update(token for token in vocabulary if token in low)
        for rel, sections in RU_COMPOSITION_SECTIONS.items():
            text = read(REPO / rel)
            for hashes, title in sections:
                body = heading_slice(text, hashes, title)
                if not body:
                    problems.append(
                        "%s: composition heading %s %r not found — the guard cannot "
                        "silently skip a missing section" % (rel, hashes, title)
                    )
                    continue
                low = body.lower()
                for token in DOMAIN_TOKENS:
                    if token.lower() in low:
                        offset = low.index(token.lower())
                        problems.append(
                            "%s: domain example %r inside §%s (slice line %d)"
                            % (rel, token, title, body[:offset].count("\n") + 1)
                        )
                ru_tokens.update(token for token in RU_VOCABULARY if token in low)
        self.assertEqual([], problems, "\n".join(problems))
        self.assertGreaterEqual(
            len(ru_tokens),
            3,
            "the RU composition sections must speak the domain-neutral vocabulary "
            f"(≥3 of {RU_VOCABULARY}), got {sorted(ru_tokens)}",
        )
        self.assertGreaterEqual(
            len(en_tokens),
            3,
            "the EN runner composition sections must speak the domain-neutral "
            f"vocabulary (≥3 of {EN_VOCABULARY}), got {sorted(en_tokens)}",
        )


if __name__ == "__main__":
    unittest.main()
