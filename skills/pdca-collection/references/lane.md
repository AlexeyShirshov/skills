# Lane: work stream, schedule revision and git model

Reference for the D phase and for a running lane. The barrier, the clustering and the collection
phases stay in `../SKILL.md`; collection gates and approval mechanics stay in `../SKILL.md` and
`common-contract.md`; campaign steps inherit the base `../../pdca/SKILL.md`.

## One lane = one group

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
3. autocommit after the item, **only in an allowed autocommit mode** (`../SKILL.md` §Scope and entry) —
   otherwise the next one does not branch from a committed result. Commit **only the files of the
   item** (`git add <paths>`), not `git add -A`: otherwise alien/artefact files are picked up.

`pdca-orchestrator` **makes no decisions** — it only routes the plan: it does not decide that an
item is impossible/not ready/independent, does not choose the scope and does not judge the result;
any question goes to `pdca-planner`, not to the user. The status `incomplete` is a consequence of a
failure or of an impossibility by the contract (§Failure), not a judgement of the lane.

## The queue and the per-item continuation

The source of truth of the queue is the collection status file (`status.md`): the runner re-reads it
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
  group is stopped"** and are **not executed**; the group is **not merged** (`../SKILL.md` §D.3).
- The commits of the group already made and the patch of the failed item are **preserved**
  (§Failure, §Git model); **other groups continue** their work.
- The lane summary is `done` | `incomplete` (per group); the status `blocked` does not exist for
  items/groups — `blocked` remains only a state of the parent verification.
- With `>=2` groups the result of a `done` group is the tip of its branch
  `collection/<id>/group-<g>`, ff-advanced to the last completed item; with one group it is the
  current branch.
- With one group no group/task branches are created: the commits (in the allowed mode) go to the
  current branch; `incomplete` leaves the commits already made without an automatic rollback, the
  uncommitted changes are preserved as a patch and rolled back only along the failed item's paths.
- The lane returns a compact summary of ≤8 lines without code/diffs/logs.

## A campaign item in a lane (designated item driver)

An item with the form `campaign` has **one designated driver throughout its steps** — the
primary in normal mode or the authorized cheap `pdca-orchestrator` in autonomous mode, with the
permitted flat-primary fallback (`../SKILL.md` §Items and execution ownership,
`../../pdca/SKILL.md` §Control modes). It holds the campaign state/status, the shared counters, the accumulated knowledge and the
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

The step semantics — the covered content of one step, the increment unit, the accepted negative
candidate as knowledge, the absence of a forced second increment, the whole-goal final check and
the claims veto — are the incremental contract's (`../../pdca-incremental/SKILL.md` §Campaign
invariants, §Campaign cycle, §Step boundary) plus the base gates; the collection adds neither a
counter nor a gate.

## Lane pause

A lane pause is **derived** from `disposition=paused` of the current item and is not stored as a
separate authoritative field of the lane. The item status stays the existing `in-progress`: a pause
is not a new status value, and no new item/group statuses are introduced. A paused lane does not go
on to the next dependent item of its group; the other groups continue.

## Stale plan and schedule revision

