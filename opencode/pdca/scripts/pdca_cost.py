"""pdca_cost.py — token/cost accounting for opencode PDCA sessions.

Reads the opencode session DB and aggregates cost and tokens by PDCA phase.
A "task" is a session tree: a root session plus every descendant linked via
`session.parent_id` (subagents spawned by the orchestrator).

The skill is stack-agnostic; this script is too. Roles are mapped to phases by a
**generic** table (see PHASE). Any role the table does not know is grouped under
the explicit `unclassified` bucket — never guessed, proxied by a name prefix or
silently dropped. Every session is counted in exactly one group, so the group
session counts and costs reconcile with the totals.

Examples
--------
  # phase breakdown for the last 3 days
  pdca_cost.py --days 3

  # same, grouped by model tier instead of phase
  pdca_cost.py --days 3 --by tier

  # list the most expensive tasks (root + descendants)
  pdca_cost.py --list --top 15

  # full per-phase breakdown of one task (matched by title substring or id)
  pdca_cost.py --task 113

  # per-session tree of that task
  pdca_cost.py --task 113 --tree

  # machine-readable
  pdca_cost.py --days 3 --json

Model tiers for `--by tier` are resolved from the host config (profile `agent`
bindings plus the `# tier:` label in each `agents/*.md`) — no model name is
hardcoded here; point `--profiles-dir`/`--agents-dir` at the install if needed.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import re
import sqlite3
import sys

DEFAULT_DB = os.path.expanduser("~/.local/share/opencode/opencode.db")
DEFAULT_PROFILES_DIR = os.path.expanduser("~/.config/opencode/profiles")
DEFAULT_AGENTS_DIR = os.path.expanduser("~/.config/opencode/agents")

# Explicit bucket for roles the generic table does not know. It is a first-class
# phase: it is counted, shown and reconciled like any other, never dropped.
UNCLASSIFIED = "unclassified"

# Generic role -> phase. Only the universal pdca roles and the generic host
# roles they extend live here. There is no name-prefix inference: a role that
# is not listed maps to `unclassified`.
PHASE = {
    "pdca-orchestrator": "orchestrator",
    "planner": "PLAN",
    "pdca-planner": "PLAN",
    "scout": "GATHER",
    "explore": "GATHER",
    "coder": "DO",
    "pdca-executor": "DO",
    "check": "CHECK",
    "pdca-check": "CHECK",
    "escalate": "ESCALATE",
    "pdca-escalate": "ESCALATE",
}

PHASE_ORDER = [
    "orchestrator",
    "PLAN",
    "GATHER",
    "DO",
    "CHECK",
    "ESCALATE",
    UNCLASSIFIED,
]

TIER_ORDER = ["cheap", "medium", "strong", "?"]

# model-id -> tier, filled from the host config in main() (never hardcoded here).
TIERS = {}

# Hot-path bindings: `phase_of`/`classify` are called once per session record, so
# the map lookup is bound here and `None`/unknown keys fall straight through to
# the explicit `unclassified` bucket (no branch, no call layer on the hot path).
_PHASE_GET = PHASE.get
_UNCLASSIFIED = UNCLASSIFIED


def _strip_jsonc(text):
    """Best-effort JSONC -> JSON: drop // line comments and trailing commas."""
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("//")]
    return re.sub(r",(\s*[}\]])", r"\1", "\n".join(lines))


