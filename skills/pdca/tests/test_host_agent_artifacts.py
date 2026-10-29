"""Generated per-harness role agents: parity with the canonical body, envelope per harness.

One role is authored once, in ``assets/opencode-agents/<role>.md``; the Claude Code and Codex sets
are generated from it by ``skills/pdca/scripts/gen_host_agents.py``.  These guards are what makes
shipping them as real files safe:

* the generator's own ``--check`` finds no drift, a missing file or a stale one;
* every package carries the same role set in all three formats;
* the body is byte-identical everywhere — a translation may only change the envelope;
* the Claude Code envelope is exactly ``name``/``description``/``tools`` plus a provenance comment,
  and the tool allowlist keeps the boundaries that matter (no shell or write for PLAN/CHECK);
* the Codex envelope round-trips with the body as ``developer_instructions``;
* no generated file carries a model: the tier binding belongs to the host.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

try:  # Python >= 3.11; the local interpreter may be older
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depends on the interpreter
    tomllib = None  # type: ignore[assignment]

REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "skills/pdca"
SCRIPT = SKILL / "scripts/gen_host_agents.py"
PACKAGES = sorted(REPO.glob("skills/pdca*/assets/opencode-agents"))  # canonical dirs

CLAUDE = "claude-agents"
CODEX = "codex-agents"


def load_generator():
    spec = importlib.util.spec_from_file_location("gen_host_agents", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def without_provenance(text: str) -> str:
    """Drop the generated header line, which names the package's own authored file."""
    return "\n".join(line for line in text.split("\n") if not line.startswith("# Generated from "))


def frontmatter(text: str) -> dict[str, str]:
    """Parse the flat Claude Code frontmatter (comments are skipped, quoted values decoded)."""
    assert text.startswith("---\n"), "no frontmatter"
    end = text.find("\n---\n", 4)
    assert end != -1, "unterminated frontmatter"
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith('"'):
            value = json.loads(value)
        fields[key.strip()] = value
    return fields


def payload(text: str) -> str:
    end = text.find("\n---\n", 4) if text.startswith("---\n") else -1
    assert end != -1, "unterminated frontmatter"
    return text[end + 5 :].lstrip("\n")


def parse_toml(text: str) -> dict:
    """Parse a generated agent file: `tomllib` when available, a narrow reader otherwise.

    The narrow reader covers exactly the layout the generator emits, so a local older interpreter
    still checks the envelope; CI runs 3.12 and exercises the real parser.
    """
    if tomllib is not None:
        return tomllib.loads(text)
    data: dict = {}
    name = re.search(r'^name = "([^"]*)"$', text, re.M)
    assert name, "no name"
    data["name"] = name.group(1)
    description = re.search(r'^description = (".*")$', text, re.M)
    assert description, "no description"
    data["description"] = json.loads(description.group(1))
    body = re.search(r"^developer_instructions = '''\n(.*?)'''$", text, re.S | re.M)
    assert body, "no developer_instructions"
    data["developer_instructions"] = body.group(1)
    if re.search(r"^features\.shell_tool = false$", text, re.M):
        data["features"] = {"shell_tool": False}
    return data


def claude_files(package: Path) -> dict[str, Path]:
    return {path.stem: path for path in sorted((package.parent / CLAUDE).glob("*.md"))}


def codex_files(package: Path) -> dict[str, Path]:
    return {path.stem: path for path in sorted((package.parent / CODEX).glob("*.toml"))}


