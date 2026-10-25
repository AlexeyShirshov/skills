#!/usr/bin/env python3
"""Check or regenerate the shared PDCA role-asset compatibility mirrors.

The canonical role definitions live once, in ``skills/pdca/assets/opencode-agents``.
The overlay skills keep real files (not symlinks) at their historical paths so an
existing install command keeps working and so the published packages stay
self-contained.  Every mirror is a byte-identical copy of its canonical file,
frontmatter, body and permissions included.

The path allowlist below is exhaustive: ``--fix`` never creates, edits or deletes
anything else, and ``--check`` ignores unrelated files (for example the
``pdca-security-auditor`` specialist or a hand-written note).  Source paths,
source ancestors and mirror parent directories must not be symlinks, and every
existing mirror parent must be a directory: a linked directory could redirect a
write outside the repository, while a regular file in the path would abort a
partially written batch.  A mirror leaf that is itself a symlink is reported by
``--check`` and replaced by ``--fix`` only when every parent directory is a real
directory inside the repository.

Usage::

    python3 skills/pdca/scripts/sync_role_assets.py            # check (default)
    python3 skills/pdca/scripts/sync_role_assets.py --check    # check
    python3 skills/pdca/scripts/sync_role_assets.py --fix      # regenerate mirrors

Exit codes: 0 = all mirrors match, 1 = missing/drifted/unsafe mirror, 2 = usage/IO
error.  No timestamps and no absolute paths are printed, so the output is stable
in CI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Canonical source, relative to the repository root.
CANONICAL_DIR = Path("skills/pdca/assets/opencode-agents")

COMMON_ROLES = (
    "pdca-planner",
    "pdca-check",
    "pdca-executor",
    "pdca-scout",
    "pdca-escalate",
    "pdca-orchestrator",
)

# Explicit mirror allowlist: skill directory -> role names copied into it.
# ``pdca-security-auditor`` is a coder/.NET specialist, not a shared role, and is
# deliberately absent: it is neither copied nor touched.
MIRRORS = {
    "skills/pdca-coder/assets/opencode-agents": COMMON_ROLES,
    "skills/pdca-dotnet/assets/opencode-agents": COMMON_ROLES,
    "skills/pdca-collection/assets/opencode-agents": ("pdca-orchestrator",),
    "skills/pdca-incremental/assets/opencode-agents": ("pdca-orchestrator",),
}


def expected_mirrors(repo: Path) -> list[tuple[Path, Path]]:
    """Return ``(canonical, mirror)`` pairs from the explicit allowlist."""
    canonical_dir = repo / CANONICAL_DIR
    pairs = []
    for rel_dir, roles in MIRRORS.items():
        for role in roles:
            pairs.append((canonical_dir / f"{role}.md", repo / rel_dir / f"{role}.md"))
    return pairs


def _describe(repo: Path, path: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return path.name


def _first_symlink(repo: Path, path: Path) -> Path | None:
    """First symlink on the repo-relative path to ``path`` (inclusive).

    Works for broken links too: ``is_symlink`` does not need the target to exist.
    """
    try:
        parts = path.relative_to(repo).parts
    except ValueError:
        return path  # outside the repository: never accept
    current = repo
    for part in parts:
        current = current / part
        if current.is_symlink():
            return current
    return None


def _first_non_directory(repo: Path, path: Path) -> Path | None:
    """First existing repo-relative component of ``path`` that is not a directory."""
    try:
        parts = path.relative_to(repo).parts
    except ValueError:
        return path
    current = repo
    for part in parts:
        current = current / part
        if current.exists() and not current.is_dir():
            return current
        if not current.exists():
            return None
    return None


def _audit(repo: Path, for_fix: bool) -> tuple[list[str], list[tuple[Path, Path]]]:
    """Validate every allowlisted pair; return problems and fix operations.

    ``for_fix`` also accepts a leaf mirror symlink (it will be replaced) while
    still rejecting linked source paths and linked mirror parents.
    """
    problems: list[str] = []
    operations: list[tuple[Path, Path]] = []

    for source, target in expected_mirrors(repo):
        source_name = _describe(repo, source)
        target_name = _describe(repo, target)

        linked_source = _first_symlink(repo, source)
        if linked_source is not None:
            problems.append(f"symlink source: {_describe(repo, linked_source)}")
            continue
        if not source.is_file():
            problems.append(f"missing canonical: {source_name}")
            continue

        linked_parent = _first_symlink(repo, target.parent)
        if linked_parent is not None:
            problems.append(f"symlink ancestor: {_describe(repo, linked_parent)}")
            continue
        non_directory = _first_non_directory(repo, target.parent)
        if non_directory is not None:
            problems.append(f"not a directory: {_describe(repo, non_directory)}")
            continue

        if target.is_symlink():
            if for_fix:
                operations.append((source, target))
            else:
                problems.append(f"symlink mirror: {target_name}")
            continue
        if target.exists() and not target.is_file():
            problems.append(f"not a file mirror: {target_name}")
            continue
        if not target.is_file():
            if for_fix:
                operations.append((source, target))
            else:
                problems.append(f"missing mirror: {target_name}")
            continue
        if target.read_bytes() != source.read_bytes():
            if for_fix:
                operations.append((source, target))
            else:
                problems.append(f"drift: {target_name}")

    return problems, operations


def check(repo: Path) -> tuple[int, list[str]]:
    """Compare every allowlisted mirror with its canonical source."""
    problems, _ = _audit(repo, for_fix=False)
    return (1 if problems else 0), problems


def fix(repo: Path) -> tuple[int, list[str]]:
    """Preflight every pair, then write only the allowlisted mirrors."""
    problems, operations = _audit(repo, for_fix=True)
    if problems:
        return 1, problems

    written: list[str] = []
    for source, target in operations:
        if target.is_symlink():
            target.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        written.append(_describe(repo, target))
    for rel in written:
        print(f"fixed: {rel}")
    return 0, []


def _repo_default() -> Path:
    # skills/pdca/scripts/sync_role_assets.py -> repository root
    return Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check or regenerate the shared PDCA role-asset mirrors."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=_repo_default(),
        help="repository root (defaults to the checkout containing this script)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check only (default)")
    mode.add_argument("--fix", action="store_true", help="regenerate drifted mirrors")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    if not (repo / CANONICAL_DIR).is_dir():
        print(f"error: no canonical directory: {CANONICAL_DIR.as_posix()}", file=sys.stderr)
        return 2

    try:
        if args.fix:
            code, problems = fix(repo)
            for problem in problems:
                print(f"error: {problem}", file=sys.stderr)
        else:
            code, problems = check(repo)
            for problem in problems:
                print(f"error: {problem}", file=sys.stderr)
    except OSError as exc:
        # Deterministic and path-free: the raw exception can carry an absolute path.
        reason = exc.strerror or exc.__class__.__name__
        print(f"error: I/O failure: {reason}", file=sys.stderr)
        return 2
    return code


if __name__ == "__main__":
    sys.exit(main())
