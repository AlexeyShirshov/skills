# ESCALATE: expert review input and disposition

Detailed protocol for the `pdca-escalate` consultation: the driver reads this file before dispatch
and passes its protocol with the expert input. The machine, counters, phase contracts and host
permissions stay in `../SKILL.md` (§State machine and counters, §Phase contracts, §Roles and host
requirements); this file changes none of them.

## Grounds

ESCALATE is an **additional expert review** on the strong tier of a difficult or disputed decision:
not a stage of the machine, not a phase, not a new attempt, and not a substitute for a phase that
feels unsure. PLAN and CHECK keep their decisions and their authority; the expert only advises the
phase that referred the question. A **substantive judgment** with enough information to judge but
low-confidence or disputed:

1. a genuinely ambiguous requirement or criterion where guessing is unacceptable;
2. the cycle **not passing by the counter** — the attempt budget and same-defect threshold are
   defined once in `../SKILL.md` §State machine and counters and are never re-thresholded here;
3. a risky or irreversible **implementation** decision inside DO's authority, or a trade-off with
   long-lasting consequences;
4. an acceptance decision needing a **risk assessment** CHECK cannot make confidently;
5. a PLAN or DO decision still low-confidence after a targeted `pdca-scout` gather, reported as such
   by the responsible role.

Routine execution, ordinary review, fact gathering and repetitive fixes are not grounds, and missing
information never is: insufficient facts to determine criteria stay **PLAN → ACT** (as does an
original task proven infeasible), and a DO that cannot finish stays **DO → ACT** — the expert supplies
no facts the phase could not gather and is no detour. No ground creates a new authorization, approval
or permission. A contract-level ambiguity or unachievable criterion is a **CHECK finding** for
`pdca-planner` (`../SKILL.md` §Phase contracts → CHECK), which may itself ask for expert review of its
low-confidence decision.

## Input and permissions

A **narrow question** with the original task; the phase and role that ask; the criteria it touches;
the result, evidence (reused, not re-gathered), attempts, defect history and constraints. A missing
fact may be gathered by `pdca-scout` within existing permissions — not mandatory per consultation.
ESCALATE is read-only, may use that delegation, and never edits, runs state-changing work, or decides
for the phase.

## Conclusion and limits

A reasoned judgment — reasoning, facts relied on, residual uncertainty and a **recommended
disposition**; never a menu, an implementation or a product verdict. It does not accept in place of
CHECK, rewrite criteria in place of PLAN, or implement in place of DO. It returns to the **phase that
asked**; the driver forwards it without semantic re-decision and waives no gate, and that phase uses
only its own transitions (`../SKILL.md` §Phase contracts): PLAN may refine its criteria or return to
ACT; DO may implement inside the contract or hand `cannot finish` to ACT; CHECK re-examines and
routes as usual.

Expert advice never waives CHECK, never replaces a required user approval, and never widens
permissions; in **normal mode** a genuine criteria revision still needs a **fresh user approval**
before DO. A consultation allocates no extra attempt; an exhausted revision follows `../SKILL.md`
§State machine and counters.
