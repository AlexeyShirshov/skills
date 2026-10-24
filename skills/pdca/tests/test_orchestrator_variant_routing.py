"""Contract guard: routing knowledge lives in skills, not in the driver agent.

`pdca-orchestrator` is a cheap dispatcher. It loads the cycle contract named in
`selected_variant` and never classifies the task by its content. The choice is made
by the skill that dispatches it:

* `pdca-entry` — a standalone task (its routing table);
* `pdca-collection` — per task;
* `pdca-incremental` — per step.

The tests pin that split so the routing rule cannot creep back into the agent:

* the driver has no variant classification, no default and a fail-closed rule;
* the entry skill owns the routing table and its precedence;
* collection/incremental state that they choose and pass `selected_variant`;
* the autonomous handoff of every cycle contract names its own `selected_variant`.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
# This repo: <root>/skills; an opencode-config checkout: <root>/config/skills.
SKILLS = REPO / "skills"
if not SKILLS.is_dir():
    SKILLS = REPO / "config" / "skills"

HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"
HOST_ORCHESTRATOR = (CONFIG / "agents/pdca-orchestrator.md") if CONFIG else None

ORCHESTRATOR = SKILLS / "pdca/assets/agents/pdca-orchestrator.md"
ENTRY = SKILLS / "pdca-entry/SKILL.md"
CYCLE_SKILLS = ("pdca", "pdca-coder", "pdca-dotnet")


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


class DriverIsThinTest(unittest.TestCase):
    def test_description_does_not_advertise_classification(self):
        description = frontmatter(ORCHESTRATOR)["description"]
        self.assertIn("selected_variant", description)
        for phrase in ("picks the cycle variant", "→ `pdca-dotnet`", "other code",
                       "otherwise `pdca`"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, description)

    def test_no_variant_classification_in_the_agent(self):
        text = norm(read(ORCHESTRATOR))
        for phrase in ("Variant selection", "a `.NET`/C# task", "another stack",
                       "default to `pdca`", "otherwise (a task with a verifiable result"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, text)

    def test_missing_contract_fails_closed(self):
        text = norm(read(ORCHESTRATOR))
        self.assertIn("given, not chosen", text)
        self.assertIn("selected_variant", text)
        self.assertIn("fail closed", text)
        self.assertIn("do not pick a variant yourself", text)


class RunnerTwoModesTest(unittest.TestCase):
    """The same dispatcher runs in exactly two modes; no new layer is introduced."""

    def test_runner_names_both_execution_modes(self):
        text = norm(read(ORCHESTRATOR)).lower()
        for phrase in ("execution_kind", "selected_variant", "collection-lane",
                       "dispatch", "fail closed"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        for mode in ("step orchestrator", "collection-lane"):
            with self.subTest(mode=mode):
                self.assertIn(mode, text)

    def test_runner_does_not_add_layers_or_a_model(self):
        text = norm(read(ORCHESTRATOR)).lower()
        for phrase in ("campaign-agent", "cycle-agent"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, text)
        self.assertNotRegex(read(ORCHESTRATOR), r"(?m)^\s*model\s*:")


class EntryOwnsRoutingTest(unittest.TestCase):
    def test_entry_routing_table_precedence(self):
        text = read(ENTRY)
        section = text[text.index("## Routing decision"):text.index("## Handoff")]
        targets = [
            match.group(1)
            for line in section.splitlines()
            if (match := re.match(r"^\|\s*[1-5]\s*\|.*\|\s*`(pdca[a-z-]*)`\s*\|\s*$", line))
        ]
        self.assertEqual(
            ["pdca-collection", "pdca-incremental", "pdca-dotnet", "pdca-coder", "pdca"],
            targets,
        )

    def test_entry_passes_the_decision_on(self):
        self.assertIn("selected_variant", read(ENTRY))


class DispatchingSkillsChooseTest(unittest.TestCase):
    def test_collection_chooses_and_passes_the_variant(self):
        text = norm(read(SKILLS / "pdca-collection/SKILL.md"))
        self.assertIn("the collection decides the variant", text)
        self.assertIn("selected_variant", text)

    def test_incremental_chooses_and_passes_the_variant(self):
        text = norm(read(SKILLS / "pdca-incremental/SKILL.md"))
        self.assertIn("the campaign determines the step's variant", text)
        self.assertIn("selected_variant", text)

    def test_each_cycle_contract_names_itself_in_the_handoff(self):
        for name in CYCLE_SKILLS:
            with self.subTest(contract=name):
                self.assertIn("selected_variant: %s" % name,
                              norm(read(SKILLS / name / "SKILL.md")))


def _nested(block: str) -> dict:
    """Indentation parser for the frontmatter subset used by V1 `permission:` maps."""
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, sep, value = raw.strip().partition(":")
        if not sep:
            continue
        key = key.strip().strip("\"'")
        value = value.strip().strip("\"'")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if value == "":
            node: dict = {}
            stack[-1][1][key] = node
            stack.append((indent, node))
        else:
            stack[-1][1][key] = value
    return root


def skill_permission_map() -> dict:
    """V1 `permission.skill` map of the host orchestrator (pattern -> effect)."""
    text = read(HOST_ORCHESTRATOR)
    block = text[3:text.find("\n---", 3)]
    permission = _nested(block).get("permission")
    skill = permission.get("skill") if isinstance(permission, dict) else None
    return skill if isinstance(skill, dict) else {}


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class HostPermissionTest(unittest.TestCase):
    def test_driver_may_load_cycle_skills(self):
        # The driver loads the contract named in `selected_variant`, so the cycle
        # skills must be loadable. A blanket `skill: "*"` allow is the host's
        # shape here; the per-agent `brainstorming: deny` that the global policy
        # asks of skill-allowing agents belongs to the host runner file
        # (`config/agents/pdca-orchestrator.md`), not to this repo.
        for name in CYCLE_SKILLS:
            with self.subTest(skill=name):
                self.assertEqual("allow", self.skill_effect(name))

    def skill_effect(self, resource: str) -> str:
        """V1 last-match within the `skill` map; no match falls back to its `*`."""
        skill = skill_permission_map()
        effect = skill.get("*", "ask")
        for pattern, value in skill.items():
            if self._match(pattern, resource):
                effect = value
        return effect

    @staticmethod
    def _match(pattern: str, value: str) -> bool:
        regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in pattern)
        return re.fullmatch(regex, value) is not None


if __name__ == "__main__":
    unittest.main()
