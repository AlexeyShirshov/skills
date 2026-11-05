# Archive receipt — previous egg-drop results moved out of the working tree

- Moved at: 2026-10-25T06:33:09Z (archive id `20261025T063309Z`)
- Repo: `/home/alex/sources/skills`, HEAD `2a60f625f5fed2ad336982b931363bef3779c1ae`
- Archive root: `/tmp/opencode/egg-drop-prev-results-20261025T063309Z` (mode `0700`, 4.6 MB)
- Purpose: a fresh run of the egg-drop benchmark must not see the previous answers, checkers,
  fixtures or retrospectives. Same rationale as the earlier archives under `runs/*/ARCHIVE-RECEIPT.md`.

## What was moved

Original repo-relative paths are preserved inside the archive, so links in the moved receipts and
in the historical `/tmp` retro reports stay valid.

| Path (repo-relative) | Kind | Files |
|---|---|---|
| `experiments/egg-drop/runs/` | directory | 166 |
| `experiments/egg-drop/retrospectives/` | directory | 8 |
| `experiments/egg-drop/INDEX.md` | file | 1 |
| `experiments/egg-drop/TRANSFER-RECEIPT.json` | file | 1 |

Total: **176 files**. Of these, 174 deletions are visible in `git status`; the remainder are
`__pycache__/*.pyc` bytecode ignored by `.gitignore`.

## What stays in the repo

- `experiments/egg-drop/egg-drop-test.md` — the task specification, **unchanged**:
  sha256 `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e`.
- This receipt.
- No live egg-drop output exists in the working tree: `experiments/egg-drop/answer*.md`,
  `.pdca/egg-drop*` and `.pdca/status/egg-drop*` are all absent (checked before the move).

## Verification

- SHA-256 of every moved file was recorded **before** the move and recomputed **after** it:
  all 176 hashes identical (`.archive-inventory.json`, `.archive-verification.json` in the
  archive root).
- Spec hash unchanged before/after.
- `git status` delta: only the 174 tracked deletions listed above; `experiments/egg-drop/egg-drop-test.md`
  is untouched and no other path changed.

## How to restore

Everything is committed in git history, so either way works:

```bash
# from git history (preferred)
git checkout 2a60f62 -- experiments/egg-drop

# or from the archive
cp -a /tmp/opencode/egg-drop-prev-results-20261025T063309Z/experiments/egg-drop/. experiments/egg-drop/
```
