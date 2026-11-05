"""Regression guards: collection-level ACT retrospective and ## Lessons learned.

The collection keeps one separate ## Lessons learned section, pending at creation
and finished at existing collection ACT closures.  It is the final retrospective
of the collection's *own* invocation — every terminal outcome, not only success or
STOP — and never a second retrospective for an item, group, phase or boundary.

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
            "pending at creation",
            "finished in act",
            "final retrospective of pdca-collection's own invocation",
            "completed once per actually completed invocation",
            "same configured pdca-check",
            "retrospective mode, read-only",
            "every actually finalized outcome",
            "accepted integration, verified partial integration",
            "terminal stop",
            "no per-item, per-group or per-phase extra retrospective is created",
            "an item cycle that itself reaches act keeps its own base skeleton",
            "pdca-executor persists it and completes the final act bookkeeping",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_every_terminal_outcome_closes_the_parent_retrospective(self) -> None:
        for token in (
            "blocked/incomplete, terminal stop, an early failure or a refusal",
            "when the collection itself actually closes blocked/incomplete/stop",
            "there is no parent-level pause status that would defer it",
            "a child campaign's running status or disposition: paused checkpoint proves only that that item has not completed",
            "does not by itself complete the collection and is not a terminal parent outcome",
            "takes precedence over the generic cycle-task retrospective inputs and the general what-worked output",
            "premature exit before a status record exists",
            "authorized form: collection shape",
            "explicit closure blocker instead of skipping it",
            "adds no verdict, check, verification, attempt, counter or do work",
            "never reopens the accepted result",
            "final act bookkeeping, not a new pdca phase or quality gate",
            "a run that ended before any item still closes it there",
            "no check or item work is invented",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_reentry_appends_without_overwriting_completed_lessons(self) -> None:
        for token in (
            "explicitly authorized already completed form: collection record is re-entered",
            "completed lesson entries are kept",
            "appended within the same ## lessons learned",
            "existing ## progress log closure reference",
            "no new counter, log, section or phase and no overwrite",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_parent_only_scope_excludes_child_lessons(self) -> None:
        for token in (
            "parent-only scope of that retrospective",
            "item decomposition, dependency dag/groups/lane allocation, routing and handoffs, integration and verification orchestration and status bookkeeping",
            "plus its own instructions as evidenced",
            "only observed defects of this skill's own operation",
            "never task/domain results",
            "a bad task outcome is not automatically a skill defect",
            "an item's own retrospective content, child lessons, or a summary/aggregation of them",
            "recorded parent-child interaction may evidence a parent routing/handoff error with attribution and uncertainty stated",
            "0–3 transferable lessons",
            "no skill-level defects found only after actual analysis",
            "it edits no skill, config or agents.md",
            "creates no parallel file, log, role, phase or counter",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_intermediate_boundaries_do_not_duplicate_it(self) -> None:
        for token in (
            "an intermediate approval wait, an item/group closure, a checkpoint, a child pause, a session ending alone, a lane boundary, a child closure and a failed probe are not triggers by themselves",
            "no per-item, per-group or per-phase extra retrospective is created",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_independent_of_an_item_act(self) -> None:
        for token in (
            "an item cycle that itself reaches act keeps its own base skeleton",
            "act also closes the collection's own final ## lessons learned retrospective",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_failed_dispatch_fails_closed(self) -> None:
        for token in (
            "if the dispatch is absent or fails",
            "section stays pending with the explicit closure blocker",
            "the original result is preserved",
            "neither driver nor executor substitutes an analysis",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)


class CollectionDocsTest(unittest.TestCase):
    """Both languages document the parent-only closure retrospective."""

    def test_docs_carry_the_collection_lesson(self) -> None:
        for path in (DOC, DOC_RU):
            body = norm(read(path))
            with self.subTest(path=path.name):
                self.assertIn("## lessons learned", body)
                self.assertIn("check: not run", body)
                self.assertIn("retrospective", body)
                self.assertIn("closure blocker", body)

    def test_docs_name_the_parent_only_scope(self) -> None:
        en = norm(read(DOC))
        ru = norm(read(DOC_RU))
        with self.subTest(path=DOC.name):
            self.assertIn("collection's own invocation", en)
            self.assertIn("completed once per actually completed invocation", en)
            self.assertIn("when the collection itself actually closes blocked/incomplete/stop", en)
            self.assertIn("there is no parent-level pause status that would defer it", en)
            self.assertIn("does not by itself complete the collection", en)
            self.assertIn("takes precedence over the generic cycle-task retrospective inputs", en)
            self.assertIn("completed lesson entries are kept", en)
            self.assertIn("no skill-level defects found", en)
            self.assertIn("never task results, child lessons", en)
        with self.subTest(path=DOC_RU.name):
            self.assertIn("собственного вызова коллекции", ru)
            self.assertIn("один раз на действительно завершённый вызов", ru)
            self.assertIn("когда коллекция действительно закрывается как blocked/incomplete/stop", ru)
            self.assertIn("родительского статуса-паузы", ru)
            self.assertIn("не завершает коллекцию", ru)
            self.assertIn("имеет приоритет над общими входными данными", ru)
            self.assertIn("завершённые записи уроков сохраняются", ru)
            self.assertIn("no skill-level defects found", ru)
            self.assertIn("не результаты задачи, уроки дочерних", ru)


if __name__ == "__main__":
    unittest.main()
