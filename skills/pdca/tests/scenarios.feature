# Gherkin description of the base `pdca` pressure scenarios.
#
# This is the human-run regression suite of the domain-neutral contract, not a
# test the runner executes: a scenario is read into a fresh `pdca` session and
# judged on the recorded status file and role reports. The executable guards live
# in `test_*.py`; the mapping below is explicit so that a rule cannot silently
# lose its guard.
#
# Conventions:
#   @<ID>       matrix id, kept from the previous `tests/scenarios.md`
#   @pinned     a guard exists and fails if this rule disappears from the text
#   @uncovered  no guard exists; the scenario is human-run only
#   # source:   the normative text the scenario asserts (every anchor resolves)
#   # test:     a guard that pins the rule (file::Class.method)
#
# Baseline in force:
#   contract      skills/pdca/SKILL.md with references/plan.md, check.md, act.md
#   roles         pdca-scout, pdca-planner, pdca-executor, pdca-check, pdca-escalate
#   driver        the primary in normal mode, pdca-orchestrator in autonomous mode
#   state         one status file under .pdca/status/, evidence under .pdca/<task>/rv<k>/
#   invariants    the original task and the user-supplied criteria are immutable;
#                 CHECK is mandatory to accept a completed result; DO has no path
#                 to PLAN; STOP is an ACT outcome; every ACT closure runs a
#                 retrospective through pdca-check in retrospective mode and
#                 records it in ## Lessons learned.

