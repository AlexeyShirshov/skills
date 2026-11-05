---
name: pdca-collection
description: "Collection execution of independent user goals, each with its own complete PDCA invocation and PLAN-selected form. The collection driver coordinates a preparation barrier, conflict-aware groups, isolated lanes when permitted, independent verification of the integrated result, and ACT without replacing an item goal or its acceptance criteria."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# A batch of independent goals as PDCA

## Scope and entry

A **Collection** batches independent user goals, each a complete PDCA invocation (not one DO's decomposition). The base entry PLAN or user selects its form; no second PLAN reclassifies it.

## Inheritance

`../pdca/SKILL.md` (§Common cycle contract) governs item, integration CHECK and corrective cycles; load alongside this file. Direct invocation skips form reclassification. A `campaign` also loads `../pdca-incremental/SKILL.md`. Resolve planner `plan_reference_path` from base `pdca`.

Collection adds batch coordination, **not another cycle or attempt counter**.

## Batch terminology

- **Item preparation** — pre-DO work: persisted cycle PLAN (`plan_state=ready`) or campaign
  charter (`preparation_state=ready`, valid `preparation_ref`). No substantive DO. A PLAN-terminal
  cycle is **resolved**, not prepared (§PLAN-terminal item projection).
- **Preparation barrier (ALL-barrier)** — before scheduling, lanes or DO, every item must be
  prepared or have a recorded PLAN-terminal resolution (§P.3); a missing plan is not resolution.
  Readiness is neither approval nor completion; resolution is neither readiness, `done` nor credit.
  Normal-mode DO still needs recorded approval.
- **Dependency DAG** — acyclic required item order (`A → B`: B depends on A), built after the
  barrier. Write conflicts also constrain groups.
- **Group** — sequential queue of dependency-linked or shared/uncertain-surface items. Groups run
  in parallel only when their write surfaces do not conflict, within host limits.
- **Lane** — one stream for one ordered group. Multiple groups get isolated Git worktrees/branches;
  one group uses the current worktree/branch.
- **Integration** — merge only `done` groups, never `incomplete`; one group needs no merge.
- **Batch status** — durable collection preparation, groups, outcomes, integration and verification
  in `.pdca/status/collection-<slug>.md`.
- **Final verification** — independent CHECK of the integrated result, in addition to item CHECKs;
  verified partial integration does not complete unfinished goals.

The **collection driver** coordinates status, barrier, schedule, integration and final CHECK/ACT, but does not plan implementation, tests or acceptance, edit or run commands. `pdca-planner` decides PLAN, `pdca-check` independently decides CHECK, and `pdca-executor` executes/writes. Each item has one
**designated driver** and durable record; collection and item drivers never compete for state.

In **normal mode**, the primary drives collection and cycles/steps, gets user approval before each DO and does not dispatch `pdca-orchestrator` to drive them. In **autonomous mode**, it delegates coordination when permitted; a group runner may drive its items and all steps of one campaign (one driver throughout). Delegation failure follows §Fallback; PLAN/CHECK authority never transfers to a cheap driver.

Collection adds preparation, barrier, DAG/groups, lanes, integration, batch status and integration verification. One item/lane is valid; inherited cycle requirements remain.

A multi-group run requires **explicit autocommit/`merge --no-ff` authorization** for `collection/**` branches via project overlay or explicit user request; otherwise task branches lack committed tips. This skill grants no universal commit/merge right and does not extend global `AGENTS.md`. Without authorization, multi-group preflight blocks; absence is not authorization and cannot silently change the run mode.

- **`>=2` groups with known incompatibility** (user forbids commits, or commit/merge is unavailable
  or forbidden): block before allocation until authorization or changed input; do not run a group
  unable to make its required tip.
- **One group** may use the current tree without commits if allowed: no Git integration is required;
  `incomplete` is explicit, never caused by missing commits.
- **Authorization withdrawn in a multi-group lane**: stop safely, preserve refs/commits and uncommitted
  changes as a patch, do not continue the chain or merge. Withdrawal never automatically means
  `incomplete`; only an explicit final outcome does. Push — **never**.

## Items and execution ownership

Preserve original goals/criteria; scheduling metadata cannot redefine acceptance. The first `pdca-planner` PLAN selects `cycle`/`campaign` and a specialized skill only for `cycle`; collection neither classifies nor adds a PLAN. After the barrier, a cycle resumes its saved PLAN at DO unless stale. Campaigns have no item contract/overlay; select each step separately, never future steps in preparation.

Collection schedules/integrates; one designated item driver owns the cycle or whole campaign. `pdca-executor` writes both records. Nested collection items and nested campaigns are forbidden. Item `done` requires accepted whole-goal CHECK/ACT; integration CHECK is separate.

## Capability preflight

Before lane allocation, and before campaign start in a lane, verify observable host capabilities: mandatory roles/contracts, permitted delegation (including `escalate → scout`), and when applicable the installed `pdca-orchestrator` against canonical asset/permissions. No trial work or assumed numeric host settings.

A missing mandatory role stops the run, recording accepted work; a missing contract fails closed without substitution. Optional runner/delegation unavailability follows §Fallback if permitted. Late-discovered failures pause before the dependent action; gates remain unchanged.

## Collection (P / D / C / A)

### P — per-item PLANs, the barrier, clustering

Strict order: **each initial item PLAN → ALL-barrier → DAG/groups → item DO**. Each PLAN belongs to its item invocation, not batch reclassification.

1. **Input and first PLAN.** Keep each independent goal's stable id, **unchanged** brief and supplied
   criteria. Dispatch each item separately to `pdca-planner` before selecting `cycle`/`campaign`.
   Planner selects form, applicable specialized skill and criteria only if user supplied none; it
   does **not** select implementation, steps, verification, evidence or commands. Only on planner
   request, call `pdca-scout` for missing facts. Pass other briefs as dependency context; do not yet
   build the DAG or order.

2. **Preparation to PLAN/DO boundary.** The item's designated driver continues that **same initial
   PLAN**, not a collection PLAN:
   - `cycle`: `pdca-executor` records the result contract and `plan_state=ready`, then returns
    `plan_handoff` at the PLAN → DO boundary. Contract holds goals, supplied/derived criteria, constraints, assumptions,
     bounds, risks and stop conditions, but no prescribed DO steps or frozen CHECK method. Record
     estimated conflict surface and prerequisite/dependency assumptions separately as scheduling
     metadata, not implementation or acceptance criteria.
   - `campaign`: follow `../pdca-incremental/SKILL.md` §Campaign cycle / Bootstrap. Executor persists
     charter at `.pdca/<collection-id>/items/<item-id>/preparation.md`,
     `preparation_state` and authoritative `preparation_ref`, then returns `preparation_handoff`.
     Barrier requires no baseline, runtime record, substantive DO, future step plan or step count.

   PLAN-terminal `acceptance criteria cannot be determined`, `goal cannot be measured under the
   available means`, proven `original task is infeasible under the stated constraints`, or
    `requested result already established` goes to ACT without DO/CHECK and **cannot be marked ready**. ACT
   records `terminal=<cause>`, `attempts=0`: no attempt, readiness, `done` or goal credit; it is a
   **terminal resolution**, not completion. A failed candidate or unproven method alone is not proof
   of infeasibility. Campaigns take these resolutions at PLAN; after barrier, current-state
   measurement is the first step (no dummy increment or pre-baseline change). Re-entry preserves
   cause/history; do not rerun the unchanged failed criterion.

   **Parallel preparation.** Dispatch up to `plan_cap` (default 4, §Parameters) and observed host
   capacity. Accept handoffs as ready; serialize shared-status writes through `pdca-executor`. Plans
   need no predecessor artifacts. Surfaces are nonbinding claims; keep unknowns explicit and limit
   lane parallelism conservatively. PLAN neither locks files nor prescribes DO.

3. **ALL-barrier.** Do not schedule/allocate lanes until **every** item has a genuine saved cycle PLAN
   or campaign charter, or a recorded PLAN-terminal resolution (`terminal` one of three causes,
   `incomplete`, `attempts=0`). Resolution satisfies the barrier as an outcome, not readiness,
   `plan_state=ready`, `done`, DO or CHECK (§Batch terminology). Any item with neither is a gap: no
   placeholder, bypass or early DO. Status/preparation writes may precede the barrier; substantive
   bootstrap and DO may not.

4. **Clustering after the barrier.** `pdca-planner` forms dependency DAG/groups using dependencies,
   estimated write conflicts and host capacity. Overlapping/uncertain surfaces share one sequential
   lane; independent groups may parallelize. Persist schedule, `plan_cap`/`lane_cap` and PLAN revision
   vector in status header before allocation. Later changes need planner decision and applicable
   approval (§Lane execution and schedule revision → Stale plan and schedule revision). DO chooses
   implementation.

5. **Durable tracking.** The collection status file (§Collection status record) is the sole batch
   progress mirror. Driver coordinates; `pdca-executor` writes each transition, handoff, group stop,
   merge, correction and escalation **in the same turn**; no parallel list. On recovery, status is
   authoritative. Item drivers maintain their own files under the same one-writer rule.

#### Barrier by item forms

- **`cycle`** — genuine PLAN with `plan_state=ready`, revision, footprint reservation/uncertainty,
   predecessor requirements, assumptions/prerequisites and refs; this same PLAN executes. `ready`
   means plan readiness, not approval/completion.
- **`campaign`** — prepared immutable/revisioned charter at
  `.pdca/<collection-id>/items/<item-id>/preparation.md`, `preparation_state` (`pending` | `ready`)
  and the item's **single authoritative** `preparation_ref=<path>@r<k>`. `ready` is not `met` or
  campaign completion. `campaign_ref` points to runtime: optional before current-state step opens it,
  then required; it is neither charter nor substitute for `preparation_ref`.
- **plan-terminal (`cycle` or `campaign`)** — `terminal=<cause>` (§PLAN-terminal item projection), a
  resolved outcome, not readiness; no DO/CHECK.

**Readiness ≠ completion.** Prepared charter without runtime is `barrier-ready`, not `started`; item stays `pending`, never `done`. Campaign succeeds only on accepted `met`; the barrier does not require later artifacts.

With **one group**, retain collection form and use one lane in the **current** worktree/branch: no worktree, group/task branch, merge barrier (§D.3) or merge. Autocommits go directly to current branch. If `incomplete`, existing commits stay (no automatic rollback); preserve failed item's uncommitted changes as patch and roll back only its paths (§Lane execution and schedule revision → The queue and the per-item continuation). One item is still a collection; empty input means report nothing to do.

### D — infrastructure, tracking, merge

Allocate lanes/worktrees/branches/runners **only** after ALL-barrier and persisted schedule binding (§P.3–§P.4).

1. `pdca-executor` creates one worktree/group at
   `<repo>-worktrees/<collection-id>/<group>` and branch `collection/<id>/group-<g>`.
   Group and task branches are sibling Git refs, never name-prefixes. **One group** has no worktree,
   branch or merge (§P).
2. In autonomous mode, available `pdca-orchestrator` runners start in parallel (one/group, up to
   recorded `lane_cap`); each may be designated item driver and keeps campaign driver across steps
   (§Items and execution ownership, §Lane execution and schedule revision). In normal mode primary
   drives cycles/steps and obtains approval; it does not spawn orchestrators as their drivers. Host
   capability bounds actual concurrency.
3. **Merge barrier**: with `>=2` groups wait until every lane is terminal (`done` or `incomplete`
   with explicit outcome); readiness means terminal, **not** successful. `pdca-executor` then
   sequentially runs `git merge --no-ff` for `done` groups only (message starts `#<n>` for issue
   item); successful integration changes group `done` → `merged`. **An `incomplete` group is never merged**,
   even if it has successful items/commits; exclude its tip and preserve results (§A,
   §Lane execution and schedule revision → The queue and the per-item continuation). Never merge a
   running lane early. On conflict, executor runs `git merge --abort`; escalate the group to strong
   `pdca-escalate` to decide manual resolution, reorder, or `incomplete`. Do not touch other groups;
   C remains blocked until resolved.

   **Repeated merge through runner.** `pdca-escalate` only decides; it does not edit, execute or
   spawn executor. Its response is not merge success. For “resolve manually”/“reorder”, runner
   returns to MERGE and itself dispatches executor to repeat `git merge --no-ff` of the unmerged tip
   after abort. Reorder only groups not yet integrated; never rerun/reset/revert/remerge an
   integrated group or reset successful results. Continue remaining eligible merges after retry; run
   **full parent integration CHECK** only after all selected `done` groups are integrated, with no
   conflict or unfinished merge. Repeated conflict: abort and escalate again, without adding a
   collection attempt counter (`r`/`n` remain the common contract). “Mark incomplete” returns to
   MERGE: exclude that entire tip, including successful items/commits; integrate remaining `done`
   groups normally, without touching or reordering already merged groups.
4. `pdca-executor` records each item/group status in the same tick as its event; the collection
   file is the sole progress mirror (§Collection status record; lane: §Lane execution and schedule
   revision). Item/group enums, `merged` transition, and typed `terminal` are defined there and in
   §PLAN-terminal item projection; `skipped` + reason is an integration note, not a group status.

   **The queue is data.** `pdca-executor` copies `scripts/status_lint.py` byte-identically to
   `.pdca/scripts/` (driver supplies its absolute path in each write brief) and runs it from project
   root after each write. Exit `0`: valid; `2`: repair row and relint in the same turn (raw `|` or
   wrapped note, wrong cell count, unknown status, malformed plan-terminal row); `1`: resource
   blocker; report the resource blocker. Lint failure is **not a written status**.

### C — integration verification

**Stage candidate before C.** Before `pdca-check`, executor persists the integrated snapshot at collection `evidence_root` inside `.pdca/` (default `.pdca/<collection-id>/rv<k>/`). Stage every CHECK input under `snapshot/` (leave product originals in place), with `sha256` manifest, identity bound to the final integrated commit/ref and worktree state, item statuses and evidence pointers. Dispatch only after writing; CHECK reads `.pdca/**` only.

Parent CHECK uses **base `../pdca/SKILL.md` §Phase contracts → CHECK**: `pdca-check` independently chooses methods/evidence; tests run through `pdca-executor`, outside observation through `pdca-scout`. Dispatch includes the complete inline base CHECK contract and `evidence_root`; scope is staged snapshot, integration invariants and relevant verification deltas (`../pdca-coder/SKILL.md`, `../pdca-dotnet/SKILL.md`). The dispatch does not replace item CHECK, widen permissions, or inline candidates/product files; CHECK reads the staged candidate itself.

Start integration CHECK **after all lanes are terminal**; merge eligible `done` groups, exclude `incomplete`, and leave no conflict/unfinished merge. Supply group statuses, `skipped` note/reason, original requirements, staged snapshot and evidence.

A **missing, incomplete or stale** snapshot (missing copy, manifest mismatch, stale identity) is not product failure or attempt: **re-gather**; collection stays `unverified`.

Integration `PASS` may coexist with `incomplete` groups and verifies included work only. Keep
**integrated-tree verdict** distinct from **collection completeness**; PASS never marks unfinished items `done` or compensates unmet goals. Run CHECK even with no eligible group; no retroactive acceptance.

- **Accepted integration** → collection ACT (§A); full completion still depends on every item.
- **Integrated-tree implementation defect** → linked **corrective PDCA cycle** on current integrated
  branch with own plan/status/base transitions; its ACT returns to **full parent integration CHECK**,
  not merely failed probe.
- **Missing/unreliable/unavailable evidence** → base CHECK `unverified`/re-gather; never product
  defect, attempt or PASS. Preserve verification state and evidence links.

No collection attempt counter: corrective cycles use base `r`, `n/3`, defect history and escalation rules, including linked-record recurrence; status path/cycle ID changes do not erase history. STOP without accepted resolution leaves parent `unverified` with prior item statuses/integration. Corrective PASS never replaces integration CHECK.

No automatic rerun/remerge/recluster/reset/revert, no additional collection lanes for a corrective cycle, and no success cleanup while integration is unverified.

### A — completion

ACT finalizes. **Full completion** requires accepted integration CHECK plus every original goal's accepted whole-goal CHECK/ACT. PASS with `incomplete` is verified partial integration, not full success. ACT also closes the collection's own final `## Lessons learned` retrospective (§Collection status record) once, after the result is frozen, for whichever outcome was reached — accepted, partial, `blocked`/`incomplete`, `STOP`, early failure or refusal; a run that ended before any item still closes it there, and no CHECK or item work is invented. Finalize `blocked`/`incomplete`/`STOP` honestly; never mark missing goals `done`. After reporting, remove only disposable worktrees/temporary branches of `done`/`merged` groups. The worktrees, branches, commits and patches of **incomplete groups must never be deleted**; preserve their refs and patch paths, and explicitly record in status when their worktree/refs are left in place. Keep status/evidence paths to preserved results. Push — **never**. If escalation yields no acceptable revised plan/STOP, preserve unresolved state, claim no success/cleanup, keep parent `unverified` and source item statuses unchanged. **A STOP or any non-`PASS` termination: cleanup and merging are forbidden.** Corrective success alone is not collection success.

A **plan-terminal resolution** satisfies barrier/schedule but is neither completion, credit nor execution failure; it prevents full completion. Summary separates **accepted goals** (`done`),
**plan-terminal resolutions** (cause/evidence, `attempts=0`) and **execution failures** (`incomplete` after real failure).

A campaign outcome follows §Campaign item status projection; campaign acceptance is not common `C`.

## Lane execution and schedule revision

### One lane = one group

A lane is one group work stream, driven by its designated driver: the primary in normal mode, or an authorized `pdca-orchestrator` in autonomous mode (flat-primary fallback if needed). With `>=2` groups — an **isolated worktree per group** (absolute paths, `cd`); with **one** group — the current worktree and branch.

For each item in the recorded order:

1. with `>=2` groups — the branch `collection/<id>/task-<g>-<k>` from the committed tip of the
   previous one (with one group there is no branch: work happens on the current branch).
2. **the continuation of the saved own PLAN** of the item's decided form, contract and overlay:
   `pdca-orchestrator` receives the handoff state of the same cycle (the same form/contract/
   overlay, `N`, `r`, `n`); before DO it checks the applicability of the plan's premises to the
   current state of the lane and the validity of the revision binding **through the roles**
   (`pdca-scout` — facts, `pdca-planner` — decision), then drives DO → CHECK → ACT by delegating
   `pdca-planner`/`pdca-executor`/`pdca-check`/`pdca-escalate`. A repeated PLAN is by default
   **not** started — the cycle continues from DO; PLAN is reopened only when staleness is
   detected (§Stale plan and schedule revision).
3. autocommit after the item, **only in an allowed autocommit mode** (§Scope and entry) —
   otherwise the next one does not branch from a committed result. Commit **only the files of the
   item** (`git add <paths>`), not `git add -A`: otherwise alien/artefact files are picked up.

`pdca-orchestrator` **makes no decisions** — it only routes the plan: it does not decide that an item is impossible/not ready/independent, does not choose the scope and does not judge the result; any question goes to `pdca-planner`, not to the user. The status `incomplete` is a consequence of a failure or of an impossibility by the contract (§Lane execution and schedule revision), not a judgement of the lane.

### The queue and the per-item continuation

The source of truth of the queue is the collection status file (§Collection status record): the runner re-reads it at the start and after each item, takes the first item with the status `pending` in the recorded order and updates its status; the launch prompt passes **the path to the file**, not an enumeration of items — that is how the queue survives compaction and a restart.

- With `>=2` groups the task branch is the unit of commit (no per-item worktree); with one group
  there is no task branch.
- **An item failure follows its own cycle's transition**: CHECK alone may send a contract defect
  to PLAN; an implementation defect goes CHECK → DO, and a DO that cannot finish goes DO → ACT.
  ACT records a final `incomplete` with cause and evidence, preserving the patch and status.
- **A plan-terminal item is not a group stop.** It closes through its own ACT with
  `terminal=<cause>`, `attempts=0`, stays `incomplete`, and the queue takes the next item; it is
  skipped for execution and never becomes `done` or an accepted goal. The group's status is decided
  by its executed items, and the remaining items keep their own statuses and are executed normally,
  wherever the terminal item sits in the order.
- A **final `incomplete` of an execution failure** (`terminal=execution`, the default; not a
  plan-terminal resolution) **stops the whole group**: the next item is not taken, all remaining
  `pending` items of the group are marked `incomplete` with the explicit reason **"the group is
  stopped"** and are **not executed**; the group is **not merged** (§D.3).
- The commits of the group already made and the patch of the failed item are **preserved**
  (§D, §A); **other groups continue** their work.
- The lane summary is `done` | `incomplete` (per group); the status `blocked` does not exist for
  items/groups — `blocked` remains only a state of the parent verification.
- With `>=2` groups the result of a `done` group is the tip of its branch
  `collection/<id>/group-<g>`, ff-advanced to the last completed item; with one group it is the
  current branch, which also keeps the commits already made and the failed item's patch (§P, §D).
- If the lane returns no result (§Lane liveness), mark the group `incomplete` and preserve its refs and patch.
- The lane returns a compact summary of ≤8 lines without code/diffs/logs.

### A campaign item in a lane (designated item driver)

An item with the form `campaign` has **one designated driver throughout its steps** — the primary in normal mode or the authorized cheap `pdca-orchestrator` in autonomous mode, with the permitted flat-primary fallback (§Items and execution ownership, `../pdca/SKILL.md` §Control modes). It holds the campaign state/status, the shared counters, the accumulated knowledge and the effort accounting, owns recovery, starts the next step **only on the planner's decision**, and runs the current step's cycle inline in its own session. A campaign is always single-threaded: one step at a time, one lane, no internal parallelism.

It receives the item's form, the incremental contract by exact ID, `preparation_ref`/`campaign_ref` and the dispatching rule from the caller; it does not choose the rule and does not classify the item. The contract/overlay of a **concrete step** is decided by `pdca-planner` for that step and persisted in the durable step record **before** the step; before the bootstrap it does not exist and the runner does not derive it.

An item with the form `cycle` is driven by its designated driver: it receives one already-planned cycle, executes it and returns the result; it does not own campaign advancement and does not advance anything else in the batch.

Collection owns the outer item completion commit; a campaign's `Commit policy: none` disables intermediate step commits, not that authorized outer commit.

The step semantics — the covered content of one step, the increment unit, the accepted negative candidate as knowledge, the absence of a forced second increment, the whole-goal final check and the claims veto — are the incremental contract's (`../pdca-incremental/SKILL.md` §Campaign invariants, §Campaign cycle, §Step boundary) plus the base phase exits; the collection adds neither a counter nor a gate.

### Lane pause

A lane pause is **derived** from `disposition=paused` of the current item and is not stored as a separate authoritative field of the lane. The item status stays the existing `in-progress`: a pause is not a new status value, and no new item/group statuses are introduced. A paused lane does not go on to the next dependent item of its group; the other groups continue.

### Lane liveness

Lane **liveness** is an observation, never a status: the item/group enumerations stay as they are and the status file remains the only progress mirror. Two readings decide it:

- **HEAD movement** — the lane's worktree HEAD or its `collection/<id>/group-<g>` / task-branch ref
  changes (a new commit, an amend, a reset, a merge): the ref id `git rev-parse <ref>` and its
  commit time `git log -1 --format=%cI`.
- **A running process of the lane** — its runner, `pdca-executor` or `pdca-check` is still alive.

Both readings are facts gathered **by the roles**, not by the driver: `pdca-executor` reads the refs and the process listing, `pdca-scout` observes the lane from outside. Commits in a lane accumulate at item boundaries (§One lane = one group), so a commit **tally** is not liveness: the count legitimately stands still while an item is being worked on, and it can grow from commits outside the lane. "The lane returned no result" (§The queue and the per-item continuation) is the lane's process ending without an outcome, not a quiet HEAD or an unchanged number of commits.

### Stale plan and schedule revision

Before starting DO the lane checks that the saved PLAN is applicable to the actual state (are the predecessors' outputs available, have the premises/assumptions changed). This is a narrow applicability check, not a mandatory repeated PLAN and not the driver deciding instead of `pdca-planner`.

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

The planned footprint is a **conservative reservation of the allowed surface for the whole item**, not a forecast of the exact edits and not the union of the first steps. A wide reservation is allowed and means less parallelism, not a wrong plan. If the disjointness of the footprints cannot be proven, the items go in one lane (are serialized): "probably they will not overlap" is not a basis. Going beyond the boundary stops the work.

The surface is issued by the collection PLAN; a campaign item's charter contains it as a subset, and a step cannot go beyond the campaign's surface. An extension of the reservation or of the surface after the barrier is stop/reapprove, i.e. an explicit renegotiation: `pdca-planner` of the collection PLAN (in normal mode — the user), taking into account the already started lanes and the already accepted results. There is no automatic `recluster`/`remerge`/`reset`/`revert`, an already integrated tip is not merged again, and the accepted steps are not recalculated.


## Collection status record

### File and content

File: `.pdca/status/collection-<slug>.md`. It contains:

- **Table shape.** Each table states its own header, and every row carries exactly those cells on
  one physical line: a note never contains a raw `|` and never wraps onto the next line, since either
  splits or truncates the queue; a status cell is one of the enumerations below and nothing else.
  `scripts/status_lint.py` enforces the shape on every write (§D.4).

- the input (the item list) and the `collection-id`; each item's goal/brief stays **verbatim**
  here and in its `## Original task`; later briefs reference that source exactly (base
  §Reference, not repetition);
- **Header caps.** `form: collection`, `plan_cap` and `lane_cap` (1–32, default **4**; below 4 needs
  `cap_reason:`) are recorded in the header. An unrecorded cap is 4, never 1; an old record gains the
  fields on its next write. `scripts/status_lint.py` rejects a `form: collection` record without both
  caps, a non-integer or out-of-range value, and a lowering without a reason — a sequential run is
  always an explicit choice;
- group table: id, items/order, worktree, branch/ref, **status** (`pending` | `in-progress` |
  `done` | `incomplete` | `merged`); only integrated `done` becomes `merged`. `incomplete` never
  merges and records stop reason ("the group is stopped"), tip/ref, preserved commits, remainder
  and patch path. `skipped` + reason is a separate integration note, not a status;
- the table of items: id, group, branch, status (`pending` | `in-progress` | `done` |
  `incomplete`) and a **separate** phase readiness of the plan `plan_state` (`pending` | `running`
  | `ready`), the item's **form** and (for `cycle`) its **contract** and **overlay**, `cycle_id`
  (including `N`), the canonical status path of the item, `plan_revision` (`r`), the baseline ref,
  the footprint/requirement/prerequisite refs, the reason + patch path for `incomplete`, a link to
  the item's status file, and the optional typed `terminal` column (§PLAN-terminal item projection).
  **The listed set is a minimum, not an exact schema.** A container may add columns the form needs —
  the `disposition` field, the typed `terminal` projection, an attempt counter — and
  `status_lint.py` validates whatever it carries; a **missing** listed column is the defect, an
  **additional** one never is, and a criterion that pins the column count exactly is over-specified:
  it bars the container from recording state the same contract elsewhere requires.
  `plan_state=ready` is plan readiness, not item execution status, approval or `done`; only groups
  can be `merged`;
- per item (both forms): `disposition` (`active` | `paused` | `finalized`) and pending step-approval
  refs. A `cycle` also has its contract/overlay and pending normal-mode approval ref. A `campaign`
  has `preparation_state` and its single authoritative `preparation_ref` (`.../preparation.md@r<k>`);
  `campaign_ref` is optional until the current-state step opens runtime, then required. Campaigns
  have no item contract: concrete step contract/overlay is in that step's durable record;
- readiness (`plan_state`/`preparation_state`), campaign runtime `Status`
  (`../pdca-incremental/SKILL.md` §Campaign status), and item `disposition` are distinct; readiness
  is neither runtime nor completion;
- an item record without a **form** is read as `cycle`; an unrecognised form value or an
  unresolvable contract/overlay — **fail closed**, not a guess;
- collection phase decisions (item PLANs, ALL-barrier, clustering, merge strategy) and schedule
  **PLAN revision vector**;
- the subsection **"General verification and recovery"** — the state of the **common verification**,
  not the status of a group or an item; the enumerations of groups/items are **not** extended by
  this:
  - last common `C` result and evidence paths (command, exit code, log, numbers);
  - blocking reason (no report / environment failure / confirmed defect) and state
    (`blocked` | `unverified` | `pass`);
  - **defect id/history**, applied fixes and each subsequent `C` result; identity persists across
    corrective-cycle closures/restarts;
  - a link to the status file of the linked corrective cycle;
  - the **next allowed step**;
- distinct fields for completeness (all original goals accepted), integrated-tree CHECK verdict,
  incomplete items and preserved results.
- a separate `## Lessons learned` section — `pending` at creation and finished in ACT as the one
  final retrospective of **`pdca-collection`'s own invocation**, completed **once per actually
  completed invocation** — never per revision, item or checkpoint for this section — after its substantive work reached
  a result and for **every** actually finalized outcome: accepted integration, verified partial
  integration, `blocked`/`incomplete`, terminal `STOP`, an early failure or a refusal. When the
  collection itself actually closes `blocked`/`incomplete`/`STOP` (or any other finalized outcome
  above), its retrospective **does** run; there is no parent-level pause status that would defer it.
  A child campaign's `running` status or `disposition: paused` checkpoint proves only that that item
  has not completed — it does not by itself complete the collection and is not a terminal parent
  outcome. An intermediate approval wait, an item/group closure, a checkpoint, a child pause, a
  session ending alone, a lane boundary, a child closure and a failed probe are **not** triggers by
  themselves. A premature exit before a status
  record exists still gets this one destination: `pdca-executor` creates the record in the authorized
  `form: collection` shape and fills the section; with no permitted destination or role available the
  driver reports an explicit **closure blocker** instead of skipping it. When an explicitly authorized
  already completed `form: collection` record is re-entered, its completed lesson entries are kept and
  the later invocation's own report is appended within the same `## Lessons learned`, tied to the
  existing `## Progress log` closure reference — no new counter, log, section or phase and no
  overwrite. It runs through the same configured `pdca-check` (`retrospective` mode, read-only) with
  the base CHECK+ACT retrospective contract and mode from `../pdca/references/act.md` and
  `../pdca/references/check.md` inlined **plus** the parent-only scope/output override below, which
  takes precedence over the generic cycle-task retrospective inputs and the general what-worked
  output; after freezing the originating result it adds no verdict,
  CHECK, verification, attempt, counter or DO work and never reopens the accepted result; it is final
  ACT bookkeeping, not a new PDCA phase or quality gate.
- **Parent-only scope of that retrospective.** The dispatcher input is the collection's own
  instructions, status record and own orchestration evidence — item decomposition, dependency
  DAG/groups/lane allocation, routing and handoffs, integration and verification orchestration and
  status bookkeeping, plus its own instructions as evidenced. It analyses only observed defects of
  this skill's own operation and evidenced instruction problems, never task/domain results (a bad task
  outcome is not automatically a skill defect), an item's own retrospective content, child lessons, or
  a summary/aggregation of them. A recorded parent-child interaction may evidence a parent
  routing/handoff error with attribution and uncertainty stated. Output: defects with evidence,
  effect, proposed change and uncertainty/limits, 0–3 transferable lessons in the base retrospective's
  shape, and `No skill-level defects found` only after actual analysis; it edits no skill, config or
  `AGENTS.md` and creates no parallel file, log, role, phase or counter. The driver only routes the raw
  report; `pdca-executor` persists it and completes the final ACT bookkeeping. If the dispatch is
  absent or fails, the section stays `pending` with the explicit **closure blocker**, the original
  result is preserved, and neither driver nor executor substitutes an analysis. No per-item,
  per-group or per-phase extra retrospective is created; an item cycle that itself reaches ACT keeps
  its own base skeleton.

### Campaign item status projection

`../pdca-incremental/SKILL.md` (§Campaign invariants, §Stop) defines campaign outcomes, whole-goal acceptance, pauses and resume. Collection only maps the campaign's persisted outcome and item `disposition` to its own item status:

- **Before campaign bootstrap** (including `preparation_state=ready`): `pending`.
- **Running or paused** (`disposition=active` | `paused`): `in-progress`;
  a pause stops progression within its group, not other groups.
- **Finalized with accepted `met`**: `done`.
- **Explicitly finalized without accepted `met`**: `incomplete` with reason;
  apply the existing group-stop rule. A failed step or a checkpoint alone
  never finalizes the item.

The collection's integration CHECK remains independent of campaign acceptance.

### PLAN-terminal item projection

The item enumeration stays `pending` | `in-progress` | `done` | `incomplete`; the PLAN-terminal distinction is a **typed column**, not a new status, and applies to `cycle` items only — a `campaign` item has no such row (its established step goes to independent CHECK, §Campaign item status projection).

- `terminal` — `execution` (the default when the column is absent or its cell is a placeholder, so
  every legacy record stays valid) or one of the three base causes: `criteria-undetermined`,
  `infeasible`, `already-established`.
- A plan-terminal row uses `incomplete`, keeps `plan_state` not `ready`, and records `attempts=0`
  (the `attempts` column is then required). `status_lint.py` rejects `done`, plan-ready, a
  consumed attempt, a missing `attempts` or `status` column, or an explicit `campaign` form.
- It is resolved for the barrier and the schedule — not `done`, not readiness, not a goal credit;
  full completion still requires that goal's own acceptance.
- It never triggers the group stop (only a final `incomplete` with `terminal=execution` does); the
  queue continues with the remaining items.
- The item's ACT carries the cause and evidence; the final summary counts accepted goals,
  plan-terminal resolutions and execution failures separately.

## Report

Follow base §Phase contracts → ACT and `../pdca/references/act.md`: report what was done, evidence, remaining/blocked work and next step. Distinguish collection completeness from integrated-tree verdict (§C), and accepted goals from plan-terminal resolutions and execution failures.

## Approval barrier (normal mode)

The shared approval rules are in `../pdca/SKILL.md` §Normal-mode approval, including the durable pending approval ref, same-ref approval record, applicability on resume and fresh approval after a substantive revision. The collection adds one handoff: the item driver returns its saved `plan_handoff` or `preparation_handoff` with the **pending approval ref** to the collection primary. The primary obtains the user's approval; the item driver cannot invent or infer it, and DO waits for the matching record. A paused item remains `in-progress` with `disposition=paused`; its lane does not advance to the next dependent item. Approval is separate from the preparation barrier, which requires **ready preparation** but not pre-approved DO.

In autonomous mode no ordinary plan approval is invented or required, but an explicit external/user permission requirement remains a blocker as in the base.

## Fallback

Host role and resource-blocker rules are inherited from `../pdca/SKILL.md` §Roles and host requirements. This section covers only driver fallback.

When an autonomous `pdca-orchestrator` is absent or cannot delegate, use the **flat cheap primary** as driver with `Notice:` and a durable reason, if the host permits it. It drives one current item per lane and delegates PLAN/DO/CHECK to their required roles; a campaign still has one designated driver for all steps. Independent groups may be processed concurrently up to the recorded `lane_cap` only if the host permits that concurrency; otherwise they are sequential, recorded as `cap_reason`. Normal mode already uses the primary driver and must not treat the lack of orchestrator delegation as a reason to skip approval. The fallback never promotes a driver into PLAN, CHECK, execution or expert-review authority.

Missing mandatory roles or forbidden fallbacks follow the base resource-blocker rules; collection preparation, barrier and handoffs remain unchanged.

## Parameters

| Parameter | Default |
|---|---|
| PLAN parallelism ceiling | `min(#items without a ready plan/charter, plan_cap)`; `plan_cap` is recorded in the status header, default 4 (unrecorded = 4, never 1; below 4 needs `cap_reason`) — a scheduling choice of this contract, not a host setting; only the common status write is serialized |
| Lane parallelism ceiling | `min(#groups, lane_cap)`; `lane_cap` is recorded in the status header, default 4 (below 4 needs `cap_reason`) — a scheduling choice of this contract, not a host setting; bounded by observed concurrency **and the declared host budget** (memory, measurement locks, containers) — a budget that cannot carry four lanes lowers `lane_cap` and records why, not discovered later as timeouts |
| Worktree directory | `<repo>-worktrees/<collection-id>/<group>` (not created with a single group) |
| Merge | `>=2` groups: after all lanes are terminal, `git merge --no-ff` of the `done` groups only, sequentially; not with one group; `incomplete` is not merged |
| One group | work in the current worktree/branch; no worktrees, branches or merge; `incomplete` keeps the commits already made |
| Autocommit/merge right | given by a project overlay or an explicit user request; the skill itself grants no right; `>=2` groups without the right — a preflight blocker before the allocation; one group may go in the current tree without commits if allowed; push never |

The roles, the tiers and their model bindings are the host's and the common contract's: this contract names roles only, carries no model id and adds no role.

## References

Load the **base `../pdca/SKILL.md` and this `SKILL.md` as separate reads on entry**, not as one concatenated tool output (the host may truncate at 50 KiB / 2000 lines). Load inherited form and base references when needed; a truncated contract must never be treated as complete:

- `../pdca/SKILL.md` — the **required common cycle contract** inherited here. Load with
  this skill; on shared rules the base is authoritative, including role boundaries,
  acceptance, verification, counters, approval, escalation, evidence and recovery.
- `../pdca-incremental/SKILL.md` — a campaign item: invariants, charter and status file, bootstrap,
  the step boundary, acceptance, the stop rules.
- `../pdca-coder/SKILL.md`, `../pdca-dotnet/SKILL.md` — the overlays applied to the relevant work.
- `../pdca/references/plan.md` — base planner-only phase detail; the driver supplies
  its exact absolute path, never loads or forwards it.
- `../pdca/references/check.md` — the base verdict/evidence contract; the driver reads it in full
  and inlines it in every item and integration `pdca-check` dispatch (CHECK cannot read it).
- `../pdca/references/act.md` — loaded by `pdca-executor` for cycle records
  and status updates; batch projections remain in §Collection status record.
