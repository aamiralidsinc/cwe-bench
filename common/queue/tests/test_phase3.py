"""Phase 3: builds, trials and stale gates of batch tasks (phase3.py), and the dispatcher's admission for them during
the drain of the old schedulers (old-script work counts against every cap)."""
import json

import dispatch
import phase3
import qdb
import reconcile
import taskstate
import worker
from conftest import write_fingerprint
from test_adopt import batch, built, ledger, proc

OPEN = {"free_disk_gb": 999, "load": 1, "mem_available_gb": 999, "tmp_inode_pct": 1}


def p3(conn, cfg, procs=()):
    return {t["task"]: t for t in phase3.reconcile(conn, cfg, taskstate.context(list(procs)))}


def jobs_of(conn, task, kind=None):
    rows = qdb.jobs(conn, "task=?" + (" AND kind=?" if kind else ""), (task, kind) if kind else (task,))
    return [(r["kind"], qdb.args_of(r)) for r in rows]


def prompt(root, slug, in_batch=True):
    """A task waiting for its build: BUILD-PROMPT.md in place and (by default) listed in batch scale-b8."""
    if in_batch:
        f = root / "pipelines" / "router" / "out" / "batches" / "scale-b8.txt"
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "a") as fh:
            fh.write(slug + "\n")
    (root / "build" / slug).mkdir(parents=True, exist_ok=True)
    (root / "build" / slug / "BUILD-PROMPT.md").write_text("build me\n")


def disp(conn, cfg, procs=(), **kw):
    return dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: dict(OPEN), proc_list=list(procs),
                               spawn=lambda i: 1, **kw)


# ---------- rules

def test_build_rule_once_per_task(root, conn, cfg):
    batch(root, "scale-b9", ["new-s2", "noprompt-s2", "half-s2"])
    prompt(root, "new-s2")
    prompt(root, "half-s2")
    (root / "build" / "half-s2" / "start_utc.txt").write_text("2026-10-27T01:00:00Z\n")   # interrupted build
    rep = p3(conn, cfg)
    assert jobs_of(conn, "new-s2") == [("build", {})] and jobs_of(conn, "half-s2") == [("build", {})]
    assert jobs_of(conn, "noprompt-s2") == [] and "no BUILD-PROMPT.md: not built" in rep["noprompt-s2"]["notes"]
    p3(conn, cfg)                                          # idempotent
    assert len(qdb.jobs(conn, "kind='build'")) == 2
    jid = qdb.jobs(conn, "task='new-s2'")[0]["id"]
    qdb.set_state(conn, jid, "failed", "builder declined")
    p3(conn, cfg)                                          # a failed build is final: no second build job
    assert len(qdb.jobs(conn, "task='new-s2'")) == 1


def test_running_or_unlisted_tasks_get_nothing(root, conn, cfg):
    batch(root, "scale-b9", ["run-s2"])
    prompt(root, "run-s2")
    p3(conn, cfg, [proc(5, "bash pipelines/sibling/6-build/run_pipeline.sh deepseek run-s2")])
    assert jobs_of(conn, "run-s2") == []                   # an old scheduler's build is running: nothing
    prompt(root, "loose-s2", in_batch=False)
    p3(conn, cfg)
    assert jobs_of(conn, "loose-s2") == []


def test_trial_rule_plans_runs_like_the_scheduler(root, conn, cfg):
    cfg["phase3"]["mimo_after_deepseek"] = False           # flag off: both models side by side, as before 2026-10-29
    batch(root, "scale-b9", ["fresh-s2", "onefail-s2"])
    built(root, "fresh-s2")
    built(root, "onefail-s2", runs={"deepseek": [0.5], "mimo": [1.0]})
    p3(conn, cfg)
    v = taskstate.gate_sha16("fresh-s2")
    assert sorted(jobs_of(conn, "fresh-s2"), key=lambda j: j[1]["model"]) == [
        ("trial_run", {"model": "deepseek", "first_run": 1, "max_runs": 3, "group": 0, "version": v}),
        ("trial_run", {"model": "mimo", "first_run": 1, "max_runs": 3, "group": 0, "version": v})]
    # deepseek failed once: its two remaining runs start together; mimo solved: nothing.
    assert sorted((a["first_run"], a["max_runs"]) for _k, a in jobs_of(conn, "onefail-s2")) == [(2, 1), (3, 1)]
    assert {a["model"] for _k, a in jobs_of(conn, "onefail-s2")} == {"deepseek"}


