#!/usr/bin/env python3
# Hand-laid-out SVG for the pdca-coder workflow:
#   orchestrator band on top with per-phase inputs; columns P/D/C/Security/
#   Escalation/STOP/A; every phase returns control to the orchestrator.
# Renders two artefacts: light (pdca-coder-hand.*) and dark (pdca-coder-hand-dark.*).
import html
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

M = 24
GAP = 28

COLN = ["P", "D", "C", "SEC", "E", "S", "A"]
WIDTH = {"P": 196, "D": 196, "C": 196, "SEC": 240, "E": 168, "S": 196, "A": 196}
COLX = {}
_x = M
for _c in COLN:
    COLX[_c] = _x
    _x += WIDTH[_c] + GAP
W = _x - GAP + M

ORB_Y, ORB_H = 24, 138
SPINE_Y, SPINE_H = 224, 40
COL_Y = 280
BOX_H, BOX_STEP = 50, 62

COLOR = {"P": "#2563eb", "D": "#7c3aed", "C": "#d97706", "SEC": "#be123c",
         "E": "#b91c1c", "S": "#b91c1c", "A": "#059669"}
NAME = {"P": "P · PLAN", "D": "D · DO", "C": "C · CHECK", "SEC": "CHECK · security (stream)",
        "E": "ESCALATION", "S": "STOP", "A": "A · ACT"}
TIER_COLOR = {"weak": "#0d9488", "medium": "#4f46e5", "strong": "#ea580c"}
TIER_MODEL = {"weak": "cheap", "medium": "medium", "strong": "strong"}

BLOCKS = {
    "P": [
        ("PLAN", "start · design", "medium"),
        ("Gather", "pdca-scout + domain lenses", "weak"),
        ("Decide · pdca-planner", "fix / defer · decomposition", "medium"),
        ("Criteria · goal", "goal · acceptance (+negative)", "medium"),
        ("Tasks · risks", "units · no TBD", "medium"),
        ("Tests · docs", "strategy · plan", "medium"),
        ("Perf decision", "measure? · tool · baseline", "medium"),
        ("Spike", "needed? · tool · PoC", "medium"),
        ("Unit mode", "sequence · tree · worktrees", "medium"),
        ("Evidence map", "criterion · source · path", "medium"),
        ("Effort policy", "accounting · not a cutoff", "medium"),
    ],
    "D": [
        ("DO", "journal · plan until approval", "weak"),
        ("Code", "inside the contract", "weak"),
        ("Tests", "DO chooses the method", "weak"),
        ("Docs · prose", "README · documentation", "weak"),
        ("Re-anchor", "drift → ACT incomplete", "weak"),
    ],
    "C": [
        ("CHECK · gather", "fork 4 streams + security", "weak"),
        ("Code audit", "collect · candidates", "weak"),
        ("Test lens", "run · coverage", "weak"),
        ("Docs lens", "prose + XML-doc", "weak"),
        ("Perf lens", "measure → judgment", "weak"),
        ("Zero run", "not success", "weak"),
        ("Exceptions", "catalog · threshold", "medium"),
    ],
    "SEC": [
        ("Security audit", "read-only · report → CHECK", "medium"),
    ],
    "E": [
        ("Scout", "pdca-scout · file:line", "weak"),
        ("Escalation", "decides · decision → orb", "strong"),
    ],
    "S": [
        ("Status file", "write · source of truth", "weak"),
        ("Report", "closed / left / blockers", "weak"),
        ("Message", "commit advice · manual", "weak"),
    ],
    "A": [
        ("ACT", "cycle close-out", "weak"),
        ("Lesson", "→ memory", "weak"),
        ("Rules", "AGENTS.md · overlay", "weak"),
        ("Status", "file · outcome", "weak"),
        ("Handoff", "→ EXIT · commit advice", "weak"),
    ],
}

# optional side gather in the security column: facts outside the diff only,
# consulted by the auditor — not a mandatory sequential first step (SKILL.md:929-931)
SEC_OPT = ("Scout (opt.)", "pdca-scout · facts outside diff (opt.)", "weak")

