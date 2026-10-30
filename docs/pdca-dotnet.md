# `pdca-dotnet`: the .NET/C# overlay

## 1. The problem and when to pick this skill

A .NET repository gives an agent many ways to look productive: a solution-wide build that hides the
affected project, a test run whose selector matched zero cases, `--no-build` against an artifact that
predates the edit, a warning count quoted from a configuration that never ran, or a symbol renamed by
text search. Each looks like evidence and none of them is.

`pdca-dotnet` is a **domain overlay** for the PDCA family. It inherits `pdca-coder` and adds only
.NET/C# facts: the `dotnet` toolchain, Roslyn-first symbol work, test and coverage specifics, analyzer
policy, documentation conventions and .NET specialists. It is still an overlay: no form, no phase state
machine, no counter, no gate of its own.

Pick it for .NET work — C#, F#, or VB on .NET: implementation, refactoring, tests, solution/project and
build configuration, packages, public API surface, and the docs tied to code. A mixed repository applies
it only to the .NET component; other stacks stay under `pdca-coder`. Specialized knowledge loads only
for the current step.

**C# symbol work is Roslyn-first.** Definitions, references, call sites, implementations, overloads,
members, renames and impact are resolved with the `roslyn` tool, never with text search. `rg`, `grep`,
`glob` and `sed` are for non-symbol text: string literals, comments, prose docs, configs, non-`.cs`
files. A symbol inferred from text search is not a resolved symbol. F# and VB symbol questions use their
own tooling; `roslyn` covers C#.

## 2. Composition and selection

The base entry PLAN selects the form and, for .NET work, the specialized skill `pdca-dotnet`, which
layers on `pdca-coder`. Loading it does not change the form, and an already selected form and overlay
set stay as they are. Invoked directly, load the contract already in force — the base for a bounded
cycle, `pdca-incremental` for a campaign step, or `pdca-collection` with its common rules for a
collection item — and preserve that form. If no form is in force, the base entry decides; the overlay
does not.

**The task stays unchanged.** The original task, its global requirements and acceptance remain as
supplied, with user criteria verbatim. The current cycle or step keeps its own scope. The .NET specifics
apply inside them; a local result is not the whole goal. This overlay neither widens nor narrows the
task, and a user-prescribed command or method stays a requirement.

## 3. The .NET toolchain

The toolchain is a property of the existing project environment. Take the build, test, format, pack and
docs commands from its manifests, CI workflow, `.editorconfig` and analyzer configuration, solution and
project files, task runner or README. A command or threshold the user prescribed is a requirement. There
is no global canonical .NET command set or exit-code table to invent here.

- **Build the affected project(s) and their dependencies, sequentially and within the host's
  resources.** A whole-solution or root build belongs outside the inner loop, and only when the actual
  scope or capacity justifies it and the phase allows it — scope and capacity, not plan preference. The
  coder overlay's inner-loop rule is unchanged.
- **`--no-build` needs a fresh artifact.** After a compiled edit, the affected project and its
  dependencies are rebuilt, or an artifact is reused only when it is known to match the actual source
  including uncommitted changes. `HEAD` alone is not that identity. A docs-only change claims no build
  receipt and needs none. Record the actual state identity and log, not a mandatory hash, manifest or a
  `committed == tested` gate.
- **Selectors must match the configured runner.** Use the fully qualified name where that runner needs
  it; `dotnet test <project> --no-build --filter <selector>` is one form, a project runner with its own
  `-class`/`-method` selection is another. A selector matching zero cases proves nothing: `0 selected` is
  a failed run, not green. Record the selector and the test identities reported.
- **Exit status belongs to the runner, not to .NET in general.** Record the configured runner identity,
  its documented exit-code meaning and the actual status. Distinguish a test failure from infrastructure
  or usage outcomes using that runner.
- **Coverage** — when relevant, configuration comes from `Directory.Build.props` /
  `Directory.Packages.props`, a `.runsettings` / `coverlet.runsettings`, the CI workflow or an accepted
  baseline; `dotnet test --collect:"XPlat Code Coverage"` is one form. The project threshold is the lower
  bound; with none configured, record the measured baseline rather than inventing a number.

### 3.1. Roslyn-first in practice

