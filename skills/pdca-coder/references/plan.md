# PLAN deltas for code: design, decisions, strategy

Reference for the PLAN phase of the programming overlay. It holds only what the base PLAN does not:
the code design checklist, the mandatory code decisions (unit mode, performance, reconnaissance),
the test strategy and the documentation plan. Gate-1 fields, the command contract, the frozen
evidence manifest, vacuous/expected-negative runs, recorded exceptions and re-anchoring stay in
`../../pdca/references/plan.md` and `../../pdca/SKILL.md` — read them there, not here.

## Two beats and the lenses

PLAN runs in two beats (like CHECK), so as not to load code into the driver's context:

1. **Gather (cheap):** review the **area of change** (not the whole repo) via `pdca-scout` + the
   selected domain lenses — findings (`file:line`, counters, structural-invariant ratio,
   anti-pattern hits), no code.
2. **Decide:** `pdca-planner` reads **only the summary**, chooses fix-now vs deferred, decomposes,
   fixes the plan. Do not pull code into context — a missing datum goes to the gatherer.

Six lenses (as selected per task — §Toolchain and lenses in `../SKILL.md`): design (SOLID/DRY),
data/type design, correctness/anti-pattern scan, test strategy, performance measurement,
reconnaissance (the last three have mandatory decisions below). Skills (via `skill`): the project's
declared design/quality skills; only available/permitted ones are named.

Look at:

- **Design (SOLID/DRY):** god classes/objects, fat interfaces, throwing overrides, leaky contracts,
  interface/implementation pairs without a second consumer, duplicated knowledge, type-switch.
- **Data/type design:** needlessly open/final types, mutable/defensive-copy value types, leaky
  mutable collections from a public API, async/await misuse, per-call allocation of collections/maps.
- **Correctness/anti-pattern scan:** string handling (culture/locale/encoding, slicing, replace
  chains), collections/iteration on a hot path, regex, I/O/serialization, async.
- **Structural invariants:** count invariant-preserving vs open types and report the ratio
  (Verify-the-Inverse), not a verdict on one type.

## PLAN owns the quality of the plan

Treat a weak statement (vague issue, half-written criteria, no edge list, habit-sketched solution)
as a **hypothesis to test**, not a contract to obey. PLAN owns plan quality regardless of input:

- **Reconstruct the goal in essence** first (§Minimal solution) — do not inherit a presupposed
  solution.
- **Derive/complete acceptance criteria** from the required observable behavior (each with a
  negative case), not the wording.
- Keep a **"What the statement did not say"** list; every gap closes one of three ways: (a) evidence
  (`file:line`), (b) an explicit **assumption/risk**, (c) a **blocker/`pdca-escalate`**. A silent
  guess is forbidden.
- Enumerate the **variant matrix** from the **execution path**, every row closed as test / guard /
  `deferred with a trigger`; surface what the input left unsaid (missing constructor/mapping, value
  vs reference types, absent/default/uninitialized, explicit projection vs whole object,
  per-provider behavior).
- Never pass incompleteness to DO: resolve in PLAN (or record an assumption/blocker). A genuinely
  new prerequisite/blocker surfaced by execution means DO cannot finish under the contract: it goes
  **DO → ACT** with the cause, evidence and residual requirements, not improvised and not to PLAN.
  A wrong or unachievable contract is a CHECK finding and only CHECK returns to PLAN.
- **PLAN assigns priority; CHECK applies it.** The severity map ("what is P1 by construction") is
  fixed in PLAN — from (1) the statement's explicit invariants, (2) the overlay's class-priority
  table, else (3) PLAN authors the row set from the execution path and the sibling's edge list (the
  only option in autonomous). Freeze the priority matrix before DO. `pdca-check` may not downgrade a
  requirement/class row and must answer every row with a finding or "checked clean, `file:line`".
- **Prefer the existing approach:** before designing new, look for an applicable approach in
  neighboring classes/methods/features and reuse it; originality only when it does not fit, with an
  explicit reason. Feed the sibling's **edge list** into the variant matrix — do not re-derive from
  memory.
