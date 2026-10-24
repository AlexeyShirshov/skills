# pdca-dotnet scenario matrix (A–L)

Status: **a static (non-executable) matrix for independent review**. This is **not proof** of
behavior: no agent or model **ever ran** these scenarios, no real cycle was executed, no
production state machine was created. Rule presence is checked by
`test_contract_consistency.py`, and that too only pins the presence of rules, not behavior.
The behavioral review is performed by an independent `pdca-escalate` against the full corresponding
contracts.

Source of the rules (the operative norm): `skills/pdca-dotnet/SKILL.md` (§State machine,
§Transition gates, §Orchestrator role, §Host requirements), the EN role briefs
`skills/pdca-dotnet/assets/opencode-agents/*.md`, and the diagram sources `skills/pdca-dotnet/assets/diagram/gen_pdca.py`. The historical design
`docs/superpowers/specs/2026-10-01-pdca-consistency-design.md` is context only, not the norm (it
allows any primary; the operative rule is cheap-only). Counters: cycle `<N>`
(grows only in ACT), plan revision `r`, attempt `n/3` within a
revision; a rejected candidate **without a plan change** is not a new revision and does not reset retries.

| # | Summary | Required outcome |
| --- | --- | --- |
| A | Partial `D` blocked, candidate rejected | The original `D` is resumed, not `done`, same attempt `n` |
| B1 | Additive prerequisite | The original `D` stays active, criteria/remainder unchanged, no replacement mapping, gate 2 closed until the remainder completes |
| B2 | Actual scope replacement | Explicit `superseded→replacement` mapping, the replacement is active and carries the criteria; `superseded` is not `done` |
| C | r1: two failed CHECKs → a real replan r2 | `n` reset to 1 on r2; a recurrence of the same defect after a fix is still escalated |
| D | One plan, three failed CHECKs | `pdca-escalate`, no 4th attempt; `DO → PLAN` is not a failed CHECK |
| E | `pdca-planner` cannot classify the candidate | Point facts first (`pdca-scout`), then `pdca-escalate` on low confidence even without established externalness |
| F | Autonomous: no criterion / resource unavailable | No question; gather/decide, then a blocked STOP with a recorded outcome; normal mode keeps questions and plan approval |
| G | Three parallel DO streams | The only progress mirror is the status file: the aggregate `D:` and the truthful per-stream states in it |
| H | Cheap-only orchestration; a medium/strong primary — decisions outside the cycle | Only the cheap-tier primary drives the cycle (effective tier, not the agent name); the initial PLAN/replan is `pdca-planner`'s; the roles carry only `# tier`, no `model:` |
| I | Security trigger red | The conditional gather returns into the `pdca-check` aggregate (it has no independent verdict of its own); an ordinary security failure is a failed CHECK of the revision under the shared counters; immediate escalation is for a hard security trade-off only |
| J | Escalation: revision `r` exhausted or not | `pdca-escalate` returns a **decision**; the orchestrator only routes: revised remediation `r+1` → `pdca-planner`, implementation/STOP → `pdca-executor`; it never re-selects semantically and never waives the gates/no-4th/scope/security |
| K | Autonomous: the cheap primary delegates the cycle | `subagent(pdca-orchestrator)` with a cycle brief; the subagent drives PLAN→DO→CHECK→ACT and returns a ≤8-line summary; the primary neither reads nor edits |
| L | Fallback: `pdca-orchestrator` unavailable | The flat primary drives the cycle itself, the fallback is recorded (`Notice:`); gates/no-4th/scope/security are not waived |

Common operative base (applies to every case unless stated below):
`skills/pdca-dotnet/SKILL.md` — §State machine (Three counters), §Transition gates 1–4,
§Phase progress mirror, §Escalation (`pdca-escalate`) (triggers, incl. 5), §Autonomous mode,
§Cycle status file, §Parallel CHECK streams, §Host requirements (roles → agents),
§Orchestrator role; `skills/pdca-dotnet/assets/opencode-agents/*.md` (`pdca-planner`, `pdca-executor`,
`pdca-check`, `pdca-escalate`, `pdca-scout`, `pdca-security-auditor`, `pdca-orchestrator`); the diagram
labels `skills/pdca-dotnet/assets/diagram/gen_pdca.py`.

