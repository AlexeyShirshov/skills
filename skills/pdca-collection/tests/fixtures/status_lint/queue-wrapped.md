# Collection demo — status

## Groups

| group | tasks (order) | worktree | branch/ref | status | stop reason |
|---|---|---|---|---|---|
| G1 | [U1] | — (one group: current worktree) | main (current branch) | done | — |
| G2 | [U2, U3] | `/repo-worktrees/demo/g2` | `collection/demo/group-2` | incomplete | the group is stopped: item U2 failed on a missing toolchain,
so U3 was marked incomplete instead of being executed |
