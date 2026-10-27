"""Post-condition checks (checks.py): a job is done only when the files show its outcome; tool self-checks."""
import json
import os
import time

import checks
import dispatch
import qdb
from conftest import gate_log, make_task, write_fingerprint


def stamp(t):
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(t))


def job(conn, kind, task, args, started):
    jid, _ = qdb.enqueue(conn, kind, task, args)
    conn.execute("UPDATE jobs SET state='done', started=?, exit_code=0 WHERE id=?", (qdb.utc(started), jid))
    return qdb.get(conn, jid)


def trial_dir(root, slug, name="T1"):
    t = root / "jobs" / f"{slug}-m-r1" / f"{slug}__{name}"
    (t / "verifier").mkdir(parents=True, exist_ok=True)
    return t


def regrade_dir(t, when, reward, **info):
    d = t / f"regrade-{stamp(when)}"
    (d / "verifier").mkdir(parents=True)
    (d / "REGRADE.json").write_text(json.dumps({"reward": reward, **info}))
    if reward is not None:
        (d / "verifier" / "reward.json").write_text(json.dumps({"reward": reward}))
    return d


def test_regrade_needs_a_scored_new_folder(root, conn, cfg):
    t0 = time.time() - 60
    t = trial_dir(root, "a-s2")
    rel = f"{t.parent.name}/{t.name}"
    row = job(conn, "regrade", "a-s2", {"trial": rel}, t0)
    assert checks.evaluate(row, cfg)[:2] == ("fail", "regrade.folder")
    regrade_dir(t, t0 - 3600, 0.5)                       # an older regrade does not count
    assert checks.evaluate(row, cfg)[0] == "fail"
    regrade_dir(t, t0 + 10, None)                        # ran, but could not score: a person looks
    assert checks.evaluate(row, cfg)[:2] == ("person", "regrade.scored")
    regrade_dir(t, t0 + 20, 0.0)                         # 0.0 is a score
    assert checks.evaluate(row, cfg)[0] == "pass"


def test_rescore_checks_the_drops(root, conn, cfg):
    t0 = time.time() - 60
    t = trial_dir(root, "b-s2")
    rel = f"{t.parent.name}/{t.name}"
    row = job(conn, "rescore", "b-s2", {"trial": rel, "drop": ["nat64_case"]}, t0)
    d = regrade_dir(t, t0 + 5, 0.5, method="rescore-from-results", dropped=["security:nat64_case=fail"])
    (d / "verifier" / "results.json").write_text(json.dumps({"security": {"other": "pass"}, "functional": {}}))
    assert checks.evaluate(row, cfg)[0] == "pass"
    (d / "verifier" / "results.json").write_text(json.dumps({"security": {"nat64_case": "fail"}}))
    assert checks.evaluate(row, cfg)[:2] == ("fail", "rescore.dropped_absent")


def test_regate_needs_a_fresh_sound_result_marker_and_fingerprint(root, conn, cfg):
    make_task(root, "c-s2", {"t.py": "x"})
    t0 = time.time() - 60
    row = job(conn, "regate", "c-s2", {"fp": "x"}, t0)
    gate_log(root, "c-s2", t0 - 600, "SOUND, ready for trials")
    assert checks.evaluate(row, cfg)[:2] == ("fail", "regate.result")   # the RESULT predates the job
    gate_log(root, "c-s2", t0 + 30, "SOUND, ready for trials (regate)")
    (root / "build" / "c-s2" / ".hold-repair").write_text("")            # a held task keeps .hold-repair
    write_fingerprint(root, "c-s2")
    assert checks.evaluate(row, cfg)[0] == "pass"
    (root / "tasks" / "c-s2" / "tests" / "t.py").write_text("changed")  # files changed after the gate
    assert checks.evaluate(row, cfg)[:2] == ("fail", "regate.fingerprint")


def test_build_needs_an_end_and_an_outcome(root, conn, cfg):
    b = root / "build" / "d-s2"
    b.mkdir(parents=True)
    t0 = time.time() - 120
    row = job(conn, "build", "d-s2", {}, t0)
    (b / "start_utc.txt").write_text(qdb.utc(t0 + 1) + "\n")
    (b / "end_utc.txt").write_text(qdb.utc(t0 + 60) + "\n")
    assert checks.evaluate(row, cfg)[:2] == ("person", "build.outcome")
    (b / ".unsound").write_text("")                      # a recorded outcome, whatever it is
    assert checks.evaluate(row, cfg)[0] == "pass"


