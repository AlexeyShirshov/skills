---
name: pdca-incremental
description: "Incremental campaign contract of the PDCA family: one verifiable goal whose method or volume is unknown, or whose next action depends on knowledge not yet obtained, advanced as a sequence of credited steps by the designated cheap driver. Loaded by the base PLAN when the form is incremental; the user explicitly names `pdca-incremental` to force it."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# pdca-incremental: the incremental campaign

**This is a standalone form contract, not an overlay and not a second cycle.** It carries the
campaign layer — the campaign unit and its credit, shared campaign state, the step boundary's
bookkeeping, baseline bootstrap and stop rules — together with a local copy of the common PDCA
contract. Invoked directly, this file plus `references/common-contract.md` is a complete contract:
**loading the base `../pdca/SKILL.md` first is not required.**

**Load order.** This file, then `references/common-contract.md`; campaign status detail is in
`references/status.md`. The base phase references (`../pdca/references/{plan,check,act}.md`) may be
consulted as optional deeper detail when they exist, but the contractual gates, counters, roles,
approval, escalation, effort and safety rules are in the local common contract. When the step's work
is code, the overlay (`../pdca-coder/SKILL.md`, `../pdca-dotnet/SKILL.md`) loads on top, for that
step only.

## Form, not a second cycle

**The form is fixed.** When the family router decided incremental, its PLAN already chose the
form, the overlay and the **first useful result unit**; when the user named `pdca-incremental`
directly, that explicit choice is the fixed form. This contract starts from that decision, does not
classify the task, keeps no routing table of its own, and never runs a second PLAN on the same
content.

- The incremental form holds when the method is unknown **or** the volume is unknown, or when the
  composition/choice of the next actions genuinely depends on knowledge not yet obtained and cannot
  be justified now.
- The user's explicit choice of this contract is a constraint: work inside it, do not silently
  re-route.
- A step that turns out to be an ordinary bounded task does not leave the campaign on its own and
  does not change the form: it is a step whose PLAN is small, and the campaign continues from its
  accepted result. A genuine strategy change follows `references/common-contract.md` §Strategic revision and
  recovery, not a per-step re-classification.

**Decomposition is an output, not an input.** A collection makes decomposition an input (the list
and footprints are known before the start); a campaign makes it an output — the step *is* the
decomposition chosen after the previous result. A ready list of grilled tasks is therefore a queue
of candidates, never a campaign plan: every goal still goes through discovery and its own PLAN, and
the order may change after an accepted result.

## Driver coordination

The DRIVER role is defined in `references/common-contract.md` and applies to every execution form. In Incremental Execution, the designated cheap driver coordinates durable state, accepted
results, counters, accumulated knowledge, effort accounting, and recovery across all steps.
It dispatches the existing roles for each step's cycle inline, without spawning a new
`pdca-orchestrator` per step. Only `pdca-planner` decides when the next step begins, and
`pdca-executor` performs the status-file writes.

The driver neither classifies the task, replans, nor judges in place of `pdca-check`. It
cannot waive any gate, counter, or permission.

**Normal mode.** The cheap-tier primary drives; the user approves each step's plan before
that step's DO (common contract §Entry and control mode). Missing or mismatched approval is an
**approval-needed checkpoint**, never permission to start DO or a reason for a fresh PLAN.
Autonomous mode has no intermediate plan-approval gate.

**A campaign as a collection item.** One designated cheap driver coordinates its steps and
state without competing coordinators. The collection's batch/lane coordination remains
separate, and the item gains no extra rights from being composed (§Campaign invariants).

## Lens: probe, increment and step

A **lens** is the depth and breadth at which the goal is understood sufficiently to act:
what is known, which boundary opens now, and what remains unknown.

- **Probe** — a bounded computation, measurement, or action within a step. A tool call
  does not start a new PLAN or require its own CHECK. A probe is bounded by the decision
  it investigates, its observable outcomes, and supporting evidence, not by a minute cap.
- **Increment** — a completed opening of the chosen part or question: a justified change
  to the result **or** decision-relevant knowledge. Several cheap, related probes may
  produce one increment; the entire project must not be treated as one step.
