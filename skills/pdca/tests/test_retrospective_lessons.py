"""Regression guards: mandatory ACT retrospective and `## Lessons learned`.

The base cycle contract closes every cycle with a short evidence-grounded
retrospective through the same configured `pdca-check` role in `retrospective`
mode, recorded by `pdca-executor` in a fixed `## Lessons learned` section.
These guards pin the skeleton position, route coverage, the normal-CHECK
discriminator, the driver/executor single-writer completion contract, and the
optional beyond-status durable-memory distinction.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
FAMILY = REPO / "skills"
BASE = SKILL_DIR / "SKILL.md"
ACT_REF = SKILL_DIR / "references/act.md"
CHECK_REF = SKILL_DIR / "references/check.md"
DRIVER_REF = SKILL_DIR / "references/driver.md"
CHECK_ASSET = SKILL_DIR / "assets/opencode-agents/pdca-check.md"
EXECUTOR_ASSET = SKILL_DIR / "assets/opencode-agents/pdca-executor.md"
SYNC_SCRIPT = FAMILY / "pdca/scripts/sync_role_assets.py"
GEN_SCRIPT = FAMILY / "pdca/scripts/gen_host_agents.py"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    """Normalize prose for stable protocol-token checks."""
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


def skeleton(text: str) -> str:
    start = text.index("## Status file")
    fence = text.index("````markdown", start)
    end = text.index("````", fence + len("````markdown"))
    return text[fence + len("````markdown"):end]


def section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start + len(start_marker))
    return text[start:end]


def frontmatter(path: Path) -> dict:
    text = read(path)
    end = text.find("\n---", 3)
    node: dict = {}
    stack = [(-1, node)]
    for raw in text[3:end].splitlines():
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
    return node


def permission(path: Path) -> dict:
    return frontmatter(path).get("permission", {})


class BaseSkeletonTest(unittest.TestCase):
    """The fixed skeleton carries `## Lessons learned` in its canonical position."""

    def setUp(self) -> None:
        self.block = skeleton(read(ACT_REF))

    def test_lessons_learned_immediately_follows_act_record(self) -> None:
        headings = [line.strip() for line in self.block.splitlines() if line.startswith("## ")]
        self.assertEqual(
            headings.index("## Lessons learned"),
            headings.index("## ACT record") + 1,
        )
        self.assertLess(
            headings.index("## Lessons learned"),
            headings.index("## Revision history"),
        )

    def test_progress_log_remains_last(self) -> None:
        headings = [line.strip() for line in self.block.splitlines() if line.startswith("## ")]
        self.assertEqual(headings[-1], "## Progress log")

    def test_pending_marker_is_the_initial_value(self) -> None:
        body = section(self.block, "## Lessons learned", "## Revision history")
        self.assertIn("pending: retrospective not yet conducted", body)
        self.assertIn("No new lessons", body)
        self.assertIn("after actual analysis", body)

    def test_no_check_is_preserved_as_absent(self) -> None:
        body = section(self.block, "## CHECK record", "## ACT record")
        self.assertIn("not run: <reason>", body)


class ActRetrospectiveContractTest(unittest.TestCase):
    """The ACT reference owns the mandatory retrospective and its completion contract."""

    def setUp(self) -> None:
        self.text = read(ACT_REF)
        self.body = norm(section(self.text, "## Retrospective (mandatory, ACT)", "## Status file"))
        self.contract = norm(section(self.text, "## Closing order", "## Status file"))

    def test_all_act_routes_inherit_the_retrospective(self) -> None:
        for token in (
            "successful check → act",
            "terminal check → act (stop)",
            "plan → act",
            "do → act",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)
        self.assertIn("intermediate check → do and check → plan do not trigger", self.body)

    def test_no_check_prerequisite_for_terminal_routes(self) -> None:
        self.assertIn("no check is required for plan → act or do → act", self.body)
        self.assertIn("check: not run", self.body)
        self.assertIn("preserves the originating accepted/stop outcome", self.contract)

    def test_retrospective_is_analysis_not_a_verdict(self) -> None:
        for token in (
            "no verdict",
            "no criteria matrix",
            "no transition authority",
            "never overrides",
            "no new verification, proving or research",
            "no new lessons",
            "completion signal",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)
        for token in ("creates no new counter", "attempt or verification"):
            with self.subTest(token=token):
                self.assertIn(token, self.contract)

    def test_single_writer_completion_contract(self) -> None:
        for token in (
            "single-writer completion",
            "raw retrospective report",
            "source input",
            "closure blocker",
            "fallback analysis",
            "only then marks act completed",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.contract)

    def test_optional_durable_memory_is_distinct(self) -> None:
        closing = norm(section(self.text, "## Closing order", "## Retrospective (mandatory, ACT)"))
        self.assertIn("retrospective (mandatory)", closing)
        self.assertIn("durable lesson (optional, beyond status)", closing)
        self.assertIn("distinct from the mandatory status retrospective", closing)
        self.assertIn("optional and permission-bound", closing)
        self.assertIn("no repository or host-config edit is required", closing)


class StatusSectionOwnershipTest(unittest.TestCase):
    """ACT owns its record and the retrospective section in the same write."""

    def test_act_fills_record_and_lessons_together(self) -> None:
        for path in (ACT_REF, EXECUTOR_ASSET):
            body = norm(read(path))
            with self.subTest(path=path.name):
                self.assertIn("act fills ## act record and ## lessons learned", body)

    def test_unrun_phase_keeps_its_pending_value(self) -> None:
        for path in (ACT_REF, EXECUTOR_ASSET):
            body = norm(read(path))
            with self.subTest(path=path.name):
                self.assertIn("pending/not reached/not applicable", body)


class BaseContractTest(unittest.TestCase):
    """The base ACT caller contract names the retrospective route and budget."""

    def setUp(self) -> None:
        self.text = read(BASE)
        start = self.text.index("#### ACT")
        end = self.text.index("### Evidence over assertion", start)
        self.raw_act = self.text[start:end]
        self.act = norm(self.raw_act)

    def test_act_reuses_pdca_check_in_retrospective_mode(self) -> None:
        for token in (
            "no separate subagent role",
            "analysis reuses pdca-check in retrospective mode",
            "every closure",
            "## lessons learned",
            "references/act.md",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.act)

    def test_act_stays_within_caller_budget(self) -> None:
        self.assertLessEqual(len(self.raw_act.encode("utf-8")), 1350)

    def test_check_inline_delivery_covers_retrospective(self) -> None:
        start = self.text.index("#### CHECK")
        end = self.text.index("#### ACT", start)
        body = norm(self.text[start:end])
        self.assertIn("act retrospective", body)
        self.assertIn("references/act.md", body)

    def test_reference_ownership_covers_retrospective(self) -> None:
        refs = norm(section(self.text, "- `references/plan.md`", "- `references/escalate.md`"))
        self.assertIn("act retrospective", refs)
        self.assertIn("retrospective section", refs)


class DriverContractTest(unittest.TestCase):
    """The driver inlines both contracts and keeps its read scope exceptional and compact."""

    def setUp(self) -> None:
        self.text = read(DRIVER_REF)

    def test_driver_inlines_check_and_act_retrospective_contracts(self) -> None:
        body = norm(self.text)
        self.assertIn("complete contents", body)
        self.assertIn("check.md", body)
        self.assertIn("retrospective contract from references/act.md", body)
        self.assertIn("act retrospective", body)

    def test_driver_read_scope_has_narrow_act_exception(self) -> None:
        body = norm(self.text)
        self.assertIn(
            "no phase or form procedure reference except references/act.md's retrospective contract for inline delivery",
            body,
        )

    def test_driver_stays_compact(self) -> None:
        self.assertLessEqual(len(self.text.splitlines()), 120)


class RoleScopeTest(unittest.TestCase):
    """`pdca-check` keeps its exact read-only scope and names retrospective mode."""

    def test_check_permission_is_exact(self) -> None:
        perm = permission(CHECK_ASSET)
        self.assertEqual("deny", perm.get("*"))
        for action in ("read", "glob", "list"):
            allowed = {k for k, v in perm[action].items() if v == "allow"}
            self.assertEqual({".pdca/**"}, allowed)
        for action in ("edit", "write", "bash", "external_directory"):
            self.assertNotIn(action, perm)

    def test_check_declares_medium_tier(self) -> None:
        self.assertIn("# tier: medium", read(CHECK_ASSET))

    def test_check_names_retrospective_mode_and_inline_contract(self) -> None:
        body = norm(read(CHECK_ASSET))
        self.assertIn("retrospective mode", body)
        self.assertIn("use the full contract supplied inline by the driver", body)
        self.assertIn("do not open an installed reference path", body)
        self.assertIn("normal check", body)

    def test_executor_names_retrospective_source_input(self) -> None:
        body = norm(read(EXECUTOR_ASSET))
        for token in (
            "retrospective source input",
            "raw retrospective report",
            "## lessons learned",
            "closure blocker",
            "fallback analysis",
            "only then mark act completed",
        ):
            with self.subTest(token=token):
                self.assertIn(token, body)

    def test_normal_check_reference_retains_its_contract(self) -> None:
        body = norm(read(CHECK_REF))
        self.assertIn("## retrospective mode (act)", body)
        self.assertIn("produces no verdict", body)
        self.assertIn("## verdict and routing", body)
        self.assertIn("## honest limits", body)


class ParityTest(unittest.TestCase):
    """Canonical, mirror and generated role assets stay aligned."""

    def test_sync_check_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--repo", str(REPO), "--check"],
            capture_output=True,
            text=True,
            env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"},
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_generation_check_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GEN_SCRIPT), "--check"],
            capture_output=True,
            text=True,
            env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"},
            cwd=str(REPO),
        )
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
