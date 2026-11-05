"""Regression guards: the campaign's own retrospective and the per-step one.

The campaign form inherits the base skeleton demoted under each step, so its
``#### Lessons learned`` is pending at step creation and finished in ACT,
including a terminal STOP.  The container also carries a distinct top-level
``## Lessons learned``: the final retrospective of the campaign skill's *own*
invocation, for every terminal outcome, kept apart from the step records and
not aggregated from them.  No new role, log, phase or counter is introduced.

Run:
    python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"
DOC = SKILL_DIR.parents[1] / "docs/pdca-incremental.md"
DOC_RU = SKILL_DIR.parents[1] / "docs/ru/pdca-incremental.md"
GUIDE = SKILL_DIR.parents[1] / "docs/pdca-guide.md"
GUIDE_RU = SKILL_DIR.parents[1] / "docs/ru/pdca-guide.md"

CONTAINER_ORDER = (
    "## Campaign state",
    "## Original task",
    "## Preparation record",
    "## Baseline record",
    "## Checkpoint",
    "## Step records",
    "## Campaign outcome",
    "## Lessons learned",
    "## Progress log",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


def container_headings(text: str) -> list[str]:
    """The fixed section order, read from the first fenced text block listing it."""
    blocks = re.findall(r"```text\n(.*?)```", text, re.DOTALL)
    for block in blocks:
        lines = [
            re.split(r"\s{2,}#", line.strip())[0].strip()
            for line in block.splitlines()
            if line.strip()
        ]
        if lines and lines[0].startswith("## Campaign state"):
            return lines
    return []


def guide_container_headings(text: str) -> list[str]:
    """The section order from the guide's inline enumeration of the container."""
    match = re.search(r"—\s*((?:`## [^`]+`(?:,\s*)?)+)", text)
    if not match:
        return []
    return [f"## {name.strip()}" for name in re.findall(r"`## ([^`]+)`", match.group(1))]


class IncrementalRetrospectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read(SKILL)
        self.body = norm(self.text)

    def test_per_step_act_runs_the_base_retrospective(self) -> None:
        for token in (
            "per-step act, including a terminal stop, runs the same configured pdca-check retrospective",
            "demoted #### lessons learned",
            "pending at step creation",
            "finished in act",
            "same campaign file",
            "no new role, log, phase or counter",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_shared_event_log_remains_single(self) -> None:
        for token in (
            "base status skeleton",
            "demoted under that step's record",
            "exactly one event log",
            "never a second chronology",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_container_carries_a_distinct_top_level_lessons_section(self) -> None:
        for path in (SKILL, DOC, DOC_RU):
            with self.subTest(path=path.name):
                order = container_headings(read(path))
                self.assertEqual(list(CONTAINER_ORDER), order)
                self.assertEqual(
                    order.index("## Lessons learned"),
                    order.index("## Campaign outcome") + 1,
                )
                self.assertLess(
                    order.index("## Lessons learned"), order.index("## Progress log")
                )

    def test_guide_documents_the_same_section_order(self) -> None:
        for path in (GUIDE, GUIDE_RU):
            with self.subTest(path=path.name):
                self.assertEqual(
                    list(CONTAINER_ORDER), guide_container_headings(read(path))
                )

    def test_campaign_level_retrospective_covers_every_outcome(self) -> None:
        for token in (
            "the container's ## lessons learned is distinct from a step's demoted #### lessons learned",
            "completed once per actually completed invocation",
            "never per revision, per step or per checkpoint",
            "met, limited, unreachable, blocked, stopped",
            "independently completed preparation-only dispatch",
            "early refusal or failure that ends the invocation before any step",
            "no step, check or execution is invented for that exit",
            "adds no verdict, check, verification, attempt, counter, do work or route",
            "final act bookkeeping, not a new pdca phase or quality gate",
            "every actually finalized outcome above",
            "closes the campaign's own ## lessons learned once",
            "a pause or an approval wait does not",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_pause_and_open_invocation_are_not_completion(self) -> None:
        for token in (
            "an actually finalized outcome",
            "a pause, not a terminal outcome",
            "invariant 5 keeps status: running with disposition: paused",
            "checkpoint, a pause, an approval wait, a session ending alone, an intermediate boundary",
            "accepted or rejected step with its own retrospective are not triggers",
            "preparation phase that continues into execution",
            "still-open invocation waiting for approval, has not completed",
            "resumed paused invocation remains the same open invocation and fills the same pending slot once",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_preparation_only_lessons_live_in_the_preparation_document(self) -> None:
        for token in (
            "no campaign runtime status",
            "final metadata inside the immutable preparation document revision",
            "for a genuinely completed preparation-only dispatch only, the final ## lessons learned metadata",
            "published under the same authorized preparation_ref path as the preparation result",
            "never an in-place edit of an already published revision",
            "already authorized preparation_ref path",
            "never a new standalone path, a separate log, a baseline or a runtime status",
            "publishes an immutable revision including ## lessons learned",
            "preserves the substantive preparation result",
            "already published revision is never mutated",
            "existing new-revision mechanism",
            "explicit authorized executor dispatch",
            "explicit closure blocker",
            "preparation result preserved",
            "not a preparation-readiness or execution-approval gate",
            "ready result stays frozen",
            "neither copied nor aggregated into a later campaign container's ## lessons learned",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_reentry_appends_without_overwriting_completed_lessons(self) -> None:
        for token in (
            "explicitly authorized already completed form: incremental record is re-entered",
            "completed lesson entries are kept",
            "appended within the same ## lessons learned",
            "existing ## progress log closure reference",
            "no new counter, log, section or phase and no overwrite",
            "preparation revisions are immutable per-dispatch records, so no separate append applies there",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_parent_only_scope_excludes_child_lessons(self) -> None:
        for token in (
            "scope override (this skill only)",
            "only observed defects of pdca-incremental's own operation",
            "preparation and bootstrap, step boundary/routing and handoffs, status bookkeeping, counters and recovery",
            "do not report task/domain results",
            "a bad task outcome as a skill defect",
            "summary or aggregation of step retrospects, or a generic what-worked section",
            "recorded parent-child interaction may evidence a routing/handoff error with attribution and uncertainty stated",
            "0–3 transferable lessons",
            "no skill-level defects found is valid only after actual analysis",
            "no automated edit of skills, config or agents.md",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_failed_dispatch_fails_closed(self) -> None:
        for token in (
            "an absent or failed dispatch keeps the section pending with an explicit closure blocker",
            "preserves the originating outcome",
            "permits no fallback analysis by the driver or the executor",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)


class IncrementalDocsTest(unittest.TestCase):
    """Both languages document the demoted per-step and the parent retrospective."""

    def test_docs_carry_the_step_lesson(self) -> None:
        for path in (DOC, DOC_RU):
            body = norm(read(path))
            with self.subTest(path=path.name):
                self.assertIn("#### lessons learned", body)
                self.assertIn("check: not run", body)
                self.assertIn("retrospective", body)

    def test_docs_carry_the_campaign_level_lesson(self) -> None:
        for path in (DOC, DOC_RU):
            body = norm(read(path))
            with self.subTest(path=path.name):
                self.assertIn("## lessons learned", body)
                self.assertIn("closure blocker", body)
        en = norm(read(DOC))
        ru = norm(read(DOC_RU))
        with self.subTest(path=DOC.name):
            self.assertIn("final retrospective of its own invocation", en)
            self.assertIn("preparation-only dispatch", en)
            self.assertIn("preparation document revision", en)
            self.assertIn("for a genuinely completed preparation-only dispatch only, the final ## lessons learned metadata", en)
            self.assertIn("published under the same authorized preparation_ref path as the preparation result", en)
            self.assertIn("completed lesson entries are kept", en)
            self.assertIn("not task results", en)
        with self.subTest(path=DOC_RU.name):
            self.assertIn("финальная ретроспектива собственного вызова", ru)
            self.assertIn("диспетчеризации только с подготовкой", ru)
            self.assertIn("ревизии документа подготовки", ru)
            self.assertIn("только для действительно завершённой диспетчеризации с одной подготовкой", ru)
            self.assertIn("по тому же разрешённому пути", ru)
            self.assertIn("завершённые записи уроков сохраняются", ru)
            self.assertIn("не результаты задачи", ru)


if __name__ == "__main__":
    unittest.main()
