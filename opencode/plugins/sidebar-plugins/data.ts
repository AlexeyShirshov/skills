// Pure data layer for the `sidebar-plugins` CLI plugin: turns the server plugin
// list plus on-disk CLI plugin directories into rows for the sidebar.
//
// Everything here is dependency free (node builtins only) so it can be exercised
// outside the TUI, e.g. `bun data.ts` against a dumped `/api/plugin` response.
//
// "Affects context" means the plugin puts something into the model prompt or the
// tool catalog: tool schemas, prompt text, agents, skills, references, MCP
// servers, or the config that decides what of that survives (permissions filter,
// tool-output truncation, compaction). Everything else — providers, websearch
// backends, VCS, integrations, TUI widgets — never reaches the prompt.

import { readFileSync, readdirSync, statSync } from "node:fs"
import { createHash } from "node:crypto"
import { homedir } from "node:os"
import { basename, dirname, extname, join } from "node:path"

export type PluginStatus = "active" | "failed" | "inactive" | "unsupported"

export type PluginItem = {
  key: string
  name: string
  status: PluginStatus
  detail?: string
  error?: string
  runtime: "server" | "cli"
  builtin: boolean
  group: string
  /** Does this plugin put anything into the model context? */
  context: boolean
}

export type RawPlugin = {
  id?: string
  source?: { type?: string; path?: string; target?: string; version?: string }
  features?: { server?: boolean; tui?: boolean; rpc?: boolean }
  state?: { status?: string; error?: string }
}

type Group = { id: string; label: string; context: boolean }

const groups: Group[] = [
  { id: "tools", label: "Tools", context: true },
  { id: "prompt", label: "Prompt", context: true },
  { id: "agent", label: "Agent", context: true },
  { id: "skill", label: "Skill", context: true },
  { id: "config", label: "Config", context: true },
  { id: "mcp", label: "MCP", context: true },
  { id: "provider", label: "Providers", context: false },
  { id: "websearch", label: "Websearch", context: false },
  { id: "other", label: "Other", context: false },
]

/**
 * What each builtin plugin actually registers. Taken from the builtin setup code
 * in opencode v2.0.28 (not from the id prefix — that guess was wrong both ways:
 * `tool.input.repair` adds no tool, `command` adds only slash commands, while
 * `mcp.codemode.defaults` does shape the Code Mode catalog).
 *
 * `context: false` entries are kept in the table on purpose: they sit under a
 * prefix that looks context-ish but the code says otherwise.
 *
 * `providers` marks builtins that only fire for those provider families — they
 * ship per-provider prompt files, so for any other model they add nothing.
 */
type Builtin = { group: string; context: boolean; providers?: string[]; note?: string }

