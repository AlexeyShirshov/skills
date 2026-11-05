// opencode-roslyn — C# semantic analysis for OpenCode V2, backed by `roslynq`
// (Roslyn + MSBuildWorkspace shipped as a .NET global tool).
//
// V2 registers tools through a plugin transform (`ctx.tool.transform` →
// `editor.add`), so this file *is* the tool definition: V2 has no `tools/*.ts`
// custom-tool entrypoint, and the plugin transform is the supported way in.
//
// The tool is named `roslyn` on purpose. It answers the questions an agent
// otherwise reaches for `rg`/`grep` to guess at — types, members, references,
// call sites, implementations — and it answers them semantically, the same job
// the V1 `lsp` tool did before V2 dropped the LSP runtime.
//
// Nothing here keeps state: `roslynq` holds the loaded workspace in one
// background daemon per solution, so MSBuild loads it once and compiles each
// project once however many calls arrive. That removes the reload, not the
// analysis: individual queries still cost seconds to tens of seconds on a large
// solution (see the README's measurements), and the daemon's memory grows with
// the projects compiled until it idles out.

import { execFile } from "node:child_process"
import { existsSync, readdirSync } from "node:fs"
import { homedir } from "node:os"
import { isAbsolute, join, resolve } from "node:path"

export const TOOL = "roslyn"
export const BINARY = "roslynq"

/** `refs`/`callers` answers on a big solution blow past the 1 MiB exec default. */
const MAX_BUFFER = 64 * 1024 * 1024

export const ACTIONS = [
  "structure",
  "types",
  "symbols",
  "members",
  "refs",
  "callers",
  "implementations",
  "rename",
]

export const DESCRIPTION = [
  "Roslyn semantic analysis of a C# solution via the `roslynq` tool.",
  "Use this INSTEAD of rg/sed when you need types, symbols, members, references, call sites, implementations or a rename.",
  "actions: structure | types | symbols | members | refs | callers | implementations | rename.",
  "Pass symbols by full name, e.g. NextORM.Core.SqlBuilder.MakeSelect.",
  "`rename` is a dry-run by default; set apply=true to write files.",
  "Batch several calls into ONE code-mode execute (Promise.all) instead of one call per step: each query takes seconds on a real solution.",
  "The first call loads the solution and starts a background daemon; queries on a large solution take seconds.",
].join(" ")

export const INPUT = {
  type: "object",
  properties: {
    action: {
      type: "string",
      enum: ACTIONS,
      description: "Analysis action",
    },
    target: {
      type: "string",
      description: "Type/member full name, or a type-name substring for `types`",
    },
    newName: {
      type: "string",
      description: "New name (required for action=rename)",
    },
    apply: {
      type: "boolean",
      description: "For rename: write changes to disk (default is dry-run)",
    },
    solution: {
      type: "string",
      description: "Path to .sln/.slnx, absolute or relative to the project directory",
    },
  },
  required: ["action"],
  additionalProperties: false,
}

/**
 * Locate the `roslynq` executable: the `bin` plugin option, then
 * `OPENCODE_ROSLYN_BIN`, then the global dotnet tool, then bare `roslynq` on
 * PATH.
 */
export function resolveBinary(options = {}, env = process.env, platform = process.platform) {
  const configured =
    typeof options.bin === "string" && options.bin.trim() !== "" ? options.bin : env.OPENCODE_ROSLYN_BIN
  if (typeof configured === "string" && configured.trim() !== "") return configured
  const tool = join(homedir(), ".dotnet", "tools", platform === "win32" ? `${BINARY}.exe` : BINARY)
  return existsSync(tool) ? tool : BINARY
}

/**
 * The solution to analyse: an explicit path wins (absolute or relative to the
 * project directory), otherwise the project's own `.slnx`/`.sln`, preferring
 * the newer `.slnx`.
 */
