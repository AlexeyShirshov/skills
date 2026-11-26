import assert from "node:assert/strict"
import { mkdtemp, rm } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { test } from "node:test"
import plugin from "../index.js"

const parent = "ses_driver"
const child = "ses_executor"
const tool = "pdca_dispatch_v1"
const send = { action: "send", key: "N2-r1-n1-recover-check", child, brief: "Verify PostgreSQL access only." }
const command = { agent: "pdca-orchestrator", sessionID: parent, messageID: "msg_driver", id: "call_1" }

async function fixture(t, options = {}) {
  const root = await mkdtemp(join(tmpdir(), "pdca-dispatch-"))
  const defs = new Map()
  const stored = new Map()
  const history = new Map([[parent, [{ type: "user", id: "msg_original" }]], [child, []]])
  const prompts = []
  const notices = new Map()
  const sent = []
  const nativeHooks = new Map()
  let contextHook, emit, cleanup
  const control = { lostPrompt: false, lostNotice: false, deny: false, moved: false }
  const ctx = {
    options,
    location: { directory: root },
    storage: {
      set: async (k, v) => stored.set(k, structuredClone(v)),
      scan: async ({ prefix }) => ({
        entries: [...stored].filter(([k]) => k.startsWith(prefix)).map(([key, value]) => ({ key, value })),
      }),
    },
    permission: {
      assert: async ({ action, sessionID, resources }) => {
        assert.equal(action, "subagent")
        assert.equal(sessionID, parent)
        assert.deepEqual(resources, ["pdca-executor"])
        if (control.deny) throw Error("permission denied")
      },
    },
    session: {
      get: async ({ sessionID: id }) => ({
        id, agent: id === parent ? "pdca-orchestrator" : "pdca-executor", time: {},
        location: { directory: id === child && control.moved ? join(root, "other") : root },
        ...(id === child && { parentID: parent }),
      }),
      context: async ({ sessionID: id }) => history.get(id),
      prompt: async (p) => {
        assert.ok([...stored.values()].some((r) => r.inputID === p.id))
        prompts.push(p)
        history.get(child).push({ ...p, type: "user" })
        if (control.lostPrompt) throw Error("admission reply lost")
      },
      synthetic: async (p) => {
        sent.push(p.id)
        if (!notices.has(p.id)) notices.set(p.id, p)
        if (control.lostNotice) throw Error("delivery reply lost")
      },
      hook: async (type, fn) => {
        assert.equal(type, "context")
        contextHook = fn
        return { dispose: async () => { contextHook = undefined } }
      },
    },
    event: {
      subscribe({ signal }) {
        let receiver
        const events = []
        const push = (value) => {
          if (receiver) {
            const resolve = receiver
            receiver = undefined
            resolve(value)
          } else events.push(value)
        }
        emit = (type = "session.execution.succeeded", sessionID = child) =>
          new Promise((done) => push({ type, data: { sessionID }, done }))
        signal.addEventListener("abort", () => push(null), { once: true })
        return (async function* () {
          while (!signal.aborted) {
            const e = events.length ? events.shift() : await new Promise((r) => { receiver = r })
            if (!e) return
            yield e
            e.done()
          }
        })()
      },
    },
    tool: {
      transform: async (fn) => fn({ add: (d) => defs.set(d.name, d) }),
      hook: async (type, fn) => {
        nativeHooks.set(type, fn)
        return { dispose: async () => { nativeHooks.delete(type) } }
      },
    },
  }
  const stop = async () => {
    await cleanup?.()
    cleanup = undefined
  }
  const reload = async () => {
    await stop()
    defs.clear()
    cleanup = await plugin.setup(ctx)
  }
  t.after(async () => {
    await stop()
    await rm(root, { force: true, recursive: true })
  })
  await reload()
  const call = async (i, actor = command) => JSON.parse((await defs.get(tool).execute(i, actor)).content)
  const inspect = () => call({ action: "inspect", key: send.key })
  const recover = () => call({ action: "recover", key: send.key })
  const complete = (text, ticket, id = "msg_report") => {
    const body = ticket ? `${text}\nPDCA-DISPATCH ${ticket} complete` : text
    history.get(child).push({
      type: "assistant", id, agent: "pdca-executor", finish: "stop", content: [{ type: "text", text: body }],
    }, { type: "idle", id: `msg_idle_${id}`, outcome: "succeeded" })
    return body
  }
  const modelContext = (fields = {}) => {
    const event = { sessionID: parent, agent: command.agent, messages: [], system: [], tools: {}, ...fields }
    contextHook?.(event)
    return event
  }
  const native = async (input, fields = {}, hook = "execute.before") => {
    const event = { ...command, tool: "subagent", input, ...fields }
    await nativeHooks.get(hook)?.(event)
    return hook === "execute.before" ? event.input : event.result
  }
  return { call, inspect, recover, complete, history, prompts, notices, sent, control, stop, reload,
    emit: (...args) => emit(...args), modelContext, native, defs }
}

