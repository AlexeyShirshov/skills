# Archive receipt — egg-drop outputs before fresh re-run

- Archive root: `/tmp/opencode/egg-drop-before-rerun-20261024T105401Z`
- Recording time (actual UTC clock): 2026-10-24T10:54:01Z (name stamp), receipt finalized 2026-10-24T10:54:20Z
- Source repo: `/home/alex/sources/skills`
- Purpose: hide/archive all existing egg-drop outputs so a fresh run tests the edited source skill without contamination.
- No cycle (PLAN/DO/CHECK/ACT) was started, no agent/cycle invoked, no content of prior answers inspected (hashing only).

## Scoped items moved (repo-relative paths preserved verbatim)

| Original repo-relative path | Type | Files |
| --- | --- | --- |
| `experiments/egg-drop/answer-a.md` | file | 1 |
| `.pdca/egg-drop-answer-a/` | directory tree (`rv1/attempts/c1-r1-n1`, `.../c1-r1-n2` incl. `__pycache__`) | 17 |
| `.pdca/status/egg-drop-answer-a-1.md` | file | 1 |

Totals: 19 regular files, 5 directories, 0 symlinks. Every original path now absent from the repo.

## Integrity

- SHA256 computed for all 19 regular files **before** the move and re-computed **after** the move.
- Missing after move: none. Hash mismatches: none. Directory set identical before/after.
- Machine-readable evidence:
  - `.archive-inventory.json` — per-entry type, size, SHA256, symlink target (if any), scoped item list, recording time.
  - `.archive-verification.json` — before/after counts, missing list, mismatch list, originals-still-present list, `integrity_ok: true`.

## Explicitly NOT touched

- `experiments/egg-drop/egg-drop-test.md` (spec) — still in place, SHA256 unchanged.
- `skills/pdca/SKILL.md` (modified tracked source) — SHA256 unchanged.
- Any other `.pdca` task/status artifacts, `.opencode/`, host config and snapshot: untouched.
- No commits, pushes, deploys, config writes, source-skill edits, test or CI changes.

## Restore

Replay the moves in the inverse direction, e.g.

```
cd /home/alex/sources/skills
mv /tmp/opencode/egg-drop-before-rerun-20261024T105401Z/experiments/egg-drop/answer-a.md experiments/egg-drop/answer-a.md
mv /tmp/opencode/egg-drop-before-rerun-20261024T105401Z/.pdca/egg-drop-answer-a .pdca/egg-drop-answer-a
mv /tmp/opencode/egg-drop-before-rerun-20261024T105401Z/.pdca/status/egg-drop-answer-a-1.md .pdca/status/egg-drop-answer-a-1.md
```

Then re-verify the restored files against `.archive-inventory.json`.

## Per-file SHA256 (original == archived)

```text
5d3ffbb4fa3a03f0abd2fde58de8a0bafbc37c93cb886fe82270d96719402236  experiments/egg-drop/answer-a.md
f3a48d7ae6cd1922d167e01a8c9fd7538f871e0d8dd2d5948d8bf4ffef2c5204  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/__pycache__/recompute.cpython-310.pyc
3b5992c3745355c45ee651d4629e24185bd4ca2116afba008e736c235a854124  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/coverage.md
8ff28d8370daf69d82b587013184f6218ccbfd59f6f8af02565b0899da5da564  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/fixture-corrupt.md
f6cf7be74d05e53def4990c7277842ab0d8a3f3e218ca7d4bfb7b532960a53ab  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/fixture.md
3513eba745b3c0bc77275f8d3166d2840d357d8d1f00599755d2e15aa62ba468  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/manifest.json
f1dea5f91b3125a29271fa088e10a7146aff77b4a13e6928374b217a8ac03624  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/recompute.log
a47b3834bbb91c5702d46b6a22eb9e2d068402ba0d7381b936c5609f473a863c  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/recompute.py
697910eeb8326af7512c2e303ae0e20cbe3dca90577316e577baa97ff449e6cc  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/selftest.log
20a31db874146dc775c4dab9c1db07d5af7cfd3fc3a92ad961dd60115983925a  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/snapshot.json
2b9756fbb2f0d4f66673e13373c5735082a665f3b925e7972ca8ba0dccac52f9  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/structure.log
692d10f3f38f3cd634152f023a2590affbb801cf5456ef26819ef27c013341b1  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/coverage.md
62a8ababca68c1254c1e0d71e96ebe9288dc2a5fc92bb5569d64ca539c355f5b  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/manifest.json
02478015763621f2a534187058e447ced5f8892abdc80162d27f374f92772633  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/recompute.log
25a06579a284712fb4b0cb3eda11f8492880c674dab312834be99cc391b00c38  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/recompute.py
2006e3c92dd8b93b9dd6561bf0f3ffd7740751067c04bc32fac446026691522b  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/selftest.log
b5cba6aded3d1b5ff5952c6e3297b4a595636492483209b6993b9e2e54f986a9  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/snapshot.json
b763c717a00e57ac51ec80dff90b32b812a1913e65a1fe40c21a0aa74080bdea  .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/structure.log
c894cefea92720348dcf841aa0fb6474306d95cb997f4885685dbaf9d32cecf0  .pdca/status/egg-drop-answer-a-1.md
```
