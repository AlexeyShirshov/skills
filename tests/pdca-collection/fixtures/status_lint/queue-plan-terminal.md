# Collection plan-terminal — status

## Tasks

| task | group | branch | status | plan_state | terminal | attempts | reason + patch | status_path |
|---|---|---|---|---|---|---|---|---|
| T1 | G1 | main (current; no task branch) | incomplete | pending | criteria-undetermined | 0 | the user supplied no acceptance criterion and none can be derived from the goal | `.pdca/status/t1-1.md` |
| T2 | G1 | main (current; no task branch) | done | ready | execution | 1 | — | `.pdca/status/t2-1.md` |
| T3 | G1 | main (current; no task branch) | incomplete | pending | infeasible | 0 | proven infeasible under the stated constraints | `.pdca/status/t3-1.md` |
| T4 | G1 | main (current; no task branch) | done | ready | — | 1 | — | `.pdca/status/t4-1.md` |
| T5 | G1 | main (current; no task branch) | incomplete | pending | already-established | 0 | the requested result already exists at the recorded ref | `.pdca/status/t5-1.md` |

## Groups

| group | tasks (order) | worktree | branch/ref | status |
|---|---|---|---|---|
| G1 | [T1, T2, T3, T4, T5] | — (one group: current worktree) | main (current branch) | done |
