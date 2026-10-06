# skills

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

Copy the skill(s) you want into your opencode skills directory.

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

## License

[MIT](LICENSE) © 2026 Alexey Shirshov
