---
name: pdca-dotnet
description: ".NET/C# overlay for the PDCA family — inherits `pdca` (base cycle) and `pdca-coder` (programming overlay), and adds only the .NET differences: the dotnet toolchain and command forms, Roslyn-first symbol work, versioned evidence and the inner-loop gates. User-invoked — runs only when the user explicitly names `pdca-dotnet`."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# pdca-dotnet: the .NET/C# overlay

**This is an overlay, not a cycle.** It contains only its differences from the contracts below: no
PLAN of its own, no state machine, no second status file, no separate routing branch.

**Inheritance chain.** The base `../pdca/SKILL.md` first (entry, form, roles, gates, counters,
recovery), then `../pdca-coder/SKILL.md` (the programming overlay), then this file. When the chosen
form is not the ordinary cycle, the form contract (`../pdca-incremental/SKILL.md`,
`../pdca-collection/SKILL.md`) also loads before the coder overlay. Phase references load at the
start of their phase, exactly as the base says; this overlay's references load the same way
(§References).

**One PLAN, one state machine, one status file.** The overlay is applied **to** the form PLAN
chose — an ordinary cycle, an incremental step, the relevant items of a collection — and never opens
a second cycle, a second gate set or a second durable state.

**If this file and the base or the coder overlay disagree on their rules, they win.** This file only
adds .NET facts, tools and the required relevant evidence. Where it restates an inherited rule in one
line (a reminder for the .NET reader), the inherited text is authoritative.

## When it applies

- **.NET work** — C#, F#, VB on .NET: implementation, refactoring, tests, solution/project/build
  configuration, package and public-API-surface work, and the docs tied to code. The overlay is
  applied to the ordinary cycle, to incremental steps and to the relevant collection items without a
  duplicate PLAN or a second state machine.
