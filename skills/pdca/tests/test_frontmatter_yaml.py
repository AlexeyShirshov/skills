"""Real-YAML gate for every agent frontmatter block in the PDCA family.

The neighbouring guards read frontmatter with hand-rolled line splitters
(``test_permission_boundaries``, ``test_routing_consistency``): they strip quotes,
ignore any syntax they do not model and never call a YAML parser.  A line such as
``- action: *`` — an unquoted alias — therefore passed the whole suite while the
frontmatter did not parse at all, so the host silently refused to register the
agent as a subagent.  This module closes that hole: the leading ``---`` … ``---``
block is parsed by a real parser and the shape the host relies on is asserted.

Guarded files are glob-discovered, never a hardcoded list:

* ``skills/*/assets/opencode-agents/*.md`` — the canonical roles plus every
  generated overlay mirror (coder / dotnet / collection / incremental);
* ``skills/*/agents/*.md`` — only when such a directory exists in the repo.

Per file: the block parses with a strict ``yaml.SafeLoader`` subclass that rejects
duplicate mapping keys (plain PyYAML would let a second ``permissions:`` silently
override the first); the result is a mapping; ``name``, ``description`` and ``mode``
are non-empty strings, ``name`` equals the file stem and ``mode`` is a host-known
value; a V2 ``permissions:`` list holds ``{action, resource, effect}`` mappings with
a known ``effect``; a V1 ``permission:`` (when present) is a mapping.  The V1↔V2
policy equivalence stays in ``test_routing_consistency``.

Dependency: PyYAML is required.  A missing ``yaml`` fails the module loudly with an
install hint instead of skipping the gate.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_frontmatter_yaml.py' -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - the gate must never silently pass
    raise ImportError(
        "test_frontmatter_yaml.py needs PyYAML to validate agent frontmatter; "
        "install it with `python3 -m pip install pyyaml`"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO_ROOT / "skills"

# Every discovered glob, relative to `skills/`. Order is irrelevant; the set is not
# pinned so a new package or a new role is covered without editing this module.
AGENT_GLOBS = ("*/assets/opencode-agents/*.md", "*/agents/*.md")

DELIMITER = "---"
REQUIRED_KEYS = ("name", "description", "mode")
KNOWN_MODES = {"subagent", "primary", "all"}
KNOWN_EFFECTS = {"allow", "deny", "ask"}
V2_RULE_KEYS = ("action", "resource", "effect")


class StrictLoader(yaml.SafeLoader):
    """``SafeLoader`` that refuses a duplicate mapping key instead of overriding it."""

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None, f"expected a mapping node, got {node.id}", node.start_mark
            )
        self.flatten_mapping(node)
        seen: set[object] = set()
        for key_node, _value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def rel(path: Path) -> str:
    """Repo-relative path for readable assertion messages."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def agent_files() -> list[Path]:
    """Every agent brief in the repo, from the globs above (deduplicated, sorted)."""
    found: set[Path] = set()
    for pattern in AGENT_GLOBS:
        found.update(path for path in SKILLS_DIR.glob(pattern) if path.is_file())
    return sorted(found)


