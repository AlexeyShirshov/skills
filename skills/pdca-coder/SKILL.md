---
name: pdca-coder
description: "Programming overlay for the PDCA family — applies to the chosen form (ordinary cycle, incremental step, collection item), adds code-specific facts, tools and evidence, and inherits the base goals, gates and safety. User-invoked — runs only when the user explicitly names `pdca-coder`."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# pdca-coder: the programming overlay

**This is an overlay, not a cycle.** It contains only its differences from the base contract: no PLAN
of its own, no state machine, no second status file, no separate routing branch.

**Load order.** The base `../pdca/SKILL.md` first, then this file. When the chosen form is not the
ordinary cycle, the form contract (`../pdca-incremental/SKILL.md`, `../pdca-collection/SKILL.md`)
also loads before this one. The base phase references load at the start of their phase, exactly as
the base says; this overlay's references load the same way (§References).

**One PLAN, one state machine, one status file.** The overlay is applied **to** the form PLAN chose —
an ordinary cycle, an incremental step, the relevant items of a collection — and never opens a second
cycle, a second gate set or a second durable state.

**If this file and the base disagree on a base rule, the base wins.** This file only adds. Where it
restates a base rule in one line (a reminder for the code reader) the base text is authoritative and
the restatement adds nothing.

## When it applies

- **Software work in any stack** — writing and changing code, tests, documentation, refactoring and
  configuration. The overlay is stack-agnostic: PLAN selects the toolchain and the review lenses per
  task (§Toolchain and lenses), and a project overlay supplies the concrete commands, thresholds and
  formats.
- **Auxiliary verification code does not reclassify a non-coding goal.** A checker, script or utility
  written to verify an otherwise non-coding result makes **that component** coding work; it does not
  turn the whole goal into a coding task and does not apply the overlay to the whole campaign.
- **It applies to the relevant component or step**, not to a whole campaign: a step that touches no
  code runs without it, and specialised knowledge is loaded **only for the current step** — not every
  language/quality skill at once. Specialist IDs come from the repository; the overlay names the
  generic ones.

## Toolchain and lenses

The cycle is stack-agnostic; **the toolchain and the review lenses are selected by PLAN for each
concrete task**. This selection is mandatory, is recorded in the plan and the status file, and gate 1
checks it is present. Five steps:

1. **Identify the deliverable type.** Code/implementation, tests, prose/API documentation,
   configuration/infrastructure, refactoring, or a mix. The deliverable type drives which lenses are
   needed.
2. **Discover the project's declared toolchain (facts, via `pdca-scout`).** The build/test/lint/
   validate/render commands and their config: project manifests, CI workflows, `Makefile`/task
   runners, README, the project overlay. If the project declares no build gate (e.g. a docs-only or
   config-only change), PLAN states that and names the manual/structural checks instead.
3. **Select the correctness lenses appropriate to the artifact.** Generic default set: design
   (structure/duplication), data/type design, correctness/anti-pattern scan, test strategy,
   performance measurement, reconnaissance — the last three always carry a mandatory decision. The
   lens set is tailored to the artifact (e.g. a docs-only change keeps the doc lens and drops the perf
   lens).
4. **Bind each lens to an available, permitted agent/skill — or an explicit generic-role path.** Only
   agents/skills the host actually exposes may be dispatched. A **missing optional lens is replaced by
   an explicit generic-role path** (`pdca-scout` for facts, `pdca-executor` for mechanics, `pdca-check`
   for judgment) — never silently dropped, and never a fabricated agent name. The escalation/security
   roles stay reserved to their triggers.
5. **Freeze the selection and the evidence each lens must return** (command/exit code/numbers for a
   build; `file:line` + rule for a review; source pointers for a claim). The frozen selection is what
   DO executes and CHECK verifies against.

**Worked example — CODE.** Task: *implement a small Python CSV-summary CLI that reads a CSV path and
prints per-column count/min/max.* PLAN's selection:

- toolchain: the project's declared test command (e.g. `python3 -m unittest discover`) and its
  declared lint command if any; if none is declared, PLAN names the run command explicitly;
