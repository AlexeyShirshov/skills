# opencode-sidebar-plugins

[![npm](https://img.shields.io/npm/v/opencode-sidebar-plugins)](https://www.npmjs.com/package/opencode-sidebar-plugins)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A `Plugins` section in the [OpenCode](https://opencode.ai) V2 CLI sidebar that lists
what is loaded — and, by default, only what actually reaches the model context.

OpenCode reports every loaded plugin (built-in and user), but a plugin only costs
tokens when it puts something into the prompt or the tool catalog. This panel
separates the two, so the sidebar answers "what am I paying for?" instead of
"what is installed?".

```text
▼ Plugins (2 in context)
  • opencode-roslyn tool          Active
  • btw-context prompt            Active
  ▶ Built-in (28 of 88)
```

## Requirements

- OpenCode V2 CLI (`opencode` 2.x).
- Depends only on the host's `@opencode/plugin` TUI API (plus the OpenTUI/Solid
  peers the host already provides); the data layer itself uses only `node:fs`
  and `node:path`.

## Install

A **CLI-only** plugin: it renders in the terminal and has no server entrypoint.
Add it to `cli.json` (not `opencode.json(c)`):

```jsonc title="~/.config/opencode/cli.json"
{
  "plugins": [
    { "package": "opencode-sidebar-plugins", "options": { "scope": "context" } }
  ]
}
```

A string entry uses the defaults: `{ "plugins": ["opencode-sidebar-plugins"] }`.

While only a staged release exists on npm, pin the dist-tag explicitly:
`"opencode-sidebar-plugins@staging"`.

### From a local checkout

The same layout works from disk — `<config>/plugins/<name>/` with `package.json`
declaring `exports: { "./tui": "./tui.tsx" }`:

```jsonc
{ "plugins": [{ "package": "./plugins/sidebar-plugins" }] }
```

## Options

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `scope` | `"context"` \| `"user"` \| `"all"` | `"context"` | `context` — only prompt-affecting plugins; `user` — all non-builtin (incl. CLI-only); `all` — plus built-ins and everything that adds nothing. |
| `interval` | number (ms) | `15000` | Refresh period; values below `1000` fall back to the default. |
| `enabled` | boolean | `true` | Set to `false` to keep the package configured but unloaded. |

Refresh also runs on `plugin.updated` and `server.connected` when the host emits
them; the timer covers the rest. Collapse state is kept in TUI storage.

## What counts as "affects context"

Built-in plugins are classified from a table taken from the built-in setup code in
the `v2.0.28` binary — by what each plugin registers, never by an id prefix:

- **context:** Tools, Prompt, Agent, Skill, Config (agent/instruction/reference/
  compatibility/policy/tool-output/compaction), MCP, plus `vcs.git` (the `<env>`
  line `Is directory a git repo: …`);
- **no context:** `tool.input.repair`, `prompt.verbosity`, providers and model
  metadata, websearch backends, VCS, slash commands, warming, browser,
  infra `config.*` (command/formatter/image/provider/websearch/shell/snapshot/
  worktree/location-watcher);
- provider-specific prompt plugins (`prompt.openai/anthropic/kimi/meta/arcee`)
  count only while the session's model belongs to that provider; unknown ids are
  marked `unclassified` and treated by their group.

Local server plugins are classified by scanning their source for real API calls,
gated by an actual rewrite of what the model sees:

| Channel | Registration | Counts when |
| --- | --- | --- |
| `tool` | `tool.transform` / `tool.hook` | always — a tool schema enters the catalog |
| `prompt` | `session.hook("prompt"\|"context"\|"compaction"\|"generate"\|"title")` | it edits `system`/`messages`/`tools`/`result` or `prompt.text` |
| `agent` | `agent.transform` | it adds/removes/defaults an agent or edits a definition field — a `draft.model = …` rebind does not |
| `skill`, `reference` | `*.transform` | it adds/updates/removes an entry |
| `mcp`, `config` | `*.transform` | it adds/updates/removes/sets a server or config entry |

Everything else a server plugin can hook — events, retries, permissions, storage,
RPC, shell, VCS, providers, model metadata — never reaches the prompt and is not
listed in `context` scope. A plugin's own state that merely *looks* like a
registration (`agents: {}`, `prompt: …`) is not one.

Package plugins are scanned from their installed entry file under
`~/.cache/opencode/npm/` (`<name>@<range>/<timestamp>/node_modules/<name>/`, git
targets `git-<name>-<sha256(target)[:12]>/`); if the entry cannot be resolved the
row is marked `unverified` and counted as context, because hiding a real
contributor is worse than showing an unproven one.

## Notes and limitations

- The built-in table is pinned to the binary's built-ins; after an OpenCode
  upgrade, new ids show up as `unclassified` until the table is refreshed.
- Source scanning is textual. It understands the V2 registration calls and their
  mutation gates, not arbitrary code; a plugin that assembles registrations
  dynamically or splits them across files may be misjudged.
- CLI-only plugin directories (`<config>/plugins`, `<location>/.opencode/plugins`)
  are not in the server list, so the panel discovers them from disk. Rows the
  server already knows are matched by name and shown once.
- CLI/TUI-only plugins are never shown in `context` scope: they run in the
  terminal process and add nothing to the model request.

## Local development

`data.ts` is dependency-free (node builtins only), so the classifier runs outside
the TUI. `npm test` (or `bun test/smoke.mjs`) covers the built-in table, the
source scan and the package fallback; the same script gates releases in CI.

Against a live host, dump `/api/plugin` and render the rows:

```bash
opencode api get /api/plugin > /tmp/opencode/plugins.json
bun -e '
  import { build, pluginDirectories } from "./data.ts"
  import { readFileSync } from "node:fs"
  const raw = JSON.parse(readFileSync("/tmp/opencode/plugins.json", "utf8")).data
  console.table(build(raw, pluginDirectories(process.cwd())).filter((i) => !i.builtin))
'
```

The view has no local preview: to see a change, copy the package to
`~/.config/opencode/plugins/` (or install it from npm) and restart the CLI — TUI
plugins live in the CLI process, so `opencode service restart` does not reload them.

## License

MIT
