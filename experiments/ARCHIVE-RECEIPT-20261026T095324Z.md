# Archive receipt — levenshtein run results moved out before the next run

- Moved at: 2026-10-26T09:53:24Z (archive id `20261026T095324Z`)
- Repo: `/home/alex/sources/skills`, HEAD `72464752c8a7ac142d08b1697d20cdf54a0b663e`
- Archive root: `/tmp/opencode/pdca-experiment-results-20261026T095324Z` (mode `0700`, 9.5 MB)
- Purpose: the next run of the Levenshtein task must not see the previous answer, its evidence,
  the status file or the built binary. Same rationale as `experiments/egg-drop/ARCHIVE-RECEIPT.md`,
  `experiments/ARCHIVE-RECEIPT-20261026T061716Z.md` and
  `experiments/ARCHIVE-RECEIPT-20261026T080211Z.md`.

## What was moved

Repo-relative paths are preserved inside the archive (`.payload.tar` holds the exact same tree,
extracted in place), so paths quoted in the moved logs, status and evidence stay valid.

| Path (repo-relative) | Kind | Files |
|---|---|---|
| `.pdca/levenshtein/` | directory (`rv1/`: `plan-r1.md`, the B1 binary, `toolchain-probe/` 11 files, `attempts/c1-r1-n1/` 33 captures/index files) | 46 |
| `.pdca/scripts/` | directory (staged `plan_lint.py`, `status_lint.py`) | 2 |
| `.pdca/status/levenshtein-1.md` | file (cycle status, `Phase: EXIT`) | 1 |
| `experiments/levenshtein/main.go` | file | 1 |
| `experiments/levenshtein/main_test.go` | file | 1 |
| `experiments/levenshtein/README.md` | file | 1 |

Total: **52 files** (4.7 MB packed). None of them was tracked by git — the Go sources and the README
were untracked, the status file was untracked, the rest is covered by `.gitignore`
(`.pdca/*/rv*/`, `.pdca/scripts/`).

## Not part of the archive

`.pdca/levenshtein/rv1/goenv/` — **1091 files, 61 157 942 bytes**: the Go `GOPATH`/`GOCACHE`/`HOME`/
`TMPDIR` area this run isolated inside the evidence root. It was deleted rather than archived
(facts recorded in `.deleted-cache.txt`): a build cache is a by-product, not evidence, and the
command contract now keeps it outside the evidence root (`references/plan.md` §Plan command
contract; `plan_lint` rejects the placement this run used). Nothing about the result is lost — the
deliverable, its captures and the plan are in the archive.

## What stays in the repo

- `experiments/levenshtein/levenshtein-test.md` — task specification, **unchanged**:
  sha256 `9c033b12f7dc10d64a4b6dcda7184a8218f9f7e1555071074bbb089397fab156` (290 B, 3 lines).
- `experiments/ARCHIVE-RECEIPT-20261026T061716Z.md` and
  `experiments/ARCHIVE-RECEIPT-20261026T080211Z.md` — receipts of the earlier archives, untouched.
- This receipt.
- Older cycles still in the index: `.pdca/status/pdca-collection-incremental-composition-1.md`,
  `.pdca/status/wsl-notify-session-filter-1.md` and their evidence.

No live output of the run remains in the working tree: `.pdca/levenshtein/`, `.pdca/scripts/` and
`.pdca/status/levenshtein-1.md` are absent, and `experiments/levenshtein/` holds only the spec.

## Verification

- SHA-256 of all 52 moved files was recorded **before** the move
  (`.inventory-before.sha256`), then re-checked with `sha256sum -c` inside the archive:
  52/52 `OK`, exit 0.
- `.payload.tar` lists 59 entries (52 files + 7 directories); `tar -tf` re-read without error.
- Spec hash re-checked after the move: unchanged.
- `git status` delta: **no tracked path changed** (the moved paths were untracked or ignored);
  only the untracked experiment and status paths disappeared.

## How to restore

```bash
# whole payload
tar -xf /tmp/opencode/pdca-experiment-results-20261026T095324Z/.payload.tar \
  -C /home/alex/sources/skills

# or a single artefact, e.g. the status
cp /tmp/opencode/pdca-experiment-results-20261026T095324Z/.pdca/status/levenshtein-1.md \
   /home/alex/sources/skills/.pdca/status/
```

The deleted cache is not restorable from the archive and does not need to be: `go build`/`go test`
recreate it, and the next run places it outside the evidence root.