Feature: The base pdca cycle under pressure
  The cycle must stay honest when the task is ambiguous, a run cannot finish, a
  defect repeats, or the host compacts mid-phase. Acceptance is judged on the
  durable record, never on a summary.

  Rule: Entry is one PLAN that decides the form

    @A1 @uncovered
    Scenario: A1 A fresh task arrives with no form named
      Given a task with one obvious deliverable and no stated method
      And neither a form nor a specialized skill is named
      When the planner runs its one PLAN
      Then it returns the form, the specialized skill or none, the rationale and the criteria
      And the rationale names the justified method and its bound, or the missing knowledge
      And no second classifier runs before or beside that PLAN
      And one deliverable is not by itself treated as a known method
      # source: skills/pdca/SKILL.md §Entry: one PLAN decides the form
      # source: skills/pdca/references/plan.md §Entry and first step

    @A2 @pinned
    Scenario: A2 The user names pdca-incremental or pdca-collection
      Given the user names a form explicitly
      When the cycle starts
      Then the named form is a constraint, not a suggestion
      And the base common rules are loaded together with it
      And the entry classification is skipped
      # source: skills/pdca/SKILL.md §Entry: one PLAN decides the form
      # source: skills/pdca/SKILL.md §Forms
      # test: skills/pdca/tests/test_dispatch_reference.py::TransportBoundaryTest.test_the_base_entry_contract_is_loaded_before_the_form_contract
      # test: skills/pdca/tests/test_contract_transitions.py::InheritanceTest.test_each_form_declares_inheritance_from_the_base

    @A3 @uncovered
    Scenario: A3 A second PLAN is proposed on unchanged content
      Given a pending PLAN already exists for the same content
      When a second PLAN is proposed
      Then it is refused as a repeated PLAN
      And the existing pending PLAN is continued
      # source: skills/pdca/SKILL.md §Generic operating constraints
      # source: skills/pdca/references/plan.md §Step boundary

  Rule: DO has exactly two outcomes

    @B1 @pinned
    Scenario: B1 DO hits a missing prerequisite
      Given an approved plan and a prerequisite the executor does not have
      When DO cannot finish under the approved contract
      Then DO returns cannot finish, with cause, evidence and residual requirements
      And the route is DO to ACT, never DO to PLAN
      And ACT finalizes the outcome without PASS, done or credit
      # source: skills/pdca/SKILL.md §State machine and counters
      # source: skills/pdca/SKILL.md §Phase contracts
      # test: skills/pdca/tests/test_contract_transitions.py::StateMachineTest.test_do_failure_goes_to_act_with_residual_requirements
      # test: skills/pdca/tests/test_diagram_artifacts.py::DiagramArtifactsTest.test_do_cannot_finish_goes_to_act_not_plan

    @B2 @uncovered
    Scenario: B2 An additive prerequisite appears during DO
      Given an active unit with its criteria and remainder
      When a prerequisite appears that adds work without replacing the goal
      Then a new active unit is added
      And the original unit stays active as blocked with unchanged criteria and remainder
      And it is not marked superseded and no mapping is written
      # source: skills/pdca/SKILL.md §Phase contracts
      # source: skills/pdca/references/plan.md §Terminal PLAN outcomes

    @B3 @uncovered
    Scenario: B3 A genuine scope replacement is needed
      Given an active unit whose goal is actually replaced
      When the replacement is accepted
      Then the original unit is marked superseded
      And an explicit superseded-unit to replacement mapping carries all original criteria
      And the mapping carries the residue that is still owed
      # source: skills/pdca/SKILL.md §Phase contracts
      # source: skills/pdca/references/act.md §Closing order

  Rule: CHECK decides the route back

    @C1 @pinned
    Scenario: C1 CHECK finds an implementation defect
      Given a completed candidate and its evidence
      When an independent CHECK finds an implementation defect
      Then the route is CHECK to DO and n increments
      And a missing report is re-gathered first
      And it is not counted as a defect or an attempt until the facts are in
      # source: skills/pdca/SKILL.md §Phase contracts
      # source: skills/pdca/references/check.md §Verdict and routing
      # test: skills/pdca/tests/test_contract_transitions.py::StateMachineTest.test_state_machine_declares_the_current_transitions
      # test: skills/pdca/tests/test_evidence_root_dispatch.py::BaseContractTest.test_check_to_do_regather_lands_in_the_root

    @C2 @pinned
    Scenario: C2 CHECK finds contradictory or unachievable criteria
      Given a result that meets an impossible or self-contradictory contract
      When CHECK assesses the criteria
      Then the route is CHECK to PLAN
      And only CHECK routes this defect
      And the planner re-examines the contract with the facts CHECK recorded
      # source: skills/pdca/SKILL.md §State machine and counters
      # source: skills/pdca/references/check.md §Verdict and routing
      # test: skills/pdca/tests/test_check_reference_dispatch.py::CheckDedupTest.test_gates_unique_to_this_phase_survive_the_trim

    @C3 @pinned
    Scenario: C3 A user-supplied criterion is ambiguous or contradictory
      Given the user supplied a criterion that cannot be settled as written
      When PLAN works with it
      Then the criterion set is preserved verbatim
      And the outcome is a PLAN-terminal label, acceptance criteria cannot be determined
      And that label can also be original task is infeasible under the stated constraints
      And the criterion set is never rewritten into a convenient one
      # source: skills/pdca/SKILL.md §The user's task and its criteria
      # source: skills/pdca/references/plan.md §Terminal PLAN outcomes
      # test: skills/pdca/tests/test_plan_act_dedup.py::PlanContractTest.test_terminal_labels_are_inline_but_their_payloads_are_not

  Rule: PLAN may end without a candidate

    @D1 @pinned
    Scenario: D1 PLAN cannot determine the criteria
      Given a task whose acceptance criteria cannot be established from the available facts
      When PLAN reaches that limit
      Then the outcome is PLAN to ACT with the missing information and the reason
      And no DO and no CHECK start
      # source: skills/pdca/references/plan.md §Terminal PLAN outcomes
      # source: skills/pdca/SKILL.md §Phase contracts
      # test: skills/pdca/tests/test_plan_act_dedup.py::PlanContractTest.test_terminal_labels_are_inline_but_their_payloads_are_not
      # test: skills/pdca/tests/test_plan_act_dedup.py::PlanContractTest.test_do_start_is_logged_and_an_indeterminate_criterion_routes_to_act

    @D2 @pinned
    Scenario: D2 The supplied facts prove the original task infeasible
      Given facts that prove the task cannot be delivered under the stated constraints
      When PLAN evaluates them
      Then the outcome is PLAN to ACT with the proven cause and its evidence
      And one failed candidate is not treated as proof
      And no substitute deliverable is produced
      # source: skills/pdca/references/plan.md §Terminal PLAN outcomes
      # source: skills/pdca/SKILL.md §State machine and counters
      # test: skills/pdca/tests/test_contract_transitions.py::StateMachineTest.test_state_machine_declares_the_current_transitions

  Rule: Repetition and escalation

    @E1 @pinned
    Scenario: E1 The same defect returns after one fix
      Given one attempt to fix a criterion already failed
      When the same defect reappears
      Then pdca-escalate is mandatory before the next fix
      And this holds even in a new revision
      And the defect key and its history survive across the revision
      # source: skills/pdca/SKILL.md §Escalation — expert review (`pdca-escalate`)
      # source: skills/pdca/references/escalate.md §Grounds
      # test: skills/pdca/tests/test_escalation_reference.py::ReferenceTest.test_reference_preserves_the_detailed_contract
      # test: skills/pdca/tests/test_dispatch_reference.py::TransportBoundaryTest.test_the_escalation_brief_carries_the_protocol_and_its_required_inputs

    @E2 @pinned
    Scenario: E2 Three substantive CHECKs of one revision fail
      Given three substantive CHECK failures of the same revision
      When a fourth attempt is proposed
      Then no fourth attempt runs
      And the mandatory expert review comes first
      And an exhausted revision ends in ACT as incomplete or STOP
      # source: skills/pdca/SKILL.md §State machine and counters
      # source: skills/pdca/references/act.md §Closing order
      # test: skills/pdca/tests/test_contract_transitions.py::StateMachineTest.test_act_finalizes_both_outcomes_and_stop_is_an_act_outcome
      # test: skills/pdca/tests/test_plan_act_dedup.py::ActContractTest.test_exit_and_stop_gates

  Rule: Counters count revisions and attempts, not effort

    @F1 @uncovered
    Scenario: F1 A rejected candidate is reported as progress
      Given a candidate that CHECK rejected
      When the same content is presented again as progress
      Then it is not a revision
      And r does not grow
      And n does not reset
      And no increment is credited
      # source: skills/pdca/SKILL.md §State machine and counters

    @F2 @uncovered
    Scenario: F2 A session restart or rename occurs
      Given a cycle with recorded counters and defect history
      When the session restarts or is renamed
      Then no counter resets
      And the status file restores N, r, n/3 and the defect history
      # source: skills/pdca/SKILL.md §State machine and counters
      # source: skills/pdca/SKILL.md §Recovery

  Rule: Approval gates normal-mode DO

    @G1 @pinned
    Scenario: G1 Normal mode, plan written but not approved
      Given a plan saved in the status file
      And no approval yet
      When the driver considers starting DO
      Then nothing outside the status file is created or edited
      And DO does not start
      # source: skills/pdca/SKILL.md §Normal-mode approval
      # test: skills/pdca/tests/test_normal_approval.py::NormalApprovalSectionTest.test_the_gate_admits_only_explicit_approval

    @G2 @pinned
    Scenario: G2 A question or OK without approval
      Given a pending plan
      When the user asks a clarifying question or says OK
      Then it is not an approval
      And the driver asks again once
      And DO still does not start
      # source: skills/pdca/SKILL.md §Normal-mode approval
      # test: skills/pdca/tests/test_normal_approval.py::NormalApprovalSectionTest.test_the_gate_admits_only_explicit_approval

    @G3 @pinned
    Scenario: G3 A caller-driven cycle carries a pending approval ref
      Given a parent cycle that delegates a step with a pending approval ref
      When approval is needed
      Then the parent obtains it, never the delegated driver
      And the executor records it against the same ref
      And a stale plan needs a genuine revision and a fresh ref
      # source: skills/pdca/SKILL.md §Normal-mode approval
      # test: skills/pdca/tests/test_normal_approval.py::NormalApprovalSectionTest.test_caller_driven_approval_binds_the_exact_cycle

  Rule: Autonomous mode fails closed

    @H1 @uncovered
    Scenario: H1 Autonomous mode encounters a missing role
      Given autonomous mode
      When a required role is unavailable
      Then the run records a Notice and a durable reason
      And it is a resource blocker
      And no silent run without the role happens
      # source: skills/pdca/SKILL.md §Roles and host requirements
      # source: skills/pdca/SKILL.md §Control modes

    @H2 @uncovered
    Scenario: H2 Autonomous mode hits an unresolvable question
      Given autonomous mode
      When a criterion stays ambiguous and no approval can be obtained
      Then no question is asked
      And the run ends in ACT as STOP with cause and evidence
      # source: skills/pdca/SKILL.md §Control modes
      # source: skills/pdca/SKILL.md §Phase contracts

  Rule: Recovery is from the record, evidence beats assertion

    @I1 @uncovered
    Scenario: I1 Compaction loses the narrative
      Given the host compacts the session mid-phase
      When the cycle resumes
      Then recovery reads the status file through pdca-scout
      And the recovery questions are answered from artefacts, not memory
      And the cycle continues from its current phase
      # source: skills/pdca/SKILL.md §Recovery

    @I2 @pinned
    Scenario: I2 Evidence is missing or stale
      Given a criterion whose proving run left no path under the cycle evidence root
      When CHECK assesses it
      Then the criterion is unverified
      And the proving action is re-run
      And missing evidence is neither a product defect nor an attempt
      # source: skills/pdca/SKILL.md §Evidence over assertion
      # source: skills/pdca/SKILL.md §Workspace and durable status
      # test: skills/pdca/tests/test_evidence_root_dispatch.py::DriverDispatchTest.test_one_rule_covers_initial_follow_up_and_regather
      # test: skills/pdca/tests/test_evidence_root_dispatch.py::BaseContractTest.test_check_to_do_regather_lands_in_the_root

  Rule: Acceptance covers the whole goal

    @J1 @pinned
    Scenario: J1 A result is accepted locally
      Given a cycle whose own scope passes CHECK
      When another original mandatory requirement is still unverified
      Then the local acceptance closes only the cycle scope
      And done still needs a whole-goal CHECK over every original mandatory requirement
      # source: skills/pdca/SKILL.md §Original task, cycle scope and acceptance
      # source: skills/pdca/references/check.md §Assess the criteria
      # test: skills/pdca/tests/test_check_reference_dispatch.py::CheckDedupTest.test_gates_unique_to_this_phase_survive_the_trim

    @J2 @uncovered
    Scenario: J2 A rejected candidate is asserted as accepted
      Given a candidate that CHECK did not accept
      When it is reported as accepted
      Then no PASS and no done are recorded
      And the status records the actual non-acceptance
      # source: skills/pdca/SKILL.md §ACT
      # source: skills/pdca/references/act.md §Closing order

  Rule: ACT closes with a mandatory retrospective

    @R1 @pinned
    Scenario: R1 A cycle closes on any ACT route
      Given a cycle that reaches ACT by a successful CHECK, a terminal STOP, PLAN or DO
      When ACT closes the cycle
      Then a short retrospective runs through pdca-check in retrospective mode
      And it analyses the phase reports that actually ran
      And a CHECK to DO or CHECK to PLAN route runs no retrospective
      And no CHECK is required for PLAN to ACT or DO to ACT
      And an absent CHECK is recorded as `CHECK: not run`, never reconstructed
      # source: skills/pdca/references/act.md §Retrospective (mandatory, ACT)
      # test: skills/pdca/tests/test_retrospective_lessons.py::ActRetrospectiveContractTest.test_all_act_routes_inherit_the_retrospective
      # test: skills/pdca/tests/test_retrospective_lessons.py::ActRetrospectiveContractTest.test_no_check_prerequisite_for_terminal_routes

    @R2 @pinned
    Scenario: R2 The retrospective is read as a second verdict
      Given a retrospective report on a closed cycle
      When it is offered as a CHECK verdict, a criteria matrix or a routing decision
      Then it is rejected: the mode issues no verdict and no transition authority
      And it never overrides the originating outcome, acceptance, security, the no-4th rule or approvals
      And it creates no new counter, attempt or verification
      And it does not reopen accepted work or alter the frozen result
      # source: skills/pdca/references/check.md §Retrospective mode (ACT)
      # source: skills/pdca/references/act.md §Retrospective (mandatory, ACT)
      # test: skills/pdca/tests/test_retrospective_lessons.py::ActRetrospectiveContractTest.test_retrospective_is_analysis_not_a_verdict

    @R3 @pinned
    Scenario: R3 The driver dispatches the retrospective
      Given an ACT closure that needs a retrospective
      When the driver composes the dispatch
      Then the dispatch is marked `mode: retrospective`
      And it carries the complete check.md and the retrospective contract from act.md inline
      And CHECK does not open an installed reference path
      And it uses the same pdca-check role and effective medium tier
      And a contract that cannot be loaded whole is a blocker before dispatch
      # source: skills/pdca/SKILL.md §ACT
      # source: skills/pdca/SKILL.md §CHECK
      # source: skills/pdca/references/driver.md §Dispatch transport
      # source: skills/pdca/references/check.md §Retrospective mode (ACT)
      # test: skills/pdca/tests/test_retrospective_lessons.py::BaseContractTest.test_check_inline_delivery_covers_retrospective
      # test: skills/pdca/tests/test_retrospective_lessons.py::DriverContractTest.test_driver_inlines_check_and_act_retrospective_contracts
      # test: skills/pdca/tests/test_retrospective_lessons.py::RoleScopeTest.test_check_names_retrospective_mode_and_inline_contract

    @R4 @pinned
    Scenario: R4 The retrospective report never arrives
      Given an ACT closure whose retrospective dispatch is absent or failed
      When the closure is recorded
      Then the record stays open with an explicit closure blocker
      And the originating accepted or STOP outcome is preserved without a fake CHECK
      And no fallback analysis by the driver or the executor happens
      And only pdca-executor persists the raw report and then marks ACT completed
      # source: skills/pdca/references/act.md §Retrospective (mandatory, ACT)
      # source: skills/pdca/references/act.md §Closing order
      # test: skills/pdca/tests/test_retrospective_lessons.py::ActRetrospectiveContractTest.test_single_writer_completion_contract

    @R5 @pinned
    Scenario: R5 The retrospective has nothing new to say
      Given a closed cycle whose retrospective analysed the available evidence
      When it records no new lesson
      Then `No new lessons` is valid with the evidence reviewed, analysis coverage and limits
      And 0-3 lessons is the editorial default, not a quota
      And an optional durable lesson beyond the status file stays separate and permission-bound
      And absent evidence is marked absent, never invented
      # source: skills/pdca/references/act.md §Lessons learned
      # source: skills/pdca/references/act.md §Closing order
      # test: skills/pdca/tests/test_retrospective_lessons.py::BaseSkeletonTest.test_pending_marker_is_the_initial_value
      # test: skills/pdca/tests/test_retrospective_lessons.py::ActRetrospectiveContractTest.test_optional_durable_memory_is_distinct

    @R6 @pinned
    Scenario: R6 ACT writes its record and the retrospective together
      Given a cycle that reaches ACT
      When pdca-executor writes the closed status
      Then it fills `ACT record` and `Lessons learned` in the same write
      And a phase that did not run keeps its pending, not reached or not applicable value and reason
      # source: skills/pdca/references/act.md §Status file
      # test: skills/pdca/tests/test_retrospective_lessons.py::StatusSectionOwnershipTest.test_act_fills_record_and_lessons_together
      # test: skills/pdca/tests/test_retrospective_lessons.py::StatusSectionOwnershipTest.test_unrun_phase_keeps_its_pending_value

  Rule: The status record must stay honest

    @S1 @uncovered
    Scenario: S1 The task and the returned plan are recorded
      Given a completed PLAN
      When the status file is written
      Then the task as the user supplied it is recorded verbatim
      And the planner's returned plan is recorded verbatim
      # source: skills/pdca/references/act.md §Original task
      # source: skills/pdca/references/act.md §PLAN record

    @S2 @pinned
    Scenario: S2 Fixed headings and the last section
      Given any status file
      When its structure is read
      Then the fixed headings are present
      And `Lessons learned` immediately follows `ACT record`
      And `Progress log` is the last section
      # source: skills/pdca/references/act.md §Status file
      # test: skills/pdca/tests/test_retrospective_lessons.py::BaseSkeletonTest.test_progress_log_remains_last
      # test: skills/pdca/tests/test_retrospective_lessons.py::BaseSkeletonTest.test_lessons_learned_immediately_follows_act_record

    @S3 @pinned
    Scenario: S3 Every phase transition is logged
      Given a phase transition
      When the transition is recorded
      Then the log row carries the counters
      And it carries an evidence pointer
      # source: skills/pdca/references/act.md §Progress log
      # test: skills/pdca/tests/test_plan_act_dedup.py::PlanContractTest.test_do_start_is_logged_and_an_indeterminate_criterion_routes_to_act

    @S4 @pinned
    Scenario: S4 An absent CHECK is recorded as absent
      Given a cycle that ended without CHECK
      When ACT writes the status
      Then the CHECK record is absent
      And it is never filled in afterwards
      # source: skills/pdca/references/act.md §CHECK record
      # test: skills/pdca/tests/test_retrospective_lessons.py::BaseSkeletonTest.test_no_check_is_preserved_as_absent

    @S5 @uncovered
    Scenario: S5 A finalized status file is kept
      Given a cycle that reached ACT
      When the cycle is over
      Then the finalized status file is preserved
      And it is not deleted by cleanup
      # source: skills/pdca/references/act.md §Status file
