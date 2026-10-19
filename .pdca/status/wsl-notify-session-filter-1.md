# PDCA status — wsl-notify-session-filter (cycle 1)

- Task: Add an `excludeSessionTitles` option to the wsl-notify plugin so that complete and error notifications for matching sessions are suppressed, without changing any other behaviour or limits; r2 additionally adds an environment variable and restores V1 option forwarding for compatibility.
- Workspace root: `/home/alex/sources/skills`
- Status file: `.pdca/status/wsl-notify-session-filter-1.md`
- Evidence dir: `.pdca/wsl-notify-session-filter/rv2/`
- Mode: normal (user approval required at PLAN → DO)

## Current state

- Phase: ACT closed — cycle complete (accepted by CHECK, revision r2)
- Active units: none (U1–U4 done, all accepted); C: closed (pass); A: closed
- Cycle N = 1, Plan revision r = 2, Attempt n = 1 (accepted on first attempt)

## Durable state

- Current cycle N: 1
- Plan revision r: 2
- Attempt n: 1
- Defect history: (empty — no defects observed; r2 CHECK reported 0 implementation defects and 0 plan defects, 2 non-blocking test-hygiene observations recorded under Risks / known issues)

## Plan revision r1 (superseded by r2)

## 1. Goal and expected result

The user can configure exclusion of sessions from **complete and error** notifications. All other notifications and existing limits keep working unchanged.

### Proposed contract — explicit assumption

"Session filter" is interpreted as a **list of literal substrings of the session title**: the title is already available to the plugin, unlike the unverified agent/model/tags fields.

This is a product assumption, not an established user requirement. In interactive mode it is part of the plan to be approved.

- Option: **`excludeSessionTitles`**.
- Valid value: array of strings; default `[]`.
- Non-empty strings match the title by **case-sensitive literal substring**.
- Multiple strings are combined with **OR**.
- Whitespace is significant; no trimming, regex, glob or special characters.
- Empty strings and non-string elements are ignored. A non-array value means `[]` — no exception, no suppression.
- Missing title or non-string title — the filter does not match.
- Matching only against the real title from the existing cache, **not** the display fallback `"opencode"`, ID, parentID or error text.
- No new environment variables.
- **V1:** no options channel; behaviour unchanged, the setting is available only through the existing V2 options channel.

## 2. Constraints and rationale

- Plain ESM only, no dependencies, no build, no new configuration subsystem.
- Reuse `DEFAULTS`, `limits()` normalization, the existing cache and the smoke harness.
- Change scope: `index.js`, `test/smoke.mjs`, `README.md` inside `opencode/plugins/wsl-notify/`.
- Do not change public entry points, the package version or event-format support unnecessarily.
- Do not add loading of unknown host fields or extra metadata requests.
- No commit/push. Do not touch other repositories.
- Cycle status/evidence files are written by the executor per the cycle contract.

Rationale: `index.js:25-45,378-392` — settings; `:475-521` — titles and cache population; `:579-621` — handler; `:628,666-677` — V2/V1 difference.

## 3. What the request did not state

| Gap | Closure |
|---|---|
| Which session attribute selects sessions? | **Assumption:** the title — the existing available field. |
| How is the filter matched? | **Assumption:** literal case-sensitive substrings, OR. |
| Suppress permission/question/form too? | **Request boundary:** no, only complete/error. |
| How to handle a malformed setting? | **Decision:** ignore invalid values; never lose notifications because of a config error. |
| What if there is no title? | **Decision:** do not suppress; do not use an invented value. |
| What after a rename? | Use the current cache on the next event; existing updates — `index.js:480-521`. |
| V1 setting or env needed? | **Minimal-scope assumption:** no; the V1 limitation is documented. |
| Do directory/agent/tags and the `data.info` shape exist? | Unverified and not needed for the chosen solution. Extended support is out of scope. |

## 4. Minimal solution and alternatives

| Approach | Pros | Cons / cost / risk |
|---|---|---|
| **Title substrings — chosen** | Uses existing data; simple contract and implementation | Title instability; too broad a substring may exclude extra sessions. Low cost. |
| Title regex | Flexible conditions, anchors, alternation | Expression errors, harder diagnosis, risk of expensive matching. Medium cost. |
| Exact session IDs | Unambiguous match | IDs must be obtained in advance; inconvenient for new sessions. Low cost, weak practical use. |

