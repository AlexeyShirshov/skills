---
name: pdca-incremental
description: "Drives a long-running goal as a chain of small PDCA increments when there is no committed plan for the whole volume (per-task plans may already be grilled) and each next step is chosen after the previous accepted measurement (coverage, perf, cleanup, hardening campaigns, or a queue of pre-planned sequential tasks). Keeps one campaign status mirror, a fixed increment floor, exactly one credited measurement per step, explicit stop conditions and two non-increment step kinds — repair and verify; every increment is a full cycle delegated to pdca-orchestrator. Invoke ONLY when the user explicitly names `pdca-incremental`."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---
# Skill: pdca-incremental

# Incremental campaign

## Role

You drive a **campaign** — a chain of full PDCA cycles that has one verifiable goal but
**no mandatory plan for the whole volume**. A plan exists only for the current step; the
next step is chosen from the result of the previous one. Plans of individual tasks may
already be ready ("grilled") — the campaign does not assemble a common DAG out of them and
is not obliged to execute them in a pre-declared order.

**This is not a rejection of decomposition but a different moment of it.** A collection
makes decomposition an input: the list of tasks and their footprints are known before the
start. Incremental makes it an output: the step *is* the decomposition chosen after the
previous measurement. For a metric with a moving set of uncovered branches the second
order is more honest.

**The selection criterion is the goal, not the shape of the list.** A known batch of tasks
with **independent goals** is `pdca-collection`, even if it runs as one lane or all tasks
share one footprint. One **shared** goal with an unknown, information-dependent path is
this campaign, even if the task list is known in advance. Parallelism is neither a
condition of entry into a collection nor a sign of a campaign.

This is **not a cycle variant** and not a replacement for the base contract. The state
machine, gates, roles, `N`/`r`/`n` counters and loop-back are taken from the base
unchanged. The campaign adds only what the single cycle lacks:

- **the increment unit** (what counts as one step and when it is accepted);
- **the baseline chain** (step N+1 does not start without the accepted number of step N);
- **the campaign status file** (one file for all steps);
- **stop rules** (the goal is reached / the remainder is provably unreachable / a blocker);
- **two non-incremental step kinds** — `repair` (fixing a non-accepted step) and
  `verify` (an integrated gate that adds no gain).

One step = one full cycle: PLAN → DO → CHECK → ACT. The step is executed by
`pdca-orchestrator`, but the campaign determines the step's variant: `.NET/C#` →
`pdca-dotnet`, other code → `pdca-coder`, otherwise → `pdca`, and passes it to the driver
as `selected_variant`. The driver does not classify the task and does not choose the
variant itself. The campaign does not substitute the variant.

**A campaign can be a collection unit.** Then its execution form is
`execution_kind=campaign`, and it is led by the collection lane driver
(`pdca-orchestrator`, `mode=collection-lane`), not by the campaign's primary: there is no
separate campaign agent and no new `Task` level appears. Such a campaign stays a campaign —
one step at a time, one credited measurement per step, its own baseline chain and its own
stop rules; the collection gives it neither parallel steps nor credit for a number without
ACCEPT. The standalone model does not change: a cheap primary leads the campaign, and it
delegates the step to the step orchestrator — one call per step.

## Roles, tiers and authority

The campaign blocks are not anonymous steps: each has an owning role, a tier and
authority. The skill names **roles**; the host binds them to agents and models through the
profile's `agent` block, there is not a single model id in the skill. Campaign tiers:
**cheap** — execution and facts, **medium** — decisions and the verdict. **strong**
(`pdca-escalate`) is not a campaign role: it is called by the cycle variant inside a step
by its own triggers, the campaign receives only the result.

