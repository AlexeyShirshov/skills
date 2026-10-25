# `pdca-coder`: the engineering cycle that cannot be closed without verification

## The problem: whose assessment is "done"?

An agent's ordinary work on an engineering task looks like a sequence of actions: read the code,
fix it, run it, say "done". That sequence has three weak spots. It is unclear what counted as
success: the criterion was not stated in advance, and "done" is the author's self-assessment, not a
verified fact. State lives in the session context: after context compaction or in a new session the
agent does not remember where it is, what has already been done and why. And mistakes cost nothing:
if something did not work, it can "try again" endlessly without changing its approach.

`pdca-coder` is a skill (a pluggable behaviour contract) — the family's **programming overlay** — that
replaces such a sequence with a **cycle with a verifiable result**: PLAN → DO → CHECK → ACT, with
explicit gates. It contains only its differences from the base: no PLAN of its own, no state machine,
no second status file, no separate routing branch. It is applied **to** the form the base PLAN chose —
an ordinary cycle, an incremental step, the relevant items of a collection — and adds engineering
facts to it. A gate is a condition under which the next step is allowed; it checks the *presence* of
the mandatory items,
not their quality. The skill is made for software-engineering tasks of any stack: writing and
changing code, tests, documentation, refactoring, configuration. Its key property is
**stack-agnosticism**: the skill does not dictate a specific language, compiler or framework; PLAN
chooses the toolchain (build, tests, lint) and the verification lenses for the specific task, while
the project overlay supplies the concrete commands, thresholds and formats. A "lens" is a
verification perspective (a set of rules and a focus), for which an agent or an explicit general
path is selected.

The cycle does not turn itself on. Until the skill is loaded, the contract does not apply and an
ordinary task is performed directly. `pdca-coder` is worth picking where the result must be
*proven*: a behaviour change, new functionality, a fix with a regression test, a config change with
verification. The value of the skill is not that it guarantees the right result (a gate is an
admission condition, not a promise of quality), but that it does not let you close work without
verification, lose state, or pass off identical retries as progress.

## Launching: the entry, or the explicit overlay

"By the cycle", "via PDCA", "run PDCA" load the family's single entry — `pdca`. Its one PLAN picks the
form and, for code work, the overlay: naming `pdca-coder` explicitly only makes that choice a
constraint. The overlay is not a cycle of its own, so it always runs on top of the base
([`skills/pdca/SKILL.md`](../skills/pdca/SKILL.md)); naming `pdca-dotnet` selects the .NET overlay,
which **inherits** this one and adds .NET specifics and .NET gates — that is not `pdca-coder` alone.

There are two modes. In **normal** mode the cycle is interactive. First the plan is written into the
status file on disk (the source of truth on the cycle), then the orchestrator states that the plan
is ready and recorded — and only after the user **reads and approves** the plan does execution
begin; a question, a request to change the plan or an optional reply does not count as a start. In
**autonomous** mode (the user has explicitly asked to
work without questions) there are no pauses: transitions happen in the same turn in which the gate
is passed, and all communication goes into the status file as `Notice:` marks. Autonomy reduces
questions but **does not expand permissions** and does not cancel the mandatory gate items.

## Who is in the cycle: roles and tiers

A role in the cycle is a function, not a person and not a specific model. The skill names only
**roles**; the host (the run environment) binds them to agents and models, and a model id never
enters a role definition — a role carries only a `# tier:` label. The economics are built on
separating cost from quality: that is why roles are marked with **tiers** — labels of
cost/quality, not of authority:

- **`pdca-scout`** — fact gathering, read-only, the cheap tier; it returns references of the form
  `file:line` and URLs, with no recommendations.
- **`pdca-executor`** — the cycle's "hands", the cheap tier; it is allowed file edits and commands. Every
  write and every run in the cycle goes through it.
- **`pdca-planner`** — decisions and decomposition, the medium tier; it only reads the summary and
  draws up the plan.
- **`pdca-check`** — the verdict, the medium tier; it judges candidates and renders `pass/fail`, a
  return, or a new attempt.
- **`pdca-security-auditor`** — security audit, the medium tier, engaged by trigger (if the change
  touches authentication, secrets, external input, cryptography).
- **`pdca-escalate`** — escalation of hard decisions, the strong tier, called rarely and by triggers: an
  ambiguous criterion, an exhausted attempt counter, an architectural or cryptographic trade-off
  with long-lasting consequences.

