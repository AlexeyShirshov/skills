#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify.py -- egg-drop (scenario A, 10 m) evidence checker, revision rv1.

Frozen interface (validated at PLAN gate 1):

    python3 verify.py --repo <abs> [--document <path>] \
        --check {probe|selftest|structure|physics|constraints|content} --log <path>

Exit codes: 0 = every selected case passed, 1 = at least one case failed (or a
deliberate corruption slipped through), 2 = usage error.

Python 3.10 standard library only.  Nothing here is a measurement: every number
is either read from the document's machine-readable model block or recomputed
from that block's inputs.
"""

import argparse
import datetime
import json
import math
import os
import re
import sys

G = 9.81
RHO_AIR = 1.225

REQUIRED_H2 = [
    "1. Концепция",
    "2. Спецификация",
    "3. Физические расчёты",
    "4. Оценка надёжности",
    "5. Альтернативы",
    "6. Итерации",
]

# The seven quantities section 3 must expose as labelled rows.
PHYS_TOKENS = ["v_impact", "E_k", "Δt", "F_avg", "F_peak", "n", "η"]

FORBIDDEN = [
    ("металл", r"металл"),
    ("сталь", r"\bстал[ьи]\b"),
    ("алюминий", r"алюмини"),
    ("железо", r"желез"),
    ("стекло", r"\bстекл"),
    ("клей", r"\bкле[йя]\b|суперклей|эпоксид"),
    ("готовый амортизатор", r"амортизатор"),
]

ALLOWED = [
    "бумаг", "картон", "соломинк", "зубочист", "резинк", "скотч", "верёвк",
    "веревк", "шпагат", "пакет", "шар", "ват", "поролон", "пенопласт",
    "бутылк", "лоток", "яйцо",
]

TBD = re.compile(r"\b(TBD|TODO|TBA|XXX|FIXME)\b|заполнит|placeholder", re.IGNORECASE)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def utcnow():
    """UTC with millisecond resolution so that two runs of the same second
    cannot be confused with one run repeated (attempt-1 defect AC12)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)


def res(rid, ok, expected, observed, detail=""):
    return {
        "id": rid,
        "ok": bool(ok),
        "expected": expected,
        "observed": observed,
        "detail": detail,
    }


def fnum(x, nd=4):
    if x is None:
        return None
    v = round(float(x), nd)
    if abs(v) < 10 ** (-nd):
        return 0.0
    return v


def rel(a, b):
    """Relative deviation of a from b (b may be 0)."""
    if b == 0:
        return abs(a - b)
    return abs(a - b) / abs(b)


def cell_num(c):
    """Parse a numeric table cell.  Returns None if the cell is not a plain number."""
    if c is None:
        return None
    s = c.replace("`", "").replace("\u00a0", "").replace(" ", "")
    s = s.replace("−", "-").replace("\u2212", "-")
    s = s.replace(",", ".")
    if s in ("", "-", "—", "–", "n/a"):
        return None
    if not re.fullmatch(r"[-+]?\d*\.?\d+", s):
        return None
    return float(s)


def parse_tables(md):
    lines = md.splitlines()
    tables = []
    i = 0
    while i < len(lines) - 1:
        ln = lines[i].strip()
        nxt = lines[i + 1].strip()
        if ln.startswith("|") and re.fullmatch(r"\|[\s:|\-]+\|?", nxt) and "-" in nxt:
            header = split_row(ln)
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(split_row(lines[j].strip()))
                j += 1
            tables.append({"header": header, "rows": rows, "line": i + 1})
            i = j
        else:
            i += 1
    return tables


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def find_table(tables, *needles):
    for t in tables:
        hdr = " ".join(t["header"]).lower()
        if all(n.lower() in hdr for n in needles):
            return t
    return None


def col_index(table, *needles):
    for i, h in enumerate(table["header"]):
        hl = h.lower()
        for n in needles:
            if n.lower() in hl:
                return i
    return None


def fenced_blocks(md):
    return re.findall(r"```([A-Za-z0-9_-]*)\n(.*?)```", md, flags=re.DOTALL)


def prose_only(md):
    """Text with fenced blocks, inline code and LaTeX removed."""
    out = re.sub(r"```.*?```", " ", md, flags=re.DOTALL)
    out = re.sub(r"\$[^$]*\$", " ", out)
    out = re.sub(r"`[^`]*`", " ", out)
    out = re.sub(r"https?://\S+", " ", out)
    return out


def section(md, num):
    """Body of '## <num>.' section (up to the next H2)."""
    pat = re.compile(r"^##\s+" + re.escape(str(num)) + r"\.", re.MULTILINE)
    m = pat.search(md)
    if not m:
        return ""
    rest = md[m.end():]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def subsection(md, num, sub):
    body = section(md, num)
    m = re.search(r"^###\s+" + re.escape(sub) + r"\.", body, re.MULTILINE)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"^#{2,3}\s+", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def h2_list(md):
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", md, re.MULTILINE)]


def model_block(md):
    """First ```json fence that parses and carries a 'model' key."""
    for lang, body in fenced_blocks(md):
        if lang.strip().lower() not in ("json", "jsonc", ""):
            continue
        try:
            obj = json.loads(body)
        except Exception:
            continue
        if isinstance(obj, dict) and "model" in obj:
            return obj, body, None
        return None, body, "json block without a 'model' key"
    return None, None, "no parseable ```json block"


def cyr_lat_ratio(md):
    txt = prose_only(md)
    cyr = len(re.findall(r"[А-Яа-яЁё]", txt))
    lat = len(re.findall(r"[A-Za-z]", txt))
    tot = cyr + lat
    return (cyr / tot if tot else 0.0), cyr, lat


def labelled_rows(md):
    """Map token -> numeric value from the section-3 'required quantities' table."""
    out = {}
    for t in parse_tables(md):
        first = t["header"][0].lower()
        if "метка" not in first and "label" not in first:
            continue
        for row in t["rows"]:
            if not row:
                continue
            tok = row[0].replace("`", "").strip()
            if tok in PHYS_TOKENS and tok not in out:
                val = None
                for c in row[1:]:
                    v = cell_num(c)
                    if v is not None:
                        val = v
                        break
                out[tok] = val
    return out


# --------------------------------------------------------------------------
# physics core -- one model, used by probe, physics and selftest
# --------------------------------------------------------------------------
def phys(H_mm, m_total_g, s_mm, k_peak, m_egg_g, delta_egg_mm, n_crit_g):
    """Constant-plateau model including the work of gravity over the usable stroke.

    The CG descends by s while the stack crushes, so the stack must absorb
    E_tot = E_k + m g s.  The net upward deceleration is a = v^2/(2s) and the
    force the stack applies to the mass is m(a + g).  Momentum then reads
    (F_avg - m g) dt = m v, which is why dt = 2s/v still holds.
    """
    H = H_mm / 1000.0
    m = m_total_g / 1000.0
    s = s_mm / 1000.0
    me = m_egg_g / 1000.0
    de = delta_egg_mm / 1000.0
    v = math.sqrt(2.0 * G * H)
    t_fall = math.sqrt(2.0 * H / G)
    Ek = 0.5 * m * v * v
    dUg = m * G * s
    E_tot = Ek + dUg
    a_avg = v * v / (2.0 * s) + G
    n_avg = a_avg / G
    F_avg = m * a_avg
    dt = 2.0 * s / v
    F_peak = k_peak * F_avg
    a_peak = k_peak * a_avg
    n_peak = a_peak / G
    F_egg = me * a_peak
    E_egg = F_egg * de
    eta = 1.0 - E_egg / Ek
    dx_min = v * v / (2.0 * n_crit_g * G)
    return {
        "v_impact_m_s": v,
        "t_fall_s": t_fall,
        "E_k_J": Ek,
        "dU_g_J": dUg,
        "E_tot_J": E_tot,
        "dUg_share": dUg / Ek if Ek else 0.0,
        "a_avg_m_s2": a_avg,
        "n_avg_g": n_avg,
        "F_avg_N": F_avg,
        "dt_s": dt,
        "k_peak": k_peak,
        "F_peak_N": F_peak,
        "a_peak_m_s2": a_peak,
        "n_peak_g": n_peak,
        "F_egg_N": F_egg,
        "n_egg_g": n_peak,
        "E_egg_J": E_egg,
        "eta": eta,
        "dx_min_mm": dx_min * 1000.0,
        "momentum_check_dt_s": m * v / (F_avg - m * G),
        "energy_check_J": F_avg * s,
    }