| block | role | agent | tier | authority | output |
| --- | --- | --- | --- | --- | --- |
| BOOTSTRAP — decision | PLAN | `pdca-planner` | medium | read-only, no delegation | goal, recipe, unit, floor, target |
| BOOTSTRAP — baseline | DO | `pdca-executor` | cheap | edit/bash only in the allowed surface | the exact baseline fraction |
| DISCOVER | GATHER | `pdca-scout` | cheap | read-only: code, measurement artifacts, git | gap map, ranked seed |
| BRIEF | PLAN | `pdca-planner` | medium | read-only, no delegation | six blocks of the step brief |
| STEP N | RUNNER | `pdca-orchestrator` | cheap | dispatch-only: edit/bash forbidden; in standalone — the step only, in collection mode (`mode=collection-lane`) the same RUNNER leads the campaign and the current cycle inline, without a separate agent and a new `Task` level, under the same tiers and authority; inside — the variant's roles (pdca-planner/pdca-check — medium, pdca-executor — cheap, pdca-escalate — strong by triggers) | step report + evidence |
| ACCEPT | CHECK | `pdca-check` | medium | read-only + the step's evidence artifacts | verdict by rows, the accepted number |
| DECIDE | PLAN | `pdca-planner` | medium | read-only | next seed, redistribution or a stop recommendation |
| ACT/STOP | DO + primary | `pdca-executor` + primary | cheap | the primary sets the semantics of the write; `pdca-executor` performs the physical status write and the git commands | the closed campaign record |

Authority rules:

- **The campaign is led by the primary on the cheap tier** (in collection mode — the
  collection lane driver, §Role). It dispatches the roles and **owns the semantic state**
  of the campaign: which rows/fields/decisions must be written. The physical write of the
  status file and any `bash`/git commands are performed by `pdca-executor` on explicit
  dispatch; the primary does not write files and does not run commands. It does not decide
  on behalf of pdca-planner/pdca-check.
- **The primary does not edit the product and does not commit anything itself.** Its only
  subject is the decision about the content of the campaign status; the write and the
  commit commands belong to `pdca-executor`.
- **pdca-planner neither executes nor delegates.** Its output is a decision, not a diff.
- **check does not edit and does not accept on a story.** The verdict is made on the
  step's evidence.
- **pdca-scout does not recommend.** It brings facts; ranking the goals is pdca-planner's
  job.
- **The orchestrator does not write code.** Inside a step it only routes the roles.
- **`pdca-escalate` only decides and lives inside the step.** Strong, read-only; the
  campaign does not call it — it only receives the result; `pdca-executor` executes the
  decision, the orchestrator holds the route.
- A missing role is a resource blocker; the flat-primary fallback is allowed only by the
  base rules and is marked `Notice:`.

A tier is a property of the role, not of the model: the host may override the binding, but
not the authority.

**Setup.** The role agents are taken from the family (`assets/agents/*.md` of the cycle
variant — `pdca` / `pdca-coder` / `pdca-dotnet`), the `pdca-orchestrator` driver lives in
this skill's `assets/agents/`; it needs allowed nested delegation and dispatch rights on
the cheap primary. The full checklist is `docs/install.md` in the skills repository.

## When to choose

- The goal is verifiable (a number, a set, a binary predicate), but **the path is
  unknown**: which files/nodes will give the gain is visible only after a measurement.
- The steps are **information-dependent**: the choice of the goal of step N+1 relies on
  the result of step N.
- A full plan for the whole volume would be a placeholder plan, and a fixed DAG would
  hinder redistributing the work when a step fell short.
- The work is long: one cycle will not cover the volume, and splitting into "mini-cycles"
  without a common status file and acceptance rules means losing state.
- Or there is a queue of grilled tasks, but they serve **one shared goal/metric**, and the
  order/composition depends on the previous measurement: each task becomes a step. If the
  tasks have **their own independent goals**, this is a batch — `pdca-collection`, even
  when it runs as one lane.

**Do not choose it:**

| situation | what to use |
| --- | --- |
| the plan for the whole volume is known and this is one task | one cycle (`pdca-coder`/`pdca-dotnet`/`pdca`) |
| a known list of tasks with **independent goals** (each with its own goal/acceptance) | `pdca-collection` — even with one footprint/one lane and without a guarantee of parallelism |
| the list is known, but all tasks serve **one shared goal/metric**, and the path is information-dependent | this campaign (a step = a task) |
| an ordinary task without a campaign | the base cycle |
| the goal is not verifiable | first PLAN/`brainstorming`, not a campaign |

