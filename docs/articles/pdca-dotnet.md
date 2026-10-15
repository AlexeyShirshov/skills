# `pdca-dotnet`: the same cycle, but with .NET gates

## 1. The problem, and when to pick this skill

An autonomous agent that "fixes C# from a task description" almost always breaks in the same way:
it builds the project, sees green tests and declares victory. But a green run proves nothing if the
tests do not intersect the change, if `--no-build` reused an old artifact, if the "full run" was
actually filtered down to zero tests, or if the report simply was not attached. The problem is not
the model but the **absence of a verifiable contract**: "done" has no single, machine-checkable
definition.

`pdca-dotnet` is an engineering contract for .NET/C# that makes "done" verifiable. In its base
mechanics (PLAN → DO → CHECK → ACT, gates as conditions for admitting the next step, roles,
parallel DO/CHECK streams) it is **identical** to the stack-neutral `pdca-coder`; the differences
are in the domain lenses and in the **additional gates** tailored to .NET. It is worth picking when
the task is C#/.NET code with real acceptance criteria: a behaviour change, a new branch of logic, a
bug fix, performance, a public API. For unrelated tasks (text, a config of another stack) it is
overkill.

## 2. Launching: "по pdca-dotnet"

This skill's trigger is **explicit**: the phrase "по pdca-dotnet" (that phrase is what selects the
.NET variant; "по циклу"/"через PDCA" lead into the general `pdca-coder` — that is how the skills
are separated in the repository's `README.md`). The variant for a task is chosen by the driver: the
logic "`.NET/C#` → `pdca-dotnet`, other code → `pdca-coder`, otherwise → `pdca`" is described in
`opencode/pdca-collection/SKILL.md`, while `pdca-orchestrator` itself is a host agent (it is not in
this repository). The skill is launched **explicitly** and does not replace ordinary tasks — an
edit without the cycle is performed directly.

## 3. Participants and tiers

The skill names only **roles**, not models: the host binds a role to a specific subagent and model
(cheap, medium or strong), while the role templates carry only a `# tier:` label — the `model:`
field is not there and must not be. The economics are built into the design:

- **the orchestrator** — cheap: it drives the cycle without pulling code into its context;
- **`scout`** and **`coder`** — cheap: facts (`file:line`) and edits/commands;
- **`planner`** and **`check`** — the medium tier: decisions (decomposition, plan) and the verdict
  (pass/fail, ranking, loop-back);
- **`escalate`** — expensive and called **rarely, by triggers**, when the cheap roles cannot give an
  answer;
- **`security-auditor`** — the medium tier, switched on **by trigger** (auth, secrets, external
  input, crypto) as a CHECK gather stream: its report returns into the `check` aggregate, and the
  stream has no verdict of its own.

The roles' permissions differ and are fixed in the templates: `planner` works from the summary,
`check` may read only the cycle's evidence artifacts (status, evidence, manifest — but never
product code), and `scout` has only read-only git from the allowlist among `bash` commands. The
economics are visible in practice too: `scripts/pdca_cost.py` computes cost and tokens by phase and
tier, and model names are not hard-coded in it.

The PLAN/CHECK domain lenses are the `dotnet-*` subagents: `dotnet-architect`/
`dotnet-code-review-agent` — design and performance during PLAN gathering (findings `file:line`,
counters, no code), while the verdict still belongs to `check`; `dotnet-testing-specialist` (what
to test and how), `dotnet-benchmark-designer`/`dotnet-async-performance-specialist`/
`dotnet-csharp-concurrency-specialist`/`dotnet-performance-analyst` (performance, the last one
**only with ready-made artifacts**), `dotnet-docs-generator` and `docfx-specialist`
(documentation). The specialized subagents are additional **gatherers** of evidence, not new gates:
the verdict still belongs to `check`.

## 4. How the .NET variant differs

### 4.1. A mandatory `test scope` and a validator that fails closed

Every implementation brief **must** carry a structured `test scope`: `projects`, `selectors`,
`files`, `rebuild` (`affected` | `none`), `boundary`, `rationale`. Without it the orchestrator
**does not send** the brief — it goes back to `planner` to be completed. `selectors` must be
precise and filtered (not "the whole project/solution"). `rebuild: "affected"` is correct for a
compilable change, while a docs-only change must go with `rebuild: "none"` (an invented rebuild
fails the gate). `boundary` is the single comprehensive point at the DO → CHECK boundary.

