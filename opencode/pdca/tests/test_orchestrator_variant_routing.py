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

# Host config (agents/profiles/AGENTS.md/skills-keep) lives in the `opencode-config` repo,
# not in this one. Point at it with OPENCODE_CONFIG_REPO to enable host-parity checks;
# they skip by default.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"

ORCHESTRATOR = (CONFIG / "agents/pdca-orchestrator.md") if CONFIG else None
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


def skill_permission_rules() -> list:
    """V2 `permissions:` rules of the orchestrator (ordered {action,resource,effect})."""
    block = between(read(ORCHESTRATOR), "---", "\n---")
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


BASE_POLICY = (
    {"action": "*", "resource": "*", "effect": "allow"},
    {"action": "read", "resource": "*.env", "effect": "ask"},
    {"action": "read", "resource": "*.env.*", "effect": "ask"},
    {"action": "read", "resource": "*.env.example", "effect": "allow"},
)


def _matches(pattern: str, value: str) -> bool:
    regex = "".join(
        ".*" if ch == "*" else "." if ch == "?" else re.escape(ch) for ch in pattern)
    flags = re.IGNORECASE if os.name == "nt" else 0
    return re.fullmatch(regex, value, flags | re.DOTALL) is not None


def effective(rules: list, action: str, resource: str) -> str:
    effect = "ask"
    for rule in BASE_POLICY + tuple(rules):
        if "action" not in rule or "resource" not in rule:
            continue
        if _matches(rule["action"], action) and _matches(rule["resource"], resource):
            effect = rule.get("effect", "ask")
    return effect


class CycleSkillsExistTest(unittest.TestCase):
    def test_each_target_cycle_skill_exists_and_is_named(self):
        for name in CYCLE_SKILLS:
            with self.subTest(skill=name):
                path = SKILLS / name / "SKILL.md"
                self.assertTrue(path.is_file(), "%s missing" % name)
                self.assertEqual(name, skill_name(path))


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class OrchestratorMayLoadCycleSkillsTest(unittest.TestCase):
    def test_skill_permission_allows_cycles_and_denies_brainstorming(self):
        rules = skill_permission_rules()
        self.assertEqual("allow", effective(rules, "skill", "*"))
        self.assertEqual("deny", effective(rules, "skill", "brainstorming"))
        for name in CYCLE_SKILLS:
            with self.subTest(skill=name):
                self.assertEqual("allow", effective(rules, "skill", name))

    def test_orchestrator_carries_no_model_id(self):
        self.assertNotRegex(read(ORCHESTRATOR), r"(?m)^\s*model\s*:")


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
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