**Recommendation:** the first option. Do not add a general filter language up front.

Implementation:

1. Add the default and defensive normalization of `excludeSessionTitles` at the existing settings points.
2. In `handle()` after `classify()` add the check **for complete/error only**, next to the existing subagent filter.
3. On a match, finish processing **before `render`, dedupe and `schedule`**. Existing `track`, `forget`, `primeUnknown` must run as before.
4. Do not change existing limits: no match does not guarantee a notification if another rule suppresses it.
5. Add tests and documentation in the existing style.

## 5. Acceptance criteria and evidence

Commands are run by the executor from the workspace; defined here only.

**T — the whole smoke suite:**
```sh
cd /home/alex/sources/skills/opencode/plugins/wsl-notify && npm test
```

**D — change and documentation inspection:**
```sh
cd /home/alex/sources/skills && git diff --check -- opencode/plugins/wsl-notify/index.js opencode/plugins/wsl-notify/test/smoke.mjs opencode/plugins/wsl-notify/README.md
```
```sh
cd /home/alex/sources/skills && git diff -- opencode/plugins/wsl-notify/index.js opencode/plugins/wsl-notify/test/smoke.mjs opencode/plugins/wsl-notify/README.md
```

For behavioural checks use the fake PowerShell and assertions on recorded toasts/argv, isolating existing timers and limits via the harness.

| ID | Criterion | Verification and negative case |
|---|---|---|
| AC1 | A matched title suppresses both complete events and both error events from the existing sets. | **T:** separate isolated scenarios for the four events. Negative case: a non-matching title under the same conditions yields the expected notification. |
| AC2 | Matching is a literal case-sensitive substring; several values work as OR. | **T:** second element matches, and a partial title matches. Negative cases: different case; `*` and a regex-like string get no special meaning. |
| AC3 | A missing option and `[]` keep prior behaviour; malformed config does not throw. | **T:** missing option, `[]`, string instead of array, object, number, `null`; a mixed array keeps only valid elements. Negative case: `[""]` does not suppress all sessions. |
| AC4 | The current known title is used, without substituting ID or a fallback. | **T:** title from a session event and from existing `session.get`; a rename changes the subsequent decision. Negative cases: an unknown title and a match only against the ID are not suppressed; the filter `"opencode"` does not match a missing title. |
| AC5 | Permission, question and form are not suppressed by the new setting; existing limits are preserved. | **T:** events with a matching title take the prior path; the whole old smoke suite is green. Negative case: a non-matching filter does not bypass the subagent-completion ban or another existing limit. |
| AC6 | An excluded event does not consume the dedupe key. | **T:** first suppress an event, rename the session to a non-matching value, repeat the event with the same key inside the dedupe window — the notification appears. Negative case: an ordinary sent duplicate is still suppressed. |
| AC7 | V1 behaves as before; the documentation accurately describes availability and the contract. | **T:** V1 without options keeps sending the prior notifications. **D:** manual check of README against AC1–AC6 and the normalizer. Negative case: the docs do not promise a V1 setting, env, regex or permission/question/form filtering. |

A successful `git diff --check` confirms only that there are no formatting errors, not that the contract is correct. AC7 also requires a substantive diff review.

## 6. Decomposition and order

**Do not split into several active units:** this is one small atomic change to one plugin; setting, tests or docs delivered separately do not give a completed result.

| ID | Priority | Expected result | Dependencies | Owner |
|---|---|---|---|---|
| U1 | P0 | The setting with the described behaviour, regression tests and documentation; AC1–AC7 met | None | `pdca-executor` / coder |

Order inside U1:

1. Record the baseline result **T**.
2. Add the check scenarios and the normalization/branch implementation.
3. Update the options example, the table and the filtering/V1 prose in README.
4. Run **T**, **D**, store the results and test pointers in `.pdca/wsl-notify-session-filter/rv1/`.
5. Hand the criteria and evidence to the independent CHECK.

## 7. Means and access

The executor needs read/write on the named files, Node/npm for the existing test and read-only Git inspection. Real Windows/PowerShell, network, dependency installation and access to OpenCode sources are not needed for this plan.

The planner reads nothing, runs nothing and changes nothing.

## 8. Risks and stop conditions

