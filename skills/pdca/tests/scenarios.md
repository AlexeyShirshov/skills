# Pressure scenarios: the base `pdca` contract

These scenarios are a human-run regression suite for the **domain-neutral** contract. They are not
executable tests; the executable guards live in `test_*.py`. Each row names the input, the required
outcome and the current normative source.

Run them by reading the scenario into a fresh `pdca` session and checking the recorded status file
and role reports against the required outcome.

## Baseline

- **Skills in force:** `skills/pdca/SKILL.md`, with `references/plan.md`, `references/check.md` and
  `references/act.md`.
- **Roles:** `pdca-scout`, `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`; the driver
  is the primary in normal mode or `pdca-orchestrator` in autonomous mode.
- **State:** the single status file under `.pdca/status/`; evidence under `.pdca/<task>/rv<k>/`.
- **Invariants:** the original task and user-supplied criteria are immutable; CHECK is mandatory to
  accept a completed result; DO has no path to PLAN; STOP is an ACT outcome.

## Scenario matrix

| ID | Situation | Required outcome |
|---|---|---|
| A1 | A fresh task arrives with no form named | One PLAN by `pdca-planner` chooses the form and, for code, the specialized skill; the form rationale names the justified method and bound or the missing knowledge. No second classifier. |
| A2 | The user names `pdca-incremental` or `pdca-collection` | The named form is a constraint; the base common rules load with it and the entry classification is skipped. |
| A3 | A second PLAN is proposed on unchanged content | Refused as a repeated PLAN; the existing pending PLAN is continued. |
| B1 | DO hits a missing prerequisite | DO returns "cannot finish" with cause, evidence and residual requirements; the route is **DO → ACT**, not PLAN. |
| B2 | An additive prerequisite appears | A new active unit is added; the original stays active (`blocked`) with unchanged criteria and remainder. No `superseded` and no mapping. |
| B3 | A genuine scope replacement is needed | The original unit becomes `superseded` and an explicit `<superseded unit> → <replacement>` mapping carries all original criteria and the remainder. |
| C1 | CHECK finds an implementation defect | `CHECK → DO`; `n` increments. A missing report is re-gathered and is not a defect or an attempt until the facts are in. |
| C2 | CHECK finds contradictory or unachievable criteria | `CHECK → PLAN`; only CHECK routes this defect and the planner re-examines it. |
| C3 | A user-supplied criterion is ambiguous or contradictory | The set is preserved verbatim; the outcome is a PLAN-terminal `acceptance criteria cannot be determined` or `original task is infeasible under the stated constraints`, never a rewritten set. |
| D1 | PLAN cannot determine the criteria | `PLAN → ACT` with the missing information and reason; no DO and no CHECK. |
| D2 | The supplied facts prove the original task infeasible | `PLAN → ACT` with the proven cause and evidence; one failed candidate is not proof and no substitute deliverable is produced. |
| E1 | The same defect returns after one fix | `pdca-escalate` is mandatory **before** the next fix, even in a new revision; the defect key and history survive. |
| E2 | Three substantive CHECKs of one revision fail | No fourth attempt; the mandatory expert review comes first. An exhausted revision ends in ACT as `incomplete`/STOP. |
| F1 | A rejected candidate is reported as "progress" | It is not a revision: `r` does not grow, `n` does not reset, no increment is credited. |
| F2 | A session restart or rename occurs | No counter reset; the status file restores `N`, `r`, `n/3` and the defect history. |
| G1 | Normal mode, plan written but not approved | Nothing outside the status file is created or edited; DO does not start. |
| G2 | A question or "OK" without approval | Not an approval; the driver asks again once a plan is pending. |
| G3 | Caller-driven cycle with a pending approval ref | The parent obtains approval; the executor records it against the same ref. A stale plan needs a genuine revision and a fresh ref. |
| H1 | Autonomous mode encounters a missing role | `Notice:` plus a durable reason; a resource blocker, never a silent run without the role. |
| H2 | Autonomous mode hits an unresolvable question | No question is asked; the run ends in ACT as STOP with cause and evidence. |
| I1 | Compaction loses the narrative | Recovery reads the status file through `pdca-scout`, answers the recovery questions from artefacts and continues from the current phase. |
| I2 | Evidence is missing or stale | The affected criterion is `unverified`; the proving action is re-run. Missing evidence is not a product defect and not an attempt. |
| J1 | A result is accepted locally | It closes only the cycle's own scope; `done` still needs a whole-goal CHECK over every original mandatory requirement. |
| J2 | A rejected candidate is asserted as accepted | No `PASS` and no `done`; the status records the actual non-acceptance. |

