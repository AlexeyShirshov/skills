# U1 Campaign Preparation — Revision r1 (immutable)

preparation_ref: .pdca/latency-readme/items/U1/preparation.md@r1
preparation_state: ready
collection-id: latency-readme
item: U1
form: campaign
Allowed surface: app.py only; bench.py is protected (the measurement recipe) and frozen
Protected/foreign: bench.py frozen/inspect-only; README.md belongs to U2
Effort accounting: elapsed time/measurements recorded as accounting only — no autonomous cutoff; a normal-mode user stop choice, if made, is carried by reference with its original anchor
commit_policy: none (no autocommit/merge right granted for this run; the outer collection completion commit is separate)
scope: preparation only. No baseline measured, no runtime campaign status, no step plans/step count/step overlays, no product changes.

## Goal predicate and recipe
U1 succeeds iff, on the same host and single-threaded, one credited `python3 bench.py` measurement taken after an accepted app.py-only change reports `p95_ms <= 40.00`, with bench.py's workload/recipe unchanged and no out-of-surface change. A faster number obtained by editing bench.py, changing seed/rows/runs/index, or concurrent load is invalid.

Recipe: unit = milliseconds; the p95 of 20 sequential runs, `sorted(samples)[int(0.95*(20-1))]`; denominator = the same 1500 rows and seed 7; exclusion filters = no concurrent load, no added I/O, no warmup. Thresholds 40.00 (target) and 60.00 (floor) are **provisional**: no baseline has been measured yet, so revising them on measurement is a supersede record, not a goal change and not a new campaign. A threshold backed by the measured baseline changes only as a goal change.

## Increment unit, floor and target
| Field | Exact value | Semantics |
|---|---|---|
| Increment unit | one valid recipe measurement after an accepted in-surface change, or one decision-relevant knowledge increment | What one credited step is. |
| Target | p95_ms <= 40.00 | Full success (`met`); stop. |
| Floor | p95_ms <= 60.00 | Minimum acceptable measurement; not a substitute target and it does not make the campaign `met`. |
| target = baseline + floor | target_ms = baseline_ms − floor_ms (the floor is the required drop) | Fixed at bootstrap, once the baseline is measured with this recipe. |
| Unacceptable final | p95_ms > 60.00 | Continue or revise; never claim success. |

`40.00 < p95_ms <= 60.00` is floor-only: target not met; it may be a checkpoint/stop only when no credible candidate remains, and it is not success.

No-silent-change rule: thresholds 40.00/60.00, seed 7, 1500 rows, 20 sequential runs, p95 index 18, output format, host/lane, surface, evidence paths and status semantics are immutable. Any change requires a new revision r2 with explicit reapproval; never silently reinterpreted.

## Step acceptance and credited-measurement boundary
- P1 invariants: report(rows) returns 1500 equal lists sorted by r[1]; input rows unchanged; ties preserve stable sort order; separate list objects unless evidence establishes aliasing is allowed. No benchmark/seed detection, monkeypatching, env sniffing or concurrency.
- P2: lower p95 with the smallest correct diff.
- Exactly one credited recipe measurement per step: exact `python3 bench.py`, same host, single-threaded, no warmup, no added file/network I/O; evidence includes command, cwd, host, Python version, UTC, exit code, full stdout/stderr and parsed p95_ms.
- Accepted for advancement iff the measurement is valid, P1 checks pass, and p95_ms is strictly below the last accepted p95 (baseline before the first step). Equal or worse valid results are rejected.
- The floor is a final/stop gate, not a per-step gate: an intermediate step may be accepted for advancement while above the floor if it strictly improves.
- No re-roll for a prettier number: once a valid measurement is written, it is final for that code state; do not re-run to replace it.
- Invalid measurement: wrong command/environment, concurrent load, bench.py change, unparseable output or missing evidence. Record it; no credit and no automatic rerun. The same step identity may be revised after the cause is fixed; this is not a re-roll of a valid result. Persistent invalidity = blocked.
- A knowledge increment (a rejected candidate that yields decision-relevant knowledge) is credited as knowledge, not as a failed measurement; no rule demands a second increment once the goal is satisfied and checked.
- Functional lens/guards: output length 1500; each list sorted by r[1]; stable ties; input not mutated; repeated calls with same object; independent lists. Other input sizes/empty input are deferred with trigger "if the code path changes".

## Carrying claims and definition of done
- Carrying claims: CC-1 the credited measurement is valid by the recipe; CC-2 bench.py is unchanged (hash-verified); CC-3 the change is inside app.py only; CC-4 report(rows) keeps its functional contract. A `confirmed`/`unverified` finding against any carrying claim forbids PASS and `met` at any rubric score.
- Definition of done: the whole-goal CHECK passes on the accepted state — the goal predicate is true, no carrying claim blocks and the original requirement is verified. A separate final check adds no planner call: its brief and pre-set STOP condition are issued at the last step boundary.
- Exit surface on the outside of the goal: `blocked` for a missing host/executor/evidence; a surface violation is stop/reapprove, never a lowered threshold.