- **Step** — a bounded unit of incremental execution with an observable result and a stop
  condition. Its credit is a result change or knowledge that affects the next decision.

A rejected candidate can produce a **knowledge increment** if its findings meaningfully
change the next choice; the rejected candidate itself is not credited. Numeric gain is a
specialization of measurable goals, not a universal requirement.

## Campaign invariants

1. **The goal and the measurement recipe are fixed at the start.** The goal predicate, the unit of
   measurement, the denominator, the exclusion filters and the thresholds are written into the
   status verbatim. A change of the **goal, recipe, threshold or floor** along the way is not a
   refinement: it is **a new campaign with a new baseline**, and the old revisions and accepted
   results are kept — backfill is forbidden. The one exception is a provisional threshold, which
   follows §Threshold calibration.
2. **One credited increment per step.** Credit follows §Lens: a justified change of the
   result **or** confirmed knowledge that changes the next choice or reduces relevant uncertainty.
   A negative candidate that yields such knowledge is credited as the **knowledge increment**, not
   as the rejected candidate. For a measurable goal the credit is one valid measurement by the
   recipe — the metric and the floor are a specialisation, not a universal gate. A repeat without
   new knowledge earns nothing, and **no rule demands a second increment**: one increment that
   satisfies the goal and passes the check ends the campaign.
3. **A result is kept, not retried for luck.** For a measurable goal: exactly one credited
   measurement per step; a replacement run is allowed only for objective invalidity (environment,
   instrumentation), is archived, and is never chosen because its number looks better. A red
   measurement stays red in the record.
4. **The chain advances on accepted state.** The next step's basis is the **accepted** state of the
   previous step — the accepted number for a measurable goal, the accepted knowledge otherwise;
   never a forecast, never an intermediate value, never "about the same". No accepted step, no next
   step.
5. **One step at a time, one lane, no recursion.** Parallel increments start from one gap map,
   duplicate goals and break "step N+1 from step N". A campaign is never nested inside a campaign,
   and a collection is never nested inside a campaign.
6. **Discovery feeds, the planner decides.** A fresh gap map and a ranked seed are gathered before
   each step; the decision on the next step stays with `pdca-planner` at the boundary.
7. **State carries over.** The deferred register with triggers, blocked arms, open tickets, accepted
   knowledge, protected/foreign changes and the effort accounting live in the campaign status and pass to every
   next step. "We forgot" is not a status.
8. **Conservative accounting.** Foreign and protected changes are excluded from the credit; a
   forecast is never written into the accepted column; denominator drift is explained separately.
9. **A pause is not an outcome.** `blocked`/`stopped`/`unreachable` with an allowed next target
   inside an unchanged goal and bounds is a checkpoint: the campaign stays open
   (`disposition=paused`, the unit stays active). It does not reset `N`/`r`/`n`, grants no extra
   attempts, and is lifted only by an explicit resume — a final unsuccessful outcome is explicit and
   is not derived from a pause.
10. **Only an accepted step is committed, and only when allowed.** Auto-commit is not a right of the
    skill: a project overlay or an explicit user request grants it, and the policy is fixed in the
    status (`Commit policy: auto | none`). Under `auto`, after acceptance only the step's paths are
    committed (`git add <paths>`, not `-A`), the message names the campaign and the step, and the
    tip is part of the step's evidence. `push` — never. `none` forbids the campaign's intermediate
    step commits and does not forbid a collection's external outer completion commit: campaign
    completion and unit finalization are different events.

### Threshold calibration

A numeric threshold without a measured baseline is marked **provisional** in the PLAN
(`../pdca/references/plan.md` §Plan fields). Revising it on measurement is a `supersede` record with
the reason and the evidence — **not** a goal change and not a new campaign. A threshold backed by a
measured baseline or set by the user changes only as a goal change (invariant 1). "Red and on
baseline" is asserted by measurement, never by assumption. A metric and a floor are a
specialisation for measurable goals, not a universal gate.

## Campaign status

