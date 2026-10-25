#!/usr/bin/env python3
"""Run a Docker-heavy command only while one of N shared slots is free (2026-10-16).

    python3 build/slot.py 3 -- python3 -I builder/gate.py SLUG
    python3 build/slot.py 3 -- python3 build/regrade_from_code.py <trial> "<why>"

Parallel gate and regrade runs share the 12 GB Colima VM with live trials; without a cap they
starve each other. The slots are lock files in ~/.tb-graders/cwe/slots/ held with flock, so a
crashed holder frees its slot automatically. Waits until a slot is free, then runs the command
and exits with its exit code. A number in ~/.tb-graders/cwe/slots/MAX overrides N (re-read while
waiting), so the cap can be raised without restarting callers.
"""
import fcntl
import subprocess
import sys
import time
from pathlib import Path

DIR = Path.home() / ".tb-graders" / "cwe" / "slots"
MAX_INDEX = 16


def main():
    if len(sys.argv) < 4 or sys.argv[2] != "--":
        sys.exit(__doc__)
    n, cmd = int(sys.argv[1]), sys.argv[3:]
    DIR.mkdir(parents=True, exist_ok=True)
    waited = 0
    while True:
        try:
            n = int((DIR / "MAX").read_text().strip())
        except (OSError, ValueError):
            pass
        # The cap counts every held slot, whatever its number (2026-10-16: lowering MAX from 6 to 2
        # let new jobs take slots 0-1 while older jobs still held 2-3). A guard lock makes
        # count-then-take atomic between waiters.
        with open(DIR / "guard.lock", "w") as g:
            fcntl.flock(g, fcntl.LOCK_EX)
            held, free = 0, []
            for i in range(MAX_INDEX):
                f = open(DIR / f"slot{i}.lock", "w")
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    held += 1
                    f.close()
                    continue
                free.append((i, f))
            mine = None
            if held < n and free:
                mine = free.pop(0)
            for _, f in free:
                f.close()                                   # closing releases the probe lock
        if mine:
            print(f"[slot.py] got slot {mine[0]} after {waited} s", file=sys.stderr, flush=True)
            sys.exit(subprocess.run(cmd).returncode)
        time.sleep(15)
        waited += 15


if __name__ == "__main__":
    main()
