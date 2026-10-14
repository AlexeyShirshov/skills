// Smoke test: drives the real `setup()` with synthetic V2 events and a fake
// powershell, so every assertion is made against the toasts the plugin would
// raise — no Windows desktop involved.
//
//   node test/smoke.mjs

import { mkdtemp, writeFile, chmod, readFile, rm } from "node:fs/promises"
import { join } from "node:path"
import { tmpdir } from "node:os"

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const dir = await mkdtemp(join(tmpdir(), "wsl-notify-test-"))
const fake = join(dir, "fake-powershell.sh")
const log = join(dir, "toasts.log")

await writeFile(fake, `#!/bin/sh\nprintf '%s\\n' "$*" >> '${log}'\n`)
await chmod(fake, 0o755)

let failures = 0
function check(name, condition, extra = "") {
  if (condition) {
    console.log(`  ok   ${name}`)
  } else {
    failures += 1
    console.log(`  FAIL ${name}${extra ? ` — ${extra}` : ""}`)
  }
}

async function toasts() {
  const content = await readFile(log, "utf8").catch(() => "")
  return content.split("\n").filter(Boolean)
}

// Each toast is one invocation of the fake executable: the last argument is the
// base64 UTF-16LE script, whose XML carries the title and the message.
function toastText(line) {
  const encoded = line.split(" ").at(-1)
  return Buffer.from(encoded, "base64").toString("utf16le")
}

function resetState() {
  const state = globalThis[Symbol.for("opencode.wsl-notify.state")]
  if (!state) return
  for (const timer of state.pending.values()) clearTimeout(timer)
  state.pending.clear()
  state.seen.clear()
  state.started?.clear()
  state.sessions?.clear()
  state.priming?.clear()
  state.warned.clear()
}

// The plugin must never *await* a session read inside the event handler: live, a
// read issued while that session is finishing never returns. The fake below
// reproduces that — it counts calls and never settles. A regression therefore
// stalls the handler (no toast) instead of passing quietly.
let sessionGetCalls = 0

function neverSettles() {
  sessionGetCalls += 1
  return new Promise(() => {})
}

async function run(events, options = {}, gap = 10, sessionGetter = neverSettles) {
  await writeFile(log, "")
  resetState()
  sessionGetCalls = 0

  const module = await import("../index.js")
  const ctx = {
    options: { powershell: fake, graceMs: 40, minTurnMs: 0, ...options },
    event: {
      subscribe: async function* () {
        for (const event of events) {
          yield event
          await sleep(gap)
        }
      },
    },
    session: { get: sessionGetter },
  }

  const dispose = module.default.setup(ctx)
  await sleep(200)
  dispose()
  await sleep(20)
  return toasts()
}

const SESSION = "ses_test"
const sessionCreated = (sessionID, parentID) => ({
  id: `evt_created_${sessionID}`,
  type: "session.created",
  data: parentID ? { sessionID, parentID, title: `Title of ${sessionID}` } : { sessionID, title: `Title of ${sessionID}` },
})
const permissionAsked = (id, sessionID = SESSION) => ({
  id: `evt_${id}`,
  type: "permission.asked",
  data: { id, sessionID },
})
const permissionReplied = (id, sessionID = SESSION) => ({
  id: `evt_reply_${id}`,
  type: "permission.replied",
  data: { requestID: id, sessionID },
})

