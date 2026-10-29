#!/usr/bin/env python3
"""Test repairs as queue work: what needs a repair, the test version a grading used, and lost repairs.

History (owner, 2026-10-28). The repair step already existed as the fairfix step
(pipelines/sibling/10-fairfix/run_fairfix.sh, pipelines/stacking/8-fairfix/run_fairfix_stack.sh): an Opus
orchestrator started it and the work ran on the VM through DeepSeek (`common/launch/drive.sh deepseek bash
pipelines/sibling/10-fairfix/run_fairfix.sh SLUG`). It was lost when the pipeline moved to the SQLite work queue: the
queue had no repair kind, so repairs were done by hand with Opus sub-agents. The `repair` kind (kinds/repair.py,
repairjob.py) brings it back as a queue job on DeepSeek. The owner once gave the (now dropped) hardening step the
runs' results it was missing: run_harden.sh ran trial_summary.py before its snapshot moved the runs out of jobs/
(pipelines/sibling/archive/hardening-dropped/run_harden.sh, 2026-10-21). Fairfix never got the same input; the repair
job passes the failing runs' evidence (repairjob.py: trial_summary.md, per-test failures, the final diff, transcript
excerpts).

Planning rule T1 (one `repair` job per finding, args {"finding": <key>}); the finding of a task is everything below
that no newer repair folder covers:
  (a) a recorded post-run audit (POSTMORTEM.json on the grading in use, or carried over) whose failing items are
      unfair (verdict test-fault / instruction-ambiguity, or an unfair_kind other than none). Planned when one of
      them decided a run (the run's attribution is test-fault / instruction-ambiguity, or the run fails no fair
      test), or, by the owner's standing rule "fix every unfair test", when the task is kept or delivered;
  (b) the fairness review is NOT_READY with test-only required changes (no current human decision), or its
      CONFLICTS line counts a deciding conflict (no CONFLICTS-RULED KEEP);
  (c) HUMAN-DECISION.md records a current DECISION: REPAIR.
  Never: the task is dropped or withdrawn; a repaired-tests-* / removed-tests-* / testfix-* folder is newer than the
  finding; a repair job already ran for the same finding (build/<slug>/repair-inputs-*/FINDING.json, or the job
  table); another repair of the task is queued or running; the task is held (.hold-repair: a repair cycle is in
  progress); [repair] max_per_task repairs already ran; with [repair] skip_solved, a model already solved a task
  that is not kept or delivered (no breaker to protect).
  [repair] auto = false (the first deploy): nothing is queued; the plan is shown by `cweq explain`, `cweq repairs`
  and the inbox, and the owner queues it with `cweq enqueue repair <slug> --args '{"finding": "<key>"}'`.

Test version of a grading (the regrade rule R2, reconcile.py): the content hash of tests/ that graded it, the same
20-hex hash as the verifier image tag (common/harbor_ext/cwe_reuse_tag.py): REGRADE.json "tests_hash" (written by
regrade_from_code.py and rescore_from_results.py since 2026-10-28) or the tag in its "image"; for the original
grading the `cwe-reuse/<task>:verifier-<hash>` image named in the run's trial.log. None when nothing records it.

    python3 -I common/queue/repairstep.py findings <slug>     the finding (JSON) and why it is or is not planned
    python3 -I common/queue/repairstep.py lost [--json]       tasks with a test-fault audit and no later repair
    python3 -I common/queue/repairstep.py record-tests <slug> <file>   write {"tests_hash", "written_utc"} (fairness)
"""
import calendar
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402
sys.path.insert(0, str(paths.COMMON / "harbor_ext"))
import cwe_reuse_tag  # noqa: E402  (context_hash: the verifier image's content hash of tests/)

import markers  # noqa: E402
import qdb  # noqa: E402

