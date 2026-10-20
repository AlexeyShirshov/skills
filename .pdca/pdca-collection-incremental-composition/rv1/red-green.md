# Red evidence — D2 (red guards before the contract change)

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`.

Baseline for comparison (D0): pdca 101 tests / 22 skipped, pdca-entry 23 / 0, both exit 0
(`baseline.md`). After part A: pdca 115 tests / 22 skipped, pdca-entry 28 / 0 — the delta is
exactly the 14 + 5 new methods below; no pre-existing test was removed, renamed or weakened.
Every failure recorded here is an `AssertionError` from a **new** test; there are no import,
collection or error (`ERROR:`) entries in either log. All red tests read repository text only —
no model, no network.

## Part A — five test files (added red guards)

| new test id | file | AC ids | expected red reason | observed result | log path |
|---|---|---|---|---|---|
| `RunnerTwoModesTest.test_runner_names_both_execution_modes` | `opencode/pdca/tests/test_orchestrator_variant_routing.py` | AC01, AC02, AC11, AC18 | canonical asset has no `execution_kind`, no `collection-lane`, no `step orchestrator` mode name | FAIL — 4 subTest `AssertionError`s (`execution_kind`, `collection-lane`, `step orchestrator`, `collection-lane`) | `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d2a-red-pdca.log` |
| `RunnerTwoModesTest.test_runner_does_not_add_layers_or_a_model` | same | AC01, AC11 | negative guard: a `campaign-agent`/`cycle-agent` layer or a `model:` key would be added | PASS on the pre-change tree (guard is protective) | same |
| `RunnerMetadataBoundaryTest.test_runner_receives_metadata_from_tool_outputs` | `opencode/pdca/tests/test_routing_consistency.py` | AC11 | asset never says metadata arrives via `tool output(s)` | FAIL — `assertRegex` `AssertionError` | same |
| `RunnerMetadataBoundaryTest.test_runner_reads_durable_state_only_in_scope` | same | AC11 | no `scoped`/`host-permitted` read boundary | FAIL — `assertTrue` `AssertionError` | same |
| `RunnerMetadataBoundaryTest.test_runner_does_not_search_the_workspace_or_shell_out` | same | AC11 | negative guard: no workspace discovery, no `rg`/`grep` runner action | PASS on the pre-change tree (guard is protective) | same |
| `RunnerAssetBoundaryTest.test_runner_asset_denies_edit_write_and_bash` | `opencode/pdca/tests/test_permission_boundaries.py` | AC11 | preservation guard: asset keeps `edit`/`write`/`bash` deny | PASS (unchanged frontmatter) | same |
| `RunnerAssetBoundaryTest.test_runner_asset_task_is_default_deny_with_the_role_allowlist` | same | AC11 | preservation guard: `task` default deny + existing role allowlist | PASS (unchanged frontmatter) | same |
| `RunnerAssetBoundaryTest.test_runner_asset_grants_itself_no_read_write_or_bash_allow` | same | AC11 | preservation guard: asset grants no `read`/`write`/`bash` allow | PASS (unchanged frontmatter) | same |
| `RunnerAssetBoundaryTest.test_skill_loading_fallback_belongs_to_an_authorized_role` | same | AC11, AC12 | fallback paragraph ("if the host cannot load it, read its `SKILL.md`…") names no `authorized role`, no `pdca-scout` | FAIL — `assertTrue` `AssertionError` | same |
| `CompositionTest.test_priority_rows_are_unchanged` | `opencode/pdca-entry/tests/test_contract.py` | AC02, AC13 | preservation guard: rows 0–5 and their five labels stay in order | PASS (table unchanged) | `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d2a-red-pdca-entry.log` |
| `CompositionTest.test_execution_kind_is_not_selected_variant` | same | AC02 | entry has no `execution_kind` and no "different fields" statement | FAIL — 2 subTest `AssertionError`s (missing token; missing phrasing) | same |
| `CompositionTest.test_a_batch_may_contain_campaign_units` | same | AC01, AC02 | no sentence says a collection/batch contains campaign units (the existing "…not a campaign…" sentence is not a containment statement) | FAIL — `assertTrue` `AssertionError` | same |
| `CompositionTest.test_medium_primary_hands_off_to_the_cheap_primary` | same | AC13 | no sentence combines handoff + medium/strong primary + cheap primary | FAIL — `assertTrue` `AssertionError` | same |
| `CompositionTest.test_no_rerouting_after_the_contract_starts` | same | AC02, AC06 | preservation guard: `do not re-route` present | PASS (already stated) | same |
| `CompositionDocsTest.test_incremental_article_exists_in_both_languages` | `opencode/pdca/tests/test_docs_sources.py` | AC17 | `docs/pdca-incremental.md` does not exist yet (only the RU article exists) | FAIL — `assertTrue` `AssertionError` | `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d2a-red-pdca.log` |
| `CompositionDocsTest.test_article_pairs_exist` | same | AC17 | preservation guard: collection/guide/install EN↔RU pairs exist | PASS | same |
| `CompositionDocsTest.test_readme_says_a_collection_may_contain_a_campaign` | same | AC01, AC17 | README never says a collection may contain campaign units | FAIL — `assertTrue` `AssertionError` | same |
| `CompositionDocsTest.test_install_docs_do_not_claim_a_bare_depth_is_enough` | same | AC12 | install docs present bare depth sufficiency claims (`≥ 2` / `>= 2` near `subagent_depth`/`глубин`) | FAIL — 8 findings: `docs/install.md:285,286`, `docs/ru/install.md:243,244`, `docs/install-prompt.md:101,132` | same |
| `CompositionDocsTest.test_install_docs_state_verification_status` | same | AC12 | no verification-status/precondition statement in any of the three install files | FAIL — 3 subTest `AssertionError`s (`docs/install.md`, `docs/install-prompt.md`, `docs/ru/install.md`) | same |

Counts: **19 new tests** (14 in `opencode/pdca/tests`, 5 in `opencode/pdca-entry/tests`);
**11 red, 8 green/protective** on the pre-change tree.

Suite results (commands, run one at a time from `/home/alex/sources/skills`):

| suite | invocation | exit_code | Ran | failures | errors | skipped | log |
|---|---|---|---|---|---|---|---|
| pdca | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 1 | 115 | 13 | 0 | 22 | `do-d2a-red-pdca.log` |
| pdca-entry | `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v` | 1 | 28 | 4 | 0 | 0 | `do-d2a-red-pdca-entry.log` |

The failure counts exceed the red test count because `subTest` cases are tallied individually
(e.g. four mode-name subTests in one method). Skips are unchanged from baseline (22 in `pdca`,
0 in `pdca-entry`); a skip is not a pass.

## Part B — `pdca-collection` / `pdca-incremental` (added red guards)

Part B touches only the seven existing suites below (F05–F11); no new suite, no contract edit.
Every new method is RED on the pre-change tree because at least one required token does not
exist yet. Negative guards are part of the same methods, so they activate as soon as the token
lands; none of them matches the pre-change text (verified: 0 matches for the runtime-status,
first-steps-reservation, outer-commit-ban and campaign-in-campaign patterns).

| new test id | file | AC ids | expected red reason | observed result | log path |
|---|---|---|---|---|---|
| `CollectionUnitPreparationBarrierTest.test_pipeline_declares_execution_kind_and_both_kinds` | `opencode/pdca-collection/tests/test_plan_barrier.py` | AC03 | contract has no `execution_kind` and no `campaign` kind | FAIL — 2 subTest `AssertionError`s (`execution_kind`, `campaign`) | `do-d2b-red-pdca-collection.log` |
| `CollectionUnitPreparationBarrierTest.test_preparation_state_gates_dispatch_on_ready` | same | AC03, AC05 | no `preparation_state`/`preparation_ref`/`@r` fields, no state values | FAIL — 4 subTest `AssertionError`s + empty-window assert | same |
| `CollectionUnitPreparationBarrierTest.test_preparation_state_is_readiness_not_completion` | same | AC05 | readiness-not-completion sentence absent (no `preparation_state` window at all) | FAIL — `assertTrue` `AssertionError` | same |
| `CollectionUnitPreparationBarrierTest.test_preparation_ref_is_single_authoritative` | same | AC05 | no `preparation_ref`, hence no `единственн` binding | FAIL — `assertTrue` `AssertionError` (empty windows) | same |
| `CollectionUnitPreparationBarrierTest.test_unit_disposition_values_are_declared` | same | AC14 | no `disposition`/`active`/`paused`/`finalized` | FAIL — 4 subTest `AssertionError`s | same |
| `CollectionUnitPreparationBarrierTest.test_unit_preparation_artifact_and_campaign_binding` | same | AC03, AC14 | no `campaign_ref`, no `preparation.md`, no unit path template | FAIL — 3 subTest `AssertionError`s | same |
| `CollectionUnitPreparationBarrierTest.test_barrier_ready_names_both_execution_kinds` | same | AC03, AC14 | no `barrier-ready` / `baseline bootstrap` / `change-producing DO`; runtime-status negative guard in the same method | FAIL — 3 subTest `AssertionError`s | same |
| `CollectionContractSemanticsTest.test_lane_pause_is_derived_and_adds_no_new_status` | `opencode/pdca-collection/tests/test_verification_recovery.py` | AC07 | no `paused`, no `производн`, no `новых статусов`; `blocked`-definition negative guard in the same method | FAIL — `assertIn` `AssertionError` (`paused`) | same |
| `CollectionContractSemanticsTest.test_failure_recovery_writes_a_checkpoint_and_resumes` | same | AC08 | no `resume`, no `group-stop` | FAIL — 2 subTest `AssertionError`s | same |
| `CollectionContractSemanticsTest.test_final_disposition_is_explicit_and_only_accepted_met_is_done` | same | AC08 | no `явн`, no `только принятый` | FAIL — `assertIn` `AssertionError` (`явн`) | same |
| `RoutingGuardTest.test_reservation_covers_the_whole_task` | `opencode/pdca-collection/tests/test_routing_guard.py` | AC09 | no `резервац`/`всю задачу`/`сериализ`/`непересечен`; first-steps negative guard in the same method | FAIL — 4 subTest `AssertionError`s | same |
| `RoutingGuardTest.test_reservation_is_renegotiated_before_any_recluster` | same | AC15 | no `пересогласован`, no `поверхност` | FAIL — 2 subTest `AssertionError`s + `резервац` | same |
| `GitModelContractTextTest.test_commit_policy_none_is_declared` | `opencode/pdca-collection/tests/test_git_model.py` | AC10 | `Commit policy: none` absent, so the `внешн`-near-`commit` scope is absent | FAIL — `assertIn` `AssertionError` (`Commit policy: none`) | same |
| `GitModelContractTextTest.test_commit_policy_none_does_not_forbid_the_outer_commit` | same | AC10 | no `preflight`, no `блокер`; outer-commit-ban negative guard in the same method | FAIL — `assertIn` `AssertionError` (`preflight`) | same |
| `RunnerAssetTest.test_runner_declares_execution_kind_and_the_lane_mode` | `opencode/pdca-collection/tests/test_orchestrator_asset.py` | AC01, AC11 | canonical asset has no `execution_kind`, no `collection-lane`, no `step orchestrator` | FAIL — 3 subTest `AssertionError`s | same |
| `RunnerAssetTest.test_runner_adds_no_agent_layers_and_keeps_the_family_roles` | same | AC01, AC11 | the mode field is absent (the no-layer/no-`model:` guard stays protective) | FAIL — `assertIn` `AssertionError` (`execution_kind`) | same |
| `CompositionContractTest.test_execution_kind_is_a_field_and_preparation_is_given_not_copied` | `opencode/pdca-incremental/tests/test_contract.py` | AC02, AC04 | no `execution_kind`, no `preparation_ref`, no `collection-lane`, no `не копир` | FAIL — 3 subTest `AssertionError`s | `do-d2b-red-pdca-incremental.log` |
| `CompositionContractTest.test_disposition_and_pause_are_declared_states` | same | AC06, AC15 | no `disposition`, no `paused`, no `готовност`, no `пауза` | FAIL — 3 subTest `AssertionError`s + empty-window assert | same |
| `CompositionContractTest.test_one_lane_and_no_campaign_in_campaign` | same | AC02, AC15 | no `один лейн`, no `рекурси`; campaign-in-campaign negative guard in the same method | FAIL — `assertIn` `AssertionError` (`один лейн`) | same |
| `CompositionContractTest.test_commit_policy_none_keeps_the_outer_commit` | same | AC06 | `Commit policy: none` absent, so no `внешн` scope near `commit` | FAIL — `assertTrue` `AssertionError` (empty windows) | same |
| `CompositionContractTest.test_readiness_is_concrete_per_step` | same | AC04 | no `конкретн` per-step readiness | FAIL — `assertIn` `AssertionError` (`конкретн`) | same |
| `CompositionContractTest.test_required_sections_and_step_row_survive` | same | AC02, AC06 | headings and the `STEP N` row survive, but `execution_kind` is absent | FAIL — `assertIn` `AssertionError` (`execution_kind`) | same |
| `RunnerAssetTest.test_runner_declares_execution_kind_and_the_lane_mode` | `opencode/pdca-incremental/tests/test_orchestrator_asset.py` | AC01, AC11 | canonical asset has no `execution_kind`, no `collection-lane`, no `step orchestrator` | FAIL — 3 subTest `AssertionError`s | same |
| `RunnerAssetTest.test_runner_adds_no_agent_layers_and_keeps_the_family_roles` | same | AC01, AC11 | the mode field is absent (the no-layer/no-`model:` guard stays protective) | FAIL — `assertIn` `AssertionError` (`execution_kind`) | same |

Counts: **24 new tests** (16 in `opencode/pdca-collection/tests`, 8 in
`opencode/pdca-incremental/tests`); **24 red, 0 pre-existing failures**. Every failure is an
`AssertionError` from a new test; no `ERROR:`/import/collection entry in either log.

| suite | invocation | exit_code | Ran | failures | errors | skipped | log |
|---|---|---|---|---|---|---|---|
| pdca-collection | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 1 | 85 | 35 | 0 | 7 | `do-d2b-red-pdca-collection.log` |
| pdca-incremental | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v` | 1 | 52 | 14 | 0 | 0 | `do-d2b-red-pdca-incremental.log` |