console.log("permission")
{
  const raised = await run([permissionAsked("per_1")])
  check("waiting permission produces one toast", raised.length === 1, `got ${raised.length}`)
  check("toast asks for input", toastText(raised[0] ?? "").includes("Permission needs input"))
}
{
  const raised = await run([permissionAsked("per_2"), permissionReplied("per_2")])
  check("permission answered inside the grace window stays silent", raised.length === 0, `got ${raised.length}`)
}
{
  const raised = await run([permissionAsked("per_3"), permissionAsked("per_3"), permissionAsked("per_3")])
  check("re-emitted permission toasts once", raised.length === 1, `got ${raised.length}`)
}
{
  // The environment is the only knob for a locally discovered plugin file.
  // A 40ms window with a reply at ~60ms must toast; if the variable were ignored,
  // the 500ms default would swallow it.
  process.env.WSL_NOTIFY_GRACE_MS = "40"
  const raised = await run([permissionAsked("per_4"), permissionReplied("per_4")], { graceMs: undefined }, 60)
  check("WSL_NOTIFY_GRACE_MS widens/narrows the window", raised.length === 1, `got ${raised.length}`)
  process.env.WSL_NOTIFY_GRACE_MS = "2000"
  const quiet = await run([permissionAsked("per_5"), permissionReplied("per_5")], { graceMs: undefined }, 60)
  check("a large WSL_NOTIFY_GRACE_MS suppresses the toast", quiet.length === 0, `got ${quiet.length}`)
  delete process.env.WSL_NOTIFY_GRACE_MS
}

console.log("completion")
{
  const raised = await run([
    sessionCreated(SESSION),
    { id: "e1", type: "session.execution.started", data: { sessionID: SESSION } },
    { id: "e2", type: "session.execution.succeeded", data: { sessionID: SESSION } },
  ])
  check("finished session toasts once", raised.length === 1, `got ${raised.length}`)
  check("toast says the session finished", toastText(raised[0] ?? "").includes("Session finished"))
  check("toast carries the session title", toastText(raised[0] ?? "").includes("Title of ses_test"))
  check("a known session needs no server read", sessionGetCalls === 0, `calls=${sessionGetCalls}`)
}
{
  // A session that predates the plugin: no announcement, and the read hangs
  // exactly like the live one. The toast must not wait for it.
  const raised = await run([{ id: "e1", type: "session.execution.succeeded", data: { sessionID: "ses_unseen" } }])
  check("a session read that never settles does not stop the toast", raised.length === 1, `got ${raised.length}`)
  check("the plugin asked the server about the unknown session", sessionGetCalls >= 1, `calls=${sessionGetCalls}`)
}
{
  // Same pre-existing session, but this time the read answers: the title it
  // returns is used for the toast.
  const primed = async ({ sessionID }) => ({ id: sessionID, title: "Primed title" })
  const raised = await run(
    [
      { id: "e1", type: "session.execution.started", data: { sessionID: "ses_old" } },
      { id: "e2", type: "session.execution.succeeded", data: { sessionID: "ses_old" } },
    ],
    {},
    10,
    primed,
  )
  check("a title learned from the server is used", toastText(raised[0] ?? "").includes("Primed title"))
}
{
  // A pre-existing subagent session: the primed record carries its parent, so it
  // stays quiet like any other subagent.
  const primedChild = async ({ sessionID }) => ({ id: sessionID, title: "Child", parentID: SESSION })
  const raised = await run(
    [
      { id: "e1", type: "session.execution.started", data: { sessionID: "ses_old_child" } },
      { id: "e2", type: "session.execution.succeeded", data: { sessionID: "ses_old_child" } },
    ],
    {},
    10,
    primedChild,
  )
  check("a pre-existing subagent is silent once primed", raised.length === 0, `got ${raised.length}`)
}
{
  const raised = await run([
    sessionCreated(SESSION),
    { id: "e1", type: "session.execution.succeeded", data: { sessionID: SESSION } },
    { id: "e2", type: "session.idle", data: { sessionID: SESSION } },
  ])
  check("succeeded plus legacy idle coalesces into one toast", raised.length === 1, `got ${raised.length}`)
}
{
  const raised = await run([
    sessionCreated(SESSION),
    { id: "e1", type: "session.execution.succeeded", data: { sessionID: SESSION } },
    { id: "e2", type: "session.execution.started", data: { sessionID: SESSION } },
    { id: "e3", type: "session.execution.succeeded", data: { sessionID: SESSION } },
  ])
  check("a second turn toasts again", raised.length === 2, `got ${raised.length}`)
}
{
  const subagent = "ses_child"
  const raised = await run([
    sessionCreated(subagent, SESSION),
    { id: "e1", type: "session.execution.succeeded", data: { sessionID: subagent } },
  ])
  check("subagent completion stays silent by default", raised.length === 0, `got ${raised.length}`)
}
{
  const subagent = "ses_child2"
  const raised = await run(
    [
      sessionCreated(subagent, SESSION),
      { id: "e1", type: "session.execution.succeeded", data: { sessionID: subagent } },
    ],
    { subagentComplete: true },
  )
  check("subagent completion toasts when enabled", raised.length === 1, `got ${raised.length}`)
  check("subagent toast is labelled", toastText(raised[0] ?? "").includes("Subagent finished"))
}
{
  // A session the stream never announced (it predates the plugin or a reload):
  // stay quiet only if we truly know it is a child, otherwise notify.
  const raised = await run([
    { id: "e1", type: "session.execution.succeeded", data: { sessionID: "ses_unseen" } },
  ])
  check("an unknown session is still announced", raised.length === 1, `got ${raised.length}`)
}

