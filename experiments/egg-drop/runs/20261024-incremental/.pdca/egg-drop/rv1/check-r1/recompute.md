# Independent recompute — frozen candidate `m001` (facts and numbers only)

Stream A of the CHECK gather for campaign `egg-drop`. **No rubric score, no PASS/FAIL gate verdict.**

* Script: `/tmp/opencode/egg_recompute.py` (Python 3.10), written from the task statement, reading **JSON inputs only**
  plus the prose of `answer.md` and the specification text.
* `check_answer.py` was **not read** (only `stat`/`sha256sum`, see `integrity.md`).
* Inputs: `.pdca/egg-drop/rv1/m001/answer.md`, `.pdca/egg-drop/rv1/m001/egg-drop-test.md`.
* Constants taken from the JSON: `H=10.0 m`, `g=9.81 m/s²`, `M=0.458 kg`, `d=165 mm`, `k=1.30`, `A_eff=320 mm²`, `m_egg=60 g`.

## 1. Recomputed quantities

| id | quantity | unit | declared | recomputed | diff | rel. diff | tolerance | match |
|---|---|---|---|---|---|---|---|---|
| `v` | v_impact | m/s | 14.007141 | 14.00714104 | +3.591e-08 | 2.56e-09 | rel<=1e-4 | yes |
| `t` | t_fall | s | 1.427843 | 1.427843123 | +1.229e-07 | 8.61e-08 | rel<=1e-4 | yes |
| `Ek` | Ek | J | 44.9298 | 44.9298 | +0.000e+00 | 0.00e+00 | rel<=1e-4 | yes |
| `a` | a_eq | m/s² | 594.545455 | 594.5454545 | -4.545e-07 | 7.65e-10 | rel<=1e-4 | yes |
| `dt` | delta_t_eq | s | 0.023559 | 0.02355941153 | +4.115e-07 | 1.75e-05 | rel<=1e-4 | yes |
| `Favg` | F_avg | N | 276.794798 | 276.7947982 | +1.818e-07 | 6.57e-10 | rel<=1e-4 | yes |
| `Fpeak` | F_peak | N | 359.833238 | 359.8332376 | -3.636e-07 | 1.01e-09 | rel<=1e-4 | yes |
| `n_load` | n_load | g | 80.087879 | 80.08787879 | -2.121e-07 | 2.65e-09 | rel<=1e-4 | yes |
| `Fegg` | F_egg | N | 47.139725 | 47.13972545 | +4.545e-07 | 9.64e-09 | rel<=1e-4 | yes |
| `sigma` | sigma_egg | MPa | 0.147312 | 0.147311642 | -3.580e-07 | 2.43e-06 | rel<=1e-3 | yes |
| `dmin_n50` | d_min @ 50 g | mm | 200 | 200 | -2.842e-14 | 1.42e-16 | abs<=0.05 mm | yes |
| `dmin_n100` | d_min @ 100 g | mm | 100 | 100 | -1.421e-14 | 1.42e-16 | abs<=0.05 mm | yes |
| `dmin_n200` | d_min @ 200 g | mm | 50 | 50 | -7.105e-15 | 1.42e-16 | abs<=0.05 mm | yes |
| `Eres` | E_residual | J | 0.55 | 0.55 | +0.000e+00 | 0.00e+00 | identity (input) | yes |
| `Eabs` | E_absorbed = Ek - Eres | J | 44.3798 | 44.3798 | +0.000e+00 | 0.00e+00 | abs<=0.01 | yes |
| `eta` | eta = Eabs/Ek | - | 0.987759 | 0.9877586813 | -3.187e-07 | 3.23e-07 | rel<=1e-4 | yes |
| `M` | total mass M used in Ek | kg | 0.458 | 0.458 | +0.000e+00 | 0.00e+00 | identity | yes |
| `sum_mass` | Σ material mass_g (egg excluded) | g | 398 | 398 | +0.000e+00 | 0.00e+00 | abs<=0.1 g | yes |
| `sum_mass_egg` | Σ materials + egg(once) | g | 458 | 458 | +0.000e+00 | 0.00e+00 | abs<=0.1 g | yes |
| `sum_cost` | Σ cost_usd | $ | 3.11 | 3.11 | +0.000e+00 | 0.00e+00 | abs<=0.01 | yes |

Quantities recomputed: **20**; outside tolerance: **0**.