Before starting DO the lane checks that the saved PLAN is applicable to the actual state (are the
predecessors' outputs available, have the premises/assumptions changed). This is a narrow
applicability check, not a mandatory repeated PLAN and not the driver deciding instead of
`pdca-planner`.

- **The premises are unmet** → control returns to the **own PLAN** of this item: `pdca-planner`
  decides by the base revision rules (`r`/`n`, `../../pdca/SKILL.md` §State machine and counters);
  the counters and the identity of the item are preserved (`N` is not reset, no cycle "from
  scratch").
- **A change before the lanes start.** If the footprints/dependencies refined from the PLAN change
  the picture, the collection `pdca-planner` may **rebuild the schedule** (DAG/groups/order), and
  the barrier and the revision binding are updated and persisted. This is the only allowed revision
  window.
- **After the lanes start** automatic `rerun`/`remerge`/`recluster`/`reset`/`revert` are forbidden
  (`../SKILL.md` §C). A change incompatible with the approved groups (footprint overlap, a broken
  order) **stops** the continuation pending an explicit decision of `pdca-planner`/
  `pdca-escalate`; a silent old DAG and an automatic regrouping are inadmissible. Compatible local
  revisions may continue only with evidence from `pdca-planner` and a persisted updated revision
  binding; the driver itself does not declare compatibility.
- **A new campaign or a new item after the barrier.** An item or campaign added after the barrier
  does not mutate the DAG silently: it is an **explicit collection replan/reapprove**
  (`pdca-planner`, in normal mode — the user) taking into account the already started lanes and the
  stop/scope constraints (`../SKILL.md` §C). The old identities, statuses and evidence are
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

## Git model

Example (the instances `group-A`/`task-A-1` are `group-<g>`/`task-<g>-<k>`):

```text
current-branch
├─ merge --no-ff collection/<id>/group-A   (worktree A: task-A-1 → task-A-2 → task-A-3)
└─ merge --no-ff collection/<id>/group-B   (worktree B: task-B-1 → task-B-2)
```

- With `>=2` groups: 1 worktree per group; the group branch `collection/<id>/group-<g>` is
  ff-advanced to the tip of each completed item and at the end equals the tip of the last one.
- **One group**: no isolation is needed — neither a worktree nor group/task branches; the commits
  go straight into the current branch, `merge --no-ff` is not performed (`../SKILL.md` §P/§D).
- With `>=2` groups, inside a group — a chain of task branches `collection/<id>/task-<g>-<k>`; the
  next one branches from the tip of the previous one. With one group there are no task branches.
- With `>=2` groups the group and task branches are **siblings**, not nested into each other: git
  does not allow a ref that is a prefix of another ref.
- Integration — with `>=2` groups **after the terminality of all lanes**: `git merge --no-ff`
  **only for `done` groups**, one at a time, sequentially (`../SKILL.md` §D.3); a successfully
  integrated group moves `done` → `merged`. An `incomplete` group is never merged, even when
  successful commits exist; its refs/commits and the patch are preserved.
- `tip` — the last commit of the group branch (with one group — the current branch); for an
  `incomplete` group it is preserved as evidence but does not enter the integration.
- Merge conflict → `git merge --abort`; `pdca-escalate` (strong) only returns a decision (it does
  not edit itself and does not run `pdca-executor`), and the repeated `git merge --no-ff` of the
  unmerged tip is performed by `pdca-executor` on the runner's dispatch; previously
  integrated tips are not touched; gate `C` is not passed until all selected `done` groups are
  integrated.
- Push — never.
- **The external commit/branch lifecycle of an item belongs to the collection** and follows the
  layout above — the collection makes the outer completion commit of a completed item.
- **`Commit policy: none`** of a campaign or a step means the absence of intermediate step commits;
  it does not forbid the collection's external outer completion commit.
- An explicit no-commit restriction of the user conflicting with the git model of `>=2` groups is a
  **preflight blocker before the worktree/lane allocation**, not a silent override of the model and
  not a patch fallback without an explicit decision. For one group git integration is not required
  (`../SKILL.md` §Scope and entry). The completion of a campaign and the finalization of the outer item are
  different events.

## Failure (semantics)

| Event | Behavior |
|---|---|
| An item does not pass CHECK | **do not stop first:** control → `pdca-planner` (PLAN); it may fix it (loop-back to DO, the usual `r`/`n`) or **finally** close the item as `incomplete` (then `pdca-executor` saves the current changes as a patch, returns **only its paths** to the last green tip, writes the reason + the patch path into the status). A final `incomplete` **stops the whole group**: the following `pending` items → `incomplete` with the reason **"the group is stopped"**, they are not executed; the group is not merged; the other groups continue |
| The group finished partially (`incomplete`) | its tip is **not merged** even with successful items/commits; the results are preserved — refs/branches/commits + the patch of the failed item (in autocommit mode) or the group's aggregate patch by the item paths (if a commit is unavailable); the report says `incomplete` |
| A commit/merge is unavailable, forbidden or withdrawn | **`>=2` groups:** a known incompatibility — a preflight blocker before the allocation; a withdrawal during a lane — a safe stop preserving the commits/refs and a patch of the uncommitted changes, without a further branch chain and merge; `incomplete` only by an explicit terminal outcome. **One group:** work in the current tree without commits is admissible if allowed; git integration is not required. A deny is not bypassed; a normal multi-group no-commit mode is not invented |
| A merge conflict of a group | `git merge --abort` → **`pdca-escalate`** (strong) decides (resolve/reorder/`incomplete`), but does not execute and does not run `pdca-executor`; the runner returns to MERGE and dispatches `pdca-executor` for a repeated `git merge --no-ff` of the unmerged tip; the `incomplete` decision excludes the group tip fully and integrates the remaining `done` groups; already merged ones are not touched; gate `C` is not passed until all selected `done` groups are integrated |
| A regression of the mandatory checks/artefacts of an item | gate `C` is not passed; → `../SKILL.md` §C: an aggregate of the mandatory reports → the verdict of `pdca-check` (medium) → a standard corrective cycle, a re-gather of the missing report or a `blocked` state; the collection is not closed |
| A missing/unreliable mandatory report or an environment failure | **not** a defect: no code edits; the condition of the common verification → **`blocked`**; the source transcript/evidence are preserved; after the environment is restored/the evidence obtained — a repeat of **the whole** common `C`; no unbounded auto-polling/retries |
| A repeat of the same defect after one fix | `pdca-escalate` **before the second fix** (even with a local CHECK=PASS of the corrective cycle and a new corrective id); a change of the item id/session/status file **does not** reset `r`/`n`/the defect history (`../../pdca/SKILL.md` §Escalation (`pdca-escalate`)) |
| An exhausted revision / a STOP without a revised plan | there is no 4th implementation CHECK even after `pdca-escalate`; continuation only by a genuinely revised plan `r+1`; otherwise the unresolved status/evidence/integrated work are preserved, there is no success/cleanup, the parent collection is **`unverified`**, the source items — their **previous** statuses |
| The lane returned "no result" | the group = `incomplete`, no merge is done, refs/patch are preserved |
