# Read a PDCA result

[Русский](../ru/guide/read-the-result.md)

If the agent says a run is over, use the status file and evidence to distinguish accepted work from an incomplete or unverified result.

1. Open the reported status file. Read the original task and PLAN before the CHECK record. Your supplied criteria are the acceptance set, not an editable paraphrase.
2. In CHECK, trace each mandatory criterion to the evidence it needs. `met` means the evidence supports it; `unmet` means the result fails it; `unverified` means the evidence is insufficient. Neither of the latter two permits acceptance.
3. In ACT, confirm what actually closed. A passing campaign step doesn't prove the whole campaign; a collection with an unfinished item isn't fully done even if the merged subset passes. A pause preserves a checkpoint. `STOP` closes the run without acceptance.

PDCA keeps the candidate in its checkout. Look under `.pdca/` for proof such as run logs, measurements, or observations, not copies of changed source files. A report's path and SHA-256 identify the exact report; they don't prove the candidate works. Existing evidence counts when the relevant inputs and conditions still apply.

Some PLAN outcomes go straight to ACT without DO or CHECK: undetermined criteria, an unmeasurable goal under the available means, proven infeasibility under the constraints, or an already-established requested result. For the last case, inspect the derivation rather than looking for a PASS.

For method selection and failure routing, see the [technical CHECK reference](../../skills/pdca/references/check.md).
