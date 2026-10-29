"""Process identity and labels for queue jobs.

Identity. When a worker starts a job's command it records, in the table `job_procs`:
  - its own pid, its process group (the worker leads its own session, so the group holds the whole job), and the
    process start time from /proc/<pid>/stat (clock ticks since boot);
  - the command's pid and start time;
  - the code version (common/queue/DEPLOYED_FROM, else `git rev-parse --short HEAD`).
`cweq stop <id>` signals that group only after checking that the recorded pid still has the recorded start time, so
a reused pid is never hit. Nothing is ever killed by matching command lines.

Labels. job_env() gives every process a worker starts these variables (children inherit them):
    CWE_JOB_ID CWE_KIND CWE_TASK CWE_BATCH CWE_MODEL CWE_RUN CWE_CODE_VERSION
Harbor runs inside that environment, and common/harbor_ext/cwe_labels.py turns them into Docker labels
(cwe.job_id, cwe.kind, ...) on every container of the job.

Orphans. orphans() lists, read-only: containers labelled with a job that is no longer running, pipeline containers
with no cwe labels, and processes carrying a queue job id whose job is no longer running.
"""
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import qdb

HERE = Path(__file__).resolve().parent
SCHEMA = """
CREATE TABLE IF NOT EXISTS job_procs (
    job_id        INTEGER PRIMARY KEY,
    attempt       INTEGER,
    host          TEXT,
    worker_pid    INTEGER,
    worker_start  INTEGER,                       -- /proc/<pid>/stat field 22 (clock ticks since boot)
    pgid          INTEGER,
    child_pid     INTEGER,
    child_start   INTEGER,
    code_version  TEXT,
    recorded      TEXT
);
"""
RUNNING = ("leased", "running")


def ensure(conn):
    conn.executescript(SCHEMA)


def proc_start(pid):
    """Start time of a live process (clock ticks since boot), or None (gone, or no /proc)."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    rest = stat[stat.rfind(")") + 2:].split()            # fields after "(comm)"; field 3 is rest[0]
    if rest and rest[0] in ("Z", "X"):                   # a zombie has ended; only its parent's wait is missing
        return None
    try:
        return int(rest[19])                             # field 22
    except (IndexError, ValueError):
        return None


_version = []


def code_version():
    """The release this code runs from (RELEASE.json at the code root, common/util/release.py), else the
    DEPLOYED_FROM file of a copied deploy, else the checkout's git commit."""
    if not _version:
        v = ""
        rel = HERE.parents[1] / "RELEASE.json"
        if rel.is_file():
            try:
                import json
                v = json.loads(rel.read_text()).get("sha", "")
            except (OSError, ValueError):
                v = ""
        f = HERE / "DEPLOYED_FROM"
        if not v and f.is_file():
            v = f.read_text().strip()
        if not v:
            try:
                v = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--short=8", "HEAD"], capture_output=True,
                                   text=True, timeout=10).stdout.strip()
            except (OSError, subprocess.SubprocessError):
                v = ""
        _version.append(v or "unknown")
    return _version[0]


def batch_of(task, batches_dir):
    for f in sorted(Path(batches_dir).glob("*.txt")):
        try:
            for line in f.read_text().splitlines():
                if line.split("#")[0].strip() == task:
                    return f.stem
        except OSError:
            pass
    return ""


def job_env(row, batches_dir):
    """CWE_* variables for every process of a job."""
    a = qdb.args_of(row)
    run = a.get("run") or a.get("first_run") or ""
    if a.get("first_run") and a.get("max_runs") and int(a["max_runs"]) > 1:
        run = f"{a['first_run']}-{int(a['first_run']) + int(a['max_runs']) - 1}"
    return {"CWE_JOB_ID": str(row["id"]), "CWE_KIND": row["kind"], "CWE_TASK": row["task"],
            "CWE_BATCH": batch_of(row["task"], batches_dir), "CWE_MODEL": str(a.get("model", "")),
            "CWE_RUN": str(run), "CWE_CODE_VERSION": code_version()}


