#!/usr/bin/env python3
# Hand-laid-out SVG for the pdca-collection workflow:
#   orchestrator band on top; the peer row P / DO / MERGE / CHECK / ACT is wired
#   straight to the band, while the corrective blocks sit on a second row
#   directly under their trigger (`REPAIR · PDCA` under CHECK, `ESCALATE` under
#   MERGE) joined by a parent->child dispatch/return pair, so the loops read like
#   the state graph.  Mirrors the sibling pdca diagrams so they read alike.
#   as the same family.
# Renders two artefacts: light (collection-hand.*) and dark (collection-hand-dark.*).
import html
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

M = 24
GAP = 28

# The state-graph node box and horizontal step drive the shared canvas width;
# both main rows are spread across that same width.
NW, NH = 160, 44
_G_STEP = 208
_G_ORDER = ["START", "P", "DO", "MERGE", "C", "A", "EXIT"]
GX = {_n: M + _i * _G_STEP for _i, _n in enumerate(_G_ORDER)}

# Top row: the band-connected peer blocks.  The two corrective blocks render on
# a second row directly below their trigger (`REPAIR` under `CHECK`, `ESCALATE`
# under `MERGE`), joined to it by a parent->child arrow pair instead of the
# straight orchestrator bus, so the loop reads like the state graph.
PEER_ROW = ["P", "DO", "MERGE", "C", "A"]
CHILD_PARENT = {"REPAIR": "C", "E": "MERGE"}
COLN = PEER_ROW  # the band and the straight dispatch/result buses cover this row
WIDTH = {"P": 196, "DO": 424, "MERGE": 176, "C": 196,
         "REPAIR": 196, "E": 216, "A": 232}
# full canvas width comes from the lower state graph (`EXIT` right edge + margin)
W = GX["EXIT"] + NW + M
# spread the top row across the canvas
_R1_GAP = (W - 2 * M - sum(WIDTH[c] for c in PEER_ROW)) / (len(PEER_ROW) - 1)
COLX = {}
_x = M
for _c in PEER_ROW:
    COLX[_c] = _x
    _x += WIDTH[_c] + _R1_GAP
# a child block is centred under its parent column
CHILD_X = {
    _ch: COLX[_p] + (WIDTH[_p] - WIDTH[_ch]) / 2
    for _ch, _p in CHILD_PARENT.items()
}

ORB_Y, ORB_H = 24, 138
SPINE_H = 40
BOX_H, BOX_STEP = 50, 62

# ---- central main-column <-> lower-state model ----------------------------
# The main flowchart's seven peer blocks and the lower state graph are two
# projections of one model.  Each peer block maps to exactly one lower state;
# `D · ПОДГОТОВКА` and `ЛЕЙН` are merged into the single composite `DO` column
# (no separate D/LANE peer blocks and no D/LANE alias, never an extra lower
# node or edge).
MAIN_COLUMN_TO_STATE = {
    "P": "P", "DO": "DO", "MERGE": "MERGE",
    "C": "C", "REPAIR": "REPAIR", "E": "ESCALATE", "A": "A",
}

# (from_id, to_id, condition) -- the single source of the lower arrows.
# Forbidden shortcuts (C→DO, C→P, C→EXIT, REPAIR→A/EXIT, ESCALATE→C,
# DO→ESCALATE) are absent by construction.  The normal path is DO→MERGE→C;
# the single-group degradation keeps the direct DO→C bypass; a conflict goes
# MERGE→ESCALATE and the resolution returns ESCALATE→MERGE (the orchestrator
# re-dispatches the retry to `coder`, or the group tip is skipped as
# `incomplete`).  MERGE therefore has exactly two inputs: the phase-DO
# completion and the escalate decision.  The corrective `REPAIR` composition
# returns to a full `C` on success and terminates in the distinct lower `STOP`
# node when the corrective revision is exhausted with no actionable revised
# plan (no 4th implementation CHECK; the collection stays `unverified`).
STATE_EDGES = [
    ("START", "P", "старт"),
    ("P", "DO", "группы"),
    ("DO", "MERGE", "≥2 · all-lanes-terminal"),
    ("DO", "C", "одна группа · без merge"),
    ("MERGE", "C", "интеграция завершена"),
    ("C", "REPAIR", "FAIL"),
    ("REPAIR", "C", "full-verification"),
    ("C", "C", "re-gather"),
    ("C", "A", "PASS"),
    ("A", "EXIT", "finalized"),
    ("MERGE", "ESCALATE", "merge-конфликт"),
    ("ESCALATE", "MERGE", "решено/переставить/пометить incomplete"),
    # repeat of the same defect after one fix escalates before the second fix
    # (base r/n, independent of task id/session): the corrective cycle routes
    # into the strong escalation instead of taking a second fix.
    ("REPAIR", "ESCALATE", "повтор дефекта после 1 фикса"),
    ("REPAIR", "STOP", "ревизия исчерпана · нет плана"),
]

# The single central human-label map, keyed by the FULL edge triple.  Both the
# main event entries and the lower captions read from it (there is no shadow
# DISPATCH string store).  The semantic `condition` strings stay the source of
# truth and are never rewritten here.
EDGE_LABELS = {
    ("START", "P", "старт"): "START: список задач",
    ("P", "DO", "группы"): "PLAN: все планы готовы · группы/порядок зафиксированы",
    ("DO", "MERGE", "≥2 · all-lanes-terminal"): "все группы завершены",
    ("DO", "C", "одна группа · без merge"): "одна группа: без MERGE",
    ("MERGE", "C", "интеграция завершена"): "MERGE завершён",
    ("C", "REPAIR", "FAIL"): "CHECK fail · real defect",
    ("REPAIR", "C", "full-verification"): "REPAIR completed",
    ("C", "C", "re-gather"): "re-gather: blocked",
    ("C", "A", "PASS"): "CHECK pass",
    ("A", "EXIT", "finalized"): "финализация",
    ("MERGE", "ESCALATE", "merge-конфликт"): "MERGE fail",
    ("ESCALATE", "MERGE", "решено/переставить/пометить incomplete"): "ESCALATE: повтор MERGE или incomplete skip",
    ("REPAIR", "ESCALATE", "повтор дефекта после 1 фикса"): "повтор дефекта после 1 фикса",
    ("REPAIR", "STOP", "ревизия исчерпана · нет плана"): "STOP: нет пересмотренного плана",
}

# strict completeness guard: every edge into a mapped peer block must have a
# human label; a missing source key fails loudly instead of silently dropping.
_MAIN_TARGET_STATES = set(MAIN_COLUMN_TO_STATE.values())
for _f, _t, _c in STATE_EDGES:
    if _t in _MAIN_TARGET_STATES and (_f, _t, _c) not in EDGE_LABELS:
        raise ValueError(f"missing human label for edge triple {(_f, _t, _c)!r}")
