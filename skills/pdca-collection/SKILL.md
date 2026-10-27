---
name: pdca-collection
description: "PDCA collection: the batch contract of the PDCA family — a batch of independent goals whose items the same configured planner classifies into an ordinary cycle or an incremental campaign, then clustered into parallel groups (worktree per group, `git merge --no-ff` of the `done` groups only). Loaded by the base PLAN when the collection form is decided; a single-lane collection is the normal case."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# A batch of independent goals as PDCA

## Role

This contract is **self-contained**. Invoked directly, this file plus
`references/common-contract.md` is a complete contract and **loading the base `../pdca/SKILL.md`
first is not required**. When entered from the family router, its single PLAN already decided the
**collection** form — a list of **independent goals**, not an internal split of one goal — and
passed the plan by reference. Either way this skill **does not classify the batch** and has no
routing table of its own: the form of the whole batch is already fixed.

Collection planning then classifies **each item** by the same rules as the common contract (§Forms) —
ordinary cycle or incremental campaign — with the **same configured `pdca-planner`**; that is the
per-item decision that starts each item's own PLAN, not a second PLAN of the batch. A batch may be
heterogeneous; a **single-lane collection is the normal case**, not a degradation. The collection
PLAN owns the batch: item ids, footprints, dependencies and the grouping decision.

**Naming.** An item's **form** is `cycle` | `campaign`; the **contract** is `pdca` plus the
**overlay** (`none` | `coder` | `coder+.NET`, applied to the chosen form, common contract §Forms). A
campaign item has **no item-level contract**: the contract/overlay belongs to each concrete **step**
and is decided by `pdca-planner` for that step; the campaign itself is governed by
`../pdca-incremental/SKILL.md`.

The common gates, counters, roles, approval mechanics, escalation, recovery, effort accounting and
generic operating constraints are in `references/common-contract.md` (a local copy, so this form
works without the base); the campaign's step semantics are the incremental contract's. This skill
adds only the batch level: the barrier, the clustering, the lanes, the merge decision and the
collection status file.

You (the collection owner) **do not edit files and do not run commands yourself**. The
infrastructure (worktrees, branches), `git merge --no-ff` and the mandatory checks of an item are
executed by `pdca-executor` on your command; you own the tracking, the gates and the merge decision.

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

## Ownership

- **Batch and lane ownership stays with the collection owner** (the cheap primary, or the cheap
  `pdca-orchestrator` it dispatches as the group runner): the schedule, the ALL-barrier, the lane
  queue, the merge decision and the collection status file.
- An item with the form **`cycle`** is executed by the same cheap dispatcher in **cycle-control**
  (common contract §Roles and tiers): it receives one already-planned cycle, executes it
  and returns the result; it does not advance the campaign, the queue or anything else.
- An item with the form **`campaign`** has its campaign state owned by **one designated existing
  cheap `pdca-orchestrator` in campaign-control** (common contract §Roles and tiers),
  designated when the schedule is bound: it holds the campaign record, the effort accounting and the
  recovery, and it is the only writer of that record. **No competing writers** — the collection
  owner never writes or advances a campaign; a pause and a stop are durable in the campaign record
  and in the item's `disposition`.

## Items: form, contract, overlay

A batch consists of **items** — the collection's tracked entries, each with a stable id. Every item
has a **form**, decided by the collection PLAN (`pdca-planner`) before any dispatch:

- `cycle` — one cycle of the chosen contract+overlay: one full PLAN → DO → CHECK → ACT; the item
  carries `plan_state`, the contract with its overlay and its pending approval ref;
- `campaign` — one incremental campaign with its own goal, charter (the immutable preparation
  document), runtime record and steps. The item carries **no** contract/overlay: they appear on a
  concrete step only.

The runner only reads the decided values and does not classify the item or pick a contract.
**Composition is not recursive:** a campaign step is only a family cycle; a campaign inside a
campaign, a collection inside a campaign and a collection inside a collection are not expressible.

**Step and lens semantics follow the form.** A `campaign` item follows the incremental contract —
one planner call per step boundary, an accepted negative candidate credited as knowledge, no forced
second increment, a whole-goal final check before `done`, and the claims veto
(`../pdca-incremental/SKILL.md` §Campaign cycle, §Stop; common contract §Claims and veto). A `cycle` item follows the common gates as they are. Neither is restated
here.

## Collection (P / D / C / A)

### P — per-item PLANs, the barrier, clustering