KIND = "repair"
REPAIR_GLOBS = ("repaired-tests-*", "removed-tests-*", "testfix-*")
INPUTS_GLOB = "repair-inputs-*"
UNFAIR_VERDICTS = ("test-fault", "instruction-ambiguity")
UNFAIR_ATTRIBUTIONS = ("test-fault", "instruction-ambiguity")
VERIFIER_TAG = re.compile(r"cwe-reuse/[a-z0-9._-]+:verifier-([0-9a-f]{20})")
NAME_DAY = re.compile(r"(20\d{6})")
CLIENT_AUDIT = re.compile(r"(?mi)^\s*CLIENT-AUDIT\s*:\s*(.+)$")
CONFLICTS = re.compile(r"(?mi)^[\s>*`_|-]*CONFLICTS[*`_]*\s*[:=]\s*[*`_]*\s*(\d+)\b([^\n]*)$")
DECIDING = re.compile(r"(?i)DECIDING[*`_]*\s*[:=]?\s*[*`_]*\s*(\d+|unknown)")
CONFLICTS_RULED = re.compile(r"(?mi)^\s*CONFLICTS-RULED\s*:\s*(\d{4}-\d{2}-\d{2})\s+(KEEP|DROP|REPAIR)\b")
INSTRUCTION_WORDS = re.compile(r"(?i)instruction|wording|reword|sentence|phrase")
TEST_WORDS = re.compile(r"(?i)\btests?/|\btests?\b|fixture|score\.py|assert|harness|oracle|fix\.patch|reference")
DEFAULTS = {"auto": False, "lift_holds": True, "max_per_task": 3, "skip_solved": True, "timeout_sec": 10800,
            "wait_sec": 7200, "static_check": True, "agent_cmd": [], "cleanup_image": "alpine:3", "trial_summary": True}


def settings(cfg):
    return {**DEFAULTS, **((cfg or {}).get("repair") or {})}


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def read(p, limit=None):
    try:
        with open(p, errors="replace") as f:
            return f.read(limit) if limit else f.read()
    except OSError:
        return ""


def mtime(p):
    try:
        return Path(p).stat().st_mtime
    except OSError:
        return None


# ---------------------------------------------------------------- test versions

_hash_cache = {}


def tests_hash(slug):
    """20-hex content hash of tasks/<slug>/tests/ (the verifier image tag's hash), '' when there is no tests/."""
    t = paths.TASKS / slug / "tests"
    if not t.is_dir():
        return ""
    sig = []
    for d, dirs, files in os.walk(t):
        dirs[:] = [x for x in dirs if x not in cwe_reuse_tag._IGNORE]
        for name in files:
            try:
                st = os.lstat(os.path.join(d, name))
                sig.append((os.path.join(d, name), st.st_size, st.st_mtime_ns, st.st_mode))
            except OSError:
                pass
    sig = tuple(sorted(sig))
    hit = _hash_cache.get(str(t))
    if hit and hit[0] == sig:
        return hit[1]
    h = cwe_reuse_tag.context_hash(t)[:20]
    _hash_cache[str(t)] = (sig, h)
    return h


def regrade_tests_hash(info):
    """The test version a regrade or rescore graded on (REGRADE.json), or None."""
    h = (info or {}).get("tests_hash")
    if h:
        return str(h)[:20]
    m = VERIFIER_TAG.search(str((info or {}).get("image", "")))
    return m.group(1) if m else None


def original_tests_hash(trial):
    """The test version of a run's original grading: the verifier image its trial.log names, or None."""
    text = read(Path(trial) / "trial.log", 8 << 20)
    hits = VERIFIER_TAG.findall(text)
    return hits[-1] if hits else None


def valid_regrade(d, info):
    """A regrade folder counts as a grading only when it scored (the regrade post-conditions: a numeric reward in
    REGRADE.json and in verifier/reward.json). A failed regrade does not count as done."""
    def num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    return num((info or {}).get("reward")) and num((jload(Path(d) / "verifier" / "reward.json") or {}).get("reward"))


def grading_in_use(run):
    """(name, tests hash or None, epoch) of the grading a run counts with now: its newest valid regrade, else the
    original grading. run: a reconcile.graded_runs() entry."""
    for when, info, d in sorted(run.get("regrade_dirs", []), key=lambda x: x[0], reverse=True):
        if valid_regrade(d, info):
            return Path(d).name, regrade_tests_hash(info), when
    return "original", original_tests_hash(run["path"]), run["graded"]


