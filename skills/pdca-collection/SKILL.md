---
name: pdca-collection
description: "Collection execution of independent user goals, each with its own complete PDCA invocation and PLAN-selected form. The collection driver coordinates a preparation barrier, conflict-aware groups, isolated lanes when permitted, independent verification of the integrated result, and ACT without replacing an item goal or its acceptance criteria."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# A batch of independent goals as PDCA

## Scope and entry

A **Collection** is a set of independent user-defined goals. Each item is a separate, complete
invocation of PDCA; a collection is **not** an internal DO decomposition of one goal. Its form
has already been selected by the base entry PLAN (or explicitly named by the user), so no
second PLAN reclassifies the collection.

## Inheritance

`../pdca/SKILL.md` (§Common cycle contract) governs all item cycles, integration
CHECK and corrective cycles. Load it alongside this file; on direct invocation,
skip form reclassification. A `campaign` item also loads
`../pdca-incremental/SKILL.md`. The planner's `plan_reference_path` resolves
from the base `pdca` directory.

Collection adds batch coordination, **not another cycle or attempt counter**.

## Batch terminology

- **Item preparation** — completing the pre-DO work for each goal: a persisted PLAN for a
  `cycle` item (`plan_state=ready`), or a persisted preparation charter for a `campaign` item
  (`preparation_state=ready` with a valid `preparation_ref`). No substantive item DO occurs yet.
- **Preparation barrier (ALL-barrier)** — the gate requiring **every** item to be prepared
  before the collection can build its schedule, allocate execution lanes or begin any item DO.
  Readiness is **not** user approval or task completion; normal-mode DO still requires its
  own recorded approval.
- **Dependency DAG (directed acyclic graph)** — the graph of required order between items:
  an edge `A → B` means B depends on A's result. It is built after the ALL-barrier and
  contains no dependency cycles. File-write conflicts additionally constrain grouping.
- **Group** — a set of items assigned to the same sequential execution queue because of
  dependencies or shared/uncertain write surfaces. Distinct groups are scheduled so their
  work does not conflict and may run in parallel within the host's limits.
- **Lane** — one execution stream running **one group**, with that group's items in order.
  With multiple groups each lane has an isolated Git worktree and group branch; with one
  group it uses the current worktree and branch.
- **Integration** — bringing the completed groups' results together: for multiple groups,
  merge only `done` groups into the main tree, never `incomplete` groups; a single-group
  collection needs no merge.
- **Batch status** — the durable collection-wide record of preparation, groups, item outcomes,
  integration and verification in `.pdca/status/collection-<slug>.md`.
- **Final verification** — the independent CHECK of the integrated result, **in addition to**
  each item's own acceptance CHECK. A verified partial integration is not completion of
  the original goals left unfinished.

The **collection driver** coordinates the batch, including its status, preparation barrier,
schedule, group integration and final CHECK/ACT. It does not plan implementations, choose tests,
judge acceptance, edit files or run commands. `pdca-planner` makes substantive PLAN decisions,
`pdca-check` makes independent CHECK decisions, and `pdca-executor` performs all writes and
execution. Each item has its own **designated driver** and durable record. Collection coordination
is separate from the execution of the individual goals; no two drivers compete for an item's state.

In **normal mode**, the primary drives the collection and the cycles/steps, obtains the user's
approval before each DO and does not dispatch `pdca-orchestrator` to drive a cycle or step.
In **autonomous mode**, the primary delegates coordination to `pdca-orchestrator` when permitted;
an available group runner may itself be the designated driver for its items and, for a campaign,
its successive steps. A single campaign keeps **one driver across all steps**. Host inability to
delegate follows §Fallback, without transferring PLAN or CHECK authority to a cheap driver.

The collection adds item preparation, ALL-barrier, DAG/groups, lanes, integration,
batch status and integration verification. A one-item or one-lane collection remains
valid; these collection-specific rules never waive inherited cycle requirements.

A standard multi-group run assumes an **explicitly authorized autocommit** for the `collection/**`
branches and `merge --no-ff` (otherwise the task branch will not get a committed tip — the last
commit the next one branches from). This authorization is given by a **project overlay** (a rule or
a skill of a particular project) or by an **explicit user request**; the `pdca-collection` skill
itself **grants no** universal right to commit/merge and does not extend the global `AGENTS.md`.
**Without authorization** a multi-group run does not start: that is a preflight blocker, not a
silent switch to another run mode. The absence of authorization is **not** an authorization.

