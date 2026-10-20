# Baseline (D0) — pdca-collection-incremental-composition, rv1

- Cycle: 1 (`N` = 1), plan revision `r` = 1, attempt `n` = 1/3
- Recorded: 2026-10-20T06:47Z (host clock, `date -u`)
- Workspace: `/home/alex/sources/skills`
- Evidence contract revision: `rv1`
- Log dir: `/tmp/opencode/pdca-collection-incremental-composition/rv1/`

## HEAD

- `git rev-parse HEAD`: `dd661e79360899f055c4cdc88719c576885bdf7a`
- Branch: `main`
- Log: `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-git.log` (exit_code=0)

## Working tree before any change

Full `git status --short --untracked-files=all` output (verbatim, 3 entries):

```
?? .pdca/status/pdca-collection-incremental-composition-1.md
?? docs/superpowers/plans/2026-10-20-pdca-collection-incremental-composition.md
?? docs/superpowers/specs/2026-10-20-pdca-collection-incremental-composition-design.md
```

No modified (` M`/`M `) or staged entries: the tree is clean of tracked changes. All three
entries are untracked additions belonging to this cycle, not foreign work:

| Entry | Origin | Note |
|---|---|---|
| `.pdca/status/pdca-collection-incremental-composition-1.md` | this cycle's own artifact (status file, written in PLAN/DO) | created by this cycle |
| `docs/superpowers/plans/2026-10-20-pdca-collection-incremental-composition.md` | this cycle's approved implementation plan (input, created before DO) | created by this cycle in PLAN |
| `docs/superpowers/specs/2026-10-20-pdca-collection-incremental-composition-design.md` | this cycle's approved design (input, created before DO) | created by this cycle in PLAN |

