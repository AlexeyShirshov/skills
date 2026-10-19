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
    python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
# Canonical repo: <root>/config/skills; published pack: <root>/opencode.
SKILLS = REPO / "opencode"
if not SKILLS.is_dir():
    SKILLS = REPO / "skills"

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
        self.assertIn("вариант определяет коллекция", text)
        self.assertIn("selected_variant", text)

    def test_incremental_chooses_and_passes_the_variant(self):
        text = norm(read(SKILLS / "pdca-incremental/SKILL.md"))
        self.assertIn("вариант шага определяет кампания", text)
        self.assertIn("selected_variant", text)

    def test_each_cycle_contract_names_itself_in_the_handoff(self):
        for name in CYCLE_SKILLS:
            with self.subTest(contract=name):
                self.assertIn("selected_variant: %s" % name,
                              norm(read(SKILLS / name / "SKILL.md")))


def skill_permission_rules() -> list:
    """V2 `permissions:` rules of the host orchestrator (ordered {action,resource,effect})."""
    block = read(HOST_ORCHESTRATOR)
    block = block[block.find("---") + 3:block.find("\n---", 3)]
    rules: list = []
    current: dict | None = None
    in_list = False
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0:
            in_list = stripped == "permissions:"
            current = None
            continue
        if not in_list:
            continue
        if stripped.startswith("- "):
            current = {}
            rules.append(current)
            stripped = stripped[2:]
        if current is None:
            continue
        key, _, value = stripped.partition(":")
        current[key.strip().strip("\"'")] = value.strip().strip("\"'")
    return rules


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class HostPermissionTest(unittest.TestCase):
    def test_driver_may_load_cycle_skills_and_not_brainstorming(self):
        for name in CYCLE_SKILLS:
            with self.subTest(skill=name):
                self.assertEqual("allow", self.effective("skill", name))
        self.assertEqual("deny", self.effective("skill", "brainstorming"))

    def effective(self, action: str, resource: str) -> str:
        """Last matching rule wins; no match falls back to `ask`."""
        effect = "ask"
        for rule in skill_permission_rules():
            if self._match(rule.get("action", ""), action) and \
               self._match(rule.get("resource", ""), resource):
                effect = rule.get("effect", "ask")
        return effect

    @staticmethod
    def _match(pattern: str, value: str) -> bool:
        regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in pattern)
        return re.fullmatch(regex, value) is not None


if __name__ == "__main__":
    unittest.main()
