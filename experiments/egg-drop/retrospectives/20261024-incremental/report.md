# Egg-drop `pdca-incremental` run — raw API telemetry audit

Generated: 2026-10-24T18:47:01Z · receipts: `/tmp/opencode/retro-egg-drop-incremental-20261024T184049Z/`
(`raw/`, `results.json`, `summary.json`, `hashes.json`, `receipts.sha256`, scripts `fetch.py`, `inspect.py`, `analyze.py`, `figures.py`, `finalize.py`).

Method: OpenCode v2.1.3 built-in authenticated `opencode api get` (no credential files, no server restart, no host/repo
writes, no experiment script executed). All JSON is stored verbatim in `raw/`; all arithmetic below is Python `Decimal`.
Recursive discovery via `GET /api/session?parentID=<id>`; messages via `/api/session/<id>/message?limit=200&order=asc`
(the default 50 rows would drop the last row of the 51-row D0 transcript).

## 1. Root and tree

Newest egg-drop campaign rooted at the working directory `/home/alex/sources/skills`:

| field | value |
|---|---|
| root | `ses_e91154aa2ffeUmLHXVS5oWmQom` |
| parentID | `null` |
| title | `Autonomous egg drop test via pdca-incremental` |
| location.directory | `/home/alex/sources/skills` |
| first user message | `skill pdca-incremental по спецификации experiments/egg-drop/egg-drop-test.md автономно` (`msg_16eeab567001U0xYfoitS8RaIt`, 17:17:18.229Z) |
| session created / updated | 17:17:18.067Z / 18:30:58.715Z |
| wall (session) | **4,420.648 s = 1h13m40.6s** |
| wall (first user → final assistant) | **4,420.486 s** |
| outcome | `succeeded` |

Discovery is closed: 17 sessions, 1 root + 9 direct children + 7 orchestrator children; 0 orphan children of any
family member in the 500-session inventory. The planner session is one session resumed 4 times; the baseline executor is
resumed once; the other 15 sessions are single-use.

| phase | session | parent | agent | model (variant) | start–end UTC | active s | asst msgs | reported $ |
|---|---|---|---|---|---:|---:|---:|---:|
| ROOT (campaign controller) | `ses_e91154aa2ffeUmLHXVS5oWmQom` | — | build | `opencode-go/deepseek-v4.1-flash` (default) | 17:17:18.067–18:30:58.715 | 4,420.6 (session) | 19 | 0.046078434 |
| facts | `ses_e91149a4fffeWi4V6iFiyqkM0h` | root | pdca-scout | `opencode-go/deepseek-v4.1-flash` | 17:18:03.193–17:19:24.718 | 81.5 | 17 | 0.012204234 |
| planner (4 turns) | `ses_e91131328ffe8UGrvKXeGu6NPw` | root | pdca-planner | `openai/gpt-6.1-sol` (high) | 17:19:43–18:29:20 | 570.2 | 4 | 0 (unpriced) |
| baseline+charter+status | `ses_e910dfafeffesWN9HcBcOxdTu4` | root | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 17:25:17.194–17:30:54.719 | 337.5 | 19 | 0.024328758 |
| STEP-1 orchestrator | `ses_e9106ab0bffekAzivcR5KEplQh` | root | pdca-orchestrator | `opencode-go/deepseek-v4.1-flash` | 17:33:16.419–18:13:25.215 | 2,408.8 | 10 | 0.027678996 |
| D0 checker+controls | `ses_e9105d2f8ffehXzjhKS09LtHhn` | orch | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 17:34:11.727–17:48:19.502 | 847.8 | 49 | 0.111770904 |
| known-good verifier | `ses_e90f86f9bffeIlwkFHzGua7Dej` | orch | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 17:48:49.191–17:50:18.282 | 89.1 | 9 | 0.010301802 |
| D1 answer | `ses_e90f86f9dffec7p3Ixv99P1TCD` | orch | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 17:48:49.135–17:59:04.131 | 615.0 | 25 | 0.059818362 |
| D2 freeze+C1/C2 | `ses_e90eedb34ffekdoGO0ZIKaLdfn` | orch | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 17:59:16.948–18:01:53.763 | 156.8 | 19 | 0.015838728 |
| CHECK gather | `ses_e90ec35c2ffeF1R95wrN0uKcIy` | orch | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 18:02:10.373–18:08:22.911 | 372.5 | 33 | 0.041343678 |
| CHECK triage | `ses_e90e63e56ffewCl3u2NkBeuoW1` | orch | pdca-check | `opencode/gemini-4-argon` (high) | 18:08:41.394–18:11:36.106 | 174.7 | 4 | 0.284912500 |
| ACT bookkeeping | `ses_e90e35facffelFSkV6adG83uLz` | orch | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 18:11:49.468–18:13:21.124 | 91.7 | 11 | 0.007686300 |
| ACCEPT rubric | `ses_e90e1b654ffew2T4qWLerBIFcC` | root | pdca-check | `opencode/gemini-4-argon` (high) | 18:13:38.360–18:19:13.231 | 334.9 | 4 | 0.405825100 |
| record ACCEPT | `ses_e90dc461bffeXLlWzGrN2YZ1Ob` | root | pdca-executor | `deepseek/deepseek-flash` | 18:19:34.773–18:20:41.720 | 66.9 | 21 | 0.011666850 |
| verify mechanical | `ses_e90d959bbffeSrWXwfrAXOYckB` | root | pdca-executor | `deepseek/deepseek-flash` | 18:22:46.348–18:23:48.001 | 61.7 | 17 | 0.008754324 |
| verify rubric | `ses_e90d84827ffeismbW7PUrUidCd` | root | pdca-check | `opencode/gemini-4-argon` (high) | 18:23:56.387–18:28:28.836 | 272.4 | 3 | 0.302139800 |
| close status | `ses_e90d31ecdffezEuBHyTMkhWgCg` | root | pdca-executor | `deepseek/deepseek-flash` | 18:29:34.651–18:30:46.562 | 71.9 | 20 | 0.012031518 |

