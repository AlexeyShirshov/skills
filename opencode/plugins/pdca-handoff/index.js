import { spawn, spawnSync } from "node:child_process"
import { createHash, randomUUID } from "node:crypto"
import { realpath } from "node:fs/promises"
import { join } from "node:path"
import { fileURLToPath } from "node:url"
import { isDeepStrictEqual } from "node:util"
import { installMechanics } from "./mechanics.js"

const tool = "pdca_handoff_v1"
const helper = fileURLToPath(new URL("./ledger.py", import.meta.url))
const hash = (value) => createHash("sha256").update(value).digest("hex")
const check = (v, why) => {
  if (!v) throw Error(why)
}
const statusPattern = /^\.pdca\/status\/[A-Za-z0-9][A-Za-z0-9_-]{0,99}\.md$/
const evidencePattern = /^\.pdca\/[A-Za-z0-9][A-Za-z0-9_-]{0,99}\/rv[1-9]\d*$/
const sessionPattern = /^ses_[a-zA-Z0-9]+$/
// Status is read into agents' contexts. Keep the potentially large delivery
// brief in host storage, and bind its exact content to the on-disk receipt.
function receiptSpec({ owner, planner, evidence, boundary, brief, fences }) {
  return { owner, planner, evidence, boundary, authorization: hash(JSON.stringify([brief, fences])) }
}

function ledger(root, input) {
  return new Promise((resolve, reject) => {
    const p = spawn("python3", ["-I", "-B", helper], { cwd: root, stdio: ["pipe", "pipe", "pipe"] })
    let out = "",
      err = ""
    p.stdout.setEncoding("utf8").on("data", (d) => {
      out += d
    })
    p.stderr.setEncoding("utf8").on("data", (d) => {
      err += d
    })
    p.once("error", reject)
    p.stdin.on("error", reject)
    p.once("close", (code) => {
      if (code !== 0) return reject(Error(err.trim() || `ledger exit ${code}`))
      try {
        resolve(JSON.parse(out))
      } catch (e) {
        reject(e)
      }
    })
    p.stdin.end(JSON.stringify(input))
  })
}

const schema = {
  type: "object",
  additionalProperties: false,
  properties: {
    action: { type: "string", enum: ["arm", "inspect", "release", "recover"] },
    status: { type: "string", description: "Assigned .pdca/status/<slug>.md" },
    boundary: { type: "string", enum: ["next-step", "plan"] },
    planner: { type: "string", description: "Existing sibling planner session ID" },
    evidence: { type: "string", description: "Existing .pdca/<task>/rv<number> directory" },
    brief: {
      type: "string",
      description: "Already-authorized DO dispatch constraints, exact original task and overlay references",
    },
    ticket: { type: "string", description: "Previous ticket to replace, or exact ticket to release/recover" },
  },
  required: ["action", "status"],
}

function report(messages, ticket) {
  const marker = `PDCA-HANDOFF ${ticket}`
  const tail = messages.at(-1)
  const m = messages.at(-2)
  const user = messages.findLast((x) => x.type === "user")
  if (!user?.text?.split("\n").includes(marker)) return
  if (tail?.type !== "idle") return
  if (tail.outcome !== "succeeded")
    return { op: "interrupted", reason: `Planner ended: ${tail.outcome}`, message: tail.id }
  if (m?.type !== "assistant" || m.agent !== "pdca-planner" || m.finish !== "stop" || m.error)
    return { op: "interrupted", reason: "No completed planner decision", message: tail.id }
  const texts = m.content.filter((p) => p.type === "text")
  if (texts.length !== 1 || !texts[0].text.trim())
    return { op: "interrupted", reason: "Missing or ambiguous planner report", message: m.id }
  const text = texts[0].text
  // Only a terminal, explicit planner decision can open DO. Ordinary prose,
  // tool output and text quoting a marker earlier in the report cannot.
  return { report: text, message: m.id, op: text.trimEnd().endsWith(`\n${marker} ready`) ? "ready" : "hold" }
}

