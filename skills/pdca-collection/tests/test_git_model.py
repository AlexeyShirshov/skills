"""Run the executable git-model check inside ``unittest discover``.

``git-model-sim.sh`` encodes the git model (``references/lane.md`` §Git model) on throwaway temp
repositories (branch chain, fast-forwarded group branch, ``merge --no-ff`` of
completed groups, conflict detection, single-group isolation, ``incomplete``
group preserved but never merged).  This wrapper only shells out to it, so the
bash check cannot silently rot: the same ``unittest discover`` command that runs
every other skill test runs it too.

Requires ``bash`` and ``git >= 2.28`` (``git init -b``); the test skips when
either is unavailable.  No network, no third-party dependencies.

Run:
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SIM = SKILL_DIR / "tests/git-model-sim.sh"
SKILL = SKILL_DIR / "SKILL.md"
LANE_REF = SKILL_DIR / "references/lane.md"

BASH = shutil.which("bash")
GIT = shutil.which("git")


def _git_supports_init_b() -> bool:
    """``git init -b`` (used by the script) landed in git 2.28."""
    if not GIT:
        return False
    try:
        version = subprocess.run(
            [GIT, "version"], capture_output=True, text=True, timeout=30
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    match = re.search(r"(\d+)\.(\d+)", version)
    return bool(match) and (int(match.group(1)), int(match.group(2))) >= (2, 28)


@unittest.skipUnless(BASH and _git_supports_init_b(), "requires bash and git >= 2.28")
class GitModelSimTest(unittest.TestCase):
    def test_git_model_sim_passes(self):
        self.assertTrue(SIM.is_file(), f"missing git-model script: {SIM}")
        try:
            proc = subprocess.run(
                [BASH, str(SIM)],
                cwd=str(SKILL_DIR),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(f"git-model-sim.sh timed out after {exc.timeout}s")

        output = (
            f"exit={proc.returncode}\n"
            f"--- stdout ---\n{proc.stdout}"
            f"--- stderr ---\n{proc.stderr}"
        )
        self.assertEqual(0, proc.returncode, f"git-model-sim.sh failed\n{output}")
        # Every case prints its own OK line; the final marker proves the whole
        # script ran to completion instead of exiting early after one case.
        self.assertIn("OK: git model verified", proc.stdout, output)


def _statements(text: str) -> list[str]:
    """Paragraphs, further split at bullet/table-row boundaries (one statement each)."""
    out: list[str] = []
    for block in re.split(r"\n\s*\n", text):
        if not block.strip():
            continue
        out.extend(
            part for part in re.split(r"\n(?=\s*(?:[-*|]|\d+\.)\s)", block) if part.strip()
        )
    return out


def _outer_commit_prohibitions(text: str) -> list[str]:
    """Statements that read `Commit policy: none` as a ban on the outer commit.

    Only a *non-negated* ``forbid...`` counts: ``does not forbid`` is the wording the
    contract is expected to use (the policy does not forbid the collection's own
    outer commit). ``not allowed`` is always a prohibition.
    """
    hits: list[str] = []
    for statement in _statements(text):
        if not re.search(r"(?i)Commit policy:\s*`?none", statement):
            continue
        if not re.search(r"(?i)commit", statement):
            continue
        for ban in re.finditer(r"(?i)(forbid\w*|not\s+allowed)", statement):
            before = statement[max(0, ban.start() - 12):ban.start()].lower()
            if re.search(r"(?:\bnot|\bno)\s*$", before):
                continue  # "does not forbid" — the allowed wording
            hits.append(statement)
            break
    return hits


class GitModelContractTextTest(unittest.TestCase):
    """Git model + `Commit policy: none`: not a ban on the collection's outer commit.

    The git model moved from SKILL.md §Git model into ``references/lane.md``; the
    commit-right preflight stayed in §Role/§Parameters. Both files are checked.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = SKILL.read_text(encoding="utf-8") + "\n\n" + LANE_REF.read_text(encoding="utf-8")
        cls.plain = " ".join(cls.raw.replace("**", "").replace("`", "").split())

    def test_commit_policy_none_is_declared(self):
        self.assertIn(
            "Commit policy: none",
            self.raw,
            "the contract/reference lacks the explicit `Commit policy: none` marker",
        )
        windows = [
            self.plain[max(0, m.start() - 300): m.end() + 300]
            for m in re.finditer(r"Commit policy: none", self.plain)
        ]
        self.assertTrue(
            any(re.search(r"(?i)commit", w) and "external" in w for w in windows),
            "the contract must scope `Commit policy: none` to external work "
            f"(stem 'external' near 'commit'): {windows!r}",
        )

    def test_commit_policy_none_does_not_forbid_the_outer_commit(self):
        self.assertIn(
            "preflight",
            self.plain,
            "SKILL.md lacks the git `preflight` step (paired with the "
            "commit-policy scope)",
        )
        self.assertTrue(
            "blocker" in self.plain,
            "SKILL.md must name a `blocker` instead of an outer-commit ban",
        )
        self.assertEqual(
            [],
            _outer_commit_prohibitions(self.raw),
            "`Commit policy: none` must not be presented as forbidding the "
            "collection's outer commit",
        )
