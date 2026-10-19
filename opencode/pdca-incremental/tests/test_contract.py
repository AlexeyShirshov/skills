"""Contract tests for the pdca-incremental skill text.

The skill is a campaign-level wrapper over single cycles: no committed whole-volume plan
(per-task plans may already exist), one accepted measurement per step, a baseline chain,
one status mirror, explicit stop conditions and two non-increment step kinds (repair,
verify). These tests pin those invariants to the normative text so an edit cannot silently
turn the skill into a collection (parallel batch) or a single cycle (fixed plan).

Style follows the sibling suites: plain ``unittest``, ``pathlib`` paths and
section-scoped assertions (locate a section, then assert within it), never global bare
keyword counts.

Run:
    python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"


def _plain(text: str) -> str:
    """Normalize markdown emphasis/backticks and whitespace for semantic asserts."""
    return " ".join(text.replace("**", "").replace("`", "").replace("«", '"').replace("»", '"').split())


def _section(text: str, start: str, end: str) -> str:
    i = text.find(start)
    if i < 0:
        raise AssertionError(f"section start not found: {start!r}")
    j = text.find(end, i + len(start))
    if j < 0:
        raise AssertionError(f"section end not found: {end!r} (after {start!r})")
    return text[i:j]


class FrontmatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")
        self.head = self.text.split("---", 2)[1]

    def test_name_matches_directory(self) -> None:
        self.assertIn(f"name: {SKILL_DIR.name}\n", self.head)

    def test_description_carries_triggers_and_scope(self) -> None:
        description = " ".join(self.head.split("description:", 1)[1].split())
        for token in ("инкрементами", "маленькими шагами", "нет плана на весь объём"):
            self.assertIn(token, description)
        self.assertIn("pdca-orchestrator", description)


class DefinitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))

    def test_campaign_is_not_a_cycle_variant(self) -> None:
        role = _section(self.text, "## Роль", "## Когда выбирать")
        self.assertIn("не вариант цикла", role)
        self.assertIn("не замена базового контракта", role)

    def test_each_step_is_a_full_cycle_delegated_with_variant_routing(self) -> None:
        role = _section(self.text, "## Роль", "## Когда выбирать")
        for variant in ("pdca-dotnet", "pdca-coder", "pdca-orchestrator"):
            self.assertIn(variant, role)
        self.assertIn("PLAN → DO → CHECK → ACT", role)

    def test_collection_is_the_neighbour_not_the_alternative(self) -> None:
        when = _section(self.text, "## Когда выбирать", "## Инварианты кампании")
        self.assertIn("известный список задач", when)
        self.assertIn("ALL-barrier", when)
        self.assertIn("не выбирает коллекцию", when)
        self.assertIn("≥2", when)


class RolesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.roles = _section(self.text, "## Роли, тиры и полномочия", "## Когда выбирать")

    def test_every_campaign_block_has_an_owner(self) -> None:
        for block in ("BOOTSTRAP", "DISCOVER", "BRIEF", "STEP N", "ACCEPT", "DECIDE", "ACT/STOP"):
            self.assertIn(block, self.roles)

    def test_roles_tiers_and_permissions_are_named(self) -> None:
        for role in ("pdca-planner", "pdca-executor", "pdca-scout", "pdca-orchestrator", "pdca-check", "primary", "pdca-escalate"):
            self.assertIn(role, self.roles)
        for tier in ("cheap", "medium", "strong"):
            self.assertIn(tier, self.roles)
        for permission in ("read-only", "edit/bash", "dispatch-only"):
            self.assertIn(permission, self.roles)

    def test_primary_does_not_edit_the_product(self) -> None:
        self.assertIn("primary не правит продукт", self.roles)

    def test_model_ids_stay_out_of_the_skill(self) -> None:
        self.assertIn("нет ни одного model id", self.roles)


class InvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.invariants = _section(
            _plain(SKILL.read_text(encoding="utf-8")),
            "## Инварианты кампании",
            "## Статус-файл кампании",
        )

    def test_baseline_chain_is_accepted_measurement_only(self) -> None:
        self.assertIn("принятое число шага N", self.invariants)
        self.assertIn("Нет принятого числа — нет следующего шага", self.invariants)

    def test_floor_and_single_credited_measurement(self) -> None:
        self.assertIn("Флор инкремента (floor)", self.invariants)
        self.assertIn("Один зачётный замер на шаг", self.invariants)
        self.assertIn("не повторяют", self.invariants)

    def test_target_is_discovered_not_planned_upfront(self) -> None:
        self.assertIn("Цели открываются, а не планируются заранее", self.invariants)
        self.assertIn("свежая карта разрыва", self.invariants)

    def test_frozen_goal_recipe_and_no_parallel_steps(self) -> None:
        self.assertIn("Менять их по ходу — значит менять цель", self.invariants)
        self.assertIn("Один шаг за раз", self.invariants)


class StatusMirrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")
        self.mirror = _section(self.text, "## Статус-файл кампании", "## Цикл кампании")

    def test_mirror_is_single_and_recoverable(self) -> None:
        plain = _plain(self.mirror)
        self.assertIn("Единственный источник состояния", plain)
        self.assertIn("после компакции", plain)

    def test_status_template_has_the_required_blocks(self) -> None:
        for block in (
            "Goal:",
            "Recipe:",
            "Floor:",
            "Next-step seed:",
            "Deferred:",
            "Blockers:",
            "Protected/foreign:",
            "Stop verdict:",
        ):
            self.assertIn(block, self.mirror)

    def test_status_template_has_step_kinds(self) -> None:
        self.assertIn("| step | kind | parent |", self.mirror)
        for kind in ("increment", "repair", "verify"):
            self.assertIn(kind, self.mirror)


class LoopAndStopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))

    def test_bootstrap_measures_the_baseline_with_the_acceptance_recipe(self) -> None:
        boot = _section(self.text, "### 0. Bootstrap", "### 1. Discovery")
        self.assertIn("Сними baseline тем же рецептом", boot)
        self.assertIn("target = baseline + floor", boot)

    def test_discovery_feeds_plan_but_does_not_replace_it(self) -> None:
        discovery = _section(self.text, "### 1. Discovery", "### 2. Brief шага")
        self.assertIn("Discovery не является PLAN шага", discovery)
        self.assertIn("Next-step seed", discovery)

    def test_stop_conditions_are_explicit_and_only_met_is_success(self) -> None:
        stop = _section(self.text, "### 5. Решение об остановке", "### 6. Сайзинг")
        for status in ("met", "unreachable", "blocked", "stopped"):
            self.assertIn(f"`{status}`".replace("`", ""), stop)
        self.assertIn("met — единственный успех", stop)

    def test_red_flags_guard_against_goalpost_moving(self) -> None:
        flags = _section(self.text, "## Красные флаги", "## Восстановление")
        self.assertIn("Меняю порог/знаменатель/фильтр", flags)
        self.assertIn("Повторяю провальный замер", flags)
        self.assertIn("два инкремента параллельно", flags)

    def test_failed_step_routes_to_repair_not_group_stop(self) -> None:
        accept = _section(self.text, "### 4. Приёмка", "### 5. Решение об остановке")
        for token in ("repair", "unreachable", "blocked", "group-stop", "blast radius"):
            self.assertIn(token, accept)


class StepKindTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))
        self.kinds = _section(self.text, "### 3.1. Типы шагов", "### 4. Приёмка")

    def test_three_step_kinds_are_named(self) -> None:
        for kind in ("increment", "repair", "verify"):
            self.assertIn(kind, self.kinds)

    def test_repair_keeps_target_and_is_bounded(self) -> None:
        self.assertIn("тот же target", self.kinds)
        self.assertIn("parent = N", self.kinds)
        self.assertIn("один repair на провальный шаг", self.kinds)
        self.assertIn("pdca-escalate", self.kinds)

    def test_verify_does_not_move_baseline_or_replace_accept(self) -> None:
        self.assertIn("не двигает baseline", self.kinds)
        self.assertIn("не заменяет ACCEPT", self.kinds)
        self.assertIn("target = gate", self.kinds)


class AutonomyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))

    def test_autonomous_step_is_delegated_one_at_a_time(self) -> None:
        autonomy = _section(self.text, "## Автономный режим", "## Связь с семейством")
        self.assertIn("делегирует один шаг", autonomy)
        self.assertIn("`pdca-orchestrator`".replace("`", ""), autonomy)
        self.assertIn("не задаёт вопросы", autonomy)

    def test_flat_primary_fallback_is_recorded(self) -> None:
        autonomy = _section(self.text, "## Автономный режим", "## Связь с семейством")
        self.assertIn("Notice:", autonomy)


if __name__ == "__main__":
    unittest.main()
