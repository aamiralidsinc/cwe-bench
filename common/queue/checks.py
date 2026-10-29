"""Post-condition checks and tool self-checks (docs/RULES.md, roadmap section 5).

A job whose script exits with an ok code counts as `done` only when the files show the outcome it was meant to
produce. worker.py calls after_done() when qdb.finish() returned `done`. Failing checks turn the job `failed` with the
check named, or `blocked` when what is on disk needs a person's judgement (for example a regrade that ran but could
not score). Every evaluation is recorded in the `job_checks` table.

Checks read files only: markers, logs, JSON written by the pipeline's own scripts. They never run product code or
tests. `t0` is the job's start (UTC, second precision); a file counts as the job's output when its time is at or
after t0 - SLACK.

    regrade     a new <trial>/regrade-<UTC>/ with REGRADE.json carrying a numeric reward, and verifier/reward.json,
                graded on the current tests (REGRADE.json tests_hash = the content hash of tasks/<slug>/tests/)
    rescore     the same, made by the rescore tool, every --drop name listed in `dropped` and absent from the new
                verifier/results.json
    regate      a gate RESULT line in postbuild.log at or after t0 saying SOUND, the .sound marker (or .hold-repair
                for a held task), and a gate fingerprint written at or after t0 that matches the current files
    build       end_utc.txt at or after t0 and not older than start_utc.txt, and a recorded outcome: a gate marker
                written at or after t0, or a STOP / BUILD-INCOMPLETE / stopped line in the build's logs
    trial_run   runs_<model>.log gained rows at or after t0 for the job's runs (r<first_run> at least, none outside
                first_run .. first_run+max_runs-1); a model held by hold_<model> needs no row
    audit_prep  a <trial>/postmortem-<UTC>/PREPARED.json at or after t0
    audit_record build/audit/ledger.md and trials.tsv rewritten at or after t0
    fairness    FAIRNESS.md written at or after t0, fairness_status.txt says ok, and the review states a verdict
    cleanup     a "pass done" line in build/audit/hourly_cleanup.log at or after t0
    repair      kinds/repair.py: JOB-RESULT.json (result repaired) written after t0 in build/<slug>/repair-inputs-*/,
                the new repair folder with README.md, instruction.md unchanged, .hold-repair kept
    step3, gate no file outcome to check: the exit code decides

Self-checks (`cweq selfcheck`): each grading tool reproduces a known graded run whose tests have not changed since,
on a copy of the run's folder (the real run folder is never written), and must give the same reward. Results go to
the `selfchecks` table; with [checks] refuse_on_failed_selfcheck the dispatcher holds that tool's jobs while the
newest real self-check of the tool failed.
"""
import calendar
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402
sys.path.insert(0, str(paths.COMMON / "fairness"))
sys.path.insert(0, str(paths.COMMON / "gate"))

import markers  # noqa: E402  (task-folder markers: common/markers.py)
import qdb  # noqa: E402

