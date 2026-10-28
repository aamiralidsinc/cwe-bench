"""The dispatcher: one process that starts queued jobs by effective priority, within the admission limits.

Each tick:
  1. reap   - a leased/running job whose worker is gone (pid dead) or whose lease expired is stale: its process
              group is stopped (SIGTERM) if anything is left of it, then it is requeued (attempts + 1 was counted at
              claim) or, with its attempts used up, blocked;
  2. deps   - a queued job whose dependency failed or was blocked becomes blocked ("dependency #N ...");
  3. start  - candidates in order of priority + aging_per_hour x hours waited (nothing starves), skipping a job when
              no adoption is recorded (require_adoption), its dependencies are not done, a trial_run task is held,
              the files show its work done (closed as done: never redo) or an old script is running it, its task is
              busy (build/gate/regate/regrade/rescore run alone on a task; trial_runs of one task may run together,
              up to max_running_per_task), its kind is at max_running or the total at max_running_total (old-script
              builds and trials count too: count_foreign), a trial_run while builds running + queued >=
              trials_wait_builds (builds first, as scale_queue.py did), the machine is over a limit, or the kind's
              disk floor (limits.disk_floor -> common/util/diskguard.py) is not met. At most max_starts_per_tick
              starts per tick, start_spacing_sec apart (fill_spacing_sec during the first fill; [low, high] = random).

The worker is `cweq.py _work <id>` in its own session (setsid): it runs the existing script, refreshes the lease and
records the exit code (worker.py). The dispatcher never waits for it, so restarting the dispatcher stops no job.
"""
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402
sys.path.insert(0, str(paths.COMMON / "util"))
import diskguard  # noqa: E402  (disk floors per kind, common/util/diskguard.py; live values in limits.env)

import procs  # noqa: E402
import kinds  # noqa: E402
import monitor  # noqa: E402
import qdb  # noqa: E402
import taskstate  # noqa: E402
import checks  # noqa: E402
import autolimit  # noqa: E402

CWEQ = Path(__file__).resolve().parent / "cweq.py"
REDO = "not needed, it would redo finished work: "


def batch_hold(row, ctx):
    """Why a batch build must wait: its batch is on hold (`# hold: yes`), or the reconciler queued it for a batch
    the task has since left (a re-ranked batch file). None when it may start."""
    b = ctx.get("batches", {}).get(row["task"])
    if b and (ctx.get("batch_meta") or {}).get(b, {}).get("hold"):
        return f"batch {b} on hold (# hold: yes in its batch file)"
    if not b and row["origin"] == "reconciler":
        return "no longer in a batch file (the reconciler queued it for a batch)"
    return None


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


# Both come from the kind declarations (kinds/: exclusive, foreign); plan() reads them again so plug-in kinds count.
EXCLUSIVE = tuple(sorted(kinds.exclusive()))      # one at a time per task, alone on the task
FOREIGN_KIND = kinds.foreign_map()                 # old-script processes -> job kind


def spacing(v):
    """A start spacing setting: a number of seconds, or [low, high] for a random pause in that range."""
    if isinstance(v, (list, tuple)):
        return random.uniform(float(v[0]), float(v[1]))
    return float(v or 0)


