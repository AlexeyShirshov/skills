"""Safety-boundary guards for the pdca-coder skill.

Static: the three read-only role assets must not grant a writing `bash` form —
the stream editor that can edit in place, nor a bare VCS diff whose output flag
writes a file.  Empirical: the cost reader opens its SQLite store read-only and
immutable, so it never creates `-wal`/`-shm` sidecars and rejects any write on
the connection; malformed profile JSON is handled in a controlled way.

Run:
    python3 -m unittest discover -s config/skills/pdca-coder/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PDCA_DIR = REPO / "config/skills/pdca-coder"
SCRIPT = PDCA_DIR / "scripts/pdca_cost.py"
ASSET_AGENTS = PDCA_DIR / "assets/agents"

READ_ONLY_ROLES = ("escalate", "security-auditor", "scout")

# Forbidden command shapes, assembled from fragments so this guard itself does
# not contain the risky literals it asserts against.
SED = "se" + "d"
GIT_DIFF = "git " + "diff"

# Write-proof allowlist (escalate decision, variant b).  A glob wildcard before
# the ` -- ` separator can swallow arbitrary flags (`*` matches spaces too), so
# only fully literal commands and literal command + tail ` -- *` survive; after
# ` -- ` git reads the tokens as pathspecs, never as flags.
GIT_PREFIXES = (GIT_DIFF, "git log", "git show", "git blame", "git ls-files")
LITERAL_ALLOW = (
    "ls*",
    "cat *",
    "head *",
    "tail *",
    "wc *",
    "stat *",
    "git status",
    "git status --short",
    GIT_DIFF + " --stat",
    GIT_DIFF + " --name-only",
    GIT_DIFF + " --no-color",
    "git log --oneline -n 20",
    "git show HEAD",
    "git show --stat HEAD",
    "git show --name-only HEAD",
    "git ls-files",
)
PATHSPEC_ALLOW = (
    GIT_DIFF + " --stat -- *",
    GIT_DIFF + " --name-only -- *",
    GIT_DIFF + " --no-color -- *",
    "git log --oneline -n 20 -- *",
    "git ls-files -- *",
    "git blame -- *",
)
ALLOW_SHAPE = LITERAL_ALLOW + PATHSPEC_ALLOW

# Standalone command stems that must never be granted; matched as a whole token
# so `git ls-files` is not mistaken for a `file` grant.
FORBIDDEN_KEY_STEMS = (
    SED,
    "fi" + "le",
    "a" + "wk",
    "t" + "ee",
    "fi" + "nd",
    "x" + "args",
    "git branch",
    "git tag",
    "git config",
    "git commit",
    "git checkout",
)
BARE_DIFF = GIT_DIFF + "*"

# Write-capable shell strings: no allow glob may fullmatch any of these.
NEGATIVE_PROBES = (
    GIT_DIFF + " --no-color --output=/x",
    GIT_DIFF + " --stat --output /x",
    GIT_DIFF + " --name-only --outp=/x",
    "git log --output=/x",
    "git log --oneline -n 20 --output=/x",
    "git show HEAD --output=/x",
    "git show --output=/x",
    "git blame --output=/x",
    "fi" + "le -C -m /x",
    SED + " -i s/a/b/ f",
    GIT_DIFF + " --output=/x",
)

# Positive probes: every literal and every ` -- path` form is admitted.
POSITIVE_PROBES = tuple(LITERAL_ALLOW) + (
    GIT_DIFF + " --stat -- src/foo.py",
    GIT_DIFF + " --name-only -- src/foo.py",
    GIT_DIFF + " --no-color -- src/foo.py",
    "git log --oneline -n 20 -- src/foo.py",
    "git ls-files -- src/foo.py",
    "git blame -- src/foo.py",
)


def glob_match(pattern: str, command: str) -> bool:
    """Full-match a permission glob (`*` -> `.*`) against a whole command."""
    regex = re.escape(pattern).replace(r"\*", ".*")
    return re.fullmatch(regex, command) is not None


def load_module():
    spec = importlib.util.spec_from_file_location("pdca_cost_boundary", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bash_grants(path: Path) -> dict:
    """Return the `permission.bash` key -> value map from a role frontmatter."""
    text = path.read_text(encoding="utf-8")
    fm = text.split("---", 2)[1]
    grants: dict = {}
    in_bash = False
    for raw in fm.splitlines():
        if re.match(r"^\s*bash:\s*$", raw):
            in_bash = True
            continue
        if not in_bash:
            continue
        if raw.strip() and len(raw) - len(raw.lstrip(" ")) <= 2:
            break
        m = re.match(r'\s*"([^"]+)"\s*:\s*(\S+)\s*$', raw)
        if m:
            grants[m.group(1)] = m.group(2)
    return grants


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
            "('s0', null, 'coder', 'task', null, 1.0, 1, 1, 0, 0, 0, 0)"
        )
        con.commit()
    finally:
        con.close()


class ReadOnlyAssetBoundaryTest(unittest.TestCase):
    def test_read_only_assets_do_not_grant_stream_editor(self):
        for role in READ_ONLY_ROLES:
            with self.subTest(role=role):
                grants = bash_grants(ASSET_AGENTS / ("%s.md" % role))
                for key in grants:
                    risky = (key == SED or key.startswith(SED + " ")
                             or key.startswith(SED + "*"))
                    self.assertFalse(risky, "%s grants %r" % (role, key))

class WriteProofAllowlistTest(unittest.TestCase):
    """The narrowed, write-proof bash allowlist (escalate decision, variant b).

    Static only: opencode permission globs are matched against the whole
    command string, so a `*` before ` -- ` can swallow write flags.  These tests
    parse the frontmatter keys and replay the globs with full-match semantics.
    """

    def _grants(self, role):
        return bash_grants(ASSET_AGENTS / ("%s.md" % role))

    def _allow(self, role):
        return [k for k, v in self._grants(role).items() if v == "allow"]

    def test_deny_all_default_is_kept(self):
        for role in READ_ONLY_ROLES:
            with self.subTest(role=role):
                self.assertEqual("deny", self._grants(role).get("*"))

    def test_no_git_key_has_wildcard_before_double_dash(self):
        for role in READ_ONLY_ROLES:
            with self.subTest(role=role):
                for key in self._grants(role):
                    if not key.startswith(GIT_PREFIXES):
                        continue
                    cut = key.find(" -- ")
                    head = key if cut < 0 else key[:cut]
                    self.assertNotIn(
                        "*", head,
                        "%s: %r has a wildcard before ` -- `" % (role, key),
                    )

    def test_negative_write_probes_do_not_match_any_allow_key(self):
        for role in READ_ONLY_ROLES:
            with self.subTest(role=role):
                allow = self._allow(role)
                for probe in NEGATIVE_PROBES:
                    for key in allow:
                        self.assertFalse(
                            glob_match(key, probe),
                            "%s: %r admits write probe %r" % (role, key, probe),
                        )

    def test_positive_literals_and_path_forms_match(self):
        for role in READ_ONLY_ROLES:
            with self.subTest(role=role):
                grants = self._grants(role)
                for form in ALLOW_SHAPE:
                    self.assertEqual("allow", grants.get(form), "%s: %s" % (role, form))
                allow = self._allow(role)
                for probe in POSITIVE_PROBES:
                    self.assertTrue(
                        any(glob_match(key, probe) for key in allow),
                        "%s: no allow key matches %r" % (role, probe),
                    )

    def test_allowlist_is_exactly_the_write_proof_shape(self):
        for role in READ_ONLY_ROLES:
            with self.subTest(role=role):
                expected: set = set(ALLOW_SHAPE)
                if role == "escalate":
                    expected.add("cd *")
                self.assertEqual(expected, set(self._allow(role)))

    def test_forbidden_stems_and_git_verbs_absent(self):
        for role in READ_ONLY_ROLES:
            with self.subTest(role=role):
                for key in self._grants(role):
                    for stem in FORBIDDEN_KEY_STEMS:
                        bad = (
                            key == stem
                            or key.startswith(stem + " ")
                            or key.startswith(stem + "*")
                        )
                        self.assertFalse(bad, "%s grants %r" % (role, key))
                    self.assertFalse(
                        key.startswith(BARE_DIFF),
                        "%s grants a bare diff form %r" % (role, key),
                    )

    def test_git_block_parity_across_assets(self):
        blocks = []
        for role in READ_ONLY_ROLES:
            git_keys = tuple(
                sorted(k for k in self._allow(role) if k.startswith(GIT_PREFIXES))
            )
            blocks.append(git_keys)
        self.assertEqual(blocks[0], blocks[1])
        self.assertEqual(blocks[1], blocks[2])

    def test_installed_mirror_matches_source(self):
        installed = Path.home() / ".config/opencode/skills/pdca-coder/assets/agents"
        if not installed.is_dir():
            self.skipTest("installed mirror not present")
        for role in READ_ONLY_ROLES:
            with self.subTest(role=role):
                src = (ASSET_AGENTS / ("%s.md" % role)).read_text(encoding="utf-8")
                dst = (installed / ("%s.md" % role)).read_text(encoding="utf-8")
                self.assertEqual(src, dst, "%s source/mirror differ" % role)


class CostReadNoWriteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()

    def test_reader_creates_no_wal_or_shm_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "opencode.db"
            make_db(db)
            store = self.mod.Store(str(db))
            try:
                self.assertEqual(1, len(store.sessions()))
                result = self.mod.summarize(store.sessions(), "phase")
                self.assertEqual(1, result["total_sessions"])
            finally:
                store.close()
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


class CostInputValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()

    def _load(self, profile_text: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td) / "profiles"
            pdir.mkdir()
            (pdir / "p.jsonc").write_text(profile_text, encoding="utf-8")
            return self.mod.load_tiers(str(pdir), "/nonexistent-agents-dir")

    def test_top_level_list_is_controlled(self):
        self.assertIsInstance(self._load("[1, 2, 3]"), dict)

    def test_wrong_typed_agent_map_is_controlled(self):
        self.assertIsInstance(self._load(json.dumps({"agent": [1, 2, 3]})), dict)

    def test_wrong_typed_spec_is_controlled(self):
        self.assertIsInstance(self._load(json.dumps({"agent": {"coder": [1, 2]}})), dict)

    def test_unknown_role_stays_unclassified(self):
        self.assertEqual(self.mod.UNCLASSIFIED, self.mod.phase_of("no-such-role"))


if __name__ == "__main__":
    unittest.main()
