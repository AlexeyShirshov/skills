# Collection demo — status

- **collection-id:** `demo`
- **form:** `collection`
- **plan_cap:** 4
- **lane_cap:** 4
- **Phase progress mirror:** this file is the single source of truth.

## Units

| unit | form | status | disposition | plan_state | preparation_state | preparation_ref | campaign_ref | refs |
|---|---|---|---|---|---|---|---|---|
| U1 | cycle | in-progress | active | ready | — | — | — | `.pdca/status/U1.md` |
| U2 | campaign | pending (barrier-ready; not started) | active | n/a (campaign) | ready | `.pdca/demo/items/U2/preparation.md@r1` | — | `.pdca/demo/items/U2/preparation.md@r1` |

## Tasks

| task | unit | group | branch | status | plan_state | plan_revision | status_path | reason + patch |
|---|---|---|---|---|---|---|---|---|
| U1 | U1 | G1 | main (current; no task branch) | in-progress | ready | r1 | `.pdca/status/U1.md` | — |

## Groups

| group | tasks (order) | worktree | branch/ref | status |
|---|---|---|---|---|
| G1 | [U1, U2] | — (one group: current worktree) | main (current branch) | in-progress |

## Collection decisions

| when (UTC) | decision | by | evidence |
|---|---|---|---|
| 2026-10-28T10:00:00Z | Clustering accepted: one group G1 | pdca-planner | this file |
