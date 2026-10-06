"""Contract guard for the shared cheap driver `pdca-orchestrator` variant selection.

The driver is an LLM subagent, so "it loads the right cycle skill for a task" is a
contract, not code: given a task it must load exactly one of

* `pdca-dotnet` for .NET/C#,
* `pdca-coder` for other code,
* `pdca` otherwise (the default).

These tests pin that contract end to end:

* the three target skills exist and their frontmatter `name` matches the folder,
  so `skill pdca` / `skill pdca-coder` / `skill pdca-dotnet` resolve;
* the orchestrator's `skill` permission may load them (and still denies
  `brainstorming`);
* the documented routing rule lists the variants in precedence order (.NET before
  generic code before the default) and names `pdca` as the default;
* fixture tasks resolve to the skill the documented rule prescribes -- including a
  mixed .NET+other-code task, which must fall through to `pdca-dotnet`.

The rule is read from the agent document, so the document stays the single source
of truth: reordering or rewording the mapping breaks these tests.

Run:
    python3 -m unittest discover -s config/skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ORCHESTRATOR = REPO / "config/agents/pdca-orchestrator.md"
CYCLE_SKILLS = ("pdca", "pdca-coder", "pdca-dotnet")

ROUTING_HEADER = "**Выбор варианта цикла.**"
ROUTING_END = "**Группа `pdca-collection`.**"
DEFAULT_SKILL = "pdca"

# Signals the driver keys on.  Order matters: `.NET` wins over generic code so a
# mixed task is routed to `pdca-dotnet`.
DOTNET_HINTS = (".net", "c#", "csharp", "dotnet", "ef core", "asp.net")
CODE_HINTS = ("python", "javascript", "typescript", "java ", "go ", "rust",
              "скрипт", "функци", "рефактор", "код")

# (task, skill the rule must prescribe)
FIXTURES = (
    ("Оптимизируй EF Core запрос в .NET сервисе", "pdca-dotnet"),
    ("Почини падение теста в C#-проекте", "pdca-dotnet"),
    ("Порти DotNet-модуль на Python (смешанный случай)", "pdca-dotnet"),
    ("Отрефактори Python-скрипт сборки", "pdca-coder"),
    ("Напиши функцию на JavaScript", "pdca-coder"),
    ("Подготовь план миграции данных", "pdca"),
    ("Собери отчёт по метрикам", "pdca"),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i:j] if j >= 0 else text[i:]


def routing_section() -> str:
    return between(read(ORCHESTRATOR), ROUTING_HEADER, ROUTING_END)


def documented_order() -> list:
    """The `-> skill` targets of the routing bullets, in document order."""
    return re.findall(r"→\s*`([a-z][a-z-]*)`", routing_section())


def documented_default() -> str:
    match = re.search(r"по умолчанию\s+`([a-z][a-z-]*)`", routing_section())
    return match.group(1) if match else ""


def classify(task: str) -> str:
    low = task.lower()
    if any(hint in low for hint in DOTNET_HINTS):
        return "dotnet"
    if any(hint in low for hint in CODE_HINTS):
        return "code"
    return "other"


def resolve(task: str) -> str:
    order = documented_order()
    mapping = {"dotnet": order[0], "code": order[1], "other": documented_default()}
    return mapping[classify(task)]


def skill_name(path: Path) -> str:
    block = between(read(path), "---", "\n---")
    match = re.search(r"(?m)^name:\s*\"?([a-z][a-z-]*)\"?\s*$", block)
    return match.group(1) if match else ""


def skill_permission_block() -> str:
    frontmatter = between(read(ORCHESTRATOR), "---", "\n---")
    i = frontmatter.find("skill:")
    return frontmatter[i:] if i >= 0 else ""


class CycleSkillsExistTest(unittest.TestCase):
    def test_each_target_cycle_skill_exists_and_is_named(self):
        for name in CYCLE_SKILLS:
            with self.subTest(skill=name):
                path = REPO / "config/skills" / name / "SKILL.md"
                self.assertTrue(path.is_file(), "%s missing" % name)
                self.assertEqual(name, skill_name(path))


class OrchestratorMayLoadCycleSkillsTest(unittest.TestCase):
    def test_skill_permission_allows_cycles_and_denies_brainstorming(self):
        block = skill_permission_block()
        self.assertRegex(block, r"\"?\*\"?:\s*allow")
        self.assertRegex(block, r"brainstorming:\s*deny")
        for name in CYCLE_SKILLS:
            with self.subTest(skill=name):
                self.assertNotRegex(block, r"%s:\s*deny" % re.escape(name))

    def test_orchestrator_carries_no_model_id(self):
        self.assertNotRegex(read(ORCHESTRATOR), r"(?m)^\s*model\s*:")


class RoutingRuleTest(unittest.TestCase):
    def test_variants_listed_in_precedence_order(self):
        self.assertEqual(["pdca-dotnet", "pdca-coder", "pdca"], documented_order())

    def test_dotnet_precedes_generic_code(self):
        order = documented_order()
        self.assertLess(order.index("pdca-dotnet"), order.index("pdca-coder"))

    def test_default_is_pdca(self):
        self.assertEqual(DEFAULT_SKILL, documented_default())

    def test_fixture_tasks_resolve_to_prescribed_skill(self):
        for task, expected in FIXTURES:
            with self.subTest(task=task):
                self.assertEqual(expected, resolve(task))


if __name__ == "__main__":
    unittest.main()
