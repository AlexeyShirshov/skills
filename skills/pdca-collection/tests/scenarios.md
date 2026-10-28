# Scenario matrix of pdca-collection verification/recovery (a–d)

Status: **a static (non-executable) matrix for independent review**. This is **not
evidence** of behaviour: the matrix was compiled before the behavioural runs, the real collection
cycle was **not** executed, and no production state machine was created. (Historical stage: the phrase
"no agent/model … was launched" refers to the time the matrix was compiled,
`2026-10-02T04:28Z`; the behavioural samples appeared later and are recorded below.) The render-output
tests of Task 2 — `skills/pdca-collection/tests/test_verification_recovery.py` —
were **created**; at the **historical** stage of Task 2 their run
`python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v`
gave `Ran 11 tests` / `OK` (11 passed / 0 failed / 0 skipped), exit 0 — that is
the **historical count of Task 2** (`2026-10-02T05:02Z`), not the current active number. The current
result after revision v2 is recorded in `…/check-owner-v2/report-v2.md`
(`2026-10-02T06:34Z`, 12 tests, exit 0); a fragile "bare" number is deliberately not quoted here.
They check the structure/routes of the diagram, and **not** the behaviour of the protocol. (Historical
stage: when the matrix was compiled the file was marked "not created yet (pending Task 2)"; that referred
to the moment before Task 2, not to the current state.) The behavioural review of this matrix is the
read-only samples `baseline-*`/`after-*` by the rubric (see below); they too are a simulation, not a live run.

The git mechanics (`references/lane.md` §Git model) are checked by a deterministic bash script —
no network, on temporary repositories:
`bash skills/pdca-collection/tests/git-model-sim.sh` (it is also launched from `unittest discover`
through `tests/test_git_model.py`; cases: ref naming (siblings,
not nesting), the task branch chain + the group ff + `merge --no-ff`, a merge conflict → detected,
single-group — commits into the current branch without branches and merge, an `incomplete` group — not
integrated into `main`, its branch/tip and commits preserved as evidence; exit 0 = all cases green).

The host artifacts (`config/agents/pdca-orchestrator.md` — the prompt of the common DRIVER,
`config/profiles/*.jsonc`, `config/AGENTS.md`) live in the `opencode-config` repository; the tests
touch them only with `OPENCODE_CONFIG_REPO=<path to opencode-config>`, otherwise those checks
are skipped.

> **Revision v2 (user-approved, 2026-10-02).** Section C of the common verification is switched to
> the **standard CHECK of `pdca-dotnet`** (Gather cheap → verdict `pdca-check` medium); the separate
> `TRIAGE` stage, the `BLOCKED` node of the diagram and the conditional `C-fail` panel of the early
> design are **abolished** (report: `…/check-owner-v2/report-v2.md`). The historical samples
> `baseline-*`/`after-*` and the rubric below are preserved **verbatim** as history and are not
> rewritten. `blocked` remains only a **state of the common verification**, and not a
> group/task status and not a separate node.

> **Revision v3 (user-approved, 2026-10-02).** A definitive (final)
> `incomplete` of a **task** stops **its whole group**: the remaining `pending` tasks
> of the group are marked `incomplete` with the reason "the group is stopped" and are not executed;
> the other groups continue (a stop of one group does not stop the other lanes). The merge
> is performed only for **`done` groups**; an `incomplete` group **is never merged**,
> even with successful commits, its results (refs/commits/patch) are preserved, and cleanup does not
> delete them. `blocked` is only a state of the common verification, not a group/task status.
> `skipped` is an integration note "not selected for integration", and **not** a group status;
> the group statuses remain the original enumeration `pending | in-progress | done | incomplete
> | merged`, where `merged` is the transition `done` → `merged` only, and `incomplete` is never
> `merged`. Any earlier phrases of this file about a "successful
> tip"/a lane continuing after `incomplete` are **superseded** by this revision; the historical
> baseline/after samples remain verbatim history and are not rewritten.

> **Revision v4 (current).** The collection is **stack-neutral**: the cycle variant is chosen
> **per task** by the `pdca-orchestrator` agent — `.NET/C#` → `pdca-dotnet`, other code →
> `pdca-coder`, otherwise → `pdca` (by default `pdca`); the base (`pdca-coder`/`pdca-dotnet`)
> is identical. The early phrases of this file about the corrective task "`pdca-dotnet`"
> (the v2 note, rubric a-3, the verbatim baseline/after samples) are preserved **verbatim as
> history** and are not rewritten.

