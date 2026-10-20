# PDCA status — pdca-collection-incremental-composition (cycle 1)

Status file: `.pdca/status/pdca-collection-incremental-composition-1.md`
Evidence dir: `.pdca/pdca-collection-incremental-composition/rv1/`
Design: `docs/superpowers/specs/2026-10-20-pdca-collection-incremental-composition-design.md`
Approved implementation plan: `docs/superpowers/plans/2026-10-20-pdca-collection-incremental-composition.md`
Mode: normal (plan approval required before DO)
Plan revision: r2
Approval: r2 approved by the user — DO started (progress log)
Workspace: `/home/alex/sources/skills`

## Task

Implement the approved composition design §8 (three skill contracts, canonical runner + five byte-identical copies, extensions to twelve existing guard suites, EN/RU documentation) and satisfy all eighteen §9 acceptance criteria without changing the base cycle, the domain variants, role assets, permissions, counters or unrelated work.

## Goal / expected result

`pdca-collection` units have an explicit execution form: `execution_kind=cycle` (a single full cycle) or `execution_kind=campaign` (a sequential incremental campaign led inline by the collection lane driver), with `selected_variant` reserved for a cycle/step, an honest ALL-barrier (real cycle PLAN / approved separate immutable preparation document), baseline bootstrap after the barrier, separate readiness/runtime/disposition, pause ≠ final, conservative whole-task footprint reservation, collection-owned git lifecycle, a dispatcher-only runner in two modes, and domain-agnostic shared rules. Existing guarantees stay intact.

## Constraints

- Only §8-listed files may change (contracts §8.1, tests §8.2, docs §8.3) plus this cycle's administrative artifacts under `.pdca/` and `/tmp/opencode/`.
- Do not edit `opencode/pdca/SKILL.md`, `opencode/pdca-coder/SKILL.md`, `opencode/pdca-dotnet/SKILL.md`, or role assets `pdca-{planner,executor,check,escalate,scout}.md`.
- No git commit, no `git push`, no branch/worktree operations. All edits stay in the working tree.
- No new roles, tiers, model ids, skill contracts, status values, counters, allowlist entries or permissions.
- Runner frontmatter/permissions unchanged: `edit`/`write`/`bash` deny, `task` default deny with the existing allowlist.
- Six runner copies byte-identical; copy the canonical file, never edit mirrors individually.
- New shared composition rules stay domain-agnostic; existing unrelated domain wording is not scrubbed.
- Preserve all pre-existing/foreign working-tree changes; `.pdca/status/wsl-notify-session-filter-1.md` and `.pdca/wsl-notify-session-filter/` are untouched.
- Design cannot be overridden: divergence = stop and return to planner.
- Red-first: every new behavior guard is added to an existing suite before the contract change and must fail on the pre-change tree (valid failure, not a syntax/import error).

## Assumptions

- Working-tree cleanliness is unknown until D0 records it; pre-existing changes are preserved and reported separately.
- Host `subagent_depth` semantics, cap and allowlist sufficiency are unproven; D1 records facts or "not established", never an invented number.
- Cold-host verification remains an OPEN deployment prerequisite recorded in the new section; D1 is done, and this item does not block D2–D9 under r2. Unproven host facts are not assumed, and no numeric sufficiency claim is made.
- Exact new test identifiers and line locations are planned until implemented; the traceability matrix records actual ones.
- No coverage threshold is established; only the designated acceptance checks and existing suites are required.
- Normal-mode approval applies to this plan; the executor follows the approval state recorded by the orchestrator.

## Acceptance criteria (all binding; verification method after the arrow)

