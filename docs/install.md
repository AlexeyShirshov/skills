# Setting up the host for the PDCA skill family

Installing a skill copies instructions only. A PDCA skill **names roles** — it creates no agents and
sets no models — so the cycle only runs after the host provides those agents, lets the cheap primary
dispatch them, and allows nested delegation. This page is the missing install checklist:
skills → agents → orchestrator → delegation depth → permissions → model bindings → restart →
verification. It is host-agnostic; the commands shown as the reference adapter are OpenCode V2, with
the OpenCode V1 mapping and the mapping for Claude Code, Codex and custom hosts (`dsh`, …) given
inline.

Without it the cycle does not fail loudly. It either degrades to the flat primary (a recorded
`Notice:`), or hits a resource blocker on the first dispatch.

## 1. What the skill expects from the host

The roles are **subagent names**. Every skill in the family is explicit about its own table
(`## Roles and host requirements`); this page only aggregates them.

| Skill | Roles it dispatches | Role assets shipped |
|---|---|---|
| `pdca` | `pdca-scout`, `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate` | `assets/opencode-agents/*.md` (6 files — the canonical shared set) |
| `pdca-coder` | `pdca-scout`, `pdca-planner`, `pdca-executor`, `pdca-check`, `pdca-escalate`, `pdca-security-auditor` | `assets/opencode-agents/*.md` (7 files — 6 byte-identical mirrors + specialist) |
| `pdca-dotnet` | same as `pdca-coder`, plus the `dotnet-*` lenses | `assets/opencode-agents/*.md` (7 files — 6 byte-identical mirrors + specialist) |
| `pdca-collection` | all of the above per item, plus the runner `pdca-orchestrator` | `assets/opencode-agents/pdca-orchestrator.md` (mirror) |
| `pdca-incremental` | `pdca-planner`, `pdca-executor`, `pdca-scout`, `pdca-check` per step, plus the runner `pdca-orchestrator` (the step's own cycle adds `pdca-escalate`) | `assets/opencode-agents/pdca-orchestrator.md` (mirror) |

Every shipped agent id carries the `pdca-` prefix and is **the same across the base and the overlays**,
so a skill never takes over a host's existing `planner`, `coder`, `scout`, `check` or `escalate` agent.

Agents carry only **identity, tier, permissions and an output contract**; decision knowledge
(routes, gates, checklists) lives in the skill and is loaded with it. The driver in particular
never classifies a task — it loads the contract of the form and the overlay that the plan declared.

The runner **`pdca-orchestrator` ships in every skill's `assets/opencode-agents/`** (the same file,
so any install carries it). Every skill also needs a cheap-tier primary — the tier is taken from the host
profile's effective tier, not from the agent's name. A medium or strong primary (for example
`architect`) **does not** launch or dispatch the cycle and does not run it flat itself: it hands off
explicitly to the cheap primary (`build` by default), preserving the task, the status file and the
`.pdca/` references, and that handoff is the only supported path into a cycle.

## 2. Install the skills

Install the whole skill directory: `SKILL.md`, `assets/`, and `scripts/` where the skill ships it.
Map the skills root to your host:

| Host | Skills root |
|---|---|
| OpenCode | `~/.config/opencode/skills/` (user), `.opencode/skills/` (project) |
| Claude Code | `~/.claude/skills/` (user), `.claude/skills/` (project) |
| Codex | `~/.codex/skills/` (or `$CODEX_HOME/skills`), project `.agents/skills/` |
| custom (`dsh`, …) | the host's own skills root; same layout `<root>/<id>/SKILL.md` |

The commands below are the OpenCode reference adapter — for another host, replace the destination
root.

```sh
npx skills add AlexeyShirshov/skills@pdca-dotnet -g -y
```

One command per skill (`pdca`, `pdca-coder`, `pdca-dotnet`, `pdca-collection`,
`pdca-incremental`); `-g` installs for all projects, without it the CLI targets the current one.
`pdca` is the single entry and the whole cycle; the two overlays and the two forms stay installable
on their own for an explicit invocation. Only `pdca` is advertised to the model: every other skill
carries `metadata.opencode/autoinvoke: false`, so it loads only by explicit ID (`@pdca-dotnet`) or
when the base PLAN selects that overlay or form. This is the deliberate split — the model cannot
pick a contract by phrase.
From a checkout (paths are relative to the repository root):

