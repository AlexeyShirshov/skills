#!/usr/bin/env python3
"""Independent recomputation of experiments/egg-drop/fixtures/known-good/answer.md.

Written without reading check_answer.py. Stdlib only. Python 3.10+.
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

FIX = Path("/home/alex/sources/skills/experiments/egg-drop/fixtures/known-good/answer.md")

raw = FIX.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
text = raw.decode("utf-8")

# --- extract the JSON block ------------------------------------------------
m = re.search(r"```json\s*\n(.*?)\n```", text, re.S)
if not m:
    sys.exit("no json block")
data = json.loads(m.group(1))

phys = data["physics"]
H = phys["H_m"]
g = phys["g_m_s2"]
mats = data["materials"]
egg_m = data["egg"]["mass_g"]
tot = data["totals"]
outer = data["outer_dimensions_mm"]
br = data["braking"]
res = data["results"]

# independent sums
sum_mass = sum(x["mass_g"] for x in mats)
sum_cost = sum(x["cost_usd"] for x in mats)
sum_mass_all = sum_mass + egg_m
nonneg = all(x["mass_g"] >= 0 and x["cost_usd"] >= 0 for x in mats) and egg_m >= 0
vol = outer["length"] * outer["width"] * outer["height"] / 1e9
sides = [outer["length"], outer["width"], outer["height"]]

# physics
M = sum_mass_all / 1000.0
d = br["available_stroke_mm"] / 1000.0
k = br["peak_factor_k"]
A = br["effective_contact_area_mm2"]
v = math.sqrt(2 * g * H)
t_f = math.sqrt(2 * H / g)
Ek = M * v * v / 2
a_eq = v * v / (2 * d)
dt_eq = 2 * d / v
F_avg = M * (a_eq + g)
F_peak = k * F_avg
n_load = F_peak / (M * g)
F_egg = (egg_m / 1000.0) * g * n_load
sigma = F_egg / A  # N/mm^2 == MPa
d_min = {n: v * v / (2 * n * g) * 1000 for n in (50, 100, 200)}
E_res = res["E_residual_J"]
E_abs = Ek - E_res
eta = E_abs / Ek
stroke_sum = sum(v_ for kk, v_ in br["stroke_chain_mm"].items() if kk != "sum")

rows = []


def cmp(name, declared, computed, kind="rel", tol=0.01, unit=""):
    if declared is None:
        rows.append((name, "n/a", computed, "n/a", "N/A", unit))
        return None
    if kind == "rel":
        # relative tolerance, but absolute 0.1 g / 0.01 $ / 0.1 mm handled by caller-chosen kind
        diff = abs(computed - declared)
        rel = diff / abs(declared) if declared else (0.0 if diff == 0 else float("inf"))
        ok = rel <= tol
        rows.append((name, declared, computed, f"{rel*100:.4f}% (abs {diff:.6g})", "OK" if ok else "MISMATCH", unit))
    else:
        diff = abs(computed - declared)
        ok = diff <= tol
        rows.append((name, declared, computed, f"abs {diff:.6g}", "OK" if ok else "MISMATCH", unit))
    return ok


cmp("H (input)", H, H, "abs", 1e-9, "m")
cmp("g (input)", g, g, "abs", 1e-9, "m/s^2")
cmp("M total (sum)", tot["total_mass_g"], sum_mass_all, "abs", 0.1, "g")
cmp("v_impact", res["v_impact_m_s"], v, "rel", 0.01, "m/s")
cmp("t_fall", res["t_fall_s"], t_f, "rel", 0.01, "s")
cmp("Ek", res["Ek_J"], Ek, "rel", 0.01, "J")
cmp("a_eq", res["a_eq_m_s2"], a_eq, "rel", 0.01, "m/s^2")
cmp("delta_t_eq", res["delta_t_eq_s"], dt_eq, "rel", 0.01, "s")
cmp("F_avg", res["F_avg_N"], F_avg, "rel", 0.01, "N")
cmp("F_peak", res["F_peak_N"], F_peak, "rel", 0.01, "N")
cmp("n_load", res["n_load_g"], n_load, "rel", 0.01, "g")
cmp("F_egg", res["F_egg_N"], F_egg, "rel", 0.01, "N")
cmp("sigma_egg", res["sigma_egg_MPa"], sigma, "rel", 0.01, "MPa")
for n, key in ((50, "n50"), (100, "n100"), (200, "n200")):
    cmp(f"d_min n={n}", res["d_min_mm"][key], d_min[n], "abs", 0.1, "mm")
cmp("E_absorbed", res["E_absorbed_J"], E_abs, "rel", 0.01, "J")
cmp("eta", res["eta"], eta, "rel", 0.01, "-")
# independent sums / geometry / limits
cmp("sum(material masses)", sum_mass, sum_mass, "abs", 0.0, "g")
cmp("total_mass_g", tot["total_mass_g"], sum_mass_all, "abs", 0.1, "g")
cmp("total_cost_usd", tot["total_cost_usd"], sum_cost, "abs", 0.01, "$")
cmp("volume", 0.019683, vol, "rel", 0.01, "m^3")
cmp("stroke chain sum", br["stroke_chain_mm"]["sum"], stroke_sum, "abs", 0.1, "mm")
cmp("available_stroke <= outer height", br["available_stroke_mm"], min(br["available_stroke_mm"], outer["height"]), "abs", 0.1, "mm")

print(f"sha256 {sha}")
print(f"file {FIX}")
print()
print("DECLARED vs COMPUTED")
for r in rows:
    print(f"{r[0]:28s} | decl {r[1]!s:>14} | comp {r[2]:.9g} | {r[3]:>28} | {r[4]} | {r[5]}")
print()

# gate checks
expr = {
    "k >= 1": k >= 1,
    "n_load <= 100 g": n_load <= 100.0,
    "eta > 0.98": eta > 0.98,
    "E_res < 0.8 J": 0 < E_res < 0.8,
    "0 <= E_res <= Ek": 0 <= E_res <= Ek,
    "total <= 500 g": sum_mass_all <= 500,
    "cost <= 5.00": sum_cost <= 5.00 + 1e-9,
    "time <= 30 min": tot["build_time_min"] <= 30,
    "each side <= 300 mm": max(sides) <= 300,
    "volume <= 0.02 m3": vol <= 0.02,
    "all quantities non-negative": nonneg,
    "egg glued == false": data["egg"]["glued"] is False,
    "egg rigid_to_shell == false": data["egg"]["rigid_to_shell"] is False,
    "d_available >= d_min(100g)": br["available_stroke_mm"] >= d_min[100],
}
print("GATES")
for kk, vv in expr.items():
    print(f"  {'PASS' if vv else 'FAIL'}  {kk}")
print()

print("SUMS")
print(f"  sum_mass_g={sum_mass:.6g}  egg_g={egg_m:.6g}  total_g={sum_mass_all:.6g}  declared_total_g={tot['total_mass_g']:.6g}")
print(f"  sum_cost_usd={sum_cost:.6g}  declared_cost_usd={tot['total_cost_usd']:.6g}")
print(f"  volume_m3={vol:.9g}  sides_mm={sides}  max_side={max(sides):.6g}")
print(f"  build_time_min={tot['build_time_min']:.6g}")
print()

# categories / allowlist
allowed = {"бумага", "картон", "соломинки", "зубочистки", "резинки", "скотч", "верёвка",
           "пластиковые пакеты", "воздушные шары", "вата", "поролон", "пенопласт",
           "пластиковые бутылки", "яичные лотки"}
cats = [x["category"] for x in mats]
bad = [c for c in cats if c not in allowed]
print("CATEGORIES")
for c in cats:
    print(f"  {'ALLOWED' if c in allowed else 'FORBIDDEN?'}  {c}")
print(f"  not_in_allowlist={bad}")
print()

# prose vs json spot check
prose = {
    "v_impact": "14.007 м/с",
    "t_fall": "1.4278 с",
    "Ek": "43.753 Дж",
    "dt_eq": "0.021418 с",
    "F_avg": "296.059 Н",
    "F_peak": "370.074 Н",
    "n_load": "84.583 g",
    "sigma": "0.16595 МПа",
    "eta": "0.98514",
    "total_mass": "446 г",
    "cost": "2.84 $",
    "time": "26 минут",
    "volume": "0.019683 м³",
}
print("PROSE SPOT-CHECK (letter-presence in section 3 table / section 2 prose)")
for kk, vv in prose.items():
    print(f"  {'FOUND' if vv in text else 'MISSING'}  {kk}: '{vv}'")
print()
print(f"tolerance_rel=0.01 mass_abs=0.1g cost_abs=0.01usd geom_abs=0.1mm")
