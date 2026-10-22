# A batch of tasks: how `pdca-collection` coordinates several PDCA cycles

## 1. The problem: one cycle — one task

The PDCA cycle (PLAN → DO → CHECK → ACT) is built as a discipline around **one** task with a
verifiable result: plan, do, verify, finish. While there is one task, all is well. But real work
rarely arrives one piece at a time. More often it is a **batch**: a list of tasks, a milestone (a
large goal split into items), a set of edits that can be done in parallel. Inside a batch the items
are sometimes independent, sometimes related, and sometimes two tasks reach into the same files.

If such a list is driven through a single PDCA cycle **sequentially**, you lose everything that
parallelism offers and stretch the work out. If several cycles are launched **by hand**, chaos
begins: the cycles compete for the same files, and it is unclear which branches are merged, which
were abandoned and which are still in progress. The answer to this problem is the `pdca-collection`
skill.

`pdca-collection` is a **stack-neutral level above the PDCA cycle**: a list of tasks split into
**groups**. It does not duplicate or redefine the base state machine and gates (the transitions
between the cycle's phases) but adds three things: clustering (splitting the list into parallel
groups), isolation (each group in its own working directory) and correct completion (merging only
what is genuinely done). Stack-neutrality means .NET is not required: any language and any task
with a verifiable result will do.

**When to pick `pdca-collection`:**

- you have a **batch of tasks with independent goals** or a milestone that must be taken through
  PDCA (a group may serialise tasks; parallelism is a schedule property, not an entry condition);
- the tasks are **independent** or fall into small related chains;
- their **footprint** (which files and modules they touch) mostly does not intersect — a shared
  footprint means fewer lanes, not a different contract;
- you want per-task acceptance and (optionally) a **parallel** run rather than one long chain.

**When not to pick it:** if there is exactly one task and no independent items, that is an ordinary
PDCA cycle (`pdca-coder`, `pdca-dotnet` or the universal `pdca`). An empty input is not a case for
the collection either: the right answer is to report that there is nothing to do.

## 2. Launching

The skill is invoked **explicitly by name** — `pdca-collection` — or by the phrase triggers that
describe precisely batch work: "**a task list**", "**a milestone**", "**parallel groups**" — they
are listed in the skill's description; the separation from the single cycle ("by the cycle" without
qualification leads into `pdca-coder`) is set by the host rule `AGENTS.md` of the `opencode-config`
repository, which is not part of this repository. The input is a list of tasks
**in any form**: no strict format is required, because splitting into groups is the collection
PLAN's job — and that only after each task has had its own PLAN, not yours.

## 3. Participants: the base roles plus one wrapper agent

The collection **introduces no new roles**. For `pdca-coder` and `pdca-dotnet`, `pdca-planner` still
plans, `pdca-executor` does, `pdca-check` renders the verdict, `pdca-escalate` escalates and `pdca-scout` gathers facts;
for the universal `pdca` the same roles are called `pdca-planner`, `pdca-executor`, `pdca-check` and
`pdca-escalate`, and facts are still gathered by `pdca-scout`. The only addition is the **wrapper agent
`pdca-orchestrator`** (the cheap tier), which runs **one** group: it drives that group as a single
parallel stream of work. It conducts each `cycle` task's own PLAN already in phase P (the
`COLLECTION TASK PLAN` input) and stops at the PLAN→DO boundary, handing control to the collection
(`plan_handoff`); in the lane **the same** cycle continues from DO — by default there is no second
PLAN. For a `campaign` unit the same input runs the **preparation** route (planner/scout/executor
produce the immutable preparation document) and returns a `preparation_handoff`; no unit-level
variant, baseline or future step plan is demanded there.

The wrapper has hard constraints, and this matters: `pdca-orchestrator` **does not make
decisions**. It does not decide that a task is infeasible, not ready or independent, does not choose
the scope and does not judge the result — any question is addressed to `pdca-planner` (in the PLAN
phase), not to the user. It also **does not edit files or run commands**: the infrastructure
(worktree, branches), `git merge` and the mandatory checks are performed by `pdca-executor` on the command
of the collection's **primary orchestrator** — that is who keeps the tracking, watches the gates and
makes the merge decision.

