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
const argvLog = join(dir, "argv.log")
// The startup line goes to `WSL_NOTIFY_DEBUG_LOG`, read when the module is first
// imported — point it at a temp file before any test imports the plugin.
const loadLog = join(dir, "loaded.log")
process.env.WSL_NOTIFY_DEBUG_LOG = loadLog

// Every argument goes to `argv.log`; the *last* one is the toast script itself
// (one argv element, no base64), so it is written to the toast log as a line.
await writeFile(
  fake,
  `#!/bin/sh\n{ for arg in "$@"; do printf '%s\\n' "$arg"; done; } >> '${argvLog}'\nfor arg in "$@"; do last="$arg"; done\nprintf '%s\\n' "$last" >> '${log}'\n`,
)
await chmod(fake, 0o755)

let failures = 0
// Criterion ids in assertion labels are what the plan asks CHECK to read, so the
// per-criterion verdict is printed only after every assertion of that id has run.
const criteria = new Map()
function check(name, condition, extra = "") {
  const criterion = /^(AC-\d+)/.exec(name)?.[1]
  if (criterion) {
    const stats = criteria.get(criterion) ?? { total: 0, failed: 0 }
    stats.total += 1
    if (!condition) stats.failed += 1
    criteria.set(criterion, stats)
  }
  if (condition) {
    console.log(`  ok   ${name}`)
  } else {
    failures += 1
    console.log(`  FAIL ${name}${extra ? ` — ${extra}` : ""}`)
  }
}

// The environment is process-wide, so every test restores what was there before
// it started — including "it was not there at all".
async function withEnv(name, value, fn) {
  const previous = process.env[name]
  if (value === undefined) delete process.env[name]
  else process.env[name] = value
  try {
    return await fn()
  } finally {
    if (previous === undefined) delete process.env[name]
    else process.env[name] = previous
  }
}

const EXCLUDE_ENV = "WSL_NOTIFY_EXCLUDE_SESSION_TITLES"

async function toasts() {
  const content = await readFile(log, "utf8").catch(() => "")
  return content.split("\n").filter(Boolean)
}

