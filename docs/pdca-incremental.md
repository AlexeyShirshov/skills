# `pdca-incremental`: a campaign in steps, when there is no plan for the whole volume

## 1. The problem: the goal exists, the plan does not

Some goals are clear before the work starts, but their route is not. "Raise coverage until the
critical modules are protected", "make the import fast enough on real data", "find out which cache
strategy pays off" — the destination is nameable, yet the volume, the method or the next useful action
can only be known after some work has produced knowledge.

Forcing such a goal into one bounded cycle creates a speculative mega-plan: every step is guessed in
advance, the first measurement invalidates half of it, and the rest is defended because it was
written down. The opposite failure is worse: no plan at all, a chain of ad-hoc edits, and "progress"
measured by how busy the session felt.

`pdca-incremental` is the middle road. It keeps **one goal** and advances it as a sequence of
**credited steps**, each a full cycle of the base contract: plan, execute, verify independently,
finish. The next step starts from the previous **accepted** state, not from a forecast.

## 2. When to choose it

Use the incremental form when:

- the goal is clear, but the method or the volume cannot be fully determined in advance;
- the next action depends on knowledge that does not exist yet and cannot be justified now;
- a prepared list of steps exists, but it is a list of **candidates**, not a contract — each is
  planned and verified when it comes up.

Do not use it to avoid planning. A goal whose method and scope are known is a Bounded Execution; a
goal whose volume is large but whose steps are already justified is still bounded. The form exists for
genuine uncertainty, not for discomfort with a plan.

The user's explicit choice of `pdca-incremental` is a **constraint**: work inside it. A step that
turns out to be an ordinary bounded task does not leave the campaign or change the form; it is simply
a step with a small PLAN. A genuine strategy change follows the revision rules, not a per-step
reclassification.

## 3. The contract: inheritance, not a copy

The incremental skill **inherits the base common cycle contract** from `../pdca/SKILL.md`. That
contract supplies, unchanged and normative for every step: roles, permissions and tiers; normal and
autonomous modes plus the approval protocol; the phase contracts and the acceptance rules, including
the mandatory-requirement veto and the whole-goal CHECK; escalation, evidence, the counters `N`, `r`,
`n/3`, the contract revision `rv`, the same-defect threshold and the defect history; safety, effort,
recovery, workspace and status bookkeeping.

This file adds the **campaign layer only**. A local paraphrase is never an alternative: on a shared
rule, the base governs. A direct load of `pdca-incremental` also loads the base rules and skips the
entry classification, because the user already chose the form.

**The original task stays immutable.** Every step's dispatch carries the unchanged original task, its
global requirements, and that step's scope and criteria. A step's accepted scope is never global
acceptance: `done` needs the campaign's final whole-goal CHECK against every original mandatory
requirement.

**The overlay belongs to a step.** When a step's work is code, the overlay its PLAN selects
(`../pdca-coder/SKILL.md`, or `../pdca-dotnet/SKILL.md` inheriting it) applies for that step only. It
adds domain facts, tools and required evidence; it is not a form, not a second cycle and not a
cancellation of the base safety rules. Auxiliary verification code makes that component coding work; it
does not reclassify a non-coding campaign.

## 4. Goal, measurement and baseline

The campaign's goal is fixed at the start and written verbatim into the status. For a measurable goal
it includes the **goal predicate**, the **unit of measurement**, the **denominator**, the exclusion
filters, the thresholds, the increment unit, the floor and the target, and the known limitations of
the recipe. The goal must be verifiable by that recipe, not by a narrative.

**The recipe is a measurement specification, not a frozen procedure.** It defines what the result
means and when two values are comparable: metric and unit, denominator, inclusion/exclusion filters,
threshold and floor, the accepted baseline, and the conditions under which a delta is credited. It is
not a PLAN-side execution or verification method. CHECK chooses how to collect and test evidence; if
its method differs, it establishes comparability with the accepted baseline **before** credit.
Otherwise no delta is credited until a valid baseline exists. A method the user prescribed stays
binding.

- **A change of the goal, recipe, threshold or floor is not a refinement.** It is a new campaign with
  a new baseline. Old revisions and accepted results are kept; backfill is forbidden.
