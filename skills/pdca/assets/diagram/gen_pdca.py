#!/usr/bin/env python3
"""Hand-laid-out SVG for the universal pdca cycle.

The diagram is domain-neutral. It shows the orchestrator strip with the
per-phase inputs (as in the sibling diagrams), the four phase columns P/D/C/A
plus the non-phase escalation column E (dashed, a transition rather than a
phase) with tier-badged cards (fact-gathering is the `Сбор · gather`
card inside PLAN, as in the sibling diagrams), the cheap/medium/strong tier
legend with the pdca-* roles, and finally the cycle state graph (START, P · PLAN, D · DO,
C · CHECK, A · ACT, EXIT, ЭСКАЛАЦИЯ, STOP) with every side transition.

Two themes (light and dark) render into four artefacts next to this file:
pdca-hand.svg / .html and pdca-hand-dark.svg / .html; `--lang en` writes the
same set with an `-en` suffix. The generator is deterministic: no clock, no
randomness, no absolute path in the output. Standard library only.
"""
import html
import os
import re

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

M = 24
GAP = 28

COLN = ["P", "D", "C", "E", "A"]
WIDTH = {c: 212 for c in COLN}

# Canvas is wide enough for the six-node state graph (its right edge ~1340);
# the phase columns are centred inside it.
W = 1388
_cols_w = len(COLN) * WIDTH[COLN[0]] + (len(COLN) - 1) * GAP
COLX = {}
_x = (W - _cols_w) / 2
for _c in COLN:
    COLX[_c] = _x
    _x += WIDTH[_c] + GAP

ORB_Y, ORB_H = 54, 128
SPINE_Y, SPINE_H = ORB_Y + ORB_H + 44, 40
COL_Y = SPINE_Y + SPINE_H + 16
BOX_H, BOX_STEP = 50, 62

COLOR = {"P": "#2563eb", "D": "#7c3aed",
         "C": "#d97706", "E": "#b91c1c", "A": "#059669"}
NAME = {"P": "P · PLAN", "D": "D · DO",
        "C": "C · CHECK", "E": "E · ESCALATE", "A": "A · ACT"}
# Small non-phase subtitle shown under an otherwise standard header.
SUBTITLE = {"E": "переход, не фаза"}
TIER_COLOR = {"weak": "#0d9488", "medium": "#4f46e5", "strong": "#ea580c"}
TIER_MODEL = {"weak": "cheap", "medium": "medium", "strong": "strong"}

# Universal phase cards, with the responsible role tier on each.
BLOCKS = {
    "P": [
        ("Сбор · gather", "pdca-scout · file:line", "weak"),
        ("Цель · результат", "что и зачем", "medium"),
        ("Запрошено = отдано", "слова пользователя", "medium"),
        ("Форма · скилл", "обоснование выбора", "medium"),
        ("Границы · допущения", "ограничения задачи", "medium"),
        ("Критерии приёмки", "ID · наблюдаемый итог", "medium"),
        ("Средства · доступ", "ограничения, не выбор", "medium"),
        ("Риски · стоп-условия", "когда остановиться", "medium"),
        ("Политика усилий", "оценка · не лимит", "medium"),
    ],
    "D": [
        ("Исполнение контракта", "метод выбирает DO", "weak"),
        ("Units", "ID · связи · owner", "weak"),
        ("Параллельность", "не пересекаются", "weak"),
        ("Evidence", "лог под evidence_root", "weak"),
        ("Blockers", "фиксируются явно", "weak"),
        ("Unfinished", "остаётся открытым", "weak"),
        ("Сверка якорей", "дрейф → incomplete", "weak"),
        ("Candidate-отчёт", "без вердикта · без PASS", "weak"),
    ],
    "C": [
        ("Критерии", "met | unmet | unverified", "medium"),
        ("Оценка критериев", "покрытие и логика", "medium"),
        ("Согласованность", "частей между собой", "medium"),
        ("Findings", "+ severity · свой статус", "medium"),
        ("Нулевой прогон", "не успех", "medium"),
        ("Исключения", "каталог · порог", "medium"),
        ("Маршрутизация", "DO · PLAN · ACT", "medium"),
    ],
    "E": [
        ("Скаут", "pdca-scout · file:line", "weak"),
        ("Триггеры", "неоднозначность", "strong"),
        ("3-й провал", "CHECK(r) исчерпан", "strong"),
        ("Необратимый trade-off", "цена решения", "strong"),
        ("Рекомендация → фазе", "свой переход у каждой", "strong"),
    ],
    "A": [
        ("Финализация", "PASS · incomplete", "weak"),
        ("Ограничения", "границы финализации", "weak"),
        ("Статус-файл", "source of truth", "weak"),
        ("Handoff", "EXIT · PLAN N+1 · STOP", "weak"),
    ],
}

