# `pdca`: the cycle that carries a task to a verifiable result

## Why the cycle exists and when to pick `pdca`

Ordinary assistant work is a sequence of actions: read, change, run, say "done". That sequence has
three weak points. Success is not defined in advance, and "done" is the author's opinion rather than
a verified fact. State lives in the session context, so after compaction or in a new session the
assistant cannot say where it stopped, what was done and why. And a failed attempt costs nothing:
the same action can be repeated indefinitely without producing progress.

`pdca` replaces the sequence with a **path to a verifiable result**. The idea comes from the
management cycle Plan — Do — Check — Act: plan, execute, verify independently, finish or return to
the plan. The contract turns that into a **state machine with explicit exits** and keeps the state on
disk instead of in the model's head. It promises little: it cannot make a plan correct or guarantee
a good result in the real world. What it does guarantee is that work cannot be closed without
verification, that state is not silently lost, and that identical retries are not reported as
progress.

![Diagram of the domain-neutral pdca cycle: phase inputs, roles by tier, state graph](../skills/pdca/assets/diagram/pdca-hand-dark-en.svg)

`pdca` is **domain-neutral**: it names roles, phases and execution forms, and imposes no artefacts,
task types or domain examples. What the result is — a report, a document, a config, a plan, a piece of
software — and how it is verified are decided inside the cycle. That makes `pdca` suitable for a task
with a **verifiable result**: the success criteria can be stated, and evidence can decide whether
they hold.

`pdca` is the **only entry** of the family and never turns itself on. For an ordinary task, without
an invocation, the contract does not apply. It is also not the only option inside the family: one
PLAN chooses the **execution form** — Bounded Execution, an incremental campaign
(`pdca-incremental`) or a collection (`pdca-collection`) — and, when the work is code, the
**specialized skill** (`pdca-coder`, or `pdca-dotnet` inheriting it). The forms inherit the common
cycle contract and add only their container; the coding skills are overlays that add domain facts and
never open a second cycle.

## How to launch it: by phrase, or by name

`pdca` is caught by the phrases "by the cycle", "via PDCA", "run PDCA", or by the name `pdca`. Its one
PLAN classifies the goal into a form and selects the specialized skill instead of routing to a
separate umbrella.

Naming another family skill explicitly is a **constraint**, not a second entry: `pdca-dotnet`,
`pdca-collection` or `pdca-incremental` means "work inside this form or overlay"; the entry does not
silently re-route. A direct load of a form also loads the base common rules and skips the
classification, because the user already chose the form.

There is no cheap semantic classifier and no second PLAN over the same content. The planner's
decision is recorded with a **form rationale**: the method already justified and the bound on the
volume, or the missing knowledge that decides the next action. A single deliverable, one file or a
known format is not by itself a known method.

## Who does what work

The cycle has a fixed set of **roles**. A role is a function with responsibilities, permissions and a
required tier — not a person and not a specific model. The host binds agents and models; the skill
creates no agents and assigns no models.

| Role | What it does | Agent | Tier |
|---|---|---|---|
| FACT-FINDING & OBSERVATION | Collects facts (`file:line`, URLs, numbers) and observes the frozen result when CHECK needs an outsider | `pdca-scout` | cheap |
| PLAN | Classifies the form and overlay, preserves the task and supplied criteria, defines criteria when none were supplied, decides revisions | `pdca-planner` | medium |
| DO | Edits files, runs commands, gathers evidence, writes the cycle status file | `pdca-executor` | cheap |
| CHECK | Chooses the verification method per criterion and renders the independent verdict | `pdca-check` | medium |
| ESCALATE | Expert review of a difficult or disputed decision; advises, never decides for the phase | `pdca-escalate` | strong |
| DRIVER | Coordinates dispatches, handoffs and state; decides and judges nothing | cheap primary, or `pdca-orchestrator` in autonomous mode | cheap |

Five rules keep the table honest.

1. **The driver is a dispatcher.** It routes roles and reports; it does not write the plan, read
   evidence into context, pick verification methods or render verdicts. In normal mode the primary is
   the driver; in autonomous mode it delegates coordination to `pdca-orchestrator`.
2. **PLAN always belongs to `pdca-planner`.** Both the first plan and every revision are formulated
   there. `pdca-orchestrator` never reclassifies a task, re-chooses a form or rewrites a plan.
