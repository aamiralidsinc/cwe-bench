"""Freeze guards: stopped pipeline processes are reported (frozen.py, monitor, preflight), a builder cut by its overdue
timer after a pause is classified as interrupted (agent_status.py, markers.build_paused) and resumed in its own session
(kinds/build_resume.py), never rebuilt."""
import importlib
import json
import sys
from pathlib import Path

import events
import frozen
import kinds
import markers
import monitor
import phase3
import preflight
import qdb
import taskstate
from test_adopt import batch, proc

UTIL = Path(__file__).resolve().parents[2] / "util"
if str(UTIL) not in sys.path:
    sys.path.insert(0, str(UTIL))
agent_status = importlib.import_module("agent_status")


def fake_proc(root, pid, state, cmd, start="1000"):
    d = root / str(pid)
    d.mkdir(parents=True)
    rest = [state] + ["0"] * 18 + [start] + ["0"] * 10            # field 3 = state, field 22 = starttime
    (d / "stat").write_text(f"{pid} (x y) " + " ".join(rest) + "\n")
    (d / "cmdline").write_bytes(b"\0".join(a.encode() for a in cmd.split()) + b"\0")


# ---------- frozen processes

def test_scan_finds_stopped_pipeline_processes_only(tmp_path):
    fake_proc(tmp_path, 11, "T", "/home/u/.local/bin/claude -p Build one security-fix benchmark task Task: `cline-s2`")
    fake_proc(tmp_path, 12, "T", "python3 -I common/trial/trial.py psr7-s2 --models mimo")
    fake_proc(tmp_path, 13, "S", "bash common/launch/run_build.sh ember-s2")                  # running: not stopped
    fake_proc(tmp_path, 14, "T", "vim notes.txt")                                             # not pipeline work
    got = {p["pid"]: p["task"] for p in frozen.scan(tmp_path)}
    assert got == {11: "cline-s2", 12: "psr7-s2"}


def test_tracker_reports_only_after_the_grace_period():
    procs = [{"pid": 5, "start": "9", "task": "x-s2", "cmd": "trial.py x-s2"}]
    tr = frozen.Tracker(lambda: procs)
    assert tr.frozen(1000, 120) == []
    assert [p["pid"] for p in tr.frozen(1130, 120)] == [5]
    procs.clear()                                              # resumed: forgotten
    assert tr.frozen(1200, 120) == []


def test_monitor_raises_alert_and_one_urgent_event(conn, cfg, root):
    t0 = 1_800_000_000
    procs = [{"pid": 7, "start": "1", "task": "cline-s2", "cmd": "claude -p ... Task: `cline-s2`"}]
    m = monitor.Monitor(conn, cfg, root, proc_list=[], now=lambda: t[0], docker=False, frozen_scan=lambda: procs)
    t = [t0]
    rep = m.tick()
    assert not any(n == "process_frozen" for n, *_ in rep["alerts"])
    t[0] = t0 + 150
    rep = m.tick()
    assert ("process_frozen", "raised") in [(n, st) for n, st, *_ in rep["alerts"]]
    assert rep["sample"]["stopped_procs"] == 1
    ev = [r for r in events.listing(conn) if r["kind"] == "process.frozen"]
    assert len(ev) == 1 and ev[0]["urgent"] == 1 and "cline-s2" in ev[0]["task"]
    t[0] = t0 + 210
    m.tick()                                                   # still frozen: no second alert or event
    assert len([r for r in events.listing(conn) if r["kind"] == "process.frozen"]) == 1
    procs.clear()
    t[0] = t0 + 270
    rep = m.tick()
    assert ("process_frozen", "cleared") in [(n, st) for n, st, *_ in rep["alerts"]]


def test_preflight_frozen_is_critical():
    st, detail, fix = preflight.check_frozen(lambda: [{"pid": 3, "task": "go-git-s2", "cmd": "x"}])
    assert st == preflight.CRITICAL and "go-git-s2" in detail and "never freeze" in fix
    assert preflight.check_frozen(lambda: [])[0] == preflight.OK


# ---------- classification of a timer that fired late

def build_records(b, start, end, exit_code="124"):
    b.mkdir(parents=True, exist_ok=True)
    (b / "start_utc.txt").write_text(start + "\n")
    (b / "end_utc.txt").write_text(end + "\n")
    (b / "build-exit.txt").write_text(exit_code + "\n")
    (b / "build-run.json").write_text("")


