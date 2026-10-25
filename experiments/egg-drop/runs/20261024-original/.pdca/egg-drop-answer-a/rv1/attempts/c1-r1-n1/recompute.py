#!/usr/bin/env python3
"""recompute.py — frozen verification harness for experiments/egg-drop/answer-a.md (scenario A).

Cases
-----
structure : six exact `##` headings, LaTeX/Russian presence, no embedded script,
            9 required machine-readable blocks and their key/unit schema,
            `coverage.md` completeness (all 23 bullets of spec section 4),
            frozen `manifest.json` hashes, `snapshot.json` spec hash + read-only
            repository inventory (no unexpected change outside the allowed paths).
numeric   : independently recomputes every decisive number from the document's own
            tables (mass sums, drag-corrected fall, energy/momentum, braking
            kinematics, average/peak forces, egg-vs-system forces, g-loads, both
            survival gates, E_crit/eta sensitivities, probabilities, 20 m scenario,
            alternatives) and compares it with the declared values.
selftest  : in-process suite over a synthetic document; contains mandatory
            expected-negative mutants (one per check family) and CLI error paths.

Document table format (fixed by PLAN, written by D3)
----------------------------------------------------
Fenced block with info string `numeric`, first content line `# block: <id>`, then
rows `key | value | unit`. Comments start with `#`. Nine block ids are required:

    design, materials, constraints, impact, criteria, sensitivity,
    reliability, scenario20, alternatives

Units are strict tokens: g, mm, m, m2, m3, s, m/s, m/s2, kg/m3, kg*m/s, j, n,
usd, min, and `-` for a dimensionless/string value. Decimal comma is accepted in
numeric values.

Exit codes
----------
0  all selected checks passed (non-zero number of executed checks)
1  data inconsistency or constraint violation — the failing criterion ID is printed
2  cannot run: bad CLI, missing/unreadable document, non-UTF-8, internal error, or
   zero selected checks (never a pass)
A malformed table/heading in the *document* is reported as exit 1 with ID
`A02.schema` / `A02.headings` — it is a defect of the data under test, not of the
invocation. The harness never writes into the repository.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from pathlib import Path

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_CANNOT = 2

REQUIRED_HEADINGS = [
    "## 1. Концепция",
    "## 2. Спецификация",
    "## 3. Физические расчёты",
    "## 4. Оценка надёжности",
    "## 5. Альтернативы",
    "## 6. Итерации",
]

REQUIRED_BLOCKS = [
    "design",
    "materials",
    "constraints",
    "impact",
    "criteria",
    "sensitivity",
    "reliability",
    "scenario20",
    "alternatives",
]

BULLET_IDS = (
    ["4.1.%d" % i for i in (1, 2, 3)]
    + ["4.2.%d" % i for i in (1, 2, 3, 4, 5)]
    + ["4.3.%d" % i for i in (1, 2, 3, 4, 5, 6, 7)]
    + ["4.4.%d" % i for i in (1, 2, 3, 4)]
    + ["4.5.%d" % i for i in (1, 2)]
    + ["4.6.%d" % i for i in (1, 2)]
)

FORBIDDEN_FENCE_LANGS = {
    "python", "py", "python3", "js", "javascript", "ts", "typescript",
    "sh", "bash", "shell", "zsh", "html", "sql", "ruby", "go", "rust",
    "c", "cpp", "cs", "java", "php", "perl", "lua",
}

# Material names are checked by keyword; the engineering review by CHECK is the
# substantive A04 judgement (allowed list: egg-drop-test.md:56, forbidden: :57).
FORBIDDEN_NAME_TOKENS = [
    "металл", "сталь", "алюмин", "желез", "стекл", "клей", "эпокси",
    "смол", "саморез", "гвозд", "болт",
    "metal", "steel", "alumin", "iron", "glass", "glue", "epoxy",
    "resin", "screw", "nail", "bolt",
]

UNIT_ALIASES = {
    "g": "g", "г": "g", "gram": "g",
    "mm": "mm", "мм": "mm",
    "m": "m", "м": "m",
    "m2": "m2", "м2": "m2",
    "m3": "m3", "м3": "m3",
    "m/s": "m/s", "м/с": "m/s",
    "m/s2": "m/s2", "м/с2": "m/s2",
    "kg/m3": "kg/m3", "кг/м3": "kg/m3",
    "j": "j", "дж": "j",
    "n": "n", "н": "n",
    "kg*m/s": "kg*m/s", "кг*м/с": "kg*m/s",
    "s": "s", "с": "s", "sec": "s",
    "usd": "usd", "$": "usd",
    "min": "min", "мин": "min",
    "-": "-", "": "-", "1": "-",
}

SCHEMA = {
    "design": {
        "mass_total_g": "g",
        "dim_x_mm": "mm",
        "dim_y_mm": "mm",
        "dim_z_mm": "mm",
        "volume_m3": "m3",
        "cost_usd": "usd",
        "assembly_min": "min",
    },
    "constraints": {
        "egg_glued": "-",
        "protected_sides": "-",
        "braking_travel_mm": "mm",
    },
    "impact": {
        "H_m": "m",
        "g_m_s2": "m/s2",
        "rho_air_kg_m3": "kg/m3",
        "mass_total_g": "g",
        "drag_mode": "-",
        "Cd": "-",
        "area_m2": "m2",
        "deploy_delay_s": "s",
        "Cd_before": "-",
        "area_before_m2": "m2",
        "Cd_after": "-",
        "area_after_m2": "m2",
        "v_control_m_s": "m/s",
        "v_impact_m_s": "m/s",
        "t_fall_s": "s",
        "E_k_J": "j",
        "p_kg_m_s": "kg*m/s",
    },
    "criteria": {
        "eta": "-",
        "E_egg_J": "j",
        "E_crit_J": "j",
        "dt_brake_s": "s",
        "brake_distance_mm": "mm",
        "peak_factor": "-",
        "a_avg_m_s2": "m/s2",
        "a_peak_m_s2": "m/s2",
        "n_peak": "g",
        "n_crit": "g",
        "F_egg_peak_N": "n",
        "F_sys_peak_N": "n",
        "F_sys_avg_N": "n",
        "eta_required": "-",
        "binding_gate": "-",
    },
    "sensitivity": {
        "E_crit_1_J": "j",
        "E_crit_2_J": "j",
        "eta_required_1": "-",
        "eta_required_2": "-",
        "n_crit_sens": "g",
    },
    "reliability": {
        "p_single": "-",
        "p_three": "-",
        "p_mode": "-",
    },
    "scenario20": {
        "H_m": "m",
        "mass_total_g": "g",
        "v_control_m_s": "m/s",
        "v_impact_m_s": "m/s",
        "E_k_J": "j",
        "E_egg_J": "j",
        "eta": "-",
    },
    "alternatives": {
        "alt%d_%s" % (i, k): u
        for i in (1, 2, 3)
        for k, u in (("mass_g", "g"), ("cost_usd", "usd"), ("p_single", "-"))
    },
}

REQUIRED_KEYS = {
    "design": list(SCHEMA["design"]),
    "materials": ["mass_egg_g"],
    "constraints": list(SCHEMA["constraints"]),
    "impact": [
        "H_m", "g_m_s2", "rho_air_kg_m3", "mass_total_g", "drag_mode",
        "v_control_m_s", "v_impact_m_s", "t_fall_s", "E_k_J", "p_kg_m_s",
    ],
    "criteria": list(SCHEMA["criteria"]),
    "sensitivity": list(SCHEMA["sensitivity"]),
    "reliability": list(SCHEMA["reliability"]),
    "scenario20": list(SCHEMA["scenario20"]),
    "alternatives": [],
}

MATERIAL_RE = re.compile(r"^mat([0-9]{2})_(name|mass_g)$")
KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
FENCE_OPEN_RE = re.compile(r"^```([A-Za-z0-9_+.-]*)\s*$")


class CannotRun(Exception):
    """The harness cannot produce a result (exit 2)."""


class DataFail(Exception):
    """A defect of the document under test (exit 1), carrying the criterion ID."""

    def __init__(self, cid, message):
        super().__init__(message)
        self.cid = cid


class Ctx:
    def __init__(self, repo=None, document=None, rel=None, attempt_dir=None):
        self.repo = repo
        self.document = document
        self.rel = rel
        self.attempt_dir = attempt_dir


class Report:
    def __init__(self, case):
        self.case = case
        self.rows = []
        self.nchecks = 0
        self.nfail = 0

    def check(self, cid, ok, detail=""):
        self.nchecks += 1
        if not ok:
            self.nfail += 1
        self.rows.append(("PASS" if ok else "FAIL", cid, detail))

    def skip(self, cid, detail=""):
        self.rows.append(("SKIP", cid, detail))

    def note(self, cid, detail=""):
        self.rows.append(("INFO", cid, detail))


def final_rc(rep):
    if rep.nfail:
        return EXIT_FAIL
    if rep.nchecks == 0:
        return EXIT_CANNOT
    return EXIT_PASS


def norm_unit(unit):
    u = unit.strip().lower()
    u = u.replace("²", "2").replace("³", "3").replace("·", "*").replace("^", "")
    u = u.replace(" ", "")
    return UNIT_ALIASES.get(u, u)


def _close(a, b, rel=0.0, abs_=0.0):
    if rel:
        return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)
    return abs(a - b) <= abs_


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Document parsing
# --------------------------------------------------------------------------- #
def iter_outside_fences(text):
    in_fence = False
    for n, line in enumerate(text.split("\n"), 1):
        line = line.rstrip("\r")
        s = line.strip()
        if not in_fence:
            if s.startswith("```"):
                in_fence = True
                continue
            yield n, line
        else:
            if s == "```":
                in_fence = False


def split_fences(text):
    """Return [(info, body_lines, start_line)] for every fenced block."""
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\r")
        m = FENCE_OPEN_RE.match(line.strip())
        if not m:
            i += 1
            continue
        info = m.group(1).lower()
        body = []
        j = i + 1
        closed = False
        while j < len(lines):
            if lines[j].strip() == "```":
                closed = True
                break
            body.append(lines[j])
            j += 1
        if not closed:
            raise DataFail("A02.schema", "unclosed fence opened at line %d" % (i + 1))
        out.append((info, body, i + 1))
        i = j + 1
    return out


def parse_numeric_blocks(text):
    blocks = {}
    for info, body, start in split_fences(text):
        if info != "numeric":
            continue
        bid = None
        rows = {}
        for k, raw in enumerate(body, 1):
            s = raw.strip()
            if not s:
                continue
            if s.startswith("#"):
                m = re.match(r"^#\s*block\s*:\s*([a-z0-9_]+)\s*$", s)
                if m:
                    if bid is not None:
                        raise DataFail("A02.schema", "block at line %d has two '# block:' lines" % start)
                    bid = m.group(1)
                continue
            parts = [p.strip() for p in s.split("|")]
            if len(parts) != 3:
                raise DataFail(
                    "A02.schema",
                    "line %d: expected 'key | value | unit', got %r" % (start + k, s),
                )
            key, val, unit = parts
            if not KEY_RE.match(key):
                raise DataFail("A02.schema", "line %d: bad key %r" % (start + k, key))
            if key in rows:
                raise DataFail("A02.schema", "line %d: duplicate key %r" % (start + k, key))
            rows[key] = (val, unit)
        if bid is None:
            raise DataFail("A02.schema", "numeric block at line %d has no '# block: <id>' line" % start)
        if bid not in REQUIRED_BLOCKS:
            raise DataFail("A02.schema", "unknown numeric block id %r at line %d" % (bid, start))
        if bid in blocks:
            raise DataFail("A02.schema", "duplicate numeric block %r" % bid)
        blocks[bid] = (rows, start)
    return blocks


def validate_block(bid, rows):
    problems = []
    schema = SCHEMA.get(bid, {})
    for key, (val, unit) in rows.items():
        if bid == "materials":
            if key == "mass_egg_g":
                want = "g"
            else:
                m = MATERIAL_RE.match(key)
                if not m:
                    problems.append("unknown key %s" % key)
                    continue
                want = "g" if m.group(2) == "mass_g" else "-"
        else:
            if key not in schema:
                problems.append("unknown key %s" % key)
                continue
            want = schema[key]
        if norm_unit(unit) != norm_unit(want):
            problems.append("%s: unit %r != %r" % (key, unit, want))

    for key in REQUIRED_KEYS[bid]:
        if key not in rows:
            problems.append("missing key %s" % key)

    if bid == "materials":
        pairs = {}
        for key in rows:
            m = MATERIAL_RE.match(key)
            if m:
                pairs.setdefault(m.group(1), set()).add(m.group(2))
        complete = [i for i, v in pairs.items() if {"name", "mass_g"} <= v]
        if len(complete) < 4:
            problems.append("%d complete matNN_name/matNN_mass_g pairs (>=4 required)" % len(complete))
        for i, v in pairs.items():
            if {"name", "mass_g"} - v:
                problems.append("incomplete material pair mat%s" % i)
    elif bid == "impact":
        mode = (rows.get("drag_mode", ("", "-"))[0] or "").strip().lower()
        if mode == "constant":
            for key in ("Cd", "area_m2"):
                if key not in rows:
                    problems.append("missing key %s (drag_mode=constant)" % key)
        elif mode == "deployment":
            for key in ("deploy_delay_s", "Cd_before", "area_before_m2",
                        "Cd_after", "area_after_m2"):
                if key not in rows:
                    problems.append("missing key %s (drag_mode=deployment)" % key)
        elif mode != "none":
            problems.append("drag_mode %r not in none|constant|deployment" % mode)
    return problems


def _unit_for(bid, key):
    if bid == "materials":
        if key == "mass_egg_g":
            return "g"
        m = MATERIAL_RE.match(key)
        if m:
            return "g" if m.group(2) == "mass_g" else "-"
    return SCHEMA[bid][key]


class Block:
    def __init__(self, bid, rows):
        self.bid = bid
        self.rows = rows

    def _expected_unit(self, key):
        return _unit_for(self.bid, key)

    def _raw(self, key):
        if key not in self.rows:
            raise DataFail("A02.schema", "%s: missing key %s" % (self.bid, key))
        return self.rows[key]

    def num(self, key):
        val, unit = self._raw(key)
        want = self._expected_unit(key)
        if norm_unit(unit) != norm_unit(want):
            raise DataFail("A02.schema", "%s.%s: unit %r != %r" % (self.bid, key, unit, want))
        try:
            x = float(val.replace(",", ".").strip())
        except ValueError:
            raise DataFail("A02.schema", "%s.%s: not numeric: %r" % (self.bid, key, val))
        if not math.isfinite(x):
            raise DataFail("A02.schema", "%s.%s: not finite" % (self.bid, key))
        return x

    def text(self, key):
        val, unit = self._raw(key)
        want = self._expected_unit(key)
        if norm_unit(unit) != norm_unit(want):
            raise DataFail("A02.schema", "%s.%s: unit %r != %r" % (self.bid, key, unit, want))
        return val.strip()


# --------------------------------------------------------------------------- #
# Physics
# --------------------------------------------------------------------------- #
def simulate_fall(mass_kg, height_m, g, rho, cda_fn, dt=0.002):
    """RK4 integration of x'' = g - rho*CdA(t)*v|v| / (2m); returns (t_fall, v_impact)."""

    def acc(t, v):
        return g - cda_fn(t) * rho * v * abs(v) / (2.0 * mass_kg)

    x = v = t = 0.0
    steps = int(300.0 / dt)
    for _ in range(steps):
        k1v = acc(t, v)
        k1x = v
        k2v = acc(t + dt / 2.0, v + dt / 2.0 * k1v)
        k2x = v + dt / 2.0 * k1v
        k3v = acc(t + dt / 2.0, v + dt / 2.0 * k2v)
        k3x = v + dt / 2.0 * k2v
        k4v = acc(t + dt, v + dt * k3v)
        k4x = v + dt * k3v
        nx = x + dt / 6.0 * (k1x + 2 * k2x + 2 * k3x + k4x)
        nv = v + dt / 6.0 * (k1v + 2 * k2v + 2 * k3v + k4v)
        nt = t + dt
        if nx >= height_m:
            frac = (height_m - x) / (nx - x) if nx > x else 1.0
            return t + frac * dt, v + frac * (nv - v)
        x, v, t = nx, nv, nt
    raise DataFail("A06.velocity_drag", "integration did not reach the ground within 300 s")


# --------------------------------------------------------------------------- #
# Repository evidence checks (read-only git)
# --------------------------------------------------------------------------- #
def _git(repo, *args):
    try:
        r = subprocess.run(
            ["git", "-C", str(repo)] + list(args),
            capture_output=True, text=True, timeout=60,
        )
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def check_inventory(repo, snap):
    """Return a list of problems, or None if git is unavailable (check skipped)."""
    out = _git(repo, "ls-files", "--cached", "--others", "--exclude-standard")
    if out is None:
        return None
    current = set(out.splitlines())
    base = set(snap.get("inventory_baseline") or [])
    allowed = set(snap.get("allowed_new_paths") or [])
    prefixes = tuple(snap.get("allowed_new_prefixes") or [])
    problems = []

    def _allowed(path):
        if path in allowed:
            return True
        return bool(prefixes) and path.startswith(prefixes)

    extra = sorted(
        p for p in current - base
        if not _allowed(p) and not p.endswith(".pyc") and "/__pycache__/" not in p
    )
    if extra:
        problems.append("unexpected new paths: " + ", ".join(extra[:8]))
    gone = sorted(p for p in base - current if not p.endswith(".pyc"))
    if gone:
        problems.append("baseline paths missing: " + ", ".join(gone[:8]))

    st = _git(repo, "status", "--porcelain", "-uall")
    if st is not None:
        baseline_untracked = set(snap.get("baseline_untracked") or [])
        dirty = []
        for line in st.splitlines():
            if not line.strip():
                continue
            code, path = line[:2], line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if path in baseline_untracked or _allowed(path):
                continue
            dirty.append("%s %s" % (code, path))
        if dirty:
            problems.append("unexpected modifications: " + ", ".join(dirty[:8]))
    return problems


# --------------------------------------------------------------------------- #
# Case: structure
# --------------------------------------------------------------------------- #
def _heading_detail(got):
    missing = [h for h in REQUIRED_HEADINGS if h not in got]
    extra = [h for h in got if h not in REQUIRED_HEADINGS]
    bits = []
    if missing:
        bits.append("missing: " + "; ".join(missing))
    if extra:
        bits.append("extra: " + "; ".join(extra))
    if not missing and not extra and got != REQUIRED_HEADINGS:
        bits.append("order differs: " + " | ".join(got))
    return "; ".join(bits) if bits else "6/6 exact headings in order"


def case_structure(text, ctx, rep):
    outside = list(iter_outside_fences(text))
    got = [line.strip() for _, line in outside if line.startswith("## ")]
    rep.check("A02.headings", got == REQUIRED_HEADINGS, _heading_detail(got))

    math_spans = len(re.findall(r"\$\$?", text))
    rep.check("A02.latex", math_spans >= 6, "%d math delimiters found (>=6 required)" % math_spans)

    cyr = len(re.findall(r"[А-Яа-яЁё]", text))
    rep.check("A02.russian", cyr >= 200, "%d Cyrillic letters (>=200 required)" % cyr)

    bad = []
    try:
        fences = split_fences(text)
    except DataFail as exc:
        fences = []
        rep.check(exc.cid, False, str(exc))
    for info, _body, start in fences:
        if info in FORBIDDEN_FENCE_LANGS:
            bad.append("line %d: ```%s" % (start, info))
    if re.search(r"<\s*script\b", text, re.I):
        bad.append("inline <script")
    rep.check("A02.no_script", not bad, "no embedded code fences" if not bad else "; ".join(bad))

    try:
        blocks = parse_numeric_blocks(text)
    except DataFail as exc:
        rep.check(exc.cid, False, str(exc))
        blocks = None
    if blocks is not None:
        missing = [b for b in REQUIRED_BLOCKS if b not in blocks]
        rep.check(
            "A03.blocks",
            not missing,
            "9/9 required numeric blocks" if not missing else "missing: " + ", ".join(missing),
        )
        for bid in REQUIRED_BLOCKS:
            if bid not in blocks:
                continue
            probs = validate_block(bid, blocks[bid][0])
            rep.check(
                "A02.schema:%s" % bid,
                not probs,
                "ok" if not probs else "; ".join(probs[:6]),
            )

    if ctx.attempt_dir is not None and (Path(ctx.attempt_dir) / "coverage.md").is_file():
        cov = (Path(ctx.attempt_dir) / "coverage.md").read_text(encoding="utf-8")
        ids = set(re.findall(r"^\|\s*(4\.[1-6]\.[0-9])\s*\|", cov, re.M))
        missing = [b for b in BULLET_IDS if b not in ids]
        rep.check(
            "A03.coverage",
            not missing,
            "%d/%d spec bullets mapped" % (len(BULLET_IDS) - len(missing), len(BULLET_IDS))
            if not missing else "missing: " + ", ".join(missing),
        )
    else:
        rep.skip("A03.coverage", "coverage.md not found next to the harness")

    man_path = None if ctx.attempt_dir is None else Path(ctx.attempt_dir) / "manifest.json"
    if man_path is not None and man_path.is_file():
        probs = []
        try:
            man = json.loads(man_path.read_text(encoding="utf-8"))
        except Exception as exc:
            man = None
            probs.append("manifest.json is not valid JSON: %s" % exc)
        if man is not None:
            files = man.get("files") or {}
            artefact = man.get("artefact")
            if not files:
                probs.append("manifest records no files")
            if artefact and artefact not in files:
                probs.append("artefact %r is not listed in files" % artefact)
            for rel, sha in sorted(files.items()):
                p = Path(ctx.repo) / rel
                if not p.is_file():
                    probs.append("%s: missing" % rel)
                elif sha256_file(p) != sha:
                    probs.append("%s: sha256 %s != %s" % (rel, sha256_file(p)[:12], sha[:12]))
        rep.check("A12.manifest", not probs, "frozen hashes match" if not probs else "; ".join(probs[:6]))
    else:
        rep.skip("A12.manifest", "manifest not frozen yet (written at DO -> CHECK)")

    snap_path = None if ctx.attempt_dir is None else Path(ctx.attempt_dir) / "snapshot.json"
    if snap_path is not None and snap_path.is_file():
        try:
            snap = json.loads(snap_path.read_text(encoding="utf-8"))
        except Exception as exc:
            rep.check("A12.spec_hash", False, "snapshot.json is not valid JSON: %s" % exc)
            snap = None
        if snap is not None:
            probs = []
            for rel, sha in sorted((snap.get("documents") or {}).items()):
                if not sha:
                    continue
                p = Path(ctx.repo) / rel
                if not p.is_file():
                    probs.append("%s: missing" % rel)
                elif sha256_file(p) != sha:
                    probs.append("%s: sha256 changed" % rel)
            rep.check("A12.spec_hash", not probs, "spec bytes unchanged" if not probs else "; ".join(probs))
            inv = check_inventory(Path(ctx.repo), snap)
            if inv is None:
                rep.skip("A01.inventory", "git unavailable")
            else:
                rep.check(
                    "A01.inventory",
                    not inv,
                    "only allowed paths changed" if not inv else "; ".join(inv[:6]),
                )
    else:
        rep.skip("A12.spec_hash", "snapshot.json not found")
        rep.skip("A01.inventory", "snapshot.json not found")


# --------------------------------------------------------------------------- #
# Case: numeric
# --------------------------------------------------------------------------- #
def case_numeric(text, ctx, rep):
    try:
        blocks = parse_numeric_blocks(text)
    except DataFail as exc:
        rep.check(exc.cid, False, str(exc))
        return

    missing = [b for b in REQUIRED_BLOCKS if b not in blocks]
    rep.check(
        "A03.blocks",
        not missing,
        "9/9 required numeric blocks" if not missing else "missing: " + ", ".join(missing),
    )
    if missing:
        return

    schema_problems = []
    for bid in REQUIRED_BLOCKS:
        schema_problems += ["%s: %s" % (bid, p) for p in validate_block(bid, blocks[bid][0])]
    rep.check(
        "A02.schema",
        not schema_problems,
        "schema ok" if not schema_problems else "; ".join(schema_problems[:6]),
    )
    if schema_problems:
        return

    def B(bid):
        return Block(bid, blocks[bid][0])

    # --- specification -----------------------------------------------------
    d = B("design")
    mat = B("materials")
    egg_g = mat.num("mass_egg_g")
    pairs = {}
    for key in mat.rows:
        m = MATERIAL_RE.match(key)
        if m:
            pairs.setdefault(m.group(1), {})[m.group(2)] = key
    comp_ids = sorted(i for i, v in pairs.items() if {"name", "mass_g"} <= set(v))
    rep.check("A04.materials", len(comp_ids) >= 4, "%d declared components (>=4)" % len(comp_ids))
    names = [mat.text("mat%s_name" % i) for i in comp_ids]
    banned = [n for n in names if any(tok in n.lower() for tok in FORBIDDEN_NAME_TOKENS)]
    rep.check(
        "A04.forbidden_materials",
        not banned,
        "no forbidden material names" if not banned else "forbidden: " + ", ".join(banned),
    )
    comp_sum = sum(mat.num("mat%s_mass_g" % i) for i in comp_ids)
    total_g = d.num("mass_total_g")
    rep.check(
        "A05.mass_sum",
        abs(total_g - (comp_sum + egg_g)) <= 0.6,
        "total %.1f g vs egg+components %.1f g" % (total_g, comp_sum + egg_g),
    )
    rep.check("A05.mass_limit", 0 < total_g <= 500.0, "total mass %.1f g (limit 500 g)" % total_g)

    dims = {k: d.num(k) for k in ("dim_x_mm", "dim_y_mm", "dim_z_mm")}
    rep.check(
        "A05.dims",
        all(0 < v <= 300.0 for v in dims.values()),
        "dims %s mm (limit 300 mm per side)" % dims,
    )
    vol = d.num("volume_m3")
    bbox = 1.0
    for v in dims.values():
        bbox *= v / 1000.0
    rep.check(
        "A05.volume",
        0 < vol <= 0.020 and vol <= bbox * 1.01,
        "volume %.5f m3, bounding box %.5f m3, limit 0.02 m3" % (vol, bbox),
    )
    cost = d.num("cost_usd")
    rep.check("A05.cost", 0 <= cost <= 5.0, "cost $%.2f (limit $5.00)" % cost)
    asm = d.num("assembly_min")
    rep.check("A05.time", 0 < asm <= 30.0, "assembly %.0f min (limit 30 min)" % asm)

    c = B("constraints")
    rep.check("A04.egg_not_glued", c.num("egg_glued") == 0, "egg_glued=%d (0 required)" % c.num("egg_glued"))
    sides = c.num("protected_sides")
    rep.check("A04.all_sides", sides == 6, "protected_sides=%d (6 required)" % sides)
    travel = c.num("braking_travel_mm")
    rep.check(
        "A04.travel",
        20.0 <= travel <= min(dims.values()),
        "braking travel %.0f mm (>=20 mm and <= smallest dimension %.0f mm)" % (travel, min(dims.values())),
    )

    # --- impact ------------------------------------------------------------
    im = B("impact")
    H = im.num("H_m")
    g = im.num("g_m_s2")
    rho = im.num("rho_air_kg_m3")
    rep.check("A06.scenario", abs(H - 10.0) <= 0.1, "H=%.2f m (scenario A: 10.0 m)" % H)
    rep.check(
        "A06.constants",
        abs(g - 9.81) <= 0.02 and abs(rho - 1.225) <= 0.02,
        "g=%.3f m/s2, rho=%.4f kg/m3" % (g, rho),
    )
    m_imp = im.num("mass_total_g")
    rep.check(
        "A06.one_mass",
        abs(m_imp - total_g) <= 0.6,
        "impact mass %.1f g vs design mass %.1f g (one parameter set)" % (m_imp, total_g),
    )
    M = m_imp / 1000.0
    m_egg = egg_g / 1000.0

    mode = im.text("drag_mode").lower()
    if mode == "constant":
        cd = im.num("Cd")
        area = im.num("area_m2")
        rep.check("A06.drag_params", cd > 0 and area > 0, "Cd=%.3f, A=%.4f m2 (constant over the fall)" % (cd, area))
        cda_const = cd * area
        cda_fn = lambda t: cda_const
    elif mode == "deployment":
        delay = im.num("deploy_delay_s")
        cda0 = im.num("Cd_before") * im.num("area_before_m2")
        cda1 = im.num("Cd_after") * im.num("area_after_m2")
        rep.check(
            "A06.drag_params",
            delay >= 0 and cda0 >= 0 and cda1 > 0,
            "deployment model: delay %.3f s, CdA %.5f -> %.5f" % (delay, cda0, cda1),
        )
        cda_fn = lambda t: cda1 if t >= delay else cda0
    else:
        cda_fn = lambda t: 0.0

    v_control = math.sqrt(2.0 * g * H)
    rep.check(
        "A06.velocity_control",
        _close(im.num("v_control_m_s"), v_control, rel=0.015),
        "declared %.3f m/s vs sqrt(2gH)=%.3f m/s" % (im.num("v_control_m_s"), v_control),
    )
    t_sim, v_sim = simulate_fall(M, H, g, rho, cda_fn)
    v_imp = im.num("v_impact_m_s")
    rep.check(
        "A06.velocity_drag",
        _close(v_imp, v_sim, rel=0.02),
        "declared %.3f m/s vs integrated %.3f m/s (drag_mode=%s)" % (v_imp, v_sim, mode),
    )
    rep.check(
        "A06.velocity_order",
        0 < v_imp <= v_control * 1.001,
        "v_impact %.3f <= v_control %.3f m/s" % (v_imp, v_control),
    )
    rep.check(
        "A06.fall_time",
        _close(im.num("t_fall_s"), t_sim, rel=0.03),
        "declared %.3f s vs integrated %.3f s" % (im.num("t_fall_s"), t_sim),
    )

    E_k = 0.5 * M * v_imp * v_imp
    rep.check(
        "A07.energy",
        _close(im.num("E_k_J"), E_k, rel=0.02),
        "declared %.3f J vs 0.5*M*v^2 = %.3f J (M=%.3f kg)" % (im.num("E_k_J"), E_k, M),
    )
    rep.check(
        "A07.momentum",
        _close(im.num("p_kg_m_s"), M * v_imp, rel=0.01),
        "declared %.4f vs M*v = %.4f kg*m/s" % (im.num("p_kg_m_s"), M * v_imp),
    )

    # --- braking, forces, g-loads, gates ------------------------------------
    cr = B("criteria")
    eta = cr.num("eta")
    rep.check("A08.eta_range", 0 < eta < 1, "eta=%.4f" % eta)
    E_egg = cr.num("E_egg_J")
    rep.check(
        "A08.energy_to_egg",
        _close(E_egg, E_k * (1 - eta), rel=0.02),
        "declared %.4f J vs E_k*(1-eta) = %.4f J (eta is the declared efficiency)" % (E_egg, E_k * (1 - eta)),
    )
    E_crit = cr.num("E_crit_J")
    rep.check("A08.E_crit", abs(E_crit - 0.8) <= 0.005, "E_crit=%.3f J (primary conservative 0.8 J)" % E_crit)
    eta_req = 1.0 - E_crit / E_k
    rep.check(
        "A08.eta_required",
        abs(cr.num("eta_required") - eta_req) <= 0.002,
        "declared %.4f vs 1-E_crit/E_k = %.4f" % (cr.num("eta_required"), eta_req),
    )
    rep.check(
        "A08.gate_energy",
        E_egg < E_crit,
        "E_egg=%.4f J < E_crit=%.3f J; eta=%.4f vs required %.4f" % (E_egg, E_crit, eta, eta_req),
    )

    dt = cr.num("dt_brake_s")
    rep.check("A07.dt", 0 < dt < 1.0, "braking time %.4f s" % dt)
    a_avg = cr.num("a_avg_m_s2")
    rep.check(
        "A07.a_avg_impulse",
        _close(a_avg, v_imp / dt, rel=0.03),
        "declared %.1f m/s2 vs v/dt = %.1f m/s2" % (a_avg, v_imp / dt),
    )
    rep.check(
        "A07.brake_kinematics",
        _close(a_avg, v_imp * v_imp / (2.0 * travel / 1000.0), rel=0.03),
        "declared %.1f m/s2 vs v^2/(2*t) = %.1f m/s2 (t=%.0f mm)"
        % (a_avg, v_imp * v_imp / (2.0 * travel / 1000.0), travel),
    )
    pf = cr.num("peak_factor")
    rep.check("A07.peak_factor", pf >= 1.0, "peak factor %.3f (>=1, peak vs average stated)" % pf)
    a_peak = cr.num("a_peak_m_s2")
    rep.check(
        "A07.a_peak",
        _close(a_peak, a_avg * pf, rel=0.02),
        "declared %.1f m/s2 vs a_avg*peak_factor = %.1f m/s2" % (a_peak, a_avg * pf),
    )
    n_peak = cr.num("n_peak")
    rep.check(
        "A07.n_peak",
        _close(n_peak, a_peak / g, rel=0.02),
        "declared %.2f g vs a_peak/g = %.2f g" % (n_peak, a_peak / g),
    )
    n_crit = cr.num("n_crit")
    rep.check("A07.n_crit", abs(n_crit - 100.0) <= 0.5, "n_crit=%.1f g (operational reference 100 g)" % n_crit)
    rep.check(
        "A07.gate_dynamics",
        n_peak <= n_crit,
        "n_peak=%.2f g <= n_crit=%.1f g" % (n_peak, n_crit),
    )
    rep.check(
        "A07.F_egg",
        _close(cr.num("F_egg_peak_N"), m_egg * a_peak, rel=0.02),
        "declared %.2f N vs m_egg*a_peak = %.2f N (m_egg=%.3f kg; egg load, not M*a)"
        % (cr.num("F_egg_peak_N"), m_egg * a_peak, m_egg),
    )
    rep.check(
        "A07.F_sys_peak",
        _close(cr.num("F_sys_peak_N"), M * a_peak, rel=0.02),
        "declared %.2f N vs M*a_peak = %.2f N (system load)" % (cr.num("F_sys_peak_N"), M * a_peak),
    )
    rep.check(
        "A07.F_sys_avg",
        _close(cr.num("F_sys_avg_N"), M * v_imp / dt, rel=0.03),
        "declared %.2f N vs M*v/dt = %.2f N (average, not peak)" % (cr.num("F_sys_avg_N"), M * v_imp / dt),
    )
    dx = cr.num("brake_distance_mm")
    rep.check(
        "A07.brake_distance",
        _close(dx, v_imp * dt / 2.0 * 1000.0, rel=0.05),
        "declared %.1f mm vs v*dt/2 = %.1f mm" % (dx, v_imp * dt / 2.0 * 1000.0),
    )
    rep.check(
        "A07.travel_consistent",
        _close(dx, travel, rel=0.10),
        "brake distance %.1f mm vs declared travel %.0f mm" % (dx, travel),
    )
    dx_min = v_imp * v_imp / (2.0 * n_crit * g) * 1000.0
    rep.check(
        "A07.brake_min",
        travel >= dx_min * 0.95,
        "travel %.0f mm vs dx_min=%.1f mm at n_crit=%.0f g" % (travel, dx_min, n_crit),
    )
    marg_e = E_egg / E_crit
    marg_n = n_peak / n_crit
    binding = "energy" if marg_e > marg_n + 0.02 else ("dynamics" if marg_n > marg_e + 0.02 else "equal")
    rep.check(
        "A07.binding",
        cr.text("binding_gate").lower() == binding,
        "declared %r vs computed %r (margins energy %.3f, dynamics %.3f)"
        % (cr.text("binding_gate"), binding, marg_e, marg_n),
    )

    # --- sensitivity --------------------------------------------------------
    se = B("sensitivity")
    rep.check(
        "A08.sensitivity_crit",
        abs(se.num("E_crit_1_J") - 1.0) <= 0.005 and abs(se.num("E_crit_2_J") - 1.5) <= 0.005,
        "E_crit sensitivity 1.0 and 1.5 J",
    )
    rep.check(
        "A08.sensitivity_eta",
        abs(se.num("eta_required_1") - (1.0 - 1.0 / E_k)) <= 0.002
        and abs(se.num("eta_required_2") - (1.0 - 1.5 / E_k)) <= 0.002,
        "declared %.4f/%.4f vs %.4f/%.4f"
        % (se.num("eta_required_1"), se.num("eta_required_2"), 1.0 - 1.0 / E_k, 1.0 - 1.5 / E_k),
    )
    rep.check(
        "A07.sensitivity_n",
        abs(se.num("n_crit_sens") - 50.0) <= 0.5,
        "mandatory 50 g sensitivity: n_crit_sens=%.1f g" % se.num("n_crit_sens"),
    )

    # --- reliability --------------------------------------------------------
    rl = B("reliability")
    p1 = rl.num("p_single")
    p3 = rl.num("p_three")
    pmode = rl.text("p_mode").lower()
    rep.check("A09.p_range", 0 < p1 < 1 and 0 < p3 < 1, "p_single=%.3f, p_three=%.3f" % (p1, p3))
    if pmode == "independent":
        rep.check(
            "A09.p_three",
            abs(p3 - p1 ** 3) <= 0.005,
            "p_mode=independent: declared %.4f vs p^3 = %.4f" % (p3, p1 ** 3),
        )
    elif pmode in ("dependent", "damage"):
        rep.check(
            "A09.p_three",
            p3 < p1,
            "p_mode=%s: declared p_three %.4f < p_single %.4f" % (pmode, p3, p1),
        )
    else:
        rep.check("A09.p_three", False, "p_mode %r must be independent|dependent|damage" % pmode)

    # --- 20 m scenario ------------------------------------------------------
    s2 = B("scenario20")
    H2 = s2.num("H_m")
    rep.check("A10.h20", abs(H2 - 20.0) <= 0.1, "H=%.2f m for the 20 m scenario" % H2)
    m20 = s2.num("mass_total_g")
    rep.check("A05.mass_limit_20", 0 < m20 <= 500.0, "20 m variant mass %.1f g (limit 500 g)" % m20)
    vc20 = s2.num("v_control_m_s")
    rep.check(
        "A10.v20_control",
        _close(vc20, math.sqrt(2.0 * 9.81 * H2), rel=0.02),
        "declared %.2f m/s vs sqrt(2gH)=%.2f m/s" % (vc20, math.sqrt(2.0 * 9.81 * H2)),
    )
    v20 = s2.num("v_impact_m_s")
    rep.check("A10.v20", 0 < v20 <= vc20 * 1.001, "v_impact %.2f <= v_control %.2f m/s" % (v20, vc20))
    E20 = 0.5 * (m20 / 1000.0) * v20 * v20
    rep.check(
        "A10.Ek20",
        _close(s2.num("E_k_J"), E20, rel=0.02),
        "declared %.2f J vs 0.5*M*v^2 = %.2f J" % (s2.num("E_k_J"), E20),
    )
    eta20 = s2.num("eta")
    rep.check("A10.eta20", 0 < eta20 < 1, "eta(20 m)=%.4f" % eta20)
    Eegg20 = s2.num("E_egg_J")
    rep.check(
        "A10.energy20",
        _close(Eegg20, E20 * (1 - eta20), rel=0.02),
        "declared %.4f J vs E_k*(1-eta) = %.4f J" % (Eegg20, E20 * (1 - eta20)),
    )
    rep.check(
        "A10.scenario20_closes",
        Eegg20 < E_crit,
        "E_egg(20 m)=%.4f J < E_crit=%.3f J" % (Eegg20, E_crit),
    )

    # --- alternatives -------------------------------------------------------
    al = B("alternatives")
    alts = []
    for i in (1, 2, 3):
        keys = ["alt%d_mass_g" % i, "alt%d_cost_usd" % i, "alt%d_p_single" % i]
        present = sum(1 for k in keys if k in al.rows)
        if present == 3:
            alts.append(i)
        elif present:
            rep.check("A10.alt%d_complete" % i, False, "incomplete alternative %d" % i)
    rep.check("A10.alternatives", 2 <= len(alts) <= 3, "%d complete alternatives (2-3 required)" % len(alts))
    ok = True
    det = []
    for i in alts:
        mg = al.num("alt%d_mass_g" % i)
        cs = al.num("alt%d_cost_usd" % i)
        pp = al.num("alt%d_p_single" % i)
        good = 0 < mg <= 500 and 0 <= cs <= 5 and 0 < pp < 1
        ok = ok and good
        det.append("alt%d %.0f g / $%.2f / p=%.2f%s" % (i, mg, cs, pp, "" if good else " OUT OF LIMITS"))
    rep.check("A10.alt_limits", ok, "; ".join(det))


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
def _synth_blocks():
    """Synthetic, internally consistent scenario-A document (NOT the answer)."""
    return {
        "design": {
            "mass_total_g": "360",
            "dim_x_mm": "240",
            "dim_y_mm": "240",
            "dim_z_mm": "260",
            "volume_m3": "0.0140",
            "cost_usd": "3.75",
            "assembly_min": "22",
        },
        "materials": {
            "mass_egg_g": "60",
            "mat01_name": "cardboard", "mat01_mass_g": "120",
            "mat02_name": "foam", "mat02_mass_g": "80",
            "mat03_name": "plastic bag", "mat03_mass_g": "45",
            "mat04_name": "tape", "mat04_mass_g": "15",
            "mat05_name": "string", "mat05_mass_g": "10",
            "mat06_name": "cotton", "mat06_mass_g": "30",
        },
        "constraints": {
            "egg_glued": "0",
            "protected_sides": "6",
            "braking_travel_mm": "137",
        },
        "impact": {
            "H_m": "10.0",
            "g_m_s2": "9.81",
            "rho_air_kg_m3": "1.225",
            "mass_total_g": "360",
            "drag_mode": "constant",
            "Cd": "1.2",
            "area_m2": "0.0503",
            "v_control_m_s": "14.007",
            "v_impact_m_s": "9.127",
            "t_fall_s": "1.680",
            "E_k_J": "14.994",
            "p_kg_m_s": "3.286",
        },
        "criteria": {
            "eta": "0.965",
            "E_egg_J": "0.525",
            "E_crit_J": "0.8",
            "dt_brake_s": "0.030",
            "brake_distance_mm": "137",
            "peak_factor": "1.7",
            "a_avg_m_s2": "304.2",
            "a_peak_m_s2": "517.2",
            "n_peak": "52.7",
            "n_crit": "100",
            "F_egg_peak_N": "31.0",
            "F_sys_peak_N": "186.2",
            "F_sys_avg_N": "109.5",
            "eta_required": "0.9466",
            "binding_gate": "energy",
        },
        "sensitivity": {
            "E_crit_1_J": "1.0",
            "E_crit_2_J": "1.5",
            "eta_required_1": "0.9333",
            "eta_required_2": "0.9000",
            "n_crit_sens": "50",
        },
        "reliability": {
            "p_single": "0.92",
            "p_three": "0.779",
            "p_mode": "independent",
        },
        "scenario20": {
            "H_m": "20.0",
            "mass_total_g": "360",
            "v_control_m_s": "19.81",
            "v_impact_m_s": "9.693",
            "E_k_J": "16.912",
            "E_egg_J": "0.592",
            "eta": "0.965",
        },
        "alternatives": {
            "alt1_mass_g": "340", "alt1_cost_usd": "3.10", "alt1_p_single": "0.88",
            "alt2_mass_g": "420", "alt2_cost_usd": "4.40", "alt2_p_single": "0.90",
        },
    }


def build_doc(blocks, headings=None):
    parts = []
    for h in (headings if headings is not None else REQUIRED_HEADINGS):
        parts.append(
            h + "\n\nРаздел с формулой $E_k=\\frac{1}{2} m v^2$ и пояснением результатов.\n"
        )
    for bid in REQUIRED_BLOCKS:
        if bid not in blocks:
            continue
        parts.append("```numeric\n# block: %s" % bid)
        for key, val in blocks[bid].items():
            if isinstance(val, tuple):
                value, unit = val
            else:
                value, unit = val, _unit_for(bid, key)
            parts.append("%s | %s | %s" % (key, value, unit))
        parts.append("```\n")
    return "\n".join(parts)


def _eval_doc(text, case, ctx):
    rep = Report(case)
    try:
        if case == "structure":
            case_structure(text, ctx, rep)
        else:
            case_numeric(text, ctx, rep)
    except DataFail as exc:
        rep.check(exc.cid, False, str(exc))
    except CannotRun as exc:
        return EXIT_CANNOT, rep
    return final_rc(rep), rep


def run_selftest():
    ctx = Ctx()
    base = _synth_blocks()
    ok = 0
    bad = 0

    def expect(name, cond, detail=""):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("PASS %s — %s" % (name, detail))
        else:
            bad += 1
            print("FAIL %s — %s" % (name, detail))

    def mut():
        return copy.deepcopy(base)

    def rc_of(blocks=None, case="numeric", headings=None, text=None):
        doc = text if text is not None else build_doc(base if blocks is None else blocks, headings)
        return _eval_doc(doc, case, ctx)

    def expect_fail(name, cid, blocks=None, case="numeric", headings=None, text=None):
        rc, rep = rc_of(blocks=blocks, case=case, headings=headings, text=text)
        ids = [r[1] for r in rep.rows if r[0] == "FAIL"]
        expect(
            name,
            rc == EXIT_FAIL and cid in ids,
            "rc=%d expected %s, failing IDs: %s" % (rc, cid, ids[:5]),
        )

    # expected-positive: the synthetic document passes both cases
    rc, rep = rc_of(case="structure")
    expect("ST-01 positive structure", rc == EXIT_PASS and rep.nchecks > 0,
           "rc=%d checks=%d failed=%d" % (rc, rep.nchecks, rep.nfail))
    rc, rep = rc_of(case="numeric")
    expect("ST-02 positive numeric", rc == EXIT_PASS and rep.nchecks > 0,
           "rc=%d checks=%d failed=%d" % (rc, rep.nchecks, rep.nfail))
    expect("ST-03 positive numeric reports both gates",
           any(r[1] == "A08.gate_energy" and r[0] == "PASS" for r in rep.rows)
           and any(r[1] == "A07.gate_dynamics" and r[0] == "PASS" for r in rep.rows),
           "energy and dynamics gates both evaluated")

    # expected-negative: structure
    expect_fail("ST-10 NEG missing heading", "A02.headings", case="structure",
                headings=REQUIRED_HEADINGS[:-1])
    expect_fail("ST-11 NEG extra heading", "A02.headings", case="structure",
                headings=REQUIRED_HEADINGS + ["## 7. Лишнее"])
    expect_fail("ST-12 NEG renamed heading", "A02.headings", case="structure",
                headings=["## 1. Идея"] + REQUIRED_HEADINGS[1:])
    expect_fail("ST-13 NEG embedded script", "A02.no_script", case="structure",
                text=build_doc(base) + "\n```python\nprint(1)\n```\n")
    expect_fail("ST-14 NEG malformed row", "A02.schema", case="structure",
                text=build_doc(base).replace("eta | 0.965 | -", "eta | 0.965"))
    expect_fail("ST-15 NEG unknown block id", "A02.schema", case="structure",
                text=build_doc(base).replace("# block: criteria", "# block: kriterien"))
    expect_fail("ST-16 NEG empty document", "A02.headings", case="structure", text="")

    # expected-negative: numeric constraints
    b = mut(); b["design"]["mass_total_g"] = "361.5"
    expect_fail("ST-20 NEG mass sum", "A05.mass_sum", blocks=b)
    b = mut(); b["design"]["mass_total_g"] = "520"
    expect_fail("ST-21 NEG mass limit", "A05.mass_limit", blocks=b)
    b = mut(); b["design"]["dim_z_mm"] = "301"
    expect_fail("ST-22 NEG dimension limit", "A05.dims", blocks=b)
    b = mut(); b["design"]["volume_m3"] = "0.030"
    expect_fail("ST-23 NEG volume limit", "A05.volume", blocks=b)
    b = mut(); b["design"]["cost_usd"] = "5.50"
    expect_fail("ST-24 NEG cost limit", "A05.cost", blocks=b)
    b = mut(); b["design"]["assembly_min"] = "31"
    expect_fail("ST-25 NEG assembly limit", "A05.time", blocks=b)
    b = mut(); b["materials"]["mat01_name"] = "steel plate"
    expect_fail("ST-26 NEG forbidden material", "A04.forbidden_materials", blocks=b)
    b = mut(); b["constraints"]["egg_glued"] = "1"
    expect_fail("ST-27 NEG glued egg", "A04.egg_not_glued", blocks=b)
    b = mut(); b["constraints"]["protected_sides"] = "5"
    expect_fail("ST-28 NEG side protection", "A04.all_sides", blocks=b)
    b = mut(); b["constraints"]["braking_travel_mm"] = "60"
    expect_fail("ST-29 NEG travel vs brake distance", "A07.travel_consistent", blocks=b)

    # expected-negative: physics
    b = mut(); b["impact"]["mass_total_g"] = "500"
    expect_fail("ST-30 NEG mass basis substituted", "A06.one_mass", blocks=b)
    b = mut(); b["impact"]["v_impact_m_s"] = "12.5"
    expect_fail("ST-31 NEG wrong impact velocity", "A06.velocity_drag", blocks=b)
    b = mut(); b["impact"]["E_k_J"] = "20.0"
    expect_fail("ST-32 NEG wrong kinetic energy", "A07.energy", blocks=b)
    b = mut(); b["criteria"]["E_egg_J"] = "0.70"
    expect_fail("ST-33 NEG wrong energy to egg", "A08.energy_to_egg", blocks=b)
    b = mut(); b["criteria"]["eta"] = "0.90"; b["criteria"]["E_egg_J"] = "1.499"
    expect_fail("ST-34 NEG energy gate open", "A08.gate_energy", blocks=b)
    b = mut(); b["criteria"]["n_peak"] = "120.0"
    expect_fail("ST-35 NEG dynamics gate open", "A07.gate_dynamics", blocks=b)
    b = mut(); b["criteria"]["F_egg_peak_N"] = "186.2"
    expect_fail("ST-36 NEG egg force uses system mass", "A07.F_egg", blocks=b)
    b = mut(); b["criteria"]["binding_gate"] = "dynamics"
    expect_fail("ST-37 NEG wrong binding gate", "A07.binding", blocks=b)
    b = mut(); b["criteria"]["n_crit"] = "200"
    expect_fail("ST-38 NEG wrong operational threshold", "A07.n_crit", blocks=b)
    b = mut(); b["sensitivity"]["eta_required_2"] = "0.8500"
    expect_fail("ST-39 NEG wrong eta sensitivity", "A08.sensitivity_eta", blocks=b)

    # expected-negative: reliability, 20 m, alternatives, blocks
    b = mut(); b["reliability"]["p_three"] = "0.95"
    expect_fail("ST-40 NEG unjustified p^3", "A09.p_three", blocks=b)
    b = mut(); b["reliability"]["p_mode"] = "magic"
    expect_fail("ST-41 NEG unknown probability mode", "A09.p_three", blocks=b)
    b = mut(); b["scenario20"]["mass_total_g"] = "520"
    expect_fail("ST-42 NEG 20 m mass limit", "A05.mass_limit_20", blocks=b)
    b = mut(); b["scenario20"]["E_egg_J"] = "1.20"
    expect_fail("ST-43 NEG 20 m does not close", "A10.scenario20_closes", blocks=b)
    b = mut(); del b["criteria"]
    expect_fail("ST-44 NEG missing block", "A03.blocks", blocks=b)
    b = mut(); b["alternatives"] = {"alt1_mass_g": "340"}
    expect_fail("ST-45 NEG incomplete alternatives", "A10.alternatives", blocks=b)
    b = mut(); b["alternatives"]["alt2_cost_usd"] = "7.00"
    expect_fail("ST-46 NEG alternative over budget", "A10.alt_limits", blocks=b)

    # exit-2 paths: nothing selected / bad invocation / traversal
    expect("ST-50 NEG zero selected checks -> exit 2", final_rc(Report("numeric")) == EXIT_CANNOT,
           "final_rc(empty report)=2")
    empty_rep = Report("numeric")
    expect("ST-51 zero-check guard is exit 2 not a pass",
           final_rc(empty_rep) != EXIT_PASS, "rc=%d" % final_rc(empty_rep))

    def cli_rc(argv):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stderr(buf):
                return main(argv)
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else EXIT_CANNOT

    repo = str(Path.cwd())
    doc = "README.md"
    expect("ST-52 NEG unknown case -> exit 2",
           cli_rc(["--repo", repo, "--document", doc, "--case", "nope", "--read-only"]) == EXIT_CANNOT,
           "--case nope")
    expect("ST-53 NEG missing --document -> exit 2",
           cli_rc(["--repo", repo, "--case", "structure", "--read-only"]) == EXIT_CANNOT,
           "required argument dropped")
    expect("ST-54 NEG missing --read-only -> exit 2",
           cli_rc(["--repo", repo, "--document", doc, "--case", "structure"]) == EXIT_CANNOT,
           "required flag dropped")
    expect("ST-55 NEG path traversal -> exit 2",
           cli_rc(["--repo", repo, "--document", "../etc/passwd", "--case", "structure", "--read-only"]) == EXIT_CANNOT,
           "../etc/passwd rejected")
    expect("ST-56 NEG missing document -> exit 2",
           cli_rc(["--repo", repo, "--document", "no/such/file.md", "--case", "structure", "--read-only"]) == EXIT_CANNOT,
           "missing document rejected")

    rc = EXIT_PASS if bad == 0 else EXIT_FAIL
    print("RESULT %s checks=%d failed=%d exit=%d"
          % ("PASS" if rc == EXIT_PASS else "FAIL", ok + bad, bad, rc))
    return rc


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="recompute.py",
        description="Frozen verification harness for experiments/egg-drop/answer-a.md (scenario A).",
    )
    ap.add_argument("--repo", required=True, help="repository root (absolute)")
    ap.add_argument("--document", required=True, help="repo-relative document path")
    ap.add_argument("--case", required=True, choices=["structure", "numeric", "selftest"])
    ap.add_argument("--read-only", action="store_true", required=True,
                    help="required: the harness never writes; this flag proves intent")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print("CANNOT repository root is not a directory: %s" % args.repo, file=sys.stderr)
        return EXIT_CANNOT

    if args.case == "selftest":
        return run_selftest()

    rel = args.document
    parts = Path(rel).parts
    if Path(rel).is_absolute() or ".." in parts:
        print("CANNOT --document must be a repo-relative path without '..': %s" % rel, file=sys.stderr)
        return EXIT_CANNOT
    doc = repo / rel
    if not doc.is_file():
        print("CANNOT document not found: %s" % rel, file=sys.stderr)
        return EXIT_CANNOT
    try:
        text = doc.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print("CANNOT document is not valid UTF-8: %s" % exc, file=sys.stderr)
        return EXIT_CANNOT
    except OSError as exc:
        print("CANNOT cannot read document: %s" % exc, file=sys.stderr)
        return EXIT_CANNOT

    ctx = Ctx(repo=repo, document=doc, rel=rel, attempt_dir=Path(__file__).resolve().parent)
    rep = Report(args.case)
    try:
        if args.case == "structure":
            case_structure(text, ctx, rep)
        else:
            case_numeric(text, ctx, rep)
    except DataFail as exc:
        rep.check(exc.cid, False, str(exc))
    except CannotRun as exc:
        print("CANNOT %s" % exc, file=sys.stderr)
        return EXIT_CANNOT

    print("CASE %s | document %s | repo %s" % (args.case, rel, repo))
    for status, cid, detail in rep.rows:
        print("%-4s %s — %s" % (status, cid, detail))
    rc = final_rc(rep)
    verdict = "PASS" if rc == EXIT_PASS else ("FAIL" if rc == EXIT_FAIL else "CANNOT")
    print("RESULT %s checks=%d failed=%d exit=%d" % (verdict, rep.nchecks, rep.nfail, rc))
    return rc


if __name__ == "__main__":
    sys.exit(main())