console.log("short turns")
{
  // Default is 500ms: a turn of ~10ms was answered while you were still looking.
  const raised = await run(
    [
      { id: "e1", type: "session.execution.started", data: { sessionID: SESSION } },
      { id: "e2", type: "session.execution.succeeded", data: { sessionID: SESSION } },
    ],
    { minTurnMs: undefined },
  )
  check("a turn shorter than the default 500ms stays silent", raised.length === 0, `got ${raised.length}`)
}
{
  const raised = await run(
    [
      { id: "e1", type: "session.execution.started", data: { sessionID: SESSION } },
      { id: "e2", type: "session.execution.succeeded", data: { sessionID: SESSION } },
    ],
    { minTurnMs: 100 },
    120,
  )
  check("a turn longer than minTurnMs toasts", raised.length === 1, `got ${raised.length}`)
}
{
  // No start event (plugin loaded mid-turn, service restarted): fail open.
  const raised = await run(
    [{ id: "e1", type: "session.execution.succeeded", data: { sessionID: SESSION } }],
    { minTurnMs: undefined },
  )
  check("a completion without a start mark toasts anyway", raised.length === 1, `got ${raised.length}`)
}
{
  // 50ms is below the ~120ms turn: only reading the variable can raise a toast
  // here, because the 500ms default would suppress it.
  process.env.WSL_NOTIFY_MIN_TURN_MS = "50"
  const raised = await run(
    [
      { id: "e1", type: "session.execution.started", data: { sessionID: SESSION } },
      { id: "e2", type: "session.execution.succeeded", data: { sessionID: SESSION } },
    ],
    { minTurnMs: undefined },
    120,
  )
  check("WSL_NOTIFY_MIN_TURN_MS sets the threshold", raised.length === 1, `got ${raised.length}`)
  delete process.env.WSL_NOTIFY_MIN_TURN_MS
}

console.log("failure")
{
  const raised = await run([
    { id: "e1", type: "session.execution.failed", data: { sessionID: SESSION, error: { message: "boom" } } },
  ])
  check("failed session toasts once", raised.length === 1, `got ${raised.length}`)
  check("toast carries the error message", toastText(raised[0] ?? "").includes("Error: boom"))
}

console.log("question")
{
  const raised = await run([
    {
      id: "e1",
      type: "form.created",
      data: { form: { id: "frm_1", title: "Pick one", fields: [{ title: "Which?" }] } },
    },
  ])
  check("form toasts once", raised.length === 1, `got ${raised.length}`)
  check("toast carries the form title", toastText(raised[0] ?? "").includes("Pick one"))
  check("toast carries the question", toastText(raised[0] ?? "").includes("Which?"))
}