Formulas used independently: `v=sqrt(2gH)`, `t=sqrt(2H/g)`, `Ek=Mv²/2`, `a=v²/(2d)`, `Δt=2d/v`,
`F_avg=M(a+g)`, `F_peak=k·F_avg`, `n=F_peak/(Mg)`, `F_egg=m_egg·g·n`, `σ=F_egg/A_eff`,
`d_min=v²/(2ng)`, `E_abs=Ek−E_res`, `η=E_abs/Ek`. `M` includes the egg (458 g).

## 2. Mass and cost sums

| item | value | declared | diff | tolerance | match |
|---|---|---|---|---|---|
| Σ material `mass_g` (egg excluded) | 398.0 g | 398.0 g | +0.0 g | 0.1 g | yes |
| Σ materials + egg ×1 | 458.0 g | 458.0 g | +0.0 g | 0.1 g | yes |
| Σ `cost_usd` | 3.11 $ | 3.11 $ | +0.00 $ | 0.01 $ | yes |

* Egg appears **once**: the 12 material rows contain no egg entry (`egg` is a separate object); "materials 398 g + egg 60 g = 458 g" matches the prose.
* Negative values: mass `none`, cost `none`, other `none`.

### 2.1 Plausibility of per-item masses against the declared dimensions

| id | qty | line mass, g | per-unit mass, g | dimensions per unit, mm | bbox volume per unit, m³ | implied per-unit density, kg/m³ | areal density (two largest sides), kg/m² |
|---|---|---|---|---|---|---|---|
| `cardboard_frame` | 1 | 165.0 | 165.0 | 250 × 250 × 3 | 0.000188 | 880.0 | 2.64 |
| `paper_cones` | 16 | 55.0 | 3.4375 | 60 × 60 × 96 | 0.000346 | 9.95 | 0.597 |
| `straws` | 8 | 10.0 | 1.25 | 240 × 6 × 6 | 8.64e-06 | 144.68 | 0.868 |
| `toothpicks` | 12 | 3.0 | 0.25 | 65 × 2 × 2 | 2.6e-07 | 961.54 | 1.923 |
| `rubber_bands` | 8 | 8.0 | 1.0 | 120 × 3 × 1 | 3.6e-07 | 2777.78 | 2.778 |
| `tape` | 1 | 30.0 | 30.0 | 5000 × 48 × 0.09 | 2.16e-05 | 1388.89 | 0.125 |
| `rope` | 1 | 14.0 | 14.0 | 5000 × 4 × 4 | 8e-05 | 175.0 | 0.7 |
| `plastic_bag` | 1 | 4.0 | 4.0 | 300 × 250 × 0.05 | 3.75e-06 | 1066.67 | 0.053 |
| `cotton` | 1 | 30.0 | 30.0 | 140 × 120 × 40 | 0.000672 | 44.64 | 1.786 |
| `foam` | 5 | 40.0 | 8.0 | 200 × 200 × 20 | 0.0008 | 10.0 | 0.2 |
| `polystyrene` | 8 | 24.0 | 3.0 | 50 × 50 × 40 | 0.0001 | 30.0 | 1.2 |
| `egg_carton` | 1 | 15.0 | 15.0 | 140 × 140 × 40 | 0.000784 | 19.13 | 0.765 |

No item mass is physically absurd on a per-unit basis: cardboard 880 kg/m³ (solid-equivalent), wood toothpicks
962 kg/m³, molded pulp 19 kg/m³, cotton 45 kg/m³, soft foam 10 kg/m³, EPS 30 kg/m³, hollow paper cone 10 kg/m³,
hollow straw 145 kg/m³, thin film 10⁰–10³ kg/m³. Three items sit at the heavy end of their class but stay within
an order of magnitude of a plausible value: tape 125 g/m² areal (typical packing tape 45–70 g/m², ≈2×),
rubber bands ≈2.8 kg/m² at 1 mm thickness (≈2× a 1.1 g/cm³ rubber at 1 mm), rope 2.8 g/m at 4 mm (light, not absurd).

Declared-dimension observation (arithmetic fact, not scoring):
* `cardboard_frame` is declared as **one** blank `250 × 250 × 3 mm` (0.0625 m², areal density 2.64 kg/m² —
  above typical 3 mm corrugated board) while its role (box 250 × 250 × 290 + cap + ribs) needs ≈0.415 m²;
  at that area the same 165 g gives ≈398 g/m², i.e. the **mass** is plausible for the role but the declared
  **blank dimension/quantity** is smaller than the role requires.

