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
#   symbols     choose permitted methods by task and policy; text matches are candidates, not resolved bindings

Feature: The pdca-dotnet overlay under pressure
  The overlay must add .NET-specific facts to the programming overlay without
  inventing a cycle, a counter, a gate or a metric.

  Rule: C# symbol evidence follows the task and governing policy

    @A1 @uncovered
    Scenario: A1 A C# member must be renamed
      Given a request to identify and rename one exact C# member
      When an available and permitted semantic method is used
      Then symbol identity and reference evidence inform the rename
      And text-only matches are not called resolved bindings or complete references
      # source: skills/pdca-dotnet/SKILL.md §Semantic tooling for C# symbols

    @A2 @uncovered
    Scenario: A2 Roslyn is absent but another semantic method is available
      Given a C# reference task and an available permitted project-supported semantic method
      When Roslyn is absent from the host tool inventory
      Then tool choice follows the task and higher-priority policy
      And Roslyn absence alone does not block unrelated .NET work
      # source: skills/pdca-dotnet/SKILL.md §Semantic tooling for C# symbols

    @A3 @uncovered
    Scenario: A3 Text inspection finds possible occurrences
      Given text inspection is permitted and produces possible symbol occurrences
      When the occurrences are presented
      Then they are labelled as candidates with their uncertainty
      And they do not establish resolved bindings or complete references
      # source: skills/pdca-dotnet/SKILL.md §Semantic tooling for C# symbols

    @A4 @uncovered
    Scenario: A4 Host policy requires Roslyn but Roslyn is unavailable or denied
      Given a higher-priority host policy allows only Roslyn for this symbol criterion
      When Roslyn is absent or its use is denied
      Then the host restriction is honored without a workaround
      And only the unmet criterion is reported as unverified under the base contract
      # source: skills/pdca-dotnet/SKILL.md §Semantic tooling for C# symbols

    @A5 @uncovered
    Scenario: A5 An ordinary .NET task has no symbol criterion
      Given a .NET build and test task with no symbol question or mandatory tool policy
      When Roslyn is absent
      Then the .NET task follows the existing project and base-contract requirements
      And no Roslyn dependency or catalog search is added
      # source: skills/pdca-dotnet/SKILL.md §Semantic tooling for C# symbols

  Rule: A run proves the source it actually tested

    @B1 @uncovered
    Scenario: B1 A docs-only change is made
      Given a change that touches no compiled file
      When the evidence is reported
      Then no build receipt is claimed and none is needed
      And a fictitious rebuild of the docs change is rejected
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands

    @B2 @uncovered
    Scenario: B2 A compiled edit is tested with no-build
      Given a compiled edit and a no-build test run
      When the run reports green
      Then the artifact must match the actual source including uncommitted changes
      And HEAD alone is not that identity
      And a stale artifact mismatch is unverified, not a product defect
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands

    @B3 @uncovered
    Scenario: B3 A selector matches zero cases
      Given a test selector that selects no test
      When the run reports its result
      Then zero selected is a failed run, not green
      And it is not evidence
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands

    @B4 @uncovered
    Scenario: B4 The runner reports a non-zero exit
      Given a run with a non-zero exit code
      When the outcome is recorded
      Then the documented exit-code meaning and the actual status are recorded
      And a test failure is distinguished from infrastructure or usage
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands

  Rule: The inner loop is the affected projects, not the solution

    @C1 @uncovered
    Scenario: C1 A whole-solution build is proposed in the inner loop
      Given an inner-loop step on one project
      When a whole-solution build or test is proposed
      Then it is rejected
      And the affected projects and their dependencies run sequentially
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas

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

    @E1 @uncovered
    Scenario: E1 A container-backed integration suite is proposed inside DO
      Given an integration suite that needs containers
      When it is proposed inside the inner loop
      Then it runs one serialized lane at the stream or DO to CHECK boundary
      And the deviation is recorded rather than renamed away
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas

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
    Scenario: G1 Build evidence is produced without copying the candidate
      Given a candidate in its checkout, including relevant uncommitted state
      When the executor builds it for CHECK
      Then the build evidence is bound to the candidate identity
      And CHECK receives the evidence, not a copy of the project
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas
      # test: tests/pdca-dotnet/test_evidence_inheritance.py::EvidenceInheritanceTest.test_build_evidence_is_persisted_without_copying_the_candidate

    @G2 @uncovered
    Scenario: G2 Cleanup would delete a failed task's evidence
      Given a failed task with preserved artifacts
      When cleanup is considered
      Then the evidence is preserved
      And cleanup is not a phase gate
      And it is limited to task-owned artifacts inside an explicit scope
      # source: skills/pdca-dotnet/SKILL.md §.NET do/act deltas

  Rule: The overlay adds no second contract

    @S1 @uncovered
    Scenario: S1 No .NET-specific counter or status section
      Given any campaign step or collection item using this overlay
      When its status is written
      Then no .NET-specific counter is added
      And no .NET-specific status section is added
      And no second status file is created
      # source: skills/pdca-dotnet/SKILL.md §Composition

    @S2 @uncovered
    Scenario: S2 Missing or stale evidence is unverified
      Given missing or stale evidence for a criterion
      When the criterion is assessed
      Then it is unverified, never a pass
      # source: skills/pdca-dotnet/SKILL.md §.NET check deltas

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

  Rule: Local coverage evidence stays comparable and reusable

    @U10 @uncovered @simulated
    Scenario: U10 An unchanged coverage baseline crosses attempts and sessions
      Given a simulated coverage baseline whose source, tests, tooling, configuration, scope, provider, environment, exclusions and denominator remain unchanged
      And a later candidate has different production source and additional branches
      When an attempt, plan revision and executor session change without changing the stored baseline
      Then the baseline and candidate reports remain bound to their respective source identities
      And comparability is decided by the metric and measurement basis rather than source equality
      And `r`, `n` or a session change alone does not request a new baseline
      # source: skills/pdca-dotnet/SKILL.md §Coverage comparison and report reuse

    @U11 @uncovered @simulated
    Scenario: U11 Shared production code changes after partitioned coverage runs
      Given simulated unit and integration coverage artifacts from separate test projects that both reference one production library
      And a later candidate changes that shared production library
      When CHECK reads the preserved earlier runs
      Then evidence depending on the changed production input is invalidated in both partitions
      And a project boundary alone does not establish test independence
      When a later edit changes only an isolated unit test with dependency independence established
      Then unaffected integration evidence may be retained while the unit evidence is refreshed
      # source: skills/pdca-coder/SKILL.md §Coverage evidence lifecycle
      # source: skills/pdca/references/check.md §Candidate identity

    @U12 @uncovered @simulated
    Scenario: U12 A scoped branch delta passes while the complete gate does not
      Given simulated changed-file branch reporting with a high selected denominator result
      And the project separately requires a whole-solution threshold and a dedicated integration gate
      When the scoped delta report is presented at the final measurement boundary
      Then it reports its selected denominator and baseline/candidate comparability
      And it does not replace either complete required gate or change either threshold
      And the report filter describes the denominator rather than a reduction in collection duration
      # source: skills/pdca-dotnet/SKILL.md §Coverage comparison and report reuse

    @U13 @uncovered @simulated
    Scenario: U13 Partial and complete raw reports are joined before summary generation
      Given a simulated unchanged candidate with completed unit raw coverage and a separate integration scope still pending
      When the integration raw report completes and the relevant report set becomes complete
      Then ReportGenerator creates the overall summary from the complete raw set once
      And the overall and integration report scopes remain distinct
      When CHECK continues on the same candidate with the same raw reports and filters
      Then the existing summary and logs remain reusable for independent judgment
      And no collection or ReportGenerator run is caused only by CHECK continuation
      # source: skills/pdca-dotnet/SKILL.md §Coverage comparison and report reuse
      # source: skills/pdca/references/check.md §Candidate identity

    @U14 @uncovered @simulated
    Scenario: U14 A report-generation error is corrected without recollecting valid raw coverage
      Given a simulated complete immutable raw coverage set and a summary-generation failure caused by an invalid report-tool setting
      When the report setting is corrected without changing candidate or collection inputs
      Then the failed report attempt remains recorded
      And the summary is regenerated from the retained raw reports without recollecting coverage
      # source: skills/pdca-dotnet/SKILL.md §Coverage comparison and report reuse

    @U15 @uncovered @simulated
    Scenario: U15 A failed collect and a completed assertion failure are reported separately
      Given a simulated collect process that exits before producing complete coverage data with a diagnostic pointing to a configuration failure
      And a separate test run that completes and reports an assertion failure
      When the executor records both runs and the configuration cause is corrected
      Then the incomplete collect remains failed evidence and is not a cached success
      And only still-needed evidence affected by the corrected configuration is eligible for a justified retry
      And the completed assertion remains result evidence rather than being classified as infrastructure
      # source: skills/pdca-coder/SKILL.md §Test run safety (every phase — DO and CHECK)
      # source: skills/pdca-dotnet/SKILL.md §Coverage comparison and report reuse

    @U16 @uncovered @simulated
    Scenario: U16 A matching test build is reused for collection and CHECK
      Given a simulated affected project whose product and test compiled inputs and effective build settings match a recorded build
      When the authorized boundary launches coverage collection against that candidate
      Then `--no-build` may use the verified matching artifact
      And launching collection or CHECK alone does not cause another compilation
      And a later compiled-input change invalidates the affected artifact and may require a rebuild
      # source: skills/pdca-dotnet/SKILL.md §.NET toolchain and commands
