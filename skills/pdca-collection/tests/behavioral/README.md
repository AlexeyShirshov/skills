# Behavioral probes for `pdca-collection`

The rest of `tests/` checks the **normative text** of the contract. These probes check
**artifacts of a real run**: an isolated opencode sandbox executes a collection in a throwaway
git repo, and the verdict is made from the status file, the preparation document and git
state — never from the agent's summary.

A live probe is **opt-in**: it costs model tokens and is non-deterministic, so it never runs in
the default suite. The offline half (`test_behavioral_contract.py`) does run there: it replays
the recorded statuses from `fixtures/` through the same checks and proves they fail on
mutations that a contract violation would produce.

## Probes

| Probe | Input | What must hold |
|---|---|---|
| `gap` | three units; `T2` needs a metric/recipe/target that the user reserved and never supplied | `T2` stays a gap (`plan_state`/`preparation_state` not ready, no `ready` placeholder); the ALL-barrier fails; no DAG, group, worktree, branch, lane or product edit |
| `campaign` | `U1` campaign (fixed recipe/target, unknown information-dependent path) + `U2` a simple cycle; no autocommit right | `U1` has `form=campaign` with the immutable preparation document (mandatory blocks), `preparation_state=ready` and one `preparation_ref`; no item-level contract, no baseline, no runtime status, no step plans; the barrier passes and D leaves no lane behind the preflight blocker |
| `lane` | one task, autonomous mode | after the barrier the group is driven through DO by `pdca-orchestrator` (nested roles), the product changes and the unit reaches `done`/`merged`; a flat-primary fallback is a failure |

## Prerequisites

1. An isolated sandbox, e.g. `~/sources/opencode-config-sandbox` (own `XDG_*`, own sessions DB).
2. `python3 probe.py install` — copies the six family skills and the `pdca-coder` role set from
   **this repository** into the sandbox config. Re-run after changing a skill.
3. Sandbox permissions: non-interactive runs auto-reject `external_directory` reads, and the
   agents read their skills/agents from the sandbox config dir. Allow that dir and `/tmp` in the
   sandbox `opencode.jsonc`.
4. For `lane` only: `experimental.subagent_depth >= 2` — otherwise `pdca-orchestrator` cannot
   delegate and the contract's flat-primary fallback engages (the probe fails by design and the
   status records a `Notice:`).

## Usage

```bash
python3 skills/pdca-collection/tests/behavioral/probe.py install
python3 skills/pdca-collection/tests/behavioral/probe.py gap
python3 skills/pdca-collection/tests/behavioral/probe.py campaign
python3 skills/pdca-collection/tests/behavioral/probe.py lane
python3 skills/pdca-collection/tests/behavioral/probe.py check ~/pdca-behavioral/gap-<stamp>
```

Each run prints `PASS`/`FAIL` with the concrete failures, and leaves the evidence in the
workdir: `repo/.pdca/**` (the artifacts), `run.log` (the transcript), `run.meta` (exit code,
duration), `baseline.sha256` (pre-run hashes of tracked files) and `result.json`.

Environment:

| Variable | Default |
|---|---|
| `PDCA_SANDBOX_BIN` | `~/sources/opencode-config-sandbox/bin/oc-sandbox` |
| `PDCA_BEHAVIORAL_MODEL` | `deepseek/deepseek-flash` |
| `PDCA_BEHAVIORAL_TIMEOUT` | `1800` (seconds) |

`OPENCODE_CONFIG` and `OPENCODE_SESSION_ID` are stripped from the child environment: inheriting
them makes the sandbox load the host profile and/or attach to the host session.

## Recorded runs and the offline suite

`fixtures/` holds the artifacts of three real sandbox runs (`gap-status.md`,
`campaign-status.md`, `campaign-preparation.md`, `lane-status.md`). The offline test
(`test_behavioral_contract.py`, part of the normal `unittest discover`) replays them through
`checks.py` and then mutates them the way a contract violation would — a `ready` placeholder on
the gap unit, an allocated group despite the open barrier, a cycle instead of a campaign, a
missing frame point, a runtime status at the barrier, a missing product change after DO — and
requires every mutation to be caught. Refresh the fixtures only together with the status-file
format, and keep both table shapes in mind: the recorded runs use a units table and a separate
tasks table, with different column orders.

## What the probes do not prove

DO/CHECK/ACT quality, autocommit and `merge --no-ff` integration, group-stop after a terminal
`incomplete`, and corrective-task STOP. Those need dedicated scenarios (and, for the merge path,
`tests/git-model-sim.sh` already covers the git mechanics deterministically).
