#!/usr/bin/env python3
"""cweq: the CWE-bench work queue (phase 1: re-gate, regrade, rescore). Design: docs/WORK-QUEUE.md.

    python3 common/queue/cweq.py init                          create the database (WAL)
    python3 common/queue/cweq.py adopt [--dry-run] [--detail]  read the running pipeline's state into the queue;
                                                               the dispatcher starts nothing until this is OK
    python3 common/queue/cweq.py tasks [--stage S] [--next TEXT]   the adopted state per task
    python3 common/queue/cweq.py reconcile [--once] [--dry-run] [--task SLUG]   derive jobs from the files on disk
    python3 common/queue/cweq.py dispatch [--once] [--dry-run] start queued jobs within the limits
    python3 common/queue/cweq.py status                        counts, running jobs, blocked jobs, headroom
    python3 common/queue/cweq.py enqueue KIND TASK [--args JSON] [--priority N] [--after ID ...]
    python3 common/queue/cweq.py retry ID | block ID [--why TEXT]
    python3 common/queue/cweq.py stop ID [--grace N] [--why TEXT]   stop one job (identity-checked) and its containers
    python3 common/queue/cweq.py orphans [--json]              containers and processes with no live job (read-only)
    python3 common/queue/cweq.py monitor [--once] [--dry-run]   sample the machine every minute (monitor.py)
    python3 common/queue/cweq.py preflight                     read-only setup checks (preflight.py); exit 2 = critical
    python3 common/queue/cweq.py explain TASK                  what the rules see for a task, and all its jobs
    python3 common/queue/cweq.py verify [--kind K] [--state S]  post-condition checks of finished jobs (read-only)
    python3 common/queue/cweq.py selfcheck [--tool regrade|rescore|all] [--run]   reproduce a known grading per tool
    python3 common/queue/cweq.py events [--open] | events next | events handle ID --action TEXT   the event queue
    python3 common/queue/cweq.py inbox [--html PATH] [--json]  every decision waiting on the owner
    python3 common/queue/cweq.py delivered TASK NAME COMMIT    record a delivery after the push

Options before the command: --db PATH (default from the config), --config PATH (default common/queue/queue.toml
or $CWEQ_CONFIG). --dry-run prints what would start (or be queued) and why, and changes nothing.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adopt  # noqa: E402
import checks  # noqa: E402
import config  # noqa: E402
import monitor  # noqa: E402
import preflight  # noqa: E402
import dispatch  # noqa: E402
import identity  # noqa: E402
import procs  # noqa: E402
import qdb  # noqa: E402
import reconcile  # noqa: E402
import taskstate  # noqa: E402
import worker  # noqa: E402
from dispatch import paths  # noqa: E402


def age(ts):
    t = qdb.parse_utc(ts)
    if t is None:
        return "-"
    s = int(time.time() - t)
    return f"{s // 3600}h{s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m{s % 60:02d}s"


def short_args(row):
    a = qdb.args_of(row)
    if "trial" in a:
        a["trial"] = a["trial"].split("/")[-1]
    a.pop("why", None)
    return json.dumps(a, separators=(",", ":"))


def line(row, extra=""):
    return (f"  #{row['id']:<5} {row['kind']:<9} {row['task']:<34} {row['state']:<8} "
            f"att {row['attempts']}/{row['max_attempts']} {short_args(row)} {extra}").rstrip()


def cmd_reconcile(conn, cfg, a):
    while True:
        slugs = [a.task] if a.task else None
        rep = reconcile.reconcile(conn, cfg, slugs=slugs, dry_run=a.dry_run)
        stamp = qdb.utc()
        for t in rep:
            if not t["want"] and not t["notes"]:
                continue
            print(f"{stamp} {t['task']}: " + ("; ".join(t["notes"]) if t["notes"] else ""))
            for w in t["want"]:
                tag = f"#{w['id']}" if "id" in w else "would queue"
                dep = " (after the regate)" if w.get("after_regate") else ""
                print(f"    {tag} {w['kind']} {json.dumps({k: v for k, v in w['args'].items() if k != 'why'})}{dep}")
        if a.once or a.dry_run:
            return 0
        time.sleep(cfg["reconcile"]["tick_sec"])


def cmd_monitor(conn, cfg, a):
    from dispatch import paths as _paths
    mon = monitor.Monitor(conn, cfg, _paths.ROOT, wait_df=a.once or a.dry_run)
    while True:
        rep = mon.tick(dry_run=a.dry_run)
        print(monitor.line(rep["sample"]), flush=True)
        for name, state, value, thr, msg in rep["alerts"]:
            print(f"{rep['sample']['ts']} ALERT {state} {name}: {msg}", flush=True)
        for jid, r in rep["queued"]:
            what = "would queue" if a.dry_run else (f"queued #{jid}" if jid else "already queued")
            print(f"{rep['sample']['ts']} {what} {r['kind']} {json.dumps(r['args'])}", flush=True)
        if a.once or a.dry_run:
            return 0
        time.sleep(monitor.settings(cfg)["tick_sec"])


def cmd_preflight(conn, cfg, a):
    return preflight.report(preflight.run_all(cfg))


def cmd_dispatch(conn, cfg, a):
    if not a.dry_run and not a.skip_preflight:
        res = preflight.run_all(cfg)
        if preflight.exit_code(res) == 2:
            preflight.report(res)
            print("dispatch refused: preflight is critical (fix it, or pass --skip-preflight)")
            return 2
    if a.dry_run and a.with_reconcile:
        # Plan on a private in-memory copy: reconcile into it, then show what would start. Nothing is written.
        mem = qdb.connect(":memory:")
        conn.backup(mem)
        conn = mem
        if qdb.latest_adoption(conn) is None:            # the plan as it would be after `cweq adopt`
            rep = adopt.adopt(conn, cfg)
            print(f"{qdb.utc()} adoption (in memory): {'OK' if rep['ok'] else 'NOT OK'}, {len(rep['tasks'])} tasks, "
                  f"{len(rep['conflicts'])} conflicts")
        for t in reconcile.reconcile(conn, cfg):
            for n in t["notes"]:
                print(f"{qdb.utc()} reconcile {t['task']}: {n}")
    d = dispatch.Dispatcher(conn, cfg, a.db)
    while True:
        rep = d.tick(dry_run=a.dry_run)
        stamp = qdb.utc()
        for jid, state, why in rep["reaped"]:
            print(f"{stamp} reaped #{jid}: {why} -> {state}")
        for jid, why in rep["blocked"]:
            print(f"{stamp} blocked #{jid}: {why}")
        for r, how in rep["started"]:
            print(f"{stamp} {'WOULD START' if a.dry_run else 'started'} {line(r, how)}")
        if a.dry_run or a.verbose:
            for r, why in rep["waiting"]:
                print(f"{stamp} waits      {line(r, '- ' + why)}")
        if a.dry_run:
            by_kind, wait_kind = {}, {}
            for r, _how in rep["started"]:
                by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
            for r, why in rep["waiting"]:
                key = (r["kind"], (why or "").split(":")[0].split(" (")[0][:60])
                wait_kind[key] = wait_kind.get(key, 0) + 1
            print(f"{stamp} would start now: " + (", ".join(f"{k} {n}" for k, n in sorted(by_kind.items())) or "nothing"))
            for (k, why), n in sorted(wait_kind.items(), key=lambda kv: -kv[1]):
                print(f"{stamp} waiting: {n:>4} {k:<9} {why}")
            print(f"{stamp} headroom: {procs.headroom(str(paths.ROOT))}")
        if a.once or a.dry_run:
            return 0
        time.sleep(cfg["dispatch"]["tick_sec"])


def queue_line(conn, proc_list=None):
    """One line for the heartbeat (pipelines/router/status_report.py): per kind, the queue's running jobs (+ old-script
    work still running, drain) and queued jobs; blocked jobs need a person."""
    counts = {}
    for r in conn.execute("SELECT kind, state, COUNT(*) n FROM jobs GROUP BY kind, state"):
        counts.setdefault(r["kind"], {})[r["state"]] = r["n"]
    ctx = taskstate.context(procs.list_processes() if proc_list is None else proc_list, ignore_own=True)
    old = {}
    for runs in ctx["running"].values():
        for kind, _m, _p in runs:
            k = dispatch.FOREIGN_KIND.get(kind)
            if k:
                old[k] = old.get(k, 0) + 1
    parts = []
    for k in ("build", "trial_run", "regate", "regrade", "rescore", "fairness", "audit_prep", "audit_record",
              "cleanup", "delivery_prep"):
        c = counts.get(k, {})
        run = c.get("running", 0) + c.get("leased", 0)
        q, o = c.get("queued", 0), old.get(k, 0)
        if run or q or o:
            parts.append(f"{k} {run}{f' (+{o} old)' if o else ''} running, {q} queued")
    blocked = sum(c.get("blocked", 0) for c in counts.values())
    return "work queue: " + ("; ".join(parts) or "idle") + (f" | {blocked} blocked (a person looks)" if blocked else "")


def cmd_status(conn, cfg, a):
    rows = qdb.jobs(conn)
    counts = {}
    for r in rows:
        counts.setdefault(r["kind"], {}).setdefault(r["state"], 0)
        counts[r["kind"]][r["state"]] += 1
    print(f"queue {a.db}  (config {cfg['_file']}; {'ON' if cfg.get('enabled', True) else 'SWITCHED OFF'})")
    for k in sorted(counts):
        print(f"  {k:<10} " + "  ".join(f"{s} {n}" for s, n in sorted(counts[k].items())))
    run = [r for r in rows if r["state"] in qdb.ACTIVE]
    print(f"running ({len(run)}):")
    for r in run:
        print(line(r, f"pid {r['owner_pid']} age {age(r['started'] or r['queued_at'])} log {r['log_path'] or '-'}"))
    blk = [r for r in rows if r["state"] == "blocked"]
    print(f"blocked ({len(blk)}){' <- needs a person' if blk else ''}:")
    for r in blk:
        print(line(r, f"- {r['result']}"))
    fail = [r for r in rows if r["state"] == "failed" and not (r["result"] or "").startswith("superseded")]
    print(f"failed ({len(fail)}):")
    for r in fail[-20:]:
        print(line(r, f"exit {r['exit_code']} - {r['result']}"))
    m, lim = procs.headroom(str(paths.ROOT)), cfg["limits"]
    print("headroom:")
    print(f"  free disk {m['free_disk_gb']} GB (min {lim['min_free_disk_gb']}); load {m['load']} (max {lim['max_load']});"
          f" memory available {m['mem_available_gb']} GB (min {lim['min_mem_available_gb']});"
          f" /tmp inodes {m['tmp_inode_pct']}% (max {lim['max_tmp_inode_pct']}%)")
    over = procs.over_limits(m, lim)
    print("  admission " + ("CLOSED: " + "; ".join(over) if over else "open"))
    per_kind = {}
    for r in run:
        per_kind[r["kind"]] = per_kind.get(r["kind"], 0) + 1
    print("  slots " + ", ".join(f"{k} {per_kind.get(k, 0)}/{n}" for k, n in lim["max_running"].items())
          + f"; total {len(run)}/{cfg['dispatch']['max_running_total']}")
    return 0


def cmd_adopt(conn, cfg, a):
    rep = adopt.adopt(conn, cfg, dry_run=a.dry_run)
    adopt.report(rep, detail=a.detail)
    return 0 if rep["ok"] else 1


def cmd_tasks(conn, cfg, a):
    ad = qdb.latest_adoption(conn)
    if ad is None:
        print("no adoption recorded yet: run `cweq adopt --dry-run`, then `cweq adopt`")
        return 1
    print(f"adoption #{ad['id']} at {ad['finished']} ({'OK' if ad['ok'] else 'NOT OK'}; code {ad['code_version']})")
    where, params = "1", []
    if a.stage:
        where, params = "stage=?", [a.stage]
    for r in conn.execute(f"SELECT * FROM tasks WHERE {where} ORDER BY stage, task", params):
        if a.next and a.next not in r["next"]:
            continue
        print(f"  {r['task']:<44} {r['stage']:<20} {r['next']}")
    return 0


def cmd_enqueue(conn, cfg, a):
    args = json.loads(a.args) if a.args else {}
    why = taskstate.redo_reason(a.kind, a.task, args, taskstate.context(procs.list_processes()))
    if why:
        print(f"refused: {a.kind} {a.task} would redo finished work ({why})")
        return 1
    pri = a.priority if a.priority is not None else cfg["priority"].get(a.kind, 0)
    jid, created = qdb.enqueue(conn, a.kind, a.task, args, priority=pri,
                               max_attempts=cfg["max_attempts"].get(a.kind, 2), depends_on=a.after or ())
    print(f"#{jid} {'queued' if created else 'already in the queue (unchanged)'}")
    return 0


def cmd_retry(conn, cfg, a):
    ids = qdb.retry(conn, a.id)
    print(f"re-queued: {', '.join('#' + str(i) for i in ids)}" if ids else f"#{a.id}: not found or still running")
    return 0 if ids else 1


def cmd_block(conn, cfg, a):
    row = qdb.get(conn, a.id)
    if row is None:
        print(f"#{a.id}: not found")
        return 1
    qdb.set_state(conn, a.id, "blocked", a.why or "blocked by hand")
    note = " (its worker stops at its next lease refresh)" if row["state"] in qdb.ACTIVE else ""
    print(f"#{a.id} blocked{note}")
    return 0


def cmd_events(conn, cfg, a):
    import events
    if a.op == "next":
        r = events.next_open(conn)
        if r is None:
            print("no open events")
            return 1
        print(events.line(r))
        print(json.dumps(json.loads(r["payload"]), indent=2))
        return 0
    if a.op == "handle":
        if a.id is None or not a.action:
            print("usage: cweq events handle ID --action TEXT")
            return 2
        ok = events.handle(conn, a.id, a.action)
        print(f"#{a.id} handled" if ok else f"#{a.id}: not an open event")
        return 0 if ok else 1
    rows = events.listing(conn, open_only=a.open, limit=a.limit)
    n_open = sum(1 for r in rows if r["state"] == "open")
    print(f"events ({len(rows)} shown, {n_open} open; oldest first, urgent ones are handled first):")
    for r in rows:
        print(events.line(r))
    return 0


def cmd_inbox(conn, cfg, a):
    import delivery
    import events
    import inbox
    states = events.read_all(taskstate.context(procs.list_processes()))
    items = inbox.collect(conn, states, delivery.prepared())
    if a.html:
        Path(a.html).write_text(inbox.page(items))
        print(f"wrote {a.html} ({sum(len(v) for v in items.values())} items)")
    if a.json:
        print(inbox.as_json(items))
    elif not a.html:
        print(inbox.text(items), end="")
    return 0


def cmd_delivered(conn, cfg, a):
    import delivery
    added, wrote = delivery.record_delivered(a.task, a.name, a.commit, a.date, a.note,
                                             delivery.settings(cfg)["repo_label"])
    print(f"register: {', '.join(added) if added else 'already listed'}; "
          f"HUMAN-DECISION.md: {'DELIVERED line added' if wrote else 'already has this commit'}")
def cmd_stop(conn, cfg, a):
    for line in identity.stop(conn, a.id, grace=a.grace, why=a.why or "stopped by cweq stop"):
        print(line)
    return 0


def cmd_orphans(conn, cfg, a):
    res = identity.orphans(conn)
    if a.json:
        print(json.dumps(res, indent=1))
        return 0
    print(f"containers whose job is no longer running ({len(res['containers_job_ended'])}):")
    for c in res["containers_job_ended"]:
        print(f"  {c['id']} {c['name']:<60} {c['state']:<8} job #{c['labels'].get('cwe.job_id')} {c['job_state']}")
    print(f"pipeline containers with no cwe labels ({len(res['containers_unlabelled'])}):")
    for c in res["containers_unlabelled"]:
        print(f"  {c['id']} {c['name']:<60} {c['state']:<8} {c['status']}")
    print(f"processes whose job is no longer running ({len(res['processes_job_ended'])}):")
    for p in res["processes_job_ended"]:
        print(f"  pid {p['pid']} job #{p['job_id']} {p['job_state']} {p['cmd']}")
    return 0


def cmd_explain(conn, cfg, a):
    t = reconcile.analyse(a.task, cfg, procs.busy_tasks([a.task], cfg["busy"]["patterns"],
                                                        skip_dirs=(paths.COMMON,)))
    print(f"{a.task}")
    for k in ("repairs", "markers", "fp", "fp16", "last_result", "held"):
        if k in t:
            print(f"  {k:<12} {t[k]}")
    import lintstep
    if lintstep.line(a.task):
        print(f"  lint         {lintstep.line(a.task)}")
    for n in t["notes"]:
        print(f"  note         {n}")
    for w in t["want"]:
        print(f"  rules want   {w['kind']} {json.dumps({k: v for k, v in w['args'].items() if k != 'why'})}"
              f"{' (after the regate)' if w.get('after_regate') else ''}")
    rows = qdb.jobs(conn, "task=?", (a.task,))
    print(f"  jobs ({len(rows)}):")
    for r in rows:
        print(line(r, f"{r['origin']} created {r['created']} exit {r['exit_code']} - {r['result'] or ''}"))
    return 0


def cmd_verify(conn, cfg, a):
    where, params = "state=?", [a.state]
    if a.kind:
        where, params = where + " AND kind=?", params + [a.kind]
    print(f"post-condition checks of {a.state} jobs (nothing is changed):")
    _counts, bad = checks.verify_past(conn, cfg, where, tuple(params))
    return 1 if bad else 0


def cmd_selfcheck(conn, cfg, a):
    tools = list(checks.TOOLS) if a.tool == "all" else [a.tool]
    rc = 0
    for t in tools:
        sid = checks.selfcheck(conn, cfg, t, run=a.run)
        row = conn.execute("SELECT ok FROM selfchecks WHERE id=?", (sid,)).fetchone()
        rc = rc or (1 if a.run and row and row["ok"] == 0 else 0)
    if not a.run:
        print("dry run: nothing was graded (add --run to reproduce; it costs one grading per tool)")
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cweq", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db")
    ap.add_argument("--config")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("adopt")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--detail", action="store_true", help="every task's stage and next step, every difference")
    p = sub.add_parser("tasks")
    p.add_argument("--stage", choices=taskstate.STAGES)
    p.add_argument("--next", help="only tasks whose next step contains this text")
    p = sub.add_parser("reconcile")
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--task")
    p = sub.add_parser("dispatch")
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true", help="also list waiting jobs and why")
    p.add_argument("--skip-preflight", action="store_true", help="start even when a preflight check is critical")
    p.add_argument("--with-reconcile", action="store_true",
                   help="with --dry-run: first reconcile into an in-memory copy of the queue (what would happen now)")
    sub.add_parser("status")
    p = sub.add_parser("monitor")
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="one sample, printed; nothing written or queued")
    sub.add_parser("preflight")
    p = sub.add_parser("enqueue")
    p.add_argument("kind", choices=qdb.KINDS)
    p.add_argument("task")
    p.add_argument("--args", help="JSON object, e.g. '{\"trial\": \"<job>/<trial>\", \"why\": \"...\"}'")
    p.add_argument("--priority", type=int)
    p.add_argument("--after", type=int, action="append", help="job id this one waits for (repeatable)")
    p = sub.add_parser("retry")
    p.add_argument("id", type=int)
    p = sub.add_parser("block")
    p.add_argument("id", type=int)
    p.add_argument("--why")
    p = sub.add_parser("stop", help="stop one job: its process group (identity verified) and its containers")
    p.add_argument("id", type=int)
    p.add_argument("--grace", type=int, default=30)
    p.add_argument("--why")
    p = sub.add_parser("orphans", help="containers and processes with no live job (read-only)")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("explain")
    p.add_argument("task")
    p = sub.add_parser("verify")
    p.add_argument("--kind", choices=qdb.KINDS)
    p.add_argument("--state", default="done", choices=qdb.STATES)
    p = sub.add_parser("selfcheck")
    p.add_argument("--tool", default="all", choices=["all", *checks.TOOLS])
    p.add_argument("--run", action="store_true", help="really reproduce (one grading per tool); default is a dry run")
    p = sub.add_parser("events", help="the event queue: list, next, handle")
    p.add_argument("op", nargs="?", choices=("list", "next", "handle"), default="list")
    p.add_argument("id", nargs="?", type=int)
    p.add_argument("--open", action="store_true", help="only open events")
    p.add_argument("--limit", type=int)
    p.add_argument("--action", help="with handle: what was done")
    p = sub.add_parser("inbox", help="every decision waiting on the owner")
    p.add_argument("--html", help="write one self-contained HTML page here")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("delivered", help="record a delivery after the push (register + DELIVERED line)")
    p.add_argument("task")
    p.add_argument("name")
    p.add_argument("commit")
    p.add_argument("--date")
    p.add_argument("--note", default="")
    p = sub.add_parser("_work")                          # internal: the worker wrapper
    p.add_argument("id", type=int)
    a = ap.parse_args(argv)
    cfg = config.load(a.config)
    a.db = a.db or cfg["db"]
    # Looking never creates the database: a dry run, status or explain on a missing file uses an empty one in memory.
    looking = getattr(a, "dry_run", False) or a.cmd in ("orphans", "status", "explain", "tasks", "verify", "inbox",
                                                         "preflight")
    conn = qdb.connect(":memory:" if looking and not Path(a.db).exists() else a.db)
    if a.cmd == "init":
        print(f"queue database ready: {a.db}")
        return 0
    if a.cmd == "_work":
        return worker.run(conn, cfg, a.id)
    return {"adopt": cmd_adopt, "tasks": cmd_tasks, "reconcile": cmd_reconcile, "dispatch": cmd_dispatch, "status": cmd_status, "enqueue": cmd_enqueue,
            "retry": cmd_retry, "block": cmd_block, "explain": cmd_explain, "verify": cmd_verify,
            "selfcheck": cmd_selfcheck, "events": cmd_events, "inbox": cmd_inbox,
            "delivered": cmd_delivered, "stop": cmd_stop, "orphans": cmd_orphans, "monitor": cmd_monitor,
            "preflight": cmd_preflight}[a.cmd](conn, cfg, a)


if __name__ == "__main__":
    sys.exit(main())
