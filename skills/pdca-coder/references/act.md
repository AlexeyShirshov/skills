# DO and ACT deltas for code: streams, worktrees, status additions

Reference for the DO and ACT phases of the programming overlay. The base DO/ACT contracts — what a
DO report contains, the status-file lifecycle, unit states and the `superseded→replacement` rule, the
closing order and the next-session message — stay in `../../pdca/SKILL.md`,
`../../pdca/references/act.md` and `../../pdca/references/check.md`. This file adds the code streams,
the worktree protocol, the coder editing discipline, the code status rows and the code additions to
the handoff.

## Parallel DO streams (code + tests + prose docs)

DO proceeds in these steps; **code, tests and prose documentation are written simultaneously**, right
after the plan, not sequentially (a deliberate rejection of "test → code" and "docs later"; there is
no TDD ordering in DO — the only red→green requirement is the regression test of a bug fix,
§Debugging). **Generated/API docs** are not part of this launch — they follow the finished code
(step 4):

1. **Status file.** The plan is already written there (the last step of PLAN); on approval
   `pdca-executor` records `DO started` in its progress log.
2. **Shared contract — only if the streams need it.** If the tests or docs rely on an
   abstraction/DTO/signature, **first** only the contract is fixed: signatures and types **without
   implementation** (a single `pdca-executor` dispatch or a sketch in the status file). The streams
   need nothing beyond that from each other. No contract — the step is skipped.
