#!/usr/bin/env python3
# Hand-laid-out SVG for the pdca-coder workflow:
#   orchestrator band on top with per-phase inputs; columns P/D/C/Безопасность/
#   Эскалация/STOP/A; every phase returns control to the orchestrator.
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
NAME = {"P": "P · PLAN", "D": "D · DO", "C": "C · CHECK", "SEC": "CHECK · security (поток)",
        "E": "ЭСКАЛАЦИЯ", "S": "STOP", "A": "A · ACT"}
TIER_COLOR = {"weak": "#0d9488", "medium": "#4f46e5", "strong": "#ea580c"}
TIER_MODEL = {"weak": "cheap", "medium": "medium", "strong": "strong"}

BLOCKS = {
    "P": [
        ("PLAN", "старт · дизайн", "medium"),
        ("Сбор · gather", "scout + доменные линзы", "weak"),
        ("Decide · planner", "fix / defer · декомпозиция", "medium"),
        ("Критерии · цель", "goal · приёмка (+негатив)", "medium"),
        ("Задачи · риски", "шаги · без TBD", "medium"),
        ("Тесты · Доки", "стратегия · план", "medium"),
        ("Перф-решение", "мерить? · чем · baseline", "medium"),
        ("Разведка (spike)", "нужен ли? · чем · PoC", "medium"),
        ("Юнит-режим", "послед. · дерево · worktrees", "medium"),
    ],
    "D": [
        ("DO", "журнал · план до go", "weak"),
        ("Код", "из плана", "weak"),
        ("Тесты", "из плана", "weak"),
        ("Доки · проза", "README · документация", "weak"),
    ],
    "C": [
        ("CHECK · gather", "форк 4 потоков + security", "weak"),
        ("Аудит кода", "сбор · кандидаты", "weak"),
        ("Линза тестов", "прогон · покрытие", "weak"),
        ("Линза доков", "проза + XML-doc", "weak"),
        ("Линза перфа", "замер → суждение", "weak"),
    ],
    "SEC": [
        ("Аудит безопасности", "read-only · отчёт → CHECK", "medium"),
    ],
    "E": [
        ("Скаут", "scout · факты · file:line", "weak"),
        ("Эскалация", "решает · решение → орб", "strong"),
    ],
    "S": [
        ("Статус-файл", "запись · source of truth", "weak"),
        ("Отчёт", "закрыто / осталось / блокеры", "weak"),
        ("Сообщение", "commit advice · manual", "weak"),
    ],
    "A": [
        ("ACT", "закрытие цикла", "weak"),
        ("Урок", "→ memory", "weak"),
        ("Правила", "AGENTS.md · оверлей", "weak"),
        ("Статус", "файл · итог", "weak"),
        ("Handoff", "→ EXIT · commit advice", "weak"),
    ],
}

# optional side gather in the security column: facts outside the diff only,
# consulted by the auditor — not a mandatory sequential first step (SKILL.md:929-931)
SEC_OPT = ("Скаут (опц.)", "scout · только факты вне диффа (опц.)", "weak")

# post-fan sequential steps (after the parallel streams)
TAIL = {"D": [
    ("XML-doc", "после кода · если требует проект", "weak"),
    ("Сборка · тесты", "build-гейт · unit-луп", "weak"),
    ("Интеграц. тесты", "граница DO → CHECK", "weak"),
], "C": [
    ("Триаж · вердикт", "агрегат всех потоков → pass/fail", "medium"),
]}