```sh
cp -r skills/pdca* ~/.config/opencode/skills/
```

For the PDCA family the global skills root is enough — OpenCode discovers
`~/.config/opencode/skills`. The `skills-keep.txt` + `curate-skills.mjs` pack is only for skills kept
in a custom `skills` source; if the family lives there, add the five ids to that list and rebuild it.

The helpers under the installed skill's `scripts/` are the **source** of the runtime copies — the
package you installed determines which ones exist (`pdca` and `pdca-coder` ship `pdca_cost.py` and
`plan_lint.py`; `pdca-dotnet` also ships `validate_inner_loop.py` and `pdca_evidence.py`). Before the first helper run,
`pdca-executor` stages them into the project's `.pdca/scripts/` as byte-identical copies, and every
command runs from the project root (`python3 .pdca/scripts/<helper>.py …`); a helper is never
executed from the installed skill directory. The `.pdca/` workspace itself is created by the cycle in
the project it runs in. `tests/` and the diagram generators under `assets/diagram/` are
development-only and not needed at runtime.

Keep the durable record and drop the local by-product — add once, in the project that runs cycles:

```gitignore
# PDCA: the status file is the durable record; evidence and staged helpers stay local
.pdca/*/rv*/
.pdca/scripts/
```


## 3. Install the role agents

Agents are **host subagent definitions**. The shipped `assets/opencode-agents/*.md` carry OpenCode
frontmatter (`mode: subagent`, `permission:`) over a portable role prompt; another host keeps the body
and translates the frontmatter:

| Host | Agents root | Frontmatter |
|---|---|---|
| OpenCode | `~/.config/opencode/agents/`, `.opencode/agents/` | as shipped (V1-native; V2 translates) |
| Claude Code | `~/.claude/agents/`, `.claude/agents/` | `name`, `description`, `tools`; express permissions via the tool allowlist, drop `mode`/`permission` |
| Codex | the host's subagent/workflow directory | keep the body, adapt the frontmatter |
| custom (`dsh`, …) | the host's agent root | keep the body, adapt the frontmatter |

If the host has no subagents, the cycle runs in the flat-primary fallback defined by the skill.

OpenCode discovers agents at `~/.config/opencode/agents/<name>.md` (global) and
`.opencode/agents/<name>.md` (project). The path gives the agent ID (a nested path becomes part of
it, e.g. `.opencode/agents/team/reviewer.md` → `team/reviewer`).

```sh
# pdca
cp skills/pdca/assets/opencode-agents/*.md ~/.config/opencode/agents/

# or pdca-coder / pdca-dotnet
cp skills/pdca-coder/assets/opencode-agents/*.md ~/.config/opencode/agents/
```

> **One shared set, generated mirrors.** The six shared roles (`pdca-planner`, `pdca-executor`,
> `pdca-check`, `pdca-escalate`, `pdca-scout`, `pdca-orchestrator`) have **one authoritative source**:
> `skills/pdca/assets/opencode-agents/`. `pdca-coder` and `pdca-dotnet` ship byte-identical real-file
> copies of those six (frontmatter, body and permissions), and `pdca-collection`/`pdca-incremental`
> carry only the same `pdca-orchestrator` copy. Regenerate or verify the mirrors with
> `python3 skills/pdca/scripts/sync_role_assets.py --check` (or `--fix`); the explicit allowlist
> never touches `pdca-security-auditor` or hand-written files. `pdca-security-auditor` is the only
> coder/.NET role that differs by design — it is a specialist gather role, not one of the shared six.
> Copying `pdca`/`pdca-coder`/`pdca-dotnet` assets therefore yields the same six roles; a form package
> (`pdca-collection`/`pdca-incremental`) contributes only the orchestrator and is combined with one of
> those six-role packages.

## 4. One authoritative source, host adapters kept separate

