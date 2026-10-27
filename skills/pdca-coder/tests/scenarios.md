# Сценарная матрица скилла pdca-coder (A–L)

Статус: **статическая (не исполняемая) матрица для независимого разбора**. Это — **не доказательство**
поведения: ни один агент/модель по этим сценариям **не запускался**, реальный цикл не исполнялся,
production-автомат не создавался. Статического guard'а на присутствие этих правил нет; любой
presence-guard фиксировал бы лишь наличие правил, а не поведение.
Поведенческий разбор проходит независимый `pdca-escalate` по полным соответствующим контрактам.

Источник правил (действующая норма): `skills/pdca-coder/SKILL.md` (§State machine,
§Transition gates, §Orchestrator role, §Host requirements, §PLAN selects the toolchain and lenses),
EN-роли `skills/pdca-coder/assets/opencode-agents/*.md` и источник
диаграммы `skills/pdca-coder/assets/diagram/gen_pdca.py`. Счётчики: цикл `<N>` (растёт
только в ACT), ревизия плана `r`, попытка `n/3` в пределах
ревизии; отвергнутый кандидат **без смены плана** не новая ревизия и не сбрасывает ретраи.

Установленная копия скилла (`config/skills/pdca-coder/**`) живёт в репозитории `opencode-config`;
тест обращается к ней только при `OPENCODE_CONFIG_REPO=<путь к opencode-config>`, иначе проверка
пропускается.

| # | Кратко | Требуемый исход |
| --- | --- | --- |
| A | Частичный `D` заблокирован, кандидат отвергнут | Исходный `D` возобновлён, не `done`, та же попытка `n` |
| B1 | Аддитивное предусловие | Исходный `D` активен, критерии/остаток без изменений, отображения замены нет, gate 2 закрыт до завершения остатка |
| B2 | Фактическая замена объёма | Явное отображение `superseded→replacement`, замена активна и несёт критерии; `superseded` не `done` |
| C | r1: два провала CHECK → реальный replan r2 | `n` сброшен в 1 на r2; повтор того же дефекта после фикса всё равно эскалируется |
| D | Один план, три провальных CHECK | `pdca-escalate`, 4-й попытки нет; `DO → PLAN` — не провальный CHECK |
| E | `pdca-planner` не может классифицировать кандидата | Сначала точечные факты (`pdca-scout`), затем `pdca-escalate` по низкой уверенности даже без доказанной внешности |
| F | Автономно: нет критерия / недоступен ресурс | Без вопроса; сбор/решение, затем blocked STOP с записанным итогом; обычный режим сохраняет вопросы и апрув плана |
| G | Три параллельных потока DO | Единственное зеркало прогресса — статус-файл: агрегированный `D:` и правдивые состояния каждого потока в нём |
| H | Cheap-only оркестрация; medium/strong primary — решения вне цикла | Цикл ведёт только cheap-tier primary (эффективный тир, не имя агента); начальный PLAN/replan — `pdca-planner`; в ролях только `# tier`, без `model:` |
| I | Security-триггер red | Conditional gather возвращается в агрегат `pdca-check` (своего независимого вердикта нет); обычный security-провал — провальный CHECK ревизии по общим счётчикам; немедленная эскалация — только жёсткий security-tradeoff |
| J | Эскалация: исчерпана ревизия `r` или нет | `pdca-escalate` даёт **решение**; оркестратор только роутит: revised remediation `r+1` → `pdca-planner`, реализация/STOP → `pdca-executor`; семантически не перевыбирает, гейты/no-4th/scope/security не отменяет |
| K | Автономно: cheap primary делегирует цикл | `subagent(pdca-orchestrator)` с cycle brief; субагент ведёт PLAN→DO→CHECK→ACT, возвращает сводку ≤8 строк; primary не читает/не правит |
| L | Fallback: `pdca-orchestrator` недоступен | Flat primary ведёт цикл сам, fallback зафиксирован (`Notice:`); гейты/no-4th/scope/security не отменяются |

Общая оперативная база (применяется ко всем кейсам, если ниже не уточнено):
`skills/pdca-coder/SKILL.md` — §State machine (Three counters), §Transition gates 1–4,
§Phase progress mirror, §Escalation (`pdca-escalate`) (триггеры, в т.ч. 5), §Autonomous mode,
§Cycle status file, §Parallel CHECK streams, §Host requirements (roles → agents),
§Orchestrator role, §PLAN selects the toolchain and lenses; `skills/pdca-coder/assets/opencode-agents/*.md`
(`pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`, `pdca-scout`, `pdca-security-auditor`,
`pdca-orchestrator`); метки диаграммы `skills/pdca-coder/assets/diagram/pdca-coder-hand.svg`.

