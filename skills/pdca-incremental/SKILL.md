---
name: pdca-incremental
description: "Incremental campaign contract of the PDCA family: one verifiable goal whose achievement method or volume is unknown, or whose next action depends on knowledge not yet obtained, advanced as a sequence of credited steps. The goal's measurement method is fixed at PLAN and the current state is measured before any work toward the goal. Adds the campaign layer to the base `pdca` common cycle contract; the user may name `pdca-incremental` explicitly."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# pdca-incremental: the incremental campaign

An incremental campaign takes one clear goal to completion as a sequence of verifiable steps. Each
step is **one full cycle** of the base contract — PLAN → DO → CHECK → ACT — with its own result and
acceptance.

## Inheritance: the base contract is the single source of the shared rules

The **common cycle contract** (§Common cycle contract) in `../pdca/SKILL.md` supplies, unchanged and
normative for every step: roles, permissions and tiers; normal/autonomous modes and the approval protocol;
the phase contracts and criteria/acceptance rules, including the mandatory-requirement veto and the
whole-goal CHECK; escalation, evidence, the counters `N`, `r`, `n/3` and the evidence-path contract
revision `rv` (§State machine and counters), the same-defect threshold and the defect history; safety,
effort, recovery, workspace and status bookkeeping.

This file **adds the campaign layer only** and never restates those rules: a local paraphrase is not
an alternative, and on a shared rule the base governs. Read it whenever a shared rule is in question.

**Loading.** The base entry PLAN selects the form and the driver continues here. A direct load — the
user named `pdca-incremental` — loads the base common rules and **skips the entry classification**:
the form is a given constraint, not re-decided, and no new PLAN runs to choose it. Collection
likewise inherits the base common rules for its item cycles and CHECK, while adding its own
batch coordination. A campaign that is a collection item still runs this campaign contract
for its steps, with the collection coordinating the batch.

**Overlay.** When a step's work is code, the overlay its PLAN declares (`../pdca-coder/SKILL.md`, or
`../pdca-dotnet/SKILL.md` inheriting it) applies **for that step only**: domain facts, tools and
required evidence — not a form, not a second cycle or state machine, and never a cancellation of the
base goals, exits or safety. Auxiliary verification code makes that component coding work; it does
not reclassify a non-coding campaign.

**The original task is immutable here too.** Every step's dispatch carries the unchanged original
task, its global requirements and that step's scope and criteria (§Original task, cycle scope and
acceptance in the base). A step's accepted scope is **never** global acceptance: `done` needs the
campaign's final whole-goal CHECK against all original mandatory requirements.

## When to use

Use incremental when the goal is clear but the method or the volume cannot be fully determined in
advance; the method may already be known. Work proceeds in steps: make an improvement, verify it,
assess progress toward the goal and determine the next step.

The goal's **measurement method is chosen at PLAN**, and the campaign opens by computing the current
state with it. A goal no available method can measure is rejected at PLAN; it never becomes a
campaign that improvises a metric.

- A prepared list of steps is a list of **candidates**; each step is planned and verified as it comes
  up. Ready candidate tasks may already exist — discovery reuses them rather than rediscovering the
  whole surface.
- The user's explicit choice of this contract is a constraint: work inside it, do not silently
  re-route. A step that turns out to be an ordinary bounded task does not leave the campaign or change
  the form: it is a step whose PLAN is small, and the campaign continues from its accepted result. A
  genuine strategy change follows §Strategic revision and recovery, not a per-step reclassification.

## Probe, increment and step

- **Probe** — a bounded computation, measurement or action inside a step; it starts no new PLAN and
  owes no per-probe CHECK. It is bounded by the decision it investigates and its observable outcomes,
  not by a minute cap, and waives no approval.
- **Increment** — a completed opening of the chosen part or question: a justified change to the
  result **or** decision-relevant knowledge. Several cheap related probes may produce one increment;
  the whole project is never one step.
- **Step** — a bounded unit with an observable result and a stop condition; its credit is a result
  change or knowledge that affects the next decision.

## Campaign goal and measurement