Baseline (D0): pdca-collection 69 / 7 skipped, pdca-incremental 44 / 0. The delta is exactly the
16 + 8 new methods (24); skips are unchanged; failure counts exceed the red test count because
`subTest` cases are tallied individually. To make every new method red today, each negative
guard shares a method with a still-missing positive token; the negative regexes themselves
already hold on the pre-change text.

## D3 — contracts applied (entry / collection / incremental)

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`. Scope: `opencode/pdca-entry/SKILL.md`,
`opencode/pdca-collection/SKILL.md`, and in `opencode/pdca-incremental/SKILL.md` only
§«Статус-файл кампании» and §«0. Bootstrap». No test, runner or doc file was edited in D3.

**Resume note.** A server restart cancelled the previous D3 run after the edits were written.
The working tree was audited against the D3 checklist (items 1–15 for collection, A for entry,
C for incremental): every required token/statement is present, so no additional contract edit was
needed. All four suites were re-run from scratch after the audit; the numbers below are from this
resumed run.

| suite | invocation | exit_code | Ran | failures | errors | skipped | log |
|---|---|---|---|---|---|---|---|
| pdca-entry | `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v` | 0 | 28 | 0 | 0 | 0 | `do-d3-resume-pdca-entry.log` |
| pdca-collection | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 1 | 85 | 4 | 0 | 7 | `do-d3-resume-pdca-collection.log` |
| pdca-incremental | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v` | 1 | 52 | 4 | 0 | 0 | `do-d3-resume-pdca-incremental.log` |
| pdca | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 1 | 115 | 13 | 0 | 22 | `do-d3-resume-pdca.log` |