# --------------------------------------------------------------------------
# embedded fixture builder (selftest base) -- in memory only
# --------------------------------------------------------------------------
def build_fixture(**ov):
    p = {
        "H_mm": 10000,
        "m_total_g": 436,
        "m_egg_g": 65,
        "s_mm": 159.6,
        "k": 1.5,
        "delta_egg_mm": 10,
        "n_crit_g": 100,
        "P1": 0.75,
        "p2": 0.15,
        "p3": 0.05,
        "lang": "ru",
        "drop_heading": None,
        "drop_token": None,
        "bad_material": None,
        "mass_total": None,
        "budget": 3.17,
        "favg_mult": 1.0,
        "wall_panel": 5.0,
        "wall_table": None,
        "lat_zero": False,
        "merge_bullets": False,
        "lid_oversize": False,
    }
    p.update(ov)
    m_total = p["mass_total"] if p["mass_total"] is not None else p["m_total_g"]
    o = phys(p["H_mm"], p["m_total_g"], p["s_mm"], p["k"], p["m_egg_g"],
             p["delta_egg_mm"], p["n_crit_g"])
    o["F_avg_N"] *= p["favg_mult"]
    o20 = phys(20000, p["m_total_g"], p["s_mm"], p["k"], p["m_egg_g"],
               p["delta_egg_mm"], p["n_crit_g"])

    w = float(p["wall_panel"])
    wtab = float(p["wall_table"]) if p["wall_table"] is not None else w
    box = [250.0, 250.0, 300.0]          # X, Y, H
    cavity = [box[0] - 2 * w, box[1] - 2 * w, box[2] - 2 * w]
    bed = [90.0, 80.0, 60.0]
    bottom = {"layers": 14, "pitch_mm": 15.0, "residual_mm": 3.6}
    top = {"layers": 5, "pitch_mm": 4.0, "residual_mm": 0.96}
    lat_x = {"count": 2, "layers": 5, "pitch_mm": 15.0, "residual_mm": 3.6,
             "depth_mm": (cavity[0] - bed[0]) / 2.0}
    lat_y = {"count": 2, "layers": 5, "pitch_mm": 16.0, "residual_mm": 3.84,
             "depth_mm": (cavity[1] - bed[1]) / 2.0}
    if p["lat_zero"]:
        lat_x = {"count": 2, "layers": 1, "pitch_mm": 3.6, "residual_mm": 3.6,
                 "depth_mm": (cavity[0] - bed[0]) / 2.0}
    for d in (bottom, top, lat_x, lat_y):
        d["nominal_mm"] = d["layers"] * d["pitch_mm"]
        d["usable_mm"] = d["layers"] * (d["pitch_mm"] - d["residual_mm"])

    vol = box[0] * box[1] * box[2]
    bom = [
        ("Яйцо C1", "яйцо куриное", 65, 0.25, "полезная нагрузка"),
        ("Боковые панели, 4 шт (5 мм)", "гофрокартон", 130, 0.60, "силовая оболочка"),
        ("Дно (5 мм)", "гофрокартон", 30, 0.15, "оболочка"),
        ("Крышка (5 мм)", "гофрокартон", 30, 0.15, "оболочка"),
        ("Труба-направляющая", "бумага", 20, 0.10, "удерживает пакеты"),
        ("Нижний аккордеон, 14 слоёв", "бумага", 45, 0.20, "рабочий ход"),
        ("Верхний аккордеон, 5 слоёв", "бумага", 13, 0.06, "ход при отскоке"),
        ("Боковые аккордеоны, 4 шт", "бумага", 16, 0.16, "радиальный ход"),
        ("Ложе: лоток и вата", "яичный лоток, вата", 20, 0.20, "распределение силы"),
        ("Резинки, 6 шт", "резинка", 8, 0.30, "фиксация яйца"),
        ("Верёвка (шпагат) 1.5 м", "верёвка", 4, 0.15, "фиксация яйца"),
        ("Скотч 4 м", "скотч", 6, 0.40, "соединения"),
        ("Соломинки, 8 шт", "соломинка", 5, 0.10, "направляющие"),
        ("Уголки-усилители, 8 шт", "картон", 12, 0.05, "жёсткость углов"),
        ("Пенопласт, 4 шт", "пенопласт", 8, 0.10, "углы ложа"),
        ("Резерв", "резерв", 24, 0.20, "запас"),
    ]
    if p["bad_material"] is not None:
        bom[4] = (bom[4][0], p["bad_material"], bom[4][2], bom[4][3], bom[4][4])
    mass_sum = sum(b[2] for b in bom)
    cost_sum = round(sum(b[3] for b in bom), 3)

    if p["lang"] == "ru":
        t_bom = "Полный список материалов с массами, ценами и ролью каждого элемента."
        t_dim = "Габариты всех элементов в мм."
        t_attach = ("Яйцо не приклеено: оно посажено в ложе и удерживается шестью "
                    "резинками и верёвкой, клей не используется.")
        t_conc = ("Конструкция «Бумажный кокон» гасит энергию в ступени: "
                  "пластическая работа оболочки, рабочий ход аккордеона, "
                  "распределённое ложе.")
        t_verdict = "Вердикт: вероятно, с условиями, перечисленными ниже."
        t_rel = "Оценка вероятности выживания при одном дропе."
        t_3 = "Вероятность выживания при трёх дропах подряд без ремонта."
        t_alt = ("Альтернатива B — парашют и крэш-контейнер; альтернатива C — "
                 "резиновая подвеска и мягкая оболочка.")
        t_imp = "Что улучшить после первого теста: измеримые изменения."
        t_20 = ("При 20 000 мм скорость 19.81 м/с, энергия 85.54 Дж, требуемый ход "
                "300 мм, что больше 300 мм корпуса, поэтому нужен парашют.")
        t_weak = "Слабые места конструкции перечислены ниже."
        t_fail = "Что может пойти не так — перечислено ниже."
    else:
        t_bom = "Full bill of materials with masses, prices and the role of each item."
        t_dim = "Dimensions of every element in millimetres."
        t_attach = ("The egg is not glued: it sits in the bed and is held by six "
                    "rubber bands and a rope, no glue is used.")
        t_conc = ("The Paper Cocoon design absorbs energy in stages: plastic "
                  "work of the shell, the accordion stroke, the distributed bed.")
        t_verdict = "Verdict: probably, with the conditions listed below."
        t_rel = "Estimated probability of survival for one drop."
        t_3 = "Probability of survival for three consecutive drops without repair."
        t_alt = ("Alternative B is a parachute and crush container; alternative C is "
                 "a rubber band suspension and soft shell.")
        t_imp = "What to improve after the first test: measurable changes."
        t_20 = ("At 20000 mm the speed is 19.81 m/s, the energy 85.54 J, the required "
                "stroke 300 mm, more than the 300 mm body, so a parachute is needed.")
        t_weak = "The weak points of the design are listed below."
        t_fail = "What can go wrong is listed below."

    def h(i):
        if p["drop_heading"] == i:
            return ""
        return "## " + REQUIRED_H2[i] + "\n"

    rows7 = [
        ("v_impact", o["v_impact_m_s"], "м/с"),
        ("E_k", o["E_k_J"], "Дж"),
        ("Δt", o["dt_s"], "с"),
        ("F_avg", o["F_avg_N"], "Н"),
        ("F_peak", o["F_peak_N"], "Н"),
        ("n", o["n_peak_g"], "g"),
        ("η", o["eta"], "—"),
    ]
    rows7 = [r for r in rows7 if r[0] != p["drop_token"]]
    t7 = ["| Метка | Величина | Значение | Единица |", "|---|---|---|---|"]
    names = {"v_impact": "Скорость удара", "E_k": "Кинетическая энергия",
             "Δt": "Время торможения", "F_avg": "Средняя сила",
             "F_peak": "Пиковая сила", "n": "Пиковая перегрузка",
             "η": "Доля поглощённой энергии"}
    for tok, val, unit in rows7:
        t7.append("| `%s` | %s | %.4f | %s |" % (tok, names[tok], val, unit))
    t7 = "\n".join(t7)

    bom_md = ["| Позиция | Материал | Масса, г | Стоимость, $ | Роль |", "|---|---|---|---|---|"]
    for b in bom:
        bom_md.append("| %s | %s | %d | %.2f | %s |" % b)
    bom_md = "\n".join(bom_md)

    def f1(x):
        return ("%.1f" % x).rstrip("0").rstrip(".")

    lid_x = 250.0 if p["lid_oversize"] else cavity[0]
    lid_y = 250.0 if p["lid_oversize"] else cavity[1]
    dims_md = [
        "| Элемент | X, мм | Y, мм | Высота Z, мм |",
        "|---|---|---|---|",
        "| Корпус, габарит внешний | %s | %s | %s |" % tuple(f1(v) for v in box),
        "| Боковая панель X, 2 шт (толщина %s) | 250 | %s | 300 |" % (f1(wtab), f1(wtab)),
        "| Боковая панель Y, 2 шт (толщина %s) | %s | %s | 300 |" % (f1(wtab), f1(cavity[0]), f1(wtab)),
        "| Дно, вставное | %s | %s | %s |" % (f1(lid_x), f1(lid_y), f1(w)),
        "| Крышка, вставная | %s | %s | %s |" % (f1(lid_x), f1(lid_y), f1(w)),
        "| Полость внутренняя | %s | %s | %s |" % tuple(f1(v) for v in cavity),
        "| Нижний аккордеон | 200 | 200 | %s |" % f1(bottom["nominal_mm"]),
        "| Верхний аккордеон | 200 | 200 | %s |" % f1(top["nominal_mm"]),
        "| Боковой аккордеон X, 2 шт | %s | 80 | 60 |" % f1(lat_x["nominal_mm"]),
        "| Боковой аккордеон Y, 2 шт | 90 | %s | 60 |" % f1(lat_y["nominal_mm"]),
        "| Ложе | 90 | 80 | 60 |",
    ]
    dims_md = "\n".join(dims_md)

    asm_md = [
        "| Этап | Время, мин |",
        "|---|---|",
        "| Разметка и раскрой | 5 |",
        "| Складывание аккордеона | 7 |",
        "| Сборка корпуса | 4 |",
        "| Укладка ложа | 4 |",
        "| Установка яйца | 3 |",
        "| Контроль и маркировка | 2 |",
    ]
    asm_md = "\n".join(asm_md)

    model = {
        "model": "egg-drop",
        "revision": 1,
        "units": {"length": "mm", "mass": "g", "energy": "J", "force": "N"},
        "inputs": {
            "H_mm": p["H_mm"],
            "H2_mm": 20000,
            "g_m_s2": G,
            "m_egg_g": p["m_egg_g"],
            "m_total_g": m_total,
            "m_worst_g": 500,
            "A_contact_mm2": 1000,
            "E_crit_J": 1.0,
            "n_crit_g": p["n_crit_g"],
            "n_crit_range_g": [50, 200],
            "n_crit_strict_range_g": [50, 100],
            "box_H_mm": box[2],
            "box_X_mm": box[0],
            "box_Y_mm": box[1],
            "wall_panel_mm": w,
            "wall_total_mm": 2 * w,
            "cavity_H_mm": cavity[2],
            "cavity_X_mm": cavity[0],
            "cavity_Y_mm": cavity[1],
            "bed_X_mm": bed[0],
            "bed_Y_mm": bed[1],
            "bed_H_mm": bed[2],
            "top_stack_mm": top["nominal_mm"],
            "s_mm": p["s_mm"],
            "bottom_stack": bottom,
            "top_stack": top,
            "lateral_x_stack": lat_x,
            "lateral_y_stack": lat_y,
            "delta_egg_mm": p["delta_egg_mm"],
            "k_peak": p["k"],
            "budget_usd": p["budget"],
            "P1": p["P1"],
            "P2_cond": p["p2"],
            "P3_cond": p["p3"],
        },
        "bom": [{"item": b[0], "material": b[1], "mass_g": b[2], "price_usd": b[3]}
                for b in bom],
        "dims": [{"element": d} for d in ["box", "panel", "floor", "lid"]],
        "assembly": [{"step": "разметка", "min": 5}, {"step": "складка", "min": 7}],
        "outputs": {
            "v_impact_m_s": fnum(o["v_impact_m_s"], 3),
            "t_fall_s": fnum(o["t_fall_s"], 3),
            "E_k_J": fnum(o["E_k_J"], 2),
            "E_k_worst_J": fnum(0.5 * 0.5 * o["v_impact_m_s"] ** 2, 2),
            "dU_g_J": fnum(o["dU_g_J"], 3),
            "E_tot_J": fnum(o["E_tot_J"], 2),
            "a_avg_m_s2": fnum(o["a_avg_m_s2"], 1),
            "dt_s": fnum(o["dt_s"], 5),
            "F_avg_N": fnum(o["F_avg_N"], 1),
            "F_peak_N": fnum(o["F_peak_N"], 1),
            "n_avg_g": fnum(o["n_avg_g"], 1),
            "n_peak_g": fnum(o["n_peak_g"], 1),
            "F_egg_N": fnum(o["F_egg_N"], 1),
            "E_egg_J": fnum(o["E_egg_J"], 3),
            "eta": fnum(o["eta"], 4),
            "dx_min_mm": fnum(o["dx_min_mm"], 1),
            "v20_m_s": fnum(o20["v_impact_m_s"], 3),
            "E_k20_J": fnum(o20["E_k_J"], 2),
            "s_req20_mm": fnum(p["k"] * o20["v_impact_m_s"] ** 2 / (2 * 100.0 * G) * 1000, 1),
            "n_peak20_g": fnum(o20["n_peak_g"], 1),
            "P3": fnum(p["P1"] * p["p2"] * p["p3"], 4),
        },
    }

    md = []
    md.append("# Egg Drop -- сценарий A\n")
    md.append(t_conc + "\n")
    md.append(h(0))
    md.append("### 1.1 Название\n\nКонструкция называется «Бумажный кокон».\n")
    md.append("### 1.2 Принцип работы\n\n" + t_conc + "\n")
    md.append("$$\nE_k + m g s = E_{stack} + E_{egg}\n$$\n")
    md.append("### 1.3 Схема\n\n```text\n[яйцо] -> [ложе] -> [аккордеон] -> [оболочка] -> пол\n```\n")
    md.append("### 1.4 Почему эти материалы\n\n"
              "| Материал | Физическое обоснование | Роль |\n|---|---|---|\n"
              "| Гофрокартон | жёсткость при малой массе | оболочка |\n"
              "| Бумага | пластическая складка | ход |\n"
              "| Вата | распределение силы | ложе |\n"
              "| Резинка | упругая фиксация | крепление |\n"
              "| Скотч | работа на сдвиг | соединения |\n\n")
    md.append(h(1))
    md.append("### 2.1 Состав\n\n" + t_bom + "\n\n" + bom_md + "\n")
    md.append("### 2.2 Габариты\n\n" + t_dim + "\n\n" + dims_md + "\n")
    md.append("### 2.3 Крепление яйца\n\n" + t_attach + "\n")
    md.append("### 2.4 Итоговая масса\n\nИтоговая масса системы %d г.\n" % m_total)
    md.append("### 2.5 Итоговый бюджет\n\nИтоговый бюджет %.2f $.\n" % p["budget"])
    md.append("Габаритный объём %d мм³.\n" % vol)
    md.append("### 2.6 Сборка\n\n" + asm_md + "\n")
    md.append(h(2))
    md.append("### 3.1 Исходные данные\n\n$H = 10000$ мм, $g = 9.81$ м/с².\n")
    md.append("### 3.2 Скорость и энергия\n\n$$v = \\sqrt{2gH}$$\n")
    md.append("### 3.3 Модель торможения\n\nПостоянная сила на ходе $s$ (работа силы тяжести "
              "$m g s$ включена).\n")
    md.append("### 3.4 Сводка величин\n\n" + t7 + "\n")
    md.append("### 3.5 Нагрузка на яйцо\n\n$\\eta = 1 - E_{egg}/E_k$.\n")
    md.append("### 3.6 Вердикт\n\n" + t_verdict + "\n")
    md.append(h(3))
    md.append("### 4.1 Модель\n\n" + t_rel + " $P_1 = %.2f$.\n" % p["P1"])
    md.append("### 4.2 Три дропа\n\n" + t_3 + " $P_3 = %.4f$.\n"
              % (p["P1"] * p["p2"] * p["p3"]))
    if p["merge_bullets"]:
        md.append("### 4.3 Слабые места\n\n" + t_weak + "\n\n"
                  "- кромка\n- влага\n- ось\n- смятие\n- угол\n- отскок\n- пробой\n- перекос\n")
        md.append("### 4.4 Что может пойти не так\n\n" + t_fail + "\n")
    else:
        md.append("### 4.3 Слабые места\n\n" + t_weak + "\n\n"
                  "- кромка\n- влага\n- ось\n- смятие\n- угол\n- отскок\n")
        md.append("### 4.4 Что может пойти не так\n\n" + t_fail + "\n\n"
                  "- удар углом\n- мокрый картон\n- перекос\n- недобор хода\n- пробой\n- отскок\n")
    md.append(h(4))
    md.append("### 5.1 Альтернативы\n\n" + t_alt + "\n")
    md.append("| Вариант | Масса, г | Стоимость, $ | Надёжность |\n|---|---|---|---|\n"
              "| A | 436 | 3.17 | 0.75 |\n| B | 451 | 3.57 | 0.60 |\n"
              "| C | 415 | 3.80 | 0.50 |\n")
    md.append(h(5))
    md.append("### 6.1 После первого теста\n\n" + t_imp + "\n\n"
              "| Наблюдение | Метрика | Изменение |\n|---|---|---|\n"
              "| смятие | ход | +слой |\n")
    md.append("### 6.2 Высота 20 м\n\n" + t_20 + "\n")
    md.append("### 6.3 Машиночитаемая модель\n\n```json\n"
              + json.dumps(model, ensure_ascii=False, indent=2) + "\n```\n")
    return "\n".join(md)


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
def check_structure(md):
    out = []
    h2 = h2_list(md)
    norm = [re.sub(r"\s+", " ", x).strip() for x in h2]
    out.append(res("HEADING", norm == REQUIRED_H2,
                   "six H2 headings in spec order: " + " | ".join(REQUIRED_H2),
                   " | ".join(norm) or "(none)",
                   "AC1: mandatory sections, exact order"))
    out.append(res("HEADING_COUNT", len(h2) == 6, "exactly 6 H2", len(h2),
                   "no other top-level sections"))

    ratio, cyr, lat = cyr_lat_ratio(md)
    out.append(res("LANGUAGE", ratio >= 0.60, "Cyrillic share of prose letters >= 0.60",
                   round(ratio, 3), "cyr=%d lat=%d (code, LaTeX and inline tokens excluded)" % (cyr, lat)))

    dollars = len(re.findall(r"\$[^$\n]+\$", md)) + len(re.findall(r"\$\$", md))
    out.append(res("LATEX", dollars >= 10, ">=10 LaTeX fragments", dollars,
                   "AC1: formulas in LaTeX"))

    rows = labelled_rows(md)
    missing = [t for t in PHYS_TOKENS if t not in rows or rows[t] is None]
    out.append(res("MISSING_NUMBER", not missing,
                   "all 7 labelled quantities present with numeric values",
                   "missing=" + ",".join(missing) if missing else "all 7 present",
                   "AC1/AC3/AC8: v_impact, E_k, dt, F_avg, F_peak, n, eta"))

    units_ok = sum(1 for u in ("мм", "г", "Дж", "Н") if u in md)
    out.append(res("UNITS", units_ok == 4 and len(rows) == 7,
                   "mm, g, J, N all used and 7 numeric rows", "%d/4 units, %d rows" % (units_ok, len(rows)),
                   "AC1: units contract of spec section 6"))

    model, _, err = model_block(md)
    out.append(res("MODEL", model is not None, "parseable json model block with 'model' key",
                   "present" if model else (err or "absent"), "AC12: machine-readable model"))
    return out


