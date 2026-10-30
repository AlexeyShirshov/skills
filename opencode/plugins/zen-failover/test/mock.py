#!/usr/bin/env python3
"""Mock providers for the zen-failover test.

Port 18081 (mockgo): every chat completion returns HTTP 429 with a transient
rate-limit wording (a plan with quota left can answer like this).
Port 18083 (mockai): HTTP 429 with an exhausted-quota wording — or the
transient wording when the prompt contains "transient" (scenario 5).
Port 18082 (mockds): streams a minimal OpenAI-compatible completion.

Every request is appended to $MOCK_LOG (JSON lines).
"""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG = os.environ.get("MOCK_LOG", "/tmp/opencode/zen-failover-test/mock.jsonl")
lock = threading.Lock()


def record(port, path, body):
    entry = {
        "ts": time.time(),
        "port": port,
        "path": path,
        "model": body.get("model"),
        "stream": body.get("stream"),
        "messages": len(body.get("messages") or []),
        "last": ((body.get("messages") or [{}])[-1].get("content") or "")[:120]
        if body.get("messages")
        else "",
    }
    with lock, open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def chunk(payload):
    return f"data: {json.dumps(payload)}\n\n".encode()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def flipped(self):
        """18083 answers successfully once $MOCK_FLIP exists (plan restored)."""
        flip = os.environ.get("MOCK_FLIP")
        return bool(flip and os.path.exists(flip))

    def _send(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.endswith("/models"):
            self._send(200, {"object": "list", "data": [{"id": "deepseek-flash", "object": "model"}]})
            return
        self._send(404, {"error": {"message": "not found"}})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except Exception:
            body = {}
        port = self.server.server_address[1]
        record(port, self.path, body)
        free = str(body.get("model") or "").endswith("-free")

        if (port == 18081 and not free) or (port == 18083 and not self.flipped()):
            messages = [m for m in (body.get("messages") or []) if isinstance(m, dict)]
            transient = any("transient" in str(m.get("content") or "") for m in messages)
            if port == 18083 and not transient:
                payload = {
                    "error": {
                        "message": "You have hit your usage limit for gpt-6.1-sol.",
                        "type": "usage_limit_reached",
                        "code": "usage_limit_reached",
                    }
                }
            else:
                payload = {
                    "error": {
                        "message": "Rate limit reached for requests per min (RPM)",
                        "type": "rate_limit_error",
                        "code": "rate_limit_exceeded",
                    }
                }
            self._send(429, payload)
            return

        answer = "OK-PRIMARY" if port == 18083 else "OK-FALLBACK"
        if port == 18081 and free:
            answer = "OK-FREE"

        if not body.get("stream"):
            self._send(
                200,
                {
                    "id": "chatcmpl-mock",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": body.get("model") or "deepseek-flash",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": answer},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
                },
            )
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        model = body.get("model") or "deepseek-flash"
        base = {
            "id": "chatcmpl-mock",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
        }
        self.wfile.write(chunk({**base, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]}))
        self.wfile.write(chunk({**base, "choices": [{"index": 0, "delta": {"content": answer}, "finish_reason": None}]}))
        self.wfile.write(
            chunk(
                {
                    **base,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
                }
            )
        )
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def serve(port):
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    open(LOG, "w").close()
    threading.Thread(target=serve, args=(18082,), daemon=True).start()
    threading.Thread(target=serve, args=(18083,), daemon=True).start()
    serve(18081)
