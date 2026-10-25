#!/usr/bin/env python3
"""Save the final code of runs whose containers Harbor deletes right after grading.

    python3 common/audit/harvest_watch.py

For every recent trial with no result.json yet: as soon as grading starts
(verifier/test-stdout.txt appears) the agent is done, so its code is saved with
harvest_code.py; then the grader's /tmp logs are re-copied every few seconds until
the container is gone (the last copy holds the most setup evidence). Exits once no
trial.py process is left and nothing is being graded.
Needed only for runs started without keep_containers (before 2026-10-15 ~17:10 UTC).
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest_code import harvest, save_tmp_logs  # noqa: E402

JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
RECENT_S = 4 * 3600


def live_trials():
    now = time.time()
    for job in JOBS.iterdir():
        if job.is_dir() and now - job.stat().st_mtime < RECENT_S:
            for t in job.iterdir():
                if t.is_dir() and not (t / "result.json").exists():
                    yield t


def container_up(name):
    r = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", name], capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == "true"


def log(msg):
    print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), msg, flush=True)


def main():
    grading = {}                       # trial -> container, while its grader runs
    while True:
        for t in live_trials():
            if t in grading or not (t / "verifier" / "test-stdout.txt").exists():
                continue
            info = harvest(t, "during-grading")
            log(f"harvested {t.parent.name}/{t.name}: {info}")
            grading[t] = f"{t.name.lower()}__env-main-1"
        for t, c in list(grading.items()):
            if container_up(c):
                save_tmp_logs(t / "final-code", c)
            else:
                log(f"grading over for {t.parent.name}/{t.name}; logs: "
                    f"{sorted(p.name for p in (t / 'final-code' / 'tmp-logs').glob('*'))}"
                    if (t / "final-code" / "tmp-logs").exists() else f"grading over for {t.name}; no tmp logs")
                del grading[t]
        busy = subprocess.run(["pgrep", "-f", "common/trial/trial.py "], capture_output=True).returncode == 0
        if not busy and not grading:
            log("no trials left; exiting")
            return
        time.sleep(5)


if __name__ == "__main__":
    main()