# orchestrator strip: the per-phase inputs (as in the sibling diagrams)
INPUTS = [
    "PLAN ← «старт» · «реплан от CHECK» · «r+1 от ESCALATE» · «цикл N+1 от ACT»",
    "DO ← «апрув от PLAN» · «дефект от CHECK» · «r не исчерпан от ESCALATE»",
    "CHECK ← «units done от DO»",
    "ESCALATE ← «неоднозначность» · «повтор» · «счётчик исчерпан» · «trade-off» · «риск приёмки» · «низкая уверенность PLAN/DO»",
    "ACT ← «все criteria met от CHECK» · «DO не может завершить» · «PLAN-терминал» · «STOP-финализация»",
    "STOP ← «нет плана r+1» · «критерии не определены» · «CHECK исчерпан» · «отказ в approval» — исход ACT",
    "EXIT ← «ACT закрыт»",
]

# down-arrow (dispatch) label per column
DISPATCH = {
    "P": "факты собраны\nреплан от CHECK",
    "D": "план принят · апрув\nякоря сверены",
    "C": "все активные units done\nнулевой выбор ≠ успех",
    "E": "неоднозначность\nповтор · 3-й провал",
    "A": "criteria met\nили STOP → ACT",
}

# tier legend, cheap / medium / strong
LEGEND = [
    ("#0d9488", "дешёвая ступень", "cheap", "pdca-executor · pdca-orchestrator · pdca-scout"),
    ("#4f46e5", "средняя ступень", "medium", "pdca-planner · pdca-check"),
    ("#ea580c", "дорогая ступень", "strong", "pdca-escalate"),
]

THEMES = {
    "light": {
        "bg": "#f1f5f9", "card": "#fff", "shadow": "0 1px 3px rgba(0,0,0,.12)",
        "title": "#0f172a", "sub": "#64748b", "band": "#1f2937",
        "orb_list": "#e6e9ef", "arrow": "#334155", "bus": "#94a3b8",
        "label": "#475569", "box": "#ffffff", "box_stroke": "#cbd5e1",
        "box_stroke_w": 1, "frame_op": 0.35, "frame_w": 1, "tint": True,
        "badge_op": 0.13, "badge_text": None,
        "state_neutral": "#475569",
        "plan": "#2563eb", "do": "#7c3aed", "check": "#d97706",
        "act": "#059669", "escalate": "#b91c1c", "stop": "#7f1d1d",
    },
    "dark": {
        "bg": "#0f172a", "card": "#1e293b", "shadow": "0 1px 3px rgba(0,0,0,.5)",
        "title": "#e2e8f0", "sub": "#94a3b8", "band": "#141d31",
        "orb_list": "#e2e8f0", "arrow": "#94a3b8", "bus": "#64748b",
        "label": "#cbd5e1", "box": "#223046", "box_stroke": "#3b4a63",
        "box_stroke_w": 1, "frame_op": 0.6, "frame_w": 1.6, "tint": False,
        "badge_op": 0.13, "badge_text": "#cbd5e1",
        "state_neutral": "#94a3b8",
        "plan": "#60a5fa", "do": "#a78bfa", "check": "#fbbf24",
        "act": "#34d399", "escalate": "#f87171", "stop": "#dc2626",
    },
}

# --- localization (ru by default; `--lang en` selects English) --------------
LANG = "ru"

