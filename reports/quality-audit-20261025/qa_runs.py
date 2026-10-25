import csv, json, sys
from pathlib import Path
ROOT = Path.home()/"cwe-bench"; JOBS = Path.home()/".tb-graders/cwe/jobs"
rows = json.load(open("/tmp/qa/qa_tasks.json"))
keep = {r["slug"] for r in rows if "BREAKER" in r["verdict"] or ("rejected" in r["verdict"] and "both" not in r["verdict"])}
trials = [t for t in csv.DictReader(open(ROOT/"build/audit/trials.tsv"), delimiter="\t") if t["task"] in keep]
out = {}
for t in trials:
    d = JOBS/t["job"]/t["trial"]
    g = d/t["grading"] if t["grading"] != "original" else d
    res = json.load(open(g/"verifier"/"results.json")) if (g/"verifier"/"results.json").is_file() else {}
    fails = [f"{grp}:{k}" for grp in ("security","functional") for k,v in (res.get(grp) or {}).items() if v != "pass"]
    pms = sorted(d.glob("postmortem-*/POSTMORTEM.json"))
    v = (json.load(open(pms[-1])).get("verdict") or {}) if pms else {}
    out.setdefault(t["task"], []).append({"model": "deepseek" if "deepseek" in t["model"] else "mimo", "start": t["start_utc"],
        "reward": t["reward"], "timed_out": t["timed_out"], "grading": t["grading"], "failing": fails,
        "audit": {k: v.get(k) for k in ("trustworthy","attribution","confidence")}, "audit_summary": (v.get("summary") or "")[:600]})
json.dump(out, open("/tmp/qa/qa_runs.json","w"), indent=1); print(len(out), "tasks")