- **`>=2` groups and a known incompatibility** (an explicit user no-commit, commit/merge
  unavailable or forbidden) — a **preflight blocker before worktree/lane allocation**: the groups do
  not start until the authorization is obtained or the user changes the input; a group known to be
  unable to make the mandatory tips is **not** executed.
- **One group** may work in the **current** tree without commits if allowed: git integration is not
  required, the result is the working tree and evidence; `incomplete` here is only an explicit
  terminal outcome, not a consequence of a missing commit.
- **Authorization withdrawn during a running lane** (`>=2` groups) — safe stop: keep the commits/refs
  and the uncommitted changes as a patch, do not continue the branch chain, do not merge;
  `incomplete` only by an explicit final outcome, never automatically from the withdrawal. Push —
  **never**.

## Items and execution ownership

Each item preserves its original goal and user criteria; scheduling metadata cannot
redefine acceptance. In the first PLAN, `pdca-planner` selects `cycle` or `campaign`
and, only for `cycle`, the specialized skill. The collection driver neither
classifies items nor inserts another PLAN. A `cycle` resumes its saved PLAN at DO
after the barrier (unless stale); a `campaign` has no item-level contract/overlay:
each step gets its own selection, without planning future steps during preparation.

The collection driver owns scheduling and integration; one designated item driver
owns the cycle or the full campaign across its steps. `pdca-executor` writes both
records. Items cannot be nested collections, and campaigns cannot nest. Item
`done` requires its own accepted whole-goal CHECK/ACT; integration CHECK is separate.

## Capability preflight

Before allocating lanes and again before starting a campaign in a lane, check
the host's observable capabilities: mandatory roles and contracts, permitted
delegation (including the `escalate → scout` path), and the installed
`pdca-orchestrator` against its canonical asset and permissions when applicable.
Do not run trial work or assume numeric host settings.

A missing mandatory role stops the run with accepted work recorded; a missing
contract fails closed, without substituting another. An unavailable optional
runner/delegation follows §Fallback if permitted. A failure discovered late
pauses before the dependent action, without weakening the gate.

## Collection (P / D / C / A)

### P — per-item PLANs, the barrier, clustering

The order is strict: **each item's initial PLAN → ALL-barrier → DAG/groups → item DO**.
The first PLAN of every item is part of its separate PDCA invocation; it is not a second
classification of the batch.

1. **Input and first PLAN.** The input is the user's list of independent goals, each with a stable
   id and its **unchanged** brief and any supplied criteria. Dispatch each item to its own
   `pdca-planner` before choosing `cycle` or `campaign`. The planner chooses form, applicable
   specialized skill and acceptance criteria (only if the user supplied none), but **does not**
   choose implementation actions, steps, verification methods, evidence sources or commands. Only
   at the planner's request does the driver call `pdca-scout` for missing facts. Pass the other
   item briefs as dependency context; do not determine the DAG or group order yet.

2. **Preparation to the PLAN/DO boundary.** Through the item's designated driver, continue the
   **same initial PLAN**, not a new PLAN introduced by the collection:
   - `cycle`: `pdca-executor` records the completed result contract and its
     `plan_state=ready`, then returns a `plan_handoff` at the PLAN → DO boundary. The plan
     includes goals, preserved or derived criteria, constraints, assumptions, bounds, risks and
     stop conditions, but no mandated DO steps or frozen CHECK method. Record the available
     **estimated conflict surface** and prerequisite/dependency assumptions separately as
     scheduling metadata, not as prescribed implementation or an acceptance criterion.
   - `campaign`: follow `../pdca-incremental/SKILL.md` §Campaign cycle / Bootstrap:
     `pdca-executor` persists the preparation charter at
     `.pdca/<collection-id>/items/<item-id>/preparation.md`, its
     `preparation_state` and authoritative `preparation_ref`; return
     `preparation_handoff`. No baseline, runtime record, substantive DO, future step plan
     or step count is required at the barrier.

   PLAN-terminal `acceptance criteria cannot be determined` or proven
   `original task is infeasible under the stated constraints` goes to that item's ACT,
   without DO or CHECK, and **cannot** be marked ready. A failed candidate or an
   unproven method alone does not establish infeasibility; no substitute goal is created.
   A re-entry after a terminal result preserves its cause and history rather than rerunning
   the same failed criterion unchanged.

   **Parallel preparation.** Send the initial PLAN/preparation dispatches concurrently up to
   `plan_cap` and observed host capacity, accepting handoffs as they finish; the physical
   writes to the shared collection status are serialized through `pdca-executor`.
   Independent planning does not require predecessor artefacts. Estimated write surfaces
   are **non-binding claims** derived from known constraints; uncertain or unknown surfaces
   stay explicit and conservatively constrain later lane parallelism. Planning never
   locks files or promises that DO will use a prescribed implementation.

