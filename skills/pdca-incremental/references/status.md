# Campaign status, preparation record and checkpoint

Reference for the campaign's durable state. Load it at bootstrap and whenever the status content is
composed. The base schema (`../pdca/references/act.md` §Status file) stays in force as written —
this file adds only the campaign fields and the records.

## One file, runtime only

- **Path:** `.pdca/status/<campaign>.md` under the base's `.pdca/` root. A subdirectory or a suffix
  inside `.pdca/status/` is allowed; the file never leaves the workspace root.
- **One file for all steps** — there is no per-step status file and no separate todo.
- **One writer:** `pdca-executor`, on explicit dispatch. The campaign owner (cheap
  `pdca-orchestrator` in `campaign-control`) composes the content from the reports and passes it in
  the brief; it does not write files. Normal mode uses the same writer.
- **The preparation document is referenced, never copied.** `Preparation ref` is the only pointer;
  previous revisions are not rewritten.
- **Readiness is not completion.** `preparation_state`/`preparation_ref` are fixed at the barrier,
  before the runtime status exists; the runtime status is created only by the baseline bootstrap and
  says nothing about the goal being met.
- **The per-unit `disposition`** (`active | paused | finalized`) lives in the collection unit record
  when the campaign is a collection item; the pause itself is written here as a checkpoint. The
  state levels do not nest: a campaign step is a family cycle, not a collection and not another
  campaign.

## Template

```text
# <campaign>
Status: running | met | unreachable | blocked | stopped
Goal: <verifiable predicate>
Recipe: <unit, denominator, filters, threshold — verbatim; a threshold without a measured
         baseline is marked provisional>
Allowed surface: <what the campaign may change — a subset of the unit surface>
Increment unit: <what one credited increment is for this campaign>
Floor: <increment floor, or — when credit is knowledge>   Target: <baseline + floor | next decision>
Preparation ref: <preparation_ref@r<k> — a reference only, no charter copy>
Commit policy: none | auto (<who allowed it: overlay / explicit request>)
Effort accounting: <elapsed time/tokens/cost, observed only — never a stop condition; a normal-mode
                    user stop choice, when made, is recorded here and in the approval record>

| step | basis | target | accepted | credited | verdict | commit | evidence |
| ---- | ----- | ------ | -------- | -------- | ------- | ------ | -------- |
| 1    | <accepted basis at the start> | <expected observable> | <accepted result or knowledge ref> | <change or knowledge> | met | <sha or —> | <path> |

Current step: N   Cycle: <id>   Plan revision: rN   Contract: rvN   Attempt: n/3
Baseline evidence: <paths to the captured baseline and to the evidence of accepted steps>
Next-step seed: <candidate clusters and why they are next>
Accepted knowledge: <finding → scope, conditions, evidence, limits → superseded? reason>
Assumptions and unknowns: <…>
Rejected approaches: <approach → why → conditions for reconsideration>
Deferred: <row → reason → reopening trigger>
Blockers: <ticket/condition → which goals are closed>
Protected/foreign: <paths/hashes excluded from the credit>
Tickets: <numbers>
Checkpoint: <last boundary: accepted basis, next-step seed, resume point — or —>
Pending approval ref: <durable ref → task/cycle_id / cycle N / plan revision r / criteria set — or —>
Approval record: <approval against the ref: approver, time, reason, same identity — or —>
Stop verdict: <empty while running>
```

The durable counters sit in the header line above the seed, not in a side file: `Current cycle N`,
`Plan revision r` and `Attempt n` are the base's fields and restore the state on their own. The
`Pending approval ref` / `Approval record` slots exist in normal mode only; absent in autonomous
mode is normal, not a gap.

## Field rules

- **The step table is append-only.** An accepted row is never rewritten; a revised step is the
  **same row** under the same identity (a new attempt value, not a new row); a step that is never
  accepted stays `not accepted` and keeps its red result.
- **`basis`** is the **accepted** state of the previous step — a number for a measurable goal, a
  knowledge reference otherwise. A forecast, an intermediate value or "about the same" is not a
  basis.
- **`target`** is the step's expected observable; for a knowledge increment it reads `knowledge`.
- **`credited`** names what earned the increment: the change of the result, or the knowledge that
  changed the next choice. A rejected candidate is not credited; the knowledge it produced is.
- **`verdict`** is the independent `pdca-check` verdict for the step's claims — not a
  self-assessment and not the campaign's route.
- **`commit`** is filled only under `Commit policy: auto`; `no commit` plus the reason otherwise.
- **`Checkpoint` is written at every step boundary**, in the same turn as the boundary event: the
  accepted basis, the current step, the counters, the remaining accounting, the next-step seed.
- **Divergence between the status and the evidence:** the evidence wins, and the divergence is
  recorded — the number is never repaired by memory.
- **The knowledge register is append-only as a fact history.** Accepted conclusions may be
  superseded with a reason; nothing is backfilled, and a superseded conclusion stays readable.
- **A pause does not reset `N`/`r`/`n`** and is not a final outcome; `Checkpoint` records the resume
  point and the pause reason. The pause is lifted only by an explicit resume.
- **`Commit policy: none`** means no campaign step commits and does not forbid a collection's
  external outer completion commit.
- **The progress log, defect history and lifetime** are the base's: one line per event,
  `<UTC time> | <phase> | revision r | iteration n/3 | <event> | <evidence pointer>`, append-only,
  and the file is finalized and kept.

## Preparation document

The immutable revision the status points at. It is written once per revision by `pdca-executor` on
explicit dispatch and holds:

- the goal predicate and the measurement recipe (unit, denominator, filters, thresholds, with a
  provisional mark on every threshold that has no measured baseline);
- the increment unit, and for a measurable goal the floor and `target = baseline + floor`;
- the allowed surface and the protected/foreign areas;
- the candidate list for the first step — not a plan of the whole volume;
- the carrying claims and the definition of done (which whole-goal check closes the campaign);
- the effort accounting (accounting only, no autonomous cap) and the commit policy with who granted it;
- `preparation_state` and `preparation_ref` (the revision the status will reference).

A change to any of it is a **new revision** of the document, never an edit in place: the status
references the revision it worked from, and the previous revisions stay. The document is never
copied into the status, and the goal is not measured at this point.

## Baseline bootstrap record

Written once, before the first step's DO, by a dedicated `pdca-executor` dispatch, with **the same
recipe that will accept steps**:

- the exact baseline value and the composition of the measurement (what was included, what was
  filtered out);
- the command or instrumentation, its exit status and the timestamp from the clock;
- the evidence path of the captured baseline, and the frozen identity of the surface (tree/hash) the
  baseline belongs to;
- the reference to `preparation_ref@r<k>` the runtime status is opened against.

The baseline is not a step: it consumes no step, earns no credit and changes no product. If it
already satisfies the goal, the campaign closes without a dummy increment (§Stop in `../SKILL.md`).

## Checkpoint

At every step boundary the owner records the checkpoint before the next step is dispatched:

1. the accepted basis after the boundary acceptance, or the unchanged basis after a rejected
   candidate;
2. the current step identity (`cycle_id`, `N`, `r`, `n`) and the step's state;
3. the counters and the remaining accounting — values are carried forward, never recomputed lower;
4. the next-step seed and what the planner decided it opens;
5. the knowledge added since the previous checkpoint, with its evidence pointers;
6. the next resume point in one line: what a new session of the same controller must do first.

The checkpoint is what a new session of the same cheap `pdca-orchestrator` restores after a
controller loss or context exhaustion; accepted steps are not repeated and no counter or accounting is
reset.
