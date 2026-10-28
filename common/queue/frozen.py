"""Frozen pipeline processes: builders, gates and trials stopped by SIGSTOP (state T in /proc/<pid>/stat).

A stopped process keeps its timers running against the wall clock. `timeout 18000` around a builder (run_build.sh)
fires the moment the builder is resumed if five hours have passed meanwhile, so a frozen builder is cut on resume. Pausing
the pipeline means stopping new starts (queue `enabled = false`, the dispatcher, the diskguard floors), never freezing
running work (docs/WORK-QUEUE.md, "Pausing safely").

scan() lists the pipeline processes that are stopped right now. The monitor (monitor.py) raises `process_frozen` and
an urgent `process.frozen` event when one stays stopped for frozen_after_sec; preflight reports any as CRITICAL.
"""
import os
import re
from pathlib import Path

# What counts as pipeline work, and how to find the task it serves.
MARKERS = ("run_build.sh", "run_pipeline.sh", "resume_pipeline.sh", "run_stack_pipeline.sh", "regate.sh",
           "postbuild.sh", "gate_one_ds.sh", "gate.py", "trial.py", "run_trial.sh", "harbor run",
           "Build one security-fix benchmark task", "run_fairness", "run_blindfix.sh")
SLUG = r"([A-Za-z0-9][A-Za-z0-9._-]*)"
TASK_RULES = (
    re.compile(r"Task: `" + SLUG + "`"),
    re.compile(r"(?:run_build|run_stack_pipeline|regate|postbuild|gate_one_ds|run_blindfix)\.sh " + SLUG),
    re.compile(r"run_pipeline\.sh \S+ " + SLUG),
    re.compile(r"resume_pipeline\.sh " + SLUG),
    re.compile(r"(?:gate|trial)\.py " + SLUG),
    re.compile(r"/tasks/" + SLUG),
)


def task_of(cmd):
    for rx in TASK_RULES:
        m = rx.search(cmd)
        if m:
            return m.group(1)
    return ""


def is_pipeline(cmd):
    return any(k in cmd for k in MARKERS)


def read_stat(path):
    """(state, starttime) from a /proc/<pid>/stat file, or (None, None)."""
    try:
        raw = Path(path).read_text()
    except OSError:
        return None, None
    rest = raw[raw.rfind(")") + 2:].split()                 # fields after "(comm)": state is field 3
    if len(rest) < 20:
        return None, None
    return rest[0], rest[19]                                 # field 22: starttime (clock ticks since boot)


def scan(proc_root="/proc"):
    """[{pid, start, task, cmd}] for pipeline processes in state T (stopped) or t (traced-stopped)."""
    out = []
    root = Path(proc_root)
    try:
        pids = [d for d in os.listdir(root) if d.isdigit()]
    except OSError:
        return out
    for pid in pids:
        state, start = read_stat(root / pid / "stat")
        if state not in ("T", "t"):
            continue
        try:
            cmd = " ".join(a.decode(errors="replace") for a in (root / pid / "cmdline").read_bytes().split(b"\0") if a)
        except OSError:
            continue
        if not is_pipeline(cmd):
            continue
        out.append({"pid": int(pid), "start": start, "task": task_of(cmd), "cmd": cmd[:200]})
    return out


class Tracker:
    """Remembers when each stopped process was first seen, so a short stop (a debugger, a ^Z) is not reported."""

    def __init__(self, scanner=scan):
        self.scanner = scanner
        self.first_seen = {}

    def frozen(self, now, after_sec):
        """[{pid, task, cmd, stopped_sec}] stopped for at least after_sec (as far as this tracker has seen)."""
        cur = {(p["pid"], p["start"]): p for p in self.scanner()}
        self.first_seen = {k: self.first_seen.get(k, now) for k in cur}
        return [dict(cur[k], stopped_sec=round(now - t)) for k, t in self.first_seen.items() if now - t >= after_sec]
