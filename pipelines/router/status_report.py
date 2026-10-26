#!/usr/bin/env python3
"""Full status of the scale run, for the heartbeat (2026-10-26). Run on the VM from the repo root:

    python3 -I pipelines/router/status_report.py            # report; remembers what it printed
    python3 -I pipelines/router/status_report.py --no-save   # report without updating the "since last" memory

Per batch (pipelines/router/out/batches/*.txt): build and gate state of every task, then trial verdicts from the
ledger (build/audit/ledger.md, regenerated here). Then audits owed, queues, the machine, and what changed or looks
wrong since the previous report (state: pipelines/router/out/queue/status_last.json).
"""
import collections, glob, json, os, re, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
os.chdir(ROOT)
LAST = "pipelines/router/out/queue/status_last.json"


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


# Not -I: isolated mode drops the script's own folder from sys.path, so audit_results.py could not import its
# helpers and the report read a stale ledger (2026-10-26). A failure is reported, never hidden.
_ar = subprocess.run([sys.executable, "common/audit/audit_results.py"], capture_output=True, text=True)
LEDGER_ERR = "" if _ar.returncode == 0 else (_ar.stderr.strip().splitlines() or ["?"])[-1][:200]
led = {}
for l in open("build/audit/ledger.md").read().split("## All tasks")[1].splitlines():
    c = [x.strip() for x in l.split("|")]
    if len(c) > 5:
        led[c[2]] = (c[3], c[4], c[5])

running = sh("ps -eo args")
def proc_has(s, pat):
    return any(pat in a and re.search(rf"(\s|/){re.escape(s)}(\s|$)", a) for a in running.splitlines())


def gate_state(s):
    b = f"build/{s}"
    for m, k in ((".sound", "sound"), (".unsound", "unsound"), (".gate_error", "gate error"), (".listing_fail", "held at listing")):
        if os.path.exists(f"{b}/{m}"):
            return k
    logs = "".join(open(f"{b}/{f}", errors="replace").read() for f in ("stack_pipeline.log", "pipeline.log") if os.path.exists(f"{b}/{f}"))
    if proc_has(s, "regate.sh"):
        return "re-gating"
    if "STOP: no manifest" in logs or "stopped/failed" in logs:
        return "builder declined (not buildable)"
    if "BUILD-INCOMPLETE" in logs:
        return "build incomplete"
    if not os.path.exists(f"{b}/end_utc.txt"):
        return "building" if os.path.exists(f"{b}/start_utc.txt") else "waiting to build"
    if proc_has(s, "postbuild.sh") or proc_has(s, "gate_one_ds.sh"):
        return "in post-build checks"
    return "waiting for re-gate"


def trial_state(s):
    ds, mm, v = led.get(s, ("", "", ""))
    f = lambda c: c.startswith("**failed")
    if "BREAKER" in v:
        return "BREAKER (both 0/3)"
    if "both solved" in v:
        return "solved by both"
    if "rejected" in v:
        if f(ds):
            return "DeepSeek-only breaker (MiMo solved)"
        if f(mm):
            return "MiMo-only breaker (DeepSeek solved)"
        return "one model solved, other still running"
    if not s in led:
        return "trials not started"
    if f(ds) or f(mm):
        return "one model 0/3, other still running"
    return "trials under way"


now = {}
out = []
for bf in sorted(glob.glob("pipelines/router/out/batches/*.txt")):
    name = os.path.basename(bf)[:-4]
    slugs = [l.split("#")[0].strip() for l in open(bf) if l.split("#")[0].strip()]
    g = collections.defaultdict(list); t = collections.defaultdict(list)
    for s in slugs:
        gs = gate_state(s); g[gs].append(s); now[s] = gs
        if gs == "sound":
            ts = trial_state(s); t[ts].append(s); now[s] = "sound/" + ts
    out.append(f"== {name}: {len(slugs)} tasks")
    out.append("  build/gate: " + "; ".join(f"{k} {len(v)}" for k, v in sorted(g.items(), key=lambda x: -len(x[1]))))
    for k in ("unsound", "gate error", "held at listing", "builder declined (not buildable)", "build incomplete"):
        if g.get(k):
            out.append(f"    {k}: {', '.join(g[k])}")
    if t:
        out.append("  trials (of sound): " + "; ".join(f"{k} {len(v)}" for k, v in sorted(t.items(), key=lambda x: -len(x[1]))))
        for k in ("BREAKER (both 0/3)", "DeepSeek-only breaker (MiMo solved)", "MiMo-only breaker (DeepSeek solved)", "one model 0/3, other still running"):
            if t.get(k):
                out.append(f"    {k}: {', '.join(t[k])}")