def test_trial_rule_respects_ledger_holds_and_launch_limit(root, conn, cfg):
    cfg["phase3"]["mimo_after_deepseek"] = False           # flag off: mimo planned whatever DeepSeek's state
    batch(root, "scale-b9", ["led-s2", "held-s2", "tired-s2"])
    built(root, "led-s2", runs={"deepseek": [0.5]})
    ledger(root, [("led-s2", "**failed 0/3** [0.5]", "", "open")])     # older version's runs gave deepseek a verdict
    built(root, "held-s2")
    (root / "build" / "held-s2" / "hold_mimo").write_text("")
    built(root, "tired-s2", runs={"mimo": [1.0]})
    v = taskstate.gate_sha16("tired-s2")
    for g in range(3):                                     # three launches ended without a deepseek verdict
        jid, _ = qdb.enqueue(conn, "trial_run", "tired-s2", {"model": "deepseek", "first_run": g + 1, "max_runs": 3,
                                                            "group": g, "version": v})
        qdb.set_state(conn, jid, "done", "ended")
    rep = p3(conn, cfg)
    assert {a["model"] for _k, a in jobs_of(conn, "led-s2")} == {"mimo"}
    assert {a["model"] for _k, a in jobs_of(conn, "held-s2")} == {"deepseek"}
    assert "mimo held (hold_mimo)" in rep["held-s2"]["notes"]
    assert len(jobs_of(conn, "tired-s2")) == 3 and any("a person looks" in n for n in rep["tired-s2"]["notes"])


def mimo_jobs(conn, task):
    return [a for _k, a in jobs_of(conn, task) if a["model"] == "mimo"]


def test_mimo_waits_until_deepseek_has_three_graded_fails(root, conn, cfg):
    assert cfg["phase3"]["mimo_after_deepseek"] is True     # the default
    batch(root, "scale-b9", ["ds0-s2", "ds1-s2", "ds2-s2", "ds3-s2"])
    built(root, "ds0-s2")
    built(root, "ds1-s2", runs={"deepseek": [0.5]})
    built(root, "ds2-s2", runs={"deepseek": [0.5, 0.2], "mimo": [None]})
    built(root, "ds3-s2", runs={"deepseek": [0.5, 0.2, 0.0]})
    rep = p3(conn, cfg)
    for slug, n in (("ds0-s2", 0), ("ds1-s2", 1), ("ds2-s2", 2)):
        assert mimo_jobs(conn, slug) == [], slug
        assert f"mimo waits: DeepSeek has {n}/3 graded fails (mimo_after_deepseek)" in rep[slug]["notes"]
    assert {a["model"] for _k, a in jobs_of(conn, "ds0-s2")} == {"deepseek"}   # DeepSeek is still planned
    v = taskstate.gate_sha16("ds3-s2")
    assert mimo_jobs(conn, "ds3-s2") == [{"model": "mimo", "first_run": 1, "max_runs": 3, "group": 0, "version": v}]
    assert not any("mimo waits" in n for n in (rep.get("ds3-s2") or {}).get("notes", []))
    # the third DeepSeek fail lands: mimo is planned on the next pass
    (root / "build" / "ds2-s2" / "runs_deepseek.log").write_text("".join(f"run {i} reward=0.5\n" for i in range(3)))
    p3(conn, cfg)
    assert [a["model"] for a in mimo_jobs(conn, "ds2-s2")] == ["mimo"]


def test_deepseek_solved_means_no_mimo(root, conn, cfg):
    batch(root, "scale-b9", ["dss-s2", "dsl-s2"])
    built(root, "dss-s2", runs={"deepseek": [0.5, 1.0]})
    built(root, "dsl-s2", runs={"deepseek": [0.5, 0.5, 0.5]})
    ledger(root, [("dsl-s2", "**solved 1/3** [0.5, 1.0, 0.5]", "", "rejected")])   # a regrade solved it
    rep = p3(conn, cfg)
    for slug in ("dss-s2", "dsl-s2"):
        assert jobs_of(conn, slug) == [], slug
        assert any(n.startswith("mimo not planned: DeepSeek solved") for n in rep[slug]["notes"]), slug


def test_mimo_gate_leaves_queued_mimo_jobs_alone(root, conn, cfg):
    batch(root, "scale-b9", ["old-s2"])
    built(root, "old-s2", runs={"deepseek": [0.5]})
    v = taskstate.gate_sha16("old-s2")
    jid, _ = qdb.enqueue(conn, "trial_run", "old-s2", {"model": "mimo", "first_run": 1, "max_runs": 3, "group": 0,
                                                       "version": v}, origin="reconciler")
    p3(conn, cfg)
    assert qdb.get(conn, jid)["state"] == "queued" and len(mimo_jobs(conn, "old-s2")) == 1
    starts, _waits = disp(conn, cfg).plan()                 # and the dispatcher still starts it
    assert jid in [r["id"] for r, _ in starts]


