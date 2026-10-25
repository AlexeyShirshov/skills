# Manual review — `experiments/egg-drop/answer.md`, cycle 1 / revision 1 / attempt 2

Reviewer: `pdca-executor` (DO phase, D3, generation `c1-r1-n2`). Document
`experiments/egg-drop/answer.md`, 865 lines, sha256
`b254ced7db9ab14cb54779801a3a72c6131bc6836c63941667a6f6c4c53c25de`. Checker
`.pdca/egg-drop/rv1/verify.py`, sha256
`fb30f7a8a42631769f36397903a86cee112ab608d44d946b89df11c15cfd55bf`.

Machine evidence (all exit 0, each with its own `started_utc` after the last edit of the document):

| # | Check | Exit | Selected / passed / failed | Log |
|---|---|---|---|---|
| C1 | probe | 0 | 21 / 21 / 0 | `probe.json` |
| C2 | selftest | 0 | 13 / 13 / 0 | `selftest.json` |
| C3 | structure | 0 | 7 / 7 / 0 | `structure.json` |
| C4 | physics | 0 | 19 / 19 / 0 | `physics.json` |
| C5 | constraints | 0 | 13 / 13 / 0 | `constraints.json` |
| C6 | content | 0 | 21 / 21 / 0 | `content.json` |

Transcript: `checks-transcript.log` — expanded argv, one exit per command, the artifact and
checker sha256, a `hand recompute` block whose 40 formula→value lines were re-derived from the
document's own inputs, and the θ-capacity bisection. This file is the `review` kind of evidence; it
decides nothing automatically and it does **not** upgrade a check that failed.

## What is only an estimate, and what is unverified

| Item | Status | Pointer |
|---|---|---|
| All component masses | **design estimate** from area × basis weight; nothing was weighed | `answer.md:117-140`, `:191` |
| All prices | **indicative retail estimate**, not a quotation | `:197-201` |
| Paper crush residual (0.24·pitch) | **fold model, not measured** | `:360-362` |
| Peak factor $k_{peak}=1.5$ | **assumed**; 1.2–1.8 sensitivity shown | `:277-283`, `:514-520` |
| Plateau per fold (force ∝ fold count) | **assumed model**, used only in §6.1 | `:690-696` |
| Egg thresholds $n_{crit}$ 50–200 g / 50–100 g, $E_{crit}$ 1.0 J | **spec design points**, not measured | `:231-234`, `:552-555` |
| $\delta_{egg}=10$ mm | estimate of the bed's compliance | `:236`, `:332-344` |
| Buckling load of a straw (12 N) | **computed from assumed E** = 2 GPa | `:390-397` |
| $P_1=0.75$, $P_3=0.0056$ | **subjective model output**, explicitly not a frequency | `:568-583`, `:585-608` |
| Rebounds, obliquity, aero restoring moment | **estimates**, labelled, and the aero credit is **not** used | `:432-441`, `:471-486` |
| Drag estimate (11.82 m/s terminal, 10.27 m/s impact) | model only, deliberately **not** used in the design numbers | `:255-263` |

Unverified end to end: no device was built, no drop was performed, no crush curve exists.

## AC1 — structure and units

`structure.json`: six H2 in spec order, `HEADING_COUNT=6`, Cyrillic share of prose letters
**0.923**, 281 LaTeX fragments, the seven labelled rows present, `MODEL` parses. LaTeX formulas and
mm/g/J/N tables hold throughout (`:285-301`, `:410-419`). The 300 mm axis is now named one way
only — **H, the drop axis** — in the intro (`:10-11`), the dimension table (`:144-146`), the ASCII
scheme (`:63-90`) and the model block (`:744-746`). **Met.**

## AC2 — every required subsection substantive, and the dimension table complete

Spec §4.1–4.6 coverage: §1 name/principle/scheme/material justification `:14-113`; §2 BOM
`:117-140`, dims `:142-176`, attachment `:178-189`, mass `:191`, budget `:197-201`, assembly
`:203-218`; §3 inputs `:222-238`, $v/E_k$ `:240-263`, model `:265-283`, summary `:285-301`,
egg load `:303-356`, stroke geometry `:358-400`, oblique `:402-469`, rebound/inverted `:471-498`,
self-check `:500-530`, verdict `:532-555`; §4 model `:559-566`, one drop `:568-583`, three drops
`:585-608`, weak points `:610-621`, failure modes `:623-631`; §5 B `:635-650`, C `:652-658`,
D `:660-665`, comparison `:667-674`; §6 improvements `:678-707`, 20 m `:709-736`, model `:738-865`.

