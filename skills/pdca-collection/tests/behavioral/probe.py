#!/usr/bin/env python3
"""Live behavioral probes for ``pdca-collection`` (opt-in, costs model tokens).

The probes are deliberately not part of the default unittest run: they launch a
real agent session in an isolated opencode sandbox, which is slow, non-
deterministic and billable. What they prove that the text-contract tests cannot
is that the *artifacts* land where the contract says they do:

* ``gap``      — a unit whose plan cannot be made stays a gap; the ALL-barrier
                 fails, and no DAG, group, lane, branch or product edit happens;
* ``campaign`` — a campaign unit is prepared (frame + ref) during phase P next
                 to the cycle units, with no baseline/runtime/step plans yet;
* ``lane``     — after the barrier a single group is driven through DO by
                 ``pdca-orchestrator`` (needs ``experimental.subagent_depth>=2``
                 in the sandbox).

Usage::

    python3 probe.py install                # copy the family into the sandbox
    python3 probe.py gap                    # run one probe, print the verdict
    python3 probe.py check <workdir>        # re-check a recorded probe offline

Environment:

    PDCA_SANDBOX_BIN       oc-sandbox wrapper (default: ~/sources/opencode-config-sandbox/bin/oc-sandbox)
    PDCA_BEHAVIORAL_MODEL  model for the session (default: deepseek/deepseek-flash)
    PDCA_BEHAVIORAL_TIMEOUT  seconds per probe (default: 1800)

Requires a sandbox that already has the skills/agents installed (``install``).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checks  # noqa: E402  (sibling module, not a package)

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS = ("pdca", "pdca-coder", "pdca-dotnet", "pdca-collection", "pdca-incremental", "pdca-entry")
AGENT_SET = "pdca-coder"  # the collection's base variant (identical base for .NET)
AGENTS = ("pdca-orchestrator", "pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate", "pdca-scout")

SANDBOX_BIN = Path(
    os.environ.get(
        "PDCA_SANDBOX_BIN",
        Path.home() / "sources/opencode-config-sandbox/bin/oc-sandbox",
    )
)
SANDBOX_CONFIG = SANDBOX_BIN.parent.parent / "config/opencode"
MODEL = os.environ.get("PDCA_BEHAVIORAL_MODEL", "deepseek/deepseek-flash")
TIMEOUT = int(os.environ.get("PDCA_BEHAVIORAL_TIMEOUT", "1800"))

ENV_DROP = ("OPENCODE_CONFIG", "OPENCODE_SESSION_ID")

GAP_PROMPT = """Follow the skill pdca-collection exactly (load it with the skill tool). This repo is the workspace.

Input — a collection of three tasks (do not change, add or reorder tasks):
1) T1 — add mul(a, b) to calc.py with a doctest.
2) T2 — make the report faster. The acceptance metric, the measurement recipe and the target must be chosen by me (the user). I have not chosen them, and you may not invent or assume them.
3) T3 — add README.md describing the project.

The user is unavailable in this run: do not ask questions and do not wait for approval. Execute the collection's P phase exactly as the contract requires, persist everything it requires (including the collection status file under .pdca/status/), and stop exactly where the contract says to stop. Do not write product code in this run."""

CAMPAIGN_PROMPT = """Follow the skill pdca-collection exactly (load it with the skill tool). This repo is the workspace.

Input — a collection of two units (do not change, add or reorder units):
1) U1 — campaign: reduce the p95 latency of `python3 bench.py` (recipe: p95 over 20 runs, same host, single-threaded) from its measured baseline to target p95 <= 40 ms, floor p95 <= 60 ms. The path is unknown: which of report() / row normalization / caching / data layout gives the gain is only visible after each measurement, and each next step must be chosen from the previous measurement. Surface: app.py and bench.py only.
2) U2 — add README.md describing the project.

The user is unavailable in this run: do not ask questions and do not wait for approval. No autocommit/merge right is granted for this run. Execute the collection's P phase exactly as the contract requires, persist everything it requires (including the collection status file under .pdca/status/ and U1's preparation document), and stop exactly where the contract says to stop. Do not write product code and do not run the baseline measurement in this run."""

