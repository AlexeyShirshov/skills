"""Run the executable git-model check inside ``unittest discover``.

``git-model-sim.sh`` encodes the git model (``SKILL.md`` §Git model) on throwaway temp
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
LANE_REF = SKILL_DIR / "SKILL.md"

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
