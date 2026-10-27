# A batch of tasks: how `pdca-collection` coordinates several PDCA cycles

## 1. The problem: one cycle — one task

A PDCA cycle is built around one verifiable goal. That is the point: a single scope, a single
acceptance set, a single status record. But real work often arrives as a **list of independent goals**:
five issues for one milestone, three unrelated fixes before a release, four features that touch
different parts of a repository.

Running them one after another is safe but slow. Running them as one big cycle is wrong: the goals
share no acceptance criterion, a failure in one must not invalidate the others, and one status file
would blur which goal was actually verified. Splitting them into ad-hoc sessions loses the batch view:
what is prepared, what is running, what is merged and what is still unfinished.

`pdca-collection` is the batch form. It treats every item as a **separate, complete PDCA invocation**
and adds only the coordination: preparation, a barrier, dependency-aware groups, isolated lanes,
integration and one batch status record. The collection creates **no second cycle and no additional
attempt counter**.

## 2. What a collection is, and what it is not

A collection is:

- a set of **independent user-defined goals**, each with a stable id, its unchanged brief and any
  user-supplied criteria;
- a batch whose items may be ordinary `cycle` items or sequential `campaign` items;
- a coordinated run with a preparation barrier, a dependency DAG, groups, lanes and an integration
  CHECK.

A collection is not:

- an internal decomposition of one goal — that is DO's unit split inside one cycle;
- a way to bypass a blocked item by averaging it with successful ones;
- a new state machine, a new acceptance rule or a new attempt budget;
- a claim that an integration PASS completes unfinished source goals.

The base common cycle contract governs every item cycle, the integration CHECK and the corrective
cycles. On a shared rule the base wins. The collection adds batch coordination only.

## 3. Choosing and launching it

The base entry PLAN may select the collection form for a list of independent goals, or the user may
name `pdca-collection` explicitly. In the second case the form is a **constraint**: the collection does
not run a second classification to “confirm” it.

A direct load also loads the base common rules and skips the entry classification. A campaign item
additionally loads `pdca-incremental`; the planner's `plan_reference_path` always resolves from the
base `pdca` directory, never from the collection skill.

A collection may contain one item or one group. That is still a collection: the form is not downgraded,
but the one-group rules remove the infrastructure that has nothing to merge.

## 4. The vocabulary

| Term | Meaning |
|---|---|
| **Item preparation** | The pre-DO work for one goal: a persisted cycle PLAN (`plan_state=ready`) or a persisted campaign preparation charter (`preparation_state=ready` with a valid `preparation_ref`). No substantive item DO yet. |
| **Preparation barrier (ALL-barrier)** | Every item must be prepared before the collection builds its schedule, allocates lanes or starts any item DO. Readiness is not approval and not completion. |
| **Dependency DAG** | The acyclic order between items: `A → B` means B depends on A's result. File-write conflicts additionally constrain grouping. |
| **Group** | Items assigned to one sequential execution queue because of dependencies or a shared/uncertain write surface. |
| **Lane** | One execution stream running one group, in its order. With several groups, each lane gets an isolated Git worktree and group branch; with one group, the current worktree and branch. |
| **Integration** | Bringing the completed groups' results together. Multiple groups merge only `done` groups into the main tree; one group needs no merge. |
| **Batch status** | The durable collection-wide record in `.pdca/status/collection-<slug>.md`. |
| **Final verification** | The independent CHECK of the integrated result, in addition to each item's own acceptance CHECK. |

The **collection driver** coordinates the batch: status, preparation barrier, schedule, group
integration and the final CHECK/ACT. It does not plan implementations, choose tests, judge acceptance,
edit files or run commands. `pdca-planner` makes substantive PLAN decisions, `pdca-check` makes
independent CHECK decisions, and `pdca-executor` performs every write and execution.

Each item has its own **designated driver** and durable record. Collection coordination is separate
from the execution of the individual goals; two drivers never compete for an item's state.

**Modes.** In normal mode the primary drives the collection and its cycles/steps, obtains the user's
approval before each DO, and does not dispatch `pdca-orchestrator` to drive a cycle or step. In
autonomous mode the primary delegates coordination to `pdca-orchestrator` when permitted; an available
group runner may itself be the designated driver for its items and, for a campaign, for its successive
steps. A single campaign keeps **one driver across all steps**. A host that cannot delegate follows the
fallback rules without transferring PLAN or CHECK authority to a cheap driver.

