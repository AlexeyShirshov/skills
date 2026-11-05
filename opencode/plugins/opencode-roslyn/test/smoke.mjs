// Smoke test: drives the real `setup()` with a synthetic V2 plugin context and a
// fake `roslynq` on disk, so every assertion is made against the tool definition
// the plugin registers and the argv it would execute — no .NET, no solution, no
// opencode server involved.
//
//   node test/smoke.mjs

import { mkdtemp, writeFile, chmod, readFile, rm } from "node:fs/promises"
import { join } from "node:path"
import { tmpdir } from "node:os"

import Plugin, { ACTIONS, INPUT, TOOL, buildArgs, findSolution, resolveBinary } from "../index.js"

let failures = 0

function check(name, condition, extra = "") {
  if (condition) {
    console.log(`  ok   ${name}`)
  } else {
    failures += 1
    console.log(`  FAIL ${name}${extra ? ` — ${extra}` : ""}`)
  }
}

async function withTemp(name, body) {
  const dir = await mkdtemp(join(tmpdir(), `opencode-roslyn-${name}-`))
  try {
    return await body(dir)
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
}

/** A stand-in `roslynq` that records its argv and runs `body`. */
async function fakeRoslynq(dir, { name = "roslynq", body = "printf 'fake output\\n'\n" } = {}) {
  const bin = join(dir, name)
  const log = join(dir, `${name}.argv`)
  await writeFile(bin, `#!/bin/sh\nprintf '%s\\n' "$@" > '${log}'\n${body}`)
  await chmod(bin, 0o755)
  const argv = async () => {
    try {
      return (await readFile(log, "utf8")).trim().split("\n").filter(Boolean)
    } catch {
      return []
    }
  }
  return { bin, argv }
}

/** Register the plugin against a fake context and return the tool it added. */
async function register(directory, options = {}) {
  const tools = []
  const permissions = []
  const progress = []
  const ctx = {
    location: { directory, project: { id: "test", directory, canonical: directory } },
    options,
    tool: {
      transform: async (callback) => {
        callback({ add: (tool) => tools.push(tool) })
        return { dispose: async () => {} }
      },
    },
    permission: { assert: async (input) => permissions.push(input) },
  }
  await Plugin.setup(ctx)
  return {
    tool: tools[0],
    tools,
    permissions,
    progress,
    execute: (input, signal) =>
      tools[0].execute(input, {
        sessionID: "ses_test",
        agent: "build",
        messageID: "msg_test",
        id: "call_test",
        signal: signal ?? new AbortController().signal,
        progress: async (update) => progress.push(update),
      }),
  }
}

async function main() {
  check("plugin exports the V2 id/setup shape", Plugin.id === "opencode-roslyn" && typeof Plugin.setup === "function")

  await withTemp("registration", async (dir) => {
    const { bin } = await fakeRoslynq(dir)
    const { tool } = await register(dir, { bin })
    check("registers exactly one tool, named roslyn", tool?.name === TOOL)
    check("input requires `action`", tool?.input?.required?.join(",") === "action")
    check("input advertises all eight actions", tool?.input?.properties?.action?.enum?.join(",") === ACTIONS.join(","))
    check("input is closed to extra properties", tool?.input?.additionalProperties === false)
    check("carries the roslyn permission action", tool?.options?.permission === TOOL)
    check(
      "tells the model to prefer it over rg/sed",
      String(tool?.description).includes("INSTEAD of rg/sed") && String(tool?.description).includes("apply=true"),
    )
  })

  await withTemp("slnx", async (dir) => {
    const { bin, argv } = await fakeRoslynq(dir)
    await writeFile(join(dir, "b.sln"), "")
    await writeFile(join(dir, "a.slnx"), "")
    const { execute, permissions, progress } = await register(dir, { bin })

    const result = await execute({ action: "refs", target: "Ns.Type.Member" })
    const args = await argv()
    check("discovers the solution, preferring .slnx", args[0]?.endsWith("a.slnx"), args.join(" "))
    check("passes `<solution> refs <target>`", args[1] === "refs" && args[2] === "Ns.Type.Member")
    check("returns the roslynq output", result.content.includes("fake output"), result.content)
    check(
      "asserts the roslyn permission on the solution with tool provenance",
      permissions[0]?.action === "roslyn" &&
        permissions[0]?.resources?.[0]?.endsWith("a.slnx") &&
        permissions[0]?.source?.type === "tool" &&
        permissions[0]?.source?.id === "call_test",
      JSON.stringify(permissions[0] ?? null),
    )
    check("reports progress for the cold load", progress.length === 1 && /refs/.test(progress[0]?.status ?? ""))
  })

  await withTemp("sln", async (dir) => {
    const { bin, argv } = await fakeRoslynq(dir)
    await writeFile(join(dir, "only.sln"), "")
    const { execute } = await register(dir, { bin })
    await execute({ action: "structure" })
    check("falls back to a .sln", (await argv())[0]?.endsWith("only.sln"))
  })

  await withTemp("explicit", async (dir) => {
    const { bin, argv } = await fakeRoslynq(dir)
    await writeFile(join(dir, "near.slnx"), "")
    const { execute } = await register(dir, { bin })
    await execute({ action: "types", target: "SqlBuilder", solution: "nested/far.slnx" })
    check("resolves an explicit relative solution against the project directory", (await argv())[0] === join(dir, "nested", "far.slnx"))
  })

  await withTemp("rename", async (dir) => {
    const { bin, argv } = await fakeRoslynq(dir)
    await writeFile(join(dir, "app.slnx"), "")
    const { execute } = await register(dir, { bin })

    await execute({ action: "rename", target: "Ns.Type.Kw", newName: "Keyword" })
    check(
      "dry-run passes the new name without --apply",
      (await argv()).slice(1).join(" ") === "rename Ns.Type.Kw Keyword",
      (await argv()).join(" "),
    )

    await execute({ action: "rename", target: "Ns.Type.Kw", newName: "Keyword", apply: true })
    check("apply appends --apply", (await argv()).at(-1) === "--apply", (await argv()).join(" "))

    const before = (await argv()).length
    const refused = await execute({ action: "rename", target: "Ns.Type.Kw" })
    check("rename without newName is refused", /requires `newName`/.test(refused.content), refused.content)
    check("rename without newName never spawns", (await argv()).length === before)
  })

  await withTemp("exit", async (dir) => {
    const { bin } = await fakeRoslynq(dir, { body: "printf 'boom\\n' >&2\nexit 3\n" })
    await writeFile(join(dir, "app.slnx"), "")
    const { execute } = await register(dir, { bin })
    const result = await execute({ action: "refs", target: "Ns.Type" })
    check("non-zero exit surfaces stderr and the code", result.content.includes("boom") && result.content.includes("code 3"), result.content)
  })

  await withTemp("missing", async (dir) => {
    await writeFile(join(dir, "app.slnx"), "")
    const { execute } = await register(dir, { bin: join(dir, "not-installed") })
    const result = await execute({ action: "structure" })
    check("a missing binary returns an install hint", result.content.includes("Cannot run"), result.content)
  })

  await withTemp("abort", async (dir) => {
    const { bin } = await fakeRoslynq(dir, { body: "sleep 5\n" })
    await writeFile(join(dir, "app.slnx"), "")
    const { execute } = await register(dir, { bin })
    const controller = new AbortController()
    setTimeout(() => controller.abort(), 50)
    const result = await execute({ action: "structure" }, controller.signal)
    check("an aborted call reports cancellation", result.content === "roslynq cancelled.", result.content)
  })

  await withTemp("nosolution", async (dir) => {
    const { bin, argv } = await fakeRoslynq(dir)
    const { execute } = await register(dir, { bin })
    const result = await execute({ action: "structure" })
    check("no solution returns guidance", result.content.includes("No .sln/.slnx found"), result.content)
    check("no solution never spawns", (await argv()).length === 0)
  })

  await withTemp("precedence", async (dir) => {
    const option = await fakeRoslynq(dir, { name: "option-roslynq" })
    const fromEnv = await fakeRoslynq(dir, { name: "env-roslynq" })
    await writeFile(join(dir, "app.slnx"), "")

    check("resolveBinary: the option beats the environment", resolveBinary({ bin: option.bin }, { OPENCODE_ROSLYN_BIN: fromEnv.bin }) === option.bin)
    check("resolveBinary: the environment is used when the option is absent", resolveBinary({}, { OPENCODE_ROSLYN_BIN: fromEnv.bin }) === fromEnv.bin)
    check(
      "resolveBinary: falls back to the global dotnet tool or PATH",
      /(^|[\\/])roslynq(\.exe)?$/.test(resolveBinary({}, {})),
      resolveBinary({}, {}),
    )

    const previous = process.env.OPENCODE_ROSLYN_BIN
    process.env.OPENCODE_ROSLYN_BIN = fromEnv.bin
    try {
      const { execute } = await register(dir)
      await execute({ action: "structure" })
      check("the environment binary is really executed", (await fromEnv.argv()).length > 0)
      check("the option wins over the environment at run time", (await option.argv()).length === 0)
    } finally {
      if (previous === undefined) delete process.env.OPENCODE_ROSLYN_BIN
      else process.env.OPENCODE_ROSLYN_BIN = previous
    }
  })

  check(
    "buildArgs: rename needs a new name, other actions never do",
    buildArgs({ action: "rename", target: "T" }, "/s.slnx").error !== undefined &&
      buildArgs({ action: "members", target: "T" }, "/s.slnx").args.join(" ") === "/s.slnx members T",
  )
  check("findSolution: unknown directory is not a solution", findSolution("/definitely/not/here") === null)

  console.log(failures === 0 ? "\nall checks passed" : `\n${failures} check(s) failed`)
  process.exit(failures === 0 ? 0 : 1)
}

await main()