Only a cheap-tier primary drives the cycle — by the **host profile's effective tier**, not by the
agent's name; a medium or strong primary does not conduct the cycle and outside the cycle remains
the deciding primary. The ready-made role assets (`assets/opencode-agents/*.md`) carry explicit
permissions as well: `pdca-scout` has bash only via an allowlist of read-only commands,
`pdca-executor` has `edit`/`bash`, `pdca-check` has default-deny (except a scoped read of the cycle's
artifacts), and `pdca-escalate` and `pdca-security-auditor` have `doom_loop: ask`.

Required roles are not substituted. An absent or forbidden required role is a **resource blocker**,
not a reason to fall back to built-in `general`/`explore` or to work silently without it. A host that
has **forbidden** a role must not be bypassed. The only permitted fallback is the driver: if
`pdca-orchestrator` is unavailable, the flat cheap primary drives the cycle and records a `Notice:`.
Optional specialist lenses may use an explicit generic-role path, which is not a substitute for a
required role.

## How `pdca-coder` differs from the base cycle

The base PDCA cycle is domain-neutral. `pdca-coder` adds engineering concreteness to it, and only
that: the base goals, gates, counters, claims and safety stay in force unchanged.

**Three DO streams run at the same time.** This is the main difference. Code, tests and prose
documentation (README, guides) are written **in parallel**, right after the plan, not sequentially.
The contract explicitly forbids both "code first, tests later" and "docs later": no TDD order is
used in DO, and the only "red → green" requirement applies to a regression test for a bug fix.
Each stream depends **only on the plan** (and, if needed, on a frozen shared contract — signatures
and types without implementations). If tests and docs need a shared abstraction or DTO, first only
the contract is fixed and frozen: only PLAN may change it. A file that different streams write to
is not parallelized — it moves into the contract, or the task stays single-streamed. Generated and
API docs (comments such as XML-doc) are the exception: they live in the same files as the code, so
they are written **after** the code stream. The result: all three sides are derived from the plan
and do not wait for one another.

**PLAN chooses the toolchain and the lenses.** Since the skill is stack-agnostic, PLAN must, for
each specific task, determine the type of result; find the build/test/lint toolchain declared in the
project through `pdca-scout`; choose the appropriate correctness lenses; bind each lens to an available
agent or an explicit general path; and **freeze** that choice together with the evidence each lens
must return. A missing optional lens is replaced by an explicit general path, not silently dropped.
Gate 1 (PLAN → DO) checks that this choice is written down together with the acceptance criteria,
the testing strategy, the documentation plan, and reasoned decisions on performance measurement,
reconnaissance and the unit execution mode. Re-entry is stipulated separately: after a terminal
`incomplete`/STOP, the previous terminal cause is a mandatory plan input, and a criterion whose
evidence failed cannot be re-run unchanged — either it is proven to be reachable now, or the
criterion is reformulated against a reproducible oracle.

**The plan close is shared with the base cycle.** Gate 1 also requires every **frozen command** to
pass the plan command contract: the identifier resolves to at least one target in the declared
scope, the argv survives the harness (no shell alias, redirection or unexpanded placeholder), the
phase is legal (a boundary-only sweep is not inner work), the scope fits the declared budget, and
the expected outcome is `green`, `expected-negative` or `informational`. A violation is a **plan
defect**, not a runtime exception. The gate also fixes a **stop-loss budget** (revisions, wall
clock, measurement time); a run that selects zero targets is a failure whatever its exit code, and
a decisive negative arm is declared `expected-negative` with its exact failure identity. Recorded
exceptions come from a fixed catalog — a class appearing in three or more units of one campaign is
systemic. On DO entry the executor re-resolves the plan's anchors before the first edit: cosmetic
drift is a `Notice`, semantic drift is DO → PLAN.

