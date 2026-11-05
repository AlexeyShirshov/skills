"""Guards for the Gherkin scenario suite of the `pdca-collection` form.

The scenarios themselves are human-run (see ``tests/scenarios.feature``); what
this module enforces is that the file stays a usable specification:

* one ``Feature``, every scenario carries ``Given``/``When``/``Then``;
* every matrix id appears exactly once and matches its tag;
* every scenario is classified as ``@pinned`` (a guard exists) or ``@uncovered``;
* every ``# source:`` anchor resolves to a real heading of a real file;
* every ``# test:`` reference resolves to a real test method, and only a
  ``@pinned`` scenario may carry one.

A stale mapping is worse than none: it claims coverage that does not exist.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
FEATURE = SKILL / "tests/scenarios.feature"

EXPECTED_IDS = (
    *(f"a{i}" for i in range(1, 4)),
    *(f"b{i}" for i in range(1, 4)),
    *(f"c{i}" for i in range(1, 5)),
    *(f"d{i}" for i in range(1, 5)),
    *(f"e{i}" for i in range(1, 5)),
    *(f"r{i}" for i in range(1, 3)),
    *(f"s{i}" for i in range(1, 5)),
)

STEP = re.compile(r"^(Given|When|Then|And|But)\s")
HEADING = re.compile(r"^#{2,4}\s+(.*)$")
SOURCE = re.compile(r"^#\s*source:\s*(.+)$")
TEST = re.compile(r"^#\s*test:\s*(.+)$")
SCENARIO = re.compile(r"^Scenario:\s*(.+)$")
REPO = SKILL.parent.parent


def norm_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


class Scenario:
    def __init__(self, title: str, tags: list[str], rule: str) -> None:
        self.title = title
        self.tags = tags
        self.rule = rule
        self.steps: list[str] = []
        self.sources: list[str] = []
        self.tests: list[str] = []

    @property
    def id(self) -> str:
        return self.title.split(" ", 1)[0]

    @property
    def pinned(self) -> bool:
        return "@pinned" in self.tags

    @property
    def uncovered(self) -> bool:
        return "@uncovered" in self.tags


def parse(text: str) -> tuple[list[str], list[Scenario]]:
    features: list[str] = []
    scenarios: list[Scenario] = []
    tags: list[str] = []
    current: Scenario | None = None
    rule = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Feature:"):
            features.append(line)
            current = None
            continue
        if line.startswith("Rule:"):
            rule = line[len("Rule:"):].strip()
            current = None
            continue
        if line.startswith("@"):
            tags = line.split()
            continue
        match = SCENARIO.match(line)
        if match:
            current = Scenario(match.group(1).strip(), tags, rule)
            scenarios.append(current)
            tags = []
            continue
        if current is not None:
            match = SOURCE.match(line)
            if match:
                current.sources.append(match.group(1).strip())
                continue
            match = TEST.match(line)
            if match:
                current.tests.append(match.group(1).strip())
                continue
            if STEP.match(line):
                current.steps.append(STEP.match(line).group(1))
    return features, scenarios


class ScenarioFeatureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.features, cls.scenarios = parse(FEATURE.read_text(encoding="utf-8"))

    def test_there_is_exactly_one_feature(self) -> None:
        self.assertEqual(1, len(self.features), "one feature per contract")

    def test_every_matrix_id_appears_once_and_matches_its_tag(self) -> None:
        ids = [s.id for s in self.scenarios]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate scenario id in {ids}")
        self.assertEqual(sorted(EXPECTED_IDS), sorted(ids))
        for scenario in self.scenarios:
            self.assertIn(f"@{scenario.id}", scenario.tags, scenario.title)

    def test_every_scenario_has_the_three_step_kinds(self) -> None:
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario.id):
                for kind in ("Given", "When", "Then"):
                    self.assertIn(kind, scenario.steps, f"{scenario.id} lacks {kind}")
                self.assertGreaterEqual(len(scenario.steps), 3)

    def test_every_scenario_is_classified(self) -> None:
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario.id):
                self.assertNotEqual(
                    scenario.pinned, scenario.uncovered,
                    f"{scenario.id} must be exactly one of @pinned/@uncovered",
                )

    def test_every_source_anchor_resolves(self) -> None:
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario.id):
                self.assertTrue(scenario.sources, f"{scenario.id} has no # source:")
                for spec in scenario.sources:
                    path_text, _, heading = spec.partition(" §")
                    path = REPO / path_text
                    self.assertTrue(path.is_file(), f"{scenario.id}: missing {path_text}")
                    if not heading:
                        continue
                    headings = {
                        norm_heading(m.group(1))
                        for m in (HEADING.match(l) for l in path.read_text(encoding="utf-8").splitlines())
                        if m
                    }
                    self.assertIn(
                        norm_heading(heading), headings,
                        f"{scenario.id}: §{heading} not found in {path_text}",
                    )

    def test_pinned_scenarios_cite_existing_tests(self) -> None:
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario.id):
                if scenario.uncovered:
                    self.assertFalse(
                        scenario.tests,
                        f"{scenario.id} is @uncovered but cites a test",
                    )
                    continue
                self.assertTrue(
                    scenario.tests, f"{scenario.id} is @pinned but cites no test"
                )
                for ref in scenario.tests:
                    path_text, _, target = ref.partition("::")
                    path = REPO / path_text
                    self.assertTrue(path.is_file(), f"{scenario.id}: missing {path_text}")
                    self.assertIn(
                        "::", ref, f"{scenario.id}: test ref needs file::Class.method"
                    )
                    klass, _, method = target.partition(".")
                    self.assertTrue(method, f"{scenario.id}: {target} is not Class.method")
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                    found = {
                        (node.name, fn.name)
                        for node in tree.body
                        if isinstance(node, ast.ClassDef)
                        for fn in node.body
                        if isinstance(fn, ast.FunctionDef)
                    }
                    self.assertIn(
                        (klass, method), found,
                        f"{scenario.id}: {klass}.{method} not found in {path_text}",
                    )

    def test_the_current_rules_and_the_history_are_split(self) -> None:
        # One source of truth for the rules; the rubric and samples stay as history.
        self.assertFalse((SKILL / "tests/scenarios.md").exists())
        self.assertTrue((SKILL / "tests/scenarios-history.md").is_file())


if __name__ == "__main__":
    unittest.main()
