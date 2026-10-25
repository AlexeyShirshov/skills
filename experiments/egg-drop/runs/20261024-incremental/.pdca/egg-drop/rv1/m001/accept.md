# ACCEPT — step 1, rv1, m001 (campaign egg-drop)

Recorded: 2026-10-24T18:20:12Z (UTC).
Assessor: `pdca-check`, independent of the answer's author (session `ses_e90e1b654ffew2T4qWLerBIFcC`).
Machine-readable block: `.pdca/egg-drop/rv1/m001/rubric.json` (verbatim from the assessor).

Package: `.pdca/egg-drop/rv1/m001/` — frozen inputs: `answer.md` (sha256 `40a56cc8…`), `egg-drop-test.md`
(`8a79d64b…`), `check_answer.py` (`d6260656…`), 24 `fixtures/**` files; 27 inputs total.

## Verdict

`S_accept = 9.100`, baseline `S0 = 0.000`, delta `+9.100` >= floor `0.500` — **floor met**, campaign
acceptance criterion 1 of 2 (mechanical gate PASS + `S_accept >= 9.000`) satisfied. The second half of
the goal (`final verify PASS`) is a later step and is not claimed here.

## Per-criterion scores (every number and pointer as the assessor gave them)

| criterion | weight | score | applied anchor | evidence pointers |
|---|---|---|---|---|
| physics | 0.30 | 9.0 | 5 → 10 (interpolated 9.0) | `answer.md:203-303`, `answer.md:75-82`, `answer.md:130-163` |
| constraints | 0.20 | 10.0 | 10: all constraints satisfied | `answer.md:35-40`, `answer.md:51-73`, `answer.md:103-129` |
| reliability | 0.20 | 8.5 | 5 (50–80 %) → 10 (>90 %) (interpolated 8.5) | `answer.md:294-303`, `answer.md:305-342`, `answer.md:78-82` |
| materials | 0.15 | 9.0 | 5 → 10 (interpolated 9.0) | `answer.md:12-16`, `answer.md:31-43`, `answer.md:51-65`, `answer.md:241-270` |
| specification | 0.10 | 8.5 | 5 → 10 (interpolated 8.5) | `answer.md:45-90`, `answer.md:93-143` |
| iterations | 0.05 | 10.0 | 10: concrete plan with calculations | `answer.md:343-392` |

Justifications (condensed; no number or pointer dropped):

- **physics 9.0** — all formulas and numbers reproduce within <0.01 %; assumptions k=1.30, A_eff=320 mm²,
  beta=0.093 and the prompt contradictions (`:152`/`:160`, `E_crit`) are disclosed with sensitivity
  analysis. −1.0 for two unjustified simplifications: (1) 96 mm paper cones credited with a full 96 mm
  crush stroke to zero residual thickness, though `:243` admits ~20–25 % densification at the end of
  travel; (2) the 60 mm free suspension stroke and the 96 mm cone crush merged into one uniform
  deceleration of the whole M=0.458 kg at F_avg=276.8 N without matching the two stages' forces (only the
  105 g cradle decelerates over the first 60 mm; when the 105 g cradle hits the cone block with its
  276.8 N crush threshold, the egg's own g-load would exceed 200 g).
- **constraints 10.0** — independent recomputation: total mass 398+60=458.0 g ≤ 500 g; sides
  250×250×290 mm ≤ 300 mm; volume 0.018125 m³ ≤ 0.02 m³; cost $3.11 ≤ $5.00; build 28 min ≤ 30 min;
  12 materials all allowed; film 0.09 and 0.05 mm ≤ 2 mm; no glue/metal/glass/ready absorbers; egg fixed
  by suspension, not glued.
- **reliability 8.5** — P1=0.943 decomposed by landing orientation; P3=0.730 (0.824 with block
  replacement) from a justified dependent-damage model with weak points and failure modes. But the key
  P(bottom)=0.96 rests on a "low centre of mass" claim (`:311`) while the dimension chain (`:78-82`) puts
  the 105 g cradle at 177–232 mm from the floor in a 290 mm box, raising the tumble risk onto the side
  (152 g) or top (290 g).
- **materials 9.0** — each of the 12 materials is motivated by its mechanism (plastic crush of 16 paper
  cones, elastic-viscous rubber suspension, contact-pressure spread by cotton and tray, foam and EPS
  corner dampers). For a 10.0 the quantitative link is missing: buckling force of one paper cone
  (~17.3 N at 3.4 g) and total stiffness of eight rubber bands 120×3×1 mm over 60–165 mm are not
  estimated.