The base `skills/pdca/assets/opencode-agents/` is the **single source of truth** for the shared
roles. The overlay copies are generated from it, and a host config repository is an **adapter**, not
another source: never copy host role files back into the skills. Host-specific descriptions, model
tier bindings and frontmatter translation stay in that adapter/host profile and are applied when the
agent files are deployed.

- **one package** — copy `skills/pdca/assets/opencode-agents/*.md` (or the equivalent six-role
  mirror in `pdca-coder`/`pdca-dotnet`); add the form package's orchestrator if you use a form;
- **CI drift guard** — `python3 skills/pdca/scripts/sync_role_assets.py --check` fails on any
  missing or drifted mirror; `--fix` writes only the allowlisted mirror paths. The canonical files
  are never written by the generator.

Either way the role files carry only a `# tier:` label and permissions. **Never put a `model:` into
a role markdown** — model ids are bound by the host profile (§8).

> **Downstream migration is a separate step.** Vendoring this source into a config repository does
> **not** update an already deployed host. The current `opencode-config` `sync-roles` helper is tied
> to the old `pdca-dotnet` mirror and compares frontmatter settings — including permissions — and
> heading **levels**, but not instruction text. A heading-level mismatch may therefore be detected;
> an instruction-only edit is not, and its `--fix` preserves the existing body, so it cannot migrate
> instructions. After the source commit/push/vendor, the host role bodies must be migrated
> deliberately and re-verified — do not assume `vendor-skills` or `sync_role_assets.py --fix` updated
> them.

## 5. Install the runner `pdca-orchestrator`

The runner is the cheap **dispatcher** that drives one child cycle, one collection group or one
incremental step. It ships in every skill's `assets/opencode-agents/`, so step 3 copies it with the
rest — do not write your own, and do not keep an older host copy under the same id. The
`mode:`/`permission:` frontmatter is the legacy OpenCode adapter (V1-native; V2 translates it); other
hosts reuse the body.

What it must be (the asset already encodes this — check it after installation):

- `mode: subagent`, `# tier: cheap`, no `model:`;
- `edit`/`write`/`shell`: **deny** — it dispatches, it does not work;
- a `subagent` allowlist for `pdca-planner`/`pdca-executor`/`pdca-check`/`pdca-escalate`/
  `pdca-scout`/`pdca-security-auditor` (+ the `dotnet-*` lenses and `docfx-specialist` where used),
  with `*` denied;
- `skill` allowed (it loads the contract of the form and the overlay declared by the plan).

A host that already ships its own runner may keep it only if it grants the same allowlist; otherwise
the shipped copy should win, because a dispatcher without the `pdca-*` allowlist cannot start a
cycle. Without a runner at all, autonomous mode falls back to the flat cheap primary; normal mode
keeps working.

## 6. Allow nested delegation

The runner drives a child cycle, so a subagent must be able to launch subagents. The skill only needs
the **capability**; the host decides how it is spelled — OpenCode V2 keeps the depth **only** under
`experimental`, OpenCode V1 uses the top-level key, Claude Code and Codex use their own subagent
settings. Without it the documented flat-primary fallback applies.

OpenCode V2:

```jsonc
{
  "experimental": {
    "subagent_depth": 3
  }
}
```

OpenCode V1:

```jsonc
{
  "subagent_depth": 3
}
```

What the graph needs is not an abstract depth but the **edges a call must traverse**:
`primary → driver`, `driver → role`, and `escalate → scout` — three edges. On V2,
`experimental.subagent_depth` counts session-nesting edges below the primary (default `1`), and a
spawn is allowed only while the calling session's depth is below the configured limit. The number is
a budget for that counting rule, not a capability certificate: a configured value on its own does
**not** prove that the installed build supports the chain. Record the installed build's version and
rely on the smoke run (§9), not on the number. The value shown above is an example of a configured
setting, not a validated budget.

The forms are not interchangeable: V2 accepts a top-level `subagent_depth` but **ignores** it
(warning `omitted unsupported legacy setting`), and V1 ignores `experimental.subagent_depth`. In both
cases the depth falls back to a single level — the runner can no longer delegate and every autonomous
cycle degrades to the flat primary. Requires a restart.

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