---

## A. Частичный `D` заблокирован, кандидат отвергнут

**Вход:** реализация `D` остановлена на частичном результате и отчёте DO о блокере; `pdca-planner`
отвергает DO-кандидата, план **не меняется**.
**Требуемый исход:** незавершённая реализация `D` не помечается `completed`; работа
возобновляется с **исходного** `D`, а не заводится новая; счётчик попыток не растёт и не
сбрасывается (та же попытка `n`); гейт 2 не открывается.
**Оперативные источники:** SKILL §State machine / §Transition gates (gate 2: blocker report ≠ `done`,
rejected candidate resumes the original `D`); `assets/opencode-agents/pdca-executor.md`
(Unfinished work / retention); §Cycle status file.

## B1. Аддитивное предусловие (не замена)

**Вход:** DO сообщает о предусловии, добавляющем недостающую возможность; `pdca-planner` принимает его
как in-cycle задачу.
**Требуемый исход:** исходный `D` остаётся **активным** с критериями и остатком **без изменений**
(blocked на новой зависимости, **не `superseded`**); добавляется новая **активная** единица;
**отображения `superseded→replacement` нет**; гейт DO→CHECK заблокирован, пока остаток не завершён;
`done` — только фактически выполненная принятая работа; анализ кандидата «реализация завершена» не
завершает `D`.
**Оперативные источники:** SKILL §State machine / gate 2 / §Cycle status file (unit states, additive
prerequisite); `assets/opencode-agents/pdca-planner.md`, `assets/opencode-agents/pdca-executor.md`.

## B2. Фактическая замена объёма

**Вход:** `pdca-planner` фактически заменяет объём работы (не добавление предусловия).
**Требуемый исход:** исходная единица помечается `superseded` и **обязательно** оформляется явное
отображение `superseded→replacement`; единицы-замены **активны** и несут **все исходные критерии
приёмки и остаток**; цепочка замены должна свестись к активным `done`-единицам, покрывающим
сохранённые критерии; `superseded` никогда не считается `done`; гейт 2 отклоняется при
отсутствующем отображении/замене, висячей/циклической/само-замене или pending/blocked замене.
**Оперативные источники:** SKILL §State machine / gate 2 / §Cycle status file (unit states incl.
`superseded`, replacement chain); `assets/opencode-agents/pdca-planner.md`.

## C. Реальный replan между ревизиями

**Вход:** ревизия r1: два провальных CHECK (попытка `n=3`); `pdca-planner` выдаёт пересмотренный план
→ r2 (не отвергнутый кандидат без смены плана). Дополнительно: один и тот же дефект повторяется
после одного фикса на другой ревизии.
**Требуемый исход:** `DO → PLAN`/`CHECK → PLAN` не расходуют попытки следующей ревизии; r2
начинает `PLAN(r2) → DO` с `n=1`; исходящая провальная попытка записана в статус-файле до замены
плана; история одного и того же дефекта **не стирается** репланом — повтор дефекта после одного
фикса эскалируется **до второго фикса**. Исчерпанная ревизия (третий провальный CHECK) **не
получает 4-й попытки даже после `pdca-escalate`**; продолжить можно **только** через реально
пересмотренный план `r+1` (фактически изменённые задачи/зависимости/действия при сохранении
исходного критерия); переименование/переформулировка или сброс сессии — **не** новая ревизия.
**Оперативные источники:** SKILL §State machine / §Escalation (триггер про один и тот же дефект) /
§Cycle status file; `assets/opencode-agents/pdca-planner.md`, `assets/opencode-agents/pdca-check.md`, `assets/opencode-agents/pdca-escalate.md`.

## D. Третий провальный CHECK одного плана

**Вход:** один план (ревизия r), три провальных CHECK подряд; отдельно рассматривается переход
`DO → PLAN` внутри той же ревизии (новое предусловие/блокер).
**Требуемый исход:** после третьего провального CHECK **одной и той же** ревизии вызывается
`pdca-escalate`; четвёртой попытки нет; сам `DO → PLAN` — **не** провальный CHECK и не расходует
попытку следующей ревизии.
**Оперативные источники:** SKILL §State machine (`third failed CHECK of the same revision`,
`no 4th attempt`, `PLAN(r) → DO`, `CHECK → DO`); §Red flags (revision-local 4th attempt);
`assets/opencode-agents/pdca-check.md`, `assets/opencode-agents/pdca-escalate.md`.