SLACK = 2.0
RESULT_RE = markers.RESULT_RE
STAMP_RE = re.compile(r"^(regrade|postmortem)-(\d{8}T\d{6}Z)$")
RUN_ROW = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\t\S+\treward=(\S+)\t.*\t(\S+)$")
BUILD_STOP = markers.END_LINES
GATE_MARKERS = markers.STATE_FLAGS
TOOLS = {"regrade": "common/audit/regrade_from_code.py", "rescore": "common/audit/rescore_from_results.py"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS job_checks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER NOT NULL,
    checked_at  TEXT NOT NULL,
    verdict     TEXT NOT NULL CHECK (verdict IN ('pass', 'fail', 'person', 'none')),
    failed      TEXT,                          -- the first failing check, e.g. regrade.scored
    detail      TEXT                           -- JSON list of [name, ok, detail]
);
CREATE INDEX IF NOT EXISTS job_checks_job ON job_checks (job_id);
CREATE TABLE IF NOT EXISTS selfchecks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tool        TEXT NOT NULL,                 -- regrade | rescore
    started     TEXT NOT NULL,
    finished    TEXT,
    reference   TEXT,                          -- <job>/<trial> of the reference run
    expected    REAL,
    got         REAL,
    ok          INTEGER,                       -- 1 same reward, 0 differs or the tool failed, NULL dry run
    dry_run     INTEGER NOT NULL DEFAULT 0,
    detail      TEXT
);
"""


def ensure(conn):
    conn.executescript(SCHEMA)


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def read(p):
    try:
        return Path(p).read_text(errors="replace")
    except OSError:
        return ""


def mtime(p):
    try:
        return Path(p).stat().st_mtime
    except OSError:
        return None


def stamp_epoch(name):
    m = STAMP_RE.match(name)
    return calendar.timegm(time.strptime(m.group(2), "%Y%m%dT%H%M%SZ")) if m else None


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def new_dirs(trial, prefix, t0):
    """Folders <trial>/<prefix>-<UTC>/ stamped at or after t0, oldest first."""
    out = []
    for d in sorted(Path(trial).glob(f"{prefix}-*")):
        e = stamp_epoch(d.name)
        if d.is_dir() and e is not None and e >= t0 - SLACK:
            out.append(d)
    return out


# ---------------------------------------------------------------- per-kind checks: list of (name, ok, detail, person)

def _statuses(group):
    """{test name: passed?} from one results.json group (a dict of name -> status or {status})."""
    out = {}
    for k, v in (group or {}).items():
        st = v if isinstance(v, str) else (v or {}).get("status", "") if isinstance(v, dict) else v
        out[k] = st in ("passed", "pass", True)
    return out


def functional_drops(orig_results, new_results):
    """Functional tests that passed in orig_results and do not pass in new_results (names in both)."""
    a, b = jload(orig_results) or {}, jload(new_results) or {}
    before, after = _statuses(a.get("functional")), _statuses(b.get("functional"))
    return sorted(k for k, ok in before.items() if ok and k in after and not after[k])


def c_regrade(task, a, t0, cfg, rescore=False):
    trial = Path(cfg["jobs_dir"]) / a["trial"]
    kind = "rescore" if rescore else "regrade"
    dirs = [d for d in new_dirs(trial, "regrade", t0) if (d / "REGRADE.json").is_file()]
    if not dirs:
        return [(f"{kind}.folder", False, f"no regrade-*/REGRADE.json in {trial.name} since the job started", False)]
    d = dirs[-1]
    info = jload(d / "REGRADE.json") or {}
    out = [(f"{kind}.folder", True, d.name, False)]
    reward = info.get("reward")
    out.append((f"{kind}.scored", is_num(reward), f"REGRADE.json reward = {reward!r}", not is_num(reward)))
    rj = (jload(d / "verifier" / "reward.json") or {}).get("reward")
    out.append((f"{kind}.reward_file", is_num(rj), f"verifier/reward.json reward = {rj!r}", False))
    # Graded on the current tests (by content: the test version reconcile R2 compares). A grading that records no
    # test version (a tool from before 2026-10-28) is not judged here.
    import repairstep
    got, cur = repairstep.regrade_tests_hash(info), repairstep.tests_hash(task)
    out.append((f"{kind}.tests_current", got is None or got == cur,
                f"graded on tests {got or 'unrecorded'}, current {cur}", False))
    if not rescore:
        # Same code, same or repaired tests: a functional test that passed in the original grading and fails
        # in the regrade points at the grading environment (stk-bifrost-19592 2026-10-28: --network none left no
        # local address). Not fatal (a repaired functional test can legitimately change); it becomes an event.
        drops = functional_drops(trial / "verifier" / "results.json", d / "verifier" / "results.json")
        out.append((f"{kind}.functional_kept", not drops,
                    f"passed originally, fail now: {drops[:4]}" if drops else "no functional test lost", False))
    if rescore:
        method = str(info.get("method", ""))
        out.append(("rescore.method", method.startswith("rescore"), method[:60], False))
        dropped = info.get("dropped") or []
        miss = [x for x in a.get("drop", []) if not any(x in y for y in dropped)]
        out.append(("rescore.dropped_listed", not miss, f"not listed: {miss}" if miss else "every drop listed", False))
        res = jload(d / "verifier" / "results.json") or {}
        left = [k for g in ("security", "functional") for k in (res.get(g) or {}) if any(x in k for x in a.get("drop", []))]
        out.append(("rescore.dropped_absent", not left, f"still present: {left[:3]}" if left else "absent", False))
    return out


def last_result(b):
    return markers.last_result(b)


def c_regate(task, a, t0, cfg):
    b = paths.BUILD / task
    ts, text = last_result(b)
    out = [("regate.result", bool(ts and ts >= t0 - SLACK and text and text.startswith("SOUND")),
            f"last RESULT {qdb.utc(ts) if ts else '-'}: {text or '-'}", False)]
    marker = markers.has(b, ".sound") or markers.has(b, ".hold-repair")
    out.append(("regate.marker", marker, "present" if marker else "neither .sound nor .hold-repair", False))
    fp = jload(markers.path(b, "gate_fingerprint.json")) or {}
    w = qdb.parse_utc(fp.get("written_utc"))
    fresh = bool(w and w >= t0 - SLACK)
    current = False
    if fresh:
        try:
            import fingerprint
            current = fp.get("sha256") == fingerprint.digest(task)[0]
        except Exception as e:                          # an unreadable task tree reads as not current
            current, fp["error"] = False, str(e)[:80]
    out.append(("regate.fingerprint", fresh and current,
                f"written {fp.get('written_utc', '-')}, {'matches' if current else 'does not match'} the files", False))
    return out


def c_build(task, a, t0, cfg):
    b = paths.BUILD / task
    end, start = markers.read_text(markers.path(b, "end_utc.txt")).strip(), markers.read_text(markers.path(b, "start_utc.txt")).strip()
    e = qdb.parse_utc(end)
    ended = bool(e and e >= t0 - SLACK and (not start or end >= start))
    out = [("build.ended", ended, f"start {start or '-'} end {end or '-'}", False)]
    marks = [m for m in GATE_MARKERS if (mt := mtime(b / m)) is not None and mt >= t0 - SLACK]
    stop = [s for f in ("stack_pipeline.log", "pipeline.log") for s in BUILD_STOP if s in read(b / f)]
    led = paths.PIPELINES / "sibling" / "out" / "pipeline" / "ledger_deepseek.tsv"
    lane = [l for l in read(led).splitlines() if f"\t{task}\t" in l and (qdb.parse_utc(l.split("\t")[0]) or 0) >= t0 - SLACK]
    outcome = marks or stop or lane
    out.append(("build.outcome", bool(outcome),
                f"markers {marks}" if marks else f"log: {stop[0]}" if stop else f"lane ledger: {lane[-1][:80]}" if lane
                else "no gate marker, STOP or lane ledger row since the job started", not outcome))
    return out


def c_trial(task, a, t0, cfg):
    m = a.get("model", "")
    if markers.model_held(paths.BUILD / task, m):
        return [("trial_run.rows", True, f"hold_{m}: no run expected", False)]
    first, k = int(a.get("first_run", 1)), int(a.get("max_runs", 1))
    want = set(range(first, first + k))
    runs = []
    for line in markers.read_text(markers.runs_log(paths.BUILD / task, m)).splitlines():
        r = RUN_ROW.match(line)
        if not r:
            continue
        ts = calendar.timegm(time.strptime(r.group(1), "%Y-%m-%d %H:%M:%S"))
        n = re.search(rf"-{re.escape(m)}-r(\d+)-", r.group(3))
        if ts >= t0 - SLACK and n:
            runs.append(int(n.group(1)))
    out = [("trial_run.rows", first in runs, f"rows since start for runs {sorted(set(runs)) or '-'}", False)]
    stray = sorted(set(runs) - want)
    out.append(("trial_run.in_range", not stray, f"runs outside {first}..{first + k - 1}: {stray}" if stray
                else f"within {first}..{first + k - 1}", False))
    return out


def c_audit_prep(task, a, t0, cfg):
    trial = Path(cfg["jobs_dir"]) / a["trial"]
    dirs = [d for d in new_dirs(trial, "postmortem", t0) if (d / "PREPARED.json").is_file()]
    return [("audit_prep.prepared", bool(dirs), dirs[-1].name if dirs else "no postmortem-*/PREPARED.json since start",
             False)]


def c_audit_record(task, a, t0, cfg):
    out = []
    for f in ("ledger.md", "trials.tsv"):
        mt = mtime((paths.BUILD / "audit") / f)
        out.append((f"audit_record.{f}", bool(mt and mt >= t0 - SLACK), f"modified {qdb.utc(mt) if mt else '-'}", False))
    return out


def c_fairness(task, a, t0, cfg):
    b = paths.BUILD / task
    mt = mtime(b / "FAIRNESS.md")
    out = [("fairness.review", bool(mt and mt >= t0 - SLACK), f"FAIRNESS.md {qdb.utc(mt) if mt else 'missing'}", False)]
    st = read(b / "fairness_status.txt").strip()
    out.append(("fairness.finished", st.startswith("ok"), f"fairness_status.txt: {st[:60] or '-'}", False))
    try:
        import fairness_verdict
        v, why = fairness_verdict.verdict(task)
    except Exception as e:
        v, why = "ERROR", str(e)[:80]
    out.append(("fairness.verdict", v in ("READY", "NOT_READY"), f"{v} ({why})"[:120], v not in ("READY", "NOT_READY")))
    return out


def c_cleanup(task, a, t0, cfg):
    ok = False
    for line in read((paths.BUILD / "audit") / "hourly_cleanup.log").splitlines():
        if "pass done" in line and (qdb.parse_utc(line.split(" ", 1)[0]) or 0) >= t0 - SLACK:
            ok = True
    return [("cleanup.pass_done", ok, "pass done logged" if ok else "no 'pass done' line since the job started", False)]


def c_lint(task, a, t0, cfg):
    import lintstep
    f = lintstep.out_path(task, a.get("fp", ""))
    mt = mtime(f)
    return [("lint.result", bool(mt and mt >= t0 - SLACK), f"{f.name} {qdb.utc(mt) if mt else 'missing'}", False)]


def check_of(kind):
    """The kind's post-condition check from its declaration (kinds/), or None."""
    import kinds
    kd = kinds.get(kind)
    return kd.check if kd else None