- Actions: `structure` / `types` for discovery; `members` / `refs` / `callers` / `implementations` for
  the answer; `rename` for changes.
- In Code Mode the call goes **inside `execute`**:
  `const r = await tools.roslyn({ action: "refs", target: "Ns.Type.Member" }); return r`. Batch several
  queries in one `execute` with `Promise.all`; the daemon keeps the solution loaded.
- Name a solution outside the session directory explicitly: `solution: "/abs/path/App.slnx"`. If the
  catalog does not show the tool, run `search({ query: "roslyn" })` first — a missing catalog entry is
  not grounds for text search.
- Apply a rename with `roslyn rename` (dry run, then `apply`) and re-check with the same tool; never by
  textual substitution.
- Text search remains valid for non-symbol text and is reported as such; a symbol-bearing meaning is
  never inferred from it. When the tool cannot load a solution or there is no `.cs`, a labelled
  text-search fallback is allowed, but its result is never called a resolved symbol.
- **Source-side gather resolves; CHECK interprets.** Resolution happens on the candidate snapshot the run
  actually produced. CHECK reads that evidence and needs neither an inaccessible solution nor a widened
  tool grant.

### 3.2. .NET specialists (gather-only)

Specialists are advisory gathers, not cycle roles. The phase whose chosen method needs one requests it on
demand through the driver; the report joins the evidence `pdca-check` judges. A specialist never issues a
verdict, widens a permission or replaces a base role. Tiers are role labels bound to models only by the
host profile, and a capability label never creates an agent. Use one only where the repository actually
declares it; otherwise the coder overlay's generic path applies.

| Specialist | Useful when |
|---|---|
| `dotnet-code-review-agent` | diff review raw candidates, no verdict |
| `dotnet-testing-specialist` | test strategy, coverage configuration, gaps |
| `dotnet-docs-generator`, `dotnet-api-docs`, `docfx-specialist` | prose docs, generated API docs, a DocFX site |
| `dotnet-benchmark-designer`, `dotnet-performance-analyst` | measurement design; the analyst only with ready traces, heap dumps or benchmark comparisons |
| `dotnet-async-performance-specialist` | async hot paths: `ValueTask` vs `Task`, `ConfigureAwait`, `async void`, sync-over-async, state-machine allocations, `Channel` / `IO.Pipelines`, ThreadPool starvation |
| `dotnet-csharp-concurrency-specialist` | races, deadlocks, `lock` / `SemaphoreSlim` / `Interlocked`, lock order |
| `pdca-security-auditor` | the diff touches auth, secrets, external input or crypto |

Related skills load on demand for the current step, not as a catalogue every run:
`dotnet-csharp-nullable-reference-types`, `dotnet-csharp-async-patterns`,
`analyzing-dotnet-performance`, `type-design-performance`, `dotnet-api-surface-validation`,
`dotnet-editorconfig`, `slopwatch`, `dotnet-testing-strategy`, `dotnet-test-quality`,
`dotnet-integration-testing`, `testcontainers`, `dotnet-xml-docs`.

## 4. .NET plan deltas

For code work under the base common cycle, PLAN defines only the cycle's observable criteria; every other
plan field, the original task, the cycle/step scope and criteria ownership stay as the governing contract
sets them. A form's own PLAN protocol is not replaced here.

- **Correctness** — the requested behaviour including its error path and exit status, empty / single /
  many input, malformed or missing input, and a negative condition where the task makes one relevant.
- **Nullability and API surface** — only where the task's result includes them: a nullable annotation
  contract, a public-API baseline, or a compatibility guarantee the project enforces.
- **Performance** — a numeric threshold only when the task or the project's declared policy supplies one.
- **Documentation** — an obligation only when the task or the declared project policy mandates it.

PLAN does not choose the test strategy, the implementation decomposition, the concrete commands or the
specialist list; those belong to DO and, per criterion, to CHECK at CHECK time. A user-prescribed command
or method is carried unchanged as a requirement. .NET environment facts — target frameworks, configured
runner, solution layout, existing thresholds — may reach PLAN through `pdca-scout` as inputs, not as a
frozen procedure. If the criteria cannot be determined, the base `PLAN → ACT` outcome applies; this
overlay adds no extra completeness checklist, mandatory row or pre-DO blocker.

## 5. .NET check deltas

