# PDCA skill catalog

Use this catalog to find the contract behind a PDCA run. If you want to run
your first task, start with the [user guide](../docs/guide/README.md) or
[руководство пользователя](../docs/ru/guide/README.md).

## Entry, forms, and overlays

Ask for `pdca` in your prompt. Its entry PLAN chooses the form and, for
code work, the applicable overlay. A form organizes the work; an overlay
adds rules for a programming domain without starting another cycle.

| Skill contract | Role | When it applies |
| --- | --- | --- |
| [`pdca`](pdca/SKILL.md) | Entry and shared contract | Start here for any PDCA run. It also defines Bounded Execution for a task with a known method and scope. |
| [`pdca-incremental`](pdca-incremental/SKILL.md) | Campaign form | One goal needs several verified steps because the method or scope of work isn't known up front. |
| [`pdca-collection`](pdca-collection/SKILL.md) | Collection form | A batch has independent goals. Each item has its own run and can itself be a campaign. |
| [`pdca-coder`](pdca-coder/SKILL.md) | Programming overlay | The task involves code. The overlay adds rules for engineering evidence, existing tests, and safe command execution. |
| [`pdca-dotnet`](pdca-dotnet/SKILL.md) | .NET overlay | The task involves .NET or C#. This overlay inherits `pdca-coder` and adds .NET-specific guidance. |

## Setup and reference

For skill dependencies and role agents, see the
[installation checklist](../docs/install.md). For phase rules and how
the forms compose, see the [technical guide](../docs/pdca-guide.md).
