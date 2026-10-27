"""Adoption (adopt.py) and the never-redo rule (taskstate.redo_reason): the queue starts from the pipeline's current
state, records running work instead of starting it again, and refuses or closes jobs whose work the files show done."""
import adopt
import dispatch
import qdb
import taskstate


def batch(root, name, slugs):
    d = root / "pipelines" / "router" / "out" / "batches"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.txt").write_text("\n".join(slugs) + "\n")


def built(root, slug, markers=(".sound",), runs=None):
    """A build that ran and ended, with the given markers and per-model rewards in runs_<model>.log."""
    b = root / "build" / slug
    b.mkdir(parents=True, exist_ok=True)
    (root / "tasks" / slug / "tests").mkdir(parents=True, exist_ok=True)
    (b / "start_utc.txt").write_text("2026-10-27T01:00:00Z\n")
    (b / "end_utc.txt").write_text("2026-10-27T02:00:00Z\n")
    for m in markers:
        (b / m).write_text("")
    for model, rewards in (runs or {}).items():
        (b / f"runs_{model}.log").write_text("".join(f"run {i} reward={r}\n" for i, r in enumerate(rewards)))
    return b


def ledger(root, rows):
    """rows: (slug, deepseek cell, mimo cell, verdict)."""
    a = root / "build" / "audit"
    a.mkdir(parents=True, exist_ok=True)
    body = "".join(f"| stacking | {s} | {d} | {m} | {v} |\n" for s, d, m, v in rows)
    (a / "ledger.md").write_text("# Ledger\n\n## All tasks\n\n| Track | Task | DeepSeek | MiMo | Verdict |\n"
                                 "|---|---|---|---|---|\n" + body)


def read(slug, procs=()):
    return taskstate.read(slug, taskstate.context(list(procs)))


def proc(pid, cmd):
    return (pid, cmd.split(), None, {})


def test_stages_cover_the_pipeline(root):
    batch(root, "scale-b9", ["new-s2", "half-s2", "brk-s2", "kept-s2", "gone-s2", "solved-s2", "one-s2"])
    (root / "build" / "half-s2").mkdir()
    (root / "build" / "half-s2" / "start_utc.txt").write_text("2026-10-27T01:00:00Z\n")
    built(root, "brk-s2", runs={"deepseek": [0.5, 0.5, 0.5], "mimo": [0.2, 0.2, 0.2]})
    built(root, "kept-s2", runs={"deepseek": [0.5] * 3, "mimo": [0.5] * 3})
    (root / "build" / "kept-s2" / "HUMAN-DECISION.md").write_text("DECISION: KEEP\nDATE: 2026-10-27\n")
    built(root, "gone-s2")
    (root / "build" / "gone-s2" / "HUMAN-DECISION.md").write_text(
        "DECISION: KEEP\nDATE: 2026-10-27\nDELIVERED: 2026-10-27 to the client repo\n")
    built(root, "solved-s2", runs={"deepseek": [1.0], "mimo": [0.5] * 3})
    built(root, "one-s2", runs={"deepseek": [0.5] * 3})
    ledger(root, [("brk-s2", "**failed 0/3** [0.5]", "**failed 0/3** [0.2] (+1 awaiting audit)", "**BREAKER candidate**")])
    got = {s: read(s) for s in ("new-s2", "half-s2", "brk-s2", "kept-s2", "gone-s2", "solved-s2", "one-s2")}
    assert got["new-s2"]["stage"] == "waiting_build" and got["new-s2"]["next"] == "build"
    assert got["half-s2"]["stage"] == "build_interrupted"
    assert got["brk-s2"]["stage"] == "awaiting_audit"
    assert got["kept-s2"]["stage"] == "kept"
    assert got["gone-s2"]["stage"] == "delivered" and got["gone-s2"]["next"] == "nothing"
    assert got["solved-s2"]["stage"] == "not_breaker"
    assert got["one-s2"]["stage"] == "waiting_trials" and got["one-s2"]["next"] == "trial mimo"