- **Semantic risk:** the user may have wanted regex, IDs or another field. Deviating from the chosen contract requires a real replan, not a hidden scope extension.
- **Broad match:** a short substring may suppress too many notifications. Mitigate by explicitly documenting literal OR matching and giving a specific-string example.
- **Incomplete metadata:** an unknown title is not suppressed. This preserves notifications, it does not guarantee filtering before metadata arrives.
- **Initially red tests:** stop the behaviour change to separate a pre-existing fault from a new one; do not weaken the criteria.
- If the existing cache does not provide the title at the needed point, or the test requires changing the unverified host protocol: return DO → PLAN with observations; a targeted scout first.
- A proven external incompatibility or persistent low confidence after a targeted scout is grounds to recommend `pdca-escalate`. Do not silently widen the scope.

## 9. Confidence and remaining uncertainties

**High confidence in the supplied pointers:** the settings points, the title cache, a suitable early-exit place and the test harness exist.

**Medium confidence in the product contract:** the title-substring choice remains an explicit assumption. External host API fields are unverified and unused.

There is no blocker for the proposed minimal solution now. No proof of execution exists yet: DO must obtain it and CHECK must assess it independently.

## Plan revision r2 (current)

# PLAN r2 — `wsl-notify-session-filter`

Cycle 1; revision **r2**; attempt **1/3**. This genuinely revises r1: adds environment configuration, restores V1 option forwarding, extends V1 tests, and corrects contradicted documentation. The original filtering criteria remain intact.

## 1. Goal and constraints

Users can exclude sessions from **complete/error notifications by their real cached title**, using either plugin options or an environment variable, on both V1 and V2.

Constraints:
- Preserve existing notification behavior when the filter is absent.
- Never suppress permission/question/form notifications through this setting.
- Reuse existing normalization, title cache, classification, and smoke infrastructure.
- Changes limited to `opencode/plugins/wsl-notify/{index.js,test/smoke.mjs,README.md}`, plus cycle evidence/status.
- No dependencies, commits, unrelated refactoring, or writes to another repository.

## 2. Exact configuration contract

**Option:** `excludeSessionTitles`
**Environment variable:** `WSL_NOTIFY_EXCLUDE_SESSION_TITLES`

Both represent an array of case-sensitive, literal substrings, combined with OR.

Environment format is a **JSON array**, for example:

```sh
export WSL_NOTIFY_EXCLUDE_SESSION_TITLES='["Background","Research, notes"]'
```

### Resolution and normalization

In `limits()`, on every event:

1. If `options?.excludeSessionTitles` is neither `undefined` nor `null`, use that value.
2. Otherwise parse the environment variable as JSON.
3. Normalize the chosen value:
   - Array: retain non-empty strings; ignore other entries.
   - Other types or malformed JSON: empty filter, without throwing.
   - Preserve case and whitespace; do not trim or interpret patterns.

Consequences:
- `[]` explicitly overrides an environment filter.
- An invalid, non-null option also overrides the environment and fails open.
- `undefined`/`null` options permit environment fallback.
- Unset or empty environment values fail open.

**Explicit assumption closing r1's empty-string ambiguity:** an empty string is ignored, rather than matching every title. Whitespace-only strings remain literal strings.

### Matching and suppression

Match only against the existing **real cached session title**. Missing title means no suppression. Do not match the `"opencode"` display fallback, session ID, error text, or rendered notification.

In `handle()`, immediately after `classify()` and before rendering, deduplication, or scheduling, skip matching **complete/error** notifications only. Reuse existing cache resolution; do not introduce another title store.

## 3. V1 compatibility

Change the V1 entry to accept host arguments:

```text
async server(input, options = {})
```

Capture `options ?? {}` for that server instance and pass it to `handle(event, capturedOptions)` instead of `{}`. Do not introduce module-global option state or consume new `input` APIs.

Document the actual channels:

- **V1 configured tuple:**
  `"plugin": [["<plugin-specifier>", { "excludeSessionTitles": ["Background"] }]]`
  The host forwards tuple options as `server(input, options)`.
- **V1 configured string or local auto-discovery:** no options are supplied through that entry; defaults and environment fallback remain available.
- **V2:** existing `ctx.options` path remains unchanged.

Correct the supplied falsified statements in `index.js`, `README.md`, and smoke-test comments. Replace "V1 has no options channel" with the distinction above. Update any other examples affected by forwarding existing V1 options.