- lenses: **correctness/error-handling** (rows with missing/malformed fields; type inference),
  **CLI/UX** (arguments, exit status), **security** if it reads untrusted files (path handling,
  resource limits), **performance** only if the matrix shows a per-row hotspot;
- acceptance criteria: valid CSV summarizes correctly; **empty input** (header only) is handled;
  **malformed rows** produce a clear error and a **nonzero exit status**; output is **deterministic**
  (stable column order and formatting); a negative case per criterion (e.g. a bad path must fail, not
  print an empty summary);
- test strategy: unit cases for parsing/summary plus one end-to-end CLI invocation; variant-matrix
  rows (empty, one row, many rows, malformed, missing file) each closed as test/guard/deferred.

A task may combine streams (e.g. a tool plus its README): PLAN selects the union, and each stream
carries its own lens subset.

## Code-specific plan deltas

On top of the base gate-1 fields, a code plan carries the **test strategy with its variant matrix**,
the **docs plan**, the **performance-measurement decision**, the **reconnaissance decision**, the
**unit execution mode** and the **toolchain/lens selection** — each with an argument; a silent skip
fails gate 1.

The full code design checklist — two-beat PLAN, the six lenses and what to look at, plan quality
(variant/priority matrices, fail-open ban, "what the statement did not say"), minimal solution and
first principles, unit execution mode, performance measurement, milestone scope, prototype/
reconnaissance, test strategy and its anti-patterns, documentation owners — is in
`references/plan.md`. Load it at PLAN start, together with `../pdca/references/plan.md` (base plan
fields, command contract, frozen evidence manifest, vacuous/expected-negative runs, recorded
exceptions, re-anchoring).

### Language and correctness anti-patterns

The scan the correctness lens runs, and PLAN must not plan around:

- **String handling** — culture/locale/encoding assumptions, slicing, chains of `Replace`/`Format`.
- **Collections and iteration on a hot path** — per-call allocation of collections/maps, repeated
  enumeration, `Count()` over a lazy sequence, quadratic joins.
- **Regex** — catastrophic backtracking, compiled-vs-per-call, culture-sensitive options.
- **I/O and serialization** — unbuffered streams, sync-over-async, deserialization of untrusted input
  without limits, culture-dependent number/date parsing.
- **Async** — `async void`, fire-and-forget, `.Result`/`.Wait()`, missing `CancellationToken`
  propagation, `ConfigureAwait` misuse.
- **Design and types** — god classes, fat interfaces, leaky contracts, interface/implementation pairs
  without a second consumer, type-switch, needlessly open/final types, defensive copies, mutable
  collections leaking from a public API.

**Optional-null/default** (an optional value with a null/default fallback, especially `*Options`) is a
finding when it lets a wrong behavior be chosen silently — fix with a pair of overloads (a minimal one
that sets the fallback internally, a required one that rejects the missing value at the boundary).
CHECK detail: `references/check.md`.

### Code evidence requirements

- **Every run**: exit status (read from `<stem>.rc`, never from prose), key numbers (passed/failed/
  skipped, warnings, coverage), and the path to the full log — never the log in the message.
- **Diff facts** come from a non-author (`pdca-scout`: changed files, `git diff --stat`, `file:line`).
- **A regression test is red↔green** — it failed without the fix and passes with it, both runs by
  `pdca-executor`, both exit codes reported. "Passed once" proves nothing.
- **Build/lint is a gate**: clean under the project's own warning/error policy; a new warning or lint
  error is not a fix.
- **Coverage and mutation** are numbers with a baseline and the project threshold, not adjectives; a
  green line % does not prove new branches were exercised.
- **A report ≠ a result**: "build should pass", "tests look green", a self-written summary — order the
  run. The base evidence chain (re-run → observe → judge) is unchanged; this overlay only fixes what
  a code run must return.
- **The candidate carries its own index**: the plan-pinned `manifest.json` with a row per `required`
  criterion (evidence pointers, not restatements) and the staged `plan_lint` receipt for the
  `commands.json` projection. DO writes both before reporting the candidate; without them there is
  no candidate, and CHECK spends the round re-gathering instead of judging.

