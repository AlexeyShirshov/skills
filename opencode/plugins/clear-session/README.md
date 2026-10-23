# opencode-clear-session

`/clear` for the [OpenCode](https://opencode.ai) V2 CLI: archive the current
session and start fresh. The conversation stays recoverable instead of being
deleted, and the archived session stops cluttering the session list.

```text
/clear     Clear session
/archive   Clear session
```

This is the V2 build of the V1 `clear-session.tsx` TUI plugin, moved to the V2
CLI-plugin API (`keymap.layer` + `client.session.update`) — V1 plugin modules do
not run in V2.

## What it does

1. Archives the session you are in: `client.session.update({ sessionID, archived: true })`.
2. Closes its tab, because an archived session no longer appears in the session list.
3. Drops you on the empty session screen. That screen *is* V2's new session — it
   becomes a real session with the first prompt, so `/clear` never leaves an
   empty record behind.

The command is registered as a global keymap layer: it shows up as `/clear`
and `/archive` and as **Clear session** in the command palette (`ctrl+p`). It is
enabled only inside a session. `/archive` is a second command with its own id
rather than a `slash.aliases` entry: V2 expands an alias into the canonical row
as well, so `/archive` would list the command twice. The `/clear` description
also avoids the word "archive" for the same reason — completion matches
descriptions.

## Why it reuses the built-in `session.clear` id

V2 already ships a built-in `session.clear` — the same title and the same
`/clear` slash name — but it only navigates home and leaves the session
**unarchived**. Registering a fresh command id therefore produced two `/clear`
rows: the built-in one and this one.

The plugin instead registers a layer with a higher `priority` and the built-in's
command id, so V2 resolves the conflict in favour of the plugin: one `/clear`
row, and it archives. Outside a session the command is disabled, and the
built-in one is shown as before.

## Requirements

- OpenCode V2 CLI (`opencode` 2.x).
- Depends only on the host's `@opencode/plugin` TUI API; no runtime dependencies.

## Install

A **CLI-only** plugin: it runs in the terminal and has no server entrypoint. Add
it to `cli.json` (not to `opencode.json(c)`):

```jsonc title="~/.config/opencode/cli.json"
{
  "plugins": ["./plugins/clear-session"]
}
```

Or, once the package is published, by name:

```jsonc
{ "plugins": ["opencode-clear-session"] }
```

CLI-only plugins stay active when the CLI is connected to a remote server,
because they run locally in the terminal.

## Options

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `newSession` | boolean | `true` | Set to `false` to archive and stay on the archived session (its tab is kept) instead of starting fresh. |
| `enabled` | boolean | `true` | Set to `false` to keep the package configured but unloaded. |

```jsonc title="~/.config/opencode/cli.json"
{
  "plugins": [
    { "package": "./plugins/clear-session", "options": { "newSession": false } }
  ]
}
```

## Where the archived session goes

Archiving is not deleting: the session keeps every message, its title and its
cost, and the API can list and restore it.

```sh
opencode api get '/api/session?archived=true'
opencode api patch /api/session/<sessionID> --data '{"archived":false}'
```

The TUI has no archive browser yet, so a restored session shows up in the session
list again.

**The session list still shows archived sessions** in OpenCode 2.1.3: the
`Ctrl+O` picker renders `GET /api/session` without the `archived` filter, so an
archived session stays visible next to active ones until it is deleted
(tracked upstream: [anomalyco/opencode#58364](https://github.com/anomalyco/opencode/issues/58364)).
Archiving therefore keeps the conversation recoverable, but it does not tidy the
list yet.

## Notes and limitations

- Archiving is a server-side update; it does **not** interrupt a running turn.
  If you clear while the model is still working, that turn keeps running in the
  background — interrupt it first (`escape`) if you do not want that.
- If the server rejects the archive, the command shows an error toast and leaves
  the session, its tab and your position untouched.
- On a host without session tabs the tab step is skipped; the rest is unchanged.
- The single-row `/clear` relies on the built-in id `session.clear`. If a future
  V2 renames it, the plugin keeps working as a standalone `/clear` but may show
  up next to the renamed built-in.

## Local development

CLI plugins are discovered from `<config>/plugins/<name>/`, so the same package
layout works from disk:

```text
~/.config/opencode/plugins/clear-session/
├── package.json   # exports: { "./tui": "./tui.tsx" }
├── tui.tsx        # Plugin.define({ id, setup }) — keymap layer
└── clear.ts       # archive / close tab / navigate, plain TS
```

```jsonc title="~/.config/opencode/cli.json"
{ "plugins": ["./plugins/clear-session"] }
```

Tests exercise the decision logic against a fake host — no terminal, no server:

```sh
npm test   # node --experimental-strip-types test/smoke.mjs
```

## License

MIT
