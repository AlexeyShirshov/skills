# opencode-git-status-v1

[![npm](https://img.shields.io/npm/v/opencode-git-status-v1)](https://www.npmjs.com/package/opencode-git-status-v1)

Git working-tree status in the **OpenCode V1** CLI sidebar footer — current branch,
ahead/behind, staged, modified, untracked, conflicts and stashes on one line, updated
while you work.

```text
~/sources/opencode-config:main ↑1 ↓2 !1 -3 +4 ±5 ~6 ?7 ⚑2
```

This is the V1 build of the plugin. For OpenCode V2 use
[`opencode-git-status`](https://www.npmjs.com/package/opencode-git-status): the two are
separate packages because V1 and V2 use different plugin APIs.

- One line: path, branch, then only the non-zero counters.
- Counters follow `git status --porcelain=v2` exactly — staged, modified, added,
  deleted, untracked, conflicted — plus ahead/behind and the stash count.
- Refreshes on a timer and on filesystem, git and session events; the terminal
  never waits for git (all reads are async `execFile`).

## Requirements

- OpenCode V1 CLI (1.18.x, the `tui.json` plugin system). Tested on 1.18.30.
- `git` on `PATH`.
- A terminal that supports the theme's ANSI colors, as usual for the TUI.

It does **not** load in OpenCode V2: V2 resolves `./tui` modules through a different
loader and expects a `Plugin.define({ id, setup })` module. Use `opencode-git-status`
there.

## Install

This is a **TUI-only** plugin. V1 keeps TUI plugins in `tui.json`, separately from the
server plugins in `opencode.json(c)`. Entries are `[spec, options]` pairs or plain
strings:

```jsonc title="~/.config/opencode/tui.json"
{
  "$schema": "https://opencode.ai/tui.json",
  "plugin": [
    ["opencode-git-status-v1", { "interval": 2500 }]
  ]
}
```

A string entry works too and uses the defaults:

```jsonc
{ "plugin": ["opencode-git-status-v1"] }
```

Do not add it to `opencode.json(c)` — V1 loads V1 *server* plugins from there, and this
package has no server entrypoint. Restart the TUI after editing `tui.json`; no separate
install step is needed, the host fetches the package on startup.

### From a local file

The same module also works straight from disk, which is handy for development:

```text
~/.config/opencode/plugins/git-status-v1/
├── package.json   # exports: { "./tui": "./tui.tsx" }
└── tui.tsx
```

```jsonc title="~/.config/opencode/tui.json"
{ "plugin": [["./plugins/git-status-v1", { "interval": 2500 }]] }
```

## Options

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `interval` | number (ms) | `2500` | Refresh period. Values below `500` fall back to `2500`. |
| `enabled` | boolean | `true` | Set to `false` to keep the plugin configured but unloaded. |

Refresh also runs immediately on `file.edited`, `file.watcher.updated`,
`vcs.branch.updated` and `session.idle` events (event types missing on a host version
are ignored; the timer still covers them).

Disable a loaded plugin by its id without touching the `plugin` array:

```jsonc title="~/.config/opencode/tui.json"
{ "plugin_enabled": { "git-status": false } }
```

## What it shows

| Part | Source | Color |
| --- | --- | --- |
| `parent/` | location path, `$HOME` abbreviated by the plugin | muted |
| `name` | last path segment | base text |
| `:branch` | `# branch.head` | accent |
| `↑N` / `↓N` | `# branch.ab`, or commits not on any remote when there is no upstream | info |
| `!N` | unmerged (`u` records) | error |
| `-N` | staged deletions | error |
| `+N` | staged additions | success |
| `±N` | other staged changes (including renames) | warning |
| `~N` | unstaged modifications | warning |
| `?N` | untracked | muted |
| `⚑N` | `git stash list` entries | secondary |
| `✓` | working tree clean, nothing ahead/behind | success |

Detached HEAD renders the abbreviated commit instead of a branch name.

## How it reads git

- `git status --porcelain=v2 --branch --untracked-files=normal`
- `git stash list --format=%gd`
- `git rev-list --count HEAD --not --remotes` (only when the branch has no upstream)

All calls use `GIT_OPTIONAL_LOCKS=0`, a 5 s timeout and a 4 MB output cap, so status
refreshes never take index locks or hang the UI. The directory is the active session's
location, falling back to the current location's worktree and directory.

## Notes and limitations

- V1 renders the `sidebar_footer` slot in `single_winner` mode: the plugin wins it
  (`order: 10`) and therefore draws the whole footer itself, including the
  `• Open Code <version>` line. The built-in footer extras (the clickable path and the
  `Getting started` hint) are not shown while it is active.
- `↑`/`↓` come from the branch upstream; with no upstream the plugin counts commits
  that exist on no remote at all, which is a hint rather than an exact ahead/behind
  value.
- Worktrees: the plugin reports the location it is loaded for, so open the session in
  the worktree directory to see that worktree's status.

## License

MIT
