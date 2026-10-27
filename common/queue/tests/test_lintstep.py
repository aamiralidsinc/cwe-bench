"""The task-quality lint as a light queue job (lintstep.py): once per task version, never holding other work."""
import json

import dispatch
import events
import lintstep
import qdb
import taskstate
from test_adopt import batch, built
from conftest import write_fingerprint
from test_phase3 import disp


def states(root):
    return events.read_all(taskstate.context([]))


def test_lint_once_per_task_version(root, conn, cfg):
    batch(root, "scale-b9", ["ok-s2", "nobatch-s2"])
    built(root, "ok-s2")                                    # SOUND, no runs yet: waiting_trials
    (root / "tasks" / "ok-s2" / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n")
    jobs = lintstep.plan(states(root))
    assert [j["task"] for j in jobs] == ["ok-s2"] and jobs[0]["args"] == {"fp": "legacy"}
    lintstep.reconcile(conn, cfg, states(root))
    lintstep.reconcile(conn, cfg, states(root))
    assert len(qdb.jobs(conn, "kind='lint'")) == 1          # enqueue is idempotent
    out = lintstep.out_path("ok-s2", "legacy")
    out.parent.mkdir(parents=True)
    out.write_text(json.dumps({"task": "ok-s2", "fp": "legacy", "warn": 0, "info": 1, "findings": []}))
    assert lintstep.plan(states(root)) == []                 # this version is linted
    write_fingerprint(root, "ok-s2")                         # a SOUND gate on the current files: a new version
    fp = taskstate.gate_sha16("ok-s2")
    assert fp != "legacy" and [j["args"]["fp"] for j in lintstep.plan(states(root))] == [fp]


def test_lint_run_writes_counts(root):
    built(root, "run-s2")
    (root / "tasks" / "run-s2" / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n")
    assert lintstep.run("run-s2", "f00d") == 0
    r = json.loads(lintstep.out_path("run-s2", "f00d").read_text())
    assert r["task"] == "run-s2" and r["fp"] == "f00d" and isinstance(r["findings"], list)
    assert r["warn"] == sum(1 for f in r["findings"] if f["severity"] == "warn")
    assert "lint" in lintstep.line("run-s2")


def test_lint_never_holds_a_task_or_the_start_budget(root, conn, cfg):
    cfg["commands"] = {"trial_run": ["true"], "lint": ["true"]}
    cfg["limits"]["max_running"].update({"trial_run": 5, "lint": 5})
    cfg["dispatch"]["max_running_per_task"] = 1
    cfg["dispatch"]["max_starts_per_tick"] = 1
    lid, _ = qdb.enqueue(conn, "lint", "t-s2", {"fp": "x"}, priority=90)
    qdb.claim(conn, lid, 600)
    qdb.start(conn, lid, 1, 600, "log")                      # a lint job runs on the task
    for i in range(3):
        qdb.enqueue(conn, "lint", f"o{i}-s2", {"fp": "x"}, priority=90)
    tid, _ = qdb.enqueue(conn, "trial_run", "t-s2", {"model": "mimo", "first_run": 1, "max_runs": 1}, priority=20)
    starts, waits = disp(conn, cfg).plan()
    started = {r["id"] for r, _ in starts}
    assert tid in started                                    # not held by the running lint, nor by queued lints
    assert sum(1 for r, _ in starts if r["kind"] == "lint") == 3
