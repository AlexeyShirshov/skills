# Install prompt: let an agent do the checklist

Copy the fenced prompt below into a cheap primary session (for example `build`), fill the `Inputs`
block with your values, and send it. The agent installs the family idempotently, makes backups, and
stops on anything it cannot verify. The prompt is written in Russian — it mirrors the maintainer's
working language; commands and file names are exact. The family is host-agnostic: the same
`SKILL.md` + `assets/` go to OpenCode, Claude Code, Codex or a custom host (`dsh`, …); the roots and
the subagent frontmatter differ and are resolved in step 0.

## Inputs (fill before sending)

```text
HOST=opencode
SKILLS_REPO=/home/alex/sources/skills
SKILLS_ROOT=
AGENTS_ROOT=
CONFIG_REPO=
VARIANT=pdca-dotnet
INSTALL_COLLECTION=yes
INSTALL_INCREMENTAL=yes
PRIMARY=
PROFILE=
```

- `HOST` — `opencode`, `claude`, `codex`, `dsh` or `custom`. Unknown value → the agent asks.
- `SKILLS_ROOT` / `AGENTS_ROOT` — empty means "use the host default" (table in
  `docs/install.md`); filled means "use exactly this".
- `VARIANT` — one cycle contract: `pdca`, `pdca-coder` or `pdca-dotnet`. Install the other cycle
  contracts too if the entry has to route to them.
- `INSTALL_COLLECTION` / `INSTALL_INCREMENTAL` — install the two top-level contracts.
- `PRIMARY` — the cheap primary that will drive the cycle.
- `PROFILE` — optional host profile with model bindings; empty means "do not touch bindings".

## Prompt

