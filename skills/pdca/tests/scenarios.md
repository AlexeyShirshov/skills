# #238 — pressure-сценарии pdca (BINDING/APPLICABLE-гейт)

Матрица общей семантики #238 для домен-нейтрального варианта `pdca` (вариант-специфичные
строки помечены). Это **не доказательство** поведения: сценарии не запускались.

## #238 — pressure-сценарии: BINDING/APPLICABLE-гейт и audit-disposition

Матрица для **всех трёх** вариантов (`pdca`, `pdca-coder`, `pdca-dotnet`); общие сценарии
прогоняются для каждого, variant-specific — только где применимо. Это **не доказательство**
поведения: ни один агент/модель по этим сценариям не запускался, реальный цикл не исполнялся.
Наличие правил статическим guard'ом сейчас не проверяется; поведенческий
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
нового hashing/provenance-графа; хостовый бриф `config/agents/pdca-check.md` и canonical
(`assets/opencode-agents/**`) role rules согласованы; результат различает diagnostic note и actual mandatory unmet.
**Оперативные источники:** `config/agents/pdca-check.md`, `assets/opencode-agents/pdca-check.md` —
пункт «binding/applicable».

## Вход, известность метода и пропорциональная проверка (presence; не запускалось)

Это **presence-сценарии**, а не доказательство поведения: модель/агент по ним не запускались,
реальный цикл не исполнялся. Наличие части правил проверяет `test_routing_consistency.py`.

### E1. Один готовый результат, метод неизвестен

**Вход:** пользователь просит один файл/один готовый результат, но не задаёт метод; из брифа не
видно, какая последовательность действий уже обоснована.
**Требуемый исход:** форма не объявляется `cycle` только из-за одного deliverable: PLAN называет
недостающее знание и выбирает incremental либо один ограниченный choice-probe; полный downstream
дизайн не замораживается до ответа probe.
**Оперативные источники:** SKILL §Entry → «A fresh, unclassified task…»; §Forms → «One deliverable
is not a known method»; `references/plan.md` §Proportional planning.

### E2. Известная ограниченная последовательность

**Вход:** метод известен, шаги зависимы, объём фиксирован (передача результата шага в следующий).
**Требуемый исход:** ordinary cycle; зависимость данных не выдаётся за неопределённость, лишний
incremental не навязывается.
**Оперативные источники:** SKILL §Forms → ordinary/incremental discriminators.

### E3. Допустимые модельные предположения

**Вход:** расчёт допускает явные предположения, которые ограничивают результат; проверяемого
механизма они не доказывают.
**Требуемый исход:** ordinary cycle допустим, если предположения записаны как assumptions и
ограничивают объём; assumption не выдаётся за свидетельство работоспособности decision-critical
механизма.
**Оперативные источники:** SKILL §Forms; `references/plan.md` §Gap closure.

### E4. Не хватает evidence для decision-critical механизма

**Вход:** формально есть «полный» дизайн, но ключевой механизм не продемонстрирован; probe
проверяет уже выбранные числа.
**Требуемый исход:** это не known method: выбор действия остаётся открытым до наблюдаемого
результата probe; post-hoc проверка не переименовывается в exploration.
**Оперативные источники:** SKILL §Forms → probe before dependent work; `pdca-planner` §Form.

### E5. Пользователь ограничил форму

**Вход:** пользователь явно назвал `pdca-incremental` (или другую форму/контракт).
**Требуемый исход:** ограничение уважается; PLAN работает внутри него и не перенаправляет молча.
**Оперативные источники:** SKILL §Entry; §Forms.

### E6. Самодельный checker без обоснования

**Вход:** PLAN предлагает новый executable checker, хотя carrying claims проверяются независимым
наблюдением или точечным пересчётом.
**Требуемый исход:** verification economy требует cheapest sufficient method; bespoke checker
допустим только с конкретной причиной, почему существующие/manual средства недостаточны, и с
пропорциональной границей.
**Оперативные источники:** `references/plan.md` §Verification economy; `pdca-planner` §Plan hygiene.

### E7. Уже запланированный resume

**Вход:** есть persisted `plan_handoff` с form/ref; повторный вход не должен заново решать форму.
**Требуемый исход:** тот же controller принимает решённый контекст; нет второго PLAN ради
маршрутизации и нет нового dispatcher; applicability и approval идут по существующим правилам.
**Оперативные источники:** `pdca-orchestrator` §Entry stage; §Input 2.

### E8. Свежая коллекция — handoff владельцу, а не lane