## 5. P — per-item PLANs, the barrier, clustering

The order is strict: **each item's initial PLAN → ALL-barrier → DAG/groups → item DO**.

### 5.1. Input and first PLAN

The input is the user's list of independent goals, each with a stable id, its **unchanged** brief and
any supplied criteria. Each item goes to its own `pdca-planner` before a form is chosen.

The planner selects `cycle` or `campaign`, the specialized skill for a `cycle` item, and the acceptance
criteria when the user supplied none. It does **not** choose implementation actions, steps,
verification methods, evidence sources or commands. Only at the planner's request does the driver call
`pdca-scout` for missing facts. Other item briefs are dependency context, not a reason to build the DAG
yet.

### 5.2. Preparation to the PLAN/DO boundary

Through the item's designated driver, the **same initial PLAN** continues — not a new PLAN introduced
by the collection.

- **`cycle`**: `pdca-executor` records the completed result contract and `plan_state=ready`, then
  returns a `plan_handoff` at the PLAN → DO boundary. The plan includes the goal, preserved or derived
  criteria, constraints, assumptions, bounds, risks and stop conditions, but no mandated DO steps and no
  frozen CHECK method. The estimated conflict surface and prerequisite assumptions are recorded
  separately as scheduling metadata — not as prescribed implementation and not as an acceptance
  criterion.
- **`campaign`**: follow the incremental form's bootstrap. `pdca-executor` persists the preparation
  charter at `.pdca/<collection-id>/items/<item-id>/preparation.md`, with `preparation_state` and the
  authoritative `preparation_ref`, and returns a `preparation_handoff`. No baseline, runtime record,
  substantive DO, future step plan or step count is required at the barrier.

A PLAN-terminal `acceptance criteria cannot be determined` or a proven
`original task is infeasible under the stated constraints` goes to that item's ACT, without DO or
CHECK, and **cannot** be marked ready. A failed candidate or an unproven method alone does not establish
infeasibility, and no substitute goal is created. Re-entry after a terminal result preserves its cause
and history rather than rerunning the same failed criterion unchanged.

**Parallel preparation** is allowed up to `plan_cap` and observed host capacity, accepting handoffs as
they finish. Physical writes to the shared collection status are serialized through `pdca-executor`.
Independent planning does not need predecessor artefacts. Estimated write surfaces are **non-binding
claims** derived from known constraints; uncertain surfaces stay explicit and conservatively constrain
later lane parallelism. Planning never locks files or promises that DO will use a prescribed
implementation.

### 5.3. The ALL-barrier

The collection schedule and lanes are not allocated until **every** item has a genuine saved `cycle`
plan or `campaign` preparation charter. Readiness is neither user approval nor completion, and
normal-mode DO still requires recorded approval against the exact pending ref.

An undetermined or unreachable goal, or a missing preparation, is an explicit gap. Do not invent a
`ready` placeholder, bypass the barrier or start another item's DO early. Status updates and preparation
writes are permitted before the barrier; substantive bootstrap and DO are not.

**Barrier by item form.**

- **`cycle`** — a genuine PLAN of this cycle: `plan_state=ready`, the plan revision, the footprint
  reservation and its uncertainty, the requirements on predecessors' results, assumptions and
  prerequisites, and refs. This is the same plan that is later executed. `plan_state=ready` is the
  readiness of the plan, not an approval and not completion.
- **`campaign`** — the prepared immutable/revisioned charter at
  `.pdca/<collection-id>/items/<item-id>/preparation.md`, the readiness `preparation_state`
  (`pending` | `ready`) and the **single authoritative** `preparation_ref` of the form `<path>@r<k>`
  in the item record. `ready` is not `met` and is not the campaign's completion. `campaign_ref` is a
  pointer to the campaign's runtime record: it may be absent before the baseline bootstrap and is
  mandatory after it; it is neither a pointer to the charter nor a replacement for `preparation_ref`.

**Readiness is not completion.** `preparation_state=ready` without a runtime record is
`barrier-ready`, not `started`: the item stays `pending` and never `done`. The only success of a
campaign item is an accepted `met`; the barrier does not require what is created later.

### 5.4. Clustering after the barrier