def check_physics(md):
    out = []
    model, _, err = model_block(md)
    if model is None:
        return [res("MODEL", False, "json model block", err or "absent", "cannot recompute")]

    i = model.get("inputs", {})
    o = model.get("outputs", {})
    need = ["H_mm", "g_m_s2", "m_egg_g", "m_total_g", "E_crit_J", "n_crit_g",
            "s_mm", "k_peak", "delta_egg_mm"]
    miss = [k for k in need if k not in i]
    if miss:
        return [res("MISSING_NUMBER", False, "model inputs complete", "missing=" + ",".join(miss), "")]

    p = phys(i["H_mm"], i["m_total_g"], i["s_mm"], i["k_peak"], i["m_egg_g"],
             i["delta_egg_mm"], i["n_crit_g"])
    p_worst = phys(i["H_mm"], 500.0, i["s_mm"], i["k_peak"], i["m_egg_g"],
                   i["delta_egg_mm"], i["n_crit_g"])

    def cmp(key, rid, got_key, tol_rel=0.05, tol_abs=None, note=""):
        claimed = o.get(got_key)
        if claimed is None:
            out.append(res(rid, False, "%s present in outputs" % got_key, "absent", note))
            return
        ok = rel(float(claimed), p[key]) <= tol_rel
        if tol_abs is not None:
            ok = ok or abs(float(claimed) - p[key]) <= tol_abs
        out.append(res(rid, ok, fnum(p[key], 5), fnum(claimed, 5), note))

    cmp("v_impact_m_s", "V_IMPACT", "v_impact_m_s", 0.0036, 0.05, "sqrt(2gH), AC3")
    cmp("t_fall_s", "T_FALL", "t_fall_s", 0.01, 0.02, "sqrt(2H/g), AC3")
    cmp("E_k_J", "E_K", "E_k_J", 0.011, 0.5, "0.5*m*v^2 at model m_total, AC3")
    cmp("dt_s", "DT", "dt_s", 0.02, 0.002, "2s/v, AC8")
    cmp("F_avg_N", "F_AVG", "F_avg_N", 0.05, None, "m*v/ dt, AC8")
    cmp("F_peak_N", "F_PEAK", "F_peak_N", 0.05, None, "k_peak * F_avg, AC8")
    cmp("n_peak_g", "N_PEAK", "n_peak_g", 0.05, None, "k_peak*v^2/(2 s g), AC8")
    cmp("E_egg_J", "E_EGG", "E_egg_J", 0.05, 0.05, "F_egg*delta_egg, AC8")
    cmp("eta", "ETA", "eta", 0.005, 0.005, "1 - E_egg/E_k, AC8")

    ek_worst = p_worst["E_k_J"]
    cw = o.get("E_k_worst_J")
    out.append(res("E_K_WORST", cw is not None and rel(float(cw), ek_worst) <= 0.011,
                   fnum(ek_worst, 2), cw, "E_k at the 500 g worst case, AC3"))

    # stroke: dx_min and a stroke derived from the layer geometry
    dx = p["dx_min_mm"]
    cdx = o.get("dx_min_mm")
    out.append(res("DX_MIN", cdx is not None and rel(float(cdx), dx) <= 0.05,
                   fnum(dx, 1), cdx, "v^2/(2 n_crit g), AC11"))

    # ---- stroke derived from geometry, on every face --------------------
    s = float(i["s_mm"])
    bottom = i.get("bottom_stack") or {}
    top = i.get("top_stack") or {}
    lat_x = i.get("lateral_x_stack") or {}
    lat_y = i.get("lateral_y_stack") or {}

    def stack_geom(d):
        try:
            n = float(d.get("layers"))
            pch = float(d.get("pitch_mm"))
            rsd = float(d.get("residual_mm"))
            nom = float(d.get("nominal_mm"))
            use = float(d.get("usable_mm"))
        except (TypeError, ValueError):
            return None
        return {"layers": n, "pitch": pch, "residual": rsd, "nominal": nom,
                "usable": use, "d_nominal": n * pch, "d_usable": n * (pch - rsd)}

    bg = stack_geom(bottom)
    if bg is None:
        out.append(res("STROKE", False, "bottom_stack with layers/pitch/residual/nominal/usable",
                       "absent or incomplete", "AC11"))
    else:
        geo_ok = (abs(bg["d_nominal"] - bg["nominal"]) <= 0.5
                  and abs(bg["d_usable"] - bg["usable"]) <= 0.5
                  and abs(bg["usable"] - s) <= 5.0)
        out.append(res("STROKE", geo_ok and s >= dx,
                       "usable == layers*(pitch-residual) within 0.5 mm, == s within 5 mm, s >= dx_min",
                       "derived=%.1f claimed=%.1f s=%.1f dx_min=%.1f"
                       % (bg["d_usable"], bg["usable"], s, dx),
                       "AC11: usable stroke from layer geometry, not declared"))

    cav_h = i.get("cavity_H_mm")
    bed_h = i.get("bed_H_mm")
    tg = stack_geom(top)
    lgx = stack_geom(lat_x)
    lgy = stack_geom(lat_y)
    vert = None
    if bg is not None and tg is not None and cav_h is not None and bed_h is not None:
        vert = bg["nominal"] + float(bed_h) + tg["nominal"]
    fits_v = vert is not None and abs(vert - float(cav_h)) <= 1.0
    out.append(res("STROKE_FITS", fits_v,
                   "bottom.nominal + bed_H + top.nominal == cavity_H",
                   "chain=%s cavity_H=%s" % (vert, cav_h),
                   "AC11: the vertical cavity chain closes exactly"))

    if tg is None:
        out.append(res("TOP_STROKE", False, "top_stack geometry present", "absent", "AC2/AC8"))
    else:
        top_ok = (abs(tg["d_usable"] - tg["usable"]) <= 0.5 and tg["usable"] >= 10.0
                  and abs(tg["d_nominal"] - tg["nominal"]) <= 0.5
                  and tg["nominal"] <= float(i.get("top_stack_mm", 0)) + 0.5)
        out.append(res("TOP_STROKE", top_ok,
                       "top stack: usable>0 (>=10 mm), usable from layers*(pitch-residual), nominal <= top_stack_mm",
                       "usable=%.1f (derived %.1f) nominal=%.1f cap=%s"
                       % (tg["usable"], tg["d_usable"], tg["nominal"], i.get("top_stack_mm")),
                       "AC8: the inverted/rebound face has a real dissipater"))

    def lat_case(d, g, axis):
        if g is None:
            return False, "%s: geometry absent" % axis
        try:
            depth = float(d.get("depth_mm"))
            bed = float(i["bed_%s_mm" % axis])
            cav = float(i["cavity_%s_mm" % axis])
        except (KeyError, TypeError, ValueError):
            return False, "%s: depth/bed/cavity missing" % axis
        want = (cav - bed) / 2.0
        ok = (abs(g["d_usable"] - g["usable"]) <= 0.5
              and g["usable"] > 0.0 and g["usable"] >= 30.0
              and abs(g["d_nominal"] - g["nominal"]) <= 0.5
              and g["nominal"] <= depth + 0.5
              and abs(depth - want) <= 0.5)
        return ok, ("%s: usable=%.1f nominal=%.1f depth=%.1f (annulus %.1f)"
                    % (axis, g["usable"], g["nominal"], depth, want))

    lx_ok, lx_txt = lat_case(lat_x, lgx, "X")
    ly_ok, ly_txt = lat_case(lat_y, lgy, "Y")
    out.append(res("LATERAL_STROKE", lx_ok and ly_ok,
                   "both lateral stacks: usable>0 and >=30 mm, nominal <= annulus depth, depth == (cavity-bed)/2",
                   lx_txt + "; " + ly_txt,
                   "AC8/AC11: the side gaps are dissipaters, not free clearance"))

    dUg = p["dU_g_J"]
    cdg = o.get("dU_g_J")
    etot = o.get("E_tot_J")
    g_ok = (cdg is not None and rel(float(cdg), dUg) <= 0.05
            and etot is not None and rel(float(etot), p["E_tot_J"]) <= 0.01
            and p["dUg_share"] <= 0.05)
    out.append(res("GRAVITY_TERM", g_ok,
                   "dU_g = m*g*s present and == recomputed (share of E_k <= 5%)",
                   "claimed=%s recomputed=%.3f share=%.2f%% E_tot=%s"
                   % (cdg, dUg, 100.0 * p["dUg_share"], etot),
                   "AC11/AC12: gravitational work is not silently dropped"))

    # chain consistency -- over the document's OWN claimed numbers
    chain = []
    try:
        m_kg = float(i["m_total_g"]) / 1000.0
        v_c = float(o["v_impact_m_s"])
        ek_c = float(o["E_k_J"])
        fa_c = float(o["F_avg_N"])
        fp_c = float(o["F_peak_N"])
        dt_c = float(o["dt_s"])
        aa_c = float(o["a_avg_m_s2"])
        ea_c = float(o["E_egg_J"])
        eta_c = float(o["eta"])
        dg_c = float(o.get("dU_g_J", 0.0))
        chain.append(("F_avg = m*a_avg", rel(fa_c, m_kg * aa_c) <= 0.02))
        chain.append(("m*v/(F_avg-m*g) = dt", rel(dt_c, m_kg * v_c / (fa_c - m_kg * G)) <= 0.02))
        chain.append(("F_avg*s = E_k + m*g*s", rel(fa_c * s / 1000.0, ek_c + dg_c) <= 0.02))
        chain.append(("F_peak/F_avg = k", rel(fp_c / fa_c, float(i["k_peak"])) <= 0.02))
        chain.append(("a_avg = v^2/2s + g", rel(aa_c, v_c * v_c / (2 * s / 1000.0) + G) <= 0.02))
        chain.append(("eta = 1-E_egg/E_k", rel(eta_c, 1.0 - ea_c / ek_c) <= 0.005))
        chain.append(("eta > 0.98 requirement", eta_c > 0.98))
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        chain.append(("outputs complete: %s" % exc, False))
    bad = [n for n, ok in chain if not ok]
    out.append(res("CHAIN", not bad, "all 7 chain identities hold (gravity included)",
                   "broken=" + "; ".join(bad) if bad else "ok",
                   "AC12: E_k/momentum/energy/peak/eta identities"))

    # the seven labelled rows must agree with the model outputs
    rows = labelled_rows(md)
    tols = {"v_impact": (0.05, 0.05), "E_k": (0.011, 0.5), "Δt": (0.02, 0.002),
            "F_avg": (0.05, None), "F_peak": (0.05, None), "n": (0.05, None),
            "η": (0.006, 0.006)}
    keys = {"v_impact": "v_impact_m_s", "E_k": "E_k_J", "Δt": "dt_s",
            "F_avg": "F_avg_N", "F_peak": "F_peak_N", "n": "n_peak_g", "η": "eta"}
    bad2 = []
    for tok in PHYS_TOKENS:
        v = rows.get(tok)
        c = o.get(keys[tok])
        if v is None or c is None:
            bad2.append(tok + "(absent)")
            continue
        tr, ta = tols[tok]
        okr = rel(v, float(c)) <= tr
        oka = ta is not None and abs(v - float(c)) <= ta
        if not (okr or oka):
            bad2.append("%s(%s vs %s)" % (tok, v, c))
    out.append(res("TABLE_VS_MODEL", not bad2, "section-3 table equals model outputs",
                   "mismatch=" + "; ".join(bad2) if bad2 else "ok", "AC12"))

    # 20 m iteration
    v20 = math.sqrt(2 * G * 20.0)
    ek20 = 0.5 * (i["m_total_g"] / 1000.0) * v20 * v20
    s_req20 = p["k_peak"] * v20 * v20 / (2 * 100.0 * G) * 1000.0
    c20 = o.get("v20_m_s")
    ce = o.get("E_k20_J")
    cs = o.get("s_req20_mm")
    ok20 = (c20 is not None and rel(float(c20), v20) <= 0.005 and
            ce is not None and rel(float(ce), ek20) <= 0.02 and
            cs is not None and rel(float(cs), s_req20) <= 0.05 and
            s_req20 > float(i["s_mm"]))
    out.append(res("P_20M", ok20,
                   "v20=%.2f E_k20=%.2f s_req20=%.0f mm > achievable %.0f mm" % (v20, ek20, s_req20, float(i["s_mm"])),
                   "v=%s E_k=%s s_req=%s" % (c20, ce, cs),
                   "AC10: 20 m demands a parachute (stroke exceeds the box)"))
    return out