def test_running_work_is_recorded_not_restarted(root):
    batch(root, "scale-b9", ["b-s2", "t-s2", "stk-r-1"])
    (root / "build" / "b-s2").mkdir()
    built(root, "t-s2", runs={"deepseek": [0.5]})
    built(root, "stk-r-1", markers=(".sound", ".hold-repair"))
    ps = [proc(11, "bash pipelines/sibling/6-build/run_pipeline.sh deepseek b-s2"),
          proc(12, "python3 -I common/trial/trial.py t-s2 --models deepseek"),
          proc(13, "bash common/gate/regate.sh stk-r-1 --listing")]
    ctx = taskstate.context(ps)
    assert taskstate.read("b-s2", ctx)["stage"] == "building"
    t = taskstate.read("t-s2", ctx)
    assert t["stage"] == "trialing" and t["models"]["deepseek"]["running"] == 1
    assert taskstate.read("stk-r-1", ctx)["stage"] == "regating"
    assert taskstate.redo_reason("build", "b-s2", {}, ctx) == "a build is running"
    assert taskstate.redo_reason("trial_run", "t-s2", {"model": "deepseek"}, ctx) == "deepseek trials are running"


def test_never_redo(root):
    built(root, "done-s2", runs={"deepseek": [0.5] * 3, "mimo": [0.4]})
    ctx = taskstate.context([])
    assert "already ran" in taskstate.redo_reason("build", "done-s2", {}, ctx)
    assert taskstate.redo_reason("gate", "done-s2", {}, ctx) == "SOUND on the current files"
    assert "already has a verdict" in taskstate.redo_reason("trial_run", "done-s2", {"model": "deepseek"}, ctx)
    assert taskstate.redo_reason("trial_run", "done-s2", {"model": "mimo"}, ctx) is None    # 1 of 3 runs: continue
    assert taskstate.redo_reason("regrade", "done-s2", {}, ctx) is None                     # reconciler rules decide


def test_ledger_verdict_wins_over_an_empty_runs_log(root):
    """Runs of an older task version count in the ledger; the queue must not trial the model again."""
    built(root, "old-s2", runs={"deepseek": [0.5] * 3})
    ledger(root, [("old-s2", "**failed 0/3** [0.5]", "SOLVED 1/1", "rejected (MiMo solved)")])
    t = read("old-s2")
    assert t["stage"] == "not_breaker"
    assert taskstate.redo_reason("trial_run", "old-s2", {"model": "mimo"},
                                 taskstate.context([])) == "trials are over (stage not_breaker)"


def test_adopt_records_and_is_idempotent(root, conn, cfg):
    batch(root, "scale-b9", ["a-s2", "b-s2"])
    built(root, "a-s2", runs={"deepseek": [1.0], "mimo": [1.0]})
    rep = adopt.adopt(conn, cfg, dry_run=True, proc_list=[])
    assert rep["ok"] and rep["id"] is None and qdb.latest_adoption(conn) is None      # dry run writes nothing
    rep1 = adopt.adopt(conn, cfg, proc_list=[])
    rep2 = adopt.adopt(conn, cfg, proc_list=[])
    assert rep1["ok"] and rep2["id"] == rep1["id"] + 1
    rows = conn.execute("SELECT task, stage, adoption_id FROM tasks ORDER BY task").fetchall()
    assert [(r["task"], r["stage"], r["adoption_id"]) for r in rows] == [
        ("a-s2", "not_breaker", rep2["id"]), ("b-s2", "waiting_build", rep2["id"])]
    assert rep2["counts"] == {"waiting_build": 1, "not_breaker": 1}


