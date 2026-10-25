# egg-drop (campaign 1)

Status: met
disposition: finalized
Goal: met <=> mechanical gate PASS AND S_accept >= 9.000 AND final verify PASS, where S_accept = min(S_measure, S_verify); S = 0.30*s_physics + 0.20*s_constraints + 0.20*s_reliability + 0.15*s_materials + 0.10*s_specification + 0.05*s_iterations, s_i in [0,10], rubric anchors 0/5/10 from egg-drop-test.md:236-243; failures per egg-drop-test.md:268-273

Recipe: immutable measurement procedure, compact restatement (full text: `.pdca/egg-drop/charter-r1.md#2-recipe`, section «2. RECIPE»). (a) B0 snapshot = actual HEAD, pre-existing foreign dirt, allowed paths, spec content; no whole-repo hash, no retrospective `committed == tested`. (b) Gate infrastructure validated on positive + negative fixtures before any measurement. (c) Each measurement = immutable package `.pdca/egg-drop/rv1/mNNN/` holding answer.md, egg-drop-test.md, check_answer.py, used fixtures, `manifest.json` with SHA-256 of those inputs, gate report + run log + exit code, and the independent rubric; the hashes bind one measurement, they are not a repository audit. (d) Gate runs on the frozen answer; zero selected cases is an error, never PASS. (e) Independent assessor `pdca-check`, not the answer's author, receives only frozen spec + answer, the immutable scoring procedure and the mechanical report — never the author's self-score, expected gain, prior scores or another assessor's score. (f) The assessor covers the whole rubric AND every §7 failure condition separately; a structural PASS does not cancel a semantic violation. (g) Per category: score, answer-section pointer, applied §5 anchor, concrete justification.
Recipe anchors (original §5, 0/5/10, transcribed from read-only egg-drop-test.md:236-243; weights 30/20/20/15/10/5%): physics 0 gross formula errors / 5 correct with simplifications / 10 all correct and justified; constraints 0 >2 violated / 5 one violated / 10 all met; reliability 0 will certainly break / 5 survival 50–80% / 10 survival >90%; materials 0 arbitrary / 5 partial justification / 10 full physical justification; specification 0 no dimensions / 5 partial / 10 full with masses and dimensions; iterations 0 no improvement plan / 5 general ideas / 10 concrete plan with calculations. Intermediate 0.5 scores only by interpolation between adjacent anchors; an unsubstantiated number does not count as a met requirement.
Recipe scoring rules: decimal arithmetic; keep the exact value, print three decimals; compare with the threshold on the exact value, never round up. Uncertainty between two adjacent scores resolves to the lower. One cause cannot mechanically dock several categories (each affected category needs its own effect); style nitpicks outside the rubric do not lower a score; pretty formatting does not compensate a physics error; honestly disclosed model assumptions are not violations, while fabricated tests or an assumption passed off as a measurement are an evidence defect; a «probably» conclusion instead of a guarantee is allowed.
Recipe INVALID (absence of a valid measurement — not a zero score and not a failed DO by itself): checker and assessor saw different input snapshots; assessor saw the author's self-score or prior scores; inputs changed after freezing without a new measurement; checker changed between measurement and acceptance without a full re-run; missing log, exit code, input identification or mandatory scores; gate selected zero cases, crashed, or failed the fixture controls; other weights, anchors, formulas or rounding rules used.
Interpreter: /usr/bin/python3 (3.10.12), equivalent to the planned /usr/bin/python3.10 — probed at bootstrap: `/usr/bin/python3` is a symlink to `/usr/bin/python3.10`, both report Python 3.10.12, stdlib `json,re,hashlib,sys` import OK (`stdlib-ok`). Planned argv C1/C2 below are kept with `/usr/bin/python3.10` as written in the charter, since that path exists and is the same binary.

