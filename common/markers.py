#!/usr/bin/env python3
"""The task-folder markers: one place that names them, says what they mean, who writes and who reads them, and
reads or writes them. Every pipeline stage reads and writes build/<slug>/ through these names (contracts:
common/stage_contracts.toml, docs/STAGE-CONTRACTS.md; shell twin: common/markers.sh).

    python3 common/markers.py check SLUG [SLUG ...]   contract violations of task folders (read-only)
    python3 common/markers.py check --all [--json]     every build/<slug>/ folder
    python3 common/markers.py table                    the marker table as Markdown (docs/STAGE-CONTRACTS.md)

Paths are resolved at call time from paths.BUILD, so tests and tools that point paths at another tree work.
Functions that take a folder `b` (a Path) work on any build folder; the slug-based ones use paths.BUILD.
"""
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402


@dataclass(frozen=True)
class Marker:
    name: str          # file name inside build/<slug>/ ({model} for per-model markers)
    kind: str          # flag (empty file) | record (content) | log | folder
    meaning: str
    writers: str
    readers: str


MARKERS = {m.name: m for m in (
    # ---- gate verdict (gate_one_ds.sh writes exactly one; postbuild.sh / regate.sh finish it)
    Marker(".sound", "flag", "The task gated SOUND on its current files and is ready for trials.",
           "common/gate/gate_one_ds.sh (on pass), common/gate/postbuild.sh and regate.sh (final), a listing waiver",
           "taskstate.py, scale_queue.py, phase3/4, trial launchers, status_report.py"),
    Marker(".unsound", "flag", "A gate stage failed on the task itself (deterministic). No trials.",
           "common/gate/gate_one_ds.sh", "taskstate.py, scale_queue.py, reconcile.py"),
    Marker(".gate_error", "flag", "The gate kept failing on infrastructure; not a task verdict.",
           "common/gate/gate_one_ds.sh", "taskstate.py, scale_queue.py, reconcile.py"),
    Marker(".gate_passed", "flag", "The gate passed but the post-gate steps (blind patch, fingerprint, listing) have not "
           "finished; trials must not start yet. Left behind only when a post-build or re-gate stopped early.",
           "common/gate/postbuild.sh, regate.sh", "taskstate.py, scale_queue.py, reconcile.py"),
    Marker(".listing_fail", "flag", "Stacking only: the instruction lists hidden traps after the allowed rewrites; "
           "not sound unless LISTING_WAIVER.md says otherwise.",
           "common/gate/postbuild.sh, regate.sh", "taskstate.py, scale_queue.py, inbox.py"),
    Marker(".listing_warn", "flag", "Stacking only: listing check failed while enforcement was advisory.",
           "common/gate/postbuild.sh, regate.sh", "people"),
    Marker(".blind_fail", "flag", "The blind fix's patch did not pass; kept as checks/blind.failed.patch. Not blocking.",
           "common/gate/postbuild.sh, regate.sh", "people, lint"),
    Marker("gate_fingerprint.json", "record", "What the last SOUND gate covered (sha256 of tests, solution, "
           "environment, checks); a different digest means the gate is stale.",
           "common/gate/fingerprint.py write (via gate_one_ds.sh / postbuild.sh / regate.sh)",
           "run_trial.sh, regrade tools, taskstate.py, reconcile.py, phase3.py"),
    Marker("postbuild.log", "log", "Post-build and re-gate log; its last `RESULT:` line is the gate outcome.",
           "common/gate/postbuild.sh, regate.sh, repair and waiver steps", "reconcile.py, checks.py, people"),
    # ---- repair and holds
    Marker(".hold-repair", "flag", "A test repair is between its edit and its regrades: no new trials of the task. "
           "Its text says who holds it; `repair failed ...` keeps it for a person.",
           "repair steps (the queue's repair job, people), the queue after a held re-gate; lifted by reconcile R6",
           "taskstate.py, dispatch.py, scale_queue.py, phase4.py, reconcile.py (R6)"),
    Marker("hold_{model}", "flag", "No new runs of this model on this task. When its text says the model was blocked "
           "(or {MODEL}-BLOCKED.md exists), the ledger shows that model as blocked.", "people",
           "common/trial/run_trial.sh, trial.py, phase3.py, dispatch.py"),
    Marker("repaired-tests-*", "folder", "Originals (*.orig) and README.md of tests changed by a repair.",
           "repair steps", "reconcile.py (R1-R4), people"),
    Marker("removed-tests-*", "folder", "Originals and README.md of tests removed by a repair.",
           "repair steps", "reconcile.py (R1-R4), people"),
    Marker("history", "folder", "Records of the steps after the build (fairfix, upgrade, test repair, regrade), one "
           "file each (<YYYYMMDD>-<kind>.md), so notes.md keeps build facts only (2026-10-28).",
           "fairfix and upgrade agents, repair steps, people", "people (never the fairness reviewer or the auditor)"),
    Marker("notes.for-review.md", "record", "The build notes without earlier conclusions, regenerated before each "
           "fairness review (common/util/notes_filter.py); the reviewer reads it instead of notes.md.",
           "pipelines/sibling/9-fairness, pipelines/stacking/7-fairness", "the fairness reviewer"),
    Marker("testfix-*", "folder", "An older test repair's record (originals and notes); counts as a repair for the "
           "lost-repair check and for repair coverage.", "repair steps (before 2026-10-26)",
           "repairstep.py (coverage, lost repairs), people"),
    Marker("repair-inputs-*", "folder", "One queue repair job: FINDING.md/.json, INPUTS.md, runs/ (the failing runs' "
           "evidence), backup/, OUTCOME.json (the agent), JOB-RESULT.json (the job), failed/ (a reverted repair).",
           "common/queue/repairjob.py", "the repair agent, kinds/repair.py check, repairstep.py, people"),
    Marker("repair_status.txt", "record", "Whether the last repair agent run finished (`ok` or `error: ...`).",
           "pipelines/sibling/10-fairfix/run_repair_agent.sh", "common/queue/repairjob.py"),
    Marker("fairness_tests.json", "record", "The content hash of tests/ the last queued fairness review was shown; a "
           "different hash makes the review stale (phase4 rule F1).", "the fairness job (phase4.command)",
           "phase4.py"),
    # ---- build
    Marker("BUILD-PROMPT.md", "record", "The builder's prompt for this task.", "common/builder/build_prepare.py",
           "common/launch/run_build.sh, phase3.py"),
    Marker("start_utc.txt", "record", "UTC start of the last build.", "common/launch/run_build.sh",
           "taskstate.py, scale_queue.py"),
    Marker("end_utc.txt", "record", "UTC end of the last build (written when the builder exits, whatever the outcome).",
           "common/launch/run_build.sh, resume_pipeline.sh", "taskstate.py, scale_queue.py, orphan_builder_guard.sh"),
    Marker("build-exit.txt", "record", "Exit code of the last builder run.", "common/launch/run_build.sh",
           "run_pipeline.sh, run_stack_pipeline.sh, checks.py"),
    Marker("resume_start_utc.txt", "record", "UTC start of the last resumed builder session (resume_pipeline.sh).",
           "pipelines/sibling/6-build/resume_pipeline.sh", "common/util/agent_status.py, markers.build_paused"),
    Marker("build_status.json", "record", "agent_status.py details of the last builder run (exit code, result, "
           "wall_sec / limit_sec / paused_interrupt for an exit 124).", "common/util/agent_status.py (via the build "
           "pipelines)", "markers.build_paused, people"),
    Marker("pipeline.log", "log", "Sibling build log; STOP / BUILD-INCOMPLETE / stopped/failed lines end a build.",
           "pipelines/sibling/6-build/run_pipeline.sh", "taskstate.py, scale_queue.py"),
    Marker("stack_pipeline.log", "log", "Stacking build log; same end lines as pipeline.log.",
           "pipelines/stacking/3-build-gate/run_stack_pipeline.sh", "taskstate.py, scale_queue.py"),
    # ---- trials
    Marker("runs_{model}.log", "log", "One line per run of the current task version (`reward=`), moved away with each "
           "new version.", "common/trial/trial.py", "common/trial/trial_state.py, taskstate.py"),
    # ---- review, decision, delivery
    Marker("FAIRNESS.md", "record", "The fairness review; its GATE_A line is the verdict, its CONFLICTS line the tests "
           "that disagree with the instruction (since 2026-10-28).",
           "pipelines/sibling/9-fairness, pipelines/stacking/7-fairness", "common/fairness/fairness_verdict.py, inbox.py, "
           "delivery.py, export_delivery.py"),
    Marker("fairness_status.txt", "record", "Whether the last fairness run finished (`ok ...`).",
           "pipelines/sibling/9-fairness, pipelines/stacking/7-fairness", "common/fairness/fairness_verdict.py"),
    Marker("HUMAN-DECISION.md", "record", "The owner's decision (DECISION: KEEP|REPAIR|DROP, DATE:), the ruling on "
           "deciding conflicts (CONFLICTS-RULED: <date> <KEEP|DROP|REPAIR> <reason>), client-audit outcomes "
           "(CLIENT-AUDIT:) and, after a delivery, a DELIVERED: line.", "people; `cweq delivered`", "fairness_verdict.py, taskstate.py, "
           "delivery.py, inbox.py"),
    Marker("LISTING_WAIVER.md", "record", "The owner's decision to trial a stacking task despite the listing check.",
           "people", "people, this checker"),
    Marker("lint", "folder", "Task-quality lint results, one JSON per gate version.", "common/queue/lintstep.py",
           "cweq explain, inbox.py"),
)}

