# Red-first journal — m001 / D0 (checker + controls)

Step 1, plan revision r1, attempt 1/3, contract rv1. Working tree `/home/alex/sources/skills`.
Interpreters: `/usr/bin/python3.10` (3.10.12). All runs are recorded below in order, with the
exact command, UTC timestamp, exit code and a one-line observation.

## Declared expectations (written before the first run)

Suite `selftest`, selector `--case all-declared` expands to 22 controls: the handwritten
known-good, 20 declared mutants and 1 positive control. Aggregate expectation: **exit 0**,
`selected_cases = 22`, every case `ok = true`, report `gate = "PASS"`.

| case | expected status | expected G-ID |
|---|---|---|
| known-good | PASS | — |
| m01-missing-section | FAIL | G01 |
| m02-section-order | FAIL | G01 |
| m03-missing-s4-item | FAIL | G02 |
| m04-mass-501 | FAIL | G04 |
| m05-side-301 | FAIL | G04 |
| m06-volume-300-cube | FAIL | G04 |
| m07-budget-501 | FAIL | G04 |
| m08-build-31 | FAIL | G04 |
| m09-metal-used | FAIL | G05 |
| m10-egg-glued | FAIL | G05 |
| m11-zero-stroke | FAIL | G06 |
| m12-wrong-velocity | FAIL | G07 |
| m13-wrong-energy | FAIL | G07 |
| m14-wrong-force | FAIL | G07 |
| m15-wrong-load | FAIL | G07 |
| m16-wrong-stress | FAIL | G07 |
| m17-wrong-eta | FAIL | G09 |
| m18-bad-probabilities | FAIL | G10 |
| m19-null-total-mass | FAIL | G03 |
| m20-unknown-material | FAIL | G05 |
| p01-prohibition-only | PASS | — |

A mutant that passes, or fails at any other ID than the one declared above, is a selftest
failure. The expectation is fixed here and is not edited to match observed behaviour.

## Staged development (why the first run is red on purpose)

The checker is built in two slices so the harness itself is tested red-first:

1. **Slice 1** — structure (G01), independent mass/cost recomputation (G03) and hard limits
   (G04) only; G02 and G05–G12 are emitted as `NA: not implemented in the first slice`.
   Controls that violate an unimplemented row must be *wrongly accepted* by this slice.
2. **Slice 2** — the full G01–G12 implementation; the aggregate must become green without
   weakening any limit.

## Runs

### Run 1 — slice 1 against the declared controls (expected RED)

Command (cwd `/home/alex/sources/skills`):

```text
/usr/bin/python3.10 experiments/egg-drop/check_answer.py --repo /home/alex/sources/skills --suite selftest --case all-declared --fixtures experiments/egg-drop/fixtures --report .pdca/egg-drop/rv1/m001/selftest-red1.json
```

Declared expectation: exit 1, `gate = "FAIL"`, `ok = false` for every control whose assigned
row is not implemented in slice 1 (m03 → G02, m09/m10/m20 → G05, m11 → G06, m12–m16 → G07,
m17 → G09, m18 → G10), while m01/m02/m04–m08/m19 behave as declared and known-good/p01 pass.
That red result is the observable proof that the slice cannot certify the controls yet.

## Observed results (appended after each run; nothing above is edited)

### Run 1 — 2026-10-24T17:43:36Z, exit 1, RED (invalid controls, not a gate verdict)

Report `.pdca/egg-drop/rv1/m001/selftest-red1.json`, log `selftest-red1.log`. All 22 cases
reported `G01 FAIL` — the *fixtures* were broken: the fixture generator wrote the JSON block
through a `re.sub` **string** replacement, which collapsed the doubled backslashes of the LaTeX
pointer fragments, so every control's data block was invalid JSON (`Invalid \escape`). Known-good
itself (not regenerated) was the only PASS. Observation: a harness failure must never be read as
a property of the checker; the generator, not the gate, was wrong.

