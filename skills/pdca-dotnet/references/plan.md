# PLAN deltas for .NET: evidence contract, inner loop, test strategy

Reference for the PLAN phase of the .NET overlay. The base plan fields, the command contract,
vacuous/expected-negative runs, recorded exceptions, re-anchoring, proportional planning and the
one-evidence-location binding stay in `../../pdca/references/plan.md` and `../../pdca/SKILL.md`; the
code design checklist, the mandatory decisions (unit mode, performance, reconnaissance), the generic
test strategy and the documentation plan stay in `../../pdca-coder/references/plan.md`. This file
holds only the .NET additions: the versioned evidence contract, the machine-checked command
projection, the inner-loop gate, the .NET test-strategy and documentation deltas, and the reviewer
evidence pack.

## PLAN lenses and .NET skills

PLAN runs in the coder's two beats — gather (cheap) over the **area of change**, not the whole
repository, via `pdca-scout` + the selected lenses with `file:line` findings and no code; decide via
`pdca-planner`, which reads only the summary. The .NET binding of the six lenses:

- **Design (SOLID/DRY)** — `dotnet-solid-principles`, `dotnet-architect`: god classes, fat
  interfaces, throwing overrides, leaky contracts, `IFoo`/`Foo` without a second consumer, duplicated
  knowledge, switch-on-type.
- **Data/type design** — `type-design-performance`: unsealed library types, mutable/defensive-copy
  structs, `List<T>` from a public API, `ValueTask` misuse, `Span<T>` in async, per-call
  `new Dictionary/List`.
- **Correctness/anti-pattern scan** — `analyzing-dotnet-performance`, `dotnet-csharp-code-smells`:
  strings (no `StringComparison`, `.Substring`, `.Replace` chains), collections/LINQ on a hot path,
  regex, I/O/serialization, async.
- **Test strategy** — `dotnet-testing-strategy` + `dotnet-testing-specialist` (§.NET test strategy
  deltas).
- **Performance measurement** — `dotnet-benchmarkdotnet`/`dotnet-benchmark-designer`; the decision and
  its argument are the coder's mandatory one.
- **Reconnaissance** — `pdca-executor` (harness, commands, numbers) + `pdca-scout` (facts, versions,
  docs); the decision and its argument are the coder's mandatory one.

**Structural sealedness:** count sealed vs unsealed types and report the ratio (Verify-the-Inverse),
not a verdict on one type.

## Versioned evidence contract

**REQUIRED at PLAN:** pin a versioned evidence contract in the cycle status file before DO. This
subsection is the single global definition; agent templates and project overlays must reference it,
not define competing contracts. The status file holds the authoritative contract for the cycle.

Every contract row must contain:

- A stable requirement ID and a stable row ID.
- The required check or scenario.
- Expected evidence kinds and their sources.
- The exact command or invocation, required exit-code or invocation-result evidence, and log
  requirements.
- Expected artifacts, including their locations, or an explicitly justified N/A.
- The owner stream responsible for producing the evidence.
- An observable applicability predicate; unconditional obligations are always applicable.
- The contract revision `rv`.

**No optional slots:** PLAN may choose the layout, but must not omit slots or weaken required
checks. Planned artifact locations are expectations, not evidence. Do not fabricate future test
symbols or `file:line`; use verified existing references or explicitly planned sources. PLAN must also
pin a finite CHECK re-gather budget and its owner, and the frozen evidence manifest path, in the
status file. Every plan carries a **`PLAN-LINT`** row: the `plan_lint.py check` receipt (path + exit
`0`) proving the frozen commands passed the plan command contract before gate 1 (§Machine projection).

### Default evidence dir and the attempt child