LANE_PROMPT = """Follow the skill pdca-collection exactly (load it with the skill tool). This repo is the workspace.

Input — a collection of one task: T1 — add mul(a, b) to calc.py with a doctest.

Run in autonomous mode: no plan approval is expected from the user in this mode. One group means no worktree, no group/task branches and no merge are needed; commit only the files of the task. Drive the collection through its phases and stop where the contract says to stop."""


# --------------------------------------------------------------------------- #
# Sandbox
# --------------------------------------------------------------------------- #

def require_sandbox() -> None:
    if not SANDBOX_BIN.is_file():
        sys.exit(f"sandbox wrapper not found: {SANDBOX_BIN} (set PDCA_SANDBOX_BIN)")
    missing = [name for name in SKILLS if not (SANDBOX_CONFIG / "skills" / name / "SKILL.md").is_file()]
    if missing:
        sys.exit(f"sandbox is missing skills {missing}; run: python3 probe.py install")
    absent = [name for name in AGENTS if not (SANDBOX_CONFIG / "agents" / f"{name}.md").is_file()]
    if absent:
        sys.exit(f"sandbox is missing agents {absent}; run: python3 probe.py install")


def install() -> None:
    if not SANDBOX_BIN.is_file():
        sys.exit(f"sandbox wrapper not found: {SANDBOX_BIN}")
    ignore = shutil.ignore_patterns("tests", "__pycache__", ".pdca")
    for name in SKILLS:
        target = SANDBOX_CONFIG / "skills" / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(REPO_ROOT / "skills" / name, target, ignore=ignore)
        print(f"skill  {name} -> {target}")
    (SANDBOX_CONFIG / "agents").mkdir(parents=True, exist_ok=True)
    for name in AGENTS:
        source = REPO_ROOT / "skills" / AGENT_SET / "assets" / "opencode-agents" / f"{name}.md"
        shutil.copy2(source, SANDBOX_CONFIG / "agents" / f"{name}.md")
        print(f"agent  {name} -> {SANDBOX_CONFIG / 'agents' / (name + '.md')}")


def run_session(workdir: Path, prompt: str) -> int:
    env = {key: value for key, value in os.environ.items() if key not in ENV_DROP}
    command = [str(SANDBOX_BIN), "run", "--model", MODEL, "--agent", "build", prompt]
    print(f"probe  {workdir.name}: {MODEL}, timeout {TIMEOUT}s")
    started = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=workdir / "repo",
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
        output, code = result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "") if isinstance(exc.stdout, str) else ""
        code = 124
    elapsed = time.time() - started
    (workdir / "run.log").write_text(output, encoding="utf-8")
    (workdir / "run.meta").write_text(f"exit={code}\nelapsed={elapsed:.0f}s\nmodel={MODEL}\n", encoding="utf-8")
    print(f"probe  {workdir.name}: exit={code}, {elapsed:.0f}s, log {workdir / 'run.log'}")
    return code


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

def _init_repo(repo: Path, files: dict[str, str]) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (repo / name).write_text(body, encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=False)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=probe@local", "-c", "user.name=probe", "commit", "-qm", "initial"],
        cwd=repo,
        check=True,
    )


def fixture_gap(repo: Path) -> None:
    _init_repo(repo, {"calc.py": 'def add(a, b):\n    """Return the sum of two numbers."""\n    return a + b\n'})


def fixture_campaign(repo: Path) -> None:
    _init_repo(
        repo,
        {
            "app.py": (
                'def report(rows):\n'
                '    """Return rows grouped per row, sorted by score (deliberately naive)."""\n'
                "    out = []\n"
                "    for _ in rows:\n"
                "        out.append(sorted(rows, key=lambda r: r[1]))\n"
                "    return out\n"
            ),
            "bench.py": (
                "import random, time\n"
                "from app import report\n\n"
                "random.seed(7)\n"
                'rows = [(f"id{i}", random.random(), i) for i in range(1500)]\n'
                "samples = []\n"
                "for _ in range(20):\n"
                "    t0 = time.perf_counter()\n"
                "    report(rows)\n"
                "    samples.append((time.perf_counter() - t0) * 1000.0)\n"
                "samples.sort()\n"
                'p95 = samples[int(0.95 * (len(samples) - 1))]\n'
                'print(f"p95_ms={p95:.2f}")\n'
            ),
        },
    )


