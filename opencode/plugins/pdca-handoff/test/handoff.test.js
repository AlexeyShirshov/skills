import { test } from "node:test"
import assert from "node:assert/strict"
import { mkdtemp, mkdir, readFile, writeFile, rm, symlink } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { createHash } from "node:crypto"
import plugin from "../index.js"

const election = "Mechanics: pdca-handoff-v1"
const campaign = `# Campaign
## Campaign state
Status: running
Mode: autonomous
Current step: 3   Phase: ACT   Cycle: 7   Plan revision: r2   Attempt: 2/3
## Original task
Support composite keys.
## Preparation record
Ready.
## Baseline record
Baseline: accepted
## Checkpoint
${election}
Disposition: open
Resume: planner boundary.
## Step records
### Step 3
#### ACT record
Record: completed; outcome: accepted
## Campaign outcome
Pending.
## Lessons learned
Pending campaign retrospective.
## Progress log
Previous evidence.
`
const cycle = `# Cycle
## Current state
${election}
- mode: \`autonomous\`
- cycle: \`N=7\` · revision: \`r=2\` · attempt: \`n=0\`
- phase: \`PLAN\` · record: \`open\` · outcome: \`pending\`
## Original task
Unchanged.
## PLAN record
### r1
Immutable previous plan.
### r2
pending
## Progress log
Prior row.
`

async function fixture(t, statusText = campaign) {
  const root = await mkdtemp(join(tmpdir(), "handoff-"))
  await mkdir(join(root, ".pdca/status"), { recursive: true })
  await mkdir(join(root, ".pdca/demo/rv2"), { recursive: true })
  const status = ".pdca/status/demo.md",
    path = join(root, status)
  await writeFile(path, statusText)
  const storage = new Map(),
    inbox = new Map(),
    issued = [],
    failed = { reply: false }
  const ids = { executor: "ses_executor", planner: "ses_planner", driver: "ses_driver" }
  const ctxs = new Map([
    [ids.driver, [{ type: "user", id: "msg_original" }]],
    [ids.planner, []],
  ])
  const access = { denied: false }
  const roles = { ses_executor: "pdca-executor", ses_planner: "pdca-planner", ses_driver: "build" }
  let def, dispose
  const host = {
    location: { directory: root },
    session: {
      get: async ({ sessionID: id }) => ({
        id,
        agent: roles[id],
        location: { directory: root },
        time: {},
        ...(id !== ids.driver && { parentID: ids.driver }),
      }),
      context: async ({ sessionID: id }) => ctxs.get(id) ?? [],
      prompt: async (p) => {
        issued.push(p.id)
        if (!inbox.has(p.id)) inbox.set(p.id, p)
        if (failed.reply) throw Error("lost reply after admission")
        return { id: p.id }
      },
    },
    event: {
      subscribe: ({ signal }) =>
        (async function* () {
          if (!signal.aborted) await new Promise((r) => signal.addEventListener("abort", r, { once: true }))
        })(),
    },
    storage: {
      set: async (k, v) => storage.set(k, structuredClone(v)),
      scan: async ({ prefix }) => ({
        entries: [...storage].filter(([k]) => k.startsWith(prefix)).map(([key, value]) => ({ key, value })),
      }),
    },
    permission: {
      assert: async () => {
        if (access.denied) throw Error("denied")
      },
    },
    tool: {
      transform: async (fn) =>
        fn({
          add: (d) => {
            def = d
          },
        }),
    },
  }
  const reload = async () => {
    await dispose?.()
    dispose = await plugin.setup(host)
  }
  await reload()
  t.after(async () => {
    await dispose?.()
    await rm(root, { recursive: true, force: true })
  })
  const call = async (i, agent = "pdca-executor") =>
    JSON.parse(
      (
        await def.execute(
          { status, ...i },
          { agent, sessionID: ids.executor, messageID: "msg_test", id: "call" },
        )
      ).content,
    )
  const arm = () =>
    call({
      action: "arm",
      planner: ids.planner,
      evidence: ".pdca/demo/rv2",
      boundary: statusText === cycle ? "plan" : "next-step",
      brief: "Use the original task, inherited criteria and test scope.",
    })
  const finish = (ticket, decision = "ready") => {
    const text = `The exact original plan.\nPDCA-HANDOFF ${ticket} ${decision}`
    ctxs.set(ids.planner, [
      { type: "user", id: "msg_req", text: `Decide.\nPDCA-HANDOFF ${ticket}` },
      {
        type: "assistant",
        agent: "pdca-planner",
        id: "msg_plan",
        finish: "stop",
        content: [{ type: "text", text }],
      },
      { type: "idle", id: "msg_idle", outcome: "succeeded" },
    ])
    return text
  }
  return { root, path, arm, call, finish, inbox, issued, failed, access, ctxs, reload }
}

for (const [name, initial] of [
  ["cycle", cycle],
  ["campaign", campaign],
])
  test(`${name}: atomic PLAN → DO, original bytes and one admission`, async (t) => {
    const f = await fixture(t, initial)
    const { ticket } = await f.arm()
    assert.equal((await f.arm()).ticket, ticket)
    const original = f.finish(ticket)
    const res = await f.call({ action: "recover", ticket })
    assert.equal(res.stage, "delivered")
    assert.deepEqual(res.counters, name === "cycle" ? { N: 7, r: 2, n: 1 } : { step: 4, N: 8, r: 1, n: 1 })
    assert.equal(await readFile(join(f.root, res.ref.path), "utf8"), original)
    assert.equal(res.ref.sha256, createHash("sha256").update(original).digest("hex"))
    assert.ok([...f.inbox.values()][0].text.includes(res.ref.path))
    const text = await readFile(f.path, "utf8")
    assert.ok(text.includes(name === "cycle" ? "Immutable previous plan." : "### Step 4"))
    assert.ok(text.includes("Prior row.") || text.includes("Previous evidence."))
    await f.call({ action: "recover", ticket })
    assert.equal(await readFile(f.path, "utf8"), text)
    assert.equal(f.issued.length, 1)
  })

