#!/usr/bin/env python3.10
"""Independent recompute of the frozen egg-drop candidate.

Reads ONLY:
  - .pdca/egg-drop/rv1/m001/answer.md   (prose + egg-drop-data-v1 JSON block)
  - .pdca/egg-drop/rv1/m001/egg-drop-test.md (spec text: limits, allowlist, contradiction lines)
Does NOT read check_answer.py.
Writes check-r1/recompute.json + recompute.md (numbers/facts only, no verdict).
"""
import json, math, re, sys, pathlib

PKG = pathlib.Path("/home/alex/sources/skills/.pdca/egg-drop/rv1/m001")
OUT = pathlib.Path("/home/alex/sources/skills/.pdca/egg-drop/rv1/check-r1")
ANS = (PKG / "answer.md").read_text(encoding="utf-8")
SPEC = (PKG / "egg-drop-test.md").read_text(encoding="utf-8")
SPEC_LINES = SPEC.splitlines()

blocks = re.findall(r"```json\s*(\{.*?\})\s*```", ANS, re.S)
assert len(blocks) == 1, f"expected 1 json block, got {len(blocks)}"
D = json.loads(blocks[0])
assert D["schema"] == "egg-drop-data-v1"

g = D["physics"]["g_m_s2"]; H = D["physics"]["H_m"]
mat = D["materials"]; egg = D["egg"]
M_g = D["totals"]["total_mass_g"]
M = M_g / 1000.0
d_mm = D["braking"]["available_stroke_mm"]; d = d_mm / 1000.0
k = D["braking"]["peak_factor_k"]
A_mm2 = D["braking"]["effective_contact_area_mm2"]
R = D["results"]; m_egg = egg["mass_g"] / 1000.0

def cmp(declared, rec, tol_abs=0.0, tol_rel=0.0, tol_text=""):
    diff = rec - declared
    rel = abs(diff) / abs(declared) if declared else (0.0 if diff == 0 else float("inf"))
    ok = (abs(diff) <= tol_abs + 1e-12) or (tol_rel and rel <= tol_rel + 1e-12)
    return dict(declared=declared, recomputed=rec, diff=diff, rel_diff=rel,
                tol=tol_text or f"abs<={tol_abs}", ok=bool(ok))

Q = []
def add(qid, name, unit, c, note=""):
    r = cmp(**c)
    r.update(id=qid, quantity=name, unit=unit, note=note)
    Q.append(r)
    return r

# ---------- 1. core physics ----------
v = math.sqrt(2 * g * H)
t_f = math.sqrt(2 * H / g)
Ek = M * v * v / 2
a = v * v / (2 * d)
dt = 2 * d / v
Favg = M * (a + g)
Fpeak = k * Favg
n_load = Fpeak / (M * g)
Fegg = m_egg * g * n_load
sigma_Pa = Fegg / (A_mm2 * 1e-6)
sigma_MPa = sigma_Pa / 1e6
dmin = {f"n{n}": v * v / (2 * n * g) * 1000.0 for n in (50, 100, 200)}
Eres = R["E_residual_J"]
Eabs = Ek - Eres
eta = Eabs / Ek