# every state edge (not just the peer-target ones) must carry a canonical human
# label, so no rendered route caption can silently fall back to the raw condition.
for _f, _t, _c in STATE_EDGES:
    if (_f, _t, _c) not in EDGE_LABELS:
        raise ValueError(f"missing human label for edge triple {(_f, _t, _c)!r}")


def main_events_for_column(col: str) -> list[tuple[str, str, str]]:
    """Incoming lower edges of a peer block, in STATE_EDGES order."""
    lower = MAIN_COLUMN_TO_STATE[col]
    return [(f, t, c) for (f, t, c) in STATE_EDGES if t == lower]


# ---- bus label band: sized before any dependent coordinate ----------------
BUS_LABEL_CW = 6.0
BUS_LABEL_LINE_H = 12
BUS_ENTRY_GAP = 8
BUS_PAD_TOP = 16
BUS_PAD_BOTTOM = 20


def _wrap_label(text: str, maxpx: float, cw: float = BUS_LABEL_CW) -> list[str]:
    """Greedy word wrap; never splits a word, never returns an empty list."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) * cw <= maxpx or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _bus_event_lines(col: str) -> list[list[str]]:
    maxpx = max(40.0, WIDTH[col] / 2 - 24)
    return [
        _wrap_label(EDGE_LABELS[triple], maxpx)
        for triple in main_events_for_column(col)
    ]


_BUS_EVENT_LINES = {c: _bus_event_lines(c) for c in COLN}
_BUS_BAND_H = 0
for _c in COLN:
    _lines_total = sum(len(_ls) for _ls in _BUS_EVENT_LINES[_c])
    _h = _lines_total * BUS_LABEL_LINE_H + max(0, len(_BUS_EVENT_LINES[_c]) - 1) * BUS_ENTRY_GAP
    _BUS_BAND_H = max(_BUS_BAND_H, _h)

ORB_B = ORB_Y + ORB_H
SPINE_Y = ORB_B + BUS_PAD_TOP + _BUS_BAND_H + BUS_PAD_BOTTOM
COL_Y = SPINE_Y + SPINE_H + 16

COLOR = {"P": "#2563eb", "DO": "#7c3aed", "MERGE": "#475569",
         "C": "#d97706", "REPAIR": "#8b5cf6", "E": "#b91c1c", "A": "#059669"}
NAME = {"P": "PLAN", "DO": "DO · ПОДГОТОВКА + ЛЕЙНЫ",
        "MERGE": "MERGE", "C": "CHECK", "REPAIR": "REPAIR",
        "E": "ESCALATE", "A": "ACT"}
TIER_COLOR = {"weak": "#0d9488", "medium": "#4f46e5", "strong": "#ea580c"}
TIER_MODEL = {"weak": "cheap", "medium": "medium", "strong": "strong"}
# workflow composition is a separate axis, never a fourth model tier: the
# `composite` badge reads `составной` in the purple composition colour and is
# grouped apart from the cheap/medium/strong tiers in the legend.
COMPOSITE_COLOR = "#8b5cf6"
COMPOSITE_BADGE = "составной"
# descriptive name of the strong block (body card / band input); the header
# and the lower state-graph node keep the uppercase id `ESCALATE`.
E_BLOCK_NAME = ["Разрешение", "конфликтов слияния"]
# band/arrow prefix per phase; several phases show a display name instead of
# the bare column id so the band matches the main block headers.
DISPLAY_PREFIX = {"P": "PLAN", "C": "CHECK", "E": " ".join(E_BLOCK_NAME), "A": "ACT"}

BLOCKS = {
    "P": [
        ("Вход", "список задач · от пользователя", "weak"),
        # own PLAN of EVERY task runs first, then the all-plans barrier, and only
        # then clustering (DAG/groups); the three planning sub-steps are the
        # semantic `data-step` anchors below.
        ("Свой PLAN задачи", "scout + planner · каждой задачи", "medium"),
        ("ALL-barrier", "все планы готовы · до DAG", "weak"),
        ("DAG · группы", "planner · после барьера", "medium"),
        ("Статус-файл", "plan_state + groups/tasks", "weak"),
    ],
    "DO": [
        ("Worktree + ветки", "coder · на группу", "weak"),
        ("Запуск лейнов", "параллельно · ≤ cap (4)", "weak"),
        ("Лейн · группа", "один Task · оркеструет, не решает", "weak"),
        ("Ветка задачи", "от tip предыдущей · coder", "weak"),
        (("pdca-цикл · continue from saved PLAN", "DO→CHECK→ACT"), "руки cheap · решения medium · эскалация strong", "composite"),
        # autocommit is only available inside the explicitly authorized
        # collection mode (otherwise the next task cannot branch from a committed
        # tip) and the card never grants that permission by itself; without it the
        # results are preserved as a patch.
        ("Коммит · если разрешён автокоммит", "иначе patch · только файлы задачи", "weak"),
    ],
    "MERGE": [
        ("merge --no-ff", "coder · в текущий бранч", "weak"),
        ("По группам", "последовательно · «#<n>»", "weak"),
    ],
    "C": [
        # the mandatory general-`C` measurements, gathered by `coder` (cheap).
        # which checks are obligatory is defined by the task/acceptance criteria
        # (build/tests/lint for code, render/preview for design, …), never
        # hardcoded here.  The verdict itself is the always-run medium `check`
        # card appended inside the column (see render below).
        ("Проверки задачи", "обязательные · по типу работы", "weak"),
        ("Тесты", "функциональные · приёмка", "weak"),
        (("Замеры", "производительности"), "если hot path", "weak"),
        ("Review-линзы", "риск · регресс · соответствие", "weak"),
    ],
    "REPAIR": [
        # the orchestrator-launched corrective standard PDCA composition;
        # `composite` marks the workflow composition, not a model tier.
        # the long title is wrapped so it clears the tier badge instead of
        # running underneath it (a single line is wider than REPAIR's column).
        (("PDCA", "исправления"), "стандартный PDCA · оркестратор", "composite"),
    ],
    "E": [
        ("Скаут", "scout · факты · file:line", "weak"),
        (("Разрешение", "конфликтов слияния"), "merge fail · решает", "strong"),
    ],
    "A": [
        ("Отчёт", "группы · задачи · evidence", "weak"),
        # ACT cleanup is limited to disposable DONE/merged outputs; incomplete
        # results (branches/patch/pointers) are preserved.
        ("Чистка · done/merged", "incomplete сохраняются", "weak"),
        ("Статус-файл", "Done / Verified / Incomplete", "weak"),
    ],
}

# Planning sub-steps of the P column, exposed as `data-step` so the rendered
# order (own PLAN of every task -> all-plans barrier -> clustering) is machine
# checkable and cannot silently collapse back into a pre-DAG footprint pass.
P_SUBSTEP = {
    "Свой PLAN задачи": "task-plan",
    "ALL-barrier": "all-plans-barrier",
    "DAG · группы": "collection-scheduling",
}

# columns that apply only when the collection has >=2 groups; with a single group
# there is nothing to merge (work happens on the current branch).
CONDITIONAL = {"MERGE": "только при ≥2 группах", "REPAIR": "по FAIL от check",
               # per-task cycle variant chosen by the orchestrator
               "DO": ("цикл: .NET/C# → pdca-dotnet · другой код → pdca-coder",
                      "иначе → pdca (по умолчанию)")}

# post-fan sequential steps (after the parallel streams)
TAIL = {}

# orchestrator inputs, per phase -- EVERY incoming event of a phase is enumerated
# (in STATE_EDGES order) with the exact same EDGE_LABELS wording as the arrows and
# the lower captions, so band text, arrows and graph can never drift.  The visible
# prefix is the peer column id; the strong block shows its descriptive name in the
# band/node (`E_BLOCK_NAME`) while its header keeps the uppercase id `ESCALATE`.
for _phase_col in COLN:
    for _phase_triple in main_events_for_column(_phase_col):
        if _phase_triple not in EDGE_LABELS:
            raise ValueError(
                f"missing human label for incoming triple {_phase_triple!r} "
                f"of phase {_phase_col!r}"
            )
INPUTS = [
    "{} ← {}".format(
        DISPLAY_PREFIX.get(_phase_col, _phase_col),
        " · ".join(
            f"«{EDGE_LABELS[_t]}»" for _t in main_events_for_column(_phase_col)
        ),
    )
    for _phase_col in COLN
]

# ---- state-graph layout: single source of nodes and routes ----------------
# Node ids keep the pre-existing ids minus the removed bespoke TRIAGE/BLOCKED
# stages.  The verification node is the semantic id `C` (the standard CHECK
# owned by `check`/medium); `A` is the parent collection ACT (report /
# authorized cleanup / finalize), a real reachable node.  `REPAIR` is the
# standard corrective PDCA composition (composite), triggered by the
# orchestrator on FAIL.  `MERGE` is the explicit integration node (`coder`
# cheap): lanes reach it at their terminal barrier, it hands the integrated
# tree to `C`, and a merge conflict routes through it to `ESCALATE`.
# Two main rows: the peer row (header + cards) then the corrective row, each
# child centred under its parent.  `CHECK` carries one extra always-run verdict
# card, so its row count is len(BLOCKS)+1.
def _main_column_bottom(c: str) -> float:
    # every peer column is its own card stack; C carries one extra always-run
    # verdict card below its measurements.
    if c == "C":
        return COL_Y + len(BLOCKS[c]) * BOX_STEP + BOX_H + 8
    return COL_Y + (len(BLOCKS[c]) - 1) * BOX_STEP + BOX_H + 8


# Each corrective child keeps its own top (just under *its own* parent trigger)
# but the two share one bottom edge, so the corrective row reads as a single
# baseline at the bottom even though CHECK's stack is taller than MERGE's.
_R2_GAP = 56
_PARENT_BOTTOM = {
    "C": _main_column_bottom("C"),
    # clear the five wrapped barrier lines under the narrow MERGE column
    "MERGE": _main_column_bottom("MERGE") + 100,
}


def _natural_spine_y(child: str) -> float:
    return _PARENT_BOTTOM[CHILD_PARENT[child]] + _R2_GAP


def _r2_height(child: str) -> float:
    return (len(BLOCKS[child]) - 1) * BOX_STEP + BOX_H


ROW2_BOT = max(
    _natural_spine_y(child) + SPINE_H + 16 + _r2_height(child)
    for child in CHILD_PARENT
)


def r2_col_y(child: str) -> float:
    return ROW2_BOT - _r2_height(child)


def r2_spine_y(child: str) -> float:
    return r2_col_y(child) - (SPINE_H + 16)


CONTENT_BOTTOM = ROW2_BOT + 56
LEG_Y = CONTENT_BOTTOM + 48
SG_TITLE_Y = LEG_Y + 74
R1_TOP = SG_TITLE_Y + 120
R1_BOT = R1_TOP + NH
R2_TOP = R1_BOT + 76
R2_BOT = R2_TOP + NH
# third graph row: the terminal corrective STOP (unrecoverable), a vertical
# branch directly below `REPAIR`; lower-graph node only, never a main phase.
R3_TOP = R2_BOT + 76
R3_BOT = R3_TOP + NH
M4 = R3_BOT + 34
NOTE_Y = M4 + 28
# six footnote lines (single-group/no-rollback, autocommit, merge barrier,
# STOP/cleanup, lane definition, flat primary fallback) with a bottom margin.
H = NOTE_Y + 16 * 5 + 40

# x/y are generator-owned absolute layout; `tier` is the visible model tier
# (cheap/medium/strong); `composite` marks the workflow composition, not a fourth
# model tier.  `annotation` is a small local visible note rendered under the node.
STATE_NODES = {
    "START":      {"x": GX["START"], "y": R1_TOP, "label": "START",        "tier": None},
    "P":          {"x": GX["P"],     "y": R1_TOP, "label": "PLAN",          "tier": None},
    "DO":         {"x": GX["DO"],    "y": R1_TOP, "label": ["DO · ПОДГОТОВКА", "+ ЛЕЙНЫ"], "tier": "cheap"},
    "MERGE":      {"x": GX["MERGE"], "y": R1_TOP, "label": "MERGE",         "tier": "cheap",
                   "owner": "coder · cheap"},
    "C":          {"x": GX["C"],     "y": R1_TOP, "label": "CHECK",         "tier": "medium",
                   "owner": "check · medium"},
    "A":          {"x": GX["A"],     "y": R1_TOP, "label": "ACT",           "tier": None},
    "EXIT":       {"x": GX["EXIT"],  "y": R1_TOP, "label": "EXIT",          "tier": None},
    "REPAIR":     {"x": GX["C"],     "y": R2_TOP, "label": "REPAIR",         "composite": True,
                   "owner": "pdca · составной"},
    "ESCALATE":   {"x": GX["MERGE"], "y": R2_TOP, "label": "ESCALATE",      "tier": "strong",
                   # the escalated decision is only routed by the orchestrator:
                   # a revised plan goes to planner, implementation/STOP to coder.
                   # kept left of the node so it clears the REPAIR->ESCALATE route.
                   "annotation": ["решение → planner (план)",
                                  "или coder (реализация, STOP)"],
                   "annotation_x": GX["MERGE"] - 12, "annotation_anchor": "end"},
    "STOP":       {"x": GX["C"],     "y": R3_TOP, "label": "STOP",          "tier": None,
                   "annotation": "unverified · без ACT/cleanup"},
}

STATE_COLOR = {"START": None, "P": "#2563eb", "DO": "#7c3aed", "MERGE": "#475569",
               "C": "#4f46e5", "A": "#059669", "EXIT": None,
               "REPAIR": "#8b5cf6", "ESCALATE": "#b91c1c", "STOP": "#b91c1c"}

_R1C = R1_TOP + NH / 2
_MID = (R1_BOT + R2_TOP) / 2
_MID3 = (R2_BOT + R3_TOP) / 2
_BYPASS_TOP = R1_TOP - 40
# Every corrective loop is a tight parallel pair of vertical arrows below its
# source node (`REPAIR` under `C`, `ESCALATE` under `MERGE`); captions sit
# outside the pair, so no long horizontal channel ever crosses another route
# and the only detour (the single-group DO→C bypass) runs above row 1.
_GDO = GX["DO"] + NW / 2       # DO node centre
_GMC = GX["MERGE"] + NW / 2    # MERGE node centre
_GCC = GX["C"] + NW / 2        # CHECK node centre
_C_TOP_X = GX["C"] + 20        # DO→C bypass attachment on the CHECK top edge
ROUTES = {
    ("START", "P"): {"points": [(GX["START"] + NW, _R1C), (GX["P"], _R1C)]},
    ("P", "DO"): {"points": [(GX["P"] + NW, _R1C), (GX["DO"], _R1C)]},
    ("DO", "MERGE"): {"points": [(GX["DO"] + NW, _R1C), (GX["MERGE"], _R1C)]},
    ("MERGE", "C"): {"points": [(GX["MERGE"] + NW, _R1C), (GX["C"], _R1C)]},
    ("C", "A"): {"points": [(GX["C"] + NW, _R1C), (GX["A"], _R1C)]},
    ("A", "EXIT"): {"points": [(GX["A"] + NW, _R1C), (GX["EXIT"], _R1C)]},
    # single-group degradation: DO → C skips MERGE over the top of row 1
    ("DO", "C"): {"points": [(_GDO, R1_TOP), (_GDO, _BYPASS_TOP),
                             (_C_TOP_X, _BYPASS_TOP), (_C_TOP_X, R1_TOP)],
                  "caption": EDGE_LABELS[("DO", "C", "одна группа · без merge")],
                  "label": ((_GDO + _C_TOP_X) / 2, _BYPASS_TOP - 8)},
    # orchestrator dispatches the standard corrective PDCA on a real FAIL;
    # `REPAIR` sits directly below `C` as a tight vertical loop.
    ("C", "REPAIR"): {"points": [(_GCC - 15, R1_BOT), (_GCC - 15, R2_TOP)],
                      "caption": EDGE_LABELS[("C", "REPAIR", "FAIL")],
                      "dispatched_by": "orchestrator",
                      "label": (_GCC - 64, _MID)},
    # corrective ACT returns to a full parent CHECK (not a shortcut to ACT);
    # reverse arrows are never captioned.
    ("REPAIR", "C"): {"points": [(_GCC + 15, R2_TOP), (_GCC + 15, R1_BOT)],
                      "caption": []},
    # a missing mandatory report is re-gathered by the existing gather path;
    # this is a `blocked`/awaiting-reports state, NOT a code defect and never a
    # REPAIR trigger (no edits).
    ("C", "C"): {"points": [(GX["C"] + 113, R1_TOP), (GX["C"] + 113, R1_TOP - 20),
                            (GX["C"] + 193, R1_TOP - 20), (GX["C"] + 193, R1_TOP + 28),
                            (GX["C"] + 160, R1_TOP + 28)],
                 "caption": _wrap_label(EDGE_LABELS[("C", "C", "re-gather")], 80),
                 "label": (GX["C"] + 153, R1_TOP - 60)},
    # conflict is discovered at MERGE; `ESCALATE` sits directly below it as a
    # tight vertical loop.
    ("MERGE", "ESCALATE"): {"points": [(_GMC - 15, R1_BOT), (_GMC - 15, R2_TOP)],
                            "caption": EDGE_LABELS[("MERGE", "ESCALATE", "merge-конфликт")],
                            "label": (_GMC - 107, _MID - 8)},
    # resolution returns to MERGE; the ORCHESTRATOR re-dispatches coder's retry
    # (the strong expert itself never patches) or the group tip is skipped as
    # `incomplete`.  Reverse arrows are uncaptioned.
    ("ESCALATE", "MERGE"): {"points": [(_GMC + 15, R2_TOP), (_GMC + 15, R1_BOT)],
                            "caption": [],
                            "dispatched_by": "orchestrator"},
    # repeat of the same defect after one fix -> escalate before the second fix;
    # routed through the clear band below the corrective row (no crossing of the
    # dispatch/return pair above).
    ("REPAIR", "ESCALATE"): {"points": [(GX["C"] + 40, R2_BOT),
                                        (GX["C"] + 40, R2_BOT + 36),
                                        (GX["MERGE"] + NW / 2, R2_BOT + 36),
                                        (GX["MERGE"] + NW / 2, R2_BOT)],
                             "caption": _wrap_label(
                                 EDGE_LABELS[("REPAIR", "ESCALATE", "повтор дефекта после 1 фикса")],
                                 92),
                             "label": ((GX["C"] + 40 + GX["MERGE"] + NW / 2) / 2, R2_BOT + 12)},
    # unrecoverable corrective outcome: the standard corrective revision is
    # exhausted and there is no actionable revised plan -> STOP, a distinct
    # terminal (never a successful EXIT), preserving evidence with no ACT.
    ("REPAIR", "STOP"): {"points": [(_GCC, R2_BOT), (_GCC, R3_TOP)],
                         "caption": _wrap_label(
                             EDGE_LABELS[("REPAIR", "STOP", "ревизия исчерпана · нет плана")],
                             200),
                         "label": (_GCC + 46, _MID3 - 6),
                         "anchor": "start"},
}

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
    def box(x, y, w, h, _title, sub, tier):
        _composite = tier == "composite"
        col = COMPOSITE_COLOR if _composite else TIER_COLOR[tier]
        _label = COMPOSITE_BADGE if _composite else TIER_MODEL[tier]
        _bw, _bh = (78, 18) if _composite else (50, 18)
        _bx, _by = x + w - _bw - 8, y + 7
        if P["tint"]:
            _badge = f'<rect x="{_bx}" y="{_by}" width="{_bw}" height="{_bh}" rx="6" fill="{col}" fill-opacity="{P["badge_op"]}" stroke="{col}" stroke-opacity="0.7"/>'
            _btxt = col
        else:
            _badge = f'<rect x="{_bx}" y="{_by}" width="{_bw}" height="{_bh}" rx="6" fill="{col}"/>'
            _btxt = P["badge_text"]
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{P["box"]}" stroke="{P["box_stroke"]}" stroke-width="{P["box_stroke_w"]}"/>',
               f'<rect x="{x+1}" y="{y+7}" width="3" height="{h-14}" rx="1.5" fill="{col}"/>',
               _badge,
               f'<text x="{_bx+_bw/2}" y="{_by+_bh/2+3.5}" class="bm" fill="{_btxt}" text-anchor="middle">{_label}</text>']
        # local wrapped-title support for the long descriptive card names; a
        # single line keeps the historical baselines, two lines fit the same
        # 50px card (title lines y+20/y+34, subtitle y+47) so no card grows.
        lines = _title if isinstance(_title, (list, tuple)) else [_fit(_title, (_bx-6)-(x+13), 7.4)]
        for _i, _line in enumerate(lines):
            _line_y = y + 23 if len(lines) == 1 else y + 20 + _i * 14
            out.append(f'<text x="{x+13}" y="{_line_y}" class="t">{esc(_line)}</text>')
        if sub:
            _sub_y = y + 42 + max(0, len(lines) - 1) * 5
            out.append(f'<text x="{x+13}" y="{_sub_y}" class="s">{esc(_fit(sub, (x+w-8)-(x+13), 5.2))}</text>')
        return "\n".join(out)

    def header(x, y, w, h, lbl, col):
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{COLOR[col]}"/>']
        lines = lbl if isinstance(lbl, (list, tuple)) else [lbl]
        if len(lines) == 1:
            out.append(f'<text x="{x+w/2}" y="{y+h/2+5}" class="h" text-anchor="middle">{esc(lines[0])}</text>')
        else:
            # local two-line support for the long descriptive peer names; the
            # header keeps its height so every peer baseline stays aligned
            _y0 = y + h / 2 - 3
            for _i, _line in enumerate(lines):
                out.append(f'<text x="{x+w/2}" y="{_y0 + _i*15}" class="h" text-anchor="middle">{esc(_line)}</text>')
        return "".join(out)

    def poly(points, color=None, dash=None, marker: "str | None" = "arrow"):
        color = color or P["arrow"]
        pts = " ".join(f"{a},{b}" for a, b in points)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#{marker})"' if marker else ""
        return f'<polyline points="{pts}" fill="none" stroke="{color}"{d}{m}/>'

    def label(x, y, text, color=None, anchor="middle"):
        color = color or P["label"]
        return f'<text x="{x}" y="{y}" class="g" fill="{color}" text-anchor="{anchor}">{esc(text)}</text>'

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
             f'.nt{{font-size:10.5px;fill:{P["sub"]}}}\n'
             '.lm{font-family:ui-monospace,Consolas,Menlo,monospace;font-size:12px;font-weight:700}\n'
             '.bm{font-family:ui-monospace,Consolas,Menlo,monospace;font-size:10.5px;font-weight:700}\n'
             '.st{font-size:14px;font-weight:700}\n'
             '</style>')

    s.append(f'<rect x="{M}" y="{ORB_Y}" width="{W-M-M}" height="{ORB_H}" rx="10" class="band" data-band="orchestrator"/>')
    s.append(f'<text x="{M+18}" y="{ORB_Y+24}" class="bt">Оркестратор · pdca-collection — входы по фазам</text>')
    _cw = W - 2 * M
    _col2 = M + 18 + _cw / 2
    # balance the phase inputs across the two band columns instead of a fixed 4+1
    _rows = max(1, (len(INPUTS) + 1) // 2)
    for _i, _t in enumerate(INPUTS):
        _x = M + 18 if _i < _rows else _col2
        _y = ORB_Y + 52 + (_i % _rows) * 18
        s.append(f'<text x="{_x}" y="{_y}" class="ol">← {esc(_t)}</text>')

    def cx(c):
        return COLX[c] + WIDTH[c] / 2

    for c in COLN:
        x, w = COLX[c], WIDTH[c]
        blocks = BLOCKS[c]
        INDENT = 30
        # Every phase is an addressable peer column root.  C additionally carries
        # its owner tier; REPAIR is the orchestrator-dispatched corrective PDCA
        # composition (a peer, never a card below C).
        _cattrs = f'data-column="{c}"'
        if c == "C":
            # the whole verification column is one addressable group owned by
            # the medium `check`: four cheap measurements + the verdict card.
            _cattrs += ' data-role="check" data-tier="medium"'
        elif c == "REPAIR":
            _cattrs += (' data-main-recovery="corrective-pdca"'
                        ' data-dispatched-by="orchestrator"'
                        ' data-composition="composite"')
        s.append(f'<g {_cattrs}>')
        # the real header background rect, addressable for peer-baseline checks
        s.append(f'<g data-peer-header="{c}">')
        s.append(header(x, SPINE_Y, w, SPINE_H, NAME[c], c))
        s.append('</g>')
        s.append(poly([(cx(c), SPINE_Y + SPINE_H), (cx(c), COL_Y)]))
        bottom = COL_Y - 8
        if c == "DO":
            # `D · ПОДГОТОВКА`'s two prep cards are full width; below them the lane
            # parent `Лейн · группа` is full width and its four steps are nested
            # sub-blocks (narrower, shifted right by INDENT), wired sequentially and
            # looped back by the "следующая ветка группы" arrow on the left.
            n_head = 3  # Worktree+ветки, Запуск лейнов, Лейн · группа (parent)
            for j in range(n_head):
                t, sub, tier = blocks[j]
                s.append(box(x, COL_Y + j * BOX_STEP, w, BOX_H, t, sub, tier))
                bottom = COL_Y + j * BOX_STEP + BOX_H
                if j:
                    y1 = COL_Y + (j - 1) * BOX_STEP + BOX_H
                    y2 = COL_Y + j * BOX_STEP
                    s.append(poly([(cx(c), y1), (cx(c), y2)], P["bus"]))
            child_x, child_w = x + INDENT, w - INDENT
            ccx = child_x + child_w / 2
            # lane parent bottom -> first child top, at the child center
            s.append(poly([(ccx, COL_Y + (n_head - 1) * BOX_STEP + BOX_H),
                           (ccx, COL_Y + n_head * BOX_STEP)], P["bus"]))
            prev_bottom = COL_Y + n_head * BOX_STEP
            for j, (t, sub, tier) in enumerate(blocks[n_head:], start=n_head):
                by = COL_Y + j * BOX_STEP
                s.append(box(child_x, by, child_w, BOX_H, t, sub, tier))
                if j > n_head:
                    s.append(poly([(ccx, prev_bottom), (ccx, by)], P["bus"]))
                bottom = by + BOX_H
                prev_bottom = by + BOX_H
            cy_first = COL_Y + n_head * BOX_STEP + BOX_H / 2
            cy_last = COL_Y + (len(blocks) - 1) * BOX_STEP + BOX_H / 2
            gx = x + 16
            s.append(f'<path d="M{child_x},{cy_last} L{gx},{cy_last} L{gx},{cy_first} L{child_x},{cy_first}" fill="none" stroke="{P["bus"]}" marker-end="url(#arrow)"/>')
            _my = (cy_first + cy_last) / 2
            # inside a lane the loop-back is task-to-task: after the committed
            # task the next task branches from its tip.
            s.append(f'<text x="{gx - 5}" y="{_my}" class="g" fill="{P["label"]}" text-anchor="middle" transform="rotate(-90 {gx - 5} {_my})">следующая задача</text>')
        else:
            for j, (t, sub, tier) in enumerate(blocks):
                by = COL_Y + j * BOX_STEP
                step = P_SUBSTEP.get(t) if c == "P" else None
                if step is not None:
                    s.append(f'<g data-step="{step}">')
                s.append(box(x, by, w, BOX_H, t, sub, tier))
                if step is not None:
                    s.append('</g>')
                bottom = by + BOX_H
            if len(blocks) > 1:
                for j in range(len(blocks) - 1):
                    y1 = COL_Y + j * BOX_STEP + BOX_H
                    y2 = COL_Y + (j + 1) * BOX_STEP
                    s.append(poly([(cx(c), y1), (cx(c), y2)], P["bus"]))
        if c == "C":
            # the standard CHECK verdict is an *always-run* medium card,
            # independent of whether the raw command measurements are green.
            vy = COL_Y + len(blocks) * BOX_STEP
            y1 = COL_Y + (len(blocks) - 1) * BOX_STEP + BOX_H
            s.append(poly([(cx(c), y1), (cx(c), vy)], P["bus"]))
            s.append('<g data-step="check-verdict" data-role="check" data-tier="medium">')
            s.append(box(x, vy, w, BOX_H, "Вердикт", "check · PASS / FAIL", "medium"))
            s.append('</g>')
            bottom = vy + BOX_H
        _frame = f'<rect x="{x-6}" y="{COL_Y-8}" width="{w+12}" height="{bottom-COL_Y+16}" rx="12" fill="none" stroke="{COLOR[c]}" stroke-opacity="{P["frame_op"]}" stroke-width="{P["frame_w"]}" data-frame="{c}"/>'
        if c == "MERGE":
            # the actual all-terminal merge barrier (>=2 groups): every lane must be
            # terminal (done or incomplete) before the sequential merge of the
            # successful tips; `incomplete` tips are skipped.  The visible label
            # lives *inside* this marker group and is wrapped to the narrow column.
            s.append('<g data-condition="all-lanes-terminal">')
            s.append(_frame)
            s.append(f'<text x="{cx(c)}" y="{bottom + 25}" class="g" fill="{P["label"]}" text-anchor="middle">{esc(CONDITIONAL[c])}</text>')
            s.append(f'<text x="{cx(c)}" y="{bottom + 40}" class="g" fill="{P["label"]}" text-anchor="middle">barrier · ALL LANES TERMINAL</text>')
            s.append(f'<text x="{cx(c)}" y="{bottom + 55}" class="ls" fill="{P["sub"]}" text-anchor="middle">done | incomplete</text>')
            s.append(f'<text x="{cx(c)}" y="{bottom + 70}" class="ls" fill="{P["sub"]}" text-anchor="middle">merge только done</text>')
            s.append(f'<text x="{cx(c)}" y="{bottom + 85}" class="ls" fill="{P["sub"]}" text-anchor="middle">incomplete · skip</text>')
            s.append('</g>')
        else:
            s.append(_frame)
            if c in CONDITIONAL:
                _cond = CONDITIONAL[c]
                _cond_lines = _cond if isinstance(_cond, (list, tuple)) else [_cond]
                for _ci, _cline in enumerate(_cond_lines):
                    s.append(f'<text x="{cx(c)}" y="{bottom + 25 + _ci*15}" class="g" fill="{P["label"]}" text-anchor="middle">{esc(_cline)}</text>')
        s.append('</g>')

    # ---- second row: the corrective blocks under their triggers -------------
    for _child, _parent in CHILD_PARENT.items():
        x, w = CHILD_X[_child], WIDTH[_child]
        blocks = BLOCKS[_child]
        _ccx = x + w / 2
        _spine = r2_spine_y(_child)
        _cy = r2_col_y(_child)
        _cattrs = (f'data-column="{_child}" data-child-of="{_parent}"'
                   ' data-dispatched-by="orchestrator"')
        if _child == "REPAIR":
            _cattrs += (' data-main-recovery="corrective-pdca"'
                        ' data-composition="composite"')
        s.append(f'<g {_cattrs}>')
        s.append(f'<g data-peer-header="{_child}">')
        s.append(header(x, _spine, w, SPINE_H, NAME[_child], _child))
        s.append('</g>')
        s.append(poly([(_ccx, _spine + SPINE_H), (_ccx, _cy)]))
        _bottom = _cy
        for j, (t, sub, tier) in enumerate(blocks):
            by = _cy + j * BOX_STEP
            s.append(box(x, by, w, BOX_H, t, sub, tier))
            _bottom = by + BOX_H
            if j:
                y1 = _cy + (j - 1) * BOX_STEP + BOX_H
                s.append(poly([(_ccx, y1), (_ccx, by)], P["bus"]))
        s.append(f'<rect x="{x-6}" y="{_cy-8}" width="{w+12}" height="{_bottom-_cy+16}" rx="12" fill="none" stroke="{COLOR[_child]}" stroke-opacity="{P["frame_op"]}" stroke-width="{P["frame_w"]}" data-frame="{_child}"/>')
        if _child in CONDITIONAL:
            _cond = CONDITIONAL[_child]
            _cond_lines = _cond if isinstance(_cond, (list, tuple)) else [_cond]
            for _ci, _cline in enumerate(_cond_lines):
                s.append(f'<text x="{_ccx}" y="{_bottom + 25 + _ci*15}" class="g" fill="{P["label"]}" text-anchor="middle">{esc(_cline)}</text>')
        s.append('</g>')

        # parent->child connector: down = trigger dispatch, up = return.  The
        # orchestrator mediation stays in data-dispatched-by, not a caption.
        _pcx = COLX[_parent] + WIDTH[_parent] / 2
        _pb = _PARENT_BOTTOM[_parent]
        _cstate = MAIN_COLUMN_TO_STATE[_child]
        _pstate = MAIN_COLUMN_TO_STATE[_parent]
        # enumerate EVERY incoming event of the child (its own dispatch path is
        # one physical arrow; the event labels are grouped, wrapped to the column)
        _incomings = [t for t in STATE_EDGES if t[1] == _cstate]
        _down_x, _up_x = _pcx - 15, _pcx + 15
        s.append(f'<g data-bus="dispatch" data-origin="{_parent}" '
                 f'data-target="{_child}" data-kind="dispatch">')
        s.append(poly([(_down_x, _pb), (_down_x, _spine)]))
        _ly = _spine - 30
        for _incoming in _incomings:
            s.append(f'<g data-entry-from="{esc(_incoming[0])}" '
                     f'data-entry-to="{esc(_incoming[1])}" '
                     f'data-entry-condition="{esc(_incoming[2])}">')
            for _ln in _wrap_label(EDGE_LABELS[_incoming], 104):
                s.append(label(_down_x - 8, _ly, _ln, P["label"], "end"))
                _ly += 12
            s.append('</g>')
        s.append('</g>')
        s.append(f'<g data-bus="result" data-origin="{_child}" '
                 f'data-target="{_parent}" data-kind="result">')
        s.append(poly([(_up_x, _spine), (_up_x, _pb)]))
        # reverse arrows are never captioned: the return event is already listed
        # as an incoming event of the parent phase in the orchestrator band.
        s.append('</g>')

    # Orchestrator <-> peer buses.  Every phase column is wired straight to the
    # top band by ONE generic dispatch path (band->header, down) and ONE result
    # path (header->band, up).  The dispatch path is a single physical arrow; its
    # incoming events are separate visible label groups derived from the lower
    # STATE_EDGES (`data-entry-from/to/condition`), so the main event set cannot
    # drift from the lower graph.  The composite `DO` column shows its single
    # `P -> DO` event (no separate `D`/`LANE` columns); `MERGE` no longer has a
    # bespoke second branch.
    for c in COLN:
        xc = cx(c)
        s.append(f'<g data-bus="dispatch" data-origin="orchestrator" '
                 f'data-target="{c}" data-kind="dispatch">')
        s.append(poly([(xc - 16, ORB_B), (xc - 16, SPINE_Y)]))
        _event_lines = _BUS_EVENT_LINES[c]
        _total = (
            sum(len(_ls) for _ls in _event_lines) * BUS_LABEL_LINE_H
            + max(0, len(_event_lines) - 1) * BUS_ENTRY_GAP
        )
        _y = ORB_B + BUS_PAD_TOP + (_BUS_BAND_H - _total) / 2
        for _triple, _lines in zip(main_events_for_column(c), _event_lines):
            _from, _to, _cond = _triple
            s.append(f'<g data-entry-from="{esc(_from)}" data-entry-to="{esc(_to)}" '
                     f'data-entry-condition="{esc(_cond)}">')
            for _ln in _lines:
                _y += BUS_LABEL_LINE_H
                s.append(label(xc - 20, _y - 3, _ln, P["arrow"], "end"))
            s.append('</g>')
            _y += BUS_ENTRY_GAP
        s.append('</g>')
        s.append(f'<g data-bus="result" data-origin="{c}" '
                 f'data-target="orchestrator" data-kind="result">')
        s.append(poly([(xc + 16, SPINE_Y), (xc + 16, ORB_B)]))
        # user correction: outgoing result arrows are drawn but never captioned.
        # The block->orchestrator return is still a real arrow (marker + both
        # endpoints) carrying the caller identity via the bus group attributes.
        s.append('</g>')

    legend = [
        ("#0d9488", "дешёвая ступень", "cheap", "pdca-orchestrator · scout · coder"),
        ("#4f46e5", "средняя ступень", "medium", "planner · check · security-auditor"),
        ("#ea580c", "дорогая ступень", "strong", "escalate"),
    ]
    ly = LEG_Y
    _titles_y = ly - 22
    _legend_w = W - 2 * M
    _tier_w = _legend_w * 0.58
    _tier_iw = _tier_w / 3
    _comp_x = M + _tier_w + 60
    _div_x = M + _tier_w + 30

    def _legend_swatch(x, col, model, roles):
        out = [f'<rect x="{x}" y="{ly-12}" width="15" height="15" rx="4" fill="{col}"/>']
        _mw = len(model) * 7.4 + 16
        if P["tint"]:
            out.append(f'<rect x="{x+22}" y="{ly+8}" width="{_mw}" height="21" rx="7" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.65"/>')
            _mtxt = col
        else:
            out.append(f'<rect x="{x+22}" y="{ly+8}" width="{_mw}" height="21" rx="7" fill="{col}"/>')
            _mtxt = "#ffffff"
        out.append(f'<text x="{x+22+_mw/2}" y="{ly+23}" class="lm" fill="{_mtxt}" text-anchor="middle">{esc(model)}</text>')
        if roles:
            out.append(f'<text x="{x+22+_mw+10}" y="{ly+23}" class="ls">{esc(roles)}</text>')
        return out

    # model tiers: the host model steps cheap / medium / strong
    s.append('<g data-legend="model-tiers">')
    s.append(f'<text x="{M}" y="{_titles_y}" class="lt">Ступени модели</text>')
    for _i, (_col, _t, _model, _roles) in enumerate(legend[:3]):
        _x = M + _i * _tier_iw
        s.append(f'<text x="{_x+22}" y="{ly}" class="lt">{esc(_t)}</text>')
        s.extend(_legend_swatch(_x, _col, _model, _roles))
    s.append('</g>')

    # divider: composition is a different axis, not a fourth model tier
    s.append(f'<line x1="{_div_x}" y1="{ly-26}" x2="{_div_x}" y2="{ly+34}" stroke="{P["sub"]}" stroke-opacity="0.5"/>')

    # composition is a different axis, not a fourth model tier: a dashed
    # outline chip (never a tier badge/swatch) plus the composition wording.
    s.append('<g data-legend="composition">')
    s.append(f'<text x="{_comp_x}" y="{_titles_y}" class="lt">Композиция PDCA</text>')
    s.append(f'<rect x="{_comp_x}" y="{ly-12}" width="15" height="15" rx="4" '
             f'fill="none" stroke="{COMPOSITE_COLOR}" stroke-dasharray="3 2"/>')
    s.append(f'<text x="{_comp_x+22}" y="{ly+3}" class="ls" fill="{P["label"]}">'
             'составной: руки cheap · решения medium · эскалация strong</text>')
    s.append('</g>')

    # ---- state graph (below the legend): nodes and routes from the model ----
    s.append(f'<text x="{M}" y="{SG_TITLE_Y}" class="lt">Граф состояний коллекции</text>')
    neutral = P["state_neutral"]
    for _k, _n in STATE_NODES.items():
        _c = STATE_COLOR[_k] or neutral
        _da = ''
        _tier = f' data-tier="{_n["tier"]}"' if _n.get("tier") else ''
        _comp = ' data-composition="composite"' if _n.get("composite") else ''
        s.append(f'<g data-node="{_k}"{_tier}{_comp}>')
        s.append(f'<rect x="{_n["x"]}" y="{_n["y"]}" width="{NW}" height="{NH}" rx="10" fill="{_c}" fill-opacity="0.08" stroke="{_c}" stroke-width="1.6"{_da}/>')
        if _n.get("owner"):
            # visible owner label on the actual node (e.g. `check · medium`)
            s.append(f'<text x="{_n["x"]+NW/2}" y="{_n["y"]+17}" class="st" fill="{_c}" text-anchor="middle">{esc(_n["label"])}</text>')
            s.append(f'<text x="{_n["x"]+NW/2}" y="{_n["y"]+33}" class="ls" fill="{_c}" text-anchor="middle">{esc(_n["owner"])}</text>')
        else:
            _lines = _n["label"] if isinstance(_n["label"], (list, tuple)) else [_n["label"]]
            if len(_lines) == 1:
                s.append(f'<text x="{_n["x"]+NW/2}" y="{_n["y"]+NH/2+5}" class="st" fill="{_c}" text-anchor="middle">{esc(_lines[0])}</text>')
            else:
                # local two-line support for the long descriptive node name
                _y0 = _n["y"] + 17
                for _i, _line in enumerate(_lines):
                    s.append(f'<text x="{_n["x"]+NW/2}" y="{_y0 + _i*14}" class="st" fill="{_c}" text-anchor="middle">{esc(_line)}</text>')
        s.append('</g>')
        # local note rendered *outside* the `data-node` group: it is not part of
        # the node's name text (tests read the node's exact visible label).
        if _n.get("annotation"):
            _ann = _n["annotation"] if isinstance(_n["annotation"], (list, tuple)) else [_n["annotation"]]
            _ax = _n.get("annotation_x", _n["x"] + NW / 2)
            _aanchor = _n.get("annotation_anchor", "middle")
            s.append(f'<g data-annotation="{_k}">')
            for _ai, _aline in enumerate(_ann):
                s.append(f'<text x="{_ax}" y="{_n["y"]+NH+16 + _ai*13}" class="nt" text-anchor="{_aanchor}">{esc(_aline)}</text>')
            s.append('</g>')
    for _a, _b, _cond in STATE_EDGES:
        _route = ROUTES[(_a, _b)]
        _disp = (
            f' data-dispatched-by="{esc(_route["dispatched_by"])}"'
            if "dispatched_by" in _route
            else ""
        )
        s.append(f'<g data-from="{_a}" data-to="{_b}" data-condition="{esc(_cond)}"{_disp}>')
        s.append(poly(_route["points"]))
        if "label_line" in _route:
            # visible leader tie-in: caption -> its own route (no shared row)
            s.append(poly(_route["label_line"], P["label"], marker=None))
        _caption = _route.get("caption", EDGE_LABELS.get((_a, _b, _cond), _cond))
        if isinstance(_caption, str):
            _caption = [_caption]
        if "label" in _route:
            _lx, _ly = _route["label"]
            _anchor = _route.get("anchor", "middle")
            for _i, _line in enumerate(_caption):
                s.append(label(_lx, _ly + _i * 12, _line, P["label"], _anchor))
        s.append('</g>')
    _notes = [
        # single-group degradation + no rollback of earlier commits
        "Одна группа — деградация: worktree и ветки не создаются, работа в текущем бранче, "
        "merge --no-ff не нужен; сделанные ранее коммиты остаются, автоотката нет · push — никогда",
        # explicit authorized-autocommit prerequisite (the card never grants it)
        "Коммит — только в явно разрешённом режиме автокоммита коллекции; иначе/при запрете — patch сохраняется, "
        "коммитов и цепочки незакоммиченных веток нет (исключение задаётся overlay проекта, не глобально)",
        # merge barrier: terminal = readiness; only successful (done) tips merge
        "≥2: барьер ждёт терминальности ВСЕХ лейнов (done | incomplete) — это готовность, не успех; "
        "MERGE только успешных (done) tip, incomplete пропускается; конфликт → abort → escalate",
        # STOP is not success; ACT cleanup preserves incomplete results;
        # re-gather is a blocked/no-defect state, never a code repair
        "C: re-gather остаётся blocked (нет отчёта) — не дефект, правок кода нет; "
        "STOP корректирующего PDCA ≠ EXIT: unverified, evidence сохранён, без ACT/cleanup; "
        "ACT чистит только DONE/merged, incomplete-результаты (ветки/patch/указатели) сохраняются",
        # lane definition
        "Лейн (work stream) — один параллельный поток работ на группу: отдельный субагент, свой worktree и ветка, "
        "задачи строго по одной, полный pdca-цикл на каждую; параллельно идут группы (≤ cap), не задачи внутри лейна.",
        # flat primary fallback when a nested `Task` is unavailable
        "Fallback: pdca-orchestrator недоступен (нет агента / subagent_depth < 2 / Task запрещён) → "
        "primary ведёт цикл сам · autonomous: Notice: + summary · normal: сообщение пользователю",
    ]
    for _i, _ntext in enumerate(_notes):
        s.append(f'<text x="{M}" y="{NOTE_Y + _i * 16}" class="nt">{esc(_ntext)}</text>')
    s.append('</svg>')
    return "\n".join(s)


def htmlwrap(P, title, svg):
    return ('<!doctype html><html lang="ru"><meta charset="utf-8">'
            f'<title>{esc(title)}</title>'
            f'<style>body{{margin:0;background:{P["bg"]};font-family:Segoe UI,system-ui,sans-serif}}'
            f'.card{{background:{P["card"]};border-radius:12px;margin:20px;padding:12px;box-shadow:{P["shadow"]};overflow:auto}}</style>'
            '<div class="card">' + svg + '</div></html>')


VARIANTS = [
    ("light", "collection-hand", "pdca-collection — ручная раскладка"),
    ("dark", "collection-hand-dark", "pdca-collection — ручная раскладка (тёмная тема)"),
]


def main() -> None:
    """Render both themes next to this script.  Importing makes no file writes."""
    for theme, stem, title in VARIANTS:
        P = THEMES[theme]
        svg = render(P, title)
        svg_out = svg + "\n"
        with open(os.path.join(OUT_DIR, stem + ".svg"), "w", encoding="utf-8") as f:
            f.write(svg_out)
        # embed the exact `.svg` text (including its final newline) so the
        # assets are whitespace-clean and the HTML still embeds the SVG verbatim
        with open(os.path.join(OUT_DIR, stem + ".html"), "w", encoding="utf-8") as f:
            f.write(htmlwrap(P, title, svg_out) + "\n")
        print("wrote %s.{svg,html}" % stem)
    print("W=%d" % W)


if __name__ == "__main__":
    main()
