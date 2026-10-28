---
name: pdca-dotnet
description: ".NET/C# domain overlay for the PDCA family — adds only .NET/C# specifics to the form and overlay the base already selected: the dotnet toolchain, Roslyn-first C# symbol work, and .NET test and documentation facts. User-invoked — runs only when the user explicitly names `pdca-dotnet`."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# pdca-dotnet: the .NET/C# overlay

**A domain overlay, not a cycle, a driver or a phase state machine.** It carries only .NET/C#
additions: no form or phase state machine, no PLAN of its own, no counter, gate, acceptance rule,
approval, escalation ground or status shape. Those live once in the contract the base selected
(`../pdca/SKILL.md` §Common cycle contract, or the form that inherits or governs it).

**What it composes with.** The base carries the form, the original task and acceptance, and the
current cycle/step scope; `../pdca-coder/SKILL.md` carries the generic programming discipline. This
file adds .NET/C# facts inside them and never reclassifies the task, selects a form or overlay, or
opens a second PLAN. An already selected form and overlay set stay as they are. Invoked directly,
load the contract already in force — `../pdca/SKILL.md` for a bounded cycle,
`../pdca-incremental/SKILL.md` (which inherits it) for a campaign step,
`../pdca-collection/SKILL.md` with its local common contract for a collection — and preserve that
form; the overlay layers on the coder overlay where it applies. If no form is in force, the base
entry decides it; this overlay does not.

**Apply .NET discipline inside the unchanged task.** The original task, its global requirements and
acceptance stay as supplied, with user criteria verbatim, and the current cycle or step keeps its own
scope; the .NET specifics below apply within them, and a local result is not the whole goal. This
overlay neither widens nor narrows the task, and a user-prescribed command or method stays a
requirement.

## When it applies

- **.NET work** — C#, F#, or VB on .NET: implementation, refactoring, tests, solution/project/build
  configuration, packages, public-API surface, and the docs tied to code.
