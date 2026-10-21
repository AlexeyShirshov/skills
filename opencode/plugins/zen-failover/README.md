# zen-failover

Server plugin for [OpenCode](https://opencode.ai) V2. When a subscription
provider's usage limit is hit, the whole server moves off that provider instead
of failing request by request — and moves back as soon as the plan answers
again.

- **Whole-server switch**: every agent bound to the degraded provider, the
  default model, and the session that hit the limit.
- **No false positives on bursts**: a bare per-minute `429` is retried; only an
  explicit quota wording or a `402` degrades a subscription.
- **Availability probe**: while degraded, the plan is asked once a minute; the
  first successful answer restores the original bindings.
- **Persisted**: a restart does not silently go back to a plan that is still out.

## Rules

| Source | Fallback |
| --- | --- |
| `opencode-go` (Go plan) | `deepseek/deepseek-flash` |
| `openai` (ChatGPT Plus/Pro token sharing) | `opencode/<id>` — the same Sol/Codex model on Console, `-fast` stripped |

Per-model overrides: `opencode-go/gemini-4-argon-contributor` → `opencode/gemini-4-argon`,
`opencode-go/kimi-k3` → `moonshotai/kimi-k3`.

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
   `ZEN_FAILOVER_PROBE_MS` (default 60s) the plugin creates a throwaway session
   on one of the source's original models, asks for one word, and removes it.
   A successful answer means the plan is usable again, so the transforms are
   disposed and the switched sessions return to their original models — without
   waiting for the cooldown. The probe also runs once at process start (capped
   by `ZEN_FAILOVER_PROBE_START_WAIT_MS`, default 5s).
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
| availability probe | every `60s` while degraded; also once at start (max 5s wait) |
| cooldown per source | `7d` (backstop); `ZEN_FAILOVER_RESET_<SOURCE>` = `5h`, `7d`, `month` |

Env overrides: `ZEN_FAILOVER_RULES`, `ZEN_FAILOVER_MAP`
(`src/model=dst/model,...`), `ZEN_FAILOVER_QUOTA_ONLY` (comma list, default
`openai`), `ZEN_FAILOVER_PROBE_MS` (`0` disables), `ZEN_FAILOVER_PROBE_ON_START`,
`ZEN_FAILOVER_PROBE_START_WAIT_MS`, `ZEN_FAILOVER_MIN_HITS`,
`ZEN_FAILOVER_WINDOW_MS`, `ZEN_FAILOVER_RESET_<SOURCE>`, `ZEN_FAILOVER_RESET_AT`
(tests, overrides all), `ZEN_FAILOVER_LOG`, `ZEN_FAILOVER_DEBUG=1`.

Log: `/tmp/opencode/zen-failover.log` (override with `ZEN_FAILOVER_LOG`).

## Install

Copy (or symlink) the plugin directory into the OpenCode config and let it
discover the entrypoint:

```sh
cp -r opencode/plugins/zen-failover ~/.config/opencode/plugins/
```

It is loaded from `~/.config/opencode/plugins/zen-failover/index.js` without a
`plugins` entry in `opencode.json(c)`. Takes effect on the next OpenCode start
(or plugin reload).

## Test

```bash
opencode/plugins/zen-failover/test/run.sh
```

Two mock subscription providers (Go on 18081, ChatGPT on 18083) answer `429`;
a mock fallback (18082) streams a reply. Six scenarios:

1. fresh Go limit → agents + session switched, retry answered by the fallback;
2. new process with the persisted state → first request goes straight to the
   fallback (zero Go hits);
3. continued session → stays on the fallback;
4. fresh ChatGPT-style limit → switches to its own fallback, Go untouched;
5. transient `429` on a quota-only source → retried, not switched;
6. the plan answers again → the startup probe restores the original bindings,
   and the next turn reaches the subscription.

The test never uses real providers or the real session database. Point it at a
candidate build with `ZEN_FAILOVER_PLUGIN=/path/to/plugin`.
