# ACT: closing, status and handoff

Reference for the ACT phase and the durable cycle status file. The transitions, the acceptance rule
and the counters stay in `../SKILL.md` (§State machine and counters, §Phase contracts → ACT,
§Workspace and durable status, §Recovery); this file does not restate them.

## Closing order

ACT closes every cycle and is its only closing path. It records the outcome the ending phase already
determined: it issues no new verdict, no expert waiver and no approval, and it never implements,
tests or changes a product, test or checked artifact.

1. **Durable lesson** — 0–2 transferable conclusions, only where the host already provides durable
   memory writable within the current permissions: reusable beyond this workspace, no natural home in
   the status file, no product effect, no new write permission. A no-op is normal; no repository or
   host-config edit is required or implied by closing.
2. **Status file — finalized by `pdca-executor`**, always: the driver passes the reports of the phases
   that actually ran (PLAN's returns, DO's results, CHECK's verdict) and the executor records the
   outcome, the criteria outcome and the handoff — or, for a non-accepted outcome, the cause, evidence,
   residual `unmet`/`unverified` requirements, counters and defect history, with no `PASS` and no
   `done`.
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
| `PLAN → ACT` | the resolution `acceptance criteria cannot be determined`, the concrete missing information and the reason; no invented criteria, no `PASS`, no CHECK |
| `DO → ACT` | the cause, what was completed, what remains (`unmet`/`unverified`), evidence pointers; no CHECK, no planner detour |
| `CHECK → ACT`, terminal | the incomplete/`STOP` outcome with the remaining criteria, counters and defect history; no `PASS`, no `done` |

The status file states the phase actually reached and names a check that did not happen as absent
instead of reconstructing a history. Accepted and incomplete outcomes stay visibly distinct.

## Status file

Default path `.pdca/status/<task>-<N>.md`: `<task>` a kebab slug, `<N>` the task's cycle number
(`../SKILL.md` §State machine and counters). Written only by `pdca-executor`, in the same turn as the
event.

1. **Creation** — as PLAN finishes, before the start signal. The file is created as soon as there is
   something to record, so it does not depend on a ready plan: a PLAN-terminal outcome is recorded
   there too. `awaiting user approval` is logged only when PLAN produced a complete criteria set, so
   that an approval is actually required (normal mode); a `PLAN → ACT` outcome records its resolution
   instead, and autonomous mode has no plan-approval wait at all.
2. **Progress** — every event of DO and CHECK, and each replan.
3. **Replan** (`CHECK → PLAN`) — the file records the genuine revised contract and the resulting
   counters per §State machine and counters; an unchanged plan is not a revision. The outgoing attempt
   is recorded first, then `Replanned: <reason> (r <old>→<new>)`, in the same file.
4. **Finalization** — in ACT, per the closing order.

**Progress log** — append-only, one line per event, never edited retroactively:

```text
<UTC time> | <phase> | revision r | attempt n | <event> | <evidence pointer>
```

The time is the recording time from a real tool or environment clock; where no clock record exists,
mark it unknown. Recording time is not occurrence time: never invent or reorder a timestamp and never
reconstruct unsupported phase history. Log at least: plan ready when a plan was produced, approval
events only in normal mode, `DO started` only when DO actually started; phase transitions and
loop-backs with their cause; unit state changes and closures with the exit status and log path of the
run that decided them, where a run did; each CHECK report and verdict; each failure/fix with the
defect key and the applied fix count; replans with the outgoing attempt; unit additions and
replacements; escalation and its outcome; `Recovered after compaction`; `Notice: …` (autonomous); ACT
closed, including a terminal outcome with its cause and residual criteria.

**Durable state** — explicit fields, restored from this file alone:

- **Counters** — `Current cycle N`, `Plan revision r`, `Attempt n` (plus `rv` where the base uses it);
  §State machine and counters is the sole source for their definitions and effects. A restart or a
  session reset preserves them and resets no recorded history; a rejected candidate never counts as
  accepted progress.
- **Defect history** — one row per stable defect key (a criterion/failure identity, independent of `r`):
  observed revisions and attempts, applied fix count, evidence pointers, last recurrence and escalation
  outcome. Outgoing attempts are never erased and an unaccepted attempt never becomes progress.

**Content — a brief handoff, not a report:**

- task, cycle goal, and the **current state** actually reached: phase, counters, active units, known
  blockers;
- **acceptance criteria** with their IDs where the criteria were determined; only where CHECK actually
  ran, its outcome and the verification methods it chose with the evidence each produced (nothing
  frozen before DO); an absent CHECK is stated as absent, never filled with invented results;
- **form and specialized skill**; constraints, assumptions, declared risks and stop conditions,
  including the bound access and resources the cycle relied on; in normal mode the PLAN's effort
  estimate (recorded, never a cutoff);
- **DO execution units**, only when the work was split: ID | state | criteria covered | dependency or
  `superseded → replacement` pointer (`../SKILL.md` §DO, execution units);
- decisions made and why; accepted limitations; deferred work with the signal that revives it;
- **pointers** (`file:line` evidence, approvals, open questions) and changed artefacts, without
  retelling content;
- **handoff**: actual outcome and reasons, completed and unfinished work, known issues and constraints,
  the recovery step and the next authorized action — not a future implementation plan and not a
  mandate for a new session;
- **progress log** (above).

**Approval slots (normal mode only).** The slots exist only when a ready plan exists and an approval
was actually requested; a `PLAN → ACT` outcome has no pending ref, since there are no criteria to bind.
`Pending approval ref` binds the stable task/`cycle_id`, cycle `N`, plan revision `r` and the criteria
set; `Approval record` stores the approval against that same identity (approver, time, reason),
including a user stop-at-estimate choice, if one was made. A fresh revision needs a fresh approval ref;
a new estimate does not reset an already agreed cutoff. Both slots are absent in autonomous mode, which
is normal, not a gap. `../SKILL.md` §Normal-mode approval is the source for the protocol.

The file must let a fresh session restore, without the transcript: the current phase, the criteria and
their revision, the actual result and its evidence pointers, the counters and defect history, the
blockers, the remaining work and the next authorized transition.