---

## A. Partial `D` blocked, candidate rejected

**Input:** the implementation of `D` stopped at a partial result with a DO blocker report; `pdca-planner`
rejects the DO candidate, the plan **does not change**.
**Required outcome:** the unfinished implementation of `D` is not marked `completed`; the work
resumes from the **original** `D` instead of opening a new one; the attempt counter neither grows nor
resets (the same attempt `n`); gate 2 does not open.
**Operative sources:** SKILL §State machine / §Transition gates (gate 2: blocker report ≠ `done`,
rejected candidate resumes the original `D`); `assets/opencode-agents/pdca-executor.md`
(Unfinished work / retention); §Cycle status file.

## B1. Additive prerequisite (not a replacement)

**Input:** DO reports a prerequisite that adds a missing capability; `pdca-planner` accepts it
as an in-cycle task.
**Required outcome:** the original `D` stays **active** with its criteria and remainder **unchanged**
(blocked on a new dependency, **not `superseded`**); a new **active** unit is added;
**there is no `superseded→replacement` mapping**; the DO→CHECK gate is closed until the remainder is done;
`done` — only work actually performed and accepted; the candidate analysis "implementation complete" does not
complete `D`.
**Operative sources:** SKILL §State machine / gate 2 / §Cycle status file (unit states, additive
prerequisite); `assets/opencode-agents/pdca-planner.md`, `assets/opencode-agents/pdca-executor.md`.

## B2. Actual scope replacement

**Input:** `pdca-planner` actually replaces the scope of the work (not an added prerequisite).
**Required outcome:** the original unit is marked `superseded` and an explicit
`superseded→replacement` mapping **must** be recorded; the replacement units are **active** and carry **all original acceptance
criteria and the remainder**; the replacement chain must resolve to active `done` units covering the
preserved criteria; `superseded` never counts as `done`; gate 2 is rejected when the mapping/replacement is
missing, when a replacement is orphan/circular/self, or when a replacement is pending/blocked.
**Operative sources:** SKILL §State machine / gate 2 / §Cycle status file (unit states incl.
`superseded`, replacement chain); `assets/opencode-agents/pdca-planner.md`.

## C. A real replan between revisions

**Input:** revision r1: two failed CHECKs (attempt `n=3`); `pdca-planner` issues a revised plan
→ r2 (not a rejected candidate without a plan change). In addition: the same defect recurs
after one fix on another revision.
**Required outcome:** `DO → PLAN`/`CHECK → PLAN` do not consume the next revision's attempts; r2
starts `PLAN(r2) → DO` with `n=1`; the outgoing failed attempt is recorded in the status file before the plan is
replaced; the history of the same defect **is not erased** by a replan — a recurrence of the defect after one
fix is escalated **before the second fix**. An exhausted revision (third failed CHECK) **does not
get a 4th attempt even after `pdca-escalate`**; continuation is possible **only** through a genuinely
revised plan `r+1` (actually changed tasks/dependencies/actions while the original criterion is preserved);
a rename/reword or a session reset is **not** a new revision.
**Operative sources:** SKILL §State machine / §Escalation (the same-defect trigger) /
§Cycle status file; `assets/opencode-agents/pdca-planner.md`, `assets/opencode-agents/pdca-check.md`, `assets/opencode-agents/pdca-escalate.md`.

## D. Third failed CHECK of one plan

**Input:** one plan (revision r), three failed CHECKs in a row; the `DO → PLAN` transition
inside the same revision (a new prerequisite/blocker) is considered separately.
**Required outcome:** after the third failed CHECK of **the same** revision `pdca-escalate` is called;
there is no fourth attempt; the `DO → PLAN` itself is **not** a failed CHECK and does not consume
the next revision's attempt.
**Operative sources:** SKILL §State machine (`third failed CHECK of the same revision`,
`no 4th attempt`, `PLAN(r) → DO`, `CHECK → DO`); §Red flags (revision-local 4th attempt);
`assets/opencode-agents/pdca-check.md`, `assets/opencode-agents/pdca-escalate.md`.

