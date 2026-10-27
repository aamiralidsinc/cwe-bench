"""Phase 4 (phase4.py): audit preparation and recording, fairness, the hourly cleanup and router step 3, which replace
pipelines/router/auto_advance.sh and the hourly_cleanup.sh loop."""
import json
import os
import sqlite3
import time

import dispatch
import phase4
import qdb
import taskstate
import worker

HOUR = 1_800_000_000          # a fixed "now" (UTC 2027-01-15T08:00)


def ledger(root, rows):
    a = root / "build" / "audit"
    a.mkdir(parents=True, exist_ok=True)
    body = "".join(f"| stacking | {s} | {d} | {m} | {v} |\n" for s, d, m, v in rows)
    (a / "ledger.md").write_text("# Ledger\n\n## All tasks\n\n| Track | Task | DeepSeek | MiMo | Verdict |\n"
                                 "|---|---|---|---|---|\n" + body)


def awaiting(root, runs):
    """runs: (job, trial)."""
    a = root / "build" / "audit"
    a.mkdir(parents=True, exist_ok=True)
    (a / "awaiting_audit.tsv").write_text("task\tmodel\treward\tjob\ttrial\tgrading\n" + "".join(
        f"{t.split('__')[0]}\tm\t0.5\t{j}\t{t}\toriginal\n" for j, t in runs))


def trial(root, job, name):
    t = root / "jobs" / job / name
    (t / "verifier").mkdir(parents=True, exist_ok=True)
    (t / "result.json").write_text("{}")
    return t


def batch(root, slugs):
    d = root / "pipelines" / "router" / "out" / "batches"
    d.mkdir(parents=True, exist_ok=True)
    (d / "scale-b9.txt").write_text("\n".join(slugs) + "\n")


def on(cfg, **switches):
    cfg["phase4"] = {"enabled": True, "audits": False, "fairness": False, "cleanup": False, "step3": False, **switches}
    return cfg


def plan(cfg, procs=()):
    ctx = taskstate.context(list(procs))
    return ctx


def proc(pid, cmd, env=None):
    return (pid, cmd.split(), None, env or {})


def wanted(rep, kind=None):
    return [(w["kind"], w["task"], w["args"]) for r in rep for w in r["want"] if kind in (None, w["kind"])]


# ---------- A1 audit_prep

def test_audit_prep_selection(root, conn, cfg):
    on(cfg, audits=True)
    j = {n: f"{t}-{m}-r1-20261027-000000-n001" for n, t, m in (
        ("a", "a-s2", "deepseek"), ("held", "held-s2", "mimo"), ("solved", "sol-s2", "mimo"),
        ("both", "both-s2", "deepseek"), ("ready", "rdy-s2", "deepseek"), ("old", "old-s2", "mimo"))}
    runs = [(j["a"], "a-s2__A"), (j["held"], "held-s2__H"), (j["solved"], "sol-s2__S"), (j["both"], "both-s2__B"),
            (j["ready"], "rdy-s2__R"), (j["old"], "old-s2__O")]
    for job, t in runs:
        trial(root, job, t)
    awaiting(root, runs)
    (root / "build" / "held-s2").mkdir(parents=True)
    (root / "build" / "held-s2" / ".hold-repair").write_text("")
    ledger(root, [("sol-s2", "**failed 0/3**", "SOLVED 1/1", "rejected (MiMo solved)"),
                  ("both-s2", "SOLVED 1/1", "SOLVED 1/1", "rejected (both solved)")])
    # rdy: a folder prepared for the grading in use, waiting for its auditor
    pm = root / "jobs" / j["ready"] / "rdy-s2__R" / "postmortem-20261027T000000Z"
    pm.mkdir()
    (pm / "PREPARED.json").write_text(json.dumps({"grading_audited": "original"}))
    # old: prepared before a regrade -> prepare again for the regrade
    o = root / "jobs" / j["old"] / "old-s2__O"
    (o / "postmortem-20261027T000000Z").mkdir()
    (o / "postmortem-20261027T000000Z" / "PREPARED.json").write_text(json.dumps({"grading_audited": "original"}))
    (o / "regrade-20261027T010000Z" / "verifier").mkdir(parents=True)
    rep = phase4.reconcile(conn, cfg, taskstate.context([]), [], now=HOUR)
    prep = wanted(rep, "audit_prep")
    assert prep == [("audit_prep", "a-s2", {"trial": f"{j['a']}/a-s2__A", "grading": "original"}),
                    ("audit_prep", "old-s2", {"trial": f"{j['old']}/old-s2__O",
                                              "grading": "regrade-20261027T010000Z"})]
    notes = " ".join(n for r in rep for n in r["notes"])
    assert "held for a repair" in notes and "mimo already solved sol-s2" in notes
    assert (root / "pipelines/router/out/queue/audit_ready.txt").read_text().strip() == str(pm)
    # idempotent: a second pass queues nothing new
    n = len(qdb.jobs(conn))
    phase4.reconcile(conn, cfg, taskstate.context([]), [], now=HOUR)
    assert len(qdb.jobs(conn)) == n