Notes: the planner session is listed once but contributes four separate turns (310.9 / 112.3 / 105.7 / 41.3 s). Five
late executor sessions ran on `deepseek/deepseek-flash` instead of `opencode-go/deepseek-v4.1-flash`; both providers
list the identical 0.15 / 0.60 / 0.003 price, so the provider switch does not change the arithmetic (verified separately
per provider in §6). The old ordinary run (`ses_e91cedfe2ffenrzGxquhj3MxgF`) and the direct-Sol baseline
(`ses_e918ecc1dffe3LzsVPFwf7EAxM`) are comparisons only — their values are carried from the prior audit
(`/tmp/opencode/retro-egg-drop-cost-20261024T161904Z`) and are not in this receipt tree; the current retro session
(`ses_e929b3ae4ffefyewuKW7WmuzFK`) and its children are excluded.

## 2. What was actually loaded — old installed contract, not the new design

| item | receipt |
|---|---|
| initial skill tool call | `msg_16eeab625001OdinRXWvHimrML`, tool part `call_00_bt6to21m3r064oqrhvg8pvd2`, input `{"id":"pdca-incremental"}`, 17:17:18.268Z, metadata `truncated: false`, response 38,369 chars |
| loaded incremental body | equals the **host** `/home/alex/.config/opencode/skills/pdca-incremental/SKILL.md` body (plus the injected `# Skill:` header); it contains `otherwise → pdca` and `pdca/SKILL.md`, and **no** `pdca-general` |
| host vs working source | host `0c74eb78…` (mtime 07:22Z) vs source `940172f2…` (mtime 17:06Z); diff = five `pdca` → `pdca-general` rename lines only |
| new design doc | `docs/superpowers/specs/2026-10-24-pdca-lensing-design.md`: birth **18:22:22Z**, last modified **18:34:22Z**, status “На согласовании” (under review, implementation out of scope) |
| design-doc references | **no explicit access found** — no `read`/`glob`/`grep` tool input targets the file and no assistant text discusses its content; `lensing`/`superpowers` occur in 19/21 message rows only as `snapshot.files` metadata (dirty-tree listing), `pdca-general` in 11 rows of `git status` output listing unrelated staged renames |

The new run used the **old installed** `pdca-incremental` contract from the host deploy (which still carries the
pre-rename `pdca` names). The working-tree source was 11 minutes old at run start but had not been deployed, so its
only differences are the pending renames. The design doc was **created 18:22:22Z** — 8m36.7s *before* final delivery
(18:30:58.715Z) — and last modified 18:34:22Z, 3m23.3s *after* it; its mtime therefore cannot prove it was unavailable
during the run. What the receipts show is the **absence of an explicit read/glob/grep targeting the file and of any
assistant discussion of its content** (occurrences are only snapshot metadata and `git status` output). That absence is
**not** proof that the model never received the document as context, and the timestamps do not settle availability.
What *is* proven is the loaded contract itself (host sha `0c74eb78…`, no `pdca-general`) and that no implemented design
change was rolled out.

### 2.1 Step variant

| item | receipt |
|---|---|
| campaign rule (loaded skill) | “The step is executed by `pdca-orchestrator`, but the campaign determines the step's variant: `.NET/C#` → `pdca-dotnet`, other code → `pdca-coder`, otherwise → `pdca` … as `selected_variant`.” |
| actual selection | root, when commissioning the step-1 brief: “`selected_variant: pdca-coder` (the step's acceptance is dominated by executable artifacts: `check_answer.py`, controlled fixtures with expected-FAIL mutants, gate reports — real red-first work; prose quality is covered by the campaign's independent rubric ACCEPT)” — `msg_16ef72bd9001ZbzjDCWz0EbBT9` |
| passed to driver | same string in the orchestrator prompt `msg_16ef904b3001OZxlOfxfIHiroF`; manifest `measurement.variant = "pdca-coder"` |
| orchestrator load | `msg_16ef95530001JmjmK8gsViGXsf`, tool part `call_00_6z2hq88n8pyriei1of2c5ohq`; **metadata `truncated: true`**, 677 of 1,426 lines (50,529 chars) + note “full output saved to …/tool-output/tool_16ef9648e001G2QtyhEJzoIDhz” |

The truncation was recovered, not lost: the orchestrator immediately read the saved output at offset 677 (lines
677–1336) and then offset 1337 (lines 1337–1426), i.e. the whole `pdca-coder` contract entered context in three chunks.
This is a content-injection limit observation, not a flat capability fallback.

### 2.2 Controller / fallback