## 4. Gaps and decisions

| Statement gap | Closure |
|---|---|
| Whether V1 can receive options | **Evidence:** supplied host sources for `v1.18.0` and `v1.18.29`, plus migration guide, establish tuple → `server(input, options)`. Existing repository claims are contradicted. |
| Environment list encoding | **Decision:** JSON array; no existing list-parser precedent was found. |
| Option/environment precedence | **Decision:** nullish fallback, consistent with existing environment-backed options. |
| Empty strings and malformed configuration | **Explicit assumption/contract:** ignore empty entries; malformed input fails open as specified above. |
| How V1 tests obtain options | **Decision:** extend `runV1(events, gap = 10, options = undefined)` to forward its third argument. Preserve existing positional callers. |
| Actual installed-host integration | **Evidence boundary:** compatibility is established by supplied host source plus adapter tests, not a claimed live V1 run. |
| V1 title availability | **Constraint:** use existing supported cache producers. Unknown titles must not suppress; do not invent an additional host API. |

### Encoding alternatives

| Approach | Benefit | Cost/risk |
|---|---|---|
| Comma-separated list | Simple shell entry | Ambiguous for titles containing commas; requires escaping rules. |
| JSON array — **chosen** | Unambiguous strings, delimiters, quotes, and Unicode; native parser | Requires shell quoting; malformed input must fail open. |

Regex and session-ID alternatives remain rejected as in r1.

## 5. Acceptance criteria and verification

**S** is the exact smoke command below. Add assertion groups identified by these criterion IDs, emitting `PASS AC-x` only after their assertions pass. Use existing test mechanisms rather than creating a second runner.

| ID | Required observable behavior and negative cases | Verification |
|---|---|---|
| **AC-1** | Matching cached titles suppress complete **and** error; substring OR works and remains case-sensitive. Nonmatching titles, case mismatch, and literal regex-looking text do not overmatch. | **S**, labelled assertions covering both notification kinds and multiple sessions. |
| **AC-2** | Missing real title never suppresses. Matching text found only in fallback `"opencode"`, session ID, or error content does not count. Matching titles do not suppress permission/question/form. A skipped event does not enter dedupe/scheduling and prevent a subsequent eligible notification. | **S**, using existing cache/event fixtures and notification capture. |
| **AC-3** | JSON environment filtering works on **V2 and V1**, including a title containing a comma. Environment changes after initialization are observed on subsequent events. Unset/empty environment leaves normal behavior. | **S**, exercise both adapters; restore environment in `finally`. |
| **AC-4** | Options win over environment on both adapters. Test conflicting lists and explicit `[]`. Undefined/null options fall back; invalid non-null options do not fall back. | **S**, separate precedence cases for V1 and V2. |
| **AC-5** | Invalid option types, invalid JSON, non-array JSON, and empty/non-string entries never throw. Invalid entries are ignored; valid entries in mixed arrays still work. Invalid configuration alone causes no suppression. | **S**, normalization matrix for option and environment sources. |
| **AC-6** | V1 tuple-supplied options reach the filter through `server(input, options)`. The extended helper forwards options. No-argument `server()` and explicit undefined options remain supported; with the new environment variable absent, prior behavior remains unchanged. | **S**, forwarded-options tests plus explicit no-argument coverage. Source-backed CHECK inspection verifies host-call correspondence; do not label this a live-host test. |
| **AC-7** | Documentation describes the option, JSON format, precedence, failure behavior, title semantics, V1 tuple, V1 no-options discovery/string path, and V2 configuration. No blanket "V1 has no options channel" claim remains in the three scoped files. | **D** below; CHECK reviews the resulting files and diff, including the supplied stale locations. Negative case: any contradictory claim or implication that discovery supplies tuple options fails. |
| **AC-8** | Every pre-existing smoke test still passes, with no skipped, removed, or weakened assertions. Whitespace validation passes. | **S** and **W** below; compare test changes against the baseline. Any existing failure blocks completion. |

### Exact evidence commands

Run from `/home/alex/sources/skills`; commands are for the executor/CHECK, not executed by this planner.

```sh
mkdir -p .pdca/wsl-notify-session-filter/rv2
```

