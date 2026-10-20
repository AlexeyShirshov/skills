# Verification (D8) — pdca-collection-incremental-composition, rv1

- Cycle 1 (`N` = 1), plan revision `r` = 2, attempt `n` = 1/3, evidence contract `rv1`
- Recorded: 2026-10-20T09:21Z (host clock, `date -u`)
- Workspace: `/home/alex/sources/skills`
- HEAD: `dd661e79360899f055c4cdc88719c576885bdf7a` (unchanged since D0)
- Log dir: `/tmp/opencode/pdca-collection-incremental-composition/rv1/`
- Read-only verification: **no project file was edited** before or during these runs. The only files
  written are this document, the D8 block in `red-green.md` and the progress-log line in the status
  file — all cycle-administrative artifacts under `.pdca/`.

Every invocation redirected stdout+stderr to its own log, took the exit status from the process
itself (never through a pipe) and appended it as a final `exit_code=<N>` line. Every started run is
listed; none was cancelled or over budget.

## 1. Results matrix

Environment variants are reported **separately**: A = `OPENCODE_CONFIG_REPO` unset, B = host-parity
enabled (`OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config`).

| id | command (argv) | env | exit | ran | failures | errors | skipped | log path |
|---|---|---|---|---|---|---|---|---|
| A1 | `python3 -m unittest discover -s opencode/pdca/tests -p test_*.py -v` | unset | 0 | 115 | 0 | 0 | 22 | `do-d8-nohost-pdca.log` |
| A2 | `python3 -m unittest discover -s opencode/pdca-entry/tests -p test_*.py -v` | unset | 0 | 28 | 0 | 0 | 0 | `do-d8-nohost-pdca-entry.log` |
| A3 | `python3 -m unittest discover -s opencode/pdca-collection/tests -p test_*.py -v` | unset | 0 | 85 | 0 | 0 | 7 | `do-d8-nohost-pdca-collection.log` |
| A4 | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p test_*.py -v` | unset | 0 | 52 | 0 | 0 | 0 | `do-d8-nohost-pdca-incremental.log` |
| A-total | A1–A4 | unset | 0 | **280** | **0** | **0** | **29** | — |
| B1 | `python3 -m unittest discover -s opencode/pdca/tests -p test_*.py -v` | hostcfg | 0 | 115 | 0 | 0 | **0** | `do-d8-hostcfg-pdca.log` |
| B2 | `python3 -m unittest discover -s opencode/pdca-entry/tests -p test_*.py -v` | hostcfg | 0 | 28 | 0 | 0 | **0** | `do-d8-hostcfg-pdca-entry.log` |
| B3 | `python3 -m unittest discover -s opencode/pdca-collection/tests -p test_*.py -v` | hostcfg | 0 | 85 | 0 | 0 | **0** | `do-d8-hostcfg-pdca-collection.log` |
| B4 | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p test_*.py -v` | hostcfg | 0 | 52 | 0 | 0 | **0** | `do-d8-hostcfg-pdca-incremental.log` |
| B-total | B1–B4 | hostcfg | 0 | **280** | **0** | **0** | **0** | — |
| C1 | `bash opencode/pdca-collection/tests/git-model-sim.sh` | unset | 0 | n/a (script, 6 `OK:` lines) | 0 | 0 | 0 | `do-d8-sim-nohost.log` |
| C2 | `bash opencode/pdca-collection/tests/git-model-sim.sh` | hostcfg | 0 | n/a (script, 6 `OK:` lines + 1 non-failing notice) | 0 | 0 | 0 | `do-d8-sim-hostcfg.log` |
| D1 | `cmp opencode/pdca/assets/agents/pdca-orchestrator.md opencode/<s>/assets/agents/pdca-orchestrator.md` for `s` ∈ {pdca-entry, pdca-coder, pdca-dotnet, pdca-collection, pdca-incremental} + `wc -c` on all six | — | 0 | 5 comparisons | 0 | 0 | 0 | `do-d8-parity.log` |
| E1 | `python3 -m unittest discover -s opencode/pdca-coder/tests -p test_*.py -v` | unset | 0 | 75 | 0 | 0 | 1 | `do-d8-nonreg-pdca-coder.log` |
| E2 | `python3 -m unittest discover -s opencode/pdca-dotnet/tests -p test_*.py -v` | unset | 0 | 320 | 0 | 0 | 29 | `do-d8-nonreg-pdca-dotnet.log` |
| E3 | `python3 -m unittest discover -s opencode/pdca-coder/tests -p test_*.py -v` | hostcfg | 0 | 75 | 0 | 0 | **0** | `do-d8-nonreg-hostcfg-pdca-coder.log` |
| E4 | `python3 -m unittest discover -s opencode/pdca-dotnet/tests -p test_*.py -v` | hostcfg | 0 | 320 | 0 | 0 | **0** | `do-d8-nonreg-hostcfg-pdca-dotnet.log` |
| F1 | `git rev-parse HEAD`, `git status --short --untracked-files=all`, `git diff --name-status`, `git diff --check` | — | 0 | n/a | 0 | 0 | 0 | `do-d8-scope.log` |
| G1 | `git diff --quiet -- <18 protected paths>` + `git cat-file -e HEAD:<path>` per path + foreign-artifact status | — | 0 | 18 paths checked | 0 | 0 | 0 | `do-d8-protected.log` |

