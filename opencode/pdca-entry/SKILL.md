---
name: pdca-entry
description: "Single entry point (umbrella) for the PDCA skill family: classifies a task and hands it to exactly one contract — pdca-collection for a batch of independent tasks («список задач», «milestone»; parallel when footprints allow), pdca-incremental for a long-running campaign without a whole-volume plan («инкрементами», «маленькими шагами», «двигаемся к цели»), pdca-dotnet for .NET/C#, pdca-coder for other code, pdca otherwise. Invoke when the user asks to run a task \"by the cycle\", \"via PDCA\", \"по циклу\", \"через PDCA\", \"запусти PDCA\", or names pdca-entry; the other contracts are loaded only by explicit ID. Not for ordinary tasks."
---

# PDCA entry: the family umbrella

**You are the entry point.** Your only job is to classify the task and hand it to exactly one
contract of the family. You do not run the cycle yourself, do not edit files, do not issue a
verdict and do not keep a status file — the chosen contract owns all of that.

## Routing decision (first match wins)

| # | Signal | Contract |
|---|---|---|
| 0 | the user names a contract explicitly (`pdca`, `pdca-coder`, `pdca-dotnet`, `pdca-collection`, `pdca-incremental`) | that contract, verbatim — no re-classification |
| 1 | a known list / milestone of **independent tasks with their own goals** (a batch) — parallelism is optional | `pdca-collection` |
| 2 | **one** verifiable goal with **no whole-volume plan**, where the next step follows the previous accepted measurement (even over a known list) | `pdca-incremental` |
| 3 | .NET / C# work | `pdca-dotnet` |
| 4 | software work in another stack | `pdca-coder` |
| 5 | anything else with a verifiable result | `pdca` |

Precedence is deliberate: a .NET campaign is still a campaign (row 2) — its per-step cycle
picks `pdca-dotnet` inside `pdca-incremental`.

**A known list alone is not a campaign, and a batch does not require parallelism.** Several
independent goals → `pdca-collection`: it runs in parallel when ≥2 disjoint footprints exist and
degrades to a single sequential group when they do not (one measurement host, a host lock,
`cap = 1`). One shared goal/metric whose whole-volume plan is unknown — even across a known list —
→ `pdca-incremental` (step = task). A single shared goal whose whole plan is already known is one
cycle (rows 3–5), not a campaign. Do not choose incremental merely because a batch is serialized,
because all tasks share one footprint, or because a single goal's work is listed.

**Size alone is not a signal.** A large but plannable task is one cycle. The campaign criteria are
canonical in `pdca-incremental` §«Когда выбирать»: the goal is checkable, the path is unknown,
the steps are information-dependent, and a whole-volume plan would be a stub.

### Composition: form of execution vs. cycle variant

A batch (a collection) may contain units of two kinds: `execution_kind=cycle` (one full cycle of
its variant) and `execution_kind=campaign` (an incremental campaign with its own frame and steps).
The collection owns the batch in both cases; the PLAN of the collection decides each unit's form of
execution.

`execution_kind` and `selected_variant` are different fields: `execution_kind` says how a unit is
executed, while `selected_variant` names only a cycle contract (`pdca`, `pdca-coder`, `pdca-dotnet`)
and is never a campaign or a form of execution. A campaign has no unit-level variant: the variant
belongs to each concrete step and is chosen by the campaign by the existing selection rules.

A medium/strong primary does not drive or dispatch the cycle: it makes an explicit handoff to the
cheap primary, preserving refs. There is no re-routing after the contract starts.

## Handoff

- **Normal mode (plan approval):** load the chosen contract through the host's skill mechanism (by
  exact ID where the host supports explicit loading) and follow it; the plan approval and all gates
  happen there. The contracts are registered as manual-only where the host supports such a flag; if
  the host cannot load one, read the sibling `../<contract>/SKILL.md` and follow it — never fall back
  to another contract.
- **Autonomous mode:** for `pdca`, `pdca-coder` and `pdca-dotnet`, dispatch
  `pdca-orchestrator` with the original brief and `selected_variant: <contract>`; for
  `pdca-collection` and `pdca-incremental`, load that contract — it owns its runner and
  per-task delegation.
- Report the decision in one line (`Routing: pdca-dotnet — .NET/C# signal`) and pass it on.
  Once the contract starts, do not re-route: loop-backs (DO → PLAN, CHECK → DO) belong to it.

## Boundaries

- This skill is **not a sixth cycle contract**: no roles table, no gates, no counters, no
  status file, no model ids.
- It does not duplicate or override the chosen contract; if this text and a contract disagree,
  the contract wins.
- `pdca-collection` and `pdca-incremental` are not cycle variants — they are top-level
  contracts that delegate complete cycles to `pdca-orchestrator`.
- An ordinary task is done directly; the umbrella applies only when the user asked for the
  cycle.

## Host requirements

The role agents are shipped by the chosen variant (`assets/agents/*.md`); this skill ships the
runner `assets/agents/pdca-orchestrator.md` (the same file as the rest of the family). A cheap
primary drives the entry; a medium/strong primary does not dispatch the cycle.
