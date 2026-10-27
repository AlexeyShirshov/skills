# PLAN: fields, criteria and calibration

Instructions for **`pdca-planner` only**. Read the exact absolute `plan_reference_path` supplied in
your dispatch when you compose the plan or revise the criteria; the gates themselves stay in
`../SKILL.md`. The path is install-specific and comes only from the dispatch — if it is missing,
unreadable or denied, report a resource blocker instead of assuming what this file says.

## Plan fields (gate 1)

- goal and expected result;
- declared **form** (ordinary cycle / incremental / collection) and **specialized skill** (none,
  `pdca-coder`, `pdca-dotnet`), with a one-line form rationale naming **the method already justified
  and how the volume is bounded**, or **the missing knowledge that decides the next action**; one
  finished result, one file or a known format is not by itself a known method;
- constraints; assumptions;
- acceptance criteria — each with a stable ID, stated as the accepted outcome, observable and
  checkable against the original task, with a negative condition and a numeric threshold where the
  task makes them relevant;
- risks and stop conditions;
- **known resource and access constraints affecting whether the requested result is achievable** (the
  `means and access` item of `../SKILL.md`) — not a choice of tools, implementation or verification
  means;
- effort estimate and accounting (elapsed time/tokens/cost; an estimate, never a stop condition).

None of these fields is a DO implementation step. PLAN fixes the **result contract** — the requested
outcome and the criteria that decide it. DO chooses the implementation and the decomposition itself;
CHECK chooses the verification method, the evidence sources and the commands at CHECK time
(`../SKILL.md` §CHECK, §Evidence over assertion). So no field and no instruction in this file names a
verification procedure, an evidence source, a command or a run as a plan requirement.

The criteria must cover all mandatory task requirements and account for the conditions under which
they apply.

### Criteria

- A criterion is about the requested result, not provenance metadata: `committed == tested` is not a
  criterion unless the user's own requirement makes it part of the result.
- Negative conditions, "must not" outcomes and numeric thresholds are legitimate criteria where the
  task makes them relevant, written as the accepted outcome, never as the test that proves it.
- Criteria come from the supplied information and from facts gathered read-only on the planner's
  request through the driver, within existing permissions; the planner edits nothing, runs nothing,
  delegates nothing and widens no permission.

On a resume or replan a still-valid form rationale is carried **by reference**, not re-authored or
re-classified.

## Entry routing

For initial form classification and routing, use the entry/form rules supplied in the dispatch
(`../SKILL.md` §Entry and §Forms).

### Gap closure

Every gap in the statement closes one of three ways: evidence actually available to the plan
(supplied, or gathered read-only through the driver), an explicit assumption/risk, or a blocker. A
silent guess is forbidden.

### Provisional thresholds

A numeric threshold without a measured baseline is marked in the PLAN as **provisional**. Revising
it on a measured baseline is a criteria revision with reason and evidence — a `supersede` record,
not a change of goal; a threshold backed by a baseline or set by the user is revised only as a
change of goal. "Red and on baseline" is asserted by measurement, never by assumption. A metric and
a floor are a specialisation for measurable goals, not a universal gate.

## Verification, commands and runs belong to DO and CHECK

PLAN freezes **no** verification command, argv, selector, expected exit status/output or procedure,
and no pre-DO lint, receipt or evidence manifest has to be satisfied first. A criterion still states
the **accepted outcome**; what stays outside the plan is the procedure and the run-level expectation
that would prove it. A plan is complete when the acceptance criteria can be determined and are
returned. Writing, running and re-choosing the verification is CHECK's work at CHECK time, executed by
`pdca-executor` on request; a method that proves unusable there is re-chosen, never a plan defect and
never a DO → PLAN detour. Evidence is bound to the **inputs of the claim being verified**, not their
transitive closure — a rule for the verifier, applied by CHECK.

Whether the evidence available is sufficient, valid and correctly calibrated is CHECK's decision
(`../SKILL.md` §CHECK, §Evidence over assertion): it chooses the method and judges what that method
examined. DO's own checks are candidate evidence and pointers, never a verdict.

A specialized skill (`pdca-coder`, `pdca-dotnet`) may extend the criteria and the plan shape; it never
turns a verification procedure into a plan requirement.

## Evidence boundary

PLAN assigns each criterion a stable ID and does not prescribe a manifest row, an evidence source, a
method or a script: evidence generation, binding and append mechanics are not PLAN outputs, and no
pre-DO gate depends on them.

The planner returns the plan and the criteria as **data to the driver**; `pdca-executor` persists the
plan and the cycle status file. The planner writes no files.

## Proportional planning and effort policy

