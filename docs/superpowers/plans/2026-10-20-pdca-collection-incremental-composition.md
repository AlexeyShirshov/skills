# План реализации: композиция `pdca-collection` и `pdca-incremental`

**Статус:** план утверждён к исполнению (DO — отдельный шаг; этот документ ничего не реализует и не коммитит).
**Дата:** 2026-10-20.
**Основание (approved design):** [`docs/superpowers/specs/2026-10-20-pdca-collection-incremental-composition-design.md`](../specs/2026-10-20-pdca-collection-incremental-composition-design.md), включая последнюю правку про `selected_variant` (§3.2, §9.2).
**Область:** верхние контракты семейства (`skills/pdca-entry`, `skills/pdca-collection`, `skills/pdca-incremental`) и общий ассет раннера `skills/pdca/assets/agents/pdca-orchestrator.md` с его копиями; guard-тесты и двуязычные документы.
**Не входит:** базовая машина (`skills/pdca/SKILL.md`), доменные контракты `pdca-coder`/`pdca-dotnet`, роль-ассеты `pdca-{planner,executor,check,escalate,scout}.md`, новые роли/тиры/model id, новые статусы задач/групп, git-модель коллекции, продуктовый код.

**Цель.** Реализовать ровно то, что зафиксировано в approved design: collection может содержать единицы-циклы (`execution_kind=cycle`) и единицы-кампании (`execution_kind=campaign`); форма исполнения отделена от `selected_variant`; барьер требует настоящий PLAN цикла либо отдельный immutable `preparation.md@r<k>` кампании; кампания в коллекции ведётся существующим `pdca-orchestrator` inline без нового агента/уровня `Task`; состояния readiness/runtime/disposition раздельны; пауза ≠ финал; права и fallback не расширяются. Дизайн переопределять нельзя: расхождение — stop и возврат к planner, а не «улучшение» по ходу.

**Инварианты исполнения плана**

- C#-специфики в задаче нет; символы C# не анализируются. Текстовые guard-тесты — обычный `unittest`.
- Один поток реализации; тесты, контракты и документы можно вести параллельно только там, где это явно разрешено ниже.
- Коммитов и push нет. Все правки — в рабочем дереве.
- Любая новая правка поведения начинается с регрессионной проверки, которая на текущем дереве падает/отсутствует (red), и только затем контракт меняется (green). Это guard-тесты скиллов, а не продуктовая норма.
- Неизвестные host-факты не превращаются в числа. Если проверить нельзя — это ограничение и capability-safe fallback, а не догадка.
- Гейты и безопасность не ослабляются: новых попыток сверх базовых `N`/`r`/`n`, новых гейтов, расширения allowlist или прав нет.

---

## 0. Baseline рабочего дерева и текущих проверок

**Зависимости:** нет. **Владелец:** cheap executor (на стадии DO).

**Files (read-only):** всё дерево; отдельно — `skills/*/tests/`, `README.md` (раздел Tests), `.pdca/status/`.

**Action.**

1. Зафиксировать baseline без присвоения чужих изменений: `git status --porcelain` и `git diff --stat` в `/home/alex/sources/skills`. Ожидаемое состояние на момент написания плана: отслеживаемые файлы не изменены, untracked — только `docs/superpowers/` (эта спека и этот план). Если появились другие изменения — записать их как **чужие/предсуществующие**, не откатывать, не форматировать, не включать в diff-ревью как свои.
2. Точечно запустить текущие релевантные наборы (см. команды ниже) и записать exit code, passed/failed/skipped, полный лог в `/tmp/opencode/<task>-baseline-<suite>.log`.
3. Отдельно перечислить known failures/skips и их причины. Особенно: host-parity проверки, которым нужен `OPENCODE_CONFIG_REPO`, и `test_git_model.py`, который скипается без `bash`/`git >= 2.28`.
4. Проверить наличие `.pdca/status/` в репозитории и зафиксировать, какие persisted-схемы реально доступны для чтения (нужно для факт-гейта FG-4). Файлы не менять.

**Commands (существующие конвенции репозитория, `README.md` §Tests):**