Allowed surface: experiments/egg-drop/answer.md, experiments/egg-drop/check_answer.py, experiments/egg-drop/fixtures/**, .pdca/status/egg-drop-1.md, .pdca/egg-drop/**
Floor: delta S >= 0.500   Target: 0.500 (baseline 0.000 + floor)
Preparation ref: .pdca/egg-drop/charter-r1.md@r1
Commit policy: none (user did not request a commit; repo rule AGENTS.md "commit only on explicit request")

| step | kind | parent | baseline | target | accepted | delta | verdict | commit | evidence |
| 1 | increment | — | 0.000 | 0.500 | 9.100 | +9.100 | accepted | — (Commit policy: none) | .pdca/egg-drop/rv1/m001/ (gate.json, selftest.json, manifest.json, rubric.json, accept.md) |
| 2 | verify | — | — | gate | pass | — | — | — | .pdca/egg-drop/rv1/verify-v001/ |

Current step: 2 (verify) — closed   Cycle: 1   Plan revision: 1   Contract: rv1   Attempt: 1/3
Baseline evidence: .pdca/egg-drop/rv1/baseline.md (S0=0.000, gate FAIL, no answer); accepted step 1 at `.pdca/egg-drop/rv1/m001/` (accepted S=9.100). Facts: HEAD 6636d3690c1c75833a7cc016a65372f5c20eea87; 67 dirty entries at bootstrap (68 after adding this campaign's baseline file; all foreign in-flight work, untouched); `experiments/` is untracked (0 files in `git ls-files`), `.pdca/` is tracked (18 files); spec `experiments/egg-drop/egg-drop-test.md` sha256 8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e, 289 lines; `experiments/egg-drop/` contains the spec only. Interpreter: /usr/bin/python3 (3.10.12), equivalent to the planned /usr/bin/python3.10.
Next-step seed: ranked named weaknesses from the m001 ACCEPT (not acceptance defects — seeds for the next step), each with its expected effect on the rubric category it belongs to:
(a) **reliability** — COM height vs P(bottom): the 105 g cradle sits 177–232 mm from the floor of a 290 mm box while `answer.md:311` justifies P(bottom)=0.96 by "low COM"; resolving the COM/tumble geometry (or re-deriving P(bottom) with the side 152 g / top 290 g risk) should lift reliability 8.5 → 9.0–9.5.
(b) **physics** — stage-wise deceleration model + cone crush stroke: replace the single uniform deceleration of M=0.458 kg at F_avg=276.8 N with the two real stages (105 g cradle over the 60 mm free stroke, then the cone block's 276.8 N threshold), and cap the cone stroke below 100 % of 96 mm (the ~20–25 % densification admitted at `answer.md:243`); removing both unjustified simplifications should lift physics 9.0 → 9.5–10.0.
(c) **materials** — quantitative cone buckling force and rubber-band stiffness: estimate the buckling force of one paper cone (~17.3 N at 3.4 g target) and the total stiffness of eight 120×3×1 mm bands over 60–165 mm; adding the quantitative mechanism link should lift materials 9.0 → 10.0.
(d) **specification** — the three blank/chain inconsistencies: cardboard qty 1 as 250×250×3 mm without the 290 mm side walls, five foam pads listed vs the sixth 18 mm bottom pad, 52 mm cradle width vs the 140×120×40 / 140×140×40 blanks; closing all three should lift specification 8.5 → 9.5–10.0.
(e) **physics** — peak factor k justification: k=1.30 (and the 1.30 → 1.15 iteration target) is assumed rather than derived from the crush curve; deriving it should secure the physics score above and unblock the iterations plan's own numbers.
Deferred: полные решения held-out сценариев B–F → trigger: отдельный запрос и новая кампания; реальные испытания → trigger: отдельный запрос на физическую валидацию и доступность ресурсов; CAD и покупки → trigger: явное разрешение пользователя в отдельной задаче.
Blockers: none
Protected/foreign: experiments/egg-drop/egg-drop-test.md (read-only input); every other path in the tree, including the pre-existing modified files; no commits
Rubric: accepted S=9.100 by independent pdca-check (session ses_e90e1b654ffew2T4qWLerBIFcC)
Tickets: —
Checkpoint: none — открытого checkpoint нет.
Pending approval ref: — (autonomous mode, no approval gate)
Approval record: — (autonomous)
## Stop verdict

- Outcome: met.
- Final accepted S: min(9.100, 9.250) = 9.100 >= 9.000.
- Mechanical gate: PASS; selftest 22/22; candidate G01-G12 PASS.
- §7: clean; оба независимых оценивания valid.
- Threshold: 9.000, unchanged.
- Floor: 0.500, unchanged.
- Initial baseline: 0.000.
- Accepted increment: +9.100. Verify не начисляет gain и не сдвигает baseline.
- Evidence: .pdca/egg-drop/rv1/m001/; .pdca/egg-drop/rv1/verify-v001/.
- Snapshot: m001, hash-stable; HEAD 6636d36.
- Filters unchanged; selected_cases: selftest=22, candidate=1.
- Commit policy: none; commit/push не выполнялись.

### Remainder to ideal

10.000 - 9.100 = 0.900. Оба оценщика снизили оценки в четырёх категориях: физическая корректность (упрощение стадий торможения, доступного хода и коэффициента пика); надёжность (недостаточное обоснование вероятности номинальной ориентации); материалы (нет количественной силовой характеристики конусов и резинок); детализация спецификации (несогласованности перечня картона, числа прокладок и размеров люльки).

Диагностические замечания verify: включение Mg в F_avg физически корректно и консервативно; округление E_res в тексте чувствительности отмечено оценщиком. Они не изменили пороги или вердикт; допуски контракта не пересматривались.

### Verification boundary

Физического drop test не было: проверен теоретический проект. Заявленные нагрузки при иных ориентациях: бок 152 g, верх 290 g. Выживание обосновывается для номинальной ориентации дном вниз; P1=0.943 - оценка модели, не экспериментально измеренная вероятность. Это раскрытие границ, не условие провала: якоря рубрики не требуют реального испытания.
Budgets: max 4 full cycles, 8 candidate measurements, 3 plan revisions per cycle, 3 failed CHECKs per revision, 2 targeted re-gathers at CHECK, 2 INVALID recoveries, 2 final verify runs, 90 min wall clock

## Charter refs

- `.pdca/egg-drop/charter-r1.md`@r1 — immutable campaign charter (goal, recipe, unit, floor, target), sha256 `b80d80343912724c8f2b9f249f2190c1f6edef123f4155c0c08f0ead372741b8`, 384 lines; supersedes nothing, superseded by nothing.
- `.pdca/egg-drop/rv1/baseline.md` — baseline evidence package, sha256 `b18f7e7e580a030db9976c373a8c55f3e18473b6d2fc82cf45c1ee2f6fba201d` (A1–A7 facts frozen; A8 appended after the decision arrived).
- Spec (read-only, protected): `experiments/egg-drop/egg-drop-test.md`, sha256 `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e`, 289 lines.

## Progress log

```text
2026-10-24T17:28:24Z | BOOTSTRAP | baseline | S0=0.000 gate=FAIL | .pdca/egg-drop/rv1/baseline.md
2026-10-24T17:29:37Z | BOOTSTRAP | charter r1 written | .pdca/egg-drop/charter-r1.md
2026-10-24T17:30:19Z | BOOTSTRAP | status running | .pdca/status/egg-drop-1.md
2026-10-24T17:36:12Z | PLAN | revision r1 | iteration 1/3 | PLAN ready (autonomous, no approval gate) | .pdca/egg-drop/charter-r1.md
2026-10-24T17:36:12Z | DO | revision r1 | iteration 1/3 | DO started | step 1 / D0 checker+controls
2026-10-24T17:36:12Z | DO | revision r1 | iteration 1/3 | D0 running | experiments/egg-drop/check_answer.py + fixtures
```

## Plan (r1)

Step 1, cycle 1, plan revision r1, attempt 1/3. Kind: increment. Contract rv1, charter `.pdca/egg-drop/charter-r1.md`@r1.

- **Goal of the step.** Produce a validly measured first accepted answer: mechanical gate `PASS` (all G01–G12) plus independent rubric, target `S_accept >= 0.500` against baseline `S0 = 0.000` (floor 0.500). Full first answer expected `S = 8.0–9.5` when the gate is PASS; the floor is the binding acceptance criterion, the 8.0–9.5 range is only an expectation, not a claim.
- **D-tasks.**
  - `D0` — checker + control fixtures (`experiments/egg-drop/check_answer.py`, `experiments/egg-drop/fixtures/**`); prerequisite to measurement, no credited gain of its own. State: active (this dispatch).
  - `D1` — `experiments/egg-drop/answer.md`: full Russian answer + one consistent `egg-drop-data-v1` JSON block; explicit resolution of the spec contradiction `egg-drop-test.md:152` vs `:160`. State: pending (not started in this dispatch).
  - `D2` — freeze measurement package `.pdca/egg-drop/rv1/m001/`, run C1/C2, independent rubric, accept/reject against the immutable target. State: pending.
- **Acceptance.** `E01` — selftest: known-good PASS, every declared mutant FAIL **at its assigned G-ID**, positive control (prohibition mentions only) PASS, exit 0, report `selftest.json`. `E02` — candidate answer: all G01–G12 rows present, any applicable FAIL excludes acceptance, exit 0, report `gate.json`.
- **Test strategy.** Known-good handwritten reference (arithmetically consistent, not a pre-scored 9/10 answer) + 20 declared mutants (one controlled defect each, each FAIL at its declared G-ID) + 1 positive control (forbidden materials only as prohibitions/negations → PASS). Every control is expanded by `--case all-declared`; a mutant that passes, or fails at a different ID, is a selftest failure. Zero selected cases is INVALID (exit 2), never PASS.
- **Docs plan.** Product answer in Russian, LF only; no other documentation is touched (no EN/RU pair exists, so translation sync is N/A).
- **Perf decision.** No benchmark: `egg-drop-test.md` grades a document and its physics, not software speed; the checker is a correctness oracle, and physical characteristics are verified by calculation, not by timing. Recorded as a deliberate exclusion, not an omission.
- **Reconnaissance decision.** Bounded probe = D0 harness proof (E01), <=15 min, <=2 implementation fixes; on failure — escalation, never measuring the answer with a non-working gate.
- **Unit execution mode.** Sequential, single tree, shared contract between answer schema, checker and fixtures; no worktrees, no parallel edits of the same contract.
- **Toolchain / lens.** `/usr/bin/python3.10` (3.10.12), stdlib only (`json, re, sys, hashlib, argparse, math, pathlib`); gates G01–G12 per charter §3; `# Scope` comment in the checker marks which rows are structural/declarative and are finally judged by the independent assessor; independent CHECK by `pdca-check`, not the answer's author.
- **Risks.** (a) Checker fitting the fixture instead of the contract — mitigated by the declared mutant→G-ID matrix and by not weakening any limit; (b) G02/G05/G06/G10–G12 are partly structural (keyword/fragment/declaration level) — the scope comment states this and the assessor owns semantic plausibility; (c) known-good is written by the checker author — CHECK must re-derive its arithmetic; (d) autonomous mode: no approval gate, a PLAN error can only be corrected by a later revision that keeps the criteria.
- **Budgets.** This dispatch: wall clock <=15 min probe for D0; campaign: max 4 cycles, 8 candidate measurements, 3 plan revisions per cycle, 3 failed CHECKs per revision, 2 re-gathers, 2 INVALID recoveries, 2 final verifies, 90 min total.

## Progress log (continued)

```text
2026-10-24T17:43:36Z | DO | revision r1 | iteration 1/3 | D0 selftest red (fixture generator collapsed LaTeX backslashes, 22/22 controls failed G01) exit=1 | .pdca/egg-drop/rv1/m001/selftest-red1.log
2026-10-24T17:44:24Z | DO | revision r1 | iteration 1/3 | D0 selftest red (slice-1: 12 controls wrongly accepted, m19 null overwritten) exit=1 | .pdca/egg-drop/rv1/m001/selftest-red2.log
2026-10-24T17:45:00Z | DO | revision r1 | iteration 1/3 | D0 selftest red (full checker: m15 failed G07+G08, duplicate ownership) exit=1 | /tmp/opencode/full1.json
2026-10-24T17:45:32Z | DO | revision r1 | iteration 1/3 | D0 selftest green exit=0 selected=22 ok=22/22 | /tmp/opencode/full2.json
2026-10-24T17:46:12Z | DO | revision r1 | iteration 1/3 | D0 E01 final selftest exit=0 selected=22 ok=22/22 gate=PASS | .pdca/egg-drop/rv1/m001/selftest.json
2026-10-24T17:47:30Z | DO | revision r1 | iteration 1/3 | D0 done (E01 met), D1 pending, D2 pending | .pdca/egg-drop/rv1/m001/argv-selftest.txt
```

## Durable state (after D0)

Current cycle: 1   Plan revision: 1   Attempt: 1/3   Contract: rv1

| unit | state | evidence |
|---|---|---|
| D0 checker + controls | done (E01 met: exit 0, 22/22 controls behaved as declared) | `.pdca/egg-drop/rv1/m001/selftest.json`, `selftest.log`, `argv-selftest.txt` |
| D1 `experiments/egg-drop/answer.md` | pending (not started in this dispatch) | — |
| D2 freeze m001 + C1/C2 + independent rubric + accept/reject | pending | — |

Defect history (DO implementation defects, stable keys; none is a CHECK finding):

| defect key | observed at | fix count | evidence | outcome |
|---|---|---|---|---|
| `DEF-fixture-json-escape` | r1 / attempt 1, run 1 | 1 | `selftest-red1.log` | fixed: fixture generator uses a lambda replacement so LaTeX backslashes survive |
| `DEF-fixture-null-overwrite` | r1 / attempt 1, run 2 | 1 | `selftest-red2.log` | fixed: the null total mass is applied after the recomputation step |
| `DEF-g08-double-owner` | r1 / attempt 1, run 3 | 1 | `/tmp/opencode/full1.json` | fixed: G08 no longer re-judges `results.n_load_g`; it requires design peak = recomputed peak (1 %) and <= 100 g |

Budget note: the reconnaissance probe planned <= 2 implementation fixes; 3 were needed before the
selftest turned green. Recorded as a deviation (see `red-first.md#deviations`), no gate limit was
weakened and no manifest declaration was changed to fit observed behaviour.

```text
2026-10-24T17:47:53Z | DO | revision r1 | iteration 1/3 | D0 E01 re-run after adding spec hash: exit=0 selected=22 ok=22/22 hashes=24 | .pdca/egg-drop/rv1/m001/selftest.json
```

```text
2026-10-24T17:55:53Z | DO | revision r1 | iteration 1/3 | D1 running | experiments/egg-drop/answer.md
2026-10-24T17:57:59Z | DO | revision r1 | iteration 1/3 | D1 done: draft gate exit=0 gate=PASS G01-G12 12/12, selected=1 | .pdca/egg-drop/rv1/m001/draft-gate.json
```

## Durable state (after D1, append-only)

Current cycle: 1   Plan revision: 1   Attempt: 1/3   Contract: rv1

| unit | state | evidence |
|---|---|---|
| D0 checker + controls | done (E01 met: exit 0, 22/22 controls behaved as declared) | `.pdca/egg-drop/rv1/m001/selftest.json`, `selftest.log`, `argv-selftest.txt` |
| D1 `experiments/egg-drop/answer.md` | done for the DO scope (deliverable written, draft gate green); freezing/measurement is D2 | `.pdca/egg-drop/rv1/m001/draft-gate.json` (exit 0, G01–G12 PASS), `draft-gate.log`, `argv-draft.txt`, answer sha256 `40a56cc82905a64da7d6104beec99565e5ef7b49d5fcfa29c94439a3882cd4c3` |
| D2 freeze m001 + C1/C2 + independent rubric + accept/reject | pending | — |

Draft-stage defect history (answer defects, stable keys; none is a CHECK finding):

| defect key | observed at | fix count | evidence | outcome |
|---|---|---|---|---|
| `DEF-g05-line-wrap-negation` | r1 / attempt 1, draft run 1 | 1 | `draft-gate.log` run 1, `draft-gate.json` run 1 | fixed: the prohibition sentence is split so each line with a forbidden-material word also carries its negation |
| `DEF-prose-number-drift` | r1 / attempt 1, draft run 2 (not caught by the gate) | 1 | `argv-draft.txt` run history | fixed: alternative #2 peak 190 g → 326 g, top-direction peak 238 g → 290 g, section 6 iteration/20 m arithmetic re-derived from the same formulas |

Note: the draft gate is not a measurement; it selects one case and does not freeze inputs.

## Progress log (D2)

```text
2026-10-24T17:58:40Z | DO | revision r1 | iteration 1/3 | D2 running — freeze package .pdca/egg-drop/rv1/m001/ (answer, spec, checker, fixtures/**) | .pdca/egg-drop/rv1/m001/manifest.json
2026-10-24T17:59:04Z | DO | revision r1 | iteration 1/3 | D2 freeze complete: 27 frozen inputs, all byte-identical to source (answer/spec/checker source_matches_frozen=true), fixtures 24/24 files | .pdca/egg-drop/rv1/m001/input-hashes.txt
2026-10-24T17:59:12Z | DO | revision r1 | iteration 1/3 | C1 selftest exit=0 selected=22 ok=22/22 gate=PASS diagnostics=0 (frozen fixtures tree) | .pdca/egg-drop/rv1/m001/selftest.json + selftest.log
2026-10-24T17:59:26Z | DO | revision r1 | iteration 1/3 | C2 answer exit=0 selected=1 gate=PASS G01-G12 12/12 non-PASS=[] | .pdca/egg-drop/rv1/m001/gate.json + gate.log
2026-10-24T18:00:20Z | DO | revision r1 | iteration 1/3 | D2 post-run integrity: 27/27 frozen hashes unchanged, post_run_hashes_match=true, working checker == frozen checker (d6260656...) | .pdca/egg-drop/rv1/m001/manifest.json#post_run_integrity
2026-10-24T18:01:10Z | DO | revision r1 | iteration 1/3 | D2 done — freeze + C1 + C2 (Gate infrastructure green, candidate gate PASS); rubric + accept/reject not in this dispatch | .pdca/egg-drop/rv1/m001/argv-measurement.txt
2026-10-24T18:01:10Z | CHECK | revision r1 | iteration 1/3 | DO → CHECK: handoff of the frozen package m001 for mechanical re-read + independent rubric (E03) and step decision (E04) | .pdca/egg-drop/rv1/m001/
```

Notices (cosmetic, same identity):

- C1 ran with `--fixtures .pdca/egg-drop/rv1/m001/fixtures` instead of the charter's
  `experiments/egg-drop/fixtures`, so the measured fixture tree is the frozen one (declared
  deviation in `argv-measurement.txt`, checker consumed the relocated tree unchanged, exit 0).
  C2 argv is exactly the planned one. No threshold, weight, formula or fixture declaration changed.
- D0's E01 report paths `selftest.json`/`selftest.log` are the charter-prescribed C1 output paths and
  were therefore overwritten by the m001 run. A replay of the same C1 argv on the working fixtures
  (`/tmp/opencode/d0-rerun.json`, exit 0, 22/22, gate PASS) differs from the current file only in the
  fixtures path prefix; all 24 hash values and all outcome fields are identical. D0's E01 outcome is
  preserved in substance; no D0 defect.

## Durable state (after D2, append-only)

Attempt identity: task=egg-drop, N=1, r=1, n=1   Current cycle: 1   Plan revision: 1   Attempt: 1/3   Contract: rv1
Measurement package: `.pdca/egg-drop/rv1/m001/` (frozen)   Manifest: `.pdca/egg-drop/rv1/m001/manifest.json`

| unit | state | evidence |
|---|---|---|
| D0 checker + controls | done (E01 met: selftest exit 0, 22/22 controls behaved as declared) | `.pdca/egg-drop/rv1/m001/selftest.json`, `selftest.log`, `argv-selftest.txt` |
| D1 `experiments/egg-drop/answer.md` | done for the DO scope; frozen into m001 (sha256 `40a56cc8...`) | `.pdca/egg-drop/rv1/m001/answer.md`, `argv-draft.txt` |
| D2 freeze m001 + C1/C2 | done: package frozen, post-run hashes unchanged, C1 exit 0 (22/22), C2 exit 0 (G01–G12 12/12 PASS) | `manifest.json`, `input-hashes.txt`, `argv-measurement.txt`, `selftest.json`/`.log`, `gate.json`/`.log` |
| D2 independent rubric + accept/reject (E03/E04) | pending — outside this dispatch, belongs to CHECK | — |

Frozen measurement facts:

- C1: exit=0, expected 0, selected_cases=22 (non-vacuous), gate=PASS, diagnostics=0.
- C2: exit=0, expected 0, selected_cases=1, gate=PASS, checks=12 (G01–G12 all PASS), non-PASS none.
- Manifest: 27 frozen inputs (`answer.md`, `egg-drop-test.md`, `check_answer.py`, 24 `fixtures/**` files),
  `input_hashes_sha256 = 22d09176f140f5f8910513dcb169326da1cc48b5a17dfc6749406da9f14411b8`,
  `post_run_hashes_match = true` (re-hash after both runs equals the manifest).
- Provenance: answer/spec/checker frozen copies byte-identical to source at freeze time; working checker
  `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` == frozen checker. C2 has no
  `--spec` argument; the checker hashed the working spec, whose bytes equal the frozen spec
  (`8a79d64b...`), so gate and frozen package saw the same spec.
- S is NOT computed here and the rubric is NOT judged here; no `met` claim is made by this dispatch.

Defect history: unchanged by this dispatch — no new DO implementation defect, no answer/checker/fixture
edit was made (freeze only). Counts stay at 3 checker/fixture fixes and 2 answer fixes recorded above.

## ACT record (step 1, bookkeeping, append-only)

```text
2026-10-24T18:12:44Z | DO | revision r1 | iteration 1/3 | D2 closed — freeze + C1 + C2 + independent rubric handed to CHECK; D2 unit done | .pdca/egg-drop/rv1/m001/manifest.json
2026-10-24T18:12:44Z | CHECK | revision r1 | iteration 1/3 | DO → CHECK — handoff line for this transition already recorded at 2026-10-24T18:01:10Z; not duplicated | .pdca/egg-drop/rv1/m001/
2026-10-24T18:12:44Z | CHECK | revision r1 | iteration 1/3 | CHECK stream: gather (recompute+integrity) done — read-only, no frozen input modified | .pdca/egg-drop/rv1/check-r1/{recompute.md,recompute.json,integrity.md,integrity.json}
2026-10-24T18:12:44Z | CHECK | revision r1 | iteration 1/3 | CHECK verdict: green (E01/E02/G01-G12 PASS, §7 violations: 0, loop-back none, new package not required, re-gather none) | .pdca/egg-drop/rv1/check-r1/verdict.md
2026-10-24T18:12:44Z | ACT | revision r1 | iteration 1/3 | ACT closed (step 1, bookkeeping) — verdict persisted verbatim; campaign ACCEPT (E03/E04) and any `met` decision are NOT taken here | .pdca/egg-drop/rv1/check-r1/verdict.md
2026-10-24T18:12:44Z | ACT | revision r1 | iteration 1/3 | Notice: D0 probe used 3 implementation fixes vs planned max 2; probe finished in budget, no limit or declaration widened | .pdca/egg-drop/rv1/m001/red-first.md#deviations
```

Current step: 1 (DO+CHECK green; awaiting campaign ACCEPT)
Cycle: 1
Plan revision: 1
Attempt: 1/3

No counter was reset by this record: `r` stays 1, `n` stays 1/3, the defect history below is unchanged
(6 fixes total: 3 checker/fixture + 3 answer/draft), and the campaign ACCEPT is still outstanding.

```text
2026-10-24T18:12:44Z | ACT | revision r1 | iteration 1/3 | state re-asserted after ACT record: current step=1, cycle=1, r=1, n=1/3, counters not reset, no step-table row written | .pdca/status/egg-drop-1.md#act-record
```

Checkpoint: step 1 mechanical evidence complete and green at `.pdca/egg-drop/rv1/m001/` (C1 exit 0,
selected_cases=22, 22/22 controls as declared; C2 exit 0, selected_cases=1, G01–G12 12/12 PASS;
27/27 frozen input hashes match the manifest pre/post), verdict at
`.pdca/egg-drop/rv1/check-r1/verdict.md`. The campaign rubric ACCEPT (E03/E04) and any `met` decision are
owned by the campaign parent — not done here, and S is not computed.

Next plan: the next action is the campaign-level independent rubric ACCEPT of the frozen m001; the step-table
row and the next step are added only after that decision.

Changed files (step 1, campaign egg-drop):

- `experiments/egg-drop/check_answer.py` — gate G01–G12 checker (stdlib only).
- `experiments/egg-drop/answer.md` — the candidate answer (Russian, one `egg-drop-data-v1` JSON block).
- `experiments/egg-drop/fixtures/**` — fixture manifest + known-good + 21 controls (20 mutants, 1 positive control) + generator.
- `.pdca/egg-drop/rv1/m001/**` — frozen measurement package (answer, spec, checker, fixtures, manifest, selftest, gate, argv, red-first, independent known-good).
- `.pdca/egg-drop/rv1/check-r1/**` — CHECK stream (recompute, integrity, verdict).
- `.pdca/status/egg-drop-1.md` — this status file.

Not touched by this dispatch: anything under `experiments/egg-drop/**` and `m001/**` (all frozen hashes
were re-verified unchanged after writing this record; see the final line of the progress log).

## Campaign ACCEPT (step 1, append-only)

```text
2026-10-24T18:20:12Z | STEP | revision r1 | iteration 1/3 | step 1 closed green: gate PASS, selftest 22/22, S=9.100 accepted | .pdca/egg-drop/rv1/m001/{gate.json,selftest.json,manifest.json,rubric.json,accept.md}
2026-10-24T18:20:12Z | ACCEPT | revision r1 | iteration 1/3 | campaign ACCEPT step 1: S=9.100, delta +9.100, floor 0.500 met, §7 clean | .pdca/egg-drop/rv1/m001/accept.md + rubric.json
```

Current step: 1 accepted — route decision pending   Cycle: 1   Plan revision: 1   Attempt: 1/3
No counter reset: `r` stays 1, `n` stays 1/3, defect history unchanged (6 fixes total: 3 checker/fixture
+ 3 answer/draft). Frozen-input integrity at ACCEPT: 27/27 manifest hashes of `m001` unchanged, no drift.

## Verify run v001 and STOP (append-only)

```text
2026-10-24T18:30:25Z | VERIFY | verify-v001 | V1 exit 0, 22/22 controls; V2 exit 0, G01-G12 PASS; independent S_verify=9.250; §7 clean; measurement valid; inputs hash-stable | .pdca/egg-drop/rv1/verify-v001/
2026-10-24T18:30:31Z | STOP | met | min(9.100,9.250)=9.100>=9.000; gate PASS; §7 clean; threshold and floor unchanged; disposition=finalized; no open checkpoint; verify gain=0 | .pdca/status/egg-drop-1.md
```

Durable state at STOP: current step 2 (verify) closed; status met; disposition finalized; no open
checkpoint; cycle 1, plan revision 1, attempt 1/3 (no counter reset by verify); defect history unchanged
(6 fixes total: 3 checker/fixture + 3 answer/draft); verified artifact for run `verify-v001` is
`.pdca/egg-drop/rv1/verify-v001/` (`verify-rubric.json`, `verify-review.md`, `verify-decision.json`,
the mechanical V1/V2 reports).