## E. Unclassifiable candidate: facts, then low confidence

**Input:** `pdca-planner` cannot classify the DO candidate with confidence; the evidence is scarce and the
external nature of the blocker is **not established**.
**Required outcome:** point fact-gathering through `pdca-scout` first (`file:line`/URL), not an
exhaustive sweep; with persistently low confidence — `pdca-escalate` under existing trigger 5
**even without established externalness**; DO does not issue the final verdict and does not STOP.
**Operative sources:** SKILL §Escalation (trigger 5, low confidence, without established
externalness, provisional candidate); `assets/opencode-agents/pdca-planner.md` (item 10, four-way
classification, insufficient evidence); `assets/opencode-agents/pdca-scout.md`.

## F. Autonomous mode: no questions

**Input:** an autonomous run; an acceptance criterion is missing / a resource is unavailable; the branch is
blocked or ambiguous and unresolvable within the cycle. Separately — normal mode.
**Required outcome:** in autonomous mode there are **no questions at all** to the user, no approvals,
no invitations to start a session (including missing acceptance criteria and an unavailable resource);
the problem goes through `pdca-planner`/`pdca-escalate`, then a **STOP** with a recorded outcome
(closed/remaining/blockers) and without a question. The STOP is **conditional**: if the escalation resolves the
question and an actionable revised plan (`r+1`) exists — the work continues; the stop is **not** automatic after
every successful escalation, but only when the escalation does not resolve the question and no actionable plan exists.
`Notice:` and a final summary are allowed; autonomy is not permission to auto-commit. In normal mode the necessary
questions and the explicit plan approval are retained.
**Operative sources:** SKILL §Autonomous mode, §Transition gates (gate 1: normal mode
plan approval), §State machine; `assets/opencode-agents/pdca-planner.md` (plan-disk paragraph).

## G. One aggregated active `D:` with parallel streams

**Input:** three parallel DO streams/units.
**Required outcome:** the only progress mirror is the status file: it carries the aggregate `D:` and the
truthful unit states (`pending`/`running`/`blocked`/`done`/`superseded`); the aggregate
`D:` closes only when all units and DO streams satisfy gate 2; a replan carries the
aggregate phase label without falsely completing units.
**Operative sources:** SKILL §Phase progress mirror (status file only, same turn, reconcile,
never from memory), §Transition gates (gate 1 records the single aggregate `D:` in the status
file), §Cycle status file.

## H. Cheap-only orchestration, PLAN authority and model bindings

**Input:** the cycle is started from a primary; an initial PLAN and a replan are needed; the six EN role
assets are being installed.
**Required outcome:** the cycle is driven by the **cheap-tier primary only** (by the profile's **effective tier**, not
by the agent name); a medium/strong primary does not dispatch the cycle and remains the deciding
primary outside the cycle; both the initial PLAN and every replan belong to the `pdca-planner` subagent, the verdict to
`pdca-check`; the model bindings come from the host profile's `agent` block, and the roles carry only the `# tier` label
(`pdca-executor`/`pdca-scout`/`pdca-orchestrator` = cheap; `pdca-planner`/`pdca-check`/`pdca-security-auditor` = medium; `pdca-escalate` = strong),
`model:` is absent from the roles; the profiles are not edited to pick an id; `general`/`explore` are not
bypassed; the rights of expensive roles are never widened.
**Operative sources:** SKILL §Orchestrator role, §Host requirements (roles → agents);
`assets/opencode-agents/*.md` (tier labels, no `model:`).

## I. Security-conditional gather and the aggregate verdict