```sh
python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
python3 -m unittest discover -s skills/pdca-entry/tests -p 'test_*.py' -v
python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v
```

**Acceptance.**

- Есть baseline-запись: commit hash (`git rev-parse HEAD`), список untracked/modified, по каждой команде — exit code и числа.
- Known skips перечислены поимённо с причиной; ни один skip не засчитан как pass.
- В рабочем дереве нет новых файлов/правок, созданных этим шагом.

**Stop/replan:** если baseline-прогон уже красный по причине, не связанной с задачей, — зафиксировать как предсуществующий дефект, не «чинить» его в этом изменении; при конфликте с acceptance-критериями — вернуть вопрос planner'у.

---

## 1. Факт-гейт: read-only scout (host depth, allowlist, cap, schema)

**Зависимости:** задача 0. **Владелец:** `pdca-scout` (read-only), сводку потребляет planner; medium primary только планирует и **не запускает PDCA-цикл**.

**Files (read-only):** host-конфиг, доступный через `OPENCODE_CONFIG_REPO` (если передан) — `config/agents/`, `config/profiles/`, `config/AGENTS.md`, `config/skills-keep.txt`; `docs/install.md`, `docs/ru/install.md`, `docs/install-prompt.md`; `.pdca/status/*` (реальные persisted-файлы); `skills/pdca/assets/agents/pdca-orchestrator.md` (§Contract, права), `skills/pdca/tests/test_routing_consistency.py` (host-parity skip-логика).

**Action.** Собрать факты, ничего не записывая вне workspace и не расширяя права:

1. **Host depth semantics.** Какая именно настройка/ключ действует в установленной версии хоста (`experimental.subagent_depth` vs top-level `subagent_depth`) и что именно считается: уровень драйвера, уровень роли, ребро `escalate → scout`. Факты — только из host-конфига/`opencode debug config`/наблюдаемого поведения. Текущие формулировки install-документов (`experimental.subagent_depth` ≥ 2, предупреждение об игнорировании top-level) считать **проверяемой гипотезой**, а не доказательством.
2. **Бюджет рёбер.** Посчитать рёбра для `primary → group runner → role → scout` и отдельно `escalate → scout`. Зафиксировать, какие значения реально наблюдаемы.
3. **Capability/allowlist skill loading.** Как хост загружает скилл по ID, доступен ли allowlist нужных контрактов, не требует ли композиция новых записей в task-allowlist раннера.
4. **Cap.** Как параллельный cap хоста соотносится с `cap` коллекции и однопоточностью кампании (нужен ли отдельный лимит или достаточно существующего расписания).
5. **Durable schema defaults.** По реальным `.pdca/status/` подтвердить: отсутствующий `execution_kind`; отсутствующий `preparation_state`; старый блок каркаса в статусе кампании; отсутствующие `campaign_ref`/`disposition`; append-only accepted-строки. Только чтение.

**Acceptance.**

- Сводка «факт / источник (path:line или вывод команды) / уверенность» по каждому пункту.
- Для каждого недоказанного пункта явно написано «не установлено»; **никаких чисел**, выведенных из рассуждений.
- Если host-конфиг недоступен (нет `OPENCODE_CONFIG_REPO`, нет установленного хоста) — это ограничение: фиксируется capability-safe fallback (проверка результата «роль/делегирование работают», а не сравнение с порогом), install-документы не получают числовых утверждений.
- Если факт нарушает обязательные роли/рёбра (например, недоступна вложенная делегация или `escalate → scout`) — это **hard blocker** для соответствующего пути: stop и вопрос planner'у, не «обход» и не расширение прав.

**Stop/replan:** недоказанное число нельзя использовать в контракте или docs. Если проверка требует записи/установки вне workspace — остановиться и запросить отдельное разрешение; без него пункт остаётся ограничением.

---

## 2. Регрессионные проверки контрактов (red до изменения поведения)

