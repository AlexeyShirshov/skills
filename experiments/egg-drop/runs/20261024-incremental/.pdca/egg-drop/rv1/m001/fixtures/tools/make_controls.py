#!/usr/bin/env python3.10
"""Build the declared controls from the handwritten known-good answer.

Each control is a full copy of ``known-good/answer.md`` with exactly one
controlled defect. Numeric mutations are applied to the JSON block first and
then the derived numbers (totals, results, verification table) are recomputed,
so the control stays arithmetically coherent and only the intended rule is
violated.

Usage (from the repository root):
    /usr/bin/python3.10 experiments/egg-drop/fixtures/tools/make_controls.py
"""

import copy
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent
KNOWN_GOOD = FIXTURES / "known-good" / "answer.md"


def split_doc(text):
    lines = text.splitlines()
    heads = []
    in_fence = False
    for index, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and re.match(r"^##\s+\S", line):
            heads.append(index)
    preamble = "\n".join(lines[: heads[0]])
    sections = []
    for position, start in enumerate(heads):
        end = heads[position + 1] if position + 1 < len(heads) else len(lines)
        block = lines[start:end]
        title = block[0]
        body = "\n".join(block[1:]).strip("\n")
        sections.append([title, body])
    return preamble, sections


def render_doc(preamble, sections):
    chunks = [preamble.rstrip("\n"), ""]
    for title, body in sections:
        chunks.append(title)
        chunks.append("")
        chunks.append(body.strip("\n"))
        chunks.append("")
    return "\n".join(chunks).rstrip("\n") + "\n"


def extract_data(section_two_body):
    match = re.search(r"```json\n(.*?)\n```", section_two_body, re.S)
    if not match:
        raise SystemExit("known-good section 2 has no json block")
    return json.loads(match.group(1))


def replace_data(section_two_body, data):
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    block = "```json\n" + payload + "\n```"
    # lambda replacement: a string replacement would eat backslashes of the
    # LaTeX fragments stored in the pointer values
    return re.sub(r"```json\n.*?\n```", lambda _match: block, section_two_body, flags=re.S)


def recompute(data, *, keep=()):
    """Recompute totals and the derived model from the declared inputs."""
    total_mass = sum(float(item["mass_g"]) for item in data["materials"]) + float(data["egg"]["mass_g"])
    total_cost = sum(float(item["cost_usd"]) for item in data["materials"])
    data["totals"]["total_mass_g"] = round(total_mass, 3)
    data["totals"]["total_cost_usd"] = round(total_cost, 4)

    mass = total_mass / 1000.0
    g = float(data["physics"]["g_m_s2"])
    h = float(data["physics"]["H_m"])
    v = math.sqrt(2.0 * g * h)
    e_k = 0.5 * mass * v * v
    results = data["results"]
    if "Ek_J" not in keep:
        results["Ek_J"] = round(e_k, 6)
    if "v_impact_m_s" not in keep:
        results["v_impact_m_s"] = round(v, 6)
    if "t_fall_s" not in keep:
        results["t_fall_s"] = round(math.sqrt(2.0 * h / g), 6)

    stroke = float(data["braking"]["available_stroke_mm"]) / 1000.0
    if stroke > 0:
        k = float(data["braking"]["peak_factor_k"])
        area = float(data["braking"]["effective_contact_area_mm2"])
        a_eq = v * v / (2.0 * stroke)
        f_avg = mass * (a_eq + g)
        f_peak = k * f_avg
        n_load = f_peak / (mass * g)
        f_egg = float(data["egg"]["mass_g"]) / 1000.0 * g * n_load
        sigma = f_egg / area
        if "a_eq_m_s2" not in keep:
            results["a_eq_m_s2"] = round(a_eq, 6)
        if "delta_t_eq_s" not in keep:
            results["delta_t_eq_s"] = round(2.0 * stroke / v, 8)
        if "F_avg_N" not in keep:
            results["F_avg_N"] = round(f_avg, 6)
        if "F_peak_N" not in keep:
            results["F_peak_N"] = round(f_peak, 6)
        if "n_load_g" not in keep:
            results["n_load_g"] = round(n_load, 6)
        if "F_egg_N" not in keep:
            results["F_egg_N"] = round(f_egg, 6)
        if "sigma_egg_MPa" not in keep:
            results["sigma_egg_MPa"] = round(sigma, 6)
        results["d_min_mm"] = {
            "n50": round(v * v / (2.0 * 50.0 * g) * 1000.0, 3),
            "n100": round(v * v / (2.0 * 100.0 * g) * 1000.0, 3),
            "n200": round(v * v / (2.0 * 200.0 * g) * 1000.0, 3),
        }
    if "eta" not in keep:
        e_res = float(results["E_residual_J"])
        results["E_absorbed_J"] = round(e_k - e_res, 6)
        results["eta"] = round((e_k - e_res) / e_k, 8)
    return data


