#!/usr/bin/env python3
"""Sequential, early-abort trial runner for one built task.

    trial.py <slug> [--max-runs 3] [--models deepseek,mimo]

Rule: a task is a breaker only if it fails EVERY run on EVERY model. So the
instant any single run is solved (reward 1.0), the task is rejected and we stop
— no further runs on either model. Runs go one at a time to avoid wasting
tokens and CPU on a task already decided.

Order: cheaper/stronger solver first (deepseek), so rejections happen fast.
Updates build/queue.json with the verdict. Each run uses the harness wrapper
with a single attempt.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "harness" / "run_trial.sh"
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"


def one_run(model, task_dir, idx):
    name = f"{task_dir.name}-{model}-seq{idx}-{int(time.time())}"
    cmd = ["bash", str(RUN), model, str(task_dir), "1", "--job-name", name, "-n", "1", "-y"]
    subprocess.run(cmd, capture_output=True, text=True)
    trials = sorted((JOBS / name).glob("*/result.json"))
    if not trials:
        return None, f"no result.json for {name}"
    r = json.loads(trials[0].read_text())
    if r.get("exception_info"):
        return None, r["exception_info"].get("exception_type", "exception")
    reward = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    return reward, name


def set_verdict(slug, status, result):
    q = ROOT / "build" / "queue.json"
    d = json.loads(q.read_text())
    for item in d["queue"]:
        if item["slug"] == slug:
            item["status"] = status
            item["result"] = result
    q.write_text(json.dumps(d, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--max-runs", type=int, default=3)
    ap.add_argument("--models", default="deepseek,mimo")
    args = ap.parse_args()
    task_dir = ROOT / "tasks" / args.slug
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    log = []
    for model in models:
        for i in range(1, args.max_runs + 1):
            reward, info = one_run(model, task_dir, i)
            log.append(f"{model} run {i}: reward={reward} ({info})")
            print(log[-1], flush=True)
            if reward is None:
                print(f"[trial] {args.slug}: infra/exception on {model} run {i}; "
                      f"not counting as a solve, retrying once", file=sys.stderr)
                reward, info = one_run(model, task_dir, i)
                log.append(f"{model} run {i} retry: reward={reward} ({info})")
                print(log[-1], flush=True)
            if reward == 1.0:
                verdict = f"REJECTED: {model} solved on run {i} (early-abort). " + "; ".join(log)
                set_verdict(args.slug, "rejected", verdict)
                print(f"[trial] {args.slug}: REJECTED ({model} solved run {i}); stopping.")
                return 0
    verdict = f"ACCEPTED: all runs failed on all models. " + "; ".join(log)
    set_verdict(args.slug, "accepted", verdict)
    print(f"[trial] {args.slug}: ACCEPTED — no run solved it on any model.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