One file is the campaign's source of truth: `.pdca/status/<campaign>.md`, under the common contract's `.pdca/`
root; the project may add a subdirectory or a suffix inside
`.pdca/status/`, never move it out of the workspace root. It holds **runtime only**, and there is no
separate todo. The physical write is `pdca-executor`'s on explicit dispatch; the owner composes the
content from the reports and passes it in the brief — the owner does not write files.

Beyond the common contract's mandatory status content, the campaign file carries the accepted steps and their
credit, the current step (`cycle_id`, `N`, `r`, `n`), the increment unit and its expected
observable, the accepted knowledge register, the deferred rows with triggers, the effort accounting, the
checkpoint of the last step boundary and the commit policy. `references/status.md` has the full
template, the field rules and the records.

The common contract's status schema applies as written: the append-only progress log, the durable
counters (`Current cycle N`, `Plan revision r`, `Attempt n`), the defect history and the status-file
lifetime. A step boundary is **one** logged event like any other, and the current state always
matches the last log line.

## Campaign cycle

The campaign's PLAN work is one phase with two owners: `pdca-scout` gathers facts (discovery),
`pdca-planner` decides (brief, boundary). Both are PLAN; neither is a separate DO.

### 0. Bootstrap (once)

Three operations that do not substitute for each other:

1. **Preparation record** — on explicit dispatch, before any DO (for a collection item, before or at
   the barrier): the preparation document, its state and reference, the plan and the refs. The goal
   is not measured, the product does not change, and no runtime status is created.
2. **Baseline bootstrap** — after the barrier and before the first step's DO: the baseline is
   captured **with the recipe that will accept steps**, the baseline evidence is stored, and the
   runtime status is opened (`Status: running`) referencing the preparation record. It is not a
   step: it consumes no step, earns no credit and changes no product.
3. **Change-producing DO** — only after the baseline and the step's own PLAN.

Bootstrap fixes, in the status: the goal predicate and the recipe; the baseline with its evidence
path; the increment unit (and, for a measurable goal, the floor and `target = baseline + floor`);
the allowed surface (a subset of the unit surface) and the protected/foreign areas; a **short list
of candidates** for the first step — not a plan for the whole volume.

If the bootstrap shows the recipe inapplicable, the goal unreachable within the bounds or the
surface insufficient, this is a return to `pdca-planner` and the active approval — never a silent
restatement of the criteria. If the baseline **already satisfies the goal**, no dummy increment is
created: the baseline goes to an independent CHECK against the goal criteria and the campaign can
close (§Stop).

### 1. Discovery (before each step)

`pdca-scout` (cheap, read-only) assembles a fresh gap map from the last accepted basis and a ranked
list of goals: expected yield, reachability route, blockers, already closed families, deferred rows
whose trigger has fired. Facts only — it does not rank for the planner's decision and does not write
a brief. The result is the next-step seed in the status. Discovery is not the step's PLAN.

### 2. Step brief

The first step's brief comes from the initial PLAN; every later one from the boundary call that
accepted the previous increment (§Step boundary). It is passed by reference, and it carries six
blocks — the proven minimum that keeps a step from re-opening what is closed:

```text
1. GOAL: the campaign predicate + the step's place in the chain (accepted basis → the observable).
2. CURRENT STATE: the exact accepted basis, the composition of the last accepted result or the
   accepted knowledge, the remaining accounting.
3. HARD CONSTRAINTS: thresholds and their provisional marks, the allowed surface, protected/foreign
   areas, the commit policy (`Commit policy` from the status: under `auto` only the accepted step
   and only its paths; `push` forbidden always), what counts as a valid increment.
4. SCOPE: what is executed, what verifies it, the mandatory controls, the measurement recipe when
   the goal is measurable.
5. ACCEPTANCE: the increment unit, the credit rule (a result change or decision-relevant knowledge),
   what counts as a failure (including a forecast substituted for a number and denominator drift).
6. TARGETS: the seed clusters with `file:line`/nodes and estimates; explicitly — what is not part
   of this step.
```

Six is a lower bound, not a format: each block closes its own failure type (goal drift, a plan built
on stale numbers, threshold substitution, the wrong scope, self-assessment, sprawl). The plan's
detail stays `pdca-planner`'s decision, not the brief's. A project overlay may extend the blocks,
never shorten them. The step's plan is a full plan of **that step**, not a plan of the campaign.