- **specification 8.5** — full material table with masses, prices, dimensions, attachment method, closed
  height (290 mm) and width (250 mm) chains, totals. −1.5 for three internal mismatches: cardboard qty 1
  as 250×250×3 mm without the 290 mm side walls and cap; five foam pads listed while a sixth 18 mm bottom
  pad is used in the scheme (`:27`), height chain (`:81`) and `protection.bottom` (`:138`); cradle width
  52 mm in the width chain (`:84-88`) vs 140×120×40 and 140×140×40 blanks and the 56–60 mm longitudinal
  egg size at the declared transverse orientation (`:282`).
- **iterations 10.0** — concrete post-test plan with numbers (two-stage block 30+66 mm, k 1.30 → 1.15,
  peak 80.1 → 70.9 g; proof that a symmetric top stroke of 100 mm is impossible: 364 mm > 300 mm and
  515 g > 500 g) and a full 20 m recomputation (v=19.81 m/s, t_f=2.02 s, Ek=89.86 J, d_min(100 g)=200 mm,
  peak 159 g, chain 334 mm > 300 mm).

## Arithmetic

`S = 0.30*9.0 + 0.20*10.0 + 0.20*8.5 + 0.15*9.0 + 0.10*8.5 + 0.05*10.0 = 2.700 + 2.000 + 1.700 + 1.350 + 0.850 + 0.500 = 9.100`

`S = 9.100` (= `9.100` exact; three decimals kept, not rounded up). Baseline `S0 = 0.000` →
`delta = +9.100`. Floor `0.500` **met**. Campaign target `S_accept >= 9.000` **met**.

## §7 verdict: clean

All five §7 conditions clean:

- **(a) limits** — mass 458.0 g ≤ 500 g; sides 250×250×290 mm ≤ 300 mm; volume 0.018125 m³ ≤ 0.02 m³;
  cost $3.11 ≤ $5.00; build 28 min.
- **(b) calculations** — full calculations present and verified.
- **(c) six directions** — protected with nonzero stroke.
- **(d) fixation** — egg suspended on 8 rubber bands over a replaceable 16-cone crush block, not rigid to
  the shell.
- **(e) materials** — only allowed materials, film ≤ 2 mm, no glue/metal/glass/ready absorbers.

`invalid: false`, `invalid_reason: null`.

## measured_mismatches: `[]`

Recomputation reproduced every number with zero mismatch: mass 398+60=458.0 g; cost $3.11; volume
0.250*0.250*0.290=0.018125 m³; v=14.0071410 m/s; t_f=1.4278431 s; Ek=44.9298 J (M=0.458 kg);
d_min = 200.0/100.0/50.0 mm at 50/100/200 g; a_eq=594.545455 m/s²; dt_eq=0.0235594 s;
F_avg=276.794798 N; F_peak=359.833238 N; n_load=80.087879 g; F_egg=47.139725 N;
sigma_egg=0.147312 MPa; E_abs=44.3798 J; eta=0.987759.

## Named weaknesses — NOT defects of acceptance

These do not invalidate the measurement, do not lower the accepted score below the floor and do not
block acceptance. They are recorded as the **seed for the next step** (ranked in the status file as
`Next-step seed`).

1. **Cone crush stroke claimed at 100 % of the 96 mm height** — 96 mm paper cones credited with a full
   96 mm stroke to zero residual thickness, while `answer.md:243` admits ~20–25 % densification at the
   end of travel (physics).
2. **Suspension stroke 60 mm merged with cone crush 96 mm** into a single uniform deceleration of
   M=0.458 kg at F_avg=276.8 N, without matching the two stages' forces (physics).
3. **P(bottom)=0.96 justified by "low COM"** while the 105 g cradle sits 177–232 mm from the floor of a
   290 mm box, so the tumble risk onto the side (152 g) or top (290 g) is unaddressed (reliability).
4. **Missing quantitative cone buckling force / rubber-band stiffness** — ~17.3 N per cone at 3.4 g and
   the stiffness of eight 120×3×1 mm bands over 60–165 mm are not estimated (materials).
5. **Three specification inconsistencies** — cardboard qty 1 as 250×250×3 mm without the 290 mm side
   walls; five foam pads listed vs a sixth 18 mm bottom pad; 52 mm cradle width in the width chain vs
   140×120×40 / 140×140×40 blanks (specification).

## Frozen-input integrity

27 manifest hashes of `m001` recomputed at ACCEPT time, before and after writing this record:
**unchanged** (27/27 match `manifest.json#inputs`, `bad = []`). Aggregate
`input_hashes_sha256 = 22d09176f140f5f8910513dcb169326da1cc48b5a17dfc6749406da9f14411b8` as recorded.
No drift → the ACCEPT stands; `experiments/**`, the charter and the m001 frozen inputs were not touched.
