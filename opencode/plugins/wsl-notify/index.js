// Windows toast notifications for OpenCode (V1 and V2).
//
// One entrypoint serves both generations: V2 reads `id`/`setup()` and delivers
// events through `ctx.event.subscribe()`; V1 calls `server()` and uses the
// returned hooks. V2 replaced the V1 `question.asked` event with `form.created`,
// so both shapes are handled.
//
// V2 also loads the same plugin once per location activation: several instances
// per server process, each with its own module graph, all subscribed to the same
// event stream. Shared state therefore lives on `globalThis`, so one request
// produces exactly one toast (V1 sent one as well).
//
// There is no Bun `$` helper in V2 and no dependency is needed: the plugin is a
// plain object, so it works in both generations without `@opencode/plugin`.

import { spawn } from "node:child_process"
import { existsSync, readFileSync } from "node:fs"
import { appendFile } from "node:fs/promises"
import { randomUUID } from "node:crypto"
import { delimiter, join } from "node:path"
import { tmpdir } from "node:os"

const APP_ID = "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe"

const DEFAULTS = {
  maxTitle: 60,
  maxMessage: 240,
  // A permission that is answered inside this window never reaches the desktop.
  // See the README: with `session.permissions: "autoaccept"` the TUI answers at
  // once, and only the events would tell you otherwise.
  graceMs: 500,
  // Subagent completions are noise by default: the parent session reports the
  // turn that spawned them.
  subagentComplete: false,
  sound: {
    permission: "Notification.IM",
    question: "Notification.Default",
    complete: "Notification.Default",
    error: "Notification.Reminder",
  },
}

// Windows installations on a DrvFs/9p mount, and PowerShell 7 next to it.
const POWERSHELL_RELATIVE = [
  "Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
  "WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe",
  "Program Files/PowerShell/7/pwsh.exe",
]

const POWERSHELL_NAMES = ["powershell.exe", "pwsh.exe", "powershell", "pwsh"]

const COMPLETE_EVENTS = new Set(["session.execution.succeeded", "session.idle"])
const ERROR_EVENTS = new Set(["session.execution.failed"])
const SESSION_START_EVENTS = new Set(["session.execution.started"])

const LOOKUP_TIMEOUT_MS = 2000

// Diagnostics: `WSL_NOTIFY_DEBUG=1` in the environment of the opencode process
// writes every decision (toast/skip) to WSL_NOTIFY_DEBUG_LOG
// (default `$TMPDIR/wsl-notify.log`).
const INSTANCE = randomUUID().slice(0, 8)
const DEBUG_LOG = process.env.WSL_NOTIFY_DEBUG_LOG ?? join(tmpdir(), "wsl-notify.log")

function debug(line) {
  if (process.env.WSL_NOTIFY_DEBUG !== "1") return
  void appendFile(DEBUG_LOG, `${new Date().toISOString()} ${INSTANCE} ${line}\n`).catch(() => {})
}

// Dedupe: one toast per request. The key is the request id (form/permission) or
// the session plus turn (completion), never the event id, because V2 delivers one
// event to several plugin instances, re-emits `permission.asked` for a pending
// request, and can report one finished turn as both `session.execution.succeeded`
// and the legacy `session.idle`.
const STATE_KEY = Symbol.for("opencode.wsl-notify.state")
const state = (globalThis[STATE_KEY] ??= {
  seen: new Set(),
  pending: new Map(),
  warned: new Set(),
  resolved: false,
  powershell: undefined,
})
const MAX_SEEN = 512

function warnOnce(key, message) {
  if (state.warned.has(key)) return
  state.warned.add(key)
  console.error(message)
}

function findOnPath(name) {
  const dirs = (process.env.PATH ?? "").split(delimiter).filter(Boolean)
  const names = process.platform === "win32" ? [name] : [`${name}.exe`, name]
  for (const dir of dirs) {
    for (const candidate of names) {
      const full = join(dir, candidate)
      if (existsSync(full)) return full
    }
  }

  return undefined
}