- **Threshold provenance.** A numeric threshold without a measured baseline is **provisional**.
  Revising it on measurement is a `supersede` record with reason and evidence, not a goal change. A
  threshold backed by a measured baseline or set by the user changes only as a goal change. "Red and
  on baseline" is asserted by measurement.
- **Floor and target.** The floor is the smallest increment worth its fixed price; the target is
  `baseline + floor` for a measurable goal, or the next decision for a knowledge increment. Neither
  adds an automatic cutoff.
- **Baseline.** Captured **before the first step's DO**, on a basis comparable under the recipe that
  will accept steps: exact value, composition (included and filtered out), the capture actually used,
  its exit status, clock timestamp, evidence path and the frozen identity of the measured surface. It
  is not a step: no credit and no product change. A baseline that already satisfies the goal goes to
  an independent CHECK, not a dummy increment.
- **Accepted basis.** The next step starts from the accepted state of the previous one — the accepted
  measurement or knowledge, never a forecast, an intermediate value or "about the same". No accepted
  step, no next step.
- **One credited increment per step.** A repeat without new knowledge earns nothing. No rule demands a
  second increment after the goal is satisfied and checked.
- **A result is kept, not retried for luck.** One credited measurement per step. A replacement is
  allowed only for objective invalidity (environment, instrumentation), is archived, and is never
  chosen for a prettier number. A red measurement stays red.
- **Conservative accounting.** Foreign and protected changes are excluded from the credit; a forecast
  never enters the accepted column; denominator drift is explained separately.

## 5. Probe, increment and step

| Term | Meaning |
|---|---|
| **Probe** | A bounded computation, measurement or action inside a step. It starts no new PLAN and owes no per-probe CHECK; it is bounded by the decision it investigates and its observable outcomes, not by a minute cap, and it waives no approval. |
| **Increment** | A completed opening of the chosen part or question: a justified change to the result **or** decision-relevant knowledge. Several cheap related probes may produce one increment. |
| **Step** | A bounded unit with an observable result and a stop condition. Its credit is a result change or knowledge that affects the next decision. |

The whole project is never one step, and a step is never a formality. If a step cannot name what it
will leave behind, what will be credited and when it stops, it is not a step yet.

**Counters.** Each step's cycle has its **actual base counters** — `N`, `r`, `n/3` — recorded inside
that step's cycle record; `rv` is read from the evidence path. A step may consume more than one cycle,
and a loop-back keeps the same step identity. Step IDs and base `N` need not coincide.

`N` remains the base **cycle number**, never a step number: it grows only in ACT, and after ACT a
further PLAN is the next authorized cycle, never a reopening of the closed one. **Step** is a campaign
field of its own, never a counter. A rename, a session restart, a method change or a step change alone
never resets a budget or the history; a genuine criteria revision updates the counters only per the
base definitions, and the outgoing values and history are retained.

## 6. Campaign invariants

1. **The chain advances on accepted state**, never on an unverified candidate or an "about the same"
   basis.
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
6. **Commit policy only by explicit authorization.** Auto-commit is not a right of the skill: a project
   overlay or an explicit user request grants it, and the policy is fixed in the status
   (`Commit policy: auto | none`). Under `auto`, after acceptance only the step's paths are committed
   (`git add <paths>`, not `-A`), the message names the campaign and the step, and the tip is part of
   the step's evidence. `push` — never. `none` forbids the campaign's step commits and does not forbid
   a collection's external outer completion commit. Nothing here authorizes committing the status file
   itself.

## 7. One campaign, one status file

The campaign's source of truth is one file under the base `.pdca/` root:
`.pdca/status/<campaign>.md`. A subdirectory or suffix under `.pdca/status/` is allowed, never a
location outside the workspace root. That one file contains the campaign record **and every step's
cycle records**: no per-step status files, no parallel todo and no second event log.
`pdca-executor` is its only writer, as in the base. Without permitted persistent storage it is a
handoff limitation: never durable, never verified.

The container has one fixed section order of its own:

```text
## Campaign state        # campaign index, global metrics, actual counters
## Original task         # the task exactly as the user supplied it, verbatim
## Preparation record    # state and reference of the preparation revision
## Baseline record       # the captured baseline and its evidence
## Checkpoint            # the last step boundary and the resume point
## Step records          # one ### Step <id> per step, in order
## Campaign outcome      # empty while running; the finalized ACT outcome
## Progress log          # last: the one shared event log of the whole file
```

A step's record is `### Step <id>`. The base cycle skeleton is **demoted** under it: its `##` headings
become `####`, and a `###` inside them becomes `#####`. The base immutable blocks apply inside that
record: the planner's returned text unchanged (or by an accessible reference) in `#### PLAN record`,
and the original task by reference to `## Original task` — that block is the one canonical copy,
written verbatim. A step's reference preserves the task entire: no summary, no paraphrase, no body
translation.

**Campaign state** is the container's first section. It records the campaign status, form and overlay,
goal predicate and global acceptance, recipe, allowed surface, increment unit, floor and target,
preparation ref, commit policy, constraints, effort accounting, baseline evidence, evidence root, the
steps index, current step and counters, next-step seed, accepted knowledge, assumptions, rejected
approaches, deferred rows, blockers, protected/foreign areas, decisions, defect history, checkpoint,
approval slots (normal mode) and the stop verdict. Counters, acceptance and defect history follow the
base; the rest are campaign fields.

**Field rules.**

- **The steps index is append-only.** An accepted entry is never rewritten, a revised step stays the
  same identity, and an unaccepted step stays `not accepted` with its red result kept.
- **`basis`** is the accepted state of the previous step. **`credited`** names what earned the
  increment: a rejected candidate is not credited, but the knowledge it produced is. **`verdict`** is
  the independent `pdca-check` verdict, not self-assessment and not the campaign's route.
- **`Checkpoint` is written at every step boundary** in the same turn. A pause resets no counter and
  is lifted only by an explicit resume.
- **The status never overrules the evidence.** A divergence is recorded and no number is repaired from
  memory. The knowledge register is an append-only fact history: conclusions may be superseded with a
  reason, nothing is backfilled.
- An absent CHECK is stated as absent, never filled with invented results. Accepted and incomplete
  outcomes stay visibly distinct.

**Progress log.** The file has exactly **one** event log: `## Progress log` as its last section, one
line per event carrying the campaign, step and cycle identity — `N`, `Step`, `r`, `n`. Each step's
demoted `#### Progress log` holds only a pointer to that shared log plus its own cycle and step IDs,
never a second chronology. Duplicated events are forbidden. `## Campaign state` and a step's
`#### Current state` always match the latest event recorded for that cycle and for the campaign.

`limited` is never a widened or weakened `met`: it exists only under an explicit, new user instruction
that revised the task or the criterion, and it reports that revised scope while the remainder on the
original task stays recorded. `Status: running` with `disposition: paused` is a paused campaign, not a
terminal value: the same file and counters continue, and only an explicit resume lifts it.

### 7.1. Preparation record

Holds the immutable **preparation document**: a revision the status points at, written once per
revision by `pdca-executor` on explicit dispatch. It records the goal predicate and recipe (metric and
unit, denominator, filters, thresholds, comparability conditions, a baseline-less threshold marked
provisional, known limitations); the increment unit and, for a measurable goal, floor and
`target = baseline + floor`; the allowed surface and protected/foreign areas; the **criteria** of the
campaign's result and its definition of done (which whole-goal CHECK closes it) — not DO's
implementation, commands or a plan of the whole volume; the candidate list for the first step; the
effort accounting and commit policy with who granted it; `preparation_state` and `preparation_ref`.

A change to any of it is a **new revision**, never an edit in place: the status references the revision
it worked from, previous revisions stay, and it is never copied into the status. The goal is not
measured at this point.

### 7.2. Baseline record

Written once, before the first step's DO, by a dedicated `pdca-executor` dispatch, on a basis
comparable under the recipe that will accept steps: the exact baseline and the composition of the
measurement; the capture actually used, its exit status and clock timestamp; the evidence path of the
captured baseline and the frozen identity of its surface; the `preparation_ref@r<k>` the runtime status
is opened against. It is not a step.

