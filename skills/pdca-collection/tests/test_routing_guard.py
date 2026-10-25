"""Collection is a batch of independent goals, not a parallelism-only contract.

The base `pdca` PLAN decides the **collection form** and hands its plan to this
contract; the collection then classifies **each item** into the form `cycle` or
`campaign` (contract `pdca` + overlay `none | coder | coder+.NET`) with the same
configured planner. Parallelism is an execution mode: with one group or `cap = 1`
the collection degrades to a single sequential lane instead of changing
contracts. These guards pin that boundary so the "≥2 disjoint footprints" rule is
not misread as an entry condition, and so the removed router (`execution_kind` /
`selected_variant`) cannot come back.

Run:
    python3 -m unittest discover -s skills/pdca-collection/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_DIR.parent
SKILL = SKILL_DIR / "SKILL.md"
STATUS_REF = SKILL_DIR / "references/status.md"
LANE_REF = SKILL_DIR / "references/lane.md"
BASE = SKILLS_ROOT / "pdca/SKILL.md"
INCREMENTAL = SKILLS_ROOT / "pdca-incremental/SKILL.md"

# The host truncates tool output at 50 KiB / 2000 lines: every contract must stay below it.
HOST_LIMIT_BYTES = 50 * 1024
HOST_LIMIT_LINES = 2000


def _plain(text: str) -> str:
    return " ".join(text.replace("**", "").replace("`", "").split())


class RoutingGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = SKILL.read_text(encoding="utf-8")
        self.text = " ".join(self.raw.split())

    def test_parallelism_is_not_an_entry_condition(self):
        self.assertIn("Parallelism is not an entry condition", self.text)

    def test_one_group_or_cap_one_degrades_to_a_single_lane(self):
        self.assertIn("cap = 1", self.text)
        self.assertIn("degradation to a single lane", self.text)
        self.assertIn("Do not create fake groups", self.text)

    def test_reservation_covers_the_whole_item(self):
        # A resource reservation is taken for the whole item and serialized; it is
        # never narrowed to the first steps. (The section moved to references/lane.md.)
        lane = _plain(LANE_REF.read_text(encoding="utf-8"))
        for stem in ("reservation", "whole item", "serializ", "disjoint"):
            with self.subTest(stem=stem):
                self.assertIn(
                    stem, lane,
                    f"references/lane.md lacks the reservation stem {stem!r}",
                )
        for line in LANE_REF.read_text(encoding="utf-8").splitlines():
            with self.subTest(line=line.strip()[:80]):
                self.assertIsNone(
                    re.search(r"(?i)(only|just).{0,40}first.{0,20}step", line),
                    "references/lane.md must not allow reserving only the first steps: "
                    f"{line!r}",
                )

    def test_reservation_is_renegotiated_before_any_recluster(self):
        lane = _plain(LANE_REF.read_text(encoding="utf-8"))
        for stem in ("renegotiat", "surface"):
            with self.subTest(stem=stem):
                self.assertIn(
                    stem, lane,
                    f"references/lane.md lacks the boundary stem {stem!r}",
                )
        low = lane.lower()
        self.assertIn("recluster", low,
                      "references/lane.md lost the no-recluster token")
        self.assertIn("reservation", low,
                      "reservation and recluster must be stated together")


class BatchFormGuardTest(unittest.TestCase):
    """The restructured batch vocabulary: item form, not a routing field."""

    FILES = (SKILL, STATUS_REF, LANE_REF, BASE, INCREMENTAL)

    def setUp(self) -> None:
        self.raw = SKILL.read_text(encoding="utf-8")
        self.text = _plain(self.raw)

    def test_the_collection_names_the_decided_batch_form(self):
        self.assertIn(
            "its single PLAN decided the collection form", self.text,
            "the collection must name the base decision it executes",
        )
        self.assertIn("does not classify the batch", self.text)
        self.assertIn("no routing table of its own", self.text)

    def test_each_item_has_a_form_not_a_variant(self):
        items = _plain(self.raw.split("## Items:", 1)[1].split("## Collection", 1)[0])
        role = _plain(self.raw.split("## Role", 1)[1].split("## Ownership", 1)[0])
        self.assertTrue(
            "Every item has a form, decided by the collection PLAN" in items,
            "the bare vocabulary must live in §Items",
        )
        for token in ("one cycle of the chosen contract+overlay", "one incremental campaign"):
            with self.subTest(token=token):
                self.assertTrue(token in items, f"§Items lost {token!r}")
        self.assertTrue("no contract/overlay" in items, "§Items must deny a campaign-level contract")
        self.assertTrue("the contract is pdca plus the overlay" in role, "§Role lost the contract naming")
        for value in ("none", "coder", "coder+.NET"):
            with self.subTest(value=value):
                self.assertTrue(value in role, f"§Role lost the overlay value {value!r}")

    def test_no_legacy_routing_fields_anywhere_in_the_family(self):
        for path in (SKILL, STATUS_REF, LANE_REF):
            with self.subTest(path=str(path)):
                raw = path.read_text(encoding="utf-8")
                self.assertNotIn("execution_kind", raw)
                self.assertNotIn("selected_variant", raw)

    def test_campaign_ownership_is_the_existing_cheap_orchestrator(self):
        ownership = _plain(
            self.raw.split("## Ownership", 1)[1].split("## Items", 1)[0]
        )
        self.assertIn("one designated existing cheap pdca-orchestrator", ownership)
        self.assertIn("campaign-control", ownership)
        self.assertIn("No competing writers", ownership)
        self.assertIn("the collection owner never writes or advances a campaign", ownership)
        self.assertIn("it is the only writer of that record", ownership)

    def test_a_cycle_item_is_cycle_control_and_does_not_advance_the_campaign(self):
        ownership = _plain(self.raw.split("## Ownership", 1)[1].split("## Items", 1)[0])
        self.assertTrue(
            "An item with the form cycle is executed by the same cheap dispatcher in cycle-control"
            in ownership,
            "§Ownership must route a cycle item to cycle-control",
        )
        self.assertTrue(
            "it does not advance the campaign, the queue or anything else" in ownership,
            "a cycle item must not advance the campaign or the queue",
        )

    def test_a_campaign_item_delegates_its_step_semantics(self):
        items = _plain(self.raw.split("## Items:", 1)[1].split("## Collection", 1)[0])
        for token in (
            "one planner call per step boundary",
            "an accepted negative candidate credited as knowledge",
            "no forced second increment",
            "a whole-goal final check before `done`".replace("`", ""),
            "the claims veto",
        ):
            with self.subTest(token=token):
                self.assertIn(token, items)
        # delegated, not restated: the incremental contract owns them
        self.assertIn("../pdca-incremental/SKILL.md", items)

    def test_one_increment_may_close_a_campaign_item(self):
        # the batch must not demand a second step once the whole goal is checked
        incremental = _plain(INCREMENTAL.read_text(encoding="utf-8"))
        self.assertIn(
            "one increment that satisfies the goal and passes the check ends the campaign",
            incremental,
        )
        self.assertIn("no rule demands a second increment", incremental)
        self.assertIn("The only success of a campaign item is an accepted `met`".replace("`", ""), self.text)

    def test_readiness_is_not_completion(self):
        self.assertIn("Readiness ≠ completion", self.text)
        self.assertIn("barrier-ready", self.text)
        self.assertIn("the item stays `pending` and never `done`".replace("`", ""), self.text)

    def test_every_contract_stays_under_the_host_limit(self):
        for path in self.FILES:
            with self.subTest(path=str(path)):
                raw = path.read_bytes()
                self.assertLess(
                    len(raw), HOST_LIMIT_BYTES,
                    f"{path} is {len(raw)} bytes, over the {HOST_LIMIT_BYTES}-byte host limit",
                )
                self.assertLess(
                    len(raw.decode("utf-8").splitlines()), HOST_LIMIT_LINES,
                    f"{path} is over the {HOST_LIMIT_LINES}-line host limit",
                )


if __name__ == "__main__":
    unittest.main()
