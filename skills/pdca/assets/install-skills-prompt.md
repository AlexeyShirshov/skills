# Install prompt: missing skill contracts

Hand the fenced prompt below to the user verbatim, filling only its `Context` block. It is a request
for the host's approved installation workflow, not an installer or permission to change host state.
Fill every Context field with observed facts before handoff. If exact loader wording is unavailable,
state `exact loader message unavailable` and the known failure class; never invent a response or leave
template tokens in the filled Context.

## Prompt (fill only its Context)

```text
Resolve only the PDCA skill contracts listed in Context. Do not run or resume the user's task.

Context:
  MISSING_SKILL_IDS=<exact skill IDs the host loader reported missing or unreadable>
  REQUIRED_BY=<the selected form/overlay and dependency that requires each ID>
  HOST_LOAD_FAILURE=<the host loader's actual response for each ID; preserve denied/unreadable distinctions>

The source of truth is https://github.com/AlexeyShirshov/skills, under `skills/<skill-id>/`.
Use the host/repository's approved install/deploy source-of-truth workflow. First identify that
workflow and the exact target; if either is unclear, stop and ask rather than inventing commands.
Scope work to the listed missing IDs and only the dependency closure needed to load them. Preserve
already loadable contracts. Do not install all five PDCA skills, optional forms/overlays, or a
different skill as a substitute.

If the host loader reported permission denied/forbidden, treat this as a permission blocker, not an
uninstalled skill: do not reinstall, try another loader or path, bypass the denial, or widen
permissions. Report the exact blocker and ask for the authorized permission remedy.

Do not auto-install, auto-deploy, overwrite unrelated configuration, change role/model bindings or
permissions, or start the user's task. Make no host or project changes unless the approved workflow
and the user explicitly authorize the exact changes. Report the source, IDs, target, actions and
remaining blockers.
```
