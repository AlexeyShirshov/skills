#!/usr/bin/env bash
# Deterministic check of the pdca-collection git model (references/lane.md §Git model):
#   - per-task branch chain inside a group, auto-commit per task
#   - group branch fast-forwarded to the last task tip
#   - `git merge --no-ff` of each group branch into the current branch
#   - a conflicting merge is detected, not silently ignored
#   - a single-group collection creates no worktree/branch and does not merge
#   - an `incomplete` group is never merged, yet its branch/tip and commits survive
# No product code, no network, temp repos only.
#
# Branch naming (must be siblings — git forbids a ref that is a prefix of
# another ref):  group `collection/<id>/group-<g>`, task `collection/<id>/task-<g>-<k>`.
#
# Run:  bash skills/pdca-collection/tests/git-model-sim.sh
set -euo pipefail

SKILL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# Optional host config root (agents/profiles live outside this repo). Resolved in
# this order: $OPENCODE_CONFIG_REPO/config, `<config>/skills/pdca-collection/../..`
# (installed), `<config>/skills/pdca-collection/../../..` (repo checkout).
host_root=""
if [ -n "${OPENCODE_CONFIG_REPO:-}" ] && [ -d "$OPENCODE_CONFIG_REPO/config/agents" ]; then
  host_root=$(cd "$OPENCODE_CONFIG_REPO/config" && pwd)
else
  for cand in "$SKILL_DIR/../.." "$SKILL_DIR/../../.."; do
    if [ -d "$cand/agents" ]; then host_root=$(cd "$cand" && pwd); break; fi
  done
fi

base=""; base2=""; base3=""; base4=""
cleanup() { rm -rf "${base:-}" "${base2:-}" "${base3:-}" "${base4:-}"; }
trap cleanup EXIT

say() { printf '%s\n' "$*"; }

# ---------- Case 0: artifact branch-naming consistency ----------
# The skill (and the lane agent, if installed) must not use the illegal nested
# scheme `collection/<id>/<group>/t<k>` (a ref that is a prefix of another ref).
artifacts=("$SKILL_DIR/SKILL.md")
if [ -n "$host_root" ]; then artifacts+=("$host_root/agents/lane.md"); fi
for a in "${artifacts[@]}"; do
  if [ ! -f "$a" ]; then say "SKIP: $a not installed"; continue; fi
  if grep -qF 'collection/<id>/<group>/' "$a"; then
    say "FAIL: stale nested branch naming in $a"; exit 1
  fi
  grep -qE 'collection/<id>/group-<g>|collection/<id>/task-<g>-<k>' "$a" \
    || { say "FAIL: new branch naming missing in $a"; exit 1; }
done
say "OK: artifact branch naming consistent"

# ---------- Case 1: happy path ----------
base=$(mktemp -d); repo="$base/repo"
mkdir "$repo"; git -C "$repo" init -q -b main
git -C "$repo" config user.email t@t; git -C "$repo" config user.name t
echo base > "$repo/base.txt"; git -C "$repo" add -A; git -C "$repo" commit -qm base

for g in A B; do
  git -C "$repo" worktree add -q -b "collection/x/group-$g" "$base/wt$g" main
done

# Group A: task branches chain t1 -> t2; group branch ff-equal to last tip.
(
  cd "$base/wtA"
  git checkout -q -b "collection/x/task-A-1"
  echo a1 > a1.txt; git add -A; git commit -qm "A t1"
  git branch -f collection/x/group-A HEAD
  git checkout -q -b "collection/x/task-A-2"
  echo a2 > a2.txt; git add -A; git commit -qm "A t2"
  git branch -f collection/x/group-A HEAD
)

# Group B: task branches chain t1 -> t2.
(
  cd "$base/wtB"
  git checkout -q -b "collection/x/task-B-1"
  echo b1 > b1.txt; git add -A; git commit -qm "B t1"
  git branch -f collection/x/group-B HEAD
  git checkout -q -b "collection/x/task-B-2"
  echo b2 > b2.txt; git add -A; git commit -qm "B t2"
  git branch -f collection/x/group-B HEAD
)

cd "$repo"

# Branch chain + group tip == last task tip.
git rev-parse --verify -q collection/x/group-A >/dev/null
git rev-parse --verify -q collection/x/task-A-1   >/dev/null
git rev-parse --verify -q collection/x/task-A-2   >/dev/null
git merge-base --is-ancestor collection/x/task-A-1 collection/x/task-A-2
[ "$(git rev-parse collection/x/group-A)" = "$(git rev-parse collection/x/task-A-2)" ]
[ "$(git rev-parse collection/x/group-B)" = "$(git rev-parse collection/x/task-B-2)" ]

git merge --no-ff -q collection/x/group-A -m "merge group-A"
git merge --no-ff -q collection/x/group-B -m "merge group-B"

merges=$(git rev-list --merges --count main)
ok=1
for f in a1.txt a2.txt b1.txt b2.txt; do [ -f "$f" ] || ok=0; done
[ "$merges" -eq 2 ] || ok=0
if [ "$ok" -eq 1 ]; then
  say "OK: group-A merged, group-B merged, 2 merge commits"