TABLE_FORMATS = {
    "v_impact": ("v_impact_m_s", "%.4f", "м/с"),
    "t_fall": ("t_fall_s", "%.4f", "с"),
    "Ek": ("Ek_J", "%.3f", "Дж"),
    "dt_eq": ("delta_t_eq_s", "%.6f", "с"),
    "F_avg": ("F_avg_N", "%.3f", "Н"),
    "F_peak": ("F_peak_N", "%.3f", "Н"),
    "n_load": ("n_load_g", "%.3f", "g"),
    "sigma_egg": ("sigma_egg_MPa", "%.5f", "МПа"),
    "eta": ("eta", "%.5f", ""),
}


def write_table(sections, data):
    body = sections[2][1]
    for key, (field, fmt, unit) in TABLE_FORMATS.items():
        value = float(data["results"][field])
        cell = (fmt % value).strip() + (" " + unit if unit else "")
        pattern = re.compile(r"^\|\s*" + re.escape(key) + r"\s*\|[^|]*\|$", re.M)
        body, count = pattern.subn("| %s | %s |" % (key, cell), body)
        if count != 1:
            raise SystemExit("verification table row %r not found exactly once (%d)" % (key, count))
    sections[2][1] = body


def set_section_two(sections, data):
    sections[1][1] = replace_data(sections[1][1], data)


def case(name, description, expected_status, expected_id, mutate):
    return {
        "case": name,
        "description": description,
        "expected_status": expected_status,
        "expected_id": expected_id,
        "mutate": mutate,
    }


def mutate_mass_501(data, sections, text_ops):
    data["materials"][0]["mass_g"] = 205.0
    text_ops.append(("446 г", "501 г"))


def mutate_side_301(data, sections, text_ops):
    data["outer_dimensions_mm"]["width"] = 301.0
    text_ops.append(("270 × 270 × 270 мм, объём 0.019683 м³", "270 × 301 × 270 мм, объём 0.021943 м³"))
    text_ops.append(("270 × 270 × 270 мм, внутри", "270 × 301 × 270 мм, внутри"))


def mutate_volume_cube(data, sections, text_ops):
    data["outer_dimensions_mm"] = {"length": 300.0, "width": 300.0, "height": 300.0}
    text_ops.append(("270 × 270 × 270 мм, объём 0.019683 м³", "300 × 300 × 300 мм, объём 0.027 м³"))
    text_ops.append(("270 × 270 × 270 мм, внутри", "300 × 300 × 300 мм, внутри"))


def mutate_budget_501(data, sections, text_ops):
    data["materials"][0]["cost_usd"] = 2.77
    text_ops.append(("2.84 $", "5.01 $"))


def mutate_build_31(data, sections, text_ops):
    data["totals"]["build_time_min"] = 31.0
    text_ops.append(("Время сборки — 26 минут", "Время сборки — 31 минута"))


def mutate_metal(data, sections, text_ops):
    sections[1][1] = sections[1][1].rstrip("\n") + "\n\nДля усиления углов используется металлическая скоба.\n"


def mutate_glued(data, sections, text_ops):
    data["egg"]["glued"] = True


def mutate_zero_stroke(data, sections, text_ops):
    data["braking"]["available_stroke_mm"] = 0.0
    data["braking"]["stroke_chain_mm"] = {"crush_zone": 0.0, "foam": 0.0, "cotton": 0.0, "sum": 0.0}


def mutate_velocity(data, sections, text_ops):
    data["results"]["v_impact_m_s"] = 12.0


def mutate_energy(data, sections, text_ops):
    data["results"]["Ek_J"] = 60.0


def mutate_force(data, sections, text_ops):
    data["results"]["F_peak_N"] = 500.0


def mutate_load(data, sections, text_ops):
    data["results"]["n_load_g"] = 120.0


def mutate_stress(data, sections, text_ops):
    data["results"]["sigma_egg_MPa"] = 3.5


def mutate_eta(data, sections, text_ops):
    data["results"]["E_residual_J"] = 1.5
    e_k = float(data["results"]["Ek_J"])
    data["results"]["E_absorbed_J"] = round(e_k - 1.5, 6)
    data["results"]["eta"] = round((e_k - 1.5) / e_k, 8)


def mutate_probabilities(data, sections, text_ops):
    data["probabilities"]["P3"] = 1.3
    text_ops.append(("P3 = 0.703", "P3 = 1.3"))


def mutate_null_mass(data, sections, text_ops):
    data["totals"]["total_mass_g"] = None


def mutate_unknown_material(data, sections, text_ops):
    data["materials"].append(
        {
            "id": "polyurethane_pad",
            "category": "полиуретан",
            "role": "дополнительный демпфер",
            "quantity": 1,
            "mass_g": 5.0,
            "cost_usd": 0.10,
            "dimensions_mm": [50.0, 50.0, 10.0],
            "plastic_thickness_mm": None,
        }
    )
    text_ops.append(("446 г", "451 г"))
    text_ops.append(("2.84 $", "2.94 $"))


def mutate_prohibition_only(data, sections, text_ops):
    sections[0][1] = (
        sections[0][1].rstrip("\n")
        + "\n\nСтекло не применяем, клей не используем, готовые амортизаторы не применяем:"
        + " все они запрещены условиями задания.\n"
    )


