# Install prompt: let an agent do the checklist

Copy the fenced prompt below into a cheap primary session (for example `build`), fill the `Inputs`
block with your values, and send it. The agent installs the family idempotently, makes backups, and
stops on anything it cannot verify. The prompt is written in Russian — it mirrors the maintainer's
working language; commands and file names are exact. The family is host-agnostic: the same
`SKILL.md` + `assets/` + `scripts/` (where a skill ships it) go to OpenCode, Claude Code, Codex or a
custom host (`dsh`, …); the roots and the subagent frontmatter differ and are resolved in step 0.
For OpenCode the prompt detects the major (V1 or V2) and uses the matching delegation/permission
keys; V2 is the reference adapter.

## Inputs (fill before sending)

```text
HOST=opencode
OPENCODE_MAJOR=auto
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
- `OPENCODE_MAJOR` — only for `HOST=opencode`: `auto` detects the major from `opencode --version`;
  `1`/`2` pin the adapter (must match detection; unknown or mismatch → ask). Ignored for other hosts.
- `SKILLS_ROOT` / `AGENTS_ROOT` — empty means "use the host default" (table in
  `docs/install.md`); filled means "use exactly this".
- `VARIANT` — the overlay chain to install on top of the base: `pdca`, `pdca-coder` or
  `pdca-dotnet` (`pdca` is always installed — it is the single entry and the cycle itself).
- `INSTALL_COLLECTION` / `INSTALL_INCREMENTAL` — install the two form contracts.
- `PRIMARY` — the cheap primary that will drive the cycle.
- `PROFILE` — optional host profile with model bindings; empty means "do not touch bindings".

## Prompt

```text
Ты устанавливаешь семейство PDCA-скиллов в хост агента. Работай идемпотентно, с бэкапами,
ничего не коммить и не пушь. Значения ниже — из блока Inputs; если переменная пуста или
неоднозначна, остановись и спроси.

HOST=<opencode | claude | codex | dsh | custom>
OPENCODE_MAJOR=<auto | 1 | 2>
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
   - Проверь, что $SKILLS_REPO/skills/pdca/SKILL.md и
     $SKILLS_REPO/skills/$VARIANT/SKILL.md существуют.
   - Разреши корни по хосту (таблица — в docs/install.md §2/§3):
     opencode : skills ~/.config/opencode/skills, agents ~/.config/opencode/agents
     claude   : skills ~/.claude/skills,           agents ~/.claude/agents
     codex    : skills ~/.codex/skills (или $CODEX_HOME/skills), agents — каталог субагентов хоста
     dsh/custom: возьми SKILLS_ROOT и AGENTS_ROOT из Inputs; если пусты — спроси, не гадай.
   - Только для HOST=opencode: определи major. `opencode --version` → первый компонент
     (1.x → V1, 2.x → V2). Если OPENCODE_MAJOR=1|2 и найденный major не совпал — остановись
     и спроси. Если версию определить нельзя (команда недоступна, вывод неожиданный) — спроси,
     не угадывай. Запиши `opencode_major` в план.
   - Покажи план изменений (каталоги и файлы) и продолжай.

1. Скиллы
   - Скопируй из $SKILLS_REPO/skills/ в $SKILLS_ROOT каталоги целиком:
     pdca, $VARIANT, а также pdca-collection и pdca-incremental, если соответствующий
     INSTALL_* = yes. Каталог скилла — это `SKILL.md`, `assets/` и `scripts/`, если скилл их
     поставляет; `tests/` и генераторы диаграмм для рантайма не нужны. База `pdca` — единственный
     вход семейства, поэтому она нужна всегда.
   - Хелперы из `scripts/` установленного скилла — источник рантайм-копий: `pdca-executor` кладёт
     их байт-в-байт копиями в `.pdca/scripts/` проекта и запускает оттуда
     (`python3 .pdca/scripts/<helper>.py …`), а не из установленного каталога скилла.
   - Существующие каталоги с теми же именами сначала сохрани в <name>.bak-<UTC timestamp>.
   - Проверь frontmatter каждого установленного SKILL.md:
     * `name` совпадает с именем каталога;
     * у pdca-coder, pdca-dotnet, pdca-collection, pdca-incremental скрытие из авто-выбора:
       OpenCode V2 — `disable-model-invocation: true` и `metadata.opencode/autoinvoke: false`;
       OpenCode V1 — только `metadata.opencode/autoinvoke: false` (V1 не знает
       `disable-model-invocation`; если ключ есть, он безвреден — не требуй его и не добавляй);
     * у pdca этих флагов нет — он единственный авто-вызываемый скилл семейства.
   - Тело скиллов должно остаться host-агностичным: не добавляй в SKILL.md пути конкретного хоста.