# Russian label -> English. Only the labels the diagram draws; anything not
# listed (identifiers such as `met | unmet | unverified`, role names, `STOP`)
# is emitted as-is. Lookup keys are the exact strings in the data above and in
# the render sites below.
_TR_EN = {
    # subtitles / titles
    "переход, не фаза": "a transition, not a phase",
    "Универсальный контракт цикла": "The universal cycle contract",
    "Граф состояний цикла": "The cycle state graph",
    "pdca · оркестратор — входы по фазам · normal: primary · autonomous: pdca-orchestrator (только cheap-тир)":
        "pdca · orchestrator — per-phase inputs · normal: primary · autonomous: pdca-orchestrator (cheap tier only)",
    # PLAN cards
    "Сбор · gather": "Gather",
    "pdca-scout · file:line": "pdca-scout · file:line",
    "Цель · результат": "Goal · result",
    "что и зачем": "what and why",
    "Запрошено = отдано": "Requested = delivered",
    "слова пользователя": "the user's own words",
    "Форма · скилл": "Form · skill",
    "обоснование выбора": "rationale for the choice",
    "Границы · допущения": "Bounds · assumptions",
    "ограничения задачи": "task constraints",
    "Критерии приёмки": "Acceptance criteria",
    "ID · наблюдаемый итог": "ID · observable outcome",
    "Средства · доступ": "Means · access",
    "ограничения, не выбор": "limits, not a choice",
    "Риски · стоп-условия": "Risks · stop rules",
    "когда остановиться": "when to stop",
    "Политика усилий": "Effort policy",
    "оценка · не лимит": "estimate, not a cap",
    # DO cards
    "Исполнение контракта": "Execute the contract",
    "метод выбирает DO": "method chosen by DO",
    "Units": "Units",
    "ID · связи · owner": "ID · links · owner",
    "Параллельность": "Parallelism",
    "не пересекаются": "stay disjoint",
    "лог под evidence_root": "log under evidence_root",
    "Blockers": "Blockers",
    "фиксируются явно": "recorded explicitly",
    "остаётся открытым": "stays open",
    "Сверка якорей": "Anchor re-check",
    "дрейф → incomplete": "drift → incomplete",
    "Candidate-отчёт": "Candidate report",
    "без вердикта · без PASS": "no verdict · no PASS",
    # CHECK cards
    "Критерии": "Criteria",
    "Оценка критериев": "Criteria assessment",
    "покрытие и логика": "requirements · logic",
    "Согласованность": "Consistency",
    "частей между собой": "of the parts",
    "+ severity · свой статус": "+ severity · own status",
    "Маршрутизация": "Routing",
    "DO · PLAN · ACT": "DO · PLAN · ACT",
    "Нулевой прогон": "Zero-selection run",
    "не успех": "not success",
    "Исключения": "Exceptions",
    "каталог · порог": "catalog · threshold",
    # ESCALATE cards
    "Скаут": "Scout",
    "Триггеры": "Triggers",
    "3-й провал": "3rd failure",
    "CHECK(r) исчерпан": "CHECK(r) exhausted",
    "Необратимый trade-off": "Irreversible trade-off",
    "цена решения": "cost of the call",
    "Рекомендация → фазе": "Recommendation",
    "свой переход у каждой": "each keeps its own",
    # ACT cards
    "Финализация": "Finalization",
    "PASS · incomplete": "PASS · incomplete",
    "Ограничения": "Limitations",
    "границы финализации": "finalization bounds",
    "Статус-файл": "Status file",
    "EXIT · PLAN N+1 · STOP": "EXIT · PLAN N+1 · STOP",
    # orchestrator inputs
    "PLAN ← «старт» · «реплан от CHECK» · «r+1 от ESCALATE» · «цикл N+1 от ACT»":
        "PLAN ← “start” · “replan from CHECK” · “r+1 from ESCALATE” · “cycle N+1 from ACT”",
    "DO ← «апрув от PLAN» · «дефект от CHECK» · «r не исчерпан от ESCALATE»":
        "DO ← “approval from PLAN” · “defect from CHECK” · “r not exhausted from ESCALATE”",
    "CHECK ← «units done от DO»": "CHECK ← “units done from DO”",
    "ESCALATE ← «неоднозначность» · «повтор» · «счётчик исчерпан» · «trade-off» · «риск приёмки» · «низкая уверенность PLAN/DO»":
        "ESCALATE ← “ambiguity” · “repeat” · “counter exhausted” · “trade-off” · “acceptance risk” · “low PLAN/DO confidence”",
    "ACT ← «все criteria met от CHECK» · «DO не может завершить» · «PLAN-терминал» · «STOP-финализация»":
        "ACT ← “all criteria met from CHECK” · “DO cannot finish” · “PLAN terminal” · “STOP finalization”",
    "STOP ← «нет плана r+1» · «критерии не определены» · «CHECK исчерпан» · «отказ в approval» — исход ACT":
        "STOP ← “no plan r+1” · “criteria undetermined” · “CHECK exhausted” · “approval refused” — ACT outcome",
    "EXIT ← «ACT закрыт»": "EXIT ← “ACT closed”",
    # dispatch labels (per line, rendered through label())
    "факты собраны": "facts gathered",
    "реплан от CHECK": "replan from CHECK",
    "план принят · апрув": "plan accepted · approval",
    "якоря сверены": "anchors re-checked",
    "фикс дефекта · r активен": "defect fix · r active",
    "все активные units done": "all active units done",
    "нулевой выбор ≠ успех": "zero selection ≠ success",
    "неоднозначность": "ambiguity",
    "повтор · 3-й провал": "repeat · 3rd failure",
    "criteria met": "criteria met",
    "или STOP → ACT": "or STOP → ACT",
    # legend
    "дешёвая ступень": "cheap tier",
    "средняя ступень": "medium tier",
    "дорогая ступень": "strong tier",
    # state-graph node subtitles
    "начало": "start",
    "план": "plan",
    "исполнение": "execute",
    "проверка": "verify",
    "финализация": "finalize",
    "завершение": "exit",
    # state-graph edges
    "старт": "start",
    "сразу (авто)": "instant (auto)",
    "закрыто": "closed",
    "следующий цикл · N+1": "next cycle · N+1",
    "контракт · апрув": "contract · approval",
    "не может завершить → ACT": "cannot finish → ACT",
    "дефект · n+1 (n/3)": "defect · n+1 (n/3)",
    "неверный контракт → CHECK → PLAN · r+1": "wrong contract → CHECK → PLAN · r+1",
    "критерии · невозможность · уже установлено → ACT":
        "criteria · infeasible · already established → ACT",
    "исчерпание": "exhausted",
    "STOP · blocked/incomplete": "STOP · blocked/incomplete",
    "r не исчерпан → DO": "r not exhausted → DO",
    "исчерпан r → PLAN r+1": "r exhausted → PLAN r+1",
    "нет плана r+1 → ACT": "no plan r+1 → ACT",
    # escalation row
    "ЭСКАЛАЦИЯ": "ESCALATION",
    "решение": "decision",
    "терминал": "terminal",
    "исход ACT": "ACT outcome",
    # footer
    "сплошная стрелка — переход": "plain arrow — a transition",
    "дуга — loop-back до ACT": "arc — side route",
    "пунктир — следующий цикл": "dashed — next cycle",
    "нижний ряд — эскалация; STOP — исход ACT": "bottom row — escalation; STOP is an ACT outcome",
}


