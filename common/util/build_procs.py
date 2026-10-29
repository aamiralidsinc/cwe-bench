#!/usr/bin/env python3
"""Builder processes: who belongs to which build, which builder lost its launcher, and the after-build sweep (2026-10-28).

    python3 -I common/util/build_procs.py sweep <token> [--dry-run]   stop every process left by one builder run
    python3 -I common/util/build_procs.py guard [--dry-run]           one pass of the orphan-builder guard
    python3 -I common/util/build_procs.py list                        builders and whether their launcher is alive

common/launch/run_build.sh starts the builder with CWE_BUILD_RUN=<slug>:<epoch>:<launcher pid> and CWE_BUILD_SLUG=<slug>
in its environment, never in its arguments (the brief goes in on stdin). Every process the builder starts inherits
them, so a build's processes are found by their environment, and a name search (`pgrep -f`, an app's own `ps | grep`
clean-up) can no longer match a builder. Seen on 2026-10-28: claude-mem's start-up clean-up and 9router's updater
killed every process whose command line named their files, which the brief on the command line did; smarty's builder
killed itself with `pgrep -f "gate.py smarty-s2" | xargs kill -9`.

sweep: the processes that still carry the run's token after the builder ended (a background gate, a Monitor, a
daemon of the app under test: claude-mem's service ran 11 h) get SIGTERM, then SIGKILL after a grace period. The
sweeping process and its ancestors are never touched. Containers are not processes of the build: the hourly clean-up
and `cweq orphans` handle them.

guard: a builder is orphaned when no ancestor is its launcher (run_build.sh, or resume_pipeline.sh for builders that
an older release resumed): its `timeout` or run_build.sh was killed, so nothing limits it and the pipeline already
moved on to the post-build checks (scale batch 1: an orphaned builder killed those twice). Until 2026-10-28 the guard
acted on build/<slug>/end_utc.txt alone, and stopped spring-data-mongodb-s2's live builder after it wrote that file
itself. Now:
  tagged builder (CWE_BUILD_RUN in its environment): orphaned when its launcher is gone; the whole run is swept;
  older builder (brief on its command line, no tag): orphaned when its launcher is gone AND end_utc.txt is newer
  than the process (the old rule, kept as a second condition); the builder and its descendants are stopped.
Also, processes that carry the tag of a run whose launcher is gone (the token names the launcher's pid) are swept:
leftovers when run_build.sh was killed before its own sweep. A candidate is checked twice, a few seconds apart,
before anything is stopped.
"""
import argparse
import os
import re
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))

TAGS = ("CWE_BUILD_RUN", "CWE_BUILD_SLUG")
LAUNCHERS = ("run_build.sh", "resume_pipeline.sh")
BRIEF_LINE = "Build one security-fix benchmark task"
TASK_LINE = re.compile(r"Task: `([A-Za-z0-9][A-Za-z0-9._-]*)`")
MAX_DEPTH = 12


def read_table(proc_root="/proc"):
    """{pid: {pid, ppid, comm, argv, env, start}} for every readable process. env holds only the CWE_BUILD_* tags;
    start is the start time in clock ticks since boot (field 22 of stat)."""
    root, out = Path(proc_root), {}
    try:
        pids = [d for d in os.listdir(root) if d.isdigit()]
    except OSError:
        return out
    for d in pids:
        try:
            stat = (root / d / "stat").read_text()
            raw = (root / d / "cmdline").read_bytes()
        except OSError:
            continue
        comm = stat[stat.find("(") + 1:stat.rfind(")")]
        rest = stat[stat.rfind(")") + 2:].split()
        if len(rest) < 20:
            continue
        env = {}
        try:
            for kv in (root / d / "environ").read_bytes().split(b"\0"):
                k, _, v = kv.partition(b"=")
                if k.decode(errors="replace") in TAGS:
                    env[k.decode()] = v.decode(errors="replace")
        except OSError:
            pass
        out[int(d)] = {"pid": int(d), "ppid": int(rest[1]), "comm": comm, "start": rest[19],
                       "argv": [a.decode(errors="replace") for a in raw.split(b"\0") if a], "env": env}
    return out


