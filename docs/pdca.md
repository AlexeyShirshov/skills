# `pdca`: the cycle that carries a task to a verifiable result

## Why the cycle exists and when to pick `pdca`

An assistant's ordinary work is a sequence of actions: read, fix, run, say "done". It has three
holes. It is unclear what counted as success: the criterion was not stated in advance, and "done"
is the author's self-assessment, not a verified fact. State lives in the session context. After
compaction (the host compresses the context) or in a new session the assistant does not remember
where it is, what was done and why. And mistakes go unpunished: a failure does not stop it from
"trying again" the same way.

The `pdca` skill replaces the sequence with a **path to a verifiable result**. The idea is borrowed
from the management cycle Plan — Do — Check — Act: plan, do, verify independently, finish — or
return to the plan. In the contract this is a state machine with **gates**: a gate is a condition
under which the next step is allowed. A gate checks the **presence** of the required items, not
quality. The promise is modest: the cycle does not guarantee the right result in the real world,
but it does not let you close work without verification, silently lose state, or pass off identical
retries as progress.

![Diagram of the domain-neutral pdca cycle: phase inputs, roles by tier, state graph](../opencode/pdca/assets/diagram/pdca-hand-dark-en.svg)

`pdca` is a **domain-neutral** skill: it names only **roles** and **phases** and imposes neither
artifacts, nor task types, nor domain examples. What the result will be — a report, a document, a
config, a plan — is decided by the planning phase; that phase also chooses the way to verify it.
So `pdca` is worth picking for a task with a **verifiable result**: you can name the success
criteria and the way to check them in advance.

Separately: `pdca` does not turn itself on — without an explicit invocation the contract does not
apply. And it is not the only option: `pdca`, `pdca-coder` and `pdca-dotnet` are three variants of
one cycle with different levels of concreteness, while `pdca-collection` sits **above** the cycle:
it coordinates several cycles and does not redefine the state machine. `pdca` sets the common core;
the neighbouring variants are described in the neighbouring articles. If the cycle is launched as a
collection task's PLAN, it stops at the **PLAN → DO** boundary and returns control to the
collection parent as a `plan_handoff` — same task, same `N`/`r`/`n`, DO does not start.

## How to launch it: explicitly and by name only

