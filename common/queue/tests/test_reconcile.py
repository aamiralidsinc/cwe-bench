"""The reconciler on a fake build/ + tasks/ + jobs/ tree: the phase-1 rules, rebuilding a deleted queue.db without
duplicates or redone work, and skipping tasks an old script is busy with."""
import json
import os
import time

import qdb
import reconcile
from conftest import gate_log, make_task, make_trial, set_mtime, write_fingerprint

DAY = 86400


def kinds(conn, task=None):
    rows = qdb.jobs(conn, "task=?", (task,)) if task else qdb.jobs(conn)
    return sorted((r["kind"], r["task"], r["state"]) for r in rows)


def repaired_task(root, slug="stk-a", t0=None):
    """A task whose test file was repaired after two runs were graded; the gate fingerprint is from before."""
    t0 = t0 or time.time() - 2 * DAY
    tdir = make_task(root, slug, {"security/a_test.py": "old", "functional/f_test.py": "f"})
    write_fingerprint(root, slug)                        # gate of the old files
    gate_log(root, slug, t0, "SOUND, ready for trials")
    make_trial(root, slug, 1, t0 + 3600)
    make_trial(root, slug, 2, t0 + 7200)
    rep = root / "build" / slug / "repaired-tests-20261026"
    rep.mkdir()
    (rep / "README.md").write_text("repair\n")
    (rep / "a_test.py.orig").write_text("old")
    (tdir / "tests" / "security" / "a_test.py").write_text("new")   # the repair: now, after both runs
    return tdir


def test_repair_pending_regate_queues_regate_and_dependent_regrades(conn, cfg, root):
    repaired_task(root)
    rep, = reconcile.reconcile(conn, cfg, proc_list=[])
    assert rep["fp"] == "stale"
    rows = qdb.jobs(conn)
    gate = [r for r in rows if r["kind"] == "regate"]
    assert len(gate) == 1 and qdb.args_of(gate[0])["listing"] is True       # stk- -> --listing
    regrades = [r for r in rows if r["kind"] == "regrade"]
    assert len(regrades) == 2 and all(qdb.deps_of(r) == [gate[0]["id"]] for r in regrades)
    # a second pass adds nothing
    reconcile.reconcile(conn, cfg, proc_list=[])
    assert len(qdb.jobs(conn)) == 3


def test_deleted_db_is_rebuilt_with_the_same_jobs(conn, cfg, root, tmp_path):
    repaired_task(root)
    reconcile.reconcile(conn, cfg, proc_list=[])
    before = sorted((r["kind"], r["task"], r["args"]) for r in qdb.jobs(conn))
    conn.close()
    for f in tmp_path.glob("queue.db*"):
        f.unlink()
    conn2 = qdb.connect(cfg["db"])
    reconcile.reconcile(conn2, cfg, proc_list=[])
    assert sorted((r["kind"], r["task"], r["args"]) for r in qdb.jobs(conn2)) == before


def test_after_regate_only_runs_without_a_current_regrade(conn, cfg, root, tmp_path):
    repaired_task(root)
    reconcile.reconcile(conn, cfg, proc_list=[])
    # The re-gate happened (here: by an old script): fingerprint current, RESULT SOUND, run 1 already regraded.
    write_fingerprint(root, "stk-a")
    gate_log(root, "stk-a", time.time() + 1, "SOUND, ready for trials (regate)")
    t1 = root / "jobs" / "stk-a-m-r1" / "stk-a__T1"
    rg = t1 / f"regrade-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(time.time() + 5))}"
    (rg / "verifier").mkdir(parents=True)
    (rg / "REGRADE.json").write_text(json.dumps({"reward": 1.0}))
    rep, = reconcile.reconcile(conn, cfg, proc_list=[])
    assert rep["fp"] == "current" and [w["kind"] for w in rep["want"]] == ["regrade"]
    st = {(r["kind"], qdb.args_of(r).get("trial", "")): r["state"] for r in qdb.jobs(conn)}
    assert st[("regate", "")] == "done"                  # done on disk by someone else
    assert st[("regrade", "stk-a-m-r1/stk-a__T1")] == "done"
    assert st[("regrade", "stk-a-m-r2/stk-a__T2")] == "queued"
    # A fresh database after the regate holds only the one regrade still owed, with no dependency.
    conn.close()
    for f in tmp_path.glob("queue.db*"):
        f.unlink()
    conn2 = qdb.connect(cfg["db"])
    reconcile.reconcile(conn2, cfg, proc_list=[])
    rows = qdb.jobs(conn2)
    assert [(r["kind"], qdb.args_of(r)["trial"], qdb.deps_of(r)) for r in rows] == \
        [("regrade", "stk-a-m-r2/stk-a__T2", [])]