`pdca-planner` builds the dependency DAG and groups from item dependencies, estimated write conflicts
and host capacity. Overlapping or uncertain write surfaces must run in one sequential lane; independent
groups may run in parallel. The schedule and PLAN revision vector are persisted before lanes are
allocated. Later changes need a planner decision and, where applicable, approval.

DO chooses implementation. A plan never prescribes it, and a scheduling claim never becomes a
criterion.

### 5.5. Durable tracking

The collection status file is the only batch progress mirror. The collection driver coordinates
updates, but `pdca-executor` writes each transition, handoff, group stop, merge, correction and
escalation **in the same turn**, without a competing sidebar list. On recovery the status is the source
of truth; item drivers maintain their own status files by the same one-writer rule.

## 6. D — infrastructure, tracking and merge

Lanes — worktrees, group/task branches and runners — exist only after the ALL-barrier and the
persistent binding of the schedule.

### 6.1. Worktrees and branches

With two or more groups, `pdca-executor` creates one worktree per group,
`<repo>-worktrees/<collection-id>/<group>`, and the branch `collection/<id>/group-<g>`. Group and task
branches are sibling refs, never name-prefixes of each other.

With **one group**, no worktree and no group/task branch are created: work happens in the current
worktree on the current branch, the commits (in an allowed autocommit mode) go straight into it,
`merge --no-ff` is not needed because there is nothing to merge, and the merge barrier does not apply.
If the group ends `incomplete`, the commits already made stay on the current branch (no automatic
rollback), the uncommitted changes of the failed item are preserved as a patch, and only that item's
paths are rolled back. A one-item collection stays a collection; an empty input means there is nothing
to do.

### 6.2. Autonomous runners

In autonomous mode, available `pdca-orchestrator` group runners are started in parallel, one per group,
up to the host's capacity. Each may be the **designated item driver** and keeps a campaign's driver
across all its steps. In normal mode the primary itself drives the cycles/steps and obtains approval;
it does not spawn a `pdca-orchestrator` as their driver. Actual lane concurrency is bounded by observed
host capability and the declared host budget. With one group there is one lane in the current worktree.

### 6.3. The merge barrier

With two or more groups, merging starts only when **all lanes are terminal** (`done` | `incomplete`
with an explicit outcome). Readiness is terminality, **not success**.

`pdca-executor` then sequentially performs `git merge --no-ff` for **only the `done` groups**. A
successfully integrated group moves `done` → `merged`. An `incomplete` group is **never merged**, even
if it produced successful items and commits before the failure: its tip does not enter the integration,
and its results are preserved. A running lane is never merged early.

A merge conflict is aborted with `git merge --abort`, then escalated. `pdca-escalate` (strong) decides:
resolve manually, reorder the not-yet-merged groups, or mark the group `incomplete`. The expert only
decides; the runner returns control to the merge step and dispatches `pdca-executor` to carry the
decision out with a repeated `git merge --no-ff` of the **unmerged** tip. A previously merged tip is not
touched: no rerun, reset, revert or remerge. A repeated conflict is aborted and escalated again,
without introducing a new counter. The full parent CHECK runs only when all selected `done` groups are
integrated, with no active conflict and no unfinished merge state.

### 6.4. Statuses