## E. Неклассифицируемый кандидат: факты, затем низкая уверенность

**Вход:** `pdca-planner` не может уверенно классифицировать DO-кандидата; доказательств мало и
внешняя природа блокера **не доказана**.
**Требуемый исход:** сначала точечный сбор фактов через `pdca-scout` (`file:line`/URL), не
исчерпывающий перебор; при стойко низкой уверенности — `pdca-escalate` по существующему триггеру 5
**даже без доказанной внешности**; DO не выдаёт финальный вердикт и не делает STOP.
**Оперативные источники:** SKILL §Escalation (триггер 5, low confidence, without established
externalness, provisional candidate); `assets/opencode-agents/pdca-planner.md` (item 10, four-way
classification, insufficient evidence); `assets/opencode-agents/pdca-scout.md`.

## F. Автономный режим: без вопросов

**Вход:** автономный прогон; отсутствует критерий приёмки / недоступен ресурс; ветка
заблокирована или неоднозначна и неразрешима в цикле. Отдельно — обычный режим.
**Требуемый исход:** в автономном режиме **вообще нет вопросов** пользователю, апрувов,
приглашений начать сессию (включая missing acceptance criteria и unavailable resource);
проблема проходит через `pdca-planner`/`pdca-escalate`, затем **STOP** с записанным итогом
(закрыто/осталось/блокеры) и без вопроса. STOP **условен**: если эскалация разрешает вопрос и есть
actionable пересмотренный план (`r+1`) — работа продолжается; остановка **не** автоматическая после
каждой успешной эскалации, а только когда эскалация не разрешает вопрос и actionable плана нет.
`Notice:` и финальный итог допустимы; автономность — не разрешение авто-коммита. В обычном режиме
сохраняются необходимые вопросы и явный апрув плана.
**Оперативные источники:** SKILL §Autonomous mode, §Transition gates (gate 1: normal mode
plan approval), §State machine; `assets/opencode-agents/pdca-planner.md` (plan-disk paragraph).

## G. Один агрегированный активный `D:` при параллельных потоках

**Вход:** три параллельных потока/единицы DO.
**Требуемый исход:** единственное зеркало прогресса — статус-файл: в нём агрегированный `D:` и
правдивые состояния единиц (`pending`/`running`/`blocked`/`done`/`superseded`); агрегированный
`D:` закрывается только когда все единицы и DO-потоки удовлетворяют гейту 2; replan переносит
агрегированную фазовую метку, не завершая единицы ложно.
**Оперативные источники:** SKILL §Phase progress mirror (status file only, same turn, reconcile,
never from memory), §Transition gates (gate 1 records the single aggregate `D:` in the status
file), §Cycle status file.

## H. Cheap-only оркестрация, полномочия PLAN и привязки моделей

**Вход:** цикл запускается из primary; нужен начальный PLAN и replan; установка шести EN-ассетов
ролей.
**Требуемый исход:** цикл ведёт **только cheap-tier primary** (по **эффективному тиру профиля**, а
не по имени агента); medium/strong primary цикл не диспетчеризует и вне цикла
остаётся решающим primary; и начальный PLAN, и replan принадлежат субагенту `pdca-planner`, вердикт —
`pdca-check`; привязки моделей даёт `agent`-блок профиля хоста, в ролях только ярлык `# tier`
(`pdca-executor`/`pdca-scout`/`pdca-orchestrator` = cheap; `pdca-planner`/`pdca-check`/`pdca-security-auditor` = medium; `pdca-escalate` = strong),
`model:` в ролях отсутствует; профили не редактируются ради выбора id; `general`/`explore` не
обходятся; права дорогих ролей не расширяются.
**Оперативные источники:** SKILL §Orchestrator role, §Host requirements (roles → agents);
`assets/opencode-agents/*.md` (tier labels, no `model:`); `config/profiles/*.jsonc` (`agent` block, только
чтение).

## I. Security-conditional gather и агрегатный вердикт

