# Gherkin description of the `pdca-coder` overlay pressure scenarios.
#
# This is the human-run regression suite of the programming overlay, not a test
# the runner executes. The executable guards live in `test_*.py`; the mapping
# below is explicit so that a rule cannot silently lose its guard.
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
#   overlay     skills/pdca-coder/SKILL.md — domain facts only: no form, cycle,
#               counter, gate, acceptance rule, status shape or second PLAN
#   scope       the code component or step only; auxiliary verification code makes
#               that component coding work, never the whole goal
#
# Note: the overlay's static assets (role permissions, tier labels, cost
# accounting, the hand diagram) are guarded by other `test_*.py` modules. Those
# guards are not scenario counterparts and do not appear below.

Feature: The pdca-coder overlay under pressure
  The overlay must add code discipline to whichever form is already in force,
  and must not become a second cycle, a second classifier or a permission of its
  own.

  Rule: The overlay applies to the code component only

    @A1 @uncovered
    Scenario: A1 A non-coding task writes a small checker
      Given a documentation task whose result is verified by a one-off script
      When the script is written
      Then the goal stays non-coding
      And only the checker component is coding work
      And the overlay does not reclassify the campaign or the collection item
      # source: skills/pdca-coder/SKILL.md §When it applies
      # source: skills/pdca-coder/SKILL.md §Composition

    @A2 @uncovered
    Scenario: A2 A mixed repository changes code and prose
      Given a repository with code and prose in the same change
      When the overlay is loaded
      Then it applies to the code component
      And the other stacks stay without it
      # source: skills/pdca-coder/SKILL.md §When it applies

    @A3 @uncovered
    Scenario: A3 A user names pdca-coder directly
      Given the user names the coder overlay
      When the cycle starts
      Then the contract already in force is loaded and preserved
      And the overlay does not choose a form
      And the overlay does not create a cycle of its own
      # source: skills/pdca-coder/SKILL.md §Composition

  Rule: PLAN states outcomes, DO and CHECK choose the method

    @B1 @uncovered
    Scenario: B1 PLAN writes a test strategy and concrete commands
      Given a plan that names a specific test command, coverage threshold and mutation run
      When the plan is reviewed
      Then it is PLAN overreach and is refused
      And the test strategy belongs to DO
      And the per-criterion verification belongs to CHECK at CHECK time
      And a command the user prescribed stays a requirement
      # source: skills/pdca-coder/SKILL.md §Code-specific plan deltas
      # source: skills/pdca-coder/SKILL.md §Toolchain and lenses

    @B2 @uncovered
    Scenario: B2 PLAN states outcomes and criteria only
      Given a plan that names observable outcomes and criteria
      When the plan is reviewed
      Then it is correct
      And it covers correctness, public contract, security, performance and documentation only where the task requires them
      And it freezes no implementation or verification procedure
      # source: skills/pdca-coder/SKILL.md §Code-specific plan deltas

  Rule: Code evidence must prove the actual source

    @C1 @uncovered
    Scenario: C1 A test run reports green with zero selected tests
      Given a test run that selected zero tests
      When its report claims green
      Then the run is a failure, whatever its exit status
      And it is not evidence for any criterion
      # source: skills/pdca-coder/SKILL.md §Code evidence requirements

    @C2 @uncovered
    Scenario: C2 A stale no-build artifact is reported green
      Given a compiled edit and a run against a stale artifact
      When the run reports green
      Then it does not prove the actual source including uncommitted changes
      And the criterion stays unverified
      And the fix is a fresh affected build, not a product defect
      # source: skills/pdca-coder/SKILL.md §Code evidence requirements

    @C3 @uncovered
    Scenario: C3 A regression fix reports passed once
      Given a regression defect and its fix
      When the fix reports a single green run
      Then it is insufficient: a regression fix is red and green
      And both exit codes are required
      # source: skills/pdca-coder/SKILL.md §Code evidence requirements

    @C4 @uncovered
    Scenario: C4 Coverage is quoted as an adjective
      Given a report that calls coverage good or high
      When it is offered as evidence
      Then it is rejected
      And a number is reported with its baseline and the project threshold, or no coverage is claimed
      # source: skills/pdca-coder/SKILL.md §Code evidence requirements

  Rule: Security is a gather, not a verdict

    @D1 @uncovered
    Scenario: D1 A diff touches authentication
      Given a diff that changes an authorization or authentication path
      When the diff is reviewed
      Then a security gather is triggered
      And its report is evidence for CHECK
      And CHECK keeps the decision
      # source: skills/pdca-coder/SKILL.md §Security boundaries

    @D2 @uncovered
    Scenario: D2 A diff touches no trust boundary
      Given a diff with nothing on a trust boundary
      When the security lens is applied
      Then no standing audit is owed
      And the inapplicable lens is recorded as not applicable with its reason
      # source: skills/pdca-coder/SKILL.md §Security boundaries

  Rule: Parallel DO streams need disjoint ownership

    @E1 @uncovered
    Scenario: E1 Code, tests and prose docs are ready to start
      Given code, tests and documentation that can proceed independently
      When DO starts
      Then they may run as independent streams with disjoint ownership
      And no TDD ordering is imposed
      And a stream divergence is a CHECK finding, not a DO verdict
      # source: skills/pdca-coder/SKILL.md §Parallel DO streams

    @E2 @uncovered
    Scenario: E2 Two streams want to edit the same file
      Given two streams whose files overlap
      When the overlap is detected
      Then they stay single or move behind a shared interface
      And overlapping ownership is refused
      # source: skills/pdca-coder/SKILL.md §Parallel DO streams

  Rule: A test run must not take the host down

    @F1 @uncovered
    Scenario: F1 A run is killed with exit 137
      Given a test run killed with exit code 137
      When the outcome is recorded
      Then the test host was unbounded or the resource limit was hit
      And the run stops and the cap is reviewed before any rerun
      And the actual reason is recorded, not a diagnosis from the code
      # source: skills/pdca-coder/SKILL.md §Test run safety (every phase — DO and CHECK)

    @F2 @uncovered
    Scenario: F2 A heavyweight suite is about to run beside the editor
      Given a heavyweight integration suite and a responsive-editor requirement
      When the suite is scheduled
      Then it is serialized
      And the affected project runs alone
      # source: skills/pdca-coder/SKILL.md §Test run safety (every phase — DO and CHECK)

  Rule: Workspace operations and ACT stay authorized

    @G1 @uncovered
    Scenario: G1 A worktree split is proposed for units
      Given a cycle with units that could run in separate worktrees
      When the split is proposed
      Then it is an authorised workspace operation
      And each unit is a separate executor dispatch inside its worktree
      And every unit stays nested in the same cycle record
      # source: skills/pdca-coder/SKILL.md §Worktree sub-tasks

    @G2 @uncovered
    Scenario: G2 A commit is proposed as part of the cycle
      Given a finished unit and a proposed commit
      When the commit is considered
      Then it is refused unless an explicit user authorisation or a recorded task policy covers the named scope
      And push is never part of the cycle
      # source: skills/pdca-coder/SKILL.md §Status, ACT and handoff additions

    @G3 @uncovered
    Scenario: G3 A code cycle closes without inventing a project lesson
      Given a code cycle that reaches ACT
      When the closing work is considered
      Then no AGENTS.md, registry or project docs edit is forced and no project lesson is fabricated
      And the base mandatory evidence-grounded status retrospective in `Lessons learned` still runs
      And it requires no product or docs write
      # source: skills/pdca-coder/SKILL.md §Status, ACT and handoff additions

  Rule: Specialists are optional and advisory

    @H1 @uncovered
    Scenario: H1 A specialist is named that the host does not have
      Given a specialist the host does not provide
      When the cycle needs that expertise
      Then the generic role path is used
      And no agent name is fabricated
      # source: skills/pdca-coder/SKILL.md §Optional specialists

    @H2 @uncovered
    Scenario: H2 A specialist returns a verdict
      Given a specialist's report
      When the acceptance decision is made
      Then the report is advisory only
      And CHECK alone decides
      # source: skills/pdca-coder/SKILL.md §Optional specialists

  Rule: The overlay adds no second contract

    @S1 @uncovered
    Scenario: S1 The overlay adds no counter or status file
      Given any campaign step or collection item using this overlay
      When its status is written
      Then no overlay-specific counter is added
      And no overlay-specific status section is added
      And no second status file is created
      # source: skills/pdca-coder/SKILL.md §Status, ACT and handoff additions

    @S2 @uncovered
    Scenario: S2 Every run reported to CHECK carries its proof
      Given a run reported to CHECK
      When the report is written
      Then it carries the exit status
      And it carries the key numbers
      And it carries a log path
      # source: skills/pdca-coder/SKILL.md §Code evidence requirements

    @S3 @uncovered
    Scenario: S3 A lens has nothing applicable
      Given a code change with no applicable security or performance lens
      When the lenses are applied
      Then the lens is recorded as not applicable with its reason
      And it is not forced green
      # source: skills/pdca-coder/SKILL.md §Toolchain and lenses

    @S4 @uncovered
    Scenario: S4 The original task stays verbatim
      Given any overlay run
      When its result is accepted
      Then the original task and the user-supplied criteria remain verbatim
      # source: skills/pdca-coder/SKILL.md §Code-specific plan deltas