const builtinTable: Record<string, Builtin> = {
  // tool.transform → tool schema in the model's tool catalog
  "opencode.tool.patch": { group: "tools", context: true },
  "opencode.tool.edit": { group: "tools", context: true },
  "opencode.tool.glob": { group: "tools", context: true },
  "opencode.tool.grep": { group: "tools", context: true },
  "opencode.tool.read": { group: "tools", context: true },
  "opencode.tool.shell": { group: "tools", context: true },
  "opencode.tool.skill": { group: "tools", context: true },
  "opencode.tool.subagent": { group: "tools", context: true },
  "opencode.tool.webfetch": { group: "tools", context: true },
  "opencode.tool.websearch": { group: "tools", context: true },
  "opencode.tool.write": { group: "tools", context: true },
  "opencode.tool.question": { group: "tools", context: true },
  // tools.opencode.* namespace + list/read MCP resource tools, plus system text
  "opencode.tools": { group: "tools", context: true },
  "opencode.tools.mcp-resources": { group: "tools", context: true },
  // tool.hook("execute.before") only repairs inputs of existing tools
  "opencode.tool.input.repair": { group: "tools", context: false },

  // session.hook("context") → text spliced into the system prompt
  "opencode.prompt.identity": { group: "prompt", context: true },
  "opencode.prompt.openai": { group: "prompt", context: true, providers: ["openai", "chatgpt", "codex", "azure", "copilot"] },
  "opencode.prompt.anthropic": { group: "prompt", context: true, providers: ["anthropic", "claude"] },
  "opencode.prompt.kimi": { group: "prompt", context: true, providers: ["kimi", "moonshot"] },
  "opencode.prompt.meta": { group: "prompt", context: true, providers: ["meta", "llama"] },
  "opencode.prompt.arcee": { group: "prompt", context: true, providers: ["arcee", "trinity"] },
  // sets the request option `textVerbosity`, adds no prompt text
  "opencode.prompt.verbosity": { group: "prompt", context: false },

  // agent.transform → agent definitions offered to the model
  "opencode.agent": { group: "agent", context: true },
  "opencode.plan": { group: "agent", context: true },

  // skill.transform → skill list in the prompt
  "opencode.skill": { group: "skill", context: true },
  "opencode.config.skill": { group: "skill", context: true },

  // config that decides what lands in the prompt
  "opencode.config.agent": { group: "config", context: true },
  "opencode.config.instruction": { group: "config", context: true },
  "opencode.config.reference": { group: "config", context: true },
  "opencode.config.compatibility": { group: "config", context: true },
  "opencode.config.policy": { group: "config", context: true },
  "opencode.config.tool-output": { group: "config", context: true },
  "opencode.config.compaction": { group: "config", context: true },
  // config of things that never reach the prompt
  "opencode.config.command": { group: "config", context: false },
  "opencode.config.formatter": { group: "config", context: false },
  "opencode.config.image": { group: "config", context: false },
  "opencode.config.provider": { group: "config", context: false },
  "opencode.config.websearch": { group: "config", context: false },
  "opencode.config.shell": { group: "config", context: false },
  "opencode.config.snapshot": { group: "config", context: false },
  "opencode.config.worktree": { group: "config", context: false },
  "opencode.config.location-watcher": { group: "config", context: false },

  // MCP servers themselves and the Code Mode catalog they feed
  "opencode.config.mcp": { group: "mcp", context: true },
  "opencode.mcp.codemode.defaults": { group: "mcp", context: true },

  // slash commands, integrations, keep-alive generation, browser launcher
  "opencode.command": { group: "other", context: false },
  "opencode.wellknown": { group: "other", context: false },
  "opencode.warming": { group: "other", context: false },
  "opencode.browser": { group: "other", context: false },
  // не контекст сам по себе, но поставляет данные для core-инструкции
  // `core/environment` → строка "Is directory a git repo: yes|no" в системке
  "opencode.vcs.git": { group: "other", context: true, note: "env" },
  "opencode.vcs.hg": { group: "other", context: false },
}

/**
 * Whole families whose code path never touches the prompt: provider/model
 * metadata (`provider.*`, `models.*`), websearch backends for the existing
 * `websearch` tool, and VCS info for the UI.
 */
const builtinFamilies: { prefix: string; group: string }[] = [
  { prefix: "opencode.provider.", group: "provider" },
  { prefix: "opencode.models.", group: "provider" },
  { prefix: "opencode.websearch.", group: "websearch" },
  { prefix: "opencode.vcs.", group: "other" },
]

// Prefixes used only for builtins not covered by the table or the families above
// (e.g. after an opencode upgrade); such rows are flagged `unclassified`.
function fallbackGroup(id: string) {
  if (id.startsWith("opencode.tool")) return "tools"
  if (id.startsWith("opencode.prompt.")) return "prompt"
  if (id.startsWith("opencode.config.")) return "config"
  return "other"
}

