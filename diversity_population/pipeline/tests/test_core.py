"""divq core tests: the queue, reconciler, adaptive limits and poll logic, driven by a fake GitHub executor.
No network, no gpg. Run: ~/.venvs/kaggle/bin/python3.12 -m pytest diversity_population/pipeline/tests -q
"""
import json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import divq_core as core
import pytest


# ---- a temp experiment tree + settings -------------------------------------------------
def make_tree(tmp, n=5, accounts=(("acc1", "V1", "acc1/divq-runs"),), chunks=(1,), enabled=True):
    (tmp / "out" / "chunks").mkdir(parents=True)
    (tmp / "out" / "results").mkdir(parents=True)
    rows = ["chunk\torder\tpattern\tentry_id\trepo\tslug\tscore_read\tdeepseek_score\tdeepseek_picked_by"]
    for i in range(n):
        rows.append(f"1\t{i+1}\txxe\te{i}\towner/repo{i}\tdiversity-repo{i}\t{20-i}\t9\t2")
    (tmp / "out" / "chunks" / "all_chunks.tsv").write_text("\n".join(rows) + "\n")
    (tmp / "key").write_text("testpass\n")
    (tmp / ".env").write_text("V1=tok-acc1\nV2=tok-acc2\n")
    acc = "\n".join(f'[[accounts]]\nname="{n_}"\ntoken_var="{v}"\nrepo="{r}"\nenabled={str(enabled).lower()}\n'
                    for n_, v, r in accounts)
    toml = f"""
[paths]
db="{tmp/'out'/'divq.db'}"
releases="{tmp/'out'/'releases'}"
results="{tmp/'out'/'results'}"
chunks="{tmp/'out'/'chunks'}"
key_file="{tmp/'key'}"
env_file="{tmp/'.env'}"
[dispatch]
enabled=true
tick_sec=1
chunks={list(chunks)}
chunk_priority_step=100
aging_per_hour=1
spacing_sec=0
local_disk_floor_gb=0
[limits]
max_running.build=60
max_running.trial_run=120
max_attempts.build=2
max_attempts.trial_run=3
[runner]
cpus=4
memory_mb=16000
[adaptive]
initial=3
min=1
max=6
queued_wait_min=8
raise_wait_min=3
raise_window_min=30
cooldown_min=30
[trial]
models=["deepseek","mimo"]
runs=3
{acc}
"""
    (tmp / "settings.toml").write_text(toml)
    s = core.Settings(tmp / "settings.toml")
    c = core.connect(s.p("db"))
    core.kv_set(c, "release.current", "rel-aaa")   # pretend a release is active
    return s, c


def write_build_result(s, slug, token="j1-a1", status="sound", fp="fp0", account="acc1", cpus=None, mem=None):
    d = s.p("results") / slug / "build" / token
    d.mkdir(parents=True, exist_ok=True)
    (d / "divq-result.json").write_text(json.dumps({"kind": "build", "status": status, "fingerprint": fp,
                                                     "account": account, "run_id": "100", "token": token}))
    if cpus or mem:
        tt = d / "root" / "tasks" / slug; tt.mkdir(parents=True)
        env = "".join([f"cpus = {cpus}\n" if cpus else "", f"memory_mb = {mem}\n" if mem else ""])
        (tt / "task.toml").write_text(f"[environment]\n{env}")


def write_trial_result(s, slug, model, run, token, reward, account="acc1"):
    d = s.p("results") / slug / "trials" / token
    d.mkdir(parents=True, exist_ok=True)
    (d / "divq-result.json").write_text(json.dumps({"kind": "trial", "model": model, "run": run,
        "graded": reward is not None, "reward": reward, "infra_reason": None if reward is not None else "x",
        "account": account}))


class FakeGH:
    """Records dispatches; the test sets run states. Artifact fetch is monkeypatched, so no gpg/network."""
    def __init__(self):
        self.n = 0
        self.dispatched = []            # (account, workflow, inputs)
        self.state = {}                 # run_id -> (status, conclusion, started_at)

    def dispatch(self, account, workflow, inputs):
        self.n += 1
        rid = str(1000 + self.n)
        self.dispatched.append((account, workflow, inputs))
        self.state[rid] = ("queued", "", None)
        return rid

    def find_run(self, a, w, token):
        return None

    def run_status(self, account, run_id):
        return self.state.get(run_id, ("unknown", "", None))

    def download_artifact(self, a, r, n, dest):  # not used (fetch is patched)
        return None


# ---- tests -----------------------------------------------------------------------------
def test_reconcile_plans_one_build_per_chunk_task(tmp_path):
    s, c = make_tree(tmp_path, n=5)
    planned, new = core.reconcile(c, s)
    assert new == 5 and all(p[0] == "build" for p in planned)
    # idempotent: a second pass adds nothing
    _, new2 = core.reconcile(c, s)
    assert new2 == 0


def test_only_enabled_chunks_are_planned(tmp_path):
    s, c = make_tree(tmp_path, n=5, chunks=(2,))     # batch is chunk 1; enabled chunk is 2
    _, new = core.reconcile(c, s)
    assert new == 0


def test_deleted_db_rebuilds_same_jobs(tmp_path):
    s, c = make_tree(tmp_path, n=4)
    core.reconcile(c, s)
    before = [(r["kind"], r["task"]) for r in c.execute("SELECT kind,task FROM jobs ORDER BY id")]
    c.close()
    s.p("db").unlink()
    c2 = core.connect(s.p("db"))
    core.reconcile(c2, s)
    after = [(r["kind"], r["task"]) for r in c2.execute("SELECT kind,task FROM jobs ORDER BY id")]
    assert before == after and len(before) == 4


