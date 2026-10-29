"""Untrusted runs (untrusted.py, 2026-10-29): a graded run whose post-run audit is untrusted is left out of the ledger,
so the queue must not count it as a graded fail. It is re-run (infrastructure causes, test faults nobody repairs),
re-audited (a repaired test fault whose regrade kept the reward), or left waiting for the regrade or the repair."""
import json

import phase3
import phase4
import qdb
import repairstep
import taskstate
import trial_state
import untrusted
from conftest import set_mtime
from test_adopt import batch, built, ledger
from test_repair import epoch, rcfg

UNFAIR = {"test": "security::t_unfair", "outcome": "fail", "verdict": "test-fault"}


def run(root, slug, model, n, reward=0.5, stamp="20261028T010000Z", seq=1):
    """A finished, graded trial named like trial.py's jobs, and its row in runs_<model>.log. Returns (job, trial)."""
    job = f"{slug}-{model}-r{n}-{stamp[:8]}-{stamp[9:15]}-n{seq:03d}"
    t = root / "jobs" / job / f"{slug}__{model[0]}{n}x{seq}"
    (t / "verifier").mkdir(parents=True)
    (t / "config.json").write_text(json.dumps({"task": {"path": f"/x/tasks/{slug}"}}))
    (t / "result.json").write_text(json.dumps({"finished_at": stamp[:4] + "-" + stamp[4:6] + "-" + stamp[6:8] + "T"
                                               + stamp[9:11] + ":" + stamp[11:13] + ":00Z",
                                               "verifier_result": {"rewards": {"reward": reward}}}))
    (t / "final-code").mkdir()
    (t / "final-code" / "changes.patch").write_text("")
    log_row(root, slug, model, reward, job)
    return job, t


def log_row(root, slug, model, reward, job=""):
    with open(root / "build" / slug / f"runs_{model}.log", "a") as f:
        f.write(f"2026-10-28 01:00:00\tn001\treward={reward}\tcause=None" + (f"\t{job}" if job else "") + "\n")


def audit(t, trusted=True, attribution="model-failed", stamp="20261028T020000Z", grading="original", items=()):
    pm = t / f"postmortem-{stamp}"
    pm.mkdir(parents=True)
    (pm / "PREPARED.json").write_text(json.dumps({"grading_audited": grading}))
    (pm / "POSTMORTEM.json").write_text(json.dumps({"grading_audited": grading, "verdict": {
        "trustworthy": trusted, "attribution": attribution, "items": list(items)}}))
    return pm


def regrade(t, stamp, reward, tests_hash):
    d = t / f"regrade-{stamp}"
    (d / "verifier").mkdir(parents=True)
    (d / "REGRADE.json").write_text(json.dumps({"reward": reward, "tests_hash": tests_hash}))
    (d / "verifier" / "reward.json").write_text(json.dumps({"reward": reward}))
    return d


def task(root, slug, deepseek="**failed 0/3** [0.5, 0.5, 0.5]", mimo="0/2 so far, needs 3 [0.5, 0.5] "
         "(+1 audit: untrusted)"):
    """A sound batch task: DeepSeek failed 3 trusted runs, MiMo's cell as given."""
    batch(root, "scale-b9", [slug])
    built(root, slug)
    (root / "tasks" / slug / "tests" / "security").mkdir(parents=True, exist_ok=True)
    (root / "tasks" / slug / "tests" / "security" / "a_test.py").write_text("assert True\n")
    for n in (1, 2, 3):
        _job, t = run(root, slug, "deepseek", n)
        audit(t)
    ledger(root, [(slug, deepseek, mimo, "open")])


def read(slug, cfg, ctx=None):
    """taskstate.read with the test settings (jobs_dir); the queue's passes put cfg in ctx the same way."""
    ctx = ctx if ctx is not None else taskstate.context([])
    ctx.setdefault("cfg", cfg)
    return taskstate.read(slug, ctx)