**Default evidence dir (defined by the skill, not by overlays or agent settings):**
`.pdca/<task>/rv<k>/` — `<task>` = `D<issue>` or a kebab-slug, `<k>` = contract revision `rv`; this is
the evidence **root**. Each attempt's frozen manifest, logs and per-row artifacts live in a **fresh
child**, `.pdca/<task>/rv<k>/attempts/c<N>-r<r>-n<n>/` (e.g. `c1-r1-n1`, `c1-r1-n2`; `c<N>` is the
cycle, so the next cycle never reuses the previous child at the same `rv`/`r`/`n`). The status file
records the attempt identity `task/N/r/n`, the frozen snapshot hash and the authoritative
`manifest.json` path **before DO→CHECK**; a CHECK→DO return under the same contract starts the next
`n` in a new child, the same CHECK uses its child append-only, and prior manifests are retained. `rv`
changes only with the criteria/contract, not with an implementation fix under the same criteria. The
`.pdca/` root is fixed (§Workspace and durable status in the base `pdca` contract) — the plan chooses
`<task>` and `rv`, an overlay never relocates the root. The check role's scoped `read` grants it
generically (`.pdca/**`), so the concrete path is defined **only here** — never repeated in an overlay
or an agent's settings.

### DO ledger

Record actual evidence against each row ID and `rv`: verified test symbols or `file:line`, results,
executed commands or invocations, exit codes or invocation results, and log/artifact paths. Record
failed, not-run, missing, and blocked evidence explicitly. N/A requires an observed applicability
predicate; it must never waive an unconditional obligation.

### Frozen evidence manifest

**One per task — the single object CHECK reconciles.** DO writes one machine-readable manifest at the
path PLAN pins in the status file (the default path is the `generate` output of §Mechanical evidence
pipeline), and CHECK reads it first. It is **frozen at the DO→CHECK boundary** (after the boundary
sweep), bound to the frozen tree revision (`commit`/sha) and the contract revision `rv` under CHECK,
and carries an immutable **evidence generation** keyed by `task/N/r/n` + the frozen tree identity (+
`rv`). The generation is an evidence-snapshot identity, **not** the criterion revision `rv`: `rv`
belongs to the contract/criteria, the generation distinguishes attempts of the same contract. During
CHECK the **same generation** is **append-only**: re-gather adds evidence or an `open` reason to
existing rows; it never rewrites a row or starts a second manifest. **CHECK never writes**: it returns
the disposition decision and the exact append instruction; `pdca-executor` writes it into the same
canonical manifest, and CHECK reconciles the durable result. A contract revision (`rv` → `rv+1`)
starts a new manifest generation; the superseded one is kept. A **CHECK → DO** return under an
**unchanged contract** also starts a **new immutable generation** for the new attempt/snapshot in a
**fresh attempt child directory**, retaining the prior one — without a fake replan or reset of `r`/`n`.

Minimum content — each entry maps one contract row to its evidence **by reference, not by copy**. The
mechanical gate is the **union of two helpers with different responsibilities**, so the minimum is
their exact joint requirement; neither helper is weakened and neither substitutes for the other:

- required by `validate_inner_loop.py manifest`: `task`, `status_file`, `tree` (non-empty strings),
  `contract_rv` (integer ≥ 1), `required_rows`, and the `rows[]` shape plus two-way `required_rows` ↔
  `rows[]` coverage;
- required by `pdca_evidence.py lint`: `tree` (40-hex, resolvable by `git cat-file -t`, equal to the
  recomputed frozen tree), `base_ref`, `footprint`, `exclusions`, and the same two-way coverage (plus
  the receipt/generation checks of §Mechanical evidence pipeline).

A self-contained minimum therefore carries: `task`, `status_file`, `contract_rv`, `tree`, `base_ref`,
`footprint`, `exclusions`, `required_rows`, `rows[]` — where:

- `tree` is the frozen synthetic tree id, never a claim that it equals `HEAD^{tree}`;
- `base_ref`, `footprint`, `exclusions` are the tree's input binding: a resolvable ref/commit, a
  non-empty list of repo-relative footprint paths (none covered by an exclusion), and the exclusion
  list (e.g. `.pdca/**`). Without them the tree cannot be recomputed, so the lint fails;
- `required_rows` are the mandatory row IDs of the pinned contract; `rows[]` has one per required
  row: `id`, `status` (`met` | `open` | `na`), and for `met` an `evidence[]` of
  `{kind, path, command?, exit?, value?}` — `path` is **repo-relative and contained in the
  repository** (no absolute path, no `..` traversal, no symlink escape: the helper rejects all
  three) — plus exit code, key number, test symbol; for `open` a `reason`; for `na` an observed
  `predicate`.