**CHECK in two beats and parallel streams.** Verification does not mix fact gathering with
judging. First the cheap **gathering**: the mechanics — commands through `pdca-executor` (build and lint
clean under the project's policy), the semantics — code lenses (raw `file:line` candidates + a rule
id, no verdict), tests, documentation, performance; then the **triage** — `pdca-check` on the medium
tier renders the verdict. The gathered evidence converges into a single machine-readable **evidence
manifest**: DO writes it at the path fixed in the plan and freezes it at the DO→CHECK boundary; in
CHECK the manifest is only appended to, and `pass` is forbidden while even one mandatory item is
open **and binding**. A self-imposed extra *audit* row that follows from no agreed goal is not
rewritten or dropped: CHECK returns an explicit append instruction for it in the same manifest; the
executor writes it and CHECK reconciles the result (a stable row ID plus the
`diagnostic_nonbinding` classification and a reason), so the row may stay `open` while
it is excluded from the binding blockers, with binding unmet rows and audit notes reported
separately. `pdca-check` reads the aggregated report and may open the cycle's artifacts directly — a scoped
read of the status, the evidence and the manifest, but never the product's code. Four streams are
unconditional: code audit, tests, documentation, performance; the fifth — the security audit — is
conditional and engaged by trigger, and its report returns into the common verdict rather than
being rendered separately. Any stream failure of the current revision, including a security hit,
counts as a failed CHECK for the attempt counter; only a hard security trade-off is escalated
immediately. Independently green branches of work do not combine automatically: if subtasks were
carried out in separate worktrees (isolated working copies of git), CHECK is supplemented by two
mandatory steps — merging the branches into a common tree and **re-verifying the merged code**. Any
CHECK stream failure becomes a `D:` task (a DO stream item) for `pdca-executor` or a return to the plan,
and does not cancel the other streams.

**A project overlay on top of this one.** A repository may add its own cycle rules: a file in
`instructions`, a project skill `*-pdca`, or `.opencode/skills/<name>/SKILL.md`. Such a project
overlay refines invariants,
finding registries, report formats and thresholds, and takes precedence over the general
recommendation, but **does not cancel** the state machine and the gates — the plan approval, "everything green",
returns, autonomous mode. Before PLAN, `pdca-scout` looks for such an overlay and brings back its rules.

## A teaching scenario (an illustration, not a rule)

> **Note:** this is a fictional example explaining the mechanics. It is not part of the contract
> and does not describe a real repository.

Task: add to a console utility a `--strict` flag that exits the process with a non-zero code if
there were warnings while parsing the config.

**PLAN.** `pdca-scout` finds the test and lint commands declared in the project. `pdca-planner` formulates the
goal and the acceptance criteria with negative cases: without the flag, warnings do not change the
exit code; with the flag, they do; an empty config does not crash. A matrix of variants is built
(each row is closed as a test, a guard check, or deferred with a trigger): a config with no
warnings, with one, with several, a missing file. Lenses are chosen: correctness and error
handling, CLI/UX, security — if an untrusted file is read. Performance decision: not needed, the
work is not on a line-by-line hot path, with `file:line` given. Documentation decision: update the
README and the guide section. `pdca-executor` writes the plan into the status file. After the approval, DO begins.

**DO.** Three streams start in one turn: the code adds the flag and changes the exit code; the tests
write the cases from the matrix; the prose docs describe the flag. All three rely only on the plan.
Generated API docs, if the project requires them, are added after the code stream.

**CHECK.** Four streams gather evidence: the build/lint commands (exit code, log path), the test
lens (a run, coverage against the project threshold, a branch report, not just lines), the
documentation lens (the README is created and matches the implementation), the performance lens
(confirmation that the path is not line-by-line). `pdca-check` finds that one negative case from the
matrix is not covered and returns a `D:` for `pdca-executor`. After the fix the streams are re-gathered and
the verdict turns green.

**ACT.** The skill records 0–2 transferable lessons into memory (optional; no lesson is a normal
outcome), updates `AGENTS.md`/registries/tests, finalizes and **keeps** the status file, and in
normal mode prints a message for the next session. The status file is never deleted — it remains
either as a baton to the next session or as a closed record.

## Limitations and false expectations

**Commit and push.** The cycle does not commit or push on its own initiative. The only mechanical
exception is the worktree mode: each unit commits into its own isolated `pdca/<task>` branch inside
its worktree; this is an isolation mechanism that the merge in CHECK relies on, not a delivery.
Commits into the working branch are made only on explicit request (for example, an autonomous
auto-commit); push — never without a separate explicit request.

**Autonomy does not expand permissions.** The absence of questions is not a permission. An
unavailable mandatory role, a secret, an irreversible external action or a step requiring approval
is a blocker or a STOP, not a silent pass.

