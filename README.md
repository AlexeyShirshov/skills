# skills

[![skills.sh](https://skills.sh/b/AlexeyShirshov/skills)](https://skills.sh/AlexeyShirshov/skills)

Use PDCA when you need an agent to show what it delivered and what proves it. You give it the
goal; a separate CHECK judges the result against the acceptance criteria. For work that doesn't
need a cycle, ask for the task directly.

## Start here

1. [Set up your host](docs/install.md): install the skill contracts and their role agents.
2. [Run your first cycle](docs/guide/first-cycle.md): try a read-only repository task and approve its plan.
3. [Read the result](docs/guide/read-the-result.md): check the verdict against the recorded evidence.

For example, in a repository with a root README, send this to your agent:

```text
Use pdca in normal mode. List the existing local files linked from the
root README.md. Don't edit product files or commit.
```

See the [user guide](docs/guide/README.md), [руководство пользователя](docs/ru/guide/README.md),
[technical guide](docs/pdca-guide.md), or [Russian slide deck (PDF)](docs/ru/pdca-slides/slides-export.pdf).

Persistent PDCA state and proof live under the project root, in `.pdca/` — helpers
it runs (`.pdca/scripts/`), cycle status files (`.pdca/status/`) and evidence
(`.pdca/<task>/rv<k>/`). The skill's own `scripts/` is the source of those helpers; the project runs
its copies from `.pdca/scripts/`. Product files stay in their checkout.

## Contents

See the [skill catalog](skills/README.md) for direct links to each contract.

| Skill | Description |
| --- | --- |
| [`pdca`](skills/pdca) | Single entry and base cycle of the family: one PLAN picks the **form** (Bounded Execution, incremental campaign or collection) and the coder/.NET **specialized skill**, then drives PLAN → DO → CHECK → ACT with independent verification, durable status, recovery and an honest STOP. |
| [`pdca-coder`](skills/pdca-coder) | Programming **overlay** applied to the chosen form (not a cycle of its own): adds code-specific criteria forms, toolchain discovery, command safety, evidence rules, security boundaries, parallel DO streams and the code CHECK deltas. |
| [`pdca-collection`](skills/pdca-collection) | Collection **form**: independent goals as separate complete PDCA invocations, coordinated through a preparation barrier, dependency groups, isolated lanes, an integration CHECK and one batch status; only `done` groups are merged, and incomplete work is preserved. |
| [`pdca-dotnet`](skills/pdca-dotnet) | .NET/C# **overlay** that inherits `pdca-coder` and adds only the .NET differences: the dotnet toolchain, optional task- and policy-aware semantic tooling for C# symbols, test host safety, coverage/mutation facts and .NET documentation conventions. |
| [`pdca-incremental`](skills/pdca-incremental) | Incremental **form**: one goal whose method or volume is unknown advanced as credited steps on the base common contract — a preparation record, a comparable baseline, one accepted increment per step, one campaign status file and explicit stop conditions; a campaign can also be a `campaign` item of a collection batch and then stays sequential. |

**Five skills, two layers.** `pdca` is the **only entry** and carries the common cycle contract;
`pdca-coder` and `pdca-dotnet` are **overlays** (dotnet inherits coder) applied _to_ whichever form was
chosen, never a second cycle; `pdca-collection` and `pdca-incremental` are **forms** that inherit the
common contract and add only their container. The driver is the primary in normal mode or the cheap
`pdca-orchestrator` in autonomous mode; `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-scout` and
`pdca-escalate` carry the phases. Every CHECK is evidence-based, and a required approval that cannot be
obtained is a STOP rather than an open question.

## Install

<details>
<summary>Installation commands and host adapters</summary>

Install a single skill with the [skills](https://skills.sh) CLI — one command per skill:

```sh
npx skills add AlexeyShirshov/skills@pdca
npx skills add AlexeyShirshov/skills@pdca-coder
npx skills add AlexeyShirshov/skills@pdca-dotnet
npx skills add AlexeyShirshov/skills@pdca-collection
npx skills add AlexeyShirshov/skills@pdca-incremental
```

Add `-g` for a user-level install (all projects) and `-y` to skip prompts:

```sh
npx skills add AlexeyShirshov/skills@pdca-coder -g -y
```

Without `-g` the CLI targets the current project.

Installing a skill is only half of the setup: the cycle dispatches **subagents**, so the host needs
the role agents and the driver `pdca-orchestrator` (they ship in the skills' `assets/opencode-agents/`:
the six shared roles — `pdca-scout`, `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`,
`pdca-orchestrator` — are canonical in `pdca` and byte-identical mirrors in the overlays;
`pdca-coder` and `pdca-dotnet` add only the `pdca-security-auditor` specialist, while the forms
`pdca-collection` and `pdca-incremental` carry only the driver mirror; check or regenerate the
mirrors with `python3 tools/pdca/sync_role_assets.py --check` / `--fix`),
nested delegation (`experimental.subagent_depth`) and `subagent` permissions. Every agent id is
`pdca-`prefixed (`pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`, `pdca-scout`,
`pdca-security-auditor`, `pdca-orchestrator`), so it cannot collide with an existing
`planner`/`coder`/`scout`. The full checklist — with a verification step and a troubleshooting table —
is in [`docs/install.md`](docs/install.md) ([`docs/ru/install.md`](docs/ru/install.md)); an agent
can perform the whole checklist from [`docs/install-prompt.md`](docs/install-prompt.md).

Nothing has to be copied by hand. The role agents ship in three ready-to-copy sets — one envelope
per harness, one body: `assets/opencode-agents/` (canonical), `assets/claude-agents/*.md`
(`name`/`description`/`tools`) and `assets/codex-agents/*.toml`
(`name`/`description`/`developer_instructions`). The last two are generated from the canonical assets
by `tools/pdca/gen_host_agents.py` and checked in CI. `pdca` checks the roles before its
first dispatch and, when one does not resolve, hands you the install prompt it ships at
`assets/install-agents-prompt.md`: the agent copies your host's set into the agent directory, binds
the models by tier (an OpenCode profile map, `model:` in a Claude Code agent file, or
`model`/`model_reasoning_effort` in a Codex TOML) and verifies the result. Binding models is the one
part a generator cannot decide — the ids must be ones the host really offers.

### From a checkout

Clone the repository and copy the skill directories you want into an opencode skills directory.
Copy a skill directory whole: `SKILL.md`, `references/`, `assets/`, and `scripts/` where present — the
helpers there are the source of the runtime copies the executor stages into the project's
`.pdca/scripts/` (see the workspace note above). `tests/` and the diagram generators are
development-only and not needed at runtime.

Global (all projects) — the full family, five skills:

```sh
cp -r skills/pdca skills/pdca-coder skills/pdca-collection \
  skills/pdca-dotnet skills/pdca-incremental ~/.config/opencode/skills/
```

Per project:

```sh
mkdir -p .opencode/skills
cp -r skills/pdca* .opencode/skills/
```

In OpenCode V2 the directory determines the exact skill ID; the frontmatter `name` is a display
label. Copying all five does not change which ones the model may pick: only `pdca` is advertised,
the overlays and the forms keep
`metadata.opencode/autoinvoke: false`.

</details>

## Usage

Ask for `pdca` explicitly; it is the single entry of the
family. `pdca-coder`, `pdca-dotnet`, `pdca-collection` and `pdca-incremental` set
`metadata.opencode/autoinvoke: false`: they stay registered but load only when the user names them
explicitly (`skill pdca-dotnet`, `@pdca-dotnet`) or when the base PLAN selects that overlay or form.

Invoke a skill by name, e.g. in an opencode session:

- `pdca` — "by the cycle" / "via PDCA" / `pdca`: the entry. One PLAN picks the form and, for code
  work, the overlay, then the cycle runs.
- `pdca-coder` — explicitly, as the code overlay for tasks of any stack.
- `pdca-dotnet` — explicitly, as the .NET/C# overlay (it inherits `pdca-coder`).
- `pdca-collection` — explicitly, to force the collection form for a list of independent goals / a
  milestone; a batch may contain `cycle` items and `campaign` items, and a campaign item stays
  sequential (one lane, one step at a time).
- `pdca-incremental` — explicitly, to force the incremental form for a goal whose method or volume
  is unknown: one goal moved forward as credited steps, with an explicit stop condition — a step's
  shortfall is a loop-back inside the step, and the campaign closes only on a whole-goal check. A
  campaign can also run as a `campaign` item of a collection batch.

## Tests

The source checkout keeps each skill's test suite in `tests/<skill>/`, outside the
installable `skills/` tree. To run the base suite, install PyYAML and run:

```sh
python3 -m unittest discover -s tests/pdca -p 'test_*.py' -v
```

Some checks compare the skill against host-side artifacts that live in a separate config
repository (`config/agents/`, `config/profiles/`, `config/AGENTS.md`, the host `README.md`). Those
checks skip unless you point at that checkout:

```sh
OPENCODE_CONFIG_REPO=/path/to/opencode-config \
  python3 -m unittest discover -s tests/pdca-dotnet -p 'test_*.py'
```

The collection test suite also includes a Bash check of its Git model (branch
chain, `--no-ff` merge of completed groups, conflict detection, single-group isolation, and an
incomplete group preserved but never merged) on throwaway temp repositories. `unittest discover`
runs it through `tests/pdca-collection/test_git_model.py`; you can also run it directly:

```sh
bash tests/pdca-collection/git-model-sim.sh
```

Maintainer scripts live in `tools/pdca/`. Run diagram generators from the
directory where you want the SVG and HTML output to appear.

To inspect OpenCode token usage and costs, run
`python3 tools/pdca/pdca_cost.py --days 3` from the source checkout. This
optional utility is not part of the skill installation.

## Plugins

Plugins live under [`opencode/plugins/`](opencode/plugins/), one directory per package.

| Plugin | Description |
| --- | --- |
| [`opencode-git-status`](opencode/plugins/git-status) [![npm](https://img.shields.io/npm/v/opencode-git-status)](https://www.npmjs.com/package/opencode-git-status) | Git working-tree status in the OpenCode CLI sidebar footer — path, branch, ahead/behind and only the non-zero `git status --porcelain=v2` counters (staged, modified, added, deleted, untracked, conflicts, stashes) on one line, refreshed on a timer and on filesystem, git and session events without ever blocking the terminal. |
| [`opencode-git-status-v1`](opencode/plugins/git-status-v1) [![npm](https://img.shields.io/npm/v/opencode-git-status-v1)](https://www.npmjs.com/package/opencode-git-status-v1) | The same one-line git status for **OpenCode V1** (`tui.tsx` entry) — branch, ahead/behind and porcelain-v2 counters, updated while you work. |
| [`wsl-notify`](opencode/plugins/wsl-notify) [![npm](https://img.shields.io/npm/v/wsl-notify)](https://www.npmjs.com/package/wsl-notify) | Windows toast notifications for OpenCode — permission, question, completion and error events. Zero dependencies, one entrypoint for OpenCode V1 and V2, works from WSL (`powershell.exe` interop) and native Windows. |
| [`opencode-roslyn`](opencode/plugins/opencode-roslyn) [![npm](https://img.shields.io/npm/v/opencode-roslyn)](https://www.npmjs.com/package/opencode-roslyn) [![NuGet](https://img.shields.io/nuget/v/opencode-roslyn)](https://www.nuget.org/packages/opencode-roslyn) | C# semantic analysis for OpenCode V2 — the `roslyn` tool answers structure/types/symbols/members/refs/callers/implementations/rename through the `roslynq` CLI (Roslyn + `MSBuildWorkspace`), with permissions, progress and cancellation. V2 has no LSP runtime yet; this is the semantic answer in the meantime. |
| [`opencode-sidebar-plugins`](opencode/plugins/sidebar-plugins) [![npm](https://img.shields.io/npm/v/opencode-sidebar-plugins)](https://www.npmjs.com/package/opencode-sidebar-plugins) | A `Plugins` section in the OpenCode V2 CLI sidebar — every loaded plugin and, by default, only those that actually reach the model context (prompt, tools, agents, skills). Classifies built-ins from their registrations, scans local and package plugin sources, and refuses to guess when a package entry cannot be resolved. |
| [`zen-failover`](opencode/plugins/zen-failover) [![npm](https://img.shields.io/npm/v/zen-failover)](https://www.npmjs.com/package/zen-failover) | Server failover for subscription providers: on an exhausted quota it moves every agent, the default model and the active session to the fallback (`ChatGPT` → the same model on Console, `Go` → direct DeepSeek), probes the plan once a minute, and restores the original bindings as soon as the subscription answers again. Transient per-minute `429`s are retried, not degraded. |
| [`opencode-clear-session`](opencode/plugins/clear-session) [![npm](https://img.shields.io/npm/v/opencode-clear-session)](https://www.npmjs.com/package/opencode-clear-session) | `/clear` for the OpenCode V2 CLI — archives the current session (recoverable, not deleted), closes its tab and lands on a fresh session. V2 port of the V1 TUI plugin that replaces V2's built-in `session.clear` (same `/clear`, but it does not archive) and adds `/archive`; its only dependency is the host's `@opencode/plugin` API. |

Install the published package in `opencode.json(c)` (`plugins` on V2, `plugin` on V1), or copy a plugin's
entry file (`index.js`, or `tui.tsx` for the sidebar/TUI plugins) into `<config>/plugins/` and let
opencode discover it locally. See each plugin's README for options and requirements.

## License

[MIT](LICENSE) © 2026 Alexey Shirshov