**Вход:** срабатывает security-триггер (auth/секреты/ввод/крипто); `pdca-security-auditor` возвращает
отчёт/находку.
**Требуемый исход:** security — **conditional gather-поток** CHECK; его результат **возвращается в
агрегат** и судится `pdca-check` (своего независимого вердикта нет; обычный security-дефект не обходит
агрегированный триаж); гейт 3 зелёный только при **всех** потоках; обычный security-провал считается
провальным CHECK текущей ревизии по общим счётчикам `n/3`/истории дефектов; немедленная эскалация —
только **жёсткий security-tradeoff**; финальный вердикт по всем потокам — `pdca-check`'s.
**Оперативные источники:** SKILL §Transition gates (gate 3, «every failed CHECK … triggered security
failure»), §Parallel CHECK streams (security gather/return; any failed stream counts as a failed CHECK
of the current revision), §Escalation (hard security trade-off, counters);
`assets/opencode-agents/pdca-security-auditor.md`, `assets/opencode-agents/pdca-check.md`.

## J. Решение эскалации: роутинг, не перевыбор и без обхода гейтов

**Вход:** `pdca-escalate` вернул решение. Два случая: (1) ревизия **не исчерпана**; (2) ревизия
**исчерпана** (третий провальный CHECK той же `r`).
**Требуемый исход:** `pdca-escalate` возвращает **решение**, не меню и не код; cheap-оркестратор исполняет
его **только маршрутизацией** — реально пересмотренный remediation-план `r+1` → `pdca-planner` (автор
плана), реализация по текущему плану или STOP статуса → `pdca-executor`; оркестратор **семантически не
перевыбирает** и план не переписывает. Решение **не отменяет** гейты, запрет 4-й попытки, scope и
security-ограничения; при **не исчерпанной** ревизии продолжение возможно по текущему плану, при
**исчерпанной** — 4-й попытки нет даже после эскалации, продолжение только через genuine `r+1`; нет
actionable-плана → **STOP** (обычный режим — вопрос пользователю; автономный — записанный STOP без
вопроса).
**Оперативные источники:** SKILL §Orchestrator role (execute by routing, never re-decide),
§Escalation (After the escalation …), §State machine (no 4th), §Red flags;
`assets/opencode-agents/pdca-escalate.md`.

## K. Автономное делегирование: primary диспатчит `pdca-orchestrator`

**Вход:** cheap-tier primary; пользователь **явно** просит работать автономно; цикл ещё не начат.
**Требуемый исход:** primary **не ведёт** цикл сам, а запускает субагента
`pdca-orchestrator` с **cycle brief** (goal, scope, acceptance criteria, constraints,
references); `pdca-orchestrator` проводит PLAN→DO→CHECK→ACT и возвращает компактную
**сводку ≤8 строк**; primary лишь передаёт сводку дальше и **не читает** файлы/логи и **не правит** их;
коллекционный статус-файл не создаётся, обязательный pdca статус-файл пишет `pdca-executor`;
вопросы не задаются.
**Оперативные источники:** SKILL §Two paths → "Two paths, one contract." / §Autonomous mode
(Delegation) / §Host requirements (Autonomous driver; setup-allowlist включает `pdca-orchestrator`);
`assets/opencode-agents/pdca-orchestrator.md` (вход «одиночный автономный цикл», cycle brief → сводка ≤8 строк).

## L. Fallback: `pdca-orchestrator` недоступен

**Вход:** автономная просьба, но запуск субагента `pdca-orchestrator` невозможен — агент отсутствует,
либо `subagent_depth` < 2, либо делегирование запрещено хостом.
**Требуемый исход:** primary переходит в **flat primary** и ведёт цикл **сам** (PLAN→DO→CHECK→ACT
с теми же гейтами); fallback зафиксирован (`Notice:` в статус-файле); запрет 4-й попытки, scope и
security-ограничения **не отменяются**; вопросы по-прежнему не задаются.
**Оперативные источники:** SKILL §Autonomous mode (Delegation: fall back to the flat primary, log
the fallback) / §Host requirements (resource blocker); `assets/opencode-agents/pdca-orchestrator.md`.

---

## Дополнительно: отвергнутый кандидат не сбрасывает ретраи

**Вход:** `pdca-planner` отвергает DO-кандидата/просит уточнение, план остаётся тем же.
**Требуемый исход:** это **не** новая ревизия (`r` не растёт) и **не** сброс счётчика попыток
(`n` не обнуляется); кейсы A/C/D не могут быть обойдены через «переоткрытие» кандидатом.
**Оперативные источники:** SKILL §State machine (rejected candidate not a new revision, does not
reset the attempt counter, not erased by a replan); `assets/opencode-agents/pdca-planner.md` item 10.

