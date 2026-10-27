# CHECK deltas for code: streams, audit, merge

Reference for the CHECK phase of the programming overlay. The base CHECK — independence, the
criteria matrix, findings and carrying claims, the veto, local vs whole-goal checks, verdict and
routing — stays in `../../pdca/references/check.md` and `../../pdca/SKILL.md`. This file adds the code
streams and the code audit detail.

## Two beats

CHECK proceeds in two beats, so as **not to load code into the driver's context**:

1. **Gather (cheap + commands).** Mechanics via `pdca-executor` (no LLM): the project's declared
   build/lint (clean under its own warning/error policy — gate), suppressions scan (the project's
   suppression markers, skipped tests, empty catch, sleeps), enumerate public surface, mandated doc
   coverage — metrics/tables, not code. Semantics via the selected code/correctness lens (diff
   sliced by files/chunks → **raw candidates** `file:line`+rule ID/counter, **no verdict/severity**).
   Tests via `pdca-executor` (run, coverage against the **project threshold**, complexity/mutation) +
   the test lens (does the suite match the **PLAN test strategy**; missing cases / coverage drop —
   `file:line`). Docs via the doc lens: affected docs, API-doc completeness, reference mismatches,
   outdated examples — `file:line`. Perf, when PLAN says "needed": the perf specialist +
   `pdca-executor` commands (suite/case, runs, baseline) → **raw numbers, no verdict**;
   async/concurrency hot paths + a concurrency specialist; a profiling specialist only with ready
   artifacts; "not needed" → the `file:line` one-time/not-per-row facts.
2. **Triage (the `pdca-check` subagent).** Reads the **aggregated report** and may open the cycle's
   evidence artifacts directly (its scoped `read`: status/evidence/manifest files, never product
   code) to reconcile each contract row's `path`; judges the code audit (real defect? severity? fix
   now vs accepted) and issues the verdict (pass/fail, ranking, loop-back). Do not pull the product
   code/diff into context; a missing datum goes to the gatherer. The driver executes the loop-back:
   `D:` via `pdca-executor`, the `P:` via `pdca-planner` — no manual agent switching.

The CHECK brief includes the **frozen variant and priority matrices** from the approved PLAN;
triage applies the priority/row obligations defined in `references/plan.md`
(§PLAN owns the quality of the plan). That section is the single normative definition — this file
only points to it and does not restate it.

## Keep CHECK within one approved PLAN

The driver holds the active task, the approved PLAN and the `task_id` from `pdca-check`:

- the first CHECK of a PLAN calls `pdca-check` and saves `task_id`;
- on a loop-back to DO for an implementation defect, the next CHECK of the **same task and unchanged
  PLAN** resumes the saved `task_id` and passes the **full, current** aggregated report (not a
  delta — earlier reports are history, not evidence);
- reset `task_id` (new `pdca-check` session) after CHECK → PLAN, after ACT, before the
  next task, and whenever it is lost. **This is independent of the counters:** it never resets `r`,
  `n` or the defect history (they live in the status file). A lost ID is not a passed gate; a
  resumed session waives no lens or triggered security verdict. Never recover an ID by slug alone —
  confirm same PLAN + same session.
- **Unchanged PLAN** means criteria, design decision, DO tasks/actions and dependencies are all
  unchanged — not the same iteration number, and not unchanged criteria/design while the actions
  changed.

## Parallel CHECK streams (code audit + test + doc + perf + security*)

Four unconditional streams + one conditional (security) + specialized subagents by trigger. All
independent: launch **in parallel** (one turn, several Tasks), not in sequence:

- **Code audit (two-phase)** — the code/correctness lens (raw candidates, no verdict) +
  `pdca-executor` commands (build/lint clean, suppression/slop, smell, public-API/doc coverage) =
  items 3–6, 9–10; judgment in `pdca-check` beat 2 = items 7–8. Specialized async/concurrency
  subagents by trigger are part of the gather.
