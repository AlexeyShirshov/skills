# Run your first PDCA cycle

[Русский](../ru/guide/first-cycle.md)

If you're using PDCA for the first time, try a read-only task in a local Git repository. You'll approve a result contract and check the answer against the files without editing the product.

## Before you begin

You need a repository with a root `README.md` that links to at least one local file, a host that can dispatch the PDCA roles, and permission to write PDCA state under `.pdca/`.

## Start and review the run

1. Follow [the installation checklist](../install.md) for your host. Verify both skill loading and role resolution; a skill in the picker alone doesn't verify setup.
2. In a session opened in that repository, send this prompt:

   ```text
   Use pdca in normal mode. List the distinct repository-relative files
   linked from the root README.md that exist on disk. Sort the paths.
   Don't edit product files or commit.
   ```

3. Open the saved PLAN at the path the agent gives you. Confirm that it promises the list you requested, not a general link audit. If the PLAN changes the task, don't approve it.
4. Approve that exact plan. The separate question about stopping after an effort estimate doesn't count as approval and approval doesn't opt you into an effort cap.
5. After ACT, open the reported status file. Confirm that CHECK accepted the result and that it points to evidence for the list. Compare a path in the answer with the README and the file on disk.

If PLAN says the result was already established, look for its derivation in ACT; an independent CHECK did not run. If setup blocks the run, follow the install or permission guidance for the exact missing role or skill instead of asking the agent to skip it.

Next, see [how to read a result](read-the-result.md).
