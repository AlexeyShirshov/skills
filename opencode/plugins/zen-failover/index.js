// zen-failover — when a subscription provider's usage limit is hit, move the
// whole server off it: every agent and the default model that point at that
// provider switch to its pay-as-you-go fallback, the session that hit the
// limit is switched too, and the decision persists until the monthly reset.
//
// Rules (env ZEN_FAILOVER_RULES, "source=fallback;..."):
//   opencode-go=deepseek/deepseek-flash   Go plan -> direct DeepSeek
//   openai=opencode/<id>                  ChatGPT Plus/Pro -> Console twin
// `<id>` keeps the model id (minus a `-fast` suffix).
//
// Trigger: two limit errors from the same source within five minutes, or one
// 402. A single transient 429 is retried without switching.
//
// Sources listed in ZEN_FAILOVER_QUOTA_ONLY (default: openai) must name an
// exhausted quota in the error text: a subscription answers a transient
// per-minute 429 with the same status, and switching the whole server off the
// plan for a week on a burst limit is exactly the false positive we had on
// 2026-10-20 (ChatGPT at 95%/79% remaining, Sol moved to Console).
//
// Once degraded, the plugin does not wait for the cooldown: every
// ZEN_FAILOVER_PROBE_MS (default 60s, 0 disables) it asks the source directly —
// a throwaway session on the source model, one minimal generation — and
// restores the agents/sessions as soon as that probe succeeds. The cooldown in
// `resetAt` stays as a backstop.
//
// Env:
//   ZEN_FAILOVER_RULES         source=fallback rules (see above)
//   ZEN_FAILOVER_MAP           "src/model=dst/model,..." per-model override
//   ZEN_FAILOVER_QUOTA_ONLY    sources where a bare 429 is not a limit (openai)
//   ZEN_FAILOVER_PROBE_MS      availability probe interval, 0 disables (60000)
//   ZEN_FAILOVER_PROBE_ON_START  "0" skips the probe at process start (on)
//   ZEN_FAILOVER_PROBE_START_WAIT_MS  max startup wait for that probe (5000)
//   ZEN_FAILOVER_RESET_<SRC>   cooldown, "7d" | "5h" | "month" (default 7d)
//   ZEN_FAILOVER_RESET_AT      ISO timestamp or epoch ms (tests; overrides all)
//   ZEN_FAILOVER_MIN_HITS      limit errors before switching  (2)
//   ZEN_FAILOVER_WINDOW_MS     window for those errors        (300000)
//   ZEN_FAILOVER_LOG           debug log path                (/tmp/opencode/zen-failover.log)
//   ZEN_FAILOVER_DEBUG         "1" to log every retry event

import { appendFileSync } from "node:fs"

const RULES_TEXT =
  process.env.ZEN_FAILOVER_RULES ??
  ["opencode-go=deepseek/deepseek-flash", "openai=opencode/<id>"].join(";")
const RULES = parseRules(RULES_TEXT)
const MODEL_MAP = parseMap(
  process.env.ZEN_FAILOVER_MAP ??
    [
      "opencode-go/gemini-4-argon-contributor=opencode/gemini-4-argon",
      "opencode-go/kimi-k3=moonshotai/kimi-k3",
    ].join(","),
)
const RESET_AT_ENV = process.env.ZEN_FAILOVER_RESET_AT
const LOG = process.env.ZEN_FAILOVER_LOG ?? "/tmp/opencode/zen-failover.log"
const DEBUG = process.env.ZEN_FAILOVER_DEBUG === "1"
const MIN_HITS = Number(process.env.ZEN_FAILOVER_MIN_HITS ?? 2)
const HIT_WINDOW = Number(process.env.ZEN_FAILOVER_WINDOW_MS ?? 5 * 60 * 1000)
const QUOTA_ONLY = new Set(
  String(process.env.ZEN_FAILOVER_QUOTA_ONLY ?? "openai")
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean),
)
const QUOTA_TEXT =
  /usage.?limit|quota|insufficient|weekly limit|plan limit|subscription limit|exceeded your/i