def check_constraints(md):
    out = []
    model, _, err = model_block(md)
    if model is None:
        return [res("MODEL", False, "json model block", err or "absent", "cannot check constraints")]
    i = model.get("inputs", {})
    tables = parse_tables(md)

    bom = find_table(tables, "материал", "масса")
    if bom is None:
        out.append(res("MASS_SUM", False, "BOM table with Материал+Масса", "absent", "AC4"))
        out.append(res("BUDGET_SUM", False, "BOM table", "absent", "AC6"))
        return out
    cm = col_index(bom, "масса")
    cp = col_index(bom, "стоим", "цена")
    masses, prices = [], []
    for row in bom["rows"]:
        if len(row) <= max(cm, cp):
            continue
        v = cell_num(row[cm])
        if v is None:
            v = 0.0
        masses.append(v)
        pv = cell_num(row[cp]) if cp is not None else None
        prices.append(pv if pv is not None else 0.0)
    msum = sum(masses)
    psum = round(sum(prices), 4)
    stated_m = float(i.get("m_total_g", -1))
    stated_b = float(i.get("budget_usd", -1))

    out.append(res("MASS_SUM", abs(msum - stated_m) <= 1.0,
                   "BOM mass sum == stated m_total_g (+-1 g)",
                   "sum=%.1f stated=%.1f rows=%d" % (msum, stated_m, len(masses)), "AC4"))
    out.append(res("MASS_LIMIT", msum <= 500.0 and stated_m <= 500.0,
                   "<= 500 g including egg", "sum=%.1f stated=%.1f" % (msum, stated_m), "AC4"))
    out.append(res("RESERVE", any(("резерв" in (r[0] + r[1]).lower()) or ("запас" in (r[0] + r[1]).lower())
                                  for r in bom["rows"] if len(r) > 1),
                   "explicit reserve row in the BOM", "found" if any(
                       ("резерв" in " ".join(r).lower()) or ("запас" in " ".join(r).lower())
                       for r in bom["rows"]) else "absent", "AC4: stated reserve"))
    out.append(res("BUDGET_SUM", abs(psum - stated_b) <= 0.01,
                   "BOM cost sum == stated budget (+-0.01 $)",
                   "sum=%.2f stated=%.2f" % (psum, stated_b), "AC6"))
    out.append(res("BUDGET_LIMIT", psum <= 5.0 and stated_b <= 5.0,
                   "<= 5.00 $", "sum=%.2f stated=%.2f" % (psum, stated_b), "AC6"))

    dims = find_table(tables, "элемент", "мм")
    if dims is None:
        out.append(res("DIM_MAX", False, "dimension table", "absent", "AC5"))
        out.append(res("VOLUME", False, "dimension table", "absent", "AC5"))
    else:
        vals = []
        for row in dims["rows"]:
            for c in row[1:4]:
                v = cell_num(c)
                if v is not None:
                    vals.append(v)
        mx = max(vals) if vals else None
        out.append(res("DIM_MAX", mx is not None and mx <= 300.0,
                       "every dimension <= 300 mm", "max=%.1f rows=%d" % (mx, len(dims["rows"])) if mx else "no numeric cells",
                       "AC5"))
        box = [i.get("box_X_mm", 0), i.get("box_Y_mm", 0), i.get("box_H_mm", 0)]
        vol = float(box[0]) * float(box[1]) * float(box[2])
        found = []
        for sv in re.findall(r"(\d[\d\s\u00a0]{2,})\s*мм³", md):
            found.append(float(sv.replace(" ", "").replace("\u00a0", "")))
        vol_ok = vol <= 20_000_000.0 and any(abs(f - vol) <= 1000.0 for f in found)
        out.append(res("VOLUME", vol_ok, "bounding volume <= 20 000 000 mm3 and stated",
                       "box=%s vol=%.0f stated=%s" % (box, vol, found[:3]), "AC5"))

    # ---- one wall thickness everywhere, and a cavity chain that closes ----
    def dim_row(*needles):
        if dims is None:
            return None
        for row in dims["rows"]:
            name = (row[0] if row else "").lower()
            if all(n.lower() in name for n in needles):
                return row
        return None

    wp = i.get("wall_panel_mm")
    wt = i.get("wall_total_mm")
    panel = dim_row("панель")
    if panel is None or wp is None:
        out.append(res("WALL_TABLE", False,
                       "a side-panel row in the dimension table and wall_panel_mm in the model",
                       "row=%s wall_panel_mm=%s" % ("found" if panel else "absent", wp), "AC2/AC11"))
    else:
        pv = [cell_num(c) for c in panel[1:4]]
        pv = [v for v in pv if v is not None]
        thin = min(pv) if pv else None
        ok = (thin is not None and abs(thin - float(wp)) <= 0.1
              and wt is not None and abs(float(wt) - 2.0 * float(wp)) <= 0.1)
        out.append(res("WALL_TABLE", ok,
                       "panel thickness in the table == wall_panel_mm, wall_total == 2*wall_panel",
                       "table=%s model=%s wall_total=%s" % (thin, wp, wt),
                       "AC2: one wall thickness, no split 1.5+1.5 vs 10"))

    # ---- lid and floor must be INSET panels inside the 300 mm walls ----
    lid_row = dim_row("крышк")
    flo_row = dim_row("дно")

    def inset_case(row, what):
        if row is None:
            return False, "%s: row absent" % what
        v = [cell_num(c) for c in row[1:4]]
        if len(v) < 3 or None in v:
            return False, "%s: non-numeric cells %s" % (what, v)
        cx = i.get("cavity_X_mm")
        cy = i.get("cavity_Y_mm")
        if cx is None or cy is None:
            return False, "%s: cavity inputs absent" % what
        ok = (abs(v[0] - float(cx)) <= 0.5 and abs(v[1] - float(cy)) <= 0.5
              and 0 < v[2] <= 10.0)
        return ok, "%s: %.1fx%.1fx%.1f mm (cavity %.1fx%.1f)" % (what, v[0], v[1], v[2],
                                                                 float(cx), float(cy))

    lid_ok, lid_txt = inset_case(lid_row, "lid")
    flo_ok, flo_txt = inset_case(flo_row, "floor")
    out.append(res("INSET_PANELS", lid_ok and flo_ok,
                   "lid and floor are inset panels: plan == cavity plan, thickness <= 10 mm",
                   lid_txt + "; " + flo_txt,
                   "AC2/AC5: 250x250 caps would push the outer height to 310 mm"))

    cav = {k: i.get("cavity_%s_mm" % k) for k in ("X", "Y", "H")}
    bx = {k: i.get("box_%s_mm" % k) for k in ("X", "Y", "H")}
    crow = dim_row("полост")
    chain = []
    if None in cav.values() or None in bx.values() or wp is None:
        out.append(res("WALL_CHAIN", False, "box/cavity/wall inputs present", "incomplete", "AC2/AC11"))
    else:
        for k in ("X", "Y", "H"):
            chain.append(("cavity_%s = box_%s - 2w" % (k, k),
                          abs(float(cav[k]) - (float(bx[k]) - 2.0 * float(wp))) <= 0.5))
        if crow is not None:
            cv = [cell_num(c) for c in crow[1:4]]
            for k, v in zip(("X", "Y", "H"), cv):
                chain.append(("table cavity_%s row" % k,
                              v is not None and abs(v - float(cav[k])) <= 0.5))
        else:
            chain.append(("cavity row in the dimension table", False))
        # the annulus must be exactly the lateral stack depth, and the vertical
        # chain must close: bottom.nominal + bed_H + top.nominal == cavity_H
        try:
            lx = i["lateral_x_stack"]
            ly = i["lateral_y_stack"]
            chain.append(("X annulus == lateral X depth",
                          abs((float(cav["X"]) - float(i["bed_X_mm"])) / 2.0
                              - float(lx["depth_mm"])) <= 0.5))
            chain.append(("Y annulus == lateral Y depth",
                          abs((float(cav["Y"]) - float(i["bed_Y_mm"])) / 2.0
                              - float(ly["depth_mm"])) <= 0.5))
            chain.append(("vertical chain closes",
                          abs(float(i["bottom_stack"]["nominal_mm"]) + float(i["bed_H_mm"])
                              + float(i["top_stack"]["nominal_mm"]) - float(cav["H"])) <= 1.0))
        except (KeyError, TypeError, ValueError) as exc:
            chain.append(("stack geometry present: %s" % exc, False))
        badc = [n for n, k in chain if not k]
        out.append(res("WALL_CHAIN", not badc,
                       "cavity = box - 2*wall on every axis, table row agrees, annulus == lateral depth, vertical chain closes",
                       "broken=" + "; ".join(badc) if badc else "%d/%d identities hold" % (len(chain), len(chain)),
                       "AC2/AC11/AC12: the geometry is one chain, recomputable"))

    forb = []
    for row in bom["rows"]:
        cell = " ".join(row[1:2]).lower()
        for name, pat in FORBIDDEN:
            if re.search(pat, cell):
                forb.append(name)
    out.append(res("MATERIAL", not forb, "only allowed materials in the BOM material column",
                   "forbidden=" + ",".join(sorted(set(forb))) if forb else "clean", "AC7"))

    unlisted = []
    for row in bom["rows"]:
        if len(row) < 2:
            continue
        cell = row[1].lower()
        if "резерв" in cell or "запас" in cell:
            continue
        if not any(a in cell for a in ALLOWED):
            unlisted.append(cell)
    out.append(res("MATERIAL_ALLOWED", not unlisted,
                   "every BOM material is on the allowed list of spec 2.3",
                   "unlisted=" + "; ".join(unlisted) if unlisted else "all allowed", "AC7"))
    return out