The goal and its **measurement method** are fixed by `pdca-planner` at entry and returned in the
plan, then written verbatim into the status: the **goal predicate**, the **unit of measurement**, the
**denominator**, the exclusion filters, the thresholds, the increment unit, the floor and the target,
and the known limitations of that method. The goal must be computable by that method, not by a
narrative. A goal that requires a value but has no available method — no metric, no instrument or
data source, or no comparable basis — is rejected at PLAN
(`goal cannot be measured under the available means`) and never enters the campaign.

**The recipe is a measurement specification, not a frozen procedure.** It defines what the result
means and on what basis two values are comparable: metric and unit, denominator, inclusion/exclusion
filters, threshold and floor, the accepted baseline, and the comparability conditions under which a
delta is credited. Its metric and basis are PLAN's; the capture instrument is DO's and its
comparability is CHECK's. It is **not** a PLAN-side execution or verification method: CHECK chooses
how to collect and test the evidence, and where its method differs it establishes comparability with
the accepted baseline **before** credit — otherwise no delta is credited until a valid baseline exists.
PLAN may clarify the metric's meaning or the criteria and never binds its own procedure; a method the
user prescribed stays binding.

- **A change of the goal, recipe, threshold or floor is not a refinement**: it is a **new campaign
  with a new baseline**. Old revisions and accepted results are kept; backfill is forbidden.
- **Threshold provenance.** A numeric threshold without a measured baseline is **provisional**;
  revising it on measurement is a `supersede` record with reason and evidence, not a goal change. A
  threshold backed by a measured baseline or set by the user changes only as a goal change; "red and
  on baseline" is asserted by measurement.
- **Floor and target** — the floor is the smallest **detectable** increment of the metric: a
  **credit threshold, not a work quota**. Any delta at or above it earns credit, and one step may
  deliver a batch far above it — size the work by the goal. An expensive measurement buys more
  steps, never a higher floor. The target is `baseline + floor`, or the next decision for a
  knowledge increment; neither adds an automatic cutoff.
- **Baseline.** The campaign's opening step computes the current state **on a basis comparable under
  the method that will accept steps**: exact value, composition (included and filtered out), the
  capture actually used (command or instrumentation), exit status, clock timestamp, evidence path and
  the frozen identity of the measured surface. Its DO changes no product; its CHECK verifies the
  measurement; its ACT writes the baseline and finalizes the status before any change-producing step.
  When the plan's supplied facts already establish a comparable current value, that value is the
  baseline and the first step is the change. When the supplied facts already prove the goal is met,
  the plan is the terminal outcome `requested result already established` and the task goes straight
  to ACT; a measured current state that satisfies the goal goes to the whole-goal CHECK and closes
  `met` — no dummy implementation step.
- **Accepted basis.** The next step starts from the **accepted** state of the previous one — the
  accepted measurement or knowledge, never a forecast, an intermediate value or "about the same". No
  accepted step, no next step.
- **One credited increment per step.** A repeat without new knowledge earns nothing, and no rule
  demands a second increment after the goal is satisfied and checked.
- **A result is kept, not retried for luck.** One credited measurement per step; a replacement is
  allowed only for objective invalidity (environment, instrumentation), is archived, and is never
  chosen for a prettier number. A red measurement stays red.
- **Conservative accounting.** Foreign and protected changes are excluded from the credit; a forecast
  never enters the accepted column; denominator drift is explained separately.

## Step and counters

**Step** is a campaign field of its own. Each step's cycle has its **actual base counters** — `N`, `r`,
`n/3` — recorded inside that step's cycle record; `rv` is read from the evidence path, as in the base. A
step may consume more than one cycle, and a loop-back keeps the same step identity. Step IDs and base
`N` need not coincide.

`N` remains the base **cycle number** and is never redefined as a step number: it grows only in ACT,
and after ACT a further PLAN is the next authorized cycle, never a reopening of the closed one. `Step`
is a campaign field of its own, never a counter. A rename, a session restart, a method change or a step
change **alone** never resets a budget or the history; a genuine criteria revision updates the counters
solely per the base definitions, and the outgoing values and history are retained.

## Campaign invariants

