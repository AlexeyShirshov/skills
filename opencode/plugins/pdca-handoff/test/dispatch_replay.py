"""Check managed dispatch on a private OpenCode server with a scripted provider."""
import json
import re

from replay import STATUS, run, wait_for


KEY = "N8-r1-n1-recover"
REPORT = "Verified PostgreSQL access. No new test run or attempt."
MARKER = re.compile(r"PDCA-DISPATCH [a-f0-9]{64} complete")


class ManagedDispatch:
    native_seen_by_model = False

    def elect(self, _root, owner):
        self.child = owner

    def observe_request(self, request):
        if request["model"] == "parent":
            self.native_seen_by_model |= any(
                REPORT in str(m.get("content")) and "<background-result" in str(m.get("content"))
                for m in request["messages"]
            )

    def response(self, model, last, text):
        if model == "parent" and last["role"] == "user" and "Exercise managed dispatch" in text:
            return "managed-send", ("pdca_dispatch_v1", {
                "action": "send", "key": KEY, "child": self.child, "brief": "Verify PostgreSQL access only.",
            }), None
        match = MARKER.search(text)
        if match and model == "executor" and "For this managed turn" in text:
            return "managed-child", None, REPORT + "\n" + match[0]
        if match and model == "parent" and REPORT in text:
            if "<background-result" in text:
                return "duplicate-native-result", None, "Unexpected native copy."
            if f"PDCA dispatch {KEY}" in text:
                return "managed-delivered", None, "Received the saved report."
        if model == "parent" and last["role"] == "user" and "Inspect the managed dispatch" in text:
            return "managed-inspect", ("pdca_dispatch_v1", {"action": "inspect", "key": KEY}), None
        return None

    def exercise(self, root, api, messages, prompt, owner, parent, requests):
        status = (root / STATUS).read_bytes()
        prompt(parent, "Exercise managed dispatch.")

        def delivery():
            return [
                m for m in messages(parent)
                if m.get("metadata", {}).get("source") == "pdca-dispatch"
            ]

        notices = wait_for(delivery, "saved report from managed child")
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
        return {"deliveries": 1, "child_turns": 1, "status_unchanged": True}


if __name__ == "__main__":
    print(json.dumps(run(True, extension=ManagedDispatch()), indent=2))