const nativeFollowUp = { sessionID: child, agent: "pdca-executor", prompt: send.brief }

test("native follow-up is managed without replacing the OpenCode sender", async (t) => {
  const f = await fixture(t)
  const input = await f.native(nativeFollowUp)
  const ticket = /\nPDCA-DISPATCH ([a-f0-9]{64}) native$/.exec(input.prompt)[1]
  assert.ok(input.prompt.startsWith(send.brief + "\n"))
  assert.equal(f.prompts.length, 0)
  const ack = await f.native(input, {
    status: "completed", result: { content: "Native launch", metadata: { sessionID: child } },
  }, "execute.after")
  const { key } = ack.metadata.pdcaDispatch
  assert.equal((await f.call({ action: "inspect", key })).state, "admitted")
  f.history.get(child).push({ id: "msg_native_admission", type: "user", text: input.prompt })
  f.complete("Native child report.", ticket)
  await f.emit()
  assert.equal(f.notices.size, 1)
  assert.match([...f.notices.values()][0].text, /Native child report\./)
  assert.equal([...f.notices.values()][0].metadata.childID, child)
  assert.equal((await f.call({ action: "inspect", key })).inputID, "msg_native_admission")
  await assert.rejects(f.native(nativeFollowUp), /Existing managed dispatch/)
})

test("preserve native initial dispatch, a live follow-up, CHECK, and another adapter's protocol", async (t) => {
  const f = await fixture(t)
  for (const input of [
    { agent: "pdca-executor", prompt: send.brief },
    { ...nativeFollowUp, agent: "pdca-check" },
    { ...nativeFollowUp, prompt: `${send.brief}\nPDCA-HANDOFF ticket` },
    { ...nativeFollowUp, prompt: `${send.brief}\nPDCA-RECORD receipt do` },
    { ...nativeFollowUp, model: "provider/override" },
  ]) assert.equal(await f.native(input), input)
  f.history.get(child).push({ id: "msg_live", type: "user", text: "Already running." })
  assert.equal(await f.native(nativeFollowUp), nativeFollowUp)
  assert.equal(f.notices.size, 0)
  assert.equal(f.prompts.length, 0)
})

test("an unmarked native completion retires the watch only after actual final delivery", async (t) => {
  const f = await fixture(t)
  const input = await f.native(nativeFollowUp)
  const ack = await f.native(input, {
    status: "completed", result: { content: "Native launch", metadata: { sessionID: child } },
  }, "execute.after")
  const { key } = ack.metadata.pdcaDispatch
  const messages = f.history.get(child)
  messages.push({ id: "msg_native_input", type: "user", text: input.prompt })
  const body = f.complete("Final report in the required native format.")
  messages.at(-2).time = { completed: 2000 }
  const notice = (id, state, created) => ({
    id, type: "synthetic", time: { created }, metadata: { source: "subagent", childID: child, state: "completed" },
    text: `<background-result kind="subagent" sessionID="${child}" state="${state}" description="Native">\n${body}\n</background-result>`,
  })
  const parentMessages = f.history.get(parent)
  parentMessages.push(notice("msg_old_report", "completed", 1000), notice("msg_running", "running", 2100))
  await f.emit("session.inbox.delivered", parent)
  assert.equal((await f.call({ action: "inspect", key })).state, "admitted")
  parentMessages.push(notice("msg_delivered", "completed", 2200))
  await f.emit("session.inbox.delivered", parent)
  const receipt = await f.call({ action: "inspect", key })
  assert.equal(receipt.state, "delivered")
  assert.equal(receipt.ref.message, "msg_report")
  assert.equal(f.notices.size, 0)
  assert.notEqual(await f.native(nativeFollowUp, { id: "call_next" }), nativeFollowUp)
})

test("restart recovers a native marked result without submitting a plugin prompt", async (t) => {
  const f = await fixture(t)
  const input = await f.native(nativeFollowUp)
  const ticket = /\nPDCA-DISPATCH ([a-f0-9]{64}) native$/.exec(input.prompt)[1]
  await f.stop()
  f.history.get(child).push({ id: "msg_native_input", type: "user", text: input.prompt })
  f.complete("Saved after the observer stopped.", ticket)
  await f.reload()
  // Drain the startup reconciliation before checking its notice.
  await f.emit()
  assert.equal(f.notices.size, 1)
  assert.equal(f.prompts.length, 0)
})