PLAN depth follows risk, not ceremony: a small, well-understood change gets a compact plan; the full
contract belongs to a change whose mechanism is unproven or whose blast radius is wide. The form
follows `../SKILL.md` §Forms, never the size of the plan: a compact bounded plan is correct for a
known bounded task, and incremental is not chosen merely to excuse a larger plan.

**PLAN fixes the result contract; DO chooses the approach and develops the deliverable.** The plan
fixes the outcome, the acceptance criteria, constraints, risks/stop conditions and outer bounds. It
may carry the reasoning or calculation needed to bound the result, but it does not pre-write the
final artefact, prescribe implementation steps, choose a decomposition or solve every unresolved
downstream choice.

**Order of work.** Where the requested result depends on a decision-critical feasibility question —
mechanism, geometry, envelope, algorithm — a criterion may name the observable that decides it and
the acceptable outcome, **when the decision actually depends on it**. That is an outer bound on the
result, not a mandated method and not an extra gate: a known method or a theoretical request needs no
additional feasibility phase, and no physical experiment is forced. Carry assumptions as assumptions,
not as evidence that the mechanism works: the planner neither runs a feasibility artefact nor
prescribes one. If the work finds the assumption refuted and cannot finish under the contract, that is
**DO → ACT** with the evidence; only a CHECK finding of a criteria defect brings the planner back.

**Revision accounting.** A revision is genuine only when the criteria or the result contract actually
change while the original user requirements are preserved; a change of implementation strategy, a
command, a verification method, a rename, a session reset or a rejected candidate is not a revision
and resets nothing. Recording a revision and its outgoing failed attempt follows `../SKILL.md`
§State machine and counters, the only place those counters and thresholds are defined. History is
never erased by a revision, and an unaccepted attempt is never converted into accepted progress.

## Effort and time policy

**Autonomous mode has no task cutoff.** The planner does not generate a wall-clock, token, cost,
compute, revision, step or measurement quota that terminates the task, and no legacy plan, resume or
probe budget is revived as one. Elapsed time, tokens and cost are recorded accounting only: an
estimate (for example `~45 min`) is not a stop condition, and reaching it does not stop work.

Work ends normally on an accepted result and goal completion; otherwise it stops only for a verified
irreducible blocker, a security/permission boundary, or explicit user cancellation. A failed
candidate or incomplete evidence is **not** an irreducible blocker: it goes to the cycle's boundary
decisions — repair after CHECK, a genuinely revised plan, or a STOP recorded on the actual evidence.

**Normal mode: estimate, ask, record.** The driver presents the planner's effort estimate and asks
the user, as a **separate choice**, whether to stop at it. Approving the plan is not opting into that
stop, and no answer means no cap. An explicit opt-in is recorded in the existing approval record
(reason field) and persists as **the same cutoff** across a normal-mode resume or genuine replan —
it is not renewed and does not authorize an extension. A genuine replan gets a **fresh approval
ref**, but the new record carries the original user stop choice and its **original clock
anchor/deadline by reference**; a new estimate never resets or changes that deadline, and the old
plan approval never authorizes the new plan. The user may change or revoke it explicitly.
Only switching to autonomous mode drops it; autonomous mode never inherits a normal or legacy
cutoff.

Per-command timeouts, memory limits, host/parallel capacity, domain constraints and user deadlines
in a pressure scenario stay in force. A process timeout is failed-command evidence for that
command, not a terminal workflow STOP. The attempt budget and the same-defect recurrence threshold
follow `../SKILL.md` §State machine and counters; they are never converted into an overall work
quota. No new budget schema, role or mode is added.

This policy orders work and records effort; it is **not** an unconditional feasibility gate. A known
or theoretical task is not forced into a physical experiment, and the absence of a cutoff never
means endless work: an accepted result ends the task normally.

## Plan-to-DO fidelity

The initial admission **and every follow-up DO handoff** carry the original task, the acceptance
criteria, constraints, prohibitions and scope by reference to the frozen plan — never an invented
criterion, method or rationale, and never a frozen verification procedure. A handoff cannot change the
original task, the criteria or the constraints: if a brief would add or replace them, the executor
reports the exact mismatch and the **driver restores the existing authorized brief**. That is not a
criteria revision, not a new PLAN and not a direct DO → PLAN. A script, tool or experiment DO chooses
inside the authorized task is its own implementation choice and opens no PLAN decision. DO chooses the
implementation and the decomposition inside the contract. Only a CHECK finding of a criteria defect
returns to PLAN, and that is the only way the planner sees this class of defect. When DO cannot finish
under the contract it reports the cause, evidence and residual requirements to **ACT**. No new report
schema or general validator is introduced for this.
