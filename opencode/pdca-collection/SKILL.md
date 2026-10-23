---
name: pdca-collection
description: "PDCA collection: a batch of tasks with independent goals, each planned in full before any DO, then clustered into parallel groups (worktree per group, `git merge --no-ff` of the `done` groups only). User-invoked — runs only when the user explicitly names `pdca-collection`."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# A batch of tasks as PDCA

## Role

You drive a **batch of tasks** — a stack-neutral top level above the PDCA cycle.
Load this skill; the base (state machine, gates, roles) is neither duplicated nor
overridden. A collection = a list of tasks; groups are an execution mode, not an entry condition.

**The cycle variant is chosen per task — here, in the collection contract.** Every task (and
every corrective task) is executed by `pdca-orchestrator`, but the collection decides the
variant: `.NET/C#` → `pdca-dotnet`, other code → `pdca-coder`, otherwise → `pdca` (by
default), and passes it to the driver as `selected_variant`. This applies to units with
`execution_kind=cycle`; a campaign unit has no unit-level variant — the variant is chosen by
`pdca-planner` for a concrete step by the campaign's stack rule and persisted until the step.
The driver does not classify the task and does not choose the variant itself. The collection's base is the standard CHECK of the code contract
(`../pdca-coder/SKILL.md`; for .NET — the identical base
`../pdca-dotnet/SKILL.md`).

**First we plan the tasks, then we cluster.** A collection starts not from a
preliminary analysis of the descriptions but from **each** task's **own genuine PLAN**
(its variant). The early PLAN is the very same plan that is executed later: the task
goes through it in phase P, stops at the PLAN→DO boundary and **hands control to the
collection parent**, and the lane later continues **that same** cycle with DO. Control
is handed over at the existing PLAN→DO boundary (just as a manual run hands it to the user before
their plan approval) — this is not an alternative imitation of PLAN and not a standalone-autonomous phase.

You (the primary orchestrator) **do not edit files and do not run commands yourself**.
The infrastructure (worktrees, branches), `git merge --no-ff` and the mandatory checks of a task
are executed by `pdca-executor` on your command; you own the tracking, the gates and the merge decision.

A standard multi-group run assumes an **explicitly authorized autocommit** for the
`collection/**` branches and `merge --no-ff` (otherwise the task branch will not get a committed
tip — the last commit the next one branches from). This authorization is given by a
**project overlay** (a rule or a skill of a particular project) or by an
**explicit user request**; the `pdca-collection` skill itself **grants no** universal right to
commit/merge and does not extend the global `AGENTS.md`. **Without authorization** a
multi-group run does not start: that is a preflight blocker, not a silent switch to another model.
The absence of authorization is **not** an authorization.

- **`>=2` groups and a known incompatibility** (an explicit user no-commit, commit/merge
  unavailable or forbidden) — a **preflight blocker before worktree/lane allocation**: the groups do not
  start until the authorization is obtained or the user changes the input. A group that is
  known to be unable to make the mandatory tips is **not** executed.
- **One group** may work in the **current** tree without commits if that is allowed:
  git integration (group/task branches, merge) is not required, the result is the working tree and
  evidence; `incomplete` here is only an explicit terminal outcome, not a consequence of a missing
  commit.
- **Authorization withdrawn/became unavailable during a running lane** (`>=2` groups) — safe
  stop: keep the existing commits/refs and the uncommitted changes of the task/group as a
  patch, do not continue the branch chain, do not merge; `incomplete` — only by an explicit
  final outcome, not automatically from the fact of the withdrawal. Push — **never**.

## Collection (P / D / C / A)

### Collection units and the execution form

A batch consists of **collection units** (`unit`). Every unit has an execution form
`execution_kind`, and there are exactly two values:

- `cycle` — a single cycle: one full PLAN → DO → CHECK → ACT of the chosen variant;
  such a unit has `plan_state` and `selected_variant`;
- `campaign` — an incremental campaign with its own goal, frame (the preparation document),
  runtime status and steps. A campaign unit has **no** own `selected_variant` and
  no "campaign domain": the variant appears only on a concrete step.

`execution_kind` and `selected_variant` are different fields. A unit's execution form is decided by the collection
PLAN (`pdca-planner`); the runner only reads the ready value and does not classify the
task.

**Composition is not recursive.** A campaign step is only a family cycle; "a campaign in a campaign",
"a collection inside a campaign" and "a collection inside a collection" are forbidden, so a nested
execution form is not expressible.

### P — per-task PLANs, the barrier, clustering

The order is strict: **each task's own PLAN → ALL-barrier → DAG and groups.**
A preliminary analysis of the task descriptions (`pdca-scout`) is by itself **not** a PLAN and does not
replace it.

1. **Input and bootstrap.** The task list in any form is given by the user. Give every
   unit a stable id, the source brief and `execution_kind`. The initial `execution_kind` of every
   unit is decided by the collection PLAN (`pdca-planner`) **before** the per-kind dispatch; the primary/runner only
   passes the ready value and does not infer it from the task text. `selected_variant` is chosen
   **only** for a `cycle` unit (§Role); a `campaign` unit has none — the variant will appear on a
   concrete step. Pass the common task list to each unit as context, as a source of
   dependency requirements — but do **not** compute the DAG, the order or the groups in advance.
