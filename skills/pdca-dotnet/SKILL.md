---
name: pdca-dotnet
description: ".NET/C# domain overlay for the PDCA family — adds only .NET/C# specifics to the form and overlay the base already selected: the dotnet toolchain, task- and policy-aware C# symbol guidance, and .NET test and documentation facts. The base PLAN selects it whenever the task's code component is .NET/C#, and it inherits `pdca-coder`, so plain `pdca-coder` is never the right choice for .NET work. Hidden from the host's own auto-selection (`metadata.opencode/autoinvoke: false`): that keeps it out of the skill picker, it does not forbid PLAN from choosing it."
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

Before applying work on direct invocation, explicitly load `pdca-coder` by exact skill ID;
`pdca-dotnet`'s inheritance of it does not prove its contract is loaded. Load base `pdca` by exact
skill ID too, then follow its §Preflight — required skill contracts for the current form and overlay
closure. If `pdca` cannot be loaded, its preflight owner is unavailable: stop and report the exact
ID and host loader's failure; do not wait for that rule, reconstruct it or start work.

**Apply .NET discipline inside the unchanged task.** The original task, its global requirements and
acceptance stay as supplied, with user criteria verbatim, and the current cycle or step keeps its own
scope; the .NET specifics below apply within them, and a local result is not the whole goal. This
overlay neither widens nor narrows the task, and a user-prescribed command or method stays a
requirement.

## When it applies

- **.NET work** — C#, F#, or VB on .NET: implementation, refactoring, tests, solution/project/build
  configuration, packages, public-API surface, and the docs tied to code.
- **C# symbol work follows the task and governing policy.** When a criterion needs exact symbol
  identity, references or rename impact, use an available, permitted, project- or host-supported
  semantic method. Roslyn is one possible method, not a dependency or the sole resolver imposed by
  this overlay. Higher-priority host/project policies and permissions take precedence; never bypass a
  denial. This guidance does not make a language tool a prerequisite for unrelated .NET work.
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

- **Build in dependency order.** Build each affected project after its required dependencies.
  Treat projects as parallel candidates only after their dependency relation is known; build
  independent affected projects concurrently only when outputs are isolated and known shared-host/
  resource headroom is sufficient. Never overlap builds that write shared output paths. If output
  isolation or headroom is unknown, serialize only that project group, not all work globally. A
  whole-solution or root build remains outside the inner loop and only when scope/capacity justify it
  and the phase allows it. The coder's affected-project inner-loop rule is unchanged.
- **`--no-build` needs a matching artifact.** After a compiled input changes, rebuild the affected
  project and its dependencies, or reuse an artifact only when the product and test compiled inputs
  and effective build configuration it consumed are known equivalent. `HEAD` alone neither
  establishes nor defeats that equivalence; follow the base CHECK identity rule and record the
  available identity, not a mandatory hash, manifest or `committed == tested` gate. Once a matching
  build is verified, use it with `--no-build`; launching collection or CHECK is not by itself a reason
  to recompile. A docs-only change claims no build receipt and needs none.
- **Build the original project.** When CHECK needs a build, run the project-configured command on the
  original candidate in its checkout. Persist the build evidence, not a buildable project copy, under
  `evidence_root`; leave `.csproj` and other product files in the checkout.
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

### Semantic tooling for C# symbols

- **Choose by task and policy.** When exact symbol identity, reference completeness or rename impact
  matters, use an available, permitted, project- or host-supported semantic method where it can
  establish that fact. Roslyn is one possible method, not an overlay dependency or the sole resolver
  allowed by this skill. This C# guidance does not create a tooling requirement for F#/VB or
  non-symbol .NET work.
- **Honor tool policy.** Higher-priority host/project requirements and permissions govern tool choice.
  A permission denial is a policy constraint, not an availability signal; do not bypass it or treat it
  as an automatic install request. An absent tool does not block unrelated .NET work or require a
  substitute.
- **Bound text evidence.** Where policy allows, text inspection can find candidate occurrences.
  Text matches alone do not establish resolved bindings, complete references or rename impact; label
  them as candidates and state uncertainty.
- **Keep the criterion precise.** If an acceptance criterion requires a symbol fact and no permitted,
  available method establishes it, report that criterion as unverified under the base contract. The
  missing method does not block unrelated criteria or all .NET work.
- **Bind evidence to the candidate.** When a tool-based gather is used, it applies to the candidate
  snapshot the run actually produced. CHECK interprets that evidence and need not rerun the gather or
  have access to the same tool.

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

- **Applicable evidence.** Verify behavior with tests or direct program/API runs. Where required,
  use build and analyzer results under the project's actual warning policy, API compatibility
  reports, documentation observations, or a security gather. CHECK evaluates those results against
  the criteria rather than adding a source review or requiring a universal API baseline.
- **Build and test evidence is executed evidence.** Link the original runner or CI output for the
  candidate. Record the actual commands, exit status and counts; red↔green for a fix with both
  exit codes. An unfinished or not-started run carries no invented exit status or selected count,
  and a later retry does not erase the earlier
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
- **Security** — the coder's trigger and boundaries apply; the review is evidence, the decision
  CHECK's, and its absence `unverified`, never a pass.