**S — AC-1–6 and AC-8:**
```sh
bash -o pipefail -c 'node opencode/plugins/wsl-notify/test/smoke.mjs 2>&1 | tee .pdca/wsl-notify-session-filter/rv2/smoke.log'
```

**D — review evidence for AC-7 and baseline comparison:**
```sh
git diff -- opencode/plugins/wsl-notify/index.js opencode/plugins/wsl-notify/test/smoke.mjs opencode/plugins/wsl-notify/README.md > .pdca/wsl-notify-session-filter/rv2/changes.diff
```

**W — AC-8:**
```sh
bash -o pipefail -c 'git diff --check -- opencode/plugins/wsl-notify/index.js opencode/plugins/wsl-notify/test/smoke.mjs opencode/plugins/wsl-notify/README.md 2>&1 | tee .pdca/wsl-notify-session-filter/rv2/diff-check.log'
```

CHECK records criterion-level results and source pointers; command success alone does not establish documentation correctness.

## 6. Units, dependencies, ownership

| Unit | Priority | Expected result/evidence | Dependencies | Owner |
|---|---|---|---|---|
| **U1 — Shared filter** | P0 | Option/environment normalization and correctly placed title-based suppression; AC-1–5 | None | Executor |
| **U2 — V1 adapter** | P0 | Per-instance host-option forwarding, omitted-option compatibility; AC-6 | U1 contract | Executor |
| **U3 — Verification** | P0 | Extended V1 helper, isolated environment tests, complete regression evidence | U1, U2 | Executor; independent CHECK verdict |
| **U4 — Configuration documentation** | P1 | Accurate examples and corrected V1 claims; AC-7 | U1, U2 | Executor; CHECK review |

U1/U2 both edit `index.js`; execute serially. Preserve original r1 work rather than replacing it.

## 7. Means, risks, and stop conditions

- Use existing Node smoke harness, event fixtures, fake notification capture, and environment conventions. No real Windows toast is required.
- Save and restore previous environment values in `finally`; do not merely delete variables that may have existed.
- V1 forwarding intentionally makes previously dropped existing options effective; include this in compatibility review.
- Treat shell-quoting mistakes as malformed configuration, not crashes or implicit CSV fallback.

**Stop and return to PLAN** if the prescribed insertion point cannot access the authoritative cached title without changing established behavior, or existing tests expose an unresolved regression. Do not substitute rendered text or weaken criteria.

**Targeted scout, then escalation if still uncertain:** contradictory host-option evidence, inability to establish the required V1 title path, or unavailable verification that leaves compatibility persistently low-confidence. Recommend `pdca-escalate` trigger 5 in that persistent case. No external blocker is currently established.

## 8. Return classification and confidence

This is a **user-requested revision**, not a DO → PLAN candidate. The original filter remains active; environment support and V1 forwarding are additive requirements.

**High confidence:** V1 host option channel and existing integration points, based on supplied evidence.
**Explicit assumptions:** empty-string handling and the selected JSON/precedence contract.
**Still unverified:** implementation, all runtime assertions, and any live-host execution. No completion claim is made.

## DO units

| Unit | State | Criteria covered | superseded→replacement |
|---|---|---|---|
| U1 — Shared filter (option + env normalization, title-based skip) | done | AC-1–AC-5 | — |
| U2 — V1 adapter (`server(input, options)` forwarding) | done | AC-6 | — |
| U3 — Verification (extend `runV1`, env tests, regression) | done | AC-3, AC-4, AC-5, AC-6, AC-8 | — |
| U4 — Configuration documentation (option/env/V1 channels, correct falsified claims) | done | AC-7 | — |

Dependencies: U2 depends on U1's contract; U3 depends on U1,U2; U4 depends on U1,U2. U1 and U2 both edit `index.js` → execute serially.

## Decisions made

- Filter key = session title (explicit assumption, medium confidence); alternative approaches (regex, session IDs) rejected — see PLAN §4.
- Invalid config never throws and never suppresses (fail-open on notifications).
- Environment list encoding = JSON array (r2 decision; malformed input fails open).
- Option/environment precedence = nullish fallback: non-null option wins, `undefined`/`null` falls back to the environment (r2 decision).
- Empty strings are ignored rather than matching every title (r2 explicit assumption).
- V1 receives tuple options via `server(input, options)` and forwards them per server instance (r2, evidence-backed); r1's "no V1 options channel" claim is superseded.

## Means and verification methods

