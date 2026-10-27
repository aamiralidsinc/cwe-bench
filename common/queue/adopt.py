"""Adoption: the queue takes over from the running pipeline where it stands, and never redoes finished work.

    python3 common/queue/cweq.py adopt --dry-run     what the queue would record, and any conflicts (writes nothing)
    python3 common/queue/cweq.py adopt               record it (tables `adoptions` and `tasks`)

One pass reads every task the pipeline knows (batch files, ledger rows, task packages with a build record) through
taskstate.read(): build and gate markers, gate fingerprint, trial state per model, the audited ledger, fairness,
the owner's decision, delivery, and the processes running for it right now. Each task gets a stage and the one next
step that moves it on. Work that is running under the current scripts is recorded as running, never started again.

Checks before the dispatcher may start anything (an adoption is ok only with zero conflicts):
  conflict    a reading that would make the queue repeat finished work, or lose track of running work:
              - a task package exists but no build record (the queue would build it again)
              - the ledger calls the task a BREAKER candidate, or rejected, and the queue reads an earlier stage for
                a reason the files do not explain (no repair, re-gate or new task version)
              - a running pipeline process names a task the queue does not know
  difference  the audited ledger and the launch state of a model disagree (for example runs of an older task
              version count in the ledger but not in the current runs log). Shown for a person; the queue follows
              the ledger, which is the audited one.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import procs  # noqa: E402
import qdb  # noqa: E402
import taskstate  # noqa: E402
from taskstate import paths  # noqa: E402

BREAKER_STAGES = ("awaiting_audit", "awaiting_fairness", "fairness_not_ready", "awaiting_decision", "kept",
                  "dropped", "delivered")
# Stages that legitimately sit "before" a ledger verdict: the task changed (repair, re-gate, new version) or is
# being reworked, so its old runs no longer decide it.
REWORK_STAGES = ("regating", "held_repair", "stale_gate", "trialing", "waiting_trials", "building",
                 "build_interrupted")


def code_version():
    rel = paths.ROOT / "RELEASE.json"                   # a versioned release (common/util/release.py)
    if rel.is_file():
        try:
            return json.loads(rel.read_text()).get("sha") or None
        except (OSError, ValueError):
            pass
    try:
        r = subprocess.run(["git", "-C", str(paths.ROOT), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                           text=True, timeout=10)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def check(t, ctx):
    """(conflicts, differences) for one task reading."""
    conflicts, diffs = [], []
    slug, stage = t["task"], t["stage"]
    if stage == "waiting_build" and (paths.TASKS / slug).is_dir():
        conflicts.append(f"{slug}: task package exists but no build record; the queue would build it again")
    lv = t["ledger_verdict"]
    if "BREAKER" in lv and stage not in BREAKER_STAGES and stage not in REWORK_STAGES:
        conflicts.append(f"{slug}: ledger says BREAKER candidate, queue reads {stage}")
    # A rejected task may still have an open (task, model) pair: every pair gets its own verdict.
    if lv.startswith("rejected") and stage not in ("not_breaker", "delivered", "dropped", "kept", "trials_stuck") \
            and stage not in REWORK_STAGES:
        conflicts.append(f"{slug}: ledger says {lv}, queue reads {stage}")
    for m, mm in t["models"].items():
        led, launch = mm["ledger"], mm["launch"]
        if led in ("solved", "failed") and launch in ("solved", "failed") and led != launch:
            diffs.append(f"{slug} {m}: ledger {led}, runs log {launch} (the queue follows the ledger)")
        elif led in ("solved", "failed") and launch in ("none", "incomplete") and stage in REWORK_STAGES:
            diffs.append(f"{slug} {m}: ledger {led} from earlier runs, current version {launch}")
    return conflicts, diffs


def adopt(conn, cfg=None, dry_run=False, proc_list=None, ctx=None):
    """One adoption pass. Returns {"tasks": [...], "counts", "conflicts", "differences", "ok", "id"}."""
    started = qdb.utc()
    ctx = ctx or taskstate.context(procs.list_processes() if proc_list is None else proc_list)
    known = taskstate.slugs(ctx)
    rows, conflicts, diffs, counts = [], [], [], {}
    for slug in known:
        try:
            t = taskstate.read(slug, ctx)
        except Exception as e:                             # one unreadable task must not hide the others
            conflicts.append(f"{slug}: could not be read ({type(e).__name__}: {e})")
            continue
        c, d = check(t, ctx)
        conflicts += c
        diffs += d
        counts[t["stage"]] = counts.get(t["stage"], 0) + 1
        rows.append(t)
    for slug, procs_of in sorted(ctx["running"].items()):
        if slug not in known:
            conflicts.append(f"{slug}: running work ({', '.join(k for k, _m, _p in procs_of)}) for a task the "
                             "queue does not know")
    rep = {"tasks": rows, "counts": dict(sorted(counts.items(), key=lambda kv: taskstate.STAGES.index(kv[0]))),
           "conflicts": conflicts, "differences": diffs, "ok": not conflicts, "id": None}
    if dry_run:
        return rep
    now = qdb.utc()
    with qdb.tx(conn):
        cur = conn.execute("INSERT INTO adoptions (started, finished, code_version, tasks, counts, conflicts,"
                           " differences, ok) VALUES (?,?,?,?,?,?,?,?)",
                           (started, now, code_version(), len(rows), json.dumps(rep["counts"]),
                            json.dumps(conflicts), json.dumps(diffs), int(rep["ok"])))
        rep["id"] = cur.lastrowid
        for t in rows:
            facts = {k: v for k, v in t.items() if k not in ("task", "batch", "pipeline", "stage", "next")}
            conn.execute("INSERT INTO tasks (task, adoption_id, batch, pipeline, stage, next, facts, read_at)"
                         " VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(task) DO UPDATE SET adoption_id=excluded.adoption_id,"
                         " batch=excluded.batch, pipeline=excluded.pipeline, stage=excluded.stage, next=excluded.next,"
                         " facts=excluded.facts, read_at=excluded.read_at",
                         (t["task"], rep["id"], t["batch"], t["pipeline"], t["stage"], t["next"],
                          json.dumps(facts, sort_keys=True), now))
    return rep


def report(rep, out=print, detail=False):
    """Human-readable summary of an adoption pass."""
    out(f"tasks read: {len(rep['tasks'])}")
    for stage, n in rep["counts"].items():
        out(f"  {stage:<20} {n}")
    nxt = {}
    for t in rep["tasks"]:
        key = t["next"].split(" (")[0] if not t["next"].startswith("trial ") else "trial (per model)"
        nxt[key] = nxt.get(key, 0) + 1
    out("next steps:")
    for k, n in sorted(nxt.items(), key=lambda kv: -kv[1]):
        out(f"  {n:>4}  {k}")
    running = sum(len(t["running"]) for t in rep["tasks"])
    out(f"running pipeline processes adopted (recorded, not restarted): {running}")
    out(f"conflicts ({len(rep['conflicts'])}){' -- the dispatcher stays closed until these are resolved' if rep['conflicts'] else ''}:")
    for c in rep["conflicts"]:
        out(f"  {c}")
    out(f"differences, ledger vs launch state ({len(rep['differences'])}; the queue follows the ledger):")
    for d in rep["differences"][: None if detail else 15]:
        out(f"  {d}")
    if not detail and len(rep["differences"]) > 15:
        out(f"  ... {len(rep['differences']) - 15} more (--detail)")
    if detail:
        out("per task:")
        for t in rep["tasks"]:
            out(f"  {t['task']:<44} {t['stage']:<20} {t['next']}")
    out("adoption " + ("OK" if rep["ok"] else "NOT OK") + (f" (#{rep['id']})" if rep["id"] else " (dry run: nothing written)"))
