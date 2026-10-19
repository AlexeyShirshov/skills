# Setting up the host for the PDCA skill family

Installing a skill copies instructions only. A PDCA skill **names roles** — it creates no agents and
sets no models — so the cycle only runs after the host (OpenCode) provides those agents, lets the
cheap primary dispatch them, and allows nested delegation. This page is the missing install
checklist: skills → agents → orchestrator → delegation depth → permissions → model bindings →
restart → verification.

Without it the cycle does not fail loudly. It either degrades to the flat primary (a recorded
`Notice:`), or hits a resource blocker on the first dispatch.

## 1. What the skill expects from the host

The roles are **subagent names**. Every skill in the family is explicit about its own table
(`## Host requirements (roles → agents)`); this page only aggregates them.

| Skill | Roles it dispatches | Role assets shipped |
|---|---|---|
| `pdca` | `scout`, `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate` | `assets/agents/*.md` (5 files) |
| `pdca-coder` | `scout`, `planner`, `coder`, `check`, `escalate`, `security-auditor` | `assets/agents/*.md` (6 files) |
| `pdca-dotnet` | same as `pdca-coder`, plus the `dotnet-*` lenses | `assets/agents/*.md` (6 files) |
| `pdca-collection` | all of the above per task, plus the runner `pdca-orchestrator` | none (uses the family's) |
| `pdca-incremental` | `planner`, `coder`, `scout`, `check`, `escalate` + `pdca-orchestrator` | none (uses the family's) |

The runner **`pdca-orchestrator` is not shipped by any skill**: it is a shared host agent. Every
skill also needs a cheap-tier primary — the tier is taken from the host profile's effective tier,
not from the agent's name.

## 2. Install the skills

```sh
npx skills add AlexeyShirshov/skills@pdca-dotnet -g -y
```

One command per skill (`pdca`, `pdca-coder`, `pdca-dotnet`, `pdca-collection`,
`pdca-incremental`); `-g` installs for all projects, without it the CLI targets the current one.
From a checkout (paths are relative to the repository root):

```sh
cp -r opencode/pdca* ~/.config/opencode/skills/
```

Nothing else in the skill directory needs installing. The runtime workspace `.pdca/` is created by
the cycle itself in the project it runs in.

## 3. Install the role agents

OpenCode discovers agents at `~/.config/opencode/agents/<name>.md` (global) and
`.opencode/agents/<name>.md` (project). The file name or the `name` field gives the agent ID.

```sh
# pdca
cp opencode/pdca/assets/agents/*.md ~/.config/opencode/agents/

# or pdca-coder / pdca-dotnet
cp opencode/pdca-coder/assets/agents/*.md ~/.config/opencode/agents/
```

> **Name collision.** `pdca-coder` and `pdca-dotnet` ship agents under the **same** names
> (`planner`, `check`, `coder`, `escalate`, `scout`, `security-auditor`) with **different bodies** —
> the .NET copies carry the evidence contract and the inner-loop gate. Copying both into one
> directory silently overwrites one family with the other. Install one family's assets, or keep a
> single shared set (see §4).

### 4. Keep one shared set when you use several families

`pdca` uses distinct `pdca-*` names, so it never collides. `pdca-coder` and `pdca-dotnet` do, and a
third, richer copy may already live in your config repository. Pick one source of truth:

- **one family** — copy that skill's `assets/agents/*.md`;
- **shared host set** — keep `agents/*.md` in the host config repository and mirror it into the
  skill assets mechanically (this repository's config uses `tools/sync-roles.mjs --check` as a CI
  gate; `--fix` rewrites the asset frontmatter from the host agents).

Either way the role files carry only a `# tier:` label and permissions. **Never put a `model:` into
a role markdown** — model ids are bound by the host profile (§7).

## 5. Provide the runner `pdca-orchestrator`

It is a cheap **dispatcher**: it may call subagents, and may not edit, run commands or read files.
Minimal frontmatter (the body is the dispatcher prompt — see the skill's §Orchestrator role, or the
host's own copy):

```yaml
---
description: PDCA orchestrator (cheap tier) — drives one cycle via subagents; dispatches only.
mode: subagent
# tier: cheap
permissions:
  - action: subagent
    resource: "*"
    effect: deny
  - action: subagent
    resource: planner
    effect: allow
  - action: subagent
    resource: coder
    effect: allow
  - action: subagent
    resource: check
    effect: allow
  - action: subagent
    resource: escalate
    effect: allow
  - action: subagent
    resource: scout
    effect: allow
  - action: subagent
    resource: security-auditor
    effect: allow
  - action: subagent
    resource: pdca-planner
    effect: allow
  - action: subagent
    resource: pdca-executor
    effect: allow
  - action: subagent
    resource: pdca-check
    effect: allow
  - action: subagent
    resource: pdca-escalate
    effect: allow
  - action: edit
    resource: "*"
    effect: deny
  - action: shell
    resource: "*"
    effect: deny
  - action: skill
    resource: "*"
    effect: allow
---
```

Add `dotnet-*` (or any other lens the PLAN selects) to the allowlist if your tasks use them. Without
the runner, autonomous mode falls back to the flat cheap primary; normal mode keeps working.

## 6. Allow nested delegation

The runner drives a child cycle, so a subagent must be able to launch subagents. In V2 the depth
lives **only** under `experimental`:

```jsonc
{
  "experimental": {
    "subagent_depth": 3
  }
}
```

A top-level `subagent_depth` is accepted but **ignored** in V2 (warning
`omitted unsupported legacy setting`) and the depth falls back to a single level — the runner can no
longer delegate and every autonomous cycle degrades to the flat primary. Requires a restart.

## 7. Permissions: let the cheap primary dispatch

V2 uses one ordered `permissions` array; the action for child agents is **`subagent`** (V1 called it
`task`, and V2 config files still using `permission.task` are translated). A `build` primary already
allows everything. A primary with default-deny — `plan`, `architect`, or any custom read-only
primary — must allow each role explicitly:

```jsonc
{
  "permissions": [
    { "action": "*", "resource": "*", "effect": "deny" },
    { "action": "subagent", "resource": "scout", "effect": "allow" },
    { "action": "subagent", "resource": "planner", "effect": "allow" },
    { "action": "subagent", "resource": "coder", "effect": "allow" },
    { "action": "subagent", "resource": "check", "effect": "allow" },
    { "action": "subagent", "resource": "escalate", "effect": "allow" },
    { "action": "subagent", "resource": "security-auditor", "effect": "allow" },
    { "action": "subagent", "resource": "pdca-orchestrator", "effect": "allow" }
  ]
}
```

`pdca`-family names (`pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`) go in the same
list. The runner gets the same allowlist for its own children — and it may **not** widen the
expensive roles' permissions.

If the host forbids `general`/`explore`, do not bypass it: a missing role is a **resource blocker**
(normal mode: reported to you; autonomous: `Notice:` plus a recorded summary), not a silent run.

## 8. Bind models by tier

| Tier | Roles |
|---|---|
| cheap | `scout`, `coder` / `pdca-executor`, `pdca-orchestrator` |
| medium | `planner` / `pdca-planner`, `check` / `pdca-check`, `security-auditor` |
| strong | `escalate` / `pdca-escalate` |

Bind ids in the profile's agent block (or a project config), never in the role markdown:

```jsonc
{
  "agents": {
    "planner": { "model": "provider/model#high" },
    "check": { "model": "other-provider/other-model#high" },
    "coder": { "model": "cheap-provider/cheap-model" }
  }
}
```

A subagent with no binding inherits the invoking primary's model — it works out of the box, but the
whole cycle then runs on one (usually expensive) model. Prefer a CHECK model from a **different
family** than PLAN: an independent verdict is the point of the role.

## 9. Restart and verify

Agents load at startup:

```sh
opencode service restart
```

Then check, in this order:

1. **Agents are visible.** `opencode debug agents` must list every role the skill dispatches, plus
   `pdca-orchestrator`.
2. **Depth is applied.** `opencode debug config` must show `experimental.subagent_depth` ≥ 2. A
   warning about an ignored `subagent_depth` means it sits at the top level.
3. **Permissions resolve.** The same `debug agents` output shows the merged rule list per agent; the
   `subagent`/`edit`/`shell` rules must be present and in the right order (last match wins).
4. **Smoke run.** Start a trivial cycle on a throwaway task. Success criteria: the primary dispatches
   the planner (not itself), the executor writes the status file under `.pdca/`, and CHECK is done by
   `check`, not by the author. If you see `Notice:` in the status file, the cycle fell back — read
   the recorded reason instead of treating the run as normal.

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| A role is "not found" on dispatch | agent file missing, or installed into a directory the host does not discover | put it in `~/.config/opencode/agents/` (or `.opencode/agents/`), restart, re-check with `debug agents` |
| Cycle falls back to the flat primary | no `pdca-orchestrator`, or `subagent_depth` < 2, or the host forbids delegation | §5 and §6 |
| `Notice:` about a missing role | the skill's role name differs from the installed agent name (e.g. `pdca-planner` vs `planner`) | install the matching family, or alias the agent |
| A role behaves like its V1 twin | the asset uses the legacy `permission:` map | V2 translates it; the merged rules are visible in `debug agents` — prefer `permissions:` in new agents |
| Expensive model used for gathering | no tier binding in the profile | §8 |
| `.pdca/` reads are asked for approval | the host denies `.pdca/**` to the check/executor | allow `read`/`edit` on `.pdca/**` for those agents |

## 11. What the setup does not do

- It does not install the runner — §5 is manual by design.
- It does not grant commit or merge rights. `pdca-collection` needs an explicit project overlay or
  your request for `git merge --no-ff`; without it the group runs without commits and is marked
  `incomplete`. Push is never granted.
- It does not widen permissions for autonomous mode. Autonomy removes questions, not the gates.

The skill files remain the normative source: `opencode/<skill>/SKILL.md`, section
`## Host requirements (roles → agents)`.
