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
.NET variant). The generic phrases "по циклу"/"через PDCA" go to `pdca-entry`, which routes .NET/C#
work here; naming another contract explicitly bypasses the umbrella. The variant for a task is
chosen by the dispatching skill (`pdca-entry`, or the collection/campaign per task/step) and
passed to the driver as `selected_variant`; the driver never classifies. The logic "`.NET/C#` →
`pdca-dotnet`, other code → `pdca-coder`, otherwise → `pdca`" is described in
`opencode/pdca-entry/SKILL.md`, while `pdca-orchestrator` itself ships as
`assets/agents/pdca-orchestrator.md` in every skill of the family. The skill is launched **explicitly** and does not replace ordinary tasks — an
edit without the cycle is performed directly.

## 3. Participants and tiers

The skill names only **roles**, not models: the host binds a role to a specific subagent and model
(cheap, medium or strong), while the role templates carry only a `# tier:` label — the `model:`
field is not there and must not be. The economics are built into the design:

- **the orchestrator** — cheap: it drives the cycle without pulling code into its context;
- **`pdca-scout`** and **`pdca-executor`** — cheap: facts (`file:line`) and edits/commands;
- **`pdca-planner`** and **`pdca-check`** — the medium tier: decisions (decomposition, plan) and the verdict
  (pass/fail, ranking, loop-back);
- **`pdca-escalate`** — expensive and called **rarely, by triggers**, when the cheap roles cannot give an
  answer;
- **`pdca-security-auditor`** — the medium tier, switched on **by trigger** (auth, secrets, external
  input, crypto) as a CHECK gather stream: its report returns into the `pdca-check` aggregate, and the
  stream has no verdict of its own.

The roles' permissions differ and are fixed in the templates: `pdca-planner` works from the summary,
`pdca-check` may read only the cycle's evidence artifacts (status, evidence, manifest — but never
product code), and `pdca-scout` has only read-only git from the allowlist among `bash` commands. The
economics are visible in practice too: `.pdca/scripts/pdca_cost.py` computes cost and tokens by phase and
tier, and model names are not hard-coded in it.

The PLAN/CHECK domain lenses are the `dotnet-*` subagents: `dotnet-architect`/
`dotnet-code-review-agent` — design and performance during PLAN gathering (findings `file:line`,
counters, no code), while the verdict still belongs to `pdca-check`; `dotnet-testing-specialist` (what
to test and how), `dotnet-benchmark-designer`/`dotnet-async-performance-specialist`/
`dotnet-csharp-concurrency-specialist`/`dotnet-performance-analyst` (performance, the last one
**only with ready-made artifacts**), `dotnet-docs-generator` and `docfx-specialist`
(documentation). The specialized subagents are additional **gatherers** of evidence, not new gates:
the verdict still belongs to `pdca-check`.

## 4. How the .NET variant differs

### 4.1. A mandatory `test scope` and a validator that fails closed

Every implementation brief **must** carry a structured `test scope`: the brief is an **envelope** —
`unit` (the DO unit id, a string) at the top level, and the fields nested under `scope`:
`projects`, `selectors`, `files` (mandatory key, may be an empty list), `rebuild` (`affected` |
`none`), `boundary`, `rationale` — and, for the run policy, `integration_projects` and
`integration_boundary_runs`. A bare scope object at the top level is rejected
(`missing required key: unit`). Without a valid scope the orchestrator **does not send** the brief —
it goes back to `pdca-planner` to be completed. `selectors` must be precise; a wide
selector ("the whole solution") is rejected. `rebuild: "affected"` is correct for a compilable
change, while a docs-only change must go with `rebuild: "none"` (an invented rebuild fails the
gate). `boundary` is the single comprehensive point at the DO → CHECK boundary.

**The limit is on the actual integration run, not on the number of report entries.** Unit runs are
unlimited inside DO and at phase boundaries: build the affected project once, then run
`dotnet test <project> --no-build --filter <selector>` — **or** the affected **unit** project
unfiltered. The presence or absence of `--filter` is **not** a unit-vs-integration criterion and is
never grounds to restrict a unit run. Expensive **integration** runs are permitted only at the
DO → CHECK boundary, within the scope and the count PLAN fixed in advance; an integration run inside
DO is a visible policy deviation (recorded in the ledger, not masked by a phase or a rename), and a
mixed solution run that really executes integration is not "unit" because of a command name.

