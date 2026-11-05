# Archive receipt — levenshtein run results moved out before the next run

- Moved at: 2026-10-26T08:02:11Z (archive id `20261026T080211Z`)
- Repo: `/home/alex/sources/skills`, HEAD `a6ffa067bc7692a4772ca5c7ea9b078fbaac9058`
- Archive root: `/tmp/opencode/pdca-experiment-results-20261026T080211Z` (mode `0700`, 4.9 MB)
- Purpose: the next run of the Levenshtein task must not see the previous answer, its evidence,
  the status file or the built binary. Same rationale as `experiments/egg-drop/ARCHIVE-RECEIPT.md`
  and `experiments/ARCHIVE-RECEIPT-20261026T061716Z.md`.

## What was moved

Repo-relative paths are preserved inside the archive (`.payload.tar` holds the exact same tree,
extracted in place), so paths quoted in the moved logs, status and evidence stay valid.

| Path (repo-relative) | Kind | Files |
|---|---|---|
| `.pdca/levenshtein/` | directory (`rv1/attempts/c1-r1-n1/`: 13 command logs × 3 artefacts, `commands.json`, `manifest.json`, `plan-lint.txt`, `observation-pack.md`, `inputs/`) | 46 |
| `.pdca/scripts/` | directory (staged `plan_lint.py`) | 1 |
| `.pdca/status/levenshtein-1.md` | file (cycle status, `Phase: EXIT`) | 1 |
| `experiments/levenshtein/go.mod` | file | 1 |
| `experiments/levenshtein/main.go` | file | 1 |
| `experiments/levenshtein/main_test.go` | file | 1 |
| `experiments/levenshtein/README.md` | file | 1 |
| `experiments/levenshtein/levenshtein` | file (built binary, 2 365 867 B) | 1 |

Total: **52 files** (2.4 MB packed). None of them was tracked by git — the Go sources, the README
and the status file were untracked, the rest is covered by `.gitignore` (`.pdca/*/rv*/`,
`.pdca/scripts/`).

## What stays in the repo

- `experiments/levenshtein/levenshtein-test.md` — task specification, **unchanged**:
  sha256 `9c033b12f7dc10d64a4b6dcda7184a8218f9f7e1555071074bbb089397fab156` (before and after the move).
- `experiments/ARCHIVE-RECEIPT-20261026T061716Z.md` — receipt of the earlier archive, untouched.
- This receipt.
- Older cycles still in the index: `.pdca/status/pdca-collection-incremental-composition-1.md`,
  `.pdca/status/wsl-notify-session-filter-1.md` and their evidence.

No live output of the run remains in the working tree: `.pdca/levenshtein/`, `.pdca/scripts/`,
`.pdca/status/levenshtein-1.md` and `experiments/levenshtein/*.go` (+ `go.mod`, `README.md`,
binary) are absent; the task file is the only file in `experiments/levenshtein/`.

## Verification

- SHA-256 of all 52 moved files was recorded **before** the move
  (`.inventory-before.sha256`), then re-checked with `sha256sum -c` inside the archive:
  `HASHES-OK`, no mismatch.
- `.payload.tar` lists 60 entries (52 files + 8 directories); `tar -tf` re-read without error.
- Spec hash re-checked after the move: unchanged.
- `git status` delta: **no tracked path changed** (the moved paths were untracked or ignored);
  only the untracked experiment paths disappeared.

## How to restore

```bash
# whole payload
tar -xf /tmp/opencode/pdca-experiment-results-20261026T080211Z/.payload.tar \
  -C /home/alex/sources/skills

# or a single artefact, e.g. the status
cp /tmp/opencode/pdca-experiment-results-20261026T080211Z/.pdca/status/levenshtein-1.md \
   /home/alex/sources/skills/.pdca/status/
```
