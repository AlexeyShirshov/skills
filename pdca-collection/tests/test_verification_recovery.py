"""Rendered-output regression tests for the pdca-collection recovery diagram.

These are *behavioral* tests over the real rendered artefacts: the harness copies
the generator into a `TemporaryDirectory`, executes it with `sys.executable`, and
the tests parse the produced SVG (`xml.etree.ElementTree`) and HTML.  Nothing is
imported from the generator and nothing is written into the live repository.

They prove the diagram/output structure only (routes, node references, tiers,
merge barrier, determinism, canvas fit).  They do **not** prove a live collection
integration run; that is a separate concern.

v2 (user-approved): collection verification `C` is the *standard* CHECK of the
per-task code contract (`pdca-coder`, or the identical `pdca-dotnet` base).  The
bespoke `TRIAGE` stage, the `BLOCKED` diagram state and the
conditional `C-fail` recovery panel are removed.  The expected contract is
literal: column `C` is owned by `check · medium` from the outset, carries the
four cheap measurement cards plus an always-run medium verdict card; the state
graph dispatches `FAIL` from `C` to the standard corrective `REPAIR` composition
by the orchestrator, returns via `REPAIR→C full-verification`, and re-gathers a
missing report through a `C→C re-gather` self-loop.

v3 (user hierarchy, supersedes the below-C card): the corrective `REPAIR · PDCA`
is a standalone **peer column** between `C · CHECK` and `E · ЭСКАЛАЦИЯ` -- same
header/frame baseline as the other phases -- wired directly to the top
orchestrator band by its own real dispatch (down) and result (up) bus arrows.
It is *not* a card below `C`, and `C` never launches it directly; the
`C→orchestrator→REPAIR` mediation stays visible.

Run:
    python3 -m unittest discover -s config/skills/pdca-collection/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
GEN = REPO / "config/skills/pdca-collection/assets/diagram/gen_collection.py"

THEME_STEMS = {
    "light": "collection-hand",
    "dark": "collection-hand-dark",
}
FILES = [
    "collection-hand.svg",
    "collection-hand.html",
    "collection-hand-dark.svg",
    "collection-hand-dark.html",
]

EXPECTED_NODE_IDS = {
    "START",
    "P",
    "DO",
    "MERGE",
    "C",
    "A",
    "EXIT",
    "REPAIR",
    "ESCALATE",
    # terminal unrecoverable corrective outcome (distinct from the successful
    # EXIT): the corrective revision exhausted with no actionable revised plan.
    "STOP",
}
RECOVERY_NODE_IDS = {"REPAIR", "STOP"}
KNOWN_TIERS = {"cheap", "medium", "strong"}

# Fix round 1: every in-scope text file must be whitespace-clean.  `git diff
# --check` does not cover untracked files (the whole diagram asset dir and the
# tests dir are untracked on this branch), so this scan is explicit and has no
# hidden suppressions.
IN_SCOPE_TEXT_FILES = [
    "config/skills/pdca-collection/assets/diagram/gen_collection.py",
    "config/skills/pdca-collection/tests/test_verification_recovery.py",
    "config/skills/pdca-collection/tests/scenarios.md",
    "config/skills/pdca-collection/SKILL.md",
    "config/agents/pdca-orchestrator.md",
    "config/skills/pdca-collection/assets/diagram/collection-hand.svg",
    "config/skills/pdca-collection/assets/diagram/collection-hand.html",
    "config/skills/pdca-collection/assets/diagram/collection-hand-dark.svg",
    "config/skills/pdca-collection/assets/diagram/collection-hand-dark.html",
]

# Step 5 mutation: remove the REPAIR->C full-verification edge from a *copied*
# generator source.  The tolerant pattern matches the tuple regardless of the
# whitespace the generator uses.
_MUTATE_REPAIR_TO_C = re.compile(
    r'\(\s*"REPAIR"\s*,\s*"C"\s*,\s*"full-verification"\s*\)\s*,?'
)

# v4 mutation: blank ONLY the *actual* C->REPAIR dispatch polyline points in the
# rendered SVG, leaving the bus group, its data-* attributes, the REPAIR card and
# the state-graph REPAIR node all intact.  If the assertions only looked at
# attributes this mutation would survive; they inspect real geometry, so it must
# be caught.
_MUTATE_REPAIR_DISPATCH_PTS = re.compile(
    r'(data-bus="dispatch" data-origin="C" data-target="REPAIR" '
    r'data-kind="dispatch">\s*<polyline points=")[^"]*(")'
)


def render_assets(generator_source: str | None = None) -> dict[str, str]:
    """Run the generator in a fresh temp dir and return the four outputs.

    ``generator_source`` is injected only by this test harness (default: the
    in-repo generator read from disk).  There is no environment variable or test
    hook in the generator itself, and the live repository is never written.
    """
    source = (
        generator_source
        if generator_source is not None
        else GEN.read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        gen = tmp_path / "gen_collection.py"
        gen.write_text(source, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(gen)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"generator exited {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )
        return {name: (tmp_path / name).read_text(encoding="utf-8") for name in FILES}


def parse_svg(svg: str) -> ET.Element:
    return ET.fromstring(svg.strip())


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _iter_local(root: ET.Element, name: str):
    return (e for e in root.iter() if _local(e.tag) == name)


def _groups(root: ET.Element):
    return _iter_local(root, "g")


def node_map(root: ET.Element) -> dict[str, dict]:
    """id -> {tier, element} for every rendered `<g data-node=...>`."""
    out: dict[str, dict] = {}
    for g in _groups(root):
        node_id = g.get("data-node")
        if node_id is not None:
            out[node_id] = {"tier": g.get("data-tier"), "element": g}
    return out


def edge_groups(root: ET.Element) -> list[ET.Element]:
    return [g for g in _groups(root) if g.get("data-from") is not None]


def edge_triples(root: ET.Element) -> set[tuple[str, str, str]]:
    return {
        (g.attrib["data-from"], g.attrib["data-to"], g.attrib.get("data-condition", ""))
        for g in edge_groups(root)
    }


def edge_pairs(root: ET.Element) -> set[tuple[str, str]]:
    return {(g.attrib["data-from"], g.attrib["data-to"]) for g in edge_groups(root)}


def _has_arrow_shape(group: ET.Element) -> bool:
    return any(child.tag.endswith(("path", "polyline")) for child in group.iter())


def _texts_with_class(group: ET.Element, cls: str) -> list[str]:
    return [
        (e.text or "").strip()
        for e in group.iter()
        if _local(e.tag) == "text" and e.get("class") == cls
    ]


def viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    parts = [float(v) for v in root.get("viewBox", "").split()]
    if len(parts) != 4:
        raise AssertionError("SVG viewBox missing/invalid")
    return parts[0], parts[1], parts[2], parts[3]


def polyline_points(group: ET.Element) -> list[tuple[float, float]]:
    """The real points of a group's arrow polyline (not detached metadata)."""
    for child in group.iter():
        if _local(child.tag) in ("polyline", "path"):
            pts = child.get("points")
            if pts:
                out: list[tuple[float, float]] = []
                for pt in pts.split():
                    x, y = pt.split(",")
                    out.append((float(x), float(y)))
                return out
    raise AssertionError("edge group has no polyline points")


def poly_segments(points: list[tuple[float, float]]):
    return list(zip(points, points[1:]))


def collinear_overlap(a, b) -> float:
    """Positive length shared by two collinear axis-aligned segments.

    Shared endpoints touch with zero length and are allowed; a positive overlap
    means the two routes are drawn on top of each other.
    """
    (ax1, ay1), (ax2, ay2) = a
    (bx1, by1), (bx2, by2) = b
    if ay1 == ay2 == by1 == by2:
        a_lo, a_hi = sorted((ax1, ax2))
        b_lo, b_hi = sorted((bx1, bx2))
        return min(a_hi, b_hi) - max(a_lo, b_lo)
    if ax1 == ax2 == bx1 == bx2:
        a_lo, a_hi = sorted((ay1, ay2))
        b_lo, b_hi = sorted((by1, by2))
        return min(a_hi, b_hi) - max(a_lo, b_lo)
    return 0.0


def group_visible_text(group: ET.Element) -> str:
    return " ".join((e.text or "") for e in group.iter() if _local(e.tag) == "text")


FAILURE_ROUTES = (
    ("C", "REPAIR", "FAIL"),
    ("REPAIR", "C", "full-verification"),
)
FORBIDDEN_SHORTCUTS = (("C", "DO"), ("C", "P"), ("C", "EXIT"))


def failure_route_problems(assets: dict[str, str]) -> list[str]:
    """Return a list of route violations for both themes (empty == good).

    Deliberately plain (no ``subTest``) so ``assertRaises(AssertionError)`` in
    the mutation check actually sees the failure instead of swallowing it.
    """
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        triples = edge_triples(root)
        pairs = edge_pairs(root)
        for required in FAILURE_ROUTES:
            if required not in triples:
                problems.append(f"{theme}: missing route {required}")
        for forbidden in FORBIDDEN_SHORTCUTS:
            if forbidden in pairs:
                problems.append(f"{theme}: forbidden shortcut {forbidden}")
    return problems


def bus_groups(root: ET.Element) -> list[ET.Element]:
    """Every rendered orchestrator dispatch/result bus group."""
    return [g for g in _groups(root) if g.get("data-bus") is not None]


def peer_column_groups(root: ET.Element) -> dict[str, ET.Element]:
    """data-column -> peer-column root group for every phase column."""
    out: dict[str, ET.Element] = {}
    for g in _groups(root):
        col = g.get("data-column")
        if col is not None:
            out[col] = g
    return out


def _first_rect(group: ET.Element) -> ET.Element | None:
    for child in group:
        if _local(child.tag) == "rect":
            return child
    return None


def _rect_with_attr(root: ET.Element, attr: str, value: str) -> ET.Element | None:
    for element in _iter_local(root, "rect"):
        if element.get(attr) == value:
            return element
    return None


def peer_header_rect(root: ET.Element, col: str) -> ET.Element | None:
    """The real header background rect of a peer column, read from the render."""
    for g in _groups(root):
        if g.get("data-peer-header") == col:
            return _first_rect(g)
    return None


def peer_frame_rect(root: ET.Element, col: str) -> ET.Element | None:
    return _rect_with_attr(root, "data-frame", col)


def _poly_has_arrow(group: ET.Element) -> bool:
    return any(
        _local(c.tag) in ("polyline", "path") and c.get("marker-end")
        for c in group.iter()
    )


def _single_bus_route(
    root: ET.Element, origin: str, target: str, kind: str
) -> list[ET.Element]:
    return [
        g
        for g in bus_groups(root)
        if g.get("data-origin") == origin
        and g.get("data-target") == target
        and g.get("data-kind") == kind
    ]


def polyline_point_lists(group: ET.Element) -> list[list[tuple[float, float]]]:
    """Real point lists of every arrow polyline inside a group."""
    out: list[list[tuple[float, float]]] = []
    for child in group.iter():
        if _local(child.tag) in ("polyline", "path"):
            pts = child.get("points")
            if pts:
                out.append(
                    [
                        (float(pt.split(",")[0]), float(pt.split(",")[1]))
                        for pt in pts.split()
                    ]
                )
    return out


def _point_near(a, b, tol: float = 0.5) -> bool:
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def _fnum(element: ET.Element, attr: str) -> float:
    value = element.get(attr)
    if value is None:
        raise AssertionError(f"missing numeric attribute {attr!r}")
    return float(value)


