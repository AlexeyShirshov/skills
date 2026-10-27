# Collection status: the batch record and item outcomes

Reference for the status file of a collection. The phase rules stay in `../SKILL.md`; the write semantics are determined by the relevant phase's role; the designated driver coordinates
and `pdca-executor` performs physical writes on an explicit dispatch.

## File and content

File: `.pdca/status/collection-<slug>.md`. It contains:

- the input (the item list) and the `collection-id`;
- the table of groups: id, items, order, worktree, branch/ref, **status**
  (`pending` | `in-progress` | `done` | `incomplete` | `merged`): `merged` is an integrated `done`
  group (the transition is only `done` → `merged`); `incomplete` stays `incomplete` (never
  `merged`), and it has the stop reason ("the group is stopped"), the tip/ref, the preserved
  commits, the remainder and the patch path; a separate integration note `skipped` ("not selected
  for integration" + the reason) is **not** a group status and does not extend the enumeration;
- the table of items: id, group, branch, status (`pending` | `in-progress` | `done` |
  `incomplete`) and a **separate** phase readiness of the plan `plan_state` (`pending` | `running`
  | `ready`), the item's **form** and (for `cycle`) its **contract** and **overlay**, `cycle_id`
  (including `N`), the canonical status path of the item, `plan_revision` (`r`), the baseline ref,
  the footprint/requirement/prerequisite refs, the reason + patch path for `incomplete`, a link to
  the item's status file. `plan_state` (`ready` ≠ an approval and ≠ `done`) is not the execution
  status of the item but the readiness of its plan; the merge is at the group level, an item never
  has the status `merged`;
- per item: the **form** (`cycle` | `campaign`); for `cycle` — `plan_state`, the contract with its
  overlay and the pending approval ref pointer (normal mode); for `campaign` —
  `preparation_state` (`pending` | `ready`), the **single authoritative** `preparation_ref`
  (`.../preparation.md@r<k>`) and `campaign_ref` (optional before the baseline bootstrap, mandatory
  after); no item-level contract for a campaign — the contract/overlay of a concrete step is
  recorded in the step's durable record; the per-item `disposition` (`active` | `paused` |
  `finalized`) — an explicit field of **both** forms; the pending approval refs of the step;
- **three different things:** readiness (`plan_state`/`preparation_state`), the campaign runtime
  status (`Status`, `../../pdca-incremental/SKILL.md` §Campaign status) and the per-item
  `disposition` — not the same thing; readiness is not runtime and is not completion;
- an item record without a **form** is read as `cycle`; an unrecognised form value or an
  unresolvable contract/overlay — **fail closed**, not a guess;
- the decisions of the collection phases (the items' own PLANs and the ALL-barrier, clustering, the
  merge strategy) and the **PLAN revision vector** used for the schedule;
- the subsection **"General verification and recovery"** — the state of the **common verification**,
  not the status of a group or an item; the enumerations of groups/items are **not** extended by
  this:
  - the last result of the common `C` + the paths to the evidence (command, exit code, log,
    numbers);
  - the blocking reason (no report / environment failure / a confirmed defect) and the verification
    state (`blocked` | `unverified` | `pass`);
  - the **defect id** and the **history**: the applied fixes and the result of `C` after each (the
    identity of the defect is preserved across closures/restarts of the corrective cycle);
  - a link to the status file of the linked corrective cycle;
  - the **next allowed step**;
- Collection completeness (all original item goals accepted) / integrated-tree verification
  (independent CHECK verdict) / incomplete items and preserved results: these are distinct fields.

## Routing campaign outcomes

Campaign acceptance (`met`) and the common verification of the collection are different events. The
success or failure of a campaign **does not replace** the common `C` on the integrated tree: `C` is
performed by its own rules, and `unverified`/`blocked`/`pass` remain its separate state.

| Campaign runtime status | Per-item `disposition` | Item status | Note |
|---|---|---|---|
| `preparation_state=pending`, no runtime | `active` | `pending` | the barrier is not passed |
| `preparation_state=ready`, no runtime | `active` | `pending` | barrier-ready, not started; not `done` |
| `running` | `active` | `in-progress` | an accepted step does not make the item `done` |
| `met` (accepted) | `finalized` | `done` | the only success of a campaign |
| `blocked` | `paused` | `in-progress` | a checkpoint, not final |
| `stopped` | `paused` | `in-progress` | a checkpoint, not final |
| `unreachable`, the next target is admissible within the unchanged goal/boundaries | `paused` | `in-progress` | a checkpoint; resume is explicit |
| `unreachable`, the route is exhausted | `finalized` (failure) | `incomplete` + reason | only an explicit final unsuccessful disposition |
| `blocked`/`stopped` with an explicit final unsuccessful disposition | `finalized` (failure) | `incomplete` + reason | group-stop |
| the step is not accepted, a `repair`/new revision is in progress | `active` | `in-progress` | the campaign is not closed |
| a `verify` failure | `active` or `paused` by the step's route | `in-progress` | the threshold is not lowered |

Rules:

- no new item/group statuses are introduced: the existing `pending`/`in-progress`/`done`/
  `incomplete` are used; `disposition` is a per-item field, not a status;
- `done` is given **only by an accepted** `met`; the readiness of the charter or `running` do not
  give it;
- `blocked`/`stopped` are a checkpoint (`paused`, the item stays `in-progress`), not an automatic
  `incomplete`; an explicit resume is needed;
- `unreachable` with an admissible next target within the unchanged goal/boundaries is also a
  checkpoint;
- a final `incomplete` and the existing group-stop — only by an explicit final unsuccessful
  disposition: the remaining `pending` items of the group are marked `incomplete` with the reason
  "the group is stopped" and are not executed, the group is not merged, the other groups continue;
- a paused lane does not advance the dependent chain of its group;
- the success criteria, the threshold and the stop rules are not changed silently.

## Invariants

- `merged` is the status of an integrated `done` group (the transition is only `done` → `merged`);
  `incomplete` is never `merged`.
- `skipped` is an integration note "not selected for integration", **not** a group status, and it
  does not extend the enumeration.
- An `incomplete` group is not merged and its tip is not integrated; the results (refs, commits,
  patch) are preserved before and after cleanup.
- `blocked` is a state of the common verification, not an item/group status.
- The status/evidence paths are not deleted while they hold a pointer to the preserved results.
- The `tip` of a group = the last commit of its branch.
- One writer per record: the collection status is written by `pdca-executor` on the collection
  driver's dispatch; a campaign item's runtime status is written by `pdca-executor` on its
  designated item driver's dispatch — never by the driver directly.