test("restart after admission but before acknowledgement reuses inbox ID", async (t) => {
  const f = await fixture(t)
  const { ticket } = await f.arm()
  f.finish(ticket)
  f.failed.reply = true
  await assert.rejects(f.call({ action: "recover", ticket }), /lost reply/)
  assert.equal((await f.call({ action: "inspect" })).stage, "pending")
  await assert.rejects(f.call({ action: "release", ticket }), /reconcile/)
  f.failed.reply = false
  await f.reload()
  assert.equal((await f.call({ action: "inspect" })).stage, "delivered")
  assert.equal(f.issued.length, 2)
  assert.equal(f.inbox.size, 1)
  assert.equal((await readFile(f.path, "utf8")).match(/### Step 4\b/g).length, 1)
})

test("new user instruction, changed file or denied permission cannot start work", async (t) => {
  const f = await fixture(t)
  f.access.denied = true
  await assert.rejects(f.arm(), /denied/)
  assert.equal(await readFile(f.path, "utf8"), campaign)
  f.access.denied = false
  const { ticket } = await f.arm()
  f.finish(ticket)
  f.ctxs.get("ses_driver").push({ type: "user", id: "msg_stop" })
  await assert.rejects(f.call({ action: "recover", ticket }), /new instruction/)
  f.ctxs.get("ses_driver").pop()
  await writeFile(
    f.path,
    (await readFile(f.path, "utf8")).replace("Disposition: open", "Disposition: paused"),
  )
  await assert.rejects(f.call({ action: "recover", ticket }), /status changed/)
  assert.equal(f.inbox.size, 0)
})

test("held, interrupted, stale and released decisions do not deliver", async (t) => {
  const f = await fixture(t)
  const { ticket } = await f.arm()
  f.finish("another-ticket")
  assert.equal((await f.call({ action: "recover", ticket })).stage, "armed")
  f.finish(ticket, "stop")
  assert.equal((await f.call({ action: "recover", ticket })).stage, "held")
  await f.call({ action: "release", ticket })
  f.finish(ticket)
  await f.reload()
  assert.equal((await f.call({ action: "inspect" })).stage, "released")
  assert.equal(f.inbox.size, 0)
})

test("interruption holds the ticket without fabricating a report", async (t) => {
  const f = await fixture(t)
  const { ticket } = await f.arm()
  f.finish(ticket)
  f.ctxs.get("ses_planner").at(-1).outcome = "interrupted"
  const result = await f.call({ action: "recover", ticket })
  assert.equal(result.stage, "held")
  assert.match(result.reason, /interrupted/)
  assert.equal(result.ref, undefined)
  assert.equal(f.inbox.size, 0)
})

test("normal mode, manual records, other roles and escaping paths are excluded", async (t) => {
  const f = await fixture(t)
  await assert.rejects(f.call({ action: "inspect" }, "pdca-planner"), /executor/)
  await assert.rejects(f.call({ action: "arm", status: "../outside.md" }), /assigned status/)
  await writeFile(f.path, campaign.replace("Mode: autonomous", "Mode: normal"))
  await assert.rejects(f.arm(), /status field/)
  await writeFile(f.path, campaign.replace(election, "Mechanics: manual"))
  await assert.rejects(f.arm(), /status field/)
  await rm(f.path)
  await writeFile(join(f.root, "outside.md"), campaign)
  await symlink(join(f.root, "outside.md"), f.path)
  await assert.rejects(f.arm(), /symlink/)
  assert.equal(await readFile(join(f.root, "outside.md"), "utf8"), campaign)
})

test("ACT still open or an unaccepted baseline never advances the campaign", async (t) => {
  const f = await fixture(t)
  for (const pair of [
    ["Record: completed; outcome: accepted", "Record: open"],
    ["Baseline: accepted", "Baseline: pending"],
  ]) {
    const changed = campaign.replace(...pair)
    await writeFile(f.path, changed)
    await assert.rejects(f.arm(), /status field/)
    assert.equal(await readFile(f.path, "utf8"), changed)
  }
})

test("a changed pinned report after a failed admission cannot be re-delivered", async (t) => {
  const f = await fixture(t)
  const { ticket } = await f.arm()
  f.finish(ticket)
  f.failed.reply = true
  await assert.rejects(f.call({ action: "recover", ticket }), /lost reply/)
  const pending = await f.call({ action: "inspect" })
  await writeFile(join(f.root, pending.ref.path), "other candidate")
  f.failed.reply = false
  await assert.rejects(f.call({ action: "recover", ticket }), /pinned report changed/)
  assert.equal(f.issued.length, 1)
})

test("manual takeover keeps the ledger and late reports cannot reopen it", async (t) => {
  const f = await fixture(t)
  const { ticket } = await f.arm()
  await f.call({ action: "release", ticket })
  const manual = (await readFile(f.path, "utf8")).replace(election, "Mechanics: manual")
  await writeFile(f.path, manual)
  f.finish(ticket)
  await assert.rejects(f.call({ action: "recover", ticket }), /status field/)
  assert.equal(await readFile(f.path, "utf8"), manual)
  assert.equal(f.inbox.size, 0)
})
