#!/usr/bin/env python3
# Hand-laid-out SVG for the pdca-incremental campaign, in the shared PDCA family
# layout: the orchestrator band on top with per-phase inputs, one column per campaign
# block (BOOTSTRAP / DISCOVER / BRIEF / STEP / ACCEPT / DECIDE / STOP), a tier legend
# and the campaign state graph at the bottom.  The defining edge is DECIDE -> DISCOVER:
# the next step starts from the accepted baseline of the previous one.
# Renders light (incremental-hand.*) and dark (incremental-hand-dark.*).
import html
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

M = 24
GAP = 24

# One column per campaign block; widths drive the shared canvas.
COLN = ["B", "P", "S", "A", "R", "X"]
WIDTH = {"B": 210, "P": 236, "S": 210, "A": 190, "R": 196, "X": 200}
COLX = {}
_x = M
for _c in COLN:
    COLX[_c] = _x
    _x += WIDTH[_c] + GAP
W = _x - GAP + M

COLOR = {"B": "#0e7490", "P": "#2563eb", "S": "#7c3aed",
         "A": "#d97706", "R": "#059669", "X": "#b91c1c"}
NAME = {"B": "B · BOOTSTRAP", "P": "P · PLAN", "S": "S · STEP N",
        "A": "A · ACCEPT", "R": "R · DECIDE", "X": "X · STOP"}
OWNER = {"B": "pdca-planner + pdca-executor · medium/cheap", "P": "pdca-scout + pdca-planner · cheap/medium",
         "S": "orchestrator · cheap", "A": "pdca-check · medium",
         "R": "pdca-planner · medium", "X": "primary · cheap"}
TIER_COLOR = {"cheap": "#0d9488", "medium": "#4f46e5", "strong": "#ea580c"}
TIER_MODEL = {"cheap": "cheap", "medium": "medium", "strong": "strong"}

BLOCKS = {
    "B": [
        ("Goal + recipe", "pdca-planner · read-only · fixation", "medium"),
        ("Baseline", "pdca-executor · edit/bash · recipe", "cheap"),
        ("Floor · target", "pdca-planner · baseline + floor", "medium"),
        ("Status file", "primary · status-only · one file", "cheap"),
    ],
    "P": [
        ("Discover · gap map", "pdca-scout · gap + deferred · read-only", "cheap"),
        ("Ranked seed", "pdca-scout · facts, not a decision", "cheap"),
        ("Brief · six blocks", "pdca-planner · read-only", "medium"),
        ("Acceptance · targets", "pdca-planner · floor · scope", "medium"),
    ],
    "S": [
        ("P · PLAN", "pdca-planner · step plan · rev r", "medium"),
        ("D · DO", "pdca-executor · edit/bash · facts", "cheap"),
        ("C · CHECK", "pdca-check · read-only · evidence", "medium"),
        ("A · ACT", "pdca-executor · status/docs", "cheap"),
        ("Step exit", "accept · revise · blocked → ACT", "medium"),
    ],
    "A": [
        ("Verdict", "pdca-check · read-only · by rows", "medium"),
        ("Number", "one run · red is archived", "cheap"),
        ("Step row", "one writer · status write", "cheap"),
    ],
    "R": [
        ("Goal?", "pdca-planner · predicate", "medium"),
        ("Remainder", "prove with numbers · blocker", "medium"),
        ("Next seed", "pdca-planner · the next step", "medium"),
        ("Route", "next · revise · stop", "medium"),
    ],
    "X": [
        ("met", "the only success", "cheap"),
        ("unreachable", "the remainder proven by numbers", "cheap"),
        ("blocked/stopped", "resume point in the status file", "cheap"),
    ],
}

# orchestrator inputs, per phase
INPUTS = [
    'BOOTSTRAP ← "campaign start" · "new goal"',
    'PLAN ← "baseline accepted" · "next seed"',
    'STEP ← "brief approved" · "replan r+1"',
    'ACCEPT ← "step closed"',
    'DECIDE ← "measurement accepted"',
    'STOP ← "met" · "unreachable" · "blocked" · "stopped"',
]
DISPATCH = {"B": "start", "P": "plan ready",
            "S": "step closed", "A": "measurement accepted", "R": "decision", "X": "stop"}

