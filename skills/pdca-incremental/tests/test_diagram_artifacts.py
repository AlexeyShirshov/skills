"""Artifact and reproducibility guards for the pdca-incremental hand diagram.

Reads the generated files under ``skills/pdca-incremental/assets/diagram/`` and
asserts the family invariants: light/dark titles, required labels, XML well-formedness,
one byte-equal inline SVG per HTML and no domain tokens.  Reproducibility is proven
empirically: only the generator is copied into a temporary directory, executed twice
with the current Python and compared byte-for-byte with the committed artifacts.

Run:
    python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
DIAGRAM = SKILL_DIR / "assets/diagram"

GEN = "gen_incremental.py"
LIGHT = "incremental-hand"
DARK = "incremental-hand-dark"
FILES = (
    GEN,
    LIGHT + ".svg", LIGHT + ".html",
    DARK + ".svg", DARK + ".html",
    "incremental-contract-dark.svg",
    "incremental-state-dark.svg",
)
LIGHT_TITLE = "pdca-incremental — campaign in steps"
DARK_TITLE = "pdca-incremental — campaign in steps (dark theme)"
LABELS = (
    "BOOTSTRAP", "PLAN", "STEP N", "ACCEPT", "DECIDE", "STOP",
    "Discover · gap map", "Brief · six blocks", "Ranked seed",
    "P · PLAN", "D · DO", "C · CHECK", "A · ACT",
    # the step exit is the base step boundary, not a step-kind table
    "Step exit", "accept · revise · new step",
    "Route", "next · revise · stop",
    "one writer · status write",
    "next step · baseline = accepted", "repair · parent N",
    "verify — optional integrated gate: target = gate, does not move the baseline",
    "met · unreachable · blocked · stopped",
    "Orchestrator · cheap — cycle-control / campaign-control",
    "pdca-planner · read-only", "pdca-executor · edit/bash",
    "pdca-scout · facts, not a decision", "pdca-check · read-only · evidence", "primary · status-only",
    "cheap tier", "medium tier", "pdca-check · medium",
    "strong · pdca-escalate — not a campaign role",
)
# The old campaign catalogue (step kinds) is gone: the step boundary decides.
STALE_LABELS = (
    "Step kind", "increment · repair · verify", "next · repair · verify",
    "verify — optional integrated gate<",
)
BAD_TOKENS = ("nextorm", "dot" + "net", "python")


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
    def test_all_files_exist(self) -> None:
        for name in FILES:
            with self.subTest(name=name):
                self.assertTrue((DIAGRAM / name).is_file(), "%s missing" % name)

    def test_svgs_are_well_formed(self) -> None:
        for name in (LIGHT + ".svg", DARK + ".svg"):
            with self.subTest(name=name):
                root = ET.parse(DIAGRAM / name).getroot()
                self.assertTrue(root.tag.endswith("svg"))
                self.assertTrue(root.get("viewBox"))

    def test_both_svgs_carry_the_step_loop_labels(self) -> None:
        for name in (LIGHT + ".svg", DARK + ".svg"):
            with self.subTest(name=name):
                svg = read(DIAGRAM / name)
                for label in LABELS:
                    self.assertIn(label, svg)

    def test_the_defining_feedback_edge_exists(self) -> None:
        for name in (LIGHT + ".svg", DARK + ".svg"):
            with self.subTest(name=name):
                self.assertIn('data-edge-id="decide_plan"', read(DIAGRAM / name))

    def test_the_stale_step_kind_catalogue_is_gone(self) -> None:
        for name in (LIGHT + ".svg", DARK + ".svg"):
            with self.subTest(name=name):
                svg = read(DIAGRAM / name)
                for label in STALE_LABELS:
                    self.assertNotIn(label, svg, f"stale step-kind label {label!r}")

    def test_the_repair_feedback_edge_exists(self) -> None:
        for name in (LIGHT + ".svg", DARK + ".svg"):
            with self.subTest(name=name):
                self.assertIn('data-edge-id="decide_step"', read(DIAGRAM / name))

    def test_two_dark_crops_split_the_hand_diagram(self) -> None:
        def viewbox(name: str) -> tuple[float, float, float, float]:
            svg = read(DIAGRAM / name)
            match = re.search(r'viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"', svg)
            self.assertIsNotNone(match, name)
            return tuple(float(value) for value in match.groups())  # type: ignore[return-value]

        _, _, _, full_h = viewbox(DARK + ".svg")
        cx, cy, cw, ch = viewbox("incremental-contract-dark.svg")
        sx, sy, sw, sh = viewbox("incremental-state-dark.svg")
        self.assertEqual((cx, cy), (0.0, 0.0))
        self.assertEqual(sx, 0.0)
        self.assertEqual(ch, sy, "contract must end where the state graph starts")
        self.assertEqual(ch + sh, full_h, "the two crops must cover the full canvas")
        self.assertEqual(cw, sw)

    def test_html_titles_are_exact(self) -> None:
        self.assertEqual(title_of(read(DIAGRAM / (LIGHT + ".html"))), LIGHT_TITLE)
        self.assertEqual(title_of(read(DIAGRAM / (DARK + ".html"))), DARK_TITLE)

    def test_html_embeds_exactly_one_copy_of_the_svg(self) -> None:
        for stem in (LIGHT, DARK):
            with self.subTest(stem=stem):
                html_text = read(DIAGRAM / (stem + ".html"))
                self.assertEqual(html_text.count("<svg"), 1)
                self.assertEqual(embedded_svg(html_text), read(DIAGRAM / (stem + ".svg")))

    def test_no_domain_tokens_leak_into_the_artifacts(self) -> None:
        for name in FILES[1:]:
            with self.subTest(name=name):
                low = read(DIAGRAM / name).lower()
                for token in BAD_TOKENS:
                    self.assertNotIn(token, low)


class DiagramReproducibilityTest(unittest.TestCase):
    def test_generator_reproduces_committed_artifacts_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            shutil.copy2(DIAGRAM / GEN, work / GEN)
            outputs = []
            for _ in range(2):
                subprocess.run(
                    [sys.executable, GEN],
                    cwd=work,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                outputs.append({
                    name: (work / name).read_bytes()
                    for name in FILES[1:]
                })
            self.assertEqual(outputs[0], outputs[1], "generator is not deterministic")
            for name in FILES[1:]:
                with self.subTest(name=name):
                    self.assertEqual(outputs[0][name], (DIAGRAM / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