const RATE_TEXT = /rate.?limit|limit reached|too many requests|budget|exceeded/i
const PROBE_MS = Number(process.env.ZEN_FAILOVER_PROBE_MS ?? 60 * 1000)
const PROBE_ON_START = process.env.ZEN_FAILOVER_PROBE_ON_START !== "0"
const PROBE_START_WAIT_MS = Number(process.env.ZEN_FAILOVER_PROBE_START_WAIT_MS ?? 5000)
const PROBE_PROMPT = "Reply with the single word OK."
const STORAGE_KEY = "zen-failover"
const STORAGE_VERSION = 2

let registrations = null
let applying = null
let restoreRegistration = null
let probeTimer = null
let probeInFlight = false
const recentHits = new Map()

function log(line) {
  try {
    appendFileSync(LOG, `${new Date().toISOString()} ${line}\n`)
  } catch {}
}

function debug(line) {
  if (DEBUG) log(line)
}

function unwrap(value) {
  return value && typeof value === "object" && "data" in value ? value.data : value
}

function parseModel(text) {
  const raw = String(text ?? "").trim()
  const slash = raw.indexOf("/")
  if (slash <= 0 || slash === raw.length - 1) throw new Error(`zen-failover: bad model "${text}"`)
  return { providerID: raw.slice(0, slash), id: raw.slice(slash + 1) }
}

function parseRules(text) {
  const rules = new Map()
  for (const pair of String(text ?? "").split(";")) {
    const [from, to] = pair.split("=").map((part) => part.trim())
    if (!from || !to) continue
    rules.set(from, { source: from, fallback: parseModel(to) })
  }
  return rules
}

function parseMap(text) {
  const map = new Map()
  for (const pair of String(text ?? "").split(",")) {
    const [from, to] = pair.split("=").map((part) => part.trim())
    if (!from || !to) continue
    map.set(from, parseModel(to))
  }
  return map
}

/** Model ref as it appears in agents/model defaults (id or modelID). */
function modelID(ref) {
  return ref?.id ?? ref?.modelID
}

/** Map a source model ref to its fallback (variant is dropped). */
function fallbackFor(source, ref) {
  const id = modelID(ref)
  if (!id) return null
  const hit = MODEL_MAP.get(`${source}/${id}`)
  if (hit) return { providerID: hit.providerID, id: hit.id }
  const rule = RULES.get(source)
  if (!rule) return null
  const target = rule.fallback.id === "<id>" ? id.replace(/-fast$/, "") : rule.fallback.id
  return { providerID: rule.fallback.providerID, id: target }
}

/**
 * A quota-only source (a subscription plan) must spell out that the plan is
 * exhausted: its transient per-minute 429 carries the same status and a
 * "rate limit" wording. `402` stays an immediate signal for every source.
 */
function isLimitError(source, error) {
  if (!error) return false
  if (error.status === 402) return true
  const text = `${error.type ?? ""} ${error.code ?? ""} ${error.message ?? ""}`
  if (QUOTA_TEXT.test(text)) return true
  if (QUOTA_ONLY.has(source)) return false
  return error.status === 429 || RATE_TEXT.test(text)
}

/**
 * A single 429 can be a transient burst limit; only a sustained run from the
 * same source is treated as an exhausted plan. 402 switches immediately.
 */
function sustainedLimit(source, error) {
  if (error?.status === 402) return true
  const now = Date.now()
  const hits = (recentHits.get(source) ?? []).filter((at) => now - at < HIT_WINDOW)
  hits.push(now)
  recentHits.set(source, hits)
  return hits.length >= MIN_HITS
}