# ---------------------------------------------------------------- repair folders and coverage

def repair_folders(b):
    """[(name, epoch)] of the task's repair folders (repaired-tests-*, removed-tests-*, testfix-*)."""
    out = []
    for g in REPAIR_GLOBS:
        for p in Path(b).glob(g):
            if p.is_dir():
                out.append((p.name, folder_time(p)))
    return sorted(out, key=lambda x: x[1])


def folder_time(p):
    """When a repair folder was made: the end of the day in its name when its mtime is a later day (a folder touched
    later), else its mtime; the start of that day when the mtime is older than the name says (copied with -p)."""
    mt = mtime(p) or 0.0
    m = NAME_DAY.search(Path(p).name)
    if not m:
        return mt
    day = calendar.timegm(time.strptime(m.group(1), "%Y%m%d"))
    if mt < day:
        return float(day)
    if mt >= day + 86400:
        return float(day + 86399)
    return mt


def covering(b, when):
    """The newest repair folder made after `when` (epoch), or None."""
    later = [n for n, t in repair_folders(b) if when is not None and t > when]
    return later[-1] if later else None


# ---------------------------------------------------------------- audits

def grading_name(trial):
    regs = sorted(p for p in Path(trial).glob("regrade-*") if (p / "verifier").is_dir())
    return regs[-1].name if regs else "original"


def _grading_reward(trial, grading):
    if grading == "original":
        return (((jload(Path(trial) / "result.json") or {}).get("verifier_result") or {}).get("rewards") or {}).get("reward")
    return (jload(Path(trial) / grading / "REGRADE.json") or {}).get("reward")


def current_audit(trial):
    """(POSTMORTEM.json dict, folder) of the run's newest RECORDED audit when it audited the grading in use (or is
    carried over to a regrade with the same reward, as audit_results.py does), else None."""
    pms = sorted(Path(trial).glob("postmortem-*/POSTMORTEM.json"))
    if not pms:
        return None
    pm = jload(pms[-1]) or {}
    audited, cur = pm.get("grading_audited") or "original", grading_name(trial)
    if audited != cur:
        if not (cur.startswith("regrade-") and (audited == "original" or audited < cur)):
            return None
        r_old, r_new = _grading_reward(trial, audited), _grading_reward(trial, cur)
        if r_old is None or r_old != r_new:
            return None
    return pm, pms[-1].parent


def unfair_items(v):
    """Failing items of a verdict the auditor calls unfair."""
    out = []
    for it in (v or {}).get("items") or []:
        if not isinstance(it, dict) or it.get("outcome") != "fail":
            continue
        kind = str(it.get("unfair_kind") or "none").strip().lower()
        if it.get("verdict") in UNFAIR_VERDICTS or kind not in ("none", ""):
            out.append(it)
    return out


def audit_deciding(v, unfair):
    """True when the unfair tests decided the run: the auditor attributes the run to the tests or the instruction, or
    the run fails no fair test (FAIRNESS-REVIEW-BRIEF.md step 1a)."""
    if (v or {}).get("attribution") in UNFAIR_ATTRIBUTIONS:
        return True
    fails = [it for it in (v or {}).get("items") or [] if isinstance(it, dict) and it.get("outcome") == "fail"]
    return bool(unfair) and len(unfair) == len(fails)


def stamp_epoch(name):
    m = re.search(r"(\d{8}T\d{6}Z)", name)
    return calendar.timegm(time.strptime(m.group(1), "%Y%m%dT%H%M%SZ")) if m else None


def task_trials(slug, jobs_dir, index=None):
    """Trial folders of a task in jobs/ (by the <slug>__<id> name)."""
    if index is not None:
        return index.get(slug, [])
    return sorted(t for t in Path(jobs_dir).glob(f"*/{slug}__*") if t.is_dir())


def trial_index(jobs_dir):
    """{slug: [trial folders]} for every trial in jobs/ (one directory listing per job)."""
    out = {}
    for t in Path(jobs_dir).glob("*/*__*"):
        if t.is_dir():
            out.setdefault(t.name.split("__")[0], []).append(t)
    return {k: sorted(v) for k, v in out.items()}


