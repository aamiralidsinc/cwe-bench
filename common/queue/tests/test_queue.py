"""The job table and the dispatcher: idempotent enqueue, priority with aging, admission limits, stale workers,
dependencies, holds, and real worker processes running fake commands (true / false / sleep)."""
import os
import subprocess
import time

import dispatch
import qdb
import worker
from conftest import wait_for, write_config

OPEN = {"free_disk_gb": 999, "load": 1, "mem_available_gb": 999, "tmp_inode_pct": 1}


def disp(conn, cfg, metrics=OPEN, spawn=None):
    return dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: dict(metrics), proc_list=[],
                               spawn=spawn or (lambda job_id: 999999), sleep=lambda s: None)


def test_enqueue_is_idempotent(conn):
    a, new_a = qdb.enqueue(conn, "regrade", "t1", {"trial": "j/t", "fp": "ab"})
    b, new_b = qdb.enqueue(conn, "regrade", "t1", {"fp": "ab", "trial": "j/t"})      # same args, other order
    c, new_c = qdb.enqueue(conn, "regrade", "t1", {"trial": "j/t2", "fp": "ab"})
    assert (a, new_a) == (b, True) and new_b is False
    assert c != a and new_c
    assert len(qdb.jobs(conn)) == 2


def test_enqueue_rejects_unknown_kind(conn):
    import pytest
    with pytest.raises(ValueError):
        qdb.enqueue(conn, "launch_rockets", "t1")


def test_priority_then_aging(conn, cfg):
    lo, _ = qdb.enqueue(conn, "regrade", "a", priority=0)
    hi, _ = qdb.enqueue(conn, "regrade", "b", priority=50)
    starts, _ = disp(conn, cfg).plan()
    assert [r["id"] for r, _ in starts] == [hi, lo]
    # lo has waited 10 h: 0 + 10/h x 10 h = 100 > 50
    conn.execute("UPDATE jobs SET queued_at=? WHERE id=?", (qdb.utc(time.time() - 36000), lo))
    starts, _ = disp(conn, cfg).plan()
    assert [r["id"] for r, _ in starts] == [lo, hi]


def test_admission_limits_block_starts(conn, cfg):
    for t in ("a", "b", "c", "d"):
        qdb.enqueue(conn, "regrade", t)
    starts, waits = disp(conn, cfg, metrics=dict(OPEN, load=900)).plan()
    assert not starts and all("admission closed: load 900" in w for _, w in waits)
    starts, waits = disp(conn, cfg, metrics=dict(OPEN, free_disk_gb=10, tmp_inode_pct=95)).plan()
    assert not starts and "free disk" in waits[0][1] and "/tmp inodes" in waits[0][1]
    # per-kind limit: regrade = 3
    starts, waits = disp(conn, cfg).plan()
    assert len(starts) == 3 and "regrade at its limit" in waits[0][1]


def test_per_task_and_total_limits(tmp_path, root):
    cfg = write_config(tmp_path, root, "[dispatch]\nmax_running_total = 2\nstart_spacing_sec = 0\nfill_spacing_sec = 0\n"
                                       "max_starts_per_tick = 50\n")
    conn = qdb.connect(cfg["db"])
    qdb.enqueue(conn, "regate", "a")
    qdb.enqueue(conn, "regrade", "a", {"trial": "x"})
    qdb.enqueue(conn, "regrade", "b", {"trial": "y"})
    qdb.enqueue(conn, "rescore", "c", {"trial": "z"})
    starts, waits = disp(conn, cfg).plan()
    assert [(r["kind"], r["task"]) for r, _ in starts] == [("regate", "a"), ("regrade", "b")]
    reasons = {r["task"] + r["kind"]: w for r, w in waits}
    assert reasons["aregrade"] == "another job of this task is running"
    assert reasons["crescore"].startswith("total at its limit")


def test_kind_without_worker_never_starts(conn, cfg):
    qdb.enqueue(conn, "fairness", "a")                 # audits and fairness move into the queue in phase 4
    starts, waits = disp(conn, cfg).plan()
    assert not starts and waits[0][1] == "no worker for fairness in phase 1"


