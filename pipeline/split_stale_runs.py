#!/usr/bin/env python3
"""split_stale_runs.py [--apply] : one-time repair (2026-10-20) of result logs that mix task versions.

Before snapshot_experiment.sh learned to move them, build/<slug>/runs_<model>.log and
trial_detail*.json kept the rows of every earlier version, so launchers read old rewards as
current (hubuum-client-rust-ds and flowise-ds were filed SOLVED on an older version's runs).
For every slug in ~/.tb-graders/cwe/experiments/INDEX.tsv this moves rows (and detail files)
dated before the slug's LATEST snapshot into <file>.<version> (e.g. runs_deepseek.log.v1). Nothing is deleted.
Without --apply it only prints what it would move.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = Path.home() / ".tb-graders" / "cwe" / "experiments" / "INDEX.tsv"
apply = "--apply" in sys.argv

latest = {}   # slug -> (snapshot datetime, version that was snapshotted)
for line in INDEX.read_text().splitlines():
    c = line.split("\t")
    if len(c) < 3:
        continue
    try:
        ts = datetime.strptime(c[0], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        continue
    if c[1] not in latest or ts > latest[c[1]][0]:
        latest[c[1]] = (ts, c[2])

moved = 0
for slug, (snap, ver) in sorted(latest.items()):
    b = ROOT / "build" / slug
    if not b.is_dir():
        continue
    if subprocess.run(["pgrep", "-f", rf"build/trial\.py {re.escape(slug)}( |$)"], capture_output=True).returncode == 0:
        print(f"{slug}: a trial is running now; skipped (re-run this script when it ends)")
        continue
    for log in sorted(b.glob("runs_*.log")):
        old, cur = [], []
        for row in log.read_text(errors="replace").splitlines():
            try:   # trial.py writes '%Y-%m-%d %H:%M:%S' in the VM's zone, which is UTC
                t = datetime.strptime(row.split("\t")[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                cur.append(row)        # unparseable: keep, never guess
                continue
            (old if t < snap else cur).append(row)
        if not old:
            continue
        moved += len(old)
        print(f"{slug} {log.name}: {len(old)} row(s) of {ver} (before its snapshot {snap:%FT%TZ}) "
              f"-> {log.name}.{ver}; {len(cur)} current row(s) stay")
        if apply:
            with open(f"{log}.{ver}", "a") as f:
                f.write("\n".join(old) + "\n")
            tmp = log.with_suffix(".log.tmp")
            tmp.write_text("\n".join(cur) + ("\n" if cur else ""))
            os.replace(tmp, log)
    for det in sorted(list(b.glob("trial_detail*.json")) + [b / "auto_trial.out"]):
        if det.is_file() and datetime.fromtimestamp(det.stat().st_mtime, timezone.utc) < snap:
            moved += 1
            print(f"{slug} {det.name}: last written before {ver}'s snapshot -> {det.name}.{ver}")
            if apply:
                os.replace(det, f"{det}.{ver}")
print(f"{'moved' if apply else 'would move'} {moved} item(s) across {len(latest)} snapshotted task(s)")
