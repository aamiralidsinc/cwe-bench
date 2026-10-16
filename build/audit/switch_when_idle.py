#!/usr/bin/env python3
"""Detached helper (2026-10-16): switch rclone / rclone-sib to the offline setting once their
in-flight runs end, and release webob once its re-gate on the clean commit passes. Each task is
then listed in build/audit/offline_since.tsv, which lets build/queue_offline.py start it."""
import json, re, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SINCE = ROOT / "build/audit/offline_since.tsv"
BLOCK = ('network_mode = "allowlist"   # offline like CWE-bench: only the model APIs (arXiv 2610.17020, 2026-10-16)\n'
         'allowed_hosts = ["api.deepseek.com", "api.xiaomimimo.com"]\n')
now = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
def log(m): open(ROOT / "build/audit/offline_queue.log", "a").write(f"{now()}Z switch: {m}\n")
def busy(task): return subprocess.run(["pgrep", "-f", f"trial.py {task} "], capture_output=True).returncode == 0
def listed(task): return any(l.startswith(task + "\t") for l in SINCE.read_text().splitlines())
def go_offline(task):
    d = ROOT / "tasks" / task; t = (d / "task.toml").read_text()
    if BLOCK not in t:
        t = re.sub(r'(\[agent\]\n(?:[^\[]*?\n)?timeout_sec = [0-9.]+\n)', lambda m: m.group(1) + BLOCK, t, count=1)
        assert BLOCK in t; (d / "task.toml").write_text(t)
    c = d / "environment" / "docker-compose.yaml"
    if c.exists() and "netguard" in c.read_text(): c.unlink()
    with open(SINCE, "a") as f: f.write(f"{task}\t{now()}\n")
    log(f"{task} offline and ready")
todo = {"rclone", "rclone-sib", "webob"}
while todo:
    for task in sorted(todo):
        if task == "webob":
            r = json.loads((ROOT / "build/webob/gate_report.json").read_text())
            if r.get("finished", "") >= "2026-10-15T19:37" and r.get("passed"):
                p = ROOT / "build/audit/task_defects.tsv"
                p.write_text(p.read_text().replace("webob\t\t", f"webob\t{now()}\t", 1))
                go_offline("webob"); todo.discard(task)
            elif r.get("finished", "") >= "2026-10-15T19:37" and not r.get("passed"):
                log(f"webob gate FAILED: {r.get('failure','')[:200]}"); todo.discard(task)
        elif not busy(task) and not listed(task):
            go_offline(task); todo.discard(task)
    time.sleep(60)
