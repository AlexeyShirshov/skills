// Independent, elected operations. Neither the presence of the v1 tool nor a
// provider name implies that a particular operation is available or owned here.
import { createHash, randomUUID } from "node:crypto"
import { createReadStream } from "node:fs"
import { readFile, realpath, stat, link, unlink, open } from "node:fs/promises"
import { dirname, join, relative, resolve, sep } from "node:path"
import { isDeepStrictEqual } from "node:util"

const sha = (bytes) => createHash("sha256").update(bytes).digest("hex")
const must = (ok, msg) => {
  if (!ok) throw Error(msg)
}
const obj = (properties, required) => ({ type: "object", properties, required, additionalProperties: false })
const str = { type: "string" }
const num = { type: "integer", minimum: 0 }
const refSchema = obj({ path: str, sha256: { type: "string", pattern: "^[0-9a-f]{64}$" } }, [
  "path",
  "sha256",
])
const coord = obj(
  { phase: { enum: ["PLAN", "DO", "CHECK", "ACT"], type: "string" }, N: num, r: num, n: num, step: num },
  ["phase", "N", "r", "n"],
)
const common = { status: str, evidence: str, owner: str }
const tools = {
  "packet-v1": [
    "pdca_check_packet_v1",
    "Verify and pin the CHECK packet against the elected evidence manifest.",
    obj(
      {
        ...common,
        key: str,
        expect: coord,
        manifest: refSchema,
        checker: str,
        track: {
          type: "boolean",
          description: "Record DO→CHECK and a signed checker decision using elected events-v1",
        },
        action: { type: "string", enum: ["prepare", "send", "inspect"] },
      },
      ["status", "evidence", "key"],
    ),
  ],
  "events-v1": [
    "pdca_record_event_v1",
    "Record an exact phase decision once in the elected cycle status.",
    obj(
      {
        ...common,
        key: str,
        expect: coord,
        kind: {
          type: "string",
          enum: [
            "plan",
            "revised-plan",
            "contract",
            "do",
            "candidate",
            "incomplete",
            "check",
            "accepted",
            "stop",
            "act",
            "retrospective",
          ],
        },
        session: str,
        message: str,
        ref: refSchema,
      },
      ["status", "evidence", "key", "expect", "kind"],
    ),
  ],
  "wait-v1": [
    "pdca_wait_v1",
    "Register or reconcile an already launched shell job of this executor.",
    obj(
      {
        ...common,
        action: { type: "string", enum: ["register", "inspect", "recover", "release"] },
        job: str,
        next: str,
        expect: coord,
      },
      ["status", "evidence", "action", "job"],
    ),
  ],
}
const statusRE = /^\.pdca\/status\/[A-Za-z0-9][A-Za-z0-9_-]{0,99}\.md$/
const evidenceRE = /^\.pdca\/[A-Za-z0-9][A-Za-z0-9_-]{0,99}\/rv[1-9]\d*$/
const validKey = (s) => typeof s === "string" && /^[a-zA-Z0-9_-]{1,128}$/.test(s)
const validRef = (r) => r && typeof r.path === "string" && /^[a-f0-9]{64}$/.test(r.sha256)
const json = JSON.stringify

async function checkedPath(root, path) {
  const full = resolve(root, path)
  must(
    typeof path === "string" &&
      relative(root, full) === path &&
      path &&
      !path.startsWith(".." + sep) &&
      full === (await realpath(full)) &&
      (await stat(full)).isFile(),
    "expected a regular workspace file",
  )
  return full
}

// Publish by link, not overwrite. A lost status write can reuse the same file.
async function publish(root, evidence, prefix, bytes, authorize) {
  const ref = { path: `${evidence}/${prefix}-${sha(bytes)}.md`, sha256: sha(bytes) }
  const path = join(root, ref.path),
    dir = dirname(path)
  must(dir === (await realpath(dir)), "invalid evidence directory")
  await authorize("edit", path)
  const tmp = join(dir, ".packet-" + randomUUID()),
    f = await open(tmp, "wx", 0o600)
  try {
    await f.writeFile(bytes)
    await f.sync()
    try {
      await link(tmp, path)
    } catch (e) {
      if (e.code !== "EEXIST") throw e
    }
    must(sha(await readFile(await checkedPath(root, ref.path))) === ref.sha256, "pinned artifact differs")
    const d = await open(dir, "r")
    try {
      await d.sync()
    } finally {
      await d.close()
    }
  } finally {
    await f.close()
    await unlink(tmp)
  }
  return ref
}

