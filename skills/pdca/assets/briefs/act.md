# ACT brief

Bookkeeping only: no product, test or checked artifact changes.

- **identity**: task / `N` / `r` / `n` / `rv`
- **accepted verdict**: the check verdict pointer and the matrix it accepted
- **record**: conclusions, limitations, accepted assumptions, decisions, handoff
- **manifest**: the same evidence generation; append the dispositions CHECK returned, never rewrite
  or delete a row
- **status file**: append the verdict and the ACT section, finalize `Phase: EXIT`, keep the file
- **status lint**: `<receipt path>` — run `status_lint.py check` on the finalized file; a structural
  violation (`S002`–`S007`) is corrected as bookkeeping in the same edit and the file is linted again
- **report**: what was appended, the final counters and both lint exit statuses, and every limitation
  that stays open
