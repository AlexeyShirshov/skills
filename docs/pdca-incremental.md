# `pdca-incremental`: a campaign in steps, when there is no plan for the whole volume

## 1. The problem: the goal exists, the plan does not

A PDCA cycle assumes the task is known in full: it can be planned, done and checked. `pdca-collection`
assumes something else: the list of tasks already exists, it can be split into groups and run in
parallel. But a large part of real work resembles neither.

The goal is verifiable — "raise coverage to 75%", "halve the allocations", "remove N warnings", "close
a class of defects" — while **the path is unknown**: which files, nodes or classes will produce the
gain only becomes clear after a measurement. Each next step depends on the previous result, so a plan
for the whole volume cannot be written: it would be a set of guesses.

Three naive options and why they fall short:

- **one big cycle.** PLAN is written blind; the contract cannot be verified until the end; a red CHECK
  at the finish costs the whole effort;
- **many cycles by hand.** Each cycle is correct on its own, but the campaign state lives in heads and
  scattered statuses: deferred branches, blockers, protected files and — most importantly — the
  accepted number from which the next step is counted are lost;
- **`pdca-collection`.** Its input is a known list of tasks, and the ALL-barrier requires a real PLAN of
  every task **before** the first DO. For a research chain that means placeholder plans and a fixed DAG
  that does not redistribute itself when a step falls short.

`pdca-incremental` is the answer to that case: **a fixed increment unit, rolling goal selection, a
chain of accepted measurements and one campaign status file**. There is no plan for the whole volume;
there is a plan for the next step and a rule for choosing it. Individual task plans may be ready in
advance ("grilled") — the campaign does not assemble them into a common DAG and is not obliged to
execute them in a pre-declared order.

### 1.1 Decomposition: upfront or along the way

`pdca-collection` is not a synonym for decomposition. A collection assumes that the decomposition
**has already been made**: the list of tasks with independent goals is known, and every task can be
planned before the first DO. An incremental campaign does not cancel decomposition — it moves its
moment: the goal is split into steps **along the way**, and the next step is chosen from the result
of the previous measurement.

These are two planning modes, not "with a collection and without one":

| feature | `pdca-collection` | `pdca-incremental` |
| --- | --- | --- |
| decomposition | input: the list is known before the start | output: a step is chosen after a measurement |
| plan | all tasks at once, ALL-barrier | the current step only |
| unit | a task with its own goal/acceptance | an increment: goal + floor + measurement |
| next step | from the plan | from the result of the previous measurement |
| failure | group-stop, the rest are not executed | a loop-back of the same step, the campaign continues |
| parallelism | an execution mode (one lane is a normal degradation), not an entry condition | no, sequential by nature |

This is not movement at random: every step has a goal, a floor and a credited measurement, and the next
step does not start without the accepted number of the previous one.

For a metric such as coverage, upfront decomposition is unreliable: the set of uncovered branches
changes after every added test, the marginal yield of a cluster is unknown until measured, and the
denominator can move. A plan ten steps ahead would therefore be a set of guesses; it is more honest to
fix the increment unit, the floor and the measurement recipe, and open goals against a fresh gap map.
The historical check of this distinction is in §5.6.

## 2. When to choose

Choose `pdca-incremental` when the goal is a verifiable predicate (a number, a set, a binary feature)
with a **measurement recipe**, and at least one of the following holds:

- the path to the goal is unknown and opens up through measurement;
- the steps are information-dependent: the goal of step N+1 only makes sense after the result of step N;
- the work is long: one cycle will not cover the volume, while parallel lanes would duplicate goals;
- there is a queue of pre-planned tasks serving **one shared goal/metric**, and their order and
  composition depend on the previous measurement: each task becomes a step, not an item of a fixed
  DAG.

| situation | what to use |
| --- | --- |
| the plan for the whole volume is known and it is one task | one cycle: [`pdca-dotnet.md`](pdca-dotnet.md), [`pdca-coder.md`](pdca-coder.md), [`pdca.md`](pdca.md) |
| a list of tasks with **independent goals** is known | [`pdca-collection.md`](pdca-collection.md) — even with one shared footprint or a single lane; parallelism is a schedule property, not an entry condition |
| the list is known, but all tasks serve **one shared goal/metric** and the path is information-dependent | this campaign (a step = a task) |
| the list has independent goals but no per-item acceptance (one common stream) | one campaign/cycle on the shared goal, not a collection |
| there is a goal, there is no plan, the step is determined by measurement | **`pdca-incremental`** |
| the goal is not verifiable | design/`brainstorming` first, not a campaign |

The key feature that separates it from a collection is **not the number of goals and not whether the
list is known**, but the **kind of goal and the path**: independent per-task goals are a batch even
when it runs in one lane or shares a footprint; one shared goal whose path is unknown and
information-dependent is a campaign. A known list by itself does not select a collection, and a
shared footprint does not by itself select a campaign.

Composition does not change that rule: a collection may contain campaign units (§3.2), but a campaign
inside a batch does not make a sequential chain parallel and does not waive the barrier — the choice
between a collection and a campaign is still decided by the goal structure, not by proven parallelism.

## 3. The campaign contract

A campaign does not redefine the base cycle: the state machine, gates, roles, `N`/`r`/`n` counters and
loop-back come from the base. It adds invariants; the eight key ones follow. The composition
consequences (one lane, commit policy, pause as a checkpoint) are covered in §3.2.

