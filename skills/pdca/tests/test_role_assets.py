"""Shared PDCA role assets: one canonical set, real-file compatibility mirrors.

The six shared roles live once in ``skills/pdca/assets/opencode-agents``.  The
coder and .NET overlays keep byte-identical copies (frontmatter, body and
permissions) at their historical paths; collection and incremental keep the
orchestrator only.  ``pdca-security-auditor`` stays a coder/.NET specialist and
is not part of the shared set.

The generator tests run ``sync_role_assets.py`` against a temporary fixture
repository: the default/``--check`` mode is read-only, ``--fix`` writes only the
explicit allowlist, and specialist/unknown files survive untouched.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FAMILY = REPO / "skills"
SCRIPT = FAMILY / "pdca/scripts/sync_role_assets.py"
CANONICAL = FAMILY / "pdca/assets/opencode-agents"

COMMON_ROLES = (
    "pdca-planner",
    "pdca-check",
    "pdca-executor",
    "pdca-scout",
    "pdca-escalate",
    "pdca-orchestrator",
)
# Independent expectation (not imported from the script): which packages must
# carry which shared roles, and that the mirrors are real files.
EXPECTED = {
    "pdca-coder": COMMON_ROLES,
    "pdca-dotnet": COMMON_ROLES,
    "pdca-collection": ("pdca-orchestrator",),
    "pdca-incremental": ("pdca-orchestrator",),
}
MIRROR_DIRS = {skill: FAMILY / skill / "assets/opencode-agents" for skill in EXPECTED}


def run_script(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), *args],
        capture_output=True,
        text=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"},
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def role_text(name: str, extra_body: str = "") -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f'description: "fixture {name}"\n'
        "mode: subagent\n"
        "# tier: medium\n"
        "permission:\n"
        '  "*": deny\n'
        "  read:\n"
        '    ".pdca/**": allow\n'
        "---\n\n"
        f"# {name}\n\n"
        "Fixture body with a permission block and a body line.\n"
        f"{extra_body}"
    )


class SourceParityTest(unittest.TestCase):
    """The checkout itself: complete byte parity for the shared roles."""

    def test_common_roles_are_byte_identical_in_coder_and_dotnet(self) -> None:
        for skill in ("pdca-coder", "pdca-dotnet"):
            for role in COMMON_ROLES:
                with self.subTest(skill=skill, role=role):
                    source = CANONICAL / f"{role}.md"
                    mirror = MIRROR_DIRS[skill] / f"{role}.md"
                    self.assertTrue(source.is_file(), f"canonical {role} missing")
                    self.assertTrue(mirror.is_file(), f"mirror {skill}/{role} missing")
                    self.assertFalse(mirror.is_symlink(), f"{skill}/{role} must be a real file")
                    self.assertEqual(source.read_bytes(), mirror.read_bytes())

    def test_orchestrator_is_byte_identical_in_collection_and_incremental(self) -> None:
        source = CANONICAL / "pdca-orchestrator.md"
        for skill in ("pdca-collection", "pdca-incremental"):
            with self.subTest(skill=skill):
                mirror = MIRROR_DIRS[skill] / "pdca-orchestrator.md"
                self.assertTrue(mirror.is_file())
                self.assertFalse(mirror.is_symlink())
                self.assertEqual(source.read_bytes(), mirror.read_bytes())

    def test_no_extra_shared_roles_leak_into_collection_or_incremental(self) -> None:
        for skill in ("pdca-collection", "pdca-incremental"):
            with self.subTest(skill=skill):
                shipped = sorted(p.stem for p in MIRROR_DIRS[skill].glob("*.md"))
                self.assertEqual(["pdca-orchestrator"], shipped)

    def test_security_auditor_stays_a_specialist_not_a_shared_role(self) -> None:
        self.assertFalse((CANONICAL / "pdca-security-auditor.md").exists())
        for skill in ("pdca-coder", "pdca-dotnet"):
            path = MIRROR_DIRS[skill] / "pdca-security-auditor.md"
            with self.subTest(skill=skill):
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())
                self.assertIn("name: pdca-security-auditor", path.read_text(encoding="utf-8"))

    def test_every_shipped_role_mirror_is_a_real_file(self) -> None:
        for skill, roles in EXPECTED.items():
            for role in roles:
                with self.subTest(skill=skill, role=role):
                    self.assertFalse((MIRROR_DIRS[skill] / f"{role}.md").is_symlink())

    def test_generator_check_passes_on_the_checkout(self) -> None:
        result = run_script(REPO, "--check")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_coding_obligations_stay_in_the_coder_overlay(self) -> None:
        # The shared executor brief is domain-neutral; the coder overlay keeps the
        # code-specific duties instead of losing them when the briefs were unified.
        skill = (FAMILY / "pdca-coder/SKILL.md").read_text(encoding="utf-8")
        for token in ("no TDD ordering", "defect history", "Do not commit or push"):
            with self.subTest(token=token):
                self.assertIn(token, skill)

    def test_phase_references_stay_with_the_base(self) -> None:
        # Overlays no longer ship copies of plan.md/check.md/act.md: those references
        # belong to the base package and are routed by role from there.
        plan = (FAMILY / "pdca/references/plan.md").read_text(encoding="utf-8")
        check = (FAMILY / "pdca/references/check.md").read_text(encoding="utf-8")
        act = (FAMILY / "pdca/references/act.md").read_text(encoding="utf-8")
        self.assertIn("Instructions for **`pdca-planner` only**", plan)
        self.assertIn("Reference for the CHECK phase", check)
        self.assertIn("Reference for the ACT phase", act)
        for skill in ("pdca-coder", "pdca-dotnet"):
            self.assertFalse((FAMILY / skill / "references").exists(),
                             f"{skill} must inherit the base references, not copy them")

    def test_role_assets_point_at_the_phase_reference_owner(self) -> None:
        # An agent is a thin adapter: it names the reference (or the skill load) that owns its
        # procedure instead of carrying a second copy.
        owners = {
            "pdca-planner": "references/plan.md",
            "pdca-check": "references/check.md",
            "pdca-executor": "references/act.md",
            "pdca-escalate": "references/escalate.md",
            "pdca-orchestrator": "skill mechanism by exact ID",
        }
        for role, token in owners.items():
            with self.subTest(role=role):
                self.assertIn(
                    token,
                    (CANONICAL / f"{role}.md").read_text(encoding="utf-8"),
                    f"{role} must name the owner of its contract",
                )

    def test_net_inner_loop_and_helpers_stay_in_the_dotnet_overlay(self) -> None:
        skill = (FAMILY / "pdca-dotnet/SKILL.md").read_text(encoding="utf-8")
        for token in (
            "inner loop",
            "whole-solution",
            "validate_inner_loop.py",
            "pdca_evidence.py",
            "Roslyn-first",
        ):
            with self.subTest(token=token):
                self.assertIn(token, skill)


class GeneratorFixtureTest(unittest.TestCase):
    """Behavior of ``sync_role_assets.py`` in an isolated fixture repository."""

    def make_repo(self) -> tuple[Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name)
        canonical = repo / "skills/pdca/assets/opencode-agents"
        canonical.mkdir(parents=True)
        for role in COMMON_ROLES:
            (canonical / f"{role}.md").write_text(role_text(role), encoding="utf-8")
        for rel in (
            "skills/pdca-coder/assets/opencode-agents",
            "skills/pdca-dotnet/assets/opencode-agents",
            "skills/pdca-collection/assets/opencode-agents",
            "skills/pdca-incremental/assets/opencode-agents",
        ):
            (repo / rel).mkdir(parents=True)
        # Specialist and unrelated files must survive every mode.
        (repo / "skills/pdca-coder/assets/opencode-agents/pdca-security-auditor.md").write_text(
            role_text("pdca-security-auditor"), encoding="utf-8"
        )
        (repo / "skills/pdca-coder/assets/opencode-agents/NOTES.md").write_text(
            "hand-written note\n", encoding="utf-8"
        )
        return repo, canonical

    def mirror(self, repo: Path, skill: str, role: str) -> Path:
        return repo / f"skills/{skill}/assets/opencode-agents/{role}.md"

    def test_check_is_read_only_and_reports_missing_mirrors(self) -> None:
        repo, _ = self.make_repo()
        before = snapshot(repo)
        for args in ((), ("--check",)):
            with self.subTest(args=args):
                result = run_script(repo, *args)
                self.assertEqual(1, result.returncode)
                self.assertIn("missing mirror:", result.stderr)
                self.assertEqual(before, snapshot(repo), "check must not write")
                self.assertFalse(self.mirror(repo, "pdca-coder", "pdca-planner").exists())

    def test_clean_check_passes_and_writes_nothing(self) -> None:
        repo, _ = self.make_repo()
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        before = snapshot(repo)
        result = run_script(repo, "--check")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, snapshot(repo))

    def test_fix_writes_all_and_only_allowlisted_mirrors(self) -> None:
        repo, canonical = self.make_repo()
        before_canonical = snapshot(canonical)
        result = run_script(repo, "--fix")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before_canonical, snapshot(canonical), "canonical files changed")
        for skill, roles in EXPECTED.items():
            for role in roles:
                with self.subTest(skill=skill, role=role):
                    target = self.mirror(repo, skill, role)
                    self.assertTrue(target.is_file())
                    self.assertFalse(target.is_symlink())
                    self.assertEqual(
                        (canonical / f"{role}.md").read_bytes(), target.read_bytes()
                    )
        # Collection/incremental get the orchestrator only.
        for skill in ("pdca-collection", "pdca-incremental"):
            shipped = sorted(p.stem for p in (repo / f"skills/{skill}/assets/opencode-agents").glob("*.md"))
            self.assertEqual(["pdca-orchestrator"], shipped)

    def test_fix_is_idempotent(self) -> None:
        repo, _ = self.make_repo()
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        first = snapshot(repo)
        second = run_script(repo, "--fix")
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(first, snapshot(repo))
        self.assertNotIn("fixed:", second.stdout)

    def test_body_only_drift_is_detected(self) -> None:
        repo, _ = self.make_repo()
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        target = self.mirror(repo, "pdca-dotnet", "pdca-check")
        target.write_text(target.read_text(encoding="utf-8") + "local edit\n", encoding="utf-8")
        result = run_script(repo, "--check")
        self.assertEqual(1, result.returncode)
        self.assertIn("drift:", result.stderr)
        self.assertIn("skills/pdca-dotnet/assets/opencode-agents/pdca-check.md", result.stderr)
        # --fix restores the canonical bytes.
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        self.assertEqual(0, run_script(repo, "--check").returncode)

    def test_permission_only_drift_is_detected(self) -> None:
        repo, _ = self.make_repo()
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        target = self.mirror(repo, "pdca-coder", "pdca-planner")
        text = target.read_text(encoding="utf-8")
        target.write_text(
            text.replace('  "*": deny\n', '  "*": allow\n'), encoding="utf-8"
        )
        result = run_script(repo, "--check")
        self.assertEqual(1, result.returncode)
        self.assertIn("drift:", result.stderr)

    def test_missing_mirror_is_detected_and_repaired(self) -> None:
        repo, _ = self.make_repo()
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        self.mirror(repo, "pdca-incremental", "pdca-orchestrator").unlink()
        result = run_script(repo, "--check")
        self.assertEqual(1, result.returncode)
        self.assertIn("missing mirror:", result.stderr)
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        self.assertEqual(0, run_script(repo, "--check").returncode)

    def test_fix_preserves_specialist_and_unknown_files(self) -> None:
        repo, _ = self.make_repo()
        specialist = repo / "skills/pdca-coder/assets/opencode-agents/pdca-security-auditor.md"
        unknown = repo / "skills/pdca-coder/assets/opencode-agents/NOTES.md"
        original = (specialist.read_bytes(), unknown.read_bytes())
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        self.assertEqual(original, (specialist.read_bytes(), unknown.read_bytes()))

    def test_check_reports_a_symlink_mirror_and_fix_replaces_it(self) -> None:
        repo, _ = self.make_repo()
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        target = self.mirror(repo, "pdca-coder", "pdca-scout")
        target.unlink()
        target.symlink_to(self.mirror(repo, "pdca-coder", "pdca-planner"))
        result = run_script(repo, "--check")
        self.assertEqual(1, result.returncode)
        self.assertIn("symlink mirror:", result.stderr)
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        self.assertFalse(target.is_symlink())
        self.assertEqual(0, run_script(repo, "--check").returncode)

    def other_tree(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_missing_canonical_source_preflights_before_any_write(self) -> None:
        repo, canonical = self.make_repo()
        (canonical / "pdca-check.md").unlink()
        before = snapshot(repo)
        result = run_script(repo, "--fix")
        self.assertEqual(1, result.returncode)
        self.assertIn("missing canonical:", result.stderr)
        self.assertNotIn(str(repo), result.stderr, "diagnostics must be relative")
        self.assertEqual(before, snapshot(repo), "preflight failure must not write any mirror")
        self.assertFalse(self.mirror(repo, "pdca-coder", "pdca-planner").exists())

    def test_symlink_source_file_is_rejected_without_writes(self) -> None:
        repo, canonical = self.make_repo()
        outside = self.other_tree()
        source = outside / "pdca-check.md"
        source.write_text(role_text("pdca-check"), encoding="utf-8")
        (canonical / "pdca-check.md").unlink()
        (canonical / "pdca-check.md").symlink_to(source)
        before = snapshot(repo)
        for args in (("--check",), ("--fix",)):
            with self.subTest(args=args):
                result = run_script(repo, *args)
                self.assertEqual(1, result.returncode)
                self.assertIn("symlink source:", result.stderr)
                self.assertEqual(before, snapshot(repo), "linked source must not be written")
                self.assertFalse(self.mirror(repo, "pdca-coder", "pdca-check").exists())

    def test_symlink_source_ancestor_is_rejected_without_writes(self) -> None:
        repo, canonical = self.make_repo()
        real = repo / "real-canonical"
        canonical.rename(real)
        canonical.symlink_to(real)
        result = run_script(repo, "--check")
        self.assertEqual(1, result.returncode)
        self.assertIn("symlink source: skills/pdca/assets/opencode-agents", result.stderr)
        fix = run_script(repo, "--fix")
        self.assertEqual(1, fix.returncode)
        self.assertFalse(self.mirror(repo, "pdca-coder", "pdca-planner").exists())

    def test_regular_file_in_mirror_path_aborts_before_any_write(self) -> None:
        repo, _ = self.make_repo()
        dotnet_dir = repo / "skills/pdca-dotnet"
        shutil.rmtree(dotnet_dir)
        dotnet_dir.write_text("not a directory\n", encoding="utf-8")
        before = snapshot(repo)
        for args in (("--check",), ("--fix",)):
            with self.subTest(args=args):
                result = run_script(repo, *args)
                self.assertEqual(1, result.returncode)
                self.assertIn("not a directory: skills/pdca-dotnet", result.stderr)
                self.assertEqual(before, snapshot(repo),
                                 "a non-directory ancestor must abort before any write")
                self.assertFalse(self.mirror(repo, "pdca-coder", "pdca-planner").exists())
                self.assertFalse(self.mirror(repo, "pdca-dotnet", "pdca-planner").exists())

    def test_symlink_mirror_directory_is_rejected_and_leaves_both_trees_unchanged(self) -> None:
        repo, _ = self.make_repo()
        other = self.other_tree()
        marker = other / "marker.txt"
        marker.write_text("outside tree\n", encoding="utf-8")
        target_dir = repo / "skills/pdca-coder/assets/opencode-agents"
        shutil.rmtree(target_dir)
        target_dir.symlink_to(other)
        repo_before = snapshot(repo)
        other_before = snapshot(other)
        for args in (("--check",), ("--fix",)):
            with self.subTest(args=args):
                result = run_script(repo, *args)
                self.assertEqual(1, result.returncode)
                self.assertIn("symlink ancestor: skills/pdca-coder/assets/opencode-agents",
                              result.stderr)
                self.assertEqual(repo_before, snapshot(repo),
                                 "the repository tree must not change")
                self.assertEqual(other_before, snapshot(other),
                                 "a linked mirror directory must not be written")
                self.assertTrue(target_dir.is_symlink())
                self.assertFalse((target_dir / "pdca-planner.md").exists())

    def test_broken_source_and_mirror_links_are_handled(self) -> None:
        repo, canonical = self.make_repo()
        (canonical / "pdca-check.md").unlink()
        (canonical / "pdca-check.md").symlink_to(self.other_tree() / "missing.md")
        result = run_script(repo, "--fix")
        self.assertEqual(1, result.returncode)
        self.assertIn("symlink source:", result.stderr)
        self.assertFalse(self.mirror(repo, "pdca-coder", "pdca-check").exists())

        # A broken link in a mirror parent is equally rejected before any write.
        repo2, _ = self.make_repo()
        target_dir = repo2 / "skills/pdca-coder/assets/opencode-agents"
        shutil.rmtree(target_dir)
        target_dir.symlink_to(self.other_tree() / "missing-dir")
        result = run_script(repo2, "--fix")
        self.assertEqual(1, result.returncode)
        self.assertIn("symlink ancestor:", result.stderr)
        self.assertFalse((target_dir / "pdca-planner.md").exists())

    def test_repeated_fix_is_byte_identical(self) -> None:
        repo, _ = self.make_repo()
        self.assertEqual(0, run_script(repo, "--fix").returncode)
        first = snapshot(repo)
        for _ in range(2):
            result = run_script(repo, "--fix")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(first, snapshot(repo))
            self.assertNotIn("fixed:", result.stdout)


if __name__ == "__main__":
    unittest.main()