### Run 2 — 2026-10-24T17:44:24Z, exit 1, RED (the declared slice-1 red state)

Report `selftest-red2.json`, log `selftest-red2.log`. After fixing the generator: known-good PASS,
m01/m02 → G01, m04–m08 → G04 as declared, p01 PASS; m03 (G02), m09/m10/m20 (G05), m11 (G06),
m12–m16 (G07), m17 (G09), m18 (G10) were **wrongly accepted** because slice 1 does not implement
those rows — exactly the declared red behaviour. One additional generator bug surfaced: m19 passed
because the recomputation step overwrote `totals.total_mass_g = null` back to a number; the null is
now applied after the recomputation.

### Run 3 — 2026-10-24T17:45:00Z, exit 1, RED (full checker, one collateral failure)

Full G01–G12 implementation, report `/tmp/opencode/full1.json` (scratch run). 21/22 as declared;
m15-wrong-load failed at `G07` **and** `G08`, because G08 re-checked the declared `results.n_load_g`
(> 100 g) although that field is owned and recomputed by G07. Fix, recorded explicitly: G08 no
longer re-judges the declared load value; it now requires the *declared design peak* to equal the
independently recomputed peak (1 % tolerance) and to be ≤ 100 g. This is not a weakened limit —
the peak ≤ 100 g requirement is unchanged, the duplicate ownership that made one defect fail at
two IDs is removed, and the new design-peak-vs-recomputed-peak equality is stricter than before.
No declaration in the manifest was changed to fit observed behaviour.

### Run 4 — 2026-10-24T17:45:32Z, exit 0, GREEN

Report `/tmp/opencode/full2.json`: `gate = PASS`, `selected_cases = 22`, all `ok = true`,
`diagnostics = []`.

### Infrastructure probes (exit-2 paths must never yield PASS)

| probe | command target | exit | report |
|---|---|---|---|
| missing answer file | `--suite answer --answer /tmp/opencode/nope.md` | 2 | gate FAIL, selected 0, `INVALID: answer file not found` |
| selector matches nothing | `--suite selftest --case no-such-case` | 2 | gate FAIL, selected 0, `INVALID: zero cases selected` |
| empty manifest (vacuous run) | `--fixtures /tmp/opencode/emptyfix` | 2 | gate FAIL, selected 0, `INVALID: manifest declares no cases` |
| real violation through the answer suite | `--suite answer` on m04-mass-501 | 1 | gate FAIL, `G04` |

### Final run — 2026-10-24T17:46:12Z, exit 0, GREEN

Exact brief command, report `.pdca/egg-drop/rv1/m001/selftest.json`, log `selftest.log`:
`selected_cases = 22`, `gate = PASS`, `ok = 22/22`, `input_hashes = 23`, `diagnostics = []`.
Candidate-suite sanity run on known-good (`--suite answer`): exit 0, `gate = PASS`, all twelve rows
`G01–G12` present with status `PASS` (none `NA`, none silently skipped).

## Deviations

- The bounded reconnaissance probe planned **<= 2 implementation fixes**; the D0 harness needed
  **3** (two fixture-generator bugs, one checker ownership fix) before turning green. All three are
  recorded above with their evidence; the probe still met E01 within the 15-minute bound, so no
  escalation was triggered. Recorded as a budget deviation for CHECK, not as a PASS claim.
- `experiments/egg-drop/fixtures/tools/make_controls.py` is an extra file inside the allowed
  `fixtures/**` surface; it only regenerates the controls from the handwritten known-good and is
  not consumed by the gate at run time.


### Final re-run — 2026-10-24T17:47:53Z, exit 0, GREEN

The checker changed after run 4 (the consumed spec file is now recorded in `input_hashes`), so the
frozen report was regenerated by the same brief command: `selected_cases = 22`, `gate = PASS`,
`ok = 22/22`, `input_hashes = 24` (manifest + spec + 22 controls). The known-good answer-suite
sanity run also re-ran: exit 0, all twelve rows `G01–G12` = `PASS`.