- **No fail-open degradation:** an unsupported shape/branch must not silently change observable
  semantics; without support **throw** a typed error (matching the sibling's class).
  Catch-and-continue with a substituted value is forbidden.

A thin requirement is no excuse for a happy-path plan. An unenumerated execution variant is a
**PLAN defect**: gate 1 fails, and if found in CHECK it is a **CHECK → PLAN** loop-back. A weak
statement raises PLAN's burden, it does not lower the bar.

### Minimal solution and first principles

For a non-trivial plan, record in the plan answers to: (1) the goal **in essence** (which result,
not which edit)? (2) constraints that **must not** be violated (public contract, compatibility,
invariants)? (3) the optimal solution **under these constraints**? Keep it **minimal** (YAGNI
ladder): no functionality without a consumer → reuse what exists → standard library → platform
capability → only then a dependency/new code; "the minimum that works". A superfluous abstraction,
"future" config or generalization without a second consumer is a PLAN finding like duplication.
Perf measurement and reconnaissance are needed only if they affect the solution choice.

**Alternatives:** for a non-obvious/trade-off choice, present **2–3 options** (approach / pros /
cons, cost and risk) and a recommendation ("I take A, because …"); a single option only if truly
obvious, else `pdca-escalate`.

**Chesterton's Fence:** do not change/delete something until you understand why it is there
(history/`git blame`, consumers); "looks superfluous" is not a reason.

### Re-entry after a terminal `incomplete` / STOP

When a task resumes after a terminal `incomplete`, the prior terminal reason is a **required input**
to PLAN. It may not re-run the criterion whose proof failed **unchanged**: it must either (a) show
that the failed proof is now obtainable (new evidence or a fixed harness, demonstrated per §Test
strategy → "Decisive evidence") or (b) **re-scope the criterion** to a reproducible oracle. A plan
that silently re-attempts the same failed proof is **not** `ready`.

### Unit execution mode (mandatory decision)

PLAN splits the feature into **units** (`D:` tasks/streams) and **explicitly decides** their
execution mode (recorded in plan + status file). `pdca-planner` decides **by footprint** (which
files/contracts each unit touches); the roles execute.

- **Sequential** (default, if dependencies) — in order, **one** tree.
- **Parallel in one tree** — independent units (footprints don't overlap), no build isolation
  needed.
- **Parallel in separate worktrees** — only when isolation is needed (independent build per branch,
  risky/experimental unit, or user asked); units commit to own branches, and CHECK adds merge +
  re-verification.

Independence invariant: units **do not share mutable files or a shared contract**; any footprint
overlap ⇒ sequential, or **one** cycle with a shared contract (step 2 of §Parallel DO streams in
`references/act.md`). "Looks independent" without a footprint is not a reason. The mode is **visible
at gate 1** (plan + approval); the user can override.

### Performance measurement (mandatory decision)

PLAN **explicitly** decides whether a **runtime measurement** is needed and records the argument in
the plan and status file. A silent skip or "not needed" without an argument fails gate 1.

- **Needed** — the change touches a hot/repeated path (per-row/per-item work: parsing, binding,
  materialization, serialization, cache handling) or the overlay requires acceptance. Record **what**
  to measure (existing benchmark/suite, a new case, a profile) and the **baseline**.
- **Not needed** — with proof: not on a per-row path (per-column/one-time: metadata, config-time
  validation) or docs-only; point to the `file:line` where the work runs once.
- A change adding work **into a per-row loop**, without a measurement (or a project benchmark gate),
  does not close the cycle.

**Project invariants take priority over generic advice** (§Composition in `../SKILL.md`, project
checklists).
Plan output (into the plan): findings by severity (🔴/🟡/ℹ️), `file:line`, a one-line fix + the
applicable invariant; split **fix now** vs **deferred with a trigger**. The edits are applied by
`pdca-executor` in DO, not by PLAN.

### Scope and the milestone

**Scope does not leave the current milestone.** If the project tracks milestones: a task that cannot
finish this cycle may be **split**, but every slice stays in the **same milestone** — moving the
leftover to the next milestone is forbidden; an unimplemented slice is a separate unit/issue *in
that milestone*, not deferred. Documenting a limitation does not replace the task.

### Prototype / reconnaissance (spike) — mandatory decision

PLAN **explicitly** decides whether an unknown **blocks the choice of solution** (driver/API
behavior, memory, seam shape). A silent skip or "decide as we go" fails gate 1; **asserting without
measuring is forbidden**. `pdca-planner` collects nothing: the experiment runs on cheap roles —
`pdca-executor` (commands, harness, numbers) and `pdca-scout` (facts, versions, docs) — the driver
only dispatches, `pdca-planner` judges (measure cheaply → judge on medium).

- **Regression / red-arm reconnaissance.** If the plan's decisive evidence is a red↔green proof, the
  decisive probe must be shown to **run and fail (red)** from the declared source before the plan is
  frozen; a deferred red-arm demonstration is a gate-1 failure (§Test strategy → "Decisive
  evidence").
- **A spike task in the normal cycle** — the unknown blocks the fix choice; a separate `D:` with an
  acceptance criterion = an **observable fact**; the result is evidence, then usual DO → CHECK.
- **An experiment-only iteration** — the unknown blocks even the decision; the whole cycle is the
  experiment, the product is unchanged (frozen public contract), the "product" is the verdict. Gate 1
  adapts: goal = the question; criteria = reproducible harness + metric; test strategy = an
  integration probe behind an env gate (unit explicitly deferred); perf = "no acceptance required"
  **with an argument** (path unchanged) or a harness measure; docs = public docs untouched, protocol
  in the status file; risks include a "false pass" and the ban on weakening a guard for the
  experiment. ACT fork: pass → new `P:` for implementation; fail → revise/abandon.

Hygiene (both): PoC lives **outside `src/`** behind an env gate; CHECK verifies it did not leak into
the product diff. Result = reproducible command + numbers/observation + exact dependency version.
Utilization: **delete** it or turn it into a test/benchmark — "kept just in case" is not allowed. The
PoC changed the answer → before the contract is frozen, refine the same pending PLAN; once in DO,
report the changed premise to ACT (incomplete) and let a CHECK finding drive any contract revision.
A PoC may precede the plan but must not be the plan: for a shipping change gate 1 is not cancelled.

## Test strategy (PLAN → TEST)

For each cycle task PLAN decides **how to verify it** before DO — the cases become the acceptance
criterion, independent of the implementation (in DO tests are written in parallel with code/docs). If
tests need a shared contract (abstraction/DTO/signature), name it here — it becomes DO step 2.

- **Unit** — pure logic, branching, boundaries (new public method/class, rules, mappers, value
  objects); one test per behavior, name = assertion.
- **Integration** — what a unit test cannot see: data store (real database/broker/storage),
  HTTP/endpoints, DI graph, serialization/snapshot, migrations; use the project's
  integration/snapshot tooling.
- **E2E** — the full user-visible path, only when the project declares such a suite.
- **Not covered** — trivial proxies and logic-free data/DTO types; recorded as `deferred` with a
  trigger.

### Variant/branch matrix — mandatory, before the cases

Enumerate the change's execution variants on the axes that matter (input kinds;
`null`/default/uninitialized; value vs reference types; missing constructor/mapping; explicit
projection vs whole object; per provider/backend; on/off flags) and close **every** row: test, guard,
or `deferred` with a trigger. A happy-path list is not a strategy; unenumerated edges hide coverage
gaps and silent corruption. The matrix is PLAN's deliverable; CHECK verifies each row.

### Decisive evidence must be provably obtainable before gate 1 (no undemonstrated arms)

A binding acceptance criterion whose proof is state-dependent — the negative/baseline arm of a
regression (red↔green), or any criterion that reproduces a specific state — must be shown
**obtainable from committed or otherwise reproducible sources before the plan is frozen**, by a
reconnaissance run of the decisive probe against the declared baseline (§Prototype /
reconnaissance). A *declared* source identity is not enough: a valid-looking commit can still not
contain the required arm. If the arm cannot be reproduced — e.g. the only "red" lives in a
rejected/uncommitted artifact, or the probe does not execute against the declared baseline — the
criterion is a **GAP** (like "no consumer"): **not** `ready`, gate 1 fails, and the plan must
**re-scope it to a reproducible oracle**, never carry it as an in-cycle prerequisite or a `ready`
placeholder.

### Coverage comes from the project, mandatory

Find the project's coverage config/threshold (gather via `pdca-scout`/the test lens): the project's
build/test config files, coverage config, the CI workflow, a baseline artifact. **The project
threshold is the lower bound** — do not lower it; new code comes with tests. No config → record the
baseline explicitly; do not invent a threshold.

**Branch, not only line; mutation, not only green.** A green line % does not prove new branches are
exercised: report the **branch** delta and run **mutation testing** (the project's mutation tool,
scoped to the touched module) — surviving mutants on new code are killed or explicitly justified. No
tooling → say so and list the untested branches; never imply coverage you did not measure.

Gather (the test lens): existing tests of the area (`file:line`), gaps, regression risk, config and
current coverage. Decision (case list, unit/integration/E2E, name, what it checks) by
`pdca-planner`, written by `pdca-executor`. Skills: the project's declared testing/quality skills;
only available/permitted ones are named. Output: case list + split + current/target coverage. CHECK
verifies against it.

**Anti-patterns the CHECK test lens rejects (PLAN must not plan them):** tests that survive a wrong
implementation (control: "which test still passes if the logic is subtly swapped?"); a test that
cannot fail (tautology, mock not behavior, coverage-for-the-%); happy-path only (no empty/one/many,
absent/default, upper bound); line coverage as proof; an edge without a decision; checking the
implementation instead of behavior; mocking what works (prefer real components / integration); a "for
the future" test without a criterion.

## Documentation (owners by phase)

Documentation is part of done. **Prose docs and generated/API docs are separate artifacts with
different timing.** For code this means API docs + README/guides; for a configuration change,
comments + a runbook. The condition is always **"when the project/task mandates it"**.

Prose (README/guides/user documentation) — derived from the plan, written in parallel: **PLAN**
gathers via `pdca-scout` (which docs and format); "no contract/behavior change" → record "we do not
touch the docs". **DO** — the third parallel stream, from the plan/contract, not from the code;
`pdca-executor` (+ the docs/format specialist selected by PLAN). **CHECK** — doc lens: created and
matching the implementation.

Generated/API docs — from the **finished code**; mandatory only if the project/task mandates them
(the project's doc-generation setting/config) or the user requested it: **PLAN** — `pdca-scout`
reports the setting (required ⇒ mandatory, else only on user request); **DO** — written after the
code stream (`pdca-executor`); **CHECK** — generated on every new/changed public member and matching
signatures when mandatory, else only if requested. **ACT** — the final stable-rules **AGENTS.md**
(`pdca-executor`); docs are finished in DO/CHECK, not edited in ACT.

Rule: a public contract/behavior change without updated prose docs does not close the cycle; missing
mandated API docs block closure only when the project/task mandates them. On-demand skills: the
project's declared documentation/format skills; only available/permitted ones are named.

## Plan section and approval prompt (code additions)

On top of the base plan fields, the status-file plan section of a code task carries: the **test
strategy** with the variant and priority matrices, the **docs plan**, the **perf** / **recon** /
**unit-mode** decisions, the **toolchain and lens selection** with the evidence each lens must
return, the DO task list and the risks. That is also what the normal-mode approval prompt shows
(goal, criteria, test strategy, docs plan, perf decision, unit mode, toolchain/lenses, tasks, risks)
next to the status-file path. The approval protocol itself is the base one.
