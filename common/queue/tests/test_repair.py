"""Test repairs as queue work (2026-10-28): the repair kind, planning rule T1, the job (hold, inputs, checks, restore),
the hold lift R6, regrades by test content (R2), the fresh fairness review after a repair (F1), the dispatcher's
wait, the lost-repair report and the regrade check."""
import calendar
import json
import os
import sys
import time

import checks
import dispatch
import kinds
import phase4
import qdb
import reconcile
import repairjob
import repairstep
from conftest import gate_log, make_task, make_trial, set_mtime, write_fingerprint

DAY = 86400


def epoch(s):
    return calendar.timegm(time.strptime(s, "%Y%m%dT%H%M%SZ"))


def audit(trial, items, attribution="test-fault", stamp="20261025T145457Z", grading="original"):
    pm = trial / f"postmortem-{stamp}"
    pm.mkdir(parents=True)
    (pm / "PREPARED.json").write_text(json.dumps({"grading_audited": grading}))
    (pm / "POSTMORTEM.json").write_text(json.dumps({
        "grading_audited": grading, "recorded_utc": "2026-10-25T15:00:00+00:00",
        "verdict": {"trustworthy": attribution not in ("test-fault", "instruction-ambiguity"), "attribution": attribution,
                    "confidence": "high", "summary": "s", "items": items}}))
    return pm


UNFAIR = {"test": "security::t_unfair", "outcome": "fail", "verdict": "test-fault", "correct_fix_would_pass": False,
          "model_behaviour": "refused at store time"}
GENUINE = {"test": "security::t_real", "outcome": "fail", "verdict": "genuine-fail", "correct_fix_would_pass": True}


def audited_task(root, slug="rp-a", items=(UNFAIR,), attribution="test-fault", runs=2):
    make_task(root, slug, {"security/a_test.rs": "old", "functional/f_test.rs": "f"})
    (root / "tasks" / slug / "instruction.md").write_text("Fix it.\n")
    (root / "tasks" / slug / "task.toml").write_text("[verifier]\n")
    trials = []
    for n in range(1, runs + 1):
        t = make_trial(root, slug, n, epoch("20261025T120000Z") + n)
        audit(t, list(items), attribution)
        trials.append(t)
    return trials


def rcfg(cfg, **kw):
    c = dict(cfg)
    c["repair"] = {**cfg["repair"], **kw}
    return c


# ---------------------------------------------------------------- the kind

def test_kind_declared_with_its_command(cfg):
    kd = kinds.get("repair")
    assert kd.exclusive and kd.foreign == "repair" and kd.plan and kd.check
    argv = kd.command({"id": 7, "task": "rp-a", "args": json.dumps({"finding": "f-0123456789abcdef"})}, cfg)
    assert argv[:3] == ["bash", "common/launch/drive.sh", "deepseek"]          # DeepSeek, never Opus
    assert "common/queue/repairjob.py" in argv and argv[argv.index("--job") + 1] == "7"
    assert json.loads(argv[argv.index("--finding") + 1]) == "f-0123456789abcdef"


# ---------------------------------------------------------------- planning rule T1

def test_deciding_audit_is_planned_but_not_queued_while_auto_is_off(conn, cfg, root):
    audited_task(root)
    rep, = repairstep.plan(conn, cfg, {"ledger": {}}, {}, slugs=["rp-a"])
    f = rep["finding"]
    assert f["plan"] and f["key"].startswith("f-") and len(f["items"]) == 2
    assert rep["want"][0]["planned_only"] and not qdb.jobs(conn, "kind='repair'")
    assert any("cweq enqueue repair rp-a" in n for n in rep["notes"])
    assert conn.execute("SELECT COUNT(*) FROM events WHERE kind='repair.planned'").fetchone()[0] == 1


def test_auto_on_queues_one_job_per_finding(conn, cfg, root):
    audited_task(root)
    c = rcfg(cfg, auto=True)
    for _ in range(2):
        repairstep.plan(conn, c, {"ledger": {}}, {}, slugs=["rp-a"])
    rows = qdb.jobs(conn, "kind='repair'")
    assert len(rows) == 1 and qdb.args_of(rows[0])["finding"].startswith("f-")