1. **The goal and the measurement recipe are fixed at the start** — the predicate, the unit, the
   denominator, the exclusion filters, the threshold and the floor are recorded verbatim. Changing
   the **goal, recipe, threshold or floor** along the way is not a refinement: it is a **new campaign
   with a new baseline**; old revisions and accepted numbers are retained and are never backfilled.
2. **One increment unit for the whole campaign** — "one accepted gain", not a file, a test or a day.
   Inside a step the work is split into clusters, but the step is accepted as a whole.
3. **Increment floor** — the minimum gain that is worth paying for a full cycle. The step target =
   accepted baseline + floor; the floor is a lower bound, not a ceiling.
4. **Baseline chain** — the input of step N+1 is only the last **accepted** number. No accepted
   number — no next step. A revised step that is finally accepted advances the baseline from the last
   accepted one; the rejected candidate stays `not accepted` and its delta is never credited.
5. **One credited measurement per step** — a red result is not re-taken "for luck"; a replacement is
   admissible only on objective invalidity and is archived.
6. **Goals are opened, not planned in advance** — first a fresh gap map, then selection by expected
   yield, taking blockers, the deferred register and protected areas into account.
7. **State moves along** — deferred rows with triggers, blocked arms, tickets, protected areas and
   effort accounting live in one status file and are passed to every step.
8. **One step at a time and an immovable threshold** — parallel increments break the chain; lowering
   the threshold, changing the filter or deleting tests does not close the campaign.

**The campaign status file** is the single source of state: `Goal`, `Recipe`, `Floor`, the step table
(`kind`, `parent`, `baseline → target → accepted → delta`), `Current step`, `Next-step seed`,
`Deferred` with triggers, `Blockers`, `Protected/foreign`, `Tickets`, `Stop verdict`. The step table is
append-only; when the status and the evidence disagree, the evidence wins.

A step is a bounded campaign unit with an observable result and a stop condition — there are no step
"kinds". A shortfall is a **loop-back of the same step identity** (a corrected brief, `r`/`n` per the
base rules), not a second kind of step and not "the next step with the shortfall"; a genuinely distinct
step preserves history, state and accounting. The final whole-goal check is **not** a step: its brief and
its pre-set stop condition are issued at the last step boundary. More in §4.2.

**Stopping** is explicit and records the remainder:

| status | meaning |
| --- | --- |
| `met` | the whole-goal check passed: the predicate is true on the **accepted** state, no carrying claim blocks and the original requirements are verified; the only success |
| `unreachable` | the remainder is proven with numbers for every cluster and redistributed |
| `blocked` | an external blocker: a ticket, the environment, access |
| `stopped` | a verified blocker, security boundary or user stop; the remainder is preserved for continuation |
| `limited` | a carrying-claim block removed by an explicit narrowing of the result inside the original goal |

`met` needs the whole-goal check, combined with the increment's check or run separately: a set of
accepted increments and PASS on every mechanical row does **not** prove the whole goal, and a partial
check does not give `met`. If the **baseline already satisfies the goal**, no fictitious increment is
created: the baseline goes to an independent `pdca-check` against the goal criteria (never a
DO/orchestrator self-accept), and only then is the campaign closed. A red whole-goal check is a planner
loop-back or `blocked`; `unreachable` requires a `pdca-planner` proof of impossibility in numbers,
never an automatic step from a failed check.

### 3.1 Roles, tiers and authority

The campaign's blocks are not anonymous steps: each has an owning role, a tier and authority. The
skill names roles; the host binds them to agents and models through the profile's `agent` block, and
the skill contains no model id. Campaign tiers: **cheap** — execution and facts, **medium** — decisions
and the verdict. **strong** (`pdca-escalate`) is not a campaign role: it is invoked by the step's
own cycle through its own triggers (the overlay included), and the campaign only receives the result.

| block | role | tier | authority | output |
| --- | --- | --- | --- | --- |
| BOOTSTRAP — decision | `pdca-planner` | medium | read-only, no delegation | goal, recipe, unit, floor, target |
| BOOTSTRAP — baseline | `pdca-executor` | cheap | edit/bash on the permitted surface | the exact baseline fraction |
| DISCOVER | `pdca-scout` | cheap | read-only: code, measurement artifacts, git | gap map, ranked seed |
| BRIEF | `pdca-planner` | medium | read-only, no delegation | the six blocks of the brief |
| STEP N | `pdca-orchestrator` | cheap | dispatch-only; in the collection mode the same runner leads the campaign and the step's cycle inline (§3.2); inside — the base roles (pdca-planner/pdca-check — medium, pdca-executor — cheap, escalate — strong by triggers) | step report + evidence |
| ACCEPT | `pdca-check` | medium | read-only + the step's evidence | verdict by rows, the credited number |
| DECIDE | `pdca-planner` | medium | read-only | next seed, redistribution or a stop recommendation |
| ACT/STOP | `pdca-executor` + primary | cheap | pdca-executor: status/docs; primary: only the campaign status file | the closed campaign record |

Rules: the primary does not edit the product (its file is the campaign status file); pdca-planner does
not execute and does not delegate; check does not edit and does not judge from a story; pdca-scout does
not recommend; the orchestrator does not write code; escalate (strong) lives inside a step and only
decides. A missing role is a resource blocker; the flat-primary fallback is marked with `Notice:`.

### 3.2 A campaign as a collection item

A campaign is not only a standalone mode. It can be a **collection item** with the form `campaign`,
and the form is not the same value as the item's contract and overlay — a campaign item has none of
those at item level (`skills/pdca-collection/SKILL.md §Items: form, contract, overlay`). The form is
decided by the collection PLAN (`pdca-planner`); the runner only reads the ready value and does not
classify the task.