**Optional metadata, not gate requirements:** `tree_binding` — when present it must equal `tree` (the
`generate` output always writes it and every receipt carries the same pair), and `tree_method` — the
helper's frozen-tree recipe verbatim, so reconciliation repeats the recorded recipe instead of
inventing one. Both may be omitted from a hand-written minimum; neither helper rejects their absence.
A hand-written minimum is accepted only when its `tree` equals the tree recomputed from its
`base_ref` + `footprint` + `exclusions` (the `generate` output satisfies this by construction). Every
`required_rows` entry must appear; a row without a resolving reference is `open`, never silently
dropped. Logs stay references — the manifest is a thin index, not a copy of artifacts.

**No PASS while any BINDING/APPLICABLE `required_rows` entry is `open`;** CHECK resolves a row by
opening its `path`, not by re-deriving it from the brief, and records the applicability disposition of
a non-binding audit row (below). The manifest passes the mechanical gate only when **both** tracked
helpers exit `0`:

- `.pdca/scripts/validate_inner_loop.py manifest <manifest.json>` — row/evidence shape plus two-way
  `required_rows` ↔ `rows[]` coverage;
- `.pdca/scripts/pdca_evidence.py lint --repo <root> --manifest <manifest.json>` — frozen-tree binding
  (§Mechanical evidence pipeline below).

Neither substitutes for the other; a nonzero exit is a failed evidence gate, never a warning.

### Mechanical evidence pipeline (`.pdca/scripts/pdca_evidence.py`, stdlib only)

The plan may opt into the atomic generator; DO then materialises the pinned contract as a JSON object
that mirrors the status file (e.g. `<evidence-dir>/inputs/contract.json`) and runs:

- `generate --repo <root> --contract <contract.json> --output <evidence-dir>` — resolves the frozen
  synthetic tree from `base_ref` + `footprint` (paths under `exclusions` are overlaid out, not
  removed from the base tree), writes one immutable receipt per required row under
  `generations/<digest>/results/<row-id>.json`, and replaces `<evidence-dir>/manifest.json` last and
  atomically. **Operational `--output` recipe:** the evidence root stays `.pdca/<task>/rv<k>/`, and
  every attempt passes its own fresh child `<root>/attempts/c<N>-r<r>-n<n>/` as `<evidence-dir>`; the
  status file pins that child's `manifest.json` as the authoritative path before DO→CHECK and records
  `task/N/r/n` plus the snapshot hash. The helper preflights any existing manifest in `<evidence-dir>`
  and refuses a stale one (`preflight: existing evidence is stale`), so the next attempt **must** use
  a fresh child instead of overwriting the old one; prior manifests are retained. An implementation
  fix under the same required rows/criteria keeps `contract_rv` — a new attempt snapshot is not a
  contract revision. A held lock refuses a concurrent writer — it never silently repairs, never
  invents an execution and never turns `open` into `met`. DO runs it at the DO→CHECK boundary.
