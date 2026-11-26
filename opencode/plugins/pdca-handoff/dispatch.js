import { createHash } from "node:crypto"
import { isDeepStrictEqual } from "node:util"

const tool = "pdca_dispatch_v1"
const digest = (value) => createHash("sha256").update(JSON.stringify(value)).digest("hex")
const sessionID = /^ses_[a-zA-Z0-9]+$/
const keyPattern = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/
const reportPattern = /^[a-f0-9]{16}$/
const nativeBinding = (ticket) => `PDCA-DISPATCH ${ticket} native`
const nativeNotice = /^<background-result kind="subagent" sessionID="[^"]+" state="completed"[^\n]*>\n([\s\S]*)\n<\/background-result>$/
const exclusiveProtocol = /\bPDCA-(?:HANDOFF|RECORD|DISPATCH)\b/
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
const managedBrief = (brief, ticket) =>
  `${brief}\n\nFor this managed turn, append the following exact line only to your final report, after all required background work and evidence are ready. An interim report must omit it.\n${marker(ticket)}`
const reportKey = (parent, id) => digest([parent, id]).slice(0, 16)
const sourceNotice = (message) =>
  (message.metadata?.source === "subagent" && message.metadata.state === "completed" && nativeNotice.test(message.text)) ||
  (message.metadata?.source === "pdca-dispatch" && typeof message.metadata.messageID === "string")
const messageText = (message) => typeof message.content === "string" ? message.content :
  message.content?.filter((p) => p.type === "text").map((p) => p.text).join("\n") ?? ""
const driverPointer =
  "pdca_dispatch_v1 is available. Before a new role dispatch, apply §Dispatch transport in the " +
  "base pdca skill's references/driver.md; on resume, read the current section before choosing a sender."
const reportPointer =
  "To pass a completed report to an executor for capture, use its PDCA-REPORT token instead of " +
  "typing a child session or message ID: set report on pdca_dispatch_v1, or copy the whole token line into an eligible native follow-up."

const schema = {
  type: "object",
  additionalProperties: false,
  required: ["action", "key"],
  properties: {
    action: { type: "string", enum: ["send", "inspect", "recover"] },
    key: { type: "string", pattern: keyPattern.source, description: "Stable key for this logical role turn" },
    child: { type: "string", pattern: sessionID.source, description: "Existing direct child session (send only)" },
    brief: { type: "string", minLength: 1, maxLength: 32000, description: "Exact authorized role brief (send only)" },
    report: { type: "string", pattern: reportPattern.source, description: "PDCA report token from this driver's completed notice (send only)" },
    timeoutSeconds: { type: "integer", minimum: 30, maximum: 86400, description: "Time before reporting an unknown result; default 600" },
  },
}

// A successful idle alone is not a result. A role can go idle with a live shell,
// and a reused child can contain several previously completed results.
function childTurn(messages, record) {
  const start = messages.findIndex((m) => m.type === "user" &&
    (record.native ? m.text?.split("\n").includes(nativeBinding(record.ticket)) : m.id === record.inputID))
  if (start < 0) return
  const stop = messages.findIndex((m, i) => i > start && m.type === "user")
  return { inputID: messages[start].id, messages: messages.slice(start + 1, stop < 0 ? undefined : stop) }
}

function result(turn, record) {
  if (!turn) return
  let final
  for (const m of turn.messages) {
    if (m.type === "assistant") {
      const text = m.agent === record.role && m.finish === "stop" && !m.error ? assistantText(m) : ""
      final = text.trimEnd().endsWith(`\n${marker(record.ticket)}`) ? { message: m.id, text } : undefined
    }
    if (m.type !== "idle") continue
    if (m.outcome === "failed" || m.outcome === "interrupted")
      return { state: "failed", idle: m.id, inputID: turn.inputID, reason: `Child execution ${m.outcome}` }
    if (m.outcome === "succeeded" && final)
      return { state: "delivered", idle: m.id, inputID: turn.inputID, ...final }
    final = undefined
  }
}