OpenCode V1 uses the `permission` map and the `task` action; the `subagent` action and the
`permissions` array are V2-only:

```jsonc
{
  "permission": {
    "task": {
      "*": "deny",
      "pdca-*": "allow"
    },
    "skill": "allow"
  }
}
```

The `task` pattern matches the subagent name, last match wins; `pdca-*` covers the six roles, and
`skill` lets the runner load its contract. V1 has no `subagent` action to translate.

All six ids are the same across the base and the overlays (`pdca-planner`, `pdca-executor`, `pdca-check`,
`pdca-escalate`, `pdca-scout`, `pdca-security-auditor`), so one allowlist serves the family. The
runner gets the same allowlist for its own children — and it may **not** widen the expensive roles'
permissions.

If the host forbids `general`/`explore`, do not bypass it: a missing role is a **resource blocker**
(normal mode: reported to you; autonomous: `Notice:` plus a recorded summary), not a silent run.

### OpenCode V1 and V2 at a glance

| Item | V1 | V2 |
|---|---|---|
| nested delegation | top-level `subagent_depth` | `experimental.subagent_depth` |
| dispatch permission | `permission: { task: ... }` | `permissions: [{ action: "subagent", ... }]` |
| skill auto-selection | `metadata.opencode/autoinvoke: "false"` | same, plus optional `disable-model-invocation` |
| agent frontmatter | `mode: subagent`, `permission:` (native) | the same legacy map, translated |
| `skills` config | `{ paths, urls }` | one array |
| restart / verify | restart the TUI; `opencode agent list` | `opencode service restart`; `opencode debug agents` / `debug config` |

Both versions share the config locations and are not installed side by side by default; identify the
major with `opencode --version`. The install prompt (`docs/install-prompt.md`) takes
`OPENCODE_MAJOR=auto|1|2` and stops on an unknown or mismatched version.

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

Agents load at startup; the check differs per host:

| Host | Restart | Verify |
|---|---|---|
| OpenCode | `opencode service restart` | `opencode debug agents`, `opencode debug config` |
| Claude Code | start a new session | `/agents` lists the subagents |
| Codex | start a new session | the host's agent/workflow listing |
| custom (`dsh`, …) | per host | the host's equivalent of the two checks below |

OpenCode reference:

```sh
opencode service restart
```

Then check, in this order:

1. **Agents are visible.** `opencode debug agents` must list every role the skill dispatches, plus
   `pdca-orchestrator`.
2. **Delegation is configured.** `opencode debug config` must show the depth inside `experimental`
   (a warning about an ignored `subagent_depth` means it sits at the top level). Record the configured
   value, the installed host build version and the date — the value alone is not the check, the smoke
   run below is.
3. **Permissions resolve.** The same `debug agents` output shows the merged rule list per agent; the
   `subagent`/`edit`/`shell` rules must be present and in the right order (last match wins).
4. **Smoke run.** Start a trivial cycle on a throwaway task. Success criteria: the primary dispatches
   the `pdca-planner` (not itself), `pdca-executor` writes the status file under `.pdca/`, and CHECK is done by
   `pdca-check`, not by the author. The run must also produce a real delegation chain that reaches
   `escalate → scout` on a task that triggers escalation. If you see `Notice:` in the status file, the cycle fell back — read
   the recorded reason instead of treating the run as normal.

## 10. Preflight and fallback

Every collection lane and every campaign checks capability **before** it allocates work. The check is
about observable capability, not about a number in the config:

- are the mandatory roles resolvable — allowed by policy, loadable as agents, present in the host's
  agent list? Verify by resolution, never by dummy substantive work: no probe edits, probe tasks or
  fake steps.
- is nested delegation actually usable by the runner, and is `pdca-orchestrator` available as a
  subagent?
- is the `escalate → scout` edge reachable on every path where escalation may be needed?
- is the step's cycle contract loadable and not forbidden?

No numbers are invented here. `experimental.subagent_depth` is a configuration fact, not proof of the
chain (§6). No host-side parallel-cap key, schema entry or constant was found in the inspected V2
source; that absence is **not** evidence of unlimited concurrency, and `cap` values are not invented
either.

