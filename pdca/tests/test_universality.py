"""Domain-neutrality guards for the universal `pdca` runtime.

Rule-presence/absence only: these tests read the runtime surface as text; they
never execute a model or a real cycle.  The universal skill must not carry a list
of task types, domain examples, mandatory domain specialists, a security-audit
lens/section, or a code/test/docs stream model.  It must still keep the generic
operating constraints (permission/authority boundary, untrusted-content and
injection distinction, credential confidentiality, user authorization for
consequential/external actions, no permission bypass).

The runtime surface is the SKILL plus the role assets/host agents; the
``tests/`` directory itself is not scanned.

Run:
    python3 -m unittest discover -s config/skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

SKILL_PATH = REPO / "config/skills/pdca/SKILL.md"
ASSET_AGENTS = REPO / "config/skills/pdca/assets/agents"
HOST_AGENTS = tuple(
    REPO / ("config/agents/pdca-%s.md" % name)
    for name in ("planner", "executor", "check", "escalate")
)

ALLOWED_ROLES = frozenset(
    ("pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate",
     "pdca-orchestrator", "scout")
)
ROLE_TOKEN = re.compile(r"pdca-[a-z]+")

# Markers of a domain example / task-type list: none may appear.
DOMAIN_EXAMPLE_MARKERS = (
    "worked example",
    "deliverable type",
    "task types:",
    "csv",
    "cli",
    "presentation",
    "onboarding",
)
# Markers of a code/test/docs stream model: the universal skill has none.
STREAM_MARKERS = (
    "parallel do streams",
    "test first, then code",
    "docs later",
    "code/test/docs",
    "prose documentation",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("*", "")).strip()


def runtime_texts() -> dict:
    texts = {SKILL_PATH: read(SKILL_PATH)}
    if ASSET_AGENTS.is_dir():
        for p in sorted(ASSET_AGENTS.glob("*.md")):
            texts[p] = read(p)
    for p in HOST_AGENTS:
        if p.is_file():
            texts[p] = read(p)
    return texts


class UniversalityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.texts = runtime_texts()
        cls.skill_raw = cls.texts[SKILL_PATH]
        cls.skill = norm(cls.skill_raw)

    # --- no task-type list / no domain examples ---------------------------

    def test_skill_declares_neutrality(self):
        self.assertIn("The cycle is domain-neutral", self.skill)
        self.assertIn("no task-type list and no domain example", self.skill)

    def test_no_domain_example_or_task_type_markers(self):
        for path, raw in self.texts.items():
            low = raw.lower()
            for marker in DOMAIN_EXAMPLE_MARKERS:
                with self.subTest(path=str(path), marker=marker):
                    self.assertNotIn(marker, low)

    # --- no mandatory domain specialists ----------------------------------

    def test_roles_referenced_are_only_the_universal_set(self):
        offenders = set()
        for path, raw in self.texts.items():
            for hit in ROLE_TOKEN.findall(raw):
                if hit not in ALLOWED_ROLES:
                    offenders.add((str(path), hit))
        self.assertEqual(set(), offenders, "non-universal role names: %r" % sorted(offenders))

    def test_no_security_auditor_or_domain_specialist(self):
        joined = " ".join(self.texts.values()).lower()
        self.assertNotIn("security-auditor", joined)
        self.assertNotIn("security lens", joined)
        self.assertNotIn("specialist is mandatory", joined)
        self.assertNotIn("mandatory stack", joined)

    def test_no_security_or_audit_section_header(self):
        headers = []
        for raw in self.texts.values():
            headers += [ln for ln in raw.splitlines() if ln.startswith("#")]
        for header in headers:
            low = header.lower()
            self.assertNotIn("security", low, header)
            self.assertNotIn("audit", low, header)

    # --- generic operating constraints still present ----------------------

    def test_generic_operating_constraints_present(self):
        for token in (
            "Authority and permission boundaries",
            "Trusted instructions vs untrusted content",
            "Injection defense",
            "Credential confidentiality",
            "User authorization for consequential or external actions",
            "Never bypass permissions",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.skill)

    # --- no code/test/docs stream model -----------------------------------

    def test_skill_does_not_frame_code_test_docs_streams(self):
        low = self.skill_raw.lower()
        for marker in STREAM_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, low)


if __name__ == "__main__":
    unittest.main()
