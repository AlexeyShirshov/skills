# PLAN: fields, commands, evidence and calibration

Reference for the PLAN phase. Read it when the plan is composed or revised; the gates themselves
stay in `../SKILL.md`.

## Plan fields (gate 1)

- goal and expected result;
- declared **form** (ordinary cycle / incremental / collection) and **overlay** (none, coder,
  coder+.NET), with a one-line reason naming **the method already justified and how the volume is
  bounded**, or **the missing knowledge that decides the next action**; one finished result, one
  file or a known format is not by itself a known method;
- constraints; assumptions;
- acceptance criteria, **each with a verification method** and a negative case;
- **carrying claims** with IDs — the central claims of the goal, mandatory criteria and hard
  validity constraints — listed separately from quality-rubric axes;
- decomposition into units with dependencies, or an explicit decision not to split a simple task;
- the **nearest useful step** and its observable result;
- **verification choice** — the cheapest sufficient method per carrying claim; for a bespoke
  checker, why existing or manual means are insufficient and the bound that keeps it proportional
  (§Verification economy);
- means and access;
- risks and stop conditions;
- effort estimate and accounting (elapsed time/tokens/cost; an estimate, never a stop condition).

For a campaign step the same fields are narrowed to that step, while the whole goal, requirements
and constraints stay stored; a full backlog is not imitated. On a resume/replan, a still-valid form
rationale and verification choice are carried **by reference**, not re-authored or re-classified.

## Entry routing and bounded continuations

**Fresh entry.** A dispatch with no decided form and no persisted plan enters as `contract: pdca`,
`form: UNDECIDED`; one goal or deliverable does not make it `form=cycle`, and the driver names no
`cycle-control`/`campaign-control` before the PLAN. The single planner brief carries the original
goal, a user-named form/contract separately as a constraint, the facts, the decision-relevant
unknowns, and the **form discriminators themselves** (`../SKILL.md` §Forms) — names alone are not
enough for a read-denied planner. The planner returns the form, overlay, nearest useful step and
carrying claims, or one bounded choice probe (below). This is a stage of the existing dispatcher, not
a fourth context, role or recursive orchestrator.

**Routing the decision.** Cycle and campaign stay with the same controller (`cycle-control` /
`campaign-control`). A chosen collection hands the existing initial batch plan **by reference** back
to the cheap primary/collection owner, which loads `pdca-collection` and starts the per-item/lane
machinery under the existing permissions; the entry controller does not become the batch owner, does
not self-delegate, and `collection-lane` stays an existing caller-dispatched lane. Batch-level
ownership and lane duties stay distinct; a single-lane batch is normal; legitimate per-item PLANs
and lane calls stay as the collection contract requires.

