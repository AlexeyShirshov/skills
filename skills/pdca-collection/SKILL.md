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

## Inheritance: the base contract is the single source of shared rules

The **common cycle contract** in `../pdca/SKILL.md` governs each item's cycle (including
incremental campaign steps), integration verification, corrective cycles, and the applicable
shared requirements: original task and acceptance, roles and permissions, control modes,
PLAN/DO/CHECK/ACT, counters and recurrence, escalation, evidence, approval, recovery,
effort and safety. **These rules are inherited, not copied or replaced here.** On a shared
rule, the base governs. This file adds **only the collection layer**: readiness, dependencies,
group scheduling, lanes, integration and collection-specific status/outcome projection.

**Loading.** The base entry PLAN selects Collection and continues here. On a direct load
(the user explicitly named `pdca-collection`), load the base common cycle rules **with this
file** and skip the entry classification: Collection is already a constraint, not a second
decision. For PLAN dispatch, the planner's `plan_reference_path` is derived from the
**base** `pdca/SKILL.md` directory; `references/plan.md` is read by `pdca-planner`
only. CHECK and status writers load the base phase references under their own contracts.
For a `campaign` item, also load `../pdca-incremental/SKILL.md`, which inherits
the same base contract for each step.

**Scope of inheritance.** Collection is a container, not an additional ordinary cycle:
it has no parent `N`, `r` or `n/3` attempt counter. These belong to each actual item
cycle or corrective cycle; the collection status tracks items, groups, integration
and their outcome links. An integration CHECK is a check **of the integrated snapshot**,
not proof that every original item goal was achieved. Full collection completion
requires each item's own accepted whole-goal CHECK and the integration CHECK.

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

The base §The user's task and its criteria applies **per item**: every handoff preserves
the original goal and any user-supplied acceptance criteria verbatim. Scheduling metadata
is not an alternative goal or an acceptance requirement.

Each item's **first PLAN** is delegated to `pdca-planner`. It classifies the item's form under the
same definitions as the base entry: **Bounded Execution** (`cycle`) when the method and scope are
known and bounded, or **Incremental Execution** (`campaign`) when the method, volume or next
actions genuinely require learning. It also selects the applicable specialized skill for a bounded
coding item: `pdca-coder` for general programming or **only `pdca-dotnet`** for .NET; non-coding
work requires none. No collection-driver preclassification or second PLAN is inserted. The
planner requests missing facts through the driver, who calls `pdca-scout` and returns the findings
to the **same pending PLAN**; a bounded choice probe is not a new cycle.

- `cycle` — one complete PLAN → DO → CHECK → ACT for the item's entire goal. Store its saved plan,
  form, selected specialized skill, revision and approval pointer; resume that same PLAN at DO
  after the barrier, unless the planner finds a substantive contract defect.
- `campaign` — one incremental invocation for the item's entire goal, with a preparation charter,
  runtime record and successive complete cycles. The campaign has **no item-level step overlay**:
  each concrete step's applicable specialized skill is selected for that step. Preparation does not
  create or decide future steps. The same designated item driver retains state, history and
  recovery across those steps.

An item cannot be a nested collection; there is no campaign inside a campaign or collection
inside a collection. The collection driver owns the batch schedule and integration, while the
item driver owns its own cycle/campaign progression. `pdca-executor` is the physical writer of
both records. No separate `cycle-control`, `campaign-control` or `collection owner` role exists.

**Acceptance boundary.** Each item's `done` requires its own accepted whole-goal CHECK and ACT,
not merely a ready plan, accepted increment or passing test. The collection's CHECK is additional:
it verifies the actual integrated result and never supplies missing acceptance for an item.

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

4. **Clustering after the barrier.** `pdca-planner` examines the available dependency
   requirements, estimated conflict surfaces, their uncertainty and host resource budget,
   and decides the DAG, ordering and independent groups. Actual implementation choices
   remain DO's. Known overlapping or **unresolved** write/conflict surfaces do not execute
   in concurrent lanes; a conservative single lane is valid. The schedule and PLAN revision
   vector are persisted before allocation. Prefer independent lanes when the known
   constraints support them, without fabricating independence; a schedule revision after
   new facts requires the recorded planner decision and applicable approval
   (`references/lane.md` §Stale plan and schedule revision).

5. **Durable tracking.** The collection status file (`references/status.md`) is the only
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

**What the barrier does not have.** Not needed: an item-level contract/overlay for `campaign`,
baseline evidence, a `running` runtime record, the campaign status file, the plans of future steps,
their contracts and the number of steps. An item without a meaningful plan or charter stays a gap
and does not get a `ready` placeholder. Before the barrier not a single lane is allocated; early DO
is forbidden for both forms. Before the barrier the executor's **preparation writes** are allowed
(the plan, `plan_state`, the charter, `preparation_ref`, links, the collection status); substantive
bootstrap and DO of an item before the barrier are forbidden. The charter's content, the baseline
bootstrap and the change-producing DO are defined once in `../pdca-incremental/SKILL.md`
(§Campaign invariants, §Campaign cycle, subsection 0. Bootstrap).

**Readiness ≠ completion.** `preparation_state=ready` without a runtime record is `barrier-ready`,
not `started`: the item stays `pending` and never `done`. The only success of a campaign item is an
accepted `met`; the barrier does not require what is created later.