1. **The chain advances on accepted state** and never on an unverified candidate or an "about the
   same" basis.
2. **One step at a time, one lane, no nesting.** Parallel increments start from one gap map, duplicate
   goals and break "step N+1 from step N". A campaign is never nested in a campaign, a collection never
   in a campaign, and a campaign step is a family cycle — not a collection or another campaign.
3. **Discovery feeds, the planner decides.** A fresh gap map and a ranked seed precede each step; the
   next-step decision stays with `pdca-planner` at the boundary.
4. **State carries over.** Deferred rows with triggers, blocked arms, open tickets, accepted knowledge,
   protected/foreign changes and effort accounting live in the campaign status and pass to every next
   step. "We forgot" is not a status.
5. **A pause is not an outcome and not a terminal status.** `blocked`/`stopped`/`unreachable` with an
   allowed next target inside an unchanged goal and bounds is a checkpoint: the campaign stays open —
   `Status: running` with `disposition: paused` recorded in `## Checkpoint` — and resumes in the same
   file with the same counters only on an explicit resume. It resets no counter, grants no extra
   attempts, is no hidden stop and is never accepted progress.
6. **Commit policy only by explicit authorization.** Auto-commit is not a right of the skill: a
   project overlay or an explicit user request grants it, and the policy is fixed in the status
   (`Commit policy: auto | none`). Under `auto`, after acceptance only the step's paths are committed
   (`git add <paths>`, not `-A`), the message names the campaign and the step, and the tip is part of
   the step's evidence. `push` — never. `none` forbids the campaign's step commits and does not forbid
   a collection's external outer completion commit. Nothing here authorizes committing the status
   file itself.
7. **No change before the accepted baseline.** The current state measured by the chosen method is the
   campaign's opening step; no change-producing step starts until that measurement is accepted. A
   supplied comparable current value takes its place; a missing or invalid measurement blocks instead
   of improvising a number.

## Campaign status

One file is the campaign's source of truth under the base `.pdca/` root:
`.pdca/status/<campaign>.md`; a subdirectory or suffix under `.pdca/status/` is allowed, never a
location outside the workspace root. That one file contains the campaign record **and every step's
cycle records**: no per-step status files, no parallel todo and no second event log. `pdca-executor`
is its only writer, as in the base. Without permitted persistent storage it is a handoff limitation:
never durable, never verified.

**Campaign container.** The file has one fixed section order of its own. The base cycle skeleton is not
reproduced at container level: it is used **only** inside a step's cycle record, demoted.

```text
## Campaign state        # the block below — campaign index, global metrics, actual counters
## Original task         # the task exactly as the user supplied it, verbatim
## Preparation record    # state and reference of the preparation revision
## Baseline record       # the captured baseline and its evidence
## Checkpoint            # the last step boundary and the resume point
## Step records          # one ### Step <id> per step, in order
## Campaign outcome      # empty while running; the finalized ACT outcome
## Progress log          # last: the one shared event log of the whole file
```

A step's record is `### Step <id>`; the base skeleton is demoted under it — its `##` headings become
`####` and a `###` inside them becomes `#####`. The base immutable blocks apply inside that record: the
planner's returned text unchanged (or by accessible reference) in `#### PLAN record`, and the original
task by reference to `## Original task` — that block is the one canonical copy, written verbatim, and a
step's reference preserves the task entire: no summary, no paraphrase, no body translation. The
reference stays valid against the immutable raw source.

**Campaign state** — the container's first section; the fields below are campaign fields, while
counters, acceptance and defect history follow the base:

```text
# <campaign>
Status: running | limited | met | unreachable | blocked | stopped
Form: incremental   Overlay: none | pdca-coder | pdca-dotnet
Goal: <verifiable predicate>
Global acceptance: <original mandatory requirements and user-supplied criteria — unchanged>
Recipe: <the PLAN's metric/unit, denominator, filters, threshold/floor and comparability basis; no measured baseline ⇒ provisional>
Allowed surface: <subset of the unit surface the campaign may change>
Increment unit: <what one credited increment is>
Floor: <increment floor, or — when credit is knowledge>   Target: <baseline + floor | next decision>
Preparation ref: <preparation_ref@r<k> — reference only, no copy>
Commit policy: none | auto (<who allowed it: overlay / explicit request>)
Constraints: <hard constraints, declared risks and stop conditions>
Effort accounting: <PLAN estimate, recorded, never a cutoff; elapsed values observed only>
Baseline evidence: <captured baseline and accepted-step evidence paths>
Evidence root: <the actual `.pdca/<task>/rv<k>/…` locators in use — no separate rv field>
Steps:              <index: step id → accepted basis → credited → verdict → evidence>
Current step: <id>   Phase: <phase>   Cycle: <N>   Plan revision: r<N>   Attempt: n/3
Next-step seed: <candidate clusters and why they are next>
Accepted knowledge: <finding → scope, conditions, evidence, limits → superseded? reason>
Assumptions and unknowns: <…>
Rejected approaches: <approach → why → conditions for reconsideration>
Deferred: <row → reason → reopening trigger>
Blockers: <ticket/condition → which goals are closed>
Protected/foreign: <paths/hashes excluded from the credit>
Decisions: <decision → why; accepted limitations; changed artefacts>
Defect history: <key → observed r/n, fixes, evidence, last recurrence, escalation outcome>
Checkpoint: <last boundary: accepted basis, next-step seed, disposition open|paused, resume point — or —>
Pending approval ref / Approval record: <normal mode only — the base slots, same protocol>
Stop verdict: <empty while running; else outcome, cause, evidence, remaining unmet/unverified, handoff>
```

**Per-step cycle records** use the **base status skeleton** from `../pdca/references/act.md` — the same
fixed headings (`## Current state` … `## Progress log`) — demoted under that step's record as above;
the base skeleton itself is never rewritten here.

`limited` is never a widened or weakened `met`: it exists only under an explicit, new user instruction
that revised the task or the criterion (§Stop), and it reports that revised scope while the remainder
on the original task stays recorded. `Status: running` with `disposition: paused` in `## Checkpoint` is
a paused campaign, not a terminal value: the same file and counters continue, and only an explicit
resume lifts it.

**Progress log.** The file has exactly **one** event log: `## Progress log` as its last section, one
line per event carrying the campaign, step and cycle identity — `N`, `Step`, `r`, `n`. Each step's
demoted `#### Progress log` holds only a pointer to that shared log plus its own cycle and step IDs,
never a second chronology; duplicated events are forbidden. `## Campaign state` and a step's
`#### Current state` always match the latest event recorded for that cycle and for the campaign.

**Field rules** (campaign-specific; the base applies otherwise):

- **The steps index is append-only**: an accepted entry is never rewritten, a revised step stays the
  same identity, and an unaccepted step stays `not accepted` with its red result kept.
- **`basis`** is the accepted state of the previous step; **`credited`** names what earned the
  increment (a rejected candidate is not credited, the knowledge it produced is); **`verdict`** is the
  independent `pdca-check` verdict, not self-assessment and not the campaign's route.
- **`Checkpoint` is written at every step boundary** in the same turn; a pause resets no counter and is
  lifted only by an explicit resume.
- **The status never overrules the evidence**: a divergence is recorded and no number is repaired from
  memory. The knowledge register is an append-only fact history — conclusions may be superseded with a
  reason, nothing is backfilled, and a working result may be revised (result and fact history differ).
- An absent CHECK is stated as absent, never filled with invented results; accepted and incomplete
  outcomes stay visibly distinct.

The three subsections below describe the content of the container's `## Preparation record`,
`## Baseline record` and `## Checkpoint` sections; they are not additional top-level sections.

### Preparation record