def trial_jobs(conn, slug):
    return [(r["state"], qdb.args_of(r)) for r in qdb.jobs(conn, "kind='trial_run' AND task=?", (slug,))]


def p3(conn, cfg):
    return {t["task"]: t for t in phase3.reconcile(conn, cfg, taskstate.context([]))}


# ---------------------------------------------------------------- trial_state

def test_trial_state_drops_named_graded_rows_only(root):
    built(root, "ts-a")
    log_row(root, "ts-a", "mimo", 0.5, "ts-a-mimo-r1-20261028-010000-n001")
    log_row(root, "ts-a", "mimo", None, "ts-a-mimo-r2-20261028-010000-n001")
    log_row(root, "ts-a", "mimo", 0.5, "ts-a-mimo-r3-20261028-010000-n001")
    log_row(root, "ts-a", "mimo", 0.5)                       # an older row without a job name
    assert trial_state.state("ts-a", "mimo") == ("failed", [0.5, 0.5, 0.5], 1)
    s, graded, ungraded = trial_state.state("ts-a", "mimo", drop={"ts-a-mimo-r1-20261028-010000-n001",
                                                                  "ts-a-mimo-r2-20261028-010000-n001"})
    assert (s, graded, ungraded) == ("incomplete", [0.5, 0.5], 1)   # an ungraded row is not "dropped"


# ---------------------------------------------------------------- rerun: an infrastructure cause

def test_infra_untrusted_run_is_rerun_and_the_task_waits_for_trials(root, conn, cfg):
    task(root, "un-a")
    j1, t1 = run(root, "un-a", "mimo", 1)
    audit(t1, trusted=False, attribution="harness-or-infra")      # a provider content-filter stop
    for n in (2, 3):
        _j, t = run(root, "un-a", "mimo", n)
        audit(t)
    t = read("un-a", cfg)
    mm = t["models"]["mimo"]
    assert t["stage"] == "waiting_trials" and "re-runs 1 untrusted run" in t["next"]
    assert (mm["launch"], mm["graded"], mm["rerun"], mm["untrusted"]) == ("incomplete", 2, [j1], {"rerun": 1})
    rep = p3(conn, cfg)
    v = taskstate.gate_sha16("un-a")
    assert trial_jobs(conn, "un-a") == [("queued", {"model": "mimo", "first_run": 4, "max_runs": 1, "group": 3,
                                                    "version": v})]
    assert any("untrusted run(s) do not count as graded" in n for n in rep["un-a"]["notes"])
    assert taskstate.redo_reason("trial_run", "un-a", {"model": "mimo"}, {**taskstate.context([]), "cfg": cfg}) is None
    p3(conn, cfg)                                                   # idempotent
    assert len(trial_jobs(conn, "un-a")) == 1


def test_without_the_ledger_mark_nothing_changes(root, conn, cfg):
    task(root, "un-n", mimo="**failed 0/3** [0.5, 0.5, 0.5]")
    for n in (1, 2, 3):
        _j, t = run(root, "un-n", "mimo", n)
        audit(t, trusted=n != 1, attribution="harness-or-infra" if n == 1 else "model-failed")
    assert read("un-n", cfg)["models"]["mimo"]["launch"] == "failed"
    p3(conn, cfg)
    assert trial_jobs(conn, "un-n") == []


def test_held_or_blocked_model_gets_no_run(root, conn, cfg):
    task(root, "un-h")
    _j, t1 = run(root, "un-h", "mimo", 1)
    audit(t1, trusted=False, attribution="harness-or-infra")
    for n in (2, 3):
        run(root, "un-h", "mimo", n)
    (root / "build" / "un-h" / "hold_mimo").write_text("blocked by the provider\n")
    p3(conn, cfg)
    assert trial_jobs(conn, "un-h") == []                           # hold_mimo: blocked models get no runs
    (root / "build" / "un-h" / "hold_mimo").unlink()
    (root / "build" / "un-h" / ".hold-repair").write_text("repair in progress\n")
    p3(conn, cfg)
    assert trial_jobs(conn, "un-h") == [] and read("un-h", cfg)["stage"] == "held_repair"