function windowsMounts() {
  const mounts = []
  try {
    for (const line of readFileSync("/proc/mounts", "utf8").split("\n")) {
      const [mount, , type] = line.split(/\s+/)
      if (!mount || !/^\/mnt\/[a-z]$/i.test(mount)) continue
      if (type === "drvfs" || type === "9p" || type === "cifs") mounts.push(mount)
    }
  } catch {
    // Not Linux: no DrvFs mounts to scan.
  }

  if (mounts.length === 0 && existsSync("/mnt/c")) mounts.push("/mnt/c")
  return mounts
}

// Resolution order: explicit option, `WSL_NOTIFY_POWERSHELL`, PATH (native
// Windows and WSL interop put powershell.exe there), then the Windows drive
// mounts of a WSL host.
export function resolvePowerShell(options) {
  const explicit = options?.powershell ?? process.env.WSL_NOTIFY_POWERSHELL
  if (typeof explicit === "string" && explicit.length > 0) {
    if (existsSync(explicit)) return explicit
    const onPath = findOnPath(explicit)
    if (onPath) return onPath
    warnOnce("explicit", `[wsl-notify] powershell not found at "${explicit}", falling back to discovery`)
  }

  for (const name of POWERSHELL_NAMES) {
    const found = findOnPath(name)
    if (found) return found
  }

  for (const mount of windowsMounts()) {
    for (const relative of POWERSHELL_RELATIVE) {
      const full = join(mount, relative)
      if (existsSync(full)) return full
    }
  }

  return undefined
}

function powershell(options) {
  if (state.resolved && state.powershell) return state.powershell

  if (!state.resolved) {
    state.powershell = resolvePowerShell(options)
    state.resolved = true
  }

  if (!state.powershell) {
    warnOnce(
      "missing",
      "[wsl-notify] powershell.exe not found (set WSL_NOTIFY_POWERSHELL or the plugin's `powershell` option); notifications are skipped",
    )
  }

  return state.powershell
}

function sessionIDOf(event) {
  return event?.data?.sessionID ?? event?.properties?.sessionID
}

// Classify the event and build its dedupe key. `undefined` means "not ours".
function classify(event) {
  switch (event?.type) {
    case "permission.asked": {
      const id = event.data?.id ?? event.data?.requestID ?? event.properties?.id ?? event.properties?.requestID
      const key = id === undefined || id === null ? (event.id ? `event:${event.id}` : undefined) : `permission:${id}`
      return { kind: "permission", key, sessionID: sessionIDOf(event) }
    }

    case "form.created": {
      const id = event.data?.form?.id
      const key = id === undefined || id === null ? (event.id ? `event:${event.id}` : undefined) : `form:${id}`
      return { kind: "question", key, sessionID: sessionIDOf(event) }
    }

    case "question.asked": {
      const first = event.properties?.questions?.[0]
      const key =
        first?.question === undefined
          ? event.id && `event:${event.id}`
          : `question:${sessionIDOf(event) ?? ""}:${first.question}`
      return { kind: "question", key, sessionID: sessionIDOf(event) }
    }

    default: {
      const sessionID = sessionIDOf(event)
      if (COMPLETE_EVENTS.has(event?.type)) return { kind: "complete", key: `done:${sessionID}`, sessionID }
      if (ERROR_EVENTS.has(event?.type)) return { kind: "error", key: `failed:${sessionID}`, sessionID }
      return undefined
    }
  }
}

function cancelPending(key) {
  const timer = state.pending.get(key)
  if (timer === undefined) return
  clearTimeout(timer)
  state.pending.delete(key)
}

function forgetKey(key) {
  if (!key) return
  cancelPending(key)
  state.seen.delete(key)
}

