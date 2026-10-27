"""The reconciler: derives jobs from the artifacts on disk, never from its own memory.

Phase 1 rules (docs/WORK-QUEUE.md); the phase-3 rules (builds, trials) are in phase3.py and run in the same pass. Only tasks with a test repair (build/<slug>/repaired-tests-* or removed-tests-*)
or a hold (.hold-repair) are looked at.

  R1  repair + gate fingerprint STALE + no gate RESULT since the files last changed      -> regate
      repair + fingerprint current + .gate_passed (a re-gate stopped before its RESULT)  -> regate
  R2  repair + fingerprint current + last RESULT is SOUND                                 -> per graded run whose
      grading is older than the newest change under tasks/<slug>/tests/ and has no newer regrade-*:
        rescore (rescore_from_results.py --drop) when the repair only removed whole test files and the drop
        names match exactly the same test ids as a word and as a substring; otherwise regrade (regrade_from_code.py)
  R1+R2  when R1 fires, the R2 jobs are queued at once with depends_on = the regate (they wait for it, and are
      blocked if it fails).
  R3  .hold-repair -> trial_run jobs of the task are not started (dispatch.py); shown by `cweq explain`.
  R4  the repairs only removed tests (removed-tests-*, no repaired-tests-*) and the audited ledger says both models
      SOLVED -> no job: fewer
      tests cannot turn a solve into a failure (note "both models solved; removing tests cannot change the verdict").
  --  fingerprint missing (gated before 2026-10-25): no job, reported. A gate that failed on the current files: no
      job, reported (needs a person). A task busy with an old script: no job this pass.

Job keys carry the 16-hex gate digest of the current files ("fp"), so a regrade is queued once per test version and
a deleted queue.db is rebuilt with the same keys; queued jobs for an older digest are marked superseded.
"""
import calendar
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)
sys.path.insert(0, str(paths.COMMON / "gate"))
import fingerprint  # noqa: E402  (the gate fingerprint: what a SOUND gate covered)

import procs  # noqa: E402
import qdb  # noqa: E402

PHASE1_KINDS = ("regate", "regrade", "rescore")
SKIP = fingerprint.SKIP
RESULT_RE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) \S+ RESULT: (.*)$")
BACKUP_SUFFIXES = (".orig", ".before", ".relaxed")


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def walk(roots):
    """(path, stat) of every file and folder under roots, skipping the folders fingerprint.py skips."""
    for r in roots:
        if not r.is_dir():
            continue
        for d, dirs, files in os.walk(r):
            dirs[:] = [x for x in dirs if x not in SKIP]
            for name in [None, *files]:
                p = Path(d) if name is None else Path(d) / name
                try:
                    yield p, p.stat()
                except OSError:
                    pass


def newest_mtime(roots):
    """Newest mtime of any file or folder under roots (folders count: deleting a file changes its folder)."""
    return max((st.st_mtime for _p, st in walk(roots)), default=0.0)


_digest_cache = {}


def gate_digest(slug):
    """fingerprint.digest(slug), recomputed only when a covered file's size or mtime changed (hashing a task's
    environment every pass would be slow)."""
    t, b = paths.TASKS / slug, paths.BUILD / slug
    roots = [t / "tests", t / "solution", t / "environment", b / "checks"]
    sig = (tuple((str(p), st.st_size, st.st_mtime_ns) for p, st in walk(roots)),
           (b / "manifest.json").stat().st_mtime_ns if (b / "manifest.json").exists() else 0)
    hit = _digest_cache.get(slug)
    if hit and hit[0] == sig:
        return hit[1]
    digest = fingerprint.digest(slug)[0]
    _digest_cache[slug] = (sig, digest)
    return digest


def last_result(build_dir):
    """(epoch, text) of the last RESULT line in postbuild.log, or (None, None)."""
    ts = text = None
    try:
        for line in (build_dir / "postbuild.log").read_text(errors="replace").splitlines():
            m = RESULT_RE.match(line)
            if m:
                ts, text = qdb.parse_utc(m.group(1)), m.group(2)
    except OSError:
        pass
    return ts, text


def strip_backup(name):
    for s in BACKUP_SUFFIXES:
        if name.endswith(s):
            return name[: -len(s)]
    return name


def repair_kind(slug):
    """('rescore', [drop names]) when the repair only removed whole test files, else ('regrade', [])."""
    b, tests = paths.BUILD / slug, paths.TASKS / slug / "tests"
    present = {p.name for p in tests.rglob("*") if p.is_file()} if tests.is_dir() else set()
    # A repaired file that is still in the suite changed what a test accepts: only a re-run of the code can tell.
    for d in b.glob("repaired-tests-*"):
        for f in d.iterdir():
            if f.name.endswith(".orig") and strip_backup(f.name) in present:
                return "regrade", []
        if any(f.is_file() and not f.name.endswith(".orig") and f.name != "README.md" and f.name in present
               for f in d.iterdir()):
            return "regrade", []
    drops = []
    for d in b.glob("removed-tests-*"):
        for f in d.iterdir():
            if not f.is_file() or f.name == "README.md":
                continue
            name = strip_backup(f.name)
            if name in present:
                return "regrade", []                     # one test function removed from a file that stays
            drops.append(name.split(".")[0])             # invalid_schema_value.test.js -> invalid_schema_value
    return ("rescore", sorted(set(drops))) if drops else ("regrade", [])