**Two execution models.** Both use the same roles; they differ in the route, not in the role set.

| model | route | who holds the state |
| --- | --- | --- |
| standalone | cheap primary → step orchestrator (`pdca-orchestrator`) → the base roles | the primary: the campaign state machine, one delegated step per call |
| collection-lane | collection primary → collection lane driver (`pdca-orchestrator`, `mode=collection-lane`) → the base roles | the same driver: the campaign state machine and the current step's cycle inline, in one lane session |

There is no separate campaign agent and no new `Task` level; the collection primary does not become the
campaign's executor — it keeps the collection status, not the step. A collection gives the campaign
neither parallel steps nor crediting a number without ACCEPT
(`skills/pdca-incremental/SKILL.md §Driver coordination`). The standalone model is unchanged.

**The contract and the overlay belong to the step, not to the campaign.** A campaign item has no
item-level contract or overlay and no "campaign domain". Each step gets them from the step's content —
`.NET/C#` → the `coder+.NET` overlay (`pdca-dotnet`, inheriting `pdca-coder`), other code → `coder`,
otherwise `none` — and they are fixed in the durable record
(the frame/status), not chosen by the runner
(`skills/pdca-incremental/SKILL.md §3. Step execution`). The dispatch policy belongs to the loaded
campaign contract; the runner executes it and does not classify the task.

**The frame is a separate artifact, not a copy in the status.** Campaign preparation lives in a
separate immutable/revisioned **preparation document** —
`.pdca/<collection-id>/items/<item-id>/preparation.md` — and at the barrier the item presents
`preparation_state=ready` and a single authoritative `preparation_ref` of the form `<path>@r<k>`. The
frame has nine items: the goal predicate; the target/floor criteria (concrete values or rules for
deriving them approved before evidence); the step acceptance criteria and the boundary of the credited
measurement; the bounds and the conservative reservation of the surface; dependencies; resources and
proof of non-conflict with the schedule; promotion rules; stop rules and the bootstrap protocol;
schedule-compatibility evidence. The campaign runtime status stores `preparation_ref` as a
**reference**, not as a copy of the frame
(`skills/pdca-incremental/SKILL.md §Campaign status`); renegotiating the goal, the criteria,
the threshold or the stop rules creates a **new** immutable revision, updates the reference and keeps
the previous one. A silent edit and the backfill of already accepted criteria are forbidden.

**Three operations.**

| operation | when | what it creates | what it does not do |
| --- | --- | --- | --- |
| Preparation record | before/at the barrier, on dispatch | the frame, `preparation_state`, `preparation_ref`, the plan, refs, the collection status | does not measure the goal, does not change the product, does not create the runtime status |
| Baseline bootstrap | after the barrier, before the first step DO, by a dedicated `pdca-executor` | baseline evidence by the recipe and the campaign runtime status `Status: running`, referencing `preparation_ref` | is not a step, is not credited, does not change the product, does not copy the frame |
| Change-producing DO | after the baseline and the step's own PLAN | changes to the product/step artifacts | does not start without the step's PLAN |

`campaign_ref`, the pointer to the campaign runtime status, may be absent before the bootstrap and is
mandatory after it. The barrier does not need a baseline, a `running` runtime status, future step plans,
their contracts/overlays or a number of steps; before the barrier no lane is allocated.

**Readiness ≠ completion.** `preparation_state=ready` without a runtime is `barrier-ready`, not
`started`: the unit stays `pending` and never becomes `done` because the frame is ready. `done` is given
only by an accepted `met` with an explicit `disposition=finalized`
(`skills/pdca-collection/references/status.md §Routing campaign outcomes`).

**Pause ≠ final.** `blocked`, `stopped` and `unreachable` with an admissible next target within an
unchanged goal and bounds are a checkpoint: `disposition=paused`, the unit stays `in-progress`, and
`Checkpoint` in the status names the reason, the last accepted number and the resume point. A final
`incomplete` — and the existing collection group-stop it triggers — requires an explicit final
unsuccessful disposition and is not derived from a pause. Resume is explicit; there is no automatic
endless retry; a pause does not reset `N`/`r`/`n`, does not grant attempts beyond the base contract and
does not advance its group's dependent chain, while the other groups continue
(`skills/pdca-incremental/SKILL.md §Stop`).

**Three different fields.** Readiness (`preparation_state`, `plan_state`), the campaign runtime status
(`Status`) and the per-unit `disposition` (`active | paused | finalized`) are different things, and
none of them is a task status. The lane pause is **derived** from the current unit's
`disposition=paused` and is not stored as a separate authoritative lane field; no new task or group
status is introduced (`skills/pdca-collection/references/lane.md §One lane = one group`).

**The step's PLAN and approval.** The brief neither replaces the step's PLAN nor constitutes approval.
In normal mode every actual step passes a full PLAN of its contract+overlay and is approved under the active
contract; the approval is recorded as a durable pending approval ref, and the current unit gets
`disposition=paused`. In autonomous mode the campaign invents no approval the contract does not require.

**Commits.** `Commit policy: none` means no intermediate step commits and does **not** forbid the
collection's outer completion commit: campaign completion and unit finalization are different events.
The external commit/branch lifecycle of the unit belongs to the collection. An explicit no-commit
restriction that conflicts with the mandatory git model is a preflight blocker before lanes are
allocated, not a silent override of the model (`skills/pdca-collection/references/lane.md §Git model`).

