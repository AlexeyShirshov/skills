# Collection r2-campaign — status

- **collection-id:** `r2-campaign`
- **Status file:** `.pdca/status/collection-r2-campaign.md`
- **Interaction mode:** user unavailable; no questions, no waiting for approval
- **Git rights:** no autocommit / no merge right granted for this run; push never
- **Scope of this run:** collection P phase only — own PLANs/preparation, ALL-barrier, clustering. No product code, no baseline measurement, no lane allocation, no DO.
- **Phase progress mirror:** this file is the single source of truth.

## Input units (order locked)

| unit | brief | form |
|---|---|---|
| U1 | Campaign: reduce p95 of `python3 bench.py` (p95 over 20 runs, same host, single-threaded) from measured baseline to target p95 <= 40 ms, floor p95 <= 60 ms; next step chosen from previous measurement; surface `app.py`, `bench.py` only. | campaign |
| U2 | Add `README.md` describing the project. | cycle |

## Units

| unit | form | status | disposition | plan_state | contract+overlay | cycle_id / N | plan_revision | preparation_state | preparation_ref | campaign_ref | baseline_ref | footprint reservation | predecessor requirements | assumptions / prerequisites | refs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| U1 | campaign | pending (barrier-ready; not started) | active | — | — (step-level) | — | — | ready | `.pdca/r2-campaign/items/U1/preparation.md@r1` | — | none | surface {app.py, bench.py}; write reservation {app.py}; bench.py frozen/read-only as the measurement recipe; no new product files; uncertainty: baseline and in-surface headroom unmeasured | none | preparation barrier before baseline bootstrap; same host, single-threaded, frozen recipe; commit policy none unless overlay grants | `.pdca/r2-campaign/items/U1/preparation.md@r1` |
| U2 | cycle | pending (PLAN ready at PLAN→DO; DO not started) | active | ready | `pdca` + `coder` | `U2-1 (N=1)` | r1 | — | — | — | none | `README.md` (new, repo root) only; no `app.py`/`bench.py` edits; uncertainty: prose must match final code | none (independent of U1) | repo root cwd; docs-only; no performance numbers; U1 state is not an input | `.pdca/status/U2.md` |

## Tasks

| task | unit | group | branch | status | plan_state | contract+overlay | cycle_id / N | plan_revision | canonical task status path | baseline ref | footprint/requirements/prerequisites refs | incomplete reason + patch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| U1 | U1 | G1 | not allocated (D blocked) | pending | — | — | — | r1 (preparation revision) | `.pdca/status/collection-r2-campaign-unit-U1.md` (not created) | pending (baseline bootstrap after barrier) | preparation_ref `.pdca/r2-campaign/items/U1/preparation.md@r1`; the mandatory preparation blocks verified; footprint reservation: `app.py` editable, `bench.py` frozen as measurement recipe (subset of `app.py`+`bench.py` unit surface) | barrier-ready; not started; no baseline measured; no product code |
| U2 | U2 | G2 | not allocated (D blocked) | pending | ready | `pdca` + `coder` | `U2-1 (N=1)` | r1 | `.pdca/status/U2.md` | none | status ref `.pdca/status/U2.md`; footprint `README.md` (new file only); requirements none; independent of U1 | barrier-ready; PLAN→DO boundary; README not written; DO not started |

## Groups

| group | tasks (order) | worktree | branch/ref | status | notes |
|---|---|---|---|---|---|
| G1 | U1 | not allocated (D blocked) | not allocated (D blocked); planned `collection/r2-campaign/group-1` | pending | singleton; footprint `{app.py, bench.py}`, write reservation `{app.py}`, `bench.py` frozen/read-only |
| G2 | U2 | not allocated (D blocked) | not allocated (D blocked); planned `collection/r2-campaign/group-2` | pending | singleton; footprint `{README.md}` new file only |

Group footprints are disjoint: {app.py, bench.py} ∩ {README.md} = ∅. No DAG edge between U1 and U2; display order G1,G2 is not a dependency.

