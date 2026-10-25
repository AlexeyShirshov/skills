# Manual review — `experiments/egg-drop/answer.md`, cycle 1 / revision 1 / attempt 1

Reviewer: `pdca-executor` (DO phase, D3). Document sha256
`b499caf47de2fd2afd13e01dfe622a3d513a46431e0236a9da9ff9a6c47cec92`, checker sha256
`e039a04acbeffa3097cf905bc2bd38b8bccbc14a5c185842cca2f68efd2e90ac`.

Machine evidence (all exit 0): `probe.json` 21/21, `selftest.json` 10/10,
`structure.json` 7/7, `physics.json` 16/16, `constraints.json` 11/11, `content.json` 20/20.
Transcript: `checks-transcript.log`. This file is the `review` kind of evidence — it decides
nothing automatically and it does **not** upgrade a check that failed.

## What is only an estimate, and what is unverified

| Item | Status | Pointer |
|---|---|---|
| All component masses | **design estimate** from area × basis weight (400 / 80 g/m²); nothing was weighed | `answer.md:108-110`, `:149` |
| All prices | **indicative retail estimate**, not a quotation | `answer.md:109-110`, `:155` |
| Paper crush plateau force | **not measured and not derived from first principles**; stated only as a requirement 245–307 N | `:225-227`, `:336-338` |
| Peak factor $k_{peak} = 1.5$ | **assumed** material property; 1.2–1.8 sensitivity shown | `:223-227`, `:308-316` |
| Egg thresholds $n_{crit}$ 50–200 g, $E_{crit}$ 1.0 J | **spec design points**, not measured | `:183-186` |
| $\delta_{egg}$ = 10 mm | estimate of the bed's compliance | `:188`, `:262-266` |
| $P_1$ = 0.75, $P_3$ = 0.0056 | **subjective model output**, explicitly not a frequency | `:350-354`, `:361`, `:384` |
| Drag estimate (10.33 m/s terminal, 9.47 m/s impact) | model only, deliberately **not** used in the design numbers | `:204-216` |

Unverified end to end: no device was built, no drop was performed, no crush curve exists. The
document says so at `:6-8` and never uses the language of measurement.

## AC2 — every required subsection substantive

Checked section by section against spec §4.1–4.6:
§1 name/principle/scheme/material justification `:12-85`; §2 BOM `:89-110`, dimensions
`:113-132`, attachment `:136-144`, total mass `:147-150`, budget `:153-155`, assembly
`:158-170`; §3 inputs `:175-188`, $v_{impact}$/$E_k$ `:191-214`, model `:216-230`, summary
`:232-247`, egg load and $\eta$ `:249-276`, stroke derivation `:276-291`, self-check
`:295-316`, verdict `:328-346`; §4 probability model `:350-354`, one drop `:356-369`,
three drops `:372-390`, weak points `:392-403`, failure modes `:405-413`; §5 B `:413-424`,
C `:426-432`, D `:434-438`, comparison `:440-447`; §6 improvements `:451-466`, 20 m
`:469-493`. No `TBD`/placeholder anywhere (`content.json:T_NO_TBD`).
**Met.**

## AC5 — dimensions and volume

Every one of the 13 dimension rows is ≤ 300 mm; the max is the box height 300 mm
(`:116`). Bounding volume 18 750 000 mm³ = 18.75 L ≤ 20 L, stated at `:131` with the honest
note that at the 300 mm side limit a cube would be 27 L, so volume binds (equivalent edge
271 mm). The 270 mm composition hypothesis from the plan was replaced by 300 × 250 × 250 —
still inside both limits and it buys the 210 mm crush cavity that the 270 mm cube could not
(see AC11). **Met**, with a deviation from the plan's hypothesis that is recorded as a
`Notice` in the status file.

## AC7 — materials, forbidden list, egg attachment

BOM material column `:92-106` contains only paper, cardboard, pulp tray, cotton, rubber
bands, string, tape, straws, styrofoam — all on the allowed list (`constraints.json`
`MATERIAL` + `MATERIAL_ALLOWED`, both clean). No metal, glass, rigid plastic > 2 mm, glue or
ready-made damper. The egg is explicitly not glued and is held by six rubber bands plus string
(`:42-44`, `:138-144`); the only adhesive is tape on the shell, and the document says no tape
seam touches the egg (`:141-143`). Load path contains no rigid member between egg and shell
(`:63-64`, `:67-68`). **Met.**

