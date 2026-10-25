# Measurement-integrity facts — package `rv1/m001`

Facts only. No verdict, no interpretation, no recommendation.

## 1. Manifest hashes vs the frozen files

`manifest.json` declares `input_count` = 27; entries present = **27**;
mismatches = **0**.

| # | file (package-relative) | size, B | manifest sha256 | actual sha256 | match |
|---|---|---|---|---|---|
| 1 | `answer.md` | 35049 | `40a56cc82905a64d…` | `40a56cc82905a64d…` | yes |
| 2 | `egg-drop-test.md` | 15194 | `8a79d64b3b38c4b2…` | `8a79d64b3b38c4b2…` | yes |
| 3 | `check_answer.py` | 45641 | `d62606562418fab9…` | `d62606562418fab9…` | yes |
| 4 | `fixtures/controls/m01-missing-section/answer.md` | 18311 | `b146328c1dba08d0…` | `b146328c1dba08d0…` | yes |
| 5 | `fixtures/controls/m02-section-order/answer.md` | 19182 | `57f2567de749c5d3…` | `57f2567de749c5d3…` | yes |
| 6 | `fixtures/controls/m03-missing-s4-item/answer.md` | 18948 | `2290635664ba0932…` | `2290635664ba0932…` | yes |
| 7 | `fixtures/controls/m04-mass-501/answer.md` | 19182 | `9a96df30dd6b0376…` | `9a96df30dd6b0376…` | yes |
| 8 | `fixtures/controls/m05-side-301/answer.md` | 19182 | `6a79319a6dc995b8…` | `6a79319a6dc995b8…` | yes |
| 9 | `fixtures/controls/m06-volume-300-cube/answer.md` | 19179 | `d7dfcf3bcdd11959…` | `d7dfcf3bcdd11959…` | yes |
| 10 | `fixtures/controls/m07-budget-501/answer.md` | 19183 | `79a124de50be6fc3…` | `79a124de50be6fc3…` | yes |
| 11 | `fixtures/controls/m08-build-31/answer.md` | 19184 | `872412de623062f2…` | `872412de623062f2…` | yes |
| 12 | `fixtures/controls/m09-metal-used/answer.md` | 19282 | `9d2111365543c117…` | `9d2111365543c117…` | yes |
| 13 | `fixtures/controls/m10-egg-glued/answer.md` | 19181 | `a3a798357b0344a1…` | `a3a798357b0344a1…` | yes |
| 14 | `fixtures/controls/m11-zero-stroke/answer.md` | 19174 | `a61c7f1d67d56332…` | `a61c7f1d67d56332…` | yes |
| 15 | `fixtures/controls/m12-wrong-velocity/answer.md` | 19177 | `3615ea69b3c47f28…` | `3615ea69b3c47f28…` | yes |
| 16 | `fixtures/controls/m13-wrong-energy/answer.md` | 19179 | `15d5ddcc32c34a91…` | `15d5ddcc32c34a91…` | yes |
| 17 | `fixtures/controls/m14-wrong-force/answer.md` | 19177 | `5c59558792e22236…` | `5c59558792e22236…` | yes |
| 18 | `fixtures/controls/m15-wrong-load/answer.md` | 19179 | `ad74043eb91f7b22…` | `ad74043eb91f7b22…` | yes |
| 19 | `fixtures/controls/m16-wrong-stress/answer.md` | 19177 | `bdeb73a6396b83b9…` | `bdeb73a6396b83b9…` | yes |
| 20 | `fixtures/controls/m17-wrong-eta/answer.md` | 19181 | `0703cc19a32a85ef…` | `0703cc19a32a85ef…` | yes |
| 21 | `fixtures/controls/m18-bad-probabilities/answer.md` | 19176 | `037b2f8e0f2987ae…` | `037b2f8e0f2987ae…` | yes |
| 22 | `fixtures/controls/m19-null-total-mass/answer.md` | 19181 | `8042f2c72b4f8d82…` | `8042f2c72b4f8d82…` | yes |
| 23 | `fixtures/controls/m20-unknown-material/answer.md` | 19505 | `7d51aa80efc3a5a8…` | `7d51aa80efc3a5a8…` | yes |
| 24 | `fixtures/controls/p01-prohibition-only/answer.md` | 19390 | `c7fbd4ac7953c114…` | `c7fbd4ac7953c114…` | yes |
| 25 | `fixtures/known-good/answer.md` | 17458 | `16cdb204ef645fdb…` | `16cdb204ef645fdb…` | yes |
| 26 | `fixtures/manifest.json` | 4852 | `adedef98e22ca68f…` | `adedef98e22ca68f…` | yes |
| 27 | `fixtures/tools/make_controls.py` | 14377 | `b31530519bb612ed…` | `b31530519bb612ed…` | yes |

