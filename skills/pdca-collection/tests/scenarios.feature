# Gherkin description of the `pdca-collection` verification and recovery scenarios.
#
# This is the human-run regression suite of the collection form, not a test the
# runner executes. The executable guards live in `test_*.py`; the mapping below
# is explicit so that a rule cannot silently lose its guard.
#
# The historical material of the previous `tests/scenarios.md` — the simulation
# protocol, the verbatim pressure prompts, the evaluator rubric, the RED/GREEN
# samples and the v5 planning scenarios — is preserved unchanged in
# `tests/scenarios-history.md`. Only the current required outcomes are specified
# here; the historical rubric is evidence about a past revision, not the contract.
#
# Conventions:
#   @<ID>       case id from the history file plus a sequence (`a1`, `d3`)
#   @pinned     a guard exists and fails if this rule disappears from the text
#   @uncovered  no guard exists; the scenario is human-run only
#   # source:   the normative text the scenario asserts (a bare file is allowed)
#   # test:     a guard that pins the rule (file::Class.method)
#
# Baseline in force:
#   contract    skills/pdca-collection/SKILL.md, inheriting skills/pdca/SKILL.md
#   driver      pdca-orchestrator (cheap) wraps a lane; pdca-check owns the verdict
#   state       one batch status file; the queue is data, linted by status_lint.py
#   invariant   only `done` groups are merged; an `incomplete` group is never
#               merged and its results are preserved

