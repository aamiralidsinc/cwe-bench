"""The job table: one SQLite file (WAL mode). It records work in flight only; the artifacts on disk stay the truth.

A job is (kind, task, args). args is canonical JSON (sorted keys, no spaces), and (kind, task, args) is UNIQUE, so the
same job can never be queued twice: enqueue() of an existing key returns the existing row and changes nothing.

States: queued -> leased (claimed by the dispatcher) -> running (the worker started) -> done | failed;
blocked = needs a person (too many attempts, or a dependency failed). `cweq retry <id>` puts a job back in the queue.
"""
import json
import sqlite3
import time
from datetime import datetime, timezone

KINDS = ("build", "gate", "regate", "trial_run", "regrade", "rescore", "audit_prep", "audit_record", "fairness",
         "cleanup", "step3", "delivery_prep")
STATES = ("queued", "leased", "running", "done", "failed", "blocked")
ACTIVE = ("leased", "running")

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS jobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT NOT NULL CHECK (kind IN {KINDS}),
    task          TEXT NOT NULL,                 -- the slug (build/<slug>, tasks/<slug>)
    args          TEXT NOT NULL DEFAULT '{{}}',   -- canonical JSON; part of the unique key
    priority      INTEGER NOT NULL DEFAULT 0,    -- higher starts first; waiting time adds to it (aging)
    state         TEXT NOT NULL DEFAULT 'queued' CHECK (state IN {STATES}),
    attempts      INTEGER NOT NULL DEFAULT 0,    -- starts so far
    max_attempts  INTEGER NOT NULL DEFAULT 2,
    owner_pid     INTEGER,                       -- the worker wrapper (its own session: pgid = pid)
    lease_expires TEXT,                          -- UTC; the worker refreshes it while the job runs
    depends_on    TEXT NOT NULL DEFAULT '[]',    -- JSON list of job ids that must be done first
    created       TEXT NOT NULL,                 -- UTC
    queued_at     TEXT NOT NULL,                 -- UTC of the last (re)queue; aging counts from here
    started       TEXT,
    finished      TEXT,
    exit_code     INTEGER,
    result        TEXT,                          -- short text: last log line, or why blocked/skipped
    log_path      TEXT,
    origin        TEXT NOT NULL DEFAULT 'manual', -- reconciler | manual
    UNIQUE (kind, task, args)
);
CREATE INDEX IF NOT EXISTS jobs_state ON jobs (state);
CREATE INDEX IF NOT EXISTS jobs_task ON jobs (task);

-- Adoption (adopt.py): the queue's picture of the running pipeline, imported from disk before it dispatches.
CREATE TABLE IF NOT EXISTS adoptions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    started       TEXT NOT NULL,
    finished      TEXT,
    code_version  TEXT,                          -- git commit of the queue code that read the state
    tasks         INTEGER,
    counts        TEXT,                          -- JSON {{stage: n}}
    conflicts     TEXT,                          -- JSON list: readings that would make the queue redo work
    differences   TEXT,                          -- JSON list: ledger vs launch-state differences (information)
    ok            INTEGER NOT NULL DEFAULT 0     -- 1 = no conflicts: the dispatcher may start work
);
CREATE TABLE IF NOT EXISTS tasks (
    task          TEXT PRIMARY KEY,
    adoption_id   INTEGER NOT NULL,
    batch         TEXT,
    pipeline      TEXT,
    stage         TEXT NOT NULL,
    next          TEXT NOT NULL,
    facts         TEXT NOT NULL,                 -- JSON: markers, per-model states, verdicts, running processes
    read_at       TEXT NOT NULL
);
"""


def utc(ts=None):
    """UTC timestamp string, second precision, sortable as text."""
    return datetime.fromtimestamp(time.time() if ts is None else ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc(s):
    """Epoch seconds from utc() or any ISO time; None when empty or unreadable."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def canon(args):
    return json.dumps(args or {}, sort_keys=True, separators=(",", ":"))


def connect(path):
    """Open (and create) the database. Autocommit; write transactions use BEGIN IMMEDIATE (see tx())."""
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.executescript(SCHEMA)
    migrate(conn)
    return conn


def migrate(conn):
    """Bring an older jobs table up to the current kind list. SQLite cannot change a CHECK constraint, so the table
    is rebuilt in one transaction (ids, the AUTOINCREMENT sequence and every row are kept). Run with the queue loops
    stopped (deploy step); a no-op when the table already accepts every kind."""
    row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jobs'").fetchone()
    if row is None or all(f"'{k}'" in row[0] for k in KINDS):
        return False
    ddl = SCHEMA.split("CREATE TABLE IF NOT EXISTS jobs", 1)[1].split(");", 1)[0] + ");"
    with tx(conn):
        conn.execute("CREATE TABLE jobs_new" + ddl)
        conn.execute("INSERT INTO jobs_new SELECT * FROM jobs")
        conn.execute("DROP TABLE jobs")
        conn.execute("ALTER TABLE jobs_new RENAME TO jobs")
        conn.execute("CREATE INDEX IF NOT EXISTS jobs_state ON jobs (state)")
        conn.execute("CREATE INDEX IF NOT EXISTS jobs_task ON jobs (task)")
    return True


class tx:
    """with tx(conn): ...  -- one write transaction (BEGIN IMMEDIATE takes the write lock up front)."""
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        self.conn.execute("BEGIN IMMEDIATE")
        return self.conn

    def __exit__(self, et, ev, tb):
        self.conn.execute("COMMIT" if et is None else "ROLLBACK")
        return False


