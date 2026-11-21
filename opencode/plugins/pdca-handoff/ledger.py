"""One atomic transaction on the authorized PDCA Markdown file (POSIX)."""
import base64
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

VERSION = "pdca-handoff-v1"
OPT_IN = f"Mechanics: {VERSION}"
PREFIX = "<!-- pdca-handoff-v1 "
SLUG = r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def scoped(name, pattern, *, directory=False):
    require(isinstance(name, str) and re.fullmatch(pattern, name), "invalid PDCA locator")
    path = Path.cwd() / name
    require(path.resolve() == path and not path.is_symlink(), "symlink in PDCA locator")
    require(path.is_dir() if directory else path.is_file(), f"missing {name}")
    return path


def one(text, pattern):
    matches = list(re.finditer(pattern, text, re.M))
    require(len(matches) == 1, "missing or ambiguous status field: " + pattern)
    return matches[0]


def section(text, heading):
    start = one(text, "^" + re.escape(heading) + "$").end()
    end = re.search(r"^## ", text[start:], re.M)
    return start, start + end.start() if end else len(text)


def replace_match(text, match, new):
    return text[:match.start()] + new + text[match.end():]


def coordinate(text, kind):
    if kind == "next-step":
        a, b = section(text, "## Campaign state")
        header = text[a:b]
        one(header, r"^Status: running$")
        one(header, r"^Mode: autonomous$")
        m = one(header, r"^Current step: (\d+) +Phase: ACT +Cycle: (\d+) +Plan revision: r(\d+) +Attempt: (\d+)/3$")
        step, cycle, rev, attempt = map(int, m.groups())
        steps_start, steps_end = section(text, "## Step records")
        steps = re.findall(r"^### Step (\d+)$", text[steps_start:steps_end], re.M)
        require(steps and int(steps[-1]) == step and str(step+1) not in steps, "step index mismatch")
        last = text[steps_start:steps_end].rsplit(f"\n### Step {step}\n", 1)[-1]
        act = one(last, r"^#### ACT record$")
        one(last[act.end():].split("\n#### ",1)[0], r"^Record: completed; outcome: accepted$")
        a, b = section(text, "## Baseline record")
        one(text[a:b], r"^Baseline: accepted$")
        ca, cb = section(text, "## Checkpoint")
        one(text[ca:cb], r"^Disposition: open$")
        one(text[ca:cb], r"^Resume: .+$")
        return dict(step=step+1, N=cycle+1, r=1, n=1)
    require(kind == "plan", "unknown boundary")
    a, b = section(text, "## Current state")
    header = text[a:b]
    one(header, r"^- mode: `autonomous`$")
    one(header, r"^- phase: `PLAN` · record: `open` · outcome: `pending`$")
    m = one(header, r"^- cycle: `N=(\d+)` · revision: `r=(\d+)` · attempt: `n=0`$")
    return dict(N=int(m[1]), r=int(m[2]), n=1)


def save(path, data, *, immutable=False):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        try:
            if path.exists() and not immutable:
                os.fchmod(tmp.fileno(), stat.S_IMODE(path.stat().st_mode))
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
            if immutable:
                try:
                    os.link(tmp.name, path)
                except FileExistsError:
                    require(not path.is_symlink() and path.is_file() and path.read_bytes() == data,
                            "pinned report mismatch")
            else:
                os.replace(tmp.name, path)
            fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp.name)


def step_record(c, ref):
    return f"""### Step {c['step']}

#### Current state
Autonomous · DO open · N={c['N']}, r=1, n=1/3. Goal, scope, criteria: {ref}

#### Original task
See campaign §Original task.

#### PLAN record
##### r1
{ref}

#### Approval record
Not applicable: autonomous mode.

#### DO result
Pending substantive DO.

#### CHECK record
Not run: candidate pending.

#### ACT record
Pending.

#### Lessons learned
Pending retrospective.

#### Revision history
None.

#### Defect history
See campaign defect history; prior history retained.

#### Changed files
None yet.

#### Git state
See campaign checkpoint and frozen plan.

#### Progress log
See shared progress log for Step {c['step']}, N={c['N']}.
"""


def project(text, state, ref, now):
    spec, c = state["spec"], state["counters"]
    require(coordinate(text, spec["boundary"]) == c, "boundary changed")
    if spec["boundary"] == "next-step":
        a, b = section(text, "## Campaign state")
        h = text[a:b]
        h = replace_match(h, one(h, r"^Current step: .+$"),
                          f"Current step: {c['step']}   Phase: DO   Cycle: {c['N']}   Plan revision: r1   Attempt: 1/3")
        text = text[:a] + h + text[b:]
        a, b = section(text, "## Checkpoint")
        ck = text[a:b]
        text = text[:a] + replace_match(ck, one(ck, r"^Resume: .+$"),
                    f"Resume: Step {c['step']}, N={c['N']} r1 n1/3 — execute {ref}.") + text[b:]
        _, b = section(text, "## Step records")
        text = text[:b].rstrip() + "\n\n" + step_record(c, ref) + "\n" + text[b:]
    else:
        a, b = section(text, "## Current state")
        h = text[a:b].replace("· attempt: `n=0`", "· attempt: `n=1`").replace("phase: `PLAN`", "phase: `DO`")
        text = text[:a]+h+text[b:]
        a,b = section(text, "## PLAN record")
        revision = one(text[a:b], rf"^### r{c['r']}$")
        require(text[a+revision.end():b].strip() in ("pending", "not reached: no PLAN yet"),
                "refusing to replace a recorded plan")
        text = text[:a+revision.end()] + f"\n\n{ref}\n\n" + text[b:]
    _, b = section(text, "## Progress log")
    require(b == len(text), "progress log must be last")
    return text.rstrip() + f"\n{now} | DO | revision {c['r']} | attempt 1 | PLAN ready; DO handoff N={c['N']} | {ref}\n"