class GeneratorCheckTest(unittest.TestCase):
    def test_check_reports_no_drift(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("ok:", result.stdout)


class RoleSetTest(unittest.TestCase):
    def test_every_package_carries_the_same_roles_in_all_three_formats(self) -> None:
        self.assertTrue(PACKAGES, "no canonical role packages found")
        for package in PACKAGES:
            canonical = {path.stem for path in package.glob("*.md")}
            with self.subTest(package=package.parents[1].name):
                self.assertTrue(canonical)
                self.assertEqual(canonical, set(claude_files(package)))
                self.assertEqual(canonical, set(codex_files(package)))

    def test_every_generated_file_names_its_canonical_source(self) -> None:
        for package in PACKAGES:
            for files in (claude_files(package), codex_files(package)):
                for name, path in files.items():
                    with self.subTest(file=path.name):
                        text = read(path)
                        match = re.search(r"^# Generated from (\S+) by (\S+) — do not edit this file\.$", text, re.M)
                        self.assertIsNotNone(match, "no provenance header in %s" % path)
                        source, generator = match.groups()
                        self.assertTrue((REPO / source).is_file(), source)
                        self.assertEqual("skills/%s/assets/opencode-agents/%s.md" % (
                            package.parents[1].name, name), source)
                        self.assertEqual("skills/pdca/scripts/gen_host_agents.py", generator)

    def test_identical_canonical_roles_generate_identical_bytes(self) -> None:
        """A generated copy is a pure function of the authored role file.

        The six shared roles are byte-identical mirrors, so their generated copies must be too.
        `pdca-security-auditor` is hand-authored in both overlays and may differ; the guard
        therefore compares packages only where their canonical files are already equal.
        """
        groups: dict[tuple[str, str], list[tuple[Path, Path]]] = {}
        for package in PACKAGES:
            sets = ((CLAUDE, claude_files(package)), (CODEX, codex_files(package)))
            for kind, files in sets:
                for name, path in files.items():
                    groups.setdefault((kind, name), []).append((package / (name + ".md"), path))
        self.assertTrue(groups)
        for (kind, name), pairs in groups.items():
            canonical = {read(src) for src, _ in pairs}
            if len(canonical) != 1:
                continue  # authored per package (the specialist); parity is checked per file
            with self.subTest(kind=kind, role=name):
                # The provenance line names the package's own file, so it may differ; everything
                # after it must not.
                bodies = {without_provenance(read(path)) for _, path in pairs}
                self.assertEqual(1, len(bodies), [str(path) for _, path in pairs])


class ClaudeArtifactTest(unittest.TestCase):
    def test_body_is_the_canonical_body_byte_for_byte(self) -> None:
        for package in PACKAGES:
            for name, path in claude_files(package).items():
                with self.subTest(role=name, package=package.parents[1].name):
                    canonical = read(package / (name + ".md"))
                    self.assertEqual(payload(canonical), payload(read(path)))

    def test_frontmatter_is_the_claude_envelope_only(self) -> None:
        for package in PACKAGES:
            for name, path in claude_files(package).items():
                fields = frontmatter(read(path))
                with self.subTest(role=name, package=package.parents[1].name):
                    self.assertEqual({"name", "description", "tools"}, set(fields))
                    self.assertEqual(name, fields["name"])
                    self.assertEqual(
                        list(GEN.CLAUDE_TOOLS[name]),
                        [tool.strip() for tool in fields["tools"].split(",")],
                    )

    def test_description_matches_the_canonical_one(self) -> None:
        for package in PACKAGES:
            for name, path in claude_files(package).items():
                canonical = GEN.read_role(package / (name + ".md"))
                with self.subTest(role=name):
                    self.assertEqual(canonical["description"], frontmatter(read(path))["description"])

    def test_read_only_roles_get_no_shell_and_no_write(self) -> None:
        for package in PACKAGES:
            for name, path in claude_files(package).items():
                tools = {tool.strip() for tool in frontmatter(read(path))["tools"].split(",")}
                if name in {"pdca-planner", "pdca-check", "pdca-security-auditor"}:
                    with self.subTest(role=name):
                        self.assertIn("Read", tools)
                        self.assertFalse(tools & {"Bash", "Edit", "Write", "Agent"}, sorted(tools))

    def test_only_the_delegating_roles_may_spawn(self) -> None:
        for package in PACKAGES:
            for name, path in claude_files(package).items():
                tools = {tool.strip() for tool in frontmatter(read(path))["tools"].split(",")}
                with self.subTest(role=name):
                    self.assertEqual(
                        name in {"pdca-escalate", "pdca-orchestrator"}, "Agent" in tools
                    )


class CodexArtifactTest(unittest.TestCase):
    def test_toml_carries_the_canonical_body(self) -> None:
        for package in PACKAGES:
            for name, path in codex_files(package).items():
                parsed = parse_toml(read(path))
                canonical = read(package / (name + ".md"))
                with self.subTest(role=name, package=package.parents[1].name):
                    self.assertEqual(name, parsed["name"])
                    self.assertEqual(payload(canonical), parsed["developer_instructions"])
                    self.assertEqual(
                        {"name", "description", "developer_instructions"},
                        set(parsed) - {"features"},
                    )
                    first_line = parsed["developer_instructions"].splitlines()[0]
                    self.assertTrue(first_line.startswith("# "), first_line)

    def test_shell_is_disabled_for_the_roles_that_must_not_run_commands(self) -> None:
        for package in PACKAGES:
            for name, path in codex_files(package).items():
                parsed = parse_toml(read(path))
                shell = parsed.get("features", {}).get("shell_tool", True)
                with self.subTest(role=name):
                    self.assertEqual(name not in GEN.CODEX_SHELL_OFF, shell)


class NoModelBoundTest(unittest.TestCase):
    """The tier binding belongs to the host, never to the shipped role."""

    MODEL_KEYS = {"model", "model_reasoning_effort", "model_reasoning_summary", "model_verbosity"}

    def test_generated_files_carry_no_model(self) -> None:
        for package in PACKAGES:
            for name, path in claude_files(package).items():
                with self.subTest(harness="claude", role=name):
                    self.assertEqual(set(), self.MODEL_KEYS & set(frontmatter(read(path))))
            for name, path in codex_files(package).items():
                with self.subTest(harness="codex", role=name):
                    self.assertEqual(set(), self.MODEL_KEYS & set(parse_toml(read(path))))


if __name__ == "__main__":
    unittest.main()
