#!/usr/bin/env python3
"""Quality-audit data pack: one row per trialled task (injection / stacking / precision-validation).
Run on the VM from ~/cwe-bench. Reads build/audit/{ledger.md,trials.tsv}, build/<slug>/, tasks/<slug>/ and the
postmortems under ~/.tb-graders/cwe/jobs. Writes qa_tasks.tsv and qa_tasks.json in the cwd given as argv[1]."""
import csv, glob, json, os, re, subprocess, sys
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / "cwe-bench"
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
OUT = Path(sys.argv[1])


def jl(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None


def toml_field(slug, key):
    t = ROOT / "tasks" / slug / "task.toml"
    if not t.is_file():
        return ""
    m = re.search(rf'^\s*{key}\s*=\s*"([^"]*)"', t.read_text(), re.M)
    return m.group(1) if m else ""


def utc(p):
    try:
        s = Path(p).read_text().strip()
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


# ledger rows
ledger = {}
sec = (ROOT / "build/audit/ledger.md").read_text().split("## All tasks")[1]
for line in sec.splitlines():
    c = [x.strip() for x in line.split("|")]
    if len(c) > 5 and c[1] in ("injection", "stacking", "precision-validation", "mined"):
        ledger[c[2]] = {"track": c[1], "ds": c[3], "mm": c[4], "verdict": c[5]}

trials = list(csv.DictReader(open(ROOT / "build/audit/trials.tsv"), delimiter="\t"))

rows = []
for slug, L in sorted(ledger.items()):
    if L["track"] == "mined":
        continue
    b = ROOT / "build" / slug
    m = jl(b / "manifest.json") or {}
    traps = m.get("traps") or []
    br = jl(b / "build-run.json") or {}
    us = br.get("usage") or {}
    st, en = utc(b / "start_utc.txt"), utc(b / "end_utc.txt")
    build_h = round((en - st).total_seconds() / 3600, 2) if st and en and en > st else ""
    tr = [t for t in trials if t["task"] == slug]
    agent_min = sum(float(t["agent_min"]) for t in tr if t["agent_min"] not in ("", None))
    # fairness verdict via the official reader
    try:
        fv = subprocess.run(["python3", "common/fairness/fairness_verdict.py", slug], cwd=ROOT,
                            capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        fv = "?"
    marker = next((k for k in (".sound", ".unsound", ".gate_error") if (b / k).exists()), "")
    # audits of this task's runs (newest postmortem per trial)
    confs = {"high": 0, "medium": 0, "low": 0}
    attrib = {}
    for t in tr:
        pms = sorted((JOBS / t["job"] / t["trial"]).glob("postmortem-*/POSTMORTEM.json"))
        if not pms:
            continue
        v = (jl(pms[-1]) or {}).get("verdict") or {}
        if v.get("trustworthy") is True:
            confs[v.get("confidence", "low")] = confs.get(v.get("confidence", "low"), 0) + 1
        attrib[v.get("attribution", "?")] = attrib.get(v.get("attribution", "?"), 0) + 1
    repairs = {
        "testfix": len(list(b.glob("testfix-*"))),
        "fairfix": len(list(b.glob("fairfix*"))) + len(list(b.glob("FAIRFIX*"))),
        "upgrade": int((b / "upgrade-run.json").exists()),
        "fairness_prev": len(list(b.glob("FAIRNESS.md.prev-*"))),
        "regrades": sum(len(list((JOBS / t["job"] / t["trial"]).glob("regrade-*"))) for t in tr),
    }
    rows.append({
        "slug": slug, "track": L["track"], "verdict": L["verdict"].replace("*", ""),
        "ds": L["ds"].replace("*", ""), "mm": L["mm"].replace("*", ""),
        "cwe": toml_field(slug, "cwe_id"), "language": toml_field(slug, "language").lower(),
        "repo": toml_field(slug, "repo").replace("https://github.com/", ""),
        "source": toml_field(slug, "source"), "n_traps": len(traps),
        "trap_levers": " / ".join((t.get("lever") or t.get("shape") or "")[:70] for t in traps),
        "stacking": json.dumps(m.get("stacking"))[:300] if m.get("stacking") else "",
        "build_h": build_h, "build_out_tok": us.get("output_tokens", ""),
        "build_cache_read_tok": us.get("cache_read_input_tokens", ""),
        "n_runs": len(tr), "trial_agent_min": round(agent_min),
        "fairness": fv, "gate": marker,
        "audit_trusted_high": confs["high"], "audit_trusted_medium": confs["medium"],
        "audit_attrib": json.dumps(attrib), "repairs": json.dumps(repairs),
    })

OUT.mkdir(parents=True, exist_ok=True)
json.dump(rows, open(OUT / "qa_tasks.json", "w"), indent=1)
with open(OUT / "qa_tasks.tsv", "w") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows")