def test_newer_repair_folder_covers_the_finding(conn, cfg, root):
    audited_task(root)
    rep = root / "build" / "rp-a" / "repaired-tests-20261026-fairness"
    rep.mkdir()
    set_mtime(rep, epoch("20261026T100000Z"))
    assert repairstep.findings("rp-a", cfg)["items"] == []
    older = root / "build" / "rp-a" / "testfix-20261024"       # an older testfix does not cover a later audit
    rep.rename(older)
    set_mtime(older, epoch("20261024T100000Z"))
    assert repairstep.findings("rp-a", cfg)["plan"]
    older.rename(root / "build" / "rp-a" / "testfix-20261026")   # a later testfix-* counts as a repair
    set_mtime(root / "build" / "rp-a" / "testfix-20261026", epoch("20261026T100000Z"))
    assert repairstep.findings("rp-a", cfg)["items"] == []


def test_not_planned_when_dropped_withdrawn_held_or_already_run(conn, cfg, root):
    audited_task(root)
    b = root / "build" / "rp-a"
    (b / "HUMAN-DECISION.md").write_text("DECISION: DROP\nDATE: 2026-10-27\n")
    assert "dropped" in repairstep.findings("rp-a", cfg)["why"]
    (b / "HUMAN-DECISION.md").write_text("CLIENT-AUDIT: WITHDRAW\n")
    assert "withdrawn" in repairstep.findings("rp-a", cfg)["why"]
    (b / "HUMAN-DECISION.md").unlink()
    (b / ".hold-repair").write_text("someone repairs by hand\n")
    assert "held" in repairstep.findings("rp-a", cfg)["why"]
    (b / ".hold-repair").unlink()
    key = repairstep.findings("rp-a", cfg)["key"]
    d = b / "repair-inputs-20261028T100000Z"
    d.mkdir()
    (d / "FINDING.json").write_text(json.dumps({"key": key}))
    (d / "JOB-RESULT.json").write_text(json.dumps({"result": "failed"}))
    f = repairstep.findings("rp-a", cfg)
    assert not f["plan"] and "already ran" in f["why"]


def test_non_deciding_unfair_test_is_planned_only_for_a_kept_task(conn, cfg, root):
    audited_task(root, items=(UNFAIR, GENUINE), attribution="model-failed")
    f = repairstep.findings("rp-a", cfg)
    assert f["items"] and not f["plan"] and "decided no run" in f["why"]
    (root / "build" / "rp-a" / "HUMAN-DECISION.md").write_text("DECISION: KEEP\nDATE: 2026-10-27\n")
    f = repairstep.findings("rp-a", cfg)
    assert f["plan"] and "standing rule" in f["why"]


def test_run_failing_only_unfair_tests_is_deciding(conn, cfg, root):
    audited_task(root, items=(UNFAIR,), attribution="model-failed")
    assert repairstep.findings("rp-a", cfg)["plan"]


def test_skip_solved(conn, cfg, root):
    audited_task(root)
    ctx = {"ledger": {"rp-a": {"deepseek": "SOLVED 1/3", "mimo": "failed 0/3", "verdict": "open"}}}
    f = repairstep.findings("rp-a", cfg, ctx)
    assert not f["plan"] and "solved" in f["why"]
    assert repairstep.findings("rp-a", rcfg(cfg, skip_solved=False), ctx)["plan"]


def test_fairness_conflict_and_owner_repair_decision_are_findings(conn, cfg, root):
    make_task(root, "rp-f", {"security/a.py": "x"})
    b = root / "build" / "rp-f"
    (b / "FAIRNESS.md").write_text("Review.\n\nGATE_A: NOT_READY\nCONFLICTS: 2; DECIDING: 1\nNEEDS_HUMAN_REVIEW: YES\n")
    (b / "fairness_status.txt").write_text("ok\n")
    f = repairstep.findings("rp-f", cfg)
    assert f["plan"] and f["items"][0]["source"] == "fairness"
    (b / "HUMAN-DECISION.md").write_text("CONFLICTS-RULED: 2099-01-01 KEEP the tests are right\n")
    assert repairstep.findings("rp-f", cfg)["items"] == []
    (b / "FAIRNESS.md").write_text("Review.\n\n## Required changes\n1. reword the instruction sentence\n\nGATE_A: NOT_READY\n")
    (b / "HUMAN-DECISION.md").unlink()
    f = repairstep.findings("rp-f", cfg)
    assert not f["items"] and any("may touch the instruction" in n for n in f["notes"])
    (b / "FAIRNESS.md").write_text("Review.\n\n## Required changes\n1. make tests/security/a.py accept any 4xx\n\n"
                                   "GATE_A: NOT_READY\n")
    assert repairstep.findings("rp-f", cfg)["plan"]
    (b / "FAIRNESS.md").unlink()
    (b / "HUMAN-DECISION.md").write_text("DECISION: REPAIR\nDATE: 2026-10-28\n")
    f = repairstep.findings("rp-f", cfg)
    assert f["plan"] and f["items"][0]["source"] == "decision"