def check_content(md):
    out = []
    s1, s2, s3 = section(md, 1), section(md, 2), section(md, 3)
    s4, s5, s6 = section(md, 4), section(md, 5), section(md, 6)
    tables = parse_tables(md)
    model, _, err = model_block(md)
    i = (model or {}).get("inputs", {})
    o = (model or {}).get("outputs", {})

    out.append(res("T_CONCEPT_NAME", "«" in s1 and "»" in s1,
                   "design name in guillemets in section 1", "present" if "«" in s1 else "absent", "spec 4.1"))
    has_diagram = any(l in ("", "text", "txt", "ascii") for l, _ in fenced_blocks(s1))
    out.append(res("T_DIAGRAM", has_diagram, "fenced text/ASCII scheme in section 1",
                   "present" if has_diagram else "absent", "spec 4.1"))
    just = find_table(parse_tables(s1), "материал")
    out.append(res("T_MATERIAL_JUSTIFY", just is not None and len(just["rows"]) >= 4,
                   "material justification table with >=4 rows in section 1",
                   "rows=%d" % (len(just["rows"]) if just else 0), "rubric: material choice 15%"))
    out.append(res("T_STAGED", ("ступен" in s1.lower()) or ("каскад" in s1.lower()),
                   "staged energy absorption described in section 1",
                   "present" if "ступен" in s1.lower() else "absent", "spec 4.1"))

    bom = find_table(parse_tables(s2), "материал", "масса")
    out.append(res("T_BOM", bom is not None and len(bom["rows"]) >= 10,
                   "BOM table with >=10 rows in section 2",
                   "rows=%d" % (len(bom["rows"]) if bom else 0), "spec 4.2 / AC2"))
    dims = find_table(parse_tables(s2), "элемент", "мм")
    out.append(res("T_DIMS", dims is not None and len(dims["rows"]) >= 8,
                   "dimension table with >=8 rows in section 2",
                   "rows=%d" % (len(dims["rows"]) if dims else 0), "spec 4.2 / AC2"))
    s23 = subsection(md, 2, "2.3") or s2
    out.append(res("T_ATTACH", ("резин" in s23.lower()) and re.search(r"не прикле|без кле", s23.lower()) is not None,
                   "attachment by rubber bands/rope and explicit 'not glued'",
                   "present" if "резин" in s23.lower() else "absent", "AC7 / spec 4.2"))

    mt = i.get("m_total_g")
    mass_txt_ok = mt is not None and re.search(r"\b%d\b" % int(mt), s2) is not None
    out.append(res("T_TOTAL_MASS", mass_txt_ok, "total mass in g stated in section 2",
                   "m_total_g=%s" % mt, "spec 4.2 / AC4"))
    bud = i.get("budget_usd")
    budget_ok = bud is not None and re.search(r"%d[.,]%02d" % (int(bud), round((bud - int(bud)) * 100)), s2) is not None
    out.append(res("T_BUDGET", budget_ok, "total budget in $ stated in section 2",
                   "budget_usd=%s" % bud, "spec 4.2 / AC6"))

    rows = labelled_rows(md)
    out.append(res("T_PHYSICS_ROWS", len(rows) == 7 and all(v is not None for v in rows.values()),
                   "7 labelled rows with numbers in section 3", "rows=%d" % len(rows), "spec 4.3"))

    out.append(res("T_VERDICT", re.search(r"вердикт", s3.lower()) is not None and
                   re.search(r"вероятн|\bда\b|\bнет\b", s3.lower()) is not None,
                   "explicit verdict (да/нет/вероятно) in section 3",
                   "present" if re.search(r"вердикт", s3.lower()) else "absent", "spec 4.3"))

    p1 = i.get("P1")
    out.append(res("T_P1", p1 is not None and re.search(r"P_?1", s4) is not None and "одн" in s4.lower(),
                   "P(survive 1 drop) with its probability model in section 4",
                   "P1=%s" % p1, "AC9"))
    out.append(res("T_P3", re.search(r"P_?3", s4) is not None and re.search(r"тр[её]х|3", s4) is not None,
                   "P(3 consecutive drops) in section 4",
                   "P3=%s" % (o.get("P3")), "AC9"))
    def h3_block(needle):
        m = re.search(r"^###\s+[^\n]*" + needle + r"[^\n]*\n", s4, re.MULTILINE | re.IGNORECASE)
        if not m:
            return ""
        rest = s4[m.end():]
        nxt = re.search(r"^#{2,3}\s+", rest, re.MULTILINE)
        return rest[: nxt.start()] if nxt else rest

    weak_b = h3_block("слаб")
    fail_b = h3_block("пойти не так")
    n_weak = len(re.findall(r"^\s*[-*]\s+\S", weak_b, re.MULTILINE))
    n_fail = len(re.findall(r"^\s*[-*]\s+\S", fail_b, re.MULTILINE))
    out.append(res("T_WEAK_BULLETS", bool(weak_b.strip()) and n_weak >= 4,
                   "the weak-point heading carries >=4 bullets of its own",
                   "bullets=%d" % n_weak,
                   "AC9: counted in its own block, not over all of section 4"))
    out.append(res("T_FAILURE_BULLETS", bool(fail_b.strip()) and n_fail >= 4,
                   "the failure-mode heading carries >=4 bullets of its own",
                   "bullets=%d (weak=%d)" % (n_fail, n_weak),
                   "AC9: the two lists are counted separately"))
    out.append(res("T_FAILURE", ("пойти не так" in s4.lower()) or ("отказ" in s4.lower()),
                   "failure-mode list in section 4",
                   "present" if "пойти не так" in s4.lower() else "absent", "AC9"))

    alt_ok = ("парашют" in s5.lower()) and ("резин" in s5.lower())
    alt_tbl = find_table(parse_tables(s5), "масса")
    out.append(res("T_ALTS", alt_ok and alt_tbl is not None,
                   "alternatives B (parachute) and C (rubber band) with numbers in section 5",
                   "B=%s C=%s" % ("парашют" in s5.lower(), "резин" in s5.lower()), "AC10"))
    out.append(res("T_ALT_TABLE", alt_tbl is not None and
                   find_table(parse_tables(s5), "масса", "надёж") is not None,
                   "comparison table mass/cost/reliability in section 5",
                   "present" if alt_tbl is not None else "absent", "AC10"))

    out.append(res("T_IMPROVE", ("после первого" in s6.lower()) or ("первого теста" in s6.lower()),
                   "post-first-test improvements in section 6",
                   "present" if "первого" in s6.lower() else "absent", "spec 4.6"))
    out.append(res("T_20M", ("20 000" in s6 or "20000" in s6 or "20 м" in s6)
                   and re.search(r"300", s6) is not None,
                   "20 000 mm recalculation incl. the 300 mm stroke limit in section 6",
                   "present" if ("20 000" in s6 or "20000" in s6) else "absent", "AC10"))
    out.append(res("T_NO_TBD", TBD.search(md) is None, "no placeholder text",
                   "clean" if TBD.search(md) is None else TBD.search(md).group(0), "AC2"))
    return out


