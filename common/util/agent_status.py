#!/usr/bin/env python3
"""agent_status.py <claude-output.json> <exit-code> [--details <out.json>] : did a
`claude -p --output-format json` run finish cleanly? Prints `ok` or `error: <why>`; exit 0 / 1.

A run cut by a quota or session limit, an API error, the timeout (exit 124) or a crash produced
no substantive result, whatever files it left behind. Until 2026-10-20 several launchers used
such output anyway: backstage-ds wired a quota-cut agent's half patch in as a must-pass fix.

--details writes EVERYTHING known about the run for root-cause analysis: exit code, the agent's
complete result text, its error list, terminal reason, turns, duration, cost, permission
denials, and the tail of its stderr (<same name>.err). The printed line is a summary that names
that file; until 2026-10-21 it kept only the first 160 characters and nothing else.

Exit 124 from a run that lasted far longer than its limit is not a timeout: the process was paused (SIGSTOP) and its
overdue timer fired when it resumed (2026-10-27: sixteen builders frozen for hours during a disk emergency were all cut
at the same second on resume). When the wall time between the run's start (start_utc.txt, or resume_start_utc.txt for
a resumed build, next to the output file) and end_utc.txt exceeds BUILD_TIMEOUT (default 18000 s) by more than 25 %, the
status is `error: interrupted (timer fired late: process was paused ...)` and details carry `paused_interrupt: true`,
`wall_sec` and `limit_sec`. Such a build is resumable (taskstate stage build_interrupted; queue kind build_resume).
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

CUT = re.compile(r"^\s*(You've hit your|API Error: ?\d{3}|Credit balance is too low)|overloaded_error", re.I)
STDERR_TAIL = 100_000


LATE_FACTOR = 1.25


def _utc(path):
    try:
        return datetime.fromisoformat(Path(path).read_text().strip().replace("Z", "+00:00")).timestamp()
    except (OSError, ValueError):
        return None


def wall_time(run_dir):
    """Seconds between the run's start (the later of start_utc.txt and resume_start_utc.txt) and end_utc.txt."""
    d = Path(run_dir)
    starts = [t for t in (_utc(d / "start_utc.txt"), _utc(d / "resume_start_utc.txt")) if t is not None]
    end = _utc(d / "end_utc.txt")
    if not starts or end is None:
        return None
    start = max(starts)
    return end - start if end >= start else None


def paused_interrupt(run_dir, rc, limit=None):
    """(True, wall, limit) when exit 124 came long after the limit: the timer fired late because the process was
    paused. (False, wall, limit) otherwise."""
    limit = float(limit if limit is not None else os.environ.get("BUILD_TIMEOUT") or 18000)
    wall = wall_time(run_dir)
    return (rc == 124 and wall is not None and wall > LATE_FACTOR * limit), wall, limit


def one_line(text, n=300):
    s = " ".join(str(text or "").split())
    return s if len(s) <= n else s[: n - 3] + "..."


def inspect(path, rc):
    """(status line, full details dict)."""
    p = Path(path)
    err_file = p.with_suffix(".err")
    details = {"output_file": str(p), "exit_code": rc,
               "stderr_file": str(err_file) if err_file.exists() else None}
    try:
        details["stderr_tail"] = err_file.read_text(errors="replace")[-STDERR_TAIL:] if err_file.exists() else None
    except OSError as e:
        details["stderr_tail"] = f"(unreadable: {type(e).__name__}: {e})"
    if rc == 124:
        late, wall, limit = paused_interrupt(p.parent, rc)
        details.update({"wall_sec": wall, "limit_sec": limit, "paused_interrupt": late})
        if late:
            return (f"error: interrupted (timer fired late: process was paused; ran {round(wall / 60)} min against a "
                    f"{round(limit / 60)} min limit)"), details
        return "error: agent timed out (exit 124)", details
    try:
        raw = p.read_text(errors="replace")
    except FileNotFoundError:
        return f"error: no agent output {p} (exit {rc})", details
    except OSError as e:
        return f"error: unreadable agent output {p} ({type(e).__name__}: {e}, exit {rc})", details
    try:
        data = json.loads(raw)
    except ValueError as e:
        details["output_head"], details["output_tail"] = raw[:5000], raw[-20000:]
        return f"error: agent output is not JSON ({type(e).__name__}: {e}, exit {rc})", details
    if isinstance(data, list):        # stream form: the last result event decides
        data = next((e for e in reversed(data) if isinstance(e, dict) and e.get("type") == "result"), {})
    text = str(data.get("result") or "")
    details.update({k: data.get(k) for k in ("is_error", "subtype", "terminal_reason", "num_turns",
                                             "duration_ms", "total_cost_usd", "errors",
                                             "permission_denials", "session_id", "modelUsage")})
    details["agent_result"] = text
    if data.get("is_error"):
        return f"error: agent reported is_error: {one_line(text)} (exit {rc})", details
    if CUT.search(text[:2000]):
        return f"error: agent was cut off: {one_line(text)}", details
    if rc != 0:
        return f"error: agent exited {rc}: {one_line(text or details.get('stderr_tail'))}", details
    return "ok", details


def status(path, rc):
    return inspect(path, rc)[0]


if __name__ == "__main__":
    args = sys.argv[1:]
    out = None
    if "--details" in args:
        i = args.index("--details")
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    if len(args) != 2:
        sys.exit("usage: agent_status.py <claude-output.json> <exit-code> [--details <out.json>]")
    line, details = inspect(args[0], int(args[1]))
    if out:
        details["status"] = line
        Path(out).write_text(json.dumps(details, indent=1, default=str))
        if line != "ok":
            line += f" [full: {out}]"
    print(line)
    sys.exit(0 if line == "ok" else 1)
