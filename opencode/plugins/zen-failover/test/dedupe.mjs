#!/usr/bin/env node
// Probe deduplication test.
//
// The host loads the plugin once per location, so one process holds several
// copies of the module. The probe is a real request to the plan (and a real
// rejection in its usage log while the plan is out): it must fire once per
// interval per degraded source for the whole process, not once per copy.
//
//   ZEN_FAILOVER_PROBE_MS=600000 node test/dedupe.mjs start
//     two copies start at the same moment -> exactly one probe request
//
//   ZEN_FAILOVER_PROBE_MS=200 node test/dedupe.mjs ticks
//     three copies over several intervals -> probes never bunch up
//
// Both copies below are separate module instances (cache-busting query string)
// sharing one globalThis, exactly like the host's per-location loads.

import { dirname, join } from "node:path"
import { fileURLToPath, pathToFileURL } from "node:url"

const HERE = dirname(fileURLToPath(import.meta.url))
const PLUGIN = process.env.ZEN_FAILOVER_TEST_PLUGIN ?? join(HERE, "..", "index.js")
const MODE = process.argv[2] ?? "start"
const PROBE_MS = Number(process.env.ZEN_FAILOVER_PROBE_MS ?? 600000)
const PROBE_TIMEOUT = 15000

process.env.ZEN_FAILOVER_RULES = "mockgo=mockds/deepseek-flash"
process.env.ZEN_FAILOVER_MAP = "mockgo/gemini-4-argon=mockds/gemini-4-argon"

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function withTimeout(promise, ms, what) {
  let timer
  const limit = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${what} stalled after ${ms}ms`)), ms)
    timer.unref?.()
  })
  try {
    return await Promise.race([promise, limit])
  } finally {
    clearTimeout(timer)
  }
}

function fail(message) {
  console.error(`FAIL: ${message}`)
  process.exit(1)
}

// One degraded source, shared by every copy (one storage, like the host DB).
const started = Date.now()
const storageMap = new Map([
  [
    "zen-failover",
    {
      version: 2,
      sources: {
        mockgo: {
          degradedAt: started - 60000,
          resetAt: started + 3600000,
          agents: { planner: { id: "gemini-4-argon", providerID: "mockgo" } },
          sessions: {},
        },
      },
    },
  ],
])
const storage = {
  async get(key) {
    return storageMap.get(key)
  },
  async set(key, value) {
    storageMap.set(key, value)
  },
  async remove(key) {
    storageMap.delete(key)
  },
}

const calls = []
// A real probe is a network round-trip, so the verdict finishes a bit after the
// tick that started it. The interval must be anchored at the request, not at
// the answer: with the anchor at the answer the next tick looks fresh and the
// cadence silently doubles.
const PROBE_LATENCY = Math.min(Math.round(PROBE_MS * 0.2), 200)

function makeCtx() {
  return {
    storage,
    session: {
      async create() {
        return { id: `ses_probe_${calls.length + 1}` }
      },
      async generate() {
        calls.push(Date.now())
        await sleep(PROBE_LATENCY)
        // The plan is still out: every probe is rejected.
        throw Object.assign(new Error("usage limit reached for gemini-4-argon"), { status: 429 })
      },
      async remove() {},
      async switchModel() {},
      async hook() {
        return () => {}
      },
    },
    agent: {
      async list() {
        return []
      },
      async reload() {},
      async transform(editor) {
        editor({ list: () => [], update() {} })
        return { dispose() {} }
      },
    },
    model: {
      async transform(editor) {
        editor({ default: { get: () => undefined, set() {} } })
        return { dispose() {} }
      },
      async reload() {},
      async default() {
        return undefined
      },
    },
    event: {
      async *subscribe({ signal }) {
        await new Promise((resolve) => signal.addEventListener("abort", resolve, { once: true }))
      },
    },
  }
}

async function loadCopy(n) {
  const module = await import(`${pathToFileURL(PLUGIN).href}?copy=${n}`)
  return module.default
}

const copies = MODE === "ticks" ? 3 : 2
const plugins = await Promise.all(Array.from({ length: copies }, (_, i) => loadCopy(i)))
const start = Date.now()
const cleanups = []
if (MODE === "start") {
  // Every copy starts at the same moment: the startup probe must be shared.
  cleanups.push(
    ...(await Promise.all(
      plugins.map((plugin, i) => withTimeout(plugin.setup(makeCtx(i)), PROBE_TIMEOUT, "setup")),
    )),
  )
} else {
  // Copies load at different moments, so their timers sit at different phases —
  // the usual case in a live host.
  for (const [i, plugin] of plugins.entries()) {
    if (i > 0) await sleep(Math.round(PROBE_MS * 0.02) * i)
    cleanups.push(await withTimeout(plugin.setup(makeCtx(i)), PROBE_TIMEOUT, "setup"))
  }
}

if (MODE === "start") {
  if (calls.length !== 1) {
    cleanups.forEach((cleanup) => cleanup?.())
    fail(`${copies} copies issued ${calls.length} startup probe(s), expected 1`)
  }
  console.log(`   ok: ${copies} copies issued one startup probe`)
} else {
  await sleep(PROBE_MS * 5)
  const elapsed = Date.now() - start
  cleanups.forEach((cleanup) => cleanup?.())

  const gaps = calls.slice(1).map((at, i) => at - calls[i])
  const bunched = gaps.filter((gap) => gap < PROBE_MS * 0.5)
  if (bunched.length > 0) {
    fail(
      `${copies} copies issued probes ${JSON.stringify(bunched)}ms apart ` +
        `(interval ${PROBE_MS}ms) — a burst is a duplicate probe, not a new interval`,
    )
  }
  const stretched = gaps.filter((gap) => gap > PROBE_MS * 1.6)
  if (stretched.length > 0) {
    fail(
      `probes ${JSON.stringify(stretched)}ms apart (interval ${PROBE_MS}ms) — ` +
        `an interval was skipped, the cadence is not the configured one`,
    )
  }
  const budget = 1 + Math.ceil(elapsed / PROBE_MS) + 2
  if (calls.length > budget) {
    fail(`${calls.length} probes in ${elapsed}ms across ${copies} copies (budget ${budget})`)
  }
  if (calls.length < 2) fail("the loop stopped probing")
  console.log(
    `   ok: ${calls.length} probes in ${elapsed}ms across ${copies} copies, ` +
      `gaps ${Math.min(...gaps)}..${Math.max(...gaps)}ms (interval ${PROBE_MS}ms)`,
  )
}