- **Symbol work is Roslyn-first.** Definitions, references, call sites, implementations, overloads,
  members, renames and impact questions are resolved with the `roslyn` tool, never with text search
  (§Roslyn-first for C# symbols).
- **A mixed repository** applies it to the .NET component or step only; other stacks in the same
  repository stay under the coder overlay alone. Specialised knowledge is loaded **only for the
  current step** — not every .NET skill at once.
- **Auxiliary verification code does not reclassify a non-coding goal** (inherited from the coder
  overlay): a checker or script makes **that component** .NET work, not the whole campaign.

## .NET toolchain and commands

The coder's toolchain and lens selection runs unchanged; this section fixes the concrete .NET
commands so a plan does not reinvent them.

### Canonical command forms (frozen; do not reinvent per plan)

- **Builds** — affected project(s) and their dependencies, sequentially. A solution/root build is
  allowed only when the plan proves the host can carry it (memory budget, lane count) and the phase
  permits it; it is never an unexamined default.
- **Selectors** — fully-qualified `-class`/`-method` names. A short name that selects zero cases is
  rejected: `0 selected` is failure, not green. Runner exit codes are pinned (`0` success, `2`
  executed-case failure); a red arm's non-zero exit is recorded against its declared identity.
- **Integration** — one container-backed boundary lane under the shared lease, the provider
  connection environment set, no provider-skip opt-out enabled, skip budget applied only to the
  complete sweep (never to a class-filtered log). A transport/resource timeout gets one sanctioned
  rerun; two consecutive same-class infra failures escalate.
- **Mutation** — probe the harness before planning a mutation run. A broken runner mode or absent
  provider config is a tooling incompatibility: the controlled-mutant fallback (inject the change,
  kill the mutant, observe the intended assertion) is planned **up front**. No score is claimed
  from a run that did not execute.
- **Documentation** — EN/RU pairs move together; verify byte-level line endings (CRLF preserved),
  EN↔RU section parity, and the absence of links into internal specs. A doc-only deviation is still
  a deviation: fix it in DO/CHECK, never in ACT.

The inner loop itself — the affected subset, `dotnet test <project> --no-build --filter <selector>`,
the boundary rule and the mandatory `test scope` envelope — is in `references/plan.md`
(§Inner-loop gate) with the coder's build/test command forms.

### Roslyn-first for C# symbols

- The `roslyn` tool is the **only** way to answer a C# symbol question: `structure`/`types` for
  discovery, `members`/`refs`/`callers`/`implementations` for the answer, `rename` for changes.
  `rg`/`grep`/`glob`/`sed` are never a symbol tool, and a symbol inferred from text search is not a
  resolved symbol.
- In Code Mode the call goes **inside `execute`**:
  `const r = await tools.roslyn({ action: "refs", target: "Ns.Type.Member" }); return r`. Several
  queries are batched in one `execute` (`Promise.all`); the daemon keeps the solution loaded.
- A solution that is not the session directory is named explicitly:
  `solution: "/abs/path/App.slnx"`. A missing catalog entry is resolved with `search({ query:
  "roslyn" })` first — not by falling back to text search.
- A rename is applied with `roslyn rename` (dry-run first, then `apply`), never by a textual
  substitution; the result is re-checked by the same tool.
- Text search stays legal **only** for non-symbol text — string literals, comments, docs, configs,
  non-`.cs` files — and is reported as such.
- Roslyn resolution belongs to the **source-side gather** on the frozen snapshot
  (`references/plan.md` → Reviewer evidence pack); medium CHECK evaluates the pack and does not run
  Roslyn against an inaccessible solution.

### .NET specialists (gather-only)

Selected by PLAN, dispatched as extra gathers whose reports join the aggregated report; they never
issue a verdict (that stays `pdca-check`'s) and never widen permissions. Tiers are role labels only:

| Specialist | When | Tier label |
|---|---|---|
| `dotnet-architect` / `dotnet-code-review-agent` | PLAN design/perf area review; CHECK code-audit raw candidates (no verdict) | cheap |
| `dotnet-testing-specialist` | test strategy, coverage config, gaps; CHECK test lens | cheap |
| `dotnet-docs-generator` | CHECK doc lens: affected docs, doc mismatch | cheap |
| `dotnet-api-docs` | generated API-doc lens, on demand | cheap |
| `docfx-specialist` | DocFX structure and doc-site pages | cheap |
| `dotnet-benchmark-designer` | perf gather when PLAN says measurement is needed | cheap |
| `dotnet-performance-analyst` | only with ready artifacts (traces, heap dumps, comparisons) | cheap |
| `dotnet-async-performance-specialist` | async hot paths: `ValueTask` vs `Task`, `ConfigureAwait`, `async void`, sync-over-async, state-machine allocs, `Channel`/`IO.Pipelines`, ThreadPool starvation | cheap |
| `dotnet-csharp-concurrency-specialist` | races, deadlocks, `lock`/`SemaphoreSlim`/`Interlocked`, lock order | cheap |
| `pdca-security-auditor` | diff touches auth/secrets/external input/crypto | medium |

Answers come from the repository's declared skills/agents. A missing .NET specialist is replaced by
the coder's explicit generic-role path (`pdca-scout` for facts, `pdca-executor` for mechanics,
`pdca-check` for judgment), never by a fabricated name. Skills are loaded on demand for the current
step: `dotnet-solid-principles`, `type-design-performance`, `analyzing-dotnet-performance`,
`dotnet-csharp-code-smells`, `slopwatch`, `dotnet-api-surface-validation`, `api-design`,
`dotnet-library-api-compat`, `dotnet-editorconfig`, `dotnet-add-analyzers`,
`dotnet-csharp-nullable-reference-types`, `dotnet-testing-strategy`, `dotnet-test-quality`,
`crap-analysis`, `dotnet-xunit` / `dotnet-tunit-test`, `dotnet-integration-testing`, `testcontainers`,
`snapshot-testing`, `dotnet-xml-docs`, `dotnet-github-docs`, `dotnet-mermaid-diagrams`,
`dotnet-documentation-strategy`.

## .NET plan deltas

Gate 1 fields, carrying claims, the form and the effort policy stay the base ones; on top of the coder's
code plan, a .NET plan carries these **decisions with their evidence**, or gate 1 fails. The six
lenses stay the coder's; their .NET skill binding and the concrete look-at items are in
`references/plan.md` (§PLAN lenses and .NET skills).

- **Versioned evidence contract, pinned in the status file before DO.** Stable requirement/row IDs,
  expected evidence kinds and sources, the exact command with exit-code/log requirements, planned
  artifact locations (or a justified N/A), the owner stream, an observable applicability predicate,
  the contract revision `rv`, a **`PLAN-LINT` row**, a finite CHECK re-gather plan with its owner,
  and the frozen manifest path. No optional slots: the layout is the plan's, the obligations are not.
  Detail — contract rows, the attempt child `attempts/c<N>-r<r>-n<n>/`, the DO ledger, the frozen
  manifest and its two-helper gate, the `pdca_evidence.py` pipeline, the append-only
  binding/applicability disposition, contract revision: `references/plan.md` (§Versioned evidence
  contract).
- **The command projection and `plan_lint.py`.** The prose block of **verification** commands (the
  ones that produce acceptance evidence — never DO's implementation actions) is not
  machine-checkable, so PLAN also emits `<evidence-dir>/inputs/commands.json` and validates it before gate 1 and again
  on DO entry after re-anchoring:
  `python3 .pdca/scripts/plan_lint.py check --repo <checkout> --commands <projection> --receipt
  <evidence-dir>/plan-lint.json`, and `probe` when a harness probe is declared. Exit `0` ok, `2`
  violation, `1` usage/operational; a nonzero `check` **is** a gate-1 failure, and its receipt is the
  `PLAN-LINT` row. Detail: `references/plan.md` (§Machine projection).
- **Per-unit `test scope` and the inner-loop gate.** Every unit names its affected test
  project(s) and exact non-broad selectors, the single DO → CHECK boundary sweep, and which projects
  really execute integration tests with how many boundary runs. `pdca-executor` validates the
  envelope before editing (`validate_inner_loop.py brief <brief.json>`, fail-closed) and the report
  before CHECK (`report <evidence.json>`, reconciled with `--journal`); missing or invalid evidence
  fails closed. Detail — the mandatory JSON envelope, `project`, `manifest`, the journal and the
  execution states: `references/plan.md` (§Inner-loop gate).
- **.NET test strategy.** Unit vs integration by what a unit test cannot see (EF Core/Testcontainers,
  `WebApplicationFactory`, DI graph, serialization/snapshot, migrations); coverage config and
  threshold discovered from `Directory.Build.props`/`Directory.Packages.props`, `.runsettings`,
  `coverlet.runsettings`, `dotnet test --collect:"XPlat Code Coverage"`, the CI workflow or a
  baseline; **branch** delta and mutation (Stryker.NET scoped to the touched assembly/type), CRAP.
  The project threshold is the lower bound; no config → record the baseline, never invent a
  threshold. Detail: `references/plan.md` (§.NET test strategy deltas).
- **Test run safety (every phase).** Cap the test host (`DOTNET_GCHeapHardLimit=0x80000000
  DOTNET_gcServer=0`, 2 GiB — raise only when justified) inside a wall-clock `timeout 600 …`;
  serialize heavyweight suites; stream the log (`2>&1 | tee <log>`, keep `rc=${PIPESTATUS[0]}`),
  never `| tail`. Exit **137**/"Out of memory" ⇒ an unbounded test: stop, record the test and the
  command, do not re-run without the cap. `references/plan.md` (§Test run safety).
- **Docs.** Prose docs are the third DO stream (README/guides/DocFX, `docfx-specialist`); XML-doc
  (`///`) follows the finished code and is mandatory only when the project enables it
  (`GenerateDocumentationFile` / CS1591 under `TreatWarningsAsErrors` or `<NoWarn>`) or the user asks.
  Detail: `references/plan.md` (§.NET documentation owners).
- **The reviewer evidence pack is planned at the DO → CHECK boundary.** The full bodies a reviewer
  needs are staged (a copy, not a move) into `rv<k>`, independently verified by a read-only
  source-side gather against the same frozen snapshot — source identity, digest, staged-vs-source
  equality, Roslyn/C# resolution. Detail: `references/plan.md` (§Reviewer evidence pack).

### Completeness gate at PLAN

PLAN does not invent audit hard gates: for an ordinary product task it must not require a full
transitive reference graph, retrospective hashes or an execution-time `committed == tested` proof
beyond the agreed scope. Such metadata is a **diagnostic note**, and its absence forces no extra DO
iteration, retest, return, escalation or STOP. The mandatory checks above are not downgraded because
of a note; the classification path for an already-frozen extra row is in `references/check.md`
(§CHECK completeness gate).

## .NET check deltas

CHECK keeps the base two beats and verdict and the coder's four unconditional streams plus the
triggered security stream; .NET binds each stream to its agent and adds the evidence gates.

- **Stream → agent.** Code audit: `dotnet-code-review-agent` raw candidates + `pdca-executor`
  commands (build 0 warnings, suppressions/slop, public surface, XML-doc coverage) with judgment in
  `pdca-check`. Test lens: `dotnet-testing-specialist` + `pdca-executor` (run, coverage vs the
  project threshold, CRAP). Doc lens: `dotnet-docs-generator` (+ `dotnet-api-docs` on demand). Perf
  lens: `dotnet-benchmark-designer` + `pdca-executor`, raw numbers and baseline only; a profiling
  analyst only with artifacts. Trigger-only gathers: async and concurrency specialists, and
  `pdca-security-auditor` for a diff touching auth/secrets/external input/crypto. Gate 3 needs all
  green, and any failed stream — including a triggered security failure — is a failed CHECK of the
  current revision for the base counter. Detail: `references/check.md` (§Streams and audit items).
- **Inner-loop evidence gate (fails closed).** The test lens requires the
  `validate_inner_loop.py report` exit code (reconciled with `--journal` when the raw journal
  exists). A missing/unrunnable/nonzero validator FAILS the lens; so do a whole-solution or
  integration run inside DO, missing commands/phase/exit codes, a zero or missing `selected_count`, an
  invented result for a run that never finished, stale `--no-build` artifacts, an unamended scope
  widening, a relabelled boundary, an omitted started execution and a boundary integration count
  above the planned boundary runs. Unlimited unfiltered **unit** runs are legitimate.
  `references/check.md` (§Inner-loop evidence gate).
- **Evidence completeness.** Before PASS, the pinned contract is reconciled with the frozen manifest
  (contract row → evidence by reference), both helpers must exit `0`, every applicable required row
  is `met` or `na`, and a retained `diagnostic_nonbinding` audit row is reported separately without
  blocking. Missing evidence is re-gathered within the declared re-gather plan — not a product defect, not a DO
  iteration. `references/check.md` (§CHECK completeness gate).
- **Reviewer pack reconciliation.** CHECK reads row-level evidence addressably, confirms
  staged-vs-source fidelity with the gather's actual finding, and treats a missing body, a mismatch
  or an absent independent verdict as **evidence open/blocked**, not product FAIL and not PASS.
- **Optional-null C# constraints.** An optional `T? x = null`/`= default` on `*Options` is 🟡, 🔴 if
  it silently chooses wrong behavior; the fix is a pair of overloads. Overloads differing only in
  nullability are a duplicate signature (**CS0111**); under `TreatWarningsAsErrors`, `null` in a
  required parameter is **CS8625**.

## .NET do/act deltas

- **Execution journal and the unit/integration policy.** The restriction is on the **actual**
  integration run, not on report entries: unit tests are unlimited in DO, expensive integration runs
  happen at the DO → CHECK boundary within the planned scope. Every started run is recorded
  (`start` at launch, result appended) and the CHECK report is **projected** from the raw journal, so
  an omitted execution is a completeness failure and a run beyond the planned boundary stays in the journal.
  `references/act.md` (§Execution journal and the unit/integration policy).
- **Cleanup receipt.** Only on a genuine terminal closure, gated by
  `validate_inner_loop.py cleanup <receipt.json>`: approved terminal closure + independent final
  verdict, deletion limited to this task's `rv` staged copies, retained report/manifest/digests, and
  `archived <manifest.json> --cleanup <receipt.json>` checking the manifest digest. Premature or
  blanket cleanup is rejected; STOP/incomplete/continuing work keeps its staged evidence.
  `references/act.md` (§ACT cleanup receipt).
- **Status additions.** The coder's status rows plus the pinned contract revision `rv` and its rows,
  the `PLAN-LINT` receipt, the attempt identity `task/N/r/n` with the frozen snapshot hash and the
  authoritative `manifest.json` path, the reviewer-pack pointer, and the cleanup receipt on closure.
  `references/act.md` (§Status-file additions).
- The coder's parallel DO streams, worktree sub-tasks, editing discipline, debugging order, security
  boundaries and handoff additions apply unchanged; a worktree brief additionally carries the
  mandatory `test scope` envelope.

## Composition

| Area | Where it comes from | This overlay |
|---|---|---|
| Entry, one PLAN, forms, overlay selection | base | inherits — never classifies, never re-plans, adds no form |
| Roles and host requirements | base | inherits; adds the `dotnet-*` gather lenses as gather-only roles |
| Control modes, approval, campaign/cycle control | base | inherits unchanged |
| State machine, counters (`N`, `r`, `n/3`, `rv`), status file | base | inherits unchanged — no local counters, no execution-variant enum |
| Lens / probe / increment / step boundary | base | inherits; a .NET increment is one code question with its own check |
| Gates 1–4, claims and veto, evidence chain, effort policy, recovery, escalation | base | inherits; gate 1 gains the .NET decisions above, gate 3 the .NET streams |
| Generic constraints, red flags | base | inherits; no .NET addition to the lists |
| Toolchain/lens selection, code anti-patterns, parallel DO streams, worktree sub-tasks, security boundaries, optional specialists | coder | inherits unchanged |
| .NET commands, Roslyn-first, versioned evidence, inner loop, completeness gate, reviewer pack, cleanup receipt | this file | adds |

The overlay adds **no** universal numeric cap of its own (the integration scope is fixed by PLAN),
no second approval, no new reporting framework and no permission widening. Its references hold the
bulky .NET contracts; the inherited phase references are loaded alongside them, never replaced.

## References

Loaded at the start of their phase (the host truncates tool output, so a contract loaded whole would
lose its tail — the base rule):

- `references/plan.md` — the .NET lens→skill binding, versioned evidence contract,
  `pdca_evidence.py` pipeline, `commands.json` + `plan_lint.py`, the `test scope` envelope and
  `validate_inner_loop.py` inner-loop gate, test run safety, the .NET test-strategy and documentation
  deltas, the reviewer evidence pack, evidence helper discipline. Load with
  `../pdca/references/plan.md` and `../pdca-coder/references/plan.md`.
- `references/check.md` — .NET stream→agent mapping, the audit items 3–13, the inner-loop evidence
  gate, the CHECK completeness gate, the optional-null C# case. Load with
  `../pdca/references/check.md` and `../pdca-coder/references/check.md`.
- `references/act.md` — execution journal and integration policy, the ACT cleanup receipt, the
  status-file additions. Load with `../pdca/references/act.md` and
  `../pdca-coder/references/act.md`.
