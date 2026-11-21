"""Additional capabilities. Called under the same directory lock as a v1 handoff."""
import datetime
import json
import re

from ledger import checkpoint, digest, one, replace_match, require, section


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def header(text):
    campaign = "\n## Campaign state\n" in text
    a, b = section(text, "## Campaign state" if campaign else "## Current state")
    h = text[a:b]
    if campaign:
        m = one(h, r"^Current step: (\d+) +Phase: (PLAN|DO|CHECK|ACT) +Cycle: (\d+) +Plan revision: r(\d+) +Attempt: (\d+)/3$")
        step, phase, n, r, attempt = m.groups()
        coords = dict(step=int(step), N=int(n), r=int(r), n=int(attempt), phase=phase)
    else:
        phase = one(h, r"^- phase: `(PLAN|DO|CHECK|ACT)` · record: `open` · outcome: `pending`$")[1]
        n, r, attempt = one(h, r"^- cycle: `N=(\d+)` · revision: `r=(\d+)` · attempt: `n=(\d+)`$").groups()
        coords = dict(N=int(n), r=int(r), n=int(attempt), phase=phase)
    return coords, a, b


def election(text, req):
    a, b = section(text, "## Checkpoint" if "\n## Campaign state\n" in text else "## Current state")
    block = text[a:b]
    caps = one(block, r"^Adapters: ([a-z0-9 -]+)$")[1].split()
    require(req["cap"] in caps, "capability not elected; keep the current writer")
    one(block, "^Adapter owner: " + re.escape(req["owner"]) + "$")
    one(block, "^Adapter evidence: " + re.escape(req["evidence"]) + "$")


def local_section(text, coord, name):
    if "step" not in coord:
        return section(text, "## "+name)
    a, b = section(text, "## Step records")
    rec = text[a:b]
    start = one(rec, rf"^### Step {coord['step']}$").end()
    rec = rec[start:]
    require(not re.search(r"^### Step ", rec, re.M), "not the active campaign step")
    h = one(rec, "^#### "+name+"$").end()
    end = re.search(r"^#### ", rec[h:], re.M)
    return a+start+h, a+start+(h+end.start() if end else len(rec))


def log(text, c, summary, pointer, marker):
    _, end = section(text, "## Progress log")
    require(end == len(text), "shared progress log must be last")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return (text.rstrip() + f"\n{now} | {c['phase']} | revision {c['r']} | attempt {c['n']} | "
            f"{summary} | {pointer} {marker}\n")


# The semantic producer owns the decision. Events record or project the common
# uncontested exits. Gates requiring additional evidence/approval use the manual writer.
EVENTS = {
    "plan": ("PLAN", "PLAN record", "PLAN"),
    "revised-plan": ("PLAN", "PLAN record", "PLAN"),
    "contract": ("CHECK", "CHECK record", "PLAN"),
    "do": ("DO", "DO result", "DO"),
    "candidate": ("DO", "DO result", "CHECK"),
    "incomplete": ("DO", "DO result", "ACT"),
    "check": ("CHECK", "CHECK record", "CHECK"),
    "accepted": ("CHECK", "CHECK record", "ACT"),
    "stop": ("CHECK", "CHECK record", "ACT"),
    "act": ("ACT", "ACT record", "ACT"),
    "retrospective": ("ACT", "Lessons learned", "ACT"),
}


def record(text, req, c, a, b):
    k = req["kind"]
    source, name, target = EVENTS[k]
    require(c["phase"] == source, "decision incompatible with status")
    ref = canonical(req["ref"])
    x, y = local_section(text, c, name)
    block = text[x:y]
    if k == "revised-plan":
        level = "#####" if "step" in c else "###"
        require(not re.search(rf"^{level} r{c['r']+1}$", block,re.M), "revision already exists")
        one(block, rf"^{level} r{c['r']}$")
        block = block.rstrip()+f"\n\n{level} r{c['r']+1}\n{ref}\n\n"
    elif k == "plan":
        level = "#####" if "step" in c else "###"
        m = one(block, rf"^{level} r{c['r']}$")
        require(block[m.end():].strip() in ("pending", "not reached: no PLAN yet"), "revision already recorded")
        block = block[:m.end()]+"\n\n"+ref+"\n\n"
    else:
        # Preserve append-only observations; remove the template placeholder when
        # the first actual event fills it, never overwrite previous results.
        if block.strip() in ("Pending.", "pending", "Pending substantive DO.", "Not run: candidate pending.",
                             "Pending retrospective.", "pending: retrospective not yet conducted"):
            block = ""
        block = block.rstrip()+f"\n\n{k}: {ref}\n\n"
    text = text[:x]+block+text[y:]
    if target != source or k == "revised-plan":
        h = text[a:b]
        field = f"Phase: {source} " if "step" in c else f"- phase: `{source}`"
        h = h.replace(field, field.replace(source,target),1)
        if k == "revised-plan":
            oldr, oldn = c["r"], c["n"]
            x,y = local_section(text,c,"Revision history")
            text = text[:y].rstrip()+f"\nr{oldr} attempt {oldn} → r{oldr+1}: {ref}\n\n"+text[y:]
            field = (f"Plan revision: r{oldr}   Attempt: {oldn}/3" if "step" in c else
                     f"revision: `r={oldr}` · attempt: `n={oldn}`")
            new = f"Plan revision: r{oldr+1}   Attempt: 0/3" if "step" in c else f"revision: `r={oldr+1}` · attempt: `n=0`"
            require(field in h, "ambiguous revision counters")
            h = h.replace(field,new,1)
        text = text[:a]+h+text[b:]
        if "step" in c:
            x,y = local_section(text,c,"Current state")
            h = text[x:y]
            m = one(h,rf"^(Autonomous · ){source}( open · N={c['N']}, r={c['r']}, n={c['n']}/3\..*)$")
            tail = m[2] if k!="revised-plan" else m[2].replace(f"r={oldr}, n={oldn}/3",f"r={oldr+1}, n=0/3")
            text = text[:x]+replace_match(h,m,m[1]+target+tail)+text[y:]
        if k == "revised-plan":
            c = dict(c,r=oldr+1,n=0)
    return text, dict(c, phase=target)