// Server-plugin surface that ends up in the model context: tool schemas, prompt
// text, config-derived agents/skills/instructions, mcp and reference contributions.
// Everything else a server plugin can hook (events, permissions, storage, rpc,
// shell, vcs) never reaches the prompt.
//
// Each entry is a real API call, never a look-alike object literal: `agents: {}`
// in persisted state (zen-failover) is data, while `ctx.agent.transform(...)` is
// a registration. A registration only counts when something the model sees is
// actually rewritten (`needs`): re-binding `draft.model` or answering a retry
// (zen-failover) adds no prompt text and no tool.
const contextHooks: { channel: string; match: RegExp; needs?: RegExp }[] = [
  { channel: "tool", match: /\btool\.(transform|hook)\s*\(/ },
  {
    channel: "prompt",
    match: /session\.hook\(\s*["'](prompt|context|compaction|generate|title)["']/,
    // a registered hook adds nothing until it edits the request it receives
    needs: /\b[\w$]+\.(?:system|messages|tools|result)\b|\bprompt\.(?:text|files)\b/,
  },
  {
    channel: "agent",
    match: /\bagent\.transform\s*\(/,
    // `editor.update(id, d => { d.model = x })` only rebinds a model
    needs: /editor\.(add|remove|default)\(|\.(name|description|prompt|mode|tools|permissions?)\s*[=:]/,
  },
  { channel: "skill", match: /\bskill\.transform\s*\(/, needs: /\b[\w$]+\.(?:add|update|remove)\s*\(/ },
  { channel: "reference", match: /\breference\.transform\s*\(/, needs: /\b[\w$]+\.(?:add|update|remove)\s*\(/ },
  { channel: "mcp", match: /\bmcp\.transform\s*\(/, needs: /\b[\w$]+\.(?:add|update|remove|set)\s*\(/ },
  { channel: "config", match: /\bconfig\.transform\s*\(/, needs: /\b[\w$]+\.(?:add|update|remove|set)\s*\(/ },
]

function groupOf(id: string) {
  return groups.find((group) => group.id === id) ?? groups[groups.length - 1]
}

export function groupLabel(id: string) {
  return groupOf(id).label
}

export function groupRank(id: string) {
  const index = groups.findIndex((group) => group.id === id)
  return index === -1 ? groups.length : index
}

function readSource(path: string) {
  try {
    if (!statSync(path).isDirectory()) return readFileSync(path, "utf8")
    const parts: string[] = []
    for (const name of ["index.ts", "index.js", "server.ts", "server.js"]) {
      try {
        parts.push(readFileSync(join(path, name), "utf8"))
      } catch {
        // entrypoint variant not present
      }
    }
    return parts.join("\n")
  } catch {
    return ""
  }
}

/** Context channels a local server plugin hooks, e.g. ["tool"] or ["prompt"]. */
export function contextChannels(path: string) {
  const source = readSource(path)
  if (!source) return []
  return contextHooks
    .filter((hook) => hook.match.test(source))
    .filter((hook) => !hook.needs || hook.needs.test(source))
    .map((hook) => hook.channel)
}

/**
 * Entry file of an installed package plugin. The server reports no path for
 * packages, but it materializes them under `~/.cache/opencode/npm/`:
 * `<name>@<range>/<timestamp>/node_modules/<name>/`, or for git targets
 * `git-<name>-<sha256(target)[0..12]>/`.
 */
function packageEntry(target: string): string | undefined {
  const cache = join(homedir(), ".cache", "opencode", "npm")
  let directories: string[]
  try {
    directories = readdirSync(cache)
  } catch {
    return undefined
  }
  const git = target.includes("@git+")
  const name = git ? target.slice(0, target.indexOf("@git+")) : target
  const wanted = git
    ? `git-${basename(name)}-${createHash("sha256").update(target).digest("hex").slice(0, 12)}`
    : undefined
  const matches = directories
    .filter((entry) => (git ? entry === wanted : entry.startsWith(`${target}@`) && !entry.startsWith("git-")))
    .sort()
    .reverse()

  for (const directory of matches) {
    let versions: string[]
    try {
      versions = readdirSync(join(cache, directory)).filter((entry) => /^\d+$/.test(entry)).sort().reverse()
    } catch {
      continue
    }
    for (const version of versions) {
      const root = join(cache, directory, version, "node_modules", name)
      const entry = packageMain(root)
      if (entry) return entry
    }
  }
  return undefined
}

function packageMain(root: string) {
  let manifest: { main?: unknown; exports?: unknown }
  try {
    manifest = JSON.parse(readFileSync(join(root, "package.json"), "utf8"))
  } catch {
    manifest = {}
  }
  const exported = manifest.exports as Record<string, unknown> | string | undefined
  const dot =
    typeof exported === "string"
      ? exported
      : exported && typeof exported === "object"
        ? ((exported["."] as Record<string, unknown> | string | undefined) ?? undefined)
        : undefined
  const candidates = [
    typeof manifest.main === "string" ? manifest.main : undefined,
    typeof dot === "string" ? dot : undefined,
    typeof dot === "object" && dot ? (dot.default as string | undefined) : undefined,
    "index.js",
  ]
  for (const relative of candidates) {
    if (!relative) continue
    const path = join(root, relative)
    try {
      if (statSync(path).isFile()) return path
    } catch {
      // candidate not present
    }
  }
  return undefined
}

function statusOf(value: string | undefined): PluginStatus {
  if (value === "failed") return "failed"
  if (value === "inactive" || value === "disabled") return "inactive"
  if (value === "unsupported") return "unsupported"
  return "active"
}

function stem(file: string) {
  const extension = extname(file)
  return extension ? file.slice(0, -extension.length) : file
}

/** Directories scanned for CLI-only (TUI) plugins, in the same spirit as the runtime's discovery. */
export function pluginDirectories(locationDirectory?: string) {
  const configHome = process.env.XDG_CONFIG_HOME || join(homedir(), ".config")
  const directories = [join(configHome, "opencode", "plugins")]
  if (locationDirectory) directories.push(join(locationDirectory, ".opencode", "plugins"))
  return directories
}

function readPluginDirs(directory: string) {
  try {
    return readdirSync(directory, { withFileTypes: true })
      .filter((entry) => {
        if (entry.isDirectory()) return true
        if (!entry.isSymbolicLink()) return false
        try {
          return statSync(join(directory, entry.name)).isDirectory()
        } catch {
          return false
        }
      })
      .map((entry) => entry.name)
      .sort((left, right) => left.localeCompare(right))
  } catch {
    return []
  }
}

/**
 * Server plugins first (builtin + local + package, as reported by `/api/plugin`),
 * then CLI-only plugin directories that the server does not know about.
 */
export function build(
  plugins: RawPlugin[],
  directories: string[],
  options?: { providerID?: string },
): PluginItem[] {
  const items: PluginItem[] = []
  const known = new Set<string>()
  const seen = new Set<string>()
  const provider = options?.providerID?.toLowerCase()

  for (const plugin of plugins) {
    const source = plugin.source ?? {}
    const builtin = source.type === "builtin"
    const id = plugin.id ?? (source.type === "package" ? source.target : source.path) ?? source.type ?? "unknown"
    const key = `${builtin ? "builtin" : "plugin"}:${id}`
    if (seen.has(key)) continue
    seen.add(key)

    if (!builtin) {
      if (source.path) {
        known.add(basename(source.path))
        known.add(stem(basename(source.path)))
        // `…/zen-failover/index.js` is the `zen-failover` plugin directory, which
        // the CLI directory scan would otherwise report a second time.
        if (/^(?:index|server)\.[cm]?[jt]s$/.test(basename(source.path))) {
          known.add(basename(dirname(source.path)))
        }
      }
      if (source.target) {
        known.add(basename(source.target))
        known.add(stem(basename(source.target)))
      }
    }

    let group = ""
    let context = false
    let detail: string | undefined

    if (builtin) {
      const table = builtinTable[id]
      const family = builtinFamilies.find((entry) => id.startsWith(entry.prefix))
      if (table) {
        group = table.group
        context = table.context
        if (table.providers) {
          const matches = !provider || table.providers.some((alias) => provider.includes(alias))
          context = context && matches
          detail = matches ? undefined : `${table.providers[0]}-only`
        } else if (!table.context) {
          detail = table.note ?? "no context"
        } else {
          detail = table.note
        }
      } else if (family) {
        group = family.group
        context = false
        detail = "no context"
      } else {
        group = fallbackGroup(id)
        context = groupOf(group).context
        detail = "unclassified"
      }
    } else {
      group = "local"
      if (source.type === "package") {
        // Package sources live in the opencode cache; scan the installed entry
        // file when it can be located, otherwise assume it hooks context.
        const entry = source.target ? packageEntry(source.target) : undefined
        const channels = entry ? contextChannels(entry) : []
        context = entry ? channels.length > 0 : true
        detail = channels.length > 0 ? channels.join("+") : entry ? "no context" : "unverified"
        if (source.version) detail = `${detail} ${source.version.slice(0, 7)}`
      } else {
        const channels = source.path ? contextChannels(source.path) : []
        context = channels.length > 0
        detail = channels.length > 0 ? channels.join("+") : "no context"
      }
    }

    items.push({
      key,
      name: id,
      status: statusOf(plugin.state?.status),
      detail,
      error: plugin.state?.error,
      runtime: "server",
      builtin,
      group,
      context,
    })
  }

  // CLI plugins live only in the TUI process, so the server list cannot report
  // them. Fall back to the plugin directories; anything the server already knows
  // is skipped by name.
  for (const directory of directories) {
    for (const name of readPluginDirs(directory)) {
      if (known.has(name)) continue
      known.add(name)
      items.push({
        key: `cli:${name}`,
        name,
        status: "active",
        runtime: "cli",
        builtin: false,
        group: "cli",
        context: false,
      })
    }
  }

  return items
}