No existing test regressed against D2: entry 28/4 → 28/0; collection 85/35 → 85/4;
incremental 52/14 → 52/4; pdca 115/13 → 115/13. The remaining failures belong to D4 (canonical
runner asset, not yet edited) and D6/D7 (install docs and the new article/README), never to a D3
contract file.

| test id | status now | reason |
|---|---|---|
| `CompositionTest.test_priority_rows_are_unchanged` (entry) | PASS | protective: rows 0–5 and their labels unchanged and in order |
| `CompositionTest.test_execution_kind_is_not_selected_variant` (entry) | PASS | both fields distinguished; `selected_variant` only for a cycle/step |
| `CompositionTest.test_a_batch_may_contain_campaign_units` (entry) | PASS | a batch may contain `execution_kind=campaign` units |
| `CompositionTest.test_medium_primary_hands_off_to_the_cheap_primary` (entry) | PASS | explicit handoff to the cheap primary preserving refs |
| `CompositionTest.test_no_rerouting_after_the_contract_starts` (entry) | PASS | protective: literal `re-rout` present; loop-backs belong to the contract |
| `RunnerTwoModesTest.test_runner_names_both_execution_modes` (pdca) | FAIL — D4 | runner asset lacks `execution_kind`, `collection-lane`, `step orchestrator` (4 subTests) |
| `RunnerTwoModesTest.test_runner_does_not_add_layers_or_a_model` (pdca) | PASS | protective: no `campaign-agent`/`cycle-agent`, no `model:` |
| `RunnerMetadataBoundaryTest.test_runner_receives_metadata_from_tool_outputs` (pdca) | FAIL — D4 | runner asset lacks regex `tool outputs?` |
| `RunnerMetadataBoundaryTest.test_runner_reads_durable_state_only_in_scope` (pdca) | FAIL — D4 | runner asset lacks the scoped/host-permitted durable-read boundary |
| `RunnerMetadataBoundaryTest.test_runner_does_not_search_the_workspace_or_shell_out` (pdca) | PASS | protective: no workspace discovery / `rg`/`grep` in the runner |
| `RunnerAssetBoundaryTest.test_runner_asset_denies_edit_write_and_bash` (pdca) | PASS | protective: runner frontmatter unchanged |
| `RunnerAssetBoundaryTest.test_runner_asset_task_is_default_deny_with_the_role_allowlist` (pdca) | PASS | protective: `task` default deny, allowlist unchanged |
| `RunnerAssetBoundaryTest.test_runner_asset_grants_itself_no_read_write_or_bash_allow` (pdca) | PASS | protective: no `read`/`write`/`bash` allow |
| `RunnerAssetBoundaryTest.test_skill_loading_fallback_belongs_to_an_authorized_role` (pdca) | FAIL — D4 | fallback paragraph names neither `authorized role` nor `pdca-scout` |
| `CompositionDocsTest.test_incremental_article_exists_in_both_languages` (pdca) | FAIL — D7 | `docs/pdca-incremental.md` does not exist yet |
| `CompositionDocsTest.test_article_pairs_exist` (pdca) | PASS | protective: existing EN↔RU article pairs intact |
| `CompositionDocsTest.test_readme_says_a_collection_may_contain_a_campaign` (pdca) | FAIL — D7 | README lacks the campaign-unit containment statement |
| `CompositionDocsTest.test_install_docs_do_not_claim_a_bare_depth_is_enough` (pdca) | FAIL — D6 | bare depth claims remain at `docs/install.md:285,286`, `docs/ru/install.md:243,244`, `docs/install-prompt.md:101,132` |
| `CompositionDocsTest.test_install_docs_state_verification_status` (pdca) | FAIL — D6 | `docs/install.md`, `docs/install-prompt.md`, `docs/ru/install.md` lack the verification-status/prerequisite statement (3 subTests) |
| `CollectionUnitPreparationBarrierTest.test_pipeline_declares_execution_kind_and_both_kinds` | PASS | `execution_kind` and both kinds declared |
| `CollectionUnitPreparationBarrierTest.test_preparation_state_gates_dispatch_on_ready` | PASS | `preparation_state`/`preparation_ref`/`@r<k>` gate dispatch |
| `CollectionUnitPreparationBarrierTest.test_preparation_state_is_readiness_not_completion` | PASS | readiness ≠ completion is stated |
| `CollectionUnitPreparationBarrierTest.test_preparation_ref_is_single_authoritative` | PASS | single authoritative `preparation_ref` stated |
| `CollectionUnitPreparationBarrierTest.test_unit_disposition_values_are_declared` | PASS | `active`/`paused`/`finalized` declared |
| `CollectionUnitPreparationBarrierTest.test_unit_preparation_artifact_and_campaign_binding` | PASS | `campaign_ref` + unit preparation path declared |
| `CollectionUnitPreparationBarrierTest.test_barrier_ready_names_both_execution_kinds` | PASS | barrier-ready for both kinds; runtime negative guard holds |
| `CollectionContractSemanticsTest.test_lane_pause_is_derived_and_adds_no_new_status` | PASS | pause derived from `disposition`; no new status |
| `CollectionContractSemanticsTest.test_failure_recovery_writes_a_checkpoint_and_resumes` | PASS | checkpoint/resume and group-stop declared |
| `CollectionContractSemanticsTest.test_final_disposition_is_explicit_and_only_accepted_met_is_done` | PASS | only accepted `met` → `done`; explicit final disposition |
| `RoutingGuardTest.test_reservation_covers_the_whole_task` | PASS | whole-task reservation; first-steps negative guard holds |
| `RoutingGuardTest.test_reservation_is_renegotiated_before_any_recluster` | PASS | stop/reapproval on expansion; no auto `recluster` |
| `GitModelContractTextTest.test_commit_policy_none_is_declared` | PASS | `Commit policy: none` declared with the outer-commit scope |
| `GitModelContractTextTest.test_commit_policy_none_does_not_forbid_the_outer_commit` | PASS | `preflight` blocker declared; no outer-commit ban |
| `RunnerAssetTest.test_runner_declares_execution_kind_and_the_lane_mode` (collection) | FAIL — D4 | runner asset lacks `execution_kind`, `collection-lane`, `step orchestrator` |
| `RunnerAssetTest.test_runner_adds_no_agent_layers_and_keeps_the_family_roles` (collection) | FAIL — D4 | runner asset lacks `execution_kind` (no-layer guard itself holds) |
| `CompositionContractTest.test_execution_kind_is_a_field_and_preparation_is_given_not_copied` | PASS | `execution_kind`, `preparation_ref`, `не копир` present |
| `CompositionContractTest.test_disposition_and_pause_are_declared_states` | PASS | `disposition`, `paused`, readiness ≠ runtime, pause ≠ final |
| `CompositionContractTest.test_one_lane_and_no_campaign_in_campaign` | PASS | one lane; recursion ban present |
| `CompositionContractTest.test_commit_policy_none_keeps_the_outer_commit` | PASS | `Commit policy: none` + outer `внешн` commit scope |
| `CompositionContractTest.test_readiness_is_concrete_per_step` | PASS | concrete per-step readiness |
| `CompositionContractTest.test_required_sections_and_step_row_survive` | PASS | D5 headings and the `STEP N` row intact; `execution_kind` present |
| `RunnerAssetTest.test_runner_declares_execution_kind_and_the_lane_mode` (incremental) | FAIL — D4 | runner asset lacks `execution_kind`, `collection-lane`, `step orchestrator` |
| `RunnerAssetTest.test_runner_adds_no_agent_layers_and_keeps_the_family_roles` (incremental) | FAIL — D4 | runner asset lacks `execution_kind` (no-layer guard itself holds) |

