"""Builder processes (common/util/build_procs.py, 2026-10-28): the orphan guard checks the launcher, not end_utc.txt
alone; a build's processes are found by the tag in their environment; the sweep never touches itself."""
import os
import signal
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "common" / "util"))
import build_procs as bp  # noqa: E402

BTIME = 1_800_000_000


def proc(root, pid, ppid, comm, cmd, env=None, start_ticks=100):
    d = root / str(pid)
    d.mkdir(parents=True)
    rest = ["S", str(ppid)] + ["0"] * 17 + [str(start_ticks)] + ["0"] * 10   # field 4 = ppid, field 22 = starttime
    (d / "stat").write_text(f"{pid} ({comm}) " + " ".join(rest) + "\n")
    (d / "cmdline").write_bytes(b"\0".join(a.encode() for a in cmd.split()) + b"\0")
    (d / "environ").write_bytes(b"\0".join(f"{k}={v}".encode() for k, v in (env or {}).items()) + b"\0")


def proc_root(tmp_path):
    r = tmp_path / "proc"
    r.mkdir()
    (r / "stat").write_text(f"cpu 0 0\nbtime {BTIME}\n")
    proc(r, 1, 0, "systemd", "/sbin/init")
    return r


TAG = {"CWE_BUILD_RUN": "ember-s2:1800000100:40", "CWE_BUILD_SLUG": "ember-s2"}


def live_build(r, tag=TAG):
    proc(r, 30, 1, "bash", "bash pipelines/sibling/6-build/run_pipeline.sh deepseek ember-s2")
    proc(r, 40, 30, "bash", "bash /rel/common/launch/run_build.sh ember-s2")
    proc(r, 41, 40, "timeout", "timeout 18000 /home/u/.local/bin/claude -p --model m", tag)
    proc(r, 42, 41, "claude", "/home/u/.local/bin/claude -p --model m --output-format json", tag)
    proc(r, 43, 42, "bash", "bash -c python3 -I common/gate/gate.py ember-s2 --only nop", tag)


def test_a_tagged_builder_under_its_launcher_is_not_an_orphan(tmp_path):
    r = proc_root(tmp_path)
    live_build(r)
    proc(r, 44, 43, "claude", "claude -p hello", TAG)          # a claude the builder started itself (plugin test)
    t = bp.read_table(r)
    assert [(b["pid"], b["slug"], b["tagged"]) for b in bp.builders(t)] == [(42, "ember-s2", True)]
    assert bp.launcher_alive(42, t)
    assert bp.orphans(t, tmp_path / "build", r) == []


def test_a_builder_whose_launcher_was_killed_is_an_orphan_and_its_whole_run_is_swept(tmp_path):
    r = proc_root(tmp_path)
    proc(r, 41, 1, "timeout", "timeout 18000 claude -p", TAG)          # run_build.sh killed: timeout re-parented
    proc(r, 42, 41, "claude", "/home/u/.local/bin/claude -p --model m", TAG)
    proc(r, 50, 1, "bun", "bun worker-service.cjs --daemon", TAG)       # a daemon of the app under test
    proc(r, 60, 1, "claude", "/home/u/.local/bin/claude -p", {"CWE_BUILD_RUN": "other-s2:1:9"})  # another run
    t = bp.read_table(r)
    o = bp.orphans(t, tmp_path / "build", r)
    assert sorted((x["pid"], x["slug"]) for x in o) == [(42, "ember-s2"), (60, "other-s2")]
    assert sorted(bp.tagged(TAG["CWE_BUILD_RUN"], t)) == [41, 42, 50]


def test_end_utc_written_by_a_live_builder_does_not_make_it_an_orphan(tmp_path):
    """spring-data-mongodb-s2 (2026-10-28): the builder wrote end_utc.txt itself; the old guard stopped it."""
    r = proc_root(tmp_path)
    b = tmp_path / "build" / "spring-s2"
    b.mkdir(parents=True)
    (b / "end_utc.txt").write_text("2030-01-01T00:00:00Z\n")           # after the process started
    proc(r, 40, 1, "bash", "bash common/launch/run_build.sh spring-s2")
    proc(r, 41, 40, "timeout", "timeout 18000 claude -p Build one security-fix benchmark task Task: `spring-s2`")
    proc(r, 42, 41, "claude", "/home/u/.local/bin/claude -p Build one security-fix benchmark task Task: `spring-s2`")
    t = bp.read_table(r)
    assert [(x["pid"], x["tagged"]) for x in bp.builders(t)] == [(42, False)]
    assert bp.orphans(t, tmp_path / "build", r) == []


