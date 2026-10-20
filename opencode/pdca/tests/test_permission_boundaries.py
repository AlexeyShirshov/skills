"""Permission-boundary guards for the universal `pdca` skill.

Static: the read-only roles must not grant a writing `edit`/`write`/`bash`; the
escalation `bash` allowlist is inspection-only; the runner (`pdca-orchestrator`)
never reaches `general`/`explore`; the executor is the only role with `edit`/`bash`.

Empirical: the cost reader opens its SQLite store read-only and immutable, so it
never mutates the database bytes, never creates `-wal`/`-shm` sidecars and
rejects any write on the connection; a malformed profile is handled without an
unhandled exception.

Run:
    python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts/pdca_cost.py"
RUNNER_ASSET = SKILL_DIR / "assets/agents/pdca-orchestrator.md"

# Host config (agents/profiles/AGENTS.md/skills-keep) lives in the `opencode-config` repo,
# not in this one. Point at it with OPENCODE_CONFIG_REPO to enable host-parity checks;
# they skip by default.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"

HOST_DIR = (CONFIG / "agents") if CONFIG else None

# Forbidden escalation commands: state-changing build/test/run shapes.  Built
# from fragments so this guard itself does not carry the literals it forbids
# where practical (kept readable; the tests dir is not part of the runtime).
FORBIDDEN_COMMAND_STEMS = (
    "build", "make", "test", "run", "pytest", "tox", "npm", "yarn", "pnpm",
    "cargo", "gradle", "mvn", "go", "python", "python3", "bash", "sh", "exec",
    "sudo", "install", "cp", "mv", "rm", "touch", "mkdir", "tee", "dd",
)
INSPECTION_STEMS = frozenset(
    ("cd", "ls", "cat", "sed", "head", "tail", "wc", "stat", "file")
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_block(block: str) -> dict:
    root: dict = {}
    stack: list = [(-1, root)]
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, val = raw.strip().partition(":")
        key = key.strip().strip('"').strip("'")
        val = val.strip().strip('"').strip("'")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if val == "":
            stack[-1][1][key] = {}
            stack.append((indent, stack[-1][1][key]))
        else:
            stack[-1][1][key] = val
    return root


def frontmatter(path: Path) -> dict:
    text = read(path)
    end = text.find("\n---", 3)
    return _parse_block(text[3:end])


def _frontmatter_block(path: Path) -> str:
    text = read(path)
    if not text.startswith("---"):
        raise AssertionError("%s: no frontmatter" % path)
    end = text.find("\n---", 3)
    if end < 0:
        raise AssertionError("%s: unterminated frontmatter" % path)
    return text[3:end]


def permission_rules(path: Path) -> list[dict]:
    """V2 frontmatter `permissions:` — an ordered list of {action, resource, effect}."""
    rules: list[dict] = []
    current: dict | None = None
    in_list = False
    for raw in _frontmatter_block(path).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if indent == 0:
            if stripped == "permission:":
                raise AssertionError(
                    "%s: V1 `permission:` frontmatter — migrate to V2 `permissions:`" % path)
            in_list = stripped == "permissions:"
            current = None
            continue
        if not in_list:
            continue
        if stripped.startswith("- "):
            current = {}
            rules.append(current)
            stripped = stripped[2:]
        if current is None:
            continue
        key, sep, value = stripped.partition(":")
        if not sep:
            raise AssertionError("%s: malformed permission line %r" % (path, raw))
        current[key.strip().strip("\"'")] = value.strip().strip("\"'")
    if not rules:
        raise AssertionError("%s: no V2 `permissions:` rules" % path)
    return rules


BASE_POLICY = (
    {"action": "*", "resource": "*", "effect": "allow"},
    {"action": "read", "resource": "*.env", "effect": "ask"},
    {"action": "read", "resource": "*.env.*", "effect": "ask"},
    {"action": "read", "resource": "*.env.example", "effect": "allow"},
)


def _matches(pattern: str, value: str) -> bool:
    regex = "".join(
        ".*" if ch == "*" else "." if ch == "?" else re.escape(ch) for ch in pattern)
    flags = re.IGNORECASE if os.name == "nt" else 0
    return re.fullmatch(regex, value, flags | re.DOTALL) is not None


def effective(rules: list[dict], action: str, resource: str) -> str:
    """Last matching rule wins; no match falls back to `ask`."""
    effect = "ask"
    for rule in BASE_POLICY + tuple(rules):
        if _matches(rule["action"], action) and _matches(rule["resource"], resource):
            effect = rule["effect"]
    return effect


def allowed_resources(rules: list[dict], action: str) -> set:
    probes = {rule["resource"] for rule in rules if _matches(rule["action"], action)}
    return {res for res in probes if effective(rules, action, res) == "allow"}


def rules_of(role: str) -> list[dict]:
    return permission_rules(HOST_DIR / ("%s.md" % role))


def load_module():
    spec = importlib.util.spec_from_file_location("pdca_cost_boundary", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_db(path: Path) -> None:
    con = sqlite3.connect(str(path))
    try:
        con.execute(
            "create table session (id text primary key, parent_id text, "
            "agent text, title text, model text, cost real, tokens_input integer, "
            "tokens_output integer, tokens_reasoning integer, "
            "tokens_cache_read integer, tokens_cache_write integer, "
            "time_created integer)"
        )
        con.execute(
            "insert into session values "
            "('s0', null, 'pdca-executor', 'task', 'test-model', "
            "1.0, 1, 1, 0, 0, 0, 0)"
        )
        con.commit()
    finally:
        con.close()


class RunnerAssetBoundaryTest(unittest.TestCase):
    """The canonical runner asset keeps the dispatcher-only permissions of every copy."""

    ALLOWLIST = {
        "pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate",
        "pdca-scout", "pdca-security-auditor", "docfx-specialist", "dotnet-*",
    }

    def permission(self) -> dict:
        perm = frontmatter(RUNNER_ASSET).get("permission")
        self.assertIsInstance(perm, dict, "%s: no `permission:` map" % RUNNER_ASSET)
        return perm

    def test_runner_asset_denies_edit_write_and_bash(self):
        perm = self.permission()
        for action in ("edit", "write", "bash"):
            with self.subTest(action=action):
                self.assertEqual("deny", perm.get(action))

    def test_runner_asset_task_is_default_deny_with_the_role_allowlist(self):
        task = self.permission().get("task")
        self.assertIsInstance(task, dict, "runner: no `task` map")
        self.assertEqual("deny", task.get("*"), "runner must deny `task` by default")
        allowed = {name for name, effect in task.items() if effect == "allow"}
        self.assertEqual(self.ALLOWLIST, allowed, "runner role allowlist drifted")

    def test_runner_asset_grants_itself_no_read_write_or_bash_allow(self):
        perm = self.permission()
        for action in ("read", "edit", "write", "bash"):
            with self.subTest(action=action):
                self.assertNotEqual("allow", perm.get(action),
                                    "runner must not grant itself `%s`" % action)

    def test_skill_loading_fallback_belongs_to_an_authorized_role(self):
        paragraphs = [
            p for p in re.split(r"\n\s*\n", read(RUNNER_ASSET))
            if any(k in p.lower() for k in ("fallback", "cannot load", "skill-loading"))
        ]
        self.assertTrue(paragraphs, "runner must describe the skill-loading fallback")
        for paragraph in paragraphs:
            with self.subTest(paragraph=" ".join(paragraph.split())[:60]):
                low = paragraph.lower()
                self.assertTrue("authorized role" in low or "pdca-scout" in low,
                                "fallback must be assigned to an authorized role")


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class ReadOnlyRoleBoundaryTest(unittest.TestCase):
    def test_planner_check_runner_do_not_grant_edit_or_write(self):
        for role in ("pdca-planner", "pdca-check", "pdca-orchestrator"):
            rules = rules_of(role)
            with self.subTest(role=role):
                self.assertNotEqual("allow", effective(rules, "edit", "*"))
                self.assertFalse([r for r in rules if r["action"] == "write"])

    def test_planner_and_check_grant_no_bash(self):
        for role in ("pdca-planner", "pdca-check"):
            rules = rules_of(role)
            with self.subTest(role=role):
                self.assertNotEqual("allow", effective(rules, "shell", "*"))
                self.assertEqual(set(), allowed_resources(rules, "shell"))

    def test_escalate_bash_is_inspection_only(self):
        rules = rules_of("pdca-escalate")
        self.assertEqual("deny", effective(rules, "shell", "*"))
        allowed = allowed_resources(rules, "shell")
        self.assertTrue(allowed)
        for key in allowed:
            stem = key.split()[0].rstrip("*")
            with self.subTest(key=key):
                self.assertIn(stem, INSPECTION_STEMS)
                self.assertNotIn(stem, FORBIDDEN_COMMAND_STEMS)

    def test_runner_subagent_excludes_general_and_explore(self):
        rules = rules_of("pdca-orchestrator")
        self.assertEqual("deny", effective(rules, "subagent", "*"))
        allowed = allowed_resources(rules, "subagent")
        self.assertNotIn("general", allowed)
        self.assertNotIn("explore", allowed)

    def test_executor_grants_edit_and_bash(self):
        rules = rules_of("pdca-executor")
        self.assertEqual("allow", effective(rules, "edit", "*"))
        self.assertEqual("allow", effective(rules, "shell", "*"))


class CostReadNoWriteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()

    def test_reader_does_not_change_db_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "opencode.db"
            make_db(db)
            before = db.read_bytes()
            store = self.mod.Store(str(db))
            try:
                result = self.mod.summarize(store.sessions(), "phase")
                self.assertEqual(1, result["total_sessions"])
            finally:
                store.close()
            self.assertEqual(before, db.read_bytes(), "reader mutated the database")
            self.assertFalse(Path(str(db) + "-wal").exists())
            self.assertFalse(Path(str(db) + "-shm").exists())

    def test_connection_rejects_writes(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "opencode.db"
            make_db(db)
            store = self.mod.Store(str(db))
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    store.con.execute("create table nope (x)")
            finally:
                store.close()


class MalformedProfileInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()

    def _load(self, text: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td) / "profiles"
            pdir.mkdir()
            (pdir / "p.jsonc").write_text(text, encoding="utf-8")
            return self.mod.load_tiers(str(pdir), "/nonexistent-agents-dir")

    def test_malformed_json_is_controlled(self):
        self.assertIsInstance(self._load("{ this is not json"), dict)

    def test_top_level_list_is_controlled(self):
        self.assertIsInstance(self._load("[1, 2, 3]"), dict)

    def test_wrong_typed_agent_map_is_controlled(self):
        self.assertIsInstance(self._load(json.dumps({"agent": [1, 2, 3]})), dict)

    def test_wrong_typed_spec_is_controlled(self):
        self.assertIsInstance(
            self._load(json.dumps({"agent": {"pdca-planner": [1, 2]}})), dict
        )


if __name__ == "__main__":
    unittest.main()