**`pdca-collection` is a neighbour, not an alternative.** The collection's input is a known
list of tasks with independent goals and an ALL-barrier: a real PLAN of every task
**before** the first DO. Parallelism is a property of the schedule, not a condition of
entry: if the footprint is one, the host gives one lane (`cap = 1`) or the tasks share a
resource, the collection degrades to one sequential lane as designed, but the contract and
the per-task acceptance stay collection-owned. An incremental campaign is chosen by a
**different** sign: one shared verifiable goal/metric, while the path to it is unknown and
information-dependent — the next step is chosen after the previous measurement. A shared
goal and a shared footprint do not by themselves make a batch a campaign if the tasks have
independent goals; conversely, a known list does not make the project a collection if all
tasks are steps of one metric. If the list is born along the way — this is the campaign.

## Campaign invariants

1. **The goal and the measurement recipe are fixed at the start.** The goal predicate, the
   unit of measurement, the denominator, the exclusion filters and the thresholds are
   written into the status file verbatim. A change of the **goal, recipe, threshold or
   floor** along the way is not a "refinement" but **a new campaign with a new baseline**;
   the old immutable revisions and accepted numbers are kept, backfill is forbidden.
2. **The increment unit is one for the whole campaign.** "One step = one accepted gain"
   (not "one file", "one check" or "one day"). Inside a step the work is split into
   clusters, but the step is accepted as a whole.
3. **The increment floor.** The minimum gain that is worth paying for a full cycle at all
   (measurement, evidence, review). The floor is set at the start; the step target =
   accepted baseline + floor. The floor is a lower bound, not a ceiling.
4. **The baseline chain.** The input of step N+1 is the **accepted** number of step N, not
   a forecast, not an intermediate result and not "about the same". No accepted number —
   no next step.
5. **One credited measurement per step.** Exactly one valid result by the recipe; a failed
   result is not repeated "for luck". A replacement is allowed only for objective
   invalidity (environment, instrumentation), is archived and is not chosen by "where the
   number looks nicer".
6. **Goals are discovered, not planned in advance.** On step N+1 a fresh gap map is
   assembled first (what remains, what became reachable), then goals are selected by
   expected yield taking blockers, the deferred register and protected areas into account.
   A ready list of grilled tasks is a queue of candidates, not a campaign plan: every goal
   still goes through discovery and its own PLAN, and the order may change after an
   accepted measurement.
7. **State carries over.** The deferred register with triggers, blocked arms, open tickets,
   protected/foreign changes and budgets live in the status file and are passed to every
   next step. "We forgot" is not a status.
8. **Conservative accounting.** Foreign and protected changes are excluded from the gain;
   denominator drift is explained separately; a forecast is never written into the
   "measured" column.
9. **The threshold does not move.** A campaign cannot be closed by lowering the threshold,
   changing the filter, deleting checks, widening the skip budget or converting the work
   into units that the recipe does not count.
10. **One step at a time.** Parallel increments break the chain: they start from one gap
    map, duplicate goals and make "step N+1 from the number of step N" inapplicable. A
    campaign always occupies one lane — both standalone and as a collection unit.
11. **Only an accepted step is committed, and only with permission.** Auto-commit is not a
    right of the skill: it is granted by a project overlay or an explicit user request; the
    policy is fixed in the status (`Commit policy: auto | none`). Under `auto`, after a
    step is accepted only its paths are committed (`git add <paths>`, not `-A`), the
    message names the campaign and the step, and the tip is part of the step's evidence.
    `push` — never. Under `none` there are no commits; the baseline chain lives on numbers
    and the frozen tree, not on commits. `none` refers to the campaign's intermediate
    step commits and does not forbid the collection's external outer completion commit;
    campaign completion and unit finalization are different events.
12. **A pause is not final, and composition grants no rights.** `blocked`, `stopped` and
    `unreachable` with an allowed next target within an unchanged goal/bounds is a
    checkpoint: `disposition=paused`, the unit stays `in-progress` and is not closed.
    Only an accepted `met` with an explicit `disposition=finalized` gives the unit `done`.
    A final failure requires an explicit final unsuccessful disposition and is not derived
    from a pause. A campaign inside a collection gains no extra rights: no commits beyond
    the policy, no gate bypass, no parallel steps. A campaign step is only a family cycle;
    recursion (a campaign in a campaign, a collection inside a campaign) is forbidden.