2. **Each task's own PLAN / campaign preparation.** Through `pdca-orchestrator` at the
   **COLLECTION TASK PLAN** entry, run the route matching the `execution_kind`
   (the dispatcher neither derives nor classifies it):
   - `cycle` — the task's own genuine PLAN of its variant: `pdca-scout` gathers facts,
     `pdca-planner` makes decisions, `pdca-executor` persists the status. The task's PLAN
     ends at the PLAN→DO boundary (durable checkpoint) and **hands control to the
     collection parent** — it is not DO, not an error and not the completion of the task. Together with
     the plan, handoff metadata goes to the collection: the planned write footprint and its
     uncertainty, the requirements on the predecessors' results, assumptions/prerequisites
     and refs, and — in normal mode — the durable pending approval ref pointer (the handoff is a
     checkpoint for the parent, which owns obtaining the approval). The task's code is **not**
     written at this step.
   - `campaign` — **frame preparation**, not a step PLAN: `pdca-scout` gathers facts,
     `pdca-planner` makes decisions, `pdca-executor` writes the immutable preparation document
     (§"Barrier by unit kinds"), `preparation_state` (`pending` | `ready`; `ready` is not
     `met` and does not equal completion) and the single `preparation_ref`. A
     `preparation_handoff` is returned; a unit-level `selected_variant` is neither required nor requested.
     The baseline, the runtime status, the plans of future steps, their number and their variants are **not**
     created or required at this step — they appear after the barrier and the step's own PLAN.
     The dispatcher receives the selection rule (stack rule) from the caller and passes it to the campaign;
     it does not classify the task and does not choose the variant itself.

   **The units' PLANs are independent and run in parallel.** One unit's plan does not require another
   unit's artifacts: the dependency is recorded as a requirement on the predecessor's results in the
   handoff metadata, not as waiting for someone else's plan.

   - **Dispatching.** `COLLECTION TASK PLAN` is sent immediately for all units without a
     ready plan/frame — by the criterion of their kind (§P.3 and "Barrier by unit kinds") — up to
     the ceiling `plan_cap` (§Parameters); handoffs are accepted as they become ready, not in the order the
     tasks were declared. Several calls go out **as one block** (up to `plan_cap`), not one at a
     time: sending the next one only after the previous one returns is serialization, even
     if the text says "in parallel". Actual parallelism is bounded by the host's capabilities:
     `plan_cap` is an upper bound, not a guarantee.
   - **Status writing.** The primary appends the rows of the common collection status file after
     each handoff returns, not between sends. The write is serialized, not
     delegated to every PLAN: the semantics of the rows is set by the primary/`pdca-planner`, the physical
     write is performed by `pdca-executor` on an explicit dispatch (§Collection status), so the unit rows,
     `plan_handoff`/`preparation_ref` and the decisions log are entered one by one, without a race.
     A parallel PLAN changes the cost of the phase, not the content of the rows.
   - **Barrier.** §P.3 is not weakened by this: it is about the readiness of **all** plans, not about their
     sequence.
   - **Schedule.** A parallel PLAN **does not fix the schedule**: the groups and the order
     are determined only after the barrier (§P.4), so a sequential chain of tasks in one
     group is a normal outcome, not a conflict with parallel planning.
   - **Code overlap** is resolved there too: the footprint reservation is a **claim** for
     clustering, not a lock. The PLAN **declares** the write footprint and its
     uncertainty, but holds no lock and does not prevent other plans from being assembled in parallel.
     Overlapping footprints do not forbid parallel planning — they forbid
     parallel **lanes**: such units land in one group and go through it sequentially
     (branch after branch), and the groups' footprints do not overlap after clustering.
   - **A dependency on a predecessor's result** is recorded in the handoff as a requirement on the
     results; the lane checks applicability before DO and, when the premises are unmet,
     returns the task to its own PLAN (§Stale PLAN).

   **A re-entry after a terminal `incomplete`/STOP** does not re-run the failed
   criterion unchanged: the previous terminal cause is a mandatory input of the own PLAN,
   and `pdca-planner` either proves that the evidence is now obtainable or redefines
   the oracle; otherwise the task stays a gap (§ALL-barrier, §Stale PLAN).

   **A collection is a batch, not a licence to skip plan hygiene.** The task's own PLAN
   validates its command contract before `plan_state=ready` (selectors resolve, argv survives
   the harness, phase/scope legal, expected outcome declared), names a stop-loss budget, and — for
   an unproven mechanism — plans a bounded probe before the full acceptance contract. A plan whose
   decisive command cannot run is a gap at the barrier, not a lane surprise.
3. **ALL-barrier.** The DAG, the groups and the order are **not built** until the requirement of its kind
   is met for **every** unit (§"Barrier by unit kinds"): for `cycle` — this cycle's own genuine
   PLAN with `plan_state=ready`; for `campaign` — an approved preparation document with
   `preparation_state=ready` and `preparation_ref`. A unit's readiness by its kind is **not** a
   user approval and **not** a successful completion of the task; readiness alone never triggers
   lane allocation or an early DO — in normal mode the lane's DO still waits for the recorded
   approval against the unit's pending approval ref (§Approval protocol). A task for which a
   meaningful plan is impossible (not enough data/decisions) stays a gap and is **not**
   marked with a `ready` placeholder: the barrier is not passed, early DO is forbidden. The barrier
   constrains the **start** of the DAG/groups/lanes, not the order of the PLANs: it does not require
   assembling the plans sequentially and does not forbid the parallel dispatching of §P.2.
4. **Clustering (after the barrier).** `pdca-planner` validates the contradictions and the
   uncertainty from the handoff metadata, then builds the DAG and cuts it into groups by the
   applicable rules: a group = a connected component/line by dependencies and shared
   files; the groups' footprints do not overlap; inside a group the tasks are ordered
   topologically. The result is bound to the **PLAN revision vector** (which plans exactly
   were used) and recorded in the collection status file (§Collection status). Before the persistent
   binding of the schedule there is no lane allocation.
   **Width is an objective, not a by-product.** Minimise the largest serialized group: a
   component whose units touch disjoint file families is cut into separate groups even when one
   lane could carry them in order. A schedule that leaves most units in one chain has degraded to
   a single lane by construction and must be justified in the status file, not accepted silently.
   The schedule also declares the **host budget** — available memory, measurement locks, container
   capacity — and `cap` is derived from it (see §Parameters), never from the number of groups.
   After the first wave the schedule is **re-examined**: a group that has lost its last writer
   releases waiting units into a new lane through the persisted revision binding; this is a
   schedule revision, not an automatic recluster.
   **Parallelism is not an entry condition.** If the barrier leaves one group, the host
   allows only one lane (`cap = 1`), or the tasks share a measurement resource, that is a
   normal degradation to a single lane (§Lane), not a reason to change the contract. Do not create
   fake groups and do not call the run parallel.
5. **The only progress mirror is the collection status file.** There is no separate sidebar todo:
   the host may not provide a todo tool, and a second mirror only produces
   divergence. You (the primary) **define the semantics** of the collection status file write (§Collection status)
   in the same tick as the event: a group/task transition, a group stop, a merge,
   a corrective task, an escalation; **the physical write is performed by `pdca-executor`** on an explicit
   dispatch — the primary does not write files itself. Before dispatching, check the status file;
   after compaction the state is restored from it, not from memory. Groups, tasks and their
   statuses live in the tables of §Collection status — a separate list of items is not needed;
   `pdca-orchestrator` subagents write the status file of their own task, not the sidebar.

#### Barrier by unit kinds

The ALL-barrier imposes the requirement of its kind on every unit:

- **`cycle`** — a genuine PLAN of this cycle: `plan_state` (`pending` | `running` | `ready`) with
  the value `ready`, the plan revision, the footprint reservation and its uncertainty, the requirements on
  the predecessors' results, assumptions/prerequisites, refs. This is the same plan that is later
  executed; `plan_state=ready` is the readiness of the plan, not an approval and not completion.
