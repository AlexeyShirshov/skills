# known-good fixture — independent arithmetic verification

- Fixture: `experiments/egg-drop/fixtures/known-good/answer.md`
- sha256: `16cdb204ef645fdb2c9178203bd9b2bd0e4e2d18d359cfce7dcc714f16e071be`
- Verified (UTC): `2026-10-24T17:49:25Z`
- Independence: `experiments/egg-drop/check_answer.py` was **never opened**; no value produced by it is used here. Every number below was re-derived from the ```` ```json ```` block of the fixture (lines 60–168).
- Script: `/tmp/opencode/known_good_independent.py` (Python 3, stdlib only, outside the repo)
- Command: `cd /tmp/opencode && python3 known_good_independent.py | tee /tmp/opencode/known_good_independent.out`
- Exit code: `0`; full output: `/tmp/opencode/known_good_independent.out`
- Inputs as declared in the JSON: `H = 10.0 m`, `g = 9.81 m/s²`, `M = total_mass_g = 446 g`, `d = available_stroke = 150 mm` (0.15 m), `k = 1.25`, `A_eff = 300 mm²`, `m_egg = 60 g`, `E_res = 0.65 J`.
- Tolerances applied: relative 1 % for derived quantities; absolute 0.1 g (masses), $0.01 (cost), 0.1 mm (geometry/throw).
- Mass convention: JSON `mass_g` per material row is read as the **row total** (not per unit); see ambiguity note A1.

## 1. Declared vs independently computed

| quantity | declared | independent | diff | verdict |
|---|---|---|---|---|
| H (input) | 10.0 m | 10.0 | 0 | OK |
| g (input) | 9.81 m/s² | 9.81 | 0 | OK |
| M (mass incl. egg) | 446.0 g | 446.0 | 0 | OK |
| v = √(2gH) | 14.007141 m/s | 14.0071409 | 3.6e-08 (0.0000 %) | OK |
| t_f = √(2H/g) | 1.427843 s | 1.42784312 | 1.2e-07 (0.0000 %) | OK |
| E_k = Mv²/2 | 43.7526 J | 43.75260 | 0 (0.0000 %) | OK |
| a_eq = v²/2d | 654.0 m/s² | 654.0 | 0 (0.0000 %) | OK |
| Δt_eq = 2d/v | 0.02141765 s | 0.0214176468 | 3.2e-09 (0.0000 %) | OK |
| F_avg = M(a_eq+g) | 296.059260 N | 296.059260 | 0 (0.0000 %) | OK |
| F_peak = k·F_avg | 370.074075 N | 370.074075 | 0 (0.0000 %) | OK |
| n_load = F_peak/(Mg) | 84.583333 g | 84.5833333 | 3.3e-07 (0.0000 %) | OK |
| F_egg = m_egg·g·n_load | 49.785750 N | 49.785750 | 0 (0.0000 %) | OK |
| σ = F_egg/A_eff | 0.165953 MPa | 0.1659525 | 5e-07 (0.0003 %) | OK |
| d_min, n=50 g | 200.0 mm | 200.0 | 2.8e-14 | OK |
| d_min, n=100 g | 100.0 mm | 100.0 | 1.4e-14 | OK |
| d_min, n=200 g | 50.0 mm | 50.0 | 7.1e-15 | OK |
| E_abs = E_k − E_res | 43.1026 J | 43.10260 | 0 (0.0000 %) | OK |
| η = E_abs/E_k | 0.98514374 | 0.98514374 | 2.9e-11 (0.0000 %) | OK |
| Σ material masses | 386.0 g | 386.0 | 0 | OK |
| declared total mass | 446.0 g | 446.0 (= 386 + 60) | 0 | OK |
| declared total cost | 2.84 $ | 2.84 | 4.4e-16 | OK |
| V = a·b·c/1e9 | 0.019683 m³ | 0.019683 | 0 (0.0000 %) | OK |
| stroke chain 120+20+10 | 150.0 mm | 150.0 | 0 | OK |

23 quantitative rows checked; 0 mismatches.

### Gate conditions (all re-evaluated, not scored)

| condition | result |
|---|---|
| k ≥ 1 | PASS (k = 1.25) |
| n_load ≤ 100 g (main verdict bound) | PASS (84.583 g) |
| η > 0.98 | PASS (0.985144) |
| E_res < 0.8 J | PASS (0.65) |
| 0 ≤ E_res ≤ E_k | PASS (0 ≤ 0.65 ≤ 43.7526) |
| total mass ≤ 500 g | PASS (446) |
| cost ≤ $5.00 | PASS (2.84) |
| build time ≤ 30 min | PASS (26) |
| each external side ≤ 300 mm | PASS (max 270) |
| V ≤ 0.02 m³ | PASS (0.019683) |
| all quantities non-negative | PASS |
| egg not glued (`glued: false`) | PASS |
| egg not rigid to shell (`rigid_to_shell: false`) | PASS |
| d_available ≥ d_min(100 g) | PASS (150 ≥ 100 mm) |

## 2. Independent sums table

| item | independent value | declared | verdict |
|---|---|---|---|
| Σ 12 material rows, g | 386.0 | 386 (implicit: 446 − 60) | OK |
| egg mass counted exactly once, g | 60.0 | 60.0 | OK |
| total mass Σ + egg, g | 446.0 | 446.0 | OK (Δ = 0 g ≤ 0.1 g) |
| Σ costs, $ | 2.84 | 2.84 | OK (Δ = 4.4e-16 ≤ 0.01) |
| volume a·b·c, m³ | 0.019683 | 0.019683 | OK (≤ 0.02) |
| external sides, mm | 270 / 270 / 270 | 270 / 270 / 270 | OK (≤ 300 each) |
| build time, min | 26 (declared only; not derivable from materials) | 26 | OK (≤ 30) |

## 3. Material allowlist / forbidden materials

Allowlist and bans taken from `experiments/egg-drop/egg-drop-test.md`:

> `:56` — "Разрешённые материалы | Бумага, картон, соломинки, зубочистки, резинки, скотч, верёвка, пластиковые пакеты, воздушные шары, вата, поролон, пенопласт, пластиковые бутылки, яичные лотки"
> `:57` — "Запрещённые материалы | Металл, стекло, жёсткий пластик (толще 2 мм), клей (кроме скотча), готовые амортизаторы"
> `:58` — "Крепление яйца | Яйцо не должно быть приклеено; допускается фиксация резинками/верёвкой"

Category-by-category (JSON `materials[].category`), 12 of 12 map to the allowlist:

| category | allowlist | evidence |
|---|---|---|
| картон | ALLOWED | `:56` "картон"; fixture `:71` `"category": "картон"` |
| бумага | ALLOWED | `:56` "Бумага"; `:72` "бумага" |
| соломинки | ALLOWED | `:56` "соломинки"; `:73` |
| зубочистки | ALLOWED | `:56` "зубочистки"; `:74` |
| резинки | ALLOWED | `:56` "резинки"; `:75` |
| скотч | ALLOWED | `:56` "скотч" (`:57` allows tape as the only "glue"); `:76` |
| верёвка | ALLOWED | `:56` "верёвка"; `:77` |
| пластиковые пакеты | ALLOWED | `:56` "пластиковые пакеты"; `:78` |
| вата | ALLOWED | `:56` "вата"; `:79` |
| поролон | ALLOWED | `:56` "поролон"; `:80` |
| пенопласт | ALLOWED | `:56` "пенопласт"; `:81` |
| яичные лотки | ALLOWED | `:56` "яичные лотки"; `:82` |

Forbidden-material sweep (none found):

- Metal / glass: no category names a metal or glass item; all 12 categories are paper/wood-plastic-soft items. → clean.
- Hard plastic > 2 mm: the only plastic-bearing entries declare thickness — `:76` `"plastic_thickness_mm": 0.1` (tape) and `:78` `"plastic_thickness_mm": 0.05` (bag); fixture prose `:43` "влагозащитный чехол (толщина 0.05 мм)". Both ≪ 2 mm → clean, thickness is declared where applicable.
- Glue other than tape: fixture `:26` "Клей не используем: все соединения выполнены на скотче"; no material row is an adhesive other than `скотч` → clean.
- Egg glued: `:86` `"glued": false`, `:87` `"rigid_to_shell": false`, `:88` `"attachment": "suspended"`; prose `:27` "Яйцо не приклеено — только резинки и ватный ложемент." → conforms to `:58`.
- Ready-made shock absorbers: no `готовый амортизатор` item is present; foam/polystyrene are raw allowlisted materials used as pads (`:80`, `:81`) → no violation. See ambiguity A2.

### Ambiguities (reported, not resolved here)

- **A1 — mass column semantics.** The spec (`:204` "Полный список материалов с массами") does not say whether a row's `mass_g` is per unit or the row total, while rows carry `quantity` (up to 12). Under "row total" the sums reconcile exactly (386 + 60 = 446); under "per unit" the system would be 1 514 g (Σ mass·quantity = 1 454 g + 60 g egg) and violate the 500 g limit. The fixture is only self-consistent under the "row total" reading, which is what was verified.
- **A2 — "готовые амортизаторы".** The spec bans ready-made shock absorbers but explicitly allowlists `поролон`/`пенопласт`/`вата`. Using those as compressible pads (`:79`–`:81`) is an allowed-material use, not a bought shock-absorber unit; a strict reader could call the layered pad stack an "amortiser". Not counted as a violation.
- **A3 — tape thickness field.** `:76` sets `plastic_thickness_mm: 0.1` for tape, which the spec does not require (tape is allowed regardless); harmless, and it keeps the ≤ 2 mm rule trivially satisfied.

## 4. Prose ↔ JSON internal consistency

Spot-check of the prose (§2, §3) against the JSON `results`/`totals`/`outer_dimensions_mm`:

| prose claim | prose location | JSON value | agrees |
|---|---|---|---|
| v_impact 14.007 м/с | `:208` | `v_impact_m_s: 14.007141` | yes |
| t_fall 1.4278 с | `:209` | `1.427843` | yes |
| Ek 43.753 Дж | `:210` | `43.7526` | yes |
| dt_eq 0.021418 с | `:211` | `0.02141765` | yes |
| F_avg 296.059 Н | `:212` | `296.059260` | yes |
| F_peak 370.074 Н | `:213` | `370.074075` | yes |
| n_load 84.583 g | `:214` | `84.583333` | yes |
| sigma_egg 0.16595 МПа | `:215` | `0.165953` | yes |
| eta 0.98514 | `:216` | `0.98514374` | yes |
| итоговая масса 446 г | `:49` | `total_mass_g: 446.0` | yes |
| бюджет 2.84 $ | `:49` | `total_cost_usd: 2.84` | yes |
| время сборки 26 минут | `:50` | `build_time_min: 26.0` | yes |
| габариты 270 × 270 × 270 мм | `:50` | `outer_dimensions_mm 270/270/270` | yes |
| объём 0.019683 м³ | `:50` | re-derived a·b·c/1e9 | yes |
| ход 150 мм = 120 + 20 + 10 | `:55-56` | `stroke_chain_mm.sum = 150` | yes |
| «150 мм больше 118 мм при 84.6 g» | `:218-219` | d_min(84.6 g) = 10000/84.6 = 118.2 mm | yes |
| «0.166 МПа много ниже 25 МПа» | `:222` | σ = 0.16595 vs `σ_comp` 25 МПа (`:31`) | yes |

Prose and JSON agree on every checked number; verbatim copies of the JSON values (rounded) appear in the §3 numeric table.

## 5. Verdict

- 23 quantitative rows recomputed independently, 0 mismatches; all declared values reproduce within the stated tolerances (largest relative deviation 0.0003 %, on σ).
- Independent sums reconcile: 386 g materials + 60 g egg = 446 g; $2.84; 0.019683 m³; max side 270 mm; 26 min — all within the spec limits of 500 g / $5.00 / 0.02 m³ / 300 mm / 30 min.
- All 12 material categories are on the allowlist; no metal, glass, >2 mm hard plastic, non-tape glue, or ready-made shock absorber; egg not glued; plastic thickness declared (0.1 mm tape, 0.05 mm bag).

known-good arithmetic: CONSISTENT
