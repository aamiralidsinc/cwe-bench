#!/usr/bin/env python3
"""Run DeepSeek + MiMo trials across many tasks at 2+2 concurrency.

Keeps at most 2 deepseek and 2 mimo trial.py jobs running at once (counting
jobs started outside this fleet too, via process check, so it never exceeds the
cap or double-launches). Skips (task,model) already done (trial_detail_<model>
.json exists). Logs each job to build/trial-logs/<task>__<model>.log and
rewrites build/trial-matrix.md after every change.

    python3 build/trial_fleet.py <task1> <task2> ...

Each job: `python3 build/trial.py <task> --models <model> --no-verdict`
(per-model, early-exit on a solve, infeasible-stop on a double-None run 1).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGDIR = ROOT / "build" / "trial-logs"
MODELS = ("deepseek", "mimo")
MAX_PER_MODEL = 2
POLL = 20


def done(task, model):
    return (ROOT / "build" / task / f"trial_detail_{model}.json").is_file()


def running(task, model):
    return bool(subprocess.run(["pgrep", "-f", f"trial.py {task} --models {model}"],
                               capture_output=True, text=True).stdout.strip())


def read_detail(task, model):
    p = ROOT / "build" / task / f"trial_detail_{model}.json"
    if not p.is_file():
        return None
    d = json.loads(p.read_text())
    pm = (d.get("per_model") or {}).get(model, {})
    return {"verdict": d.get("verdict", "?"),
            "pass": pm.get("pass", 0), "fail": pm.get("fail", 0), "err": pm.get("error", 0)}


def cell(task, model):
    d = read_detail(task, model)
    if d is None:
        return "running…" if running(task, model) else "—"
    v = (d["verdict"] or "").lower()
    if "solved" in v or d["pass"]:
        return "SOLVED"
    if d["fail"]:                       # real completed non-solve runs
        return f"failed {d['fail']}/3" + (f"+{d['err']}e" if d["err"] else "")
    return "infeasible"                 # pass==0 and fail==0 -> only errors/None


def write_matrix(tasks):
    L = ["# Trial matrix (per-model)", "", f"_updated {time.strftime('%H:%M:%S')}_", "",
         "BREAKER = both models fail all runs (no solve).", "",
         "| task | DeepSeek | MiMo | verdict |", "|---|---|---|---|"]
    for t in tasks:
        ds, mm = cell(t, "deepseek"), cell(t, "mimo")
        if ds.startswith("failed") and mm.startswith("failed"):
            v = "**BREAKER**"
        elif ds == "SOLVED" or mm == "SOLVED":
            v = "rejected (solved)"
        elif "infeasible" in (ds, mm) and "running" not in ds + mm and "—" not in (ds, mm):
            v = "infeasible"
        else:
            v = "in progress"
        L.append(f"| {t} | {ds} | {mm} | {v} |")
    (ROOT / "build" / "trial-matrix.md").write_text("\n".join(L) + "\n")


def live_count(tasks, model):
    return sum(1 for t in tasks if running(t, model))


def main():
    tasks = sys.argv[1:]
    if not tasks:
        print("usage: trial_fleet.py <task> ..."); return 2
    LOGDIR.mkdir(parents=True, exist_ok=True)
    pending = [(t, m) for t in tasks for m in MODELS if not done(t, m) and not running(t, m)]
    handles = []
    print(f"[fleet] {len(pending)} jobs queued; 2+2 concurrency; tasks={tasks}", flush=True)
    while True:
        for model in MODELS:
            while live_count(tasks, model) < MAX_PER_MODEL:
                nxt = next(((t, m) for (t, m) in pending if m == model and not done(t, m)), None)
                if nxt is None:
                    break
                t, _ = nxt
                pending.remove(nxt)
                log = LOGDIR / f"{t}__{model}.log"
                handles.append(subprocess.Popen(
                    [sys.executable, str(ROOT / "build" / "trial.py"), t, "--models", model, "--no-verdict"],
                    stdout=open(log, "w"), stderr=subprocess.STDOUT))
                print(f"[fleet] launched {t}/{model} -> {log.name}", flush=True)
                time.sleep(2)  # let pgrep see it before recounting
        write_matrix(tasks)
        any_running = any(running(t, m) for t in tasks for m in MODELS)
        if not pending and not any_running:
            break
        time.sleep(POLL)
    write_matrix(tasks)
    print("[fleet] complete; see build/trial-matrix.md", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