- AC01 Two execution models not mixed: standalone `cheap primary → step orchestrator → roles`; campaign in collection led inline by the lane driver; no campaign agent, no new `Task` level. → F01, F02, F10, F11 + source review; negative guard rejects a campaign agent/nested runner.
- AC02 Execution form separated: `execution_kind` (`cycle`|`campaign`) ≠ `selected_variant`; variant only on cycle/step, concrete per step, immutable for the run; dispatch policy belongs to the loaded contract; runner only executes. → F01, F04, F10.
- AC03 Honest barrier: `plan_state=ready` per cycle; approved separate immutable/revisioned preparation document (`preparation_ref` in the unit record, `preparation_state=ready`) with all nine frame items per campaign; baseline/runtime/future step plans not required or simulated; no lane before the barrier. → F05, F10.
- AC04 Bootstrap after barrier: baseline + runtime status by a dedicated executor after the barrier and before the first step DO; runtime references `preparation_ref@r<k>`, no charter copy; not a step, not change-producing; divergence → planner + approval, no backfill; renegotiation → new immutable revision, ref updated, old kept; `campaign_ref` optional before init, mandatory after; ready without runtime = barrier-ready/not started, not `done`. → F05, F06, F10.
- AC05 Preparation ≠ substantive work: pre-barrier preparation records allowed; substantive bootstrap/task DO forbidden; the three operations are distinguishable in contracts and status. → F05, F10.
- AC06 Every step fully planned: a real PLAN of the chosen variant before its DO; variant chosen by step content per current rules; normal mode approved per active contract, durable pending approval ref, current unit `disposition=paused`, lane pause derived; brief does not replace PLAN; autonomous invents no new approval. → F01, F06, F10.
- AC07 Readiness/runtime/disposition separate: `preparation_state`/`plan_state` are not runtime `Status`; campaign `Status` is the existing enum; `disposition` per-unit; lane pause computed; no charter copy; no new task/group statuses including `blocked`. → F06, F07, F10.
- AC08 Pause ≠ final: `blocked`/`stopped` and `unreachable` with an allowed next target → `paused`+`in-progress`; only accepted `met` → `done`; final `incomplete`/group-stop only by explicit final unsuccessful disposition; explicit resume; no infinite retry; `N`/`r`/`n` not reset; a paused lane does not advance its dependent chain, other groups continue; criteria never silently changed. → F06, F07, F08, F10.
- AC09 Footprint = reservation: whole-task conservative allowed surface, not an edit forecast or first-step union; wide allowed; unprovable disjointness → serialization; unknown edits do not cancel the bound; expansion = stop/reapprove, no auto recluster. → F05, F07.
- AC10 Git: collection owns the external commit/branch lifecycle; `Commit policy: none` does not forbid the outer completion commit; a conflicting explicit no-commit restriction is a preflight blocker; campaign completion ≠ outer finalization. → F08, F10, SIM.
- AC11 No new layers/rights: dispatcher-only (`edit`/`write`/`bash` deny, `task` default deny); no own read/write/bash; metadata via tool outputs; direct durable read only in host scope, else executor/scout; skill loading via host mechanism, fallback by an authorized role; no read-wildcard/workspace discovery. → F02, F03, F09, F11.
- AC12 Capability/fallback: observable preflight, safe role check, no dummy substantive work; unavailable driver → flat cheap primary with `Notice:` + durable reason; unavailable mandatory role → resource stop; unavailable cycle contract → fail closed; `escalate → scout` on all paths; late discovery → safe pause; no invented host number; install docs do not treat bare `>= 2` as sufficient; cold-host verification remains an OPEN deployment prerequisite, not a blocker for D2–D9. AC12 is satisfied as documentation of the prerequisite; this does not establish clean-host verification or close spec §11.6. → H01, F02, F04, F09–F12.
- AC13 Medium/strong primary: no cycle dispatch in autonomous, no flat cycle, no bypass by launching a cheap runner from `architect`; explicit handoff to cheap primary preserving refs. → F02, F04.
- AC14 States separate and durable: collection/preparation/campaign-runtime/step each own files, ids, links; preparation immutable/revisioned with one authoritative pointer; mutation only by executor on explicit dispatch, semantics by primary/driver; resume never repeats an accepted step, never double-credits, never restores a number from memory, never bypasses the barrier. → F05, F06, F10.
- AC15 No recursion: a campaign step is only a family cycle; no campaign-in-campaign, collection-in-campaign, collection-in-collection. → F07, F10.
- AC16 Domain-agnostic: shared composition rules speak of goal, evidence, acceptance criteria, surface, dependencies, resources, pause/stop; no new domain examples/norms; implementation guards present and green. → F01, F04, F05, F10, F12.
- AC17 Asset and docs in sync: six runner copies byte-identical; affected articles in EN and RU including the new `docs/pdca-incremental.md`; README and install docs consistent; routing/guard suites updated and green. → F02, F09, F11, F12, PARITY.
- AC18 Sources cover every item: contracts/tests/docs of §8 reflect each design call; existing guarantees (counters/gates, git model, merge barrier, `incomplete` policy, collection verification) intact; no new statuses or counters. → ALL, SIM, finite scope review.

## Plan revision / counters

- `N` = 1 (cycle number)
- `r` = 2 (plan revision)
- `n` = 1/3 (attempt of revision 2)
- Evidence contract revision: `rv1`

Defect history (D9b closure; `r`/`n` unchanged — a defect fix without a replan is not a new revision):

| key | AC | observed | fix count | evidence | outcome |
|---|---|---|---|---|---|
| G1 | AC06 | D9 (r2, n1) — matrix row GAP, no direct test | 1 (one test method, 3 assertions) | `posthoc-red-g1.log` exit 1 → `do-d9b-pdca-collection.log` exit 0 | **closed** |
| G2 | AC16 | D9 (r2, n1) — matrix row GAP, review-only | 1 (one test method, heading-scoped slices) | `posthoc-red-g2.log` exit 1 → `do-d9b-pdca.log` exit 0 | **closed** |

## Units (sequential, one tree)