The attempt-1 objections are closed by inspection, not by wording:

- the top stack now has a **pitch and a residual**: 5 layers × 4 mm, residual 0.96 mm, usable
  15.2 mm (`:373-374`, model `:770-771`), not "4 layers, 20 mm" with no pitch;
- walls are **one** value everywhere: 5 mm per panel → 10 mm total; the table row `:147`, the
  cavity chain `:168-174` (300−10 = 290; 250−10 = 240) and the model `:752-758` agree, and
  `constraints.json:WALL_TABLE/WALL_CHAIN` (9/9 identities) now proves it mechanically;
- lateral crush is quantified (below), strut coordinates and end clearances are given (`:84-97`),
  anchor positions are bounded (`:92-94`);
- no `TBD`/placeholder (`content.json:T_NO_TBD`). **Met.**

## AC3 — kinematics, and no unlabelled paper claim

$v=14.01$ m/s, $t_{fall}=1.43$ s, $E_k=42.77$ J at 436 g, $49.05$ J at the 500 g worst case
(`:240-263`, `:285-301`); `physics.json:V_IMPACT/T_FALL/E_K/E_K_WORST` recompute all four from the
model block. Drag is computed separately and explicitly **not credited** (`:255-263`).

The attempt-1 arithmetic error is gone: the 10 m text no longer contains "187 g". $n_{peak}=95.5$ g
at $s=159.6$ mm (`:294`, `:301`), and 187.5 g appears **only** in the 20 m section, where 189.5 g
is now correctly derived at the same stroke (`:716-722`). Every paper property is labelled
«оценка, не измерено»: `:105-108` (pulp, cotton, foam), `:279` ($k_{peak}$), `:360-362` (fold
residual), `:390-392` (straw modulus), `:474` (elastic return), `:578-579` (plateau scatter,
moisture), `:690` (fold-count model).

Both spec windows are cited: `:233` gives «50–100 g для короткого импульса» (`egg-drop-test.md:152`)
and `:232` the wide 50–200 g (`:160`); `:552-555` states the margin to the **stricter** window
(4.5 g, since $\Delta t=22.8$ ms is a short impulse) and to the wide one (104.5 g). **Met.**

## AC4 — mass

`constraints.json:MASS_SUM`: BOM rows sum to **436.0 g** and the stated total is 436.0 g (16 rows);
`MASS_LIMIT` 436 ≤ 500; `RESERVE` row present. The margin (64 g, 12.8%) is stated at `:191-195`. The
egg is 65 g (upper C1) and included. **Met.**

## AC5 — dimensions and volume

`DIM_MAX` = 300.0 mm over 16 rows — the box height, i.e. exactly at the limit and not above it
(`:144`). `VOLUME` 18 750 000 mm³ = 18.75 L ≤ 20 L, and the document states the volume rather than
the side limit as the binding constraint, with the 271 mm equivalent cube (`:174-176`). **Met.**

## AC6 — budget, and the price-doubling claim removed

`BUDGET_SUM` 3.17 $ = stated 3.17 $ over 16 priced rows including tape; `BUDGET_LIMIT` 3.17 ≤ 5.00.
The false attempt-1 sentence is replaced by the true headroom: prices may rise by **57.7%**
(5.00/3.17 = 1.577) and doubling (2 × 3.17 = 6.34) **breaks** the budget (`:197-201`). **Met**, with
the review pointer required because the attempt-1 defect was a prose claim, not a sum.

## AC7 — materials, forbidden list, egg attachment

`MATERIAL` clean, `MATERIAL_ALLOWED` all rows on the spec list, `EGG_ATTACH` present. Rubber bands
and rope only; the rope is named «верёвка (шпагат)» so the spec's literal word appears
(`:131`, `:183`, `:56`). Anchors are on the cradle only, with ≥75 mm (X) / ≥80 mm (Y) to the inner
wall, filled by the lateral accordion (`:92-94`, `:188-189`). Tape only on the shell. **Met.**

## AC8 — Δt, η and the all-sides load path, derived

Profile stated (`:265-283`): plateau over the stroke, $E_{tot}=F_{avg}s$, $a_{avg}=v^2/(2s)+g$,
$\Delta t=2s/v=mv/(F_{avg}-mg)$, $F_{peak}=kF_{avg}$, $\eta=1-E_{egg}/E_k$. The requirement
$\eta>0.98$ is **derived** from $E_{crit}$ (0.9766) and labelled a requirement (`:338-344`).

