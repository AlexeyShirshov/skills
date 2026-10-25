# CHECK deltas for .NET: streams, audit, completeness

Reference for the CHECK phase of the .NET overlay. The base CHECK — independence, the criteria
matrix, findings and carrying claims, the veto, local vs whole-goal checks, verdict and routing, the
re-gather append instruction — stays in `../../pdca/references/check.md` and `../../pdca/SKILL.md`.
The two beats, the `pdca-check` session rule, the four parallel streams and the worktree merge stay in
`../../pdca-coder/references/check.md`. This file fixes the .NET stream→agent mapping, the audit items'
.NET artifacts, the inner-loop evidence gate and the completeness gate.

## Streams and audit items

Four unconditional streams + the conditional security gather, launched in parallel in one turn; the
verdict for every stream is `pdca-check`'s (beat 2).

- **Code audit (two-phase)** — `dotnet-code-review-agent` returns **raw candidates** (diff sliced by
  files/chunks, `file:line` + rule ID/counter, **no verdict/severity**); `pdca-executor` runs the
  deterministic mechanics (build 0 warnings, suppression/slop scan, public types, XML-doc coverage) —
  items 3–6, 9–10. Judgment in `pdca-check` — items 7–8. Async/concurrency subagents by trigger are
  part of this gather.
- **Test lens** — `dotnet-testing-specialist` + `pdca-executor` (run, coverage against the **project
  threshold**, CRAP) — item 11. It also gathers the `.pdca/scripts/validate_inner_loop.py report
  <evidence.json>` exit code; a missing/invalid gate fails the lens **closed**, never a warning.
- **Doc lens** — `dotnet-docs-generator` (+ `dotnet-api-docs` on demand) — item 12.
- **Perf lens (two-phase)** — when PLAN says "needed": measurement (`dotnet-benchmark-designer` +
  `pdca-executor`; `dotnet-performance-analyst` only with ready artifacts) → **raw numbers + baseline,
  no verdict**; async hot paths + `dotnet-async-performance-specialist`; "not needed" → `file:line`
  facts; judgment in `pdca-check` — item 13.
- **Security audit\*** (conditional **gather**) — `pdca-security-auditor` if the diff touches
  auth/secrets/external input/crypto; same parallel turn, medium tier, by trigger. It is a gather
  stream: its report **returns into the aggregated report** and is judged by `pdca-check` in beat 2.
  It issues **no independent verdict** and never routes a defect around the aggregate triage. The
  brief carries the diff/area (it may take `git diff` itself; read-only `bash`) and it audits without
  `pdca-scout`; `pdca-scout` only for facts outside the diff (other occurrences, callers,
  `appsettings*`/`.gitignore`) via a narrow question — like `pdca-escalate` it does not surf
  (`grep`/`glob`/web denied).

**Trigger specialists** (cheap, read-only, same parallel turn; output joins the aggregated report,
verdict still `pdca-check`): `dotnet-async-performance-specialist` (`ValueTask` vs `Task`,
`ConfigureAwait`, `async void`, sync-over-async, state-machine allocs, `Channel`/`IO.Pipelines`,
ThreadPool starvation); `dotnet-csharp-concurrency-specialist` (races, deadlocks,
`lock`/`SemaphoreSlim`/`Interlocked`, lock order); `dotnet-performance-analyst` **only with data**
(`dotnet-trace`/heap dumps/benchmark comparisons). Each is an additional **gather**, not a new gate.

Each stream relies only on the plan/diff and does not wait for another. Gate 3 passes only with **all
green** (four unconditional + security if launched); a stream failure becomes a `D:` task for
`pdca-executor` (or a PLAN return via `pdca-planner`, if the plan is wrong) and does not cancel the
others. **Any failed CHECK stream — including a triggered security failure — counts as a failed CHECK
of the current revision** for the base escalation counter; ordinary security findings use the shared
attempt/defect-history counters, and only a **hard security trade-off** escalates immediately.

### Audit workflow — .NET artifacts (items 3–13)

Items 1–2 (load skills, read project registries on demand) are the coder's. .NET specifics:

3. **Analyzer baseline:** build (0 warnings — gate); list active `dotnet_diagnostic.*` severities in
   `.editorconfig`.
4. **Suppression/slop scan:** `#pragma warning disable`, `[SuppressMessage]`, `<NoWarn>`, `Skip=`,
   empty `catch`, `Task.Delay`; count suppressed vs justified and report the ratio.
5. **Smell scan** (`dotnet-csharp-code-smells`: IDisposable, suppression, async, DI, NRT, optional
   `= null`), each with its CA rule and fix.
6. **Public-API scan:** enumerate public types/members; BCL-conflict/convention rules (`api-design`);
   XML-doc coverage (CS1591); surface-lock status.
7. **Judgment (`pdca-check`):** classify raw candidates with the project taxonomy (`P0/P1/P2` API,
   `🔴/🟡/ℹ️` smells default) — real defect vs noise; do not invent a scale.
8. **Per-finding (`pdca-check`; facts from gather):** exact number, `file:line`, CA/analyzer ID or
   naming rule, a one-line fix; split **fix now** vs **accepted/deviation with justification**.
9. **Registry records** (if any) by `pdca-executor` in `Was`/`Now`/`Check`; do not rewrite unrelated
   sections. **Author ≠ certifier:** an independent read-only stream re-derives each
   registry/acceptance claim from the cited `file:line`; a mismatch or a code-basisless self-assessed
   `deferred`/`acceptable` is a finding.
10. Hot-path measurement favors the perf specialist; the code fix is `pdca-executor`.
11. **Test lens** (parallel) — see §Inner-loop evidence gate; a missing test, a coverage drop or an
    open variant-matrix row is a `D:` task, not "good enough".
12. **Doc lens** (parallel). Per PLAN verifies **both**: prose docs (README/guides/DocFX,
    examples/migration notes) **created** and **matching the implementation** (content, not presence;
    `dotnet-docs-generator`); and XML-doc comments **only when mandated** (CS1591) or
    user-requested — generated on every new/changed public member and matching signatures/behavior
    (`dotnet-api-docs` on-demand). A gap/mismatch → `D:` task for `docfx-specialist`/`pdca-executor`.
13. **Perf lens** (two-phase, parallel). Gather: measurement done with numbers + baseline, or
    `file:line` one-time facts. Judgment (`pdca-check`): against the PLAN perf decision — regression
    acceptable? plan fulfilled? argument convincing? Work in a per-row loop with no measurement → `D:`
    task (measure) or PLAN return; no silent close.

**Inlined specialists may not drop the port.** An overlay that inlines a specialist's checklist into
CHECK must keep that agent's **skill-loading** (step 1) and **measurable artifacts** —
suppression/slop counts and ratio (step 4), per-finding `file:line` + rule ID (step 8) — not just its
topic list. A CHECK that skipped step 1 or reports no numbers is **not** a pass.

## Inner-loop evidence gate (mandatory, fails closed)

The lens requires the `.pdca/scripts/validate_inner_loop.py report <evidence.json>` result (reconciled
with `--journal <journal.json>` when the raw journal exists); if the validator is missing, cannot run,
or exits nonzero, CHECK **FAILS** — never warns. It FAILS on any of: the inner loop ran the **whole
solution** or an **integration** run inside DO; the exact commands/phase/exit codes are missing; a
**missing or zero `selected_count`** on a `finished` run (`selected_count ≥ 1` per execution — a
zero-match run is rejected); a result invented for a run that never finished
(`failed-to-start`/`not-started`/`interrupted` must not carry one); **stale `--no-build` artifacts**
after a compiled edit (`source_revision != artifact_revision`, or no prior build with the matching
artifact revision); the scope was **widened without a prior validated amendment**; a boundary
**relabelled/fabricated**; a **projection that omits a started execution**; or a **boundary
integration count above the planned budget**. Unlimited unfiltered **unit** runs inside DO are
legitimate and never consume an integration budget.

## CHECK completeness gate — mandatory evidence contract