---

## #238 — pressure-сценарии: BINDING/APPLICABLE-гейт и audit-disposition

Матрица для **всех трёх** вариантов (`pdca`, `pdca-coder`, `pdca-dotnet`); общие сценарии
прогоняются для каждого, variant-specific — только где применимо. Это **не доказательство**
поведения: ни один агент/модель по этим сценариям не запускался, реальный цикл не исполнялся.
Наличие правил статическим guard'ом не проверяется; поведенческий
прогон — отдельный шаг с **fresh** role-контекстом и фактическим тиром роли (model IDs не
хардкодить).

### A238. Зелёные required-строки и audit-ссылка без ledger-hash

**Вход:** build/tests зелёные и обязательные строки `met`; старый report ссылается на log/patch
без отдельного ledger-hash.
**Требуемый исход:** CHECK принимает по required-строкам; недостающий hash — audit-note, **нет**
`incomplete`/STOP и нового round ради hash.
**Оперативные источники:** SKILL §Frozen evidence manifest → «Binding/applicability disposition
(append-only)».

### B238. Тесты на текущем незакоммиченном состоянии без `committed == tested`

**Вход:** tests выполнены на текущем uncommitted состоянии; per-path snapshot на момент запуска
отсутствует.
**Требуемый исход:** честная identity фактически проверенного состояния принимается; существующий
freshness без mismatch ⇒ нет commit/provenance-блокера и нет требования коммитить ради PASS.
**Оперативные источники:** SKILL §Evidence over assertion; §Frozen evidence manifest.

### C238. CHECK постфактум требует runtime-дигесты / recursive inventory

**Вход:** CHECK пытается добавить ретроспективные runtime-дигесты или рекурсивный инвентарь
ссылок прошлых артефактов.
**Требуемый исход:** audit-only требование отвергается с rationale; исходная строка остаётся
`open` с disposition `diagnostic_nonbinding` и исключается из binding-блокеров; product-работа не
перезапускается.
**Оперативные источники:** SKILL → «Binding/applicability disposition (append-only)».

### D238. PLAN сам freeze-нул transitive inventory без user-acceptance

**Вход:** PLAN-автор закрепил generic `complete transitive inventory`, не согласованный как
отдельная audit-цель.
**Требуемый исход:** правило не становится обязательным по инерции; explicit invalid
classification записан; реальные mandatory acceptance сохранены; ложного product `incomplete` нет.
**Оперативные источники:** SKILL §CHECK completeness gate → «PLAN does not invent audit hard
gates».

### E238. Реальный failed/missing required test или stale binary

**Вход:** обязательный тест упал/отсутствует либо обнаружен stale `--no-build`/другая ревизия.
**Требуемый исход:** существующий FAIL/re-gather/STOP-маршрут сохраняется; audit-exemption **не**
маскирует реальную проблему freshness/функциональности.
**Оперативные источники:** SKILL §CHECK completeness gate; §Versioned evidence contract.

### F238. Direct-evidence из #235 не ослаблен

**Вход:** задача требует reviewer pack с полными телами, source-copy fidelity и полный execution
ledger.
**Требуемый исход:** обязательные direct-evidence требования #235 не ослаблены; «диагностическими»
объявляются только extra recursive/retrospective audit-proofs, а не представленный нужный body,
mismatch staged-source или неподтверждённый запуск.
**Оперативные источники:** SKILL §Reviewer evidence pack; §Execution journal and the
unit/integration policy.

### G238. Пользователь явно заказал конечную audit-задачу

**Вход:** user согласовал finite audit как **отдельную** audit-задачу.
**Требуемый исход:** её acceptance остаётся **binding**; обычный fail/re-gather при невыполнении
сохраняется; disposition-путь к ней неприменим.
**Оперативные источники:** SKILL → «…stays binding»; §Frozen evidence manifest.

### H238. Append-only, отсутствие новых гейтов и согласованность ролей

**Вход:** проверка последствий правки.
**Требуемый исход:** ни один файл/статус/артефакт/исторический вердикт #232 не переписан; нет
нового hashing/provenance-графа; canonical (`assets/opencode-agents/**`) role rules согласованы; результат различает diagnostic note и actual mandatory unmet.
**Оперативные источники:** `assets/opencode-agents/pdca-check.md` — пункт «binding/applicable».