/** Parse "month", "7d", "5h", "30m" (default: 7d, the weekly cap window). */
function parseReset(raw) {
  const text = String(raw ?? "").trim().toLowerCase()
  if (text === "month") {
    const now = new Date()
    return Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1, 0, 0, 0, 0)
  }
  const match = /^(\d+)([hdm])$/.exec(text)
  if (!match) return Date.now() + 7 * 24 * 60 * 60 * 1000
  const value = Number(match[1])
  const unit = match[2] === "h" ? 3600000 : match[2] === "m" ? 60000 : 86400000
  return Date.now() + value * unit
}

function nextResetAt(source) {
  if (RESET_AT_ENV) {
    const asNumber = Number(RESET_AT_ENV)
    const date = Number.isFinite(asNumber) ? new Date(asNumber) : new Date(RESET_AT_ENV)
    if (!Number.isNaN(date.getTime())) return date.getTime()
  }
  // Both sources have weekly sub-limits; a monthly cap simply re-degrades on
  // the next probe after a week instead of blocking the subscription all month.
  const key = `ZEN_FAILOVER_RESET_${String(source).toUpperCase().replace(/[^A-Z0-9]/g, "_")}`
  return parseReset(process.env[key] ?? "7d")
}

async function loadState(ctx) {
  const state = await ctx.storage.get(STORAGE_KEY)
  if (!state || state.version !== STORAGE_VERSION || !state.sources) {
    return { version: STORAGE_VERSION, sources: {} }
  }
  return state
}

async function saveState(ctx, state) {
  if (Object.keys(state.sources).length === 0) {
    await ctx.storage.remove(STORAGE_KEY)
  } else {
    await ctx.storage.set(STORAGE_KEY, state)
  }
}

function track(map, session, source) {
  if (session?.model?.providerID === source && !map[session.id]) {
    const id = modelID(session.model)
    map[session.id] = { id, providerID: source, variant: session.model.variant }
  }
}

async function ensureDegraded(ctx, source, sessionID, model) {
  if (applying) return applying
  applying = (async () => {
    const state = await loadState(ctx)
    let entry = state.sources[source]
    if (!entry) {
      entry = { degradedAt: Date.now(), resetAt: nextResetAt(source), agents: {}, sessions: {} }
      const agents = unwrap(await ctx.agent.list()) ?? []
      for (const agent of agents) {
        if (agent?.model?.providerID === source) {
          entry.agents[agent.id] = {
            id: modelID(agent.model),
            providerID: source,
            variant: agent.model.variant,
          }
        }
      }
      state.sources[source] = entry
      await saveState(ctx, state)
      log(`limit hit: ${source} degraded`)
    }

    if (sessionID && model?.providerID === source && !entry.sessions[sessionID]) {
      track(entry.sessions, { id: sessionID, model }, source)
      await saveState(ctx, state)
    }

    // Re-register on every limit hit: a transform registered during setup is
    // replaced when the location config loads, and only a live registration
    // affects the retry that is about to be scheduled.
    await registerTransforms(ctx)
    for (const [id, original] of Object.entries(entry.sessions)) {
      const target = fallbackFor(source, original)
      if (!target) continue
      try {
        await ctx.session.switchModel({ sessionID: id, model: target })
        log(`switchModel ${id}: ${original.providerID}/${original.id} -> ${target.providerID}/${target.id}`)
      } catch (error) {
        debug(`switchModel ${id} failed: ${error?.message ?? error}`)
      }
    }
    log(
      `switched ${Object.keys(entry.agents).length} agent(s), ` +
        `${Object.keys(entry.sessions).length} session(s) off ${source}`,
    )
    await startProbes(ctx)
    return state
  })()
  try {
    return await applying
  } finally {
    applying = null
  }
}

