#!/usr/bin/env python3
"""Remove this user's top-level /tmp entries older than 12 h that no process has open (cwd, open files or command-line
paths). Other users' entries are never touched. --dry-run only counts. Step 7 of hourly_cleanup.sh."""
import os, pwd, shutil, sys, time
DRY = "--dry-run" in sys.argv
me = os.getuid(); cutoff = time.time() - 12 * 3600
inuse = set()
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    for link in ["cwd", "root"] + [f"fd/{x}" for x in (os.listdir(f"/proc/{pid}/fd") if os.access(f"/proc/{pid}/fd", os.R_OK) else [])]:
        try:
            t = os.readlink(f"/proc/{pid}/{link}")
        except OSError:
            continue
        if t.startswith("/tmp/"):
            inuse.add("/tmp/" + t[5:].split("/")[0])
    try:
        for a in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0"):
            a = a.decode(errors="replace")
            if a.startswith("/tmp/"):
                inuse.add("/tmp/" + a[5:].split("/")[0])
    except OSError:
        pass
removed = skipped = 0
for name in sorted(os.listdir("/tmp")):
    p = "/tmp/" + name
    try:
        st = os.lstat(p)
    except OSError:
        continue
    if st.st_uid != me or st.st_mtime > cutoff:
        continue
    if p in inuse:
        skipped += 1; print("in use, kept:", p); continue
    removed += 1
    if not DRY:
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p, ignore_errors=True)
        else:
            try: os.remove(p)
            except OSError: pass
print(("would remove" if DRY else "removed"), removed, "entries; kept in use:", skipped)
