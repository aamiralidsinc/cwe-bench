#!/usr/bin/env python3
"""Disk-aware admission (owner decision 2026-10-27): no new image-building work starts while free disk is below
a floor. Work that is already running is never stopped; it only decides whether the NEXT unit of work may start.

Floors, in GB, from the environment or ~/.tb-graders/cwe/slots/limits.env (NAME=VALUE lines, read on every check,
so a change applies at once to processes that are already waiting). 0 disables a floor.
  DISK_MIN_FREE_GB_GATE   (default 150)  a gate Harbor run waits before taking its slot (common/gate/gate.py)
  DISK_MIN_FREE_GB_TRIAL  (default 150)  a scheduler does not launch a trial job, and a trial job waits before each
                                         run (pipelines/router/scale_queue.py, common/trial/trial.py)
  DISK_MIN_FREE_GB_BUILD  (default 250)  a scheduler does not start a new build (pipelines/router/scale_queue.py)

    python3 common/util/diskguard.py            # print free disk and each floor
"""
import os
import shutil
import sys
import time
from pathlib import Path

LIMITS_FILE = Path.home() / ".tb-graders" / "cwe" / "slots" / "limits.env"
DEFAULTS = {"DISK_MIN_FREE_GB_GATE": 150, "DISK_MIN_FREE_GB_TRIAL": 150, "DISK_MIN_FREE_GB_BUILD": 250}


def floor_gb(name: str) -> int:
    """The floor for `name`: the environment variable if set, else the limits file, else the default."""
    if os.environ.get(name, "").strip():
        try:
            return int(os.environ[name])
        except ValueError:
            pass
    try:
        for line in LIMITS_FILE.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name and v.strip():
                return int(v.strip())
    except (OSError, ValueError):
        pass
    return DEFAULTS.get(name, 0)


def free_gb(path: str = "/") -> int:
    """Free space on the file system that holds Docker's data and the job folders."""
    return shutil.disk_usage(path).free // (1 << 30)


def ok(name: str) -> bool:
    """True when free disk is at or above the floor `name` (or the floor is 0)."""
    f = floor_gb(name)
    return f <= 0 or free_gb() >= f


def wait(name: str, what: str = "", poll: int = 60) -> None:
    """Block until ok(name). Prints one line when it starts waiting and one when it resumes."""
    if ok(name):
        return
    t0 = time.time()
    print(f"[diskguard] {what or name}: free {free_gb()} GB < {floor_gb(name)} GB ({name}); waiting", file=sys.stderr, flush=True)
    while not ok(name):
        time.sleep(poll)
    print(f"[diskguard] {what or name}: free {free_gb()} GB, resuming after {(time.time() - t0) / 60:.0f} min",
          file=sys.stderr, flush=True)


if __name__ == "__main__":
    print(f"free {free_gb()} GB")
    for n in DEFAULTS:
        print(f"{n}={floor_gb(n)} ({'ok' if ok(n) else 'BLOCKED'})")