## Campaign status file

The single source of state is **one** campaign status file (in nextorm —
`.pdca/status/<campaign>.md`; otherwise — the project convention), and it stores **runtime
only**: `Status`, the append-only step table, `Current step`, the revision/attempt, the
seed, deferred, blockers, baseline evidence refs, the pause checkpoint, the pending
approval ref, the commit policy and the stop verdict. There is no separate todo. Update it
in the same beat as the event; after compaction the state is restored from it, not from
memory.

The campaign charter (preparation document) is **not copied** here: the status keeps
`preparation_ref` as a reference to the immutable revision of the charter. The write
semantics are set by the primary (standalone) or the collection lane driver; the physical
write is performed by `pdca-executor` on explicit dispatch.

The runtime status is separated from readiness (`preparation_state`/`preparation_ref`):
readiness is not the runtime `Status` and not campaign completion; it is fixed at the
barrier, and the runtime status is created only by the baseline bootstrap. The per-unit
`disposition` (`active` | `paused` | `finalized`) lives in the collection unit record; a
pause is not final but a checkpoint, which is written here. The state levels do not nest:
a campaign step is only a family cycle. Recursion is forbidden: a campaign in a campaign,
a collection inside a campaign. `execution_kind` is a field of the collection unit, not of
the campaign.

Required blocks:

```text
# <campaign>
Status: running | met | unreachable | blocked | stopped
Goal: <verifiable predicate>
Recipe: <unit, denominator, filters, threshold — verbatim>
Allowed surface: <what the campaign may change — a subset of the unit surface>
Floor: <increment floor>   Target: <baseline + floor>
Preparation ref: <preparation_ref@r<k> — a reference only, no charter copy>
Commit policy: none | auto (<who allowed it: overlay / explicit request>)

| step | kind | parent | baseline | target | accepted | delta | verdict | commit | evidence |
| 1    | increment | —  | ...      | ...    | ...      | ...   | met     | <sha or —> | ... |
| 2    | repair    | 1  | ...      | the same | ...    | ...   | met     | <sha or —> | ... |
| 3    | verify    | —  | —        | gate   | pass     | —     | —       | —      | ...      |

Current step: N   Cycle: <id>   Plan revision: rN   Contract: rvN   Attempt: n/3
Baseline evidence: <paths to the captured baseline and the evidence of accepted steps>
Next-step seed: <candidate clusters and why they are next>
Deferred: <row → reason → reopening trigger>
Blockers: <ticket/condition → which goals are closed>
Protected/foreign: <paths/hashes excluded from the credit>
Tickets: <numbers>
Checkpoint: <pause reason, last accepted number, resume point — or —>
Pending approval: <durable ref → cycle N / plan revision r / criteria set — or —>
Stop verdict: <empty while running>
```

`kind` — `increment` (an ordinary step), `repair` (fixing a non-accepted step, `parent` = N)
or `verify` (an integrated gate that adds no gain). `parent` is filled only for `repair`.
`Current step` is a concrete step (`cycle_id`, revision, attempt), not an average over the
campaign.

Status-file rules:

- the step table is **append-only**: accepted rows are not rewritten;
- `Next-step seed` is a hypothesis, not a plan: the next step still goes through its own
  PLAN;
- when the status and the evidence diverge, the evidence wins, and the divergence is
  recorded;
- `Preparation ref` is the only pointer to the charter; the charter itself is not copied
  here, and previous revisions are not rewritten;
- `Commit policy: none` means there are no intermediate step commits and does not forbid
  the collection's external outer completion commit;
- `Checkpoint` is written on a pause and does not rewrite the append-only history; a pause
  does not reset the counters and is not a final outcome.

## Campaign cycle

**The campaign PLAN is one phase with two owners.** `pdca-scout` gathers the facts
(Discovery), `pdca-planner` makes the decision (Brief). They are separated by the artifact
and by authority, but not by phase: in PDCA this is P, not a separate D.

### 0. Bootstrap (once) — pdca-planner + pdca-executor

Owners: `pdca-planner` makes the decisions, `pdca-executor` captures the baseline by
execution and persists the record.

