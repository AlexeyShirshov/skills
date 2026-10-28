# Archive receipt — levenshtein run results moved out before the next run

- Moved at: 2026-10-28T06:10:14Z (archive id `20261028T061014Z`)
- Repo: `/home/alex/sources/skills`, HEAD `ea145a46bda0152c8bc3c0378ed29622b5a9ca12`
  (the branch also holds uncommitted skill edits from a concurrent session; they are not run
  artefacts and are not part of this archive)
- Archive root: `/tmp/opencode/pdca-experiment-results-20261028T061014Z` (mode `0700`, 5.8 MB)
- Purpose: the next run of the Levenshtein task must not see the previous answer, its evidence,
  the status file or the built binary. Same rationale as the five earlier receipts in this
  directory (`ARCHIVE-RECEIPT-20261026T061716Z.md`, `…T080211Z.md`, `…T095324Z.md`,
  `…T113519Z.md`, `…T122427Z.md`).

## What was moved

Repo-relative paths are preserved inside the archive (`.payload.tar`, sha256
`c3f780e3f2a50eb38c6513d41637647efee21ccc856d1c84fc1521dd6c838681`, holds the exact same tree),
so paths quoted in the moved logs, status and evidence stay valid.

| Path (repo-relative) | Kind | Files |
|---|---|---|
| `.pdca/levenshtein-go/` | directory (`rv1/plan-r1.md` … `plan-r3.md`, `rv1/attempts/c1-r1-n1/`, `c1-r2-n1/`, `c1-r3-n1/` with command captures, identities, manifests, observation packs) | 104 |
| `.pdca/scripts/` | directory (staged `plan_lint.py`, `status_lint.py`) | 2 |
| `.pdca/status/levenshtein-go-1.md` | file (cycle status, `Phase: EXIT`) | 1 |
| `experiments/levenshtein/` | directory (`levenshtein-test.md` task note, `go.mod`, `main.go`, `main_test.go`, built `levenshtein`) | 5 |

Total: **112 files**. None of them was tracked by git.

The working tree after the move carries no Levenshtein artefact: `git status --porcelain` lists
neither `.pdca/status/levenshtein-go-1.md` nor `experiments/levenshtein/`.

## Restore

```bash
tar -C /home/alex/sources/skills -xf \
  /tmp/opencode/pdca-experiment-results-20261028T061014Z/.payload.tar
```