- **C# symbol work is Roslyn-first** — definitions, references, call sites, implementations,
  overloads, members, renames and impact are resolved with the `roslyn` tool, never with text search
  (§Roslyn-first for C# symbols).
- **Applied to the relevant component or step.** A mixed repository applies it to the .NET component
  or step only; other stacks stay under the coder overlay alone. Specialised knowledge loads only for
  the current step.
- **Auxiliary verification code does not reclassify a non-coding goal** (inherited from the coder
  overlay): a checker or script makes that component .NET work, not the whole campaign.

## .NET toolchain and commands

The toolchain is a property of the existing project environment. Take the build, test, format, pack
and docs commands from its manifests, CI workflow, `.editorconfig`/analyzer configuration, solution
and project files, task runner or README; a command or threshold the user prescribed is a
requirement. There is no global canonical .NET command set or exit-code table to invent here.

- **Build the affected project(s) and their dependencies, sequentially and within the host's
  resources.** A whole-solution or root build belongs outside the inner loop, and only when the
  actual scope or capacity justifies it and the phase allows it — scope and capacity, not plan
  preference. The coder's inner-loop rule is unchanged.
- **`--no-build` needs a fresh artifact.** After a compiled edit, the affected project and its
  dependencies are rebuilt, or an artifact is reused only when it is known to match the actual source
  including uncommitted changes; `HEAD` alone is not that identity. A docs-only change claims no
  build receipt and needs none. Record the actual state identity and log, not a mandatory hash,
  manifest or a `committed == tested` gate.
- **Selectors must match the configured runner.** Use the fully qualified name where that runner
  needs it; `dotnet test <project> --no-build --filter <selector>` is one form, a project runner with
  its own `-class`/`-method` selection is another. A selector matching zero cases proves nothing:
  `0 selected` is a failed run, not green. Record the selector and the test identities reported.
- **Exit status belongs to the runner, not to .NET in general.** Record the configured runner
  identity, its documented exit-code meaning and the actual status; distinguish test failure from
  infrastructure or usage outcomes using that runner.
- **Coverage** — when relevant, configuration comes from `Directory.Build.props`/
  `Directory.Packages.props`, a `.runsettings`/`coverlet.runsettings`, the CI workflow or an accepted
  baseline; `dotnet test --collect:"XPlat Code Coverage"` is one form. The project threshold is the
  lower bound; with none configured, record the measured baseline rather than inventing a number.

### Roslyn-first for C# symbols

- The `roslyn` tool answers **C# symbol questions only**; F#/VB symbol questions are not covered by
  it and use their own tooling. Actions: `structure`/`types` for discovery;
  `members`/`refs`/`callers`/`implementations` for the answer; `rename` for changes.
- It is the only C# symbol resolver: a symbol inferred from text search is not a resolved symbol.
  `rg`/`grep`/`glob`/`sed` are for non-symbol text.
- In Code Mode the call goes **inside `execute`**:
  `const r = await tools.roslyn({ action: "refs", target: "Ns.Type.Member" }); return r`. Batch
  several queries in one `execute` with `Promise.all`; the daemon keeps the solution loaded.
- Name a solution outside the session directory explicitly: `solution: "/abs/path/App.slnx"`. If the
  catalog does not show the tool, run `search({ query: "roslyn" })` first — a missing catalog entry
  is not grounds for text search.
- Apply a rename with `roslyn rename` (dry run, then `apply`) and re-check with the same tool; never
  by textual substitution.
- Text search remains valid for non-symbol text — string literals, comments, prose docs, configs,
  non-`.cs` files — and is reported as such; a symbol-bearing meaning is never inferred from such
  text. When the tool cannot load a solution or there is no `.cs`, a labelled text-search fallback is
  allowed, but its result is never called a resolved symbol.
- **Source-side gather resolves; CHECK interprets.** Resolution happens on the candidate snapshot the
  run actually produced. CHECK reads that evidence and needs neither an inaccessible solution nor a
  widened tool grant.

### .NET specialists (gather-only)

Specialists are advisory gathers, not cycle roles. The phase whose chosen method needs one requests
it on demand through the driver; the report joins the evidence `pdca-check` judges. A specialist
never issues a verdict, widens a permission or replaces a base role; tiers are role labels bound to
models only by the host profile, and a capability label never creates an agent. Use one only where
the repository actually declares it; otherwise the coder's generic path applies (`pdca-scout` for
facts, `pdca-executor` for mechanics, `pdca-check` for judgment).

| Specialist | Useful when |
|---|---|
| `dotnet-code-review-agent` | diff review raw candidates, no verdict |
| `dotnet-testing-specialist` | test strategy, coverage configuration, gaps |
| `dotnet-docs-generator`, `dotnet-api-docs`, `docfx-specialist` | prose docs, generated API docs, a DocFX site |
| `dotnet-benchmark-designer`, `dotnet-performance-analyst` | measurement design; the analyst only with ready traces, heap dumps or benchmark comparisons |
| `dotnet-async-performance-specialist` | async hot paths: `ValueTask` vs `Task`, `ConfigureAwait`, `async void`, sync-over-async, state-machine allocations, `Channel`/`IO.Pipelines`, ThreadPool starvation |
| `dotnet-csharp-concurrency-specialist` | races, deadlocks, `lock`/`SemaphoreSlim`/`Interlocked`, lock order |
| `pdca-security-auditor` | the diff touches auth, secrets, external input or crypto |

Related skills load on demand for the current step, not as a catalogue every run:
`dotnet-csharp-nullable-reference-types`, `dotnet-csharp-async-patterns`,
`analyzing-dotnet-performance`, `type-design-performance`, `dotnet-api-surface-validation`,
`dotnet-editorconfig`, `slopwatch`, `dotnet-testing-strategy`, `dotnet-test-quality`,
`dotnet-integration-testing`, `testcontainers`, `dotnet-xml-docs`.

## .NET plan deltas

For code work under the base common cycle, PLAN defines only the cycle's observable criteria; every
other plan field, the original task, the cycle/step scope and criteria ownership stay as the
governing contract sets them. A form's own PLAN protocol is not replaced here.

- **Correctness** — the requested behaviour including its error path and exit status, empty / single
  / many input, malformed or missing input, and a negative condition where the task makes one
  relevant.
