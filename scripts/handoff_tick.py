#!/usr/bin/env python3
"""Handoff autopilot: one deterministic "tick" of the pipeline side of the Grok/Cursor handoff loop (2026-10-20).

Run every ~30 min (Claude Code /loop). Each tick:
  1. rebuilds data/handoff/STATE.json + STATE.md (scripts/handoff.py);
  2. answered-but-unconsumed requests -> runs stage 3 (handoff backend) for those candidates: answers are validated, the
     next requests (tests phase, retries) are written, finished tasks get instruction.md, unsuitable ones are retired;
  3. generated tasks with no stage-4 verdict -> launches stage 4 then stages 5-6 for them in the BACKGROUND (never a second
     copy of a stage that is already running; the trial waits for any running trial to finish);
  4. writes results, alerts (every safeguards flag is surfaced - project rule) and next actions into STATE.md.
It never edits verdicts, never touches flagged candidates (the pipeline retires them), and never calls a model itself.
Logs: data/logs/<date>_handoff-autopilot/ (tick.log + one log per launched step).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import handoff  # noqa: E402

PY = str(ROOT / ".venv" / "bin" / "python")
LOGDIR_FILE = ROOT / "data" / "handoff" / "autopilot_logdir.txt"
HANDOFF_ENV = {"TASK_GEN_BACKEND": "handoff", "HANDOFF_MODEL": os.environ.get("HANDOFF_MODEL", "grok-4.7-high")}


def logdir() -> Path:
    if LOGDIR_FILE.is_file():
        d = ROOT / LOGDIR_FILE.read_text().strip()
        if d.is_dir():
            return d
    d = ROOT / "data" / "logs" / f"{time.strftime('%Y-%m-%d_%H%M')}_handoff-autopilot"
    d.mkdir(parents=True, exist_ok=True)
    (d / "README.md").write_text(
        "# Handoff autopilot\n\nscripts/handoff_tick.py run every ~30 min: consumes Grok answers (stage 3), launches stage 4 "
        "+ trial (stages 5-6) for finished tasks, writes data/handoff/STATE.md.\n\n- tick.log: one line per tick\n"
        "- stage3_*.log, chain_*.log: the steps it launched\n")
    readme = ROOT / "data" / "logs" / "README.md"
    if readme.is_file():
        with readme.open("a") as fh:
            fh.write(f"| {d.name} | Handoff autopilot: 30-min ticks (stage 3 consume, stage 4 + trial launch, STATE.md) | running |\n")
    LOGDIR_FILE.write_text(str(d.relative_to(ROOT)))
    return d


def running(stage: str) -> bool:
    """A real pipeline process for this stage - not a shell whose command text merely mentions it (a "stage 4; then
    stage 5" chain contains "--stage 5" long before stage 5 starts; the Claude Code Bash tool wraps commands in zsh)."""
    ps = subprocess.run(["ps", "-axo", "args="], capture_output=True, text=True).stdout.splitlines()
    shell = re.compile(r"(/bin/|/usr/bin/)?(ba|z|k|da)?sh\b")
    return any(f"run_pipeline.py --stage {stage}" in a for a in ps if not shell.match(a.strip()))


def tick() -> dict:
    D = logdir()
    stamp = time.strftime("%H%M%S")
    did, alerts = [], []
    st = handoff.build_state()

    # 2. consume answers
    to_consume = sorted({v["candidate"] for v in st["requests"].values() if v["status"] == "answered"})
    if to_consume and running(3):
        did.append(f"stage 3 already running; {len(to_consume)} answered candidates wait for the next tick")
    elif to_consume:
        log = D / f"stage3_{stamp}.log"
        with log.open("w") as fh:
            rc = subprocess.run([PY, "run_pipeline.py", "--stage", "3", "--workers", str(min(8, len(to_consume))),
                                 "--only", ",".join(to_consume)], cwd=ROOT, env={**os.environ, **HANDOFF_ENV},
                                stdout=fh, stderr=subprocess.STDOUT, timeout=3600).returncode
        text = log.read_text(errors="replace")
        gen = re.findall(r"\[([\w-]+)\] generated \(", text)
        retired = re.findall(r"Retired: unsuitable candidate\s+osv_id=([\w-]+)", text)
        rejected = re.findall(r"\[([\w-]+)\] (?:design|tests) attempt \d+/\d+ rejected", text)
        did.append(f"stage 3 consumed {len(to_consume)} candidates (rc={rc}): generated {gen or 'none'}, "
                   f"retired {retired or 'none'}, answers sent back for retry {sorted(set(rejected)) or 'none'}")
        st = handoff.build_state()

    # 3. launch stage 4 + trial for finished tasks without a stage-4 verdict
    ready = sorted(k for k, v in st["candidates"].items()
                   if v["generated"] and not v["retired"] and v["stage4"] in (None, "failed"))
    if ready and running(4):
        did.append(f"stage 4 already running; {len(ready)} generated tasks wait: {ready}")
    elif ready:
        ids = ",".join(ready)
        chain = (f"{PY} run_pipeline.py --stage 4 --workers {min(4, len(ready))} --only {ids} "
                 f"> {D}/chain_{stamp}_stage4.log 2>&1; "
                 f"while ps -axo args= | grep -v -E '^(/bin/|/usr/bin/)?(ba|z|k|da)?sh' | grep -q '[r]un_pipeline.py --stage 5'; do sleep 60; done; "
                 f"{PY} run_pipeline.py --stage 5 6 --workers {min(4, len(ready))} --only {ids} "
                 f"> {D}/chain_{stamp}_stage5.log 2>&1")
        subprocess.Popen(["bash", "-c", chain], cwd=ROOT, start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        did.append(f"launched stage 4 -> trial in the background for {ready}")

    # 4. alerts: safeguards flags in anything this autopilot launched (every flag is reported - project rule)
    for f in sorted(D.glob("*.log")):
        for line in f.read_text(errors="replace").splitlines():
            if "safeguards flagged" in line.lower() and "flagged this candidate earlier" not in line:
                alerts.append(f"{f.name}: {line[:220]}")

    st = handoff.build_state()
    handoff_tasks = {k: v for k, v in st["candidates"].items() if v["generator"] == "handoff"}
    results = [f"{k}: stage4={v['stage4'] or '-'}, stage5={v['stage5'] or '-'}" for k, v in handoff_tasks.items()]
    pend = [n for n, v in st["requests"].items() if v["status"] == "pending"]
    stale = [n for n, v in st["requests"].items() if v["stale_claim"]]
    nxt = []
    if pend:
        nxt.append(f"CURSOR: answer {len(pend)} pending request(s) (list above)")
    if stale:
        nxt.append(f"CURSOR: {len(stale)} stale claim(s) - re-take them")
    if not pend and not stale and not to_consume and not ready:
        nxt.append("nothing for Cursor; pipeline steps are running or the batch is finished")
    pipeline = {s: ("running" if running(s) else "idle") for s in ("3", "4", "5")}
    out = handoff.write_state({"pipeline": {f"stage {k}": v for k, v in pipeline.items()}, "next_actions": nxt,
                               "results": results, "alerts": alerts, "last_tick": did})
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {out['counts']} | did: {'; '.join(did) or 'nothing'} | alerts: {len(alerts)}"
    with (D / "tick.log").open("a") as fh:
        fh.write(line + "\n")
    print(line)
    for a in alerts:
        print("ALERT", a)
    return out


if __name__ == "__main__":
    tick()
