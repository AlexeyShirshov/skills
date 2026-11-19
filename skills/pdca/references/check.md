# CHECK: evidence, criteria and verdict

Reference for the CHECK phase: the procedure delivered to `pdca-check`. The base contract
(`../SKILL.md`) owns the state machine, the phase exits and the host and permission boundaries; this
file holds what CHECK receives, how it verifies, and what its verdict carries.

## How this reference reaches you

The executor packages this file's **complete contents inline** in every
`pdca-check` dispatch file — the first CHECK, a recheck after DO, a campaign step and a collection item
alike. Read the `.pdca/**` handoff named by the driver through its end marker (continue partial reads).
CHECK has no permission to read the installed reference. If the complete text is absent,
truncated or visibly incomplete, CHECK returns an explicit blocker and no verdict; it does not judge
from the agent prompt alone.

## What CHECK receives

The original task, the acceptance criteria by exact reference to their source (the original task for
user-supplied criteria; the saved plan for PLAN-derived criteria), the frozen candidate's identity,
and the available evidence and observations. Later handoffs use exact references and stable
criterion IDs, not a second paraphrased criteria set. It also receives counters `N`, `r`, `n/3` from
the status, never restated from a brief or earlier turn; the **defect history** (stable defect keys,
observed revisions/attempts, applied fix count, last outcome); and, on a loop-back, the previous CHECK
report and the finding it routed. CHECK takes none of these as established: it assesses the task and
criteria itself, verifies the result against them, and treats the author's restatement as no evidence.

CHECK is read-only and judges; it runs no proving action and delegates nothing. Its file reads
are limited to `.pdca/**` for task records and evidence.
An observation or run its chosen method needs is requested through the driver, which has
`pdca-executor` produce it or `pdca-scout` observe it.