The executor runs `.pdca/scripts/validate_inner_loop.py brief <brief.json>` **before any editing** and
`report <evidence.json>` **before CHECK** — reconciled with `--journal <journal.json>` when the raw
execution journal exists. The validator executes nothing — it only parses the recorded argument
arrays and JSON. Exit codes: `0` — valid, `2` — a violation (`FAIL: …`), `1` — a usage error,
unreadable or broken JSON. A non-zero code is **fail-closed**: editing does not begin, CHECK is not
skipped.

Among other things, the validator checks:

- the ban on wide selectors and on a "fake" affected rebuild for docs-only;
- mandatory execution fields: `phase` (`inner`/`boundary`), non-empty
  `source_revision`/`artifact_revision`, and — for a `finished` run — an integer `exit_code` and
  `selected_count ≥ 1`;
- the absence of shell wrappers and compound commands;
- the **kind/phase policy**: an integration run inside DO, more boundary integration runs than the
  plan allows, and a solution or integration-project run mislabelled as `unit`;
- that the filters match the declared scope (otherwise — "silent scope expansion");
- that an affected build exists before the first inner test;
- the freshness of `--no-build`: `source_revision == artifact_revision` and a matching previous
  build;
- the freshness of the boundary;
- a final green result in every group.

**Every actually-started run is recorded**, regardless of exit code, cancellation, retry or
over-budget status: the report is **projected** from the raw journal, and a projection that drops a
started execution is rejected (`projection incomplete`). The execution states are explicit —
`finished` | `started` | `running` | `interrupted` | `canceled` | `failed-to-start` | `not-started`;
exit code and selected count are nullable and are never invented for a run that did not finish, and
an unfinished attempt does not satisfy a required success even though it is retained after a
successful retry.

The remaining modes serve the evidence pack and the lifecycle. `journal` validates the raw
start/finish capture, and `project` rebuilds the report from it mechanically. `manifest <manifest.json>` checks the **row coverage** of the frozen evidence manifest (see §4.2), not
execution; an `open` row is a legitimate input, and it is exactly what forbids a PASS in CHECK while
it is binding (§4.3). Finally `cleanup` and `archived` gate the ACT cleanup receipt — the receipts
that make the removal of heavy staged material verifiable (§4.5).

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
fixes its path in the status file (by default `.pdca/<task>/rv<k>/`, where `<k>` is the
contract revision `rv`); DO writes the manifest, and it is **frozen** at the DO → CHECK boundary,
tied to the tree revision and `rv`. In CHECK the manifest is **only appended to** (evidence or an
`open` reason for existing rows): rewriting a row or starting a second manifest is not allowed.
The minimum: `task`, `tree`, `contract_rv`, `status_file`, `required_rows` (the contract's
mandatory IDs) and `rows[]` — one row per ID: `id`, `status` (`met` | `open` | `na`), for `met` an
`evidence[]` of references `{kind, path, command?, exit?, value?}`, for `open` a `reason`, for `na`
an observable `predicate`. These are **references, not copies**: logs and artifacts live at their
own paths, the manifest is a thin index. Every ID from `required_rows` must be in `rows[]`, and
vice versa; a row without a permitting reference is `open`, not gone.

**The mechanical pipeline.** The contract can be materialised as a JSON object that mirrors the
status file and handed to the skill's tracked helper, run as `.pdca/scripts/pdca_evidence.py`
(standard library only).
`generate --repo <root> --contract <contract.json> --output <evidence-dir>` resolves a frozen
synthetic tree from `base_ref` + `footprint`, writes one immutable receipt per required row and
replaces `manifest.json` last and atomically; a preflight lint refuses to regenerate over stale
evidence and a held lock refuses a concurrent writer. `lint --repo <root> --manifest
<manifest.json>` recomputes the same tree and fails on any disagreement, on a path outside the
repository, on duplicate row IDs and on a one-sided `required_rows` ↔ `rows[]` coverage. The tool
never invents an execution and never turns `open` into `met`; codes are `0` (valid), `2`
(violation) and `1` (usage/operational error).

