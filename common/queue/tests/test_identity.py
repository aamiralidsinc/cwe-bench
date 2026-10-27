"""Process identity, labels and orphans (identity.py, common/harbor_ext/cwe_labels.py)."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import identity
import qdb
import worker
from conftest import wait_for, write_config

sys.path.insert(0, str(Path(identity.__file__).resolve().parents[1] / "harbor_ext"))
import cwe_labels  # noqa: E402


def fake_start(monkeypatch, table=None):
    """proc_start without /proc: a live pid gets a fixed start time (or the one in `table`)."""
    def ps(pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return None
        return (table or {}).get(pid, 4242)
    monkeypatch.setattr(identity, "proc_start", ps)


def claimed(conn, kind="regrade", task="t-s2", args=None):
    jid, _ = qdb.enqueue(conn, kind, task, args or {"trial": "j/t-s2__1", "why": "w"})
    assert qdb.claim(conn, jid, 600)
    return jid


# ---------- labels

def test_job_env_carries_every_label(root, conn):
    d = root / "pipelines" / "router" / "out" / "batches"
    d.mkdir(parents=True)
    (d / "scale-b9.txt").write_text("t-s2  # a comment\n")
    jid, _ = qdb.enqueue(conn, "trial_run", "t-s2", {"model": "mimo", "first_run": 2, "max_runs": 2})
    env = identity.job_env(qdb.get(conn, jid), d)
    assert env == {"CWE_JOB_ID": str(jid), "CWE_KIND": "trial_run", "CWE_TASK": "t-s2", "CWE_BATCH": "scale-b9",
                   "CWE_MODEL": "mimo", "CWE_RUN": "2-3", "CWE_CODE_VERSION": identity.code_version()}


def test_docker_labels_from_the_environment(tmp_path):
    env = {"CWE_JOB_ID": "17", "CWE_KIND": "trial_run", "CWE_TASK": "t-s2", "CWE_MODEL": "mimo", "CWE_RUN": "1",
           "CWE_CODE_VERSION": "abc12345", "CWE_BATCH": "", "OTHER": "x"}
    lab = cwe_labels.labels(env, "t-s2__AbC__env", "t-s2")
    assert lab == {"cwe.job_id": "17", "cwe.kind": "trial_run", "cwe.task": "t-s2", "cwe.model": "mimo",
                   "cwe.run": "1", "cwe.code_version": "abc12345", "cwe.started_by": "cweq",
                   "cwe.session": "t-s2__AbC__env"}
    f = cwe_labels.write_compose(tmp_path / "x" / "labels.json", lab)
    assert json.loads(f.read_text()) == {"services": {"main": {"labels": lab}}}


def test_runs_outside_the_queue_still_carry_their_task():
    lab = cwe_labels.labels({}, "s1", "stk-a-1")
    assert lab == {"cwe.task": "stk-a-1", "cwe.started_by": "script", "cwe.session": "s1"}
    assert cwe_labels.labels({"CWE_TASK": "a b;c"}, "", "")["cwe.task"] == "a_b_c"


def test_worker_gives_the_command_its_labels_and_records_identity(tmp_path, root):
    cfg = write_config(tmp_path, root, '[commands]\nregrade = ["sh", "-c", "env | grep ^CWE_"]\n')
    conn = qdb.connect(cfg["db"])
    jid = claimed(conn)
    assert worker.run(conn, cfg, jid) == 0
    log = Path(qdb.get(conn, jid)["log_path"]).read_text()
    assert f"CWE_JOB_ID={jid}" in log and "CWE_KIND=regrade" in log and "CWE_TASK=t-s2" in log
    p = identity.get(conn, jid)
    assert p["worker_pid"] == os.getpid() and p["child_pid"] and p["code_version"]


# ---------- stop

def test_stop_signals_the_verified_group_and_blocks_the_job(monkeypatch, conn):
    fake_start(monkeypatch)
    # A session leader that is not our child (its launcher exits at once), as a worker is to `cweq stop`.
    out = subprocess.run([sys.executable, "-c", "import subprocess as s; p = s.Popen(['sleep', '60'], start_new_session=True, "
                          "stdin=s.DEVNULL, stdout=s.DEVNULL, stderr=s.DEVNULL); print(p.pid)"], capture_output=True, text=True)
    pid = int(out.stdout)
    try:
        jid = claimed(conn)
        identity.record(conn, jid, 1, pid, pid)
        lines = identity.stop(conn, jid, grace=5, docker=lambda args: "")
        assert any("SIGTERM to process group" in x for x in lines)
        assert wait_for(lambda: identity.proc_start(pid) is None, 10)
        assert qdb.get(conn, jid)["state"] == "blocked"
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def test_stop_never_signals_a_reused_pid(monkeypatch, conn):
    w = subprocess.Popen(["sleep", "60"], start_new_session=True)
    try:
        jid = claimed(conn)
        fake_start(monkeypatch, {w.pid: 1})
        identity.record(conn, jid, 1, w.pid, w.pid)                      # recorded start 1
        fake_start(monkeypatch, {w.pid: 2})                              # same pid, other process now
        sent = []
        lines = identity.stop(conn, jid, grace=1, docker=lambda args: "",
                              killpg=lambda g, s: sent.append((g, s)))
        assert sent == [] and any("reused" in x for x in lines)
        assert w.poll() is None
    finally:
        w.kill()


def test_stop_removes_the_jobs_compose_project(conn, monkeypatch):
    fake_start(monkeypatch)
    jid, _ = qdb.enqueue(conn, "trial_run", "t-s2", {"model": "mimo"})
    ps = "\n".join(json.dumps(c) for c in [
        {"ID": "aaa", "Names": "t-s2__x__env-main-1", "State": "running",
         "Labels": f"cwe.job_id={jid},com.docker.compose.project=t-s2__x__env"},
        {"ID": "bbb", "Names": "t-s2__x__env-netguard-1", "State": "running",
         "Labels": "com.docker.compose.project=t-s2__x__env"},
        {"ID": "ccc", "Names": "other__y__env-main-1", "State": "running",
         "Labels": "cwe.job_id=999,com.docker.compose.project=other__y__env"}])
    calls = []

    def docker(args):
        calls.append(args)
        return ps if args[:1] == ["ps"] else ""
    lines = identity.stop(conn, jid, docker=docker)
    assert ["rm", "-f", "aaa", "bbb"] in calls
    assert any("removed 2 container" in x for x in lines)


# ---------- orphans

def test_orphans_lists_what_no_live_job_owns(conn):
    run_id = claimed(conn, task="live-s2")
    done_id, _ = qdb.enqueue(conn, "regrade", "old-s2", {"trial": "j/old"})
    qdb.set_state(conn, done_id, "done", "ok")
    ps = "\n".join(json.dumps(c) for c in [
        {"ID": "a1", "Names": "live", "State": "running", "Labels": f"cwe.job_id={run_id},cwe.task=live-s2"},
        {"ID": "b1", "Names": "ended", "State": "running", "Labels": f"cwe.job_id={done_id},cwe.task=old-s2"},
        {"ID": "c1", "Names": "t__z__env-main-1", "State": "exited",
         "Labels": "com.docker.compose.project=t__z__env"},
        {"ID": "d1", "Names": "script-run", "State": "running",
         "Labels": "cwe.task=x,cwe.started_by=script,com.docker.compose.project=x__q__env"},
        {"ID": "e1", "Names": "unrelated-db", "State": "running", "Labels": "app=postgres"}])
    procs = [(101, ["python3", "worker"], None, {"CWEQ_JOB": str(done_id)}),
             (102, ["python3", "worker"], None, {"CWEQ_JOB": str(run_id)}),
             (103, ["bash"], None, {})]
    res = identity.orphans(conn, docker=lambda args: ps, proc_list=procs)
    assert [c["id"] for c in res["containers_job_ended"]] == ["b1"]
    assert [c["id"] for c in res["containers_unlabelled"]] == ["c1"]
    assert [p["pid"] for p in res["processes_job_ended"]] == [101]