def check_egg_attach(md):
    """Constraint rows that live outside a table."""
    s2 = section(md, 2).lower()
    ok = ("резин" in s2) and (re.search(r"не прикле|без кле", s2) is not None)
    out = [res("EGG_ATTACH", ok, "egg held by rubber bands/rope, not glued",
               "present" if ok else "absent", "AC7")]
    asm = find_table(parse_tables(section(md, 2)), "этап", "мин") or find_table(parse_tables(section(md, 2)), "шаг", "мин")
    if asm is None:
        out.append(res("ASSEMBLY", False, "assembly table with minutes", "absent", "spec 2.3"))
    else:
        total = 0.0
        for row in asm["rows"]:
            for c in row[1:]:
                v = cell_num(c)
                if v is not None:
                    total += v
                    break
        out.append(res("ASSEMBLY", total <= 30.0, "assembly time <= 30 min", "%.1f min" % total, "spec 2.3"))
    return out


# --------------------------------------------------------------------------
# probe
# --------------------------------------------------------------------------
def check_probe():
    """Design-feasibility probe for H = 10 m and H = 20 m.  NOT proof of survival."""
    out = []
    m_design = 436.0          # the document's own design mass (BOM total, section 2.1)
    m_worst = 500.0
    s_geom = 159.6            # the document's own usable bottom stroke (section 3.6)
    k_design = 1.5
    n_design_peak = 100.0
    m_egg = 65.0
    delta_egg = 10.0

    rows = []
    for H in (10000.0, 20000.0):
        tag = "A" if H == 10000.0 else "B"
        pr = phys(H, m_design, s_geom, k_design, m_egg, delta_egg, n_design_peak)
        pw = phys(H, m_worst, s_geom, k_design, m_egg, delta_egg, n_design_peak)
        s_req = k_design * pr["v_impact_m_s"] ** 2 / (2 * n_design_peak * G) * 1000.0
        s_req_avg = pr["v_impact_m_s"] ** 2 / (2 * n_design_peak * G) * 1000.0
        rows.append((tag, pr, pw, s_req, s_req_avg))
        out.append(res("PR_%s_V" % tag, abs(pr["v_impact_m_s"] - math.sqrt(2 * G * H / 1000.0)) < 1e-9,
                       "sqrt(2 g H)", fnum(pr["v_impact_m_s"], 4),
                       "H=%d mm" % int(H)))
        out.append(res("PR_%s_EK_DESIGN" % tag, pr["E_k_J"] > 0, "0.5*m_design*v^2",
                       fnum(pr["E_k_J"], 3), "m_design=%d g" % int(m_design)))
        out.append(res("PR_%s_EK_WORST" % tag, pw["E_k_J"] > 0, "0.5*500g*v^2",
                       fnum(pw["E_k_J"], 3), "500 g worst case"))
        out.append(res("PR_%s_S_REQ" % tag, s_req > 0,
                       "k*v^2/(2*n_peak*g) for n_peak<=100 g", fnum(s_req, 1),
                       "avg-only variant %.1f mm" % s_req_avg))
        out.append(res("PR_%s_FAVG" % tag, pr["F_avg_N"] > 0, "m*(v^2/(2s)+g)",
                       fnum(pr["F_avg_N"], 1), "s=%.1f mm, gravity included (dU_g=%.3f J)"
                       % (s_geom, pr["dU_g_J"])))
        out.append(res("PR_%s_FPEAK" % tag, pr["F_peak_N"] > 0, "k_peak*F_avg at k_peak=%s" % k_design,
                       fnum(pr["F_peak_N"], 1), "F_avg=%.1f N" % pr["F_avg_N"]))
        out.append(res("PR_%s_N" % tag, pr["n_peak_g"] > 0, "k_peak*(v^2/(2s*g)+1)",
                       fnum(pr["n_peak_g"], 1), "s=%.1f mm, n_crit design point 100 g" % s_geom))
        out.append(res("PR_%s_EEGG" % tag, pr["E_egg_J"] > 0, "F_egg*delta_egg",
                       fnum(pr["E_egg_J"], 3), "E_crit=1.0 J"))
        out.append(res("PR_%s_ETA" % tag, pr["eta"] > 0, "1-E_egg/E_k", fnum(pr["eta"], 4), "requirement eta>0.98"))

    # peak-factor sensitivity
    sens = []
    for k in (1.2, 1.4, 1.5, 1.8):
        p10 = phys(10000.0, m_design, s_geom, k, m_egg, delta_egg, n_design_peak)
        p20 = phys(20000.0, m_design, s_geom, k, m_egg, delta_egg, n_design_peak)
        sens.append({"k_peak": k, "F_peak_10m_N": fnum(p10["F_peak_N"], 1),
                     "n_peak_10m_g": fnum(p10["n_peak_g"], 1),
                     "F_peak_20m_N": fnum(p20["F_peak_N"], 1),
                     "n_peak_20m_g": fnum(p20["n_peak_g"], 1),
                     "eta_10m": fnum(p10["eta"], 4), "eta_20m": fnum(p20["eta"], 4)})
    ok = all(s["n_peak_10m_g"] < 200 for s in sens)
    out.append(res("PR_K_SENS", ok, "n_peak(10 m) stays inside the 50-200 g band for k=1.2..1.8",
                   "n(10m): %s" % [s["n_peak_10m_g"] for s in sens], "peak factor sensitivity"))

    a_pr = rows[0][1]
    b_pr = rows[1][1]
    a20 = rows[1][3]
    ok_a = a_pr["n_peak_g"] <= n_design_peak
    out.append(res("PR_VERDICT_10M", ok_a,
                   "s=%.1f mm at 436 g keeps n_peak <= 100 g at 10 m" % s_geom,
                   fnum(a_pr["n_peak_g"], 1), "margin %.1f g" % (n_design_peak - a_pr["n_peak_g"])))
    out.append(res("PR_BLOCKER_20M", rows[1][3] > s_geom,
                   "required stroke at 20 m (%.0f mm) exceeds the achievable %.0f mm" % (a20, s_geom),
                   "n_peak_20m=%.1f g, E_egg=%.2f J" % (b_pr["n_peak_g"], b_pr["E_egg_J"]),
                   "BLOCKER for scenario B in a 300 mm box: a parachute/drogue is mandatory"))

    extra = {
        "design": {"m_total_g": m_design, "m_worst_g": m_worst, "m_egg_g": m_egg,
                   "s_geom_mm": s_geom, "k_peak": k_design, "n_crit_g": n_design_peak,
                   "E_crit_J": 1.0, "delta_egg_mm": delta_egg},
        "peak_factor_sensitivity": sens,
        "scenarios": [],
    }
    for tag, pr, pw, s_req, s_req_avg in rows:
        extra["scenarios"].append({
            "scenario": tag, "H_mm": 10000 if tag == "A" else 20000,
            "v_impact_m_s": fnum(pr["v_impact_m_s"], 4), "t_fall_s": fnum(pr["t_fall_s"], 4),
            "E_k_design_J": fnum(pr["E_k_J"], 3), "E_k_worst_J": fnum(pw["E_k_J"], 3),
            "a_avg_m_s2": fnum(pr["a_avg_m_s2"], 1), "n_avg_g": fnum(pr["n_avg_g"], 1),
            "F_avg_N": fnum(pr["F_avg_N"], 1), "dt_s": fnum(pr["dt_s"], 5),
            "F_peak_N": fnum(pr["F_peak_N"], 1), "n_peak_g": fnum(pr["n_peak_g"], 1),
            "F_egg_N": fnum(pr["F_egg_N"], 1), "E_egg_J": fnum(pr["E_egg_J"], 3),
            "eta": fnum(pr["eta"], 4), "s_required_mm_at_100g": fnum(s_req, 1),
            "s_required_avg_mm": fnum(s_req_avg, 1),
            "dx_min_mm_at_100g": fnum(pr["dx_min_mm"], 1),
        })
    return out, extra


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------
def run_all_checks(md):
    fails = []
    for r in check_structure(md) + check_physics(md) + check_constraints(md) + \
            check_content(md) + check_egg_attach(md):
        if not r["ok"]:
            fails.append(r["id"])
    return fails


