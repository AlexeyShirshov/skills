"""Guards for the two published excerpts of the collection hand picture.

The single ``collection-hand-dark.svg`` is also published as two images:
``collection-contract-dark.svg`` (the hand diagram: orchestrator + peer columns +
corrective row + tier legend) and ``collection-state-dark.svg`` (the state graph
with its footnotes).  Both carry the full hand document and differ only in the
opening ``viewBox`` -- the same deterministic crop approach as ``pdca``'s
contract/state excerpts.  These tests guard against an excerpt drifting after a
diagram regeneration.

Run:
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
DIAGRAM = SKILL_DIR / "assets/diagram"

GEN = "gen_collection.py"
HAND = "collection-hand-dark.svg"
EXCERPTS = ("collection-contract-dark.svg", "collection-state-dark.svg")
VIEWBOX = re.compile(r'viewBox="(-?\d+) (-?\d+) (\d+) (\d+)"')


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class DiagramExcerptTest(unittest.TestCase):
    @staticmethod
    def body(text: str) -> str:
        return text[text.index(">") + 1:]

    def viewbox(self, name: str):
        match = VIEWBOX.search(read(DIAGRAM / name))
        self.assertIsNotNone(match, "%s has no viewBox" % name)
        return tuple(int(part) for part in match.groups())

    def test_both_excerpts_exist(self):
        for name in (GEN, HAND) + EXCERPTS:
            with self.subTest(name=name):
                self.assertTrue((DIAGRAM / name).is_file(), "%s missing" % name)

    def test_excerpts_share_the_hand_body(self):
        hand = read(DIAGRAM / HAND)
        for name in EXCERPTS:
            with self.subTest(name=name):
                self.assertEqual(self.body(hand), self.body(read(DIAGRAM / name)))

    def test_excerpts_tile_the_hand_vertically(self):
        _, hand_y, _, hand_h = self.viewbox(HAND)
        _, c_y, _, c_h = self.viewbox(EXCERPTS[0])
        _, s_y, _, s_h = self.viewbox(EXCERPTS[1])
        self.assertEqual(0, hand_y)
        self.assertEqual(0, c_y)
        self.assertEqual(c_h, s_y, "the state excerpt must start where the diagram ends")
        self.assertEqual(hand_h, c_h + s_h, "the excerpts must cover the whole hand canvas")

    def test_excerpts_are_reproducible(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / GEN).write_text(read(DIAGRAM / GEN), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(tmp / GEN)],
                cwd=str(tmp),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(0, proc.returncode,
                             proc.stderr.decode("utf-8", "replace"))
            for name in EXCERPTS:
                with self.subTest(name=name):
                    self.assertEqual(
                        (DIAGRAM / name).read_bytes(), (tmp / name).read_bytes(),
                        "%s drifted from the committed artifact" % name,
                    )


if __name__ == "__main__":
    unittest.main()