## D4 — canonical runner asset + five byte-identical mirrors

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`. Scope: canonical
`opencode/pdca/assets/agents/pdca-orchestrator.md` rewritten (frontmatter untouched) and copied
with `cp` to the five mirrors; no mirror was edited individually and no test file was changed.

The asset now defines one dispatcher in two modes — `step orchestrator` (one step per call, the
cheap primary owns the campaign state machine) and `collection-lane` (`mode=collection-lane`:
campaign state machine + current step's cycle inline in one session, no separate campaign or
cycle agent, no extra `Task` level). `selected_variant` stays given/immutable and fail closed;
the `dispatch` policy belongs to the loaded contract; metadata arrives via tool outputs; durable
read is limited to the host-permitted/`scoped` lane/campaign status files with the
`authorized role` (`pdca-scout`) skill-loading fallback; role graph unchanged, `escalate → scout`
edge kept; pause derived from the current unit's `disposition`.

Canonical size: 127 lines, 8353 bytes.

| mirror | `cmp` against canonical |
|---|---|
| `opencode/pdca-entry/assets/agents/pdca-orchestrator.md` | exit_code=0 (identical) |
| `opencode/pdca-coder/assets/agents/pdca-orchestrator.md` | exit_code=0 (identical) |
| `opencode/pdca-dotnet/assets/agents/pdca-orchestrator.md` | exit_code=0 (identical) |
| `opencode/pdca-collection/assets/agents/pdca-orchestrator.md` | exit_code=0 (identical) |
| `opencode/pdca-incremental/assets/agents/pdca-orchestrator.md` | exit_code=0 (identical) |

| suite | invocation | exit_code | Ran | failures | errors | skipped | log |
|---|---|---|---|---|---|---|---|
| pdca | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 1 | 115 | 6 | 0 | 22 | `do-d4-pdca.log` |
| pdca-collection | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 0 | 85 | 0 | 0 | 7 | `do-d4-pdca-collection.log` |
| pdca-incremental | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v` | 0 | 52 | 0 | 0 | 0 | `do-d4-pdca-incremental.log` |
| pdca-entry (regression check) | `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v` | 0 | 28 | 0 | 0 | 0 | `do-d4-pdca-entry.log` |
| pdca-coder (regression check) | `python3 -m unittest discover -s opencode/pdca-coder/tests -p 'test_*.py' -v` | 0 | 75 | 0 | 0 | 1 | `do-d4-pdca-coder.log` |
| pdca-dotnet (regression check) | `python3 -m unittest discover -s opencode/pdca-dotnet/tests -p 'test_*.py' -v` | 0 | 320 | 0 | 0 | 29 | `do-d4-pdca-dotnet.log` |

All runner guards are green: `RunnerTwoModesTest` (both modes, no layers, no `model:`),
`RunnerMetadataBoundaryTest` (tool outputs, scoped durable read, no workspace search),
`RunnerAssetBoundaryTest` (deny edit/write/bash, task default deny with unchanged allowlist,
authorized-role fallback), and `RunnerAssetTest` in collection and incremental
(`execution_kind`, `collection-lane`, `step orchestrator`, family roles). D2/D3 red was
13 failures in `pdca` (4F), `pdca-collection` (4F) and `pdca-incremental` (4F) → now 0 in
both runner suites and 6 in `pdca`.

Remaining `pdca` failures are the docs guards only, all with expected tokens:
`CompositionDocsTest.test_incremental_article_exists_in_both_languages` (D7 —
`docs/pdca-incremental.md` + RU pair), `CompositionDocsTest.test_readme_says_a_collection_may_contain_a_campaign`
(D7 — README containment statement), `CompositionDocsTest.test_install_docs_do_not_claim_a_bare_depth_is_enough`
(D6 — remove bare depth-sufficiency claims), `CompositionDocsTest.test_install_docs_state_verification_status`
(D6, 3 subTests — `Verification status: unverified` + open prerequisite). No test regressed.

## D5 — incremental contract: contextual composition changes

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`. File: `opencode/pdca-incremental/SKILL.md`
only. +46 net lines (447 → 490 including the D3 additions); every pre-existing heading, rule,
counter and resume invariant preserved — additions are contextual and standalone semantics are
not re-declared.

| section | change |
|---|---|
| `## Роль` | campaign may be a collection unit (`execution_kind=campaign`); led by the collection lane driver (`pdca-orchestrator`, `mode=collection-lane`), not a campaign primary; stays one step at a time / one credited measurement per step / own baseline chain and stop rules; standalone model (cheap primary + one delegated step per call) explicitly unchanged |
| `## Роли, тиры и полномочия` — `STEP N` row | same RUNNER leads the campaign and the current cycle inline in collection mode, executes only the step in standalone; tier `cheap`, dispatch-only and the variant roles unchanged; the "campaign is led by the primary" bullet qualified, not removed |
| `## Инварианты кампании` | 10: campaign always occupies one lane (standalone and as a collection unit); 11: `Commit policy: none` does not forbid the collection's outer completion commit; new 12: pause (incl. `unreachable` with an allowed next target) is a checkpoint, only accepted `met` + `disposition=finalized` gives `done`, a campaign inside a collection gets no extra rights, recursion ban restated |
| `### 3. Исполнение шага` | in a collection lane the same driver runs the step's cycle inline in its own session — no separate campaign agent, no extra `Task` level; the step passes its own full PLAN of its variant; `selected_variant` is concrete for that step and comes from the durable record, not the runner |
| `### 5. Решение об остановке` | explicit disposition instead of automatic closure: `blocked`/`stopped`/`unreachable`-with-next-target = checkpoint (`disposition=paused`, unit `in-progress`), explicit resume, no infinite retry, final `incomplete`/collection group-stop only by explicit final unsuccessful disposition, pause never resets `N`/`r`/`n` |
| `## Автономный режим` | split into **Standalone** (cheap primary delegates one step per call, no approval pause between steps) and **Collection-lane** (driver leads steps inline under the collection schedule; the collection primary is not the campaign executor; pause/stop is durable) |

