"""Install recipe `.gitignore`: recursive `rv<k>` evidence is ignored, the durable status is not.

The recipe in `docs/install.md` §2 (and its Russian twin) is added once in the project that
runs cycles.  The contract default for evidence is `.pdca/<task>/rv<k>/`, and a collection
nests the work deeper — `.pdca/<collection-id>/items/<item-id>/…`, canonical integration
evidence at `.pdca/<collection-id>/rv<k>/` — so a single-level `.pdca/*/rv*/` left nested
evidence unignored (tracked by accident, or blocking a checkout).  Two edges keep the fix
narrow:

* `**` between `.pdca/` and the revision directory also matches **zero** directories, which
  would hide a durable root like `.pdca/rv-tests/status.md`;
* `rv*` also matches a non-numeric id such as `.pdca/collection/rv-policy/status.md`.

So the recipe is `.pdca/*/**/rv[0-9]*/`: a task/collection id must precede a numeric revision
directory.  Only the contract default is ignored — an explicitly chosen other `evidence_root`
is not blanket-ignored — and the durable status files stay visible at every depth:
`.pdca/status/<task>.md`, `.pdca/<collection>/status.md`, `.pdca/<collection>/<item>/status.md`.

Guards:

* the repo `.gitignore` and **both** documented recipes carry the same `.pdca` patterns —
  a recipe that drifts from the repo (or from its translation) is the defect;
* real `git check-ignore` behaviour in a throwaway repository, with the global/system git
  config, excludes and inherited repository-local `GIT_*` variables neutralised so neither a
  developer's configuration nor a git hook's environment can mask the result.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

REPOSITORY_IGNORE = ".gitignore"
RECIPE_DOCS = ("docs/install.md", "docs/ru/install.md")

FLAT_RV = ".pdca/*/rv*/"
ZERO_DEPTH_RV = ".pdca/**/rv*/"
NESTED_RV = ".pdca/*/**/rv[0-9]*/"
SCRIPTS = ".pdca/scripts/"

# The contract-default evidence layout at three depths: flat task, nested collection item,
# and a deeper group directory.  Only `rv<k>` with a numeric `k` is ignored.
IGNORED = (
    ".pdca/task/rv1/result.txt",
    ".pdca/collection/task-1/rv1/result.txt",
    ".pdca/collection/items/item-1/rv2/attempts/fix1.log",
    ".pdca/scripts/pdca_cost.py",
)

# The durable on-disk record: must never be hidden by the recipe.  A zero-depth `rv` name and
# a hyphenated `rv` id are not revision directories, and `.pdca/rv1/` is not a canonical
# layout because the contract puts an id before the revision.
VISIBLE = (
    ".pdca/status/task-1.md",
    ".pdca/collection/status.md",
    ".pdca/collection/task-1/status.md",
    ".pdca/collection/items/item-1/preparation.md",
    ".pdca/rv-tests/status.md",
    ".pdca/collection/rv-policy/status.md",
    ".pdca/rv1/manifest.json",
)

GIT = shutil.which("git")


def read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def fenced_gitignore_blocks(text: str) -> list[str]:
    return re.findall(r"```gitignore\n(.*?)```", text, re.S)


def patterns(block: str) -> list[str]:
    """The effective pattern lines of a fence (comments and blanks dropped)."""
    out: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def pdca_patterns(pattern_lines: list[str]) -> list[str]:
    return [line for line in pattern_lines if line.startswith(".pdca/")]


def recipe_sources() -> dict[str, list[str]]:
    """`.pdca` patterns per source: the repo file and every documented recipe fence."""
    sources = {REPOSITORY_IGNORE: pdca_patterns(patterns(read(REPOSITORY_IGNORE)))}
    for rel in RECIPE_DOCS:
        blocks = fenced_gitignore_blocks(read(rel))
        sources[f"{rel} recipe"] = pdca_patterns(
            [line for block in blocks for line in patterns(block)]
        )
    return sources


def git_env(root: Path) -> dict[str, str]:
    """Environment isolated from the caller's git config and repository-local `GIT_*`."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        {
            "HOME": str(root),
            "XDG_CONFIG_HOME": str(root / ".config"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
        }
    )
    return env