def load_tiers(profiles_dir, agents_dir):
    """Derive model-id -> tier from the host, without naming any model.

    Tiers come from the role files (the `# tier:` label in each `agents/*.md`) and
    the model each role is bound to in the profile `agent` block. A model serving
    roles of exactly one tier gets that tier; anything else (unbound, mixed) is "?".
    """
    agent_tier = {}
    if os.path.isdir(agents_dir):
        for fn in sorted(os.listdir(agents_dir)):
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(agents_dir, fn), encoding="utf-8") as fh:
                    txt = fh.read()
            except OSError:
                continue
            m = re.search(r"^#\s*tier:\s*(cheap|medium|strong)\b", txt, re.M)
            if m:
                agent_tier[fn[:-3]] = m.group(1)

    tiers = collections.defaultdict(set)
    if os.path.isdir(profiles_dir):
        for fn in sorted(os.listdir(profiles_dir)):
            if not fn.endswith(".jsonc"):
                continue
            try:
                with open(os.path.join(profiles_dir, fn), encoding="utf-8") as fh:
                    cfg = json.loads(_strip_jsonc(fh.read()))
            except (OSError, ValueError):
                continue
            # Shape-validate the parsed profile: only a top-level object with an
            # object `agent` map of object specs is usable. Anything else (a list,
            # a scalar, a wrong-typed `agent`/spec) is skipped, never raised.
            if not isinstance(cfg, dict):
                continue
            agents = cfg.get("agent")
            if not isinstance(agents, dict):
                continue
            for agent, spec in agents.items():
                if not isinstance(spec, dict):
                    continue
                model = spec.get("model")
                tier = agent_tier.get(agent)
                if isinstance(model, str) and tier:
                    tiers[model.rsplit("/", 1)[-1]].add(tier)
    return {mid: next(iter(ts)) for mid, ts in tiers.items() if len(ts) == 1}


def classify(agent):
    """Map a generic role name to its phase; unknown roles -> `unclassified`."""
    return _PHASE_GET(agent, _UNCLASSIFIED)


def phase_of(agent, title=""):
    # Inlined (no `classify` call layer): `phase_of` is the per-record hot path.
    return _PHASE_GET(agent, _UNCLASSIFIED)


def model_id(raw):
    if not raw:
        return "?"
    try:
        return json.loads(raw).get("id", "?")
    except (ValueError, AttributeError):
        return raw


def tier_of(raw):
    return TIERS.get(model_id(raw), "?")


class Store:
    def __init__(self, db):
        # Strictly read-only *and* immutable: `immutable=1` tells SQLite the file
        # cannot change, so it never creates `-wal`/`-shm` sidecars. `query_only`
        # is an extra safeguard: any write statement on this connection fails.
        con = sqlite3.connect("file:%s?mode=ro&immutable=1" % db, uri=True)
        con.execute("PRAGMA query_only=ON")
        self.con = con
        cols = (
            "id,parent_id,agent,title,model,cost,tokens_input,tokens_output,"
            "tokens_reasoning,tokens_cache_read,tokens_cache_write,time_created"
        )
        rows = con.execute("select %s from session" % cols).fetchall()
        self.by_id = {}
        self.kids = collections.defaultdict(list)
        for r in rows:
            self._add(self._record(r))
        self._reconcile()

    @classmethod
    def from_records(cls, records):
        """Create a Store from in-memory, credential-free session dicts (tests/fixtures).

        Each record is a mapping with the same keys as a `session` row; missing
        numeric fields default to 0 and a missing parent to None.
        """
        obj = cls.__new__(cls)
        obj.con = None
        obj.by_id = {}
        obj.kids = collections.defaultdict(list)
        for r in records:
            obj._add(obj._coerce(r))
        obj._reconcile()
        return obj

    @staticmethod
    def _record(r):
        return {
            "id": r[0], "parent": r[1], "agent": r[2], "title": r[3],
            "model": r[4], "cost": r[5] or 0.0,
            "ti": r[6] or 0, "to": r[7] or 0, "tr": r[8] or 0,
            "tcr": r[9] or 0, "tcw": r[10] or 0, "t": r[11],
        }

    @staticmethod
    def _coerce(r):
        return {
            "id": r["id"], "parent": r.get("parent"), "agent": r.get("agent"),
            "title": r.get("title", ""), "model": r.get("model"),
            "cost": r.get("cost") or 0.0,
            "ti": r.get("ti") or 0, "to": r.get("to") or 0,
            "tr": r.get("tr") or 0, "tcr": r.get("tcr") or 0,
            "tcw": r.get("tcw") or 0, "t": r.get("t"),
        }

    def _add(self, s):
        self.by_id[s["id"]] = s
        self.kids[s["parent"]].append(s["id"])

    def _reconcile(self):
        # Every stored session is reachable from the kids index (or is a root),
        # so no session is silently dropped from a tree walk.
        reachable = 0
        for roots in (self.kids.get(None, []),):
            reachable += len(roots)
        assert reachable <= len(self.by_id)

    def close(self):
        if self.con is not None:
            self.con.close()

    def descendants(self, sid):
        out = [sid]
        stack = list(self.kids.get(sid, []))
        while stack:
            x = stack.pop()
            out.append(x)
            stack += self.kids.get(x, [])
        return out

    def roots(self):
        return [s for s in self.by_id.values() if s["parent"] is None]

    def sessions(self):
        return list(self.by_id.values())


