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

- you have a **batch of tasks** or a milestone that must be taken through PDCA;
- the tasks are **independent** or fall into small related chains;
- their **footprint** (which files and modules they touch) mostly does not intersect;
- you want a **parallel** run rather than a long sequence.

**When not to pick it:** if there is exactly one task and no independent items, that is an ordinary
PDCA cycle (`pdca-coder`, `pdca-dotnet` or the universal `pdca`). An empty input is not a case for
the collection either: the right answer is to report that there is nothing to do.

## 2. Launching

The skill is invoked **explicitly by name** — `pdca-collection` — or by the phrase triggers that
describe precisely batch work: "**список задач**", "**milestone**" / "**милстоун**", "**параллельные
группы**" — they are listed in the skill's description; the separation from the single cycle ("по
циклу" without qualification leads into `pdca-coder`) is set by the host rule `AGENTS.md` of the
`opencode-config` repository, which is not part of this repository. The input is a list of tasks
**in any form**: no strict format is required, because splitting into groups is the collection
PLAN's job — and that only after each task has had its own PLAN, not yours.

## 3. Participants: the base roles plus one wrapper agent

The collection **introduces no new roles**. For `pdca-coder` and `pdca-dotnet`, `planner` still
plans, `coder` does, `check` renders the verdict, `escalate` escalates and `scout` gathers facts;
for the universal `pdca` the same roles are called `pdca-planner`, `pdca-executor`, `pdca-check` and
`pdca-escalate`, and facts are still gathered by `scout`. The only addition is the **wrapper agent
`pdca-orchestrator`** (the cheap tier), which runs **one** group: it drives that group as a single
parallel stream of work. It conducts each task's own PLAN already in phase P (the `COLLECTION TASK
PLAN` input) and stops at the PLAN→DO boundary, handing control to the collection
(`plan_handoff`); in the lane **the same** cycle continues from DO — by default there is no second
PLAN.

The wrapper has hard constraints, and this matters: `pdca-orchestrator` **does not make
decisions**. It does not decide that a task is infeasible, not ready or independent, does not choose
the scope and does not judge the result — any question is addressed to `planner` (in the PLAN
phase), not to the user. It also **does not edit files or run commands**: the infrastructure
(worktree, branches), `git merge` and the mandatory checks are performed by `coder` on the command
of the collection's **primary orchestrator** — that is who keeps the tracking, watches the gates and
makes the merge decision.

Separately, the **cycle variant is chosen per task**: `.NET/C#` → `pdca-dotnet`, other code →
`pdca-coder`, otherwise → the universal `pdca` (`pdca` by default). The base of `pdca-coder` and
`pdca-dotnet` is identical, so the collection really is stack-neutral. The top-level primary
orchestrator (the main session driving the whole collection) also does not edit files or run
commands.

## 4. How it works

### P — the tasks' own PLANs, the barrier, clustering

The order is strict: **first the real PLAN of every task, then the ALL-barrier, and only then the
DAG and the groups.** `pdca-orchestrator` conducts the task's own PLAN phase (of its variant) in the
**COLLECTION TASK PLAN** input: `scout` gathers facts, `planner` makes decisions, `coder` persists
the status. The task stops at the PLAN→DO boundary and hands control to the collection (a
`plan_handoff`); no code is written at this step. Until the own PLAN of **all** tasks is ready
(`plan_state=ready`), the DAG is not built and an early DO is forbidden; a task without a
meaningful plan remains a gap and does not pass the barrier.

Separately, the contract closes the **re-entry** case: after a terminal `incomplete`/STOP the
previous terminal cause is a **mandatory input** to the task's own PLAN, and `planner` either proves
that the failed evidence is now obtainable or redefines the oracle. A silent re-run of the same
criterion is forbidden — otherwise the task again remains a gap.

After the barrier, contradictions from the handoff metadata (the planned footprint, requirements on
predecessors' results, assumptions) are validated, and `planner` builds the **DAG** — a directed
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
groups, `coder` creates for each its own **worktree** — an isolated working copy of the repository
in a separate directory `<repo>-worktrees/<collection-id>/<group>` — and its own branch
`collection/<id>/group-<g>`. Inside a group the tasks go **sequentially**: a task branch
`collection/<id>/task-<g>-<k>` branches off the **committed tip** (the last commit) of the previous
task. Each task enters the lane already with its own PLAN ready: `pdca-orchestrator` checks the
plan's applicability to the current state and continues **that same** cycle from DO (without
launching a new PLAN).

