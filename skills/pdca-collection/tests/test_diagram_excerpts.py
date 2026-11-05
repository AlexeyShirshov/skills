"""Guards for the two published excerpts of the collection hand picture.

The single ``collection-hand-dark*.svg`` is also published as two images:
``collection-contract-dark*.svg`` (the hand diagram: orchestrator + peer columns +
corrective row + tier legend) and ``collection-state-dark*.svg`` (the state graph
with its footnotes).  Both carry the full hand document and differ only in the
opening ``viewBox`` -- the same deterministic crop approach as ``pdca``'s
contract/state excerpts.  The diagram ships in Russian (unsuffixed) and English
(``-en``); the crops follow the hand file of their own language.

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
LANGUAGES = {
    "ru": (
        "collection-hand-dark.svg",
        ("collection-contract-dark.svg", "collection-state-dark.svg"),
        [],
    ),
    "en": (
        "collection-hand-dark-en.svg",
        ("collection-contract-dark-en.svg", "collection-state-dark-en.svg"),
        ["--lang", "en"],
    ),
}
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
        for hand, excerpts, _ in LANGUAGES.values():
            for name in (GEN, hand) + excerpts:
                with self.subTest(name=name):
                    self.assertTrue((DIAGRAM / name).is_file(), "%s missing" % name)

    def test_excerpts_share_the_hand_body(self):
        for hand, excerpts, _ in LANGUAGES.values():
            hand_body = self.body(read(DIAGRAM / hand))
            for name in excerpts:
                with self.subTest(name=name):
                    self.assertEqual(hand_body, self.body(read(DIAGRAM / name)))

    def test_excerpts_tile_the_hand_vertically(self):
        for hand, excerpts, _ in LANGUAGES.values():
            with self.subTest(hand=hand):
                _, hand_y, _, hand_h = self.viewbox(hand)
                _, c_y, _, c_h = self.viewbox(excerpts[0])
                _, s_y, _, s_h = self.viewbox(excerpts[1])
                self.assertEqual(0, hand_y)
                self.assertEqual(0, c_y)
                self.assertEqual(c_h, s_y, "the state excerpt must start where the diagram ends")
                self.assertEqual(hand_h, c_h + s_h, "the excerpts must cover the whole hand canvas")

    def test_the_store_is_reproducible_in_both_languages(self):
        for hand, excerpts, args in LANGUAGES.values():
            with self.subTest(language=hand):
                with tempfile.TemporaryDirectory() as td:
                    tmp = Path(td)
                    (tmp / GEN).write_text(read(DIAGRAM / GEN), encoding="utf-8")
                    proc = subprocess.run(
                        [sys.executable, str(tmp / GEN), *args],
                        cwd=str(tmp),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    self.assertEqual(0, proc.returncode,
                                     proc.stderr.decode("utf-8", "replace"))
                    for name in (hand,) + excerpts:
                        with self.subTest(name=name):
                            self.assertEqual(
                                (DIAGRAM / name).read_bytes(),
                                (tmp / name).read_bytes(),
                                "%s drifted from the committed artifact" % name,
                            )


if __name__ == "__main__":
    unittest.main()
