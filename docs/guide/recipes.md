# Copy a PDCA prompt

[Русский](../ru/guide/recipes.md)

Use these examples as starting points after [setting up PDCA](../install.md). Adapt the goal to your repository, and write criteria only if you intend to keep them as the exact acceptance set.

## Fix a reproducible bug

For an export that repeats rows after retry, start with this prompt:

```text
Use pdca in normal mode. Fix the duplicate CSV rows on retry.
Show the bug on the unmodified code and verify the fix on the same case.
Preserve existing test behavior. Don't commit or push.
```

Expect evidence of the failure and the corrected behavior, not a claim that a new test passed once.

## Change a .NET service

For an endpoint with an established error response contract, try:

```text
Use pdca. Make the .NET export endpoint return the same validation error
shape as the existing import endpoint for invalid dates. Preserve the
success response and existing test expectations. Don't commit.
```

Expect the .NET overlay for the code change. If a decision depends on a C# symbol, the host or project determines which semantic tool is appropriate.

## Improve a metric when the method is unknown

If a benchmark already exists but the bottleneck is unknown, try:

```text
Use pdca in normal mode. Reduce the import benchmark's p95 below 200 ms
on its existing fixture and runner. Keep the same input and measurement
conditions. Establish the baseline before optimizing. Don't commit.
```

Expect a comparable baseline and verified steps, not a promise to hit the target after a fixed number of steps.

## Batch independent changes

For separate defects in different parts of a release, try:

```text
Use pdca in normal mode for this batch: correct the export CLI help,
and fix broken local links in the deployment guide. Keep the goals
separate. Wait for my approval before execution. Don't push.
```

Expect a preparation barrier and a report per item plus the integration verdict. If multiple groups need commits and merges, authorize those actions explicitly or expect a blocker; omitting push permission doesn't grant commit or merge permission.