- `lint --repo <root> --manifest <manifest.json> [--scope-root <dir>]` — recomputes the frozen tree
  with the same recipe and fails (`exit 2`) unless `manifest.tree == recomputed == every receipt's
  tree == every receipt's tree_binding`, every referenced path resolves under the repo, row IDs are
  unique, and `required_rows` ↔ `rows[]` cover each other exactly. It scans exactly one selected
  revision directory (default: the manifest's own); unrelated historical revisions are untouched.

Contract fields: `task`, `issue`, `status_file`, `path`, `base_ref`, `collection_baseline_ref`,
`footprint`, `exclusions`, `contract_rv`, `supersedes`, `required_rows`, `rows[]` — the same row schema
as the manifest (`id`, `status`, `requirements`, `predicate`, and by status `evidence` / `reason`;
`open` rows are valid input). Exit codes: `0` ok, `2` violation (the diagnostic names the path +
field), `1` usage/operational error. The CLI only mechanises provenance: the frozen manifest stays the
single object CHECK reconciles, and re-gathering stays append-only. **Helper compatibility:** the tree
binding, receipt schema and `generations/<digest>` layout stay as implemented; the evidence generation
is an identity recorded in the manifest/status, not a new helper format, and no helper change is made
unless a test proves it necessary.

### Binding/applicability disposition (append-only)

The frozen manifest is never rewritten and no row is ever deleted: a pre-existing, self-imposed extra
*audit* row stays in place with its original `status`/text and is never quietly turned into `met`.
CHECK returns an explicit applicability disposition instruction; `pdca-executor` appends it inside the
same canonical manifest — a stable row ID, the classification `diagnostic_nonbinding`, and the
concrete reason/basis in the agreed scope or the priority global rule (the plan fixes the exact field
names; no second competing manifest). CHECK then reconciles the durable row. A raw row may thus stay
`open` while it is **excluded from the set of binding acceptance blockers**: the final receipt shows
binding unmet rows and audit notes separately, so a PASS on the genuine gates does not contradict a
retained historical audit `open`.

This path is **not a loophole**. It covers only unsupported *extra* audit demands that do not follow
from the agreed goal — a recursive historical inventory, or a retrospective/unrequested
execution-time `committed == tested`. A failing or missing required test, unverified direct evidence,
a source-copy mismatch, or a real functional/security variant stays on the normal fail/re-gather/STOP
route, and a finite audit goal the user explicitly agreed as a **separate** audit task stays
**binding**. The scope basis and reason are checked by the role decision, not merely asserted by the
author; an extra gate does not acquire normative force from the word `frozen`. The applicability
allowance is not a tuning knob: an absent audit-only row consumes no gather/replan allowance, while a
missing *mandatory* direct result still goes through bounded re-gather.

### Contract revision

A newly discovered required variant must return CHECK → PLAN with a justification. PLAN explicitly
supersedes the previous contract revision, retains existing row IDs, adds IDs for new variants, and
preserves all still-required acceptance obligations. Completing evidence does not itself revise the
contract. Contract supersession does not supersede DO work or discard unfinished acceptance criteria;
existing plan-revision and attempt rules remain unchanged.

## Machine projection: `commands.json` + `plan_lint.py`

The base plan command contract (§Plan command contract in `../../pdca/references/plan.md`) applies
unchanged: selector resolves, argv survives the harness, phase and scope are legal, the expected
outcome is declared. The prose command block is not machine-checkable, so PLAN also emits a
**projection** at `<evidence-dir>/inputs/commands.json` (same attempt child as the contract): `task`,
`plan_r`, optional `checkout`, `evidence_root`, `host_budget`, `integration_boundary_runs`, optional
`units`, and one object per command — `id`, `phase`, `kind`, `argv[]`, `cwd`, `env`, `expected`,
`expected_identity`, `min_selected`, `log`, `timeout_s`, `covers`, and for mutation a `harness_probe`
or a declared `fallback`.

`pdca-executor` stages `plan_lint.py` into `.pdca/scripts/` (byte-identical, §Helper staging in the
base plan reference) and runs it **before gate 1** and **again on DO entry** after re-anchoring:

- `python3 .pdca/scripts/plan_lint.py check --repo <checkout> --commands <projection> --receipt
  <evidence-dir>/plan-lint.json` — static: schema, argv shape (array, no shell
  wrapper/operator/placeholder), phase and scope legality, solution-build scope against
  `host_budget`, selector resolution against the project sources (fully-qualified `-class`/`-method`;
  an exact `FullyQualifiedName=` without a namespace is rejected), expected outcome, evidence binding
  to the linted checkout, unit coverage;
- `python3 .pdca/scripts/plan_lint.py probe --repo <checkout> --commands <projection>` —
  additionally runs each `harness_probe` (allow-list: `dotnet`, `git`, `python3`; timeout-bounded;
  never the planned command).

Exit codes are `0` ok, `2` violation, `1` usage/operational — the same convention as
`pdca_evidence.py`. A nonzero `check` **is** a gate-1 failure; the receipt is the evidence row
`PLAN-LINT` (path + exit). The lint proves the command is well-formed and resolvable; it does not
prove the row passes — that stays with CHECK. Selector resolution reads project sources, not a built
assembly, so a source-level false negative is possible and is recorded as a warning, not a pass.

## Inner-loop gate: `test scope`, journal, report

### Mandatory `test scope` envelope

Every implementation brief to `pdca-executor` **MUST** carry a mandatory structured `test scope` (with
a rationale); **without it the driver must NOT dispatch the brief** — it returns to `pdca-planner` to
complete the scope. `pdca-executor` runs `.pdca/scripts/validate_inner_loop.py brief <brief.json>`
**before any edit** (the helper is staged into `.pdca/scripts/` first, §Helper staging in the base
plan reference); a nonzero exit is **fail-closed** → return to the driver (do not start editing).

Required fields — the **brief is a wrapper**: the unit id at the top level, the scope nested under
`scope`. (A bare scope object is rejected with `missing required key: unit`.)

```json
{
  "unit": "<DO unit id, e.g. D1>",
  "scope": {
    "projects": ["<affected test project path>.csproj"],
    "selectors": ["FullyQualifiedName~<TestClass>.<Test>"],
    "files": ["<changed file path>.cs"],
    "rebuild": "affected",
    "boundary": "<the single DO → CHECK comprehensive sweep point>",
    "rationale": "<why this subset covers the changed behavior>",
    "integration_projects": ["<test project that really runs integration tests>"],
    "integration_boundary_runs": 1
  }
}
```

- `unit` — the **string id of the DO unit** (`D1`, `T2`, …), not a container: projects/selectors/files
  live inside `scope`.
- `projects` — the affected test project(s); `selectors` — nonempty, never a whole-project/solution or
  all-selecting filter.
- `files` — the planned changed files; the key is **mandatory**, the list **may be empty**
  (`"files": []`). With `rebuild: "affected"` it must contain at least one `.cs`/`.fs`/`.vb` file.
- `rebuild` — `affected` on a compiled-input change; `none` for a docs-only change (no fictitious
  rebuild). A docs-only scope (no `.cs`/`.fs`/`.vb` file) must **not** claim an `affected` rebuild; a
  fictitious rebuild fails the gate.
- `boundary` — the one comprehensive sweep point at the **DO → CHECK boundary**.
- `integration_projects` (optional) — the test projects that **actually execute integration tests**;
  `integration_boundary_runs` (optional int ≥ 1) — the number of **actual** integration runs PLAN
  approves at the boundary. Both are how PLAN fixes the integration scope up front; the gate invents
  no universal numeric cap of its own (§Execution journal in `references/act.md`).

Before CHECK, the full evidence (scope + `executions` with exact argument arrays, filters, phase,
revisions, exit codes) is validated with `.pdca/scripts/validate_inner_loop.py report
<evidence.json>`; CHECK consumes that exit code and fails closed when it is missing or nonzero. When
the raw journal exists, the report is reconciled against it with `--journal`
(`report <report.json> --journal <journal.json>`), and generated mechanically from it with
`project <journal.json>`.

### Test run safety (memory + streaming) — every phase

Any test invocation (`dotnet test`/`dotnet run` on a test project) in DO or CHECK; put these in the
`pdca-executor`/`pdca-check` brief; CHECK rejects a violating report:

- **Cap the test-host heap** so a runaway recursion fails fast instead of OOM-killing the machine:
  `DOTNET_GCHeapHardLimit=0x80000000 DOTNET_gcServer=0` (2 GiB — raise only when justified) and wrap
  in a wall-clock `timeout 600 …`. Exit **137**/"Out of memory" ⇒ the test is unbounded: stop, record
  the test name and SQL, do not re-run without the cap.
- **Serialize heavyweight suites:** never two test projects in parallel (e.g. `core` + `sqlite`), and
  never beside the editor/agent stack (agent workers, VS Code, LSPs); run the affected project alone.
  A DB/provider suite runs at the stream boundary, not per edit.
- **Capture three artifacts, never a merged log:** `cmd > <stem>.out 2> <stem>.err; printf '%s\n'
  $? > <stem>.rc` (base §Plan command contract). A merged `2>&1` stream erases what a negative
  criterion claims, and an empty log without `.rc` cannot be told apart from a run that never
  started. Never `| tail` (buffers to EOF and looks hung); `| tee` is for visibility only. Always
  return the three paths **and** the exit code.

A run that selects zero targets is a failed run whatever its exit status (base vacuous-run rule; in
code: zero discovered tests, zero executed cases), and every decisive run names its minimum selected
count.

### Inner-loop coverage (summary; the norm is in the coder overlay)

Build the affected project once when compilable inputs change, then run it —
`dotnet test <project> --no-build --filter <selector>` **or** an unfiltered run of an affected
**unit** project (a `rebuild: none` docs-only scope skips the build). Unit runs are unlimited, and the
presence of `--filter` is **not** a unit-vs-integration criterion. The whole solution in the inner
loop, or an integration run inside DO, is a red flag and the report is rejected. Widening to a shared
contract/dependency is allowed only if the scope is amended **and validated BEFORE running**, with the
reason recorded.

## .NET test strategy deltas

The coder test strategy, variant matrix, decisive-evidence rule and anti-patterns apply unchanged.
.NET binding:

- **Unit** — pure logic, branching, boundaries; one test per behavior, name = assertion.
- **Integration** — what a unit test cannot see: DB/EF Core (`Testcontainers`), HTTP/endpoints
  (`WebApplicationFactory`), DI graph, serialization/snapshot, migrations; tooling
  `dotnet-integration-testing` / `testcontainers` / `snapshot-testing`.
- **Not covered** — trivial proxies and logic-free `record` DTOs; recorded as `deferred` with a
  trigger.
- **Coverage comes from the project, mandatory.** Find the project's coverage config/threshold (gather
  via `pdca-scout`/`dotnet-testing-specialist`): `Directory.Build.props`/`Directory.Packages.props`,
  `.runsettings`, `coverlet.runsettings`, `dotnet test --collect:"XPlat Code Coverage"`, the CI
  workflow, a baseline artifact. **The project threshold is the lower bound** — do not lower it; new
  code comes with tests. No config → record the baseline explicitly; do not invent a threshold.