def test_a_changed_finding_supersedes_the_queued_job_and_one_repair_at_a_time(conn, cfg, root):
    trials = audited_task(root)
    c = rcfg(cfg, auto=True)
    repairstep.plan(conn, c, {"ledger": {}}, {}, slugs=["rp-a"])
    first, = qdb.jobs(conn, "kind='repair'")
    audit(trials[0], [UNFAIR, dict(UNFAIR, test="security::t_two")], stamp="20261026T000000Z")   # a newer audit
    repairstep.plan(conn, c, {"ledger": {}}, {}, slugs=["rp-a"])
    assert qdb.get(conn, first["id"])["state"] == "failed"
    second = [r for r in qdb.jobs(conn, "kind='repair'") if r["state"] == "queued"]
    assert len(second) == 1 and second[0]["id"] != first["id"]
    qdb.claim(conn, second[0]["id"], 60)                       # running now
    audit(trials[1], [dict(UNFAIR, test="security::t_three")], stamp="20261027T000000Z")
    rep, = repairstep.plan(conn, c, {"ledger": {}}, {}, slugs=["rp-a"])
    assert not rep["want"] and any("queued or running" in n for n in rep["notes"])


# ---------------------------------------------------------------- the job

FAKE_AGENT = r'''
import json, os, sys, shutil
from pathlib import Path
slug, inputs, mode = sys.argv[1], Path(sys.argv[2]), os.environ.get("FAKE_MODE", "ok")
t, b, date = Path("tasks") / slug, Path("build") / slug, os.environ["REPAIR_DATE"]
assert (inputs / "FINDING.md").is_file() and (inputs / "INPUTS.md").is_file() and (inputs / "runs").is_dir()
if mode == "no_repair":
    (inputs / "OUTCOME.json").write_text(json.dumps({"outcome": "no_repair_needed", "reason": "the audit is wrong"}))
    sys.exit(0)
rep = b / f"repaired-tests-{date}-repair"
(rep / "original").mkdir(parents=True)
shutil.copy2(t / "tests/security/a_test.rs", rep / "original" / "a_test.rs")
(rep / "README.md").write_text("why and what\n")
(t / "tests/security/a_test.rs").write_text("new")
(b / "history").mkdir(exist_ok=True)
(b / "history" / f"{date}-repair.md").write_text("record\n")
(b / "notes.md").write_text("the agent wrote here\n")
if mode == "instruction":
    (t / "instruction.md").write_text("Fix it, and here is the answer.\n")
if mode == "stopped":                       # cweq stop / a reaped lease while the agent works
    import signal, time
    os.kill(os.getppid(), signal.SIGTERM)
    time.sleep(30)
(inputs / "OUTCOME.json").write_text(json.dumps({"outcome": "repaired", "folder": rep.name}))
'''


def job_setup(tmp_path, root, cfg, mode="ok"):
    audited_task(root)
    b = root / "build" / "rp-a"
    (b / "notes.md").write_text("build facts\n")
    (b / ".sound").write_text("")
    agent = tmp_path / "fake_agent.py"
    agent.write_text(FAKE_AGENT)
    os.environ["FAKE_MODE"] = mode
    c = rcfg(cfg, agent_cmd=[sys.executable, str(agent), "{slug}", "{inputs}"], static_check=False, trial_summary=False,
             wait_sec=0)
    return b, c