Bootstrap separates **three operations** that do not substitute for each other:

1. **Preparation record** — before/at the collection barrier, on explicit dispatch: the
   preparation document (charter), `preparation_state`, `preparation_ref`, the plan, refs
   and the collection status. This is the preparation write: the goal is not measured, the
   product does not change, no runtime status is created.
2. **Baseline bootstrap** — after the ALL-barrier and before the first step DO, by a
   dedicated `pdca-executor`: the baseline is captured by the recipe, the baseline evidence
   and the campaign runtime status `Status: running` are created, referencing
   `preparation_ref`. `campaign_ref` may be absent before the bootstrap and is mandatory
   after it. The baseline bootstrap is not a step: it does not consume a step and is not
   credited as a gain, it does not change the product and does not copy the charter.
3. **Change-producing DO** — only after the baseline and the step's own PLAN; it is what
   changes the product/the step's artifacts.

The order and the content:

1. Formulate the goal as a predicate and the measurement recipe; check that the threshold
   and the filters are fixed in the repository, not "by eye".
2. Capture the baseline with the same recipe you will use to accept steps. Record the exact
   fraction and the path to the baseline evidence.
3. Define the increment unit and the floor; compute `target = baseline + floor`.
4. Fix the allowed surface of edits (a subset of the unit surface) and the
   protected/foreign areas.
5. Assemble a **short list of candidates** for the first step — not a plan for the whole
   volume.
6. Create the campaign runtime status with a reference to `preparation_ref`.
7. Bootstrap does not take a second lane: the campaign is single-threaded — one step at a
   time, one lane.

If the bootstrap shows that the recipe is inapplicable, the goal is unreachable within the
bounds or the surface is insufficient, this is a return to `pdca-planner` and the active
approval, not a silent backfill of the criteria.

### 1. Discovery (before every step)

Owner: `pdca-scout` (cheap, read-only). It brings facts, but does not rank the decision for
pdca-planner and does not write the brief.

Assemble a fresh gap map from the last accepted number and a ranked list of goals: expected
yield, the public reachability route, blockers, already closed families, deferred rows whose
trigger has fired. The result is the `Next-step seed` in the status. Discovery is not the
step's PLAN: it supplies facts, the cycle's PLAN makes the decision.

### 2. Step brief — pdca-planner

Owner: `pdca-planner` (medium, read-only). Discovery supplies the facts, it assembles the
brief; the primary only passes the finished brief to the orchestrator.

Pass `pdca-orchestrator` exactly six blocks (this is the proven minimum that is enough for
a step not to reopen what is closed):

```text
1. GOAL: the campaign predicate + the step's place in the chain (baseline → target).
2. CURRENT STATE: the exact numbers, the composition of the last accepted measurement,
   the budgets.
3. HARD CONSTRAINTS: thresholds, the allowed surface, protected, the commit policy
   (`Commit policy` from the status: under `auto` — only the accepted step and only its
   paths; `push` is forbidden always), what counts as a valid measurement.
4. SCOPE: what is executed, what verifies it, the mandatory controls, the measurement
   recipe.
5. ACCEPTANCE: the step floor, one credited measurement, what counts as a failure
   (including substituting a forecast for the number and denominator drift).
6. TARGETS: the seed clusters with `file:line`/nodes and estimates; explicitly — what is
   not part of this step.
```

Six is a lower bound, not a format: each block closes its own failure type (goal drift, a
plan built on stale numbers, threshold substitution, the wrong scope, self-assessment,
sprawl). The rest is already given by the base contract; the plan's details are
pdca-planner's decision, not the brief's. A project overlay may extend the blocks, but not
shorten them.

### 3. Step execution

A step goes through the full cycle of its variant: PLAN (revision `r`, contract `rv`) → DO
→ CHECK → ACT. The campaign does not interfere with its gates and does not accept a number
in place of CHECK. If the step falls short of the floor, this is a loop-back **inside the
step** (a new plan revision), not "a next step with a shortfall". A red measurement is
kept. Exhausting revisions and attempts follows the base contract: escalation or a stop
with the recorded remainder, not a silent move to the next step.