3. **Only `pdca-executor` writes and runs.** That includes the status file. The planner, check,
   escalate and driver have no file write permissions by design, so there is exactly one writer.
4. **CHECK is independent of the author.** It did not produce the result and does not take the
   executor's report as evidence. It may read the cycle's evidence artefacts directly, within its
   scoped permission, but never the product itself as the sole proof.
5. **Tiers are cost, not authority.** `pdca-escalate` is strong but read-only; `pdca-executor` is
   cheap yet owns edits and commands; planner and check are medium but default-deny. The host profile
   binds a model to the tier; the permission rules bind what the role may do.

An unavailable mandatory role is a **resource blocker** — never a silent run without it. Normal mode
reports it to the user; autonomous mode records `Notice:` and the durable reason. A fallback that the
host forbids is not bypassed. If `pdca-orchestrator` itself is unavailable in autonomous mode, the
cheap primary drives the cycle flat and records the fallback.

## How the cycle runs

The state machine is the whole machine:

```text
PLAN → DO (normal mode: after approval) → CHECK → ACT → (EXIT | PLAN)
DO → ACT (cannot finish) | CHECK → DO (defect) | CHECK → PLAN (contract) | CHECK → ACT (STOP)
PLAN → ACT (criteria undetermined | original task infeasible)
```

**PLAN.** `pdca-planner` defines the **result contract of this cycle**: the goal and expected result,
the form and specialized skill with a rationale, constraints and assumptions, acceptance criteria
(each judgeable as met, unmet or unverified), means and access, risks and stop conditions, and in
normal mode an effort estimate. It does not prescribe implementation steps or a step-by-step DO; the
executor chooses the implementation. It does not prescribe verification methods, evidence sources or
commands either; that is CHECK's decision. If the criteria cannot be determined from the information
and the authorized read-only gather, PLAN returns `acceptance criteria cannot be determined` and the
cycle goes straight to ACT — no DO, no CHECK. If the supplied facts prove that the **original task
itself** cannot be achieved under its constraints, PLAN returns `original task is infeasible under the
stated constraints` with cause and evidence. One failed candidate is not such proof, and an
explanation or a smaller goal is never a substitute deliverable.

**DO.** `pdca-executor` carries out the approved result contract and chooses the implementation inside
it. It may split the work into units, with disjoint ownership for any parallel work, and it records
every run with its exit status, key numbers and log path. It gathers candidate evidence but renders
no verdict. DO has exactly two outcomes: a **completed candidate with evidence**, or **cannot
finish** with cause, evidence and the residual `unmet`/`unverified` requirements.

**CHECK.** `pdca-check` receives the original task, the global requirements, the cycle scope and
criteria, and the actual frozen result. It first assesses the criteria themselves — coverage,
contradiction, judgeability — then chooses a verification method per criterion, obtains the evidence
through the driver, and only then compares. A missing check is not a pass: without numbers, pointers
or an actual observation, the criterion is `unverified`, never `met`. The verdict carries a criteria
matrix (`met | unmet | unverified`), findings bound to the requirement they concern, evidence
pointers and the next authorized transition. An aggregate score never compensates for an unmet
mandatory requirement.

**ACT.** ACT finalizes the outcome the ending phase determined. It records the conclusions,
limitations, accepted snapshot and handoff, and it changes no product, test or checked artefact. An
accepted CHECK leads to `EXIT` or the next authorized cycle; a `blocked`/`incomplete`/`STOP` outcome
is finalized honestly, with no `PASS`, no `done` and no credit. STOP is an **ACT outcome**, not a
separate phase or a path beside ACT. Work discovered during finalization goes back to DO and a fresh
CHECK, or invalidates the accepted snapshot; it is never slipped into ACT.

**Returns.** `CHECK → DO` is an implementation defect: the criteria are sound but the result fails
them. `CHECK → PLAN` is a contract defect: the criteria are contradictory, unverifiable or do not
cover the original requirements. Only CHECK routes a contract defect, and only a genuine revision of
the result contract changes `r`. There is **no `DO → PLAN`**: a DO that cannot finish goes to ACT.

**Whole-goal acceptance.** Accepting a cycle accepts its own scope only. `done` is reserved for an
accepted **whole-goal** CHECK covering every original mandatory requirement — the whole task in
Bounded Execution, the campaign's final check in Incremental Execution. A local PASS never proves the
whole goal.

