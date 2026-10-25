# Manual review — egg-drop, revision r=1, attempt n=3 (final corrective generation)

Document: `experiments/egg-drop/answer.md`, 921 lines,
sha256 `7a67e1a91be885640962b27548e73707ef760eb8d3c252d0ce284113d6cda3c3` (unchanged after the
last edit and before every run). Checker: `.pdca/egg-drop/rv1/verify.py`,
sha256 `c8a4ee5d14e5bf7b67cbe29e45109d3868c873eb56195e633f7d5e9f7e30773e`.
Runs: `checks-transcript.log` in this directory. Each pointer below was re-checked against the
file after the last edit; the counts quoted are the ones in the JSON logs.

## AC1 — six mandatory sections in spec order

`structure.json` 7/7, exit 0. Headings: `answer.md:12` (`## 1. Концепция`), `:129`
(`## 2. Спецификация`), `:242` (`## 3. Физические расчёты`), `:597` (`## 4. Оценка
надёжности`), `:675` (`## 5. Альтернативы`), `:718` (`## 6. Итерации`) — exactly six H2, in
order; LANGUAGE 0.923 Cyrillic; 150+ LaTeX fragments; the seven labelled rows are at
`answer.md:311-317` (v_impact 14.01 m/s, E_k 42.77 J, Δt 0.02279 s, F_avg 272.3 N,
F_peak 408.4 N, n 95.5 g, η 0.9858). **Met.**

## AC2 — every required subsection is present and substantive

`content.json` 21/21, exit 0 (T_CONCEPT_NAME, T_DIAGRAM, T_MATERIAL_JUSTIFY with 7 rows,
T_STAGED, T_BOM 16 rows, T_DIMS 17 rows, T_ATTACH, T_TOTAL_MASS, T_BUDGET, T_PHYSICS_ROWS,
T_VERDICT, T_P1, T_P3, T_WEAK_BULLETS 7, T_FAILURE_BULLETS 7, T_FAILURE, T_ALTS, T_ALT_TABLE,
T_IMPROVE, T_20M, T_NO_TBD). Review of the four R2/R3/R5/R6 objections:

- R2 lid/floor: both are **inset** panels 240 × 240 × 5 (`answer.md:168-169`), the four walls
  run the full 0…300 mm (`:166-167`), the cavity row is 240 × 240 × 290 (`:170`) and the outer
  height is stated as exactly 300 mm, not 310 (`:185-187`); the model block agrees
  (`:818-824`: box 250/250/300, wall 5, cavity 290/240/240). Enforced mechanically by
  `constraints.json:INSET_PANELS` (pass) and `WALL_CHAIN` (9/9 identities).
- R6 pads: 4 × 40 × 35 × 8 (`answer.md:178`) fit the 90 × 80 cradle with 10 mm to spare in X
  and 10 mm in Y, placed in the four corner quadrants next to the cradle corners, H ∈ [215, 223]
  (`:103-106`); they sit outside both lateral stacks (X stack Y ∈ [−40, 40], pad Y ∈ [40, 75]).
  BOM mass (8 g) and cost (0.10 $) unchanged (`:149`).
- R5 straws: `190 + 10 + 10 = 210` (`:99`, `:431`) — exactly the bottom cavity, no longer 200 < 210.
- R3 free stroke: the blanket claim is gone; `:400-411` states the three closing sums
  (210+60+20 = 290, 75+90+75 = 240, 80+80+80 = 240), the explicit 20 mm perimeter
  ((240−200)/2, `:192-194`), the open corner quadrants as a named weak point (`:411`, `:655`),
  and the corner-stiffener positions (8 × 30 × 30 × 30, two per vertical edge, `:100-102`).

**Met.**

## AC3 — kinematics + drag consistency

`physics.json` 19/19 (V_IMPACT 14.0071, T_FALL 1.4278, E_K 42.772, CHAIN 7/7) and
`structure.json` 7/7, both exit 0; `probe.json` now recomputes the same headline numbers from
the same inputs. R10: drag is recomputed at the document's own C_d = 0.8, A = 0.0625 m²,
v = 14.01 m/s ⇒ F_D = 0.5·1.225·0.8·0.0625·196.2 = 6.01 N (`answer.md:471-472`), and the
restoring moment follows from it: K = 6.01·0.1236 = 0.74 N·m/rad, ω_n = 11.6 rad/s,
ω_0/ω_n = 1.5° (`:472-474`), still not credited. R11: the post-crush state is labelled
«допущение модели (не измерено)» (`:628`). **Met.**

## AC4 — mass ≤ 500 g with a stated margin

`constraints.json` 14/14, exit 0: MASS_SUM 436.0 = stated 436 (`answer.md:152`), MASS_LIMIT
436 ≤ 500, RESERVE row present (`:150`), margin 64 g = 12.8% (`:215-217`). **Met.**

## AC5 — dimensions ≤ 300 mm, volume ≤ 0.02 m³

`constraints.json` DIM_MAX 300.0 (17 rows), VOLUME 18 750 000 mm³ stated at `answer.md:196`,
WALL_TABLE 5 mm (table = model, wall_total 10), WALL_CHAIN 9/9, INSET_PANELS lid 240×240×5 /
floor 240×240×5. Review: the outer height is 300 mm because the lid and floor sit inside the
300 mm walls (`:166-170`, `:185-187`); the 310 mm failure mode is exactly the new fixture
`INSET_PANELS`, which the selftest rejects. Volume binds before the side limit (`:197-198`).
**Met.**

## AC6 — budget ≤ $5.00