**Recursion is forbidden.** A campaign step is only a family cycle: neither "a campaign in a campaign"
nor "a collection inside a campaign" (nor a collection inside a collection). A campaign inside a
collection gets no extra rights — no commits beyond the policy, no bypassing of gates, no parallel
steps (`skills/pdca-incremental/SKILL.md §Campaign invariants`).

## 4. How it works

![The pdca-incremental campaign graph: BOOT → PLAN → STEP → ACC → DEC, the DEC → PLAN loop "next step · baseline = accepted", the step exit "accept · revise · new step" and the DEC → STOP branch](../../skills/pdca-incremental/assets/diagram/incremental-state-dark.svg)

*Diagram: `skills/pdca-incremental/assets/diagram/incremental-state-dark.svg`; the full layout with
roles and tiers is `incremental-contract-dark.svg`. The step exit is the base step boundary —
accept the increment, revise the same step or open a new one; the final whole-goal check is not a
step.*

- **Bootstrap** — `pdca-planner` fixes the goal, the recipe, the unit, the floor and the target;
  `pdca-executor` takes the baseline with the same recipe that will be used to accept steps.
- **Discovery + Brief are one PLAN phase with two owners.** `pdca-scout` supplies facts (a ranked list
  of goals), `pdca-planner` assembles six blocks: goal, current state, hard constraints, scope,
  acceptance, targets. Discovery on its own is not a step's plan: the decision is made by pdca-planner.
  The split exists for authority and artifacts, not for phases.
- **STEP N** is executed by `pdca-orchestrator`, but the campaign's plan declares the step's contract
  and overlay (`.NET` → `pdca-dotnet`, code → `pdca-coder`, otherwise none) and passes them along; the
  driver does not classify the task. In a collection lane the same driver leads the step's cycle inline
  (§3.2). The campaign does not interfere with the step's gates and does not accept the number in place
  of CHECK.
- **ACCEPT** — `pdca-check` renders the verdict and the credited number; the primary appends the row to
  the table and carries the state over.
- **DECIDE** — `pdca-planner` checks the stop condition and chooses the next seed; the primary records
  the status. A floor shortfall is a loop-back inside the step (a new plan revision), not "the next step
  with the shortfall"; exhausting the revisions means escalation or a stop with the remainder recorded.

**ACCEPT and DECIDE are not merged**, unlike DISCOVER + BRIEF: they are CHECK and ACT, not two halves of
one phase. ACCEPT is an independent verdict on evidence plus the credited number; DECIDE is the
campaign's route. Merging them would let the verifier choose the route and would mix "the step was not
accepted" with "the step was accepted but the campaign stopped". Between them the accepted number is
recorded, and the next step is counted from it.

### 4.1 Why the brief has six blocks

Six is **a proven minimum, not a fixed format**: that many blocks survived ten campaign steps without
reopening what was closed and without scope creep. Each block answers its own question and closes its
own type of failure.

| block | question | which failure it prevents |
| --- | --- | --- |
| `GOAL` | what counts as success and where the step sits in the `baseline → target` chain | local optimisation, goal drift |
| `CURRENT STATE` | the exact numbers and composition of the last accepted run | planning from stale or "roughly" numbers |
| `HARD CONSTRAINTS` | thresholds, the permitted surface, protected files, the commit policy (`auto`/`none`; push forbidden) | substituting the threshold, foreign edits, leaving the scope |
| `SCOPE` | projects, selectors, guards, the measurement recipe | a step that does the wrong thing or does not exercise the live DBMS |
| `ACCEPTANCE` | the floor, one credited measurement, the list of failures | self-assessment, re-taking a red result, a forecast presented as "measured" |
| `TARGETS` | seed clusters with `file:line` and an explicit "what is outside the step" | scope creep and reopening what is closed |

**Why not fewer.** Merging `ACCEPTANCE` with `SCOPE` loses the "what counts as a failure" list, which is
the main thing preventing a fitted result. Merging `HARD CONSTRAINTS` with `GOAL` dissolves invariants
into the goal.

**Why not more.** The rest is already set by the skill and the base contract: roles, tiers, evidence
paths, status-file fields, the PLAN → DO → CHECK → ACT order. Duplicating that in the brief is noise.
The plan's details (which tests exactly and in what order) are `pdca-planner`'s work inside the step; if
the brief starts describing them, it turns into a plan and takes the decision away from pdca-planner.

A project overlay may **extend** the blocks (for example, add a security section inside
`HARD CONSTRAINTS`), but not shrink them: this is a lower bound.

**Sizing the last step.** When the remainder is comparable to the floor (≲ 2×floor), the step is planned
for the whole remainder. If it falls short — one revision inside the step or one more step, but the
step's goal stays the remainder, not "the floor because it is easier". The number of steps is not
planned: it follows from the remainder and the actual deltas.

**Economics.** The floor exists because a step has a fixed price: a full run, evidence, review, the
status-file update. An over-large step is bad too: its plan is written blind, and a failure costs more.
A good target is a step that is realistically achieved in one or two plan revisions.

**Autonomous mode.** A cheap primary delegates one step to `pdca-orchestrator` and retells the report;
there is no approval pause between steps until the stop condition fires. If the orchestrator is
unavailable, the flat primary drives the step itself and marks that with a `Notice:` line.

### 4.2 Revise, accept, and the route after a step