**Binding/applicability disposition.** The frozen manifest is never rewritten and no row is ever
deleted — a pre-existing, self-imposed extra *audit* row keeps its original status and text and is
never quietly turned into `met`. Instead CHECK appends an explicit applicability disposition to that
row inside the same manifest: a stable row ID, the classification `diagnostic_nonbinding`, and the
concrete reason/basis in the agreed scope or in the priority global rule. The row may therefore stay
`open` while it is excluded from the set of **binding acceptance blockers**, and the final receipt
shows binding unmet rows and audit notes separately. This is not a loophole: it covers only
unsupported extra audit demands that follow from no agreed goal — a recursive historical inventory,
or a retrospective execution-time `committed == tested`. A failing or missing required test,
unverified direct evidence, a source-copy mismatch or a real functional/security variant stays on
the normal fail/re-gather/STOP route, and a finite audit goal that the user agreed as a **separate**
audit task stays **binding**. The mirror-image obligation binds PLAN too: in an ordinary product
task it may not freeze a hard gate on arbitrary audit completeness (a whole transitive reference
graph, retrospective hashes, an execution-time `committed == tested`); such metadata is a
**diagnostic note**, and its absence never forces `incomplete`/STOP.

**Revision.** If a new mandatory variant is discovered, that is a CHECK → PLAN return with a
justification: PLAN explicitly declares the supersession of the previous contract revision, keeps
the existing row IDs, adds IDs for the new variants, and retains all still-mandatory acceptance
criteria. The mere fact of "gathering more evidence" does not revise the contract. A contract
supersession does **not** cancel DO's work and does not discard unfinished criteria; the rules for
plan revisions and attempts stay as they were.

### 4.3. The CHECK completeness gate: no PASS while a binding row is open

Before a PASS, the check reconciles the active contract with the **frozen manifest** (a single
object per task, rows by reference) and with the DO ledger, and then **opens the references
themselves**: CHECK permits a row by reading its `path`, not by retelling the brief. **Every
applicable mandatory row** must be satisfied by actual evidence for the current `rv`; all mandatory
IDs from `required_rows` are in the `met` or `na` status, and any `open` row that is
**binding/applicable** forbids a PASS. The required artifacts must exist and confirm the claimed
result. N/A is valid only with a demonstrated fixed predicate; unconditional obligations are not
lifted.

**The gate is mechanical.** CHECK runs both tracked helpers on the frozen manifest and treats a
non-zero exit as a failed evidence gate, never a warning: `.pdca/scripts/validate_inner_loop.py manifest
<manifest.json>` (row/evidence shape and two-way `required_rows` ↔ `rows[]` coverage) and
`.pdca/scripts/pdca_evidence.py lint --repo <root> --manifest <manifest.json>` (frozen-tree binding,
recomputed independently, plus the same coverage). A tree that does not reconcile, a missing
required row, an undeclared row or a dangling evidence reference is an open evidence gate — it is
never reclassified into a PASS.

**The gate is binding-scoped, not absolute.** A retained audit row carrying a valid
`diagnostic_nonbinding` disposition (§4.2) is reported **separately** and does not block the PASS:
the receipt shows binding unmet rows and audit notes apart. The exclusion is deliberately narrow —
only extra audit demands that follow from no agreed goal — and it never covers a failing or missing
required test, unverified direct evidence, a source-copy mismatch or a genuine functional/security
variant.

**Missing evidence is not a product defect.**
Missing reports, logs, artifacts or check results are gathered **inside CHECK** from the assigned
owner, within the fixed budget and the existing permissions. Because of that, one cannot return to
DO, spin up a DO iteration, or render a product FAIL. Nor may evidence be invented or the product
edited during the supplementary gathering. But a **proven product defect** still requires a FAIL
and the usual loop-back, and a new mandatory variant requires a justified CHECK → PLAN with an
explicit supersession. CHECK may not silently add, remove or weaken contract rows.

If the budget is exhausted while mandatory evidence is still open, CHECK remains unresolved: the
open row IDs and the reasons are listed, and then the usual blocker/escalation rules apply. **PASS
is forbidden while a binding/applicable mandatory row is open.** This gate adds no new phase to the
state machine, does not lower priorities and does not replace the existing correctness checks.

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

### 4.5. The reviewer evidence pack and the ACT cleanup receipt

