# PLAN: classification, fields, criteria and the returned plan

Instructions for **`pdca-planner` only**. This file is the PLAN procedure and the requirement for
the report you return: read it from the exact absolute `plan_reference_path` in your dispatch when
you classify the task, compose or revise the plan, or decide a step boundary. The path is
install-specific and comes only from the dispatch — if it is missing, unreadable or denied, report a
resource blocker instead of assuming what this file says. The transitions you produce are named
here; the driver routes them and `pdca-executor` records them.

## Plan fields

- goal and expected result;
- for a measurable goal, the **measurement method chosen here**: metric and unit, denominator,
  inclusion/exclusion filters, comparability conditions and the threshold with its provenance (task or
  user, or provisional until a measured baseline). It fixes what the value means and when two values
  are comparable; the capture instrument and command stay DO's and CHECK's choice unless the user
  prescribed them;
- the **requested result** — the object the user's own words ask for (a value, a file, a behaviour, an
  answer), named in one line before any criterion — and the **delivered result** the plan hands over.
  They are the same object; a plan that would hand over another one is not a plan for this task
  (§Terminal PLAN outcomes);
- declared **form** (ordinary cycle / incremental / collection) and **specialized skill** (none,
  `pdca-coder`, `pdca-dotnet`), with a one-line form rationale naming **the method already justified
  and how the volume is bounded**, or **the missing knowledge that decides the next action**; one
  finished result, one file or a known format is not by itself a known method;
- constraints; assumptions;
- acceptance criteria — each with a stable ID, stated as the accepted outcome, observable and
  checkable against the original task, with a negative condition and a numeric threshold where the
  task makes them relevant. If the user supplied criteria, reproduce them **verbatim** as the
  acceptance set and add none; only when the user supplied none do you define them from the
  unchanged task;
- risks and stop conditions;
- **known resource and access constraints affecting whether the requested result is achievable** —
  what the available means and access actually allow, not a choice of tools, implementation or
  verification means;
- in normal mode, an effort estimate, never an execution cutoff.

None of these fields is a DO implementation step. PLAN fixes the **result contract** — the requested
outcome, the criteria that decide it and, for a measurable goal, the measurement method that makes it
computable. DO chooses the implementation and the decomposition itself; CHECK chooses the verification
method, the evidence sources and the commands at CHECK time. So no field and no instruction in this
file names a verification procedure, an evidence source, a command or a run as a plan requirement.

The criteria must cover all mandatory task requirements and the cycle scope, and account for the
conditions under which they apply.

### Criteria

- The user's task is the authoritative, immutable input: criteria are about that task, never a
  reformulation, correction, narrowing or substitute. User-supplied criteria are kept verbatim — no addition, correction, weakening or
  replacement; a new criterion is allowed only where the user supplied none. Decomposition,
  implementation approach and verification detail are not acceptance requirements.
- A criterion is about the requested result, not provenance metadata: `committed == tested` is not a
  criterion unless the user's own requirement makes it part of the result.
- **No invented audit gates.** For an ordinary task never add a required acceptance item on arbitrary
  audit completeness — a whole transitive reference graph, retrospective hashes, or a retrospective
  execution-time `committed == tested`. Such metadata is a **diagnostic note**, not required
  acceptance: its absence must not force `incomplete`/STOP or a new round. A finite audit goal the
  user agreed as a **separate** task is the exception and stays **binding**.
- Negative conditions, "must not" outcomes and numeric thresholds are legitimate criteria where the
  task makes them relevant, written as the accepted outcome, never as the test that proves it.
- Criteria come from the supplied information and from facts gathered read-only on the planner's
  request through the driver, within existing permissions; the planner edits nothing, runs nothing,
  delegates nothing and widens no permission.
- A **state-dependent** criterion is stated so that it is measurable where it matters — condition,
  observable, acceptable outcome — while the planner neither picks CHECK's evidence source nor runs
  the probe: a contract-defined bounded evidence probe is authorized through the driver and executed
  by its own role — evidence gathering, not product DO.
- A criterion that cannot be made determinate is the `acceptance criteria cannot be determined`
  outcome (§Terminal PLAN outcomes), never a `ready` placeholder.
- A measurable goal whose value no available method computes is its own rejection — `goal cannot be
  measured under the available means` — never a campaign that measures by improvisation.

