"""A/B one campaign boundary on an isolated OpenCode server and a local scripted model."""
import argparse
import base64
import contextlib
import hashlib
import json
import os
import statistics
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

PLUGIN = Path(__file__).resolve().parents[1]
PLAN = "Support composite keys in declared order. Run the frozen representative cases."
STATUS = ".pdca/status/demo.md"
EVIDENCE = ".pdca/demo/rv1"
BRIEF = "Execute the selected plan under the existing task and loaded contracts."
INITIAL = """# Campaign
## Campaign state
Status: running
Mode: autonomous
Current step: 3   Phase: ACT   Cycle: 7   Plan revision: r1   Attempt: 1/3
## Original task
Support composite keys.
## Preparation record
Complete.
## Baseline record
Baseline: accepted
## Checkpoint
Mechanics: {mode}
Disposition: open
Resume: planner boundary.
## Step records
### Step 3
#### ACT record
Record: completed; outcome: accepted
## Campaign outcome
Pending.
## Lessons learned
Pending.
## Progress log
Previous row.
"""


def wait_for(f, why, timeout=25):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        value = f()
        if value:
            return value
        time.sleep(.05)
    raise RuntimeError("timeout: " + why)


def run(fast):
    requests, errors = [], []
    planner, ticket = None, None
    provider_done = threading.Event()

    class Model(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            model = d["model"]
            last = d["messages"][-1]
            text = str(last.get("content", ""))
            tool = None
            result = "Acknowledged."
            label = "host/parent"
            if model == "executor" and last["role"] == "tool":
                label = "tool-return"
                result = "Finished substantive DO." if "PRODUCT_OK" in text else "Recorded: " + text
            elif model == "executor" and "Bootstrap" in text:
                label = "bootstrap"
                if fast:
                    label = "arm"
                    tool = ("pdca_handoff_v1", {"action":"arm","status":STATUS,"boundary":"next-step",
                            "evidence":EVIDENCE,"planner":planner,"brief":BRIEF})
            elif model == "planner" and "Select next" in text:
                label = "decision"
                result = PLAN + (f"\nPDCA-HANDOFF {ticket} ready" if fast else "")
            elif model == "executor" and "Manual bookkeeping" in text:
                label = "bookkeeping"
                tool = ("shell", {"command":"python3 manual_record.py"})
            elif model == "executor" and "Perform substantive DO" in text:
                label = "do"
                tool = ("shell", {"command":"python3 run_fixture.py"})
                provider_done.set()
            requests.append((label, model, time.perf_counter()))
            if tool:
                names = [x.get("function",{}).get("name") for x in d.get("tools",[])]
                if tool[0] not in names:
                    errors.append(f"{tool[0]} missing from snapshot: {names}")
                delta = {"tool_calls":[{"index":0,"id":f"call_{len(requests)}","type":"function",
                            "function":{"name":tool[0],"arguments":json.dumps(tool[1])}}]}
            else:
                delta = {"content":result}
            self.send_response(200)
            self.send_header("Content-Type","text/event-stream")
            self.end_headers()
            for value, finish in [({"role":"assistant"},None),(delta,None),
                                  ({}, "tool_calls" if tool else "stop")]:
                frame = {"id":"chatcmpl-test","object":"chat.completion.chunk","model":model,
                         "created":1,"choices":[{"index":0,"delta":value,"finish_reason":finish}]}
                self.wfile.write(("data: "+json.dumps(frame)+"\n\n").encode())
            self.wfile.write(b"data: [DONE]\n\n")

    with tempfile.TemporaryDirectory(prefix="pdca-replay-") as tmp, contextlib.ExitStack() as stack:
        root = Path(tmp)/"project"
        root.mkdir()
        for d in [EVIDENCE, ".pdca/status"]:
            (root/d).mkdir(parents=True)
        (root/STATUS).write_text(INITIAL.format(mode="pdca-handoff-v1" if fast else "manual"))
        # Deterministic manual executor for the control: a single tool call for
        # all bookkeeping, rather than penalizing it with several LLM turns.
        (root/"manual_record.py").write_text(
            "from pathlib import Path\nimport hashlib,json\n"
            f"p=Path({STATUS!r}); data=Path('planner-result').read_bytes(); sha=hashlib.sha256(data).hexdigest(); "
            f"ref=Path({EVIDENCE!r})/('report-'+sha+'.md'); ref.write_bytes(data)\n"
            "s=p.read_text().replace('step: 3   Phase: ACT   Cycle: 7','step: 4   Phase: DO   Cycle: 8'); "
            "pair=json.dumps(dict(path=str(ref),sha256=sha)); "
            "s=s.replace('Resume: planner boundary.','Resume: Step 4, N=8 r1 n1/3 — execute '+pair+'.'); "
            "s=s.replace('## Campaign outcome','\\n'+Path('step-4.md').read_text().rstrip().replace('REPORT_REF',pair)+'\\n\\n## Campaign outcome'); "
            "p.write_text(s+'2026-01-01T00:00:00Z | DO | revision 1 | attempt 1 | PLAN ready; DO handoff N=8 | '+pair+'\\n')\n")
        httpd=ThreadingHTTPServer(("127.0.0.1",0),Model)
        threading.Thread(target=httpd.serve_forever,daemon=True).start()
        stack.callback(httpd.server_close)
        stack.callback(httpd.shutdown)
        models = {n:{"limit":{"context":128000,"output":8000},"capabilities":{"tools":True}}
                  for n in ["planner","executor","parent"]}
        config = {"model":"local/parent","small_model":"local/parent",
                  "providers":{"local":{"package":"@opencode/ai/providers/openai-compatible",
                  "settings":{"baseURL":f"http://127.0.0.1:{httpd.server_port}/v1","apiKey":"fixture"},"models":models}},
                  "agents":{f"pdca-{r}":{"mode":"subagent","model":f"local/{r}"} for r in ["planner","executor"]},
                  "plugins":[str(PLUGIN)] if fast else [],
                  "permissions":[{"action":"*","resource":"*","effect":"allow"}]}
        (root/"opencode.json").write_text(json.dumps(config))
        env = {k:os.environ[k] for k in ("PATH","LANG","TMPDIR") if k in os.environ}
        env.update(HOME=tmp, XDG_CONFIG_HOME=tmp+"/config",XDG_STATE_HOME=tmp+"/state",
                   XDG_CACHE_HOME=tmp+"/cache", XDG_DATA_HOME=tmp+"/data",NO_PROXY="127.0.0.1,localhost")
        with socket.socket() as s:
            s.bind(("127.0.0.1",0));port=s.getsockname()[1]
        (root/"step-4.md").write_bytes((PLUGIN/"test/step-4.md").read_bytes())
        (root/"run_fixture.py").write_text(
            "from pathlib import Path\n"
            "columns=[('a', 2), ('b', 1), ('c', 0)]\n"
            "keys=','.join(k for k,n in sorted(columns,key=lambda col:col[1]) if n)\n"
            "assert keys=='b,a'\nPath('result.txt').write_text(keys)\nprint('PRODUCT_OK')\n")
        with open(Path(tmp)/"server.log","w+") as log:
            proc = subprocess.Popen([shutil.which("opencode"),"serve","--hostname","127.0.0.1","--port",str(port)],
                cwd=root,stdout=log,stderr=log,env=env)
            try:
                auth = ""
                def api(path, body=None):
                    req=Request(f"http://127.0.0.1:{port}/api/{path}",
                        data=json.dumps(body).encode() if body is not None else None,
                        headers={"Content-Type":"application/json","x-opencode-directory":str(root),
                                 "Authorization":auth})
                    with urlopen(req,timeout=15) as resp:
                        return json.load(resp).get("data")
                def alive():
                    nonlocal auth
                    if proc.poll() is not None: raise RuntimeError("private server exited")
                    match=re.search(r"server password (\S+)", (Path(tmp)/"server.log").read_text())
                    if not match: return False
                    for candidate in ["Basic "+base64.b64encode(("opencode:"+match[1]).encode()).decode(),
                                      "Bearer "+match[1]]:
                        auth=candidate
                        try: return api("info") or True
                        except HTTPError as e:
                            if e.code!=401:raise
                        except OSError:return False
                    raise RuntimeError("test server rejected its startup credential")
                wait_for(alive,"private server startup")
                parent=api("session",{"agent":"build","location":{"directory":str(root)},"title":"Driver"})["id"]
                planner=api("session",{"agent":"pdca-planner","parentID":parent,"title":"Plan"})["id"]
                owner=api("session",{"agent":"pdca-executor","parentID":parent,"title":"Work"})["id"]
                def prompt(s,text):
                    return api(f"session/{s}/prompt",{"text":text})
                def messages(s):
                    return api(f"session/{s}/context")
                def final(s):
                    m=messages(s)
                    if len(m)>1 and m[-1]["type"]=="idle" and m[-2]["type"]=="assistant":
                        return "\n".join(p["text"] for p in m[-2]["content"] if p["type"]=="text")
                prompt(owner,"Bootstrap executor.")
                setup=wait_for(lambda:final(owner),"executor bootstrap")
                if fast:
                    match=re.search(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',setup)
                    if not match:raise RuntimeError("arm failed: "+setup)
                    ticket=match[0]
                start=len(requests)
                prompt(planner,"Select next step."+(f"\nPDCA-HANDOFF {ticket}" if fast else ""))
                if not fast:
                    plan=wait_for(lambda:final(planner),"decision")
                    (root/"planner-result").write_text(plan)
                    prompt(owner,"Manual bookkeeping: pin planner-result, open step 4, return its reference.")
                    wait_for(lambda:"PLAN ready;" in (root/STATUS).read_text(),"manual status")
                    wait_for(lambda:(final(owner) or "").startswith("Recorded:"),"bookkeeping acknowledgement")
                    prompt(owner,"Perform substantive DO using the recorded plan.")
                wait_for(provider_done.is_set,"substantive DO")
                wait_for(lambda:final(owner)=="Finished substantive DO.","DO reply")
                status=(root/STATUS).read_text()
                if fast:
                    checkpoint=re.search(r"^<!-- pdca-handoff-v1 (\S+) -->$",status,re.M)
                    saved=json.loads(base64.b64decode(checkpoint[1]))
                    assert saved["stage"]=="delivered"
                    # Exercise this release's real durable inbox deduplication,
                    # independent of the plugin's own acknowledged-state guard.
                    admitted=next(m for m in messages(owner) if m["id"]==saved["deliveryID"])
                    api(f"session/{owner}/prompt",{"id":admitted["id"],"text":admitted["text"],"delivery":"queue"})
                    assert sum(m["id"]==admitted["id"] for m in messages(owner))==1
                assert status.count("### Step 4\n")==1 and "step: 4   Phase: DO   Cycle: 8" in status
                files=list((root/EVIDENCE).glob("report-*.md"))
                assert len(files)==1 and files[0].read_text().splitlines()[0]==PLAN
                assert hashlib.sha256(files[0].read_bytes()).hexdigest() in status
                assert not errors,errors
                ref=json.dumps({"path":str(files[0].relative_to(root)),"sha256":hashlib.sha256(files[0].read_bytes()).hexdigest()})
                logical=status.replace(ref,"REPORT_REF")
                logical=re.sub(r"^<!-- pdca-handoff-v1 \S+ -->\n","",logical,flags=re.M)
                logical=re.sub(r"^Mechanics: .+$","Mechanics: MODE",logical,flags=re.M)
                logical=re.sub(r"^.*? \| DO \| revision 1 \| attempt 1 \| ","TIME | DO | revision 1 | attempt 1 | ",logical,flags=re.M)
                lane=[x for x in requests[start:] if x[1]!="parent"]
                i=next(i for i,x in enumerate(lane) if x[0]=="decision")
                j=next(i for i,x in enumerate(lane) if x[0]=="do")
                return {"mode":"plugin" if fast else "manual",
                        "calls_before_decision":[x[0] for x in requests[:start] if x[1]!="parent"],
                        "decision_to_DO":[x[0] for x in lane[i:j+1]],"intermediate_calls":j-i-1,
                        "interval_ms":round(1000*(lane[j][2]-lane[i][2])),
                        "status_sha256_normalized":hashlib.sha256(logical.encode()).hexdigest(),
                        "product":(root/"result.txt").read_text(),
                        "host_parent_requests_observed":sum(x[1]=="parent" for x in requests)}
            except Exception:
                log.flush();log.seek(0)
                print("Last private server output:",re.sub(r"server password \S+","[private server]",log.read())[-3500:],
                      "fixture requests:",requests[-12:],"errors:",errors)
                raise
            finally:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--runs",type=int,default=1)
    count=cli.parse_args().runs
    if count<1:cli.error("runs must be positive")
    results=[]
    for _ in range(count):
        pair=[run(False),run(True)]
        assert [r["intermediate_calls"] for r in pair]==[2,0]
        assert pair[0]["status_sha256_normalized"]==pair[1]["status_sha256_normalized"]
        assert pair[0]["product"]==pair[1]["product"]=="b,a"
        results.extend(pair)
    print(json.dumps({"runs":results,"median_interval_ms":{
        mode:statistics.median(r["interval_ms"] for r in results if r["mode"]==mode)
        for mode in ("manual","plugin")}},indent=2))
