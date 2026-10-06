"""Artifact guards for the pdca-coder hand diagram.

These tests read the generated diagram files under
``config/skills/pdca-coder/assets/diagram/`` only; they never re-run the generator.
Reproducibility is proven by command evidence in the cycle status file.

Run:
    python3 -m unittest discover -s config/skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
DIAGRAM = REPO / "config/skills/pdca-coder/assets/diagram"

# Assembled at runtime; the contiguous bad token is never written as one literal.
BAD_TOKEN = "dot" + "net"
HAND_FILES = (
    "pdca-coder-hand.svg",
    "pdca-coder-hand.html",
    "pdca-coder-hand-dark.svg",
    "pdca-coder-hand-dark.html",
)
LENS_LABEL = "scout + доменные линзы"
DOCS_LABEL = "README · документация"
LIGHT_TITLE = "pdca-coder — ручная раскладка"
DARK_TITLE = "pdca-coder — ручная раскладка (тёмная тема)"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def title_of(html_text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html_text, re.DOTALL)
    return match.group(1) if match else ""


def embedded_svg(html_text: str) -> str:
    start = html_text.find("<svg")
    end = html_text.find("</svg>", start)
    if start < 0 or end < 0:
        raise AssertionError("no embedded <svg> ... </svg> found")
    return html_text[start:end + len("</svg>")]


class DiagramArtifactsTest(unittest.TestCase):
    def test_four_hand_files_exist(self):
        for name in HAND_FILES:
            with self.subTest(name=name):
                self.assertTrue((DIAGRAM / name).is_file(), "%s missing" % name)

    def test_both_svgs_carry_generic_labels(self):
        for name in ("pdca-coder-hand.svg", "pdca-coder-hand-dark.svg"):
            with self.subTest(name=name):
                svg = read(DIAGRAM / name)
                self.assertIn(LENS_LABEL, svg)
                self.assertIn(DOCS_LABEL, svg)

    def test_html_titles_are_generic(self):
        light = title_of(read(DIAGRAM / "pdca-coder-hand.html"))
        dark = title_of(read(DIAGRAM / "pdca-coder-hand-dark.html"))
        self.assertIn(LIGHT_TITLE, light)
        self.assertIn(DARK_TITLE, dark)

    def test_svgs_are_wellformed_xml(self):
        for name in ("pdca-coder-hand.svg", "pdca-coder-hand-dark.svg"):
            with self.subTest(name=name):
                root = ET.parse(DIAGRAM / name).getroot()
                self.assertTrue(root.tag.endswith("svg"), root.tag)

    def test_embedded_svgs_in_html_are_wellformed_xml(self):
        for name in ("pdca-coder-hand.html", "pdca-coder-hand-dark.html"):
            with self.subTest(name=name):
                root = ET.fromstring(embedded_svg(read(DIAGRAM / name)))
                self.assertTrue(root.tag.endswith("svg"), root.tag)

    def test_hand_files_carry_no_stack_token(self):
        for name in HAND_FILES:
            with self.subTest(name=name):
                self.assertNotIn(BAD_TOKEN, read(DIAGRAM / name).lower())

    def test_emit_titles(self):
        for name in ("pdca-coder-hand.html", "pdca-coder-hand-dark.html"):
            print("title[%s] = %r" % (name, title_of(read(DIAGRAM / name))))


if __name__ == "__main__":
    unittest.main()
