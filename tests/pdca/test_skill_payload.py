"""Keep maintainer tooling out of the directories copied by skills installers."""

import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[2] / "skills"
PYTHON_HELPERS = {
    "pdca": {"check_handoff.py", "report_ref.py"},
    "pdca-coder": set(),
    "pdca-collection": {"status_lint.py"},
    "pdca-dotnet": set(),
    "pdca-incremental": set(),
}


class SkillPayloadTest(unittest.TestCase):
    def test_install_roots_only_contain_runtime_python(self):
        for name, helpers in PYTHON_HELPERS.items():
            with self.subTest(skill=name):
                skill = SKILLS / name
                self.assertTrue((skill / "SKILL.md").is_file())
                self.assertEqual(
                    {f"scripts/{helper}" for helper in helpers},
                    {path.relative_to(skill).as_posix() for path in skill.rglob("*.py")},
                )
                self.assertEqual(
                    [],
                    [
                        path.relative_to(skill).as_posix()
                        for path in (skill / "tests").rglob("*")
                        if path.is_file() and "__pycache__" not in path.parts
                    ],
                )