**Зависимости:** задачи 0, 1 (схема defaulting нужна для тестов миграции). **Files (tests only):** `skills/pdca/tests/test_orchestrator_variant_routing.py`, `skills/pdca/tests/test_routing_consistency.py`, `skills/pdca/tests/test_permission_boundaries.py`, `skills/pdca-entry/tests/test_contract.py`, `skills/pdca-collection/tests/test_plan_barrier.py`, `skills/pdca-collection/tests/test_verification_recovery.py`, `skills/pdca-collection/tests/test_routing_guard.py`, `skills/pdca-collection/tests/test_git_model.py`, `skills/pdca-collection/tests/test_orchestrator_asset.py`, `skills/pdca-incremental/tests/test_contract.py`, `skills/pdca-incremental/tests/test_orchestrator_asset.py`, `skills/pdca/tests/test_docs_sources.py`.

**Action.** Расширить существующие наборы (новый suite не создавать) проверками, фиксирующими контракт **до** правок SKILL/ассета. Минимальный набор:

- `execution_kind` (`cycle`|`campaign`) и `selected_variant` — разные поля; у `campaign` нет собственного `selected_variant`; вариант шага конкретен и immutable для запуска; раннер не классифицирует и fail closed при отсутствии/неразрешимости.
- Смешанный пакет: `cycle` + `campaign` в одной коллекции; барьер требует разное, но обязателен для каждой единицы.
- Readiness ≠ runtime baseline: `preparation_state=ready` без runtime-статуса — barrier-ready/not started, unit не `done`; baseline/runtime не требуются на барьере.
- Настоящий PLAN на каждый фактический шаг; бриф не подменяет PLAN; normal-mode pending approval ref + `disposition=paused`.
- Нет лишнего вложенного `Task`: одна исполняющая модель standalone и inline collection-lane, без `campaign-agent`/`cycle-agent` и без второго уровня оркестратора.
- Standalone incremental совместим: `blocked`/`stopped` — checkpoint, resume не переобъявлен.
- Выбор совместимого контракта шага: `pdca-dotnet`/`pdca-coder`/`pdca` по содержанию шага; `pdca-collection`/`pdca-incremental` вариантом шага быть не могут; новый домен в общих правилах не появляется.
- Домен-агностичность общих правил: в текстах композиции нет доменных норм/примеров (тесты самой реализации разрешены).

**Acceptance.**

- Каждая новая проверка сформулирована как structural guard по тексту контрактов/фронтматтеру/правам, без исполнения модели и без сети.
- На текущем (неизменённом поведении) дереве новые проверки падают или отсутствуют ожидаемые строки — red зафиксирован логом.
- Проверки не дублируют существующие и не требуют правок вне перечисленных файлов.

**Command (после добавления тестов, до правок контрактов):**

```sh
python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
```

**Stop/replan:** если red нельзя получить структурной проверкой без догадок о формате — сузить до проверки уже существующего инварианта и отметить это в отчёте; не ослаблять проверку, чтобы она «прошла».

---

## 3. Артефакт подготовки, ревизии, поверхность и раздельные состояния

**Зависимости:** задачи 1, 2. **Files:** `skills/pdca-collection/SKILL.md` (§§ `Роль`, `Коллекция (P / D / C / A)`, `Лейн`, `Статус коллекции`, `Fallback`), `skills/pdca-incremental/SKILL.md` (§§ `Campaign status file`, `Campaign cycle` → `0. Bootstrap`), тесты из задачи 2.

**Action.**

1. Ввести в контракт коллекции `execution_kind` и поля подготовки: `plan_state` (только `cycle`), `preparation_state` (`pending`|`ready`), единственный authoritative `preparation_ref` (`.../preparation.md@r<k>`), `campaign_ref` (optional до bootstrap, обязателен после), per-unit `disposition` (`active`|`paused`|`finalized`).
2. Описать preparation document как отдельный immutable/revisioned файл (author call: `.pdca/<collection-id>/units/<unit-id>/preparation.md`, safe equivalent допустим) и mapping из текущего блока каркаса в статусе кампании. Каркас не копируется ни в статус unit, ни в runtime-статус, ни в бриф.
3. Разделить три операции: preparation record (до/на барьере; подготовительные записи executor разрешены), baseline bootstrap (после барьера, до первого step DO; создаёт baseline evidence + runtime `Status: running` + `campaign_ref`), change-producing DO (после step PLAN).
4. Зафиксировать владение поверхностью: резервация — консервативная верхняя граница **всей** задачи, не прогноз и не union первых шагов; недоказуемое непересечение → сериализация; расширение → stop/reapprove без авто-recluster/remerge/reset.
5. Сохранить существующий ALL-barrier: ни один лейн не аллоцируется, пока каждая единица не готова по правилу своего вида; единица без осмысленного плана/каркаса остаётся gap и не получает `ready`-placeholder.
6. Legacy/defaulting (по фактам FG-4): отсутствующий `execution_kind` у старых прогонов трактуется явно (по утверждённому правилу), неизвестное значение `execution_kind` — **fail closed**, без неявной конвертации уже идущей работы; accepted-строки append-only не переписываются; новые поля не ломают закрытые прогоны.