export function findSolution(directory, requested) {
  if (typeof requested === "string" && requested.trim() !== "") {
    return isAbsolute(requested) ? requested : resolve(directory, requested)
  }
  let entries
  try {
    entries = readdirSync(directory, { withFileTypes: true })
  } catch {
    return null
  }
  const solutions = entries
    .filter((entry) => entry.isFile() && /\.slnx?$/i.test(entry.name))
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b))
  const preferred = solutions.find((name) => name.toLowerCase().endsWith(".slnx")) ?? solutions[0]
  return preferred ? join(directory, preferred) : null
}

/** Map tool input onto `roslynq` argv, or report the input it cannot honour. */
export function buildArgs(input, solution) {
  const args = [solution, input.action]
  if (input.target) args.push(input.target)
  if (input.action !== "rename") return { args }
  const newName = input.newName
  if (!newName) return { error: "action=rename requires `newName`." }
  args.push(newName)
  if (input.apply) args.push("--apply")
  return { args }
}

/**
 * Run `roslynq` once. `signal` cancels the child together with the tool call;
 * a missing executable is reported separately from a non-zero exit code.
 */
export function runRoslynq(binary, args, cwd, signal) {
  return new Promise((done) => {
    execFile(binary, args, { cwd, signal, maxBuffer: MAX_BUFFER }, (error, stdout, stderr) => {
      const text = [String(stdout ?? "").trim(), String(stderr ?? "").trim()].filter(Boolean).join("\n").trim()
      if (error?.name === "AbortError") return done({ aborted: true, code: 0, text, missing: false })
      if (error?.code === "ENOENT") return done({ aborted: false, code: 1, text, missing: true })
      const code = error ? (typeof error.code === "number" ? error.code : 1) : 0
      done({ aborted: false, code, text, missing: false })
    })
  })
}

export default {
  id: "opencode-roslyn",

  async setup(ctx) {
    // The plugin loads per location, so the project directory is the analysis
    // root: it is where the solution is discovered and where roslynq runs.
    const root =
      typeof ctx.location?.directory === "string" && ctx.location.directory !== ""
        ? ctx.location.directory
        : process.cwd()
    const binary = resolveBinary(ctx.options)
    const permission =
      typeof ctx.options.permission === "string" && ctx.options.permission.trim() !== ""
        ? ctx.options.permission
        : TOOL

    await ctx.tool.transform((editor) => {
      editor.add({
        name: TOOL,
        description: DESCRIPTION,
        input: INPUT,
        options: { permission },
        async execute(raw, context) {
          const input = raw ?? {}
          const solution = findSolution(root, input.solution ?? ctx.options.solution)
          if (!solution) {
            return { content: `No .sln/.slnx found in ${root}. Pass \`solution\` with the path to the solution.` }
          }

          const built = buildArgs(input, solution)
          if (built.error) return { content: built.error }

          // Rules match on the solution, so `{ "action": "roslyn", "resource": "*" }`
          // allows the tool outright and anything narrower is scoped to one solution.
          await ctx.permission.assert({
            sessionID: context.sessionID,
            agent: context.agent,
            action: permission,
            resources: [solution],
            save: ["*"],
            metadata: { action: input.action, target: input.target, apply: input.apply === true, binary, solution },
            source: { type: "tool", messageID: context.messageID, id: context.id },
          })

          await context.progress({ status: `${TOOL}: ${input.action} (the first call loads the solution)` })

          const result = await runRoslynq(binary, built.args, root, context.signal)
          if (result.aborted) return { content: `${BINARY} cancelled.` }
          if (result.missing) {
            return {
              content: `Cannot run \`${binary}\`. Install the tool (\`dotnet tool install --global opencode-roslyn\`) or set the plugin option \`bin\` / the \`OPENCODE_ROSLYN_BIN\` environment variable.`,
            }
          }
          if (result.code !== 0) {
            const detail = result.text ? `${result.text}\n` : ""
            return { content: `${detail}${BINARY} exited with code ${result.code}` }
          }
          return { content: result.text || "(no output)" }
        },
      })
    })
  },
}
