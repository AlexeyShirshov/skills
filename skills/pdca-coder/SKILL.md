---
name: pdca-coder
description: "Programming domain overlay for the PDCA family — adds only code-specific criteria forms, evidence, command safety and DO/CHECK/ACT additions to the form and overlay the base already selected. User-invoked — runs only when the user explicitly names `pdca-coder`."
metadata:
  opencode/autoinvoke: false
disable-model-invocation: true
---

# pdca-coder: the programming overlay

**This is a domain overlay, not a cycle, a driver or a phase state machine.** It carries only
code-specific additions: no form or phase state machine, no PLAN of its own, no counter, gate,
acceptance rule, approval, escalation ground or status shape. Those live once in the contract the
base selected (`../pdca/SKILL.md` §Common cycle contract, or the form that inherits or governs it).

**What it composes with.** The base contract carries the form, the user's original task and its
acceptance, and the current cycle/step scope; entry and driver routing stay the base's. This overlay
applies to the code component or step of that form — bounded, an incremental step, or a collection
item — and never reclassifies the task, selects another form or opens a second PLAN. An already
selected form and overlay set stay as they are. Invoked directly without the base loaded, load the
contract already in force — `../pdca/SKILL.md` for a bounded cycle,
`../pdca-incremental/SKILL.md` (which inherits it) for an incremental step,
`../pdca-collection/SKILL.md` with its local common contract for a collection — and preserve that
form. If no form is in force, the base entry decides it; this overlay does not.

**Apply code discipline inside the unchanged task.** The original task, its global requirements and
acceptance stay as supplied, with user criteria verbatim, and the current cycle or step keeps its own
scope; the code-specific discipline below applies within them, and a local result is not the whole
goal. The governing contract remains authoritative, a user-prescribed method stays a requirement, and
this overlay neither widens nor narrows the task.

## When it applies

- **Software work in any stack** — writing and changing code, tests, documentation, refactoring and
  configuration.
- **Applied to the relevant component or step.** A step that touches no code runs without it; a
  mixed repository applies it only to the code component.
- **Auxiliary verification code does not reclassify a non-coding goal.** A checker, script or
  utility written to verify an otherwise non-coding result makes **that component** coding work,
  not the whole goal or campaign.
- **Specialised knowledge loads only for the current step**, not every language/quality skill at
  once; the repository supplies the concrete IDs and this overlay names the generic ones.

## Toolchain and lenses

The usable toolchain is a property of the existing project environment; each phase decides only
what it owns.

- **Discover, do not invent.** Take the declared build/test/lint/format/docs commands from the
  project's manifests, CI workflow, task runner, README or project overlay. A declared gate runs as
  declared; when the project declares none, use the runnable check the environment actually
  provides and say so. A command, method or threshold the user prescribed is a requirement, not a
  choice.
- **PLAN** — for code work under the base common cycle, PLAN defines the cycle's observable
  criteria; all other plan fields stay the base's. An independent collection keeps its own currently
  governing phase protocol, which this overlay does not modernize and to which it adds no command or
  evidence gate. Toolchain and environment constraints may reach PLAN as input facts via
  `pdca-scout`; choosing commands, a test strategy, decomposition, specialists or verification
  methods is not PLAN's.
- **DO** maps criteria to implementation and chooses its own developer verification and test
  strategy; its runs are candidate evidence, not acceptance.
- **CHECK** chooses per criterion the independent method, lens and concrete command at CHECK time. A
  lens is used when the actual change and the criteria need it: correctness/anti-pattern scan,
  tests, docs, security when a trust boundary is touched (§Security boundaries), performance only
  when a criterion is quantitative, design/type design when the change is structural. Nothing here
  owes coverage, mutation or performance work to a task that does not need it.
- **A missing lens is replaced, not dropped.** Use the generic-role path — `pdca-scout` for facts,
  `pdca-executor` for mechanics, `pdca-check` for judgment — never a fabricated agent name. Role
  labels and tiers stay the base's.

## Code-specific plan deltas

