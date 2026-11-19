"""Exercise the executor → driver (one path) → scoped reader boundary."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest


BASE = Path(__file__).resolve().parents[1]


class CheckHandoffTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.brief = Path(".pdca/sample/rv1/brief.md")
        (self.root / self.brief).parent.mkdir(parents=True)
        (self.root / self.brief).write_text("AC-1: see ./run.json\n")

    def invoke(self, mode, *args):
        return subprocess.run(
            [sys.executable, BASE / "scripts/check_handoff.py", mode, self.brief, *args],
            cwd=self.root, text=True, capture_output=True,
        )

    def packet(self, mode, *args):
        result = self.invoke(mode, *args)
        self.assertEqual(0, result.returncode, result.stderr)
        ref = json.loads(result.stdout)
        path = (self.root / ref["path"]).resolve()
        self.assertEqual(path.parent, (self.root / self.brief).parent)
        data = path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), ref["sha256"])
        self.assertTrue(data.startswith((BASE / "references/check.md").read_bytes()))
        self.assertIn((self.root / self.brief).read_bytes(), data)
        self.assertTrue(data.endswith(b"<!-- end CHECK handoff -->\n"))
        return data

    def test_candidate_only_requested_overlay_and_retrospective_only_its_contract(self):
        label = "Coverage evidence lifecycle"
        candidate = self.packet("candidate", "--section", "pdca-coder:" + label)
        overlay = (BASE.parent / "pdca-coder/SKILL.md").read_bytes()
        heading = b"### " + label.encode()
        start = overlay.index(heading)
        self.assertIn(overlay[start:overlay.index(b"\n### Build and test command forms", start)], candidate)
        retro = self.packet("retrospective")
        self.assertNotIn(heading, retro)
        source = (BASE / "references/act.md").read_bytes()
        self.assertIn(source[source.index(b"## Retrospective"):source.index(b"## Status file")], retro)
        self.assertNotIn(source, retro)

    def test_unavailable_section_returns_no_path_or_partial_packet(self):
        result = self.invoke("candidate", "--section", "pdca-coder:Nonexistent")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual([self.root / self.brief], list((self.root / self.brief).parent.iterdir()))

    def test_pin_preserves_original_bytes_and_detects_drift_without_overwriting(self):
        command = [sys.executable, BASE / "scripts/report_ref.py"]
        pin = [*command, "file", self.brief.parent, self.brief]
        original = "План\r\nрезультат без перевода строки".encode()
        (self.root / self.brief).write_bytes(original)
        receipt = subprocess.check_output(pin, cwd=self.root)
        self.assertEqual(receipt, subprocess.check_output(pin, cwd=self.root))
        ref = json.loads(receipt)
        frozen = self.root / ref["path"]
        self.assertEqual(original, frozen.read_bytes())
        self.assertEqual(ref["sha256"], hashlib.sha256(original).hexdigest())
        frozen.write_bytes(original + b"\n")
        for cmd in ([*command, "verify", ref["path"], ref["sha256"]], pin):
            result = subprocess.run(cmd, cwd=self.root, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn(b"SHA-256 mismatch", result.stderr)
        self.assertEqual(original + b"\n", frozen.read_bytes())
