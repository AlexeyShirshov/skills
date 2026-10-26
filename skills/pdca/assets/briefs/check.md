# CHECK brief

Fill every slot; write `none` explicitly when it does not apply. The plan and the status travel **by
reference** — the checker reads `.pdca/**` itself, so a restated table adds no reach.

- **identity**: task / `N` / `r` / `n/3` / `rv` / form / overlay
- **plan**: `<status path>` and the criterion IDs of this round — **by reference**: the rows live in
  the status file; a restated table adds no reach and drifts from it. Read its **durable state,
  carrying claims and progress log**; the plan text inside it is a copy of the plan file you already
  hold by reference
- **manifest**: `<path>` — the index CHECK opens first
- **observation pack**: `<path>` — the scout's per-criterion `observed | assumed | unverified` rows,
  bound to the frozen result identity; the **only** channel for anything outside `.pdca/**`, the
  deliverable included. Missing pack = re-gather, not a CHECK round.
- **read scope**: `.pdca/**` only — this brief names no product path and asks for no product artefact
- **read budget**: the manifest, the pack and **one `decisive` row per criterion**; the verdict names
  the files it opened, and a whole-tree ingestion is a finding about the round
- **carrying claims**: their IDs, kept separate from the quality axes
- **counters and defect history**: `n/3`, prior findings with their stable keys and outcomes
- **evidence root**: `.pdca/<task>/rv<k>/`
- **delta**: what changed since the previous CHECK of this revision, not the history (a re-check
  judges the delta plus the same pack, not the whole evidence tree; dispatch it in a **fresh
  session** — the previous verdict travels by pointer)
- **output**: verdict; matrix `met | unmet | unverified` with a pointer per row; findings with their
  carrying-claim IDs; verification limits; routing (implementation defect → DO, wrong plan → PLAN);
  and for a re-gather the exact append instruction for the same manifest