def test_mimo_gate_flag_off_plans_mimo_beside_deepseek(root, conn, cfg):
    cfg["phase3"]["mimo_after_deepseek"] = False
    batch(root, "scale-b9", ["off-s2"])
    built(root, "off-s2", runs={"deepseek": [0.5]})
    rep = p3(conn, cfg)
    assert [(a["first_run"], a["max_runs"]) for a in mimo_jobs(conn, "off-s2")] == [(1, 3)]
    assert not any("mimo" in n for n in rep.get("off-s2", {}).get("notes", []))


def test_stale_gate_rule_shares_the_phase1_key(root, conn, cfg):
    batch(root, "scale-b9", ["stale-s2"])
    built(root, "stale-s2")
    (root / "tasks" / "stale-s2" / "tests" / "t.py").write_text("x\n")
    write_fingerprint(root, "stale-s2", sha="0" * 64)
    p3(conn, cfg)
    fp = reconcile.gate_digest("stale-s2")[:16]
    assert jobs_of(conn, "stale-s2") == [("regate", {"fp": fp, "listing": False})]
    qdb.enqueue(conn, "regate", "stale-s2", {"fp": fp, "listing": False})            # what rule R1 would queue
    assert len(qdb.jobs(conn, "task='stale-s2'")) == 1


def test_new_task_version_supersedes_queued_trials(root, conn, cfg):
    batch(root, "scale-b9", ["ver-s2"])
    built(root, "ver-s2")
    old, _ = qdb.enqueue(conn, "trial_run", "ver-s2", {"model": "mimo", "first_run": 1, "max_runs": 3, "group": 0,
                                                       "version": "oldversion000000"}, origin="reconciler")
    p3(conn, cfg)
    assert qdb.get(conn, old)["state"] == "failed" and "superseded" in qdb.get(conn, old)["result"]


# ---------- worker

def test_worker_commands_and_exit_codes(root, conn, cfg):
    b, _ = qdb.enqueue(conn, "build", "stk-x-1")
    s, _ = qdb.enqueue(conn, "build", "y-s2")
    t, _ = qdb.enqueue(conn, "trial_run", "y-s2", {"model": "mimo", "first_run": 2, "max_runs": 1})
    assert worker.command(qdb.get(conn, b), cfg) == ["bash", "pipelines/stacking/3-build-gate/run_stack_pipeline.sh",
                                                     "stk-x-1"]
    assert worker.command(qdb.get(conn, s), cfg)[1:] == ["pipelines/sibling/6-build/run_pipeline.sh", "deepseek", "y-s2"]
    argv = worker.command(qdb.get(conn, t), cfg)
    assert argv[2].endswith("common/trial/trial.py") and argv[3:] == [
        "y-s2", "--models", "mimo", "--no-verdict", "--first-run", "2", "--max-runs", "1"]
    assert cfg["env"]["trial_run"]["CWE_AGENT_TIMEOUT_MULT"] == "1.5"
    qdb.claim(conn, t, 60)
    qdb.start(conn, t, 77, 60, "/dev/null")
    assert qdb.finish(conn, t, 77, 2, "some runs ungraded", ok_codes=tuple(cfg["ok_exit_codes"]["trial_run"])) == "done"


# ---------- admission during the drain

def test_old_script_work_counts_against_the_caps(root, conn, cfg):
    cfg["limits"]["max_running"]["build"] = 2
    for s in ("q1-s2", "q2-s2"):
        prompt(root, s)
        qdb.enqueue(conn, "build", s)
    old = [proc(11, "bash pipelines/sibling/6-build/run_pipeline.sh deepseek a-s2"),
           proc(12, "bash pipelines/stacking/3-build-gate/run_stack_pipeline.sh stk-b-1")]
    starts, waits = disp(conn, cfg, old).plan()
    assert not starts and all("build at its limit (2 running, old scripts included)" == w for _, w in waits)
    cfg["dispatch"]["max_running_total"] = 2
    cfg["limits"]["max_running"]["build"] = 9
    starts, waits = disp(conn, cfg, old).plan()
    assert not starts and "total at its limit" in waits[0][1]


def test_an_old_build_holds_one_slot_however_many_processes_it_has(root, conn, cfg):
    """A resumed build runs its gate in a subshell with the same command line: still one build slot."""
    cfg["limits"]["max_running"]["build"] = 2
    prompt(root, "q1-s2")
    qdb.enqueue(conn, "build", "q1-s2")
    sess = "6fd2190f-cd82-4eb5-a875-7336d6787b86"
    old = [proc(11, f"bash pipelines/sibling/6-build/resume_pipeline.sh ember-s2 build {sess}"),
           proc(12, f"bash pipelines/sibling/6-build/resume_pipeline.sh ember-s2 build {sess}")]
    starts, _ = disp(conn, cfg, old).plan()
    assert [r["task"] for r, _ in starts] == ["q1-s2"]


