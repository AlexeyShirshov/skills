"""Artifact guards for the pdca-coder hand diagram.

These tests read the generated diagram files under
``skills/pdca-coder/assets/diagram/`` only; they never re-run the generator.
Reproducibility is proven by command evidence in the cycle status file.

Run:
    python3 -m unittest discover -s skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
DIAGRAM = SKILL_DIR / "assets/diagram"

# Assembled at runtime; the contiguous bad token is never written as one literal.
BAD_TOKEN = "dot" + "net"
HAND_FILES = (
    "pdca-coder-hand.svg",
    "pdca-coder-hand.html",
    "pdca-coder-hand-dark.svg",
    "pdca-coder-hand-dark.html",
)
LENS_LABEL = "pdca-scout + domain lenses"
DOCS_LABEL = "README · documentation"
LIGHT_TITLE = "pdca-coder — hand layout"
DARK_TITLE = "pdca-coder — hand layout (dark theme)"


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

    def test_do_cannot_finish_routes_to_act_and_stop_is_act_finalised(self):
        """DO → ACT; STOP is an ACT outcome; no DO → PLAN edge survives."""
        for name in ("pdca-coder-hand.svg", "pdca-coder-hand-dark.svg"):
            with self.subTest(name=name):
                root = ET.parse(DIAGRAM / name).getroot()
                boxes = {}
                for el in root.iter():
                    nid = el.get("data-node-id")
                    if nid:
                        boxes[nid] = tuple(float(el.get(a) or 0)
                                           for a in ("x", "y", "width", "height"))
                edges = {el.get("data-edge-id"): el for el in root.iter()
                         if el.get("data-edge-id")}
                self.assertIn("do_act_incomplete", edges)
                self.assertNotIn("do_plan_blocker", edges)
                self.assertIn("act_stop", edges)
                self.assertNotIn("escalate_stop", edges)

                def ends(edge):
                    pts = [tuple(map(float, p.split(",")))
                           for p in (edge.get("points") or "").split()]
                    return pts[0], pts[-1]

                def inside(node, point):
                    x, y, w, h = boxes[node]
                    return x - 1 <= point[0] <= x + w + 1 and y - 1 <= point[1] <= y + h + 1

                start, end = ends(edges["do_act_incomplete"])
                self.assertTrue(inside("DO", start))
                self.assertTrue(inside("ACT", end))
                start, end = ends(edges["act_stop"])
                self.assertTrue(inside("ACT", start))
                self.assertTrue(inside("stop", end))

    def test_emit_titles(self):
        for name in ("pdca-coder-hand.html", "pdca-coder-hand-dark.html"):
            print("title[%s] = %r" % (name, title_of(read(DIAGRAM / name))))


if __name__ == "__main__":
    unittest.main()
