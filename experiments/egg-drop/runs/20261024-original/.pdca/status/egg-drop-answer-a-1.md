# PDCA status — egg-drop-answer-a (cycle 1)

- Task: Produce the benchmark answer for scenario **A** of `experiments/egg-drop/egg-drop-test.md` as a standalone Russian Markdown document `experiments/egg-drop/answer-a.md` with exactly six mandatory `##` headings, LaTeX formulas, dimensions in mm, masses in g, energies in J, forces in N, covering all §4.1–4.6 bullets, for scenario A (H = 10.0 m, concrete, M_max 500 g incl. egg, any side ≤ 300 mm, volume ≤ 0.02 m³, budget $5.00, assembly ≤ 30 min, allowed materials only, no metal/glass/plastic > 2 mm/glue except tape/ready-made shock absorbers, egg not glued, real braking path, egg protected from all sides).
- Workspace root: `/home/alex/sources/skills`
- Status file: `.pdca/status/egg-drop-answer-a-1.md`
- Evidence root: `.pdca/egg-drop-answer-a/rv1/`; attempt dirs: `.../attempts/c1-r1-n1/` (failed generation, kept) and `.../attempts/c1-r1-n2/` (accepted generation — current pointers)
- Mode: **autonomous** (no PLAN → DO approval gate; no approval ref is written)

## Current state

- Phase: **done / accepted** — ACT closed. CHECK on attempt n2 returned **PASS** (A01–A12 all `met`); the cycle is finalized. (History: n1 CHECK = FAIL → loop-back → n2 accepted.)
- Active units: none — D1–D5 `done`; no unit superseded, no `superseded→replacement` mapping.
- Cycle N = 1, Plan revision r = 1, Attempt n = 2 (n2/3) — accepted, Contract rv = 1. *(ACT correction: this line still read `Attempt n = 1 (n1/3)` after the n2 handoff; corrected here, not silently — the value it replaced is the n1 attempt, closed by the CHECK FAIL.)*

## Durable state

- Current cycle N: 1
- Plan revision r: 1
- Attempt n: 2 (n1 CHECK = FAIL; the loop-back consumed attempt 2; result handed to CHECK — the counter is not reset by the handoff)
- Contract rv: 1
- Defect history:

| Key | Defect (CHECK of n1) | Revision / attempt | Fixes | Pointer (no logs) | Outcome |
|---|---|---|---|---|---|
| B1 | Event-tree branch A used n_peak 25 g instead of the nominal 44.7 g; degradation rows followed the wrong base | r1 / n1 | 1 | doc §4.2, §4.3 | fixed in n2: 44.7 → 48.3 → 52.1 g (+8 %/drop) |
| B2 | Branches C/D stated 75/150 g not derivable from their effective travel; no per-branch v, x_eff, p_f | r1 / n1 | 1 | doc §4.2 | fixed in n2: per-branch v_i/x_eff/p_f and n=pf·v²/(2g·x_eff); C 88.4 g, D 159.1 g |
| B3 | Stage table mixed bases: 149 N presented against a 7.18 J sum | r1 / n1 | 1 | doc §3.7 | fixed in n2: stages sum 7.10 J = E_k−E_egg at 149 N + explicit 7.18 J / 151 N total row |
| B4 | §6.3 mass deltas +35/+15/+20 = +70 g vs the stated 480 g (would breach 500 g) | r1 / n1 | 1 | doc §6.3 | fixed in n2: nine signed deltas sum +20 g (460→480) and +$0.36 (→$3.03) |
| B5 | §1.2 "≈90 % of stored energy" by the canopy contradicted the energy budget | r1 / n1 | 1 | doc §1.2 | fixed in n2: 84 % of MgH by drag, 98.9 % of E_k by the structure, 0.08 J to the egg |
| B6 | Two 20 m configurations in one section (460 g unchanged at `:583` vs 480 g redesign at `:606`) — **not a defect**, correctly separated; recorded as labelled | r1 / n1 | 0 | doc §6.2 vs §6.3 | no change needed; the separation is explicit (CHECK C6, already clean) |
| H1 | Harness (A11) validated only the `numeric` blocks; prose/table numbers never crossed-checked | r1 / n1 | 1 | `recompute.py` (n2) | fixed in n2: 5 prose-table checks + 4 expected-negative mutants |

## 1. Goal

`experiments/egg-drop/answer-a.md` — the benchmark answer for scenario A, written as a standalone Russian Markdown document with exactly six mandatory `##` headings (`## 1. Концепция`, `## 2. Спецификация`, `## 3. Физические расчёты`, `## 4. Оценка надёжности`, `## 5. Альтернативы`, `## 6. Итерации`), LaTeX formulas, dimensions in mm, masses in g, energies in J, forces in N, covering all §4.1–4.6 bullets, and passing the frozen verification contract C1/C2/C3.

## 2. Constraints

- Writes allowed only: the new `experiments/egg-drop/answer-a.md` and new files of this cycle under `.pdca/`.
- No git writes (read-only git allowed). No network.
- No verification code/logs inside the answer document.
- Existing files (`experiments/egg-drop/egg-drop-test.md`, the two existing status files, everything else) stay unchanged.

## 3. Assumptions / physics interpretation fixed by PLAN (DO must follow, including in the document's own statements)

