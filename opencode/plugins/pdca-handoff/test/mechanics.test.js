import { test } from "node:test"
import assert from "node:assert/strict"
import { createHash } from "node:crypto"
import { mkdtemp, mkdir, readFile, writeFile, rm, symlink } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import plugin from "../index.js"

const skills = fileURLToPath(new URL("../../../../skills/", import.meta.url))
const hash = (b) => createHash("sha256").update(b).digest("hex")
const owner = "ses_executor",
  driver = "ses_driver",
  checker = "ses_checker",
  planner = "ses_planner"
const packet = "pdca_check_packet_v1",
  events = "pdca_record_event_v1",
  wait = "pdca_wait_v1"
const base = { status: ".pdca/status/demo.md", evidence: ".pdca/demo/rv1" }
const expect = { N: 1, r: 1, n: 1, phase: "DO" }
const caps = "packet-v1 events-v1 wait-v1"
async function fixture(t, opts = {}) {
  const root = await mkdtemp(join(tmpdir(), "pdca-mechanics-"))
  for (const path of [".pdca/status", base.evidence]) await mkdir(join(root, path), { recursive: true })
  const pin = async (file, data) => {
    const path = base.evidence + "/" + file
    const bytes = typeof data === "string" ? data : JSON.stringify(data)
    await writeFile(join(root, path), bytes)
    return { path, sha256: hash(bytes) }
  }
  const log = await pin("run.log", "passed: 3/3"),
    obs = await pin("observer.md", "Independent observation")
  const brief = await pin("brief.md", "Original task, criteria and defect history by reference.")
  const recipe = await pin("requirements.json", {
    mode: "candidate",
    criteria: ["C1"],
    slots: [
      { id: "test", kind: "run", criterion: "C1" },
      { id: "observation", kind: "observation", criterion: "C1" },
    ],
  })
  const manifest = {
    candidate: "snapshot-1",
    brief,
    criteria: ["C1"],
    required: [
      { id: "test", ref: log, criterion: "C1" },
      { id: "observation", ref: obs, criterion: "C1" },
    ],
    runs: [{ log: "test", command: "test-suite", exit: 0, candidate: "snapshot-1" }],
  }
  const manifestRef = await pin("manifest.json", manifest)
  const status = join(root, base.status)
  await writeFile(
    status,
    `# Cycle
## Current state
Mechanics: manual
Adapters: ${opts.election ?? caps}
Adapter owner: ${owner}
Adapter evidence: ${base.evidence}
Packet requirements candidate N1/r1: ${JSON.stringify(recipe)}
- cycle: \`N=1\` · revision: \`r=1\` · attempt: \`n=1\`
- phase: \`DO\` · record: \`open\` · outcome: \`pending\`
## Original task
Original immutable input.
## PLAN record
### r1
Original plan.
## DO result
Pending substantive DO.
## CHECK record
Not run: candidate pending.
## ACT record
Pending.
## Lessons learned
Pending retrospective.
## Revision history
none
## Progress log
Initial event.
`,
  )
  const defs = new Map(),
    storage = new Map(),
    inbox = new Map(),
    msgs = new Map()
  const agents = {
    [owner]: "pdca-executor",
    [driver]: "build",
    [checker]: "pdca-check",
    [planner]: "pdca-planner",
  }
  const receipt = (agent, text, id) => ({
    agent,
    id,
    type: "assistant",
    finish: "stop",
    content: [{ type: "text", text }],
  })
  const controls = { lost: false, deny: null, interruptBefore: false }
  const ctx = {
    options: opts,
    location: { directory: root },
    tool: { transform: (fn) => fn({ add: (d) => defs.set(d.name, d) }) },
    session: {
      get: async ({ sessionID: id }) => ({
        id,
        agent: agents[id],
        parentID: id === driver ? undefined : driver,
        location: { directory: root },
        time: {},
      }),
      context: async ({ sessionID }) => msgs.get(sessionID) ?? [],
      prompt: async (input) => {
        if (controls.interruptBefore) throw Error("offline before admission")
        inbox.set(input.id, input)
        if (controls.lost) throw Error("lost admission reply")
      },
    },
    skill: {
      list: async () =>
        ["pdca", "pdca-coder", "pdca-dotnet"].map((id) => ({ id, path: join(skills, id, "SKILL.md") })),
    },
    permission: {
      assert: async (i) => {
        if (controls.deny?.(i)) throw Error("permission denied")
      },
    },
    storage: {
      set: (k, v) => storage.set(k, v),
      scan: async ({ prefix }) => ({
        entries: [...storage].filter(([k]) => k.startsWith(prefix)).map(([key, value]) => ({ key, value })),
      }),
    },
  }
  let close, trigger
  ctx.event = {
    subscribe: ({ signal }) => ({
      async *[Symbol.asyncIterator]() {
        while (!signal.aborted) {
          const v = await new Promise((r) => {
            trigger = r
            signal.addEventListener("abort", () => r(null), { once: true })
          })
          if (v) yield v
        }
      },
    }),
  }
  const reload = async () => {
    await close?.()
    defs.clear()
    close = await plugin.setup(ctx)
  }
  await reload()
  t.after(async () => {
    await close?.()
    await rm(root, { recursive: true, force: true })
  })
  const call = async (tool, i, id = owner) =>
    JSON.parse(
      (
        await defs
          .get(tool)
          .execute({ ...base, ...i }, { agent: agents[id], sessionID: id, messageID: "msg_tool", id: "call" })
      ).content,
    )
  const event = async (e) => {
    trigger(e)
    await new Promise((r) => setImmediate(r))
  }
  return {
    root,
    status,
    pin,
    recipe,
    manifest,
    manifestRef,
    defs,
    controls,
    call,
    receipt,
    inbox,
    msgs,
    reload,
    event,
    storage,
    log,
  }
}

