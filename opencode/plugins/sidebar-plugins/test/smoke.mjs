// Smoke test for the data layer: what counts as "affects the model context".
//
// Everything asserted here is the rule the sidebar renders, so a regression in
// the classifier shows up as a failing row, not as a wrong panel.
//
//   npm test         (node --experimental-strip-types test/smoke.mjs)
//   bun test/smoke.mjs

import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises"
import { join } from "node:path"
import { tmpdir } from "node:os"
import { build, contextChannels, pluginDirectories } from "../data.ts"

let failures = 0

function check(name, condition, extra = "") {
  if (condition) {
    console.log(`  ok   ${name}`)
  } else {
    failures += 1
    console.log(`  FAIL ${name}${extra ? ` — ${extra}` : ""}`)
  }
}

const dir = await mkdtemp(join(tmpdir(), "sidebar-plugins-test-"))
const file = async (name, text) => {
  const path = join(dir, name)
  await writeFile(path, text)
  return path
}
const channelsOf = async (text) => contextChannels(await file(`src-${Math.random().toString(36).slice(2)}.js`, text))
const one = (raw, options) => build([raw], [], options)[0]
const builtin = (id, options) => one({ id, source: { type: "builtin" } }, options)

console.log("builtin table")

check("a tool plugin adds a tool schema", builtin("opencode.tool.read").context === true)
check("tool.input.repair is not a tool", builtin("opencode.tool.input.repair").context === false)
check("vcs.git adds the <env> repo line", builtin("opencode.vcs.git").context === true)
check(
  "a provider prompt counts for its own provider",
  builtin("opencode.prompt.anthropic", { providerID: "claude-code" }).context === true,
)
check(
  "the same provider prompt is inert for another provider",
  builtin("opencode.prompt.anthropic", { providerID: "openai" }).context === false,
)
check("provider metadata never reaches the prompt", builtin("opencode.provider.openai").context === false)
check(
  "an unknown prompt plugin is unclassified but contextual",
  builtin("opencode.prompt.brand-new").context === true &&
    builtin("opencode.prompt.brand-new").detail === "unclassified",
)

console.log("source scan")

const cases = [
  ["tool.transform", "ctx.tool.transform((draft) => { draft.description = 'x' })", ["tool"]],
  [
    "tool.hook",
    "ctx.tool.hook('read', () => ({}) )",
    ["tool"],
  ],
  ["a prompt hook that edits the request", "ctx.session.hook('prompt', (e) => { e.system.push('x'); return e })", ["prompt"]],
  ["a context hook that rewrites messages", "session.hook(\"context\", (e) => { e.messages = e.messages })", ["prompt"]],
  ["a prompt hook that edits nothing", "ctx.session.hook('prompt', () => undefined)", []],
  ["a model-only agent transform", "ctx.agent.transform((draft) => { draft.model = 'x' })", []],
  [
    "an agent transform that shapes an agent",
    "ctx.agent.transform((editor) => { editor.update('x', (d) => { d.description = 'y' }) })",
    ["agent"],
  ],
  ["a skill that is added", "ctx.skill.transform((list) => { list.add({ name: 'x' }) })", ["skill"]],
  ["an mcp server that is added", "ctx.mcp.transform((servers) => { servers.add('x', {}) })", ["mcp"]],
  ["a config entry that is set", "ctx.config.transform((config) => { config.set('x', 1) })", ["config"]],
  ["command and model transforms", "ctx.command.transform((d) => d); ctx.model.transform((d) => d)", []],
  ["state that only looks like a registration", "const state = { agents: {}, prompt: 'hello' }", []],
  ["an empty source", "", []],
]

for (const [label, source, expected] of cases) {
  const actual = await channelsOf(source)
  check(label, JSON.stringify(actual) === JSON.stringify(expected), `got ${JSON.stringify(actual)}`)
}

const withDir = join(dir, "dir-plugin")
await mkdir(withDir, { recursive: true })
await writeFile(join(withDir, "index.js"), "ctx.tool.transform((draft) => draft)")
check("a plugin directory is read through its index", JSON.stringify(contextChannels(withDir)) === '["tool"]')

console.log("build")

const local = await file("local.js", "ctx.session.hook('prompt', (e) => { e.system = '' })")
const localItem = one({ id: "local", source: { type: "local", path: local } })
check("a local plugin with a prompt hook is context", localItem.context === true && localItem.detail === "prompt")

const quiet = await file("quiet.js", "ctx.event.on('session.idle', () => {})")
const quietItem = one({ id: "quiet", source: { type: "local", path: quiet } })
check("a local plugin without context is excluded", quietItem.context === false && quietItem.detail === "no context")

const missing = one({
  id: "opencode-not-installed-xyz",
  source: { type: "package", target: "definitely-not-installed-xyz", version: "9.9.9" },
})
check(
  "an unresolvable package is unverified and counted as context",
  missing.context === true && String(missing.detail).startsWith("unverified"),
  `got ${missing.detail}`,
)

const pluginsDir = join(dir, "plugins")
await mkdir(join(pluginsDir, "dedupe-me"), { recursive: true })
await writeFile(join(pluginsDir, "dedupe-me", "index.js"), "ctx.tool.transform((d) => d)")

const deduped = build(
  [{ id: "dedupe-me", source: { type: "local", path: join(pluginsDir, "dedupe-me", "index.js") } }],
  [pluginsDir],
)
check(
  "a server path and its CLI directory are one row",
  deduped.length === 1 && deduped[0].runtime === "server",
  `got ${deduped.map((item) => `${item.name}:${item.runtime}`).join(", ")}`,
)

await mkdir(join(pluginsDir, "cli-only"), { recursive: true })

const discovered = build([], [pluginsDir])
const cli = discovered.find((item) => item.name === "cli-only")
check(
  "a CLI-only plugin is discovered from disk and is not context",
  Boolean(cli) && cli.runtime === "cli" && cli.context === false,
)

const previous = process.env.XDG_CONFIG_HOME
process.env.XDG_CONFIG_HOME = join(dir, "xdg")
const dirs = pluginDirectories(join(dir, "project"))
if (previous === undefined) delete process.env.XDG_CONFIG_HOME
else process.env.XDG_CONFIG_HOME = previous
check(
  "plugin directories follow XDG_CONFIG_HOME and the location",
  dirs[0] === join(dir, "xdg", "opencode", "plugins") && dirs[1] === join(dir, "project", ".opencode", "plugins"),
  `got ${dirs.join(", ")}`,
)

await rm(dir, { recursive: true, force: true })

if (failures > 0) {
  console.log(`\n${failures} failed`)
  process.exit(1)
}
console.log("\nsmoke ok")