For code work under the base common cycle, PLAN defines the cycle's observable criteria using the
forms below; every other plan field, the original task, the cycle/step scope and criteria ownership
stay as the governing contract sets them.

- **Correctness** — the requested behaviour including its error path and exit status, empty /
  single / many input, malformed or missing input, and a negative condition where the task makes one
  relevant.
- **Public contract** — a signature, format or compatibility guarantee only where the task's result
  includes it.
- **Security** — the property the task requires (authorisation, input trust, secret handling), not
  an audit process.
- **Performance** — a numeric threshold only when the task or the project's declared policy supplies
  one.
- **Documentation** — an obligation only when the task or the declared project policy mandates it.

Criteria state required outcomes; implementation and developer verification belong to DO, and
independent verification to CHECK, as the governing contract assigns. DO may propose a worktree
split, performed only within the cycle's authorised workspace operations.

## Code-specific check deltas

CHECK keeps the base procedure, its per-criterion method choice, verdict, routing and accounting;
this section adds what a code check examines and how code evidence is read. The evidence and safety
rules below hold wherever code evidence is produced or judged — DO follows them when it runs, CHECK
when it judges or requests a run.

- **Applicable work, no fixed tally.** Examine the actual change and the criteria, not a checklist
  of streams: an audit of the diff (build/lint clean under the project's own policy,
  suppressions/slop, smells, public surface when the task touches it), the tests against the cycle's
  criteria, docs against the implementation where required, a security gather when triggered, numbers
  when a criterion is quantitative. A lens with nothing applicable is recorded as not applicable with
  its reason; an "all streams green" tally is not required, and an inapplicable lens never blocks.
- **Coverage of the criteria's own variants.** An execution variant the change actually exposes —
  input kind, `null`/default/uninitialized, value vs reference form, constructor/mapping, projection
  vs whole object, provider/backend, on/off flag — is verified as part of the existing criteria, not
  as new behaviour. CHECK independently notices when a relevant variant of an existing criterion has
  no evidence; the absence is `unverified`, never an automatic product defect. A genuine defect in
  the criteria themselves remains the base CHECK → PLAN route.
- **Evidence and judgment are separate.** `pdca-executor` runs and returns the exit status, key
  numbers and log path; it issues no verdict. `pdca-check` interprets independently and alone
  decides; a specialist's report is advisory input to that decision.
- **Author ≠ certifier.** CHECK re-derives each acceptance or deferral claim from the actual
  `file:line` evidence; a self-authored assessment, an unsupported "acceptable" or a deferred item
  with no code basis is not a waiver. This is the base CHECK's independence applied to code, not a
  second certifier role or an extra approval.
- **A code audit, when chosen, is two-phase.** A cheap gather returns raw `file:line` candidates with
  rule IDs, not severity or a verdict; `pdca-check` judges each as a real defect or noise, its
  severity, and whether it is fixed now or accepted as a deviation. Suppressions, disabled tests,
  empty catches and sleeps in the actual changed code are counted over a meaningful denominator and
  read as candidates that need a reason; the marker alone is not a defect. The .NET overlay names its
  exact markers.
- **Existing registers stay on demand.** Where the repository already keeps defect or deviation
  registers, update only the actual finding; do not reopen a resolved item without new evidence or
  relist accepted deviations, and keep the base defect history. No new register or `Was`/`Now`/`Check`
  schema is required.
- **Integrated candidate.** After an authorised merge or integration, CHECK verifies the integrated
  candidate itself; green components do not make a green integration, and component conclusions are
  re-evaluated against the actual combined result.
- **Session reuse.** Reuse the current `pdca-check` session on a loop-back when the host offers one;
  otherwise a fresh session reads the persisted evidence. Every loop-back dispatch still carries the
  complete inline CHECK reference; reuse never shortens it. This changes no independence or
  accounting rule.
- **Routing and accounting are the base's.** An applicable failing check is a finding; the
  governing contract alone accounts findings and attempts.
- **Finding form.** A finding carries the location, the problem, the required change, the check
  evidence and the numbers; its language follows the project and the base dialogue language. An
  optional user-facing summary never replaces the full report the base records. No fixed severity
  vocabulary, mandatory baseline ratio or line-count limit is imposed here.

