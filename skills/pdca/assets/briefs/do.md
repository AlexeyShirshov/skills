# DO brief

Fill every slot; write `none` explicitly when it does not apply. An omitted evidence slot is exactly
what turns the next round into a re-gather.

- **identity**: task / `N` / `r` / `n/3` / `rv` / overlay / mode
- **plan**: `<status path>` plus the unit/step IDs this DO serves — **by reference**: the criteria,
  their rationale and the plan rows stay in the status file, which the executor reads from
  `## Durable state`; the fenced plan copy above that heading is not re-read on a follow-up DO
- **persistence** (first DO dispatch only): include the plan document `<plan-r<n>.md>` **verbatim**
  in the status file (a file copy, never a re-typed copy) inside a fence of at least four backticks,
  longer than any fence inside it, so the plan's own `##` headings never shadow a status section;
  then the `commands.json` projection, the staged `plan_lint` / `status_lint` receipts and gate 1 — a
  lint violation stops the dispatch before DO and reports the PLAN defect. The two shapes come from
  `plan_lint.py schema` / `status_lint.py schema`, not from the helper source
- **literal only**: footprint, prohibitions, capture shape and command `argv` travel verbatim; a
  criterion the plan does not name never enters this brief
- **footprint**: paths this DO may create or change; everything else is out of bounds
- **prohibitions**: no commit or push, no scope beyond the plan, no method the plan does not name
- **capture**: per frozen command `<stem>.out` / `<stem>.err` / `<stem>.rc`; a decisive row also writes
  `<stem>.identity` (the SHA-256 of its declared `identity` inputs, taken before the run; a directory
  digests the sorted `<sha256>  <path>` lines of its regular files); a merged stream is not evidence
  for a negative criterion, and an empty log without `.rc` proves nothing
- **index**: manifest `<path>` with a row per `required` ID, the `commands.json` projection, and the
  staged `plan_lint` / `status_lint` receipts — without them there is no candidate. On a new attempt
  the projection comes from `plan_lint.py fork-attempt`, never from editing its paths by hand
- **commands**: verbatim from the plan (`argv`, cwd, expected outcome); a substitution is a PLAN
  question, not a DO decision
- **documented commands**: every command block this DO puts into a doc (README, usage, help) is a
  frozen row — run it once with real arguments and capture it. A block with no row is a PLAN defect
  to report, not a row to invent and not a line to leave unrun
- **report**: changed / completed / evidence (exit status from `.rc`, key numbers, paths) / blockers
  / unfinished
- **delta**: only what changed since the previous DO of this cycle