// Each toast is one invocation of the fake executable: the last argument is the
// PowerShell script itself, whose XML carries the title and the message.
function toastText(line) {
  return line
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
  await writeFile(argvLog, "")
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

// 1.18.x drives the plugin through the `server()` hooks. A tuple entry in the
// config reaches the plugin as `server(input, options)`; a bare specifier or local
// auto-discovery supplies none, so the module defaults and `WSL_NOTIFY_*` apply.
// Options are forwarded only when the caller supplies them, so the existing
// one- and two-argument calls keep the exact no-options invocation.
async function runV1(events, gap = 10, options = undefined) {
  await writeFile(log, "")
  await writeFile(argvLog, "")
  resetState()

  const module = await import("../index.js")
  const hooks = options === undefined ? await module.default.server() : await module.default.server({}, options)
  for (const event of events) {
    await hooks.event({ event })
    await sleep(gap)
  }
  await sleep(60)
  return toasts()
}

const SESSION = "ses_test"
const sessionCreated = (sessionID, parentID) => ({
  id: `evt_created_${sessionID}`,
  type: "session.created",
  data: parentID ? { sessionID, parentID, title: `Title of ${sessionID}` } : { sessionID, title: `Title of ${sessionID}` },
})
// Same announcement with a title of the test's choosing — the filter matches the
// real title, so the default `Title of …` is not enough to exercise it.
const sessionTitled = (sessionID, title) => ({
  id: `evt_created_${sessionID}`,
  type: "session.created",
  data: { sessionID, title },
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

console.log("startup line")
{
  // Registration must leave a trace even without WSL_NOTIFY_DEBUG: that is what
  // separates "the plugin never loaded" from "it loaded and stayed quiet".
  const module = await import("../index.js")
  await module.default.server()
  await sleep(50)
  const content = await readFile(loadLog, "utf8").catch(() => "")
  check("registration writes a loaded line", /loaded path=v1/.test(content), content.trim().slice(0, 90))
}

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
console.log("1.18.x server() limits")
{
  // The V1 path keeps the same defaults as everywhere else: an ask waits out the
  // grace window, and an answer inside it cancels the toast.
  const raised = await runV1([
    { id: "v1_def_ask", type: "permission.asked", properties: { id: "per_v1", sessionID: SESSION, permission: "bash" } },
  ])
  check("an ask waits out the grace window on the V1 path", raised.length === 0, `got ${raised.length}`)
}
{
  // `WSL_NOTIFY_GRACE_MS=0` makes it immediate — the environment is the override,
  // as it was for the old standalone V1 file (which had no window at all).
  process.env.WSL_NOTIFY_GRACE_MS = "0"
  const raised = await runV1([
    { id: "v1_env_ask", type: "permission.asked", properties: { id: "per_v1b", sessionID: SESSION, permission: "bash" } },
  ])
  delete process.env.WSL_NOTIFY_GRACE_MS
  check("WSL_NOTIFY_GRACE_MS=0 makes the V1 ask immediate", raised.length === 1, `got ${raised.length}`)
}
{
  // A short turn is filtered by the same `minTurnMs` default on this path too.
  const raised = await runV1([
    { id: "v1_def_user", type: "message.updated", properties: { sessionID: SESSION, info: { id: "msg_s1", role: "user" } } },
    { id: "v1_def_idle", type: "session.idle", properties: { sessionID: SESSION } },
  ])
  check("a short turn is filtered on the V1 path too", raised.length === 0, `got ${raised.length}`)
}

console.log("AC-1 excluded titles: complete and error events")
{
  const sessionID = "ses_ac1"
  const created = sessionTitled(sessionID, "Background research notes")
  const events = [
    ["session.execution.succeeded", { id: "ac1_succeeded", type: "session.execution.succeeded", data: { sessionID } }],
    ["session.idle", { id: "ac1_idle", type: "session.idle", data: { sessionID } }],
    [
      "session.execution.failed",
      { id: "ac1_failed", type: "session.execution.failed", data: { sessionID, error: { message: "boom" } } },
    ],
    ["session.error", { id: "ac1_error", type: "session.error", data: { sessionID, error: { message: "boom" } } }],
  ]

  for (const [name, event] of events) {
    const raised = await run([created, event], { excludeSessionTitles: ["Background"] })
    check(`AC-1 a matching title suppresses ${name}`, raised.length === 0, `got ${raised.length}`)
  }
  for (const [name, event] of events) {
    const raised = await run([created, event], { excludeSessionTitles: ["Nope"] })
    check(`AC-1 a non-matching title still notifies ${name}`, raised.length === 1, `got ${raised.length}`)
  }

  {
    const raised = await run([created, events[0][1]], { excludeSessionTitles: ["Nope", "research"] })
    check("AC-1 a later list element matches (OR)", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await run([created, events[0][1]], { excludeSessionTitles: ["round res"] })
    check("AC-1 a substring inside a longer title matches", raised.length === 0, `got ${raised.length}`)
  }
  {
    // Case is significant: "background" is not "Background".
    const raised = await run([created, events[0][1]], { excludeSessionTitles: ["background"] })
    check("AC-1 matching is case-sensitive", raised.length === 1, `got ${raised.length}`)
  }
  {
    // A regex-looking entry is a literal string, both ways round: it matches the
    // literal text and it does not match what the expression would.
    const literal = sessionTitled("ses_ac1_literal", "Work.* in progress")
    const raised = await run(
      [literal, { id: "ac1_literal", type: "session.execution.succeeded", data: { sessionID: "ses_ac1_literal" } }],
      { excludeSessionTitles: ["Work.*"] },
    )
    check("AC-1 regex-looking text matches literally", raised.length === 0, `got ${raised.length}`)
  }
  {
    const plain = sessionTitled("ses_ac1_plain", "Working on docs")
    const raised = await run(
      [plain, { id: "ac1_plain", type: "session.execution.succeeded", data: { sessionID: "ses_ac1_plain" } }],
      { excludeSessionTitles: ["Work.*"] },
    )
    check("AC-1 regex-looking text does not overmatch", raised.length === 1, `got ${raised.length}`)
  }
}

console.log("AC-2 title source, non-completion events, dedupe")
{
  // No cached title: the rendered fallback is "opencode", but it is not a title
  // the filter may match — a session with an unknown title still notifies.
  {
    const raised = await run(
      [{ id: "ac2_unknown", type: "session.execution.succeeded", data: { sessionID: "ses_ac2_unknown" } }],
      { excludeSessionTitles: ["opencode"] },
    )
    check("AC-2 a missing title is not suppressed by the fallback", raised.length === 1, `got ${raised.length}`)
    check("AC-2 the fallback title is still rendered", toastText(raised[0] ?? "").includes("opencode"))
  }
  {
    // The session id contains the configured text; the title does not.
    const created = sessionTitled("ses_Background_42", "Plain title")
    const raised = await run(
      [created, { id: "ac2_id", type: "session.execution.succeeded", data: { sessionID: "ses_Background_42" } }],
      { excludeSessionTitles: ["Background"] },
    )
    check("AC-2 a match only in the session id does not count", raised.length === 1, `got ${raised.length}`)
  }
  {
    // Only the error text contains the configured string.
    const created = sessionTitled("ses_ac2_err", "Plain title")
    const raised = await run(
      [
        created,
        {
          id: "ac2_err",
          type: "session.execution.failed",
          data: { sessionID: "ses_ac2_err", error: { message: "Background job failed" } },
        },
      ],
      { excludeSessionTitles: ["Background"] },
    )
    check("AC-2 a match only in the error message does not count", raised.length === 1, `got ${raised.length}`)
  }

  {
    const created = sessionTitled(SESSION, "Background research notes")
    const nonCompletion = [
      ["permission.asked", permissionAsked("per_ac2")],
      [
        "question.asked",
        {
          id: "ac2_question",
          type: "question.asked",
          properties: { sessionID: SESSION, questions: [{ header: "Pick", question: "Which?" }] },
        },
      ],
      [
        "form.created",
        {
          id: "ac2_form",
          type: "form.created",
          data: { form: { id: "frm_ac2", title: "Pick one", fields: [{ title: "Which?" }] } },
        },
      ],
    ]
    for (const [name, event] of nonCompletion) {
      const raised = await run([created, event], { excludeSessionTitles: ["Background"] })
      check(`AC-2 a matching title does not suppress ${name}`, raised.length === 1, `got ${raised.length}`)
    }
  }

  {
    // A skipped event never reaches dedupe: after the rename the same key toasts.
    const created = sessionTitled(SESSION, "Background research notes")
    const renamed = { id: "ac2_renamed", type: "session.updated", data: { sessionID: SESSION, title: "Visible notes" } }
    const raised = await run(
      [
        created,
        { id: "ac2_skip", type: "session.execution.succeeded", data: { sessionID: SESSION } },
        renamed,
        { id: "ac2_after", type: "session.execution.succeeded", data: { sessionID: SESSION } },
      ],
      { excludeSessionTitles: ["Background"] },
    )
    check("AC-2 a skipped event does not consume the dedupe key", raised.length === 1, `got ${raised.length}`)
  }
  {
    // An ordinary duplicate is still deduped.
    const created = sessionTitled(SESSION, "Visible notes")
    const raised = await run([
      created,
      { id: "ac2_first", type: "session.execution.succeeded", data: { sessionID: SESSION } },
      { id: "ac2_second", type: "session.execution.succeeded", data: { sessionID: SESSION } },
    ])
    check("AC-2 a sent duplicate is still deduped", raised.length === 1, `got ${raised.length}`)
  }
}

console.log("AC-3 environment filter")
{
  const v2Events = (id = "ac3") => [
    sessionTitled(SESSION, "Background research"),
    { id, type: "session.execution.succeeded", data: { sessionID: SESSION } },
  ]
  const v1Events = (id = "ac3") => [
    sessionTitled(SESSION, "Research, notes weekly"),
    { id, type: "session.idle", data: { sessionID: SESSION } },
  ]

  {
    const raised = await withEnv(EXCLUDE_ENV, JSON.stringify(["Background"]), () => run(v2Events()))
    check("AC-3 env filters V2 completions", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, JSON.stringify(["Background"]), () =>
      run([
        sessionTitled(SESSION, "Background research"),
        {
          id: "ac3_error",
          type: "session.execution.failed",
          data: { sessionID: SESSION, error: { message: "boom" } },
        },
      ]),
    )
    check("AC-3 env filters V2 errors", raised.length === 0, `got ${raised.length}`)
  }
  {
    // A comma inside the title is exactly why the env format is JSON.
    const raised = await withEnv(EXCLUDE_ENV, JSON.stringify(["Research, notes"]), () => runV1(v1Events()))
    check("AC-3 env filters V1, including a title with a comma", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, JSON.stringify(["Other"]), () => runV1(v1Events("ac3_v1_other")))
    check("AC-3 a non-matching env list still notifies on V1", raised.length === 1, `got ${raised.length}`)
  }
  {
    // The environment is read per event, not captured at startup: the first
    // completion is filtered, the value changes, the later one is not.
    function* changing() {
      yield sessionTitled("ses_ac3_first", "Background one")
      yield { id: "ac3_first", type: "session.execution.succeeded", data: { sessionID: "ses_ac3_first" } }
      process.env[EXCLUDE_ENV] = JSON.stringify(["Other"])
      yield sessionTitled("ses_ac3_second", "Background two")
      yield { id: "ac3_second", type: "session.execution.succeeded", data: { sessionID: "ses_ac3_second" } }
    }
    const raised = await withEnv(EXCLUDE_ENV, JSON.stringify(["Background"]), () => run(changing()))
    check("AC-3 an env change is observed on a later event", raised.length === 1, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, undefined, () => run(v2Events("ac3_unset")))
    check("AC-3 an unset env leaves normal behaviour", raised.length === 1, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, "", () => runV1(v1Events("ac3_empty")))
    check("AC-3 an empty env leaves normal behaviour", raised.length === 1, `got ${raised.length}`)
  }
}

console.log("AC-4 option and environment precedence")
{
  const env = JSON.stringify(["Background"])
  const v2 = (options) =>
    run([sessionTitled(SESSION, "Background research"), { id: "ac4", type: "session.execution.succeeded", data: { sessionID: SESSION } }], options)
  const v1 = (options) =>
    runV1([sessionTitled(SESSION, "Background research"), { id: "ac4", type: "session.idle", data: { sessionID: SESSION } }], 10, options)

  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v2({ excludeSessionTitles: ["Other"] }))
    check("AC-4 a conflicting option wins over the env on V2", raised.length === 1, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v2({ excludeSessionTitles: ["Background"] }))
    check("AC-4 a matching option still suppresses on V2", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v2({ excludeSessionTitles: [] }))
    check("AC-4 an explicit empty option overrides the env", raised.length === 1, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v2({ excludeSessionTitles: undefined }))
    check("AC-4 an undefined option falls back to the env", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v2({ excludeSessionTitles: null }))
    check("AC-4 a null option falls back to the env", raised.length === 0, `got ${raised.length}`)
  }
  for (const invalid of ["x", 42, {}]) {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v2({ excludeSessionTitles: invalid }))
    check(
      `AC-4 an invalid option (${JSON.stringify(invalid)}) overrides the env and fails open`,
      raised.length === 1,
      `got ${raised.length}`,
    )
  }

  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v1({ excludeSessionTitles: ["Other"] }))
    check("AC-4 a conflicting option wins over the env on V1", raised.length === 1, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v1({ excludeSessionTitles: ["Background"] }))
    check("AC-4 a matching V1 option suppresses", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v1({ excludeSessionTitles: [] }))
    check("AC-4 an explicit empty V1 option overrides the env", raised.length === 1, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v1(undefined))
    check("AC-4 undefined V1 options fall back to the env", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v1(null))
    check("AC-4 null V1 options fall back to the env", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, env, () => v1({ excludeSessionTitles: "x" }))
    check("AC-4 an invalid V1 option overrides the env and fails open", raised.length === 1, `got ${raised.length}`)
  }
}

