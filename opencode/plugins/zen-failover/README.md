# zen-failover

Server plugin for [OpenCode](https://opencode.ai) V2. When a subscription
provider's usage limit is hit, the whole server moves off that provider instead
of failing request by request — and moves back as soon as the plan answers
again.

- **Whole-server switch**: every agent bound to the degraded provider, the
  default model, and the session that hit the limit.
- **No false positives on bursts**: a bare per-minute `429` is retried; only an
  explicit quota wording or a `402` degrades a subscription.
- **Availability probe**: while degraded, the plan is asked once every five
  minutes — once per process, not once per loaded copy; the first successful
  answer restores the original bindings.
- **Persisted**: a restart does not silently go back to a plan that is still out.

## Rules

| Source | Fallback |
| --- | --- |
| `opencode-go` (Go plan) | `deepseek/deepseek-flash` |
| `openai` (ChatGPT Plus/Pro token sharing) | `opencode/<id>` — the same Sol/Codex model on Console, `-fast` stripped |

Per-model overrides: `opencode-go/gemini-4-argon` (and the older
`-contributor` id) → `opencode/gemini-4-argon`, `opencode-go/kimi-k3` → `moonshotai/kimi-k3`.

**Free models are exempt.** A model that costs nothing (every price tier is 0) or whose id ends in
`-free` is never switched off a degraded source, a limit it hits itself never degrades the source,
and a probe prefers a paid model. A free model does not consume the paid allowance, so it keeps
working while the plan is exhausted.

**But a free pool has its own cap.** When a free model answers `429` with a `retry-after` of a minute
or more (a daily quota — 17 hours was observed on `opencode-go/beam-free`), waiting it out stalls the
lane: the runtime honours up to 15 minutes per attempt. The plugin records the model as capped until
the provider's reset, moves the affected session and every agent bound to it onto the source's
fallback, and retries at once. Nothing is marked degraded — the source's allowance was never touched
— and when the cap expires the free binding returns on its own. Sessions already moved keep running
on the fallback until they end. Tune the threshold with `ZEN_FAILOVER_FREE_CAP_MIN_MS` (default
60000) and the longest recorded cap with `ZEN_FAILOVER_FREE_CAP_MAX_MS` (default 24 h).

## What it switches

1. **Every agent** whose model belongs to the degraded source, via a live agent
   transform.
2. **The default model**, if it belongs to that source.
3. **The session that hit the limit** via `session.switchModel`. Sessions already
   pinned to the source switch on their first limit error (the plugin API has no
   session enumeration).
4. The decision is persisted per source and re-applied on the next OpenCode
   start, so a restart does not silently go back.
5. **Availability probe**: while a source is degraded, every
   `ZEN_FAILOVER_PROBE_MS` (default 5 min) the plugin creates a throwaway
   session on one of the source's original models, asks for one word, and
   removes it. A successful answer means the plan is usable again, so the
   transforms are disposed and the switched sessions return to their original
   models — without waiting for the cooldown. The probe also runs once at
   process start (capped by `ZEN_FAILOVER_PROBE_START_WAIT_MS`, default 5s).
   The host loads the plugin once per location, so a process can hold several
   copies; the request itself is issued once per interval for the whole process
   and every copy reuses the verdict, so a degraded plan sees one rejection per
   interval instead of one per location.
6. The cooldown (`resetAt`) stays as a backstop: if probing is disabled or keeps
   failing, the source is restored when the cooldown expires.

Sources are independent: degrading `opencode-go` leaves `openai` (ChatGPT)
untouched, and vice versa.

## Trigger

- Two limit errors (`429`, `402`, `rate limit`, `quota`, `usage limit`, …) from
  the **same** source within five minutes, or one `402`.
- A single transient `429` is retried but does not switch.
- Sources in `ZEN_FAILOVER_QUOTA_ONLY` (default `openai`) need an explicit
  quota wording (`usage limit`, `quota`, `insufficient`, `weekly limit`, …)
  or a `402`. A subscription answers a per-minute burst limit with the same
  `429` status, so a bare rate limit there only gets retried — otherwise a
  short burst would move the whole server to the paid twin for a week.

## Defaults

| Option | Default |
| --- | --- |
| rules | `opencode-go=deepseek/deepseek-flash;openai=opencode/<id>` |
| quota-only sources | `openai` (bare 429 is transient there) |
| availability probe | every `5 min` while degraded (one request per process); also once at start (max 5s wait) |
| cooldown per source | `7d` (backstop); `ZEN_FAILOVER_RESET_<SOURCE>` = `5h`, `7d`, `month` |

Env overrides: `ZEN_FAILOVER_RULES`, `ZEN_FAILOVER_MAP`
(`src/model=dst/model,...`), `ZEN_FAILOVER_QUOTA_ONLY` (comma list, default
`openai`), `ZEN_FAILOVER_PROBE_MS` (`0` disables), `ZEN_FAILOVER_PROBE_ON_START`,
`ZEN_FAILOVER_PROBE_START_WAIT_MS`, `ZEN_FAILOVER_MIN_HITS`,
`ZEN_FAILOVER_WINDOW_MS`, `ZEN_FAILOVER_RESET_<SOURCE>`, `ZEN_FAILOVER_RESET_AT`
(tests, overrides all), `ZEN_FAILOVER_LOG`, `ZEN_FAILOVER_DEBUG=1`.

Log: `/tmp/opencode/zen-failover.log` (override with `ZEN_FAILOVER_LOG`).

## Install

```jsonc
// opencode.json(c)
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["zen-failover"]
}
```

```sh
opencode plugin add zen-failover
```

Or copy (or symlink) the plugin directory into the OpenCode config and let it
discover the entrypoint:

```sh
cp -r opencode/plugins/zen-failover ~/.config/opencode/plugins/
```

Then it is loaded from `~/.config/opencode/plugins/zen-failover/index.js` without a
`plugins` entry in `opencode.json(c)`. Takes effect on the next OpenCode start
(or plugin reload).

## Test

```bash
opencode/plugins/zen-failover/test/run.sh
```

Two mock subscription providers (Go on 18081, ChatGPT on 18083) answer `429`;
a mock fallback (18082) streams a reply. Ten scenarios:

1. fresh Go limit → agents + session switched, retry answered by the fallback;
2. new process with the persisted state → first request goes straight to the
   fallback (zero Go hits);
3. continued session → stays on the fallback;
4. free model (`beam-free`) on a degraded source → keeps its binding and is
   served by the subscription;
5. free model capped by its own pool → moved to the fallback, source untouched,
   and the free binding comes back once the reset passes;
6. fresh ChatGPT-style limit → switches to its own fallback, Go untouched;
7. transient `429` on a quota-only source → retried, not switched;
8. the plan answers again → the startup probe restores the original bindings,
   and the next turn reaches the subscription;
9. probe deduplication across plugin copies.

The test never uses real providers or the real session database. Point it at a
candidate build with `ZEN_FAILOVER_PLUGIN=/path/to/plugin`.