def record(conn, job_id, attempt, worker_pid, child_pid):
    ensure(conn)
    try:
        pgid = os.getpgid(worker_pid)
    except OSError:
        pgid = None
    conn.execute("INSERT INTO job_procs (job_id, attempt, host, worker_pid, worker_start, pgid, child_pid, child_start,"
                 " code_version, recorded) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET"
                 " attempt=excluded.attempt, host=excluded.host, worker_pid=excluded.worker_pid,"
                 " worker_start=excluded.worker_start, pgid=excluded.pgid, child_pid=excluded.child_pid,"
                 " child_start=excluded.child_start, code_version=excluded.code_version, recorded=excluded.recorded",
                 (job_id, attempt, socket.gethostname(), worker_pid, proc_start(worker_pid), pgid, child_pid,
                  proc_start(child_pid), code_version(), qdb.utc()))


def get(conn, job_id):
    ensure(conn)
    return conn.execute("SELECT * FROM job_procs WHERE job_id=?", (job_id,)).fetchone()


def alive_and_same(pid, start):
    """True when pid is alive and is still the process that was recorded (same start time)."""
    if not pid or start is None:
        return False
    return proc_start(pid) == start


def _signal_group(killpg, pgid, sig, said):
    try:
        killpg(pgid, sig)
        return said
    except ProcessLookupError:
        return said + " (group already gone)"
    except PermissionError as e:
        return said + f" (not permitted: {e})"


def stop(conn, job_id, grace=30, why="stopped by cweq stop", docker=None, sleep=time.sleep, killpg=os.killpg):
    """Stop one job: its whole process group (verified first), then its labelled containers. Returns a list of
    lines saying what was done. The job is marked blocked so nothing restarts it on its own."""
    out = []
    row = qdb.get(conn, job_id)
    if row is None:
        return [f"#{job_id}: no such job"]
    p = get(conn, job_id)
    if row["state"] in RUNNING and p is not None:
        if p["host"] and p["host"] != socket.gethostname():
            return [f"#{job_id}: recorded on host {p['host']}, not here; nothing signalled"]
        if alive_and_same(p["worker_pid"], p["worker_start"]) and p["pgid"]:
            out.append(_signal_group(killpg, p["pgid"], signal.SIGTERM, f"#{job_id}: SIGTERM to process group "
                                     f"{p['pgid']} (worker {p['worker_pid']})"))
            for _ in range(int(grace)):
                if not alive_and_same(p["worker_pid"], p["worker_start"]):
                    break
                sleep(1)
            if alive_and_same(p["worker_pid"], p["worker_start"]):
                out.append(_signal_group(killpg, p["pgid"], signal.SIGKILL,
                                         f"#{job_id}: SIGKILL to process group {p['pgid']} after {grace}s"))
        elif p["worker_pid"]:
            out.append(f"#{job_id}: worker {p['worker_pid']} is gone or its pid was reused; nothing signalled")
    elif row["state"] in RUNNING:
        out.append(f"#{job_id}: no process record; nothing signalled")
    projects = job_projects(job_id, docker=docker)       # read before the labelled containers go
    ids = job_containers(job_id, docker=docker)
    if ids:
        (docker or _docker)(["rm", "-f", *ids])
        out.append(f"#{job_id}: removed {len(ids)} container(s) of its compose project(s)")
    # `docker rm` never removes a compose network; each holds one /24 of the 4,096-network pool
    # (reports/gate-compose-rca-20261029.md). Remove the job's projects whole, as `compose down` would: the
    # verifier project's containers too, then every network of both.
    if projects:
        n_ctr, n_net = _compose_cleanup().remove_projects(projects, docker=docker or _docker)
        out.append(f"#{job_id}: compose projects {', '.join(projects)}: removed {n_ctr} more container(s) "
                   f"and {n_net} network(s)")
    if row["state"] not in ("done", "failed", "blocked"):
        qdb.set_state(conn, job_id, "blocked", why)
        out.append(f"#{job_id}: blocked ({why})")
    return out or [f"#{job_id}: {row['state']}, nothing to stop"]