Separately, the **cycle variant is chosen per `cycle` unit**: `.NET/C#` → `pdca-dotnet`, other code →
`pdca-coder`, otherwise → the universal `pdca` (`pdca` by default). A `campaign` unit has no
unit-level `selected_variant`: its `pdca-planner` selects the concrete step variant by the
campaign's stack rule and persists it before the step. The base of `pdca-coder` and
`pdca-dotnet` is identical, so the collection really is stack-neutral. The top-level primary
orchestrator (the main session driving the whole collection) also does not edit files or run
commands.

## 4. How it works

### P — the tasks' own PLANs, the barrier, clustering

The order is strict: **first the real PLAN of every `cycle` task (or the preparation document of
every `campaign` unit), then the ALL-barrier, and only then the DAG and the groups.**
`pdca-orchestrator` conducts the route matching the unit's `execution_kind` in the
**COLLECTION TASK PLAN** input: for `cycle`, `pdca-scout` gathers facts, `pdca-planner` makes
decisions, `pdca-executor` persists the status, and the task stops at the PLAN→DO boundary with a
`plan_handoff`; for `campaign`, the same roles produce the immutable preparation document,
`preparation_state=ready` and the single `preparation_ref`, returning a `preparation_handoff`.
No code is written at this step. Until the own PLAN of **all** `cycle` tasks is ready
(`plan_state=ready`) and every `campaign` unit is `preparation_state=ready`, the DAG is not built
and an early DO is forbidden; a task without a meaningful plan remains a gap and does not pass the
barrier. A campaign unit does not need a unit-level `selected_variant`, baseline, runtime status,
future step plans or a step count at the barrier.

Planning is not serialized: `COLLECTION TASK PLAN` may be dispatched for every unit without a
ready plan at once, up to `plan_cap` (4 by default); the barrier constrains the **start** of the
DAG and the lanes, not the order of the PLANs. The writes of the collection status file are
serialized — the primary/`pdca-planner` sets the semantics of the rows and `pdca-executor` performs
the physical write — only the rows go in one at a time, not the planning itself.

A parallel PLAN does not fix the schedule: the groups and the order are decided only after the
barrier, so a sequential chain of tasks inside one group is a normal outcome. Code overlap is
resolved there too: a footprint reservation is a claim for clustering, not a lock — a PLAN
*declares* the write footprint and its uncertainty without blocking other plans. Intersecting
footprints do not prevent parallel planning — they forbid parallel **lanes**: such units land in
one group and run sequentially, and the footprints of the groups do not intersect after clustering.

Separately, the contract closes the **re-entry** case: after a terminal `incomplete`/STOP the
previous terminal cause is a **mandatory input** to the task's own PLAN, and `pdca-planner` either proves
that the failed evidence is now obtainable or redefines the oracle. A silent re-run of the same
criterion is forbidden — otherwise the task again remains a gap.

After the barrier, contradictions from the handoff metadata (the planned footprint, requirements on
predecessors' results, assumptions) are validated, and `pdca-planner` builds the **DAG** — a directed
acyclic dependency graph — and cuts it into groups. A group is a connected component or a line by
dependencies and shared files; the **footprints of the groups do not intersect**, and inside a group
the tasks are ordered **topologically** (those that others depend on come first). The list of
groups, the order and the PLAN revision vector are kept in the collection status file.

The last step of phase P is recording the schedule in the **collection status file**, and that
file is the **only progress mirror**: there is no separate todo or sidebar mirror, since the host
may not provide a todo tool (V2 does not), and a second mirror only creates divergence. The primary
orchestrator updates the file in the same turn as the event, reconciles against it before
dispatching, and restores the state from it after compaction — never from memory. The groups and
tasks with their statuses live in the status-file tables.

If the result is a **single** group, that is not a failure but a **degradation to one lane**: no
isolation is needed (see below). The current branch's existing commits stay in place.

### D — infrastructure, tracking and merging

The lanes (worktrees, group/task branches, executors) are allocated **only** after the ALL-barrier
and a persistent binding of the schedule — before that step they do not exist. With **two or more**
groups, `pdca-executor` creates for each its own **worktree** — an isolated working copy of the repository
in a separate directory `<repo>-worktrees/<collection-id>/<group>` — and its own branch
`collection/<id>/group-<g>`. Inside a group the tasks go **sequentially**: a task branch
`collection/<id>/task-<g>-<k>` branches off the **committed tip** (the last commit) of the previous
task. Each task enters the lane already with its own PLAN ready: `pdca-orchestrator` checks the
plan's applicability to the current state and continues **that same** cycle from DO (without
launching a new PLAN).