The inner loop is the **affected subset**: build the affected project once, then run
`dotnet test <project> --no-build --filter <selector>`; a full project/solution run in the inner
loop is a red flag. The executor runs `scripts/validate_inner_loop.py brief <scope.json>`
**before any editing** and `report <evidence.json>` **before CHECK**. The validator executes
nothing — it only parses the recorded argument arrays and JSON. Exit codes: `0` — valid, `2` — a
violation (`FAIL: …`), `1` — a usage error, unreadable or broken JSON. A non-zero code is
**fail-closed**: editing does not begin, CHECK is not skipped.

Among other things, the validator checks:

- the ban on wide selectors and on a "fake" affected rebuild for docs-only;
- mandatory execution fields: `phase` (`inner`/`boundary`), non-empty
  `source_revision`/`artifact_revision`, an integer `exit_code` and `selected_count ≥ 1`;
- the absence of shell wrappers and compound commands;
- at most one comprehensive boundary sweep and one solution build at the boundary;
- that the filters match the declared scope (otherwise — "silent scope expansion");
- that an affected build exists before the first inner test;
- the freshness of `--no-build`: `source_revision == artifact_revision` and a matching previous
  build;
- the freshness of the boundary;
- a final green result in every group.

A filtered integration test at the boundary is legitimate and does not consume the one-sweep limit.
The validator also has a third mode — `manifest <manifest.json>`: it checks the **row coverage** of
the frozen evidence manifest (see §4.2), not execution; an `open` row is a legitimate input, and it
is exactly what forbids a PASS in CHECK.

### 4.2. Versioned evidence contract: rows, the DO ledger, `rv`

At PLAN the versioned evidence contract must be **fixed** in the status file — before DO begins.
This is the single global definition: agent templates and project overlays must **reference** it
rather than set up a competing contract of their own. Every row requires:

