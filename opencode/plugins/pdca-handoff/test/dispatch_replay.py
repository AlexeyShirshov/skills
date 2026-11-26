"""Check managed dispatch on a private OpenCode server with a scripted provider."""
import argparse
import json
import re

from replay import STATUS, run, wait_for


KEY = "N8-r1-n1-recover"
REPORT = "Verified PostgreSQL access. No new test run or attempt."
MARKER = re.compile(r"PDCA-DISPATCH [a-f0-9]{64} complete")


class ManagedDispatch:
    parent_agent = "pdca-orchestrator"

    def __init__(self, native=False):
        self.native = native
        self.source_token = None
        self.native_seen_by_model = False
        self.pointer_seen = False

    def setup(self, root, config, _plugin_dir):
        config["agents"][self.parent_agent] = {"mode": "subagent", "model": "local/parent"}
        (root / "opencode.json").write_text(json.dumps(config))

    def elect(self, _root, owner):
        self.child = owner

    def observe_request(self, request):
        if request["model"] == "parent":
            self.pointer_seen = any(
                m.get("role") == "system" and
                "pdca_dispatch_v1 is available" in str(m.get("content")) and
                "references/driver.md" in str(m.get("content"))
                for m in request["messages"]
            )
            self.native_seen_by_model |= any(
                REPORT in str(m.get("content")) and "<background-result" in str(m.get("content"))
                for m in request["messages"]
            )
            for m in request["messages"]:
                content = str(m.get("content"))
                if "Finished substantive DO." not in content:
                    continue
                token = re.search(r"PDCA-REPORT ([a-f0-9]{16})", content)
                if token:
                    self.source_token = token[1]

    def response(self, model, last, text):
        if model == "parent" and last["role"] == "user" and "Exercise managed dispatch" in text:
            if not self.pointer_seen:
                return "missing-transport-pointer", None, "Missing current transport instructions."
            if not self.source_token:
                return "missing-report-token", None, "Missing the prior report selector."
            if self.native:
                return "native-send", ("subagent", {
                    "agent": "pdca-executor", "sessionID": self.child, "description": "Verify PostgreSQL access",
                    "prompt": f"Verify PostgreSQL access only.\nPDCA-REPORT {self.source_token}",
                }), None
            return "managed-send", ("pdca_dispatch_v1", {
                "action": "send", "key": KEY, "child": self.child, "brief": "Verify PostgreSQL access only.",
                "report": self.source_token,
            }), None
        match = MARKER.search(text)
        if match and model == "executor" and "For this managed turn" in text:
            if f'Verified PDCA report source: {{"session":"{self.child}","message":"msg_' not in text:
                return "missing-bound-report", None, "Missing the verified source."
            return "managed-child", None, REPORT + "\n" + match[0]
        if match and model == "parent" and REPORT in text:
            if "<background-result" in text:
                return "duplicate-native-result", None, "Unexpected native copy."
            if "PDCA dispatch " in text:
                return "managed-delivered", None, "Received the saved report."
        if model == "parent" and last["role"] == "user" and "Inspect the managed dispatch" in text:
            return "managed-inspect", ("pdca_dispatch_v1", {"action": "inspect", "key": self.key}), None
        return None

    def exercise(self, root, api, messages, prompt, owner, parent, requests):
        status = (root / STATUS).read_bytes()
        wait_for(lambda: self.source_token, "prior native report selector offered to the orchestrator")
        prompt(parent, "Exercise managed dispatch.")

        def delivery():
            return [
                m for m in messages(parent)
                if m.get("metadata", {}).get("source") == "pdca-dispatch"
            ]

        notices = wait_for(delivery, "saved report from managed child")
        self.key = re.match(r"PDCA dispatch ([^ ]+) ", notices[0]["text"])[1]
        assert self.key.startswith("native-") if self.native else self.key == KEY
        wait_for(lambda: any(x[0] == "managed-delivered" for x in requests), "driver received managed notice")
        wait_for(lambda: any(
            m.get("metadata", {}).get("source") == "subagent" and REPORT in m.get("text", "")
            for m in messages(parent)
        ), "native report in history")
        # Replay the synthetic admission using the same ID against the real host.
        api(f"session/{parent}/synthetic", {
            **{k: notices[0][k] for k in ("id", "text", "metadata")}, "delivery": "queue",
        })
        prompt(parent, "Inspect the managed dispatch.")
        wait_for(lambda: any(x[0] == "managed-inspect" for x in requests), "inspect dispatch")
        exact = next(m for m in messages(owner) if m["id"] == notices[0]["metadata"]["messageID"])
        text = "\n\n".join(p["text"] for p in exact["content"] if p["type"] == "text")
        assert notices[0]["text"].endswith(text)
        assert notices[0]["metadata"]["childID"] == owner
        assert len(delivery()) == 1
        assert sum(x[0] == "managed-child" for x in requests) == 1
        assert not self.native_seen_by_model
        assert (root / STATUS).read_bytes() == status
        return {"native_launch": self.native, "deliveries": 1, "child_turns": 1, "status_unchanged": True}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--native", action="store_true", help="send through the built-in subagent tool")
    print(json.dumps(run(True, extension=ManagedDispatch(cli.parse_args().native)), indent=2))