**Acceptance.**

- В тексте коллекции нет утверждений, что `preparation_state=ready` равно `done`/`running`/приёмке.
- `preparation_ref` единственный; копий каркаса нет; `preparation_ref` обязателен на барьере, `campaign_ref` — нет.
- Ни один шаг не расширяет поверхность молча.
- Guard-тесты задачи 2 (barrier/routing/plan) зелёные.

**Command:** `python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v`.

**Stop/replan:** если реальные persisted-файлы противоречат выбранному defaulting (FG-4) — остановиться, вернуть planner'у правило чтения; не «мигрировать» чужие статус-файлы.

---

## 4. Раннер: collection-lane и inline-ведение

**Зависимости:** задачи 1, 3. **Files:** канонический `skills/pdca/assets/agents/pdca-orchestrator.md`; байт-в-байт копии: `skills/pdca-entry/assets/agents/pdca-orchestrator.md`, `skills/pdca-coder/assets/agents/pdca-orchestrator.md`, `skills/pdca-dotnet/assets/agents/pdca-orchestrator.md`, `skills/pdca-collection/assets/agents/pdca-orchestrator.md`, `skills/pdca-incremental/assets/agents/pdca-orchestrator.md`; тесты `skills/pdca/tests/test_routing_consistency.py`, `skills/pdca-collection/tests/test_orchestrator_asset.py`, `skills/pdca-incremental/tests/test_orchestrator_asset.py`.

**Action.**

1. Описать два режима одного ассета: step orchestrator (standalone, один шаг) и collection-lane driver (ведёт state machine кампании и текущий цикл inline в своей сессии).
2. Collection-lane driver получает `execution_kind`, загруженный контракт кампании, `selected_variant` шага и правило диспетчеризации; перечитывает durable-состояние между единицами/шагами, собирает брифы из решений ролей, диспетчеризует роли строго по заданному правилу.
3. Явно запретить раннеру: классифицировать задачу, выбирать домен/форму исполнения/вариант, выводить правило диспетчеризации, решать за planner/check/escalate, править/исполнять, расширять read-scope.
4. Сохранить права: `edit: deny`, `write: deny`, `bash: deny`, `task` default deny с текущим allowlist; метаданные — через tool outputs; durable read — только в host-разрешённом scope, иначе evidence готовит executor/scout.
5. Зафиксировать загрузку контрактов: разрешённый механизм скиллов, fallback — чтение `SKILL.md` из установленного корня делегированной авторизованной ролью; это не workspace discovery.
6. Синхронизировать **все шесть** копий атомарно существующим parity-механизмом (копирование канонического файла), не редактировать копии по отдельности.

**Acceptance.**

- `cmp` всех шести файлов даёт побайтовое совпадение.
- В ассете нет новых ролей/агентов, нет `model:`, нет новых записей allowlist, нет упоминания второго уровня `Task`.
- Standalone-модель (`primary → step orchestrator → roles`) не переобъявлена.
- Guard-тесты раннера зелёные.

**Commands:**

```sh
python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v
```

**Stop/replan:** если parity-механизм требует правки копий вручную или расхождение не устраняется одной синхронизацией — остановиться и вернуть planner'у вопрос о механизме; не оставлять частично обновлённые копии.

---

## 5. Incremental-контракт: две модели, resume, пауза, git

