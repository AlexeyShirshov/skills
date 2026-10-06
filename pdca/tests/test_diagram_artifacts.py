"""Artifact + reproducibility guards for the universal `pdca` hand diagram.

These tests read the generated diagram files under
``config/skills/pdca/assets/diagram/``, assert the exact light/dark titles and
labels, XML well-formedness, a single byte-equal inline SVG per HTML, and zero
domain/security tokens.  Reproducibility is proven empirically: only the
generator is copied into a temporary directory, executed with the current Python
and compared byte-for-byte with the committed artifacts (twice, to prove
determinism).  The external `archify` skill is never invoked.

Run:
    python3 -m unittest discover -s config/skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
DIAGRAM = REPO / "config/skills/pdca/assets/diagram"

GEN = "gen_pdca.py"
LIGHT_STEM = "pdca-hand"
DARK_STEM = "pdca-hand-dark"
FILES = (
    GEN,
    LIGHT_STEM + ".svg", LIGHT_STEM + ".html",
    DARK_STEM + ".svg", DARK_STEM + ".html",
)
LIGHT_TITLE = "pdca — ручная раскладка"
DARK_TITLE = "pdca — ручная раскладка (тёмная тема)"
LABELS = ("P · PLAN", "D · DO", "C · CHECK", "A · ACT", "ЭСКАЛАЦИЯ", "STOP")
NEXT_CYCLE_EDGE_ID = "act_plan"
NEXT_CYCLE_LABEL = "следующий цикл · N+1"
SVG_NS = "{http://www.w3.org/2000/svg}"

# Universal rich-diagram sections that must be present in both themes.
PHASE_COLUMNS = ("P · PLAN", "D · DO", "C · CHECK", "E · ESCALATE", "A · ACT")
GATHER_CARD = "Сбор · gather"
TIER_BADGES = ("cheap", "medium", "strong")
TIER_ROLES = ("pdca-executor", "pdca-orchestrator", "scout",
              "pdca-planner", "pdca-check", "pdca-escalate")

# Domain/stack tokens (as in the contract guard) plus the security markers.
FORBIDDEN_WORDS = (
    "coding", "code", "код", "dotnet", "python", "roslyn", "build", "lint",
    "tdd", "coverage", "xml", "analyzer", "solid", "benchmark", "perf",
    "worktree", "debug", "regression", "docfx", "pdca-coder", "pdca-dotnet",
    "readme", "test", "tests", "security-auditor", "sec", "security",
    "безопасность",
)
FORBIDDEN_LITERALS = (".net", "c#")


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


def boundary_regex(token: str) -> "re.Pattern":
    return re.compile(r"(?<!\w)%s(?!\w)" % re.escape(token), re.IGNORECASE)


def forbidden_hits() -> list:
    hits = []
    for path in sorted(DIAGRAM.iterdir()):
        if not path.is_file():
            continue
        text = read(path)
        for token in FORBIDDEN_WORDS:
            if boundary_regex(token).search(text):
                hits.append((path.name, token))
        low = text.lower()
        for token in FORBIDDEN_LITERALS:
            if token in low:
                hits.append((path.name, token))
    return hits


def contains(rect, px, py) -> bool:
    x1, y1, x2, y2 = rect
    return x1 - 0.5 <= px <= x2 + 0.5 and y1 - 0.5 <= py <= y2 + 0.5


def node_rects(root) -> dict:
    rects = {}
    for el in root.iter():
        nid = el.get("data-node-id")
        if nid:
            x, y = float(el.get("x")), float(el.get("y"))
            w, h = float(el.get("width")), float(el.get("height"))
            rects[nid] = (x, y, x + w, y + h)
    return rects


def edge_endpoints(root, edge_id: str):
    for el in root.iter():
        if el.get("data-edge-id") != edge_id:
            continue
        pts = []
        if el.tag in (SVG_NS + "polyline", "polyline"):
            pts = [tuple(map(float, p.split(","))) for p in el.get("points").split()]
        elif el.tag in (SVG_NS + "path", "path"):
            pts = [tuple(map(float, m.split(",")))
                   for m in re.findall(r"[-.\d]+,[-.\d]+", el.get("d"))]
        if pts:
            return pts[0], pts[-1]
    return None


class DiagramArtifactsTest(unittest.TestCase):
    def test_five_diagram_files_exist(self):
        for name in FILES:
            with self.subTest(name=name):
                self.assertTrue((DIAGRAM / name).is_file(), "%s missing" % name)

    def test_html_titles_are_exact(self):
        self.assertEqual(LIGHT_TITLE, title_of(read(DIAGRAM / (LIGHT_STEM + ".html"))))
        self.assertEqual(DARK_TITLE, title_of(read(DIAGRAM / (DARK_STEM + ".html"))))

    def test_required_labels_in_both_themes(self):
        for name in (LIGHT_STEM + ".svg", LIGHT_STEM + ".html",
                     DARK_STEM + ".svg", DARK_STEM + ".html"):
            text = read(DIAGRAM / name)
            with self.subTest(name=name):
                for label in LABELS:
                    self.assertIn(label, text)

    def test_phase_columns_with_tier_badges_in_both_themes(self):
        for name in (LIGHT_STEM + ".svg", LIGHT_STEM + ".html",
                     DARK_STEM + ".svg", DARK_STEM + ".html"):
            text = read(DIAGRAM / name)
            with self.subTest(name=name):
                for header in PHASE_COLUMNS:
                    self.assertIn(header, text)
                for badge in TIER_BADGES:
                    self.assertIn(badge, text)
                for role in TIER_ROLES:
                    self.assertIn(role, text)
                self.assertIn(GATHER_CARD, text)
                self.assertNotIn("G · GATHER", text)

    def test_act_plan_next_cycle_edge_present_in_both_themes(self):
        for name in (LIGHT_STEM + ".svg", LIGHT_STEM + ".html",
                     DARK_STEM + ".svg", DARK_STEM + ".html"):
            text = read(DIAGRAM / name)
            with self.subTest(name=name):
                self.assertIn('data-edge-id="%s"' % NEXT_CYCLE_EDGE_ID, text)
                self.assertIn('data-edge-id="act_exit"', text)
                self.assertIn(NEXT_CYCLE_LABEL, text)

    def test_act_plan_connects_act_to_plan_not_exit(self):
        for stem in (LIGHT_STEM, DARK_STEM):
            with self.subTest(stem=stem):
                root = ET.parse(DIAGRAM / (stem + ".svg")).getroot()
                rects = node_rects(root)
                declared = {
                    el.get("data-edge-id") for el in root.iter()
                    if el.get("data-edge-id")
                }
                self.assertIn(NEXT_CYCLE_EDGE_ID, declared)
                self.assertIn("act_exit", declared)
                endpoints = edge_endpoints(root, NEXT_CYCLE_EDGE_ID)
                if endpoints is None:
                    self.fail("act_plan endpoints missing")
                start, end = endpoints
                self.assertTrue(contains(rects["ACT"], *start),
                                "act_plan must start in ACT")
                self.assertTrue(contains(rects["PLAN"], *end),
                                "act_plan must end in PLAN")
                self.assertFalse(contains(rects["EXIT"], *end),
                                 "act_plan must not terminate in EXIT")

    def test_svgs_are_wellformed_xml(self):
        for name in (LIGHT_STEM + ".svg", DARK_STEM + ".svg"):
            with self.subTest(name=name):
                root = ET.parse(DIAGRAM / name).getroot()
                self.assertTrue(root.tag.endswith("svg"), root.tag)

    def test_each_html_has_exactly_one_inline_svg_byte_equal(self):
        for stem in (LIGHT_STEM, DARK_STEM):
            html_text = read(DIAGRAM / (stem + ".html"))
            svg_text = read(DIAGRAM / (stem + ".svg"))
            with self.subTest(stem=stem):
                self.assertEqual(1, html_text.count("<svg"))
                self.assertEqual(svg_text, embedded_svg(html_text))

    def test_no_forbidden_token_in_diagram_files(self):
        hits = forbidden_hits()
        self.assertEqual([], hits, "forbidden tokens found: %r" % hits)


class DiagramReproducibilityTest(unittest.TestCase):
    def _run(self, tmp: Path):
        proc = subprocess.run(
            [sys.executable, str(tmp / GEN)],
            cwd=str(tmp),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))

    def test_generator_reproduces_committed_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / GEN).write_text(read(DIAGRAM / GEN), encoding="utf-8")
            self._run(tmp)
            first = {}
            for name in FILES:
                if name == GEN:
                    continue
                first[name] = (tmp / name).read_bytes()
                self.assertEqual(
                    (DIAGRAM / name).read_bytes(), first[name],
                    "%s drifted from the committed artifact" % name,
                )
            # Second run: same generator, same bytes (deterministic).
            self._run(tmp)
            for name in FILES:
                if name == GEN:
                    continue
                self.assertEqual(
                    first[name], (tmp / name).read_bytes(),
                    "%s is not deterministic across runs" % name,
                )

    def test_generator_is_stdlib_only_and_has_no_clock_or_absolute_path(self):
        source = read(DIAGRAM / GEN)
        self.assertNotIn("import archify", source)
        self.assertNotIn("import datetime", source)
        self.assertNotIn("import random", source)
        self.assertNotRegex(source, r"['\"]/home/")


if __name__ == "__main__":
    unittest.main()