**Вход:** entry PLAN выбрал `collection`, но dispatcher пытается сам стать batch owner, применить
lane-правила ко всему batch или создать отдельный lane-context.
**Требуемый исход:** entry controller передаёт существующий batch plan by reference обратно
cheap primary/collection owner; тот загружает `pdca-collection` и запускает per-item/lane механику
в существующих правах. Начальный batch choice не повторяется, каждый item получает свой PLAN;
`collection-lane` остаётся существующим caller-dispatched lane; batch ownership и lane duties
различны, single-lane batch — норма; self-delegation/recursion и новый контекст/роль не появляются.
**Оперативные источники:** `pdca-orchestrator` §Entry stage; `pdca-collection/SKILL.md`
§Ownership.

### E9. Entry-owned plan не пересобирается в Input 2

**Вход:** entry PLAN уже вернул и сохранил initial plan, затем поток входит в «new cycle».
**Требуемый исход:** план переиспользуется by reference; controller стартует с текущего
PLAN → DO gate со всеми validation/approval; второй full PLAN не запускается; named plan ref в
существующем brief/status достаточен, новых state-файлов/схем/счётчиков нет.
**Оперативные источники:** `pdca-orchestrator` §Entry stage шаг 5; §Input 2.

### E10. Form-known dispatch без собственного плана

**Вход:** форма известна, но task-own PLAN действительно отсутствует (например, collection item);
либо есть persisted `plan_handoff`/resume.
**Требуемый исход:** отсутствующий task-own PLAN выполняется по существующим правилам; resume не
перепланируется; это не mixing с entry-owned планом.
**Оперативные источники:** `pdca-orchestrator` §Entry stage шаг 5; §Input 1–2.

### E11. Bounded choice probe до решения формы

**Вход:** planner не может обосновать форму без одного наблюдаемого факта.
**Требуемый исход:** planner авторизует **один** bounded choice probe с open decision, observable
outcomes и budget; `pdca-executor` выполняет probe, `pdca-scout` наблюдает, тот же planner уточняет
**тот же pending PLAN**; форма остаётся `UNDECIDED` до выбора; нет independent cycle, fresh
controller, per-tool CHECK или extra full PLAN; права/approval не ослабляются.
**Оперативные источники:** `pdca-orchestrator` §Entry stage → «Bounded choice probe»;
`pdca-planner` §Form.

### E12. Bespoke checker без rationale

**Вход:** PLAN предлагает самодельный checker, но не даёт concrete insufficiency reason и bound.
**Требуемый исход:** dispatcher проверяет только присутствие этих двух элементов и возвращает
**incomplete pending PLAN** тому же planner; necessity он не судит; новый validator/checker не
создаётся.
**Оперативные источники:** `pdca-planner` §Plan hygiene → «Verification choice»;
`pdca-orchestrator` §Entry stage.

### E13. Контракт fresh entry — только база

**Вход:** fresh dispatch (`form: UNDECIDED`) несёт `contract: pdca`; оверлей/форма ещё не решены.
**Требуемый исход:** загружается только base `pdca` (не cycle/step contract, оверлей не требуется);
post-decision loader берёт форму/оверлей из решения planner, не из семантического выбора драйвера;
отсутствующий base contract и отсутствующий старый cycle/step contract одинаково fail closed.
**Оперативные источники:** `pdca-orchestrator` §Contract.

### E14. Bounded continuations не расширяют planner cap

**Вход:** незавершённая clarification или choice-probe refinement после начального PLAN.
**Требуемый исход:** это продолжения **того же pending PLAN**, а не новые strategic decisions; они
считаются учётными записями усилий (границы probe задаются открытым решением, наблюдаемыми исходами и evidence, а не минутным капом), без unchanged
confirmation/restart/unbounded retry и без лишнего вызова ради routing; успешный обычный путь
остаётся `1 + number of steps`.
**Оперативные источники:** SKILL §Lens; `pdca-planner` §Step boundary.

### E15. Campaign bootstrap order

**Вход:** entry PLAN выбрал `campaign`.
**Требуемый исход:** `pdca-executor` сохраняет immutable preparation record + `preparation_ref` из
entry-плана (тот же pending PLAN уточняется только при реально недостающих полях), затем
baseline/runtime, затем first step DO; initial PLAN не дублируется, approval/counters — по
incremental-контракту.
**Оперативные источники:** `pdca-orchestrator` §Entry stage шаг 4;
`pdca-incremental` §0 Bootstrap.