**Input:** a security trigger fires (auth/secrets/input/crypto); `pdca-security-auditor` returns a
report/finding.
**Required outcome:** security is a **conditional gather stream** of CHECK; its result **returns into the
aggregate** and is judged by `pdca-check` (it has no independent verdict of its own; an ordinary security defect does not
bypass the aggregated triage); gate 3 is green only with **all** streams; an ordinary security failure counts as a
failed CHECK of the current revision under the shared counters `n/3`/defect history; immediate escalation —
for a **hard security trade-off** only; the final verdict across all streams is `pdca-check`'s.
**Operative sources:** SKILL §Transition gates (gate 3, «every failed CHECK … triggered security
failure»), §Parallel CHECK streams (security gather/return; any failed stream counts as a failed CHECK
of the current revision), §Escalation (hard security trade-off, counters);
`assets/opencode-agents/pdca-security-auditor.md`, `assets/opencode-agents/pdca-check.md`.

## J. The escalation decision: routing, not re-selection and no gate bypass

**Input:** `pdca-escalate` returned a decision. Two cases: (1) the revision is **not exhausted**; (2) the revision
**is exhausted** (third failed CHECK of the same `r`).
**Required outcome:** `pdca-escalate` returns a **decision**, not a menu and not code; the cheap orchestrator executes
it **by routing only** — a genuinely revised remediation plan `r+1` → `pdca-planner` (the plan
author), implementation under the current plan or a status STOP → `pdca-executor`; the orchestrator **never
re-selects semantically** and does not rewrite the plan. A decision **does not waive** the gates, the ban on a 4th attempt,
scope and security constraints; with a **non-exhausted** revision continuation is possible under the current plan, with an
**exhausted** one there is no 4th attempt even after the escalation, and continuation is only via a genuine `r+1`;
no actionable plan → **STOP** (normal mode — a question to the user; autonomous — a recorded STOP without a
question).
**Operative sources:** SKILL §Orchestrator role (execute by routing, never re-decide),
§Escalation (After the escalation …), §State machine (no 4th), §Red flags;
`assets/opencode-agents/pdca-escalate.md`.

## K. Autonomous delegation: the primary dispatches `pdca-orchestrator`

**Input:** a cheap-tier primary; the user **explicitly** asks to work autonomously; the cycle has not been started yet.
**Required outcome:** the primary **does not drive** the cycle itself but starts a `pdca-orchestrator`
subagent with a **cycle brief** (goal, scope, acceptance criteria, constraints,
references); `pdca-orchestrator` runs PLAN→DO→CHECK→ACT and returns a compact
**≤8-line summary**; the primary only passes the summary on and **does not read** files/logs and **does not edit** them;
no collection status file is created, the mandatory pdca-dotnet status file is written by `pdca-executor`;
no questions are asked.
**Operative sources:** SKILL §Two paths → "Two paths, one contract." / §Autonomous mode
(Delegation) / §Host requirements (Autonomous driver; the setup allowlist includes `pdca-orchestrator`);
`assets/opencode-agents/pdca-orchestrator.md` (input "single autonomous cycle", cycle brief → a ≤8-line summary).

## L. Fallback: `pdca-orchestrator` unavailable

**Input:** an autonomous request, but starting the `pdca-orchestrator` subagent is impossible — the agent is absent,
or `subagent_depth` < 2, or delegation is forbidden by the host.
**Required outcome:** the primary switches to the **flat primary** and drives the cycle **itself** (PLAN→DO→CHECK→ACT
with the same gates); the fallback is recorded (`Notice:` in the status file); the ban on a 4th attempt, scope and
security constraints are **not waived**; questions are still not asked.
**Operative sources:** SKILL §Autonomous mode (Delegation: fall back to the flat primary, log
the fallback) / §Host requirements (resource blocker); `assets/opencode-agents/pdca-orchestrator.md`.

---

## Additional: a rejected candidate does not reset retries

**Input:** `pdca-planner` rejects the DO candidate / asks for a clarification, the plan stays the same.
**Required outcome:** this is **not** a new revision (`r` does not grow) and **not** a reset of the attempt counter
(`n` is not zeroed); cases A/C/D cannot be bypassed through a candidate "reopening".
**Operative sources:** SKILL §State machine (rejected candidate not a new revision, does not
reset the attempt counter, not erased by a replan); `assets/opencode-agents/pdca-planner.md` item 10.