def fixture_lane(repo: Path) -> None:
    fixture_gap(repo)


PROBES = {
    "gap": (GAP_PROMPT, fixture_gap),
    "campaign": (CAMPAIGN_PROMPT, fixture_campaign),
    "lane": (LANE_PROMPT, fixture_lane),
}


# --------------------------------------------------------------------------- #
# Verdicts
# --------------------------------------------------------------------------- #

def verdict(probe: str, workdir: Path, exit_code: int) -> list[str]:
    repo = workdir / "repo"
    status_path = checks.find_status_file(repo)
    if status_path is None:
        return [f"no collection status file under {repo / '.pdca/status'} (exit={exit_code})"]
    status_text = status_path.read_text(encoding="utf-8")
    before: dict[str, str] | None = None
    meta = workdir / "baseline.sha256"
    if meta.is_file():
        before = {}
        for line in meta.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            before[name] = digest

    if probe == "gap":
        failures = checks.check_gap_probe(status_text, repo=repo, before=before)
    elif probe == "campaign":
        failures = checks.check_campaign_probe(
            status_text,
            checks.read_text(checks.find_preparation(repo)),
            repo=repo,
            before=before,
        )
    else:
        failures = check_lane(status_text, repo, before)

    if exit_code != 0:
        failures.append(f"the session exited with {exit_code} (see {workdir / 'run.log'})")
    return failures


def check_lane(status_text: str, repo: Path, before: dict[str, str]) -> list[str]:
    failures: list[str] = []
    statuses = checks.task_statuses(status_text)
    if not statuses:
        failures.append("no unit statuses recorded in the collection status")
    for unit_id, status in statuses.items():
        if status not in ("done", "merged"):
            failures.append(f"{unit_id} did not reach done/merged (status={status!r})")
    after = checks.tracked_hashes(repo)
    unchanged = sorted(name for name, digest in after.items() if before.get(name) == digest)
    if "calc.py" in unchanged:
        failures.append("calc.py is unchanged: DO never ran")
    if "flat-primary fallback" in status_text.lower() or "fallback used" in status_text.lower():
        failures.append("the status records a flat-primary fallback: pdca-orchestrator was not driven")
    return failures


def write_baseline(workdir: Path) -> None:
    repo = workdir / "repo"
    lines = [f"{digest}  {name}" for name, digest in checks.tracked_hashes(repo).items()]
    (workdir / "baseline.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_probe(probe: str, workdir: Path | None) -> int:
    require_sandbox()
    prompt, build = PROBES[probe]
    workdir = (workdir or Path.home() / "pdca-behavioral" / f"{probe}-{time.strftime('%Y%m%d-%H%M%S')}").resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    repo = workdir / "repo"
    if repo.exists():
        shutil.rmtree(repo)
    build(repo)
    write_baseline(workdir)
    code = run_session(workdir, prompt)
    failures = verdict(probe, workdir, code)
    checks.dump_result(workdir / "result.json", {"probe": probe, "exit": code, "failures": failures})
    if failures:
        print("FAIL " + probe)
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"PASS {probe} — artifacts in {workdir}")
    return 0


def check_only(workdir: Path) -> int:
    workdir = workdir.resolve()
    recorded = workdir / "result.json"
    probe = None
    if recorded.is_file():
        probe = json.loads(recorded.read_text(encoding="utf-8")).get("probe")
    if probe not in PROBES:
        probe = next((name for name in PROBES if name in workdir.name), None)
    if probe is None:
        sys.exit(f"cannot tell which probe {workdir} recorded; expected one of {sorted(PROBES)}")
    failures = verdict(probe, workdir, 0)
    for failure in failures:
        print(f"  - {failure}")
    print("PASS" if not failures else "FAIL")
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install", help="copy the pdca family into the sandbox")
    for probe in PROBES:
        runner = sub.add_parser(probe, help=f"run the {probe} probe")
        runner.add_argument("--workdir", type=Path, default=None)
    checker = sub.add_parser("check", help="re-check a recorded probe workdir")
    checker.add_argument("workdir", type=Path)
    args = parser.parse_args()

    if args.command == "install":
        install()
        return 0
    if args.command == "check":
        return check_only(args.workdir)
    return run_probe(args.command, args.workdir)


if __name__ == "__main__":
    sys.exit(main())