def is_claude(p):
    return p["comm"] == "claude" or (p["argv"] and os.path.basename(p["argv"][0]) == "claude")


def ancestors(pid, table):
    """Ancestor pids, nearest first, as far as the table knows them."""
    out, cur = [], table.get(pid, {}).get("ppid")
    while cur and cur in table and cur not in out and len(out) < MAX_DEPTH:
        out.append(cur)
        cur = table[cur]["ppid"]
    return out


def launcher_alive(pid, table):
    return any(any(any(m in a for m in LAUNCHERS) for a in table[a_pid]["argv"]) for a_pid in ancestors(pid, table))


def builders(table):
    """[{pid, slug, token, tagged}]: the main builder process of each build (a claude run started by run_build.sh, or
    an older one that carries the brief on its command line). A claude process the builder itself started (a nested
    one, e.g. while testing a Claude Code plugin) is not a builder."""
    out = []
    for pid, p in table.items():
        if not is_claude(p):
            continue
        tok = p["env"].get("CWE_BUILD_RUN")
        if tok:
            if any(table[a]["env"].get("CWE_BUILD_RUN") == tok and is_claude(table[a]) for a in ancestors(pid, table)):
                continue                                   # started by the builder itself
            out.append({"pid": pid, "slug": p["env"].get("CWE_BUILD_SLUG") or tok.split(":")[0], "token": tok,
                        "tagged": True})
            continue
        cmd = " ".join(p["argv"])
        if BRIEF_LINE in cmd:
            m = TASK_LINE.search(cmd)
            if m:
                out.append({"pid": pid, "slug": m.group(1), "token": None, "tagged": False})
    return out


def _utc_epoch(path):
    try:
        return datetime.fromisoformat(Path(path).read_text().strip().replace("Z", "+00:00")).timestamp()
    except (OSError, ValueError):
        return None


def _proc_start_epoch(p, proc_root="/proc"):
    """Wall-clock start of a process from its stat start time, or None."""
    try:
        btime = next(int(l.split()[1]) for l in Path(proc_root, "stat").read_text().splitlines() if l.startswith("btime"))
        return btime + int(p["start"]) / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, StopIteration):
        return None


def orphans(table, build_root, proc_root="/proc"):
    """Builders whose launcher is gone ([{pid, slug, token, tagged, why}])."""
    out = []
    for b in builders(table):
        if launcher_alive(b["pid"], table):
            continue
        if b["tagged"]:
            out.append(dict(b, why="launcher gone (no run_build.sh above it)"))
            continue
        end = _utc_epoch(Path(build_root) / b["slug"] / "end_utc.txt")
        start = _proc_start_epoch(table[b["pid"]], proc_root)
        if end is not None and start is not None and start < end:
            out.append(dict(b, why="launcher gone and the build ended (end_utc.txt) after it started"))
    return out


def stale_runs(table):
    """{token: slug} of build runs whose launcher is gone while processes still carry their tag (e.g. a daemon left
    behind when run_build.sh was killed before its sweep). The token's third field is the launcher's pid; it counts
    as alive only while that pid runs run_build.sh for the same slug (a reused pid does not)."""
    out = {}
    for p in table.values():
        tok = p["env"].get("CWE_BUILD_RUN")
        if not tok or tok in out:
            continue
        parts = tok.split(":")
        slug, lpid = parts[0], int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
        launcher = table.get(lpid) if lpid else None
        if launcher and any("run_build.sh" in a for a in launcher["argv"]) and slug in launcher["argv"]:
            continue
        out[tok] = slug
    return out