**Delegated, not flat.** The root `build` session owns the campaign and ran BOOTSTRAP itself (scout → planner →
executor); step 1 was delegated to one `pdca-orchestrator` child, which ran DO → CHECK → ACT. There is no `Notice:` of a
flat fallback in the transcript (the only `Notice:` is the D0 3-fixes-vs-2 budget deviation). Controller owner =
root `ses_e91154aa2ffeUmLHXVS5oWmQom`.

## 3. Timing — actual transcript times

Definitions used (no status-file stamp is used for any duration):

- **T0** = first user message `time.created` = 17:17:18.229Z; **T1** = root `time.updated` = last assistant
  `time.completed` = 18:30:58.715Z. Root wall = T1−T0.
- **Phase active span** = first assistant message `time.created` → last assistant message `time.completed` of that
  dispatch/turn. This excludes pre-dispatch gaps and, for the resumed planner session, the idle time between turns.
- **Parent wait** = `subagent` tool part `time.created → time.completed`; it includes dispatch overhead and must not be
  added to child active spans.
- **Child calendar** = first child start → last child end; **child additive** = Σ active spans; **gaps** = calendar −
  (additive − true overlap).

| group | span UTC | s | % of 4,420.486 |
|---|---|---:|---:|
| BOOTSTRAP total | 17:17:18.229 → 17:33:16.419 | 958.2 | 21.68 |
|  · skill load + spec read (root own) | 17:17:18.229 → 17:18:03.193 | 45.0 | 1.02 |
|  · facts scout | 17:18:03.193 → 17:19:24.718 | 81.5 | 1.84 |
|  · planner BOOTSTRAP decision (Sol) | 17:19:43.394 → 17:24:54.305 | 310.9 | 7.03 |
|  · baseline + charter + status | 17:25:17.194 → 17:30:54.719 | 337.5 | 7.64 |
|  · planner STEP-1 brief (Sol) | 17:31:03.425 → 17:32:55.742 | 112.3 | 2.54 |
| STEP 1 total (orchestrator) | 17:33:16.419 → 18:13:25.215 | 2,408.8 | 54.49 |
|  · D0 checker + controls | 17:34:11.727 → 17:48:19.502 | 847.8 | 19.18 |
|  · known-good independent verifier | 17:48:49.191 → 17:50:18.282 | 89.1 | 2.02 |
|  · D1 answer | 17:48:49.135 → 17:59:04.131 | 615.0 | 13.91 |
|  · D2 freeze + C1/C2 | 17:59:16.948 → 18:01:53.763 | 156.8 | 3.55 |
|  · CHECK gather | 18:02:10.373 → 18:08:22.911 | 372.5 | 8.43 |
|  · CHECK triage (Gemini) | 18:08:41.394 → 18:11:36.106 | 174.7 | 3.95 |
|  · ACT bookkeeping | 18:11:49.468 → 18:13:21.124 | 91.7 | 2.07 |
| POST-STEP total | 18:13:25.215 → 18:30:58.715 | 1,053.5 | 23.83 |
|  · ACCEPT rubric (Gemini) | 18:13:38.360 → 18:19:13.231 | 334.9 | 7.58 |
|  · record ACCEPT | 18:19:34.773 → 18:20:41.720 | 66.9 | 1.51 |
|  · planner DECIDE (Sol) | 18:20:52.303 → 18:22:37.972 | 105.7 | 2.39 |
|  · verify mechanical | 18:22:46.348 → 18:23:48.001 | 61.7 | 1.39 |
|  · verify rubric (Gemini) | 18:23:56.387 → 18:28:28.836 | 272.4 | 6.16 |
|  · planner STOP (Sol) | 18:28:39.317 → 18:29:20.627 | 41.3 | 0.93 |
|  · close status | 18:29:34.651 → 18:30:46.562 | 71.9 | 1.63 |

Children (15 sessions, 18 turns): **additive 4,143.986 s**, true overlap **89.147 s** (known-good inside D1),
**calendar 4,363.369 s**, gaps **308.530 s** (6.98%). Root own time **30.540 s** (0.69%); root waits for 13 subagent
dispatches **4,389.946 s**; the 26.577 s difference between root waits and child calendar is dispatch overhead inside
the root–child edges. Orchestrator: wall 2,408.796 s = 7 children calendar 2,349.397 s + 59.399 s before/after children;
its children are serial except the 89.147 s known-good ∥ D1 overlap; child internal gaps 90.961 s. No parent wait is
added twice.

Milestones (T0-based): first full-file `answer.md` write (draft, 23,142 chars) **2,214.499 s (36m54.5s)** — this is
the first drafting write, not the final/quality-approved answer (35,049 bytes after five later edits);
ACCEPT rubric complete **3,715.002 s (61m55.0s)**; verify rubric complete **4,270.607 s (71m10.6s)**; final delivered
message **4,420.486 s (73m40.5s)**.

### 3.1 Human waits, timeouts, retries, compactions

| event | count | evidence |
|---|---:|---|
| user messages / human clarifications | 1 / **0** | single user row at 17:17:18.229; no later human input |
| provider timeouts | **0** | no `provider.transport`, no `tokens:null`, no `cost:null` in 284 assistant rows |
| provider error messages | 0 | `error` absent on every assistant row |
| prompt-correction retry | 1 | root passed literal `[PASTE]` in `msg_16ef1f2050e…`; executor correctly withheld the charter (`msg_16ef53163…`, 17:28:50), root corrected at 17:29:24 (`msg_16ef5ca5a…`); 34.1 s gap + 90.4 s second turn |
| D0 implementation fixes | 3 | `selftest-red1.log`, `selftest-red2.log`, `/tmp/opencode/full1.json`; green at 17:45:32/17:46:12 |
| answer/draft fixes | 3 (status count) | `DEF-g05-line-wrap-negation`, `DEF-prose-number-drift`, plus the ACT-recorded third; `red-first.md#deviations` |
| session compactions | **0** | no `compaction`/`summary` message rows; only user/assistant/idle |
| tool failures | 7 | 4 `read` (3 permission.rejected + 1 binary `.git/index`), 2 `shell` permission.rejected, 1 `grep` unknown (invalid ripgrep output) |

