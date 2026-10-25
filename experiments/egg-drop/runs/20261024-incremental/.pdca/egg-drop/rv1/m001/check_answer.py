#!/usr/bin/env python3.10
"""Mechanical gate for the Egg Drop answer (report schema: egg-drop-gate-v1).

# Scope

Rows G01-G12 mix two kinds of evidence and the report keeps them apart:

  * hard, mechanically verifiable facts: section structure, strict JSON typing,
    independent recomputation of mass / cost / energy / force / stress, hard
    limits (mass, budget, build time, side, volume) and a normalized
    forbidden-material scan of the prose;
  * structural / declarative rows: G02 coverage pointers, G05 role and negation
    reading of prose, G06 declared six-direction protection, G10 repeat-drop
    dependency model, G11 comparison axes, G12 LaTeX/unit style and
    narrative-vs-JSON equality of the verification table.

For the second group the checker only proves that the required declaration is
present and internally consistent. It never treats keyword presence as proof of
physics: physical plausibility, completeness and semantic coherence of those
rows are finally judged by the independent assessor (pdca-check) on the frozen
measurement package.

Exit codes: 0 = PASS (answer) / all controls behaved as declared (selftest);
1 = a violation was correctly detected; 2 = infrastructure/input error or zero
selected cases (INVALID - never PASS).
"""

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SCHEMA = "egg-drop-gate-v1"
DATA_SCHEMA = "egg-drop-data-v1"

SECTION_TITLES = [
    "## 1. Концепция",
    "## 2. Спецификация",
    "## 3. Физические расчёты",
    "## 4. Оценка надёжности",
    "## 5. Альтернативы",
    "## 6. Итерации",
]

ALLOWED_CATEGORIES = {
    "бумага",
    "картон",
    "соломинки",
    "зубочистки",
    "резинки",
    "скотч",
    "верёвка",
    "веревка",
    "пластиковые пакеты",
    "воздушные шары",
    "вата",
    "поролон",
    "пенопласт",
    "пластиковые бутылки",
    "яичные лотки",
}

# categories whose declared wall thickness matters (thin film is allowed, rigid
# plastic thicker than 2 mm is forbidden)
PLASTIC_CATEGORIES = {"пластиковые пакеты", "пластиковые бутылки", "скотч"}

# forbidden materials: normalized stems, matched on prose lines only
FORBIDDEN_PATTERNS = [
    ("metal", re.compile(r"металл|сталь|стальн|алюмин|желез|проволок|латун|олов", re.I)),
    ("glass", re.compile(r"стекл|стеклян", re.I)),
    ("glue", re.compile(r"\bкле[йяю]\b|клеев|прикле", re.I)),
    ("hard plastic", re.compile(r"жёстк\w*\s+пластик|жестк\w*\s+пластик|пластик\w*\s+толще", re.I)),
    ("ready shock absorbers", re.compile(r"готов\w*\s+амортизатор|амортизатор\w*\s+готов", re.I)),
]
NEGATION_RE = re.compile(
    r"(^|[^а-яёa-z])(не|без|запрещ|недопуст|исключ|отказ|вместо|нельзя|никак|не\s+использ|не\s+примен)",
    re.I,
)

GATE_IDS = ["G%02d" % i for i in range(1, 13)]

REQUIRED_POINTERS = [
    "name",
    "principle",
    "scheme",
    "materials_list",
    "element_dimensions",
    "egg_attachment",
    "final_mass",
    "final_budget",
    "v_impact",
    "Ek",
    "delta_t",
    "F_peak",
    "n_load",
    "eta",
    "verdict",
    "p1",
    "p3",
    "weak_points",
    "failure_modes",
    "alternatives",
    "comparison",
    "first_iteration",
    "height_20m",
]

DIRECTIONS = ["top", "bottom", "front", "back", "left", "right"]

# verification-table key -> results field
TABLE_KEYS = {
    "v_impact": "v_impact_m_s",
    "t_fall": "t_fall_s",
    "Ek": "Ek_J",
    "dt_eq": "delta_t_eq_s",
    "F_avg": "F_avg_N",
    "F_peak": "F_peak_N",
    "n_load": "n_load_g",
    "sigma_egg": "sigma_egg_MPa",
    "eta": "eta",
}


class Invalid(Exception):
    """Infrastructure / input error: the run must not produce PASS."""


class Findings:
    """Per-G-ID collection of schema and content findings."""

    def __init__(self):
        self.items = {gid: [] for gid in GATE_IDS}

    def add(self, gid, message):
        self.items[gid].append(message)

    def has(self, gid):
        return bool(self.items[gid])

    def text(self, gid):
        return "; ".join(self.items[gid])


def is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def get_path(data, path):
    """Dotted path lookup; returns (found, value)."""
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return False, None
    return True, cur


def require_num(data, path, owner, findings, *, positive=False, nonneg=False):
    found, value = get_path(data, path)
    if not found:
        findings.add(owner, "missing field %s" % path)
        return None
    if not is_num(value):
        findings.add(owner, "field %s is not a finite number (%r)" % (path, value))
        return None
    if positive and value <= 0:
        findings.add(owner, "field %s must be > 0 (got %r)" % (path, value))
        return None
    if nonneg and value < 0:
        findings.add(owner, "field %s must be >= 0 (got %r)" % (path, value))
        return None
    return float(value)


