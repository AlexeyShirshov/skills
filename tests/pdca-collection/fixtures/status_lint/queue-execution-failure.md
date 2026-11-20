# Collection execution failure — status

## Tasks

| task | group | branch | status | plan_state | terminal | attempts | reason + patch | status_path |
|---|---|---|---|---|---|---|---|---|
| T1 | G1 | main (current; no task branch) | done | ready | execution | 1 | — | `.pdca/status/t1-1.md` |
| T2 | G1 | main (current; no task branch) | incomplete | ready | execution | 3 | the group is stopped: DO could not finish; patch `.pdca/t2/patch.diff` | `.pdca/status/t2-1.md` |
| T3 | G1 | main (current; no task branch) | incomplete | pending | execution | 0 | the group is stopped | `.pdca/status/t3-1.md` |
| T4 | G1 | main (current; no task branch) | incomplete | pending | — | 0 | the group is stopped | `.pdca/status/t4-1.md` |

## Groups

| group | tasks (order) | worktree | branch/ref | status |
|---|---|---|---|---|
| G1 | [T1, T2, T3, T4] | — (one group: current worktree) | main (current branch) | incomplete |