3. **ALL-barrier.** The collection schedule and lanes are not allocated until **every** item
   has a genuine saved `cycle` plan or `campaign` preparation charter. Readiness is neither
   user approval nor completion, and normal-mode DO still requires recorded approval
   against the exact pending ref (§Approval barrier). An undetermined/unreachable goal or
   missing item preparation is an explicit gap: do not invent a `ready` placeholder, bypass
   the barrier or start another item's DO early. Status updates and preparation writes are
   permitted before the barrier; substantive bootstrap and DO are not.

4. **Clustering after the barrier.** `pdca-planner` builds the dependency DAG and
   groups from item dependencies, estimated write conflicts and host capacity. Overlapping
   or uncertain write surfaces must run in one sequential lane; independent groups may run
   in parallel. Persist the schedule and PLAN revision vector before allocating lanes.
   Later changes require a planner decision and applicable approval
   (§Lane execution and schedule revision → Stale plan and schedule revision).
   DO chooses implementation.

5. **Durable tracking.** The collection status file (§Collection status record) is the only
   batch progress mirror. The collection driver coordinates updates, but `pdca-executor`
   writes each transition, handoff, group stop, merge, correction and escalation **in the
   same turn**, without a competing sidebar list. On recovery the status is the source of
   truth; item drivers maintain their own status files by the same one-writer rule.

#### Barrier by item forms

- **`cycle`** — a genuine PLAN of this cycle: `plan_state=ready`, the plan revision, the footprint
  reservation and its uncertainty, the requirements on the predecessors' results,
  assumptions/prerequisites, refs. This is the same plan that is later executed;
  `plan_state=ready` is the readiness of the plan, not an approval and not completion.
- **`campaign`** — the prepared immutable/revisioned **charter** (preparation document) at
  `.pdca/<collection-id>/items/<item-id>/preparation.md`, the readiness `preparation_state`
  (`pending` | `ready`) and the **single authoritative** `preparation_ref` of the form `<path>@r<k>`
  in the item record. `ready` is not `met` and is not the completion of the campaign.
  `campaign_ref` — a pointer to the runtime record of the campaign: before the baseline bootstrap
  it may be absent and after it is mandatory; it is not a pointer to the charter and not a
  replacement for `preparation_ref`.

**Readiness ≠ completion.** `preparation_state=ready` without a runtime record is `barrier-ready`,
not `started`: the item stays `pending` and never `done`. The only success of a campaign item is an
accepted `met`; the barrier does not require what is created later.

If there is **one group** — keep the collection form and use a single lane. **No worktree and no group branch
are created**: work in the **current** worktree on the current branch, the commits (in autocommit
mode) go straight into it, `merge --no-ff` is not needed — there is nothing to merge; the merge
barrier (§D.3), the group/task branches and the merge itself **do not apply**. On `incomplete` of
such a group the commits already made **stay** in the current branch (no automatic rollback), and
the uncommitted changes of the failed item are preserved as a patch; only the paths of that item are
rolled back (§Lane execution and schedule revision → The queue and the per-item continuation). A one-item collection stays a collection; an empty input → report that there is nothing to do.

### D — infrastructure, tracking, merge

The lanes (worktrees, group/task branches, runners) are allocated **only** after the ALL-barrier and
the persistent binding of the schedule (§P.3–§P.4). Before that step they do not exist.

1. Through `pdca-executor`: one worktree per group
   `<repo>-worktrees/<collection-id>/<group>` and the branch `collection/<id>/group-<g>`.
   Group and task branches are sibling Git refs, never name-prefixes of each other.
   **If there is one group** — no worktree and no branches (`group-<g>`, `task-<g>-<k>`) are
   created: work in the current worktree on the current branch, the commits go there too; instead of
   `merge --no-ff` — ordinary work in place (there is nothing to merge).
2. In autonomous mode, available `pdca-orchestrator` group runners are started in parallel
   (one per group, up to `cap`); each may be the **designated item driver** and keeps a campaign's
   driver across all its steps (§Items and execution ownership, §Lane execution and schedule revision). In normal
   mode the primary itself drives the cycles/steps and obtains approval; it does not spawn a
   `pdca-orchestrator` as their driver. Actual lane concurrency is bounded by host capability.
   With one group there is one lane in the current worktree.
