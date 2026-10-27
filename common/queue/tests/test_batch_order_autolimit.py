"""Batch order, batch priority and hold (taskstate.batch_meta, phase3, dispatch.batch_hold) and the total job limit
that follows sustained CPU idle time (autolimit.py)."""
import autolimit
import monitor
import qdb
from test_adopt import batch
from test_phase3 import OPEN, disp, p3, prompt


def batch_file(root, name, lines):
    batch(root, name, lines)


# ---------- batch order, priority, hold

def test_builds_queue_in_batch_file_order_with_the_batch_priority(root, conn, cfg):
    batch_file(root, "scale-b5", ["# priority: 0", "zeta-s2", "alpha-s2"])
    batch_file(root, "scale-b6", ["# priority: -2", "beta-s2"])
    for s in ("zeta-s2", "alpha-s2", "beta-s2"):
        prompt(root, s, in_batch=False)
    p3(conn, cfg)
    rows = qdb.jobs(conn, "kind='build'")
    assert [r["task"] for r in rows] == ["zeta-s2", "alpha-s2", "beta-s2"]          # file order, not alphabetical
    base = cfg["priority"]["build"]
    assert [r["priority"] for r in rows] == [base, base, base - 2]
    starts, _ = disp(conn, cfg).plan()
    assert [r["task"] for r, _ in starts] == ["zeta-s2", "alpha-s2", "beta-s2"]


def test_held_batch_builds_wait_and_resume_when_the_hold_is_lifted(root, conn, cfg):
    batch_file(root, "scale-b6", ["# hold: yes", "beta-s2"])
    prompt(root, "beta-s2", in_batch=False)
    rep = p3(conn, cfg)
    assert any("on hold" in n for n in rep["beta-s2"]["notes"])
    assert not qdb.jobs(conn, "kind='build'")                        # nothing new is queued while held
    batch_file(root, "scale-b6", ["beta-s2"])                        # lift the hold
    p3(conn, cfg)
    assert [r["task"] for r, _ in disp(conn, cfg).plan()[0]] == ["beta-s2"]
    batch_file(root, "scale-b6", ["# hold: yes", "beta-s2"])         # hold again: the queued build waits
    starts, waits = disp(conn, cfg).plan()
    assert not starts and "on hold" in waits[0][1]


def test_reconciler_build_waits_when_its_task_left_every_batch(root, conn, cfg):
    batch_file(root, "scale-b6", ["gone-s2"])
    prompt(root, "gone-s2", in_batch=False)
    p3(conn, cfg)
    batch_file(root, "scale-b6", ["other-s2"])                       # re-ranked: gone-s2 dropped
    starts, waits = disp(conn, cfg).plan()
    assert not starts and "no longer in a batch" in waits[0][1]


# ---------- total limit from sustained idle CPU

def samples(conn, now, minutes, busy):
    monitor.ensure_schema(conn)
    for i in range(minutes):
        e = now - i * 60
        conn.execute("INSERT OR REPLACE INTO metrics (ts, epoch, cpu_busy_pct) VALUES (?,?,?)",
                     (qdb.utc(e), e, busy))


def test_limit_rises_only_after_a_full_window_of_idle_cpu(conn, cfg):
    now = 1_000_000.0
    base = cfg["dispatch"]["max_running_total"]
    samples(conn, now, 30, busy=50)                                  # half an hour of idle: not enough evidence
    assert autolimit.step(conn, cfg, now=now, queued_heavy=10) == (None, "no sustained change")
    samples(conn, now, 60, busy=50)                                  # a full hour at 50% idle
    new, why = autolimit.step(conn, cfg, now=now, queued_heavy=10)
    assert new == base + 4 and "60 min" in why
    assert autolimit.effective(conn, cfg) == base + 4
    assert autolimit.step(conn, cfg, now=now + 600, queued_heavy=10)[1].startswith("cooldown")


def test_limit_does_not_rise_without_waiting_work_or_with_short_bursts(conn, cfg):
    now = 1_000_000.0
    samples(conn, now, 60, busy=50)
    assert autolimit.step(conn, cfg, now=now, queued_heavy=0)[0] is None
    for i in range(0, 60, 5):                                        # busy spikes in 12 of 60 minutes
        e = now - i * 60
        conn.execute("UPDATE metrics SET cpu_busy_pct=99 WHERE epoch=?", (e,))
    assert autolimit.step(conn, cfg, now=now, queued_heavy=10)[0] is None


def test_limit_steps_back_down_on_sustained_saturation_never_below_base(conn, cfg):
    now = 1_000_000.0
    base = cfg["dispatch"]["max_running_total"]
    autolimit.ensure(conn)
    conn.execute("INSERT INTO autolimit (ts, epoch, old, new, reason) VALUES ('t', ?, ?, ?, 'test')",
                 (now - 7200, base, base + 4))
    samples(conn, now, 30, busy=99)
    new, _ = autolimit.step(conn, cfg, now=now, queued_heavy=10)
    assert new == base
    samples(conn, now + 7200, 30, busy=99)
    assert autolimit.step(conn, cfg, now=now + 7200, queued_heavy=10)[0] is None   # already at the base


def test_dispatcher_uses_the_raised_limit(root, conn, cfg):
    cfg["dispatch"]["max_running_total"] = 1
    for s in ("a-s2", "b-s2"):
        prompt(root, s)
    p3(conn, cfg)
    assert len(disp(conn, cfg).plan()[0]) == 1
    autolimit.ensure(conn)
    conn.execute("INSERT INTO autolimit (ts, epoch, old, new, reason) VALUES ('t', 1, 1, 5, 'test')")
    assert len(disp(conn, cfg).plan()[0]) == 2
    cfg["autolimit"] = {"enabled": False}
    assert len(disp(conn, cfg).plan()[0]) == 1
