#!/usr/bin/env python3
"""Re-grade a trial's FINAL OUTPUT inside its kept container (no new model run).

    python3 build/regrade.py <trial_dir> "<why>" [--memory 8g]

For runs where the grader broke (not the model): restart the kept container, copy in the
task's current tests/, run tests/test.sh, and store the result separately:

    <trial>/regrade-<UTC>/verifier/     reward.json, results.json, test-stdout.txt, ...
    <trial>/regrade-<UTC>/tmp-logs/     the grader's /tmp logs
    <trial>/regrade-<UTC>/REGRADE.json  why, when, memory, test.sh sha256, reward

The original <trial>/verifier/ (the grading that broke) is backed up first and restored
afterwards, so the raw record is never changed. The container is stopped again (kept)
when done. audit_results.py uses the newest regrade in place of the original grading.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest_code import save_tmp_logs  # noqa: E402


def sh(*a, **kw):
    return subprocess.run(a, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial_dir")
    ap.add_argument("why")
    ap.add_argument("--memory", help="new container memory limit, e.g. 8g (default: unchanged)")
    ap.add_argument("--timeout", type=int, default=2400)
    a = ap.parse_args()
    trial = Path(a.trial_dir).resolve()
    res = json.loads((trial / "result.json").read_text())
    task = Path(res["config"]["task"]["path"]).name
    tests = ROOT / "tasks" / task / "tests"
    container = f"{trial.name.lower()}__env-main-1"
    if sh("docker", "inspect", container).returncode != 0:
        sys.exit(f"container {container} not found (was it kept?)")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = trial / f"regrade-{stamp}"
    backup = out / "original-verifier-backup"
    out.mkdir()
    shutil.copytree(trial / "verifier", backup)

    if a.memory:
        sh("docker", "update", "--memory", a.memory, "--memory-swap", a.memory, container)
    sh("docker", "start", container)
    sh("docker", "cp", f"{tests}/.", f"{container}:/tests/")
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        run = sh("docker", "exec", "-u", "root", container, "bash", "/tests/test.sh", timeout=a.timeout)
        rc, stdout = run.returncode, run.stdout + run.stderr
    except subprocess.TimeoutExpired as e:
        rc, stdout = "timeout", (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else str(e.stdout or "")
    finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
    save_tmp_logs(out, container)
    sh("docker", "stop", container)

    # Move the new grading out of verifier/ and put the original back exactly as it was.
    shutil.copytree(trial / "verifier", out / "verifier")
    (out / "verifier" / "test-stdout.txt").write_text(stdout)
    for p in (trial / "verifier").iterdir():
        (shutil.rmtree if p.is_dir() else Path.unlink)(p)
    for p in backup.iterdir():
        (shutil.copytree if p.is_dir() else shutil.copy2)(p, trial / "verifier" / p.name)
    shutil.rmtree(backup)

    reward = None
    rj = out / "verifier" / "reward.json"
    if rj.is_file():
        reward = json.loads(rj.read_text()).get("reward")
    info = {"trial": str(trial), "task": task, "container": container, "why": a.why,
            "memory": a.memory or "unchanged", "started_utc": started, "finished_utc": finished,
            "test_sh_sha256": hashlib.sha256((tests / "test.sh").read_bytes()).hexdigest(),
            "exit": rc, "reward": reward}
    (out / "REGRADE.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