- **Test lens** — the test lens + `pdca-executor` (run, coverage, mutation/complexity) — item 11.
- **Doc lens** — the doc lens — item 12.
- **Perf lens (two-phase)** — when "needed": measurement (the perf specialist + `pdca-executor`; a
  profiling specialist only with artifacts) → **raw numbers + baseline, no verdict**; async hot paths
  + a concurrency specialist; "not needed" → `file:line` facts; judgment in `pdca-check` — item 13.
- **Security audit\*** (conditional **gather**) — `pdca-security-auditor` if the diff touches
  auth/secrets/external input/crypto; same parallel turn, medium tier, by trigger. It is a gather
  stream: its report **returns into the aggregated report** (the security result goes back to
  `pdca-check`) and is judged by `pdca-check` in beat 2. It issues **no independent verdict** and
  never routes a defect around the aggregate triage. The brief carries the diff/area (it may take
  `git diff` itself; read-only `bash`) and it audits without `pdca-scout`; `pdca-scout` only for
  facts outside the diff (other occurrences, callers, config files) via a narrow question — like
  `pdca-escalate` it does not surf (`grep`/`glob`/web denied).

**Specialized subagents by trigger** (cheap, read-only; same parallel turn; output joins the
aggregated report, verdict still `pdca-check`): a concurrency/async lens (races, deadlocks, lock
ordering, sync-over-async, fire-and-forget, resource starvation); a profiling/performance analyst
**only with data** (profiles/heap dumps/benchmark comparisons). Each is an additional **gather**, not
a new gate.

Each stream relies only on the plan/diff and does not wait for another. Results converge in the
aggregated report; gate 3 passes only with **all green** (four unconditional + security if launched)
— "part of them" is not a pass, and the final verdict for **every** stream is `pdca-check`'s. Any
stream failure becomes a `D:` task for `pdca-executor` (or a PLAN return via `pdca-planner`, if the
plan is wrong) and does not cancel the others. **Any failed CHECK stream — including a triggered
security failure — counts as a failed CHECK of the current revision** for the base escalation
counter; ordinary security findings use the shared attempt/defect-history counters, and only a **hard
security trade-off** escalates immediately.

Skills (via `skill`): the project's declared code-quality/API/testing skills; only available/permitted
ones are named. Project registries: maintain on demand — `pdca-executor` edits them (only the needed
finding/section; do not re-open fixed ones or re-list accepted deviations).

**Inlined specialists may not drop the port.** An overlay that inlines a specialist's checklist into
CHECK must keep that agent's **skill-loading** (step 1) and **measurable artifacts** —
suppression/slop counts and ratio (step 4), per-finding `file:line` + rule ID (step 8) — not just its
topic list. A CHECK that skipped step 1 or reports no numbers is **not** a pass.

## Workflow (code-audit stream, items 3–10; parallel with lenses 11–13)

Two-phase: 3–6 and 9–10 cheap gather, 7–8 judgment.

1. Load skills (+ on-demand for the audit area).
2. Read project registries/findings on demand.
3. Analyzer baseline: the project's build/lint (clean under its policy — gate); list active
   analyzer/lint severities in the project's config.
4. Suppression/slop scan (as above); count suppressed vs justified and report the ratio.
5. Smell scan (the project's code-smell skill: resource disposal, suppression, async, DI, nullability,
   optional nullable defaults), each with its rule and fix.
6. Public-API scan: enumerate public types/members; naming/convention rules; mandated doc coverage;
   surface-lock status.
7. **Judgment (`pdca-check`):** classify raw candidates with the project taxonomy (`P0/P1/P2` or
   `🔴/🟡/ℹ️` default) — real defect vs noise; do not invent a scale.
8. **Per-finding (`pdca-check`; facts from gather):** exact number, `file:line`, analyzer/lint ID or
   naming rule, a one-line fix; split **fix now** vs **accepted/deviation with justification**.