- **`campaign`** — an approved separate immutable/revisioned **preparation document**
  (frame) at the path `.pdca/<collection-id>/units/<unit-id>/preparation.md`, the readiness
  `preparation_state` (`pending` | `ready`) and the **single authoritative** `preparation_ref`
  of the form `<path>@r<k>` in the unit record. `ready` is not `met` and is not the completion of the
  campaign. A unit-level `selected_variant` is **not** required at the barrier: the variant of the step is chosen by
  `pdca-planner` by the stack rule and persisted until the step. `campaign_ref` — a pointer to the runtime status of the
  campaign: before the baseline bootstrap it may be absent and after it is mandatory; this is not a pointer
  to the frame and not a replacement for `preparation_ref`.

**What the barrier does not have.** Not needed: a unit-level `selected_variant` for `campaign`, baseline
evidence, the `running` runtime status, the campaign status file, the plans of future steps, the chosen
variants of future steps and the number of steps. A unit without a meaningful plan or frame stays
a gap and does not get a `ready` placeholder. Before the barrier not a single lane is allocated, early DO is
forbidden for both kinds.

**The campaign frame — nine mandatory items:** (1) a verifiable goal predicate; (2) the
target/floor criteria — concrete values or, approved before the evidence is obtained, the rules for deriving them;
(3) the step acceptance criteria and the boundary of the credited measurement; (4) the boundaries and the conservative reservation of the
surface as a subset of the unit's surface; (5) dependencies without hidden order;
(6) resources and proof of non-conflict with the schedule; (7) advancement rules;
(8) stop rules and the bootstrap protocol; (9) evidence of schedule compatibility:
single-threadedness, the declared status/evidence paths, the absence of a hidden reverse order,
a predictable read point of the runtime status, step kinds only `increment`/`repair`/`verify`.

#### Three operations: preparation, baseline bootstrap, change-producing DO

| Operation | When | What it creates | What it does not do |
|---|---|---|---|
| **Preparation record** | before/at the barrier, on dispatch | the preparation document, `preparation_state`, `preparation_ref`, the plan, refs, the collection status | does not measure the goal, does not change the product, does not create the runtime status |
| **Baseline bootstrap** | after the barrier, before the first step DO, by a dedicated `pdca-executor` | baseline evidence by the recipe and the campaign runtime status `Status: running` referring to `preparation_ref` (+ the `campaign_ref` path) | is not a step, is not credited, does not change the product, does not copy the frame |
| **Change-producing DO** | after the baseline and the step's own PLAN | product/artifact changes of the step | does not start without the step's PLAN and an applicable frame |

Before the barrier the executor's **preparation records** are allowed (the plan, `plan_state`, the preparation
document, `preparation_ref`, links, the collection status); substantive bootstrap and DO of a task before the
barrier are forbidden.

**Readiness ≠ completion.** `preparation_state=ready` without runtime is `barrier-ready`, not
`started`: the unit stays `pending` and never `done`. The only success of a campaign is
an accepted `met`; the barrier does not require what is created later.

**Renegotiation.** A new **revision** of the immutable preparation document is allowed only for the
method, the schedule, the surface boundaries or other parts of the frame **compatible with the unchanged
goal/recipe/threshold/floor and the approvals already given**; that is `pdca-planner` and the applicable
approval, then a new revision, an update of `preparation_ref` and preservation of the previous one. A change of
the **goal, measurement recipe, threshold or floor** is not a revision and not a "refinement": it is a **new
campaign with a new baseline** and a new frame/unit, even if the collection-id is kept.
A silent edit, a weakening of criteria and a backfill of already accepted criteria are forbidden; the old
immutable revisions are not rewritten. An extension of a **compatible** surface is stop/reapprove,
but it does not change the metrics/threshold/floor (§"Surface reservation").

If there is **one group** — do not fail: degrade to a single lane. **No worktree and no group
branch are created**: work in the **current** worktree on the current branch,
the commits (in autocommit mode) go straight into it, `merge --no-ff` is not needed — there is
nothing to merge; the merge barrier (§D.3), the group/task branches and the merge itself **do not
apply**. On `incomplete` of such a group the commits already made **stay** in the
current branch (no automatic rollback), and the uncommitted changes of the failed task
are preserved as a patch; only the paths of that task are rolled back (§Lane, §Failure). If there are no independent tasks at all — an ordinary pdca cycle; an empty input →
report that there is nothing to do.

### D — infrastructure, tracking, merge

The lanes (worktrees, group/task branches, executors) are allocated **only** after the
ALL-barrier and the persistent binding of the schedule (§P.3–§P.4). Before that step they do not exist.

1. Through `pdca-executor`: one worktree per group
   `<repo>-worktrees/<collection-id>/<group>` and the branch `collection/<id>/group-<g>`.
   **If there is one group** — no worktree and no branches (`group-<g>`, `task-<g>-<k>`) are
   created: work in the **current** worktree on the current branch, the commits go there
   too; instead of `merge --no-ff` — ordinary work in place (there is nothing to merge).
2. The `pdca-orchestrator` agents are started in parallel (one subagent per group), no more than
   `cap` at a time. With one group — one `pdca-orchestrator` in the current worktree.
3. **Merge barrier**: with `>=2` groups the merge starts only when **all** lanes are
   terminal (`done` | `incomplete` with an explicit outcome) — readiness = terminality,
   **not** success. Then `pdca-executor` sequentially performs `git merge --no-ff` **only for the
   `done` groups** (the message starts with `#<n>` for an issue task); a successfully integrated group
   moves `done` → `merged`. **An `incomplete` group is
   never merged**, even if before the failure it has successful tasks and commits: its tip
   (the last commit of the branch) does not enter the integration, the results are preserved (§A, §Failure).
   **A running lane is not merged early.** With **one** group no merge/worktree/branches are
   created (see §P). If the merge conflicts — `pdca-executor` runs `git merge --abort`, the group
   **is escalated**: `pdca-escalate` (strong) makes the decision — resolve manually, reorder
   the order or mark the group `incomplete`; the other groups are not touched; gate `C` is not
   passed until the conflict is resolved.

   **Merge conflict — a repeated merge through the orchestrator.** `pdca-escalate` (strong) is not an
   executor: it never edits files itself, does not run and does not spawn `pdca-executor` — it only
   returns a decision. The expert's answer is **not** a merge success. On a "resolve manually"
   or "reorder" decision the orchestrator returns control to MERGE and **itself** dispatches
   `pdca-executor` for a repeated `git merge --no-ff` of the **unmerged** tip (after
   `git merge --abort`), to resolve the conflict by the decision and finish the merge. The order can be
   changed only for groups **not yet integrated**; a previously merged tip (e.g. `G1`)
   is not touched — no repeated merges of already integrated tips, no rerun/reset/revert/remerge
   of groups and no reset of successful results. After a successful repeated merge the
   **remaining pending/eligible** merges continue; the **full** CHECK of the parent collection is performed
   only when all selected `done` groups are integrated, there is no active conflict and no
   unfinished merge state. A repeated conflict again → `git merge --abort` and
   `pdca-escalate` again (without a new attempt counter: the base `r`/`n` are not introduced). The
   "mark `incomplete`" decision explicitly returns control to MERGE: the tip of that group is **fully
   excluded** from the integration (even if part of its tasks/commits is successful), and the **remaining
   `done` groups** are integrated by the usual policy; already merged `done` groups are not touched
   and not reordered.