# post-fan sequential steps (after the parallel streams)
TAIL = {"D": [
    ("XML-doc", "after code · if required", "weak"),
    ("Build · tests", "build gate · unit loop", "weak"),
    ("Integr. tests", "DO → CHECK boundary", "weak"),
], "C": [
    ("Triage · verdict", "all streams → pass/fail", "medium"),
]}

# orchestrator inputs, per phase
INPUTS = [
    "PLAN ← “start” · “replan from pdca-check” · “cycle N+1 from ACT”",
    "DO ← “plan ready” · “defect fix from pdca-check (incl. security)” · “fix from pdca-escalate while r not exhausted”",
    "CHECK ← “streams closed”",
    "CHECK · security ← “if: auth / secrets / input / crypto” · “report → CHECK”",
    "ACT ← “pdca-check pass” · “DO cannot finish” · “STOP finalization”",
    "ESCALATION ← “ambiguity” · “repeat after 1 fix / 3rd CHECK(r) failure”\n"
    "“arch/API/hard-security trade-off” · “risky diff acceptance” · “low PLAN/DO confidence”",
    "STOP ← “ACT outcome: no doable PLAN r+1” · “blocker unresolved”\n"
    "“queue empty / remainder blocked” · “iteration limit (n/3)” · “user stop”",
]
# down-arrow (dispatch) label per column
DISPATCH = {"P": "start\nreplan: pdca-check\ncycle N+1", "D": "plan ready · contract/approval\nfix from pdca-check (security)\nfix from pdca-escalate (r active)", "C": "streams closed",
            "SEC": "from CHECK · if\ngather (facts)\nreport → CHECK", "E": "repeat after 1 fix\n3rd CHECK(r) failure\nhard trade-off", "S": "no plan r+1\n→ ACT", "A": "pdca-check pass\nor STOP → ACT"}

# per-phase state-graph node colors (shared by both themes)
STC = {"START": None, "PLAN": "#2563eb", "DO": "#7c3aed", "CHECK": "#d97706",
       "ACT": "#059669", "EXIT": None}

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


def esc(s):
    return html.escape(s, quote=True)


def _fit(text, maxpx, cw):
    if not text:
        return text
    if len(text) * cw <= maxpx:
        return text
    n = max(1, int(maxpx / cw) - 1)
    return text[:n].rstrip() + "\u2026"


