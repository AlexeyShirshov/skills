"""Collection contract regression tests: one skill file, inherited common rules."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"

class CollectionContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_one_contract_under_50kb(self):
        self.assertLess(len(SKILL.read_bytes()), 50000)
        self.assertFalse((ROOT / "references").exists())

    def test_base_contract_inherited(self):
        self.assertIn("../pdca/SKILL.md", self.text)
        self.assertIn("single source of shared rules", self.text)

    def test_batch_model_and_inlined_sections(self):
        for term in ("## Batch terminology", "### P — per-item PLANs",
                     "### D — infrastructure", "### C — integration verification",
                     "### A — completion", "## Lane execution and schedule revision",
                     "## Collection status record", "### Routing campaign outcomes",
                     "## Git model details", "### The queue and the per-item continuation"):
            with self.subTest(term=term): self.assertIn(term, self.text)

    def test_completion_and_preservation(self):
        for term in ("**An `incomplete` group is never merged**",
                     "A STOP or any", "cleanup and merging are forbidden",
                     "final `incomplete`", "other groups continue"):
            with self.subTest(term=term): self.assertIn(term, self.text)

    def test_no_deleted_reference_links(self):
        self.assertNotIn("references/lane.md", self.text)
        self.assertNotIn("references/status.md", self.text)

if __name__ == "__main__": unittest.main()
