# PLAN brief

The planner reads nothing but this brief, so **nothing travels by reference here**: facts, the goal
and the form discriminators arrive verbatim.

- **identity**: task / `N` / previous `r`, `n` / `form` (`UNDECIDED | cycle | campaign`) / requested
  overlay or `none` / control mode and the approval state
- **original goal**: verbatim, with the file or message it came from
- **facts**: the scout report verbatim, pointers included, plus the environment facts actually
  measured (never an assumed version or path)
- **package constants**: the two lint invocations are fixed by the package, not gathered per task —
  `python3 .pdca/scripts/plan_lint.py check --repo <checkout> --commands <projection> --receipt
  <evidence-dir>/plan_lint.json` and `python3 .pdca/scripts/status_lint.py check --repo <checkout>
  --status .pdca/status/<task>-<N>.md --receipt <evidence-dir>/status_lint.txt`; `plan_lint.py
  schema` / `status_lint.py schema` print the two shapes
- **form discriminators**: the `### Forms` block verbatim — the names alone are not a brief
- **decision-critical unknowns**: numbered, each with the observation that would close it
- **output**: every gate-1 field — form and rationale, overlay, nearest useful step, carrying claims
  with IDs, criteria each with a verification method, verification choice, constraints, assumptions,
  decomposition or a decision not to split, means/access, risks and stop conditions — or a replan
  with the reason the previous revision failed. A command the result will document is a frozen row,
  and a negative case that names it verifies it by running it
- **manifest**: pin `<evidence-root>/attempts/c<N>-r<r>-n<n>/manifest.json` exactly — a gate-1
  field fixed by convention, not a choice; the attempt child is the only legal location and a
  root-level `<evidence-root>/manifest.json` is a PLAN defect
- **plan document**: `<path>` — your one permitted write (`.pdca/<task>/rv<k>/plan-r<n>.md`): put the
  same plan text there, and mark the **decisive** command per criterion (the row that decides it)
  so DO can mark it `decisive: true` in the manifest