def test_launch_limit_still_applies(root, conn, cfg):
    task(root, "un-l")
    _j, t1 = run(root, "un-l", "mimo", 1)
    audit(t1, trusted=False, attribution="harness-or-infra")
    for n in (2, 3):
        run(root, "un-l", "mimo", n)
    v = taskstate.gate_sha16("un-l")
    for g in (0, 1, 2):
        jid, _ = qdb.enqueue(conn, "trial_run", "un-l", {"model": "mimo", "first_run": g + 1, "max_runs": 1,
                                                         "group": g, "version": v})
        qdb.set_state(conn, jid, "done", "ran")
    rep = p3(conn, cfg)
    assert len(trial_jobs(conn, "un-l")) == 3
    assert any("3 trial launches without a verdict" in n for n in rep["un-l"]["notes"])


# ---------------------------------------------------------------- a stuck model: one fresh run per untrusted run

def test_stuck_model_gets_one_fresh_run_per_untrusted_run(root, conn, cfg):
    task(root, "un-s", mimo="0/1 so far, needs 3 [0.8] (+6 provider stop) (+1 audit: untrusted)")
    j1, t1 = run(root, "un-s", "mimo", 1, reward=0.0)
    audit(t1, trusted=False, attribution="harness-or-infra")
    for i in range(6):                                              # rate-limit cuts: ungraded rows
        log_row(root, "un-s", "mimo", None, f"un-s-mimo-r{2 + i}-20261028-030000-n00{i}")
    _j, t7 = run(root, "un-s", "mimo", 7, reward=0.8)
    audit(t7)
    ctx = taskstate.context([])
    t = read("un-s", cfg, ctx)
    assert t["models"]["mimo"]["launch"] == "stuck" and t["stage"] == "waiting_trials"
    p3(conn, cfg)
    v = taskstate.gate_sha16("un-s")
    assert trial_jobs(conn, "un-s") == [("queued", {"model": "mimo", "first_run": 9, "max_runs": 1, "group": 8,
                                                    "version": v, "rerun_of": j1})]
    p3(conn, cfg)                                                   # queued: not planned twice
    assert len(trial_jobs(conn, "un-s")) == 1
    # the fresh run ended (here: no result again) -> the task is stuck for a person, no second fresh run
    jid = qdb.jobs(conn, "kind='trial_run' AND task='un-s'")[0]["id"]
    qdb.set_state(conn, jid, "done", "ran")
    log_row(root, "un-s", "mimo", None, "un-s-mimo-r9-20261028-050000-n001")
    p3(conn, cfg)
    assert len(trial_jobs(conn, "un-s")) == 1
    ctx = taskstate.context([])
    ctx["reruns"] = untrusted.rerun_jobs(conn)
    assert read("un-s", cfg, ctx)["stage"] == "trials_stuck"


# ---------------------------------------------------------------- test faults: re-audit, wait, or re-run

def repaired_task(root, slug, regrade_on_current=True, reward_after=0.5):
    """MiMo r1: an untrusted test-fault audit of its original grading, a repair folder after it, then a regrade."""
    task(root, slug)
    j1, t1 = run(root, slug, "mimo", 1)
    audit(t1, trusted=False, attribution="test-fault", stamp="20261028T020000Z", items=[UNFAIR])
    for n in (2, 3):
        _j, t = run(root, slug, "mimo", n)
        audit(t)
    rep = root / "build" / slug / "repaired-tests-20261028T030000Z-repair"
    rep.mkdir()
    (rep / "README.md").write_text("repaired\n")
    set_mtime(rep, epoch("20261028T030000Z"))
    cur = repairstep.tests_hash(slug)
    g = regrade(t1, "20261028T040000Z", reward_after, cur if regrade_on_current else "0" * 20)
    return j1, t1, g