async function registerTransforms(ctx) {
  if (registrations) {
    try {
      await registrations.agentRegistration.dispose()
      await registrations.modelRegistration.dispose()
    } catch {}
    registrations = null
  }
  if (restoreRegistration) {
    try {
      await restoreRegistration.dispose()
    } catch {}
    restoreRegistration = null
  }

  const state = await loadState(ctx)
  const degraded = new Set(
    Object.keys(state.sources).filter((source) => RULES.has(source)),
  )
  if (degraded.size === 0) {
    stopProbes()
    await ctx.agent.reload()
    await ctx.model.reload()
    return null
  }

  const agentRegistration = await ctx.agent.transform((editor) => {
    for (const agent of editor.list()) {
      const source = agent?.model?.providerID
      if (!source || !degraded.has(source)) continue
      const target = fallbackFor(source, agent.model)
      if (!target) continue
      editor.update(agent.id, (draft) => {
        draft.model = target
      })
    }
  })
  const modelRegistration = await ctx.model.transform((editor) => {
    const current = editor.default.get()
    const source = current?.providerID
    if (!source || !degraded.has(source)) return
    const target = fallbackFor(source, current)
    if (target) editor.default.set(target.providerID, target.id)
  })
  registrations = { agentRegistration, modelRegistration }
  await ctx.agent.reload()
  await ctx.model.reload()
  log(`transforms registered for ${[...degraded].join(",")}`)
  if (DEBUG) {
    try {
      const agents = unwrap(await ctx.agent.list()) ?? []
      debug(
        `agents now: ${agents
          .filter((agent) => agent.model)
          .map((agent) => `${agent.id}=${agent.model.providerID}/${modelID(agent.model)}`)
          .join(",")}`,
      )
      const fallback = unwrap(await ctx.model.default())
      debug(`default now: ${fallback?.providerID}/${modelID(fallback)}`)
    } catch (error) {
      debug(`introspection failed: ${error?.message ?? error}`)
    }
  }
  return registrations
}

async function restoreSource(ctx, source, state) {
  const entry = state.sources[source]
  if (!entry) return
  for (const [id, original] of Object.entries(entry.sessions ?? {})) {
    try {
      await ctx.session.switchModel({ sessionID: id, model: original })
    } catch {}
  }
  delete state.sources[source]
  await saveState(ctx, state)
  log(`limits reset: ${source} available again`)
}

/**
 * Ask the degraded source itself whether it is back: a throwaway session on
 * one of its original models, one minimal generation, then remove it. A success
 * means the plan can serve requests again, a limit error means "still out".
 */
/**
 * The model to probe with: any agent bound to the source, otherwise the session
 * that was switched away from it (a model can be used without any agent).
 */
function probeModel(entry) {
  const agent = Object.values(entry.agents ?? {})[0]
  if (agent) return { providerID: agent.providerID, id: agent.id, variant: agent.variant }
  const session = Object.values(entry.sessions ?? {})[0]
  if (session) return { providerID: session.providerID, id: session.id, variant: session.variant }
  return undefined
}

async function probeSource(ctx, source, entry) {
  const original = probeModel(entry)
  if (!original) {
    debug(`probe ${source}: no agent or session to probe with`)
    return false
  }
  let sessionID
  try {
    const created = unwrap(
      await ctx.session.create({
        title: "zen-failover probe",
        model: { providerID: original.providerID, id: original.id },
      }),
    )
    sessionID = created?.id
    if (!sessionID) return false
    const result = unwrap(await ctx.session.generate({ sessionID, prompt: PROBE_PROMPT }))
    return typeof result?.text === "string"
  } catch (error) {
    debug(
      `probe ${source}: still unavailable ` +
        `(status=${error?.status ?? "-"} message=${error?.message ?? error})`,
    )
    return false
  } finally {
    if (sessionID) {
      try {
        await ctx.session.remove(sessionID)
      } catch {}
    }
  }
}

async function probeDegraded(ctx) {
  if (probeInFlight) return
  probeInFlight = true
  try {
    const state = await loadState(ctx)
    const restored = []
    for (const [source, entry] of Object.entries(state.sources)) {
      if (!RULES.has(source)) continue
      if (!(await probeSource(ctx, source, entry))) continue
      await restoreSource(ctx, source, state)
      log(`probe ${source}: available, restored`)
      restored.push(source)
    }
    if (restored.length > 0) {
      await registerTransforms(ctx)
      await startProbes(ctx)
    }
  } catch (error) {
    debug(`probe failed: ${error?.message ?? error}`)
  } finally {
    probeInFlight = false
  }
}