### 3. Step execution

The step runs the **common cycle** — PLAN (`r`, `rv`) → DO → CHECK → ACT — under the common gates,
counters and approval. The campaign does not accept a result in place of CHECK and does not
interfere with the step's gates. The dispatch selection rule is the common contract's: the step's cycle is
`pdca`, and the overlay the plan declared for that step (`pdca-coder`, or `pdca-dotnet` inheriting
it) applies when the step's work is code — a step that touches no code runs without an overlay. The
form is never re-decided per step, and the overlay never opens a second PLAN or a second status.

If the step falls short, the route depends on the finding. An implementation defect is `CHECK → DO`
inside the same step identity; a wrong or unachievable acceptance contract is `CHECK → PLAN` for a
genuine revision (`r+1`). A DO that **cannot finish** makes no CHECK and no planner detour: it goes
`DO → ACT`, which finalizes `blocked`/`incomplete` with the cause, evidence and residual
requirements. The step is **not credited**, the campaign is **blocked** with that residual work, and
a DO failure never earns an accepted increment, never auto-replans, and never advances to the next
step. A red result is kept. Exhausting revisions and attempts follows the common contract: escalation
or an ACT-finalized STOP with the recorded remainder, never a silent move to the next step.

## Step boundary

At the boundary after the step's CHECK, **one** planner call decides and, in the same
turn, emits either the next brief or a STOP. The driver's work is routing and
bookkeeping, not a second PLAN:

- **accept the increment** — on a positive independent CHECK: a change of the result **or**
  decision-relevant knowledge, including an accepted negative candidate (credited as a knowledge
  increment). Then the brief of the next step, or STOP when the whole-goal end conditions are met.
- **revise/reject the same step** — a corrected brief of the **same** step identity
  (repair/loop-back) or a justified STOP. The step number does not grow without acceptance, `r`/`n`
  follow the common loop-back rules, the independent CHECK is never rewritten to `met`, and no
  increment is credited for bypassing a failed CHECK. A failed step never closes the rest of the
  campaign by itself: the blast radius is one step, and the route stays the planner's.
- **a new step** — distinct from revising: history, counters and accounting are preserved, every
  actual cost and attempt counts, and an unaccepted red step is never converted into extra accepted
  progress.

**Whole-goal verification.** A STOP with `met`/`limited` requires a whole-goal CHECK,
combined with the increment's CHECK when it already covers every original requirement and
carrying claim, or performed separately when the last CHECK was local (common contract §One loop,
gate 4). After a local CHECK, the planner issues the final-check brief and a
**pre-set completion condition in the same boundary call**. A whole-goal PASS on all
carrying claims and applicable original requirements permits the designated outcome;
otherwise the result loops back to the planner. On PASS, the driver routes the
pre-approved STOP to **ACT** for finalization by `pdca-executor` — without a new planner call or
an independent verdict. A separate final CHECK is not a step and adds no planner call.
`unreachable` still requires the proven remainder (§Stop).

Planner calls are **accounted**, not capped: the successful path is `1 + number of steps`, plus
genuine revisions (common contract §Strategic revision and recovery), the current step's loop-backs, and bounded
continuations of the **same pending PLAN** for clarification or probe refinement. There are
no hidden exempt planner calls: separate DECIDE → brief → STOP turns on unchanged content
are a repeated PLAN and are not allowed. Example for one increment: initial PLAN → local
CHECK → step boundary (acceptance + final-check brief with the STOP condition) → final
CHECK PASS → STOP — **two calls**.

## Acceptance and carry-over

The verdict is `pdca-check`'s (medium, read-only plus the step's evidence artifacts); the route is
`pdca-planner`'s at the boundary; the physical write is `pdca-executor`'s. ACCEPT and the route do
not merge: the reviewer must not choose the next step, and "the step was not accepted" must not blur
into "the step was accepted but the campaign stops". Between them the accepted basis is fixed, and
the next step is counted from it.

1. Take the step's independent CHECK verdict and the credited increment.
2. After the boundary call accepted the increment, append the row to the step table. Accepted rows
   are append-only; a revised step stays the **same** row under the same identity; a step that is
   never accepted stays `not accepted` with its red result kept.
