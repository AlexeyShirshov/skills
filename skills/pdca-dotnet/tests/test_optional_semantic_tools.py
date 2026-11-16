"""Regression guards for portable, policy-aware C# symbol tooling."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "skills/pdca-dotnet/SKILL.md"


class OptionalSemanticToolContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL.read_text(encoding="utf-8")
        start = cls.skill.index("### Semantic tooling for C# symbols")
        end = cls.skill.index("\n### .NET specialists", start)
        cls.section = " ".join(cls.skill[start:end].split())

    def test_roslyn_is_not_a_dependency_or_sole_resolver(self) -> None:
        self.assertIn("Roslyn is one possible method", self.section)
        self.assertIn("not an overlay dependency", self.section)
        self.assertIn("the sole resolver allowed by this skill", self.section)

    def test_host_policy_and_permissions_take_precedence(self) -> None:
        self.assertIn("Higher-priority host/project requirements and permissions", self.section)
        self.assertIn("A permission denial is a policy constraint", self.section)
        self.assertIn("do not bypass it", self.section)
        self.assertIn("automatic install request", self.section)

    def test_text_matches_remain_candidates_not_resolved_symbols(self) -> None:
        self.assertIn("Text matches alone do not establish resolved bindings", self.section)
        self.assertIn("label them as candidates and state uncertainty", self.section)

    def test_missing_tool_only_unverifies_the_unmet_criterion(self) -> None:
        self.assertIn("report that criterion as unverified under the base contract", self.section)
        self.assertIn("does not block unrelated criteria or all .NET work", self.section)

    def test_no_roslyn_catalog_bootstrap_or_v2_call_is_required(self) -> None:
        for obsolete in (
            "Roslyn-first",
            "tools.roslyn",
            'search({ query: "roslyn" })',
            "catalog does not show the tool",
        ):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, self.skill)

    def test_active_docs_do_not_teach_universal_roslyn_first(self) -> None:
        paths = (
            REPO / "README.md",
            REPO / "docs/pdca-dotnet.md",
            REPO / "docs/ru/pdca-dotnet.md",
            REPO / "docs/pdca-guide.md",
            REPO / "docs/ru/pdca-guide.md",
        )
        for path in paths:
            with self.subTest(path=path.relative_to(REPO)):
                content = path.read_text(encoding="utf-8")
                for obsolete in (
                    "Roslyn-first",
                    "resolved with the `roslyn` tool",
                    "разрешаются инструментом `roslyn`",
                ):
                    self.assertNotIn(obsolete, content)


if __name__ == "__main__":
    unittest.main()
