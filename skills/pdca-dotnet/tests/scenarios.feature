# Gherkin description of the `pdca-dotnet` overlay pressure scenarios.
#
# This is the human-run regression suite of the .NET/C# overlay, not a test the
# runner executes. The executable guards live in `test_*.py`; the mapping below
# is explicit so that a rule cannot silently lose its guard.
#
# Conventions:
#   @<ID>       matrix id, kept from the previous `tests/scenarios.md`
#   @pinned     a guard exists and fails if this rule disappears from the text
#   @uncovered  no guard exists; the scenario is human-run only
#   # source:   the normative text the scenario asserts (a bare file is allowed)
#   # test:     a guard that pins the rule (file::Class.method)
#
# Baseline in force:
#   contract    the base `pdca` common cycle, plus the form that inherits it when
#               the work is a campaign step or a collection item
#   overlays    skills/pdca-dotnet/SKILL.md inherits skills/pdca-coder/SKILL.md
#               and adds only .NET/C# facts: no form, state machine, counter or
#               gate of its own
#   symbols     C# symbols are resolved with the `roslyn` tool, never text search
#
# Note: the mechanical gates (`validate_inner_loop.py`, `pdca_evidence.py`) are
# exercised directly by `test_inner_loop_gate.py` and `test_pdca_evidence.py`,
# so several scenarios below cite a real executable check rather than a text pin.