3. **Merge barrier**: with `>=2` groups the merge starts only when **all** lanes are terminal
   (`done` | `incomplete` with an explicit outcome) — readiness = terminality, **not** success. Then
   `pdca-executor` sequentially performs `git merge --no-ff` **only for the `done` groups** (the
   message starts with `#<n>` for an issue item); a successfully integrated group moves `done` →
   `merged`. **An `incomplete` group is never merged**, even if before the failure it has successful
   items and commits: its tip does not enter the integration, the results are preserved (§A,
   §Lane execution and schedule revision → The queue and the per-item continuation). **A running lane is not merged early.** With **one** group no
   merge/worktree/branches are created (see §P). If the merge conflicts — `pdca-executor` runs
   `git merge --abort`, the group **is escalated**: `pdca-escalate` (strong) makes the decision —
   resolve manually, reorder the order or mark the group `incomplete`; the other groups are not
   touched; gate `C` is not passed until the conflict is resolved.

   **Merge conflict — a repeated merge through the runner.** `pdca-escalate` is not an executor: it
   never edits files itself, does not run and does not spawn `pdca-executor` — it only returns a
   decision. The expert's answer is **not** a merge success. On a "resolve manually" or "reorder"
   decision the runner returns control to MERGE and **itself** dispatches `pdca-executor` for a
   repeated `git merge --no-ff` of the **unmerged** tip (after `git merge --abort`), to resolve the
   conflict by the decision and finish the merge. The order can be changed only for groups **not yet
   integrated**; a previously merged tip is not touched — no rerun/reset/revert/remerge of groups
   and no reset of successful results. After a
   successful repeated merge the **remaining pending/eligible** merges continue; the **full** CHECK
   of the parent collection is performed only when all selected `done` groups are integrated, there
   is no active conflict and no unfinished merge state. A repeated conflict again →
   `git merge --abort` and `pdca-escalate` again (without a new attempt counter: the common `r`/`n`
   are not introduced). The "mark `incomplete`" decision explicitly returns control to MERGE: the
   tip of that group is **fully excluded** from the integration (even if part of its items/commits
   is successful), and the **remaining `done` groups** are integrated by the usual policy; already
   merged `done` groups are not touched and not reordered.
4. You **define** the status records: an item `pending` | `in-progress` | `done` | `incomplete`; a
   group `pending` | `in-progress` | `done` | `incomplete` | `merged`; the physical write into the
   file is performed by `pdca-executor`. `merged` is the status of an **integrated** `done` group
   (the transition is only `done` → `merged`); `incomplete` stays `incomplete` and never `merged`.
   A separate integration note `skipped` ("not selected for integration" + the reason) is **not** a
   group status and does not extend the enumeration. The status is recorded in the same tick as the
   event: the status file is the only progress mirror, a divergence from it is an error. Details:
   §Collection status record; running the lane: §Lane execution and schedule revision.

### C — integration verification

The parent CHECK uses the **base `../pdca/SKILL.md` §Phase contracts → CHECK**:
`pdca-check` independently chooses methods/evidence for the actual integrated result, with
test execution through `pdca-executor` and outside observation through `pdca-scout`.
Its scope is the **integrated snapshot**, plus integration invariants and any relevant
specialized-skill verification deltas (`../pdca-coder/SKILL.md` and
`../pdca-dotnet/SKILL.md`). It does not replace each item's own whole-goal CHECK.

The integration CHECK starts **after all lanes are terminal**. With multiple groups, all
eligible `done` groups must already be merged, all `incomplete` groups excluded, and
no merge conflict or unfinished merge state may remain. Its inputs include the actual
group statuses and the separate integration note (`skipped` + reason), original item
requirements, the integrated snapshot and evidence pointers.

An integration `PASS` can coexist with `incomplete` groups: it verifies only the
integration of work actually included. Keep the **integrated-tree verdict** and
**collection completeness** as different fields. An integration PASS never marks an
unfinished source item `done`, nor compensates for unmet original requirements.
Run integration CHECK even if no group qualified for integration; no work then gets
retroactive acceptance.

- **Accepted integrated result** → collection ACT (§A), with full completion separately
  conditional on all item outcomes.
- **Implementation defect in the integrated tree** → a linked **corrective PDCA cycle**
  on the current integrated branch, with its own plan, status and base cycle transitions.
  Its ACT returns to the **full parent integration CHECK**, not just the failed probe.
- **Missing, unreliable or unavailable verification evidence** → base CHECK's
  `unverified`/re-gather route; do not turn missing evidence into a product defect,
  attempt or PASS. Preserve the collection verification state and its evidence links.