def test_an_untagged_older_builder_needs_both_a_gone_launcher_and_a_recorded_end(tmp_path):
    r = proc_root(tmp_path)
    proc(r, 42, 1, "claude", "/home/u/.local/bin/claude -p Build one security-fix benchmark task Task: `old-s2`",
         start_ticks=100)                                            # started BTIME + 1 s
    t = bp.read_table(r)
    assert bp.orphans(t, tmp_path / "build", r) == []                # no end_utc.txt: left alone
    b = tmp_path / "build" / "old-s2"
    b.mkdir(parents=True)
    (b / "end_utc.txt").write_text("2027-01-16T00:00:00Z\n")         # after the process started (BTIME + 1 s)
    assert [x["pid"] for x in bp.orphans(t, tmp_path / "build", r)] == [42]
    (b / "end_utc.txt").write_text("2020-01-01T00:00:00Z\n")         # an older build's end: a rebuild, not an orphan
    assert bp.orphans(t, tmp_path / "build", r) == []


def test_an_older_resume_counts_as_a_live_launcher(tmp_path):
    r = proc_root(tmp_path)
    proc(r, 30, 1, "bash", "bash pipelines/sibling/6-build/resume_pipeline.sh cut-s2 build abc")
    proc(r, 31, 30, "bash", "bash -c . markers.sh; timeout 18000 claude -p $0 --resume abc")
    proc(r, 32, 31, "timeout", "timeout 18000 claude -p note --resume abc")
    proc(r, 33, 32, "claude", "/home/u/.local/bin/claude -p Build one security-fix benchmark task Task: `cut-s2`")
    t = bp.read_table(r)
    assert bp.launcher_alive(33, t)


def test_stop_spares_itself_and_its_ancestors_and_kills_survivors(tmp_path):
    me = os.getpid()
    table = {me: {"pid": me, "ppid": 7, "comm": "python", "argv": ["python"], "env": {}},
             7: {"pid": 7, "ppid": 1, "comm": "bash", "argv": ["bash", "run_build.sh"], "env": {}},
             50: {"pid": 50, "ppid": 1, "comm": "bun", "argv": ["bun", "x"], "env": {}},
             51: {"pid": 51, "ppid": 50, "comm": "sleep", "argv": ["sleep", "9"], "env": {}}}
    sent, alive = [], {50: True, 51: True}

    def killer(pid, sig):
        sent.append((pid, sig))
        if pid == 51:                                    # 51 exits on TERM, 50 ignores it
            alive[51] = False
        if sig == signal.SIGKILL:
            alive[pid] = False
    got = bp.stop([me, 7, 50, 51], table, grace=0.6, say=lambda *_: None, killer=killer, alive=lambda p: alive[p])
    assert got == [50, 51]
    assert (50, signal.SIGTERM) in sent and (51, signal.SIGTERM) in sent and (50, signal.SIGKILL) in sent
    assert (51, signal.SIGKILL) not in sent and all(p not in (me, 7) for p, _s in sent)
    assert bp.stop([50], table, dry_run=True, say=lambda *_: None, killer=killer) == [50]


def test_guard_cli_stops_only_confirmed_orphans(tmp_path, monkeypatch, capsys):
    r = proc_root(tmp_path)
    live_build(r)
    proc(r, 70, 1, "claude", "/home/u/.local/bin/claude -p", {"CWE_BUILD_RUN": "gone-s2:1:9", "CWE_BUILD_SLUG": "gone-s2"})
    stopped = []
    monkeypatch.setattr(bp, "stop", lambda pids, table, **kw: stopped.append(sorted(pids)) or pids)
    import paths
    monkeypatch.setattr(paths, "BUILD", tmp_path / "build")
    assert bp.main(["--proc-root", str(r), "guard", "--recheck", "0"]) == 0
    assert stopped == [[70]]
    assert "orphaned builder of gone-s2 (pid 70)" in capsys.readouterr().out


def test_leftovers_of_a_run_whose_launcher_died_are_found_by_the_token(tmp_path):
    r = proc_root(tmp_path)
    live_build(r)                                                    # launcher pid 40 is in TAG: alive
    proc(r, 80, 1, "bun", "bun worker-service.cjs --daemon", {"CWE_BUILD_RUN": "mem-s2:1:77"})   # launcher 77 gone
    proc(r, 77, 1, "python3", "python3 something-else mem-s2")       # pid 77 reused by another program
    t = bp.read_table(r)
    assert bp.stale_runs(t) == {"mem-s2:1:77": "mem-s2"}