Holds the immutable **preparation document**: a revision the status points at, written once per
revision by `pdca-executor` on explicit dispatch. It records: the goal predicate and the **measurement
method returned by PLAN** (metric and unit, denominator, filters, thresholds, comparability conditions,
a baseline-less threshold marked provisional, known limitations) — never a method invented at
preparation; the increment unit and, for a measurable goal, floor and `target = baseline + floor`; the
allowed surface and protected/foreign areas; the **criteria** of the campaign's result and its
definition of done (which whole-goal CHECK closes it) — **not** DO's implementation, commands or a plan
of the whole volume; the first step (the current-state measurement, or the change when the plan's
facts already establish the baseline); the effort accounting and commit policy with who granted it;
`preparation_state` and `preparation_ref`. A change to any of it is a **new revision**, never an edit
in place: the status references the revision it worked from, previous revisions stay, and it is never
copied into the status. The goal is not measured at this point.

### Baseline record

Written by the current-state step's ACT, after its CHECK and before the first change-producing step's
DO, on a basis comparable under the method that will accept steps: the exact current value and the
composition of the measurement; the capture actually used, its exit status and clock timestamp; the
evidence path of the captured value and the frozen identity of its surface; the `preparation_ref@r<k>`
the runtime status is opened against. When the plan's supplied facts already establish a comparable
current value, the record cites that value and its evidence and no measurement step runs; when the
value already satisfies the goal, the same ACT finalizes `met`.

### Checkpoint

At every step boundary the driver composes, before the next step is dispatched: the accepted basis (or
the unchanged basis after a rejected candidate); the current step identity and state; the counters as
the base defines them — a genuine criteria revision updates them only there, and the outgoing values
and history are retained — together with the remaining accounting; the next-step seed and what the
planner decided it opens; the knowledge added since the previous checkpoint with evidence pointers;
the `disposition` (open or paused); and the one-line resume point a new session must act on first.

## Campaign cycle

The campaign's PLAN work has two owners: `pdca-scout` gathers facts (discovery), `pdca-planner`
decides (brief, boundary) — both PLAN, neither a separate DO.

### 0. Bootstrap (once)

Three operations that never substitute for each other:

1. **Preparation record** — on explicit dispatch, before any DO (for a collection item, before or at
   the barrier): the preparation document, its state, reference and refs, carrying the measurement
   method returned by PLAN. The goal is not measured, the product does not change, no runtime status is
   created.
2. **Current-state step** — the campaign's first step, after the barrier: open the runtime status
   (`Status: running`, referencing the preparation record); the step's DO computes the current value by
   the chosen method and changes no product; its CHECK verifies that the measurement is valid,
   comparable and complete; its ACT writes `## Baseline record` and fixes the accepted basis. No
   change-producing step starts before that acceptance. A comparable current value already established
   by the plan's facts replaces the step and is recorded as the baseline with its evidence; a value
   that already satisfies the goal goes to the whole-goal CHECK and ACT `met`.
3. **Change-producing DO** — only after the accepted baseline and the step's own PLAN.

If the measurement cannot produce a comparable value, its CHECK fails: the step is not credited, no
baseline is invented, and the boundary finalizes `blocked` with the proven cause; a method change is a
new campaign (§Campaign goal and measurement), never a silent repair. A recipe shown inapplicable, a
goal unreachable within the bounds or an insufficient surface returns to `pdca-planner` and the active
approval — never a silent restatement of the criteria.

### 1. Discovery (before each step)

`pdca-scout` (cheap, read-only) assembles a fresh gap map from the last accepted basis and a ranked
list of goals — expected yield, reachability route, blockers, already closed families, deferred rows
whose trigger has fired, and any ready candidates. Facts only: it does not rank for the planner's
decision and writes no brief. The result is the next-step seed in the status. Discovery is not the
step's PLAN and does not repeat what an existing candidate list already settles.

### 2. Step brief

The first step's brief comes from the initial PLAN; every later one from the boundary call that
accepted the previous increment. Passed by reference, it carries six blocks — the minimum that keeps a
step from re-opening what is closed:

```text
1. GOAL: the campaign predicate, its limitations, and the step's place in the chain (basis → observable).
2. CURRENT STATE: the exact accepted basis, the composition of the last accepted result or knowledge,
   the remaining accounting — for the current-state step, "no baseline yet" is the basis it computes.
3. HARD CONSTRAINTS: thresholds and their provenance/provisional marks, the allowed surface,
   protected/foreign areas, the commit policy (`auto`: only the accepted step and its paths; `push`
   never), what counts as a valid increment.
4. SCOPE: what is executed, the mandatory controls, the measurement method when the goal is measurable.
5. ACCEPTANCE: the increment unit, the credit rule (result change or decision-relevant knowledge),
   what counts as a failure (a forecast substituted for a number, denominator drift, a dropped row).
6. TARGETS: the seed clusters with `file:line`/nodes and estimates, and explicitly what is not part of
   this step.
```