## 3. Hard limits

| id | limit | value | unit | bound | satisfied |
|---|---|---|---|---|---|
| `L_mass` | total mass <= 500 g | 458 | g | 500 | yes |
| `L_cost` | budget <= $5.00 | 3.11 | $ | 5 | yes |
| `L_build` | build time <= 30 min | 28 | min | 30 | yes |
| `L_side_length` | side length <= 300 mm | 250 | mm | 300 | yes |
| `L_side_width` | side width <= 300 mm | 250 | mm | 300 | yes |
| `L_side_height` | side height <= 300 mm | 290 | mm | 300 | yes |
| `L_vol` | volume <= 0.02 m3 | 0.018125 | m3 | 0.02 | yes |

Volume recomputed from `outer_dimensions_mm`: 0.250 × 0.250 × 0.290 = 0.018125 m³.
Limits violated: **0**.

## 4. Dimensional chains (explicit addition)

| chain | addition as declared | sum | target | diff | ≤0.1 mm |
|---|---|---|---|---|---|
| height | 3 + 20 + 35 + 55 + 60 + 96 + 18 + 3 = 290 | 290 | 290.0 | +0.0 | yes |
| width | 3 + 20 + 76 + 52 + 76 + 20 + 3 = 250 | 250 | 250.0 | +0.0 | yes |
| lower stroke (JSON `braking.stroke_chain_mm`) | 60.0 + 96.0 + 9.0 = 165.0 | 165.0 | 165.0 | +0.0 | yes |

Prose breakdown of the same stroke: "60 (free gap) + 96 (crush) + 9 (compression of the bottom foam) = 165 mm".
The available stroke is non-zero (165 mm) and geometrically consistent: the egg+lodgement travels 60 mm of free
gap, crushes 96 mm of cones and compresses 9 mm into the declared 18 mm bottom foam; 165 mm of travel fits the
174 mm of material below the lodgement (60 + 96 + 18), so the chain does not demand more space than exists.

| comparison (not a chain the candidate declares) | addition | sum | d declared | diff |
|---|---|---|---|---|
| free gap + crush + **full** 18 mm foam | 60 + 96 + 18 = 174 | 174 | 165.0 | +9.0 |

Flag: the JSON field `braking.stroke_chain_mm.bottom_foam` is **9.0 mm**, while the height chain and the prose list
the same foam layer as **18 mm** and only 9 mm of it as compression. Label/parameter ambiguity, arithmetic unaffected.

## 5. Main peak, sensitivity, spec contradiction

* Design peak `n_load` = **80.087879 g** (declared 80.087879 g) → below 100 g: `n_load ≤ 100` holds.
* Sensitivity set present: `[50.0, 100.0, 200.0]` g; `d_min` keys `['n50', 'n100', 'n200']`; values `{'n50': 200.0, 'n100': 100.0, 'n200': 50.0}` mm
  vs recomputed `{'n50': 200.0, 'n100': 100.0, 'n200': 50.0}` mm (200/100/50 mm at 50/100/200 g).
* Spec line 152: `Яйцо выживает, если $n < n_{crit}$, где $n_{crit} \approx 50$–100 g для короткого импульса.`
* Spec line 160: `Это теоретический максимум. На практике из-за концентраторов напряжения и дефектов скорлупы реальный порог **в 100–1000 раз ниже**: $n_{crit,real} \approx 50$–200 g.`
* Contradiction disclosed in JSON `spec_contradiction.refs` = `['egg-drop-test.md:152', 'egg-drop-test.md:160']`: **True**;
  disclosed in prose ("Противоречие исходника", both `:152` and `:160` cited): **True**.

## 6. Survival criteria

| criterion | recomputed | bound | satisfied |
|---|---|---|---|
| η > 0.98 (strict) | 0.987759 | 0.98 | yes |
| η required for E_res < 0.8 J | 0.982194 | — | — |
| E_res < 0.8 J (strict) | 0.55 J | 0.8 J | yes |
| σ ≤ 25 MPa | 0.147312 MPa | 25 MPa | yes |

0.8 / 1.0 / 1.5 J range in prose, recomputed required η for each:

| E_res, J | η required = 1 − E_res/Ek | prose value |
|---|---|---|
| 0.8 | 0.9822 | 0.9822 |
| 1.0 | 0.9777 | 0.9777 |
| 1.5 | 0.9666 | 0.9666 |

E_res model: `E_res = Ek·(m_egg/M)·β`; implied β from the declared 0.55 J = **0.09344** (declared ≈0.093).
Sensitivity: β=0.093 → 0.547 J; β=0.13 → 0.765 J; β=0.15 → 0.883 J.

## 7. Probabilities

* `P1` = 0.943 ∈ [0,1]: True; decomposition 0.96·0.97 + 0.04·0.30 = 0.943200 (diff +0.000200).
* `P3` = 0.73 ∈ [0,1]: True; repeat model P3 = 0.943·0.90·0.86 = 0.729882 (diff -0.000118).
* `P3 ≤ P1`: True.
* Repeat-drop model present (explicit `P_(k+1) = P_k f_k`, `dependency_declared=true`): True.
* Bare cube check: P1³ = 0.838562; declared P3 equals P1³: **False** (the prose itself states P1³=0.839 is inapplicable).

## 8. Materials vs the allowlist

Spec allowlist (`egg-drop-test.md:56`): "Бумага, картон, соломинки, зубочистки, резинки, скотч, верёвка, пластиковые пакеты, воздушные шары, вата, поролон, пенопласт, пластиковые бутылки, яичные лотки "

Spec prohibited list (`:57`): "Металл, стекло, жёсткий пластик (толще 2 мм), клей (кроме скотча), готовые амортизаторы "

| material id | category (answer) | in allowlist | declared plastic thickness, mm |
|---|---|---|---|
| `cardboard_frame` | картон | yes | — |
| `paper_cones` | бумага | yes | — |
| `straws` | соломинки | yes | — |
| `toothpicks` | зубочистки | yes | — |
| `rubber_bands` | резинки | yes | — |
| `tape` | скотч | yes | 0.09 |
| `rope` | верёвка | yes | — |
| `plastic_bag` | пластиковые пакеты | yes | 0.05 |
| `cotton` | вата | yes | — |
| `foam` | поролон | yes | — |
| `polystyrene` | пенопласт | yes | — |
| `egg_carton` | яичные лотки | yes | — |

* All 12 categories are in the allowlist; none outside it. Max declared plastic thickness = **0.09 mm** (tape); the bag declares 0.05 mm; hard plastic > 2 mm: **False**.
* Egg `glued` = **False**, `rigid_to_shell` = **False**; attachment "suspended".
* Prohibition mentions in the prose (mentions only, not use):
  * "Запрещённые материалы — металл, стекло, жёсткий пластик толще 2 мм, клей — не используются"
  * "яйцо не приклеено"
  * "Готовые амортизаторы тоже не применяются"

## 9. Prose ↔ JSON consistency

| id | quantity | prose occurrence(s) | JSON value | match |
|---|---|---|---|---|
| `P_v` | v_impact | 14.007141, 14.007, 14.007141 | 14.007141 | yes |
| `P_t` | t_fall | 1.427843, 1.428, 1.427843 | 1.427843 | yes |
| `P_Ek` | Ek | 44.9298, 44.93, 44.9298, 44.93 | 44.9298 | yes |
| `P_d` | available stroke d | 165.0, 165.0, 165.0, 165.0 | 165 | yes |
| `P_k` | peak factor k | 1.3, 1.3, 1.3 | 1.3 | yes |
| `P_n` | n_load | 80.09, 80.087879, 80.09, 80.087879 | 80.087879 | yes |
| `P_sigma` | sigma_egg | 0.147312, 0.147, 0.147312, 0.147 | 0.147312 | yes |
| `P_eta` | eta | 0.987759, 0.9878, 0.987759, 0.9878 | 0.987759 | yes |
| `P_Eres` | E_residual | 0.55, 0.55 | 0.55 | yes |
| `P_mass` | total mass | 458.0 | 458 | yes |
| `P_cost` | total cost | 3.11 | 3.11 | yes |
| `P_build` | build time | 28.0 | 28 | yes |
| `P_env` | envelope | 250.0, 250.0, 290.0, 250.0 | 250 | yes |
| `P_vol` | volume | 0.018125 | 0.018125 | yes |
| `P_P1` | P1 | 0.943, 0.943 | 0.943 | yes |
| `P_P3` | P3 | 0.73, 0.73, 0.73 | 0.73 | yes |
| `P_bottom_foam` | bottom foam layer (height chain) vs JSON braking.stroke_chain_mm.bottom_foam | 18.0 | 9 | **NO** |
| `P_stroke_top` | top stroke | 45.0 | 45 | yes |
| `P_stroke_side` | side stroke | 86.0 | 86 | yes |
| `P_protection_sym` | protection covers 6 directions | 6.0 | 6 | yes |