# campaign state graph
STC = {"START": None, "BOOT": "#0e7490", "PLAN": "#2563eb",
       "STEP": "#7c3aed", "ACC": "#d97706", "DEC": "#059669", "STOP": "#b91c1c"}

THEMES = {
    "light": {
        "bg": "#f1f5f9", "card": "#fff", "shadow": "0 1px 3px rgba(0,0,0,.12)",
        "title": "#0f172a", "sub": "#64748b", "band": "#1f2937",
        "orb_list": "#e6e9ef", "arrow": "#334155", "bus": "#94a3b8",
        "label": "#475569", "box": "#ffffff", "box_stroke": "#cbd5e1",
        "box_stroke_w": 1, "frame_op": 0.35, "frame_w": 1, "tint": True,
        "badge_op": 0.13, "badge_text": None,
        "state_neutral": "#475569",
    },
    "dark": {
        "bg": "#0f172a", "card": "#1e293b", "shadow": "0 1px 3px rgba(0,0,0,.5)",
        "title": "#e2e8f0", "sub": "#94a3b8", "band": "#141d31",
        "orb_list": "#e2e8f0", "arrow": "#94a3b8", "bus": "#64748b",
        "label": "#cbd5e1", "box": "#223046", "box_stroke": "#3b4a63",
        "box_stroke_w": 1, "frame_op": 0.6, "frame_w": 1.6, "tint": False,
        "badge_op": 0.13, "badge_text": "#cbd5e1",
        "state_neutral": "#94a3b8",
    },
}

ORB_Y, ORB_H = 24, 138
SPINE_Y, SPINE_H = 224, 40
COL_Y = 280
BOX_H, BOX_STEP = 50, 62
ROWS = max(len(b) for b in BLOCKS.values())
COL_BOTTOM = COL_Y + (ROWS - 1) * BOX_STEP + BOX_H + 8
LEG_Y = COL_BOTTOM + 48
SG_TITLE_Y = LEG_Y + 74
CUT_Y = SG_TITLE_Y - 20
R1_TOP = SG_TITLE_Y + 80
R1_BOT = R1_TOP + 44
R2_TOP = R1_TOP + 132
H = R2_TOP + 44 + 40


def esc(value):
    return html.escape(value, quote=True)


def _fit(text, maxpx, cw):
    if not text:
        return text
    if len(text) * cw <= maxpx:
        return text
    n = max(1, int(maxpx / cw) - 1)
    return text[:n].rstrip() + "\u2026"