Log paths are under `/tmp/opencode/pdca-collection-incremental-composition/rv1/`.

Totals without the host config repo: **280 Python tests, 0 failures, 0 errors, 29 skipped, all four
suites exit 0**. With the host config repo: **280 tests, 0 failures, 0 errors, 0 skipped, exit 0** in
all four suites. The delta 29 → 0 is the proof that the host-parity branch actually executed rather
than being silently skipped.

## 2. Skips are not passes

A skipped test is **not** a pass and is not evidence for any acceptance criterion. In variant A the
29 skips all carry the same recorded reason:

`host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config`

i.e. they are host-configuration checks that did not execute. Every one of them executed and passed
in variant B, which is why variant B is the one that supports host-parity claims; variant A alone
would leave those 29 claims "not executed".

The 29 tests that skip without the config repo (22 in `pdca`, 7 in `pdca-collection`, 0 in the other
two suites):

- `pdca` — `test_contract_consistency.ForbiddenTokenGuardTest.test_scan_is_limited_to_expected_files`
- `pdca` — `test_cost_accounting.CostAccountingTest.test_models_derive_valid_tiers`
- `pdca` — `test_cost_accounting.CostAccountingTest.test_tier_grouping_uses_the_resolved_table`
- `pdca` — `test_orchestrator_variant_routing.HostPermissionTest.test_driver_may_load_cycle_skills_and_not_brainstorming`
- `pdca` — `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_escalate_bash_is_inspection_only`
- `pdca` — `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_executor_grants_edit_and_bash`
- `pdca` — `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_planner_and_check_grant_no_bash`
- `pdca` — `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_planner_check_runner_do_not_grant_edit_or_write`
- `pdca` — `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_runner_subagent_excludes_general_and_explore`
- `pdca` — `test_routing_consistency.AdditiveIntegrationTest.test_agents_md_points_to_the_entry_without_a_phrase_table`
- `pdca` — `test_routing_consistency.AdditiveIntegrationTest.test_cycle_skills_are_not_in_the_always_on_pack`
- `pdca` — `test_routing_consistency.OrchestratorVariantSelectionTest.test_orchestrator_exists`
- `pdca` — `test_routing_consistency.OrchestratorVariantSelectionTest.test_orchestrator_subagent_allowlist_covers_universal_roles`
- `pdca` — `test_routing_consistency.PermissionRoutingTest.test_escalate_only_allows_scout`
- `pdca` — `test_routing_consistency.PermissionRoutingTest.test_planner_and_check_are_default_deny`
- `pdca` — `test_routing_consistency.ProfileBindingTest.test_deepseek_existing_roles_keep_a_model`
- `pdca` — `test_routing_consistency.ProfileBindingTest.test_deepseek_pdca_roles_mirror_host_routing`
- `pdca` — `test_routing_consistency.ProfileBindingTest.test_gp_roles_keep_a_model`
- `pdca` — `test_routing_consistency.RoleParityTest.test_assets_match_host_except_external_directory`
- `pdca` — `test_routing_consistency.RoleParityTest.test_each_role_carries_expected_tier_and_no_model`
- `pdca` — `test_routing_consistency.RoleParityTest.test_four_host_agents_exist`
- `pdca` — `test_routing_consistency.RoleParityTest.test_host_agent_identity_is_the_filename_stem`
- `pdca-collection` — `test_plan_barrier.OrchestratorCollectionPlanHandoffTest.test_orchestrator_declares_collection_task_plan_entry`
- `pdca-collection` — `test_plan_barrier.OrchestratorCollectionPlanHandoffTest.test_orchestrator_returns_plan_handoff`
- `pdca-collection` — `test_verification_recovery.CollectionContractSemanticsTest.test_definitive_incomplete_stops_whole_group`
- `pdca-collection` — `test_verification_recovery.CollectionContractSemanticsTest.test_other_groups_continue`
- `pdca-collection` — `test_verification_recovery.CollectionContractSemanticsTest.test_remaining_tasks_incomplete_reason_not_blocked`
- `pdca-collection` — `test_verification_recovery.CollectionContractSemanticsTest.test_single_group_exemption`
- `pdca-collection` — `test_verification_recovery.VerificationRecoveryRenderTest.test_in_scope_text_files_have_clean_whitespace`