The groups run in parallel — one `pdca-orchestrator` per group, no more than **cap** at a time. By
default `cap = 4` (configurable), and the actual ceiling is `min(#groups, cap)`. After each task, in
the permitted mode, `pdca-executor` makes an **auto-commit** — and only of the task's files (`git add
<paths>`, never `git add -A`, so as not to pick up someone else's). With one group, no worktree,
group/task branches or merging are created: the work goes on in the current directory on the current
branch.

The key element is the **merge barrier**. Merging begins only when **all** lanes (parallel streams
of work) have reached a terminal state: `done`, or `incomplete` with an explicit outcome; a running
lane is not merged early. Readiness here means **terminality, not success**. After that, `pdca-executor`
sequentially runs `git merge --no-ff` (a merge with a forced merge commit, to preserve the branch
history) **only for the `done` groups**; for issue tasks the merge message begins with `#<n>`. A
successfully merged group goes `done` → `merged`. An `incomplete` group is **never merged**, even if
it had successful tasks and commits before the failure: its tip does not enter the integration.

If a merge conflicts, `pdca-executor` runs `git merge --abort` (rolling back the unfinished merge). The
group is **escalated**: `pdca-escalate` (the strong role) decides — to resolve manually, to reorder, or
to mark the group `incomplete`. The escalation **does not execute**: a decision to "resolve
manually" or "reorder" returns control to the merge phase, and the orchestrator itself dispatches
`pdca-executor` to repeat `git merge --no-ff` on the **unmerged** tip. The order can only be changed for
groups not yet integrated; previously merged tips are not touched — no rerun/reset/revert/remerge. A
repeated conflict again leads to `abort` and an escalation, with no new attempt counter.

### C — the common verification