def test_removed_test_file_gives_rescore_jobs(conn, cfg, root):
    t0 = time.time() - 2 * DAY
    slug = "fastify-x2"
    tdir = make_task(root, slug, {"security/keep.test.js": "k", "security/Dup_case.test.js": "d"})
    write_fingerprint(root, slug)
    gate_log(root, slug, t0, "SOUND, ready for trials")
    res = {"security": {"test::[security/Dup_case] refuses": "fail", "test::[security/keep] ok": "pass"},
           "functional": {"f": "pass"}}
    make_trial(root, slug, 1, t0 + 60, res)
    done = make_trial(root, slug, 2, t0 + 120, res)
    rem = root / "build" / slug / "removed-tests-20261026"
    rem.mkdir()
    os.replace(tdir / "tests" / "security" / "Dup_case.test.js", rem / "Dup_case.test.js")
    (rem / "README.md").write_text("removed\n")
    # run 2 was already rescored (before the re-gate, as the orchestrator's rule 5.4 does)
    rg = done / "regrade-20261026T144741Z"
    rg.mkdir()
    (rg / "REGRADE.json").write_text(json.dumps({"dropped": ["security:test::[security/Dup_case] refuses=fail"]}))
    set_mtime(rg / "REGRADE.json", t0 + 200)
    reconcile.reconcile(conn, cfg, proc_list=[])
    got = sorted((r["kind"], qdb.args_of(r).get("trial"), tuple(qdb.args_of(r).get("drop", ()))) for r in qdb.jobs(conn))
    assert got == [("regate", None, ()), ("rescore", f"{slug}-m-r1/{slug}__T1", ("Dup_case",))]
    assert qdb.args_of(qdb.jobs(conn, "kind='regate'")[0])["listing"] is False


def test_removed_function_from_a_file_that_stays_gives_regrade(conn, cfg, root):
    t0 = time.time() - 2 * DAY
    slug = "stk-b"
    make_task(root, slug, {"security/test_own.py": "def test_a(): pass\n"})
    write_fingerprint(root, slug)
    gate_log(root, slug, t0, "SOUND, ready for trials")
    make_trial(root, slug, 1, t0 + 60)
    rem = root / "build" / slug / "removed-tests-20261026"
    rem.mkdir()
    (rem / "test_own.py.before").write_text("def test_a(): pass\ndef test_b(): pass\n")
    (root / "tasks" / slug / "tests" / "security" / "test_own.py").write_text("def test_a(): pass\n#\n")
    reconcile.reconcile(conn, cfg, proc_list=[])
    assert kinds(conn) == [("regate", slug, "queued"), ("regrade", slug, "queued")]


def test_gate_failed_on_current_files_needs_a_person(conn, cfg, root):
    repaired_task(root)
    gate_log(root, "stk-a", time.time() + 1, "not sound (regate gate exit 1)")
    rep, = reconcile.reconcile(conn, cfg, proc_list=[])
    assert not qdb.jobs(conn) and "needs a person" in rep["notes"][0]


def test_stopped_regate_is_requeued(conn, cfg, root):
    repaired_task(root)
    write_fingerprint(root, "stk-a")                     # gate stage passed and wrote the fingerprint ...
    (root / "build" / "stk-a" / ".gate_passed").touch()  # ... but the re-gate died before its RESULT
    reconcile.reconcile(conn, cfg, proc_list=[])
    assert ("regate", "stk-a", "queued") in kinds(conn)


def test_no_fingerprint_no_job(conn, cfg, root):
    repaired_task(root)
    (root / "build" / "stk-a" / "gate_fingerprint.json").unlink()
    rep, = reconcile.reconcile(conn, cfg, proc_list=[])
    assert not qdb.jobs(conn) and "no gate fingerprint" in rep["notes"][0]


def test_busy_task_gets_no_jobs(conn, cfg, root, tmp_path):
    repaired_task(root)
    repaired_task(root, "stk-c")
    script = tmp_path / "repair-rescore.sh"             # a one-off script that names the slug only inside
    script.write_text("S=stk-c\nbash common/gate/regate.sh $S\n")
    procs = [(5, ["bash", str(script)], None, {})]
    reconcile.reconcile(conn, cfg, proc_list=[(4, ["bash", "common/gate/regate.sh", "stk-a", "--listing"], None, {})]
                        + procs)
    assert not qdb.jobs(conn)


def test_newer_test_version_supersedes_queued_jobs(conn, cfg, root):
    tdir = repaired_task(root)
    reconcile.reconcile(conn, cfg, proc_list=[])
    (tdir / "tests" / "security" / "a_test.py").write_text("newer still")
    reconcile.reconcile(conn, cfg, proc_list=[])
    old = [r for r in qdb.jobs(conn) if r["state"] == "failed"]
    new = [r for r in qdb.jobs(conn) if r["state"] == "queued"]
    assert len(old) == 3 and all(r["result"].startswith("superseded") for r in old) and len(new) == 3


