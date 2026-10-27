#!/usr/bin/env python3
"""Task-quality lint as a light queue job: warning-only, it never holds or blocks a build, gate or trial.

    L1  A batch task that is SOUND on its gate (any stage from waiting_trials on) and has no
        build/<slug>/lint/<fp>.json for its current gate fingerprint gets one `lint` job (args {"fp": fp}).
        A new task version (new fingerprint) is linted again; an older result stays as history.
    The job runs `lintstep.py run <slug> <fp>`: common/lint/task_lint.py over tasks/<slug> (static checks plus the
    task's own score.py against synthetic results), written to build/<slug>/lint/<fp>.json as
        {"task", "fp", "linted", "warn", "info", "findings": [{kind, severity, file, line, message}, ...]}.
    `cweq explain` and the decisions inbox show the newest result (latest()).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qdb  # noqa: E402
import taskstate  # noqa: E402
from taskstate import paths  # noqa: E402

KIND = "lint"
STAGES = ("waiting_trials", "trialing", "trials_stuck", "not_breaker", "awaiting_audit", "awaiting_fairness",
          "fairness_not_ready", "awaiting_decision", "kept")


def out_path(slug, fp):
    return paths.BUILD / slug / "lint" / f"{fp}.json"


def latest(slug):
    """The newest lint result of a task (dict with an added "path"), or None."""
    d = paths.BUILD / slug / "lint"
    files = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime) if d.is_dir() else []
    for f in reversed(files):
        try:
            r = json.loads(f.read_text())
            r["path"] = str(f)
            return r
        except (OSError, ValueError):
            continue
    return None


def line(slug):
    """One line for explain / the inbox, or ''."""
    r = latest(slug)
    if not r:
        return ""
    kinds = sorted({f["kind"] for f in r.get("findings", []) if f.get("severity") == "warn"})
    return (f"lint {r.get('warn', 0)} warnings, {r.get('info', 0)} notes (gate {r.get('fp', '?')}, {r.get('linted', '')})"
            + (f": {', '.join(kinds)}" if kinds else ""))


def plan(states):
    """[{task, args}] for L1."""
    jobs = []
    for slug, t in sorted(states.items()):
        if not t.get("batch") or t.get("stage") not in STAGES or ".sound" not in t.get("markers", []):
            continue
        if not (paths.TASKS / slug / "tests").is_dir():
            continue
        fp = taskstate.gate_sha16(slug)
        if not out_path(slug, fp).is_file():
            jobs.append({"task": slug, "args": {"fp": fp}})
    return jobs


def reconcile(conn, cfg, states, dry_run=False):
    if not (cfg.get("lint", {}) or {}).get("enabled", True):
        return []
    out = []
    for w in plan(states):
        if not dry_run:
            w["id"], _ = qdb.enqueue(conn, KIND, w["task"], w["args"], priority=cfg["priority"].get(KIND, 0),
                                     max_attempts=cfg["max_attempts"].get(KIND, 1), origin="reconciler")
        w["kind"] = KIND
        out.append({"task": w["task"], "stage": "lint", "want": [w], "notes": []})
    return out


def command(row, cfg):
    """argv for a lint job (worker.py), or None for other kinds."""
    if row["kind"] != KIND:
        return None
    return [sys.executable, "-I", str(Path(__file__).resolve()), "run", row["task"], qdb.args_of(row)["fp"]]


def run(slug, fp):
    sys.path.insert(0, str(paths.COMMON / "lint"))
    import task_lint
    findings = task_lint.lint(paths.TASKS / slug, None, True)
    rows = [f.as_dict() for f in findings]
    res = {"task": slug, "fp": fp, "linted": qdb.utc(),
           "warn": sum(1 for f in rows if f.get("severity") == "warn"),
           "info": sum(1 for f in rows if f.get("severity") == "info"), "findings": rows}
    dst = out_path(slug, fp)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(res, indent=1))
    os.replace(tmp, dst)
    print(f"lint {slug}: {res['warn']} warnings, {res['info']} notes -> {dst}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "run":
        sys.exit(run(sys.argv[2], sys.argv[3]))
    sys.exit("usage: lintstep.py run <slug> <fp>")