def frontmatter_lines(path: Path) -> list[str]:
    """Lines strictly between the leading ``---`` delimiters, without the delimiters."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != DELIMITER:
        raise AssertionError(f"{rel(path)}: no leading '{DELIMITER}' frontmatter delimiter")
    for index in range(1, len(lines)):
        if lines[index].strip() == DELIMITER:
            return lines[1:index]
    raise AssertionError(f"{rel(path)}: unterminated frontmatter (no closing '{DELIMITER}')")


def load_frontmatter(path: Path) -> object:
    """Parse the frontmatter with the strict loader; fail with file, position, problem."""
    block = frontmatter_lines(path)
    text = "\n".join(block)
    try:
        return yaml.load(text, Loader=StrictLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        position = ""
        if mark is not None:
            # Block line 1 is file line 2; marks are 0-based, the message is 1-based.
            position = (
                f" at line {mark.line + 1} (file line {mark.line + 2}),"
                f" column {mark.column + 1}"
            )
        problem = getattr(exc, "problem", None) or str(exc).replace("\n", " ")
        raise AssertionError(
            f"{rel(path)}: frontmatter is not valid YAML{position}: {problem}"
        ) from exc


def require_str(mapping: dict, key: str, path: Path) -> str:
    """Assert ``mapping[key]`` is a non-empty string and return it."""
    if key not in mapping:
        raise AssertionError(f"{rel(path)}: frontmatter is missing required key {key!r}")
    value = mapping[key]
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(
            f"{rel(path)}: frontmatter key {key!r} must be a non-empty string, got {value!r}"
        )
    return value


class AgentFrontmatterTest(unittest.TestCase):
    """Every agent brief carries frontmatter that a real YAML parser accepts."""

    def test_discovery_is_not_empty(self):
        files = agent_files()
        self.assertTrue(files, f"no agent files matched {AGENT_GLOBS} under {rel(SKILLS_DIR)}")
        self.assertTrue(
            list((SKILLS_DIR / "pdca" / "assets" / "opencode-agents").glob("*.md")),
            "the canonical role directory yielded no files — the glob is broken",
        )

    def test_frontmatter_parses(self):
        """A parse error here is a host-side registration failure, not a style nit."""
        for path in agent_files():
            with self.subTest(path=rel(path)):
                load_frontmatter(path)

    def test_required_keys(self):
        for path in agent_files():
            with self.subTest(path=rel(path)):
                data = load_frontmatter(path)
                self.assertIsInstance(
                    data, dict, f"{rel(path)}: frontmatter must be a mapping, got {type(data).__name__}"
                )
                name = require_str(data, "name", path)
                require_str(data, "description", path)
                mode = require_str(data, "mode", path)
                self.assertEqual(
                    name, path.stem, f"{rel(path)}: frontmatter name {name!r} != file stem {path.stem!r}"
                )
                self.assertIn(mode, KNOWN_MODES, f"{rel(path)}: unknown mode {mode!r}")

    def test_v2_permissions_shape(self):
        """The V2 `permissions:` list is what the host compiles into rules."""
        for path in agent_files():
            with self.subTest(path=rel(path)):
                data = load_frontmatter(path)
                if not isinstance(data, dict) or "permissions" not in data:
                    continue
                rules = data["permissions"]
                self.assertIsInstance(
                    rules, list, f"{rel(path)}: V2 'permissions' must be a list, got {type(rules).__name__}"
                )
                self.assertTrue(rules, f"{rel(path)}: V2 'permissions' list is empty")
                for index, rule in enumerate(rules):
                    where = f"{rel(path)}: permissions[{index}]"
                    self.assertIsInstance(rule, dict, f"{where} must be a mapping, got {rule!r}")
                    for key in V2_RULE_KEYS:
                        self.assertIn(key, rule, f"{where} is missing key {key!r}")
                        value = rule[key]
                        self.assertIsInstance(
                            value, str, f"{where}[{key}] must be a string, got {value!r}"
                        )
                        self.assertTrue(value.strip(), f"{where}[{key}] is empty")
                    self.assertIn(
                        rule["effect"], KNOWN_EFFECTS, f"{where}: unknown effect {rule['effect']!r}"
                    )

    def test_v1_permission_is_mapping(self):
        """The V1 `permission:` map is the other half of the documented pair."""
        for path in agent_files():
            with self.subTest(path=rel(path)):
                data = load_frontmatter(path)
                if not isinstance(data, dict) or "permission" not in data:
                    continue
                self.assertIsInstance(
                    data["permission"],
                    dict,
                    f"{rel(path)}: V1 'permission' must be a mapping, got {type(data['permission']).__name__}",
                )


if __name__ == "__main__":
    unittest.main()
