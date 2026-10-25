# Egg-drop PDCA — raw API telemetry audit

Generated: 2026-10-24T16:26:46.264Z · receipts: `/tmp/opencode/retro-egg-drop-cost-20261024T161904Z/` (`raw/`, `results.json`, scripts `audit.py`, `analyze.py`).

Method: V2.1.3 built-in `opencode api get` auth flow (no credential files, no server restart); all JSON stored verbatim; all arithmetic in Python `Decimal`. No repo/config edits, no tests, no commits.

Pagination: `/api/session/:id/message` defaults to 50 rows; `?limit=200&order=asc` returns the full set (e.g. DO3 = 76 messages, not 50). Sessions discovered recursively via `GET /api/session?parentID=<id>`.

## 1. Discovery — exactly 15 cycle sessions (root + orchestrator + 13 children)

| phase | session | parent | agent | model | start (UTC) | end (UTC) | wall s |
|---|---|---|---|---|---|---|---:|
| ROOT | `ses_e91cedfe2ffenrzGxquhj3MxgF` | `—` | build | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T13:54:35.717Z | 2026-10-24T16:03:21.138Z | 7,725.421 |
| ORCH | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | `ses_e91cedfe2ffenrzGxquhj3MxgF` | pdca-orchestrator | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T13:55:12.028Z | 2026-10-24T16:03:15.566Z | 7,683.538 |
| facts | `ses_e91ce1f17ffeW0JLtOdrvVhZmJ` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-scout | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T13:55:25.043Z | 2026-10-24T13:56:02.855Z | 37.812 |
| planner | `ses_e91cd38a3ffexwn61J3gbHi056` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-planner | `openai/gpt-6.1-sol` | 2026-10-24T13:56:24.037Z | 2026-10-24T14:17:52.957Z | 1,288.920 |
| gate | `ses_e91b93889ffebFqr3Klw0zGOOL` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T14:18:14.785Z | 2026-10-24T14:20:06.657Z | 111.872 |
| DO1 | `ses_e91b6d109ffeKt9My5Zm9SdzMv` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T14:20:52.353Z | 2026-10-24T14:33:31.340Z | 758.987 |
| OBS1 | `ses_e91ab03d6ffeWP0BLUQ6hZPg9l` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-scout | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T14:33:45.794Z | 2026-10-24T14:38:23.394Z | 277.600 |
| CHECK1 | `ses_e91a64e18ffepVBxGQFF558ZPA` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-check | `opencode/gemini-4-argon` | 2026-10-24T14:38:54.462Z | 2026-10-24T14:46:03.126Z | 428.664 |
| DO2 | `ses_e919f6995ffeWr2NAQ97dO4SZB` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T14:46:26.171Z | 2026-10-24T15:03:05.084Z | 998.913 |
| OBS2 | `ses_e918ff3ebffeEvJ446P71xP29z` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-scout | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T15:03:19.335Z | 2026-10-24T15:10:09.036Z | 409.701 |
| CHECK2 | `ses_e91894bc6ffeJRF6NWCR3yyaNU` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-check | `opencode/gemini-4-argon` | 2026-10-24T15:10:35.594Z | 2026-10-24T15:16:55.794Z | 380.200 |
| DO3 | `ses_e91833b12ffeLdHdwBrz7W3DFa` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T15:17:13.099Z | 2026-10-24T15:46:50.273Z | 1,777.174 |
| OBS3 | `ses_e9167e340ffezhDS1FAos3GVhl` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-scout | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T15:47:05.034Z | 2026-10-24T15:54:19.557Z | 434.523 |
| CHECK3 | `ses_e9160c353ffespSliv7OyEsq0b` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-check | `opencode/gemini-4-argon` | 2026-10-24T15:54:51.956Z | 2026-10-24T16:00:00.676Z | 308.720 |
| ACT | `ses_e915bde0cffeZltHAj2W69KAF6` | `ses_e91ce51ecffeHc9ZSZNdxKC8Qq` | pdca-executor | `opencode-go/deepseek-v4.1-flash` | 2026-10-24T16:00:12.796Z | 2026-10-24T16:03:09.596Z | 176.800 |