Textual mismatches: **P_bottom_foam** —
only the `bottom_foam` label (9 mm compression vs 18 mm layer); every other required quantity (v, t, Ek, d, k,
n_load, σ, η, E_res, total mass, cost, build time, envelope, volume, P1, P3) agrees with the JSON within rounding.

### 9.1 Additional numeric claims in the prose (recomputed independently)

| id | prose | recomputed | diff | within rounding |
|---|---|---|---|---|
| `X_n_k1_0` | 61.6 | 61.61 | +0.010 | yes |
| `X_k_for_100g` | 1.62 | 1.623 | +0.003 | yes |
| `X_n_k1_15` | 70.9 | 70.85 | -0.050 | yes |
| `X_n_side_86` | 152.0 | 152.5 | +0.500 | yes |
| `X_n_top_45` | 290.0 | 290.2 | +0.200 | yes |
| `X_n_alt_mono_40` | 326.0 | 326.3 | +0.300 | yes |
| `X_n_alt_double_70` | 187.0 | 187.0 | +0.000 | yes |
| `X_v_20m` | 19.81 | 19.809 | -0.001 | yes |
| `X_t_20m` | 2.02 | 2.019 | -0.001 | yes |
| `X_Ek_20m` | 89.86 | 89.86 | +0.000 | yes |
| `X_n_20m_165mm` | 159.0 | 158.9 | -0.100 | yes |
| `X_Eres_beta_0_13` | 0.78 | 0.765 | -0.015 | **NO** |
| `X_Eres_beta_0_15` | 0.88 | 0.883 | +0.003 | yes |
| `X_chain_alt_top_100` | 364.0 | 364.0 | +0.000 | yes |
| `X_chain_20m` | 334.0 | 334.0 | +0.000 | yes |
| `X_chain_20m_trimmed` | 299.0 | 299.0 | +0.000 | yes |
| `X_mass_after_paper` | 515.0 | 515.0 | +0.000 | yes |
| `X_peak_pct` | 32.0 | 32.1 | +0.100 | yes |

All hold except `X_Eres_beta_0_13`: prose "при β = 0.13 … 0.78 Дж" vs recomputed 0.765 J (difference 0.015 J; the conclusion 0.765 J < 0.8 J is unchanged).
20 m scenario: v=19.809 m/s, t=2.019 s, Ek=89.86 J, d_min(100 g)=200 mm, peak at 165 mm ≈158.9 g;
chains 364 mm, 334 mm and 299 mm and the 515 g mass all reproduce as stated.

## 10. Red flags (§7 / evidence)

* Header disclaimer: "Аналитический проект: все числа получены расчётом по модели из задания, испытаний не проводилось."
* Claims of a conducted test or measurement: **0** found by keyword scan.
* Rubric self-score (S/10): **0** found.
* Explicit non-measurement statements present:
  * "Аналитический проект: все числа получены расчётом по модели из задания, испытаний не проводилось."
  * "Цены, массы закупных материалов и время сборки — оценки, а не измерения."
  * "$k = 1.30 \ge 1$ — инженерная оценка, не измерение."
  * "измерением коэффициент не подтверждён"
  * "Коэффициент $\beta$ — допущение, а не измерение."
  * "$P(\text{низ}) = 0.96$ — оценка, не измерение"
  * "После первого аналитического прогона (без физического испытания)"
* Section-level tension (qualified, not an unqualified contradiction):
  * §3 verdict: "Вердикт: яйцо выживет с высокой вероятностью при номинальной (нижней) ориентации"
  * §3 next sentence: "При боковом и верхнем ударе вердикт — «вероятно, нет»: защита там частичная."
  * qualified by orientation in the same paragraph; not an unqualified contradiction

No claim of a real drop test, no author self-score of the rubric, and no assumption presented as a measured
result was found in the prose.

---

Facts and numbers only: this file carries no rubric score and no PASS/FAIL gate verdict.