CHECK keeps the base procedure, its per-criterion method choice, verdict, routing and accounting, and the
coder overlay's evidence rules. This section adds what a .NET check examines and how its evidence is read.
CHECK chooses its own methods and commands; nothing here is a pre-DO obligation.

- **Applicable work, no fixed tally.** Examine the actual change and the criteria: build and analyzers
  under the project's own `.editorconfig` / warning policy — read the effective `dotnet_diagnostic.*`
  severities when the chosen lens needs them; suppressions (`#pragma warning disable`,
  `[SuppressMessage]`, `<NoWarn>`), disabled tests (`Skip=`), empty `catch` and `Task.Delay` as raw
  candidates from the actual diff, with scope, counts and judgment left to CHECK — a marker is not an
  automatic defect; public API, naming/BCL conventions, compatibility or an API baseline and the CS1591
  policy when the change touches the surface; tests against the criteria; docs where required; a security
  gather when triggered. No frozen plan manifest is created, and no universal surface lock is required
  where the project has none.
- **Diff review candidates.** Where the actual change makes them relevant: unsealed types when
  extensibility is intentional and invariants allow it; mutable or defensive-copy structs; a mutable
  `List<T>` or collection exposed from a public API; `ValueTask` misuse (multiple awaits, mixing with
  `Task`, no synchronous fast path); `Span<T>`/async combinations judged against the project's language
  version and target; missing `StringComparison` where comparison semantics matter;
  `Substring`/`Replace` chains whose cost is real; `IDisposable` lifetimes; DI scope; async and
  nullable-reference mistakes. These are candidates for CHECK's judgment, not token violations, and no
  fixed list is applied blindly.
- **Build and test evidence is executed evidence.** Record the actual commands, exit status, key numbers
  and log path; red↔green for a fix with both exit codes. An unfinished or not-started run carries no
  invented exit status or selected count, and a later retry does not erase the earlier failure; recording
  a deviation does not authorise it. Findings carry the actual CA/analyzer id when one exists — never a
  fabricated id. A configured analyzer is evidence only when it ran. The executor's run is candidate
  evidence; CHECK interprets it independently, and a report, `0 selected` or an unexecuted log is not
  green.
- **Tests are judged on the applicable complete scope.** Unit coverage, and integration coverage only
  where the task actually exercises EF Core or a real database, Testcontainers,
  `WebApplicationFactory`, the DI graph, serialization/snapshots or migrations. Read the threshold from
  the project configuration or baseline; no configured threshold means no invented target, and an
  irrelevant task owes no coverage or mutation measurement. Branch delta and CRAP are reported only where
  the project's policy asks for them, compared with a baseline; no universal red CRAP threshold is
  created. Mutation, when required, is the scoped Stryker.NET result on the touched assembly/type or a
  controlled-mutant demonstration; surviving mutants on the changed code are killed or justified against
  the criterion. A controlled mutant is not equivalent to a full Stryker score, and neither is claimed
  from a run that did not execute.
- **Optional `T? x = null` / `= default` on `*Options`** — a finding when it lets a wrong behaviour be
  chosen silently; the overload pair (one minimal, one requiring the value) is one fix where the task
  matches. Nullable reference annotations alone do not create distinct signatures — a pair differing only
  in annotations is a duplicate member (CS0111) — and this does not generalise to `Nullable<T>` value
  types. `CS8625` is a warning when a `null` literal reaches a non-nullable reference type under nullable
  analysis, and an error only where the project's warnings-as-errors policy makes it one. `required`
  enforces initialization, not runtime null rejection for reference types.
- **Security** — the coder overlay's trigger and boundaries apply; the review is evidence, the decision
  CHECK's, and its absence `unverified`, never a pass.
- **Missing evidence stays `unverified`**, to be re-gathered under the base. It is not a product defect,
  not an implementation attempt and not an infrastructure criterion. A genuine inability to proceed is
  `DO → ACT` per the base.

## 6. .NET DO and ACT deltas

DO owns the implementation, the test strategy and the command choice; ACT records the outcome. The coder
overlay's DO/ACT rules — parallel code/test/docs streams, editing discipline, worktree sub-tasks, security
boundaries and handoff — apply unchanged.

