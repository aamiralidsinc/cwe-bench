"""Build-path fixes of 2026-10-28 (pipeline fixes, item 3): build_resume also plans genuine 5-hour timeouts (behind
[build_resume] auto_timeouts) and takes a message (h6); the build job records the builder's own exit code (h7);
audit_prep is planned for failing runs only, also after a regrade turned a run into a solve; a stopped builder is
found by its build tag (the brief is no longer on its command line)."""
import calendar
import json
import os
import time

import events
import frozen
import kinds
import phase4
import qdb
import taskstate
import worker
from conftest import write_config
from test_adopt import batch
from test_freeze_guard import build_records, fake_proc, paused_task

BR = kinds.get("build_resume")
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("br_mod", BR.source)
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)

TIMEOUT_END = "2026-10-27T08:22:30Z"        # 300 min after the start build_records uses: a genuine timeout


def stopped(root, slug, exit_code="124", end=TIMEOUT_END, stop=False):
    b = root / "build" / slug
    build_records(b, "2026-10-27T03:22:03Z", end, exit_code)
    (b / "BUILD-PROMPT.md").write_text("build me\n")
    (b / "pipeline.log").write_text("BUILD-INCOMPLETE (agent did not finish)\n")
    (root / "tasks" / slug).mkdir(parents=True, exist_ok=True)
    if stop:
        (b / "STOP.md").write_text("declined: no real entry point\n")
    return b


def world(root):
    batch(root, "scale-b9", ["cut-s2", "to-s2", "kill-s2", "stop-s2", "stk-to-1", "ok-s2"])
    paused_task(root, "cut-s2")
    stopped(root, "to-s2")
    stopped(root, "kill-s2", exit_code="137")
    stopped(root, "stop-s2", stop=True)
    stopped(root, "stk-to-1")
    stopped(root, "ok-s2", exit_code="0")                       # finished and stopped: nothing to resume


def plan(conn, cfg):
    ctx = taskstate.context([])
    return {r["task"]: r for r in BR.plan(conn, cfg, ctx, events.read_all(ctx))}


def notes(rep, slug):
    return " ".join(rep[slug]["notes"])


def test_timeouts_are_reported_not_planned_by_default(root, conn, cfg, monkeypatch):
    monkeypatch.delenv("BUILD_TIMEOUT", raising=False)
    world(root)
    assert cfg["build_resume"] == {"auto_timeouts": False, "max_auto_resumes": 1}
    rep = plan(conn, cfg)
    jobs = [(r["task"], qdb.args_of(r)) for r in qdb.jobs(conn, "kind='build_resume'")]
    assert jobs == [("cut-s2", {"end": "2026-10-27T14:18:42Z"})]           # the paused build, as before
    assert "cweq enqueue build_resume to-s2" in notes(rep, "to-s2") and "auto_timeouts = false" in notes(rep, "to-s2")
    assert "killed from outside (exit 137, SIGKILL)" in notes(rep, "kill-s2") and not rep["kill-s2"]["want"]
    assert "STOP.md" in notes(rep, "stop-s2") and not rep["stop-s2"]["want"]
    assert "a person" in notes(rep, "stk-to-1") and not rep["stk-to-1"]["want"]
    assert "ok-s2" not in rep


def test_auto_timeouts_plan_one_resume_per_interruption_up_to_the_cap(root, conn, cfg, monkeypatch):
    monkeypatch.delenv("BUILD_TIMEOUT", raising=False)
    world(root)
    cfg["build_resume"] = {"auto_timeouts": True, "max_auto_resumes": 1}
    plan(conn, cfg)
    plan(conn, cfg)                                                          # idempotent
    got = {r["task"]: qdb.args_of(r) for r in qdb.jobs(conn, "kind='build_resume'")}
    assert got == {"cut-s2": {"end": "2026-10-27T14:18:42Z"}, "to-s2": {"end": TIMEOUT_END, "reason": "timeout"}}
    # The resumed build timed out again (a new end): not resumed a second time automatically.
    first = qdb.jobs(conn, "kind='build_resume' AND task='to-s2'")[0]["id"]
    qdb.set_state(conn, first, "done", "")
    stopped(root, "to-s2", end="2026-10-27T13:30:00Z")
    (root / "build" / "to-s2" / "resume_start_utc.txt").write_text("2026-10-27T08:30:00Z\n")
    rep = plan(conn, cfg)
    assert len(qdb.jobs(conn, "kind='build_resume' AND task='to-s2'")) == 1
    assert "again after 1 automatic resume(s)" in notes(rep, "to-s2")