test("election is per capability; old, unselected and disabled adapters remain manual", async (t) => {
  const f = await fixture(t, { capabilities: ["events-v1"], election: "packet-v1" })
  assert.deepEqual([...f.defs.keys()].sort(), [events, "pdca_handoff_v1"].sort())
  const before = await readFile(f.status)
  await assert.rejects(f.call(events, { key: "first", expect, kind: "do", ref: f.log }), /not elected/)
  assert.deepEqual(await readFile(f.status), before)
})

test("CHECK pack is candidate-bound, contains the installed contract, redelivers once", async (t) => {
  const f = await fixture(t),
    args = { key: "review1", expect, manifest: f.manifestRef, checker }
  const r = await f.call(packet, args)
  const body = await readFile(join(f.root, r.ref.path), "utf8")
  assert.equal(hash(body), r.ref.sha256)
  assert.ok(body.startsWith(await readFile(join(skills, "pdca/references/check.md"), "utf8")))
  assert.ok(body.includes("test-suite"))
  assert.ok(body.includes(f.log.sha256))
  assert.equal((await f.call(packet, args)).duplicate, true)
  const before = await readFile(f.status, "utf8")
  assert.equal(before.split("CHECK packet ready").length, 2)
  f.controls.lost = true
  await assert.rejects(f.call(packet, { ...args, action: "send" }), /lost admission/)
  const pending = await f.call(packet, { action: "inspect", key: args.key })
  assert.equal(pending.delivery.stage, "pending")
  assert.equal(f.inbox.get(pending.delivery.id).text, JSON.stringify(r.ref))
  // Downgrade between write and acknowledgement: receipt is readable without plugin code.
  assert.ok((await readFile(f.status, "utf8")).includes(pending.delivery.id))
  f.controls.lost = false
  f.msgs.set(checker, [{ type: "user", id: pending.delivery.id }])
  await f.reload()
  assert.equal((await f.call(packet, { ...args, action: "send" })).delivery.stage, "sent")
  assert.equal(f.inbox.size, 1)
})