Baseline (not a child): `ses_e918ecc1dffe3LzsVPFwf7EAxM`, agent `build`, `openai/gpt-6.1-sol`, 15:04:35.059→15:13:38.711Z, wall 543.652 s.

**Count check:** 15 = 1 root + 1 orchestrator + 13 direct children. No extra nested child sessions. The prior scout's '16 sessions' is consistent only if the **baseline top-level Sol session** is counted as a 16th audited session; it is not in the cycle family.

## 2. Message and tool counts (deduplicated by message id)

| scope | sessions | assistant | user | synthetic | idle | all messages | tool parts | failed tools |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cycle family | 15 | 348 | 15 | 2 | 15 | 380 | 411 | 7 |
| baseline | 1 | 6 | 2 | 0 | 2 | 10 | 4 | 0 |
| **all audited** | **16** | **354** | **17** | **2** | **17** | **390** | **415** | **7** |

- Duplicate message IDs across the 16 sessions: **0**.

- The scout's **354 assistant messages** equals the *all-audited* count (family 348 + baseline 6), not the family count. Its per-role 'calls 372' and per-role tool sum '514' do not reproduce under assistant-message, tool-part, or assistant+user counts; they are not used here.

- Tool kinds (all 415): `shell` 189 (182 ok + 7 error), `read` 121, `edit` 38, `grep` 25, `subagent` 14, `write` 10, `glob` 9, `execute` 7, `skill` 2. All failures are `shell`.

## 3. Per-role totals — message-level (family only)

| role | sessions | unique assistant msgs | input | output | reasoning | cache read | reported msg cost $ | hidden session cost $ | session wall s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pdca-check | 3 | 10 | 195,388 | 36,037 | 53,349 | 231,608 | 1.3077968 | 0 | 1,117.584 |
| pdca-executor | 5 | 243 | 794,511 | 181,092 | 153,214 | 28,102,656 | 0.404068218 | 0 | 3,823.746 |
| pdca-scout | 4 | 71 | 449,709 | 42,531 | 105,441 | 4,838,784 | 0.170755902 | 0 | 1,159.636 |
| pdca-orchestrator | 1 | 16 | 136,036 | 27,620 | 12,185 | 1,130,624 | 0.047680272 | 0 | 7,683.538 |
| build | 1 | 6 | 31,179 | 2,560 | 1,483 | 175,488 | 0.007629114 | 0.000036018 | 7,725.421 |
| pdca-planner | 1 | 2 | 228 | 4,716 | 3,106 | 7,936 | 0 | 0 | 1,288.920 |

- `pdca-planner` ran on `openai/gpt-6.1-sol`; its reported message cost is **$0** because the OpenAI model entry in `/api/model` has an empty `cost` array. That $0 is *not* evidence of free usage. `pdca-check` (Gemini) is the dominant known cost: $1.307796800.

- Role wall times for `build` (root) and `pdca-orchestrator` include subagent waiting; they are not active compute. See §6.

## 4. Per-child-phase totals

### 4.1 Timing (session API `time.created` → `time.updated`/idle)

The session object exposes `time.created`, `time.updated`, `time.idle`, `time.viewed`; there is no `completed` field. `updated` is the last-activity marker (idle is typically 5 ms later). These are transcript/API times, not the manual status-file ledger times.