def check_selftest():
    out = []
    base = build_fixture()
    base_fails = run_all_checks(base)
    out.append(res("BASE_VALID", not base_fails,
                   "the uncorrupted in-memory fixture passes every check",
                   "fails=" + ",".join(base_fails) if base_fails else "0 failures",
                   "selftest precondition"))

    cases = [
        ("HEADING", build_fixture(drop_heading=2), "section 3 heading removed"),
        ("MISSING_NUMBER", build_fixture(drop_token="v_impact"), "v_impact row removed"),
        ("MASS_LIMIT", build_fixture(m_total_g=620, mass_total=620), "BOM total 620 g > 500 g"),
        ("BUDGET_LIMIT", build_fixture(budget=6.10), "budget 6.10 $ > 5.00 $"),
        ("MATERIAL", build_fixture(bad_material="алюминиевая фольга"), "forbidden material in the BOM"),
        ("STROKE", build_fixture(s_mm=80), "stroke 80 mm < dx_min 100 mm"),
        ("LANGUAGE", build_fixture(lang="en"), "document translated to English"),
        ("CHAIN", build_fixture(favg_mult=2.0), "F_avg doubled: momentum chain broken"),
        ("WALL_TABLE", build_fixture(wall_table=1.5),
         "panel 1.5 mm in the table while the model and the cavity say 5 mm"),
        ("LATERAL_STROKE", build_fixture(lat_zero=True),
         "lateral stack with zero usable stroke: the old free-air side gap"),
        ("T_FAILURE_BULLETS", build_fixture(merge_bullets=True),
         "weak-point and failure-mode bullets merged into one list"),
        ("INSET_PANELS", build_fixture(lid_oversize=True),
         "250x250 lid/floor over a 240x240 cavity: outer height would read 310 mm"),
    ]
    missed = []
    for expected, md, why in cases:
        fails = run_all_checks(md)
        detected = expected in fails
        if not detected:
            missed.append(expected)
        out.append(res("FIX_" + expected, detected,
                       "corruption rejected with id %s" % expected,
                       "failing ids=" + (",".join(sorted(set(fails))) if fails else "(none)"),
                       why))
    out.append(res("SELFTEST_COVERAGE", len(cases) >= 12 and not missed,
                   ">=12 fixtures, each rejected with its expected id",
                   "%d fixtures, missed=%s" % (len(cases), missed or "[]"),
                   "an undetected corruption must fail the run"))
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
CHECKS = ("probe", "selftest", "structure", "physics", "constraints", "content")