def test_busy_repair_task_is_not_prepared(root, conn, cfg):
    on(cfg, audits=True)
    job = "bz-s2-deepseek-r1-20261027-000000-n001"
    trial(root, job, "bz-s2__Z")
    awaiting(root, [(job, "bz-s2__Z")])
    ps = [proc(7, "bash common/gate/regate.sh bz-s2")]
    rep = phase4.reconcile(conn, cfg, taskstate.context(ps), ps, now=HOUR)
    assert not wanted(rep, "audit_prep")


# ---------- A2 audit_record

def test_audit_record_when_verdicts_or_newer_results(root, conn, cfg):
    on(cfg, audits=True)
    t = trial(root, "x-s2-mimo-r1-20261027-000000-n001", "x-s2__X")
    ledger(root, [])
    led = root / "build" / "audit" / "ledger.md"
    os.utime(led, (time.time() + 100, time.time() + 100))          # ledger newer than every result
    assert not wanted(phase4.reconcile(conn, cfg, taskstate.context([]), [], now=HOUR), "audit_record")
    pm = t / "postmortem-20261027T000000Z"
    pm.mkdir()
    (pm / "verdict.json").write_text("{}")
    os.utime(pm / "verdict.json", (time.time() + 200, time.time() + 200))
    rec = wanted(phase4.reconcile(conn, cfg, taskstate.context([]), [], now=HOUR), "audit_record")
    assert len(rec) == 1 and rec[0][1] == phase4.LEDGER
    # same state: the same key, nothing new
    phase4.reconcile(conn, cfg, taskstate.context([]), [], now=HOUR)
    assert len(qdb.jobs(conn, "kind='audit_record'")) == 1


# ---------- F1 fairness

def test_fairness_rule(root, conn, cfg):
    on(cfg, fairness=True)
    batch(root, ["stk-a-1", "b-s2", "c-s2", "d-s2"])
    ledger(root, [("stk-a-1", "**failed 0/3**", "**failed 0/3**", "**BREAKER candidate**"),
                  ("b-s2", "**failed 0/3**", "**failed 0/3**", "**BREAKER candidate**"),
                  ("c-s2", "**failed 0/3**", "**failed 0/3**", "**BREAKER candidate**"),
                  ("d-s2", "**failed 0/3**", "**failed 0/3**", "**BREAKER candidate**")])
    for s in ("stk-a-1", "b-s2", "c-s2", "d-s2"):
        trial(root, f"{s}-mimo-r3-20261027-000000-n003", f"{s}__T")
        (root / "build" / s).mkdir(parents=True, exist_ok=True)
    # b: reviewed after its newest trial; c: held; d: an old-script review is running
    (root / "build" / "b-s2" / "FAIRNESS.md").write_text("GATE_A: READY\n")
    later = time.time() + 50
    os.utime(root / "build" / "b-s2" / "FAIRNESS.md", (later, later))
    (root / "build" / "c-s2" / ".hold-repair").write_text("")
    ps = [proc(9, "bash pipelines/sibling/9-fairness/run_fairness.sh d-s2")]
    rep = phase4.reconcile(conn, cfg, taskstate.context(ps), ps, now=HOUR)
    assert [(k, t) for k, t, _a in wanted(rep, "fairness")] == [("fairness", "stk-a-1")]
    row = qdb.jobs(conn, "kind='fairness'")[0]
    argv = worker.command(row, cfg)
    assert argv[-2:] == ["pipelines/stacking/7-fairness/run_fairness_stack.sh", "stk-a-1"]
    assert "fairness.nohup" in argv[2]