Not touched (D3 scope, complete): `## Статус-файл кампании`, `### 0. Bootstrap`. No test, runner
or docs file changed; no new roles, tiers, model ids, statuses or counters.

| suite | invocation | exit_code | Ran | failures | errors | skipped | log |
|---|---|---|---|---|---|---|---|
| pdca-incremental | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v` | 0 | 52 | 0 | 0 | 0 | `do-d5-pdca-incremental.log` |
| pdca-collection | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 0 | 85 | 0 | 0 | 7 | `do-d5-pdca-collection.log` |
| pdca-entry (regression check) | `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v` | 0 | 28 | 0 | 0 | 0 | `do-d5-pdca-entry.log` |
| pdca (regression check) | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 1 | 115 | 6 | 0 | 22 | `do-d5-pdca.log` |

The six `pdca` failures are byte-for-byte the D4 set (`CompositionDocsTest`: `docs/pdca-incremental.md`
+ RU pair, README containment, three install-doc `Verification status` subTests, bare depth
sufficiency) — all D6/D7 docs work, none caused by this unit. Guards green:
`CompositionContractTest.test_required_sections_and_step_row_survive` (`STEP N` row keeps
`pdca-orchestrator`), `test_one_lane_and_no_campaign_in_campaign`, `test_commit_policy_none_keeps_the_outer_commit`,
`test_readiness_is_concrete_per_step`, `test_disposition_and_pause_are_declared_states`,
`AutonomyTests` (one-step delegation, `Notice:`), `InvariantTests` and `LoopAndStopTests`.

## D6 — capability/install docs: preflight, fallback, verification status

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`. Files: `docs/install.md`,
`docs/ru/install.md`, `docs/install-prompt.md`, plus one sentence added to each of the two existing
fallback/link sections (`opencode/pdca-collection/SKILL.md` §Fallback,
`opencode/pdca-incremental/SKILL.md` §Связь с семейством). `README.md`, the articles and
`docs/pdca.md` untouched (D7 scope). No host configuration edited.

Bare depth-sufficiency claims removed (pre-edit locations):

| file:line | old claim | replacement |
|---|---|---|
| `docs/install.md:285` (§9 item 2) | "`opencode debug config` must show `experimental.subagent_depth` ≥ 2" | key must be inside `experimental`; record configured value + installed build version + date; the value is not the check |
| `docs/install.md:299` (troubleshooting) | fallback caused by "`subagent_depth` < 2" | fallback caused by "no usable nested delegation (legacy key ignored, limit too low)" |
| `docs/ru/install.md:243-244` (§9 item 2) | "должен показать `experimental.subagent_depth` ≥ 2" | same as EN |
| `docs/ru/install.md:258` (troubleshooting) | "либо `subagent_depth` < 2" | "нет рабочей вложенной делегации (legacy-ключ игнорируется, предел слишком мал)" |
| `docs/install-prompt.md:101` (step 3, V2) | "`experimental.subagent_depth` >= 2" | edge budget (`primary → driver`, `driver → role`, `escalate → scout`), counter = nesting edges below the primary (default 1), configured value is not proof, verify build version + real chain |
| `docs/install-prompt.md:132` (step 6) | "`opencode debug config` (subagent_depth >= 2)" | key visible inside `experimental`; the value is not a chain check |

`docs/install.md` §6 and `docs/ru/install.md` §6 now carry the edge-budget explanation (3 edges;
V2 counts nesting edges below the primary, default `1`, spawn while `depth < limit`; a configured
value alone does not prove the installed build supports the chain; the snippet value is an example,
not a validated budget). Troubleshooting rows no longer name any threshold.

New sections (structurally parallel EN/RU, numbering shifted in both files):
`## 10. Preflight and fallback` / `## 10. Preflight и fallback` — observable capability, safe role
resolvability check, no dummy substantive work, no invented `subagent_depth`/`cap` numbers, no
host-side parallel cap in the inspected V2 source (absence ≠ unlimited), installed-runner drift
refreshed from the canonical asset with effective permissions verified (`pdca-scout` omission
example), and the failure table (driver unavailable → exactly one flat fallback with `Notice:` +
durable reason; mandatory role unavailable → resource stop; cycle contract unavailable → fail
closed; late discovery → safe pause). `## 11. Verification status: unverified` / `## 11. Статус
проверки: не проверено` — OPEN prerequisite with the r2 EN/RU limitation wording adapted to
install-doc voice: clean-host install and `primary → driver → roles` incl. `escalate → scout`
unverified; green repository tests do not substitute; closing trigger = operator clean-host run
recording host version/date, six roles' availability, collection-lane mode + fallback, a real chain
reaching `escalate → scout`, with logs; a separate follow-up cycle records it and only that cycle may
close it.

`docs/install-prompt.md` (RU-only) carries the same preflight facts as checklist items in steps 3 and
6, no bare `>= 2`, the medium/strong-primary handoff, and the line that cold-host verification is an
open prerequisite recorded in the install docs (`docs/install.md` §11,
`Verification status: unverified`).

Medium/strong primary (task 5): `docs/install.md` §1 and `docs/ru/install.md` §1 now state that such
a primary does not launch or dispatch the cycle and does not run it flat itself — it hands off
explicitly to the cheap primary preserving the task, the status file and the `.pdca/` references;
the incremental §Связь с семейством repeats the handoff rule. The collection §Fallback gained two
sentences (parallel-cap absence ≠ unlimited; runner drift + effective permissions with the
`pdca-scout` example); no section was restructured.

Red-first: the three install-doc guards were already red on the pre-change tree (D4/D5 records) —
`test_install_docs_do_not_claim_a_bare_depth_is_enough` and the three
`test_install_docs_state_verification_status` subTests. Both now pass.

