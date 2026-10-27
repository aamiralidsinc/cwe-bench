"""Phase 4 rules: audit preparation and recording, fairness reviews, the hourly cleanup and router step 3.

They replace pipelines/router/auto_advance.sh (run on every heartbeat) and the separate
`common/util/hourly_cleanup.sh loop`, with the same commands and the same selections, plus the skips noted below.

  A1 audit_prep    every run listed in build/audit/awaiting_audit.tsv (audit_results.py: a graded run that counts
                   toward a verdict and lacks a current audit) gets its evidence folder prepared
                   (`common/audit/postmortem.py prepare <trial>`), keyed by the grading it will audit.
                   Skipped, as in auto_advance: tasks the ledger marks "rejected (both solved)".
                   Skipped, new: tasks held for a repair (.hold-repair) or busy with a re-gate/regrade/repair script
                   (their grading is about to change), and runs of a model that already SOLVED the task in the
                   ledger (an audit cannot change that model's verdict; e.g. oauth-s2 MiMo).
                   A prepared folder that is still waiting for its auditor is not prepared again; one prepared for an
                   older grading (a regrade came after it) is replaced by a new one (auto_advance reused it).
     audit_ready   every pass rewrites pipelines/router/out/queue/audit_ready.txt with the prepared folders waiting
                   for an auditor (the orchestrator's Opus sub-agents read it; audits are never run by a CLI).
  A2 audit_record  when an auditor's verdict.json is not recorded yet, or a trial result / regrade is newer than the
                   ledger: `postmortem.py record-ready` then `audit_results.py` (one at a time; keyed by the newest
                   input, so the same state never runs twice).
  F1 fairness      a batch task the ledger marks BREAKER candidate, with no FAIRNESS.md newer than its newest trial
                   job folder and no review running: `common/launch/drive.sh deepseek bash <review script> <slug>`
                   with output to build/<slug>/fairness.nohup (stacking: 7-fairness/run_fairness_stack.sh; sibling:
                   9-fairness/run_fairness.sh), exactly as auto_advance. New: never for held or busy tasks.
  C1 cleanup       one job per UTC hour: `common/util/hourly_cleanup.sh once` (never two at once; it runs in its own
                   worker, so its long dangling-image removal holds no other kind's slot). Not while the old
                   `hourly_cleanup.sh loop` still runs. A queued job of an earlier hour is superseded.
  S3 step3         one job per UTC half hour: router step 3 routes stacked tasks any model solved into the general
                   sibling pool (pipelines/router/out/step2/screener) and refreshes the pool file when something
                   new was routed. It never prepares or selects: the general ranking decides what is built.

Job kinds without a task use pseudo tasks: _ledger (audit_record), _machine (cleanup), _router (step3).
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import procs  # noqa: E402
import qdb  # noqa: E402
import taskstate  # noqa: E402
from taskstate import paths  # noqa: E402
import markers  # noqa: E402  (task-folder markers: common/markers.py; on sys.path via taskstate)

KINDS = ("audit_prep", "audit_record", "fairness", "cleanup", "step3")
LEDGER, MACHINE, ROUTER = "_ledger", "_machine", "_router"
JOB_RE = re.compile(r"^(?P<task>.+?)-(?P<model>deepseek|mimo)-r[0-9]+-")
READY_FILE = Path("pipelines/router/out/queue/audit_ready.txt")
FAIRNESS_SCRIPT = {"stk": "pipelines/stacking/7-fairness/run_fairness_stack.sh",
                   "sibling": "pipelines/sibling/9-fairness/run_fairness.sh"}
# Step 3 routes solved stacked tasks into the general sibling pool and refreshes the pool file; it never prepares
# or selects (owner rule 2026-10-27: they are ranked with every other sibling candidate).
STEP3_SH = (
    'L=pipelines/router/out/queue/auto_advance.log; '
    'O=$(python3 -I pipelines/router/route.py step3 2>&1); '
    'echo "$O" | grep -E "^step 3|wait for a screen" >> $L; '
    'if echo "$O" | grep -qE "^step 3: [1-9][0-9]* newly routed"; '
    'then python3 -I pipelines/router/route.py pool 2>&1 | grep -E "^general pool" >> $L; fi; true')


def _json(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def awaiting():
    """[(job, trial)] from build/audit/awaiting_audit.tsv (what `postmortem.py pending` reads)."""
    f = paths.BUILD / "audit" / "awaiting_audit.tsv"
    rows = []
    try:
        lines = f.read_text().splitlines()
    except OSError:
        return rows
    if not lines:
        return rows
    head = lines[0].split("\t")
    for line in lines[1:]:
        cells = dict(zip(head, line.split("\t")))
        if cells.get("job") and cells.get("trial"):
            rows.append((cells["job"], cells["trial"]))
    return rows


def grading_name(trial):
    """postmortem.grading_dir(): the newest regrade-* with a verifier folder, else 'original'."""
    regs = sorted(p for p in trial.glob("regrade-*") if (p / "verifier").is_dir())
    return regs[-1].name if regs else "original"


def postmortem_state(trial, grading):
    """('ready', folder) waiting for its auditor on the current grading; ('recording', folder) verdict written, not
    recorded; ('none', None) nothing usable (no folder, a recorded one, or one prepared for an older grading)."""
    pms = sorted(trial.glob("postmortem-*/"))
    if not pms:
        return "none", None
    pm = pms[-1]
    if (pm / "POSTMORTEM.json").exists():
        return "none", None
    if (pm / "verdict.json").exists():
        return "recording", pm
    prep = _json(pm / "PREPARED.json") or {}
    if prep.get("grading_audited", "original") != grading:
        return "none", None                              # prepared before a regrade: audit the grading now in use
    return "ready", pm


def held_or_busy(slugs, cfg, proc_list, ctx):
    """{slug: why} for tasks whose grading is about to change."""
    out = {}
    for s in slugs:
        if markers.has(paths.BUILD / s, ".hold-repair"):
            out[s] = "held for a repair (.hold-repair)"
    for s, runs in ctx["running"].items():
        kinds = {k for k, _m, _p in runs}
        if s in slugs and kinds & {"regate", "repair"}:
            out.setdefault(s, "re-gate or repair running")
    busy = procs.busy_tasks(set(slugs), cfg["busy"]["patterns"], proc_list, skip_dirs=(paths.COMMON,))
    for s, ps in busy.items():
        out.setdefault(s, f"busy (pid {ps[0][0]})")
    return out


def audit_plan(cfg, ctx, proc_list):
    """(jobs [{kind, task, args}], ready folders [Path], notes [str])."""
    jobs, ready, notes = [], [], []
    rows = awaiting()
    tasks = {}
    for job, trial in rows:
        m = JOB_RE.match(job)
        tasks[(job, trial)] = (m.group("task"), m.group("model")) if m else (trial.split("__")[0], "")
    hb = held_or_busy({t for t, _m in tasks.values()}, cfg, proc_list, ctx)
    led = ctx["ledger"]
    for job, trial in rows:
        task, model = tasks[(job, trial)]
        lrow = led.get(task, {})
        if "rejected (both solved)" in lrow.get("verdict", ""):
            continue                                     # auto_advance's own skip
        if task in hb:
            notes.append(f"{trial}: not prepared, {hb[task]}")
            continue
        if model and taskstate.ledger_model(lrow.get(model, "")) == "solved":
            notes.append(f"{trial}: not prepared, {model} already solved {task}")
            continue
        t = Path(cfg["jobs_dir"]) / job / trial
        if not t.is_dir():
            notes.append(f"{trial}: trial folder missing")
            continue
        g = grading_name(t)
        state, pm = postmortem_state(t, g)
        if state == "ready":
            ready.append(pm)
        elif state == "none":
            jobs.append({"kind": "audit_prep", "task": task, "args": {"trial": f"{job}/{trial}", "grading": g}})
    return jobs, ready, notes


def newest_input(jobs_dir):
    """Newest mtime of a trial result, a regrade record or an auditor's unrecorded verdict; and the unrecorded list."""
    j = Path(jobs_dir)
    newest = 0.0
    for pat in ("*/*/result.json", "*/*/regrade-*/REGRADE.json"):
        for p in j.glob(pat):
            try:
                newest = max(newest, p.stat().st_mtime)
            except OSError:
                pass
    unrecorded = [v for v in j.glob("*/*/postmortem-*/verdict.json") if not (v.parent / "POSTMORTEM.json").exists()]
    for v in unrecorded:
        try:
            newest = max(newest, v.stat().st_mtime)
        except OSError:
            pass
    return newest, unrecorded