If there is **one group** — keep the collection form and use a single lane. **No worktree and no group branch
are created**: work in the **current** worktree on the current branch, the commits (in autocommit
mode) go straight into it, `merge --no-ff` is not needed — there is nothing to merge; the merge
barrier (§D.3), the group/task branches and the merge itself **do not apply**. On `incomplete` of
such a group the commits already made **stay** in the current branch (no automatic rollback), and
the uncommitted changes of the failed item are preserved as a patch; only the paths of that item are
rolled back (`references/lane.md` §Failure). A one-item collection stays a collection; an empty input → report that there is nothing to do.

### D — infrastructure, tracking, merge

The lanes (worktrees, group/task branches, runners) are allocated **only** after the ALL-barrier and
the persistent binding of the schedule (§P.3–§P.4). Before that step they do not exist.

1. Through `pdca-executor`: one worktree per group
   `<repo>-worktrees/<collection-id>/<group>` and the branch `collection/<id>/group-<g>`.
   **If there is one group** — no worktree and no branches (`group-<g>`, `task-<g>-<k>`) are
   created: work in the current worktree on the current branch, the commits go there too; instead of
   `merge --no-ff` — ordinary work in place (there is nothing to merge).
2. In autonomous mode, available `pdca-orchestrator` group runners are started in parallel
   (one per group, up to `cap`); each may be the **designated item driver** and keeps a campaign's
   driver across all its steps (§Items and execution ownership, `references/lane.md`). In normal
   mode the primary itself drives the cycles/steps and obtains approval; it does not spawn a
   `pdca-orchestrator` as their driver. Actual lane concurrency is bounded by host capability.
   With one group there is one lane in the current worktree.
3. **Merge barrier**: with `>=2` groups the merge starts only when **all** lanes are terminal
   (`done` | `incomplete` with an explicit outcome) — readiness = terminality, **not** success. Then
   `pdca-executor` sequentially performs `git merge --no-ff` **only for the `done` groups** (the
   message starts with `#<n>` for an issue item); a successfully integrated group moves `done` →
   `merged`. **An `incomplete` group is never merged**, even if before the failure it has successful
   items and commits: its tip does not enter the integration, the results are preserved (§A,
   `references/lane.md` §Failure). **A running lane is not merged early.** With **one** group no
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
   `references/status.md`; running the lane: `references/lane.md`.

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

A campaign item's outcome is routed to its item status by `references/status.md` §Routing campaign
outcomes; campaign acceptance is not the common `C` and does not replace it.

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

The host requirements, role table and resource-blocker rules are inherited from
`../pdca/SKILL.md` §Roles and host requirements; this section adds only
collection-specific coordination and preflight.

When an autonomous `pdca-orchestrator` is absent or cannot delegate, use the **flat cheap primary**
as driver with `Notice:` and a durable reason, if the host permits it. It drives one current item
per lane and delegates PLAN/DO/CHECK to their required roles; a campaign still has one designated
driver for all steps. Independent groups may be processed concurrently up to `cap` only if the
host permits that concurrency; otherwise they are sequential. Normal mode already uses the
primary driver and must not treat the lack of orchestrator delegation as a reason to skip approval.
The fallback never promotes a driver into PLAN, CHECK, execution or expert-review authority.

Missing mandatory roles or forbidden fallbacks follow the base resource-blocker rules;
collection preparation, barrier and handoffs remain unchanged.

**Capability preflight.** Before the lane allocation and before the start of a campaign in a lane
the observable capability of the host is checked: the availability of the mandatory roles and
contracts, of the nested delegation to the runner, of `pdca-orchestrator` as a subagent and of the
`escalate → scout` edge. The check does not perform dummy substantive work: no trial edits, trial
items or fake steps. The exact numeric value of a host setting is not invented. The installed runner
is compared against the canonical asset and checked against the applicable permissions: the observed
case was an installed copy without `pdca-scout` delegation, which silently breaks the
`escalate → scout` edge.

An unavailable **mandatory role** — a resource stop of the run: another agent does not perform its
functions, the work stops recording what has already been accepted; an unavailable **contract** —
fail closed without substituting a "similar" one; **late discovery** — a safe pause before the
dependent action, not a weakening of the gate.

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
Load the other referenced files **when their phase starts**; a truncated contract
must never be treated as complete:

- `../pdca/SKILL.md` — the **required common cycle contract** inherited here. Load with
  this skill; on shared rules the base is authoritative, including role boundaries,
  acceptance, verification, counters, approval, escalation, evidence and recovery.
- `../pdca-incremental/SKILL.md` — a campaign item: invariants, charter and status file, bootstrap,
  the step boundary, acceptance, the stop rules.
- `../pdca-coder/SKILL.md`, `../pdca-dotnet/SKILL.md` — the overlays applied to the relevant work.
- `references/lane.md` — lane work stream, queue, designated item driver and campaign continuity, lane pause, stale plan
  and schedule revision, surface reservation, git model, failure semantics.
- `references/status.md` — the collection status file, its invariants and the routing of campaign
  outcomes to item status.
- `../pdca/references/plan.md` — base planner-only phase detail; the driver supplies
  its exact absolute path, never loads or forwards it.
- `../pdca/references/check.md` — loaded by CHECK for the base verdict/evidence contract.
- `../pdca/references/act.md` — loaded by `pdca-executor` for cycle records
  and status updates; batch projections remain in `references/status.md`.
