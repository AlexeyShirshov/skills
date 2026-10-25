## 1. Концепция

Раздел с формулой $E_k=\frac{1}{2} m v^2$ и пояснением результатов.

## 2. Спецификация

Раздел с формулой $E_k=\frac{1}{2} m v^2$ и пояснением результатов.

## 3. Физические расчёты

Раздел с формулой $E_k=\frac{1}{2} m v^2$ и пояснением результатов.

## 4. Оценка надёжности

Раздел с формулой $E_k=\frac{1}{2} m v^2$ и пояснением результатов.

## 5. Альтернативы

Раздел с формулой $E_k=\frac{1}{2} m v^2$ и пояснением результатов.

## 6. Итерации

Раздел с формулой $E_k=\frac{1}{2} m v^2$ и пояснением результатов.

```numeric
# block: design
mass_total_g | 361.5 | g
dim_x_mm | 240 | mm
dim_y_mm | 240 | mm
dim_z_mm | 260 | mm
volume_m3 | 0.0140 | m3
cost_usd | 3.75 | usd
assembly_min | 22 | min
```

```numeric
# block: materials
mass_egg_g | 60 | g
mat01_name | cardboard | -
mat01_mass_g | 120 | g
mat02_name | foam | -
mat02_mass_g | 80 | g
mat03_name | plastic bag | -
mat03_mass_g | 45 | g
mat04_name | tape | -
mat04_mass_g | 15 | g
mat05_name | string | -
mat05_mass_g | 10 | g
mat06_name | cotton | -
mat06_mass_g | 30 | g
```

```numeric
# block: constraints
egg_glued | 0 | -
protected_sides | 6 | -
braking_travel_mm | 137 | mm
```

```numeric
# block: impact
H_m | 10.0 | m
g_m_s2 | 9.81 | m/s2
rho_air_kg_m3 | 1.225 | kg/m3
mass_total_g | 360 | g
drag_mode | constant | -
Cd | 1.2 | -
area_m2 | 0.0503 | m2
v_control_m_s | 14.007 | m/s
v_impact_m_s | 9.127 | m/s
t_fall_s | 1.680 | s
E_k_J | 14.994 | j
p_kg_m_s | 3.286 | kg*m/s
```

```numeric
# block: criteria
eta | 0.965 | -
E_egg_J | 0.525 | j
E_crit_J | 0.8 | j
dt_brake_s | 0.030 | s
brake_distance_mm | 137 | mm
peak_factor | 1.7 | -
a_avg_m_s2 | 304.2 | m/s2
a_peak_m_s2 | 517.2 | m/s2
n_peak | 52.7 | g
n_crit | 100 | g
F_egg_peak_N | 31.0 | n
F_sys_peak_N | 186.2 | n
F_sys_avg_N | 109.5 | n
eta_required | 0.9466 | -
binding_gate | energy | -
```

```numeric
# block: sensitivity
E_crit_1_J | 1.0 | j
E_crit_2_J | 1.5 | j
eta_required_1 | 0.9333 | -
eta_required_2 | 0.9000 | -
n_crit_sens | 50 | g
```

```numeric
# block: reliability
p_single | 0.92 | -
p_three | 0.779 | -
p_mode | independent | -
```

```numeric
# block: scenario20
H_m | 20.0 | m
mass_total_g | 360 | g
v_control_m_s | 19.81 | m/s
v_impact_m_s | 9.693 | m/s
E_k_J | 16.912 | j
E_egg_J | 0.592 | j
eta | 0.965 | -
```

```numeric
# block: alternatives
alt1_mass_g | 340 | g
alt1_cost_usd | 3.10 | usd
alt1_p_single | 0.88 | -
alt2_mass_g | 420 | g
alt2_cost_usd | 4.40 | usd
alt2_p_single | 0.90 | -
```

## 7. Лишнее