3. Advance the basis: the next step starts from the last accepted basis plus the credited change —
   a knowledge increment advances it with knowledge, not with an invented number.
4. Under `Commit policy: auto`, commit only the accepted step's paths and record the tip in the
   `commit` cell; `push` never. If the commit is not allowed or failed, record `no commit` and the
   reason — the accepted result lives in the measurement and the evidence, not in the commit.
5. Carry the registers and the knowledge into the status, and write the next-step seed.

**The knowledge register is an append-only fact history:** findings with their scope, conditions,
evidence and limits; explicit assumptions and unknowns; rejected or replaced approaches with the
reasons and the conditions under which they would be reconsidered; the next decision. An accepted
conclusion may be **superseded** with a reason; nothing is backfilled. A working result may be
revised — the working result and the fact history are different things.

## Stop

A `met`/`limited` stop is the planner's decision at the boundary, or the pre-set condition of the
final-check brief recorded by the owner without a new call. A **DO cannot finish** outcome is not a
planner decision and not a CHECK: `DO → ACT` finalizes it directly.

| condition | status | what is recorded |
|---|---|---|
| the whole-goal CHECK passed: the goal predicate is true on the **accepted** state, no carrying claim blocks, the original requirements are verified | `met` | the final result, the remainder, the evidence |
| the remainder is provably unreachable | `unreachable` | per cluster: why, how it was proven, where it was redistributed |
| an external blocker (ticket, environment, access) | `blocked` | the blocker and which goals it closes |
| the DO of the current step cannot finish under the contract | `blocked` | the cause, evidence, residual `unmet`/`unverified` requirements; **no accepted increment**, no auto-replan, the campaign stays blocked with the residual work |
| a verified blocker, security boundary or user stop | `stopped` | what is done, what remains, where to continue |
| a carrying-claim block is removed by an explicit narrowing of the result inside the original goal | `limited` | what was narrowed, why, the blocking finding |

`met` is the only success — the campaign record's `done` — and needs the whole-goal CHECK: a set of
accepted increments and PASS on every mechanical row does **not** prove the whole goal, and a rubric
score or a margin over a threshold never compensates a `confirmed`/`unverified` finding against a
carrying claim (common contract §Claims and veto). `limited` is a narrowing inside the original goal, never a
weakened goal, and in normal mode the user approves it. `unreachable` is proven with numbers (for
example, the goal requires a product change or an unavailable source), never declared from fatigue.
Every non-`met` row is finalized **in ACT**, not on a separate terminal path. Under
`blocked`/`stopped` the chain does not pretend to be closed: the next session continues from the last
accepted basis and the residual work recorded by ACT, and invariant 9 decides whether the campaign is
paused or finally closed.

## Verification

- **A step check is local** to the increment's claims and the affected invariants. The **whole-goal
  check** is separate, and combined with the increment's check when the candidate claims the whole
  goal (`../pdca/references/check.md` §Local and whole-goal checks). It is not a full audit of every
  increment.
- **Not per probe**: several related probes in one increment give one CHECK; a tool call starts no
  PLAN and owes no CHECK.
- **No second judge by default** — only on the common triggers: a margin over the rubric threshold no
  larger than the value declared in the PLAN, an unresolved finding against a carrying claim, or an
  operator/plan requirement.
- **No bespoke verifier "for completeness"** and no coverage audit because it can be built: the plan
  justifies the cheapest sufficient method (`../pdca/references/plan.md` §Verification economy), and
  a custom checker is proportional to the artefact under check.
- Credit does not replace the check. Evidence is bound to the inputs of the claim, not to their
  transitive closure; an unconfirmed claim is `unverified`, never `met`.

## Effort accounting and safety