| phase | session | wall s | gap before s | assistant msgs | tools (failed) |
|---|---|---:|---:|---:|---:|
| facts | `ses_e91ce1f17ffeW0JLtOdrvVhZmJ` | 37.812 | 0.000 | 5 | 11 (1) |
| planner | `ses_e91cd38a3ffexwn61J3gbHi056` | 1,288.920 | 21.182 | 2 | 0 (0) |
| gate | `ses_e91b93889ffebFqr3Klw0zGOOL` | 111.872 | 21.828 | 11 | 12 (0) |
| DO1 | `ses_e91b6d109ffeKt9My5Zm9SdzMv` | 758.987 | 45.696 | 64 | 64 (0) |
| OBS1 | `ses_e91ab03d6ffeWP0BLUQ6hZPg9l` | 277.600 | 14.454 | 15 | 25 (2) |
| CHECK1 | `ses_e91a64e18ffepVBxGQFF558ZPA` | 428.664 | 31.068 | 3 | 11 (0) |
| DO2 | `ses_e919f6995ffeWr2NAQ97dO4SZB` | 998.913 | 23.045 | 71 | 70 (0) |
| OBS2 | `ses_e918ff3ebffeEvJ446P71xP29z` | 409.701 | 14.251 | 25 | 34 (1) |
| CHECK2 | `ses_e91894bc6ffeJRF6NWCR3yyaNU` | 380.200 | 26.558 | 3 | 11 (0) |
| DO3 | `ses_e91833b12ffeLdHdwBrz7W3DFa` | 1,777.174 | 17.305 | 73 | 78 (1) |
| OBS3 | `ses_e9167e340ffezhDS1FAos3GVhl` | 434.523 | 14.761 | 26 | 35 (2) |
| CHECK3 | `ses_e9160c353ffespSliv7OyEsq0b` | 308.720 | 32.399 | 4 | 11 (0) |
| ACT | `ses_e915bde0cffeZltHAj2W69KAF6` | 176.800 | 12.120 | 24 | 24 (0) |
| **13 children** | — | **7,389.886** | **274.667 (total gaps)** | **326** | **386 (7)** |

Children are strictly serial (`end[i] <= start[i+1]` for all 13: **True**). Additive child wall **7,389.886 s**; calendar span **7,664.553 s**; gaps **274.667 s**.

### 4.2 Tokens and cost

| phase | assistant msgs | input | output | reasoning | cache read | reported msg cost $ | session meta cost $ |
|---|---:|---:|---:|---:|---:|---:|---:|
| ROOT | 6 | 31,179 | 2,560 | 1,483 | 175,488 | 0.007629114 | 0.007665132 |
| ORCH | 16 | 136,036 | 27,620 | 12,185 | 1,130,624 | 0.047680272 | 0.047680272 |
| facts | 5 | 15,721 | 4,704 | 1,338 | 72,192 | 0.006199926 | 0.006199926 |
| planner | 2 | 228 | 4,716 | 3,106 | 7,936 | 0 | 0 |
| gate | 11 | 39,263 | 10,377 | 5,823 | 282,624 | 0.016457322 | 0.016457322 |
| DO1 | 64 | 143,140 | 55,734 | 44,365 | 7,045,632 | 0.102667296 | 0.102667296 |
| OBS1 | 15 | 75,530 | 12,879 | 24,004 | 796,928 | 0.035850084 | 0.035850084 |
| CHECK1 | 3 | 48,110 | 14,651 | 20,352 | 49,331 | 0.4511831 | 0.4511831 |
| DO2 | 71 | 212,593 | 61,064 | 57,787 | 10,846,080 | 0.13573779 | 0.13573779 |
| OBS2 | 25 | 146,861 | 12,744 | 42,384 | 2,025,856 | 0.061183518 | 0.061183518 |
| CHECK2 | 3 | 70,160 | 12,729 | 17,401 | 62,670 | 0.447887 | 0.447887 |
| DO3 | 73 | 294,151 | 43,952 | 40,354 | 8,742,144 | 0.120932682 | 0.120932682 |
| OBS3 | 26 | 211,597 | 12,204 | 37,715 | 1,943,808 | 0.067522374 | 0.067522374 |
| CHECK3 | 4 | 77,118 | 8,657 | 15,596 | 119,607 | 0.4087267 | 0.4087267 |
| ACT | 24 | 105,364 | 9,965 | 4,885 | 1,186,176 | 0.028273128 | 0.028273128 |
| **family total** | **348** | **1,607,051** | **294,556** | **328,778** | **34,487,096** | **1.937930306** | **1.937966324** |
| baseline | 6 | 18,785 | 6,143 | 7,242 | 121,728 | 0 | 0.000606018 |

`session meta cost` equals the sum of message costs for 14/15 family sessions within float noise. The only family exception is the root (+0.000036018); the baseline separately has +0.000606018. Each is a hidden, flash-priced usage block not present as a returned message (see §5.4).

