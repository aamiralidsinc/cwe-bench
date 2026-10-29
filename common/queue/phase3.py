"""Phase 3 rules: builds, trials and stale gates of the batch tasks, derived from taskstate.read().

These rules replace pipelines/router/scale_queue.py. They look only at tasks listed in a batch file
(pipelines/router/out/batches/*.txt, or the batches named in [phase3] batches), the same input the scheduler had.

  P1  stage waiting_build or build_interrupted, and build/<slug>/BUILD-PROMPT.md exists     -> build {}
      (a build whose builder was paused and cut by its overdue timer is resumed by kind build_resume instead)
      (one build job per task, ever: a failed or declined build is final; `cweq retry` is a person's decision)
  P2  stage waiting_trials -> per model without a verdict (not stuck, not held by hold_<model>):
        no graded run yet, or one run left      -> one trial_run with --max-runs <left>      (early abort at a solve)
        a graded run and two or more runs left  -> one trial_run per remaining run, --max-runs 1, started together
                                                   (a failing model reaches its third verdict in one run's time)
      args {"model", "first_run", "max_runs", "group", "version"}: version = the SOUND gate's fingerprint, group = runs
      tried when planned. A new task version starts a new set of keys, and the same plan is never queued twice.
      After [phase3] max_launches launch groups of one (task, model, version) without a verdict: no more jobs; the
      task is reported for a person (the scheduler's --max-launches).
      Untrusted runs (untrusted.py, 2026-10-29): a graded run the ledger leaves out for an untrusted audit and that is
      owed a fresh run does not count as graded (taskstate), so the plan above re-runs it. A `stuck` model gets
      exactly one fresh run per such run: args {"model", "first_run", "max_runs": 1, "group", "version",
      "rerun_of": <the untrusted run's job>}, never a second one for the same run (any job with that rerun_of that
      is not superseded). Holds and max_launches apply as to every trial_run.
      MiMo after DeepSeek (owner rule 2026-10-29, [phase3] mimo_after_deepseek, default on): MiMo's API concurrency is
      limited, so no trial_run of mimo (first runs or the fresh runs of a stuck mimo) is planned until DeepSeek has 3
      valid graded fails: its launch state (trial_state, not the audited ledger, so MiMo does not wait for audits)
      is failed, or the ledger already says failed. Untrusted runs being re-run do not count (taskstate drops them).
      DeepSeek solved (or blocked): MiMo is never planned, the task is not a breaker. Queued or running mimo jobs are
      left alone. The note "mimo waits: DeepSeek has n/3 graded fails" says why (cweq explain prints it).
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


def tried_of(mm):
    """Rows in the model's runs log: graded, ungraded and the untrusted runs left out of the graded count."""
    return mm["graded"] + mm["ungraded"] + len(mm.get("rerun") or ())


def trial_plan(slug, m, mm, version):
    """The trial_run jobs for one open (task, model): list of args dicts."""
    graded = mm["graded"]
    tried, left = tried_of(mm), max(1, 3 - graded)
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


def rerun_plan(m, mm, version, active=()):
    """One fresh run per untrusted run of a stuck model that has none yet (planned, running or ended)."""
    fresh = [j for j in mm.get("rerun_owed") or () if j not in active]
    tried = tried_of(mm)
    return [{"model": m, "first_run": tried + i + 1, "max_runs": 1, "group": tried, "version": version,
             "rerun_of": j} for i, j in enumerate(fresh)]


def mimo_wait(t, p3):
    """None when MiMo trials may be planned, else the note that says why not ([phase3] mimo_after_deepseek)."""
    ds = t["models"].get("deepseek")
    if not p3.get("mimo_after_deepseek", True) or ds is None:
        return None
    if ds["ledger"] == "solved" or (ds["launch"] == "solved" and ds["ledger"] != "failed"):
        return "mimo not planned: DeepSeek solved the task (not a breaker; mimo_after_deepseek)"
    if ds["ledger"] == "blocked":
        return "mimo not planned: DeepSeek is blocked by the provider (mimo_after_deepseek)"
    if ds["ledger"] == "failed" or ds["launch"] == "failed":
        return None
    return f"mimo waits: DeepSeek has {ds['graded']}/3 graded fails (mimo_after_deepseek)"