### Language and correctness anti-patterns

The correctness lens looks for these in the actual change, and DO does not introduce them:

- **String handling** — culture/locale/encoding assumptions, slicing, chains of `Replace`/`Format`.
- **Collections and iteration on a hot path** — per-call allocation of collections/maps, repeated
  enumeration, `Count()` over a lazy sequence, quadratic joins.
- **Regex** — catastrophic backtracking, compiled-vs-per-call, culture-sensitive options.
- **I/O and serialization** — unbuffered streams, sync-over-async, deserialization of untrusted
  input without limits, culture-dependent number/date parsing.
- **Async** — `async void`, fire-and-forget, `.Result`/`.Wait()`, missing `CancellationToken`
  propagation, `ConfigureAwait` misuse.
- **Design and types** — god classes, fat interfaces, leaky contracts, interface/implementation
  pairs without a second consumer, type-switch, needlessly open/final types, defensive copies,
  mutable collections leaking from a public API.

When the change is structural, the design/type lens checks that construction preserves the type's
invariants and weighs mutability, openness to extension and copy cost against the actual use; where
the choice is non-obvious it may compare the inverse construction, and no whole-repository count or
ratio is required.

**Optional-null/default** — an optional value with a null/default fallback, especially `*Options`, is
a finding when it lets a wrong behaviour be chosen silently. Handle it in the language's own terms:
make the fallback explicit at the boundary, or require the value where its absence would change
behaviour, according to the language contract. The boundary rejects a missing required value only
where the user's contract or the language's nullable contract makes it required, not for every
parameter by default. The C# overload pair is one form, not a requirement for every stack; .NET
nullability specifics belong to the .NET overlay.

### Code evidence requirements

- **Every run returns** its exit status, the key numbers (passed/failed/skipped, warnings, coverage
  when measured) and the log path — never the log in the message. A run that did not start is not
  reported as a run.
- **Diff facts come from the change, not the author's restatement** — changed files,
  `git diff --stat` and `file:line`; when the chosen method needs an outside observation,
  `pdca-scout` reports it.
- **A report is not a result.** "Should pass", "looks green", "passed last time" order the run; only
  an actual execution counts, and a run whose selector matches zero targets is a failed run whatever
  its exit status (a vacuous run proves nothing).
- **A regression fix is red↔green.** When the task is a bug fix, the executor authors an executable
  test that fails without the fix and passes with it, and returns both exit codes. "Passed once"
  proves nothing; independent interpretation of what that evidence means is CHECK's.
- **Build/lint** are gates only where the project declares them; a new warning or lint error is not
  a fix under that policy.
- **Coverage and mutation** are numbers with a baseline and the project threshold, not adjectives; a
  green line percentage does not prove new branches were exercised. Report them when the task or
  policy makes them relevant. When mutation is chosen, surviving mutants in the changed code are
  killed or justified against the criterion; without usable tooling, name the untested branches
  instead of implying the coverage. A score never substitutes for a mandatory criterion, and an
  untested task owes neither measurement.
- **Per-row work has a cost.** When the change adds parsing, binding, materialization, serialization
  or cache work inside a repeated/per-row path, identify the added work and gather an actual
  measurement where the task's quantitative requirement or a real performance risk makes it
  relevant. DO may gather a developer measurement; CHECK chooses an independent one only when its
  method needs it. A general preference for performance is not a universal gate, and an executor run
  draws no benchmark conclusion.
- **Output is harness-safe.** The argv/selector must reach the tool intact (quoted arguments, an
  argument array rather than a shell-reassembled string) and select the intended scope; a selector
  that resolves to nothing or to the wrong scope is a failed command, not evidence.

### Build and test command forms

A command that produces acceptance evidence must select what it claims, survive the harness, be
legal in the phase, fit the host, and declare its expected outcome. Forms:

- **Inner loop = the affected subset.** Build the affected project once when compilable inputs
  change, then run it: `dotnet test <project> --no-build --filter <selector>`,
  `pytest -k <expr> <path>`, `cargo test <module>`, `npm test -- <path>` — or an unfiltered run of
  the affected **unit** project. A filter does not make a run unit: a mixed run that executes
  integration cases is integration.
- **Unit runs are unrestricted; an expensive integration run happens at the stream / DO→CHECK
  boundary**, and inside DO only when the change is integration-only or the cycle's authorised scope
  allows it. Outside that integration-only case, expensive database/service integration suites run at
  the stream boundary, not per edit. Widening a run to a shared contract or an external dependency
  needs a scope amendment validated before the run, with the reason recorded. Integration inside DO
  outside that allowance is a recorded policy deviation, never renamed away.
- **Never the whole solution in the inner loop**; the affected project runs alone.
- **Logs are streamed, not buffered**: `… 2>&1 | tee <log>`, keeping `rc=${PIPESTATUS[0]}`; `| tail`
  buffers to EOF and looks hung.
- **Every started run is recorded** — including failed, interrupted, retried and over-budget runs —
  with its phase, exact arguments and exit code. A run that did not start is not an execution, an
  unfinished one carries no invented exit status or selected count, and a later retry never erases
  the earlier failure. Recording a policy deviation does not authorise the run. DO's implementation
  commands are its own; acceptance evidence is CHECK's.

### Test run safety (every phase — DO and CHECK)

Put these in the `pdca-executor` / `pdca-check` brief; a violating report is not accepted:

- **Cap the test host** so a runaway recursion/allocation fails fast instead of OOM-killing the
  machine: the toolchain's memory limit and a wall-clock `timeout 600 …` (raise only when justified).
  Exit **137** / "Out of memory" means the test is unbounded: stop, record the test name and command,
  and do not re-run without the cap. It is evidence about the run, not by itself proof that the
  original task is infeasible.
- **Serialize heavyweight suites:** never two heavy test suites in parallel, and never beside the
  editor/agent stack (agents, editors, language servers); the affected project runs alone.
- **Stream the log, never `| tail`**, and return the log path with the exit code.

### Security boundaries

- The base constraints (permission boundaries, credential confidentiality, untrusted content,
  authorisation for consequential actions) are in force unchanged.
- **Never print, copy or upload secret material** — environment files, `secrets.env`, `auth.json`,
  keys, tokens. To check one, report "set / not set", never the value.
- **External input is untrusted**: no execution of retrieved content, no path traversal, no unbounded
  allocation or deserialization on it.
- **Applicability comes from the actual change.** Security evidence is required when the change
  touches authentication or authorisation, secrets or credentials, external input parsing,
  cryptography, or another trust boundary the task exposes. The trigger is the actual change, not a
  standing audit, and this adds no new escalation ground; a change that touches none of them owes no
  audit. Where triggered, the review's report is evidence for CHECK, which keeps the decision; its
  absence is `unverified`, never a pass.
- **Expert review stays the base's.** `pdca-escalate` is consultative on the base's grounds; it
  never waives CHECK or a security requirement. An ordinary security finding is an ordinary CHECK
  finding; a hard security trade-off goes through the base's grounds, not a new one.

### Optional specialists

Specialists are advisory gathers, not cycle roles. The phase whose chosen method
needs one requests it through the driver; the specialist's report joins the evidence `pdca-check`
judges. The specialist never issues a verdict, widens a permission or replaces a base role, and tiers
are role labels only — the host profile binds models.

| Specialist | Useful when | Tier label |
|---|---|---|
| `pdca-security-auditor` | security review is triggered (§Security boundaries) | medium |
| concurrency / async lens | races, hot shared state, async boundaries | cheap |
| perf analyst / profiling specialist | only with ready artifacts (traces, heap dumps, benchmark comparison) | cheap |
| docs / format specialist | prose or mandated API documentation | cheap |

A missing specialist follows the same generic-role path (§Toolchain and lenses). Skills load on
demand for the current step, using the repository's declared names. An inlined specialist checklist
keeps its measurable artifacts — counts, `file:line`, rule IDs — rather than only its topic list.