There is **no autonomous cutoff**: no wall-clock, token, cost, compute, revision, step or measurement
total is fixed before DO to terminate the campaign; elapsed time/cost is accounting only, an
estimate is not a stop condition, and no legacy/plan/resume budget is revived. An accepted whole goal
closes the campaign normally. Otherwise work stops early only for a verified irreducible blocker for
the **agreed goal**, a security/permission boundary or explicit user cancellation; a failed candidate
or incomplete evidence alone is not a blocker — it returns to the step boundary. In
normal mode the driver presents the planner's estimate and asks whether to stop at it; only an
explicit user answer enables that stop, recorded in the existing approval record; the same cutoff
persists across a normal-mode resume or genuine replan (not renewed) until the user changes or
revokes it, and only a switch to autonomous drops it. Per-command timeouts, host capacity and user deadlines stay in
force. The no-4th-pass rule, security/permission boundaries and the protection of irreversible actions are
in `references/common-contract.md` and this contract does not relax them. No new universal minutes or costs; the commit policy of invariant 10 is the
only campaign-specific permission, and `push` is never part of it.

## Economics and sizing

- A step has a fixed price — plan, measurement, evidence, review, status write. An increment cheaper
  than that price does not pay off; the floor formalises this for measurable goals only.
- An oversized step is bad too: its PLAN is written blind, and a failure costs the whole cycle. Aim
  for a step that can realistically be brought home in one or two plan revisions.
- The number of steps is not planned. It follows from the remainder and the actual deltas: "ten
  steps" is a consequence, never a goal.
- Goal estimates are discounted and never written as an accepted result.
- **The last step takes the whole remainder.** When the remainder is comparable to the floor
  (≲ 2×floor), the step is planned for the remainder, not for another floor. Falling short is one
  revision or one more step with the same target — never "the floor, because it is easier".

## Red flags (self-check)

The common contract and the following campaign-specific list govern:

- I wrote a forecast or an intermediate value into the accepted column, or repeated a failed
  measurement for a nicer number.
- I moved the threshold, the denominator or a filter to push the campaign through; I treated a
  provisional threshold as fixed, or a baseline-backed one as provisional.
- I started a step without the previous step's accepted basis, or let "about the same" stand for it.
- I lost a deferred row, a blocker or an accepted finding between steps.
- I ran two increments in parallel, or inflated the whole project into one step.
- I demanded a second increment after the goal was satisfied and checked, or used a completeness
  audit as a substitute for the whole-goal check.
- I let a rubric score or a threshold margin outvote a carrying-claim finding.
- I let DECIDE turn into a second planner call on the same content, or let the reviewer choose the
  route.
- I declared `met` on a step-local or partial check, or on accepted increments alone.
- I repeated an accepted step after a controller loss, or reset a counter or the history.
- I built a "full plan" or a projected backlog before acting.
- I edited outside the allowed surface, or committed/pushed outside the commit policy.

## Recovery

The common contract's recovery rules apply; campaign-specific:

- A **checkpoint is recorded at every step boundary**: the accepted basis, the current step, the
  counters, the remaining accounting and the next-step seed.
- After a lost controller, a host restart, a provider timeout or compaction, the owner restores from
  the status. **Accepted steps are never repeated**, `N`/`r`/`n`, the accounting and the defect history are **not reset**,
  and the work continues from the last checkpoint. An interrupted dispatch is retried no more than
  the common retry rules allow.
- Context compression/exhaustion of the driver's incremental execution session is a special case of controller
  loss: a **planned handover to a new session of the same cheap `pdca-orchestrator`** restores from
  the status at the last checkpoint — not a new role and not a second writer (the previous session
  is finished by then).
- A result whose evidence is missing is not accepted: it is re-measured by the recipe, never
  restored from memory.

## References

Campaign-specific material is loaded when it is used, never up front (the host truncates tool output
at 50 KiB / 2000 lines):

- `references/status.md` — campaign status template and field rules, the preparation document, the
  baseline-bootstrap record and the checkpoint. Load at bootstrap and at every status write.
- `references/common-contract.md` — the self-contained common contract: entry and control mode,
  the one loop, roles and tiers, counters, claims and veto, evidence and workspace, escalation and
  guardrails. Load it with this file; the base `../pdca/SKILL.md` is optional deeper detail, not a
  prerequisite.
- `../pdca/references/plan.md`, `../pdca/references/check.md`, `../pdca/references/act.md` — phase
  detail (plan fields and calibration, the verdict and the veto, the status schema and the progress
  log).