The order is strict: **each item's own PLAN → ALL-barrier → DAG and groups.** A preliminary
analysis of the descriptions (`pdca-scout`) is by itself **not** a PLAN and does not replace it.

1. **Input and bootstrap.** The goal list in any form is given by the user. Give every item a
   stable id, the source brief and its **form**; the collection PLAN decides the form of every item
   **before** the per-form dispatch, and the primary/runner only passes the ready value. For a
   `cycle` item the contract and overlay are part of that decision; a `campaign` item has none
   (§Items). Pass the common item list to each item as context, as a source of dependency
   requirements — but do **not** compute the DAG, the order or the groups in advance.
2. **Each item's own PLAN / campaign preparation.** Through `pdca-orchestrator` at the
   **COLLECTION TASK PLAN** entry, run the route matching the item's form (the dispatcher neither
   derives nor classifies it):
   - `cycle` — the item's own genuine PLAN of its contract+overlay: `pdca-scout` gathers facts,
     `pdca-planner` decides, `pdca-executor` persists the status. The PLAN ends at the PLAN→DO
     boundary (durable checkpoint) and **hands control to the collection parent** — it is not DO,
     not an error and not the completion of the item. The handoff carries the planned write
     footprint and its uncertainty, the requirements on the predecessors' results,
     assumptions/prerequisites and refs, and — in normal mode — the pending approval ref pointer (a
     checkpoint for the parent, which owns obtaining the approval). The item's code is **not**
     written at this step.
   - `campaign` — the **preparation route of the incremental contract**
     (`../pdca-incremental/SKILL.md` §Campaign cycle, subsection 0. Bootstrap): `pdca-scout`
     gathers facts, `pdca-planner` decides, `pdca-executor` writes the immutable charter at
     `.pdca/<collection-id>/items/<item-id>/preparation.md`, `preparation_state` (`pending` |
     `ready`; `ready` is not `met` and is not completion) and the single `preparation_ref`; a
     `preparation_handoff` is returned. The charter's content, its mandatory items and their
     renegotiation rules are the incremental contract's (§Campaign invariants, §Campaign
     status) — not restated here. The baseline, the runtime record, the plans of future steps, their
     number and their contracts are **not** created or required now; the step's contract/overlay is
     chosen by `pdca-planner` at that step.

   **The items' PLANs are independent and run in parallel.** One item's plan does not require
   another item's artefacts: the dependency is recorded as a requirement on the predecessor's
   results in the handoff metadata, not as waiting for someone else's plan.

   - **Dispatching.** `COLLECTION TASK PLAN` goes out immediately for all items without a ready
     plan/charter (§P.3, §Barrier by item forms), up to `plan_cap` (§Parameters); handoffs are
     accepted as they become ready, not in the declared order. Several calls go out **as one block**,
     not one at a time — sending the next only after the previous returns is serialization even if
     the text says "in parallel". Parallelism is bounded by the host: `plan_cap` is an upper bound,
     not a guarantee.
   - **Status writing.** The primary appends the rows after each handoff returns, not between
     sends. The write is serialized, not delegated to every PLAN: the semantics are set by the
     primary/`pdca-planner`, the physical write is done by `pdca-executor` on an explicit dispatch
     (`references/status.md`), so item rows, handoff/`preparation_ref` and the decisions log are
     entered without a race. Parallel planning changes the cost of the phase, not the rows.
   - **Barrier.** §P.3 is not weakened by this: it is about the readiness of **all** plans, not
     about their sequence.
   - **Schedule.** A parallel PLAN **does not fix the schedule**: the groups and the order are
     determined only after the barrier (§P.4), so a sequential chain of items in one group is a
     normal outcome, not a conflict with parallel planning.
   - **Code overlap** is resolved there too: the footprint reservation is a **claim** for
     clustering, not a lock. The PLAN **declares** the write footprint and its uncertainty, but
     holds no lock and does not prevent other plans from being assembled in parallel. Overlapping
     footprints do not forbid parallel planning — they forbid parallel **lanes**: such items land in
     one group and go through it sequentially (branch after branch).
   - **A dependency on a predecessor's result** is recorded in the handoff as a requirement on the
     results; the lane checks applicability before DO and, when the premises are unmet, returns the
     item to its own PLAN (`references/lane.md` §Stale plan and schedule revision).

   **A re-entry after a terminal `incomplete`/STOP** does not re-run the failed criterion unchanged:
   the previous terminal cause is a mandatory input of the own PLAN, and `pdca-planner` either
   proves that the evidence is now obtainable or redefines the oracle; otherwise the item stays a
   gap (§P.3).

   **A collection is a batch, not a licence to skip plan hygiene.** The item's own PLAN validates
   its command contract before `plan_state=ready` (`../pdca/references/plan.md` §Plan command
   contract), names its verification choice and effort estimate/accounting, and — for an unproven mechanism — plans a bounded probe
   before the full acceptance contract. A plan whose decisive command cannot run is a gap at the
   barrier, not a lane surprise.
