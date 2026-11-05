"""Regression guards: collection-level ACT retrospective and ## Lessons learned.

The collection keeps one separate ## Lessons learned section, pending at creation
and finished at existing collection ACT closures.  It does not create an extra
retrospective for every item, group or phase.

Run:
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"
DOC = SKILL_DIR.parents[1] / "docs/pdca-collection.md"
DOC_RU = SKILL_DIR.parents[1] / "docs/ru/pdca-collection.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


class CollectionRetrospectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(SKILL)
        self.body = norm(self.text)

    def test_collection_has_a_separate_lessons_section(self) -> None:
        for token in (
            "a separate ## lessons learned section",
            "pending at creation, finished in act",
            "same configured pdca-check (retrospective mode)",
            "collection-level act closures",
            "successful integrated-tree check",
            "terminal stop",
            "no per-item, per-group or per-phase extra retrospective is created unless an item cycle itself reaches act",
            "persisted only by pdca-executor",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)


class CollectionDocsTest(unittest.TestCase):
    """Both languages document the collection-level closure retrospective."""

    def test_docs_carry_the_collection_lesson(self) -> None:
        for path in (DOC, DOC_RU):
            body = norm(read(path))
            with self.subTest(path=path.name):
                self.assertIn("## lessons learned", body)
                self.assertIn("check: not run", body)
                self.assertIn("retrospective", body)


if __name__ == "__main__":
    unittest.main()
