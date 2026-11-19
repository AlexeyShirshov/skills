"""The .NET overlay inherits the base evidence root and adds no path of its own.

The base contract owns `.pdca/<task>/rv<k>/` and the persistence rule. The
overlay stores proof there and builds the original candidate in its checkout.

Run:
    python3 -m unittest discover -s skills/pdca-dotnet/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "")).strip()


class EvidenceInheritanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = norm(SKILL.read_text(encoding="utf-8")).lower()

    def test_overlay_declares_no_evidence_path_of_its_own(self) -> None:
        for token in (
            "local counter or evidence path of its own",
            "the overlay inherits the base evidence_root",
            "introduces no path that competes with it",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_build_evidence_is_persisted_without_copying_the_candidate(self) -> None:
        self.assertIn("persist the build evidence, not a buildable project copy", self.text)
        self.assertIn("leave .csproj and other product files in the checkout", self.text)
        self.assertIn("record candidate identity in place", self.text)
        self.assertNotIn("byte copy", self.text)

    def test_the_old_mandated_path_wording_does_not_return(self) -> None:
        self.assertNotIn("or mandated evidence path", self.text)


if __name__ == "__main__":
    unittest.main()