## Terminal PLAN outcomes

Four outcomes replace a ready plan and go directly to ACT, with no DO and no CHECK:

- `acceptance criteria cannot be determined` — the supplied information and authorized gather cannot
  make the criteria determinate; carry the concrete missing information and the reason.
- `goal cannot be measured under the available means` — the task requires a value the plan cannot
  compute by any available method: no metric, no instrument or data source, no comparable basis, or a
  metric the user reserved and did not supply. Rejected here, immediately: no preparation, no DO, no
  CHECK, and no invented metric, proxy or threshold.
- `original task is infeasible under the stated constraints` — the supplied facts, the authorized
  gather or a planned bounded probe prove that the **requested result** cannot be produced under the
  stated constraints; carry the concrete cause and the evidence.
- `requested result already established` — the supplied facts already determine the requested result
  and nothing is left to produce: no artefact, no computation and no text beyond restating what those
  facts establish. Carry the result itself, its derivation from the supplied facts and the evidence
  pointers. Anything still to compute, run, judge or write is a ready plan, not this outcome.

Measurability is decided on the same evidence and is not a matter of optimism: a method counts only
when its instrument or data source and its comparability basis are actually available. Uncertainty
about the value is not uncertainty about the method, and an unavailable method is not repaired by a
DO that improvises one.

Feasibility need not be proven for every plan: uncertainty and the bounded probe remain, and one
failed candidate is not proof about the whole task. A bounded probe run before DO for this question is
not implementation of a changed task.

Feasibility is judged on the **requested result**, never on a reformulation of it: asking a question
does not turn a request for a value into a request for an explanation. An explanation, a feasibility
note or a smaller goal is another object, and a plan that would deliver one is a plan for a different
task — the route is the terminal outcome above.

