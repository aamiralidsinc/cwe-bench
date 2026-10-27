"""The total job limit follows sustained CPU idle time, never a single reading.

The settings file's [dispatch] max_running_total is the base. The monitor (one sample a minute) moves the limit in
steps between the base and [autolimit] ceiling:
  - up one step when CPU idle stayed >= raise_idle_pct for raise_window_min (at least min_share of the samples in
    the window, and the window is covered by samples), and queued work is waiting;
  - down one step (never below the base) when CPU idle stayed <= lower_idle_pct for lower_window_min.
After a change nothing moves again for cooldown_min, so each step is judged on a full window at the new level.
Lowering the limit stops nothing: it only admits fewer new jobs. Every change is a row in `autolimit` and an event.
"""
import time

import qdb

DEFAULTS = {"enabled": True, "ceiling": 85, "step": 4,
            "raise_idle_pct": 25, "raise_window_min": 60,
            "lower_idle_pct": 5, "lower_window_min": 30,
            "min_share": 0.9, "min_coverage": 0.8, "cooldown_min": 60}

SCHEMA = """
CREATE TABLE IF NOT EXISTS autolimit (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT NOT NULL,
    epoch   REAL NOT NULL,
    old     INTEGER NOT NULL,
    new     INTEGER NOT NULL,
    reason  TEXT NOT NULL
);
"""


def settings(cfg):
    return {**DEFAULTS, **(cfg.get("autolimit") or {})}


def ensure(conn):
    conn.executescript(SCHEMA)


def _last(conn):
    try:
        return conn.execute("SELECT * FROM autolimit ORDER BY id DESC LIMIT 1").fetchone()
    except Exception:                                    # no table yet
        return None


def effective(conn, cfg):
    """The total limit in force: the last automatic value, kept between the base and the ceiling."""
    base = int(cfg["dispatch"]["max_running_total"])
    s = settings(cfg)
    if not s["enabled"]:
        return base
    r = _last(conn)
    val = r["new"] if r else base
    return max(base, min(int(s["ceiling"]), int(val)))


def _idle_shares(conn, since):
    rows = conn.execute("SELECT cpu_busy_pct FROM metrics WHERE epoch >= ? AND cpu_busy_pct IS NOT NULL",
                        (since,)).fetchall()
    return [100.0 - r[0] for r in rows]


def decide(conn, cfg, now=None, queued_heavy=None):
    """(new limit, reason) when the limit should move now, else (None, why not). Pure apart from reading the DB."""
    s = settings(cfg)
    if not s["enabled"]:
        return None, "off"
    now = time.time() if now is None else now
    base, ceiling = int(cfg["dispatch"]["max_running_total"]), int(s["ceiling"])
    cur = effective(conn, cfg)
    last = _last(conn)
    if last and now - last["epoch"] < s["cooldown_min"] * 60:
        return None, f"cooldown: last change {int((now - last['epoch']) / 60)} min ago"
    if queued_heavy is None:
        light = set(cfg["dispatch"].get("light_kinds", ()))
        queued_heavy = sum(1 for r in conn.execute("SELECT kind FROM jobs WHERE state='queued'") if r[0] not in light)

    def held(window_min, ok):
        idle = _idle_shares(conn, now - window_min * 60)
        if len(idle) < s["min_coverage"] * window_min:   # one sample a minute: too few = not enough evidence
            return False, len(idle), None
        share = sum(1 for x in idle if ok(x)) / len(idle)
        return share >= s["min_share"], len(idle), round(sum(idle) / len(idle), 1)

    if cur < ceiling and queued_heavy:
        good, n, mean = held(s["raise_window_min"], lambda x: x >= s["raise_idle_pct"])
        if good:
            new = min(ceiling, cur + int(s["step"]))
            return new, (f"CPU idle >= {s['raise_idle_pct']}% for {s['raise_window_min']} min "
                         f"(mean {mean}%, {n} samples) with {queued_heavy} jobs queued")
    if cur > base:
        good, n, mean = held(s["lower_window_min"], lambda x: x <= s["lower_idle_pct"])
        if good:
            new = max(base, cur - int(s["step"]))
            return new, (f"CPU idle <= {s['lower_idle_pct']}% for {s['lower_window_min']} min "
                         f"(mean {mean}%, {n} samples)")
    return None, "no sustained change"


def step(conn, cfg, now=None, dry_run=False, queued_heavy=None):
    """Apply decide(): record the change and emit an event. Returns (new or None, reason)."""
    ensure(conn)
    old = effective(conn, cfg)
    new, why = decide(conn, cfg, now, queued_heavy)
    if new is None or new == old or dry_run:
        return (new if dry_run else None), why
    now = time.time() if now is None else now
    with qdb.tx(conn):
        conn.execute("INSERT INTO autolimit (ts, epoch, old, new, reason) VALUES (?,?,?,?,?)",
                     (qdb.utc(), now, old, new, why))
    try:
        import events
        events.ensure(conn)
        events.emit(conn, "limit.changed", f"limit.changed:{int(now)}", task="_machine",
                    payload={"old": old, "new": new, "reason": why})
    except Exception:
        pass
    return new, why