def evaluate(row, cfg):
    """(verdict, failed check or None, [(name, ok, detail)]) for a job, from its start time and the files.
    verdict: pass | fail | person (a failing check that needs a person) | none (no file outcome for this kind)."""
    fn = check_of(row["kind"])
    if fn is None or cfg.get("commands", {}).get(row["kind"]):
        return "none", None, []                        # step3, gate, or a replaced command: the exit code decides
    t0 = qdb.parse_utc(row["started"]) or 0
    try:
        res = fn(row["task"], qdb.args_of(row), t0, cfg)
    except Exception as e:                             # a check that cannot read its inputs is a failed check
        res = [(f"{row['kind']}.readable", False, f"{type(e).__name__}: {e}"[:160], False)]
    bad = [r for r in res if not r[1]]
    if not bad:
        return "pass", None, [r[:3] for r in res]
    return ("person" if any(r[3] for r in bad) else "fail"), bad[0][0], [r[:3] for r in res]


def record(conn, job_id, verdict, failed, items):
    ensure(conn)
    conn.execute("INSERT INTO job_checks (job_id, checked_at, verdict, failed, detail) VALUES (?,?,?,?,?)",
                 (job_id, qdb.utc(), verdict, failed, json.dumps(items)))


def after_done(conn, cfg, job_id, log_path=None):
    """Run the checks of a job the worker just recorded as done. Returns the job's final state."""
    if not cfg.get("checks", {}).get("enabled", True):
        return "done"
    row = qdb.get(conn, job_id)
    verdict, failed, items = evaluate(row, cfg)
    record(conn, job_id, verdict, failed, items)
    if verdict in ("pass", "none"):
        return "done"
    detail = next((d for n, ok, d in items if n == failed), "")
    state = "blocked" if verdict == "person" else "failed"
    qdb.set_state(conn, job_id, state, f"post-condition failed: {failed}: {detail}")
    if log_path:
        try:
            with open(log_path, "a") as f:
                f.write(f"{qdb.utc()} cweq job {job_id}: post-condition {failed} failed ({detail}) -> {state}\n")
        except OSError:
            pass
    return state