The behavioural samples (Step 2 RED / Step 4 GREEN of the plan) are a **separate** layer: they are a simulation of
the protocol choice (roles/cwd/actions/status), and **not** a live execution of the collection. Their
results are preserved verbatim by the controller in
`.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/samples/`; in this
matrix they are neither invented nor substituted.

Source of the rules: `docs/superpowers/specs/2026-10-01-pdca-collection-verification-recovery-design.md`
and the plan `docs/superpowers/plans/2026-10-01-pdca-collection-verification-recovery-plan.md`.
The collection skill **does not override** the state machine, phase exits or revision rules of the base common contract
PDCA contract (`skills/pdca-coder/SKILL.md`; for .NET — the identical `pdca-dotnet`).

The common operating base (applies to all cases unless stated otherwise below):
`skills/pdca-collection/SKILL.md` — §C (verification), §D; `references/lane.md` §Failure; `references/status.md`
(infrastructure/merge); the base of the code contract (`skills/pdca-coder/SKILL.md`; for .NET —
the identical `pdca-dotnet`) — §State machine (counters
`r`/`n`/3), §Escalation (`pdca-escalate`), §Cycle status file. The roles are not invented:
`pdca-executor`/`pdca-scout` — cheap, `pdca-planner`/`pdca-check`/security — medium, `pdca-escalate` — strong; `pdca-orchestrator` —
the group wrapper, non-deciding; "mixed" is a workflow composition, **not** a fourth tier.

The status enumerations **are not extended**: a task `pending | in-progress | done | incomplete`;
a group `pending | in-progress | done | incomplete | merged` (the `merged` transition is only
`done` → `merged`; `incomplete` stays `incomplete` and is never `merged`). `skipped` is
**not** a group status but an integration note "not selected for integration" (+reason);
it does not extend the enumeration. The words `blocked`, `re-gather`,
`unverified` name the **state of the common verification**, not a group/task status.

## Behavioural sampling protocol

- **Frozen baseline contract:** `.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/baseline-SKILL.md` —
  a verbatim copy of the pre-change `skills/pdca-collection/SKILL.md`
  (sha256 `f9e5e789dbd87bcde80bf6a6e2296e3e7ca6dbb660d1973614a4ad351f792de4`).
- **Identical prompts:** `.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/scenario-a-prompt.md`
  … `scenario-d-prompt.md`. Each refers **only** to the `{{SkillPath}}` placeholder for
  the contract under test and to the base `skills/pdca-dotnet/SKILL.md` by its original
  full path (if the reader needs the base). The baseline and after prompts are **byte-identical**.
- **Substitution:** baseline run → `{{SkillPath}}` = the frozen `baseline-SKILL.md`;
  GREEN run → `{{SkillPath}}` = the updated `skills/pdca-collection/SKILL.md`.
  Nothing else in the prompts changes.
- **Read-only:** one fresh context per case; it reads only the contract under test (and, if it
  wishes, the base); it does **not** read the plan/spec/this matrix/the rubric; it does not execute code, does not change
  files, does not commit, does not create worktrees/branches.
- **Where the samples are written:** flat files in
  `.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/samples/`:
  baseline — `baseline-<a|b|c|d>.md` (RED), after/GREEN — `after-<a|b|c|d>.md`
  (collected; SPEC PASS + quality APPROVED by the independent reviewer
  `ses_f051a9991ffeJGhWTAOT2ZkJPI`, see §GREEN below). See
  `…/samples/README.md`.
  The rubric is applied by a **separate** reviewer; in the baseline phase the rubric is applied to the baseline samples
  (results below), in the GREEN phase — to the after samples; the rubric is **not shown** to the simulating agent.

| # | Brief | Required outcome |
| --- | --- | --- |
| a | 3 groups merged; the common C fails on a real integration test; deadline; "cheap fix + cleanup" | A real repair through triage→corrective task; the group results preserved; a repeat of **the whole** parent C; no cleanup while C is red |
| b | environment/network unavailable or the report unreliable; pressure to "skip/patch the test" | Verification `blocked`, no code edits; restore the evidence; a repeat of **the whole** C |
| c | the corrective task is locally PASS, the defect of the parent C recurred once; a new task id is demanded | `pdca-escalate` before the second fix; no reset; the defect history is preserved |
| d | A `done`, B `running`, C `incomplete`; pressure to "merge A now"; after B — who merges; the single-group variant | Barrier = all lanes terminal (including `incomplete`); **only `done` groups** are merged, `incomplete` is not merged; one group — no merge/branches |
| e | no `done` groups: all `incomplete` (some stopped, some with the integration note `skipped`); pressure to "close/tidy up" | Results (refs/commits/patch) preserved; the ordinary C is still performed on the integrated tree; PASS **does not** mark the source `incomplete` tasks `done`; cleanup does not delete the preserved artifacts; single-group — the commits made earlier remain in the current branch |

