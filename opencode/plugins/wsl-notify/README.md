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

OpenCode V1, in `opencode.json`:

```json
{
  "plugin": ["wsl-notify"]
}
```

Or drop `index.js` into `<config>/plugins/wsl-notify.js` and let OpenCode
discover it locally. Options below need the configured form:
`plugins: [{ "package": "wsl-notify", "options": { … } }]`.

Pin a version (`wsl-notify@1.0.0`) to keep upgrades explicit.

## Options

Passed through the configured plugin form and read from `ctx.options` (V2):

```jsonc
{
  "plugins": [
    {
      "package": "wsl-notify",
      "options": {
        "graceMs": 500,
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
| `session.execution.succeeded` (subagent) | V2 | `Subagent finished`, only with `subagentComplete: true` |

Completion toasts carry the session title when one is known, falling back to
`opencode`. A finished turn that surfaces as both `session.execution.succeeded`
and `session.idle` produces one toast; the next `session.execution.started`
re-arms the session, so the following turn toasts again.

`session.execution.interrupted` (you pressed Esc) is deliberately silent: you are
already at the keyboard. Subagent sessions are detected from the session record's
`parentID`, so a subagent finishing does not report as a top-level session.

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

## Development

```sh
npm test        # drives setup() with synthetic events and a fake powershell
```

The smoke test asserts on the toasts the plugin would raise: one toast per
waiting permission, silence for a permission answered inside the grace window,
coalesced completion events, subagent suppression, and error text.

## License

[MIT](LICENSE) © 2026 Alexey Shirshov