# ---------------------------------------------------------------- self-checks of the grading tools

def _tests_changed(slug):
    t = paths.TASKS / slug / "tests"
    return max((p.stat().st_mtime for p in t.rglob("*") if p.exists()), default=0.0) if t.is_dir() else None


def references(cfg, tool, limit=3):
    """Reference runs for a tool, best first: [{"trial": <path>, "rel": job/trial, "expected": reward, ...}].
    regrade: an original grading (no regrade-* yet), saved code present, tests unchanged since it was graded,
             a reward strictly between 0 and 1 (a partial score exercises both test groups).
    rescore: a run whose newest regrade is a rescore, tests unchanged since; replays the same drops. A partial reward
             (strictly between 0 and 1) is preferred: a 0 or a 1 is easier to reproduce by accident."""
    jobs = Path(cfg["jobs_dir"])
    out, weak = [], []                                   # weak: rescore references at 0 or 1 (less telling)
    for t in sorted(jobs.glob("*/*__*"), key=lambda p: mtime(p / "result.json") or 0, reverse=True):
        res = jload(t / "result.json")
        if not res or not (t / "verifier").is_dir():
            continue
        slug = Path(((jload(t / "config.json") or {}).get("task") or {}).get("path", "")).name
        changed = _tests_changed(slug) if slug else None
        if changed is None:
            continue
        regs = sorted(d for d in t.glob("regrade-*") if (d / "REGRADE.json").is_file())
        if tool == "regrade":
            if regs or not ((t / "final-code" / "changes.patch").is_file() or (t / "artifacts").is_dir()):
                continue
            r = ((res.get("verifier_result") or {}).get("rewards") or {}).get("reward")
            graded = qdb.parse_utc(res.get("finished_at")) or mtime(t / "result.json") or 0
            if is_num(r) and 0 < r < 1 and changed < graded:
                out.append({"trial": str(t), "rel": f"{t.parent.name}/{t.name}", "expected": float(r)})
        else:
            if not regs:
                continue
            info = jload(regs[-1] / "REGRADE.json") or {}
            if not str(info.get("method", "")).startswith("rescore") or not is_num(info.get("reward")):
                continue
            if changed < (stamp_epoch(regs[-1].name) or 0) and (t / "verifier" / "results.json").is_file():
                drops = sorted({x.split(":", 1)[1].rsplit("=", 1)[0] for x in info.get("dropped", []) if ":" in x})
                ref = {"trial": str(t), "rel": f"{t.parent.name}/{t.name}", "expected": float(info["reward"]),
                       "drops": drops}
                (out if 0 < ref["expected"] < 1 else weak).append(ref)
        if len(out) >= limit:
            break
    return (out + weak)[:limit]