def render(P):
    def box(x, y, w, h, title, sub, tier):
        col = TIER_COLOR[tier]
        bw, bh = 50, 18
        bx, by = x + w - bw - 8, y + 7
        if P["tint"]:
            badge = (f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6" fill="{col}" '
                     f'fill-opacity="{P["badge_op"]}" stroke="{col}" stroke-opacity="0.7"/>')
            btxt = col
        else:
            badge = f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6" fill="{col}"/>'
            btxt = P["badge_text"]
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{P["box"]}" '
               f'stroke="{P["box_stroke"]}" stroke-width="{P["box_stroke_w"]}"/>',
               f'<rect x="{x + 1}" y="{y + 7}" width="3" height="{h - 14}" rx="1.5" fill="{col}"/>',
               badge,
               f'<text x="{bx + bw / 2}" y="{by + bh / 2 + 3.5}" class="bm" fill="{btxt}" '
               f'text-anchor="middle">{TIER_MODEL[tier]}</text>',
               f'<text x="{x + 13}" y="{y + 23}" class="t">{esc(_fit(title, (bx - 6) - (x + 13), 7.9))}</text>']
        if sub:
            out.append(f'<text x="{x + 13}" y="{y + 42}" class="s">{esc(_fit(sub, (x + w - 8) - (x + 13), 5.2))}</text>')
        return "\n".join(out)

    def header(x, y, w, h, lbl, col, owner):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{COLOR[col]}"/>'
                f'<text x="{x + w / 2}" y="{y + 17}" class="h" text-anchor="middle">{esc(lbl)}</text>'
                f'<text x="{x + w / 2}" y="{y + 33}" class="ho" text-anchor="middle">{esc(owner)}</text>')

    def poly(points, color=None, dash=None, edge_id=None):
        color = color or P["arrow"]
        pts = " ".join(f"{a},{b}" for a, b in points)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        eid = f' data-edge-id="{edge_id}"' if edge_id else ""
        return (f'<polyline points="{pts}" fill="none" stroke="{color}"{d}{eid} '
                f'marker-end="url(#arrow)"/>')

    def label(x, y, value, color=None, anchor="middle"):
        color = color or P["label"]
        return (f'<text x="{x}" y="{y}" class="g" fill="{color}" text-anchor="{anchor}">'
                f'{esc(value)}</text>')


    s = []
    s.append(f'<svg viewBox="0 0 {W} {H}" width="{W}" xmlns="http://www.w3.org/2000/svg" '
             f'font-family="Segoe UI, system-ui, sans-serif">')
    s.append('<defs>\n'
             f'<marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">'
             f'<path d="M0,0 L7,3 L0,6 Z" fill="{P["arrow"]}"/></marker>\n'
             '</defs>\n<style>\n'
             f'.t{{font-size:13px;font-weight:600;fill:{P["title"]}}}\n'
             f'.s{{font-size:10.5px;fill:{P["sub"]}}}\n'
             '.h{font-size:12.5px;font-weight:700;fill:#ffffff}\n'
             '.ho{font-size:9.5px;fill:#ffffff;fill-opacity:0.85}\n'
             '.g{font-size:10.5px;font-weight:600}\n'
             f'.band{{fill:{P["band"]}}}\n'
             '.bt{fill:#ffffff;font-size:15px;font-weight:700}\n'
             f'.ol{{fill:{P["orb_list"]};font-size:11.5px}}\n'
             f'.lt{{font-size:12.5px;font-weight:700;fill:{P["title"]}}}\n'
             f'.ls{{font-size:10.5px;fill:{P["sub"]}}}\n'
             '.lm{font-family:ui-monospace,Consolas,Menlo,monospace;font-size:12px;font-weight:700}\n'
             '.bm{font-family:ui-monospace,Consolas,Menlo,monospace;font-size:10.5px;font-weight:700}\n'
             '.st{font-size:14px;font-weight:700}\n'
             '</style>')

    # ---- orchestrator band ----
    s.append(f'<rect x="{M}" y="{ORB_Y}" width="{W - 2 * M}" height="{ORB_H}" rx="10" class="band"/>')
    s.append(f'<text x="{M + 18}" y="{ORB_Y + 24}" class="bt">'
             'Orchestrator · cheap — cycle-control / campaign-control</text>')
    split = (len(INPUTS) + 1) // 2
    for gi in range(2):
        gx = M + 18 if gi == 0 else M + 18 + (W - 2 * M) / 2
        for row, line in enumerate(INPUTS[:split] if gi == 0 else INPUTS[split:]):
            prefix = "\u2190 "
            s.append(f'<text x="{gx}" y="{ORB_Y + 52 + row * 18}" class="ol">{prefix}{esc(line)}</text>')

    def cx(c):
        return COLX[c] + WIDTH[c] / 2

    # ---- columns ----
    for c in COLN:
        x, w = COLX[c], WIDTH[c]
        s.append(header(x, SPINE_Y, w, SPINE_H, NAME[c], c, OWNER[c]))
        s.append(poly([(cx(c), SPINE_Y + SPINE_H), (cx(c), COL_Y)]))
        bottom = COL_Y
        for j, (title, sub, tier) in enumerate(BLOCKS[c]):
            by = COL_Y + j * BOX_STEP
            s.append(box(x, by, w, BOX_H, title, sub, tier))
            bottom = by + BOX_H
            if j:
                s.append(poly([(cx(c), COL_Y + (j - 1) * BOX_STEP + BOX_H),
                               (cx(c), by)], P["bus"]))
        s.append(f'<rect x="{x - 6}" y="{COL_Y - 8}" width="{w + 12}" '
                 f'height="{bottom - COL_Y + 16}" rx="12" fill="none" stroke="{COLOR[c]}" '
                 f'stroke-opacity="{P["frame_op"]}" stroke-width="{P["frame_w"]}"/>')

    # ---- band <-> columns ----
    orb_b = ORB_Y + ORB_H
    mid = (orb_b + SPINE_Y) / 2 + 3
    for c in COLN:
        xc = cx(c)
        s.append(poly([(xc - 16, orb_b), (xc - 16, SPINE_Y)], edge_id=f"dispatch_{c.lower()}"))
        s.append(label(xc - 24, mid, DISPATCH[c], P["arrow"], "end"))
        if c != "X":
            s.append(poly([(xc + 16, SPINE_Y), (xc + 16, orb_b)], edge_id=f"return_{c.lower()}"))

    # ---- tier legend ----
    legend = [
        ("#0d9488", "cheap tier", "cheap", "primary · pdca-scout · pdca-executor · orchestrator"),
        ("#4f46e5", "medium tier", "medium", "pdca-planner · pdca-check"),
    ]
    iw = (W - 2 * M) / 2
    for i, (col, title, model, roles) in enumerate(legend):
        lx = M + i * iw
        s.append(f'<rect x="{lx}" y="{LEG_Y - 12}" width="15" height="15" rx="4" fill="{col}"/>')
        s.append(f'<text x="{lx + 22}" y="{LEG_Y}" class="lt">{esc(title)}</text>')
        mw = len(model) * 7.4 + 16
        if P["tint"]:
            s.append(f'<rect x="{lx + 22}" y="{LEG_Y + 8}" width="{mw}" height="21" rx="7" '
                     f'fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.65"/>')
            mtxt = col
        else:
            s.append(f'<rect x="{lx + 22}" y="{LEG_Y + 8}" width="{mw}" height="21" rx="7" fill="{col}"/>')
            mtxt = "#ffffff"
        s.append(f'<text x="{lx + 22 + mw / 2}" y="{LEG_Y + 23}" class="lm" fill="{mtxt}" '
                 f'text-anchor="middle">{esc(model)}</text>')
        s.append(f'<text x="{lx + 22 + mw + 10}" y="{LEG_Y + 23}" class="ls">{esc(roles)}</text>')
        if i == len(legend) - 1:
            s.append(f'<text x="{W / 2}" y="{LEG_Y + 44}" class="ls" text-anchor="middle">'
                     'strong · pdca-escalate — not a campaign role: called inside STEP by triggers, '
                     'the campaign receives the result</text>')

    # ---- campaign state graph (20 % narrower than the canvas content) ----
    NH, NW = 44, 120
    order = ["START", "BOOT", "PLAN", "STEP", "ACC", "DEC"]
    graph_w = (W - 2 * M) * 0.8
    graph_x = M + (W - 2 * M - graph_w) / 2
    gap = (graph_w - NW) / (len(order) - 1)
    stx = {name: graph_x + i * gap for i, name in enumerate(order)}
    s.append(f'<text x="{graph_x}" y="{SG_TITLE_Y}" class="lt">Campaign graph</text>')
    stc = {k: (v or P["state_neutral"]) for k, v in STC.items()}
    for name in order:
        x = stx[name]
        s.append(f'<rect x="{x}" y="{R1_TOP}" width="{NW}" height="{NH}" rx="10" '
                 f'fill="{stc[name]}" fill-opacity="0.08" stroke="{stc[name]}" stroke-width="1.6" '
                 f'data-node-id="{name}"/>')
        s.append(f'<text x="{x + NW / 2}" y="{R1_TOP + NH / 2 + 5}" class="st" fill="{stc[name]}" '
                 f'text-anchor="middle">{esc(name)}</text>')
    _y = R1_TOP + NH / 2
    edges = [
        ("start_boot", "START", "BOOT", "start"),
        ("boot_plan", "BOOT", "PLAN", "recipe"),
        ("plan_step", "PLAN", "STEP", "brief"),
        ("step_acc", "STEP", "ACC", "closed | blocked (DO → ACT)"),
        ("acc_dec", "ACC", "DEC", "accepted"),
    ]
    for eid, a, b, lab in edges:
        x1, x2 = stx[a] + NW, stx[b]
        s.append(poly([(x1, _y), (x2, _y)], edge_id=eid))
        s.append(label((x1 + x2) / 2, _y - 7, lab, P["label"]))
    # the defining feedback edge: DECIDE -> DISCOVER, next step starts from the accepted number
    s.append(f'<path d="M{stx["DEC"] + NW / 2},{R1_TOP} C{stx["DEC"] + NW / 2},{R1_TOP - 46} '
             f'{stx["PLAN"] + NW / 2},{R1_TOP - 46} {stx["PLAN"] + NW / 2},{R1_TOP}" '
             f'fill="none" stroke="{P["arrow"]}" stroke-dasharray="5 4" marker-end="url(#arrow)" '
             f'data-edge-id="decide_plan"/>')
    s.append(label((stx["PLAN"] + stx["DEC"]) / 2 + NW / 2, R1_TOP - 52,
                   "next step · baseline = accepted", P["label"]))
    # repair: a failed increment re-runs the same target, it is not the next step.
    # Routed below the row so it reads separately from the defining DEC -> PLAN edge.
    rx1 = stx["DEC"]
    ry1 = R1_TOP + NH / 2
    rx2 = stx["STEP"] + NW / 2
    ry2 = R1_TOP + NH
    s.append(f'<path d="M{rx1},{ry1} C{rx1},{R1_TOP + 80} {rx2},{R1_TOP + 80} {rx2},{ry2}" '
             f'fill="none" stroke="{P["arrow"]}" stroke-dasharray="2 3" marker-end="url(#arrow)" '
             f'data-edge-id="decide_step"/>')
    s.append(label((rx1 + rx2) / 2, R1_TOP + 72,
                   "repair · parent N", P["label"]))
    # stop branch
    sx = stx["DEC"]
    s.append(poly([(sx + NW / 2, R1_BOT), (sx + NW / 2, R2_TOP)], STC["STOP"], edge_id="decide_stop"))
    s.append(f'<rect x="{sx}" y="{R2_TOP}" width="{NW}" height="{NH}" rx="10" '
             f'fill="{STC["STOP"]}" fill-opacity="0.08" stroke="{STC["STOP"]}" stroke-width="1.6" '
             f'data-node-id="STOP"/>')
    s.append(f'<text x="{sx + NW / 2}" y="{R2_TOP + NH / 2 + 5}" class="st" fill="{STC["STOP"]}" '
             f'text-anchor="middle">STOP</text>')
    s.append(label(sx - 10, R2_TOP + NH / 2 + 4,
                   "ACT-finalized · met · unreachable · blocked · stopped", P["label"], "end"))
    # verify is an optional integrated gate, not a second increment
    s.append(label(graph_x, R2_TOP + NH + 24,
                   "verify — optional integrated gate: target = gate, does not move the baseline",
                   P["label"], "start"))

    s.append("</svg>")
    return "\n".join(s)