- **Nullability and API surface** — only where the task's result includes them: a nullable
  annotation contract, a public-API baseline, or a compatibility guarantee the project enforces.
- **Performance** — a numeric threshold only when the task or the project's declared policy supplies
  one.
- **Documentation** — an obligation only when the task or the declared project policy mandates it.

PLAN does not choose the test strategy, the implementation decomposition, the concrete commands or
the specialist list; those belong to DO and, per criterion, to CHECK at CHECK time. A
user-prescribed command or method is carried unchanged as a requirement. .NET environment facts
(target frameworks, configured runner, solution layout, existing thresholds) may reach PLAN through
`pdca-scout` as inputs, not as a frozen procedure. If the criteria cannot be determined, the base
PLAN → ACT outcome applies; this overlay adds no extra completeness checklist, mandatory row or
pre-DO blocker.

## .NET check deltas

CHECK keeps the base procedure, its per-criterion method choice, verdict, routing and accounting, and
the coder's evidence rules; this section adds what a .NET check examines and how its evidence is
read. CHECK chooses its own methods and commands — nothing here is a pre-DO obligation.

- **Applicable work, no fixed tally.** Examine the actual change and the criteria: build and analyzers
  under the project's own `.editorconfig`/warning policy — read the effective `dotnet_diagnostic.*`
  severities when the chosen lens needs them; suppressions (`#pragma warning disable`,
  `[SuppressMessage]`, `<NoWarn>`), disabled tests (`Skip=`), empty `catch` and `Task.Delay` as raw
  candidates from the actual diff, with scope, counts and judgment left to CHECK — a marker is not an
  automatic defect; public API, naming/BCL conventions, compatibility or an API baseline and CS1591
  policy when the change touches the surface; tests against the criteria; docs where required; a
  security gather when triggered. No frozen plan manifest is created, and no universal surface lock
  is required where the project has none.
- **Diff review candidates.** Where the actual change makes them relevant: unsealed types when
  extensibility is intentional and invariants allow it; mutable or defensive-copy structs; a mutable
  `List<T>` or collection exposed from a public API; `ValueTask` misuse (multiple awaits, mixing with
  `Task`, no synchronous fast path); `Span<T>`/async combinations judged against the project's
  language version and target; missing `StringComparison` where comparison semantics matter;
  `Substring`/`Replace` chains whose cost is real; `IDisposable` lifetimes; DI scope; async and
  nullable-reference mistakes. These are candidates for CHECK's judgment, not token violations, and
  no fixed list is applied blindly.
- **Build and test evidence is executed evidence.** Record the actual commands, exit status, key
  numbers and log path; red↔green for a fix with both exit codes. An unfinished or not-started run
  carries no invented exit status or selected count, and a later retry does not erase the earlier
  failure; recording a deviation does not authorise it. Findings carry the actual CA/analyzer ID when
  one exists — never a fabricated ID; a configured analyzer is evidence only when it ran. The
  executor's run is candidate evidence; CHECK interprets it independently, and a report, `0 selected`
  or an unexecuted log is not green.
- **Tests are judged on the applicable complete scope.** Unit coverage, and integration coverage only
  where the task actually exercises EF Core or a real database, Testcontainers,
  `WebApplicationFactory`, the DI graph, serialization/snapshots or migrations. Read the threshold
  from the project configuration or baseline; no configured threshold means no invented target, and
  an irrelevant task owes no coverage or mutation measurement. Branch delta and CRAP are reported
  only where the project's policy asks for them, compared with a baseline; no universal red CRAP
  threshold is created. Mutation, when required, is the scoped Stryker.NET result on the touched
  assembly/type or a controlled-mutant demonstration; surviving mutants on the changed code are
  killed or justified against the criterion. A controlled mutant is not equivalent to a full Stryker
  score, and neither is claimed from a run that did not execute.