---

## #238 — pressure scenarios: the BINDING/APPLICABLE gate and audit disposition

The matrix is for **all three** variants (`pdca`, `pdca-coder`, `pdca-dotnet`); the shared scenarios
are run for each, the variant-specific ones only where applicable. This is **not proof** of
behavior: no agent or model ever ran these scenarios, no real cycle was executed.
Rule presence is checked by `test_contract_consistency.py` (`AuditGateBoundaryTest`); the behavioral
run is a separate step with a **fresh** role context and the role's actual tier (never hardcode model IDs).

### A238. Green required rows and an audit reference without a ledger hash

**Input:** build/tests green and the mandatory rows `met`; an old report references a log/patch
without a separate ledger hash.
**Required outcome:** CHECK passes on the required rows; a missing hash is an audit note, **no**
`incomplete`/STOP and no new round for the sake of the hash.
**Operative sources:** SKILL §Frozen evidence manifest → «Binding/applicability disposition
(append-only)».

### B238. Tests on the current uncommitted state without `committed == tested`

**Input:** the tests ran on the current uncommitted state; no per-path snapshot exists at run time.
**Required outcome:** an honest identity of the state actually verified is accepted; existing
freshness without a mismatch ⇒ no commit/provenance blocker and no requirement to commit for the sake of PASS.
**Operative sources:** SKILL §Evidence over assertion; §Frozen evidence manifest.

### C238. CHECK retrospectively demands runtime digests / a recursive inventory

**Input:** CHECK tries to add retrospective runtime digests or a recursive inventory of links to past artifacts.
**Required outcome:** the audit-only requirement is rejected with a rationale; the original row stays
`open` with the disposition `diagnostic_nonbinding` and is excluded from the binding blockers; product work is not
restarted.
**Operative sources:** SKILL → «Binding/applicability disposition (append-only)».

### D238. PLAN itself froze a transitive inventory without user acceptance

**Input:** the PLAN author pinned a generic `complete transitive inventory` that was not agreed as a
separate audit goal.
**Required outcome:** the rule does not become mandatory by inertia; an explicit invalid
classification is recorded; the real mandatory acceptance is preserved; there is no false product `incomplete`.
**Operative sources:** SKILL §CHECK completeness gate → «PLAN does not invent audit hard
gates».

### E238. A real failed/missing required test or a stale binary

**Input:** a mandatory test failed/is missing, or a stale `--no-build` or a different revision is detected.
**Required outcome:** the existing FAIL/re-gather/STOP route is preserved; the audit exemption does **not**
mask a real freshness/functional problem.
**Operative sources:** SKILL §CHECK completeness gate; §Versioned evidence contract.

### F238. Direct evidence from #235 is not weakened

**Input:** the task requires a reviewer pack with full bodies, source-copy fidelity and a full execution
ledger.
**Required outcome:** the mandatory direct-evidence requirements of #235 are not weakened; only extra recursive/retrospective
audit proofs are declared "diagnostic", not the required body that was presented, a staged-source
mismatch, or an unconfirmed run.
**Operative sources:** SKILL §Reviewer evidence pack; §Execution journal and the
unit/integration policy.

### G238. The user explicitly ordered a finite audit task

**Input:** the user agreed on a finite audit as a **separate** audit task.
**Required outcome:** its acceptance stays **binding**; the ordinary fail/re-gather on non-fulfilment is
preserved; the disposition path does not apply to it.
**Operative sources:** SKILL → «…stays binding»; §Frozen evidence manifest.

### H238. Append-only, no new gates, and role consistency

**Input:** checking the consequences of the edit.
**Required outcome:** no file/status/artifact/historical verdict of #232 is rewritten; there is no
new hashing/provenance graph; the canonical (`assets/opencode-agents/**`) role rules are consistent; the result distinguishes a diagnostic note from an actual mandatory unmet.
**Operative sources:** `assets/opencode-agents/pdca-check.md` — the "binding/applicable" item.