## 5. Token semantics and cost arithmetic

### 5.1 Message token schema

- Keys observed on message tokens: `cache, input, output, reasoning`; cache keys: `read, write`. There is **no `total` field** at message or session level. All 352 non-null token objects carry every component key; 2 messages (both timeouts) have `tokens: null` — these are **unknown, not zero**, and are excluded from sums (so sums are lower bounds).

- Message shape: `type=assistant` carries `id, time{created,streamed,completed}, agent, model{providerID,id,variant}, content[], finish, cost, tokens`; `content[]` holds `reasoning` / `text` / `tool` parts, and a tool part carries `name, time{created,ran,completed}, state{status,input,error,content}`. User messages are separate `type=user` rows with `text/files/agents`; `idle` and `synthetic` rows are not assistant turns and are excluded from token/cost sums.

- Cost is **per message, not cumulative**: summing the 346 family messages with non-null `cost` reproduces the session total for 14/15 family sessions; only the root differs (hidden block below). The exact cost fit (below) implies the components are disjoint: `input` = uncached prompt, `cache.read` = prompt served from cache, `output` = visible completion, `reasoning` = hidden reasoning billed at the **output** rate. `cache.write` is 0 everywhere here.

- Derived (not API fields): prompt tokens processed = `input + cache.read`; output-rate tokens = `output + reasoning`. Do not sum all four as one 'total'.

### 5.2 Prices used (from `GET /api/model`, per 1M tokens)

| provider/model | input $ | output $ | cache read $ | cache write $ |
|---|---:|---:|---:|---:|
| `opencode-go/deepseek-v4.1-flash` | 0.15 | 0.60 | 0.003 | 0 |
| `opencode/gemini-4-argon` | 2.00 | 10.00 | 0.10 | 0 |
| `openai/gpt-6.1-sol` | — (empty) | — | — | — |

`opencode/gpt-6.1-sol` is a *different provider* listed at 2/10/0.1; it is not the OpenAI price and is not used as an invoice.

### 5.3 Formula verification per priced message (tolerance 1e-9 USD)

C1 = input·p_in + output·p_out + cache·p_cache  
C2 = input·p_in + (output + reasoning)·p_out + cache·p_cache  
C3 = input·p_in + (output − reasoning)·p_out + cache·p_cache

| model | priced msgs | C1 matches | C1 maxdiff $ | C2 matches | C2 maxdiff $ | C3 matches | C3 maxdiff $ |
|---|---:|---:|---:|---:|---:|---:|---:|
| flash | 335 | 84 | 0.016301400 | **335** | **3E-18** | 84 | 0.032602800 |
| gemini | 10 | 0 | 0.2001000 | **10** | **1E-17** | 0 | 0.4002000 |

- **Flash:** C2 matches all 335 priced messages; max deviation 3e-18 USD (JSON-float noise). C1/C3 match only the 84 messages whose `reasoning = 0`; max deviations 0.0163014 / 0.0326028. **Verified formula: C2.**

- **Gemini:** C2 matches all 10 priced messages; max deviation 1e-17. C1/C3 match none; max deviations 0.2001 / 0.4002. **Verified formula: C2.**

- **Sol:** 8 messages, of which 7 have `cost = 0` and 1 has `cost = null`; the OpenAI price array is empty. **No formula can be verified and no dollar invoice can be inferred.** Because C2 is unverified for this provider, no Sol dollar estimate is asserted. For reference only (not a validated estimate): 8 messages at `opencode/gpt-6.1-sol` 2/10/0.1 would be **$0.2630624**, before any usage lost in the planner timeout; this is neither an invoice nor an OpenAI price.

- The CHECK example in the prior scout (input 265,548 / output 48,766 / reasoning 70,950 / cache 294,278 → $1.7576838) is internally inconsistent. The true three CHECK sessions total 195,388 / 36,037 / 53,349 / 231,608, which at 2/10/0.1 gives exactly **$1.3077968** — the cost the scout quoted. So its cost came from message-level data while its token totals did not.

### 5.4 Session aggregate vs visible-message sum