function alreadyDelivered(turn, parentMessages, record) {
  const hits = []
  for (const [i, msg] of turn.messages.entries()) {
    const idle = turn.messages[i + 1]
    if (msg.type !== "assistant" || msg.agent !== record.role || msg.finish !== "stop" ||
      msg.error || idle?.type !== "idle" || idle.outcome !== "succeeded") continue
    const text = assistantText(msg)
    const completed = msg.time?.completed
    if (!text || !Number.isFinite(completed) || text.trimEnd().endsWith(`\n${marker(record.ticket)}`)) continue
    for (const notice of parentMessages)
      if (notice.type === "synthetic" && notice.metadata?.source === "subagent" &&
        notice.metadata.state === "completed" && notice.metadata.childID === record.child &&
        notice.time?.created >= completed && nativeNotice.exec(notice.text)?.[1] === text)
        hits.push({ state: "delivered", idle: idle.id, inputID: turn.inputID, message: msg.id, nativeNotice: notice.id })
  }
  return hits.length === 1 ? hits[0] : undefined
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
    key: r.key, ticket: r.ticket, child: r.child, inputID: r.inputID ?? r.outcome?.inputID, state: r.state,
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
  const outstanding = (child) => [...records.values()].some((r) => r.child === child && !ended.has(r.state))

  async function boundReport(parent, token) {
    require(typeof token === "string" && reportPattern.test(token), "invalid PDCA report token")
    const notices = (await sessions.context({ sessionID: parent.id })).filter((m) =>
      m.type === "synthetic" && reportKey(parent.id, m.id) === token && sourceNotice(m))
    require(notices.length === 1, "expected one completed PDCA report notice in this driver")
    const notice = notices[0]
    const source = await info(notice.metadata.childID)
    require(source.parentID === parent.id && (roles.has(source.agent) || source.agent === "pdca-check"),
      "report source is not this driver's direct PDCA child")
    const messages = await sessions.context({ sessionID: source.id })
    const nativeBody = nativeNotice.exec(notice.text)?.[1]
    const reports = messages.filter((m, i) => m.type === "assistant" && m.agent === source.agent &&
      m.finish === "stop" && !m.error && messages[i + 1]?.type === "idle" &&
      messages[i + 1].outcome === "succeeded" &&
      (notice.metadata.source === "pdca-dispatch" ? m.id === notice.metadata.messageID :
        nativeBody && assistantText(m) === nativeBody))
    require(reports.length === 1, "report notice does not identify one exact completed child message")
    return `Verified PDCA report source: ${JSON.stringify({ session: source.id, message: reports[0].id })}. Use these exact IDs.`
  }

  async function reconcile(r) {
    if (closed || ended.has(r.state)) return r
    await authorize(r)
    if (!(await unchanged(r))) return hold(r)
    let outcome = r.outcome
    if (!outcome) {
      const turn = childTurn(await sessions.context({ sessionID: r.child }), r)
      outcome = result(turn, r)
      if (!outcome && r.native && turn)
        outcome = alreadyDelivered(turn, await sessions.context({ sessionID: r.parent }), r)
    }
    if (outcome) {
      // A native final report without our marker is still valid if the parent
      // already received it. Retire the watch without sending a second notice.
      if (outcome.nativeNotice) return save({ ...r, state: "delivered", outcome })
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
    // A resumed orchestrator may still have pre-plugin instructions in its transcript.
    if (event.agent === "pdca-orchestrator" && Object.hasOwn(event.tools, tool))
      event.system.push({ type: "text", text: driverPointer })
    // Native child reports remain in history. Hide only managed marked results
    // from this recipient's model so a late native wake can't route them twice.
    event.messages = event.messages.filter((m) => {
      if (m.metadata?.source !== "subagent") return true
      const match = messageText(m).match(/\nPDCA-DISPATCH ([0-9a-f]{64}) complete(?=\s*(?:Background work still running:|<\/background-result>))/)
      const r = match && records.get(match[1])
      return !(r && r.parent === event.sessionID && r.child === m.metadata.childID)
    })
    if (drivers.has(event.agent) && (Object.hasOwn(event.tools, tool) || ctx.tool.hook && Object.hasOwn(event.tools, "subagent"))) {
      let reportVisible = false
      event.messages = event.messages.map((m) => {
        if (!m.metadata?.childID) return m
        const text = messageText(m)
        if (!sourceNotice({ ...m, text })) return m
        reportVisible = true
        return { ...m, content: `${text}\n\nPDCA-REPORT ${reportKey(event.sessionID, m.id)}` }
      })
      if (reportVisible) event.system.push({ type: "text", text: reportPointer })
    }
  })

  const nativeKey = (e) => `native-${digest([e.messageID, e.id]).slice(0, 32)}`
  async function nativeBefore(event) {
    const i = event.input
    if (event.tool !== "subagent" || event.agent !== "pdca-orchestrator" || !i ||
      !sessionID.test(i.sessionID) || !roles.has(i.agent) || i.model ||
      typeof i.prompt !== "string" || !i.prompt.trim() || i.prompt.length > 32000 || exclusiveProtocol.test(i.prompt)) return
    const parent = await info(event.sessionID).catch(() => undefined)
    const child = await info(i.sessionID).catch(() => undefined)
    if (!parent || parent.agent !== event.agent || child?.parentID !== parent.id || child.agent !== i.agent) return
    const history = await sessions.context({ sessionID: child.id })
    const last = history.at(-1)
    if (last && last.type !== "idle") return // Native steering into live turns is unchanged.
    const key = nativeKey(event)
    const ticket = digest([root, parent.id, key])
    require(!records.has(ticket) && !outstanding(child.id), "Existing managed dispatch must be reconciled before sending again")
    const selectors = [...i.prompt.matchAll(/^PDCA-REPORT ([^\r\n]*)\r?$/gm)]
    require(selectors.length <= 1, "expected one PDCA report token")
    const needsReport = selectors.length === 1
    require(!needsReport || i.agent === "pdca-executor", "only the executor receives a bound report")
    const source = needsReport ? `\n\n${await boundReport(parent, selectors[0][1])}` : ""
    const r = await save({
      ticket, key, parent: parent.id, driver: parent.agent, child: child.id, role: child.agent,
      native: true, briefHash: digest(i.prompt), deadline: Date.now() + 600_000,
      state: "pending", fences: await fences(parent.id),
    })
    schedule(r)
    // Keep OpenCode's original sender, permission checks and job. Bind its
    // delivered input by an exact line instead of submitting a second prompt.
    event.input = { ...i, prompt: `${managedBrief(i.prompt + source, ticket)}\n${nativeBinding(ticket)}` }
  }

  const nativeRegistration = await ctx.tool.hook?.("execute.before", (event) => {
    if (event.tool === "subagent" && event.agent === "pdca-orchestrator") return serial(() => nativeBefore(event))
  })
  const nativeReceipt = await ctx.tool.hook?.("execute.after", (event) => {
    if (event.tool !== "subagent" || event.agent !== "pdca-orchestrator" || event.status !== "completed") return
    return serial(async () => {
      const key = nativeKey(event)
      const r = records.get(digest([root, event.sessionID, key]))
      const meta = event.result.metadata
      if (!r?.native || meta?.sessionID !== r.child ||
        !event.input?.prompt?.endsWith(`\n${nativeBinding(r.ticket)}`)) return
      event.result.metadata = { ...meta, pdcaDispatch: { key, ticket: r.ticket } }
      if (typeof event.result.content === "string")
        event.result.content += `\nManaged PDCA dispatch ${key}: use the managed result notice; recover by this key if needed.`
      if (r.state === "pending") await save({ ...r, state: "admitted" })
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
    const briefHash = digest(i.report === undefined ? [i.brief, seconds] : [i.brief, seconds, i.report])
    if (old) {
      require(old.child === i.child && old.briefHash === briefHash, "dispatch key already bound to different inputs")
      return publicState(old)
    }
    const child = await info(i.child)
    require(child.parentID === parent.id && roles.has(child.agent), "expected existing direct PDCA child")
    require(!outstanding(child.id), "child already has an unresolved dispatch")
    require(i.report === undefined || child.agent === "pdca-executor", "only the executor receives a bound report")
    const report = i.report === undefined ? "" : `\n\n${await boundReport(parent, i.report)}`
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
        text: managedBrief(i.brief + report, ticket),
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
      for (const r of records.values()) {
        if (ended.has(r.state)) continue
        if ((terminal.has(e.type) && r.child === e.data?.sessionID) ||
          (r.native && r.parent === e.data?.sessionID &&
            (e.type === "session.synthetic" || e.type === "session.inbox.delivered")))
          await run(r.ticket)
      }
    },
    async close() {
      closed = true
      for (const timer of timers.values()) clearTimeout(timer)
      timers.clear()
      await nativeReceipt?.dispose()
      await nativeRegistration?.dispose()
      await registration.dispose()
    },
  }
}