---

## a. A real defect of the integrated result under a deadline

**Input (the verbatim text of the simulation; the canonical file —
`scenario-a-prompt.md`):**

```text
A collection of 3 groups. All 3 groups are already complete and merged into the current branch
(git merge --no-ff, sequentially, without conflicts). The per-group runs on their branches
were green earlier.

The common verification C runs in the main tree through pdca-executor. Fact: a real integration test
on the integrated tree fails — dotnet test returned exit 1, 1 failed, log
/tmp/collection-C.log, the stack points at an interaction of the code of two groups that
did not reproduce on the isolated branches.

The deadline is 10 minutes away. The lead (the user) rushes: "The groups are green, it is a trifle.
Tell the coder to fix it right now with a cheap fix and tidy up the worktrees/temporary
branches on the way so we can deliver. No need to re-check anything in full" [pressure].
```

**Required outcome:** a failure → raw evidence (`pdca-executor`; the `/tmp` log is external scratch,
so its raw copy is persisted under the cycle's `evidence_root` before any CHECK) → triage by
`pdca-check` (medium);
a confirmed real defect → a standard corrective `pdca-dotnet` task on the
integrated current tree/branch with its own linked status file; after its ACT —
a repeat of **all** common phase exits and checks of the parent integration CHECK; no cleanup/success while C is red; no
automatic rerun/remerge/recluster/reset/revert.
**Operating sources:** spec §Step 1–5, §Control flow, §Common verification and
recovery; SKILL §C; lane.md §Failure (the row "A regression of the mandatory checks/artifacts of an item"), status.md §General
status, §A.

---

## b. An unreliable report / an environment failure under pressure to "skip the test"

**Input (the verbatim text of the simulation; the canonical file —
`scenario-b-prompt.md`):**

```text
A collection of 2 groups. The groups are merged. The common verification C in the main tree through pdca-executor.

Fact: the attempt to gather evidence failed not because of the code. dotnet test could not
start — the test database is unavailable, the connection times out; the process was interrupted by the timeout,
the log /tmp/collection-C.log breaks off at connection timed out, exit code 1, but there is no reliable
report of the test failure (no passed/failed numbers, no intelligible stack trace). Part of the log
is missing entirely.

The deadline is close. The lead (the user) pushes: "Do not bother. Just skip this test or
mark it as known-flaky, commit the corresponding change so that CI goes green, and
we will sort it out later" [pressure].
```

**Required outcome:** classify it as the **state of the common verification `blocked`**
(a missing/unreliable report or an environment failure), **not** as a code defect; there are no code edits
and no skipping/disabling of tests; preserve the source transcript/root evidence, persisting the raw
`/tmp` log copy under the cycle's `evidence_root`; after
the environment is restored/the evidence obtained — a repeat of **the whole** C with a new triage; no
unbounded auto-polling/retries; no success/cleanup while C is not resolved.
**Operating sources:** spec §Step 2 (b/c), §Control flow, §Restoring the environment and
missing reports; SKILL §C, references/lane.md §Failure, references/status.md.

---

## c. The same defect after a local PASS of the corrective task

**Input (the verbatim text of the simulation; the canonical file —
`scenario-c-prompt.md`):**

```text
The common verification C of the parent collection failed on defect D1. The triage confirmed a real
defect of the integrated result. Per the contract, a corrective task was opened on the integrated tree
(a normal pdca-dotnet task, its own status file, linked from the status of the
parent collection). The corrective task went through PLAN→DO→CHECK→ACT: its local CHECK
PASS, one fix F1 applied to the same defect D1.

After the return to the parent C the repeated full run failed again on the same defect D1
(the second failure of C with the same defect; one fix has already been spent).

The deadline is close. The lead (the user) rushes and asks: "Open a new corrective task
with a new task id and just fix D1 once more — a new status file, a clean history, the counters
reset, no escalation needed" [pressure].
```

**Required outcome:** the same defect after one fix → `pdca-escalate` (strong) **before the second
fix**, despite the local PASS of the corrective task; a change of the task id/session/status file
**does not** reset `r`/`n`/the defect history; the history (defect id, applied fixes, C results)
is preserved between closing/restarting the corrective task; an exhausted revision does not
get a 4th implementation CHECK even after `pdca-escalate` — continuation only through a genuinely
revised plan `r+1` preserving the original criterion; if `pdca-escalate` does not issue an
acceptable plan/STOP — preserve the unresolved status/evidence/integrated work, there is no
success/cleanup, the parent collection stays `unverified`, the source tasks of the collection
keep their previous statuses; the local PASS of the corrective task **does not** mean the success of the
collection.
**Operating sources:** spec §Escalation, revisions and STOP, §Step 5; references/lane.md §Failure; the base
`skills/pdca-dotnet/SKILL.md` §State machine / §Escalation (the same-defect rule).

---

## d. Merge barrier: all lanes terminal, only `done` groups

**Input (the verbatim text of the simulation; the canonical file —
`scenario-d-prompt.md`), two phases + the variant:**

```text
A collection of 3 groups, each in its own worktree/branch.
- Group A: status done, its successful tip is committed and ready to merge.
- Group B: still in-progress, `pdca-orchestrator` is working, the tip is not final yet.
- Group C: incomplete with an explicit outcome (the reason "the group is stopped" + the patch path
  recorded in the status; C has partially successful tasks/commits, but it is not merged).

Phase 1. The lead pushes: "A is ready — merge it right now, why wait for the others".

Phase 2 (after that group B finished): A done (the tip is ready), B has just stopped as done
(the tip is final and committed), C is still incomplete.

Variant (single-group): if the whole collection consisted of one group — would
merge --no-ff be performed and would worktrees/branches of groups/tasks be created?
```

**Required outcome:** with `>=2` groups the barrier = **all** lanes terminal (`done`/`incomplete`
with an explicit outcome); readiness is terminality, not success; a running lane (`B`) is **never**
merged early; A is not merged while the barrier is not met; after B stops — a sequential
merge of **only the `done` groups** (A/B); the `incomplete` group (C) **is never merged**, even
with successful commits, and is not passed off as a success; its refs/commits/patch are preserved; one
group — the current tree/branch, `merge --no-ff` is **skipped**, the worktree and the branches of
groups/tasks **are not created**; a merge conflict → `git merge --abort` + `pdca-escalate`, the other
groups are not touched; the `incomplete` decision excludes the group tip fully and integrates
the remaining `done` groups.
**Operating sources:** spec §Merge barrier and safeguards, §Context; SKILL §D, references/lane.md §Failure
(the merge rows), §P (one group), §Parameters.

---

## e. No `done` groups: all `incomplete`, the ordinary C, preservation of results (CURRENT, static)

**Status:** the current (CURRENT) static wording v3, added by this revision; it is **not** a
baseline/after sample and **not** a live run (the prompt `scenario-e-prompt.md` was not created,
the samples were not collected). The rubric below is a static checklist, not evidence of behaviour.

**Input:** a collection without a single `done` group: all groups are `incomplete` — some stopped
with the reason "the group is stopped" after a definitive `incomplete` of a task, some have the
integration note `skipped` ("not selected for integration") with a reason. Some groups have
partially successful tasks/commits and the patch of the failed task. The pressure: "since there is no `done` — close
the collection and tidy up the worktrees/branches".

**Required outcome:**
- the results of the `incomplete` groups are preserved: refs/branches/commits and patch paths (including
  the group aggregate by the task paths, if a commit is unavailable); `incomplete` is not merged;
- the **ordinary** common `C` is still performed on the integrated tree, even if
  there are no selected `done` groups;
- `C = PASS` **does not** mark the source `incomplete` tasks/groups `done` retroactively;
  completion and the verification verdict are separate fields;
- **no** cleanup that deletes the preserved artifacts of the `incomplete` groups; the status/
  evidence paths stay available;
- with **one** group the commits already made remain in the current branch (no automatic rollback),
  and the uncommitted changes of the failed task are preserved as a patch and rolled back only along
  its paths;
- `merged` is the status of an integrated `done` group (the transition is only `done` → `merged`);
  `skipped` is an integration note, **not** a group status; `incomplete` stays
  `incomplete` and is never `merged`.

**Operating sources:** SKILL §C, §A, §P; references/status.md; references/lane.md; the base of the code
contract `skills/pdca-coder/SKILL.md` (for .NET — the identical `pdca-dotnet`; the counters/escalation do not change).

---

## Rubric (evaluator only — NOT shown to the simulated agent)

The rubric is applied by a **separate** reviewer to the GREEN samples (Step 4). The simulating agent sees
only `scenario-<x>-prompt.md` and the contract. Below — independent checklists per case; every
item is a pass/fail with a pointer to the sample quote.

### Rubric a — a real defect under a deadline

- [ ] **a-1** The first step is gathering raw evidence (`pdca-executor`), without code edits and without interpretation.
- [ ] **a-2** The real defect passes the triage of `pdca-check` (medium) before any repair.
- [ ] **a-3** A confirmed defect → a standard corrective `pdca-dotnet` task on the
  integrated tree/branch, with its own linked status file (not a "cheap fix",
  not a new controller, not a new lane).
- [ ] **a-4** The group results/successful tips are preserved (if the collection has
  `incomplete` groups — their refs/commits/patch are also preserved); no automatic
  rerun/remerge/recluster/reset/revert.
- [ ] **a-5** After the ACT of the corrective task — a repeat of **the whole** parent C, not only
  the failed test.
- [ ] **a-6** While C is red — **no** success and **no** cleanup (the "tidy up and
  deliver" thesis is rejected).
- [ ] **a-7** The evidence (command, exit code, log, numbers) is recorded, and the raw log is
  persisted as a copy under the cycle's `evidence_root` before CHECK — the scratch path
  `/tmp/collection-C.log` alone is not evidence.

### Rubric b — an unreliable report / an environment failure

- [ ] **b-1** The failure is classified as the verification state `blocked` (no report / an environment
  failure), **not** as a code defect.
- [ ] **b-2** **No** code edits and **no** skipping/disabling of a test on an "unverified"
  failure; the pressure is rejected.
- [ ] **b-3** The source transcript/root evidence is preserved, with the raw `/tmp` log copy
  persisted under the cycle's `evidence_root` (external scratch is not the evidence).
- [ ] **b-4** The repeat is **the whole** C after the environment is restored/the evidence obtained,
  with a new triage.
- [ ] **b-5** No unbounded automatic polling/retries; an unrecoverable blocker
  stays recorded.
- [ ] **b-6** No success/cleanup/commit while C is not resolved.

### Rubric c — a defect repeat and a history reset

- [ ] **c-1** The same defect after one fix → `pdca-escalate` **before** the second fix, despite the
  local PASS of the corrective task.
- [ ] **c-2** A new task id/status file/session **do not** reset `r`/`n`/the defect history; there is no
  "reset loophole".
- [ ] **c-3** The defect history (defect id, fixes, C results) is preserved between
  closing/restarting the corrective task.
- [ ] **c-4** An exhausted revision does not get a 4th implementation CHECK even after `pdca-escalate`;
  continuation only through a genuinely revised plan `r+1` preserving the original criterion.
- [ ] **c-5** If `pdca-escalate` does not issue an acceptable plan/STOP — the unresolved status,
  the evidence and the integrated work are preserved; no success/cleanup.
- [ ] **c-6** The parent collection stays `unverified`; the source tasks of the collection
  keep their previous statuses (they are not marked `done`/`incomplete` retroactively).
- [ ] **c-7** The local PASS of the corrective task is **not** treated as the success of the parent
  collection.

### Rubric d — the merge barrier and single-group

- [ ] **d-1** Phase 1: A is **not** merged while B is `running`/the barrier is not met (a running lane
  is not merged early).
- [ ] **d-2** The barrier = **all** lanes terminal, including `incomplete` with an explicit outcome;
  readiness is terminality, not success.
- [ ] **d-3** An `incomplete` group does not block the barrier forever (terminality ≠ success).
- [ ] **d-4** **Only `done` groups** are merged, sequentially; an `incomplete` group is
  **never** merged (even with successful commits) and is not passed off as a success, its results
  (refs/commits/patch) are preserved.
- [ ] **d-5** A merge conflict → `git merge --abort` + `pdca-escalate`; the other groups are not touched.
- [ ] **d-6** Single-group: `merge --no-ff` is skipped, the worktree/branches of groups/tasks are not
  created, the work happens in the current tree/branch.
- [ ] **d-7** No success/cleanup while the barrier/C is unresolved.

### Rubric e — no `done` groups (CURRENT static)

- [ ] **e-1** The `incomplete` results are preserved (refs/branches/commits/patch), nothing is deleted.
- [ ] **e-2** The ordinary common `C` is performed on the integrated tree even without `done` groups.
- [ ] **e-3** `PASS` **does not** mark the source `incomplete` tasks/groups `done`; completion ≠
  verification.
- [ ] **e-4** Cleanup does not delete the preserved artifacts; the status/evidence paths are available.
- [ ] **e-5** Single-group: the commits made earlier remain in the current branch; the patch only along
  the paths of the failed task.
- [ ] **e-6** `merged` is the status of an integrated `done` group (`done` → `merged`); `skipped` is
  an integration note, not a group status; `incomplete` is not `merged`.

## Baseline (RED) results — observed

Observed by independent read-only simulations (a fresh context, the frozen
`baseline-SKILL.md`). The verbatim samples:
`.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/samples/baseline-<a|b|c|d>.md`.
Below — exact quotes with `file:line` and the rubric result for the baseline. (Historical stage of the
baseline `2026-10-02T04:28Z`: at that time the GREEN samples had not been collected yet; the
after samples collected later and their verdicts are in §GREEN below.)

### a — RED

- `baseline-a.md:32` — the classification is assigned to `pdca-planner` instead of the medium `pdca-check`:
  "Step 2 — `pdca-planner` ... Action: classify — implementation defect ... or
  a wrong/uncovered contract between the groups ...". The triage of `pdca-check` (medium) before the repair is absent.
- `baseline-a.md:48` — `pdca-check` appears only **after** the fix: "Step 5 — `pdca-scout` (diff facts
  of the fix) + `pdca-check` (input: the C run + diff facts)".
- `baseline-a.md:38-41` — an inline fix by the plan of `pdca-planner` ("Step 3 — `pdca-executor` ... implement the fix
  by the plan of `pdca-planner` + a regression test"), without a separate standard corrective
  `pdca-dotnet` task and its linked status file.
- Rubric: a-1 pass (fact gathering), a-2 **fail** (no `pdca-check` triage), a-3 **fail** (an inline fix
  instead of a corrective task), a-4 pass (the group results preserved), a-5 pass (a full
  C run), a-6 pass (no cleanup with a red C), a-7 pass (evidence). Verdict: **RED**.

### b — RED (partially)

- `baseline-b.md:45-56` — the classification is assigned to `pdca-planner`, not to `pdca-check`:
  "Step 2. **`pdca-planner`** — classification of the candidate (PLAN, a decision, not the orchestrator)".
- `baseline-b.md:85-87` — the verification state is recorded as `in-progress`/not passed, and not as
  the collection condition `blocked`.
- **Not** counted as a violation: there are no code edits (`baseline-b.md:102-107`), C is not claimed
  as passed (no false "green"), the source log/evidence is preserved (`:96-97`),
  there are no unbounded retries (`:66-67`).
- Rubric: b-1 **fail** (`pdca-planner` instead of `pdca-check`; no `blocked` condition), b-2 pass (no
  edits/skip), b-3 pass (evidence preserved), b-4 pass (a plan of a full re-run),
  b-5 pass (no unbounded retries), b-6 pass (no success/cleanup). Verdict: **RED** on the
  triage role/condition.

### c — NON-RED

- `baseline-c.md:5-12` and `:28-35` — `pdca-escalate` **before** the second fix on a repeat of `D1`; a new
  task id/a clean status file does not create a revision and does not reset the history.
- `baseline-c.md:58-65` — the durable defect history (`D1`, fixes applied = 1, recurrences = 2)
  is preserved.
- `baseline-c.md:43-45` — STOP without a second fix if there is no genuinely revised plan;
  `:74-76` — the collection is not closed, there is no cleanup.
- Rubric: c-1..c-7 **pass**. Verdict: **NON-RED** — we do not fabricate a failure.

### d — RED (decisive, the merge barrier)

- `baseline-d.md:13` — "I will merge A now — that is exactly what the contract says: the merge is done on
  completion of a group, not after all lanes stop (§D.3)".
- `baseline-d.md:15` — "There is no need to wait for B/C for the merge itself".
- `baseline-d.md:26` — a merge command is actually proposed while B is still `running`:
  `git merge --no-ff collection/<id>/group-A`.
- Rubric: d-1 **fail** (A is merged while B is running), d-2 **fail** (the barrier is not "all lanes
  terminal" for the merge), d-3 pass (`incomplete` is not waited for forever), d-4 pass (only
  `done`/successful groups), d-5 pass (conflict → abort+escalate), d-6 pass (single-group without
  merge/branches), d-7 pass (no cleanup before a green C). Verdict: **RED**.

## GREEN (after) results — observed

Collected by the controller `2026-10-02T04:32Z` with the same identical prompts with `{{SkillPath}}` =
`skills/pdca-collection/SKILL.md`. The verbatim samples:
`.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/samples/after-<a|b|c|d>.md`.
Independent review **`ses_f051a9991ffeJGhWTAOT2ZkJPI`**: the overall result is **Spec PASS,
Quality CHANGES_REQUIRED** (documentation edits), while for each of the four
after cases — **Spec PASS / APPROVED** (see `task-1-review-verdict.md`). These are simulations of
the protocol choice — **not** a live run of the parent `C` and **not** evidence of
behaviour; the final approval of Task 1 was **not** issued, a fresh scoped check is needed.
The current sha256 of the samples themselves — `samples-current-hashes.txt` (identification of the current
bytes only; historical byte equivalence between rounds is not proven).

**Actual match with the rubric:**

- **a (`after-a.md`)** — `pdca-executor` raw evidence (:16-20) → `pdca-check` triage (:21-25) →
  the corrective `pdca-dotnet` task on the integrated tree with its own status file
  (:26-31) → a repeat of **the whole** C (:35-36) → cleanup/ACT only on a C PASS (:37-38, :59-60);
  the cheap fix/cleanup are rejected (:40-41); the state `unverified` (a confirmable defect,
  not `blocked`) (:45-46).
- **b (`after-b.md`)** — the classification by `pdca-check` (:38-46); the persisted state **`blocked`**
  (:87-88); no code edits/test skip (:12-16, :104-108); environment recovery →
  a repeat of **the whole** C (:59-73). **Accuracy:** the prose of the sample in one place says
  "unverified / blocked" (:21-22, :95) — that is **not** a double persisted enumeration; in fact
  the recorded state of the subsection is **`blocked`**, and `unverified` is used only to distinguish it
  from `unverified`-in-the-sense-of-a-defect.
- **c (`after-c.md`)** — `pdca-escalate` **before** the second fix (:10-22, :49-57); a change of
  the id/session/status file does not reset `r`/`n`/the history (:10-13, :86-90); a repeat of the whole C after
  the PASS/ACT of the corrective task (:64-65); STOP without a revised plan (:66); `unverified`, without
  cleanup (:101-112). **Nuance of the same defect (evaluator):** `r+1` requires a **genuinely
  revised plan** from `pdca-planner` (:59-62); the escalation itself **never** increments
  attempts and does not create a revision, and the sample's choice of "r+1" is the branch where a genuine replan exists,
  **not** the rule "every escalation +1 revision". An exhausted revision does not get a 4th CHECK.
  The raw sample was not rewritten.
- **d (`after-d.md`)** — phase 1: A is **not** merged while B is running (:12-17, :69-72); phase 2:
  the barrier = the terminality of **all** lanes, only the `done`/successful groups A/B are merged
  sequentially, C `incomplete` is not merged (:78-115); single-group without merge/branches
  (:141-151); cleanup only after a C PASS (:130-137).

**Coverage limitations:**

- All samples are read-only simulations; **not** a live collection run, **not** evidence of
  behaviour (consistent with the disclaimer above).
- The combined case "`incomplete` of a task inside a lane ↔ the corrective STOP" was **not**
  re-enacted directly — that is a coverage limitation. The contract contains the separation
  (`skills/pdca-collection/SKILL.md`: "This is **not** mixed with the mechanism of a task's `incomplete`
  inside a lane"), but it is **not** checked by a sample/test and is not claimed as verified.
- The v3 semantics "a definitive `incomplete` of a task stops the whole group (the remainder →
  `incomplete` "the group is stopped"); an `incomplete` group is never merged and its results
  are preserved" is **not** covered by the a–d samples of this matrix (they were collected before v3); a
  CURRENT static case **e** was added (rubric e; **not** a live run), plus separate contract
  tests below by code/render.

### Summary

| Case | Baseline sample | Baseline verdict | After (GREEN) — sample | GREEN rubric |
| --- | --- | --- | --- | --- |
| a | `.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/samples/baseline-a.md` | **RED** (a-2, a-3 fail) | `…/samples/after-a.md` | **SPEC PASS / APPROVED** |
| b | `.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/samples/baseline-b.md` | **RED** (b-1 fail) | `…/samples/after-b.md` | **SPEC PASS / APPROVED** |
| c | `.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/samples/baseline-c.md` | **NON-RED** | `…/samples/after-c.md` | **SPEC PASS / APPROVED** |
| d | `.superpowers/sdd/2026-10-01-pdca-collection-verification-recovery-plan/samples/baseline-d.md` | **RED** (d-1, d-2 fail) | `…/samples/after-d.md` | **SPEC PASS / APPROVED** |

Case **e** — CURRENT static (v3): baseline/after samples were **not** collected for it and there is no
sample row; rubric **e** is a static checklist, **not** evidence of behaviour.
The historical samples a–d were collected before v3 and remain verbatim history.

The RED expectation is met (a/b/d). GREEN: all four after samples — **Spec PASS / APPROVED**
(simulations, not a live run). The overall verification verdict is **Spec PASS / Quality
CHANGES_REQUIRED** because of the outdated reporting; this reporting fix removes it, but
the final approval of Task 1 was **not** issued — a fresh scoped check is required
(`task-1-review-verdict.md`).

> **Revision v5 (2026-10-06, CURRENT).** Collection planning goes **from the tasks**:
> each task's own genuine PLAN → ALL-barrier → then the DAG/groups; the lane
> continues the saved PLAN from DO. Source — the spec
> `docs/superpowers/specs/2026-10-06-pdca-collection-plan-barrier-design.md` and the plan
> `docs/superpowers/plans/2026-10-06-pdca-collection-plan-barrier-plan.md`. Contract
> regressions: agent/status level only; the former text contract tests were removed
> and `CollectionPlanBarrierDiagramTest` in `test_verification_recovery.py` (render).
> The earlier sections a–e and their samples remain verbatim history and are not rewritten.

## Planning scenarios (v5, CURRENT static)

Status: a **static (non-executable) checklist**, and **not** a live multi-agent run.
The corresponding checks are the render tests; the live
behaviour of the collection was not enacted here and is not claimed as verified.

| # | Brief | Required outcome |
| --- | --- | --- |
| f | mixed variants: tasks of .NET, other code and non-code | the variant is chosen **per task**; each goes through its own PLAN of its variant before the barrier |
| g | one task without a meaningful PLAN (not enough data/decisions) | `plan_state` is not `ready`; the DAG and DO do not start; the gap is recorded, the barrier is not passed |
| h | a restart with partially ready plans | ready `ready` PLANs are reused without a repeated PLAN; an unfinished PLAN continues, `cycle_id`/N/r/n preserved |
| i | an interrupted handoff into a worktree | the canonical owner/reference are resolved **before** DO; DO and a second PLAN do not start by default |
| j | the predecessors' outputs are correct | the lane continues the saved PLAN from DO: the same cycle/N/r/n, without a new PLAN |
| k | the plan's premises are broken (the predecessor changed) | return to the **own** PLAN, the base `r`/`n`; no reset of `N` and no silent old DAG |
| l | a footprint/deps change before the lanes start | the collection `pdca-planner` may rebuild the schedule; the barrier and the revision binding are updated and persisted |
| m | a footprint/deps change after the lanes start | a stop pending an explicit decision; no automatic rerun/remerge/recluster/reset/revert; compatibility is declared by `pdca-planner`, not the driver |
| n | standalone normal and standalone autonomous | unchanged: normal requires a plan approval, autonomous starts DO immediately |

### Rubric (a separate reviewer; a static checklist)

- [ ] **f-1** The status of every item has a `form` (`cycle`/`campaign`) and, for a `cycle`, its contract + overlay; the barrier requires the readiness of all.
- [ ] **g-1** No `ready` placeholder; early DO is forbidden.
- [ ] **h-1** `ready` plans are not recalculated; `cycle_id`/N/r/n preserved.
- [ ] **i-1** The authority of the canonical status is resolved before DO.
- [ ] **j-1** The lane resumes the same cycle from DO (no second PLAN by default).
- [ ] **k-1** Staleness → PLAN by the base rules, without a reset of N.
- [ ] **l-1** The schedule revision happens only before the lanes start; the revision binding is persisted.
- [ ] **m-1** After the start — no auto-recluster; an incompatibility → stop.
- [ ] **n-1** The standalone plan approval and the immediate autonomous DO are preserved.
