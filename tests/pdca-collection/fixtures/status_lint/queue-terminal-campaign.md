# Collection plan-terminal malformed: campaign form — status

A `campaign` item never carries a PLAN-terminal row: an established step result goes
to an independent CHECK inside the campaign, so the typed row cannot bypass it.

## Units

| unit | form | status | plan_state | terminal | attempts | reason + patch |
|---|---|---|---|---|---|---|
| U1 | campaign | incomplete | — | already-established | 0 | the requested result already exists at the recorded ref |
