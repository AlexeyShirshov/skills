# CHECK: evidence, criteria and verdict

Reference for the CHECK phase: the procedure delivered to `pdca-check`. The base contract
(`../SKILL.md`) owns the state machine, the phase exits and the host and permission boundaries; this
file holds what CHECK receives, how it verifies, and what its verdict carries.

## How this reference reaches you

The driver reads this file in full and passes its **complete contents inline** in every
`pdca-check` dispatch — the first CHECK, a recheck after DO, a campaign step and a collection item
alike. `pdca-check` has no permission to read the installed reference, so this text in the dispatch
is its contract: it receives no path and no instruction to open one. If the complete text is absent,
truncated or visibly incomplete, CHECK returns an explicit blocker and no verdict; it does not judge
from the agent prompt alone.

## What CHECK receives

The original task, the acceptance criteria, the frozen actual result with its identity, and the
available evidence and observations. It also receives the counters (`N`, `r`, `n/3`) — as recorded in
the status, never as a restatement from a brief or an earlier turn — and the
**defect history** (stable defect keys, observed revisions/attempts, applied fix count, last
outcome), and — on a loop-back — the previous CHECK report and the finding it routed. CHECK takes
none of them as established: it assesses the task and the criteria itself and verifies the result
against them. The author's own restatement is not evidence.

CHECK is read-only and judges; it runs no proving action and delegates nothing. Its scoped access
stays inside the permissions it already has, on the task inputs and the cycle's evidence artifacts.
An observation or run its chosen method needs is requested through the driver, which has
`pdca-executor` produce it or `pdca-scout` observe it.

## Assess the criteria

Before judging the result, assess the criteria against the original task: do they cover its
mandatory requirements and the explicit cycle scope, do they contradict each other or the task, is
each one judgeable? Where the user supplied the criteria, they are the acceptance set: judge against
them verbatim and do not accept the result against a different, weaker or enlarged set. Missing
coverage, contradiction or an unjudgeable criterion is a criteria defect for PLAN, not a reason to
judge the result against a weaker reading. One failed candidate is not proof that a criterion is
unachievable.

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

- **→ DO** — an implementation defect, or evidence the chosen method needs is still missing. The
  report states the precise missing evidence and the proving action it requests; the driver has it
  assembled and run, and CHECK delegates nothing directly.
- **→ PLAN** — a real criteria defect: criteria wrong or incomplete against the original
  requirements, contradictory, unjudgeable, or actually unachievable. A failed implementation or a
  failed verification method is not such a defect.
- **→ ACT** — the result is accepted; or the terminal case of the base contract's §CHECK and
  §Escalation — expert review (`pdca-escalate`): the current revision's attempts are exhausted and
  the mandatory expert review found no criteria defect, so ACT finalizes `incomplete`/`STOP` with no
  false PASS.

Counter effects and their recording stay in the base contract's §State machine and counters.
Re-gathering missing evidence is not a product defect and is not a counted attempt; it never extends
the no-4th rule. A criterion gets **one** such round per revision: when its evidence is still missing
after that round, record it `unverified` and return a verdict on the artefacts that exist — the same
criterion is not sent out for a second round in the same revision, and a repeated request is itself
the signal to route to PLAN, to escalation, or to the containing form's boundary decision.

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
the whole file — inlined by the driver, together with the complete `check.md`. A driver that cannot
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
