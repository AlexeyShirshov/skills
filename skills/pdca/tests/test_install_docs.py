"""Install docs: the checkout commands cover the whole family and ship the runtime helpers.

Guards two install defects:

* the global "from a checkout" copy listed five contracts and silently dropped
  `pdca-entry` (the umbrella), so a fresh host had nothing to route through;
* the install docs claimed that only `SKILL.md` + `assets/` travel and that nothing
  else needs installing, while the helpers under the skill's `scripts/` are the
  source of the byte-identical copies the executor stages into the project's
  `.pdca/scripts/`.

The guards parse the shell commands and the explicit `npx skills add` list instead of
looking for a skill name anywhere in the text, and they match per sentence — no full
phrase snapshots, so the docs stay editable.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import shlex
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

# Every skill the repository ships (a directory with a SKILL.md entry point).
SHIPPED = sorted(
    path.parent.name for path in REPO.glob("skills/pdca*/SKILL.md")
)

CHECKOUT_DOCS = ("README.md", "docs/install.md", "docs/ru/install.md")
INSTALL_FILES = ("docs/install.md", "docs/ru/install.md", "docs/install-prompt.md")

# Sentences that scope the copied content down to `SKILL.md`/`assets/` (or to "the skill
# directory") while leaving `scripts/` out are the defect this module guards.  The subject
# must be the install scope, not an incidental `SKILL.md` mention (e.g. frontmatter checks).
EXCLUSION = re.compile(r"\b(only|nothing else|только|нечего)\b", re.I)
SCOPE_DIRECTORY = re.compile(r"skill directory|каталог(?:а)? скилл", re.I)

# The second half of the same defect: telling the operator to leave the runtime helpers out
# ("do not install scripts", "omit scripts", "скрипты ставить не нужно").  Negation is only
# read inside the clause that names scripts, so "tests/ and diagram generators are dev-only"
# and "scripts only where present" stay allowed.
SCRIPT_WORD = re.compile(r"\b(?:scripts?|скрипт\w*)\b", re.I)
NEGATED_SCRIPT = re.compile(
    # install-scope verbs only: "never run helpers from the installed directory" is the
    # correct rule and must stay allowed.
    r"\b(?:do not|don't|never)\s+(?:need|install|copy|include|ship|stage)\b"
    r"|\b(?:no need|need not|not needed|not required|unnecessary)\b"
    r"|\bwithout\b|\bomit\w*\b|\bskip\w*\b"
    r"|\bне\s+(?:нужн\w*|надо|требу\w*|став\w*|копир\w*|устанавлива\w*|включ\w*)\b"
    r"|\bнечего\b|\bбез\b",
    re.I,
)
CLAUSE = re.compile(r"[;.!?]+")

STAGING_TOKENS = {
    "docs/install.md": ("scripts/", ".pdca/scripts", "byte-identical", "pdca-executor"),
    "docs/ru/install.md": ("scripts/", ".pdca/scripts", "байт-в-байт", "pdca-executor"),
}
BYTE_IDENTICAL = {
    "docs/install.md": ("byte-identical",),
    "docs/ru/install.md": ("байт-в-байт", "идентичн"),
}


def read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


def scripts_excluded(sentence: str) -> bool:
    """True when a clause both names the helpers and tells the operator to leave them out."""
    for clause in CLAUSE.split(sentence):
        if SCRIPT_WORD.search(clause) and NEGATED_SCRIPT.search(clause):
            return True
    return False


def harmful_install_claim(sentence: str) -> bool:
    """True for install-scope prose that omits the runtime helpers the executor needs."""
    if scripts_excluded(sentence):
        return True
    low = sentence.lower()
    if "scripts" in low or "скрипт" in low:
        # The helpers are in scope, so `only …` is a legitimate qualifier
        # ("scripts only where the skill ships them").
        return False
    if not EXCLUSION.search(sentence):
        return False
    files_scope = "skill.md" in low and "assets" in low
    return bool(files_scope or SCOPE_DIRECTORY.search(sentence))


def fenced_blocks(text: str) -> list[str]:
    return re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.S)


def shell_lines(text: str) -> list[list[str]]:
    """Split fenced blocks into `shlex`-parsed commands, joining `\\` continuations."""
    out: list[list[str]] = []
    for block in fenced_blocks(text):
        joined = re.sub(r"\\\s*\n", " ", block)
        for line in joined.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                out.append(shlex.split(line))
            except ValueError:
                continue
    return out


def copy_commands(text: str) -> list[tuple[list[str], str]]:
    """`(sources, destination)` for every `cp -r … <dest>` in the doc's fenced blocks."""
    found: list[tuple[list[str], str]] = []
    for argv in shell_lines(text):
        if not argv or argv[0] != "cp" or "-r" not in argv[1:]:
            continue
        operands = [part for part in argv[1:] if not part.startswith("-")]
        if len(operands) < 2:
            continue
        found.append((operands[:-1], operands[-1]))
    return found


def expand_sources(sources: list[str]) -> set[str]:
    """Resolve explicit paths and `skills/pdca*` globs to shipped skill ids."""
    covered: set[str] = set()
    for source in sources:
        if any(char in source for char in "*?["):
            matches = REPO.glob(source)
        else:
            matches = [REPO / source]
        for match in matches:
            if (match / "SKILL.md").is_file():
                covered.add(match.name)
    return covered


def section(text: str, heading: str) -> str:
    """Slice from a `##` heading to the next `##` heading."""
    lines = text.splitlines()
    start = -1
    for index, line in enumerate(lines):
        if re.match(r"^##\s+" + re.escape(heading), line):
            start = index
            break
    if start == -1:
        return ""
    for index in range(start + 1, len(lines)):
        if re.match(r"^##\s+", lines[index]):
            return "\n".join(lines[start:index])
    return "\n".join(lines[start:])