Two more pieces make the evidence verifiable end to end.

**Reviewer evidence pack.** An independent CHECK reads only inside its allowed roots, so at the
DO → CHECK boundary the executor **stages the full bodies** of the changed files a reviewer needs
into the task's `rv<k>` evidence directory — staging is a **copy, not a move**: the originals are
preserved. A diffstat, a paraphrase, a link to an unreadable original or isolated quoted lines is
**not** reviewable evidence. A separate, cheap **read-only source-side gather** performs the
transport and the technical check **before** medium CHECK: per staged file it records the original
path, the staged copy path, the content digest, the **source identity** of the verified
revision/working tree and the **content equality** of copy vs source — the receipt carries the
gather's actual finding, not the author's declaration. A single `HEAD` is insufficient when the
working tree has uncommitted edits, so the source identity names the state that was actually
reviewed. Roslyn resolution runs in that same gather, on the same frozen snapshot, and the pack
carries the result with the same source identity; CHECK never runs Roslyn against an inaccessible
whole solution. Any drift of the task-relevant footprint between the frozen capture and CHECK
**invalidates** the verdict, and the current revision gets a new `rv`/receipt/check. CHECK itself
reconciles each changed registry claim against the supplied confirmation and records a **row-level**
result, without loading every staged file into context and without widened read rights. A missing
body, a staged-vs-source mismatch, an incomplete justification or the absence of an independent
verdict is **evidence open/blocked** — neither a product FAIL nor a PASS. This is source-copy
fidelity, not a proof of execution-time `committed == tested`.

**ACT cleanup receipt.** Staged evidence is retained until the independent CHECK, the review and the
task closure are complete — it is not cleaned on every DO → CHECK. On a genuine **terminal closure**
ACT removes this task's heavy staged copies and temp material, and that removal is gated by a
**machine-checkable receipt** (`validate_inner_loop.py cleanup <receipt.json>`): the receipt is
bound to the task and its `rv`, to the approved terminal closure and to the independent final
verdict, and lists the removed paths with their **prior hashes** plus the retained records. The
right to terminal closure is checked **before** deletion — a receipt without it, or without the
independent verdict, is rejected as premature cleanup. The deletion scope is this task's own `rv`
directory only: a blanket `rm` of the whole task directory, a broad pattern or another task's files
are rejected, and the retained report/manifest/digests/certification are never removed.
`validate_inner_loop.py archived <manifest.json> --cleanup <receipt.json>` checks the frozen
manifest's digest against the receipt and requires every missing body to be explained by it, so a
correctly cleaned-up snapshot is a **planned lifecycle** rather than "the evidence never existed" —
while a snapshot missing *before* ACT, or without a valid receipt, stays an error. Archived
validation claims no re-certification over removed bodies and does not replace the checks.

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

- `more than one comprehensive boundary test sweep: 2` — instead of one whole-solution check at the
  boundary there were two;
- `execution 1: stale --no-build artifact (source_revision != artifact_revision)` — after a
  compilable edit, a run with `--no-build` reused an old artifact: source and binary were of
  different revisions.

In addition, the CHECK completeness gate sees that the contract row "boundary: the
`null`/`default` branches" is not confirmed: its boundary evidence is invalid — the validator
rejected the report (two whole-solution boundary sweeps instead of one, a stale `--no-build`
artifact), so the row has no valid evidence — in the manifest it is `open` with a reason. This is
**not** a product FAIL but a supplementary gathering in CHECK from the owning stream (the test
lens), within the budget. Only after a real boundary run with a fresh artifact
(`source_revision == artifact_revision`) and `selected_count ≥ 1` does the row close; if the budget
is exhausted, CHECK remains unresolved with the open IDs listed rather than a PASS.

The gate distinguishes "the work is done, the report is incomplete" (gather more) from "the product
is defective" (FAIL and loop-back) — and in both cases it does not let a "green by eye" through.

## 6. The cycle's outcome and ACT

The cycle does not "end silently": ACT is a mandatory gate, and it has an observable outcome. In
normal mode it leaves **two artifacts**: a finalized **cycle status file** (filled in by `pdca-executor`
from the reports — the `pdca-check` verdict, the run results, the `file:line` facts from `pdca-scout`:
Done/Verified, Next plan, Changed files) and a ready **message for the next session**. In
autonomous mode there is no second artifact — there is no user to address, the work continues in
the same session, and the status file is kept.