| suite | invocation | exit_code | Ran | failures | errors | skipped | log |
|---|---|---|---|---|---|---|---|
| pdca | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 1 | 115 | 2 | 0 | 22 | `do-d6-pdca.log` |
| pdca-collection | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 0 | 85 | 0 | 0 | 7 | `do-d6-pdca-collection.log` |
| pdca-incremental | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v` | 0 | 52 | 0 | 0 | 0 | `do-d6-pdca-incremental.log` |
| pdca-entry (regression check) | `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v` | 0 | 28 | 0 | 0 | 0 | `do-d6-pdca-entry.log` |

Remaining `pdca` failures are exactly the two D7 guards:
`CompositionDocsTest.test_incremental_article_exists_in_both_languages` (`docs/pdca-incremental.md`
missing) and `CompositionDocsTest.test_readme_says_a_collection_may_contain_a_campaign`. Guards now
green: `test_install_docs_do_not_claim_a_bare_depth_is_enough`,
`test_install_docs_state_verification_status` (all three subTests), `test_article_pairs_exist`,
`InstallAdapterTest.*` (both adapters, V1/V2 keys).

Grep over the three install files: `[>≥]=?\s*2` → 0 matches; "sufficien"/"guarantee" → 0 matches;
"достаточн" → 1 match at `docs/ru/install.md:71` ("глобального каталога достаточно"), which is about
the skills root, not delegation depth — no depth-sufficiency claim remains.

## D7a — incremental article: EN counterpart created, composition added to both languages

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`. Scope: `docs/pdca-incremental.md` (new) and
`docs/ru/pdca-incremental.md`. `README.md`, `docs/pdca-collection.md`, `docs/pdca-guide.md`,
`docs/ru/pdca-guide.md`, `docs/pdca.md` and the install docs were **not** touched (D7b / other units).

**Red-first.** `CompositionDocsTest.test_incremental_article_exists_in_both_languages` was red from
D2a through D6 (`docs/pdca-incremental.md` missing; D4/D5/D6 logs) and is now **PASS**. The second D7
guard, `test_readme_says_a_collection_may_contain_a_campaign`, is still **FAIL** — that is D7b's
scope, and it is the only remaining failure in the suite.

| file | lines | role |
|---|---|---|
| `docs/pdca-incremental.md` | 629 | new EN counterpart, same structure/coverage as the RU article |
| `docs/ru/pdca-incremental.md` | 650 | RU article, composition added; voice and existing sections kept |

**Heading parity (EN vs RU).** 21 headings each, identical levels and identical section numbers:
`1`, `1.1`, `2`, `3`, `3.1`, `3.2`, `4`, `4.1`, `4.2`, `5`, `5.1`–`5.7`, `6`, `7`, plus one unnumbered
final heading in both (`Sources` / `Источники`). No heading was added on one side only; `3.2` is new in
both.

**Composition coverage (both languages, same facts):**

| topic | where |
|---|---|
| campaign as a collection unit, `execution_kind=campaign`, two execution models (standalone / collection-lane), no campaign agent, no extra `Task` level | `### 3.2`, first block + model table; `§2` closing paragraph |
| no own `selected_variant`; the step's variant comes from step content and is fixed in the durable record; dispatch policy from the loaded contract | `### 3.2`, "the variant belongs to the step" |
| `preparation.md@r<k>` separate immutable/revisioned artifact, nine frame items, `preparation_ref` as a reference, renegotiation → new revision | `### 3.2`, "the frame is a separate artifact" |
| baseline bootstrap after the barrier by a dedicated executor, `Status: running`, `campaign_ref` optional → mandatory | `### 3.2`, three-operations table + following paragraph |
| readiness ≠ completion (`barrier-ready`, never `done`) | `### 3.2`; `§6` bullet |
| pause ≠ final (checkpoint, `disposition=paused`, `in-progress`, explicit resume, `N`/`r`/`n` kept, derived lane pause) | `### 3.2`; `§6` bullet |
| per-unit `disposition` separate from task status and campaign runtime `Status` | `### 3.2`, "three different fields" |
| step PLAN/approval in normal mode (brief ≠ PLAN, ≠ approval) | `### 3.2` |
| `Commit policy: none` vs the outer completion commit; no-commit conflict = preflight blocker | `### 3.2`; `§6` bullet |
| recursion ban (campaign-in-campaign, collection-in-campaign) and no extra rights | `### 3.2`; `§6` bullet |
| step's cycle led inline by the same driver | `§3.1` `STEP N` row, `§4` `STEP N` bullet |
| real nextorm campaign kept as an article illustration, explicitly not a composition rule | `§5.6` closing paragraph |

**One factual alignment.** The `§2` table row for "known list, one footprint / chain / one shared
metric" said "if the goals differ — `pdca-collection` (even with one lane)", which contradicts the
current `opencode/pdca-incremental/SKILL.md §Когда выбирать` ("если цели разные — базовые циклы") and
`§4.2` of the same article. Both languages now read "base cycles"; no other pre-existing sentence was
changed.

**Constraints checked:** no model ids (`grep -nE "model:|claude|gpt-|deepseek|subagent_depth"` → 0
matches in both files); no line-range citations (`SKILL.md:<n>` → 0 matches); every EN citation
resolves to a real `##`/`###` heading (`DocsSourceMapTest.test_citations_are_sections_or_preamble_lines`
PASS); RU keeps the `§Раздел` / closed-backtick citation style already used in that article.

| suite | invocation | exit_code | Ran | failures | errors | skipped | log |
|---|---|---|---|---|---|---|---|
| pdca | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 1 | 115 | 1 | 0 | 22 | `do-d7a-pdca.log` |
| pdca-incremental (regression) | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v` | 0 | 52 | 0 | 0 | 0 | `do-d7a-pdca-incremental.log` |
| pdca-collection (regression) | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 0 | 85 | 0 | 0 | 7 | `do-d7a-pdca-collection.log` |
| pdca-entry (regression) | `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v` | 0 | 28 | 0 | 0 | 0 | `do-d7a-pdca-entry.log` |

The single `pdca` failure is `test_readme_says_a_collection_may_contain_a_campaign` (D7b). Guards green:
`test_incremental_article_exists_in_both_languages`, `test_article_pairs_exist`,
`test_citations_are_sections_or_preamble_lines`, both install-doc guards. No test regressed against D6
(115 ran / 2F → 115 ran / 1F). D7 stays `running`: D7b (`README.md` containment statement and the
remaining §8.3 pairs) is still open.

## D7b — composition in the collection pair, the guide pair and the README

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`. Scope: `docs/pdca-collection.md`,
`docs/ru/pdca-collection.md`, `docs/pdca-guide.md`, `docs/ru/pdca-guide.md`, `README.md`. The
incremental pair (D7a), `docs/pdca.md`, `docs/ru/pdca.md` and the install docs were not touched.

**Red-first closed by this unit.** `CompositionDocsTest.test_readme_says_a_collection_may_contain_a_campaign`
had been red from D2a through D7a and is now **PASS**; it was the only remaining failure in the
`pdca` suite. No other guard was red on entry to D7b.

| file | lines | change |
|---|---|---|
| `docs/pdca-collection.md` | 278 → 384 | new `## 7. Composition: a batch may contain campaigns`; former "Where to go next" renumbered to `## 8`; `pdca-incremental.md` added to the neighbouring articles; 7 source-map rows added |
| `docs/ru/pdca-collection.md` | 284 → 387 | same section in RU (`## 7. Композиция: в пакете может быть кампания`, `## 8. Куда дальше`), same 7 source rows |
| `docs/pdca-guide.md` | 1287 → 1309 | family map brought to RU parity (the stale "four skills" count and the missing `pdca-incremental` row — the RU map already had both), new "Neighbour and composition" paragraph in §2, new "Composition" paragraph in §11 |
| `docs/ru/pdca-guide.md` | 1383 → 1401 | "Соседство и композиция" in §2, "Композиция" in §11 — same facts |
| `README.md` | 139 | `pdca-collection` and `pdca-incremental` rows; the two Usage bullets |