def require_str(data, path, owner, findings, *, min_len=1):
    found, value = get_path(data, path)
    if not found or not isinstance(value, str) or len(value.strip()) < min_len:
        findings.add(owner, "field %s must be a non-empty string (got %r)" % (path, value))
        return None
    return value


def split_sections(text):
    """Return level-2 sections with their body text (fences respected)."""
    lines = text.splitlines()
    heads = []
    in_fence = False
    for index, line in enumerate(lines):
        if re.match(r"^```", line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence and re.match(r"^##\s+\S", line):
            heads.append((index, line.strip()))
    sections = []
    for position, (index, title) in enumerate(heads):
        end = heads[position + 1][0] if position + 1 < len(heads) else len(lines)
        sections.append({"index": position + 1, "title": title, "body": "\n".join(lines[index + 1:end])})
    return sections


def fenced_blocks(body):
    """Return list of (info, content, terminated)."""
    blocks = []
    current = None
    info = ""
    terminated = True
    for line in body.splitlines():
        match = re.match(r"^```(\w*)\s*$", line.strip())
        if match:
            if current is None:
                current = []
                info = match.group(1)
                terminated = False
            else:
                blocks.append((info, "\n".join(current), True))
                current = None
                info = ""
                terminated = True
        elif current is not None:
            current.append(line)
    if current is not None:
        blocks.append((info, "\n".join(current), False))
    return blocks


def strip_fences(body):
    out = []
    in_fence = False
    for line in body.splitlines():
        if re.match(r"^```", line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def parse_answer(text):
    """Parse structure + data block. Returns dict; raises Invalid on unreadable input."""
    sections = split_sections(text)
    data = None
    json_blocks = 0
    block_problem = ""
    if len(sections) >= 2:
        blocks = fenced_blocks(sections[1]["body"])
        json_blocks = sum(1 for info, _content, _ok in blocks if info == "json")
        candidates = [(content, ok) for info, content, ok in blocks if info == "json"]
        if len(candidates) == 1:
            content, terminated = candidates[0]
            if not terminated:
                block_problem = "json block is not terminated"
            else:
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as exc:
                    block_problem = "json block does not parse: %s" % exc
        elif len(candidates) == 0:
            block_problem = "no fenced json block in section 2"
        else:
            block_problem = "more than one fenced json block in section 2 (%d)" % len(candidates)
    return {
        "sections": sections,
        "data": data,
        "json_blocks": json_blocks,
        "block_problem": block_problem,
    }


def validate_schema(data, findings):
    """Strict typing. Every breach is attached to the G-ID that owns the field."""
    if not isinstance(data, dict):
        findings.add("G01", "data block is not a JSON object")
        return
    found, schema = get_path(data, "schema")
    if schema != DATA_SCHEMA:
        findings.add("G01", "data block marker is %r, expected %r" % (schema, DATA_SCHEMA))

    # physics: declared inputs, owned by the recomputation row
    require_num(data, "physics.H_m", "G07", findings, positive=True)
    require_num(data, "physics.g_m_s2", "G07", findings, positive=True)
    require_num(data, "physics.rho_air_kg_m3", "G07", findings, nonneg=True)
    require_num(data, "physics.cd", "G07", findings, positive=True)
    require_num(data, "physics.v0_m_s", "G07", findings, nonneg=True)

    # materials: mass/cost/quantity rows belong to G03, geometry to G04
    found, materials = get_path(data, "materials")
    if not found or not isinstance(materials, list) or not materials:
        findings.add("G03", "materials must be a non-empty list")
        materials = []
    for position, item in enumerate(materials):
        prefix = "materials[%d]" % position
        if not isinstance(item, dict):
            findings.add("G03", "%s is not an object" % prefix)
            continue
        if not isinstance(item.get("id"), str) or not item.get("id", "").strip():
            findings.add("G03", "%s.id must be a non-empty string" % prefix)
        if not isinstance(item.get("category"), str) or not item.get("category", "").strip():
            findings.add("G05", "%s.category must be a non-empty string" % prefix)
        if not isinstance(item.get("role"), str) or len(item.get("role", "").strip()) < 3:
            findings.add("G05", "%s.role must declare the material role" % prefix)
        require_num(item, "quantity", "G03", findings, nonneg=True)
        require_num(item, "mass_g", "G03", findings, nonneg=True)
        require_num(item, "cost_usd", "G03", findings, nonneg=True)
        dims = item.get("dimensions_mm")
        if not isinstance(dims, list) or len(dims) != 3 or not all(is_num(v) and v >= 0 for v in dims):
            findings.add("G04", "%s.dimensions_mm must be three non-negative numbers" % prefix)
        thickness = item.get("plastic_thickness_mm", "absent")
        if thickness != "absent" and thickness is not None and not is_num(thickness):
            findings.add("G05", "%s.plastic_thickness_mm must be a finite number or null" % prefix)

    # egg
    require_num(data, "egg.mass_g", "G03", findings, positive=True)
    found, glued = get_path(data, "egg.glued")
    if not isinstance(glued, bool):
        findings.add("G05", "egg.glued must be a boolean (got %r)" % (glued,))
    found, rigid = get_path(data, "egg.rigid_to_shell")
    if not isinstance(rigid, bool):
        findings.add("G06", "egg.rigid_to_shell must be a boolean (got %r)" % (rigid,))
    attachment = require_str(data, "egg.attachment", "G06", findings)
    if attachment is not None and attachment not in {"suspended", "soft_suspended"}:
        findings.add("G06", "egg.attachment must declare a soft/suspended type (got %r)" % attachment)
    require_str(data, "egg.attachment_note", "G06", findings, min_len=8)

    # totals and geometry
    require_num(data, "totals.total_mass_g", "G03", findings, nonneg=True)
    require_num(data, "totals.total_cost_usd", "G03", findings, nonneg=True)
    require_num(data, "totals.build_time_min", "G04", findings, nonneg=True)
    for axis in ("length", "width", "height"):
        require_num(data, "outer_dimensions_mm.%s" % axis, "G04", findings, positive=True)

    # braking and protection
    require_num(data, "braking.available_stroke_mm", "G06", findings, nonneg=True)
    require_num(data, "braking.effective_contact_area_mm2", "G07", findings, positive=True)
    require_num(data, "braking.peak_factor_k", "G07", findings, positive=True)
    found, chain = get_path(data, "braking.stroke_chain_mm")
    if not isinstance(chain, dict) or not chain:
        findings.add("G06", "braking.stroke_chain_mm must be a non-empty object")
    else:
        for key, value in chain.items():
            if not is_num(value) or value < 0:
                findings.add("G06", "braking.stroke_chain_mm.%s must be a finite non-negative number" % key)
    for direction in DIRECTIONS:
        found, item = get_path(data, "protection.%s" % direction)
        if not isinstance(item, dict):
            findings.add("G06", "protection.%s must be an object with a declared element" % direction)
            continue
        element = item.get("element")
        if not isinstance(element, str) or len(element.strip()) < 5:
            findings.add("G06", "protection.%s.element must be a non-empty declaration" % direction)
        stroke = item.get("stroke_mm")
        if not is_num(stroke) or stroke < 0:
            findings.add("G06", "protection.%s.stroke_mm must be a finite non-negative number" % direction)

    # model / sensitivity
    require_num(data, "model.n_design_g", "G08", findings, positive=True)
    found, sensitivity = get_path(data, "model.n_sensitivity_g")
    if not isinstance(sensitivity, list) or not all(is_num(v) for v in sensitivity):
        findings.add("G08", "model.n_sensitivity_g must be a list of numbers")
    else:
        for needed in (50.0, 100.0, 200.0):
            if not any(abs(v - needed) < 1e-9 for v in sensitivity):
                findings.add("G08", "model.n_sensitivity_g must include %g g" % needed)

    # results: computed values
    for field in (
        "v_impact_m_s",
        "t_fall_s",
        "Ek_J",
        "a_eq_m_s2",
        "delta_t_eq_s",
        "F_avg_N",
        "F_peak_N",
        "n_load_g",
        "F_egg_N",
        "sigma_egg_MPa",
    ):
        require_num(data, "results.%s" % field, "G07", findings)
    found, dmin = get_path(data, "results.d_min_mm")
    if not isinstance(dmin, dict):
        findings.add("G07", "results.d_min_mm must be an object with n50/n100/n200")
    else:
        for key in ("n50", "n100", "n200"):
            if not is_num(dmin.get(key)):
                findings.add("G07", "results.d_min_mm.%s must be a finite number" % key)
    require_num(data, "results.E_residual_J", "G09", findings, nonneg=True)
    require_num(data, "results.E_absorbed_J", "G09", findings, nonneg=True)
    require_num(data, "results.eta", "G09", findings)

    # probabilities
    require_num(data, "probabilities.P1", "G10", findings)
    require_num(data, "probabilities.P3", "G10", findings)
    found, conditions = get_path(data, "probabilities.conditions")
    if not isinstance(conditions, list) or not conditions:
        findings.add("G10", "probabilities.conditions must declare per-drop conditional factors")
    else:
        for position, item in enumerate(conditions):
            if not isinstance(item, dict) or not is_num(item.get("factor")) or not is_num(item.get("drop")):
                findings.add("G10", "probabilities.conditions[%d] must hold numeric drop and factor" % position)
            elif not (0 < item["factor"] <= 1):
                findings.add("G10", "probabilities.conditions[%d].factor must be in (0, 1]" % position)
    found, declared = get_path(data, "probabilities.dependency_declared")
    if declared is not True:
        findings.add("G10", "probabilities.dependency_declared must be true")
    require_str(data, "probabilities.model", "G10", findings, min_len=40)

    # spec contradiction acknowledgement
    found, refs = get_path(data, "spec_contradiction.refs")
    if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
        findings.add("G08", "spec_contradiction.refs must be a list of strings")
    else:
        joined = " ".join(refs)
        for token in (":152", ":160"):
            if token not in joined:
                findings.add("G08", "spec_contradiction.refs must cite egg-drop-test.md%s" % token)
    note = require_str(data, "spec_contradiction.note", "G08", findings, min_len=20)
    if note is not None and "противореч" not in note.lower():
        findings.add("G08", "spec_contradiction.note must acknowledge the contradiction")

    # coverage pointers
    found, pointers = get_path(data, "pointers")
    if not isinstance(pointers, dict):
        findings.add("G02", "pointers must be an object")
        pointers = {}
    for key in REQUIRED_POINTERS:
        item = pointers.get(key)
        if not isinstance(item, dict):
            findings.add("G02", "missing coverage pointer %r" % key)
            continue
        section = item.get("section")
        fragment = item.get("fragment")
        if not isinstance(section, int) or isinstance(section, bool) or not (1 <= section <= 6):
            findings.add("G02", "pointer %r.section must be 1..6 (got %r)" % (key, section))
        if not isinstance(fragment, str) or len(fragment.strip()) < 8:
            findings.add("G02", "pointer %r.fragment must be a non-empty fragment (>= 8 chars)" % key)


def recompute(data):
    """Independent recomputation from declared inputs. Returns dict of expected values."""
    _, h = get_path(data, "physics.H_m")
    _, g = get_path(data, "physics.g_m_s2")
    _, materials = get_path(data, "materials")
    _, egg_mass = get_path(data, "egg.mass_g")
    _, stroke_mm = get_path(data, "braking.available_stroke_mm")
    _, area_mm2 = get_path(data, "braking.effective_contact_area_mm2")
    _, peak_k = get_path(data, "braking.peak_factor_k")
    _, e_res = get_path(data, "results.E_residual_J")

    material_mass = sum(float(m["mass_g"]) for m in materials)
    material_cost = sum(float(m["cost_usd"]) for m in materials)
    total_mass_g = material_mass + float(egg_mass)
    total_cost = material_cost

    mass = total_mass_g / 1000.0
    v = math.sqrt(2.0 * float(g) * float(h))
    t_fall = math.sqrt(2.0 * float(h) / float(g))
    e_k = 0.5 * mass * v * v
    out = {
        "material_mass_g": material_mass,
        "material_cost_usd": material_cost,
        "total_mass_g": total_mass_g,
        "total_cost_usd": total_cost,
        "mass_kg": mass,
        "v_impact_m_s": v,
        "t_fall_s": t_fall,
        "Ek_J": e_k,
    }
    stroke = float(stroke_mm) / 1000.0
    if stroke <= 0:
        out["stroke_ok"] = False
        return out
    out["stroke_ok"] = True
    a_eq = v * v / (2.0 * stroke)
    dt_eq = 2.0 * stroke / v
    f_avg = mass * (a_eq + float(g))
    f_peak = float(peak_k) * f_avg
    n_load = f_peak / (mass * float(g))
    f_egg = float(egg_mass) / 1000.0 * float(g) * n_load
    sigma = f_egg / float(area_mm2)  # N / mm^2 == MPa
    out.update(
        {
            "a_eq_m_s2": a_eq,
            "delta_t_eq_s": dt_eq,
            "F_avg_N": f_avg,
            "F_peak_N": f_peak,
            "n_load_g": n_load,
            "F_egg_N": f_egg,
            "sigma_egg_MPa": sigma,
            "d_min_mm": {n: v * v / (2.0 * n * float(g)) * 1000.0 for n in (50, 100, 200)},
            "E_residual_J": float(e_res),
            "E_absorbed_J": e_k - float(e_res),
            "eta": (e_k - float(e_res)) / e_k,
        }
    )
    return out


def rel_ok(declared, expected, rel=0.01):
    if abs(expected) < 1e-12:
        return abs(declared) <= 1e-6
    return abs(declared - expected) / abs(expected) <= rel


def row(gid, status, expected, actual, source):
    return {"id": gid, "status": status, "expected": expected, "actual": actual, "source": source}


def check_structure(parsed, findings):
    """G01."""
    sections = parsed["sections"]
    titles = [s["title"] for s in sections]
    if titles != SECTION_TITLES:
        findings.add("G01", "level-2 sections are %r, expected exactly %r" % (titles, SECTION_TITLES))
    for section in sections:
        if not section["body"].strip():
            findings.add("G01", "section %r is empty" % section["title"])
    if parsed["block_problem"]:
        findings.add("G01", parsed["block_problem"])
    if parsed["json_blocks"] > 1:
        findings.add("G01", "section 2 must hold exactly one json block (found %d)" % parsed["json_blocks"])


def check_coverage(parsed, data, findings):
    """G02: every required item points at a non-empty fragment of its own section."""
    pointers = data.get("pointers") or {}
    sections = parsed["sections"]
    for key in REQUIRED_POINTERS:
        item = pointers.get(key)
        if not isinstance(item, dict):
            continue
        section = item.get("section")
        fragment = item.get("fragment")
        if not isinstance(section, int) or isinstance(section, bool) or not (1 <= section <= 6):
            continue
        if not isinstance(fragment, str) or len(fragment.strip()) < 8:
            continue
        if section > len(sections):
            findings.add("G02", "pointer %r targets missing section %d" % (key, section))
            continue
        body = norm(strip_fences(sections[section - 1]["body"]))
        needle = norm(fragment)
        if needle not in body:
            findings.add("G02", "pointer %r fragment not found in section %d: %r" % (key, section, fragment))
        if re.search(r"egg-drop-data-v1|\"schema\"", needle):
            findings.add("G02", "pointer %r points at the JSON block instead of prose" % key)


def check_mass_cost(data, expected, findings):
    """G03."""
    _, declared_mass = get_path(data, "totals.total_mass_g")
    _, declared_cost = get_path(data, "totals.total_cost_usd")
    if is_num(declared_mass) and abs(declared_mass - expected["total_mass_g"]) > 0.1:
        findings.add(
            "G03",
            "declared total mass %r g != independent sum %.3f g (tol 0.1 g)"
            % (declared_mass, expected["total_mass_g"]),
        )
    if is_num(declared_cost) and abs(declared_cost - expected["total_cost_usd"]) > 0.01:
        findings.add(
            "G03",
            "declared total cost %r $ != independent sum %.3f $ (tol $0.01)"
            % (declared_cost, expected["total_cost_usd"]),
        )
    _, materials = get_path(data, "materials")
    if isinstance(materials, list):
        for item in materials:
            if isinstance(item, dict) and isinstance(item.get("category"), str):
                if "яйцо" == norm(item["category"]):
                    findings.add("G03", "material %r duplicates the egg mass" % item.get("id"))


def check_limits(data, expected, findings):
    """G04: hard limits compared with independently recomputed values."""
    mass = expected["total_mass_g"]
    cost = expected["total_cost_usd"]
    if mass > 500.0:
        findings.add("G04", "total mass %.3f g > 500 g" % mass)
    if cost > 5.0 + 1e-9:
        findings.add("G04", "total cost %.4f $ > 5.00 $" % cost)
    _, build = get_path(data, "totals.build_time_min")
    if is_num(build) and build > 30.0:
        findings.add("G04", "build time %r min > 30 min" % build)
    sides = []
    for axis in ("length", "width", "height"):
        _, value = get_path(data, "outer_dimensions_mm.%s" % axis)
        if is_num(value):
            sides.append(float(value))
            if value > 300.0:
                findings.add("G04", "outer %s %r mm > 300 mm" % (axis, value))
    if len(sides) == 3:
        volume = sides[0] * sides[1] * sides[2] / 1e9
        if volume > 0.02 + 1e-12:
            findings.add("G04", "bounding volume %.6f m3 > 0.02 m3" % volume)


def check_materials(parsed, data, findings):
    """G05: allowed categories, plastic thickness, egg not glued, prose scan."""
    _, materials = get_path(data, "materials")
    if isinstance(materials, list):
        for item in materials:
            if not isinstance(item, dict):
                continue
            category = item.get("category")
            if not isinstance(category, str):
                continue
            key = norm(category)
            if key not in ALLOWED_CATEGORIES:
                findings.add("G05", "unknown material category %r" % category)
                continue
            if key in PLASTIC_CATEGORIES:
                thickness = item.get("plastic_thickness_mm")
                if not is_num(thickness):
                    findings.add("G05", "plastic %r must declare plastic_thickness_mm" % category)
                elif thickness > 2.0:
                    findings.add("G05", "plastic %r thickness %r mm > 2 mm" % (category, thickness))
    _, glued = get_path(data, "egg.glued")
    if glued is True:
        findings.add("G05", "egg is declared glued")

    sections = parsed["sections"]
    prose = "\n".join(strip_fences(s["body"]) for s in sections)
    for line in prose.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for label, pattern in FORBIDDEN_PATTERNS:
            if pattern.search(stripped) and not NEGATION_RE.search(stripped):
                findings.add("G05", "forbidden material in use (%s): %r" % (label, stripped[:120]))


def check_protection(data, findings):
    """G06."""
    _, stroke = get_path(data, "braking.available_stroke_mm")
    if is_num(stroke) and stroke <= 0:
        findings.add("G06", "available braking stroke is %r mm, must be > 0" % stroke)
    _, chain = get_path(data, "braking.stroke_chain_mm")
    if isinstance(chain, dict) and is_num(stroke):
        parts = [v for k, v in chain.items() if k != "sum" and is_num(v)]
        total = chain.get("sum")
        if parts and is_num(total):
            if abs(sum(parts) - total) > 0.1:
                findings.add("G06", "stroke chain parts sum %.2f mm != declared sum %.2f mm" % (sum(parts), total))
            if abs(total - stroke) > 0.1:
                findings.add("G06", "stroke chain sum %.2f mm != available stroke %.2f mm" % (total, stroke))
        elif parts and not is_num(total):
            findings.add("G06", "stroke chain must declare numeric sum")
    _, rigid = get_path(data, "egg.rigid_to_shell")
    if rigid is True:
        findings.add("G06", "egg is rigidly attached to the outer shell")
    _, protection = get_path(data, "protection")
    if isinstance(protection, dict):
        for direction in DIRECTIONS:
            item = protection.get(direction)
            if not isinstance(item, dict) or not isinstance(item.get("element"), str):
                findings.add("G06", "direction %r has no declared protective element" % direction)


def check_physics(data, expected, findings):
    """G07: independent recomputation with 1% relative tolerance."""
    if not expected.get("stroke_ok", False):
        return False
    _, results = get_path(data, "results")
    if not isinstance(results, dict):
        return True
    for field in (
        "v_impact_m_s",
        "t_fall_s",
        "Ek_J",
        "a_eq_m_s2",
        "delta_t_eq_s",
        "F_avg_N",
        "F_peak_N",
        "n_load_g",
        "F_egg_N",
        "sigma_egg_MPa",
    ):
        declared = results.get(field)
        if not is_num(declared):
            continue
        if not rel_ok(declared, expected[field]):
            findings.add("G07", "%s declared %r != recomputed %.6g" % (field, declared, expected[field]))
    dmin = results.get("d_min_mm")
    if isinstance(dmin, dict):
        for key, n in (("n50", 50), ("n100", 100), ("n200", 200)):
            declared = dmin.get(key)
            if is_num(declared) and not rel_ok(declared, expected["d_min_mm"][n]):
                findings.add("G07", "d_min_mm.%s declared %r != recomputed %.4f mm" % (key, declared, expected["d_min_mm"][n]))
    for field in ("E_residual_J", "E_absorbed_J", "eta"):
        declared = results.get(field)
        if is_num(declared) and not rel_ok(declared, expected[field]):
            findings.add("G07", "%s declared %r != recomputed %.6g" % (field, declared, expected[field]))
    return True


def check_load_and_contradiction(data, expected, findings, spec_path):
    """G08."""
    _, n_design = get_path(data, "model.n_design_g")
    if is_num(n_design) and n_design > 100.0:
        findings.add("G08", "declared design peak %r g > 100 g" % n_design)
    if is_num(n_design) and expected.get("stroke_ok") and not rel_ok(n_design, expected["n_load_g"]):
        findings.add(
            "G08",
            "declared design peak %r g does not match the recomputed peak %.4f g"
            % (n_design, expected["n_load_g"]),
        )
    _, sensitivity = get_path(data, "model.n_sensitivity_g")
    if isinstance(sensitivity, list):
        for needed in (50.0, 100.0, 200.0):
            if not any(is_num(v) and abs(v - needed) < 1e-9 for v in sensitivity):
                findings.add("G08", "sensitivity for %g g is missing" % needed)
    _, dmin = get_path(data, "results.d_min_mm")
    if isinstance(dmin, dict):
        for key in ("n50", "n100", "n200"):
            if not is_num(dmin.get(key)):
                findings.add("G08", "d_min for %s is missing" % key)
    if spec_path is not None and spec_path.exists():
        lines = spec_path.read_text(encoding="utf-8").splitlines()
        if len(lines) >= 160:
            if "100" not in lines[151] or "50" not in lines[151]:
                findings.add("G08", "spec line 152 no longer states the 50-100 g range")
            if "200" not in lines[159]:
                findings.add("G08", "spec line 160 no longer states the 50-200 g range")


def check_energy(data, expected, findings):
    """G09: strict thresholds on independently recomputed values."""
    if not expected.get("stroke_ok"):
        return
    e_k = expected["Ek_J"]
    e_res = expected["E_residual_J"]
    eta = expected["eta"]
    sigma = expected["sigma_egg_MPa"]
    if not (0.0 <= e_res <= e_k):
        findings.add("G09", "residual energy %r J outside [0, Ek=%.4f]" % (e_res, e_k))
    if not (eta > 0.98):
        findings.add("G09", "efficiency %.6f is not > 0.98 (strict)" % eta)
    if not (e_res < 0.8):
        findings.add("G09", "residual energy %.6f J is not < 0.8 J (strict)" % e_res)
    if not (sigma <= 25.0):
        findings.add("G09", "contact stress %.6f MPa > 25 MPa" % sigma)


def check_probabilities(data, findings):
    """G10."""
    _, p1 = get_path(data, "probabilities.P1")
    _, p3 = get_path(data, "probabilities.P3")
    if is_num(p1) and not (0.0 <= p1 <= 1.0):
        findings.add("G10", "P1=%r outside [0, 1]" % p1)
    if is_num(p3) and not (0.0 <= p3 <= 1.0):
        findings.add("G10", "P3=%r outside [0, 1]" % p3)
    if is_num(p1) and is_num(p3) and p3 > p1 + 1e-12:
        findings.add("G10", "P3=%r is greater than P1=%r" % (p3, p1))
    _, conditions = get_path(data, "probabilities.conditions")
    if is_num(p1) and is_num(p3) and isinstance(conditions, list):
        factors = [item.get("factor") for item in conditions if isinstance(item, dict)]
        if factors and all(is_num(f) for f in factors):
            expected = p1
            for factor in factors:
                expected *= float(factor)
            if abs(p3 - expected) > 0.02:
                findings.add(
                    "G10",
                    "P3=%r contradicts the declared dependency model (expected %.4f from P1 and conditional factors)"
                    % (p3, expected),
                )
    _, model = get_path(data, "probabilities.model")
    if isinstance(model, str) and re.fullmatch(r"\s*P_?\{?1\}?\s*\^\s*3\s*", model):
        findings.add("G10", "bare P1^3 independence model without justification")


def check_alternatives(parsed, findings):
    """G11: 2-3 compared alternatives, first-iteration response, 20 m recalculation."""
    sections = parsed["sections"]
    if len(sections) < 6:
        return
    alt_body = strip_fences(sections[4]["body"])
    numbered = [ln for ln in alt_body.splitlines() if re.match(r"^\s*\d+\.\s+\S", ln)]
    if not (2 <= len(numbered) <= 3):
        findings.add("G11", "expected 2-3 compared alternatives, found %d numbered items" % len(numbered))
    lowered = norm(alt_body)
    for axis, words in (("mass", ("масс",)), ("cost", ("стоим", "цен")), ("reliability", ("надёжн", "надежн", "вероятн"))):
        if not any(word in lowered for word in words):
            findings.add("G11", "comparison axis %r is missing" % axis)
    iter_body = norm(strip_fences(sections[5]["body"]))
    if "19.81" not in iter_body and "19,81" not in iter_body:
        findings.add("G11", "20 m recalculation (impact velocity 19.81 m/s) is missing")
    if "200 мм" not in iter_body:
        findings.add("G11", "20 m recalculation (required stroke 200 mm) is missing")
    if "перв" not in iter_body:
        findings.add("G11", "first-iteration response is missing")


def parse_verification_table(body):
    values = {}
    for line in strip_fences(body).splitlines():
        match = re.match(r"^\|\s*([A-Za-z_]+)\s*\|\s*([-+]?\d+(?:[.,]\d+)?)\s*([^|]*)\|", line.strip())
        if not match:
            continue
        key = match.group(1)
        if key in TABLE_KEYS:
            values[key] = float(match.group(2).replace(",", "."))
    return values


def check_style_and_consistency(parsed, data, findings):
    """G12: LaTeX, units, narrative-vs-JSON equality of the verification table."""
    sections = parsed["sections"]
    if len(sections) < 3:
        return
    physics = sections[2]["body"]
    spec = sections[1]["body"]
    math_lines = sum(1 for line in physics.splitlines() if "$" in line)
    if math_lines < 5:
        findings.add("G12", "expected LaTeX formulas in section 3, found %d math lines" % math_lines)
    if "$$" not in physics:
        findings.add("G12", "display LaTeX ($$...$$) is missing in section 3")
    for unit, body in (("мм", spec), ("г", spec), ("Дж", physics), ("Н", physics)):
        if unit not in body:
            findings.add("G12", "unit %r is missing from the answer" % unit)
    table = parse_verification_table(physics)
    _, results = get_path(data, "results")
    if not isinstance(results, dict):
        return
    for key, field in TABLE_KEYS.items():
        if key not in table:
            findings.add("G12", "verification table row %r is missing" % key)
            continue
        declared = results.get(field)
        if not is_num(declared):
            continue
        if not rel_ok(table[key], declared, 0.01):
            findings.add("G12", "narrative %s=%r != JSON %s=%r" % (key, table[key], field, declared))


def run_gate(text, spec_path=None):
    """Run all G01-G12 rows. Returns (checks, gate, diagnostics)."""
    findings = Findings()
    parsed = parse_answer(text)
    diagnostics = []
    data = parsed["data"]

    check_structure(parsed, findings)
    if findings.has("G01"):
        checks = [
            row(
                "G01",
                "FAIL",
                "six level-2 sections in the required order, one egg-drop-data-v1 json block in section 2",
                findings.text("G01"),
                "answer.md:headings",
            )
        ]
        for gid in GATE_IDS[1:]:
            checks.append(
                row(gid, "NA", "not evaluated", "structure gate G01 failed, content rows not evaluated", "answer.md")
            )
        return checks, "FAIL", diagnostics

    if not isinstance(data, dict):
        findings.add("G01", "data block is not a JSON object")
        checks = [
            row("G01", "FAIL", "parseable egg-drop-data-v1 json block", findings.text("G01"), "answer.md:section 2")
        ]
        for gid in GATE_IDS[1:]:
            checks.append(row(gid, "NA", "not evaluated", "structure gate G01 failed", "answer.md"))
        return checks, "FAIL", diagnostics

    validate_schema(data, findings)
    expected = recompute(data)

    check_coverage(parsed, data, findings)
    check_mass_cost(data, expected, findings)
    check_limits(data, expected, findings)
    check_materials(parsed, data, findings)
    check_protection(data, findings)
    stroke_ok = check_physics(data, expected, findings)
    check_load_and_contradiction(data, expected, findings, spec_path)
    check_energy(data, expected, findings)
    check_probabilities(data, findings)
    check_alternatives(parsed, findings)
    check_style_and_consistency(parsed, data, findings)

    expectations = {
        "G01": "six level-2 sections in the required order, one egg-drop-data-v1 json block in section 2",
        "G02": "every mandatory section-4 item covered by a non-empty fragment in its own section",
        "G03": "mass and cost independently recomputed, egg counted once, non-negative quantities",
        "G04": "mass <= 500 g, cost <= $5.00, build <= 30 min, each side <= 300 mm, V <= 0.02 m3",
        "G05": "allowed materials only, plastic thickness declared, egg not glued, no forbidden material in use",
        "G06": "six protected directions, non-zero braking stroke with a dimensional chain, soft egg attachment",
        "G07": "velocity, time, energy, force, load, stress and absorption recomputed within 1%",
        "G08": "design peak <= 100 g, 50/100/200 g sensitivity, spec contradiction at :152/:160 acknowledged",
        "G09": "eta > 0.98, residual energy < 0.8 J, contact stress <= 25 MPa, 0 <= Eres <= Ek",
        "G10": "P1,P3 in [0,1], P3 <= P1, explicit dependency/damage model",
        "G11": "2-3 alternatives compared on mass, cost, reliability; first iteration; 20 m recalculation",
        "G12": "LaTeX formulas, consistent units, narrative numbers equal to the JSON",
    }
    sources = {
        "G01": "answer.md:headings",
        "G02": "answer.md:pointers",
        "G03": "answer.md:json.materials,json.totals",
        "G04": "answer.md:json.totals,json.outer_dimensions_mm",
        "G05": "answer.md:json.materials,answer.md:prose",
        "G06": "answer.md:json.braking,json.protection",
        "G07": "answer.md:json.results (recomputed)",
        "G08": "answer.md:json.model,json.spec_contradiction",
        "G09": "answer.md:json.results (recomputed)",
        "G10": "answer.md:json.probabilities",
        "G11": "answer.md:sections 5-6",
        "G12": "answer.md:section 3 verification table",
    }
    checks = []
    for gid in GATE_IDS:
        if gid == "G07" and not stroke_ok:
            checks.append(
                row(gid, "NA", expectations[gid], "not evaluated: zero braking stroke (see G06)", sources[gid])
            )
            continue
        status = "FAIL" if findings.has(gid) else "PASS"
        actual = findings.text(gid) if findings.has(gid) else "all assertions of this row hold"
        checks.append(row(gid, status, expectations[gid], actual, sources[gid]))
    gate = "PASS" if all(item["status"] in ("PASS", "NA") for item in checks) and not any(
        item["status"] == "FAIL" for item in checks
    ) else "FAIL"
    return checks, gate, diagnostics


def resolve(repo, value):
    path = Path(value)
    if not path.is_absolute():
        path = Path(repo) / path
    return path


def write_report(path, report):
    target = Path(path)
    if target.parent and str(target.parent):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def report_skeleton(suite, selected):
    return {
        "schema": SCHEMA,
        "suite": suite,
        "selected_cases": selected,
        "input_hashes": {},
        "checks": [],
        "cases": [],
        "gate": "FAIL",
        "diagnostics": [],
    }


def run_answer(args):
    repo = Path(args.repo)
    answer_path = resolve(repo, args.answer)
    report = report_skeleton("answer", 0)
    if not answer_path.is_file():
        raise Invalid("answer file not found: %s" % answer_path)
    report["selected_cases"] = 1
    report["input_hashes"][str(answer_path)] = sha256_file(answer_path)
    spec_path = repo / "experiments" / "egg-drop" / "egg-drop-test.md"
    if spec_path.is_file():
        report["input_hashes"][str(spec_path)] = sha256_file(spec_path)
    text = answer_path.read_text(encoding="utf-8")
    checks, gate, diagnostics = run_gate(text, spec_path if spec_path.is_file() else None)
    report["checks"] = checks
    report["cases"] = [
        {
            "case": args.case,
            "expected_status": "PASS",
            "expected_id": None,
            "observed_status": gate,
            "observed_ids": [item["id"] for item in checks if item["status"] == "FAIL"],
            "ok": gate == "PASS",
        }
    ]
    report["gate"] = gate
    report["diagnostics"] = diagnostics
    write_report(args.report, report)
    return 0 if gate == "PASS" else 1


def load_manifest(fixtures_dir):
    manifest_path = Path(fixtures_dir) / "manifest.json"
    if not manifest_path.is_file():
        raise Invalid("manifest not found: %s" % manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Invalid("manifest does not parse: %s" % exc)
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise Invalid("manifest declares no cases")
    return manifest_path, cases


def run_selftest(args):
    repo = Path(args.repo)
    fixtures_dir = resolve(repo, args.fixtures)
    manifest_path, declared = load_manifest(fixtures_dir)
    if args.case == "all-declared":
        selected = declared
    else:
        selected = [item for item in declared if item.get("case") == args.case]
    if not selected:
        raise Invalid("zero cases selected for --case %r" % args.case)

    report = report_skeleton("selftest", len(selected))
    report["input_hashes"][str(manifest_path)] = sha256_file(manifest_path)
    spec_path = repo / "experiments" / "egg-drop" / "egg-drop-test.md"
    if spec_path.is_file():
        report["input_hashes"][str(spec_path)] = sha256_file(spec_path)
    cases = []
    failures = 0
    for item in selected:
        answer_path = resolve(repo, str(Path(args.fixtures) / item["path"])) if not Path(item["path"]).is_absolute() else Path(item["path"])
        if not answer_path.is_file():
            raise Invalid("control answer not found: %s" % answer_path)
        report["input_hashes"][str(answer_path)] = sha256_file(answer_path)
        text = answer_path.read_text(encoding="utf-8")
        checks, gate, diagnostics = run_gate(text, spec_path if spec_path.is_file() else None)
        observed_ids = [row_item["id"] for row_item in checks if row_item["status"] == "FAIL"]
        expected_status = item.get("expected_status")
        expected_id = item.get("expected_id")
        if expected_status == "PASS":
            ok = gate == "PASS" and not observed_ids
        else:
            ok = gate == "FAIL" and observed_ids == [expected_id]
        if not ok:
            failures += 1
            report["diagnostics"].append(
                "case %s: expected %s at %s, observed %s %s"
                % (item.get("case"), expected_status, expected_id, gate, observed_ids)
            )
        cases.append(
            {
                "case": item.get("case"),
                "expected_status": expected_status,
                "expected_id": expected_id,
                "observed_status": gate,
                "observed_ids": observed_ids,
                "ok": ok,
            }
        )
    report["cases"] = cases
    report["gate"] = "PASS" if failures == 0 else "FAIL"
    write_report(args.report, report)
    return 0 if failures == 0 else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Egg Drop mechanical gate")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--suite", required=True, choices=["selftest", "answer"])
    parser.add_argument("--case", required=True)
    parser.add_argument("--fixtures")
    parser.add_argument("--answer")
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)

    try:
        if args.suite == "answer":
            if not args.answer:
                raise Invalid("--answer is required for --suite answer")
            return run_answer(args)
        if not args.fixtures:
            raise Invalid("--fixtures is required for --suite selftest")
        return run_selftest(args)
    except Invalid as exc:
        report = report_skeleton(args.suite, 0)
        report["diagnostics"] = ["INVALID: %s" % exc]
        try:
            write_report(args.report, report)
        except OSError as write_exc:
            sys.stderr.write("cannot write report: %s\n" % write_exc)
        sys.stderr.write("INVALID: %s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