test("#403: resolve exact native report IDs from notification, not from the brief", async (t) => {
  const f = await fixture(t)
  const report = f.complete("Exact source body from the saved child.", undefined, "msg_exact_body")
  const text = `<background-result kind="subagent" sessionID="${child}" state="completed" description="Find facts">\n${report}\n</background-result>`
  const notice = { type: "synthetic", id: "msg_original_notice", text,
    metadata: { source: "subagent", childID: child, state: "completed" } }
  f.history.get(parent).push(notice)
  const projected = f.modelContext({ tools: { [tool]: {} }, messages: [{ ...notice, content: text }] })
  const token = /\nPDCA-REPORT ([a-f0-9]{16})$/.exec(projected.messages[0].content)[1]
  assert.match(projected.system.at(-1).text, /use its PDCA-REPORT token/)
  await assert.rejects(f.call({ ...send, report: "ffffffffffffffff" }), /one completed PDCA report/)
  const bound = await f.native({ ...nativeFollowUp, prompt: `Pin the indicated report.\nPDCA-REPORT ${token}` })
  assert.match(bound.prompt, /"session":"ses_executor","message":"msg_exact_body"/)
  assert.equal(f.prompts.length, 0)
  assert.equal(f.history.get(parent).at(-1), notice)
})

test("explicit dispatch binds a report token, and ambiguous native notices fail closed", async (t) => {
  const f = await fixture(t)
  const text = "Repeated scout summary."
  f.complete(text, undefined, "msg_first")
  f.complete(text, undefined, "msg_second")
  const notice = { type: "synthetic", id: "msg_notice", metadata: { source: "subagent", childID: child, state: "completed" },
    text: `<background-result kind="subagent" sessionID="${child}" state="completed" description="Observe">\n${text}\n</background-result>` }
  f.history.get(parent).push(notice)
  const msg = { ...notice, content: notice.text }
  const projected = f.modelContext({ tools: { [tool]: {} }, messages: [msg] })
  const token = projected.messages[0].content.split("PDCA-REPORT ")[1]
  await assert.rejects(f.call({ ...send, report: token }), /one exact completed child message/)
  assert.equal(f.prompts.length, 0)
  f.history.set(child, f.history.get(child).slice(0, 2))
  await f.call({ ...send, report: token })
  assert.match(f.prompts[0].text, /"session":"ses_executor","message":"msg_first"/)
})

test("a resumed orchestrator receives the current transport pointer only if it can call dispatch", async (t) => {
  const f = await fixture(t)
  const tools = { subagent: {}, [tool]: {} }
  const messages = [{ role: "assistant", content: "Previous follow-ups used subagent." }]
  await f.reload()
  const request = f.modelContext({ tools, messages })
  assert.match(request.system[0].text, /pdca_dispatch_v1.*references\/driver\.md/)
  assert.match(request.system[0].text, /on resume, read the current section/)
  assert.deepEqual(request.tools, tools)
  assert.deepEqual(request.messages, messages)
  assert.deepEqual(f.modelContext({ tools: { subagent: {} } }).system, [])
  assert.deepEqual(f.modelContext({ tools, agent: "pdca-executor" }).system, [])
  assert.equal(f.prompts.length, 0)
})

test("#417: deliver the saved child report without a native result or another execution", async (t) => {
  const f = await fixture(t)
  const request = await f.call(send)
  assert.equal(request.state, "admitted")
  assert.equal(f.prompts[0].id, request.inputID)
  assert.ok(f.prompts[0].text.startsWith(send.brief + "\n"))
  const original = f.complete("Verified access. No test or new attempt.", request.ticket)
  await f.emit()
  assert.deepEqual((await f.inspect()).ref, { session: child, message: "msg_report" })
  assert.equal((await f.inspect()).state, "delivered")
  assert.ok([...f.notices.values()][0].text.endsWith(original))
  await f.emit()
  await f.reload()
  await f.recover()
  assert.equal(f.sent.length, 1)
  assert.equal(f.prompts.length, 1)
  const late = {
    metadata: { source: "subagent", childID: child },
    content: [{ type: "text", text: `<background-result>\n${original}\n</background-result>` }],
  }
  const unrelated = { ...late, metadata: { source: "subagent", childID: "ses_other" } }
  const interim = { ...late, content: [{ type: "text", text: "Still building." }] }
  assert.deepEqual(f.modelContext({ messages: [late, unrelated, interim] }).messages, [unrelated, interim])
})

