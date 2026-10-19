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
| `pdca` | `pdca-scout`, `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate` | `assets/agents/*.md` (6 files) |
| `pdca-coder` | `pdca-scout`, `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`, `pdca-security-auditor` | `assets/agents/*.md` (7 files) |
| `pdca-dotnet` | same as `pdca-coder`, plus the `dotnet-*` lenses | `assets/agents/*.md` (7 files) |
| `pdca-collection` | all of the above per task, plus the runner `pdca-orchestrator` | `assets/agents/pdca-orchestrator.md` |
| `pdca-incremental` | `pdca-planner`, `pdca-executor`, `pdca-scout`, `pdca-check` per block, plus the runner `pdca-orchestrator` (the step's own cycle adds `pdca-escalate`) | `assets/agents/pdca-orchestrator.md` |

Every shipped agent id carries the `pdca-` prefix and is **the same across the variants**, so a
skill never takes over a host's existing `planner`, `coder`, `scout`, `check` or `escalate` agent.

The runner **`pdca-orchestrator` ships in every skill's `assets/agents/`** (the same file, so any
install carries it). Every skill also needs a cheap-tier primary — the tier is taken from the host
profile's effective tier, not from the agent's name. A medium or strong primary (for example `architect`) **does not** drive
the cycle; switch to the cheap primary (`build` by default) before asking for a cycle.

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
`.opencode/agents/<name>.md` (project). The path gives the agent ID (a nested path becomes part of
it, e.g. `.opencode/agents/team/reviewer.md` → `team/reviewer`).

```sh
# pdca
cp opencode/pdca/assets/agents/*.md ~/.config/opencode/agents/

# or pdca-coder / pdca-dotnet
cp opencode/pdca-coder/assets/agents/*.md ~/.config/opencode/agents/
```

> **One variant, one asset set.** All three cycle variants ship **the same six ids**
> (`pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`, `pdca-scout`, and — in the
> `pdca-coder`/`pdca-dotnet` variants — `pdca-security-auditor`) with **different bodies**: `pdca` is
> domain-neutral, `pdca-coder` selects a toolchain per task, `pdca-dotnet` carries the evidence
> contract and the inner-loop gate. Copying two variants into one directory silently overwrites
> one with the other. Install one variant's assets, or keep a single shared set (§4).

## 4. Keep one shared set when you use several families

The variants are alternatives, not layers: their role ids coincide by design, so one deployed copy
always wins. A third, richer copy may already live in your config repository. Pick one source of
truth:

- **one family** — copy that skill's `assets/agents/*.md`;
- **shared host set** — keep the role files in your host config repository and mirror them into the
  skill assets mechanically (a small sync script that rewrites the asset frontmatter from the host
  agents and fails in CI when they drift). This is what keeps a `.NET` host from silently losing the
  `pdca-coder` bodies, and vice versa.

Either way the role files carry only a `# tier:` label and permissions. **Never put a `model:` into
a role markdown** — model ids are bound by the host profile (§8).

## 5. Install the runner `pdca-orchestrator`

The runner is the cheap **dispatcher** that drives one child cycle, one collection group or one
incremental step. It ships in every skill's `assets/agents/`, so step 3 copies it with the rest — do
not write your own, and do not keep an older host copy under the same id.

What it must be (the asset already encodes this — check it after installation):

- `mode: subagent`, `# tier: cheap`, no `model:`;
- `edit`/`write`/`shell`: **deny** — it dispatches, it does not work;
- a `subagent` allowlist for `pdca-planner`/`pdca-executor`/`pdca-check`/`pdca-escalate`/
  `pdca-scout`/`pdca-security-auditor` (+ the `dotnet-*` lenses and `docfx-specialist` where used),
  with `*` denied;
- `skill` allowed (it loads the selected variant).

A host that already ships its own runner may keep it only if it grants the same allowlist; otherwise
the shipped copy should win, because a dispatcher without the `pdca-*` allowlist cannot start a
cycle. Without a runner at all, autonomous mode falls back to the flat cheap primary; normal mode
keeps working.

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
    { "action": "subagent", "resource": "pdca-scout", "effect": "allow" },
    { "action": "subagent", "resource": "pdca-planner", "effect": "allow" },
    { "action": "subagent", "resource": "pdca-executor", "effect": "allow" },
    { "action": "subagent", "resource": "pdca-check", "effect": "allow" },
    { "action": "subagent", "resource": "pdca-escalate", "effect": "allow" },
    { "action": "subagent", "resource": "pdca-security-auditor", "effect": "allow" },
    { "action": "subagent", "resource": "pdca-orchestrator", "effect": "allow" }
  ]
}
```

All six ids are the same in every variant (`pdca-planner`, `pdca-executor`, `pdca-check`,
`pdca-escalate`, `pdca-scout`, `pdca-security-auditor`), so one allowlist serves the family. The
runner gets the same allowlist for its own children — and it may **not** widen the expensive roles'
permissions.

If the host forbids `general`/`explore`, do not bypass it: a missing role is a **resource blocker**
(normal mode: reported to you; autonomous: `Notice:` plus a recorded summary), not a silent run.

## 8. Bind models by tier

| Tier | Roles |
|---|---|
| cheap | `pdca-scout`, `pdca-executor`, `pdca-orchestrator` |
| medium | `pdca-planner`, `pdca-check`, `pdca-security-auditor` |
| strong | `pdca-escalate` |

Bind ids in the profile's agent block (or a project config), never in the role markdown:

```jsonc
{
  "agents": {
    "pdca-planner": { "model": "provider/model#high" },
    "pdca-check": { "model": "other-provider/other-model#high" },
    "pdca-executor": { "model": "cheap-provider/cheap-model" }
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
   the `pdca-planner` (not itself), `pdca-executor` writes the status file under `.pdca/`, and CHECK is done by
   `pdca-check`, not by the author. If you see `Notice:` in the status file, the cycle fell back — read
   the recorded reason instead of treating the run as normal.

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| A role is "not found" on dispatch | agent file missing, or installed into a directory the host does not discover | put it in `~/.config/opencode/agents/` (or `.opencode/agents/`), restart, re-check with `debug agents` |
| Cycle falls back to the flat primary | no `pdca-orchestrator`, or `subagent_depth` < 2, or the host forbids delegation | §5 and §6 |
| `Notice:` about a missing role | the skill's role name differs from the installed agent name (e.g. `pdca-planner` vs `pdca-planner`) | install the matching family, or alias the agent |
| A role behaves like its V1 twin | the asset uses the legacy `permission:` map | V2 translates it (`permission` → `permissions`, `task` → `subagent`, `bash` → `shell`, `write`/`patch` → `edit`); the merged rules are visible in `debug agents` — prefer `permissions:` in new agents |
| A rule has no effect | the asset names an action outside the V2 Core list | `todowrite`, `doom_loop` and `list` are not V2 Core permission actions (plugins may define their own). They pass through the config but match no built-in tool. Harmless, but do not rely on them |
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