The collection's common verification is the **standard CHECK of the base contract** (two beats: a
cheap gathering of raw measurements → the `pdca-check` verdict), not a separate home-made stage. The full
CHECK of the parent collection runs when all the selected `done` groups are integrated and there is
no active conflict or unfinished merge state. The orchestrator **always** — even when all checks are
green — gathers through `pdca-executor` and `pdca-scout` the mandatory reports (tests universally plus checks by
type of work: build/linter for code, rendering for design and presentations, measurements if there
is a hot path, and the review lenses' reports) and passes the aggregate to `pdca-check`. Raw
measurements never decide a PASS by themselves: the verdict is rendered by `pdca-check`.

**A PASS can coexist with `incomplete` groups.** The completion report (how many tasks and groups
were carried through) and the verification verdict of the integrated tree are separate fields. Even
if there are no selected `done` groups, the standard check is still performed on the integrated
tree, and the original tasks are not marked `done` retroactively.

If the check finds a **real defect**, a **standard corrective task** is opened on the current
integrated tree/branch (the cycle variant by the general task-selection rule) with its own linked
status file. Its ACT returns control to the **full** parent CHECK — all mandatory gates are re-run,
not just the failed test. If a mandatory report is missing, unreliable, or the environment broke,
that is **not a code defect** and no reason to edit code: a **re-gather** (a repeated gathering of
the report) is performed, and the check state may remain `blocked`. The revision/escalation rules
are the base ones (`r`, `n/3`), with no collection counter.

### A — completion

Completion is permitted **only by a PASS of the common verification**. The report lists the groups,
tasks, branches, `merged`/`incomplete`, the evidence and the outcome of the corrective tasks.
`pdca-executor` removes **only the one-off** worktrees and temporary group/task branches that are
`done`/`merged`. The worktrees, branches, commits and patches (applied "band-aids" with uncommitted
changes) of **`incomplete` groups are never deleted**: their refs (branch pointers), patch paths,
status and evidence paths are preserved — most simply, leave everything in place and record that
explicitly in the status. While the check is red, there is no success and no cleanup. **STOP before
a PASS — no cleanup.**

## 5. A teaching scenario (marked)

> Below is a **teaching example**, not a description of a real run.

Imagine a collection of three groups: A, B, C. Group B, on its second task, hits an impossibility by
the contract. The failure first goes to `pdca-planner` (PLAN): it tries to return to DO (the base
contract's usual loop-back and counters) and, having failed, **finally** closes the task as
`incomplete` — `pdca-executor` saves its changes as a patch, returns only its paths to the last green tip,
and writes the reason into the status.

What happens next is the main idea:

- **a final `incomplete` stops the whole group**: `pdca-orchestrator` does not take the next task;
  all remaining `pending` tasks of group B are marked `incomplete` with the reason "the group is
  stopped" and are **not executed**;
- **group B's already-made commits and the failed task's patch are preserved**;
- **group B is not merged** — its tip does not enter the integration;
- **the other groups (A and C) keep working**: one group stopping does not stop the other lanes.

When all lanes are terminal, the merge barrier passes only groups A and C (if they are `done`): they
are merged sequentially with `git merge --no-ff` and go `done` → `merged`. Group B stays
`incomplete`. The common verification is performed on the integrated tree — and its verdict
describes the **integrated result**, while the completion report honestly says that some groups were
not carried through.

## 6. Limitations and false expectations

- **Readiness ≠ success.** The merge barrier waits for all lanes to be terminal, but that does not
  mean they all succeeded. `incomplete` is a normal terminal outcome.
- **`incomplete` is never merged**, even with successful commits inside. Its results are preserved
  as refs/commits/patch, but do not enter the integration.
- **The skill itself does not grant the right to commit/merge.** Permission for auto-commits on
  `collection/**` branches and for `merge --no-ff` is given by the **project overlay** (for example,
  a project rule) or by an **explicit user request**; the skill does not extend global `AGENTS.md`.
  For **`>=2` groups** a known incompatibility (an explicit no-commit request, commits/merge
  unavailable or forbidden) is a **preflight blocker before worktrees/lanes are allocated** — a
  group that knowingly cannot make the mandatory tips is not executed. Missing permission is not
  authorization. A **single group** may work in the current tree without commits if that is
  permitted; it needs no git integration. If permission is revoked mid-lane, the run takes a safe
  stop, preserving refs and commits and saving the uncommitted task/group changes as a patch;
  `incomplete` follows only an explicit terminal outcome, and no further branch-chain work is done.
- **Push — never.** That is not part of the collection in any mode.
- **Merge conflict → abort → escalate.** There is no automatic "resolution" of a conflict; an
  escalation only returns a decision, and `pdca-executor` executes again.
- **`blocked` is not a group or task status.** It is a state of the common verification: groups and
  tasks have no `blocked` status; `incomplete` is a consequence of a contract failure, not a lane's
  judgement. A group has exactly five statuses — `pending`, `in-progress`, `done`, `incomplete`,
  `merged`; `skipped` ("not selected for integration") is an integration note, not a status; a task
  never has `merged`.
- **The two failure mechanisms are not mixed.** A task's terminal `incomplete` inside a lane is a
  single task's failure and a decision of that cycle's `pdca-planner`; a STOP of a corrective task is a
  recurrence of a defect of the **common** verification under the base `r`/`n`.
- **No automatic rerun/remerge/recluster/reset/revert** and no new branch chains; a corrective task
  is a separate record, not an extra lane.
- **The success of a corrective task does not mean the collection succeeded.** On a STOP without an
  admissible revised plan, the collection remains `unverified` and the original tasks keep their
  previous statuses.
- **Fallback.** The flat primary kicks in when `pdca-orchestrator` is unavailable: the agent is
  absent, `subagent_depth` < 2, or the host forbids a subagent to delegate (no nested
  delegation). Then there is no one to orchestrate, and the primary takes the groups on itself: it
  drives **one current task per group**, starting the next when the previous finishes. Independent
  groups keep the allowed parallelism — up to `cap` groups at once when the host permits it; if the
  host provides no concurrency, the same fallback runs the groups sequentially (`cap` is an upper
  bound, not a guarantee). Fallback substitutes the driver only, never a required role. In phase P
  it likewise conducts each unit's `COLLECTION TASK PLAN` itself — the own PLAN of a `cycle` or the
  preparation route of a `campaign` — respecting the ALL-barrier, and continues the saved PLAN in
  the lane from DO. In autonomous mode the fallback is marked with a `Notice:` line and the recorded
  reason, in normal mode with a message to the user; a host prohibition is not bypassed.

## 7. Composition: a batch may contain campaigns

A batch is not obliged to consist of single cycles. The collection works with **units**, and a
unit's form of execution is `execution_kind` with exactly two values: `cycle` — one full
PLAN → DO → CHECK → ACT of its variant, with `plan_state` and `selected_variant`; and `campaign` —
an incremental campaign with its own goal, frame, runtime status and steps, with **no** unit-level
`selected_variant` and no "campaign domain". `execution_kind` and `selected_variant` are different
fields: the collection PLAN (`pdca-planner`) decides the form, the runner only reads the ready value
(`opencode/pdca-collection/SKILL.md §Collection units and the execution form`). A step of a campaign is
only a cycle of the family: neither "a campaign in a campaign" nor "a collection inside a campaign"
(nor a collection inside a collection) is expressible.

**The barrier asks each unit for what that unit has.** A `cycle` unit presents the real PLAN of that
cycle (`plan_state=ready`). A `campaign` unit presents an approved separate immutable/revisioned
**preparation document** — `.pdca/<collection-id>/units/<unit-id>/preparation.md` — with the nine
frame items, `preparation_state=ready` and a **single authoritative** `preparation_ref` of the form
`<path>@r<k>` in the unit record. `campaign_ref`, the pointer to the campaign runtime status, may be
absent before the baseline bootstrap and is mandatory after it; it is not a pointer to the frame and
does not replace `preparation_ref`. The barrier needs no baseline evidence, no `running` runtime
status, no future step plans, no future step variants and no number of steps; before the barrier no
lane is allocated for either kind
(`opencode/pdca-collection/SKILL.md §P — per-task PLANs, the barrier, clustering`).

**Baseline bootstrap happens after the barrier.** A dedicated `pdca-executor` creates the baseline
evidence by the frame's recipe and the campaign runtime status `Status: running`, mentioning
`preparation_ref` and writing `campaign_ref`. It is not a step, is not credited and does not change
the product; the preparation records before the barrier are allowed, while a substantive bootstrap
and a change-producing DO are not. The runtime stores `preparation_ref` as a **reference**, not as a
copy of the frame. A **preparation revision** is admissible only for the method, schedule, surface
bounds or other frame parts **compatible with unchanged goal/recipe/threshold/floor and already
given approvals**; it goes through `pdca-planner` and the active approval, creates a new immutable
revision, updates `preparation_ref` and keeps the previous one. Changing the **goal, measurement
recipe, threshold or floor** is not a revision: it is a **new campaign with a new baseline** and a
new frame/unit, even when the collection id stays. Silent weakening and backfill of accepted
criteria are forbidden; old immutable revisions are never rewritten
(`opencode/pdca-incremental/SKILL.md §Campaign status file`).

**Readiness is not completion.** `preparation_state=ready` without a runtime is `barrier-ready`, not
`started`: the unit stays `pending` and never becomes `done` because the frame is ready. Only an
accepted `met` with an explicit `disposition=finalized` gives `done`
(`opencode/pdca-collection/SKILL.md §A.1 Routing campaign outcomes`).

**Pause is not final.** `blocked`, `stopped` and `unreachable` with an admissible next target within
an unchanged goal and bounds are a checkpoint: `disposition=paused`, the unit stays `in-progress`,
and a resume is explicit. A final `incomplete` — and the existing group-stop it triggers, where the
remaining `pending` units of the group are marked `incomplete` and are not executed — requires an
explicit final unsuccessful disposition and is not derived from a pause. There is no endless
automatic retry; pause and resume do not reset `N`/`r`/`n`; a paused lane does not advance its
group's dependent chain, while the other groups continue; the success criteria are never changed
silently (`opencode/pdca-collection/SKILL.md §A.1 Routing campaign outcomes`).

**Disposition, and the derived lane pause.**
`disposition` (`active` | `paused` | `finalized`) is a per-unit field, not a task or group status.
The lane pause is **derived** from the current unit's `disposition=paused` and is not stored as a
separate authoritative lane field; no new status value is introduced, and `blocked` stays a state of
the common verification (`opencode/pdca-collection/SKILL.md §Lane pause`).

**Three separate state spaces.** Unit readiness (`plan_state` / `preparation_state`), the campaign
runtime status (`Status`) and the per-unit `disposition` are different things, each with its own file
and its own identifiers: the collection status, the preparation document, the campaign runtime status
and the step's own cycle status. The semantics of a record belong to the primary/`pdca-planner`; the
physical write is done by `pdca-executor` on an explicit dispatch
(`opencode/pdca-collection/SKILL.md §Collection status`).

**The surface belongs to the collection.** The planned footprint is a **conservative reservation of
the allowed surface for the whole task**, not a forecast of the exact edits and not the union of the
first steps; a wide reservation is admissible and means less parallelism, not a wrong plan. The
campaign frame contains the surface as a subset, and a step cannot leave the campaign's surface.
Expanding the reservation or the surface after the barrier is a stop/reapproval: an explicit
renegotiation by the collection's `pdca-planner` (in normal mode — the user), taking the already
started lanes and the already accepted results into account, with no automatic
`recluster`/`remerge`/`reset`/`revert`
(`opencode/pdca-collection/SKILL.md §Surface reservation and its extension`).

**The driver is the same cheap runner.** In a collection the campaign is led by the existing
`pdca-orchestrator` in `mode=collection-lane`: it receives the unit's `execution_kind`, the loaded
campaign contract, the `preparation_ref`/`campaign_ref` and the **dispatch selection rule supplied
by the caller** (the campaign's stack rule; the runner does not choose it), and leads the campaign
state machine and the current step's cycle **inline** in one lane session. There is no campaign
agent and no new `Task` level; a campaign is always sequential — one step at a time, one lane, no
internal parallelism. The concrete step variant is selected by `pdca-planner` per the stack rule and
persisted in the durable step record before the step, not before bootstrap.

In normal mode every actual step passes a full PLAN of its variant. The driver may plan, but it
**never obtains or assumes approval** and never starts the gated DO without the matching recorded
approval: `pdca-executor` persists a durable pending approval ref bound to the stable
task/`cycle_id`, the exact `N`/`r`/criteria set (`N` is not globally unique), the driver returns a
checkpoint to the primary, the primary asks the user, and the executor records the approval against
the same ref. Resume validates the match and first checks applicability through the roles: an
applicable plan continues the **same** step; a stale plan gets a genuine planner revision and a
**fresh approval**, which the stale approval never authorizes. Approval resume does not
unconditionally replan or add a step; the unit is `disposition=paused` / `in-progress` while
waiting, not `done`/`incomplete`, and compaction is safe
(`opencode/pdca-collection/SKILL.md §Lane driver and campaign (mode=collection-lane) · §Approval protocol (normal mode)`).

**Completion and commits stay on the collection's level.** The campaign's acceptance (`met`) and the
collection's common verification are different events: a campaign's success does not replace the
common CHECK on the integrated tree. The external commit/branch lifecycle of a unit belongs to the
collection; `Commit policy: none` means no intermediate step commits and does not forbid the outer
completion commit, and an explicit no-commit restriction that conflicts with the mandatory git model
is a preflight blocker before the lanes are allocated
(`opencode/pdca-collection/SKILL.md §Git model`).

**Preflight and fallback.** Before lanes are allocated and before a campaign starts in its lane, the
host's observable capability is checked: the mandatory roles and contracts, nested delegation for the
driver, `pdca-orchestrator` itself and the `escalate → scout` edge — with no dummy substantive work
and no invented host number. Exactly one fallback exists: if the lane driver is unavailable, the flat
cheap primary drives the work itself, one current task per group; independent groups keep the
allowed parallelism up to `cap` when the host permits, otherwise the fallback serializes them,
marking this with a `Notice:` line and a durable reason, still dispatching the roles and not
acquiring their rights. An unavailable **mandatory role** is a resource stop of the run; an
unavailable **cycle contract** fails closed without substituting a "similar" variant; a late
discovery is a safe pause before the dependent action, not a weakened gate
(`opencode/pdca-collection/SKILL.md §Fallback`).

## 8. Where to go next

- The full text of the skill, its role (the wrapper agent `pdca-orchestrator`, the `COLLECTION TASK
  PLAN` input, the group lane), the P/D/C/A phases, the status, the git model and the failure
  semantics —
  [`opencode/pdca-collection/SKILL.md`](../opencode/pdca-collection/SKILL.md). The runner ships as
  [`assets/agents/pdca-orchestrator.md`](../opencode/pdca-collection/assets/agents/pdca-orchestrator.md);
  the profiles and `AGENTS.md` remain host artifacts of the `opencode-config` repository.
- The cycle base: [`opencode/pdca-coder/SKILL.md`](../opencode/pdca-coder/SKILL.md) (for .NET, the
  identical base [`opencode/pdca-dotnet/SKILL.md`](../opencode/pdca-dotnet/SKILL.md)).
  The family's neighbouring articles: [`pdca.md`](pdca.md) — the domain-neutral core,
  [`pdca-coder.md`](pdca-coder.md) and [`pdca-dotnet.md`](pdca-dotnet.md) — the engineering
  variants, and [`pdca-incremental.md`](pdca-incremental.md) — the campaign that can become a unit
  of a batch.
- The contract checks — [`opencode/pdca-collection/tests/`](../opencode/pdca-collection/tests/):
  tests of the skill's text and the diagram rendering, plus a scenario matrix **marked as
  static** (not proof of behaviour); the diagram — `assets/diagram/` (generator
  `gen_collection.py`).
- An overview of the whole family is the guide [`docs/pdca-guide.md`](pdca-guide.md).

## Sources

The "claim → source" map. The article's normative claims were reconciled with the repository's
current files (commit `a58f338`); where they disagree, `opencode/pdca-collection/SKILL.md` takes
precedence.

| Claim in the article | Source |
| --- | --- |
| The top-level role and stack-neutrality; the cycle variant is chosen per task; the own PLAN stops at the PLAN→DO boundary and continues in the lane; the primary does not edit files | `opencode/pdca-collection/SKILL.md §Role` |
| Auto-commit only by project overlay or explicit request; `push` never; the one-group mode | `opencode/pdca-collection/SKILL.md §Role` |
| P: each task's own PLAN before the DAG, the ALL-barrier, a gap without a `ready` placeholder, groups go to `pdca-planner`, the revision vector, lane allocation only after the schedule is bound; parallel PLANs up to `plan_cap` that do not fix the schedule, a serialized status-file write; a re-entry after a terminal `incomplete`/STOP requires proof or a new oracle | `opencode/pdca-collection/SKILL.md §P — per-task PLANs, the barrier, clustering` |
| P: the status file as the only progress mirror (per-group and per-task tables), one group → one lane, an empty input | `opencode/pdca-collection/SKILL.md §P — per-task PLANs, the barrier, clustering` |
| D: worktrees and branches, cap, schedule binding, the merge barrier, `done → merged`, `#<n>` in the merge message, `incomplete` is not merged, conflict/abort/escalation; the five group statuses, `skipped` as an integration note, `blocked` is not a status | `opencode/pdca-collection/SKILL.md §D — infrastructure, tracking, merge` |
| C: the standard two-beat CHECK, the mandatory reports and review lenses, the full check after all selected `done` groups are integrated, a PASS alongside `incomplete`, the corrective task, re-gather, the base `r`/`n`, STOP and `unverified`; the mechanism of a task's `incomplete` in a lane is not mixed with a STOP of a corrective task | `opencode/pdca-collection/SKILL.md §C — verification (the standard CHECK)` |
| A: completion only by a PASS, the report's composition, cleanup only of `done`/`merged`, preservation of `incomplete` results and of status/evidence paths, STOP | `opencode/pdca-collection/SKILL.md §A — completion` |
| The lane: task branches off the tip, continuing the saved PLAN from DO, stopping the group, preserving commits/patch, other groups continuing, `blocked` is not a group status | `opencode/pdca-collection/SKILL.md §Lane (work stream)` |
| A stale plan and schedule revision (reopening PLAN, the ban on auto-recluster after the lanes start) | `opencode/pdca-collection/SKILL.md §Stale PLAN and schedule revision` |
| The git model: 1 worktree per group, ff advancement, sibling refs, `--no-ff` merge, the tip | `opencode/pdca-collection/SKILL.md §Git model` |
| The failure semantics (table) and the collection status with invariants (`plan_state`, `merged`, `skipped`, `blocked`, evidence preservation) | `opencode/pdca-collection/SKILL.md §Failure (semantics) · §Collection status` |
| Parameters: `cap = 4` for lanes, `plan_cap = 4` for the PLAN phase, the worktree directory, the merge right | `opencode/pdca-collection/SKILL.md §Report · §Parameters` |
| The fallback (flat primary, including COLLECTION TASK PLAN and continuing the saved PLAN) | `opencode/pdca-collection/SKILL.md §Relation to the base PDCA · §Fallback` |
| Composition: the two execution forms (`execution_kind` ≠ `selected_variant`), the recursion ban, the form decided by the collection PLAN | `opencode/pdca-collection/SKILL.md §Collection units and the execution form` |
| The barrier by unit kind, the separate immutable/revisioned preparation document, `preparation_state`, the single `preparation_ref`, `campaign_ref` optional before and mandatory after the bootstrap, the three operations, readiness ≠ completion, renegotiation as a new revision | `opencode/pdca-collection/SKILL.md §P — per-task PLANs, the barrier, clustering · §A.1 Routing campaign outcomes`; `opencode/pdca-incremental/SKILL.md §Campaign status file` |
| `met` as the only success, pause vs final, the explicit final unsuccessful disposition and the group-stop, the per-unit `disposition` and the derived lane pause, the separate readiness/runtime/disposition spaces | `opencode/pdca-collection/SKILL.md §A.1 Routing campaign outcomes · §Lane pause · §Collection status` |
| The collection-lane driver (the same `pdca-orchestrator`, the campaign inline, one lane) and the step's PLAN/approval | `opencode/pdca-collection/SKILL.md §Lane driver and campaign (mode=collection-lane)` |
| Surface ownership and the conservative whole-task reservation; expansion as stop/reapproval | `opencode/pdca-collection/SKILL.md §Surface reservation and its extension` |
| Commits: the collection owns the external lifecycle, `Commit policy: none` and the preflight blocker | `opencode/pdca-collection/SKILL.md §Git model` |
| Preflight and the single fallback (`Notice:` + durable reason, resource stop, fail closed) | `opencode/pdca-collection/SKILL.md §Fallback` |
| The role tiers (cheap: `pdca-orchestrator`/`pdca-scout`/`pdca-executor`; medium: `pdca-planner`/`pdca-check`; strong: `pdca-escalate`) | `opencode/pdca-collection/assets/diagram/gen_collection.py:800-803` |
| The cycle base: the two-beat CHECK, the `N`/`r`/`n/3` counters, escalation, the autonomous fallback and `Notice:`; the role names of the universal variant (`pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`) | `opencode/pdca-coder/SKILL.md §Host requirements (roles → agents) · §Orchestrator role · §State machine · §Worktree sub-tasks of one cycle: subagent prompt template · §Escalation (pdca-escalate) · §Frozen evidence manifest · §CHECK: audit checklist (generic)` (for .NET, the identical base `opencode/pdca-dotnet/SKILL.md §Host requirements (roles → agents) · §Orchestrator role · §State machine · §Worktree sub-tasks of one cycle: subagent prompt template · §Escalation (pdca-escalate) · §Reviewer evidence pack (independent CHECK over full bodies)`); `opencode/pdca/SKILL.md §Host requirements (roles → agents), :22-36` |
| The contract texts are checked by tests, and the scenario matrix is marked as static (not proof of behaviour); the host artifacts (the `pdca-orchestrator` prompt runner, the profiles, `AGENTS.md`) are outside this repository | `opencode/pdca-collection/tests/test_plan_barrier.py` (including `:33-38`), `tests/test_verification_recovery.py`, `tests/scenarios.md` |