def record_plan(cfg):
    newest, unrecorded = newest_input(cfg["jobs_dir"])
    led = paths.BUILD / "audit" / "ledger.md"
    led_m = led.stat().st_mtime if led.exists() else 0.0
    if unrecorded or newest > led_m:
        why = f"{len(unrecorded)} verdicts to record" if unrecorded else "trial results newer than the ledger"
        return [{"kind": "audit_record", "task": LEDGER, "args": {"token": int(newest)}, "why": why}]
    return []


def fairness_plan(cfg, ctx, proc_list):
    jobs, notes = [], []
    scale = sorted(ctx["batches"])
    cands = [s for s in scale if "BREAKER" in ctx["ledger"].get(s, {}).get("verdict", "")]
    hb = held_or_busy(set(cands), cfg, proc_list, ctx)
    jd = Path(cfg["jobs_dir"])
    for s in cands:
        if any(k == "fairness" for k, _m, _p in ctx["running"].get(s, [])):
            continue
        if s in hb:
            notes.append(f"{s}: fairness waits, {hb[s]}")
            continue
        dirs = [p for p in jd.glob(f"{s}-*/") if p.is_dir()]
        last = max(dirs, key=lambda p: p.stat().st_mtime) if dirs else None
        f = paths.BUILD / s / "FAIRNESS.md"
        if f.exists() and last is not None and f.stat().st_mtime > last.stat().st_mtime:
            continue                                     # reviewed after the newest trial
        jobs.append({"kind": "fairness", "task": s, "args": {"after": last.name if last else ""}})
    return jobs, notes


