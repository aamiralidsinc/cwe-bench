"""The event queue: what happened, in order, for the orchestrator to handle one at a time.

Every reconcile pass calls sync(), which turns changes on disk and in the job table into rows of the `events` table:

  job.done / job.failed / job.blocked   a job ended (done only for the kinds in [events] job_done_kinds)
  stage.<stage>                         a task reached a new stage (taskstate.STAGES; only the stages in
                                        [events] stages emit; every stage is remembered)
  breaker.candidate                     the audited ledger now calls the task a BREAKER candidate
  audit.ready                           an evidence folder is waiting for its auditor (audit_ready.txt)
  adoption.conflict                     the latest adoption has a conflict (the dispatcher stays closed)
  disk.critical                         free disk fell below [events] disk_critical_gb

Each event has a dedup key; inserting an existing key does nothing, so the same transition never emits twice, even
after a restart. Remembered values (a task's stage, the ledger verdict, the disk state) live in the `marks` table. On
the very first pass the marks are recorded silently (a baseline), so deploying the queue does not flood the table
with the whole history.

Handling (`cweq events ...`): `next` gives the oldest open event, urgent kinds first ([events] urgent); `handle ID
--action TEXT` closes it with the action taken. Events are worked strictly in that order.
"""
import json
import time
from pathlib import Path