def test_job_repairs_holds_and_queues_the_regate(tmp_path, conn, cfg, root):
    b, c = job_setup(tmp_path, root, cfg)
    key = repairstep.findings("rp-a", c)["key"]
    t0 = time.time()
    code = repairjob.Job("rp-a", c, job_id=11, conn=conn, proc_lister=lambda: [], out=lambda *_: None).run(key)
    assert code == repairjob.EXIT_REPAIRED
    assert (b / ".hold-repair").exists() and not (b / ".sound").exists()
    assert "waiting for the re-gate" in (b / ".hold-repair").read_text()
    assert (b / "notes.md").read_text() == "build facts\n"                     # notes edit reverted
    inp, = b.glob("repair-inputs-*")
    res = json.loads((inp / "JOB-RESULT.json").read_text())
    assert res["result"] == "repaired" and res["folder"].startswith("repaired-tests-")
    assert json.loads((inp / "FINDING.json").read_text())["key"] == key
    runs = sorted(p.name for p in (inp / "runs").iterdir())
    assert len(runs) == 2 and (inp / "runs" / runs[0] / "failures.md").is_file()
    regate, = qdb.jobs(conn, "kind='regate'")
    assert qdb.args_of(regate)["fp"] == reconcile.gate_digest("rp-a")[:16]     # the key rule R1 uses
    assert not (b / "gate_fingerprint.json").exists()                         # gated before fingerprints: still queued
    assert all(ok for _n, ok, _d, _p in kinds.get("repair").check("rp-a", {}, t0, c))
    # the finding is now covered by the new repair folder: nothing more to plan
    assert repairstep.findings("rp-a", c)["items"] == []


def test_job_restores_the_originals_when_the_agent_edits_the_instruction(tmp_path, conn, cfg, root):
    b, c = job_setup(tmp_path, root, cfg, mode="instruction")
    before = (root / "tasks" / "rp-a" / "tests" / "security" / "a_test.rs").read_text()
    code = repairjob.Job("rp-a", c, job_id=12, conn=conn, proc_lister=lambda: [], out=lambda *_: None).run(
        repairstep.findings("rp-a", c)["key"])
    assert code == repairjob.EXIT_FAILED
    assert (root / "tasks" / "rp-a" / "instruction.md").read_text() == "Fix it.\n"
    assert (root / "tasks" / "rp-a" / "tests" / "security" / "a_test.rs").read_text() == before
    assert (b / ".hold-repair").read_text().startswith("repair failed")
    assert not list(b.glob("repaired-tests-*"))                               # moved into the inputs folder
    inp, = b.glob("repair-inputs-*")
    assert list((inp / "failed").iterdir()) and json.loads((inp / "JOB-RESULT.json").read_text())["restored"]
    assert not qdb.jobs(conn, "kind='regate'")
    # a failed repair keeps the hold (never lifted by R6) and T1 does not plan the same finding again
    assert not repairstep.findings("rp-a", c)["plan"]


def test_job_stopped_mid_edit_restores_the_task(tmp_path, conn, cfg, root):
    b, c = job_setup(tmp_path, root, cfg, mode="stopped")
    before = (root / "tasks" / "rp-a" / "tests" / "security" / "a_test.rs").read_text()
    code = repairjob.Job("rp-a", c, job_id=15, conn=conn, proc_lister=lambda: [], out=lambda *_: None).run(
        repairstep.findings("rp-a", c)["key"])
    assert code == repairjob.EXIT_FAILED
    assert (root / "tasks" / "rp-a" / "tests" / "security" / "a_test.rs").read_text() == before
    assert "stopped (SIGTERM)" in (b / ".hold-repair").read_text() and not list(b.glob("repaired-tests-*"))


def test_job_no_repair_and_nothing_to_do_and_wait(tmp_path, conn, cfg, root):
    b, c = job_setup(tmp_path, root, cfg, mode="no_repair")
    job = repairjob.Job("rp-a", c, job_id=13, conn=conn, proc_lister=lambda: [], out=lambda *_: None)
    assert job.run("f-0000000000000000") == repairjob.EXIT_NOTHING and (b / ".sound").exists()
    assert job.run(repairstep.findings("rp-a", c)["key"]) == repairjob.EXIT_NO_REPAIR
    assert (b / ".hold-repair").read_text().startswith("repair failed")
    (b / ".hold-repair").rename(b / ".sound")
    busy = [(4242, ["python3", "common/trial/trial.py", "rp-a", "--models", "mimo"], "/", {})]
    job = repairjob.Job("rp-a", c, job_id=14, conn=conn, proc_lister=lambda: busy, out=lambda *_: None)
    assert job.run({"why": "the owner's own finding"}) == repairjob.EXIT_WAIT       # a manual finding, task busy
    assert (b / ".sound").exists() and not (b / ".hold-repair").exists()            # hold put back as it was


