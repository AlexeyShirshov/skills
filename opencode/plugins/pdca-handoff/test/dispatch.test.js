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
    tool: { transform: async (fn) => fn({ add: (d) => defs.set(d.name, d) }) },
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
  const applyContext = (messages) => {
    const event = { sessionID: parent, messages }
    contextHook(event)
    return event.messages
  }
  return { call, inspect, recover, complete, history, prompts, notices, sent, control, stop, reload,
    emit: (...args) => emit(...args), applyContext, defs }
}

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
  assert.deepEqual(f.applyContext([late, unrelated, interim]), [unrelated, interim])
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
  })
}