`constraints.json` BUDGET_SUM 3.17 = stated 3.17 (`answer.md:152`, `:221`), BUDGET_LIMIT pass;
the price-doubling sentence is the stated boundary, not a claim that doubling passes
(`:221-223`). **Met.**

## AC7 — allowed materials, egg not glued

`constraints.json` MATERIAL clean, MATERIAL_ALLOWED clean, EGG_ATTACH pass; `answer.md:202-211`
states six rubber bands + rope, no glue, tape only on the shell; the material justification
table is `:115-127`; the BOM (`:133-150`) contains no metal, glass, rigid plastic > 2 mm or
ready-made absorber. **Met.**

## AC8 — Δt and η derived, not asserted

`physics.json` 19/19: DT 0.02279 (2s/v and the momentum cross-check), F_AVG 272.27,
F_PEAK 408.40, N_PEAK 95.5, E_EGG 0.609, ETA 0.9858, GRAVITY_TERM dU_g 0.683 J = 1.60% and
E_tot 43.45 J, CHAIN 7/7. Review: the force profile is stated at `answer.md:287-303`,
ΔU_g = m·g·s is included (`:295-297`), and η's requirement 0.9766 is derived from E_crit and
labelled a requirement (`:363`). R8: the parenthetical at `:342-346` now says the 60.9 N figure
is 0.6% **optimistic** (0.615 J / η 0.9856 with the egg's weight) and that both values clear
0.9766 — it no longer claims to be conservative. **Met.**

## AC9 — reliability with an explicit probability model

`content.json` T_P1, T_P3, T_WEAK_BULLETS (7), T_FAILURE_BULLETS (7), T_FAILURE all pass;
`answer.md:599-606` states the conditional chain P_3 = P_1·P(2|)·P(3|), `:610` P1 = 0.75,
`:643` P3 = 0.0056, with the independence caveat at `:645-649`. R11: the second-drop input
«~50 / ~10 мм» is labelled «допущение модели (не измерено)» (`:628`) and the table row is
marked «допущение 10 мм» (`:635`). R4: one value each — residual 1501.5 g (`:635`), side
264.6 g (`:636`), inverted 988.4 g (`:637`), identical to `:506`, `:532`, `:661`, `:662`.
**Met.**

## AC10 — ≥2 alternatives with numbers + 20 m iteration

`physics.json` P_20M pass (v 19.81, E_k20 85.54, s_req20 300 mm > 159.6 mm); `content.json`
T_ALTS/T_ALT_TABLE pass. `answer.md:677-716`: B 451 g / 3.57 $ / 0.60, C 415 g / 3.80 $ / 0.50,
D 360 g / 3.20 $ / 0.35, with a single mass m_B = 451 g used everywhere (`:681-690`). 20 m at
`:765-792`. R1: the §6.1 improvement no longer bottoms out — the stroke floor is stated as
s_req(257 N) = 169.2 mm **> 159.6 mm usable**, with an explicit refusal to compare against the
210 mm nominal cavity (`:736-741`), so the plateau is held at 272.3 N and the gain is taken on
k_peak: 1.50 → 1.35 ⇒ F_peak = 367.6 N, n_peak = 1.35·624.5/9.81 = 85.9 g, −10.0 %
(`:744-753`). R7: thicker cotton (8 → 12 mm) now **increases** compliance δ_egg 10 → 12 mm at
constant E_egg = 0.609 J, so F_egg falls 60.9 → 50.8 N and the contact stress 0.061 → 0.051 MPa
(`:728`), consistent with `:120`. **Met.**

## AC11 — a braking path exists and is derived from geometry

`physics.json` STROKE derived 159.6 = claimed 159.6 = 14·(15−3.6), ≥ dx_min 100; STROKE_FITS
210+60+20 = 290 = cavity_H; LATERAL_STROKE X 57.0 (5·11.4), Y 60.8 (5·12.16), top 15.2
(5·3.04); DX_MIN 100.0. Review: `answer.md:382-434` derives every face from layers × pitch and
states the two load-path facts (straw P_cr ≈ 12 N ≪ 272 N at `:425-429`; anchors 75/80 mm
inside the stacks at `:432-434`). **Met.**

## AC12 — numerical self-consistency and evidence hygiene

`structure.json` 7/7 + `content.json` 21/21 + `physics.json` 19/19, all exit 0.

- R1–R10: every cross-section contradiction closed (see AC2/AC3/AC5/AC9/AC10 above); the same
  cavity chain appears at `:170`, `:187-188`, `:402` and in the model (`:818-824`).
- R13: the probe is no longer stale — `probe.json` runs at m = 436 g and s = 159.6 mm with
  ΔU_g = m·g·s and prints 14.0071 m/s, 42.772 J, 272.3 N, 408.4 N, 95.5 g, 0.609 J, 0.9858,
  i.e. exactly the document's headline numbers (see the last block of `checks-transcript.log`).
- R15: the model block reads `"revision": 1` (`answer.md:802`).
- R17: `min_selected` is per check (2/8/6/7/6/12) and a below-floor run fails
  (`verify.py` MIN_SELECTED); every run here selects 14–21.
- One value per quantity: 436 g, 3.17 $, 300 mm, 18.75 L, 159.6 / 57.0 / 60.8 / 15.2 mm,
  14.01 m/s, 42.77 J, 0.02279 s, 408.4 N, 95.5 g, 0.9858, 264.6 g, 988.4 g, 1501.5 g,
  31.4° (adopted 31°), 6.01 N, 176.4 mm, 0.75 / 0.0056 — each recomputed by hand in
  `checks-transcript.log`.
- Six distinct `started_utc` values (15:41:42.810Z … 15:41:43.084Z), all after the last edit;
  the sha256 in the transcript is the file that was read.

**Met.**
