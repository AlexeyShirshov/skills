# ACT: closing, status and handoff

Reference for the ACT phase and the durable status file. Gate 4 stays in `../SKILL.md`.

## Closing order

ACT is mandatory and ends, in normal mode, with **two artefacts**: the cycle status file (finalized
and kept) and a ready message for the next session. In autonomous mode there is no second
artefact — the status file remains and the work continues in the same session.

1. **Durable lesson** — if the host provides durable memory, record 0–2 transferable lessons
   (optional; a no-op is normal). Only what is reusable beyond this workspace and has no natural
   home in the durable artefacts. A conclusion, not a narrative.
2. **Stable project rules** (if the project has them) — updated by `pdca-executor`, but **only** when
   the edit is pure bookkeeping that cannot affect the checked result. An instruction change that
   could affect verification belongs **before** the final CHECK (as DO work); otherwise the accepted
   verdict is invalid and the cycle loops back. The cycle state is not written there.
3. **Cycle status file — finalized by `pdca-executor`:** the driver passes the reports (CHECK
   verdict, executor run results, scout facts) and the executor fills in Done/Verified, Next plan
   and Changed artefacts, then runs the **status lint** (`references/plan.md` §Status lint) and
   corrects a `S002`–`S007` structural violation in the same bookkeeping edit before the file is
   kept.
4. **Status-file lifetime** — finalized and **kept**, never deleted: the next session's handoff in
   normal mode, the next PLAN's input in autonomous mode.
5. **Message for the next session** — last, nothing after it; **not printed in autonomous mode**.

ACT is bookkeeping only: it does not change product, tests or any checked artifact. Work found
during finalization is either done in DO and re-checked by the final CHECK, or invalidates the
accepted snapshot and loops back (implementation defect → DO, wrong plan → PLAN); it is never
slipped in under ACT. `rework`/`replan` are not part of ACT — they are loop-backs before ACT.

## Status file

Default path `.pdca/status/<task>-<N>.md`: `<task>` is a kebab slug, `<N>` the cycle number within
that task (grows only in ACT; loop-backs change `r`/`n`, not `<N>`). A plan may add a subdirectory or
a distinguishing suffix under `.pdca/status/`, but never leaves the workspace root.

Lifecycle:

1. **Creation, last step of PLAN before the start signal:** the plan (goal, criteria with
   verification methods, carrying claims, form/overlay, constraints, assumptions, decomposition and
   dependencies, means and access, risks/stop conditions, effort estimate and accounting) plus the
   log opened with `PLAN ready — awaiting user approval`.
2. **Progress — every event** of DO/CHECK.
3. **Replan** (CHECK → PLAN / DO → PLAN): a real revised plan bumps `r`, resets `n` to 1; an
   unchanged plan does not. The **same** file's plan section is rewritten; the outgoing failed
   attempt is recorded first, then `Replanned: <reason> (r <old>→<new>, iteration 1/3)`. No new file.
4. **Finalization in ACT:** Done/Verified, Next plan, Changed artefacts, pointers.

**Progress log** — append-only, one line per event, never edited retroactively:

```text
<UTC time> | <phase> | revision r | iteration n/3 | <event> | <evidence pointer>
```

The first field is the **observed** time from the available tool or environment records; where no
such record exists, mark the time unknown. The recording time is not the occurrence time: never
invent or reorder a timestamp, never reconstruct unsupported phase history, and keep historical
bytes as they are — a factual correction is added separately. The status file remains the recovery
authority; the log records the observed event.

Must log: `PLAN ready — awaiting user approval`; `plan approved — DO started`; each `D:` unit state
change; each `D:` closed (exit status + log path); DO → CHECK; each CHECK report; the verdict; each
CHECK failure/fix/loop-back with its defect key and applied fix count (pointers, not logs); loop-back
to DO / `Replanned` (with the outgoing failed attempt); an additive-prerequisite addition or a
`superseded→replacement` mapping; a step boundary and the accepted increment; escalation and its
outcome; `Recovered after compaction`; `Notice: …` (autonomous); ACT closed. Written **one event at
a time** by a short `pdca-executor` dispatch (or as the last step of one). The current state must
match the last log line.