**Composition coverage in the collection pair (same facts, both languages):**

| topic | where |
|---|---|
| units with `execution_kind=cycle|campaign`; form decided by the collection PLAN; runner only reads it; recursion ban | §7 first paragraph |
| separate immutable/revisioned preparation document `.pdca/<collection-id>/units/<unit-id>/preparation.md`, nine frame items, `preparation_state=ready`, single authoritative `preparation_ref` `<path>@r<k>`; `campaign_ref` optional before the bootstrap and mandatory after; no baseline/runtime/step plans at the barrier | §7 "The barrier asks each unit for what that unit has" |
| baseline bootstrap after the barrier by a dedicated `pdca-executor`; not a step, not credited, no product change, no frame copy; renegotiation → new immutable revision | §7 "Baseline bootstrap happens after the barrier" |
| readiness ≠ completion (`barrier-ready` is not `done`; only an accepted `met` with `disposition=finalized` → `done`) | §7 "Readiness is not completion" |
| pause vs final (`blocked`/`stopped`/`unreachable` with an allowed next target = checkpoint; final `incomplete` + group-stop only by an explicit final unsuccessful disposition; explicit resume; `N`/`r`/`n` kept; criteria never changed silently) | §7 "Pause is not final" |
| per-unit `disposition`, derived lane pause, no new status even for `blocked` | §7 "Disposition, and the derived lane pause" |
| the separate state spaces (readiness / campaign runtime `Status` / `disposition`; primary or planner owns the semantics, executor writes) | §7 "Three separate state spaces" |
| surface ownership, conservative whole-task reservation, campaign surface as a subset, expansion = stop/reapproval without auto-recluster | §7 "The surface belongs to the collection" |
| the collection-lane driver (same `pdca-orchestrator`, `mode=collection-lane`, campaign inline, one lane), step PLAN/approval, no campaign agent / no new `Task` level | §7 "The driver is the same cheap runner" |
| campaign acceptance ≠ the collection's common CHECK; collection owns the external commit/branch lifecycle; `Commit policy: none`; preflight blocker | §7 "Completion and commits stay on the collection's level" |
| preflight (observable capability, no dummy work, no invented number) and exactly one fallback with `Notice:` + durable reason; unavailable role → resource stop; unavailable contract → fail closed; late discovery → safe pause | §7 "Preflight and fallback" |

**Guide pair.** §2 now states the neighbour relation — a collection batch may contain cycle units and
campaign units, a campaign inside it stays sequential (one step, one lane, no internal parallelism),
the entry priorities are unchanged (collection → incremental → .NET → other code → neutral), no sixth
contract, no re-routing after a contract starts, and `execution_kind` ≠ `selected_variant`. §11 carries
the same relation in one paragraph and points to the collection article §7. No applied case was
introduced. The EN family map's stale count ("four skills", with five rows) and its missing
`pdca-incremental` row were aligned to the RU map, which already had both; the other rows are
unchanged.

**README.** The `pdca-collection` row now says a batch may contain single-cycle and sequential
campaign units; the `pdca-incremental` row says a campaign can be a unit of a batch and then stays
sequential; the two Usage bullets state the same. Table format and all other rows are unchanged. The
README does not list articles, so no article link was added there; the new EN article is reachable
from the guide and the collection article.

**Heading parity.** Collection pair: 14 headings each (1 × `#`, 9 × `##`, 4 × `###`), identical
numbering `1`–`8` plus `Sources` / `Источники`, same P/D/C/A subsections. Guide pair: 39 headings each
(1 × `#`, 16 × `##`, 22 × `###`), unchanged structure.

**Constraints checked.** No line-range citations added (the new text cites only `opencode/<skill>/SKILL.md §Раздел`
/ `§Section`; the pre-existing numeric references in the guide's source preamble are unchanged and
still pass); no model ids; no invented numbers; only `##`/`###` headings are cited (the `####`
subsections of the collection contract are reached through their `###` parents).

| suite | invocation | exit_code | Ran | failures | errors | skipped | log |
|---|---|---|---|---|---|---|---|
| pdca | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 0 | 115 | 0 | 0 | 22 | `do-d7b-pdca.log` |
| pdca-collection | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 0 | 85 | 0 | 0 | 7 | `do-d7b-pdca-collection.log` |
| pdca-incremental | `python3 -m unittest discover -s opencode/pdca-incremental/tests -p 'test_*.py' -v` | 0 | 52 | 0 | 0 | 0 | `do-d7b-pdca-incremental.log` |
| pdca-entry | `python3 -m unittest discover -s opencode/pdca-entry/tests -p 'test_*.py' -v` | 0 | 28 | 0 | 0 | 0 | `do-d7b-pdca-entry.log` |

All four suites are green: every composition guard added in D2 is now satisfied, the docs guards
(`test_incremental_article_exists_in_both_languages`, `test_article_pairs_exist`,
`test_readme_says_a_collection_may_contain_a_campaign`,
`test_citations_are_sections_or_preamble_lines`, both install-doc guards) are green, and no
pre-existing test regressed (`pdca` 115 ran / 1F → 0F; skips unchanged at 22, and a skip is not a
pass). D7 is complete.

Final confirmation re-run after the last administrative edit (identical commands, `/tmp/.../do-d7b-final-*.log`):
pdca 115 / 0F / 22S exit 0; pdca-collection 85 / 0F / 7S exit 0; pdca-incremental 52 / 0F exit 0;
pdca-entry 28 / 0F exit 0. No file changed between the two runs except `.pdca/` artifacts.

