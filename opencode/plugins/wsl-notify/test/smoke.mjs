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
  state.warned.clear()
}

async function run(events, options = {}, sessions = {}, gap = 10) {
  await writeFile(log, "")
  resetState()

  const module = await import("../index.js")
  const ctx = {
    options: { powershell: fake, graceMs: 40, ...options },
    event: {
      subscribe: async function* () {
        for (const event of events) {
          yield event
          await sleep(gap)
        }
      },
    },
    session: {
      get: async ({ sessionID }) => sessions[sessionID] ?? { id: sessionID, title: "Test session" },
    },
  }

  const dispose = module.default.setup(ctx)
  await sleep(200)
  dispose()
  await sleep(20)
  return toasts()
}

const SESSION = "ses_test"
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
  const raised = await run([permissionAsked("per_4"), permissionReplied("per_4")], { graceMs: undefined }, {}, 60)
  check("WSL_NOTIFY_GRACE_MS widens/narrows the window", raised.length === 1, `got ${raised.length}`)
  process.env.WSL_NOTIFY_GRACE_MS = "2000"
  const quiet = await run([permissionAsked("per_5"), permissionReplied("per_5")], { graceMs: undefined }, {}, 60)
  check("a large WSL_NOTIFY_GRACE_MS suppresses the toast", quiet.length === 0, `got ${quiet.length}`)
  delete process.env.WSL_NOTIFY_GRACE_MS
}

console.log("completion")
{
  const raised = await run([
    { id: "e1", type: "session.execution.started", data: { sessionID: SESSION } },
    { id: "e2", type: "session.execution.succeeded", data: { sessionID: SESSION } },
  ])
  check("finished session toasts once", raised.length === 1, `got ${raised.length}`)
  check("toast says the session finished", toastText(raised[0] ?? "").includes("Session finished"))
  check("toast carries the session title", toastText(raised[0] ?? "").includes("Test session"))
}
{
  const raised = await run([
    { id: "e1", type: "session.execution.succeeded", data: { sessionID: SESSION } },
    { id: "e2", type: "session.idle", data: { sessionID: SESSION } },
  ])
  check("succeeded plus legacy idle coalesces into one toast", raised.length === 1, `got ${raised.length}`)
}
{
  const raised = await run([
    { id: "e1", type: "session.execution.succeeded", data: { sessionID: SESSION } },
    { id: "e2", type: "session.execution.started", data: { sessionID: SESSION } },
    { id: "e3", type: "session.execution.succeeded", data: { sessionID: SESSION } },
  ])
  check("a second turn toasts again", raised.length === 2, `got ${raised.length}`)
}
{
  const subagent = "ses_child"
  const raised = await run(
    [{ id: "e1", type: "session.execution.succeeded", data: { sessionID: subagent } }],
    {},
    { [subagent]: { id: subagent, title: "Subagent", parentID: SESSION } },
  )
  check("subagent completion stays silent by default", raised.length === 0, `got ${raised.length}`)
}
{
  const subagent = "ses_child2"
  const raised = await run(
    [{ id: "e1", type: "session.execution.succeeded", data: { sessionID: subagent } }],
    { subagentComplete: true },
    { [subagent]: { id: subagent, title: "Subagent", parentID: SESSION } },
  )
  check("subagent completion toasts when enabled", raised.length === 1, `got ${raised.length}`)
  check("subagent toast is labelled", toastText(raised[0] ?? "").includes("Subagent finished"))
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

await rm(dir, { recursive: true, force: true })

console.log(failures === 0 ? "\nall checks passed" : `\n${failures} check(s) failed`)
process.exit(failures === 0 ? 0 : 1)