3. **ALL-barrier.** The DAG, the groups and the order are **not built** until the requirement of its
   form is met for **every** item (§Barrier by item forms). An item's readiness by its form is
   **not** a user approval and **not** a successful completion; readiness alone never triggers lane
   allocation or an early DO — in normal mode the lane's DO still waits for the recorded approval
   against the item's pending approval ref (§Approval barrier). An item for which a meaningful plan
   is impossible (not enough data/decisions) stays a gap and is **not** marked with a `ready`
   placeholder: the barrier is not passed, early DO is forbidden. The barrier constrains the
   **start** of the DAG/groups/lanes, not the order of the PLANs: it does not require assembling the
   plans sequentially and does not forbid the parallel dispatching of §P.2.
4. **Clustering (after the barrier).** `pdca-planner` validates the contradictions and the
   uncertainty from the handoff metadata, then builds the DAG and cuts it into groups: a group = a
   connected component/line by dependencies and shared files; the groups' footprints do not overlap;
   inside a group the items are ordered topologically. The result is bound to the **PLAN revision
   vector** (which plans exactly were used) and recorded in the collection status file
   (`references/status.md`). Before the persistent binding of the schedule there is no lane
   allocation.

   **Width is an objective, not a by-product.** Minimise the largest serialized group: a component
   whose items touch disjoint file families is cut into separate groups even when one lane could
   carry them in order. A schedule that leaves most items in one chain has degraded to a single lane
   by construction and must be justified in the status file, not accepted silently. The schedule
   also declares the **host budget** — available memory, measurement locks, container capacity — and
   `cap` is derived from it (§Parameters), never from the number of groups. After the first wave the
   schedule is **re-examined**: a group that has lost its last writer releases waiting items into a
   new lane through the persisted revision binding; this is a schedule revision, not an automatic
   recluster (`references/lane.md`).

   **Parallelism is not an entry condition.** If the barrier leaves one group, the host allows only
   one lane (`cap = 1`), or the items share a measurement resource, that is a normal degradation to
   a single lane (§D, `references/lane.md`), not a reason to change the contract. Do not create
   fake groups and do not call the run parallel.
5. **The only progress mirror is the collection status file.** There is no separate sidebar todo:
   the host may not provide a todo tool, and a second mirror only produces divergence. You (the
   primary) **define the semantics** of the write in the same tick as the event: a group/item
   transition, a group stop, a merge, a corrective cycle, an escalation; **the physical write is
   performed by `pdca-executor`** on an explicit dispatch — the primary does not write files itself.
   Before dispatching, check the status file; after compaction the state is restored from it, not
   from memory. Groups, items and their statuses live in the tables of `references/status.md` — a
   separate list of items is not needed; a runner writes the status file of its own item, not the
   sidebar.

#### Barrier by item forms

- **`cycle`** — a genuine PLAN of this cycle: `plan_state=ready`, the plan revision, the footprint
  reservation and its uncertainty, the requirements on the predecessors' results,
  assumptions/prerequisites, refs. This is the same plan that is later executed;
  `plan_state=ready` is the readiness of the plan, not an approval and not completion.
- **`campaign`** — the approved immutable/revisioned **charter** (preparation document) at
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

If there is **one group** — do not fail: degrade to a single lane. **No worktree and no group branch
are created**: work in the **current** worktree on the current branch, the commits (in autocommit
mode) go straight into it, `merge --no-ff` is not needed — there is nothing to merge; the merge
barrier (§D.3), the group/task branches and the merge itself **do not apply**. On `incomplete` of
such a group the commits already made **stay** in the current branch (no automatic rollback), and
the uncommitted changes of the failed item are preserved as a patch; only the paths of that item are
rolled back (`references/lane.md` §Failure). If there are no independent items at all — an ordinary
pdca cycle; an empty input → report that there is nothing to do.

### D — infrastructure, tracking, merge

The lanes (worktrees, group/task branches, runners) are allocated **only** after the ALL-barrier and
the persistent binding of the schedule (§P.3–§P.4). Before that step they do not exist.

