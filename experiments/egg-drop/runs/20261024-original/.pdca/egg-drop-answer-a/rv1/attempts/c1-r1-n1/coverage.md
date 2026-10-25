# Coverage manifest and machine-readable table format — `experiments/egg-drop/answer-a.md`

Attempt: `.pdca/egg-drop-answer-a/rv1/attempts/c1-r1-n1/` (cycle 1, plan r1, attempt n1, contract rv1).
Purpose: this file is the **answer → spec bullet** map validated by `C1` (`--case structure`, check `A03.coverage`)
and the **binding format contract** the answer follows. CHECK confirms the *content* of each anchor; `C1` only
proves that every bullet is mapped and that the tables parse.

## 1. Machine-readable table format (as implemented in the answer)

The answer carries **9 fenced `numeric` blocks**. Each block is a fenced code block whose info string is
exactly `numeric`, whose first content line is `# block: <id>`, followed by rows `key | value | unit`.
Lines starting with `#` are comments; empty lines are ignored; a duplicate key is an error.
Numeric values accept a decimal point or a decimal comma. Units are **strict tokens** from this list:
`g`, `mm`, `m`, `m2`, `m3`, `s`, `m/s`, `m/s2`, `kg/m3`, `kg*m/s`, `j`, `n`, `usd`, `min`, `-`
(`-` for dimensionless numbers and string values).

```numeric
# block: design
mass_total_g | 460 | g
dim_x_mm | 270 | mm
...
```

### Required blocks and keys (as written in the answer)

| Block | Keys used | Checks that consume them |
|---|---|---|
| `design` | `mass_total_g` (g), `dim_x_mm`, `dim_y_mm`, `dim_z_mm` (mm), `volume_m3` (m3), `cost_usd` (usd), `assembly_min` (min) | A05 |
| `materials` | `mass_egg_g` (g) + 9 pairs `matNN_name` (`-`, free text) and `matNN_mass_g` (g) | A04, A05.mass_sum |
| `constraints` | `egg_glued` (0), `protected_sides` (6), `braking_travel_mm` (mm; operating point 47.6 of the 96 mm resource) | A04, A07 |
| `impact` | `H_m`, `g_m_s2`, `rho_air_kg_m3`, `mass_total_g`, `drag_mode=deployment`, `deploy_delay_s`, `Cd_before`, `area_before_m2`, `Cd_after`, `area_after_m2`, `v_control_m_s`, `v_impact_m_s`, `t_fall_s`, `E_k_J`, `p_kg_m_s` | A06, A07 |
| `criteria` | `eta`, `E_egg_J`, `E_crit_J`, `dt_brake_s`, `brake_distance_mm`, `peak_factor`, `a_avg_m_s2`, `a_peak_m_s2`, `n_peak`, `n_crit`, `F_egg_peak_N`, `F_sys_peak_N`, `F_sys_avg_N`, `eta_required`, `binding_gate` | A07, A08 |
| `sensitivity` | `E_crit_1_J` = 1.0, `E_crit_2_J` = 1.5, `eta_required_1`, `eta_required_2`, `n_crit_sens` = 50 | A07, A08 |
| `reliability` | `p_single` (0.930), `p_three` (0.768), `p_mode=damage` | A09 |
| `scenario20` | `H_m`, `mass_total_g`, `v_control_m_s`, `v_impact_m_s`, `E_k_J`, `E_egg_J`, `eta` | A10 |
| `alternatives` | 3 complete triples `altN_mass_g`, `altN_cost_usd`, `altN_p_single` | A10 |

The harness **recomputes** every value and compares it with the declared one; tolerances are printed per
check and were not widened for this candidate.

## 2. Spec-bullet coverage map (`A03`)

Every bullet of `experiments/egg-drop/egg-drop-test.md` §4.1–4.6 (`egg-drop-test.md:197-231`). `C1` fails if
an ID is absent from this table; CHECK confirms that each anchor actually says what the bullet requires.

