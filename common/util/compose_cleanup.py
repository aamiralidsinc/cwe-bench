#!/usr/bin/env python3
"""Remove Harbor compose projects whole, and leaked Harbor compose networks (reports/gate-compose-rca-20261029.md).

Each Harbor trial runs two compose projects, `<trial>__env` and `<trial>__verifier__trial`, and each project has one
bridge network, `<project>_default`. A network is removed only by `docker compose down`, never by `docker rm` of the
containers. Every network holds one /24 of daemon.json's 172.16.0.0/12 pool (4,096 networks); on 2026-10-29 leaked
networks filled the pool and gates failed with "all predefined address pools have been fully subnetted".

    remove_projects(projects)     every container (any state) of each project, then the project's networks; what
                                  `compose down` does, without needing the compose files. Used by trial.py
                                  remove_container, identity.stop and throttle_gates.py.
    leaked_networks(...)          the filter of hourly_cleanup.sh's network step (pure; tested)

    python3 common/util/compose_cleanup.py leaked [--min-age-h 2] [--keep REGEX] [--pause 0.2] [--dry-run]
        Removes, one at a time with a pause, every Harbor run network (project label ending __env or
        __verifier__trial, name <project>_default) created more than --min-age-h hours ago that no container in any
        state references. --keep (an extended regex, case-insensitive) spares matching names: the tasks under
        repair. The container list is re-read every 100 networks; Docker itself refuses a network with an attached
        endpoint. Stops after --max-sec seconds (default 1500), leaving the rest to the next pass. Prints one
        summary line.
"""
import argparse
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

PROJECT_LABEL = "com.docker.compose.project"
HARBOR_SUFFIXES = ("__env", "__verifier__trial")
RECHECK_EVERY = 100


def _docker(args, timeout=120):
    """stdout of `docker <args>`; '' when Docker fails or hangs (every caller here is best-effort)."""
    try:
        return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def harbor_projects(project):
    """Both compose projects of the Harbor trial that `project` belongs to (any other project: itself)."""
    for suf in HARBOR_SUFFIXES:
        if project.endswith(suf):
            base = project[: -len(suf)]
            return [base + s for s in HARBOR_SUFFIXES]
    return [project]


def remove_projects(projects, docker=None):
    """Remove every container of each compose project (running, exited, created or dead), then its networks.
    Returns (containers removed, networks removed). Never raises."""
    d = docker or _docker
    n_ctr = n_net = 0
    for p in dict.fromkeys(x for x in projects if x):         # unique, in order
        ids = d(["ps", "-aq", "--filter", f"label={PROJECT_LABEL}={p}"]).split()
        if ids:
            d(["rm", "-f", "-v", *ids])
            n_ctr += len(ids)
        nets = d(["network", "ls", "-q", "--filter", f"label={PROJECT_LABEL}={p}"]).split()
        if nets:
            d(["network", "rm", *nets])
            n_net += len(nets)
    return n_ctr, n_net


def parse_created(text):
    """Docker's CreatedAt ('2026-10-22 05:45:33.796585083 +0000 UTC') as an aware datetime; None if unreadable."""
    m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)(?:\.\d+)? ([+-]\d{4})", (text or "").strip())
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        return None


def is_harbor_network(name, project):
    return (bool(project) and project.endswith(HARBOR_SUFFIXES) and name == f"{project}_default")


def leaked_networks(rows, used, now, min_age_h=2.0, keep=None):
    """Names of the networks to remove. rows: (name, created_at, project label) per network; used: network names any
    container (any state) references; keep: a regex (case-insensitive) whose matching names are spared."""
    cutoff = now - timedelta(hours=min_age_h)
    keep_re = re.compile(keep, re.I) if keep else None
    out = []
    for name, created, project in rows:
        when = parse_created(created)
        if when is None or when >= cutoff:                   # young, or age unknown: may be starting up
            continue
        if not is_harbor_network(name, project) or name in used:
            continue
        if keep_re and keep_re.search(name):
            continue
        out.append(name)
    return out


def network_rows(docker=None):
    fmt = "{{.Name}}\t{{.CreatedAt}}\t{{.Label \"%s\"}}" % PROJECT_LABEL
    raw = (docker or _docker)(["network", "ls", "--filter", f"label={PROJECT_LABEL}", "--format", fmt], 300)
    return [tuple((line.split("\t") + ["", ""])[:3]) for line in raw.splitlines() if line.strip()]


def used_networks(docker=None):
    raw = (docker or _docker)(["ps", "-a", "--no-trunc", "--format", "{{.Networks}}"], 600)
    return {n.strip() for line in raw.splitlines() for n in line.split(",") if n.strip()}


def remove_leaked(min_age_h=2.0, keep=None, pause=0.2, dry_run=False, docker=None, sleep=time.sleep, now=None,
                  max_sec=None, clock=time.monotonic):
    """The network step of hourly_cleanup.sh. Returns {candidates, removed, in_use, failed, left}; `left` counts the
    candidates not reached within max_sec seconds (the next pass takes them)."""
    d = docker or _docker
    t0 = clock()
    used = used_networks(d)
    cand = leaked_networks(network_rows(d), used, now or datetime.now(timezone.utc), min_age_h, keep)
    res = {"candidates": len(cand), "removed": 0, "in_use": 0, "failed": 0, "left": 0}
    for i, name in enumerate(cand):
        if max_sec is not None and clock() - t0 > max_sec:
            res["left"] = len(cand) - i
            break
        if i and i % RECHECK_EVERY == 0:
            used = used_networks(d)                          # a container may have appeared since
        if name in used:
            res["in_use"] += 1
            continue
        if dry_run:
            continue
        r = d(["network", "rm", name], 60)
        res["removed" if r.strip() else "failed"] += 1       # `docker network rm` echoes the name it removed
        sleep(pause)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    lk = sub.add_parser("leaked")
    lk.add_argument("--min-age-h", type=float, default=2.0)
    lk.add_argument("--keep", default="")
    lk.add_argument("--pause", type=float, default=0.2)
    lk.add_argument("--max-sec", type=float, default=1500)
    lk.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    keep = a.keep if a.keep and a.keep != "^$" else None
    r = remove_leaked(a.min_age_h, keep, a.pause, a.dry_run, max_sec=a.max_sec)
    done = r["candidates"] - r["in_use"] - r["left"] if a.dry_run else r["removed"]
    print(f"candidates {r['candidates']}, {'would remove' if a.dry_run else 'removed'} {done}, in use {r['in_use']}, "
          f"failed {r['failed']}" + (f", left for the next pass {r['left']} (time budget)" if r["left"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