Six is a lower bound, not a format: the plan's detail stays `pdca-planner`'s decision, and an overlay
may extend the blocks, never shorten them. The step's plan is a full plan of **that step**, not of the
campaign.

### 3. Step execution

The step runs the base cycle — PLAN → DO → CHECK → ACT — inline, with the base phase contracts,
counters, evidence rules and approval. The campaign accepts no result in place of CHECK and
does not interfere with the step's exits. The step's cycle is the base `pdca` form; the declared
overlay applies when the step's work is code, and a step touching no code runs without one. The form is
never re-decided per step, and no overlay opens a second PLAN or status. Every step CHECK dispatch —
first verdict and loop-back — carries the complete inline base CHECK contract; the campaign never
shortens or replaces it.

If the step falls short, the route follows the base phase contracts: an implementation defect is
`CHECK → DO` in the same step identity; a wrong or unachievable contract is `CHECK → PLAN` for a
genuine revision (`r+1`). A DO that **cannot finish** goes straight `DO → ACT`, which finalizes
`blocked`/`incomplete` with cause, evidence and residual requirements: the step is **not credited**,
the campaign is **blocked** with that residual work, and the failure neither reboots the step, nor
erases history, nor earns an increment, nor advances to the next step. A red result is kept.
Exhaustion follows the base counters and escalation — escalation or an ACT-finalized STOP with the
recorded remainder, never a silent move on.

### Step boundary

After the step's CHECK, **one** planner call decides and, in the same turn, emits either the next
brief or a STOP; the driver routes and books, it does not run a second PLAN. The decision procedure
and the planner-call accounting are the planner's, in `../pdca/references/plan.md` §Step boundary —
the campaign layer does not restate them.

Campaign consequences of that decision:

- **An accepted increment** advances the accepted basis and the index entry (§Acceptance and
  carry-over). A rejected candidate is not credited, but the knowledge it produced is.
- **The current-state step** credits the baseline as decision-relevant knowledge — step 1 in the
  index — and the accepted basis after it is the measured (or supplied) value, not progress toward the
  goal. When its CHECK already proves the goal predicate, the boundary issues the whole-goal STOP and
  no implementation step is opened.
- **A revised or rejected step** keeps its step identity: the step number does not grow without
  acceptance, `r`/`n` follow the base loop-back rules, the independent CHECK is never rewritten to
  `met`, and no increment is credited for bypassing a failed CHECK. A failed step never closes the
  rest of the campaign by itself: the blast radius is one step and the route stays the planner's.
- **A new step** preserves history, counters and accounting; every actual cost and attempt counts,
  and an unaccepted red step never becomes accepted progress.

**Whole-goal verification.** A STOP with `met` needs a whole-goal CHECK against **every** original
mandatory requirement — combined with the increment's CHECK when that CHECK already covers them,
separate when the last CHECK was local. A `limited` STOP verifies the scope the user's new explicit
instruction revised and records what stays unmet on the original task; it is never a shortcut to
`met`. After a local CHECK the planner issues the final-check brief and a **pre-set completion
condition in the same boundary call**; a whole-goal PASS permits the designated outcome, otherwise the
result loops back. On PASS the driver routes the pre-approved STOP to **ACT** for `pdca-executor` to
finalize — no new planner call, no independent verdict. A separate final CHECK is not a step and adds
no planner call; `unreachable` still requires the proven remainder.

One campaign-side count stays explicit: a campaign whose current-state step already meets the goal
costs **two calls** — initial PLAN → CHECK → boundary → STOP — the measurement's CHECK serving as the
whole-goal CHECK.

## Acceptance and carry-over