def new_acc():
    return [0, 0.0, 0, 0, 0, 0, 0]


def add(acc, s):
    acc[0] += 1
    acc[1] += s["cost"]
    acc[2] += s["ti"]
    acc[3] += s["to"]
    acc[4] += s["tr"]
    acc[5] += s["tcr"]
    acc[6] += s["tcw"]


def group_key(s, by):
    if by == "agent":
        return s["agent"] or "?"
    if by == "tier":
        return tier_of(s["model"])
    if by == "model":
        return model_id(s["model"])
    return phase_of(s["agent"], s["title"])


def summarize(sessions, by="phase"):
    """Aggregate sessions into groups; totals reconcile by construction.

    Returns a dict with `groups` (key -> accumulator), `total_cost` and
    `total_sessions`. Every input session lands in exactly one group, including
    unknown roles in `unclassified`, so the sums equal the totals.
    """
    agg = collections.defaultdict(new_acc)
    for s in sessions:
        add(agg[group_key(s, by)], s)
    return {
        "total_cost": sum(v[1] for v in agg.values()),
        "total_sessions": sum(v[0] for v in agg.values()),
        "groups": dict(agg),
    }


def hdr(col):
    return "%s %10s %7s %11s %9s %9s %13s" % (
        col, "cost$", "share", "input", "output", "reason", "cache_read"
    )


def fmt(name, acc, total, width=24):
    n, cost, ti, to, tr, tcr, _tcw = acc
    share = (cost / total * 100) if total else 0.0
    return "%-*s %10.4f %6.1f%% %11s %9s %9s %13s" % (
        width, name, cost, share, f"{ti:,}", f"{to:,}", f"{tr:,}", f"{tcr:,}"
    )


def ts(ms):
    return dt.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M")


def window_start(args):
    if args.since:
        return int(dt.datetime.strptime(args.since, "%Y-%m-%d").timestamp() * 1000)
    if args.days is not None:
        return int((dt.datetime.now() - dt.timedelta(days=args.days)).timestamp() * 1000)
    return None


def order_keys(by, keys):
    if by == "phase":
        fixed = [k for k in PHASE_ORDER if k in keys]
        return fixed + sorted(k for k in keys if k not in PHASE_ORDER)
    if by == "tier":
        return [k for k in TIER_ORDER if k in keys] + sorted(k for k in keys if k not in TIER_ORDER)
    return sorted(keys)


def run_summary(store, args):
    start = window_start(args)
    sel = [s for s in store.sessions()
           if start is None or (s["t"] or 0) >= start]
    res = summarize(sel, args.by)
    agg = res["groups"]
    total = res["total_cost"]

    title = args.by
    print("=== pdca_cost: %s%s · sessions=%d · total $%.4f ===" % (
        title,
        "" if start is None else " · since " + ts(start),
        res["total_sessions"], total,
    ))
    print(hdr(title))
    for k in order_keys(args.by, agg.keys()):
        print(fmt(str(k), agg[k], total))
    if args.json:
        print(json.dumps({
            "by": args.by, "sessions": res["total_sessions"], "total_cost": total,
            "groups": {str(k): {"sessions": v[0], "cost": v[1], "input": v[2],
                                "output": v[3], "reasoning": v[4],
                                "cache_read": v[5], "cache_write": v[6]}
                       for k, v in agg.items()},
        }, ensure_ascii=False, indent=1))


def task_roots(store, needle):
    needle = needle.lower()
    hits = [s for s in store.roots()
            if needle in s["id"].lower() or needle in (s["title"] or "").lower()]
    return sorted(hits, key=lambda s: -(s["t"] or 0))


