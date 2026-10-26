# Archive receipt — levenshtein run results moved out before the next run

- Moved at: 2026-10-26T11:35:19Z (archive id `20261026T113519Z`)
- Repo: `/home/alex/sources/skills`, HEAD `2aaa62937d9b221d2748dc3c328857826040aa6b`
- Archive root: `/tmp/opencode/pdca-experiment-results-20261026T113519Z` (mode `0700`, 9.8 MB)
- Purpose: the next run of the Levenshtein task must not see the previous answer, its evidence,
  the status file or the built binary. Same rationale as the three earlier receipts in this
  directory (`ARCHIVE-RECEIPT-20261026T061716Z.md`, `…T080211Z.md`, `…T095324Z.md`).

## What was moved

Repo-relative paths are preserved inside the archive (`.payload.tar` holds the exact same tree,
extracted in place), so paths quoted in the moved logs, status and evidence stay valid.

| Path (repo-relative) | Kind | Files |
|---|---|---|
| `.pdca/levenshtein/` | directory (`rv1/plan-r1.md`, `rv1/attempts/c1-r1-n1/` and `c1-r1-n2/` with their captures, manifests, identity files, observation packs and the gate-1 `history/pre-fix/`) | 75 |
| `.pdca/scripts/` | directory (staged `plan_lint.py`, `status_lint.py`) | 2 |
| `.pdca/status/levenshtein-1.md` | file (cycle status, `Phase: EXIT`) | 1 |
| `experiments/levenshtein/main.go` | file (1255 B, sha256 `97b398e8…`) | 1 |
| `experiments/levenshtein/main_test.go` | file (3287 B, sha256 `ff487c75…`) | 1 |
| `experiments/levenshtein/README.md` | file (4146 B, sha256 `f50f2463…`) | 1 |

Total: **81 files**. None of them was tracked by git — the Go sources and the README were untracked,
the status file was untracked, and the rest is covered by `.gitignore` (`.pdca/*/rv*/`,
`.pdca/scripts/`).

The run itself used two attempts (`c1-r1-n1` failed CHECK on the README test command,
`c1-r1-n2` passed); both generations are in the archive, `n1` retained untouched as the superseded
generation.

## Not part of the archive

`/tmp/opencode/levenshtein-1-cache` — **828 files, 60 614 854 bytes**: the Go `GOPATH`/`GOCACHE`/
`HOME`/`TMPDIR` area. It lived **outside the checkout**, as the command contract requires
(`references/plan.md` §Plan command contract), and was deleted rather than archived (facts recorded
in `.deleted-cache.txt`). A build cache is a by-product, not evidence, and the next run recreates it.
Unlike the previous run, nothing cached sat inside the evidence root: the root held evidence only
(75 files / 4.9 MB).

## What stays in the repo

- `experiments/levenshtein/levenshtein-test.md` — task specification, **unchanged**:
  sha256 `9c033b12f7dc10d64a4b6dcda7184a8218f9f7e1555071074bbb089397fab156` (290 B, 3 lines).
- The three earlier receipts in `experiments/`, untouched.
- This receipt.
- Older cycles still in the index: `.pdca/status/pdca-collection-incremental-composition-1.md`,
  `.pdca/status/wsl-notify-session-filter-1.md` and their evidence.

No live output of the run remains in the working tree: `.pdca/levenshtein/`, `.pdca/scripts/` and
`.pdca/status/levenshtein-1.md` are absent, and `experiments/levenshtein/` holds only the spec.

## Verification

- SHA-256 of all 81 moved files was recorded **before** the move (`.inventory-before.sha256`), then
  re-checked with `sha256sum -c` inside the archive: 81/81 `OK`, exit 0.
- `.payload.tar` lists 89 entries (81 files + 8 directories); `tar -tf` re-read without error.
- Spec hash re-checked after the move: unchanged.
- `git status` delta: **no tracked path changed**; only the untracked experiment and status paths
  disappeared.

## How to restore

```bash
# whole payload
tar -xf /tmp/opencode/pdca-experiment-results-20261026T113519Z/.payload.tar \
  -C /home/alex/sources/skills

# or a single artefact, e.g. the final status
cp /tmp/opencode/pdca-experiment-results-20261026T113519Z/.pdca/status/levenshtein-1.md \
   /home/alex/sources/skills/.pdca/status/
```

The deleted cache is not restorable from the archive and does not need to be: `go build`/`go test`
recreate it, and it lives outside the evidence root by contract.
