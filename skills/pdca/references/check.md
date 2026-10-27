# CHECK: evidence, claims and verdict

Reference for the CHECK phase. Independence and the gates stay in `../SKILL.md`; this file holds
what the verdict must contain and how a finding is bound.

## What CHECK receives

The brief (criteria, carrying claims, the frozen result identity) plus the `pdca-scout`
observation; the checker may open the cycle's own evidence artifacts under `.pdca/**` directly
(status, manifest, logs) — never the product artefact. The author's own restatement is not
evidence.

## Premises and inference scope

Before arithmetic or content consistency, CHECK validates the **central definitions, units, model
assumptions and inference scope**: which quantities come from the supplied model and which are new
assumptions. An independent family or model alone does not guarantee independent premises.
Agreement of arithmetic proves only the arithmetic: an invalid equality or an assumed relationship
that the supplied model does not support is a finding, never proof that the specification is
impossible. An unverified model or premise stays `unverified`; estimates are legitimate when the
source allows them, and empirical proof is not demanded for every estimate. Scope claims must match
the evidence class: a ceiling, failure or impossibility shown for one candidate class or prototype
limits **that class** only, never the whole goal without evidence covering the goal.

## Decisions already made

A decision recorded by escalation — including an audit or metadata gate classified
`diagnostic_nonbinding` under the existing rules — stays decided. A later CHECK, planner call or
driver does not resurrect it; reopening requires new evidence and the planner's explicit revision.
Applicability dispositions never waive a genuine required test, security check or direct evidence.

A denied specific operation proves only that the operation was rejected — not that a capability or
tool is absent. Inspect the role's known permissions and its directly available built-in tools; do
not reattempt the denied operation, do not hunt MCP servers for a substitute, and do not widen any
role. Assign the evidence to a role whose known permissions can satisfy it.

## Criteria matrix

For **every** criterion: `met | unmet | unverified`, with the evidence pointer that resolves it and,
for a decisive run, the command, exit status and key number. **The absence of a check is NOT a
pass.** A verdict that rests on no numbers is **Verifier Theater** and is worthless. A claim without
a resolving reference is `unverified`, not `met`.

The matrix distinguishes what was observed, what rests on an assumption, and what remains unknown.
Successful verification establishes only what its method examined; matching result identities do not
establish content correctness or consistency between renderings of the same content.

## Findings

Each finding names its severity, the **carrying-claim ID** it touches, the affected row and the
evidence pointer, and gets one status:

- `confirmed` — reproduced/observed with evidence;
- `refuted` — objectively contradicted by evidence reproduced by a non-author;
- `unverified` — plausible or unresolved, but not established.

A finding that touches a mandatory criterion but is bound to no ID counts as **carrying** until the
planner labels it.

## Carrying claims and the veto

A `confirmed` or `unverified` finding against a carrying claim **forbids PASS and final `done` at
any rubric score**, and forbids a STOP with `done`. With several judges, a block from any one of them
blocks the result; the score aggregate (for example `min`) concerns only quality axes. A rubric rank
above the threshold, or a comfortable margin over it, compensates nothing.

Removing the block has exactly three paths, chosen by the planner at the step boundary:

1. fix and re-check;
2. objective refutation with evidence reproduced by a non-author — CHECK confirms the refutation;
3. explicit narrowing of the result inside the original goal, recorded as `limited`, not `done`
   (normal mode: the user approves the narrowing).

Moving the finding to "next step" does not remove the block. The model may not weaken the original
goal to clear a block. An unsupported allegation is not truth by itself: it requires adjudication,
not merely a point deduction; and an unknown claim stays non-PASS / not `met` — the previous rule is
not cancelled. Rubric quality rank and hard validity requirements are different things.

The decision is recorded with why the finding blocks, or why a refutation removes it. ACT only
records the decision.

## Local and whole-goal checks

- **Every increment candidate** before acceptance gets an independent `pdca-check`, limited to the
  increment's claims and the affected invariants. Observe/Judge independence and the existing gates
  apply as needed; medium CHECK rights are not widened.
- CHECK is **not** run per tool/probe: several related probes in one increment give one CHECK.
- The step check is local to the new claims. The **final CHECK of the whole goal** is separate and
  is not a full audit of every increment. Completion of the whole goal requires an integrated check
  of the original requirements: a set of accepted increments and PASS on every mechanical gate row
  does not prove the whole goal.
- **Combination.** When the candidate claims to close the whole goal, the increment CHECK and the
  final integrated check are **one session** covering the whole goal. A second isolated judge runs
  only on an explicit trigger: the margin over the rubric threshold is no larger than a value
  declared in the PLAN, an unresolved finding against a carrying claim, or an operator/plan
  requirement. By default there is no second judge.

## Verdict and routing

Report:

- **verdict** — accepted / not accepted;
- **criteria matrix** and the **claims status** (`confirmed` / `refuted` / `unverified` per ID);
- **findings** with severity and evidence pointers;
- **verification limits** — what was established and what remains unknown;
- **correction routing** — implementation defect → DO; wrong or unachievable contract → PLAN;
  a completed candidate that cannot be accepted and has no viable contract correction → ACT
  finalizes the honest `incomplete`/STOP outcome;
- for a re-gather: the exact **append instruction** for the same canonical manifest (CHECK never
  writes).

A CHECK → DO return of revision `r` grows `n/3`; a return to PLAN does not. A missing required
report is re-gathered, not counted as an invented defect.

## Honest limits

CHECK judges only a **completed** candidate: a DO that cannot finish goes directly to ACT and is not
sent to CHECK. When confirmation is impossible for a completed candidate, the verdict says so:
`unverified` or STOP under the existing rules, finalized in ACT — without an invented probability and
without weakening the criterion. A requirement the observer's permissions cannot satisfy is marked
`unverified-by-design` by the PLAN, or assigned to a role that can satisfy it; a denied specific
operation proves only that operation was rejected, not that the tool is absent, and it is not retried
or worked around by widening permissions.
