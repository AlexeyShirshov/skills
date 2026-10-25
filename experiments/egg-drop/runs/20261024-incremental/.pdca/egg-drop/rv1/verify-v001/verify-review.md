# Verify run v001 — second independent rubric evaluation (isolated)

Run: `verify-v001`, package `m001` (frozen), campaign `egg-drop`, contract `rv1`.
Evaluator: second independent assessor, isolated from the first evaluation.
Machine-readable block: `.pdca/egg-drop/rv1/verify-v001/verify-rubric.json` (verbatim, values unchanged).
Weights and anchors: rubric `egg-drop-test.md` §5 (`0.30 / 0.20 / 0.20 / 0.15 / 0.10 / 0.05`, anchors 0 / 5 / 10,
interpolation only between adjacent anchors). Decimal arithmetic, three printed decimals, no rounding up.

## Inputs received

Exactly the five files of `.pdca/egg-drop/rv1/verify-v001/verify-inputs.json` and nothing else:

- `.pdca/egg-drop/rv1/m001/egg-drop-test.md` — frozen prompt, sha256 `8a79d64b…`
- `.pdca/egg-drop/rv1/m001/answer.md` — frozen answer, sha256 `40a56cc8…`
- `.pdca/egg-drop/rv1/m001/manifest.json` — frozen measurement manifest, sha256 `ee7c59bf…`
- `.pdca/egg-drop/rv1/verify-v001/verify-gate.json` — V2 mechanical report (G01–G12)
- `.pdca/egg-drop/rv1/verify-v001/selftest.json` — V1 control-suite report (22 controls)

## Per-criterion scores

| criterion | weight | score | applied anchor | evidence pointers |
|---|---|---|---|---|
| physics | 0.30 | 9.0 | interpolated 5..10 | `answer.md:203-303` |
| constraints | 0.20 | 10.0 | 10: all constraints satisfied | `answer.md:51-73`, `answer.md:103-129` |
| reliability | 0.20 | 9.0 | interpolated 5..10 | `answer.md:294-342` |
| materials | 0.15 | 9.0 | interpolated 5..10 | `answer.md:12-16`, `answer.md:51-65`, `answer.md:241-258`, `answer.md:343-368` |
| specification | 0.10 | 9.0 | interpolated 5..10 | `answer.md:45-201` |
| iterations | 0.05 | 10.0 | 10: concrete plan with calculations | `answer.md:369-392` |

Justifications (as given by the evaluator, restored to full sentences):

- **physics 9.0 (interpolated 5..10)** — all formulas and numbers reproduce within 1 %; the peak force of
  the system `F_peak` and the egg's own load `F_egg` are separated; sensitivity over `k` and `n_crit` is
  shown. −1.0 for merging the 60 mm free suspension stroke and the 96 mm cone crush into one stroke with
  100 % use of the cone height.
- **constraints 10.0 (anchor 10: all constraints satisfied)** — mass 458.0 g ≤ 500 g, sides
  250×250×290 mm ≤ 300 mm, volume 0.018125 m³ ≤ 0.02 m³, cost $3.11 ≤ $5.00, build 28 min ≤ 30 min,
  materials only from the allowed list, egg not glued.
- **reliability 9.0 (interpolated 5..10)** — P1 = 0.943 for the nominal bottom-first landing and
  P3 = 0.730 for three drops with damage accumulation; −1.0 for a strong dependence on the 0.96
  no-tumble probability for a blunt 250×250×290 mm box at 152 g side and 290 g top loads.
- **materials 9.0 (interpolated 5..10)** — the physical role of all 12 materials and the dissipation
  mechanisms are explained and compared with three alternatives, but the buckling force of the paper
  cones and the rubber-band stiffness are not derived from material properties.
- **specification 9.0 (interpolated 5..10)** — all masses, prices, part dimensions and the closed 290 mm
  and 250 mm chains are given; −1.0 for blank-table inaccuracies: a single 250×250×3 mm cardboard sheet
  for the whole body, five 20 mm foam sheets for six sides with an 18 mm bottom layer, and a 4×4 cone
  matrix of 240 mm against a 204 mm gap between the side foam.