# ---------------------------------------------------------------- R2 by test content, R6 hold lift

def repaired_and_regated(root, slug="rp-r", copy_p=False):
    t0 = time.time() - 2 * DAY
    tdir = make_task(root, slug, {"security/a_test.py": "old"})
    old_hash = repairstep.tests_hash(slug)
    trials = [make_trial(root, slug, n, t0 + n * 60) for n in (1, 2)]
    for t in trials:
        (t / "trial.log").write_text(f"pull cwe-reuse/{slug}:verifier-{old_hash} ok\n")
    rep = root / "build" / slug / "repaired-tests-20261028-repair"
    rep.mkdir()
    (rep / "README.md").write_text("r\n")
    f = tdir / "tests" / "security" / "a_test.py"
    f.write_text("new")
    if copy_p:                                         # copied with cp -p: the file keeps an old time
        set_mtime(f, t0 - DAY)
        set_mtime(f.parent, t0 - DAY)
        set_mtime(tdir / "tests", t0 - DAY)
    write_fingerprint(root, slug)
    gate_log(root, slug, RESULT_AT, "SOUND, ready for trials (regate)")
    return trials


RESULT_AT = int(time.time()) - 600


def test_regrade_follows_test_content_not_file_times(conn, cfg, root):
    repaired_and_regated(root, copy_p=True)
    a = reconcile.analyse("rp-r", cfg)
    assert sorted(w["args"]["trial"] for w in a["want"] if w["kind"] == "regrade") == \
        ["rp-r-m-r1/rp-r__T1", "rp-r-m-r2/rp-r__T2"]
    c = dict(cfg, reconcile={**cfg["reconcile"], "unknown_tests_version": "mtime"})
    assert len(reconcile.analyse("rp-r", c)["want"]) == 2      # the trial.log tag is a known version: not by time


def test_grading_without_a_recorded_version(conn, cfg, root):
    trials = repaired_and_regated(root, copy_p=True)
    for t in trials:
        (t / "trial.log").write_text("no image tag here\n")      # a run from before image reuse
    assert len(reconcile.analyse("rp-r", cfg)["want"]) == 2                    # "regrade": regraded once
    c = dict(cfg, reconcile={**cfg["reconcile"], "unknown_tests_version": "mtime"})
    assert reconcile.analyse("rp-r", c)["want"] == []          # the old rule misses the cp -p repair
    c = dict(cfg, reconcile={**cfg["reconcile"], "unknown_tests_version": "repair_folder"})
    assert len(reconcile.analyse("rp-r", c)["want"]) == 2      # graded before the repair folder: regraded


def test_current_grading_needs_no_regrade_and_a_failed_regrade_does_not_count(conn, cfg, root):
    trials = repaired_and_regated(root)
    cur = repairstep.tests_hash("rp-r")
    (trials[0] / "trial.log").write_text(f"cwe-reuse/rp-r:verifier-{cur}\n")     # graded on the current tests
    rg = trials[1] / "regrade-20991231T000000Z"
    (rg / "verifier").mkdir(parents=True)
    (rg / "REGRADE.json").write_text(json.dumps({"reward": None, "tests_hash": cur}))   # did not score
    a = reconcile.analyse("rp-r", cfg)
    assert [w["args"]["trial"] for w in a["want"]] == ["rp-r-m-r2/rp-r__T2"]
    (rg / "REGRADE.json").write_text(json.dumps({"reward": 0.5, "tests_hash": cur}))
    (rg / "verifier" / "reward.json").write_text(json.dumps({"reward": 0.5}))
    assert reconcile.analyse("rp-r", cfg)["want"] == []


def test_hold_is_lifted_once_the_regate_is_sound_and_every_run_is_regraded(conn, cfg, root):
    trials = repaired_and_regated(root)
    b = root / "build" / "rp-r"
    (b / ".hold-repair").write_text("repair job #5 done: waiting\n")
    set_mtime(b / ".hold-repair", RESULT_AT)                    # re-applied by the held re-gate (keeps .sound's time)
    rep, = reconcile.reconcile(conn, cfg, slugs=["rp-r"], proc_list=[])
    assert not rep.get("lift") and (b / ".hold-repair").exists()        # regrades still owed
    cur = repairstep.tests_hash("rp-r")
    for t in trials:
        (t / "trial.log").write_text(f"cwe-reuse/rp-r:verifier-{cur}\n")
    for r in qdb.jobs(conn, "kind='regrade'"):
        qdb.set_state(conn, r["id"], "done", "x")
    rep, = reconcile.reconcile(conn, cfg, slugs=["rp-r"], proc_list=[], dry_run=True)
    assert rep["lift"] and any("would lift" in n for n in rep["notes"]) and (b / ".hold-repair").exists()
    rep, = reconcile.reconcile(conn, cfg, slugs=["rp-r"], proc_list=[])
    assert (b / ".sound").exists() and not (b / ".hold-repair").exists()
    assert "hold lifted by the queue" in next(b.glob("repair-*.log")).read_text()