The attempt-1 blocker — no lateral crushable stroke — is closed: four lateral stacks, 5 layers each,
depth $(240-90)/2=75$ mm (X) and $(240-80)/2=80$ mm (Y), usable **57.0** and **60.8** mm, verified
by `physics.json:LATERAL_STROKE` (including `nominal ≤ depth` and `depth == annulus`). The top stack
is no longer an admitted 20 mm dead end: 5 × 4 mm, usable 15.2 mm (`TOP_STROKE`), sized against a
5% elastic rebound (`:471-485`, 14.7 mm of 15.2 mm used).

No rigid load path, proven geometrically: 8 straws at (±85, ±85), 190 mm long with 5 mm end
clearance, buckling load 12 N = 4.4% of the 272 N plateau (`:390-397`), and all anchors clear of
the shell by the annulus (`:398-400`). The free-body mass ratio $F_{egg}=(m_{egg}/m)F_{stack}=
0.1491$ is derived explicitly (`:315-327`), so the 272/408 N stack forces do not cross the egg
boundary. **Met**, with the honest residual that a full-speed inverted drop is a computed failure
(`:487-497`) — a limitation of the 300 mm envelope, now with a real dissipater on that face.

## AC9 — reliability, counted correctly

$P_1=0.75$ with a driver table (`:568-583`); $P_3$ as a conditional chain 0.75·0.15·0.05 = 0.0056
(`:585-608`), naive $P_1^3=0.42$ named and rejected. The avg/peak mixing is gone: `:591-598` gives
**one** convention ($n_{avg}$, then $n_{peak}=1.5n_{avg}$) for the design stack (63.7 → 95.5 g), the
residual stack (1001.0 → 1501.5 g), a fresh lateral face (176.4 → 264.6 g) and a fresh top face
(658.9 → 988.3 g). Bullets are counted **per block** now: 7 weak points (`:610-621`) and 7 failure
modes (`:623-631`) — `content.json:T_WEAK_BULLETS=7`, `T_FAILURE_BULLETS=7`, no longer one merged
count of 13. **Met.**

## AC10 — alternatives and the 20 m recalc

B uses **one** mass everywhere — 451 g in $v_{term}$ (`:635-650`), in the prose, in §5.4 and in
§6.2: $v_{term}=9.23$ m/s, $v(10\,м)=8.76$ m/s, $E_k=17.29$ J, $s_{req}=58.7$ mm, cost 3.57 $.
C 415 g / 3.80 $ / 0.50 / 90 mm, D 360 g / 3.20 $ / 0.35 / 70 mm, comparison `:667-674`.
20 m: $v=19.81$ m/s, $E_k=85.54$ J, $n_{peak}=189.5$ g at the existing stroke, $E_{egg}=1.21$ J >
1 J, $s_{req}=300$ mm = the whole box → parachute mandatory; with the canopy 451 g, $v=9.18$ m/s,
$E_k=19.01$ J, $s_{req}=64.5$ mm (`:709-736`). `physics.json:P_20M` recomputes all of it. **Met.**

## AC11 — braking path, wall arithmetic, gravity

$\Delta x_{min}=100$ mm (`:379-386`), stroke derived on **every** face from layers: 14·(15−3.6) =
159.6 mm (`:364-367`), 5·(15−3.6) = 57.0, 5·(16−3.84) = 60.8, 5·(4−0.96) = 15.2. `STROKE` and
`STROKE_FITS` confirm the derivation and that 210 + 60 + 20 = 290 closes the cavity; margins 1.60
over $\Delta x_{min}$ and 6.4% over the 150 mm peak-limited requirement are stated, not hidden
(`:384-386`).

The attempt-1 wall contradiction (3 mm in the table vs 10 mm in the chain) is gone: 5 mm panels,
10 mm total, and `WALL_CHAIN` closes 9/9 identities including the annulus = lateral-depth identity.

The missing gravitational term is now in the balance: $\Delta U_g = m g s = 0.683$ J = 1.60% of
$E_k$, $E_{tot}=43.45$ J, $a_{avg}=v^2/(2s)+g$, and the momentum identity is written with weight
$(F_{avg}-mg)\Delta t=mv$ (`:265-283`, `:297-301`, `:507`). `GRAVITY_TERM` recomputes the term and
its share; `CHAIN` holds all seven identities with gravity. **Met.**