**No second PLAN.** The returned plan **is** the initial plan: `pdca-executor` persists it by the
existing rules, and the controller continues at the current PLAN → DO gate with every validation,
approval and low-tier boundary. An entry-owned plan is never re-authored as Input 2's full PLAN. A
form-known dispatch that genuinely has no plan of its own (for example a collection task's own PLAN)
still runs that PLAN; a persisted `plan_handoff`/resume is never re-planned. A named plan ref in the
existing brief/status suffices — no new state file, schema or counter.

**Bounded choice probe.** The planner may authorize one bounded probe before the form is settled:
name the open decision, the observable outcomes and the evidence that closes it, and keep
`form: UNDECIDED`. A choice probe
opens its decision with an observable outcome before dependent work is fixed; validating a known
method is legitimate. Do not make every design task incremental; permissible assumptions may bound a
calculation-only result but do not evidence a decision-critical mechanism. `pdca-executor` runs
exactly that probe and `pdca-scout` observes; the same
planner refines the **same pending PLAN** from the facts and then chooses. A probe is not an
independent cycle, creates no fresh controller, adds no per-tool CHECK and no extra full PLAN, and
waives no permission or approval. A missing method/volume rationale is a completeness clarification
with the same planner — not automatically incremental or a STOP — and never bumps `r`/`n`.

**Campaign bootstrap order.** A campaign reuses the entry choice and first useful step:
`pdca-executor` persists the immutable preparation record with `preparation_ref` from that plan
(clarify the same pending PLAN only if preparation fields are genuinely missing), then
baseline/runtime is bootstrapped before the first step DO; the initial PLAN is not duplicated and
approval/counters follow `../pdca-incremental/SKILL.md` §0.

**Bespoke checker admission.** The driver checks only that a proposed bespoke checker's verification
choice carries a concrete insufficiency reason and a bound; if either is absent, it returns an
incomplete pending PLAN to the same planner and does not judge necessity.

**Planner-call accounting.** Successful path: `1 + number of steps`, plus legitimate
revisions/loop-backs, **and** bounded same-pending-PLAN continuations (clarification or probe
refinement). Continuations are not new strategic decisions; the call count is recorded state, not a
task limit. They are never unchanged confirmations or routing calls and create no hidden exempt
calls.

### Plan document and status persistence

The planner returns the plan **and writes the same text** to the plan document the brief pins
(`.pdca/<task>/rv<k>/plan-r<n>.md`) — its one permitted write. Persistence is then mechanical, not a
second authoring pass:

- `pdca-executor` creates the status file by **including the plan document verbatim** (a file copy,
  never a re-typed copy) plus the status schema and counters; the document stays the reference for
  the plan text.
- This happens in the **first DO dispatch**, together with the `commands.json` projection, the
  staged `plan_lint`/`status_lint` receipts and gate 1 — on a gate-1 failure the dispatch stops
  before DO and reports the PLAN defect. A separate "persist the plan" dispatch is a wasted context,
  not a checkpoint.
- The status file remains the durable record: it carries the plan text, the counters and the log,
  and the plan document is its frozen source for a re-read.

### Gap closure

Every gap in the statement closes one of three ways: evidence, an explicit
assumption/risk, or a blocker. A silent guess is forbidden.

### Provisional thresholds

A numeric threshold without a measured baseline is marked in the PLAN
as **provisional**. Its revision on measurement is a `supersede` record with reason and evidence,
not a change of goal; a threshold backed by a baseline or set by the user is revised only as a
change of goal. "Red and on baseline" is asserted by measurement, never by assumption. A metric and
a floor are a specialisation for measurable goals, not a universal gate.

### Evidence binding

Evidence is bound to the **inputs of the claim being verified**, not to their
transitive closure. A retrospective "committed == tested" requirement is not an acceptance gate
unless the commit is part of the claim. Previously valid observations are reused until refuted;
numbers/pointers do not replace relevant observed evidence, and a numeric gain is not mandatory
where the claim is not numeric.

### Verification economy

No bespoke verifier or coverage audit "because we can build one": the plan needs a rationale for
the current decision and the cheapest sufficient method. Independent manual observation or a
focused recomputation can be sufficient; "verifiable evidence" does not require a new executable
checker. A custom checker is allowed when the PLAN justifies why existing means and manual checking
of the carrying claims are insufficient, and its size is proportional to the artefact under check.
A full future verification infrastructure is not the default at the start, and a genuine required
test, security or carrying-veto gate is never waived by this economy.

### Evidence requirements match role permissions

The PLAN never requires from the observer an
action its role forbids (for example computing a hash without shell). Otherwise the requirement is
marked `unverified-by-design` up front or assigned to a role with the needed rights.

## Step fields

A step records, in the existing status fields and without a new reporting framework: the known
basis; the useful part or the uncertainty; the minimal action; the expected observable; which
decision it opens; the bounded cost/stop condition.

## Plan command contract (PLAN close)

Every command or invocation the plan freezes is **validated before gate 1** — by `pdca-executor`,
against the actual environment, with the result recorded in the status file. The contract is
**conditional on an actual command**: when the verification choice is manual observation or a
focused recomputation, the plan records that choice and does not invent a command line,
selector or argument vector to fill these rows. A plan whose decisive command cannot produce a
valid result is **not `ready`**:

- **selector resolves** — the identifier names at least one target inside the declared scope; a
  short or ambiguous identifier is rejected even when the tool accepts it and exits `0`;
- **argument vector survives the harness** — quoting, separators and redirections are recorded in
  expanded form, never as a shell alias or an unexpanded placeholder;
- **phase is legal** — an inner-phase command is not a boundary-only sweep, and a boundary-only
  command is not planned as inner work;
- **scope matches the declared host capacity** — the affected surface rather than the whole
  workspace when the host cannot carry the whole workspace;
- **expected outcome is declared** — `green`, `expected-negative`, or `informational`; "green unless
  it happens to be red" is not a declaration;
- **capture is declared** — each frozen command names a capture stem and writes three artifacts:
  `<stem>.out`, `<stem>.err`, `<stem>.rc`. A single merged log is not evidence for an exit status or
  for a negative stream criterion (empty stdout, non-empty stderr), and an empty log without `.rc`
  cannot be told apart from a run that never started. A **decisive** command also writes
  `<stem>.identity`: the SHA-256 of the input paths it declares in `identity`, taken immediately
  before the run, so the capture and the frozen snapshot resolve to the same bytes. A directory
  input digests the sorted `<sha256>  <path>` lines of its regular files, the same method for every
  executor; the plan may name a file DO creates, because gate 1 checks the shape and the capture is
  what fails if the input is still missing.
- **a documented command is a frozen command** — a user-facing invocation the result documents (a
  README's run block, a usage line, a help text) is decided in PLAN as a row of this contract, even
  though the document itself is written in DO: the command block is written *from* the row's `argv`,
  never the other way round. A criterion whose negative case names a documented command verifies it
  by running it, never by reading it — a README line that has never been executed is a claim, not
  evidence, and a documented invocation that was not run is a defect, not a limitation.
- **caches stay outside the evidence root** — a command that needs a cache, home or temp area
  (`GOCACHE`, `GOPATH`, `HOME`, `TMPDIR`, a package cache) names it in `env` outside the checkout
  (`$TMPDIR/<task>-<n>-cache` is the default target), never under the evidence root: the root holds
  evidence, and one build cache turns a 40-file evidence tree into a thousand-file pile that every
  later role listing it has to filter out.

A violation is a **PLAN defect**: gate 1 fails and `pdca-planner` revises the plan. It is never
absorbed as a recorded exception, a substituted command or a `Notice`.

## Machine projection: `commands.json` and `plan_lint.py`

The prose command block is not machine-checkable, so a plan that freezes commands also emits a
**projection** at `<evidence-dir>/inputs/commands.json` (same attempt child as the contract):

- `task` and `plan_r` (required); `checkout`, `evidence_root`, `units`, `criteria`, `host_budget`,
  `integration_boundary_runs` (optional);
- one object per command: `id`, `phase` (`inner | boundary | any`), `kind`
  (`unit | integration | build | mutation | docs | other`), `argv[]`, `cwd`, `env`, `expected`
  (`green | expected-negative | informational`), `expected_identity`, `log`, `timeout_s`, `covers`,
  `decisive`, `identity`, and for a mutation row a `harness_probe` or a declared `fallback` — `log` is
  the capture **stem**, and the `.out`/`.err`/`.rc` artifacts beside it carry the facts a criterion
  claims.

`criteria` lists the plan's required criterion IDs; `decisive` names the criteria a row decides.
**One row decides a criterion**, the rest are pointers — a plan whose prose calls `T2`, `T3` and `T4`
decisive for the same criterion has drifted, and the projection is where that becomes checkable:
`plan_lint` rejects a criterion decided by two rows, a declared criterion with no deciding row, an
`informational` row marked decisive, and a decisive row without a capture stem or without `identity`.
An empty `decisive` array is the same as omitting the key, and a declared input that does not exist
yet is only a warning: the plan names what the run consumes, and DO creates it before the capture.
`covers` keeps naming units, so a plan with no unit table declares its criteria in `criteria`, never
in `covers`.

`pdca-executor` stages `plan_lint.py` into `.pdca/scripts/` (§Helper staging) and runs it **before
gate 1** and **again on DO entry** after re-anchoring:

- `python3 .pdca/scripts/plan_lint.py check --repo <checkout> --commands <projection> --receipt
  <evidence-dir>/plan_lint.json` — schema, argv shape, phase and scope legality, expected outcome,
  evidence binding to the linted checkout, the one-row-per-criterion mapping, unit coverage;
- `python3 .pdca/scripts/plan_lint.py probe …` — additionally runs each `harness_probe` from an
  allow-list (`git`, `python3`, `go`, `gofmt`), timeout-bounded, never the planned command;
- `python3 .pdca/scripts/plan_lint.py schema` — prints the projection shape, so the executor writes
  `commands.json` from it instead of reverse-engineering the helper source;
- `python3 .pdca/scripts/plan_lint.py fork-attempt --commands <old projection> --output <new
  projection> --from c<N>-r<r>-n<old> --to c<N>-r<r>-n<new>` — copies a frozen projection into the
  next attempt child, rewriting only the `attempts/<old>` segment. A new attempt keeps the frozen
  plan; re-deriving the paths by hand is how a capture lands in the previous attempt.

Exit codes `0` ok, `2` violation, `1` usage/operational. A nonzero `check` **is** a gate-1 failure;
the receipt is the evidence row `PLAN-LINT` (path + exit). The check proves a command is well-formed
and resolvable, not that its row passes — that stays with CHECK. A plan that freezes no command
(§Plan command contract) emits no projection; a plan that freezes a command and ships **no**
projection is a PLAN defect and fails gate 1, never an accepted variation — the `PLAN-LINT` receipt
is part of the plan's evidence, and until it exists there is no candidate to check.

A language overlay may extend the schema and the probe allow-list; it never narrows these rows.

### Status lint: `status_lint.py`

The same staging rule covers the durable status file. The plan stages `status_lint.py` into
`.pdca/scripts/` and freezes a `STATUS-LINT` command row, run **after the status file is written**
and **again in ACT before finalization**:

- `python3 .pdca/scripts/status_lint.py check --repo <checkout> --status
  .pdca/status/<task>-<N>.md --receipt <evidence-dir>/status_lint.txt` — required sections, the
  durable-state block (`N`/`r`/`n`/`rv`/form/overlay/mode/`Status`/`Phase`), the closed-cycle
  sections once the cycle closes, one claims row per claim ID, every progress-log line in the frozen
  shape `<UTC> | <phase> | revision r<n> | iteration <n>/3 | <event> | <pointer>` (a leading list
  bullet is tolerated), and no event that
  restates the file's own log-line count (`9 log lines`): such a line is stale the moment the next
  event is appended, so the receipt carries the counts and the line carries the pointer;
- `python3 .pdca/scripts/status_lint.py schema` — prints the durable-status shape, including the
  section-matching rule and the log-line column rule, so the executor writes the file from it
  instead of reading the helper source.

A `##` heading inside a fenced block is body text: the plan document copied into `## Plan` carries
its own headings, and none of them may shadow a required section. The copy is fenced with at least
four backticks (longer than any fence inside it), so section order in the file never matters. A role
that appends or reads state, claims or the log opens the file at `## Durable state`; the fenced copy
above is the plan for the one reader that needs its verification methods, and the others do not
re-read it.

Exit codes `0` ok, `2` violation, `1` usage/IO; the receipt is the evidence row `STATUS-LINT`. The
helper is structural: it proves the durable record is machine-readable and consistent with itself,
never that its conclusions are true. A violation is corrected as bookkeeping in the same edit, and
the corrected file is checked again.

## Workspace tracking

The status files under `.pdca/status/` are the durable record and belong in the index — a status
file that never leaves the working tree has no handoff. Evidence and staged helpers are local
by-products: `.pdca/*/rv*/` (frozen manifests, logs, per-row artifacts) and `.pdca/scripts/`
(runtime copies of the installed helpers) stay out of the index. The install docs ship the ignore
snippet.

## Vacuous and expected-negative runs

A run that discovers or selects **zero** targets is a **failed** run, whatever its exit status.
Exit `0` with zero selected targets, zero executed cases or an empty result set is **not** evidence
of success: the executor records the observed count and the run is re-planned. Every decisive run
names its minimum selected count.

A decisive negative arm is declared `expected-negative` in the contract together with the exact
expected failure identity (the status/message and the target it belongs to). Such a run is `met` on
its observed expected outcome; a "final run must be green" rule cannot override it, a negative run
is never silently repeated until it turns green, and a negative run without the declared identity
is a failure.

## Recorded exceptions: catalog and repetition threshold

A verdict may accept a recorded exception only from a fixed catalog, each with a required shape:

- **environment/infrastructure** — the failure and the recovery, both logged, plus the affected
  command;
- **tooling incompatibility** — the tool's own error output and the supported substitute that was
  actually used;
- **scope/resource policy** — the authority that imposed the limit and the command it affects;
- **historical provenance** — the artifact identity and why it cannot be re-executed.

Every exception names its class, the affected row, the evidence pointer and the substitute. A class
that appears in **three or more units of one campaign** is a **systemic defect**: it is filed once
as its own issue and the mechanism is fixed, instead of a fourth exception being recorded. A PASS
introduces no new exception class; `pass-with-recorded-exceptions` is a diagnostic verdict, never
the default.

## Re-anchoring at DO entry

A plan written against an earlier snapshot drifts when sibling work lands. On DO entry, before the
first edit, `pdca-executor` re-resolves every planned anchor and records the result:

- **cosmetic drift** — line numbers or moved declarations with the same identity → a `Notice` with
  the old→new pointers; no revision;
- **semantic drift** — changed footprint, contract, symbol or behavior → DO → PLAN, a genuine
  revision.

A plan may not execute stale anchors, and cosmetic drift may not manufacture a revision.

## Proportional planning and effort policy

PLAN depth follows risk, not ceremony: a small, well-understood change gets a compact plan; the full
contract belongs to a change whose mechanism is unproven or whose blast radius is wide.

**PLAN chooses the approach; DO develops the deliverable.** The plan fixes the approach, the
nearest justified action, criteria/evidence, bounds and stop condition. It may carry the reasoning
or calculation needed to choose the approach, but it does not pre-write the final artefact or solve
every unresolved downstream choice. In the incremental form the first step resolves the leading
unknown, later work stays conditional on its result rather than a full speculative backlog, and one
increment may finish the goal. Do not change to incremental merely to excuse a larger plan; a
compact ordinary plan is still correct for a known bounded task.

**Order of work.** The nearest action resolves the decision-critical feasibility question —
mechanism, geometry, envelope, algorithm — before dependent artefacts expand, **when the decision
actually depends on it**. This is an ordering rule, not an extra gate: a known method or a
theoretical request needs no additional feasibility phase, and no physical experiment is forced.
Carry assumptions as assumptions, not as evidence that the mechanism works; a newly refuted
mechanism or feasible-region conflict is returned to PLAN promptly instead of polishing an unchanged
plan. One candidate class or prototype never proves the whole goal impossible.

For a measurable target whose mechanism is **not yet demonstrated**, PLAN first authorises a
**bounded probe** — one question, one observable answer, the evidence that decides it — and writes
the acceptance contract only afterwards. A campaign whose measured result cannot reach the target
STOPs only on a verified irreducible gap for the **agreed goal**, not because one candidate class
failed and not merely because the current mechanism failed; if alternatives remain, that is
decision-relevant knowledge → PLAN before another full rewrite, not a STOP. It does not buy another
revision hoping for a different number.

**Revision accounting.** A revision is genuine only when the tasks/remediation actions actually
change while the original criterion is preserved; a rename, a session reset or a rejected candidate
is not a revision and does not reset `n`. Each revision records the outgoing failed attempt first.
A new step resets no counter, history or accounting entry, and an unaccepted red step is never
converted into extra accepted progress.

## Effort and time policy

**Autonomous mode has no task cutoff.** The planner does not generate a wall-clock, token, cost,
compute, revision, step or measurement quota that terminates the task, and no legacy plan, resume or
probe budget is revived as one. Elapsed time, tokens and cost are recorded accounting only: an
estimate (for example `~45 min`) is not a stop condition, and reaching it does not stop work.

Work ends normally on an accepted result and goal completion; otherwise it stops only for a verified
irreducible blocker, a security/permission boundary, or explicit user cancellation. A failed
candidate or incomplete evidence is **not** an irreducible blocker: it goes to the step boundary —
repair, a genuinely revised plan, or a STOP recorded on the actual evidence.

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
command, not a terminal workflow STOP. The no-4th rule and recurrence escalation stay per defect;
they are never converted into an overall work quota. No new budget schema, role or mode is added.

This policy orders work and records effort; it is **not** an unconditional feasibility gate. A known
or theoretical task is not forced into a physical experiment, and the absence of a cutoff never
means endless work: an accepted result ends the task normally.

## Plan-to-DO fidelity

The initial admission **and every follow-up DO handoff** carry the plan's verification choice,
prohibitions and scope by reference to the frozen plan — never an invented criterion, method or
rationale. A brief that needs another means (a checker, script, experiment or wider scope), or a
**refuted assumption or wrong method**, is a pending PLAN decision until the planner revises the
plan; the executor returns the exact mismatch rather than obeying newly-added scope. The driver
returns such a request to the planner and does not reinterpret the goal or judge whether a custom
checker is necessary. No new report schema or general validator is introduced for this.

## Frozen evidence manifest

One object reconciles CHECK with DO: a single machine-readable **evidence manifest**. DO writes it
at the path PLAN pins in the status file; CHECK reads it first. The path is a **gate-1 field**: a plan
that pins no manifest path does not pass gate 1, and no CHECK is dispatched until DO has written the
manifest. The plan also names the **observation route** — which role observes a deliverable that
lives outside `.pdca/**` (it is `pdca-scout`, at the deliverable's own path; the scout **writes its
pack itself** at the pinned path `.pdca/<task>/rv<k>/attempts/<c-r-n>/observation-pack.md`, so no
other role copies it). A candidate with no manifest is not reported as a candidate — the
same rule as the `PLAN-LINT` receipt, and for the same reason: the index is what makes the evidence
reachable without the author's summary. It is **frozen at the
DO→CHECK boundary** and bound to the frozen result identity (plan revision `r` + the frozen
input/artefact identity, e.g. commit/tree or output hash) **and to an immutable evidence generation**
keyed by `task/N/r/n` + that frozen identity. The generation is an evidence-snapshot identity, **not**
the criterion revision `rv`: `rv` belongs to criteria/plan, the generation distinguishes successive
attempts. During CHECK the **same generation** is append-only: a re-gather adds evidence or an
`open` reason to existing entries; entries are never rewritten and no second manifest is started.
**CHECK never writes**: it returns the disposition decision and the exact append instruction;
`pdca-executor` writes it into the same canonical manifest, and CHECK reconciles the durable result.
A new plan revision starts a new manifest generation; the superseded one is kept. A **CHECK → DO**
return under an **unchanged plan** also starts a **new immutable generation** for the new
attempt/snapshot — the prior generation is retained — even though `r`/`n` follow the base counters
(no fake replan or reset is introduced for the sake of a new file). The new attempt child's
projection is produced by `plan_lint.py fork-attempt`, never by editing paths by hand; the plan
text, criteria and `argv` semantics stay frozen. Each entry maps one **required
criterion ID** to its evidence **by reference, not by copy**:

- `task`, `revision`, `status_file`, `required` — the mandatory criterion IDs (acceptance criteria
  / unit criteria) of the pinned plan;
- `rows[]` — one per required ID: `id`, `status` (`met` | `open` | `na`), and for `met` an
  `evidence[]` of `{kind, path, command?, exit?, value?, identity?, decisive?}` (path, command, exit
  status, key number, the `identity` capture that binds the run to the inputs it consumed, and
  `decisive: true` on the row that decides the criterion); for `open` a `reason`; for `na` an
  observed `predicate`. A row whose evidence is a `pdca-scout` observation uses `kind: observation`
  and the pack's path. Exactly one evidence entry per criterion is marked `decisive`; the rest stay
  pointers.

Every `required` ID must appear; a criterion without a resolving reference is `open`, never dropped,
and logs stay references — the manifest is a thin index, not a copy. **No PASS while any
BINDING/APPLICABLE `required` entry is `open`.** If the project ships a manifest validator, run it
(row completeness + shape).

**The deliverable keeps the path the goal names.** Moving it into `.pdca/**` so that the checker can
read it is a **changed goal**: the planner records a `limited` decision (normal mode: the user
approves the narrowing), the observation route covers the original path instead. A DO convenience or
a CHECK workaround never relocates the result.

**Binding/applicability disposition (append-only).** The frozen manifest is never rewritten and no
row is ever deleted: a pre-existing, self-imposed extra *audit* row stays in place with its original
`status`/text and is never quietly turned into `met`. CHECK returns an explicit applicability
disposition instruction for that row; `pdca-executor` appends it inside the same canonical manifest
— a stable row ID, the classification `diagnostic_nonbinding`, and the concrete reason/basis in the
agreed scope or the priority global rule (the plan fixes the exact field names; no second competing
manifest). CHECK then reconciles the durable row. A raw row may thus stay `open` while it is
**excluded from the set of binding acceptance blockers**: the final receipt shows binding unmet
criteria and audit notes separately, so a PASS on the genuine gates does not contradict a retained
historical audit `open`.

This path is **not a loophole**. It covers only unsupported *extra* audit demands that do not follow
from the agreed goal — a recursive historical inventory, or a retrospective/unrequested
execution-time `committed == tested`. A failing or missing required test, unverified direct
evidence, a source-copy mismatch, or a real functional/security variant stays on the normal
fail/re-gather/STOP route, and a finite audit goal the user explicitly agreed as a **separate**
audit task stays **binding**. The scope basis and reason are checked by the role decision, not
merely asserted by the author; an extra gate does not acquire normative force from the word
`frozen`. PLAN must not, on its own initiative, freeze a hard gate on arbitrary audit completeness
(a whole transitive reference graph, retrospective hashes, execution-time `committed == tested`)
for an ordinary task; such metadata belongs in the plan as separate **diagnostic notes**, and its
absence never forces `incomplete`/STOP or a new round.

**Default evidence dir:** **`.pdca/<task>/rv<k>/`** — `<task>` = kebab-slug, `<k>` = plan/criterion
revision `rv`; this is the evidence **root**. The frozen manifest, its logs and per-row artifacts of
an attempt live in a **fresh child** of that root, `.pdca/<task>/rv<k>/attempts/c<N>-r<r>-n<n>/`
(examples: `c1-r1-n1`, `c1-r1-n2`; `c<N>` is the cycle, so the next cycle never reuses the previous
child at the same `rv`/`r`/`n`). The status file records the attempt identity `task/N/r/n` plus the
frozen snapshot hash **and pins the authoritative `manifest.json` path inside that child before the
DO→CHECK boundary**. A CHECK→DO return under the same contract is the next `n` in a **new** child;
the same CHECK keeps using its own child append-only, and prior manifests are retained, never
overwritten. `rv` changes only with the criteria/contract (including a plan revision that adds a
required criterion), not with an implementation fix under the same criteria. The `.pdca/` root is
fixed (`../SKILL.md` §Workspace and durable status), the plan chooses `<task>` and `rv`. The check
role's scoped `read` grants `.pdca/**` generically, so the concrete path is defined only here.

## One evidence location binding

The evidence root and every manifest path are resolved **in the same checkout the checks run in**.
When the work happens in a secondary checkout, that checkout is the binding root: the helper's
repository argument names it and the evidence appears at the identical repository-relative path
there. There is no second "main-tree" form: a manifest whose tree cannot be recomputed from its own
`base_ref` is invalid, not an exception.

## Helper staging

Each package ships its own helpers under `scripts/`; the plan stages what the selected package
actually contains into `.pdca/scripts/` (byte-identical copies, stdlib only) before the first helper
command. The executor records the source package path, the destination paths and the copy evidence.
A required original missing from the installed package is a **resource blocker**: the executor never
generates a substitute and never runs a helper from the installed skill directory. A project fork of
a helper must be declared (path + reason) in the status file.
