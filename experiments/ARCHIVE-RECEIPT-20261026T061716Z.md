# Archive receipt — experiment results moved out before the next phase

- Moved at: 2026-10-26T06:17:16Z (archive id `20261026T061716Z`)
- Repo: `/home/alex/sources/skills`, HEAD `1f9bac374db6e01a2edbd72126e14cf2728baf54`
- Archive root: `/tmp/opencode/pdca-experiment-results-20261026T061716Z` (mode `0700`, 5.5 MB)
- Purpose: the next phase must not see the previous runs' answers, evidence, statuses or
  generated sources. Same rationale as `experiments/egg-drop/ARCHIVE-RECEIPT.md`.

## What was moved

Repo-relative paths are preserved inside the archive (`.payload.tar` holds the exact same
tree, extracted in place), so paths quoted in the moved logs, statuses and evidence stay valid.

| Path (repo-relative) | Kind | Files |
|---|---|---|
| `.pdca/egg-drop/` | directory (answer, preparation, U1/U2 evidence, logs, `rv1/`, `rv2/`) | 10 |
| `.pdca/levenshtein/` | directory (`rv1/` run logs, verification artefacts, built binary) | 40 |
| `.pdca/scripts/` | directory (`egg-drop-*.py` stagers + `__pycache__`) | 3 |
| `.pdca/status/egg-drop-1.md` | file | 1 |
| `.pdca/status/levenshtein-1.md` | file | 1 |
| `experiments/levenshtein/go.mod` | file | 1 |
| `experiments/levenshtein/main.go` | file | 1 |
| `experiments/levenshtein/main_test.go` | file | 1 |

Total: **58 files** (2.7 MB packed). None of them was tracked by git — the two levenshtein
sources and the status files were untracked, the rest is covered by `.gitignore`
(`.pdca/*/rv*/`, `.pdca/scripts/`).

## What stays in the repo

- `experiments/egg-drop/egg-drop-test.md` — task specification, unchanged:
  sha256 `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e`.
- `experiments/egg-drop/ARCHIVE-RECEIPT.md` — receipt of the earlier archive, untouched:
  sha256 `29f462156684861de46f00662341fd68484fc0e7cf2bb2ff2810a68d70440507`.
- `experiments/levenshtein/levenshtein-test.md` — task specification, unchanged:
  sha256 `9c033b12f7dc10d64a4b6dcda7184a8218f9f7e1555071074bbb089397fab156`.
- This receipt.
- Older cycles still in the index: `.pdca/status/pdca-collection-incremental-composition-1.md`,
  `.pdca/status/wsl-notify-session-filter-1.md` and their evidence.

No live output of either run remains in the working tree: `.pdca/egg-drop*`,
`.pdca/levenshtein*`, `.pdca/scripts/`, `.pdca/status/egg-drop*`,
`.pdca/status/levenshtein*` and `experiments/levenshtein/*.go` (+ `go.mod`) are absent.

## Verification

- SHA-256 of all 58 files was recorded **before** the move (`.inventory-before.sha256`),
  recomputed **after** extraction into the archive (`.inventory-in-archive.sha256`):
  `diff` empty — all hashes identical.
- `.payload.tar` lists 65 entries (58 files + 7 directories); `tar -tf` re-read without error.
- Spec hashes re-checked after the move: unchanged.
- `git status` delta: no tracked path changed; only untracked paths disappeared.

## Not part of the archive

`skills/pdca/tests/fixtures/plan_lint/repo/tests/Proj/obj/` and its `pdca-dotnet` twin
(20 files, 60 KB each) were MSBuild leftovers of the skill test suites, not experiment results:
deleted, and `.gitignore` now ignores `skills/*/tests/fixtures/**/{bin,obj}/` so a test run
does not dirty the tree again.

## How to restore

```bash
# whole payload
tar -xf /tmp/opencode/pdca-experiment-results-20261026T061716Z/.payload.tar -C /home/alex/sources/skills

# or a single artefact, e.g. one status
cp /tmp/opencode/pdca-experiment-results-20261026T061716Z/.pdca/status/levenshtein-1.md \
   /home/alex/sources/skills/.pdca/status/
```