## AC8 — Δt and η derived, not asserted

The force profile is stated (constant plateau over a stroke, `:216-221`), then
$a_{avg} = v^2/2s$, $\Delta t = 2s/v = mv/F_{avg}$ with the momentum cross-check
(`:243-246`), $F_{peak} = k F_{avg}$, and $\eta = 1 - E_{egg}/E_k$ with
$E_{egg} = F_{egg}\delta_{egg}$, $F_{egg} = m_{egg}a_{peak}$ (`:254-259`). The requirement
$\eta > 0.98$ is explicitly labelled **derived from** $E_{crit}/E_k$, not a property of paper
(`:260-262`), and its implication is shown as a limit on the bed: $\delta_{egg} \le 16.7$ mm
(`:263-266`). The same $F_y$, $s$ produce $\Delta t$, $\eta$ and $F_{peak}$ used in §3.4 and
`:315-321`; `physics.json:CHAIN` confirms the seven identities over the document's own claims.
**Met.**

## AC9 — reliability with an explicit model

$P_1 = 0.75$ with a driver table (`:361-370`), $P_3$ built as a **conditional chain**, not
$P_1^3$ (`:350-354`, `:384`), with the degradation re-derived: crushed stack leaves ~10 mm of
stroke, $n_{avg}$ = 1000 g, $n_{peak}$ ≈ 1500 g (`:374-378`). Naive $P_1^3 = 0.42$ is named and
rejected (`:386`). Weak points: 6 bullets (`:392-403`); failure modes: 7 bullets (`:405-413`).
The checker's own count was reported as `bullets=13` in `content.json` — that is the sum of **both**
lists (6 + 7), not the weak-point count; see the correction note at the end of this file.
Both probabilities are labelled model estimates (`:350-354`). **Met.** Honest weakness: 0.75
and 0.15/0.05 are judgement calls, not fitted values — the document says so and gives the
driver list, which is the most that can be done without data.

## AC10 — alternatives and the 20 m recalc

B: parachute 300 mm, $v_{term}$ 8.85 m/s, impact over 10 m 8.48 m/s, $E_k$ 14.9 J, mass 355 g,
cost 4.10 $, reliability 0.60 (`:413-424`); C: rubber-band suspension 380 g / 3.60 $ / 0.50
(`:426-432`); D: foam cocoon 360 g / 3.20 $ / 0.35 (`:434-438`); comparison table
`:442-447`. 20 m: $v$ 19.81 m/s, $E_{k}$ 78.48 J, $n_{peak}$ 187.5 g at the existing stroke,
$E_{egg}$ 1.20 J > 1 J, $s_{req}$ = 300 mm > 160 mm achievable and equal to the whole 300 mm
box → parachute becomes mandatory, then $s_{req}$ falls to 59 mm at 415 g / 3.40 $
(`:469-493`). `physics.json:P_20M` recomputes all three numbers. **Met.**

## AC11 — braking path exists and is derived

$\Delta x_{min} = v^2/(2n_{crit}g)$ = 100 mm at 100 g (`:288-290`); the design stroke is derived
as 14 layers × (15 − 3.6) mm = 159.6 ≈ 160 mm inside a cavity of 300 − 10 − 20 − 60 = 210 mm
(`:276-284`); `physics.json:STROKE` and `:STROKE_FITS` confirm both. Margin 1.6 over
$\Delta x_{min}$, and only 1.07 over the 150 mm needed to keep the **peak** at 100 g
(`:292-294`) — the document states that thin margin rather than hiding it. No rigid load path
`:63-64`. **Met**, with the caveat that 160 mm is the *usable* stroke only if the layers crush
individually; the "pancake collapse" mode is listed as the top risk (`:391-393`) and is the
first item of the improvement plan (`:459-460`).

## AC12 — numerical self-consistency

Independent hand recomputation (the arithmetic is reproduced in this file, continuously from the
numbers above; the transcript of this attempt carries no such section — see the correction note at
the end of this file):