Working tree vs frozen copy (path: `experiments/egg-drop/`):

| file | manifest sha (frozen) | frozen file sha | working file sha | all three equal |
|---|---|---|---|---|
| `answer.md` | `40a56cc82905a64d…` | `40a56cc82905a64d…` | `40a56cc82905a64d…` | yes |
| `egg-drop-test.md` | `8a79d64b3b38c4b2…` | `8a79d64b3b38c4b2…` | `8a79d64b3b38c4b2…` | yes |
| `check_answer.py` | `d62606562418fab9…` | `d62606562418fab9…` | `d62606562418fab9…` | yes |

* `input-hashes.txt`: 27 lines, 27 parsed entries;
  entries not matching the manifest = none; manifest entries missing there = none.
* Manifest `input_hashes_sha256` = `22d09176f140f5f8910513dcb169326da1cc48b5a17dfc6749406da9f14411b8`; package declaration `source_matches_frozen` = {'answer.md': True, 'egg-drop-test.md': True, 'check_answer.py': True}; `post_run_hashes_match` = True; `post_run_mismatches` = {}.

## 2. `selftest.json` (C1 report)

* `selected_cases` declared = **22**; case rows = **22**; distinct case names = 22;
  zero-case selection = **False**.
* `gate` field = `PASS`; `checks` array length = **0**; `diagnostics` = [].
* rows with `ok=true` = **22/22**; `ok=false` = none.
* rows where a mutant produced **more than one** FAIL id = none.
* expected-id mismatches = none; expected-status mismatches = none.
* `input_hashes` entries = 24; entries whose sha256 does not match the file on disk = none.

| case | expected_status | expected_id | observed_status | observed_ids | ok |
|---|---|---|---|---|---|
| `known-good` | PASS | — | PASS | — | True |
| `m01-missing-section` | FAIL | G01 | FAIL | G01 | True |
| `m02-section-order` | FAIL | G01 | FAIL | G01 | True |
| `m03-missing-s4-item` | FAIL | G02 | FAIL | G02 | True |
| `m04-mass-501` | FAIL | G04 | FAIL | G04 | True |
| `m05-side-301` | FAIL | G04 | FAIL | G04 | True |
| `m06-volume-300-cube` | FAIL | G04 | FAIL | G04 | True |
| `m07-budget-501` | FAIL | G04 | FAIL | G04 | True |
| `m08-build-31` | FAIL | G04 | FAIL | G04 | True |
| `m09-metal-used` | FAIL | G05 | FAIL | G05 | True |
| `m10-egg-glued` | FAIL | G05 | FAIL | G05 | True |
| `m11-zero-stroke` | FAIL | G06 | FAIL | G06 | True |
| `m12-wrong-velocity` | FAIL | G07 | FAIL | G07 | True |
| `m13-wrong-energy` | FAIL | G07 | FAIL | G07 | True |
| `m14-wrong-force` | FAIL | G07 | FAIL | G07 | True |
| `m15-wrong-load` | FAIL | G07 | FAIL | G07 | True |
| `m16-wrong-stress` | FAIL | G07 | FAIL | G07 | True |
| `m17-wrong-eta` | FAIL | G09 | FAIL | G09 | True |
| `m18-bad-probabilities` | FAIL | G10 | FAIL | G10 | True |
| `m19-null-total-mass` | FAIL | G03 | FAIL | G03 | True |
| `m20-unknown-material` | FAIL | G05 | FAIL | G05 | True |
| `p01-prohibition-only` | PASS | — | PASS | — | True |