The same gate accounts for the 1 `pdca-coder` skip and the 29 `pdca-dotnet` skips in E1/E2; both
counts are identical to their pre-change values recorded in D4 (75 ran / 1 skip, 320 ran / 29 skips),
so they are pre-existing host-config gating, **not** a regression introduced by this cycle. E3/E4
confirm it: with the config repo both suites run with 0 skips and 0 failures.

## 3. SIM (git model)

Both variants exit 0 with all model checks passing:

- C1 (unset): `OK: artifact branch naming consistent`, `OK: group-A merged, group-B merged, 2 merge
  commits`, `OK: conflict detected, group marked failed`, `OK: single group — commits on current
  branch, no branches, no merge`, `OK: incomplete group-B not merged, branch/tip preserved`,
  `OK: git model verified` → `exit_code=0`.
- C2 (hostcfg): identical six `OK:` lines plus one **non-failing notice**, recorded verbatim:

  `SKIP: /home/alex/sources/opencode-config/config/agents/lane.md not installed`

  The script treats a missing host lane agent as a skip of that one host check and still exits 0 with
  `OK: git model verified`. That individual host check is **not** a pass; the git-model assertions
  themselves all executed and passed.

## 4. PARITY (six runner copies)

| file | bytes | `cmp` vs canonical |
|---|---|---|
| `opencode/pdca/assets/agents/pdca-orchestrator.md` (canonical) | 8353 | — |
| `opencode/pdca-entry/assets/agents/pdca-orchestrator.md` | 8353 | identical (exit 0) |
| `opencode/pdca-coder/assets/agents/pdca-orchestrator.md` | 8353 | identical (exit 0) |
| `opencode/pdca-dotnet/assets/agents/pdca-orchestrator.md` | 8353 | identical (exit 0) |
| `opencode/pdca-collection/assets/agents/pdca-orchestrator.md` | 8353 | identical (exit 0) |
| `opencode/pdca-incremental/assets/agents/pdca-orchestrator.md` | 8353 | identical (exit 0) |
| **total** | **50118** | **0 drift, 0 `DRIFT` lines, exit 0** |

## 5. Scope diff and classification

`git diff --check` exit 0 (no whitespace errors); `git diff --name-status`: 30 modified tracked files,
all `M` (no additions/deletions/renames of tracked paths). `git status --short --untracked-files=all`
adds 7 untracked entries at snapshot time (this document was created afterwards).