9. Registry records (if any) by `pdca-executor` in `Was`/`Now`/`Check`; do not rewrite unrelated
   sections. **Author ≠ certifier:** an independent read-only stream re-derives each
   registry/acceptance claim from the cited `file:line`; a mismatch or a code-basisless self-assessed
   `deferred`/`acceptable` is a finding.
10. Hot-path measurement favors the perf specialist; the code fix is `pdca-executor`.
11. **Test lens** (parallel). New behavior ⇒ a new test from the PLAN test strategy; run green;
    **coverage not below the project threshold** (or baseline if none), area coverage not dropped; no
    new critical complexity/mutation hotspots. **Every variant-matrix row is closed** (test / guard /
    `deferred with a trigger`); CHECK augments the matrix with rows from the actual diff and the
    sibling's edge list — an added uncovered row is a defect. **PASS is forbidden while any
    requirement/class row is open**; iteration count does not prove completeness. Report the
    **branch** delta (not line only); **mutation testing** on changed code was run or untested
    branches are listed. A missing test / coverage drop / open row → a `D:` task, not "good enough".
12. **Doc lens** (parallel). Per PLAN verifies **both**: prose docs (README/guides/user documentation,
    examples/migration notes) **created** and **matching the implementation** (content, not
    presence); and generated/API docs **only when mandated** or user-requested — generated on every
    new/changed public member and matching signatures/behavior. A gap/mismatch → `D:` task for
    `pdca-executor` (+ the docs specialist).
13. **Perf lens** (two-phase, parallel). Gather: measurement done with numbers+baseline, or
    `file:line` one-time facts. Judgment (`pdca-check`): against the PLAN perf decision — regression
    acceptable? plan fulfilled? argument convincing? Work in a per-row loop with no measurement →
    `D:` task (measure) or PLAN return; no silent close.

## Optional-null/default smell

**An optional value with a null/default fallback, especially on `*Options`:** severity 🟡 by default,
🔴 if it allows silently choosing wrong behavior, ℹ️ for a genuine sentinel. Fix: a pair of overloads
— a parameterless (or minimal) one with the fallback set internally, plus a required overload that
rejects the missing value at the boundary (an explicit argument/validation error). Constraints:
overloads that differ only in nullability are a duplicate signature; under the project's warning
policy, a null in a required parameter is a gate error.

## Boundaries and output

Code and registry edits by `pdca-executor` (Do); renames/analyzer policy in Do; do not re-open fixed
findings; out of scope: profiling, security. Check output: project language, `P0/P1/P2` or
`Finding N` with `Was`/`Now`/`Check`, exact numbers, up front the build baseline + suppression
ratio.

## Parallel sub-tasks in worktrees (within one cycle)

This section is about **sub-tasks of one cycle** (a shared PLAN/contract). For **independent
features** (each with its own cycle) do not apply it: that is N separate cycles/worktrees, and the
integration after the merge there is done by a separate verification cycle, not by this CHECK.

If the plan chose (or the user asked) to perform **sub-tasks of one cycle** in parallel in
**separate worktrees**, CHECK is supplemented with two mandatory steps (do not skip them). The
build/tests of **each unit on its branch** are gathered in DO; here the already **merged** tree is
re-verified:

14. **Merge.** `pdca-executor` merges the branches/patches of all tasks into the **common tree** — in
    order, resolving conflicts from the subagent reports (`file:line`); do not delete the task
    branches.
15. **Verify the merged tree.** Rebuild and run the tests (unit + integration) **on the combined
    code** (clean under the project's policy — gate): independently green branches ≠ a green merge.
    Divergences from the per-worktree checks — into the report as integration regressions/conflicts.

Statuses — one per task (`<task>-<N>`, see `references/act.md`), the handoff — one per task. If the
merge or the merged check did not pass — return to DO (a `D:` task "resolve the conflict/regression"),
do not close the cycle.