def test_switched_off_starts_nothing(tmp_path, root):
    cfg = write_config(tmp_path, root, "enabled = false\n")
    conn = qdb.connect(cfg["db"])
    qdb.enqueue(conn, "regate", "a")
    starts, waits = disp(conn, cfg).plan()
    assert not starts and "switched off" in waits[0][1]


def dead_pid():
    p = subprocess.Popen(["true"])
    p.wait()
    return p.pid


def test_dead_worker_requeued_then_blocked(conn, cfg):
    jid, _ = qdb.enqueue(conn, "regate", "a", max_attempts=2)
    d = disp(conn, cfg, spawn=lambda job_id: dead_pid())
    d.tick()
    assert qdb.get(conn, jid)["state"] == "leased"
    (rid, state, why), = d.reap()
    assert (rid, state) == (jid, "queued") and "gone" in why
    d.tick()                                             # second attempt, the worker dies again
    d.reap()
    row = qdb.get(conn, jid)
    assert row["state"] == "blocked" and row["attempts"] == 2


def test_expired_lease_kills_group_and_requeues(conn, cfg):
    jid, _ = qdb.enqueue(conn, "regrade", "a", {"trial": "x"}, max_attempts=3)
    hung = subprocess.Popen(["sleep", "60"], start_new_session=True)
    d = disp(conn, cfg, spawn=lambda job_id: hung.pid)
    d.tick()
    conn.execute("UPDATE jobs SET state='running', lease_expires=? WHERE id=?", (qdb.utc(time.time() - 5), jid))
    (rid, state, why), = d.reap()
    assert state == "queued" and "expired" in why
    assert hung.wait(timeout=10) != 0                    # SIGTERM to its process group


def test_dependency_waits_then_blocks_and_retry_reopens(conn, cfg):
    gate, _ = qdb.enqueue(conn, "regate", "a")
    rg, _ = qdb.enqueue(conn, "regrade", "a", {"trial": "x"}, depends_on=[gate])
    d = disp(conn, cfg)
    starts, waits = d.plan()
    assert [r["id"] for r, _ in starts] == [gate]
    assert dict((r["id"], w) for r, w in waits)[rg] == f"waiting for #{gate}"
    qdb.set_state(conn, gate, "done")
    starts, _ = d.plan()
    assert [r["id"] for r, _ in starts] == [rg]
    qdb.set_state(conn, gate, "failed", "unsound")
    assert d.block_broken_deps() == [(rg, f"dependency #{gate} failed")]
    assert qdb.get(conn, rg)["state"] == "blocked"
    assert sorted(qdb.retry(conn, gate)) == sorted([gate, rg])
    assert qdb.get(conn, rg)["state"] == "queued"


def test_hold_blocks_trials_only(conn, cfg, root):
    b = root / "build" / "a"
    b.mkdir()
    (b / ".hold-repair").touch()
    cfg["limits"]["max_running"]["trial_run"] = 5
    tr, _ = qdb.enqueue(conn, "trial_run", "a", {"model": "deepseek"})
    rg, _ = qdb.enqueue(conn, "regate", "a")
    starts, waits = disp(conn, cfg).plan()
    assert [r["id"] for r, _ in starts] == [rg]
    assert dict((r["id"], w) for r, w in waits)[tr] == "held (.hold-repair)"
    (b / ".hold-repair").unlink()
    (b / "hold_deepseek").touch()
    assert "held (hold_deepseek)" in [w for _, w in disp(conn, cfg).plan()[1]]


def test_busy_task_is_skipped(conn, cfg, root, tmp_path):
    qdb.enqueue(conn, "regate", "stk-a")
    qdb.enqueue(conn, "regate", "stk-b")
    qdb.enqueue(conn, "regate", "stk-a2")
    lst = tmp_path / "regate-list.txt"
    lst.write_text("stk-b\n")
    fake = [(1, ["bash", "common/gate/regate.sh", "stk-a", "--listing"], None, {}),
            (2, ["python3", "pipelines/router/regate_queue.py", str(lst), "10"], None, {}),
            (3, ["bash", "common/gate/regate.sh", "stk-a2"], None, {"CWEQ_JOB": "7"})]   # our own worker
    d = disp(conn, cfg)
    d.proc_list = fake
    starts, waits = d.plan()
    assert [r["task"] for r, _ in starts] == ["stk-a2"]
    assert all(w.startswith("task busy") for _, w in waits)