### 7.3. Checkpoint

At every step boundary the driver composes, before the next step is dispatched: the accepted basis (or
the unchanged basis after a rejected candidate); the current step identity and state; the counters as
the base defines them — a genuine criteria revision updates them only there, and the outgoing values and
history are retained — together with the remaining accounting; the next-step seed and what the planner
decided it opens; the knowledge added since the previous checkpoint with evidence pointers; the
`disposition` (open or paused); and the one-line resume point a new session must act on first.

## 8. The campaign cycle

The campaign's PLAN work has two owners: `pdca-scout` gathers facts (discovery), `pdca-planner` decides
(brief, boundary). Both are PLAN; neither is a separate DO.

### 8.0. Bootstrap (once)

Three operations that never substitute for each other:

1. **Preparation record** — on explicit dispatch, before any DO (for a collection item, before or at
   the barrier): the preparation document, its state, reference and refs. The goal is not measured,
   the product does not change, and no runtime status is created.
2. **Baseline bootstrap** — after the barrier, before the first step's DO: capture the baseline on a
   basis comparable under the accepting recipe, store its evidence, open the runtime status
   (`Status: running`) referencing the preparation record.
3. **Change-producing DO** — only after the baseline and the step's own PLAN.

If the bootstrap shows the recipe inapplicable, the goal unreachable within the bounds or the surface
insufficient, the question returns to `pdca-planner` and the active approval — never a silent
restatement of the criteria. If the baseline already satisfies the goal, no dummy increment is created:
it goes to an independent CHECK against the goal criteria and the campaign can close.

### 8.1. Discovery (before each step)

`pdca-scout` (cheap, read-only) assembles a fresh gap map from the last accepted basis and a ranked
list of goals: expected yield, reachability route, blockers, already closed families, deferred rows
whose trigger has fired, and any ready candidates. Facts only: it does not rank for the planner's
decision and writes no brief. The result is the next-step seed in the status. Discovery is not the
step's PLAN and does not repeat what an existing candidate list already settles.

### 8.2. Step brief

The first step's brief comes from the initial PLAN; every later one from the boundary call that
accepted the previous increment. Passed by reference, it carries six blocks — the minimum that keeps a
step from re-opening what is closed:

```text
1. GOAL: the campaign predicate, its limitations, and the step's place in the chain (basis → observable).
2. CURRENT STATE: the exact accepted basis, the composition of the last accepted result or knowledge,
   the remaining accounting.
3. HARD CONSTRAINTS: thresholds and their provenance/provisional marks, the allowed surface,
   protected/foreign areas, the commit policy, what counts as a valid increment.
4. SCOPE: what is executed, the mandatory controls, the measurement recipe when the goal is measurable.
5. ACCEPTANCE: the increment unit, the credit rule (result change or decision-relevant knowledge),
   what counts as a failure (a forecast substituted for a number, denominator drift, a dropped row).
6. TARGETS: the seed clusters with `file:line`/nodes and estimates, and explicitly what is not part of
   this step.
```

Six is a lower bound, not a format: the plan's detail stays `pdca-planner`'s decision, and an overlay
may extend the blocks, never shorten them. The step's plan is a full plan of **that step**, not of the
campaign.

### 8.3. Step execution

The step runs the base cycle — PLAN → DO → CHECK → ACT — inline, with the base phase contracts,
counters, evidence rules and approval. The campaign accepts no result in place of CHECK and does not
interfere with the step's exits. The step's cycle is the base form; the selected overlay applies when
the step's work is code, and a step touching no code runs without one. The form is never re-decided per
step, and no overlay opens a second PLAN or status.

If the step falls short, the route follows the base phase contracts: an implementation defect is
`CHECK → DO` in the same step identity; a wrong or unachievable contract is `CHECK → PLAN` for a
genuine revision (`r+1`). A DO that **cannot finish** goes straight `DO → ACT`, which finalizes
`blocked`/`incomplete` with cause, evidence and residual requirements: the step is **not credited**,
the campaign is **blocked** with that residual work, and the failure neither reboots the step, erases
history, earns an increment, nor advances to the next step. A red result is kept. Exhaustion follows
the base counters and escalation — escalation or an ACT-finalized STOP with the recorded remainder,
never a silent move on.