| ID | Unit | Deps | State |
|---|---|---|---|
| D0 | Baseline: record HEAD, working-tree status, four suite runs and skips; preserve pre-existing changes | — | done — evidence: `.pdca/pdca-collection-incremental-composition/rv1/baseline.md`; logs: `/tmp/opencode/pdca-collection-incremental-composition/rv1/` |
| D1 | Fact review complete; cold-host prerequisite documented, not established. Evidence: `baseline.md` + `baseline-hostcfg.md`. The deployment prerequisite stays OPEN; dependent units D2–D9 proceed after r2 approval. D1 is done, not blocked or superseded; its completion does not close the prerequisite. | D0 | done |
| D2 | Red guards: extend exactly F01–F12 with positive/negative checks for AC01–AC18 before contract changes; record red evidence | D0, D1 | done — D2a (19 new tests: 11 red / 8 protective-green) and D2b (24 new tests: 24 red) added before any contract change; red-green.md §D2a/§D2b |
| D3 | Contracts: `pdca-entry/SKILL.md` (composition in routing description, `execution_kind` ≠ `selected_variant`, priorities unchanged, no re-routing, medium/strong → cheap primary handoff); `pdca-collection/SKILL.md` (preparation artifact/revisions, barrier, footprint, three operations, state ownership, routing/disposition, surface, fallback, git, recursion ban); `pdca-incremental/SKILL.md` (§Статус-файл кампании, §0. Bootstrap contextual changes) | D1, D2 | done — resumed after restart and audited: all D3 checklist items present, no further edit needed. Entry suite green 28/28 exit 0; no regression (collection 85 ran/4 failures/7 skips, incremental 52/4, pdca 115/13/22 — all remaining failures are D4 runner asset or D6/D7 docs). Evidence: `.pdca/pdca-collection-incremental-composition/rv1/red-green.md` §D3; logs `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d3-resume-*.log` |
| D4 | Runner: canonical `opencode/pdca/assets/agents/pdca-orchestrator.md` in two modes; copy to the five mirrors; parity | D1, D3 | done — canonical 127 lines / 8353 bytes, frontmatter byte-identical; five mirrors `cmp` exit 0. Runner guards green: collection 85/0F/7S exit 0, incremental 52/0F exit 0; pdca 115 ran / 6F / 22S exit 1 with only D6/D7 docs failures left (13F → 6F from D3); no regression (entry 28/0, coder 75/0, dotnet 320/0). Evidence: `.pdca/pdca-collection-incremental-composition/rv1/red-green.md` §D4; logs `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d4-*.log` |
| D5 | Incremental contract: §Роль, RUNNER row, §Автономный режим, and by meaning §Инварианты кампании, §Статус-файл кампании, §0. Bootstrap, §3. Исполнение шага, §5. Решение об остановке | D3, D4 | done — D5 edited §Роль, the `STEP N` row + its permissions bullet, §Инварианты (10/11/12), §3. Исполнение шага, §5. Решение об остановке, §Автономный режим (+46 net lines, no rule removed); §Статус-файл кампании and §0 Bootstrap were already completed in D3 and were not touched. incremental 52/0F exit 0; collection 85/0F/7S exit 0; entry 28/0 exit 0; pdca 115/6F/22S exit 1 with the same 6 D6/D7 docs failures as D4. Evidence: `.pdca/pdca-collection-incremental-composition/rv1/red-green.md` §D5; logs `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d5-*.log` |
| D6 | Capability/install: collection §Fallback, incremental family link, `docs/install.md`, `docs/ru/install.md`, `docs/install-prompt.md`; add "Verification status: unverified" with the open prerequisite and closing trigger; carry the EN/RU limitation wording (new section). Remove bare `>= 2` sufficiency claims; make no claim that 3 suffices. Keep fail-closed behavior; external host configuration remains untouched. Evidence: install §10 preflight/fallback + §11 `Verification status: unverified` (EN/RU), §6 edge budget, prompt checklist items; both install-doc guards green. | D1, D4 | done |
| D7 | Docs: §8.3 pairs, `README.md`, create `docs/pdca-incremental.md`; keep prerequisite status consistent with D6 and spec §11.6 OPEN. Do not present repository verification as clean-host verification. | D3–D6 | done — D7a: `docs/pdca-incremental.md` created (629 lines) and `docs/ru/pdca-incremental.md` (650 lines) with the composition content; heading parity 21/21. D7b: `docs/pdca-collection.md` (278→384) + `docs/ru/pdca-collection.md` (284→387) gained `## 7` composition (units of both kinds, preparation document/`preparation_ref`, baseline bootstrap, readiness ≠ completion, pause ≠ final, disposition + derived lane pause, separate state spaces, surface reservation, collection-lane driver, preflight/fallback); guide pair §2 "neighbour and composition" + §11 composition paragraph (EN family map aligned to RU: five skills, `pdca-incremental` row); `README.md` rows + Usage. Heading parity 14/14 and 39/39. All four suites green: pdca 115/0F/22S exit 0 (the last D7 guard, README containment, now PASS), collection 85/0F/7S exit 0, incremental 52/0F exit 0, entry 28/0F exit 0. Evidence: `.pdca/pdca-collection-incremental-composition/rv1/red-green.md` §D7a/§D7b; logs `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7a-*.log`, `do-d7b-*.log` |
| D8 | Verification: four full suites, SIM, PARITY, host-config matrix (only with an actual authorized path), logs; report the environment variants with skips and without skips separately, including commands, exit codes, results and skip reasons, and report the parity result explicitly. Repository results do not close the cold-host prerequisite. | D2–D7 | done — both environment variants green: unset 280 tests / 0F / 0E / 29S (all 29 = `host config not available — set OPENCODE_CONFIG_REPO=…`; skips not passes), hostcfg 280 / 0F / 0E / 0S; SIM exit 0 both ways (hostcfg prints the non-failing notice `SKIP: …/config/agents/lane.md not installed`); PARITY canonical + 5 mirrors all 8353 bytes, `cmp` 5/5 identical, 0 drift; domain non-regression coder 75/0/1S, dotnet 320/0/29S (= D4 counts; 0S with hostcfg); scope 30 `M` + 7 `??`, 0 out of scope, `git diff --check` exit 0; 18 protected paths unchanged; wsl-notify artifacts untouched; HEAD `dd661e7`, no commit/push. Cold-host prerequisite stays OPEN. Evidence: `.pdca/pdca-collection-incremental-composition/rv1/verification.md`; logs `/tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-*.log` |
| D9 | Final review/traceability: AC01–AC18 matrix with actual locations and test ids; scope review; handoff. Mark AC12 "satisfied as documentation of the prerequisite", retain spec §11.6 OPEN, and carry the final EN/RU limitation wording. Explicitly state that green repository tests do not verify a clean-host installation. | D8 | **done** — **18/18 PASS, 0 GAPs**. D9b closed both defects with one post-hoc test each in the existing suites: G1 AC06 → `StepPlanApprovalContractTest.test_normal_mode_step_plan_approval_is_durable_and_pauses_the_unit` (`opencode/pdca-collection/tests/test_plan_barrier.py`; 3 assertions: normal mode + durable pending approval ref, `disposition=paused`, `Бриф шага PLAN не подменяет`); G2 AC16 → `CompositionDomainNeutralityTest.test_composition_sections_use_neutral_vocabulary_and_no_domain_examples` (`opencode/pdca/tests/test_docs_sources.py`; composition-heading slices only, ≥3 RU and ≥3 EN neutral stems, zero of {`.NET`,`dotnet`,`performance`,`coverage`,`NuGet`,`ASP.NET`}, missing heading = named failure). Post-hoc red against the `HEAD` blobs: G1 3/3 FAIL exit 1 (`posthoc-red-g1.log`), G2 exit 1 (`posthoc-red-g2.log`). Reruns green (variant B): pdca 116/0F/0E/0S exit 0, pdca-collection 86/0F/0E/0S exit 0; variant A same with 22/7 skips, no new skip. AC12 remains documentation of the OPEN cold-host prerequisite (H01 absent, spec §11.6 OPEN); green repository tests do not verify a clean-host installation. Scope unchanged at D9b (both edited test files are inside §8.2; baselines/logs in `/tmp`): 30 `M` + 9 `??`, 0 out of scope, 18/18 protected paths unchanged, wsl-notify untouched, HEAD `dd661e7`, no commit/push. Evidence: `.pdca/pdca-collection-incremental-composition/rv1/traceability.md`, `red-green.md` §D9b; logs `do-d9b-*.log`, `posthoc-red-g1.log`, `posthoc-red-g2.log`, `do-d9-scope.log`, `do-d9-protected.log` |