def htmlwrap(P, title, svg):
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            f'<title>{esc(title)}</title>'
            f'<style>body{{margin:0;background:{P["bg"]};font-family:Segoe UI,system-ui,sans-serif}}'
            f'.card{{background:{P["card"]};border-radius:12px;margin:20px;padding:12px;'
            f'box-shadow:{P["shadow"]};overflow:auto}}</style>'
            '<div class="card">' + svg + '</div></html>')


VARIANTS = [
    ("light", "incremental-hand", "pdca-incremental — campaign in steps"),
    ("dark", "incremental-hand-dark", "pdca-incremental — campaign in steps (dark theme)"),
]

rendered = {}
for theme, stem, title in VARIANTS:
    P = THEMES[theme]
    svg = render(P)
    rendered[theme] = svg
    open(os.path.join(OUT_DIR, stem + ".svg"), "w", encoding="utf-8").write(svg)
    open(os.path.join(OUT_DIR, stem + ".html"), "w", encoding="utf-8").write(htmlwrap(P, title, svg))
    print("wrote %s.{svg,html}" % stem)


def crop(svg, y, height):
    """Re-frame the shared dark SVG: same body, a different viewBox."""
    head = f'viewBox="0 0 {W} {H}" width="{W}"'
    tail = f'viewBox="0 {y} {W} {height}" width="{W}" height="{height}"'
    if head not in svg:
        raise SystemExit("crop: unexpected svg header")
    return svg.replace(head, tail, 1)


dark = rendered["dark"]
open(os.path.join(OUT_DIR, "incremental-contract-dark.svg"), "w", encoding="utf-8").write(
    crop(dark, 0, CUT_Y))
open(os.path.join(OUT_DIR, "incremental-state-dark.svg"), "w", encoding="utf-8").write(
    crop(dark, CUT_Y, H - CUT_Y))
print("wrote incremental-{contract,state}-dark.svg")

print("W=%d H=%d" % (W, H))
