# AGENTS.md — working in the skills repository

This repo is the **source of truth** for `opencode/<skill>/` and `opencode/plugins/<plugin>/`.
Everything downstream is generated from it — never the other way around.

```
here (skills repo)  →  ../opencode-config (snapshot)  →  ~/.config/opencode (host, deploy only)
```

Local checkout of the snapshot: `/home/alex/sources/opencode-config` (`../opencode-config`).
The host config is `~/.config/opencode`.

## Edit here, not downstream

- A skill or plugin is fixed **only in this repo**. Do not edit
  `../opencode-config/config/skills/**`, `../opencode-config/config/plugins/<vendored>/**`
  or `~/.config/opencode/**` — those are copies (the host is a deploy target, not a source).
- An edit found in the snapshot or the host is never "legalised" by copying it back; if it
  matters, port it here deliberately and go through the normal order.

## Order of work

1. Change `opencode/<skill>/` or `opencode/plugins/<plugin>/`.
2. Test:
   ```bash
   OPENCODE_CONFIG_REPO=/home/alex/sources/opencode-config \
     python3 -m unittest discover -s opencode/<skill>/tests -p 'test_*.py'
   ```
   Some suites compare against the snapshot (`config/agents`, `config/profiles`); they are
   skipped unless `OPENCODE_CONFIG_REPO` is set.
3. Commit and push **here**.
4. Only then vendor into the snapshot (it refuses a dirty or unpushed source):
   ```bash
   cd /home/alex/sources/opencode-config
   bun config/tools/vendor-skills.mjs --fix     # source -> snapshot, writes skills.lock.json
   bun config/tools/vendor-skills.mjs --check   # must exit 0
   ```
5. Commit the snapshot in `opencode-config`. Deploying the host is a separate explicit step —
   never part of a skill change.

## What is vendored

`config/tools/vendor-skills.mjs` in the snapshot lists the items (`ITEMS`): skills `pdca`,
`pdca-entry`, `pdca-coder`, `pdca-collection`, `pdca-dotnet`, `pdca-incremental` and plugins
`git-status`, `zen-failover`. A new skill/plugin reaches the snapshot only after adding it to
that list — and only after it exists here, committed and pushed.