**Revise is not "one more attempt" and not a new step.** After the step's CHECK, one planner call at the
boundary decides and, in the same turn, emits either a brief or a STOP. A corrected brief of the **same**
step identity (repair/loop-back) keeps the target, recipe, threshold and floor; the rejected candidate
stays `not accepted` with its red measurement preserved, no increment is credited for bypassing a
failed CHECK, and the number of the step does not grow without acceptance. The step's `r`/`n` follow the
base loop-back rules; an exhausted revision is `pdca-escalate` or `unreachable`, never a fourth attempt
and never a silent move to "the next step with the shortfall".

**A new step is distinct from revising.** History, state and the shared accounting are preserved, every
actual cost and attempt counts, and an unaccepted red step is never converted into extra accepted
progress. The latest step takes the whole remainder when the remainder is small.

**The final whole-goal check is not a step.** After a local step CHECK the planner, in the same turn,
issues the final-check brief with a **pre-set completion condition**; on PASS the campaign owner records
the STOP from that condition without a new planner call, on a non-PASS it is a planner loop-back. The
check is local to the increment's claims and the affected invariants, not a full audit of every
increment; it is combined with the increment's check or run separately (`skills/pdca/references/check.md`
§Local and whole-goal checks).

**The route after a step.** `accepted` → `next`, or STOP when the whole-goal end conditions are met.
`not accepted`, but the goal is still reachable → a revised brief of the same step. `not accepted` and
the goal is proven unreachable → `unreachable` with evidence and a move to the next target (if the
campaign allows independent goals) or `stop`. An external blocker → `blocked`. A step's failure does not
close the remaining steps: there is no group-stop in a campaign, the blast radius is one step, and the
route stays the planner's.

That is also the answer to ten grilled tasks **with one campaign goal** (coverage, performance,
cleanup): each becomes an `increment` step with its own plan, a failure of one opens `repair` only for
it, and at the end a `verify` over the integral tree runs if needed. There is no common ALL-barrier and
no group-stop here. If ten tasks have ten independent goals, that is not one campaign but a collection
(even with one lane or a shared footprint) or ten base cycles.

## 5. A real case: the coverage campaign in nextorm (October 2026)

> The following is a **real run**, not a teaching example: ten autonomous cycles of one task, one metric
> and not a single worktree. It shows how the .NET overlay drives a long series where every next plan
> rests on the previous measurement, and why it was driven as a chain of cycles rather than as a
> collection.

### 5.1 The setup

The user stated the task as follows (quoted from the conversation, abridged):

> "integration tests must use a real DBMS; if a test does not use one, it is a unit test", "move inmemory
> into unit tests", "core tests may be done in integration tests on a single provider, for example
> sqlite", "75% branch coverage by integration tests", "open a ticket in rc4 for every defect", "do not
> ask me — work in autonomous mode".

From that, PLAN assembled a verifiable contract:

- **goal** — bring the branch coverage of a separate integration gate to a hard 75%
  (`MIN_INTEGRATION_BRANCH_COVERAGE`); the threshold may not be lowered;
- **denominator** — the integration run only: `reportgenerator` over cobertura, `NextORM.Core.InMemory*`
  excluded by policy (in-memory is unit tests), which is why literal 38 407 and counted 38 317 differ by
  90 branch points;
- **legality** — every added fact exercises a live DBMS (a containerised provider or a file SQLite);
  core facts use one SQLite context; SQL text without execution does not count as coverage;
- **side output** — every product defect gets a minimal repro and a ticket in the `1.0.9-rc4` milestone;
  a duplicate is commented on rather than created again;
- **mode** — autonomous: no questions and no pauses for plan approval.

Campaign start: **24 828 / 38 281 = 64.8%** branch, the gate red. Finish: **28 926 / 38 317 = 75.49%**
counted (literal 75.48%), the gate green.

### 5.2 How the skill was pulled in

The task was .NET (xunit v3, Testcontainers, `dotnet-coverage`), so the overlay `pdca-dotnet` was chosen
rather than `pdca-coder` or the domain-neutral `pdca`. On top of it the project overlay `nextorm-pdca`
was enabled: registers, the toolchain, the cached-path performance acceptance and plan hygiene. The
overlay does not extend the base contract's gates — it adds project-specific audit detail.

In autonomous mode the cheap primary does not drive the cycle itself: it **delegates one cycle** to the
`pdca-orchestrator` subagent and passes the contract and the overlay, the goal, the state, the constraints, the scope and
the acceptance criteria in the brief. The orchestrator goes through PLAN → DO → CHECK → ACT itself,
writes the status file and returns a compressed report; the primary only starts the next cycle and
retells the result without asking the user. Hence "ten cycles" means ten delegations, not ten manual
runs.

`pdca-collection` was **never invoked** in the campaign: its input is a batch of tasks or a milestone
with independent items, and here there was one task with one numeric metric. The detailed analysis of
the boundary is in §5.6.

### 5.3 How the skill split the task

The key decision: **the decomposition unit is a measurement step, not a file and not a feature**. One
cycle = one coverage gain with its own contract and its own acceptance. Inside a cycle clusters are cut
by subsystem, but the cycle stays indivisible for crediting.

PLAN of every cycle contains:

- **baseline** — the accepted number of the previous cycle (the exact fraction, not "roughly");
- **floor** — the gain floor, +250 counted branches; target = baseline + floor;
- **clusters** — for example, cycle 10 had 14 of them (`SqlBuilder`, `MergeBuilder`, `QueryPreparer`,
  dialects, translators, rendering, correlated queries), each with a public route, a branch estimate and
  a way to close it (a fact plus a live control);