# plan section 9: every selector must resolve to at least this many cases; a run below its
# floor is a vacuous pass and must FAIL the command even if every selected case passed.
MIN_SELECTED = {
    "probe": 2,       # 10 m and 20 m
    "selftest": 8,    # >=8 negative fixtures
    "structure": 6,   # headings, count, language, latex, numbers, units, model
    "physics": 7,     # >=7 recomputed base results
    "constraints": 6, # mass sum/limit, budget sum/limit, dims, volume, materials
    "content": 12,    # >=12 presence/format checks
}


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--document", default=None)
    ap.add_argument("--check", required=True, choices=CHECKS)
    ap.add_argument("--log", required=True)
    args = ap.parse_args(argv)  # exits 2 on bad usage / unknown selector

    if not os.path.isdir(args.repo):
        sys.stderr.write("usage: --repo is not a directory: %s\n" % args.repo)
        return 2
    doc_checks = ("structure", "physics", "constraints", "content")
    if args.check in doc_checks and not args.document:
        sys.stderr.write("usage: --document is required for --check %s\n" % args.check)
        return 2

    started = utcnow()
    doc_path = None
    md = None
    extra = None
    limits = []
    note = ""

    if args.check == "probe":
        results, extra = check_probe()
        limits = [
            "PROBE IS A DESIGN-FEASIBILITY PROBE, NOT PROOF OF SURVIVAL.",
            "Constant-plateau deceleration model including gravity: F_avg = m*(v^2/(2s)+g), "
            "dU_g = m*g*s, dt = 2s/v.",
            "Peak factor k_peak = F_peak/F_avg is an ASSUMED material property "
            "(folded paper 1.4-1.8); k=1.2-1.8 sensitivity is reported.",
            "Paper crush stress, fold quality, moisture and the bed stiffness are NOT measured.",
            "No air drag at 10/20 m (v = sqrt(2gH)); a parachute case is computed separately in section 6.",
            "E_crit = 1.0 J and n_crit = 100 g are spec design points, not measured thresholds.",
        ]
        note = ("design probe for H=10 m and H=20 m at the document's own m_design=436 g, "
                "m_worst=500 g, s=159.6 mm, k=1.5; gravity work dU_g=m*g*s included")
    elif args.check == "selftest":
        results = check_selftest()
        limits = ["Fixtures are generated in memory; no repository fixtures are used.",
                  "Four fixtures cover the earlier CHECK defects: split wall thickness, "
                  "side gap with no usable stroke, merged weak-point/failure lists, and "
                  "250x250 lid/floor caps that would give a 310 mm outer height.",
                  "The base fixture is a synthetic document, not the deliverable."]
        note = "12 deliberate corruptions must each be rejected with the expected id"
    else:
        doc_path = args.document if os.path.isabs(args.document) else os.path.join(args.repo, args.document)
        if not os.path.isfile(doc_path):
            results = [res("DOCUMENT", False, "document exists", "absent: " + doc_path, "cannot check")]
            note = "document missing"
        else:
            with open(doc_path, "r", encoding="utf-8") as fh:
                md = fh.read()
            if args.check == "structure":
                results = check_structure(md)
                limits = ["Text-only structural analysis; no rendering is performed.",
                          "Language check counts Cyrillic vs Latin letters outside code/LaTeX."]
                note = "AC1 / AC12 structural contract"
            elif args.check == "physics":
                results = check_physics(md)
                limits = ["Model recomputation only; the machine block is the single source of numbers.",
                          "Constant-plateau model with an assumed peak factor.",
                          "No measured data exists for paper crush behaviour."]
                note = "AC3 / AC8 / AC10 / AC11 / AC12 recomputation"
            elif args.check == "constraints":
                results = check_constraints(md) + check_egg_attach(md)
                limits = ["Tables are parsed as GitHub markdown; every row must carry a plain number.",
                          "Prices and masses are document claims, not verified purchases or weighings."]
                note = "AC4 / AC5 / AC6 / AC7"
            else:
                results = check_content(md)
                limits = ["Presence and format checks only; semantic quality is reviewed manually.",
                          "This check cannot decide whether the physics is right."]
                note = "AC2 / AC9 / AC10 presence and format"

    failed = [r for r in results if not r["ok"]]
    status = "pass" if not failed else "fail"
    counts = {
        "selected": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "skipped": 0,
    }
    if counts["selected"] == 0:
        status = "fail"
        results.append(res("VACUOUS", False, "selector resolves to >=1 case", "0 selected", "vacuous run"))
    min_sel = MIN_SELECTED[args.check]
    if counts["selected"] < min_sel:
        status = "fail"
        results.append(res("MIN_SELECTED", False,
                           ">=%d cases selected" % min_sel,
                           "%d selected" % counts["selected"],
                           "a run below the plan's floor is a vacuous pass"))

    log = {
        "check": args.check,
        "selector": {
            "check": args.check,
            "ids": [r["id"] for r in results],
            "min_selected": min_sel,
            "argv": ["--repo", args.repo, "--document", args.document or "",
                     "--check", args.check, "--log", args.log],
        },
        "started_utc": started,
        "repo": os.path.abspath(args.repo),
        "document": doc_path,
        "status": status,
        "counts": counts,
        "results": results,
        "limits": limits,
        "note": note,
    }
    if extra is not None:
        log["probe"] = extra

    log_dir = os.path.dirname(os.path.abspath(args.log))
    if log_dir and not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    with open(args.log, "w", encoding="utf-8") as fh:
        json.dump(log, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print("[%s] %s: %d/%d passed, %d failed -> exit %d" % (
        args.check, status, counts["passed"], counts["selected"], counts["failed"],
        0 if status == "pass" else 1))
    for r in failed:
        print("  FAIL %s: expected %s, observed %s" % (r["id"], r["expected"], r["observed"]))
    print("log: %s" % os.path.abspath(args.log))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
