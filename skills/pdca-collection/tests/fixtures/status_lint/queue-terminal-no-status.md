# Collection plan-terminal malformed: no status column — status

A plan-terminal row must be provably `incomplete`; without a `status` column the
lint fails closed instead of skipping the check.

## Units

| unit | form | plan_state | terminal | attempts | reason + patch |
|---|---|---|---|---|---|
| U1 | cycle | pending | infeasible | 0 | proven infeasible under the stated constraints |
