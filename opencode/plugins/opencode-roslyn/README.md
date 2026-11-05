# opencode-roslyn

[![npm](https://img.shields.io/npm/v/opencode-roslyn)](https://www.npmjs.com/package/opencode-roslyn)

C# semantic analysis for [OpenCode](https://opencode.ai) V2 — types, symbols, members, references,
call sites, implementations and renames, answered by Roslyn instead of by `rg`.

The plugin registers one tool, `roslyn`, and delegates to the
[`roslynq`](#roslynq) CLI (Roslyn + `MSBuildWorkspace`). It is the V2 answer for the questions an
agent would otherwise guess at with text search: *what type is this*, *who calls this*, *what
implements this*, *rename this symbol everywhere*.

- Semantic answers only: the solution is loaded by `MSBuildWorkspace`, so comments, strings and
  same-named text never produce false hits.
- One daemon per solution: `roslynq` loads the MSBuild workspace once and keeps compiled projects, so
  repeated calls skip the reload. Queries still cost seconds — see [Performance](#performance).
- Works because **V2 has no LSP runtime yet**. Instead of porting the LSP client
  ([opencode#38528](https://github.com/anomalyco/opencode/issues/38528)), this plugin drives a CLI
  through an ordinary tool transform — the same eight operations the V1 `lsp` tool gained in
  [opencode#51715](https://github.com/anomalyco/opencode/issues/51715).
- Zero dependencies, no build step, plain ESM, one entrypoint (`index.js`).

## Requirements

- .NET SDK able to build the target solution (the CLI targets `net10.0`).
- The `roslynq` executable, resolved in this order:
  1. the `bin` plugin option,
  2. `OPENCODE_ROSLYN_BIN`,
  3. `~/.dotnet/tools/roslynq` (the global dotnet tool),
  4. bare `roslynq` on `PATH`.

```sh
dotnet tool install --global opencode-roslyn
dotnet tool update  --global opencode-roslyn
```

Working on an unreleased version of the CLI? Build it from source — it lives next to this plugin, in
[`roslynq/`](roslynq/) — and install it from the local package:

```sh
cd opencode/plugins/opencode-roslyn/roslynq
dotnet pack -c Release                     # → nupkg/opencode-roslyn.1.0.0.nupkg
dotnet tool install --global --add-source ./nupkg opencode-roslyn
```

## Install

```jsonc
// opencode.json(c)
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["opencode-roslyn"]
}
```

```sh
opencode plugin add opencode-roslyn
```

OpenCode also loads the plugin from `~/.config/opencode/plugins/` without a config entry. Keep only
one of the two: this package and the hand-rolled `plugins/roslyn.js` register the same tool name, and
the later registration wins.

## Use

`roslyn` is registered into Code Mode, so agents call it from `execute`:

```ts
const refs = await tools.roslyn({ action: "refs", target: "NextORM.Core.SqlBuilder.ToCommand" })
return refs
```

| `action`          | `target`                                             | Returns                                                   |
| ----------------- | ---------------------------------------------------- | --------------------------------------------------------- |
| `structure`       | —                                                    | Projects, namespaces and types of the solution            |
| `types`           | type-name substring                                  | Matching type names                                       |
| `symbols`         | full name, e.g. `NextORM.Core.SqlBuilder.MakeSelect` | Definition location(s)                                    |
| `members`         | type full name                                       | Members of the type                                       |
| `refs`            | member/type full name                                | Every reference                                           |
| `callers`         | member full name                                     | Incoming call sites                                       |
| `implementations` | interface/abstract full name                         | Implementing types/members                                |
| `rename`          | member/type full name + `newName`                    | Workspace edit; **dry-run** unless `apply: true` writes it |

Inputs: `action` (required), `target`, `newName` (required for `rename`), `apply` (rename only),
`solution` (path, absolute or relative to the project directory).

## Options

```jsonc
{
  "plugins": [
    {
      "package": "opencode-roslyn",
      "options": {
        "bin": "/usr/local/bin/roslynq",
        "solution": "src/App.slnx",
        "permission": "roslyn"
      },
    },
  ],
}
```

| Option       | Default                        | Meaning                                                                |
| ------------ | ------------------------------ | ---------------------------------------------------------------------- |
| `bin`        | `~/.dotnet/tools/roslynq`      | Executable to run.                                                     |
| `solution`   | first `.slnx`/`.sln` in the project directory | Solution to analyse when the call passes no `solution`. |
| `permission` | `roslyn`                       | Permission action name reported for this tool.                          |

## Permissions

Every call asserts the permission action `roslyn` with the **solution path as the resource**, so a
narrow rule can scope the tool to one solution and a broad one allows it outright:

```jsonc
{
  "permissions": [
    // allow roslyn everywhere
    { "action": "roslyn", "resource": "*", "effect": "allow" },
    // …or only in this checkout, and force a prompt everywhere else
    { "action": "roslyn", "resource": "**/src/App.slnx", "effect": "allow" },
    { "action": "roslyn", "resource": "*", "effect": "ask" }
  ]
}
```

Agents that deny everything (`"*": deny`) must allow `roslyn` explicitly — the tool is filtered out
of their tool list otherwise. `apply: true` renames are gated by the same action; there is no separate
write permission, so scope the resource pattern if a repository should not be renamed in place.

## How it works

```
ctx.tool.transform(editor => editor.add({ name: "roslyn", … }))
```

- V2 has no `tools/*.ts` entrypoint; a tool is a plugin transform. This plugin is therefore a plain
  object with `id` + `setup()`, discovered like any other V2 plugin.
- The plugin loads per location, so the **project directory** is the analysis root: the solution is
  discovered there (`*.slnx` preferred) and `roslynq` runs with it as `cwd`.
- `context.signal` is passed to the child process, so stopping the session stops the analysis.
- Output up to 64 MiB is accepted (`refs`/`callers` on a large solution exceed Node's 1 MiB default).
- A missing binary and a non-zero exit are reported differently: the first returns an install hint,
  the second returns the CLI's stderr plus its exit code.

## Performance

Measured on `nextorm.slnx` (20 projects, ~800 types in the largest, `SqlBuilder.cs` ~2100 lines),
.NET 10.0.401, one warm daemon:

| Call                              | Wall clock    |
| --------------------------------- | ------------- |
| first query, cold (loads solution) | ~29 s        |
| first query after the workspace is loaded | 8–27 s |
| repeated query on a compiled project | ~8 s       |
| `structure` (20 projects)          | 12–40 s      |

The daemon's RSS grows as projects get compiled — ~180 MB right after loading, ~550 MB after the
first query, ~730 MB after a few — and it exits after 10 min idle (`ROSLYNQ_IDLE_MS`). The plugin
process itself stays at ~50 MB; it only talks to the daemon.

So the daemon buys you the MSBuild reload, not the analysis: expect **seconds to tens of seconds per
query** on a real solution, not milliseconds. That is the honest cost of asking Roslyn instead of
grepping, and it is why agents should batch several calls into one Code Mode `execute`
(`Promise.all`) instead of firing them one per step.

## Development

```sh
node test/smoke.mjs
```

The smoke test drives the real `setup()` with a synthetic plugin context and a fake `roslynq` script
on disk, so it needs neither .NET nor a solution. It asserts the registered tool shape, solution
discovery (`.slnx` over `.sln`, explicit paths), the argv for every action, `rename` dry-run vs
`--apply`, permission assertion, progress reporting, missing binary, non-zero exit, cancellation, and
binary resolution precedence.

## Relationship to other C# tooling

[`opencode-sharp`](https://github.com/adamhathcock/opencode-sharp) is the closest neighbour: it starts
the `roslyn-language-server` sidecar and exposes diagnostics, code actions, organize-imports and
workspace symbols. This plugin runs no language server and pulls no diagnostics — it covers the
navigation and rename surface (`structure`/`types`/`symbols`/`members`/`refs`/`callers`/
`implementations`/`rename`) through `roslynq`. The two can be installed side by side.

## Releasing

Both artifacts ship from CI, tag-driven, with OIDC trusted publishing and **no stored credentials**:

| Artifact              | Registry | Workflow                               | Tag                    |
| --------------------- | -------- | -------------------------------------- | ---------------------- |
| plugin `opencode-roslyn` | npm  | `.github/workflows/publish-npm.yml`     | `opencode-roslyn-vX.Y.Z` |
| CLI `roslynq`         | NuGet    | `.github/workflows/publish-nuget.yml`   | `roslynq-vX.Y.Z`         |

The tag must carry the version the artifact already declares — the workflow compares the two and
refuses a mismatch:

```sh
# plugin: bump package.json, commit, then
git tag opencode-roslyn-v0.2.0 && git push origin opencode-roslyn-v0.2.0

# CLI: bump <Version> in roslynq/Roslyn.Cli.csproj, commit, then
git tag roslynq-v1.1.0 && git push origin roslynq-v1.1.0
```

npm runs on **staged publishing**: CI calls `npm stage publish`, the trusted publisher keeps its
default stage-only rights, and a maintainer approves the version with 2FA — the flow `wsl-notify`
used, and the reason nothing landed on the registry unreviewed:

```sh
npx --yes npm@latest stage list
npx --yes npm@latest stage approve <id>   # needs npm >= 11.5.1; the local 10.x has no `stage`
```

NuGet needs none of that: `NuGet/login@v1` exchanges the GitHub OIDC token for a one-hour API key,
and the policy is scoped to the account's package globs, so it also covers a package that does not
exist yet.

Two things are one-time setup:

1. npmjs.com → `opencode-roslyn` → Settings → **Trusted publishing** → GitHub Actions: user
   `AlexeyShirshov`, repository `skills`, workflow filename `publish-npm.yml` (filename only).
   Leave the default stage-only rights.
2. nuget.org → **Trusted Publishing** → new policy: repository owner `AlexeyShirshov`, repository
   `skills`, workflow file `publish-nuget.yml`, environment empty, scope covering new packages and
   new versions. Then `gh secret set NUGET_USER --repo AlexeyShirshov/skills` with the nuget.org
   **username** (not the email).

A brand-new npm package cannot get a trusted publisher until it exists, so the very first version
was published by hand. Never bootstrap with the version `0.0.0-stage`: since October 2026 that string
is npm's own placeholder for `npm stage publish` on a package that does not exist yet, and the
registry rejects it for an ordinary publish (`You cannot publish using the version`). Use a real
version — `npx --yes npm@latest stage publish` then `stage approve` claims the name and publishes it.
That is what `0.1.0` was: staged and approved by hand on 2026-10-18 (shasum `1cc12b07…`), which is why
the first release made by CI is `0.1.1` — same plugin, built and published by the workflow, no
functional change.

Not done yet:

- The `~/.config/opencode/tools/roslyn-cli/` copy and the one in
  [`AlexeyShirshov/opencode-config`](https://github.com/AlexeyShirshov/opencode-config) are now legacy;
  the global tool is installed from the NuGet package, not from them.