- **Optional `T? x = null` / `= default` on `*Options`** — a finding when it lets a wrong behaviour be
  chosen silently; the overload pair (one minimal, one requiring the value) is one fix where the task
  matches. Nullable reference annotations alone do not create distinct signatures — a pair differing
  only in annotations is a duplicate member (CS0111) — and this does not generalise to `Nullable<T>`
  value types. `CS8625` is a warning when a `null` literal reaches a non-nullable reference type
  under nullable analysis, and an error only where the project's warnings-as-errors policy makes it
  one. `required` enforces initialization, not runtime null rejection for reference types.
- **Security** — the coder's trigger and boundaries apply; the review is evidence, the decision
  CHECK's, and its absence `unverified`, never a pass.
- **Missing evidence stays `unverified`**, to be re-gathered under the base; it is not a product
  defect, not an implementation attempt, and not an infrastructure criterion. A genuine inability to
  proceed is DO → ACT per the base.

## .NET do/act deltas

DO owns the implementation, the test strategy and the command choice; ACT records the outcome. The
coder's DO/ACT rules (parallel code/test/docs streams, editing discipline, worktree sub-tasks,
security boundaries, handoff) apply unchanged.

- **Integration lane.** When the project declares a container-backed integration lane or a shared
  lease, DO runs one serialized lane at the stream / DO→CHECK boundary, with the provider connection
  environment configured and no hidden provider-skip opt-out. The skip budget is judged against the
  applicable complete scope, never a class-filtered subset; a skip is not proof, and a missing
  prerequisite is recorded honestly rather than silently skipped. Expensive integration inside DO
  outside the authorised allowance is recorded in the executing phase as a policy deviation, never
  renamed away, and it neither freezes the verification choice nor licenses repeat runs.
- **Timeouts and retries follow the governing policy.** A transport or resource timeout is failed-run
  evidence, not a new criterion or a local counter; repeated occurrences are classified by the base
  retry/escalation policy, and its limits and grounds are unchanged.
- **Test host safety (DO and CHECK).** Serialize heavyweight suites — never two in parallel or
  beside the editor/agent stack — and cap the test host, e.g. `DOTNET_GCHeapHardLimit=0x80000000
  DOTNET_gcServer=0` (2 GiB, raised only when justified) inside a wall-clock `timeout 600 …`. Stream
  the log (`2>&1 | tee <log>`, keeping `rc=${PIPESTATUS[0]}`), never `| tail`. Exit **137** or
  "Out of memory" signals a possible resource failure: stop and review the failure and the cap before
  any rerun, record the actual reason rather than asserting a diagnosis from the code, and treat the
  code alone as neither proof of an unbounded application nor proof that the original task is
  infeasible.
- **Mutation harness.** When mutation is relevant, the phase choosing it first confirms that the
  harness runs with the project and its provider configuration. Broken tooling is not a green run or
  a score. If the runner is unusable, the responsible phase may choose a controlled mutant (inject
  the change, observe the intended assertion fail) only when it demonstrates target behaviour; a
  controlled mutant is not a substitute for a full Stryker score.
- **Docs.** Prose docs are an independent, optional DO stream, as the coder says; XML `///` follows
  the finished implementation and reflects its actual signatures, never an intended one. Generated
  docs come after real implementation. Follow the project's `GenerateDocumentationFile` setting and
  effective `CS1591` warning policy; `<NoWarn>` may suppress missing-doc warnings, it does not enable
  documentation requirements the project does not have, and a disabled CS1591 is not turned into an
  unconditional zero-warning requirement. A new or changed public member's XML doc matches its real
  signature when the project requires it. Existing EN/RU pairs, CRLF and section parity, and any
  no-internal-spec-link convention apply only where the repository actually keeps paired docs and
  that convention; .NET does not by itself require bilingual docs or CRLF. Doc mismatches are fixed
  in DO/CHECK, never in ACT.
- **Status metadata.** Use the base `act.md` CYCLE RECORD, nested in a form-owned outer container
  when the form defines one; put .NET facts in the matching existing sections — the actual
  project/runner configuration, artifact pointers, coverage baseline and runs under `## DO result` /
  `## CHECK record` as the base section owns them. No separate schema, top-level field, local counter
  or mandated evidence path. The executor remains the sole status writer; the original task, phase
  reports, dialogue language and Git ledger come from the base unchanged; per-unit evidence belongs
  to the parent cycle record, not a per-unit status file.