def test_a_resume_queued_by_hand_is_not_planned_again(root, conn, cfg, monkeypatch):
    monkeypatch.delenv("BUILD_TIMEOUT", raising=False)
    world(root)
    cfg["build_resume"] = {"auto_timeouts": True, "max_auto_resumes": 1}
    jid, _ = qdb.enqueue(conn, "build_resume", "to-s2", {"end": TIMEOUT_END, "msg": "debugged: see note"})
    rep = plan(conn, cfg)
    assert [r["id"] for r in qdb.jobs(conn, "kind='build_resume' AND task='to-s2'")] == [jid]
    assert rep["to-s2"]["want"][0]["id"] == jid


def test_the_message_comes_from_the_job_then_the_file_then_the_default(root, monkeypatch):
    b = stopped(root, "to-s2")
    rel = root / "rel"
    text, src = br.message("to-s2", "", b, rel, env={})
    assert src == "default (timeout)" and "5-hour time budget ran out" in text
    assert "~/.tb-graders/cwe/work/to-s2/" in text and f"The project root is now `{rel}`" in text
    assert "only the static and nop gate stages" in text
    f = b / "resume_msg.txt"
    f.write_text("Debugged: the oracle failed on the SSH stand-in; fix test.sh, then report.\n")
    end = calendar.timegm(time.strptime(TIMEOUT_END, "%Y-%m-%dT%H:%M:%SZ"))
    os.utime(f, (end - 60, end - 60))                                       # written before the interruption
    assert br.message("to-s2", "", b, rel, env={"RESUME_MSG": "outer"})[1] == "RESUME_MSG"
    os.utime(f, (end + 60, end + 60))
    text, src = br.message("to-s2", "", b, rel, env={"RESUME_MSG": "outer"})
    assert src == str(f) and text.startswith("Debugged: the oracle failed")
    assert br.message("to-s2", "From the job.", b, rel, env={})[0].startswith("From the job.")
    paused = root / "build" / "cut-s2"
    paused_task(root, "cut-s2")
    assert "paused for several hours" in br.message("cut-s2", "", paused, rel, env={})[0]


def test_the_job_message_reaches_the_command(root):
    row = {"task": "to-s2", "args": json.dumps({"end": TIMEOUT_END, "msg": "hello"})}
    assert BR.command(row, {})[-3:] == ["to-s2", "--msg", "hello"]
    assert BR.command({"task": "to-s2", "args": json.dumps({"end": TIMEOUT_END})}, {})[-1] == "to-s2"


def test_resume_outcome_counts_only_since_the_job_started(root, cfg):
    b = stopped(root, "to-s2")
    t0 = time.time()
    (b / "resume_start_utc.txt").write_text(qdb.utc(t0 + 5) + "\n")
    (b / "end_utc.txt").write_text(qdb.utc(t0 + 50) + "\n")
    old = "2026-10-20T00:00:00Z\tto-s2\tbuild\tBUILD-INCOMPLETE (resumed; agent did not finish)\t\t\n"
    (b / "pipeline.log").write_text(old)
    res = {n: ok for n, ok, _d, _p in BR.check("to-s2", {}, t0, cfg)}
    assert res == {"build_resume.ran": True, "build_resume.outcome": False}   # an older resume's line
    (b / "pipeline.log").write_text(old + f"{qdb.utc(t0 + 60)}\tto-s2\tbuild\tBUILD-INCOMPLETE (resumed; x)\t\t\n")
    assert all(ok for _n, ok, _d, _p in BR.check("to-s2", {}, t0, cfg))