class Dispatcher:
    def __init__(self, conn, cfg, db_path, metrics=None, proc_list=None, spawn=None, sleep=time.sleep,
                 disk_ok=None):
        self.conn, self.cfg, self.db_path = conn, cfg, db_path
        # Admission values: the monitor's latest sample when it is fresh (monitor.py), else measured here.
        self.metrics = metrics or (lambda: monitor.fresh_headroom(conn, cfg) or procs.headroom(str(paths.ROOT)))
        self.proc_list = proc_list                       # None = read the real process table
        self.spawn = spawn or self._spawn
        self.sleep = sleep
        self.disk_ok = disk_ok or diskguard.ok           # floor name -> True when free disk is above it
        self.filling = True                              # first fill: longer pauses between starts
        self.total_seen = 0
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
        per_kind, per_task, excl_task = {}, {}, set()
        exclusive, foreign_kind = kinds.exclusive(), kinds.foreign_map()
        light = set(d.get("light_kinds", ()))             # bookkeeping kinds: outside the total and the machine limits
        for r in active:
            per_kind[r["kind"]] = per_kind.get(r["kind"], 0) + 1
            if r["kind"] in light:                       # bookkeeping never holds a task's other work
                continue
            per_task[r["task"]] = per_task.get(r["task"], 0) + 1
            if r["kind"] in exclusive:
                excl_task.add(r["task"])
        total = sum(1 for r in active if r["kind"] not in light)
        cap = self.cap = autolimit.effective(self.conn, cfg)   # base from the settings file, moved by sustained idle
        # The old scripts' builds and trials hold slots too (cutover: the queue and the schedulers never exceed the
        # caps together). Their processes, without the queue's own workers.
        plist = procs.list_processes() if self.proc_list is None else self.proc_list
        ctx = taskstate.context(plist, ignore_own=True)
        foreign = {}
        for slug, runs in ctx["running"].items():
            seen = set()
            for kind, _m, _p in runs:
                k = foreign_kind.get(kind)
                if not k or k not in d.get("count_foreign", ()):
                    continue
                # A task holds one slot of an exclusive kind however many processes its script has (a resumed build
                # runs its gate in a subshell with the same command line); trial runs count one per process.
                if k in exclusive or k == "fairness":
                    if k in seen:
                        continue
                    seen.add(k)
                foreign[k] = foreign.get(k, 0) + 1
        for k, n in foreign.items():
            per_kind[k] = per_kind.get(k, 0) + n
            total += n
        queued_builds = sum(1 for r in queued if r["kind"] == "build")
        self.total_seen = total
        limits = procs.over_limits(self.metrics(), cfg["limits"])
        busy = procs.busy_tasks({r["task"] for r in queued}, cfg["busy"]["patterns"], self.proc_list,
                                skip_dirs=(paths.COMMON,))
        maxk = cfg["limits"]["max_running"]
        adoption = qdb.latest_adoption(self.conn)
        not_adopted = None
        if cfg.get("require_adoption", True):
            if adoption is None:
                not_adopted = "no adoption yet: run `cweq adopt` so the queue starts from the pipeline's current state"
            elif not adoption["ok"]:
                not_adopted = f"adoption #{adoption['id']} has conflicts: resolve them and run `cweq adopt` again"
        starts, waits = [], []
        for r in queued:
            k, t = r["kind"], r["task"]
            if not cfg.get("enabled", True):
                why = "queue switched off (enabled = false)"
            elif not_adopted:
                why = not_adopted
            elif k not in maxk and k not in cfg.get("commands", {}):
                why = f"no worker for {k} in phase 1"  # (kinds without a [limits.max_running] entry)
            elif not self.deps_done(r):
                why = "waiting for " + ", ".join(f"#{x}" for x in qdb.deps_of(r))
            elif held(t, k, qdb.args_of(r)):
                why = held(t, k, qdb.args_of(r))
            elif k == "build" and (bh := batch_hold(r, ctx)):
                why = bh
            elif k in checks.TOOLS and (refused := checks.tool_refused(self.conn, k, cfg)):
                why = refused
            elif k in taskstate.REDO_CHECKED and (redo := taskstate.redo_reason(k, t, qdb.args_of(r), ctx)):
                # Finished work closes the job; work the old scripts are running only makes it wait.
                why = ("task busy (old script): " + redo) if redo.endswith("running") else REDO + redo
            elif t in busy:
                why = f"task busy (old script pid {busy[t][0][0]}: {busy[t][0][1][:80]})"
            elif t in excl_task or (k in exclusive and per_task.get(t, 0)):
                why = "another job of this task is running"
            elif per_task.get(t, 0) >= d["max_running_per_task"]:
                why = f"{d['max_running_per_task']} jobs of this task are running"
            elif per_kind.get(k, 0) >= maxk.get(k, 0):
                why = f"{k} at its limit ({maxk.get(k, 0)} running{', old scripts included' if foreign.get(k) else ''})"
            elif total >= cap and k not in light:
                why = f"total at its limit ({cap} running)"
            elif k == "trial_run" and per_kind.get("build", 0) + queued_builds >= d["trials_wait_builds"]:
                why = (f"builds first: {per_kind.get('build', 0)} running + {queued_builds} queued >= "
                       f"{d['trials_wait_builds']}")
            elif limits and k not in light:              # cleanup must run exactly when the disk is short
                why = "admission closed: " + "; ".join(limits)
            elif cfg["limits"].get("disk_floor", {}).get(k) and not self.disk_ok(cfg["limits"]["disk_floor"][k]):
                why = f"disk below its {k} floor ({cfg['limits']['disk_floor'][k]}, common/util/diskguard.py)"
            elif k not in light and sum(1 for x, _ in starts if x["kind"] not in light) >= d["max_starts_per_tick"]:
                why = "start budget of this tick used"
            else:
                why = None
                per_kind[k] = per_kind.get(k, 0) + 1
                if k not in light:                       # bookkeeping holds no task slot and no start budget
                    per_task[t] = per_task.get(t, 0) + 1
                total += 0 if k in light else 1
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
        if not dry_run:                                  # the files show the work done: close the job, never run it
            for r, why in waits:
                if why and why.startswith(REDO):
                    qdb.set_state(self.conn, r["id"], "done", why)
            waits = [(r, w) for r, w in waits if not (w and w.startswith(REDO))]
        rep["waiting"] = waits
        if dry_run:
            rep["started"] = [(r, "would start") for r, _ in starts]
            return rep
        d = self.cfg["dispatch"]
        light = set(d.get("light_kinds", ()))
        heavy_started = 0
        for r, _ in starts:
            if r["kind"] not in light:
                if heavy_started:
                    # Staggered starts: simultaneous container spin-up starves sshd. Longer pauses during the first
                    # fill. Bookkeeping kinds start no containers and are not spaced.
                    pause = spacing(d.get("fill_spacing_sec", d["start_spacing_sec"]) if self.filling
                                    else d["start_spacing_sec"])
                    if pause:
                        self.sleep(pause)
                heavy_started += 1
            if not qdb.claim(self.conn, r["id"], self.cfg["dispatch"]["lease_sec"]):
                continue
            pid = self.spawn(r["id"])
            qdb.set_owner(self.conn, r["id"], pid)
            rep["started"].append((r, f"pid {pid}"))
        # The first fill ends once the total cap is reached, or a tick started everything that was startable.
        budget_left = any(w == "start budget of this tick used" for _, w in waits)
        if self.filling and (self.total_seen + len(rep["started"]) >= getattr(self, "cap", d["max_running_total"]) or not budget_left):
            self.filling = False
        return rep