Items have `pending` | `in-progress` | `done` | `incomplete`. Groups have `pending` | `in-progress` |
`done` | `incomplete` | `merged`. `merged` exists only for an integrated `done` group; `incomplete`
stays `incomplete` and is never `merged`. A separate integration note `skipped` ("not selected for
integration" plus the reason) is not a group status and does not extend the enumeration.

The physical write into the file is performed by `pdca-executor`, in the same tick as the event. A
divergence from the file is an error.

### 6.5. Commits and merge authorization

A standard multi-group run assumes an **explicitly authorized autocommit** for the `collection/**`
branches and the `merge --no-ff` that gives the task branch a committed tip. The authorization comes
from a project overlay or an explicit user request. The `pdca-collection` skill itself grants **no**
universal right to commit or merge and does not extend a global `AGENTS.md`.

- **Two or more groups with a known incompatibility** — an explicit user no-commit, or commit/merge
  unavailable or forbidden — is a **preflight blocker before worktree/lane allocation**. The groups do
  not start until the authorization is obtained or the user changes the input. A group known to be
  unable to make the mandatory tips is not executed.
- **One group** may work in the current tree without commits if allowed: Git integration is not
  required, the result is the working tree and evidence, and `incomplete` is only an explicit terminal
  outcome, never a consequence of a missing commit.
- **Authorization withdrawn during a running lane** (two or more groups) is a safe stop: keep the
  commits and refs, preserve uncommitted changes as a patch, do not continue the branch chain, do not
  merge. `incomplete` only by an explicit final outcome, never automatically from the withdrawal.
  Push — never.

## 7. C — integration verification

The parent CHECK uses the base `§Phase contracts` → CHECK. `pdca-check` independently chooses
methods and evidence for the **actual integrated result**, with test execution through
`pdca-executor` and outside observation through `pdca-scout`. Its scope is the integrated snapshot plus
integration invariants and any relevant specialized-skill verification deltas. It does not replace
each item's own whole-goal CHECK.

The integration CHECK starts **after all lanes are terminal**. With multiple groups, all eligible
`done` groups must already be merged, all `incomplete` groups excluded, and no merge conflict or
unfinished merge state may remain. Its inputs include the actual group statuses and the separate
integration note (`skipped` plus the reason), the original item requirements, the integrated snapshot
and evidence pointers.

An integration PASS can coexist with `incomplete` groups: it verifies only the integration of work
actually included. Keep the **integrated-tree verdict** and **collection completeness** as different
fields. An integration PASS never marks an unfinished source item `done` and never compensates for unmet
original requirements. Run the integration CHECK even if no group qualified for integration; no work
then receives retroactive acceptance.

- **Accepted integrated result** → collection ACT, with full completion separately conditional on all
  item outcomes.
- **Implementation defect in the integrated tree** → a linked **corrective PDCA cycle** on the current
  integrated branch, with its own plan, status and base transitions. Its ACT returns to the **full
  parent integration CHECK**, not just to the failed probe.
- **Missing, unreliable or unavailable evidence** → the base `unverified`/re-gather route. Do not turn
  missing evidence into a product defect, an attempt or a PASS. Preserve the collection verification
  state and its evidence links.

The collection creates **no additional attempt counter**. For each actual corrective cycle the base
`r`, `n/3`, defect history and escalation rules apply, including recurrence across linked corrective
records. A change of status path or cycle id does not erase defect history. A STOP without an accepted
resolution leaves the parent collection `unverified` and preserves prior item statuses and integrated
work. A corrective cycle's local PASS never substitutes for rerunning the integration CHECK. No
automatic rerun, remerge, recluster, reset or revert; no additional collection lanes for a corrective
cycle; no success cleanup while integration is unverified.

## 8. A — completion

ACT finalizes the collection outcome. **Full collection completion** needs both an accepted common
integration CHECK **and** completion of every original item goal by that item's own whole-goal
CHECK/ACT. An integration PASS with `incomplete` items is a verified partial integration, **not** full
collection success.

A `blocked`/`incomplete`/`STOP` outcome is finalized honestly, without claiming `done` for missing goals
and without taking the success cleanup path. Report what was done, what evidence verified it, what
remains or is blocked, and the next step. Keep collection completeness distinct from the integrated-tree
verdict.

`pdca-executor` removes **only disposable** worktrees and temporary group/task branches that are
`done`/`merged`. The worktrees, branches, commits and patches of **`incomplete` groups are never
deleted**: before any cleanup their refs and patch paths are preserved (the simplest form is to leave
the worktree and refs in place and record that explicitly in the status). Status and evidence paths stay
available while they hold pointers to preserved results. Push — never.

If escalation does not issue an acceptable revised plan or STOP, the unresolved status, the evidence
and the integrated work are preserved: no success and no cleanup, the parent collection stays
`unverified`, and source items keep their previous statuses. A STOP or any non-PASS termination forbids
cleanup and merging. A corrective cycle's success alone does not mean the collection succeeded.

### 8.1. Campaign item projection

The incremental contract defines campaign outcomes, whole-goal acceptance, pauses and resume. The
collection only maps the campaign's persisted outcome and item `disposition` to its own item status:

- **Before campaign bootstrap**, including `preparation_state=ready` → `pending`.
- **Running or paused** (`disposition=active` | `paused`) → `in-progress`. A pause stops progression
  within its group, not other groups.
- **Finalized with accepted `met`** → `done`.
- **Explicitly finalized without accepted `met`** → `incomplete` with the reason; the existing
  group-stop rule applies. A failed step or a checkpoint alone never finalizes the item.

The collection's integration CHECK remains independent of campaign acceptance.

## 9. Lanes and schedule revision

### 9.1. One lane is one group

A lane is one group work stream, driven by its designated driver: the primary in normal mode, or an
authorized `pdca-orchestrator` in autonomous mode (with the flat-primary fallback if needed). With two
or more groups, each lane has an isolated worktree; with one group, the current worktree and branch.

For each item in the recorded order:

1. With two or more groups, create the branch `collection/<id>/task-<g>-<k>` from the committed tip of
   the previous one. With one group there is no branch: work happens on the current branch.
2. Continue the saved own PLAN of the item's decided form, contract and overlay. The designated driver
   receives the handoff state of the same cycle (same form/contract/overlay, `N`, `r`, `n`); before DO
   it checks the plan's premises against the current state of the lane and the validity of the revision
   binding through the roles — facts from `pdca-scout`, the decision from `pdca-planner`. A repeated
   PLAN is by default **not** started: the cycle continues from DO. PLAN is reopened only when
   staleness is detected.
3. In an allowed autocommit mode, commit after the item; otherwise the next item does not branch from a
   committed result. Commit **only the item's files** (`git add <paths>`), not `git add -A`, so alien or
   artefact files are not picked up.

The driver **makes no decisions**: it routes the plan. It does not decide that an item is impossible,
not ready or independent, does not choose scope and does not judge the result; questions go to
`pdca-planner`, not to the user. `incomplete` is a consequence of a failure or of an impossibility
under the contract, not a judgment of the lane.

### 9.2. The queue and per-item continuation

The collection status file is the source of truth of the queue. The runner re-reads it at the start and
after each item, takes the first item with status `pending` in the recorded order and updates its
status. The launch prompt passes **the path to the file**, not an enumeration of items — that is how the
queue survives compaction and a restart.

- With two or more groups the task branch is the unit of commit (no per-item worktree); with one group
  there is no task branch.
- **An item failure follows its own cycle's transition**: CHECK alone may send a contract defect to
  PLAN; an implementation defect goes CHECK → DO; a DO that cannot finish goes DO → ACT. ACT records a
  final `incomplete` with cause and evidence, preserving the patch and status.
- A **final `incomplete` of an item stops the whole group**: the next item is not taken, all remaining
  `pending` items of the group are marked `incomplete` with the explicit reason **“the group is
  stopped”**, and they are **not executed**. The group is **not merged**.
- The commits already made and the patch of the failed item are **preserved**. Other groups continue
  their work.
- The lane summary is `done` | `incomplete` per group. The status `blocked` does not exist for
  items/groups; `blocked` remains only a state of the parent verification.
- With two or more groups the result of a `done` group is the tip of its branch
  `collection/<id>/group-<g>`, fast-forwarded to the last completed item. With one group it is the
  current branch.
- If the lane returns no result, mark the group `incomplete` and preserve its refs and patch. The lane
  returns a compact summary of at most eight lines, without code, diffs or logs.

### 9.3. A campaign item in a lane

An item with the form `campaign` has **one designated driver throughout its steps** — the primary in
normal mode, or the authorized cheap `pdca-orchestrator` in autonomous mode, with the permitted
flat-primary fallback. It holds the campaign status, the shared counters, the accumulated knowledge and
the effort accounting, owns recovery, starts the next step **only on the planner's decision**, and runs
the current step's cycle inline in its own session. A campaign is always single-threaded: one step at a
time, one lane, no internal parallelism.

It receives the item's form, the incremental contract by exact ID, `preparation_ref`/`campaign_ref` and
the dispatching rule from the caller; it does not choose the rule and does not classify the item. The
contract/overlay of a **concrete step** is decided by `pdca-planner` for that step and persisted in the
durable step record **before** the step; before the bootstrap it does not exist and the runner does not
derive it.

An item with the form `cycle` is driven by its designated driver: it receives one already-planned cycle,
executes it and returns the result. It does not own campaign advancement and does not advance anything
else in the batch. Collection owns the outer item completion commit; a campaign's `Commit policy: none`
disables intermediate step commits, not that authorized outer commit.

The step semantics — the covered content of one step, the increment unit, the accepted negative
candidate as knowledge, the absence of a forced second increment, the whole-goal final check and the
mandatory-requirement veto — belong to the incremental contract plus the base rules. The collection adds
neither a counter nor a gate.

### 9.4. Lane pause

A lane pause is **derived** from `disposition=paused` of the current item and is not stored as a
separate authoritative lane field. The item status stays `in-progress`: a pause is not a new status
value, and no new item/group statuses are introduced. A paused lane does not proceed to the next
dependent item of its group; other groups continue.

### 9.5. Stale plan and schedule revision

Before starting DO the lane checks that the saved PLAN is applicable to the actual state: are the
predecessors' outputs available, have the premises or assumptions changed? This is a narrow
applicability check, not a mandatory repeated PLAN and not the driver deciding instead of the planner.

- **The premises are unmet** → control returns to the item's **own PLAN**. `pdca-planner` decides by
  the base revision rules (`r`/`n`); the counters and the item's identity are preserved (`N` is not
  reset, no cycle “from scratch”).