| session | delta input | delta output | delta reasoning | delta cache read | delta cost $ |
|---|---:|---:|---:|---:|---:|
| `ses_e91cedfe2ffenrzGxquhj3MxgF` (build) | 203 | 8 | 0 | 256 | 0.0000360179999999999 |
| `ses_e918ecc1dffe3LzsVPFwf7EAxM` (build) | 3,979 | 14 | 0 | 256 | 0.000606018 |

Both hidden blocks price exactly at flash rates: root 203/8/0/256 → $0.000036018; baseline 3,979/14/0/256 → $0.000606018. They are real session-level usage with no returned assistant message; the API does not identify the call. The baseline's entire reported `cost` is this hidden block, not its Sol messages.

### 5.5 Cost totals (known vs unknown)

| component | USD | status |
|---|---:|---|
| flash messages (335 priced) | 0.630133506 | formula-verified against reported per-message cost |
| Gemini messages (10 priced) | 1.307796800 | formula-verified |
| Sol messages (8) | 0 | **unknown** — unpriced provider, all reported costs 0/null |
| root hidden flash block | 0.000036018 | session aggregate only |
| **family known reported total** | **1.937966324** | lower bound; excludes Sol and 2 timed-out calls |
| baseline hidden flash block | 0.000606018 | session aggregate only |
| baseline Sol messages | 0 | **unknown** |

Sol token totals are clear even though dollars are not:

| Sol scope | assistant msgs | input | output | reasoning | cache read | cost |
|---|---:|---:|---:|---:|---:|---|
| baseline | 6 | 18,785 | 6,143 | 7,242 | 121,728 | 0 |
| planner | 2 (1 has `tokens=null`) | 228 | 4,716 | 3,106 | 7,936 | 0 / null |
| **Sol total** | **8** | **19,013** | **10,859** | **10,348** | **129,664** | **unknown** |

Actual invoice **cannot** be established from this API: OpenAI has no price, and both timed-out calls have `tokens: null`, `cost: null`. The defensible statement is: *known formula-consistent spend $1.937966324 for the cycle + $0.000606018 hidden baseline usage; Sol usage and two timeout usages are unbilled/unknown in the data.*

## 6. Wall-time decomposition (actual API times)

- Root wall **41.883 s own** + orchestrator wall **7,683.538 s** = 7,725.421 s. Root own = 36.311 s before dispatch + 5.572 s after orchestrator.

- Orchestrator wall **7,683.538 s** = 13 children **7,389.886 s** + inter-phase gaps **274.667 s** + residual **18.985 s**.

- 13-child additive wall **7,389.886 s** (2h03m09.9s); calendar child span **7,664.553 s** (2h07m44.6s). Baseline is **not** additive: it ran concurrently with OBS2/CHECK2 (15:04:35→15:13:38 inside 15:03:19→15:16:55).


### 6.1 The two provider timeouts

| call | session | message | created→completed | duration s | error | tokens | cost |
|---|---|---|---|---:|---|---|---|
| planner attempt 1 | `ses_e91cd38a3ffexwn61J3gbHi056` | `msg_16e32c784001ucV6PLkuqUhXWP` | 13:56:24.084→14:16:03.329 | **979.245** | `provider.transport`: Timed out waiting for response data (HTTP 200) | null | null |
| DO3 mid-call | `ses_e91833b12ffeLdHdwBrz7W3DFa` | `msg_16e8096d7001vadh9h0AvDu1KM` | 15:21:23.438→15:36:28.675 | **905.237** | `provider.transport`: Timed out waiting for response data (HTTP 200) | null | null |

- Planner phase **1,288.920 s** = 979.245 s timeout + 307.936 s successful retry (`msg_16e41bf39001f5TIvVSZ1kFdlR`, 14:16:05.021→14:17:52.957) + 1.739 s handoff. The initial call alone was **16.32 min**; the successful call was **5.13 min**.

- DO3 phase **1,777.174 s**, of which **905.237 s (50.9%)** is the timeout; the remaining 72 assistant messages take 871.937 s.

- Combined timeout time **1,884.482 s = 31m24.5s = 24.4%** of the 7,725.421 s root wall. Both are unbilled in the data (no usage), so both cost and time are lower bounds.

