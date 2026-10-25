# PDCA status — egg-drop — cycle 1

- Task slug: `egg-drop`
- Workspace root: `/home/alex/sources/skills`
- Status file: `.pdca/status/egg-drop-1.md`
- Evidence dir (revision 1): `.pdca/egg-drop/rv1/`
- Attempt dir (generation c1-r1-n1, frozen): `.pdca/egg-drop/rv1/attempts/c1-r1-n1/`
- Attempt dir (generation c1-r1-n2, frozen): `.pdca/egg-drop/rv1/attempts/c1-r1-n2/`
- Attempt dir (current, c1-r1-n3 — final corrective generation of r=1): `.pdca/egg-drop/rv1/attempts/c1-r1-n3/`
- Spec (read-only input): `experiments/egg-drop/egg-drop-test.md` (289 lines, sha256 `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e`)
- Mode: `autonomous` (no approval gate)
- Started (UTC, observed): `2026-10-24T14:18:20Z`
- Closed (UTC, ACT): `2026-10-24T16:05:00Z`
- Status: `done`

## Durable state

- Current cycle N: 1
- Plan revision r: 1 (unchanged: the two CHECK loop-backs are corrective attempts, not replans)
- Attempt n: 3 (final corrective generation of revision r=1; attempts 1 and 2 failed CHECK)
- Contract revision rv: 1
- Mode: autonomous (no approval gate)
- Status: done
- Phase: ACT closed (pass on attempt 3/3, revision r=1, cycle N=1, rv=1) — CHECK verdict `pass`
  at 2026-10-24T15:41:43Z, ACT closed 2026-10-24T16:05:00Z
- Active units: none — all three units `done` and closed at ACT: D1 `done` (n=3: probe at 436 g /
  159.6 mm with ΔU_g, per-check `min_selected`, `INSET_PANELS` + its fixture), D2 `done` (n=3:
  answer.md 921 lines, sha256 `7a67e1a9…`, after the last edit), D3 `done` (n=3: six logs with
  distinct timestamps, review.md, manifest.json 12/12) — attempts 1 and 2 stay frozen
- Rejected candidates: attempt 1 (c1-r1-n1) — 8 of 12 AC unmet; attempt 2 (c1-r1-n2) — 6 of 12 AC
  unmet; neither is a new plan revision, so r stays 1 and this is attempt 3 of 3
- Superseded→replacement mapping: none (no unit was replaced; D1–D3 were reopened in place in both
  attempts)

### Defect history (stable keys)

Format: key — severity — criteria — observed revisions/attempts — applied fixes — evidence — status.

| Key | Sev | Criteria | Observed | Fixes applied | Evidence | Status |
|---|---|---|---|---|---|---|
| `DEF-ALL-SIDES-PROTECTION` | **P0** | AC8, AC11, AC2, spec §7.3/§7.4 | r=1/n=1 | 1 (n=2) | `.pdca/egg-drop/rv1/attempts/c1-r1-n1/manifest.json` rows AC8/AC11 (CHECK `unmet`); `answer.md:400-401` ("сверху всего 20 мм, перевёрнутый сброс почти наверняка фатален") | **closed in n=2 CHECK**, fixes 1 |
| `DEF-WALL-CAVITY-GEOMETRY` | P1 | AC2, AC11, AC12 | r=1/n=1 | 1 (n=2) | n=1 `manifest.json` AC2/AC11 (CHECK `unmet`); `answer.md:118` (1.5 mm) vs `:283`/`:520` (10 mm) | **closed in n=2 CHECK**, fixes 1 |
| `DEF-PROSE-MATH-CONTRADICTIONS` | P1 | AC3, AC6, AC9, AC10, AC11, AC12, spec §7.2 | r=1/n=1 | 1 (n=2) | n=1 `manifest.json` AC3/AC6/AC9/AC10 (CHECK `unmet`); `answer.md:155-156` (price doubling), `:346` (187 g at 160 mm), `:379-381` (avg/peak mixed), `:413-424` (415 vs 355 g) | **closed in n=2 CHECK**, fixes 1 |
| `DEF-ENERGY-GRAVITY-BOOKKEEPING` | P1 | AC8, AC11, AC12 | r=1/n=1 | 1 (n=2) | n=1 `manifest.json` AC11 (CHECK `unmet`); `answer.md:268-272` (`E_stack + E_egg` without the free-body ratio, no `m g s` term) | **closed in n=2 CHECK**, fixes 1 |
| `DEF-UNLABELLED-CLAIMS-AND-SPEC-WINDOW` | P1 | AC3, AC9, spec §7.2 | r=1/n=1 | 1 (n=2) | n=1 `manifest.json` AC3/AC9 (CHECK `unmet`); `answer.md:69`, `:77-78`, `:80`, `:226`, `:339`, `:377` (unlabelled paper properties); `egg-drop-test.md:152` window unused | **closed in n=2 CHECK**, fixes 1 |
| `DEF-EVIDENCE-LOG-MISMATCH` | P1 | AC12 | r=1/n=1 | 1 (n=2) | n=1 `manifest.json` AC12 (CHECK `unmet`); n=1 `review.md:106` (broken transcript pointer), `review.md:78` vs `content.json:T_WEAK` (`bullets=13`), six logs sharing `started_utc` 2026-10-24T14:30:45Z while the claims they cover close later | **closed in n=2 CHECK**, fixes 1 |

All six attempt-1 keys were confirmed fixed by the attempt-2 CHECK (each: 1 applied fix, closed in
n=2 CHECK) and stay at fixes=1; they are not reopened, because attempt 3 changes none of the areas
they cover. The six AC that the attempt-2 CHECK rejected were carried by four NEW keys (below), all
opened at r=1/n=2 with fixes=0 and `open → fixing n=3`. The executor does not close a defect: a new
key is closed only by a CHECK pass with a review pointer, and a recurrence reopens it with an
incremented count. Evidence generation: `c1-r1-n3`.

**ACT closure (n=3 CHECK, `pass`).** All four keys below were fixed once each in attempt 3 and are
**closed in n=3 CHECK** with fixes=1; no key is open and none was escalated. Closure pointers:
`.pdca/egg-drop/rv1/attempts/c1-r1-n3/manifest.json` → `triage.closed_defects` (all four keys) and
`…/c1-r1-n3/review.md` (per-AC review with `answer.md` line pointers). The four keys did not recur
in n=3.

| Key | Sev | Criteria | Observed | Fixes applied | Evidence | Status |
|---|---|---|---|---|---|---|
| `DEF-LID-BED-CLEARANCE-DIMS` | **P1** | AC2, AC5, AC12, spec §7.1 | r=1/n=2 → n=3 | 1 (n=3) | n=2 `manifest.json` triage rows AC2/AC5 (`unmet`); `answer.md:66`/`:76` (lid/floor 250×250 outside 300 mm walls ⇒ 310 mm), `:91` (190+5+5=200 vs 210), `:160` (4 × 70×70 pads in a 90×80 bed), `:377` («свободного хода нет ни на одной грани»); closure: n=3 `manifest.json` `triage.closed_defects`, `…/c1-r1-n3/review.md` | **closed in n=3 CHECK**, fixes 1 |
| `DEF-IMPROVEMENT-STROKE-AND-COTTON` | **P1** | AC10, AC12, spec §7.2 | r=1/n=2 → n=3 | 1 (n=3) | n=2 triage row AC10; `answer.md:686` (δ_egg 10 → 8 mm with thicker cotton), `:696` (169.2 mm validated against the 210 mm nominal cavity); closure: n=3 `manifest.json` `triage.closed_defects`, `…/c1-r1-n3/review.md` (AC10) | **closed in n=3 CHECK**, fixes 1 |
| `DEF-SCATTERED-NUMBERS-AND-DRAG` | **P1** | AC3, AC9, AC12, spec §7.2 | r=1/n=2 → n=3 | 1 (n=3) | n=2 triage rows AC3/AC9; `answer.md:437` (F_D = 8.26 N vs 6.01 N at C_d = 0.8), `:467` (263 g) vs `:595` (264.6 g), `:492` (988) vs `:596` (988.4), `:594` (1501.6) vs `:593-596` chain, `:587-588` (unlabelled «~50/~10 мм»); closure: n=3 `manifest.json` `triage.closed_defects`, `…/c1-r1-n3/review.md` (AC3/AC9/AC12) | **closed in n=3 CHECK**, fixes 1 |
| `DEF-PROBE-AND-SELECTOR-SYNC` | **P1** | AC12 | r=1/n=2 → n=3 | 1 (n=3) | n=2 triage row AC12; `verify.py:1144-1146` (probe at 400 g / 160 mm), `verify.py:1378` (`min_selected: 1`), `answer.md:746` (`"revision": 2`); closure: n=3 `manifest.json` `triage.closed_defects` + rows AC3/AC12, `…/c1-r1-n3/review.md` (AC12) | **closed in n=3 CHECK**, fixes 1 |

