"""Regression guards: the CHECK reference reaches `pdca-check` inline.

The canonical reference lives once in ``pdca/references/check.md``.  `pdca-check`
keeps its ``.pdca/**``-only scoped read, so it cannot open the installed reference:
the driver (normal primary or `pdca-orchestrator`) must read the file in full and
inline its complete text in every CHECK dispatch, and fail closed if it cannot.
A missing contract is a blocker, never a verdict judged from the agent prompt.

These are static contract guards in the style of the family's routing tests.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
FAMILY = REPO / "skills"
BASE = SKILL_DIR / "SKILL.md"
CHECK_REFERENCE = SKILL_DIR / "references/check.md"
CHECK_ASSET = SKILL_DIR / "assets/opencode-agents/pdca-check.md"
DRIVER_ASSET = SKILL_DIR / "assets/opencode-agents/pdca-orchestrator.md"
DRIVER_REFERENCE = SKILL_DIR / "references/driver.md"
FAMILY_SKILLS = ("pdca", "pdca-coder", "pdca-collection", "pdca-dotnet", "pdca-incremental")
DOCS_POINTERS = (
    (REPO / "docs/pdca-incremental.md", "inlines"),
    (REPO / "docs/ru/pdca-incremental.md", "встраивает"),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip()


def _parse_block(block: str) -> dict:
    root: dict = {}
    stack: list = [(-1, root)]
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, val = raw.strip().partition(":")
        key = key.strip().strip('"').strip("'")
        val = val.strip().strip('"').strip("'")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if val == "":
            stack[-1][1][key] = {}
            stack.append((indent, stack[-1][1][key]))
        else:
            stack[-1][1][key] = val
    return root


def permission(path: Path) -> dict:
    text = read(path)
    end = text.find("\n---", 3)
    node = _parse_block(text[3:end]).get("permission")
    if not isinstance(node, dict) or not node:
        raise AssertionError("%s: expected a non-empty `permission:` map" % path)
    return node


class BaseContractTest(unittest.TestCase):
    """The base cycle contract names inline delivery as the only CHECK handoff."""

    def test_check_section_requires_complete_inline_contract(self) -> None:
        text = read(BASE)
        start = text.index("#### CHECK")
        end = text.index("#### ACT", start)
        section = norm(text[start:end]).lower()
        for token in (
            "references/check.md",
            "inline",
            "complete contents",
            "every pdca-check dispatch",
            "recheck",
            "campaign step",
            "collection item",
            "explicit blocker",
            "no reduced contract",
        ):
            with self.subTest(token=token):
                self.assertIn(token, section)

    def test_references_section_assigns_inline_delivery_to_the_driver(self) -> None:
        text = read(BASE)
        start = text.index("- `references/check.md`")
        end = text.find("\n- `references/act.md`", start)
        self.assertGreater(end, start, "check.md bullet not found before act.md")
        bullet = norm(text[start:end]).lower()
        for token in ("inline", "complete", "driver", "explicit blocker"):
            with self.subTest(token=token):
                self.assertIn(token, bullet)

    def test_plan_reference_stays_planner_only_and_uninlined(self) -> None:
        text = norm(read(BASE)).lower()
        for token in (
            "references/plan.md is pdca-planner only",
            "the plan reference is never part of a do, check",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)
        # The driver-side copy moved to the single driver reference; it must still forbid the read.
        driver = norm(read(DRIVER_REFERENCE)).lower()
        for token in (
            "plan_reference_path",
            "never read or inline that file",
            "forward its contents",
        ):
            with self.subTest(token=token):
                self.assertIn(token, driver)


class DriverDispatchTest(unittest.TestCase):
    """The driver reference routes the inline rule; the base owns its text and fail-closed form."""

    def test_driver_inlines_the_complete_contract_in_every_check_dispatch(self) -> None:
        body = norm(read(DRIVER_REFERENCE)).lower()
        for token in (
            "in every pdca-check dispatch",
            "complete contents",
            "check.md",
            "inline",
            "first check",
            "recheck",
            "campaign step",
            "collection lane/item",
            "integration check",
            "no path and no instruction to read it",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_driver_fails_closed_before_a_reduced_contract(self) -> None:
        body = norm(read(DRIVER_REFERENCE)).lower()
        for token in (
            "if it cannot be loaded whole",
            "blocker before dispatch",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)
        # The fail-closed contract itself is the base's, not a reference-local rule.
        base = norm(read(BASE)).lower()
        for token in (
            "explicit blocker",
            "no reduced contract",
            "no verdict from the agent prompt alone",
        ):
            with self.subTest(token=token):
                self.assertIn(token, base)

    def test_every_shipped_driver_copy_routes_the_inline_rule(self) -> None:
        for skill in FAMILY_SKILLS:
            path = FAMILY / skill / "assets/opencode-agents/pdca-orchestrator.md"
            body = norm(read(path)).lower()
            with self.subTest(skill=skill):
                # The procedure is loaded once, from the base package, right after the skill.
                self.assertIn("references/driver.md", body)
                self.assertIn("inlined in every pdca-check dispatch", body)


class CheckerAssetTest(unittest.TestCase):
    """`pdca-check` receives contract text, not a path it cannot open."""

    def test_checker_is_given_the_contract_inline(self) -> None:
        body = norm(read(CHECK_ASSET)).lower()
        for token in (
            "check contract",
            "complete contents",
            "inlined by the driver",
            "no permission to read the installed reference",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_checker_returns_a_blocker_instead_of_a_reduced_verdict(self) -> None:
        body = norm(read(CHECK_ASSET)).lower()
        for token in (
            "absent, truncated or visibly incomplete",
            "explicit blocker",
            "instead of judging from this prompt",
            "not a verdict",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_checker_cannot_read_the_installed_reference(self) -> None:
        perm = permission(CHECK_ASSET)
        self.assertEqual("deny", perm.get("*"))
        for action in ("read", "glob", "list"):
            with self.subTest(action=action):
                allowed = {k for k, v in perm[action].items() if v == "allow"}
                self.assertEqual({".pdca/**"}, allowed,
                                 "CHECK's scoped read must stay .pdca/** only")
        for action in ("edit", "write", "bash", "external_directory"):
            with self.subTest(action=action):
                self.assertNotIn(action, perm, "CHECK must not gain `%s`" % action)


class ReferenceSourceTest(unittest.TestCase):
    """The single source describes its own inline delivery; no overlay copies it."""

    def test_reference_describes_inline_delivery(self) -> None:
        body = norm(read(CHECK_REFERENCE)).lower()
        for token in (
            "complete contents inline",
            "every pdca-check dispatch",
            "explicit blocker",
            "agent prompt alone",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_overlays_do_not_ship_a_second_copy(self) -> None:
        for skill in FAMILY_SKILLS:
            if skill == "pdca":
                continue
            with self.subTest(skill=skill):
                self.assertFalse((FAMILY / skill / "references").exists(),
                                 "%s must inherit the base reference" % skill)


class CheckDedupTest(unittest.TestCase):
    """The inline section keeps the caller contract; the procedure lives in the reference."""

    # The trimmed section is ~2596 bytes; the cap leaves room for a wording
    # correction, not for a return of the ~2070 bytes of procedure moved out.
    MAX_SECTION_BYTES = 2700
    MAX_BASE_BYTES = 50000

    def setUp(self) -> None:
        self.text = read(BASE)
        start = self.text.index("#### CHECK")
        self.raw = self.text[start:self.text.index("#### ACT", start)]
        self.body = norm(self.raw).lower()

    def test_inline_section_stays_a_contract_not_a_procedure(self) -> None:
        self.assertLessEqual(len(self.raw.encode("utf-8")), self.MAX_SECTION_BYTES)

    def test_base_file_stays_under_the_fifty_kilobyte_ceiling(self) -> None:
        self.assertLessEqual(len(self.text.encode("utf-8")), self.MAX_BASE_BYTES)

    def test_the_shared_procedure_is_not_restated_inline(self) -> None:
        for token in ("criteria matrix", "absence of a check", "stable criterion id"):
            with self.subTest(token=token):
                self.assertNotIn(token, self.body)

    def test_gates_unique_to_this_phase_survive_the_trim(self) -> None:
        for token in (
            "explicit cycle scope",
            "cross-part consistency",
            "aggregate score cannot compensate",
            "own scope only",
            "whole-goal check",
            "only check routes such a defect",
            "re-examines the findings with their facts",
            "copying no verdict",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)
        self.assertIn("plan → act", self.body, "user criteria stay whole: PLAN → ACT only")

    def test_the_reference_absorbs_the_moved_procedure(self) -> None:
        body = norm(read(CHECK_REFERENCE))
        for token in ("explicit cycle scope", "parts of a composite result are consistent"):
            with self.subTest(token=token):
                self.assertIn(token, body)
        self.assertNotIn("an attempt is an actual execution", body,
                         "attempt counters have one home: §State machine and counters")
        self.assertIn("base contract's §Escalation — expert review", body)


class PointerConsistencyTest(unittest.TestCase):
    """Every skill's pointer says the driver inlines the file, never that CHECK reads it."""

    def _paragraphs(self, path: Path) -> list[str]:
        return [
            norm(part).lower()
            for part in re.split(r"\n\s*\n", read(path))
            if "references/check.md" in part
        ]

    def test_each_skill_pointer_describes_inline_delivery(self) -> None:
        for skill in FAMILY_SKILLS:
            paragraphs = self._paragraphs(FAMILY / skill / "SKILL.md")
            with self.subTest(skill=skill):
                self.assertTrue(paragraphs, "no check.md pointer")
                self.assertTrue(
                    any(("inline" in p or "inlines" in p) and ("full" in p or "complete" in p)
                        for p in paragraphs),
                    "pointer must say the driver inlines the complete reference",
                )
                for paragraph in paragraphs:
                    self.assertNotIn("read by pdca-check", paragraph)
                    self.assertNotIn("loaded by check", paragraph)

    def test_docs_incremental_pointers_match(self) -> None:
        for path, token in DOCS_POINTERS:
            body = norm(read(path)).lower()
            with self.subTest(path=str(path.relative_to(REPO))):
                self.assertIn("references/check.md", body)
                self.assertIn(token, body)


if __name__ == "__main__":
    unittest.main()