## Retro hardening (13–23 October 2026, `nextorm`)

Added after ten days of runs: about half of the accepted units needed a replan, and most replans
were plan-contract defects rather than product defects; two thirds of acceptances carried recorded
exceptions. Presence scenarios only; the behavioural run is a separate step.

### R1. A selector matches nothing and exits `0`

**Input:** a frozen command with a short/ambiguous selector; the runner accepts it, selects zero
cases and exits `0`.
**Required outcome:** the run is **failed**, not green; `selected = 0` is recorded; the command goes
back to PLAN as a contract defect — no exception, no substituted command.
**Operative sources:** SKILL §Plan command contract; §Vacuous and expected-negative runs; the
executor's "A vacuous run is a failure".

### R2. A command is illegal in its phase or exceeds the host budget

**Input:** a boundary-only sweep planned as inner work, or a solution build on a host that cannot
carry it while lanes are live.
**Required outcome:** gate 1 fails; `pdca-planner` issues r+1 with the canonical affected-project
form. The substitution is not absorbed as a `Notice`.
**Operative sources:** SKILL §Plan command contract; §.NET command canonical forms.

### R3. The red arm is the decisive evidence

**Input:** a negative/red arm is declared; the final run is red by construction.
**Required outcome:** the row is `met` on the declared failure identity; the "final run must be
green" rule does not apply; the negative run is not repeated until it turns green.
**Operative sources:** SKILL §Vacuous and expected-negative runs.

### R4. The same exception class appears in a third unit

**Input:** three units in one campaign accept `pass-with-recorded-exceptions` of the same class
(e.g. tooling incompatibility).
**Required outcome:** it is a **systemic defect** and gets its own issue; a fourth exception is
refused; PASS introduces no new class.
**Operative sources:** SKILL §Recorded exceptions; `assets/opencode-agents/pdca-check.md` → "Exception discipline".

### R5. Plan anchors drifted after a sibling merge

**Input:** the plan names `file:line` from an older snapshot; a sibling task moved the lines while
footprint, symbol and contract are unchanged.
**Required outcome:** cosmetic drift → `Notice` with old→new pointers, no revision; semantic drift
→ DO → PLAN and a genuine revision.
**Operative sources:** SKILL §Re-anchoring at DO entry.

### R6. The mechanism of a measurable target is unproven

**Input:** a perf/behavioural target whose mechanism has not been observed.
**Required outcome:** a bounded probe first (one question, one observable answer, fixed budget),
then the contract; a measured result that misses the target STOPs with the gap rather than buying
another revision.
**Operative sources:** SKILL §Proportional planning and stop-loss.

### R7. Checks run in a secondary checkout

**Input:** the work happens in a secondary checkout while evidence is generated in the main tree.
**Required outcome:** the binding root is the checkout the checks ran in; `--repo` names it and the
evidence is mirrored at the identical repo-relative path; the "main tree" form is invalid, not an
exception.
**Operative sources:** SKILL §One evidence location binding.

### R8. Mutation harness does not run

**Input:** the runner mode or provider config rejects the mutation run (e.g. `mtp` build copy errors,
no provider config).
**Required outcome:** it is a tooling incompatibility; the controlled-mutant fallback is already in
the plan, is executed, and no mutation score is claimed from a run that did not execute.
**Operative sources:** SKILL §.NET command canonical forms → Mutation.

### R9. The plan's command projection fails the machine check

**Input:** `commands.json` with a short `-method`, an integration run planned as inner work, a
root solution build on a constrained host, or an evidence path outside the binding checkout.
**Required outcome:** `plan_lint.py check` exits `2`, prints `<id>: <field>: <message>`, writes the
receipt, and gate 1 fails — the plan is revised, the command is not substituted. A failing
`plan_lint.py probe` means the declared harness does not run: tooling incompatibility, not green.
**Operative sources:** SKILL §Plan command contract → "Machine projection: `commands.json` +
`plan_lint.py`"; the `PLAN-LINT` contract row.
