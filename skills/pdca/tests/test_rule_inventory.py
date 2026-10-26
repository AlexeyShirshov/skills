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
ROW = re.compile(r"^\| (R-\d{3}) \| (\d+)(?:–(\d+))? \| (абз|пункт|табл|код) \| (.+) \|$")


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
            rid, lo, hi, kind, text = match.groups()
            if not text.strip():
                problems.append("%s: empty rule" % rid)
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


if __name__ == "__main__":
    unittest.main()