def audit_items(slug, jobs_dir, index=None):
    """One entry per run whose current recorded audit names unfair failing tests (or attributes the run to them)."""
    out = []
    for t in task_trials(slug, jobs_dir, index):
        cur = current_audit(t)
        if not cur:
            continue
        pm, folder = cur
        v = pm.get("verdict") or {}
        unfair = unfair_items(v)
        run_level = v.get("attribution") in UNFAIR_ATTRIBUTIONS
        if not unfair and not run_level:
            continue
        tests = unfair or [it for it in v.get("items") or [] if isinstance(it, dict) and it.get("outcome") == "fail"]
        prepared = stamp_epoch(folder.name) or mtime(folder / "PREPARED.json")
        m = re.search(r"-(deepseek|mimo)-r(\d+)-", t.parent.name)
        out.append({
            "source": "audit", "ref": f"{t.parent.name}/{t.name}/{folder.name}", "trial": f"{t.parent.name}/{t.name}",
            "model": m.group(1) if m else "", "run": f"r{m.group(2)}" if m else "", "postmortem": str(folder),
            "audited": pm.get("grading_audited"), "recorded": pm.get("recorded_utc"), "when": prepared,
            "attribution": v.get("attribution"), "confidence": v.get("confidence"),
            "trustworthy": v.get("trustworthy"), "deciding": audit_deciding(v, unfair),
            "summary": str(v.get("summary") or "")[:4000], "recommended_action": v.get("recommended_action"),
            "reward": _grading_reward(t, grading_name(t)),
            "tests": [{k: it.get(k) for k in ("test", "verdict", "unfair_kind", "model_behaviour",
                                                "stated_in_instruction", "correct_fix_would_pass",
                                                "conflicting_sentences", "other_reading_fails") if k in it}
                      for it in tests]})
    return out


# ---------------------------------------------------------------- fairness review and decisions

def conflicts(slug):
    """(n, deciding) from the review's CONFLICTS line (fairness_verdict.conflicts when present), or None."""
    import taskstate
    fv = taskstate.fairness_verdict
    if hasattr(fv, "conflicts"):
        return fv.conflicts(slug)
    hits = CONFLICTS.findall(read(paths.BUILD / slug / "FAIRNESS.md"))
    if not hits:
        return None
    n, rest = int(hits[-1][0]), hits[-1][1]
    m = DECIDING.search(rest)
    return n, (n if not m or m.group(1).lower() == "unknown" else min(n, int(m.group(1))))


def required_text(text):
    """The review's required-change text: 'Required ...' sections and the Conflicts table, or ''."""
    parts = re.findall(r"(?ims)^[#*\s]*(?:required[^\n]*|conflicts?(?: table)?)\s*:?[*\s]*\n(.+?)(?=^#|^GATE_A|^CONFLICTS:|\Z)",
                       text)
    return "\n".join(p.strip() for p in parts)[:6000]


def fairness_item(slug):
    """A finding from the fairness review, or None (see T1 (b)). Adds 'note' when it cannot be planned."""
    import taskstate
    fv = taskstate.fairness_verdict
    b = paths.BUILD / slug
    f = b / "FAIRNESS.md"
    if not f.is_file():
        return None
    v, why = fv.verdict(slug)
    if v == "ERROR":
        return None
    hd = fv.human_decision(slug)
    text = read(f)
    c = conflicts(slug)
    ruled = CONFLICTS_RULED.findall(read(b / "HUMAN-DECISION.md"))
    fday = time.strftime("%Y-%m-%d", time.gmtime(mtime(f) or 0))
    ruling = ruled[-1][1].upper() if ruled and ruled[-1][0] >= fday else None
    req = required_text(text)
    item = {"source": "fairness", "ref": "FAIRNESS.md:" + hashlib.sha256(text.encode()).hexdigest()[:12],
            "when": mtime(f), "verdict": v, "conflicts": list(c) if c else None, "required": req,
            "deciding": True, "tests": []}
    if c and c[0] > 0 and ruling in ("KEEP", "DROP"):
        return None                                      # the owner ruled on the conflicts (CONFLICTS-RULED)
    if c and c[1] > 0:
        item["why"] = f"{c[1]} deciding conflict(s) (CONFLICTS: {c[0]})" + (" ruled REPAIR" if ruling else "")
        return item
    if v != "NOT_READY" or (hd and not hd[2]):
        return None
    if c and c[0] > 0:
        item["why"] = f"NOT_READY with {c[0]} conflict(s): the brief's remedy is a test change"
        return item
    if req and TEST_WORDS.search(req) and not INSTRUCTION_WORDS.search(req):
        item["why"] = "NOT_READY, required changes are test-only"
        return item
    item["note"] = ("fairness NOT_READY but the required change may touch the instruction (or names none): "
                    "not a test-only repair, a person decides")
    return item