## The counters

Four counters name four different things. They are defined once, in
[`skills/pdca/SKILL.md §State machine and counters`](../skills/pdca/SKILL.md), and no local section
redefines them.

| Name | What it counts | When it grows | When it resets |
|---|---|---|---|
| `N` | The task's **cycle number**, visible in `.pdca/status/<task>-<N>.md` | Only in ACT, when a further cycle of the same task is authorized | Never on a loop-back |
| `r` | The **plan revision** | Only when the substantive result/criteria contract genuinely changes | Never by a rename, a command change, a session restart or a rejected candidate |
| `n/3` | Execution attempts of the current revision | `CHECK → DO` increments it | A new revision starts at 1 |
| `rv` | The **contract revision** in the evidence path | Only when criteria or required rows actually change | Not an attempt counter at all |

Alongside them lives the **defect history**, one row per stable defect key, tracked across revisions.
A rejected candidate is not a revision; a clarification, a new verification method or a new session
is not a revision either. The same defect returning after one attempted fix requires
`pdca-escalate` before the next fix. After the **third failed substantive CHECK of one revision**
there is no fourth attempt: the mandatory expert review comes first, and an exhausted revision ends in
ACT as `incomplete`/`STOP`, never in a silent reset. A genuine revised plan may continue, but it
never erases the same-defect history.

## Evidence, status and recovery

The cycle closes only on **fresh evidence**, never on an assertion, including a subagent report. The
driver does not inspect evidence itself; it builds the chain and routes requests. CHECK chooses the
method, the executor runs or produces the evidence, `pdca-scout` observes when an outsider is needed,
and CHECK judges. "Should work", "probably", "looks correct" and "passed last time" are instructions
to run the check, not evidence. **A report is not a result**: matching identities do not establish
content correctness.

Everything the skill writes lives under one project-local root, `.pdca/`, in the project root:

```text
.pdca/
├─ scripts/            # runtime copies of helper scripts, when a helper is used
├─ status/             # durable cycle and campaign status files
└─ <task>/rv<k>/       # evidence: manifest, logs, per-row artifacts
```

The **status file** is the source of truth. Its default path in Bounded Execution is
`.pdca/status/<task>-<N>.md`; an inheriting form may keep one file for several cycles. It has fixed
headings — `## Current state`, `## Original task`, `## PLAN record`, `## Approval record`,
`## DO result`, `## CHECK record`, `## ACT record`, `## Revision history`, `## Defect history`,
`## Changed files`, `## Git state`, `## Progress log` — and only `pdca-executor` writes it. The task
and the planner's returned plan are recorded verbatim. History is append-only; a final status file is
kept after ACT and is never deleted.

Durable on disk is not the same as Git-tracked. A status write never stages, commits or pushes
anything; the skill commits only when an explicit user instruction or a recorded task policy says so,
and `## Git state` records the truth (path, created/modified, tracked/untracked, pending commit).

After compaction, the status file is what survives. Recovery starts by stopping the current action,
reading the status and evidence through `pdca-scout`, answering the recovery questions from the
artefacts, and continuing from the recorded phase without reopening PLAN or CHECK. Retelling from
memory is **State Rot**; the status file wins.

## Normal and autonomous modes

In **normal mode**, the user approves the plan before DO. The executor writes the plan to the status
file, the driver gives the user the path and asks for approval, and that approval is the **only start
signal**. A question, a change request or a non-committal reply is not approval. Without it, nothing
outside the status file is created or edited. For caller-driven cycles the approval is bound to a
durable **pending approval ref** (task/`cycle_id`, `N`, `r`, criteria set); the parent asks the user,
and the executor records the approval against the same ref. A stale plan needs a genuine revision and
a fresh ref.

In **autonomous mode**, there are no intermediate approvals or questions. The driver dispatches the
roles, records `Notice:` for an unavailable role, a detected injection, a recovery or an assumption,
and advances on the planner's decisions and CHECK's results. Permissions, contracts, evidence rules
and stop conditions do not relax. An approval required by the environment or the user still blocks;
it is not invented away.

## Escalation and honest limits