- **Branch, not only line; mutation, not only green.** A green line % does not prove new branches are
  exercised: report the **branch** delta and run **mutation testing** (Stryker.NET, scoped to the
  touched assembly/type) — surviving mutants on new code are killed or explicitly justified. No
  tooling → say so and list the untested branches; never imply coverage you did not measure.
- **CRAP / complexity** — no new 🔴 CRAP hotspot on the changed area.
- **Per-unit test scope is part of the strategy.** For **every unit** the plan names its **affected
  subset** — the test project(s) and the exact, non-broad filtered selector(s) — the **boundary sweep
  point** (the single DO → CHECK comprehensive run), and which of those projects actually execute
  **integration** tests (the boundary-only runs). This mapping feeds the DO brief's mandatory `test
  scope` envelope (§Inner-loop gate); a unit whose affected subset or boundary point is unnamed fails
  gate 1. Unlimited **unit** runs inside DO are normal and must not be constrained with artificial
  namespace filters; an **integration** run inside DO is a policy deviation (`references/act.md`).
- **Gather** (`dotnet-testing-specialist`): existing tests of the area (`file:line`), gaps, regression
  risk, config and current coverage. Decision (case list, unit/integration, name, what it checks) by
  `pdca-planner`, written by `pdca-executor`. Skills: `dotnet-testing-strategy`, `crap-analysis`,
  `dotnet-test-quality`, `dotnet-xunit` (+ `dotnet-tunit-test` if present). Output: case list + split +
  current/target coverage; CHECK verifies against it.

## .NET documentation owners

The coder documentation contract applies (prose docs derived from the plan, written in parallel;
generated/API docs only when mandated). .NET binding — **prose docs and XML-doc are separate artifacts
with different timing**:

- **Prose** (README/guides/DocFX): **PLAN** gathers via `pdca-scout` + the skill
  `dotnet-documentation-strategy` (which docs and format); "no contract/behavior change" → record "we
  do not touch the docs". **DO** — the third parallel stream, from the plan/contract, not from the
  code; `pdca-executor` (+ `docfx-specialist`). **CHECK** — doc lens: created and matching the
  implementation.
- **XML-doc** (`///`): from the **finished code**; mandatory only if the project enables it
  (`GenerateDocumentationFile` / CS1591 via `TreatWarningsAsErrors` or `<NoWarn>`): **PLAN** —
  `pdca-scout` reports the setting (required ⇒ mandatory, else only on user request); **DO** — written
  after the code stream (`pdca-executor`); **CHECK** — generated on every new/changed public member
  and matching signatures when mandatory, else only if requested.
