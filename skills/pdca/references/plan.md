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
- in normal mode, an effort estimate, never an execution cutoff.

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

### Numeric thresholds

A numeric threshold must come from the task requirements or have an explicit rationale. Missing
information must not be hidden behind an arbitrary value.

## Evidence boundary

PLAN assigns each criterion a stable ID and does not prescribe a manifest row, an evidence source, a
method or a script: evidence generation, binding and append mechanics are not PLAN outputs, and no
pre-DO gate depends on them.

The planner returns the plan and the criteria as **data to the driver**; `pdca-executor` persists the
plan and the cycle status file. The planner writes no files.

## Revision accounting

A revision is genuine only when the criteria or the result contract actually
change while the original user requirements are preserved; a change of implementation strategy, a
command, a verification method, a rename, a session reset or a rejected candidate is not a revision
and resets nothing. Recording a revision and its outgoing failed attempt follows `../SKILL.md`
§State machine and counters, the only place those counters and thresholds are defined. History is
never erased by a revision, and an unaccepted attempt is never converted into accepted progress.

## Effort and time policy

In normal mode, provide an effort estimate. The estimate is not an execution cutoff; when criteria
are revised, a new estimate does not change the constraints agreed by the user.