console.log("AC-5 invalid configuration fails open")
{
  const events = () => [
    sessionTitled(SESSION, "Background research"),
    { id: "ac5", type: "session.execution.succeeded", data: { sessionID: SESSION } },
  ]
  // A throw inside the handler is swallowed and produces no toast as well, so
  // "one toast" is both the no-throw and the fail-open assertion.
  for (const [label, value] of [
    ["a string", "x"],
    ["a number", 42],
    ["an object", {}],
    ["an empty string", ""],
    ["an array holding only empty strings", ["", ""]],
    ["an array of non-strings", [1, true, null, {}]],
  ]) {
    const raised = await withEnv(EXCLUDE_ENV, undefined, () => run(events(), { excludeSessionTitles: value }))
    check(`AC-5 ${label} option does not throw and suppresses nothing`, raised.length === 1, `got ${raised.length}`)
  }
  {
    // Valid entries in a mixed array still take effect.
    const raised = await withEnv(EXCLUDE_ENV, undefined, () =>
      run(events(), { excludeSessionTitles: ["", 42, "Background", null] }),
    )
    check("AC-5 a mixed option array keeps its valid entries", raised.length === 0, `got ${raised.length}`)
  }
  for (const [label, value] of [
    ["malformed JSON", "not json"],
    ["a JSON object", '{"list":["Background"]}'],
    ["a JSON string", '"Background"'],
    ["a JSON number", "42"],
    ["an empty-string array", '[""]'],
    ["whitespace only", "   "],
  ]) {
    const raised = await withEnv(EXCLUDE_ENV, value, () => runV1(events("ac5_env")))
    check(`AC-5 ${label} in the env does not throw and suppresses nothing`, raised.length === 1, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, '["", 42, "Background", null]', () => runV1(events("ac5_mixed")))
    check("AC-5 a mixed env array keeps its valid entries", raised.length === 0, `got ${raised.length}`)
  }
}