- mass: 65+120+25+25+20+45+13+20+8+4+6+5+12+8+24 = **400 g** — matches `:149`;
- budget: 0.25+0.60+0.15+0.15+0.10+0.20+0.06+0.20+0.30+0.15+0.40+0.10+0.05+0.10+0.19 = **3.00 $** — matches `:155`;
- energy: 0.5 · 0.400 · 196.199 = **39.24 J** — matches `:236`, `:300-302`;
- stroke: 14 · 11.4 = **159.6 mm**, cavity 210 mm — matches `:282-284`;
- $\eta$: 1 − 0.598/39.24 = **0.9848** — matches `:241`, `:257`, `:305`.

Cross-section scan found and fixed three contradictions before this review was written:

1. the §1.2 three-part energy split vs the §3.5 two-part split — resolved at `:268-272` by
   stating that shell and stack cannot be separated without a test and are lumped into
   $E_{stack}$;
2. the bed footprint (70 vs 90 mm) in the diagram — the diagram now says ложе 90×80×60 with a
   70×70×60 cup (`:53-54`), matching `:123` and `bed_mm` in the model block;
3. `§3.7` claimed the g-load is mass-independent *and* that the 500 g case is fine — true only
   if the plateau is matched to the mass; `:314-322` now derives $F_y = mv^2/(2s)$ = 245 N at
   400 g and 307 N at 500 g and shows that a 245 N plateau at 500 g would demand 200 mm of
   stroke and bottom out.

One earlier error was also corrected rather than left in: the first draft claimed air drag
changes $v$ by < 1%; the correct estimate is $v_{term}$ = 10.33 m/s and impact ≈ 9.47 m/s
(`:204-213`). The design numbers deliberately stay on the no-drag model (conservative), and
the document says the drag credit is **not** used.

## Is the verdict justified by the numbers?

Yes, and it is deliberately weaker than the numbers could support. $n_{peak}$ = 93.8 g sits in
the upper half of the 50–200 g band (`:160`), only 6.2 g below the chosen 100 g design point,
the peak factor is unmeasured, and the stroke margin over the 150 mm peak-limited requirement
is 7%. "Да" would overclaim; "нет" would ignore a computed margin of 1.6× on stroke and 1.7×
on $E_{egg}$ (0.598 vs 1.0 J). "Вероятно" with six explicit conditions (`:333-344`) and an
explicit failure boundary — "if the real threshold is near 50 g, the device does not pass,
the required stroke is 200 mm" (`:345-347`) — is the honest verdict.

## Residual review findings (not blocking AC, recorded for ACT)

- The plateau target is a **requirement**, not a derived number: no formula links fold geometry
  to force. This is the single largest gap and it is listed first among the risks.
- $P_1$ = 0.75 remains a judgement; a first real drop would replace it.
- The assembly time (29 min) is an estimate like the masses; it is not machine-checked beyond
  the table sum.

## Correction note (CHECK, attempt 1) — 2026-10-24T14:50:22Z

This file is not part of the frozen manifest generation; the two defects the CHECK found in it are
corrected here in place, and the correction is recorded rather than hidden.

`Notice:` `review.md:106` (AC12) pointed at "`checks-transcript.log`, section *hand recompute*".
That section never existed: the attempt-1 transcript holds only the six command banners and their
exit codes, with no recompute block. The pointer is corrected to say the arithmetic is reproduced
in the review itself, and the next generation (`c1-r1-n2/checks-transcript.log`) carries a real,
named `hand recompute` section.

`Notice:` `review.md:78` stated "Weak points: 6 bullets; failure modes: 7 bullets" while
`content.json:T_WEAK` recorded `bullets=13`. The document is 6 + 7 = 13 bullets; the checker was
counting every bullet of section 4 in one bucket. The prose count is right, the checker count was
ambiguous, and `verify.py` in the next generation counts the two lists in separately numbered
subsections (`T_WEAK_BULLETS`, `T_FAILURE_BULLETS`).

Both defects are carried in the status file defect history as `DEF-EVIDENCE-LOG-MISMATCH` and
`DEF-UNLABELLED-CLAIMS-AND-SPEC-WINDOW` (§4.4 bullet accounting).