def wants(t, cfg, conn, ctx_ledger=None, meta=None, reruns=None):
    """(jobs wanted [{kind, args}], notes) for one task reading. meta: its batch's header ({priority, hold}).
    reruns: untrusted.rerun_jobs() of this pass."""
    p3, slug, stage = cfg["phase3"], t["task"], t["stage"]
    out, notes = [], []
    allowed = p3.get("batches") or []
    if not t["batch"] or (allowed and t["batch"] not in allowed):
        return out, notes
    if stage in ("waiting_build", "build_interrupted"):
        if (meta or {}).get("hold"):
            notes.append(f"batch {t['batch']} on hold (# hold: yes): no new build")
        elif t.get("paused_build"):
            notes.append("builder was paused and cut by its timer: resumed by kind build_resume, never rebuilt")
        elif (paths.BUILD / slug / "BUILD-PROMPT.md").is_file():
            out.append({"kind": "build", "args": {}})
        else:
            notes.append("no BUILD-PROMPT.md: not built")
    elif stage == "waiting_trials":
        version = taskstate.gate_sha16(slug)
        for m, mm in t["models"].items():
            if mm["ledger"] in ("solved", "failed", "blocked") or mm["launch"] in ("solved", "failed"):
                continue
            active = ((reruns or {}).get((slug, m)) or {}).get("active", set())
            if mm["launch"] == "stuck" and not rerun_plan(m, mm, version, active):
                continue
            if m == "mimo" and (why := mimo_wait(t, p3)):
                notes.append(why)
                continue
            if (paths.BUILD / slug / f"hold_{m}").exists():
                notes.append(f"{m} held (hold_{m})")
                continue
            if launches(conn, slug, m, version) >= p3["max_launches"]:
                notes.append(f"{m}: {p3['max_launches']} trial launches without a verdict: a person looks")
                continue
            if mm["launch"] == "stuck":
                plan = rerun_plan(m, mm, version, active)
                notes.append(f"{m} stuck: one fresh run for each untrusted run ({', '.join(a['rerun_of'] for a in plan)})")
            else:
                plan = trial_plan(slug, m, mm, version)
                if mm.get("rerun"):
                    notes.append(f"{m}: {len(mm['rerun'])} untrusted run(s) do not count as graded: re-run")
            out += [{"kind": "trial_run", "args": a} for a in plan]
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
    metas = ctx.get("batch_meta") or {}
    import untrusted
    ctx.setdefault("cfg", cfg)                             # untrusted.py reads jobs_dir and the repair settings
    if conn is not None:                                   # read by taskstate (stage) and wants (one re-run per run)
        ctx.setdefault("reruns", untrusted.rerun_jobs(conn))
        ctx.setdefault("repairs_active", untrusted.active_repairs(conn))
    # Batch-file order (files by name, lines as written): equal priorities start in rank order (ids ascend).
    for slug in ctx["batches"]:
        try:
            t = taskstate.read(slug, ctx)
        except Exception as e:                             # one unreadable task must not stop the pass
            rep.append({"task": slug, "stage": "?", "want": [], "notes": [f"unreadable: {type(e).__name__}: {e}"]})
            continue
        meta = metas.get(t["batch"]) or {}
        w, notes = wants(t, cfg, conn, ctx["ledger"], meta, ctx.get("reruns"))
        for x in w:
            why = taskstate.redo_reason(x["kind"], slug, x["args"], ctx, t)
            if why:                                        # never plan finished or running work
                notes.append(f"{x['kind']} not planned: {why}")
                x["skip"] = True
        w = [x for x in w if not x.get("skip")]
        if not dry_run:
            for x in w:
                bump = meta.get("priority", 0) if x["kind"] in ("build", "trial_run") else 0
                x["id"], _ = qdb.enqueue(conn, x["kind"], slug, x["args"],
                                         priority=cfg["priority"].get(x["kind"], 0) + bump,
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