function section(body, heading) {
  const all = [...body.matchAll(/^(#{1,6}) (.+?)\r?$/gm)]
  const selected = all.filter((h) => h[2] === heading)
  must(selected.length === 1, "missing or ambiguous overlay section: " + heading)
  const h = selected[0],
    next = all.find((v) => v.index > h.index && v[1].length <= h[1].length)
  return body.slice(h.index, next?.index)
}

function receiptParts(messages, job) {
  let launch, terminal
  for (const m of messages) {
    if (
      m.type === "synthetic" &&
      m.metadata?.source === "shell" &&
      m.metadata.shellID === job &&
      ["completed", "cancelled", "error", "failed"].includes(m.metadata.state)
    )
      terminal = m
    if (m.type !== "assistant" || m.agent !== "pdca-executor") continue
    for (const p of m.content)
      if (p.type === "tool" && p.name === "shell" && p.state.status === "completed") {
        const line = p.state.content?.[0]?.text ?? ""
        const hit = /^Command moved to the background \(shell ID: (sh_[a-zA-Z0-9]+)\)\.\r?\nPID: (\d+)/.exec(
          line,
        )
        if (hit?.[1] === job) launch = { message: m.id, pid: Number(hit[2]) }
      }
  }
  return { launch, terminal }
}

async function processIdentity(pid) {
  try {
    const [boot, proc] = await Promise.all([
      readFile("/proc/sys/kernel/random/boot_id", "utf8"),
      readFile(`/proc/${pid}/stat`, "utf8"),
    ])
    const fields = proc.slice(proc.lastIndexOf(")") + 2).split(" ")
    if (["Z", "X"].includes(fields[0]) || !/^\d+$/.test(fields[19])) return null
    return boot.trim() + ":" + fields[19]
  } catch {
    return null
  } // Absence never proves a successful exit.
}

export async function installMechanics(ctx, { root, ledger, serial, info, fences }) {
  const configured = ctx.options?.capabilities
  const enabled = Object.keys(tools).filter(
    (cap) =>
      (configured === undefined || (Array.isArray(configured) && configured.includes(cap))) &&
      (cap !== "packet-v1" || typeof ctx.skill?.list === "function"),
  )
  const watches = new Map(),
    prefix = `mechanics/wait/${sha(root)}/`
  const reviews = new Map(),
    reviewPrefix = `mechanics/check/${sha(root)}/`
  const indexKey = (b) => prefix + sha(b.status + ":" + b.key)
  const settled = (s) =>
    s && (s.released || s.delivery === "native" || (s.delivery === "admitted" && s.state !== "unknown"))
  async function retire(b, s) {
    if (settled(s)) {
      const k = indexKey(b)
      await ctx.storage.remove?.(k)
      watches.delete(k)
    }
    return s
  }
  const authorize = async (owner, action, path, agent = "pdca-executor") =>
    ctx.permission.assert({ sessionID: owner, agent, action, resources: [path], save: [] })
  const tx = (base, action, extra = {}) => ledger(root, { op: "mechanics", ...base, action, ...extra })
  const waitHint = (b) => `pdca.wait.${sha(b.status).slice(0, 16)}`
  const readRef = async (base, r, allowProduct = false, verifyOnly = false) => {
    must(
      validRef(r) && (allowProduct || r.path.startsWith(base.evidence + "/")),
      "expected evidence path and SHA-256",
    )
    await authorize(base.owner, "read", resolve(root, r.path))
    const path = await checkedPath(root, r.path)
    if (verifyOnly) {
      const hash = createHash("sha256")
      for await (const chunk of createReadStream(path)) hash.update(chunk)
      must(hash.digest("hex") === r.sha256, "changed evidence: " + r.path)
      return
    }
    const bytes = await readFile(path)
    must(sha(bytes) === r.sha256, "changed evidence: " + r.path)
    return bytes
  }

  async function packet(base, i, owner) {
    let previous = await tx(base, "receipt", { key: i.key })
    if (i.action === "inspect") return previous
    if (i.action === "send") {
      must(validKey(i.checker) && i.expect, "checker and coordinates required")
      if (i.track) {
        must(
          enabled.includes("events-v1") && i.key.length <= 115,
          "tracking requires events-v1 and a short key",
        )
        await tx({ ...base, cap: "events-v1" }, "scope")
        await authorize(owner.id, "pdca_record_event_v1", base.status)
      }
      const dst = await info(i.checker),
        driver = await info(owner.parentID)
      must(dst.agent === "pdca-check" && dst.parentID === driver.id, "expected an existing sibling checker")
      await ctx.permission.assert({
        sessionID: driver.id,
        agent: driver.agent,
        action: "subagent",
        resources: ["pdca-check"],
        save: [],
      })
      const fresh = !previous
      if (fresh) previous = await packet(base, { ...i, action: "prepare" }, owner)
      const { ref } = previous,
        id = `msg_${sha([root, base.status, i.key, ref.sha256].join(":"))}`
      let pending = previous.delivery
      if (pending)
        must(
          pending.id === id && pending.checker === dst.id && !!pending.track === !!i.track,
          "packet already assigned",
        )
      if (pending?.stage === "sent") return previous
      const args = { key: i.key, ref, expect: i.expect }
      const ack = async () => ({
        ref,
        delivery: await tx(base, "sent", {
          ...args,
          previous: pending,
          delivery: { ...pending, stage: "sent" },
        }),
      })
      if (pending && (await ctx.session.context({ sessionID: dst.id })).some((m) => m.id === id)) return ack()
      // Re-run preflight before an unsent dispatch; no runs or scout tasks are repeated.
      if (!fresh) {
        const again = await packet(base, { ...i, action: "prepare" }, owner)
        must(isDeepStrictEqual(again.ref, ref), "packet changed before delivery")
      }
      const fence = sha(json(await fences(owner.id)))
      if (pending) must(fence === pending.fence, "new instruction since CHECK dispatch")
      else {
        const k = reviewPrefix + sha(id),
          review = {
            base,
            key: i.key,
            checker: dst.id,
            id,
            ref,
            manifest: i.manifest,
            prior: i.expect,
            track: !!i.track,
            expect: { ...i.expect, phase: "CHECK" },
            fence,
          }
        await ctx.storage.set(k, review)
        reviews.set(k, review)
        pending = await tx(base, "sending", {
          ...args,
          delivery: { id, checker: dst.id, stage: "pending", fence, track: !!i.track },
        })
      }
      must(sha(json(await fences(owner.id))) === pending.fence, "new instruction before CHECK admission")
      await ctx.session.prompt({ sessionID: dst.id, id, text: json(ref), delivery: "queue" })
      return ack()
    }
    const manifest = JSON.parse(await readRef(base, i.manifest))
    const { mode = "candidate", criteria, inputs = [], required, runs = [], sections = [] } = manifest
    must(
      ["candidate", "retrospective"].includes(mode) &&
        Array.isArray(criteria) &&
        criteria.length &&
        criteria.every(validKey) &&
        new Set(criteria).size === criteria.length,
      "missing or ambiguous criterion IDs",
    )
    must(
      typeof manifest.candidate === "string" &&
        manifest.candidate.trim() &&
        Array.isArray(required) &&
        required.length &&
        Array.isArray(inputs) &&
        Array.isArray(runs) &&
        Array.isArray(sections),
      "incomplete CHECK manifest",
    )
    const checker = i.checker ? await info(i.checker) : null
    must(
      owner.parentID && (!checker || (checker.agent === "pdca-check" && checker.parentID === owner.parentID)),
      "expected checker under the same driver",
    )
    const readable = (ref) =>
      authorize(checker?.id ?? owner.parentID, "read", join(root, ref.path), "pdca-check")
    const current =
      previous?.delivery?.track && previous.delivery.stage === "pending"
        ? { ...i.expect, phase: "CHECK" }
        : i.expect
    const contractRef = await tx(base, "requirements", { expect: current, mode })
    const recipe = JSON.parse(await readRef(base, contractRef))
    await readable(contractRef)
    must(
      isDeepStrictEqual(recipe.criteria, criteria) &&
        isDeepStrictEqual(recipe.sections ?? [], sections) &&
        recipe.mode === mode &&
        Array.isArray(recipe.slots) &&
        recipe.slots.length,
      "wrong CHECK recipe",
    )
    must(
      (recipe.inputPaths ?? []).every((p) => inputs.some((r) => r.path === p)),
      "missing declared candidate input",
    )
    const brief = (await readRef(base, manifest.brief)).toString("utf8")
    must(brief.trim(), "empty CHECK brief")
    await readable(i.manifest)
    await readable(manifest.brief)
    for (const input of inputs) await readRef(base, input, true, true)
    const slots = new Map()
    must(
      recipe.slots.every(
        (s) =>
          validKey(s.id) &&
          criteria.includes(s.criterion) &&
          ["run", "observation", "evidence"].includes(s.kind),
      ) && new Set(recipe.slots.map((s) => s.id)).size === recipe.slots.length,
      "invalid required slot declaration",
    )
    for (const item of required) {
      must(
        validKey(item.id) && !slots.has(item.id) && criteria.includes(item.criterion),
        "invalid required evidence slot",
      )
      await readRef(base, item.ref, false, true)
      await readable(item.ref)
      slots.set(item.id, item)
    }
    for (const run of runs)
      must(
        slots.has(run.log) &&
          typeof run.command === "string" &&
          run.command.trim() &&
          Number.isInteger(run.exit) &&
          run.candidate === manifest.candidate,
        "incomplete run receipt or candidate mismatch",
      )
    const missing = recipe.slots.filter(
      (s) =>
        !slots.has(s.id) ||
        slots.get(s.id).criterion !== s.criterion ||
        (s.kind === "run" && !runs.some((run) => run.log === s.id)),
    )
    must(!missing.length, "missing required evidence: " + missing.map((s) => s.id).join(", "))
    const inventory = await ctx.skill.list()
    const available = Array.isArray(inventory) ? inventory : inventory.data
    must(Array.isArray(available), "unavailable installed skill catalog")
    const skill = (id) => {
      const found = available.filter((s) => s.id === id)
      must(found.length === 1 && typeof found[0].path === "string", "missing installed skill: " + id)
      return found[0]
    }
    const contract = async (name) => {
      const file = join(dirname(skill("pdca").path), "references", name)
      await authorize(owner.id, "read", file)
      return readFile(file, "utf8")
    }
    const parts = [await contract("check.md")]
    if (mode === "retrospective") {
      must(!sections.length, "retrospectives have no overlay sections")
      parts.push(section(await contract("act.md"), "Retrospective (mandatory, ACT)"))
    }
    for (const sel of sections) {
      must(["pdca-coder", "pdca-dotnet"].includes(sel.skill), "unknown selected overlay")
      const entry = skill(sel.skill)
      await authorize(owner.id, "read", entry.path)
      parts.push(section(await readFile(entry.path, "utf8"), sel.heading))
    }
    parts.push(
      "## Cycle brief",
      `mode: ${mode}`,
      brief,
      `Coordinates: ${json(i.expect)}\nManifest: ${json(i.manifest)}\n` +
        json({ candidate: manifest.candidate, criteria, inputs, required, runs, requirements: contractRef }),
    )
    if (i.track) {
      must(mode === "candidate", "track supports candidate CHECK only")
      parts.push(
        `Preserve your full independent report. On a matching decision only, append one final line:\n` +
          `PDCA-RECORD ${i.key}-verdict <kind>\nUse accepted only for CHECK → ACT acceptance, stop for terminal CHECK → ACT, ` +
          `contract for CHECK → PLAN. Otherwise use check (report only; driver routes).`,
      )
    }
    parts.push("<!-- end CHECK handoff -->\n")
    const ref = await publish(root, base.evidence, "check", Buffer.from(parts.join("\n\n")), (a, p) =>
      authorize(owner.id, a, p),
    )
    await readable(ref)
    return tx(base, "commit", { key: i.key, expect: i.expect, mode, requirements: contractRef, ref })
  }

  async function record(base, i, owner, actor) {
    const role =
      {
        plan: "pdca-planner",
        "revised-plan": "pdca-planner",
        contract: "pdca-check",
        check: "pdca-check",
        accepted: "pdca-check",
        stop: "pdca-check",
        retrospective: "pdca-check",
      }[i.kind] ?? "pdca-executor"
    let ref = i.ref
    if (i.session || i.message || role !== "pdca-executor" || actor.id !== owner.id) {
      must(validKey(i.message) && validKey(i.session), "completed producer session and message required")
      const source = await info(i.session)
      must(
        owner.parentID &&
          source.parentID === owner.parentID &&
          source.agent === role &&
          (role !== "pdca-executor" || source.id === owner.id),
        "incorrect decision producer",
      )
      const msg = (await ctx.session.context({ sessionID: source.id })).find((m) => m.id === i.message)
      const texts = msg?.content?.filter((p) => p.type === "text") ?? []
      must(
        msg?.type === "assistant" &&
          msg.agent === role &&
          msg.finish === "stop" &&
          !msg.error &&
          texts.length === 1 &&
          texts[0].text.trimEnd().endsWith(`\nPDCA-RECORD ${i.key} ${i.kind}`),
        "decision does not authorize the named event",
      )
      ref = await publish(root, base.evidence, "report", Buffer.from(texts[0].text), (a, p) =>
        authorize(owner.id, a, p),
      )
    } else await readRef(base, ref, false, true)
    return tx(base, "commit", { key: i.key, kind: i.kind, expect: i.expect, ref })
  }

  const setWait = (b, old, wait) => tx(b, "update", { key: b.key, previous: old, wait })
  async function reconcile(b, manual = false, event) {
    let s = await tx(b, "inspect", { key: b.key })
    if (!s || s.released || s.delivery === "native" || (s.delivery === "admitted" && s.state !== "unknown"))
      return s
    const owner = await info(b.owner)
    must(owner.agent === "pdca-executor" && owner.parentID === b.parent, "wait owner changed")
    await authorize(b.owner, "pdca_wait_v1", b.status)
    await authorize(b.owner, "edit", join(root, b.status))
    const msgs = await ctx.session.context({ sessionID: b.owner })
    const { terminal } = receiptParts(msgs, b.key)
    if (!isDeepStrictEqual(s.expect, b.expect) || s.next !== b.next || s.pid !== b.pid)
      throw Error("wait registration changed")
    if (terminal) {
      // Native shell delivery already wakes this executor; never send a second continuation.
      return setWait(b, s, {
        ...s,
        state: terminal.metadata.state === "completed" ? "completed" : "interrupted",
        exit: terminal.metadata.exit ?? null,
        message: terminal.id,
        delivery: "native",
      })
    }
    if (s.delivery === "admitted") return s
    if (s.deliveryID && msgs.some((m) => m.id === s.deliveryID))
      return setWait(b, s, { ...s, delivery: "admitted" })
    if (
      event?.type === "shell.exited" &&
      event.data.id === b.key &&
      event.location?.directory === root &&
      ["running", "awaiting-receipt"].includes(s.state) &&
      ["exited", "killed", "timeout"].includes(event.data.status)
    ) {
      s = await setWait(b, s, {
        ...s,
        state: event.data.status === "exited" ? "completed" : "interrupted",
        exit: event.data.exit ?? null,
        delivery: "await-native",
      })
    }
    if (s.state === "running" && s.identity && (await processIdentity(s.pid)) === s.identity) return s
    if (!manual && ["running", "awaiting-receipt"].includes(s.state)) return s // native delivery can follow exit
    // Only recovery/startup reports a lost handle. Never rerun the command.
    if (["running", "awaiting-receipt"].includes(s.state) || (s.delivery === "await-native" && manual))
      s = await setWait(b, s, {
        ...s,
        state: s.delivery === "await-native" ? s.state : "unknown",
        delivery: "pending",
        deliveryID: `msg_${sha([root, b.owner, b.status, b.key].join(":"))}`,
      })
    if (s.delivery === "pending") {
      if (!isDeepStrictEqual(await fences(b.owner), b.fences)) return s
      await ctx.session.prompt({
        sessionID: b.owner,
        id: s.deliveryID,
        delivery: "queue",
        text:
          `PDCA recovery: ${b.key}: ${s.state}; exit=${s.exit ?? "unknown"}. Reconcile its original output; do not relaunch. ` +
          `Status: ${b.status}. Authorized next action after a verified outcome: ${s.next}`,
      })
      return setWait(b, s, { ...s, delivery: "admitted" })
    }
    return s
  }

  async function wait(base, i, owner) {
    must(/^sh_[a-zA-Z0-9]+$/.test(i.job), "exact shell handle required")
    const index = prefix + sha(base.status + ":" + i.job)
    let b = watches.get(index)
    const old = await tx(base, "inspect", { key: i.job })
    if (i.action === "inspect") return old
    if (i.action === "release") {
      must(old && old.delivery !== "pending", "reconcile pending admission before release")
      if (
        ![...watches.values()].some((w) => w.status === base.status && w.key !== i.job) &&
        ctx.session.instructions?.entry?.remove
      )
        await ctx.session.instructions.entry.remove({ sessionID: owner.id, key: waitHint(base) })
      return retire(
        { ...base, key: i.job },
        await setWait({ ...base, key: i.job }, old, { ...old, released: true }),
      )
    }
    if (i.action === "recover") {
      if (settled(old)) return old
      must(b && old, "no registered wait")
      return retire(b, await reconcile(b, true))
    }
    must(
      i.action === "register" && i.next?.trim() && i.next.length <= 2000 && i.expect,
      "invalid wait registration",
    )
    if (old) {
      must(
        old.next === i.next && isDeepStrictEqual(old.expect, i.expect) && (b || settled(old)),
        "conflicting wait registration",
      )
      return old
    }
    const { launch, terminal } = receiptParts(await ctx.session.context({ sessionID: owner.id }), i.job)
    must(launch, "not a background shell launched by this executor")
    b = {
      ...base,
      key: i.job,
      parent: owner.parentID,
      fences: await fences(owner.id),
      next: i.next,
      expect: i.expect,
      pid: launch.pid,
    }
    await ctx.storage.set(index, b)
    watches.set(index, b)
    const identity = await processIdentity(launch.pid)
    let s = await setWait(b, null, {
      state: identity ? "running" : "awaiting-receipt",
      next: i.next,
      expect: i.expect,
      ...launch,
      identity,
      delivery: "waiting",
    })
    // The native notification supplies the result. A bounded instruction supplies
    // the registered continuation even if compaction lost the original tool call.
    await ctx.session.instructions?.entry?.put?.({
      sessionID: owner.id,
      key: waitHint(base),
      value:
        `On a shell result, use its ID to find the registered PDCA wait in ${base.status}. ` +
        "If present and still authorized, follow its recorded next action once. Never relaunch a lost job.",
    })
    if (terminal) s = await reconcile(b)
    return retire(b, s)
  }

  for (const cap of enabled) {
    const [name, description, input] = tools[cap]
    await ctx.tool.transform((editor) =>
      editor.add({
        name,
        description,
        input,
        options: { permission: name, codemode: false },
        async execute(i, context) {
          return serial(async () => {
            must(statusRE.test(i.status) && evidenceRE.test(i.evidence), "invalid PDCA locator")
            const actor = await info(context.sessionID),
              owner = await info(i.owner ?? actor.id)
            must(
              actor.agent === context.agent &&
                owner.agent === "pdca-executor" &&
                (actor.id === owner.id || (cap === "events-v1" && actor.id === owner.parentID)),
              "executor or its routing driver required",
            )
            await ctx.permission.assert({
              sessionID: actor.id,
              agent: actor.agent,
              action: name,
              resources: [i.status],
              save: [],
              source: { type: "tool", messageID: context.messageID, id: context.id },
            })
            await authorize(owner.id, i.action === "inspect" ? "read" : "edit", join(root, i.status))
            const base = { status: i.status, evidence: i.evidence, owner: owner.id, cap }
            await tx(base, "scope")
            if (cap !== "wait-v1") must(validKey(i.key), "stable event key required")
            const result =
              cap === "events-v1"
                ? await record(base, i, owner, actor)
                : cap === "packet-v1"
                  ? await packet(base, i, owner)
                  : await wait(base, i, owner)
            return { content: json(result) }
          })
        },
      }),
    )
  }
  async function observeReview(k, b) {
    const { base, checker, id, ref } = b
    const owner = await info(base.owner),
      source = await info(checker)
    must(
      owner.agent === "pdca-executor" && source.parentID === owner.parentID && source.agent === "pdca-check",
      "review participants changed",
    )
    await authorize(owner.id, "pdca_check_packet_v1", base.status)
    await authorize(owner.id, "edit", join(root, base.status))
    const saved = await tx(base, "receipt", { key: b.key })
    if (!saved?.delivery || saved.delivery.id !== id || !isDeepStrictEqual(saved.ref, ref)) return
    if (saved.delivery.stage === "pending") {
      await packet(
        base,
        { key: b.key, action: "send", expect: b.prior, checker, manifest: b.manifest, track: b.track },
        owner,
      )
    }
    if (!saved.delivery.track) {
      await ctx.storage.remove?.(k)
      reviews.delete(k)
      return
    }
    if (!enabled.includes("events-v1")) return
    await authorize(owner.id, "pdca_record_event_v1", base.status)
    const key = b.key + "-verdict",
      writer = { ...base, cap: "events-v1" }
    if (!(await tx(writer, "receipt", { key }))) {
      if (sha(json(await fences(owner.id))) !== b.fence) return
      const msgs = await ctx.session.context({ sessionID: checker })
      const idx = msgs.findIndex((m) => m.type === "user" && m.id === id)
      if (idx < 0) return
      const turn = msgs.slice(idx + 1)
      const next = turn.findIndex((m) => m.type === "user" || m.type === "synthetic" || m.type === "idle")
      if (next < 1 || turn[next].type !== "idle" || turn[next].outcome !== "succeeded") return
      const m = turn[next - 1],
        parts = m.content?.filter((p) => p.type === "text") ?? []
      if (m.type !== "assistant" || parts.length !== 1) return
      const [marker, token, kind] = parts[0].text.trimEnd().split("\n").at(-1).split(" ")
      if (
        marker !== "PDCA-RECORD" ||
        token !== key ||
        !["accepted", "check", "contract", "stop"].includes(kind)
      )
        return
      await record(writer, { key, kind, expect: b.expect, session: checker, message: m.id }, owner, owner)
    }
    await ctx.storage.remove?.(k)
    reviews.delete(k)
  }
  const watchReview = (k, b) =>
    serial(() => observeReview(k, b)).catch((e) => console.warn(`[pdca CHECK] ${b.key}: ${e.message}`))
  let after
  if (enabled.includes("wait-v1"))
    do {
      const page = await ctx.storage.scan({ prefix, after, limit: 100 })
      for (const { key, value } of page.entries) watches.set(key, value)
      after = page.next
    } while (after)
  if (enabled.includes("packet-v1"))
    do {
      const page = await ctx.storage.scan({ prefix: reviewPrefix, after, limit: 100 })
      for (const { key, value } of page.entries) reviews.set(key, value)
      after = page.next
    } while (after)
  const run = (b, recovery, event) =>
    serial(async () => retire(b, await reconcile(b, recovery, event))).catch((e) =>
      console.warn(`[pdca wait] ${b.key}: ${e.message}`),
    )
  return {
    restore() {
      for (const b of watches.values()) void run(b, true)
      for (const [k, b] of reviews) void watchReview(k, b)
    },
    async event(e) {
      if (
        ![
          "session.synthetic",
          "session.inbox.delivered",
          "shell.exited",
          "session.execution.succeeded",
        ].includes(e.type)
      )
        return
      for (const b of watches.values())
        if (b.owner === e.data?.sessionID || b.key === e.data?.id) await run(b, false, e)
      if (e.type === "session.execution.succeeded")
        for (const [k, b] of reviews) if (b.checker === e.data.sessionID) await watchReview(k, b)
    },
  }
}