### 8.4. Step boundary

After the step's CHECK, **one** planner call decides and, in the same turn, emits either the next brief
or a STOP. The step boundary (§Step boundary) is the campaign's decision point. The driver routes and
books; it does not run a second PLAN.

- **Accept the increment** — on a positive independent CHECK: a result change **or** decision-relevant
  knowledge, including an accepted negative candidate credited as a knowledge increment. Then the next
  brief, or STOP when the whole-goal end conditions are met.
- **Revise/reject the same step** — a corrected brief of the **same** step identity (repair/loop-back)
  or a justified STOP. The step number does not grow without acceptance; `r`/`n` follow the base
  loop-back rules; the independent CHECK is never rewritten to `met`; no increment is credited for
  bypassing a failed CHECK. A failed step never closes the rest of the campaign by itself: the blast
  radius is one step and the route stays the planner's.
- **A new step** — history, counters and accounting are preserved; every actual cost and attempt
  counts, and an unaccepted red step never becomes accepted progress.

**Whole-goal verification.** A STOP with `met` needs a whole-goal CHECK against **every** original
mandatory requirement — combined with the increment's CHECK when that CHECK already covers them,
separate when the last CHECK was local. A `limited` STOP verifies the scope the user's new explicit
instruction revised and records what stays unmet on the original task; it is never a shortcut to `met`.
After a local CHECK the planner issues the final-check brief and a **pre-set completion condition in
the same boundary call**; a whole-goal PASS permits the designated outcome, otherwise the result loops
back. On PASS the driver routes the pre-approved STOP to **ACT** for `pdca-executor` to finalize — no
new planner call, no independent verdict. A separate final CHECK is not a step and adds no planner
call; `unreachable` still requires the proven remainder.

Planner calls are **accounted**, not capped: the successful path is `1 + number of steps`, plus genuine
revisions, the current step's loop-backs and bounded continuations of the **same pending PLAN**.
Separate DECIDE → brief → STOP turns on unchanged content are a repeated PLAN. A one-step campaign costs
**two calls**: initial PLAN → local CHECK → boundary → final CHECK PASS → STOP.

## 9. Acceptance and carry-over

The verdict is `pdca-check`'s; the route is `pdca-planner`'s at the boundary; the write is
`pdca-executor`'s. ACCEPT and the route do not merge: the reviewer does not choose the next step, and
"not accepted" must not blur into "accepted but the campaign stops". The accepted basis is fixed between
them and the next step is counted from it.

After the boundary accepts, append the index entry and advance the basis: the next step starts from the
last accepted basis plus the credited change — knowledge advances it with knowledge, not an invented
number. Under `Commit policy: auto`, commit only the accepted step's paths and record the tip; if the
commit is not allowed or fails, record `no commit` and the reason — the accepted result lives in the
measurement and the evidence, not the commit. Carry the registers and knowledge into the status and
write the next-step seed.

## 10. Claims and the mandatory-requirement veto

The campaign adds **no separate claim, rubric or veto layer**. Acceptance is the base
mandatory-requirement veto: a result cannot be accepted, and `done` cannot be recorded, while any
mandatory requirement or criterion is `unmet`/`unverified`, and no score, margin or rubric compensates.
A metric or rubric that is part of the original requirement is a **criterion** with its evidence, not a
parallel taxonomy. A local step acceptance never clears a global requirement. Independently refuting
evidence is CHECK's ordinary judging under `../pdca/references/check.md`, and `limited` exists only
under the Stop rule below.

## 11. Stop

A `met`/`limited` stop is the planner's decision at the boundary, or the pre-set condition of the
final-check brief recorded without a new call. A **DO cannot finish** outcome is not a planner decision
and not a CHECK: `DO → ACT` finalizes it directly.