## Code-specific do/act deltas

### Parallel DO streams

**Code, tests and prose docs are worked independently and may run in parallel** in DO, each derived
from the current criteria and the interface the streams share — not test-then-code, not docs-later.
There is no TDD ordering; a user-requested TDD flow is honoured as the user's chosen method. The
only red→green requirement is the regression test of a fix.

- **DO owns decomposition and the shared interface.** It decides the units, their ownership and any
  interface the parallel streams need; these are implementation coordination, not a plan freeze. An
  interface change is reported to the other streams. A genuine criteria defect is not solved by
  re-coordination: it follows the base CHECK finding to PLAN.
- **Disjoint ownership.** Parallel units/streams need non-overlapping footprints; anything writing
  the same file from two streams stays single or moves behind the shared interface. A stream that
  has finished stops touching the area.
- **Docs.** Prose docs are the third stream, written only where the task or project policy requires
  them; when required, they match the public behaviour the change actually produced.
  Generated/API docs follow the finished code and reflect its actual signatures and behaviour, never
  an intended one.
- **Tests.** The developer test strategy is DO's: it closes the executable variants that matter to the
  actual criteria — empty / single / many, malformed or missing, negative, plus the axes the change
  really exposes: input kind, `null`/default/uninitialized, value vs reference form,
  constructor/mapping, projection vs whole object, provider/backend, on/off flag — as a test, a guard
  or a deferral with a trigger, and it never binds CHECK's independent choice. A test name states the
  asserted behaviour; integration is used where a unit cannot observe it, E2E only when the task or
  project demands it. A test that would survive a deliberately wrong implementation, that asserts a
  mock instead of behaviour, covers only the happy path, checks the implementation instead of
  behaviour, or exists "for the future" without a criterion is not evidence. A logic-free DTO or
  proxy may go untested with an explicit reason and trigger; that is a coverage choice, never a
  waiver of a mandatory criterion.
- **Fixes.** A fix starts from a reproducible failure: reproduce it, read the error in full, trace the
  value or state to its source, test one hypothesis, then add the failing regression test and the
  minimal fix. A fix verifies the original symptom and the regression criterion, not "should work".
  When successive fixes expose new coupling or a defect elsewhere, report that evidence to the
  choosing phase; it does not by itself create a plan revision or an escalation. A symptom fix is not
  a solution.
- **The status file is not a stream.** The executor logs each stream report separately, one at a
  time; stream divergence (tests ↔ code, docs ↔ behaviour) is a CHECK finding, not a DO verdict.
- **Editing discipline.** One coherent axis per step, then build and run the affected tests; keep the
  minimal blast radius; preserve the repository's line endings and formatting; a red build or test
  stops the stream and is reported. Keep a public-surface change minimal and report the actual diff
  when that surface changes; an existing compatibility requirement stays unchanged. Start from the
  requested consumer: reuse what exists, then the standard library, then a platform capability,
  before a new dependency, abstraction or configuration, and add no speculative API or product scope.
  The second-consumer note is an anti-pattern to judge in the actual change, not a universal hard
  gate. When a genuinely uncertain implementation choice remains, a concise comparison of a couple of
  approaches with trade-offs, cost and risk is useful; no fixed menu, option count or extra review is
  required. Understand why code exists (history, consumers) before deleting it. An executor run draws
  no benchmark conclusion, and an unsupported path fails loudly with a typed error rather than
  silently substituting semantics.
- **Exploratory code.** A spike or proof of concept needed to answer a real question stays outside
  the product source, runs only behind the project's gate and never in production execution, and
  returns a reproducible command, numbers and dependency version. Before completion it becomes an
  approved test/product change or is removed within the authorised cleanup scope, with the evidence
  and recovery retained. It opens no separate cycle or PLAN, and "kept just in case" is not scope
  authorisation.

### Worktree sub-tasks