- **A change before the lanes start** — if the footprints or dependencies refined from the PLAN change
  the picture, the collection `pdca-planner` may **rebuild the schedule** (DAG/groups/order), and the
  barrier and revision binding are updated and persisted. This is the only allowed revision window.
- **After the lanes start**, automatic `rerun`/`remerge`/`recluster`/`reset`/`revert` are forbidden. A
  change incompatible with the approved groups — footprint overlap, a broken order — **stops** the
  continuation pending an explicit decision of `pdca-planner`/`pdca-escalate`. A silent old DAG and an
  automatic regrouping are inadmissible. Compatible local revisions may continue only with evidence
  from `pdca-planner` and a persisted updated revision binding; the driver itself does not declare
  compatibility.
- **A new campaign or item after the barrier** does not mutate the DAG silently: it is an explicit
  collection replan/reapprove (`pdca-planner`, and in normal mode the user), taking into account the
  already started lanes and the stop/scope constraints. Old identities, statuses and evidence are
  preserved; there is no automatic `recluster`. A compatible local change goes through the existing
  route (PLAN revision plus a persisted revision binding). The addition consumes capacity explicitly:
  its queue position is recorded, and it may not silently jump ahead of ready items. When the milestone
  window is fixed, it is scheduled for the next milestone instead of stretching the current one.

