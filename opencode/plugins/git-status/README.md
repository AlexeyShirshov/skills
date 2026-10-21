# opencode-git-status

[![npm](https://img.shields.io/npm/v/opencode-git-status)](https://www.npmjs.com/package/opencode-git-status)

Git working-tree status in the [OpenCode](https://opencode.ai) CLI sidebar footer —
current branch, ahead/behind, staged, modified, untracked, conflicts and stashes on
one line, updated while you work.

```text
~/sources/opencode-config:main ↑1 ↓2 !1 -3 +4 ±5 ~6 ?7 ⚑2
```

- One line: path, branch, then only the non-zero counters.
- Counters follow `git status --porcelain=v2` exactly — staged, modified, added,
  deleted, untracked, conflicted — plus ahead/behind and the stash count.
- Refreshes on a timer and on filesystem, git and session events; the terminal
  never waits for git (all reads are async `execFile`).
- Zero runtime dependencies beyond the OpenCode plugin API and the OpenTUI/Solid
  peers the host already provides.

This is the V2 build. For OpenCode V1 use the separate
[`opencode-git-status-v1`](https://www.npmjs.com/package/opencode-git-status-v1) package
(V1 loads TUI plugins from `tui.json` through a different API).

## Requirements

- OpenCode V2 CLI (`opencode` 2.x).
- `git` on `PATH`.
- A terminal that supports the theme's ANSI colors, as usual for the TUI.

## Install

This is a **CLI-only** plugin: it renders in the terminal and has no server
entrypoint. Add it to `cli.json` (not to `opencode.json(c)`):

```jsonc title="~/.config/opencode/cli.json"
{
  "plugins": [
    { "package": "opencode-git-status", "options": { "interval": 2500 } }
  ]
}
```

While the package is published on the `staging` dist-tag, install it explicitly:

```jsonc
{ "package": "opencode-git-status@staging", "options": { "interval": 2500 } }
```

A string entry works too and uses the defaults:

```jsonc
{ "plugins": ["opencode-git-status"] }
```

CLI-only plugins stay active when the CLI is connected to a remote server, because
they run locally in the terminal.

## Options

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `interval` | number (ms) | `2500` | Refresh period. Values below `500` fall back to `2500`. |
| `enabled` | boolean | `true` | Set to `false` to keep the package configured but unloaded. |

Refresh also runs immediately on `filesystem.changed`, `git`,
`vcs.branch.updated`, `session.idle` and `worktree.resolved` events (event names
missing on a host version are ignored; the timer still covers them).

## What it shows

| Part | Source | Color |
| --- | --- | --- |
| `parent/` | location path, home abbreviated by the host | muted |
| `name` | last path segment | base text |
| `:branch` | `# branch.head` | accent |
| `↑N` / `↓N` | `# branch.ab`, or commits not on any remote when there is no upstream | info |
| `!N` | unmerged (`u` records) | error |
| `-N` | staged deletions | error |
| `+N` | staged additions | success |
| `±N` | other staged changes (including renames) | warning |
| `~N` | unstaged modifications | warning |
| `?N` | untracked | muted |
| `⚑N` | `git stash list` entries | muted |
| `✓` | working tree clean, nothing ahead/behind | success |

Detached HEAD renders the abbreviated commit instead of a branch name.

## How it reads git

- `git status --porcelain=v2 --branch --untracked-files=normal`
- `git stash list --format=%gd`
- `git rev-list --count HEAD --not --remotes` (only when the branch has no upstream)

All calls use `GIT_OPTIONAL_LOCKS=0`, a 5 s timeout and a 4 MB output cap, so
status refreshes never take index locks or hang the UI. The directory is the
active session's location, falling back to the current location and its default.

## Notes and limitations

- The plugin **replaces** the built-in `sidebar.footer` slot to keep path, branch
  and counters on one line. As a result the built-in footer extras are not shown:
  the click-to-move-session path and the `Getting started` hint.
- `↑`/`↓` come from the branch upstream; with no upstream the plugin counts
  commits that exist on no remote at all, which is a hint rather than an exact
  ahead/behind value.
- Worktrees: the plugin reports the location it is loaded for, so open the
  session in the worktree directory to see that worktree's status.

## Local development

Plugins are discovered from `<config>/plugins/<name>/`, so the same package layout
works from disk:

```text
~/.config/opencode/plugins/git-status/
├── package.json   # exports: { "./tui": "./tui.tsx" }
└── tui.tsx
```

```jsonc title="~/.config/opencode/cli.json"
{ "plugins": ["./plugins/git-status"] }
```

`opencode plugin list` shows local entries with source `local` and package entries
with their resolved version.

## License

MIT