A unit without a meaningful result is not marked `done`; `done` only at the DO → CHECK gate with recorded evidence.

## Means and access

- Roles: planner (decisions), scout (read-only facts), executor (writes/commands), check (verdict), escalate (decision only).
- Tests: `python3 -m unittest discover -s opencode/<skill>/tests -p 'test_*.py' -v`; SIM: `bash opencode/pdca-collection/tests/git-model-sim.sh`; PARITY: `cmp` of the canonical runner against the five mirrors.
- Logs: `/tmp/opencode/pdca-collection-incremental-composition/rv1/<phase>-<invocation>.log`; every run reports exit code, counts and log path; a skip is never a pass.
- No network; no repository writes beyond the working tree edits and the administrative `.pdca/` artifacts.

## Risks / stop conditions

- Cold-host verification remains an OPEN deployment prerequisite recorded in the new section and does not block D2–D9 under r2; no numbers are invented and no numeric sufficiency claim is made. If the user or spec requires recorded clean-host evidence before the diff is accepted, work stops and returns to PLAN/escalate.
- Design divergence or scope expansion → stop affected work, return to planner.
- Foreign change overlaps a required edit → preserve and request a targeted decision.
- Guard fails for wording, not behavior → improve the guard without weakening its AC; keep the red evidence.
- Pre-existing baseline failures → distinguish from regressions; never count as pass.
- Permission/allowlist drift, protected-file edits, unrelated `.pdca` changes → reject the candidate and revert only this cycle's unauthorized delta.

## Decisions

- Adopt the approved implementation plan's 0→9 decomposition, red-first rule and single implementation thread.
- Deviation 1: add the mandatory `opencode/pdca-entry/SKILL.md` edit to D3 (spec §8.1; the approved plan omitted it).
- Deviation 2: exclude `docs/pdca.md`/`docs/ru/pdca.md` (not in §8.3; §9.18 requires the listed sources only).
- Deviation 3: per the escalation decision, cold-host verification remains an OPEN deployment prerequisite recorded in the new section; D1 is done, and this item does not block D2–D9 under r2. Unproven host facts stay unproven, and no numeric sufficiency claim is made.
- `.pdca/status/wsl-notify-session-filter-1.md` and `.pdca/wsl-notify-session-filter/` are out of scope and untouched.
- No commits, no pushes.

### What changed in r2

- Reclassified cold-host verification as an OPEN deployment prerequisite, not a repository implementation blocker; D1 is done for documenting it, and D2–D9 proceed after approval.
- Updated the host facts: V2 source establishes edge-based depth semantics; the installed host build version remains unverified. No numeric sufficiency claim is made.
- Amended D6/D7 documentation obligations, AC12's prerequisite disposition, and D8/D9 reporting obligations; spec §11.6 remains OPEN.
- Advanced the plan to r2 with iteration 1/3 and pending normal-mode user re-approval.

## Open deployment prerequisite — cold host

**Status: OPEN — prerequisite documented, not established.**

D1's fact review and prerequisite documentation are complete, supported by `baseline.md` and `baseline-hostcfg.md`. This does not complete cold-host verification. D2–D9 remain active under their existing acceptance criteria and dependencies and may proceed after r2 approval. No unit is superseded.

### Unverified scope and observed host facts

- Clean-host installation and execution of `primary → driver → roles`, including a real delegation reaching `escalate → scout`, have not been verified.
- The inspected installed `pdca-orchestrator` omits permission to delegate to `pdca-scout`; the repository's canonical asset includes it. This is an observed installed/canonical drift, not proof of effective cold-host permissions.
- The inspected profiles set `experimental.subagent_depth: 3`.
- Authoritative V2 source in `/home/alex/sources/opencode`, version 2.0.32, defines `experimental.subagent_depth` as the maximum subagent nesting depth, defaulting to 1 (`packages/schema/src/config/experimental.ts:11-13`). Enforcement follows the calling session's `parentID` chain and permits spawning when `depth < limit` (`packages/core/src/tool/plugin/subagent.ts:117-133`). This counts session-nesting edges below the primary, not agents.
- The required graph is `primary(0) → driver(1) → escalate(2) → scout(3)`. The source semantics are established, but the installed host build version is not verified. The inspected V1 1.18.x SDK uses a deprecated top-level key that V2 ignores; that SDK observation does not establish the running host's version. The experimental setting is effective only on a V2 build and must be verified by the operator. No numeric sufficiency claim is made.
- No host-side parallel-cap key, schema entry or constant was found in the inspected V2 source. This is a source observation, not evidence of unlimited host concurrency.
- External host configuration has not been modified in this cycle.

### Why this remains open

Repository inspection and repository tests cannot establish a clean-host installation, the running host's version, effective installed permissions, or successful execution of the required delegation chain. No verified clean-host execution is available in this cycle. Green repository tests do not substitute for that evidence.

