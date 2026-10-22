# #238 — pressure-сценарии pdca (BINDING/APPLICABLE-гейт)

Матрица общей семантики #238 для домен-нейтрального варианта `pdca` (вариант-специфичные
строки помечены). Это **не доказательство** поведения: сценарии не запускались.

## #238 — pressure-сценарии: BINDING/APPLICABLE-гейт и audit-disposition

Матрица для **всех трёх** вариантов (`pdca`, `pdca-coder`, `pdca-dotnet`); общие сценарии
прогоняются для каждого, variant-specific — только где применимо. Это **не доказательство**
поведения: ни один агент/модель по этим сценариям не запускался, реальный цикл не исполнялся.
Наличие правил проверяет `test_contract_consistency.py` (`AuditGateBoundaryTest`); поведенческий
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
(`assets/agents/**`) role rules согласованы; результат различает diagnostic note и actual mandatory unmet.
**Оперативные источники:** `config/agents/pdca-check.md`, `assets/agents/pdca-check.md` —
пункт «binding/applicable».