The order of ACT: a transferable lesson (optional, 0–2 per cycle; a no-op is normal) → updating
`AGENTS.md`/tests (`pdca-executor`) → stable rules into the project overlay → finalizing the cycle status
file (`pdca-executor`) → on a genuine terminal closure, the **gated cleanup** of this task's heavy staged
material with its machine-checkable receipt (§4.5); last in normal mode comes the "commit advice +
message" block, and after it nothing.
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
  verdict, ranking and loop-back belong to `pdca-check`; zero numbers or the author's self-report is a
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
[`opencode/pdca-dotnet/SKILL.md`](../opencode/pdca-dotnet/SKILL.md), as well as the role
templates that reference them
([`pdca-planner.md`](../opencode/pdca-dotnet/assets/agents/pdca-planner.md),
[`check.md`](../opencode/pdca-dotnet/assets/agents/pdca-check.md)) and the compact implementation of
the gate —
[`scripts/validate_inner_loop.py`](../opencode/pdca-dotnet/scripts/validate_inner_loop.py).
An overview of the whole family is in [`docs/pdca-guide.md`](pdca-guide.md).

## Sources

The article's normative claims were reconciled with the repository's current files (the
`pdca-dotnet` mirror of canonical `opencode-config` commit `063dffa`); where they disagree, `opencode/pdca-dotnet/SKILL.md` takes precedence. The
"claim → source" map:

| Claim | Source |
|---|---|
| The .NET variant is the same contract, the tools are replaceable | `opencode/pdca-dotnet/SKILL.md:11-13` |
| The variant per task (`.NET/C#` → `pdca-dotnet`) and the identity of the `pdca-coder`/`pdca-dotnet` base | `opencode/pdca-collection/SKILL.md §Роль` |
| The explicit trigger and the separation of the skills; "an edit without the cycle — directly" | `README.md:42-48`; `opencode/pdca-dotnet/SKILL.md:1-4,8-9` |
| Roles and tiers (`# tier:`, no `model:`); roles → agents and the fallbacks to built-ins | `opencode/pdca-dotnet/SKILL.md §Host requirements (roles → agents), :15-19`; `opencode/pdca-dotnet/assets/agents/*.md:5` |
| `pdca-check` may open the evidence artifacts (not product code); `pdca-scout` — read-only git only | `opencode/pdca-dotnet/SKILL.md §CHECK: audit checklist (generic), :21-26`; `opencode/pdca-dotnet/assets/agents/pdca-check.md:6-22`; `opencode/pdca-dotnet/assets/agents/pdca-scout.md:6-23` |
| `pdca-security-auditor` is a conditional gather, its report returns into the `pdca-check` aggregate | `opencode/pdca-dotnet/SKILL.md §Parallel CHECK streams (code audit + test + doc + perf + security*)` |
| The economics in practice (cost/tokens by phase and tier, no model names) | `opencode/pdca-dotnet/scripts/pdca_cost.py:4-6,28-31,93-99` |
| The mandatory `test scope` (the `unit`+`scope` envelope, fields, wide selectors, docs-only/`rebuild`, the boundary) | `opencode/pdca-dotnet/SKILL.md §DO brief: mandatory test scope` |
| The validator modes (`brief`/`report`/`journal`/`project`/`manifest`/`cleanup`/`archived`), the `--journal` reconciliation, the `0`/`2`/`1` codes, "executes nothing" | `opencode/pdca-dotnet/scripts/validate_inner_loop.py:1-30,84-102,1241-1300` |
| The scope/execution rules: wide selectors, an invented rebuild, `selected_count ≥ 1` for a finished run, shell wrappers, the kind/phase policy (integration inside DO, the planned boundary budget, a mislabelled `unit`), scope expansion, freshness, final green; structural violations before the freshness/boundary rules | `opencode/pdca-dotnet/scripts/validate_inner_loop.py:322-364,415-471,487-595,598-658,660-681,694-748` |
| The frozen manifest: its path, freezing at DO → CHECK, append-only, the fields, aggregation by reference; the schema and row coverage in the validator | `opencode/pdca-dotnet/SKILL.md §Versioned evidence contract`; `opencode/pdca-dotnet/scripts/validate_inner_loop.py:32-83,1158-1226` |
| The mechanical evidence pipeline: `generate`/`lint`, the frozen synthetic tree, atomic publication, two-way `required_rows` ↔ `rows[]` coverage in lint | `opencode/pdca-dotnet/SKILL.md §Versioned evidence contract`; `opencode/pdca-dotnet/scripts/pdca_evidence.py:1-29,397-493,577-709` |
| The versioned evidence contract: row slots, "No optional slots", the DO ledger, the re-gather budget, revision/supersession | `opencode/pdca-dotnet/SKILL.md §Documentation (owners by phase) · §Versioned evidence contract` |
| The inner-loop evidence gate: CHECK fails rather than warns; the list of conditions, incl. the omitted-execution projection | `opencode/pdca-dotnet/SKILL.md §Parallel CHECK streams (code audit + test + doc + perf + security*)` |
| The CHECK completeness gate: reconciling contract↔manifest, missing evidence = re-gather, the ban on PASS while a **binding** row is `open`, the budget | `opencode/pdca-dotnet/SKILL.md §Parallel sub-tasks in worktrees (within one cycle) · §CHECK completeness gate — mandatory evidence contract` |
| A re-entry after a terminal `incomplete`/STOP: the previous cause is a PLAN input | `opencode/pdca-dotnet/SKILL.md §PLAN owns the quality of the plan`; `opencode/pdca-collection/SKILL.md §P — собственные PLAN задач, барьер, кластеризация` |
| Quality gates: zero warnings; coverage/branches/mutations/CRAP; test-run safety | `opencode/pdca-dotnet/SKILL.md §Coder editing discipline (applying fixes) · §Test strategy (PLAN → TEST) · §Test run safety (memory + streaming) — every phase · §Parallel CHECK streams (code audit + test + doc + perf + security*)` |
| The `dotnet-*` lenses of PLAN/CHECK | `opencode/pdca-dotnet/SKILL.md §Delegation by phase · §PLAN: design checklist (generic) · §CHECK: audit checklist (generic) · §Parallel CHECK streams (code audit + test + doc + perf + security*)` |
| The ban on a 4th attempt, escalation by counter, decision routing | `opencode/pdca-dotnet/SKILL.md §State machine · §Escalation (pdca-escalate)` |
| ACT: two artifacts, the order of steps, the status file always kept; the status file path, the durable state (`N`, `r`, `n`) and the defect history | `opencode/pdca-dotnet/SKILL.md §ACT: closing the cycle, status and handoff · §Cycle status file` |
| The execution policy and the journal: unit unlimited, integration boundary-only, the planned boundary count, the explicit states, the projection | `opencode/pdca-dotnet/SKILL.md §DO brief: mandatory test scope · §Execution journal and the unit/integration policy`; `opencode/pdca-dotnet/scripts/validate_inner_loop.py:126-156,415-471,507-596,711-748,750-958` |
| The reviewer evidence pack: staged full bodies, the source-side receipt (digest/source identity/content equality), Roslyn on one snapshot, drift ⇒ invalidation | `opencode/pdca-dotnet/SKILL.md §Reviewer evidence pack (independent CHECK over full bodies)` |
| The binding/applicability disposition: append-only, `diagnostic_nonbinding`, the non-loophole boundary | `opencode/pdca-dotnet/SKILL.md §Versioned evidence contract · §CHECK completeness gate — mandatory evidence contract` |
| The ACT cleanup receipt: the gate, the deletion scope, `cleanup`/`archived`, the immutable manifest | `opencode/pdca-dotnet/SKILL.md §ACT cleanup receipt (heavy staged materials)`; `opencode/pdca-dotnet/scripts/validate_inner_loop.py:960-1140` |
| The teaching scenario: the numbers are fictional; the skill's static matrix does not prove behaviour | `opencode/pdca-dotnet/tests/scenarios.md:3-5` |

The host artifacts (`config/agents/*.md`, `config/AGENTS.md`, `config/profiles/*.jsonc`,
`config/skills/…`) live in a separate config repository and are not shipped here: the checks
consult them only when `OPENCODE_CONFIG_REPO` is set (`README.md:59-66`); the phrase-to-trigger mapping
comes from there as well.