### Closing trigger and owner

The operator must perform an authorized clean-host installation and execution, recording:

- the actual host build/version and execution date;
- availability of all six required roles;
- the collection-lane mode and observed fallback behavior;
- a real delegation chain reaching `escalate → scout`;
- execution results and supporting logs.

A separate follow-up cycle must evaluate that evidence and record the result in the install documentation. Only that follow-up cycle may change this prerequisite's status from OPEN. D1 completion, repository test success, or reporting alone must not close it.

### Documentation and dependent evidence obligations

- D6 adds a section titled `Verification status: unverified` to the install documentation, with this status and closing trigger. D6/D7 retain fail-closed requirements, remove bare `>= 2` sufficiency claims, make no claim that 3 suffices, and leave external host configuration untouched.
- D8 reports the with-skips and without-skips environment variants separately. Each report retains its required invocation, exit-code/result/log evidence and skip explanations; success in a skipped variant must not be presented as a successful no-skips run. Report the parity result explicitly. All four full suites, SIM, PARITY and the authorized-path restriction on the host-config matrix remain required as already specified.
- D9 records AC12 as "satisfied as documentation of the prerequisite", not as verified host execution; spec §11.6 remains OPEN. The final handoff includes the EN/RU limitation wording below and states that green repository tests do not verify a clean-host installation.
- Evidence contract `rv1` remains unchanged. Existing stable requirement/row IDs, required checks and scenarios, evidence kinds and sources, exact invocations, exit-code/result/log requirements, artifact expectations, owner streams, observable applicability predicates, priorities, and the finite CHECK re-gather budget and owner remain binding. No existing obligation is removed or weakened, no future test symbol or source location is fabricated, and planned evidence remains labelled planned. Missing reporting alone does not justify another contract revision or DO iteration.

### Final English wording — documentation and handoff

> **Host verification limitations.** The inspected installed `pdca-orchestrator` does not allow delegation to `pdca-scout`; the repository's canonical asset does. Refresh the installed runner from the canonical asset and verify its effective permissions before relying on that delegation path. This cycle has not modified the external host configuration.
>
> The inspected profiles configure `experimental.subagent_depth: 3`. Authoritative V2 2.0.32 source defines depth as session-nesting edges below the primary and permits a spawn when the calling session's depth is less than the configured limit. The required chain `primary → driver → escalate → scout` reaches depth 3. However, the installed host build version has not been verified. The experimental setting is effective only on a V2 build and must be verified by the operator; the inspected V1 SDK uses a deprecated top-level key that V2 ignores. The configured value alone does not establish support on the installed host. No numeric sufficiency claim is made.
>
> No host-side parallel-cap key, schema entry or constant was found in the inspected V2 source. This does not establish unlimited host concurrency.
>
> Cold-host installation and execution of `primary → driver → roles`, including `escalate → scout`, have not been verified. Green repository tests do not verify a clean-host installation. The cold-host prerequisite remains OPEN and does not block repository implementation under r2. To close it, the operator must perform an authorized clean-host run recording the host version and date, all six roles' availability, collection-lane mode and fallback, and a real chain reaching `escalate → scout`, with results and logs. A separate follow-up cycle must record the result in the install documentation; only that follow-up may close the prerequisite.

### Итоговая русская формулировка — документация и передача результата

> **Ограничения проверки хоста.** В проверенной установленной копии `pdca-orchestrator` отсутствует разрешение на делегирование `pdca-scout`; в каноническом файле репозитория оно есть. Перед использованием этого пути обновите установленный runner из канонического файла и проверьте действующие разрешения. Внешняя конфигурация хоста в этом цикле не изменялась.
>
> В проверенных профилях задано `experimental.subagent_depth: 3`. Авторитетный исходный код V2 2.0.32 определяет глубину как число рёбер вложенности сессий ниже основной сессии и разрешает создание дочерней сессии, когда глубина вызывающей сессии меньше настроенного предела. Требуемая цепочка `primary → driver → escalate → scout` достигает глубины 3. Однако версия установленной сборки хоста не проверена. Настройка в секции `experimental` действует только в сборке V2 и должна быть проверена оператором; в проверенном SDK V1 используется устаревший ключ верхнего уровня, который V2 игнорирует. Само настроенное значение не подтверждает поддержку цепочки на установленном хосте. Утверждение о достаточности числового значения не делается.
>
> В проверенном исходном коде V2 не найдены ключ, элемент схемы или константа ограничения параллелизма хоста. Это не доказывает неограниченную конкурентность хоста.
>
> Установка и выполнение на чистом хосте цепочки `primary → driver → roles`, включая `escalate → scout`, не проверены. Успешные тесты репозитория не подтверждают установку на чистом хосте. Prerequisite остаётся OPEN и в r2 не блокирует реализацию в репозитории. Для его закрытия оператор должен выполнить разрешённый запуск на чистом хосте, зафиксировав версию хоста и дату, доступность всех шести ролей, режим collection-lane и fallback, а также реальную цепочку, достигающую `escalate → scout`, с результатами и журналами. Отдельный последующий цикл должен записать результат в документацию по установке; только этот цикл может закрыть prerequisite.

## Evidence contract rv1 (summary)

Every AC row records: row id, revision `rv1`, applicability predicate, positive and negative scenario, expected evidence kind and source, exact invocation, exit code and counts, log path, artifacts (`red-green.md`, `traceability.md`, `verification.md`; AC12 also `host-evidence.md`), owner stream. Test aliases: F01 `pdca/test_orchestrator_variant_routing.py`, F02 `pdca/test_routing_consistency.py`, F03 `pdca/test_permission_boundaries.py`, F04 `pdca-entry/test_contract.py`, F05 `pdca-collection/test_plan_barrier.py`, F06 `pdca-collection/test_verification_recovery.py`, F07 `pdca-collection/test_routing_guard.py`, F08 `pdca-collection/test_git_model.py`, F09 `pdca-collection/test_orchestrator_asset.py`, F10 `pdca-incremental/test_contract.py`, F11 `pdca-incremental/test_orchestrator_asset.py`, F12 `pdca/test_docs_sources.py`. CHECK re-gather budget: two evidence-only rounds; a revision must state "rvN supersedes rvN−1" and keep the row ids.