| Condition | Status | What is recorded |
|---|---|---|
| the whole-goal CHECK passed: the predicate holds on the **accepted** state and every original mandatory requirement is verified | `met` | the final result, the remainder, the evidence |
| the remainder is provably unreachable | `unreachable` | per cluster: why, how it was proven, where it was redistributed |
| an external blocker (ticket, environment, access) | `blocked` | the blocker and which goals it closes |
| the current step's DO cannot finish under the contract | `blocked` | cause, evidence, residual requirements; no accepted increment, no auto-replan |
| a verified blocker, security boundary or user stop | `stopped` | what is done, what remains, where to continue |
| a new explicit user instruction revises the task or criterion, and the result is reported against that revised scope | `limited` | that instruction verbatim, the revised scope, what remains unmet on the original task |

`met` is the only success — the campaign record's `done` — and needs the whole-goal CHECK: accepted
increments and PASS on every mechanical row do **not** prove the whole goal. `limited` is only for a
scope the user explicitly revised through a new instruction, never a weakened goal; no mode may narrow
the task itself, and plan approval is not a revision of the input. The original task and that
instruction both stay recorded verbatim, and nothing on the original task is silently accepted as met.
`unreachable` is proven with numbers (a required product change, an unavailable source), never declared
from fatigue.

Every non-`met` row is finalized **in ACT**, not on a separate terminal path. A step's `PLAN → ACT`
terminal outcome stays a cycle close in ACT: a **proven infeasible original task** projects to
`unreachable`, otherwise `blocked`/`stopped` as the cause supports, with no new status value. Under
`blocked`/`stopped` the chain does not pretend to be closed: the next session continues from the last
accepted basis and the residual work recorded by ACT, and invariant 5 decides whether the campaign is
paused or finally closed.

## 12. Effort, safety and recovery

The base effort policy applies unchanged: **no autonomous cutoff**. Estimates, elapsed time, tokens,
cost, revisions, steps and measurement totals are accounting, never a stop condition, and no legacy or
resume budget is revived. Work ends on an accepted whole goal, a verified irreducible blocker for the
agreed goal, a security/permission boundary or explicit user cancellation; a failed candidate or
incomplete evidence returns to the step boundary. Normal-mode estimate and stop choice, per-command
timeouts and safety hold as in the base. The **commit policy** is the only campaign-specific
permission, and `push` is never part of it.

New facts may require revising the strategy at an explicit safe checkpoint while preserving the goal,
history, result, knowledge, constraints and unfinished work. Silent in-flight switching and resetting
counters or history to bypass limits are forbidden; `pdca-planner` decides, not the cheap driver. A
revision is genuine only when the contract rows, units, dependencies or bounding approach actually
change while the original acceptance criterion is preserved — a rename, a session reset or a rejected
candidate is not one.

The base recovery rules apply. **Campaign-specific:** the checkpoint at every step boundary is what a
new session restores. After a lost controller, restart, timeout or compaction the driver restores from
the status: **accepted steps are never repeated**, `N`/`r`/`n`, the accounting and the defect history
are **not reset**, and work continues from the last checkpoint; an interrupted dispatch is retried only
as the retry rules allow. Session exhaustion is controller loss: a planned handover to a new session of
the same cheap driver restores from the checkpoint — not a new role and not a second writer. A result
whose evidence is missing is re-measured comparably under the recipe, never restored from memory.

## 13. Economics and sizing

- A step has a fixed price — plan, measurement, evidence, review, status write — and an increment
  cheaper than that does not pay off (the floor formalises this for measurable goals). An oversized
  step is blind-written and a failure costs the whole cycle, so aim for one or two plan revisions.
- The number of steps follows from the remainder and the actual deltas; "ten steps" is a consequence,
  never a goal, and estimates are discounted, never accepted results.
- **The last step takes the whole remainder.** When the remainder is comparable to the floor
  (≲ 2×floor), plan for the remainder, not another floor; falling short is one revision or one more step
  with the same target — never "the floor, because it is easier".

## 14. A real case: coverage as a campaign

> This is an illustration from practice, not a source of a rule. Names and numbers are illustrative.

A library had a clear goal: protect the critical modules with tests and raise meaningful coverage. The
method was unknown: which modules carried the risk, which tests would pay off, and how much coverage was
enough could only be learned by measuring. A bounded plan would have guessed the whole backlog.