| Bullet | Section | Anchor in `answer-a.md` (heading + quoted lead-in) | Evidence | Status |
|---|---|---|---|---|
| 4.1.1 | §4.1 Концепция | `### 1.1. Название и назначение` — «**«Кокон К-10»** — картонно-пенный контейнер с жёстким куполом-парашютом» | doc §1.1 | met |
| 4.1.2 | §4.1 Концепция | `### 1.2. Принцип работы` — «Энергия удара снимается последовательно…» (3 стадии) | doc §1.2 | met |
| 4.1.3 | §4.1 Концепция | `### 1.3. Схема` — «купол Ø500 (пакет), 8 строп по 300 мм», «рабочий ход 47,6 мм» | doc §1.3 | met |
| 4.2.1 | §4.2 Спецификация | `### 2.1. Материалы и массы` — таблица «№ \| Материал \| Масса, г \| Что из него» (9 позиций) | doc §2.1, block `materials` | met |
| 4.2.2 | §4.2 Спецификация | `### 2.2. Габариты элементов` — таблица «Элемент \| Размеры, мм \| Кол-во» | doc §2.2 | met |
| 4.2.3 | §4.2 Спецификация | `### 2.3. Крепление яйца` — «Яйцо **не приклеено**.» резинки + шпагат, съёмное | doc §2.3, block `constraints` | met |
| 4.2.4 | §4.2 Спецификация | `### 2.1` — строка «**Итого** \| **460** \| предел 500 г» | doc §2.1, block `design` | met |
| 4.2.5 | §4.2 Спецификация | `### 2.5. Стоимость` — «**Итого** \| \| \| **$2,67** (предел $5,00)» | doc §2.5, block `design` | met |
| 4.3.1 | §4.3 Физические расчёты | `### 3.2. Скорость падения` — «$v_{control} = \sqrt{2gH} = 14{,}01$» и «$v_{impact} = 5{,}59$ м/с» | doc §3.2, block `impact` | met |
| 4.3.2 | §4.3 Физические расчёты | `### 3.3. Импульс и кинетическая энергия` — «$E_k = … = 7{,}18$ Дж» | doc §3.3, block `impact` | met |
| 4.3.3 | §4.3 Физические расчёты | `### 3.4. Тормозной путь, время и ускорение` — «$\Delta t = 2x/v_{impact} = 17{,}0$ мс» | doc §3.4, block `criteria` | met |
| 4.3.4 | §4.3 Физические расчёты | `### 3.5. Средняя и пиковая сила` — «$F_{peak} = … = 202$ Н», «$p_f = 1{,}34$» | doc §3.5, block `criteria` | met |
| 4.3.5 | §4.3 Физические расчёты | `### 3.8. Два независимых критерия` — «$n_{peak} = 44{,}7 \le 100$» | doc §3.8, block `criteria` | met |
| 4.3.6 | §4.3 Физические расчёты | `### 3.7. Энергобаланс и эффективность` — «**Независимое обоснование $\eta$**» (таблица стадий, неопределённость) | doc §3.7, block `criteria` | met |
| 4.3.7 | §4.3 Физические расчёты | `### 3.12. Вердикт` — «**Яйцо выживает.**» | doc §3.12 | met |
| 4.4.1 | §4.4 Оценка надёжности | `### 4.2. Один сброс: дерево событий` — «Итог: **$P_1 \approx 0{,}93$**» | doc §4.2, block `reliability` | met |
| 4.4.2 | §4.4 Оценка надёжности | `### 4.3. Три сброса подряд` — «$P_3 = 0{,}930 \cdot 0{,}917 \cdot 0{,}900 = 0{,}768$» | doc §4.3, block `reliability` | met |
| 4.4.3 | §4.4 Оценка надёжности | `### 4.4. Слабые места` — таблица «Слабое место \| Механизм отказа \| Покрыто ли запасом» | doc §4.4 | met |
| 4.4.4 | §4.4 Оценка надёжности | `### 4.5. Что ещё может пойти не так` — отказ/позднее раскрытие купола, смещение яйца, удар на крышку | doc §4.5 | met |
| 4.5.1 | §4.5 Альтернативы | `### 5.1`–`### 5.3` — три альтернативы с обоснованием | doc §5.1–5.3, block `alternatives` | met |
| 4.5.2 | §4.5 Альтернативы | `### 5.4. Сравнение` — таблица «Вариант \| Масса \| Цена \| η \| n_peak \| P1» | doc §5.4, block `alternatives` | met |
| 4.6.1 | §4.6 Итерации | `### 6.1. Что измерить после первого сброса` — 7 наблюдаемых величин с порогами и действиями | doc §6.1 | met |
| 4.6.2 | §4.6 Итерации | `### 6.3. Что меняется в конструкции для 20 м` — таблица изменений и пересчёт | doc §6.2–6.3, block `scenario20` | met |

## 3. Notes for CHECK

- `C1` proves structure only: 6 headings, 9 blocks, schema, this map's completeness, frozen hashes and the
  read-only inventory. It does not prove that a mapped section actually says the right thing.
- A04 also needs the engineering review of the scheme/spec: allowed materials (`:56`), no metal / glass /
  plastic > 2 mm / glue except tape / ready-made absorbers (`:57`), egg not glued (`:58`), protection from
  all sides (`:271`), real braking travel (`:272`).
- A08/A09 interpretation (η basis, probability assumptions, explanation of 49 J / 0.98 / 25 500 g) is a
  CHECK judgement; `C2` only proves the arithmetic.
- Deliberate reading choices to review explicitly: (a) the 300 mm envelope applies to the assembled device,
  the deployed Ø500 canopy is outside it, and the answer shows that both gates still pass without the
  canopy (67.4 g, 0.105 J) — see doc §2.2 and §4.5; (b) `braking_travel_mm` is the operating point
  (47.6 mm), while the cartridge resource is 96 mm — the worst case uses 95.3 mm of it.