export async function install(ctx) {
  const root = await realpath(ctx.location.directory)
  const prefix = `handoff/v1/${hash(root)}/`
  const key = (status) => prefix + status.slice(13)
  const active = new Map()
  let chain = Promise.resolve()
  const serial = (f) => {
    const next = chain.then(f)
    chain = next.catch(() => {})
    return next
  }
  const sessions = ctx.session
  async function latest(id, limit, type) {
    // Avoid loading multi-day controller transcripts merely to compare a user
    // message ID. Older V2 adapters expose only the context read.
    if (sessions.message?.list) {
      const page = await sessions.message.list({ sessionID: id, order: "desc", limit, ...(type && { type }) })
      return page.data.toReversed()
    }
    const messages = await sessions.context({ sessionID: id })
    return (type ? messages.filter((m) => m.type === type) : messages).slice(-limit)
  }
  const info = async (id) => {
    const s = await sessions.get({ sessionID: id })
    check(
      s?.id === id && s.location.directory === root && !s.time.archived,
      "session moved, archived or unavailable",
    )
    return s
  }
  async function identities(owner, planner) {
    const dst = await info(owner),
      src = await info(planner)
    check(
      dst.agent === "pdca-executor" &&
        src.agent === "pdca-planner" &&
        dst.parentID &&
        src.parentID === dst.parentID,
      "expected existing sibling planner and executor",
    )
    const driver = await info(dst.parentID)
    await ctx.permission.assert({
      sessionID: driver.id,
      agent: driver.agent,
      action: "subagent",
      resources: ["pdca-planner", "pdca-executor"],
      save: [],
    })
  }
  // A later user instruction invalidates a previously authorized continuation.
  async function fences(parent) {
    const result = []
    const seen = new Set()
    while (parent) {
      check(!seen.has(parent), "invalid parent chain")
      seen.add(parent)
      const s = await info(parent)
      const [user] = await latest(parent, 1, "user")
      result.push([parent, user?.id ?? null])
      parent = s.parentID
    }
    return result
  }
  async function permissions(owner, status, artifact, source) {
    await ctx.permission.assert({
      sessionID: owner,
      agent: "pdca-executor",
      action: "edit",
      resources: [join(root, status), ...(artifact ? [join(root, artifact)] : [])],
      save: [],
      ...(source && { source }),
    })
  }
  async function saveIndex(status, record) {
    await ctx.storage.set(key(status), record)
    active.set(status, record)
  }
  function verify(state, record) {
    check(
      state && state.ticket === record.ticket && isDeepStrictEqual(state.spec, receiptSpec(record.spec)),
      "checkpoint does not match registered handoff",
    )
  }
  async function advance(record) {
    const { status, ticket, spec } = record
    const tx = (op, more = {}) => ledger(root, { op, status, ticket, ...more })
    let s = await tx("inspect")
    verify(s, record)
    if (!["armed", "pending"].includes(s.stage)) return s
    await identities(spec.owner, spec.planner)
    await permissions(spec.owner, status)
    if (
      s.stage === "pending" &&
      (await sessions.context({ sessionID: spec.owner })).some(
        (m) => m.type === "user" && m.id === s.deliveryID,
      )
    )
      return tx("delivered")
    check(
      isDeepStrictEqual(await fences(spec.owner), spec.fences),
      "new instruction since authorization; reconcile before continuing",
    )
    if (s.stage === "armed") {
      const [user] = await latest(spec.planner, 1, "user")
      const result = report([...(user ? [user] : []), ...(await latest(spec.planner, 2))], ticket)
      if (!result) return s
      if (result.op === "interrupted") return tx(result.op, result)
      await permissions(spec.owner, status, `${spec.evidence}/report-${hash(result.report)}.md`)
      s = await tx(result.op, {
        ...result,
        deliveryID: `msg_${hash(`${root}:${status}:${ticket}:${result.message}`)}`,
      })
    }
    if (s.stage === "pending") {
      // Write-ahead outbox in the status. OpenCode deduplicates a caller-supplied
      // message ID, including after the server admitted it but lost our reply.
      s = await tx("outbox")
      check(
        isDeepStrictEqual(await fences(spec.owner), spec.fences),
        "new instruction before admission; reconcile the pending handoff",
      )
      const id = s.deliveryID
      const prompt =
        `${spec.brief}\n\nPerform substantive DO now under the frozen plan ${JSON.stringify(s.ref)}.\n` +
        `Status: ${status}; ${JSON.stringify(s.counters)}. PLAN recording and numbering are complete.`
      await sessions.prompt({ sessionID: spec.owner, id, text: prompt, delivery: "queue" })
      s = await tx("delivered")
    }
    return s
  }

  async function invoke(i, context) {
    check(
      context.agent === "pdca-executor" && statusPattern.test(i.status),
      "executor and assigned status required",
    )
    const dst = await info(context.sessionID)
    check(dst.agent === context.agent, "session agent changed")
    const old = active.get(i.status)
    check(!old || old.spec.owner === dst.id, "status belongs to another session")
    if (i.action === "arm") {
      check(
        evidencePattern.test(i.evidence) &&
          sessionPattern.test(i.planner) &&
          ["plan", "next-step"].includes(i.boundary) &&
          typeof i.brief === "string" &&
          i.brief.trim() &&
          i.brief.length <= 32000,
        "incomplete handoff",
      )
      await identities(dst.id, i.planner)
      const spec = {
        owner: dst.id,
        planner: i.planner,
        evidence: i.evidence,
        boundary: i.boundary,
        brief: i.brief,
        fences: await fences(dst.id),
      }
      await permissions(dst.id, i.status, null, {
        type: "tool",
        messageID: context.messageID,
        id: context.id,
      })
      if (old && isDeepStrictEqual(old.spec, spec) && !i.ticket) {
        const prior = await ledger(root, { status: i.status, op: "inspect" })
        verify(prior, old)
        return prior
      }
      const candidate = { spec, status: i.status, ticket: randomUUID() }
      const s = await ledger(root, {
        op: "arm",
        status: i.status,
        spec: receiptSpec(spec),
        ticket: candidate.ticket,
        previous: i.ticket,
      })
      // If interrupted between ledger and index, replaying the same arm recovers
      // the original ticket; the driver has not dispatched it before tool return.
      await saveIndex(i.status, { ...candidate, ticket: s.ticket })
      return s
    }
    check(old, "no registered handoff")
    const s = await ledger(root, { op: "inspect", status: i.status })
    verify(s, old)
    if (i.action === "inspect") return s
    check(i.ticket === old.ticket, "exact ticket required")
    await permissions(dst.id, i.status)
    if (i.action === "release") return ledger(root, { op: "release", status: i.status, ticket: i.ticket })
    check(i.action === "recover", "unknown operation")
    return advance(old)
  }

  let after
  do {
    const page = await ctx.storage.scan({ prefix, after, limit: 100 })
    for (const { value: r } of page.entries) if (r && statusPattern.test(r.status)) active.set(r.status, r)
    after = page.next
  } while (after)
  const controller = new AbortController()
  const reconcile = (r) =>
    serial(() => advance(r)).catch((e) => {
      // Do not acknowledge an unknown/failed prompt admission or retry in a loop.
      console.warn(`[pdca-handoff] ${r.status}: ${e.message}`)
    })
  const terminal = [
    "session.execution.succeeded",
    "session.execution.failed",
    "session.execution.interrupted",
  ]
  const mechanics = await installMechanics(ctx, { root, ledger, serial, info, fences })
  const events = ctx.event.subscribe({
    types: [...terminal, "session.synthetic", "session.inbox.delivered", "shell.exited"],
    signal: controller.signal,
  })
  const observer = (async () => {
    for await (const event of events) {
      if (controller.signal.aborted) break
      await mechanics.event(event)
      if (!terminal.includes(event.type)) continue
      for (const r of active.values()) if (event.data?.sessionID === r.spec.planner) await reconcile(r)
    }
  })().catch((e) => {
    if (!controller.signal.aborted) console.warn(`[pdca-handoff] events: ${e.message}`)
  })
  // No polling. Recovery deals with a completion during reload and an admitted
  // outbox message whose receipt was lost.
  for (const r of active.values()) void reconcile(r)
  mechanics.restore()
  await ctx.tool.transform((editor) =>
    editor.add({
      name: tool,
      description:
        "Executor-owned PDCA v1: arm, inspect, release or recover an authorized autonomous PLAN → DO handoff.",
      input: schema,
      options: { permission: tool, codemode: false },
      async execute(input, context) {
        const state = await serial(() => invoke(input, context))
        return {
          content: JSON.stringify({
            stage: state.stage,
            ticket: state.ticket,
            counters: state.counters,
            ref: state.ref,
            reason: state.reason,
            deliveryID: state.deliveryID,
          }),
        }
      },
    }),
  )
  return async () => {
    controller.abort()
    await observer
    await chain
  }
}

export default {
  id: "pdca-handoff",
  async setup(ctx) {
    if (
      !ctx.location?.directory ||
      !ctx.storage?.scan ||
      !ctx.event?.subscribe ||
      !ctx.session?.prompt ||
      !ctx.permission?.assert ||
      !ctx.tool?.transform ||
      spawnSync("python3", ["-I", "-c", "import fcntl"], { timeout: 3000 }).status !== 0
    )
      return
    return install(ctx)
  },
}