- S: `bash -o pipefail -c 'node opencode/plugins/wsl-notify/test/smoke.mjs 2>&1 | tee .pdca/wsl-notify-session-filter/rv2/smoke.log'`.
- D: `git diff -- ... > .pdca/wsl-notify-session-filter/rv2/changes.diff` + substantive review of index.js, test/smoke.mjs, README.md.
- W: `git diff --check -- ... 2>&1 | tee .pdca/wsl-notify-session-filter/rv2/diff-check.log`.
- Per-criterion behavioural scenarios in test/smoke.mjs in the existing harness style, labelled `PASS AC-x`.
- Evidence manifest (frozen at DO→CHECK): `.pdca/wsl-notify-session-filter/rv2/manifest.json`.

## Risks / known issues

- Semantic risk (title vs regex/ID) — medium, status: accepted assumption.
- Broad substring match — low, mitigated by docs.
- V1 forwarding makes previously dropped existing options effective — compatibility review required (done in CHECK; accepted).
- Unverified host `Session.Info` fields (directory/agent/tags, `data.info` shape) — not used; out of scope.
- **[non-blocking / deferred]** `test/smoke.mjs:835-845` — `AC-6 server(input, options) accepts a tuple call` is a no-throw smoke check that is vacuous on its own (a zero-arg `server()` would also not throw); coverage is carried by the non-vacuous `AC-6 tuple options reach the V1 filter and suppress` + `server() with no arguments keeps prior behaviour`. Status: deferred, no action.
- **[cosmetic / deferred]** `test/smoke.mjs:675,807,811` — `events()` helper called with an unused string argument in AC-5. Status: cosmetic, deferred.

## Deferred + trigger

- Support for filtering on other session attributes (directory/agent/tags/ID) — deferred; trigger: user reports a need for a different key.
- Test-hygiene cleanup of the two observations above — trigger: next touch of `test/smoke.mjs`.

## Next plan

- No next cycle planned for this task. Natural next steps if the user asks: (a) support a different session key (directory/agent/tags/ID) — unknown whether the host exposes them; (b) a release/publish step for the plugin (version bump + npm publish) was intentionally NOT part of this cycle.

## Changed artefacts

- `opencode/plugins/wsl-notify/index.js` (U1/U2 — `excludeSessionTitles` option/env, title-based skip, V1 `server(input, options)` forwarding)
- `opencode/plugins/wsl-notify/test/smoke.mjs` (U3 — extended `runV1`, AC-1…AC-6 assertions, regression)
- `opencode/plugins/wsl-notify/README.md` (U4 — option/env/precedence/V1 tuple docs, falsified claims corrected)
- `.pdca/status/wsl-notify-session-filter-1.md` (this file — status/evidence record, kept)
- `.pdca/wsl-notify-session-filter/rv1/` (r1 evidence dir, empty)
- `.pdca/wsl-notify-session-filter/rv2/baseline-smoke.log`
- `.pdca/wsl-notify-session-filter/rv2/smoke-post-u1-u2.log`
- `.pdca/wsl-notify-session-filter/rv2/probe-u1-u2.log`
- `.pdca/wsl-notify-session-filter/rv2/probe-dedupe-v1.log`
- `.pdca/wsl-notify-session-filter/rv2/smoke.log`
- `.pdca/wsl-notify-session-filter/rv2/changes.diff`
- `.pdca/wsl-notify-session-filter/rv2/diff-check.log`
- `.pdca/wsl-notify-session-filter/rv2/stale-phrase-grep.log`
- `.pdca/wsl-notify-session-filter/rv2/manifest.json`

## Pointers

- Plan source: PLAN r2 above (r1 preserved under "Plan revision r1 (superseded by r2)").
- Code: `opencode/plugins/wsl-notify/index.js:25-45,378-392,579-621,628,666-677`.
- V1 host evidence (`anomalyco/opencode` v1.18.29):
  - `packages/plugin/src/index.ts` — `Plugin = (input, options?)`.
  - `packages/opencode/src/plugin/index.ts` — `server(input, load.options)`.
  - `packages/opencode/src/config/plugin.ts` — `pluginOptions`.
  - Migration guide: https://opencode.ai/v2/docs/build/plugins/migrate-v1/

## Done / Verified