Fixture manifest (`fixtures/manifest.json`, 22 controls) declares exactly the same (case, expected_status, expected_id)
triples as the selftest rows above: checked, 0 differences.

## 3. `gate.json` (C2 report)

* `selected_cases` = 1; `gate` = `PASS`; `diagnostics` = [].
* G01–G12 rows present: **12**; missing = none.

| id | status | expected (from report) |
|---|---|---|
| G01 | PASS | six level-2 sections in the required order, one egg-drop-data-v1 json block in section 2 |
| G02 | PASS | every mandatory section-4 item covered by a non-empty fragment in its own section |
| G03 | PASS | mass and cost independently recomputed, egg counted once, non-negative quantities |
| G04 | PASS | mass <= 500 g, cost <= $5.00, build <= 30 min, each side <= 300 mm, V <= 0.02 m3 |
| G05 | PASS | allowed materials only, plastic thickness declared, egg not glued, no forbidden material in use |
| G06 | PASS | six protected directions, non-zero braking stroke with a dimensional chain, soft egg attachment |
| G07 | PASS | velocity, time, energy, force, load, stress and absorption recomputed within 1% |
| G08 | PASS | design peak <= 100 g, 50/100/200 g sensitivity, spec contradiction at :152/:160 acknowledged |
| G09 | PASS | eta > 0.98, residual energy < 0.8 J, contact stress <= 25 MPa, 0 <= Eres <= Ek |
| G10 | PASS | P1,P3 in [0,1], P3 <= P1, explicit dependency/damage model |
| G11 | PASS | 2-3 alternatives compared on mass, cost, reliability; first iteration; 20 m recalculation |
| G12 | PASS | LaTeX formulas, consistent units, narrative numbers equal to the JSON |

Input hashes recorded in `gate.json`:

| path | sha256 |
|---|---|
| `/home/alex/sources/skills/.pdca/egg-drop/rv1/m001/answer.md` | `40a56cc82905a64da7d6104beec99565e5ef7b49d5fcfa29c94439a3882cd4c3` |
| `/home/alex/sources/skills/experiments/egg-drop/egg-drop-test.md` | `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e` |

C2 case row: {'case': 'candidate', 'expected_status': 'PASS', 'expected_id': None, 'observed_status': 'PASS', 'observed_ids': [], 'ok': True}

## 4. Commands C1 / C2: exit codes and logs

| id | suite | case | selected | expected_exit | observed_exit | gate | log exists | log bytes | log lines | log content |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | selftest | all-declared | 22 | 0 | 0 | PASS | True | 7 | 1 | `exit=0` |
| C2 | answer | candidate | 1 | 0 | 0 | PASS | True | 7 | 1 | `exit=0` |

Commands whose observed exit ≠ 0 or whose log is missing: **none**.
Report sizes: `gate.json` = 3786 B, `selftest.json` = 8654 B.

## 5. Frozen vs working `check_answer.py`

| source | sha256 |
|---|---|
| frozen `.pdca/egg-drop/rv1/m001/check_answer.py` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` |
| working `experiments/egg-drop/check_answer.py` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` |
| `manifest.inputs["check_answer.py"]` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` |
| `manifest.provenance.checker_sha256_working` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` |
| `manifest.provenance.checker_sha256_frozen` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` |

All five values equal: **True**.

---

**facts-only note.** This file reports observed values, hashes, counts and file sizes. It contains no PASS/FAIL
gate verdict, no rubric score, no ranking and no recommendation. `check_answer.py` was executed/frozen only as
an opaque subject for hashing and for its recorded reports; its source was not read for stream A.
