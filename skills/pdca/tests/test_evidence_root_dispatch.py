"""Regression guards: CHECK's evidence lives in the cycle's `.pdca` evidence root.

A cycle once ended with the only raw log in a scratch directory outside the project
(`/tmp/opencode`): `pdca-check` reads `.pdca/**` only, could not reach it, and the
evidence had to be re-gathered.  The contract now closes that hole in three linked
places, and these static guards keep all three honest:

* the base §Workspace and durable status is the single source — an explicit
  `evidence_root` in every DO dispatch, and evidence persisted there instead of a
  scratch-only copy;
* `pdca-executor` receives the root and persists full logs under it, while
  temporary scratch outside `.pdca/` stays allowed beside the persisted copy;
* the driver's DO transport names the root and defers the rule to the base, which refuses
  scratch-only evidence and a pointer CHECK cannot read.

Mirror parity is not retested here: `sync_role_assets.py --check` is the
authoritative guard (asserted in ``test_role_assets.py``).

A **product file** itself is never relocated into `.pdca/`; the snapshot, staged
copy or diff that CHECK reads is the evidence and lives under the root.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
BASE = SKILL_DIR / "SKILL.md"
EXECUTOR = SKILL_DIR / "assets/opencode-agents/pdca-executor.md"
CHECK_ASSET = SKILL_DIR / "assets/opencode-agents/pdca-check.md"
DRIVER_REF = SKILL_DIR / "references/driver.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip().lower()


def raw_section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start + len(start_marker))
    return text[start:end]


def section(text: str, start_marker: str, end_marker: str) -> str:
    return norm(raw_section(text, start_marker, end_marker))


def paragraph(text: str, starts_with: str) -> str:
    for part in re.split(r"\n\s*\n", text):
        if norm(part).startswith(starts_with):
            return norm(part)
    raise AssertionError("no paragraph starting with %r" % starts_with)


def bullet(text: str, marker: str) -> str:
    """One bullet of a tight list: from `marker` to the next top-level bullet."""
    start = text.index(marker)
    rest = text[start + len(marker):]
    end = re.search(r"\n- ", rest)
    return norm(marker + (rest[:end.start()] if end else rest))


class BaseContractTest(unittest.TestCase):
    """The evidence-root rule has one home: the base workspace section."""

    def setUp(self) -> None:
        self.text = read(BASE)
        self.window = ("### Workspace and durable status", "### Effort and time policy")
        self.workspace = section(self.text, *self.window)

    def test_workspace_defines_the_explicit_evidence_root(self) -> None:
        for token in (
            "evidence root",
            "evidence_root",
            "every do dispatch",
            "check-directed re-gather",
            "contract default .pdca/<task>/rv<k>/",
            "attempts under attempts/",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.workspace)

    def test_evidence_is_persisted_even_when_scratch_is_used(self) -> None:
        for token in (
            "persisted there",
            "full logs",
            "temporary scratch files may live outside .pdca/",
            "never the only source",
            "written under evidence_root before do returns",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.workspace)

    def test_the_persistence_reason_is_checks_scoped_read(self) -> None:
        # Without this clause the rule looks arbitrary and gets "simplified" away.
        raw = re.sub(r"\s+", " ", raw_section(self.text, *self.window))
        self.assertIn("CHECK's scoped read reaches `.pdca/**` only", raw)

    def test_originals_stay_put_but_a_check_snapshot_is_evidence(self) -> None:
        self.assertIn("the product files themselves stay wherever the task puts them", self.workspace)
        self.assertIn("evidence never relocates an original", self.workspace)
        self.assertIn("a snapshot, staged copy or diff", self.workspace)
        self.assertIn("separate artefact under evidence_root", self.workspace)

    def test_plan_to_do_handoff_carries_the_root(self) -> None:
        text = paragraph(self.text, "plan → do")
        self.assertIn("evidence_root", text)
        self.assertIn("§workspace and durable status", text)

    def test_check_to_do_regather_lands_in_the_root(self) -> None:
        check = section(self.text, "#### CHECK", "#### ACT")
        start = check.index("- check → do")
        end = check.index("- check → plan", start)
        regather = check[start:end]
        self.assertIn("re-gathered into the cycle's evidence_root", regather)
        self.assertIn("not a counted defect or attempt", regather)

    def test_run_bullet_points_at_the_root_not_at_scratch(self) -> None:
        evidence = section(self.text, "### Evidence over assertion", "### Workspace and durable")
        self.assertIn("path under the cycle's evidence_root", evidence)


class ExecutorAssetTest(unittest.TestCase):
    """`pdca-executor` must receive the root and persist what CHECK will read."""

    def setUp(self) -> None:
        self.text = read(EXECUTOR)
        self.low = norm(self.text)
        self.rule = bullet(self.text, "- **Evidence, not assertion.**")

    def test_brief_input_names_the_evidence_root(self) -> None:
        inputs = section(self.text, "## Inputs (what the brief contains)", "## Rules")
        for token in ("evidence_root", ".pdca/<task>/rv<k>/"):
            with self.subTest(token=token):
                self.assertIn(token, inputs)

    def test_full_logs_are_persisted_and_scratch_is_only_scratch(self) -> None:
        for token in (
            "persist what check will read under the cycle's evidence_root",
            "exists only in scratch outside .pdca/",
            "is not evidence",
            "the run is then re-gathered",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.rule)

    def test_scratch_is_allowed_beside_the_persisted_copy(self) -> None:
        self.assertIn(
            "scratch outside .pdca/ is allowed beside the persisted copy, not instead of it",
            self.rule,
        )
        self.assertNotIn("do not write outside .pdca/", self.low)

    def test_originals_stay_put_but_a_snapshot_is_persisted(self) -> None:
        self.assertIn(
            "the product files themselves stay where the task puts them (never moved into .pdca/)",
            self.rule,
        )
        self.assertIn("a snapshot, staged copy or diff that check must read is evidence", self.rule)
        self.assertIn("goes under evidence_root, bound to the source identity", self.rule)

    def test_missing_root_falls_back_to_the_contract_default(self) -> None:
        self.assertIn("falls back to the contract default", self.rule)
        self.assertIn("never an ad-hoc directory", self.rule)

    def test_output_contract_reports_the_persisted_path(self) -> None:
        output = section(self.text, "## Output contract", "Do not send diffs")
        self.assertIn("log path under evidence_root", output)


class DriverDispatchTest(unittest.TestCase):
    """The driver's DO transport names the root; the base owns the rule and both refusals."""

    def setUp(self) -> None:
        self.text = read(DRIVER_REF)
        self.base = read(BASE)
        self.transport = section(self.text, "## Dispatch transport", "## Read scope")
        self.workspace = section(self.base, "### Workspace and durable status", "### Effort and time policy")

    def test_driver_do_transport_names_the_root(self) -> None:
        do = bullet(self.text, "- **DO**")
        for token in (
            "frozen plan by exact reference",
            "the cycle's evidence_root",
            "phase-specific deltas",
        ):
            with self.subTest(token=token):
                self.assertIn(token, do)

    def test_driver_defers_the_root_rule_to_its_owner(self) -> None:
        owners = section(self.text, "| Rule | Owner |", "## Entry adoption")
        self.assertIn("evidence root", owners)
        self.assertIn("§workspace and durable status", owners)
        # The procedure (which dispatch, which default, why) is not restated in the driver.
        self.assertNotIn("contract default .pdca/<task>/rv<k>/", self.transport)

    def test_one_rule_covers_initial_follow_up_and_regather(self) -> None:
        for token in (
            "every do dispatch",
            "the initial one",
            "a follow-up",
            "check-directed re-gather",
            ".pdca/<task>/rv<k>/",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.workspace)
        # It is a single rule, not a second paragraph that can drift from the first.
        self.assertEqual(1, norm(self.base).count("every do dispatch"))

    def test_scratch_only_evidence_is_not_a_handoff(self) -> None:
        for token in (
            "temporary scratch files may live outside .pdca/",
            "never the only source",
            "written under evidence_root before do returns",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.workspace)

    def test_a_pointer_check_cannot_read_is_not_a_handoff(self) -> None:
        self.assertIn("a reference the role cannot reach is not a handoff", self.workspace)
        # `norm` strips the asterisks of `.pdca/**`.
        self.assertIn("check's scoped read reaches .pdca/ only", self.workspace)


class SingleSourceTest(unittest.TestCase):
    """One policy: no second copy of the layout, no widened CHECK read."""

    def test_layout_tree_keeps_the_evidence_dir(self) -> None:
        text = read(BASE)
        start = text.index("```text\n.pdca/")
        layout = norm(text[start:text.index("\n```", start)])
        self.assertIn("<task>/rv<k>/", layout)
        self.assertIn("evidence", layout)
        self.assertNotIn("status path", layout)

    def test_check_read_scope_stays_pdca_only(self) -> None:
        # The persistence rule exists *because* CHECK cannot read outside `.pdca/`;
        # widening this read would silently retire the reason.
        text = read(CHECK_ASSET)
        frontmatter = text[3:text.find("\n---", 3)]
        read_block = re.search(r"^  read:\n((?:    .*\n)+)", frontmatter, re.MULTILINE)
        self.assertIsNotNone(read_block, "pdca-check must keep an explicit read map")
        allowed = re.findall(r'"([^"]+)":\s*allow', read_block.group(1))
        self.assertEqual([".pdca/**"], allowed)


if __name__ == "__main__":
    unittest.main()