## 1. Goal / expected result

Produce `experiments/egg-drop/answer.md` — a complete Russian-language Markdown engineering answer
for the Egg Drop task, **scenario A** (10 m, concrete, ≤500 g, ≤$5), per
`experiments/egg-drop/egg-drop-test.md` §4 and §6: concept, specification (masses, dimensions,
attachment, total mass, total budget), physical calculations, reliability estimate, alternatives,
iterations. All calculations must be physically correct, numerically self-consistent, and
**independently recomputable** from the document's own inputs — not merely asserted.

Out of scope for this cycle: physical build, fabrication, real drop testing, measured data.

## 2. Constraints

### 2.1 Task constraints (from the spec — must not be fabricated or relaxed)

| Constraint | Value |
|---|---|
| Drop height H | 10.0 m |
| Landing surface | concrete, rigid, non-deformable |
| Total system mass incl. egg | ≤ 500 g |
| Max any single dimension | ≤ 300 mm |
| Max volume | ≤ 0.02 m³ (20 L) |
| Materials budget | ≤ $5.00 |
| Assembly time | ≤ 30 min (stated in answer, not verified) |
| Allowed materials | paper, cardboard, straws, toothpicks, rubber bands, tape, rope, plastic bags, balloons, cotton wool, foam rubber, styrofoam, plastic bottles, egg cartons |
| Forbidden | metal, glass, rigid plastic > 2 mm, glue other than tape, ready-made shock absorbers |
| Egg attachment | egg must not be glued; rubber bands / rope only |
| Egg protected | from **all sides** |
| Braking path | must exist — a rigid attachment to the outer shell is a failure criterion |

### 2.2 Process constraints (this cycle)

- Footprint: `experiments/egg-drop/` and `.pdca/` only.
- No git write commands (no add/commit/push/branch/checkout/stash/restore).
- No edits to `skills/`, `config/`, `opencode/`, `~/.config/opencode`, or the spec file
  `experiments/egg-drop/egg-drop-test.md`.
- `python3` stdlib only; observed interpreter `Python 3.10.12` (`/usr/bin/python3`) — **no
  3.11+ features** (`tomllib`, `ExceptionGroup`/`except*`, `typing.Self`).
- No fabricated measurements, no fabricated spec content, no measurements implied to have been
  performed when they were not.

## 3. Assumptions (explicit, must be visible in the answer)

1. Material prices are **indicative retail estimates** (2026, generic), not quotations.
2. Component masses are **design estimates with margin**; the device must be weighed before any
   real test.
3. Paper is dry, concrete is flat and level, no wind (per spec).
4. Paper crush properties, peak factor, and all probabilities are **not measured**; they are model
   inputs with stated uncertainty.
5. Δt (braking time) and η (absorption efficiency) are **not given by the spec** and must be
   **derived** from a chosen, justified force profile — not assumed independently of geometry.
6. A computed energy-absorption requirement is **not** proof that folded paper can deliver it.
   The answer states the requirement, the model used, and its uncertainty; it does not claim a
   verified device.
7. Scenario A only; other scenarios in spec §8 are out of scope (20 m is required only as an
   iteration discussion, §4.6).

## 4. Acceptance criteria (AC1–AC12)

Each AC names its verification method and the frozen command(s) that prove it. Commands are
`python3 .pdca/egg-drop/rv1/verify.py …`; log paths are under
`.pdca/egg-drop/rv1/attempts/c1-r1-n1/`. Command IDs C1–C6 are defined in §9.