console.log("AC-6 V1 forwarded options")
{
  const events = () => [
    sessionTitled(SESSION, "Background research"),
    { id: "ac6_idle", type: "session.idle", data: { sessionID: SESSION } },
  ]

  {
    const raised = await withEnv(EXCLUDE_ENV, undefined, () => runV1(events(), 10, { excludeSessionTitles: ["Background"] }))
    check("AC-6 tuple options reach the V1 filter and suppress", raised.length === 0, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, undefined, () => runV1(events()))
    check("AC-6 server() with no arguments keeps prior behaviour", raised.length === 1, `got ${raised.length}`)
  }
  {
    const raised = await withEnv(EXCLUDE_ENV, undefined, () => runV1(events(), 10, undefined))
    check("AC-6 explicit undefined options keep prior behaviour", raised.length === 1, `got ${raised.length}`)
  }
  {
    // The host's tuple call, made directly: it must be accepted.
    const module = await import("../index.js")
    let blew = false
    try {
      await module.default.server({}, { excludeSessionTitles: ["Background"] })
    } catch {
      blew = true
    }
    check("AC-6 server(input, options) accepts a tuple call", !blew)
  }
}

console.log("invocation")
{
  // The script must reach powershell as one `-Command` argument: `-EncodedCommand`
  // doubles it through base64 UTF-16LE and a host that caps an argument at ~2 KB
  // then fails the spawn with EINVAL (exit 1, nothing on screen).
  const raised = await run([permissionAsked("per_invocation")])
  const args = (await readFile(argvLog, "utf8").catch(() => "")).split("\n").filter(Boolean)
  check("the toast script is passed after -Command", args.at(-2) === "-Command", args.slice(0, -1).join(" "))
  check("-EncodedCommand is never used", !args.includes("-EncodedCommand"))
  check("the script travels unencoded", (args.at(-1) ?? "").startsWith("$ErrorActionPreference="))
  check("the toast still goes out", raised.length === 1, `got ${raised.length}`)
}

await rm(dir, { recursive: true, force: true })

for (const [criterion, stats] of criteria) {
  if (stats.failed === 0) console.log(`PASS ${criterion} — ${stats.total} assertions`)
  else console.log(`FAIL ${criterion} — ${stats.failed}/${stats.total} assertions failed`)
}

console.log(failures === 0 ? "\nall checks passed" : `\n${failures} check(s) failed`)
process.exit(failures === 0 ? 0 : 1)