def checkpoint(text):
    lines = [line for line in text.splitlines() if line.startswith(PREFIX)]
    if not lines:
        return None, None
    require(len(lines) == 1 and lines[0].endswith(" -->"), "ambiguous or invalid handoff checkpoint")
    return lines[0], json.loads(base64.b64decode(lines[0][len(PREFIX):-4], validate=True))


def transact(req):
    path = scoped(req["status"], rf"\.pdca/status/{SLUG}\.md")
    # Lock the stable directory inode, not a status inode replaced by rename.
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        raw = path.read_bytes()
        text = raw.decode()
        if req["op"] == "mechanics":
            from mechanics_ledger import apply
            updated, result = apply(text, req)
            if updated != text:
                save(path, updated.encode())
            return result
        one(text, "^"+OPT_IN+"$")
        line, s = checkpoint(text)
        op = req["op"]
        if op == "inspect":
            return s
        if op == "arm":
            spec = req["spec"]
            a, b = section(text, "## Checkpoint" if spec["boundary"]=="next-step" else "## Current state")
            one(text[a:b], "^"+OPT_IN+"$")
            scoped(spec["evidence"], rf"\.pdca/{SLUG}/rv[1-9]\d*", directory=True)
            if s and s["spec"] == spec and req.get("previous") != s["ticket"]:
                return s
            require(not s or (s["stage"] in ("delivered", "released") and
                              req.get("previous") == s["ticket"]), "checkpoint has another handoff")
            require(not s or s["spec"]["owner"] == spec["owner"], "different executor owns status")
            s = dict(ticket=req["ticket"], stage="armed", spec=spec, counters=coordinate(text,spec["boundary"]),
                     base=digest(text.replace(line+"\n", "").encode() if line else raw))
        else:
            require(s and s["ticket"] == req["ticket"], "stale handoff ticket")
            if op == "outbox":
                require(s["stage"] == "pending" and digest(text.replace(line+"\n", "").encode()) == s["projection"],
                        "committed status changed before delivery")
                sha = s["ref"]["sha256"]
                require(re.fullmatch("[0-9a-f]{64}", sha) and
                        s["ref"]["path"] == f"{s['spec']['evidence']}/report-{sha}.md", "invalid pinned ref")
                artifact = scoped(s["ref"]["path"], rf"\.pdca/{SLUG}/rv[1-9]\d*/report-[0-9a-f]{{64}}\.md")
                require(digest(artifact.read_bytes()) == sha, "pinned report changed before delivery")
                return s
            elif op == "release":
                require(s["stage"] in ("armed","held","released"), "reconcile the committed delivery first")
                s["stage"] = "released"
            elif op == "delivered":
                require(s["stage"] in ("pending","delivered"), "no committed delivery")
                s["stage"] = "delivered"
            elif op == "interrupted":
                if s["stage"] == "armed":
                    s.update(stage="held", reason=req["reason"], message=req["message"])
            elif op in ("ready","hold"):
                if s["stage"] != "armed":
                    return s
                require(digest(text.replace(line+"\n","").encode()) == s["base"], "status changed after arm")
                directory = scoped(s["spec"]["evidence"], rf"\.pdca/{SLUG}/rv[1-9]\d*", directory=True)
                data = req["report"].encode()
                sha = digest(data)
                artifact = directory / f"report-{sha}.md"
                save(artifact, data, immutable=True)
                s.update(ref=dict(path=str(artifact.relative_to(Path.cwd())),sha256=sha), message=req["message"])
                if op == "ready":
                    text = project(text, s, json.dumps(s["ref"]), datetime.datetime.now(datetime.timezone.utc).isoformat())
                    s["deliveryID"] = req["deliveryID"]
                    s["projection"] = digest(text.replace(line+"\n", "").encode())
                    s["stage"] = "pending"
                else:
                    s["stage"] = "held"
            else:
                raise ValueError("unknown transaction")
        new = PREFIX + base64.b64encode(json.dumps(s, separators=(",",":")).encode()).decode() + " -->"
        text = text.replace(line, new, 1) if line else text.replace(OPT_IN+"\n", OPT_IN+"\n"+new+"\n", 1)
        save(path, text.encode())
        return s
    finally:
        os.close(fd)


if __name__ == "__main__":
    # -I excludes cwd and the script directory. Import helpers only from the installed package.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.modules.setdefault("ledger", sys.modules[__name__])
    try:
        print(json.dumps(transact(json.load(sys.stdin))))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        sys.exit(str(exc))