def decision_item(slug):
    b = paths.BUILD / slug
    hd = markers.human_decision(b)
    if not hd or hd[2] or hd[0] != "REPAIR":
        return None
    text = read(b / "HUMAN-DECISION.md")
    return {"source": "decision", "ref": f"DECISION REPAIR {hd[1]}", "when": mtime(b / "HUMAN-DECISION.md"),
            "why": f"owner DECISION: REPAIR {hd[1]}", "text": text[-3000:], "deciding": True, "tests": []}


def excluded(slug):
    """Why a task gets no repair (dropped, withdrawn), or None."""
    b = paths.BUILD / slug
    hd = markers.human_decision(b)
    if hd and not hd[2] and hd[0] == "DROP":
        return f"dropped (DECISION: DROP {hd[1]})"
    ca = CLIENT_AUDIT.findall(read(b / "HUMAN-DECISION.md"))
    if ca and ca[-1].strip().upper().startswith("WITHDRAW"):
        return "withdrawn (CLIENT-AUDIT: WITHDRAW)"
    if (b / ".terminal").exists():
        return "terminal (.terminal)"
    return None


def kept_or_delivered(slug, ctx=None):
    b = paths.BUILD / slug
    hd = markers.human_decision(b)
    return bool((hd and not hd[2] and hd[0] == "KEEP") or markers.delivered_line(b)
                or slug in ((ctx or {}).get("delivered") or {}))


def finding_key(items):
    mat = sorted([it["source"], it["ref"], sorted(str(x.get("test")) for x in it.get("tests", []))] for it in items)
    return "f-" + hashlib.sha256(json.dumps(mat, sort_keys=True).encode()).hexdigest()[:16]


def past_findings(b):
    """{finding key: (inputs folder, job result dict or {})} of the repairs that already ran."""
    out = {}
    for d in sorted(Path(b).glob(INPUTS_GLOB)):
        f = jload(d / "FINDING.json") or {}
        if f.get("key"):
            out[f["key"]] = (d, jload(d / "JOB-RESULT.json") or {})
    return out


def findings(slug, cfg, ctx=None, index=None):
    """{key, items, plan: bool, why, notes} for one task: the uncovered unfair findings and whether T1 plans them."""
    b = paths.BUILD / slug
    st = settings(cfg)
    notes, items = [], []
    for it in audit_items(slug, cfg["jobs_dir"], index):
        cov = covering(b, it["when"])
        if cov:
            continue
        items.append(it)
    for it in (fairness_item(slug), decision_item(slug)):
        if not it:
            continue
        if it.get("note"):
            notes.append(it["note"])
            continue
        cov = covering(b, it["when"])
        if cov:
            notes.append(f"{it['source']} finding covered by {cov}")
            continue
        items.append(it)
    out = {"task": slug, "items": items, "key": finding_key(items) if items else None, "plan": False, "why": "",
           "notes": notes}
    if not items:
        return out
    deciding = [it for it in items if it.get("deciding")]
    kept = kept_or_delivered(slug, ctx)
    ex = excluded(slug)
    past = past_findings(b)
    runs = sum(1 for _d, r in past.values() if r.get("result") == "repaired")
    if ex:
        out["why"] = f"no repair: {ex}"
    elif out["key"] in past:
        d, r = past[out["key"]]
        out["why"] = f"a repair already ran for this finding ({d.name}: {r.get('result') or 'no result recorded'})"
    elif not deciding and not kept:
        out["why"] = "unfair tests that decided no run, task not kept or delivered: fairness review / owner"
    elif runs >= int(st["max_per_task"]):
        out["why"] = f"{runs} repairs already ran (max_per_task {st['max_per_task']}): a person looks"
    elif st["skip_solved"] and not kept and _any_solved(slug, ctx):
        out["why"] = "a model already solved the task and it is not kept: no breaker to protect"
    elif (b / ".hold-repair").exists():
        out["why"] = "held (.hold-repair): a repair cycle is in progress; planned again once the hold is lifted"
    else:
        out["plan"] = True
        out["why"] = ("deciding unfair test(s)" if deciding else "standing rule: fix every unfair test (kept/delivered)")
    return out


