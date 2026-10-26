#!/usr/bin/env python3
"""Emit one line per built task: slug, entry_id, repo, track, deepseek rewards, mimo rewards,
parked flag, policy-b flag. Run on the VM from the repo root. Reads BUILD-PROMPT.md (embedded screener
record has entry_id/repo), runs_<model>.log, PARKED.txt, POLICY-B-ACCEPT.txt."""
import json, os, re, glob

def rewards(slug, model):
    p = f"build/{slug}/runs_{model}.log"
    if not os.path.exists(p):
        return []
    return [float(x) for x in re.findall(r"reward=([0-9.]+)", open(p).read())]

def entry_repo_track(slug):
    bp = f"build/{slug}/BUILD-PROMPT.md"
    eid = repo = track = ""
    if os.path.exists(bp):
        t = open(bp, encoding="utf-8", errors="replace").read()
        m = re.search(r'"entry_id":\s*(\d+)', t); eid = m.group(1) if m else ""
        m = re.search(r'"repo":\s*"([^"]+)"', t); repo = m.group(1) if m else ""
        m = re.search(r"Track:\s*`?(mined|injected|stacking)", t); track = m.group(1) if m else ""
    return eid, repo, track

print("slug\tentry_id\trepo\ttrack\tdeepseek\tmimo\tparked\tpolicy_b")
for d in sorted(glob.glob("build/*/")):
    slug = d.rstrip("/").split("/")[-1]
    if not os.path.exists(f"{d}/BUILD-PROMPT.md") and not os.path.exists(f"{d}/manifest.json"):
        continue
    if slug in ("audit", "exp", "checks", "trial-logs"):
        continue
    eid, repo, track = entry_repo_track(slug)
    ds = rewards(slug, "deepseek"); mm = rewards(slug, "mimo")
    parked = "yes" if os.path.exists(f"{d}/PARKED.txt") else ""
    pb = "yes" if os.path.exists(f"{d}/POLICY-B-ACCEPT.txt") else ""
    print(f"{slug}\t{eid}\t{repo}\t{track}\t{','.join(str(x) for x in ds)}\t"
          f"{','.join(str(x) for x in mm)}\t{parked}\t{pb}")