def descendants(pid, table):
    kids, todo = [], [pid]
    while todo:
        cur = todo.pop()
        for q, p in table.items():
            if p["ppid"] == cur and q not in kids:
                kids.append(q)
                todo.append(q)
    return kids


def tagged(token, table):
    return [pid for pid, p in table.items() if p["env"].get("CWE_BUILD_RUN") == token]


def stop(pids, table, grace=5.0, dry_run=False, say=print, killer=os.kill, alive=None):
    """SIGTERM, then SIGKILL after grace seconds for those still alive. Never this process or its ancestors."""
    me = os.getpid()
    spare = {me, *ancestors(me, table)}
    pids = [p for p in pids if p not in spare]
    for p in pids:
        info = table.get(p, {})
        say(f"  {'would stop' if dry_run else 'stopping'} pid {p} ({info.get('comm', '?')}: "
            f"{' '.join(info.get('argv', []))[:120]})")
    if dry_run or not pids:
        return pids
    alive = alive or (lambda q: Path(f"/proc/{q}").exists())
    for p in pids:
        try:
            killer(p, signal.SIGTERM)
        except OSError as e:
            say(f"  pid {p}: SIGTERM failed ({e.strerror})")
    deadline = time.time() + grace
    while time.time() < deadline and any(alive(p) for p in pids):
        time.sleep(0.5)
    for p in pids:
        if alive(p):
            try:
                killer(p, signal.SIGKILL)
            except OSError:
                pass
    return pids


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def cmd_sweep(a):
    table = read_table(a.proc_root)
    pids = tagged(a.token, table)
    if not pids:
        return 0
    print(f"{utc()} build sweep {a.token}: {len(pids)} process(es) left after the builder ended")
    stop(pids, table, grace=a.grace, dry_run=a.dry_run)
    return 0


def cmd_guard(a, build_root):
    table = read_table(a.proc_root)
    cands, runs = orphans(table, build_root, a.proc_root), stale_runs(table)
    if not cands and not runs:
        return 0
    time.sleep(a.recheck)                                  # check twice: never act on a half-started launch
    table = read_table(a.proc_root)
    again = {(o["pid"], o["slug"]) for o in orphans(table, build_root, a.proc_root)}
    swept = set()
    for o in cands:
        if (o["pid"], o["slug"]) not in again:
            continue
        print(f"{utc()} orphaned builder of {o['slug']} (pid {o['pid']}): {o['why']}")
        pids = tagged(o["token"], table) if o["tagged"] else [o["pid"], *descendants(o["pid"], table)]
        stop(pids, table, grace=a.grace, dry_run=a.dry_run)
        swept.add(o["token"])
    still = stale_runs(table)
    for tok, slug in runs.items():
        if tok in swept or tok not in still:
            continue
        pids = tagged(tok, table)
        print(f"{utc()} leftovers of {slug}'s build run {tok} (launcher gone): {len(pids)} process(es)")
        stop(pids, table, grace=a.grace, dry_run=a.dry_run)
    return 0


def cmd_list(a, build_root):
    table = read_table(a.proc_root)
    for b in builders(table):
        print(f"{b['pid']}\t{b['slug']}\t{'tagged' if b['tagged'] else 'argv'}\t"
              f"launcher {'alive' if launcher_alive(b['pid'], table) else 'GONE'}\t{len(tagged(b['token'], table)) if b['token'] else '-'} procs")
    return 0


def main(argv=None):
    import paths
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proc-root", default="/proc")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sweep")
    p.add_argument("token")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--grace", type=float, default=5.0)
    p = sub.add_parser("guard")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--grace", type=float, default=3.0)
    p.add_argument("--recheck", type=float, default=5.0)
    sub.add_parser("list")
    a = ap.parse_args(argv)
    if a.cmd == "sweep":
        return cmd_sweep(a)
    if a.cmd == "guard":
        return cmd_guard(a, paths.BUILD)
    return cmd_list(a, paths.BUILD)


if __name__ == "__main__":
    sys.exit(main())