**Зависимости:** задачи 3, 4. **Files:** `skills/pdca-incremental/SKILL.md` — точечно §§ `Role`, `Roles, tiers and authority` (строка `STEP N | RUNNER | pdca-orchestrator`), `Autonomous mode`; по смыслу §§ `Campaign invariants`, `Campaign status file`, `Campaign cycle` → `0. Bootstrap`, `3. Step execution` (фактические заголовки проверить в файле, не выдумывать), `5. Stop decision`; тест `skills/pdca-incremental/tests/test_contract.py`.

**Action.**

1. Разделить две исполняющие модели: standalone (cheap primary ведёт кампанию, делегирует каждый шаг существующему step orchestrator) и collection-lane (тот же раннер ведёт кампанию и текущий цикл inline; primary коллекции исполнителем не становится). Standalone-модель и текущая resume-семантика не переобъявляются.
2. Уточнить `STEP N`: в collection-режиме RUNNER ведёт кампанию и текущий цикл inline; в standalone — только шаг; тир и полномочия не меняются.
3. Разделить `Автономный режим`: standalone — один шаг за вызов, между шагами апрув-пауз нет; collection-lane — шаги inline под коллекционным расписанием.
4. Привести статус кампании к runtime-зеркалу: `Status`, append-only шаги, `Current step`, ревизия/попытка, seed, deferred, blockers, baseline evidence refs, checkpoint паузы, commit policy, stop verdict; `preparation_ref` — ссылка, не копия каркаса; физическая запись — `pdca-executor`, семантика — primary/driver.
5. Bootstrap: развести preparation document, baseline bootstrap и change-producing DO; baseline и runtime-статус — только после барьера.
6. Остановка/пауза: `blocked`/`stopped` — checkpoint с причиной, последним принятым числом, выполненными шагами, незавершёнными refs, `preparation_ref@r<k>` и требуемым resume; пауза не сбрасывает `N`/`r`/`n` и не даёт новых попыток; финальный `incomplete` — только по явному финальному неуспешному disposition.
7. Git: `Commit policy: none` запрещает промежуточные step-коммиты, но не outer completion commit коллекции; явное no-commit ограничение, конфликтующее с обязательной git-моделью, — preflight blocker, не тихое переопределение и не patch-fallback без решения.
8. Явно запретить рекурсию: кампания не содержит кампанию/коллекцию; шаг — только совместимый цикл семейства.

**Acceptance.**

- Изменения контекстные: остальной текст кампании (экономика, красные флаги, восстановление после компакции, связь с семейством) не переписан.
- В контракте нет домена кампании, дефолтного варианта и свободного выбора скилла.
- `test_contract.py` покрывает две модели, `preparation_ref`, готовность ≠ завершение, пауза ≠ финал, per-unit disposition, commit policy, запрет рекурсии, один лейн.
- Resume-инварианты (нет повторного зачёта принятого шага, нет обхода барьера) присутствуют и не ослаблены.

**Command:** `python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v`.

**Stop/replan:** если required-раздел отсутствует под ожидаемым именем — найти фактический заголовок в файле и обновить план-ссылку; не создавать параллельный раздел-дубль.

---

## 6. Capability, fallback и host-документация

**Зависимости:** задачи 1, 4. **Files:** `docs/install.md`, `docs/ru/install.md`, `docs/install-prompt.md`; соответствующий текст preflight/fallback — в `skills/pdca-collection/SKILL.md` (§`Fallback`) и `skills/pdca-incremental/SKILL.md` (§`Relation to the family`/fallback-часть, фактический заголовок проверить).

**Action.**