### 9.6. Surface reservation and extension

The planned footprint is a **conservative reservation of the allowed surface for the whole item**, not
a forecast of the exact edits and not the union of the first steps. A wide reservation is allowed and
means less parallelism, not a wrong plan. If the disjointness of footprints cannot be proven, the items
go in one lane: “probably they will not overlap” is not a basis. Going beyond the boundary stops the
work.

The surface is issued by the collection PLAN; a campaign item's charter contains it as a subset, and a
step cannot go beyond the campaign's surface. Extending the reservation or the surface after the
barrier is a stop/reapprove — an explicit renegotiation by `pdca-planner` (and in normal mode the user),
taking into account the already started lanes and accepted results. There is no automatic
`recluster`/`remerge`/`reset`/`revert`; an already integrated tip is not merged again, and accepted
steps are not recalculated.

## 10. The collection status record

File: `.pdca/status/collection-<slug>.md`. It contains:

- the input (the item list) and the `collection-id`;
- the table of groups: id, items, order, worktree, branch/ref and **status**
  (`pending` | `in-progress` | `done` | `incomplete` | `merged`). `merged` is an integrated `done`
  group (the transition is only `done` → `merged`); `incomplete` stays `incomplete` and never merges.
  A group record has its stop reason (“the group is stopped”), tip/ref, preserved commits, remainder
  and patch path;
- the table of items: id, group, branch, status (`pending` | `in-progress` | `done` | `incomplete`) and
  a **separate** plan readiness `plan_state` (`pending` | `running` | `ready`), the item's **form** and
  (for a `cycle`) its contract and overlay, `cycle_id` (including `N`), the canonical status path of
  the item, `plan_revision` (`r`), the baseline ref, the footprint/requirement/prerequisite refs, the
  reason and patch path for `incomplete`, and a link to the item's status file. `plan_state=ready` is
  not an approval and not `done`; the merge is at the group level, and an item never has the status
  `merged`;