CASES = [
    case("known-good", "handwritten arithmetic-consistent reference answer", "PASS", None, None),
    case("m01-missing-section", "section 6 removed", "FAIL", "G01", lambda d, s, t: s.pop(5)),
    case(
        "m02-section-order",
        "sections 5 and 6 swapped",
        "FAIL",
        "G01",
        lambda d, s, t: s.__setitem__(slice(4, 6), [s[5], s[4]]),
    ),
    case(
        "m03-missing-s4-item",
        "section 4 weak points item and its pointer removed",
        "FAIL",
        "G02",
        lambda d, s, t: (
            d["pointers"].pop("weak_points"),
            s[3].__setitem__(
                1,
                s[3][1].replace("Слабые места: углы каркаса и остаточный ресурс смятия после второго падения.\n", ""),
            ),
        ),
    ),
    case("m04-mass-501", "one material mass raised so the total is 501 g", "FAIL", "G04", mutate_mass_501),
    case("m05-side-301", "outer width 301 mm", "FAIL", "G04", mutate_side_301),
    case("m06-volume-300-cube", "outer dimensions 300x300x300 mm (V=0.027 m3)", "FAIL", "G04", mutate_volume_cube),
    case("m07-budget-501", "material cost raised so the budget is $5.01", "FAIL", "G04", mutate_budget_501),
    case("m08-build-31", "build time 31 min", "FAIL", "G04", mutate_build_31),
    case("m09-metal-used", "metal bracket used in the project prose", "FAIL", "G05", mutate_metal),
    case("m10-egg-glued", "egg declared glued", "FAIL", "G05", mutate_glued),
    case("m11-zero-stroke", "available braking stroke set to zero", "FAIL", "G06", mutate_zero_stroke),
    case("m12-wrong-velocity", "declared impact velocity 12 m/s", "FAIL", "G07", mutate_velocity),
    case("m13-wrong-energy", "declared kinetic energy 60 J", "FAIL", "G07", mutate_energy),
    case("m14-wrong-force", "declared peak force 500 N", "FAIL", "G07", mutate_force),
    case("m15-wrong-load", "declared load factor 120 g", "FAIL", "G07", mutate_load),
    case("m16-wrong-stress", "declared contact stress 3.5 MPa", "FAIL", "G07", mutate_stress),
    case("m17-wrong-eta", "residual energy 1.5 J, so eta <= 0.98", "FAIL", "G09", mutate_eta),
    case("m18-bad-probabilities", "P3 = 1.3 (outside [0,1])", "FAIL", "G10", mutate_probabilities),
    case("m19-null-total-mass", "total mass is null instead of a number", "FAIL", "G03", mutate_null_mass),
    case("m20-unknown-material", "unknown material category", "FAIL", "G05", mutate_unknown_material),
    case(
        "p01-prohibition-only",
        "forbidden materials mentioned only as prohibitions/negations",
        "PASS",
        None,
        mutate_prohibition_only,
    ),
]


def build_one(spec):
    preamble, sections = split_doc(KNOWN_GOOD.read_text(encoding="utf-8"))
    sections = [list(item) for item in sections]
    data = copy.deepcopy(extract_data(sections[1][1]))
    text_ops = []
    if spec["case"] == "m19-null-total-mass":
        # the null must survive the recomputation, so it is applied afterwards
        recompute(data)
        spec["mutate"](data, sections, text_ops)
    else:
        if spec["mutate"] is not None:
            spec["mutate"](data, sections, text_ops)
        # keep every control arithmetically coherent: recompute totals, derived
        # results and the verification table, except for fields the mutation
        # deliberately corrupts (a derived value) or removes (zero stroke)
        keep = ()
        if spec["case"] in ("m12-wrong-velocity", "m13-wrong-energy", "m14-wrong-force", "m15-wrong-load", "m16-wrong-stress"):
            keep = ("v_impact_m_s", "Ek_J", "F_peak_N", "n_load_g", "sigma_egg_MPa")
        recompute(data, keep=keep)
    set_section_two(sections, data)
    write_table(sections, data)
    text = render_doc(preamble, sections)
    for old, new in text_ops:
        if old not in text:
            raise SystemExit("case %s: literal %r not found" % (spec["case"], old))
        text = text.replace(old, new)
    return text


def main():
    manifest = {"schema": "egg-drop-fixtures-v1", "controls": len(CASES), "cases": []}
    for spec in CASES:
        relative = "known-good/answer.md" if spec["case"] == "known-good" else "controls/%s/answer.md" % spec["case"]
        if spec["case"] != "known-good":
            target = FIXTURES / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(build_one(spec), encoding="utf-8")
            print("wrote", relative)
        manifest["cases"].append(
            {
                "case": spec["case"],
                "path": relative,
                "expected_status": spec["expected_status"],
                "expected_id": spec["expected_id"],
                "description": spec["description"],
            }
        )
    (FIXTURES / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("cases:", len(manifest["cases"]))


if __name__ == "__main__":
    main()