- **iterations 10.0 (anchor 10: concrete plan with calculations)** — concrete first-iteration
  calculations (two-stage block, `k` down to 1.15, peak down to 70.9 g; the 364 mm and 515 g proof
  against symmetric top reinforcement) and a full 20 m recomputation (v = 19.81 m/s, E_k = 89.86 J,
  d_min = 200 mm, chains 334 mm and 299 mm).

## Arithmetic

```text
S = 0.30*9.0 + 0.20*10.0 + 0.20*9.0 + 0.15*9.0 + 0.10*9.0 + 0.05*10.0
  = 2.700 + 2.000 + 1.800 + 1.350 + 0.900 + 0.500
  = 9.250
```

`S_verify = 9.250`; recomputed from `verify-rubric.json` independently: 9.250. Compared with
`S_measure = 9.100`: `S_accept = min(9.100, 9.250) = 9.100` ≥ threshold `9.000` ≥ baseline 0.000 + floor
0.500. `delta = +9.100`. The verify run adds no gain and does not move the baseline.

## §7 verdict: clean

Every failure condition of `egg-drop-test.md` §7 checked separately against the frozen answer; none holds:

| # | §7 condition | result | evidence |
|---|---|---|---|
| 1 | a hard limit violated (mass > 500 g, dimension > 300 mm) | not violated | `answer.md:51-73`, `answer.md:103-129` — 458.0 g, 250×250×290 mm |
| 2 | physical calculations missing | not violated | `answer.md:203-303` — full force/energy/stroke derivation |
| 3 | egg not protected from all sides | not violated | `answer.md:35-40`, `answer.md:51-90`, `answer.md:103-163` — foam + free stroke on six faces, corner dampers |
| 4 | no braking path (rigid attachment to the outer shell) | not violated | `answer.md:103-163` — 60 mm free suspension stroke + 96 mm cone crush |
| 5 | forbidden materials used | not violated | `answer.md:35-40` — metal, glass, plastic > 2 mm and glue only as prohibitions; egg not glued |

`invalid: false`, `invalid_reason: null`. Inputs hash-stable: the answer and prompt the evaluator read
equal both directories' frozen copies, and both mechanical reports (V1 exit 0, 22/22 controls; V2 exit 0,
G01–G12 all PASS, selected_cases 1) were produced on those same bytes.

## Diagnostic observations (not score-changing)

1. **Static weight `Mg` inside `F_avg`.** The answer writes `F_avg = M(a_eq + g) ≈ 276.8 N`
   (`answer.md:217`), i.e. it keeps the static weight term, which the prompt's simplified `M·v/Δt`
   omits. The difference is 1.65 % on `F_avg` and the direction is conservative (a larger force is
   claimed than the simplified prompt formula gives). Physically correct; no deduction.
2. **`E_res = 0.78 J` versus exact 0.7652 J.** In the sensitivity text (`answer.md:284`) the residual
   energy for β = 0.13 is printed as 0.78 J; the exact product is 0.7652 J, a 1.9 % rounding. It is a
   display rounding inside the sensitivity paragraph, consistent with its stated conclusion ("ещё
   проходит"), and does not affect any threshold or the verdict.

Neither observation changes an anchor, a weight, the threshold or the verdict; tolerances of the
contract were not revised.

## Isolation note

The evaluator received only: the frozen prompt (`m001/egg-drop-test.md`), the frozen answer
(`m001/answer.md`), the frozen manifest (`m001/manifest.json`), the two mechanical reports
(`verify-gate.json`, `selftest.json`) and the rubric rules of §5/§7. It did NOT receive the first
assessor's score or justification, the weaknesses list (`Next-step seed`), the campaign status file
`.pdca/status/egg-drop-1.md`, the charter, or any other artifact of the campaign package. This run is
therefore an independent second evaluation, not a revision of the first one.