4. You **define** the status records: a task `pending` | `in-progress` | `done` | `incomplete`; a group
   `pending` | `in-progress` | `done` | `incomplete` | `merged`; the physical write into the file is
   performed by `pdca-executor`. `merged` is the status of an **integrated** `done` group (the transition
   is only `done` → `merged`); `incomplete` stays `incomplete` and never `merged`.
   A separate integration note `skipped` ("not selected for integration" + the reason) is **not**
   a group status and does not extend the enumeration. The status is recorded in the same tick as the
   event: the status file is the only progress mirror, a divergence from it is an error.

### C — verification (the standard CHECK)

The common verification of a collection is the **standard CHECK of the base contract** (two ticks:
Gather cheap → verdict `pdca-check` medium; the input and the verdict format — `../pdca-coder/assets/agents/pdca-check.md`,
the structure — `../pdca-coder/SKILL.md` §CHECK; for .NET — the identical
`../pdca-dotnet/SKILL.md` §CHECK), and **not** a separate
bespoke stage of the collection. When all lanes are stopped, in the main tree: all
**`done`** groups are integrated (**became `merged`**, including a repeated merge after a
conflict, §D.3), **`incomplete` groups are not merged**, and there is **no unfinished
merge state**.

The input of the common `C` includes the **actual statuses of the groups** (`pending` | `in-progress` | `done`
| `incomplete` | `merged`) and a separate **integration note** (`skipped` with the reason);
`skipped` is a mark "not selected for integration", **not** a group status, and introduces no new
status values. Only the **selected `done` groups** are integrated and moved to `merged`;
`incomplete` stays `incomplete` (never `merged`), its evidence is
preserved.
`PASS` of the parent `C` **may coexist** with `incomplete` groups: the report about
**completion** (how many tasks/groups were carried through) and the **verification verdict** of the integrated
tree are **separate** fields. Even if there are no selected `done` groups or the current group is
`incomplete`, the standard `C` is still performed on the integrated tree; the source tasks
are **not** marked `done` retroactively. Counters/escalation — the base ones
(`../pdca-coder/SKILL.md`; .NET — the identical base `pdca-dotnet`), without a collection counter.

The orchestrator **always** — even when all checks are green — gathers through the existing
`pdca-executor`/`pdca-scout` the mandatory reports about the raw measurements (tests — universally, plus
the checks set by the type of work — build/linter for code, render/preview for design and
presentations, performance measurements if there is a hot path, etc.: the command, exit code, log) and
the review-lens reports, and passes the **aggregate** to `pdca-check` (medium). The raw command measurements **never** decide gate PASS by themselves:
the verdict of `C` (`pass`/`fail` + findings) is issued by `pdca-check`; `pdca-check` does not run hands and does not edit code.

- **PASS** → the common ACT of the collection is allowed (§A).
- **FAIL · a real defect** → the orchestrator opens a **standard corrective
  task** (the variant — by the task selection rule, §Role; PLAN→DO→CHECK→ACT) on the **current integrated tree/branch**
  with **its own linked status file**; its ACT returns control to the **full**
  parent CHECK — **all** mandatory common gates are re-run, not only the failed test. A
  cheap verdict without a corrective task is not allowed.
- **No mandatory report / an unreliable report / an environment failure** → a standard
  **re-gather** (gather the missing report again); this is **not** a code defect and **not**
  a reason to edit code. The state of the common verification may stay `blocked`/awaiting-reports
  in the existing status, but there is **no separate bespoke protocol** (a third verdict, a separate
  stage/node).

No automatic rerun/remerge/recluster/reset/revert and no new
collection worktrees/branch chains; corrective tasks are **separate records/links, not
additional lanes**. While `C` is red — **no** success/cleanup, the results are preserved.

The revision/escalation rules inside a corrective task are the **base `r`/`n/3`**
(`../pdca-coder/SKILL.md` §State machine, §Escalation; for .NET —
the identical base `pdca-dotnet`): the same defect after
one fix → `pdca-escalate` **before the second fix** even with a local CHECK=PASS and a new task
id; a change of the task id/session/status file **does not** reset `r`/`n`/the defect history; an exhausted
revision does **not** get a 4th implementation CHECK even after `pdca-escalate` — continuation only
through a genuinely revised plan `r+1`. There is no separate collection attempt counter and no
generalized "three-failure rule of `C` at the collection level". On STOP without an acceptable
revised plan the unresolved status/evidence/integrated work are preserved;
the parent collection stays **`unverified`**, the source tasks — with their **previous**
statuses; **the success of the corrective task by itself does not mean the success of the collection**.

This is **not** mixed with the mechanism of a task's `incomplete` inside a lane (§Lane, §Failure): that one
concerns the failure of a single task of a group and the decision of `pdca-planner` in its cycle, whereas the STOP
of a corrective task is about a repeat of a defect of the **common** `C` and obeys the base `r`/`n`.

### A — completion

Only a **PASS of the common `C`** allows completion. Report (groups, tasks, branches,
merged/incomplete, evidence, the result of the corrective tasks); `pdca-executor` removes **only
disposable** worktrees and temporary group/task branches that are **`done`/`merged`**. The worktrees,
branches, commits and patches of **`incomplete` groups are never deleted**: before any cleanup
their refs (the group/task branch) and patch paths are preserved (simplest — leave their worktree and
refs in place, explicitly recording that in the status); the status/evidence paths stay available — they
must not be deleted while they hold pointers to the preserved results. Push — **never**.
If `pdca-escalate` does not issue an acceptable revised plan/STOP, the
unresolved status, the evidence and the integrated work are preserved: **no** success and no cleanup,
the parent collection stays **`unverified`**, and the source tasks of the collection keep their
**previous** statuses. **A STOP before `C = PASS` — cleanup is forbidden.** **The success of a corrective
task by itself does not mean the success of the collection.**

### A.1 Routing campaign outcomes

