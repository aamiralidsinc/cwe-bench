#!/usr/bin/env python3
"""Keep the KEEP earliest post-build gates of scale-b1; stop the gate processes (gate_one_ds/gate.py/harbor + their
containers) of the other tasks. Blind fix, listing, builders and pipelines are not touched. --apply to act."""
import os, re, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)
os.chdir(paths.ROOT)
KEEP = int(os.environ.get("KEEP", "10")); apply = "--apply" in sys.argv
slugs = [l.split("#")[0].strip() for l in open("pipelines/stacking/out/scale-b1.txt") if l.split("#")[0].strip()]
act = []
for s in slugs:
    p = f"build/{s}/postbuild.log"
    if os.path.isfile(p) and "RESULT" not in open(p).read():
        act.append((open(p).readline()[:20], s))
act.sort(); keep = [s for _, s in act[:KEEP]]; stop = [s for _, s in act[KEEP:]]
print(f"post-build running: {len(act)}; keep {len(keep)}; stop gates of {len(stop)}")
procs = []
for pid in os.listdir("/proc"):
    if not pid.isdigit(): continue
    try: a = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
    except Exception: continue
    procs.append((int(pid), a))
def gate_procs(s):
    b = re.escape(s)
    pats = [rf"gate_one_ds\.sh {b}(\s|$)", rf"common/gate/gate\.py {b}(\s|$)", rf"harbor run .*(/|\s){b}(\s|$)",
            rf"--project-name {re.escape(s.lower())}__"]
    return [pid for pid, a in procs if any(re.search(p, a) for p in pats)
            and "run_blindfix" not in a and "claude" not in a and "listing" not in a]
total = 0
for s in stop:
    pids = gate_procs(s); total += len(pids)
    if apply:
        for pid in pids:
            try: os.kill(pid, 9)
            except Exception: pass
print(f"gate processes {'killed' if apply else 'to kill'}: {total}")
if apply:
    time.sleep(3)
    names = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True).stdout.split()
    rm = [n for n in names for s in stop if n.startswith(s.lower() + "__") or n.startswith(s + "__")]
    for i in range(0, len(rm), 40):
        subprocess.run(["docker", "rm", "-f"] + rm[i:i+40], capture_output=True)
    print("containers removed:", len(rm))
    open("pipelines/router/out/queue/regate-b1.txt", "w").write("\n".join(stop) + "\n")
    print("re-gate list: pipelines/router/out/queue/regate-b1.txt")
print("keep:", keep)