def numbered_step(text: str, number: int, next_number: int) -> str:
    """Slice a prompt step (`<n>. Title` … up to the next numbered step)."""
    start = re.search(r"(?m)^%d\.\s" % number, text)
    if not start:
        return ""
    end = re.search(r"(?m)^%d\.\s" % next_number, text[start.start():])
    return text[start.start():start.start() + end.start()] if end else text[start.start():]


class CheckoutCommandTest(unittest.TestCase):
    def test_every_checkout_copy_command_covers_the_shipped_family(self) -> None:
        problems: list[str] = []
        commands = 0
        for rel in CHECKOUT_DOCS:
            for sources, dest in copy_commands(read(rel)):
                if not dest.rstrip("/").endswith("skills"):
                    continue
                commands += 1
                missing = sorted(set(SHIPPED) - expand_sources(sources))
                if missing:
                    problems.append(
                        "%s: cp to %s omits %s" % (rel, dest, ", ".join(missing))
                    )
        self.assertGreater(commands, 0, "no checkout copy command found in the docs")
        self.assertEqual([], problems, "\n".join(problems))

    def test_readme_explicit_install_list_covers_the_family(self) -> None:
        names = set()
        for block in fenced_blocks(read("README.md")):
            for line in block.splitlines():
                match = re.search(
                    r"npx\s+skills\s+add\s+\S+@([A-Za-z0-9._-]+)", line
                )
                if match:
                    names.add(match.group(1))
        self.assertTrue(names, "README has no explicit `npx skills add` list")
        self.assertEqual([], sorted(set(SHIPPED) - names), "README install list omits skills")


class RuntimeScriptsTest(unittest.TestCase):
    def test_install_docs_ship_scripts_and_stage_them_in_the_workspace(self) -> None:
        problems: list[str] = []
        for rel, tokens in STAGING_TOKENS.items():
            body = section(read(rel), "2.")
            if not body:
                problems.append("%s: §2 not found" % rel)
                continue
            low = body.lower()
            for token in tokens:
                if token.lower() not in low:
                    problems.append("%s §2: missing %r" % (rel, token))
            if not any(token.lower() in low for token in BYTE_IDENTICAL[rel]):
                problems.append(
                    "%s §2: helpers are not described as byte-identical copies" % rel
                )
            if not re.search(r"установленн|installed", low):
                problems.append(
                    "%s §2: the installed skill is not named as the helper source" % rel
                )
        self.assertEqual([], problems, "\n".join(problems))

    def test_install_docs_do_not_claim_scripts_are_not_needed(self) -> None:
        problems: list[str] = []
        for rel in INSTALL_FILES:
            for sentence in re.split(r"(?<=[.!?])\s+", norm(read(rel))):
                if harmful_install_claim(sentence):
                    problems.append(
                        "%s: scopes the install without scripts: %r" % (rel, sentence)
                    )
        self.assertEqual([], problems, "\n".join(problems))

    def test_install_scope_checker_on_known_prose(self) -> None:
        """Fixtures: the old doc prose and explicit helper exclusion must be caught."""
        harmful = (
            "Only `SKILL.md` and `assets/` travel; map the skills root to your host:",
            "Nothing else in the skill directory needs installing.",
            "Do not install scripts.",
            "scripts do not need installing",
            "omit scripts from the copied skill directory",
            "Переносятся только `SKILL.md` и `assets/`;",
            "Больше из каталога скилла ставить нечего.",
            "Не устанавливайте скрипты — они не нужны.",
            "Скрипты ставить не нужно.",
        )
        allowed = (
            "Install the whole skill directory: `SKILL.md`, `assets/`, and `scripts/` "
            "where the skill ships it.",
            "Copy `scripts/` only where the skill ships them.",
            "Ставьте каталог скилла целиком: `SKILL.md`, `assets/` и `scripts/`, "
            "если скилл их поставляет.",
            "`tests/` and the diagram generators under `assets/diagram/` are "
            "development-only and not needed at runtime.",
            "`tests/` и генераторы диаграмм в `assets/diagram/` нужны только для "
            "разработки, не для рантайма.",
            "Helpers under the installed skill's `scripts/` are the source of the runtime "
            "copies; a helper is never executed from the installed skill directory.",
            "Never run helpers from the installed `scripts/` directory; run the staged "
            "copies from `.pdca/scripts/`.",
        )
        for sentence in harmful:
            with self.subTest(harmful=sentence):
                self.assertTrue(harmful_install_claim(sentence), sentence)
        for sentence in allowed:
            with self.subTest(allowed=sentence):
                self.assertFalse(harmful_install_claim(sentence), sentence)

    def test_install_prompt_stages_helpers_from_installed_scripts(self) -> None:
        text = read("docs/install-prompt.md")
        intro = text.split("## Inputs", 1)[0]
        step = numbered_step(text, 1, 2)
        problems: list[str] = []
        if "scripts/" not in intro:
            problems.append("intro does not list scripts/ among the copied files")
        if not step:
            problems.append("step 1 (skills) not found")
        else:
            for token in ("scripts/", ".pdca/scripts", "pdca-executor"):
                if token not in step:
                    problems.append("step 1: missing %r" % token)
            if not re.search(r"байт-в-байт|идентичн", step):
                problems.append("step 1: helpers are not described as byte-identical copies")
            if not re.search(r"установленн", step):
                problems.append("step 1: the installed skill is not named as the helper source")
        self.assertEqual([], problems, "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