The campaign fixed the predicate ("the critical modules have tests that fail on a real defect"),
the recipe (line and branch coverage per critical module, the configured runner, the reported denominator),
the increment unit (one module or one evident risk family), and the floor (one module protected).
It captured a baseline with the actual runner, then worked in steps: one step measured the gaps and
produced a ranked seed; the next protected the highest-risk module and was accepted on a real red↔green
test; the boundary recorded the new accepted basis and the next seed. A step that found no reachable
gap was accepted as a **knowledge increment** — it changed the next decision — while its red result
stayed red. A later step hit an unavailable fixture; DO could not finish, ACT recorded `blocked`, and
the campaign resumed from the same accepted basis when the fixture was restored. No counter was reset
and no accepted step was repeated.

The campaign ended with `met` only after a whole-goal CHECK confirmed that every original requirement —
not merely the per-step coverage numbers — held.

## 15. Limitations and false expectations

- **"The method is unknown, so no plan is needed."** The step still needs a result contract, criteria
  and a stop condition. Uncertainty lowers detail, not discipline.
- **"A campaign can run steps in parallel."** No. One step at a time, one lane. Parallelism duplicates
  goals and breaks the accepted-basis chain.
- **"A red result can be replaced with a better number."** No. A replacement is allowed only for
  objective invalidity and is archived; a red result stays red.
- **"A pause is a terminal outcome."** No. A pause is a checkpoint with `disposition: paused` in the
  same open campaign; only an explicit resume lifts it.
- **"A local PASS is the campaign's success."** No. `met` needs the whole-goal CHECK against every
  original mandatory requirement.
- **"The status file can be committed because it is durable."** No. Durable on disk is not tracked;
  committing needs an explicit instruction or a recorded policy.

## 16. Where to go next

- The base cycle and its common contract: [`pdca.md`](pdca.md), [`pdca-guide.md`](pdca-guide.md),
  [`skills/pdca/SKILL.md`](../skills/pdca/SKILL.md).
- The batch form that may contain campaign items: [`pdca-collection.md`](pdca-collection.md).
- The coding overlays that apply to a step: [`pdca-coder.md`](pdca-coder.md),
  [`pdca-dotnet.md`](pdca-dotnet.md).
- Host setup: [`install.md`](install.md).

## Sources

| Claim | Source |
|---|---|
| The incremental form inherits the base common contract and adds only the campaign layer | `skills/pdca-incremental/SKILL.md §Inheritance: the base contract is the single source of the shared rules` |
| When to use the form and why a named form is a constraint | `skills/pdca-incremental/SKILL.md §When to use` |
| Probe, increment and step | `skills/pdca-incremental/SKILL.md §Probe, increment and step` |
| Goal predicate, recipe, threshold provenance, baseline and accepted basis | `skills/pdca-incremental/SKILL.md §Campaign goal and measurement` |
| Step IDs are not base counters | `skills/pdca-incremental/SKILL.md §Step and counters` |
| Campaign invariants, pause and commit policy | `skills/pdca-incremental/SKILL.md §Campaign invariants` |
| The campaign container, field rules and shared log | `skills/pdca-incremental/SKILL.md §Campaign status` |
| Preparation, baseline and checkpoint records | `skills/pdca-incremental/SKILL.md §Preparation record`; §Baseline record; §Checkpoint |
| Bootstrap, discovery, brief, execution and boundary | `skills/pdca-incremental/SKILL.md §Campaign cycle`; §0. Bootstrap (once); §1. Discovery (before each step); §2. Step brief; §3. Step execution; §Step boundary |
| Acceptance, carry-over and the veto | `skills/pdca-incremental/SKILL.md §Acceptance and carry-over`; §Claims and veto |
| Stop statuses and whole-goal verification | `skills/pdca-incremental/SKILL.md §Stop` |
| No autonomous cutoff and campaign recovery | `skills/pdca-incremental/SKILL.md §Effort accounting and safety`; §Strategic revision and recovery |
| Economics and sizing | `skills/pdca-incremental/SKILL.md §Economics and sizing` |