### 6.2 Tool overhead

- 14 `subagent` parts are parent-wait spans, not compute: root→orchestrator 7,683.570 s + orchestrator→13 children 7,390.694 s = 15,074.264 s. They duplicate child wall and are excluded from additive time.

- Non-subagent tools: 401 parts, summed duration **41.700 s** family + **0.968 s** baseline; individual non-subagent tools average tens of ms. So tool execution is negligible against 2h08m; the wall is model latency plus the two timeouts.

- 7 failures: 6 × `permission.rejected` shell (facts 1, OBS1 2, OBS2 1, OBS3 2; each 0.014–0.07 s) and 1 × `provider.transport` shell part in the DO3 timeout (no ran→completed duration). The permission failures are policy denials, not infrastructure faults.

## 7. Baseline direct Sol session

| segment | from | to | duration |
|---|---|---|---:|
| first user → first complete deliverable | 15:04:35.423 | 15:11:07.090 (`msg_16e753999…`, `finish=stop`) | **391.667 s (6m31.7s)** |
| user wait before clarification | 15:11:07.090 | 15:13:27.714 | 140.624 s |
| clarification → reply | 15:13:27.714 | 15:13:38.711 (`msg_16e7954b3…`, `finish=stop`) | **10.997 s** |
| session wall | 15:04:35.059 | 15:13:38.711 | 543.652 s |

Tokens: 18,785 input / 6,143 output / 7,242 reasoning / 121,728 cache read. Reported Sol message cost: $0 (unpriced). Session meta cost $0.000606018 is the hidden flash block, not Sol. Illustrative Sol-only list estimate at 2/10/0.1: **$0.1835928** (baseline) — not an invoice.

## 8. OBS3 evidence — the non-author observation did execute

`OBS3 = ses_e9167e340ffezhDS1FAos3GVhl`, agent `pdca-scout`, parent `pdca-orchestrator`, 26 assistant messages, 35 tool parts (2 shell permission denials), 15:47:05→15:54:19Z, $0.067522374.

It read the frozen n=3 attempt directly: `answer.md` lines 1–320, 321–650, 651–921 (all 921); `egg-drop-test.md` 1–290; `.pdca/status/egg-drop-1.md`; `manifest.json`; `probe.json`; `physics.json`; `constraints.json`; `content.json`; `structure.json`; `selftest.json`; `checks-transcript.log`; `review.md`; and `verify.py:1318–1466`. It ran 4 `execute` arithmetic blocks and 11 greps, and returned 18,228 characters of findings.

Exact quotes from its final message (`msg_16e9d9594001H4Ao0dQwIcbdJY`, 18,228-char text part):

> "Runtime limitation: `bash`/`shell` is **denied** in this session (permission.rejected) and Code Mode has no filesystem access, so I used the JS `execute` runtime for all arithmetic and could not run `python3`. Physically independent of `verify.py`."

> "**Transcript**: carries sha256 for document and checker (`:5, :58-59`, same strings as `manifest:11, :16`) and a real 50-row hand recompute with `answer.md` line pointers (`:61-112`) … I reproduced 25 of those rows independently — **no discrepancy**."

> "**UNVERIFIED**: the sha256 values themselves and the "unchanged after the last edit / before every run" claim — I cannot hash or stat files here (`shell` denied, Code Mode has no FS); file line count **921 confirmed** by read …"


**Verdict on the scout's 'no observer' claim:** false. There are three distinct non-author `pdca-scout` observation sessions (OBS1 `ses_e91ab03d…`, OBS2 `ses_e918ff3e…`, OBS3 `ses_e9167e34…`), each with its own transcript and findings. OBS3 did observe the frozen content and recompute independently (it returned PARTIAL on R6/R14/R18 and two value-level misses, so it was not a rubber stamp); what it could **not** do is cryptographically bind the file to the recorded hash, because shell/hash access was denied. So the correct status is **observed, read-only, hash-binding unverified**, not 'no observer'.

## 9. Status-file vs transcript mismatch