The groups run in parallel — one `pdca-orchestrator` per group, no more than **cap** at a time. By
default `cap = 4` (configurable), and the actual ceiling is `min(#groups, cap)`. After each task, in
the permitted mode, `coder` makes an **auto-commit** — and only of the task's files (`git add
<paths>`, never `git add -A`, so as not to pick up someone else's). With one group, no worktree,
group/task branches or merging are created: the work goes on in the current directory on the current
branch.

The key element is the **merge barrier**. Merging begins only when **all** lanes (parallel streams
of work) have reached a terminal state: `done`, or `incomplete` with an explicit outcome; a running
lane is not merged early. Readiness here means **terminality, not success**. After that, `coder`
sequentially runs `git merge --no-ff` (a merge with a forced merge commit, to preserve the branch
history) **only for the `done` groups**; for issue tasks the merge message begins with `#<n>`. A
successfully merged group goes `done` → `merged`. An `incomplete` group is **never merged**, even if
it had successful tasks and commits before the failure: its tip does not enter the integration.

If a merge conflicts, `coder` runs `git merge --abort` (rolling back the unfinished merge). The
group is **escalated**: `escalate` (the strong role) decides — to resolve manually, to reorder, or
to mark the group `incomplete`. The escalation **does not execute**: a decision to "resolve
manually" or "reorder" returns control to the merge phase, and the orchestrator itself dispatches
`coder` to repeat `git merge --no-ff` on the **unmerged** tip. The order can only be changed for
groups not yet integrated; previously merged tips are not touched — no rerun/reset/revert/remerge. A
repeated conflict again leads to `abort` and an escalation, with no new attempt counter.

### C — the common verification