| # | Rule |
|---|---|
| P1 | `E_k` and `p` use the **actual total mass M from the document's own material table** (egg included) — never the 500 g limit as a stand-in. |
| P2 | Egg mass 60 g nominal; 55 g and 65 g sensitivity cases change M accordingly. Impact load on the egg is `F_egg = m_egg·a`, not `M·a`. |
| P3 | The spec's 49 J example is explicitly explained as an example for M = 0.5 kg (exact: `2·9.81·10 = 196.2`; `½·0.5·196.2 = 49.05 J`), not as the energy of the design. |
| P4 | Two velocities: control (no drag, `sqrt(2gH)`) and drag-corrected with the design's own `C_d, A`. A fixed Cd·A over the whole fall must be justified or replaced by a piecewise model; if drag is only available after deployment, model the delay and a deployment-failure case. |
| P5 | Design g-load reference threshold **n_crit = 100 g** (matches §3.6's example); 50 g is a mandatory sensitivity; 200 g only as range context. The static-shell estimate ≈25 500 g is shown separately and explained as not replacing the operational criterion. |
| P6 | Energy fracture criterion: primary conservative `E_crit = 0.8 J`; sensitivity to 1.0 and 1.5 J; connect to the spec's 1 J example. Compute the design's own η requirement `η > 1 − E_crit/E_k`; never carry the spec's 0.98 over automatically. |
| P7 | Two independent gates, both checked: energy (`E_egg = E_k·(1−η) < E_crit`) and dynamics (`n_peak ≤ 100`); state which is more binding by normalised margin. Passing one does not prove the other. |
| P8 | Peak force explicitly distinguished from average force (impulse model / peak factor stated). η must have an independent engineering basis and a stated uncertainty — it may not be back-derived from the requirement and then declared achieved. |
| P9 | Survival probabilities are **conditional engineering estimates** with explicit assumptions; no invented test statistics, no unqualified `P > 90 %`, no unjustified `p³` for three drops. |

## 4. Acceptance criteria (IDs are the manifest `required` rows)

| ID | Criterion (negative case in italics) | Verification | Evidence |
|---|---|---|---|
| A01 | Only allowed artefacts created; spec and unrelated files unchanged. *Forbidden path modified.* | read-only inventory before/after + structure run | `snapshot.json`, `structure.log` |
| A02 | Standalone Russian Markdown, exactly six exact `##` headings, LaTeX formulas, no embedded script. *Wrong/extra heading.* | `C1` + CHECK review | `structure.log` |
| A03 | All §4.1–4.6 bullets covered, none missing. *Missing bullet.* | `coverage.md` validated by `C1`; CHECK confirms each reference | `coverage.md`, `structure.log` |
| A04 | Only allowed materials, egg not glued, protection from all sides, real travel. *Rigid fixation / missing side protection.* | `C1`, `C2` + engineering review of scheme/spec | `structure.log`, `recompute.log`, `coverage.md` |
| A05 | Mass ≤ 500 g, each dimension ≤ 300 mm, volume ≤ 0.02 m³, cost ≤ $5.00, assembly ≤ 30 min, sums internally consistent. *Any excess.* | `C2` | `recompute.log` |
| A06 | One parameter set used consistently for velocity/energy/momentum; drag model and conditions disclosed; actual mass not replaced by the limit. *Substituted limit mass.* | `C2` + CHECK on parameter basis | `recompute.log` |
| A07 | Travel, time, average/peak forces and g-loads recomputed; primary case passes 100 g; peak-vs-average and egg-force-vs-system-force never conflated. | `C2` + review | `recompute.log` |
| A08 | Both criteria independently treated; `E_egg < 0.8 J` in the primary model; 49 J / 0.98 / contradictory thresholds explained. *Required η declared achieved without basis.* | `C2` + CHECK | `recompute.log` |
| A09 | Numerical conditional probabilities for 1 and 3 consecutive drops with assumptions, dependence/damage and weak points. *Fabricated statistics or unjustified p³.* | `C2` (arithmetic) + CHECK (interpretation) | `recompute.log` |
| A10 | 2–3 comparable alternatives, post-test actions, quantitative 20 m scenario. *Bare promise to "strengthen" without numbers.* | `C1`, `C2` | `recompute.log`, `structure.log` |
| A11 | Every decisive number extracted from the answer's own tables and independently reproduced; a false number is detected. *Inconsistency or empty selector.* | `C2`, `C3` | `recompute.log`, `selftest.log` |
| A12 | Evidence refers to the actual bytes of the answer; manifest complete. *Current SHA-256 mismatch.* | `C1` + read-only manifest check | `manifest.json`, `structure.log` |

## 5. DO units

| Unit | Priority | Expected result | Depends on | State |
|---|---|---|---|---|
| D1 — Concept + scheme (§4.1) | P0 | Named design, energy-absorption principle, textual/ASCII scheme, A04 constraints visible | — | done |
| D2 — Specification (§4.2) | P0 | Materials with masses (g), element dimensions (mm), egg fixation, total mass, budget, assembly time — matching the `materials`/`design`/`constraints` numeric blocks | D1 | done |
| D3 — Physics (§4.3) | P0 | v (control + drag), E_k, Δt, F_avg/F_peak, n (egg vs system), η with basis + uncertainty, verdict; both gates; all numbers in the 9 numeric blocks | D2 | done |
| D4 — Reliability (§4.4) + alternatives (§4.5) | P0 | P(1), P(3) with assumptions, weak points, failure modes; 2–3 alternatives with mass/cost/reliability comparison | D3 | done |
| D5 — Iterations (§4.6) + numeric-block freeze + manifest | P0 | Post-test improvements, quantitative 20 m scenario; all 9 blocks consistent; `manifest.json` frozen (A12) | D3, D4 | done |

No unit is `superseded`; no `superseded→replacement` mapping exists. All five units are `done` with the evidence in §11.

## 6. Means and access

edit/bash/read; `python3` stdlib only; read-only git; no network. Only the paths in §2 are writable.

## 7. Risks and stop conditions

- Max 2 plan revisions (r1, r2); max 3 failed CHECKs per revision, 6 total; cycle budget 90 min.
- Immediate return to PLAN: a frozen command does not run; the candidate needs a forbidden material; the calculation does not close; braking path unclear; a mandatory parameter cannot be justified even as a bounded assumption.
- DO → PLAN classification: extra prerequisite → additive unit (original D stays active); tolerable material uncertainty → recorded assumption; missing facts → targeted scout.
- Tolerances are fixed in `recompute.py` and printed per check; they must not be widened to make a candidate pass.

## 8. Frozen command contract (rv1) — validated at gate 1

```text
C1: python3 /home/alex/sources/skills/.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/recompute.py --repo /home/alex/sources/skills --document experiments/egg-drop/answer-a.md --case structure --read-only
C2: python3 /home/alex/sources/skills/.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/recompute.py --repo /home/alex/sources/skills --document experiments/egg-drop/answer-a.md --case numeric --read-only
C3: python3 /home/alex/sources/skills/.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/recompute.py --repo /home/alex/sources/skills --document experiments/egg-drop/answer-a.md --case selftest --read-only
```

Expected: C1/C2 green exit 0 `PASS` with a non-zero number of executed checks; C3 green exit 0 for the self-test suite, containing mandatory expected-negative cases. Data inconsistency or constraint violation → exit 1 with the failing criterion ID; launch/parse error, missing argument or zero selected checks → exit 2 (never a pass).

## 9. Evidence paths

- Root: `.pdca/egg-drop-answer-a/rv1/`; attempt: `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/`
- Files: `recompute.py`, `recompute.log`, `structure.log`, `selftest.log`, `coverage.md`, `snapshot.json`, `manifest.json` (+ probe fixtures `fixture.md`, `fixture-corrupt.md`).
- On later attempts only `n` changes.

## 10. Gate-1 probe result (P0 / P2)

**P0 (scope):** this is a **standalone autonomous cycle** — no parent `plan_handoff`, no approval ref (autonomous mode writes none), and no additional global evidence contract in this repo (`.pdca/` holds only `status/` with two unrelated status files and two unrelated task dirs). The evidence contract of record is exactly the one pinned in §8–§9.

**P2 (harness):** `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/recompute.py` — 1405 lines, python3 stdlib only, three cases, exit codes 0/1/2, `--read-only` mandatory, never writes. It recomputes from the document's own tables; no answer value is hardcoded (the only built-in numbers are physics constants and the synthetic self-test fixture).

**Document format fixed** (D3 must follow, full schema in `coverage.md` §1): fenced ` ```numeric ` blocks, first line `# block: <id>`, rows `key | value | unit`; units are strict tokens (`g`, `mm`, `m2`, `m3`, `s`, `m/s`, `m/s2`, `kg/m3`, `kg*m/s`, `j`, `n`, `usd`, `min`, `-`); decimal comma accepted. Nine blocks: `design`, `materials`, `constraints`, `impact`, `criteria`, `sensitivity`, `reliability`, `scenario20`, `alternatives`.

**Fixture validation** (explicitly *not* answer validation): `fixture.md` is a synthetic, internally consistent scenario-A design (360 g incl. 60 g egg, 240×240×260 mm, 0.0140 m³, $3.75, 22 min, constant Cd·A, η = 0.965, n_peak = 52.7 g, energy-binding). Its fall numbers were cross-checked independently by the closed-form constant-drag solution (v_t = 9.7737 m/s, t_fall = 1.6801 s, v_impact = 9.1255 m/s, E_k = 14.9896 J, p = 3.2852 kg·m/s).

| Probe | Command (frozen argv, `--document` = fixture) | Exit | Checks | Verdict |
|---|---|---|---|---|
| C1 positive | `--case structure` | 0 | 17 executed + 1 skip (manifest not frozen until DO→CHECK) | PASS |
| C2 positive | `--case numeric` | 0 | 58 | PASS |
| C3 positive | `--case selftest` | 0 | 44 (expected-positive + 34 expected-negative mutants + 7 CLI/zero-selection paths) | PASS |
| C1 expected-negative | `fixture-corrupt.md` (extra 7th heading) | 1 | 17 | FAIL `A02.headings` |
| C2 expected-negative | `fixture-corrupt.md` (mass sum 361.5 ≠ 360.0) | 1 | 58 | FAIL `A05.mass_sum`, `A06.one_mass` |
| CLI expected-negative | `--case nope`; missing `--document`; missing `--read-only`; missing document file | 2 | — | CANNOT (never a pass) |

**Verdict: commands validated — gate 1 open.** The selector resolves, argv is the frozen one, the phase/scope are legal, and the expected outcome for each case is declared. Failure modes are exercised: exit 1 carries the failing criterion ID, exit 2 is used for invocation/zero-selection failures.

## 11. DO result (D1–D5) — n1 generation, historical

**ACT correction (n2 accepted):** this section records attempt n1. The pointers in “Frozen evidence” below have been updated to the accepted n2 generation, and the numbers that were superseded (P1 0.930, P3 0.768, C2 58, C3 44, sha `4a74c62d…`) are kept as history in §12 and in the n1 manifest.

All units completed in one pass; no DO blocker, no scope change, no plan revision. The product file is `experiments/egg-drop/answer-a.md` (625 lines, 6 exact `##` headings, 9 `numeric` blocks, all formulas in LaTeX, all numbers in mm / g / J / N).

| Unit | Closed | What it produced | Evidence |
|---|---|---|---|
| D1 | done | §4.1: «Кокон К-10», three absorption stages, ASCII scheme with the 47.6 mm braking travel, load path, all-sides protection | doc §1.1–1.5 |
| D2 | done | §4.2: 9 materials 400 g + egg 60 g = 460 g, element dimensions, egg fixation without glue, assembly 29 min, cost $2.67, compliance table | doc §2.1–2.6, blocks `design`/`materials`/`constraints` |
| D3 | done | §4.3: v 14.007 / 5.587 m/s (piecewise drag, 0.35 s deployment), E_k 7.179 J, x 47.6 mm, Δt 17.0 ms, F_avg 151 N / F_peak 202 N, a_peak 439 m/s², n 44.7 g, F_egg 26.3 N, η 0.989 with stage basis, both gates, 49 J / 0.98 / 25 500 g explained, sensitivity tables, verdict | doc §3.1–3.13, blocks `impact`/`criteria`/`sensitivity` |
| D4 | done | §4.4: event tree P1 = 0.930, degradation model P3 = 0.768 (vs naive cube 0.804), weak points, failure modes; §4.5: three alternatives and comparison | doc §4.1–4.6, §5.1–5.6, blocks `reliability`/`alternatives` |
| D5 | done | §4.6: seven post-test measurements with thresholds and actions; 20 m redesign (7.831 J, 50.8 mm of 120 mm, 44.3 g, 480 g, $3.10); blocks consistent; manifest frozen | doc §6.1–6.5, block `scenario20` |

### Frozen commands — n1 run (historical; accepted n2 results in §12–§13)

| Command | Exit | Checks | Result |
|---|---|---|---|
| C1 `--case structure` | 0 | 18 executed, 0 skips (manifest frozen) | PASS |
| C2 `--case numeric` | 0 | 58 | PASS |
| C3 `--case selftest` | 0 | 44 | PASS |

Logs: `structure.log`, `recompute.log`, `selftest.log` (each keeps the earlier fixture probe and the appended real-document run).

### Frozen evidence

- Answer (accepted): `experiments/egg-drop/answer-a.md`, sha256 `5d3ffbb4fa3a03f0abd2fde58de8a0bafbc37c93cb886fe82270d96719402236` (645 lines). *(ACT correction: this bullet named the n1 answer `4a74c62d…`, 626 lines.)*
- Manifest (accepted): `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/manifest.json` — `required` A01…A12, 12 rows `met`, evidence references only. *(ACT correction: was the n1 manifest.)*
- Snapshot (accepted): `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/snapshot.json` — HEAD `cc27a4c…`, spec sha256 `8a79d64b…`, answer sha256 `5d3ffbb4…`, harness `25a06579…` (1797 lines), 220 baseline paths, 3 allowed new paths. *(ACT correction: was the n1 snapshot/harness.)*
- Allowed new paths at freeze: `experiments/egg-drop/answer-a.md`, `.pdca/status/egg-drop-answer-a-1.md`, prefix `.pdca/egg-drop-answer-a/`.

### Interpretation choices for CHECK

1. The 300 mm / 0.02 m³ envelope applies to the assembled device; the deployed Ø500 canopy is outside it. The answer shows both gates still pass without the canopy (67.4 g, 0.105 J), so a strict reading does not invalidate the design (doc §2.2, §4.5).
2. `constraints.braking_travel_mm = 47.6` is the operating point (primary case); the cartridge resource is 96 mm and the canopy-failure case uses 95.3 mm of it (doc §3.4, §4.5).
3. η is derived from a stage-by-stage work sum, not from the requirement; its uncertainty is stated (±0.003) and the required value (0.889) is compared separately (doc §3.7–3.8).


## 12. Attempt n2 (after the n1 CHECK FAIL)

CHECK of n1 (pointer: `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/manifest.json#check_reconciliation`) returned **FAIL** with 7 criteria `unmet` (A05–A11): the numbers a reader sees in the prose/table sections contradicted the `numeric` blocks, and the n1 harness could not see it because it only parsed the blocks. Loop-back: **implementation defect, plan r1 unchanged, attempt n 1→2**; the plan and its criteria are untouched.

Corrections in the artefact (no parameter was tuned to preserve a published result):

| Section | Was | Now |
|---|---|---|
| §4.2 event tree | branch A 25 g; C/D 75/150 g without a kinematic basis | per-branch $v_i$, $x_{eff}$, $p_f$; rule $n=p_fv_i^2/(2g\,x_{eff})$; A 44.7, B 67.4, C 88.4, D 159.1 g |
| §4.2 $P_1$ | 0.930 (built on the wrong branch A) | **0.909** (Σ p·P; model median 120 g, σ 0.35, cap 0.99) |
| §4.3 three drops | 25/27/29 base; $P_3$ 0.768 | 44.7→48.3→52.1 g (A, +8 %/drop); C/D also lose 7 %/drop foam stroke; $P_3$ = 0.909·0.874·0.831 = **0.660** (naive cube 0.751) |
| §3.7 stage table | stage sum 7.18 J but total row 149 N (mixed bases) | 2.40+3.24+1.46 = 7.10 J = $E_k-E_{egg}$ at 149 N; explicit "всего 7.18 J / 151 N" row; η 0.989 |
| §6.3 redesign | +35/+15/+20 = +70 g vs 480 g | nine signed deltas: −15 +35 −22 −6 +10 +6 +4 +4 +4 = **+20 g** (460→480); cost −0.03 +0.06 −0.13 −0.07 +0.05 +0.06 +0.02 +0.24 +0.16 = **+$0.36** (→**$3.03**) |
| §1.2 | "≈90 % of the stored energy" by the canopy | 38.0 J of 45.1 J = 84 % by drag; 7.10 J of 7.18 J = 98.9 % by the structure; 0.08 J reaches the egg |

n2 freeze: `experiments/egg-drop/answer-a.md` sha256 `5d3ffbb4fa3a03f0abd2fde58de8a0bafbc37c93cb886fe82270d96719402236`; harness n2 1797 lines, C2 63 checks (58 block + 5 prose), C3 49 checks; manifest `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/manifest.json` (12 rows, all `met`); snapshot n2 with the same answer hash and a 220-path inventory baseline.

## Decisions made

- **Autonomous mode:** there is no approval gate and **no pending approval ref** — the plan is recorded, not approved; PLAN → DO gate 1 is the command-contract validation only. No user approval is awaited or claimed.
- The evidence contract of record is exactly the one pinned in this plan (paths + frozen commands). No broader global contract exists in this repo (`.pdca/` holds only `status/` with two unrelated status files and two unrelated task dirs).
- Machine-readable document format = **fenced ` ```numeric ` blocks** with a `# block: <id>` first line and `key | value | unit` rows, strict unit tokens, decimal comma accepted; the 9 required blocks (`design`, `materials`, `constraints`, `impact`, `criteria`, `sensitivity`, `reliability`, `scenario20`, `alternatives`) and the key/unit schema are fixed in `recompute.py` and documented in `coverage.md`. D3 writes the document in exactly this format; the schema must not be changed in DO (that would be a plan revision).

## Deferred + trigger

- A held-out scenario set (B–F of `egg-drop-test.md:281-288`) — deferred; trigger: an explicit request for a held-out check of the same answer.
- A second, independent physics implementation cross-check — deferred; trigger: a CHECK dispute about a recomputed number.

## Next plan

- Gate 1 closed; D1 → D5 completed; manifest frozen and the three commands green. Next: independent CHECK verdict. If CHECK fails, the defect key and fix count go into the defect history and the attempt counter stays n1 until a new attempt starts. *(Superseded: the verdict arrived — n1 FAIL → n2 PASS; see §13.)*

## Changed artefacts

- `experiments/egg-drop/answer-a.md` — **the product**, accepted (645 lines, sha256 `5d3ffbb4fa3a03f0abd2fde58de8a0bafbc37c93cb886fe82270d96719402236`). *(ACT correction: this line named the superseded n1 hash `5a57b1f4…`; the list below is the accepted n2 generation.)*
- `.pdca/status/egg-drop-answer-a-1.md` (this file)
- `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/**` — failed generation, kept untouched except the appended CHECK reconciliation in its `manifest.json`
- `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/**` — accepted generation: `recompute.py` (extended harness), `coverage.md`, `snapshot.json`, `manifest.json`, `structure.log`, `recompute.log`, `selftest.log`

## Pointers

- Plan source: this file, §1–§9.
- Spec: `experiments/egg-drop/egg-drop-test.md` (§2.2 conditions, §2.3 limits, §3 physics, §4.1–4.6 answer requirements, §6 format, §7 failure criteria, §8 scenario A).
- Allowed-materials list: `egg-drop-test.md:56`; forbidden: `:57`; egg not glued: `:58`; all-sides protection: `:271`; real braking path: `:272`.


## 13. ACT — finalization (cycle c1, attempt n2 accepted)

### Verdict

CHECK on attempt `c1-r1-n2`: **PASS** — A01–A12 all `met`, manifest reconciled, no append required.
Pointer: `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/manifest.json`.

### Notices recorded (non-blocking; no artefact change)

1. **Cosmetic evidence-prose discrepancy.** `c1-r1-n2/coverage.md:34,69` still quotes the n1 reliability figures in descriptive anchor text (`p_single` 0.930, `p_three` 0.768, «$P_1 \approx 0{,}93$»), while the accepted artefact and the harness use $P_1 = 0{,}909$ and $P_3 = 0{,}660$. The checked artefact and the n2 `numeric` blocks are canonical. Deliberately **not edited** after the accepted CHECK snapshot: editing evidence prose post-verdict would change bytes the verdict refers to, with no product gain.
2. **Process notice.** The first CHECK could not read the deliverable directly (host permission scope `read: .pdca/**`), so the artefact-level facts were re-gathered independently by `pdca-scout` and adjudicated append-only within the same generation. That re-gather is what produced the n1 FAIL and the B1–B5 defect set.

### Decisions / accepted assumptions

1. **The 300 mm envelope is read as the assembled device** (270×270×260 mm, canopy stowed); the deployed Ø500 canopy is an out-of-envelope deployable, as for any parachute. Basis: the answer shows the design passes both gates without the canopy at all (67.4 g, 0.105 J), so the design does not depend on this reading (doc §2.2, §4.5).
2. **$\Delta x = 47{,}6$ мм — рабочий ход** of a 96 mm cartridge resource; the 96 mm resource is sized so the canopy-failure case (95.3 mm) does not bottom out on the tray stop (doc §3.4, §4.5).
3. **`pdca_cost.py` was deliberately not staged** — cost accounting is irrelevant to this deliverable; `.pdca/scripts/` was not created.
4. **Physics model fixed by PLAN and accepted:** actual total mass in $E_k$ and $p$; two independent gates ($E_{egg} < 0{,}8$ Дж and $n_{peak} \le 100$ g) with dynamics binding (0.098 vs 0.447); the spec's 49 J / 0.98 / 25 500 g are explained rather than copied (doc §3.9–3.10).

### Defect history (final)

| Key | Defect | Revision / attempt | Fixes | Pointer | Outcome |
|---|---|---|---|---|---|
| B1 | Branch A used a g-load of 25 g instead of the nominal 44.7 g; degradation rows rebased on the wrong value | r1 / n1 | 1 | n1 manifest `check_reconciliation`; n2 manifest A09 | fixed in n2: 44.7 → 48.3 → 52.1 g |
| B2 | Branch C/D g-loads (75/150 g) were not derivable from their effective travel | r1 / n1 | 1 | n1 manifest; n2 doc §4.2 | fixed in n2: per-branch v/x_eff/p_f, C 88.4 g, D 159.1 g |
| B3 | Stage table mixed bases: 149 N presented against a 7.18 J sum | r1 / n1 | 1 | n1 manifest; n2 doc §3.7 | fixed in n2: 7.10 J at 149 N + explicit 7.18 J / 151 N row |
| B4 | 20 m mass deltas +35/+15/+20 = +70 g vs the stated 480 g (would breach 500 g) | r1 / n1 | 1 | n1 manifest; n2 doc §6.3 | fixed in n2: nine signed rows sum +20 g and +$0.36 |
| B5 | §1.2 "≈90 % of stored energy" contradicted the energy budget | r1 / n1 | 1 | n1 manifest; n2 doc §1.2 | fixed in n2: 84 % of $MgH$ by drag, 98.9 % of $E_k$ by the structure |
| B6 | Two 20 m configurations in one section — **not a defect**, correctly separated | r1 / n1 | 0 | n2 doc §6.2 vs §6.3 | no change; labelled (CHECK C6) |
| H1 | Harness validated only the `numeric` blocks (A11 blind to prose tables) | r1 / n1 | 1 | n2 `recompute.py` | fixed: 5 prose-table checks + 4 expected-negative mutants |

### Done / Verified

- **Deliverable:** `experiments/egg-drop/answer-a.md` — sha256 `5d3ffbb4fa3a03f0abd2fde58de8a0bafbc37c93cb886fe82270d96719402236`, 645 lines, exactly six `##` headings, 9 `numeric` blocks, all formulas in LaTeX, dimensions in mm / masses in g / energies in J / forces in N.
- **Verified by:** C1 `--case structure` exit 0 / 18 checks, C2 `--case numeric` exit 0 / 63 checks (58 block + 5 prose-table), C3 `--case selftest` exit 0 / 49 checks; CHECK verdict PASS with matrix A01–A12 all `met`.
- **Decisive verified numbers:** $M = 460$ g; 270×270×260 mm; 0.0189 м³; $2.67; 29 мин; $v_{control} = 14{,}007$ м/с, $v_{impact} = 5{,}587$ м/с (установившаяся 5.59); $E_k = 7{,}179$ Дж; $\Delta x = 47{,}6$ мм из 96 мм; $\Delta t = 17{,}0$ мс; $F_{avg} = 151$ Н, $F_{peak} = 202$ Н, $p_f = 1{,}337$; $F_{egg} = 26{,}3$ Н; $n_{peak} = 44{,}7$ g; $E_{egg} = 0{,}0787$ Дж; $\eta = 0{,}989$ при требуемой 0.889; нормированные запасы 0.098 (энергия) и 0.447 (динамика), определяющий — динамика; $P_1 = 0{,}909$, $P_3 = 0{,}660$ (наивный куб 0.751).

### Changed artefacts

- `experiments/egg-drop/answer-a.md` — **new product file** (645 lines).
- `.pdca/egg-drop-answer-a/**` — cycle evidence only (n1 failed generation + n2 accepted generation).
- `.pdca/status/egg-drop-answer-a-1.md` — this file.
- **No source, spec or pre-existing status file was modified** (`experiments/egg-drop/egg-drop-test.md` and the two unrelated status files are untouched), and **no git write was performed** (read-only git only).

### Next plan (note only — no next cycle opened)

- Physical first drop; replaceable foam/tubes to test the $P_3$ hypothesis; the 20 m variant (120 mm stroke, 480 g, $3.03). Trigger: the user asking for a measurement-backed revision.

### Limitations

- The probabilities are conditional engineering estimates from an assumed lognormal failure threshold (median 120 g, $\sigma_{\ln} 0{,}35$, cap 0.99), not measured frequencies. No material property was measured: crush forces, foam recovery and canopy deployment are design estimates with stated uncertainty.

`ACT closed — cycle c1 finalized`

## Progress log

```text
2026-10-24T09:14:02Z | PLAN | revision 1 | iteration 1/3 | PLAN ready — recorded (autonomous, no approval gate) | .pdca/status/egg-drop-answer-a-1.md
2026-10-24T09:14:40Z | PLAN | revision 1 | iteration 1/3 | P0 closed — standalone autonomous cycle: no plan_handoff, no approval ref, no additional global evidence contract (scout-confirmed) | .pdca/status/egg-drop-answer-a-1.md
2026-10-24T09:15:30Z | DO | revision 1 | iteration 1/3 | gate-1 validation started: D1–D5 remain pending, no content work in this dispatch | .pdca/status/egg-drop-answer-a-1.md
2026-10-24T09:16:05Z | DO | revision 1 | iteration 1/3 | P2 harness built: recompute.py 1405 lines, cases structure|numeric|selftest, exit 0/1/2, --read-only mandatory, stdlib only | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/recompute.py
2026-10-24T09:16:20Z | DO | revision 1 | iteration 1/3 | document table format fixed: 9 fenced `numeric` blocks (design, materials, constraints, impact, criteria, sensitivity, reliability, scenario20, alternatives), key|value|unit, strict unit tokens | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/coverage.md
2026-10-24T09:16:55Z | DO | revision 1 | iteration 1/3 | coverage.md written: 23/23 spec bullets (§4.1–4.6) mapped, format contract stated | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/coverage.md
2026-10-24T09:17:02Z | DO | revision 1 | iteration 1/3 | snapshot.json written: HEAD cc27a4c574806176f319025a353cdbb8fd858aa8, spec sha256 8a79d64b…db4e, harness a47b3834…863c, inventory 220 baseline paths | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/snapshot.json
2026-10-24T09:17:20Z | DO | revision 1 | iteration 1/3 | C1 fixture probe: exit 0, checks=17, failed=0 (+1 skip: manifest not frozen) (headings 6/6, 9 blocks, schema, coverage 23/23, spec hash, inventory) | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/structure.log
2026-10-24T09:17:25Z | DO | revision 1 | iteration 1/3 | C2 fixture probe: exit 0, checks=58, failed=0 (masses, limits, drag fall, energy/momentum, braking, forces, both gates, sensitivities, probabilities, 20 m, alternatives) | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/recompute.log
2026-10-24T09:17:30Z | DO | revision 1 | iteration 1/3 | C3 fixture probe: exit 0, checks=44, failed=0 (expected-positive + expected-negative mutants + CLI exit-2 paths) | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/selftest.log
2026-10-24T09:17:35Z | DO | revision 1 | iteration 1/3 | expected-negative probes: corrupt fixture -> C1 exit 1 A02.headings (extra heading), C2 exit 1 A05.mass_sum + A06.one_mass; bad invocation -> exit 2 (--case nope, missing --document, missing --read-only, missing document) | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/selftest.log
2026-10-24T09:18:10Z | DO | revision 1 | iteration 1/3 | commands validated — gate 1 open; C1/C2/C3 run green on the synthetic fixture (17/58/44 checks), failure modes produce exit 1 with a criterion ID and exit 2 for invocation/zero-selection errors | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/
2026-10-24T09:19:05Z | DO | revision 1 | iteration 1/3 | gate 1 open — D phase started (D1→D5, one pass, no scope change) | .pdca/status/egg-drop-answer-a-1.md
2026-10-24T09:21:40Z | DO | revision 1 | iteration 1/3 | D1 closed (done): §4.1 «Кокон К-10», 3 absorption stages, ASCII scheme, 47.6 mm travel labelled, load path, all-sides protection | experiments/egg-drop/answer-a.md
2026-10-24T09:23:55Z | DO | revision 1 | iteration 1/3 | D2 closed (done): §4.2 nine materials 400 g + egg 60 g = 460 g, element dims, fixation without glue, 29 min, $2.67, compliance table | experiments/egg-drop/answer-a.md
2026-10-24T09:26:30Z | DO | revision 1 | iteration 1/3 | D3 closed (done): §4.3 v 14.007/5.587 m/s, E_k 7.179 J, x 47.6 mm, Δt 17.0 ms, F 151/202 N, n 44.7 g, F_egg 26.3 N, η 0.989 with stage basis, both gates, 49 J/0.98/25 500 g explained, sensitivity, verdict | experiments/egg-drop/answer-a.md
2026-10-24T09:28:15Z | DO | revision 1 | iteration 1/3 | D4 closed (done): §4.4 P1 0.930, P3 0.768 under accumulated damage (naive cube 0.804), weak points and failure modes; §4.5 three alternatives with comparison | experiments/egg-drop/answer-a.md
2026-10-24T09:29:40Z | DO | revision 1 | iteration 1/3 | D5 closed (done): §4.6 seven measurements with thresholds and actions; 20 m redesign 7.831 J / 50.8 mm of 120 mm / 44.3 g; all 9 blocks consistent | experiments/egg-drop/answer-a.md
2026-10-24T09:30:05Z | DO | revision 1 | iteration 1/3 | evidence run on the real document: C1 exit 0 checks=18, C2 exit 0 checks=58, C3 exit 0 checks=44 (no harness change needed) | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/structure.log
2026-10-24T09:30:20Z | DO | revision 1 | iteration 1/3 | answer frozen: sha256 5a57b1f4c80193be380f7e5b0ba3e643bc22d366a39dc7af717568287ab4ed12; manifest frozen (A01–A12, 12 met); snapshot updated (HEAD cc27a4c, spec 8a79d64b, 220 baseline paths) | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/manifest.json
2026-10-24T09:30:30Z | DO | revision 1 | iteration 1/3 | D: closed — all units done; phase DO → CHECK; attempt n=1 handed to CHECK (no defect recorded yet) | .pdca/status/egg-drop-answer-a-1.md
2026-10-24T09:31:20Z | DO | revision 1 | iteration 1/3 | self-review before CHECK found two documentation defects in the answer (stage-sum arithmetic in §3.7; late-deployment figures in §4.5 claimed 7.4 m/s but the model gives 5.60 m/s) — corrected in the answer, no harness change, no criterion weakened | experiments/egg-drop/answer-a.md
2026-10-24T09:31:45Z | DO | revision 1 | iteration 1/3 | answer re-frozen sha256 4a74c62d905a41c294281b42a9596974fb386c045741b734386c94703fe33ab8; manifest and snapshot re-hashed; C1 exit 0 checks=18, C2 exit 0 checks=58, C3 exit 0 checks=44 | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/manifest.json
2026-10-24T09:32:00Z | DO | revision 1 | iteration 1/3 | D: closed (final) — all units done; phase DO → CHECK; attempt n=1 handed to CHECK; defect history still empty (the two defects above were found and fixed inside DO, before any CHECK) | .pdca/egg-drop-answer-a-1.md
2026-10-24T09:48:10Z | CHECK | revision 1 | iteration 1/3 | CHECK verdict on n1: FAIL — 7 criteria unmet (A05–A11); prose/table numbers contradict the numeric blocks; reconciliation appended to the n1 manifest | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/manifest.json
2026-10-24T09:48:20Z | PLAN | revision 1 | iteration 1/3 | loop-back to DO (implementation defect; plan r1 unchanged, no replan); attempt n 1→2 | .pdca/status/egg-drop-answer-a-1.md
2026-10-24T09:50:40Z | DO | revision 1 | iteration 2/3 | defect B1 fixed: event-tree branch A = nominal 44.7 g; degradation rebased 44.7→48.3→52.1 g | experiments/egg-drop/answer-a.md
2026-10-24T09:51:30Z | DO | revision 1 | iteration 2/3 | defect B2 fixed: per-branch v_i/x_eff/p_f and n=pf*v^2/(2g*x_eff); C 88.4 g, D 159.1 g; P1 0.909 and P3 0.660 propagated to §1, §4, §5, §6 and the blocks | experiments/egg-drop/answer-a.md
2026-10-24T09:52:10Z | DO | revision 1 | iteration 2/3 | defect B3 fixed: stages 2.40+3.24+1.46 = 7.10 J = E_k−E_egg at 149 N, plus the 7.18 J / 151 N total row | experiments/egg-drop/answer-a.md
2026-10-24T09:52:50Z | DO | revision 1 | iteration 2/3 | defect B4 fixed: 20 m mass deltas sum +20 g (460→480), cost deltas +$0.36 (→$3.03), nine signed rows | experiments/egg-drop/answer-a.md
2026-10-24T09:53:10Z | DO | revision 1 | iteration 2/3 | defect B5 fixed: §1.2 energy statement replaced (84 % of MgH by drag, 98.9 % of E_k by the structure, 0.08 J to the egg) | experiments/egg-drop/answer-a.md
2026-10-24T09:54:20Z | DO | revision 1 | iteration 2/3 | defect H1 fixed: harness n2 extended with 5 prose-table checks (A09.branch_kinematics, A09.branch_a_consistency, A09.drop_chain, A08.stage_table, A10.redesign20_deltas) and 4 expected-negative mutants | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/recompute.py
2026-10-24T09:55:40Z | DO | revision 1 | iteration 2/3 | n2 evidence run: C1 exit 0 checks=18, C2 exit 0 checks=63, C3 exit 0 checks=49 | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/recompute.log
2026-10-24T09:56:00Z | DO | revision 1 | iteration 2/3 | n2 freeze: answer sha256 5d3ffbb4fa3a03f0abd2fde58de8a0bafbc37c93cb886fe82270d96719402236; manifest n2 (12 rows met); snapshot n2 | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/manifest.json
2026-10-24T09:56:10Z | DO | revision 1 | iteration 2/3 | D: closed — attempt n=2 handed to CHECK; phase DO → CHECK | .pdca/status/egg-drop-answer-a-1.md
2026-10-24T09:57:00Z | DO | revision 1 | iteration 2/3 | DO → CHECK (n2): artefact frozen sha256 5d3ffbb4fa3a03f0abd2fde58de8a0bafbc37c93cb886fe82270d96719402236, manifest n2 with 12 rows, C1 18 / C2 63 / C3 49 checks green | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/manifest.json
2026-10-24T10:02:00Z | CHECK | revision 1 | iteration 2/3 | CHECK verdict on n2: PASS — A01–A12 all met, manifest reconciled, no append required | .pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n2/manifest.json
2026-10-24T10:05:00Z | ACT | revision 1 | iteration 2/3 | finalization: stale n1 pointer lines corrected in the status file with an explicit ACT note; two non-blocking notices recorded (coverage.md n1 figures; first CHECK re-gather) | .pdca/status/egg-drop-answer-a-1.md
2026-10-24T10:06:00Z | ACT | revision 1 | iteration 2/3 | ACT closed — cycle c1 finalized: deliverable accepted, defect history B1–B6/H1 closed, no next cycle opened | .pdca/status/egg-drop-answer-a-1.md
```
