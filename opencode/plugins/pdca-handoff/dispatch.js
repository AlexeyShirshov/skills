import { createHash } from "node:crypto"
import { isDeepStrictEqual } from "node:util"

const tool = "pdca_dispatch_v1"
const digest = (value) => createHash("sha256").update(JSON.stringify(value)).digest("hex")
const sessionID = /^ses_[a-zA-Z0-9]+$/
const keyPattern = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/
const drivers = new Set(["build", "pdca-orchestrator"])
const roles = new Set(["pdca-planner", "pdca-executor", "pdca-escalate", "pdca-scout"])
const ended = new Set(["delivered", "failed", "held"])
const terminal = new Set([
  "session.execution.succeeded",
  "session.execution.failed",
  "session.execution.interrupted",
])
const require = (value, why) => {
  if (!value) throw Error(why)
}
const marker = (ticket) => `PDCA-DISPATCH ${ticket} complete`
const assistantText = (message) =>
  message.content.filter((p) => p.type === "text" && p.text).map((p) => p.text).join("\n\n")

const schema = {
  type: "object",
  additionalProperties: false,
  required: ["action", "key"],
  properties: {
    action: { type: "string", enum: ["send", "inspect", "recover"] },
    key: { type: "string", pattern: keyPattern.source, description: "Stable key for this logical role turn" },
    child: { type: "string", pattern: sessionID.source, description: "Existing direct child session (send only)" },
    brief: { type: "string", minLength: 1, maxLength: 32000, description: "Exact authorized role brief (send only)" },
    timeoutSeconds: { type: "integer", minimum: 30, maximum: 86400, description: "Time before reporting an unknown result; default 600" },
  },
}

// A successful idle alone is not a result. A role can go idle with a live shell,
// and a reused child can contain several previously completed results.
function result(messages, record) {
  const start = messages.findIndex((m) => m.type === "user" && m.id === record.inputID)
  if (start < 0) return
  let final
  for (const m of messages.slice(start + 1)) {
    if (m.type === "user") break
    if (m.type === "assistant") {
      const text = m.agent === record.role && m.finish === "stop" && !m.error ? assistantText(m) : ""
      final = text.trimEnd().endsWith(`\n${marker(record.ticket)}`) ? { message: m.id, text } : undefined
    }
    if (m.type !== "idle") continue
    if (m.outcome === "failed" || m.outcome === "interrupted")
      return { state: "failed", idle: m.id, reason: `Child execution ${m.outcome}` }
    if (m.outcome === "succeeded" && final) return { state: "delivered", idle: m.id, ...final }
    final = undefined
  }
}

