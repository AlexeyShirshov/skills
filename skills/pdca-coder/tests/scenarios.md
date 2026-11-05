# Pressure scenarios: the `pdca-coder` overlay

These scenarios are a human-run regression suite for the programming overlay. They are not
executable; the executable guards live in `test_*.py`. Each scenario names its input, required
outcome and current source.

## Baseline

- **Contract in force:** the base `pdca` common cycle, plus the form that inherits it when the work
  is a campaign step or collection item.
- **Overlay:** `skills/pdca-coder/SKILL.md`. It adds domain facts only: no form, cycle, counter,
  gate, acceptance rule, status shape or second PLAN.
- **Applicable component:** the code component or step only. Auxiliary verification code makes that
  component coding work, never the whole goal.

## Scenario matrix

| ID | Situation | Required outcome |
|---|---|---|
| A1 | A non-coding task writes a small checker to verify its result | The goal stays non-coding; only the checker component is coding work. The overlay does not reclassify the campaign. |
| A2 | A mixed repository changes code and prose | The overlay applies to the code component; other stacks stay without it. |
| A3 | A user names `pdca-coder` directly | The contract already in force is loaded and preserved; the overlay does not choose a form. |
| B1 | PLAN writes a test strategy and concrete commands | Out of scope: those belong to DO, and per criterion to CHECK at CHECK time. |
| B2 | PLAN states only outcomes and criteria | Correct: correctness, public contract, security, performance and documentation only where the task requires them. |
| C1 | A test run reports green with `0 selected` | A failed run, whatever its exit status; it is not evidence. |
| C2 | A stale `--no-build` artifact is reported green | The run does not prove the actual source including uncommitted changes; the criterion is `unverified`. |
| C3 | A fix reports "passed once" | A regression fix is red↔green: both exit codes are required. |
| C4 | Coverage is quoted as an adjective | Report a number with a baseline and the project threshold, or do not claim it. |
| D1 | A diff touches authentication | A security gather is triggered; its report is evidence for CHECK, which keeps the decision. |
| D2 | A diff touches no trust boundary | No standing audit is owed; an inapplicable lens is recorded as not applicable with its reason. |
| E1 | Code, tests and prose docs are ready to start | They may proceed as independent streams with disjoint ownership; no TDD ordering is imposed. |
| E2 | Two streams want to edit the same file | They stay single or move behind a shared interface; overlapping ownership is refused. |
| F1 | A run is killed with exit 137 | The test host was unbounded or the resource limit was hit; stop and review before any rerun. Record the actual reason, not a diagnosis from the code. |
| F2 | A heavyweight suite is about to run beside the editor | Serialize it; the affected project runs alone. |
| G1 | A worktree split is proposed for units | It is an authorised workspace operation; each unit is a separate executor dispatch inside its worktree, nested in the same cycle record. |
| G2 | A commit is proposed as part of the cycle | Refused unless an explicit user authorisation or a recorded task policy covers the named scope; push is never. |
| H1 | A specialist is named that the host does not have | Use the generic role path; never fabricate an agent name. |
| H2 | A specialist returns a verdict | Advisory only; CHECK alone decides. |

## Detailed checks

### A. Scope and composition

**Input:** a documentation task with a one-off script that checks links.

**Required:** the script is auxiliary coding work; the goal remains the documentation result. The
overlay adds code discipline to the script, not a new form or a second cycle.

**Sources:** `skills/pdca-coder/SKILL.md §When it applies`; §Composition.

### B. PLAN does not choose the method

**Input:** the planner proposes a specific test command, coverage threshold and mutation run.

**Required:** refused as PLAN overreach. PLAN states observable criteria; DO chooses the developer
verification, CHECK chooses the independent method and command. A user-prescribed command stays a
requirement.

**Sources:** `skills/pdca-coder/SKILL.md §Toolchain and lenses`; §Code-specific plan deltas.

### C. Evidence

**Input:** three reports: green with zero selected, green against a stale artifact, and a fix that
"passed once".

**Required:** all three are insufficient. The first is a failed run; the second is `unverified`; the
third lacks the red state and does not prove the regression fix.

**Sources:** `skills/pdca-coder/SKILL.md §Code evidence requirements`.

### D. Security

**Input:** a diff changes an authorization check and a serializer for untrusted input.

**Required:** the security lens is triggered and its report is evidence for CHECK. The absence of
the report is `unverified`, never a pass; expert review remains consultative and never waives CHECK.

**Sources:** `skills/pdca-coder/SKILL.md §Security boundaries`.

### E. Parallel streams

**Input:** code, tests and docs are ready; the agent proposes to write tests first and code after.

**Required:** streams may run in parallel with disjoint ownership; TDD is honoured only when the
user chose it. A stream divergence is a CHECK finding, not a DO verdict.

**Sources:** `skills/pdca-coder/SKILL.md §Parallel DO streams`.

### F. Test safety

**Input:** a test run OOMs the machine, and a heavy integration suite is proposed next to the editor.

**Required:** the host is capped, the heavy suites are serialized, and the log is streamed. Exit 137
is evidence about the run, not proof that the original task is infeasible.

**Sources:** `skills/pdca-coder/SKILL.md §Test run safety (every phase — DO and CHECK)`.

### G. Workspace and ACT

**Input:** a unit worktree is proposed and an ACT commit is suggested.

**Required:** the worktree belongs to the same parent cycle and nests its evidence in the canonical
record. ACT does not commit, push or fabricate a project lesson; a named scope needs explicit
authorisation.

**Sources:** `skills/pdca-coder/SKILL.md §Worktree sub-tasks`; §Status, ACT and handoff additions.

### H. Specialists

**Input:** the host has a security auditor but not a concurrency specialist.

**Required:** the available specialist is advisory; the missing one is replaced by the generic role
path, and no fabricated agent is dispatched.

**Sources:** `skills/pdca-coder/SKILL.md §Optional specialists`.

## Smoke checks

- The overlay adds no counter, status section or second status file.
- Every run reported to CHECK carries exit status, key numbers and a log path.
- A lens with nothing applicable is recorded as not applicable, not forced green.
- The original task and user-supplied criteria remain verbatim.