`pdca-escalate` is an **additional expert review**, not a phase. It is called for a substantive
judgment that remains low-confidence or disputed: an ambiguous requirement, a counter that no longer
lets the cycle pass, a risky or irreversible implementation decision, an acceptance needing a risk
assessment, or a PLAN/DO decision still uncertain after a targeted gather. It returns reasoning, the
facts it relied on, residual uncertainty and a recommended disposition — never a menu, an
implementation or a product verdict. PLAN and CHECK keep their decisions; the expert waives no gate
and widens no permission.

The cycle has deliberate limits. A plan can be formally complete and still weak; the contract checks
presence and evidence, not expertise. A criterion can remain `unverified`; that blocks acceptance
rather than being rounded up. A task can be infeasible or its criteria undeterminable; the honest
outcome is then a recorded ACT `STOP`, not a substitute deliverable. And `pdca` does not commit,
push, merge or widen permissions on its own: those are explicit user or project decisions.

## Where to go next

- The full walkthrough — forms, roles, phases, counters, evidence, modes, recovery, teaching stories
  — is the guide [`docs/pdca-guide.md`](pdca-guide.md).
- The normative base contract is [`skills/pdca/SKILL.md`](../skills/pdca/SKILL.md).
- The programming overlay is [`pdca-coder.md`](pdca-coder.md); the .NET/C# overlay, which inherits
  it, is [`pdca-dotnet.md`](pdca-dotnet.md).
- The incremental campaign is [`pdca-incremental.md`](pdca-incremental.md); the collection batch is
  [`pdca-collection.md`](pdca-collection.md).
- Host setup — role agents, the orchestrator, delegation depth, permissions, model bindings — is
  [`install.md`](install.md).

## Sources

The article is reconciled with the repository's current contracts; where prose and contract differ,
the skill file wins. Line ranges are used only for the short preamble before the first `##` heading.

| Claim | Source |
|---|---|
| `pdca` is domain-neutral: roles, phases and forms, no domain artefacts | `skills/pdca/SKILL.md:6-13`; §Forms |
| `pdca` is the single entry; one PLAN chooses form and specialized skill; a named form is a constraint | `skills/pdca/SKILL.md §Entry: one PLAN decides the form` |
| The three forms and how they continue | `skills/pdca/SKILL.md §Forms`; §Where each form continues |
| The common cycle contract is the single source for shared rules | `skills/pdca/SKILL.md §Common cycle contract` |
| The task and user-supplied criteria are immutable | `skills/pdca/SKILL.md §The user's task and its criteria`; §Original task, cycle scope and acceptance |
| Roles, tiers, permissions and the driver | `skills/pdca/SKILL.md §Roles and host requirements`; §Control modes |
| The state machine, STOP as an ACT outcome and the whole-goal rule | `skills/pdca/SKILL.md §State machine and counters`; §Phase contracts |
| PLAN defines the result contract, terminal outcomes and no implementation or verification procedure | `skills/pdca/SKILL.md §PLAN`; `skills/pdca/references/plan.md §Plan fields`; §Terminal PLAN outcomes |
| DO has two outcomes and cannot return to PLAN | `skills/pdca/SKILL.md §DO` |
| CHECK chooses the method and routes `CHECK → DO`, `CHECK → PLAN`, `CHECK → ACT` | `skills/pdca/SKILL.md §CHECK`; `skills/pdca/references/check.md §Verify the result · §Verdict and routing` |
| ACT finalizes acceptance and honest non-acceptance; STOP is not a path beside ACT | `skills/pdca/SKILL.md §ACT`; `skills/pdca/references/act.md §Closing order` |
| The four counters and the defect threshold | `skills/pdca/SKILL.md §State machine and counters` |
| Evidence over assertion; the method/run/observe/judge split | `skills/pdca/SKILL.md §Evidence over assertion` |
| The `.pdca/` workspace, the status skeleton and the Git-state rule | `skills/pdca/SKILL.md §Workspace and durable status`; `skills/pdca/references/act.md §Status file` |
| Recovery is read from the status, not from memory | `skills/pdca/SKILL.md §Recovery` |
| Normal-mode approval, durable refs and autonomous mode | `skills/pdca/SKILL.md §Normal-mode approval`; §Control modes |
| Escalation grounds and its advisory scope | `skills/pdca/SKILL.md §Escalation — expert review (pdca-escalate)` |
| Permission, secret and untrusted-content boundaries | `skills/pdca/SKILL.md §Generic operating constraints` |
| Bounded Execution is the whole task | `skills/pdca/SKILL.md §Bounded Execution` |