export async function installDispatch(ctx, { root, info, fences, serial }) {
  const { managedDispatch, capabilities } = ctx.options ?? {}
  const enabled = managedDispatch === true || (managedDispatch === undefined &&
    (capabilities === undefined || (Array.isArray(capabilities) && capabilities.includes("dispatch-v1"))))
  if (!enabled || !ctx.session?.synthetic || !ctx.session.hook) return
  const prefix = `dispatch/v1/${digest(root)}/`
  const records = new Map()
  const timers = new Map()
  const sessions = ctx.session
  let closed = false

  async function save(r) {
    await ctx.storage.set(prefix + r.ticket, r)
    records.set(r.ticket, r)
    return r
  }

  async function authorize(r, source) {
    const parent = await info(r.parent)
    const child = await info(r.child)
    require(parent.agent === r.driver && child.parentID === parent.id && child.agent === r.role,
      "dispatch owner, child, or role changed")
    await ctx.permission.assert({
      sessionID: parent.id, agent: parent.agent, action: "subagent", resources: [child.agent], save: [],
      ...(source && { source }),
    })
  }

  const publicState = (r) => ({
    key: r.key, ticket: r.ticket, child: r.child, inputID: r.inputID, state: r.state,
    deadline: r.deadline, ref: r.outcome?.message && { session: r.child, message: r.outcome.message },
    reason: r.reason,
  })

  async function notify(r, outcome) {
    const id = `msg_${digest([r.ticket, outcome.state])}`
    const ref = outcome.message ? ` Source: ${r.child}/${outcome.message}.` : ""
    const text = `PDCA dispatch ${r.key} (${r.ticket}): ${outcome.state}.${ref}\n` +
      (outcome.text ?? `${outcome.reason}. Keep the same phase and counters; reconcile the existing child. Do not launch a replacement on an unknown outcome.`)
    await sessions.synthetic({
      sessionID: r.parent, id, text, delivery: "queue",
      metadata: { source: "pdca-dispatch", ticket: r.ticket, childID: r.child,
        ...(outcome.message && { messageID: outcome.message }) },
    })
  }

  const unchanged = async (r) => isDeepStrictEqual(await fences(r.parent), r.fences)
  const hold = (r) => save({ ...r, state: "held", reason: "New instruction since dispatch; reconcile before continuing" })

  async function reconcile(r) {
    if (closed || ended.has(r.state)) return r
    await authorize(r)
    if (!(await unchanged(r))) return hold(r)
    const outcome = r.outcome ?? result(await sessions.context({ sessionID: r.child }), r)
    if (outcome) {
      // Save the exact report before notification. Replays reuse the same inbox ID
      // even if the server admitted the notification but lost its response.
      if (!r.outcome) r = await save({ ...r, state: "pending-result", outcome })
      if (!(await unchanged(r))) return hold(r)
      if (closed) return r
      await notify(r, outcome)
      const { text, ...receipt } = outcome
      return save({ ...r, state: outcome.state, outcome: receipt, reason: outcome.reason })
    }
    if (r.state !== "unknown" && Date.now() >= r.deadline) {
      const reason = "No bound terminal report at the deadline"
      if (!(await unchanged(r))) return hold(r)
      if (closed) return r
      await notify(r, { state: "unknown", reason })
      return save({ ...r, state: "unknown", reason })
    }
    return r
  }

  function schedule(r) {
    if (closed || timers.has(r.ticket) || ended.has(r.state)) return
    const timer = setTimeout(() => {
      timers.delete(r.ticket)
      void run(r.ticket)
    }, Math.max(0, r.deadline - Date.now()))
    timer.unref?.()
    timers.set(r.ticket, timer)
  }

  function pruneTimer(r) {
    if (!ended.has(r.state)) return
    clearTimeout(timers.get(r.ticket))
    timers.delete(r.ticket)
  }

  const run = (ticket) => serial(async () => pruneTimer(await reconcile(records.get(ticket)))).catch((e) => {
    if (!closed) console.warn(`[pdca-dispatch] ${ticket}: ${e.message}`)
  })

  let after
  do {
    const page = await ctx.storage.scan({ prefix, after, limit: 100 })
    for (const { value: r } of page.entries) records.set(r.ticket, r)
    after = page.next
  } while (after)

  const registration = await sessions.hook("context", (event) => {
    // Native child reports remain in history. Hide only managed marked results
    // from this recipient's model so a late native wake can't route them twice.
    event.messages = event.messages.filter((m) => {
      if (m.metadata?.source !== "subagent") return true
      const content = typeof m.content === "string" ? m.content :
        m.content?.filter((p) => p.type === "text").map((p) => p.text).join("\n") ?? ""
      const match = content.match(/\nPDCA-DISPATCH ([0-9a-f]{64}) complete(?=\s*(?:Background work still running:|<\/background-result>))/)
      const r = match && records.get(match[1])
      return !(r && r.parent === event.sessionID && r.child === m.metadata.childID)
    })
  })

  async function invoke(i, context) {
    const parent = await info(context.sessionID)
    require(drivers.has(parent.agent) && parent.agent === context.agent && keyPattern.test(i.key),
      "PDCA driver and stable dispatch key required")
    const ticket = digest([root, parent.id, i.key])
    const old = records.get(ticket)
    if (i.action === "inspect" || i.action === "recover") {
      require(old, "unknown dispatch key")
      if (i.action === "inspect") return publicState(old)
      const r = await reconcile(old)
      pruneTimer(r)
      return publicState(r)
    }
    const seconds = i.timeoutSeconds ?? 600
    require(i.action === "send" && sessionID.test(i.child) && typeof i.brief === "string" &&
      i.brief.trim() && i.brief.length <= 32000 && Number.isInteger(seconds) && seconds >= 30 && seconds <= 86400,
      "invalid dispatch")
    const briefHash = digest([i.brief, seconds])
    if (old) {
      require(old.child === i.child && old.briefHash === briefHash, "dispatch key already bound to different inputs")
      return publicState(old)
    }
    const child = await info(i.child)
    require(child.parentID === parent.id && roles.has(child.agent), "expected existing direct PDCA child")
    require(![...records.values()].some((r) => r.child === child.id && !ended.has(r.state)),
      "child already has an unresolved dispatch")
    const r = {
      ticket, key: i.key, parent: parent.id, driver: parent.agent, child: child.id, role: child.agent,
      inputID: `msg_${digest([ticket, "input"])}`, briefHash, deadline: Date.now() + seconds * 1000,
      state: "pending", fences: await fences(parent.id),
    }
    await authorize(r, { type: "tool", messageID: context.messageID, id: context.id })
    const last = (await sessions.context({ sessionID: child.id })).at(-1)
    require(!last || last.type === "idle", "child still has work or unconsumed input")
    require(await unchanged(r), "new instruction before dispatch")
    await save(r)
    schedule(r)
    try {
      await sessions.prompt({
        sessionID: child.id, id: r.inputID, delivery: "queue",
        text: `${i.brief}\n\nFor this managed turn, append the following exact line only to your final report, after all required background work and evidence are ready. An interim report must omit it.\n${marker(ticket)}`,
      })
    } catch (e) {
      // Admission may have succeeded. The dispatch is already registered; neither
      // a duplicate tool call nor automatic recovery resends an unknown input.
      console.warn(`[pdca-dispatch] ${ticket}: admission uncertain: ${e.message}`)
      return publicState(r)
    }
    return publicState(await save({ ...r, state: "admitted" }))
  }

  await ctx.tool.transform((editor) => editor.add({
    name: tool,
    description: "PDCA transport: send an already authorized role brief to an idle direct child once; inspect or recover its durable result by the same key. Never use alongside another adapter that owns the same handoff.",
    input: schema,
    options: { permission: tool, codemode: false },
    async execute(i, context) {
      return { content: JSON.stringify(await serial(() => invoke(i, context))) }
    },
  }))

  return {
    restore() {
      for (const r of records.values()) {
        if (ended.has(r.state)) continue
        if (Date.now() < r.deadline) schedule(r)
        void run(r.ticket)
      }
    },
    async event(e) {
      if (!terminal.has(e.type)) return
      for (const r of records.values()) {
        if (r.child === e.data?.sessionID && !ended.has(r.state)) await run(r.ticket)
      }
    },
    async close() {
      closed = true
      for (const timer of timers.values()) clearTimeout(timer)
      timers.clear()
      await registration.dispose()
    },
  }
}
