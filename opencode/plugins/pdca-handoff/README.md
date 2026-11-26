# PDCA handoff for OpenCode V2

Use this optional server plugin when your PDCA agents spend model turns moving results
between roles rather than deciding or doing the work. The plugin handles those transfers
and records their state. You can run the same PDCA skills without it.

## What the plugin does

For example, in an autonomous bug-fix cycle, the planner finishes the plan, the executor fixes
the bug, and an independent checker reviews the evidence. With the plugin, OpenCode can handle
these steps between the agents' substantive turns:

- **Send a finished plan to the executor.** At an authorized autonomous boundary, save the original
  plan, record PLAN → DO, and queue the DO brief for the existing executor. The planner and
  executor must already work for the same driver in the same project directory. This also works
  for the next campaign step after a completed, accepted ACT.
- **Prepare and deliver CHECK evidence.** Verify the declared inputs and access, pin the packet,
  and, when configured, send it to the assigned checker. Delivery doesn't mean acceptance.
- **Record phase decisions.** Save the producer's exact report and apply supported status
  transitions. With tracked CHECK delivery, record the verdict without a separate executor turn.
- **Track a background command.** Reconcile an already launched and registered job after a restart.
  If its outcome is unknown, keep it unknown rather than treating it as success or rerunning the job.

The plugin doesn't write the plan, do the work, or judge the result. It doesn't change approval
requirements or schedule collection items. Read the [Russian user guide](../../../docs/ru/guide/pdca-handoff.md)
for an overview of when to use it.

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

### Choose operations independently

New skills use only the tool names the host actually offers. The 0.1 plugin continues to handle PLAN → DO only. Upgrading the plugin doesn't transfer ownership of an existing status file. The following 0.2 capabilities are on by default where supported; to offer a subset, use a plugin config entry with `options.capabilities`, for example `["packet-v1", "events-v1"]`. An empty list leaves the original handoff tool alone.

| Capability | What the adapter does | What remains a decision |
| --- | --- | --- |
| `packet-v1` | Checks the pinned transport recipe, declared candidate inputs, command receipts, observation/log hashes and checker read permissions. Includes the installed CHECK contract and selected sections. Pins and optionally delivers the packet by a stable inbox ID. | Which inputs are required and what their evidence proves. |
| `events-v1` | Records the original phase report, projects the supported phase/counter change and appends a single keyed row to the shared log. With tracked delivery it captures the checker's exact decision without another executor turn. | The plan, verdict, and whether a revision is substantive. |
| `wait-v1` | Tracks a registered executor shell. Native completion wakes the executor once; after restart, a matching live Linux process remains running. Lost process identity without a terminal receipt means **unknown**, not success. | Whether to fix a failure or authorize a new run. |

See the [adapter contract](../../../skills/pdca/references/adapters.md) for the wire formats, election fields and manual takeover. Registration requires the host-issued background handle in the same executor's history. The plugin does not rerun a lost command.

### Track follow-ups to existing subagents

Managed dispatch is on by default on supported hosts. If you set `options.capabilities`, include
`"dispatch-v1"` to keep it. Set `options.managedDispatch` to `true` or `false` to override that list
for managed dispatch.

Confirm that `pdca_dispatch_v1` appears for your driver. It sends a follow-up to an existing direct
PDCA child. Keep the existing route for initial dispatch, CHECK, and handoffs with their own adapter
or final report marker. When the tool is available to an OpenCode orchestrator, the plugin points
it to the current dispatch instructions, including in resumed sessions. Existing in-flight work
is not enrolled.

For each managed follow-up, the plugin records the prompt ID before submission. It checks the
child's saved result on completion, after a restart, and at the dispatch deadline (10 minutes by
default). It delivers the marked final report under one stable inbox ID. The native report stays
in OpenCode history but the driver receives only the managed copy as a routing input. If no final
report is available at the deadline, the plugin reports `unknown` and leaves the child and any
background commands alone. An unknown prompt admission is not retried. The plugin doesn't change
phase decisions, approvals, or counters.

See [managed child dispatch](../../../skills/pdca/references/adapters.md#managed-child-dispatch) for
the driver's procedure. To check the transport on a private OpenCode server, run
`python3 test/dispatch_replay.py` from this directory.

## What survives a restart

The authoritative receipt is in the original `.pdca/status/*.md` file. The plugin pins the exact completed planner report under the assigned evidence directory, updates the status and counters in one atomic replacement, and queues the substantive DO brief. The plugin store indexes authorized tickets by location; it is not a second progress log. Repeating a delivery uses the same OpenCode inbox message ID. The planner's ordinary notification to its parent can still wake that parent.

The executor can `inspect` the ticket. `held` returns a pinned decision or an interruption reason. `pending` means the status was committed but delivery is unconfirmed. `delivered` means inbox admission, not performance or acceptance of the task. `recover` reconciles the same ticket. New instructions, a changed status, a changed pinned report or lost permission prevent automatic dispatch.

For a planned transfer to manual operation, release a waiting ticket before changing the writer election. After an unexpected removal, quiesce the old writer; inspect the checkpoint and compare pending IDs with the recipient's inbox/history. Resume admitted work instead of dispatching it again. Retain the prepared packet if delivery has not begun. The status retains the operation receipts even with the plugin unloaded; an unknown outcome stays open for reconciliation.

## Reproduce the measurements

From this directory, run:

```sh
node --test test/*.test.js
python3 test/replay.py --runs 3
python3 test/compatibility.py
```

The first command needs Node.js 22+ and Python 3. The replay also needs `opencode` on `PATH`. It creates private OpenCode servers with temporary home, config and data directories, and a loopback-only scripted provider. Neither a production model nor a running PDCA session is used.

Run `test/compatibility.py` from a source checkout with commit `96b5f27` available. It compares no plugin, the actual 0.1 plugin at that commit, 0.2, and removal of 0.2 after packet publication but before delivery. It executes a background shell, verifies an independent CHECK received the packet once, checks its pinned verdict, counters and product, and reports model requests after the verdict separately from total requests.

On OpenCode 2.3.2, all four lanes delivered one CHECK and reached ACT at `N=8, r=1, n=1`. Recording the verdict took two executor model requests in the manual, 0.1 and takeover lanes and zero in 0.2. In one run the complete extension fixture used 13 provider requests both manually and with 0.2 (19 with takeover); setup, wait registration and native parent notifications also consume turns. This measures bookkeeping removal, not a whole-campaign speedup.

The control has no plugin. Its executor pins the report and records the transition in one tool call. Both lanes execute the same fixture, compare the product and check the complete normalized status. Normalization excludes the writer receipt, clock and content-addressed reference; each original report is verified separately. The replay prints role-specific provider calls, including the cost of arming before PLAN; parent notifications are counted separately. The interval is local test latency, not a prediction for a production campaign.

In three paired runs on OpenCode 2.3.2, the campaign opened step 4, cycle 8, revision 1, attempt 1 and produced `b,a` in both modes:

| Metric | Manual | Plugin |
| --- | ---: | ---: |
| Executor requests before the decision, including setup | 1 | 2 |
| Bookkeeping requests between the planner and substantive DO | 2 | 0 |
| Median time from the planner request to the substantive DO request | 422 ms | 293 ms |

The extra setup turn reduces the net saving in this fixture to one executor request. The parent still receives native OpenCode notifications. For a field measurement, count those requests separately and compare complete campaigns, including setup, checks, tool runtime and interruptions.
