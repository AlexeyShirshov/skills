# Install prompt: the role agents for this skill

The role definitions travel with the installed skill, in its own `assets/opencode-agents/` — nothing
has to be copied by hand before this prompt is used. Hand the fenced prompt below to a session that
may write host configuration (a `build` primary on OpenCode, the main session on Claude Code or
Codex), with the values in `Context` filled in. It installs or refreshes the agents idempotently,
binds models by tier, makes backups, and stops on anything it cannot verify.

The base `pdca` skill runs the same check before its first dispatch: when a role does not resolve, it
stops and points here instead of substituting an agent.

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
   - Source roles: $SKILL_DIR/assets/opencode-agents/*.md. If the coder or .NET overlay is
     installed (pdca-coder / pdca-dotnet), take pdca-security-auditor from that skill's
     assets/opencode-agents/ as well; the six shared roles always come from pdca.
   - Target by host:
     opencode : <config>/agents (global, normally ~/.config/opencode/agents) or
                <PROJECT>/.opencode/agents (project)
     claude   : ~/.claude/agents or <PROJECT>/.claude/agents
     codex    : $CODEX_HOME/agents (personal, normally ~/.codex/agents) or
                <PROJECT>/.codex/agents (project) — one TOML file per role;
     custom (dsh, ...): the host's agent root — if you cannot establish it, ask instead of guessing.
1. Write every role file.
   - opencode: copy as-is. The frontmatter carries both the V1 `permission:` map and the equivalent
     V2 `permissions:` list, and is meant to be used unchanged.
   - claude: write a translated copy — frontmatter `name` (same as the shipped one), `description`
     (same text), `tools` from this table, `model` from step 4; then the shipped body,
     byte-identical. Drop `mode`, `permission`, `permissions` and `steps`: Claude Code ignores
     unknown fields silently, so a leftover `permission:` map would look enforced while enforcing
     nothing, and an absent `tools:` field would inherit every tool.

     | Role | Tier | Claude Code `tools:` |
     |---|---|---|
     | `pdca-scout` | cheap | `Read, Grep, Glob, Bash` |
     | `pdca-planner` | medium | `Read` |
     | `pdca-executor` | cheap | `Read, Write, Edit, Bash, Glob, Grep` |
     | `pdca-check` | medium | `Read, Grep, Glob` |
     | `pdca-escalate` | strong | `Read, Grep, Glob, Agent` |
     | `pdca-orchestrator` | cheap | `Read, Agent, Skill` |
     | `pdca-security-auditor` | medium | `Read, Grep, Glob` |

   - codex: one TOML file per role, `<role>.toml`, with only these keys:
       name = "<role>"
       description = "<the shipped description>"
       developer_instructions = """<the shipped body, frontmatter dropped>"""
     Convert the body into that multi-line string without reflowing it: escape every backslash and
     any `"""` it contains, keep the rest byte-for-byte. Do not carry over `mode`, `permission`,
     `permissions`, `steps` or the `# tier:` label — Codex has no permission map and reads only its
     own keys. For the roles that must not run commands add `features.shell_tool = false`
     (pdca-planner, pdca-check, pdca-orchestrator). Codex has no per-agent switch for file edits: a
     read-only rule for pdca-executor or pdca-escalate stays an instruction in the body — say so in
     the report.
   - another host: keep the body unchanged and translate only the frontmatter.
   - An existing file with the same content: leave it untouched and report it as unchanged.
   - An existing file with different content: back it up first (the same file name plus
     `.bak-<UTC timestamp>`), then overwrite it. Never edit a role body in place.
2. Do not invent anything: no `model:` in a shipped role file, no tool name, model id or
   configuration key that this host does not have. On Claude Code a role whose `tools:` entry
   resolves to nothing fails to launch; on Codex a key it does not know is a TOML error or is
   silently ignored — verify both against the installed build.
3. Allow dispatch and nested delegation:
   - opencode V2: `experimental.subagent_depth` in the `experimental` section — a top-level
     `subagent_depth` is ignored by V2. `permissions`: action `subagent` allowed for pdca-scout,
     pdca-planner, pdca-executor, pdca-check, pdca-escalate, pdca-security-auditor,
     pdca-orchestrator; `skill` allowed.
   - opencode V1: top-level `subagent_depth`; `permission.task` with `"*": "deny"` and
     `"pdca-*": "allow"` (the `subagent` action and the `permissions` array are V2-only — do not
     create them in V1).
   - claude: nesting is on by default (three layers below the main conversation). The spawning tool
     is `Agent` (older builds call it `Task`; the old name still works) and it must be in the
     `tools:` list of the two delegating roles — pdca-orchestrator and pdca-escalate. The depth is
     changed with CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH in settings.json (1 disables nesting); the
     needed chain is primary → driver → role → scout. Note that inside a subagent an `Agent(type)`
     list is ignored, so a child allowlist cannot be enforced by `tools` — the role body carries it.
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
   - claude: the `model` field of each agent file — an alias (sonnet, opus, haiku, fable), a full
     model id, or `inherit`. There is no separate profile map: the file is the binding, so a refresh
     must re-apply `model` and never drop it. If CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1 is set, the field
     is ignored by the host — check and report that instead of pretending the binding works.
   - codex: `model` and `model_reasoning_effort` in each role's TOML file — the file wins over the
     `[agents]` default, and a role without them inherits the parent session. `[agents]
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
     again, then delegate to a role on a throwaway task — the agent thread opening under that name is the check, and the thread shows
     the model it runs on. Roles inherit the parent's skills, and skill discovery under
     `$CODEX_HOME/skills`, `~/.agents/skills` and the project `.agents/skills`/`.codex/skills` varies
     by build, so confirm the `pdca` skill is listed as available in the same session.
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
  specialist and comes from that overlay.
- **Why a prompt and not a script.** Copying the files is mechanical; the rest is not. On OpenCode
  the tier bindings live in a commented JSONC profile merged from more than one place; on Claude Code
  they are the `model:` field of each translated file, with a per-role tool allowlist; on Codex they
  are the `model` and `model_reasoning_effort` keys of each TOML file, and the role body has to
  survive the conversion into a TOML string unchanged. All three need ids the host really offers. A
  script can copy bytes; it cannot choose a model, a tool set or an escaped body without inventing
  values or destroying the file it edits.
- **What Claude Code cannot enforce, and how it is handled here.** There is no per-agent permission
  map and no per-command shell scoping: `Bash` is granted whole. So `pdca-scout` keeps `Bash` (its
  fixed read-only literals are its job) and `pdca-escalate` gets facts through `pdca-scout` instead
  of a shell of its own; `pdca-planner` and `pdca-check` get no `Bash` and no write tool at all. The
  driver's child allowlist becomes a prompt-level rule, because `Agent(type)` is ignored inside a
  subagent. Add `permissions.deny` rules in settings.json if the session needs those boundaries
  enforced rather than declared.
- **What Codex cannot enforce.** A custom agent file inherits the parent's sandbox, approval policy
  and MCP servers, and the only capability switches are feature toggles such as
  `features.shell_tool`. There is no per-agent permission map and no per-agent edit switch, so the
  read-only roles rely on their instructions plus, where it applies, `features.shell_tool = false`.
  Whether a subagent may spawn its own children is host-managed in the documented configuration —
  check the installed build before promising the autonomous chain.
- The full host checklist — delegation depth, permissions, model bindings, restart and the
  verification status — is in the repository's `docs/install.md` §3–§9; this prompt covers the
  agents and their bindings.
