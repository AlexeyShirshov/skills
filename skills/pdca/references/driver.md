# DRIVER: dispatcher mechanics

The driver (`pdca-orchestrator`, or the normal-mode primary) reads this file in full right after it
loads the contract (`../SKILL.md` §References). Every context loads the **base `pdca` entry contract
first, by exact ID**, and resolves this file, `references/check.md` and `references/escalate.md` against
the **base directory its load result returns**; a form contract never supplies that directory, so it
is loaded in addition, never instead. It records **only mechanics no phase or form contract owns**:
adopting a fresh decision, composing a dispatch and its read scope. Each policy stays with its owner;
the contract wins conflicts, and a missing rule blocks rather than invites reconstruction. After
each PLAN selects a form/overlay, base §Preflight — required skill contracts owns the exact-ID
dependency closure and must pass before dependent preparation, DO or work dispatch.

| Rule | Owner |
|---|---|
| form/overlay **discriminators**, plan fields, terminal outcomes | `plan.md` §Entry and first step (planner-owned and planner-read); `../SKILL.md` §Forms only routes a decided form to its contract and pairs its human label with the machine form id |
| the driver's own read scope | this file §Read scope — the base §Roles only points here |
| approval protocol, handoff fidelity, reference-not-repetition | `../SKILL.md` §Normal-mode approval, §Reference, not repetition |
| evidence root, persisted evidence, every write via executor, Git state | `../SKILL.md` §Workspace and durable status |
| counters, defect history, thresholds, escalation trigger | `../SKILL.md` §State machine and counters |
| phase exits, recovery, red flags, role permissions | `../SKILL.md` §Phase contracts, §Recovery, §Red flags, §Roles and host requirements |
| collection P/barrier/lanes/approval barrier | the loaded `pdca-collection` contract |
| campaign bootstrap, step, boundary, stop | the loaded `pdca-incremental` contract |
| CHECK method and verdict | `check.md` (inlined in every dispatch) |
| escalation grounds and input | `escalate.md` (inlined with the expert brief; its §Input and permissions is the brief's required input) |

## Entry adoption

A fresh dispatch carries `contract: pdca`, `form: UNDECIDED` and no persisted plan. Then:

1. `pdca-scout` gathers the minimum facts, pointers only.
2. One `pdca-planner` call carries the original goal unchanged, the facts as pointers, the
   decision-relevant unknowns, any user-named form/overlay as a constraint, and the
   `plan_reference_path` — the absolute path of the loaded `pdca` skill's `references/plan.md`. The
   **only** form/overlay discriminator is `plan.md` §Entry and first step, which the planner reads
   there: the dispatch carries no copy of the base §Forms routing table and no second form-selection
   text. Never read or inline that file, or forward its contents.
3. The returned plan **is** the initial plan. `pdca-executor` persists it and the same controller
   continues at the **PLAN → DO** boundary of the decided context: no second full PLAN, no fresh
   controller, no new state file.
4. A bounded choice probe is executed by `pdca-executor`, observed by `pdca-scout`, and refined by
   the **same** planner while the form stays `UNDECIDED`.
5. A plan missing a mandatory field — the justified method/volume reason, or a bespoke checker's
   insufficiency reason and bound — is **incomplete**: return it to the same planner as a
   clarification of the same pending PLAN. That is not a replan and never makes the form your choice.
6. A decided **collection** returns to its existing owner, which loads `pdca-collection` and runs
   the batch; do not become its owner, spawn a second orchestrator or widen the allowlist. A decided
   **campaign** is adopted as `campaign-control`, reuses the entry choice for its first step, and
   follows `pdca-incremental` for preparation/baseline without inventing at preparation.
7. `plan_handoff`, `preparation_handoff` and resume are never re-planned: a named plan ref in the
   existing brief or status is enough.

## Dispatch transport

**Dispatchability gate (before any DO dispatch).** A plan about to be dispatched must name, for a
measurable goal, its measurement method (block 4 of a step brief) and targets the goal's own domain
allows one to point at. A plan naming only an area, cluster, theme or category where pointable items
exist **is not dispatchable**: return it to the same planner, missing block named. The driver fills
no such gap itself or through DO discovery, and DO-discovered work never replaces the plan's
targets. Where the domain genuinely has no such items, say so in the dispatch: that absence belongs
to the goal, not a licence for vague targets.

Compose a dispatch from the receiving phase's own contract inputs, plus only these transport items:

- **PLAN** — `plan_reference_path` above; the task by exact reference; the facts as pointers.
- **DO** — frozen plan by exact reference, the cycle's `evidence_root`, phase-specific deltas, and the phase report exactly as returned or an exact reference to its complete readable artefact. A digest, retelling or translation is not a source. An overlay's helper lives in that overlay's `scripts/` (`pdca-dotnet` ships `validate_inner_loop.py` and `pdca_evidence.py` there, never in the base's); the project's `.pdca/scripts/` starts empty and the executor stages byte-identical copies — a missing copy is never a substitute-check, waiver or `Notice:` ground. For code work, apply the selected-overlay section rule below.
- **CHECK** — in every `pdca-check` dispatch (first check, recheck, campaign step, collection lane/item, integration check), inline the **complete contents** of `check.md` with **no path and no instruction to read it**. Candidate CHECK also gets applicable PLAN-selected overlay sections **verbatim inline**, with no path or instruction to open an installed file. If it cannot be loaded whole, return a blocker before dispatch. This delivery does not grant file access or choose a method. Pass the candidate identity and evidence pointers, not changed files.
- **ACT retrospective CHECK** — inline complete `check.md` and the `act.md` retrospective contract; omit selected-overlay proving/run sections.
- **ESCALATE** — build the brief from `escalate.md` §Input and permissions and pass that protocol's **complete contents inline** (fail closed before dispatch if it cannot be loaded whole): the narrow question and its boundaries, original task, phases and role asking, criteria in play, result, evidence reused, not re-gathered, what was already tried and why it failed, attempts, constraints, pre-gathered scout pack, and live cycle `N`, revision `r`, attempt `n/3` and defect history (each key, observed attempts and applied fixes). The counter procedure is the base §State machine and counters, already loaded by the driver; nothing here re-thresholds it and the expert has no discretion to waive it.
- **Status work** — `pdca-executor` reads `act.md` itself; the driver passes source reports unrewritten and never renders status content.
- **Selected-overlay section delivery** (candidate DO/CHECK only) — PLAN owns the selected overlay set. First pass the base §Preflight — required skill contracts for its exact-ID closure; then use only relevant sections from those already loaded skill contents. Never discover, select or load another overlay or open an installation-path file. DO gets each applicable section verbatim or as an exact skill-ID + file/heading reference DO can read. CHECK gets applicable sections verbatim inline, with no path/open instruction. Select by criterion, evidence and actual run, not overlay presence. Do not deliver whole overlays or unrelated skills by default; if a section is unavailable, block rather than summarize, widen permissions or substitute.
  Section map (locations only; applicability remains phase/criterion-specific):
  | Selected overlay | Applicable evidence/run sections |
  |---|---|
  | `pdca-coder` | `SKILL.md` §Code evidence requirements (relevant rules); §Coverage evidence lifecycle; §Build and test command forms; §Test run safety (every phase — DO and CHECK), only when relevant. |
  | `pdca-dotnet` (inherits coder) | Relevant coder sections, plus `SKILL.md` §.NET toolchain and commands; §Coverage comparison and report reuse; §.NET check deltas → Tests are judged on the applicable complete scope; §.NET do/act deltas → Freeze order and line endings, Integration lane or Test host safety (DO and CHECK), only when relevant. |

