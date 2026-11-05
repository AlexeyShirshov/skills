// Smoke test for `/clear`'s decision logic.
//
// Every branch the command can take is asserted against a fake host, so a
// regression in the archive/navigate order shows up here instead of as a
// vanished session in the terminal.
//
//   npm test         (node --experimental-strip-types test/smoke.mjs)
//   bun test/smoke.mjs

import {
  ARCHIVE_COMMAND_ID,
  CLEAR_COMMAND_ID,
  CLEAR_LAYER_PRIORITY,
  clearSession,
  createArchiveCommand,
  createClearCommand,
} from "../clear.ts"

let failures = 0

function check(name, condition, extra = "") {
  if (condition) {
    console.log(`  ok   ${name}`)
  } else {
    failures += 1
    console.log(`  FAIL ${name}${extra ? ` — ${extra}` : ""}`)
  }
}

function equal(name, actual, expected) {
  check(name, JSON.stringify(actual) === JSON.stringify(expected), `got ${JSON.stringify(actual)}`)
}

/** Fake plugin context recording every call the command makes. */
function host({ route = { type: "session", sessionID: "ses_current" }, options = {}, update, tabs } = {}) {
  const calls = { update: [], navigate: [], toasts: [], closeTab: [] }
  const context = {
    options,
    client: {
      session: {
        update: async (input) => {
          calls.update.push(input)
          if (update) await update(input)
        },
      },
    },
    ui: {
      router: {
        current: () => route,
        navigate: (destination) => calls.navigate.push(destination),
      },
      tabs:
        tabs === undefined
          ? {
              enabled: () => true,
              close: (sessionID) => {
                calls.closeTab.push(sessionID)
                return true
              },
            }
          : tabs,
      toast: {
        show: (options) => calls.toasts.push(options),
      },
    },
  }
  return { context, calls }
}

console.log("in a session")

{
  const { context, calls } = host()
  const outcome = await clearSession(context)
  equal("archives the active session", calls.update, [{ sessionID: "ses_current", archived: true }])
  equal("closes the archived tab", calls.closeTab, ["ses_current"])
  equal("lands on a fresh session", calls.navigate, [{ type: "home" }])
  equal("reports cleared", outcome, "cleared")
  equal("toasts the archive", calls.toasts.map((t) => [t.variant, t.message]), [["success", "Session archived"]])
}

console.log("archive only")

{
  const { context, calls } = host({ options: { newSession: false } })
  const outcome = await clearSession(context)
  equal("still archives", calls.update.length, 1)
  equal("keeps the tab", calls.closeTab, [])
  equal("stays put", calls.navigate, [])
  equal("reports archived", outcome, "archived")
}

console.log("archive failure")

{
  const { context, calls } = host({ update: () => Promise.reject(new Error("server down")) })
  const outcome = await clearSession(context)
  equal("reports failed", outcome, "failed")
  equal("keeps the tab", calls.closeTab, [])
  equal("does not navigate", calls.navigate, [])
  equal(
    "explains the failure",
    calls.toasts.map((t) => [t.variant, t.message]),
    [["error", "Could not archive the session: server down"]],
  )
}

console.log("not in a session")

{
  const { context, calls } = host({ route: { type: "home" } })
  const outcome = await clearSession(context)
  equal("reports skipped", outcome, "skipped")
  equal("does not archive", calls.update, [])
  equal("does not navigate", calls.navigate, [])
}

console.log("host without session tabs")

{
  const { context, calls } = host({ tabs: { enabled: () => false, close: () => false } })
  const outcome = await clearSession(context)
  equal("still clears", outcome, "cleared")
  equal("leaves tabs alone", calls.closeTab, [])
  equal("still lands on a fresh session", calls.navigate, [{ type: "home" }])
}

{
  const { context, calls } = host({
    tabs: {
      enabled: () => true,
      close: () => {
        throw new Error("no such tab")
      },
    },
  })
  const outcome = await clearSession(context)
  equal("survives a failing tab close", outcome, "cleared")
  equal("does not archive twice", calls.update.length, 1)
  equal("still lands on a fresh session", calls.navigate, [{ type: "home" }])
}

console.log("command shape")

{
  const command = createClearCommand(host().context)
  equal("id", command.id, CLEAR_COMMAND_ID)
  // Pinned: reusing the built-in id is what keeps `/clear` a single row in V2.
  equal("overrides the built-in command", command.id, "session.clear")
  check("layer outranks the built-in layer", CLEAR_LAYER_PRIORITY > 0)
  equal("slash name", command.slash, { name: "clear" })
  equal("palette entry", command.palette, true)
  check("enabled inside a session", command.enabled() === true)
  check("disabled outside a session", createClearCommand(host({ route: { type: "home" } }).context).enabled() === false)

  const { context, calls } = host()
  const resolved = await createClearCommand(context).run()
  equal("run archives once", calls.update.length, 1)
  equal("run resolves to nothing", resolved, undefined)
}

console.log("archive command")

{
  const command = createArchiveCommand(host().context)
  equal("id", command.id, ARCHIVE_COMMAND_ID)
  equal("its own slash name", command.slash, { name: "archive" })
  check("no second palette entry", command.palette === undefined)
  check("enabled inside a session", command.enabled() === true)
  check("disabled outside a session", createArchiveCommand(host({ route: { type: "home" } }).context).enabled() === false)

  const { context, calls } = host()
  await createArchiveCommand(context).run()
  equal("archives the same way", calls.update, [{ sessionID: "ses_current", archived: true }])
  equal("lands on a fresh session", calls.navigate, [{ type: "home" }])
}

console.log("")

if (failures > 0) {
  console.log(`${failures} check(s) failed`)
  process.exit(1)
}
console.log("all checks passed")