# ---- real worker processes (fake commands)

def run_until_settled(d, conn, ids, timeout=30):
    def settled():
        d.tick()
        return all(qdb.get(conn, i)["state"] in ("done", "failed", "blocked") for i in ids)
    assert wait_for(settled, timeout), [dict(qdb.get(conn, i)) for i in ids]


def test_workers_run_fake_commands(tmp_path, root):
    cfg = write_config(tmp_path, root, '[commands]\nregate = ["true"]\nregrade = ["false"]\n'
                                       'rescore = ["sh", "-c", "echo rescored {task} {trial}"]\n'
                                       "[dispatch]\nstart_spacing_sec = 0\nfill_spacing_sec = 0\nmax_starts_per_tick = 10\nlease_sec = 20\n")
    conn = qdb.connect(cfg["db"])
    ok, _ = qdb.enqueue(conn, "regate", "a")
    bad, _ = qdb.enqueue(conn, "regrade", "b", {"trial": "j/t"})
    rs, _ = qdb.enqueue(conn, "rescore", "c", {"trial": "j/t", "drop": ["X"], "why": "w"})
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: dict(OPEN), proc_list=[])
    run_until_settled(d, conn, [ok, bad, rs])
    assert (qdb.get(conn, ok)["state"], qdb.get(conn, ok)["exit_code"]) == ("done", 0)
    assert (qdb.get(conn, bad)["state"], qdb.get(conn, bad)["exit_code"]) == ("failed", 1)
    r = qdb.get(conn, rs)
    assert r["state"] == "done" and r["result"] == f"rescored c {root / 'jobs' / 'j/t'}"
    assert os.path.isfile(r["log_path"])


def test_retryable_exit_requeues_then_blocks(tmp_path, root):
    cfg = write_config(tmp_path, root, '[commands]\nregate = ["sh", "-c", "exit 2"]\n'
                                       "[dispatch]\nstart_spacing_sec = 0\nfill_spacing_sec = 0\nlease_sec = 20\n")
    conn = qdb.connect(cfg["db"])
    jid, _ = qdb.enqueue(conn, "regate", "a", max_attempts=2)
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: dict(OPEN), proc_list=[])
    run_until_settled(d, conn, [jid])
    row = qdb.get(conn, jid)
    assert row["state"] == "blocked" and row["attempts"] == 2 and row["exit_code"] == 2


def test_worker_reholds_a_held_task_after_regate(tmp_path, root):
    b = root / "build" / "a"
    b.mkdir()
    (b / ".hold-repair").touch()
    cfg = write_config(tmp_path, root, f'[commands]\nregate = ["touch", "{b / ".sound"}"]\n')
    conn = qdb.connect(cfg["db"])
    jid, _ = qdb.enqueue(conn, "regate", "a")
    assert qdb.claim(conn, jid, 60)
    assert worker.run(conn, cfg, jid) == 0               # in-process, so it sees the fake build/ tree
    assert (b / ".hold-repair").exists() and not (b / ".sound").exists()
    assert qdb.get(conn, jid)["state"] == "done"


def test_worker_stops_when_job_is_taken_away(tmp_path, root):
    cfg = write_config(tmp_path, root, '[commands]\nregrade = ["sleep", "30"]\n[dispatch]\nlease_sec = 10\n'
                                       "start_spacing_sec = 0\nfill_spacing_sec = 0\n")
    conn = qdb.connect(cfg["db"])
    jid, _ = qdb.enqueue(conn, "regrade", "a", {"trial": "x"})
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: dict(OPEN), proc_list=[])
    d.tick()
    assert wait_for(lambda: qdb.get(conn, jid)["state"] == "running")
    pid = qdb.get(conn, jid)["owner_pid"]
    qdb.set_state(conn, jid, "blocked", "blocked by hand")
    child = d.children[0]
    assert child.wait(timeout=15) is not None            # the wrapper noticed at its next refresh and stopped
    assert qdb.get(conn, jid)["state"] == "blocked" and pid
