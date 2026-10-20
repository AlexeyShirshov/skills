# Baseline with host-parity enabled (D1, fact gate) — rv1

- Cycle 1 (`N` = 1), plan revision `r` = 1, attempt `n` = 1/3; evidence contract `rv1`.
- Recorded: 2026-10-20T06:52Z (host clock, `date -u`).
- Workspace: `/home/alex/sources/skills`; HEAD `dd661e79360899f055c4cdc88719c576885bdf7a` (unchanged since D0).
- Read-only run: no project file edited before or during these runs.
- Purpose: prove whether the suites are **already red** with host-parity enabled, **before** any
  contract change, so later failures cannot be attributed to this cycle.

## Invocations

All five ran sequentially from `/home/alex/sources/skills` with
`OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config`, stdout+stderr redirected to the log, the
exit status captured from the process itself (not through a pipe) and appended as a final
`exit_code=<N>` line.

1. `OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v`
2. `OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v`
3. `OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v`
4. `OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v`
5. `OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config bash opencode/pdca-collection/tests/git-model-sim.sh`

## Results

| suite | exit_code | Ran | failures | errors | skipped | log path |
|---|---|---|---|---|---|---|
| pdca | 0 | 101 | 0 | 0 | 0 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-hostcfg-pdca.log` |
| pdca-entry | 0 | 23 | 0 | 0 | 0 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-hostcfg-pdca-entry.log` |
| pdca-collection | 0 | 69 | 0 | 0 | 0 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-hostcfg-pdca-collection.log` |
| pdca-incremental | 0 | 44 | 0 | 0 | 0 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-hostcfg-pdca-incremental.log` |
| git-model-sim (`bash`) | 0 | n/a (script) | 0 | 0 | 0 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-hostcfg-git-model-sim.log` |

Totals: 237 Python tests, 0 failures, 0 errors, 0 skipped, all suites exit 0.

Skip-count change vs D0 (proof the host-parity branch really executed, not skipped): D0 ran without
`OPENCODE_CONFIG_REPO` and reported 29 skips (pdca 22, pdca-collection 7, others 0). With the variable
set every one of those host-parity tests ran and passed, so the green result is **with** parity
checks enabled, not a silent skip.

`git-model-sim.sh` printed one non-failing notice, no failing assertion:
`SKIP: /home/alex/sources/opencode-config/config/agents/lane.md not installed` — the suite treats a
missing host lane agent as a skip of that one check; the script still exited 0 with
`OK: git model verified`. Recorded as a notice, not a pass of that individual host check.

## Failing test ids

None. No test failed or errored in any of the five runs, therefore no failure reasons to list.

## Verdict

**green** — with `OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config` the tree at HEAD
`dd661e7` is fully green (237 tests, exit 0). There is **no pre-existing host-parity red**; any red
observed later in this cycle is attributable to the cycle's own changes, not to a pre-existing
host-parity breakage.

## Fact: runner allowlist — installed vs canonical

Command (log: `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-runner-installed-vs-canonical.diff`,
`diff` exit code 1):

```
diff -u /home/alex/.config/opencode/agents/pdca-orchestrator.md opencode/pdca/assets/agents/pdca-orchestrator.md
```

**They differ.** The divergence is not limited to one permission line: the installed file is an older
generation of the runner (list-style `permissions:` with `action`/`effect`, no `name:` field,
Russian free-form body), the canonical asset is the map-style `permission:` generation with an
English sectioned body. Permission-level differences, line by line:

| permission aspect | installed (`~/.config/opencode/agents/pdca-orchestrator.md`) | canonical (`opencode/pdca/assets/agents/pdca-orchestrator.md`) |
|---|---|---|
| schema | `permissions:` list of `{action, resource, effect}` | `permission:` map (`edit`/`write`/`bash`/`task`/`skill`) |
| edit | `action: edit, resource: "*", effect: deny` | `edit: deny` (same effect) |
| write | **absent** (no line) | `write: deny` |
| shell / bash | `action: shell, resource: "*", effect: deny` | `bash: deny` (same effect, different action name) |
| task/subagent default | `action: subagent, resource: "*", effect: deny` | `task: {"*": deny}` (same effect) |
| task allowlist: legacy roles | allows `planner`, `coder`, `check`, `escalate`, `scout` | **absent** (these five lines removed) |
| task allowlist: pdca roles | allows `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate` | allows the same four |
| task allowlist: `pdca-scout` | **absent** | `pdca-scout: allow` (added) |
| task allowlist: specialists | `security-auditor`, `docfx-specialist`, `dotnet-*` | same three |
| skill | `"*": allow` **and** `brainstorming: deny` | `"*": allow` only — **no `brainstorming` deny line** |

Additional related fact (outside the requested comparison): the copy the host-parity tests actually
read, `/home/alex/sources/opencode-config/config/agents/pdca-orchestrator.md`, differs from the
canonical asset in the same way (same list-style permission block), and is **not** byte-identical to
the `~/.config/opencode` copy either (7477 vs 7483 bytes; only the trailing description wording
differs). Log: `.../baseline-runner-configrepo-vs-canonical.diff` (`diff` exit code 1). Consequence
for D4: making the canonical asset byte-identical to the installed/config copies is impossible; the
mirror set is the repo's five copies, and the two host copies are drifted pre-existing state that
this cycle does not own. The suites are green **despite** that drift, so no test currently enforces
these permission lines against the host copies.