The collection creates **no additional** attempt counter. For each actual corrective
cycle the base `r`, `n/3`, defect history and `pdca-escalate` rules apply, including
recurrence across linked corrective records; changing a status path or cycle ID does
not erase defect history. A STOP without accepted resolution leaves the parent
collection `unverified` and preserves the prior item statuses and integrated work.
A corrective cycle's local PASS never substitutes for rerunning the integration CHECK.

No automatic rerun/remerge/recluster/reset/revert, no additional collection lanes
for a corrective cycle, and no success cleanup while integration is unverified.

### A — completion

ACT finalizes the collection outcome. **Full collection completion** requires both an accepted
common integration CHECK **and completion of every original item goal** by that item's own
whole-goal CHECK/ACT. An integration PASS with `incomplete` items is a verified partial integration,
**not** full collection success. A `blocked`/`incomplete`/`STOP` outcome is finalized honestly,
without claiming `done` for missing goals and without taking the success cleanup path. Report (§Report); `pdca-executor` removes
**only disposable** worktrees and temporary group/task branches that are **`done`/`merged`**. The
worktrees, branches, commits and patches of **`incomplete` groups are never deleted**: before any
cleanup their refs and patch paths are preserved (simplest — leave their worktree and refs in
place, explicitly recording that in the status); the status/evidence paths stay available — they
must not be deleted while they hold pointers to the preserved results. Push — **never**. If
`pdca-escalate` does not issue an acceptable revised plan/STOP, the unresolved status, the evidence
and the integrated work are preserved: **no** success and no cleanup, the parent collection stays
**`unverified`**, and the source items keep their **previous** statuses. **A STOP or any
non-`PASS` termination — cleanup and merging are forbidden.** **The success of a corrective cycle
by itself does not mean the success of the collection.**

A campaign item's outcome is routed to its item status by §Collection status record → Campaign item status projection; campaign acceptance is not the common `C` and does not replace it.

## Lane execution and schedule revision

### One lane = one group

A lane is one group work stream, driven by its designated driver: the primary in normal mode,
or an authorized `pdca-orchestrator` in autonomous mode (flat-primary fallback if needed). With
`>=2` groups — an **isolated worktree per group** (absolute paths, `cd`); with **one** group — the
current worktree and branch.

For each item in the recorded order:

1. with `>=2` groups — the branch `collection/<id>/task-<g>-<k>` from the committed tip of the
   previous one (with one group there is no branch: work happens on the current branch);
2. **the continuation of the saved own PLAN** of the item's decided form, contract and overlay:
   `pdca-orchestrator` receives the handoff state of the same cycle (the same form/contract/
   overlay, `N`, `r`, `n`); before DO it checks the applicability of the plan's premises to the
   current state of the lane and the validity of the revision binding **through the roles**
   (`pdca-scout` — facts, `pdca-planner` — decision), then drives DO → CHECK → ACT by delegating
   `pdca-planner`/`pdca-executor`/`pdca-check`/`pdca-escalate`. A repeated PLAN is by default
   **not** started — the cycle continues from DO; PLAN is reopened only when staleness is
   detected (§Stale plan and schedule revision);
3. autocommit after the item, **only in an allowed autocommit mode** (§Scope and entry) —
   otherwise the next one does not branch from a committed result. Commit **only the files of the
   item** (`git add <paths>`), not `git add -A`: otherwise alien/artefact files are picked up.

`pdca-orchestrator` **makes no decisions** — it only routes the plan: it does not decide that an
item is impossible/not ready/independent, does not choose the scope and does not judge the result;
any question goes to `pdca-planner`, not to the user. The status `incomplete` is a consequence of a
failure or of an impossibility by the contract (§Lane execution and schedule revision), not a judgement of the lane.

### The queue and the per-item continuation

The source of truth of the queue is the collection status file (§Collection status record): the runner re-reads it
at the start and after each item, takes the first item with the status `pending` in the recorded
order and updates its status; the launch prompt passes **the path to the file**, not an enumeration
of items — that is how the queue survives compaction and a restart.

- With `>=2` groups the task branch is the unit of commit (no per-item worktree); with one group
  there is no task branch.
- **An item failure follows its own cycle's transition**: CHECK alone may send a contract defect
  to PLAN; an implementation defect goes CHECK → DO, and a DO that cannot finish goes DO → ACT.
  ACT records a final `incomplete` with cause and evidence, preserving the patch and status.
- A **final `incomplete` of an item stops the whole group**: the next item is not taken, all
  remaining `pending` items of the group are marked `incomplete` with the explicit reason **"the
  group is stopped"** and are **not executed**; the group is **not merged** (§D.3).
- The commits of the group already made and the patch of the failed item are **preserved**
  (§D, §A); **other groups continue** their work.