**In the collection lane the same driver leads the step cycle.** The same
`pdca-orchestrator` (`mode=collection-lane`) runs the step cycle inline in the lane's own
session — without a separate agent and without an extra `Task` level. Before DO the step
goes through a full PLAN of its variant; the step's `selected_variant` is concrete for this
step and is taken from the durable record (charter/status), not chosen by the runner.

**Normal mode: the step approval is durable, not a chat.** The driver may run the step's
PLAN, but it does not obtain the user's approval and does not start a gated DO.
`pdca-executor` writes the durable pending approval ref bound to the exact
`task`/`cycle_id`, `cycle N`, plan revision `r` and the step's criteria set (`N` alone is
not globally unique), and the driver returns a checkpoint to the parent/cheap primary.
The primary asks the user; on an explicit approval `pdca-executor` records the approval
against the same ref, and resume **first checks the applicability** of the saved plan to
the actual state through the roles (`pdca-scout` — facts, `pdca-planner` — decision): if
the plan is applicable, **the same** step continues without a new PLAN and without a new
step; if the plan is stale, `pdca-planner` makes a real revision by the base rules, and it
needs a **fresh** approval — the old approval does not authorize it. Approval-resume does
not do an unconditional replan and does not create a new step. Until the approval the
campaign is a checkpoint (`Checkpoint` in the status), not `met`/`incomplete`; compaction
is safe because the ref and the record are durable. Autonomous mode does not invent an
external approval: until it is obtained this is a blocker/STOP, not a silent pass.

### 3.1. Step kinds: increment, repair, verify

`increment` — an ordinary step: a new gain from the accepted baseline. Only an **accepted
step** moves the baseline and the campaign number — `increment` or an accepted `repair`,
and exactly once; `verify` does not move the baseline.

`repair` — a new cycle on **the same** target after `increment` was closed `not accepted`
(an internal `incomplete`/STOP; revisions/attempts exhausted or a different approach is
needed). This is not a revision inside the step: revision `r+1` stays in the same cycle and
does not create a row, `repair` creates a new row with `parent = N`. Rules:

- the same target, the same recipe and threshold; a change of the goal/recipe/threshold/
  floor is a new campaign (invariants 1 and 9);
- the old `increment` stays `not accepted` and is not rewritten; the red measurement is
  kept;
- **an accepted `repair` moves the baseline from the last accepted baseline, and only
  once:** the next step starts from the last **accepted** baseline; `repair` adds its
  accepted delta to that baseline, not to the non-accepted number of the original
  increment. The original increment does not get ACCEPT and its delta is not credited; the
  total gain is counted once — by the accepted `repair`;
- `verify` does not move the baseline;
- one `repair` per failed step; a repeated failure is `pdca-escalate` or `unreachable`, not
  a second `repair`;
- a recurrence of the same defect after one fix is `pdca-escalate` before the second fix,
  even if the local CHECK passed.

`verify` — the campaign's integrated gate, the analogue of collection C, but not a separate
contract: it gives no gain, does not move the baseline, in the table `target = gate`,
`accepted = pass/fail`. It runs the full campaign gate (build, tests, coverage, docs —
whatever the definition of done declares) on the current accepted state. Its place is fixed
at bootstrap: the campaign's end or every K steps. A `verify` failure opens `repair` of the
affected goals or `blocked`; lowering the threshold is not allowed. `verify` does not
replace the step's ACCEPT: the step numbers stay the source of truth.

### 4. Acceptance and state carry-over