`pdca` has **no phrase trigger of its own**. It is invoked explicitly by name — with a command like
`skill pdca`; this is how it differs from `pdca-coder` (the phrases "by the cycle", "via PDCA", "по
pdca") and `pdca-dotnet` (the phrase "по pdca-dotnet"). The domain-neutral `pdca` is the family's
"reference": it stays with whoever named it deliberately, and it does not redefine other skills'
triggers.

## Who does what work

The cycle has a fixed set of **roles**. A role is not a person and not a specific model, but a
function with permissions. A **tier** (cheap / medium / strong) is a label for a model's cost and
quality, **not** an authority: a cheap role can have more permissions than an expensive one. The
host binds specific agents and models; the skill names only roles.

| Role | What it does | Agent of the domain-neutral `pdca` | Tier |
|---|---|---|---|
| GATHER — fact gathering | Collects `file:line` pointers, URLs, numbers; no recommendations | `scout` | cheap |
| PLAN — decisions | Goal, acceptance criteria, decomposition, risks, verification method | `pdca-planner` | medium |
| DO — hands | Edits files, runs commands, keeps the status file (the cycle's state on disk) | `pdca-executor` | cheap |
| CHECK — verdict | Independently verifies every criterion against actual evidence | `pdca-check` | medium |
| ESCALATE | The second tier for hard decisions | `pdca-escalate` | strong |
| RUNNER — orchestrator | Drives the cycle, reading and editing nothing | `pdca-orchestrator` | cheap |

A few rules keep the table working. **The orchestrator is a dispatcher, not a reader and not a
decision maker**: it dispatches the roles to subagents and passes their reports to one another, but it
does not write the plan, read files or run commands. **PLAN always belongs to the planner**: both
the initial plan and a revision are formulated by `pdca-planner`. **Only the executor may write
and run**, including the status file.
**The checker is independent of the author**: it judges by the aggregated report with fresh runs and
facts from `scout`, but it may also **open the cycle's evidence artifacts directly** — the status
file and the manifest with their pointers (scoped `read`), never the product itself. Hence the
prohibition on self-editing, self-reading and self-verdict: the executor does not render a verdict
and does not declare STOP, the checker does not verify its own work, the orchestrator does not
substitute for the roles.

The cycle is driven by the **cheap primary only** (the primary is the main session) — by the
profile's effective tier, not by the agent's name. A medium/strong primary (for example,
`architect`) does not dispatch the cycle. In autonomous mode the cheap primary delegates the whole
cycle to the cheap **`pdca-orchestrator`** agent. `pdca-orchestrator` is **not a
fifth skill** but a driver agent: it loads the chosen variant (`pdca`, `pdca-coder` or
`pdca-dotnet`) and runs one child cycle or one collection group. An unavailable mandatory role is a
**resource blocker**: in normal mode it is reported to the user, in autonomous mode it is written
as `Notice:`; a fallback forbidden by the host is not bypassed. If `pdca-orchestrator` itself is
unavailable, in autonomous mode the cheap primary drives the cycle itself (flat primary fallback)
and records a `Notice:`.

## How the cycle runs

The cycle's state machine looks like this:

```text
PLAN → (normal: the user approves the plan) → DO → CHECK → ACT → (EXIT | PLAN)
                    ▲                      │
                    └──────── DO → PLAN ───┘
```

Plus a separate terminal path, **STOP** — neither a "green" gate nor a successful ACT.

**PLAN.** The planner restores the goal by essence — "what result is needed", not "what action to
perform" — and returns the mandatory fields: goal/expected result, constraints, assumptions,
acceptance criteria **each with a way to verify it**, a decomposition with dependencies or an
explicit decision not to split, means and access, risks and stop conditions. A gap is closed with a
fact, an explicit assumption/risk, or a blocker/escalation; a silent guess is forbidden. A special
case is a criterion whose verification **depends on state** (for example, a negative branch that
holds only from a certain prior state): it must name a **reproducible** source of evidence, and the
decisive run is shown on the declared baseline **before gate 1**; an unprovable criterion is a gap
(report it or redefine the oracle), not a "done" mark. And a return after a terminal
`incomplete`/STOP is also a PLAN entry: a criterion whose evidence failed cannot be re-run
unchanged — either show that it is now obtainable, or redefine the scope.

**DO.** The executor does only what the plan says; a change beyond the unit is "Over-Reach" — a
separate task. The verdict and STOP are not its own: it returns a **preliminary candidate with
evidence**, and the candidate "the result is achieved" never closes the unit — the verdict belongs
to CHECK.

**CHECK.** The checker judges every criterion by actual evidence and checks the consistency of the
parts. Statuses: `met` (satisfied), `unmet` (not satisfied), `unverified` (not verified). A missing
check is not a pass: without numbers and pointers a criterion gets `unverified`, not `met`. The
output is a verdict, a criteria matrix, findings and routing: an implementation defect → DO, a
wrong plan → PLAN.

**ACT.** It completes only a result accepted by the current CHECK: it records conclusions,
constraints, status and handover, and finalizes the status file. Without ACT the cycle cannot be
closed, and without an accepted check there is no ACT; `rework`/`replan` are not part of ACT but
**returns before** it.

**Returns.** `CHECK → DO` — an implementation defect: fix it and verify again. `CHECK → PLAN` — a
wrong plan: the planner issues a new revision. `DO → PLAN` — a new precondition or a blocker: not a
unilateral revision but a candidate for the planner to review. An **additive precondition** (a new
active unit, the original one stays `blocked` with its own criteria, no mapping) differs from a
**scope replacement** (a genuine supersession: `superseded` and a mandatory "superseded →
replacement" mapping covering all the original criteria).

**Five gates** permit the transitions:

1. **Plan → DO:** all mandatory fields are in place, the plan is written into the status file, the
   user **has approved the plan** — or autonomous mode.
2. **DO → CHECK:** all active, non-superseded units are `done` with evidence.
3. **CHECK → ACT:** all criteria are `met` on actual data, none `unmet`/`unverified`.
4. **ACT → EXIT:** the result and the status file are finalized.
5. **STOP:** a separate finalization, outside the series of transitions above.

Two invariants are unbreakable: **CHECK cannot be skipped** and **the cycle cannot be closed
without ACT**.

Progress is counted by **three counters**. `N` is the number of the task's cycle in the file name
`.pdca/status/<task>-<N>.md`; it grows only in ACT, when the next cycle of the same task is
planned. `r` is the plan revision; it grows only for a genuinely different plan. `n/3` is the
execution attempt of the current revision: it starts at 1, `CHECK → DO` increments it, a new
revision resets it to 1. A rejected candidate with an unchanged plan is **not** a revision: `r` and
`n` do not change; renaming or resetting the session does not "produce" a revision. Alongside lives
the **defect history** — one row per stable defect key (revisions/attempts, number of fixes,
pointers, escalation outcome); it is not erased by a revision or a new session. The counters and
the history live in the status file. They help tell "one more attempt" from a revision and call an
escalation in time: **the same defect returning after one fix** is a signal earlier than three
different failures; after the third failed CHECK of one revision there is no fourth attempt.

**Modes.** In **normal** mode, after the plan is written the orchestrator states that the **plan is
ready and recorded in the status file**, gives the path to it and asks you to **read the plan and
approve it** — the **only** start signal. A question, a request to change the plan or a
non-committal reply ("OK" without an approval) does not start; without an approval nothing is
created or edited except the status file. In **autonomous** mode the same contract runs without
pauses or questions: transitions
happen in the same turn in which the gate is passed, nothing "for the user" is printed, and
notifications (an unavailable role, recovery after compaction, an assumption instead of a question)
are written into the status file as `Notice:`. No questions are asked: the unresolvable leads to
STOP.

**Memory and evidence.** The **cycle status file** is the source of truth on the plan and progress.
It lives on disk, survives compaction and a new session, and the executor updates it on every
event. It is the **only** progress mirror: there is no separate todo or sidebar mirror, so a host
that provides no todo tool (V2 does) loses nothing, and a second mirror cannot diverge from it.
After compaction the state is restored from the status file (through
`scout`), not from memory. The cycle closes only on **fresh evidence** — an exit code, numbers, a
log path, `file:line` — and never on an assertion, including subagent reports. Marker words like
"should work", "probably" are a signal to schedule a re-run: **a report ≠ a result**.

DO and CHECK are reconciled by the **frozen evidence manifest**: DO writes it at the DO → CHECK
boundary and ties it to the fixed identity of the result (revision `r` plus the captured
input/artifact), and CHECK reads it **first**. Afterwards the manifest is only appended to, never
rewritten; every mandatory criterion has one row in it with the status `met` / `open` / `na`, and
**while even one mandatory row is `open` *and binding*, no PASS is rendered**. A self-imposed extra
*audit* row that follows from no agreed goal is not rewritten or deleted either: CHECK appends an
explicit disposition to it in the same manifest — a stable row ID and the classification
`diagnostic_nonbinding` with a reason — so the row may stay `open` while it is excluded from the
binding acceptance blockers, and the receipt shows binding unmet rows and audit notes separately.
The exclusion never covers a failing or missing required check, unverified direct evidence or a real
functional/security variant, and a finite audit task the user asked for **separately** stays
binding. If the project has a manifest validator, it is run. By default the manifest and its logs
live in `.pdca/<task>/rv<k>/` — next to the status directory `.pdca/status/`.

## A teaching story: when the cycle stops

> This is a **teaching illustration**, not a source of a rule. It shows the transitions and STOP
> schematically; the real wordings and lines are in the sources at the end of the article.

Imagine a task: answer whether caching intermediate results speeds up a nightly report. In PLAN r1
the planner formulates the criteria: (1) run times with and without the cache on the same data set;
(2) the conclusion follows from the numbers; (3) the methodology is reproducible. Units: the
baseline measurement, the measurement with the cache, writing up the conclusion. The plan is
written, the user approves the plan — DO begins (`N=1`, `r=1`, `n=1`).

During DO the executor discovers that the promised data set of the required size is not available.
It may not unilaterally fix the plan: DO returns a preliminary candidate, and the planner classifies
it as an **additive precondition** — the "measurement with the cache" unit stays active but
`blocked` on a dependency, and a new active unit, "obtain the data set", is added. This is not a
scope replacement, no mapping is needed. The precondition is closed, the measurements are taken,
the conclusion is written up, DO → CHECK.

CHECK in revision r1 returns `unmet` for the criterion "the methodology is reproducible": the
numbers are there, but the methodology is described incompletely. This is an implementation defect,
the cycle returns `CHECK → DO`, `n`=2. The executor expands the description; a re-check of the same
revision again returns `unmet` for the same criterion. The same defect came back after one fix — a
signal for **escalation before a second fix**, and the orchestrator calls `pdca-escalate`. The
escalation establishes that the required data set cannot be obtained in the permitted environment,
and without it the criterion cannot be met; there is no revised plan that preserves the original
criterion. The cycle ends in **STOP**: the remaining `unmet`/`unverified` criteria, the counters
(`N=1`, `r=1`, `n=2/3`) and the defect history are recorded — **without a false PASS and without a
successful ACT**. There is no fourth attempt, and STOP does not bypass that.

This outcome is not a failure of discipline: the cycle stopped where the verifiable result ran out,
and kept a record of why. And it is not "try a little harder": the "no fourth attempt" rule holds
after an escalation as well.

## Limitations and false expectations

- **"The task is too simple for the cycle."** The size of a task does not cancel the gates: it is
  on "simple" tasks that rework happens most often. Declining to split is a decision of the planner
  inside PLAN, not an exemption from criteria and verification.
- **Only a cheap primary drives the cycle.** A medium/strong primary (for example, `architect`)
  does not dispatch the cycle; outside the cycle it remains the decision maker.
- **There is no phrase trigger.** `pdca` is not caught by "by the cycle" — that is `pdca-coder`'s
  job. The domain-neutral variant is invoked explicitly by name, otherwise the contract does not
  apply.
- **An unavailable role is not a reason to work without it.** A missing mandatory agent is a
  resource blocker: in normal mode it is reported, in autonomous mode a `Notice:` and the reason
  are written.
- **A gate is an admission, not quality and not a guarantee of success.** The cycle does not make a
  plan correct and does not replace domain expertise; it merely does not let you close work without
  verification.
- **A report ≠ a result.** "The executor said `done`" does not close a unit; fresh evidence and an
  independent verdict are required. A self-verified verdict is "checker theater".
- **STOP is neither success nor failure.** A separate terminal outcome without a false PASS.
- **The status file is not deleted.** It is finalized and kept in any case.

## Where to go next

- A full walkthrough of the whole family — gates, counters, roles, modes, memory and evidence — is
  in the guide [`docs/pdca-guide.md`](pdca-guide.md).
- The normative contract of the domain-neutral cycle is the skill file
  [`opencode/pdca/SKILL.md`](../opencode/pdca/SKILL.md).
- The engineering cycle of the same core for code, tests, documentation and configuration is the
  article [`pdca-coder.md`](pdca-coder.md).
- The .NET-specific variant with its own gates (zero warnings, coverage and mutations, a mandatory
  test scope) is the article [`pdca-dotnet.md`](pdca-dotnet.md).
- A batch of independent tasks split into parallel group lanes (a merge barrier, a terminal
  `incomplete`) is the article [`pdca-collection.md`](pdca-collection.md).

## Sources

The article's normative claims were reconciled with the repository at commit `a58f338`; where the
article and the skill disagree, the skill file takes precedence. The "claim → source" map:

| Claim | Source |
|---|---|
| `pdca` is domain-neutral: it names only roles and phases; what to verify with is decided by PLAN | `opencode/pdca/SKILL.md:6-14` |
| Roles, tiers, fallback; an unavailable role is a resource blocker | `opencode/pdca/SKILL.md:38-88` |
| `pdca-orchestrator` is a cheap dispatcher, not a fifth skill (the agent prompt lives in the host config and is not shipped here) | `opencode/pdca/SKILL.md:48-52,63-71` |
| CHECK sees the cycle's evidence artifacts directly (scoped `read`), but not the product | `opencode/pdca/SKILL.md:22-28,59`; `opencode/pdca/assets/agents/pdca-check.md:11-20,27-28` |
| The orchestrator is a dispatcher; the ban on self-editing/self-reading/self-verdict | `opencode/pdca/SKILL.md:89-117` |
| The state machine and the `DO → PLAN` branch | `opencode/pdca/SKILL.md:118-142` |
| The counters `N`, `r`, `n/3` and the defect history | `opencode/pdca/SKILL.md:129-141` |
| The DO candidate → PLAN; an additive precondition vs a scope replacement | `opencode/pdca/SKILL.md:161-176,243-252` |
| Gates 1–5 and the STOP finalization | `opencode/pdca/SKILL.md:178-221` |
| The PLAN/DO/CHECK/ACT/STOP phase contracts, a state-dependent criterion, and the return after `incomplete` | `opencode/pdca/SKILL.md:222-280` |
| The frozen evidence manifest and the `.pdca/<task>/rv<k>/` directory | `opencode/pdca/SKILL.md:281-324` |
| The normal (plan approval) and autonomous (`Notice:`, no questions) modes | `opencode/pdca/SKILL.md:327-351` |
| The collection `plan_handoff` at the PLAN → DO boundary | `opencode/pdca/SKILL.md:343-350` |
| The status file as the only progress mirror, evidence, recovery | `opencode/pdca/SKILL.md:143-160,369-392,393-410,411-438` |
| Escalation, triggers 1–5, the "no fourth attempt" rule | `opencode/pdca/SKILL.md:439-494` |
| Limitations: permissions, instructions, injections, secrets, authorization | `opencode/pdca/SKILL.md:495-519` |