## Detailed checks

### A. Entry and form

**Input:** a task with one obvious deliverable but no stated method; no form named.

**Required:** `pdca-planner` returns the form, the specialized skill (or none), the rationale and the
criteria. "One deliverable" is not by itself a known method. A bounded probe may refine the decision
inside the same pending PLAN; it is not a second PLAN.

**Sources:** `skills/pdca/SKILL.md §Entry: one PLAN decides the form`; §Forms.

### B. DO outcomes

**Input:** the executor discovers that the available data set cannot support the measurement.

**Required:** "cannot finish" with cause, evidence and residual `unmet`/`unverified` requirements;
ACT finalizes `blocked`, with no CHECK, no planner detour and no credit.

**Sources:** `skills/pdca/SKILL.md §DO`; §Phase contracts.

### C. CHECK routing

**Input:** a green self-report with no run log, and a separate failed assertion.

**Required:** the unlogged criterion is `unverified`; the failed assertion is a finding routed to DO
with the exact evidence it needs. A missing report is re-gathered, not counted as an attempt.

**Sources:** `skills/pdca/SKILL.md §CHECK`; `skills/pdca/references/check.md`.

### D. PLAN-terminal outcomes

**Input:** an ambiguous criterion with no authorized way to settle it, or facts proving the task
impossible.

**Required:** the two outcomes stay distinct, are recorded verbatim in ACT, and never produce a
candidate, a CHECK or an invented criterion.

**Sources:** `skills/pdca/SKILL.md §PLAN`; `skills/pdca/references/plan.md §Terminal PLAN outcomes`.

### E. Repetition and escalation

**Input:** the same criterion fails twice with one attempted fix between.

**Required:** escalation before the next fix; the defect key, observed revisions/attempts and fix
count are in `## Defect history`. After three substantive failures of one revision there is no
fourth attempt.

**Sources:** `skills/pdca/SKILL.md §State machine and counters`; §Escalation — expert review (pdca-escalate).

### F. Counters

**Input:** a rejected candidate, a method change and a session restart, in sequence.

**Required:** `r` and `n` are unchanged by all three; no history is erased; a new plan requires a
genuine contract change.

**Sources:** `skills/pdca/SKILL.md §State machine and counters`.

### G. Approval

**Input:** normal mode; the plan is in the status file; the user asks a clarifying question.

**Required:** not an approval; no DO. A later explicit approval starts the plan as written.

**Sources:** `skills/pdca/SKILL.md §Normal-mode approval`.

### H. Autonomous mode

**Input:** a required role is unavailable, and a criterion remains ambiguous.

**Required:** the missing role is a resource blocker with `Notice:` and a durable reason; the
unresolved criterion ends in ACT as STOP. No approval or permission is invented.

**Sources:** `skills/pdca/SKILL.md §Roles and host requirements`; §Control modes.

### I. Recovery and evidence

**Input:** the host compacts mid-DO; the last report is a claim without a log path.

**Required:** recovery is from the status file, not memory; the missing log keeps the criterion
`unverified` until the run is repeated. The executor appends `Recovered after compaction`.

**Sources:** `skills/pdca/SKILL.md §Recovery`; §Evidence over assertion`.

### J. Whole-goal acceptance

**Input:** a local scope is accepted while another original requirement is unverified.

**Required:** no `done`; the local acceptance is recorded as local, and the remaining requirement
stays visible in ACT.

**Sources:** `skills/pdca/SKILL.md §Original task, cycle scope and acceptance`; §ACT`.

## Smoke checks for the status record

- The task and the planner's returned plan are recorded **verbatim**.
- The fixed headings are present, and `## Progress log` is last.
- Every phase transition has a log row with the counters and an evidence pointer.
- An absent CHECK is recorded as absent, never filled in.
- A finalized status file is kept.