1. Through `pdca-executor`: one worktree per group
   `<repo>-worktrees/<collection-id>/<group>` and the branch `collection/<id>/group-<g>`.
   **If there is one group** — no worktree and no branches (`group-<g>`, `task-<g>-<k>`) are
   created: work in the current worktree on the current branch, the commits go there too; instead of
   `merge --no-ff` — ordinary work in place (there is nothing to merge).
2. The `pdca-orchestrator` instances are started in parallel (one subagent per group; a campaign
   item is led inline in its lane by that item's designated controller, §Ownership and
   `references/lane.md`), no more than `cap` at a time. With one group — one runner in the current
   worktree.
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

### C — verification (the standard CHECK)

The common verification of a collection is the **standard CHECK** of the common contract (two ticks:
gather cheap → verdict `pdca-check` medium; common contract §One loop,
`../pdca/references/check.md`), plus the overlay deltas of the contract applied to the checked work
(`../pdca-coder/SKILL.md` §Code-specific check deltas; for .NET — `../pdca-dotnet/SKILL.md`
§.NET check deltas), and **not** a separate bespoke stage of the collection. When all lanes are
stopped, in the main tree: all **`done`** groups are integrated (**became `merged`**, including a
repeated merge after a conflict, §D.3), **`incomplete` groups are not merged**, and there is **no
unfinished merge state**.

The input of the common `C` is the **actual group statuses** plus the separate **integration note**
(`skipped` + reason); only the **selected `done` groups** are integrated and moved to `merged`,
`incomplete` stays `incomplete` and keeps its evidence. `PASS` of the parent `C` **may coexist** with
`incomplete` groups: the **completion** report (how many items/groups were carried through) and the
**verification verdict** of the integrated tree are **separate** fields. Even with no selected `done`
group or with an `incomplete` current group the standard `C` still runs on the integrated tree; the
source items are **not** marked `done` retroactively. Counters/escalation are the common ones (common contract
§Counters and history, §Escalation and guardrails), without a collection counter.

The runner **always** — even when all checks are green — gathers through the existing
`pdca-executor`/`pdca-scout` the mandatory reports about the raw measurements (command, exit code,
log) and the observation-lens reports, and passes the **aggregate** to `pdca-check` (medium). The
raw command measurements **never** decide gate PASS by themselves: the verdict of `C`
(`pass`/`fail` + findings) is issued by `pdca-check`; `pdca-check` does not run hands and does not
edit code. The claims and the veto apply unchanged (common contract §Claims and veto).

- **PASS** → the common ACT of the collection is allowed (§A).
- **FAIL · a real defect** → the runner opens a **standard corrective cycle** (its form, contract
  and overlay decided by `pdca-planner` by the same rules; PLAN → DO → CHECK → ACT) on the **current
  integrated tree/branch** with **its own linked status file**; its ACT returns control to the
  **full** parent CHECK — **all** mandatory common gates are re-run, not only the failed test. A
  cheap verdict without a corrective cycle is not allowed.
- **No mandatory report / an unreliable report / an environment failure** → a standard
  **re-gather** (gather the missing report again); this is **not** a defect and **not** a reason to
  edit code. The state of the common verification may stay `blocked`/awaiting-reports in the
  existing status, but there is **no separate bespoke protocol** (a third verdict, a separate
  stage/node).

No automatic rerun/remerge/recluster/reset/revert and no new collection worktrees/branch chains;
corrective cycles are **separate records/links, not additional lanes**. While `C` is red — **no**
success/cleanup, the results are preserved.

The revision/escalation rules inside a corrective cycle are the **common `r`/`n/3`** (common contract
§Counters and history, §Escalation and guardrails): the same defect after one fix → `pdca-escalate` **before the
second fix** even with a local CHECK=PASS and a new corrective id; a change of the cycle
id/session/status file **does not** reset `r`/`n`/the defect history; an exhausted revision does
**not** get a 4th implementation CHECK even after `pdca-escalate` — continuation only through a
genuinely revised plan `r+1`. There is no separate collection attempt counter and no generalized
"three-failure rule of `C` at the collection level". On STOP without an acceptable revised plan the
unresolved status/evidence/integrated work are preserved; the parent collection stays
**`unverified`**, the source items — with their **previous** statuses; **the success of the
corrective cycle by itself does not mean the success of the collection**.