3. **Parallel launch.** In one turn, several Tasks in one message: the **code stream**
   (`pdca-executor`), the **test stream** (`pdca-executor`; with the project's test framework/tooling)
   and the **prose-docs stream** (`pdca-executor`; README/guides/user documentation; with the
   docs/format specialist selected by PLAN when one is available) start together.
4. **Generated/API docs — after the code (when required).** Once the code stream has finished
   writing the code, `pdca-executor` adds the **generated API-doc comments/annotations** the toolchain
   uses — **only when the project/task mandates them** or the user requested it. They live in the code
   files, so they cannot run in parallel with the code stream.

Invariants:

- Code depends **only on the plan** (+ the contract from step 2), **not on the tests and docs**.
- Tests depend **only on the plan** (+ the contract from step 2), **not on the code and docs**.
- Prose docs depend **only on the plan** (+ the contract from step 2), **not on the code and tests** —
  otherwise they cannot be written simultaneously with the implementation.
- The streams must not be queued one after another; "test first, then code" and "prose docs after
  code" are forbidden.
- **Generated/API docs** (public-member doc comments/annotations) are the exception: they live in the
  code files the code stream owns, so they are written **after the code stream finishes** (step 4),
  not in parallel.
- The contract from step 2 is **frozen**: only PLAN changes it, not a stream.
- Anything that writes to **the same file** from different streams is not parallelized: such a file is
  moved into the contract (step 2) or the task stays single.
- Divergence of the streams (tests ↔ code, prose docs ↔ the actual contract/behavior) is a defect, and
  it is caught by **CHECK** (the test lens and the doc lens), not by DO.
- The **status file is not written by the streams** (it would be the same file from different
  streams): as each stream report arrives, a separate short `pdca-executor` dispatch logs it, one at a
  time.

Why this way: all three sides are derived from the plan (step 2 removes the only possible link — the
shared contract), so they are isolated and do not wait for each other; the idle time of the
executor/tester/documenter disappears.

**Units (not streams).** If PLAN split the feature into several **independent units**, they are
launched in parallel the same way — with several subagent dispatches per turn. In the "one tree" mode
— right in it (units do not share files, the invariant above); in the "worktree" mode — per the
template below, and the status file of **each** unit is created when its worktree is set up at the
start of DO, inside that worktree.

**While `pdca-planner` adjudicates a `DO → PLAN` candidate,** running streams must not keep
rewriting the old-plan area.

## Coder editing discipline (applying fixes)

When a stream **applies** fixes — the `pdca-executor` role, whether the fix came from the PLAN design
review, from a design/type/pattern lens, or from a CHECK loop-back — it follows the specialist-editor
contract (the discipline a dedicated design/performance engineer would apply when it edits):

- **One axis per step, then verify.** Make one coherent change, then build + run the **affected
  tests** before the next one; do not batch unrelated refactors, no "while I'm at it" (Over-Reach).
- **Cheap inner loop, expensive at the boundary.** After each edit run only the **fast (unit)
  affected tests**; **expensive tests — integration (real database/broker/storage, HTTP, container
  dependencies)** — are run at the **stream boundary** (before the DO → CHECK gate) and in the
  **CHECK** test lens, **not after every micro-edit**. (If the change is integration-only, run the
  affected integration case directly; but do not re-run the whole suite per edit.)
- **Verify after every step, not only at the end.** A red build or failing test stops the stream and
  is reported — it is not written over with the next edit.
- **Minimal blast radius.** Touch only the fix's blast radius; leave unrelated parallel edits alone.
  Keep public-surface changes minimal and noted.
- **Preserve the repo's line endings / formatting** while editing; never leave LF-only or mixed
  endings behind (whatever the host mandates — the project overlay supplies the concrete normalizer).
- **Build/lint is the gate** — the project's configured build and lint must be clean under its own
  warning/error policy; a change that introduces a warning or lint error is not a fix.
- **No commits and no push** unless the user explicitly asked — a cycle never commits to the working
  branch on its own. **One mechanical exception:** in the worktree mode each unit commits to its own
  isolated branch `pdca/<task>` inside its worktree (§Worktree sub-tasks) — that is the isolation
  mechanism the merge in CHECK relies on, not a delivery. Commits to the working branch — only on an
  explicit request; push — never without a separate explicit request.
- **No benchmark conclusions.** The executor may run a benchmark to sanity-check, but does not draw
  conclusions from it; sub-noise deltas are noise. Interpretation goes to the perf lens/specialist.
- **Hand off what needs numbers** to the perf specialist (via a subagent) instead of asserting it.

A host/project overlay supplies the concrete values (build/test/lint commands, line endings, artifact
restore, test projects); this block is the generic skeleton and the overlay may not omit it.

## Subagent report format (mandatory)

In every dispatch brief, state the response format explicitly — otherwise the subagent will drag in
code and dumps:

- conclusion: `file:line` + the gist, **≤8 lines**; do NOT send code, diffs or logs;
- **changed files** — a list of paths (what and where), ≥3 files — a compact table;
- the full build/test/dump output — write it to a file and return the path;
- not enough data — a short question, not a guess.

Details live in files; only a pointer enters the driver's context.

## Worktree sub-tasks of one cycle: subagent prompt template

If the plan chose (or the user asked — §Unit execution mode in `references/plan.md`) to perform
**sub-tasks of one cycle** (one PLAN/contract) in parallel in separate worktrees, give each task to
`pdca-executor` as a **separate dispatch** with this brief (substitute the task and paths):

```text
Task: <what to do>.
Work ONLY in worktree <ABS_WT>.
- In bash always: cd <ABS_WT> && <command>
- read/edit/write/glob/grep — only with absolute paths inside <ABS_WT>;
  do not touch the shared tree <ABS_MAIN>.
- At the end: git -C <ABS_WT> add -A && git -C <ABS_WT> commit -m "<task>: <summary>"
  (allowed: an isolated unit branch, not the working branch; never push)
- Return COMPACTLY (≤8 lines): branch, changed files, build/test result,
  open questions; do NOT send code/diffs/logs — full outputs to a file, give the path.
```

Why this way: a subagent inherits the session directory (a subagent dispatch has no worktree
parameter), so isolation rests on absolute paths and `cd`. Each task gets its own branch `pdca/<task>`,
committed; the merge and re-verification of the merged tree are done by CHECK (`references/check.md`
→ "Parallel sub-tasks in worktrees"). The unit's status file is created when the worktree is set up at
the start of DO **inside its worktree** — otherwise the files conflict on merge; it is a progress log
of that unit only, the cycle's plan stays in the main status file.

**This is one cycle, not several.** PLAN/CHECK/ACT here are shared, the sub-tasks are brought into
one tree and re-verified together. For **independent features** (each with its own PLAN/CHECK/ACT)
this template does not apply — that is N separate cycles, each isolated in its own worktree, outside
this cycle.

## Debugging (loop-back CHECK → DO)

When CHECK returned a defect and DO takes on the fix — **the cause first, then the edit:** **no fix
without investigating the cause**; fixing a symptom is not a solution. This applies both to bug fixes
inside DO and to CHECK → DO returns. The steps below are performed by `pdca-executor` (reproduce, run,
the regression test, the fix) and `pdca-scout` (tracing facts, `file:line`); the driver dispatches and
relays, it does not read stacks or code itself.

1. **Reproduce** — a stable repeat (steps, input); otherwise "fixed" is unprovable.
2. **Read the error in full** — the stack, the code, `file:line`; do not guess from the first lines.
3. **Find the source** — trace the bad value/state back along the stack to the place of origin; fix at
   the source, not where the symptom surfaced.
4. **One hypothesis** — formulate "cause X, because Y" and test it with a minimal change; do not fix
   several things at once and do not accumulate "just in case".
5. **Fix + test** — first a failing test for the original symptom, then the minimal fix; no "while I'm
   at it" refactoring (Over-Reach).
6. **Verify** — the original symptom is gone and nothing is broken, not "should work".

**Fix counter** — the base escalation counter (trigger 2). Past it the problem is no longer a
hypothesis but the architecture: a tell of an architectural problem is that each fix reveals new
coupling or a defect elsewhere.

## Status-file additions (code)

The base status file (`../../pdca/references/act.md`) plus these code rows:

- the plan section also carries: test strategy with the variant and priority matrices, docs plan,
  perf/recon/unit-mode decisions, the toolchain/lens selection, the DO task list, risks;
- **DO units/streams table** — unit | state | criteria covered | `superseded→replacement` (actual
  replacement only); an additive prerequisite keeps the original row active and adds a new active row.
  `done` is fixed by the base gate-2 rule, and the aggregate `D:` closes only when every active
  non-superseded unit is `done` and every DO stream closed/verified;
- **Perf measurement** — needed (benchmarks/suite, baseline, result) or not needed **with an
  argument** (`file:line`, one-time not per-row); a skip without an argument fails gate 1;
- **Reconnaissance** — needed (what we prove, harness, result) or not needed **with an argument**; the
  experiment-only case records the frozen contract, verdict and fork;
- **Unit mode** — sequential / parallel one tree / parallel worktrees (+ why);
- **Toolchain and lenses** selected by PLAN and the evidence each must return;
- **Changed files** (paths, ≥3 as a table) and pointers (`file:line`, commits, open questions) —
  without retelling code;
- in parallel-worktree mode a status file **per unit**, created when its worktree is set up at DO
  start **inside the worktree**, named by the unit slug so files do not conflict on merge; the
  cycle's plan and cycle-level log stay in the main status file.

Everything else — durable state, defect history, unit states, lifetime, the progress log — is the
base schema.

## Handoff additions (code)

The base message block stays as it is, with two code additions:

- a `Registries: <comma-separated paths, if any>.` line in the copy block, and the scout line asking
  for the status **and the needed registries/baseline** on demand;
- **commit advice, optional, before the block** (the base forbids anything after it): when the work on
  the task is fully finished, tell the user they may stage the changed files and commit them so as not
  to accumulate changes in the tree. Advice only — the cycle itself never commits and never pushes.
