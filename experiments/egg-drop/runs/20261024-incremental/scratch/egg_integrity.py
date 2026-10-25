#!/usr/bin/env python3.10
"""Measurement-integrity facts for .pdca/egg-drop/rv1/m001 (no verdict)."""
import hashlib, json, pathlib, re

REPO = pathlib.Path("/home/alex/sources/skills")
PKG = REPO / ".pdca/egg-drop/rv1/m001"
OUT = REPO / ".pdca/egg-drop/rv1/check-r1"
WORK = {"answer.md": REPO / "experiments/egg-drop/answer.md",
        "egg-drop-test.md": REPO / "experiments/egg-drop/egg-drop-test.md",
        "check_answer.py": REPO / "experiments/egg-drop/check_answer.py"}

def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

man = json.loads((PKG / "manifest.json").read_text())
st = json.loads((PKG / "selftest.json").read_text())
gt = json.loads((PKG / "gate.json").read_text())

# 1. manifest hashes vs actual frozen files + working files
rows = []
for rel, exp in man["inputs"].items():
    p = PKG / rel
    actual = sha(p) if p.exists() else None
    rows.append(dict(file=rel, manifest=exp, actual=actual, exists=p.exists(),
                     match=(actual == exp), size=p.stat().st_size if p.exists() else None))
work = {}
for rel, p in WORK.items():
    work[rel] = dict(path=str(p.relative_to(REPO)), frozen_manifest=man["inputs"][rel],
                     working_sha=sha(p) if p.exists() else None,
                     frozen_sha=sha(PKG / rel) if (PKG / rel).exists() else None)
    work[rel]["all_three_equal"] = len({work[rel]["frozen_manifest"], work[rel]["working_sha"],
                                        work[rel]["frozen_sha"]}) == 1
# declared provenance hashes
prov = man.get("provenance", {})
MIS = [r["file"] for r in rows if not r["match"]]
input_hashes_txt = (PKG / "input-hashes.txt").read_text().strip().splitlines()
ih = {}
for line in input_hashes_txt:
    parts = re.split(r"\s{2,}|\t", line.strip(), maxsplit=1)
    if len(parts) == 2:
        ih[parts[0]] = parts[1]
ih_mismatch = [k for k, v in ih.items() if k not in man["inputs"] or man["inputs"][k] != v]
missing_in_ih = [k for k in man["inputs"] if k not in ih]

# 2. selftest table
cases = []
for c in st["cases"]:
    exp_id = c.get("expected_id")
    obs = c.get("observed_ids") or []
    cases.append(dict(case=c["case"], expected_status=c["expected_status"], expected_id=exp_id,
                      observed_status=c["observed_status"], observed_ids=obs, ok=c.get("ok"),
                      extra_ids=[i for i in obs if i != exp_id] if exp_id else [],
                      status_match=c["expected_status"] == c["observed_status"],
                      id_match=(exp_id in obs) if exp_id else (obs == [])))
st_facts = dict(selected_cases=st.get("selected_cases"), declared_cases=len(st["cases"]),
                gate=st.get("gate"), checks_len=len(st.get("checks", [])),
                diagnostics=st.get("diagnostics"),
                ok_true=sum(1 for c in cases if c["ok"] is True),
                ok_false=[c["case"] for c in cases if c["ok"] is not True],
                multi_fail=[c["case"] for c in cases if len(c["observed_ids"]) > 1],
                id_mismatch=[c["case"] for c in cases if not c["id_match"]],
                status_mismatch=[c["case"] for c in cases if not c["status_match"]],
                zero_case_selection=(st.get("selected_cases") == 0),
                distinct_cases=len({c["case"] for c in st["cases"]}),
                input_hash_count=len(st.get("input_hashes", {})),
                input_hash_mismatch=[k for k, v in st.get("input_hashes", {}).items()
                                     if not pathlib.Path(k).exists() or sha(k) != v])

# 3. gate rows
gate_ids = [c["id"] for c in gt["checks"]]
gt_facts = dict(selected_cases=gt.get("selected_cases"), gate=gt.get("gate"),
                rows=len(gt["checks"]), ids=gate_ids,
                missing=[f"G{i:02d}" for i in range(1, 13) if f"G{i:02d}" not in gate_ids],
                statuses={c["id"]: c["status"] for c in gt["checks"]},
                input_hashes=gt.get("input_hashes"),
                diagnostics=gt.get("diagnostics"),
                cases=gt.get("cases"))

# 4. C1/C2 exit codes + logs
cmds = []
for c in man["commands"]:
    log = REPO / c["log"]; rep = REPO / c["report"]
    data = log.read_bytes() if log.exists() else b""
    cmds.append(dict(id=c["id"], suite=c["suite"], case=c["case"], expected_exit=c["expected_exit"],
                     observed_exit=c["observed_exit"], selected_cases=c["selected_cases"],
                     observed_gate=c["observed_gate"], log_exists=log.exists(),
                     log_bytes=len(data), log_lines=data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1),
                     log_content=data.decode("utf-8", "replace").strip(),
                     report_exists=rep.exists(), report_bytes=rep.stat().st_size if rep.exists() else None,
                     argv_len=len(c["argv"]), has_timeout=("timeout" in c["argv"]),
                     python=c["argv"][2] if len(c["argv"]) > 2 else None))
exec_fail = [c["id"] for c in cmds if c["observed_exit"] != 0 or not c["log_exists"]]

# 5. checker hash
chk = dict(frozen=sha(PKG / "check_answer.py"), working=sha(WORK["check_answer.py"]),
           manifest=man["inputs"]["check_answer.py"],
           declared_working=prov.get("checker_sha256_working"),
           declared_frozen=prov.get("checker_sha256_frozen"))
chk["all_equal"] = len(set(chk[k] for k in ("frozen", "working", "manifest", "declared_working", "declared_frozen"))) == 1

out = dict(schema="egg-drop-integrity-facts-v1", package=str(PKG.relative_to(REPO)),
           manifest=dict(input_count_declared=man["input_count"], entries=rows,
                         count=len(rows), mismatches=MIS,
                         input_hashes_sha256=man.get("input_hashes_sha256"),
                         provenance_source_matches=prov.get("source_matches_frozen"),
                         post_run_mismatches=man.get("post_run_integrity", {}).get("post_run_mismatches"),
                         post_run_match=man.get("post_run_integrity", {}).get("post_run_hashes_match")),
           working_files=work,
           input_hashes_txt=dict(lines=len(input_hashes_txt), entries=len(ih),
                                 mismatch=ih_mismatch, missing=missing_in_ih),
           selftest=dict(facts=st_facts, cases=cases),
           gate=gt_facts,
           commands=cmds, command_failures=exec_fail,
           checker=chk)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "integrity.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print("manifest entries:", len(rows), "mismatches:", MIS)
print("working:", {k: v["all_three_equal"] for k, v in work.items()})
print("input-hashes.txt:", len(ih), "mismatch:", ih_mismatch, "missing:", missing_in_ih)
print("selftest:", st_facts["selected_cases"], st_facts["declared_cases"], st_facts["ok_true"],
      "ok_false", st_facts["ok_false"], "multi", st_facts["multi_fail"], "idmm", st_facts["id_mismatch"],
      "statusmm", st_facts["status_mismatch"])
print("gate:", gt_facts["rows"], gt_facts["missing"], gt_facts["statuses"])
print("cmds:", [(c["id"], c["observed_exit"], c["log_bytes"], c["log_lines"], c["log_content"]) for c in cmds])
print("checker:", chk)
print("selftest input hashes key sample:", list(st.get("input_hashes", {}).items())[:2])
