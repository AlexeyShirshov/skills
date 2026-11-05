# Gherkin description of the `pdca-incremental` campaign pressure scenarios.
#
# This is the human-run regression suite of the incremental form, not a test the
# runner executes. The executable guards live in `test_*.py`; the mapping below
# is explicit so that a rule cannot silently lose its guard.
#
# Conventions:
#   @<ID>       matrix id (this form never had a `tests/scenarios.md`)
#   @pinned     a guard exists and fails if this rule disappears from the text
#   @uncovered  no guard exists; the scenario is human-run only
#   # source:   the normative text the scenario asserts (a bare file is allowed)
#   # test:     a guard that pins the rule (file::Class.method)
#
# Baseline in force:
#   contract    the base `pdca` common cycle; the campaign adds only its container
#               and inherits counters, gates, CHECK and ACT unchanged
#   driver      pdca-orchestrator (cheap) for a campaign step; the planner decides
#               at every step boundary
#   state       one campaign status file under .pdca/status/ holding every step's
#               cycle records and the one shared event log
#   invariant   no change-producing step before an accepted baseline; a positive
#               increment is never refused for its size

Feature: The pdca-incremental campaign under pressure
  A campaign must advance on accepted, measured state — never on a forecast, a
  rejected candidate, or a "small enough" excuse — and must stop honestly.

  Rule: Entry fixes the goal, the measurement and the first step

    @A1 @pinned
    Scenario: A1 The goal is clear but the method or volume is not
      Given a goal whose method or volume cannot be fully determined in advance
      When the form is chosen
      Then the campaign form is selected
      And the measurement method is fixed at PLAN and written into the status
      And the opening step computes the current state with that method
      And no change-producing step starts before that measurement is accepted
      # source: skills/pdca-incremental/SKILL.md §When to use
      # source: skills/pdca-incremental/SKILL.md §Campaign goal and measurement
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::MeasurementFirstTest.test_current_state_is_the_first_step

    @A2 @pinned
    Scenario: A2 No available method can measure the goal
      Given a goal that requires a value with no metric, instrument or data source
      When PLAN evaluates it
      Then it is rejected at PLAN as goal cannot be measured under the available means
      And it never becomes a campaign that improvises a metric
      # source: skills/pdca-incremental/SKILL.md §Campaign goal and measurement
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::MeasurementFirstTest.test_unmeasurable_goal_is_rejected_at_plan

    @A3 @pinned
      Scenario: A3 The goal is already met
      Given supplied facts that already prove the goal is met
      When PLAN evaluates them
      Then the plan is the terminal outcome requested result already established
      And the task goes straight to ACT
      And a measured current state that satisfies the goal goes to the whole-goal CHECK and closes met
      And no dummy implementation step is opened
      # source: skills/pdca-incremental/SKILL.md §Campaign goal and measurement
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::MeasurementFirstTest.test_an_already_met_goal_does_not_open_an_implementation_step

    @A4 @pinned
    Scenario: A4 The user names pdca-incremental directly
      Given the user names this form explicitly
      When the campaign starts
      Then the named form is a constraint
      And the base common rules load with it
      And the entry classification is skipped
      And no local copy of the common contract is created
      # source: skills/pdca-incremental/SKILL.md §Inheritance: the base contract is the single source of the shared rules
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::InheritanceLoadTest.test_the_form_declares_inheritance_and_direct_load
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::InheritanceLoadTest.test_no_local_common_contract_copy

  Rule: Probes are free, credit is attributed

    @B1 @uncovered
    Scenario: B1 A bounded probe runs inside a step
      Given an open question inside a step
      When a bounded probe is run
      Then it starts no new PLAN
      And it owes no per-probe CHECK
      And it is bounded by the decision it investigates, not by a minute cap
      And it waives no approval
      # source: skills/pdca-incremental/SKILL.md §Probe, increment and step

    @B2 @pinned
    Scenario: B2 A positive increment is far below the campaign target
      Given an attributed net delta at or above the recipe floor
      When CHECK assesses the step
      Then the increment is accepted whatever its size
      And a step is never refused because it is small
      And sizing the work by the goal still forbids designing minimal steps
      # source: skills/pdca-incremental/SKILL.md §Probe, increment and step
      # source: skills/pdca-incremental/SKILL.md §Campaign invariants
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::PositiveIncrementTest.test_no_positive_increment_is_refused_for_its_size

    @B3 @uncovered
    Scenario: B3 The gate metric wobbles on one frozen package
      Given a metric whose run-to-run wobble appears on one frozen package
      When the delta is counted
      Then the wobble is neither credit nor debit
      And only an attributed result change or decision-relevant knowledge counts
      And the verdict counts a net delta
      # source: skills/pdca-incremental/SKILL.md §Probe, increment and step

    @B4 @pinned
    Scenario: B4 A forecast is quoted as if it were a threshold
      Given a plan's forecast value
      When the step is assessed
      Then the forecast never becomes a threshold
      And it never enters the accepted column
      # source: skills/pdca-incremental/SKILL.md §Campaign goal and measurement
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::PositiveIncrementTest.test_a_forecast_is_never_a_threshold

    @B5 @uncovered
    Scenario: B5 A step is re-measured for a prettier number
      Given a red measurement on a step
      When a replacement is proposed
      Then it is allowed only for objective invalidity and is archived
      And a red measurement stays red
      And one credited increment per step is the rule
      # source: skills/pdca-incremental/SKILL.md §Campaign goal and measurement

  Rule: The baseline is measured, never invented

    @C1 @pinned
      Scenario: C1 The campaign opens with the current state
      Given a campaign that has just passed PLAN
      When the opening step runs
      Then its DO changes no product
      And its CHECK verifies the measurement
      And its ACT writes the baseline and finalizes the status before any change-producing step
      # source: skills/pdca-incremental/SKILL.md §Campaign goal and measurement
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::MeasurementFirstTest.test_current_state_is_the_first_step
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::MeasurementFirstTest.test_the_baseline_is_not_described_as_a_pre_step_probe

    @C2 @uncovered
    Scenario: C2 The measured package differs from what was built or run
      Given a measurement taken before the last edit or on a different package
      When the evidence is assessed
      Then it earns no credit
      And it is archived
      And it is re-taken once on the final package as an evidence re-gather
      And it is not a product defect, a new attempt or a failed step
      # source: skills/pdca-incremental/SKILL.md §Campaign goal and measurement

    @C3 @uncovered
    Scenario: C3 The baseline measurement is missing or invalid
      Given a campaign without an accepted baseline
      When a change-producing step is proposed
      Then it does not start
      And a missing or invalid measurement blocks instead of improvising a number
      # source: skills/pdca-incremental/SKILL.md §Campaign invariants

  Rule: Steps advance on accepted state only

    @D1 @uncovered
    Scenario: D1 The next step is planned from a forecast
      Given a previous step with no accepted measurement
      When the next step is proposed
      Then it does not start
      And the next step starts from the accepted basis, never a forecast or about the same
      # source: skills/pdca-incremental/SKILL.md §Acceptance and carry-over

    @D2 @uncovered
    Scenario: D2 A rename, restart or method change occurs
      Given a campaign with counters and history
      When the session is renamed, restarted or the method changes
      Then no budget and no history resets
      And a step stays its own field while N stays the cycle number
      # source: skills/pdca-incremental/SKILL.md §Step and counters

    @D3 @pinned
    Scenario: D3 A step's DO cannot finish
      Given a step whose DO cannot finish under the contract
      When the outcome is recorded
      Then the status is blocked with cause, evidence and residual requirements
      And no credit is granted
      And there is no automatic replan and no DO to PLAN detour
      # source: skills/pdca-incremental/SKILL.md §Stop
      # source: skills/pdca/SKILL.md §State machine and counters
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::CampaignFailureSemanticsTest.test_failed_step_is_blocked_and_not_credited
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::CampaignFailureSemanticsTest.test_no_do_to_plan_detour_in_the_campaign

  Rule: Stop conditions are honest

    @E1 @pinned
    Scenario: E1 The campaign claims success from accepted steps
      Given accepted increments and a PASS on every mechanical row
      When the campaign outcome is recorded
      Then met requires the whole-goal CHECK on the accepted state
      And every original mandatory requirement must be verified
      And a local step acceptance never clears a global requirement
      # source: skills/pdca-incremental/SKILL.md §Stop
      # source: skills/pdca-incremental/SKILL.md §Claims and veto
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::PositiveIncrementTest.test_the_rule_keeps_other_mandatory_requirements

    @E2 @uncovered
    Scenario: E2 The user narrows the task without a new instruction
      Given pressure to close the campaign as limited
      When the outcome is recorded
      Then limited needs a new explicit user instruction recorded verbatim with the revised scope
      And plan approval is not a revision of the input
      And no mode narrows the task itself
      # source: skills/pdca-incremental/SKILL.md §Stop

    @E3 @uncovered
    Scenario: E3 The remainder is declared unreachable
      Given a remaining target
      When unreachable is claimed
      Then it is proven with numbers
      And it is never declared from fatigue
      # source: skills/pdca-incremental/SKILL.md §Stop

    @E4 @pinned
    Scenario: E4 The campaign is paused under a blocker
      Given a verified blocker inside an unchanged goal and bounds
      When the step boundary is reached
      Then the campaign stays open as running with disposition paused in the checkpoint
      And a pause is not an outcome and not a terminal status
      And it resumes in the same file with the same counters only on an explicit resume
      # source: skills/pdca-incremental/SKILL.md §Campaign invariants
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::CampaignFailureSemanticsTest.test_stop_table_keeps_the_blocked_row_honest

  Rule: Commit and effort are authorized, not assumed

    @F1 @uncovered
    Scenario: F1 The campaign wants to commit a step
      Given commit policy auto
      When a step is accepted
      Then only the step's paths are committed and the message names the campaign and the step
      And auto-commit exists only by an explicit authorisation recorded in the status
      And push is never part of it
      # source: skills/pdca-incremental/SKILL.md §Campaign invariants

    @F2 @uncovered
    Scenario: F2 Elapsed time or cost reaches a limit
      Given elapsed time, tokens, cost, revisions or measurement totals
      When a stop is considered
      Then accounts are accounting, never a stop condition
      And there is no autonomous cutoff
      And a failed candidate or incomplete evidence returns to the step boundary
      # source: skills/pdca-incremental/SKILL.md §Effort accounting and safety

  Rule: Revision and recovery preserve the goal

    @G1 @uncovered
    Scenario: G1 New facts require revising the strategy
      Given new facts at an explicit safe checkpoint
      When the strategy is revised
      Then the goal, history, results, knowledge, constraints and unfinished work are preserved
      And the original acceptance criterion is preserved
      And a rename, a session reset or a rejected candidate is not a revision
      # source: skills/pdca-incremental/SKILL.md §Strategic revision and recovery

    @G2 @uncovered
    Scenario: G2 The controller is lost mid-step
      Given a lost controller, restart, timeout or compaction
      When the driver resumes
      Then it restores from the checkpoint in the campaign status
      And accepted steps are never repeated
      And N, r and n and the defect history are not reset
      # source: skills/pdca-incremental/SKILL.md §Strategic revision and recovery

  Rule: Composition stays one step at a time

    @H1 @uncovered
    Scenario: H1 The campaign is an item of a collection
      Given a collection whose item is a campaign
      When the batch runs
      Then the campaign stays sequential inside its lane
      And campaign acceptance is not the common integration CHECK
      # source: skills/pdca-incremental/SKILL.md §Campaign cycle
      # source: skills/pdca-collection/SKILL.md §P — per-item PLANs, the barrier, clustering

    @H2 @uncovered
    Scenario: H2 Parallel increments are proposed
      Given two increments that could run at once
      When the schedule is proposed
      Then one step at a time in one lane is kept
      And parallel increments are refused
      And a campaign is never nested in a campaign or a collection
      # source: skills/pdca-incremental/SKILL.md §Campaign invariants

  Rule: The campaign keeps one status file

    @S1 @pinned
    Scenario: S1 A per-step status file is proposed
      Given a campaign with several steps
      When the status is written
      Then there is one campaign status file with every step's cycle records
      And the shared event log remains single
      And no per-step status file and no parallel todo exist
      # source: skills/pdca-incremental/SKILL.md §Campaign status
      # test: skills/pdca-incremental/tests/test_retrospective_lessons.py::IncrementalRetrospectiveTest.test_shared_event_log_remains_single

    @S2 @pinned
    Scenario: S2 The common rules are restated locally
      Given a campaign status and contract
      When they are written
      Then the common counters and rules are referenced, not copied
      And no local common-contract copy exists
      # source: skills/pdca-incremental/SKILL.md §Inheritance: the base contract is the single source of the shared rules
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::InheritanceLoadTest.test_no_local_common_contract_copy
      # test: skills/pdca-incremental/tests/test_standalone_contract.py::InheritanceLoadTest.test_the_form_does_not_restate_the_common_counters

    @S3 @uncovered
    Scenario: S3 The original task is paraphrased
      Given a campaign that advanced over several steps
      When the status is read
      Then the original task and the user-supplied criteria are recorded verbatim
      # source: skills/pdca-incremental/SKILL.md §Campaign status

    @S4 @pinned
    Scenario: S4 Preparation invents a baseline
      Given a campaign item at the preparation barrier
      When preparation is written
      Then no baseline is invented at preparation
      And the barrier requires no baseline, runtime record, substantive DO, future step plan or step count
      # source: skills/pdca-incremental/SKILL.md §Campaign cycle
      # test: skills/pdca-incremental/tests/test_orchestrator_asset.py::RunnerAssetTest.test_runner_invents_no_baseline_at_preparation

  Rule: Each step closes with the base retrospective

    @R1 @pinned
    Scenario: R1 A step reaches ACT
      Given a campaign step that reaches ACT, including a terminal STOP
      When the step is closed
      Then the same configured pdca-check retrospective runs in retrospective mode
      And the demoted `Lessons learned` section is pending at step creation and finished in ACT
      And it is persisted in the same campaign file
      # source: skills/pdca-incremental/SKILL.md §Campaign status
      # source: skills/pdca/references/act.md §Retrospective (mandatory, ACT)
      # test: skills/pdca-incremental/tests/test_retrospective_lessons.py::IncrementalRetrospectiveTest.test_per_step_act_runs_the_base_retrospective

    @R2 @pinned
    Scenario: R2 The retrospective grows a second campaign structure
      Given a campaign with accepted steps and one shared progress log
      When the step retrospective is recorded
      Then it creates no new role, log, phase or counter
      And the shared `Progress log` remains the single chronology
      # source: skills/pdca-incremental/SKILL.md §Campaign status
      # test: skills/pdca-incremental/tests/test_retrospective_lessons.py::IncrementalRetrospectiveTest.test_per_step_act_runs_the_base_retrospective
      # test: skills/pdca-incremental/tests/test_retrospective_lessons.py::IncrementalRetrospectiveTest.test_shared_event_log_remains_single