## Done / Verified

Implementation under r2 is complete and this cycle is closed as **met**: CHECK verdict `met`, AC01–AC18 all
met (18/18, 0 GAPs), findings minor/nit only, routing none. Decisive pointer: `traceability.md` §6
("18/18 PASS — 0 GAPs", G1 AC06 and G2 AC16 closed at D9b) and the `verification.md` matrix (§1–§5).

- Units D0–D9 all `done`; D2 closed with D2a/D2b red evidence recorded before any contract change
  (`red-green.md` §D2a/§D2b), D9b closed the two post-hoc gaps with baseline-red → green tests.
- Variant B (`OPENCODE_CONFIG_REPO` set): **282 tests / 0 failures / 0 errors / 0 skipped**, all four
  suites exit 0 (pdca 116, pdca-entry 28, pdca-collection 86, pdca-incremental 52).
- Variant A (unset): **280 ran / 0 failures / 0 errors / 29 skips** (22 `pdca` + 7 `pdca-collection`;
  282 collected − 29 skipped), all four suites exit 0. Skips are **not** passes — each is a host-gated
  check that executed green only in variant B.
- SIM (`git-model-sim.sh`): exit 0 in both variants.
- PARITY: **6/6** runner files, **8353 bytes each**, `cmp` 5/5 identical, 0 drift.
- Scope: **31 §8 files** changed, **0 out of scope**; 18 protected paths unchanged; foreign
  `wsl-notify` artifacts untouched; `git diff --check` exit 0; `HEAD` still `dd661e7`.
- No commits and no pushes were made in this cycle.

## Known limitations

**Open deployment prerequisite — cold host (status: OPEN).** Repository evidence does not close it; the
EN limitation block recorded above applies verbatim:

> **Host verification limitations.** The inspected installed `pdca-orchestrator` does not allow delegation to `pdca-scout`; the repository's canonical asset does. Refresh the installed runner from the canonical asset and verify its effective permissions before relying on that delegation path. This cycle has not modified the external host configuration.
>
> The inspected profiles configure `experimental.subagent_depth: 3`. Authoritative V2 2.0.32 source defines depth as session-nesting edges below the primary and permits a spawn when the calling session's depth is less than the configured limit. The required chain `primary → driver → escalate → scout` reaches depth 3. However, the installed host build version has not been verified. The experimental setting is effective only on a V2 build and must be verified by the operator; the inspected V1 SDK uses a deprecated top-level key that V2 ignores. The configured value alone does not establish support on the installed host. No numeric sufficiency claim is made.
>
> No host-side parallel-cap key, schema entry or constant was found in the inspected V2 source. This does not establish unlimited host concurrency.
>
> Cold-host installation and execution of `primary → driver → roles`, including `escalate → scout`, have not been verified. Green repository tests do not verify a clean-host installation. The cold-host prerequisite remains OPEN and does not block repository implementation under r2. To close it, the operator must perform an authorized clean-host run recording the host version and date, all six roles' availability, collection-lane mode and fallback, and a real chain reaching `escalate → scout`, with results and logs. A separate follow-up cycle must record the result in the install documentation; only that follow-up may close the prerequisite.

- **Installed runner drift:** the installed `pdca-orchestrator` allowlist lacks `pdca-scout`, while the
  canonical asset (and its five mirrors) includes it. The installed copy must be refreshed from the
  canonical asset and its effective permissions re-checked before that delegation path is relied on.
- **Installed host build version unverified:** the depth semantics above are source-established for V2
  2.0.32 only; whether the running host is such a build was not verified, so the `3` in the profiles is
  not evidence of support.
- **No host concurrency cap established:** no parallel-cap key, schema entry or constant exists in the
  inspected source — absence of a cap is not a cap value.
- **29 host-gated skips without `OPENCODE_CONFIG_REPO`:** variant A leaves 29 checks unexecuted (22 `pdca`
  + 7 `pdca-collection`); they support no claim and were verified only in variant B.

## Next plan

A single follow-up cycle: cold-host verification — operator clean-host run, result recorded in
`docs/install.md` §11 / `docs/ru/install.md` §11; only that cycle closes the OPEN prerequisite. No further
implementation work is planned.

## Changed artefacts

- Contracts (3): `opencode/pdca-entry/SKILL.md`, `opencode/pdca-collection/SKILL.md`,
  `opencode/pdca-incremental/SKILL.md`.
- Runner: canonical `opencode/pdca/assets/agents/pdca-orchestrator.md` (two modes) + **5 byte-identical
  mirrors** (`pdca-entry`, `pdca-coder`, `pdca-dotnet`, `pdca-collection`, `pdca-incremental`), all 8353
  bytes, `cmp` identical.
- Guard suites (12 extended, no new suite): F01–F12 under `opencode/pdca/tests/`,
  `opencode/pdca-entry/tests/`, `opencode/pdca-collection/tests/`, `opencode/pdca-incremental/tests/`.
- Docs: collection pair (`docs/pdca-collection.md`, `docs/ru/pdca-collection.md`, §7 composition);
  incremental pair (new `docs/pdca-incremental.md` + `docs/ru/pdca-incremental.md`); guide pair
  (`docs/pdca.md` family map/§11 as scoped by D7); `README.md`; install pair
  (`docs/install.md`, `docs/ru/install.md` §10/§11); `docs/install-prompt.md`.