function forget(event) {
  // A replied or cancelled request is no longer pending: drop its key so the
  // grace timer stops and nothing is toasted.
  if (event?.type === "permission.replied") {
    const id = event.data?.requestID ?? event.data?.id ?? event.properties?.requestID ?? event.properties?.id
    forgetKey(id === undefined || id === null ? undefined : `permission:${id}`)
  }

  if (event?.type === "form.replied" || event?.type === "form.cancelled") {
    const id = event.data?.id ?? event.data?.form?.id
    forgetKey(id === undefined || id === null ? undefined : `form:${id}`)
  }

  // A new execution starts the next turn: allow the next completion to toast.
  if (SESSION_START_EVENTS.has(event?.type)) {
    const sessionID = sessionIDOf(event)
    forgetKey(`done:${sessionID}`)
    forgetKey(`failed:${sessionID}`)
  }
}

function firstTime(key) {
  if (!key) return true
  if (state.seen.has(key)) return false

  state.seen.add(key)
  if (state.seen.size > MAX_SEEN) {
    for (const oldest of state.seen) {
      state.seen.delete(oldest)
      if (state.seen.size <= MAX_SEEN - 64) break
    }
  }

  return true
}

const psQuote = (value) => `'${String(value).replace(/'/g, "''")}'`

const xmlEscape = (value) =>
  String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;")

function buildScript(title, message, sound) {
  const xml =
    '<toast><visual><binding template="ToastGeneric">' +
    `<text>${xmlEscape(title)}</text>` +
    `<text>${xmlEscape(message)}</text>` +
    "</binding></visual>" +
    `<audio src="ms-winsoundevent:${sound}"/>` +
    "</toast>"
  return [
    "$ErrorActionPreference='Stop'",
    "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null",
    "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null",
    "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument",
    `$xml.LoadXml(${psQuote(xml)})`,
    "$toast = New-Object Windows.UI.Notifications.ToastNotification $xml",
    `[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(${psQuote(APP_ID)}).Show($toast)`,
  ].join("; ")
}

// V2 describes the request as a form, V1 as a list of questions. Normalize both.
function formOf(event) {
  if (event?.type === "form.created") return event.data?.form

  if (event?.type === "question.asked") {
    const questions = Array.isArray(event.properties?.questions) ? event.properties.questions : []
    return {
      title: questions[0]?.header,
      fields: questions.map((question) => ({ title: question?.question })),
    }
  }

  return undefined
}

function numberFromEnv(name) {
  const raw = process.env[name]
  if (raw === undefined || raw === "") return undefined
  const value = Number(raw)
  return Number.isFinite(value) ? value : undefined
}

function limits(options) {
  // Option wins, then the environment: a locally discovered plugin file has no
  // options, so the environment is the only knob there.
  const grace = options?.graceMs ?? numberFromEnv("WSL_NOTIFY_GRACE_MS")

  return {
    maxTitle: Number.isFinite(options?.maxTitle) ? options.maxTitle : DEFAULTS.maxTitle,
    maxMessage: Number.isFinite(options?.maxMessage) ? options.maxMessage : DEFAULTS.maxMessage,
    graceMs: Number.isFinite(grace) ? Math.max(0, grace) : DEFAULTS.graceMs,
    subagentComplete: options?.subagentComplete === true,
    sound: { ...DEFAULTS.sound, ...(options?.sound ?? {}) },
  }
}

