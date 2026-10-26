#!/usr/bin/env python3
"""Ledger of the three-step scale run (owner request 2026-10-26). Run on the VM from ~/cwe-bench; the heartbeat runs it.

    python3 pipelines/router/scale_ledger.py

Writes reports/scale-run/LEDGER.md (summary + one row per task) and reports/scale-run/ledger.tsv. Verdicts come ONLY
from build/audit/ledger.md (common/audit/audit_results.py, rebuilt here), gate state from the build markers, fairness
from common/fairness/fairness_verdict.py (which includes human decisions), audit counts from the newest postmortem of
each graded run. Batches: pipelines/router/out/batches/*.txt.
"""
import csv, glob, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(os.path.expanduser("~/cwe-bench")); os.chdir(ROOT)
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
OUT = ROOT / "reports" / "scale-run"; OUT.mkdir(parents=True, exist_ok=True)

r = subprocess.run([sys.executable, "common/audit/audit_results.py"], capture_output=True, text=True)
ledger_ok = r.returncode == 0
led = {}
for l in open("build/audit/ledger.md").read().split("## All tasks")[1].splitlines():
    c = [x.strip() for x in l.split("|")]
    if len(c) > 5:
        led[c[2]] = (c[3].replace("*", ""), c[4].replace("*", ""), c[5].replace("*", ""))
trials = list(csv.DictReader(open("build/audit/trials.tsv"), delimiter="\t"))


def step_of(slug, batch_line):
    if "dry run" in batch_line:
        return "dry run"
    if slug.startswith("stk-"):
        return "1 stacking"
    if slug.endswith("-s2"):
        return "2 sibling"
    if slug.endswith("-s3"):
        return "3 sibling"
    return "?"


def gate(slug):
    b = ROOT / "build" / slug
    for m, k in ((".sound", "sound"), (".unsound", "unsound"), (".gate_error", "gate error"), (".listing_fail", "listing hold")):
        if (b / m).exists():
            return k
    logs = "".join((b / f).read_text(errors="replace") for f in ("stack_pipeline.log", "pipeline.log") if (b / f).exists())
    if "STOP: no manifest" in logs:
        return "declined by builder"
    if not (b / "end_utc.txt").exists():
        return "building" if (b / "start_utc.txt").exists() else "queued"
    return "checks or re-gate pending"


def verdict(slug):
    ds, mm, v = led.get(slug, ("", "", ""))
    f = lambda x: x.startswith("failed")
    s = lambda x: x.startswith("SOLVED")
    if "BREAKER" in v:
        return "BOTH-MODEL BREAKER"
    if s(ds) and s(mm):
        return "solved by both"
    if s(mm) and f(ds):
        return "DeepSeek-only breaker"
    if s(ds) and f(mm):
        return "MiMo-only breaker"
    if s(ds) or s(mm):
        return "not a breaker (one solved; other open)"
    if f(ds) or f(mm):
        return "one model 0/3, other open"
    return "trialling" if slug in led else "-"


def audits(slug):
    trusted = untrusted = pending = 0
    for t in trials:
        if t["task"] != slug or t["reward"] in ("", None) or float(t["reward"]) == 1.0:
            continue
        pms = sorted((JOBS / t["job"] / t["trial"]).glob("postmortem-*/POSTMORTEM.json"))
        if not pms:
            pending += 1; continue
        v = (json.loads(pms[-1].read_text()).get("verdict") or {})
        if v.get("trustworthy") is True:
            trusted += 1
        else:
            untrusted += 1
    return trusted, untrusted, pending


def is_breaker(v):
    return v in ("BOTH-MODEL BREAKER", "DeepSeek-only breaker", "MiMo-only breaker")


def fairness(slug):
    if not (ROOT / "build" / slug / "FAIRNESS.md").exists():
        return "-"
    o = subprocess.run([sys.executable, "common/fairness/fairness_verdict.py", slug], capture_output=True, text=True).stdout.strip()
    return o.replace("(gate_a)", "").replace("(gate_a; ", "(")[:90]


rows = []
for bf in sorted(glob.glob("pipelines/router/out/batches/*.txt")):
    batch = Path(bf).stem
    for line in open(bf):
        slug = line.split("#")[0].strip()
        if not slug:
            continue
        ds, mm, _ = led.get(slug, ("", "", ""))
        tr, un, pe = audits(slug)
        removed = sorted(p.name for p in (ROOT / "build" / slug).glob("removed-tests-*"))
        rows.append(dict(task=slug, batch=batch, step=step_of(slug, line), gate=gate(slug), deepseek=ds or "-",
                         mimo=mm or "-", verdict=verdict(slug), audits=f"{tr} trusted / {un} untrusted / {pe} pending",
                         fairness=fairness(slug), notes=("tests removed (" + ", ".join(removed) + ")") if removed else ""))

with open(OUT / "ledger.tsv", "w") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t"); w.writeheader(); w.writerows(rows)

from collections import Counter
md = [f"# Scale-run ledger", "",
      f"_Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} by pipelines/router/scale_ledger.py from "
      f"build/audit/ledger.md{'' if ledger_ok else ' (WARNING: ledger rebuild failed; verdicts may be stale)'}._", "",
      "Verdicts: both models must fail 3/3 with every failing run audited trustworthy (solves are counted without audit, "
      "owner rule 2026-10-25); a breaker is final once fairness is READY (human decisions included).", ""]
md += ["## Summary", "", "| | " + " | ".join(sorted({r['batch'] for r in rows})) + " | all |", "|---|" + "---|" * (len({r['batch'] for r in rows}) + 1)]
batches = sorted({r["batch"] for r in rows})
for key, label in (("verdict", "Verdict"), ("gate", "Gate")):
    vals = Counter(r[key] for r in rows)
    for v, _ in vals.most_common():
        md.append(f"| {label}: {v} | " + " | ".join(str(sum(1 for r in rows if r['batch'] == b and r[key] == v)) for b in batches)
                  + f" | {vals[v]} |")
md += ["", "## Breakers", "", "| Task | Step | Batch | DeepSeek | MiMo | Audits | Fairness |", "|---|---|---|---|---|---|---|"]
for r in rows:
    if is_breaker(r["verdict"]):
        md.append(f"| {r['task']} | {r['step']} | {r['batch']} | {r['verdict']} — {r['deepseek'][:40]} | {r['mimo'][:40]} | {r['audits']} | {r['fairness']} |")
md += ["", "## All tasks", "", "| Task | Batch | Step | Gate | DeepSeek | MiMo | Verdict | Audits | Fairness | Notes |",
       "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append("| " + " | ".join(str(r[k]).replace("|", "/") for k in ("task", "batch", "step", "gate", "deepseek", "mimo", "verdict", "audits", "fairness", "notes")) + " |")
(OUT / "LEDGER.md").write_text("\n".join(md) + "\n")
print(f"wrote {OUT / 'LEDGER.md'}: {len(rows)} tasks; breakers: "
      + ", ".join(r["task"] + " (" + r["verdict"] + ")" for r in rows if is_breaker(r["verdict"])))