| class | files | count |
|---|---|---|
| (a) in §8 scope — contracts | `opencode/pdca-entry/SKILL.md`, `opencode/pdca-collection/SKILL.md`, `opencode/pdca-incremental/SKILL.md` | 3 |
| (a) in §8 scope — runner canonical + 5 mirrors | `opencode/pdca/assets/agents/pdca-orchestrator.md`, `opencode/{pdca-entry,pdca-coder,pdca-dotnet,pdca-collection,pdca-incremental}/assets/agents/pdca-orchestrator.md` | 6 |
| (a) in §8 scope — the 12 planned test files | `opencode/pdca/tests/{test_docs_sources,test_orchestrator_variant_routing,test_permission_boundaries,test_routing_consistency}.py`, `opencode/pdca-entry/tests/test_contract.py`, `opencode/pdca-collection/tests/{test_git_model,test_orchestrator_asset,test_plan_barrier,test_routing_guard,test_verification_recovery}.py`, `opencode/pdca-incremental/tests/{test_contract,test_orchestrator_asset}.py` | 12 |
| (a) in §8 scope — docs | `README.md`, `docs/pdca-collection.md`, `docs/ru/pdca-collection.md`, `docs/pdca-incremental.md` (new), `docs/ru/pdca-incremental.md`, `docs/pdca-guide.md`, `docs/ru/pdca-guide.md`, `docs/install.md`, `docs/ru/install.md`, `docs/install-prompt.md` | 10 |
| (b) cycle administrative artifacts under `.pdca/` | `.pdca/status/pdca-collection-incremental-composition-1.md`, `.pdca/pdca-collection-incremental-composition/rv1/{baseline.md,baseline-hostcfg.md,red-green.md,verification.md}` | 5 |
| (c) pre-existing untracked cycle inputs | `docs/superpowers/specs/2026-10-20-pdca-collection-incremental-composition-design.md`, `docs/superpowers/plans/2026-10-20-pdca-collection-incremental-composition.md` | 2 |
| **(d) OUT OF SCOPE** | — | **0** |

The 12 test files match the plan's §8.2 list exactly; the 10 doc paths are the §8.3 listed set (the
EN `docs/pdca-incremental.md` is the new article, the RU article pre-existed and was revised). No
file outside §8 and the `.pdca/` administrative area was touched.

## 6. Protected files and foreign artifacts

- `git diff --quiet -- <18 paths>` → **exit 0**, i.e. all unchanged:
  `opencode/pdca/SKILL.md`, `opencode/pdca-coder/SKILL.md`, `opencode/pdca-dotnet/SKILL.md`;
  `pdca-{planner,executor,check,escalate,scout}.md` under `opencode/pdca/assets/agents/`,
  `opencode/pdca-coder/assets/agents/` and `opencode/pdca-dotnet/assets/agents/`.
  Each path was also confirmed to exist at `HEAD:`, so the quiet diff is not vacuous.
- Foreign/unrelated artifacts untouched: `git status` reports **no** entry for
  `.pdca/status/wsl-notify-session-filter-1.md` or `.pdca/wsl-notify-session-filter/`, and
  `git diff --quiet` on the status file returns 0. Both exist on disk (`-rw-r--r-- … 31192` bytes and
  the `rv1`/`rv2` evidence directories), so "untouched" is confirmed by presence + unchanged state,
  not by absence.
- No commit, no push, no branch/worktree operation: `HEAD` is still `dd661e7`, the same as D0.

## 7. Open deployment prerequisite — cold host: **OPEN**

This D8 result is repository verification only. It does **not** verify a clean-host installation and
does **not** close the prerequisite. Cold-host installation and execution of `primary → driver →
roles`, including `escalate → scout`, remain unverified; the only related host facts on record are
those in `baseline-hostcfg.md`, including an observed installed-vs-canonical runner allowlist drift
that is **not** proof of effective cold-host permissions.

Pointer: `.pdca/status/pdca-collection-incremental-composition-1.md` →
`## Open deployment prerequisite — cold host` (line 119), with its subsections
`### Unverified scope and observed host facts`, `### Why this remains open`,
`### Closing trigger and owner`, `### Documentation and dependent evidence obligations`,
`### Final English wording — documentation and handoff`,
`### Итоговая русская формулировка — документация и передача результата`. The prerequisite is
restated as OPEN in that section, in AC12, in the D1/D7 rows and in `## Risks / stop conditions`;
closing it requires an authorized clean-host run and a separate follow-up cycle, not this one.

## 8. Verdict

**green.** Every required invocation is green: A1–A4 and B1–B4 exit 0 with 0 failures/0 errors
(B additionally 0 skips), C1/C2 SIM exit 0, D1 parity 5/5 identical with 0 drift, E1–E4 domain
suites exit 0 with no new skips or failures, F1 scope with **0 out-of-scope** files, G1 protected
files unchanged and foreign artifacts untouched. D8 is **done** at the DO → CHECK gate; the cold-host
prerequisite stays **OPEN** and is carried to D9.
