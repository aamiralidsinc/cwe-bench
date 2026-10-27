"""Processes and machine headroom, read without side effects.

busy_tasks(): which tasks other launchers are working on right now (regate.sh <slug>, regate_queue.py <list>,
a repair script that names the slug inside, ...). The queue leaves those tasks alone.
Our own workers carry CWEQ_JOB in their environment (inherited by every child) and are not counted.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

SLUG_CHARS = "A-Za-z0-9._-"


def list_processes():
    """[(pid, argv list, cwd or None, environ dict or {})] for this machine. /proc on Linux, `ps` elsewhere."""
    out = []
    if Path("/proc/self/cmdline").exists():
        for d in os.listdir("/proc"):
            if not d.isdigit():
                continue
            try:
                raw = open(f"/proc/{d}/cmdline", "rb").read()
            except OSError:
                continue
            if not raw:
                continue
            argv = [a.decode(errors="replace") for a in raw.rstrip(b"\0").split(b"\0")]
            try:
                cwd = os.readlink(f"/proc/{d}/cwd")
            except OSError:
                cwd = None
            env = {}
            try:
                for kv in open(f"/proc/{d}/environ", "rb").read().split(b"\0"):
                    if kv.startswith(b"CWEQ_JOB="):
                        env["CWEQ_JOB"] = kv[9:].decode()
            except OSError:
                pass
            out.append((int(d), argv, cwd, env))
        return out
    r = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if pid.isdigit():
            out.append((int(pid), cmd.split(), None, {}))
    return out


def _arg_file_text(arg, cwd, skip_dirs):
    """Text of a small file named on a command line (a slug list, a one-off script); '' otherwise.
    Shared code (common/) is skipped: it never hard-codes a slug, but its comments may name examples."""
    p = Path(arg)
    if not p.is_absolute():
        if not cwd:
            return ""
        p = Path(cwd) / p
    try:
        p = p.resolve()
        if any(str(p).startswith(str(s) + os.sep) for s in skip_dirs) or not p.is_file() or p.stat().st_size > 262144:
            return ""
        return p.read_text(errors="replace")
    except OSError:
        return ""


def busy_tasks(slugs, patterns, procs=None, skip_dirs=()):
    """{slug: [(pid, command)]} for every slug a matching foreign process names."""
    slugs = set(slugs)
    procs = list_processes() if procs is None else procs
    out = {}
    for pid, argv, cwd, env in procs:
        if env.get("CWEQ_JOB") or pid == os.getpid():
            continue                                    # our own workers and their children
        cmd = " ".join(argv)
        if "common/queue/cweq.py" in cmd or not any(p in cmd for p in patterns):   # cweq itself is not an old script
            continue
        text = cmd + "\n" + "\n".join(_arg_file_text(a, cwd, skip_dirs) for a in argv[1:] if "/" in a or "." in a)
        # A slug counts as a whole word: not part of a longer slug (fastify-s2 is not fastify-s2x).
        for tok in set(re.findall(rf"[{SLUG_CHARS}]+", text.replace("__", " "))):
            for cand in {tok, tok.rstrip("."), Path(tok).name}:
                if cand in slugs:
                    out.setdefault(cand, []).append((pid, cmd[:160]))
    return out


def pid_alive(pid):
    """True when pid exists and is not a zombie."""
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        stat = open(f"/proc/{pid}/stat").read()
        return stat.rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        pass
    try:                                                # macOS: ask ps for the state
        r = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
        return r.returncode == 0 and not r.stdout.strip().startswith("Z")
    except OSError:
        return True


def headroom(root):
    """Measured values the admission limits compare against; None = not measurable here (counts as fine)."""
    m = {"free_disk_gb": None, "load": None, "mem_available_gb": None, "tmp_inode_pct": None}
    try:
        m["free_disk_gb"] = round(shutil.disk_usage(root).free / 2**30, 1)
    except OSError:
        pass
    try:
        m["load"] = round(os.getloadavg()[0], 1)
    except OSError:
        pass
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                m["mem_available_gb"] = round(int(line.split()[1]) / 2**20, 1)
    except OSError:
        pass
    try:
        st = os.statvfs("/tmp")
        if st.f_files:
            m["tmp_inode_pct"] = round(100 * (st.f_files - st.f_ffree) / st.f_files, 1)
    except OSError:
        pass
    return m


def over_limits(m, limits):
    """Reasons why no job may start now (empty list = admission open)."""
    why = []
    if m.get("free_disk_gb") is not None and m["free_disk_gb"] < limits["min_free_disk_gb"]:
        why.append(f"free disk {m['free_disk_gb']} GB < {limits['min_free_disk_gb']}")
    if m.get("load") is not None and m["load"] > limits["max_load"]:
        why.append(f"load {m['load']} > {limits['max_load']}")
    if m.get("mem_available_gb") is not None and m["mem_available_gb"] < limits["min_mem_available_gb"]:
        why.append(f"memory available {m['mem_available_gb']} GB < {limits['min_mem_available_gb']}")
    if m.get("tmp_inode_pct") is not None and m["tmp_inode_pct"] > limits["max_tmp_inode_pct"]:
        why.append(f"/tmp inodes {m['tmp_inode_pct']}% > {limits['max_tmp_inode_pct']}%")
    return why