test("missing method-selected slot, changed log, and inaccessible checker evidence stop before CHECK", async (t) => {
  const f = await fixture(t),
    args = { key: "review", expect, checker }
  const before = await readFile(f.status)
  const partial = await f.pin("partial.json", { ...f.manifest, required: f.manifest.required.slice(0, 1) })
  await assert.rejects(
    f.call(packet, { ...args, manifest: partial }),
    /missing required evidence: observation/,
  )
  f.controls.deny = (i) => i.agent === "pdca-check" && i.resources.some((p) => p.endsWith("observer.md"))
  await assert.rejects(f.call(packet, { ...args, manifest: f.manifestRef }), /permission denied/)
  f.controls.deny = null
  await writeFile(join(f.root, f.log.path), "changed")
  await assert.rejects(f.call(packet, { ...args, manifest: f.manifestRef }), /changed evidence/)
  assert.equal(f.inbox.size, 0)
  assert.deepEqual(await readFile(f.status), before)
})

test("restart between candidate recording and CHECK admission reuses the prepared packet", async (t) => {
  const f = await fixture(t)
  const args = { key: "check1", action: "send", expect, manifest: f.manifestRef, checker, track: true }
  f.controls.interruptBefore = true
  await assert.rejects(f.call(packet, args), /offline before admission/)
  const p = await f.call(packet, { key: args.key, action: "inspect" })
  assert.equal(p.delivery.stage, "pending")
  assert.equal(f.inbox.size, 0)
  assert.match(await readFile(f.status, "utf8"), /phase: `CHECK`/)
  f.controls.interruptBefore = false
  await f.reload()
  assert.equal((await f.call(packet, { key: args.key, action: "inspect" })).delivery.stage, "sent")
  const message = { type: "user", id: p.delivery.id, text: JSON.stringify(p.ref) }
  const valid = f.receipt("pdca-check", "C1 met.\nPDCA-RECORD check1-verdict accepted", "msg_judge")
  f.msgs.set(checker, [message, valid, { type: "idle", outcome: "succeeded" }])
  await f.event({ type: "session.execution.succeeded", data: { sessionID: checker } })
  await f.call(packet, { key: args.key, action: "inspect" })
  const status = await readFile(f.status, "utf8")
  assert.match(status, /phase: `ACT`/)
  assert.equal(f.inbox.size, 1)
  assert.equal(status.split("pdca-op:events-v1:check1-verdict:").length, 2)
})

test("changed product inputs or a missing declared input invalidate the prepared packet", async (t) => {
  const f = await fixture(t),
    path = "result.txt"
  const recipe = await f.pin("recipe2.json", {
    mode: "candidate",
    criteria: ["C1"],
    inputPaths: [path],
    slots: [{ id: "test", criterion: "C1", kind: "run" }],
  })
  await writeFile(
    f.status,
    (await readFile(f.status, "utf8"))
      .replace(f.recipe.sha256, recipe.sha256)
      .replace(f.recipe.path, recipe.path),
  )
  const args = { key: "packet", expect, manifest: f.manifestRef, checker }
  await assert.rejects(f.call(packet, args), /missing declared candidate input/)
  await writeFile(join(f.root, path), "1")
  args.manifest = await f.pin("candidate.json", { ...f.manifest, inputs: [{ path, sha256: hash("1") }] })
  await f.call(packet, args)
  await writeFile(join(f.root, path), "2")
  await assert.rejects(f.call(packet, { ...args, action: "send" }), /changed evidence/)
  assert.equal(f.inbox.size, 0)
})

test("phase events preserve the original decision, project once and reject stale or invented verdicts", async (t) => {
  const f = await fixture(t)
  const ev = { key: "candidate1", expect, kind: "candidate", ref: f.log }
  assert.equal((await f.call(events, ev)).coordinates.phase, "CHECK")
  assert.equal((await f.call(events, ev)).duplicate, true)
  const chk = { ...expect, phase: "CHECK" }
  await assert.rejects(f.call(events, { ...ev, key: "stale" }), /stale cycle/)
  await assert.rejects(f.call(events, { key: "pass", expect: chk, kind: "accepted", ref: f.log }), /producer/)
  const report = "C1 met by test. Remaining: none.\nPDCA-RECORD pass accepted"
  f.msgs.set(checker, [f.receipt("pdca-check", report, "msg_final")])
  const decision = {
    key: "pass",
    owner,
    expect: chk,
    kind: "accepted",
    session: checker,
    message: "msg_final",
  }
  const result = await f.call(events, decision, driver)
  assert.equal(await readFile(join(f.root, result.ref.path), "utf8"), report)
  assert.deepEqual(result.coordinates, { ...expect, phase: "ACT" })
  assert.equal((await f.call(events, decision, driver)).duplicate, true)
  const status = await readFile(f.status, "utf8")
  assert.equal(status.split("pdca-op:events-v1:pass:").length, 2)
  assert.ok(status.includes("Original immutable input."))
})