def main_peer_repair_problems(assets: dict[str, str]) -> list[str]:
    """Violations of the user hierarchy v4: REPAIR is a top-level sibling block
    on the corrective second row, centred under CHECK and wired to it by a real
    parent->child dispatch arrow plus a returning result arrow.  It must not be
    a card inside `C`, and `C` never reaches the band directly for it.
    Deliberately tolerant so an old render yields assertion text, not a parse
    error.
    """
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        cols = peer_column_groups(root)
        for col in ("P", "DO", "MERGE", "C", "REPAIR", "E", "A"):
            if col not in cols:
                problems.append(f"{theme}: no data-column={col} peer group")
        repair = cols.get("REPAIR")
        if repair is None:
            continue
        c_col = cols.get("C")
        e_col = cols.get("E")

        # 1. real top-level sibling root, not nested in C/E, not a node/edge
        if repair not in list(root):
            problems.append(f"{theme}: REPAIR group is not a top-level sibling")
        if c_col is not None and any(g is repair for g in c_col.iter()):
            problems.append(f"{theme}: REPAIR group is nested inside C")
        if e_col is not None and any(g is repair for g in e_col.iter()):
            problems.append(f"{theme}: REPAIR group is nested inside E")
        if repair.get("data-node") is not None:
            problems.append(f"{theme}: REPAIR peer group must not be data-node")
        if repair.get("data-main-recovery") != "corrective-pdca":
            problems.append(f"{theme}: REPAIR missing data-main-recovery=corrective-pdca")
        if repair.get("data-dispatched-by") != "orchestrator":
            problems.append(f"{theme}: REPAIR missing data-dispatched-by=orchestrator")
        if repair.get("data-composition") != "composite":
            problems.append(f"{theme}: REPAIR missing data-composition=composite")

        # 2. visible card: named PDCA, composite composition badge, named caller
        rtext = group_visible_text(repair)
        if "PDCA исправления" not in rtext:
            problems.append(f"{theme}: REPAIR has no visible 'PDCA исправления' card")
        if "составной" not in _texts_with_class(repair, "bm"):
            problems.append(f"{theme}: REPAIR card has no visible 'составной' badge")
        if "оркестратор" not in rtext.lower():
            problems.append(f"{theme}: REPAIR does not visibly name the orchestrator")

        # 3. second row: each corrective child hangs under its OWN parent, not
        # forced onto one shared horizontal baseline
        r_head = peer_header_rect(root, "REPAIR")
        r_frame = peer_frame_rect(root, "REPAIR")
        e_head = peer_header_rect(root, "E")
        e_frame = peer_frame_rect(root, "E")
        if r_head is None:
            problems.append(f"{theme}: REPAIR has no data-peer-header rect")
        if r_frame is None:
            problems.append(f"{theme}: REPAIR has no data-frame rect")
        if r_head is not None and e_head is not None:
            if _fnum(r_head, "y") == _fnum(e_head, "y"):
                problems.append(
                    f"{theme}: REPAIR and E share one top; each must sit "
                    f"under its own parent"
                )
        if r_frame is not None and e_frame is not None:
            rb = _fnum(r_frame, "y") + _fnum(r_frame, "height")
            eb = _fnum(e_frame, "y") + _fnum(e_frame, "height")
            if abs(rb - eb) > 0.5:
                problems.append(
                    f"{theme}: REPAIR bottom {rb} != E bottom {eb}; the "
                    f"corrective row must share one bottom edge"
                )
        for child, parent in CHILD_PARENT.items():
            c_head = peer_header_rect(root, child)
            p_head = peer_header_rect(root, parent)
            if c_head is None or p_head is None:
                continue
            if _fnum(c_head, "y") <= _fnum(p_head, "y"):
                problems.append(f"{theme}: {child} is not below its parent {parent}")

        # 4. real parent->child connector geometry against the REPAIR header
        if r_head is None:
            problems.append(f"{theme}: missing REPAIR header rect")
            continue
        h_top = _fnum(r_head, "y")
        disp = _single_bus_route(root, "C", "REPAIR", "dispatch")
        if len(disp) != 1:
            problems.append(
                f"{theme}: expected one C->REPAIR dispatch bus, got {len(disp)}"
            )
        else:
            routes = polyline_point_lists(disp[0])
            if len(routes) != 1:
                problems.append(f"{theme}: C->REPAIR dispatch has {len(routes)} polylines")
            elif abs(routes[0][-1][1] - h_top) > 0.5:
                problems.append(
                    f"{theme}: C->REPAIR dispatch does not end at REPAIR header {routes[0][-1]}"
                )
            if not _poly_has_arrow(disp[0]):
                problems.append(f"{theme}: C->REPAIR dispatch has no arrow marker")
            if "fail" not in group_visible_text(disp[0]).lower():
                problems.append(f"{theme}: C->REPAIR dispatch has no FAIL event label")
        res = _single_bus_route(root, "REPAIR", "C", "result")
        if len(res) != 1:
            problems.append(
                f"{theme}: expected one REPAIR->C result bus, got {len(res)}"
            )
        else:
            routes = polyline_point_lists(res[0])
            if len(routes) != 1:
                problems.append(f"{theme}: REPAIR->C result has {len(routes)} polylines")
            elif abs(routes[0][0][1] - h_top) > 0.5:
                problems.append(
                    f"{theme}: REPAIR->C result does not start at REPAIR header {routes[0][0]}"
                )
            if not _poly_has_arrow(res[0]):
                problems.append(f"{theme}: REPAIR->C result has no arrow marker")
            if group_visible_text(res[0]).strip():
                problems.append(f"{theme}: REPAIR->C reverse arrow must be uncaptioned")

        # 5. the launch is moved off the band: no orchestrator->REPAIR bus
        for g in bus_groups(root):
            if g.get("data-origin") == "orchestrator" and g.get("data-target") == "REPAIR":
                problems.append(f"{theme}: orchestrator->REPAIR band bus present")

        # 6. no old below-C corrective branch: C owns no PDCA card at all
        if c_col is not None:
            if any(g.get("data-main-recovery") for g in c_col.iter()):
                problems.append(f"{theme}: corrective-pdca still nested in C")
            if "PDCA исправления" in group_visible_text(c_col):
                problems.append(f"{theme}: C column still carries a below-C PDCA card")
    return problems


class VerificationRecoveryRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assets = render_assets()

    def _svg(self, theme: str) -> str:
        return self.assets[THEME_STEMS[theme] + ".svg"]

    # --- v2: standard CHECK owner, dispatch and re-gather ---------------

    def test_check_failure_is_dispatched_by_orchestrator(self):
        # ordinary route assertions + mutation sanity: dropping REPAIR->C in a
        # temporary copy must be rejected by the same assertions.  The repository
        # generator is never written; injection lives only in this harness.
        self.assertEqual([], failure_route_problems(self.assets))
        source = GEN.read_text(encoding="utf-8")
        mutated, replacements = _MUTATE_REPAIR_TO_C.subn("", source, count=1)
        self.assertEqual(replacements, 1, "mutation did not remove REPAIR->C")
        with self.assertRaises(AssertionError):
            self.assertEqual(
                [], failure_route_problems(render_assets(generator_source=mutated))
            )
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                by_pair = {
                    (g.get("data-from"), g.get("data-to")): g
                    for g in edge_groups(root)
                }
                self.assertIn(("C", "REPAIR"), by_pair)
                fail = by_pair[("C", "REPAIR")]
                self.assertEqual("FAIL", fail.get("data-condition"))
                self.assertEqual("orchestrator", fail.get("data-dispatched-by"))
                self.assertTrue(_has_arrow_shape(fail))
                fail_text = group_visible_text(fail)
                # exact new human phrase; the orchestrator dispatch is proven by
                # the metadata assertion above, not by this caption text.
                self.assertEqual(CHECK_FAIL_CAPTION, fail_text.strip())
                # the actual corrective return goes back to a *full* CHECK as an
                # uncaptioned reverse arrow
                self.assertIn(("REPAIR", "C"), by_pair)
                ret = by_pair[("REPAIR", "C")]
                self.assertEqual("full-verification", ret.get("data-condition"))
                self.assertEqual("", group_visible_text(ret).strip())
                self.assertTrue(_has_arrow_shape(ret))

    def test_missing_reports_regather_without_starting_repair(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                nodes = node_map(root)
                self.assertNotIn("TRIAGE", nodes)
                self.assertNotIn("BLOCKED", nodes)
                triples = edge_triples(root)
                self.assertIn(("C", "C", "re-gather"), triples)
                by_pair = {
                    (g.get("data-from"), g.get("data-to")): g
                    for g in edge_groups(root)
                }
                self.assertIn(("C", "C"), by_pair)
                loop = by_pair[("C", "C")]
                self.assertTrue(_has_arrow_shape(loop))
                loop_text = group_visible_text(loop)
                # a missing/invalid report is a blocked/awaiting-reports state,
                # never a code defect and never a REPAIR trigger
                self.assertIn("re-gather", loop_text)
                self.assertIn("blocked", loop_text)
                # the no-defect semantics is carried by the footer note (the
                # narrow C band entry only carries the short status)
                notes = " ".join(
                    _norm(e.text or "")
                    for e in _iter_local(root, "text")
                    if e.get("class") == "nt"
                )
                self.assertIn("не дефект", notes)
                self.assertIn("re-gather", notes)
                # a missing report is re-gathered, never routed into repair
                self.assertNotIn(("C", "REPAIR", "re-gather"), triples)
                self.assertNotIn(("C", "TRIAGE"), edge_pairs(root))

    def test_column_c_has_unconditional_medium_check(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                cols = [g for g in _groups(root) if g.get("data-column") == "C"]
                self.assertEqual(1, len(cols), "expected exactly one data-column=C group")
                col = cols[0]
                self.assertEqual("check", col.get("data-role"))
                self.assertEqual("medium", col.get("data-tier"))
                col_text = group_visible_text(col).lower()
                self.assertIn("check", col_text)
                self.assertIn("medium", col_text)
                # the four generic mandatory-check cards survive (task-typed,
                # not tied to any single technology) ...
                for needle in ("проверк", "тест", "производительн", "review"):
                    self.assertIn(needle, col_text)
                self.assertEqual(
                    4,
                    _texts_with_class(col, "bm").count("cheap"),
                    "column C must carry exactly four cheap measurement badges",
                )
                # ... the contradictory generic "Верификация · coder" card is gone
                self.assertNotIn("верификация", col_text)
                # the medium verdict is an always-run card with a visible badge
                verdict = [
                    g
                    for g in col.iter()
                    if _local(g.tag) == "g" and g.get("data-step") == "check-verdict"
                ]
                self.assertEqual(1, len(verdict), "no always-run check-verdict group")
                vg = verdict[0]
                self.assertEqual("check", vg.get("data-role"))
                self.assertEqual("medium", vg.get("data-tier"))
                vtext = group_visible_text(vg).lower()
                self.assertIn("вердикт", vtext)
                self.assertIn("check", vtext)
                self.assertIn("pass", vtext)
                self.assertIn("fail", vtext)
                self.assertIn("medium", _texts_with_class(vg, "bm"))
                # the obsolete conditional C-fail recovery panel is fully removed
                self.assertFalse(
                    any(
                        _local(g.tag) == "g" and g.get("data-recovery") == "C-fail"
                        for g in col.iter()
                    ),
                    "obsolete data-recovery=C-fail panel still present",
                )

    def test_main_diagram_shows_repair_as_peer_column(self):
        # User hierarchy (supersedes the earlier below-C card): REPAIR · PDCA is
        # a standalone peer column between C and E, wired straight to the
        # orchestrator band.  The earlier FAIL-direct-from-C / return-to-Build
        # expectations are explicitly obsolete.
        self.assertEqual([], main_peer_repair_problems(self.assets))

        # Name the break: blank ONLY the actual REPAIR orchestrator dispatch
        # polyline points, leaving the bus group, every data-* attribute, the
        # REPAIR card and the state-graph REPAIR node intact.  Attribute-only
        # checks would survive this; real-geometry checks must not.
        mutated = dict(self.assets)
        replacements = 0
        for stem in THEME_STEMS.values():
            new_svg, n = _MUTATE_REPAIR_DISPATCH_PTS.subn(
                r'\g<1>0,0 0,1"', mutated[stem + ".svg"], count=1
            )
            replacements += n
            mutated[stem + ".svg"] = new_svg
        self.assertEqual(
            len(THEME_STEMS),
            replacements,
            "mutation did not blank the REPAIR dispatch points",
        )
        with self.assertRaises(AssertionError):
            self.assertEqual([], main_peer_repair_problems(mutated))

        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                # the state graph still carries its own REPAIR node
                self.assertIn("REPAIR", node_map(root))
                cols = peer_column_groups(root)
                repair = cols["REPAIR"]
                c_col = cols["C"]
                e_col = cols["E"]
                # R is a top-level sibling, never nested in C/E
                self.assertIn(repair, list(root))
                self.assertFalse(any(g is repair for g in c_col.iter()))
                self.assertFalse(any(g is repair for g in e_col.iter()))
                # each corrective child hangs under its own parent trigger, not
                # on one shared horizontal baseline
                r_head = peer_header_rect(root, "REPAIR")
                r_frame = peer_frame_rect(root, "REPAIR")
                e_head = peer_header_rect(root, "E")
                e_frame = peer_frame_rect(root, "E")
                self.assertIsNotNone(r_head, "REPAIR header rect missing")
                self.assertIsNotNone(r_frame, "REPAIR frame rect missing")
                assert r_head is not None and r_frame is not None
                assert e_head is not None and e_frame is not None
                self.assertNotEqual(_fnum(r_head, "y"), _fnum(e_head, "y"))
                self.assertNotEqual(_fnum(r_frame, "y"), _fnum(e_frame, "y"))
                self.assertAlmostEqual(
                    _fnum(r_frame, "y") + _fnum(r_frame, "height"),
                    _fnum(e_frame, "y") + _fnum(e_frame, "height"),
                    delta=0.5,
                    msg="REPAIR and E must share one bottom edge",
                )
                for child, parent in CHILD_PARENT.items():
                    c_head = peer_header_rect(root, child)
                    p_head = peer_header_rect(root, parent)
                    self.assertIsNotNone(c_head, f"{child} header rect missing")
                    self.assertIsNotNone(p_head, f"{parent} header rect missing")
                    assert c_head is not None and p_head is not None
                    self.assertGreater(_fnum(c_head, "y"), _fnum(p_head, "y"))
                # visible named PDCA card: composite composition badge + caller
                self.assertIn("PDCA исправления", group_visible_text(repair))
                self.assertIn("составной", _texts_with_class(repair, "bm"))
                self.assertIn("оркестратор", group_visible_text(repair).lower())
                # parent->child connector: C->REPAIR dispatch + REPAIR->C return
                h_top = _fnum(r_head, "y")
                disp = _single_bus_route(root, "C", "REPAIR", "dispatch")
                res = _single_bus_route(root, "REPAIR", "C", "result")
                self.assertEqual(1, len(disp))
                self.assertEqual(1, len(res))
                disp_pts = polyline_point_lists(disp[0])[0]
                res_pts = polyline_point_lists(res[0])[0]
                self.assertTrue(_point_near(disp_pts[-1], (disp_pts[-1][0], h_top)))
                self.assertTrue(_point_near(res_pts[0], (res_pts[0][0], h_top)))
                self.assertTrue(_poly_has_arrow(disp[0]))
                self.assertTrue(_poly_has_arrow(res[0]))
                self.assertIn("fail", group_visible_text(disp[0]).lower())
                # reverse arrows are never captioned
                self.assertEqual("", group_visible_text(res[0]).strip())
                # the corrective launch is off the band: no orchestrator->REPAIR bus
                self.assertFalse(
                    any(
                        g.get("data-origin") == "orchestrator"
                        and g.get("data-target") == "REPAIR"
                        for g in bus_groups(root)
                    )
                )
                self.assertFalse(
                    any(g.get("data-main-recovery") for g in c_col.iter())
                )
                self.assertNotIn("PDCA исправления", group_visible_text(c_col))

    # --- preserved contract ---------------------------------------------

    def test_only_parent_pass_reaches_success(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                triples = edge_triples(root)
                self.assertIn(("C", "A", "PASS"), triples)
                self.assertIn(("A", "EXIT", "finalized"), triples)
                pairs = edge_pairs(root)
                self.assertNotIn(("C", "EXIT"), pairs)
                self.assertNotIn(("C", "DO"), pairs)
                self.assertNotIn(("C", "P"), pairs)
                self.assertNotIn(("REPAIR", "A"), pairs)
                self.assertNotIn(("REPAIR", "EXIT"), pairs)
                # the terminal corrective outcome is a real route to the distinct
                # STOP node, never to the successful ACT/EXIT
                self.assertIn(("REPAIR", "STOP"), pairs)
                self.assertNotIn(("STOP", "A"), pairs)
                self.assertNotIn(("STOP", "EXIT"), pairs)
                self.assertNotIn(("STOP", "C"), pairs)
                # STOP is a sink: no outgoing lower edge
                self.assertEqual(
                    set(),
                    {t for f, t in pairs if f == "STOP"},
                    "STOP must be terminal (no outgoing edge)",
                )
                # and STOP is not the successful EXIT
                self.assertNotEqual("EXIT", "STOP")
                self.assertIn("STOP", node_map(root))
                self.assertIn("EXIT", node_map(root))

    def test_rendered_routes_reference_existing_nodes(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                nodes = node_map(root)
                self.assertEqual(set(nodes), EXPECTED_NODE_IDS)
                groups = edge_groups(root)
                self.assertTrue(groups, "no rendered data-from arrow groups")
                for g in groups:
                    self.assertIn(g.get("data-from"), nodes)
                    self.assertIn(g.get("data-to"), nodes)
                    # the metadata must wrap a real arrow shape, not float alone
                    self.assertTrue(
                        _has_arrow_shape(g),
                        f'edge {g.get("data-from")}->{g.get("data-to")} has no path/polyline',
                    )

    def test_html_embeds_matching_svg_and_assets_are_deterministic(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                svg = self.assets[stem + ".svg"]
                # guard the parity claim against the pre-change (unrelated) render
                self.assertEqual(set(node_map(parse_svg(svg))), EXPECTED_NODE_IDS)
                self.assertIn(svg, self.assets[stem + ".html"])
        again = render_assets()
        self.assertEqual(again, self.assets)

    def test_layout_keeps_recovery_inside_canvas(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                nodes = node_map(root)
                for node_id in RECOVERY_NODE_IDS:
                    self.assertIn(node_id, nodes)
                _, _, width, height = viewbox(root)
                for node_id, data in nodes.items():
                    rect = next(
                        (c for c in data["element"] if _local(c.tag) == "rect"), None
                    )
                    self.assertIsNotNone(rect, f"node {node_id} has no box")
                    assert rect is not None
                    x, y = float(rect.attrib["x"]), float(rect.attrib["y"])
                    w, h = float(rect.attrib["width"]), float(rect.attrib["height"])
                    self.assertGreaterEqual(x, 0)
                    self.assertGreaterEqual(y, 0)
                    self.assertLessEqual(x + w, width + 0.5)
                    self.assertLessEqual(y + h, height + 0.5)
                # the footer/note text box must fit too (approximate text extent)
                note = next(
                    (
                        e
                        for e in _iter_local(root, "text")
                        if e.get("class") == "nt"
                    ),
                    None,
                )
                self.assertIsNotNone(note, "footer/note text missing")
                assert note is not None
                nx = float(note.attrib["x"])
                approx_w = len(note.text or "") * 5.3
                self.assertGreaterEqual(nx, 0)
                self.assertLessEqual(nx + approx_w, width)

    def test_merge_condition_and_roles_are_preserved(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                svg = self._svg(theme)
                root = parse_svg(svg)
                self.assertIn("\u2265""2", svg)  # merge conditional label "≥2"
                barrier = [
                    g
                    for g in _groups(root)
                    if g.get("data-condition") == "all-lanes-terminal"
                ]
                self.assertTrue(barrier, "merge barrier marker missing")
                nodes = node_map(root)
                tiers = {
                    d["tier"] for d in nodes.values() if d["tier"] is not None
                }
                self.assertTrue(tiers <= KNOWN_TIERS, f"invented tier: {tiers}")
                self.assertLessEqual({"cheap", "medium", "strong"}, tiers)
                # the verification owner keeps its visible medium tier on the
                # real C node (no separate TRIAGE node any more)
                self.assertEqual("medium", nodes["C"]["tier"])
                self.assertNotIn("TRIAGE", nodes)
                # the escalation role keeps its visible strong tier
                self.assertEqual("strong", nodes["ESCALATE"]["tier"])

    # --- fix round 1 regressions (preserved) ----------------------------

    def test_merge_barrier_has_visible_local_semantics(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self._svg(theme))
                barriers = [
                    g
                    for g in _groups(root)
                    if g.get("data-condition") == "all-lanes-terminal"
                ]
                self.assertEqual(1, len(barriers), "expected exactly one merge barrier")
                barrier = barriers[0]
                # the marker must carry a real, visible local label -- not only
                # a metadata attribute and an unqualified ">=2" somewhere else
                texts = [e for e in barrier.iter() if _local(e.tag) == "text"]
                self.assertTrue(texts, "merge barrier has no local visible label")
                text = group_visible_text(barrier)
                self.assertIn("\u2265""2", text)
                self.assertIn("ALL LANES TERMINAL", text.upper())
                low = text.lower()
                self.assertIn("done", low)
                self.assertIn("incomplete", low)
                # merge readiness is terminality; only successful (done) tips
                # merge and incomplete tips are skipped -- shown locally
                self.assertRegex(low, r"skip|пропуск|только\s+done")
                # a real visible shape backs the marker
                self.assertTrue(any(_local(c.tag) == "rect" for c in barrier))

    def test_recovery_routes_avoid_collinear_overlap(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self._svg(theme))
                by_pair = {
                    (g.get("data-from"), g.get("data-to")): g
                    for g in edge_groups(root)
                }
                self.assertIn(("C", "REPAIR"), by_pair)
                self.assertIn(("REPAIR", "C"), by_pair)
                fail_route = polyline_points(by_pair[("C", "REPAIR")])
                repair_route = polyline_points(by_pair[("REPAIR", "C")])
                problems = []
                for sa in poly_segments(fail_route):
                    for sb in poly_segments(repair_route):
                        overlap = collinear_overlap(sa, sb)
                        if overlap > 1e-9:
                            problems.append(f"{sa} overlaps {sb} by {overlap}")
                self.assertEqual(
                    [], problems, "recovery routes share a collinear segment"
                )
                # the forward FAIL route keeps its caption; the reverse route is
                # uncaptioned (reverse arrows are never labelled)
                fail_captions = [
                    (e.text or "").strip()
                    for e in by_pair[("C", "REPAIR")].iter()
                    if _local(e.tag) == "text"
                ]
                self.assertIn(CHECK_FAIL_CAPTION, fail_captions)
                self.assertEqual(
                    [],
                    [
                        (e.text or "").strip()
                        for e in by_pair[("REPAIR", "C")].iter()
                        if _local(e.tag) == "text" and (e.text or "").strip()
                    ],
                    "reverse REPAIR->C arrow must be uncaptioned",
                )

    def test_legend_separates_composition_from_model_tiers(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self._svg(theme))
                legends = {
                    g.get("data-legend"): g
                    for g in _groups(root)
                    if g.get("data-legend")
                }
                self.assertIn("model-tiers", legends)
                self.assertIn("composition", legends)
                model_low = group_visible_text(legends["model-tiers"]).lower()
                comp_low = group_visible_text(legends["composition"]).lower()
                for tier in ("cheap", "medium", "strong"):
                    self.assertIn(tier, model_low)
                # the composition marker is never an enumerated model tier
                self.assertNotIn("mixed", model_low)
                self.assertNotIn("составн", model_low)
                self.assertNotIn("композиц", model_low)
                self.assertIn("ступени модели", model_low)
                # the composition group is visibly labelled as composition
                self.assertTrue(
                    "композиц" in comp_low or "составн" in comp_low,
                    f"composition legend not labelled as composition: {comp_low!r}",
                )
                self.assertIn("pdca", comp_low)
                self.assertNotIn("ступень", comp_low)
                # the purple composition marker survives (non-tier wording)
                self.assertIn("составной", comp_low)
                for key in ("model-tiers", "composition"):
                    self.assertTrue(
                        any(_local(c.tag) == "rect" for c in legends[key]),
                        f"legend {key} has no swatch rect",
                    )

    def test_in_scope_text_files_have_clean_whitespace(self):
        problems = []
        for rel in IN_SCOPE_TEXT_FILES:
            path = REPO / rel
            self.assertTrue(path.exists(), f"missing in-scope file: {rel}")
            raw = path.read_bytes()
            if b"\r" in raw:
                problems.append(f"{rel}: CR byte found")
            if not raw.endswith(b"\n"):
                problems.append(f"{rel}: missing final newline")
            text = raw.decode("utf-8")
            body = text[:-1] if text.endswith("\n") else text
            for number, line in enumerate(body.split("\n"), 1):
                if line != line.rstrip(" \t"):
                    problems.append(f"{rel}:{number}: trailing whitespace")
        self.assertEqual([], problems)


# ---------------------------------------------------------------------------
# 2026-10-02 merge-retry follow-up (PHASE1 focused contract tests).
#
# Post-merge conflict: a *successful* `escalate` merge advice must return to the
# orchestrator, which re-dispatches the merge to `coder` (or the group tip is
# skipped as `incomplete`); `escalate`/strong never edits and never spawns
# `coder`.  The main diagram must show two real incoming MERGE dispatch routes
# (initial all-lanes-terminal + post-escalate retry/skip) and a labelled
# `E -> orchestrator` decision result; the lower state graph must expose an
# explicit MERGE node (10 nodes / 14 edges, including the terminal corrective
# STOP and the repeat-defect escalation) that both the conflict and the
# incomplete return flow through instead of
# jumping straight to `C`.
#
# These tests are written against the real rendered artefacts and the normative
# SKILL text; they must fail with an assertion (not a parse/import error) before
# the production change and pass after it.
# ---------------------------------------------------------------------------

SKILL_PATH = REPO / "config/skills/pdca-collection/SKILL.md"
LANE_PATH = REPO / "config/agents/pdca-orchestrator.md"
SCENARIOS_PATH = REPO / "config/skills/pdca-collection/tests/scenarios.md"

# Target lower merge model: node set and edge count are *counted from the
# render* in the tests, never read from a generator constant.
MERGE_GRAPH_NODE_IDS = {
    "START", "P", "DO", "MERGE", "C", "A", "EXIT",
    "REPAIR", "ESCALATE", "STOP",
}
MERGE_GRAPH_EDGE_COUNT = 14

# Tolerant condition/event-word families: the contract fixes the semantics, the
# implementation owns the exact prose.
_DO_MERGE_COND = re.compile(r"терминал|all[- _]?lanes|≥\s*2|>=\s*2", re.I)
_DO_C_COND = re.compile(r"одн[аоыу]|single|1\s*групп|без\s*merge|no\s*merge", re.I)
_MERGE_C_COND = re.compile(r"интеграц|integration|готов|заверш|merged?", re.I)
_MERGE_ESC_COND = re.compile(r"конфликт|conflict", re.I)
_ESC_MERGE_COND = re.compile(r"реш|перестав|reorder|совет|advice|заключ", re.I)
_INITIAL_EVENT = re.compile(r"все\s+групп|терминал|all[- _]?lanes|готов", re.I)
_RETRY_EVENT = re.compile(
    r"повтор|возобнов|re-?merge|retry|ретра|после\s+escalate|после\s+эскалац", re.I
)
_DECISION_EVENT = re.compile(r"решен|решени|decision|совет|заключ", re.I)


def _arrow_polyline_points(group: ET.Element) -> list[list[tuple[float, float]]]:
    """Real point lists of every *arrow* polyline (has marker-end) in a group."""
    out: list[list[tuple[float, float]]] = []
    for child in group.iter():
        if _local(child.tag) in ("polyline", "path") and child.get("marker-end"):
            pts = child.get("points")
            if pts:
                out.append(
                    [
                        (float(pt.split(",")[0]), float(pt.split(",")[1]))
                        for pt in pts.split()
                    ]
                )
    return out


def _all_text_labels(group: ET.Element) -> list[str]:
    return [
        (e.text or "").strip()
        for e in group.iter()
        if _local(e.tag) == "text" and (e.text or "").strip()
    ]


def _skill_section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    end = text.find(end_marker, start + len(start_marker))
    return text[start:] if end == -1 else text[start:end]


def _strong_is_advisory(low: str) -> bool:
    """True when an escalate/strong mention is windowed with a negated edit/spawn."""
    for m in re.finditer(r"escalate|strong|эскалац", low):
        window = low[max(0, m.start() - 260): m.end() + 260]
        if re.search(r"\bне\b", window) and re.search(
            r"правит|edit|write|запуска|исполн|спавн|spawn|меня", window
        ):
            return True
    return False


class MergeRetryContractTest(unittest.TestCase):
    """Real-render + normative-SKILL contract for the post-escalate merge retry."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.assets = render_assets()

    # --- main diagram: two real MERGE dispatch routes from the orchestrator ---

    def test_main_merge_has_one_dispatch_arrow_with_distinct_initial_and_retry_events(self):
        # Latest user correction supersedes the earlier "two physical MERGE
        # arrows" expectation: there is exactly ONE generic orchestrator->MERGE
        # dispatch path (one physical arrow), while the incoming events stay
        # distinct as visible labelled entries -- initial all-lanes-terminal and
        # the post-escalate retry (the partial/incomplete return is removed).
        initial = ("DO", "MERGE", "≥2 · all-lanes-terminal")
        retry = ("ESCALATE", "MERGE", "решено/переставить/пометить incomplete")
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                groups = _single_bus_route(root, "orchestrator", "MERGE", "dispatch")
                self.assertEqual(
                    1, len(groups), f"{theme}: expected one generic MERGE dispatch bus"
                )
                routes = [pts for g in groups for pts in _arrow_polyline_points(g)]
                self.assertEqual(
                    1,
                    len(routes),
                    f"{theme}: expected exactly one physical MERGE dispatch arrow "
                    f"(the events are labels, not extra arrows), got {len(routes)}",
                )
                self.assertTrue(
                    _poly_has_arrow(groups[0]),
                    f"{theme}: MERGE dispatch bus has no arrow marker",
                )
                entries = dispatch_event_entries(root)["MERGE"]
                self.assertEqual(
                    {initial, retry},
                    {_entry_triple(g) for g in entries},
                    f"{theme}: MERGE events are not the two distinct incoming edges",
                )
                for g in entries:
                    self.assertTrue(
                        group_visible_text(g).strip(),
                        f"{theme}: MERGE event entry has no visible text",
                    )

    def test_main_merge_dispatch_labels_distinguish_initial_and_retry(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                labels = [
                    t
                    for g in _single_bus_route(root, "orchestrator", "MERGE", "dispatch")
                    for t in _all_text_labels(g)
                ]
                self.assertTrue(labels, f"{theme}: MERGE dispatch routes carry no event label")
                self.assertTrue(
                    any(_INITIAL_EVENT.search(t) for t in labels),
                    f"{theme}: no initial all-lanes-terminal event label among {labels!r}",
                )
                self.assertTrue(
                    any(_RETRY_EVENT.search(t) for t in labels),
                    f"{theme}: no post-escalate retry event label among {labels!r}",
                )
                self.assertGreaterEqual(
                    len(set(labels)), 2, f"{theme}: MERGE dispatch event labels are not distinct"
                )

    def test_main_escalate_returns_to_merge_through_the_orchestrator(self):
        # User model: ESCALATE is a corrective block placed directly under MERGE,
        # wired by a parent->child dispatch (`merge-конфликт`) and a returning
        # result (the retry decision).  The retry stays orchestrator-mediated:
        # that is carried by data-dispatched-by, not by the orchestrator band.
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                disp = _single_bus_route(root, "MERGE", "E", "dispatch")
                self.assertEqual(
                    1, len(disp), f"{theme}: expected one MERGE->E dispatch bus"
                )
                self.assertTrue(
                    _poly_has_arrow(disp[0]),
                    f"{theme}: MERGE->E dispatch bus lost its arrow marker",
                )
                self.assertIn(
                    "merge fail", group_visible_text(disp[0]).lower()
                )
                res = _single_bus_route(root, "E", "MERGE", "result")
                self.assertEqual(1, len(res), f"{theme}: expected one E->MERGE result bus")
                self.assertTrue(
                    _poly_has_arrow(res[0]),
                    f"{theme}: E->MERGE result bus lost its arrow marker",
                )
                # reverse arrows are never captioned
                self.assertEqual("", group_visible_text(res[0]).strip())
                # mediated: never wired straight to the orchestrator band
                for kind, origin, target in (
                    ("dispatch", "orchestrator", "E"),
                    ("result", "E", "orchestrator"),
                ):
                    self.assertEqual(
                        [],
                        _single_bus_route(root, origin, target, kind),
                        f"{theme}: direct {origin}->{target} {kind} bus present",
                    )
                esc = [g for g in _groups(root) if g.get("data-column") == "E"]
                self.assertEqual(1, len(esc), f"{theme}: expected exactly one E block")
                self.assertEqual("orchestrator", esc[0].get("data-dispatched-by"))
                merge_cols = [g for g in _groups(root) if g.get("data-column") == "MERGE"]
                self.assertEqual(
                    1, len(merge_cols), f"{theme}: expected exactly one MERGE block"
                )

    # --- lower state graph: explicit MERGE node and mediated return ----------

    def test_lower_graph_exposes_merge_node_with_ten_nodes_fourteen_edges(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                nodes = node_map(root)
                self.assertEqual(
                    MERGE_GRAPH_NODE_IDS,
                    set(nodes),
                    f"{theme}: lower graph node set changed: {sorted(nodes)}",
                )
                self.assertEqual(10, len(nodes), f"{theme}: expected 10 lower nodes")
                edges = edge_groups(root)
                self.assertEqual(
                    MERGE_GRAPH_EDGE_COUNT,
                    len(edges),
                    f"{theme}: expected 14 lower edges, got {len(edges)}",
                )
                pairs = edge_pairs(root)
                self.assertIn(("DO", "MERGE"), pairs)
                self.assertIn(("DO", "C"), pairs)
                self.assertIn(("MERGE", "C"), pairs)
                cond = {
                    (g.get("data-from"), g.get("data-to")): g.get("data-condition", "")
                    for g in edges
                }
                self.assertRegex(cond[("DO", "MERGE")], _DO_MERGE_COND)
                self.assertRegex(cond[("DO", "C")], _DO_C_COND)
                self.assertRegex(cond[("MERGE", "C")], _MERGE_C_COND)
                # MERGE is the coder/cheap integration role, rendered like the column
                self.assertEqual("cheap", nodes["MERGE"]["tier"])
                self.assertIn("coder", group_visible_text(nodes["MERGE"]["element"]).lower())

    def test_escalate_returns_through_merge_not_bypass(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                by_pair = {
                    (g.get("data-from"), g.get("data-to")): g for g in edge_groups(root)
                }
                pairs = edge_pairs(root)
                # conflict lives on MERGE, not on DO, and never jumps to C directly
                self.assertIn(("MERGE", "ESCALATE"), pairs)
                self.assertNotIn(("DO", "ESCALATE"), pairs)
                self.assertNotIn(("ESCALATE", "C"), pairs)
                self.assertIn(("ESCALATE", "MERGE"), pairs)
                self.assertRegex(
                    by_pair[("MERGE", "ESCALATE")].get("data-condition", ""),
                    _MERGE_ESC_COND,
                )
                esc_merge = by_pair[("ESCALATE", "MERGE")]
                self.assertEqual(
                    "orchestrator",
                    esc_merge.get("data-dispatched-by"),
                    f"{theme}: ESCALATE->MERGE must be dispatched by the orchestrator",
                )
                self.assertRegex(esc_merge.get("data-condition", ""), _ESC_MERGE_COND)
                # INCOMPLETE node/returns are removed entirely; the escalate
                # decision (ESCALATE->MERGE) is the single return path.
                self.assertNotIn(("ESCALATE", "INCOMPLETE"), pairs)
                self.assertNotIn(("INCOMPLETE", "MERGE"), pairs)
                self.assertNotIn(("INCOMPLETE", "C"), pairs)
                self.assertNotIn("INCOMPLETE", node_map(root))
                incoming = {t for t in edge_triples(root) if t[1] == "MERGE"}
                self.assertEqual(
                    {
                        ("DO", "MERGE", "≥2 · all-lanes-terminal"),
                        ("ESCALATE", "MERGE", "решено/переставить/пометить incomplete"),
                    },
                    incoming,
                    f"{theme}: MERGE incoming edges changed: {sorted(incoming)}",
                )
                # the ESCALATE->MERGE visible label (on the MERGE dispatch bus)
                # carries the incomplete-skip alternative, not only the
                # resolve/reorder retry.  The lower reverse arrow itself stays
                # uncaptioned; the event word lives on the visible bus entry.
                retry_entry = next(
                    g
                    for g in dispatch_event_entries(root)["MERGE"]
                    if _entry_triple(g)
                    == ("ESCALATE", "MERGE", "решено/переставить/пометить incomplete")
                )
                esc_label = group_visible_text(retry_entry)
                self.assertRegex(
                    esc_label,
                    r"повтор|ре-?мерж|re-?merge|retry",
                    f"{theme}: ESCALATE->MERGE label lost the retry wording",
                )
                self.assertRegex(
                    esc_label,
                    r"incomplete|пропуск|skip",
                    f"{theme}: ESCALATE->MERGE label does not cover the incomplete skip",
                )

    # --- normative SKILL: retry sequence + strong is advisory only -----------

    def test_skill_mandates_escalate_merge_retry_via_orchestrator_and_coder(self):
        skill = SKILL_PATH.read_text(encoding="utf-8")
        low = skill.lower()
        section = _skill_section(skill, "### D —", "### C —")
        self.assertTrue(section, "SKILL.md §D (merge) section not found")
        # match the normative prose, not its markdown emphasis formatting
        section = section.replace("**", "").replace("`", "")
        problems = []
        if not re.search(r"escalat|эскалац", section, re.I):
            problems.append("§D does not name the escalate decision")
        if not re.search(r"coder", section, re.I):
            problems.append("§D does not name coder as the merge executor")
        if not re.search(r"оркестратор|orchestrator", section, re.I):
            problems.append("§D does not route the retry through the orchestrator")
        if not re.search(r"повтор|возобнов|re-?merge|remerge|retry|ретра", section, re.I):
            problems.append("§D has no repeated-merge (retry) instruction")
        if not re.search(r"остальн|очередн|pending|другие\s+групп", section, re.I):
            problems.append("§D does not continue with the remaining/pending groups")
        if not re.search(r"полн\w*\s+(check|c\b|верификац)", section, re.I):
            problems.append("§D does not return to the full C after the retry")
        self.assertEqual([], problems, f"{SKILL_PATH}: " + "; ".join(problems))
        self.assertTrue(
            _strong_is_advisory(low),
            "SKILL.md does not state that escalate/strong never edits or spawns coder",
        )


# ---------------------------------------------------------------------------
# 2026-10-02 dispatch-label consistency (PHASE1 focused contract tests).
#
# Latest user correction supersedes the "two physical MERGE arrows" rendering:
#   * exactly ONE generic orchestrator dispatch path (one physical polyline with
#     an arrow) per each of the seven peer blocks, plus ONE result return;
#   * its visible event labels come from the lower `STATE_EDGES`: every incoming
#     lower edge whose target aliases to the block becomes a separate visible
#     entry (`data-entry-from/to/condition`), rendered as real text and not only
#     as metadata attributes;
#   * the human label for an edge triple is central/shared -- where the lower
#     graph already shows it, the main entry must show the same string;
#   * `D · ПОДГОТОВКА` and `ЛЕЙН` are merged into ONE composite `DO` peer column
#     (single `P -> DO` input); the lower graph keeps one `DO` node and never a
#     `C -> DO` edge;
#   * `P` has no invented `re-plan` event (there is no such lower edge).
#
# These tests read the real rendered artefacts and the independent literal alias
# map below; the lower graph stays at ten nodes / fourteen edges (STOP and the
# repeat-defect escalation included) and the main entries must not pollute the
# `data-from` lower-edge selector.
# ---------------------------------------------------------------------------

# Independent MAIN -> LOWER alias map (written out; never imported from gen).
MAIN_TO_LOWER = {
    "P": "P", "DO": "DO", "MERGE": "MERGE",
    "C": "C", "REPAIR": "REPAIR", "E": "ESCALATE", "A": "A",
}
PEER_COLUMNS = ("P", "DO", "MERGE", "C", "REPAIR", "E", "A")
# top row (band-connected) vs the corrective second row (parent-connected)
ROW1_COLUMNS = ("P", "DO", "MERGE", "C", "A")
CHILD_PARENT = {"REPAIR": "C", "E": "MERGE"}
_LOWER_TO_MAIN: dict[str, list[str]] = {}
for _main, _lower in MAIN_TO_LOWER.items():
    _LOWER_TO_MAIN.setdefault(_lower, []).append(_main)

# Literal expected lower STATE_EDGES triples per main peer block.  Hand-derived
# from the fourteen canonical edges; the terminal `REPAIR -> STOP` edge and the
# only edge whose target is not a peer block (`A -> EXIT finalized`) are not
# incoming main events.
EXPECTED_INCOMING = {
    "P": {("START", "P", "старт")},
    "DO": {("P", "DO", "группы")},
    "MERGE": {
        ("DO", "MERGE", "≥2 · all-lanes-terminal"),
        ("ESCALATE", "MERGE", "решено/переставить/пометить incomplete"),
    },
    "C": {
        ("DO", "C", "одна группа · без merge"),
        ("MERGE", "C", "интеграция завершена"),
        ("REPAIR", "C", "full-verification"),
        ("C", "C", "re-gather"),
    },
    "REPAIR": {("C", "REPAIR", "FAIL")},
    "E": {
        ("MERGE", "ESCALATE", "merge-конфликт"),
        ("REPAIR", "ESCALATE", "повтор дефекта после 1 фикса"),
    },
    "A": {("C", "A", "PASS")},
}

# Shared central human labels for the triples the lower graph already renders
# visibly (literal copies of the existing lower captions).
# 2026-10-02 user correction: the shared `C -> REPAIR FAIL` display is the exact
# human phrase `CHECK fail · real defect` (the orchestrator dispatch is carried
# by the edge metadata `data-dispatched-by=orchestrator`; the wording makes it
# explicit that only a REAL defect opens the corrective PDCA, never re-gather).
CHECK_FAIL_CAPTION = "CHECK fail · real defect"
SHARED_LABELS = {
    ("DO", "C", "одна группа · без merge"): "одна группа: без MERGE",
    ("C", "REPAIR", "FAIL"): CHECK_FAIL_CAPTION,
    ("REPAIR", "C", "full-verification"): "REPAIR completed",
    ("C", "C", "re-gather"): "re-gather: blocked",
    ("MERGE", "ESCALATE", "merge-конфликт"): "MERGE fail",
    ("ESCALATE", "MERGE", "решено/переставить/пометить incomplete"):
        "ESCALATE: повтор MERGE или incomplete skip",
}

# Semantic fallback for triples the lower graph does not label visibly.
ENTRY_SEMANTICS = {
    ("START", "P", "старт"): re.compile(r"старт|start", re.I),
    ("P", "DO", "группы"): re.compile(r"групп|group", re.I),
    ("DO", "MERGE", "≥2 · all-lanes-terminal"): re.compile(
        r"терминал|all[- _]?lanes|≥\s*2|групп|barrier", re.I
    ),
    ("MERGE", "C", "интеграция завершена"): re.compile(
        r"интеграц|integration|заверш|готов", re.I
    ),
    ("C", "A", "PASS"): re.compile(r"pass|успех|gate", re.I),
}


def _norm(text: str) -> str:
    return " ".join(text.split())


def _entry_triple(g: ET.Element) -> tuple[str, str, str]:
    return (
        g.get("data-entry-from", ""),
        g.get("data-entry-to", ""),
        g.get("data-entry-condition", ""),
    )


def main_event_entry_groups(root: ET.Element) -> list[ET.Element]:
    return [g for g in _groups(root) if g.get("data-entry-from") is not None]


def dispatch_event_entries(root: ET.Element) -> dict[str, list[ET.Element]]:
    """main peer column -> its visible incoming-event entry groups.

    Entries are normally child groups of the column's generic dispatch bus, so
    the "one physical arrow, many labels" slot stays together.  A peer-level
    entry not nested anywhere is associated through its lower `data-entry-to`
    alias.
    """
    out: dict[str, list[ET.Element]] = {c: [] for c in PEER_COLUMNS}
    nested: set[int] = set()
    for bus in bus_groups(root):
        if bus.get("data-kind") != "dispatch":
            continue
        target = bus.get("data-target")
        if target not in out:
            continue
        for g in bus.iter():
            if g is bus or g.get("data-entry-from") is None:
                continue
            out[target].append(g)
            nested.add(id(g))
    for g in main_event_entry_groups(root):
        if id(g) in nested:
            continue
        for col in _LOWER_TO_MAIN.get(g.get("data-entry-to") or "", []):
            out[col].append(g)
    return out


def incoming_event_problems(assets: dict[str, str]) -> list[str]:
    """Main event triples must equal the alias-mapped lower incoming edges."""
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        incoming: dict[str, set[tuple[str, str, str]]] = {}
        for triple in edge_triples(root):
            incoming.setdefault(triple[1], set()).add(triple)
        entries = dispatch_event_entries(root)
        for col in PEER_COLUMNS:
            lower = MAIN_TO_LOWER[col]
            derived = set(incoming.get(lower, set()))
            if derived != EXPECTED_INCOMING[col]:
                problems.append(
                    f"{theme}: {col}: rendered lower incoming for {lower} "
                    f"{sorted(derived)} != literal {sorted(EXPECTED_INCOMING[col])}"
                )
            got = {_entry_triple(g) for g in entries[col]}
            if got != EXPECTED_INCOMING[col]:
                problems.append(
                    f"{theme}: {col}: main event triples {sorted(got)} != "
                    f"lower incoming {sorted(EXPECTED_INCOMING[col])}"
                )
            # main entries must not pollute the lower edge selector
            for g in entries[col]:
                if g.get("data-from") is not None or g.get("data-to") is not None:
                    problems.append(
                        f"{theme}: {col}: event entry uses data-from/data-to "
                        f"(pollutes the lower edge selector)"
                    )
    return problems


def event_text_problems(assets: dict[str, str]) -> list[str]:
    """Every event entry must carry real visible text with the right semantics."""
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        entries = dispatch_event_entries(root)
        for col in PEER_COLUMNS:
            for g in entries[col]:
                triple = _entry_triple(g)
                has_text_element = any(
                    _local(e.tag) == "text" and (e.text or "").strip()
                    for e in g.iter()
                )
                text = _norm(group_visible_text(g))
                if not text:
                    problems.append(f"{theme}: {col}: event {triple} has no visible text")
                    continue
                if not has_text_element:
                    problems.append(f"{theme}: {col}: event {triple} is attrs-only")
                shared = SHARED_LABELS.get(triple)
                if shared is not None:
                    if text != shared:
                        problems.append(
                            f"{theme}: {col}: event {triple} text {text!r} does not "
                            f"reuse the shared central label {shared!r}"
                        )
                else:
                    sem = ENTRY_SEMANTICS.get(triple)
                    if sem is not None and not sem.search(text):
                        problems.append(
                            f"{theme}: {col}: event {triple} text {text!r} "
                            f"fails semantics {sem.pattern!r}"
                        )
    return problems


def dispatch_bus_problems(assets: dict[str, str]) -> list[str]:
    """One physical dispatch arrow + one result arrow per peer block."""
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        band = _rect_with_attr(root, "data-band", "orchestrator")
        if band is None:
            problems.append(f"{theme}: orchestrator band rect missing")
            continue
        band_bottom = _fnum(band, "y") + _fnum(band, "height")
        entries = dispatch_event_entries(root)
        for col in PEER_COLUMNS:
            head = peer_header_rect(root, col)
            if head is None:
                problems.append(f"{theme}: {col}: data-peer-header rect missing")
                continue
            h_top = _fnum(head, "y")
            h_x = _fnum(head, "x")
            h_w = _fnum(head, "width")
            # row 1 blocks are dispatched straight from the orchestrator band;
            # the corrective row 2 blocks from their parent block instead.
            parent = CHILD_PARENT.get(col)
            disp_origin = parent if parent else "orchestrator"
            res_target = parent if parent else "orchestrator"
            disp = [
                g for g in bus_groups(root)
                if g.get("data-kind") == "dispatch"
                and g.get("data-origin") == disp_origin
                and g.get("data-target") == col
            ]
            if len(disp) != 1:
                problems.append(
                    f"{theme}: {col}: expected one dispatch bus from "
                    f"{disp_origin!r}, got {len(disp)}"
                )
            else:
                arrows = _arrow_polyline_points(disp[0])
                if len(arrows) != 1:
                    problems.append(
                        f"{theme}: {col}: dispatch bus has {len(arrows)} physical "
                        f"arrows, expected exactly one"
                    )
                else:
                    pts = arrows[0]
                    if abs(pts[-1][1] - h_top) > 0.5:
                        problems.append(
                            f"{theme}: {col}: dispatch end {pts[-1]} not at "
                            f"header-top {h_top}"
                        )
                    if not (h_x - 0.5 <= pts[-1][0] <= h_x + h_w + 0.5):
                        problems.append(
                            f"{theme}: {col}: dispatch port {pts[-1][0]} outside header"
                        )
                    if parent is None:
                        if abs(pts[0][1] - band_bottom) > 0.5:
                            problems.append(
                                f"{theme}: {col}: dispatch does not start at band "
                                f"bottom {band_bottom} ({pts[0]})"
                            )
                        if abs(pts[0][0] - pts[-1][0]) > 0.5:
                            problems.append(
                                f"{theme}: {col}: dispatch is not a single "
                                f"horizontal port"
                            )
                    elif pts[0][1] >= h_top:
                        problems.append(
                            f"{theme}: {col}: parent dispatch does not start above "
                            f"the child header ({pts[0]})"
                        )
            res = [
                g for g in bus_groups(root)
                if g.get("data-kind") == "result"
                and g.get("data-origin") == col
                and g.get("data-target") == res_target
            ]
            if len(res) != 1:
                problems.append(
                    f"{theme}: {col}: expected one result bus to {res_target!r}, "
                    f"got {len(res)}"
                )
            else:
                arrows = _arrow_polyline_points(res[0])
                if len(arrows) != 1:
                    problems.append(
                        f"{theme}: {col}: result bus has {len(arrows)} physical "
                        f"arrows, expected exactly one"
                    )
                else:
                    pts = arrows[0]
                    if abs(pts[0][1] - h_top) > 0.5:
                        problems.append(
                            f"{theme}: {col}: result does not start at header-top "
                            f"{h_top} ({pts[0]})"
                        )
                    if not (h_x - 0.5 <= pts[0][0] <= h_x + h_w + 0.5):
                        problems.append(
                            f"{theme}: {col}: result port {pts[0][0]} outside header"
                        )
                    if parent is None:
                        if abs(pts[-1][1] - band_bottom) > 0.5:
                            problems.append(
                                f"{theme}: {col}: result does not return to band "
                                f"bottom {band_bottom} ({pts[-1]})"
                            )
                        if abs(pts[0][0] - pts[-1][0]) > 0.5:
                            problems.append(
                                f"{theme}: {col}: result is not a single horizontal port"
                            )
                    elif pts[-1][1] >= h_top:
                        problems.append(
                            f"{theme}: {col}: parent result does not reach above "
                            f"the child header ({pts[-1]})"
                        )
            for g in entries[col]:
                if _arrow_polyline_points(g):
                    problems.append(
                        f"{theme}: {col}: event entry carries its own physical arrow "
                        f"(there must be one down path only)"
                    )
    return problems


_FORBIDDEN_EVENT_TEXT = {
    "P": re.compile(r"ре-?план|re-?plan", re.I),
    "C": re.compile(r"лейны\s+стоп", re.I),
}


def shadow_label_problems(assets: dict[str, str]) -> list[str]:
    """No stale hard-coded DISPATCH strings; event labels come from the edges."""
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        entries = dispatch_event_entries(root)
        # every visible label inside a dispatch bus must be backed by an entry
        for col in PEER_COLUMNS:
            entry_lines: set[str] = set()
            for g in entries[col]:
                entry_lines |= {_norm(t) for t in _all_text_labels(g) if _norm(t)}
            bus_lines: set[str] = set()
            for bus in bus_groups(root):
                if (
                    bus.get("data-kind") == "dispatch"
                    and bus.get("data-origin") == "orchestrator"
                    and bus.get("data-target") == col
                ):
                    bus_lines |= {_norm(t) for t in _all_text_labels(bus) if _norm(t)}
            extra = bus_lines - entry_lines
            if extra:
                problems.append(
                    f"{theme}: {col}: dispatch bus carries labels not backed by an "
                    f"edge entry: {sorted(extra)}"
                )
        for col, pattern in _FORBIDDEN_EVENT_TEXT.items():
            for g in entries[col]:
                text = group_visible_text(g)
                if pattern.search(text):
                    problems.append(f"{theme}: {col}: stale shadow dispatch label {text!r}")
        # never re-introduce an invented C -> DO edge or a P self-replan
        if ("C", "DO") in edge_pairs(root):
            problems.append(f"{theme}: invented lower C->DO edge present")
        if ("P", "P") in edge_pairs(root):
            problems.append(f"{theme}: invented lower P->P replan edge present")
    return problems


def composite_do_problems(assets: dict[str, str]) -> list[str]:
    """One DO column with all cards; no D/LANE columns/nodes; no C->DO edge."""
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        do_cols = [g for g in _groups(root) if g.get("data-column") == "DO"]
        if len(do_cols) != 1:
            problems.append(
                f"{theme}: expected exactly one data-column=DO, got {len(do_cols)}"
            )
        entries = dispatch_event_entries(root)
        got = {_entry_triple(g) for g in entries["DO"]}
        if got != EXPECTED_INCOMING["DO"]:
            problems.append(
                f"{theme}: DO incoming events {sorted(got)} != "
                f"{sorted(EXPECTED_INCOMING['DO'])}"
            )
        for col in ("D", "LANE"):
            if any(g.get("data-column") == col for g in _groups(root)):
                problems.append(f"{theme}: stale data-column={col} present")
        nodes = node_map(root)
        for node_id in ("D", "LANE"):
            if node_id in nodes:
                problems.append(f"{theme}: stale lower node {node_id} present")
        if ("C", "DO") in edge_pairs(root):
            problems.append(f"{theme}: invented C->DO lower edge present")
        for f, t in edge_pairs(root):
            if f in ("D", "LANE") or t in ("D", "LANE"):
                problems.append(f"{theme}: D/LANE leaked into the lower graph: {f}->{t}")
    return problems


def do_lane_subblock_problems(assets: dict[str, str]) -> list[str]:
    """DO: 3 top-level cards + 3 nested lane sub-blocks shifted right + loop label."""
    problems: list[str] = []
    top_titles = ("Worktree + ветки", "Запуск лейнов", "Лейн · группа")
    child_titles = (
        "Ветка задачи",
        "pdca-цикл · continue from saved PLAN",
        "DO→CHECK→ACT",
        "Коммит · если разрешён автокоммит",
    )
    expected_titles = set(top_titles + child_titles)
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        cols = [g for g in _groups(root) if g.get("data-column") == "DO"]
        if len(cols) != 1:
            problems.append(f"{theme}: expected exactly one DO column, got {len(cols)}")
            continue
        col = cols[0]
        title_x: dict[str, float] = {}
        for e in col.iter():
            if _local(e.tag) == "text" and e.get("class") == "t":
                x = e.get("x")
                if x is not None:
                    title_x.setdefault((e.text or "").strip(), float(x))
        missing = [t for t in expected_titles if t not in title_x]
        if missing:
            problems.append(f"{theme}: DO card titles missing {missing!r}")
            continue
        unexpected = sorted(set(title_x) - expected_titles)
        if unexpected:
            problems.append(f"{theme}: unexpected DO card titles {unexpected!r}")
        if len(title_x) != len(expected_titles):
            problems.append(
                f"{theme}: DO has {len(title_x)} card titles, expected "
                f"{len(expected_titles)}"
            )
        if "Следующая" in title_x:
            problems.append(f"{theme}: removed DO card 'Следующая' still rendered")
        top_x = {title_x[t] for t in top_titles}
        child_x = {title_x[t] for t in child_titles}
        if len(top_x) != 1:
            problems.append(f"{theme}: top-level DO cards not aligned: {sorted(top_x)}")
        if len(child_x) != 1:
            problems.append(f"{theme}: lane sub-blocks not aligned: {sorted(child_x)}")
        if not min(child_x) > max(top_x):
            problems.append(
                f"{theme}: lane sub-blocks not indented (child_x={sorted(child_x)} "
                f"<= parent_x={sorted(top_x)})"
            )
        loop = any(
            _local(e.tag) == "text"
            and (e.text or "").strip() == "следующая задача"
            for e in col.iter()
        )
        if not loop:
            problems.append(f"{theme}: DO lane loop-back label missing")
        # the loop-back is task-to-task inside one lane; the stale group-branch
        # wording must not reappear
        if any(
            _local(e.tag) == "text"
            and "ветка группы" in (e.text or "")
            for e in col.iter()
        ):
            problems.append(f"{theme}: stale 'ветка группы' DO loop label present")
    return problems


def _parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def _find_event_entry(root: ET.Element, target: tuple[str, str, str]):
    for g in main_event_entry_groups(root):
        if _entry_triple(g) == target:
            return g
    return None


class DispatchLabelConsistencyTest(unittest.TestCase):
    """Real-render contract: one dispatch path per block, events from the edges."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.assets = render_assets()

    def test_each_peer_block_has_one_dispatch_and_one_result_arrow(self):
        self.assertEqual([], dispatch_bus_problems(self.assets))

    def test_main_events_match_all_lower_incoming_edges(self):
        self.assertEqual([], incoming_event_problems(self.assets))

    def test_main_event_texts_are_visible_and_semantic(self):
        # Precondition: every peer block must carry its event entries; the text
        # contract below is then non-vacuous (an absent entry cannot be "fine").
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                entries = dispatch_event_entries(parse_svg(self.assets[stem + ".svg"]))
                for col in PEER_COLUMNS:
                    self.assertTrue(entries[col], f"{theme}: {col} has no event entries")
        self.assertEqual([], event_text_problems(self.assets))

    def test_known_c4_and_m2_events_are_explicit(self):
        # C carries all four incoming lower edges, MERGE all two -- read from the
        # render itself, independent of the generator constants.
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                entries = dispatch_event_entries(root)
                self.assertEqual(
                    EXPECTED_INCOMING["C"], {_entry_triple(g) for g in entries["C"]}
                )
                self.assertEqual(4, len(entries["C"]))
                self.assertEqual(
                    EXPECTED_INCOMING["MERGE"],
                    {_entry_triple(g) for g in entries["MERGE"]},
                )
                self.assertEqual(2, len(entries["MERGE"]))
                for col in ("C", "MERGE"):
                    for g in entries[col]:
                        self.assertTrue(group_visible_text(g).strip())

    def test_do_is_one_column_with_all_cards_and_single_p_input(self):
        self.assertEqual([], composite_do_problems(self.assets))

    def test_do_lane_subblocks_are_nested_under_lane_parent(self):
        self.assertEqual([], do_lane_subblock_problems(self.assets))

    def test_no_stale_replan_or_resource_shadow_labels(self):
        self.assertEqual([], shadow_label_problems(self.assets))

    def test_lower_graph_stays_ten_nodes_fourteen_edges_without_pollution(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                self.assertEqual(MERGE_GRAPH_NODE_IDS, set(node_map(root)))
                self.assertEqual(MERGE_GRAPH_EDGE_COUNT, len(edge_groups(root)))
                self.assertTrue(
                    main_event_entry_groups(root),
                    f"{theme}: no main event entries to guard the lower selector",
                )
                for g in main_event_entry_groups(root):
                    self.assertIsNone(g.get("data-from"))
                    self.assertIsNone(g.get("data-to"))

    def test_missing_event_entry_is_caught(self):
        # Drop one entry (the C->C re-gather) from a parsed render while keeping
        # the bus, the arrow and every other attribute: the triple-set equality
        # must reject it.
        mutated = dict(self.assets)
        for theme, stem in THEME_STEMS.items():
            root = parse_svg(self.assets[stem + ".svg"])
            entry = _find_event_entry(root, ("C", "C", "re-gather"))
            self.assertIsNotNone(entry, f"{theme}: C->C re-gather entry missing")
            assert entry is not None
            parent = _parent_map(root)[entry]
            parent.remove(entry)
            mutated[stem + ".svg"] = ET.tostring(root, encoding="unicode")
        with self.assertRaises(AssertionError):
            self.assertEqual([], incoming_event_problems(mutated))

    def test_blank_event_text_is_caught(self):
        # Blank only the visible text of one entry, keeping data-entry-* attrs
        # and the physical arrow: attributes-only checks would survive; the
        # visible-text assertion must not.
        mutated = dict(self.assets)
        for theme, stem in THEME_STEMS.items():
            root = parse_svg(self.assets[stem + ".svg"])
            entry = _find_event_entry(root, ("C", "C", "re-gather"))
            self.assertIsNotNone(entry, f"{theme}: C->C re-gather entry missing")
            assert entry is not None
            for el in entry.iter():
                if _local(el.tag) == "text":
                    el.text = ""
            mutated[stem + ".svg"] = ET.tostring(root, encoding="unicode")
        with self.assertRaises(AssertionError):
            self.assertEqual([], event_text_problems(mutated))


# ---------------------------------------------------------------------------
# 2026-10-02 diagram caption polish (user-approved cosmetic correction).
#
# The user supersedes four visible labels of the recovery diagram:
#   * outgoing "result" arrows (block -> orchestrator) are NOT captioned at all
#     (the real arrow and its endpoints stay);
#   * the corrective return reads the exact lowercase English phrase
#     "repair completed" in both the main incoming entry and the lower caption,
#     while the `full-verification` condition metadata is unchanged;
#   * the strong block is named the exact uppercase word "ESCALATE" in the master
#     E phase header and on the lower state-graph node (both one line), while the
#     descriptive Russian phrase "Разрешение конфликтов слияния" is rendered on
#     the body card and the orchestrator band input; the internal `ESCALATE` id
#     and the `strong` tier are kept; the legend agent id remains lowercase
#     `escalate` (a different, untouched token);
#   * the shared `C -> REPAIR FAIL` display reads the exact phrase
#     "CHECK FAIL" (main incoming entry + lower caption), while the real
#     orchestrator dispatch stays proven by `data-dispatched-by=orchestrator`.
#
# Single-source rule: the orchestrator band ENUMERATES ALL incoming events per
# phase, and the main event arrows and the lower captions all derive from one
# canonical `EDGE_LABELS` map, so their event wording and count cannot drift
# (`orchestrator_trigger_sync_problems`).
#
# These read the real rendered artefacts only (estimated text bounds, no glyph
# or pixel claim).
# ---------------------------------------------------------------------------

ESCALATE_LABEL = "ESCALATE"
# Descriptive name restored on the body card and the band input.
ESCALATE_BODY_NAME = "Разрешение конфликтов слияния"
REPAIR_COMPLETED_CAPTION = "REPAIR completed"
# 2026-10-02 user correction: the MAIN C column no longer renders the visible
# owner label under its header; the lower state-graph `C` node keeps its owner
# label and its `medium` tier.
C_OWNER_LABEL = "check · medium"

_TEXT_CW = {"h": 7.0, "t": 7.4, "st": 7.6, "ol": 6.3}


def _est_text_width(text: str, cls: str) -> float:
    return len(text) * _TEXT_CW.get(cls, 7.0)


def result_bus_problems(assets: dict[str, str]) -> list[str]:
    """Every reverse arrow is a real, uncaptioned arrow: row-1
    ``block -> orchestrator`` results and the row-2 ``child -> parent`` returns
    alike (the return event is listed as an incoming event of the parent)."""
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        results = [
            g for g in bus_groups(root)
            if g.get("data-kind") == "result"
            and g.get("data-origin") in ROW1_COLUMNS
        ]
        if len(results) != len(ROW1_COLUMNS):
            problems.append(
                f"{theme}: expected {len(ROW1_COLUMNS)} orchestrator result buses, "
                f"got {len(results)}"
            )
        for g in results:
            origin = g.get("data-origin")
            text = group_visible_text(g).strip()
            if text:
                problems.append(f"{theme}: {origin} result bus is labelled {text!r}")
            arrows = _arrow_polyline_points(g)
            if len(arrows) != 1:
                problems.append(
                    f"{theme}: {origin} result bus has {len(arrows)} physical "
                    f"arrows, expected exactly one"
                )
        for child, parent in CHILD_PARENT.items():
            res = [
                g for g in bus_groups(root)
                if g.get("data-kind") == "result"
                and g.get("data-origin") == child
                and g.get("data-target") == parent
            ]
            if len(res) != 1:
                problems.append(
                    f"{theme}: {child}: expected one result bus to {parent!r}, "
                    f"got {len(res)}"
                )
                continue
            text = group_visible_text(res[0]).strip()
            if text:
                problems.append(
                    f"{theme}: {child}->{parent} reverse arrow is labelled {text!r}"
                )
            if len(_arrow_polyline_points(res[0])) != 1:
                problems.append(
                    f"{theme}: {child}->{parent} return has no single physical arrow"
                )
    return problems


def repair_completed_problems(assets: dict[str, str]) -> list[str]:
    """REPAIR->C reads exactly 'repair completed'; the condition metadata stays."""
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        by_pair = {
            (g.get("data-from"), g.get("data-to")): g for g in edge_groups(root)
        }
        ret = by_pair.get(("REPAIR", "C"))
        if ret is None:
            problems.append(f"{theme}: no lower REPAIR->C edge")
        else:
            if ret.get("data-condition") != "full-verification":
                problems.append(
                    f"{theme}: REPAIR->C condition {ret.get('data-condition')!r} "
                    f"!= 'full-verification'"
                )
            got = _norm(group_visible_text(ret))
            if got:
                problems.append(
                    f"{theme}: reverse REPAIR->C edge must be uncaptioned, got {got!r}"
                )
        entry = _find_event_entry(root, ("REPAIR", "C", "full-verification"))
        if entry is None:
            problems.append(f"{theme}: no main C entry for REPAIR->C full-verification")
        else:
            got = _norm(group_visible_text(entry))
            if got != REPAIR_COMPLETED_CAPTION:
                problems.append(
                    f"{theme}: main REPAIR->C entry text {got!r} != "
                    f"{REPAIR_COMPLETED_CAPTION!r}"
                )
    return problems


def escalation_name_problems(assets: dict[str, str]) -> list[str]:
    """Header/node 'ESCALATE'; body card descriptive (the block moved to the
    corrective second row, so its descriptive name no longer sits in the band)."""
    problems: list[str] = []
    phrase = ESCALATE_BODY_NAME
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])

        # 1. master peer header: exact uppercase word, single line that fits
        header_group = next(
            (g for g in _groups(root) if g.get("data-peer-header") == "E"), None
        )
        head_rect = peer_header_rect(root, "E")
        if header_group is None or head_rect is None:
            problems.append(f"{theme}: E header group/rect missing")
        else:
            head_text = _norm(group_visible_text(header_group))
            if head_text != ESCALATE_LABEL:
                problems.append(
                    f"{theme}: E header {head_text!r} != {ESCALATE_LABEL!r}"
                )
            lines = _texts_with_class(header_group, "h")
            if len(lines) != 1:
                problems.append(
                    f"{theme}: E header must be a single line (got {lines!r})"
                )
            head_w = _fnum(head_rect, "width")
            for line in lines:
                if _est_text_width(line, "h") > head_w + 0.5:
                    problems.append(
                        f"{theme}: header line {line!r} exceeds header width {head_w}"
                    )

        # 2. main body card: descriptive wrapped title + strong badge retained
        e_cols = [g for g in _groups(root) if g.get("data-column") == "E"]
        if len(e_cols) != 1:
            problems.append(f"{theme}: expected exactly one E column, got {len(e_cols)}")
        else:
            col = e_cols[0]
            body_lines = _texts_with_class(col, "t")
            if phrase not in _norm(" ".join(body_lines)):
                problems.append(
                    f"{theme}: E body title {body_lines!r} does not name {phrase!r}"
                )
            if "strong" not in _texts_with_class(col, "bm"):
                problems.append(f"{theme}: E block lost its visible strong badge")
            frame = peer_frame_rect(root, "E")
            if frame is not None:
                box_w = _fnum(frame, "width") - 12  # box width == frame width - 12
                avail = box_w - 77  # visible badge (50) + paddings, as box() lays out
                for line in body_lines:
                    if _est_text_width(line, "t") > avail + 0.5:
                        problems.append(
                            f"{theme}: body title line {line!r} exceeds available "
                            f"width {avail}"
                        )

        # 3. lower state node: same name as the master header, strong tier kept
        node = node_map(root).get("ESCALATE")
        if node is None:
            problems.append(f"{theme}: ESCALATE lower node missing")
        else:
            node_text = _norm(group_visible_text(node["element"]))
            if node_text != ESCALATE_LABEL:
                problems.append(
                    f"{theme}: lower ESCALATE label {node_text!r} != {ESCALATE_LABEL!r}"
                )
            if node["tier"] != "strong":
                problems.append(f"{theme}: ESCALATE tier {node['tier']!r} != 'strong'")
            lines = _texts_with_class(node["element"], "st")
            if len(lines) != 1:
                problems.append(
                    f"{theme}: ESCALATE node must be a single line (got {lines!r})"
                )
            rect = _first_rect(node["element"])
            if rect is not None:
                node_w = _fnum(rect, "width")
                for line in lines:
                    if _est_text_width(line, "st") > node_w + 0.5:
                        problems.append(
                            f"{theme}: node line {line!r} exceeds node width {node_w}"
                        )
    return problems


def orchestrator_trigger_sync_problems(assets: dict[str, str]) -> list[str]:
    """Band enumerates ALL events per phase; wording/count == EDGE_LABELS."""
    problems: list[str] = []
    spec = importlib.util.spec_from_file_location("gen_for_band", GEN)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        ol_lines = [
            (e.text or "").strip()
            for e in _iter_local(root, "text")
            if e.get("class") == "ol"
        ]
        for col in gen.COLN:
            prefix = gen.DISPLAY_PREFIX.get(col, col)
            expected = [
                _norm(gen.EDGE_LABELS[triple])
                for triple in gen.main_events_for_column(col)
            ]
            matches = [ln for ln in ol_lines if f"← {prefix} ← «" in ln]
            if len(matches) != 1:
                problems.append(
                    f"{theme}: {col}: expected exactly one orchestrator band line "
                    f"for prefix {prefix!r}, got {matches!r}"
                )
                continue
            got = [_norm(q) for q in re.findall(r"«(.*?)»", matches[0])]
            if got != expected:
                problems.append(
                    f"{theme}: {col}: band events {got!r} != arrow events "
                    f"{expected!r}"
                )
    return problems


def c_owner_label_problems(assets: dict[str, str]) -> list[str]:
    """MAIN C has no under-header owner label; the lower C node keeps it."""
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        cols = [g for g in _groups(root) if g.get("data-column") == "C"]
        if len(cols) != 1:
            problems.append(
                f"{theme}: expected exactly one main C column, got {len(cols)}"
            )
        else:
            main_hits = [
                (e.text or "").strip()
                for e in cols[0].iter()
                if _local(e.tag) == "text"
                and (e.text or "").strip() == C_OWNER_LABEL
            ]
            if main_hits:
                problems.append(
                    f"{theme}: MAIN C column still renders the under-header owner "
                    f"label {C_OWNER_LABEL!r} ({len(main_hits)} text node(s))"
                )
        node = node_map(root).get("C")
        if node is None:
            problems.append(f"{theme}: lower data-node='C' missing")
        else:
            owner_lines = _texts_with_class(node["element"], "ls")
            if C_OWNER_LABEL not in owner_lines:
                problems.append(
                    f"{theme}: lower C node lost its owner label "
                    f"{C_OWNER_LABEL!r} (got {owner_lines!r})"
                )
            if node["tier"] != "medium":
                problems.append(
                    f"{theme}: lower C node tier {node['tier']!r} != 'medium'"
                )
    return problems


class DiagramCaptionPolishTest(unittest.TestCase):
    """Real-render contract for the user-approved caption polish."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.assets = render_assets()

    def test_result_arrows_are_unlabelled(self):
        self.assertEqual([], result_bus_problems(self.assets))

    def test_repair_return_is_exactly_repair_completed(self):
        self.assertEqual([], repair_completed_problems(self.assets))

    def test_escalation_header_is_escalate_body_band_node_descriptive(self):
        self.assertEqual([], escalation_name_problems(self.assets))

    def test_orchestrator_band_matches_arrow_labels(self):
        self.assertEqual([], orchestrator_trigger_sync_problems(self.assets))

    def test_lower_route_captions_are_sourced_from_edge_labels(self):
        # (a) value invariant: every visible lower-route caption equals the
        # canonical EDGE_LABELS value for its rendered (from,to,condition).
        spec = importlib.util.spec_from_file_location("gen_for_captions", GEN)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme, part="value"):
                root = parse_svg(self.assets[stem + ".svg"])
                for group in edge_groups(root):
                    caption = _norm(group_visible_text(group))
                    if not caption:
                        continue  # this route renders no visible caption
                    triple = (
                        group.get("data-from"),
                        group.get("data-to"),
                        group.get("data-condition"),
                    )
                    self.assertIn(
                        triple,
                        gen.EDGE_LABELS,
                        f"{theme}: route {triple} has a caption but no EDGE_LABELS",
                    )
                    self.assertEqual(
                        gen.EDGE_LABELS[triple],
                        caption,
                        f"{theme}: route {triple} caption {caption!r} != "
                        f"EDGE_LABELS {gen.EDGE_LABELS[triple]!r}",
                    )
        # (b) source-targeting mutation: re-point a lower-route label's
        # EDGE_LABELS value and prove the rendered caption follows EDGE_LABELS,
        # not the raw `condition`.  (The label equals the condition today, so only
        # this mutation can distinguish source from value.)
        source = GEN.read_text(encoding="utf-8")
        old = '("MERGE", "ESCALATE", "merge-конфликт"): "MERGE fail"'
        self.assertIn(old, source, "MERGE->ESCALATE EDGE_LABELS literal not found")
        mutated = source.replace(
            old,
            '("MERGE", "ESCALATE", "merge-конфликт"): "SENTINEL-CANONICAL"',
            1,
        )
        self.assertNotEqual(source, mutated)
        massets = render_assets(generator_source=mutated)
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme, part="source"):
                root = parse_svg(massets[stem + ".svg"])
                group = next(
                    (
                        g
                        for g in edge_groups(root)
                        if g.get("data-from") == "MERGE"
                        and g.get("data-to") == "ESCALATE"
                    ),
                    None,
                )
                self.assertIsNotNone(group, f"{theme}: MERGE->ESCALATE route missing")
                assert group is not None
                self.assertEqual(
                    "SENTINEL-CANONICAL",
                    _norm(group_visible_text(group)),
                    f"{theme}: MERGE->ESCALATE caption is not sourced from "
                    f"EDGE_LABELS (raw condition leak)",
                )

    def test_main_c_drops_under_header_owner_label_lower_c_keeps_it(self):
        self.assertEqual([], c_owner_label_problems(self.assets))

    def test_lane_definition_note_is_rendered(self):
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                notes = [
                    _norm(e.text or "")
                    for e in _iter_local(root, "text")
                    if e.get("class") == "nt"
                ]
                self.assertTrue(
                    any(n.startswith("Лейн (work stream)") for n in notes),
                    f"{theme}: lane definition note missing (nt notes={notes!r})",
                )


# ---------------------------------------------------------------------------
# Static contract tests over the normative prose (SKILL.md + pdca-orchestrator.md).
#
# These prove the DOCUMENTED collection policy, not a live collection run, and
# they are section-scoped semantic invariants (not whole-file keyword soup):
#   * a definitively incomplete task STOPS its whole group; remaining pending
#     tasks become `incomplete` with reason "группа остановлена", never a task
#     or group `blocked` status (blocked stays a parent-verification state);
#   * other groups continue under their own lane;
#   * a single-group collection creates no worktree/group/task branches and no
#     merge;
#   * only `done` groups are merged; an `incomplete` group's tip is never
#     merged even when it has earlier successful commits;
#   * `incomplete` results (refs/branches/commits/patch) survive ACT cleanup;
#     current-branch earlier commits stay with no auto-rollback;
#   * the autocommit/merge right needs an explicitly authorized collection mode
#     (a project overlay such as nextorm, or an explicit user request); the
#     skill grants no universal right and does not widen global AGENTS.md.
# ---------------------------------------------------------------------------


class CollectionContractSemanticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.lane = LANE_PATH.read_text(encoding="utf-8")

    @staticmethod
    def _plain(text: str) -> str:
        return _norm(text.replace("**", "").replace("`", ""))

    def _skill_plain(self, start: str, end: str) -> str:
        return self._plain(_skill_section(self.skill, start, end))

    # --- definitive incomplete stops the group, not just the task ---------

    def test_definitive_incomplete_stops_whole_group(self):
        lane_sec = self._skill_plain("## Лейн (work stream)", "## Git-модель")
        self.assertTrue(lane_sec, "SKILL §Лейн not found")
        self.assertRegex(
            lane_sec,
            r"окончательн\w+ incomplete задачи останавливает всю группу",
        )
        self.assertRegex(
            lane_sec,
            r"оставш\w+ pending задачи группы помечаются incomplete",
        )
        self.assertIn("группа остановлена", lane_sec)
        self.assertRegex(lane_sec, r"не исполняются")
        # pdca-orchestrator.md mirrors the same rule
        lane = self._plain(self.lane)
        self.assertRegex(
            lane,
            re.compile(r"окончательн\w+ incomplete.*останавливает всю группу", re.I),
        )
        self.assertIn("группа остановлена", lane)

    def test_remaining_tasks_incomplete_reason_not_blocked(self):
        lane = self._plain(self.lane)
        m = re.search(r"оставшиеся[^.]*?incomplete[^.]*?»", lane, re.I)
        self.assertIsNotNone(m, "pdca-orchestrator.md lost the remaining-tasks sentence")
        assert m is not None
        sentence = m.group(0)
        self.assertIn("группа остановлена", sentence)
        self.assertNotIn("blocked", sentence)
        # pdca-orchestrator.md states explicitly that task/group `blocked` does not exist
        self.assertRegex(lane, r"статуса blocked у задач/групп нет")
        # SKILL §Лейн: `blocked` stays only the parent-verification state
        lane_sec = self._skill_plain("## Лейн (work stream)", "## Git-модель")
        self.assertRegex(lane_sec, r"статуса blocked у задач/групп нет")
        self.assertRegex(
            lane_sec, r"blocked остаётся только состоянием родительской верификации"
        )

    def test_other_groups_continue(self):
        lane_sec = self._skill_plain("## Лейн (work stream)", "## Git-модель")
        self.assertRegex(lane_sec, r"другие группы продолжают")
        fail = self._skill_plain("## Сбой (failure semantics)", "## Статус коллекции")
        self.assertIn("другие группы продолжают", fail)
        self.assertRegex(
            self._plain(self.lane), re.compile(r"другие группы продолж", re.I)
        )

    # --- single-group degradation ----------------------------------------

    def test_single_group_exemption(self):
        p = self._skill_plain("### P —", "### D —")
        d = self._skill_plain("### D —", "### C —")
        for sec in (p, d):
            self.assertRegex(
                sec,
                re.compile(r"одн\w+ группа|если группа одна|при одной группе", re.I),
            )
        self.assertRegex(
            p, re.compile(r"worktree и ветк\w+.*не создаются", re.I)
        )
        self.assertRegex(p, r"merge --no-ff не нужен")
        self.assertRegex(d, re.compile(r"worktree и ветки .*не создаются", re.I))
        self.assertRegex(d, r"merge")
        self.assertRegex(
            self._plain(self.lane),
            r"в режиме одной группы ветки/worktree группы и задач не создаются",
        )

    # --- sidebar todo mirrors groups, or tasks when single ----------------

    def test_sidebar_todo_lists_groups_or_all_tasks_when_single(self):
        p = self._skill_plain("### P —", "### D —")
        self.assertRegex(p, re.compile(r"туду|todo", re.I))
        # multi-group: one sidebar item per group
        self.assertRegex(p, re.compile(r"по одному пункту на группу", re.I))
        # single group (could not split): one item per task, no group item
        self.assertRegex(
            p, re.compile(r"одн\w+ группа.*по одному пункту на каждую задачу", re.I)
        )
        self.assertRegex(p, re.compile(r"пункта-«группы».*нет", re.I))
        # parallel lanes may hold several in_progress items at once
        self.assertRegex(p, re.compile(r"параллельные лейны дают.*in_progress", re.I))

    # --- merge policy -----------------------------------------------------

    def test_merge_only_done_never_incomplete_tip(self):
        d = self._skill_plain("### D —", "### C —")
        self.assertRegex(d, r"только для групп done")
        self.assertRegex(d, r"incomplete-группа не мержится никогда")
        self.assertRegex(d, r"даже если")
        status = self._skill_plain("## Статус коллекции", "## Отчёт")
        self.assertRegex(status, r"incomplete никогда не merged")
        self.assertRegex(status, r"incomplete.*не мержится")

    # --- incomplete results survive cleanup -------------------------------

    def test_incomplete_results_preserved_through_cleanup(self):
        a = self._skill_plain("### A —", "## Лейн")
        self.assertRegex(a, r"сносит только одноразовые")
        self.assertRegex(a, r"incomplete-групп не удаляются никогда")
        self.assertRegex(a, r"patch")
        self.assertRegex(a, r"refs")
        self.assertRegex(a, r"нельзя удалять")
        # single-group: earlier commits stay in the current branch, no rollback
        p = self._skill_plain("### P —", "### D —")
        self.assertRegex(p, r"incomplete.*коммиты.*остаются.*без авто-отката")
        fail = self._skill_plain("## Сбой (failure semantics)", "## Статус коллекции")
        self.assertRegex(fail, r"результаты сохраняются")
        self.assertRegex(fail, r"refs/ветки/коммиты \+ patch")

    # --- explicit authorized autocommit is an overlay, not universal ------

    def test_explicit_autocommit_overlay_not_universal(self):
        header = self._skill_plain("## Роль", "## Коллекция")
        self.assertRegex(header, r"явно разрешённый автокоммит")
        self.assertRegex(header, r"проектный overlay")
        self.assertIn("nextorm", header)
        self.assertRegex(
            header,
            r"сам скилл .{0,40}универсального права на коммит/merge не даёт",
        )
        self.assertRegex(header, r"глобальные AGENTS\.md не расширяет")
        self.assertRegex(header, re.compile(r"без разрешения", re.I))
        params = self._skill_plain("## Параметры", "## Связь с базовым PDCA")
        self.assertRegex(params, r"проектный overlay или явный запрос пользователя")
        self.assertRegex(params, r"сам скилл права не даёт")

    # --- stack-neutral: per-task variant, no hard pdca-dotnet dependency -----

    def test_collection_is_stack_neutral_with_per_task_variant(self):
        # The collection must not require .NET: the cycle variant is chosen per
        # task, so both code contracts are named and the base stays generic.
        header = self._skill_plain("## Роль", "## Коллекция")
        self.assertRegex(header, re.compile(r"вариант цикла выбирается на задачу", re.I))
        self.assertIn("pdca-dotnet", header)
        self.assertIn("pdca-coder", header)
        self.assertRegex(
            header,
            re.compile(r"\.NET/C#\s*→\s*pdca-dotnet, другой код\s*→\s*pdca-coder"),
        )
        lane_sec = self._skill_plain("## Лейн (work stream)", "## Git-модель")
        self.assertRegex(lane_sec, re.compile(r"выбранн\w+ для задачи варианта", re.I))
        self.assertIn("pdca-coder", lane_sec)
        self.assertIn("pdca-dotnet", lane_sec)
        conn = self._skill_plain("## Связь с базовым PDCA", "## Fallback")
        self.assertTrue(conn, "SKILL §Связь с базовым PDCA not found")
        self.assertRegex(conn, re.compile(r"стек-нейтрален", re.I))
        self.assertIn("pdca-coder", conn)

    # --- the branch chain is per task, not per group ----------------------

    def test_branch_chain_is_per_task_not_group(self):
        lane_sec = self._skill_plain("## Лейн (work stream)", "## Git-модель")
        self.assertRegex(
            lane_sec,
            r"ветка collection/<id>/task-<g>-<k> от закоммиченного tip предыдущей",
        )
        git = self._skill_plain("## Git-модель", "## Сбой")
        self.assertRegex(git, r"цепочка веток задач")
        self.assertRegex(git, r"следующая ветвится от tip предыдущей")

    # --- group status enum: the exact original 5 values, `merged` included -

    def test_group_status_enum_is_exact_five_including_merged(self):
        # User correction: the ORIGINAL, approved group enum has exactly five
        # values and `merged` is one of them -- reached only as the
        # `done` -> `merged` status transition.  It must NOT be renamed/relocated
        # into a separate "merge-disposition" field, and `skipped` is not a group
        # status value at all (only an integration note).
        skill_status = _skill_section(self.skill, "## Статус коллекции", "## Отчёт")
        skill_enum = re.search(
            r"\(`pending`\s*\|\s*`in-progress`\s*\|\s*`done`\s*\|\s*"
            r"`incomplete`\s*\|\s*`merged`\)",
            skill_status,
        )
        self.assertIsNotNone(
            skill_enum,
            "SKILL §Статус must carry the exact 5-value group enum including `merged`",
        )
        assert skill_enum is not None
        self.assertNotIn("skipped", skill_enum.group(0))
        # the representation is unchanged: no "merge-disposition" field anywhere
        self.assertNotIn("merge-disposition", self.skill)
        status_plain = self._plain(skill_status)
        self.assertRegex(status_plain, r"переход только done → merged")
        self.assertRegex(status_plain, r"incomplete никогда не merged")
        self.assertRegex(
            status_plain, r"skipped — примечание интеграции .*не статус группы"
        )

        # the scenario matrix enumerates the same exact 5-value group enum
        scenarios = SCENARIOS_PATH.read_text(encoding="utf-8")
        scen_enum = re.search(
            r"`pending\s*\|\s*in-progress\s*\|\s*done\s*\|\s*"
            r"incomplete\s*\|\s*merged`",
            scenarios,
        )
        self.assertIsNotNone(
            scen_enum,
            "scenarios.md must carry the exact 5-value group enum including `merged`",
        )
        assert scen_enum is not None
        self.assertNotIn("skipped", scen_enum.group(0))
        self.assertNotIn("merge-disposition", scenarios)


# ---------------------------------------------------------------------------
# Measured text-fit regression (best-effort, tools-dependent).
#
# The hand renderer lays out absolute coordinates, so the geometry tests above
# cannot see glyph overflow.  When Pillow and a DejaVu font are available this
# test measures every non-rotated `<text>` with a font wider than the requested
# Segoe UI and asserts it stays inside its nearest semantic container (peer
# column / state node / orchestrator band).  It is skipped where the tools are
# missing rather than silently weakened.
# ---------------------------------------------------------------------------

try:  # pragma: no cover - import guard
    from PIL import ImageFont as _ImageFont
except Exception:  # pragma: no cover
    _ImageFont = None  # type: ignore[assignment]

_DEJAVU_FONTS = {
    (False, False): "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    (False, True): "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    (True, False): "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    (True, True): "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
}
# class -> (px, bold, mono); mirrors the <style> block of the generator.
_FIT_CLASSES = {
    "t": (13, True, False), "s": (10.5, False, False), "h": (12.5, True, False),
    "g": (10.5, True, False), "bt": (15, True, False), "ol": (11.5, False, False),
    "lt": (12.5, True, False), "ls": (10.5, False, False), "nt": (10.5, False, False),
    "st": (14, True, False), "bm": (10.5, True, True), "lm": (12, True, True),
}

_HAS_FIT_TOOLS = _ImageFont is not None and all(
    Path(p).exists() for p in _DEJAVU_FONTS.values()
)


def _fit_font(px: float, bold: bool, mono: bool):
    return _ImageFont.truetype(_DEJAVU_FONTS[(mono, bold)], int(round(px)))


# sub-pixel/kerning slack; a real overflow (the new long labels) exceeds this by
# tens of pixels, while pre-existing borderline subtitles stay within ~1px.
_FIT_TOL = 1.0


_FIT_FONT_CACHE: dict = {}


def _measured_width(text: str, cls: str) -> float:
    px, bold, mono = _FIT_CLASSES.get(cls, (10.5, False, False))
    key = (px, bold, mono)
    if key not in _FIT_FONT_CACHE:
        _FIT_FONT_CACHE[key] = _fit_font(px, bold, mono)
    return _FIT_FONT_CACHE[key].getlength(text)


def _nearest_container(root: ET.Element, el: ET.Element) -> tuple[float, float]:
    parent = _parent_map(root)
    view = [float(v) for v in root.get("viewBox", "").split()]
    full = (24.0, view[2] - 48.0)
    cur = el
    while cur in parent:
        cur = parent[cur]
        col = cur.get("data-column")
        if col:
            for g in cur.iter():
                if g.get("data-peer-header") == col:
                    for r in g.iter():
                        if _local(r.tag) == "rect":
                            return float(r.get("x") or 0), float(r.get("width") or 0)
        if cur.get("data-node"):
            for r in cur.iter():
                if _local(r.tag) == "rect":
                    return float(r.get("x") or 0), float(r.get("width") or 0)
    return full


def measured_fit_problems(assets: dict[str, str]) -> list[str]:
    problems: list[str] = []
    for theme, stem in THEME_STEMS.items():
        root = parse_svg(assets[stem + ".svg"])
        for el in _iter_local(root, "text"):
            if el.get("transform"):
                continue  # the rotated lane loop-back label
            text = (el.text or "").strip()
            if not text:
                continue
            width = _measured_width(text, el.get("class", "s"))
            x = float(el.get("x") or 0)
            anchor = el.get("text-anchor", "start")
            if anchor == "middle":
                left, right = x - width / 2, x + width / 2
            elif anchor == "end":
                left, right = x - width, x
            else:
                left, right = x, x + width
            cx, cw = _nearest_container(root, el)
            if left < cx - _FIT_TOL or right > cx + cw + _FIT_TOL:
                problems.append(
                    f"{theme}: text {text!r} [{left:.1f},{right:.1f}] leaves "
                    f"container [{cx:.1f},{cx + cw:.1f}]"
                )
    return problems


@unittest.skipUnless(_HAS_FIT_TOOLS, "Pillow + DejaVu fonts not available")
class MeasuredTextFitTest(unittest.TestCase):
    """Every rendered text stays inside its card/node/band (measured glyphs)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.assets = render_assets()

    def test_measured_text_fits_its_container(self):
        self.assertEqual([], measured_fit_problems(self.assets))


# ---------------------------------------------------------------------------
# 2026-10-06 own-PLAN barrier (P1 RED contract).
#
# P4 will render the collection planning phase as three explicit ordered
# substeps (`task-plan` -> `all-plans-barrier` -> `collection-scheduling`) and
# make the P->DO guard express "all plans ready AND persisted schedule valid"
# instead of the bare old "groups fixed" wording.  These assertions are RED
# until that render change; they do not add/rename any diagram node or edge.
# ---------------------------------------------------------------------------


def _data_step_values(root: ET.Element) -> set[str]:
    return {
        value
        for g in _groups(root)
        if (value := g.get("data-step")) is not None
    }


_P_TO_DO_READY = re.compile(r"all\s+plans|планы\s+готовы", re.I)


class CollectionPlanBarrierDiagramTest(unittest.TestCase):
    """Rendered P shows task-plan -> all-plans-barrier -> collection-scheduling."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.assets = render_assets()

    def test_p_phase_exposes_task_plan_barrier_and_scheduling_steps(self):
        expected = ("task-plan", "all-plans-barrier", "collection-scheduling")
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                steps = _data_step_values(root)
                for step in expected:
                    self.assertIn(
                        step,
                        steps,
                        f"{theme}: rendered P lacks data-step={step!r}; "
                        f"got {sorted(steps)}",
                    )

    def test_p_to_do_guard_reflects_all_plans_ready(self):
        # The P->DO guard is rendered as the p->DO main event entry (its visible
        # label derives from the canonical edge label); the lower edge itself is
        # uncaptioned.  Locate the entry, not a line or a global keyword count.
        for theme, stem in THEME_STEMS.items():
            with self.subTest(theme=theme):
                root = parse_svg(self.assets[stem + ".svg"])
                entries = [
                    g
                    for g in _groups(root)
                    if g.get("data-entry-from") == "P"
                    and g.get("data-entry-to") == "DO"
                ]
                self.assertEqual(
                    1,
                    len(entries),
                    f"{theme}: expected exactly one P->DO guard entry, "
                    f"got {len(entries)}",
                )
                guard = group_visible_text(entries[0])
                self.assertRegex(
                    guard,
                    _P_TO_DO_READY,
                    f"{theme}: P->DO guard {guard!r} must reflect all-plans-ready",
                )


if __name__ == "__main__":
    unittest.main()