### Build and test command forms

The base command contract (selector resolves, argv survives the harness, phase is legal, scope matches
the host capacity, expected outcome declared) applies unchanged. Code-specific additions:

- **Inner loop = the affected subset.** Build the affected project once when compilable inputs change,
  then run it: `dotnet test <project> --no-build --filter <selector>`, `pytest -k <expr> <path>`,
  `cargo test <module>`, `npm test -- <path>` — or an unfiltered run of the affected **unit** project.
  Having a filter is not what makes a run "unit": a mixed run that actually executes integration cases
  is integration.
- **Unit runs are unrestricted; an expensive integration run happens only at the stream/DO→CHECK
  boundary**, within the plan's recorded boundary allowance. Running integration inside DO is a
  **recorded policy deviation**, not something to mask with a phase name or a rename. Widening the run
  to a shared contract or an external dependency needs a scope amendment validated **before** the run,
  with the reason recorded.
- **Never the whole solution in the inner loop**, and never two heavy suites in parallel or beside the
  editor/agent stack.
- **A run that selects zero targets is a failed run** whatever its exit status (base vacuous-run rule;
  in code: zero discovered tests, zero executed cases, an empty result set).
- **Every run leaves three artifacts, not one log**: `cmd > <stem>.out 2> <stem>.err; printf
  '%s\n' $? > <stem>.rc`. A merged stream (`2>&1`) erases exactly what a negative criterion claims
  (empty stdout, non-empty stderr), and an empty log without `.rc` cannot be told apart from a run
  that never started. Don't pipe the run through `| tail` (it buffers to EOF and looks hung); a
  `| tee` is optional for visibility and never replaces the artifacts.
- **Never record a run that did not start**; every started run is reported, including failed and
  cancelled ones.

### Test run safety (every phase — DO and CHECK)

Put these in the `pdca-executor` / `pdca-check` brief; CHECK rejects a violating report:

- **Cap the test-host resources** so a runaway recursion/allocation fails fast instead of OOM-killing
  the machine: the toolchain's memory limit and a wall-clock `timeout 600 …` (raise only when
  justified). Exit **137** / "Out of memory" ⇒ the test is unbounded: stop, record the test name and
  the command, do not re-run without the cap.
- **Serialize heavyweight suites:** never two heavy test suites in parallel, and never beside the
  editor/agent stack (agent workers, editors, language servers); run the affected project alone. A
  database/service suite runs at the stream boundary, not per edit.
- **Stream the log, never `| tail`**; always return the log path **and** the exit code.

### Security boundaries

- The base constraints (permission boundaries, credential confidentiality, untrusted content,
  authorization for consequential actions) are in force unchanged.
- **Never print, copy or upload secret material** — environment files, `secrets.env`, `auth.json`,
  keys, tokens. To check one, report "set / not set", never the value.
- **External input is untrusted**: no execution of retrieved content, no path traversal, no unbounded
  allocation/deserialization on it.
- **A triggered security review is a required stream, not advice**: when the diff touches
  auth/secrets/external input/crypto, the security auditor's report is part of gate 3 — its absence
  is `unverified`, not a pass.

### Optional specialists