- **Done:** the setting `excludeSessionTitles` (option + `WSL_NOTIFY_EXCLUDE_SESSION_TITLES` JSON env) implemented in `opencode/plugins/wsl-notify/index.js`; V1 `server(input, options)` now forwards options; tests extended in `opencode/plugins/wsl-notify/test/smoke.mjs`; README documents option, env format, precedence/failure semantics and the V1 tuple channel, and the falsified "V1 has no options channel" claims are corrected; suite green 109 checks / 0 failures.
- **Verified:** CHECK verdict `pass` (session `ses_eac78592affemTfycxqLnzPzlX`), matrix AC-1…AC-8 all `met`; evidence manifest `.pdca/wsl-notify-session-filter/rv2/manifest.json`; smoke log `.pdca/wsl-notify-session-filter/rv2/smoke.log` (`all checks passed`); `git diff --check` clean (`rv2/diff-check.log`, 0 bytes); stale-phrase grep none found (`rv2/stale-phrase-grep.log`). Artefact identity HEAD `2002da3f7690b0d11d224ebc3a4e5850ef3b22bd`.
- **Verification boundary (explicit):** no live OpenCode 1.18.x/V2 host run and no real Windows PowerShell execution; V1 compatibility rests on host source (`server(input, load.options)`) + adapter-level tests, as declared in plan r2 §4/AC-6 — accepted by CHECK as within the declared boundary.

## Progress log

```text
2026-10-19T09:05:53Z | PLAN | revision 1 | iteration 1/3 | PLAN ready — awaiting user approval | .pdca/status/wsl-notify-session-filter-1.md
2026-10-19T09:22:04Z | PLAN | revision 2 | iteration 1/3 | Replanned: user change request — add env var + V1 options forwarding; r1 plan superseded before DO (r 1→2, iteration 1/3) | .pdca/status/wsl-notify-session-filter-1.md
2026-10-19T09:25:19Z | DO | revision 2 | iteration 1/3 | plan approved — DO started; P: closed, D: U1 running | .pdca/wsl-notify-session-filter/rv2/baseline-smoke.log
2026-10-19T09:25:20Z | DO | revision 2 | iteration 1/3 | U1 changed: excludeSessionTitles option+env normalization, title-based skip in handle() | opencode/plugins/wsl-notify/index.js
2026-10-19T09:25:21Z | DO | revision 2 | iteration 1/3 | U2 changed: V1 server(input, options) forwards options to handle(); stale "no options channel" comments corrected | opencode/plugins/wsl-notify/index.js
2026-10-19T09:27:53Z | DO | revision 2 | iteration 1/3 | U3 running: runV1 extended with options; AC-1–AC-6 assertions added | opencode/plugins/wsl-notify/test/smoke.mjs
2026-10-19T09:27:53Z | DO | revision 2 | iteration 1/3 | U3 evidence: full smoke suite green — all checks passed (109 ok, 0 failures; PASS AC-1…AC-6) | .pdca/wsl-notify-session-filter/rv2/smoke.log
2026-10-19T09:32:54Z | DO | revision 2 | iteration 1/3 | U4 changed: README documents option + env JSON format + precedence/failure semantics + V1 tuple channel; stale V1 claims corrected | opencode/plugins/wsl-notify/README.md
2026-10-19T09:32:54Z | DO | revision 2 | iteration 1/3 | D: units U1–U4 done with recorded evidence; D: closed, C: in progress | .pdca/wsl-notify-session-filter/rv2/smoke.log
2026-10-19T09:33:48Z | DO | revision 2 | iteration 1/3 | evidence manifest frozen: required AC-1–AC-8, artefact head 2002da3 | .pdca/wsl-notify-session-filter/rv2/manifest.json
2026-10-19T09:43:18Z | CHECK | revision 2 | iteration 1/3 | CHECK verdict: pass — AC-1…AC-8 met, 0 defects, 2 non-blocking observations | .pdca/wsl-notify-session-filter/rv2/manifest.json
2026-10-19T09:43:18Z | ACT | revision 2 | iteration 1/3 | C: closed, A: in progress — CHECK-accepted result finalized | .pdca/status/wsl-notify-session-filter-1.md
2026-10-19T09:43:18Z | ACT | revision 2 | iteration 1/3 | ACT closed — cycle 1 complete; status file finalized and kept | .pdca/status/wsl-notify-session-filter-1.md
```