The status file’s hand-written stamps are not the source of these times, and its first record is **17:28:24Z**, i.e.
**11m05.8s after T0** (17:17:18.229Z): the first 11m06 of the run (skill load, facts scout, planner bootstrap) has no
status entry at all. Further drift: status says `PLAN 17:36:12` but the step-1 brief returned 17:32:55 and the
orchestrator started 17:33:16 (2m56s late); status says `D1 running 17:55:53`, but the first `answer.md` write was
17:54:12.728 (1m40.3s earlier); status says `STOP 18:30:31`, while the transcript ends 18:30:58.715 (27.7s later).
The report uses transcript times only, and every comparison is based on the actual session timestamps (T0/T1), never on
status stamps.

### 3.2 Where the time went

- **Largest single dispatch: D0 checker development, 847.8 s (19.18%)** — 49 assistant messages, 16 `check_answer.py`
  invocations, 3 red selftests and 3 fixes before green.
- **Second: D1 answer, 615.0 s (13.91%, ≈10m15s)** — of which 323.5 s pre-write analysis (reads + two arithmetic
  shells), **208.37 s (≈3m28s) of actual write/edit** (17:54:12.728 → 17:57:41.098; first full-file write 23,142
  chars), 83.0 s bookkeeping. The “answer written ~2 min” figure is the status window 17:55:53→17:57:59 = 126 s; it
  starts *after* the first full-file write and omits the 208 s write/edit span. The status claim is therefore an
  undercount, not the write time.
- **Third: CHECK, 547.3 s (12.38%)** — gather 372.5 + triage 174.7.
- **Largest composite group: bootstrap, 958.2 s (21.68%)** — five sequential sub-spans: planner decision 310.9 +
  baseline/charter/status 337.5 + brief 112.3 + scout 81.5 + root read 45.0 (+71.0 s dispatch gaps). Being a composite,
  it is larger than any single dispatch; D0 (847.8 s) is the largest **single** dispatch, not the largest block overall.
- **ACCEPT + verify + record/stop/close, 954.8 s (21.6%)** — this is campaign review/finalization, not answer work.
- **Partition caveat:** only the three calendar groups are an exclusive additive partition — BOOTSTRAP 958.190 +
  STEP-1 2,408.796 + POST-STEP 1,053.500 = **4,420.486 s**. The step-1 sub-blocks (and the rows above) include the true
  **89.147 s** known-good ∥ D1 overlap, so they must not be summed as an exclusive partition.
- No timeout, no infra stall, no compaction; the long pole is model work on checker and review, not tool execution:
  344 tool parts total, non-subagent tool execution is negligible against 73m40s.

## 4. Messages, requests and tools

| scope | count |
|---|---:|
| sessions | 17 (1 root, 1 orchestrator, 15 children; planner 4 turns) |
| assistant messages | **284** (263 `finish=tool-calls`, 21 `finish=stop`) |
| user rows | 21 (17 sessions + 3 extra planner turns + 1 baseline-executor correction) |
| idle rows | 21 |
| all message rows | 326 |
| duplicate assistant message IDs across sessions | **0** |
| tool parts | **344**, all with unique tool-call IDs (0 duplicates) |
| tools | shell 168, read 69, edit 36, write 24, subagent 20, glob 15, execute 5, grep 5, skill 2 |
| failed tools | 7 (read 4, shell 2, grep 1) |

`284` is the number of recorded assistant responses, not an independently observed provider-side request counter: the
API exposes no separate request/retry table. There are no null-usage rows and no error rows, so no request is known to
be missing; the count should still be read as “transcript-observable calls”, not “provider invoice lines”.
Session resumes are counted once: the planner’s four user turns produce four assistant turns in one session; the
baseline executor has two user turns (initial + `[PASTE]` correction) in one session. No message ID repeats.

## 5. Token/cost accounting

### 5.1 Formula verification (per message, Decimal, tolerance 1e-9 USD)

Current catalog prices (per 1M tokens, from `GET /api/model` at fetch time):

| provider/model | input | output | cache read | cache write | tier |
|---|---:|---:|---:|---:|---|
| `opencode-go/deepseek-v4.1-flash` | 0.15 | 0.60 | 0.003 | 0 | single |
| `deepseek/deepseek-flash` | 0.15 | 0.60 | 0.003 | 0 | single |
| `opencode/gemini-4-argon` | 2.00 | 10.00 | 0.10 | 0 | single |
| `openai/gpt-6.1-sol` | — (empty) | — | — | — | unpriced |
| `opencode/gpt-6.1-sol` (proxy only) | 2.00 | 10.00 | 0.10 | 2.50 | tier 1; tier 2 at 272,000 prompt = 4/15/0.2 |
| `opencode/deepseek-v4.1-flash` (not used) | 0.30 | 1.20 | 0.006 | 0 | single |