def test_agent_status_tells_a_late_timer_from_a_timeout(tmp_path, monkeypatch):
    monkeypatch.delenv("BUILD_TIMEOUT", raising=False)
    paused, normal = tmp_path / "paused", tmp_path / "normal"
    build_records(paused, "2026-10-27T03:22:03Z", "2026-10-27T14:18:42Z")      # 656 min against 300
    build_records(normal, "2026-10-27T16:32:27Z", "2026-10-27T21:32:30Z")      # 300 min: a real timeout
    line, d = agent_status.inspect(paused / "build-run.json", 124)
    assert line.startswith("error: interrupted (timer fired late") and d["paused_interrupt"] is True
    line, d = agent_status.inspect(normal / "build-run.json", 124)
    assert line == "error: agent timed out (exit 124)" and d["paused_interrupt"] is False


def test_build_paused_reader(root, monkeypatch):
    monkeypatch.delenv("BUILD_TIMEOUT", raising=False)
    b = root / "build" / "p-s2"
    build_records(b, "2026-10-27T03:22:03Z", "2026-10-27T14:18:42Z")
    assert markers.build_paused(b)
    (b / "build-exit.txt").write_text("0\n")
    assert not markers.build_paused(b)
    build_records(b, "2026-10-27T16:32:27Z", "2026-10-27T21:32:30Z")
    assert not markers.build_paused(b)                         # a genuine timeout stays stopped
    (b / "build_status.json").write_text(json.dumps({"paused_interrupt": True}))
    assert markers.build_paused(b)                             # agent_status's record decides when present
    build_records(b, "2026-10-27T03:22:03Z", "2026-10-27T14:18:42Z")
    (b / "resume_start_utc.txt").write_text("2026-10-27T14:10:00Z\n")
    (b / "build_status.json").write_text("{}")
    assert not markers.build_paused(b)                         # measured from the resumed session's start


# ---------- stage, planning and the resume job

def paused_task(root, slug, end="2026-10-27T14:18:42Z"):
    b = root / "build" / slug
    build_records(b, "2026-10-27T03:22:03Z", end)
    (b / "BUILD-PROMPT.md").write_text("build me\n")
    (b / "pipeline.log").write_text("BUILD-INCOMPLETE (agent did not finish: error: agent timed out (exit 124))\n")
    (root / "tasks" / slug).mkdir(parents=True, exist_ok=True)


def test_paused_build_is_interrupted_and_resumed_never_rebuilt(root, conn, cfg, monkeypatch):
    monkeypatch.delenv("BUILD_TIMEOUT", raising=False)
    batch(root, "scale-b9", ["cut-s2", "stk-cut-1", "timeout-s2"])
    paused_task(root, "cut-s2")
    paused_task(root, "stk-cut-1")
    paused_task(root, "timeout-s2", end="2026-10-27T08:22:30Z")                 # 300 min: a genuine timeout
    ctx = taskstate.context([])
    t = taskstate.read("cut-s2", ctx)
    assert t["stage"] == "build_interrupted" and t.get("paused_build") and t["next"].startswith("build_resume")
    assert taskstate.read("timeout-s2", ctx)["stage"] == "build_stopped"
    rep = {r["task"]: r for r in phase3.reconcile(conn, cfg, ctx)}
    assert not qdb.jobs(conn, "kind='build'")                  # never a fresh build (it would wipe tasks/<slug>)
    assert any("build_resume" in n for n in rep["cut-s2"]["notes"])
    states = events.read_all(ctx)
    kd = kinds.get("build_resume")
    out = {r["task"]: r for r in kd.plan(conn, cfg, ctx, states)}
    kd.plan(conn, cfg, ctx, states)                            # idempotent: one job per interruption
    jobs = qdb.jobs(conn, "kind='build_resume'")
    assert [(r["task"], qdb.args_of(r)) for r in jobs] == [("cut-s2", {"end": "2026-10-27T14:18:42Z"})]
    assert out["stk-cut-1"]["want"] == [] and "a person" in out["stk-cut-1"]["notes"][0]
    assert "timeout-s2" not in out


def test_running_resume_counts_as_a_build(root):
    ctx = taskstate.context([proc(41, "bash pipelines/sibling/6-build/resume_pipeline.sh cut-s2 build abc-123")])
    assert [k for k, _m, _p in ctx["running"]["cut-s2"]] == ["build"]


def test_find_session_uses_the_first_task_line(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("br", Path(kinds.__file__).parent / "build_resume.py")
    br = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(br)
    proj = tmp_path / "projects" / "-home-u-cwe"
    proj.mkdir(parents=True)
    (proj / "aaa.jsonl").write_text('{"m": "Task: `pagy-s2` ... see also Task: `nono-s2`"}\n')
    (proj / "bbb.jsonl").write_text('{"m": "Task: `nono-s2`"}\n')
    assert br.find_session("nono-s2", root=tmp_path / "projects") == "bbb"
    assert br.find_session("pagy-s2", root=tmp_path / "projects") == "aaa"
    assert br.find_session("missing-s2", root=tmp_path / "projects") is None