**Test-run safety.** Any test run in DO or CHECK limits the test host's resources: a memory limit
and `timeout 600` by wall-clock are set so that unbounded recursion or allocation fails fast rather
than destroying the machine. Heavy suites (integration ones with a real database/broker/HTTP) are
serialized: never two heavy runs in parallel, and never next to the editor or the agent harness. A
long run is **streamed to a log** rather than through `| tail`, which buffers until end of file and
looks like a hang; the output always includes both the exit code and the log path. An exit of `137`
/ "Out of memory" means the test is unbounded: it is stopped and recorded.

**What the cycle does not guarantee.** Gates constrain the permitted actions but do not make a plan
correct and do not replace domain expertise. Something else is guaranteed: without explicit
verification the work will not close, state will not be lost silently, and identical retries will
not be passed off as progress. Fresh evidence is mandatory: a verdict without numbers, `file:line`
and a baseline does not count as a pass, and the executor's report "done, the build is green" is
not proof.

## Where to go next

If the task is an engineering one with a verifiable result, start with "by the cycle" — it loads the
family's single entry, `pdca`, and lets the one PLAN formulate the criteria before anything is
written; code work then gets this overlay. If the task is purely .NET/C#, see the related
[`pdca-dotnet`](pdca-dotnet.md) (it inherits `pdca-coder`); if the result is not about code, the
family's base [`pdca`](pdca.md) runs without an overlay; if there are many independent goals —
[`pdca-collection`](pdca-collection.md); if the method or the volume is unknown —
[`pdca-incremental`](pdca-incremental.md).
The family's common mechanics — gates, the `N`/`r`/`n/3` counters, memory and evidence — are
covered in the article about the base [`pdca`](pdca.md); the full text of the contract
lives in [`skills/pdca-coder/SKILL.md`](../skills/pdca-coder/SKILL.md), and an overview of the
whole family is in the guide [`docs/pdca-guide.md`](pdca-guide.md).

## Sources

The "claim → source" map. The article's normative claims were reconciled with the current
files (`skills/pdca/SKILL.md`, `skills/pdca/references/*.md`, `skills/pdca-coder/SKILL.md` and its
`references/`); where they disagree, the skill file takes
precedence. The paths are given from this repository; the host artifacts (`config/agents/*.md`,
`config/profiles/*.jsonc`, `config/AGENTS.md`) are not part of it and live in a separate
configuration repository.

