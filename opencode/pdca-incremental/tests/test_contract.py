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

import re
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

    def test_description_requires_explicit_naming(self) -> None:
        description = " ".join(self.head.split("description:", 1)[1].split())
        self.assertIn("explicitly names", description)
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
        self.assertIn("независимыми целями", when)
        self.assertIn("свойство расписания", when)


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


class AutoCommitPolicyTest(unittest.TestCase):
    """Auto-commit is an explicit, step-scoped policy — never a right of the skill."""

    def setUp(self) -> None:
        self.text = _plain(SKILL.read_text(encoding="utf-8"))

    def test_policy_is_recorded_in_the_status(self) -> None:
        self.assertIn("Commit policy: none | auto", self.text)

    def test_only_an_accepted_step_is_committed(self) -> None:
        self.assertIn("Коммит — только принятого шага", self.text)
        self.assertIn("git add <paths>", self.text)
        self.assertIn("push — никогда", self.text)

    def test_brief_carries_the_commit_policy(self) -> None:
        brief = _section(self.text, "### 2. Brief шага", "### 3. Исполнение шага")
        self.assertIn("Commit policy", brief)
        self.assertIn("только принятый шаг", brief)


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
        self.assertIn("Смена цели, рецепта, порога или флора", self.invariants)
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


def _windows(text: str, token: str, radius: int) -> list[str]:
    """Every window of ``radius`` characters on both sides of ``token``."""
    return [
        text[max(0, m.start() - radius): m.end() + radius]
        for m in re.finditer(re.escape(token), text)
    ]


class CompositionContractTest(unittest.TestCase):
    """A campaign is a composition of units, not a copy of its lane (AC02/04/06/15)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = SKILL.read_text(encoding="utf-8")
        cls.text = _plain(cls.raw)

    def test_execution_kind_is_a_field_and_preparation_is_given_not_copied(self) -> None:
        for token in ("execution_kind", "preparation_ref"):
            with self.subTest(token=token):
                self.assertIn(
                    token, self.text,
                    f"pdca-incremental lacks the composition field {token!r}",
                )
        self.assertTrue(
            "collection-lane" in self.text or "collection lane" in self.text,
            "pdca-incremental must name the collection lane it can be driven as",
        )
        self.assertIn(
            "не копир", self.text,
            "the contract must say the preparation is not copied (stem 'не копир')",
        )

    def test_disposition_and_pause_are_declared_states(self) -> None:
        for token in ("disposition", "paused"):
            with self.subTest(token=token):
                self.assertIn(
                    token, self.text,
                    f"pdca-incremental lacks the unit state {token!r}",
                )
        readiness = _windows(self.text, "готовност", 200)
        self.assertTrue(readiness, "no 'готовност' (readiness) statement")
        self.assertTrue(
            any(re.search(r"(?<!\w)не(?!\w)", w) for w in readiness),
            "readiness must be stated as not being completion ('не' near "
            f"'готовност'): {readiness!r}",
        )
        pause = _windows(self.text, "пауза", 200)
        self.assertTrue(pause, "no 'пауза' (pause) statement")
        self.assertTrue(
            any("не финал" in w for w in pause),
            "a pause must be stated as not final ('не финал' near 'пауза'): "
            f"{pause!r}",
        )

    def test_one_lane_and_no_campaign_in_campaign(self) -> None:
        self.assertIn("один лейн", self.text,
                      "pdca-incremental must state it runs as one lane")
        self.assertIn("рекурси", self.text,
                      "pdca-incremental must ban recursion (stem 'рекурси')")
        for line in self.raw.splitlines():
            if not re.search(
                r"(?i)(campaign|кампани).{0,40}(внутри|in).{0,40}(campaign|кампани)",
                line,
            ):
                continue
            with self.subTest(line=line.strip()[:80]):
                self.assertRegex(
                    line,
                    r"(?i)не|запрещ|forbidden",
                    "campaign-in-campaign must be forbidden on the same line: "
                    f"{line!r}",
                )

    def test_commit_policy_none_keeps_the_outer_commit(self) -> None:
        self.assertIn(
            "Commit policy: none", self.raw,
            "the contract lacks the explicit `Commit policy: none` marker",
        )
        windows = [
            self.text[max(0, m.start() - 300): m.end() + 300]
            for m in re.finditer(r"Commit policy: none", self.text)
        ]
        self.assertTrue(
            any(re.search(r"(?i)commit", w) and "внешн" in w for w in windows),
            "`Commit policy: none` must be scoped to external work (stem "
            f"'внешн' near 'commit'): {windows!r}",
        )

    def test_readiness_is_concrete_per_step(self) -> None:
        self.assertIn(
            "конкретн", self.text,
            "each step must carry a concrete readiness statement (stem 'конкретн')",
        )

    def test_required_sections_and_step_row_survive(self) -> None:
        for heading in ("## Роль", "## Роли, тиры и полномочия", "## Автономный режим"):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.raw, f"section lost: {heading}")
        step_rows = [ln for ln in self.raw.splitlines() if re.match(r"\|\s*STEP N\s*\|", ln)]
        self.assertTrue(step_rows, "the `STEP N` table row is gone")
        for row in step_rows:
            with self.subTest(row=row[:60]):
                self.assertIn("pdca-orchestrator", row)
        self.assertIn(
            "execution_kind", self.text,
            "the composition field must live in the preserved section structure",
        )


if __name__ == "__main__":
    unittest.main()