This is **not** mixed with the `incomplete` of an item inside a lane (`references/lane.md`
§Failure): that one concerns the failure of a single item of a group and the decision of
`pdca-planner` in its cycle, whereas the STOP of a corrective cycle is about a repeat of a defect of
the **common** `C` and obeys the common `r`/`n`.

### A — completion

ACT finalizes the collection outcome. **Only a PASS of the common `C`** allows the success
completion and cleanup; a `blocked`/`incomplete`/`STOP` outcome is finalized by the same ACT, with
the honest outcome recorded and **no success path**. Report (§Report); `pdca-executor` removes
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

The report format follows ACT (`../pdca/references/act.md` when available; the common contract §One loop otherwise): what was done, how it was verified, what
remains/blocked, the next step; in autonomous mode — without a message to the user. The completion
report and the verification verdict of the integrated tree stay separate fields (§C).

## Approval barrier (normal mode)

An item or step waiting for approval is `disposition=paused` with the status `in-progress`, and
**not** `done`/`incomplete`. The approval mechanics are stated once in `references/common-contract.md`
§Entry and control mode: the durable pending approval ref, the approval recorded against the same
ref, the applicability check on resume, the fresh approval after a real revision. The collection
adds only what the collection owns:

1. The runner returns a **checkpoint** to the parent (the collection primary) with the ref — the
   handoff carries it as its approval pointer — and does not ask the user itself and does not start
   DO. A brief, a summary or a chat message is not an approval.
2. The primary asks the user; an explicit approval is recorded against **the same** ref. The
   protocol is the same for `cycle` and `campaign`.
3. Resume continues **the same** cycle/step, and an unchanged saved plan is no exception;
   applicability without a matching record is an **approval-needed checkpoint**, not DO and not a
   fresh PLAN. A stale plan gets a genuine revision from `pdca-planner` and a **fresh** approval, and
   the old approval does not authorize it. A paused lane does not advance its group's dependent
   chain.
4. Autonomous mode does not invent an approval: an external/user approval remains a blocker or a
   STOP until it is obtained. A mismatching/missing approval record is a blocker, not a pass.

## Fallback

The host requirements, the role table and the resource-blocker rules are in
`references/common-contract.md`; this section keeps only the collection's own fallback.

If the harness forbids a subagent to delegate (no nested delegation), `pdca-orchestrator` cannot
orchestrate pdca. Trigger: the launch of `pdca-orchestrator` fails with a
delegation/subagent-unavailability error. Then — **one** flat-primary fallback: the primary itself
leads "in flight" **one current item per group** (launches to
`pdca-planner`/`pdca-executor`/`pdca-check`/`pdca-scout`), and on completion launches the next item
of the same group. **Independent groups keep the allowed parallelism**: up to `cap` groups at a time
if the host allows it; if the host does not provide concurrency — the same fallback leads the groups
sequentially. `cap` is an upper bound, not a guarantee. The fallback does not substitute roles:
another agent does not perform the functions of an unavailable mandatory role. In phase P the flat
primary likewise conducts the **COLLECTION TASK PLAN** of every item itself (by its form — the
cycle's own PLAN or the preparation of the campaign charter), observing the ALL-barrier, and
continues the saved PLAN in the lane with DO. The fallback marks itself with a `Notice:` line and a
durable reason and does not obtain the roles' rights.

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

Loaded **at the start of its phase**, not up front (the host truncates tool output at 50 KiB /
2000 lines, so a truncated contract would lose the tail — usually the CHECK/ACT/STOP rules):

- `references/common-contract.md` — the self-contained common contract: entry and control mode, the
  loop, roles and tiers, counters, claims and veto, evidence, escalation and guardrails. Load it with
  this file; the base `../pdca/SKILL.md` is optional deeper detail, not a prerequisite.
- `../pdca-incremental/SKILL.md` — a campaign item: invariants, charter and status file, bootstrap,
  the step boundary, acceptance, the stop rules.
- `../pdca-coder/SKILL.md`, `../pdca-dotnet/SKILL.md` — the overlays applied to the relevant work.
- `references/lane.md` — lane work stream, queue, campaign-control in a lane, lane pause, stale plan
  and schedule revision, surface reservation, git model, failure semantics.
- `references/status.md` — the collection status file, its invariants and the routing of campaign
  outcomes to item status.
- `../pdca/references/plan.md`, `../pdca/references/check.md`, `../pdca/references/act.md` — plan
  fields and command contract, the verdict content and the veto, the closing order and the
  status-file shape.