console.log("1.18.x (V1 context)")
{
  // V1 nests the session under `properties.info`, and reports a finished turn as
  // `session.idle` with the id at the top level of `properties`.
  const raised = await run([
    { id: "evt_v1_created", type: "session.created", properties: { info: { id: SESSION, title: "V1 title" } } },
    { id: "evt_v1_idle", type: "session.idle", properties: { sessionID: SESSION } },
  ])
  check("V1 idle toasts once", raised.length === 1, `got ${raised.length}`)
  check("V1 toast carries the title from properties.info", toastText(raised[0] ?? "").includes("V1 title"))
}
{
  const raised = await run([
    {
      id: "evt_v1_child",
      type: "session.created",
      properties: { info: { id: "ses_v1_child", title: "Child", parentID: SESSION } },
    },
    { id: "evt_v1_child_idle", type: "session.idle", properties: { sessionID: "ses_v1_child" } },
  ])
  check("V1 subagent finish stays silent", raised.length === 0, `got ${raised.length}`)
}
{
  // V1 reports a failure as `session.error`, text in `properties.error.data.message`.
  const raised = await run([
    {
      id: "evt_v1_error",
      type: "session.error",
      properties: { sessionID: SESSION, error: { name: "APIError", data: { message: "V1 blew up" } } },
    },
  ])
  check("V1 session.error toasts once", raised.length === 1, `got ${raised.length}`)
  check("V1 error toast carries the message", toastText(raised[0] ?? "").includes("Error: V1 blew up"))
}
{
  // 1.18.x calls `setup` with a context that has no event stream: it must neither
  // throw nor leave anything behind, because `server()` carries the events there.
  const module = await import("../index.js")
  let blew = false
  let result
  try {
    result = module.default.setup({ options: { powershell: fake } })
    if (result instanceof Promise) await result
  } catch {
    blew = true
  }
  check("setup without an event stream does not throw", !blew)
  check("setup without an event stream returns no cleanup", result === undefined)
}
{
  // Several turns in one long-lived process (the TUI keeps one server for the
  // whole session). 1.18.x has no `session.execution.started`, so the turn
  // boundary has to come from a new user message — otherwise only the first
  // finished turn of a session would ever toast.
  const raised = await run([
    { id: "v1_turn1", type: "session.idle", properties: { sessionID: SESSION } },
    { id: "v1_user2", type: "message.updated", properties: { sessionID: SESSION, info: { id: "msg_u2", role: "user" } } },
    { id: "v1_busy2", type: "session.status", properties: { sessionID: SESSION, status: { type: "busy" } } },
    { id: "v1_turn2", type: "session.idle", properties: { sessionID: SESSION } },
  ])
  check("a second turn in the same process toasts too", raised.length === 2, `got ${raised.length}`)
}
{
  // 1.18.x re-emits the same user message with its summary right before the turn
  // ends. That re-emission must not release the completion key, or the re-emitted
  // `session.idle` would toast a second time for the same turn.
  const raised = await run([
    { id: "v1_reemit1", type: "message.updated", properties: { sessionID: SESSION, info: { id: "msg_same", role: "user" } } },
    { id: "v1_reemit2", type: "session.idle", properties: { sessionID: SESSION } },
    {
      id: "v1_reemit3",
      type: "message.updated",
      properties: { sessionID: SESSION, info: { id: "msg_same", role: "user", summary: { diffs: [] } } },
    },
    { id: "v1_reemit4", type: "session.idle", properties: { sessionID: SESSION } },
  ])
  check("a re-emitted user message does not re-arm the completion", raised.length === 1, `got ${raised.length}`)
}
{
  // No turn boundary between them: the legacy re-emission stays coalesced.
  const raised = await run([
    { id: "v1_dup1", type: "session.idle", properties: { sessionID: SESSION } },
    { id: "v1_dup2", type: "session.idle", properties: { sessionID: SESSION } },
  ])
  check("idle re-emitted without a new turn stays quiet", raised.length === 1, `got ${raised.length}`)
}
{
  // The user message is the turn-start mark, so `minTurnMs` works on 1.18.x too.
  const raised = await run(
    [
      { id: "v1_short_start", type: "message.updated", properties: { sessionID: SESSION, info: { role: "user" } } },
      { id: "v1_short_end", type: "session.idle", properties: { sessionID: SESSION } },
    ],
    { minTurnMs: 500 },
    10,
  )
  check("V1 turn inside minTurnMs stays silent", raised.length === 0, `got ${raised.length}`)
}

await rm(dir, { recursive: true, force: true })

console.log(failures === 0 ? "\nall checks passed" : `\n${failures} check(s) failed`)
process.exit(failures === 0 ? 0 : 1)