test("revised PLAN changes counters once, records outgoing attempt, keeps original revision", async (t) => {
  const f = await fixture(t)
  await f.call(events, { key: "candidate", kind: "candidate", expect, ref: f.log })
  for (const [id, role, kind, phase] of [
    [checker, "pdca-check", "contract", "CHECK"],
    [planner, "pdca-planner", "revised-plan", "PLAN"],
  ]) {
    f.msgs.set(id, [f.receipt(role, `Changed criterion.\nPDCA-RECORD decision-${phase} ${kind}`, "msg_1")])
    await f.call(events, {
      key: "decision-" + phase,
      kind,
      expect: { ...expect, phase },
      session: id,
      message: "msg_1",
    })
  }
  const state = await readFile(f.status, "utf8")
  assert.match(state, /revision: `r=2` · attempt: `n=0`/)
  assert.match(state, /### r1\nOriginal plan\./)
  assert.match(state, /### r2\n/)
  assert.match(state, /r1 attempt 1 → r2/)
})

const job = "sh_test"
function shellLaunch(pid) {
  return {
    type: "assistant",
    id: "msg_launch",
    agent: "pdca-executor",
    content: [
      {
        type: "tool",
        name: "shell",
        state: {
          status: "completed",
          content: [
            {
              type: "text",
              text: `Command moved to the background (shell ID: ${job}).\nPID: ${pid}\nOutput is streaming.`,
            },
          ],
        },
      },
    ],
  }
}
const waiting = {
  job,
  action: "register",
  expect,
  next: "Inspect the log and decide whether to correct the test.",
}
test("wait verifies ownership, survives restart, consumes native completion without a second prompt", async (t) => {
  const f = await fixture(t)
  await assert.rejects(f.call(wait, waiting), /not a background shell/)
  f.msgs.set(owner, [shellLaunch(process.pid)])
  assert.equal((await f.call(wait, waiting)).state, "running")
  await f.reload()
  assert.equal((await f.call(wait, { job, action: "inspect" })).state, "running")
  f.msgs
    .get(owner)
    .push({
      type: "synthetic",
      id: "msg_result",
      metadata: { source: "shell", shellID: job, state: "completed", exit: 7 },
    })
  await f.event({ type: "session.inbox.delivered", data: { sessionID: owner } })
  const done = await f.call(wait, { job, action: "inspect" })
  assert.equal(done.exit, 7)
  assert.equal(done.delivery, "native")
  assert.equal(f.inbox.size, 0)
})

test("lost shell has unknown outcome; admission retry reuses ID and never reruns the command", async (t) => {
  const f = await fixture(t)
  f.msgs.set(owner, [shellLaunch(2147483647)])
  await f.call(wait, waiting)
  f.controls.lost = true
  await assert.rejects(f.call(wait, { job, action: "recover" }), /lost admission/)
  const pending = await f.call(wait, { job, action: "inspect" })
  assert.equal(pending.state, "unknown")
  assert.equal(pending.delivery, "pending")
  assert.ok(f.inbox.get(pending.deliveryID).text.includes("do not relaunch"))
  f.controls.lost = false
  await f.reload()
  const result = await f.call(wait, { job, action: "inspect" })
  assert.equal(result.delivery, "admitted")
  assert.equal(f.inbox.size, 1)
})

test("symlink and wrong evidence revision rejected before writing", async (t) => {
  const f = await fixture(t)
  await writeFile(join(f.root, "outside.md"), "outside")
  await symlink(join(f.root, "outside.md"), join(f.root, base.evidence, "link.md"))
  const args = {
    key: "do1",
    kind: "do",
    expect,
    ref: { path: base.evidence + "/link.md", sha256: hash("outside") },
  }
  await assert.rejects(f.call(events, args), /regular workspace/)
  await assert.rejects(f.call(events, { ...args, evidence: ".pdca/demo/rv2" }), /status field/)
})