Verified formula is **C2 = input·Pin + (output + reasoning)·Pout + cache_read·Pcr + cache_write·Pcw**, applied
per message with that message’s model and that message’s own prompt size (no aggregated-context tier):

| model | priced messages | C2 matches ≤1e-9 | max C2 deviation | C1 matches | C3 matches |
|---|---:|---:|---:|---:|---:|
| `opencode-go/deepseek-v4.1-flash` | 211 | **211/211** | 1e-18 | 40 | 40 |
| `deepseek/deepseek-flash` | 58 | **58/58** | 2e-19 | 22 | 22 |
| `opencode/gemini-4-argon` | 11 | **11/11** | 2e-17 | 0 | 0 |
| `openai/gpt-6.1-sol` | 4 | unpriced | — | — | — |

C1/C3 match only messages with `reasoning=0`, as in the prior audit; C2 is the only formula that reproduces all priced
messages. `cache_write` is 0 in every message, so its price does not affect the totals.

### 5.2 Per role

| role | sessions | asst msgs | input | output | reasoning | cache read | reported $ | share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pdca-check | 3 | 11 | 175,602 | 16,352 | 42,850 | 496,534 | **0.992877400** | 71.82% |
| pdca-executor | 10 | 223 | 723,740 | 139,869 | 122,403 | 12,539,008 | 0.303541224 | 21.96% |
| build (root) | 1 | 19 | 116,463 | 29,923 | 11,342 | 1,283,328 | 0.046078434 | 3.33% |
| pdca-orchestrator | 1 | 10 | 81,558 | 11,586 | 11,248 | 581,632 | 0.027678996 | 2.00% |
| pdca-scout | 1 | 17 | 28,923 | 7,380 | 3,777 | 390,528 | 0.012204234 | 0.88% |
| pdca-planner | 1 | 4 | 11,215 | 13,062 | 5,648 | 66,944 | **0** (unpriced Sol) | 0% |
| **total** | **17** | **284** | **1,137,501** | **218,172** | **197,268** | **15,357,974** | **1.382380288** | 100% |

### 5.3 Per model

| model | asst msgs | input | output | reasoning | cache read | reported $ |
|---|---:|---:|---:|---:|---:|---:|
| `opencode/gemini-4-argon` | 11 | 175,602 | 16,352 | 42,850 | 496,534 | 0.992877400 |
| `opencode-go/deepseek-v4.1-flash` | 211 | 886,362 | 166,171 | 142,430 | 12,978,432 | 0.357050196 |
| `deepseek/deepseek-flash` | 58 | 64,322 | 22,587 | 6,340 | 1,816,064 | 0.032452692 |
| `openai/gpt-6.1-sol` | 4 | 11,215 | 13,062 | 5,648 | 66,944 | 0 (unknown) |
| **total** | **284** | **1,137,501** | **218,172** | **197,268** | **15,357,974** | **1.382380288** |

### 5.4 Per phase group (root coordination allocated by message timestamp)

| group | reported $ | share |
|---|---:|---:|
| BOOTSTRAP (root coordination + scout + planner decision + baseline/charter/status + brief) | 0.064348524 | 4.65% |
| STEP 1 (orchestrator + D0, known-good, D1, D2, CHECK gather/triage, ACT bookkeeping) | 0.559351270 | 40.46% |
| POST-STEP (ACCEPT + record + DECIDE + verify mech/rubric + STOP + close + root final coordination) | 0.758680494 | 54.88% |
| **message total** | **1.382380288** | 100% |

The full per-phase table (input/output/reasoning/cache per phase) is in `results.json.phases` and `report.md` §1/§3.

### 5.5 Hidden usage vs messages, Sol, nulls

- **Root hidden block only:** session meta tokens 116,669 / 29,934 / 11,342 / cache 1,283,584 vs message sums 116,463 /
  29,923 / 11,342 / 1,283,328 → hidden **206 input, 11 output, 0 reasoning, 256 cache read**, priced at flash rates
  exactly **$0.000038268**. This is real session-level usage with no returned assistant message; it is reported
  separately, not merged into any role.
- The other 16 sessions: meta cost equals the message sum within 2e-17 USD (float noise); token deltas 0.
- **Known total = 1.382380288 + 0.000038268 = $1.382418556** (formula-consistent; excludes Sol dollars).
- **Sol (4 messages, all planner):** 11,215 input / 13,062 output / 5,648 reasoning / 66,944 cache read; reported cost
  $0 because `openai/gpt-6.1-sol` has an empty catalog `cost` array. That $0 is **not** evidence of free usage. Proxy
  only (opencode/gpt-6.1-sol tier 1, 2/10/0.1): **$0.2162244**; the maximum prompt size of any Sol message is 28,041
  tokens, so the 272k second tier would not apply. This is a reference estimate, **not an invoice**.
- **No null-usage rows in this run** (0 timeouts, 0 `tokens:null`, 0 `cost:null`), so unlike the old run there is no
  “unknown usage” gap for priced models. Sol dollars remain the only unknown.
- Tokens are disjoint components: `input` = uncached prompt, `cache.read` = cached prompt, `output` = visible
  completion, `reasoning` = hidden reasoning billed at the output rate. Prompt tokens = input + cache.read; do not sum
  all four as a “total”. Cache share is 93.10% of prompt tokens (old: 95.55%).

## 6. Quality/ACT — separation, independence, and the physics finding