def _copy_trial(src, work, tool):
    """A private copy of the run folder for the tool (it writes regrade-*/ into the copy, never the real run)."""
    src = Path(src)
    dst = Path(work) / f"{src.name}-selfcheck"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    keep = ["result.json", "config.json", "verifier"] + (["final-code", "artifacts"] if tool == "regrade" else [])
    for name in keep:
        p = src / name
        if p.is_dir():
            shutil.copytree(p, dst / name, symlinks=True)
        elif p.is_file():
            shutil.copy2(p, dst / name)
    return dst


def selfcheck(conn, cfg, tool, run=False, ref=None, out=print):
    """Reproduce a reference run with `tool`. Dry run (default): record and print what would run. Returns the row id."""
    ensure(conn)
    refs = [ref] if ref else references(cfg, tool, limit=1)
    now = qdb.utc()
    if not refs:
        cur = conn.execute("INSERT INTO selfchecks (tool, started, finished, ok, dry_run, detail) VALUES (?,?,?,?,?,?)",
                           (tool, now, now, None, int(not run), "no reference run found"))
        out(f"{tool}: no reference run found")
        return cur.lastrowid
    r = refs[0]
    if not run:
        cur = conn.execute("INSERT INTO selfchecks (tool, started, finished, reference, expected, dry_run, detail)"
                           " VALUES (?,?,?,?,?,1,?)", (tool, now, now, r["rel"], r["expected"],
                                                        f"would run {TOOLS[tool]} on a copy of {r['rel']}"))
        out(f"{tool}: would reproduce {r['rel']} (expected reward {r['expected']}) with {TOOLS[tool]} on a private copy")
        return cur.lastrowid
    work = Path(cfg.get("checks", {}).get("selfcheck_dir", "~/.tb-graders/cwe/selfcheck")).expanduser()
    copy = _copy_trial(r["trial"], work, tool)
    if tool == "regrade":
        argv = [sys.executable, "-I", str(paths.COMMON.parent / TOOLS[tool]), str(copy), "selfcheck: reproduce a known grading"]
    else:
        argv = [sys.executable, "-I", str(paths.COMMON.parent / TOOLS[tool]), str(copy),
                *[x for d in r["drops"] for x in ("--drop", d)], "--why", "selfcheck: reproduce a known rescore"]
    cur = conn.execute("INSERT INTO selfchecks (tool, started, reference, expected, dry_run) VALUES (?,?,?,?,0)",
                       (tool, now, r["rel"], r["expected"]))
    sid = cur.lastrowid
    p = subprocess.run(argv, cwd=str(paths.ROOT), capture_output=True, text=True)
    regs = sorted(d for d in copy.glob("regrade-*") if (d / "REGRADE.json").is_file())
    got = (jload(regs[-1] / "REGRADE.json") or {}).get("reward") if regs else None
    ok = int(p.returncode == 0 and is_num(got) and abs(float(got) - r["expected"]) < 1e-6)
    detail = f"exit {p.returncode}; " + (p.stdout + p.stderr).strip().splitlines()[-1][:200] if (p.stdout + p.stderr).strip() \
        else f"exit {p.returncode}"
    conn.execute("UPDATE selfchecks SET finished=?, got=?, ok=?, detail=? WHERE id=?",
                 (qdb.utc(), got if is_num(got) else None, ok, detail, sid))
    out(f"{tool}: reproduced {r['rel']}: expected {r['expected']}, got {got} -> {'OK' if ok else 'FAILED'}")
    if ok:
        shutil.rmtree(copy, ignore_errors=True)
    return sid