def test_hold_kept_when_newer_than_the_regate_failed_or_a_regrade_failed(conn, cfg, root):
    trials = repaired_and_regated(root)
    cur = repairstep.tests_hash("rp-r")
    for t in trials:
        (t / "trial.log").write_text(f"cwe-reuse/rp-r:verifier-{cur}\n")
    b = root / "build" / "rp-r"
    (b / ".hold-repair").write_text("repair job #9 2026-10-28: held for a test-only repair\n")   # newer than RESULT
    rep, = reconcile.reconcile(conn, cfg, slugs=["rp-r"], proc_list=[])
    assert (b / ".hold-repair").exists() and any("set after the last SOUND" in n for n in rep["notes"])
    (b / ".hold-repair").write_text("repair failed (job #9): x\n")
    set_mtime(b / ".hold-repair", RESULT_AT)
    reconcile.reconcile(conn, cfg, slugs=["rp-r"], proc_list=[])
    assert (b / ".hold-repair").exists()
    (b / ".hold-repair").write_text("held\n")
    set_mtime(b / ".hold-repair", RESULT_AT)
    jid, _ = qdb.enqueue(conn, "regrade", "rp-r", {"trial": "x", "fp": reconcile.gate_digest("rp-r")[:16]})
    qdb.set_state(conn, jid, "failed", "post-condition failed: regrade.scored")
    rep, = reconcile.reconcile(conn, cfg, slugs=["rp-r"], proc_list=[])
    assert (b / ".hold-repair").exists() and any("a person looks" in n for n in rep["notes"])


def test_regrade_check_wants_the_current_tests(conn, cfg, root):
    trials = repaired_and_regated(root)
    t0 = time.time() - 5
    rg = trials[0] / f"regrade-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    (rg / "verifier").mkdir(parents=True)
    (rg / "verifier" / "reward.json").write_text(json.dumps({"reward": 1.0}))
    (rg / "REGRADE.json").write_text(json.dumps({"reward": 1.0, "tests_hash": "0" * 20}))
    res = {n: ok for n, ok, _d, _p in checks.c_regrade("rp-r", {"trial": "rp-r-m-r1/rp-r__T1"}, t0, cfg)}
    assert res["regrade.tests_current"] is False
    (rg / "REGRADE.json").write_text(json.dumps({"reward": 1.0, "tests_hash": repairstep.tests_hash("rp-r")}))
    res = {n: ok for n, ok, _d, _p in checks.c_regrade("rp-r", {"trial": "rp-r-m-r1/rp-r__T1"}, t0, cfg)}
    assert res["regrade.tests_current"] is True


# ---------------------------------------------------------------- F1: a fresh fairness review after a repair

def fairness_ctx(root, slug):
    return {"batches": {slug: "b1"}, "batch_meta": {}, "ledger": {slug: {"verdict": "BREAKER candidate"}},
            "running": {}, "delivered": {}}