Selected by PLAN, dispatched as extra gathers whose reports join the aggregate; they never issue a
verdict (that stays `pdca-check`'s) and never widen permissions. Tiers are role labels only:

| Specialist | When | Tier label |
|---|---|---|
| `pdca-security-auditor` | diff touches auth/secrets/external input/crypto | medium |
| code/correctness lens | always (code audit gather) | cheap |
| test lens, doc lens | always | cheap |
| perf specialist / profiling analyst | perf decision = needed; analyst only with ready artifacts | cheap |
| concurrency/async lens | races, hot shared state, async boundaries | cheap |
| docs/format specialist | prose or mandated API docs | cheap |

Answers come from the repository's declared skills/agents; a missing optional specialist is replaced
by the explicit generic-role path (§Toolchain and lenses step 4), never by a fabricated name. Tiers
bind to models in the host profile — no model id is written here.

## Code-specific check deltas

CHECK keeps the base two beats and the base verdict; the code overlay adds the streams.

- **Four unconditional streams plus security when triggered** — code audit, test, doc, perf — run in
  **parallel**, plus trigger-only gathers (concurrency, profiling with data). Results converge in one
  aggregated report; gate 3 needs **all green**; any failed stream is a failed CHECK of the current
  revision for the base counter.
- **Code audit is two-phase**: cheap gather (build/lint clean, suppressions/slop, smell, public API,
  doc coverage, raw `file:line` candidates) → judgment in `pdca-check`.
- **Test lens**: the suite matches the PLAN test strategy, every variant-matrix row closed, coverage
  not below the project threshold, branch delta and mutation reported.
- **Doc lens**: prose docs created **and** matching the implementation; generated API docs only when
  mandated or requested.
- **Perf lens**: numbers and baseline, judged against the PLAN perf decision.
- **One approved PLAN**: the `pdca-check` session is resumed for an implementation loop-back under an
  unchanged plan, and reset only after PLAN/ACT — it never resets the base counters or defect history.
- **Worktree sub-tasks**: the merged tree is rebuilt and re-tested before gate 3; green branches do
  not make a green merge.

Full text — the two beats, the session rule, every stream's brief and the audit workflow items 1–13,
the optional-null smell, the worktree merge steps: `references/check.md`.

## Code-specific do/act deltas

### Parallel DO streams (code + tests + prose docs)

**Code, tests and prose documentation are written simultaneously** right after the plan — not "test
then code", not "docs later". There is no TDD ordering in DO; the only red→green requirement is the
**regression test of a bug fix**.

- **Shared contract first, only if the streams need it**: signatures and types without implementation,
  then frozen — only PLAN changes it.
- Then three streams in one turn: code, tests, prose docs. Code depends only on the plan (+ the
  frozen contract), not on tests/docs; tests only on the plan, not on code/docs; prose docs only on the
  plan, not on code/tests. Anything writing the **same file** from two streams is not parallelized —
  it moves into the contract or the task stays single.
- **Generated/API docs follow the finished code** — they live in the files the code stream owns, so
  they are written after it, and only when mandated or requested.
- **The streams never write the status file**: each stream report is logged by a separate short
  `pdca-executor` dispatch, one at a time.
- Stream divergence (tests ↔ code, docs ↔ behavior) is a defect found by **CHECK**, not by DO.
- Independent **units** (not streams) launch in parallel the same way, in one tree or per worktree.

The full protocol, its invariants and rationale, the coder editing discipline (one axis per step,
verify after each step, minimal blast radius, line endings, build/lint gate, no benchmark
conclusions), the mandatory subagent report format, debugging order for a CHECK → DO fix, and the
code status rows are in `references/act.md`.

### Worktree sub-tasks

When PLAN chose separate worktrees for the sub-tasks of **one** cycle, each task is a separate
`pdca-executor` dispatch that works **only** with absolute paths inside its worktree and commits to
its own branch `pdca/<task>` there — a mechanical isolation step, not a delivery; push never happens.
The unit's status file is created inside its worktree, so it cannot conflict on merge; the cycle's
plan stays in the main status file. The merge and the re-verification of the merged tree belong to
CHECK. Template: `references/act.md` → "Worktree sub-tasks of one cycle".

**This is one cycle, not several.** Independent features (each with its own PLAN/CHECK/ACT) are N
separate cycles, not worktree sub-tasks.

### Status, ACT and handoff additions

- **Status schema additions** (code rows only): test strategy with its matrices, docs plan,
  perf/recon/unit-mode decisions, the toolchain/lens selection, the per-unit/stream table with
  criteria covered, changed files as a table, and — in worktree mode — one status file per unit inside
  its worktree. Durable state, unit states, defect history, lifetime and the progress log stay exactly
  the base schema.
- **Do not commit or push** as part of the cycle. The only exception is the worktree unit branch above.
  Commits to the working branch happen only on an explicit request; push never without a separate
  explicit one.
- **Handoff**: the base next-session block, plus a `Registries:` line and the registries/baseline in
  the scout request; optional commit advice is placed **before** the block (the base forbids anything
  after it) and is advice only.
- Project registries/`AGENTS.md`: edited by `pdca-executor`, bookkeeping only, never inside ACT when
  the edit could affect the checked result — the base rule applies unchanged.

## Composition

The overlay composes with the base by addition only.

| Base area | What this overlay does |
|---|---|
| Entry, one PLAN, forms | inherits; never classifies, never re-plans, adds no form |
| Roles and host requirements | inherits; adds optional specialists as gather-only roles (§Optional specialists) |
| Control modes, approval, campaign/cycle control | inherits unchanged |
| State machine and counters (`N`, `r`, `n/3`, `rv`) | inherits unchanged — no local counters and no execution-variant enum of its own |
| Lens/probe/increment/step boundary | inherits; a code increment is one code question with its own check |
| Gate 1 | inherits the base fields **and** adds the code decisions (§Code-specific plan deltas) |
| Gate 2 | inherits; a code unit/stream is `done` only under the same rule |
| Gate 3 | inherits; adds code streams and their evidence |
| Gate 4 / ACT | inherits; adds only the status rows and handoff lines above |
| Claims and veto | inherits unchanged — a code finding against a carrying claim blocks PASS |
| Evidence over assertion | inherits; adds what a code run must return |
| Effort accounting | inherits unchanged — no autonomous cutoff; the overlay adds no new minutes/costs and no renewal |
| Recovery | inherits; after compaction the code state (unit mode, worktree branches, streams) is rebuilt from the same status file |
| Escalation | inherits the triggers and the no-4th rule; code adds the trigger examples (public API/compat, concurrency, migrations, crypto) and the rule that an ordinary security finding is an ordinary failed stream, while a **hard security trade-off** escalates immediately |
| Generic constraints, red flags | inherits; code-specific red flags are added below |

**Code-specific red flags** (the base list still governs):

- "Tests/docs later", "test strategy as I go" — in DO all three streams run in parallel.
- A fix without a failing test for the original symptom, or a fix without investigating the cause.
- The whole suite (or an integration suite) re-run after every micro-edit in the inner loop.
- A run reported without exit code, numbers and log path; a test run without the resource cap.
- Units in parallel with overlapping footprints, or edits outside the unit's footprint.
- Work outside its own worktree, or a worktree unit committed to the working branch / pushed.
- A triggered security review skipped, or a security finding routed around the aggregate triage.
- A "green build" accepted as the result of a change nobody re-ran.

**Project overlay and project checklists (preserved).** A repository may have its own additions — a
project instruction file, a project skill named `*-pdca`, a project-level skills directory, its
`AGENTS.md`. Have `pdca-scout` find it and report its rules **before PLAN**, and follow it on top of
the contract: it refines invariants, finding registries, report formats and lens prefixes, and takes
priority over the generic advice. It may **not** override the state machine, the gates or this
overlay's safety rules. A project subagent declared without an explicit model inherits the parent's
model — either bind it in the host profile or inline the instructions into the project checklist.

## References

Loaded at the start of their phase (the host truncates tool output, so a contract loaded whole would
lose its tail — the base rule):

- `references/plan.md` — code design checklist, plan-quality rules, unit execution mode, performance
  measurement, reconnaissance, milestone scope, test strategy with the variant matrix and coverage,
  documentation owners, the code plan section and approval prompt. Load with
  `../pdca/references/plan.md`.
- `references/check.md` — CHECK two beats, the `pdca-check` session rule, parallel streams and the
  security gather, the audit workflow items 1–13, the optional-null smell, worktree merge steps.
  Load with `../pdca/references/check.md`.
- `references/act.md` — parallel DO streams, coder editing discipline, subagent report format,
  worktree template, debugging order, code status rows, handoff additions. Load with
  `../pdca/references/act.md`.