- The lane summary is `done` | `incomplete` (per group); the status `blocked` does not exist for
  items/groups — `blocked` remains only a state of the parent verification.
- With `>=2` groups the result of a `done` group is the tip of its branch
  `collection/<id>/group-<g>`, ff-advanced to the last completed item; with one group it is the
  current branch.
- With one group no group/task branches are created: the commits (in the allowed mode) go to the
  current branch; `incomplete` leaves the commits already made without an automatic rollback, the
  uncommitted changes are preserved as a patch and rolled back only along the failed item's paths.
- If the lane returns no result, mark the group `incomplete` and preserve its refs and patch.
- The lane returns a compact summary of ≤8 lines without code/diffs/logs.

### A campaign item in a lane (designated item driver)

An item with the form `campaign` has **one designated driver throughout its steps** — the
primary in normal mode or the authorized cheap `pdca-orchestrator` in autonomous mode, with the
permitted flat-primary fallback (§Items and execution ownership,
`../pdca/SKILL.md` §Control modes). It holds the campaign state/status, the shared counters, the accumulated knowledge and the
effort accounting, owns recovery, starts the next step **only on the planner's decision**, and runs the
current step's cycle inline in its own session. A campaign is always single-threaded: one step at a
time, one lane, no internal parallelism.

It receives the item's form, the incremental contract by exact ID, `preparation_ref`/`campaign_ref`
and the dispatching rule from the caller; it does not choose the
rule and does not classify the item. The contract/overlay of a **concrete step** is decided by
`pdca-planner` for that step and persisted in the durable step record **before** the step; before
the bootstrap it does not exist and the runner does not derive it.

An item with the form `cycle` is driven by its designated driver: it
receives one already-planned cycle, executes it and returns the result; it does not own campaign
advancement and does not advance anything else in the batch.

Collection owns the outer item completion commit; a campaign's `Commit policy: none`
disables intermediate step commits, not that authorized outer commit.

The step semantics — the covered content of one step, the increment unit, the accepted negative
candidate as knowledge, the absence of a forced second increment, the whole-goal final check and
the claims veto — are the incremental contract's (`../pdca-incremental/SKILL.md` §Campaign
invariants, §Campaign cycle, §Step boundary) plus the base phase exits; the collection adds neither a
counter nor a gate.

### Lane pause

A lane pause is **derived** from `disposition=paused` of the current item and is not stored as a
separate authoritative field of the lane. The item status stays the existing `in-progress`: a pause
is not a new status value, and no new item/group statuses are introduced. A paused lane does not go
on to the next dependent item of its group; the other groups continue.

### Stale plan and schedule revision