The verdict is `pdca-check`'s; the route is `pdca-planner`'s at the boundary; the write is
`pdca-executor`'s. ACCEPT and the route do not merge: the reviewer does not choose the next step, and
"not accepted" must not blur into "accepted but the campaign stops". The accepted basis is fixed
between them and the next step is counted from it.

After the boundary accepts, append the index entry and advance the basis: the next step starts from
the last accepted basis plus the credited change — knowledge advances it with knowledge, not an
invented number. The current-state step's credit is the baseline itself: knowledge, not a result
change, and the basis it fixes is where the first change starts. Under `Commit policy: auto` commit
only the accepted step's paths and record the tip; if the commit is not allowed or fails, record
`no commit` and the reason — the accepted result lives in the measurement and the evidence, not the
commit. Carry the registers and knowledge into the status and write the next-step seed.

## Claims and veto

The campaign adds **no separate claim, rubric or veto layer**. Acceptance is the base
mandatory-requirement veto: a result cannot be accepted, and `done` cannot be recorded, while any
mandatory requirement or criterion is `unmet`/`unverified` (§CHECK in `../pdca/SKILL.md`), and no score,
margin or rubric compensates. A metric or rubric that is part of the original requirement is a
**criterion** with its evidence, not a parallel taxonomy. A local step acceptance never clears a global
requirement. Independently refuting evidence is CHECK's ordinary judging under the base CHECK
contract (`../pdca/references/check.md`, inlined in full in every dispatch) — no campaign-side or
non-author gate — and `limited` exists only under the Stop rule below.

## Stop

A `met`/`limited` stop is the planner's decision at the boundary, or the pre-set condition of the
final-check brief recorded without a new call. A **DO cannot finish** outcome is not a planner decision
and not a CHECK: `DO → ACT` finalizes it directly.

| condition | status | what is recorded |
|---|---|---|
| the whole-goal CHECK passed: the predicate holds on the **accepted** state and every original mandatory requirement is verified | `met` | the final result, the remainder, the evidence |
| the remainder is provably unreachable | `unreachable` | per cluster: why, how it was proven, where it was redistributed |
| an external blocker (ticket, environment, access) | `blocked` | the blocker and which goals it closes |
| the current step's DO cannot finish under the contract | `blocked` | cause, evidence, residual requirements; no accepted increment, no auto-replan |
| a verified blocker, security boundary or user stop | `stopped` | what is done, what remains, where to continue |
| a **new explicit user instruction** revises the task or criterion, and the result is reported against that revised scope | `limited` | that instruction verbatim, the revised scope, what remains unmet on the original task |

`met` is the only success — the campaign record's `done` — and needs the whole-goal CHECK: accepted
increments and PASS on every mechanical row do **not** prove the whole goal. `limited` is only for a
scope the user explicitly revised through a new instruction, never a weakened goal; no mode may narrow
the task itself, and plan approval is not a revision of the input. The original task and that
instruction both stay recorded verbatim, and nothing on the original task is silently accepted as met.
`unreachable` is proven with numbers (a required product change, an unavailable source), never declared
from fatigue. Every non-`met` row is finalized **in ACT**, not on a separate terminal path. A step's
`PLAN → ACT` terminal outcome stays a cycle close in ACT: a **proven infeasible original task** projects
to `unreachable`; a goal shown unmeasurable after entry — the measurement cannot produce a comparable
value — is `blocked` with that proof and is never silently re-methoded; otherwise `blocked`/`stopped`
as the cause supports, with no new status value. A current-state step whose verified value already
satisfies the predicate closes `met` on that CHECK (§Campaign cycle → 0. Bootstrap); no implementation
step is opened for a goal that is already met. Under `blocked`/`stopped` the chain does not pretend to
be closed: the next session continues from the last accepted basis and the residual work recorded by
ACT, and invariant 5 decides whether the campaign is paused or finally closed.

## Effort accounting and safety

