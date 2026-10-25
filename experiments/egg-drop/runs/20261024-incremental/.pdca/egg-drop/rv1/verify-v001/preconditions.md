# Final verify (mechanical part) — preconditions

Package: `.pdca/egg-drop/rv1/verify-v001`  
Repo: `/home/alex/sources/skills`  
Run budget: final verify run 1 of 2  
Checked at: 2026-10-24T18:22Z (before V1/V2), re-checked after both runs

## 1. Manifest input hashes (27)

Manifest: `.pdca/egg-drop/rv1/m001/manifest.json` (schema `egg-drop-measurement-manifest-v1`),
`inputs_base`: package-relative to `.pdca/egg-drop/rv1/m001`, `input_count` = 27.

| # | input (package-relative) | declared sha256 | recomputed sha256 | match |
|---|---|---|---|---|
| 1 | `answer.md` | `40a56cc82905a64da7d6104beec99565e5ef7b49d5fcfa29c94439a3882cd4c3` | `40a56cc82905a64da7d6104beec99565e5ef7b49d5fcfa29c94439a3882cd4c3` | yes |
| 2 | `check_answer.py` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` | yes |
| 3 | `egg-drop-test.md` | `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e` | `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e` | yes |
| 4 | `fixtures/controls/m01-missing-section/answer.md` | `b146328c1dba08d01a857edec1cdaf023104d80b8c2b7f6f47d1ba278dec2c94` | `b146328c1dba08d01a857edec1cdaf023104d80b8c2b7f6f47d1ba278dec2c94` | yes |
| 5 | `fixtures/controls/m02-section-order/answer.md` | `57f2567de749c5d3fae3d4b647e0cbc0b4cdaba1b7e7c2e279241e06961d8f40` | `57f2567de749c5d3fae3d4b647e0cbc0b4cdaba1b7e7c2e279241e06961d8f40` | yes |
| 6 | `fixtures/controls/m03-missing-s4-item/answer.md` | `2290635664ba0932ad58dcfc18e2ae87302b00d35c69042741366ac243beb7fc` | `2290635664ba0932ad58dcfc18e2ae87302b00d35c69042741366ac243beb7fc` | yes |
| 7 | `fixtures/controls/m04-mass-501/answer.md` | `9a96df30dd6b03768d0dc5779cd7e047d387558a1aeddcefe67d70c16adb7430` | `9a96df30dd6b03768d0dc5779cd7e047d387558a1aeddcefe67d70c16adb7430` | yes |
| 8 | `fixtures/controls/m05-side-301/answer.md` | `6a79319a6dc995b889c6f0fc23a80633817d8e6cc054bab9651b5846f5be9229` | `6a79319a6dc995b889c6f0fc23a80633817d8e6cc054bab9651b5846f5be9229` | yes |
| 9 | `fixtures/controls/m06-volume-300-cube/answer.md` | `d7dfcf3bcdd11959a5a771f207f3a7a8e8a4ad38faf670ee7c8b228390cf8d3d` | `d7dfcf3bcdd11959a5a771f207f3a7a8e8a4ad38faf670ee7c8b228390cf8d3d` | yes |
| 10 | `fixtures/controls/m07-budget-501/answer.md` | `79a124de50be6fc3536940df1047d1b87f30250eeddfb7650e62ca0fa5e661e9` | `79a124de50be6fc3536940df1047d1b87f30250eeddfb7650e62ca0fa5e661e9` | yes |
| 11 | `fixtures/controls/m08-build-31/answer.md` | `872412de623062f2cd14e1d926c794490ba7e28be0a050a10cafbcba5f7380d0` | `872412de623062f2cd14e1d926c794490ba7e28be0a050a10cafbcba5f7380d0` | yes |
| 12 | `fixtures/controls/m09-metal-used/answer.md` | `9d2111365543c117d63bdd34ef676b58c1cc47ce0b4750efaa12f9be821a799c` | `9d2111365543c117d63bdd34ef676b58c1cc47ce0b4750efaa12f9be821a799c` | yes |
| 13 | `fixtures/controls/m10-egg-glued/answer.md` | `a3a798357b0344a17a76e1a5ab3a8276aa5e818dea9391fee9af4551a8957bac` | `a3a798357b0344a17a76e1a5ab3a8276aa5e818dea9391fee9af4551a8957bac` | yes |
| 14 | `fixtures/controls/m11-zero-stroke/answer.md` | `a61c7f1d67d56332a79697365ec428e675405361b04872b6ff3a26746bd2a814` | `a61c7f1d67d56332a79697365ec428e675405361b04872b6ff3a26746bd2a814` | yes |
| 15 | `fixtures/controls/m12-wrong-velocity/answer.md` | `3615ea69b3c47f2802359fc2044afff331cfab6cf2815946d6da9c8f8c411329` | `3615ea69b3c47f2802359fc2044afff331cfab6cf2815946d6da9c8f8c411329` | yes |
| 16 | `fixtures/controls/m13-wrong-energy/answer.md` | `15d5ddcc32c34a91248710ff7f42d2ac594f60d0291fdadc6fab6a541b87dd9c` | `15d5ddcc32c34a91248710ff7f42d2ac594f60d0291fdadc6fab6a541b87dd9c` | yes |
| 17 | `fixtures/controls/m14-wrong-force/answer.md` | `5c59558792e222364b6952e11ee72d78cb58b1d2f88c990ad70338ee10a83504` | `5c59558792e222364b6952e11ee72d78cb58b1d2f88c990ad70338ee10a83504` | yes |
| 18 | `fixtures/controls/m15-wrong-load/answer.md` | `ad74043eb91f7b2269820cd3038c283dbe3b8d58a019cf5cb8c2360aa8f8b02a` | `ad74043eb91f7b2269820cd3038c283dbe3b8d58a019cf5cb8c2360aa8f8b02a` | yes |
| 19 | `fixtures/controls/m16-wrong-stress/answer.md` | `bdeb73a6396b83b9238bb3ceb6ff24fb4a210584ed69eb7c0b9e37b846a42b4a` | `bdeb73a6396b83b9238bb3ceb6ff24fb4a210584ed69eb7c0b9e37b846a42b4a` | yes |
| 20 | `fixtures/controls/m17-wrong-eta/answer.md` | `0703cc19a32a85efdc4cf147aaccf4ae1038b032e163e8d2941c98b0d0fde7c5` | `0703cc19a32a85efdc4cf147aaccf4ae1038b032e163e8d2941c98b0d0fde7c5` | yes |
| 21 | `fixtures/controls/m18-bad-probabilities/answer.md` | `037b2f8e0f2987ae6115c98b93542d99553242ae6518bc9cd6419a62096963a3` | `037b2f8e0f2987ae6115c98b93542d99553242ae6518bc9cd6419a62096963a3` | yes |
| 22 | `fixtures/controls/m19-null-total-mass/answer.md` | `8042f2c72b4f8d823fbf3576bf7aa1d0338681d6549a2196b5ef46b371c3dd96` | `8042f2c72b4f8d823fbf3576bf7aa1d0338681d6549a2196b5ef46b371c3dd96` | yes |
| 23 | `fixtures/controls/m20-unknown-material/answer.md` | `7d51aa80efc3a5a8e672eb99b8eba77dd8d4e13b74a53cf06da02aae28609ae2` | `7d51aa80efc3a5a8e672eb99b8eba77dd8d4e13b74a53cf06da02aae28609ae2` | yes |
| 24 | `fixtures/controls/p01-prohibition-only/answer.md` | `c7fbd4ac7953c11489e4dc6370411c938455de77f3401f6068ce0dab24328a86` | `c7fbd4ac7953c11489e4dc6370411c938455de77f3401f6068ce0dab24328a86` | yes |
| 25 | `fixtures/known-good/answer.md` | `16cdb204ef645fdb2c9178203bd9b2bd0e4e2d18d359cfce7dcc714f16e071be` | `16cdb204ef645fdb2c9178203bd9b2bd0e4e2d18d359cfce7dcc714f16e071be` | yes |
| 26 | `fixtures/manifest.json` | `adedef98e22ca68f47dbfc0deff3444fd703ee61b1305df10a931750976e33d0` | `adedef98e22ca68f47dbfc0deff3444fd703ee61b1305df10a931750976e33d0` | yes |
| 27 | `fixtures/tools/make_controls.py` | `b31530519bb612ed64861a5dfcdfb027f0bc07562aedf0d220019e0bfd44ddc4` | `b31530519bb612ed64861a5dfcdfb027f0bc07562aedf0d220019e0bfd44ddc4` | yes |

Result: **27/27 match, `bad=[]`** (no missing files, no hash mismatch).
Manifest `input_hashes_sha256` = `22d09176f140f5f8910513dcb169326da1cc48b5a17dfc6749406da9f14411b8`; recomputed over the sorted `sha256sum`-style list of the same 27 pairs: `22d09176f140f5f8910513dcb169326da1cc48b5a17dfc6749406da9f14411b8` (match).
`post_run_integrity.post_run_hashes_match` = `True`; the post-run map equals the `inputs` map: `True`.
Recomputed again after V1 and V2: 27/27 match, `bad=[]` (no drift).

## 2. Byte-identity: working files vs the frozen m001 copies

| working file | working sha256 | frozen m001 sha256 | identical |
|---|---|---|---|
| `experiments/egg-drop/answer.md` | `40a56cc82905a64da7d6104beec99565e5ef7b49d5fcfa29c94439a3882cd4c3` | `40a56cc82905a64da7d6104beec99565e5ef7b49d5fcfa29c94439a3882cd4c3` | yes |
| `experiments/egg-drop/check_answer.py` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` | `d62606562418fab9ded912ef8af6b23c5eb108d11d56d488db671f8b44195dfa` | yes |
| `experiments/egg-drop/egg-drop-test.md` | `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e` | `8a79d64b3b38c4b208c58863d6c7a25f5de3bf5127936d191ab219487b58db4e` | yes |