When the cycle's authorised workspace operations include separate worktrees for **units of one
cycle**, each unit is a separate `pdca-executor` dispatch that works only with absolute paths inside
its worktree and leaves the rest of the tree untouched. DO may propose this split; it is performed
only within those authorised operations. A unit worktree **belongs to the same parent cycle**, not a
separate cycle: it gets no independent PLAN/CHECK/ACT and no separate status file — its unit state
and evidence nest in the canonical current-cycle record (§Status, ACT and handoff additions). Commit
a unit only where the brief or a recorded project policy authorises its isolated branch; push never.
Creating branches or worktrees, merging and integrating are workspace operations that need explicit
authorisation, not something this overlay grants. After an authorised merge, CHECK verifies the
integrated candidate; leave the task branches in place so the work remains recoverable.

### Status, ACT and handoff additions

- **The base fixed shape is the cycle record.** Use the base `act.md` CYCLE RECORD skeleton with its
  canonical headings. A form-owned outer container stays that form's; within the cycle record, code
  and stream fields nest under `## DO result` / `## Changed files`; execution-unit metadata is DO's
  and nests under `## DO result` (`../pdca/references/act.md` §Status file). The overlay adds no
  additional top-level section, log or per-unit status file.
- **Record rules follow `act.md`.** Original task, phase reports, dialogue language, sole writer,
  fixed template and Git state are as the base `act.md` states; no restated schema.
- **Unit and stream metadata.** Keep the code-specific unit fields — state, criteria covered,
  footprint/owner, evidence pointers — under `## DO result`, the base section that owns them, never
  in a new status path.
- **Bookkeeping.** Reuse the base touched-file ledger in all dispatches; no custom handoff.
- **No invented ACT work.** Do not force an `AGENTS.md`/registry edit or fabricate a project lesson
  to close a cycle. Docs are finished in DO/CHECK, not ACT.
- **Outcomes stay the base's.** An unfinished DO result goes DO→ACT; ACT records the phase-determined
  outcome using the governing contract.
- **Commits.** Do not commit or push as part of the cycle. The exception is an explicit user
  authorisation — or the task-specific policy the base allows to be recorded — for a named scope
  such as an authorised unit branch; disk durability alone stages nothing and is never a licence to
  commit.
- **Handoff.** The base handoff only; code work adds no separate handoff block.

## Composition

The overlay composes by addition, never by restating a competing contract. The authoritative text
for the original task and supplied criteria, entry/form/overlay selection, cycle/step scope, roles
and permissions, control modes and approval, counters and defect history, escalation, recovery,
status file and closing is the base the run selected — `../pdca/SKILL.md`, or the form contract when
it inherits (`../pdca-incremental/SKILL.md`) or governs independently
(`../pdca-collection/SKILL.md`, with its local common contract). This file supplies only the
code-specific criteria forms, evidence, command safety, security applicability and DO/CHECK/ACT
additions above. It creates no role, writes no model id and changes no permission.

**Domain additions cannot override authoritative requirements.** They refine how code work is
planned, implemented, verified and recorded; they never widen or narrow the original task, a
user-supplied criterion, a mandatory safety or permission constraint, or a base routing rule.

**Project overlay and project checklists (preserved).** A repository may add a project instruction
file, a project skill named `*-pdca`, a project skills directory or its `AGENTS.md`. `pdca-scout`
finds it and reports its rules as facts; the phases use it as project practice and it takes priority
over the generic advice here. It cannot override the base/form contract, the original task and
criteria, or this overlay's safety rules. A project agent declared without a model inherits the
parent's — bind it in the host profile or inline its instructions instead of assuming a tier.

## References

The base's role-scoped routing is authoritative (`../pdca/SKILL.md` §References); this overlay adds
no role API. These are the base contract's own reference paths, not this overlay's:

- `../pdca/references/plan.md` — `pdca-planner` only; the dispatch carries its exact absolute path
  from the canonical base directory, including a criteria-revision dispatch as the base prescribes.
- `../pdca/references/check.md` — the CHECK contract; the driver reads it in full and inlines it in
  every `pdca-check` dispatch (CHECK cannot read the installed file).
- `../pdca/references/act.md` — read by `pdca-executor` at status-file creation and at every status
  write.