```text
Ты устанавливаешь семейство PDCA-скиллов в хост агента. Работай идемпотентно, с бэкапами,
ничего не коммить и не пушь. Значения ниже — из блока Inputs; если переменная пуста или
неоднозначна, остановись и спроси.

HOST=<opencode | claude | codex | dsh | custom>
SKILLS_REPO=<...>
SKILLS_ROOT=<... или пусто>
AGENTS_ROOT=<... или пусто>
CONFIG_REPO=<... или пусто>
VARIANT=<pdca | pdca-coder | pdca-dotnet>
INSTALL_COLLECTION=<yes | no>
INSTALL_INCREMENTAL=<yes | no>
PRIMARY=<имя дешёвого primary>
PROFILE=<профиль или пусто>

0. Preflight и выбор адаптера
   - Проверь, что $SKILLS_REPO/opencode/pdca-entry/SKILL.md и
     $SKILLS_REPO/opencode/$VARIANT/SKILL.md существуют.
   - Разреши корни по хосту (таблица — в docs/install.md §2/§3):
     opencode : skills ~/.config/opencode/skills, agents ~/.config/opencode/agents
     claude   : skills ~/.claude/skills,           agents ~/.claude/agents
     codex    : skills ~/.codex/skills (или $CODEX_HOME/skills), agents — каталог субагентов хоста
     dsh/custom: возьми SKILLS_ROOT и AGENTS_ROOT из Inputs; если пусты — спроси, не гадай.
   - Покажи план изменений (каталоги и файлы) и продолжай.

1. Скиллы
   - Скопируй из $SKILLS_REPO/opencode/ в $SKILLS_ROOT:
     pdca-entry, $VARIANT, а также pdca-collection и pdca-incremental, если соответствующий
     INSTALL_* = yes. Если entry должен роутить и в другие цикловые варианты, установи и их —
     иначе перечисли в отчёте, какие цели маршрута отсутствуют.
   - Существующие каталоги с теми же именами сначала сохрани в <name>.bak-<UTC timestamp>.
   - Проверь frontmatter каждого установленного SKILL.md:
     * `name` совпадает с именем каталога;
     * у pdca, pdca-coder, pdca-dotnet, pdca-collection, pdca-incremental есть
       `disable-model-invocation: true` (плюс `metadata.opencode/autoinvoke: false` для OpenCode);
     * у pdca-entry этих флагов нет.
   - Тело скиллов должно остаться host-агностичным: не добавляй в SKILL.md пути конкретного хоста.

2. Агенты-роли
   - Скопируй $SKILLS_REPO/opencode/$VARIANT/assets/agents/*.md в $AGENTS_ROOT, существующие
     файлы — в бэкап.
   - Frontmatter ассетов — это адаптер OpenCode (`mode: subagent`, `permission:`). Для claude
     переведи его в формат Claude Code (`name`, `description`, `tools`; права — allowlist
     инструментов), для codex/custom — в формат хоста; тело промпта роли не меняй.
   - Убедись, что установленный pdca-orchestrator совпадает байт-в-байт с
     $SKILLS_REPO/opencode/pdca/assets/agents/pdca-orchestrator.md (тело; frontmatter мог быть
     транслирован).
   - Если CONFIG_REPO задан, синхронизируй те же файлы в его каталог агентов (источник для
     будущих установок), с бэкапами.
   - Проверь: ни в одном агенте нет выдуманного `model:`; у runner есть allowlist pdca-*.

3. Делегация и права (формат хоста)
   - opencode: `experimental.subagent_depth` >= 2; permissions `subagent` allow для pdca-scout,
     pdca-planner, pdca-executor, pdca-check, pdca-escalate, pdca-security-auditor,
     pdca-orchestrator; `skill` allow.
   - claude/codex/dsh/custom: включи вложенный запуск субагентов и разреши primary
     диспетчеризовать роли средствами хоста; не выдумывай ключи — сверься с docs/install.md и,
     если формат неизвестен, остановись и спроси.
   - Модельные биндинги: только если PROFILE задан. Иначе ничего не выдумывай — перечисли в
     отчёте, что осталось привязать вручную.

4. Инструкции хоста
   - Удали фразовые триггеры вида «по циклу»/«через PDCA» → pdca-coder из инструкций хоста
     (opencode/codex: AGENTS.md; claude: CLAUDE.md; custom: файл инструкций хоста), если они там есть.
   - Оставь одну нейтральную строку: «Семейство PDCA: единственный авто-вызываемый скилл —
     `pdca-entry`; остальные контракты загружаются только по явному id или через handoff зонтика.»
   - Если в инструкциях сказано, что драйвер сам выбирает вариант, замени на «вариант называет
     диспетчеризующий скилл и передаёт драйверу как `selected_variant`».
   - Синхронизируй $CONFIG_REPO и хостовую копию, сохранив локальные различия.

5. Курирование (только если применимо)
   - Если семейство лежит прямо в $SKILLS_ROOT — keep-list не нужен, пропусти.
   - Если хост держит скиллы в отдельном pack/списке (например OpenCode skills-keep.txt) —
     добавь туда pdca-entry и установленные контракты и пересобери pack скриптом хоста.

6. Перезапуск и проверка
   - opencode: `opencode service restart`, затем `opencode debug agents` (все роли и runner
     видны) и `opencode debug config` (subagent_depth >= 2).
   - claude: новая сессия, `/agents` перечисляет субагентов.
   - codex/dsh/custom: перезапуск/новая сессия по правилам хоста и его список агентов.
   - Проверь, что pdca-entry виден модели для авто-выбора, а остальные контракты — только по
     явному id/имени.
   - Smoke: вызови pdca-entry на тривиальной задаче; убедись, что он назвал маршрут и передал
     выбранный контракт (в autonomous — как selected_variant).

7. Отчёт
   Дай таблицу: шаг | изменено/создано/пропущено | путь | бэкап. Отдельно перечисли, что
   осталось вручную (модельные биндинги, профиль, права), и результат каждой проверки.

Ограничения: не трогай посторонние скиллы, агентов и конфиги; не коммить и не пушь; не
выдумывай model id и ключи конфигов; при неоднозначности остановись и спроси.
```
