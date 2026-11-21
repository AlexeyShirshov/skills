# Optional executor mechanics

Elect at **status creation**, not once per turn. Treat each tool in the effective role tool
catalog separately. Missing or disallowed before election → existing manual procedure for that
operation. No probe task or installation. `pdca_handoff_v1` has its own unchanged election in
`act.md`. With none of the following tools, add no fields and do no extra work.

| Tool | Election | Replaces |
| --- | --- | --- |
| `pdca_check_packet_v1` | `packet-v1` | Assemble and verify the selected CHECK inputs |
| `pdca_record_event_v1` | `events-v1` | Record an exact phase decision and project a supported transition |
| `pdca_wait_v1` | `wait-v1` | Track an executor's already launched background shell |

Put `Adapters: packet-v1 events-v1 wait-v1` (only elected names), `Adapter owner: <executor session>`
and `Adapter evidence: .pdca/<task>/rv<k>` on separate lines in Current state (bounded cycle) or
Checkpoint (campaign). Use the base canonical English machine fields for coordinates; narrative
and reports retain their original language. Bind each operation to the exact status, evidence
directory and recorded `expect: {N,r,n,phase}` (also numeric `step` for campaigns). Keep the owner
session for the cycle. A revision changing the evidence root requires a reconciled checkpoint
update before using that directory. While a v1 ticket owns a boundary, finish/release it first.

## CHECK packet

Alongside the election, record `Packet requirements candidate N1/r1: {"path":"…","sha256":"…"}`
using the actual mode and coordinates, for the transport recipe from PLAN/CHECK. Keep the original
PLAN immutable. Only include method-selected or explicitly required inputs. This is
not a new independent pre-CHECK audit or a way to change CHECK's method. The recipe JSON contains
`mode` (`candidate` or `retrospective`), criterion IDs `criteria`, `slots` (`id`, `criterion`,
`kind`: `run`, `observation` or `evidence`), optional mandatory `inputPaths` and selected overlay
`sections` (`skill`, `heading`). Bind a changed recipe to the actual decision before using it.

The executor supplies the complete brief plus a pinned **manifest** in the elected evidence
directory. Manifest fields: `mode`, `brief` (pinned ref), `criteria`, frozen `candidate` identity,
`inputs` (workspace path/SHA-256 pairs), `required` (`id`, `criterion`, `ref`), `runs` (`log` slot
ID, `command`, integer `exit`, same `candidate`), and `sections`. Each ref is `{path,sha256}`.
Keep observations and logs under the evidence root; product inputs stay in their checkout.
`prepare` with a stable `key`, `expect` and `manifest` returns the normal `{path,sha256}` ref.
Fix a missing declared input before dispatch. Return substantive evidence insufficiency to CHECK.
For an existing authorized sibling checker, `send` with that same key, manifest, `expect` and
`checker` delivers the ref; **otherwise the driver alone dispatches it normally**. Choose one sender.
With `events-v1` elected, use `send` with `track: true` in the existing executor turn. This one call
prepares the packet, records the candidate and sends it. The packet asks the checker to append
`PDCA-RECORD <key>-verdict <kind>` to its full report. The adapter records that exact turn on
completion even after a reload. Route the resulting decision; do not call a second model to record
it. A checker that returns an unmarked report still owns the decision; use ordinary recording after
reconciling the receipt.
An `inspect` result includes the prepared ref and any pending/sent inbox ID. `sent` is admission,
never a verdict.

## Record a decision

The producer decides; the adapter persists. In an existing routing turn, pass the exact producer
`session`, final `message`, stable `key`, `kind`, and expected coordinates. Ask the producer to end
the completed report with `PDCA-RECORD <key> <kind>`. Only the elected executor or its actual
parent driver (with explicit `owner`) routes it. For its own DO or ACT event the executor can
instead pass a pinned `ref` during substantive work. A verification decision must come from
`pdca-check`, a plan from `pdca-planner`. Keep one key per logical decision even on retry.

Supported kinds: `plan` (pending revision), `do`, `check`, `act`, `retrospective` (record in
phase); `candidate` (DO→CHECK), `incomplete` (DO→ACT), `accepted` or `stop` (CHECK→ACT),
`contract` (CHECK→PLAN), and `revised-plan` (pin a genuine new contract, preserve the outgoing
attempt and previous revisions, reset for the new revision). Recording ACT does not close the
cycle or waive its retrospective. Approval, substantive repair budgets, escalation and final
closure keep the base procedures. For an unsupported operation use that manual route once, never
repeat an already projected event.

## Wait and take over

After `shell` returns a background ID, register it with `job`, `next` (one authorized continuation)
and `expect` before going idle. On its native notification, consume the recorded continuation.
`completed` includes the exit code when available; inspect the actual log. `interrupted` and
`unknown` do not establish a test result. Startup or `recover` reconciles the same job and can
wake the same owner to investigate lost work. Never launch a replacement on an unknown outcome.

On plugin loss **quiesce it first**. Read the original status: `pdca-op` identifies committed
events, `pdca-delivery` identifies CHECK recipient and message ID, and `PDCA wait <id>:` records
the shell and delivery. Compare pending IDs with the actual recipient inbox/history. Resume the
missing operation only: use the existing packet, continue an admitted CHECK, or recover the original
job/output. An unknown admission stays a blocker. Remove only the reconciled capability from
`Adapters:` (or mark manual); preserve receipts and other elections. A subsequent plugin reload
cannot reclaim a manually owned operation.