def test_repaired_test_fault_is_reaudited_not_rerun(root, conn, cfg):
    j1, t1, g = repaired_task(root, "un-r")
    e, = untrusted.classify("un-r", {"cfg": cfg, "ledger": {}})["mimo"]
    assert (e["job"], e["action"], e["audited"], e["grading"]) == (j1, "reaudit", "original", g.name)
    t = read("un-r", cfg)
    assert t["stage"] == "awaiting_audit" and "1 reaudit" in t["next"]
    p3(conn, cfg)
    assert trial_jobs(conn, "un-r") == []                           # never re-run
    cfg["phase4"] = {"enabled": True, "audits": True, "fairness": False, "cleanup": False, "step3": False}
    rep = phase4.reconcile(conn, cfg, taskstate.context([]), [], now=1_800_000_000)
    prep = [(w["task"], w["args"]) for r in rep for w in r["want"] if w["kind"] == "audit_prep"]
    assert prep == [("un-r", {"trial": f"{j1}/{t1.name}", "grading": g.name})]
    # once prepared, the folder waits for its auditor: no second job
    pm = t1 / "postmortem-20261028T050000Z"
    pm.mkdir()
    (pm / "PREPARED.json").write_text(json.dumps({"grading_audited": g.name}))
    rep = phase4.reconcile(conn, cfg, taskstate.context([]), [], now=1_800_000_000)
    assert not [w for r in rep for w in r["want"] if w["kind"] == "audit_prep" and w["task"] == "un-r"]


def test_repaired_test_fault_waits_for_its_regrade_on_the_current_tests(root, conn, cfg):
    repaired_task(root, "un-w", regrade_on_current=False)
    e, = untrusted.classify("un-w", {"cfg": cfg, "ledger": {}})["mimo"]
    assert e["action"] == "wait_regrade"
    p3(conn, cfg)
    assert trial_jobs(conn, "un-w") == []


def test_reaudited_regrade_still_untrusted_is_rerun(root, conn, cfg):
    j1, t1, g = repaired_task(root, "un-x")
    audit(t1, trusted=False, attribution="test-fault", stamp="20261028T060000Z", grading=g.name, items=[UNFAIR])
    c = rcfg(cfg, max_per_task=1)                                   # the repair step takes on no further repair
    (root / "build" / "un-x" / "repair-inputs-20261028T025000Z").mkdir()
    (root / "build" / "un-x" / "repair-inputs-20261028T025000Z" / "JOB-RESULT.json").write_text(
        json.dumps({"result": "repaired"}))
    (root / "build" / "un-x" / "repair-inputs-20261028T025000Z" / "FINDING.json").write_text(json.dumps({"key": "f-1"}))
    e, = untrusted.classify("un-x", {"cfg": c, "ledger": {}})["mimo"]
    assert e["action"] == "rerun" and "still untrusted" in e["why"]


def test_test_fault_the_repair_step_owns_waits_for_the_repair(root, conn, cfg):
    task(root, "un-o")
    _j, t1 = run(root, "un-o", "mimo", 1)
    audit(t1, trusted=False, attribution="test-fault", items=[UNFAIR])
    for n in (2, 3):
        _j, t = run(root, "un-o", "mimo", n)
        audit(t)
    e, = untrusted.classify("un-o", {"cfg": cfg, "ledger": {}})["mimo"]
    assert e["action"] == "wait_repair" and "plans a repair" in e["why"]
    assert read("un-o", cfg)["stage"] == "awaiting_audit"
    p3(conn, cfg)
    assert trial_jobs(conn, "un-o") == []
    e, = untrusted.classify("un-o", {"cfg": cfg, "ledger": {}, "repairs_active": {"un-o"}})["mimo"]
    assert e["action"] == "wait_repair" and "queued or running" in e["why"]
    # a test fault the repair step does not take on (max_per_task reached) is re-run
    e, = untrusted.classify("un-o", {"cfg": rcfg(cfg, max_per_task=0), "ledger": {}})["mimo"]
    assert e["action"] == "rerun" and "does not take on" in e["why"]