- **Artifacts and cleanup.** If CHECK's chosen method needs the full bodies of artifacts, a staged
  copy may be used, with source identity and staged-vs-source fidelity verified by CHECK; no reviewer
  pack is mandatory each task. The source identity includes the uncommitted working state when
  present, so evidence is bound to the actual candidate rather than to `HEAD` alone, and a staged
  copy is validated against the original. A drift after the snapshot makes CHECK reconsider the
  impacted conclusion per the base, not a new counter. A missing body or a staged-vs-source mismatch
  is `unverified` or an evidence blocker, never an automatic product fail or pass. Cleanup is not a
  phase gate and nothing is deleted automatically: preserve proof and recovery per the base, limit
  any cleanup to task-owned artifacts within an explicit allowed scope, and never move or lose
  original source data. A true DO → ACT terminal outcome needs no phantom successful CHECK to permit
  cleanup.

## Optional verification helpers

Two standard-library helpers implement the inner-loop and evidence rules mechanically for projects
that choose that method. They are **optional**: a task whose criteria do not need them owes neither
run, and their absence is not a failure. Neither executes a supplied command; both validate recorded
JSON and print `FAIL:`/`ERROR:` with exit `2`/`1`.

`scripts/validate_inner_loop.py` accepts a `brief`, `report`, `project` (journal projection) or
`manifest`. A brief has `unit` and a nested `scope`:

```json
{
  "unit": "Foo.Tests",
  "scope": {
    "projects": ["tests/Foo.Tests.csproj"],
    "selectors": ["FullyQualifiedName~Foo.Tests.BarTests"],
    "files": ["src/Foo/Bar.cs"],
    "rationale": "affected unit project after the Bar change",
    "rebuild": "affected",
    "boundary": "stream"
  }
}
```

A report adds `executions`; a manifest has `task`, `status_file`, `contract_rv`, `tree`, `base_ref`,
`footprint`, `exclusions`, `required_rows` and `rows[]`. Optional metadata such as `tree_binding` and
`tree_method` may be omitted. `scripts/pdca_evidence.py` provides `generate` and `lint` for an
immutable receipt tree under `.pdca/<task>/rv<k>/`. Use these helpers only where the project already
keeps such evidence or the cycle chooses that method; they create no additional phase gate.

## Composition

The overlay composes by addition. The base the run selected — `../pdca/SKILL.md`, or the form that
inherits it (`../pdca-incremental/SKILL.md`) or governs independently
(`../pdca-collection/SKILL.md`, with its local common contract) — is authoritative for the original
task and criteria, entry and routing, roles and permissions, control modes and approval, phases,
counters and defect history, escalation, the mandatory-requirement veto, evidence sufficiency,
status, outcomes and closing.
`../pdca-coder/SKILL.md` supplies the generic programming discipline: toolchain discovery, command
forms, evidence and safety rules, security boundaries, specialist fallback, parallel DO, worktree
sub-tasks and handoff. This file supplies only the .NET/C# facts above. It creates no role, writes no
model id, changes no permission and grants no new escalation ground.

## References

The base's role-scoped routing is authoritative (`../pdca/SKILL.md` §References); this overlay adds
no role API and no local reference set. Load:

- the base contract in force — `../pdca/SKILL.md`, plus `../pdca-incremental/SKILL.md` for a campaign
  step or `../pdca-collection/SKILL.md` for a collection item, and a form's own references as that
  form states;
- `../pdca-coder/SKILL.md` — the generic programming overlay this one layers on;
- the base phase references by role: `../pdca/references/plan.md` for `pdca-planner` only, whose
  exact absolute path the driver takes from the canonical base directory and routes without reading
  or inlining it, never from this overlay; `../pdca/references/check.md`, the CHECK contract the
  driver reads in full and inlines in every `pdca-check` dispatch (CHECK cannot read the installed
  file); and `../pdca/references/act.md` read by `pdca-executor` at status-file creation and every
  status write.