def test_stacking_fairness_process_is_seen(root):
    ctx = taskstate.context([proc(3, "bash pipelines/stacking/7-fairness/run_fairness_stack.sh stk-q-1")])
    assert ctx["running"]["stk-q-1"][0][0] == "fairness"


# ---------- C1 cleanup and S3 step3

def test_cleanup_one_per_hour_and_supersede(root, conn, cfg):
    on(cfg, cleanup=True, step3=True)
    phase4.reconcile(conn, cfg, taskstate.context([]), [], now=HOUR)
    phase4.reconcile(conn, cfg, taskstate.context([]), [], now=HOUR + 600)
    rows = qdb.jobs(conn, "kind='cleanup'")
    assert len(rows) == 1 and qdb.args_of(rows[0]) == {"hour": "2027-01-15T08"}
    phase4.reconcile(conn, cfg, taskstate.context([]), [], now=HOUR + 3600)
    st = {qdb.args_of(r)["hour"]: r["state"] for r in qdb.jobs(conn, "kind='cleanup'")}
    assert st == {"2027-01-15T08": "done", "2027-01-15T09": "queued"}
    assert len(qdb.jobs(conn, "kind='step3'")) == 2                  # 08:00 and 08:10 share a slot; 09:00
    assert worker.command(qdb.jobs(conn, "kind='cleanup'")[-1], cfg) == ["bash", "common/util/hourly_cleanup.sh", "once"]


def test_no_queue_cleanup_while_the_old_loop_runs(root, conn, cfg):
    on(cfg, cleanup=True)
    ps = [proc(4, "bash common/util/hourly_cleanup.sh loop")]
    rep = phase4.reconcile(conn, cfg, taskstate.context(ps), ps, now=HOUR)
    assert not wanted(rep, "cleanup")


def test_light_kinds_ignore_machine_limits_and_total(root, conn, cfg):
    cfg["limits"]["min_free_disk_gb"] = 10_000                       # admission closed for everything else
    cfg["dispatch"]["max_running_total"] = 0
    qdb.enqueue(conn, "cleanup", phase4.MACHINE, {"hour": "h"})
    qdb.enqueue(conn, "regate", "a-s2", {})
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: {"free_disk_gb": 1, "load": 0,
                                                                  "mem_available_gb": 999, "tmp_inode_pct": 0},
                            proc_list=[], spawn=lambda i: 1)
    starts, waits = d.plan()
    assert [r["kind"] for r, _ in starts] == ["cleanup"]
    assert waits and waits[0][0]["kind"] == "regate"


# ---------- schema migration and the status line

def test_old_database_gains_the_new_kinds(tmp_path):
    db = tmp_path / "old.db"
    c = sqlite3.connect(db)
    old = qdb.SCHEMA.split("CREATE TABLE IF NOT EXISTS adoptions")[0]
    for k in ("audit_record", "step3"):
        old = old.replace(f", '{k}'", "")
    c.executescript(old)
    c.execute("INSERT INTO jobs (kind, task, args, created, queued_at) VALUES ('regate','t','{}','x','x')")
    c.commit()
    c.close()
    conn = qdb.connect(db)
    assert qdb.get(conn, 1)["kind"] == "regate"
    jid, _ = qdb.enqueue(conn, "audit_record", "_ledger", {"token": 1})
    assert jid == 2 and not qdb.migrate(conn)


def test_queue_line(root, conn, cfg):
    import cweq
    qdb.enqueue(conn, "build", "a-s2", {})
    line = cweq.queue_line(conn, [proc(5, "python3 -I common/trial/trial.py b-s2 --models mimo")])
    assert line == "work queue: build 0 running, 1 queued; trial_run 0 (+1 old) running, 0 queued"