| source | timestamp | evidence |
|---|---|---|
| Root transcript idle (actual end) | **2026-10-24T16:03:21.138Z** | `GET /api/session/ses_e91cedfe…` `time.updated=1792857801138`; idle message `msg_16ea701b7…` 16:03:21.143Z |
| ACT child end | 16:03:09.596Z | `ses_e915bde0c…` `time.updated` |
| Orchestrator end | 16:03:15.566Z | `ses_e91ce51ec…` |
| Status ledger ACT line | 2026-10-24T16:05:00Z | `.pdca/status/egg-drop-1.md:360` |
| Status §18 | "Verified at ACT (2026-10-24T16:05:00Z)" | `.pdca/status/egg-drop-1.md:556` |
| Status file mtime | 2026-10-24T16:02:37.311Z | `stat` (21:02:37 +0500) |

The ledger's 16:05:00Z is **98.862 s after** the parent's actual idle and **142.689 s after** the file's own mtime; it is a manual timestamp, not a transcript timestamp. History is reported as-is; no file was changed.

## 10. Independent validation checks

| check | result |
|---|---|
| Recursive parentID discovery | **pass** — 15 family sessions; 13 direct children; no extra levels |
| Unique message IDs | **pass** — 0 duplicates across 16 sessions |
| Assistant count | **pass** — 348 family / 354 incl baseline; per-role sums 348 |
| Tool parts | **pass** — 411 family + 4 baseline = 415; 7 failures |
| Flash C2 formula | **pass** — 335/335 within 1e-9; max 3e-18 |
| Gemini C2 formula | **pass** — 10/10 within 1e-9; max 1e-17 |
| Session vs message cost | **pass with 2 documented exceptions** — 14/15 equal; root +0.000036018; baseline +0.000606018 hidden |
| Child phases serial | **pass** — 13/13 non-overlapping; gaps 274.667 s |
| Root/orch double-count avoided | **pass** — root own 41.883 s; orch 7,683.538 s includes child sum + gaps |
| Sol dollar claim | **fail by design / unknown** — no price; report token totals, no invoice |
| Timeout usage | **unknown** — both `tokens/cost = null`; all totals are lower bounds |
## 11. Bottom line

- Cycle wall (actual): root **2h08m45.4s**; 13 child phases additive **2h03m09.9s**; orchestrator own/gap **4m53.7s**; root own **41.9s**.

- Known formula-consistent cost: **$1.937966324** cycle (flash $0.630133506 + Gemini $1.307796800 + hidden $0.000036018). Baseline hidden $0.000606018. Sol 8 messages and two timed-out calls are unknown; true spend is higher or equal.

- Biggest avoidable overhead: two provider timeouts, **31m24.5s (24.4% of root wall)**, both with no usage recorded.

- Observation: OBS3 was a real non-author execution; frozen binding is content-level, **hash-level UNVERIFIED**.

- Prior scout's session count (16) only works by including the baseline; its 372/514 call/tool aggregates and its token totals are not reproducible. This report supersedes them.


## Appendix — receipts and independent re-sum

- Raw API receipts: `/tmp/opencode/retro-egg-drop-cost-20261024T161904Z/raw/` (16 session JSONs, 16 message JSONs, 15 children queries, `models.json`, `sessions_all.json`, `family.json`).
- Recomputed bundle: `results.json`; human report: `report.md`; scripts: `audit.py` (fetch), `analyze.py` (arithmetic), `report_gen.py`.
- Independent re-sum over raw messages (separate pass) matched `results.json`: input 1,625,836; output 300,699; reasoning 336,020; cache read 34,608,824; message cost 1.937930306; tools 415; failures 7; missing usage 2; zero-cost 7.
- Family-only split: input 1,607,051; output 294,556; reasoning 328,778; cache read 34,487,096; message cost 1.937930306; assistant 348; tools 411.
- SHA-256: `results.json` `e5427ec2c3b44c4c8ba728e0259caf914370aad818aac112fe3b8da88d63bb58`; the current `report.md` and `results.json` hashes are in `receipts.sha256` (the report cannot contain its own post-edit hash).
- No repository/config file was written; only this `/tmp/opencode/retro-egg-drop-cost-20261024T161904Z/` directory.