- **A refusal is asserted by its reason.** A test catching an exception proves the refusal only when it
  binds to the specific cause: the message fragment, `ParamName`, a provider error number/code, or the
  resulting state. `Assert.Throws<ArgumentException>` and `Throw<InvalidOperationException>()` alone are
  not evidence, and a bare `ThrowAsync<Exception>()` never is; cancellation binds to the token's
  identity or state, not to the exception type. Before a package is frozen, sweep every guard in it for
  the pattern, not only the site CHECK named.
- **Missing evidence stays `unverified`**, to be re-gathered under the base; it is not a product
  defect, not an implementation attempt, and not an infrastructure criterion. A genuine inability to
  proceed is DO → ACT per the base.

### Coverage comparison and report reuse

- **Baseline comparability.** Reuse a captured baseline across candidates, attempts, revisions and
  sessions while the baseline inputs remain unchanged and its comparison basis remains comparable:
  baseline source/tests, build and coverage configuration, instrumentation tool/version, test scope
  and provider, measurement-relevant environment, exclusions and denominator. `r`, `n` or a new
  session alone does not invalidate it. Baseline and candidate source are expected to differ: bind
  each report to its own source and compare only under a comparable metric/specification. Added
  production branches belong in the candidate denominator; do not force stable-ID attribution across
  changed branches without a valid mapping. Missing, unreliable or incomparable data justifies only
  the narrow gather needed to restore comparability; no invented hash/metadata gate. Benchmark
  baselines remain governed by their paired measurement conditions.
- **Candidate reports.** Generate a coverage summary once for each complete relevant raw-report set,
  candidate and filter/report configuration; reuse it while those inputs remain equivalent, rather
  than running ReportGenerator after every partial collect. Keep separate report scopes (for example,
  overall and integration); merge/union only when branch data is preserved and configurations are
  comparable, and never treat a filtered report as the full required gate. Filtering changes the
  reported denominator, not collection duration. Retain raw reports immutably. If report generation
  failed and its tool/configuration is corrected, regenerate from unchanged valid raw reports without
  recollecting them.
- **Branch delta is diagnostic scope.** Where project policy requires branch delta, use changed
  files/types for local diagnosis and attribution, and report the selected denominator plus
  baseline/candidate comparability. This does not reduce the required scope, threshold, whole-solution
  gate or dedicated integration gate. At the appropriate boundary, ensure the final gate has valid
  complete-scope evidence; reuse an already adequate complete report when its identity is equivalent
  instead of collecting again. A coverage campaign or explicitly global metric keeps its prescribed
  method and scope.

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
- **Freeze order and line endings.** Where the project pins CRLF or another normalisation, normalise
  the final files **before** freezing: normalise → record candidate identity in place → build
  → one measurement on that same identity. Building or measuring before the last normalisation, or
  freezing a set that differs from the built one, makes the measurement invalid: re-freeze and
  re-measure once — an evidence re-gather, not a new product attempt.
- **Timeouts follow the owning policy.** The base DRIVER (or normal-mode primary) uses
  `../pdca/references/driver.md` §Dispatch transport → §Interrupted dispatches for role calls; the base
  requires it to load that reference in full from the `pdca` load's base directory
  (`../pdca/SKILL.md` §References). Command/test
  timeouts remain run evidence under the coder's run record. A timeout creates no criterion or product
  attempt; diagnose recurring infrastructure failures under base Recovery, not as product defects
  without causal evidence.
- **Test host safety (DO and CHECK).** Apply `../pdca-coder/SKILL.md` §Test run safety (every phase —
  DO and CHECK) in full, including its host-capacity, shared-scarce-resource and measurement-interference
  rules; do not narrow them to database/benchmark resources or impose a global serialized gate. Cap the
  test host, e.g. `DOTNET_GCHeapHardLimit=0x80000000
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
  or evidence path of its own: the overlay inherits the base `evidence_root` (base §Workspace and
  durable status) and introduces no path that competes with it. The executor remains the sole status
  writer; the original task, phase reports, dialogue language and Git ledger come from the base
  unchanged; per-unit evidence belongs to the parent cycle record, not a per-unit status file.
- **Artifacts and cleanup.** Record build, test and observation evidence per the base CHECK
  packaging rule; product changes stay in the checkout. Bind evidence to the relevant candidate
  inputs, including meaningful uncommitted changes; `HEAD` alone neither proves nor disproves
  equivalence. Drift in the candidate makes CHECK reconsider only the impacted conclusion per the
  base. Cleanup is not a
  phase gate and nothing is deleted automatically: preserve proof and recovery per the base, limit
  any cleanup to task-owned artifacts within an explicit allowed scope, and never move or lose
  original source data. A true DO → ACT terminal outcome needs no phantom successful CHECK to permit
  cleanup.

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
  executor includes in full inline in every `pdca-check` handoff (CHECK cannot read the installed
  file); and `../pdca/references/act.md` read by `pdca-executor` at status-file creation and every
  status write.
