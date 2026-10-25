# DO and ACT deltas for .NET: journal, integration policy, cleanup

Reference for the DO and ACT phases of the .NET overlay. The base DO/ACT contracts — the DO report,
the status-file lifecycle, unit states and the `superseded→replacement` rule, the closing order and
the next-session message — stay in `../../pdca/SKILL.md` and `../../pdca/references/act.md`. The code
streams, the worktree protocol, the coder editing discipline, the subagent report format, the
debugging order, the code status rows and the handoff additions stay in
`../../pdca-coder/references/act.md`. This file adds the execution journal, the unit/integration
policy, the ACT cleanup receipt and the .NET status rows.

## Execution journal and the unit/integration policy

**The restriction is on the ACTUAL integration-test run, not on the number of report entries.** Unit
tests are unlimited inside DO and at phase boundaries; *expensive integration runs* are permitted at
the **DO → CHECK boundary**, not after every unit/edit. The presence or absence of `--filter` is **not**
a unit-vs-integration criterion and is **never** grounds to restrict unit execution: classification
follows the test projects/suites actually selected, so a mixed solution run that really executes
integration is not "unit" because of a command name or a filter.

- **PLAN fixes the boundary integration scope and the allowed runs up front** (the
  `integration_projects` / `integration_boundary_runs` of the mandatory `test scope`). This skill
  invents **no** separate universal numeric cap. An extra actual integration run outside the allowed
  plan/boundary is a **visible deviation** subject to the existing gates — it is not masked by a phase
  or a rename.
- **Mandatory execution capture path.** For the cycle's test commands, a `start` event is recorded **at
  launch** and the result is **appended** on completion (`journal`). The report that CHECK consumes is
  **projected from that journal**, not hand-selected by the author:
  `.pdca/scripts/validate_inner_loop.py project <journal.json>` rebuilds it mechanically, and
  `.pdca/scripts/validate_inner_loop.py report <report.json> --journal <journal.json>` proves the
  report is a faithful projection. A projection that **omits a started execution is rejected** — a
  completeness failure, never a way to pass a cap; an over-budget run **stays in the raw journal**.
- **Every actually-started run is recorded regardless of exit code, cancellation, retry, over-budget
  status, or usability as acceptance evidence.** For a run that did **not** start, the execution state
  is stated explicitly — no invented fact. Recording the execution and judging policy compliance are
  **separate** actions: recording a violation does not legalise the run, and its absence does not
  cancel it.
- **Execution states are explicit and distinguishable:** `started`/`running`, `finished`,
  `interrupted`/`canceled`, `failed-to-start`/`not-started`. Exit code and selected count are nullable
  and are **never invented** for a run that did not finish. An unfinished or not-started attempt does
  **not** satisfy a required success, but it **is retained** even after a later successful retry.
  Before launch the path evaluates the integration policy as far as the scope is determinable, so an
  **attempt** violation (`failed-to-start`) and an **executed** violation are recorded as different
  states.
- A run outside the mandatory capture path is a process violation. Detecting an arbitrary hidden shell
  invocation is **not** promised; completeness is enforced within the existing process tooling
  (journal → projection → reconciliation).
- On a pipeline failure, incomplete accounting is explicitly **blocked/unresolved**, never PASS.

The DO brief that launches such a stream carries the mandatory `test scope` envelope
(`references/plan.md` §Inner-loop gate); the worktree brief of the coder overlay additionally carries
the same envelope, validated with `validate_inner_loop.py brief` before any edit.

### DO report: test evidence (mandatory)

In every dispatch brief, state the response format explicitly. On top of the coder report format the
.NET brief requires the **test evidence** block — the actual build/test invocations as **argument
arrays** (not shell strings), each with its `--filter` value, `phase` (`inner`/`boundary`),
`exit_code`, the number of selected tests (`selected_count ≥ 1`), and the
`.pdca/scripts/validate_inner_loop.py report <evidence.json>` **exit code**. A zero-match run or a
missing `selected_count` ⇒ CHECK FAIL, and missing or invalid evidence ⇒ CHECK cannot pass.

## ACT cleanup receipt (heavy staged materials)

Staged evidence is **retained** until the independent CHECK, review and task closure are complete — it
is not cleaned on every DO → CHECK. On a genuine task closure in ACT, this task's **heavy staged file
copies and temp materials** are removed; there is no premature cleanup on STOP / incomplete /
awaiting-decision / continuing work.

The cleanup is gated by a **machine-checkable receipt**, not by prose
(`.pdca/scripts/validate_inner_loop.py cleanup <receipt.json>`). The receipt is bound to the task and
its `rv`, to the **approved terminal closure** and to the independent final verdict, and lists the
removed paths with their **prior hashes** plus the retained records:

- **Gate before cleanup:** the right to terminal closure is checked *before* deletion. A receipt
  without an approved terminal closure or without the independent final verdict is **rejected**
  (premature cleanup).
- **Deletion scope:** only explicitly cleanable staged copies / temp files **inside this task's own
  `rv` dir** may be removed. A blanket `rm` of the whole task dir, a broad pattern, or another task's /
  `rv`'s files are rejected; the mandatory retained **report / manifest / digests / certification**
  are never removed.
- The **frozen manifest is not rewritten** or retroactively turned into different evidence; its digest
  is checked against the receipt by `.pdca/scripts/validate_inner_loop.py archived <manifest.json>
  --cleanup <receipt.json>`. Post-ACT removed staged paths are explained by the receipt (prior hash +
  lifecycle state), so a correctly cleaned-up snapshot is a **planned lifecycle**, not "the original
  evidence never existed"; a missing snapshot **before** ACT or without a valid receipt stays an
  **error**.
- The compact retained records do **not** promise that the full review can be re-run without the
  cleaned bodies; archived validation claims no re-certification over removed bodies, and it does not
  replace the checks. Pre-existing historical task artifacts (in particular #218) are neither repacked
  nor cleaned here.

## Status-file additions (.NET)

The base status schema and the coder's code rows stay as they are (durable state, defect history,
unit states, lifetime, progress log). On top of them a .NET cycle records:

- the **contract revision `rv`** and its pinned rows (with their evidence expectations, owner stream
  and applicability predicate), the frozen evidence manifest path and the finite CHECK re-gather
  budget with its owner;
- the **`PLAN-LINT`** row: the `plan_lint.py check` receipt path and exit code;
- the **attempt identity** `task/N/r/n`, the frozen snapshot hash and the authoritative
  `manifest.json` path of the current attempt child, plus the evidence root
  `.pdca/<task>/rv<k>/attempts/c<N>-r<r>-n<n>/` — recorded before DO→CHECK;
- the **integration scope** — `integration_projects` and `integration_boundary_runs` — from the
  mandatory `test scope`;
- a pointer to the **reviewer evidence pack** staged at the DO → CHECK boundary (the full text of the
  pack contract is in `references/plan.md` §Reviewer evidence pack);
- the **cleanup receipt** path on a genuine terminal closure.

These rows are additions to the existing file, not a second durable state: the status file remains the
single source of truth for the plan, progress, counters and defect history.