def test_trial_run_needs_rows_for_its_runs(root, conn, cfg):
    b = root / "build" / "e-s2"
    b.mkdir(parents=True)
    t0 = time.time() - 120
    row = job(conn, "trial_run", "e-s2", {"model": "mimo", "first_run": 2, "max_runs": 1}, t0)
    assert checks.evaluate(row, cfg)[:2] == ("fail", "trial_run.rows")
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t0 + 30))
    (b / "runs_mimo.log").write_text(f"{ts}\tn001\treward=0.5\tcause=None\te-s2-mimo-r2-20261027-100000-n001\n")
    assert checks.evaluate(row, cfg)[0] == "pass"
    with open(b / "runs_mimo.log", "a") as f:
        f.write(f"{ts}\tn002\treward=0.5\tcause=None\te-s2-mimo-r7-20261027-100000-n002\n")
    assert checks.evaluate(row, cfg)[:2] == ("fail", "trial_run.in_range")
    os.remove(b / "runs_mimo.log")
    (b / "hold_mimo").write_text("")                     # held: trial.py starts nothing, and that is the outcome
    assert checks.evaluate(row, cfg)[0] == "pass"


def test_fairness_needs_a_finished_review_with_a_verdict(root, conn, cfg):
    b = root / "build" / "f-s2"
    b.mkdir(parents=True)
    t0 = time.time() - 60
    row = job(conn, "fairness", "f-s2", {}, t0)
    (b / "fairness_status.txt").write_text("ok\n")
    (b / "FAIRNESS.md").write_text("# Review\nno verdict here\n")
    assert checks.evaluate(row, cfg)[:2] == ("person", "fairness.verdict")
    (b / "FAIRNESS.md").write_text("# Review\nGATE_A: NOT_READY\n")
    assert checks.evaluate(row, cfg)[0] == "pass"        # NOT_READY is a finished review


def test_audit_record_and_cleanup(root, conn, cfg):
    a = root / "build" / "audit"
    a.mkdir(parents=True)
    t0 = time.time() - 60
    rec = job(conn, "audit_record", "_ledger", {"token": 1}, t0)
    (a / "ledger.md").write_text("x")
    assert checks.evaluate(rec, cfg)[:2] == ("fail", "audit_record.trials.tsv")
    (a / "trials.tsv").write_text("x")
    assert checks.evaluate(rec, cfg)[0] == "pass"
    cl = job(conn, "cleanup", "_machine", {"hour": "x"}, t0)
    (a / "hourly_cleanup.log").write_text(f"{qdb.utc(t0 - 3600)} pass done: free 500 GB\n")
    assert checks.evaluate(cl, cfg)[0] == "fail"
    with open(a / "hourly_cleanup.log", "a") as f:
        f.write(f"{qdb.utc(t0 + 30)} pass done: free 510 GB\n")
    assert checks.evaluate(cl, cfg)[0] == "pass"


def test_after_done_turns_a_failed_check_into_failed_or_blocked(root, conn, cfg):
    t0 = time.time() - 60
    t = trial_dir(root, "g-s2")
    row = job(conn, "regrade", "g-s2", {"trial": f"{t.parent.name}/{t.name}"}, t0)
    assert checks.after_done(conn, cfg, row["id"]) == "failed"
    r = qdb.get(conn, row["id"])
    assert r["state"] == "failed" and r["result"].startswith("post-condition failed: regrade.folder")
    got = conn.execute("SELECT verdict, failed FROM job_checks WHERE job_id=?", (row["id"],)).fetchone()
    assert tuple(got) == ("fail", "regrade.folder")
    row2 = job(conn, "step3", "_router", {"slot": "x"}, t0)          # no file outcome: the exit code decides
    assert checks.after_done(conn, cfg, row2["id"]) == "done"
    cfg["checks"]["enabled"] = False
    row3 = job(conn, "regrade", "g-s2", {"trial": "other"}, t0)
    assert checks.after_done(conn, cfg, row3["id"]) == "done"


