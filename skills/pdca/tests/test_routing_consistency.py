"""Structural guards for the `pdca` skill: runner copies, asset sets, permissions.

The family ships the **same** dispatcher (`pdca-orchestrator`) in every skill, one role
set per package, and role assets that carry only a `# tier:` label — never a model id and
never a widened permission.  These are the source-side facts this module pins:

* five skills, five byte-identical runner copies;
* the asset set and tier of every package (base = six roles, the overlays add the
  security auditor, the forms ship only the runner);
* read-only roles stay read-only, the escalation `bash` allowlist stays inspection-only,
  and the executor stays the only role with `edit`/`bash`.

Host parity lives in the `opencode-config` repository.  The live host is **not** migrated to
the family architecture (it still ships the variant-routing orchestrator and the full-copy
role briefs), so every host-facing class is an explicit skip with that reason rather than a
silent pass.  Profile binding and the curated-skill list are migration-independent and stay
live.

Run:
    python3 -m unittest discover -s skills/pdca/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
FAMILY = SKILL_DIR.parent

BASE = SKILL_DIR / "SKILL.md"
FAMILY_SKILLS = ("pdca", "pdca-coder", "pdca-collection", "pdca-dotnet", "pdca-incremental")

ROLE_TIER = {
    "pdca-planner": "medium",
    "pdca-check": "medium",
    "pdca-escalate": "strong",
    "pdca-executor": "cheap",
    "pdca-scout": "cheap",
    "pdca-orchestrator": "cheap",
    "pdca-security-auditor": "medium",
}
# Asset set per package: the base owns the six roles; the overlays add the security
# auditor; the forms ship only the shared runner.
BASE_ASSETS = ("pdca-planner", "pdca-check", "pdca-escalate", "pdca-executor",
               "pdca-scout", "pdca-orchestrator")
OVERLAY_ASSETS = BASE_ASSETS + ("pdca-security-auditor",)
ASSET_SETS = {
    "pdca": BASE_ASSETS,
    "pdca-coder": OVERLAY_ASSETS,
    "pdca-dotnet": OVERLAY_ASSETS,
    "pdca-collection": ("pdca-orchestrator",),
    "pdca-incremental": ("pdca-orchestrator",),
}

# Roles that must never write. The executor is the only write-capable role.
READ_ONLY_ROLES = ("pdca-planner", "pdca-check", "pdca-escalate", "pdca-scout",
                   "pdca-security-auditor", "pdca-orchestrator")

# The dispatcher's subagent allowlist: the family roles plus the optional domain
# specialists the overlays select.
RUNNER_ALLOWLIST = {
    "pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate",
    "pdca-scout", "pdca-security-auditor", "docfx-specialist", "dotnet-*",
}

# Read-only git subcommands that may appear in an inspection allowlist.
GIT_INSPECTION = frozenset(
    ("status", "log", "diff", "show", "blame", "ls-files", "grep", "rev-parse", "branch")
)
INSPECTION_STEMS = frozenset(("cd", "ls", "cat", "sed", "head", "tail", "wc", "stat", "file"))
WRITE_STEMS = frozenset(
    ("build", "make", "test", "run", "pytest", "tox", "npm", "yarn", "pnpm", "cargo",
     "gradle", "mvn", "go", "python", "python3", "bash", "sh", "exec", "sudo", "install",
     "cp", "mv", "rm", "touch", "mkdir", "tee", "dd", "git")
)

# Host config lives in the `opencode-config` repo, not in this one.
HOST_REPO = Path(os.environ["OPENCODE_CONFIG_REPO"]) if os.environ.get("OPENCODE_CONFIG_REPO") else None
CONFIG = (HOST_REPO / "config") if HOST_REPO else None
HOST_AVAILABLE = bool(CONFIG) and CONFIG.is_dir()
SKIP_HOST = "host config not available — set OPENCODE_CONFIG_REPO=/path/to/opencode-config"
SKIP_HOST_NOT_MIGRATED = (
    "live host is not migrated to the family architecture (variant-routing orchestrator, "
    "full-copy role briefs); parity is re-enabled after deployment"
)



def host_not_migrated() -> bool:
    """True while the installed host still carries the retired variant-routing runner.

    The migration is observable in the host itself, so parity returns automatically once
    the host is redeployed — the skip is a fact, not a permanent exemption.
    """
    if not HOST_AVAILABLE:
        return False
    runner = HOST_DIR / "pdca-orchestrator.md"
    return runner.is_file() and "selected_variant" in read(runner)


HOST_DIR = (CONFIG / "agents") if CONFIG else None
PROFILES = (CONFIG / "profiles") if CONFIG else None
SKILLS_KEEP = (CONFIG / "skills-keep.txt") if CONFIG else None


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def norm(text: str) -> str:
    return " ".join(text.split())


def asset_path(skill: str, role: str) -> Path:
    return FAMILY / skill / "assets/opencode-agents" / ("%s.md" % role)


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


def permission(path: Path) -> dict:
    data = frontmatter(path)
    node = data.get("permission")
    if not isinstance(node, dict) or not node:
        raise AssertionError("%s: expected a non-empty `permission:` map" % path)
    return node


def tier_of(path: Path) -> str:
    match = re.search(r"^# tier: (\w+)$", read(path), re.M)
    return match.group(1) if match else ""


def load_jsonc(path: Path) -> dict:
    text = read(path)
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("//")]
    text = re.sub(r",(\s*[}\]])", r"\1", "\n".join(lines))
    return json.loads(text)


class RunnerAssetTest(unittest.TestCase):
    """One dispatcher, shipped identically in every package."""

    def test_runner_is_shipped_in_every_skill(self):
        for skill in FAMILY_SKILLS:
            with self.subTest(skill=skill):
                path = asset_path(skill, "pdca-orchestrator")
                self.assertTrue(path.is_file(), "%s: runner asset missing" % skill)
                self.assertEqual("pdca-orchestrator", frontmatter(path).get("name"))

    def test_runner_copies_are_byte_identical(self):
        copies = {s: asset_path(s, "pdca-orchestrator").read_bytes() for s in FAMILY_SKILLS}
        expected = copies["pdca"]
        for skill, body in copies.items():
            with self.subTest(skill=skill):
                self.assertEqual(expected, body, "%s: runner copy drifted" % skill)

    def test_runner_is_cheap_and_carries_no_model(self):
        raw = read(asset_path("pdca", "pdca-orchestrator"))
        self.assertRegex(raw, r"(?m)^# tier: cheap\s*$")
        self.assertNotRegex(raw, r"(?m)^\s*model\s*:")

    def test_runner_is_a_dispatcher_not_a_worker(self):
        perm = permission(asset_path("pdca", "pdca-orchestrator"))
        for action in ("edit", "write", "bash"):
            with self.subTest(action=action):
                self.assertEqual("deny", perm.get(action), "runner must not %s" % action)

    def test_runner_task_is_default_deny_with_the_family_allowlist(self):
        task = permission(asset_path("pdca", "pdca-orchestrator")).get("task")
        self.assertIsInstance(task, dict, "runner: no `task` map")
        self.assertEqual("deny", task.get("*"))
        allowed = {name for name, effect in task.items() if effect == "allow"}
        self.assertEqual(RUNNER_ALLOWLIST, allowed, "runner role allowlist drifted")

    def test_runner_never_reaches_general_or_explore(self):
        task = permission(asset_path("pdca", "pdca-orchestrator")).get("task", {})
        for agent in ("general", "explore"):
            with self.subTest(agent=agent):
                self.assertNotIn(agent, task)

    def test_runner_names_the_three_contexts(self):
        body = norm(read(asset_path("pdca", "pdca-orchestrator")))
        for context in ("cycle-control", "campaign-control", "collection"):
            with self.subTest(context=context):
                self.assertIn(context, body)
        self.assertNotIn("selected_variant", body)
        self.assertNotIn("execution_kind", body)


ENTRY_STAGE_RULES = (
    "form: UNDECIDED",
    "not a fourth context",
    "discriminators themselves",
    "same controller",
    "same pending PLAN",
    "collection owner",
    "one bounded choice probe",
    "bespoke checker",
)


def entry_stage_gaps(text: str) -> list:
    flat = norm(text).replace("`", "").replace("*", "")
    return [rule for rule in ENTRY_STAGE_RULES if rule not in flat]


class EntryStageTest(unittest.TestCase):
    """A fresh dispatch has one pre-decision stage before the existing contexts.

    Presence and mutation checks only: no model, agent or cycle is executed here.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(asset_path("pdca", "pdca-orchestrator"))
        cls.body = norm(cls.raw).replace("`", "").replace("*", "")

    def test_entry_stage_comes_before_the_three_contexts(self):
        self.assertIn("## Entry stage", self.raw)
        self.assertLess(self.raw.index("## Entry stage"),
                        self.raw.index("The same asset has three execution contexts"))
        self.assertIn("not a fourth context", self.body)

    def test_fresh_dispatch_is_form_undecided(self):
        self.assertIn("contract: pdca", self.body)
        self.assertIn("form: UNDECIDED", self.body)
        self.assertIn("one goal or deliverable does not make it form=cycle", self.body)
        self.assertIn("do not name cycle-control or campaign-control before the PLAN", self.body)

    def test_planner_brief_carries_the_discriminators_not_just_names(self):
        self.assertIn("base ### Forms discriminators themselves", self.body)
        self.assertIn("names alone are not a brief for a read-denied planner", self.body)
        for token in ("facts", "decision-relevant unknowns", "user-named form"):
            with self.subTest(token=token):
                self.assertIn(token, self.body)
        self.assertIn("a bare pdca is family entry only", self.body)

    def test_same_controller_adopts_the_decided_role(self):
        self.assertIn("same controller loads the decided contract and adopts the matching role",
                      self.body)
        self.assertIn("cycle-control", self.body)
        self.assertIn("campaign-control", self.body)
        self.assertIn("no new orchestrator", self.body)
        self.assertIn("no second planner call for routing", self.body)

    def test_a_chosen_collection_is_handed_back_to_the_primary_owner(self):
        for token in (
            "does not become the batch owner",
            "hands the existing initial batch plan by reference back to the existing cheap "
            "primary/collection owner",
            "loads pdca-collection and starts the per-item/lane machinery",
            "existing permissions",
            "not classification, a second batch PLAN",
            "task allowlist is not widened",
            "no self-delegation or recursion",
            "collection-lane stays the existing caller-dispatched lane",
            "batch-level ownership and lane duties stay distinct",
            "single-lane batch remains normal",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_runner_may_not_self_delegate_for_collection_ownership(self):
        task = permission(asset_path("pdca", "pdca-orchestrator"))["task"]
        self.assertNotIn("pdca-orchestrator", task)
        self.assertIn("no self-delegation or recursion", self.body)

    def test_entry_owned_plan_is_reused_by_reference_at_the_existing_gate(self):
        for token in (
            "The returned plan is the initial plan",
            "pdca-executor persists it by the existing rules",
            "continues at the current PLAN → DO gate",
            "Do not run Input 2's",
            "again for an entry-owned plan",
            "reuse it by reference and start at the current PLAN → DO gate",
            "named plan ref in the existing brief/status is enough",
            "no new state file, schema or counter",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_form_known_dispatch_without_a_plan_and_resume_are_distinguished(self):
        for token in (
            "form-known dispatch that genuinely has no plan of its own",
            "collection task's own PLAN",
            "persisted plan_handoff/resume is never re-planned",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_campaign_reuses_the_entry_choice_then_prepares_and_bootstraps(self):
        for token in (
            "campaign reuses the entry choice and first useful step",
            "pdca-executor persists the immutable preparation record and its preparation_ref",
            "clarify the same pending PLAN only if preparation fields are genuinely missing",
            "then baseline/runtime is bootstrapped before the first step DO",
            "initial PLAN is not duplicated",
            "approval/counters follow the incremental contract",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_fresh_entry_contract_taxonomy_is_base_only(self):
        for token in (
            "Fresh entry (form=UNDECIDED, no persisted plan)",
            "neither a cycle nor a campaign step contract",
            "no overlay is required yet",
            "Load the base pdca contract only",
            "post-decision exact contract loader uses the planner's returned form/overlay",
            "never a driver semantic choice",
            "fail closed if it is absent",
            "fail closed for that cycle/step",
            "do not pick a contract yourself",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_bounded_choice_probe_keeps_form_undecided_without_a_new_cycle(self):
        for token in (
            "authorization for one bounded choice probe",
            "open decision, observable outcomes and the evidence that closes it",
            "same planner refines the same pending PLAN",
            "form stays UNDECIDED until the planner chooses",
            "not an independent cycle",
            "creates no fresh controller",
            "adds no per-tool CHECK and no extra full PLAN",
            "waives no permission or approval",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_missing_rationale_goes_back_as_a_clarification(self):
        self.assertIn("naming the justified method and bounded volume", self.body)
        self.assertIn("clarify the same pending PLAN", self.body)
        self.assertIn("does not bump r/n", self.body)
        self.assertIn("never choose the form yourself", self.body)
        self.assertIn("not automatically incremental and not a STOP", self.body)
        self.assertIn("completeness clarification", self.body)

    def test_bespoke_checker_admission_is_presence_only(self):
        for token in (
            "bespoke checker",
            "concrete insufficiency reason and a bound",
            "return an incomplete pending PLAN to the same planner",
            "do not judge whether the checker is necessary",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.body)

    def test_existing_resume_and_collection_inputs_are_preserved(self):
        self.assertIn("Already-planned cycles (Input 2), resumes, collection lanes, campaign steps "
                      "and normal-mode approval keep their existing inputs and semantics", self.body)

    def test_entry_stage_guard_reacts_to_missing_markers(self):
        self.assertEqual([], entry_stage_gaps(self.raw))
        for old in (
            "`form: UNDECIDED`",
            "primary/collection owner",
            "one bounded choice probe",
            "**bespoke checker**",
        ):
            with self.subTest(mutation=old):
                sample = self.raw.replace(old, "")
                self.assertNotEqual([], entry_stage_gaps(sample))


class AssetSetTest(unittest.TestCase):
    def test_asset_set_and_tier_per_package(self):
        for skill, expected in ASSET_SETS.items():
            shipped = sorted(p.stem for p in (FAMILY / skill / "assets/opencode-agents").glob("*.md"))
            with self.subTest(skill=skill):
                self.assertEqual(sorted(expected), shipped)
                for role in expected:
                    self.assertEqual(ROLE_TIER[role], tier_of(asset_path(skill, role)),
                                     "%s/%s: tier drifted" % (skill, role))

    def test_no_asset_declares_a_model(self):
        for skill in FAMILY_SKILLS:
            for path in sorted((FAMILY / skill / "assets/opencode-agents").glob("*.md")):
                with self.subTest(asset=str(path.relative_to(FAMILY))):
                    self.assertNotRegex(read(path), r"(?m)^\s*model\s*:")

    def test_assets_keep_the_v1_permission_map(self):
        # V1 only understands `permission:`; V2 translates it. A V2-only `permissions:`
        # list would silently drop the restrictions on a V1 host.
        for skill in FAMILY_SKILLS:
            for path in sorted((FAMILY / skill / "assets/opencode-agents").glob("*.md")):
                data = frontmatter(path)
                with self.subTest(asset=str(path.relative_to(FAMILY))):
                    self.assertIn("permission", data)
                    self.assertNotIn("permissions", data)


class SourcePermissionBoundaryTest(unittest.TestCase):
    """No permission widening: the read-only roles stay read-only in every package."""

    def test_read_only_roles_never_grant_edit_or_write(self):
        for skill in FAMILY_SKILLS:
            for role in READ_ONLY_ROLES:
                path = asset_path(skill, role)
                if not path.is_file():
                    continue
                perm = permission(path)
                with self.subTest(skill=skill, role=role):
                    for action in ("edit", "write"):
                        self.assertNotEqual("allow", perm.get(action),
                                            "%s/%s must not grant `%s`" % (skill, role, action))

    def test_planner_is_default_deny(self):
        for skill in FAMILY_SKILLS:
            path = asset_path(skill, "pdca-planner")
            if not path.is_file():
                continue
            with self.subTest(skill=skill):
                self.assertEqual({"*": "deny"}, permission(path))

    def test_check_reads_only_the_cycle_evidence(self):
        # The common CHECK template is exactly the cycle state dir: no .NET/tool output
        # roots and no product source. Overlay copies are byte-identical, so none may
        # widen or narrow the shared template; a host adapter may narrow it separately.
        for skill in FAMILY_SKILLS:
            path = asset_path(skill, "pdca-check")
            if not path.is_file():
                continue
            perm = permission(path)
            with self.subTest(skill=skill):
                self.assertEqual("deny", perm.get("*"))
                for action in ("read", "glob", "list"):
                    node = perm.get(action)
                    self.assertIsInstance(node, dict, "check: no scoped `%s` map" % action)
                    allowed = {pattern for pattern, effect in node.items()
                               if effect == "allow"}
                    self.assertEqual({".pdca/**"}, allowed,
                                     "check: `%s` widens the generic evidence scope" % action)
                self.assertNotIn("bash", perm, "check must not run commands")

    def test_inspection_roles_keep_a_read_only_bash_allowlist(self):
        for skill in FAMILY_SKILLS:
            for role in ("pdca-escalate", "pdca-scout", "pdca-security-auditor"):
                path = asset_path(skill, role)
                if not path.is_file():
                    continue
                node = permission(path).get("bash")
                if not isinstance(node, dict):
                    continue
                with self.subTest(skill=skill, role=role):
                    self.assertEqual("deny", node.get("*"), "%s: bash must default to deny" % role)
                    for pattern, effect in node.items():
                        if effect != "allow" or pattern == "*":
                            continue
                        stem = pattern.split()[0].rstrip("*")
                        if stem == "git":
                            sub = pattern.split()[1].rstrip("*") if len(pattern.split()) > 1 else ""
                            self.assertIn(sub, GIT_INSPECTION,
                                          "`%s` is not a read-only git subcommand" % pattern)
                            continue
                        self.assertIn(stem, INSPECTION_STEMS,
                                      "`%s` is not an inspection command" % pattern)
                        self.assertNotIn(stem, WRITE_STEMS)

    def test_executor_is_the_only_writer(self):
        for skill in FAMILY_SKILLS:
            path = asset_path(skill, "pdca-executor")
            if not path.is_file():
                continue
            perm = permission(path)
            with self.subTest(skill=skill):
                self.assertEqual("allow", perm.get("edit"))
                self.assertEqual("allow", perm.get("bash"))


class SkillFrontmatterTest(unittest.TestCase):
    def test_base_frontmatter_name_is_pdca(self):
        text = read(BASE)
        end = text.find("\n---", 3)
        self.assertEqual("pdca", _parse_block(text[3:end]).get("name"))


@unittest.skipIf(host_not_migrated(), SKIP_HOST_NOT_MIGRATED)
@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class HostRoleParityTest(unittest.TestCase):
    """Host briefs vs the skill assets (blocked on the host migration)."""

    def test_four_host_agents_exist(self):
        for name in ("pdca-planner", "pdca-executor", "pdca-check", "pdca-escalate"):
            with self.subTest(role=name):
                self.assertTrue((HOST_DIR / ("%s.md" % name)).is_file())

    def test_host_briefs_carry_the_tier_and_no_model(self):
        for name, tier in ROLE_TIER.items():
            path = HOST_DIR / ("%s.md" % name)
            with self.subTest(role=name):
                if not path.is_file():
                    self.skipTest("%s not installed" % name)
                self.assertEqual(tier, tier_of(path))
                self.assertNotRegex(read(path), r"(?m)^\s*model\s*:")


@unittest.skipIf(host_not_migrated(), SKIP_HOST_NOT_MIGRATED)
@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class HostPermissionRoutingTest(unittest.TestCase):
    """Host-installed agents obey the same boundaries (blocked on the migration)."""

    def test_read_only_roles_stay_read_only(self):
        for role in READ_ONLY_ROLES:
            path = HOST_DIR / ("%s.md" % role)
            if not path.is_file():
                continue
            perm = permission(path)
            with self.subTest(role=role):
                for action in ("edit", "write"):
                    self.assertNotEqual("allow", perm.get(action))


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class ProfileBindingTest(unittest.TestCase):
    """Every role the family names is bound to a model by the host profiles."""

    BOUND = ("pdca-planner", "pdca-check", "pdca-escalate", "pdca-executor",
             "pdca-orchestrator")
    RETIRED = ("planner", "check", "escalate", "security-auditor")

    def test_both_profiles_bind_every_role(self):
        for profile in ("deepseek.jsonc", "gp.jsonc"):
            agents = load_jsonc(PROFILES / profile)["agent"]
            for role in self.BOUND:
                with self.subTest(profile=profile, role=role):
                    self.assertTrue((agents.get(role) or {}).get("model"),
                                    "%s: %s has no model" % (profile, role))

    def test_retired_bare_roles_have_no_binding_and_no_agent_file(self):
        for profile in ("deepseek.jsonc", "gp.jsonc"):
            agents = load_jsonc(PROFILES / profile)["agent"]
            for role in self.RETIRED:
                with self.subTest(profile=profile, role=role):
                    self.assertNotIn(role, agents)
                    self.assertFalse((HOST_DIR / ("%s.md" % role)).exists())


@unittest.skipUnless(HOST_AVAILABLE, SKIP_HOST)
class AdditiveIntegrationTest(unittest.TestCase):
    def test_family_skills_are_not_in_the_always_on_pack(self):
        lines = {
            ln.strip() for ln in read(SKILLS_KEEP).splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        }
        for name in FAMILY_SKILLS:
            with self.subTest(skill=name):
                self.assertNotIn(name, lines)


class RunnerMetadataBoundaryTest(unittest.TestCase):
    """The runner learns state from tool outputs and reads durable files only in scope."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = read(asset_path("pdca", "pdca-orchestrator"))
        cls.body = norm(cls.raw).lower()

    def test_runner_receives_metadata_from_tool_outputs(self):
        self.assertRegex(self.body, r"\btool outputs?\b")

    def test_runner_reads_durable_state_only_in_scope(self):
        self.assertTrue("scoped" in self.body or "host-permitted" in self.body,
                        "runner must bound durable reads to a scoped/host-permitted boundary")
        self.assertIn("read", self.body)

    def test_runner_does_not_search_the_workspace_or_shell_out(self):
        negations = re.compile(r"\b(?:never|not|no|cannot|don't)\b")
        for line in self.raw.splitlines():
            low = line.lower()
            flagged = [p for p in ("workspace discovery",) if p in low]
            if re.search(r"\b(?:rg|grep)\b", low):
                flagged.append("rg/grep")
            for phrase in flagged:
                with self.subTest(phrase=phrase, line=line):
                    self.assertRegex(low, negations,
                                     "runner must not instruct a workspace search: %r" % line)


if __name__ == "__main__":
    unittest.main()