- a stable requirement ID and a stable row ID;
- the required check or scenario;
- the expected kinds of evidence and their sources;
- the exact command/call, the requirements on the exit code (or the call's result) and on the log;
- the expected artifacts and their location, or an explicitly justified N/A;
- the owning stream responsible for producing the evidence;
- an observable applicability predicate (unconditional obligations always apply);
- the contract revision `rv`.

**"No optional slots"**: PLAN is free to choose the representation but may not omit slots or weaken
mandatory checks. The planned artifact locations are an expectation, not evidence; inventing future
test symbols or `file:line` references is forbidden — only verified existing references or
explicitly planned sources. PLAN also fixes the **final re-gather budget** (a supplementary
evidence gathering) in CHECK and its owner.

The **DO ledger** is the log of actual evidence by row ID and `rv`: verified test symbols/
`file:line`, results, executed commands, exit codes, paths to logs and artifacts. Failed,
never-run, missing and blocked evidence is recorded **explicitly**. N/A is admissible only with an
observable predicate; it does not lift an unconditional obligation.

The **frozen evidence manifest** is a single object per task that CHECK reconciles against. PLAN
fixes its path in the status file (by default `artifacts/pdca/<task>/rv<k>/`, where `<k>` is the
contract revision `rv`); DO writes the manifest, and it is **frozen** at the DO → CHECK boundary,
tied to the tree revision and `rv`. In CHECK the manifest is **only appended to** (evidence or an
`open` reason for existing rows): rewriting a row or starting a second manifest is not allowed.
The minimum: `task`, `tree`, `contract_rv`, `status_file`, `required_rows` (the contract's
mandatory IDs) and `rows[]` — one row per ID: `id`, `status` (`met` | `open` | `na`), for `met` an
`evidence[]` of references `{kind, path, command?, exit?, value?}`, for `open` a `reason`, for `na`
an observable `predicate`. These are **references, not copies**: logs and artifacts live at their
own paths, the manifest is a thin index. Every ID from `required_rows` must be in `rows[]`, and
vice versa; a row without a permitting reference is `open`, not gone.

**Revision.** If a new mandatory variant is discovered, that is a CHECK → PLAN return with a
justification: PLAN explicitly declares the supersession of the previous contract revision, keeps
the existing row IDs, adds IDs for the new variants, and retains all still-mandatory acceptance
criteria. The mere fact of "gathering more evidence" does not revise the contract. A contract
supersession does **not** cancel DO's work and does not discard unfinished criteria; the rules for
plan revisions and attempts stay as they were.

### 4.3. The CHECK completeness gate: no PASS while a row is open

Before a PASS, the check reconciles the active contract with the **frozen manifest** (a single
object per task, rows by reference) and with the DO ledger, and then **opens the references
themselves**: CHECK permits a row by reading its `path`, not by retelling the brief. **Every
applicable mandatory row** must be satisfied by actual evidence for the current `rv`; all mandatory
IDs from `required_rows` are in the `met` or `na` status, and any `open` forbids a PASS. The
required artifacts must exist and confirm the claimed result. N/A is valid only with a demonstrated
fixed predicate; unconditional obligations are not lifted.

**Missing evidence is not a product defect.**
Missing reports, logs, artifacts or check results are gathered **inside CHECK** from the assigned
owner, within the fixed budget and the existing permissions. Because of that, one cannot return to
DO, spin up a DO iteration, or render a product FAIL. Nor may evidence be invented or the product
edited during the supplementary gathering. But a **proven product defect** still requires a FAIL
and the usual loop-back, and a new mandatory variant requires a justified CHECK → PLAN with an
explicit supersession. CHECK may not silently add, remove or weaken contract rows.

If the budget is exhausted while mandatory evidence is still open, CHECK remains unresolved: the
open row IDs and the reasons are listed, and then the usual blocker/escalation rules apply. **PASS
is forbidden while an applicable mandatory row is open.** This gate adds no new phase to the state
machine, does not lower priorities and does not replace the existing correctness checks.

### 4.4. Zero warnings, coverage and mutations

The build is a gate: the project must be clean under its own warnings policy (for example,
`TreatWarningsAsErrors`). A change that introduces a warning is **not a fix**; zero warnings is
checked both in the code audit and when verifying the merged tree.

Coverage is taken **from the project** (`Directory.Build.props`, `Directory.Packages.props`,
`.runsettings`, `coverlet.runsettings`, CI, baseline) and is treated as a **lower bound** — it may
not be lowered, new code arrives with tests; with no configuration, a recorded baseline rather than
an invented threshold. A green line percentage proves nothing about new branches: the report is
kept by the **branch** increment, and mutation testing (Stryker.NET, within the affected
build/type) kills the surviving mutants or explicitly justifies them. If there is no tool, that
must be said and the uncovered branches listed, rather than hinting at coverage that does not
exist. New 🔴 CRAP hotspots are tracked separately.

Plus the run-safety requirements: a heap limit for the test host (`DOTNET_GCHeapHardLimit`, for
example 2 GiB) and a wall-clock `timeout`, serialization of heavy suites (never two test projects
in parallel, and never next to the editor/LSP), a streamed log instead of `| tail`, returning both
the log path **and** the exit code.

## 5. A teaching scenario: a .NET verification that rejects incomplete evidence

> The scenario is **teaching/illustrative**: the numbers and names are fictional, and the mechanics
> of the gates are what is shown.

Task: in the `Ordering` library a discount-calculation branch was added for a `null` customer. The
DO report arrives with four rows of evidence. The `report` validator returns `2` and prints a
structural violation:

- `execution 0 selected_count must be an integer >= 1 (zero/missing selected tests)` — the filter
  `FullyQualifiedName~Ordering.Tests` actually selected `selected_count=0`: the tests exist but do
  not touch the new branch. Zero matches is a rejection, not "green".

The structural checks fire before the freshness and boundary rules, so there are no other messages
in this run. After `selected_count` is fixed, the same `report` prints, among other things:

- `more than one comprehensive boundary test sweep: 2` — instead of one comprehensive check at the
  boundary there were two wide runs;
- `execution 1: stale --no-build artifact (source_revision != artifact_revision)` — after a
  compilable edit, a run with `--no-build` reused an old artifact: source and binary were of
  different revisions.

In addition, the CHECK completeness gate sees that the contract row "boundary: the
`null`/`default` branches" is not confirmed: its boundary evidence is invalid — the validator
rejected the report (two comprehensive boundary sweeps instead of one, a stale `--no-build`
artifact), so the row has no valid evidence — in the manifest it is `open` with a reason. This is
**not** a product FAIL but a supplementary gathering in CHECK from the owning stream (the test
lens), within the budget. Only after a real boundary run with a fresh artifact
(`source_revision == artifact_revision`) and `selected_count ≥ 1` does the row close; if the budget
is exhausted, CHECK remains unresolved with the open IDs listed rather than a PASS.

The gate distinguishes "the work is done, the report is incomplete" (gather more) from "the product
is defective" (FAIL and loop-back) — and in both cases it does not let a "green by eye" through.

## 6. The cycle's outcome and ACT

The cycle does not "end silently": ACT is a mandatory gate, and it has an observable outcome. In
normal mode it leaves **two artifacts**: a finalized **cycle status file** (filled in by `coder`
from the reports — the `check` verdict, the run results, the `file:line` facts from `scout`:
Done/Verified, Next plan, Changed files) and a ready **message for the next session**. In
autonomous mode there is no second artifact — there is no user to address, the work continues in
the same session, and the status file is kept.

The order of ACT: a transferable lesson (optional, 0–2 per cycle; a no-op is normal) → updating
`AGENTS.md`/tests (`coder`) → stable rules into the project overlay → finalizing the cycle status
file (`coder`); last in normal mode comes the "commit advice + message" block, and after it nothing.
The status file is **always kept**: via the recorded `Next plan` it either becomes the input of the
next cycle or remains a closed record. It also holds the durable state (`N`, revision `r`, attempt
`n/3`) and the **defect history** (a defect key → revisions/attempts, the number of fixes, the last
recurrence and the escalation outcome) — the counters are restored from the file, not from the
session context. Product documents are the **DO** stream; the doc lens of **CHECK** verifies them;
ACT does not edit them.

## 7. Limitations and false expectations

- **The coverage threshold is a lower bound, not a goal.** Catching up to a number with tests for
  the number's sake is not allowed: tautological tests and coverage-for-a-percentage are rejected
  by the lens. The threshold comes from the project; a missing configuration does not justify an
  invented threshold.
- **An incomplete report ≠ a product defect — but also not a PASS.** It is easy to confuse:
  "the report was not attached" is no reason to declare a FAIL, but also no reason to pass. The row
  stays open until the evidence is gathered.
- **There is no 4th attempt.** For an exhausted revision `r`, a fourth attempt is forbidden even
  after an escalation: continuation is possible only through a **substantively reworked plan** (a
  new revision, the attempt counter starting at `n=1`). `DO → PLAN`/`CHECK → PLAN` do not "spend"
  the next revision's attempts.
- **Escalation is not a universal answer.** The expensive role is called by triggers; a fourth blind
  attempt is usually more expensive than one escalation.
- **A re-entry after a terminal STOP is not a re-run of the same criterion.** The previous terminal
  cause is a mandatory PLAN input when resuming a task after `incomplete`/STOP: either it is proven
  that the failed evidence is now obtainable (new evidence or fixed tooling), or the criterion is
  redefined onto a reproducible oracle. A plan that silently repeats the failed criterion is not
  `ready`.
- **Lenses are gatherers, not judges.** The `dotnet-*` subagents bring candidates and numbers. The
  verdict, ranking and loop-back belong to `check`; zero numbers or the author's self-report is a
  fail ("verifier theater", Verifier Theater).
- **The .NET variant does not replace the general cycle.** It is the same contract with added .NET
  specifics; the state machine, the "all green" gate and the loop-back are shared.

## 8. Where to go next

Start with the family overview — [`pdca.md`](pdca.md) — then with the stack-neutral "neighbour"
[`pdca-coder.md`](pdca-coder.md): `pdca-dotnet` differs from it not in the state machine but in the
domain lenses and the additional gates (and if there are many independent tasks —
[`pdca-collection.md`](pdca-collection.md)).
The primary source of behaviour is the contract itself: the sections "Versioned evidence contract"
and "CHECK completeness gate — mandatory evidence contract" in
[`opencode/pdca-dotnet/SKILL.md`](../../opencode/pdca-dotnet/SKILL.md), as well as the role
templates that reference them
([`planner.md`](../../opencode/pdca-dotnet/assets/agents/planner.md),
[`check.md`](../../opencode/pdca-dotnet/assets/agents/check.md)) and the compact implementation of
the gate —
[`scripts/validate_inner_loop.py`](../../opencode/pdca-dotnet/scripts/validate_inner_loop.py).
An overview of the whole family is in [`docs/pdca-guide.md`](../pdca-guide.md).

## Sources

The article's normative claims were reconciled with the repository's current files (commit
`065e2b8`); where they disagree, `opencode/pdca-dotnet/SKILL.md` takes precedence. The
"claim → source" map:

| Claim | Source |
|---|---|
| The .NET variant is the same contract, the tools are replaceable | `opencode/pdca-dotnet/SKILL.md:11-13` |
| The variant per task (`.NET/C#` → `pdca-dotnet`) and the identity of the `pdca-coder`/`pdca-dotnet` base | `opencode/pdca-collection/SKILL.md:16-21,419-421` |
| The explicit trigger and the separation of the skills; "an edit without the cycle — directly" | `README.md:42-48`; `opencode/pdca-dotnet/SKILL.md:1-4,8-9` |
| Roles and tiers (`# tier:`, no `model:`); roles → agents and the fallbacks to built-ins | `opencode/pdca-dotnet/SKILL.md:15-19,62-69,71-75,84-88`; `opencode/pdca-dotnet/assets/agents/*.md:5` |
| `check` may open the evidence artifacts (not product code); `scout` — read-only git only | `opencode/pdca-dotnet/SKILL.md:21-26,996-999`; `opencode/pdca-dotnet/assets/agents/check.md:6-22`; `opencode/pdca-dotnet/assets/agents/scout.md:6-23` |
| `security-auditor` is a conditional gather, its report returns into the `check` aggregate | `opencode/pdca-dotnet/SKILL.md:69,1030-1037` |
| The economics in practice (cost/tokens by phase and tier, no model names) | `opencode/pdca-dotnet/scripts/pdca_cost.py:4-6,28-31,93-99` |
| The mandatory `test scope` (fields, wide selectors, docs-only/`rebuild`, the boundary) | `opencode/pdca-dotnet/SKILL.md:535-564` |
| The validator: the `brief`/`report`/`manifest` modes, the `0`/`2`/`1` codes, "executes nothing" | `opencode/pdca-dotnet/scripts/validate_inner_loop.py:1-17,578-610` |
| The scope/execution rules: wide selectors, an invented rebuild, `selected_count ≥ 1`, shell wrappers, the boundary sweep, scope expansion, freshness, final green; structural violations before the freshness/boundary rules | `opencode/pdca-dotnet/scripts/validate_inner_loop.py:172-201,252-277,293-335,338-397,400-440,453-457` |
| The frozen manifest: its path, freezing at DO → CHECK, append-only, the fields, aggregation by reference; the schema and row coverage in the validator | `opencode/pdca-dotnet/SKILL.md:944-949,956-973`; `opencode/pdca-dotnet/scripts/validate_inner_loop.py:40-48,495-562,604-605` |
| The versioned evidence contract: row slots, "No optional slots", the DO ledger, the re-gather budget, revision/supersession | `opencode/pdca-dotnet/SKILL.md:919-942,951-954,975-979` |
| The inner-loop evidence gate: CHECK fails rather than warns; the list of conditions | `opencode/pdca-dotnet/SKILL.md:1091-1101` |
| The CHECK completeness gate: reconciling contract↔manifest, missing evidence = re-gather, the ban on PASS while `open`, the budget | `opencode/pdca-dotnet/SKILL.md:1147-1168` |
| A re-entry after a terminal `incomplete`/STOP: the previous cause is a PLAN input | `opencode/pdca-dotnet/SKILL.md:718-722`; `opencode/pdca-collection/SKILL.md:66-70` |
| Quality gates: zero warnings; coverage/branches/mutations/CRAP; test-run safety | `opencode/pdca-dotnet/SKILL.md:504-505,861-870,889-902,985,1021,1070,1084-1090,1139` |
| The `dotnet-*` lenses of PLAN/CHECK | `opencode/pdca-dotnet/SKILL.md:393-398,666-671,985-994,1039-1044` |
| The ban on a 4th attempt, escalation by counter, decision routing | `opencode/pdca-dotnet/SKILL.md:139-142,603-604,608-615,637-649` |
| ACT: two artifacts, the order of steps, the status file always kept; the status file path, the durable state (`N`, `r`, `n`) and the defect history | `opencode/pdca-dotnet/SKILL.md:1194-1225,1229-1232,1246-1256,1274-1295` |
| The teaching scenario: the numbers are fictional; the skill's static matrix does not prove behaviour | `opencode/pdca-dotnet/tests/scenarios.md:3-5` |

The host artifacts (`config/agents/*.md`, `config/AGENTS.md`, `config/profiles/*.jsonc`,
`config/skills/…`) live in a separate config repository and are not shipped here: the checks
consult them only when `OPENCODE_CONFIG_REPO` is set (`README.md:59-66`); the phrase-to-trigger mapping
comes from there as well.