- per item: the **form** (`cycle` | `campaign`); for a `cycle` — `plan_state`, the contract with its
  overlay and the pending approval ref pointer (normal mode); for a `campaign` — `preparation_state`
  (`pending` | `ready`), the **single authoritative** `preparation_ref`
  (`.../preparation.md@r<k>`) and `campaign_ref` (optional before the baseline bootstrap, mandatory
  after). There is no item-level contract for a campaign: the contract/overlay of a concrete step is
  recorded in the step's durable record. The per-item `disposition` (`active` | `paused` | `finalized`)
  is an explicit field of **both** forms, and the step's pending approval refs are recorded here;
- **three different things**: readiness (`plan_state`/`preparation_state`), the campaign runtime status
  and the per-item `disposition` are not the same. Readiness is not runtime and not completion;
- an item record without a **form** is read as `cycle`; an unrecognised form value or an unresolvable
  contract/overlay **fails closed**, never a guess;
- the decisions of the collection phases (the items' own PLANs, the ALL-barrier, clustering, the merge
  strategy) and the **PLAN revision vector** used for the schedule;
- the subsection **“General verification and recovery”** — the state of the **common verification**,
  not the status of a group or an item. It records the last result of the common integration CHECK and
  the paths to its evidence (command, exit code, log, numbers); the blocking reason (no report,
  environment failure, confirmed defect) and the verification state (`blocked` | `unverified` |
  `pass`); the defect id and history — the applied fixes and the result of the integration CHECK after
  each — preserved across closures and restarts of the corrective cycle; a link to the corrective
  cycle's status file; and the next allowed step;
- collection completeness (all original item goals accepted), the integrated-tree verification (the
  independent CHECK verdict) and incomplete items with preserved results as **distinct fields**.

## 11. Report and approval barrier

The report follows the base ACT and `references/act.md`: what was done, what evidence verified it, what
remains or is blocked and the next step. Keep collection completeness distinct from the integrated-tree
verdict.

The shared approval rules are in the base `§Normal-mode approval`, including the durable pending
approval ref, the same-ref approval record, applicability on resume and a fresh approval after a
substantive revision. The collection adds one handoff: the item driver returns its saved `plan_handoff`
or `preparation_handoff` with the **pending approval ref** to the collection primary. The primary
obtains the user's approval; the item driver cannot invent or infer it, and DO waits for the matching
record. A paused item remains `in-progress` with `disposition=paused`; its lane does not advance to the
next dependent item. Approval is separate from the preparation barrier, which requires **ready
preparation** but not pre-approved DO.

In autonomous mode no ordinary plan approval is invented or required, but an explicit external or user
permission requirement remains a blocker as in the base.

## 12. Fallback and parameters

Host role and resource-blocker rules are inherited from the base `§Roles and host requirements`. The
collection section covers only **driver** fallback.

When an autonomous `pdca-orchestrator` is absent or cannot delegate, use the **flat cheap primary** as
driver with `Notice:` and a durable reason, if the host permits it. It drives one current item per lane
and delegates PLAN/DO/CHECK to their required roles; a campaign still has one designated driver for all
steps. Independent groups may be processed concurrently up to capacity only if the host permits that
concurrency; otherwise they are sequential. Normal mode already uses the primary driver and must not
treat the lack of orchestrator delegation as a reason to skip approval. The fallback never promotes a
driver into PLAN, CHECK, execution or expert-review authority. Missing mandatory roles or forbidden
fallbacks follow the base resource-blocker rules; collection preparation, barrier and handoffs remain
unchanged.

| Parameter | Default |
|---|---|
| PLAN parallelism ceiling | `min(#items without a ready plan/charter, plan_cap)`; `plan_cap = 4` is a scheduling choice of this contract, not a host setting. It is bounded by what the host actually runs at once; only the write of the common status is serialized. |
| Lane parallelism ceiling | `min(#groups, cap)`; `cap = 4` is a scheduling choice of this contract, not a host setting. It is bounded by observed concurrency **and** the declared host budget. A budget that cannot carry four lanes lowers `cap` and is recorded, not discovered later as timeouts. |
| Worktree directory | `<repo>-worktrees/<collection-id>/<group>` (not created with a single group) |
| Merge | With two or more groups, wait for **all** lanes to be terminal, then `git merge --no-ff` for the **`done` groups only**, sequentially. Not needed with one group; `incomplete` is never merged. |
| One group | Work in the current worktree and branch; no worktrees, group/task branches or merge; `incomplete` leaves already-made commits on the current branch. |
| Autocommit/merge right | Given by a project overlay or an explicit user request; the skill itself grants no right. Two or more groups without the right is a preflight blocker before allocation. One group may work in the current tree without commits if allowed. Push — never. |

