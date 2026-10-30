#!/usr/bin/env python3
"""Run audit 1 over a calibration set: at most N agents at once, started S seconds apart, with a progress file.

    python3 common/audit/audit1/calibration/batch.py <config.json>

config.json (a file, so no task names reach any command line):
    {"work": "/home/mara/scratch/audit1-cal",   # runs/<trial>/ prepared by prepare_set.py
     "trials": ["<trial>", ...],                # optional: only these (default: every runs/<trial> without AUDIT1.json)
     "parallel": 6, "stagger_sec": 30, "timeout_sec": 2700,
     "round": "r1",                             # label written to the progress file
     "archive_to": "<folder>"}                  # optional: move the previous round's outputs there first

Each agent runs as `bash <repo>/common/launch/drive.sh deepseek bash <repo>/common/audit/audit1/run_audit1.sh` with the
run folder as its working directory (not on the command line). Progress: <work>/progress.tsv (one line per event:
UTC, round, trial, event, pid, detail). About 30 s after each start the agent's liveness is checked (process alive,
stream file present) and logged. Only the pids this script started are ever signalled.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / ".cwe-bench-root").is_file())


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text())
    work = Path(cfg["work"])
    runs = work / "runs"
    rnd = cfg.get("round", "r1")
    trials = cfg.get("trials") or sorted(p.name for p in runs.iterdir()
                                         if p.is_dir() and not (p / "AUDIT1.json").exists())
    par, stagger = int(cfg.get("parallel", 6)), int(cfg.get("stagger_sec", 30))
    prog = work / "progress.tsv"

    def log(trial, event, pid="", detail=""):
        with open(prog, "a") as fh:
            fh.write(f"{now()}\t{rnd}\t{trial}\t{event}\t{pid}\t{detail}\n")

    env = dict(os.environ, AUDIT1_TIMEOUT=str(cfg.get("timeout_sec", 2700)))
    queue = list(trials)
    running = {}          # pid -> (trial, Popen, start, checked)
    last_start = 0.0
    log("-", "batch-start", os.getpid(), f"{len(queue)} runs, parallel {par}, stagger {stagger}s")
    while queue or running:
        for pid, (trial, p, t0, checked) in list(running.items()):
            rc = p.poll()
            d = runs / trial
            if rc is not None:
                a1 = {}
                try:
                    a1 = json.loads((d / "AUDIT1.json").read_text())
                except (OSError, ValueError):
                    pass
                log(trial, "end", pid, f"rc={rc} status={a1.get('status')} "
                                       f"first_try_quote={a1.get('first_try_quote_pass')} "
                                       f"wall={int(time.time() - t0)}s")
                del running[pid]
            elif not checked and time.time() - t0 >= 30:
                alive = p.poll() is None
                stream = d / "audit1-stream-1.jsonl"
                size = stream.stat().st_size if stream.exists() else -1
                log(trial, "liveness", pid, f"alive={alive} stream_bytes={size}")
                running[pid] = (trial, p, t0, True)
        if queue and len(running) < par and time.time() - last_start >= stagger:
            trial = queue.pop(0)
            d = runs / trial
            if cfg.get("archive_to"):        # keep the previous round's outputs OUTSIDE the agent's folder
                arch = Path(cfg["archive_to"]) / trial
                arch.mkdir(parents=True, exist_ok=True)
                for f in list(d.iterdir()):
                    if f.name.startswith(("AUDIT1", "DOSSIER", "QUOTECHECK", "audit1-", "prompt-")):
                        shutil.move(str(f), str(arch / f.name))
            for f in d.glob("AUDIT1.json"):
                f.unlink()
            out = open(d / "audit1-launch.log", "w")
            p = subprocess.Popen(["bash", str(REPO / "common/launch/drive.sh"), "deepseek", "bash",
                                  str(REPO / "common/audit/audit1/run_audit1.sh")],
                                 cwd=d, env=env, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            running[p.pid] = (trial, p, time.time(), False)
            last_start = time.time()
            log(trial, "start", p.pid, "")
        time.sleep(5)
    log("-", "batch-end", os.getpid(), "")


if __name__ == "__main__":
    main()
