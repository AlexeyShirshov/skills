"""Contract tests for the family entry point ``pdca-entry``.

The entry skill is a router, not a cycle: its text must name exactly the
family contracts, state the precedence, and hand off without duplicating a
contract.  The runner it ships must be the same file as everywhere else.

Run:
    python3 -m unittest discover -s skills/pdca-entry/tests -p 'test_*.py' -v
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


def norm(text: str) -> str:
    return " ".join(text.split())


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
        for phrase in ("by the cycle", "via PDCA", "run PDCA"):
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
        for phrase in ("task list", "milestone", "increments", "campaign"):
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


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


class CompositionTest(unittest.TestCase):
    """Collection units may be cycles or campaigns; the form is not the variant."""

    def test_priority_rows_are_unchanged(self):
        rows: list[tuple[str, str]] = []
        for line in routing_section().splitlines():
            match = re.match(r"^\|\s*([0-5])\s*\|([^|]*)\|[^|]*\|\s*$", line)
            if match:
                rows.append((match.group(1), match.group(2)))
        self.assertEqual(["0", "1", "2", "3", "4", "5"], [num for num, _ in rows],
                         "the routing table gained or lost a priority row")
        expected = [
            ("0", "names a contract explicitly"),
            ("1", "known list"),
            ("2", "verifiable goal"),
            ("3", ".NET / C#"),
            ("4", "another stack"),
        ]
        positions: list[int] = []
        for number, label in expected:
            with self.subTest(row=number):
                hits = [i for i, (num, signal) in enumerate(rows)
                        if num == number and label.lower() in signal.lower()]
                self.assertTrue(hits, "routing row %s no longer says %r" % (number, label))
                positions.append(hits[0])
        self.assertEqual(sorted(positions), positions, "routing priority order drifted")

    def test_execution_kind_is_not_selected_variant(self):
        text = norm(read(SKILL))
        for token in ("execution_kind", "selected_variant"):
            with self.subTest(token=token):
                self.assertIn(token, text)
        self.assertRegex(
            text.lower(),
            r"different fields|not the same field|not interchangeable|"
            r"different things|different fields",
            "the entry must say execution_kind and selected_variant are different fields",
        )

    def test_a_batch_may_contain_campaign_units(self):
        hits = [
            s for s in sentences(norm(read(SKILL)))
            if re.search(r"\bbatch\b|\bcollections?\b", s, re.I)
            and re.search(r"\bcampaigns?\b", s, re.I)
            and re.search(r"contain|include|units?\b", s, re.I)
        ]
        self.assertTrue(hits, "the entry must say a collection/batch may contain campaign units")

    def test_medium_primary_hands_off_to_the_cheap_primary(self):
        hits = [
            s for s in sentences(norm(read(SKILL)))
            if re.search(r"handoff|hands? off", s, re.I)
            and re.search(r"cheap primary", s, re.I)
            and re.search(r"medium|strong", s, re.I)
        ]
        self.assertTrue(
            hits,
            "the entry must state an explicit handoff from a medium/strong primary "
            "to the cheap primary",
        )

    def test_no_rerouting_after_the_contract_starts(self):
        self.assertIn("re-rout", norm(read(SKILL)).lower())


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


class InstallAdapterTest(unittest.TestCase):
    """The install prompt and docs must branch on the OpenCode major, not mix keys."""

    def setUp(self) -> None:
        self.prompt = read(REPO / "docs/install-prompt.md")
        self.install = read(REPO / "docs/install.md")

    def test_prompt_takes_and_detects_the_major(self) -> None:
        for marker in ("OPENCODE_MAJOR=auto", "OPENCODE_MAJOR=<auto | 1 | 2>",
                       "opencode --version", "opencode_major"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.prompt)

    def test_v1_branch_uses_v1_keys(self) -> None:
        for marker in ('"subagent_depth": 3', "`permission` map", "`task`",
                       "opencode agent list"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.prompt)

    def test_v2_branch_uses_v2_keys(self) -> None:
        for marker in ("experimental.subagent_depth", "action `subagent`",
                       "`permissions`", "opencode debug agents"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.prompt)

    def test_install_docs_document_both_adapters(self) -> None:
        for marker in ("OpenCode V1", "subagent_depth", "permission",
                       "opencode agent list", "OPENCODE_MAJOR"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.install)


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


class CampaignCriteriaTest(unittest.TestCase):
    """The entry delegates campaign criteria instead of restating them.

    The canonical discriminator lives in ``pdca-incremental`` §When to choose;
    the entry only points at it and states who decides a unit's form.
    """

    def test_campaign_criteria_are_delegated_to_incremental(self):
        text = norm(read(SKILL))
        self.assertIn(
            "canonical in `pdca-incremental` §When to choose",
            text,
            "the entry must point at the canonical campaign criteria instead of "
            "restating them",
        )
        for criterion in (
            "the goal is checkable",
            "the path is unknown",
            "the steps are information-dependent",
            "a whole-volume plan would be a stub",
        ):
            with self.subTest(criterion=criterion):
                self.assertIn(
                    criterion,
                    text,
                    f"the entry dropped a campaign criterion: {criterion!r}",
                )

    def test_collection_plan_decides_each_units_form_of_execution(self):
        self.assertIn(
            "PLAN of the collection decides each unit's form of execution",
            norm(read(SKILL)),
            "the entry must name the collection PLAN as the decider of "
            "`execution_kind`, not the runner or the task text",
        )

    def test_shared_goal_versus_independent_goals_is_stated(self):
        section = norm(routing_section())
        for phrase in (
            "One shared goal/metric",
            "even across a known list",
            "A single shared goal whose whole plan is already known",
            "Do not choose incremental merely because a batch is serialized",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(
                    phrase,
                    section,
                    f"the routing decision lost the batch-vs-campaign "
                    f"discriminator: {phrase!r}",
                )


if __name__ == "__main__":
    unittest.main()