def test_hold_is_reported(conn, cfg, root):
    repaired_task(root)
    (root / "build" / "stk-a" / ".hold-repair").touch()
    rep, = reconcile.reconcile(conn, cfg, proc_list=[])
    assert rep["held"] and any("held" in n for n in rep["notes"])
    assert ("regate", "stk-a", "queued") in kinds(conn)  # a hold stops trials, not the re-gate


def test_dry_run_writes_nothing(conn, cfg, root):
    repaired_task(root)
    rep, = reconcile.reconcile(conn, cfg, proc_list=[], dry_run=True)
    assert len(rep["want"]) == 3 and not qdb.jobs(conn)


def test_r4_removed_tests_cannot_change_a_both_solved_verdict(root, conn, cfg):
    """Removing tests from a task both models solved: no regate, regrade or rescore.
    A task with one failing model is still re-gated and rescored."""
    import phase3
    import taskstate
    from test_adopt import batch, ledger
    for slug in ("solved-s2", "split-s2"):
        make_task(root, slug, {"security/a.test.js": "a", "security/gone.test.js": "g"})
        write_fingerprint(root, slug)
        gate_log(root, slug, time.time() - 3600, "SOUND (gate)")
        (root / "build" / slug / ".sound").write_text("")
        make_trial(root, slug, 1, time.time() - 3000, results={"security": {"gone.test.js > x": "failed"},
                                                              "functional": {}})
        rem = root / "build" / slug / "removed-tests-20261027"
        rem.mkdir()
        (rem / "gone.test.js").write_text("g")
        (root / "tasks" / slug / "tests" / "security" / "gone.test.js").unlink()
    batch(root, "scale-b9", ["solved-s2", "split-s2"])
    ledger(root, [("solved-s2", "SOLVED 1/1", "SOLVED 2/2", "rejected (both solved)"),
                  ("split-s2", "SOLVED 1/1", "**failed 0/3** [0.5]", "rejected (DeepSeek solved)")])
    rep = {a["task"]: a for a in reconcile.reconcile(conn, cfg, slugs=["solved-s2", "split-s2"], proc_list=[])}
    assert rep["solved-s2"]["want"] == [] and reconcile.BOTH_SOLVED_NOTE in rep["solved-s2"]["notes"]
    assert [w["kind"] for w in rep["split-s2"]["want"]] == ["regate", "rescore"]
    p3 = {t["task"]: t for t in phase3.reconcile(conn, cfg, taskstate.context([]))}
    assert reconcile.BOTH_SOLVED_NOTE in p3["solved-s2"]["notes"] and not qdb.jobs(conn, "task='solved-s2'")


def test_r4_covers_a_single_removed_test_function(root, conn, cfg):
    """One test function removed from a file that stays (removed-tests-*/<file>.before).
    A repaired-tests-* folder (changed assertions) is not covered: a re-run could change the verdict."""
    from test_adopt import ledger
    for slug in ("fn-s2", "edited-s2"):
        make_task(root, slug, {"security/t.py": "def test_a(): pass\n"})
        write_fingerprint(root, slug, sha="0" * 64)
        (root / "build" / slug / ".sound").write_text("")
    (root / "build" / "fn-s2" / "removed-tests-20261026").mkdir()
    (root / "build" / "fn-s2" / "removed-tests-20261026" / "t.py.before").write_text("old")
    (root / "build" / "edited-s2" / "repaired-tests-20261027").mkdir()
    (root / "build" / "edited-s2" / "repaired-tests-20261027" / "t.py.orig").write_text("old")
    ledger(root, [("fn-s2", "SOLVED 1/3", "SOLVED 1/3", "rejected (both solved)"),
                  ("edited-s2", "SOLVED 1/3", "SOLVED 1/3", "rejected (both solved)")])
    rep = {a["task"]: a for a in reconcile.reconcile(conn, cfg, slugs=["fn-s2", "edited-s2"], proc_list=[])}
    assert rep["fn-s2"]["want"] == [] and reconcile.BOTH_SOLVED_NOTE in rep["fn-s2"]["notes"]
    assert [w["kind"] for w in rep["edited-s2"]["want"]] == ["regate"]


def test_imported_run_without_workspace_has_no_code(root, cfg):
    """A run imported from elsewhere keeps only artifacts/manifest.json: nothing to regrade."""
    import time
    import reconcile
    t = make_trial(root, "imp-s2", 1, time.time(), code=False)
    (t / "artifacts").mkdir()
    (t / "artifacts" / "manifest.json").write_text("{}")
    runs = reconcile.graded_runs("imp-s2", cfg["jobs_dir"])
    assert runs and runs[0]["has_code"] is False
    (t / "artifacts" / "workspace").mkdir()
    assert reconcile.graded_runs("imp-s2", cfg["jobs_dir"])[0]["has_code"] is True