Feature: The pdca-dotnet overlay under pressure
  The overlay must add .NET-specific facts to the programming overlay without
  inventing a cycle, a counter, a gate or a metric.

  Rule: Roslyn is the resolver for C# symbols

    @A1 @uncovered
    Scenario: A1 A C# member must be renamed
      Given a request to find all call sites of a member and rename it
      When the rename is performed
      Then roslyn answers refs and callers for the symbol
      And roslyn applies the rename
      And a textual substitution is not a resolved rename
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands

    @A2 @uncovered
    Scenario: A2 The roslyn catalog entry is missing
      Given a host where the roslyn tool is absent from the catalog
      When a symbol question is asked
      Then search is run for the roslyn entry first
      And a missing catalog entry is not grounds for rg on a symbol
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands

    @A3 @uncovered
    Scenario: A3 A symbol is inferred from text search
      Given a symbol answer produced by rg over .cs files
      When the answer is presented
      Then it is not a resolved symbol
      And it is labelled as text search, not as an answer
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands

  Rule: A run proves the source it actually tested

    @B1 @pinned
    Scenario: B1 A docs-only change is made
      Given a change that touches no compiled file
      When the evidence is reported
      Then no build receipt is claimed and none is needed
      And a fictitious rebuild of the docs change is rejected
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_docs_only_no_build_rc0
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_docs_only_fictitious_rebuild_rejected

    @B2 @pinned
    Scenario: B2 A compiled edit is tested with no-build
      Given a compiled edit and a no-build test run
      When the run reports green
      Then the artifact must match the actual source including uncommitted changes
      And HEAD alone is not that identity
      And a stale artifact mismatch is unverified, not a product defect
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_stale_no_build_source_mismatch_rejected
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_fresh_affected_build_then_no_build_rc0

    @B3 @pinned
    Scenario: B3 A selector matches zero cases
      Given a test selector that selects no test
      When the run reports its result
      Then zero selected is a failed run, not green
      And it is not evidence
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_zero_selected_tests_rejected
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_zero_selected_count_rejected

    @B4 @pinned
    Scenario: B4 The runner reports a non-zero exit
      Given a run with a non-zero exit code
      When the outcome is recorded
      Then the documented exit-code meaning and the actual status are recorded
      And a test failure is distinguished from infrastructure or usage
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ProjectionFaithfulnessTests.test_rewritten_exit_code_rejected
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_missing_exit_code_rejected

  Rule: The inner loop is the affected projects, not the solution

    @C1 @pinned
    Scenario: C1 A whole-solution build is proposed in the inner loop
      Given an inner-loop step on one project
      When a whole-solution build or test is proposed
      Then it is rejected
      And the affected projects and their dependencies run sequentially
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_whole_solution_build_inner_rejected
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_whole_solution_test_inner_rejected

    @C2 @uncovered
    Scenario: C2 Coverage is quoted without a baseline
      Given a coverage number offered as a result
      When it is assessed
      Then the measured baseline or the project threshold is recorded
      And no target is invented
      # source: skills/pdca-dotnet/SKILL.md §.NET check deltas

    @C3 @uncovered
    Scenario: C3 Mutation is relevant but the harness is broken
      Given a mutation run whose harness fails
      When its result is reported
      Then broken tooling is not a score and not a green run
      And a controlled mutant is not a full Stryker result
      # source: skills/pdca-dotnet/SKILL.md §.NET check deltas

  Rule: The diff supplies candidates, CHECK decides

    @D1 @uncovered
    Scenario: D1 The diff suppresses a warning
      Given a diff that adds NoWarn or SuppressMessage
      When the diff is reviewed
      Then it is recorded as a raw candidate with its location and count
      And CHECK decides whether it is a real deviation
      And a marker alone is not a defect
      # source: skills/pdca-dotnet/SKILL.md §.NET check deltas

    @D2 @uncovered
    Scenario: D2 The diff touches a public API
      Given a diff that changes a public surface
      When the compatibility lens is applied
      Then the surface and its configured policy are checked only where the task includes them
      # source: skills/pdca-dotnet/SKILL.md §.NET check deltas

  Rule: Integration runs are a boundary, not inner work

    @E1 @pinned
    Scenario: E1 A container-backed integration suite is proposed inside DO
      Given an integration suite that needs containers
      When it is proposed inside the inner loop
      Then it runs one serialized lane at the stream or DO to CHECK boundary
      And the deviation is recorded rather than renamed away
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::IntegrationPolicyTests.test_integration_inside_do_detected_and_recorded
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::IntegrationPolicyTests.test_integration_attempt_not_started_is_a_distinct_state

    @E2 @uncovered
    Scenario: E2 A test host recurses or allocates without bound
      Given a test host that recurses or allocates without bound
      When the run is killed with exit 137 or an OOM
      Then the run stops
      And the reason is recorded
      And the cap is reviewed before any rerun
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas

  Rule: Documentation and conventions follow the project

    @F1 @uncovered
    Scenario: F1 XML docs are required for a changed public member
      Given a project that enforces CS1591
      When a public member changes
      Then the XML doc matches the actual signature
      And the CS1591 policy is read from the project, not invented
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas

    @F2 @uncovered
    Scenario: F2 A bilingual EN and RU pair exists in the repository
      Given a repository with a bilingual documentation pair
      When documentation is written
      Then the project's convention is followed
      And .NET itself requires neither bilingual docs nor CRLF
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas

  Rule: Artifacts and cleanup stay inside the task scope

    @G1 @pinned
    Scenario: G1 A staged artifact copy is used for CHECK
      Given a staged copy offered as CHECK evidence
      When CHECK reads it
      Then source identity includes uncommitted state
      And the staged copy is validated against the source
      And a mismatch is unverified or an evidence blocker, never an automatic pass or product fail
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas
      # test: skills/pdca-dotnet/tests/test_pdca_evidence.py::MinimumManifestTests.test_tree_binding_when_present_must_equal_the_frozen_tree
      # test: skills/pdca-dotnet/tests/test_evidence_inheritance.py::EvidenceInheritanceTest.test_staged_copies_live_under_the_base_root

    @G2 @pinned
    Scenario: G2 Cleanup would delete a failed task's evidence
      Given a failed task with preserved artifacts
      When cleanup is considered
      Then the evidence is preserved
      And cleanup is not a phase gate
      And it is limited to task-owned artifacts inside an explicit scope
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::CleanupReceiptTests.test_deleting_another_task_or_a_broad_pattern_rejected
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::CleanupPathScopeTests.test_task_root_rv_root_and_glob_rejected

  Rule: Helpers are optional and never a gate

    @H1 @uncovered
    Scenario: H1 An optional helper script is available
      Given a project that has the helper scripts
      When the brief or report flow uses them
      Then they are used only where the project or the cycle chooses that method
      And they are not a new phase gate
      # source: skills/pdca-dotnet/SKILL.md §Optional verification helpers
      # source: skills/pdca-dotnet/scripts/validate_inner_loop.py

    @H2 @pinned
    Scenario: H2 validate_inner_loop rejects a brief
      Given a recorded brief that the gate rejects
      When the gate returns its verdict
      Then the recorded brief is invalid
      And the planner or executor corrects the input, not the contract
      And the script never executes the supplied command
      # source: skills/pdca-dotnet/SKILL.md §Optional verification helpers
      # source: skills/pdca-dotnet/scripts/validate_inner_loop.py
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::BriefGateTests.test_malformed_json_rc1
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::BriefGateTests.test_valid_brief_rc0

  Rule: The overlay adds no second contract

    @S1 @uncovered
    Scenario: S1 No .NET-specific counter or status section
      Given any campaign step or collection item using this overlay
      When its status is written
      Then no .NET-specific counter is added
      And no .NET-specific status section is added
      And no second status file is created
      # source: skills/pdca-dotnet/SKILL.md §Composition

    @S2 @pinned
    Scenario: S2 Missing or stale evidence is unverified
      Given missing or stale evidence for a criterion
      When the criterion is assessed
      Then it is unverified, never a pass
      # source: skills/pdca-dotnet/SKILL.md §.NET check deltas
      # test: skills/pdca-dotnet/tests/test_inner_loop_gate.py::ReportGateTests.test_stale_no_build_source_mismatch_rejected

    @S3 @uncovered
    Scenario: S3 The overlay chooses no form or method
      Given any run using this overlay
      When the plan is made
      Then the overlay chooses no form
      And it chooses no test strategy
      And it chooses no verification method
      # source: skills/pdca-dotnet/SKILL.md §Composition

    @S4 @uncovered
    Scenario: S4 The original task stays verbatim
      Given any overlay run
      When its result is accepted
      Then the original task and the user-supplied criteria remain verbatim
      # source: skills/pdca-dotnet/SKILL.md §.NET plan deltas
