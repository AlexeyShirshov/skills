"""Replay one CHECK and one actual background shell on four OpenCode configurations."""
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import time

from replay import BRIEF, EVIDENCE, PLUGIN, STATUS, run, wait_for

TOOLS = ["pdca_check_packet_v1", "pdca_record_event_v1", "pdca_wait_v1"]
BASE = {"status":STATUS,"evidence":EVIDENCE}
C = {"N":8,"r":1,"n":1,"step":4,"phase":"DO"}


class Scenario:
    def __init__(self, mode):
        self.mode = mode
        self.fast = mode in ("extended","takeover")

    def response(self, model,last,text):
        if last["role"]=="user" and text.startswith("FIXTURE "):
            op=json.loads(text[8:])
            if "name" in op:
                return op["name"],(op["name"],op["args"]),""
            return "checker",None,"Observed ordered keys; C1 met.\nPDCA-RECORD decision accepted"
        if model=="checker" and last["role"]=="user":
            # Read the real handoff as the independently configured checker role.
            ref=json.loads(text)
            return "read-check",("read",{"path":ref["path"]}),""
        if model=="checker" and last["role"]=="tool":
            assert "<!-- end CHECK handoff -->" in text
            return "verdict",None,"Observed ordered keys; C1 met.\nPDCA-RECORD packet1-verdict accepted"
        return None

    def setup(self,root,config,plugin_dir):
        self.config=config
        config["agents"]["pdca-check"]={"mode":"subagent","model":"local/checker"}
        config["providers"]["local"]["models"]["checker"]=config["providers"]["local"]["models"]["executor"]
        (root/"opencode.json").write_text(json.dumps(config))
        installed=root/".opencode/skills/pdca"
        shutil.copytree(PLUGIN.parents[2]/"skills/pdca",installed)
        def pin(name,content):
            p=root/EVIDENCE/name
            p.write_text(content if isinstance(content,str) else json.dumps(content))
            return {"path":str(p.relative_to(root)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
        recipe={"mode":"candidate","criteria":["C1"],"inputPaths":["result.txt"],"slots":[
            {"id":"test","criterion":"C1","kind":"run"}]}
        self.recipe=pin("recipe.json",recipe)
        self.brief=pin("brief.md","Original task: verify ordered keys. Scope C1; no defects.")
        self.log=pin("run.log","b,a")
        self.manifest=pin("manifest.json",{"mode":"candidate","criteria":["C1"],"candidate":"ordered-keys",
            "brief":self.brief,"inputs":[{"path":"result.txt","sha256":self.log["sha256"]}],
            "required":[{"id":"test","criterion":"C1","ref":self.log}],
            "runs":[{"log":"test","command":"python3 run_fixture.py","exit":0,"candidate":"ordered-keys"}]})
        # Give the manual executor one tool call for the complete write. The
        # harness supplies the source report, but never edits the manual status.
        (root/"manual_phase.py").write_text('''import sys,json,hashlib
from pathlib import Path
src,dst,heading=sys.argv[1:4]
if sys.argv[4:]:
    body=sys.argv[4].encode()
    sha=hashlib.sha256(body).hexdigest()
    path=".pdca/demo/rv1/report-"+sha+".md"
    Path(path).write_bytes(body)
    ref={"path":path,"sha256":sha}
else:
    ref=json.load(sys.stdin)
p=Path(".pdca/status/demo.md"); h,tail=p.read_text().split("### Step 4\\n")
h=h.replace(f"step: 4   Phase: {src}",f"step: 4   Phase: {dst}")
tail=tail.replace(f"Autonomous · {src} open",f"Autonomous · {dst} open").replace(
    "#### "+heading+"\\n","#### "+heading+"\\n"+json.dumps(ref)+"\\n",1)
p.write_text(h+"### Step 4\\n"+tail+f"\\n{src} → {dst} | {json.dumps(ref)}\\n")
print(json.dumps(ref))
''')

    def elect(self,root,owner):
        if self.fast:
            p=root/STATUS
            p.write_text(p.read_text().replace("## Checkpoint\n",
                f"## Checkpoint\nAdapters: packet-v1 events-v1 wait-v1\nAdapter owner: {owner}\n"
                f"Adapter evidence: {EVIDENCE}\nPacket requirements candidate N8/r1: {json.dumps(self.recipe)}\n"))

    def exercise(self,root,api,messages,prompt,owner,parent,requests):
        start=len(requests); t0=time.perf_counter()
        checker=api("session",{"parentID":parent,"agent":"pdca-check","title":"Check fixture"})["id"]
        def call(name,args):
            ids={m["id"] for m in messages(owner)}
            prompt(owner,"FIXTURE "+json.dumps({"name":name,"args":args}))
            def result():
                for m in reversed(messages(owner)):
                    if m["type"]=="assistant" and m["id"] not in ids:
                        for p in m["content"]:
                            if p["type"]=="tool" and p["name"]==name and p["state"]["status"]=="completed":
                                return p["state"]["content"][0]["text"]
                            if p["type"]=="tool" and p["state"]["status"]=="error":
                                raise RuntimeError(str(p["state"])[:600])
                return None
            value=wait_for(result,name)
            wait_for(lambda:messages(owner)[-1]["type"]=="idle",name+" acknowledgement")
            return value
        # Use real OpenCode shell metadata. Completion is never inferred from wall time.
        out=call("shell",{"command":"python3 -c 'import time; time.sleep(0.8); print(37)'","background":True})
        job=re.search(r"\(shell ID: (sh_\w+)\)",out)[1]
        if self.fast:
            call(TOOLS[2],{**BASE,"action":"register","job":job,"next":"Verify original output 37.","expect":C})
        wait_for(lambda:any(m.get("metadata",{}).get("shellID")==job for m in messages(owner)),"native shell result")
        if self.fast:
            checkpoint=wait_for(lambda:re.search(r"^PDCA wait .*?: (.*\"delivery\":\"native\".*)$",
                (root/STATUS).read_text(),re.M),"observed native completion")
            assert json.loads(checkpoint[1])["exit"]==0
        args={**BASE,"key":"packet1","expect":C,"manifest":self.manifest,"checker":checker,"track":self.fast}
        if self.mode=="extended":
            ref=json.loads(call(TOOLS[0],{**args,"action":"send"}))["ref"]
        elif self.fast:
            ref=json.loads(call(TOOLS[0],args))["ref"]
        else:
            shell=call("shell",{"command":f"python3 .opencode/skills/pdca/scripts/check_handoff.py candidate {self.brief['path']} | python3 manual_phase.py DO CHECK 'DO result'"})
            ref=json.loads(shell)
        if self.mode=="takeover":
            self.config["plugins"]=[]
            (root/"opencode.json").write_text(json.dumps(self.config))
            api("location/reload",{})
            def removed():
                return all(p.get("id")!="pdca-handoff" for p in api("plugin"))
            wait_for(removed,"unload adapter before delivery")
            p=root/STATUS;before=p.read_text()
            assert "pdca-op:packet-v1:packet1:" in before and "pdca-delivery:packet1:" not in before
            p.write_text(before.replace("Adapters: packet-v1 events-v1 wait-v1","Adapters: manual"))
            call("shell",{"command":"python3 manual_phase.py DO CHECK 'DO result' <<'REF'\n"+json.dumps(ref)+"\nREF"})
        if self.mode!="extended":
            # Control: driver forwards the existing ref once, without recreating the prepared packet.
            prompt(checker,json.dumps(ref))
        ended=wait_for(lambda:next((m for m in messages(checker) if m.get("finish")=="stop" and
            any(p.get("text","").endswith("packet1-verdict accepted") for p in m["content"])),None),"CHECK verdict")
        assert len([m for m in messages(checker) if m["type"]=="user"])==1
        before_record=len(requests)
        if self.mode=="extended":
            wait_for(lambda:"pdca-op:events-v1:packet1-verdict:" in (root/STATUS).read_text(),"automatic CHECK recording")
        else:
            text=next(p["text"] for p in ended["content"] if p["type"]=="text")
            call("shell",{"command":"python3 manual_phase.py CHECK ACT 'CHECK record' "+shlex.quote(text)})
        final=(root/STATUS).read_text()
        assert "step: 4   Phase: ACT   Cycle: 8   Plan revision: r1   Attempt: 1/3" in final
        assert final.count("### Step 4\n")==1 and (root/"result.txt").read_text()=="b,a"
        verdict=next(p["text"] for p in ended["content"] if p["type"]=="text")
        verdict_sha=hashlib.sha256(verdict.encode()).hexdigest()
        assert verdict_sha in final and (root/EVIDENCE/("report-"+verdict_sha+".md")).read_text()==verdict
        reports=list((root/EVIDENCE).glob("check-*.md"));assert len(reports)==1
        assert "end CHECK handoff" in reports[0].read_text()
        after=sum(m=="executor" for _,m,_ in requests[before_record:])
        assert after==(0 if self.mode=="extended" else 2), (self.mode,after)
        return {"configuration":self.mode,"CHECK_deliveries":1,"phase":"ACT","N_r_n":[8,1,1],
            "after_verdict_executor_requests":after,
            "wall_ms":round((time.perf_counter()-t0)*1000),"provider_requests":len(requests)-start}


if __name__=="__main__":
    with tempfile.TemporaryDirectory(prefix="pdca-legacy-") as tmp:
        # Exercise the released implementation, not the new plugin pretending to be v1.
        legacy=Path(tmp)
        for filename in ("package.json","ledger.py","index.js"):
            (legacy/filename).write_bytes(subprocess.check_output(
                ["git","show","96b5f27:opencode/plugins/pdca-handoff/"+filename],cwd=PLUGIN))
        for mode in ("manual","v1","extended","takeover"):
            result=run(mode!="manual",plugin_dir=legacy if mode=="v1" else PLUGIN,extension=Scenario(mode))
            print(json.dumps(result["compatibility"]),flush=True)