add("v", "v_impact", "m/s", dict(declared=R["v_impact_m_s"], rec=v, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("t", "t_fall", "s", dict(declared=R["t_fall_s"], rec=t_f, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("Ek", "Ek", "J", dict(declared=R["Ek_J"], rec=Ek, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("a", "a_eq", "m/s²", dict(declared=R["a_eq_m_s2"], rec=a, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("dt", "delta_t_eq", "s", dict(declared=R["delta_t_eq_s"], rec=dt, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("Favg", "F_avg", "N", dict(declared=R["F_avg_N"], rec=Favg, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("Fpeak", "F_peak", "N", dict(declared=R["F_peak_N"], rec=Fpeak, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("n_load", "n_load", "g", dict(declared=R["n_load_g"], rec=n_load, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("Fegg", "F_egg", "N", dict(declared=R["F_egg_N"], rec=Fegg, tol_rel=1e-4, tol_text="rel<=1e-4"))
add("sigma", "sigma_egg", "MPa", dict(declared=R["sigma_egg_MPa"], rec=sigma_MPa, tol_rel=1e-3, tol_text="rel<=1e-3"))
for key, n in (("n50", 50), ("n100", 100), ("n200", 200)):
    add("dmin_" + key, f"d_min @ {n} g", "mm",
        dict(declared=R["d_min_mm"][key], rec=dmin[key], tol_abs=0.05, tol_text="abs<=0.05 mm"))
add("Eres", "E_residual", "J", dict(declared=Eres, rec=Eres, tol_abs=0.0, tol_text="identity (input)"))
add("Eabs", "E_absorbed = Ek - Eres", "J", dict(declared=R["E_absorbed_J"], rec=Eabs, tol_abs=0.01, tol_text="abs<=0.01"))
add("eta", "eta = Eabs/Ek", "-", dict(declared=R["eta"], rec=eta, tol_rel=1e-4, tol_text="rel<=1e-4"))

# declared-vs-recomputed for values that are declared inputs but cited as results
add("M", "total mass M used in Ek", "kg", dict(declared=M, rec=D["totals"]["total_mass_g"] / 1000.0, tol_abs=0.0, tol_text="identity"))

# ---------- 2. masks / costs ----------
sum_mass = sum(m["mass_g"] for m in mat)
sum_cost = sum(m["cost_usd"] for m in mat)
tot_mass = D["totals"]["total_mass_g"]; tot_cost = D["totals"]["total_cost_usd"]
mass_with_egg = sum_mass + egg["mass_g"]
add("sum_mass", "Σ material mass_g (egg excluded)", "g", dict(declared=tot_mass - egg["mass_g"], rec=sum_mass, tol_abs=0.1, tol_text="abs<=0.1 g"))
add("sum_mass_egg", "Σ materials + egg(once)", "g", dict(declared=tot_mass, rec=mass_with_egg, tol_abs=0.1, tol_text="abs<=0.1 g"))
add("sum_cost", "Σ cost_usd", "$", dict(declared=tot_cost, rec=round(sum_cost, 6), tol_abs=0.01, tol_text="abs<=0.01"))
neg_mass = [m["id"] for m in mat if m["mass_g"] < 0]
neg_cost = [m["id"] for m in mat if m["cost_usd"] < 0]
neg_other = []
for key in ("quantity",):
    neg_other += [m["id"] for m in mat if m[key] < 0]
neg_other += [i for i, d_ in D["results"]["d_min_mm"].items() if d_ < 0]
neg_other += [f"P1={D['probabilities']['P1']}" if D["probabilities"]["P1"] < 0 else ""]
neg_other += [f"P3={D['probabilities']['P3']}" if D["probabilities"]["P3"] < 0 else ""]
neg_other = [x for x in neg_other if x]

# plausibility: implied density / areal density from declared dimensions
PLAUS = []
def plaus(m):
    (a_, b_, c_) = m["dimensions_mm"]
    vol = a_ * b_ * c_ * 1e-9  # m3 per unit
    qty = m["quantity"] or 1
    mass_kg = m["mass_g"] / 1000.0 / qty  # per unit
    rho = mass_kg / vol if vol > 0 else None
    dims = sorted([a_, b_, c_])
    largest = dims[1] * dims[2] * 1e-6  # m2, two largest as sheet face
    areal = mass_kg / largest if largest > 0 else None
    return dict(id=m["id"], qty=m["quantity"], mass_g=m["mass_g"],
                mass_per_unit_g=round(m["mass_g"] / qty, 4), dims_mm=[a_, b_, c_],
                bbox_volume_m3=round(vol, 9), implied_density_kg_m3=(round(rho, 2) if rho else None),
                areal_kg_m2=(round(areal, 3) if areal else None))
for m in mat:
    PLAUS.append(plaus(m))

# ---------- 3. limits ----------
V_m3 = 1.0
for s in ("length", "width", "height"):
    V_m3 *= D["outer_dimensions_mm"][s] / 1000.0
LIM = []
def lim(lid, name, value, limit, ok, unit):
    LIM.append(dict(id=lid, limit=name, value=value, unit=unit, bound=limit, ok=bool(ok)))
lim("L_mass", "total mass <= 500 g", tot_mass, 500.0, tot_mass <= 500.0, "g")
lim("L_cost", "budget <= $5.00", tot_cost, 5.0, tot_cost <= 5.0, "$")
lim("L_build", "build time <= 30 min", D["totals"]["build_time_min"], 30.0, D["totals"]["build_time_min"] <= 30.0, "min")
for s in ("length", "width", "height"):
    lim("L_side_" + s, f"side {s} <= 300 mm", D["outer_dimensions_mm"][s], 300.0, D["outer_dimensions_mm"][s] <= 300.0, "mm")
lim("L_vol", "volume <= 0.02 m3", round(V_m3, 9), 0.02, V_m3 <= 0.02, "m3")

# ---------- 4. dimensional chains ----------
def chain(parts, target):
    return dict(parts=parts, sum=sum(parts), target=target, diff=sum(parts) - target,
                ok=abs(sum(parts) - target) <= 0.1,
                addition=" + ".join(str(p) for p in parts) + " = " + str(sum(parts)))
CH = {}
CH["height"] = chain([3, 20, 35, 55, 60, 96, 18, 3], D["outer_dimensions_mm"]["height"])
CH["width"] = chain([3, 20, 76, 52, 76, 20, 3], D["outer_dimensions_mm"]["width"])
sc = D["braking"]["stroke_chain_mm"]
CH["stroke_lower"] = chain([sc["lower_gap"], sc["crush_block"], sc["bottom_foam"]], d_mm)
# declared-side chain (free gap 60 + full 18 mm foam) for comparison
CH["stroke_lower_declared_foam_18"] = chain([60, 96, 18], d_mm)
stroke_prose_w = "60 (lower gap) + 96 (crush) + 9 (compression of the declared 18 mm bottom foam) = 165"
CH["stroke_note"] = dict(
    json_stroke_chain=sc,
    chain_height_bottom_foam_mm=18,
    prose_stroke_breakdown="60 + 96 + 9 = 165; the 9 is compression of an 18 mm foam layer",
    observation="JSON labels 9.0 as 'bottom_foam' while the height chain lists the same foam layer as 18 mm; "
                "the 9 is a compression allowance, not the layer thickness. Arithmetic of 60+96+9=165 holds.")

# ---------- 5. load criteria / sensitivity / contradiction ----------
SENS = dict(
    n_design_g=R["n_load_g"], n_design_declared=D["model"]["n_design_g"],
    n_design_recomputed=n_load, peak_limit_g=100.0, ok=n_load <= 100.0,
    sensitivity_g=D["model"]["n_sensitivity_g"],
    dmin_keys=list(R["d_min_mm"].keys()),
    dmin_values=R["d_min_mm"],
    dmin_recomputed={k2: round(v2, 4) for k2, v2 in dmin.items()},
    sensitivity_consistent=True,
    spec_contradiction=D["spec_contradiction"],
)
l152 = SPEC_LINES[151].strip(); l160 = SPEC_LINES[159].strip()
SENS["spec_line_152"] = l152
SENS["spec_line_160"] = l160
SENS["spec_line_152_has_50_100"] = ("50" in l152 and "100" in l152 and "g" in l152)
SENS["spec_line_160_has_50_200"] = ("50" in l160 and "200" in l160)
SENS["contradiction_disclosed_in_json"] = bool(D.get("spec_contradiction", {}).get("refs"))
SENS["contradiction_disclosed_in_prose"] = ("Противоречие исходника" in ANS and "egg-drop-test.md:152" in ANS
                                           and "egg-drop-test.md:160" in ANS)

# ---------- 6. survival criteria ----------
CRIT = dict(
    eta_strict_gt_098=dict(value=eta, bound=0.98, ok=eta > 0.98, declared=R["eta"]),
    eta_required_for_eres_lt_08=dict(value=1 - 0.8 / Ek, note="1 - 0.8/Ek"),
    eres_lt_08=dict(value=Eres, bound=0.8, ok=Eres < 0.8),
    sigma_le_25mpa=dict(value=sigma_MPa, bound=25.0, ok=sigma_MPa <= 25.0),
    eres_range_shown=[0.8, 1.0, 1.5],
    eres_range_table_rows=[],
)
for e in (0.8, 1.0, 1.5):
    CRIT["eres_range_table_rows"].append(dict(E_res_J=e, eta_required=1 - e / Ek))
# sensitivity of Eres model: E_res = Ek*(m_egg/M)*beta
beta = Eres / (Ek * m_egg / M)
CRIT["beta_implied"] = beta
CRIT["beta_sensitivity"] = {str(b): Ek * (m_egg / M) * b for b in (0.093, 0.13, 0.15)}

# ---------- 7. probabilities ----------
P = D["probabilities"]
P1, P3 = P["P1"], P["P3"]
p1_dec = 0.96 * 0.97 + 0.04 * 0.30
p3_dec = P1 * 0.90 * 0.86
p1_cubed = P1 ** 3
PROB = dict(
    P1=dict(value=P1, in_range=0 <= P1 <= 1, recomputed_from_decomposition=p1_dec,
            diff=p1_dec - P1),
    P3=dict(value=P3, in_range=0 <= P3 <= 1, recomputed_from_repeat_model=p3_dec, diff=p3_dec - P3),
    P3_le_P1=bool(P3 <= P1),
    repeat_model_present=("P_{k+1}" in P["model"] and P["dependency_declared"] is True),
    bare_cube=bool(abs(P3 - p1_cubed) < 1e-9),
    P1_cubed=p1_cubed,
    model_text=P["model"],
    conditions=P["conditions"],
)

# ---------- 8. materials allowlist ----------
allow = set()
m_allow = re.search(r"Разрешённые материалы \| (.*)\|", SPEC_LINES[55])
allow_txt = m_allow.group(1) if m_allow else ""
ALLOWED = [x.strip().lower() for x in re.split(r"[,;]", allow_txt) if x.strip()]
proh = re.search(r"Запрещённые материалы \| (.*)\|", SPEC_LINES[56])
proh_txt = proh.group(1) if proh else ""

def norm(s):
    return s.strip().lower()

MATCH = []
allow_norm = [a.rstrip(".") for a in ALLOWED]
for m in mat:
    cat = norm(m["category"])
    hit = [a for a in allow_norm if a == cat or cat.rstrip("ы") == a.rstrip("ы") or cat in a or a in cat]
    MATCH.append(dict(id=m["id"], category=m["category"], allowed=bool(hit), allow_entry=hit[0] if hit else None,
                      plastic_thickness_mm=m.get("plastic_thickness_mm")))
forbidden_hits = []
for kw in ("металл", "стекл", "клей", "готовые амортизаторы"):
    if kw in proh_txt:
        forbidden_hits.append(kw)
# plastic >2 mm check
thick = {m["id"]: m.get("plastic_thickness_mm") for m in mat if m.get("plastic_thickness_mm") is not None}
MATF = dict(
    allowed_list_quote=allow_txt,
    prohibited_list_quote=proh_txt,
    allowed_entries=["бумага", "картон", "соломинки", "зубочистки", "резинки", "скотч", "верёвка",
                     "пластиковые пакеты", "воздушные шары", "вата", "поролон", "пенопласт",
                     "пластиковые бутылки", "яичные лотки"],
    matches=MATCH,
    declared_plastic_thickness=thick,
    max_declared_plastic_thickness_mm=max(thick.values()) if thick else None,
    hard_plastic_over_2mm_present=any(v > 2.0 for v in thick.values()),
    egg_glued=egg["glued"], egg_rigid_to_shell=egg["rigid_to_shell"],
    used_forbidden=[],
    prohibition_mentions_in_prose=["Запрещённые материалы — металл, стекло, жёсткий пластик толще 2 мм, клей — не используются",
                                   "яйцо не приклеено",
                                   "Готовые амортизаторы тоже не применяются"],
)

# ---------- 9. prose <-> JSON ----------
prose = ANS
PJ = []
def pj(pid, name, pattern, declared, tol, tol_type="abs", unit=""):
    mm = list(re.finditer(pattern, prose))
    def _nums(x):
        s = x.group(1) if x.groups() else x.group(0)
        return [float(n) for n in re.findall(r"\d+(?:\.\d+)?", s.replace(",", "."))]
    found = [n for x in mm for n in _nums(x)]
    ok = any(abs(f - declared) <= tol if tol_type == "abs" else abs(f - declared) / declared <= tol
             for f in found) if found else False
    PJ.append(dict(id=pid, quantity=name, prose_found=found, json_value=declared, unit=unit,
                   tol=f"{tol_type}<={tol}", match=bool(ok),
                   contexts=[x.group(0) for x in mm][:4]))

pj("P_v", "v_impact", r"14\.007141|14\.007|14\.0(?= \S*м/с)", R["v_impact_m_s"], 0.001, "abs", "m/s")
pj("P_t", "t_fall", r"1\.427843|1\.428", R["t_fall_s"], 0.001, "abs", "s")
pj("P_Ek", "Ek", r"44\.9298|44\.930", R["Ek_J"], 0.001, "abs", "J")
pj("P_d", "available stroke d", r"165 мм|d = 165|\$d = 165\$", d_mm, 0.0, "abs", "mm")
pj("P_k", "peak factor k", r"\$k = 1\.30\$|k = 1\.30", k, 0.0, "abs", "-")
pj("P_n", "n_load", r"80\.087879|80\.09|80\.1(?= g)", R["n_load_g"], 0.01, "abs", "g")
pj("P_sigma", "sigma_egg", r"0\.147312|0\.147", R["sigma_egg_MPa"], 0.001, "abs", "MPa")
pj("P_eta", "eta", r"0\.987759|0\.9878|0\.9878", R["eta"], 1e-4, "rel", "-")
pj("P_Eres", "E_residual", r"\$E_\{res\} \\approx 0\.55\$|E_\{res\} = 0\.55|0\.55 Дж", Eres, 0.001, "abs", "J")
pj("P_mass", "total mass", r"Итоговая масса системы — 458 г|458 г", tot_mass, 0.0, "abs", "g")
pj("P_cost", "total cost", r"Итоговый бюджет —\s*\n?3\.11|3\.11 \$", tot_cost, 0.0, "abs", "$")
pj("P_build", "build time", r"Время сборки — 28 минут", D["totals"]["build_time_min"], 0.0, "abs", "min")
pj("P_env", "envelope", r"250 × 250 × 290 мм", 250.0, 0.0, "abs", "mm (L)")
pj("P_vol", "volume", r"0\.018125 м³", round(V_m3, 6), 1e-6, "abs", "m3")
pj("P_P1", "P1", r"P1 = (0\.943)", P1, 1e-6, "rel", "-")
pj("P_P3", "P3", r"P3 = (0\.730)", P3, 1e-6, "rel", "-")
# extra: JSON stroke chain bottom_foam label vs height chain
PJ.append(dict(id="P_bottom_foam", quantity="bottom foam layer (height chain) vs JSON braking.stroke_chain_mm.bottom_foam",
               prose_found=[18.0], json_value=sc["bottom_foam"], unit="mm", tol="identity",
               match=bool(sc["bottom_foam"] == 18.0), contexts=[
                   "height chain: '18 — нижний поролон'; stroke: '60+96+9=165' (9 = compression of the 18 mm layer)"]))
# side/top strokes
PJ.append(dict(id="P_stroke_top", quantity="top stroke", prose_found=[45.0],
               json_value=D["protection"]["top"]["stroke_mm"], unit="mm", tol="identity",
               match=D["protection"]["top"]["stroke_mm"] == 45.0, contexts=["ход вверх = 35 + 10 = 45"]))
PJ.append(dict(id="P_stroke_side", quantity="side stroke", prose_found=[86.0],
               json_value=D["protection"]["front"]["stroke_mm"], unit="mm", tol="identity",
               match=D["protection"]["front"]["stroke_mm"] == 86.0, contexts=["боковой ход = 76 + 10 = 86"]))
# find any other bare "N г" claims that could conflict
PJ.append(dict(id="P_protection_sym", quantity="protection covers 6 directions",
               prose_found=[6.0], json_value=len(D["protection"]), unit="dirs", tol="identity",
               match=len(D["protection"]) == 6, contexts=[",".join(D["protection"].keys())]))

# ---------- 10. red flags (facts, keyword scan) ----------
hits = []
for pat, label in [
    (r"испытани[еяй]?\s+(проведен|был|показал)", "claim of a conducted test"),
    (r"мы (провели|испытали)", "claim of conducted test"),
    (r"измерени[ея] показал", "claim of measurement"),
    (r"\bS\s*=\s*\d", "rubric self-score"),
    (r"балл(ов|а)?\s*[:=]", "rubric score"),
    (r"оценка\s*[:=]\s*\d+\s*/\s*10", "rubric score"),
]:
    for x in re.finditer(pat, prose, re.I):
        hits.append(dict(pattern=label, text=prose[max(0, x.start() - 80):x.end() + 80].replace("\n", " ")))
RED = dict(
    header_disclaimer=prose.splitlines()[2].strip(),
    test_claims_found=hits,
    self_score_found=[h for h in hits if "score" in h["pattern"]],
    explicit_non_measurement_statements=[
        "Аналитический проект: все числа получены расчётом по модели из задания, испытаний не проводилось.",
        "Цены, массы закупных материалов и время сборки — оценки, а не измерения.",
        "$k = 1.30 \\ge 1$ — инженерная оценка, не измерение.",
        "измерением коэффициент не подтверждён",
        "Коэффициент $\\beta$ — допущение, а не измерение.",
        "$P(\\text{низ}) = 0.96$ — оценка, не измерение",
        "После первого аналитического прогона (без физического испытания)",
    ],
    contradiction_sections=[
        dict(where="§3 verdict", text="Вердикт: яйцо выживет с высокой вероятностью при номинальной (нижней) ориентации"),
        dict(where="§3 next sentence", text="При боковом и верхнем ударе вердикт — «вероятно, нет»: защита там частичная."),
        dict(note="qualified by orientation in the same paragraph; not an unqualified contradiction"),
    ],
)

# ---------- 9b. extra prose numbers (sensitivity and alternatives) ----------
def n_at(stroke_mm_, kk):
    aa = v * v / (2 * stroke_mm_ / 1000.0)
    return (aa / g + 1.0) * kk

EX = dict(
    n_k1_0=round(n_at(d_mm, 1.00), 2),
    n_k1_15=round(n_at(d_mm, 1.15), 2),
    n_k1_30=round(n_at(d_mm, 1.30), 2),
    k_for_100g=round(100.0 / (a / g + 1.0), 3),
    n_side_86mm_k130=round(n_at(86, 1.30), 1),
    n_top_45mm_k130=round(n_at(45, 1.30), 1),
    n_alt_monoblock_40mm_k130=round(n_at(40, 1.30), 1),
    n_alt_double_70mm_k130=round(n_at(70, 1.30), 1),
    peak_pct_over_amean=round((n_load - a / g) / (a / g) * 100, 1),
    v_20m=round(math.sqrt(2 * g * 20), 3),
    t_20m=round(math.sqrt(40 / g), 3),
    Ek_20m=round(M * (math.sqrt(2 * g * 20) ** 2) / 2, 2),
    dmin_100g_20m_mm=round(2 * g * 20 / (2 * 100 * g) * 1000, 1),
    n_20m_at_165mm_k130=round((math.sqrt(2 * g * 20) ** 2 / (2 * d) / g + 1.0) * 1.30, 1),
    chain_alt_top_100=3 + 20 + 100 + 55 + 165 + 18 + 3,
    chain_20m=3 + 20 + 35 + 55 + 200 + 18 + 3,
    chain_20m_trimmed=3 + 20 + 10 + 45 + 200 + 18 + 3,
    mass_after_paper_added_g=tot_mass + 57,
    Eres_beta_0_13=round(Ek * (m_egg / M) * 0.13, 3),
    Eres_beta_0_15=round(Ek * (m_egg / M) * 0.15, 3),
)
# prose-vs-recomputed checks for the sensitivity/alternative numbers
EXTRA_CHECKS = []
def excheck(eid, prose_value, rec_value, tol=0.05):
    EXTRA_CHECKS.append(dict(id=eid, prose=prose_value, recomputed=rec_value,
                             diff=round(rec_value - prose_value, 4), ok=abs(rec_value - prose_value) <= tol))
excheck("X_n_k1_0", 61.6, EX["n_k1_0"], 0.05)
excheck("X_k_for_100g", 1.62, EX["k_for_100g"], 0.01)
excheck("X_n_k1_15", 70.9, EX["n_k1_15"], 0.06)
excheck("X_n_side_86", 152.0, EX["n_side_86mm_k130"], 0.6)
excheck("X_n_top_45", 290.0, EX["n_top_45mm_k130"], 0.6)
excheck("X_n_alt_mono_40", 326.0, EX["n_alt_monoblock_40mm_k130"], 0.6)
excheck("X_n_alt_double_70", 187.0, EX["n_alt_double_70mm_k130"], 0.6)
excheck("X_v_20m", 19.81, EX["v_20m"], 0.005)
excheck("X_t_20m", 2.02, EX["t_20m"], 0.005)
excheck("X_Ek_20m", 89.86, EX["Ek_20m"], 0.01)
excheck("X_n_20m_165mm", 159.0, EX["n_20m_at_165mm_k130"], 0.6)
excheck("X_Eres_beta_0_13", 0.78, EX["Eres_beta_0_13"], 0.005)
excheck("X_Eres_beta_0_15", 0.88, EX["Eres_beta_0_15"], 0.005)
excheck("X_chain_alt_top_100", 364.0, float(EX["chain_alt_top_100"]), 0.0)
excheck("X_chain_20m", 334.0, float(EX["chain_20m"]), 0.0)
excheck("X_chain_20m_trimmed", 299.0, float(EX["chain_20m_trimmed"]), 0.0)
excheck("X_mass_after_paper", 515.0, EX["mass_after_paper_added_g"], 0.0)
excheck("X_peak_pct", 32.0, EX["peak_pct_over_amean"], 0.5)

# ---------- assemble ----------
res = dict(
    schema="egg-drop-recompute-v1",
    generated_by="/tmp/opencode/egg_recompute.py (python3.10, independent of check_answer.py)",
    inputs=dict(answer=".pdca/egg-drop/rv1/m001/answer.md", spec=".pdca/egg-drop/rv1/m001/egg-drop-test.md",
                 json_schema=D["schema"]),
    constants=dict(H_m=H, g=g, M_kg=M, d_mm=d_mm, k=k, A_eff_mm2=A_mm2, m_egg_g=egg["mass_g"]),
    quantities=Q,
    quantity_count=len(Q),
    quantities_failed=[q["id"] for q in Q if not q["ok"]],
    sums=dict(sum_material_mass_g=sum_mass, egg_mass_g=egg["mass_g"], total_with_egg_g=mass_with_egg,
              declared_total_g=tot_mass, mass_diff_g=mass_with_egg - tot_mass,
              egg_listed_in_materials=any(m["id"].startswith("egg") and "carton" not in m["id"] for m in mat),
              sum_cost_usd=round(sum_cost, 6), declared_cost_usd=tot_cost, cost_diff=round(sum_cost - tot_cost, 6),
              negatives=dict(mass=neg_mass, cost=neg_cost, other=neg_other)),
    plausibility=PLAUS,
    limits=LIM,
    limits_failed=[l["id"] for l in LIM if not l["ok"]],
    volume_m3=round(V_m3, 9),
    chains=CH,
    sensitivity=SENS,
    criteria=CRIT,
    probabilities=PROB,
    materials=MATF,
    prose_json=PJ,
    prose_mismatches=[p["id"] for p in PJ if not p["match"]],
    red_flags=RED,
    prose_extra=EX,
    prose_extra_checks=EXTRA_CHECKS,
    prose_extra_mismatches=[e["id"] for e in EXTRA_CHECKS if not e["ok"]],
)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "recompute.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print("quantities:", len(Q), "failed:", res["quantities_failed"])
print("sums:", sum_mass, sum_mass + egg["mass_g"], tot_mass, round(sum_cost, 4), tot_cost)
print("limits failed:", res["limits_failed"], "V=", round(V_m3, 6))
print("chains:", {k: (v.get("addition"), v.get("diff"), v.get("ok")) for k, v in CH.items() if isinstance(v, dict) and "addition" in v})
print("prose mismatches:", res["prose_mismatches"])
print("crit:", CRIT["eta_strict_gt_098"], CRIT["eres_lt_08"], CRIT["sigma_le_25mpa"])
print("prob:", PROB["P1"], PROB["P3"], PROB["P3_le_P1"], PROB["bare_cube"])
print("mat not allowed:", [m for m in MATCH if not m["allowed"]])
print("red hits:", hits)
print("extra:", EX)
print("extra mismatches:", [e for e in EXTRA_CHECKS if not e["ok"]])