def _any_solved(slug, ctx):
    import taskstate
    led = ((ctx or {}).get("ledger") or taskstate.ledger()).get(slug, {})
    return any(taskstate.ledger_model(led.get(m, "")) == "solved" for m in taskstate.MODELS)


def candidates(cfg, index):
    """Tasks worth a look: any recorded audit with unfair items, a fairness review, a REPAIR decision."""
    out = set()
    for slug, trials in index.items():
        if any(t.glob("postmortem-*/POSTMORTEM.json") for t in trials) and (paths.TASKS / slug).is_dir():
            out.add(slug)
    for p in paths.BUILD.glob("*/FAIRNESS.md"):
        out.add(p.parent.name)
    for p in paths.BUILD.glob("*/HUMAN-DECISION.md"):
        if "REPAIR" in read(p):
            out.add(p.parent.name)
    return sorted(s for s in out if (paths.TASKS / s).is_dir())


# ---------------------------------------------------------------- the plan (kinds/repair.py plan)

def active_repairs(conn, slug):
    return qdb.jobs(conn, "kind=? AND task=? AND state IN ('queued','leased','running')", (KIND, slug))


def plan(conn, cfg, ctx, states, dry_run=False, slugs=None):
    """T1: one repair job per uncovered finding. Returns reconcile reports {task, stage, want, notes}."""
    st = settings(cfg)
    index = trial_index(cfg["jobs_dir"])
    out = []
    for slug in (slugs or candidates(cfg, index)):
        f = findings(slug, cfg, ctx, index)
        if not f["items"] and not f["notes"]:
            continue
        rep = {"task": slug, "stage": (states or {}).get(slug, {}).get("stage", "repair"), "want": [],
               "notes": list(f["notes"]), "finding": f}
        if f["items"] and not f["plan"]:
            rep["notes"].append(f"repair not planned ({f['key']}): {f['why']}")
        if f["plan"]:
            args = {"finding": f["key"]}
            act = [r for r in active_repairs(conn, slug)] if conn is not None else []
            same = [r for r in act if qdb.args_of(r).get("finding") == f["key"]]
            if act and not same:
                if not dry_run:
                    for r in act:
                        if r["state"] == "queued" and r["origin"] == "reconciler":
                            qdb.set_state(conn, r["id"], "failed", "superseded: the finding changed (new audit or "
                                                                   "fairness review)")
                if any(r["state"] != "queued" or r["origin"] != "reconciler" for r in act):
                    rep["notes"].append(f"another repair of the task is queued or running (#{act[0]['id']})")
                    out.append(rep)
                    continue
            want = {"kind": KIND, "args": args, "why": f["why"]}
            if not st["auto"] and not same:
                want["planned_only"] = True
                rep["notes"].append(f"repair planned, not queued ([repair] auto = false): cweq enqueue repair {slug} "
                                    f"--args '{json.dumps(args)}'  ({f['why']})")
                if not dry_run and conn is not None:
                    try:
                        import events
                        events.ensure(conn)
                        events.emit(conn, "repair.planned", f"repair:{slug}:{f['key']}", slug,
                                    {"finding": f["key"], "why": f["why"]})
                    except Exception:
                        pass                             # bookkeeping: never fail a pass over an event
            elif not dry_run and conn is not None:
                jid, _ = qdb.enqueue(conn, KIND, slug, args, priority=cfg["priority"].get(KIND, 0),
                                     max_attempts=cfg["max_attempts"].get(KIND, 2), origin="reconciler")
                want["id"] = jid
            rep["want"].append(want)
        out.append(rep)
    return out