def init_repo(root: Path) -> None:
    result = subprocess.run(
        ["git", "init", "-q"], cwd=root, env=git_env(root), capture_output=True, text=True
    )
    if result.returncode != 0:
        raise AssertionError("git init failed: %s" % result.stderr.strip())


def check_ignored(root: Path, rel: str) -> bool:
    """`git check-ignore` verdict for `rel` inside the throwaway repo at `root`."""
    result = subprocess.run(
        ["git", "check-ignore", "-v", "--", rel],
        cwd=root,
        env=git_env(root),
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise AssertionError(
            "git check-ignore failed for %r (exit %d): %s"
            % (rel, result.returncode, result.stderr.strip())
        )
    return result.returncode == 0


class RecipeTextTest(unittest.TestCase):
    """Text-only guards: these never need `git` on the machine."""

    def test_repo_ignore_uses_the_nested_evidence_glob(self) -> None:
        found = pdca_patterns(patterns(read(REPOSITORY_IGNORE)))
        self.assertIn(NESTED_RV, found)
        self.assertNotIn(FLAT_RV, found, "flat glob leaves nested `rv<k>` evidence unignored")
        self.assertNotIn(ZERO_DEPTH_RV, found, "`**` also hides a durable `.pdca/rv*/` root")
        self.assertIn(SCRIPTS, found)

    def test_recipes_match_the_repository_and_each_other(self) -> None:
        sources = recipe_sources()
        expected = sources[REPOSITORY_IGNORE]
        self.assertEqual([NESTED_RV, SCRIPTS], expected)
        for name, found in sources.items():
            with self.subTest(source=name):
                self.assertEqual(expected, found, "%s drifted from the repo recipe" % name)


@unittest.skipUnless(GIT, "git is required for the check-ignore regression")
class RecipeIgnoreTest(unittest.TestCase):
    """Execution guards: real `git check-ignore` in a throwaway repository."""

    def assert_recipe_behaviour(self, pattern_lines: list[str]) -> None:
        body = "# PDCA: fixture\n" + "\n".join(pattern_lines) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / REPOSITORY_IGNORE).write_text(body, encoding="utf-8")
            init_repo(root)
            for rel in IGNORED:
                with self.subTest(ignored=rel):
                    self.assertTrue(check_ignored(root, rel), "%r is not ignored" % rel)
            for rel in VISIBLE:
                with self.subTest(visible=rel):
                    self.assertFalse(check_ignored(root, rel), "%r is ignored" % rel)

    def test_every_documented_recipe_ignores_nested_evidence_only(self) -> None:
        for name, found in recipe_sources().items():
            with self.subTest(source=name):
                self.assert_recipe_behaviour(found)

    def test_checker_on_known_patterns(self) -> None:
        """Fixtures: the flat and zero-depth globs are the defects, the nested one is the fix."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_repo(root)
            (root / REPOSITORY_IGNORE).write_text(FLAT_RV + "\n", encoding="utf-8")
            self.assertTrue(check_ignored(root, ".pdca/task/rv1/result.txt"))
            self.assertFalse(
                check_ignored(root, ".pdca/collection/task-1/rv1/result.txt")
            )
            (root / REPOSITORY_IGNORE).write_text(ZERO_DEPTH_RV + "\n", encoding="utf-8")
            self.assertTrue(check_ignored(root, ".pdca/collection/task-1/rv1/result.txt"))
            self.assertTrue(check_ignored(root, ".pdca/rv-tests/status.md"))
            self.assertTrue(check_ignored(root, ".pdca/collection/rv-policy/status.md"))
            (root / REPOSITORY_IGNORE).write_text(NESTED_RV + "\n", encoding="utf-8")
            self.assertTrue(check_ignored(root, ".pdca/task/rv1/result.txt"))
            self.assertTrue(check_ignored(root, ".pdca/collection/task-1/rv1/result.txt"))
            self.assertFalse(check_ignored(root, ".pdca/rv-tests/status.md"))
            self.assertFalse(check_ignored(root, ".pdca/collection/rv-policy/status.md"))


if __name__ == "__main__":
    unittest.main()
