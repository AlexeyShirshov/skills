# skills

[![skills.sh](https://skills.sh/b/AlexeyShirshov/skills)](https://skills.sh/AlexeyShirshov/skills)

Reusable agent skills for [opencode](https://opencode.ai). Each skill is a directory with a
`SKILL.md` entry point (YAML frontmatter: `name`, `description`) plus optional `assets/`,
`scripts/`, and `tests/`.

At runtime everything a skill writes lives in one project-local workspace root, `.pdca/` — helpers
it runs (`.pdca/scripts/`), cycle status files (`.pdca/status/`) and evidence
(`.pdca/<task>/rv<k>/`). The skill's own `scripts/` is the source of those helpers; the project runs
its copies from `.pdca/scripts/`.

## Contents

Skills live under [`opencode/`](opencode/).

| Skill | Description |
| --- | --- |
| [`pdca-entry`](opencode/pdca-entry) | Single entry point (umbrella) for the family: classifies a task and routes it to exactly one contract — collection, incremental, .NET, coder or the neutral cycle. |
| [`pdca`](opencode/pdca) | Domain-neutral PDCA cycle: PLAN → DO → CHECK → ACT with transition gates, evidence-based CHECK, escalation accounting, durable status, and recovery. |
| [`pdca-coder`](opencode/pdca-coder) | Stack-agnostic PDCA executor for software-engineering tasks (code, tests, docs, refactoring, config). Picks the build/test/lint toolchain per language. |
| [`pdca-collection`](opencode/pdca-collection) | Runs a batch of tasks as parallel PDCA lanes (worktree per group, branch chain + auto-commit, `--no-ff` merge of completed groups); a batch may contain single-cycle units and sequential incremental-campaign units. |
| [`pdca-dotnet`](opencode/pdca-dotnet) | PDCA cycle for .NET/C# tasks: parallel DO/CHECK streams, role routing, ACT handoff. |
| [`pdca-incremental`](opencode/pdca-incremental) | Drives a goal without a committed whole-volume plan as a chain of small PDCA increments: one accepted measurement per step, baseline chain, one campaign status file, explicit stop conditions, plus `repair` and `verify` step kinds; a campaign can also be a unit of a collection batch and then stays sequential. |

The five contracts share the same cycle: a cheap orchestrator drives roles (planner, coder,
check, scout, escalate), every CHECK is evidence-based, and a required approval that cannot
be obtained is a STOP rather than an open question. `pdca-entry` sits above them: it does not
run a cycle, it only classifies the task and hands it to exactly one contract.

## Install

Install a single skill with the [skills](https://skills.sh) CLI — one command per skill:

```sh
npx skills add AlexeyShirshov/skills@pdca-entry
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
the role agents and the runner `pdca-orchestrator` (both ship in the skill's `assets/agents/`),
nested delegation (`experimental.subagent_depth`) and `subagent` permissions. Every agent id is
`pdca-`prefixed (`pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`, `pdca-scout`,
`pdca-security-auditor`, `pdca-orchestrator`), so it cannot collide with an existing
`planner`/`coder`/`scout`. The full checklist — with a verification step and a troubleshooting table —
is in [`docs/install.md`](docs/install.md) ([`docs/ru/install.md`](docs/ru/install.md)); an agent
can perform the whole checklist from [`docs/install-prompt.md`](docs/install-prompt.md).

### From a checkout

Clone the repository and copy the skill(s) you want into an opencode skills directory.

Global (all projects):

```sh
cp -r opencode/pdca opencode/pdca-coder opencode/pdca-collection opencode/pdca-dotnet \
  opencode/pdca-incremental ~/.config/opencode/skills/
```

Per project:

```sh
mkdir -p .opencode/skills
cp -r opencode/pdca* .opencode/skills/
```

Skills are discovered by the `name` field in their frontmatter.

## Usage

Only `pdca-entry` is advertised to the model for automatic selection. The five contracts set
`metadata.opencode/autoinvoke: false`: they stay registered but load only when the user names them
explicitly (`skill pdca-dotnet`, `@pdca-dotnet`) or when the entry hands off.

Invoke a skill by name, e.g. in an opencode session:

- `pdca-entry` — "by the cycle" / "via PDCA" / "по циклу": the umbrella that routes the task to
  one contract below (an explicitly named contract bypasses it).
- `pdca` — only when explicitly named (domain-neutral cycle).
- `pdca-coder` — explicitly, for code tasks of any stack.
- `pdca-dotnet` — explicitly, for .NET/C# work.
- `pdca-collection` — for a list of independent tasks / a milestone; a collection batch may contain
  cycle units and campaign units, and a campaign unit stays sequential (one lane, one step at a
  time).
- `pdca-incremental` — for a goal without a committed whole-volume plan (per-task plans may already exist), moved forward in steps; includes per-step `repair` and an optional integrated `verify`. A campaign can also run as a unit of a collection batch.

## Tests

Each skill ships a `tests/` suite (plain `unittest`, standard library only). Run one skill:

```sh
python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v
```

Some checks compare the skill against host-side artifacts that live in a separate config
repository (`config/agents/`, `config/profiles/`, `config/AGENTS.md`, the host `README.md`). Those
checks skip unless you point at that checkout:

```sh
OPENCODE_CONFIG_REPO=/path/to/opencode-config \
  python3 -m unittest discover -s opencode/pdca-dotnet/tests -p 'test_*.py'
```

`pdca-collection` additionally ships a dependency-free bash check of its git model (branch
chain, `--no-ff` merge of completed groups, conflict detection, single-group isolation, and an
incomplete group preserved but never merged) on throwaway temp repositories. `unittest discover`
runs it through `tests/test_git_model.py`; it can also be run directly:

```sh
bash opencode/pdca-collection/tests/git-model-sim.sh
```

## Plugins

Plugins live under [`opencode/plugins/`](opencode/plugins/), one directory per package.

| Plugin | Description |
| --- | --- |
| [`wsl-notify`](opencode/plugins/wsl-notify) [![npm](https://img.shields.io/npm/v/wsl-notify)](https://www.npmjs.com/package/wsl-notify) | Windows toast notifications for OpenCode — permission, question, completion and error events. Zero dependencies, one entrypoint for OpenCode V1 and V2, works from WSL (`powershell.exe` interop) and native Windows. |
| [`opencode-roslyn`](opencode/plugins/opencode-roslyn) [![npm](https://img.shields.io/npm/v/opencode-roslyn)](https://www.npmjs.com/package/opencode-roslyn) [![NuGet](https://img.shields.io/nuget/v/opencode-roslyn)](https://www.nuget.org/packages/opencode-roslyn) | C# semantic analysis for OpenCode V2 — the `roslyn` tool answers structure/types/symbols/members/refs/callers/implementations/rename through the `roslynq` CLI (Roslyn + `MSBuildWorkspace`), with permissions, progress and cancellation. V2 has no LSP runtime yet; this is the semantic answer in the meantime. |

Install the published package in `opencode.json(c)` (`plugins` on V2, `plugin` on V1), or copy a plugin's
`index.js` into `<config>/plugins/` and let opencode discover it locally. See each plugin's README for
options and requirements.

## License

[MIT](LICENSE) © 2026 Alexey Shirshov