function render(classified, event, session, options) {
  const { maxTitle, maxMessage, graceMs, subagentComplete, sound } = limits(options)
  const sessionTitle = session?.title ? String(session.title) : undefined
  const title = (sessionTitle || "opencode").slice(0, maxTitle)

  switch (classified.kind) {
    case "permission":
      return { title: "opencode", message: "Permission needs input", sound: sound.permission, delayMs: graceMs }

    case "question": {
      const form = formOf(event)
      if (!form) return undefined
      const fields = Array.isArray(form.fields) ? form.fields : []
      const first = fields[0] ?? {}
      const candidate = first.title || first.description || form.title || "Question needs input"
      let message = String(candidate)
      if (fields.length > 1) message += ` (+${fields.length - 1})`
      return {
        title: String(form.title || "opencode").slice(0, maxTitle),
        message: message.slice(0, maxMessage),
        sound: sound.question,
      }
    }

    case "complete":
      return {
        title,
        message: session?.parentID !== undefined && subagentComplete ? "Subagent finished" : "Session finished",
        sound: sound.complete,
      }

    case "error": {
      const detail = event.data?.error?.message ?? event.properties?.error?.message
      return {
        title,
        message: (detail ? `Error: ${detail}` : "Session failed").slice(0, maxMessage),
        sound: sound.error,
      }
    }

    default:
      return undefined
  }
}

// Resolve the session behind an event. V1 has no such call, and V1 does not emit
// the execution events that need it.
async function lookupSession(ctx, sessionID) {
  if (!sessionID || typeof ctx?.session?.get !== "function") return undefined

  let timer
  try {
    return await Promise.race([
      ctx.session.get({ sessionID }),
      new Promise((resolve) => {
        timer = setTimeout(() => resolve(undefined), LOOKUP_TIMEOUT_MS)
      }),
    ])
  } catch {
    return undefined
  } finally {
    if (timer !== undefined) clearTimeout(timer)
  }
}

function toast(info, options) {
  const executable = powershell(options)
  if (!executable) return

  const encoded = Buffer.from(buildScript(info.title, info.message, info.sound), "utf16le").toString("base64")
  const child = spawn(
    executable,
    ["-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-EncodedCommand", encoded],
    { stdio: "ignore" },
  )
  child.on("error", (error) => console.error(`[wsl-notify] "${executable}" failed: ${error.message}`))
}

function schedule(key, info, options) {
  const delayMs = Number.isFinite(info.delayMs) ? info.delayMs : 0
  if (delayMs <= 0) {
    debug(`toast ${key}`)
    toast(info, options)
    return
  }

  const timer = setTimeout(() => {
    state.pending.delete(key)
    debug(`toast-delayed ${key} after=${delayMs}ms`)
    toast(info, options)
  }, delayMs)
  timer.unref?.()
  state.pending.set(key, timer)
  debug(`delayed ${key} after=${delayMs}ms`)
}

async function handle(event, options, ctx) {
  forget(event)

  const classified = classify(event)
  if (!classified) return

  const needsSession = classified.kind === "complete" || classified.kind === "error"
  const session = needsSession ? await lookupSession(ctx, classified.sessionID) : undefined

  if (needsSession && session?.parentID !== undefined && !limits(options).subagentComplete) {
    debug(`skip-subagent ${event?.type} session=${classified.sessionID}`)
    return
  }

  const info = render(classified, event, session, options)
  if (!info) return

  if (!firstTime(classified.key)) {
    debug(`skip ${classified.kind} key=${classified.key} event.id=${event?.id}`)
    return
  }

  schedule(classified.key, info, options)
}

export default {
  id: "wsl-notify",

  // V2: events arrive through the server event stream.
  setup(ctx) {
    const options = ctx?.options ?? {}
    const controller = new AbortController()

    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
          try {
            await handle(event, options, ctx)
          } catch (error) {
            console.error(`[wsl-notify] handler failed: ${error?.message ?? error}`)
          }
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error(`[wsl-notify] event stream ended: ${error?.message ?? error}`)
        }
      }
    })()

    return () => controller.abort()
  },

  // V1: the server calls this and uses the returned hooks. V1 loads the plugin
  // once per process, and its `session.idle` is the completion event.
  async server() {
    return {
      event: async ({ event }) => {
        try {
          await handle(event, {}, undefined)
        } catch (error) {
          console.error(`[wsl-notify] handler failed: ${error?.message ?? error}`)
        }
      },
    }
  },
}
