"""Structural contract checks for exact-ID PDCA skill dependency preflight."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FAMILY = REPO / "skills"
BASE = FAMILY / "pdca" / "SKILL.md"
DRIVER = FAMILY / "pdca" / "references" / "driver.md"
PROMPT = FAMILY / "pdca" / "assets" / "install-skills-prompt.md"
OWNER_START = "#### Preflight — required skill contracts"
OWNER_END = "**The driver routes, it does not discover.**"

DIRECT_PARENTS = {
    "pdca": (),
    "pdca-coder": ("pdca",),
    "pdca-dotnet": ("pdca-coder",),
    "pdca-incremental": ("pdca",),
    "pdca-collection": ("pdca",),
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def owner_text() -> str:
    base = read(BASE)
    return " ".join(base.split(OWNER_START, 1)[1].split(OWNER_END, 1)[0].split())


def closure(selected: set[str]) -> set[str]:
    """Test oracle for the documented direct-parent table, including the entry base."""
    result = {"pdca"}
    pending = list(selected)
    while pending:
        contract = pending.pop()
        if contract in result:
            continue
        result.add(contract)
        pending.extend(DIRECT_PARENTS[contract])
    return result


class DependencyClosureTest(unittest.TestCase):
    def test_owner_declares_one_parent_table_matching_the_dependency_closure(self) -> None:
        owner = owner_text()
        self.assertIn("| Contract | Direct required parent |", owner)
        for contract, parents in DIRECT_PARENTS.items():
            parent_text = ", ".join(f"`{parent}`" for parent in parents) or "none"
            self.assertRegex(
                owner,
                rf"\|\s*`{re.escape(contract)}`\s*\|\s*{re.escape(parent_text)}\s*\|",
            )

    def test_current_selection_unions_form_and_overlay_closures_only(self) -> None:
        self.assertEqual({"pdca"}, closure({"pdca"}))  # ordinary non-coding
        self.assertEqual({"pdca", "pdca-coder"}, closure({"pdca-coder"}))
        self.assertEqual(
            {"pdca", "pdca-coder", "pdca-dotnet"},
            closure({"pdca-dotnet"}),  # .NET does not imply any optional form
        )
        self.assertEqual(
            {"pdca", "pdca-incremental", "pdca-coder"},
            closure({"pdca-incremental", "pdca-coder"}),
        )
        self.assertEqual(
            {"pdca", "pdca-incremental", "pdca-coder", "pdca-dotnet"},
            closure({"pdca-incremental", "pdca-dotnet"}),
        )
        self.assertEqual(
            {"pdca", "pdca-collection"},
            closure({"pdca-collection"}),
        )
        self.assertEqual(
            {"pdca", "pdca-collection", "pdca-incremental"},
            closure({"pdca-collection", "pdca-incremental"}),
        )
        self.assertEqual(
            {"pdca", "pdca-collection", "pdca-incremental", "pdca-coder", "pdca-dotnet"},
            closure({"pdca-collection", "pdca-incremental", "pdca-dotnet"}),
        )
        owner = owner_text()
        self.assertIn("only those selected contracts", owner)
        self.assertIn("driver derives the union of the transitive closures for only those selected contracts", owner)
        self.assertIn("only from the returned decision", owner)
        self.assertIn("requires `pdca-incremental` only when its selected item is a campaign", owner)
        self.assertIn("Each step's overlay is selected and checked for that step only", owner)
        self.assertIn("Never choose a simpler form or overlay", owner)

    def test_preflight_is_post_selection_and_precedes_dependent_actions(self) -> None:
        owner = owner_text()
        self.assertIn("Do not preflight future forms or overlays before PLAN", owner)
        self.assertIn("After each PLAN selects a form and any overlay", owner)
        self.assertIn("Immediately after selection, load each new required ID", owner)
        self.assertIn("dependent preparation, DO or work", owner)
        self.assertIn("Preserve the PLAN's selected form/overlay and pending state", owner)
        self.assertIn("resume that selection without reclassification or counter reset", owner)

    def test_only_a_successful_exact_id_load_satisfies_a_contract(self) -> None:
        owner = owner_text()
        self.assertIn("full content into the active context under that exact skill ID", owner)
        self.assertIn("An advertised-skill list, picker entry, CLI lock", owner)
        self.assertIn("registry membership", owner)
        self.assertIn("host loader is not assumed to enforce this gate", owner)
        self.assertIn("a hidden auto-selection flag does not make a successful exact-ID load unavailable", owner)
        self.assertIn("Reuse an unchanged dependency already loaded", owner)
        self.assertIn("not for every unit or CHECK", owner)

    def test_role_availability_does_not_replace_contract_preflight(self) -> None:
        base = read(BASE)
        owner = owner_text()
        self.assertIn("role preflight remains separate", owner)
        self.assertIn("A required unavailable role is a **resource blocker**", base)
        self.assertIn("An advertised-skill list", owner)


class FailureAndRecoveryTest(unittest.TestCase):
    def test_missing_and_denied_loads_fail_closed_with_distinct_recovery(self) -> None:
        owner = owner_text()
        self.assertIn("report the exact ID, what selected contract requires it", owner)
        self.assertIn("and the actual loader", owner)
        self.assertIn("A denied load is a **permission blocker**, not proof", owner)
        self.assertIn("do not retry through another loader, inspect installation paths", owner)
        self.assertIn("do not auto-install or reconstruct it", owner)
        self.assertIn("Do not omit the dependency or recreate its rules from memory", owner)

    def test_recovery_prompt_is_verbatim_narrow_and_uses_approved_workflow(self) -> None:
        owner = owner_text()
        prompt = read(PROMPT)
        for context_key in (
            "MISSING_SKILL_IDS=",
            "REQUIRED_BY=",
            "HOST_LOAD_FAILURE=",
        ):
            self.assertIn(context_key, prompt)
        self.assertIn("hand its fenced prompt to the user verbatim", owner)
        self.assertIn("filling only `Context`", owner)
        self.assertIn("https://github.com/AlexeyShirshov/skills", prompt)
        self.assertIn("approved install/deploy source-of-truth workflow", prompt)
        self.assertIn("Scope work to the listed missing IDs", prompt)
        self.assertIn("Do not auto-install, auto-deploy", prompt)
        self.assertIn("Do not run or resume the user's task", prompt)
        self.assertIn("permission denied/forbidden", prompt)
        self.assertIn("do not reinstall, try another loader or path", prompt)
        self.assertNotIn("npx", prompt)
        self.assertNotIn("~/.config/opencode", prompt)

    def test_filled_context_has_factual_values_and_preserves_the_static_prompt(self) -> None:
        prompt = read(PROMPT)
        before, tail = prompt.split("Context:\n", 1)
        context_template, suffix = tail.split("\n\nThe source of truth", 1)
        values = {
            "MISSING_SKILL_IDS": "pdca-coder",
            "REQUIRED_BY": "pdca-dotnet -> pdca-coder",
            "HOST_LOAD_FAILURE": "exact loader message unavailable (host reported NOT_FOUND)",
        }
        context = context_template
        for field, value in values.items():
            pattern = re.compile(rf"(?m)^  {field}=.*$")
            self.assertEqual(1, len(pattern.findall(context)), field)
            context = pattern.sub(f"  {field}={value}", context, count=1)

        self.assertNotRegex(context, r"<[^>\n]+>")
        for value in values.values():
            self.assertIn(value, context)
        filled = before + "Context:\n" + context + "\n\nThe source of truth" + suffix
        self.assertEqual(
            prompt.split("The source of truth", 1)[1],
            filled.split("The source of truth", 1)[1],
        )
        self.assertIn("Fill every Context field with observed facts", prompt)
        self.assertIn("exact loader message unavailable", prompt)
        self.assertIn("never invent a response or leave", prompt)

    def test_driver_authorizes_only_the_two_exact_recovery_prompt_reads(self) -> None:
        driver = read(DRIVER)
        self.assertIn("base §Preflight — required skill contracts owns", driver)
        self.assertRegex(
            driver,
            r"exact recovery prompt `assets/install-agents-prompt\.md` or "
            r"`assets/install-skills-prompt\.md`",
        )
        self.assertIn("only when its corresponding preflight fires", driver)
        self.assertIn("base directory its load result returns", driver)
        self.assertIn("never open an installation-path file", driver)


class DirectInvocationTest(unittest.TestCase):
    def test_every_leaf_loads_base_and_runs_its_preflight_before_work(self) -> None:
        for skill in ("pdca-coder", "pdca-dotnet", "pdca-incremental", "pdca-collection"):
            with self.subTest(skill=skill):
                text = " ".join(read(FAMILY / skill / "SKILL.md").split()).lower()
                self.assertIn("before applying work", text)
                self.assertIn("load base `pdca` by exact skill id", text)
                self.assertIn("§preflight — required skill contracts", text)
                self.assertIn("stop and report the exact id", text)
                self.assertIn("host loader's failure", text)
                self.assertIn("preflight owner is unavailable", text)
                self.assertIn("do not wait for that rule", text)

    def test_dotnet_direct_invocation_explicitly_loads_coder_by_id(self) -> None:
        dotnet = read(FAMILY / "pdca-dotnet" / "SKILL.md")
        self.assertIn("explicitly load `pdca-coder` by exact skill ID", dotnet)
        self.assertIn("does not prove its contract is loaded", dotnet)

    def test_collection_preflight_does_not_require_unselected_campaigns(self) -> None:
        collection = read(FAMILY / "pdca-collection" / "SKILL.md")
        self.assertIn("only the currently selected collection closure", collection)
        self.assertIn("add `pdca-incremental` after an item is selected as a campaign", collection)
        self.assertIn("never as a pre-PLAN all-forms gate", collection)
        self.assertIn("This does not replace the independent role preflight", collection)


if __name__ == "__main__":
    unittest.main()
