# Install prompt: the role agents for this skill

The role definitions travel with the installed skill in **three ready-to-copy sets**, one per
harness, so nothing is translated at install time:

| Harness | Shipped set | Envelope |
|---|---|---|
| OpenCode | `assets/opencode-agents/*.md` | canonical — V1 `permission:` map and equivalent V2 `permissions:` list |
| Claude Code | `assets/claude-agents/*.md` | `name`, `description`, `tools` |
| Codex | `assets/codex-agents/*.toml` | `name`, `description`, `developer_instructions`, shell feature flag |

The canonical set is authored by hand; the other two are generated from it by
`skills/pdca/scripts/gen_host_agents.py` (`--check` in CI) and carry the role body byte-for-byte.
None of the three sets carries a model — that is the one thing the installer must bind, and only
the host knows which ids it offers.

Hand the fenced prompt below to a session that may write host configuration (a `build` primary on
OpenCode, the main session on Claude Code or Codex), with the values in `Context` filled in. It
copies the files idempotently, binds models by tier, makes backups, and stops on anything it cannot
verify. The base `pdca` skill runs the same check before its first dispatch: when a role does not
resolve, it stops and points here instead of substituting an agent.

## Context (fill before sending)

```text
SKILL_DIR=<absolute path of the installed skill, e.g. ~/.config/opencode/skills/pdca>
HOST=<opencode | claude | codex | dsh | custom>
SCOPE=<global | project>
PROJECT=<project root, only for SCOPE=project>
PROFILE=<opencode profile that holds the agents block; empty = do not touch bindings>
MODELS=<cheap=<model>, medium=<model>, strong=<model> | ask>
```

`MODELS` means the host's own model ids: `provider/model` on OpenCode, an alias or full id on Claude
Code, a Codex model name such as `gpt-6-luna` on Codex.

## Prompt