VERDICT_FLAGS = (".sound", ".unsound", ".gate_error")
STATE_FLAGS = (".sound", ".unsound", ".gate_error", ".listing_fail", ".gate_passed", ".hold-repair")
END_LINES = ("STOP:", "BUILD-INCOMPLETE", "stopped/failed")
RESULT_RE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) \S+ RESULT: (.*)$")
DECISION_RE = re.compile(r"(?mi)^\s*DECISION\s*:\s*(KEEP|REPAIR|DROP)\b")
DATE_RE = re.compile(r"(?mi)^\s*DATE\s*:\s*(\d{4}-\d{2}-\d{2})")
DELIVERED_RE = re.compile(r"(?mi)^\s*DELIVERED\s*:\s*(.+)$")
# Owner rulings added by the client audit PO-3 (2026-10-28), both in HUMAN-DECISION.md:
#   CONFLICTS-RULED: <YYYY-MM-DD> <KEEP|DROP|REPAIR> <short reason>   the ruling on the review's deciding conflicts
#   CLIENT-AUDIT: WITHDRAW | KEEP (confirmed) | KEEP, CONFIDENCE: THIN | ...   a client-audit section's outcome
CONFLICTS_RULED_LINE = re.compile(r"(?mi)^\s*CONFLICTS-RULED\s*:(.*)$")
CONFLICTS_RULED_RE = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})\s+(KEEP|DROP|REPAIR)\b\s*[-:;,]?\s*(\S.*)$", re.I)
CLIENT_AUDIT_RE = re.compile(r"(?mi)^\s*CLIENT-AUDIT\s*:\s*(.+)$")