import qdb
import taskstate
from taskstate import paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    task        TEXT NOT NULL DEFAULT '',
    payload     TEXT NOT NULL DEFAULT '{}',
    dedup       TEXT NOT NULL UNIQUE,
    urgent      INTEGER NOT NULL DEFAULT 0,
    created     TEXT NOT NULL,
    state       TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open', 'handled')),
    handled_at  TEXT,
    action      TEXT
);
CREATE INDEX IF NOT EXISTS events_state ON events (state, urgent, id);
CREATE TABLE IF NOT EXISTS marks (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    since       TEXT NOT NULL
);
"""

DEFAULTS = {
    "job_done_kinds": ["build", "regate", "regrade", "rescore", "fairness", "delivery_prep"],
    "stages": ["awaiting_audit", "awaiting_fairness", "fairness_not_ready", "awaiting_decision", "kept", "delivered",
               "trials_stuck", "listing_fail", "gate_failed", "build_stopped", "not_breaker", "stale_gate"],
    "urgent": ["disk.critical", "adoption.conflict", "process.frozen"],
    "disk_critical_gb": 130,
}


def settings(cfg):
    out = dict(DEFAULTS)
    out.update((cfg or {}).get("events", {}))
    return out


def ensure(conn):
    conn.executescript(SCHEMA)


def emit(conn, kind, dedup, task="", payload=None, urgent=False):
    """Insert one event unless its dedup key exists. Returns the new id, or None."""
    cur = conn.execute("INSERT OR IGNORE INTO events (kind, task, payload, dedup, urgent, created) VALUES (?,?,?,?,?,?)",
                       (kind, task, json.dumps(payload or {}, sort_keys=True), dedup, int(urgent), qdb.utc()))
    return cur.lastrowid if cur.rowcount == 1 else None


def mark(conn, key):
    row = conn.execute("SELECT value FROM marks WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_mark(conn, key, value):
    conn.execute("INSERT INTO marks (key, value, since) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,"
                 " since=excluded.since", (key, value, qdb.utc()))


def read_all(ctx):
    """{slug: taskstate.read(...)} for every task the pipeline knows (shared by events, delivery and the inbox)."""
    out = {}
    for s in taskstate.slugs(ctx):
        try:
            out[s] = taskstate.read(s, ctx)
        except Exception:                              # one unreadable task must not stop the others
            continue
    return out


def free_gb():
    import shutil
    return shutil.disk_usage(str(paths.ROOT)).free / (1 << 30)


def plan(conn, cfg, ctx, states, ready=None, disk_gb=None):
    """The events this pass would emit, and the marks it would set: ([event dict], {key: value}, baseline)."""
    st = settings(cfg)
    urgent = set(st["urgent"])
    ev, marks = [], {}
    baseline = conn.execute("SELECT COUNT(*) FROM marks").fetchone()[0] == 0
    since = mark(conn, "events_since")
    if since is None:
        since = qdb.utc()
        marks["events_since"] = since                  # jobs that ended before the first pass are history

    def add(kind, dedup, task="", payload=None):
        ev.append({"kind": kind, "dedup": dedup, "task": task, "payload": payload or {}, "urgent": kind in urgent})

    # Jobs that ended. The dedup key carries the finish time, so a retried job that ends again emits again.
    done_kinds = set(st["job_done_kinds"])
    for r in conn.execute("SELECT * FROM jobs WHERE state IN ('done','failed','blocked') AND finished >= ?", (since,)):
        if r["state"] == "done" and r["kind"] not in done_kinds:
            continue
        if r["state"] == "done" and (r["result"] or "").startswith(("superseded", "not needed")):
            continue                                   # bookkeeping closes, not work that ran
        add(f"job.{r['state']}", f"job:{r['id']}:{r['state']}:{r['finished']}", r["task"],
            {"job_id": r["id"], "kind": r["kind"], "exit_code": r["exit_code"], "result": r["result"]})

    # Stage transitions and ledger verdicts (silent on the baseline pass).
    show = set(st["stages"])
    for slug, t in sorted(states.items()):
        key, old = f"stage:{slug}", mark(conn, f"stage:{slug}")
        if old != t["stage"]:
            marks[key] = t["stage"]
            if old is not None and t["stage"] in show:
                add(f"stage.{t['stage']}", f"stage:{slug}:{old}->{t['stage']}:{qdb.utc()}", slug,
                    {"from": old, "to": t["stage"], "next": t["next"], "fairness": t.get("fairness", "")})
        verdict = "BREAKER" if "BREAKER" in t.get("ledger_verdict", "") else (t.get("ledger_verdict") or "-")
        vkey, vold = f"verdict:{slug}", mark(conn, f"verdict:{slug}")
        if vold != verdict:
            marks[vkey] = verdict
            if vold is not None and verdict == "BREAKER" and not baseline:
                add("breaker.candidate", f"breaker:{slug}:{qdb.utc()}", slug,
                    {"deepseek": t["models"].get("deepseek", {}).get("ledger"),
                     "mimo": t["models"].get("mimo", {}).get("ledger")})

    # Evidence folders waiting for an auditor (one event per folder, ever).
    if ready is None:
        f = paths.ROOT / "pipelines" / "router" / "out" / "queue" / "audit_ready.txt"
        try:
            ready = [l.strip() for l in f.read_text().splitlines() if l.strip()]
        except OSError:
            ready = []
    for folder in ready:
        trial = Path(folder).parent.name
        add("audit.ready", f"audit:{folder}", trial.split("__")[0], {"folder": folder, "trial": trial})

    # Conflicts of the latest adoption (each distinct conflict once).
    ad = qdb.latest_adoption(conn)
    if ad is not None and not ad["ok"]:
        for c in json.loads(ad["conflicts"] or "[]"):
            add("adoption.conflict", f"conflict:{c}", c.split(":")[0], {"adoption": ad["id"], "conflict": c})

    # Disk: an event when free disk falls below the critical level (again only after it recovered).
    gb = free_gb() if disk_gb is None else disk_gb
    state = "critical" if gb < st["disk_critical_gb"] else "ok"
    if mark(conn, "disk") != state:
        marks["disk"] = state
        if state == "critical":
            add("disk.critical", f"disk:{qdb.utc()}", "_machine", {"free_gb": round(gb, 1),
                                                                  "critical_below_gb": st["disk_critical_gb"]})
    return ev, marks, baseline


def sync(conn, cfg, ctx, states=None, dry_run=False, ready=None, disk_gb=None):
    """One pass: emit what changed. Returns the events emitted (or, in a dry run, the ones that would be)."""
    ensure(conn)
    states = read_all(ctx) if states is None else states
    if dry_run:
        return plan(conn, cfg, ctx, states, ready, disk_gb)[0]
    out = []
    with qdb.tx(conn):
        ev, marks, _baseline = plan(conn, cfg, ctx, states, ready, disk_gb)
        for e in ev:
            if emit(conn, e["kind"], e["dedup"], e["task"], e["payload"], e["urgent"]):
                out.append(e)
        for k, v in marks.items():
            set_mark(conn, k, v)
    return out


def listing(conn, open_only=False, limit=None):
    ensure(conn)
    q = "SELECT * FROM events" + (" WHERE state='open'" if open_only else "") + " ORDER BY id"
    rows = conn.execute(q).fetchall()
    return rows[-limit:] if limit else rows


def next_open(conn):
    """The event to handle now: the oldest open urgent one, else the oldest open one."""
    ensure(conn)
    return conn.execute("SELECT * FROM events WHERE state='open' ORDER BY urgent DESC, id LIMIT 1").fetchone()


def handle(conn, event_id, action):
    """Close one open event with the action taken. False when it is not open."""
    ensure(conn)
    cur = conn.execute("UPDATE events SET state='handled', handled_at=?, action=? WHERE id=? AND state='open'",
                       (qdb.utc(), (action or "")[:500], event_id))
    return cur.rowcount == 1


def line(r):
    p = json.loads(r["payload"] or "{}")
    bits = {"job.done": "kind exit_code", "job.failed": "kind exit_code result", "job.blocked": "kind result",
            "audit.ready": "trial", "adoption.conflict": "conflict", "disk.critical": "free_gb"}
    keys = bits.get(r["kind"], "from to next")
    detail = " ".join(f"{k}={p[k]}" for k in keys.split() if p.get(k) not in (None, ""))
    flag = "URGENT " if r["urgent"] else ""
    tail = f" -> {r['action']}" if r["state"] == "handled" else ""
    return f"  #{r['id']:<5} {r['created']} {r['state']:<7} {flag}{r['kind']:<20} {r['task']:<40} {detail[:160]}{tail}"
