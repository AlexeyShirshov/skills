# wsl-notify

Windows toast notifications for [OpenCode](https://opencode.ai) — on permission
requests, questions, session completion, and errors. Built for WSL (where the
Linux side has no notification daemon, but `powershell.exe` interop can raise a
real Windows toast) and works on native Windows too. Zero dependencies, one
entrypoint for OpenCode V1 and V2.

- Toast through the WinRT notification API, with sound, **non-activating**: it
  does not steal focus from the terminal.
- Zero dependencies, no build step, plain ESM, no Windows-side setup.
- Works with OpenCode V1 and V2 from the same entrypoint.
- One toast per request: neither the extra plugin instances of V2 nor re-emitted
  events produce duplicates.
- Permissions answered immediately (Auto Permissions) never reach the desktop.

## Requirements

- A Windows host with PowerShell: native Windows, or WSL with interop enabled.
- PowerShell is discovered automatically (see
  [PowerShell resolution](#powershell-resolution)). On a Linux or macOS host with
  no Windows interop there is nothing to raise a toast with, so notifications are
  skipped and one warning is logged.

## Install

OpenCode V2, in `opencode.json(c)`:

```jsonc
{
  "plugins": ["wsl-notify"]
}
```

OpenCode 1.18.x, in `opencode.json(c)`:

```json
{
  "plugin": ["wsl-notify"]
}
```

or from the CLI: `opencode plugin wsl-notify` — the command installs the package
and adds it to the config. 1.18.x resolves a package's `./server` subpath export
(or its `main`); this package declares both, and that is what makes the npm route
work there. The same file still loads from `<config>/plugins/wsl-notify.js`.

1.18.x never subscribes to events inside `setup` (its context carries no event
stream) — it drives everything through the `server()` hooks, which is what this
package returns: `session.idle` is the completion event, `session.error` a
failure, titles and `parentID` come from the session nested under
`properties.info`. Options do not reach that path, so use the `WSL_NOTIFY_*`
variables below.

Or, on V2, drop `index.js` into `<config>/plugins/wsl-notify.js` and let OpenCode
discover it locally. Options below need the configured form:
`plugins: [{ "package": "wsl-notify", "options": { … } }]`.

Pin a version (`wsl-notify@1.0.2`) to keep upgrades explicit. If a corporate npm
proxy gates packages by vulnerability scan and refuses a fresh one ("every
version … is vulnerable"), install from git or from a tarball path instead of the
registry — the plugin has no dependencies, so nothing else is fetched.

## Options

Passed through the configured plugin form and read from `ctx.options` (V2):

```jsonc
{
  "plugins": [
    {
      "package": "wsl-notify",
      "options": {
        "graceMs": 500,
        "minTurnMs": 500,
        "subagentComplete": false,
        "sound": {
          "permission": "Notification.IM",
          "question": "Notification.Default",
          "complete": "Notification.Default",
          "error": "Notification.Reminder"
        }
      }
    }
  ]
}
```

| Option | Default | Meaning |
| --- | --- | --- |
| `powershell` | auto | Path or command name of the PowerShell executable. |
| `graceMs` | `500` | How long to hold a permission toast, waiting for it to be answered. `0` notifies immediately. |
| `minTurnMs` | `500` | Skip the completion toast for a turn that ran shorter than this. `0` notifies for every finished turn. |
| `subagentComplete` | `false` | Also toast when a subagent session finishes. |
| `sound.permission` | `Notification.IM` | `ms-winsoundevent` name for the permission toast. |
| `sound.question` | `Notification.Default` | Sound for a question. |
| `sound.complete` | `Notification.Default` | Sound for a finished session. |
| `sound.error` | `Notification.Reminder` | Sound for a failed session. |
| `maxTitle` | `60` | Title truncation length. |
| `maxMessage` | `240` | Message truncation length. |

### Environment variables

| Variable | Meaning |
| --- | --- |
| `WSL_NOTIFY_POWERSHELL` | Same as the `powershell` option; wins over discovery. |
| `WSL_NOTIFY_GRACE_MS` | Same as the `graceMs` option, for setups where the plugin is discovered locally and cannot take options. |
| `WSL_NOTIFY_MIN_TURN_MS` | Same as the `minTurnMs` option, for locally discovered setups. |
| `WSL_NOTIFY_DEBUG=1` | Write every decision (`toast`/`skip`) to the debug log. |
| `WSL_NOTIFY_DEBUG_LOG` | Debug log path, default `$TMPDIR/wsl-notify.log`. |

Options win over the environment.

## Events

| Event | Generation | Toast |
| --- | --- | --- |
| `permission.asked` | V1, V2 | `Permission needs input`, after the grace window |
| `form.created` | V2 | Form title + first question; more questions counted with ` (+N)` |
| `question.asked` | V1 | Question header + first question |
| `session.execution.succeeded` | V2 | `Session finished` |
| `session.idle` | V1, transitional V2 | `Session finished` |
| `session.execution.failed` | V2 | `Error: <message>` |
| `session.error` | V1 | `Error: <message>`, the text read from `properties.error.data.message` |
| `session.execution.succeeded` (subagent) | V2 | `Subagent finished`, only with `subagentComplete: true` |

Completion toasts carry the session title when one is known, falling back to
`opencode`. A finished turn that surfaces as both `session.execution.succeeded`
and `session.idle` produces one toast; the next `session.execution.started`
re-arms the session, so the following turn toasts again.

`session.execution.interrupted` (you pressed Esc) is deliberately silent: you are
already at the keyboard. Subagent sessions are recognised from `session.created`,
whose payload carries `parentID` for a child session and omits it for a top-level
one, so a subagent finishing does not report as a top-level session. A session the
stream never announced — it predates the plugin, or was created before a reload —
is looked up in the background once (see
[Session metadata](#session-metadata-without-blocking-the-handler)) and counts as
top-level until that answers, so it is announced rather than silently dropped.

## Permission grace window

With `cli.json` → `session.permissions: "autoaccept"` (Auto Permissions) the TUI
answers permission requests the moment they appear — but OpenCode still emits
`permission.asked`, and for some tools (for example reads outside the project) it
emits several. Toasting those would announce requests that nothing is waiting on.

So a permission toast is not raised immediately. `permission.asked` schedules it
after `graceMs` (default 500 ms) and `permission.replied` for the same request
cancels it:

```text
t+0ms    permission.asked      → schedule toast at t+500ms
t+20ms   permission.replied    → cancel, nothing shown        (auto-answered)
t+500ms  (no reply)            → toast "Permission needs input"   (really waiting)
```

Trade-offs:

- A permission that is waiting for you appears about `graceMs` later. Half a
  second is imperceptible next to walking back to the machine; raise the value if
  your TUI is slow to auto-answer, or set it to `0`.
- A reply that arrives after the window has fired cannot un-toast; the toast is
  then simply stale. The window is the only knob for that.
- The decision is per request id, so an answered request never suppresses a later
  one.

## Short turns

`minTurnMs` (default 500 ms) applies the same idea to completion toasts: a turn
that began and finished inside the window was answered while you were still
looking at the terminal, so it never reaches the desktop either.

```text
t+0ms     session.execution.started    → remember the start
t+300ms   session.execution.succeeded  → 300ms < 500ms → silent
t+0ms     session.execution.started    → remember the start
t+40s     session.execution.succeeded  → toast "Session finished"
```

Without it, every `Enter` produces a toast within seconds, and a turn that hands
work to a subagent and returns can finish in hundreds of milliseconds — faster
than you can look away. With a threshold, a completion toast means what it should:
the work ran long enough that you may have walked off.

Details that matter:

- Only `complete` is filtered. A permission is a request waiting for you, and an
  error is worth knowing about even after two seconds.
- Duration is measured per session from `session.execution.started`, the same
  event that re-arms the completion key. When no start was seen — the plugin
  loaded mid-turn, the event was missed, the service restarted — the toast is
  raised anyway: a missing mark says nothing about the turn.
- `session.execution.succeeded` and the legacy `session.idle` are claimed before
  the check, so the paired event cannot slip past the window.
- Set `minTurnMs` to `0` to be told about every finished turn, or a larger value
  (for example `10000`) to hear only about work you could walk away from.

## Updating

Installed as a package, OpenCode keeps it in `~/.cache/opencode/packages/` with
its own `package.json`. Updates are never applied silently:

| Configured as | What OpenCode does | How to get a newer release |
| --- | --- | --- |
| `"wsl-notify"`, `@latest`, `^1.0.0` | checks for updates at startup, leaves the installed package alone | `opencode plugin check`, then `opencode plugin update wsl-notify` (or `opencode plugin update` for every package) |
| `"wsl-notify@1.0.0"` | the exact revision stays pinned | change the entry to the new version (`plugin update` skips exact revisions) |
| a local file or directory | there is no version to track | replace the file; `opencode service restart` if the change is not picked up |

```sh
opencode plugin list          # what is loaded, and from where
opencode plugin check         # which package plugins are outdated
opencode plugin update wsl-notify
```

Changes under the config directories reload automatically; `opencode service
restart` is the reliable fallback. Local plugins and exact package revisions are
skipped by `plugin update`.

## PowerShell resolution

In order:

1. The `powershell` option, then `WSL_NOTIFY_POWERSHELL`.
2. `PATH`, looking for `powershell.exe`, `pwsh.exe`, `powershell`, `pwsh`.
   Native Windows and WSL interop both put Windows directories here, so this
   usually resolves by itself.
3. Windows drive mounts on a WSL host, read from `/proc/mounts`
   (`drvfs`/`9p`/`cifs`): `<mount>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`,
   `<mount>/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe`, and
   `<mount>/Program Files/PowerShell/7/pwsh.exe`.

A path that does not exist falls back to discovery with one warning, so a stale
override does not silently disable notifications.

## How OpenCode delivers events

V2 loads the plugin once per location activation: several instances per server
process, each with its own module graph, all subscribed to the same event stream.
Notification events carry no location field, so one `permission.asked` reaches
every instance. The dedupe state is kept on `globalThis`, which is what keeps it
to one toast per request.

Toasts are non-activating by design: they never move focus away from the
terminal. The set of seen keys is capped at 512 entries, and a key is released as
soon as its request is replied to or cancelled.

### Session metadata without blocking the handler

The handler never *awaits* anything that talks to the server. A session read
(`ctx.session.get`) awaited inside the handler, while that same session is
finishing, does not come back — observed live on 2.0.28: the handler stops at the
call, no fallback timer fires, and the instance stays stuck for the life of the
service. Since that is exactly when a completion toast is raised, completions never
appeared at all.

Metadata comes from the event stream first:

| Event | Used for |
| --- | --- |
| `session.created` | `parentID` (subagent or top-level) and the title, when present; 1.18.x nests both under `properties.info` |
| `session.updated`, `session.renamed` | the title |
| `session.deleted` | forget the session |

A session the stream never announced — it predates the plugin, or was created
before a reload — gets its title and `parentID` from a **detached** read instead:
the first event mentioning an unknown session fires `ctx.session.get` and does not
await it, storing the answer if it arrives. Because it starts as the turn begins,
it has the whole turn to answer, which is why the completion toast still carries
the title. Nothing waits on it: if the read never settles, the toast is raised with
`opencode` as the title.

The map is capped like the seen keys, and a completion for a session with no record
is raised anyway: a missing entry means "unknown", not "subagent".

1.18.x has no `ctx.session` to prime from, so titles there come from these events
alone — which is why the session object nested under `properties.info` is read too.

## Development

```sh
npm test        # drives setup() with synthetic events and a fake powershell
```

The smoke test asserts on the toasts the plugin would raise (36 checks): one
toast per waiting permission, silence for a permission answered inside the grace
window, coalesced completion events, silence for a turn inside `minTurnMs`,
subagent suppression, error text, and the 1.18.x shapes (`properties.info`, and a
`setup` that must not fail without an event stream).

## License

[MIT](LICENSE) © 2026 Alexey Shirshov