1. Preflight описывает наблюдаемую способность, а не число: доступность обязательных ролей, фактическая вложенность делегации, доступность `pdca-orchestrator` как субагента, ребро `escalate → scout`, загружаемость варианта шага. Без dummy substantive work (никаких пробных правок/задач/фиктивных шагов).
2. Единый flat fallback: драйвер недоступен → cheap primary ведёт работу inline, не получая прав ролей; `Notice:` с причиной и durable-ссылкой (статус коллекции/кампании); в normal mode — сообщить пользователю, в autonomous — durable-запись.
3. Недоступная обязательная роль → resource stop (не runtime `blocked` кампании и не финальный disposition); контракт цикла недоступен → fail closed без подстановки «похожего»; позднее обнаружение → безопасная пауза до зависимого действия.
4. Install-документы: убрать/смягчить утверждение, что голое `>= 2` гарантирует весь граф; числовые утверждения о `subagent_depth` — только если FG-1 доказал семантику и поддерживаемое значение; иначе формулировка «проверить наблюдаемую способность и бюджет рёбер на хосте». Cold host verification — prerequisite, не выдуманный результат.
5. Medium/strong primary (включая `architect`) цикл не запускает: явный handoff cheap primary с сохранением refs; автоматического запуска cheap-раннера из `architect` нет.
6. Не добавлять новых гейтов/попыток и не ослаблять security.

**Acceptance.**

- Ни в одном install-документе нет недоказанного числа и нет утверждения «`>= 2` достаточно для всего графа».
- Fallback и resource stop описаны раздельно; ни один из них не выдаётся за успех.
- `docs/install.md` и `docs/ru/install.md` согласованы по смыслу; `docs/install-prompt.md` остаётся RU-only по текущей конвенции.
- `test_docs_sources.py` зелёный (ссылки на §существуют).

**Commands:**

```sh
python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
```

**Stop/replan:** если FG-1 не дал семантику ключа — числовые примеры в install-документах не публикуются; вместо них — capability preflight и ссылка на проверку на живом хосте.

---

## 7. Документация EN/RU

**Зависимости:** задачи 3–6 (текст контрактов уже стабилен, чтобы цитаты не разъехались). **Files:** `docs/pdca-collection.md` + `docs/ru/pdca-collection.md`; `docs/pdca-incremental.md` (создать) + `docs/ru/pdca-incremental.md`; `docs/pdca-guide.md` + `docs/ru/pdca-guide.md`; `README.md` (таблица скиллов и Usage); при необходимости — только цитаты в `docs/pdca.md`/`docs/ru/pdca.md`, если они ссылаются на изменённые разделы.

**Action.**

1. Collection: единицы-циклы и единицы-кампании; отдельный preparation document/`preparation_ref`; baseline bootstrap после барьера; пауза vs финал; per-unit `disposition`; владение поверхностью; раздельные состояния; fallback. Примеры — домен-нейтральные (цель, evidence, критерии, поверхность, зависимости, ресурсы, stop), без производительности/тестов/ИИ как нормы.
2. Incremental: кампания как единица коллекции; две исполняющие модели; `preparation_ref` вместо копии каркаса; готовность ≠ завершение; пауза ≠ финал; вариант шага и dispatch policy. Реальный кейс из `docs/ru/pdca-incremental.md` остаётся иллюстрацией статьи и не переносится в общие правила.
3. **EN-пара `docs/pdca-incremental.md`:** сейчас отсутствует, а design (§8.3, §9.17) требует двуязычности. Создать её как перевод/адаптацию RU-статьи в объёме затронутых разделов, без «гигантского» расширения и без переписывания несвязанных статей. Если по ходу выяснится, что EN-пара не требуется для acceptance — зафиксировать это решением planner'а, а не молчаливым пропуском.
4. Entry: в `docs/pdca-guide.md`/`README.md` отразить, что пакет может содержать кампанию, а кампания остаётся последовательной; маршрутизация `pdca-entry` не меняет приоритеты и не добавляет шестой контракт; различать top-level вход и вложенный контекст (кампания внутри collection не ремаршрутизируется заново).
5. Цитаты — только `skills/<skill>/SKILL.md §Раздел`, без диапазонов строк (это проверяет `test_docs_sources.py`).

**Acceptance.**

- Все затронутые пары EN/RU существуют и согласованы по смыслу; для incremental пара создана.
- В документах нет доменных норм в общих правилах композиции и нет недоказанных чисел.
- `test_docs_sources.py` зелёный; битых §-ссылок нет.
- Diff docs ограничен перечисленными файлами.

**Command:** `python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v` (включает docs-sources).

