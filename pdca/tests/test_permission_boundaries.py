"""Permission-boundary guards for the universal `pdca` skill.

Static: the read-only roles must not grant a writing `edit`/`write`/`bash`; the
escalation `bash` allowlist is inspection-only; the runner (`pdca-orchestrator`)
never reaches `general`/`explore`; the executor is the only role with `edit`/`bash`.

Empirical: the cost reader opens its SQLite store read-only and immutable, so it
never mutates the database bytes, never creates `-wal`/`-shm` sidecars and
rejects any write on the connection; a malformed profile is handled without an
unhandled exception.

Run:
    python3 -m unittest discover -s config/skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HOST_DIR = REPO / "config/agents"
SCRIPT = REPO / "config/skills/pdca/scripts/pdca_cost.py"

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


def perm_of(role: str) -> dict:
    return frontmatter(HOST_DIR / ("%s.md" % role))["permission"]


def allow_keys(mapping: dict) -> set:
    return {k for k, v in mapping.items() if v == "allow"}


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
            "('s0', null, 'pdca-executor', 'task', 'deepseek-flash', "
            "1.0, 1, 1, 0, 0, 0, 0)"
        )
        con.commit()
    finally:
        con.close()


class ReadOnlyRoleBoundaryTest(unittest.TestCase):
    def test_planner_check_runner_do_not_grant_edit_or_write(self):
        for role in ("pdca-planner", "pdca-check", "pdca-orchestrator"):
            perm = perm_of(role)
            with self.subTest(role=role):
                self.assertNotEqual("allow", perm.get("edit"))
                self.assertNotEqual("allow", perm.get("write"))

    def test_planner_and_check_grant_no_bash(self):
        for role in ("pdca-planner", "pdca-check"):
            perm = perm_of(role)
            with self.subTest(role=role):
                self.assertNotEqual("allow", perm.get("bash"))
                self.assertNotIn("bash", perm)

    def test_escalate_bash_is_inspection_only(self):
        bash = perm_of("pdca-escalate")["bash"]
        self.assertEqual("deny", bash.get("*"))
        allowed = allow_keys(bash)
        self.assertTrue(allowed)
        for key in allowed:
            stem = key.split()[0].rstrip("*")
            with self.subTest(key=key):
                self.assertIn(stem, INSPECTION_STEMS)
                self.assertNotIn(stem, FORBIDDEN_COMMAND_STEMS)

    def test_runner_task_excludes_general_and_explore(self):
        task = perm_of("pdca-orchestrator")["task"]
        self.assertEqual("deny", task.get("*"))
        allowed = allow_keys(task)
        self.assertNotIn("general", allowed)
        self.assertNotIn("explore", allowed)

    def test_executor_grants_edit_and_bash(self):
        perm = perm_of("pdca-executor")
        self.assertEqual("allow", perm.get("edit"))
        self.assertEqual("allow", perm.get("bash"))


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