pend = sh("python3 common/audit/postmortem.py pending 2>/dev/null | wc -l")
qs = []
for f in sorted(glob.glob("pipelines/router/out/queue/*.state.json")):
    try:
        st = json.load(open(f))
        qs.append(f"{st['batch']}: builds {st['builds_running']} running + {st['builds_waiting']} waiting, trials {st['trials_running']}")
    except Exception:
        pass
rg = sh("grep -c '\\[start\\]' pipelines/router/out/queue/regate-b1.log"), sh("grep -c '\\[finish\\]' pipelines/router/out/queue/regate-b1.log")
out.append(f"== queues: {' | '.join(qs)} | re-gate queue started {rg[0]}, finished {rg[1]} | failing runs awaiting audit: {pend}")
load = open("/proc/loadavg").read().split()[0]
disk = sh("df -BG / | tail -1 | awk '{print $4}'")
n_harbor = sh("pgrep -fc 'harbor run'")
n_cont = sh("docker ps -q 2>/dev/null | wc -l")
n_agents = sh("pgrep -fc 'claude -p'")
out.append(f"== machine: load {load} (64 CPUs) | disk free {disk} | gate/trial Harbor runs {n_harbor} | "
           f"containers {n_cont} | agents {n_agents}")

# what changed or looks wrong
alerts = []
prev = json.load(open(LAST)) if os.path.exists(LAST) else {}
for s, st in now.items():
    p = prev.get(s)
    if p and p != st and any(w in st for w in ("unsound", "gate error", "declined", "incomplete", "BREAKER", "breaker", "held")):
        alerts.append(f"{s}: {p} -> {st}")
guard = sh("grep -c stopped build/audit/orphan_builder_guard.log") or "0"
if guard != str(prev.get("__guard__", "0")):
    alerts.append(f"orphan guard stopped a builder (total {guard}; see build/audit/orphan_builder_guard.log)")
now["__guard__"] = guard
if float(load) > 300:
    alerts.append(f"LOAD HIGH: {load}")
if disk and int(disk.rstrip("G")) < 150:
    alerts.append(f"DISK LOW: {disk}")
for s, st in now.items():
    if st == "waiting for re-gate" and not proc_has(s, "regate"):
        pass
# Disk janitor (owner rule 2026-10-26): it only reports; every cleanup waits for the owner's approval.
jr = "build/audit/janitor/LATEST_REPORT.txt"
if os.path.exists(jr):
    rep = open(jr).read().splitlines()
    cand = os.path.basename(rep[0].split("apply ")[-1]) if rep else ""
    applied = open("build/audit/janitor/applied.log").read() if os.path.exists("build/audit/janitor/applied.log") else ""
    if cand and cand not in applied:
        out.append("== janitor report waiting for owner approval: " + " | ".join(x.strip() for x in rep[1:5]))
jl = sh("ps -eo args | grep -c '[d]isk_janitor.sh loop'")
if jl == "0":
    alerts.append("janitor report loop is not running")
if LEDGER_ERR:
    alerts.append(f"LEDGER NOT REBUILT (trial results may be stale): {LEDGER_ERR}")
out.append("== new or odd since last report: " + ("; ".join(alerts) if alerts else "nothing"))
print(time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()))
print("\n".join(out))
if "--no-save" not in sys.argv:
    json.dump(now, open(LAST, "w"))