## D8 — full verification matrix

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`. Read-only verification: no project file was
edited; only this evidence block, `verification.md`, the status-file D8 row and the progress-log line
were written. Full document: `.pdca/pdca-collection-incremental-composition/rv1/verification.md`.

| variant | suites (ran / F / E / S) | exit |
|---|---|---|
| A — `OPENCODE_CONFIG_REPO` unset | pdca 115/0/0/**22**, entry 28/0/0/0, collection 85/0/0/**7**, incremental 52/0/0/0 → 280 tests, **29 skips** | 0 ×4 |
| B — hostcfg (`/home/alex/sources/opencode-config`) | pdca 115/0/0/**0**, entry 28/0/0/0, collection 85/0/0/**0**, incremental 52/0/0/0 → 280 tests, **0 skips** | 0 ×4 |
| C — SIM `git-model-sim.sh` | unset: six `OK:` lines; hostcfg: same six `OK:` + non-failing notice `SKIP: /home/alex/sources/opencode-config/config/agents/lane.md not installed` | 0 / 0 |
| D — PARITY | canonical + 5 mirrors, 8353 bytes each (50118 total), `cmp` 5/5 identical, **0 drift** | 0 |
| E — domain non-regression | coder 75/0/0/1S, dotnet 320/0/0/29S (= pre-change D4 counts), hostcfg: both 0 skips | 0 ×2 (×2) |
| F — scope | 30 `M` + 7 `??`; (a) 31 in §8, (b) 5 `.pdca/`, (c) 2 cycle inputs, **(d) 0 out of scope**; `git diff --check` exit 0 | 0 |
| G — protected | 18 protected paths `git diff --quiet` exit 0, all present at `HEAD:`; wsl-notify status + dir untouched | 0 |

Skips are not passes: the 29 variant-A skips all carry
`host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config`; every one executed
and passed in variant B. The `lane.md` SIM notice is a skipped host check, not a pass.

Verdict: **green**, D8 done. HEAD unchanged (`dd661e7`), no commit/push, cold-host prerequisite
remains **OPEN** (`.pdca/status/pdca-collection-incremental-composition-1.md` §"Open deployment
prerequisite — cold host") and is carried to D9.

Logs: `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-*.log`.

## D9 — final review / traceability

Revision `r2`, attempt `n=1/3`, evidence contract `rv1`. Read-only review: no project file was edited;
the files written are `traceability.md`, this block and the status-file log/state line.

The 18-row matrix (AC01–AC18) is `.pdca/pdca-collection-incremental-composition/rv1/traceability.md`.
Each row was built from the design §9 and the binding AC list, then verified by opening the
implementation file and the actual test method (grep + read), not from the plan.

**Verdict: 16/18 PASS — 2 GAPs, so D9 stays `running` (not `done`).**

| GAP | AC | severity | missing |
|---|---|---|---|
| G1 | AC06 | medium | no test asserts the normal-mode step-PLAN approval rule in `pdca-collection/SKILL.md` §"Драйвер лейна и кампания" (L396–402) / §"Статус коллекции" (L525): durable pending approval ref, per-unit `disposition=paused` at the gate, brief ≠ PLAN/approval, autonomous invents no approval. Only token-level checks exist (`disposition`/`paused`/`конкретн`). |
| G2 | AC16 | low | no automated guard for the domain-agnostic property of the new composition sections (entry §Composition, collection §Единицы/§Барьер/§Резюме, incremental §Роль/§Инварианты, articles §7/§3.2). Manual review found no domain example/norm; `UniversalityTest` scans only `pdca/SKILL.md` + role assets. |

PASS: AC01–AC05, AC07–AC15, AC17, AC18; AC12 as "satisfied as documentation of the prerequisite"
(H01 `host-evidence.md` absent, spec §11.6 OPEN, not verified host execution).

Scope review (`do-d9-scope.log`, `do-d9-protected.log`): 30 `M` + 9 `??`; §8 31, `.pdca` artifacts 6,
pre-existing inputs 2; **0 out of scope**; `git diff --check` exit 0; 18/18 protected paths unchanged
(`git diff --quiet` exit 0); wsl-notify artifacts untouched (0 status entries); HEAD `dd661e7`; no
commit/push.

Final confirmation suite at the DO→CHECK boundary (variant B, hostcfg):
`do-d9-confirm-pdca.log` 115/0F/0S exit 0, `do-d9-confirm-pdca-entry.log` 28/0F/0S exit 0,
`do-d9-confirm-pdca-collection.log` 85/0F/0S exit 0, `do-d9-confirm-pdca-incremental.log` 52/0F/0S
exit 0 — 280 tests, 0 failures, 0 errors, 0 skips.

## D9b — post-hoc gap closure (G1 AC06, G2 AC16)

Plan revision `r2` (unchanged), attempt `n=1/3` (unchanged — no replan, no rejected candidate),
cycle 1. D9 defect keys **G1** and **G2** are closed by two focused tests added to the
**existing** suites (no new suite).

**Post-hoc marker.** Both guards are written after the implementation landed; they are
**post-hoc** guards, green on the working tree by construction. Their intended red state was
demonstrated against the pre-change text at `HEAD` (`dd661e7`), not by TDD ordering.

Baseline blobs extracted read-only:

```
git show HEAD:opencode/pdca-collection/SKILL.md        > rv1/baseline-collection-SKILL.md   (453 lines)
git show HEAD:opencode/pdca-incremental/SKILL.md       > rv1/baseline-incremental-SKILL.md  (399 lines)
git show HEAD:opencode/pdca/assets/agents/pdca-orchestrator.md > rv1/baseline-runner.md      (96 lines)
```

| gap | AC | new test id | file | assertions |
|---|---|---|---|---|
| G1 | AC06 | `StepPlanApprovalContractTest.test_normal_mode_step_plan_approval_is_durable_and_pauses_the_unit` | `opencode/pdca-collection/tests/test_plan_barrier.py` | (a) `normal mode` … `durable pending approval ref` in §Лейн; (b) `pending approval ref` … `disposition=paused` for the current unit; (c) `Бриф шага PLAN не подменяет` (stem `бриф` + `не подменя`) |
| G2 | AC16 | `CompositionDomainNeutralityTest.test_composition_sections_use_neutral_vocabulary_and_no_domain_examples` | `opencode/pdca/tests/test_docs_sources.py` | slices only the composition headings (collection §Единицы, §P, §Резервация; incremental §Инварианты, §Статус-файл, §0 Bootstrap; runner §Contract, §Input 1/2/3) heading→next same-level heading; requires ≥3 of the RU (`цель`/`свидетельств`/`критери`/`поверхност`/`зависимост`/`ресурс`) and ≥3 of the EN (`goal`/`evidence`/`criteria`/`surface`/`dependencies`/`resources`) vocabulary, and zero tokens from {`.NET`, `dotnet`, `performance`, `coverage`, `NuGet`, `ASP.NET`}; a missing heading is a named failure, never a skip |

### Red — baseline (pre-change text), post-hoc

Inline `python3 -c` replications of exactly the new assertions, run against the three baseline blobs.

| log | checks | outcome | exit |
|---|---|---|---|
| `rv1/posthoc-red-g1.log` | AC06 a/b/c on `baseline-collection-SKILL.md` §Лейн | **FAIL FAIL FAIL** — `pending approval ref` occurs 0× at `HEAD`; no `disposition=paused` at the gate; no `Бриф шага PLAN не подменяет` | **1** |
| `rv1/posthoc-red-g2.log` | AC16 slices on the three baselines | **FAIL** — collection headings `### Единицы коллекции и форма исполнения` and `### Резервация поверхности и её расширение` do not exist at `HEAD` (named, not skipped); EN vocabulary in the runner slice = 2 (`goal`, `criteria`) < 3; RU vocabulary 5 | **1** |

Both red logs are assertion/verdict failures (missing contract text and a failed threshold), not
syntax or import errors. Incremental/runner baselines were evaluated in the same run and reported
per file.

### Green — working tree

| suite | invocation (variant B, `OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config`) | counts | exit | log |
|---|---|---|---|---|
| pdca | `python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v` | 116 tests, 0 failures, 0 errors, 0 skips | **0** | `rv1/do-d9b-pdca.log` |
| pdca-collection | `python3 -m unittest discover -s opencode/pdca-collection/tests -p 'test_*.py' -v` | 86 tests, 0 failures, 0 errors, 0 skips | **0** | `rv1/do-d9b-pdca-collection.log` |

Variant A (`OPENCODE_CONFIG_REPO` unset) is also green: pdca 116 / 0F / 0E / **22 skipped** exit 0
(`rv1/do-d9b-nohost-pdca.log`), collection 86 / 0F / 0E / **7 skipped** exit 0
(`rv1/do-d9b-nohost-pdca-collection.log`). Both new tests run in variant A (neither is host-gated).
Counts rise 115→116 and 85→86 — exactly one test per suite, no pre-existing test removed or renamed.

**Verdict after D9b: 18/18 PASS, D9 `done`.**