- **Integration lane.** When the project declares a container-backed integration lane or a shared lease,
  DO runs one serialized lane at the stream / DO→CHECK boundary, with the provider connection environment
  configured and no hidden provider-skip opt-out. The skip budget is judged against the applicable
  complete scope, never a class-filtered subset; a skip is not proof, and a missing prerequisite is
  recorded honestly rather than silently skipped. Expensive integration inside DO outside the authorised
  allowance is recorded in the executing phase as a policy deviation, never renamed away, and it neither
  freezes the verification choice nor licenses repeat runs.
- **Timeouts and retries follow the governing policy.** A transport or resource timeout is failed-run
  evidence, not a new criterion or a local counter. Repeated occurrences are classified by the base
  retry/escalation policy, and its limits and grounds are unchanged.
- **Test host safety (DO and CHECK).** Serialize heavyweight suites — never two in parallel or beside the
  editor/agent stack — and cap the test host, for example
  `DOTNET_GCHeapHardLimit=0x80000000 DOTNET_gcServer=0` (2 GiB, raised only when justified) inside a
  wall-clock `timeout 600 …`. Stream the log (`2>&1 | tee <log>`, keeping `rc=${PIPESTATUS[0]}`), never
  `| tail`. Exit **137** or "Out of memory" signals a possible resource failure: stop and review the
  failure and the cap before any rerun, record the actual reason rather than asserting a diagnosis from
  the code, and treat the code alone as neither proof of an unbounded application nor proof that the
  original task is infeasible.
- **Mutation harness.** When mutation is relevant, the phase choosing it first confirms that the harness
  runs with the project and its provider configuration. Broken tooling is not a green run or a score. If
  the runner is unusable, the responsible phase may choose a controlled mutant (inject the change and
  observe the intended assertion fail) only when it demonstrates target behaviour; a controlled mutant is
  not a substitute for a full Stryker score.
- **Docs.** Prose docs are an independent, optional DO stream, as the coder overlay says; XML `///`
  follows the finished implementation and reflects its actual signatures, never an intended one.
  Generated docs come after real implementation. Follow the project's `GenerateDocumentationFile`
  setting and effective `CS1591` warning policy; `<NoWarn>` may suppress missing-doc warnings, it does
  not enable documentation requirements the project does not have, and a disabled CS1591 is not turned
  into an unconditional zero-warning requirement. A new or changed public member's XML doc matches its
  real signature when the project requires it. Existing EN/RU pairs, CRLF and section parity, and any
  no-internal-spec-link convention apply only where the repository actually keeps paired docs and that
  convention; .NET does not by itself require bilingual docs or CRLF. Doc mismatches are fixed in
  DO/CHECK, never in ACT.
- **Status metadata.** Use the base `act.md` CYCLE RECORD, nested in a form-owned outer container when the
  form defines one; put .NET facts in the matching existing sections — the actual project/runner
  configuration, artifact pointers, coverage baseline and runs under `## DO result` / `## CHECK record`
  as the base section owns them. No separate schema, top-level field, local counter or mandated evidence
  path. The executor remains the sole status writer; the original task, phase reports, dialogue language
  and Git ledger come from the base unchanged; per-unit evidence belongs to the parent cycle record, not a
  per-unit status file.
- **Artifacts and cleanup.** If CHECK's chosen method needs the full bodies of artifacts, a staged copy
  may be used, with source identity and staged-vs-source fidelity verified by CHECK; no reviewer pack is
  mandatory each task. Source identity includes the uncommitted working state when present, so evidence
  is bound to the actual candidate rather than to `HEAD` alone, and a staged copy is validated against the
  original. A drift after the snapshot makes CHECK reconsider the impacted conclusion per the base, not a
  new counter. A missing body or a staged-vs-source mismatch is `unverified` or an evidence blocker,
  never an automatic product fail or pass. Cleanup is not a phase gate and nothing is deleted
  automatically: preserve proof and recovery per the base, limit any cleanup to task-owned artifacts
  within an explicit allowed scope, and never move or lose original source data. A true `DO → ACT`
  terminal outcome needs no phantom successful CHECK to permit cleanup.

## 7. Optional verification helpers

The skill ships two standard-library helpers for projects that want the inner-loop and evidence rules
checked mechanically. They are **optional**: a task whose criteria do not need them owes neither run, and
their absence is not a failure. They never execute a supplied command; they validate recorded JSON.