## Ретро-харденинг (13–23 октября 2026, `nextorm`)

Правила добавлены по итогам десяти дней запусков: половина принятых задач потребовала реплана,
и большинство репланов были дефектом контракта плана, а не продукта. Это presence-сценарии;
поведенческий прогон — отдельный шаг.

### R1. Селектор не выбрал ни одной цели, код выхода `0`

**Вход:** замороженная команда с коротким/неоднозначным селектором; инструмент принимает его,
выбирает 0 целей и завершается `0`.
**Требуемый исход:** прогон — **failed**, а не green; фиксируется `selected = 0`; команда
возвращается в PLAN как дефект контракта, без «исключения» и без подстановки другой команды.
**Оперативные источники:** SKILL §Plan command contract; §Vacuous and expected-negative runs.

### R2. Команда запрещена в своей фазе или превышает бюджет хоста

**Вход:** boundary-only прогон запланирован как inner; либо сборка всего workspace на хосте,
который её не выдерживает.
**Требуемый исход:** gate 1 не проходит; `pdca-planner` выпускает r+1 с законной формой команды.
**Оперативные источники:** SKILL §Plan command contract → «phase is legal» / «scope matches the
declared budget».

### R3. Красная ветка является решающим доказательством

**Вход:** negative/red arm объявлен в контракте; финальный прогон по определению красный.
**Требуемый исход:** строка `met` по объявленной identity отказа; правило «финальный прогон
зелёный» не применяется; красный прогон не перезапускается до зелёного.
**Оперативные источники:** SKILL §Vacuous and expected-negative runs.

### R4. Один класс исключения повторяется в третьей задаче кампании

**Вход:** три unit'а подряд получают `pass-with-recorded-exceptions` одного класса
(например, tooling incompatibility).
**Требуемый исход:** класс фиксируется как **systemic defect** и заводится отдельной задачей;
четвёртое исключение не принимается, PASS не вводит новый класс.
**Оперативные источники:** SKILL §Recorded exceptions: catalog and repetition threshold;
`assets/opencode-agents/pdca-check.md` → «Exception discipline».

### R5. Якоря плана разъехались после мержа соседней задачи

**Вход:** plan указывает `file:line` на снимке, sibling-задача сместила строки; footprint,
символ и контракт не изменились.
**Требуемый исход:** cosmetic drift → `Notice` со старыми→новыми указателями, без r+1;
semantic drift → DO → PLAN и настоящая ревизия.
**Оперативные источники:** SKILL §Re-anchoring at DO entry.

### R6. Механизм измеримой цели не доказан

**Вход:** perf/поведенческая цель, механизм которой ещё не наблюдался.
**Требуемый исход:** сначала bounded probe (один вопрос, один ответ, фиксированный бюджет),
затем контракт; если измеренный результат не достигает цели — STOP с зафиксированным разрывом,
а не ещё одна ревизия в надежде на другое число.
**Оперативные источники:** SKILL §Proportional planning and effort policy.

### R7. Работа идёт во вторичном checkout

**Вход:** проверки выполняются в отдельном checkout, evidence — в главном дереве.
**Требуемый исход:** binding root — checkout проверок; `--repo` называет его, evidence
зеркалируется по тому же относительному пути; форма «main tree» недействительна, а не исключение.
**Оперативные источники:** SKILL §One evidence location binding.

### R8. Кампания сложила почти все unit'ы в одну последовательную группу

**Вход:** кластеризация оставляет 40+ unit'ов в одной цепи, хотя семейства файлов не пересекаются.
**Требуемый исход:** ширина — цель кластеризации: компонент режется на footprint-disjoint группы;
иначе деградация до одной полосы обосновывается в статусе; `cap` выводится из бюджета хоста.
**Оперативные источники:** `pdca-collection` §P.4; §Parameters.

### R9. Машинная проекция плана не проходит проверку

**Вход:** `commands.json` с коротким идентификатором селектора, integration-прогон, запланированный
как inner-работа, сборка всего workspace на ограниченном хосте или путь свидетельств вне binding
checkout.
**Требуемый исход:** `plan_lint.py check` выходит с `2`, печатает `<id>: <field>: <message>`, пишет
receipt, и гейт 1 не пройден — план ревизуется, команда не подменяется. Провал
`plan_lint.py probe` означает, что объявленный harness не запускается: несовместимость
инструмента, а не green.
**Оперативные источники:** `references/plan.md` §Machine projection: `commands.json` and
`plan_lint.py`; строка контракта `PLAN-LINT`.