`experiments/egg-drop/fixtures/**` vs `.pdca/egg-drop/rv1/m001/fixtures/**` — 24 files compared, 24 identical, 0 mismatched, 0 present only in the frozen copy.

| fixture file | working sha256 | frozen sha256 | identical |
|---|---|---|---|
| `fixtures/controls/m01-missing-section/answer.md` | `b146328c1dba08d01a857edec1cdaf023104d80b8c2b7f6f47d1ba278dec2c94` | `b146328c1dba08d01a857edec1cdaf023104d80b8c2b7f6f47d1ba278dec2c94` | yes |
| `fixtures/controls/m02-section-order/answer.md` | `57f2567de749c5d3fae3d4b647e0cbc0b4cdaba1b7e7c2e279241e06961d8f40` | `57f2567de749c5d3fae3d4b647e0cbc0b4cdaba1b7e7c2e279241e06961d8f40` | yes |
| `fixtures/controls/m03-missing-s4-item/answer.md` | `2290635664ba0932ad58dcfc18e2ae87302b00d35c69042741366ac243beb7fc` | `2290635664ba0932ad58dcfc18e2ae87302b00d35c69042741366ac243beb7fc` | yes |
| `fixtures/controls/m04-mass-501/answer.md` | `9a96df30dd6b03768d0dc5779cd7e047d387558a1aeddcefe67d70c16adb7430` | `9a96df30dd6b03768d0dc5779cd7e047d387558a1aeddcefe67d70c16adb7430` | yes |
| `fixtures/controls/m05-side-301/answer.md` | `6a79319a6dc995b889c6f0fc23a80633817d8e6cc054bab9651b5846f5be9229` | `6a79319a6dc995b889c6f0fc23a80633817d8e6cc054bab9651b5846f5be9229` | yes |
| `fixtures/controls/m06-volume-300-cube/answer.md` | `d7dfcf3bcdd11959a5a771f207f3a7a8e8a4ad38faf670ee7c8b228390cf8d3d` | `d7dfcf3bcdd11959a5a771f207f3a7a8e8a4ad38faf670ee7c8b228390cf8d3d` | yes |
| `fixtures/controls/m07-budget-501/answer.md` | `79a124de50be6fc3536940df1047d1b87f30250eeddfb7650e62ca0fa5e661e9` | `79a124de50be6fc3536940df1047d1b87f30250eeddfb7650e62ca0fa5e661e9` | yes |
| `fixtures/controls/m08-build-31/answer.md` | `872412de623062f2cd14e1d926c794490ba7e28be0a050a10cafbcba5f7380d0` | `872412de623062f2cd14e1d926c794490ba7e28be0a050a10cafbcba5f7380d0` | yes |
| `fixtures/controls/m09-metal-used/answer.md` | `9d2111365543c117d63bdd34ef676b58c1cc47ce0b4750efaa12f9be821a799c` | `9d2111365543c117d63bdd34ef676b58c1cc47ce0b4750efaa12f9be821a799c` | yes |
| `fixtures/controls/m10-egg-glued/answer.md` | `a3a798357b0344a17a76e1a5ab3a8276aa5e818dea9391fee9af4551a8957bac` | `a3a798357b0344a17a76e1a5ab3a8276aa5e818dea9391fee9af4551a8957bac` | yes |
| `fixtures/controls/m11-zero-stroke/answer.md` | `a61c7f1d67d56332a79697365ec428e675405361b04872b6ff3a26746bd2a814` | `a61c7f1d67d56332a79697365ec428e675405361b04872b6ff3a26746bd2a814` | yes |
| `fixtures/controls/m12-wrong-velocity/answer.md` | `3615ea69b3c47f2802359fc2044afff331cfab6cf2815946d6da9c8f8c411329` | `3615ea69b3c47f2802359fc2044afff331cfab6cf2815946d6da9c8f8c411329` | yes |
| `fixtures/controls/m13-wrong-energy/answer.md` | `15d5ddcc32c34a91248710ff7f42d2ac594f60d0291fdadc6fab6a541b87dd9c` | `15d5ddcc32c34a91248710ff7f42d2ac594f60d0291fdadc6fab6a541b87dd9c` | yes |
| `fixtures/controls/m14-wrong-force/answer.md` | `5c59558792e222364b6952e11ee72d78cb58b1d2f88c990ad70338ee10a83504` | `5c59558792e222364b6952e11ee72d78cb58b1d2f88c990ad70338ee10a83504` | yes |
| `fixtures/controls/m15-wrong-load/answer.md` | `ad74043eb91f7b2269820cd3038c283dbe3b8d58a019cf5cb8c2360aa8f8b02a` | `ad74043eb91f7b2269820cd3038c283dbe3b8d58a019cf5cb8c2360aa8f8b02a` | yes |
| `fixtures/controls/m16-wrong-stress/answer.md` | `bdeb73a6396b83b9238bb3ceb6ff24fb4a210584ed69eb7c0b9e37b846a42b4a` | `bdeb73a6396b83b9238bb3ceb6ff24fb4a210584ed69eb7c0b9e37b846a42b4a` | yes |
| `fixtures/controls/m17-wrong-eta/answer.md` | `0703cc19a32a85efdc4cf147aaccf4ae1038b032e163e8d2941c98b0d0fde7c5` | `0703cc19a32a85efdc4cf147aaccf4ae1038b032e163e8d2941c98b0d0fde7c5` | yes |
| `fixtures/controls/m18-bad-probabilities/answer.md` | `037b2f8e0f2987ae6115c98b93542d99553242ae6518bc9cd6419a62096963a3` | `037b2f8e0f2987ae6115c98b93542d99553242ae6518bc9cd6419a62096963a3` | yes |
| `fixtures/controls/m19-null-total-mass/answer.md` | `8042f2c72b4f8d823fbf3576bf7aa1d0338681d6549a2196b5ef46b371c3dd96` | `8042f2c72b4f8d823fbf3576bf7aa1d0338681d6549a2196b5ef46b371c3dd96` | yes |
| `fixtures/controls/m20-unknown-material/answer.md` | `7d51aa80efc3a5a8e672eb99b8eba77dd8d4e13b74a53cf06da02aae28609ae2` | `7d51aa80efc3a5a8e672eb99b8eba77dd8d4e13b74a53cf06da02aae28609ae2` | yes |
| `fixtures/controls/p01-prohibition-only/answer.md` | `c7fbd4ac7953c11489e4dc6370411c938455de77f3401f6068ce0dab24328a86` | `c7fbd4ac7953c11489e4dc6370411c938455de77f3401f6068ce0dab24328a86` | yes |
| `fixtures/known-good/answer.md` | `16cdb204ef645fdb2c9178203bd9b2bd0e4e2d18d359cfce7dcc714f16e071be` | `16cdb204ef645fdb2c9178203bd9b2bd0e4e2d18d359cfce7dcc714f16e071be` | yes |
| `fixtures/manifest.json` | `adedef98e22ca68f47dbfc0deff3444fd703ee61b1305df10a931750976e33d0` | `adedef98e22ca68f47dbfc0deff3444fd703ee61b1305df10a931750976e33d0` | yes |
| `fixtures/tools/make_controls.py` | `b31530519bb612ed64861a5dfcdfb027f0bc07562aedf0d220019e0bfd44ddc4` | `b31530519bb612ed64861a5dfcdfb027f0bc07562aedf0d220019e0bfd44ddc4` | yes |

Result: working answer, checker and the whole fixture tree are byte-identical to m001.

## 3. HEAD

`git rev-parse HEAD` = `6636d3690c1c75833a7cc016a65372f5c20eea87` — matches the expected `6636d36`, no drift.

The worktree carries the campaign's own uncommitted changes (`experiments/` and `.pdca/` are
untracked, docs/skills edits are pre-existing); this verify step made no commit, no `git add`
and no push, and touched no tracked file.

## 4. Non-modification

`m001`, `experiments/egg-drop/answer.md`, `check_answer.py` and `experiments/egg-drop/fixtures/**`
were read only. Hashes after V1+V2 are unchanged (sections 1 and 2 recomputed post-run).

## Verdict

**Preconditions OK** — V1 and V2 may proceed (and did; see `selftest.log`, `verify-gate.log`).