# ---------------------------------------------------------------- lost repairs (report, inbox)

def lost(cfg, index=None):
    """Tasks with a test-fault audit and no later repaired-tests-* / removed-tests-* / testfix-* folder.
    [{task, since, runs, attribution, excluded, planned}] oldest first."""
    index = trial_index(cfg["jobs_dir"]) if index is None else index
    out = []
    for slug in sorted(index):
        if not (paths.TASKS / slug).is_dir():
            continue
        items = [it for it in audit_items(slug, cfg["jobs_dir"], index)
                 if it.get("attribution") == "test-fault" or any(x.get("verdict") == "test-fault" for x in it["tests"])]
        b = paths.BUILD / slug
        open_ = [it for it in items if not covering(b, it["when"])]
        if not open_:
            continue
        since = min(it["when"] or 0 for it in open_)
        out.append({"task": slug, "since": time.strftime("%Y-%m-%d", time.gmtime(since)), "since_epoch": since,
                    "runs": len(open_), "attribution": sorted({str(it.get("attribution")) for it in open_}),
                    "excluded": excluded(slug) or "", "repairs": [n for n, _t in repair_folders(b)]})
    return sorted(out, key=lambda r: r["since_epoch"])


def inbox_items(conn, cfg):
    """Inbox lines: lost repairs, repairs planned but not queued (auto off), failed repairs (hold kept)."""
    items = []
    index = trial_index(cfg["jobs_dir"])
    rows = [r for r in lost(cfg, index) if not r["excluded"]]
    if rows:                                             # one line: the list is in `cweq repairs --lost`
        items.append({"task": f"{len(rows)} task(s)", "summary": "lost repairs: a test-fault audit and no later "
                                                                "repaired-tests-* / removed-tests-* / testfix-* folder",
                      "detail": "; ".join(f"{r['task']} since {r['since']} ({r['runs']} run(s))" for r in rows)
                      + " (cweq repairs --lost)"})
    for rep in plan(conn, cfg, None, {}, dry_run=True):
        for w in rep["want"]:
            if w.get("planned_only"):
                items.append({"task": rep["task"], "summary": f"repair planned ({w['why']}), auto off",
                              "detail": f"cweq enqueue repair {rep['task']} --args '{json.dumps(w['args'])}'"})
    for h in paths.BUILD.glob("*/.hold-repair"):
        text = read(h, 2000).strip()
        if text.startswith("repair failed"):
            items.append({"task": h.parent.name, "summary": "repair failed, task held", "detail": text[:600]})
    return items


def record_tests(slug, out):
    p = Path(out)
    if not p.is_absolute():
        p = paths.BUILD / slug / p
    markers.write_atomic(p, json.dumps({"slug": slug, "tests_hash": tests_hash(slug), "written_utc": qdb.utc()}) + "\n")


def main(argv):
    if len(argv) >= 3 and argv[1] == "findings":
        import config
        cfg = config.load()
        print(json.dumps(findings(argv[2], cfg), indent=1, default=str))
        return 0
    if len(argv) >= 2 and argv[1] == "lost":
        import config
        cfg = config.load()
        rows = lost(cfg)
        if "--json" in argv:
            print(json.dumps(rows, indent=1))
        else:
            print(f"lost repairs: {len(rows)} task(s) with a test-fault audit and no later repair folder")
            for r in rows:
                print(f"  {r['task']:<34} since {r['since']}  runs {r['runs']}  {'/'.join(r['attribution'])}"
                      f"{'  [' + r['excluded'] + ']' if r['excluded'] else ''}"
                      f"  repairs: {', '.join(r['repairs']) or '-'}")
        return 0
    if len(argv) == 4 and argv[1] == "record-tests":
        record_tests(argv[2], argv[3])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