- `.pdca/pdca-collection-incremental-composition/` (this cycle's evidence dir) is also this cycle's
  own artifact but does **not** appear in `git status`: it was empty at baseline time and git does
  not report empty directories.
- `.pdca/status/wsl-notify-session-filter-1.md` and `.pdca/wsl-notify-session-filter/` do **not**
  appear in the status output: no pre-existing/foreign working-tree change is present that this
  cycle must preserve.
- Conclusion: **no pre-existing changes unrelated to this cycle** were found; nothing foreign to
  preserve. `Commit policy: none` (no commit/push performed).

## Suite runs

All four commands were run sequentially from `/home/alex/sources/skills`, each redirected to its
own log with the exit status captured from the `python3` process itself (not through a pipe) and
appended to the log as a final `exit_code=<N>` line.

| suite | exit_code | Ran N tests | failures | errors | skipped | log path |
|---|---|---|---|---|---|---|
| pdca | 0 | 101 | 0 | 0 | 22 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-pdca.log` |
| pdca-entry | 0 | 23 | 0 | 0 | 0 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-pdca-entry.log` |
| pdca-collection | 0 | 69 | 0 | 0 | 7 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-pdca-collection.log` |
| pdca-incremental | 0 | 44 | 0 | 0 | 0 | `/tmp/opencode/pdca-collection-incremental-composition/rv1/baseline-pdca-incremental.log` |

Total: 237 tests, 0 failures, 0 errors, 29 skipped, all four suites exit 0.

Exact invocations:

1. `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v`
2. `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v`
3. `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v`
4. `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v`

## Skips are not passes

A skipped test is **not** counted as a pass and is not evidence for any acceptance criterion.
The 29 skips (22 pdca + 7 pdca-collection) are all gated on one condition —
`host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config` — i.e. they are
host-configuration checks that did not execute on this host. They are recorded here as
**not executed**, and they become part of the D1 fact gate (host capability): if `OPENCODE_CONFIG_REPO`
cannot be supplied, the affected claims stay "not established" rather than being treated as green.

Skipped test ids (suite / test):

- pdca: `test_contract_consistency.ForbiddenTokenGuardTest.test_scan_is_limited_to_expected_files`
- pdca: `test_cost_accounting.CostAccountingTest.test_models_derive_valid_tiers`
- pdca: `test_cost_accounting.CostAccountingTest.test_tier_grouping_uses_the_resolved_table`
- pdca: `test_orchestrator_variant_routing.HostPermissionTest.test_driver_may_load_cycle_skills_and_not_brainstorming`
- pdca: `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_escalate_bash_is_inspection_only`
- pdca: `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_executor_grants_edit_and_bash`
- pdca: `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_planner_and_check_grant_no_bash`
- pdca: `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_planner_check_runner_do_not_grant_edit_or_write`
- pdca: `test_permission_boundaries.ReadOnlyRoleBoundaryTest.test_runner_subagent_excludes_general_and_explore`
- pdca: `test_routing_consistency.AdditiveIntegrationTest.test_agents_md_points_to_the_entry_without_a_phrase_table`
- pdca: `test_routing_consistency.AdditiveIntegrationTest.test_cycle_skills_are_not_in_the_always_on_pack`
- pdca: `test_routing_consistency.OrchestratorVariantSelectionTest.test_orchestrator_exists`
- pdca: `test_routing_consistency.OrchestratorVariantSelectionTest.test_orchestrator_subagent_allowlist_covers_universal_roles`
- pdca: `test_routing_consistency.PermissionRoutingTest.test_escalate_only_allows_scout`
- pdca: `test_routing_consistency.PermissionRoutingTest.test_planner_and_check_are_default_deny`
- pdca: `test_routing_consistency.ProfileBindingTest.test_deepseek_existing_roles_keep_a_model`
- pdca: `test_routing_consistency.ProfileBindingTest.test_deepseek_pdca_roles_mirror_host_routing`
- pdca: `test_routing_consistency.ProfileBindingTest.test_gp_roles_keep_a_model`
- pdca: `test_routing_consistency.RoleParityTest.test_assets_match_host_except_external_directory`
- pdca: `test_routing_consistency.RoleParityTest.test_each_role_carries_expected_tier_and_no_model`
- pdca: `test_routing_consistency.RoleParityTest.test_four_host_agents_exist`
- pdca: `test_routing_consistency.RoleParityTest.test_host_agent_identity_is_the_filename_stem`
- pdca-collection: `test_plan_barrier.OrchestratorCollectionPlanHandoffTest.test_orchestrator_declares_collection_task_plan_entry`
- pdca-collection: `test_plan_barrier.OrchestratorCollectionPlanHandoffTest.test_orchestrator_returns_plan_handoff`
- pdca-collection: `test_verification_recovery.CollectionContractSemanticsTest.test_definitive_incomplete_stops_whole_group`
- pdca-collection: `test_verification_recovery.CollectionContractSemanticsTest.test_other_groups_continue`
- pdca-collection: `test_verification_recovery.CollectionContractSemanticsTest.test_remaining_tasks_incomplete_reason_not_blocked`
- pdca-collection: `test_verification_recovery.CollectionContractSemanticsTest.test_single_group_exemption`
- pdca-collection: `test_verification_recovery.VerificationRecoveryRenderTest.test_in_scope_text_files_have_clean_whitespace`

## Pre-existing failures

**None.** No suite was red before any change and there was no pre-existing failing test id to
separate from regressions. Every non-skipped test passed (`OK` in all four logs).

Note for D2 (red-first): because the baseline is fully green (excluding skips), a new guard that
fails after being added to a suite is attributable to the guard and the contract change, not to a
carried-over failure.

## Journal

| phase | command | exit_code | log |
|---|---|---|---|
| git | `git rev-parse HEAD`, `git branch --show-current`, `git status --short --untracked-files=all` | 0 | `baseline-git.log` |
| test | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 0 | `baseline-pdca.log` |
| test | `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v` | 0 | `baseline-pdca-entry.log` |
| test | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 0 | `baseline-pdca-collection.log` |
| test | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v` | 0 | `baseline-pdca-incremental.log` |

Skipped/failed/cancelled runs: none — every started run completed and is listed above.
