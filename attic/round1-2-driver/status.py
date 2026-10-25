#!/usr/bin/env python3
"""One-screen status of the build/trial pipeline. Reads only the filesystem."""
import glob
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # cwe-bench/
BUILD = ROOT / "build"
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
STAGES = ["static", "nop", "oracle", "patches"]


def gate_progress(slug):
    rep = BUILD / slug / "gate_report.json"
    if not rep.is_file():
        return None
    r = json.loads(rep.read_text())
    done = [s for s in STAGES if s in r.get("stages", {})]
    if r.get("passed"):
        return "gate PASSED"
    if "failure" in r:
        return f"gate FAILED at {STAGES[len(done)] if len(done) < 4 else '?'}: {r['failure'][:80]}"
    pct = int(100 * len(done) / len(STAGES))
    return f"gate {pct}% ({'/'.join(done) or 'starting'})"


def trial_summary(slug):
    out = {}
    for model in ("deepseek", "mimo"):
        rewards = []
        for job in sorted(JOBS.glob(f"{slug}-{model}-*/")):
            for res in job.glob("*/result.json"):
                try:
                    vr = json.loads(res.read_text()).get("verifier_result") or {}
                    rewards.append((vr.get("rewards") or {}).get("reward"))
                except Exception:
                    pass
        if rewards:
            passes = sum(1 for x in rewards if x == 1.0)
            out[model] = f"{passes}/{len(rewards)} pass"
    return out


def machine():
    free = "?"
    try:
        du = subprocess.run(["df", "-g", str(Path.home())], capture_output=True, text=True)
        free = du.stdout.splitlines()[1].split()[3] + "G free"
    except Exception:
        pass
    cont = "?"
    try:
        ps = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True, timeout=10)
        cont = f"{len([x for x in ps.stdout.split() if x])} containers"
    except Exception:
        pass
    return f"{free}, {cont}"


def main():
    q = json.loads((BUILD / "queue.json").read_text())["queue"]
    print(f"=== pipeline status {time.strftime('%H:%M:%S')} | {machine()} ===")
    counts = {}
    for item in q:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print("  " + "  ".join(f"{k}:{v}" for k, v in sorted(counts.items())))
    for item in q:
        if item["status"] == "pending":
            continue
        line = f"  [{item['priority']:>2}] {item['slug']:<22} {item['status']:<9}"
        gp = gate_progress(item["slug"])
        if gp:
            line += " " + gp
        ts = trial_summary(item["slug"])
        if ts:
            line += "  trials: " + ", ".join(f"{m} {v}" for m, v in ts.items())
        print(line)
    pend = [i["slug"] for i in q if i["status"] == "pending"]
    if pend:
        print(f"  pending ({len(pend)}): {', '.join(pend[:6])}{' ...' if len(pend) > 6 else ''}")


if __name__ == "__main__":
    main()
