"""build_resume: continue a sibling build in its own session instead of rebuilding it.

Owner standing rule (2026-10-28): a build cut by its 5-hour limit or killed from outside is debugged, then RESUMED in
its own session, never restarted (a fresh build wipes tasks/<slug>). The builder's conversation is on disk, so the
build continues with pipelines/sibling/6-build/resume_pipeline.sh, which then runs the normal post-build checks
(common/gate/postbuild.sh: gate + blind fix).

Planned once per interruption (key: the build's end_utc), only for sibling tasks in a batch:
  paused    exit 124 long after the limit (markers.build_paused: SIGSTOP, then the overdue timer): always planned;
  timeout   a genuine 5-hour timeout (exit 124 within the limit, stage build_stopped): planned only with
            [build_resume] auto_timeouts = true (default false: the owner reviews; the plan says how to enqueue it),
            and at most max_auto_resumes times per task;
  killed    exit 137 / 143 (an outside kill): never planned, reported for a person (debug first, then enqueue).
Never for a declined build (build/<slug>/STOP.md) or a stacking task (no resume script): reported for a person.

The message the resumed builder gets, first found: the job's args.msg; build/<slug>/resume_msg.txt when written after
the interruption (a person writes it while debugging); the RESUME_MSG environment variable; the default for the
interruption (paused or timeout). Every message names the release the job runs from as the project root.

    python3 common/queue/kinds/build_resume.py <slug> [--msg TEXT]   find the session, then exec resume_pipeline.sh
    python3 common/queue/cweq.py enqueue build_resume <slug> --args '{"end": "<end_utc>", "msg": "..."}'   by hand
"""
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _p in (str(HERE.parent), str(HERE.parent.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kinds import Kind, builder_exit_file, enqueue, register  # noqa: E402

RULES = ("Run only the static and nop gate stages yourself, and only if they have not passed on the current files; "
         "the post-build gate runs oracle and patches after you report (prove those locally). Keep logs under "
         "~/.tb-graders/cwe/work/{slug}/; wait in bounded foreground loops on your log lines or with "
         "`tail --pid=<the pid you started>`, never with pgrep/pkill -f. Never set GATE_GLOBAL_SLOTS or "
         "GATE_PARALLEL. Before your final report, stop every background task or Monitor of yours, or this session "
         "never ends. Never kill processes you did not start yourself: other jobs share this machine.")
RESUME_MSG = ("Note from the operator: this build was paused for several hours and then stopped by its timer when the "
              "machine resumed. That was an infrastructure problem, not something about your work. Continue the task "
              "from where you left off and finish it as the original brief says. " + RULES)
TIMEOUT_MSG = ("Note from the operator: your 5-hour time budget ran out before your final report. That is not a "
               "judgement on your work: on this shared machine most of a build's time goes to waiting for gate slots "
               "and image builds. This resumed session has a fresh 5-hour budget and your files are untouched. First "
               "check on disk what is already done (tasks/{slug}, build/{slug}, your logs), then finish the task as "
               "the original brief says and send its report. " + RULES)
ROOT_LINE = ("The project root is now `{root}`: run every command from there, not from the root named in the "
             "original brief.")
TASK_LINE = re.compile(rb"Task: `([A-Za-z0-9][A-Za-z0-9._-]*)`")
KILLED = {"137": "SIGKILL", "143": "SIGTERM"}


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


def session_file(slug, since=None, root=None):
    """The builder conversation file whose FIRST task line names this slug; the newest one when several do.
    since: only files changed at or after this epoch (the build's start)."""
    best = None
    for f in (root or projects_dir()).glob("*/*.jsonl"):
        try:
            st = f.stat()
        except OSError:
            continue
        if since is not None and st.st_mtime < since:
            continue
        if first_task(f) == slug and (best is None or st.st_mtime > best[0]):
            best = (st.st_mtime, f)
    return best[1] if best else None


def find_session(slug, since=None, root=None):
    """The builder session id (conversation file stem), or None (session_file)."""
    f = session_file(slug, since, root)
    return f.stem if f else None


def into_project(session, cwd, root=None):
    """`claude --resume` finds a session only in the project folder of its working directory, and a build started
    under an older release has its conversation in that release's folder. Copy it (and its side folder of sub-agent
    and tool records, if any) into the folder of `cwd`, the release the resume runs from; never overwrite. Returns
    the destination, or None when the session is already there."""
    import shutil
    dest_dir = (root or projects_dir()) / re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    if session.parent == dest_dir:
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / session.name
    if not dest.exists():
        shutil.copy2(session, dest)
    side = session.with_suffix("")
    if side.is_dir() and not (dest_dir / side.name).exists():
        shutil.copytree(side, dest_dir / side.name)
    return dest


def interruption(b):
    """(reason, detail) of a build that ended without a gate verdict: paused | timeout | killed | None."""
    import markers
    code = markers.read_text(b / "build-exit.txt").strip()
    if code == "124":
        return ("paused", "cut by its overdue timer after a pause") if markers.build_paused(b) else \
            ("timeout", "a genuine 5-hour timeout (exit 124)")
    if code in KILLED:
        return "killed", f"killed from outside (exit {code}, {KILLED[code]})"
    return None, ""


def command(row, cfg):
    import qdb
    msg = (qdb.args_of(row) or {}).get("msg")
    return [sys.executable, "-I", str(Path(__file__).resolve()), row["task"], *(["--msg", str(msg)] if msg else [])]


def plan(conn, cfg, ctx, states, dry_run=False):
    import markers
    import qdb
    from taskstate import paths
    bc = cfg.get("build_resume") or {}
    auto, cap = bool(bc.get("auto_timeouts", False)), int(bc.get("max_auto_resumes", 1))
    out = []
    for slug, t in (states or {}).items():
        b = paths.BUILD / slug
        if t.get("paused_build"):
            reason, detail = "paused", "cut by its overdue timer after a pause"
        elif t.get("stage") == "build_stopped" and t.get("batch"):
            reason, detail = interruption(b)
            if reason not in ("timeout", "killed"):
                continue
        else:
            continue
        end = markers.read_text(b / "end_utc.txt").strip()
        rep = {"task": slug, "stage": t["stage"], "want": [], "notes": []}
        out.append(rep)
        hand = f"cweq enqueue build_resume {slug} --args '{{\"end\": \"{end}\"}}'"
        if slug.startswith("stk-"):
            rep["notes"].append(f"{reason} stacking build ({detail}): no resume script, a person resumes or rebuilds it")
            continue
        if (b / "STOP.md").exists():
            rep["notes"].append(f"{reason} build with STOP.md (the builder declined): never resumed")
            continue
        if reason == "killed":
            rep["notes"].append(f"builder {detail}: debug it, write build/{slug}/resume_msg.txt, then {hand}")
            continue
        args = {"end": end}
        same = [r for r in qdb.jobs(conn, "kind='build_resume' AND task=?", (slug,)) if qdb.args_of(r).get("end") == end]
        if same:                                       # this interruption already has its job (planned or by hand)
            rep["want"].append({"kind": "build_resume", "args": qdb.args_of(same[-1]), "id": same[-1]["id"]})
            continue
        if reason == "timeout":
            if not auto:
                rep["notes"].append(f"{detail}: debug it, write build/{slug}/resume_msg.txt, then {hand} "
                                    "([build_resume] auto_timeouts = false)")
                continue
            done = [r for r in qdb.jobs(conn, "kind='build_resume' AND task=?", (slug,))
                    if (qdb.args_of(r) or {}).get("reason") == "timeout" and qdb.args_of(r).get("end") != end]
            if len(done) >= cap:
                rep["notes"].append(f"{detail} again after {len(done)} automatic resume(s) "
                                    f"(max_auto_resumes = {cap}): a person looks, then {hand}")
                continue
            args["reason"] = "timeout"
        jid = enqueue(conn, cfg, "build_resume", slug, args, dry_run=dry_run)
        want = {"kind": "build_resume", "args": args}
        if jid:
            want["id"] = jid
        rep["want"].append(want)
    return out


def _since(path, t0, slack=60):
    try:
        return path.stat().st_mtime >= t0 - slack
    except OSError:
        return False


RESUMED_LINE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\t\S+\tbuild\t(BUILD-INCOMPLETE \(resumed|stopped/failed: resumed)",
                          re.M)


def check(task, args, t0, cfg):
    """The resumed builder ran (resume_start_utc and end_utc after the job started) and the build has an outcome
    since the job started: a gate marker written then, or a resumed-build line (resume_pipeline.sh) dated then."""
    import markers
    import qdb
    from taskstate import paths
    b = paths.BUILD / task
    rs = qdb.parse_utc(markers.read_text(b / "resume_start_utc.txt").strip())
    end = qdb.parse_utc(markers.read_text(b / "end_utc.txt").strip())
    ran = bool(rs and end and rs >= t0 - 60 and end >= rs)
    lines = [m.group(1) for m in RESUMED_LINE.finditer(markers.read_text(b / "pipeline.log"))]
    outcome = any(_since(b / m, t0) for m in (".sound", ".unsound", ".gate_error", ".gate_passed")) or \
        any((qdb.parse_utc(x) or 0) >= t0 - 60 for x in lines)
    return [("build_resume.ran", ran, f"resume_start {rs} end {end}", False),
            ("build_resume.outcome", outcome, "gate marker or a resumed-build log line" if outcome else
             "no gate marker and no resumed-build line in pipeline.log since the job started", not outcome)]


register(Kind(name="build_resume", command=command, check=check, plan=plan, exclusive=True, priority=26,
              max_running=4, max_attempts=1, disk_floor="DISK_MIN_FREE_GB_BUILD", exit_of=builder_exit_file,
              reads=("build/<slug>/end_utc.txt", "build/<slug>/build-exit.txt", "build/<slug>/build_status.json",
                     "build/<slug>/STOP.md", "build/<slug>/resume_msg.txt", "~/.claude/projects/*/*.jsonl"),
              writes=("tasks/<slug>/", "build/<slug>/ (resume_start_utc.txt, end_utc.txt, build-run.json, markers)")))


def message(slug, given, b, root, env=None):
    """(text, source) of the resumed builder's message (see the module docstring for the order)."""
    import markers
    env = os.environ if env is None else env
    reason, _ = interruption(b)
    text, src = None, None
    if given:
        text, src = given, "job args.msg"
    if text is None:
        f = b / "resume_msg.txt"
        end = markers._utc_epoch(b / "end_utc.txt")
        if f.is_file() and f.read_text().strip():
            if end is None or f.stat().st_mtime >= end:
                text, src = f.read_text().strip(), str(f)
            else:
                print(f"build_resume {slug}: {f} is older than the interruption; not used", flush=True)
    if text is None and env.get("RESUME_MSG"):
        text, src = env["RESUME_MSG"], "RESUME_MSG"
    if text is None:
        text, src = (RESUME_MSG if reason == "paused" else TIMEOUT_MSG), f"default ({reason or 'unknown'})"
    text = text.replace("{slug}", slug)
    return text + "\n\n" + ROOT_LINE.format(root=root), src


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="build_resume.py")
    ap.add_argument("slug")
    ap.add_argument("--msg", default="")
    a = ap.parse_args(argv[1:])
    slug = a.slug
    sys.path.insert(0, str(HERE.parent.parent))
    import paths
    import markers
    since = None
    st = markers.read_text(paths.BUILD / slug / "start_utc.txt").strip()
    if st:
        from datetime import datetime
        since = datetime.fromisoformat(st.replace("Z", "+00:00")).timestamp() - 600
    f = session_file(slug, since=since)
    if not f:
        print(f"build_resume {slug}: no builder session found whose first task line names it", file=sys.stderr)
        return 2
    sess = f.stem
    moved = into_project(f, paths.ROOT)
    if moved:
        print(f"build_resume {slug}: session {sess} copied from {f.parent.name} into {moved.parent.name} "
              "(the release this resume runs from)", flush=True)
    text, src = message(slug, a.msg, paths.BUILD / slug, paths.ROOT)
    os.environ["RESUME_MSG"] = text
    os.environ.pop("RESUME_MSG_FILE", None)
    script = paths.ROOT / "pipelines" / "sibling" / "6-build" / "resume_pipeline.sh"
    print(f"build_resume {slug}: resuming session {sess} (message: {src})", flush=True)
    os.chdir(paths.ROOT)
    os.execvp("bash", ["bash", str(script), slug, "build", sess])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
