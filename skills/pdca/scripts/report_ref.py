"""Pin a completed report once and pass its verified {path, sha256} reference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def scoped(path):
    root = Path.cwd() / ".pdca"
    path = Path(path).resolve()
    if root.is_symlink() or not path.is_relative_to(root):
        raise ValueError("expected a path under workspace .pdca/")
    return path


def verify(path, digest):
    path = scoped(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"SHA-256 mismatch: {path}")
    return {"path": str(path.relative_to(Path.cwd())), "sha256": digest}


def pin(directory, data, prefix="report"):
    if not data.strip():
        raise ValueError("empty report")
    directory = scoped(directory)
    directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()
    path = directory / f"{prefix}-{digest}.md"
    with tempfile.NamedTemporaryFile(dir=directory) as f:
        f.write(data)
        f.flush()
        try:
            os.link(f.name, path)
        except FileExistsError:
            pass
    return verify(path, digest)


def opencode_report(session, message=None):
    import subprocess

    # Read only the explicitly dispatched session; never persist or print its transcript.
    raw = subprocess.check_output(["opencode", "session", "export", session])
    export = json.loads(raw)
    if export["info"]["id"] != session or Path(export["info"]["location"]["directory"]).resolve() != Path.cwd():
        raise ValueError("unexpected session or workspace")
    messages = export["messages"]
    if message:
        m, = (m for m in messages if m["id"] == message)
    else:
        if messages[-1].get("outcome") != "succeeded" or messages[-1]["type"] != "idle":
            raise ValueError("no completed turn; supply exact source message id")
        m = messages[-2]
    if m["type"] != "assistant" or m.get("finish") != "stop":
        raise ValueError("not a completed assistant report")
    texts = [p["text"] for p in m["content"] if p["type"] == "text"]
    if len(texts) != 1:
        raise ValueError("expected one unambiguous final report text")
    return texts[0].encode("utf-8")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    modes = cli.add_subparsers(dest="mode", required=True)
    cmd = modes.add_parser("opencode")
    cmd.add_argument("directory")
    cmd.add_argument("session")
    cmd.add_argument("--message")
    cmd = modes.add_parser("file")
    cmd.add_argument("directory")
    cmd.add_argument("source")
    cmd = modes.add_parser("verify")
    cmd.add_argument("path")
    cmd.add_argument("sha256")
    args = cli.parse_args()
    if args.mode == "verify":
        ref = verify(args.path, args.sha256)
    else:
        data = (opencode_report(args.session, args.message) if args.mode == "opencode"
                else scoped(args.source).read_bytes())
        ref = pin(args.directory, data)
    print(json.dumps(ref))


if __name__ == "__main__":
    main()