def test_dispatch_respects_account_limit(tmp_path):
    s, c = make_tree(tmp_path, n=10)
    core.reconcile(c, s)
    ex = FakeGH()
    started, why = core.dispatch_once(c, s, ex)
    assert why is None
    assert len(started) == 3           # adaptive initial = 3 slots on the one account
    # every dispatched job is now 'dispatched'
    assert c.execute("SELECT COUNT(*) n FROM jobs WHERE state='dispatched'").fetchone()["n"] == 3


def test_dispatch_closed_without_account_or_release(tmp_path):
    s, c = make_tree(tmp_path, n=3, enabled=False)
    core.reconcile(c, s)
    _, why = core.dispatch_once(c, s, FakeGH())
    assert "account" in why


def test_build_completion_then_trials_queued(tmp_path, monkeypatch):
    s, c = make_tree(tmp_path, n=1)
    core.reconcile(c, s)
    ex = FakeGH()
    core.dispatch_once(c, s, ex)
    j = c.execute("SELECT * FROM jobs WHERE kind='build'").fetchone()
    ex.state[j["run_id"]] = ("completed", "success", core.utc())

    # fetch is patched to drop a SOUND build result on disk
    def fake_fetch(s_, ex_, job, args):
        write_build_result(s_, job["task"], token=job["token"], account=job["account"])
        return s_.p("results") / job["task"] / "build" / job["token"]
    monkeypatch.setattr(core, "_fetch_and_decrypt", fake_fetch)

    closed = core.poll_once(c, s, ex)
    assert ("done" in [x[1] for x in closed])
    assert core.stage(s, {"slug": "diversity-repo0", "chunk": 1, "order": 1}) == "trialing"
    # reconcile now queues trial runs for both models (run 1 each)
    _, new = core.reconcile(c, s)
    kinds = [r["kind"] for r in c.execute("SELECT kind FROM jobs WHERE state='queued'")]
    assert kinds.count("trial_run") == 2


def test_breaker_candidate_stage(tmp_path):
    s, c = make_tree(tmp_path, n=1)
    slug = "diversity-repo0"
    write_build_result(s, slug)
    for m in ("deepseek", "mimo"):
        for n in (1, 2, 3):
            write_trial_result(s, slug, m, n, f"{m}{n}", reward=0.5)
    assert core.stage(s, {"slug": slug, "chunk": 1, "order": 1}) == "breaker_candidate"


def test_solve_is_done_not_breaker(tmp_path):
    s, c = make_tree(tmp_path, n=1)
    slug = "diversity-repo0"
    write_build_result(s, slug)
    write_trial_result(s, slug, "deepseek", 1, "d1", reward=1.0)
    write_trial_result(s, slug, "mimo", 1, "m1", reward=1.0)
    assert core.stage(s, {"slug": slug, "chunk": 1, "order": 1}) == "done_not_breaker"


def test_too_big_for_runner(tmp_path):
    s, c = make_tree(tmp_path, n=1)
    write_build_result(s, "diversity-repo0", cpus=8)
    assert core.stage(s, {"slug": "diversity-repo0", "chunk": 1, "order": 1}) == "too_big_for_runner"


def test_fetch_failure_retries_then_blocks(tmp_path, monkeypatch):
    s, c = make_tree(tmp_path, n=1)
    core.reconcile(c, s)
    ex = FakeGH()
    monkeypatch.setattr(core, "_fetch_and_decrypt", lambda *a: None)   # never fetchable
    for _ in range(4):
        j = c.execute("SELECT * FROM jobs WHERE kind='build'").fetchone()
        if j["state"] == "queued":
            core.dispatch_once(c, s, ex)
            j = c.execute("SELECT * FROM jobs WHERE kind='build'").fetchone()
        ex.state[j["run_id"]] = ("completed", "failure", core.utc())
        core.poll_once(c, s, ex)
    assert c.execute("SELECT state FROM jobs WHERE kind='build'").fetchone()["state"] == "blocked"


def test_adaptive_lowers_on_long_wait_and_raises_when_calm(tmp_path):
    s, c = make_tree(tmp_path, n=3)
    core.reconcile(c, s)
    now = time.time()
    core.account_limit(c, s, "acc1")                 # seed limit = 3
    # one dispatched run that has waited > 8 min for a runner, and cooldown is past
    c.execute("INSERT INTO jobs(kind,task,args,created,queued_at,account,run_id,state,gh_status,dispatched_at,max_attempts) "
              "VALUES('build','x','{}',?,?,?,?,'dispatched','queued',?,2)",
              (core.utc(now), core.utc(now), "acc1", "r1", core.utc(now - 9 * 60)))
    c.execute("UPDATE limits SET changed_epoch=? WHERE account='acc1'", (now - 9999,))
    core.adapt_limits(c, s, now=now, queued_work=True)
    assert core.account_limit(c, s, "acc1") == 1      # lowered to the running count (0 in_progress -> min 1)

    # now a calm window: a run that started quickly, limit at cap, work waiting -> +1
    c.execute("UPDATE limits SET changed_epoch=? WHERE account='acc1'", (now - 9999,))
    c.execute("DELETE FROM jobs WHERE task='x'")
    c.execute("INSERT INTO jobs(kind,task,args,created,queued_at,account,run_id,state,gh_status,dispatched_at,started,waited_sec,max_attempts) "
              "VALUES('build','y','{}',?,?,?,?,'running','in_progress',?,?,?,2)",
              (core.utc(now), core.utc(now), "acc1", "r2", core.utc(now - 60), core.utc(now - 30), 20))
    core.adapt_limits(c, s, now=now, queued_work=True)
    assert core.account_limit(c, s, "acc1") == 2