- **ACT** — only the final stable-rules **AGENTS.md** (`pdca-executor`); docs are finished in
  DO/CHECK, not edited in ACT.
- Rule: a public contract/behavior change without updated prose docs does not close the cycle; missing
  CS1591 blocks closure only when the project mandates XML-doc. On-demand skills: `dotnet-xml-docs`,
  `dotnet-github-docs`, `dotnet-mermaid-diagrams`.

## Reviewer evidence pack (independent CHECK over full bodies)

An independent CHECK reads only inside its allowed roots; evidence that lives only in a diffstat, a
paraphrase, a link to an unreadable original, or isolated quoted lines is **not** reviewable evidence.
At the DO → CHECK boundary the executor therefore **stages the full bodies** of the changed files a
reviewer needs into this task's `rv<k>` evidence dir (default `.pdca/<task>/rv<k>/`; the exact
filenames/layout are the plan's). Staging is a **copy, not a move** — the originals are preserved.

- **`pdca-executor` performs the staging write**; a separate, cheap **read-only source-side gather
  (`pdca-scout`)** independently verifies the staged pack and the technical source check **before**
  medium CHECK (it never copies or writes): per staged file it records the original path, the staged
  copy path, the content digest, the **source identity** of the verified revision/working tree, and
  the **content equality** of copy vs source. The receipt carries the gather's **actual finding**, not
  the author's declaration. A single `HEAD` is insufficient when the working tree has uncommitted
  edits, so the source identity names the state that was actually reviewed.