- **contract** — the blocks `REQ-COV`/`REQ-LIVE`/`REQ-QUALITY`/`REQ-BOUNDARY`/`REQ-DOCS`/`REQ-DEFECTS`/`REQ-STATE`
  with explicit negative outcomes: 28 737 instead of 28 738 is a failure; denominator drift is a
  failure; a forecast credited as a measurement is a failure; a second successful run chosen "to make
  the number prettier" is a failure;
- **deferred register** — branches that are currently unreachable, with a reopening trigger (a new
  public handle, a removed blocker, changed instrumentation) rather than "we forgot";
- **evidence plan** — where the logs, counters, hashes and verification records live.

The +250 floor was set as the minimum price of a step: one boundary run with all containers and the
evidence costs several minutes, and a step below ~250 does not repay the overhead. In fact the cycles
delivered from +277 to +897, so the floor never became a ceiling.

Branch estimates in the cluster table are **discounted forecasts**, they are never credited as a
result. In cycle 10, r1 estimated 770 cobertura branches (a ceiling of ~989 counted), but the credit gave
only 28 427 (+398) — below the 28 738 target; so pdca-planner made r2 with five new clusters (~299
cobertura / ~384 counted), and only the r2 measurement closed the gate.

The split also includes a **legal loop-back**: if the gain falls short of the floor, PLAN makes revision
r2 with a new allocation instead of "asking DO to try harder". That happened in cycle 6 (r1 gave +240
against a floor of 250) and in cycle 10 (r1 gave 28 427 against a target of 28 738 — pdca-planner
redistributed five clusters, r2 gave 28 926).

### 5.4 How it was driven

One cycle looks like this:

1. **PLAN r1** — fix the baseline, the floor, the target, the clusters, the rv1 contract, the deferred
   register, the evidence paths;
2. **DO** — `pdca-executor` writes facts cluster by cluster: first a narrow SQLite-only internal run
   (`NEXTORM_SKIP_PROVIDERS=...`), then the containerised providers; the build must be 0 warnings /
   0 errors;
3. **freeze** — after the last test edit the content is frozen (hashes); tests do not change after that;
4. **BOUNDARY** — exactly one credited full run under `dotnet-coverage` plus a `reportgenerator` report
   with `NextORM.Core.InMemory*` excluded;
5. **CHECK** — a separate role checks the contract row by row against evidence, not against the author's
   story; it has a limited scope for gathering additional facts and no right to edit tests;
6. **PASS → ACT** or **loop-back to PLAN** with the exact failed contract row.

The discipline that kept the campaign together:

- **one credited run.** A red result is not re-taken "for luck": cycle 10 r1 (28 427) stayed in the
  history as red, and pdca-planner made r2 instead of repeating the run; flaky boundary attempts are
  archived, only the green one is credited;
- **foreign edits are protected.** Uncommitted `src/**` from a parallel session were recorded by sha256
  at PLAN and verified at CHECK; their coverage was excluded from the credit, and the denominator drift
  (38 281 → 38 317) was explained separately;
- **environment ≠ defect.** ClickHouse `HttpClient` timeouts and a coverage instrumentation race were
  reproduced in isolation, recorded as environmental and not filed as tickets;
- **blocked branches are not pinned.** Paths broken by #303/#304/#307/#308/#309 stayed blocked arms with
  triggers; no test was written that pins wrong behaviour as expected;
- **no commits and no pushes** without an explicit request; `src/**` was not edited.

| cycle | branch counted | delta |
| --- | --- | --- |
| start | 24 828 / 38 281 = 64.8% | — |
| 1 | 25 136 = 65.6% | +308 |
| 2 | 25 413 = 66.3% | +277 |
| 3 | 25 807 = 67.4% | +394 |
| 4 | 26 199 = 68.3% | +392 |
| 5 | 26 543 = 69.2% | +344 |
| 6 | 26 877 = 70.1% | +334 |
| 7 | 27 286 = 71.2% | +296 |
| 8 | 27 668 = 72.2% | +382 |
| 9 | 28 029 = 73.15% | +361 |
| 10 | **28 926 = 75.49%** | **+897** |