## Boundaries / surface reservation
- Reserved surface: app.py. Only app.py may carry the performance change; bench.py is protected/foreign (inspect-only, frozen: seed, row count, timing, p95 formula, output, I/O).
- Any edit outside app.py, any credited step editing bench.py, or U1 touching README.md = surface violation -> stop/reapprove.
- No parallel measurement, no additional benchmark harness, no changing the recipe to improve the number.
- U2 owns README.md only.

## Dependencies
- None between items. U1 and U2 are independent.
- Order: preparation r1 -> ALL-barrier -> baseline bootstrap -> last accepted step -> next step chosen from that measurement.
- Single-threaded throughout; no parallel measurement.

## Resources / non-conflict
- One host, one campaign lane, one measurement at a time; host quiesced during measurement.
- Item mode: sequential single lane; no worktrees. U2 only touches README.md, so surfaces do not overlap.
- Toolchain: only python3 bench.py; no build, lint, test suite, CI or coverage threshold exists.
- Lenses: equality/shape, aliasing/input mutation, stable tie order, determinism, surface compliance, performance. Executor records evidence; review checks it.
- Docs plan: U1 none; U2 README.md only.

## Advancement
The next step is chosen only from the last accepted measurement, by one planner call at the step boundary. No precommitted step list, order or count.
First-step candidate list (not a plan; unordered):
- Single sort once, then reconstruct 1500 equal independent lists, preserving output semantics and alias behavior.
- Cache the sorted result by a stable input key, with correct invalidation; no benchmark-specific detection.
- Row/key normalization once at ingress, preserving stable ties and not mutating input.
- Data-layout change: decorate with r[1], sort once, reconstruct output.
No separate reconnaissance: the baseline measurement is the discriminator; select the next approach from it. Perf measurement is only the credited recipe; no separate harness.

## Stop rules and bootstrap protocol
Bootstrap precondition: ALL-barrier passed, preparation_state=ready, no baseline and no campaign runtime status yet. Baseline bootstrap runs after the ALL-barrier and before the first step DO by a dedicated pdca-executor.
Baseline bootstrap:
- Run the same recipe exactly: python3 bench.py, same host, single-threaded, one baseline credit; no warmup, no added I/O.
- Exact baseline fraction: p95 over 20 samples = sorted(samples)[int(0.95*(20-1))] = sorted(samples)[18] — second-highest sample, no interpolation.
- Evidence path: .pdca/latency-readme/items/U1/evidence/baseline.txt — command, cwd, host, Python version, UTC, exit code, full stdout/stderr, parsed p95_ms, fraction/index.
- A single invalid baseline attempt is recorded and does not establish baseline; retry only after fixing the cause. Persistent invalid baseline = blocked.
- Baseline bootstrap creates the campaign runtime status at .pdca/status/U1-campaign.md with Status: running and preparation_ref: .pdca/latency-readme/items/U1/preparation.md@r1. It is not a step and is not credited as a gain; it does not change the product or copy this preparation.

Stop rules:
- Met: valid accepted measurement p95_ms <= 40.00 -> stop success.
- Floor-only: 40.00 < p95_ms <= 60.00 and no credible candidate remains -> stop floor-only, never relabel as target success; final disposition is not `met`.
- Unreachable: seed candidates exhausted and last accepted p95 remains > 40.00 with no new evidence -> stop; do not lower thresholds.
- Blocked: missing host/executor/evidence or unresolved semantic blocker requiring new preparation.
- Surface violation: outside files touched, bench.py changed, concurrent measurement or cross-lane run -> stop/reapprove.
- Baseline may be > 60.00; it is a starting value, not a threshold change. Never lower thresholds.

## Schedule-compatibility evidence
- Single-threaded, no file/network I/O in bench.py; one measurement at a time.
- Declared status/evidence paths: item preparation status .pdca/status/U1-preparation.md; future campaign runtime .pdca/status/U1-campaign.md; baseline evidence .pdca/latency-readme/items/U1/evidence/baseline.txt; step evidence .pdca/latency-readme/items/U1/evidence/step-<n>.txt.
- No hidden reverse order: baseline precedes the first step; each next step follows the last accepted measurement.
- Predictable runtime-status read point: only at a step boundary after the executor writes measurement evidence and status; never mid-run.
- The step boundary decides: one planner call per boundary, an accepted/revised/new step or a STOP; no step-kind catalogue.
- U1/U2 are disjoint; U2 only touches README.md.

Gaps/assumptions/risks: report() list-identity/aliasing is not stated — preserve 1500 independent lists as a P1 risk unless evidence says otherwise. Baseline is intentionally unknown; target may be unreachable. Bench has no warmup, so one valid measurement is final and noise is not "fixed" by re-rolling. No tests/CI exist; functional checks are executor/check lenses, not a test suite. README.md is absent and belongs to U2. Confidence is high on process compatibility; performance reachability is unknown until baseline.