## AC12 — numerical self-consistency and evidence hygiene

The attempt-1 contradictions, one by one:

1. wall 3 vs 10 mm → single 5 mm panel/thickness everywhere (`:144-176`, `WALL_TABLE`, `WALL_CHAIN`);
2. two opposing 160 mm stacks in a 300 mm box → not attempted: 159.6 bottom + 60 bed + 15.2 top =
   290 mm inside a 290 mm cavity, and the impossibility of the symmetric design is stated in the
   text (`:495-497`, 480 mm vs 290 mm);
3. $E_{stack}+E_{egg}$ double count → $E_{tot}=F_{avg}s$, $E_{stack}=E_{tot}-E_{egg}$, with the
   free-body ratio and the statement that $E_{egg}$ sits *inside* $F_{avg}s$ (`:346-351`);
4. avg/peak mixing → one convention in a single table (`:591-598`);
5. 415 g vs 355 g in alternative B → 451 g everywhere (`:635-650`, `:669-673`, `:728-736`);
6. the impossible "252 mm stack in a 200 mm cavity" improvement → replaced by 12 × 17.5 = 210 mm in
   the same cavity, stroke unchanged at 159.6 mm, and the effect derived through the fold count
   (`:686-696`); the old "n down 15%" claim is explicitly retracted in the text;
7. "doubling prices fits" → 57.7% headroom, doubling breaks it (`:200-201`);
8. the 10 m "187 g" → 95.5 g, with 189.5 g kept in the 20 m case only (`:294`, `:716-722`).

Evidence hygiene, also from the attempt-1 finding: the six logs now carry **six different**
`started_utc` values (14:58:58.983 … 14:59:05.233Z), all **after** the last edit of the document;
this transcript carries the document sha256, the checker sha256, the line count and a real
`hand recompute` section (42 formula→value lines plus the θ bisection) that the review can point at
and that actually exists; this review's bullet counts equal the checker's counts.
**Met.**

## Defect keys — closure status

| Key | Evidence that closes it | Fixes applied |
|---|---|---|
| `DEF-ALL-SIDES-PROTECTION` | `LATERAL_STROKE` (57.0/60.8 mm), `TOP_STROKE` (15.2 mm), `:390-400` buckling + anchors, `:487-497` quantified inverted failure | 1 |
| `DEF-WALL-CAVITY-GEOMETRY` | `WALL_TABLE`, `WALL_CHAIN` 9/9, `:144-176` | 1 |
| `DEF-PROSE-MATH-CONTRADICTIONS` | `:200-201`, `:294`, `:591-598`, `:635-650`, `:686-696`, `TABLE_VS_MODEL` | 1 |
| `DEF-ENERGY-GRAVITY-BOOKKEEPING` | `GRAVITY_TERM` (0.683 J, 1.60%), `CHAIN` with weight, `:303-351` | 1 |
| `DEF-UNLABELLED-CLAIMS-AND-SPEC-WINDOW` | labels at `:105-108`, `:279`, `:360-362`, `:390-392`, `:474`, `:578-579`; both windows `:232-233`, `:552-555` | 1 |
| `DEF-EVIDENCE-LOG-MISMATCH` | six distinct `started_utc`, sha256 + line count in the transcript, real `hand recompute`, per-block bullet counts | 1 |

## Is the verdict justified by the numbers?

Yes, and it is deliberately weaker than the numbers could support. $n_{peak}=95.5$ g sits **inside**
the strict 50–100 g window with only 4.5 g of room, the peak factor is unmeasured, the stroke beats
the peak-limited requirement by 6.4%, and the top face cannot survive a full-speed inverted drop.
«Да» would overclaim; «нет» would ignore a computed 1.60× stroke margin and 1.64× on $E_{egg}$
(0.609 vs 1.0 J). «Вероятно» with seven explicit conditions (`:534-550`) and a named failure
boundary is the honest verdict.

## Residual findings (not blocking an AC, recorded for ACT)

- The plateau target is still a **requirement**, not a formula from fold geometry — the largest gap,
  listed first among the risks, and the reason §6.1's fold-count model is labelled an estimate.
- $P_1=0.75$ remains a judgement; a first real drop would replace it.
- The rebound margin on the top stack is 3%, and the obliquity capacity is 1.05× the no-aero bound
  (29.6°); both are thin and are stated as conditions, not as margins to be proud of.
- The assembly time (29 min) is an estimate like the masses; it is only checked as a table sum.
