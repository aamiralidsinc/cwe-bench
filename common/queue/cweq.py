#!/usr/bin/env python3
"""cweq: the CWE-bench work queue (phase 1: re-gate, regrade, rescore). Design: docs/WORK-QUEUE.md.

    python3 common/queue/cweq.py init                          create the database (WAL)
    python3 common/queue/cweq.py reconcile [--once] [--dry-run] [--task SLUG]   derive jobs from the files on disk
    python3 common/queue/cweq.py dispatch [--once] [--dry-run] start queued jobs within the limits
    python3 common/queue/cweq.py status                        counts, running jobs, blocked jobs, headroom
    python3 common/queue/cweq.py enqueue KIND TASK [--args JSON] [--priority N] [--after ID ...]
    python3 common/queue/cweq.py retry ID | block ID [--why TEXT]
    python3 common/queue/cweq.py explain TASK                  what the rules see for a task, and all its jobs

Options before the command: --db PATH (default from the config), --config PATH (default common/queue/queue.toml
or $CWEQ_CONFIG). --dry-run prints what would start (or be queued) and why, and changes nothing.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import dispatch  # noqa: E402
import procs  # noqa: E402
import qdb  # noqa: E402
import reconcile  # noqa: E402
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


def cmd_dispatch(conn, cfg, a):
    if a.dry_run and a.with_reconcile:
        # Plan on a private in-memory copy: reconcile into it, then show what would start. Nothing is written.
        mem = qdb.connect(":memory:")
        conn.backup(mem)
        conn = mem
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
            print(f"{stamp} headroom: {procs.headroom(str(paths.ROOT))}")
        if a.once or a.dry_run:
            return 0
        time.sleep(cfg["dispatch"]["tick_sec"])


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


def cmd_enqueue(conn, cfg, a):
    args = json.loads(a.args) if a.args else {}
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


def cmd_explain(conn, cfg, a):
    t = reconcile.analyse(a.task, cfg, procs.busy_tasks([a.task], cfg["busy"]["patterns"],
                                                        skip_dirs=(paths.COMMON,)))
    print(f"{a.task}")
    for k in ("repairs", "markers", "fp", "fp16", "last_result", "held"):
        if k in t:
            print(f"  {k:<12} {t[k]}")
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


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cweq", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db")
    ap.add_argument("--config")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("reconcile")
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--task")
    p = sub.add_parser("dispatch")
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true", help="also list waiting jobs and why")
    p.add_argument("--with-reconcile", action="store_true",
                   help="with --dry-run: first reconcile into an in-memory copy of the queue (what would happen now)")
    sub.add_parser("status")
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
    p = sub.add_parser("explain")
    p.add_argument("task")
    p = sub.add_parser("_work")                          # internal: the worker wrapper
    p.add_argument("id", type=int)
    a = ap.parse_args(argv)
    cfg = config.load(a.config)
    a.db = a.db or cfg["db"]
    # Looking never creates the database: a dry run, status or explain on a missing file uses an empty one in memory.
    looking = getattr(a, "dry_run", False) or a.cmd in ("status", "explain")
    conn = qdb.connect(":memory:" if looking and not Path(a.db).exists() else a.db)
    if a.cmd == "init":
        print(f"queue database ready: {a.db}")
        return 0
    if a.cmd == "_work":
        return worker.run(conn, cfg, a.id)
    return {"reconcile": cmd_reconcile, "dispatch": cmd_dispatch, "status": cmd_status, "enqueue": cmd_enqueue,
            "retry": cmd_retry, "block": cmd_block, "explain": cmd_explain}[a.cmd](conn, cfg, a)


if __name__ == "__main__":
    sys.exit(main())
