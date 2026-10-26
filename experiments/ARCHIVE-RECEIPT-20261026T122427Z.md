# Archive receipt — levenshtein run results moved out before the next run

- Moved at: 2026-10-26T12:24:27Z (archive id `20261026T122427Z`)
- Repo: `/home/alex/sources/skills`, HEAD `9b29bd5462133f3a921b787ac93ebc1fd7e3b198`
  (the skill edits implementing the 5th retro's findings 1–6 are uncommitted in the working tree;
  they are not run artefacts and are not part of this archive)
- Archive root: `/tmp/opencode/pdca-experiment-results-20261026T122427Z` (mode `0700`, 5.0 MB)
- Purpose: the next run of the Levenshtein task must not see the previous answer, its evidence,
  the status file or the built binary. Same rationale as the four earlier receipts in this
  directory (`ARCHIVE-RECEIPT-20261026T061716Z.md`, `…T080211Z.md`, `…T095324Z.md`,
  `…T113519Z.md`).

## What was moved

Repo-relative paths are preserved inside the archive (`.payload.tar` holds the exact same tree,
extracted in place), so paths quoted in the moved logs, status and evidence stay valid.

| Path (repo-relative) | Kind | Files |
|---|---|---|
| `.pdca/levenshtein-go/` | directory (`rv1/plan-r1.md`, `rv1/attempts/c1-r1-n1/` with host `toolchain.*`, `build.*` and `tests.*` captures plus their `.identity` files, `commands.json`, `manifest.json`, `observation-pack.md`, `plan_lint.json`, `status_lint.txt`, and the built `bin/levenshtein`) | 19 |
| `.pdca/scripts/` | directory (staged `plan_lint.py`, `status_lint.py`) | 2 |
| `.pdca/status/levenshtein-go-1.md` | file (cycle status, `Phase: EXIT`, ACT row finalizing it) | 1 |
| `experiments/levenshtein/main.go` | file (213 B, sha256 `731814c7…`) | 1 |
| `experiments/levenshtein/main_test.go` | file (2473 B, sha256 `1c4f4c61…`) | 1 |
| `experiments/levenshtein/distance.go` | file (996 B, sha256 `91b4423d…`) | 1 |
| `experiments/levenshtein/distance_test.go` | file (2375 B, sha256 `ae8d6e55…`) | 1 |
| `experiments/levenshtein/README.md` | file (2596 B, sha256 `6d67f1ef…`) | 1 |
| `experiments/levenshtein/go.mod` | file (40 B, sha256 `7c00818e…`) | 1 |

Total: **28 files**. None of them was tracked by git — the Go sources and the README were untracked,
the status file was untracked, and the rest is covered by `.gitignore` (`.pdca/*/rv*/`,
`.pdca/scripts/`).

The run had **one attempt**: `c1-r1-n1` passed CHECK on the first verdict, so there is no
superseded generation and no re-check in the archive. Cycle `N=1`, plan `r1`, iteration `n=1/3`
(5th Levenshtein run in this series); 9 sessions, 18.9 min, one plan revision, one PASS.

## Deliverable identity

| File | Bytes | SHA-256 |
|---|---|---|
| `README.md` | 2596 | `6d67f1efc16f0f3b768423bdd9a11fb175873bb92876fb94a1c26bbf103067a3` |
| `distance.go` | 996 | `91b4423d093fa1494b8a8eceecc6ad5f903ec3fd73dc585a5dfae570090bf37b` |
| `distance_test.go` | 2375 | `ae8d6e558b1922bd64be56858bb9c1ca22da910ef03d06c7c22566dd4dd3f6ca` |
| `go.mod` | 40 | `7c00818e7c25700ab35d29b81abff730d25f5dc672d13d05b54886e26a75eece` |
| `main.go` | 213 | `731814c7691ed24785c966225ee1c31c444a20c241b1f75890857a770ee26afe` |
| `main_test.go` | 2473 | `1c4f4c6143d784eb02e9969ad089297ec47cd0a4d02fdf1ff58c6a78e2f93a2f` |

## Not part of the archive

- `/tmp/opencode/levenshtein-go-1-cache` — **1232 files, 61 111 880 bytes**: the Go
  `GOPATH`/`GOCACHE`/`HOME`/`TMPDIR` area. It lived **outside the checkout**, as the command
  contract requires (`references/plan.md` §Plan command contract), and was deleted rather than
  archived. A build cache is a by-product, not evidence, and the next run recreates it.
- The retro's own verification scratch — `/tmp/opencode/levretro` (2 379 115 bytes: module copy and
  rebuilt binary) and `/tmp/opencode/levretro-cache` (34 163 801 bytes: Go cache). Deleted with the
  run cache; not evidence of the run.

Both facts are recorded in `.deleted-cache.txt` at the archive root. Unlike the previous run,
nothing cached sat inside the evidence root: the root held evidence only (19 files / 2 432 703
bytes, of which the built `bin/levenshtein` accounts for 2 366 270).

## What stays in the repo

- `experiments/levenshtein/levenshtein-test.md` — task specification, **unchanged**:
  sha256 `9c033b12f7dc10d64a4b6dcda7184a8218f9f7e1555071074bbb089397fab156` (290 B, 3 lines).
- The four earlier receipts in `experiments/`, untouched.
- This receipt.
- Older cycles still in the index: `.pdca/status/pdca-collection-incremental-composition-1.md`,
  `.pdca/status/wsl-notify-session-filter-1.md` and their evidence.

No live output of the run remains in the working tree: `.pdca/levenshtein-go/`, `.pdca/scripts/` and
`.pdca/status/levenshtein-go-1.md` are absent, and `experiments/levenshtein/` holds only the spec.

## Verification

- SHA-256 of all 28 moved files was recorded **before** the move (`.inventory-before.sha256`), then
  re-checked with `sha256sum -c` inside the archive: 28/28 `OK`, exit 0.
- `.payload.tar` lists 34 entries (28 files + 6 directories: `levenshtein-go`, `rv1`, `attempts`,
  `c1-r1-n1`, `bin`, `scripts`); extraction recreates the `.pdca/` and `experiments/levenshtein/`
  parents. `tar -tf` re-read without error.
- Spec hash re-checked after the move: unchanged.
- `git status` delta: **no tracked path changed**; only the untracked experiment and status paths
  disappeared.

## How to restore

```bash
# whole payload
tar -xf /tmp/opencode/pdca-experiment-results-20261026T122427Z/.payload.tar \
  -C /home/alex/sources/skills

# or a single artefact, e.g. the final status
cp /tmp/opencode/pdca-experiment-results-20261026T122427Z/.pdca/status/levenshtein-go-1.md \
   /home/alex/sources/skills/.pdca/status/
```

The deleted cache is not restorable from the archive and does not need to be: `go build`/`go test`
recreate it, and it lives outside the evidence root by contract.