def render(P, title):
    def box(x, y, w, h, _title, sub, tier, dash=None):
        col = TIER_COLOR[tier]
        _bw, _bh = 50, 18
        _bx, _by = x + w - _bw - 8, y + 7
        _d = f' stroke-dasharray="{dash}"' if dash else ""
        if P["tint"]:
            _badge = f'<rect x="{_bx}" y="{_by}" width="{_bw}" height="{_bh}" rx="6" fill="{col}" fill-opacity="{P["badge_op"]}" stroke="{col}" stroke-opacity="0.7"/>'
            _btxt = col
        else:
            _badge = f'<rect x="{_bx}" y="{_by}" width="{_bw}" height="{_bh}" rx="6" fill="{col}"/>'
            _btxt = P["badge_text"]
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{P["box"]}" stroke="{P["box_stroke"]}" stroke-width="{P["box_stroke_w"]}"{_d}/>',
               f'<rect x="{x+1}" y="{y+7}" width="3" height="{h-14}" rx="1.5" fill="{col}"/>',
               _badge,
               f'<text x="{_bx+_bw/2}" y="{_by+_bh/2+3.5}" class="bm" fill="{_btxt}" text-anchor="middle">{TIER_MODEL[tier]}</text>',
               f'<text x="{x+13}" y="{y+23}" class="t">{esc(_fit(_title, (_bx-6)-(x+13), 7.4))}</text>']
        if sub:
            out.append(f'<text x="{x+13}" y="{y+42}" class="s">{esc(_fit(sub, (x+w-8)-(x+13), 5.2))}</text>')
        return "\n".join(out)

    def header(x, y, w, h, lbl, col):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{COLOR[col]}"/>'
                f'<text x="{x+w/2}" y="{y+h/2+5}" class="h" text-anchor="middle">{esc(lbl)}</text>')

    def poly(points, color=None, dash=None, marker="arrow", edge_id=None):
        color = color or P["arrow"]
        pts = " ".join(f"{a},{b}" for a, b in points)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        eid = f' data-edge-id="{edge_id}"' if edge_id else ""
        return f'<polyline points="{pts}" fill="none" stroke="{color}"{d}{eid} marker-end="url(#{marker})"/>'

    def label(x, y, text, color=None, anchor="middle"):
        color = color or P["label"]
        return f'<text x="{x}" y="{y}" class="g" fill="{color}" text-anchor="{anchor}">{esc(text)}</text>'

    _MAXROWS = max(len(b) + len(TAIL.get(c, [])) for c, b in BLOCKS.items())
    _COL_BOTTOM = COL_Y + (_MAXROWS - 1) * BOX_STEP + BOX_H + 8
    LEG_Y = _COL_BOTTOM + 48
    SG_TITLE_Y = LEG_Y + 74
    R1_TOP = SG_TITLE_Y + 210
    R1_BOT = R1_TOP + 44
    R2_TOP = R1_TOP + 132
    R2_BOT = R2_TOP + 44
    M4 = R2_BOT + 30
    H = M4 + 40

    s = []
    s.append(f'<svg viewBox="0 0 {W} {H}" width="{W}" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, system-ui, sans-serif">')
    s.append('<defs>\n'
             f'<marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="{P["arrow"]}"/></marker>\n'
             '</defs>\n<style>\n'
             f'.t{{font-size:13px;font-weight:600;fill:{P["title"]}}}\n'
             f'.s{{font-size:10.5px;fill:{P["sub"]}}}\n'
             '.h{font-size:12.5px;font-weight:700;fill:#ffffff}\n'
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

    s.append(f'<rect x="{M}" y="{ORB_Y}" width="{W-M-M}" height="{ORB_H}" rx="10" class="band"/>')
    s.append(f'<text x="{M+18}" y="{ORB_Y+24}" class="bt">Orchestrator · cheap — normal: primary · autonomous: pdca-orchestrator</text>')
    _cw = W - 2 * M
    _col2 = M + 18 + _cw / 2
    _split = (len(INPUTS) + 1) // 2
    _groups = [[], []]
    for _i, _t in enumerate(INPUTS):
        _groups[0 if _i < _split else 1].append(_t.split("\n"))
    for _gi, _group in enumerate(_groups):
        _x = M + 18 if _gi == 0 else _col2
        _row = 0
        for _parts in _group:
            for _k, _ln in enumerate(_parts):
                _off = 0 if _k == 0 else 14
                _pre = "\u2190 " if _k == 0 else "\u00b7 "
                s.append(f'<text x="{_x + _off}" y="{ORB_Y + 52 + _row * 18}" class="ol">{_pre}{esc(_ln)}</text>')
                _row += 1

    def cx(c):
        return COLX[c] + WIDTH[c] / 2

    FAN = {"D", "C"}
    INDENT = 30
    for c in COLN:
        x, w = COLX[c], WIDTH[c]
        blocks = BLOCKS[c]
        s.append(header(x, SPINE_Y, w, SPINE_H, NAME[c], c))
        s.append(poly([(cx(c), SPINE_Y + SPINE_H), (cx(c), COL_Y)]))
        bottom = COL_Y - 8
        if c in FAN:
            t, sub, tier = blocks[0]
            s.append(box(x, COL_Y, w, BOX_H, t, sub, tier))
            bottom = COL_Y + BOX_H
            bus_x = x + 14
            child_x, child_w = x + INDENT, w - INDENT
            last_cy = COL_Y + BOX_H
            for j, (t, sub, tier) in enumerate(blocks[1:], start=1):
                by = COL_Y + j * BOX_STEP
                cyy = by + BOX_H / 2
                s.append(box(child_x, by, child_w, BOX_H, t, sub, tier))
                s.append(poly([(bus_x, cyy), (child_x - 2, cyy)], P["bus"]))
                bottom, last_cy = by + BOX_H, cyy
            s.append(f'<line x1="{bus_x}" y1="{COL_Y+BOX_H}" x2="{bus_x}" y2="{last_cy}" stroke="{P["bus"]}" stroke-width="1.5"/>')
            _row, _prev = len(blocks), bottom
            for (t, sub, tier) in TAIL.get(c, []):
                by = COL_Y + _row * BOX_STEP
                s.append(box(x, by, w, BOX_H, t, sub, tier))
                s.append(f'<path d="M{cx(c)},{_prev} L{cx(c)},{by}" fill="none" stroke="{P["bus"]}" stroke-dasharray="5 4" marker-end="url(#arrow)"/>')
                _prev, bottom, _row = by + BOX_H, by + BOX_H, _row + 1
        elif c == "SEC":
            # mandatory stream: the audit; optional side gather: pdca-scout for facts
            # outside the diff only — dashed, no mandatory sequential first step.
            t, sub, tier = blocks[0]
            s.append(box(x, COL_Y, w, BOX_H, t, sub, tier))
            _audit_bottom = COL_Y + BOX_H
            _sy = COL_Y + BOX_STEP
            # optional side gather, not a parallel task/stream: no indent (full width);
            # the dashed border alone marks it optional
            s.append(box(x, _sy, w, BOX_H, *SEC_OPT, dash="5 4"))
            s.append(f'<path d="M{cx(c)},{_sy} L{cx(c)},{_audit_bottom}" fill="none" stroke="{P["bus"]}" stroke-dasharray="5 4" marker-end="url(#arrow)"/>')
            bottom = _sy + BOX_H
        else:
            for j, (t, sub, tier) in enumerate(blocks):
                by = COL_Y + j * BOX_STEP
                s.append(box(x, by, w, BOX_H, t, sub, tier))
                bottom = by + BOX_H
            if len(blocks) > 1:
                for j in range(len(blocks) - 1):
                    y1 = COL_Y + j * BOX_STEP + BOX_H
                    y2 = COL_Y + (j + 1) * BOX_STEP
                    s.append(poly([(cx(c), y1), (cx(c), y2)], P["bus"]))
        s.append(f'<rect x="{x-6}" y="{COL_Y-8}" width="{w+12}" height="{bottom-COL_Y+16}" rx="12" fill="none" stroke="{COLOR[c]}" stroke-opacity="{P["frame_op"]}" stroke-width="{P["frame_w"]}"/>')

    ORB_B = ORB_Y + ORB_H
    mid = (ORB_B + SPINE_Y) / 2 + 3
    for c in COLN:
        xc = cx(c)
        s.append(poly([(xc - 16, ORB_B), (xc - 16, SPINE_Y)], edge_id=f"dispatch_{c.lower()}"))
        _lines = DISPATCH[c].split("\n")
        _n = len(_lines)
        for _k, _ln in enumerate(_lines):
            s.append(label(xc - 24, mid + (_k - (_n - 1) / 2) * 13, _ln, P["arrow"], "end"))
        if c != "S":
            s.append(poly([(xc + 16, SPINE_Y), (xc + 16, ORB_B)], edge_id=f"return_{c.lower()}"))

    legend = [
        ("#0d9488", "cheap tier", "cheap", "orchestration · pdca-scout · pdca-executor · CHECK gather"),
        ("#4f46e5", "medium tier", "medium", "pdca-planner · pdca-check · pdca-security-auditor"),
        ("#ea580c", "strong tier", "strong", "pdca-escalate"),
    ]
    ly = LEG_Y
    _iw = (W - 2 * M) / 3
    for _i, (_col, _t, _model, _roles) in enumerate(legend):
        _x = M + _i * _iw
        s.append(f'<rect x="{_x}" y="{ly-12}" width="15" height="15" rx="4" fill="{_col}"/>')
        s.append(f'<text x="{_x+22}" y="{ly}" class="lt">{esc(_t)}</text>')
        _mw = len(_model) * 7.4 + 16
        if P["tint"]:
            s.append(f'<rect x="{_x+22}" y="{ly+8}" width="{_mw}" height="21" rx="7" fill="{_col}" fill-opacity="0.12" stroke="{_col}" stroke-opacity="0.65"/>')
            _mtxt = _col
        else:
            s.append(f'<rect x="{_x+22}" y="{ly+8}" width="{_mw}" height="21" rx="7" fill="{_col}"/>')
            _mtxt = "#ffffff"
        s.append(f'<text x="{_x+22+_mw/2}" y="{ly+23}" class="lm" fill="{_mtxt}" text-anchor="middle">{esc(_model)}</text>')
        s.append(f'<text x="{_x+22+_mw+10}" y="{ly+23}" class="ls">{esc(_roles)}</text>')

    # ---- state graph (below the legend) ----
    s.append(f'<text x="{M}" y="{SG_TITLE_Y}" class="lt">The cycle state graph</text>')
    NH, NW = 44, 120
    stx = {"START": 24, "PLAN": 295, "DO": 566, "CHECK": 837, "ACT": 1108, "EXIT": 1379}
    neutral = P["state_neutral"]
    stc = {k: (v or neutral) for k, v in STC.items()}
    for _k, _v in stx.items():
        s.append(f'<rect x="{_v}" y="{R1_TOP}" width="{NW}" height="{NH}" rx="10" fill="{stc[_k]}" fill-opacity="0.08" stroke="{stc[_k]}" stroke-width="1.6" data-node-id="{_k}"/>')
        s.append(f'<text x="{_v+NW/2}" y="{R1_TOP+NH/2+5}" class="st" fill="{stc[_k]}" text-anchor="middle">{esc(_k)}</text>')
    _y = R1_TOP + NH / 2
    for _eid, _a, _b, _lab in [("start_plan", "START", "PLAN", "start"),
                               ("plan_do", "PLAN", "DO", "approval (normal) / instant\n(autonomous) · n=1/3"),
                               ("do_check", "DO", "CHECK", "streams closed"),
                               ("check_act", "CHECK", "ACT", "pass"),
                               ("act_exit", "ACT", "EXIT", "closed")]:
        _x1, _x2 = stx[_a] + NW, stx[_b]
        s.append(poly([(_x1, _y), (_x2, _y)], edge_id=_eid))
        _labs = _lab.split("\n")
        for _k, _ltxt in enumerate(_labs):
            s.append(label((_x1 + _x2) / 2, _y - 7 - (len(_labs) - 1 - _k) * 12, _ltxt, P["label"]))
    s.append(f'<path d="M880,{R1_TOP} C880,{R1_TOP-60} 686,{R1_TOP-60} 686,{R1_TOP}" fill="none" stroke="{P["arrow"]}" marker-end="url(#arrow)" data-edge-id="check_do_defect"/>')
    s.append(label(786, R1_TOP - 46, "defect · n+1 (max 3)", P["label"]))
    s.append(f'<path d="M950,{R1_TOP} C950,{R1_TOP-112} 415,{R1_TOP-112} 415,{R1_TOP}" fill="none" stroke="{P["arrow"]}" marker-end="url(#arrow)" data-edge-id="check_plan_replan"/>')
    s.append(label(683, R1_TOP - 100, "wrong contract · r+1 on revision", P["label"]))
    # DO cannot finish: route below the phase row straight into ACT (never back to PLAN)
    s.append(poly([(626, R1_BOT), (626, R1_BOT + 22), (1160, R1_BOT + 22), (1160, R1_BOT)],
                  P["arrow"], edge_id="do_act_incomplete"))
    s.append(label(893, R1_BOT + 14, "DO cannot finish → ACT (blocked / incomplete)", P["label"]))
    # next cycle: ACT opens a new cycle N+1 (counter grows only in ACT, SKILL.md:133)
    s.append(f'<path d="M1168,{R1_TOP} C1168,{R1_TOP-180} 355,{R1_TOP-180} 355,{R1_TOP}" fill="none" stroke="#059669" stroke-dasharray="5 4" marker-end="url(#arrow)" data-edge-id="act_plan"/>')
    s.append(label(761, R1_TOP - 186, "next cycle · N+1", P["label"]))
    for _nid, _x, _t, _c, _d in [("sec_check", 837, "CHECK stream", "#be123c", True),
                                 ("pdca-escalate", 1100, "ESCALATE", "#b91c1c", False),
                                 ("stop", 1360, "STOP", "#b91c1c", False)]:
        _da = ' stroke-dasharray="5 4"' if _d else ''
        s.append(f'<rect x="{_x}" y="{R2_TOP}" width="{NW}" height="{NH}" rx="10" fill="{_c}" fill-opacity="0.08" stroke="{_c}" stroke-width="1.6"{_da} data-node-id="{_nid}"/>')
        s.append(f'<text x="{_x+NW/2}" y="{R2_TOP+NH/2+5}" class="st" fill="{_c}" text-anchor="middle">{esc(_t)}</text>')
    _y2 = R2_TOP + NH / 2
    # conditional parallel CHECK stream: CHECK forks, stream reports back into CHECK triage
    s.append(poly([(917, R1_BOT), (917, R2_TOP)], "#be123c", dash="5 4", edge_id="check_security"))
    s.append(label(907, (R1_BOT + R2_TOP) / 2 - 6, "if · auth/secrets/input/crypto", "#be123c", "end"))
    s.append(poly([(937, R2_TOP), (937, R1_BOT)], "#be123c", edge_id="security_check_report"))
    s.append(label(947, (R1_BOT + R2_TOP) / 2 + 6, "report → CHECK", "#be123c", "start"))
    # CHECK verdict (all streams aggregated) triggers escalation on repeat / 3rd fail(r)
    s.append(poly([(945, R1_BOT), (945, R1_BOT + 30), (1180, R1_BOT + 30), (1180, R2_TOP)], edge_id="check_escalate_trigger"))
    s.append(label(1070, R1_BOT + 22, "repeat after 1 fix · 3rd CHECK(r) failure", P["label"]))
    # ONLY a hard security tradeoff escalates directly (no ordinary security fail bypass)
    s.append(poly([(955, _y2), (1100, _y2)], "#b91c1c", edge_id="security_escalate_tradeoff"))
    s.append(label(1048, _y2 - 7, "hard trade-off", P["label"]))
    # pdca-escalate decides; no actionable r+1 -> ACT finalizes it, never a STOP beside ACT
    s.append(poly([(1200, R2_TOP), (1200, R1_BOT)], "#b91c1c", edge_id="escalate_act"))
    s.append(label(1208, (R1_BOT + R2_TOP) / 2, "no plan r+1 → ACT", P["label"], "start"))
    # STOP is finalized by ACT and is not a path beside it
    s.append(poly([(1215, R1_BOT), (1215, R2_TOP - 24), (1420, R2_TOP - 24), (1420, R2_TOP)],
                  "#b91c1c", edge_id="act_stop"))
    s.append(label(1320, R2_TOP - 31, "STOP · ACT outcome", P["label"], "start"))
    # pdca-escalate decision -> DO while r not exhausted (current plan)
    s.append(poly([(1160, R2_BOT), (1160, M4), (646, M4), (646, R1_BOT)], edge_id="escalate_do_nonexhausted"))
    s.append(label(850, M4 - 8, "decision · r not exhausted → DO", P["label"]))
    # pdca-escalate decision -> genuine PLAN r+1 only when exhausted; never a 4th DO
    _m4 = M4 + 14
    s.append(poly([(1200, R2_BOT), (1200, _m4), (375, _m4), (375, R1_BOT)], edge_id="escalate_plan_exhausted"))
    s.append(label(760, _m4 + 13, "r exhausted → PLAN r+1", P["label"]))
    s.append('</svg>')
    return "\n".join(s)


def htmlwrap(P, title, svg):
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            f'<title>{esc(title)}</title>'
            f'<style>body{{margin:0;background:{P["bg"]};font-family:Segoe UI,system-ui,sans-serif}}'
            f'.card{{background:{P["card"]};border-radius:12px;margin:20px;padding:12px;box-shadow:{P["shadow"]};overflow:auto}}</style>'
            '<div class="card">' + svg + '</div></html>')


VARIANTS = [
    ("light", "pdca-coder-hand", "pdca-coder — hand layout"),
    ("dark", "pdca-coder-hand-dark", "pdca-coder — hand layout (dark theme)"),
]

for theme, stem, title in VARIANTS:
    P = THEMES[theme]
    svg = render(P, title)
    open(os.path.join(OUT_DIR, stem + ".svg"), "w", encoding="utf-8").write(svg)
    open(os.path.join(OUT_DIR, stem + ".html"), "w", encoding="utf-8").write(htmlwrap(P, title, svg))
    print("wrote %s.{svg,html}" % stem)

print("W=%d" % W)