def T(text):
    """Translate a label for the active language; identity for `ru`/unknown."""
    if LANG == "en" and text is not None:
        return _TR_EN.get(text, text)
    return text


MAXROWS = max(len(b) for b in BLOCKS.values())
COL_BOTTOM = COL_Y + (MAXROWS - 1) * BOX_STEP + BOX_H + 8
LEG_Y = COL_BOTTOM + 74
SG_TITLE_Y = LEG_Y + 56
NH, NW = 56, 156
R1_TOP = SG_TITLE_Y + 190
R2_TOP = R1_TOP + 180
M4 = R2_TOP + NH + 44
H = M4 + 40
STATE_TOP = SG_TITLE_Y - 18


def esc(text):
    return html.escape(str(text), quote=True)


def _fit(text, maxpx, cw):
    if not text:
        return text
    if len(text) * cw <= maxpx:
        return text
    n = max(1, int(maxpx / cw) - 1)
    return text[:n].rstrip() + "\u2026"


def render(P):
    def box(x, y, w, h, _title, sub, tier):
        _title, sub = T(_title), T(sub)
        col = TIER_COLOR[tier]
        _bw, _bh = 58, 17
        _bx, _by = x + w - _bw - 8, y + h - _bh - 6
        if P["tint"]:
            _badge = (f'<rect x="{_bx}" y="{_by}" width="{_bw}" height="{_bh}" rx="6" '
                      f'fill="{col}" fill-opacity="{P["badge_op"]}" stroke="{col}" stroke-opacity="0.7"/>')
            _btxt = col
        else:
            _badge = f'<rect x="{_bx}" y="{_by}" width="{_bw}" height="{_bh}" rx="6" fill="{col}"/>'
            _btxt = P["badge_text"]
        out = [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{P["box"]}" '
            f'stroke="{P["box_stroke"]}" stroke-width="{P["box_stroke_w"]}"/>',
            f'<rect x="{x+1}" y="{y+7}" width="3" height="{h-14}" rx="1.5" fill="{col}"/>',
            _badge,
            f'<text x="{_bx+_bw/2}" y="{_by+_bh/2+3.5}" class="bm" fill="{_btxt}" '
            f'text-anchor="middle">{TIER_MODEL[tier]}</text>',
            f'<text x="{x+14}" y="{y+23}" class="t">{esc(_fit(_title, (x+w-12)-(x+14), 8.0))}</text>',
        ]
        if sub:
            out.append(f'<text x="{x+14}" y="{y+42}" class="s">'
                       f'{esc(_fit(sub, (_bx-6)-(x+14), 5.2))}</text>')
        return "\n".join(out)

    def header(x, y, w, h, lbl, col, secondary=False, sub=None):
        # A secondary header is a transition, not a phase: dashed outline,
        # low-opacity fill, coloured (not white) label. `sub` is a small
        # subtitle rendered under the main label, inside the same box.
        sub = T(sub)
        if secondary:
            _rect = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
                     f'fill="{COLOR[col]}" fill-opacity="0.10" stroke="{COLOR[col]}" '
                     f'stroke-width="1.5" stroke-dasharray="5,4"/>')
            _cls, _fill = "h2", COLOR[col]
        else:
            _rect = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{COLOR[col]}"/>'
            _cls, _fill = "h", "#ffffff"
        lines = str(lbl).split("\n")
        if sub:
            _main_y, _sub_y = y + h / 2 - 2, y + h / 2 + 13
        else:
            _main_y, _sub_y = y + h / 2 + 5, None
        _txt = "".join(
            f'<text x="{x+w/2}" y="{_main_y + (k - (len(lines)-1)/2) * 15}" class="{_cls}" '
            f'fill="{_fill}" text-anchor="middle">{esc(ln)}</text>'
            for k, ln in enumerate(lines))
        if sub:
            _txt += (f'<text x="{x+w/2}" y="{_sub_y}" class="h3" fill="{_fill}" '
                     f'opacity="0.85" text-anchor="middle">{esc(sub)}</text>')
        return _rect + _txt

    def poly(points, color=None, dash=None, marker="arrow", edge_id=None):
        color = color or P["arrow"]
        pts = " ".join(f"{a},{b}" for a, b in points)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        eid = f' data-edge-id="{edge_id}"' if edge_id else ""
        return f'<polyline points="{pts}" fill="none" stroke="{color}"{d}{eid} marker-end="url(#{marker})"/>'

    def curve(d, color, edge_id, dash=None):
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        return (f'<path d="{d}" fill="none" stroke="{color}"{dd} '
                f'data-edge-id="{edge_id}" marker-end="url(#arrow)"/>')

    def label(x, y, text, color=None, anchor="middle"):
        text = T(text)
        color = color or P["label"]
        return f'<text x="{x}" y="{y}" class="g" fill="{color}" text-anchor="{anchor}">{esc(text)}</text>'

    def stnode(x, y, w, h, main, sub, color, node_id):
        main, sub = T(main), T(sub)
        cx = x + w / 2
        out = [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{color}" '
            f'fill-opacity="0.10" stroke="{color}" stroke-width="1.8" data-node-id="{node_id}"/>',
            f'<text x="{cx}" y="{y + h / 2 - 1}" class="st" fill="{color}" text-anchor="middle">{esc(main)}</text>',
        ]
        if sub:
            out.append(f'<text x="{cx}" y="{y + h / 2 + 16}" class="ss" fill="{color}" '
                       f'text-anchor="middle" opacity="0.8">{esc(sub)}</text>')
        return "\n".join(out)

    s = []
    s.append(f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
             f'xmlns="http://www.w3.org/2000/svg" '
             f'font-family="Segoe UI, system-ui, sans-serif" role="img">')
    s.append('<defs>\n'
             f'<marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">'
             f'<path d="M0,0 L7,3 L0,6 Z" fill="{P["arrow"]}"/></marker>\n'
             '</defs>\n<style>\n'
             f'.t{{font-size:13px;font-weight:600;fill:{P["title"]}}}\n'
             f'.s{{font-size:10.5px;fill:{P["sub"]}}}\n'
             '.h{font-size:12.5px;font-weight:700;fill:#ffffff}\n'
             '.h2{font-size:12.5px;font-weight:700}\n'
             '.h3{font-size:9px;font-weight:600}\n'
             '.g{font-size:10.5px;font-weight:600}\n'
             f'.band{{fill:{P["band"]}}}\n'
             '.bt{fill:#ffffff;font-size:15px;font-weight:700}\n'
             f'.ol{{fill:{P["orb_list"]};font-size:11.5px}}\n'
             f'.lt{{font-size:12.5px;font-weight:700;fill:{P["title"]}}}\n'
             f'.ls{{font-size:10.5px;fill:{P["sub"]}}}\n'
             '.lm{font-family:ui-monospace,Consolas,Menlo,monospace;font-size:12px;font-weight:700}\n'
             '.bm{font-family:ui-monospace,Consolas,Menlo,monospace;font-size:10.5px;font-weight:700}\n'
             '.st{font-size:14px;font-weight:700}\n'
             '.ss{font-size:10.5px;font-weight:600}\n'
             '</style>')

    # ---- header + orchestrator strip ----
    s.append(f'<text x="{M}" y="34" class="lt">{esc(T("Универсальный контракт цикла"))}</text>')
    s.append(f'<rect x="{M}" y="{ORB_Y}" width="{W-M-M}" height="{ORB_H}" rx="10" class="band"/>')
    _band = ("pdca · оркестратор — входы по фазам · "
             "normal: primary · autonomous: pdca-orchestrator (только cheap-тир)")
    s.append(f'<text x="{M+18}" y="{ORB_Y+26}" class="bt">{esc(T(_band))}</text>')
    _oc1 = M + 18
    _oc2 = M + 18 + (W - M - M - 36) / 2
    _rows = max(1, (len(INPUTS) + 1) // 2)
    for _i, _t in enumerate(INPUTS):
        _ox = _oc1 if _i < _rows else _oc2
        _oy = ORB_Y + 52 + (_i % _rows) * 18
        s.append(f'<text x="{_ox}" y="{_oy}" class="ol">← {esc(T(_t))}</text>')

    # ---- phase columns ----
    def cx(c):
        return COLX[c] + WIDTH[c] / 2

    for c in COLN:
        x, w = COLX[c], WIDTH[c]
        s.append(header(x, SPINE_Y, w, SPINE_H, NAME[c], c,
                        secondary=(c == "E"), sub=SUBTITLE.get(c)))
        s.append(poly([(cx(c), SPINE_Y + SPINE_H), (cx(c), COL_Y)]))
        bottom = COL_Y
        for j, (t, sub, tier) in enumerate(BLOCKS[c]):
            by = COL_Y + j * BOX_STEP
            s.append(box(x, by, w, BOX_H, t, sub, tier))
            bottom = by + BOX_H
        if len(BLOCKS[c]) > 1:
            for j in range(len(BLOCKS[c]) - 1):
                y1 = COL_Y + j * BOX_STEP + BOX_H
                y2 = COL_Y + (j + 1) * BOX_STEP
                s.append(poly([(cx(c), y1), (cx(c), y2)], P["bus"]))
        _fdash = ' stroke-dasharray="5,4"' if c == "E" else ""
        s.append(f'<rect x="{x-6}" y="{COL_Y-8}" width="{w+12}" height="{bottom-COL_Y+16}" rx="12" '
                 f'fill="none" stroke="{COLOR[c]}" stroke-opacity="{P["frame_op"]}" '
                 f'stroke-width="{P["frame_w"]}"{_fdash}/>')

    # ---- dispatch / return arrows between panel and spine ----
    ORB_B = ORB_Y + ORB_H
    mid = (ORB_B + SPINE_Y) / 2 + 3
    for c in COLN:
        xc = cx(c)
        s.append(poly([(xc - 16, ORB_B), (xc - 16, SPINE_Y)], edge_id=f"dispatch_{c.lower()}"))
        _lines = DISPATCH[c].split("\n")
        _n = len(_lines)
        for _k, _ln in enumerate(_lines):
            s.append(label(xc - 24, mid + (_k - (_n - 1) / 2) * 13, _ln, P["arrow"], "end"))
        s.append(poly([(xc + 16, SPINE_Y), (xc + 16, ORB_B)], edge_id=f"return_{c.lower()}"))

    # ---- tier legend ----
    ly = LEG_Y
    _iw = (W - 2 * M) / 3
    for _i, (_col, _t, _model, _roles) in enumerate(LEGEND):
        _x = M + _i * _iw
        s.append(f'<rect x="{_x}" y="{ly-12}" width="15" height="15" rx="4" fill="{_col}"/>')
        s.append(f'<text x="{_x+22}" y="{ly}" class="lt">{esc(T(_t))}</text>')
        _mw = len(_model) * 7.4 + 16
        if P["tint"]:
            s.append(f'<rect x="{_x+22}" y="{ly+8}" width="{_mw}" height="21" rx="7" fill="{_col}" '
                     f'fill-opacity="0.12" stroke="{_col}" stroke-opacity="0.65"/>')
            _mtxt = _col
        else:
            s.append(f'<rect x="{_x+22}" y="{ly+8}" width="{_mw}" height="21" rx="7" fill="{_col}"/>')
            _mtxt = "#ffffff"
        s.append(f'<text x="{_x+22+_mw/2}" y="{ly+23}" class="lm" fill="{_mtxt}" '
                 f'text-anchor="middle">{esc(_model)}</text>')
        s.append(f'<text x="{_x+22+_mw+10}" y="{ly+23}" class="ls">{esc(_roles)}</text>')

    # ---- state graph ----
    s.append(f'<text x="{M}" y="{SG_TITLE_Y}" class="lt">{esc(T("Граф состояний цикла"))}</text>')
    stx = {"START": 24, "PLAN": 256, "DO": 488, "CHECK": 720, "ACT": 952, "EXIT": 1184}
    stc = {"START": P["state_neutral"], "PLAN": P["plan"], "DO": P["do"],
           "CHECK": P["check"], "ACT": P["act"], "EXIT": P["state_neutral"]}
    st_sub = {"START": "начало", "PLAN": "план", "DO": "исполнение",
              "CHECK": "проверка", "ACT": "финализация", "EXIT": "завершение"}
    st_name = {"START": "START", "PLAN": "P · PLAN", "DO": "D · DO",
               "CHECK": "C · CHECK", "ACT": "A · ACT", "EXIT": "EXIT"}

    for _k, _v in stx.items():
        s.append(stnode(_v, R1_TOP, NW, NH, st_name[_k], st_sub[_k], stc[_k], _k))
    ym = R1_TOP + NH / 2
    # plan_do has both mode paths (normal approval / autonomous immediate) and the
    # 3-iteration cap; it is stacked on short lines so it fits the 76px gap.
    for _eid, _a, _b, _lab in [("start_plan", "START", "PLAN", ["старт"]),
                               ("plan_do", "PLAN", "DO",
                                ["контракт · апрув", "сразу (авто)", "· n=1/3"]),
                               ("do_check", "DO", "CHECK", ["units done"]),
                               ("check_act", "CHECK", "ACT", ["criteria met", "исчерпание"]),
                               ("act_exit", "ACT", "EXIT", ["закрыто"])]:
        _x1, _x2 = stx[_a] + NW, stx[_b]
        s.append(poly([(_x1, ym), (_x2, ym)], edge_id=_eid))
        _n = len(_lab)
        for _k, _ln in enumerate(_lab):
            s.append(label((_x1 + _x2) / 2, ym - 7 - (_n - 1 - _k) * 13, _ln, P["label"]))

    # next cycle: ACT opens a new cycle N+1 (distinct from the terminal act_exit)
    s.append(curve(f"M988,{R1_TOP} C988,{R1_TOP-40} 376,{R1_TOP-40} 376,{R1_TOP}",
                   P["act"], "act_plan", "5,4"))
    s.append(label(682, R1_TOP - 44, "следующий цикл · N+1", P["label"]))
    # DO cannot finish: goes straight to ACT, never back to PLAN
    s.append(curve(f"M566,{R1_TOP} C566,{R1_TOP-72} 1040,{R1_TOP-72} 1040,{R1_TOP}",
                   P["arrow"], "do_act_incomplete"))
    s.append(label(803, R1_TOP - 76, "не может завершить → ACT", P["label"]))
    s.append(curve(f"M798,{R1_TOP} C798,{R1_TOP-104} 566,{R1_TOP-104} 566,{R1_TOP}",
                   P["arrow"], "check_do_defect"))
    s.append(label(682, R1_TOP - 108, "дефект · n+1 (n/3)", P["label"]))
    s.append(curve(f"M798,{R1_TOP} C798,{R1_TOP-136} 334,{R1_TOP-136} 334,{R1_TOP}",
                   P["arrow"], "check_plan_replan"))
    s.append(label(566, R1_TOP - 140, "неверный контракт → CHECK → PLAN · r+1", P["label"]))
    # PLAN terminal: criteria cannot be determined, the original task is proven
    # infeasible, or the supplied facts already establish the requested result.
    s.append(curve(f"M334,{R1_TOP} C334,{R1_TOP-190} 1040,{R1_TOP-190} 1040,{R1_TOP}",
                   P["arrow"], "plan_act_terminal"))
    s.append(label(682, R1_TOP - 168, "критерии · невозможность · уже установлено → ACT", P["label"]))

    # escalation row
    s.append(stnode(488, R2_TOP, NW, NH, "ЭСКАЛАЦИЯ", "решение", P["escalate"], "ESCALATE"))
    s.append(stnode(1184, R2_TOP, NW, NH, "STOP", "исход ACT", P["stop"], "STOP"))
    r1b = R1_TOP + NH
    y2 = R2_TOP + NH / 2
    s.append(curve(f"M798,{r1b} C798,{r1b+80} 566,{R2_TOP-80} 566,{R2_TOP}",
                   P["escalate"], "check_escalate"))
    s.append(label(700, (r1b + R2_TOP) / 2, "повтор · 3-й провал", P["label"]))
    s.append(poly([(516, R2_TOP), (516, r1b)], P["escalate"], edge_id="escalate_do"))
    s.append(label(504, (R2_TOP + r1b) / 2, "r не исчерпан → DO", P["label"], "end"))
    s.append(poly([(488, y2), (334, y2), (334, r1b)], P["escalate"], edge_id="escalate_plan"))
    s.append(label(411, y2 - 10, "исчерпан r → PLAN r+1", P["label"]))
    s.append(poly([(644, y2), (980, y2), (980, r1b)], P["escalate"], edge_id="escalate_act"))
    s.append(label(812, y2 - 10, "нет плана r+1 → ACT", P["label"]))
    # STOP is finalized by ACT, not a path beside it
    s.append(curve(f"M1060,{r1b} C1060,{r1b+60} 1262,{R2_TOP-60} 1262,{R2_TOP}",
                   P["stop"], "act_stop"))
    s.append(label(1128, (r1b + R2_TOP) / 2, "STOP · blocked/incomplete", P["label"], "end"))

    # footer arrow-type legend
    FIN = M4 + 18
    s.append(label(24, FIN, "сплошная стрелка — переход", P["sub"], "start"))
    s.append(label(320, FIN, "дуга — loop-back до ACT", P["sub"], "start"))
    s.append(label(600, FIN, "пунктир — следующий цикл", P["sub"], "start"))
    s.append(label(860, FIN, "нижний ряд — эскалация; STOP — исход ACT", P["sub"], "start"))

    s.append('</svg>')
    return "\n".join(s)


def htmlwrap(P, title, svg, lang="ru"):
    return (
        f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
        f'<title>{esc(title)}</title>'
        f'<style>body{{margin:0;background:{P["bg"]};font-family:Segoe UI,system-ui,sans-serif}}'
        f'.card{{margin:16px auto;max-width:1540px;background:{P["card"]};'
        f'border-radius:12px;padding:10px;box-shadow:{P["shadow"]};overflow:auto}}'
        '</style></head><body>'
        f'<div class="card">{svg}</div>'
        '</body></html>'
    )


def crop(svg: str, top: int, height: int) -> str:
    """Re-frame the full hand SVG as a vertical excerpt (contract / state)."""
    opening = re.match(r'<svg viewBox="0 0 \d+ \d+" width="\d+" height="\d+"', svg)
    if not opening:
        raise SystemExit("unexpected svg header")
    head = '<svg viewBox="0 %d %d %d" width="%d" height="%d"' % (top, W, height, W, height)
    return head + svg[len(opening.group(0)):]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Render the universal pdca diagram (ru/en).")
    ap.add_argument("--lang", choices=["ru", "en"], default="ru",
                    help="label language (default: ru)")
    args = ap.parse_args(argv)
    global LANG
    LANG = args.lang
    suffix = "" if LANG == "ru" else "-en"
    if LANG == "ru":
        titles = ("pdca — ручная раскладка", "pdca — ручная раскладка (тёмная тема)")
    else:
        titles = ("pdca — hand layout", "pdca — hand layout (dark theme)")
    variants = [
        ("light", "pdca-hand" + suffix, titles[0]),
        ("dark", "pdca-hand-dark" + suffix, titles[1]),
    ]
    rendered = {}
    for theme, stem, title in variants:
        palette = THEMES[theme]
        svg = render(palette)
        rendered[theme] = svg
        with open(os.path.join(OUT_DIR, stem + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(svg)
        with open(os.path.join(OUT_DIR, stem + ".html"), "w", encoding="utf-8") as fh:
            fh.write(htmlwrap(palette, title, svg, LANG))
        print("wrote %s.{svg,html}" % stem)
    if LANG == "ru":
        # The slide deck uses the dark diagram split into its contract and state
        # halves; both are deterministic crops of the same rendered artifact.
        print("wrote pdca-contract-dark.svg, pdca-state-dark.svg")
    with open(os.path.join(OUT_DIR, "pdca-contract-dark" + suffix + ".svg"), "w", encoding="utf-8") as fh:
        fh.write(crop(rendered["dark"], 0, STATE_TOP))
    with open(os.path.join(OUT_DIR, "pdca-state-dark" + suffix + ".svg"), "w", encoding="utf-8") as fh:
        fh.write(crop(rendered["dark"], STATE_TOP, H - STATE_TOP))


if __name__ == "__main__":
    main()