def enqueue(conn, kind, task, args=None, priority=0, max_attempts=2, depends_on=(), origin="manual"):
    """Add a job unless the same (kind, task, args) exists. Returns (id, created)."""
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; one of {', '.join(KINDS)}")
    a, now = canon(args), utc()
    with tx(conn):
        row = conn.execute("SELECT id FROM jobs WHERE kind=? AND task=? AND args=?", (kind, task, a)).fetchone()
        if row:
            return row["id"], False
        cur = conn.execute(
            "INSERT INTO jobs (kind, task, args, priority, max_attempts, depends_on, created, queued_at, origin)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (kind, task, a, int(priority), int(max_attempts), json.dumps(sorted(set(depends_on))), now, now, origin))
    return cur.lastrowid, True


def get(conn, job_id):
    return conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()


def jobs(conn, where="1", params=()):
    return conn.execute(f"SELECT * FROM jobs WHERE {where} ORDER BY id", params).fetchall()


def args_of(row):
    return json.loads(row["args"] or "{}")


def deps_of(row):
    return json.loads(row["depends_on"] or "[]")


def claim(conn, job_id, lease_sec):
    """queued -> leased, atomically. False when another dispatcher got there first."""
    with tx(conn):
        cur = conn.execute("UPDATE jobs SET state='leased', attempts=attempts+1, owner_pid=NULL, lease_expires=?,"
                           " started=NULL, finished=NULL, exit_code=NULL, result=NULL WHERE id=? AND state='queued'",
                           (utc(time.time() + lease_sec), job_id))
        return cur.rowcount == 1


def set_owner(conn, job_id, pid):
    conn.execute("UPDATE jobs SET owner_pid=? WHERE id=? AND state='leased'", (pid, job_id))


def start(conn, job_id, pid, lease_sec, log_path):
    """leased -> running, by the worker itself. False if the job is no longer leased (requeued meanwhile)."""
    with tx(conn):
        cur = conn.execute("UPDATE jobs SET state='running', owner_pid=?, started=?, lease_expires=?, log_path=?"
                           " WHERE id=? AND state='leased'", (pid, utc(), utc(time.time() + lease_sec), log_path, job_id))
        return cur.rowcount == 1


def refresh(conn, job_id, pid, lease_sec):
    """Extend the lease. False when the job is no longer ours (the dispatcher declared us stale)."""
    cur = conn.execute("UPDATE jobs SET lease_expires=? WHERE id=? AND owner_pid=? AND state='running'",
                       (utc(time.time() + lease_sec), job_id, pid))
    return cur.rowcount == 1


def finish(conn, job_id, pid, exit_code, result, retry_codes=(), ok_codes=(0,)):
    """Record a worker's end. Exit 0 -> done; a retryable exit -> queued again (or blocked at max_attempts);
    anything else -> failed. Returns the new state, or None when the job was no longer ours."""
    with tx(conn):
        row = conn.execute("SELECT * FROM jobs WHERE id=? AND owner_pid=? AND state='running'", (job_id, pid)).fetchone()
        if row is None:
            return None
        if exit_code in ok_codes:
            state = "done"
        elif exit_code in retry_codes:
            state = "queued" if row["attempts"] < row["max_attempts"] else "blocked"
        else:
            state = "failed"
        conn.execute("UPDATE jobs SET state=?, exit_code=?, result=?, finished=?, owner_pid=NULL, lease_expires=NULL,"
                     " queued_at=CASE WHEN ?='queued' THEN ? ELSE queued_at END WHERE id=?",
                     (state, exit_code, (result or "")[:300], utc(), state, utc(), job_id))
        return state


def requeue_or_block(conn, job_id, why):
    """A stale job: back to the queue (attempts already counted at claim), or blocked when attempts are used up."""
    with tx(conn):
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None or row["state"] not in ACTIVE:
            return None
        state = "queued" if row["attempts"] < row["max_attempts"] else "blocked"
        conn.execute("UPDATE jobs SET state=?, owner_pid=NULL, lease_expires=NULL, result=?, finished=?,"
                     " queued_at=CASE WHEN ?='queued' THEN ? ELSE queued_at END WHERE id=?",
                     (state, why[:300], utc() if state == "blocked" else None, state, utc(), job_id))
        return state


def set_state(conn, job_id, state, result=None):
    """Manual or bookkeeping change (block, superseded, dependency failed)."""
    if state not in STATES:
        raise ValueError(state)
    conn.execute("UPDATE jobs SET state=?, result=?, owner_pid=NULL, lease_expires=NULL,"
                 " finished=CASE WHEN ? IN ('done','failed','blocked') THEN ? ELSE finished END WHERE id=?",
                 (state, (result or "")[:300], state, utc(), job_id))


def retry(conn, job_id):
    """Put a failed/blocked/done job back in the queue with fresh attempts; also re-open jobs blocked only because
    this one failed. Returns the ids re-queued."""
    out = []
    with tx(conn):
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None or row["state"] in ACTIVE:
            return out
        todo = [job_id] + [r["id"] for r in conn.execute(
            "SELECT id FROM jobs WHERE state='blocked' AND result LIKE ?", (f"dependency #{job_id} %",))]
        for i in todo:
            conn.execute("UPDATE jobs SET state='queued', attempts=0, owner_pid=NULL, lease_expires=NULL, started=NULL,"
                         " finished=NULL, exit_code=NULL, result='retry by hand', queued_at=? WHERE id=?", (utc(), i))
            out.append(i)
    return out


def latest_adoption(conn):
    return conn.execute("SELECT * FROM adoptions WHERE finished IS NOT NULL ORDER BY id DESC LIMIT 1").fetchone()