function stopProbes() {
  if (probeTimer) {
    clearInterval(probeTimer)
    probeTimer = null
  }
}

/** One timer for all degraded sources: probe now, then every PROBE_MS. */
async function startProbes(ctx, { immediate = false } = {}) {
  stopProbes()
  if (PROBE_MS <= 0) return
  const state = await loadState(ctx)
  const degraded = Object.keys(state.sources).filter((source) => RULES.has(source))
  if (degraded.length === 0) return
  probeTimer = setInterval(() => {
    void probeDegraded(ctx)
  }, PROBE_MS)
  probeTimer.unref?.()
  if (immediate) await probeDegraded(ctx)
}

async function resetIfExpired(ctx) {
  const state = await loadState(ctx)
  let changed = false
  for (const [source, entry] of Object.entries(state.sources)) {
    if (Date.now() < entry.resetAt) continue
    await restoreSource(ctx, source, state)
    changed = true
  }
  if (changed) await registerTransforms(ctx)
  return changed
}

export default {
  id: "zen-failover",
  async setup(ctx) {
    log(`loaded (rules: ${[...RULES.keys()].join(",")})`)
    debug(`ctx keys: ${Object.keys(ctx).join(",")}`)
    debug(`ctx.session keys: ${Object.keys(ctx.session ?? {}).join(",")}`)
    await resetIfExpired(ctx)
    const state = await loadState(ctx)
    if (Object.keys(state.sources).length > 0) {
      await registerTransforms(ctx)
      log(
        `resumed degraded state: ${Object.entries(state.sources)
          .map(([source, entry]) => `${source} until ${new Date(entry.resetAt).toISOString()}`)
          .join(", ")}`,
      )
      await startProbes(ctx)
      if (PROBE_ON_START) {
        // Start probing right away, but never stall startup on a slow provider:
        // the probe keeps running in the background and the timer retries it.
        await Promise.race([
          probeDegraded(ctx),
          new Promise((resolve) => setTimeout(resolve, PROBE_START_WAIT_MS).unref?.()),
        ])
      }
    }

    let refreshed = false
    const refreshOnce = async () => {
      if (refreshed) return
      refreshed = true
      const current = await loadState(ctx)
      if (Object.keys(current.sources).length > 0) {
        await registerTransforms(ctx)
        log("refreshed transforms after config load")
      }
    }

    const controller = new AbortController()
    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
          if (event?.type !== "agent.updated" && event?.type !== "model.updated" && event?.type !== "config.updated") {
            continue
          }
          await refreshOnce()
          controller.abort()
          break
        }
      } catch {}
    })()

    void ctx.session.hook("retry", async (event) => {
      const model = event?.model
      const source = model?.providerID
      debug(
        `retry event model=${source}/${model?.id} status=${event?.error?.status} ` +
          `attempt=${event?.attempt} type=${event?.error?.type} message=${event?.error?.message}`,
      )
      if (!source || !RULES.has(source)) return
      if (!isLimitError(source, event.error)) return
      try {
        if (!sustainedLimit(source, event.error)) {
          debug(`limit hit ${source}: below ${MIN_HITS}/${HIT_WINDOW}ms; retrying before switching`)
          if (event.attempt <= 3) event.decision = { retry: true, delay: 0 }
          return
        }
        await ensureDegraded(ctx, source, event.sessionID, model)
        refreshed = true
        if (event.attempt <= 5) event.decision = { retry: true, delay: 0 }
      } catch (error) {
        log(`switch failed: ${error?.stack ?? error}`)
      }
    })

    void ctx.session.hook("context", async () => {
      try {
        if (await resetIfExpired(ctx)) return
        await refreshOnce()
      } catch (error) {
        log(`reset check failed: ${error?.message ?? error}`)
      }
    })

    return () => {
      controller.abort()
      stopProbes()
    }
  },
}
