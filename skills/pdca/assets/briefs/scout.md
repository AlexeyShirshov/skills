# SCOUT brief

Fill every slot; write `none` explicitly when it does not apply. The scout gathers facts and
pointers only — no recommendation, no verdict, no design choice.

- **identity**: task / `N` / `r` / `rv` / mode (`normal | autonomous`)
- **decision it unblocks**: one line — which PLAN, DO or CHECK question this gather answers
- **facts wanted**: numbered, each naming the place it is expected (`path`, `file:line`, or a command
  form this surface allows: `ls`/`cat`/`head`/`tail`/`wc`/`stat`/`sha256sum`/`command -v` and the
  read-only git literals). A build, test, helper run or tool-version query is outside it — write
  `unconfirmed — outside the scout surface` instead of ordering it
- **scope**: paths in bounds; `none` = the checkout the cycle works in
- **exclusions**: `none`, or what not to read (secrets only). On a **CHECK observation stream** the
  product deliverable **is in scope**: observe it where it lives — the checker cannot read it
- **observation pack** (CHECK stream only): one row per criterion — `observed | assumed |
  unverified` — with the pointer, and the observed artefact's SHA-256, size and line count; no prose
  beyond the rows
- **report**: one row per fact — `observed | unconfirmed`, each with its pointer; no prose beyond
  the rows, and never a fact invented to fill a row

Not in this brief: a verdict, a recommendation, a widened permission, permission to run builds or
tests.
