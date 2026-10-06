# Сценарная матрица pdca-dotnet (A–L)

Статус: **статическая (не исполняемая) матрица для независимого разбора**. Это — **не доказательство** поведения: ни один агент/модель по этим сценариям **не запускался**, реальный цикл не исполнялся, production-автомат не создавался. Присутствие правил проверяет
`test_contract_consistency.py`, и она тоже лишь фиксирует наличие правил, а не поведение.
Поведенческий разбор проходит независимый `escalate` по полным соответствующим контрактам.

Источник правил (действующая норма): `config/skills/pdca-dotnet/SKILL.md` (§State machine,
§Transition gates, §Orchestrator role, §Host requirements), EN-роли
`config/skills/pdca-dotnet/assets/agents/*.md` с зеркалами `config/agents/*.md` и исходники диаграммы
`config/skills/pdca-dotnet/assets/diagram/{workflow.json,gen_pdca.py}`. Исторический дизайн
`docs/superpowers/specs/2026-10-01-pdca-consistency-design.md` — только контекст, не норма (в нём
допустим любой primary, включая `architect`; действует cheap-only). Счётчики: цикл `<N>` (растёт
только в ACT), ревизия плана `r`, попытка `n/3` в пределах
ревизии; отвергнутый кандидат **без смены плана** не новая ревизия и не сбрасывает ретраи.

| # | Кратко | Требуемый исход |
| --- | --- | --- |
| A | Частичный `D` заблокирован, кандидат отвергнут | Исходный `D` возобновлён, не `done`, та же попытка `n` |
| B1 | Аддитивное предусловие | Исходный `D` активен, критерии/остаток без изменений, отображения замены нет, gate 2 закрыт до завершения остатка |
| B2 | Фактическая замена объёма | Явное отображение `superseded→replacement`, замена активна и несёт критерии; `superseded` не `done` |
| C | r1: два провала CHECK → реальный replan r2 | `n` сброшен в 1 на r2; повтор того же дефекта после фикса всё равно эскалируется |
| D | Один план, три провальных CHECK | `escalate`, 4-й попытки нет; `DO → PLAN` — не провальный CHECK |
| E | `planner` не может классифицировать кандидата | Сначала точечные факты (`scout`), затем `escalate` по низкой уверенности даже без доказанной внешности |
| F | Автономно: нет критерия / недоступен ресурс | Без вопроса; сбор/решение, затем blocked STOP с записанным итогом; обычный режим сохраняет вопросы и `go` |
| G | Три параллельных потока DO | Ровно один активный агрегированный `D:` todo; правдивые состояния каждого потока в статус-файле |
| H | Cheap-only оркестрация; `architect` — решения вне цикла | Цикл ведёт только cheap-tier primary (эффективный тир, не имя агента); начальный PLAN/replan — `planner`; в ролях только `# tier`, без `model:` |
| I | Security-триггер red | Conditional gather возвращается в агрегат `check` (своего независимого вердикта нет); обычный security-провал — провальный CHECK ревизии по общим счётчикам; немедленная эскалация — только жёсткий security-tradeoff |
| J | Эскалация: исчерпана ревизия `r` или нет | `escalate` даёт **решение**; оркестратор только роутит: revised remediation `r+1` → `planner`, реализация/STOP → `coder`; семантически не перевыбирает, гейты/no-4th/scope/security не отменяет |
| K | Автономно: cheap primary делегирует цикл | `Task(pdca-orchestrator)` с cycle brief; субагент ведёт PLAN→DO→CHECK→ACT, возвращает сводку ≤8 строк; primary не читает/не правит |
| L | Fallback: `pdca-orchestrator` недоступен | Flat primary ведёт цикл сам, fallback зафиксирован (`Notice:`); гейты/no-4th/scope/security не отменяются |

Общая оперативная база (применяется ко всем кейсам, если ниже не уточнено):
`config/skills/pdca-dotnet/SKILL.md` — §State machine (Three counters), §Transition gates 1–4,
§Phase todo tracker, §Escalation (`escalate`) (триггеры, в т.ч. 5), §Autonomous mode,
§Cycle status file, §Parallel CHECK streams, §Host requirements (roles → agents),
§Orchestrator role; `config/skills/pdca-dotnet/assets/agents/*.md` и зеркала
`config/agents/*.md` (`planner`, `coder`, `check`, `escalate`, `scout`, `security-auditor`,
`architect`); `README.md`; метки диаграммы `config/skills/pdca-dotnet/assets/diagram/{workflow.json,gen_pdca.py}`.