| Claim | Source |
|---|---|
| Stack-agnosticism: code, tests, documentation, refactoring, configuration; the choice of toolchain and lenses belongs to PLAN | `skills/pdca-coder/SKILL.md §When it applies · §Toolchain and lenses` |
| The contract applies only with the skill loaded; a gate checks the presence of items, not their quality | `skills/pdca/SKILL.md:8-9 · §Transition gates` |
| Roles, tiers and economics (cheap / medium / strong) | `skills/pdca/SKILL.md §Roles and host requirements` |
| The host defines the roles; only a `# tier:` label, no `model:` is written into a role | `skills/pdca/SKILL.md §Roles and host requirements` |
| Only a cheap-tier primary drives the cycle (by the profile's effective tier) | `skills/pdca/SKILL.md §Roles and host requirements` |
| The role table, the fallback to `explore`/`general`; an unavailable role is a resource blocker | `skills/pdca/SKILL.md §Roles and host requirements` |
| The project overlay and its boundaries (it does not cancel the gates or the state machine) | `skills/pdca-coder/SKILL.md §Composition` |
| State: the status file is the source of truth and the only progress mirror | `skills/pdca/SKILL.md §Phase progress mirror · §Workspace and durable status` |
| The three counters `N`, `r`, `n/3` | `skills/pdca/SKILL.md §State machine and counters` |
| Gates 1–4 (PLAN → DO → CHECK → ACT) | `skills/pdca/SKILL.md §Transition gates` |
| The plan command contract, vacuous/`expected-negative` runs, the exception catalog, DO-entry re-anchoring and the stop-loss budget | `skills/pdca/references/plan.md §Plan command contract (PLAN close) · §Vacuous and expected-negative runs · §Recorded exceptions: catalog and repetition threshold · §Re-anchoring at DO entry · §Proportional planning and stop-loss` |
| The `DO → PLAN` candidate, an additive precondition vs a scope replacement, unit states | `skills/pdca/SKILL.md §DO → PLAN candidate · §Phase contracts (generic)` |
| Re-entry after a terminal `incomplete`/STOP | `skills/pdca-coder/references/plan.md §Re-entry after a terminal \`incomplete\` / STOP`; `skills/pdca/SKILL.md §Phase contracts (generic)` |
| The three parallel DO streams (code ∥ tests ∥ prose docs), the frozen shared contract | `skills/pdca-coder/SKILL.md §Parallel DO streams (code + tests + prose docs)` |
| Generated/API docs — after the code stream | `skills/pdca-coder/SKILL.md §Parallel DO streams (code + tests + prose docs)` |
| The editing discipline of `pdca-executor`; the ban on commit/push except `pdca/<task>` branches in a worktree | `skills/pdca-coder/references/act.md §Coder editing discipline (applying fixes)`; `skills/pdca-coder/SKILL.md §Worktree sub-tasks` |
| The subagent report format (pointers, not dumps) | `skills/pdca-coder/references/act.md §Subagent report format (mandatory)` |
| The worktree subtask template, the `pdca/<task>` branch, the push ban | `skills/pdca-coder/references/act.md §Worktree sub-tasks of one cycle: subagent prompt template` |
| Escalation: triggers, no 4th attempt, decision routing | `skills/pdca/SKILL.md §Escalation (pdca-escalate)` |
| PLAN chooses the toolchain and lenses; freezing the choice and the evidence | `skills/pdca-coder/SKILL.md §Toolchain and lenses` |
| Plan quality, the minimal solution, the matrix of variants | `skills/pdca-coder/references/plan.md §PLAN owns the quality of the plan · §Minimal solution and first principles · §Variant/branch matrix — mandatory, before the cases` |
| The unit execution mode (sequential / parallel one tree / worktrees) | `skills/pdca-coder/references/plan.md §Unit execution mode (mandatory decision)` |
| Performance and reconnaissance — mandatory reasoned decisions | `skills/pdca-coder/references/plan.md §Performance measurement (mandatory decision) · §Prototype / reconnaissance (spike) — mandatory decision` |
| The plan goes to disk before approval; the user's approval of the plan is the only start signal | `skills/pdca/SKILL.md §Normal-mode approval` |
| The testing strategy, the matrix of variants, coverage/branches/mutations | `skills/pdca-coder/references/plan.md §Test strategy (PLAN → TEST) · §Variant/branch matrix — mandatory, before the cases · §Coverage comes from the project, mandatory` |
| Test-run safety (limits, timeout, serialization, streamed log) | `skills/pdca-coder/SKILL.md §Test run safety (every phase — DO and CHECK)` |
| Documentation: prose vs generated, owners by phase | `skills/pdca-coder/references/plan.md §Documentation (owners by phase)` |
| The frozen evidence manifest; CHECK reads it first | `skills/pdca/references/plan.md §Frozen evidence manifest` |
| CHECK in two beats; `pdca-check` may read the cycle's artifacts (scoped read, not the product's code) | `skills/pdca-coder/references/check.md §Two beats`; `skills/pdca/SKILL.md:19-24` |
| Four unconditional streams + security by trigger; a failure is a `D:` or a return to the plan | `skills/pdca-coder/references/check.md §Parallel CHECK streams (code audit + test + doc + perf + security*)` |
| "No numbers — no pass": a verdict without numbers/`file:line` is a fail; a report ≠ a result | `skills/pdca/references/check.md §Findings · §Verdict and routing`; `skills/pdca/SKILL.md §Evidence over assertion` |
| Worktrees: merging and re-verifying the merged tree | `skills/pdca-coder/references/check.md §Parallel sub-tasks in worktrees (within one cycle)` |
| Debugging: cause before the fix, a red↔green regression test | `skills/pdca-coder/references/act.md §Debugging (loop-back CHECK → DO)` |
| ACT: memory (0–2), AGENTS.md/registries, finalizing the status file, the session message | `skills/pdca-coder/references/act.md §Status-file additions (code) · §Handoff additions (code)`; `skills/pdca/references/act.md §Closing order · §Message for the next session` |
| Commit policy: no commit/push from the cycle except the worktree unit branch; commit to the working branch only on request | `skills/pdca-coder/SKILL.md §Status, ACT and handoff additions` |
| Autonomy does not expand permissions; instruction priority, injections, secrets | `skills/pdca/SKILL.md §Generic operating constraints` |

Additionally: the phrase triggers are a launch convention, not a contract rule; in this repository
they are fixed by `README.md` (the Usage section), while `SKILL.md` itself does not formulate a
phrase trigger. The teaching scenario is marked as such in the text and creates no rules.
