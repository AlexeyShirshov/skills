# skills

[![skills.sh](https://skills.sh/b/AlexeyShirshov/skills)](https://skills.sh/AlexeyShirshov/skills)

Reusable agent skills for [opencode](https://opencode.ai). Each skill is a directory with a
`SKILL.md` entry point (YAML frontmatter: `name`, `description`) plus optional `assets/`,
`scripts/`, and `tests/`.

## Contents

Skills live under [`opencode/`](opencode/).

| Skill | Description |
| --- | --- |
| [`pdca`](opencode/pdca) | Domain-neutral PDCA cycle: PLAN → DO → CHECK → ACT with transition gates, evidence-based CHECK, escalation accounting, durable status, and recovery. |
| [`pdca-coder`](opencode/pdca-coder) | Stack-agnostic PDCA executor for software-engineering tasks (code, tests, docs, refactoring, config). Picks the build/test/lint toolchain per language. |
| [`pdca-collection`](opencode/pdca-collection) | Runs a batch of tasks as parallel PDCA lanes (worktree per group, branch chain + auto-commit, `--no-ff` merge of completed groups). |
| [`pdca-dotnet`](opencode/pdca-dotnet) | PDCA cycle for .NET/C# tasks: parallel DO/CHECK streams, role routing, ACT handoff. |

All four share the same cycle contract: a cheap orchestrator drives roles (planner, coder,
check, scout, escalate), every CHECK is evidence-based, and a required approval that cannot
be obtained is a STOP rather than an open question.

## Install

Install a single skill with the [skills](https://skills.sh) CLI — one command per skill:

```sh
npx skills add AlexeyShirshov/skills@pdca
npx skills add AlexeyShirshov/skills@pdca-coder
npx skills add AlexeyShirshov/skills@pdca-dotnet
npx skills add AlexeyShirshov/skills@pdca-collection
```

Add `-g` for a user-level install (all projects) and `-y` to skip prompts:

```sh
npx skills add AlexeyShirshov/skills@pdca-coder -g -y
```

Without `-g` the CLI targets the current project.

### From a checkout

Clone the repository and copy the skill(s) you want into an opencode skills directory.

Global (all projects):

```sh
cp -r opencode/pdca opencode/pdca-coder opencode/pdca-collection opencode/pdca-dotnet \
  ~/.config/opencode/skills/
```

Per project:

```sh
mkdir -p .opencode/skills
cp -r opencode/pdca* .opencode/skills/
```

Skills are discovered by the `name` field in their frontmatter.

## Usage

Invoke a skill by name, e.g. in an opencode session:

- `pdca` — only when explicitly named (domain-neutral cycle).
- `pdca-coder` — "by the cycle" / "via PDCA" for code tasks.
- `pdca-dotnet` — for .NET/C# work.
- `pdca-collection` — for a list of independent tasks / a milestone.

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
incomplete group preserved but never merged) on throwaway temp repositories:

```sh
bash opencode/pdca-collection/tests/git-model-sim.sh
```

## Plugins

Plugins live under [`opencode/plugins/`](opencode/plugins/), one directory per package.

| Plugin | Description |
| --- | --- |
| [`wsl-notify`](opencode/plugins/wsl-notify) [![npm](https://img.shields.io/npm/v/wsl-notify)](https://www.npmjs.com/package/wsl-notify) | Windows toast notifications for OpenCode — permission, question, completion and error events. Zero dependencies, one entrypoint for OpenCode V1 and V2, works from WSL (`powershell.exe` interop) and native Windows. |

Install the published package in `opencode.json(c)` (`plugins` on V2, `plugin` on V1), or copy a plugin's
`index.js` into `<config>/plugins/` and let opencode discover it locally. See each plugin's README for
options and requirements.

## License

[MIT](LICENSE) © 2026 Alexey Shirshov