The base §Effort and time policy applies unchanged: **no autonomous cutoff** — estimates, elapsed time,
tokens, cost, revisions, steps and measurement totals are accounting, never a stop condition, and no
legacy or resume budget is revived. Work ends on an accepted whole goal, a verified irreducible blocker
for the **agreed goal**, a security/permission boundary or explicit user cancellation; a failed
candidate or incomplete evidence returns to the step boundary. Normal-mode estimate and stop choice,
per-command timeouts and safety hold as in the base. The **commit policy** (§Campaign invariants, item 6) is
the only campaign-specific permission, and `push` is never part of it.

## Strategic revision and recovery

New facts may require revising the strategy at an explicit safe checkpoint while preserving the goal,
history, result, knowledge, constraints and unfinished work. Silent in-flight switching and resetting
counters or history to bypass limits are forbidden; `pdca-planner` decides, not the cheap driver. A
revision is genuine only when the contract rows, units, dependencies or bounding approach actually
change while the original acceptance criterion is preserved — a rename, a session reset or a rejected
candidate is not one.

The base recovery rules apply. **Campaign-specific:** the checkpoint at every step boundary
(§Checkpoint) is what a new session restores. After a lost controller, restart, timeout or compaction
the driver restores from the status: **accepted steps are never repeated**, `N`/`r`/`n`, the accounting
and the defect history are **not reset**, and work continues from the last checkpoint; an interrupted
dispatch is retried only as the retry rules allow. Session exhaustion is controller loss: a planned
handover to a new session of the same cheap `pdca-orchestrator` restores from the checkpoint — not a
new role and not a second writer. A result whose evidence is missing is re-measured comparably under
the recipe, never restored from memory.

## Economics and sizing

- A step has a fixed price — plan, measurement, evidence, review, status write — and an increment
  cheaper than that does not pay off (the floor formalises this for measurable goals). An oversized
  step is blind-written and a failure costs the whole cycle, so aim for one or two plan revisions.
- The number of steps follows from the remainder and the actual deltas; "ten steps" is a consequence,
  never a goal, and estimates are discounted, never accepted results.
- **The last step takes the whole remainder.** When the remainder is comparable to the floor
  (≲ 2×floor), plan for the remainder, not another floor; falling short is one revision or one more
  step with the same target — never "the floor, because it is easier".

## Red flags (campaign-specific)

The base self-check applies. On any of these — **stop, name the deviation, return to the contract**:

- I wrote a forecast or intermediate value into the accepted column, repeated a failed measurement for
  a nicer number, or moved the threshold, denominator or filter — and confused a provisional threshold
  with a baseline-backed one.
- I started a change-producing step before an accepted baseline, let a DO improvise the metric because
  PLAN returned none, or treated the current-state measurement as a dummy step and skipped its CHECK.
- I started a step without the previous accepted basis, let "about the same" stand for it, or lost a
  deferred row, blocker or accepted finding between steps.
- I ran two increments in parallel, inflated the whole project into one step, or demanded a second
  increment after the goal was satisfied and checked.
- I let the boundary become a second planner call on unchanged content, let the reviewer choose the
  route, or decided the plan, form, overlay or verdict myself.
- I declared `met` on a step-local or partial check or on accepted increments alone, treated STOP as a
  path beside ACT, or skipped CHECK, closed without ACT or recorded `done` without an accepted CHECK.
- I built a full plan or a projected backlog before acting, or demanded an up-front plan for work
  whose shape is unknown; I built a new campaign instead of recording a genuine revision.
- After a `cannot finish` I rebooted the step, retried its measurement for luck, reset the counters or
  the history, or repeated an accepted step after a controller loss.
- I edited outside the allowed surface, committed or pushed outside the explicit commit policy, or
  narrowed the task or a criterion without a new explicit user instruction.

## References

- `../pdca/SKILL.md` — the **common cycle contract** inherited here; the planner reference path is
  derived from that directory, never from this one.
- `../pdca/references/act.md` — the canonical status skeleton the per-step cycle records use.
- `../pdca/references/plan.md` — the planner-only procedure and output contract
  (classification, plan fields, step boundary); the driver passes its exact absolute path and never
  reads or inlines it.
- `../pdca/references/check.md` — the CHECK contract; the driver reads it in full and inlines it in
  every step `pdca-check` dispatch (CHECK cannot read the installed file).
