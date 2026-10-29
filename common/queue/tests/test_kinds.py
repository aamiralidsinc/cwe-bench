"""Job kinds as plug-ins (kinds/) and the settings history (settings.py)."""
import sqlite3
import textwrap

import config
import dispatch
import kinds
import qdb
import reconcile
import settings
from conftest import wait_for, write_config

OPEN = {"free_disk_gb": 999, "load": 1, "mem_available_gb": 999, "tmp_inode_pct": 1}

TOY = '''
"""toy: a test kind declared in its own file."""
import sys
from pathlib import Path

from kinds import Kind, enqueue, register

OUT = Path({out!r})


def plan(conn, cfg, ctx, states, dry_run=False):
    jid = enqueue(conn, cfg, "toy", "toy-task", {{"n": 1}}, dry_run=dry_run)
    want = {{"kind": "toy", "args": {{"n": 1}}}}
    if jid:
        want["id"] = jid
    return [{{"task": "toy-task", "stage": "toy", "want": [want], "notes": []}}]


def command(row, cfg):
    return [sys.executable, "-c", "import sys; open(sys.argv[1], 'w').write('made')", str(OUT / "made.txt")]


def check(task, args, t0, cfg):
    f = OUT / "made.txt"
    ok = f.is_file() and f.read_text() == "made"
    return [("toy.made", ok, "made.txt written" if ok else "made.txt missing", False)]


register(Kind(name="toy", command=command, check=check, plan=plan, priority=7, max_running=1, max_attempts=1,
              light=True, reads=(), writes=("made.txt",)))
'''


def toy_dir(tmp_path, out):
    d = tmp_path / "kinds-extra"
    d.mkdir(exist_ok=True)
    (d / "toy.py").write_text(TOY.format(out=str(out)))
    return d


def drop_toy():
    kinds.REGISTRY.pop("toy", None)
    kinds._loaded_files.clear()


def test_builtin_declarations_give_the_defaults(tmp_path, root):
    cfg = write_config(tmp_path, root)
    assert cfg["priority"]["regate"] == 50 and cfg["limits"]["max_running"]["build"] == 20
    assert cfg["retry_exit_codes"]["regate"] == [2] and cfg["ok_exit_codes"]["trial_run"] == [0, 2]
    assert cfg["env"]["trial_run"] == {"CWE_AGENT_TIMEOUT_MULT": "1.5"}
    assert cfg["limits"]["disk_floor"]["build"] == "DISK_MIN_FREE_GB_BUILD"
    assert set(cfg["dispatch"]["light_kinds"]) == {"audit_prep", "audit_record", "cleanup", "step3", "lint"}
    assert set(cfg["dispatch"]["count_foreign"]) == {"build", "trial_run", "regate", "fairness", "repair"}
    assert "gate" not in cfg["limits"]["max_running"]           # declared without a worker
    assert kinds.exclusive() == {"build", "build_resume", "gate", "regate", "regrade", "rescore", "fairness", "repair"}
    assert kinds.foreign_map() == {"build": "build", "trial": "trial_run", "regate": "regate", "fairness": "fairness",
                                   "repair": "repair"}
    assert cfg["limits"]["max_running"]["repair"] == 4 and cfg["retry_exit_codes"]["repair"] == [75]
    assert cfg["max_attempts"]["repair"] == 1
    assert cfg["repair"]["auto"] is False and cfg["limits"]["disk_floor"]["repair"] == "DISK_MIN_FREE_GB_GATE"


def test_toml_overrides_a_declared_default(tmp_path, root):
    cfg = write_config(tmp_path, root, "[limits.max_running]\nbuild = 32\n[priority]\nlint = 99\n")
    assert cfg["limits"]["max_running"]["build"] == 32 and cfg["priority"]["lint"] == 99
    assert cfg["limits"]["max_running"]["trial_run"] == 40


def test_plugin_kind_plans_starts_and_checks(tmp_path, root):
    out = tmp_path / "toy-out"
    out.mkdir()
    d = toy_dir(tmp_path, out)
    try:
        cfg = write_config(tmp_path, root, f'[kinds]\nextra_dirs = ["{d}"]\n'
                                           "[dispatch]\nstart_spacing_sec = 0\nfill_spacing_sec = 0\nlease_sec = 20\n"
                                           "[phase4]\nenabled = false\n[lint]\nenabled = false\n")
        assert "toy" in kinds.names() and cfg["priority"]["toy"] == 7 and cfg["limits"]["max_running"]["toy"] == 1
        conn = qdb.connect(cfg["db"])
        reconcile.reconcile(conn, cfg, proc_list=[])                 # the toy's plan() runs in the reconcile pass
        rows = qdb.jobs(conn, "kind='toy'")
        assert len(rows) == 1 and rows[0]["priority"] == 7 and rows[0]["origin"] == "reconciler"
        reconcile.reconcile(conn, cfg, proc_list=[])                 # idempotent: still one job
        assert len(qdb.jobs(conn, "kind='toy'")) == 1
        jid = rows[0]["id"]
        disp = dispatch.Dispatcher(conn, cfg, cfg["db"], metrics=lambda: dict(OPEN), proc_list=[])

        def settled():
            disp.tick()
            return qdb.get(conn, jid)["state"] in ("done", "failed", "blocked")
        assert wait_for(settled, 30), dict(qdb.get(conn, jid))
        row = qdb.get(conn, jid)
        assert row["state"] == "done" and row["exit_code"] == 0, dict(row)
        assert (out / "made.txt").read_text() == "made"
        chk = conn.execute("SELECT verdict FROM job_checks WHERE job_id=?", (jid,)).fetchone()
        assert chk and chk["verdict"] == "pass"
        assert row["settings_hash"] == cfg["_settings_hash"]       # the worker recorded the settings it ran under
    finally:
        drop_toy()


