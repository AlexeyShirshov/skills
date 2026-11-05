"""Artifact and reproducibility guards for the pdca-incremental hand diagram.

Reads the generated files under ``skills/pdca-incremental/assets/diagram/`` and
asserts the family invariants: light/dark titles, required labels, XML well-formedness,
one byte-equal inline SVG per HTML and no domain tokens.  The diagram ships in two
languages, Russian (unsuffixed) and English (``-en``), exactly like ``pdca``.

Reproducibility is proven empirically: only the generator is copied into a temporary
directory, executed twice per language with the current Python and compared
byte-for-byte with the committed artifacts.

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
CROPS = ("incremental-contract-dark", "incremental-state-dark")
SUFFIXES = ("", "-en")


def files_for(suffix: str) -> tuple[str, ...]:
    return (
        GEN,
        LIGHT + suffix + ".svg", LIGHT + suffix + ".html",
        DARK + suffix + ".svg", DARK + suffix + ".html",
        *(crop + suffix + ".svg" for crop in CROPS),
    )


FILES = (GEN, *(name for suffix in SUFFIXES for name in files_for(suffix)[1:]))
LIGHT_TITLE = "pdca-incremental — campaign in steps"
DARK_TITLE = "pdca-incremental — campaign in steps (dark theme)"
RU_LIGHT_TITLE = "pdca-incremental — кампания шагами"
RU_DARK_TITLE = "pdca-incremental — кампания шагами (тёмная тема)"
LABELS = (
    "BOOTSTRAP", "PLAN", "STEP N", "ACCEPT", "DECIDE", "STOP",
    "Discover · gap map", "Brief · six blocks", "Ranked seed",
    "P · PLAN", "D · DO", "C · CHECK", "A · ACT",
    # the step exit is the base step boundary, not a step-kind table
    "Step exit", "accept · revise · blocked → ACT",
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
RU_LABELS = (
    "Оркестратор · cheap — cycle-control / campaign-control",
    "Граф состояний кампании",
    "Обнаружение · пробелы",
    "Ранжированное семя",
    "Бриф · шесть блоков",
    "Приёмка · цели",
    "Цель достигнута?",
    "Следующий seed",
    "Маршрут",
    "Выход шага",
    "принять · ревизия · blocked → ACT",
    "Вердикт",
    "дешёвая ступень",
    "средняя ступень",
    "следующий шаг · baseline = принятый",
    "исправление · N",
    "финализировано ACT · met · unreachable · blocked · stopped",
    "проверка — необязательный интеграционный гейт: цель = гейт, baseline не двигает",
    "точка возобновления в статусе",
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


def stems(suffix: str) -> tuple[str, str]:
    return LIGHT + suffix, DARK + suffix


class DiagramArtifactsTest(unittest.TestCase):
    def test_all_files_exist(self) -> None:
        for name in FILES:
            with self.subTest(name=name):
                self.assertTrue((DIAGRAM / name).is_file(), "%s missing" % name)

    def test_svgs_are_well_formed(self) -> None:
        for suffix in SUFFIXES:
            for stem in stems(suffix):
                name = stem + ".svg"
                with self.subTest(name=name):
                    root = ET.parse(DIAGRAM / name).getroot()
                    self.assertTrue(root.tag.endswith("svg"))
                    self.assertTrue(root.get("viewBox"))

    def test_english_svgs_carry_the_step_loop_labels(self) -> None:
        for name in (LIGHT + "-en.svg", DARK + "-en.svg"):
            with self.subTest(name=name):
                svg = read(DIAGRAM / name)
                for label in LABELS:
                    self.assertIn(label, svg)

    def test_russian_svgs_carry_the_step_loop_labels(self) -> None:
        for name in (LIGHT + ".svg", DARK + ".svg"):
            with self.subTest(name=name):
                svg = read(DIAGRAM / name)
                for label in RU_LABELS:
                    self.assertIn(label, svg)

    def test_russian_svgs_carry_no_english_prose(self) -> None:
        # A missing translation falls back to the English source string; these
        # probes catch the most visible ones instead of letting them slip through.
        english_once = (
            "Campaign graph", "Discover · gap map", "Goal + recipe",
            "Step exit", "next step · baseline = accepted",
            "one writer · status write",
        )
        for name in (LIGHT + ".svg", DARK + ".svg"):
            with self.subTest(name=name):
                svg = read(DIAGRAM / name)
                for probe in english_once:
                    self.assertNotIn(probe, svg, f"untranslated {probe!r}")

    def test_the_defining_feedback_edge_exists(self) -> None:
        for suffix in SUFFIXES:
            for stem in stems(suffix):
                name = stem + ".svg"
                with self.subTest(name=name):
                    self.assertIn('data-edge-id="decide_plan"', read(DIAGRAM / name))

    def test_the_stale_step_kind_catalogue_is_gone(self) -> None:
        for suffix in SUFFIXES:
            for stem in stems(suffix):
                name = stem + ".svg"
                with self.subTest(name=name):
                    svg = read(DIAGRAM / name)
                    for label in STALE_LABELS:
                        self.assertNotIn(label, svg, f"stale step-kind label {label!r}")

    def test_the_repair_feedback_edge_exists(self) -> None:
        for suffix in SUFFIXES:
            for stem in stems(suffix):
                name = stem + ".svg"
                with self.subTest(name=name):
                    self.assertIn('data-edge-id="decide_step"', read(DIAGRAM / name))

    def test_a_step_that_cannot_finish_reaches_act_not_stop(self) -> None:
        """DO failure is an ACT outcome: it never opens a second STOP path."""
        finalised = {"": "финализировано ACT", "-en": "ACT-finalized"}
        for suffix in SUFFIXES:
            for stem in stems(suffix):
                name = stem + ".svg"
                text = read(DIAGRAM / name)
                with self.subTest(name=name):
                    self.assertIn('data-edge-id="step_acc"', text)
                    self.assertIn("blocked (DO → ACT)", text)
                    # STOP hangs off the campaign decision only, never off STEP
                    self.assertNotIn('data-edge-id="step_stop"', text)
                    self.assertEqual(1, text.count('data-edge-id="decide_stop"'))
                    # the campaign STOP is finalized in ACT, not a parallel terminal
                    self.assertIn(finalised[suffix], text)

    def test_two_dark_crops_split_the_hand_diagram(self) -> None:
        def viewbox(name: str) -> tuple[float, float, float, float]:
            svg = read(DIAGRAM / name)
            match = re.search(r'viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"', svg)
            self.assertIsNotNone(match, name)
            return tuple(float(value) for value in match.groups())  # type: ignore[return-value]

        for suffix in SUFFIXES:
            with self.subTest(suffix=suffix or "ru"):
                _, _, _, full_h = viewbox(DARK + suffix + ".svg")
                cx, cy, cw, ch = viewbox("incremental-contract-dark" + suffix + ".svg")
                sx, sy, sw, sh = viewbox("incremental-state-dark" + suffix + ".svg")
                self.assertEqual((cx, cy), (0.0, 0.0))
                self.assertEqual(sx, 0.0)
                self.assertEqual(ch, sy, "contract must end where the state graph starts")
                self.assertEqual(ch + sh, full_h, "the two crops must cover the full canvas")
                self.assertEqual(cw, sw)

    def test_html_titles_are_exact(self) -> None:
        self.assertEqual(title_of(read(DIAGRAM / (LIGHT + ".html"))), RU_LIGHT_TITLE)
        self.assertEqual(title_of(read(DIAGRAM / (DARK + ".html"))), RU_DARK_TITLE)
        self.assertEqual(title_of(read(DIAGRAM / (LIGHT + "-en.html"))), LIGHT_TITLE)
        self.assertEqual(title_of(read(DIAGRAM / (DARK + "-en.html"))), DARK_TITLE)

    def test_html_embeds_exactly_one_copy_of_the_svg(self) -> None:
        for suffix in SUFFIXES:
            for stem in stems(suffix):
                with self.subTest(stem=stem):
                    html_text = read(DIAGRAM / (stem + ".html"))
                    self.assertEqual(html_text.count("<svg"), 1)
                    self.assertEqual(embedded_svg(html_text), read(DIAGRAM / (stem + ".svg")))

    def test_no_domain_tokens_leak_into_the_artifacts(self) -> None:
        for name in FILES:
            if name == GEN:
                continue
            with self.subTest(name=name):
                low = read(DIAGRAM / name).lower()
                for token in BAD_TOKENS:
                    self.assertNotIn(token, low)


class DiagramReproducibilityTest(unittest.TestCase):
    def test_generator_reproduces_committed_artifacts_deterministically(self) -> None:
        for suffix, args in (("", []), ("-en", ["--lang", "en"])):
            with self.subTest(language=suffix or "ru"):
                with tempfile.TemporaryDirectory() as tmp:
                    work = Path(tmp)
                    shutil.copy2(DIAGRAM / GEN, work / GEN)
                    outputs = []
                    for _ in range(2):
                        subprocess.run(
                            [sys.executable, GEN, *args],
                            cwd=work,
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        outputs.append({
                            name: (work / name).read_bytes()
                            for name in files_for(suffix)[1:]
                        })
                    self.assertEqual(outputs[0], outputs[1], "generator is not deterministic")
                    for name, data in outputs[0].items():
                        with self.subTest(name=name):
                            self.assertEqual(data, (DIAGRAM / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