- `scripts/validate_inner_loop.py` — validates a `brief` (the DO test scope before dispatch), a `report`
  (scope plus executions before CHECK), an append-only `journal` projection, and the shape of an evidence
  `manifest`. It distinguishes unit from integration runs, rejects zero-target selectors, catches a
  stale `--no-build` artifact, and treats an unfinished run as unfinished.
- `scripts/pdca_evidence.py` — generates and lints an immutable, receipt-based evidence tree bound to a
  frozen synthetic tree, with a scoped manifest and `rv<k>` history.

Both files exist only in this skill's own `scripts/` (`skills/pdca-dotnet/scripts/`, installed as
`<skills-root>/pdca-dotnet/scripts/`). The base package's `scripts/` carries `pdca_cost.py` and
`plan_lint.py` only, so checking it says nothing about these two helpers. A project's `.pdca/scripts/`
is workspace, not installation: absence there is the normal pre-staging state, and the executor fills it
with byte-identical copies (recording the source path and sha256) before the first run. A missing copy
there is not a reason for a substitute gate, a waiver or a deviation record.

Neither helper is a gate the base did not ask for: use them where the project already has such evidence
or where a cycle chooses that method. The scripts' module docstrings are the CLI reference
(`brief`, `report`, `project`, `manifest`; `generate`, `lint`), and their exit codes are `0` success,
`2` validation violation, `1` usage or operational error.

## 8. Limitations and false expectations

- **“The overlay is the whole .NET contract.”** No. It adds .NET facts to the base and the coder overlay;
  the base owns every phase, criterion, counter and status rule.
- **“Roslyn is optional when the symbol is obvious.”** No. A C# symbol question is resolved with
  `roslyn`, not with text search. The fallback is labelled and is not called a resolved symbol.
- **“A solution build is the inner loop.”** No. The affected project and its dependencies run alone; a
  whole-solution build belongs outside the inner loop and only when scope and capacity justify it.
- **“Green tests prove the change.”** Only if the selector selected the intended cases, the artifact
  matched the actual source, and an independent CHECK interpreted the evidence. `0 selected` and a stale
  `--no-build` run are failures, not green.
- **“Every .NET task owes coverage and mutation.”** No. They are reported when the task or project policy
  makes them relevant, with a configured baseline; a score never replaces a mandatory criterion.
- **“The overlay may commit or push.”** No. Commits and pushes remain explicit authorisations.

## 9. Where to go next

- The base cycle: [`pdca.md`](pdca.md), [`pdca-guide.md`](pdca-guide.md),
  [`skills/pdca/SKILL.md`](../skills/pdca/SKILL.md).
- The generic programming overlay this one inherits: [`pdca-coder.md`](pdca-coder.md).
- A campaign step or collection item that uses this overlay: [`pdca-incremental.md`](pdca-incremental.md),
  [`pdca-collection.md`](pdca-collection.md).
- Host setup: [`install.md`](install.md).

## Sources

| Claim | Source |
|---|---|
| The overlay is not a cycle and composes with the base and the coder overlay | `skills/pdca-dotnet/SKILL.md:11-31`; §Composition |
| When it applies, including Roslyn-first | `skills/pdca-dotnet/SKILL.md §When it applies` |
| Toolchain facts, builds, `--no-build`, selectors and coverage | `skills/pdca-dotnet/SKILL.md §.NET toolchain and commands` |
| Roslyn-first details and the source-side gather | `skills/pdca-dotnet/SKILL.md §Roslyn-first for C# symbols` |
| .NET specialists and related skills | `skills/pdca-dotnet/SKILL.md §.NET specialists (gather-only)` |
| .NET plan deltas | `skills/pdca-dotnet/SKILL.md §.NET plan deltas` |
| .NET check deltas and missing evidence | `skills/pdca-dotnet/SKILL.md §.NET check deltas` |
| .NET DO/ACT deltas, host safety, docs and artifacts | `skills/pdca-dotnet/SKILL.md §.NET do/act deltas` |
| Optional helper scripts | `skills/pdca-dotnet/scripts/validate_inner_loop.py`; `skills/pdca-dotnet/scripts/pdca_evidence.py` |