def test_conflicts_keep_the_dispatcher_closed(root, conn, cfg):
    batch(root, "scale-b9", ["pkg-s2"])
    (root / "tasks" / "pkg-s2").mkdir()                    # a package with no build record: a rebuild would redo it
    ps = [proc(21, "python3 -I common/trial/trial.py stranger-s2 --models mimo")]
    rep = adopt.adopt(conn, cfg, proc_list=ps)
    assert not rep["ok"]
    assert any("pkg-s2" in c for c in rep["conflicts"]) and any("stranger-s2" in c for c in rep["conflicts"])
    cfg["require_adoption"] = True
    cfg["commands"] = {"regrade": ["true"]}
    qdb.enqueue(conn, "regrade", "x-s2", {"trial": "j/x-s2__1"})
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: {}, proc_list=[], spawn=lambda i: 1)
    starts, waits = d.plan()
    assert not starts and "has conflicts" in waits[0][1]


def test_dispatcher_waits_for_an_adoption(root, conn, cfg):
    cfg["require_adoption"] = True
    cfg["commands"] = {"regrade": ["true"]}
    qdb.enqueue(conn, "regrade", "x-s2", {"trial": "j/x-s2__1"})
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: {}, proc_list=[], spawn=lambda i: 1)
    assert "no adoption yet" in d.plan()[1][0][1]
    adopt.adopt(conn, cfg, proc_list=[])
    starts, _ = d.plan()
    assert [r["task"] for r, _ in starts] == ["x-s2"]


def test_dispatcher_closes_a_job_that_would_redo(root, conn, cfg):
    built(root, "fin-s2", runs={"deepseek": [0.5] * 3})
    cfg["commands"] = {"trial_run": ["true"]}
    cfg["limits"]["max_running"]["trial_run"] = 5
    jid, _ = qdb.enqueue(conn, "trial_run", "fin-s2", {"model": "deepseek"})
    open_id, _ = qdb.enqueue(conn, "trial_run", "fin-s2", {"model": "mimo"})
    started = []
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: {}, proc_list=[],
                            spawn=lambda i: started.append(i) or 1)
    d.tick()
    row = qdb.get(conn, jid)
    assert row["state"] == "done" and "already has a verdict" in row["result"]
    assert started == [open_id]


def test_tasks_outside_the_batches_are_never_rebuilt(root):
    """Older tasks have packages and build folders without the scale run's markers; the queue must leave them."""
    (root / "build" / "old-inv").mkdir()
    (root / "build" / "old-inv" / "pipeline.log").write_text("building...\n")    # started, never 'ended'
    (root / "tasks" / "old-inv").mkdir()
    (root / "build" / "old-inj").mkdir()
    (root / "build" / "old-inj" / "pipeline.log").write_text("done\n")
    (root / "tasks" / "old-inj").mkdir()
    ledger(root, [("old-inj", "SOLVED 2/2", "**failed 0/3** [0.5]", "rejected (DeepSeek solved)")])
    ctx = taskstate.context([])
    assert taskstate.read("old-inv", ctx)["stage"] == "outside_batches"
    assert taskstate.read("old-inj", ctx)["stage"] == "not_breaker"
    assert "before the scale batches" in taskstate.redo_reason("build", "old-inv", {}, ctx)


def test_delivery_register_marks_delivered(root):
    """Deliveries made before DELIVERED lines existed are known from build/audit/delivered.tsv: never redelivered."""
    built(root, "early-ds", runs={"deepseek": [0.5] * 3, "mimo": [0.5] * 3})
    (root / "build" / "audit").mkdir(parents=True, exist_ok=True)
    (root / "build" / "audit" / "delivered.tsv").write_text(
        "# slug\tdelivered_as\tclient_commit\tdate\nearly-ds\tearly-task-name\tabc1234\t2026-10-20\n")
    t = read("early-ds")
    assert t["stage"] == "delivered" and "early-task-name" in t["delivered"]


def test_wrapper_script_text_is_not_a_task(root):
    """A shell wrapper whose argv holds a script text such as 'regate.sh $S' names no task."""
    ps = [proc(31, "bash -c S=x-s2; bash common/gate/regate.sh $S --listing")]
    assert "$S" not in taskstate.running(ps)