- **Roslyn resolution runs in that source-side gather**, on the same frozen snapshot, and the pack
  carries the result with the same source identity. Medium CHECK evaluates the pack and does **not**
  run Roslyn against an inaccessible whole solution. Source-check data and C# resolution are bound to
  **one** snapshot: one revision may not be verified while the receipt names another.
- **Drift ⇒ invalidation, not automatically a new `rv`.** From the frozen capture until CHECK, no
  task-relevant footprint may drift without invalidation; an **unexpected** drift invalidates the
  previous verdict and requires a new attempt snapshot (fresh child, new `n`). If the required rows
  and criteria are unchanged, `contract_rv` stays; only a CHECK → PLAN that actually revises the
  criteria/issues requirements bumps `rv`. A **planned CHECK → DO** new attempt under the same
  contract is likewise a new snapshot, not drift and not `rv+1`. This is not a global ban on unrelated
  parallel work.
- The pack carries the confirmations of the changed **registry claims**; the whole repository need not
  be mirrored. Before CHECK, availability of every required reviewer material **inside the allowed
  roots** and staged-vs-source equality are checked; the original path stays metadata, not the only
  readable route.
- Author and independent certifier are **different roles**: CHECK itself reconciles each changed
  registry claim against the supplied confirmation and records a **row-level result/reason**. CHECK
  reads row-level evidence addressably and need not load every staged file into context; its read/MCP
  rights are **not** widened, and Roslyn-first for C# semantics stays in the source-side gather.
- A missing body, a staged-vs-source mismatch, an incomplete justification, or the absence of an
  independent verdict is **evidence open/blocked** — not product FAIL and not PASS.

This is **source-copy fidelity**: it reuses the existing source binding and digests and introduces no
second competing evidence contract. It is **not** a proof of execution-time `committed == tested` and
**not** the atomic evidence generator (`.pdca/scripts/pdca_evidence.py`; §Mechanical evidence
pipeline).

## Evidence helper discipline

- The runner summary is the source of truth for counts (total/selected/passed/failed/skipped); parse it
  into the journal, never infer success from an exit code alone.
- Capture the expanded argv and the real exit code per run; a log without them is not evidence.
- The manifest's `tree` is the frozen synthetic tree from `base_ref` + `footprint` + `exclusions`;
  `lint --repo <checkout>` names the checkout the checks actually ran in, and evidence is mirrored at
  the same repo-relative path when a secondary checkout is used (base §One evidence location binding).
