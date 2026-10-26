# DO brief

Fill every slot; write `none` explicitly when it does not apply. An omitted evidence slot is exactly
what turns the next round into a re-gather.

- **identity**: task / `N` / `r` / `n/3` / `rv` / overlay / mode
- **plan**: `<status path>` plus the unit/step IDs this DO serves — **by reference**: the criteria,
  their rationale and the plan rows stay in the status file, which the executor reads
- **literal only**: footprint, prohibitions, capture shape and command `argv` travel verbatim; a
  criterion the plan does not name never enters this brief
- **footprint**: paths this DO may create or change; everything else is out of bounds
- **prohibitions**: no commit or push, no scope beyond the plan, no method the plan does not name
- **capture**: per frozen command `<stem>.out` / `<stem>.err` / `<stem>.rc`; a merged stream is not
  evidence for a negative criterion, and an empty log without `.rc` proves nothing
- **index**: manifest `<path>` with a row per `required` ID, the `commands.json` projection and the
  staged `plan_lint` receipt — without them there is no candidate
- **commands**: verbatim from the plan (`argv`, cwd, expected outcome); a substitution is a PLAN
  question, not a DO decision
- **report**: changed / completed / evidence (exit status from `.rc`, key numbers, paths) / blockers
  / unfinished
- **delta**: only what changed since the previous DO of this cycle
