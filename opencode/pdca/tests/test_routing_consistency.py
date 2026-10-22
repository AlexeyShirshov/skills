"""Static routing/structure guards for the universal `pdca` skill.

Structural only: these tests parse the role frontmatter/permission blocks, the
host profiles, the curated-skill list and AGENTS.md; they never execute a model
or the live cycle.

They prove: the four host roles exist, carry only a `# tier:` label (never a
`model:` field), keep the intended narrow permissions, and match the
`pdca-dotnet` asset mirror byte-for-byte (the universal skill's own assets are
domain-neutral on purpose); the profiles bind every surviving role — the `pdca-*`
family and the host keys that still exist — to a model; the shared RUNNER
`pdca-orchestrator` is asserted separately; the integration is additive.

Run:
    python3 -m unittest discover -s opencode/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

SKILL = SKILL_DIR / "SKILL.md"
ASSET_AGENTS = SKILL_DIR / "assets/agents"
# The host `pdca-*` agents are the .NET-flavoured briefs, and the universal
# skill's own assets are domain-neutral, so host body/permission parity is
# asserted against `pdca-dotnet`'s assets (the mirror of the host briefs).
HOST_ASSETS = REPO_ROOT / "opencode/pdca-dotnet/assets/agents"

# Host config (agents/profiles/AGENTS.md/skills-keep) lives in the `opencode-config` repo,
# not in this one. Point at it with OPENCODE_CONFIG_REPO to enable host-parity checks;
# they skip by default.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"

HOST_DIR = (CONFIG / "agents") if CONFIG else None
PROFILES = (CONFIG / "profiles") if CONFIG else None
SKILLS_KEEP = (CONFIG / "skills-keep.txt") if CONFIG else None
AGENTS_MD = (CONFIG / "AGENTS.md") if CONFIG else None
ORCHESTRATOR = (CONFIG / "agents/pdca-orchestrator.md") if CONFIG else None

ROLE_TIER = {
    "pdca-planner": "medium",
    "pdca-check": "medium",
    "pdca-escalate": "strong",
    "pdca-executor": "cheap",
}
# The skill also ships the shared gatherer (`pdca-scout`) and the runner
# (`pdca-orchestrator`) as portable assets, both on the cheap tier.
ASSET_TIER = dict(ROLE_TIER, **{"pdca-scout": "cheap", "pdca-orchestrator": "cheap"})

# The `pdca-*` roles bind their models directly in the profiles. The bare host
# aliases (`planner`, `check`, `escalate`, `security-auditor`) were retired: no
# agent file and no profile key may bring them back.
HOST_ROLES = ("architect", "coder", "scout", "pdca-orchestrator")
BOUND_ROLES = tuple(ROLE_TIER) + HOST_ROLES
# The host copy of the shared gatherer/implementer is spelled `scout`/`coder`;
# the skill ships them prefixed. Host/asset comparisons normalise both sides.
ALIASES = {"scout": "pdca-scout", "coder": "pdca-executor"}
DEAD_HOST_ROLES = ("planner", "check", "escalate", "security-auditor")


def canon(text: str) -> str:
    """Rename bare host role names to the prefixed asset names (idempotent)."""
    for bare, prefixed in ALIASES.items():
        text = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(bare), prefixed, text)
    return text


def canon_resources(resources: set) -> set:
    return {canon(res) for res in resources}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


def _parse_block(block: str) -> dict:
    """Tiny indentation parser for the flat/nested frontmatter subset used here."""
    root: dict = {}
    stack: list = [(-1, root)]
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, val = raw.strip().partition(":")
        key = key.strip().strip('"').strip("'")
        val = val.strip().strip('"').strip("'")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if val == "":
            stack[-1][1][key] = {}
            stack.append((indent, stack[-1][1][key]))
        else:
            stack[-1][1][key] = val
    return root


def frontmatter(path: Path) -> dict:
    text = read(path)
    if not text.startswith("---"):
        raise AssertionError("%s: no frontmatter" % path)
    end = text.find("\n---", 3)
    return _parse_block(text[3:end])


def load_jsonc(path: Path) -> dict:
    text = read(path)
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("//")]
    text = re.sub(r",(\s*[}\]])", r"\1", "\n".join(lines))
    return json.loads(text)


def _matches(pattern: str, value: str) -> bool:
    """Whole-value wildcard: `*` = any run, `?` = one character."""
    regex = "".join(
        ".*" if ch == "*" else "." if ch == "?" else re.escape(ch) for ch in pattern)
    flags = re.IGNORECASE if os.name == "nt" else 0
    return re.fullmatch(regex, value, flags | re.DOTALL) is not None


# Published skill assets stay V1-compatible: V1 knows only `permission:`, while
# V2 translates that legacy frontmatter automatically. The host role briefs are
# their canonical source, so they stay V1 too (only host-only primaries such as
# `architect` use native V2 `permissions:`).
V1_ACTION = {"subagent": "task", "shell": "bash"}


def legacy_permission(path: Path) -> dict:
    data = frontmatter(path)
    node = data.get("permission")
    if not isinstance(node, dict) or not node:
        raise AssertionError("%s: expected a non-empty V1 `permission:` map" % path)
    return node


def legacy_effective(perm: dict, action: str, resource: str) -> str:
    node = perm.get(V1_ACTION.get(action, action))
    if node is None:
        node = perm.get("*")
    if node is None:
        return "allow"
    if isinstance(node, str):
        return node
    effect = "ask"
    for pattern, value in node.items():
        if _matches(pattern, resource):
            effect = value
    return effect


def legacy_allowed(perm: dict, action: str) -> set:
    node = perm.get(V1_ACTION.get(action, action))
    if isinstance(node, str):
        return {"*"} if node == "allow" else set()
    if not isinstance(node, dict):
        return set()
    return {res for res in node if legacy_effective(perm, action, res) == "allow"}


class RoleParityTest(unittest.TestCase):
    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_four_host_agents_exist(self):
        for name in ROLE_TIER:
            with self.subTest(role=name):
                self.assertTrue((HOST_DIR / ("%s.md" % name)).is_file())

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_host_agent_identity_is_the_filename_stem(self):
        # V2 identifies an agent by its file name; a legacy `name:` is allowed only
        # when it agrees with the stem.
        for name in ROLE_TIER:
            with self.subTest(role=name):
                path = HOST_DIR / ("%s.md" % name)
                self.assertTrue(path.is_file())
                self.assertEqual(name, path.stem)
                self.assertEqual(name, frontmatter(path).get("name", name))

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_each_role_carries_expected_tier_and_no_model(self):
        for name, tier in ROLE_TIER.items():
            with self.subTest(role=name):
                raw = read(HOST_DIR / ("%s.md" % name))
                self.assertRegex(raw, r"(?m)^# tier: %s\s*$" % tier)
                self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    def test_assets_are_the_roles_plus_gatherer_and_runner(self):
        assets = sorted(p.name for p in ASSET_AGENTS.glob("*.md"))
        expected = sorted("%s.md" % n for n in ASSET_TIER)
        self.assertEqual(expected, assets)

    def test_each_asset_carries_expected_tier_and_no_model(self):
        for name, tier in ASSET_TIER.items():
            with self.subTest(role=name):
                path = ASSET_AGENTS / ("%s.md" % name)
                self.assertTrue(path.is_file(), "%s missing" % name)
                self.assertEqual(name, frontmatter(path).get("name"))
                raw = read(path)
                self.assertRegex(raw, r"(?m)^# tier: %s\s*$" % tier)
                self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    def test_asset_agents_keep_v1_permission_map_for_compat(self):
        # V1 only understands `permission:`; V2 translates it automatically. A
        # V2-only `permissions:` list would silently drop restrictions in V1.
        for name in ASSET_TIER:
            path = ASSET_AGENTS / ("%s.md" % name)
            data = frontmatter(path)
            with self.subTest(role=name):
                self.assertIn("permission", data)
                self.assertNotIn("permissions", data)
                self.assertTrue(legacy_permission(path))

    @unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
    def test_host_briefs_match_dotnet_assets_except_external_directory(self):
        # The host role briefs are canonical for the .NET-flavoured text; the
        # `pdca-dotnet` assets mirror them. The universal skill's own assets are
        # domain-neutral on purpose and are not compared here. The mirror must not
        # carry the host-specific `external_directory` (local-env paths).
        for name in ROLE_TIER:
            with self.subTest(role=name):
                host = read(HOST_DIR / ("%s.md" % name))
                asset = read(HOST_ASSETS / ("%s.md" % name))
                self.assertEqual(
                    canon(host.split("\n---\n", 1)[1]),
                    canon(asset.split("\n---\n", 1)[1]),
                    "%s host/asset body differ" % name,
                )
                # Both sides are V1 `permission:` maps: the published assets must
                # run on V1, so the host briefs stay V1 too.
                hperm = legacy_permission(HOST_DIR / ("%s.md" % name))
                aperm = legacy_permission(HOST_ASSETS / ("%s.md" % name))
                self.assertNotIn(
                    "external_directory", aperm,
                    "%s: portable asset must not carry host external_directory rules" % name,
                )
                self.assertEqual(
                    legacy_effective(hperm, "*", "*"),
                    legacy_effective(aperm, "*", "*"),
                    "%s host/asset default deny differ" % name,
                )
                for action in ("read", "glob", "shell", "subagent", "skill", "question"):
                    with self.subTest(role=name, action=action):
                        self.assertEqual(
                            canon_resources(legacy_allowed(hperm, action)),
                            canon_resources(legacy_allowed(aperm, action)),
                            "%s: %s allowlist differs host vs asset" % (name, action),
                        )


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class PermissionRoutingTest(unittest.TestCase):
    def test_planner_and_check_are_default_deny(self):
        for name in ("pdca-planner", "pdca-check"):
            with self.subTest(role=name):
                perm = legacy_permission(HOST_DIR / ("%s.md" % name))
                self.assertEqual("deny", legacy_effective(perm, "*", "*"))

    def test_escalate_only_allows_scout(self):
        perm = legacy_permission(HOST_DIR / "pdca-escalate.md")
        self.assertEqual("deny", legacy_effective(perm, "subagent", "*"))
        self.assertEqual({"pdca-scout"}, canon_resources(legacy_allowed(perm, "subagent")))


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class ProfileBindingTest(unittest.TestCase):
    def test_deepseek_roles_keep_a_model(self):
        agents = load_jsonc(PROFILES / "deepseek.jsonc")["agent"]
        for role in BOUND_ROLES:
            with self.subTest(role=role):
                self.assertTrue((agents.get(role) or {}).get("model"), "%s has no model" % role)

    def test_gp_roles_keep_a_model(self):
        agents = load_jsonc(PROFILES / "gp.jsonc")["agent"]
        for role in BOUND_ROLES:
            with self.subTest(role=role):
                self.assertTrue((agents.get(role) or {}).get("model"), "%s has no model" % role)

    def test_retired_bare_roles_have_no_binding_and_no_agent_file(self):
        for profile in ("deepseek.jsonc", "gp.jsonc"):
            agents = load_jsonc(PROFILES / profile)["agent"]
            for role in DEAD_HOST_ROLES:
                with self.subTest(profile=profile, role=role):
                    self.assertNotIn(role, agents, "%s still binds %s" % (profile, role))
                    self.assertFalse(
                        (HOST_DIR / ("%s.md" % role)).exists(),
                        "config/agents/%s.md must stay deleted" % role,
                    )


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class AdditiveIntegrationTest(unittest.TestCase):
    def test_cycle_skills_are_not_in_the_always_on_pack(self):
        # The cycle skills live in the global skills dir and are loaded by name/trigger;
        # the curated always-on pack must not spend context on them.
        lines = {
            ln.strip() for ln in read(SKILLS_KEEP).splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        }
        for name in ("pdca", "pdca-coder", "pdca-dotnet"):
            with self.subTest(skill=name):
                self.assertNotIn(name, lines)

    def test_agents_md_points_to_the_entry_without_a_phrase_table(self):
        text = read(AGENTS_MD)
        self.assertIn("pdca-entry", text)
        self.assertIn("skill pdca", text)
        self.assertNotIn("Trigger phrases", text)
        self.assertNotIn("-> `pdca-coder`", text)
        self.assertNotIn("picks the cycle variant", text)


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class OrchestratorVariantSelectionTest(unittest.TestCase):
    """The shared cheap driver obeys the contract named by the dispatching skill."""

    UNIVERSAL_ROLES = ("pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate")

    def test_orchestrator_exists(self):
        self.assertTrue(ORCHESTRATOR.is_file())

    def test_orchestrator_subagent_allowlist_covers_universal_roles(self):
        perm = legacy_permission(ORCHESTRATOR)
        self.assertEqual("deny", legacy_effective(perm, "subagent", "*"))
        allowed = legacy_allowed(perm, "subagent")
        for role in self.UNIVERSAL_ROLES:
            with self.subTest(role=role):
                self.assertIn(role, allowed)


class SkillFrontmatterTest(unittest.TestCase):
    def test_skill_frontmatter_name_is_pdca(self):
        text = read(SKILL)
        end = text.find("\n---", 3)
        data = _parse_block(text[3:end])
        self.assertEqual("pdca", data.get("name"))


RUNNER_ASSET = ASSET_AGENTS / "pdca-orchestrator.md"
FAMILY_SKILLS = ("pdca-entry", "pdca", "pdca-coder", "pdca-dotnet", "pdca-collection", "pdca-incremental")
# Repo root: <repo>/opencode/pdca/tests/<this file>.
REPO_ROOT = Path(__file__).resolve().parents[3]


class RunnerMetadataBoundaryTest(unittest.TestCase):
    """The runner learns state from tool outputs and reads durable files only in scope."""

    @staticmethod
    def _body() -> str:
        return norm(read(RUNNER_ASSET)).lower()

    def test_runner_receives_metadata_from_tool_outputs(self):
        self.assertRegex(self._body(), r"\btool outputs?\b")

    def test_runner_reads_durable_state_only_in_scope(self):
        text = self._body()
        self.assertTrue(
            "scoped" in text or "host-permitted" in text,
            "runner must bound durable reads to a scoped/host-permitted boundary",
        )
        self.assertIn("read", text)

    def test_runner_does_not_search_the_workspace_or_shell_out(self):
        negations = re.compile(r"\b(?:never|not|no|cannot|don't)\b")
        for line in read(RUNNER_ASSET).splitlines():
            low = line.lower()
            flagged = [p for p in ("workspace discovery",) if p in low]
            if re.search(r"\b(?:rg|grep)\b", low):
                flagged.append("rg/grep")
            for phrase in flagged:
                with self.subTest(phrase=phrase, line=line):
                    self.assertRegex(
                        low, negations,
                        "runner must not instruct a workspace search or a shell grep: %r" % line,
                    )


class RunnerAssetTest(unittest.TestCase):
    """The runner ships as a portable asset in every skill of the family."""

    def test_runner_asset_is_shipped_here(self):
        self.assertTrue(RUNNER_ASSET.is_file(), "assets/agents/pdca-orchestrator.md missing")
        data = frontmatter(RUNNER_ASSET)
        self.assertEqual("pdca-orchestrator", data.get("name"))
        self.assertEqual("subagent", data.get("mode"))

    def test_runner_is_cheap_and_carries_no_model(self):
        raw = read(RUNNER_ASSET)
        self.assertRegex(raw, r"(?m)^# tier: cheap\s*$")
        self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    def test_runner_is_a_dispatcher_not_a_worker(self):
        perm = legacy_permission(RUNNER_ASSET)
        self.assertEqual("deny", perm.get("edit"), "runner must not edit")
        self.assertEqual("deny", perm.get("bash"), "runner must not run commands")
        self.assertEqual("deny", perm.get("write"))
        self.assertEqual("deny", perm["task"].get("*"))

    def test_runner_dispatches_the_family_roles(self):
        perm = legacy_permission(RUNNER_ASSET)
        allowed = {k for k, v in perm["task"].items() if v == "allow"}
        self.assertEqual(
            {"pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate",
             "pdca-scout", "pdca-security-auditor", "docfx-specialist", "dotnet-*"},
            allowed,
        )

    def test_runner_asset_is_identical_in_every_skill(self):
        copies = {s: (REPO_ROOT / "opencode" / s / "assets/agents/pdca-orchestrator.md")
                  for s in FAMILY_SKILLS}
        expected = copies["pdca"].read_bytes()
        for skill, path in copies.items():
            with self.subTest(skill=skill):
                self.assertTrue(path.is_file(), "%s: runner asset missing" % skill)
                self.assertEqual(expected, path.read_bytes(), "%s: runner copy drifted" % skill)


if __name__ == "__main__":
    unittest.main()