2. Агенты-роли
   - Скопируй $SKILLS_REPO/skills/$VARIANT/assets/opencode-agents/*.md в $AGENTS_ROOT, существующие
     файлы — в бэкап.
   - Frontmatter ассетов несёт оба представления прав: V1-карту `permission:` и V2-список
     `permissions:`; они должны выражать одну политику. Для OpenCode V1 и V2 копируй как есть
     (V2 понимает оба, V1 — карту). Для claude переведи в формат Claude Code (`name`, `description`,
     `tools`; права — allowlist инструментов), для codex/custom — в формат хоста; тело промпта роли
     не меняй.
   - Убедись, что установленный pdca-orchestrator совпадает байт-в-байт с
     $SKILLS_REPO/skills/pdca/assets/opencode-agents/pdca-orchestrator.md (тело; frontmatter мог быть
     транслирован).
   - В шестиролевых вариантах (`pdca`, `pdca-coder`, `pdca-dotnet`) общие шесть ролей
     (`pdca-planner`, `pdca-check`, `pdca-executor`, `pdca-scout`, `pdca-escalate`,
     `pdca-orchestrator`) — байт-в-байт зеркала канонического
     `$SKILLS_REPO/skills/pdca/assets/opencode-agents/`; у `pdca-collection`/`pdca-incremental`
     есть только зеркало `pdca-orchestrator`. Сверяй с каноном, а не с прежней установленной
     копией (`python3 skills/pdca/scripts/sync_role_assets.py --check`).
   - Если CONFIG_REPO задан, синхронизируй те же файлы в его каталог агентов (источник для
     будущих установок), с бэкапами.
   - Проверь: ни в одном агенте нет выдуманного `model:`; у драйвера есть allowlist pdca-*.

3. Делегация и права (формат хоста)
   - opencode V2: `experimental.subagent_depth` в секции `experimental` (top-level `subagent_depth`
     V2 игнорирует). Графу нужны рёбра `primary → driver`, `driver → role`, `escalate → scout` —
     три ребра; счётчик считает рёбра вложенности сессий ниже primary (по умолчанию 1), и
     настроенное значение не доказывает, что установленная сборка проходит цепочку: зафиксируй
     версию сборки хоста и проверь фактическую цепочку в smoke-прогоне (шаг 6). Числа
     `subagent_depth`/`cap` не выдумывай;
     `permissions` — action `subagent`, allow для pdca-scout, pdca-planner, pdca-executor,
     pdca-check, pdca-escalate, pdca-security-auditor, pdca-orchestrator; `skill` allow.
   - opencode V1: top-level `"subagent_depth": 3` (ключа `experimental.subagent_depth` в V1 нет);
     `permission` map — действие `task` (не `subagent`) с allowlist ролей `pdca-*`; `skill` allow:
     `"permission": { "task": { "*": "deny", "pdca-*": "allow" }, "skill": "allow" }`.
     Массив `permissions` и action `subagent` — V2-only, в V1 их не создавай.
   - claude/codex/dsh/custom: включи вложенный запуск субагентов и разреши primary
     диспетчеризовать роли средствами хоста; не выдумывай ключи — сверься с docs/install.md и,
     если формат неизвестен, остановись и спроси.
   - Модельные биндинги: только если PROFILE задан. Иначе ничего не выдумывай — перечисли в
     отчёте, что осталось привязать вручную.

4. Инструкции хоста
   - Убедись, что фразовые триггеры вида «по циклу»/«через PDCA» ведут в `pdca`, а не в оверлей
     или форму (`pdca-coder`/`pdca-dotnet`/`pdca-collection`/`pdca-incremental`); если в инструкциях
     они привязаны к другому скиллу, исправь это (opencode/codex: AGENTS.md; claude: CLAUDE.md;
     custom: файл инструкций хоста).
   - Оставь одну нейтральную строку: «Семейство PDCA: единственный авто-вызываемый скилл —
     `pdca`; он же единственный вход и весь цикл. `pdca-coder`/`pdca-dotnet` — оверлеи, а
     `pdca-collection`/`pdca-incremental` — формы; они загружаются только по явному id или когда
     их выберет PLAN базы.»
   - Если в инструкциях сказано, что драйвер сам классифицирует задачу или выбирает вариант,
     замени на «форму и оверлей решает единственный PLAN базы `pdca`; драйвер только загружает
     названный контракт».
   - Синхронизируй $CONFIG_REPO и хостовую копию, сохранив локальные различия.

5. Курирование (только если применимо)
   - Если семейство лежит прямо в $SKILLS_ROOT — keep-list не нужен, пропусти.
   - Если хост держит скиллы в отдельном pack/списке (например OpenCode skills-keep.txt) —
     добавь туда pdca и установленные контракты и пересобери pack скриптом хоста.
   - Если правишь `skills` в opencode.json: V1 — `{ "paths": [...], "urls": [...] }`,
     V2 — один массив `[ ... ]`; не смешивай формы в одном файле.

6. Перезапуск и проверка
   - opencode V2: `opencode service restart`, затем `opencode debug agents` (все роли и драйвер
     видны) и `opencode debug config` (`experimental.subagent_depth` виден в секции `experimental`;
     само значение — не проверка цепочки).
   - opencode V1: перезапусти TUI/приложение (команды `service` в V1 нет); проверь
     `opencode agent list` (все роли и драйвер видны) и что `pdca` виден в списке скиллов.
     `debug agents`/`debug config` — V2-only, в V1 их не требуй.
   - claude: новая сессия, `/agents` перечисляет субагентов.
   - codex/dsh/custom: перезапуск/новая сессия по правилам хоста и его список агентов.
   - Проверь, что `pdca` виден модели для авто-выбора, а `pdca-coder`, `pdca-dotnet`,
     `pdca-collection`, `pdca-incremental` — только по явному id/имени.
   - Smoke: вызови `pdca` на тривиальной задаче; убедись, что единственный PLAN назвал форму и
     (для кодовой работы) оверлей, а дальше цикл пошёл по этому решению.
   - Preflight: проверь разрешимость обязательных ролей (без dummy substantive work — никаких
     пробных правок, пробных задач и фиктивных шагов), доступность вложенной делегации драйверу,
     `pdca-orchestrator` как субагента, ребро `escalate → scout` и загружаемость контракта шага.
     Установленный `pdca-orchestrator` сверь с каноническим ассетом
     `$SKILLS_REPO/skills/pdca/assets/opencode-agents/` и проверь действующие права: наблюдавшийся случай —
     установленная копия без делегирования `pdca-scout`, что молча ломает `escalate → scout`.
     Ключа, элемента схемы или константы параллельного cap на стороне хоста в проверенном исходнике
     V2 нет — это не значит «без ограничений», значения `cap` не выдумывай.
   - Семантика отказов: обязательная роль недоступна → resource stop (другая роль её не исполняет);
     контракт цикла недоступен → fail closed; обнаружено поздно → безопасная пауза до зависимого
     действия; fallback ровно один — дешёвый primary ведёт inline, `Notice:` с durable-причиной.
   - Если установку проверяет medium/strong primary, он цикл не запускает и не диспетчеризует:
     нужен явный handoff дешёвому primary с сохранением ссылок (задача, статус-файл, `.pdca/`).
   - Проверка на чистом хосте — открытый prerequisite, записанный в install-документах
     (`docs/install.md` §11, `Verification status: unverified`): не выдавай успешные тесты
     репозитория за проверку установки.

7. Отчёт
   В шапке укажи `opencode_major` (detected/pinned) и применённую ветку адаптера.
   Дай таблицу: шаг | изменено/создано/пропущено | путь | бэкап. Отдельно перечисли, что
   осталось вручную (модельные биндинги, профиль, права), и результат каждой проверки.

Ограничения: не трогай посторонние скиллы, агентов и конфиги; не коммить и не пушь; не
выдумывай model id и ключи конфигов; при неоднозначности остановись и спроси.
```