### Interrupted dispatches

Preserve exact brief, counters, handle/checkpoint and output; reuse completed results or resume the session. Never duplicate a live/unknown planner/executor call; follow host completion without polling.
If status remains unknown at host timeout, retain the handle and record a Recovery resource blocker (not confirmed failure); continue independent authorized work.
Do not poll, wait indefinitely or retry until failure is confirmed. Transport changes no counters/history.
After confirmed failure and transient-cause resolution, retry unchanged once; another failure is a Recovery blocker, not a primary PLAN decision.

## Read scope

This section is the single owner of the driver's own reads; base §Roles and §Escalation only point here, and no other file restates the list.
- loaded base/form/PLAN-selected overlays by exact ID through the host skill mechanism; use their loaded contents only, never open an installation-path file;
- `references/driver.md` (this file), in full, once;
- `references/check.md`, opened only to inline it whole into a `pdca-check` dispatch (plus the retrospective contract from `references/act.md` for a retrospective dispatch);
- `references/escalate.md`, opened only to build an ESCALATE brief before that dispatch;
- the exact recovery prompt `assets/install-agents-prompt.md` or `assets/install-skills-prompt.md`, relative to the loaded base skill, only when its corresponding preflight fires;
- the assigned cycle, campaign or lane **status files** used as dispatch context, incl. step-boundary (base §Recovery).

Nothing else: no phase or form procedure reference except `references/act.md`'s retrospective contract for inline delivery, no workspace walk, no `rg`/`grep`,
and not the executor's status file for a REPORT-compare — there the last status comes from the executor's report, never from reading the file (base §State machine).
Metadata — status path, form, contract, overlay, dispatch rule and refs — arrives through allowed tool inputs/outputs; for evidence ask `pdca-executor` or `pdca-scout` for its report instead.

## Routed, not taken

- Planner decisions are routed, never re-decided: the next step or the STOP exactly as the loaded
  `pdca-incremental` contract's §Step boundary says, including a pre-approved STOP on PASS; a
  non-PASS goes back to the planner as a loop-back.
- A PLAN-terminal outcome goes to **ACT** with its cause and evidence (base §PLAN → ACT); a DO that
  cannot finish goes to **ACT** (base §DO → ACT), never back to PLAN. Inside a campaign step an
  established result still needs the independent CHECK.
- Approval is the primary's: a caller-driven handoff carries the durable pending ref, and a missing or
  mismatched record yields an approval-needed checkpoint — never DO and never a fresh PLAN
  (`../SKILL.md` §Normal-mode approval; a paused collection item stays `in-progress` with
  `disposition=paused`).
- A `pdca-check` finding routes by its own exit; an escalation decision is forwarded without semantic
  re-decision; no gate, scope or permission is waived by routing.