def test_own_workers_do_not_count_as_old_scripts(root, conn, cfg):
    cfg["limits"]["max_running"]["build"] = 1
    prompt(root, "q1-s2")
    qdb.enqueue(conn, "build", "q1-s2")
    mine = [(13, "bash pipelines/sibling/6-build/run_pipeline.sh deepseek a-s2".split(), None, {"CWEQ_JOB": "7"})]
    starts, _ = disp(conn, cfg, mine).plan()
    assert [r["task"] for r, _ in starts] == ["q1-s2"]


def test_trials_wait_while_builds_come_first(root, conn, cfg):
    cfg["dispatch"]["trials_wait_builds"] = 2
    built(root, "t-s2")
    qdb.enqueue(conn, "trial_run", "t-s2", {"model": "mimo", "first_run": 1, "max_runs": 3})
    prompt(root, "q-s2")
    qdb.enqueue(conn, "build", "q-s2")
    old = [proc(11, "bash pipelines/sibling/6-build/run_pipeline.sh deepseek a-s2")]
    starts, waits = disp(conn, cfg, old).plan()
    assert [r["kind"] for r, _ in starts] == ["build"]
    assert waits[0][1] == "builds first: 1 running + 1 queued >= 2"


def test_disk_floor_per_kind(root, conn, cfg):
    built(root, "t-s2")
    prompt(root, "q-s2")
    qdb.enqueue(conn, "build", "q-s2")
    qdb.enqueue(conn, "trial_run", "t-s2", {"model": "mimo", "first_run": 1, "max_runs": 3})
    seen = []
    d = disp(conn, cfg, disk_ok=lambda name: seen.append(name) or name != "DISK_MIN_FREE_GB_BUILD")
    starts, waits = d.plan()
    assert [r["kind"] for r, _ in starts] == ["trial_run"]
    assert "disk below its build floor (DISK_MIN_FREE_GB_BUILD" in waits[0][1]


def test_trials_share_a_task_exclusive_kinds_do_not(root, conn, cfg):
    built(root, "t-s2", runs={"deepseek": [0.5]})
    a, _ = qdb.enqueue(conn, "trial_run", "t-s2", {"model": "deepseek", "first_run": 2, "max_runs": 1})
    b, _ = qdb.enqueue(conn, "trial_run", "t-s2", {"model": "deepseek", "first_run": 3, "max_runs": 1})
    r, _ = qdb.enqueue(conn, "regrade", "t-s2", {"trial": "j/x"}, priority=-100)
    cfg["commands"] = {"regrade": ["true"]}
    starts, waits = disp(conn, cfg).plan()
    assert sorted(x["id"] for x, _ in starts) == [a, b]
    assert dict((x["id"], w) for x, w in waits)[r] == "another job of this task is running"


def test_old_trial_running_makes_a_job_wait_not_close(root, conn, cfg):
    built(root, "t-s2", runs={"mimo": [0.5]})
    jid, _ = qdb.enqueue(conn, "trial_run", "t-s2", {"model": "mimo", "first_run": 2, "max_runs": 2})
    old = [proc(21, "python3 -I common/trial/trial.py t-s2 --models mimo --no-verdict --first-run 2 --max-runs 2")]
    d = disp(conn, cfg, old)
    rep = d.tick()
    assert qdb.get(conn, jid)["state"] == "queued"
    assert rep["waiting"][0][1] == "task busy (old script): mimo trials are running"


def test_starts_are_staggered_longer_during_the_first_fill(root, conn, cfg):
    cfg["dispatch"].update(fill_spacing_sec=[5, 5], start_spacing_sec=[1, 1], max_starts_per_tick=3)
    cfg["limits"]["max_running"]["regrade"] = 10
    cfg["commands"] = {"regrade": ["true"]}
    pauses = []
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: dict(OPEN), proc_list=[], spawn=lambda i: 1,
                            sleep=pauses.append)
    for i in range(3):
        qdb.enqueue(conn, "regrade", f"t{i}", {"trial": f"j/{i}"})
    d.tick()
    assert pauses == [5, 5] and not d.filling
    for i in range(3, 5):
        qdb.enqueue(conn, "regrade", f"t{i}", {"trial": f"j/{i}"})
    d.tick()
    assert pauses[2:] == [1]


def test_explain_prints_why_mimo_waits(root, conn, cfg, capsys):
    import argparse
    import cweq
    batch(root, "scale-b9", ["why-s2"])
    built(root, "why-s2", runs={"deepseek": [0.5, 0.5]})
    assert cweq.cmd_explain(conn, cfg, argparse.Namespace(task="why-s2")) == 0
    assert "phase3       mimo waits: DeepSeek has 2/3 graded fails (mimo_after_deepseek)" in capsys.readouterr().out