Over the campaign: **+4 098 counted branches**, a full run in every cycle with `0 failed` and an
unchanged skip budget (195 skips, 37 reasons), 5 083 tests / 4 888 passed in total. On the side, about
fifty tickets were opened in `1.0.9-rc4` (#252–#280, #290–#293, #295, #296, #298–#300, #303, #304,
#306–#309, #312–#316), including the final batch #312–#316.

### 5.5 How it was accepted

Acceptance is **a measurement on a frozen tree**, not the author's report:

- CHECK verifies every contract row against evidence: the number, the denominator, the InMemory*
  exclusion, the run composition, the skip budget, the build, the guards, the protected files, the
  absence of commits; the `PASS` verdict is rendered by a separate role;
- the credit is taken from `Summary.txt` (`branch %`), the counted model is recomputed by subtracting
  `NextORM.Core.InMemory*` (65/90 points), the denominator is compared with the baseline;
- **the number first, docs after**: the baseline in `AGENTS.md` and in the workflow is updated only after
  the accepted measurement; thresholds and executable logic stay byte-for-byte;
- ACT closes when all mandatory rows are `met`; the status gets the final numbers, the delta, the
  remainder to the goal and the deferred clusters with triggers;
- in cycle 10 acceptance gave **28 926 / 38 317 = 75.49% ≥ 75%**, the remainder to the goal **−188**
  (that is, 188 branches above the line), the line at 81.51%, the gate green; ACT was closed with
  `residual_to_75pct: -188` and a list of what was deliberately left open.

What would have counted as an acceptance failure: 28 737 instead of 28 738, a changed denominator or
exclusion, rounded "75%", a forecast in the "measured" column, choosing the second successful run
instead of the first valid one, updating docs before the measurement.

### 5.6 Why the campaign ran as a chain of cycles, not as a collection

The honest formulation: this was **manual orchestration**: the primary itself started the next cycle
after the previous one closed. `pdca-collection` also supports a **single-group** mode — no worktrees,
branches or merge, on the current branch — so "one goal" alone does not rule out a collection.

This is not "a lack of decomposition": the campaign decomposed the goal, but **along the way** — step by
step, and the next step was chosen from a fresh measurement, not from a list compiled before the first
DO. The historical check of the boundary: between 2026-09-30 and 2026-10-17 nextorm had **14 runs** of
`pdca-collection` on various tasks; **13 were single-lane**, and only `1.0.9-b-5` actually had two
parallel groups, while `rc3-open-3` G1–G4 were sequential retries, not parallelism. At the same time,
criteria from upfront plans systematically turned out to be unattainable or poorly calibrated: `≥1.20×`
speedup (T244), `0 B/query` allocations (T245), `WARM_TIME_TOLERANCE = 1.20` (T297, later corrected to
`≤1.00`). That is the price of decomposition made before a measurement.

| feature | `pdca-collection` | this campaign |
| --- | --- | --- |
| input | a list of tasks / a milestone | one goal, steps opened as measurements arrive |
| dependency | groups are independent | step N+1 starts from the accepted number of step N |
| footprint | does not intersect between groups | one test project, shared fixtures and files |
| git | a worktree per group, `merge --no-ff` | one directory; auto-commit of an accepted step only with explicit permission, push never |
| measurement | its own per lane, common after the merge | one common one on a frozen tree |

What separates them is not "one goal" and not whether the list is known, but the **goal structure and
the path**:

- a collection's input is a known list of tasks with **independent goals** (one lane or a shared
  footprint is a normal schedule, not a disqualifier); the ALL-barrier requires a real PLAN of
  **every** task before the first DO;
- here the list was not known: the goals of the next step were chosen from a fresh map of uncovered
  branches of the previous accepted run — specific files and lines. A plan ten steps ahead would have
  been a placeholder plan, and a fixed DAG does not allow redistributing clusters when a step falls
  short of the floor (cycle 10: r1 gave +398 instead of 709 → replan r2);
- the environment adds constraints: there was no auto-commit (a repository rule), and without commits
  the multi-group mode loses its tips; with one group no worktree or merge is needed, but they bring no
  gain either.

What one collection lane would have given here: a single status file for all ten tasks, explicit
PLAN→DO boundaries for every task and the chain stopping at a terminal `incomplete`. What it would have
cost: planning all increments before the first measurement and revising the schedule at every step —
exactly the work that the next cycle's PLAN does in a chain of cycles. That is why, with one footprint,
incremental was chosen rather than a degenerate single-group collection.

If the list had been known in advance ("close ten named coverage clusters"), it would still not have
made a collection mandatory: a known list is a queue of candidates. With one footprint ten tasks go
as incremental steps (a step = a task) with the same campaign status file when they share one goal; a
collection is for independent goals with auto-commit permitted (for `>=2` groups).
For a research chain "measured → rebuilt the map → chose goals" incremental is cheaper; the price is
that the state lives in one campaign status file rather than in the statuses of ten separate cycles. The
multi-group mode (`collection/1.0.9-b-5/group-*` in this same repository) is for the case where the tasks
are genuinely independent and auto-commit is permitted.

Composition does not cancel this boundary: a campaign can be a collection unit (§3.2) and be led inline
by its lane. This case, however, is an illustration for the article, not a general composition rule:
here the list of steps was not known in advance, and the campaign was driven as a chain of cycles by
hand.

### 5.7 What is worth reproducing here

- **The cycle brief** of six blocks: goal, current state (exact numbers), hard constraints, test scope,
  acceptance criteria, target clusters. That is enough for the next cycle not to reopen what is already
  closed.
- **The gain floor and one credited run.** The floor sets the minimum price of a step, and the rule
  "we do not re-take a red result" protects against fitting the number.
- **Conservative crediting.** Foreign/protected files are excluded, denominator drift is explained,
  environmental failures do not turn into defects.
- **A deferred register with triggers.** An honest "not closed, and here is the condition under which we
  return" is better than a silent scope extension or pinning broken behaviour.

Case sources (the `nextorm` repository, not part of this repository): `.pdca/status/integration-branch-coverage-{1..10}.md`,
`AGENTS.md` (the Coverage section), `.github/workflows/dotnet.yml`, `coverage.integration.settings.xml`,
`tests/coverage/integration-report/Summary.txt`.

## 6. Limitations and false expectations

- **"No plan" does not mean "no design".** The goal predicate and the measurement recipe must be exact
  before the first step; otherwise the campaign will measure the wrong thing.
- **The floor is a project policy, not a universal constant.** It depends on the price of a step (the
  run, evidence, review) and is set once; a silent lowering of the floor is a way to imitate progress.
- **One step at a time is slower in wall-clock terms.** That is the price of comparability: parallel
  increments start from one gap map and duplicate goals.
- **A campaign does not replace the cycle or the collection.** Inside a step the full base contract
  applies. A collection remains for tasks with independent goals; a known but sequential list serving
  one shared goal is not a reason to choose a collection.
