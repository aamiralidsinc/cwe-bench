"""The worker: a thin wrapper that runs one job's EXISTING script, unchanged.

    cweq.py _work <id>      (started by the dispatcher in its own session; never by hand)

It marks the job running, runs the command with cwd = the repo root and its output in the job's log, refreshes the
lease every lease_sec/10 while the command runs, and records the exit code. If the job stops being ours (the
dispatcher declared it stale, or `cweq block`), it stops the command and exits.

Commands:
  build     bash pipelines/stacking/3-build-gate/run_stack_pipeline.sh <slug>          (stk-* slugs)
            bash pipelines/sibling/6-build/run_pipeline.sh deepseek <slug>             (the others)
  trial_run python3 -I common/trial/trial.py <slug> --models <m> --no-verdict --first-run N --max-runs K
  regate   bash common/gate/regate.sh <slug> [--listing]
  regrade  python3 -I common/audit/regrade_from_code.py <trial_dir> "<why>"
  rescore  python3 -I common/audit/rescore_from_results.py <trial_dir> --drop <name> ... --why "<why>"
A [commands] entry in the config replaces a kind's command (fields {task} {trial} {job_id}). [env.<kind>] adds
environment variables (trial_run: CWE_AGENT_TIMEOUT_MULT, as the scheduler set it). [ok_exit_codes.<kind>] lists the
exits that count as done (trial.py exits 2 when some runs were ungraded: the reconciler plans the next run).
"""
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402

import qdb  # noqa: E402


def command(row, cfg):
    """argv for a job, or raise ValueError."""
    k, task, a = row["kind"], row["task"], qdb.args_of(row)
    trial = str(Path(cfg["jobs_dir"]) / a["trial"]) if a.get("trial") else ""
    if k in cfg.get("commands", {}):
        return [x.format(task=task, trial=trial, job_id=row["id"]) for x in cfg["commands"][k]]
    if k == "build":                                    # pipelines/router/scale_queue.py build_cmd()
        if task.startswith("stk-"):
            return ["bash", "pipelines/stacking/3-build-gate/run_stack_pipeline.sh", task]
        return ["bash", "pipelines/sibling/6-build/run_pipeline.sh", "deepseek", task]
    if k == "trial_run":                                # scale_queue.py trial_candidates()
        return [sys.executable, "-I", str(paths.TRIAL), task, "--models", a["model"], "--no-verdict",
                "--first-run", str(a["first_run"]), "--max-runs", str(a["max_runs"])]
    if k == "regate":
        return ["bash", "common/gate/regate.sh", task] + (["--listing"] if a.get("listing") else [])
    if k == "regrade":
        return [sys.executable, "-I", "common/audit/regrade_from_code.py", trial, a["why"]]
    if k == "rescore":
        drops = [x for d in a["drop"] for x in ("--drop", d)]
        return [sys.executable, "-I", "common/audit/rescore_from_results.py", trial, *drops, "--why", a["why"]]
    raise ValueError(f"no worker for kind {k} in phase 1")


OWN_LINE = re.compile(r"^\S+Z cweq")


def last_line(path):
    """The command's own last output line (our header and footer lines skipped)."""
    try:
        lines = [l.strip() for l in Path(path).read_text(errors="replace").splitlines()
                 if l.strip() and not OWN_LINE.match(l)]
        return lines[-1][:300] if lines else ""
    except OSError:
        return ""


def run(conn, cfg, job_id):
    row = qdb.get(conn, job_id)
    if row is None:
        return 2
    lease = cfg["dispatch"]["lease_sec"]
    log_dir = Path(cfg["log_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{job_id}-{row['kind']}-{row['task']}.log"
    me = os.getpid()
    if not qdb.start(conn, job_id, me, lease, str(log_path)):
        return 3                                         # requeued or blocked before we got here
    try:
        argv = command(row, cfg)
    except (ValueError, KeyError) as e:
        qdb.finish(conn, job_id, me, 127, f"cannot build the command: {e}")
        return 127
    b = paths.BUILD / row["task"]
    held_before = row["kind"] == "regate" and (b / ".hold-repair").exists()
    with open(log_path, "a") as log:
        log.write(f"{qdb.utc()} cweq job {job_id} ({row['kind']} {row['task']}) attempt {row['attempts']}: "
                  f"{' '.join(argv)}\n")
        log.flush()
        env = dict(os.environ, **{k2: str(v) for k2, v in (cfg.get("env", {}).get(row["kind"]) or {}).items()})
        child = subprocess.Popen(argv, cwd=str(paths.ROOT), stdin=subprocess.DEVNULL, stdout=log,
                                 stderr=subprocess.STDOUT, env=env)
        step = max(1.0, lease / 10)
        lost = False
        while True:
            try:
                rc = child.wait(timeout=step)
                break
            except subprocess.TimeoutExpired:
                if not qdb.refresh(conn, job_id, me, lease):
                    lost = True                          # no longer ours: stop the command, record nothing
                    child.send_signal(signal.SIGTERM)
                    try:
                        rc = child.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        rc = child.wait()
                    break
        if held_before and cfg["reconcile"].get("rehold_after_regate", True) and (b / ".sound").exists():
            # Same as the repair scripts: the task stays held until its regrades are in.
            os.replace(b / ".sound", b / ".hold-repair")
            log.write(f"{qdb.utc()} cweq: task was held: .sound moved back to .hold-repair\n")
        log.write(f"{qdb.utc()} cweq job {job_id} exit {rc}{' (job no longer ours)' if lost else ''}\n")
    if lost:
        return rc
    state = qdb.finish(conn, job_id, me, rc, last_line(log_path),
                       retry_codes=tuple(cfg["retry_exit_codes"].get(row["kind"], ())),
                       ok_codes=tuple(cfg.get("ok_exit_codes", {}).get(row["kind"], (0,))))
    return 0 if state else 3
