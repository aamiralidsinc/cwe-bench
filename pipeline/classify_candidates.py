#!/usr/bin/env python3
# RAW (unconfirmed, pre-postmortem) candidate classification from the authoritative
# per-run reward.json files under ~/.tb-graders/cwe/jobs/. A model SOLVES a task if ANY
# of its runs has reward==1.0 (audit_results.py's definition); else it FAILED (if it has
# >=1 graded run) or UNTRIED (no graded reward).
import json, os, re, glob, collections

JOBS = os.path.expanduser("~/.tb-graders/cwe/jobs")
pat = re.compile(r"^(?P<task>.+?)-(?P<model>deepseek|mimo)-r\d+-\d{8}-\d{6}-n\d+$")

# task -> model -> list of rewards (float or None for ungraded)
agg = collections.defaultdict(lambda: collections.defaultdict(list))

def reward_of(jobdir):
    # authoritative: <trial>/verifier/reward.json .reward, else result json
    for rj in glob.glob(os.path.join(jobdir, "**", "verifier", "reward.json"), recursive=True):
        try:
            return json.load(open(rj)).get("reward")
        except Exception:
            pass
    for res in glob.glob(os.path.join(jobdir, "**", "result.json"), recursive=True):
        try:
            r = json.load(open(res))
            return ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        except Exception:
            pass
    return None

for d in sorted(os.listdir(JOBS)):
    m = pat.match(d)
    if not m:
        continue
    agg[m["task"]][m["model"]].append(reward_of(os.path.join(JOBS, d)))

def status(rewards):
    graded = [r for r in rewards if r is not None]
    if not graded:
        return "untried"       # runs exist but none graded
    return "solve" if any(r == 1.0 for r in graded) else "fail"

both_fail, single, both_solve, partial = [], [], [], []
for task in sorted(agg):
    ds = status(agg[task].get("deepseek", []))
    mm = status(agg[task].get("mimo", []))
    nds = len(agg[task].get("deepseek", [])); nmm = len(agg[task].get("mimo", []))
    tag = f"{task}  [ds={ds} x{nds} | mm={mm} x{nmm}]"
    if ds == "fail" and mm == "fail":
        both_fail.append(tag)
    elif (ds == "fail") ^ (mm == "fail") and "solve" in (ds, mm):
        single.append(tag)
    elif ds == "solve" and mm == "solve":
        both_solve.append(tag)
    else:
        partial.append(tag)  # untried on one/both side

def dump(title, lst):
    print(f"\n### {title}: {len(lst)}")
    for x in lst:
        print("  " + x)

print(f"total tasks with >=1 trial: {len(agg)}")
dump("BOTH-FAIL (raw both-model breaker candidates)", both_fail)
dump("SINGLE-SIDE (one model failed, other solved)", single)
dump("BOTH-SOLVE (too easy -> hardening candidates)", both_solve)
dump("PARTIAL/UNTRIED (incomplete trial coverage)", partial)