CHECK is acceptance against the recorded criteria, not a general code review. For a formal
criterion, judge the evidence that demonstrates it (for example, the build exit status or a
validator's coverage and findings). Verify software behavior with tests or direct execution of the
program or API through `pdca-executor`; source text and a successful build alone do not prove
behavior. Implementation choices are not acceptance requirements unless the user made them
requirements. If the requested result itself is not behavior (for example, documentation),
`pdca-scout` can make a targeted observation in place and report the criterion-specific finding.

## Evidence packaging

CHECK confirms the frozen candidate identity and criterion IDs, then chooses a verification method
for each criterion before judging evidence completeness. Completeness is the evidence those actual
criteria need under the chosen methods, bound to the candidate — not a pre-method audit of every
manifest link or referenced artifact. Keep the candidate in its checkout. Do not copy or stage
changed product files or diffs under `.pdca/`, or send them inline. CHECK neither requests changed
files nor treats their absence as missing evidence. Persist run logs, measurements, and targeted
observations bound to the candidate instead.

Do not inline a file inventory into the CHECK brief. For large outputs, select a criterion-specific
machine check that runs against the candidate in place.
Have DO return concise, candidate-bound results: the method, coverage (files expected and examined),
exit status, failure counts, a bounded set of actionable examples, and a pointer to the full report.
Read specific report sections only where needed to judge the criterion. Sampling is not proof of
full coverage when the criterion requires it; use a full machine check or mark it unverified.

A broken or missing link to an optional artifact unused by every chosen method is diagnostic only: it
does not delay the verdict or justify a packaging-only DO round. When a chosen method genuinely needs
evidence that is absent or inconsistent, CHECK names the affected criteria, exact missing items and
proving action, consolidating the needed evidence into one re-gather request across those criteria.
This is the existing evidence re-gather, not a product defect or counted attempt, and is subject to
the single per-criterion-per-revision allowance below — it increments neither revision nor attempt
counters and creates no extra packaging round. If required evidence remains missing after that
allowance, mark the affected criteria `unverified` and return a verdict on the evidence that exists;
an unverified mandatory criterion blocks acceptance.

## Candidate identity

DO identifies the frozen result and binds each evidence item to the inputs and conditions it actually
covers: relevant product/source, tests, build settings and outputs, runtime configuration, and
meaningful environment. Here, current evidence means applicable to the current result, not necessarily
newly executed. A commit or `HEAD` is a useful locator, not an all-purpose identity test.
Status, logs, manifests, evidence packaging and commit-only changes are bookkeeping unless they change
one of those inputs, are themselves part of the requested result/criterion, or the task explicitly
requires an exact revision. A `HEAD` mismatch alone neither invalidates the result nor requires retest
or STOP; establish relevant-input equivalence from available evidence, and use the existing bounded
evidence-gather path for a targeted clarification when it is unclear. No universal hash, manifest or
audit gate is required.

Reuse each run or artifact whose relevant inputs and conditions remain equivalent; a changed input
invalidates only the evidence that depends on it, not the whole pack. Do not repeat unrelated checks.
An explicit exact-revision requirement remains binding: evidence must cover that revision. A changed
product result still needs CHECK; a report-only change is not a product change unless the report itself
is the requested result/criterion. Keep the result identity and the evidence it supplies distinct, with
durable pointers for any evidence CHECK needs. Correcting only evidence or packaging keeps the product
result identity and does not consume an attempt.

## Assess the criteria

Before judging the result, assess the criteria against the original task: do they cover its
mandatory requirements and the explicit cycle scope, do they contradict each other or the task, is
each one judgeable? Where the user supplied the criteria, they are the acceptance set: judge against
them verbatim and do not accept the result against a different, weaker or enlarged set. Missing
coverage, contradiction or an unjudgeable criterion is a criteria defect for PLAN, not a reason to
judge the result against a weaker reading. One failed candidate is not proof that a criterion is
unachievable.

Criteria are the single source of truth: compare the handoff with their exact source (the original task
for user-supplied criteria, the saved canonical plan for PLAN-derived criteria) and refer to criteria
by their stable IDs, without creating a second wording. If the incoming dispatch has a typo, alias or
other transport distortion while the source is intact, the driver restores the exact source before
CHECK judges; a report's paraphrase is not a new criterion. This is not a PLAN revision or counter
change. A substantive defect in the saved contract
(meaning, coverage, contradiction or judgeability) follows the existing CHECK → PLAN rules. User-supplied
criteria remain verbatim and change only on explicit user instruction.

A pre-existing observation outside the explicit cycle scope is diagnostic; it does not expand a scoped
criterion. An original-task/global mandatory criterion still binds every cycle and is not waived by a
narrow local scope.

A campaign step's numeric criterion **restates the recipe's floor**: a criterion that reads a forecast
of achievable volume, a quota of work or a share of the campaign target is a criteria defect for
PLAN, not a result defect, and it is never used to refuse an increment.

A **defective user-supplied criterion is still preserved verbatim**: nobody repairs, supplements,
widens or narrows the set, and the defect never becomes a new criteria set or a DO/CHECK loop. It
resolves only as a PLAN-terminal outcome:

- a proven contradiction that makes the original task together with its supplied criteria
  unachievable → `original task is infeasible under the stated constraints`;
- an ambiguous or unverifiable supplied criterion that PLAN's authorized read-only gather cannot
  settle without changing the user's input → `acceptance criteria cannot be determined`, carrying
  that supplied set verbatim and the concrete defect/reason (the criteria are not "absent");
- missing coverage of a mandatory requirement is not permission to add a criterion: the inability to
  determine acceptance of the original task without a supplement is an explicit blocker, not an
  edit to the criteria.

A measurable goal whose value no available method computes is the same class of defect and resolves as
`goal cannot be measured under the available means`, carrying the missing metric, instrument or
comparable basis — never a proxy invented at CHECK time.

Only a **new explicit user instruction** changes the criteria, and plan approval is not one. This is
not a proactive ask-the-user detour: PLAN records the terminal outcome/blocker; it does not solicit a
rewrite.

## Verify the result

CHECK verifies that assumptions are justified and conclusions are supported by the evidence, and that
the parts of a composite result are consistent with each other. Findings for one candidate must not
be generalized to the whole goal without additional evidence.

CHECK chooses the verification method and the evidence sufficient for each criterion. Where the
original task prescribes a method, source or tool, that constraint is respected; otherwise the choice
is its own and never inherited as binding from PLAN. A successful check establishes only what its
method examined, so a criterion is judged on that, not on the report about it.

Where accepting a risky result needs a risk assessment CHECK cannot make confidently from the
evidence it has, it may consult `pdca-escalate`. The opinion returns to CHECK, which keeps the
verdict and the responsibility; the expert is not a final arbiter. The consultation protocol lives
in the base contract's §Escalation — expert review (`pdca-escalate`), which the driver manages: CHECK
reads no escalation reference itself and none is loaded on a routine CHECK.

## Recorded exceptions

An exception may be accepted only from the fixed catalog — **environment/infrastructure**,
**tooling incompatibility**, **scope/resource policy**, **historical provenance** — each with its
evidence and the substitute that covers the requirement. The same class in three or more units of
one campaign is a **systemic defect**, not a fourth exception. A PASS introduces no new exception
class.

## Matrix and findings

One row per criterion: a stable criterion ID, its status `met | unmet | unverified`, a specific basis
or reason, and the evidence pointer where one applies. Numbers appear where the criterion is
quantitative, a command and exit status where a run decided it. A row distinguishes what was
observed, what rests on an assumption and what remains unknown; evidence that resolves nothing
leaves the status `unverified`, and a missing check is not a pass. Matching result identities do not
establish content correctness.

A finding names the criterion or original requirement it concerns (by ID where one exists), its
severity, the reason and the concrete evidence, and carries its own status — `confirmed`, `refuted`,
`unverified` — separately from the criterion status.

## Verdict and routing

The verdict is `accepted` or `not accepted`, with the criteria matrix, the findings, the criteria
assessment (coverage, contradiction, judgeability), the verification limits — what was established
and what remains unknown — the next authorized transition and its reason, and the confidence and
gaps: what is verified and what remains an assumption.

**A campaign step is never refused for being small.** With an attributed net delta at or above the
campaign's floor or a decision-relevant knowledge increment, and every other mandatory requirement
met, the verdict is `accepted` **whatever the size of the increment** — even when it is far below the
plan's forecast or the campaign target. `not accepted` needs a ground that is not size: an unmet
non-volume requirement (a red test, build, convention, an un-itemized regression or a double count),
no attributed net delta (`≤ 0`) and no decision-relevant knowledge, an invalid or missing measurement,
or a criteria defect routed to PLAN. "Below the forecast" and "not enough to reach the target" are not
grounds: reachability is the campaign boundary's question, not a verdict on an increment, and the
target is never a per-step criterion. The increment stays local — `accepted` here never implies the
whole goal.

- **→ DO** — an implementation defect, or required evidence is missing while that criterion's single
  re-gather allowance remains. The report states the precise missing evidence and proving action; the
  driver has it assembled and run, and CHECK delegates nothing directly. Once the allowance is spent,
  use §Recoverable CHECK blocker after a spent allowance rather than requesting another gather.
- **→ PLAN** — a real criteria defect: criteria wrong or incomplete against the original
  requirements, contradictory, unjudgeable, or actually unachievable. A failed implementation or a
  failed verification method is not such a defect.
- **→ ACT** — the result is accepted; or the terminal case of the base contract's §CHECK and
  §Escalation — expert review (`pdca-escalate`): the current revision's attempts are exhausted and
  the mandatory expert review found no criteria defect, so ACT finalizes `incomplete`/`STOP` with no
  false PASS.

Counter effects and their recording stay in the base contract's §State machine and counters.
Re-gathering missing evidence is not a product defect or counted attempt; it never extends the no-4th
rule. A criterion gets **one** such round per revision. If evidence remains missing, mark it
`unverified` and return `not accepted`, naming the exact evidence, chosen method, and the first
re-gather's actual diagnostic. Missing evidence is not itself proof that the product failed.

### Recoverable CHECK blocker after a spent allowance

If the preserved diagnostic establishes a resource, capability or transport failure that prevents
producing or accessing required evidence within CHECK's existing permissions — without establishing a
failed product result or a criteria defect — report the precise resource blocker. The driver routes
recording of it to `pdca-executor`, the sole status writer, and keeps this same CHECK active under base
§Recovery with `N`, `r`, `n/3` and defect history unchanged. This is not a fourth exit or a
`CHECK → PLAN`/`DO`/`ACT` transition; no containing-form boundary is inferred as a fallback. Return
control under existing blocker handling: do not issue a second gather, poll, wait indefinitely, or
change counters.

Resume this pending CHECK only after a host notification or an authorized `pdca-executor`/`pdca-scout`
report, through existing input channels, establishes changed availability. The driver gains no read or
poll rights and does not probe for the change. CHECK may then inspect existing evidence within its
current permissions; this is not a re-gather and changes no counters. If availability has not changed,
do not redispatch CHECK. If the diagnostic or evidence shows a completed proving run that failed, judge
that result normally, never as a resource blocker. A criteria defect still follows CHECK → PLAN, and a
third failed substantive CHECK still requires the base's mandatory expert review before a fourth
attempt. Missing or unverified evidence alone is neither a substantive failure nor an ESCALATE ground.
Only a distinct, sufficiently informed low-confidence feasibility judgment that meets existing
escalation grounds may be referred through the driver; the expert's advice returns to CHECK and does
not select a transition.

## Honest limits

If a completed result cannot be verified, mark the affected criterion `unverified`. An unverified
mandatory criterion blocks acceptance.

A mandatory requirement that is `unmet` or `unverified` prevents acceptance, and the goal is not
weakened to obtain a PASS. A refuted finding stands on independently checked evidence, not on the
author's claim. A genuine user-requested scope change remains possible; it is the user's, and neither
CHECK nor approval of the agent's plan may substitute or narrow a user-supplied requirement or
criterion.

## Retrospective mode (ACT)

When the driver dispatches `pdca-check` for ACT, it runs in `retrospective` mode: a short
evidence-grounded analysis of the closed cycle, **not** a CHECK of a candidate. It produces no
verdict, no criteria matrix, no routing and no acceptance, and it never overrides the originating
outcome, acceptance, security, the no-4th rule or approvals. It creates no new check counter or
attempt and reuses the same role and effective tier (medium) as normal CHECK.

**Invocation discriminator.** The dispatch is marked `mode: retrospective` (or an equivalent explicit
marker) and carries the complete retrospective contract from `references/act.md` — this section or
the whole file — inlined in the ready handoff, together with the complete `check.md`. A driver that cannot
load either whole raises an explicit blocker before dispatch.

**Inputs.** The original task and cycle scope; the phase reports that actually ran — PLAN return(s),
DO result, the CHECK report where CHECK ran, and any terminal/STOP payload — each complete or by
exact reference, with absent evidence marked absent; counters and defect history; status, history and
evidence pointers. No CHECK is required for `PLAN → ACT` or `DO → ACT`; a missing CHECK is recorded
as `CHECK: not run`, never reconstructed. Preserve raw reports; mark absent evidence.

**Analysis.** What worked, what did not, what to do differently next time; 0–3 useful lessons is a
reasonable editorial default; transferable actionable conclusions; distinguish observed fact from
uncertain inference. `No new lessons` is valid after actual analysis. Partial evidence and limits
are transparent, especially for `STOP`. No new verification, proving or research; use existing
reports and evidence. Do not reopen accepted work, add DO work, or alter the frozen result.

**Output.** Lessons (0–3), categories, evidence pointers, limits and uncertainty, and a retrospective
completion signal. Not `accepted`/`not accepted`, no criteria verdict, no transition authority.
The driver routes; `pdca-executor` alone persists the result into `## Lessons learned`.
