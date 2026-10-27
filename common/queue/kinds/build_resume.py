"""build_resume: continue a sibling build whose builder was paused (SIGSTOP) and then cut by its overdue timer.

A builder frozen for longer than its 5 h limit is killed by `timeout` the moment it resumes (exit 124 long after the
limit; markers.build_paused, common/util/agent_status.py). Its work is not lost: the builder's conversation is on disk,
so the build continues in its own session with pipelines/sibling/6-build/resume_pipeline.sh, which then runs the
normal post-build gate. A fresh build would wipe tasks/<slug>, so it is never used for this.

Planned once per interruption (key: the build's end_utc), only for sibling tasks in a batch; never for a declined
build (STOP), a genuine timeout or a stacking task (no resume script: reported for a person).

    python3 common/queue/kinds/build_resume.py <slug>      find the session, then exec resume_pipeline.sh
"""
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _p in (str(HERE.parent), str(HERE.parent.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kinds import Kind, enqueue, register  # noqa: E402

RESUME_MSG = ("Note from the operator: this build was paused for several hours and then stopped by its timer when the "
              "machine resumed. That was an infrastructure problem, not something about your work. Continue the task "
              "from where you left off and finish it as the original brief says. Never kill processes you did not "
              "start yourself: other jobs share this machine.")
TASK_LINE = re.compile(rb"Task: `([A-Za-z0-9][A-Za-z0-9._-]*)`")


def projects_dir():
    return Path(os.environ.get("CWE_CLAUDE_PROJECTS", "~/.claude/projects")).expanduser()


def first_task(path, limit=4 << 20):
    """The slug of the first `Task: `<slug>`` line in a builder conversation file, or None."""
    try:
        with open(path, "rb") as f:
            m = TASK_LINE.search(f.read(limit))
        return m.group(1).decode() if m else None
    except OSError:
        return None


def find_session(slug, since=None, root=None):
    """The builder session (conversation file stem) whose FIRST task line names this slug; the newest one when
    several do. since: only files changed at or after this epoch (the build's start)."""
    best = None
    for f in (root or projects_dir()).glob("*/*.jsonl"):
        try:
            st = f.stat()
        except OSError:
            continue
        if since is not None and st.st_mtime < since:
            continue
        if first_task(f) == slug and (best is None or st.st_mtime > best[0]):
            best = (st.st_mtime, f.stem)
    return best[1] if best else None


def command(row, cfg):
    return [sys.executable, "-I", str(Path(__file__).resolve()), row["task"]]


def plan(conn, cfg, ctx, states, dry_run=False):
    import markers
    from taskstate import paths
    out = []
    for slug, t in (states or {}).items():
        if not t.get("paused_build"):
            continue
        if slug.startswith("stk-"):
            out.append({"task": slug, "stage": t["stage"], "want": [],
                        "notes": ["paused stacking build: no resume script, a person resumes or rebuilds it"]})
            continue
        end = markers.read_text(paths.BUILD / slug / "end_utc.txt").strip()
        args = {"end": end}
        jid = enqueue(conn, cfg, "build_resume", slug, args, dry_run=dry_run)
        want = {"kind": "build_resume", "args": args}
        if jid:
            want["id"] = jid
        out.append({"task": slug, "stage": t["stage"], "want": [want], "notes": []})
    return out


def check(task, args, t0, cfg):
    """The resumed builder ran (resume_start_utc and end_utc after the job started) and the build has an outcome."""
    import markers
    import qdb
    from taskstate import paths
    b = paths.BUILD / task
    rs = qdb.parse_utc(markers.read_text(b / "resume_start_utc.txt").strip())
    end = qdb.parse_utc(markers.read_text(b / "end_utc.txt").strip())
    ran = bool(rs and end and rs >= t0 - 60 and end >= rs)
    log = markers.read_text(b / "pipeline.log")
    outcome = any((b / m).exists() for m in (".sound", ".unsound", ".gate_error", ".gate_passed")) or \
        "BUILD-INCOMPLETE (resumed" in log or "stopped/failed: resumed" in log
    return [("build_resume.ran", ran, f"resume_start {rs} end {end}", False),
            ("build_resume.outcome", outcome, "gate marker or a resumed-build log line" if outcome else
             "no gate marker and no resumed-build line in pipeline.log", not outcome)]


register(Kind(name="build_resume", command=command, check=check, plan=plan, exclusive=True, priority=26,
              max_running=4, max_attempts=1, disk_floor="DISK_MIN_FREE_GB_BUILD",
              reads=("build/<slug>/end_utc.txt", "build/<slug>/build-exit.txt", "build/<slug>/build_status.json",
                     "~/.claude/projects/*/*.jsonl"),
              writes=("tasks/<slug>/", "build/<slug>/ (resume_start_utc.txt, end_utc.txt, build-run.json, markers)")))


def main(argv):
    if len(argv) != 2:
        sys.exit("usage: build_resume.py <slug>")
    slug = argv[1]
    sys.path.insert(0, str(HERE.parent.parent))
    import paths
    import markers
    since = None
    st = markers.read_text(paths.BUILD / slug / "start_utc.txt").strip()
    if st:
        from datetime import datetime
        since = datetime.fromisoformat(st.replace("Z", "+00:00")).timestamp() - 600
    sess = find_session(slug, since=since)
    if not sess:
        print(f"build_resume {slug}: no builder session found whose first task line names it", file=sys.stderr)
        return 2
    os.environ.setdefault("RESUME_MSG", RESUME_MSG)
    script = paths.ROOT / "pipelines" / "sibling" / "6-build" / "resume_pipeline.sh"
    print(f"build_resume {slug}: resuming session {sess}", flush=True)
    os.chdir(paths.ROOT)
    os.execvp("bash", ["bash", str(script), slug, "build", sess])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