def test_dispatcher_holds_a_tool_whose_selfcheck_failed(root, conn, cfg):
    cfg["commands"] = {"regrade": ["true"], "rescore": ["true"]}
    qdb.enqueue(conn, "regrade", "h-s2", {"trial": "j/h-s2__1"})
    qdb.enqueue(conn, "rescore", "i-s2", {"trial": "j/i-s2__1", "drop": ["x"]})
    checks.ensure(conn)
    conn.execute("INSERT INTO selfchecks (tool, started, finished, reference, expected, got, ok, dry_run)"
                 " VALUES ('regrade', ?, ?, 'j/ref', 0.5, 0.0, 0, 0)", (qdb.utc(), qdb.utc()))
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: {}, proc_list=[], spawn=lambda i: 1)
    starts, waits = d.plan()
    assert [r["kind"] for r, _ in starts] == ["rescore"]
    assert "failed its self-check" in dict((r["kind"], w) for r, w in waits)["regrade"]
    cfg["checks"]["refuse_on_failed_selfcheck"] = False
    assert {r["kind"] for r, _ in d.plan()[0]} == {"regrade", "rescore"}


def test_selfcheck_rescore_reproduces_on_a_private_copy(root, conn, cfg, tmp_path):
    make_task(root, "k-s2", {"t.py": "x"})
    old = time.time() - 7200
    os.utime(root / "tasks" / "k-s2" / "tests" / "t.py", (old, old))
    t = trial_dir(root, "k-s2")
    (t / "config.json").write_text(json.dumps({"task": {"path": "/x/tasks/k-s2"}}))
    (t / "result.json").write_text(json.dumps({"finished_at": qdb.utc(old + 60)}))
    (t / "verifier" / "results.json").write_text(json.dumps(
        {"security": {"a": "pass", "b": "fail", "drop_me": "fail"}, "functional": {"f": "pass"}}))
    (t / "verifier" / "reward.json").write_text(json.dumps({"reward": 0.3333}))
    regrade_dir(t, time.time() - 600, 0.5, method="rescore-from-results (test removal; no code re-run)",
                dropped=["security:drop_me=fail"])
    cfg["checks"]["selfcheck_dir"] = str(tmp_path / "sc")
    before = sorted(p.name for p in t.iterdir())
    refs = checks.references(cfg, "rescore")
    assert refs and refs[0]["drops"] == ["drop_me"] and refs[0]["expected"] == 0.5
    sid = checks.selfcheck(conn, cfg, "rescore", run=False, out=lambda *_: None)
    assert conn.execute("SELECT dry_run, ok FROM selfchecks WHERE id=?", (sid,)).fetchone()[:] == (1, None)
    sid = checks.selfcheck(conn, cfg, "rescore", run=True, out=lambda *_: None)
    row = conn.execute("SELECT ok, got FROM selfchecks WHERE id=?", (sid,)).fetchone()
    assert (row["ok"], row["got"]) == (1, 0.5)
    assert sorted(p.name for p in t.iterdir()) == before        # the real run folder is untouched
    assert checks.tool_refused(conn, "rescore", cfg) is None


def test_selfcheck_regrade_picks_an_unchanged_partial_run(root, conn, cfg):
    make_task(root, "m-s2", {"t.py": "x"})
    old = time.time() - 7200
    os.utime(root / "tasks" / "m-s2" / "tests" / "t.py", (old, old))
    t = trial_dir(root, "m-s2")
    (t / "config.json").write_text(json.dumps({"task": {"path": "/x/tasks/m-s2"}}))
    (t / "result.json").write_text(json.dumps({"finished_at": qdb.utc(old + 60),
                                               "verifier_result": {"rewards": {"reward": 0.4}}}))
    (t / "final-code").mkdir()
    (t / "final-code" / "changes.patch").write_text("")
    refs = checks.references(cfg, "regrade")
    assert [r["expected"] for r in refs] == [0.4]
    regrade_dir(t, time.time(), 0.4)                             # already regraded: not a reference any more
    assert checks.references(cfg, "regrade") == []