def tool_refused(conn, kind, cfg):
    """Why the dispatcher holds a regrade/rescore job (the newest real self-check of the tool failed), or None."""
    if kind not in TOOLS or not cfg.get("checks", {}).get("refuse_on_failed_selfcheck", True):
        return None
    ensure(conn)
    row = conn.execute("SELECT * FROM selfchecks WHERE tool=? AND dry_run=0 AND finished IS NOT NULL ORDER BY id DESC"
                       " LIMIT 1", (kind,)).fetchone()
    if row is None or row["ok"] is None or row["ok"]:
        return None
    return (f"the {kind} tool failed its self-check #{row['id']} ({row['reference']}: expected {row['expected']}, "
            f"got {row['got']}); run `cweq selfcheck --tool {kind} --run` again once fixed")


def verify_past(conn, cfg, where="state='done'", params=(), out=print):
    """Evaluate the checks of finished jobs without changing them (a read-only audit of past work)."""
    counts, bad = {}, []
    for row in qdb.jobs(conn, where, params):
        if not row["started"]:
            continue
        v, failed, items = evaluate(row, cfg)
        counts[(row["kind"], v)] = counts.get((row["kind"], v), 0) + 1
        if v in ("fail", "person"):
            bad.append((row, v, failed, next((d for n, ok, d in items if n == failed), "")))
    for (k, v), n in sorted(counts.items()):
        out(f"  {k:<13} {v:<7} {n}")
    for row, v, failed, d in bad:
        out(f"  #{row['id']} {row['kind']} {row['task']} {v}: {failed}: {d}")
    return counts, bad
