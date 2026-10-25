# PLAN: fields, commands, evidence and calibration

Reference for the PLAN phase. Read it when the plan is composed or revised; the gates themselves
stay in `../SKILL.md`.

## Plan fields (gate 1)

- goal and expected result;
- declared **form** (ordinary cycle / incremental / collection) and **overlay** (none, coder,
  coder+.NET), with a one-line reason tied to what is known and what is not;
- constraints; assumptions;
- acceptance criteria, **each with a verification method** and a negative case;
- **carrying claims** with IDs — the central claims of the goal, mandatory criteria and hard
  validity constraints — listed separately from quality-rubric axes;
- decomposition into units with dependencies, or an explicit decision not to split a simple task;
- the **nearest useful step** and its observable result;
- means and access;
- risks and stop conditions;
- stop-loss budget (wall clock / revisions / measurements).

For a campaign step the same fields are narrowed to that step, while the whole goal, requirements
and constraints stay stored; a full backlog is not imitated.

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

No bespoke verifier or coverage audit "because we can build one": the
plan needs a rationale for the current decision and the cheapest sufficient method. A custom
checker is allowed when the PLAN justifies why existing means and manual checking of the carrying
claims are insufficient, and its size is proportional to the artefact under check. A full future
verification infrastructure is not the default at the start.

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
against the actual environment, with the result recorded in the status file. A plan whose decisive
command cannot produce a valid result is **not `ready`**:

- **selector resolves** — the identifier names at least one target inside the declared scope; a
  short or ambiguous identifier is rejected even when the tool accepts it and exits `0`;
- **argument vector survives the harness** — quoting, separators and redirections are recorded in
  expanded form, never as a shell alias or an unexpanded placeholder;
- **phase is legal** — an inner-phase command is not a boundary-only sweep, and a boundary-only
  command is not planned as inner work;
- **scope matches the declared budget** — the affected surface rather than the whole workspace when
  the host cannot carry the whole workspace;
- **expected outcome is declared** — `green`, `expected-negative`, or `informational`; "green unless
  it happens to be red" is not a declaration.

A violation is a **PLAN defect**: gate 1 fails and `pdca-planner` revises the plan. It is never
absorbed as a recorded exception, a substituted command or a `Notice`.

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

## Proportional planning and stop-loss

PLAN depth follows risk, not ceremony: a small, well-understood change gets a compact plan; the
full contract and the measurement budget belong to a change whose mechanism is unproven or whose
blast radius is wide.

For a measurable target whose mechanism is **not yet demonstrated**, PLAN first authorises a
**bounded probe** — one question, one observable answer, a fixed budget — and writes the acceptance
contract only afterwards. A campaign whose measured result cannot reach the target STOPs with the
measured gap; it does not buy another revision hoping for a different number.

**Revision accounting.** A revision is genuine only when the tasks/remediation actions actually
change while the original criterion is preserved; a rename, a session reset or a rejected candidate
is not a revision and does not reset `n`. Each revision records the outgoing failed attempt first.
A new step does not reset the global budget or history, and an unaccepted red step is never
converted into extra accepted progress.

## Frozen evidence manifest

One object reconciles CHECK with DO: a single machine-readable **evidence manifest**. DO writes it
at the path PLAN pins in the status file; CHECK reads it first. It is **frozen at the DO→CHECK
boundary** and bound to the frozen result identity (plan revision `r` + the frozen
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
(no fake replan or reset is introduced for the sake of a new file). Each entry maps one **required
criterion ID** to its evidence **by reference, not by copy**:

- `task`, `revision`, `status_file`, `required` — the mandatory criterion IDs (acceptance criteria
  / unit criteria) of the pinned plan;
- `rows[]` — one per required ID: `id`, `status` (`met` | `open` | `na`), and for `met` an
  `evidence[]` of `{kind, path, command?, exit?, value?}` (path, command, exit status, key number);
  for `open` a `reason`; for `na` an observed `predicate`.

Every `required` ID must appear; a criterion without a resolving reference is `open`, never dropped,
and logs stay references — the manifest is a thin index, not a copy. **No PASS while any
BINDING/APPLICABLE `required` entry is `open`.** If the project ships a manifest validator, run it
(row completeness + shape).

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
