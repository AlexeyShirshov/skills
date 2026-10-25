# CHECK verdict — step 1, r1, n=1

Recorded at: 2026-10-24T18:12:09Z
Persisted verbatim from `pdca-check` (the bookkeeping executor did not re-judge, re-score or modify
any verdict content; only the header, the timestamp and the evidence-path list below were added).

```text
verdict: green — E01 PASS, E02 PASS, G01..G12 = PASS (12/12), §7 violations: 0
E01: known-good PASS (23/23 independently confirmed), 20/20 mutants FAIL at exactly their assigned G-ID,
     positive control (prohibition-only) PASS, selected_cases=22, exit 0, red-first progression proven (runs 1-3 exit 1 -> run 4 exit 0).
     Probe deviation (3 fixes vs planned 2) accepted: probe finished in budget, no limit widened, no manifest declaration changed to fit.
E02: gate.json all G01-G12 PASS, selected_cases=1, exit 0; 27/27 frozen inputs match manifest pre/post; checker unchanged (d6260656…); C2 argv unmodified.
Semantic reconciliation: headings/order, §4 coverage, sums (398 g + 60 g egg = 458 g; $3.11), limits (250x250x290 mm, V=0.018125 m3, 28 min),
stroke chains (290/250/165 mm), full physics model incl. 50/100/200 g sensitivity and :152/:160 contradiction, allowlist + unglued egg,
P1=0.943/P3=0.730 dependency model, 3 alternatives on mass/cost/reliability, first iteration + 20 m, data<->prose consistency, §7 absent.
Accepted notes (cosmetic, break no row): answer.md:132 stroke_chain_mm.bottom_foam 9.0 mm vs the 18 mm layer (9 mm is the compressed travel, stated at :82,:295);
answer.md:284 beta=0.13 -> prose 0.78 J vs recomputed 0.765 J (auxiliary prose, conclusion unchanged); answer.md:53,104 cardboard blank 250x250x3 mm qty 1 with 165 g row total (sums hold).
Loop-back: none. New measurement package: not required. Re-gather: none.
Evidence: .pdca/egg-drop/rv1/m001/{answer.md,manifest.json,selftest.json,gate.json,known-good-independent.md,red-first.md,argv-*.txt},
          .pdca/egg-drop/rv1/check-r1/{recompute.md,recompute.json,integrity.md,integrity.json}.
```

## Evidence paths

Measurement package (frozen, step 1 / rv1 / m001):

- `.pdca/egg-drop/rv1/m001/answer.md`
- `.pdca/egg-drop/rv1/m001/manifest.json`
- `.pdca/egg-drop/rv1/m001/selftest.json` (and `.log`)
- `.pdca/egg-drop/rv1/m001/gate.json` (and `.log`)
- `.pdca/egg-drop/rv1/m001/known-good-independent.md`
- `.pdca/egg-drop/rv1/m001/red-first.md`
- `.pdca/egg-drop/rv1/m001/argv-selftest.txt`
- `.pdca/egg-drop/rv1/m001/argv-draft.txt`
- `.pdca/egg-drop/rv1/m001/argv-measurement.txt`
- `.pdca/egg-drop/rv1/m001/input-hashes.txt`

CHECK stream artifacts (this directory):

- `.pdca/egg-drop/rv1/check-r1/recompute.md`
- `.pdca/egg-drop/rv1/check-r1/recompute.json`
- `.pdca/egg-drop/rv1/check-r1/integrity.md`
- `.pdca/egg-drop/rv1/check-r1/integrity.json`
- `.pdca/egg-drop/rv1/check-r1/verdict.md` (this file)