# ---------------------------------------------------------------- paths and raw access

def folder(slug):
    return Path(paths.BUILD) / slug


def path(b, name, model=None):
    """build folder `b` + a marker name (fills {model})."""
    return Path(b) / (name.format(model=model) if model else name)


def read_text(p):
    try:
        return Path(p).read_text(errors="replace")
    except OSError:
        return ""


def has(b, name, model=None):
    return path(b, name, model).exists()


def flags(b, names=STATE_FLAGS):
    """The state flags present in folder b, sorted."""
    return sorted(n for n in names if (Path(b) / n).exists())


def write_atomic(p, text):
    """Write a file so readers see either the old or the new content, never a half-written one."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def touch(b, name, model=None):
    p = path(b, name, model)
    if not p.exists():
        write_atomic(p, "")
    return p


def remove(b, *names):
    for n in names:
        try:
            (Path(b) / n).unlink()
        except FileNotFoundError:
            pass


def set_gate_verdict(b, flag):
    """Exactly one of .sound / .unsound / .gate_error (gate_one_ds.sh's rule)."""
    if flag not in VERDICT_FLAGS:
        raise ValueError(flag)
    remove(b, *(f for f in VERDICT_FLAGS if f != flag))
    touch(b, flag)


# ---------------------------------------------------------------- readers (behaviour of the original call sites)

def build_started(b):
    b = Path(b)
    return any((b / f).exists() for f in ("start_utc.txt", "stack_pipeline.log", "pipeline.log", "manifest.json"))


def build_done(b):
    """True when the task needs no (more) build work: sound, held, waiting for a re-gate, ended or stopped
    (scale_queue.py build_done, taskstate.build_done)."""
    b = Path(b)
    if any((b / m).is_file() for m in (".sound", ".listing_fail", ".hold-repair", ".gate_passed")):
        return True
    end, start = b / "end_utc.txt", b / "start_utc.txt"
    if end.is_file() and (not start.is_file() or read_text(end).strip() >= read_text(start).strip()):
        return True
    if any((b / m).is_file() for m in (".unsound", ".gate_error")):
        return True
    for logf in ("stack_pipeline.log", "pipeline.log"):
        t = read_text(b / logf)
        if any(x in t for x in END_LINES):
            return True
    return False


PAUSED_FACTOR = 1.25          # common/util/agent_status.py LATE_FACTOR


def _utc_epoch(p):
    from datetime import datetime
    try:
        return datetime.fromisoformat(read_text(p).strip().replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def build_paused(b, limit=None):
    """True when the last builder run ended with exit 124 long after its limit (> 25 %): it was paused (SIGSTOP) and
    its overdue timer fired on resume, so the build is resumable, not finished. Read from build_status.json
    (paused_interrupt) when agent_status recorded it, else from the start / resume_start / end records."""
    b = Path(b)
    if read_text(b / "build-exit.txt").strip() != "124":
        return False
    try:
        st = json.loads(read_text(b / "build_status.json") or "{}")
    except ValueError:
        st = {}
    if st.get("paused_interrupt") is True:
        return True
    starts = [t for t in (_utc_epoch(b / "start_utc.txt"), _utc_epoch(b / "resume_start_utc.txt")) if t is not None]
    end = _utc_epoch(b / "end_utc.txt")
    if not starts or end is None or end < max(starts):
        return False
    lim = float(limit if limit is not None else st.get("limit_sec") or os.environ.get("BUILD_TIMEOUT") or 18000)
    return end - max(starts) > PAUSED_FACTOR * lim


def last_result(b):
    """(epoch, text) of the last `RESULT:` line in postbuild.log, or (None, None)."""
    from datetime import datetime
    ts = text = None
    for line in read_text(Path(b) / "postbuild.log").splitlines():
        m = RESULT_RE.match(line)
        if m:
            ts = datetime.fromisoformat(m.group(1).replace("Z", "+00:00")).timestamp()
            text = m.group(2)
    return ts, text


def fingerprint_sha(b):
    """The sha256 recorded by the last SOUND gate, or None."""
    try:
        return json.loads((Path(b) / "gate_fingerprint.json").read_text()).get("sha256") or None
    except (OSError, ValueError):
        return None


def human_decision(b, fairness_mtime_date=None):
    """(decision, date, stale) from HUMAN-DECISION.md, or None (fairness_verdict.human_decision).
    stale: the decision is dated before FAIRNESS.md was last written."""
    b = Path(b)
    t = read_text(b / "HUMAN-DECISION.md")
    d, dt = DECISION_RE.search(t), DATE_RE.search(t)
    if not d:
        return None
    fair = b / "FAIRNESS.md"
    stale = False
    if dt and fair.is_file():
        import datetime as _dt
        stale = dt.group(1) < _dt.datetime.fromtimestamp(fair.stat().st_mtime, _dt.timezone.utc).strftime("%Y-%m-%d")
    return d.group(1).upper(), (dt.group(1) if dt else "undated"), stale


def _fairness_day(b):
    import datetime as _dt
    fair = Path(b) / "FAIRNESS.md"
    return _dt.datetime.fromtimestamp(fair.stat().st_mtime, _dt.timezone.utc).strftime("%Y-%m-%d") \
        if fair.is_file() else None


def conflicts_ruled(b):
    """(ruling, date, reason, stale) from the LAST well-formed `CONFLICTS-RULED:` line of HUMAN-DECISION.md, or None.
    stale: dated before FAIRNESS.md was last written (the same per-day rule as human_decision)."""
    lines = CONFLICTS_RULED_LINE.findall(read_text(Path(b) / "HUMAN-DECISION.md"))
    for rest in reversed(lines):
        m = CONFLICTS_RULED_RE.match(rest)
        if m:
            day = _fairness_day(b)
            return m.group(2).upper(), m.group(1), m.group(3).strip(), bool(day and m.group(1) < day)
    return None


def client_audit(b):
    """Every `CLIENT-AUDIT:` value in HUMAN-DECISION.md, in file order (e.g. ['WITHDRAW'], ['KEEP, CONFIDENCE: THIN'])."""
    return [v.strip() for v in CLIENT_AUDIT_RE.findall(read_text(Path(b) / "HUMAN-DECISION.md"))]


CONFIDENCE_RE = re.compile(r"(?mi)\bCONFIDENCE\s*:\s*(high|medium|low|thin)\b")
BLOCKED_HOLD_RE = re.compile(r"(?i)\bblocked\b")


def confidence(b):
    """The breaker's confidence label (high | medium | low | thin) from HUMAN-DECISION.md, or None. A `CONFIDENCE:`
    line or one inside a `CLIENT-AUDIT: KEEP, CONFIDENCE: THIN` line; the last one in the file wins."""
    hits = CONFIDENCE_RE.findall(read_text(Path(b) / "HUMAN-DECISION.md"))
    return hits[-1].lower() if hits else None


def blocked(b, model):
    """Why `model` is blocked on this task (the provider refused it: content filter, safety classifier, repeated
    truncation stops), or None. Blocked = a <MODEL>-BLOCKED.md record, or a hold_<model> whose text says blocked;
    a hold for another reason (a pause, a solve elsewhere) is not a block."""
    b = Path(b)
    for f in b.glob("*-BLOCKED.md") if b.is_dir() else ():
        if f.name.upper() == f"{model.upper()}-BLOCKED.MD":
            return f.name
    hold = path(b, "hold_{model}", model)
    if hold.exists() and BLOCKED_HOLD_RE.search(read_text(hold)):
        return hold.name
    return None


def delivered_line(b):
    m = DELIVERED_RE.search(read_text(Path(b) / "HUMAN-DECISION.md"))
    return m.group(1).strip() if m else ""


def repairs(b):
    """The task's repair folders: repaired-tests-*, removed-tests-*, and the older testfix-* (a repair too)."""
    b = Path(b)
    return (sorted(p.name for p in b.glob("repaired-tests-*")) + sorted(p.name for p in b.glob("removed-tests-*"))
            + sorted(p.name for p in b.glob("testfix-*")))


def runs_log(b, model):
    return Path(b) / f"runs_{model}.log"


def model_held(b, model):
    return (Path(b) / f"hold_{model}").exists()


# ---------------------------------------------------------------- contract checker

def check(slug, b=None, fp_digest=None):
    """Contract violations of one task folder: list of (severity, code, message). Read-only.
    fp_digest: a function slug -> current gate digest (default common/gate/fingerprint.digest)."""
    b = Path(b) if b else folder(slug)
    out = []
    if not b.is_dir():
        return [("error", "no-folder", f"{b} does not exist")]
    f = set(flags(b, STATE_FLAGS + (".listing_warn", ".blind_fail")))
    waiver = (b / "LISTING_WAIVER.md").is_file()

    verdicts = [x for x in VERDICT_FLAGS if x in f]
    if len(verdicts) > 1:
        out.append(("error", "verdict-not-exclusive", f"gate verdict flags together: {' '.join(verdicts)}"))
    if ".listing_fail" in f and ".sound" in f and not waiver:
        out.append(("error", "listing-fail-and-sound", ".listing_fail and .sound without LISTING_WAIVER.md"))
    if ".gate_passed" in f and ".sound" in f:
        out.append(("warn", "gate-passed-and-sound", ".gate_passed left next to .sound"))
    elif ".gate_passed" in f:
        out.append(("warn", "gate-passed-left", ".gate_passed without a result: a post-build or re-gate stopped "
                    "between the gate and its RESULT (unless one is running now)"))

    sha = fingerprint_sha(b)
    if ".sound" in f:
        if sha is None and not (b / "gate_fingerprint.json").exists():
            out.append(("info", "sound-legacy", ".sound without gate_fingerprint.json (gated before fingerprints)"))
        elif sha is None:
            out.append(("error", "fingerprint-unreadable", "gate_fingerprint.json is unreadable"))
        else:
            try:
                digest = (fp_digest or _fingerprint_digest)(slug)
            except Exception as e:                       # an unreadable task tree counts as changed
                digest = f"error: {type(e).__name__}"
            if digest != sha:
                out.append(("error", "sound-stale", ".sound but the task's files changed since the SOUND gate "
                            "(fingerprint stale): re-gate before any trial"))
    elif sha is not None and ".hold-repair" not in f and ".gate_passed" not in f:
        out.append(("warn", "fingerprint-orphan", "gate_fingerprint.json without .sound/.hold-repair "
                    "(gate_one_ds.sh removes it on a non-sound result)"))

    ts, text = last_result(b)
    if text is not None:
        sound_result = text.startswith("SOUND")
        if sound_result and not (f & {".sound", ".hold-repair"}):
            out.append(("warn", "result-sound-no-marker", f"last RESULT is SOUND but no .sound/.hold-repair "
                        f"(markers: {' '.join(sorted(f)) or 'none'})"))
        if ".sound" in f and not sound_result and not waiver:
            out.append(("warn", "sound-but-result-not-sound", f"`.sound` but the last RESULT says: {text[:80]}"))

    start, end = b / "start_utc.txt", b / "end_utc.txt"
    if end.is_file() and not start.is_file():
        out.append(("warn", "end-without-start", "end_utc.txt without start_utc.txt"))
    elif end.is_file() and read_text(end).strip() < read_text(start).strip():
        out.append(("info", "build-running-or-cut", "start_utc.txt is newer than end_utc.txt (a build is running, "
                    "or the last one was cut before it ended)"))

    hd_text = read_text(b / "HUMAN-DECISION.md")
    if hd_text:
        d, dt = DECISION_RE.search(hd_text), DATE_RE.search(hd_text)
        if not d:
            out.append(("error", "decision-unparseable", "HUMAN-DECISION.md has no `DECISION: KEEP|REPAIR|DROP` line"))
        elif not dt:
            out.append(("warn", "decision-undated", "HUMAN-DECISION.md has no `DATE:` line"))
        if DELIVERED_RE.search(hd_text) and not (d and d.group(1).upper() == "KEEP"):
            out.append(("error", "delivered-without-keep", "DELIVERED line but the decision is not KEEP"))
        bad = [r for r in CONFLICTS_RULED_LINE.findall(hd_text) if not CONFLICTS_RULED_RE.match(r)]
        if bad:
            out.append(("error", "conflicts-ruled-unparseable", "CONFLICTS-RULED line is not "
                        "`CONFLICTS-RULED: <YYYY-MM-DD> <KEEP|DROP|REPAIR> <short reason>`: " + bad[0].strip()[:80]))

    reps = repairs(b)
    for r in reps:
        if not (b / r / "README.md").is_file():
            out.append(("warn", "repair-without-readme", f"{r}/ has no README.md"))
    if ".hold-repair" in f and not reps:
        out.append(("warn", "hold-without-repair", ".hold-repair but no repaired-tests-*/removed-tests-* folder"))
    for h in sorted(b.glob("hold_*")):
        out.append(("info", "model-held", f"{h.name}: new runs of that model are held"))
    if ".blind_fail" in f:
        out.append(("info", "blind-fail", "the blind patch did not pass (kept as checks/blind.failed.patch)"))
    if waiver and ".listing_fail" in f:
        out.append(("info", "listing-waived", "listing check failed; owner waiver on record (LISTING_WAIVER.md)"))
    return out


def _fingerprint_digest(slug):
    sys.path.insert(0, str(Path(paths.COMMON) / "gate"))
    import fingerprint
    return fingerprint.digest(slug)[0]


def all_slugs():
    b = Path(paths.BUILD)
    return sorted(p.name for p in b.iterdir() if p.is_dir() and p.name not in ("audit", "pipeline")) if b.is_dir() else []


def table():
    rows = ["| Marker | Kind | Meaning | Written by | Read by |", "|---|---|---|---|---|"]
    for m in MARKERS.values():
        rows.append(f"| `{m.name}` | {m.kind} | {m.meaning} | {m.writers} | {m.readers} |")
    return "\n".join(rows)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="markers.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("slugs", nargs="*")
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--min", choices=("info", "warn", "error"), default="info", help="lowest severity shown")
    sub.add_parser("table")
    a = ap.parse_args(argv)
    if a.cmd == "table":
        print(table())
        return 0
    slugs = all_slugs() if a.all else a.slugs
    if not slugs:
        ap.error("give one or more slugs, or --all")
    rank = {"info": 0, "warn": 1, "error": 2}
    res, worst = {}, 0
    for s in slugs:
        v = [x for x in check(s) if rank[x[0]] >= rank[a.min]]
        res[s] = v
        worst = max([worst] + [rank[x[0]] for x in v])
    if a.json:
        print(json.dumps({s: [dict(zip(("severity", "code", "message"), x)) for x in v] for s, v in res.items()},
                         indent=1))
    else:
        for s, v in res.items():
            if v or not a.all:
                print(s + ("" if v else ": ok"))
                for sev, code, msg in v:
                    print(f"  {sev:<5} {code:<28} {msg}")
    return 2 if worst == 2 else 0


if __name__ == "__main__":
    sys.exit(main())