def test_plugin_check_failure_fails_the_job(tmp_path, root):
    out = tmp_path / "toy-out"
    out.mkdir()
    d = toy_dir(tmp_path, out)
    try:
        cfg = write_config(tmp_path, root, f'[kinds]\nextra_dirs = ["{d}"]\n[commands]\ntoy = ["true"]\n')
        conn = qdb.connect(cfg["db"])
        jid, _ = qdb.enqueue(conn, "toy", "toy-task", {"n": 2})
        assert qdb.claim(conn, jid, 60)
        import worker
        # The command ran ("true") but made.txt was never written: with the declared command the check fails ...
        import checks
        verdict, failed, _items = checks.evaluate(dict(qdb.get(conn, jid), started=qdb.utc()), dict(cfg, commands={}))
        assert verdict == "fail" and failed == "toy.made"
        # ... and a replaced command ([commands]) leaves the decision to the exit code, as for every kind.
        assert worker.run(conn, cfg, jid) == 0 and qdb.get(conn, jid)["state"] == "done"
    finally:
        drop_toy()


def test_unknown_kind_is_refused(conn):
    try:
        qdb.enqueue(conn, "no_such_kind", "t")
    except ValueError as e:
        assert "unknown kind" in str(e)
    else:
        raise AssertionError("an unregistered kind was accepted")


OLD_JOBS = """
CREATE TABLE jobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT NOT NULL CHECK (kind IN ('build', 'regate', 'regrade')),
    task          TEXT NOT NULL,
    args          TEXT NOT NULL DEFAULT '{}',
    priority      INTEGER NOT NULL DEFAULT 0,
    state         TEXT NOT NULL DEFAULT 'queued' CHECK (state IN ('queued','leased','running','done','failed','blocked')),
    attempts      INTEGER NOT NULL DEFAULT 0,
    max_attempts  INTEGER NOT NULL DEFAULT 2,
    owner_pid     INTEGER,
    lease_expires TEXT,
    depends_on    TEXT NOT NULL DEFAULT '[]',
    created       TEXT NOT NULL,
    queued_at     TEXT NOT NULL,
    started       TEXT,
    finished      TEXT,
    exit_code     INTEGER,
    result        TEXT,
    log_path      TEXT,
    origin        TEXT NOT NULL DEFAULT 'manual',
    UNIQUE (kind, task, args)
);
"""


def test_old_table_loses_the_kind_check_and_gains_settings_hash(tmp_path):
    db = tmp_path / "old.db"
    c = sqlite3.connect(db)
    c.executescript(OLD_JOBS)
    c.execute("INSERT INTO jobs (kind, task, args, state, created, queued_at, result) "
              "VALUES ('regate','t','{}','done','x','x','kept')")
    c.commit()
    c.close()
    conn = qdb.connect(db)                                           # migrates once
    row = qdb.get(conn, 1)
    assert (row["kind"], row["state"], row["result"], row["settings_hash"]) == ("regate", "done", "kept", None)
    sql = conn.execute("SELECT sql FROM sqlite_master WHERE name='jobs'").fetchone()[0]
    assert "CHECK (kind IN" not in sql
    jid, _ = qdb.enqueue(conn, "lint", "t", {"fp": "x"})             # a kind the old table did not allow
    assert jid == 2 and not qdb.migrate(conn)


def test_settings_history_records_versions(tmp_path, root):
    cfg = write_config(tmp_path, root)
    conn = qdb.connect(cfg["db"])
    h1 = settings.record(conn, cfg, "dispatch")
    assert h1 == cfg["_settings_hash"] and len(h1) == 16
    settings.record(conn, cfg, "reconcile")                          # same version: one row, two loads
    rows = settings.history(conn)
    assert len(rows) == 1 and rows[0]["loads"] == 2 and rows[0]["loaded_by"] == "reconcile"
    assert settings.refresh(conn, cfg, "dispatch") == (cfg, False)   # unchanged file
    path = cfg["_file"]
    with open(path, "a") as f:
        f.write("[priority]\nregate = 51\n")
    new, changed = settings.refresh(conn, cfg, "dispatch")
    assert changed and new["_settings_hash"] != h1 and new["priority"]["regate"] == 51 and new["db"] == cfg["db"]
    hist = settings.history(conn)
    assert [r["hash"] for r in hist][:2] == [new["_settings_hash"], h1] or {r["hash"] for r in hist} == {
        new["_settings_hash"], h1}
    assert "regate = 51" in settings.text_of(conn, new["_settings_hash"][:8])["text"]


def test_invalid_settings_file_keeps_the_settings_in_force(tmp_path, root):
    cfg = write_config(tmp_path, root)
    conn = qdb.connect(cfg["db"])
    with open(cfg["_file"], "a") as f:
        f.write("[broken\n")
    assert settings.refresh(conn, cfg, "dispatch") == (cfg, False)


def test_config_command_lists_history_and_kinds(tmp_path, root, capsys):
    import cweq
    cfg = write_config(tmp_path, root)
    conn = qdb.connect(cfg["db"])
    settings.record(conn, cfg, "dispatch")
    assert cweq.main(["--config", cfg["_file"], "config", "--kinds"]) == 0
    out = capsys.readouterr().out
    assert cfg["_settings_hash"] in out and "regate" in out and "no-worker" in out    # gate has no worker
    assert cweq.main(["--config", cfg["_file"], "config", "--show", cfg["_settings_hash"][:6]]) == 0
    assert textwrap.dedent(capsys.readouterr().out).startswith(f"# settings {cfg['_settings_hash']}")