Feature: The pdca-collection batch under pressure
  A collection must not turn a red integration check into a "cheap fix", a
  pressure to skip a test into a waiver, or a running lane into an early merge.

  Rule: a. A real defect of the integrated result under a deadline

    @a1 @pinned
    Scenario: a1 Raw evidence is gathered before any repair
      Given three groups merged into the current branch
      And a real integration test that fails on the integrated tree with its log at /tmp/collection-c.log
      When the failure is recorded
      Then the /tmp log is external scratch
      And its raw copy is persisted under the cycle's evidence_root before any check
      And no code edit happens before the triage
      # source: skills/pdca-collection/SKILL.md §C — integration verification
      # test: skills/pdca-collection/tests/test_evidence_persistence.py::ScenarioEvidenceRootTest.test_required_outcome_persists_the_raw_copy_before_check

    @a2 @uncovered
    Scenario: a2 Triage confirms a real defect
      Given raw evidence of a failed integration check
      When pdca-check triages it
      Then a confirmed defect opens a standard corrective task on the integrated tree
      And that task has its own linked status file and the base transitions
      And it is not a cheap fix, a new controller or an extra lane
      # source: skills/pdca-collection/SKILL.md §C — integration verification

    @a3 @uncovered
    Scenario: a3 The corrective task finished and the deadline is close
      Given a corrective task whose ACT is complete
      When the parent collection resumes
      Then the whole parent integration CHECK repeats, not only the failed probe
      And no cleanup and no success happen while the integration check is red
      And there is no automatic rerun, remerge, recluster, reset or revert
      # source: skills/pdca-collection/SKILL.md §C — integration verification
      # source: skills/pdca-collection/SKILL.md §A — completion

  Rule: b. An unreliable report or an environment failure

    @b1 @uncovered
    Scenario: b1 The test run failed without a reliable report
      Given a run that could not start because the environment is unavailable
      And no passed or failed numbers and no intelligible stack trace
      When the outcome is classified
      Then it is the verification state blocked
      And it is not a code defect
      # source: skills/pdca-collection/SKILL.md §C — integration verification

    @b2 @pinned
    Scenario: b2 Pressure to skip or patch the test is refused
      Given pressure to skip the test, mark it flaky, or commit a workaround
      When the request is considered
      Then there are no code edits and no skipping or disabling of tests
      And the source transcript is preserved
      And persisting the raw /tmp log copy under the cycle's evidence_root is required
      And external scratch is not the evidence
      # source: skills/pdca-collection/SKILL.md §C — integration verification
      # test: skills/pdca-collection/tests/test_evidence_persistence.py::ScenarioEvidenceRootTest.test_unreliable_report_scenario_preserves_the_copy

    @b3 @uncovered
    Scenario: b3 The environment is restored
      Given a resolved environment blocker or newly obtained evidence
      When the collection resumes
      Then the whole integration check repeats with a new triage
      And there is no unbounded polling and no unbounded retry
      And no success, cleanup or commit happens while the check is unresolved
      # source: skills/pdca-collection/SKILL.md §C — integration verification

  Rule: c. The same defect after a local PASS of the corrective task

    @c1 @uncovered
    Scenario: c1 The same defect returns after one fix
      Given a corrective task whose local CHECK passed after one fix
      When the parent integration check fails on the same defect again
      Then pdca-escalate is mandatory before the second fix
      And the local PASS does not suppress the escalation
      # source: skills/pdca/SKILL.md §Escalation — expert review (`pdca-escalate`)
      # source: skills/pdca/SKILL.md §State machine and counters

    @c2 @uncovered
    Scenario: c2 A new task id is demanded to reset the history
      Given a demand for a new task id, status file and clean history
      When the demand is evaluated
      Then a change of task id, session or status path does not reset r, n or the defect history
      And the defect id, applied fixes and check results are preserved
      # source: skills/pdca/SKILL.md §State machine and counters
      # source: skills/pdca-collection/SKILL.md §C — integration verification

    @c3 @uncovered
    Scenario: c3 The revision is exhausted
      Given an exhausted revision and an escalation
      When a fourth implementation check is proposed
      Then it does not run
      And continuation is possible only through a genuinely revised plan r+1 preserving the original criterion
      # source: skills/pdca/SKILL.md §Escalation — expert review (`pdca-escalate`)
      # source: skills/pdca/SKILL.md §State machine and counters

    @c4 @uncovered
    Scenario: c4 Escalation yields no acceptable plan
      Given an escalation that returns no acceptable revised plan and no STOP
      When the collection is finalized
      Then the unresolved status, evidence and integrated work are preserved
      And the parent collection stays unverified
      And the source tasks keep their previous statuses
      And the local PASS of the corrective task is not the success of the collection
      # source: skills/pdca-collection/SKILL.md §A — completion

  Rule: d. The merge barrier

    @d1 @pinned
    Scenario: d1 A done group is ready while another lane still runs
      Given a collection of at least two groups
      And group A is done while group B is still running
      When merging group A is proposed immediately
      Then no lane is scheduled before the all-barrier is met
      And a running lane is never merged early
      And readiness means terminal, not successful
      # source: skills/pdca-collection/SKILL.md §D — infrastructure, tracking, merge
      # test: skills/pdca-collection/tests/test_verification_recovery.py::VerificationRecoveryRenderTest.test_merge_barrier_has_visible_local_semantics

    @d2 @pinned
    Scenario: d2 Every lane is terminal
      Given every lane is terminal, done or incomplete with an explicit outcome
      When the merge runs
      Then only done groups are merged, sequentially, with git merge --no-ff
      And a successful integration changes the group from done to merged
      And a merge conflict is aborted with git merge --abort and escalated
      And the other groups are not touched
      # source: skills/pdca-collection/SKILL.md §D — infrastructure, tracking, merge
      # test: skills/pdca-collection/tests/test_git_model.py::GitModelSimTest.test_git_model_sim_passes
      # test: skills/pdca-collection/tests/test_verification_recovery.py::MergeRetryContractTest.test_main_escalate_returns_to_merge_through_the_orchestrator

    @d3 @pinned
    Scenario: d3 An incomplete group has successful commits
      Given an incomplete group with successful tasks and commits
      When integration is decided
      Then the incomplete group is never merged, even with successful commits
      And it is not passed off as a success
      And its refs, commits and patch are preserved
      # source: skills/pdca-collection/SKILL.md §A — completion
      # source: skills/pdca-collection/SKILL.md §D — infrastructure, tracking, merge
      # test: skills/pdca-collection/tests/test_verification_recovery.py::CollectionContractSemanticsTest.test_group_terminal_and_pause_states
      # test: skills/pdca-collection/tests/test_standalone_contract.py::CollectionContractTest.test_completion_and_preservation

    @d4 @pinned
    Scenario: d4 The collection consists of one group
      Given a collection with one group
      When the work runs
      Then it uses the current tree and branch
      And git merge --no-ff is skipped
      And no group or task worktree and no branch is created
      # source: skills/pdca-collection/SKILL.md §P — per-item PLANs, the barrier, clustering
      # source: skills/pdca-collection/SKILL.md §D — infrastructure, tracking, merge
      # test: skills/pdca-collection/tests/test_git_model.py::GitModelSimTest.test_git_model_sim_passes

  Rule: e. No done groups at all

    @e1 @pinned
    Scenario: e1 Every group is incomplete
      Given a collection with no done group, every group incomplete
      When the batch is closed
      Then the refs, branches, commits and patch paths of the incomplete groups are preserved
      And the ordinary integration check is still performed on the integrated tree
      # source: skills/pdca-collection/SKILL.md §C — integration verification
      # source: skills/pdca-collection/SKILL.md §A — completion
      # test: skills/pdca-collection/tests/test_verification_recovery.py::CollectionContractSemanticsTest.test_git_and_verification_safety

    @e2 @pinned
      Scenario: e2 The integration check passes without a done group
      Given no group is done
      When the integration check returns PASS
      Then PASS does not mark the source incomplete tasks or groups done
      And completion and the verification verdict stay separate fields
      # source: skills/pdca-collection/SKILL.md §C — integration verification
      # test: skills/pdca-collection/tests/test_status_lint.py::PlanTerminalTest.test_a_terminal_resolution_must_not_be_done

    @e3 @uncovered
    Scenario: e3 Cleanup is proposed
      Given preserved artifacts of incomplete groups
      When cleanup is proposed
      Then nothing that preserves the incomplete results is deleted
      And the status and evidence paths stay available
      # source: skills/pdca-collection/SKILL.md §A — completion

    @e4 @pinned
    Scenario: e4 The status vocabulary is stretched
      Given a status that wants to call an incomplete group merged or a skipped group a status
      When the queue is read
      Then merged is only the transition done to merged
      And skipped is an integration note, not a group status
      And incomplete stays incomplete and is never merged
      # source: skills/pdca-collection/SKILL.md §Collection status record
      # test: skills/pdca-collection/tests/test_verification_recovery.py::CollectionContractSemanticsTest.test_group_terminal_and_pause_states

  Rule: The collection closes with one retrospective

    @r1 @pinned
    Scenario: r1 A collection-level ACT closure
      Given a collection that reaches its ACT closure
      When the closure is recorded
      Then a short evidence-grounded retrospective runs through the same pdca-check in retrospective mode
      And it covers a successful integrated-tree CHECK and a terminal STOP
      And pdca-executor alone persists it in the separate `Lessons learned` section
      # source: skills/pdca-collection/SKILL.md §Collection status record
      # source: skills/pdca/references/act.md §Retrospective (mandatory, ACT)
      # test: skills/pdca-collection/tests/test_retrospective_lessons.py::CollectionRetrospectiveTest.test_collection_has_a_separate_lessons_section

    @r2 @pinned
    Scenario: r2 A retrospective is demanded for every item
      Given a collection whose items, groups and phases each close
      When a per-item, per-group or per-phase retrospective is proposed
      Then no extra retrospective is created
      And only an item cycle that itself reaches ACT inherits the base skeleton
      And the section is pending at creation and finished at the collection ACT closure
      # source: skills/pdca-collection/SKILL.md §Collection status record
      # test: skills/pdca-collection/tests/test_retrospective_lessons.py::CollectionRetrospectiveTest.test_collection_has_a_separate_lessons_section

  Rule: The queue is data and the status must lint

    @s1 @pinned
    Scenario: s1 The queue is edited by hand
      Given a status write
      When status_lint runs from the project root
      Then exit 0 means valid
      And exit 2 means the row is repaired and relinted in the same turn
      And exit 1 is a resource blocker, not a written status
      # source: skills/pdca-collection/SKILL.md §Collection status record
      # test: skills/pdca-collection/tests/test_status_lint.py::StructureTest.test_json_reports_counts_and_no_violations
      # test: skills/pdca-collection/tests/test_status_lint.py::OperatorTest.test_a_missing_file_is_a_usage_error

    @s2 @pinned
    Scenario: s2 Caps are inherited silently
      Given a collection plan that names no plan_cap or lane_cap
      When the caps are read
      Then the recorded default of 4 applies
      And a lowering needs a recorded reason
      # source: skills/pdca-collection/SKILL.md §Parameters
      # test: skills/pdca-collection/tests/test_status_lint.py::CapsTest.test_a_form_without_caps_is_rejected_not_read_as_one

    @s3 @pinned
    Scenario: s3 A plan-terminal item sits in the queue
      Given an item resolved at PLAN with a terminal cause
      When the row is written
      Then attempts is 0
      And the row is not done and not plan-ready
      And it is a terminal resolution, not completion
      # source: skills/pdca-collection/SKILL.md §Collection status record
      # test: skills/pdca-collection/tests/test_status_lint.py::PlanTerminalTest.test_a_terminal_resolution_must_not_be_done

    @s4 @pinned
    Scenario: s4 CHECK receives the integrated candidate
      Given an integration check about to be dispatched
      When the candidate is staged
      Then the snapshot is persisted under the cycle's evidence_root
      And a sha256 manifest binds it to the final integrated commit and worktree state
      And a missing, incomplete or stale snapshot is re-gathered, not a product failure
      # source: skills/pdca-collection/SKILL.md §C — integration verification
      # test: skills/pdca-collection/tests/test_verification_recovery.py::CollectionContractSemanticsTest.test_git_and_verification_safety