# orchestrator inputs, per phase
INPUTS = [
    "PLAN ← «старт» · «реплан от check» · «реплан от DO»",
    "DO ← «план готов» · «фикс дефекта от check (вкл. security)» · «фикс от escalate при r не исчерпан»",
    "CHECK ← «потоки закрыты»",
    "CHECK · security ← «условно: auth / секреты / ввод / crypto» · «отчёт → CHECK»",
    "ACT ← «check pass»",
    "ЭСКАЛАЦИЯ ← «неоднозначность» · «повтор после 1 фикса / 3-й провал CHECK(r)»\n"
    "«arch/API/hard-security trade-off» · «приёмка рискованного диффа» · «низкая уверенность PLAN/DO»",
    "STOP ← «нет выполнимого PLAN r+1» · «блокер не разрешён planner/escalate»\n"
    "«очередь пуста / остаток blocked» · «лимит итераций (n/3)» · «стоп пользователя»",
]
# down-arrow (dispatch) label per column
DISPATCH = {"P": "старт\nреплан от check\nреплан от DO", "D": "план готов\nфикс от check (с security)\nфикс от escalate (r активен)", "C": "потоки закрыты",
            "SEC": "из CHECK · условно\nсбор (gather)\nотчёт → CHECK", "E": "повтор после 1 фикса\n3-й провал CHECK(r)\nжёсткий tradeoff", "S": "нет плана r+1", "A": "check pass"}

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
    s.append(f'<text x="{M+18}" y="{ORB_Y+24}" class="bt">Оркестратор · cheap — normal: primary · autonomous: pdca-orchestrator</text>')
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
            # mandatory stream: the audit; optional side gather: scout for facts
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
        ("#0d9488", "дешёвая ступень", "cheap", "оркестрация · scout · coder · CHECK gather"),
        ("#4f46e5", "средняя ступень", "medium", "planner · check · security-auditor"),
        ("#ea580c", "дорогая ступень", "strong", "escalate"),
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
    s.append(f'<text x="{M}" y="{SG_TITLE_Y}" class="lt">Граф состояний цикла</text>')
    NH, NW = 44, 120
    stx = {"START": 24, "PLAN": 295, "DO": 566, "CHECK": 837, "ACT": 1108, "EXIT": 1379}
    neutral = P["state_neutral"]
    stc = {k: (v or neutral) for k, v in STC.items()}
    for _k, _v in stx.items():
        s.append(f'<rect x="{_v}" y="{R1_TOP}" width="{NW}" height="{NH}" rx="10" fill="{stc[_k]}" fill-opacity="0.08" stroke="{stc[_k]}" stroke-width="1.6" data-node-id="{_k}"/>')
        s.append(f'<text x="{_v+NW/2}" y="{R1_TOP+NH/2+5}" class="st" fill="{stc[_k]}" text-anchor="middle">{esc(_k)}</text>')
    _y = R1_TOP + NH / 2
    for _eid, _a, _b, _lab in [("start_plan", "START", "PLAN", "старт"),
                               ("plan_do", "PLAN", "DO", "go (normal) / сразу\n(autonomous) · n=1/3"),
                               ("do_check", "DO", "CHECK", "потоки закрыты"),
                               ("check_act", "CHECK", "ACT", "pass"),
                               ("act_exit", "ACT", "EXIT", "закрыто")]:
        _x1, _x2 = stx[_a] + NW, stx[_b]
        s.append(poly([(_x1, _y), (_x2, _y)], edge_id=_eid))
        _labs = _lab.split("\n")
        for _k, _ltxt in enumerate(_labs):
            s.append(label((_x1 + _x2) / 2, _y - 7 - (len(_labs) - 1 - _k) * 12, _ltxt, P["label"]))
    s.append(f'<path d="M880,{R1_TOP} C880,{R1_TOP-60} 686,{R1_TOP-60} 686,{R1_TOP}" fill="none" stroke="{P["arrow"]}" marker-end="url(#arrow)" data-edge-id="check_do_defect"/>')
    s.append(label(786, R1_TOP - 46, "дефект · n+1 (до 3)", P["label"]))
    s.append(f'<path d="M950,{R1_TOP} C950,{R1_TOP-112} 415,{R1_TOP-112} 415,{R1_TOP}" fill="none" stroke="{P["arrow"]}" marker-end="url(#arrow)" data-edge-id="check_plan_replan"/>')
    s.append(label(683, R1_TOP - 100, "неверный план · r+1 при ревизии", P["label"]))
    s.append(f'<path d="M606,{R1_TOP} C606,{R1_TOP-60} 405,{R1_TOP-60} 405,{R1_TOP}" fill="none" stroke="{P["arrow"]}" marker-end="url(#arrow)" data-edge-id="do_plan_blocker"/>')
    s.append(label(513, R1_TOP - 46, "новое предусловие/блокер", P["label"]))
    # next cycle: ACT opens a new cycle N+1 (counter grows only in ACT, SKILL.md:133)
    s.append(f'<path d="M1168,{R1_TOP} C1168,{R1_TOP-180} 355,{R1_TOP-180} 355,{R1_TOP}" fill="none" stroke="#059669" stroke-dasharray="5 4" marker-end="url(#arrow)" data-edge-id="act_plan"/>')
    s.append(label(761, R1_TOP - 186, "следующий цикл · N+1", P["label"]))
    for _nid, _x, _t, _c, _d in [("sec_check", 837, "поток CHECK", "#be123c", True),
                                 ("escalate", 1100, "ESCALATE", "#b91c1c", False),
                                 ("stop", 1360, "STOP", "#b91c1c", False)]:
        _da = ' stroke-dasharray="5 4"' if _d else ''
        s.append(f'<rect x="{_x}" y="{R2_TOP}" width="{NW}" height="{NH}" rx="10" fill="{_c}" fill-opacity="0.08" stroke="{_c}" stroke-width="1.6"{_da} data-node-id="{_nid}"/>')
        s.append(f'<text x="{_x+NW/2}" y="{R2_TOP+NH/2+5}" class="st" fill="{_c}" text-anchor="middle">{esc(_t)}</text>')
    _y2 = R2_TOP + NH / 2
    # conditional parallel CHECK stream: CHECK forks, stream reports back into CHECK triage
    s.append(poly([(917, R1_BOT), (917, R2_TOP)], "#be123c", dash="5 4", edge_id="check_security"))
    s.append(label(907, (R1_BOT + R2_TOP) / 2 - 6, "условно · auth/секр/ввод/crypto", "#be123c", "end"))
    s.append(poly([(937, R2_TOP), (937, R1_BOT)], "#be123c", edge_id="security_check_report"))
    s.append(label(947, (R1_BOT + R2_TOP) / 2 + 6, "отчёт → CHECK", "#be123c", "start"))
    # CHECK verdict (all streams aggregated) triggers escalation on repeat / 3rd fail(r)
    s.append(poly([(945, R1_BOT), (945, R1_BOT + 30), (1180, R1_BOT + 30), (1180, R2_TOP)], edge_id="check_escalate_trigger"))
    s.append(label(1070, R1_BOT + 22, "повтор после 1 фикса · 3-й провал CHECK(r)", P["label"]))
    # ONLY a hard security tradeoff escalates directly (no ordinary security fail bypass)
    s.append(poly([(955, _y2), (1100, _y2)], "#b91c1c", edge_id="security_escalate_tradeoff"))
    s.append(label(1048, _y2 - 7, "жёсткий tradeoff", P["label"]))
    # escalate decides; cheap dispatcher routes: no actionable r+1 -> STOP
    s.append(poly([(1220, _y2), (1360, _y2)], "#b91c1c", edge_id="escalate_stop"))
    s.append(label(1310, _y2 - 7, "нет плана r+1", P["label"]))
    # escalate decision -> DO while r not exhausted (current plan)
    s.append(poly([(1160, R2_BOT), (1160, M4), (646, M4), (646, R1_BOT)], edge_id="escalate_do_nonexhausted"))
    s.append(label(850, M4 - 8, "решение · r не исчерпан → DO", P["label"]))
    # escalate decision -> genuine PLAN r+1 only when exhausted; never a 4th DO
    _m4 = M4 + 14
    s.append(poly([(1200, R2_BOT), (1200, _m4), (375, _m4), (375, R1_BOT)], edge_id="escalate_plan_exhausted"))
    s.append(label(760, _m4 + 13, "исчерпан r → PLAN r+1", P["label"]))
    s.append('</svg>')
    return "\n".join(s)


def htmlwrap(P, title, svg):
    return ('<!doctype html><html lang="ru"><meta charset="utf-8">'
            f'<title>{esc(title)}</title>'
            f'<style>body{{margin:0;background:{P["bg"]};font-family:Segoe UI,system-ui,sans-serif}}'
            f'.card{{background:{P["card"]};border-radius:12px;margin:20px;padding:12px;box-shadow:{P["shadow"]};overflow:auto}}</style>'
            '<div class="card">' + svg + '</div></html>')


VARIANTS = [
    ("light", "pdca-coder-hand", "pdca-coder — ручная раскладка"),
    ("dark", "pdca-coder-hand-dark", "pdca-coder — ручная раскладка (тёмная тема)"),
]

for theme, stem, title in VARIANTS:
    P = THEMES[theme]
    svg = render(P, title)
    open(os.path.join(OUT_DIR, stem + ".svg"), "w", encoding="utf-8").write(svg)
    open(os.path.join(OUT_DIR, stem + ".html"), "w", encoding="utf-8").write(htmlwrap(P, title, svg))
    print("wrote %s.{svg,html}" % stem)

print("W=%d" % W)