---

## A. Частичный `D` заблокирован, кандидат отвергнут

**Вход:** реализация `D` остановлена на частичном результате и отчёте DO о блокере; `planner`
отвергает DO-кандидата, план **не меняется**.
**Требуемый исход:** незавершённая реализация `D` не помечается `completed`; работа
возобновляется с **исходного** `D`, а не заводится новая; счётчик попыток не растёт и не
сбрасывается (та же попытка `n`); гейт 2 не открывается.
**Оперативные источники:** SKILL §State machine / §Transition gates (gate 2: blocker report ≠ `done`,
rejected candidate resumes the original `D`); `assets/agents/coder.md`, `config/agents/coder.md`
(Unfinished work / retention); §Cycle status file.

## B1. Аддитивное предусловие (не замена)

**Вход:** DO сообщает о предусловии, добавляющем недостающую возможность; `planner` принимает его
как in-cycle задачу.
**Требуемый исход:** исходный `D` остаётся **активным** с критериями и остатком **без изменений**
(blocked на новой зависимости, **не `superseded`**); добавляется новая **активная** единица;
**отображения `superseded→replacement` нет**; гейт DO→CHECK заблокирован, пока остаток не завершён;
`done` — только фактически выполненная принятая работа; анализ кандидата «реализация завершена» не
завершает `D`.
**Оперативные источники:** SKILL §State machine / gate 2 / §Cycle status file (unit states, additive
prerequisite); `assets/agents/planner.md`, `assets/agents/coder.md`.

## B2. Фактическая замена объёма

**Вход:** `planner` фактически заменяет объём работы (не добавление предусловия).
**Требуемый исход:** исходная единица помечается `superseded` и **обязательно** оформляется явное
отображение `superseded→replacement`; единицы-замены **активны** и несут **все исходные критерии
приёмки и остаток**; цепочка замены должна свестись к активным `done`-единицам, покрывающим
сохранённые критерии; `superseded` никогда не считается `done`; гейт 2 отклоняется при
отсутствующем отображении/замене, висячей/циклической/само-замене или pending/blocked замене.
**Оперативные источники:** SKILL §State machine / gate 2 / §Cycle status file (unit states incl.
`superseded`, replacement chain); `assets/agents/planner.md`.

## C. Реальный replan между ревизиями

**Вход:** ревизия r1: два провальных CHECK (попытка `n=3`); `planner` выдаёт пересмотренный план
→ r2 (не отвергнутый кандидат без смены плана). Дополнительно: один и тот же дефект повторяется
после одного фикса на другой ревизии.
**Требуемый исход:** `DO → PLAN`/`CHECK → PLAN` не расходуют попытки следующей ревизии; r2
начинает `PLAN(r2) → DO` с `n=1`; исходящая провальная попытка записана в статус-файле до замены
плана; история одного и того же дефекта **не стирается** репланом — повтор дефекта после одного
фикса эскалируется **до второго фикса**. Исчерпанная ревизия (третий провальный CHECK) **не
получает 4-й попытки даже после `escalate`**; продолжить можно **только** через реально
пересмотренный план `r+1` (фактически изменённые задачи/зависимости/действия при сохранении
исходного критерия); переименование/переформулировка или сброс сессии — **не** новая ревизия.
**Оперативные источники:** SKILL §State machine / §Escalation (триггер про один и тот же дефект) /
§Cycle status file; `assets/agents/planner.md`, `assets/agents/check.md`, `assets/agents/escalate.md`.

## D. Третий провальный CHECK одного плана

**Вход:** один план (ревизия r), три провальных CHECK подряд; отдельно рассматривается переход
`DO → PLAN` внутри той же ревизии (новое предусловие/блокер).
**Требуемый исход:** после третьего провального CHECK **одной и той же** ревизии вызывается
`escalate`; четвёртой попытки нет; сам `DO → PLAN` — **не** провальный CHECK и не расходует
попытку следующей ревизии.
**Оперативные источники:** SKILL §State machine (`third failed CHECK of the same revision`,
`no 4th attempt`, `PLAN(r) → DO`, `CHECK → DO`); §Red flags (revision-local 4th attempt);
`assets/agents/check.md`, `assets/agents/escalate.md`.

