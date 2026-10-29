# ACT: closing, status and handoff

Reference for the ACT phase and the durable cycle status file. Read it when the status file is
**created or updated**, not only in ACT: §Status file holds the one fixed skeleton that
`pdca-executor` renders. The transitions, the acceptance rule and the counters stay in
`../SKILL.md` (§State machine and counters, §Phase contracts → ACT, §Workspace and durable status,
§Recovery); this file does not restate them.

## Closing order

ACT closes every cycle and is its only closing path. It records the outcome the ending phase already
determined: it issues no new verdict, no expert waiver and no approval, and it never implements,
tests or changes a product, test or checked artifact.

1. **Durable lesson** — 0–2 transferable conclusions, only where the host already provides durable
   memory writable within the current permissions: reusable beyond this workspace, no natural home in
   the status file, no product effect, no new write permission. A no-op is normal; no repository or
   host-config edit is required or implied by closing.
2. **Status file — finalized by `pdca-executor`**, always: the driver passes the reports of the phases
   that actually ran (PLAN's returns, DO's results, CHECK's verdict) **as returned** — each complete
   original in its own language, or an exact reference to a complete persisted artefact the executor
   can read, never a digest or translation — and the executor records the outcome, the criteria
   outcome and the handoff — or, for a non-accepted outcome, the cause, evidence, residual
   `unmet`/`unverified` requirements, counters and defect history, with no `PASS` and no `done`.
3. **Lifetime** — finalized and **kept**, never deleted: the record of a closed flow and the input to
   any later PLAN. Cycle `N` is finalized in ACT; a further cycle is a separate authorized PLAN under
   §State machine and counters, never an automatic reopening.

Work discovered while finalizing is never slipped in under ACT: before the result is accepted and
finalized it goes through the existing phase contracts (an implementation change → DO and a final
CHECK; a contract defect → the CHECK finding that routes it to PLAN). ACT adds no transition of its
own.

**Per route, ACT only writes down what the phase determined:**

| Route | Recorded |
|---|---|
| `CHECK → ACT`, accepted | the accepted result, the criteria outcome per criterion, the evidence pointers, limitations, handoff |
| `PLAN → ACT` | the resolution — `acceptance criteria cannot be determined` with the concrete missing information and reason, `goal cannot be measured under the available means` with the missing metric/instrument/basis and the evidence, `original task is infeasible under the stated constraints` with the proven cause and evidence, or `requested result already established` with the result, its derivation and the evidence pointers (recording that no independent CHECK ran); no invented criteria, no substitute deliverable, no `PASS`, no CHECK |
| `DO → ACT` | the cause, what was completed, what remains (`unmet`/`unverified`), evidence pointers; no CHECK, no planner detour |
| `CHECK → ACT`, terminal | the incomplete/`STOP` outcome with the remaining criteria, counters and defect history; no `PASS`, no `done` |

The status file states the phase actually reached and names a check that did not happen as absent
instead of reconstructing a history. Accepted and incomplete outcomes stay visibly distinct.

**When STOP is the outcome.** STOP is an outcome of ACT, never a phase or a path beside it: it is
finalized only once the **originating phase** confirms that no permitted continuation remains — an
unresolved consultation, a PLAN that cannot determine the criteria, proves the goal unmeasurable or
proves the original task infeasible, an unresolvable constraint, a DO that cannot finish, a refused
required approval, or CHECK attempts exhausted under the no-4th rule — and only that phase, applying
its own transitions, decides it; a consultation alone needs no new plan (`../SKILL.md` §Phase
contracts → ACT).

## Status file

Default path `.pdca/status/<task>-<N>.md`: `<task>` a kebab slug, `<N>` the task's cycle number
(`../SKILL.md` §State machine and counters). Written only by `pdca-executor`, in the same turn as the
event.

**One fixed shape.** `pdca-executor` initializes a new file as exactly the skeleton below **at the
first status write** and then fills only the section of the phase that actually ran. It never derives
the shape from a neighbouring status file, never picks where a phase goes by imitation, and never
invents an ordering: the headings stay stable, `## CHECK record` always precedes `## ACT record` and
the log, and `## Progress log` is last. Task-specific data (code rows, .NET rows, collection
disposition, sub-task tables) nests inside the matching section — never as a new competing top-level
section. The body is written in the language of the user's dialogue, and the user's task, the criteria
and every phase report are recorded verbatim in their original language. A missing source is recorded
as missing and is never replaced by an invented report. When a raw block itself contains fences,
enclose it in an outer fence longer than any fence it contains; the recorded bytes are unchanged.

````markdown
# Cycle status: <task> / cycle <N>

## Current state

- task: `<task-slug>` · form: `<form>` · specialized skill: `<none | pdca-coder | pdca-dotnet>`
- mode: `<normal | autonomous>`
- cycle: `N=<N>` · revision: `r=<r>` · attempt: `n=<n>`
- scope: `<what this cycle covers>` · status path: `<path>`
- goal: `<the requested result in one line>` — the §PLAN record and §Original task are authoritative
- phase: `<PLAN | DO | CHECK | ACT>` · record: `<open | completed>` · outcome: `pending` (a completed record keeps its last real phase `ACT` plus the final outcome; neither adds a phase)
- source: `<where the task came from>` · context refs: `<refs>`
- criteria: `<current cycle criteria identity>` — exact text in §PLAN record `r<r>` (source: `<ref>`), not retyped here

## Original task

`pending: original task not supplied` — or the user's task verbatim, in its original language, with
the user-supplied criteria if any. Never a summary, translation or reconstruction.

## PLAN record

### r1

`not reached: no PLAN yet` — or the planner's **complete** returned report, verbatim, in its original
language: the whole plan, not a digest. A revision appends `### r<new>` with its complete report and
keeps every earlier `### r<k>` block byte-identical; a later block never replaces an earlier one.

## Approval record

`not applicable: autonomous mode` · or `pending: approval requested <ref> at <time>` · or the approval
against that ref (task/`cycle_id`, `N`, `r`, criteria set): approver, time, reason and any explicit
stop-at-estimate choice. Never fabricated.

## DO result

`not reached: no DO yet` — or what was completed, the candidate, unit states and evidence pointers
(exit status, key numbers, log path). A candidate is not a verdict.

## CHECK record

`not run: <reason>` (for example `PLAN → ACT`, `DO → ACT`) — or the independent report as returned:
verdict, per-criterion matrix `met | unmet | unverified`, findings, evidence pointers, plus its
source reference. Recorded as returned; the driver does not rewrite it.

## ACT record

`pending` — or only what the ending phase determined: outcome, completed work, remaining work
(`unmet`/`unverified`), reasons, limitations and the handoff (next authorized action). No new
verdict, and no `PASS` for a check that did not run.

## Revision history

`none` — append-only: `<time> | r<old> → r<new> | <motive + outgoing attempt identity>`.

## Defect history

`none` — one row per stable defect key: `key | revisions/attempts observed | fixes applied | evidence | last recurrence/escalation`.

## Changed files

`none` — task-owned artefacts only: `path → what changed`, or pointers. Not the whole dirty tree.

## Git state

`status path: <path> — created|modified this cycle · tracked|untracked (durable on disk, not
committed)` — plus the same-cycle touched-file ledger with any task change pending commit, never
claimed as indexed; no automatic add, stage or commit.

## Progress log

append-only, one row per event, never edited retroactively:

`<UTC time> | <phase> | revision r | attempt n | <event> | <evidence pointer>`
````

A phase that has not happened stays `pending`/`not reached` with its reason: a `PLAN → ACT` outcome
fabricates no ready plan, criteria, approval or CHECK, a `DO → ACT` outcome records `CHECK: not run`,
and no `PASS` is ever written for a check that did not run.

1. **Creation** — as PLAN finishes, before the start signal. Initialize the file as the skeleton and
   record the PLAN as returned. The file is created as soon as there is something to record, so it
   does not depend on a ready plan: a PLAN-terminal outcome is recorded there too. `awaiting user
   approval` is logged only when PLAN produced a complete criteria set, so that an approval is
   actually required (normal mode); a `PLAN → ACT` outcome records its resolution instead, and
   autonomous mode has no plan-approval wait at all.
2. **Progress** — every event of DO and CHECK, and each replan.
3. **Replan** (`CHECK → PLAN`) — the file records the genuine revised contract and the resulting
   counters per §State machine and counters; an unchanged plan is not a revision. The outgoing attempt
   is recorded first, then `Replanned: <reason> (r <old>→<new>)`, in the same file.
4. **Finalization** — in ACT, per the closing order.

**Progress log** — append-only, one row per event, never edited retroactively, in exactly the row
format shown in the skeleton above (§Progress log); earlier rows are never rewritten. The time is the
recording time from a real tool or environment clock; where no clock record exists,
mark it unknown. Recording time is not occurrence time: never invent or reorder a timestamp and never
reconstruct unsupported phase history. Log at least: plan ready when a plan was produced, approval
events only in normal mode, `DO started` only when DO actually started; phase transitions and
loop-backs with their cause; unit state changes and closures with the exit status and log path of the
run that decided them, where a run did; each CHECK report and verdict; each failure/fix with the
defect key and the applied fix count; replans with the outgoing attempt; unit additions and
replacements; escalation and its outcome; `Recovered after compaction`; `Notice: …` (autonomous); ACT
closed, including a terminal outcome with its cause and residual criteria.

**Inherited forms with a shared log.** A form may supply an explicit cycle-record locator and a
shared-log locator. The inherited per-step template then demotes its headings under the step entry,
and its final `## Progress log` section references the shared log by cycle/step IDs instead of
repeating the events: one chronology, no duplicated event log. The fixed skeleton is the shape of a
cycle record: a form-owned container's explicitly defined outer sections do not replace or reorder
the cycle skeleton nested and demoted inside them, and the standalone bounded cycle needs no
containing frame. The template above is unchanged.

**Durable state** — explicit fields, restored from this file alone:

- **Counters** — `Current cycle N`, `Plan revision r`, `Attempt n`; §State machine and counters is the
  sole source for their definitions and effects. Where a contract names an `rv`, it is the identity of
  the evidence root/path and is restored from that path — not a separate counter field. A restart or a
  session reset preserves the counters and resets no recorded history; a rejected candidate never
  counts as accepted progress.
- **Defect history** — one row per stable defect key (a criterion/failure identity, independent of `r`):
  observed revisions and attempts, applied fix count, evidence pointers, last recurrence and escalation
  outcome. Outgoing attempts are never erased and an unaccepted attempt never becomes progress.

**Content — a brief handoff, not a report.** The skeleton fixes the shape; every obligation lands in
its own section:

- **§Current state** — phase, counters, active units, known blockers; form and specialized skill.
- **§Original task** — the user's task and any user-supplied criteria verbatim, in their language,
  with the source pointer.
- **§PLAN record** — the planner's complete report per revision; constraints, assumptions, declared
  risks and stop conditions, including the bound access and resources the cycle relied on; in normal
  mode the PLAN's effort estimate (recorded, never a cutoff); decisions made and why, accepted
  limitations and deferred work with the signal that revives it.
- **§DO result** — what was done, the candidate and its evidence pointers; the **DO execution units**
  only when the work was split: ID | state | criteria covered | dependency or
  `superseded → replacement` pointer (`../SKILL.md` §DO, execution units); never a verdict.
- **§CHECK record** — only where CHECK actually ran: acceptance criteria with their IDs where the
  criteria were determined, its outcome and the verification methods it chose with the evidence each
  produced (nothing frozen before DO); an absent CHECK is stated as absent, never filled with invented
  results.
- **§ACT record** — the handoff: actual outcome and reasons, completed and unfinished work, remaining
  `unmet`/`unverified` requirements, known issues and constraints, the recovery step and the next
  authorized action — not a future implementation plan and not a mandate for a new session.
- **§Revision history / §Defect history** — append-only, per the fields above.
- **§Changed files** — the **pointers** (`file:line` evidence, approvals, open questions) and the
  task-owned artefacts, without retelling content. `none` is a legitimate value when the task produces
  no file change: no source edit is required for a `PASS`.
- **§Git state** — the ledger below.
- **§Progress log** — the append-only lines above.

**Durable on disk is not Git-tracked.** The default path is a durable record because it persists on
disk and a fresh session reads it back — not because Git tracks it. A written status file may
legitimately end `untracked`; adding, staging or committing it needs an explicit user instruction or a
recorded policy (a contract's explicit commit mode included), never the word "durable" alone. `## Git
state` records the status path, whether it was created or modified in this cycle, its
tracked/untracked state, and whether task changes are pending commit — never claimed as indexed — from
the baseline the cycle supplied at creation (and the same-cycle touched-file ledger at the ACT
handoff), refreshed only for paths the cycle knows it touched; with no baseline, inspect once and
record unknown attribution honestly instead of claiming untracked names. Work outside the task's own
delta stays untouched and unclaimed.

**Approval slots (normal mode only).** The slots exist only when a ready plan exists and an approval
was actually requested; a `PLAN → ACT` outcome has no pending ref, since there is no DO to authorize.
`Pending approval ref` (§Approval record) binds the stable task/`cycle_id`, cycle `N`, plan revision
`r` and the criteria set; the recorded approval stores the approval against that same identity
(approver, time, reason), including a user stop-at-estimate choice, if one was made. A fresh revision
needs a fresh approval ref; a new estimate does not reset an already agreed cutoff. Both slots are
absent in autonomous mode, which is normal, not a gap. `../SKILL.md` §Normal-mode approval is the
source for the protocol.

The file must let a fresh session restore, without the transcript: the current phase, the criteria and
their revision, the actual result and its evidence pointers, the counters and defect history, the
blockers, the remaining work and the next authorized transition. Everything a successor needs lives in
the skeleton's sections; a separate `Next session` section is not part of the shape.
