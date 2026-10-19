"""Contract tests for the family entry point ``pdca-entry``.

The entry skill is a router, not a cycle: its text must name exactly the
family contracts, state the precedence, and hand off without duplicating a
contract.  The runner it ships must be the same file as everywhere else.

Run:
    python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parents[1]
SKILLS = SKILL_DIR.parent
SKILL = SKILL_DIR / "SKILL.md"
RUNNER = SKILL_DIR / "assets/agents/pdca-orchestrator.md"

FAMILY = ("pdca", "pdca-coder", "pdca-dotnet", "pdca-collection", "pdca-incremental")
CYCLE = ("pdca", "pdca-coder", "pdca-dotnet")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(path: Path) -> dict[str, str]:
    text = read(path)
    end = text.find("\n---", 3)
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip().strip('"')
    return data


def routing_section() -> str:
    text = read(SKILL)
    start = text.index("## Routing decision")
    end = text.index("## Handoff")
    return text[start:end]


class FrontmatterTest(unittest.TestCase):
    def test_name_matches_folder(self):
        self.assertEqual("pdca-entry", frontmatter(SKILL).get("name"))

    def test_description_names_every_contract_and_the_trigger(self):
        description = frontmatter(SKILL)["description"]
        for name in FAMILY:
            with self.subTest(contract=name):
                self.assertIn(name, description)
        for phrase in ("by the cycle", "via PDCA", "по циклу", "через PDCA"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, description)


def table_targets() -> list[str]:
    """The contract column of rows 1-5, in document order."""
    out: list[str] = []
    for line in routing_section().splitlines():
        match = re.match(r"^\|\s*[1-5]\s*\|.*\|\s*`(pdca[a-z-]*)`\s*\|\s*$", line)
        if match:
            out.append(match.group(1))
    return out


class AutoinvokeTest(unittest.TestCase):
    """Only the umbrella is advertised to the model; the rest load by explicit ID."""

    def test_only_entry_is_advertised(self):
        head = read(SKILL)[:read(SKILL).find("\n---", 3)]
        self.assertNotIn("opencode/autoinvoke: false", head)
        for name in FAMILY:
            if name == "pdca-entry":
                continue
            with self.subTest(contract=name):
                text = read(SKILLS / name / "SKILL.md")
                head = text[:text.find("\n---", 3)]
                self.assertIn("opencode/autoinvoke: false", head,
                              "%s must not be model-autoinvokable" % name)
                self.assertIn("disable-model-invocation: true", head)

    def test_variants_require_explicit_naming(self):
        for name in FAMILY:
            if name == "pdca-entry":
                continue
            with self.subTest(contract=name):
                description = frontmatter(SKILLS / name / "SKILL.md")["description"]
                self.assertIn("explicitly name", description)

    def test_entry_catches_the_former_phrase_triggers(self):
        description = frontmatter(SKILL)["description"]
        for phrase in ("список задач", "milestone", "инкрементами",
                       "маленькими шагами", "по циклу"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, description)


class RoutingRuleTest(unittest.TestCase):
    def test_precedence_is_explicit(self):
        self.assertEqual(
            ["pdca-collection", "pdca-incremental", "pdca-dotnet", "pdca-coder", "pdca"],
            table_targets(),
            "routing precedence drifted: collection < incremental < dotnet < coder < pdca",
        )

    def test_explicit_contract_wins(self):
        self.assertRegex(routing_section(), r"names a contract explicitly")
        self.assertRegex(routing_section(), r"verbatim")

    def test_a_batch_without_parallelism_stays_collection(self):
        section = routing_section()
        self.assertIn("parallelism is optional", section)
        self.assertIn("degrades to a single sequential group", section)
        self.assertIn("One shared goal/metric", section)
        self.assertIn("Do not choose incremental merely because a batch is serialized", section)

    def test_size_alone_is_not_a_signal(self):
        self.assertIn("Size alone is not a signal", routing_section())
        self.assertIn("pdca-incremental", routing_section())

    def test_campaign_and_collection_are_not_variants(self):
        text = read(SKILL)
        self.assertIn("not a sixth cycle contract", text)
        for phrase in ("pdca-collection", "pdca-incremental", "top-level"):
            self.assertIn(phrase, text)


class HandoffTest(unittest.TestCase):
    def test_both_modes_are_described(self):
        text = read(SKILL)
        self.assertIn("Normal mode", text)
        self.assertIn("Autonomous mode", text)
        self.assertIn("host's skill mechanism", text)
        self.assertIn("selected_variant", text)

    def test_no_rerouting_after_the_contract_starts(self):
        self.assertIn("do not re-route", read(SKILL))


class NotACycleTest(unittest.TestCase):
    def test_no_cycle_rules_are_duplicated(self):
        text = read(SKILL)
        for marker in ("## Transition gates", "Gate 1", "no fourth attempt",
                       "status file is the only", "PLAN → DO — only if"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, text)


class PortabilityTest(unittest.TestCase):
    """Contract bodies are host-agnostic; host paths live in the install adapters."""

    FORBIDDEN = ("~/.config/opencode", ".opencode/", "opencode.json",
                 "restart opencode", "subagent_depth", "opencode default")

    def test_contract_bodies_carry_no_host_specifics(self):
        for name in FAMILY:
            with self.subTest(contract=name):
                text = read(SKILLS / name / "SKILL.md")
                body = text[text.find("\n---", 3):]
                for token in self.FORBIDDEN:
                    self.assertNotIn(token, body)

    def test_manual_only_flag_is_portable(self):
        for name in FAMILY:
            if name == "pdca-entry":
                continue
            with self.subTest(contract=name):
                text = read(SKILLS / name / "SKILL.md")
                head = text[:text.find("\n---", 3)]
                self.assertIn("disable-model-invocation: true", head,
                              "%s needs the portable manual-only flag" % name)

    def test_install_docs_name_the_supported_hosts(self):
        install = read(REPO / "docs/install.md")
        for host in ("OpenCode", "Claude Code", "Codex"):
            with self.subTest(host=host):
                self.assertIn(host, install)


class ArtifactsTest(unittest.TestCase):
    def test_target_contracts_exist_and_are_named(self):
        for name in FAMILY:
            with self.subTest(contract=name):
                path = SKILLS / name / "SKILL.md"
                self.assertTrue(path.is_file(), "%s/SKILL.md missing" % name)
                self.assertEqual(name, frontmatter(path).get("name"))

    def test_runner_is_shipped_and_identical_to_the_family(self):
        self.assertTrue(RUNNER.is_file(), "assets/agents/pdca-orchestrator.md missing")
        self.assertEqual("pdca-orchestrator", frontmatter(RUNNER).get("name"))
        expected = (SKILLS / "pdca/assets/agents/pdca-orchestrator.md").read_bytes()
        self.assertEqual(expected, RUNNER.read_bytes(), "runner copy drifted")

    def test_no_model_id_anywhere_in_the_skill(self):
        for path in SKILL_DIR.rglob("*.md"):
            with self.subTest(file=str(path)):
                self.assertNotRegex(read(path), r"(?m)^\s*model\s*:")


if __name__ == "__main__":
    unittest.main()