```text
You are installing or refreshing the PDCA role agents in this host. Work idempotently, make backups,
do not commit or push, and stop and ask whenever a value is missing or ambiguous. Use only the files
named below — do not fetch a different version from the network or from another skill.

SKILL_DIR=<...>
HOST=<opencode | claude | codex | dsh | custom>
SCOPE=<global | project>
PROJECT=<...>
PROFILE=<...>
MODELS=<...>

0. Resolve the paths and show the plan (files, target directory, backups, bindings) before writing.
   - Source files are the host's own shipped set — OpenCode `assets/opencode-agents/*.md`,
     Claude Code `assets/claude-agents/*.md`, Codex `assets/codex-agents/*.toml`. If the coder or
     .NET overlay is installed (pdca-coder / pdca-dotnet), take pdca-security-auditor from that
     skill's same directory; the six shared roles always come from pdca.
   - Target by host:
     opencode : <config>/agents (global, normally ~/.config/opencode/agents) or
                <PROJECT>/.opencode/agents (project)
     claude   : ~/.claude/agents or <PROJECT>/.claude/agents
     codex    : $CODEX_HOME/agents (personal, normally ~/.codex/agents) or
                <PROJECT>/.codex/agents (project)
     custom (dsh, ...): the host's agent root — if you cannot establish it, ask instead of guessing.
1. Copy every file of the host's set unchanged. Do not translate, rewrite, reformat or "fix" them:
   the envelope is already the host's, and the body is the role contract.
   - opencode: `.md` files as they are; the frontmatter carries both the V1 `permission:` map and
     the equivalent V2 `permissions:` list.
   - claude: `.md` files as they are; the frontmatter carries `name`, `description` and the `tools`
     allowlist that is the role's whole permission boundary.
   - codex: `.toml` files as they are; `developer_instructions` is the role body, and the read-only
     roles already carry `features.shell_tool = false` (Codex has no per-agent edit switch, so
     read-only for the other roles is an instruction in the body, not a setting).
   - An existing file with the same content: leave it untouched and report it as unchanged.
   - An existing file with different content: back it up first (the same file name plus
     `.bak-<UTC timestamp>`), then overwrite it. Never edit a role body in place.
2. Do not invent anything: no `model:` in a copied file (models are bound in step 4), no tool name,
   model id or configuration key that this host does not have. A Claude Code role whose `tools:`
   entry resolves to nothing fails to launch; on Codex an unknown key is a TOML error or is silently
   ignored — check the installed build rather than assuming.
3. Allow dispatch and nested delegation:
   - opencode V2: `experimental.subagent_depth` in the `experimental` section — a top-level
     `subagent_depth` is ignored by V2. `permissions`: action `subagent` allowed for pdca-scout,
     pdca-planner, pdca-executor, pdca-check, pdca-escalate, pdca-security-auditor,
     pdca-orchestrator; `skill` allowed.
   - opencode V1: top-level `subagent_depth`; `permission.task` with `"*": "deny"` and
     `"pdca-*": "allow"` (the `subagent` action and the `permissions` array are V2-only — do not
     create them in V1).
   - claude: nesting is on by default (three layers below the main conversation). The spawning tool
     is `Agent` (older builds call it `Task`; the old name still works) and the shipped set already
     lists it for pdca-orchestrator and pdca-escalate. The depth is changed with
     CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH in settings.json (1 disables nesting); the needed chain is
     primary → driver → role → scout. Inside a subagent an `Agent(type)` list is ignored, so a child
     allowlist cannot be enforced by `tools` — the role body carries it.
   - codex: multi-agent work is on unless `[agents] enabled = false`. `[agents]` also takes
     `max_concurrent_threads_per_session` (`max_threads` is a legacy alias), `default_subagent_model`
     and `default_subagent_reasoning_effort`. The published documentation has no nesting-depth key;
     some builds accept `agents.max_spawn_depth`. Do not invent it: if the installed build documents
     the key, raise it to cover primary → driver → role → scout; otherwise record that depth is
     host-managed and verify it in the smoke run. A custom agent file cannot set `sandbox_mode`,
     `approval_policy`, `model_provider` or `mcp_servers` — Codex ignores them there, so do not write
     them.
   - another host: enable nested subagents with the host's own mechanism; if its format is unknown,
     ask.
4. Bind models by tier: cheap = pdca-scout, pdca-executor, pdca-orchestrator; medium = pdca-planner,
   pdca-check, pdca-security-auditor; strong = pdca-escalate.
   - opencode: the profile's agent block (the `agents` map in <config>/profiles/<name>.jsonc, or a
     project `opencode.json(c)`), written as { "<role>": { "model": "<provider>/<model>" } }. That
     file is JSONC with comments and may be merged from several places: edit it as text, keep every
     comment, key order and the existing formatting. Never rewrite it with a JSON serializer.
   - claude: add `model:` to the frontmatter of each copied file — an alias (sonnet, opus, haiku,
     fable), a full model id, or `inherit`. Keep `name`, `description` and `tools` intact. There is
     no separate profile map: the file is the binding, so a refresh must re-apply `model` and never
     drop it. If CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1 is set, the field is ignored by the host — check
     and report that instead of pretending the binding works.
   - codex: add `model` and `model_reasoning_effort` to each copied `.toml` file — the file wins over
     the `[agents]` default, and a role without them inherits the parent session. `[agents]
     default_subagent_model` is one model for every spawned agent; use it only when the user wants
     no tier split. Choose an effort the selected model supports; do not invent levels.
   - If MODELS is empty or says "ask": do not guess and do not copy an id from another host. List
     the roles without a binding, the ids the host already uses, and ask the user — or leave them
     unbound and say so in the report. An unbound role silently inherits the invoking primary's
     model, which defeats the tier split.
   - Only ids the host actually offers. If you cannot confirm an id, ask instead of writing it.
5. Restart the host so the agents load, then verify: every role the skill dispatches resolves —
   pdca-scout, pdca-planner, pdca-executor, pdca-check, pdca-escalate, pdca-orchestrator (and
   pdca-security-auditor where installed) — the delegation setting sits in the place this host build
   actually reads, and each role runs on the model its binding names.
   - opencode: `opencode debug agents` and `opencode debug config` (V1: `opencode agent list`).
   - codex: the agent is identified by its `name`; open a new thread so the agent files are loaded
     again, then delegate to a role on a throwaway task — the agent thread opening under that name is
     the check, and the thread shows the model it runs on. Roles inherit the parent's skills, and
     skill discovery under `$CODEX_HOME/skills`, `~/.agents/skills` and the project
     `.agents/skills`/`.codex/skills` varies by build, so confirm the `pdca` skill is listed as
     available in the same session.
   - claude: edits under an existing agents directory are picked up within seconds; a newly created
     agents directory needs a restarted session. `/agents` lists the subagents (builds up to
     2.1.197 open a wizard), `/tasks` shows the model each running subagent uses, and
     `claude plugin validate <agents-dir>` reports files whose frontmatter does not parse. On an
     older build, check ~/.claude/debug/<session-id>.txt for unrecognized frontmatter fields.
6. Report a table: file | created / updated / unchanged | backup path, then the bindings actually
   written, then what remains manual (profile, permissions outside this checklist) and the result of
   each check.
```

## Notes

- One shared set: the six roles are canonical in `pdca` and byte-identical mirrors in the overlays,
  so refreshing from `pdca` updates them all. `pdca-security-auditor` is the one coder/.NET
  specialist and comes from that overlay. `claude-agents/` and `codex-agents/` are generated from
  the same canonical files — edit the canonical asset, then run
  `python3 skills/pdca/scripts/gen_host_agents.py --fix`, never a generated file.
- **Why a prompt and not a script.** The conversion is mechanical, so it is generated and checked in;
  what remains is the part a generator cannot decide: which model ids this host offers, where its
  bindings live, and whether the installed build actually supports the delegation chain. A script
  can copy bytes; it cannot pick a model without inventing an id.
- **What each host cannot enforce, and how the shipped set is shaped.** Claude Code has no
  permission map and no per-command shell scoping: `Bash` is granted whole, so `pdca-scout` keeps it
  (its fixed read-only literals are its job) and `pdca-escalate` gets facts through `pdca-scout`
  instead of a shell of its own, while `pdca-planner` and `pdca-check` get no `Bash` and no write
  tool. Codex inherits the parent's sandbox, approval policy and MCP servers, and its only switches
  are feature toggles — hence `features.shell_tool = false` on the roles that must not run commands
  and no per-agent edit switch at all. Add `permissions.deny` rules in the host's settings if those
  boundaries must be enforced rather than declared.
- The full host checklist — delegation depth, permissions, model bindings, restart and the
  verification status — is in the repository's `docs/install.md` §3–§9; this prompt covers the
  agents and their bindings.
