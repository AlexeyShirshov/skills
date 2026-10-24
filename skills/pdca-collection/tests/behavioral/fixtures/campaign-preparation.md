# U1 Campaign Preparation — Revision r1 (immutable)

preparation_ref: .pdca/latency-readme/units/U1/preparation.md@r1
preparation_state: ready
collection-id: latency-readme
unit: U1
execution_kind: campaign
surface: app.py and bench.py only; bench.py workload/recipe is frozen
commit_policy: none (no autocommit/merge right granted for this run; outer collection completion commit is separate)
scope: preparation only. No baseline measured, no runtime campaign status, no step plans/step count/variants, no product changes.

## 1. Goal predicate
U1 succeeds iff, on the same host and single-threaded, one credited `python3 bench.py` measurement taken after an accepted app.py-only change reports `p95_ms <= 40.00`, with bench.py's workload/recipe unchanged and no out-of-surface change. A faster number obtained by editing bench.py, changing seed/rows/runs/index, or concurrent load is invalid.

## 2. Target/floor criteria
| Criterion | Exact value | Semantics |
|---|---|---|
| Target | p95_ms <= 40.00 | Full success (met); stop. |
| Floor | p95_ms <= 60.00 | Minimum acceptable outcome (floor_met); not a substitute target; does not make the campaign `met`. |
| Unacceptable final | p95_ms > 60.00 | Continue or repair; do not claim success. |

`40.00 < p95_ms <= 60.00` is floor-only: target not met; it may be a checkpoint/stop only when no credible candidate remains, and it is not success.

No-silent-change rule: thresholds 40.00/60.00, seed 7, 1500 rows, 20 sequential runs, p95 index 18, output format, host/lane, surface, evidence paths and status semantics are immutable. Any change requires a new revision r2 with explicit reapproval; never silently reinterpreted.

## 3. Step acceptance and credited-measurement boundary
- P1 invariants: report(rows) returns 1500 equal lists sorted by r[1]; input rows unchanged; ties preserve stable sort order; separate list objects unless evidence establishes aliasing is allowed. No benchmark/seed detection, monkeypatching, env sniffing or concurrency.
- P2: lower p95 with the smallest correct diff.
- Exactly one credited recipe measurement per step: exact `python3 bench.py`, same host, single-threaded, no warmup, no added file/network I/O; evidence includes command, cwd, host, Python version, UTC, exit code, full stdout/stderr and parsed p95_ms.
- Accepted for advancement iff the measurement is valid, P1 checks pass, and p95_ms is strictly below the last accepted p95 (baseline before the first step). Equal or worse valid results are rejected.
- The floor is a final/stop gate, not a per-step gate: an intermediate step may be accepted for advancement while above the floor if it strictly improves.
- No re-roll for a prettier number: once a valid measurement is written, it is final for that code state; do not re-run to replace it.
- Invalid measurement: wrong command/environment, concurrent load, bench.py change, unparseable output or missing evidence. Record it; no credit and no automatic rerun. A separately declared repair/verify step may retry after the cause is fixed; this is not a re-roll of a valid result. Persistent invalidity = blocked.
- Verify steps supply missing/invalid evidence only; they cannot replace a valid best or create a new best.
- Functional lens/guards: output length 1500; each list sorted by r[1]; stable ties; input not mutated; repeated calls with same object; independent lists. Other input sizes/empty input are deferred with trigger "if the code path changes".

## 4. Boundaries / surface reservation
- Reserved surface: app.py and bench.py. Only app.py may carry the performance change; bench.py is inspect-only and frozen (seed, row count, timing, p95 formula, output, I/O).
- Any edit outside these two files, any credited step editing bench.py, or U1 touching README.md = surface violation -> stop/reapprove.
- No parallel measurement, no additional benchmark harness, no changing the recipe to improve the number.
- U2 owns README.md only.

## 5. Dependencies
- None between units. U1 and U2 are independent.
- Order: preparation r1 -> ALL-barrier -> baseline bootstrap -> last accepted step -> next step chosen from that measurement.
- Single-threaded throughout; no parallel measurement.

