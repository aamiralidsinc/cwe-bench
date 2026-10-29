"""Runs whose post-run audit is UNTRUSTED: what each one is owed (owner-approved fix, 2026-10-29).

The bug. The ledger (common/audit/audit_results.py) leaves out a graded run whose current audit is untrusted (a test
fault, a harness or infrastructure fault, a provider stop, a rate-limit cut, grading of a partial workspace) and still
asks for 3 valid graded runs per model. The launch rules read only runs_<model>.log (common/trial/trial_state.py),
where such a run is a graded fail. So the queue saw each model done and planned no run, the ledger kept waiting for
one, and batch-4..6 tasks sat in awaiting_audit or trials_stuck with nothing queued (djust-s2, mollieplugin-s2,
core-s2, smarty-s2, crossplane-runtime-s2, ...).

The rule. Every untrusted run of a (task, model) gets one action:

  rerun         The cause is not a test fault the repair step owns: harness-or-infra (provider stops, rate limits,
                a partial workspace, ...), or a test fault / instruction ambiguity that no repair covers and that
                the repair step does not take on (rule T1 plans no repair, nothing holds the task). This includes a
                regrade made after a repair and audited again that is still untrusted. The run leaves the graded
                runs the launch rules count (trial_state drop=), so phase 3 plans a fresh run for it, the way it
                re-runs a provider stop (reward=None). A model that is `stuck` (STUCK_AFTER ungraded runs) still gets
                exactly one fresh run per untrusted run (phase3, args rerun_of = the untrusted run's job).
  reaudit       A test-fault / instruction-ambiguity audit that a newer repair folder covers, whose grading in use
                was made on the current tests (the R2 regrade is in), but whose audit is carried over from an older
                grading (audit_results.py keeps an audit when a regrade leaves the reward unchanged). The run is
                audited again on its regrade (phase4 audit_prep), never re-run.
  wait_regrade  Covered by a repair, but the grading in use is not on the current tests yet: the R2 regrade first,
                then the re-audit.
  wait_repair   A test fault the repair step owns: the task is held (.hold-repair), a repair job of the task is
                queued or running, or rule T1 plans one for it (repairstep.findings). It is regraded after the
                repair, then audited again, never re-run before.

A test cause is an attribution of test-fault or instruction-ambiguity, or failing items the auditor calls unfair
when the attribution is not harness-or-infra. Holds are respected elsewhere: .hold-repair and hold_<model> stop the
trial_run jobs (phase3, dispatch), so a blocked model gets no run whatever this says.

Only (task, model) pairs whose ledger cell counts an untrusted audit ("+N audit: untrusted") are read, so a pass
costs nothing for the other tasks. Results are cached in the pass's ctx.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repairstep  # noqa: E402  (audits, repair folders and test versions; also puts common/ on sys.path)
import markers  # noqa: E402
import paths  # noqa: E402
import qdb  # noqa: E402

UNTRUSTED_MARK = "audit: untrusted"
JOB_RE = re.compile(r"^(?P<task>.+?)-(?P<model>deepseek|mimo)-r(?P<run>[0-9]+)-")
TEST_ATTRIBUTIONS = repairstep.UNFAIR_ATTRIBUTIONS        # test-fault, instruction-ambiguity
NOT_TEST_ATTRIBUTIONS = ("harness-or-infra",)
ACTIONS = ("rerun", "reaudit", "wait_regrade", "wait_repair")


def ledger_untrusted(cell):
    """True when a ledger cell counts runs left out for an untrusted audit."""
    return UNTRUSTED_MARK in (cell or "")


def _cfg(ctx):
    cfg = (ctx or {}).get("cfg")
    if cfg is None:
        import config
        cfg = config.load()
        if ctx is not None:
            ctx["cfg"] = cfg
    return cfg


def test_cause(verdict):
    """True when the auditor blames the tests or the instruction rather than the harness or the provider."""
    a = (verdict or {}).get("attribution")
    if a in TEST_ATTRIBUTIONS:
        return True
    if a in NOT_TEST_ATTRIBUTIONS:
        return False
    return bool(repairstep.unfair_items(verdict))


def on_current_tests(run, cur_tests, newest_repair):
    """The grading in use was made on the current tests: by its recorded test version, else (a grading that records
    none) when it is newer than the newest repair folder (reconcile R2's repair_folder rule)."""
    _name, h, when = repairstep.grading_in_use(run)
    if h is not None:
        return h == cur_tests
    return (when or 0) > newest_repair


def active_repairs(conn):
    """Tasks with a repair job queued, leased or running."""
    return {r["task"] for r in qdb.jobs(conn, "kind='repair' AND state IN ('queued','leased','running')")}


def rerun_jobs(conn):
    """{(task, model): {"active": {untrusted job}, "ended": {untrusted job}}} of the trial_run jobs queued for an
    untrusted run (args rerun_of). A superseded job (an older task version) counts as neither."""
    out = {}
    for r in qdb.jobs(conn, "kind='trial_run'"):
        a = qdb.args_of(r)
        j = a.get("rerun_of")
        if not j or (r["state"] == "failed" and (r["result"] or "").startswith("superseded")):
            continue
        d = out.setdefault((r["task"], a.get("model")), {"active": set(), "ended": set()})
        d["ended" if r["state"] in ("done", "failed", "blocked") else "active"].add(j)
    return out


def classify(slug, ctx=None):
    """{model: [entry]} for every graded run of the task whose current audit (as the ledger reads it, carry-over
    included) is untrusted. entry: job, trial, model, audit (folder), audited (grading), grading (in use),
    attribution, cause (test | other), action (ACTIONS), why."""
    cache = ctx.setdefault("_untrusted", {}) if ctx is not None else {}
    if slug in cache:
        return cache[slug]
    import reconcile                                    # graded_runs (lazy: reconcile imports this module's peers)
    cfg = _cfg(ctx)
    b = paths.BUILD / slug
    newest = max((t for _n, t in repairstep.repair_folders(b)), default=0.0)
    held = (b / ".hold-repair").exists()
    active = slug in ((ctx or {}).get("repairs_active") or ())
    cur_tests, finding, out = None, None, {}
    for run in reconcile.graded_runs(slug, cfg["jobs_dir"]):
        m = JOB_RE.match(run["job"])
        if not m:
            continue
        cur = repairstep.current_audit(run["path"])
        if not cur:
            continue                                     # no audit, or one of an older grading: awaiting, not untrusted
        pm, folder = cur
        v = pm.get("verdict") or {}
        if v.get("trustworthy") is True:
            continue
        gname = repairstep.grading_in_use(run)[0]
        e = {"job": run["job"], "trial": run["trial"], "model": m.group("model"), "audit": folder.name,
             "audited": pm.get("grading_audited") or "original", "grading": gname,
             "attribution": v.get("attribution"), "cause": "test" if test_cause(v) else "other"}
        if e["cause"] == "other":
            e["action"], e["why"] = "rerun", f"untrusted ({e['attribution']}), not a test fault: a fresh run"
        else:
            when = repairstep.stamp_epoch(folder.name) or repairstep.mtime(folder / "PREPARED.json")
            cov = repairstep.covering(b, when)
            if cov:
                if cur_tests is None:
                    cur_tests = repairstep.tests_hash(slug)
                if not on_current_tests(run, cur_tests, newest):
                    e["action"], e["why"] = "wait_regrade", f"repaired ({cov}): the regrade on the current tests first"
                elif e["audited"] != gname:
                    e["action"], e["why"] = "reaudit", (f"repaired ({cov}) and regraded ({gname}); the untrusted "
                                                        f"audit of {e['audited']} is carried over: audit the regrade")
                else:
                    e["action"], e["why"] = "rerun", f"repaired ({cov}), the regrade audited and still untrusted"
            elif held:
                e["action"], e["why"] = "wait_repair", "held (.hold-repair): regraded after the repair, not re-run"
            elif active:
                e["action"], e["why"] = "wait_repair", "a repair job of the task is queued or running"
            else:
                if finding is None:
                    finding = repairstep.findings(slug, cfg, ctx)
                if finding.get("plan"):
                    e["action"], e["why"] = "wait_repair", f"the repair step plans a repair ({finding['key']})"
                else:
                    e["action"] = "rerun"
                    e["why"] = ("repaired, the regrade audited and still untrusted" if newest and when and when > newest
                                else "a test fault the repair step does not take on") + \
                        f" ({finding.get('why') or 'no repair planned'}): a fresh run"
        out.setdefault(e["model"], []).append(e)
    cache[slug] = out
    return out


def for_model(slug, model, ledger_cell, ctx=None):
    """The untrusted entries of one model, or [] when its ledger cell counts no untrusted audit or the model is
    blocked on the task (<MODEL>-BLOCKED.md, a hold_<model> that says blocked: never a run, even when the ledger
    has not caught up with the block yet)."""
    if not ledger_untrusted(ledger_cell) or markers.blocked(paths.BUILD / slug, model):
        return []
    try:
        return classify(slug, ctx).get(model, [])
    except Exception as e:                               # never let one unreadable trial stop a pass
        return [{"job": "", "trial": "", "model": model, "action": "error", "why": f"{type(e).__name__}: {e}"}]


def counts(entries):
    out = {}
    for e in entries:
        out[e["action"]] = out.get(e["action"], 0) + 1
    return out