**Unit states** (per `D:` unit): exactly one of `pending | running | blocked | done | superseded`.
`done` only when it satisfies gate 2; a blocker report leaves it `blocked`. An **additive
prerequisite** adds a new active unit; the original stays active (`blocked` on the dependency) with
criteria and remainder unchanged — not superseded, no mapping. Only an **actual scope replacement**
sets the original `superseded` and requires an explicit `<superseded unit> → <replacement>` mapping;
replacements are tracked active and carry all original criteria and residual work. The row records
criteria covered so gate 2 can verify all criteria are covered. The aggregate `D:` closes when every
active, non-superseded unit is `done` with evidence; `superseded` never counts as `done`, and the
replacement chain must resolve to active done units covering the preserved criteria (a missing
mapping/replacement, an orphan, a circular/self mapping or a pending `blocked` replacement ⇒ gate 2
rejected).

**Content — a brief handoff, not a report:**

- **Task**, cycle **goal**, **Current state** (phase, `n/3`, active `D:`/`P:`, in sync with the log),
  **Done/Verified** (filled at ACT).
- **Durable state** (mandatory): `Current cycle N`, `Plan revision r`, `Attempt n`, `rv` (criteria
  revision), `Form`, `Overlay`, `Mode` (`normal | autonomous`), `Status` (`pending | in-progress |
  blocked | stopped | done | incomplete`), `Phase` (`PLAN | DO | CHECK | ACT | EXIT`) and **Defect
  history** — explicit fields so the file alone restores the counters and the gate state, and
  `status_lint` can prove them present.
- **Defect history** — one row per stable **defect key** (a criterion/failure identity, independent
  of `r`): observed revisions/attempts, applied fix count, evidence/log pointers, last recurrence,
  escalation outcome (pointers, not sensitive content).
- **Form, overlay and carrying claims** — the declared form, the applied overlay (if any) and the
  claim IDs with their status.
- **DO units table** — unit | state | criteria covered | `superseded→replacement` (actual
  replacement only); an additive prerequisite keeps the original row active and adds a new one.
- **Decisions made** and why; accepted increments and the accumulated knowledge (findings with
  scope, conditions, evidence and limits; assumptions and unknowns; rejected/replaced approaches
  with reasons; the next decision).
- **Means and verification methods** selected by PLAN and the evidence each must return.
- **Risks / known issues** — severity and status; **Deferred + trigger** — what and by which signal
  to return; **Next plan** — the plan for the next cycle is not carried between sessions, so it
  lives here.
- **Changed artefacts** (paths) and **Pointers** (`file:line`, approvals, open questions) — without
  retelling content.
- **Progress log** (above).

For a campaign, the same file (or the campaign record it points to) additionally holds: accepted
steps with their credit, the current step, the shared counters, the effort accounting and the
checkpoint of the last step boundary. One writer only.

**Approval slots (normal mode only).** Two canonical fields, written by `pdca-executor`: `Pending
approval ref` — the durable pointer binding the stable task/`cycle_id`, the cycle `N`, plan revision
`r` and the acceptance-criteria set (the same pointer a caller-driven `plan_handoff` carries);
`Approval record` — the approval against that ref: approver, time, reason and the same identity,
including the user's stop-at-estimate choice when one was made (absent = no cutoff). A replan's
fresh ref points **by reference** to the original stop choice and its original clock
anchor/deadline; a new estimate does not reset that deadline, and the old plan approval authorizes
nothing new. No extra field or table is added. A
brief or a chat message is not the record. Both slots are absent in autonomous mode — an absent
value there is normal, not a gap or a blocker.

These sections answer the five recovery questions (`../SKILL.md` §Recovery). Write so the file alone
allows recovery.

## Message for the next session

Right after the status file is finalized — **normal mode only** — close the response with this block,
and nothing after it. In autonomous mode it is not printed and there is no wait state.

Signature, verbatim:

**Next instruction for the orchestrator — copy and paste into a new session.**

Then exactly one block to copy:

```text
Cycle <N> of the task "<task>" is closed.
Status: .pdca/status/<task>-<N>.md
Have pdca-scout report the status and the needed pointers on-demand; do not pull the previous session's history.
Next goal: <one line>.
Continue PDCA from PLAN.
```

Requirements: one line per meaning; workspace-relative paths; no diffs — only pointers and the goal.
Several closed cycles — reference the specific status. The `Status:` line always names the kept
status file, including a closed flow.
