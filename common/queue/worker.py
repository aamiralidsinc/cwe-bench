"""The worker: a thin wrapper that runs one job's EXISTING script, unchanged.

    cweq.py _work <id>      (started by the dispatcher in its own session; never by hand)

It marks the job running, runs the command with cwd = the repo root and its output in the job's log, refreshes the
lease every lease_sec/10 while the command runs, and records the exit code. If the job stops being ours (the
dispatcher declared it stale, or `cweq block`), it stops the command and exits.

Commands: each kind's declaration in kinds/ builds its argv (command(row, cfg)); a kind without a command has no
worker. A [commands] entry in the config replaces a kind's command (fields {task} {trial} {job_id}). [env.<kind>] adds
environment variables (trial_run: CWE_AGENT_TIMEOUT_MULT, as the scheduler set it). [ok_exit_codes.<kind>] lists the
exits that count as done (trial.py exits 2 when some runs were ungraded: the reconciler plans the next run).
The job records the settings version the worker loaded (jobs.settings_hash; settings.py).
A job that exits with an ok code is `done` only after its post-condition checks pass (checks.py, docs/RULES.md).
A kind with an exit record (kinds: exit_of) has a nonzero code from it stored as the job's exit code: a build job shows
the builder's own exit (124 for a timeout) although run_pipeline.sh exits 0 (2026-10-28: job #482 showed 0 for 124).
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

import identity  # noqa: E402
import kinds  # noqa: E402
import qdb  # noqa: E402


def command(row, cfg):
    """argv for a job, or raise ValueError."""
    k, task, a = row["kind"], row["task"], qdb.args_of(row)
    if k in cfg.get("commands", {}):
        return [x.format(task=task, trial=kinds.trial_dir(cfg, a), job_id=row["id"]) for x in cfg["commands"][k]]
    kd = kinds.get(k)
    argv = kd.command(row, cfg) if kd and kd.command else None
    if argv:
        return argv
    raise ValueError(f"no worker for kind {k}")


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
    if not qdb.start(conn, job_id, me, lease, str(log_path), cfg.get("_settings_hash")):
        return 3                                         # requeued or blocked before we got here
    try:
        import settings
        settings.record(conn, cfg, "worker")             # the version this job runs under is in the history
    except Exception:
        pass                                             # bookkeeping: never fail a job over it
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
        env.update(identity.job_env(row, paths.PIPELINES / "router" / "out" / "batches"))   # labels (identity.py)
        t0 = time.time()
        child = subprocess.Popen(argv, cwd=str(paths.ROOT), stdin=subprocess.DEVNULL, stdout=log,
                                 stderr=subprocess.STDOUT, env=env)
        try:
            identity.record(conn, job_id, row["attempts"], me, child.pid)
        except Exception as e:                           # identity is bookkeeping: never fail the job over it
            log.write(f"{qdb.utc()} cweq: process identity not recorded ({type(e).__name__}: {e})\n")
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
        shown = None
        kd = kinds.get(row["kind"])
        if kd and kd.exit_of and not lost:
            try:
                shown = kd.exit_of(row["task"], t0)
                if not shown:                            # a clean builder exit never hides the script's own code
                    shown = None
            except Exception as e:                       # bookkeeping: never fail the job over it
                log.write(f"{qdb.utc()} cweq: exit record not read ({type(e).__name__}: {e})\n")
        note = f" (job records exit {shown}, from the kind's exit record)" if shown is not None else ""
        log.write(f"{qdb.utc()} cweq job {job_id} exit {rc}{' (job no longer ours)' if lost else ''}{note}\n")
    if lost:
        return rc
    state = qdb.finish(conn, job_id, me, rc, last_line(log_path),
                       retry_codes=tuple(cfg["retry_exit_codes"].get(row["kind"], ())),
                       ok_codes=tuple(cfg.get("ok_exit_codes", {}).get(row["kind"], (0,))), recorded_exit=shown)
    if state == "done":                                  # done only when the files show the outcome (checks.py)
        import checks
        state = checks.after_done(conn, cfg, job_id, log_path)
    return 0 if state else 3
