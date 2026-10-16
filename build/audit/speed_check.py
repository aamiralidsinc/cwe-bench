#!/usr/bin/env python3
"""15-minute speed check for the 2026-10-16 repair batch (user asked for it).

    python3 build/audit/speed_check.py

Prints: running gates/regrades with elapsed time, jobs waiting for a slot, every gate stage finished
in the last 20 min with its image-build (environment_setup) and test (verifier) time, live trials,
disk free and VM load. Expectation with a warm cache: image build under ~2 min per stage, whole gate
10-30 min. A stage whose image build took over 5 min is flagged SLOW.
"""
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

GATE_JOBS = Path.home() / ".tb-graders/cwe/gate-jobs"
SLOTS = Path.home() / ".tb-graders/cwe/slots/MAX"


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def mins(a, b):
    return f"{(b - a).total_seconds() / 60:.1f}" if a and b else "?"


now = datetime.now(timezone.utc)
print(f"now {now:%H:%M} UTC | slot cap {SLOTS.read_text().strip() if SLOTS.exists() else '?'}")

ps = sh("ps -axo etime,command")
running = [l for l in ps.splitlines() if re.search(r"builder/gate\.py|regrade_from_code\.py", l)
           and "slot.py" not in l and "zsh -c" not in l and "grep" not in l]
print(f"\nrunning ({len(running)}):")
for l in running:
    et, cmd = l.strip().split(None, 1)
    m = re.search(r"(gate\.py \S+|regrade_from_code\.py \S+)", cmd)
    print(f"  {et:>9}  {m.group(1).replace(str(Path.home()) + '/.tb-graders/cwe/jobs/', '') if m else cmd[:80]}")

waiting = [l for l in ps.splitlines() if re.search(r"Python build/slot\.py", l) and "zsh -c" not in l]
held = {re.search(r"(gate\.py \S+|regrade_from_code\.py \S+)", l).group(1) for l in running
        if re.search(r"(gate\.py \S+|regrade_from_code\.py \S+)", l)}
wait = [re.search(r"-- (.*)", l).group(1) for l in waiting if re.search(r"-- (.*)", l)]
wait = [w for w in wait if not any(h in w for h in held)]
print(f"\nwaiting for a slot ({len(wait)}):")
for w in wait:
    m = re.search(r"(gate\.py \S+|regrade_from_code\.py \S+)", w)
    print("  " + (m.group(1).replace(str(Path.home()) + "/.tb-graders/cwe/jobs/", "") if m else w[:80]))

print("\ngate stages finished in the last 20 min (image build / tests, minutes):")
slow = 0
for job in sorted(GATE_JOBS.glob("*/")):
    for t in job.glob("*/result.json"):
        try:
            r = json.loads(t.read_text())
        except ValueError:
            continue
        fin = ts(r.get("finished_at"))
        if not fin or (now - fin).total_seconds() > 1200:
            continue
        env = r.get("environment_setup") or {}
        ver = r.get("verifier") or {}
        b = mins(ts(env.get("started_at")), ts(env.get("finished_at")))
        v = mins(ts(ver.get("started_at")), ts(ver.get("finished_at")))
        rew = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        flag = "  SLOW" if b != "?" and float(b) > 5 else ""
        slow += bool(flag)
        print(f"  {job.name:55} build {b:>5}  tests {v:>5}  reward {rew}{flag}")
print(f"  -> {slow} slow stage(s)")

trials = sorted({m.group(0) for m in re.finditer(r"trial\.py \S+ --models \S+ \S+ \S+ --first-run \d+", ps)})
print(f"\nlive trials ({len(trials)}): " + "; ".join(t.replace("trial.py ", "").replace(" --max-runs 1", "") for t in trials))
print("disk: " + sh("colima ssh -- df -h /var/lib/docker | tail -1").split()[3] + " free"
      + " | load: " + sh("colima ssh -- cat /proc/loadavg").split()[0] + " on 8 CPUs")