# ---------- Docker (read-only helpers; stop() is the only writer)

def _docker(args):
    r = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=120)
    return r.stdout


def containers(label_filter=None, docker=None):
    args = ["ps", "-aq"] + (["--filter", f"label={label_filter}"] if label_filter else [])
    return [x for x in (docker or _docker)(args).split() if x]


def _compose_cleanup():
    import sys
    util = str(Path(__file__).resolve().parents[1] / "util")
    if util not in sys.path:
        sys.path.insert(0, util)
    import compose_cleanup                               # common/util/compose_cleanup.py
    return compose_cleanup


def job_projects(job_id, docker=None):
    """The compose projects of the job's labelled containers, with each Harbor trial's other project
    (<trial>__env and <trial>__verifier__trial), sorted."""
    cc = _compose_cleanup()
    projects = {c["labels"].get("com.docker.compose.project") for c in container_list(docker)
                if c["labels"].get("cwe.job_id") == str(job_id)}
    projects.discard(None)
    return sorted({q for p in projects for q in cc.harbor_projects(p)})


def job_containers(job_id, docker=None):
    """Every container of the compose projects whose `main` carries cwe.job_id=<job_id> (sidecars included)."""
    projects = {c["labels"].get("com.docker.compose.project") for c in container_list(docker)
                if c["labels"].get("cwe.job_id") == str(job_id)}
    projects.discard(None)
    return sorted({c["id"] for c in container_list(docker)
                   if c["labels"].get("cwe.job_id") == str(job_id)
                   or c["labels"].get("com.docker.compose.project") in projects})


def container_list(docker=None):
    """[{id, name, state, status, labels{}}] for every container."""
    raw = (docker or _docker)(["ps", "-a", "--no-trunc", "--format", "{{json .}}"])
    out = []
    for line in raw.splitlines():
        try:
            c = json.loads(line)
        except ValueError:
            continue
        lab = {}
        for kv in (c.get("Labels") or "").split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                lab[k] = v
        out.append({"id": c.get("ID", "")[:12], "name": c.get("Names", ""), "state": c.get("State", ""),
                    "status": c.get("Status", ""), "labels": lab})
    return out


def is_pipeline_container(c):
    """A Harbor compose container of a task (<task>__<id>__...) or one already carrying cwe labels."""
    proj = c["labels"].get("com.docker.compose.project", "")
    return bool(c["labels"].get("cwe.task")) or "__" in proj


def orphans(conn, docker=None, proc_list=None):
    """{'containers_job_ended': [...], 'containers_unlabelled': [...], 'processes_job_ended': [...]} (read-only)."""
    import procs
    states = {r["id"]: r["state"] for r in conn.execute("SELECT id, state FROM jobs")}
    res = {"containers_job_ended": [], "containers_unlabelled": [], "processes_job_ended": []}
    for c in container_list(docker):
        if not is_pipeline_container(c):
            continue
        jid = c["labels"].get("cwe.job_id")
        if jid:
            st = states.get(int(jid)) if jid.isdigit() else None
            if st not in RUNNING:
                res["containers_job_ended"].append({**c, "job_state": st or "unknown"})
        elif not c["labels"].get("cwe.started_by"):        # started_by=script: another launcher, accounted for
            res["containers_unlabelled"].append(c)
    for pid, argv, _cwd, env in (procs.list_processes() if proc_list is None else proc_list):
        jid = (env or {}).get("CWEQ_JOB")
        if jid and jid.isdigit() and states.get(int(jid)) not in RUNNING:
            res["processes_job_ended"].append({"pid": pid, "job_id": int(jid), "job_state": states.get(int(jid)),
                                               "cmd": " ".join(argv)[:160]})
    return res