**Before PASS:** reconcile the current pinned contract with the frozen evidence manifest (the
reconciliation object — one contract row → evidence by reference; `references/plan.md` §Versioned
evidence contract) and inspect the referenced evidence. Every applicable required row must be
satisfied by actual evidence for the current `rv`; every `required_rows` entry must be `met` or `na`,
and any `open` row that is **binding/applicable** forbids PASS. A retained audit row carrying a valid
`diagnostic_nonbinding` disposition is reported separately and does not block PASS
(`references/plan.md` §Binding/applicability disposition); genuine required checks are never waived.
Required artifacts must exist and support the reported result. N/A is valid only when its pinned
observable predicate is demonstrated; unconditional obligations cannot be waived.

**Mandatory mechanical gate before reading rows.** CHECK runs both tracked helpers on the frozen
manifest and treats a nonzero exit as **evidence FAIL** (re-gather/STOP, never PASS):
`.pdca/scripts/validate_inner_loop.py manifest <manifest.json>` (row/evidence shape + two-way
`required_rows` ↔ `rows[]` coverage) and `.pdca/scripts/pdca_evidence.py lint --repo <root> --manifest
<manifest.json>` (frozen-tree binding, recomputed independently, plus the same coverage). A manifest
whose tree does not reconcile, a missing required row, an undeclared row, or a dangling evidence
reference is an open evidence gate — never a reason to reclassify the row.

**Missing evidence is not a product defect:** re-gather reports, logs, artifacts, or missing check
results from the designated owner inside CHECK, within the declared re-gather plan and existing permissions. Do
not return to DO, count a DO iteration, or issue product FAIL solely because reporting is missing. Do
not invent evidence or edit the product as part of re-gathering.

A verified product defect still requires FAIL and the existing loop-back. A newly uncovered required
variant requires a justified CHECK → PLAN contract revision with explicit supersession and preserved
obligations; CHECK must not silently add, remove, or weaken contract rows.

**Bounded gathering:** if the re-gather plan is exhausted with required evidence still open, leave CHECK
unresolved, report the open row IDs and reasons, and follow the existing blocker/escalation rules.
Never issue PASS while a binding/applicable required row is open. This gate adds no state-machine
phase and does not lower existing priorities or replace existing correctness checks.

**PLAN does not invent audit hard gates.** For an ordinary product task, PLAN must not add a hard gate
on arbitrary audit completeness — a full transitive reference graph, retrospective hashes, or an
execution-time `committed == tested` proof — beyond the agreed scope and the skill's unconditional
checks. Extra audit metadata belongs in the plan as separate **diagnostic notes**, not as required
acceptance: their absence or incompleteness must not force extra DO iterations or retests, a CHECK →
PLAN return, an escalation, `incomplete`, or STOP. The result on the mandatory checks is not
downgraded to FAIL/`incomplete` because of such notes, and the notes are not treated as a product
defect. A self-imposed mandatory-extra audit row is a contract-classification defect, not a new
product blocker: CHECK records the original row and the reason for its non-binding classification by
the priority global rule instead of silently deleting or replacing it. This is a boundary on *audit
over-reach*, not a weakening of real requirements — see `references/plan.md`
§Binding/applicability disposition.

## Optional-null/default smell (C#)

**`T? x = null`, incl. `= default` for reference/nullable, especially on `*Options`:** severity 🟡 by
default, 🔴 if it allows silently choosing wrong behavior, ℹ️ for a genuine sentinel. Fix: a pair of
overloads — a parameterless (`CancellationToken`-only) one with internal `x: null`, plus a required
overload with `ArgumentNullException.ThrowIfNull(x)`. Constraints: overloads differing only in a
nullable annotation are a duplicate signature (**CS0111**); with `TreatWarningsAsErrors=true`, `null`
in a required parameter is **CS8625** (the gate).

## Boundaries and output

Code and registry edits by `pdca-executor` (Do); renames/analyzer policy in Do; do not re-open fixed
findings; out of scope: profiling, security review. Check output: project language, `P0/P1/P2` or
`Finding N` with `Was`/`Now`/`Check`, exact numbers, up front the build baseline + suppression ratio.