test("restart reconciles a child that finished with no observer", async (t) => {
  const f = await fixture(t)
  const request = await f.call(send)
  await f.stop()
  f.complete("Exact offline report.", request.ticket)
  await f.reload()
  assert.equal((await f.inspect()).state, "delivered")
  assert.equal(f.notices.size, 1)
  assert.equal(f.prompts.length, 1)
})

test("inbox admission with lost response replays by the same ID", async (t) => {
  const f = await fixture(t)
  const request = await f.call(send)
  f.complete("Exact report.", request.ticket)
  f.control.lostNotice = true
  await f.emit()
  assert.equal((await f.inspect()).state, "pending-result")
  f.control.lostNotice = false
  // Reconciliation doesn't reread an evicted child transcript after pinning the result.
  f.history.set(child, [])
  await f.reload()
  assert.equal((await f.inspect()).state, "delivered")
  assert.equal(f.sent.length, 2)
  assert.equal(new Set(f.sent).size, 1)
  assert.equal(f.notices.size, 1)
})

test("deadline wakes the parent with unknown, not failure or duplicate work; late result is accepted", async (t) => {
  const f = await fixture(t)
  t.mock.timers.enable({ apis: ["setTimeout", "Date"], now: 100000 })
  // #403 Step 23: the executor can go idle before its shell is done.
  const request = await f.call({ ...send, timeoutSeconds: 30 })
  f.complete("Build started in sh_fixture; wait for the receipt.", undefined, "msg_partial")
  await f.emit()
  assert.equal(f.notices.size, 0)
  t.mock.timers.tick(30000)
  assert.equal((await f.inspect()).state, "unknown")
  assert.match([...f.notices.values()][0].text, /No bound terminal report/)
  await assert.rejects(f.call({ ...send, key: "replacement" }), /unresolved/)
  await f.recover()
  assert.equal(f.sent.length, 1)
  f.history.get(child).push({ type: "synthetic", id: "msg_shell_exit", metadata: { source: "shell" } })
  f.complete("Build finished with the required evidence.", request.ticket)
  await f.emit()
  assert.equal((await f.inspect()).state, "delivered")
  assert.equal(f.sent.length, 2)
  assert.equal(f.prompts.length, 1)
})

test("deadline finds a saved result even when neither completion event nor notice arrives", async (t) => {
  const f = await fixture(t)
  t.mock.timers.enable({ apis: ["setTimeout", "Date"], now: 100000 })
  const request = await f.call({ ...send, timeoutSeconds: 30 })
  f.complete("Exact result without a completion event.", request.ticket)
  t.mock.timers.tick(30000)
  assert.equal((await f.inspect()).state, "delivered")
  assert.equal(f.notices.size, 1)
  assert.equal(f.prompts.length, 1)
})

test("unknown prompt admission is never retried; reject rebinding and recognize the bound report", async (t) => {
  const f = await fixture(t)
  f.control.lostPrompt = true
  const request = await f.call(send)
  assert.equal(request.state, "pending")
  await f.reload()
  assert.equal((await f.call(send)).inputID, request.inputID)
  await assert.rejects(f.call({ ...send, brief: "Different brief" }), /already bound/)
  assert.equal(f.prompts.length, 1)
  f.complete("Original input was admitted.", request.ticket)
  await f.emit()
  assert.equal((await f.inspect()).state, "delivered")
})

test("authorization gates the dispatch; changed instructions hold recovered output", async (t) => {
  const f = await fixture(t)
  await assert.rejects(f.call(send, { ...command, sessionID: child }), /PDCA driver/)
  f.control.deny = true
  await assert.rejects(f.call(send), /permission denied/)
  f.control.deny = false
  f.control.moved = true
  await assert.rejects(f.call(send), /session moved/)
  f.control.moved = false
  assert.equal(f.prompts.length, 0)
  const request = await f.call(send)
  f.history.get(parent).push({ type: "user", id: "msg_new_scope" })
  f.complete("Superseded report.", request.ticket)
  await f.emit()
  assert.equal((await f.inspect()).state, "held")
  assert.equal(f.notices.size, 0)
})

for (const [name, options, enabled] of [
  ["default", {}, true],
  ["explicit opt-out", { managedDispatch: false }, false],
  ["empty capability list", { capabilities: [] }, false],
  ["selected capability", { capabilities: ["dispatch-v1"] }, true],
  ["explicit override of capability list", { capabilities: [], managedDispatch: true }, true],
]) {
  test(`tool availability: ${name}`, async (t) => {
    const f = await fixture(t, options)
    assert.equal(f.defs.has(tool), enabled)
    if (!enabled) assert.equal(await f.native(nativeFollowUp), nativeFollowUp)
  })
}