**Stop/replan:** если перевод EN требует решения о структуре, которого нет в design, — вернуть вопрос planner'у; не изобретать новые разделы контрактов в документации.

---

## 8. Верификация

**Зависимости:** задачи 2–7. **Files:** без новых; только чтение/прогоны. Логи — `/tmp/opencode/<task>-<phase>-<suite>.log`.

**Action.** Прогнать все релевантные наборы и записать exit code + passed/failed/skipped + путь к логу:

```sh
python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
python3 -m unittest discover -s skills/pdca-entry/tests -p 'test_*.py' -v
python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
python3 -m unittest discover -s skills/pdca-incremental/tests -p 'test_*.py' -v
bash skills/pdca-collection/tests/git-model-sim.sh
```

Дополнительно:

- Повторить parity-проверку шести копий раннера (входит в `test_routing_consistency.py`, но зафиксировать явно).
- Прогнать host-dependent проверки отдельно: с `OPENCODE_CONFIG_REPO`, если путь доступен, и без него. **Skip не считается pass**: в отчёте две строки — «с host-config» и «без host-config», с причиной.
- Убедиться, что ни один тест не требует сети и не пишет в репозиторий (git-model-sim работает на temp-репозиториях).
- Не объявлять продуктовой политикой прогон регрессионных тестов на tests/perf/AI: это только guard-проверки самих скиллов.

**Acceptance.**

- Все наборы зелёные, кроме явно перечисленных environment-dependent skips с причиной.
- `git-model-sim.sh` — exit 0 (или задокументированный skip при отсутствии `bash`/`git >= 2.28`, но не «pass»).
- Для каждого прогона есть exit code, числа и путь к полному логу.
- Нет «ложного pass» из-за skips.

**Stop/replan:** красный тест, относящийся к изменению, — фикс в рамках задачи-владельца; красный тест вне области — предсуществующий дефект, зафиксировать и не чинить молча.

---

## 9. Финальное ревью diff, трассировка и handoff

**Зависимости:** задача 8. **Files:** без новых правок, кроме исправлений, выявленных ревью (в рамках задач 3–7).

**Action.**

1. `git diff --stat` и `git diff` по каждому файлу; проверить, что нет правок вне области (базовая машина, доменные контракты, роль-ассеты, посторонние docs).
2. Заполнить матрицу трассировки «пункт acceptance design §9 → где реализовано (файл/§) → каким тестом покрыто». Все 18 пунктов должны иметь адрес; «покрыто косвенно» — не считается.
3. Проверить известные ограничения: host-факты, которые не удалось доказать; skips; legacy-schema правила; отсутствие cold-host verification (prerequisite). Перечислить их в handoff явно.
4. Убедиться: коммитов нет, push нет, `.pdca/status/` в репозитории не изменён.
5. Вернуть короткий отчёт: файлы, результаты прогонов (exit code + числа + логи), открытые вопросы planner'у.

**Acceptance.**

- Матрица покрывает 18/18 пунктов §9 design.
- Diff ограничен §8 design; чужие/pre-existing изменения не присвоены.
- Handoff содержит список недоказанных host-фактов и environment-dependent skips без ложного pass.
- Рабочее дерево без коммитов и без push.

**Stop/replan:** если хотя бы один пункт §9 не имеет реализации или теста — вернуть задачу-владельца, не закрывать как done.

---

## Порядок и зависимости (сводка)

```text
0 baseline
└─ 1 факт-гейт (scout, read-only)
   └─ 2 red guard-тесты
      ├─ 3 barrier/preparation/state (collection)
      │  ├─ 4 runner asset + parity
      │  │  └─ 5 incremental contract
      │  │     └─ 6 capability/fallback docs
      │  └─ 7 EN/RU docs (после стабилизации текста 3–6)
      └─ 8 verification
         └─ 9 final review + handoff
```

## Требования к отчёту исполнителя

- По каждой задаче: изменённые пути, acceptance-статус, команда и exit code.
- Полные логи — в `/tmp/opencode/`, путь в отчёте.
- Недоказанные факты — отдельным списком, без превращения в числа.
- Коммиты/push отсутствуют; продуктовый код не затронут.