The verdict owner: `pdca-check` (medium, read-only + the step's evidence); the write
semantics of the status are set by the primary, the physical write is performed by
`pdca-executor`.

1. Take the step's CHECK verdict and the credited measurement by the recipe.
2. Append the row to the step table. **Baseline of step N+1 = the last accepted baseline +
   the delta of the accepted step**; `repair` moves it from the last **accepted** baseline,
   not from the non-accepted increment; `verify` does not change the baseline. Under
   `Commit policy: auto`, after acceptance commit **only the step's paths** (`git add
   <paths>`, not `-A`) and record the tip in the `commit` column; `push` — never. If the
   commit is not allowed or failed, record `no commit` and the reason: the accepted number
   and the baseline do not change because of it (they live in the measurement, not in the
   commit).
3. Carry into the status: new tickets, blocked arms, deferred rows with triggers,
   protected/denominator changes.
4. Write the `Next-step seed` and move to the stop decision.

**ACCEPT and DECIDE do not merge.** ACCEPT is the step's CHECK: an independent verdict on
the evidence and the accepted number. DECIDE is the campaign's ACT: the route (the next
step, redistribution, stop). Merging them means letting the reviewer choose the route and
mixing "the step is not accepted" with "the step is accepted but the campaign is stopped".
Between them the accepted number is fixed, and the next step is counted from it.

**The route after a step (DECIDE).** `accepted` → `next` (a new target) or `verify`, if a
declared checkpoint has arrived. `not accepted` but the goal is still reachable → `repair`
(`parent = N`). `not accepted` and the goal is provably unreachable → `unreachable` with
evidence, then `next` target (if the campaign allows independent goals) or `stop`. An
external blocker → `blocked` with a list of the closed goals. A failed step **never**
closes the remaining steps automatically: there is no group-stop in a campaign, the blast
radius = one step.

### 5. Stop decision

The decision owner: `pdca-planner` (medium); the write semantics in the campaign status are
set by the primary, the physical write is performed by `pdca-executor`.

| condition | status | what to record |
| --- | --- | --- |
| the goal predicate is true on the **accepted** measurement, and all **due** mandatory `verify` runs (final and periodic) passed on the current accepted snapshot | `met` | the final number, the remainder, the evidence |
| the remainder is provably unreachable | `unreachable` | per cluster: why, how it was proven, where it was redistributed |
| an external blocker (ticket, environment, access) | `blocked` | the blocker and which goals it closes |
| a budget/limit/user stop | `stopped` | what is done, what remains, where to continue from |

`met` — the only success. It requires **both** conditions: an accepted measurement that
satisfies the predicate **and** all mandatory `verify` runs due at that moment passing on
the same accepted snapshot; a partial check or a `verify` promised for later does not give
`met`. A `verify` that was not due does not block `met`, but the final `verify` (if
declared) is mandatory. If the **baseline already satisfies the goal** at bootstrap, no
dummy increment is created. If a mandatory `verify` is declared, it runs on that snapshot;
`met` is possible only after the goal is accepted by an independent `pdca-check` against
the goal criteria **and** all due gates/`verify` have passed. Without a mandatory `verify`,
the baseline is accepted by the same independent `pdca-check` against the goal criteria
(not self-accept by DO or the orchestrator), after which `met` is set. A red `verify`
follows the ordinary `repair`/`blocked` route; `unreachable` is set only when
`pdca-planner` has proven unreachability with numbers, not automatically from a red
`verify`. `unreachable` is not "almost made it": the remainder must be proven with numbers
(for example, the goal requires a product change or an unavailable source), not declared
out of fatigue. Under `blocked`/`stopped` the chain does not pretend to be closed: the next
session continues from the last accepted number.

**An explicit disposition instead of automatic closure.** `blocked`, `stopped` and
`unreachable` with an allowed next target within an unchanged goal/bounds is a checkpoint:
`disposition=paused`, the unit stays `in-progress`, and the `Checkpoint` in the status
names the reason, the last accepted number and the resume point. Resume is explicit: the
pause is lifted by an active contract trigger or a user decision, there is no automatic
infinite retry. A final `incomplete` (and the collection group-stop it triggers, where one
exists) requires an explicit final unsuccessful disposition and is not derived from a
pause. A pause does not reset `N`/`r`/`n` and grants no attempts beyond the base contract.

### 6. Sizing the last step

When the remainder to the goal is comparable to the floor (≲ 2×floor), the step is planned
**for the whole remainder**, not for the next floor. If it fell short — either one revision
inside the step or one more step, but the step target stays the remainder, not "the floor,
because it is easier".

## Economics

- The floor exists because a step has a fixed price: a full measurement, evidence, review,
  a status-file update. A step cheaper than that price does not pay off.
- An oversized step is bad too: its PLAN is written blind, and a failure costs more. The
  guideline is a step that can realistically be brought home in one or two plan revisions.
- The number of steps is not planned. It follows from the remainder and the actual deltas;
  "ten steps" is a consequence, not a goal.
- Goal estimates are discounted and never written as a result.
- `repair` and `verify` are steps too and cost a full cycle; that is why `repair` is
  limited to one per failed step, and `verify` is placed at the declared checkpoints, not
  after every step.

## Red flags (self-check)

- I write a forecast or an intermediate result into "measured".
- I repeat a failed measurement to get a nicer number.
- I change the threshold/denominator/filter to "push the campaign through".
- I run two increments in parallel "for speed".
- I start a step without the previous one's accepted number.
- I lose a deferred row or a blocker between steps.
- I pin broken behaviour with a check as expected instead of a ticket.
- I declare `met` on a partial check, not on the credited frozen state.
- I stop without a status and without a remainder.
- I open `repair` without a new plan or with the same approach.
- I do a second `repair` on the same step without `pdca-escalate`.
- I use `verify` as a replacement for the step's ACCEPT.
- After a failed step I close the campaign without working out the route (`repair` / `next` /
  `stop`).
- I run ten grilled tasks as one batch without a per-step ACCEPT.

## Recovery after compaction

1. Read the campaign status file — the step table (`kind`/`parent`) and the last accepted
   baseline.
2. Check that the evidence of the last step is in place; take numbers only from there.
3. If there is no evidence, the step is not accepted: repeat the measurement by the recipe,
   do not restore the number from memory.
4. Continue from the `Next-step seed`; re-assemble discovery if the map may be stale.

## Autonomous mode

**Standalone.** The cheap primary **delegates one step** to the `pdca-orchestrator`
subagent and passes the step brief; the orchestrator runs the whole cycle and returns a
compact report. The primary does not edit files, does not run commands, does not accept a
number in place of CHECK and does not ask the user questions; it **sets the semantics** of
the campaign status update, while the physical write and (under `Commit policy: auto`) the
git commit of the accepted step are performed by `pdca-executor` (the step's paths only;
`push` — never). Then the primary starts the next step and retells the result. Between
steps there is no pause for approval — the campaign cycle continues until a stop condition
fires.

**Collection-lane.** When the campaign is a collection unit, the steps are led by the
collection lane driver (`mode=collection-lane`) inline under the collection schedule: it
runs the step cycle itself and needs no second call per step. The collection primary does
not become the campaign's executor — it drives the collection status, not the step. Pause
and stop here are durable: they are written into the campaign status and into the per-unit
`disposition`, survive a session change and are lifted only by an explicit resume; there is
no automatic catch-up after a pause.

If `pdca-orchestrator` is unavailable (no agent, nested delegation forbidden or nested
delegation) — the flat primary leads the step itself by the base contract, marks it with a
`Notice:` line and records the reason; a host prohibition is not bypassed.

## Relation to the family

| skill | input | form |
| --- | --- | --- |
| `pdca` | one task | the base cycle |
| `pdca-coder` / `pdca-dotnet` | one task, code/.NET | a cycle variant |
| `pdca-collection` | a known list of tasks with **independent goals** (parallelism is a property of the schedule, not a condition of entry) | per-task PLAN, groups/lanes, worktree, merge (one group — without git integration) |
| **`pdca-incremental`** | one goal; a list known or discovered by measurement | a sequential chain of cycles, one status file, steps `increment`/`repair`/`verify` |

The capability preflight, exactly one flat fallback with `Notice:` and a durable reason, the
resource stop when a mandatory role is unavailable and fail closed when the contract is
unavailable are described once in `pdca-collection/SKILL.md` §Fallback and apply to a
campaign in a collection lane without a separate mechanism. Host numbers are not invented:
the configured nested-delegation depth is a configuration fact, not proof that the installed
build passes `primary → driver → escalate → scout`; the installed `pdca-orchestrator` is
compared against the canonical asset and checked against the effective permissions. A
medium/strong primary does not start and does not dispatch a cycle: it makes an explicit
handoff to the cheap primary with the references preserved.

The full text of the base contract is not duplicated: see `pdca/SKILL.md` (and the
`pdca-coder`/`pdca-dotnet` variant). A real case walkthrough is in
`docs/ru/pdca-incremental.md`, §5.
