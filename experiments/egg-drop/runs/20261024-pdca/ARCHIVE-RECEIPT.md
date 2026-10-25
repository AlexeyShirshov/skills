# Archive receipt — egg-drop results moved before next run

- Archive (absolute): `/tmp/opencode/egg-drop-before-next-run-20261024T171547Z`
- Created (UTC): 2026-10-24T17:16:22Z
- Repo: /home/alex/sources/skills
- Operation: **move/archive only — nothing deleted**, no overwrite of an existing archive.
- Authorization: user steering, "перемести пока результаты эксперимента, я запущу новый".

## Moved targets (exact 3, repo-relative paths preserved)

| Original path | Archived at | Kind |
|---|---|---|
| experiments/egg-drop/answer.md | /tmp/opencode/egg-drop-before-next-run-20261024T171547Z/experiments/egg-drop/answer.md | file |
| .pdca/egg-drop/ (whole tree: rv1/verify.py, attempts c1-r1-n1..n3, __pycache__) | /tmp/opencode/egg-drop-before-next-run-20261024T171547Z/.pdca/egg-drop/ | dir, 30 files |
| .pdca/status/egg-drop-1.md | /tmp/opencode/egg-drop-before-next-run-20261024T171547Z/.pdca/status/egg-drop-1.md | file |

Total: 32 entries (32 regular files, 0 symlinks).

## Verified

- Pre-move inventory (sha256 per file) reproduced 100% inside the archive; diff empty.
- All 3 original paths absent from the workspace afterwards.
- Spec `experiments/egg-drop/egg-drop-test.md` NOT moved; sha256 unchanged:
  `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e` (before = after).
- Non-scoped `git status` byte-identical before/after (staged + unstaged source rename work, tests/CI, docs untouched).
- No commit, no push, no cycle, no tests, no reload.
- Previous archive `/tmp/opencode/egg-drop-before-rerun-20261024T105401Z` untouched; deployment/retro receipts and backups untouched; other .pdca tasks/status untouched; .opencode/ untouched.

## Note for concurrent validation session (ses_e9117a582ffeXRU24DiZ2m4YK2)

The egg-drop artifacts (`experiments/egg-drop/answer.md`, `.pdca/egg-drop/**`, `.pdca/status/egg-drop-1.md`) are intentionally ABSENT from the workspace because **this user-authorized archive moved them**. Their hashes are recorded in `.archive-inventory.json` (mapping preserved_path → sha256), so a missing-artifact comparison can be reconciled against this archive rather than treated as a lost/reverted file. Nothing was restored into the workspace and no source/prehash file was edited.

Machine-readable: `.archive-inventory.json`, `.archive-verification.json` (plus a textual copy `.archive-inventory.patch.json`).