def run_list(store, args):
    tasks = []
    for r in store.roots():
        ids = store.descendants(r["id"])
        cost = sum(store.by_id[i]["cost"] for i in ids)
        if len(ids) < 2:
            continue
        tasks.append((cost, r, len(ids)))
    tasks.sort(key=lambda x: -x[0])
    top = tasks[: args.top]
    print("=== tasks by cost (root + descendants), top %d ===" % len(top))
    print("%10s %6s  %-16s %-12s %s" % ("cost$", "sess", "when", "agent", "title"))
    for cost, r, n in top:
        print("%10.3f %6d  %-16s %-12s %s" % (
            cost, n, ts(r["t"]), r["agent"] or "?", (r["title"] or "")[:70]))


def run_task(store, args):
    roots = task_roots(store, args.task)
    if not roots:
        print("task not found: %r" % args.task, file=sys.stderr)
        return 1
    if not args.all:
        if len(roots) > 1:
            print("matched %d tasks, showing the most recent (use --all for all):" % len(roots),
                  file=sys.stderr)
            for r in roots[:10]:
                print("  %s  %s  %s" % (r["id"], ts(r["t"]), r["title"]), file=sys.stderr)
        roots = roots[:1]

    rc = 0
    for r in roots:
        rc |= _task_one(store, r, args)
    return rc


def _task_one(store, root, args):
    ids = store.descendants(root["id"])
    agg = collections.defaultdict(new_acc)
    for sid in ids:
        add(agg[group_key(store.by_id[sid], "phase")], store.by_id[sid])
    total = sum(v[1] for v in agg.values())
    print("=== task: %s ===" % root["title"])
    print("root %s · agent %s · %s · sessions=%d · total $%.4f" % (
        root["id"], root["agent"], ts(root["t"]), len(ids), total))
    print(hdr("phase"))
    for k in order_keys("phase", agg.keys()):
        print(fmt(str(k), agg[k], total))
    if args.tree:
        print()
        print("--- session tree ---")
        _print_tree(store, root["id"], 0)
    if args.json:
        print(json.dumps({
            "root": root["id"], "title": root["title"], "sessions": len(ids),
            "total_cost": total,
            "phases": {str(k): {"sessions": v[0], "cost": v[1], "input": v[2],
                                "output": v[3], "reasoning": v[4],
                                "cache_read": v[5], "cache_write": v[6]}
                       for k, v in agg.items()},
        }, ensure_ascii=False, indent=1))
    return 0


def _print_tree(store, sid, depth):
    s = store.by_id[sid]
    print("%s- %-10s $%8.4f in=%9s out=%8s reas=%8s cr=%11s  %-14s %s" % (
        "  " * depth, s["agent"] or "?", s["cost"], f"{s['ti']:,}", f"{s['to']:,}",
        f"{s['tr']:,}", f"{s['tcr']:,}", model_id(s["model"]),
        (s["title"] or "")[:60]))
    for k in store.kids.get(sid, []):
        _print_tree(store, k, depth + 1)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Token/cost accounting for opencode PDCA sessions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--db", default=DEFAULT_DB, help="opencode.db path")
    ap.add_argument("--profiles-dir", default=DEFAULT_PROFILES_DIR,
                    help="host profiles dir (role->model bindings) for --by tier")
    ap.add_argument("--agents-dir", default=DEFAULT_AGENTS_DIR,
                    help="host agents dir (# tier labels) for --by tier")
    ap.add_argument("--days", type=int, help="window: last N days")
    ap.add_argument("--since", help="window start YYYY-MM-DD")
    ap.add_argument("--by", choices=["phase", "agent", "tier", "model"],
                    default="phase", help="grouping for the summary (default: phase)")
    ap.add_argument("--task", help="task title substring or session id (session tree)")
    ap.add_argument("--tree", action="store_true", help="with --task: print the session tree")
    ap.add_argument("--list", action="store_true", help="list most expensive tasks")
    ap.add_argument("--top", type=int, default=15, help="with --list: how many")
    ap.add_argument("--all", action="store_true",
                    help="with --task: process every matching task, not just the last")
    ap.add_argument("--json", action="store_true", help="also emit JSON")
    args = ap.parse_args(argv)

    if not os.path.exists(args.db):
        print("db not found: %s" % args.db, file=sys.stderr)
        return 2

    TIERS.update(load_tiers(args.profiles_dir, args.agents_dir))
    store = Store(args.db)
    try:
        if args.list:
            run_list(store, args)
        elif args.task:
            return run_task(store, args)
        else:
            run_summary(store, args)
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