Integration note: `skipped` is not a group status and is not used here; no merge has occurred. No group is `merged`.

## Barrier and decisions log

- Collection bootstrap PLAN (`pdca-planner`): collection-id `r2-campaign`; U1 = `campaign` (no item-level contract); U2 = `cycle` with the contract `pdca` + the overlay `coder` (the project is Python code); item order locked U1, U2.
- U1 own `COLLECTION TASK PLAN` (campaign preparation) returned `preparation_handoff`: immutable preparation document `.pdca/r2-campaign/items/U1/preparation.md` at r1; `preparation_state=ready`; single authoritative `preparation_ref=.pdca/r2-campaign/items/U1/preparation.md@r1`; the mandatory preparation blocks present; no baseline measured, no runtime status, no step plans, no future step variants, no product code.
- U2 own `COLLECTION TASK PLAN` (cycle, `pdca-coder`) returned `plan_handoff`: genuine PLAN persisted at `.pdca/status/U2.md`, cycle `U2-1` (N=1), plan revision `r1`, `plan_state=ready`, footprint `README.md` (new file only); stopped at the PLAN→DO boundary; README not written; DO not started.
- `.pdca/status/project-readme-1.md` is a non-authoritative draft/duplicate created during planning; the canonical U2 status is `.pdca/status/U2.md`. It is not referenced by any handoff and must be ignored on resume.
- ALL-barrier: PASS (2/2). U1 form-specific readiness: `preparation.md@r1`, `preparation_state=ready`, the mandatory preparation blocks present. U2 form-specific readiness: `.pdca/status/U2.md`, cycle U2-1 (N=1), plan revision r1, `plan_state=ready`, contract `pdca` + overlay `coder`.
- Clustering (`pdca-planner`, after barrier): DAG nodes U1, U2 with NO directed edges. Groups: G1={U1}, G2={U2}; topological order [U1] and [U2]; group footprints disjoint (`{app.py, bench.py}` ∩ `{README.md}` = ∅); there is no real shared-footprint or shared-measurement reason to serialize them.
- PLAN revision vector used for the schedule: { U1: `.pdca/r2-campaign/items/U1/preparation.md@r1` ; U2: `.pdca/status/U2.md@r1` (cycle U2-1, N=1) }.
- Merge strategy: not applied in this run. Clustering produced 2 groups and no autocommit/merge right was granted, so D is preflight-blocked before lane/worktree allocation. No group branch, worktree, merge, or integration exists.
- P phase complete. Stop at the P→D boundary. No lanes, worktrees, branches, baseline, product changes, commits, or merges were created in this run.

## Preflight / commit

- Autocommit/merge right: NOT granted.
- D preflight: BLOCKED — clustering produced 2 groups and a multi-group run requires explicitly allowed `collection/**` autocommit and `merge --no-ff`, which this run does not have. Per the contract this is a preflight blocker BEFORE worktree/lane allocation; groups must not start until the right is granted or the user changes the input.
- Allowed in this run: P validation, clustering, and this bookkeeping. Not allowed: D, lanes/worktrees/branches, baseline/product commands, autocommit, merge, push.
- Next allowed step: obtain explicit autocommit/merge right (project overlay or explicit user request) or change the input; then allocate lanes and run baseline bootstrap for U1 and the U2 DO.

## General verification and recovery

- Last general `C`: not run (P phase only).
- Verification state: `unverified`.
- Blocking reason: P phase stop before D; no lane, no product change, no baseline, no required measurement reports yet.
- Defect id/history: none.
- Related corrective task status file: none.
- Next allowed step after this run: P phase complete and persisted. D is preflight-blocked (no autocommit/merge right with 2 groups). No general C has run; verification remains unverified.

## Completion fields

- **Done:** — (collection P phase complete: bootstrap, per-unit PLAN/preparation, ALL-barrier, clustering; D not started)
- **Verified:** no
- **Incomplete:** no (D preflight-blocked, not a terminal incomplete outcome)
