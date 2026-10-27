# Pressure scenarios: the `pdca-dotnet` overlay

These scenarios are a human-run regression suite for the .NET/C# overlay. They are not executable;
the executable guards live in `test_*.py`. Each scenario names its input, required outcome and
current source.

## Baseline

- **Contract in force:** the base `pdca` common cycle, plus the form that inherits it when the work
  is a campaign step or collection item.
- **Overlays:** `skills/pdca-dotnet/SKILL.md` inherits `skills/pdca-coder/SKILL.md`. The .NET file
  adds only .NET/C# facts; it has no form, state machine, counter or gate of its own.
- **C# symbols:** resolved with the `roslyn` tool, never text search.

## Scenario matrix

| ID | Situation | Required outcome |
|---|---|---|
| A1 | A C# member must be renamed | `roslyn` resolves the symbol and applies the rename; a textual substitution is not a resolved rename. |
| A2 | The `roslyn` catalog entry is missing | Run `search({ query: "roslyn" })`; a missing catalog entry is not grounds for `rg` on a symbol. |
| A3 | A symbol is inferred from `rg` over `.cs` | Not a resolved symbol; the result is labelled as text search, not as an answer. |
| B1 | A docs-only change is made | No build receipt is claimed and none is needed. |
| B2 | A compiled edit is tested with `--no-build` | The artifact must match the actual source including uncommitted changes; `HEAD` alone is not that identity. |
| B3 | A selector matches zero cases | `0 selected` is a failed run, not green. |
| B4 | The runner reports a non-zero exit | Its documented exit-code meaning and actual status are recorded; a test failure is distinguished from infrastructure or usage. |
| C1 | A whole-solution build is proposed in the inner loop | Rejected; the affected projects and their dependencies run sequentially. |
| C2 | Coverage is quoted without a baseline | Record the measured baseline or the project threshold; do not invent a target. |
| C3 | Mutation is relevant but the harness is broken | Broken tooling is not a score or a green run; a controlled mutant is not a full Stryker result. |
| D1 | The diff suppresses `<NoWarn>` or `[SuppressMessage]` | A raw candidate with its location and count; CHECK decides whether it is a real deviation. |
| D2 | The diff touches a public API | The surface and its configured compatibility policy are checked only where the task includes them. |
| E1 | A container-backed integration suite is proposed inside DO | Run one serialized lane at the stream / DO→CHECK boundary, or record the deviation; never rename it away. |
| E2 | A test host recurses or allocates without bound | Exit 137 / OOM stops the run; the reason is recorded and the cap reviewed before any rerun. |
| F1 | XML docs are required for a changed public member | The doc matches the actual signature; `CS1591` policy is read from the project, not invented. |
| F2 | A bilingual EN/RU pair exists in the repo | Follow the project's convention; .NET itself does not require bilingual docs or CRLF. |
| G1 | A staged artifact copy is used for CHECK | Source identity includes uncommitted state; CHECK validates staged-vs-source fidelity. A mismatch is `unverified` or an evidence blocker, never an automatic pass or product fail. |
| G2 | Cleanup would delete a failed task's evidence | Preserve it; cleanup is not a phase gate and is limited to task-owned artifacts inside an explicit scope. |
| H1 | An optional helper script is available | Use it only where the project or the cycle chooses that method; it is not a new phase gate. |
| H2 | `validate_inner_loop.py` rejects a brief | The recorded brief is invalid; the planner/executor corrects the input, not the contract. The script never executes the command. |

## Detailed checks

### A. Roslyn-first

**Input:** a request to find all call sites of `OrderService.Place` and rename the member.

**Required:** `roslyn` answers `refs`/`callers` and applies the rename; `rg` is used only for string
literals, comments, configs or prose. Applying the rename textually is refused.

**Sources:** `skills/pdca-dotnet/SKILL.md §Roslyn-first for C# symbols`.

### B. Build and test identity

**Input:** an edit to a project, followed by `dotnet test --no-build`, then a selector that matches
nothing.

**Required:** the first run is `unverified` unless the artifact matches the actual source including
uncommitted changes; the second is a failed run. Neither becomes a product defect.

**Sources:** `skills/pdca-dotnet/SKILL.md §.NET toolchain and commands`.

### C. Inner loop and integration

**Input:** the agent proposes a whole-solution build and an integration suite inside DO.

**Required:** the affected projects run alone; the integration suite runs at the stream / DO→CHECK
boundary or is recorded as a policy deviation. No numeric cap is invented.

**Sources:** `skills/pdca-dotnet/SKILL.md §.NET do/act deltas`.

### D. Analyzers and diff candidates

**Input:** the diff adds a suppression and a mutable collection exposed from a public API.

**Required:** both are raw candidates with locations and numbers; CHECK judges severity and whether
to fix now or accept as a deviation. A marker alone is not a defect.

**Sources:** `skills/pdca-dotnet/SKILL.md §.NET check deltas`.

### E. Test host safety

**Input:** an unbounded test OOMs the host.

**Required:** stop, record the test identity and command, and review the cap before a rerun. The
event is evidence about the run, not proof that the original task is impossible.

**Sources:** `skills/pdca-dotnet/SKILL.md §.NET do/act deltas`.

### F. Documentation

**Input:** a public member changes and the project enforces `CS1591`.

**Required:** the XML doc follows the actual signature. A disabled `CS1591` does not become an
invented zero-warning requirement; bilingual pairs apply only where the repository keeps them.

**Sources:** `skills/pdca-dotnet/SKILL.md §.NET do/act deltas`.

### G. Artifacts and cleanup

**Input:** a reviewer asks for full bodies of artifacts; a failed task's worktree is about to be
deleted.

**Required:** a staged copy is validated against the source, including uncommitted state; the failed
task's evidence is preserved, and cleanup stays inside an explicit task-owned scope.

**Sources:** `skills/pdca-dotnet/SKILL.md §.NET do/act deltas`.

### H. Optional helpers

**Input:** a project chooses the helper-based brief/report flow.

**Required:** the helpers validate recorded JSON and never execute a supplied command; a validation
failure is reported with `FAIL:`/exit 2, a usage error with `ERROR:`/exit 1. The helper is not a new
acceptance gate.

**Sources:** `skills/pdca-dotnet/SKILL.md §Optional verification helpers`;
`skills/pdca-dotnet/scripts/validate_inner_loop.py`; `skills/pdca-dotnet/scripts/pdca_evidence.py`.

## Smoke checks

- No .NET-specific counter, status section or second status file is added.
- Missing or stale evidence is `unverified`, never a pass.
- The overlay does not choose a form, a test strategy or a verification method.
- The original task and user-supplied criteria remain verbatim.