def test_repair_after_the_review_gives_a_fresh_review(conn, cfg, root):
    slug = "rp-h"
    make_task(root, slug, {"security/a.py": "x"})
    t0 = time.time() - 3 * DAY
    job = root / "jobs" / f"{slug}-mimo-r3-x"
    job.mkdir(parents=True)
    set_mtime(job, t0)
    b = root / "build" / slug
    (b / "FAIRNESS.md").write_text("GATE_A: READY\n")
    set_mtime(b / "FAIRNESS.md", t0 + 3600)
    old, _ = qdb.enqueue(conn, "fairness", slug, {"after": job.name}, origin="reconciler")   # a review keyed before
    qdb.set_state(conn, old, "done", "ok")
    jobs, _n = phase4.fairness_plan(cfg, fairness_ctx(root, slug), [], conn)
    assert jobs == []                                          # current review, the older key still stands
    rep = b / "repaired-tests-20991231-owner"                  # repaired after the review
    rep.mkdir()
    set_mtime(rep, t0 + 7200)
    jobs, notes = phase4.fairness_plan(cfg, fairness_ctx(root, slug), [], conn)
    assert len(jobs) == 1 and jobs[0]["args"] == {"after": job.name, "tests": repairstep.tests_hash(slug)}
    assert jobs[0]["stale"] and any("stale" in n for n in notes)
    c = dict(cfg, phase4={"enabled": True, "audits": False, "fairness": True, "cleanup": False, "step3": False})
    phase4.reconcile(conn, c, fairness_ctx(root, slug), [], now=time.time())
    assert not (b / "FAIRNESS.md").exists() and list(b.glob("FAIRNESS.md.prev-*"))
    assert len([r for r in qdb.jobs(conn, "kind='fairness'") if r["state"] == "queued"]) == 1


def test_review_moved_away_by_hand_is_replanned(conn, cfg, root):
    slug = "rp-l"                                               # langflow-s3: FAIRNESS.md moved into the repair folder
    make_task(root, slug, {"security/a.py": "x"})
    t0 = time.time() - 3 * DAY
    job = root / "jobs" / f"{slug}-mimo-r3-x"
    job.mkdir(parents=True)
    set_mtime(job, t0)
    b = root / "build" / slug
    (b / "fairness_start.txt").write_text("x\n")
    set_mtime(b / "fairness_start.txt", t0 + 3600)
    old, _ = qdb.enqueue(conn, "fairness", slug, {"after": job.name}, origin="reconciler")
    qdb.set_state(conn, old, "done", "ok")
    rep = b / "repaired-tests-20991231-owner"
    rep.mkdir()
    set_mtime(rep, t0 + 7200)
    jobs, _n = phase4.fairness_plan(cfg, fairness_ctx(root, slug), [], conn)
    assert len(jobs) == 1 and "tests" in jobs[0]["args"]


def test_recorded_test_version_decides_staleness(conn, cfg, root):
    slug = "rp-t"
    make_task(root, slug, {"security/a.py": "x"})
    b = root / "build" / slug
    (b / "FAIRNESS.md").write_text("GATE_A: READY\n")
    repairstep.record_tests(slug, phase4.FAIRNESS_TESTS)
    assert phase4.review_stale(slug, repairstep.tests_hash(slug)) is None
    (root / "tasks" / slug / "tests" / "security" / "a.py").write_text("y")
    assert "review saw tests" in phase4.review_stale(slug, repairstep.tests_hash(slug))


# ---------------------------------------------------------------- the dispatcher waits; lost repairs

OPEN = {"free_disk_gb": 999, "load": 1, "mem_available_gb": 999, "tmp_inode_pct": 1}


def test_repair_waits_for_the_tasks_other_work(conn, cfg, root):
    make_task(root, "rp-d", {"security/a.py": "x"})
    rid, _ = qdb.enqueue(conn, "repair", "rp-d", {"finding": "f-1"}, priority=32)
    tid, _ = qdb.enqueue(conn, "trial_run", "rp-d", {"model": "mimo", "first_run": 2, "max_runs": 1, "v": "x"})
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: dict(OPEN), proc_list=[])
    _starts, waits = d.plan()
    why = {r["id"]: w for r, w in waits}
    assert "repair waits for the task's other work: trial_run" in (why.get(rid) or "")
    (root / "build" / "rp-d" / ".hold-repair").write_text("x")   # a held trial cannot start: the repair goes first
    starts, _w = d.plan()
    assert rid in [r["id"] for r, _ in starts]


def test_lost_repairs_report(conn, cfg, root):
    audited_task(root, slug="rp-lost")
    audited_task(root, slug="rp-done")
    rep = root / "build" / "rp-done" / "testfix-20261026"
    rep.mkdir()
    set_mtime(rep, epoch("20261026T100000Z"))
    rows = repairstep.lost(cfg)
    assert [r["task"] for r in rows] == ["rp-lost"] and rows[0]["since"] == "2026-10-25"
    items = repairstep.inbox_items(conn, cfg)
    lost_line, = [i for i in items if "lost repairs" in i["summary"]]
    assert lost_line["task"] == "1 task(s)" and "rp-lost since 2026-10-25" in lost_line["detail"]