def apply(text, q):
    election(text, q)
    _, v1 = checkpoint(text)
    fast = v1 and v1["stage"] in ("armed", "pending", "held")
    op = q["action"]
    if op == "scope":
        return text, {"elected":True}
    if op == "requirements":
        c, _, _ = header(text)
        require(c == q["expect"], "stale packet coordinates")
        a,b = section(text, "## Checkpoint" if "step" in c else "## Current state")
        mode = q["mode"]
        require(mode in ("candidate","retrospective"),"unknown packet mode")
        pattern = rf"^Packet requirements {mode} N{c['N']}/r{c['r']}: (\{{.+\}})$"
        return text,json.loads(one(text[a:b],pattern)[1])
    key = q["key"]
    require(re.fullmatch("[A-Za-z0-9_-]{1,128}",key), "invalid operation key")
    marker = f"<!-- pdca-op:{q['cap']}:{key}:"
    if op in ("receipt","sending","sent"):
        m = re.search(r" \| (\{[^\n]+\}) "+re.escape(marker)+r"([0-9a-f]{64}) -->$",text,re.M)
        if not m:
            require(op=="receipt","packet has not been prepared")
            return text,None
        ref = json.loads(m[1])
        tag = f"<!-- pdca-delivery:{key}:"
        delivery = re.search(re.escape(tag)+r"(\{.+?\}) -->$", text,re.M)
        old = json.loads(delivery[1]) if delivery else None
        if op=="receipt":
            return text,dict(ref=ref,delivery=old)
        require(not fast and q["cap"]=="packet-v1" and q["ref"]==ref,"packet not owned")
        new = q["delivery"]
        if old == new:
            return text,old
        require(old == q.get("previous") and (not old or old["stage"]=="pending"),"conflicting delivery")
        line = tag+canonical(new)+" -->"
        if old:
            return replace_match(text,delivery,line),new
        c,_,_=header(text)
        require(c==q["expect"],"stale dispatch coordinates")
        text = text[:m.end()]+"\n"+line+text[m.end():]
        if new.get("track") and c["phase"]=="DO":
            text,_ = apply(text,{**q,"cap":"events-v1","key":key+"-candidate","action":"commit",
                                 "kind":"candidate","ref":ref})
        return text,new
    if q["cap"] == "wait-v1":
        prefix = f"PDCA wait {key}: "
        a,b = section(text, "## Checkpoint" if "\n## Campaign state\n" in text else "## Current state")
        h = text[a:b]
        matches = list(re.finditer("^"+re.escape(prefix)+"(.+)$",h,re.M))
        require(len(matches)<=1, "ambiguous wait")
        old = json.loads(matches[0][1]) if matches else None
        if op == "inspect":
            return text,old
        require(not fast, "v1 owns this boundary")
        new = q["wait"]
        if old == new:
            return text,old
        require(old == q.get("previous"), "stale wait checkpoint")
        if not old or not new.get("released"):
            require(header(text)[0] == new["expect"], "stale wait coordinates")
        line = prefix+canonical(new)
        h = replace_match(h,matches[0],line) if old else h.rstrip()+"\n"+line+"\n\n"
        return text[:a]+h+text[b:],new

    identity = digest(canonical([q["expect"],q.get("kind"),q["ref"]]).encode())
    if marker in text:
        one(text,re.escape(marker+identity+" -->")+"$")
        return text,{"ref":q["ref"],"duplicate":True}
    require(not fast, "v1 owns this boundary")
    c,a,b = header(text)
    require(c == q["expect"], "stale cycle coordinates")
    if q["cap"] == "events-v1":
        text,c = record(text,q,c,a,b)
    else:
        require(q["cap"]=="packet-v1" and c["phase"] in ("DO","CHECK","ACT"), "not a CHECK handoff")
        _, contract = apply(text,dict(q,action="requirements"))
        require(contract == q["requirements"], "packet requirements changed")
    return log(text,c,q.get("kind","CHECK packet ready"),canonical(q["ref"]),marker+identity+" -->"), {
        "ref":q["ref"],"coordinates":c,"duplicate":False}