def drop_matches_exactly(results, drops):
    """rescore_from_results.py drops by substring. Accept the drops only when every substring hit is also a
    whole-word hit (so DuplicateSecurityTest cannot take DuplicateSecurityTestExtra with it) and each drop hits."""
    ids = [k for g in ("security", "functional") for k in (results.get(g) or {})]
    for d in drops:
        sub = {k for k in ids if d in k}
        word = {k for k in ids if re.search(rf"(?<![A-Za-z0-9_]){re.escape(d)}(?![A-Za-z0-9_])", k)}
        if not sub or sub != word:
            return False
    return True


def graded_runs(slug, jobs_dir):
    """Finished, graded trials of the task: dicts with job, trial, path, graded (epoch of the grading in use), ..."""
    out = []
    for t in sorted(Path(jobs_dir).glob(f"*/{slug}__*")):
        if not t.is_dir():
            continue
        cfg, res = jload(t / "config.json") or {}, jload(t / "result.json")
        if res is None or Path((cfg.get("task") or {}).get("path", "")).name != slug:
            continue                                     # still running, or another task
        reward = ((res.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        if reward is None:
            reward = (jload(t / "verifier" / "reward.json") or {}).get("reward")
        if reward is None:
            continue                                     # never graded: nothing to re-grade
        graded = qdb.parse_utc(res.get("finished_at")) or (t / "result.json").stat().st_mtime
        regrades = []
        for r in sorted(t.glob("regrade-*/REGRADE.json")):
            m = re.match(r"regrade-(\d{8}T\d{6}Z)$", r.parent.name)
            when = calendar.timegm(time.strptime(m.group(1), "%Y%m%dT%H%M%SZ")) if m else r.stat().st_mtime
            regrades.append((when, jload(r) or {}))
        out.append({"job": t.parent.name, "trial": t.name, "path": t, "reward": reward, "graded": graded,
                    "regrades": regrades,
                    "has_code": (t / "final-code" / "changes.patch").is_file() or (t / "artifacts").is_dir()})
    return out


BOTH_SOLVED_NOTE = "both models solved; removing tests cannot change the verdict"


def removal_cannot_change_verdict(slug, ledger=None):
    """True when the task's repairs only removed tests (removed-tests-* folders, whole files or single test functions;
    no repaired-tests-* folder) and the audited ledger says both models already SOLVED: fewer tests keep a solve a
    solve, so no re-gate, regrade or rescore is worth running."""
    import taskstate
    led = (taskstate.ledger() if ledger is None else ledger).get(slug, {})
    if not all(taskstate.ledger_model(led.get(m, "")) == "solved" for m in taskstate.MODELS):
        return False
    b = paths.BUILD / slug
    return any(b.glob("removed-tests-*")) and not any(b.glob("repaired-tests-*"))


def analyse(slug, cfg, busy=None, ledger=None):
    """Everything the rules look at for one task, and the jobs they want: {facts..., 'want': [...], 'notes': [...]}.
    ledger: taskstate.ledger() of this pass (read here when not given)."""
    b = paths.BUILD / slug
    a = {"task": slug, "want": [], "notes": []}
    a["repairs"] = sorted(p.name for p in b.glob("repaired-tests-*")) + sorted(p.name for p in b.glob("removed-tests-*"))
    a["markers"] = sorted(m for m in (".sound", ".unsound", ".gate_error", ".listing_fail", ".gate_passed",
                                      ".hold-repair") if (b / m).exists())
    a["held"] = (b / ".hold-repair").exists()
    a["busy"] = (busy or {}).get(slug, [])
    if a["held"]:
        a["notes"].append("held (.hold-repair): trial jobs are not started")
    if not a["repairs"]:
        return a
    if a["busy"]:
        a["notes"].append("busy with an old script, nothing planned this pass: " +
                          "; ".join(f"pid {p} {c}" for p, c in a["busy"][:3]))
        return a

    if removal_cannot_change_verdict(slug, ledger):
        a["notes"].append(BOTH_SOLVED_NOTE)
        return a
    rec = jload(b / "gate_fingerprint.json")
    digest = gate_digest(slug)
    fp16 = digest[:16]
    a["fp"] = "missing" if rec is None else "current" if rec.get("sha256") == digest else "stale"
    a["fp16"] = fp16
    changed = newest_mtime([paths.TASKS / slug / d for d in ("tests", "solution", "environment")] + [b / "checks"])
    tests_changed = newest_mtime([paths.TASKS / slug / "tests"])
    rts, rtext = last_result(b)
    a["last_result"] = f"{qdb.utc(rts)} {rtext}" if rts else None
    sound = bool(rtext) and rtext.startswith("SOUND")

    regate = None
    if a["fp"] == "missing":
        a["notes"].append("no gate fingerprint (gated before 2026-10-25): re-gate by hand if needed")
        return a
    if a["fp"] == "stale":
        if rts and rts >= changed and not sound:
            a["notes"].append(f"the gate already ran on these files and did not pass ({rtext}): needs a person")
            return a
        regate = True
    elif ".gate_passed" in a["markers"]:
        regate = True                                    # a re-gate stopped between its gate and its RESULT
        a["notes"].append(".gate_passed without a running re-gate: the re-gate stopped early")
    elif not sound:
        a["notes"].append(f"last gate RESULT is not SOUND ({rtext}): no regrade")
        return a

    a["evaluated"] = True                                # R2 ran: queued jobs it did not want are not needed
    if regate:
        listing = any(slug.startswith(p) for p in cfg["reconcile"]["listing_prefixes"])
        a["want"].append({"kind": "regate", "args": {"fp": fp16, "listing": listing}})

    # R2: the graded runs whose grading predates the current tests.
    kind, drops = repair_kind(slug)
    why = f"test-only repair ({', '.join(a['repairs'])}); cweq after gate {fp16[:12]}"
    for r in graded_runs(slug, cfg["jobs_dir"]):
        last = max([r["graded"]] + [w for w, _ in r["regrades"]])
        if last >= tests_changed:
            continue                                     # graded (or regraded) on the current tests
        rel = f"{r['job']}/{r['trial']}"
        if kind == "rescore":
            done = any(all(any(d in x for x in info.get("dropped", [])) for d in drops) for _, info in r["regrades"])
            results = jload(r["path"] / "verifier" / "results.json") or {}
            if done:
                continue
            if drop_matches_exactly(results, drops):
                a["want"].append({"kind": "rescore", "args": {"trial": rel, "fp": fp16, "drop": drops, "why": why},
                                  "after_regate": regate})
                continue
        if not r["has_code"]:
            a["notes"].append(f"{r['trial']}: graded before the repair but no saved code; regrade.py by hand")
            continue
        a["want"].append({"kind": "regrade", "args": {"trial": rel, "fp": fp16, "why": why}, "after_regate": regate})
    return a


def candidate_slugs():
    b = paths.BUILD
    found = {p.parent.name for pat in ("*/repaired-tests-*", "*/removed-tests-*", "*/.hold-repair") for p in b.glob(pat)}
    return sorted(found)


def reconcile(conn, cfg, slugs=None, proc_list=None, dry_run=False):
    """One pass. Enqueues what the rules want (idempotent), supersedes queued jobs the files no longer want.
    Phase-1 rules (repairs) first, then the phase-3 rules (phase3.py: builds, trials, stale gates of batch tasks)
    unless slugs narrows the pass. Returns the per-task analyses."""
    phase3_too = slugs is None
    slugs = candidate_slugs() if slugs is None else slugs
    busy = procs.busy_tasks(slugs, cfg["busy"]["patterns"], proc_list, skip_dirs=(paths.COMMON,))
    import taskstate
    ledger = taskstate.ledger()
    out = []
    for slug in slugs:
        a = analyse(slug, cfg, busy, ledger)
        out.append(a)
        if dry_run or a["busy"]:
            continue
        wanted, regate_id = set(), None
        for w in a["want"]:
            deps = []
            if w.get("after_regate") and regate_id:
                deps = [regate_id]
            jid, _ = qdb.enqueue(conn, w["kind"], slug, w["args"], priority=cfg["priority"].get(w["kind"], 0),
                                 max_attempts=cfg["max_attempts"].get(w["kind"], 2), depends_on=deps,
                                 origin="reconciler")
            if w["kind"] == "regate":
                regate_id = jid
            wanted.add(jid)
            w["id"] = jid
        # Queued reconciler jobs the files no longer ask for: an older test version, or done by someone else.
        for row in qdb.jobs(conn, "task=? AND state='queued' AND origin='reconciler' AND kind IN (?,?,?)",
                            (slug, *PHASE1_KINDS)):
            if row["id"] in wanted or "fp16" not in a:
                continue
            if qdb.args_of(row).get("fp") != a["fp16"]:
                qdb.set_state(conn, row["id"], "failed", "superseded: the task's files changed since it was queued")
            elif a.get("evaluated"):
                qdb.set_state(conn, row["id"], "done", "not needed any more: the files on disk show it done")
    if phase3_too:
        import phase3
        import taskstate
        ctx = taskstate.context(procs.list_processes() if proc_list is None else proc_list)
        out += phase3.reconcile(conn, cfg, ctx, dry_run=dry_run)
    return out
