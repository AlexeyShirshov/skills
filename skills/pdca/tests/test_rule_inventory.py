"""The rule inventory is a projection of the base contract, not a second source of truth.

`docs/ru/pdca-rules.md` carries one table row per sentence of ``skills/pdca/SKILL.md`` between two
markers. These guards keep it honest:

* the block equals a fresh extraction (a contract edit that skips the inventory fails here);
* every row is well formed and its line range points inside the skill;
* ids are contiguous, so a rule can be cited by a stable `R-NNN`.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "skills/pdca/scripts/skill_rule_inventory.py"
DOC = REPO / "docs/ru/pdca-rules.md"


def load():
    spec = importlib.util.spec_from_file_location("skill_rule_inventory", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


INVENTORY = load()
ROW = re.compile(
    r"^\| (R-\d{3}) \| (\d+)(?:–(\d+))? \| (абз|пункт|табл|код) \| (.+?) \| (.+?) \|$")


class RuleInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.rows = [ROW.match(line) for line in cls.doc.splitlines()]
        cls.rows = [m for m in cls.rows if m]
        cls.skill_lines = len(INVENTORY.SOURCE.read_text(encoding="utf-8").splitlines())

    def test_the_document_carries_the_generated_block(self) -> None:
        self.assertIn(INVENTORY.BEGIN, self.doc)
        self.assertIn(INVENTORY.END, self.doc)
        self.assertGreater(len(self.rows), 100, "the inventory must not be a stub")

    def test_the_block_matches_a_fresh_extraction(self) -> None:
        self.assertEqual(INVENTORY.extract(self.doc), INVENTORY.render(INVENTORY.SOURCE),
                         "inventory drifted — run skill_rule_inventory.py --fix")

    def test_a_changed_sentence_is_detected(self) -> None:
        tampered = self.doc.replace("| R-001 |", "| R-001 | drift ", 1)
        self.assertNotEqual(INVENTORY.extract(tampered), INVENTORY.render(INVENTORY.SOURCE),
                            "the comparison must notice a changed block")

    def test_rows_are_well_formed_with_a_line_inside_the_skill(self) -> None:
        problems: list[str] = []
        for match in self.rows:
            rid, lo, hi, kind, text, practice = match.groups()
            if not text.strip():
                problems.append("%s: empty rule" % rid)
            if not practice.strip():
                problems.append("%s: empty practice" % rid)
            if not (1 <= int(lo) <= self.skill_lines):
                problems.append("%s: line %s outside the skill" % (rid, lo))
            if hi is not None and int(hi) < int(lo):
                problems.append("%s: reversed range %s–%s" % (rid, lo, hi))
        self.assertEqual([], problems, "\n".join(problems))

    def test_ids_are_contiguous(self) -> None:
        ids = [int(m.group(1)[2:]) for m in self.rows]
        self.assertEqual(list(range(1, len(ids) + 1)), ids,
                         "R-NNN ids must be contiguous and in document order")

    def test_the_count_table_matches_the_rows(self) -> None:
        cells = re.findall(r"^\| \*\*Строк в инвентаре\*\* \| \*\*(\d+)\*\* \|$", self.doc, re.M)
        self.assertTrue(cells, "the generated block must carry the count table")
        self.assertEqual(int(cells[0]), len(self.rows))


class PracticeEvidenceTest(unittest.TestCase):
    """Every rule carries practice, and the practice follows the wording, not the number."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = INVENTORY.load_evidence()
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.rows = [m for m in (ROW.match(line) for line in cls.doc.splitlines()) if m]

    def test_every_rule_has_a_practice_entry(self) -> None:
        problems: list[str] = []
        used: set[str] = set()
        INVENTORY.render(INVENTORY.SOURCE, self.entries, problems, used)
        self.assertEqual([], problems, "\n".join(problems))

    def test_no_rule_is_rendered_without_evidence(self) -> None:
        self.assertNotIn("нет подтверждения", self.doc,
                         "a rule without practice must not reach the document")

    def test_every_entry_has_a_known_kind_and_a_resolvable_ref(self) -> None:
        problems: list[str] = []
        for sha, entry in self.entries.items():
            if entry.get("kind") not in INVENTORY.KINDS:
                problems.append("%s: kind %r" % (sha[:8], entry.get("kind")))
            if not entry.get("practice", "").strip():
                problems.append("%s: empty practice" % sha[:8])
            problem = INVENTORY._ref_problem(entry.get("ref", ""))
            if problem:
                problems.append("%s: %s" % (sha[:8], problem))
        self.assertEqual([], problems, "\n".join(problems))

    def test_evidence_is_bound_to_the_rule_text_not_to_its_number(self) -> None:
        # Rewriting one word of a rule must invalidate its practice entry.
        source = INVENTORY.SOURCE.read_text(encoding="utf-8")
        marker = "**The skill is loaded"
        self.assertIn(marker, source)
        tampered = source.replace(marker, "**The skill is loaded always", 1)
        tmp = INVENTORY.SOURCE.with_suffix(".tmp.md")
        try:
            tmp.write_text(tampered, encoding="utf-8")
            problems: list[str] = []
            used: set[str] = set()
            INVENTORY.render(tmp, self.entries, problems, used)
        finally:
            tmp.unlink()
        self.assertTrue(any("no practice entry" in p for p in problems),
                        "a reworded rule must demand a practice review: %r" % problems)

    def test_an_orphan_entry_is_reported(self) -> None:
        entries = dict(self.entries)
        entries["0" * 40] = {"id": "R-999", "kind": "cf", "ref": "", "practice": "stale"}
        problems: list[str] = []
        used: set[str] = set()
        INVENTORY.render(INVENTORY.SOURCE, entries, problems, used)
        self.assertEqual(["0" * 40], sorted(set(entries) - used))

    def test_only_durable_citations_pass(self) -> None:
        self.assertIsNone(INVENTORY._ref_problem("commit:f753f11"))
        self.assertIsNone(INVENTORY._ref_problem("docs/ru/pdca-rules.md:1"))
        self.assertIsNone(INVENTORY._ref_problem(
            "nextorm:docs/specs/status/D217-datetimeoffset-1.md:23"))
        self.assertIsNotNone(INVENTORY._ref_problem("commit:zzz"))
        self.assertIsNotNone(INVENTORY._ref_problem("docs/ru/does-not-exist.md"))
        scratch = REPO / "docs/ru/.untracked-citation.tmp"
        scratch.write_text("x", encoding="utf-8")
        try:
            problem = INVENTORY._ref_problem("docs/ru/.untracked-citation.tmp")
        finally:
            scratch.unlink()
        self.assertIn("not tracked", problem or "")


if __name__ == "__main__":
    unittest.main()