The roles, tiers and model bindings belong to the host and the base common contract: this contract
names roles only, carries no model id and adds no role.

## 13. Limitations and false expectations

- **“A collection is a big cycle.”** No. Each item is a separate complete PDCA invocation with its own
  acceptance. The collection coordinates; it does not merge the goals into one verdict.
- **“A failed item can be averaged away.”** No. An `incomplete` group is never merged, and integration
  PASS never marks the missing item `done`.
- **“Readiness is approval.”** No. `plan_state=ready` or `preparation_state=ready` means the plan,
  charter or preparation exists; normal-mode DO still needs its own recorded approval.
- **“The batch can start as soon as one item is planned.”** No. The ALL-barrier is strict.
- **“A lane can be re-run after a partial failure.”** No. Automatic rerun, remerge, recluster, reset and
  revert are forbidden after lanes start. A change needs a planner decision and, where applicable,
  approval.
- **“The collection may commit and merge freely.”** No. Autocommit and `merge --no-ff` need an explicit
  project policy or user request; without it a multi-group run does not start.
- **“An integration PASS completes the collection.”** No. Full completion needs every original item's
  own whole-goal CHECK/ACT as well.

## 14. Where to go next

- The base cycle: [`pdca.md`](pdca.md), [`pdca-guide.md`](pdca-guide.md),
  [`skills/pdca/SKILL.md`](../skills/pdca/SKILL.md).
- The incremental form that a campaign item runs: [`pdca-incremental.md`](pdca-incremental.md).
- The coding overlays applied to item work: [`pdca-coder.md`](pdca-coder.md),
  [`pdca-dotnet.md`](pdca-dotnet.md).
- Host setup: [`install.md`](install.md).

## Sources

| Claim | Source |
|---|---|
| A collection is independent goals, each a complete PDCA invocation | `skills/pdca-collection/SKILL.md §Scope and entry` |
| The base common contract governs item cycles and integration; the collection adds only coordination | `skills/pdca-collection/SKILL.md §Inheritance` |
| Preparation, barrier, DAG, groups, lanes, integration and status definitions | `skills/pdca-collection/SKILL.md §Batch terminology` |
| Item ownership and designated drivers | `skills/pdca-collection/SKILL.md §Items and execution ownership` |
| Capability preflight | `skills/pdca-collection/SKILL.md §Capability preflight` |
| Per-item PLANs, the barrier and clustering | `skills/pdca-collection/SKILL.md §P — per-item PLANs, the barrier, clustering` |
| Barrier by item form and readiness vs completion | `skills/pdca-collection/SKILL.md §Barrier by item forms` |
| Worktrees, branches, runners and the merge barrier | `skills/pdca-collection/SKILL.md §D — infrastructure, tracking, merge` |
| Commits, merge authorization and preflight blocker | `skills/pdca-collection/SKILL.md §Scope and entry`; §Parameters |
| Integration verification and corrective cycles | `skills/pdca-collection/SKILL.md §C — integration verification` |
| Completion, cleanup and preservation | `skills/pdca-collection/SKILL.md §A — completion` |
| Campaign item projection | `skills/pdca-collection/SKILL.md §Campaign item status projection` |
| Lane execution and the queue | `skills/pdca-collection/SKILL.md §One lane = one group`; §The queue and the per-item continuation |
| Campaign item in a lane | `skills/pdca-collection/SKILL.md §A campaign item in a lane (designated item driver)` |
| Lane pause, stale plan and surface reservation | `skills/pdca-collection/SKILL.md §Lane pause`; §Stale plan and schedule revision; §Surface reservation and its extension |
| Collection status record and fields | `skills/pdca-collection/SKILL.md §Collection status record`; §File and content |
| Approval barrier, report and fallback | `skills/pdca-collection/SKILL.md §Approval barrier (normal mode)`; §Report; §Fallback |
| Parameters and defaults | `skills/pdca-collection/SKILL.md §Parameters` |
