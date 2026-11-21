# PDCA handoff for OpenCode V2

Use this optional server plugin to send a ready plan to an existing executor without a separate model turn to record the plan, number the step or construct the dispatch. The executor and planner must already be working for the same driver in the same project directory.

Version 1 supports two autonomous boundaries: a pending bounded PLAN and the next campaign step after an accepted, completed ACT. Approval, classification, substantive work, independent CHECK, other phase transitions and collection scheduling use the existing skills.

## Enable it in a project

Use OpenCode V2 and Python 3 on a POSIX filesystem with `flock`, atomic rename and hard links. Install the matching `pdca` and `pdca-incremental` skill contracts. In the project's `opencode.jsonc`, add this directory to the existing `plugins` array:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["/ABSOLUTE/PATH/TO/skills/opencode/plugins/pdca-handoff"]
}
```

Replace `/ABSOLUTE/PATH/TO/skills` with your checkout. The executor needs permission to use `pdca_handoff_v1` and write its assigned PDCA files. The driver needs its existing permission to dispatch both roles. The plugin doesn't install agents or select models.

Start a **new** autonomous cycle or campaign. The executor elects the adapter when it creates the status. An existing manual campaign stays manual. Without the tool, the skills use their original writer and dispatch procedure. See the [driver handoff](../../../skills/pdca/references/driver.md#dispatch-transport) and the [executor procedure](../../../skills/pdca/references/act.md#optional-handoff).

## What survives a restart

The authoritative receipt is in the original `.pdca/status/*.md` file. The plugin pins the exact completed planner report under the assigned evidence directory, updates the status and counters in one atomic replacement, and queues the substantive DO brief. The plugin store indexes authorized tickets by location; it is not a second progress log. Repeating a delivery uses the same OpenCode inbox message ID. The planner's ordinary notification to its parent can still wake that parent.

The executor can `inspect` the ticket. `held` returns a pinned decision or an interruption reason. `pending` means the status was committed but delivery is unconfirmed. `delivered` means inbox admission, not performance or acceptance of the task. `recover` reconciles the same ticket. New instructions, a changed status, a changed pinned report or lost permission prevent automatic dispatch.

For a planned transfer to manual operation, release a waiting ticket before changing the writer election. After an unexpected removal, quiesce the old writer; inspect the checkpoint's `message`, `ref`, `counters` and `deliveryID` and compare them with the executor's inbox/history. For an admitted message, resume that work; never dispatch it again. Keep an unknown outcome open for reconciliation. This mechanism recovers its own planner handoff, not arbitrary background shell jobs.

## Reproduce the measurements

From this directory, run:

```sh
node --test test/handoff.test.js
python3 test/replay.py --runs 3
```

The first command needs Node.js 22+ and Python 3. The replay also needs `opencode` on `PATH`. It creates private OpenCode servers with temporary home, config and data directories, and a loopback-only scripted provider. Neither a production model nor a running PDCA session is used.

The control has no plugin. Its executor pins the report and records the transition in one tool call. Both lanes execute the same fixture, compare the product and check the complete normalized status. Normalization excludes the writer receipt, clock and content-addressed reference; each original report is verified separately. The replay prints role-specific provider calls, including the cost of arming before PLAN; parent notifications are counted separately. The interval is local test latency, not a prediction for a production campaign.

In three paired runs on OpenCode 2.3.2, the campaign opened step 4, cycle 8, revision 1, attempt 1 and produced `b,a` in both modes:

| Metric | Manual | Plugin |
| --- | ---: | ---: |
| Executor requests before the decision, including setup | 1 | 2 |
| Bookkeeping requests between the planner and substantive DO | 2 | 0 |
| Median time from the planner request to the substantive DO request | 422 ms | 293 ms |

The extra setup turn reduces the net saving in this fixture to one executor request. The parent still receives native OpenCode notifications. For a field measurement, count those requests separately and compare complete campaigns, including setup, checks, tool runtime and interruptions.
