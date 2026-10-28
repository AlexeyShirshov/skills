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
available evidence and observations. CHECK takes none of them as established: it assesses the task
and the criteria itself and verifies the result against them. The author's own restatement is not
evidence.

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
assessment (coverage, contradiction, judgeability) and the verification limits — what was
established and what remains unknown — plus the next authorized transition and its reason.

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
the no-4th rule.

## Honest limits

If a completed result cannot be verified, mark the affected criterion `unverified`. An unverified
mandatory criterion blocks acceptance.

A mandatory requirement that is `unmet` or `unverified` prevents acceptance, and the goal is not
weakened to obtain a PASS. A refuted finding stands on independently checked evidence, not on the
author's claim. A genuine user-requested scope change remains possible; it is the user's, and neither
CHECK nor approval of the agent's plan may substitute or narrow a user-supplied requirement or
criterion.