## 6. Resources / non-conflict
- One host, one campaign lane, one measurement at a time; host quiesced during measurement.
- Unit mode: sequential single lane; no worktrees. U2 only touches README.md, so surfaces do not overlap.
- Toolchain: only python3 bench.py; no build, lint, test suite, CI or coverage threshold exists.
- Lenses: equality/shape, aliasing/input mutation, stable tie order, determinism, surface compliance, performance. Executor records evidence; review checks it.
- Docs plan: U1 none; U2 README.md only.

## 7. Advancement
The next step is chosen only from the last accepted measurement. No precommitted step list, order or count.
First-step candidate list (not a plan; unordered):
- Single sort once, then reconstruct 1500 equal independent lists, preserving output semantics and alias behavior.
- Cache the sorted result by a stable input key, with correct invalidation; no benchmark-specific detection.
- Row/key normalization once at ingress, preserving stable ties and not mutating input.
- Data-layout change: decorate with r[1], sort once, reconstruct output.
No separate reconnaissance: the baseline measurement is the discriminator; select the next approach from it. Perf measurement is only the credited recipe; no separate harness.

## 8. Stop rules and bootstrap protocol
Bootstrap precondition: ALL-barrier passed, preparation_state=ready, no baseline and no campaign runtime status yet. Baseline bootstrap runs after the ALL-barrier and before the first step DO by a dedicated pdca-executor.
Baseline bootstrap:
- Run the same recipe exactly: python3 bench.py, same host, single-threaded, one baseline credit; no warmup, no added I/O.
- Exact baseline fraction: p95 over 20 samples = sorted(samples)[int(0.95*(20-1))] = sorted(samples)[18] — second-highest sample, no interpolation.
- Evidence path: .pdca/latency-readme/units/U1/evidence/baseline.txt — command, cwd, host, Python version, UTC, exit code, full stdout/stderr, parsed p95_ms, fraction/index.
- A single invalid baseline attempt is recorded and does not establish baseline; retry only after fixing the cause. Persistent invalid baseline = blocked.
- Baseline bootstrap creates the campaign runtime status at .pdca/status/U1-campaign.md with Status: running and preparation_ref: .pdca/latency-readme/units/U1/preparation.md@r1. It is not a step and is not credited as a gain; it does not change the product or copy this preparation.

Stop rules:
- Met: valid accepted measurement p95_ms <= 40.00 -> stop success.
- Floor-only: 40.00 < p95_ms <= 60.00 and no credible candidate remains -> stop floor-only, never relabel as target success; final disposition is not `met`.
- Unreachable: seed candidates exhausted and last accepted p95 remains > 40.00 with no new evidence -> stop; do not lower thresholds.
- Blocked: missing host/executor/evidence or unresolved semantic blocker requiring new preparation.
- Surface violation: outside files touched, bench.py changed, concurrent measurement or cross-lane run -> stop/reapprove.
- Baseline may be > 60.00; it is a starting value, not a threshold change. Never lower thresholds.

## 9. Schedule-compatibility evidence
- Single-threaded, no file/network I/O in bench.py; one measurement at a time.
- Declared status/evidence paths: unit preparation status .pdca/status/U1-preparation.md; future campaign runtime .pdca/status/U1-campaign.md; baseline evidence .pdca/latency-readme/units/U1/evidence/baseline.txt; step evidence .pdca/latency-readme/units/U1/evidence/step-<n>-<kind>.txt.
- No hidden reverse order: baseline precedes the first step; each next step follows the last accepted measurement.
- Predictable runtime-status read point: only at a step boundary after the executor writes measurement evidence and status; never mid-run.
- Step kinds only: increment / repair / verify.
- U1/U2 are disjoint; U2 only touches README.md.

Gaps/assumptions/risks: report() list-identity/aliasing is not stated — preserve 1500 independent lists as a P1 risk unless evidence says otherwise. Baseline is intentionally unknown; target may be unreachable. Bench has no warmup, so one valid measurement is final and noise is not "fixed" by re-rolling. No tests/CI exist; functional checks are executor/check lenses, not a test suite. README.md is absent and belongs to U2. Confidence is high on process compatibility; performance reachability is unknown until baseline.
