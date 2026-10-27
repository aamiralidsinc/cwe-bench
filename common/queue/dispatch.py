"""The dispatcher: one process that starts queued jobs by effective priority, within the admission limits.

Each tick:
  1. reap   - a leased/running job whose worker is gone (pid dead) or whose lease expired is stale: its process
              group is stopped (SIGTERM) if anything is left of it, then it is requeued (attempts + 1 was counted at
              claim) or, with its attempts used up, blocked;
  2. deps   - a queued job whose dependency failed or was blocked becomes blocked ("dependency #N ...");
  3. start  - candidates in order of priority + aging_per_hour x hours waited (nothing starves), skipping a job when
              its dependencies are not done, its task is busy (an old script, or one of our jobs: max_running_per_task),
              its kind is at max_running (a kind with no limit has no worker yet and never starts), a trial_run task
              is held, or the machine is over a limit. At most max_starts_per_tick starts, start_spacing_sec apart.

The worker is `cweq.py _work <id>` in its own session (setsid): it runs the existing script, refreshes the lease and
records the exit code (worker.py). The dispatcher never waits for it, so restarting the dispatcher stops no job.
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402

import procs  # noqa: E402
import qdb  # noqa: E402

CWEQ = Path(__file__).resolve().parent / "cweq.py"


def effective_priority(row, now, aging_per_hour):
    waited = max(0.0, now - (qdb.parse_utc(row["queued_at"]) or now)) / 3600
    return row["priority"] + aging_per_hour * waited


def held(task, kind, args):
    """A trial_run is not started while the task is held for a repair (.hold-repair) or the model is held."""
    if kind != "trial_run":
        return None
    b = paths.BUILD / task
    if (b / ".hold-repair").exists():
        return "held (.hold-repair)"
    model = args.get("model")
    if model and (b / f"hold_{model}").exists():
        return f"held (hold_{model})"
    return None


class Dispatcher:
    def __init__(self, conn, cfg, db_path, metrics=None, proc_list=None, spawn=None, sleep=time.sleep):
        self.conn, self.cfg, self.db_path = conn, cfg, db_path
        self.metrics = metrics or (lambda: procs.headroom(str(paths.ROOT)))
        self.proc_list = proc_list                       # None = read the real process table
        self.spawn = spawn or self._spawn
        self.sleep = sleep
        self.children = []                               # our Popen objects, polled so they never linger as zombies

    # ---- 1. stale workers
    def reap(self):
        for c in list(self.children):
            if c.poll() is not None:
                self.children.remove(c)
        out = []
        now = time.time()
        for row in qdb.jobs(self.conn, "state IN ('leased','running')"):
            pid, exp = row["owner_pid"], qdb.parse_utc(row["lease_expires"])
            expired = exp is not None and exp < now
            gone = pid is not None and not procs.pid_alive(pid)
            if row["state"] == "leased" and pid is None and not expired:
                continue                                 # just claimed, the worker is being spawned
            if not (gone or expired):
                continue
            why = f"stale worker (pid {pid} {'gone' if gone else 'alive'}, lease {'expired' if expired else 'valid'})"
            if pid and not gone:
                try:
                    os.killpg(pid, signal.SIGTERM)       # the worker leads its own session: pgid = pid
                except OSError:
                    pass
            state = qdb.requeue_or_block(self.conn, row["id"], why)
            out.append((row["id"], state, why))
        return out

    # ---- 2. dependencies
    def block_broken_deps(self):
        out = []
        for row in qdb.jobs(self.conn, "state='queued' AND depends_on != '[]'"):
            for d in qdb.deps_of(row):
                dep = qdb.get(self.conn, d)
                if dep is None or dep["state"] in ("failed", "blocked"):
                    why = f"dependency #{d} {'missing' if dep is None else dep['state']}"
                    qdb.set_state(self.conn, row["id"], "blocked", why)
                    out.append((row["id"], why))
                    break
        return out

    def deps_done(self, row):
        return all((qdb.get(self.conn, d) or {"state": None})["state"] == "done" for d in qdb.deps_of(row))

    # ---- 3. starting
    def plan(self):
        """[(row, None)] to start now and [(row, reason)] waiting, in priority order. Starts nothing."""
        cfg, d = self.cfg, self.cfg["dispatch"]
        now = time.time()
        queued = sorted(qdb.jobs(self.conn, "state='queued'"),
                        key=lambda r: (-effective_priority(r, now, d["aging_per_hour"]), r["id"]))
        active = qdb.jobs(self.conn, "state IN ('leased','running')")
        per_kind, per_task = {}, {}
        for r in active:
            per_kind[r["kind"]] = per_kind.get(r["kind"], 0) + 1
            per_task[r["task"]] = per_task.get(r["task"], 0) + 1
        total = len(active)
        limits = procs.over_limits(self.metrics(), cfg["limits"])
        busy = procs.busy_tasks({r["task"] for r in queued}, cfg["busy"]["patterns"], self.proc_list,
                                skip_dirs=(paths.COMMON,))
        maxk = cfg["limits"]["max_running"]
        starts, waits = [], []
        for r in queued:
            k, t = r["kind"], r["task"]
            if not cfg.get("enabled", True):
                why = "queue switched off (enabled = false)"
            elif k not in maxk and k not in cfg.get("commands", {}):
                why = f"no worker for {k} in phase 1"
            elif not self.deps_done(r):
                why = "waiting for " + ", ".join(f"#{x}" for x in qdb.deps_of(r))
            elif held(t, k, qdb.args_of(r)):
                why = held(t, k, qdb.args_of(r))
            elif t in busy:
                why = f"task busy (old script pid {busy[t][0][0]}: {busy[t][0][1][:80]})"
            elif per_task.get(t, 0) >= d["max_running_per_task"]:
                why = "another job of this task is running"
            elif per_kind.get(k, 0) >= maxk.get(k, 0):
                why = f"{k} at its limit ({maxk.get(k, 0)} running)"
            elif total >= d["max_running_total"]:
                why = f"total at its limit ({d['max_running_total']} running)"
            elif limits:
                why = "admission closed: " + "; ".join(limits)
            elif len(starts) >= d["max_starts_per_tick"]:
                why = "start budget of this tick used"
            else:
                why = None
                per_kind[k] = per_kind.get(k, 0) + 1
                per_task[t] = per_task.get(t, 0) + 1
                total += 1
            (starts if why is None else waits).append((r, why))
        return starts, waits

    def _spawn(self, job_id):
        """Start the worker wrapper in its own session; returns its pid."""
        log_dir = Path(self.cfg["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        boot = open(log_dir / f"{job_id}.worker.err", "ab")
        p = subprocess.Popen([sys.executable, "-I", str(CWEQ), "--db", self.db_path, "--config", self.cfg["_file"],
                              "_work", str(job_id)], cwd=str(paths.ROOT), stdin=subprocess.DEVNULL, stdout=boot,
                             stderr=subprocess.STDOUT, start_new_session=True,
                             env=dict(os.environ, CWEQ_JOB=str(job_id)))
        boot.close()
        self.children.append(p)
        return p.pid

    def tick(self, dry_run=False):
        """One pass. Returns a report dict (reaped, blocked, started, waiting)."""
        rep = {"reaped": [], "blocked": [], "started": [], "waiting": []}
        if not dry_run:
            rep["reaped"] = self.reap()
            rep["blocked"] = self.block_broken_deps()
        starts, waits = self.plan()
        rep["waiting"] = waits
        if dry_run:
            rep["started"] = [(r, "would start") for r, _ in starts]
            return rep
        for i, (r, _) in enumerate(starts):
            if i and self.cfg["dispatch"]["start_spacing_sec"]:
                self.sleep(self.cfg["dispatch"]["start_spacing_sec"])
            if not qdb.claim(self.conn, r["id"], self.cfg["dispatch"]["lease_sec"]):
                continue
            pid = self.spawn(r["id"])
            qdb.set_owner(self.conn, r["id"], pid)
            rep["started"].append((r, f"pid {pid}"))
        return rep