Three Gemini `pdca-check` sessions, all fresh sessions, separate from author and checker author:

| role | session | model | asst msgs | active s | reported $ |
|---|---|---|---:|---:|---:|
| CHECK triage (mechanical contract) | `ses_e90e63e56ffewCl3u2NkBeuoW1` | `opencode/gemini-4-argon` high | 4 | 174.7 | 0.284912500 |
| ACCEPT rubric (campaign) | `ses_e90e1b654ffew2T4qWLerBIFcC` | `opencode/gemini-4-argon` high | 4 | 334.9 | 0.405825100 |
| VERIFY rubric (second isolated) | `ses_e90d84827ffeismbW7PUrUidCd` | `opencode/gemini-4-argon` high | 3 | 272.4 | 0.302139800 |

Identity separation is real at the session level: author = D1 `ses_e90f86f9d…`; checker/fixtures author = D0
`ses_e9105d2f8…`; ACCEPT and VERIFY are different sessions launched independently by the root. Their **actual reads**
(not the mere absence of a file) show the isolation:

- ACCEPT read: frozen spec, frozen answer, charter, `gate.json`, `selftest.json`, `manifest.json`, then the frozen
  `check_answer.py`. It did not read the status file, a self-score, or any prior rubric (none existed yet).
- VERIFY read: frozen spec, frozen answer, `manifest.json`, `verify-gate.json`, `verify-v001/selftest.json`; it tried
  the working `experiments/egg-drop/check_answer.py` and got `permission.rejected`, then stopped (it did **not** read the
  frozen checker either). It did **not** read `.pdca/status/**`, `accept.md`, `charter-r1.md`, `rubric.json` or any
  previous evaluation. The VERIFY prompt explicitly forbids them.
- Therefore the two rubric readers did not see each other: ACCEPT ran 18:13:38–18:19:13 and its outputs did not exist
  when it ran; VERIFY ran 18:23:56–18:28:28 and its actual read list excludes `accept.md`/`rubric.json`. This is
  actual-read evidence, not “the file wasn't there” inference.

**Critical physics finding — not rejected in ACT, downgraded to a deduction and accepted.** The ACCEPT evaluator
scored physics **9.0** while writing:

> «…при ударе 105 г ложемента о блок конусов с порогом смятия 276.8 Н перегрузка самого яйца превысила бы 200 g»
> — `msg_16f1ebce5001XiXnHf8pkEYcVV` (ACCEPT final, 18:19:13Z)

The second evaluator independently kept physics at **9.0** and described the same simplification more mildly:

> «…тормозной путь … описан одномассовой эквивалентной моделью … с 100%-м использованием высоты конусов без вычета
> зоны уплотнения (lock-up). … оценка снижена на 1.0 балл относительно якоря 10.»
> — `msg_16f288aef001y8p3tlLexTF63R` (VERIFY final, 18:28:28Z)

The ACT record explicitly classifies this as **not an acceptance defect**:

> «Named weaknesses — NOT defects of acceptance … They are recorded as the seed for the next step.»
> — `.pdca/egg-drop/rv1/m001/accept.md` (ACCEPT record; evaluator text in `msg_16f1ebce5…`)

and the STOP decision accepted:

> «min(9.100, 9.250) = 9.100 ≥ 9.000.»
> — `msg_16f2c090a001R6WVCdMX2UJx6u` (planner STOP, 18:29:20Z)

Precision on the “9.1” figure: the **threshold is 9.000**, not 9.100. 9.100 is the first assessor’s accepted S; the
second gave 9.250; the campaign takes `min` = 9.100. So the run passed with a 0.100 margin. The physics finding (a
claimed >200 g egg load, i.e. above the design’s 100 g target) was **not** treated as a failure: it cost 1.0 rubric
point, §7 was declared clean, and the finding became the top “next-step seed”. That is a quality caveat about the
rubric’s semantics (a semantic physics objection does not invalidate the mechanical gate), not evidence that the run
rejected the finding.

## 7. Artifact integrity (read-only, hashes only — harness not run)