Campaign acceptance (`met`) and the common verification of the collection are different events. The success or failure
of a campaign **does not replace** the common `C` on the integrated tree: `C` is performed by its own
rules, and `unverified`/`blocked`/`pass` remain its separate state.

| Campaign runtime status | Per-unit `disposition` | Unit status | Note |
|---|---|---|---|
| `preparation_state=pending`, no runtime | `active` | `pending` | the barrier is not passed |
| `preparation_state=ready`, no runtime | `active` | `pending` | barrier-ready, not started; not `done` |
| `running` | `active` | `in-progress` | an accepted step does not make the unit `done` |
| `met` (accepted) | `finalized` | `done` | the only success of a campaign |
| `blocked` | `paused` | `in-progress` | a checkpoint, not final |
| `stopped` | `paused` | `in-progress` | a checkpoint, not final |
| `unreachable`, the next target is admissible within the unchanged goal/boundaries | `paused` | `in-progress` | a checkpoint; resume is explicit |
| `unreachable`, the route is exhausted | `finalized` (failure) | `incomplete` + reason | only an explicit final unsuccessful disposition |
| `blocked`/`stopped` with an explicit final unsuccessful disposition | `finalized` (failure) | `incomplete` + reason | group-stop |
| the step is not accepted, a `repair`/new revision is in progress | `active` | `in-progress` | the campaign is not closed |
| a `verify` failure | `active` or `paused` by the step's route | `in-progress` | the threshold is not lowered |

Routing rules:

- no new task/group statuses are introduced: the existing
  `pending`/`in-progress`/`done`/`incomplete` are used; `disposition` is a per-unit field, not a status;
- `done` is given **only by an accepted** `met`; the readiness of the frame or `running` do not give it;
- `blocked`/`stopped` are a checkpoint (`paused`, the unit stays `in-progress`), not an
  automatic `incomplete`; an explicit resume is needed;
- `unreachable` with an admissible next target within the unchanged goal/boundaries is also a checkpoint;
- a final `incomplete` and the existing group-stop — only by an explicit final unsuccessful
  disposition: the remaining `pending` units of the group are marked `incomplete` with the reason "the group
  is stopped" and are not executed, the group is not merged, the other groups continue;
- a paused lane does not advance the dependent chain of its group;
- the success criteria, the threshold and the stop rules are not changed silently.

## Lane (work stream)

The `pdca-orchestrator` subagent executes **one** group; work stream: one parallel flow of work per group. With `>=2` groups — an **isolated worktree per group** (absolute paths, `cd`); with **one** group — the current worktree/branch.
For each task in order:

1. with `>=2` groups — the branch `collection/<id>/task-<g>-<k>` from the committed tip of the previous one (with one group there is no branch, work happens on the current branch);
2. **the continuation of the saved own PLAN** of the task of its variant chosen for the task
   (`pdca-dotnet` for .NET/C#, otherwise `pdca-coder`; §Role): `pdca-orchestrator`
   receives the handoff state of the same cycle (the same `selected_variant`/N/`r`/`n`),
   before DO checks the applicability of the plan's premises to the current state of the lane and
   the validity of the revision binding **through the roles** (`pdca-scout` — facts, `pdca-planner` —
   decision), then drives DO→CHECK→ACT with the delegation of
   pdca-planner/pdca-executor/pdca-check/pdca-escalate. A repeated PLAN is by default **not** started —
   the cycle continues from DO; PLAN is reopened only when staleness is detected
   (§Stale PLAN);
3. autocommit after the task (**in an allowed autocommit mode**, §Role) — otherwise
   the next one does not branch from the committed result. Commit **only the files of the
   task** (`git add <paths>`), not `git add -A`: otherwise you will pick up alien/artifact
   files.

`pdca-orchestrator` **makes no decisions** — it only orchestrates the plan: it does not decide that a task is
impossible/not ready/independent, does not choose the scope and does not judge the result; any question it
addresses to `pdca-planner` (PLAN), not to the user. The status `incomplete` is a consequence of a failure or of an
impossibility by the contract (§Failure), not a judgement of the lane.
The source of truth of the queue is the collection status file (§Collection status): `pdca-orchestrator` re-reads it at
the start and after each task, takes the first task with the status `pending` in the
recorded order and updates its status; the launch prompt passes **the path to the file**,
not an enumeration of tasks — that is how the queue survives context compaction and a restart.
Rules:
- with `>=2` groups the task branch is the unit of commit (no per-task worktree);
  with one group there is no task branch;
- **a task failure first → `pdca-planner` (PLAN)**: it may return to DO (the usual loop-backs and
  counters of the base contract) or **finally** close the task as `incomplete`
  (patch + reason in the status);
- a **final `incomplete` of a task stops the whole group**: the next task is not taken by `pdca-orchestrator`,
  all remaining `pending` tasks of the group are marked `incomplete` with the explicit reason
  **"the group is stopped"** and are **not executed**; the group is **not** merged (§D.3);
- the commits of the group already made and the patch of the failed task are **preserved** (§Failure, §Git model);
- **other groups continue** their work — a stop of one group does not stop the other lanes;
- the lane summary is `done` | `incomplete` (per group); the status `blocked` does not exist for tasks/groups —
  `blocked` remains only a state of the parent verification (§C, §Collection status);
- with `>=2` groups the result of a `done` group = the tip (the last commit) of its branch
  `collection/<id>/group-<g>`, ff-advanced to the last completed task; with one
  group the result = the current branch;
- with one group no group/task branches are created: the commits (in the allowed mode) go to
  the current branch, `incomplete` leaves the commits already made in the current branch without an
  automatic rollback, and the uncommitted changes of the failed task are preserved as a patch and
  rolled back only along its paths;
- the lane returns a compact summary of ≤8 lines without code/diffs/logs.

### Lane driver and campaign (mode=collection-lane)

The lane is driven by the existing cheap `pdca-orchestrator` in the mode `mode=collection-lane`;
there is no separate campaign agent and no new `Task` level either. It receives the unit's `execution_kind`,
the loaded campaign contract, `preparation_ref`/`campaign_ref` and **the dispatching rule from the caller** (the campaign's
stack rule); it does not choose the rule and does not classify the task. For a `campaign` unit it drives the campaign's
state machine and the current step cycle **inline** in one lane session: a campaign is always single-threaded — one step at a time, one lane,
without internal parallelism. The concrete variant of the step is chosen by `pdca-planner` by the stack rule
and persisted in the durable record of the step **before** the step; before the bootstrap it is not needed and is not derived by the
runner.

In normal mode every actual step goes through a full PLAN of its variant before its DO
and is approved per the applicable active contract; the approval is recorded as a durable pending
approval ref, and the current unit receives `disposition=paused`. The step brief does not replace the PLAN and is not
an approval. The driver may plan, but **does not** obtain the approval from the user and does not
start a gated DO: that is done by the parent/cheap primary (§"Approval protocol" below), after which
`pdca-executor` records the approval against the same ref. Resume first checks the applicability of the
saved plan through the roles: an applicable plan whose recorded approval matches the pending ref
(normal mode) continues **the same** step without a new PLAN;
a stale plan gets a genuine revision from `pdca-planner` and a **fresh** approval, and the old approval
does not authorize it. Approval-resume does not do an unconditional replan and does not create a new step.

### Lane pause

A lane pause is **derived** from `disposition=paused` of the current unit and is not stored as a separate
authoritative field of the lane. The task status stays the existing `in-progress`: a pause is
not a new status value, no new task/group statuses are introduced. A paused lane does not go to the
next dependent task of its group; the other groups continue.

### Approval protocol (normal mode)

A unit waiting for a user approval is `disposition=paused` with the status `in-progress`, and
**not** `done`/`incomplete`. The mechanics are stated once in the runner (`pdca-orchestrator`
§Normal-mode approval protocol): the **durable pending approval ref**, the approval recorded
against the same ref, the applicability check on resume, the fresh approval after a real revision.
The collection adds only what the collection owns:

1. The driver/lane returns a **checkpoint** to the parent (the collection primary) with the ref —
   the `plan_handoff` carries it as its approval pointer — and does not ask the user itself and
   does not start DO. A brief, a summary or a chat message is not an approval.
2. The primary asks the user; an explicit approval is recorded against **the same** ref. The
   protocol is the same for `cycle` and `campaign`.
3. Resume continues **the same** cycle/step, and an unchanged saved plan is no exception;
   applicability without a matching record is an **approval-needed checkpoint**, not DO and not a
   fresh PLAN. A stale plan gets a genuine revision from `pdca-planner` and a **fresh** approval, and
   the old approval does not authorize it: approval-resume does not do an unconditional replan. A
   paused lane does not advance its group's dependent chain.
4. Autonomous mode does not invent an approval: an external/user approval remains a blocker or
   a STOP until it is obtained. A mismatching/missing approval record is a blocker, not a pass.

## Stale PLAN and schedule revision

Before starting DO the lane checks that the saved PLAN is applicable to the actual state
(are the predecessors' outputs available, have the premises/assumptions changed). This is a narrow
applicability check, not a mandatory repeated PLAN and not the driver deciding instead of
`pdca-planner`.

- **The premises are unmet** → control returns to the **own PLAN** of this
  task: `pdca-planner` decides by the base revision rules (`r`/`n`, §Relation to the base PDCA);
  the counters and the identity of the task are preserved (`N` is not reset, no cycle "from scratch").
- **A change before the lanes start.** If the footprints/dependencies refined from the PLAN change
  the picture, the collection `pdca-planner` may **rebuild the schedule** (DAG/groups/order),
  and the barrier and the revision binding are updated and persisted. This is the only
  allowed revision window.
- **After the lanes start** automatic `rerun`/`remerge`/`recluster`/`reset`/`revert`
  are forbidden (§C). A change incompatible with the approved groups (footprint overlap,
  a broken order) **stops** the continuation pending an explicit decision of
  `pdca-planner`/`pdca-escalate`; a silent old DAG and an automatic regrouping are
  inadmissible. Compatible local revisions may continue only with evidence from
  `pdca-planner` and a persisted updated revision binding; the driver itself does not declare
  compatibility.
- **A new campaign or a new unit after the barrier.** An accepted unit/campaign added
  after the barrier does not mutate the DAG silently: it is an **explicit collection replan/reapprove** (`pdca-planner`,
  in normal mode — the user) taking into account the already started lanes and the stop/scope constraints (§C,
  §Surface reservation). The old identities, statuses and evidence are preserved; there is no automatic
  `recluster`. A compatible local change goes through the existing route (PLAN revision +
  a persisted revision binding); no new topology policy is introduced. The addition also consumes
  capacity explicitly: its queue position is recorded and it may not silently jump ahead of ready
  units; when the milestone window is fixed, it is scheduled for the next milestone instead of
  stretching the current one.

### Surface reservation and its extension

The planned footprint is a **conservative reservation of the allowed surface for the whole task**, and
not a forecast of the exact edits and not the union of the first steps. A wide reservation is allowed and means
less parallelism, not a wrong plan. If the disjointness of the footprints cannot be proven,
the units go in one lane (are serialized): "probably they will not overlap" is not a basis.
Going beyond the boundary stops the work.

The surface is issued by the collection PLAN; the campaign frame contains it as a subset, and a step cannot
go beyond the campaign's surface. An extension of the reservation or of the surface after the barrier is
stop/reapprove, i.e. an explicit renegotiation: `pdca-planner` of the collection PLAN (in normal mode —
the user), taking into account the already started lanes and the already accepted results. There is no automatic
`recluster`/`remerge`/`reset`/`revert`, an already integrated tip is not merged again, and the
accepted steps are not recalculated.

## Git model

Example (the instances `group-A`/`task-A-1` are `group-<g>`/`task-<g>-<k>`):

```text
current-branch
├─ merge --no-ff collection/<id>/group-A   (worktree A: task-A-1 → task-A-2 → task-A-3)
└─ merge --no-ff collection/<id>/group-B   (worktree B: task-B-1 → task-B-2)
```

- With `>=2` groups: 1 worktree per group; the group branch `collection/<id>/group-<g>`
  is ff-advanced to the tip of each completed task and at the end equals the tip of the last one.
- **One group**: no isolation is needed — neither a worktree nor group/task branches; the commits
  go straight into the current branch, `merge --no-ff` is not performed (see §P/§D).
- With `>=2` groups, inside a group — a chain of task branches `collection/<id>/task-<g>-<k>`;
  the next one branches from the tip of the previous one. With one group there are no task branches — only the current
  branch.
- With `>=2` groups the group and task branches are **siblings**, they are not nested into each other:
  git does not allow a ref that is a prefix of another ref.
- Integration — with `>=2` groups **after the terminality of all lanes**: `git merge --no-ff`
  **only for `done` groups**, one at a time, sequentially (§D.3); a successfully integrated group
  moves `done` → `merged`. An `incomplete` group is never
  merged, even when successful commits exist; its refs/commits and the patch
  are preserved.
- `tip` — the last commit of the group branch (with one group — the current branch); for an
  `incomplete` group it is preserved as evidence, but does not enter the integration.
- Merge conflict → `git merge --abort`; `pdca-escalate` (strong) only returns a decision
  (it does not edit itself and does not run `pdca-executor`), and the repeated `git merge --no-ff` of the unmerged tip
  is performed by `pdca-executor` on the orchestrator's dispatch (§D.3); previously integrated tips are not touched;
  gate `C` is not passed until all selected `done` groups are integrated.
- Push — never.
- **The external commit/branch lifecycle of a task belongs to the collection** and follows this model:
  it is the collection that makes the outer completion commit of a completed unit.
- **`Commit policy: none`** of a campaign or a step means the absence of intermediate step commits;
  it does not forbid the collection's external outer completion commit.
- An explicit no-commit restriction of the user conflicting with the git model of `>=2` groups is
  a **preflight blocker before the worktree/lane allocation**, not a silent override of the model and not a
  patch fallback without an explicit decision. For one group git integration is not required (§Role).
  The completion of a campaign and the finalization of the outer task are different events.

## Failure (semantics)

| Event | Behavior |
|---|---|
| A task does not pass CHECK | **do not stop first:** control → `pdca-planner` (PLAN); it may fix it (loop-back to DO, the usual `r`/`n`) or **finally** close the task as `incomplete` (then `pdca-executor` saves the current changes of the task as a patch, returns **only its paths** to the last green tip, writes the reason + the patch path into the status). A final `incomplete` **stops the whole group**: the following `pending` tasks → `incomplete` with the reason **"the group is stopped"**, they are not executed; the group is not merged; the other groups continue |
| The group finished partially (`incomplete`) | its tip is **not merged** even with successful tasks/commits; the results are preserved — refs/branches/commits + the patch of the failed task (in autocommit mode) or the group's aggregate patch by the task paths (if a commit is unavailable); the report says `incomplete` |
| A commit/merge is unavailable, forbidden or withdrawn | **`>=2` groups:** a known incompatibility — a preflight blocker before the allocation; a withdrawal during a lane — a safe stop preserving the commits/refs and a patch of the uncommitted changes, without a further branch chain and merge; `incomplete` only by an explicit terminal outcome. **One group:** work in the current tree without commits is admissible if allowed; git integration is not required. A deny is not bypassed; a normal multi-group no-commit mode is not invented |
| A merge conflict of a group | `git merge --abort` → **`pdca-escalate`** (strong) decides (resolve/reorder/`incomplete`), but does not execute and does not run `pdca-executor`; the orchestrator returns to MERGE and dispatches `pdca-executor` for a repeated `git merge --no-ff` of the unmerged tip; the `incomplete` decision excludes the group tip fully and integrates the remaining `done` groups; already merged ones are not touched; gate `C` is not passed until all selected `done` groups are integrated |
| A regression of the mandatory checks/artifacts of a task | gate `C` is not passed; → §C: an aggregate of the mandatory reports → the verdict of `pdca-check` (medium) → a standard corrective task, a re-gather of the missing report or a `blocked` state; the collection is not closed |
| A missing/unreliable mandatory report or an environment failure | **not** a code defect: no code edits; the condition of the common verification → **`blocked`**; the source transcript/evidence are preserved; after the environment is restored/the evidence obtained — a repeat of **the whole** common `C`; no unbounded auto-polling/retries |
| A repeat of the same defect after one fix | `pdca-escalate` **before the second fix** (even with a local CHECK=PASS of the corrective task and a new task id); a change of the task id/session/status file **does not** reset `r`/`n`/the defect history |
| An exhausted revision / a STOP without a revised plan | there is no 4th implementation CHECK even after `pdca-escalate`; continuation only by a genuinely revised plan `r+1`; otherwise the unresolved status/evidence/integrated work are preserved, there is no success/cleanup, the parent collection is **`unverified`**, the source tasks — their **previous** statuses |
| The lane returned "no result" | the group = `incomplete`, no merge is done, refs/patch are preserved |

## Collection status

File: `.pdca/status/collection-<slug>.md`. It contains:

- the input (the task list) and the `collection-id`;
- the table of groups: id, tasks, order, worktree, branch/ref, **status**
  (`pending` | `in-progress` | `done` | `incomplete` | `merged`): `merged` is an integrated
  `done` group (the transition is only `done` → `merged`); `incomplete` stays `incomplete`
  (never `merged`), and it has the stop reason ("the group is stopped"), the tip/ref,
  the preserved commits, the remainder and the patch path; a separate integration note `skipped`
  ("not selected for integration" + the reason) is **not** a group status and does not extend the enumeration;
- the table of tasks: id, group, branch, status
  (`pending` | `in-progress` | `done` | `incomplete`) and a **separate** phase readiness
  of the plan `plan_state` (`pending` | `running` | `ready`), `selected_variant`, `cycle_id`
  (including N), the canonical status path of the task, `plan_revision` (r), the baseline ref,
  the footprint/requirement/prerequisite refs, the reason + patch path for `incomplete`,
  a link to the task's status file;
  `plan_state` (`ready` ≠ an approval and ≠ `done`) is not the execution status of the task but the readiness
  of its plan; the merge is at the group level, a task never has the status `merged`;
- per unit: `execution_kind` (`cycle` | `campaign`); for `cycle` — `plan_state`,
  `selected_variant` and the pending approval ref pointer (normal mode); for `campaign` — `preparation_state` (`pending` | `ready`),
  the **single authoritative** `preparation_ref` (`.../preparation.md@r<k>`) and `campaign_ref`
  (optional before the baseline bootstrap, mandatory after); the per-unit `disposition`
  (`active` | `paused` | `finalized`) — an explicit field of **both** forms, `cycle` and `campaign`;
  the pending approval refs of the step;
- **three different things:** readiness (`plan_state`/`preparation_state`), the campaign runtime status
  (`Status`) and the per-unit `disposition` — not the same thing; readiness is not runtime and is not
  completion;
- the semantics of the write is set by the primary/`pdca-planner`, the physical write is performed by
  `pdca-executor` on an explicit dispatch;
- legacy files: a missing `execution_kind` is read as `cycle`; an unknown `execution_kind` value —
  **fail closed**, not a guess;
- the decisions of the collection phases (the tasks' own PLANs and the ALL-barrier, clustering,
  the merge strategy) and the **PLAN revision vector** used for the schedule;
- the subsection **"General verification and recovery"** — the state of the **common verification**, not
  the status of a group/task; the enumerations of groups/tasks are **not** extended by this:
  - the last result of the common `C` + the paths to the evidence (command, exit code, log, numbers);
  - the blocking reason (no report / environment failure / a confirmed defect) and the verification state
    (`blocked` | `unverified` | `pass`);
  - the **defect id** and the **history**: the applied fixes and the result of `C` after each
    (the identity of the defect is preserved across closures/restarts of the corrective task);
  - a link to the status file of the linked corrective task;
  - the **next allowed step**;
- Done / Verified / Incomplete.

**Invariants (briefly):**
- `merged` is the status of an integrated `done` group (the transition is only `done` → `merged`);
  `incomplete` is never `merged`.
- `skipped` is an integration note "not selected for integration", **not** a group status and it does not
  extend the enumeration.
- An `incomplete` group is not merged and its tip is not integrated; the results (refs, commits,
  patch) are preserved before and after cleanup.
- `blocked` is a state of the common verification, not a group/task status.
- The status/evidence paths are not deleted while they hold a pointer to the preserved results.
- The `tip` of a group = the last commit of its branch.

## Report

The format — as in §ACT of the base contract (`../pdca-coder/SKILL.md`; .NET —
the identical base `pdca-dotnet`): what was done, how it was verified,
what remains/blocked, the next step. In autonomous mode — without a message
to the user.

## Parameters

| Parameter | Default |
|---|---|
| Skill location | by the host's rules (see `docs/install.md`) |
| Agent location | by the host's rules (see `docs/install.md`) |
| PLAN parallelism ceiling | `min(#units without a ready plan/frame, plan_cap)`; `plan_cap` = 4 is a **scheduling choice of this contract**, not a host setting (the host exposes no such key); always bounded by what the host actually runs at once, and only the write of the common status is serialized |
| Lane parallelism ceiling | `min(#groups, cap)`; `cap` = 4 is a **scheduling choice of this contract**, not a host setting; bounded by the host's observed concurrency **and by the declared host budget** (memory, measurement locks, container capacity) — a declared budget that cannot carry four lanes lowers `cap` and is recorded, not discovered later as timeouts |
| Worktree directory | `<repo>-worktrees/<collection-id>/<group>` (not created with a single group) |
| Merge | with `>=2` groups wait for **all** lanes to be terminal, then `git merge --no-ff` of **the `done` groups only** sequentially (not needed with one group); `incomplete` is not merged |
| One group | work in the current worktree/branch; worktrees, group/task branches and the merge are not created; `incomplete` leaves the commits already made in the current branch |
| Autocommit/merge right | given by a project overlay or an explicit user request; the skill itself grants no right; `>=2` groups without the right — a preflight blocker before the allocation; one group may go in the current tree without commits if allowed; push never |

The roles are shipped with the family (`assets/agents/*.md` of the cycle variant), and the driver
`pdca-orchestrator` lives in `assets/agents/` of this skill; it needs an allowed nested
delegation and dispatching rights in the cheap primary (otherwise — a flat primary fallback).
The full installation checklist — `docs/install.md` in the skills repository.

## Relation to the base PDCA

- The skill **does not override** the state machine and the gates of the base PDCA contract; it
  adds a level above them and is **stack-neutral** — .NET is not required.
- **The cycle variant is chosen per task** (§Role): `.NET/C#` → `pdca-dotnet`,
  other code → `pdca-coder`, otherwise → `pdca`; by default `pdca`. The base for
  `pdca-coder` and `pdca-dotnet` is identical.
- Every task = a full cycle of the chosen variant (its own status file, its own gates,
  its own roles), but the lifecycle spans **two invocations**: the own PLAN in phase P
  (the `COLLECTION TASK PLAN` entry, a handoff at the PLAN→DO boundary) and **the continuation of that same
  cycle** in the lane (with DO). PLAN is part of the task's lifecycle, not a phase that the
  collection replaces with a preliminary analysis.
- The roles (`pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`, `pdca-scout`) — the same; there are no new roles
  except the wrapper agent `pdca-orchestrator`.
- The progress mirror of the collection is its status file (§P.5): it extends §Phase progress mirror
  of the base contract — instead of the phases of a single cycle it holds the tables of groups and tasks,
  it is also the source of truth.
- Recovery after a failure of `C` (the standard CHECK), the corrective task and the state of the
  common verification — §C and §Collection status ("General verification and recovery"); the rules of
  revisions/attempts/escalation — the base of the base contract
  (`../pdca-coder/SKILL.md` §State machine, §Escalation; for .NET —
  the identical base `pdca-dotnet`), without an override and without a collection counter.
  The base collection `incomplete` is **not** added to the base.

## Fallback

If the harness forbids a subagent to delegate (no nested delegation), `pdca-orchestrator`
cannot orchestrate pdca. Trigger: the launch of `pdca-orchestrator` fails with a delegation/subagent-unavailability error. Then — **one** flat-primary fallback: the primary itself leads
"in flight" **one current task per group** (launches to `pdca-planner`/`pdca-executor`/
`pdca-check`/`pdca-scout`), and on completion launches the next task of the same group.
**Independent groups keep the allowed parallelism**: up to `cap` groups at a time if the
host allows it; if the host does not provide concurrency — the same fallback leads the groups
sequentially. `cap` is an upper bound, not a guarantee. The fallback does not substitute roles: another
agent does not perform the functions of an unavailable mandatory role. In phase P the flat primary likewise
conducts the **COLLECTION TASK PLAN** of every unit itself (by its `execution_kind` — the cycle's own PLAN
or the preparation of the campaign frame), observing the ALL-barrier, and continues the saved PLAN in the
lane with DO.

**Capability preflight.** Before the lane allocation and before the start of a campaign in a lane the
observable capability of the host is checked: the availability of the mandatory roles and contracts, of the nested
delegation to the driver, of `pdca-orchestrator` as a subagent and of the `escalate → scout` edge. The check does not
perform dummy substantive work: no trial edits, trial tasks or fake steps.
The exact numeric value of a host setting is not invented. There is no key, schema element or constant of a
parallel cap on the host side in the audited V2 source; this absence does not mean
unlimited concurrency — so the 4 above is a stated scheduling choice, never a claim about the host. The installed driver is compared against
the canonical asset and checked against the applicable permissions: the observed case was an
installed copy without `pdca-scout` delegation, which silently breaks the `escalate → scout` edge.

**Exactly one fallback.** If the lane driver is unavailable, the cheap primary does the work inline
itself, one current task per group; independent groups keep the allowed
parallelism up to `cap` (or sequentially, if the host does not provide concurrency), marks this with the
line `Notice:` with a durable reference to the reason, still dispatches the roles and does not
obtain their rights.

- an unavailable **mandatory role** — a resource stop of the run: another agent does not perform its functions,
  the work stops recording what has already been accepted;
- an unavailable **cycle contract** — fail closed without substituting a "similar" variant;
- **late discovery** — a safe pause before the dependent action, not a weakening of the gate.