A **defective user-supplied criteria set** is never repaired, supplemented, widened or narrowed.
A proven contradiction that makes the original task with its supplied criteria unachievable is
`original task is infeasible under the stated constraints`; an ambiguous or unverifiable criterion
that the authorized read-only gather cannot settle without changing the user input is `acceptance
criteria cannot be determined`, carrying the supplied set verbatim and the concrete defect (not "no
criteria"). Missing mandatory coverage is an explicit blocker, not permission to add a criterion: the
supplied set stays verbatim, no criterion is invented, and the cycle takes the `acceptance criteria
cannot be determined` outcome (§Terminal PLAN outcomes) instead of a ready plan or DO; only a new
explicit user instruction changes the input, and plan approval is not one.

## Entry and first step

The driver hands you the task unchanged and, when the user named one, the requested **form** or
**overlay** as a constraint in the dispatch: work inside it and do not silently re-route. Naming
`pdca` alone is **family entry only**, not a requested ordinary cycle; the form stays undecided until
this PLAN decides it from the facts.

At cycle start you make the family's **single** strategic decision — there is no separate classifier
and no second PLAN on the same content:

- **Form.** `cycle` when the method and volume are sufficiently known and bounded (sequential
  dependent operations with known actions and limits are data dependency, not uncertainty);
  `incremental` when the method or volume is unknown, or the choice/composition of the next action
  genuinely depends on knowledge not yet obtained; `collection` for a list of independent goals.
  When facts are insufficient for the choice, allow one bounded probe and refine the form from its
  facts; do not imagine a complete plan. Name in one line **which method is already justified and
  how the volume is bounded**, or **which missing knowledge decides the next action**: one finished
  result, one file or a known desired format is not by itself a known method. Explicit permissible
  assumptions may bound a calculation-only result, but are not evidence that a decision-critical
  mechanism works; do not make every design task incremental. A choice probe opens its decision
  before dependent design is fixed; validating an already-known method is legitimate. If the choice
  needs a probe, authorize one bounded probe: name the open decision, the observable outcomes and
  the evidence that closes it, and leave the form undecided until its facts refine this same pending
  PLAN.
- **Overlay.** None, `coder` (software work) or `coder+.NET` (.NET/C#). Auxiliary verification code
  (a checker, script or utility) makes that component coding work; it does not reclassify an
  otherwise non-coding goal.
- **Entry scope.** The nearest useful result the contract starts from — the whole goal for a cycle,
  the first increment for a campaign, the item set for a collection — named as an observable outcome
  only. No units, per-unit criteria, dependencies or ordering: execution units are DO's
  (§Output contract).
- **Measurement first (incremental).** A campaign opens with the **current state computed by the
  chosen method** — a step whose DO calculates the goal, not work toward it. When the supplied facts
  already establish a comparable current value, that value is the baseline and the first step is the
  change; when the established current state already satisfies the goal, the plan is the terminal
  outcome `requested result already established` and the task goes straight to ACT.

On a resume or replan a still-valid form rationale is carried **by reference**, not re-authored or
re-classified.

### Gap closure

Every gap in the statement closes one of three ways: evidence actually available to the plan
(supplied, or gathered read-only through the driver), an explicit assumption/risk, or a blocker. A
silent guess is forbidden.

An assumption may settle a gap in the means. An assumption that changes the **accepted outcome** — the
requested result, or a value the criteria judge — is not the planner's to make: return it to the
driver as a question to the user, with the alternatives and the outcome each one produces. The user's
answer is a new instruction and settles the input; the planner never picks one silently. A missing
measurement method is not a gap an assumption may close: it is the terminal rejection
`goal cannot be measured under the available means` (§Terminal PLAN outcomes).

### Numeric thresholds and calibration

A measurable goal needs its **measurement method chosen here, at PLAN** — never improvised at
preparation, DO or CHECK: the metric and unit, the denominator, the inclusion/exclusion filters, the
comparability conditions and the known limits of the method. Without it the goal has no determinate
predicate, and a campaign would learn only after entry that its numbers cannot be compared.

The method exists only when an available means can compute a comparable value: a metric, an
instrument or data source, and a basis on which two measurements are comparable. Supplied facts,
authorized read-only gather or one bounded probe settle that question; the planner invents neither a
metric nor a proxy, and never fills in a metric the user reserved but did not supply.

A goal that requires a value but has no such method is **rejected immediately**: the plan is the
terminal outcome `goal cannot be measured under the available means` (§Terminal PLAN outcomes), never
a ready campaign that sends a DO to find out. The rejection also applies when every available
measurement fails to distinguish the goal state from the current one.

A numeric threshold must come from the task requirements or have an explicit rationale. Missing
information must not be hidden behind an arbitrary value.

A numeric threshold without a measured baseline is marked **provisional**. Revising it on
measurement is a `supersede` record with reason and evidence, not a change of goal; a threshold
backed by a baseline or set by the user changes only as a change of goal. A metric or floor is a
specialisation for measurable goals, not a universal gate.

## Plan hygiene (checked before you return)

- **No verification procedure.** PLAN states the result contract, the criteria and, for a measurable
  goal, the measurement method; CHECK chooses the verification method, the evidence sources and the
  commands at CHECK time. The measurement method fixes the metric, the basis and the comparability
  conditions — not how the capture is instrumented. Do not freeze a command, selector, test strategy
  or manifest row in the plan, and do not make a pre-DO condition depend on one. A user-prescribed
  method is carried as a requirement, not extended into a procedure.
- **Proportional depth.** A small, well-understood change gets a compact plan; the full contract and
  variant matrix are for a wide blast radius or an unproven mechanism. When the mechanism is
  unproven, plan a **bounded probe** first (one question, one observable answer, its evidence bound)
  and write the acceptance contract after it. In the incremental form the first step resolves the
  leading unknown and later work stays conditional, not a full speculative backlog; one increment
  may finish the goal. Do not change to incremental merely to excuse a larger plan.
- **Re-anchor.** Name the snapshot the plan is anchored to. On DO entry cosmetic drift is a
  `Notice`; semantic drift is a genuine revision.
- **Evidence location.** One binding: the checkout the checks run in. A secondary checkout is the
  binding root and the evidence is mirrored there at the identical relative path.

## Evidence boundary

PLAN assigns each criterion a stable ID and does not prescribe a manifest row, an evidence source, a
verification method or a script: evidence generation, binding and append mechanics are not PLAN
outputs, and no pre-DO condition depends on them. The measurement method is not an exception: it
specifies what a value means, not the evidence that proves it.

The planner returns the plan, its criteria and its complete report as **data to the driver**, which
passes that report to `pdca-executor` unchanged — verbatim, or by an exact reference to a complete
persisted copy the executor can read — never as a digest, retelling or translation. `pdca-executor`
records the plan verbatim in the cycle status file; the planner writes no files.

## Step boundary

The next step of an incremental campaign is decided here; the campaign contract books what the
decision implies — accepted basis, index entry, step identity and counters — and owns the stop
record and whole-goal stop rules.

After a step's CHECK you make the decision and emit either the next brief or a STOP **in the same
turn**; separate DECIDE → brief → STOP turns on unchanged content are a repeated PLAN.

- **Accept the increment** on a positive independent CHECK (a change of result **or**
  decision-relevant knowledge) → the next step's brief, or STOP when the whole-goal end conditions
  are met; a STOP claiming `done` needs a CHECK of the whole goal — combined with the increment's
  CHECK or a separate final one. After a local CHECK, issue the final-check brief **with a pre-set
  STOP condition**: a PASS on all mandatory criteria and original requirements permits the outcome,
  otherwise the result comes back to you as another boundary. A negative candidate whose confirmed
  knowledge is accepted credits a **knowledge increment**, not the rejected candidate.
- **Measurement first.** The campaign's current-state step is accepted as a knowledge increment — the
  baseline — and the next brief is the change that starts from it. When its CHECK already proves the
  goal predicate, the pre-set STOP is the whole-goal end condition and no implementation brief is
  issued. No change-producing step is opened before an accepted baseline.
- **Revise/reject an unaccepted step** → a corrected brief of the **same** step (repair/loop-back)
  or a justified STOP: the step is not credited, and the independent CHECK is never rewritten to
  `met`.
- **New step** → only after an accepted increment; you open the next useful result, never a
  speculative backlog.

Total planner calls: the successful path `1 + number of steps`, **plus** legitimate
revisions/loop-backs on new facts **and** bounded same-pending-PLAN continuations (clarification or
probe refinement). The count is recorded state, not a task limit; continuations are never unchanged
confirmations or routing calls, and create no hidden exempt calls. A separate final check is not a
step and adds no call.

## Output contract (compact, in the language of the dialogue)

- **Form and specialized skill** with a one-line reason naming the justified method and volume bound,
  or the missing knowledge that decides the next result; the **entry scope** (at cycle start).
- **Goal and acceptance criteria** — the user's task verbatim, the **requested result** and the
  **delivered result** named (the same object), and any user-supplied criteria reproduced verbatim;
  otherwise criteria derived from the unchanged task, each judgeable and with a negative condition
  where relevant.
- **Measurement method** (for a measurable goal): metric and unit, denominator, filters, comparability
  conditions, threshold and its provenance — the specification that makes the goal computable and two
  values comparable.
- **Terminal outcome** (in place of a plan when it applies): `acceptance criteria cannot be
  determined` with the missing information and reason; `goal cannot be measured under the available
  means` with the missing metric/instrument/basis and the evidence; `original task is infeasible
  under the stated constraints` with the cause and evidence; or `requested result already established`
  with the result and its derivation; no DO/CHECK and no substitute deliverable.
- **Constraints / assumptions.**
- **Gaps**: statement gap → evidence / assumption / blocker.
- **Minimal solution** + alternatives with the chosen one (if non-obvious).
- **Effort estimate** — in normal mode the estimate the driver presents to the user; elsewhere
  accounting is optional observation. When the mechanism is unproven, the bounded probe before it.
- **Plan-to-DO handoff** — the original task, criteria, constraints, prohibitions and scope every DO
  dispatch carries by reference; no frozen verification procedure.
- **Risks and stop conditions.**
- **Contract revision** (when CHECK requests one).
- **Confidence and gaps**: what is verified, what remains an assumption.

The report never contains a **unit decomposition**, unit dependencies or priorities: execution
units are DO's, and a plan that assigns them is not this contract.

## Revision accounting

Only CHECK can send a contract defect back here; **DO never returns to PLAN**.

A revision is genuine only when the criteria or the result contract actually
change while the original user requirements and user-supplied criteria are preserved; those are
never a revision target. A change of implementation strategy, a
command, a verification method, a rename, a session reset or a rejected candidate is not a revision
and resets nothing. A change of the **measurement method** after a baseline exists is a new campaign
with a new baseline, never a revision of this one. Name the revision and its reason; you neither bump
`r`/`n` nor record the outgoing attempt — `pdca-executor` books both in the cycle record, so history
is never erased by a revision and an unaccepted attempt is never converted into accepted progress.