- **Red does not become green.** A measurement may be replaced only on objective invalidity; "re-taken
  because the number is ugly" is falsification.
- **A stop is not success.** `blocked` and `stopped` preserve the remainder and the continuation point;
  `met` is the only status that closes the campaign. In a composition that is a checkpoint with
  `disposition=paused`, not a final `incomplete`.
- **Readiness is not completion.** `preparation_state=ready` without a runtime is barrier-ready, not
  `started`: the unit stays `pending` and does not become `done`.
- **Composition grants no rights and is not recursive.** A campaign inside a collection obeys the same
  commit policy and the same gates; a campaign step is only a family cycle, and "a campaign in a
  campaign" or "a collection inside a campaign" is forbidden.
- **Deferred is not forgotten.** A row without a reopening trigger is a lost row; it must either close or
  have a return condition.

## 7. Where to go next

- The full contract — [`skills/pdca-incremental/SKILL.md`](../skills/pdca-incremental/SKILL.md); the
  campaign diagram — `skills/pdca-incremental/assets/diagram/`.
- The cycle base — [`pdca.md`](pdca.md); the engineering overlays —
  [`pdca-coder.md`](pdca-coder.md) and [`pdca-dotnet.md`](pdca-dotnet.md).
- Batch work with independent goals — [`pdca-collection.md`](pdca-collection.md) (parallelism is a
  schedule property, not an entry condition).
- An overview of the family — [`pdca-guide.md`](pdca-guide.md).

## Sources

The "claim → source" map. Where they disagree, the contracts take precedence:
`skills/pdca-incremental/SKILL.md` for the campaign, `skills/pdca-collection/SKILL.md` (with its
`references/`) for collection items and `skills/pdca/SKILL.md` (with its `references/`) for the base.

| Claim in the article | Source |
| --- | --- |
| A form contract of the family, "not an overlay and not a second cycle"; load order over the base and the declared overlay; the campaign owner is `pdca-orchestrator` in campaign-control | `skills/pdca-incremental/SKILL.md §Form, not a second cycle · §Ownership`; `skills/pdca/SKILL.md §Control modes` |
| Roles, tiers and authority: block → role → tier → access → output; the primary/pdca-planner/pdca-check/pdca-scout/orchestrator/escalate rules | `skills/pdca-incremental/SKILL.md §Driver coordination` |
| When to choose and the distinction from `pdca-collection` (a known list by itself does not select a collection) | `skills/pdca/SKILL.md §Forms`; `skills/pdca-incremental/SKILL.md §Form, not a second cycle` |
| Campaign invariants: goal/recipe, unit, floor, baseline chain, one measurement, discovery, state transfer, seriality | `skills/pdca-incremental/SKILL.md §Campaign invariants` |
| Campaign status: the single file, fields, append-only, evidence precedence | `skills/pdca-incremental/SKILL.md §Campaign status`; `skills/pdca-incremental/references/status.md` |
| The cycle: bootstrap, discovery, the six-block brief, the step, acceptance, stop decisions, sizing | `skills/pdca-incremental/SKILL.md §Campaign cycle · §Stop` |
| A step is a bounded campaign unit with no step kinds; a shortfall is a loop-back of the same step; the final whole-goal check is not a step, and the route after a step | `skills/pdca-incremental/SKILL.md §Step boundary`; `skills/pdca-incremental/SKILL.md §Lens: probe, increment and step` |
| Brief: six blocks, why this is the minimum, what each closes and why not fewer/more | `skills/pdca-incremental/SKILL.md §2. Step brief` |
| Floor economics and step size | `skills/pdca-incremental/SKILL.md §Economics and sizing` |
| Red flags and recovery after compaction | `skills/pdca-incremental/SKILL.md §Red flags (self-check) · §Recovery` |
| Autonomous mode and the flat-primary fallback with `Notice:` | `skills/pdca/SKILL.md §Control modes · §Roles and host requirements`; `skills/pdca-incremental/SKILL.md §Driver coordination` |
| Composition: a campaign as a collection item (form ≠ item contract/overlay), two execution models | `skills/pdca-collection/SKILL.md §Items: form, contract, overlay`; `skills/pdca-incremental/SKILL.md §Driver coordination` |
| The frame, `preparation_ref` as a reference (not a copy), the three operations, readiness ≠ completion | `skills/pdca-collection/SKILL.md §P — per-item PLANs, the barrier, clustering`; `skills/pdca-incremental/SKILL.md §0. Bootstrap (once) · §Campaign status` |
| Pause ≠ final, per-item `disposition`, derived lane pause, explicit resume | `skills/pdca-collection/references/status.md §Routing campaign outcomes · §Invariants`; `skills/pdca-collection/references/lane.md §Lane pause`; `skills/pdca-incremental/SKILL.md §Stop` |
| The step's contract and overlay by content; the dispatch policy belongs to the loaded contract | `skills/pdca-incremental/SKILL.md §3. Step execution` |
| `Commit policy: none` and the outer completion commit; a no-commit conflict is a preflight blocker | `skills/pdca-collection/references/lane.md §Git model`; `skills/pdca-incremental/SKILL.md §Campaign invariants` |
| The recursion ban and "composition grants no rights" | `skills/pdca-collection/SKILL.md §Items: form, contract, overlay`; `skills/pdca-incremental/SKILL.md §Campaign invariants` |
| The real nextorm run: 10 steps, 64.8% → 75.49%, +4 098 branches | `.pdca/status/integration-branch-coverage-{1..10}.md` (the `nextorm` repository) |