## E. Неклассифицируемый кандидат: факты, затем низкая уверенность

**Вход:** `planner` не может уверенно классифицировать DO-кандидата; доказательств мало и
внешняя природа блокера **не доказана**.
**Требуемый исход:** сначала точечный сбор фактов через `scout` (`file:line`/URL), не
исчерпывающий перебор; при стойко низкой уверенности — `escalate` по существующему триггеру 5
**даже без доказанной внешности**; DO не выдаёт финальный вердикт и не делает STOP.
**Оперативные источники:** SKILL §Escalation (триггер 5, low confidence, without established
externalness, provisional candidate); `assets/agents/planner.md` (item 10, four-way
classification, insufficient evidence); `assets/agents/scout.md`.

## F. Автономный режим: без вопросов

**Вход:** автономный прогон; отсутствует критерий приёмки / недоступен ресурс; ветка
заблокирована или неоднозначна и неразрешима в цикле. Отдельно — обычный режим.
**Требуемый исход:** в автономном режиме **вообще нет вопросов** пользователю, подтверждений,
`go` или приглашений начать сессию (включая missing acceptance criteria и unavailable resource);
проблема проходит через `planner`/`escalate`, затем **STOP** с записанным итогом
(закрыто/осталось/блокеры) и без вопроса. STOP **условен**: если эскалация разрешает вопрос и есть
actionable пересмотренный план (`r+1`) — работа продолжается; остановка **не** автоматическая после
каждой успешной эскалации, а только когда эскалация не разрешает вопрос и actionable плана нет.
`Notice:` и финальный итог допустимы; автономность — не разрешение авто-коммита. В обычном режиме
сохраняются необходимые вопросы и явный PLAN `go`.
**Оперативные источники:** SKILL §Autonomous mode, §Transition gates (gate 1: normal mode
go-ahead), §State machine; `assets/agents/planner.md` (plan-disk paragraph).

## G. Один агрегированный активный `D:` при параллельных потоках

**Вход:** три параллельных потока/единицы DO.
**Требуемый исход:** в любой момент ровно один `in_progress` todo — агрегированный `D:`; сами
единицы и их правдивые состояния (`pending`/`running`/`blocked`/`done`/`superseded`) — в
статус-файле; агрегированный `D:` закрывается только когда все единицы и DO-потоки удовлетворяют
гейту 2; replan переносит агрегированную фазовую метку, не завершая единицы ложно.
**Оперативные источники:** SKILL §Phase todo tracker (exactly one in_progress, one aggregate `D:`,
units in status file), §Transition gates (gate 1 single aggregate `D:`), §Cycle status file.

## H. Cheap-only оркестрация, полномочия PLAN и привязки моделей

**Вход:** цикл запускается из primary; нужен начальный PLAN и replan; установка шести EN-ассетов
ролей.
**Требуемый исход:** цикл ведёт **только cheap-tier primary** (по **эффективному тиру профиля**, а
не по имени агента); medium/strong primary (в т.ч. `architect`) цикл не диспетчеризует и вне цикла
остаётся решающим primary; и начальный PLAN, и replan принадлежат субагенту `planner`, вердикт —
`check`; привязки моделей даёт `agent`-блок профиля хоста, в ролях только ярлык `# tier`
(`coder`/`scout`/`pdca-orchestrator` = cheap; `planner`/`check`/`security-auditor` = medium; `escalate` = strong),
`model:` в ролях отсутствует; профили не редактируются ради выбора id; `general`/`explore` не
обходятся; права дорогих ролей не расширяются.
**Оперативные источники:** SKILL §Orchestrator role, §Host requirements (roles → agents);
`config/AGENTS.md` (Tier routing), `README.md` (§Тиры ролей); `config/agents/architect.md`;
`assets/agents/*.md` (tier labels, no `model:`); `config/profiles/*.jsonc` (`agent` block, только
чтение).

## I. Security-conditional gather и агрегатный вердикт

