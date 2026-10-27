"""Phase 3 rules: builds, trials and stale gates of the batch tasks, derived from taskstate.read().

These rules replace pipelines/router/scale_queue.py. They look only at tasks listed in a batch file
(pipelines/router/out/batches/*.txt, or the batches named in [phase3] batches), the same input the scheduler had.

  P1  stage waiting_build or build_interrupted, and build/<slug>/BUILD-PROMPT.md exists     -> build {}
      (one build job per task, ever: a failed or declined build is final; `cweq retry` is a person's decision)
  P2  stage waiting_trials -> per model without a verdict (not stuck, not held by hold_<model>):
        no graded run yet, or one run left      -> one trial_run with --max-runs <left>      (early abort at a solve)
        a graded run and two or more runs left  -> one trial_run per remaining run, --max-runs 1, started together
                                                   (a failing model reaches its third verdict in one run's time)
      args {"model", "first_run", "max_runs", "group", "version"}: version = the SOUND gate's fingerprint, group = runs
      tried when planned. A new task version starts a new set of keys, and the same plan is never queued twice.
      After [phase3] max_launches launch groups of one (task, model, version) without a verdict: no more jobs; the
      task is reported for a person (the scheduler's --max-launches).
  P3  stage stale_gate -> regate {"fp", "listing"} (the same key phase-1 rule R1 uses, so the two never double up),
      except when reconcile rule R4 applies (tests only removed, both models already solved)

Tasks with a running build, gate, re-gate, trial, fairness review or repair are in stages building / regating /
trialing and get nothing. Queued phase-3 jobs of an older task version are marked superseded.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qdb  # noqa: E402
import taskstate  # noqa: E402
from taskstate import paths  # noqa: E402

KINDS = ("build", "trial_run")


def trial_plan(slug, m, mm, version):
    """The trial_run jobs for one open (task, model): list of args dicts."""
    graded, ungraded = mm["graded"], mm["ungraded"]
    tried, left = graded + ungraded, max(1, 3 - graded)
    base = {"model": m, "group": tried, "version": version}
    if graded >= 1 and left >= 2:
        return [dict(base, first_run=tried + i + 1, max_runs=1) for i in range(left)]
    return [dict(base, first_run=tried + 1, max_runs=left)]


def launches(conn, slug, m, version):
    """Launch groups of (task, model, version) that ended (done or failed)."""
    groups = set()
    for r in qdb.jobs(conn, "kind='trial_run' AND task=? AND state IN ('done','failed')", (slug,)):
        a = qdb.args_of(r)
        if a.get("model") == m and a.get("version") == version and not (r["result"] or "").startswith("not needed"):
            groups.add(a.get("group"))
    return len(groups)


def wants(t, cfg, conn, ctx_ledger=None):
    """(jobs wanted [{kind, args}], notes) for one task reading."""
    p3, slug, stage = cfg["phase3"], t["task"], t["stage"]
    out, notes = [], []
    allowed = p3.get("batches") or []
    if not t["batch"] or (allowed and t["batch"] not in allowed):
        return out, notes
    if stage in ("waiting_build", "build_interrupted"):
        if (paths.BUILD / slug / "BUILD-PROMPT.md").is_file():
            out.append({"kind": "build", "args": {}})
        else:
            notes.append("no BUILD-PROMPT.md: not built")
    elif stage == "waiting_trials":
        version = taskstate.gate_sha16(slug)
        for m, mm in t["models"].items():
            if mm["ledger"] in ("solved", "failed") or mm["launch"] in ("solved", "failed", "stuck"):
                continue
            if (paths.BUILD / slug / f"hold_{m}").exists():
                notes.append(f"{m} held (hold_{m})")
                continue
            if launches(conn, slug, m, version) >= p3["max_launches"]:
                notes.append(f"{m}: {p3['max_launches']} trial launches without a verdict: a person looks")
                continue
            out += [{"kind": "trial_run", "args": a} for a in trial_plan(slug, m, mm, version)]
    elif stage == "stale_gate":
        import reconcile
        if reconcile.removal_cannot_change_verdict(slug, ctx_ledger):
            notes.append(reconcile.BOTH_SOLVED_NOTE)
            return out, notes
        listing = any(slug.startswith(x) for x in cfg["reconcile"]["listing_prefixes"])
        out.append({"kind": "regate", "args": {"fp": reconcile.gate_digest(slug)[:16], "listing": listing}})
    return out, notes


def reconcile(conn, cfg, ctx, dry_run=False):
    """One phase-3 pass over the batch tasks. Returns [{task, stage, want, notes}] for tasks with wants or notes."""
    rep = []
    if not cfg["phase3"].get("enabled", True):
        return rep
    for slug in sorted(ctx["batches"]):
        try:
            t = taskstate.read(slug, ctx)
        except Exception as e:                             # one unreadable task must not stop the pass
            rep.append({"task": slug, "stage": "?", "want": [], "notes": [f"unreadable: {type(e).__name__}: {e}"]})
            continue
        w, notes = wants(t, cfg, conn, ctx["ledger"])
        for x in w:
            why = taskstate.redo_reason(x["kind"], slug, x["args"], ctx, t)
            if why:                                        # never plan finished or running work
                notes.append(f"{x['kind']} not planned: {why}")
                x["skip"] = True
        w = [x for x in w if not x.get("skip")]
        if not dry_run:
            for x in w:
                x["id"], _ = qdb.enqueue(conn, x["kind"], slug, x["args"], priority=cfg["priority"].get(x["kind"], 0),
                                         max_attempts=cfg["max_attempts"].get(x["kind"], 2), origin="reconciler")
            if t["stage"] in ("waiting_trials", "trialing", "awaiting_audit", "not_breaker"):
                version = taskstate.gate_sha16(slug)
                for r in qdb.jobs(conn, "task=? AND kind='trial_run' AND state='queued' AND origin='reconciler'",
                                  (slug,)):
                    if qdb.args_of(r).get("version") != version:
                        qdb.set_state(conn, r["id"], "failed", "superseded: a new task version since it was queued")
        if w or notes:
            rep.append({"task": slug, "stage": t["stage"], "want": w, "notes": notes})
    return rep