- Administrative `.pdca` artifacts: this status file and
  `.pdca/pdca-collection-incremental-composition/rv1/` (`baseline.md`, `baseline-hostcfg.md`,
  `red-green.md`, `traceability.md`, `verification.md`); raw logs in `/tmp/opencode/`.
- No commits, no pushes, no branch/worktree operations.

## Pointers

- `.pdca/pdca-collection-incremental-composition/rv1/traceability.md` — AC01–AC18 matrix, 18/18, defect history.
- `.pdca/pdca-collection-incremental-composition/rv1/verification.md` — suite/SIM/PARITY/scope matrix, skip accounting.
- `.pdca/pdca-collection-incremental-composition/rv1/red-green.md` — red-first evidence per unit, §D2a–§D9b.
- `.pdca/pdca-collection-incremental-composition/rv1/baseline.md` — pre-change baseline (HEAD, tree, four suites).
- `.pdca/pdca-collection-incremental-composition/rv1/baseline-hostcfg.md` — with-host-config baseline.
- `/tmp/opencode/pdca-collection-incremental-composition/rv1/` — raw invocation logs (DO, SIM, PARITY, post-hoc red).

## Progress log

2026-10-20T06:31:35Z | PLAN | revision r1 | iteration 1/3 | PLAN ready — awaiting user approval | `.pdca/status/pdca-collection-incremental-composition-1.md`
2026-10-20T06:47:23Z | DO | revision r1 | iteration 1/3 | plan approved — DO started | .pdca/status/pdca-collection-incremental-composition-1.md
2026-10-20T06:48:01Z | DO | revision r1 | iteration 1/3 | D0 baseline closed — baseline green (237 tests, 0 failures, 0 errors, 29 host-gated skips) | .pdca/pdca-collection-incremental-composition/rv1/baseline.md
2026-10-20T06:52:11Z | DO | revision r1 | iteration 1/3 | D1 with-config baseline recorded | .pdca/pdca-collection-incremental-composition/rv1/baseline-hostcfg.md
2026-10-20T07:03:04Z | PLAN | revision r2 | iteration 1/3 | Replanned: cold-host reclassified as open deployment prerequisite (r 1→2, iteration 1/3) | escalation decision
2026-10-20T08:10:21Z | DO | revision r2 | iteration 1/3 | plan approved — DO started (r2) | .pdca/status/pdca-collection-incremental-composition-1.md
2026-10-20T08:15:49Z | DO | revision r2 | iteration 1/3 | D2a red guards added and red confirmed (19 new tests: 11 red / 8 protective-green; failures are assertion failures only, no errors; pdca 115 tests exit 1, pdca-entry 28 tests exit 1) | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d2a-red-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d2a-red-pdca-entry.log, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T08:24:33Z | DO | revision r2 | iteration 1/3 | D2b red guards added and red confirmed (24 new tests: 24 red, 0 pre-existing failures, 0 errors; pdca-collection 85 tests exit 1, pdca-incremental 52 tests exit 1; D2 stays running) | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d2b-red-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d2b-red-pdca-incremental.log, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T08:38:56Z | DO | revision r2 | iteration 1/3 | D3 contracts complete (resumed after server restart; audit found no missing checklist item, no further edit needed; entry 28 tests/0 failures exit 0; collection 85/4F/7S exit 1; incremental 52/4F exit 1; pdca 115/13F/22S exit 1; remaining failures only D4 runner asset and D6/D7 docs; no regression vs D2) | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d3-resume-pdca-entry.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d3-resume-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d3-resume-pdca-incremental.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d3-resume-pdca.log, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T08:44:40Z | DO | revision r2 | iteration 1/3 | D4 runner asset complete (canonical 127 lines/8353 bytes in two modes; five mirrors cmp exit 0; collection 85/0F/7S exit 0; incremental 52/0F exit 0; pdca 115/6F/22S exit 1 — remaining failures only D6/D7 docs; entry 28/0, coder 75/0, dotnet 320/0; no regression) | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d4-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d4-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d4-pdca-incremental.log, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T09:04:12Z | DO | revision r2 | iteration 1/3 | D5 incremental contract complete (contextual edits in §Роль, STEP N row, §Инварианты 10/11/12, §3, §5, §Автономный режим; +46 net lines, no rule removed; §Статус-файл/§0 Bootstrap untouched — D3 scope; incremental 52/0F exit 0; collection 85/0F/7S exit 0; entry 28/0 exit 0; pdca 115/6F/22S exit 1 — same D6/D7 docs failures only; no regression) | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d5-pdca-incremental.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d5-pdca-collection.log, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T09:05:30Z | DO | revision r2 | iteration 1/3 | D6 capability/install docs complete (install §10 Preflight and fallback + §11 Verification status: unverified in EN/RU, §6 edge budget in EN/RU, prompt checklist items; bare depth-sufficiency claims removed at install.md:285/299, ru/install.md:243-244/258, install-prompt.md:101/132; collection §Fallback + incremental §Связь с семейством extended, no restructure; pdca 115/2F/22S exit 1 — only D7 guards red, install-doc guards green; collection 85/0F/7S exit 0; incremental 52/0F exit 0; entry 28/0F exit 0; grep `[>≥]=?\s*2` in three install files = 0; external host config untouched; cold-host prerequisite stays OPEN) | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d6-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d6-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d6-pdca-incremental.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d6-pdca-entry.log, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T09:09:41Z | DO | revision r2 | iteration 1/3 | D7a done (not D7): new `docs/pdca-incremental.md` 629 lines + `docs/ru/pdca-incremental.md` 650 lines with composition (campaign as collection unit, two execution models, step variant/dispatch policy, preparation_ref, readiness≠completion, pause≠final, disposition, commit policy, recursion ban); heading parity 21/21; pdca 115/1F/22S exit 1 (README guard only), incremental 52/0F exit 0, collection 85/0F/7S exit 0, entry 28/0F exit 0; D7 stays running for D7b | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7a-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7a-pdca-incremental.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7a-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7a-pdca-entry.log, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T09:26:40Z | DO | revision r2 | iteration 1/3 | D7 complete (D7a+D7b): collection EN/RU §7 composition (two execution kinds, preparation document/preparation_ref + campaign_ref, baseline bootstrap, readiness≠completion, pause≠final, per-unit disposition + derived lane pause, separate state spaces, surface reservation, collection-lane driver, preflight/fallback), guide EN/RU §2 neighbour/composition + §11 composition (EN family map aligned to RU), README rows + Usage; heading parity 14/14 and 39/39; pdca 115/0F/22S exit 0, collection 85/0F/7S exit 0, incremental 52/0F exit 0, entry 28/0F exit 0 — every guard green | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7b-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7b-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7b-pdca-incremental.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d7b-pdca-entry.log, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T09:22:31Z | DO | revision r2 | iteration 1/3 | D8 verification complete — all required invocations green (A unset: pdca 115/22S, entry 28/0S, collection 85/7S, incremental 52/0S = 280 tests 0F/0E/29S exit 0 ×4; B hostcfg: same 280 tests 0F/0E/0S exit 0 ×4; SIM exit 0 both variants, hostcfg notice `SKIP: …/config/agents/lane.md not installed`; PARITY 6 files 8353 bytes each, cmp 5/5 identical, 0 drift; domain coder 75/1S, dotnet 320/29S = pre-change counts, 0S with hostcfg; scope 30 M + 7 ??, 0 out of scope, diff --check exit 0; 18 protected paths unchanged; wsl-notify artifacts untouched; no commit/push). Skips are not passes — the 29 gate on OPENCODE_CONFIG_REPO and all execute green in variant B. Cold-host prerequisite remains OPEN and carries to D9. | /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-nohost-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-nohost-pdca-entry.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-nohost-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-nohost-pdca-incremental.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-hostcfg-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-hostcfg-pdca-entry.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-hostcfg-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-hostcfg-pdca-incremental.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-sim-nohost.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-sim-hostcfg.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-parity.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-nonreg-pdca-coder.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-nonreg-pdca-dotnet.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-scope.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d8-protected.log, .pdca/pdca-collection-incremental-composition/rv1/verification.md, .pdca/pdca-collection-incremental-composition/rv1/red-green.md
2026-10-20T09:33:05Z | DO | revision r2 | iteration 1/3 | D9 final review/traceability: 18-row AC matrix built from actual files and test methods — **16/18 PASS, 2 GAPs** (G1 AC06 medium: no test for the normal-mode step-PLAN approval rule — durable pending approval ref + `disposition=paused` + brief ≠ PLAN; G2 AC16 low: no automated domain-agnostic guard for the new composition sections). D9 stays running. Scope clean: 30 M + 9 ??, §8 31 / `.pdca` 6 / inputs 2, 0 out of scope, 18/18 protected paths unchanged, wsl-notify untouched, HEAD dd661e7, no commit/push. Final confirmation suites (variant B): 280 tests / 0F / 0E / 0S, four exit 0. AC12 recorded as documentation of the OPEN cold-host prerequisite (H01 absent, spec §11.6 OPEN); skips in variant A (29) are not passes. | .pdca/pdca-collection-incremental-composition/rv1/traceability.md, .pdca/pdca-collection-incremental-composition/rv1/red-green.md §D9, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d9-confirm-pdca.log, do-d9-confirm-pdca-entry.log, do-d9-confirm-pdca-collection.log, do-d9-confirm-pdca-incremental.log, do-d9-scope.log, do-d9-protected.log
2026-10-20T09:52:00Z | DO | revision r2 | iteration 1/3 | D9b gap closure — G1 (AC06) and G2 (AC16) closed with one post-hoc test each in the existing suites: `StepPlanApprovalContractTest.test_normal_mode_step_plan_approval_is_durable_and_pauses_the_unit` (test_plan_barrier.py; durable pending approval ref + `disposition=paused` + `Бриф шага PLAN не подменяет`) and `CompositionDomainNeutralityTest.test_composition_sections_use_neutral_vocabulary_and_no_domain_examples` (test_docs_sources.py; composition-heading slices, ≥3 RU / ≥3 EN neutral stems, 0 domain tokens, missing heading = named failure). Post-hoc red vs `HEAD` baselines: G1 3/3 FAIL exit 1, G2 exit 1. Reruns green variant B — pdca 116/0F/0E/0S exit 0, pdca-collection 86/0F/0E/0S exit 0; variant A same with 22/7 skips (no new skip). Traceability now **18/18 PASS**, D9 `done`; r=2, n=1/3 unchanged (defect fix, not a replan); AC12 stays documentation of the OPEN cold-host prerequisite; no commit/push, HEAD dd661e7. | .pdca/pdca-collection-incremental-composition/rv1/traceability.md, .pdca/pdca-collection-incremental-composition/rv1/red-green.md §D9b, /tmp/opencode/pdca-collection-incremental-composition/rv1/posthoc-red-g1.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/posthoc-red-g2.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d9b-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d9b-pdca-collection.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d9b-nohost-pdca.log, /tmp/opencode/pdca-collection-incremental-composition/rv1/do-d9b-nohost-pdca-collection.log
2026-10-20T09:43:46Z | ACT | revision r2 | iteration 1/3 | ACT closed — CHECK met 18/18; status finalized and kept; no commits | traceability.md / verification.md
2026-10-20T09:45:04Z | ACT | revision r2 | iteration 1/3 | Notice: the D9b line above carries an annotation ahead of the real clock (09:52:00Z vs 2026-10-20T09:45:04Z); append-only preserved, no line rewritten | status file