**Вход:** срабатывает security-триггер (auth/секреты/ввод/крипто); `security-auditor` возвращает
отчёт/находку.
**Требуемый исход:** security — **conditional gather-поток** CHECK; его результат **возвращается в
агрегат** и судится `check` (своего независимого вердикта нет; обычный security-дефект не обходит
агрегированный триаж); гейт 3 зелёный только при **всех** потоках; обычный security-провал считается
провальным CHECK текущей ревизии по общим счётчикам `n/3`/истории дефектов; немедленная эскалация —
только **жёсткий security-tradeoff**; финальный вердикт по всем потокам — `check`'s.
**Оперативные источники:** SKILL §Transition gates (gate 3, «every failed CHECK … triggered security
failure»), §Parallel CHECK streams (security gather/return; any failed stream counts as a failed CHECK
of the current revision), §Escalation (hard security trade-off, counters);
`assets/agents/security-auditor.md`, `assets/agents/check.md`.

## J. Решение эскалации: роутинг, не перевыбор и без обхода гейтов

**Вход:** `escalate` вернул решение. Два случая: (1) ревизия **не исчерпана**; (2) ревизия
**исчерпана** (третий провальный CHECK той же `r`).
**Требуемый исход:** `escalate` возвращает **решение**, не меню и не код; cheap-оркестратор исполняет
его **только маршрутизацией** — реально пересмотренный remediation-план `r+1` → `planner` (автор
плана), реализация по текущему плану или STOP статуса → `coder`; оркестратор **семантически не
перевыбирает** и план не переписывает. Решение **не отменяет** гейты, запрет 4-й попытки, scope и
security-ограничения; при **не исчерпанной** ревизии продолжение возможно по текущему плану, при
**исчерпанной** — 4-й попытки нет даже после эскалации, продолжение только через genuine `r+1`; нет
actionable-плана → **STOP** (обычный режим — вопрос пользователю; автономный — записанный STOP без
вопроса).
**Оперативные источники:** SKILL §Orchestrator role (execute by routing, never re-decide),
§Escalation (After the escalation …), §State machine (no 4th), §Red flags;
`config/agents/escalate.md`, `assets/agents/escalate.md`.

## K. Автономное делегирование: primary диспатчит `pdca-orchestrator`

**Вход:** cheap-tier primary; пользователь **явно** просит работать автономно; цикл ещё не начат.
**Требуемый исход:** primary **не ведёт** цикл сам, а вызывает `Task` на cheap-субагенте
`pdca-orchestrator` с **cycle brief** (goal, scope, acceptance criteria, constraints,
references); `pdca-orchestrator` проводит PLAN→DO→CHECK→ACT и возвращает компактную
**сводку ≤8 строк**; primary лишь передаёт сводку дальше и **не читает** файлы/логи и **не правит** их;
коллекционный статус-файл не создаётся, обязательный pdca-dotnet статус-файл пишет `coder`;
вопросы не задаются.
**Оперативные источники:** SKILL §Two paths → "Two paths, one contract." / §Autonomous mode
(Delegation) / §Host requirements (Autonomous driver; setup-allowlist включает `pdca-orchestrator`);
`config/agents/pdca-orchestrator.md` (вход «одиночный автономный цикл», cycle brief → сводка ≤8 строк).

## L. Fallback: `pdca-orchestrator` недоступен

**Вход:** автономная просьба, но `Task` к `pdca-orchestrator` невозможен — агент отсутствует,
либо `subagent_depth` < 2, либо `Task` запрещён хостом.
**Требуемый исход:** primary переходит в **flat primary** и ведёт цикл **сам** (PLAN→DO→CHECK→ACT
с теми же гейтами); fallback зафиксирован (`Notice:` в статус-файле); запрет 4-й попытки, scope и
security-ограничения **не отменяются**; вопросы по-прежнему не задаются.
**Оперативные источники:** SKILL §Autonomous mode (Delegation: fall back to the flat primary, log
the fallback) / §Host requirements (resource blocker); `config/agents/pdca-orchestrator.md`.

---

## Дополнительно: отвергнутый кандидат не сбрасывает ретраи

**Вход:** `planner` отвергает DO-кандидата/просит уточнение, план остаётся тем же.
**Требуемый исход:** это **не** новая ревизия (`r` не растёт) и **не** сброс счётчика попыток
(`n` не обнуляется); кейсы A/C/D не могут быть обойдены через «переоткрытие» кандидатом.
**Оперативные источники:** SKILL §State machine (rejected candidate not a new revision, does not
reset the attempt counter, not erased by a replan); `assets/agents/planner.md` item 10.