def test_the_build_job_records_the_builders_exit(tmp_path, root):
    script = ("mkdir -p build/a && date -u +%Y-%m-%dT%H:%M:%SZ > build/a/end_utc.txt && echo 124 > build/a/build-exit.txt"
              " && echo 'BUILD-INCOMPLETE (agent did not finish)' > build/a/pipeline.log"
              " && echo 'a: builder exit 124, BUILD-INCOMPLETE'")
    cfg = write_config(tmp_path, root, f'[commands]\nbuild = ["sh", "-c", "{script}"]\n')
    conn = qdb.connect(cfg["db"])
    jid, _ = qdb.enqueue(conn, "build", "a")
    assert qdb.claim(conn, jid, 60)
    worker.run(conn, cfg, jid)
    row = qdb.get(conn, jid)
    assert (row["state"], row["exit_code"], row["result"]) == ("done", 124, "a: builder exit 124, BUILD-INCOMPLETE")
    assert "job records exit 124" in open(row["log_path"]).read()


def test_an_older_exit_file_is_not_the_jobs(root):
    b = root / "build" / "a"
    b.mkdir()
    (b / "build-exit.txt").write_text("124\n")
    os.utime(b / "build-exit.txt", (1000, 1000))
    assert kinds.builder_exit_file("a", time.time()) is None
    assert kinds.builder_exit_file("a", 900) == 124
    assert kinds.builder_exit_file("missing", 0) is None


def test_audit_prep_skips_a_run_whose_regrade_is_a_solve(root, conn, cfg):
    cfg["phase4"] = {"enabled": True, "audits": True, "fairness": False, "cleanup": False, "step3": False}
    runs = []
    for name, reward in (("nifi-s2__S", 1.0), ("nifi-s2__F", 0.4)):
        job = f"nifi-s2-mimo-r{len(runs) + 1}-20261028-000000-n001"
        t = root / "jobs" / job / name
        (t / "verifier").mkdir(parents=True)
        (t / "result.json").write_text(json.dumps({"verifier_result": {"rewards": {"reward": 0.0}}}))
        g = t / "regrade-20261028T231644Z"
        (g / "verifier").mkdir(parents=True)
        (g / "REGRADE.json").write_text(json.dumps({"reward": reward}))
        runs.append((job, name))
    a = root / "build" / "audit"
    a.mkdir(parents=True)
    (a / "awaiting_audit.tsv").write_text("task\tmodel\treward\tjob\ttrial\tgrading\n" + "".join(
        f"nifi-s2\tmimo\t0.0\t{j}\t{t}\toriginal\n" for j, t in runs))     # written before the regrades
    rep = phase4.reconcile(conn, cfg, taskstate.context([]), [], now=1_800_000_000)
    prep = [w["args"]["trial"] for r in rep for w in r["want"] if w["kind"] == "audit_prep"]
    assert prep == [f"{runs[1][0]}/nifi-s2__F"]
    assert any("a solve on its current grading (regrade-20261028T231644Z)" in n for r in rep for n in r["notes"])


def test_a_stopped_builder_is_named_by_its_build_tag(tmp_path):
    fake_proc(tmp_path, 21, "T", "/home/u/.local/bin/claude -p --model m --output-format json")
    (tmp_path / "21" / "environ").write_bytes(b"HOME=/home/u\0CWE_BUILD_RUN=ember-s2:1:2\0CWE_BUILD_SLUG=ember-s2\0")
    fake_proc(tmp_path, 22, "T", "/home/u/.local/bin/claude -p hello")       # not a builder, not tagged
    assert {p["pid"]: p["task"] for p in frozen.scan(tmp_path)} == {21: "ember-s2"}


def test_a_session_from_an_older_release_is_copied_into_the_running_releases_folder(tmp_path):
    projects = tmp_path / "projects"
    old = projects / "-home-u-cwe-bench-releases-591de221a3d4"
    (old / "abc" / "tool-results").mkdir(parents=True)
    (old / "abc.jsonl").write_text('{"m": "Task: `to-s2`"}\n')
    (old / "abc" / "tool-results" / "r1.txt").write_text("x")
    f = br.session_file("to-s2", root=projects)
    dest = br.into_project(f, "/home/u/cwe-bench-releases/603b1e9cfb03", root=projects)
    assert dest == projects / "-home-u-cwe-bench-releases-603b1e9cfb03" / "abc.jsonl" and dest.read_text() == f.read_text()
    assert (dest.parent / "abc" / "tool-results" / "r1.txt").is_file()
    assert br.into_project(dest, "/home/u/cwe-bench-releases/603b1e9cfb03", root=projects) is None   # already there