def cleanup_plan(proc_list, now=None):
    hour = time.strftime("%Y-%m-%dT%H", time.gmtime(now))
    if any("hourly_cleanup.sh loop" in " ".join(argv) for _pid, argv, _cwd, _env in proc_list):
        return [], ["cleanup: the old hourly_cleanup.sh loop still runs; no queue cleanup"]
    return [{"kind": "cleanup", "task": MACHINE, "args": {"hour": hour}}], []


def step3_plan(now=None):
    t = time.gmtime(now)
    slot = time.strftime("%Y-%m-%dT%H:", t) + ("00" if t.tm_min < 30 else "30")
    return [{"kind": "step3", "task": ROUTER, "args": {"slot": slot}}]


def write_ready(ready):
    """Rewrite audit_ready.txt (atomically) with the folders waiting for an auditor, as auto_advance did."""
    f = paths.ROOT / READY_FILE
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".new")
    tmp.write_text("".join(f"{str(p).rstrip('/')}\n" for p in ready))
    tmp.replace(f)


def reconcile(conn, cfg, ctx, proc_list, dry_run=False, now=None):
    """One phase-4 pass. Returns [{task, stage, want, notes}] (same shape as the other phases)."""
    p4 = cfg.get("phase4", {})
    if not p4.get("enabled", True):
        return []
    want, notes = [], []
    if p4.get("audits", True):
        j, ready, n = audit_plan(cfg, ctx, proc_list)
        want += j
        notes += n
        want += record_plan(cfg)
        if not dry_run:
            write_ready(ready)
        notes.append(f"audit_ready.txt: {len(ready)} folders waiting for an auditor"
                     + (" (dry run: not written)" if dry_run else ""))
    if p4.get("fairness", True):
        j, n = fairness_plan(cfg, ctx, proc_list)
        want += j
        notes += n
    if p4.get("cleanup", True):
        j, n = cleanup_plan(proc_list, now)
        want += j
        notes += n
    if p4.get("step3", True):
        want += step3_plan(now)
    rep = {}
    for w in want:
        r = rep.setdefault(w["task"], {"task": w["task"], "stage": "phase4", "want": [], "notes": []})
        if not dry_run:
            w["id"], _ = qdb.enqueue(conn, w["kind"], w["task"], w["args"], priority=cfg["priority"].get(w["kind"], 0),
                                     max_attempts=cfg["max_attempts"].get(w["kind"], 1), origin="reconciler")
        r["want"].append(w)
    if not dry_run:
        # A queued periodic job of an earlier slot is not needed once a newer slot is queued.
        for kind, key in (("cleanup", "hour"), ("step3", "slot")):
            cur = [w["args"][key] for w in want if w["kind"] == kind]
            for row in qdb.jobs(conn, "kind=? AND state='queued'", (kind,)):
                if cur and qdb.args_of(row).get(key) != cur[0]:
                    qdb.set_state(conn, row["id"], "done", f"superseded by the {kind} job of {cur[0]}")
        for row in qdb.jobs(conn, "kind='audit_record' AND state='queued'"):
            tok = [w["args"]["token"] for w in want if w["kind"] == "audit_record"]
            if not tok or qdb.args_of(row).get("token") != tok[0]:
                qdb.set_state(conn, row["id"], "done", "superseded: a newer ledger refresh covers it")
    if notes:
        rep.setdefault("_phase4", {"task": "_phase4", "stage": "phase4", "want": [], "notes": []})["notes"] += notes
    return list(rep.values())


def command(row, cfg):
    """argv for a phase-4 job (worker.py), or None when the kind is not a phase-4 kind."""
    k, task, a = row["kind"], row["task"], qdb.args_of(row)
    if k == "audit_prep":
        return ["python3", "common/audit/postmortem.py", "prepare", str(Path(cfg["jobs_dir"]) / a["trial"])]
    if k == "audit_record":
        # Not -I: audit_results.py imports its helpers from its own folder (status_report.py note, 2026-10-26).
        return ["bash", "-c", "python3 common/audit/postmortem.py record-ready && python3 common/audit/audit_results.py"]
    if k == "fairness":
        script = FAIRNESS_SCRIPT["stk" if task.startswith("stk-") else "sibling"]
        return ["bash", "-c", 'common/launch/drive.sh deepseek bash "$1" "$2" > "build/$2/fairness.nohup" 2>&1 < /dev/null',
                "_", script, task]
    if k == "cleanup":
        return ["bash", "common/util/hourly_cleanup.sh", "once"]
    if k == "step3":
        return ["bash", "-c", STEP3_SH]
    return None
