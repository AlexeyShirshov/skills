# Egg Drop — baseline rv1 (bootstrap)

Status: captured (immutable snapshot of facts at bootstrap)
Created: 2026-10-24T17:28:24Z
Campaign: egg-drop, contract rv1
Workspace root: `/home/alex/sources/skills`
Role: DO/executor baseline bootstrap — facts only, no answer, no checker, no commit.

## Verdict

- **Baseline score `S0 = 0.000`**
- **Gate verdict `FAIL`**
- Reason: `experiments/egg-drop/answer.md` does not exist — `ls -la experiments/egg-drop/`
  lists only `egg-drop-test.md`. A mechanical gate cannot pass without a candidate answer
  (no document to check), so the gate is FAIL by absence, and `S_accept = min(S_measure,
  S_verify) = 0.000`. No number here is estimated: 0.000 is the floor value for "nothing
  measurable exists".
- Target: `0.500` (baseline 0.000 + floor `delta S >= 0.500`).

## A1. Repository HEAD

Command:

```bash
git -C /home/alex/sources/skills rev-parse HEAD
```

Output (verbatim):

```text
6636d3690c1c75833a7cc016a65372f5c20eea87
```

## A2. Working-tree state

Command:

```bash
git -C /home/alex/sources/skills status --porcelain | wc -l
```

Output (verbatim):

```text
67
```

Command:

```bash
git -C /home/alex/sources/skills status --porcelain -- experiments/ .pdca/
```

Output (verbatim):

```text
?? experiments/
```

Command (drill-down, added for precision — `--untracked-files=all`, same scope):

```bash
git status --porcelain --untracked-files=all -- experiments/ .pdca/
```

Output (verbatim):

```text
?? experiments/egg-drop/egg-drop-test.md
```

Composition of the 67 dirty entries (summary only; foreign files, untouched):

```text
46 skills/...        17 docs/...        1 experiments/...        1 README.md
 1 AGENTS.md          1 .opencode
staged: 39   unstaged: 34   untracked: 4
```

Note: these belong to the user's in-flight work (source-rename/validation sessions). They are
not part of this campaign, were not read for content, and were not modified, staged, cleaned or
reverted. Only the aggregate counts are recorded here.

## A3. Is the spec tracked?

Command:

```bash
git -C /home/alex/sources/skills ls-files experiments/
```

Output (verbatim, empty):

```text
```

Result: **`experiments/` is NOT tracked by git** — 0 tracked files (`git ls-files experiments/ |
wc -l` → `0`). The spec `experiments/egg-drop/egg-drop-test.md` is an untracked working-tree
file, which is why `git status` reports it as `?? experiments/egg-drop/egg-drop-test.md`.

Contrast (relevant to commit policy): `.pdca/` **is** tracked — `git ls-files .pdca/ | wc -l` →
`18` (existing status files and other campaigns' evidence). `.pdca/` is not gitignored
(`git check-ignore -v` → not ignored).

## A4. Interpreter probe

Command and output (verbatim):

```bash
/usr/bin/python3.10 --version
```
```text
Python 3.10.12
```

```bash
command -v python3 || echo NO_PYTHON3
```
```text
/usr/bin/python3
```

```bash
python3 --version
```
```text
Python 3.10.12
```

```bash
/usr/bin/python3.10 -c "import json,re,hashlib,sys;print('stdlib-ok')"
```
```text
stdlib-ok
```

Result: `python3` is on `PATH` (`/usr/bin/python3`) and is the same **Python 3.10.12** as the
explicit `/usr/bin/python3.10`; the stdlib modules the checker contract needs
(`json`, `re`, `hashlib`, `sys`) import cleanly. No `NO_PYTHON3` fallback occurred.

## A5. No answer exists yet

Command and output (verbatim):

```bash
ls -la experiments/egg-drop/
```
```text
total 24
drwxr-xr-x 2 alex alex  4096 Oct 24 22:15 .
drwxr-xr-x 3 alex alex  4096 Oct 24 14:01 ..
-rw-r--r-- 1 alex alex 15194 Oct  8 11:39 egg-drop-test.md
```

Result: the directory holds the spec only. No `answer.md`, no `check_answer.py`, no
`fixtures/`. (Earlier campaign artifacts were moved out of the workspace by the user-authorized
archive `/tmp/opencode/egg-drop-before-next-run-20261024T171547Z`, receipt
`ARCHIVE-RECEIPT.md`: 32 entries, nothing deleted, spec untouched.)

## A6. Spec fingerprint

Command and output (verbatim):

```bash
sha256sum experiments/egg-drop/egg-drop-test.md
```
```text
8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e  experiments/egg-drop/egg-drop-test.md
```

Size: 15194 bytes, 289 lines (`wc -l`). This hash matches the one recorded in the archive
receipt (spec unchanged before/after the archive), so the read-only input is the same document
the rubric line references in the status file are taken from (`egg-drop-test.md:236-243`,
`:268-273`).

## A7. Bootstrap state / blocker

- Baseline (this file): **written**.
- Charter `.pdca/egg-drop/charter-r1.md`: **NOT written** — the brief supplied the verbatim
  planner-decision section as a literal placeholder
  (`--- BEGIN VERBATIM PLANNER DECISION --- [PASTE] --- END ... ---`), and no planner decision
  text with its `RECIPE` block exists in the workspace or in
  `/tmp/opencode/**` (searched). An immutable charter is not fabricated.
- Status `.pdca/status/egg-drop-1.md`: **NOT written** — its mandatory `Recipe:` field is
  defined as the charter's `RECIPE` block verbatim, so it inherits the same gap.
- Nothing was written outside `.pdca/egg-drop/**`; no `git add`, no commit, no push.

## A8. A7 resolved (appended, A1–A7 facts unchanged)

At 2026-10-24T17:29Z the orchestrator supplied the planner decision text verbatim (the earlier
placeholder was its own mistake). Subsequently written: `.pdca/egg-drop/charter-r1.md` (immutable
charter r1, sha256 `b80d8034…`) and `.pdca/status/egg-drop-1.md` (status `running`). Section A7
above is kept as the historical bootstrap state; it no longer describes the tree.