| artifact | sha256 | bytes | lines |
|---|---|---:|---:|
| `experiments/egg-drop/answer.md` | `40a56cc82905a64da7d6104beec99565e5ef7b49d5fcfa29c94439a3882cd4c3` | 35,049 | 392 |
| `experiments/egg-drop/check_answer.py` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` | 45,641 | 1,097 |
| `experiments/egg-drop/egg-drop-test.md` | `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e` | 15,194 | 289 |
| `.pdca/egg-drop/charter-r1.md` | `b80d80343912724c8f2b9f249f2190c1f6edef123f4155c0c08f0ead372741b8` | 41,212 | 384 |
| `.pdca/egg-drop/rv1/m001/answer.md` | `40a56cc8…` (identical to working) | 35,049 | 392 |
| `.pdca/egg-drop/rv1/m001/check_answer.py` | `d6260656…` (identical to working) | 45,641 | 1,097 |
| `.pdca/egg-drop/rv1/m001/manifest.json` | `ee7c59bfd7fa984c49db01a0df60973680bd0523c2344127c35fd5bb84df11c6` | 10,538 | 171 |

- **27/27 manifest inputs match disk** (independent sha256 recompute; `bad=[]`), and the canonical
  `path␠␠hash` sorted + trailing-newline aggregate is `22d09176f140f5f8910513dcb169326da1cc48b5a17dfc6749406da9f14411b8`,
  exactly the declared `input_hashes_sha256`. Working `answer.md`, `check_answer.py` and `egg-drop-test.md` are
  byte-identical to their frozen `m001` copies. Line counts 1,097 / 392 / 384 / 289 confirm the scout’s figures.
- Read-only JSON outcomes: `m001/selftest.json` selected_cases 22, 22/22 cases ok, gate PASS, diagnostics [];
  `m001/gate.json` selected_cases 1, 12/12 checks PASS; `verify-v001/selftest.json` and `verify-gate.json` repeat the
  same 22/22 and 12/12 PASS. No experiment script was executed for this audit.

## 8. Old vs new — speed and cost (with limits)

Old = prior audited ordinary run `ses_e91cedfe2ffenrzGxquhj3MxgF`, taken from the **previous audit receipts**
`/tmp/opencode/retro-egg-drop-cost-20261024T161904Z` and **not refetched in this receipt set** (2h08m45.421s,
15 sessions, 348 assistant messages, 411 tool parts, 2 timeouts totaling 1,884.482 s). These old-run figures are
**carried comparison evidence**, not recomputable from `raw/` here. New = this run.

| metric | old | new | new/old |
|---|---:|---:|---:|
| root wall | 7,725.421 s | **4,420.648 s** | **0.5722** (42.8% faster) |
| wall excluding old timeouts | 5,840.939 s | 4,420.648 s | 0.7568 (24.3% faster) |
| known message+hidden cost | $1.937966324 | **$1.382418556** | **0.7133** (28.7% cheaper) |
| known + Sol proxy | $2.017435924 | **$1.598642956** | **0.7924** (20.8% cheaper) |
| input tokens | 1,607,051 | 1,137,501 | 0.7078 |
| output tokens | 294,556 | 218,172 | 0.7407 |
| reasoning tokens | 328,778 | 197,268 | 0.6000 |
| cache read | 34,487,096 | 15,357,974 | 0.4453 |
| assistant messages | 348 | 284 | 0.8161 |
| tool parts | 411 | 344 | 0.8370 |

Interpretation and limits:

- The new run is genuinely faster and cheaper **end-to-end**, but it is not the same amount of work: old ran three
  increments with three OBS and three CHECK phases plus two provider timeouts; new ran one increment, one ACCEPT, one
  verify. The structural saving (fewer cycles) dominates. Excluding the old 31m24s of timeouts, the wall advantage is
  still **24.3%**, so the improvement is not only “the timeouts did not happen”. That timeout-excluded comparison is an
  **arithmetic counterfactual** (recorded timeout durations subtracted from old wall), not a controlled re-run.
- Cost is dominated by Gemini in both runs: old $1.307796800 (67.5% of known), new $0.992877400 (71.8%). The new
  Gemini bill is 24.1% lower despite one more message (11 vs 10) because the check prompts/tokens were smaller.
- The Sol proxy is **not an invoice**: `openai/gpt-6.1-sol` has an empty price array. New Sol (4 planner messages)
  proxy $0.2162244 vs old planner Sol (2 messages) $0.0794696; the new planner used four turns (bootstrap, brief,
  decide, stop), so its Sol proxy is larger. The **old** Sol proxy is carried from the prior audit and is not
  recomputable here. Adding the proxy still leaves new 20.8% below the old comparable estimate.
- Old totals are lower bounds because its two timeout streams have no usage; new has no null-usage rows, so its
  priced-model total is complete, but Sol dollars are unknown. Baseline/direct-Sol session
  (`ses_e918ecc1dffe3LzsVPFwf7EAxM`: first answer 391.667 s, proxy $0.184198818) is excluded from both
  comparisons; those two values are **carried from the prior audit and not refetched here**, and it is a different,
  single-answer task — not comparable to a campaign with a checker, gate, ACCEPT and verify.
- Provider split: new ran 211 assistant messages on `opencode-go/deepseek-v4.1-flash` and 58 on
  `deepseek/deepseek-flash`; both catalog at 0.15/0.60/0.003, so the switch is price-neutral. Do not use the
  `opencode/deepseek-v4.1-flash` 0.30/1.20/0.006 entry — that provider was not used.

## 9. Independent checks

| check | result |
|---|---|
| Recursive parentID discovery / tree closure | **pass** — 17 sessions, 0 orphan children, 9 root children, 7 orchestrator children |
| Newest egg-drop root at `/home/alex/sources/skills` | **pass** — only `pdca-incremental` egg-drop root; newer top-level session is an unrelated opencode-config task |
| Unique assistant message IDs | **pass** — 0 duplicates across 17 sessions; resumed planner/baseline counted once |
| Assistant/tool counts | **pass** — 284 assistant, 263 tool-call + 21 stop, 344 unique tool parts, 7 failures |
| Flash + Gemini C2 formula | **pass** — 280/280 priced messages ≤1e-9; max 2e-17; C1/C3 fail |
| Session meta vs message cost | **pass with 1 documented hidden block** — 16/17 equal within 2e-17; root +$0.000038268 |
| Hidden block price | **pass** — 206/11/0/256 at 0.15/0.60/0.003 = $0.000038268 exactly |
| Manifest 27 inputs + aggregate | **pass** — 27/27 hashes match; aggregate `22d09176…` recomputes |
| Working vs frozen answer/checker/spec | **pass** — byte-identical |
| Child phases: overlap not double-counted | **pass** — 4,143.986 s additive, 89.147 s overlap, 4,363.369 s calendar, 308.530 s gaps |
| Root/orchestrator wait double count | **pass** — root own 30.540 s; child active kept separate from parent waits |
| Timeout/null usage | **pass** — 0 timeouts, 0 null-token/cost rows in this run |
| Sol dollar claim | **unknown by design** — no catalog price; proxy only ($0.2162244) |
| Design-doc access | **no explicit access found** — no `read`/`glob`/`grep` targets it and no assistant text discusses its content; doc birth 18:22:22Z (before final 18:30:58.715Z), modified 18:34:22Z, so timestamps do not settle availability; occurrences only in snapshot metadata / `git status`. Absence of a read is not proof of no context. |
| Old-run comparison values | **carried** — from prior audit `/tmp/opencode/retro-egg-drop-cost-20261024T161904Z`; not re-derived from these receipts |
| Assessor isolation | **pass on actual reads** — VERIFY did not read accept/rubric/status/charter; ACCEPT ran first |

## 10. Bottom line

1. **Root found:** `ses_e91154aa2ffeUmLHXVS5oWmQom` (build, `opencode-go/deepseek-v4.1-flash`, cwd
   `/home/alex/sources/skills`), 17:17:18.067–18:30:58.715Z, 17-session tree, 284 assistant messages, 344 tool parts.
2. **Wall:** 4,420.648 s = 1h13m40.6s (first user → final 4,420.486 s). No human waits; no timeouts; no compactions.
   First full-file answer write (draft, 23,142 chars; not the quality-approved answer) at 36m54.5s; ACCEPT at
   61m55.0s; verify at 71m10.6s; final at 73m40.5s. The ~62min figure is the artifact/ACCEPT milestone inside the
   73m40.5s campaign, not the whole lifecycle.
3. **Latency:** the largest **single dispatch** is D0 checker, 847.8 s (19.18%); the largest **composite group** is
   bootstrap, 958.2 s (21.68%, five sequential sub-spans). D1 answer 615.0 s (13.91% ≈ 10m15s, of which 208.37 s
   ≈ 3m28s write/edit); CHECK 547.3 s (12.38%); ACCEPT+verify+finalization 954.8 s (21.6%). These rows are **not** an
   exclusive additive partition: only BOOTSTRAP 958.190 + STEP-1 2,408.796 + POST-STEP 1,053.500 = 4,420.486 s
   partitions exactly; the step-1 sub-blocks contain the 89.147 s known-good ∥ D1 overlap. The “answer in ~2 min”
   status claim is a 126 s status window after the first full-file write, not the write time.
4. **Cost:** formula-verified **$1.382418556** known (messages $1.382380288 + root hidden $0.000038268), 71.8% Gemini.
   Sol (4 messages) is unpriced; proxy $0.2162244, not an invoice. No null-usage rows this run.
5. **Variant/provenance:** the campaign chose `pdca-coder` for the executable-artifact-dominated step; the orchestrator’s
   skill response was truncated at 677/1,426 lines and recovered by two reads from the tool-output store. The run used
   the **old host-installed** `pdca-incremental` (host sha `0c74eb78…`, no `pdca-general`), not the working-tree source
   and not an implemented `pdca-lensing` design. The design doc was created 18:22:22Z — before final delivery — and
   last modified 18:34:22Z; no explicit read/glob/grep of it was found, but that absence is not proof the model never
   received it as context. Delegated, no flat fallback; controller owner = root build session.
6. **Quality:** three separate Gemini check sessions; the two rubric readers did not see each other on actual read
   lists. The ACCEPT physics finding (claimed >200 g egg load) was **not rejected**; it was downgraded to a 1.0-point
   deduction and the campaign accepted at `min(9.100, 9.250)=9.100 ≥ 9.000` (threshold 9.000, not 9.1).
7. **Old vs new:** wall **0.5722×** (42.8% faster; **0.7568×** excluding old timeouts); known cost **0.7133×**;
   with Sol proxy **0.7924×**. Limits: different work volume, old totals exclude two null-usage timeout streams, Sol is
   proxy-only, old baseline excluded. Old-run and direct-baseline figures are **carried from the prior audit**
   (`retro-egg-drop-cost-20261024T161904Z`), not re-derived here; the timeout-excluded comparison is an arithmetic
   counterfactual, not a controlled experiment.
8. **Artifacts:** answer 392 lines / checker 1,097 / spec 289 / charter 384; 27/27 manifest inputs match; working ==
   frozen; gate 22/22 + 12/12 PASS; hashes in `hashes.json`, receipts in `receipts.sha256`.

### Transcript anchors

1. `msg_16eeab625001OdinRXWvHimrML` (17:17:18.268Z) — `skill pdca-incremental`, metadata `truncated:false`; campaign starts.
2. `msg_16f04c5c3001iKst5ocvCOwX06` (17:45:46Z) — D0 green selftest run after 3 red runs; `selftest.json` 22/22.
3. `msg_16f1ebce5001XiXnHf8pkEYcVV` (18:19:13Z) — ACCEPT S=9.100 with the >200 g physics finding;
   `msg_16f288aef001y8p3tlLexTF63R` (18:28:28Z) — VERIFY S=9.250, physics 9.0;
   `msg_16f2c090a001R6WVCdMX2UJx6u` (18:29:20Z) — STOP `min(9.100,9.250)=9.100≥9.000`.