The collection's common verification is the **standard CHECK of the base contract** (two beats: a
cheap gathering of raw measurements → the `check` verdict), not a separate home-made stage. The full
CHECK of the parent collection runs when all the selected `done` groups are integrated and there is
no active conflict or unfinished merge state. The orchestrator **always** — even when all checks are
green — gathers through `coder` and `scout` the mandatory reports (tests universally plus checks by
type of work: build/linter for code, rendering for design and presentations, measurements if there
is a hot path, and the review lenses' reports) and passes the aggregate to `check`. Raw
measurements never decide a PASS by themselves: the verdict is rendered by `check`.

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
`coder` removes **only the one-off** worktrees and temporary group/task branches that are
`done`/`merged`. The worktrees, branches, commits and patches (applied "band-aids" with uncommitted
changes) of **`incomplete` groups are never deleted**: their refs (branch pointers), patch paths,
status and evidence paths are preserved — most simply, leave everything in place and record that
explicitly in the status. While the check is red, there is no success and no cleanup. **STOP before
a PASS — no cleanup.**

## 5. A teaching scenario (marked)

> Below is a **teaching example**, not a description of a real run.

Imagine a collection of three groups: A, B, C. Group B, on its second task, hits an impossibility by
the contract. The failure first goes to `planner` (PLAN): it tries to return to DO (the base
contract's usual loop-back and counters) and, having failed, **finally** closes the task as
`incomplete` — `coder` saves its changes as a patch, returns only its paths to the last green tip,
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
  Without permission there are no commits or merges: the group proceeds without them, unfinished
  results are saved as a patch, and the group is marked `incomplete`.
- **Push — never.** That is not part of the collection in any mode.
- **Merge conflict → abort → escalate.** There is no automatic "resolution" of a conflict; an
  escalation only returns a decision, and `coder` executes again.
- **`blocked` is not a group or task status.** It is a state of the common verification: groups and
  tasks have no `blocked` status; `incomplete` is a consequence of a contract failure, not a lane's
  judgement. A group has exactly five statuses — `pending`, `in-progress`, `done`, `incomplete`,
  `merged`; `skipped` ("not selected for integration") is an integration note, not a status; a task
  never has `merged`.
- **The two failure mechanisms are not mixed.** A task's terminal `incomplete` inside a lane is a
  single task's failure and a decision of that cycle's `planner`; a STOP of a corrective task is a
  recurrence of a defect of the **common** verification under the base `r`/`n`.
- **No automatic rerun/remerge/recluster/reset/revert** and no new branch chains; a corrective task
  is a separate record, not an extra lane.
- **The success of a corrective task does not mean the collection succeeded.** On a STOP without an
  admissible revised plan, the collection remains `unverified` and the original tasks keep their
  previous statuses.
- **Fallback.** The flat primary kicks in when `pdca-orchestrator` is unavailable: the agent is
  absent, `subagent_depth` < 2, or the host forbids a subagent to delegate (no nested
  delegation). Then there is no one to orchestrate, and the primary takes the groups on itself: it
  drives one task per group itself and starts the next when the previous finishes, and in phase P it
  likewise conducts each task's `COLLECTION TASK PLAN` itself (through its variant's
  `planner`/`coder`/`scout`), respecting the ALL-barrier, and continues the saved PLAN in the lane
  from DO. In autonomous mode the fallback is marked with a `Notice:` line and the recorded reason,
  in normal mode with a message to the user; a host prohibition is not bypassed.

## 7. Where to go next

- The full text of the skill, its role (the wrapper agent `pdca-orchestrator`, the `COLLECTION TASK
  PLAN` input, the group lane), the P/D/C/A phases, the status, the git model and the failure
  semantics —
  [`opencode/pdca-collection/SKILL.md`](../opencode/pdca-collection/SKILL.md). The agent's prompt
  runner (`config/agents/pdca-orchestrator.md`), the profiles and `AGENTS.md` are host artifacts of
  the `opencode-config` repository; they are not part of this repository.
- The cycle base: [`opencode/pdca-coder/SKILL.md`](../opencode/pdca-coder/SKILL.md) (for .NET, the
  identical base [`opencode/pdca-dotnet/SKILL.md`](../opencode/pdca-dotnet/SKILL.md)).
  The family's neighbouring articles: [`pdca.md`](pdca.md) — the domain-neutral core,
  [`pdca-coder.md`](pdca-coder.md) and [`pdca-dotnet.md`](pdca-dotnet.md) — the engineering
  variants.
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
| The top-level role and stack-neutrality; the cycle variant is chosen per task; the own PLAN stops at the PLAN→DO boundary and continues in the lane; the primary does not edit files | `opencode/pdca-collection/SKILL.md:10-33` |
| Auto-commit only by project overlay or explicit request; `push` never; the one-group mode | `opencode/pdca-collection/SKILL.md:35-45` |
| P: each task's own PLAN before the DAG, the ALL-barrier, a gap without a `ready` placeholder, groups go to `planner`, the revision vector, lane allocation only after the schedule is bound; a re-entry after a terminal `incomplete`/STOP requires proof or a new oracle | `opencode/pdca-collection/SKILL.md:51-82` |
| P: the status file as the only progress mirror (per-group and per-task tables), one group → one lane, an empty input | `opencode/pdca-collection/SKILL.md:83-93` |
| D: worktrees and branches, cap, schedule binding, the merge barrier, `done → merged`, `#<n>` in the merge message, `incomplete` is not merged, conflict/abort/escalation; the five group statuses, `skipped` as an integration note, `blocked` is not a status | `opencode/pdca-collection/SKILL.md:103-149` |
| C: the standard two-beat CHECK, the mandatory reports and review lenses, the full check after all selected `done` groups are integrated, a PASS alongside `incomplete`, the corrective task, re-gather, the base `r`/`n`, STOP and `unverified`; the mechanism of a task's `incomplete` in a lane is not mixed with a STOP of a corrective task | `opencode/pdca-collection/SKILL.md:153-212` |
| A: completion only by a PASS, the report's composition, cleanup only of `done`/`merged`, preservation of `incomplete` results and of status/evidence paths, STOP | `opencode/pdca-collection/SKILL.md:216-227` |
| The lane: task branches off the tip, continuing the saved PLAN from DO, stopping the group, preserving commits/patch, other groups continuing, `blocked` is not a group status | `opencode/pdca-collection/SKILL.md:231-276` |
| A stale plan and schedule revision (reopening PLAN, the ban on auto-recluster after the lanes start) | `opencode/pdca-collection/SKILL.md:278-298` |
| The git model: 1 worktree per group, ff advancement, sibling refs, `--no-ff` merge, the tip | `opencode/pdca-collection/SKILL.md:300-330` |
| The failure semantics (table) and the collection status with invariants (`plan_state`, `merged`, `skipped`, `blocked`, evidence preservation) | `opencode/pdca-collection/SKILL.md:332-387` |
| Parameters: cap = 4, the worktree directory, the merge right | `opencode/pdca-collection/SKILL.md:390-401` |
| The fallback (flat primary, including COLLECTION TASK PLAN and continuing the saved PLAN) | `opencode/pdca-collection/SKILL.md:432-440` |
| The role tiers (cheap: `pdca-orchestrator`/`scout`/`coder`; medium: `planner`/`check`; strong: `escalate`) | `opencode/pdca-collection/assets/diagram/gen_collection.py:800-803` |
| The cycle base: the two-beat CHECK, the `N`/`r`/`n/3` counters, escalation, the autonomous fallback and `Notice:`; the role names of the universal variant (`pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`) | `opencode/pdca-coder/SKILL.md:941-975,119-141,535-597,49-91` (for .NET, the identical base `opencode/pdca-dotnet/SKILL.md:1074-1108,117-139,630-692,47-89`); `opencode/pdca/SKILL.md:22-36,57-59` |
| The contract texts are checked by tests, and the scenario matrix is marked as static (not proof of behaviour); the host artifacts (the `pdca-orchestrator` prompt runner, the profiles, `AGENTS.md`) are outside this repository | `opencode/pdca-collection/tests/test_plan_barrier.py` (including `:33-38`), `tests/test_verification_recovery.py`, `tests/scenarios.md` |
