# Which form does PDCA choose?

[Русский](../ru/guide/choose-a-form.md)

If you know what you want but don't know which PDCA skill to name, start with `pdca`. The entry PLAN selects the form from the goal and available facts. Naming `pdca` does not force a bounded cycle.

Use these distinctions to interpret the choice:

| Your task | Form | What acceptance means |
|---|---|---|
| Replace a wrong CLI help string; the location and expected text are known. | Bounded Execution (`cycle`) | CHECK covers the whole requested change. |
| Reach an agreed latency threshold; you have a repeatable benchmark but don't know which bottlenecks you'll find. | Incremental Execution (`incremental`) | Start from a comparable baseline, verify increments, and check the whole goal before declaring it met. |
| Fix independent help-text and documentation defects for one release. | Collection (`collection`) | Prepare all items before execution; check the integrated result and account for each item. A campaign item stays sequential within its lane. |

Several dependent operations with a known method and scope can still be one bounded task. A known output format doesn't establish a known method. If one missing fact decides the form, the planner can use one bounded probe without launching a second classification.

The coding overlays change what gets checked, not the form. `pdca-coder` adds engineering rules; `pdca-dotnet` inherits them and adds the .NET rules. When you explicitly name a form or overlay, it constrains routing. If that contract or a required parent can't load, PDCA preserves the selection rather than switching to an easier route.

Next, [copy a prompt for your situation](recipes.md).