The installed runner may **drift** from the canonical asset in
`skills/pdca/assets/opencode-agents/`. Refresh it from the asset and verify its effective permissions
before relying on it: an installed
`pdca-orchestrator` that does not allow delegation to `pdca-scout` is the concrete observed example,
and it silently breaks `escalate → scout`. This is part of the checklist in §5, not something the
repository's tests can see, and it needs no change to the rest of the host configuration.

Failure semantics:

| Condition | Behaviour |
|---|---|
| driver unavailable (no agent, no nested delegation, preflight failed) | exactly one fallback: the cheap primary runs inline and writes `Notice:` with a durable reason (normal mode also tells you) |
| mandatory role unavailable | resource stop: no other agent takes over; the run stops and records what was already accepted |
| cycle contract unavailable | fail closed: no substitute contract, no "similar" cycle, no generic execution |
| discovered late (after start) | safe pause before the dependent action; the gate is never weakened |

## 11. Verification status: unverified

**Status: OPEN — prerequisite documented, not established.**

Cold-host installation is **not verified** in this repository. Not verified:

- installation on a clean host;
- execution of `primary → driver → roles`, including a real delegation reaching `escalate → scout`;
- the installed host build version and the effective permissions of the installed agents;
- the collection-lane mode and its observed fallback behaviour.

Green repository tests do not verify a clean-host installation: they check contracts, assets and
documentation, not a host. A green suite says nothing about whether your host can run the chain.

**Closing trigger.** The operator performs an authorized clean-host run and records:

- the actual host build/version and the execution date;
- availability of all six required roles;
- the collection-lane mode and the observed fallback behaviour;
- a real delegation chain reaching `escalate → scout`;
- execution results and the supporting logs.

A separate follow-up cycle records that evidence on this page. Only that follow-up cycle may change
this status from OPEN; completing a step here, or a green repository run, does not.

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| A role is "not found" on dispatch | agent file missing, or installed into a directory the host does not discover | put it in `~/.config/opencode/agents/` (or `.opencode/agents/`), restart, re-check with `debug agents` |
| Cycle falls back to the flat primary | no `pdca-orchestrator`, no usable nested delegation (legacy key ignored, limit too low), or the host forbids delegation | §5 and §6 |
| `Notice:` about a missing role | the skill's role name differs from the installed agent name (e.g. `pdca-planner` vs `pdca-planner`) | install the matching family, or alias the agent |
| A role behaves like its V1 twin | the asset uses the legacy `permission:` map | V2 translates it (`permission` → `permissions`, `task` → `subagent`, `bash` → `shell`, `write`/`patch` → `edit`); the merged rules are visible in `debug agents` — prefer `permissions:` in new agents |
| A rule has no effect | the asset names an action outside the V2 Core list | `todowrite`, `doom_loop` and `list` are not V2 Core permission actions (plugins may define their own). They pass through the config but match no built-in tool. Harmless, but do not rely on them |
| Expensive model used for gathering | no tier binding in the profile | §8 |
| `.pdca/` reads are asked for approval | the host denies `.pdca/**` to the check/executor | allow `read`/`edit` on `.pdca/**` for those agents |

## 13. What the setup does not do

- It does not choose or bind models; without tier bindings every role inherits the primary's model
  (§8).
- It does not grant commit or merge rights. `pdca-collection` needs an explicit project overlay or
  your request for `git merge --no-ff`; without it the group runs without commits and is marked
  `incomplete`. Push is never granted.
- It does not widen permissions for autonomous mode. Autonomy removes questions, not the gates.

## 14. Let an agent install it

The checklist is packaged as a copy-paste prompt: [`install-prompt.md`](install-prompt.md). Fill its
`Inputs` block — including `HOST=opencode|claude|codex|dsh|custom` — send it to a cheap primary (e.g.
`build`), and the agent performs the steps idempotently, with backups, a restart and the verification
of §9.

The skill files remain the normative source: `skills/<skill>/SKILL.md`, section
`## Roles and host requirements`.
