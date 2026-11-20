# Collection status — calc-20261021

## Collection input
- collection-id: calc-20261021
- source: user-supplied collection; order is fixed.
1. T1 — add mul(a, b) to calc.py with a doctest.
2. T2 — make the report faster. The acceptance metric, the measurement recipe and the target must be chosen by me (the user). I have not chosen them, and you may not invent or assume them.
3. T3 — add README.md describing the project.

## Collection units (per-unit fields)
| unit | order | form | contract+overlay | plan_state | preparation_state | preparation_ref | campaign_ref | disposition | status | gap / readiness reason |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | 1 | cycle | `pdca` + `coder` | ready | n/a | — | — | active | pending | — |
| T2 | 2 | campaign | — (step-level) | n/a | pending | — | — | active | pending | User-reserved acceptance metric, measurement recipe and target are unchosen; user unavailable; invention/assumption forbidden. No ready preparation may be created. |
| T3 | 3 | cycle | `pdca` + none | ready | n/a | — | — | active | pending | — |

- Pending approval refs: none (ALL-barrier not passed; no DO started; user unavailable in this run).

Unit notes:
- `form` is fixed by the collection PLAN: T1/T3 are `cycle`, T2 is `campaign`.
- A campaign item has no item-level contract/overlay; the contract/overlay of a concrete step is chosen later by `pdca-planner` for that step.
- Readiness (`plan_state` / `preparation_state`), campaign runtime `Status`, and per-unit `disposition` are three different things; readiness is not runtime and not completion.
- Rule: an item record without a `form` reads as `cycle`; an unrecognised form value fails closed.

## Groups
| group | units (order) | worktree | branch/ref | status | note |
|---|---|---|---|---|---|
| — | — | — | — | — | Not formed: ALL-barrier not passed; no lane allocated. |

## Tasks (queue; source of truth)
| task | unit | group | branch | status | plan_state | contract+overlay | cycle_id (N) | canonical task status path | plan_revision | baseline ref | footprint / predecessor / prerequisite refs | incomplete reason + patch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | T1 | — | — | pending | ready | `pdca` + `coder` | T1-1 | .pdca/status/T1-1.md | r1 | — | footprint: calc.py (low uncertainty); no predecessor; prerequisites: writable calc.py, python3.10 + doctest | — |
| T2 | T2 | — | — | pending | n/a | — | — | .pdca/calc-20261021/items/T2/plan-gap.md | — | none | preparation gap: user-reserved metric/recipe/target unchosen; no report artifact; no predecessor can supply them | pending campaign preparation; no preparation_ref, no baseline, no invented threshold |
| T3 | T3 | — | — | pending | ready | `pdca` + none | T3-1 | .pdca/status/T3-1.md | r1 | — | footprint: README.md (low uncertainty); no predecessor required (not gated on T1); prerequisites: repo root writable | — |

## Phase decisions log
- 2026-10-21 bootstrap (`pdca-planner`): collection-id `calc-20261021`; T1 `cycle` (`pdca` + `coder`), T2 `campaign` (no item-level contract), T3 `cycle` (`pdca` + none); order T1 → T2 → T3 unchanged.
- 2026-10-21 T2: acceptance metric, measurement recipe and target are user-reserved and unchosen; no values invented; `preparation_state=pending`, no `preparation_ref`.
- ALL-barrier: awaiting own PLAN for T1 and T3 and campaign preparation for T2. DAG/groups/lanes are not created before the barrier.
- 2026-10-21 Notice: host denied nested delegation (Subagent depth limit reached (1)); flat-primary fallback used for all three COLLECTION TASK PLANs (collection Fallback).
- 2026-10-21 T1 own PLAN complete: plan_state=ready, r=1, status path .pdca/status/T1-1.md; DO not started.
- 2026-10-21 T2 campaign preparation: user-reserved metric/recipe/target unchosen; preparation_state=pending, no preparation_ref, gap record .pdca/calc-20261021/items/T2/plan-gap.md; no baseline/runtime/steps.
- 2026-10-21 T3 own PLAN complete: plan_state=ready, r=1, status path .pdca/status/T3-1.md; DO not started.
- 2026-10-21 ALL-barrier validation (pdca-planner): FAIL. T1 cycle PASS (plan_state=ready, r1, T1-1); T3 cycle PASS (plan_state=ready, r1, T3-1); T2 campaign FAIL (preparation_state=pending, preparation_ref=none, readiness=gap). T2=gap awaiting user-reserved acceptance metric/measurement recipe/target; not a ready placeholder and not terminal incomplete. No DAG/groups/clustering/lane allocation; DO FORBIDDEN. No schedule; no plan-revision vector bound. T1/T3 plans reusable without a fresh PLAN unless a real applicability failure occurs (scenario h). Next: user supplies T2 reserved inputs; approve preparation with a single preparation_ref and preparation_state=ready; then re-run the ALL-barrier.

## PLAN revision vector used for schedule
- Unbound. The ALL-barrier failed, so no DAG/clustering/schedule was produced and no plan-revision vector is bound. Per-unit revisions remain: T1 r1, T3 r1; T2 none.

## General verification and recovery
- Overall C: not run — no DO, no integrated tree.
- Verification state: unverified.
- Blocking reason: ALL-barrier FAIL — T2 campaign preparation_state=pending with no preparation_ref because the user-reserved acceptance metric, measurement recipe and target are unchosen.
- Defect id / history: none.
- Corrective task status file: none.
- Next allowed step: user supplies the T2 metric/recipe/target; approve T2 preparation (single preparation_ref, preparation_state=ready); re-run the ALL-barrier. Until then: no DAG, no groups, no lanes, no DO.

## Done / Verified / Incomplete
- Done: none.
- Verified: no.
- Incomplete: none.
- Current outcome: P phase complete and stopped exactly at the ALL-barrier. T1/T3 own PLANs are ready (r1) and persisted; T2 is a gap. No DAG/clustering/lanes, no DO, no product code written.
