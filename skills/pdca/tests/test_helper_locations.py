"""Helper locations: an overlay's helpers live in that overlay's `scripts/`, not the base's.

Regression guard for a real confusion (nextorm rc5 entry): a preflight listed the **base**
`skills/pdca/scripts/` (which ships only `pdca_cost.py` + `plan_lint.py`), did not find the
two .NET helpers, and concluded "the installed skill has no validators" — while
`skills/pdca-dotnet/scripts/` shipped both. The contract must say, in the base skill, the
overlay skill and the install docs, that

* a helper belongs to the package that ships it, so the base directory says nothing about
  an overlay helper;
* `.pdca/scripts/` is workspace, not installation: absence there is the pre-staging state;
* a missing workspace copy is never grounds for a substitute gate, a waiver or a deviation.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_helper_locations.py' -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

DOTNET_HELPERS = ("validate_inner_loop.py", "pdca_evidence.py")
BASE_HELPERS = ("pdca_cost.py", "plan_lint.py")


def read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


class ShippedHelperLayoutTest(unittest.TestCase):
    def test_dotnet_helpers_ship_only_with_the_overlay(self) -> None:
        overlay = REPO / "skills/pdca-dotnet/scripts"
        base = REPO / "skills/pdca/scripts"
        for helper in DOTNET_HELPERS:
            with self.subTest(helper=helper):
                self.assertTrue((overlay / helper).is_file(), "overlay missing %s" % helper)
                self.assertFalse((base / helper).exists(), "base unexpectedly ships %s" % helper)
        for helper in BASE_HELPERS:
            with self.subTest(helper=helper):
                self.assertTrue((base / helper).is_file(), "base missing %s" % helper)


class SkillDisambiguationTest(unittest.TestCase):
    def test_overlay_skill_names_its_own_scripts_dir_and_the_project_workspace(self) -> None:
        text = norm(read("skills/pdca-dotnet/SKILL.md"))
        for token in (
            "`../pdca-dotnet/scripts/`",
            "`<skills-root>/pdca-dotnet/scripts/`",
            "`../pdca/scripts/` carries `pdca_cost.py` and `plan_lint.py` only",
            "`.pdca/scripts/`",
            "byte-identical copies",
            "never grounds for a substitute gate",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_driver_reference_rejects_treating_an_empty_workspace_copy_as_unavailable(self) -> None:
        text = norm(read("skills/pdca/references/driver.md"))
        for token in (
            "An overlay's helper lives in that overlay's `scripts/`",
            "`validate_inner_loop.py` and `pdca_evidence.py` there, never in the base's",
            "`.pdca/scripts/` starts empty",
            "stages byte-identical copies",
            "never a substitute-check, waiver or `Notice:` ground",
        ):
            with self.subTest(token=token):
                self.assertIn(token, text)


class InstallDocsDisambiguationTest(unittest.TestCase):
    def test_install_docs_point_at_the_overlay_scripts_dir(self) -> None:
        cases = {
            "docs/install.md": (
                "only in its own `pdca-dotnet/scripts/`",
                "the base `pdca/scripts/` does not carry them",
                "normal pre-staging state",
            ),
            "docs/ru/install.md": (
                "только в своём `pdca-dotnet/scripts/`",
                "в базовом `pdca/scripts/` их нет",
                "нормальное состояние до стейджинга",
            ),
        }
        for rel, tokens in cases.items():
            text = norm(read(rel))
            for token in tokens:
                with self.subTest(path=rel, token=token):
                    self.assertIn(token, text)

    def test_overlay_docs_state_the_same_rule(self) -> None:
        cases = {
            "docs/pdca-dotnet.md": ("`<skills-root>/pdca-dotnet/scripts/`", "substitute gate"),
            "docs/ru/pdca-dotnet.md": ("`<skills-root>/pdca-dotnet/scripts/`", "подменного гейта"),
        }
        for rel, tokens in cases.items():
            text = norm(read(rel))
            for token in tokens:
                with self.subTest(path=rel, token=token):
                    self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