| ID | Criterion | Verification | Command / evidence |
|---|---|---|---|
| AC1 | `answer.md` exists and contains the six mandatory sections **in spec order**: `## 1. Концепция`, `## 2. Спецификация`, `## 3. Физические расчёты`, `## 4. Оценка надёжности`, `## 5. Альтернативы`, `## 6. Итерации`; the document is Russian, formulas are LaTeX (`$…$`/`$$…$$`), dimensions in mm, masses in g, energy in J, force in N. | `structure` (≥6 headings, ≥7 numeric items with units) | C3 → `structure.json` |
| AC2 | Every required subsection of spec §4.1–4.6 is present **and substantive**: design name + operating principle + textual/ASCII scheme; full BOM with masses; all element dimensions in mm; egg attachment method; total mass; total budget; v_impact, E_k, Δt, F_peak, n, η, verdict; P(1 drop), P(3 consecutive), weak points, failure modes; ≥2 alternatives with mass/cost/reliability; post-test improvements and 20 m behaviour. No `TBD`/placeholder text. | `content` (≥12 presence/format checks) + manual review | C6 → `content.json`; review item `manual review against AC2` in `review.md` |
| AC3 | Drop kinematics are computed for H = 10.0 m, g = 9.81 m/s²: `v_impact = sqrt(2gH)` = 14.01 m/s, `t_fall = sqrt(2H/g)` = 1.43 s, and `E_k = ½ m_total v²` at the stated m_total (≈49 J at 0.5 kg). Values appear in the prose/tables **and** recompute within tolerance from the document's own inputs. Air drag, if used, is computed via `v_term = sqrt(2mg/(ρ C_d A))` and not mixed into the no-drag result silently. | `physics` (≥2 heights, ≥7 base results) + `structure` | C4 → `physics.json`; C3 → `structure.json` |
| AC4 | Total mass including the egg is ≤ 500 g; the BOM masses sum to the stated total within ±1 g; the margin to 500 g is stated explicitly. | `constraints` (BOM row sums, mass limit) | C5 → `constraints.json` |
| AC5 | Every external dimension is ≤ 300 mm **and** the bounding volume is ≤ 0.02 m³ (equivalent cube edge at 0.02 m³ is 271.4 mm, so volume binds tighter than the side limit); the composition hypothesis 270×270×270 mm = 19 683 000 mm³ = 19.683 L is checked. | `constraints` + manual review | C5 → `constraints.json`; `manual review against AC5` |
| AC6 | The priced BOM sums to ≤ $5.00 within $0.01, including tape/consumables; per-item unit prices and quantities are shown; the total appears in the specification section. | `constraints` (budget) | C5 → `constraints.json` |
| AC7 | Only allowed materials are used; no forbidden item (metal, glass, rigid plastic > 2 mm, glue other than tape, ready-made shock absorbers) appears; the egg is not glued and is held by rubber bands/rope; the answer says so explicitly. | `constraints` (material allow/deny list) + manual review | C5 → `constraints.json`; `manual review against AC7` |
| AC8 | Δt and η are **derived, not asserted**: the answer states the force profile (e.g. plateau `F_y` over stroke `s`, `E_abs = F_y · s`), the average deceleration `a_avg = v²/(2s)`, `Δt ≈ 2s/v` (or from momentum `Δt = m·v/F_avg`), `η = E_abs/E_k`, and the requirement `E_egg = E_k(1−η) < E_crit = 1.0 J ⇒ η > 0.98`. The requirement is labelled a requirement (not proof of paper's capability). Self-consistency: the same `F_y`, `s` produce Δt, η and F_peak used elsewhere. | `physics` + manual review | C4 → `physics.json`; `manual review against AC8` |
| AC9 | Reliability section gives P(survive 1 drop) and P(3 consecutive drops) with an **explicit probability model** (e.g. independence `P3 = P1³`, plus the caveat that independence is optimistic after a first impact), a weakest-link list, and a failure-mode list; probabilities are clearly model estimates, not measured frequencies. | `content` + manual review | C6 → `content.json`; `manual review against AC9` |
| AC10 | ≥2 alternatives (B: parachute + crushable container; C: rubber-band suspension + soft shell) are compared by mass, cost and reliability, with numbers; the 20 m iteration is recalculated (v ≈ 19.8 m/s, E_k ≈ 98 J at 0.5 kg, Δx_min and required stroke scaling) and stays self-consistent with the stated model. | `physics` + `content` + manual review | C4 → `physics.json`; C6 → `content.json`; `manual review against AC10` |
| AC11 | A braking path is proven to exist: `Δx_min = v²/(2 n_crit g)` is computed for the chosen `n_crit`, the design stroke is ≥ Δx_min, and the stroke is **derived from geometry** — shell thickness → internal bed cavity → number/thickness of folded layers (usable stroke ≥ 100 mm must be derivable, not declared). No rigid load path from egg to outer shell; the egg-to-shell chain contains only compliant elements. | `physics` + manual review | C4 → `physics.json`; `manual review against AC11` |
| AC12 | Numerical self-consistency: every headline number (mass, budget, dimensions, energies, forces, g-load, probabilities) traces to the single machine-readable model block and to at most one arithmetic chain; no section contradicts another; `verify.py` recomputes claimed outputs from inputs; the review independently recomputes at least mass total, energy, stroke and η by hand. | `structure` + `content` + manual review | C3 → `structure.json`; C6 → `content.json`; `manual review against AC12` |

Tolerances (pinned): mass ±1 g, budget ±$0.01, dimension exact to stated integer mm, velocity ±0.05 m/s, energy ±0.5 J, force ±5 %, η ±0.005, probability ±0.02 absolute (as declared model output).

## 5. Units of work

| Unit | State | Scope | Covers | Depends on | Owner |
|---|---|---|---|---|---|
| D1 | `done` (n=3, closed 2026-10-24T15:41:43Z) | Implement `.pdca/egg-drop/rv1/verify.py` (python3 3.10 stdlib only): pure check functions over document text + CLI; probe geometry/energy model for 10 m and 20 m **at the document's own m = 436 g and s = 159.6 mm, with the gravity term**, explicitly labelled "not proof of survival"; per-check `min_selected` (probe 2, selftest 8, structure 6, physics 7, constraints 6, content 12) enforced as a hard failure; ≥8 embedded negative fixtures with IDs `HEADING`, `MISSING_NUMBER`, `MASS_LIMIT`, `BUDGET_LIMIT`, `MATERIAL`, `STROKE`, `LANGUAGE`, `CHAIN` (12 in n=3, including `INSET_PANELS`). | Provides evidence for AC1, AC3–AC8, AC10–AC12; selftest integrity for all rows | — | `pdca-executor` |
| D2 | `done` (n=3, closed 2026-10-24T15:41:43Z) | Write `experiments/egg-drop/answer.md` in Russian: sections 1–6 per spec §6, full BOM/masses/prices/dimensions, derived Δt/η/force profile, reliability with explicit probability model, alternatives B and C, iterations incl. 20 m; plus the machine-readable model block (§10.4). n=3 corrective pass: R1–R15 (inset lid/floor, pad sizes, straw clearance, free-stroke statement, §6.1 arithmetic, cotton compliance, single-value numbers, drag, model revision). | Primary artifact for AC1–AC3, AC8–AC12; content for AC4–AC7 | D1 (model/numbers must match the checker's recomputation) | `pdca-executor` |
| D3 | `done` (n=3, closed 2026-10-24T15:41:43Z) | Run C1–C6 into `c1-r1-n3/`, write `review.md` (manual review items per AC), fill `manifest.json` rows with evidence refs, verify AC1–AC12 at gate 2. | AC1–AC12 acceptance | D1, D2 | `pdca-executor` |

No unit is `done` until its criteria are verified at gate 2 with recorded evidence. After the
attempt-2 CHECK the three units were `running` again in place: none is `superseded`, none has a
replacement, and their scope and acceptance criteria are unchanged — only the evidence generation
(`c1-r1-n3`) and the corrective edits are new. An additive prerequisite was not needed: the fix
scope fits inside D1/D2/D3. n=3 is the last generation of revision r=1: if CHECK rejects it again,
the cycle must go to ACT (escalation), not to a fourth generation.

## 6. Means and access

Files and dirs to create (all inside the allowed footprint):

| Path | Purpose |
|---|---|
| `experiments/egg-drop/answer.md` | the deliverable (D2) |
| `.pdca/egg-drop/rv1/verify.py` | checker (D1) |
| `.pdca/egg-drop/rv1/attempts/c1-r1-n1/{probe,selftest,structure,physics,constraints,content}.json` | execution logs (C1–C6) |
| `.pdca/egg-drop/rv1/attempts/c1-r1-n1/review.md` | manual-review evidence, one section per AC (`file:line` pointers required) |
| `.pdca/egg-drop/rv1/attempts/c1-r1-n1/manifest.json` | evidence manifest (already created with all rows `open`) |
| `.pdca/egg-drop/rv1/attempts/c1-r1-n1/gate1-contract-validation.log` | gate-1 validation transcript (already created) |

Tools: `python3` 3.10.12 (stdlib), shell, editors. No network dependency required; MCP not needed.

## 7. Evidence manifest (pinned)

- Canonical path: `.pdca/egg-drop/rv1/attempts/c1-r1-n1/manifest.json`
- Fields: `task: "egg-drop"`, `revision: 1`, `status_file: ".pdca/status/egg-drop-1.md"`,
  `required: ["AC1" … "AC12"]`, `rows[]` — one per required ID with
  `status: open|met|na` and
  `evidence[]` refs `{kind, path, command, exit, value}`.
- Row mapping (fixed for this revision):
  AC1→structure; AC2→content+review; AC3→physics+structure; AC4→constraints;
  AC5→constraints+review; AC6→constraints; AC7→constraints+review; AC8→physics+review;
  AC9→content+review; AC10→physics+content+review; AC11→physics+review;
  AC12→structure+content+review.
- Kinds: `execution` (verify.py JSON log), `artifact` (the deliverable path + sha256),
  `review` (manual review: `command = "manual review against ACx"`, `exit = null`,
  `value = conclusion + real file:line pointers`).
- A row may be `met` only when every mapped kind for that AC is present and passing.
  `na` requires a recorded justification in `review.md`.

## 8. Risks / known issues

| # | Risk | Severity | Mitigation / how it surfaces in the answer |
|---|---|---|---|
| R1 | Paper crush curve is unproven; folded-paper elements may crush at the wrong load or collapse early | **high** | Energy/force requirement stated as a requirement; plateau stress treated as an assumption with range; verdict is probabilistic, not a guarantee |
| R2 | Excessive peak g-load from too-stiff elements | **high** | Choose `n_crit` conservatively (e.g. 100 g), derive required `F_peak` at the egg boundary, keep `F_y` well below the shell limit, report the chain |
| R3 | Damper punch-through (stroke exhausted → bottoming out on concrete) | medium | Stroke budget with margin; bottom-out case calculated and named as a failure mode |
| R4 | Rigid load bridge from fixation (tape/string path transmits shock directly) | **high** | All load paths through compliant elements; geometric check that no rigid member touches both egg and shell; failure criterion from spec §7 explicitly addressed |
| R5 | Insufficient stroke after compaction (paper densifies, usable stroke < Δx_min) | **high** | Usable stroke derived from layer count × per-layer crush, not from nominal cavity height; ≥100 mm derivation shown |
| R6 | Probability estimates are model artefacts, not data | medium | Explicit model + assumptions + wide uncertainty; no measured-frequency language |
| R7 | Prices are optimistic / region-dependent | medium | Prices labelled indicative; total kept with headroom under $5 |

## 9. Command contract (validated)

Frozen interface (validated against a throwaway stub in `/tmp/opencode/verify_stub.py`; no
`verify.py` created yet):

```
python3 /home/alex/sources/skills/.pdca/egg-drop/rv1/verify.py \
  --repo /home/alex/sources/skills \
  [--document experiments/egg-drop/answer.md] \
  --check {probe|selftest|structure|physics|constraints|content} \
  --log <path>
```

- `--repo` required, must be an existing directory (used to resolve relative `--document` and to
  confirm the spec file).
- `--document` **required** for `structure|physics|constraints|content` (missing → exit 2),
  **omitted** for `probe|selftest`.
- `--check` required, exactly the six values above; anything else → exit 2.
- `--log` required; parent directory is created if absent; the JSON log is the only evidence format.
- Exit codes: `0` all selected checks pass, `1` at least one check fails / corruption undetected,
  `2` usage error.
- Log JSON fields: `check`, `selector`, `started_utc`, `repo`, `document`, `status`,
  `counts{selected,passed,failed,skipped}`, `results[{id,ok,expected,observed,detail}]`,
  `limits` (explicitly recorded model limits), `note`.

Environment facts observed: `python3` = `/usr/bin/python3`, `Python 3.10.12`; repo path exists;
attempt log dir created and writable; `experiments/egg-drop/answer.md` absent (expected until D2).

| ID | Selector | Purpose | Min selected | Expected outcome | Log | Validation result (observed) |
|---|---|---|---|---|---|---|
| C1 | `probe` | Geometry/energy probe for 10 m and 20 m; records model limits, explicitly **not** proof of survival | ≥1 geometry model, ≥2 heights | exit 0; timings/energies present; `limits` non-empty | `…/c1-r1-n1/probe.json` | **argv accepted, exit 0** (stub); selector resolution deferred to D1 |
| C2 | `selftest` | 8 embedded negative fixtures must each be rejected with the expected ID | ≥8 fixtures | exit 0 only if all 8 reject with `HEADING`, `MISSING_NUMBER`, `MASS_LIMIT`, `BUDGET_LIMIT`, `MATERIAL`, `STROKE`, `LANGUAGE`, `CHAIN`; an undetected corruption → exit 1 | `…/c1-r1-n1/selftest.json` | **argv accepted, exit 0** (stub); selector resolution deferred to D1 |
| C3 | `structure` | Headings, section order, numeric items with units, LaTeX presence | ≥6 headings, ≥7 numeric items | exit 0 | `…/c1-r1-n1/structure.json` | **argv accepted, exit 0** (stub); `--document` absent → *expected-negative until D2*; selector resolution deferred to D3 |
| C4 | `physics` | Recompute v, E_k, Δt, F_peak, n, η, E_egg, Δx_min, 20 m case from the model block | ≥2 heights, ≥7 base results | exit 0 | `…/c1-r1-n1/physics.json` | **argv accepted, exit 0** (stub); `--document` absent → *expected-negative until D2*; selector resolution deferred to D3 |
| C5 | `constraints` | BOM mass/budget sums, dimension limits, volume, material allow/deny, egg attachment | ≥1 row of each BOM table, ≥6 limit/material checks | exit 0 | `…/c1-r1-n1/constraints.json` | **argv accepted, exit 0** (stub); `--document` absent → *expected-negative until D2*; selector resolution deferred to D3 |
| C6 | `content` | Presence/format of the 12 AC-relevant content items (sections 1–6 subsections, reliability, alternatives, iterations) | ≥12 checks | exit 0 | `…/c1-r1-n1/content.json` | **argv accepted, exit 0** (stub); `--document` absent → *expected-negative until D2*; selector resolution deferred to D3 |

Observed validation detail (full transcript:
`.pdca/egg-drop/rv1/attempts/c1-r1-n1/gate1-contract-validation.log`, 45 lines, executed
`2026-10-24T14:18:44Z`):

1. `CMD1_probe` — stub exit **0**; `repo_exists: true`, `log_dir_writable: true`, selective `check` accepted.
2. `CMD2_selftest` — stub exit **0**; same environment facts.
3. `CMD3_structure` — stub exit **0**; `document: "experiments/egg-drop/answer.md"`, `document_exists: false`.
4. `CMD4_physics` — stub exit **0**; same.
5. `CMD5_constraints` — stub exit **0**; same.
6. `CMD6_content` — stub exit **0**; same.
7. Negative fixture `--check bogus` — exit **2**, argparse rejects unknown selector (proves the
   four/six-value gate is enforceable).
8. Negative fixture `test -f experiments/egg-drop/answer.md` — exit **1**, recorded as
   `expected-negative: document absent until D2` (identity: missing deliverable).

Validation verdict: **gate 1 satisfied — ready**. All six argv vectors survive quoting/expansion
unchanged, the log directory is writable, the repo path resolves, and the only failing observation
is the declared expected-negative (document absent). Selector **content** resolution (which cases
each selector must select) is deferred to D1 for `probe`/`selftest` and to D3 for the other four,
and is re-validated before first use, as planned.

## 10. Decisions made

### 10.1 Concept A chosen — folded-paper crushable elements on all sides

Named concept: **«Бумажный кокон»** — a 270 mm cube cardboard/paper shell; the egg sits in a
compact bed (egg-carton cup + cotton/foam) at the centre; folded-paper crushable columns (accordion
folds) on all six faces between the bed and the outer shell; egg held by rubber bands/string, not
glued; tape joints only.

Energy path: egg → bed (distributed contact) → folded-paper stacks → outer shell → floor. Only
compliant elements are in series; no rigid member touches both the egg and the outer shell.

### 10.2 Alternatives considered

| Concept | Pros | Cons | Verdict |
|---|---|---|---|
| **A. Folded-paper crushable elements (chosen)** | All materials allowed and cheap; crush stroke and plateau force are designable from fold geometry; load path is inspectable; no dependence on deployment; fully verifiable on paper | Paper crush curve unproven; sensitive to moisture; stroke limited by 270 mm envelope; punch-through if folds bottom out | Chosen: the **most verifiable** paper project — the mechanism is deterministic geometry, and every claim can be recomputed from dimensions |
| B. Parachute + crushable container | Reduces impact velocity (drag), dividing E_k; familiar | Deployment is a single point of failure; Cd and opening transient are hard to justify; needs ≥10 m to be effective; adds mass high up; spec scenario A has no wind; deployment reliability is a guess | Rejected as primary; kept as an alternative with numbers |
| C. Rubber-band suspension + soft shell | Cheap, reusable, good for small drops | Rubber-band stiffness is nonlinear and hard to characterise; needs long stroke in a small envelope; snap-back can re-accelerate the egg; energy capacity per mass is lower at 10 m | Rejected as primary; kept as an alternative |

A is explicitly **not** presented as a proven reliable device: its survival probability is a model
estimate resting on unmeasured paper crush behaviour (R1) and on the assumed `n_crit` (R2).

### 10.3 Composition hypothesis (must be made self-consistent in D2)

- Outer shell: ≈270 × 270 × 270 mm (each side ≤300 mm).
- Bounding volume: 270³ = **19 683 000 mm³ = 19.683 L** ≤ 0.02 m³ (20 L) — passes with 0.317 L
  headroom; note that at the 300 mm side limit the volume would be 27 L and violate the 0.02 m³
  cap, so the volume is the binding constraint (equivalent cube edge 271.4 mm).
- Bed around the egg: compact cavity ≈ 70 × 70 × 95 mm (egg 29 × 21 × 21 mm plus bed thickness),
  centred.
- Folded-paper stack: per face thickness = (270 − bed)/2; usable stroke ≥100 mm must be derived as
  `stack height × crush fraction` summed over the faces in the load direction, with layer count ×
  per-layer crush given explicitly — not declared.
- Mass target: leave ≥30 g headroom under 500 g for tape, string and weighing error.
- Budget target: ≤ $4.50 priced, leaving ≥ $0.50 contingency under $5 (R7).

### 10.4 Interface decision enabling the frozen checks

`answer.md` carries, in addition to the human-readable sections, one fenced machine-readable model
block (JSON) containing inputs (`H`, `g`, `m_egg`, `m_total`, `A_contact`, `E_crit`, `n_crit`,
outer dimensions, bed dimensions, layer count/thickness, `F_y`, stroke `s`, BOM rows with
`mass_g`/`price_usd`, probabilities `P1`) and claimed outputs (`v_impact`, `t_fall`, `E_k`,
`dt`, `F_peak`, `n`, `eta`, `E_egg`, `dx_min`, `P3`). `verify.py` recomputes outputs from inputs
within the tolerances in §4 and cross-checks that the same numbers appear in prose/tables. This
keeps the human answer primary and makes verification mechanical rather than textual; it adds no
claim that the spec does not ask for.

## 11. Deferred + trigger

- **Deferred:** post-test improvements (spec §4.6 "what would you improve after the first test") are
  described as a plan only; nothing is measured. Physical build, fabrication and the first real drop
  are **out of scope** for this cycle.
- **Trigger** for acting on the deferred items: the **first real physical drop** of a built device —
  then the measured crush curve, actual mass/budget and observed failure mode replace the model
  assumptions (R1, R2, R4, R6) and the iteration section is updated with data.
- Also deferred: scenarios B–F (spec §8); only the 20 m iteration discussion required by §4.6 is in
  scope.

## 12. Next plan

**No cycle 2 (N=2) is planned now.** Cycle 1 is closed `done` (r=1, n=3, rv=1, CHECK `pass`).

The trigger for opening a cycle 2 is the **first real physical drop test** of a built device — the
§6 deferred item (spec §6 / §11 above): build the device, weigh it, measure the real crush behaviour,
run the 10 m drop, then open a new cycle whose D-units update the crush curve, mass/budget actuals,
the failure modes and §6 iterations with measured data (and, only then, clean up the editorial/log
notes listed in §19). Until that measurement exists the task is complete and no further cycle is
planned — an empty cycle 2 would only re-run the same model against itself.

## 13. Progress log

```
2026-10-24T14:18:20Z | PLAN | revision 1 | iteration 1/3 | PLAN ready — autonomous mode, no approval gate | .pdca/status/egg-drop-1.md
2026-10-24T14:19:10Z | PLAN | revision 1 | iteration 1/3 | PLAN persisted to status file by pdca-executor | .pdca/status/egg-drop-1.md
2026-10-24T14:19:10Z | PLAN | revision 1 | iteration 1/3 | Command contract validation — ready (6/6 argv accepted, exit 0; unknown selector exit 2; document absent = expected-negative; validation executed 2026-10-24T14:18:44Z) | .pdca/egg-drop/rv1/attempts/c1-r1-n1/gate1-contract-validation.log
2026-10-24T14:22:10Z | DO | revision 1 | iteration 1/3 | DO started — units D1→D2→D3 sequential, owner pdca-executor | .pdca/status/egg-drop-1.md
2026-10-24T14:25:23Z | DO | revision 1 | iteration 1/3 | D1 closed `done` — verify.py written; probe 21/21 exit 0; selftest 10/10 exit 0 (8/8 corruptions rejected, 0 undetected) | .pdca/egg-drop/rv1/attempts/c1-r1-n1/probe.json, .pdca/egg-drop/rv1/attempts/c1-r1-n1/selftest.json
2026-10-24T14:36:02Z | DO | revision 1 | iteration 1/3 | D2 closed `done` — answer.md written (584 lines): 400 g, 3.00 $, 300 mm, 18 750 000 mm3, v=14.01 m/s, E_k=39.24 J, n=93.8 g, eta=0.985, verdict "вероятно" | experiments/egg-drop/answer.md
2026-10-24T14:41:10Z | DO | revision 1 | iteration 1/3 | D3 closed `done` — C1..C6 exit 0 (probe 21/21, selftest 10/10, structure 7/7, physics 16/16, constraints 11/11, content 20/20); review.md and manifest.json written, 12/12 rows met | .pdca/egg-drop/rv1/attempts/c1-r1-n1/checks-transcript.log
2026-10-24T14:41:10Z | DO | revision 1 | iteration 1/3 | DO → CHECK transition — all three units closed, no blocker, no scope change | .pdca/egg-drop/rv1/attempts/c1-r1-n1/manifest.json
2026-10-24T14:50:22Z | CHECK | revision 1 | iteration 1/3 | CHECK failed — 4 met (AC1, AC4, AC5, AC7), 8 unmet (AC2, AC3, AC6, AC8, AC9, AC10, AC11, AC12); P0 defect DEF-ALL-SIDES-PROTECTION opened; 8 superseding triage rows appended to the frozen manifest | .pdca/egg-drop/rv1/attempts/c1-r1-n1/manifest.json
2026-10-24T14:50:22Z | CHECK → DO | revision 1 | iteration 2/3 | loop-back without replan (r stays 1, n 1→2); new evidence generation c1-r1-n2; D1/D2/D3 reopened `running`, none superseded; 6 defect keys open, fix count 0 | .pdca/status/egg-drop-1.md
2026-10-24T14:52:40Z | DO | revision 1 | iteration 2/3 | D2 rewritten — answer.md 584→865 lines: bottom 159.6 mm / top 15.2 mm / lateral 57.0 (X) and 60.8 (Y) mm; 436 g; 3.17 $; walls 5 mm=10 mm; dU_g included (0.683 J, 1.60%); n_peak 95.5 g; theta_max 31 deg | experiments/egg-drop/answer.md
2026-10-24T14:56:10Z | DO | revision 1 | iteration 2/3 | D1 updated — verify.py: gravity in phys(), TOP_STROKE, LATERAL_STROKE, GRAVITY_TERM, WALL_TABLE, WALL_CHAIN, per-block bullet counts; fixtures 8→11; selftest 13/13 exit 0 | .pdca/egg-drop/rv1/verify.py
2026-10-24T14:59:05Z | DO | revision 1 | iteration 2/3 | D3 closed `done` — C1..C6 exit 0 (probe 21/21, selftest 13/13, structure 7/7, physics 19/19, constraints 13/13, content 21/21), six distinct started_utc, review.md + manifest.json 12/12 met, doc sha b254ced7… | .pdca/egg-drop/rv1/attempts/c1-r1-n2/checks-transcript.log
2026-10-24T14:59:05Z | DO → CHECK | revision 1 | iteration 2/3 | attempt 2 closed — 6 defect keys at fix count 1, awaiting CHECK; no unit superseded, no blocker, no scope change | .pdca/egg-drop/rv1/attempts/c1-r1-n2/manifest.json
2026-10-24T15:02:00Z | CHECK | revision 1 | iteration 2/3 | CHECK attempt 2 failed — 6 met (AC1, AC4, AC6, AC7, AC8, AC11), 6 unmet (AC2, AC3, AC5, AC9, AC10, AC12); four new P1 defect keys opened; six triage rows appended to the frozen n=2 manifest (append-only, 12 DO rows untouched) | .pdca/egg-drop/rv1/attempts/c1-r1-n2/manifest.json
2026-10-24T15:02:00Z | CHECK → DO | revision 1 | iteration 3/3 | loop-back #2 without replan (r stays 1, n 2→3, final corrective generation); new evidence generation c1-r1-n3; D1/D2/D3 reopened `running`, none superseded; 4 new keys at fixes 0 → fixing, 6 old keys closed in n=2 CHECK | .pdca/status/egg-drop-1.md
2026-10-24T15:30:00Z | DO | revision 1 | iteration 3/3 | D2 rewritten in place — answer.md 865→921 lines: inset lid/floor 240×240×5 (outer height 300, not 310), pads 4×(40×35×8) in the corner quadrants, straws 190+10+10=210, quantified free-stroke paragraph, §6.1 held at 272.3 N with k_peak 1.50→1.35 (F_peak 367.6 N, n_peak 85.9 g), cotton 8→12 mm raises δ_egg (50.8 N / 0.051 MPa), single values 264.6 / 988.4 / 1501.5 g and 31.4°, F_D 6.01 N, model revision 1 | experiments/egg-drop/answer.md
2026-10-24T15:35:00Z | DO | revision 1 | iteration 3/3 | D1 updated — probe at the document's own 436 g / 159.6 mm with the gravity term, two formula detail strings fixed, per-check min_selected 2/8/6/7/6/12 enforced as a hard failure, new INSET_PANELS check + fixture (12 corruptions) | .pdca/egg-drop/rv1/verify.py
2026-10-24T15:41:43Z | DO | revision 1 | iteration 3/3 | D3 closed `done` — C1..C6 exit 0 (probe 21/21, selftest 14/14, structure 7/7, physics 19/19, constraints 14/14, content 21/21), six distinct started_utc 15:41:42.810Z..15:41:43.084Z, review.md + manifest.json 12/12 met, doc sha 7a67e1a9… / 921 lines | .pdca/egg-drop/rv1/attempts/c1-r1-n3/checks-transcript.log
2026-10-24T15:41:43Z | DO → CHECK | revision 1 | iteration 3/3 | attempt 3 closed — all three units `done`, no blocker, no scope change; 4 new defect keys at fixes 1 awaiting CHECK; final generation of r=1 | .pdca/egg-drop/rv1/attempts/c1-r1-n3/manifest.json
2026-10-24T15:50:00Z | CHECK | revision 1 | iteration 3/3 | CHECK pass (12/12 met, 4/4 n=2 defects closed) — no unmet AC, no escalation trigger, no defect recurrence; triage appended to the n=3 manifest (12 DO rows untouched) | .pdca/egg-drop/rv1/attempts/c1-r1-n3/manifest.json
2026-10-24T16:05:00Z | ACT | revision 1 | iteration 3/3 | ACT closed — cycle 1 complete (Status `done`, N=1, r=1, n=3, rv=1; 6 + 4 defect keys all closed, none escalated; no r=2 planned until the first physical drop) | .pdca/status/egg-drop-1.md
```

## 14. Notices

(seven notices: an envelope change, larger-than-planned margins, two evidence-hygiene/additive-check
notes from attempt 2, the n=3 `row_mapping` change, and the ACT factual-correction notice (in which
this header's own stale count — "five notices" while six were present — was corrected); all are
footprint/size/evidence only, no criterion relaxed, no scope replacement. Gate-1 validation itself
matched the plan.)

`Notice:` the plan's §10.3 composition hypothesis was a 270 × 270 × 270 mm cube (19.683 L). D2
implemented **300 × 250 × 250 mm** (18.75 L, max side exactly 300 mm) instead. Reason: the
270 mm cube leaves only 90 mm of crush cavity above the 60 mm bed after the 20 mm top stack,
which cannot deliver the 150 mm stroke the 100 g peak-limited design needs; the 300 mm axis
gives 210 mm nominal / 160 mm usable stroke. Both limits are still satisfied (300 mm ≤ 300 mm,
18.75 L ≤ 20 L) and the AC5 criterion is unchanged — footprint change only, no criterion was
relaxed, no scope replacement.

`Notice:` cost estimate 3.00 $ leaves a 2.00 $ margin and mass 400 g a 100 g margin; both are
larger than the plan's targets (≤ 4.50 $, ≥ 30 g headroom) because the BOM's shell turned out
lighter than assumed. No criterion was changed by this.

`Notice:` (attempt 2) the frozen generation `c1-r1-n1` was corrected in one place only that is not
part of the manifest: `review.md:106` pointed at a "hand recompute" section of the attempt-1
transcript that never existed, and `review.md:78` stated the weak/failure bullet split while
`content.json:T_WEAK` counted 13 bullets across both lists. Both are corrected in place and the
correction is recorded as a `Notice:` block at the end of `c1-r1-n1/review.md`; the 12 original
manifest rows were not touched (8 CHECK-triage rows were appended after them).

`Notice:` (attempt 2) three checks and three fixtures were **added** to `verify.py`
(`WALL_TABLE`, `WALL_CHAIN`, `TOP_STROKE`, `LATERAL_STROKE`, `GRAVITY_TERM`, `T_WEAK_BULLETS`,
`T_FAILURE_BULLETS`, plus the WALL/LATERAL/BULLETS fixtures) and the physics core now includes the
gravitational work term. No existing check was weakened or removed: the attempt-1 ids all still
exist, and the selftest went from 8 to 11 corruptions, all rejected. `started_utc` gained
millisecond resolution because second resolution let six runs share one stamp.

`Notice:` (attempt 3) one check was **added** to `verify.py` — `INSET_PANELS` (lid and floor must
be inset panels whose plan equals the cavity plan, thickness ≤ 10 mm) with its own fixture
(`lid_oversize`), which the selftest rejects; the fixture's own dimension table was corrected to
the inset geometry and the selftest went from 11 to 12 corruptions, all rejected. No existing
check was weakened or removed: all attempt-1/2 ids still exist, and the new check only closes the
310 mm failure mode that the previous attempts stated as prose.

`Notice:` (attempt 3, `row_mapping` change) the manifest of `c1-r1-n3` maps **AC3 → probe +
physics + structure + review** instead of the n=2 `physics + structure + review`, because the probe
now runs at the document's own inputs (m = 436 g, s = 159.6 mm, with ΔU_g = m·g·s) and can therefore
serve as the independent recomputation AC3 asks for. Every other row keeps the n=2 mapping; adding a
ref only strengthens a row, no criterion and no scope changed. §7's row mapping stays the floor it
was written as; the deltas are recorded in the manifests' `row_mapping_change` field.

`Notice:` (ACT, factual corrections; no content change) two stale count statements in this section
were corrected. (a) This section's header said "five notices" while **six** `Notice:` blocks were
present at the time it was written (the attempt-1 envelope and margin notices, the two attempt-2
notes, the attempt-3 `INSET_PANELS` note and the attempt-3 `row_mapping` note); the header now reads
"seven notices", counting those six historical blocks plus this ACT correction notice. (b) The
attempt-2 notice above says "three checks and three fixtures were **added** to `verify.py`" but then
lists seven check ids (`WALL_TABLE`, `WALL_CHAIN`, `TOP_STROKE`, `LATERAL_STROKE`, `GRAVITY_TERM`,
`T_WEAK_BULLETS`, `T_FAILURE_BULLETS`); the correct figure is **seven checks added**, with three
sampled fixtures (`FIX_WALL_TABLE`, `FIX_LATERAL_STROKE`, `FIX_T_FAILURE_BULLETS` — 12 corruptions in
total at n=3, all rejected, `.pdca/egg-drop/rv1/attempts/c1-r1-n3/selftest.json`). Both are textual
corrections only: no check, fixture, criterion, number or scope changed, and the historical lines
above are left in place unchanged.

## 15. DO evidence (units D1–D3)

### D1 — harness + bounded probe — `done` (closed 2026-10-24T14:25:23Z)

| # | Command (argv) | Exit | Key numbers | Log |
|---|---|---|---|---|
| C1 | `python3 .pdca/egg-drop/rv1/verify.py --repo /home/alex/sources/skills --check probe --log …/probe.json` | **0** | 21/21 selected, 0 failed. 10 m: v=14.0071 m/s, E_k=39.24 J (400 g) / 49.05 J (500 g), Δt=0.02285 s, F_avg=245.2 N, F_peak=367.9 N (k=1.5), n_peak=93.8 g, E_egg=0.598 J, η=0.9848, s_req(n≤100 g)=150 mm ≤ 160 mm achievable. 20 m: v=19.8091 m/s, E_k=78.48 J / 98.1 J, F_peak=735.8 N, n_peak=187.5 g, E_egg=1.196 J > 1.0 J, s_req=300 mm > 160 mm → **blocker for scenario B in a 300 mm box**. k-sensitivity: n_peak(10 m) = 75.0 / 87.5 / 93.8 / 112.5 g for k = 1.2 / 1.4 / 1.5 / 1.8 | `.pdca/egg-drop/rv1/attempts/c1-r1-n1/probe.json` |
| C2 | `python3 .pdca/egg-drop/rv1/verify.py --repo /home/alex/sources/skills --check selftest --log …/selftest.json` | **0** | 10/10: base fixture clean, 8/8 corruptions rejected with `HEADING`, `MISSING_NUMBER`, `MASS_LIMIT`, `BUDGET_LIMIT`, `MATERIAL`, `STROKE`, `LANGUAGE`, `CHAIN`; 0 undetected | `.pdca/egg-drop/rv1/attempts/c1-r1-n1/selftest.json` |

Interface implemented exactly as frozen in §9: six-valued `--check`, `--repo` required, `--document`
required for the four document checks (missing → exit 2), log JSON with
`check/selector/started_utc/repo/document/status/counts/results/limits/note`. `probe`/`selftest`
carry 0 document targets and are self-contained; selector resolution is positive in every run
(probed counts recorded above; a 0-selected run is forced to `fail` by a `VACUOUS` guard).

### D2 — `experiments/egg-drop/answer.md` — `done` (closed 2026-10-24T14:36:02Z)

Russian Markdown, six H2 sections in spec order, 584 lines, sha256
`b499caf47de2fd2afd13e01dfe622a3d513a46431e0236a9da9ff9a6c47cec92`.

Key numbers (all recomputed by the checker from the document's own model block):

| Quantity | Value | Note |
|---|---|---|
| Total mass | 400 g | BOM sums exactly; egg at 65 g + 24 g reserve; 100 g margin to 500 g |
| Budget | 3.00 $ | 15 priced rows; 2.00 $ margin |
| Max dimension | 300 mm | box 300 × 250 × 250 mm; every element ≤ 300 mm |
| Volume | 18 750 000 mm³ | 18.75 L ≤ 20 L |
| `v_impact` | 14.01 m/s | √(2gH), no drag (drag case quoted separately, not credited) |
| `E_k` | 39.24 J | at 400 g; 49.05 J at the 500 g worst case |
| `Δt` | 0.0229 s | 2s/v, cross-checked via momentum |
| `F_avg` / `F_peak` | 245.2 N / 367.9 N | k_peak = 1.5 (assumed, sensitivity 1.2–1.8 shown) |
| `n` | 93.8 g | design point 100 g; band 50–200 g |
| `η` | 0.985 | requirement is 0.9745 (from E_crit = 1.0 J) |
| `E_egg` | 0.598 J | limit δ_egg ≤ 16.7 mm |
| Stroke | 160 mm | derived: 14 layers × (15 − 3.6) mm = 159.6; cavity 210 mm |
| Verdict | **вероятно** | six explicit conditions; fails at n_crit ≈ 50 g (needs 200 mm stroke) |
| P1 / P3 | 0.75 / 0.0056 | P3 is a conditional chain, not P1³ |

### D3 — checks, review, manifest — `done` (closed 2026-10-24T14:41:10Z)

All six commands run in the planned order, absolute paths in argv, transcript
`.pdca/egg-drop/rv1/attempts/c1-r1-n1/checks-transcript.log`:

| # | Check | Exit | Selected / passed / failed | Log |
|---|---|---|---|---|
| 1 | probe | **0** | 21 / 21 / 0 | `…/c1-r1-n1/probe.json` |
| 2 | selftest | **0** | 10 / 10 / 0 | `…/c1-r1-n1/selftest.json` |
| 3 | structure | **0** | 7 / 7 / 0 | `…/c1-r1-n1/structure.json` |
| 4 | physics | **0** | 16 / 16 / 0 | `…/c1-r1-n1/physics.json` |
| 5 | constraints | **0** | 11 / 11 / 0 | `…/c1-r1-n1/constraints.json` |
| 6 | content | **0** | 20 / 20 / 0 | `…/c1-r1-n1/content.json` |

Zero-target guard: every run selected > 0 cases (7–21); a 0-selected run is forced to `fail` by
the `VACUOUS` result, so no vacuous pass is possible.

Semantic review: `.pdca/egg-drop/rv1/attempts/c1-r1-n1/review.md` — AC2, AC5, AC7, AC8, AC9,
AC10, AC11, AC12 with `answer.md` line pointers; independent hand recompute of mass (400 g),
budget (3.00 $), energy (39.24 J), stroke (159.6 mm) and η (0.9848) all match.

Manifest: `.pdca/egg-drop/rv1/attempts/c1-r1-n1/manifest.json` — 12/12 rows `met`, each with the
`execution` and/or `review` evidence mapped in §7; no row is `met` without a passing log.

Three contradictions were found during the review and fixed **before** the final runs (recorded
in `review.md`, section AC12): the §1.2 vs §3.5 energy split, the bed footprint mismatch in the
diagram, and the mass/plateau coupling at 500 g. One quantitative error in the first draft's
drag estimate was also corrected (terminal velocity is 10.33 m/s, not "negligible").

## 16. DO evidence — attempt 2 (generation `c1-r1-n2`)

Document: `experiments/egg-drop/answer.md`, 865 lines, sha256
`b254ced7db9ab14cb54779801a3a72c6131bc6836c63941667a6f6c4c53c25de`, unchanged after the last edit
and before every run. Checker sha256 `fb30f7a8…`.

| # | Check | Exit | Selected / passed / failed | `started_utc` | Log |
|---|---|---|---|---|---|
| C1 | probe | **0** | 21 / 21 / 0 | 2026-10-24T14:58:58.983Z | `…/c1-r1-n2/probe.json` |
| C2 | selftest | **0** | 13 / 13 / 0 (11 corruptions, all rejected) | 14:59:00.199Z | `…/selftest.json` |
| C3 | structure | **0** | 7 / 7 / 0 | 14:59:01.586Z | `…/structure.json` |
| C4 | physics | **0** | 19 / 19 / 0 | 14:59:02.815Z | `…/physics.json` |
| C5 | constraints | **0** | 13 / 13 / 0 | 14:59:04.027Z | `…/constraints.json` |
| C6 | content | **0** | 21 / 21 / 0 | 14:59:05.233Z | `…/content.json` |

New checks that did not exist in attempt 1 (each with a fixture that must be rejected, all rejected):
`WALL_TABLE`, `WALL_CHAIN` (9/9 cavity identities), `TOP_STROKE`, `LATERAL_STROKE`,
`GRAVITY_TERM`, `T_WEAK_BULLETS`, `T_FAILURE_BULLETS`. No check was weakened, no criterion removed.

Key numbers of the corrected document: 436 g (64 g margin), 3.17 $ (+57.7% headroom), 300 mm max
dimension, 18.75 L, strokes 159.6 mm bottom / 15.2 mm top / 57.0 mm (X) and 60.8 mm (Y) lateral,
`v`=14.01 m/s, `E_k`=42.77 J, `ΔU_g`=0.683 J (1.60%), `E_tot`=43.45 J, `Δt`=0.02279 s,
`F_peak`=408.4 N, `n_peak`=95.5 g (strict window 50–100 g, margin 4.5 g), `η`=0.9858 (requirement
0.9766), θ capacity 31° vs a 15° envelope, P1=0.75, P3=0.0056, verdict «вероятно».

Honest remainders: a full-speed inverted drop (988 g) and a full-speed pure side drop (264.6 g)
are computed failures — every face has a real dissipater (that was the AC8/AC11 objection), but the
300 mm envelope cannot give the top or the sides a 160 mm stroke. Both are stated in `answer.md`
(§3.7, §3.8, §4.4, §4.5) and are design limitations, not hidden defects.

## 17. DO evidence — attempt 3 (generation `c1-r1-n3`, final of revision r=1)

Document: `experiments/egg-drop/answer.md`, 921 lines,
sha256 `7a67e1a91be885640962b27548e73707ef760eb8d3c252d0ce284113d6cda3c3`, unchanged after the
last edit and before every run. Checker: `.pdca/egg-drop/rv1/verify.py`,
sha256 `c8a4ee5d14e5bf7b67cbe29e45109d3868c873eb56195e633f7d5e9f7e30773e`.

| # | Check | Exit | Selected / passed / failed | min_selected | `started_utc` | Log |
|---|---|---|---|---|---|---|
| C1 | probe | **0** | 21 / 21 / 0 | 2 | 2026-10-24T15:41:42.810Z | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/probe.json` |
| C2 | selftest | **0** | 14 / 14 / 0 (12 corruptions, all rejected) | 8 | 15:41:42.852Z | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/selftest.json` |
| C3 | structure | **0** | 7 / 7 / 0 | 6 | 15:41:42.951Z | `…/structure.json` |
| C4 | physics | **0** | 19 / 19 / 0 | 7 | 15:41:42.997Z | `…/physics.json` |
| C5 | constraints | **0** | 14 / 14 / 0 | 6 | 15:41:43.039Z | `…/constraints.json` |
| C6 | content | **0** | 21 / 21 / 0 | 12 | 15:41:43.084Z | `…/content.json` |

Transcript (expanded argv, per-command exit, sha256sum, and a 50-row hand recompute with line
pointers): `.pdca/egg-drop/rv1/attempts/c1-r1-n3/checks-transcript.log`. Review per AC:
`…/c1-r1-n3/review.md`. Manifest: `…/c1-r1-n3/manifest.json` — 12/12 rows `met`, AC3 mapped to
probe + physics + structure + review.

Key numbers of the corrected document: 436 g (64 g margin), 3.17 $, max dimension 300 mm,
18.75 L, outer box 250 × 250 × 300 with inset lid/floor 240 × 240 × 5, cavity 240 × 240 × 290,
strokes 159.6 mm bottom / 15.2 mm top / 57.0 mm (X) and 60.8 mm (Y), v = 14.01 m/s, E_k = 42.77 J,
ΔU_g = 0.683 J (1.60%), Δt = 0.02279 s, F_avg = 272.3 N, F_peak = 408.4 N, n_peak = 95.5 g,
η = 0.9858, θ_max = 31.4° (adopted 31°), side peak 264.6 g, inverted 988.4 g, residual 1501.5 g,
F_D = 6.01 N, model `"revision": 1`, verdict «вероятно», P1 = 0.75, P3 = 0.0056.

Fix mapping (new defect keys → what changed): `DEF-LID-BED-CLEARANCE-DIMS` — R2/R3/R5/R6 above;
`DEF-IMPROVEMENT-STROKE-AND-COTTON` — R1/R7/R9 in §6.1; `DEF-SCATTERED-NUMBERS-AND-DRAG` —
R4/R8/R10/R11/R12; `DEF-PROBE-AND-SELECTOR-SYNC` — R13/R15/R17 in `verify.py` and the model block.

## 18. ACT — Done / Verified

Verified at ACT (2026-10-24T16:05:00Z): the deliverable exists, is the one CHECK saw, and every
acceptance criterion was met by evidence recorded in the n=3 generation.

| Item | Verified value | Evidence |
|---|---|---|
| Deliverable | `experiments/egg-drop/answer.md`, **921 lines**, sha256 `7a67e1a91be885640962b27548e73707ef760eb8d3c252d0ce284113d6cda3c3` (unchanged since the last edit; re-checked read-only at ACT, hash matches the recorded value) | `experiments/egg-drop/answer.md`; `.pdca/egg-drop/rv1/attempts/c1-r1-n3/manifest.json` → `artifact` |
| CHECK verdict | **pass** — 12/12 AC met, `unmet: []`, no escalation trigger, no defect recurrence | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/manifest.json` → `triage` |
| Defects | 6 n=1 keys + 4 n=2 keys, **all closed**, each fixes=1; none open, none escalated | §Defect history; n=3 `manifest.json` → `triage.closed_defects` |

The six checks of the n=3 generation, with their logs (all exit **0**, all above their
`min_selected` floor — no vacuous run):

| # | Check | Exit | selected / passed / failed / skipped | min_selected | Log |
|---|---|---|---|---|---|
| C1 | probe | **0** | 21 / 21 / 0 / 0 | 2 | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/probe.json` |
| C2 | selftest | **0** | 14 / 14 / 0 / 0 (12 corruptions, all rejected, 0 undetected) | 8 | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/selftest.json` |
| C3 | structure | **0** | 7 / 7 / 0 / 0 | 6 | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/structure.json` |
| C4 | physics | **0** | 19 / 19 / 0 / 0 | 7 | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/physics.json` |
| C5 | constraints | **0** | 14 / 14 / 0 / 0 | 6 | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/constraints.json` |
| C6 | content | **0** | 21 / 21 / 0 / 0 | 12 | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/content.json` |

Full run transcript (expanded argv, per-command exit, hashes, hand recompute with line pointers):
`.pdca/egg-drop/rv1/attempts/c1-r1-n3/checks-transcript.log`. Per-AC review:
`.pdca/egg-drop/rv1/attempts/c1-r1-n3/review.md`.

## 19. ACT — Limitations / residual non-binding notes

Three items, exactly as the CHECK returned them (`triage.diagnostic_nonbinding`). None of them
changes a met criterion, a headline number outside its pinned tolerance, or an acceptance
criterion — they are recorded so that a later revision does not have to rediscover them.

1. **Bedding / corner-gusset tolerances (D1, D2).** The cotton thickness is stated as **uncompressed
   loose batting**, not as a compressed gap under rubber-band preload; compressed at the egg poles it
   wraps the tapered shoulders inside the 60 mm cradle, and δ_egg = 10 mm acts in series with the
   compliant cup/stack interface, leaving 9.6 mm of usable stroke margin. The four 30×30×30 mm corner
   gussets overlap the 200×200 mm stack corners by 10×10 mm in plan (400 mm² = 1.0 % of stack area,
   within the ±5 % force tolerance, 180 mm from the cradle); build either with a 10×10 mm corner
   relief or with 20×20 mm gussets.
2. **Spec §3.5 notation clarification (D11).** `a_peak = F_peak/m_egg` in spec §3.5 means the **egg
   free-body** force: F_egg = 60.9 N → 95.5 g, which equals `F_peak,sys/m_total` = 408.4/0.436 =
   95.5 g (Newton's second law, AC11). Dividing the 408.4 N total-vehicle force by the 640 g egg-pair
   mass instead would mix frames; the document's own result is the correct application.
3. **Minor editorial / log notes (D3–D10, D12, R14, R18).** Review wording and 0.001 rounding; prose
   framing; the status notice count; 20 m E_egg 1.208 vs 1.2145 J (0.0065 J ≪ 0.5 J tolerance); the
   7+1=8 min step sum; h_cg 176.36 vs 176.34 mm (both 176.4); 16.4 vs 16 mm conservative integer;
   secondary peaks in the transcript; static detail strings in the JSON logs. To be cleaned up only
   if a revision r=2 is opened after physical drop testing.

## 20. ACT — Changed artefacts

| Path | Change |
|---|---|
| `experiments/egg-drop/answer.md` | the deliverable: written in n=1, rewritten in n=2 (584→865 lines) and n=3 (865→921 lines); 921 lines, sha256 `7a67e1a9…` |
| `.pdca/egg-drop/rv1/verify.py` | the checker: six-valued `--check`, per-check `min_selected`, 14 selftest rows (12 corruptions), probe re-based on the document's own inputs; sha256 `c8a4ee5d…` |
| `.pdca/egg-drop/rv1/attempts/c1-r1-n1/` | frozen generation 1: six logs, `review.md`, 12 rows + 8 CHECK-triage rows, gate-1 validation log |
| `.pdca/egg-drop/rv1/attempts/c1-r1-n2/` | frozen generation 2: six logs, `review.md`, 12 rows + 6 CHECK-triage rows |
| `.pdca/egg-drop/rv1/attempts/c1-r1-n3/` | generation 3 (closing): six logs, `checks-transcript.log`, `review.md`, 12 DO rows + appended `triage` object |
| `.pdca/status/egg-drop-1.md` | this status file: durable state, defect history, DO evidence, notices, progress log, ACT closure |

No file outside `experiments/egg-drop/` and `.pdca/` was created or modified; no git write command
was run; the spec `experiments/egg-drop/egg-drop-test.md` is unchanged (read-only input).

## 21. Pointers

| What | Where |
|---|---|
| Spec (read-only) | `experiments/egg-drop/egg-drop-test.md` (289 lines, sha256 `8a79d64b…`) |
| Deliverable | `experiments/egg-drop/answer.md` (921 lines, sha256 `7a67e1a9…`) |
| Checker | `.pdca/egg-drop/rv1/verify.py` |
| Closing manifest (rows + `triage`) | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/manifest.json` |
| Closing review | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/review.md` |
| Closing transcript + logs | `.pdca/egg-drop/rv1/attempts/c1-r1-n3/{checks-transcript.log,probe,selftest,structure,physics,constraints,content}.json` |
| Earlier generations | `.pdca/egg-drop/rv1/attempts/c1-r1-n1/`, `.pdca/egg-drop/rv1/attempts/c1-r1-n2/` |
| This status file | `.pdca/status/egg-drop-1.md` |