else
  say "FAIL: happy path (merges=$merges)"; exit 1
fi

# ---------- Case 2: conflicting merges ----------
base2=$(mktemp -d); repo2="$base2/repo"
mkdir "$repo2"; git -C "$repo2" init -q -b main
git -C "$repo2" config user.email t@t; git -C "$repo2" config user.name t
printf 'line\n' > "$repo2/shared.txt"; git -C "$repo2" add -A; git -C "$repo2" commit -qm base
for g in A B; do
  git -C "$repo2" worktree add -q -b "collection/x/group-$g" "$base2/wt$g" main
done
( cd "$base2/wtA"; echo 'A-changed' > shared.txt; git add -A; git commit -qm "A change" )
( cd "$base2/wtB"; echo 'B-changed' > shared.txt; git add -A; git commit -qm "B change" )

cd "$repo2"
git merge --no-ff -q collection/x/group-A -m "merge group-A"
if git merge --no-ff collection/x/group-B -m "merge group-B" >/dev/null 2>&1; then
  say "FAIL: expected conflict, merge group-B succeeded"; exit 1
else
  git merge --abort 2>/dev/null || true
  say "OK: conflict detected, group marked failed"
fi

# ---------- Case 3: single group — no worktree, no branches, no merge ----------
base3=$(mktemp -d); repo3="$base3/repo"
mkdir "$repo3"; git -C "$repo3" init -q -b main
git -C "$repo3" config user.email t@t; git -C "$repo3" config user.name t
echo base > "$repo3/base.txt"; git -C "$repo3" add -A; git -C "$repo3" commit -qm base

cd "$repo3"
echo s1 > s1.txt; git add s1.txt; git commit -qm "single t1"
echo s2 > s2.txt; git add s2.txt; git commit -qm "single t2"

refs=$(git for-each-ref --format='%(refname)' refs/heads)
merges3=$(git rev-list --merges --count main)
worktrees=$(git worktree list --porcelain | grep -c '^worktree ')
ok=1
[ "$refs" = "refs/heads/main" ] || ok=0
[ "$merges3" -eq 0 ] || ok=0
[ "$worktrees" -eq 1 ] || ok=0
if [ "$ok" -eq 1 ]; then
  say "OK: single group — commits on current branch, no branches, no merge"
else
  say "FAIL: single-group isolation (refs=$refs merges=$merges3 worktrees=$worktrees)"; exit 1
fi

# ---------- Case 4: incomplete group — never merged, evidence preserved ----------
# Group A reaches `done` and is merged; group B's next task is definitively
# incomplete, so its committed work must stay on the group branch (evidence for
# the final report) while main receives nothing from it.
base4=$(mktemp -d); repo4="$base4/repo"
mkdir "$repo4"; git -C "$repo4" init -q -b main
git -C "$repo4" config user.email t@t; git -C "$repo4" config user.name t
echo base > "$repo4/base.txt"; git -C "$repo4" add -A; git -C "$repo4" commit -qm base
for g in A B; do
  git -C "$repo4" worktree add -q -b "collection/y/group-$g" "$base4/wt$g" main
done

# Group A: one completed task; group branch ff-equal to its tip.
(
  cd "$base4/wtA"
  git checkout -q -b "collection/y/task-A-1"
  echo a1 > a1.txt; git add -A; git commit -qm "A t1"
  git branch -f collection/y/group-A HEAD
)

# Group B: task 1 completed, task 2 committed but left incomplete.  Its commits
# are preserved on the branch, and the group branch still points at that tip.
(
  cd "$base4/wtB"
  git checkout -q -b "collection/y/task-B-1"
  echo b1 > b1.txt; git add -A; git commit -qm "B t1"
  git branch -f collection/y/group-B HEAD
  git checkout -q -b "collection/y/task-B-2"
  echo partial > b2.txt; git add -A; git commit -qm "B t2 (incomplete)"
  git branch -f collection/y/group-B HEAD
)

cd "$repo4"
btip=$(git rev-parse collection/y/group-B)
git merge --no-ff -q collection/y/group-A -m "merge group-A"

merges4=$(git rev-list --merges --count main)
ok=1
[ "$merges4" -eq 1 ] || ok=0
[ -f a1.txt ] || ok=0
# nothing from the incomplete group reached the integrated branch ...
if [ -e b1.txt ] || [ -e b2.txt ]; then ok=0; fi
if git merge-base --is-ancestor "$btip" main; then ok=0; fi
# ... but its refs and commits are still there as evidence.
git rev-parse --verify -q collection/y/group-B >/dev/null || ok=0
[ "$(git rev-parse collection/y/group-B)" = "$btip" ] || ok=0
git merge-base --is-ancestor "$btip" collection/y/task-B-2 || ok=0
if [ "$ok" -eq 1 ]; then
  say "OK: incomplete group-B not merged, branch/tip preserved"
else
  say "FAIL: incomplete-group isolation (merges=$merges4)"; exit 1
fi

say "OK: git model verified"