Before starting DO the lane checks that the saved PLAN is applicable to the actual state (are the
predecessors' outputs available, have the premises/assumptions changed). This is a narrow
applicability check, not a mandatory repeated PLAN and not the driver deciding instead of
`pdca-planner`.

- **The premises are unmet** → control returns to the **own PLAN** of this item: `pdca-planner`
  decides by the base revision rules (`r`/`n`, `../pdca/SKILL.md` §State machine and counters);
  the counters and the identity of the item are preserved (`N` is not reset, no cycle "from
  scratch").
- **A change before the lanes start.** If the footprints/dependencies refined from the PLAN change
  the picture, the collection `pdca-planner` may **rebuild the schedule** (DAG/groups/order), and
  the barrier and the revision binding are updated and persisted. This is the only allowed revision
  window.
- **After the lanes start** automatic `rerun`/`remerge`/`recluster`/`reset`/`revert` are forbidden
  (§C). A change incompatible with the approved groups (footprint overlap, a broken
  order) **stops** the continuation pending an explicit decision of `pdca-planner`/
  `pdca-escalate`; a silent old DAG and an automatic regrouping are inadmissible. Compatible local
  revisions may continue only with evidence from `pdca-planner` and a persisted updated revision
  binding; the driver itself does not declare compatibility.
- **A new campaign or a new item after the barrier.** An item or campaign added after the barrier
  does not mutate the DAG silently: it is an **explicit collection replan/reapprove**
  (`pdca-planner`, in normal mode — the user) taking into account the already started lanes and the
  stop/scope constraints (§C). The old identities, statuses and evidence are
  preserved; there is no automatic `recluster`. A compatible local change goes through the existing
  route (PLAN revision + a persisted revision binding); no new topology policy is introduced. The
  addition also consumes capacity explicitly: its queue position is recorded and it may not
  silently jump ahead of ready items; when the milestone window is fixed, it is scheduled for the
  next milestone instead of stretching the current one.

### Surface reservation and its extension

The planned footprint is a **conservative reservation of the allowed surface for the whole item**,
not a forecast of the exact edits and not the union of the first steps. A wide reservation is
allowed and means less parallelism, not a wrong plan. If the disjointness of the footprints cannot
be proven, the items go in one lane (are serialized): "probably they will not overlap" is not a
basis. Going beyond the boundary stops the work.

The surface is issued by the collection PLAN; a campaign item's charter contains it as a subset,
and a step cannot go beyond the campaign's surface. An extension of the reservation or of the
surface after the barrier is stop/reapprove, i.e. an explicit renegotiation: `pdca-planner` of the
collection PLAN (in normal mode — the user), taking into account the already started lanes and the
already accepted results. There is no automatic `recluster`/`remerge`/`reset`/`revert`, an already
integrated tip is not merged again, and the accepted steps are not recalculated.


## Collection status record

### File and content

File: `.pdca/status/collection-<slug>.md`. It contains:

- the input (the item list) and the `collection-id`;
- the table of groups: id, items, order, worktree, branch/ref, **status**
  (`pending` | `in-progress` | `done` | `incomplete` | `merged`): `merged` is an integrated `done`
  group (the transition is only `done` → `merged`); `incomplete` stays `incomplete` (never
  `merged`), and it has the stop reason ("the group is stopped"), the tip/ref, the preserved
  commits, the remainder and the patch path; a separate integration note `skipped` ("not selected
  for integration" + the reason) is **not** a group status and does not extend the enumeration;
- the table of items: id, group, branch, status (`pending` | `in-progress` | `done` |
  `incomplete`) and a **separate** phase readiness of the plan `plan_state` (`pending` | `running`
  | `ready`), the item's **form** and (for `cycle`) its **contract** and **overlay**, `cycle_id`
  (including `N`), the canonical status path of the item, `plan_revision` (`r`), the baseline ref,
  the footprint/requirement/prerequisite refs, the reason + patch path for `incomplete`, a link to
  the item's status file. `plan_state` (`ready` ≠ an approval and ≠ `done`) is not the execution
  status of the item but the readiness of its plan; the merge is at the group level, an item never
  has the status `merged`;
- per item: the **form** (`cycle` | `campaign`); for `cycle` — `plan_state`, the contract with its
  overlay and the pending approval ref pointer (normal mode); for `campaign` —
  `preparation_state` (`pending` | `ready`), the **single authoritative** `preparation_ref`
  (`.../preparation.md@r<k>`) and `campaign_ref` (optional before the baseline bootstrap, mandatory
  after); no item-level contract for a campaign — the contract/overlay of a concrete step is
  recorded in the step's durable record; the per-item `disposition` (`active` | `paused` |
  `finalized`) — an explicit field of **both** forms; the pending approval refs of the step;
- **three different things:** readiness (`plan_state`/`preparation_state`), the campaign runtime
  status (`Status`, `../pdca-incremental/SKILL.md` §Campaign status) and the per-item
  `disposition` — not the same thing; readiness is not runtime and is not completion;
- an item record without a **form** is read as `cycle`; an unrecognised form value or an
  unresolvable contract/overlay — **fail closed**, not a guess;
- the decisions of the collection phases (the items' own PLANs and the ALL-barrier, clustering, the
  merge strategy) and the **PLAN revision vector** used for the schedule;
- the subsection **"General verification and recovery"** — the state of the **common verification**,
  not the status of a group or an item; the enumerations of groups/items are **not** extended by
  this:
  - the last result of the common `C` + the paths to the evidence (command, exit code, log,
    numbers);
  - the blocking reason (no report / environment failure / a confirmed defect) and the verification
    state (`blocked` | `unverified` | `pass`);
  - the **defect id** and the **history**: the applied fixes and the result of `C` after each (the
    identity of the defect is preserved across closures/restarts of the corrective cycle);
  - a link to the status file of the linked corrective cycle;
  - the **next allowed step**;
- Collection completeness (all original item goals accepted) / integrated-tree verification
  (independent CHECK verdict) / incomplete items and preserved results: these are distinct fields.

### Campaign item status projection

`../pdca-incremental/SKILL.md` (§Campaign invariants, §Stop) defines campaign
outcomes, whole-goal acceptance, pauses and resume. Collection only maps the
campaign's persisted outcome and item `disposition` to its own item status:

- **Before campaign bootstrap** (including `preparation_state=ready`): `pending`.
- **Running or paused** (`disposition=active` | `paused`): `in-progress`;
  a pause stops progression within its group, not other groups.
- **Finalized with accepted `met`**: `done`.
- **Explicitly finalized without accepted `met`**: `incomplete` with reason;
  apply the existing group-stop rule. A failed step or a checkpoint alone
  never finalizes the item.

The collection's integration CHECK remains independent of campaign acceptance.

## Report

The report follows the base §Phase contracts → ACT and `../pdca/references/act.md`:
what was done, what evidence verified it, what remains or is blocked and the next
step. Keep collection completeness distinct from the integrated-tree verdict (§C).

## Approval barrier (normal mode)

The shared approval rules are in `../pdca/SKILL.md` §Normal-mode approval,
including the durable pending approval ref, same-ref approval record, applicability
on resume and fresh approval after a substantive revision. The collection adds one
handoff: the item driver returns its saved `plan_handoff` or
`preparation_handoff` with the **pending approval ref** to the collection
primary. The primary obtains the user's approval; the item driver cannot
invent or infer it, and DO waits for the matching record. A paused item remains
`in-progress` with `disposition=paused`; its lane does not advance to the next
dependent item. Approval is separate from the preparation barrier, which
requires **ready preparation** but not pre-approved DO.

In autonomous mode no ordinary plan approval is invented or required, but an
explicit external/user permission requirement remains a blocker as in the base.

## Fallback

Host role and resource-blocker rules are inherited from `../pdca/SKILL.md`
§Roles and host requirements. This section covers only driver fallback.

When an autonomous `pdca-orchestrator` is absent or cannot delegate, use the **flat cheap primary**
as driver with `Notice:` and a durable reason, if the host permits it. It drives one current item
per lane and delegates PLAN/DO/CHECK to their required roles; a campaign still has one designated
driver for all steps. Independent groups may be processed concurrently up to `cap` only if the
host permits that concurrency; otherwise they are sequential. Normal mode already uses the
primary driver and must not treat the lack of orchestrator delegation as a reason to skip approval.
The fallback never promotes a driver into PLAN, CHECK, execution or expert-review authority.

Missing mandatory roles or forbidden fallbacks follow the base resource-blocker rules;
collection preparation, barrier and handoffs remain unchanged.

## Parameters

| Parameter | Default |
|---|---|
| PLAN parallelism ceiling | `min(#items without a ready plan/charter, plan_cap)`; `plan_cap` = 4 is a **scheduling choice of this contract**, not a host setting (the host exposes no such key); always bounded by what the host actually runs at once, and only the write of the common status is serialized |
| Lane parallelism ceiling | `min(#groups, cap)`; `cap` = 4 is a **scheduling choice of this contract**, not a host setting; bounded by the host's observed concurrency **and by the declared host budget** (memory, measurement locks, container capacity) — a declared budget that cannot carry four lanes lowers `cap` and is recorded, not discovered later as timeouts |
| Worktree directory | `<repo>-worktrees/<collection-id>/<group>` (not created with a single group) |
| Merge | with `>=2` groups wait for **all** lanes to be terminal, then `git merge --no-ff` of **the `done` groups only** sequentially (not needed with one group); `incomplete` is not merged |
| One group | work in the current worktree/branch; worktrees, group/task branches and the merge are not created; `incomplete` leaves the commits already made in the current branch |
| Autocommit/merge right | given by a project overlay or an explicit user request; the skill itself grants no right; `>=2` groups without the right — a preflight blocker before the allocation; one group may go in the current tree without commits if allowed; push never |

The roles, the tiers and their model bindings are the host's and the common contract's: this
contract names roles only, carries no model id and adds no role.

## References

Load the **base `../pdca/SKILL.md` and this `SKILL.md` as separate reads on entry**,
not as one concatenated tool output (the host may truncate at 50 KiB / 2000 lines).
Load inherited form and base references when needed; a truncated contract
must never be treated as complete:

- `../pdca/SKILL.md` — the **required common cycle contract** inherited here. Load with
  this skill; on shared rules the base is authoritative, including role boundaries,
  acceptance, verification, counters, approval, escalation, evidence and recovery.
- `../pdca-incremental/SKILL.md` — a campaign item: invariants, charter and status file, bootstrap,
  the step boundary, acceptance, the stop rules.
- `../pdca-coder/SKILL.md`, `../pdca-dotnet/SKILL.md` — the overlays applied to the relevant work.
- `../pdca/references/plan.md` — base planner-only phase detail; the driver supplies
  its exact absolute path, never loads or forwards it.
- `../pdca/references/check.md` — loaded by CHECK for the base verdict/evidence contract.
- `../pdca/references/act.md` — loaded by `pdca-executor` for cycle records
  and status updates; batch projections remain in §Collection status record.
