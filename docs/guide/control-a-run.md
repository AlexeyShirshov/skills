# Control and resume a PDCA run

[Русский](../ru/guide/control-a-run.md)

Use this page when you need to keep the approval decision or continue after an interrupted session.

## Choose a mode

- **Normal:** the primary coordinates the cycle. Before DO, it links the saved plan and asks for explicit approval. For an incremental campaign, approve each step; a collection has a preparation barrier before execution. A question, silence, or approval of an older revision doesn't authorize DO.
- **Autonomous:** ask for this mode explicitly when intermediate plan approval is unnecessary. A cheap-tier primary can delegate to `pdca-orchestrator`; if that route is unavailable, the permitted flat fallback records a `Notice:`. Autonomy doesn't grant tool permissions, Git authorization, or consent for external or irreversible actions. An unobtainable required approval is a blocker, not implicit consent.

## Resume an interrupted run

1. Find the status path the previous session reported. A bounded cycle defaults to `.pdca/status/<task>-<N>.md`; campaigns and collections have their own containing status records.
2. In a session for the same workspace, ask PDCA to resume and give it that exact path. Keep any original commit and scope constraints in force.
3. Confirm that the agent identifies the saved phase and counters before continuing. A checkpoint or an interrupted dispatch doesn't justify a fresh PLAN or a counter reset. If a pending approval is stale or mismatched, review the revision before approving.

If loading a required skill is denied, resolve the host policy with its owner. Installation isn't a workaround for a denial. If the skill is missing, use the install prompt provided with the blocker.

Next, see [how to read the result](read-the-result.md).
