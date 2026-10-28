#!/usr/bin/env python3
"""Rebuild the results ledger from the RAW trial folders only.

    python3 common/audit/audit_results.py

Reads every trial folder under ~/.tb-graders/cwe/jobs (every trial in every job — early
jobs ran 3 trials in one job; ext-actions-* jobs are runs made on GitHub Actions and imported, see
build/audit/EXTERNAL-RUNS.md), and nothing else: not queue.json, not runs_<model>.log,
not trial_detail_*.json. Those derived files were written by a reader with two bugs (see
docs/history/RESULTS-AUDIT.md) and are superseded by this script.

Writes:
    build/audit/trials.tsv   one row per trial, ordered task / model / start time
    build/audit/ledger.md    per-task, per-model table + one-model-failure table

Rules:
    graded run   = the verifier produced a reward, INCLUDING runs cut at the agent time
                   limit (grade-at-timeout, as CWE-bench does)
    leaked run   = the agent read or ran hidden tests baked into the image (listed in
                   build/audit/contaminated.tsv); excluded from verdicts
    needs review = a non-solve whose grading setup broke (common/audit/review_flags.py); not a
                   model failure until build/audit/reviews.tsv decides model / harness
    cut run      = graded run cut by a SHORTER limit than the task's current one
                   (e.g. 60 min before the switch to 120 min) that did not solve; it is
                   not a failure under the current limit and is shown separately
    ungraded run = no reward (cancelled, rate-limited, agent crashed, timed out before
                   grading); never counted as a model failure
    SOLVED       = at least one graded run with reward 1.0
    failed       = at least one graded run and none at 1.0
    BREAKER      = both models failed (and each has >= 3 graded runs for a full pass@3)

Notes (2026-10-28): build/audit/ledger_notes.tsv (task, model, job, trial, kind, note) adds remarks about a
per-model verdict, e.g. a solve that used the file-time leak (reports/reward-hacking.md). Notes never change a
verdict; they are listed in a "## Notes" section at the end of ledger.md, after the tables.
"""
import json
import re
import time
from datetime import datetime
import sys
from pathlib import Path

from review_flags import setup_flags

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = paths.ROOT
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
OUT = ROOT / "build" / "audit"
TRACK_ORDER = {"mined": 0, "stacking": 1, "injection": 2, "precision-validation": 3}
MODELS = (("deepseek", "DeepSeek"), ("mimo", "MiMo"))
# Agent time limit of runs that predate CWE_AGENT_LIMIT_SEC (all runs before the
# 2026-10-15 switch to 7200 s ran at 3600 s; each task had one checksum throughout).
PRE_LIMIT_SEC = 3600


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None


def track_of(task):
    # pv-*: built by the closed precision_validation experiment (experiments/precision_validation), trialled on
    # GitHub Actions; its runs are imported as ext-actions-* jobs (see build/audit/EXTERNAL-RUNS.md).
    if task.startswith("pv-"):
        return "precision-validation"
    # stk- tasks are stacking by name: some scale-run builders wrote source = "injected" (2026-10-26).
    if task.startswith("stk-"):
        return "stacking"
    toml = ROOT / "tasks" / task / "task.toml"
    m = re.search(r'^\s*source\s*=\s*"([^"]+)"', toml.read_text(), re.M) if toml.is_file() else None
    src = m.group(1) if m else "?"
    return "stacking" if "stacking" in src else "injection" if "injected" in src else "mined"


def read_trial(trial):
    cfg = jload(trial / "config.json") or {}
    res = jload(trial / "result.json") or {}
    agent = cfg.get("agent") or {}
    task = Path((cfg.get("task") or {}).get("path", "")).name
    reward = ((res.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    if reward is None:
        reward = (jload(trial / "verifier" / "reward.json") or {}).get("reward")
    verifier = trial / "verifier"
    # A re-grade of the final output (common/audit/regrade.py) replaces a grading that broke.
    # Only finished regrades (REGRADE.json is written last); one still running is ignored.
    regrades = sorted(r.parent / "verifier" / "reward.json" for r in trial.glob("regrade-*/REGRADE.json")
                      if (r.parent / "verifier" / "reward.json").is_file())
    if regrades:
        verifier = regrades[-1].parent
        reward = (jload(verifier / "reward.json") or {}).get("reward")
    tests = jload(verifier / "results.json") or {}

    def frac(k):
        v = list((tests.get(k) or {}).values())
        return f"{sum(x == 'pass' for x in v)}/{len(v)}" if v else ""

    ex = res.get("exception_info") or {}
    ae = res.get("agent_execution") or {}
    mins = ""
    if ae.get("started_at") and ae.get("finished_at"):
        a, b = (datetime.fromisoformat(ae[k].replace("Z", "+00:00")) for k in ("started_at", "finished_at"))
        mins = round((b - a).total_seconds() / 60)
    if regrades:
        note = f"regraded ({verifier.parent.name})"
    elif not res:
        note = "no result.json (killed)"
    elif ex:
        note = ex.get("exception_type", "?") + (" (graded)" if reward is not None else "")
    else:
        note = ""
    env = agent.get("env") or {}
    # A session ended by an API/network error (Claude Code terminal_reason "api_error", e.g. the local
    # DNS outage of 2026-10-16 13:51 UTC) was cut off, not finished: its grade measures unfinished code.
    log = trial / "agent" / "claude-code.txt"
    api_cut = bool(ex) and log.is_file() and '"terminal_reason":"api_error"' in log.read_text(errors="replace")[-20000:]
    return {"task": task, "api_cut": api_cut, "model": agent.get("model_name", ""), "start_utc": (res.get("started_at") or "")[:16],
            "limit_sec": int(env.get("CWE_AGENT_LIMIT_SEC", PRE_LIMIT_SEC)),
            "timed_out": ex.get("exception_type") == "AgentTimeoutError",
            "reward": reward, "security": frac("security"), "functional": frac("functional"),
            "agent_min": mins, "note": note, "env": ",".join(sorted((agent.get("env") or {}).keys())),
            "checksum": (res.get("task_checksum") or "")[:12], "job": trial.parent.name, "trial": trial.name,
            "regraded": bool(regrades),
            "grading": verifier.parent.name if regrades else "original",
            "flags": "; ".join(setup_flags(trial, verifier)) if reward is not None and reward != 1.0 else ""}


def model_key(name):
    return "deepseek" if "deepseek" in name else "mimo" if "mimo" in name else None


def task_limit(task):
    toml = ROOT / "tasks" / task / "task.toml"
    sec, cur = None, None
    for line in toml.read_text().splitlines():
        m = re.match(r"\s*\[(.+)\]", line)
        cur = m.group(1) if m else cur
        m = re.match(r"\s*timeout_sec\s*=\s*([0-9.]+)", line)
        if m and cur == "agent":
            sec = int(float(m.group(1)))
    return sec


def contaminated():
    """(job, trial) pairs whose agent read or ran the hidden tests (see the file's header)."""
    f = OUT / "contaminated.tsv"
    if not f.is_file():
        return set()
    return {tuple(l.split("\t")[:2]) for l in f.read_text().splitlines()
            if l and not l.startswith(("#", "job\t"))}


def task_defects():
    """task -> (fixed_utc or "", kind) from task_defects.tsv: the task's build leaked the answer, so
    its runs that started before fixed_utc (all, if empty) do not count."""
    f = OUT / "task_defects.tsv"
    if not f.is_file():
        return {}
    out = {}
    for l in f.read_text().splitlines():
        if l and not l.startswith(("#", "task\t")):
            c = l.split("\t")
            out[c[0]] = (c[1] if len(c) > 1 else "", c[2] if len(c) > 2 else "task-defect")
    return out


def excluded_runs():
    """(job, trial) -> kind, from excluded_runs.tsv: runs whose grading can no longer be trusted
    and cannot be regraded (no saved final code). Kinds: 'test-fault' (the run failed a test
    since found faulty and repaired; see docs/research/own-runs/FINDINGS.md) and 'provider-stop'
    (the model provider refused the request mid-run: an infrastructure stop, not a result)."""
    f = OUT / "excluded_runs.tsv"
    if not f.is_file():
        return {}
    return {tuple(l.split("\t")[:2]): l.split("\t")[2] for l in f.read_text().splitlines()
            if l and not l.startswith(("#", "job\t"))}


def postmortem_state(job, trial, grading):
    """'trusted' / 'untrusted' / 'awaiting' from the newest <trial>/postmortem-*/POSTMORTEM.json
    (common/audit/postmortem.py). A postmortem only counts if it audited the grading now in use."""
    d = JOBS / job / trial
    pms = sorted(d.glob("postmortem-*/POSTMORTEM.json"))
    if not pms:
        return "awaiting"
    pm = jload(pms[-1]) or {}
    audited, current = pm.get("grading_audited"), grading or "original"
    if audited != current:
        # Carry-over (2026-10-16): a newer regrade re-runs repaired tests on the SAME saved code. The
        # audit (contamination, tampering, what the code does) still holds when the reward is the
        # same; only a changed reward needs a fresh audit. Carried-over trials are listed in
        # build/audit/audit_carryover.tsv.
        if not (current.startswith("regrade-") and audited and (audited == "original" or audited < current)):
            return "awaiting"
        r_old, r_new = grading_reward(d, audited), grading_reward(d, current)
        if r_old is None or r_old != r_new:
            return "awaiting"
        CARRYOVER.append((job, trial, audited, current, r_new))
    v = pm.get("verdict") or {}
    return "trusted" if v.get("trustworthy") is True else "untrusted"


CARRYOVER = []


def grading_reward(trial_dir, grading):
    """Reward of one grading of a trial: 'original' (result.json) or a regrade-<UTC> folder."""
    if grading == "original":
        res = jload(trial_dir / "result.json") or {}
        return ((res.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    return (jload(trial_dir / grading / "REGRADE.json") or {}).get("reward")


def reviews():
    """(job, trial, grading) -> 'model' | 'harness'. grading = 'original' or the
    regrade-<UTC> folder the decision is about (optional 6th column; default original)."""
    f = OUT / "reviews.tsv"
    if not f.is_file():
        return {}
    out = {}
    for l in f.read_text().splitlines():
        if l and not l.startswith(("#", "job\t")):
            c = l.split("\t")
            out[(c[0], c[1], c[5] if len(c) > 5 and c[5] else "original")] = c[2]
    return out


def ledger_notes():
    """[{task, model, job, trial, kind, note}] from ledger_notes.tsv (remarks only: never change a verdict)."""
    f = OUT / "ledger_notes.tsv"
    if not f.is_file():
        return []
    cols = ("task", "model", "job", "trial", "kind", "note")
    out = []
    for l in f.read_text().splitlines():
        if l and not l.startswith(("#", "task\t")):
            c = l.split("\t")
            out.append(dict(zip(cols, c + [""] * (len(cols) - len(c)))))
    return out


AWAITING = []          # graded runs that would count but have no current post-run audit
TIMEOUT_RERUNS = []
WEB_TOOLS_OFF_UTC = "2026-10-16T00:33"   # run_trial.sh passes disallowed_tools=WebSearch,WebFetch from here on    # non-solves that timed out under 3 h: owed a 3 h re-run


def cell(runs, limit, tainted=frozenset(), decided=None, excluded=None):
    if not runs:
        return "not run", None
    # Runs whose old grading was faulty and that cannot be regraded prove nothing: excluded.
    excluded = excluded or {}
    fault = [r for r in runs if excluded.get((r["job"], r["trial"])) == "test-fault"]
    defects = task_defects()
    leaked_task = [r for r in runs if r["task"] in defects
                   and (not defects[r["task"]][0] or (r.get("start_utc") or "") < defects[r["task"]][0])]
    stopped = [r for r in runs if excluded.get((r["job"], r["trial"])) == "provider-stop"
               or (r.get("api_cut") and r["reward"] != 1.0)]
    runs = [r for r in runs if r not in fault and r not in stopped and r not in leaked_task]
    # Runs that used leaked hidden tests prove nothing about the model: excluded.
    leaked = [r for r in runs if (r["job"], r["trial"]) in tainted]
    runs = [r for r in runs if r not in leaked]
    # A solve under a shorter limit is still a solve; a failure caused by a shorter
    # limit cutting the run is not a failure under the current limit.
    cut = [r for r in runs if r["timed_out"] and r["limit_sec"] < limit and r["reward"] != 1.0]
    runs = [r for r in runs if r not in cut]
    # User rule (2026-10-20, supersedes 2026-10-16): a timeout IS a model failure once an independent
    # post-run audit records it as a genuine model-failed time-limit miss (postmortem trustworthy);
    # such an audited timeout counts as a graded fail at whatever limit it ran. An UN-audited sub-3h
    # timeout is still owed a 3 h re-run (its grade measures unfinished code until the audit confirms
    # the miss is a genuine capability shortfall, not an infra/provider cut). A 3 h timeout always counts.
    rerun_3h = [r for r in runs if r["timed_out"] and r["reward"] not in (None, 1.0)
                and r["limit_sec"] < 10800
                and postmortem_state(r["job"], r["trial"], r["grading"]) != "trusted"]
    runs = [r for r in runs if r not in rerun_3h]
    TIMEOUT_RERUNS.extend(rerun_3h)
    # A non-solve whose grading setup broke is not a model failure until reviewed:
    # 'model' -> counts as a graded fail; 'harness' -> excluded (our fault).
    decided = decided or {}
    # A review decision describes the ORIGINAL grading; a regraded run is judged on its regrade.
    dec = lambda r: decided.get((r["job"], r["trial"], r["grading"]))
    review = [r for r in runs if r["flags"] and dec(r) != "model"]
    harness = [r for r in review if dec(r) == "harness"]
    pending = [r for r in review if r not in harness]
    runs = [r for r in runs if r not in review]
    # Every graded FAILING run needs an independent post-run audit (common/audit/postmortem.py) before it can
    # count: awaiting -> not yet final; untrusted -> excluded until a human decides.
    # Solves are not audited (user decision 2026-10-25: solve audits rarely change a verdict and are not worth
    # the throughput). An unaudited solve counts as graded and is marked "solves counted, not audited"; an
    # audited solve that came back untrusted is still excluded.
    audit = {id(r): postmortem_state(r["job"], r["trial"], r["grading"]) for r in runs if r["reward"] is not None}
    unaudited_solves = [r for r in runs if audit.get(id(r)) == "awaiting" and r["reward"] == 1.0]
    awaiting = [r for r in runs if audit.get(id(r)) == "awaiting" and r["reward"] != 1.0]
    untrusted = [r for r in runs if audit.get(id(r)) == "untrusted"]
    runs = [r for r in runs if r not in awaiting and r not in untrusted]
    AWAITING.extend(awaiting)
    # CWE-bench runs agents OFFLINE (only the model API; arXiv 2610.17020). Before a task's switch
    # (build/audit/offline_since.tsv) its trials had open internet: a SOLVE counts only if the run
    # did no internet lookup (common/audit/internet_use.py). Failures with more access still count.
    from internet_use import cached_hits, offline_since
    since = offline_since()
    # Offline network but web tools still on (until WEB_TOOLS_OFF_UTC): WebSearch ran on the
    # provider's side and returned live results (filament r11), so such a solve counts only
    # without a WebSearch call. From WEB_TOOLS_OFF_UTC run_trial.sh removes WebSearch/WebFetch.
    def _used_internet(r):
        hits = cached_hits(JOBS / r["job"] / r["trial"])
        start = r.get("start_utc") or ""
        if r["task"] not in since or start < since[r["task"]]:
            return bool(hits)                          # open-internet era: any lookup
        if start < WEB_TOOLS_OFF_UTC:
            return any(h.startswith("WebSearch") for h in hits)
        return False
    own = [r for r in runs if r["reward"] == 1.0 and _used_internet(r)]
    runs = [r for r in runs if r not in own]
    graded = [r["reward"] for r in runs if r["reward"] is not None]
    ungraded = len(runs) - len(graded)
    tail = (f" (+{ungraded} ungraded)" if ungraded else "") + (
        f" (+{len(cut)} cut at {cut[0]['limit_sec'] // 60} min)" if cut else "") + (
        f" (+{len(rerun_3h)} timed out, re-run at 3 h)" if rerun_3h else "") + (
        f" (+{len(leaked)} used leaked tests)" if leaked else "") + (
        f" (+{len(fault)} test fault, not regradable)" if fault else "") + (
        f" (+{len(leaked_task)} task leaked the answer)" if leaked_task else "") + (
        f" (+{len(stopped)} provider stop)" if stopped else "") + (
        f" (+{len(awaiting)} awaiting audit)" if awaiting else "") + (
        f" ({len(unaudited_solves)} solves counted, not audited)" if unaudited_solves else "") + (
        f" (+{len(untrusted)} audit: untrusted)" if untrusted else "") + (
        f" (+{len(own)} solved using the internet)" if own else "") + (
        f" (+{len(harness)} grader fault)" if harness else "") + (
        f" (+{len(pending)} NEEDS REVIEW)" if pending else "")
    if not graded:
        return f"no graded run{tail}", "none"
    passes = sum(1 for g in graded if g == 1.0)
    scores = ", ".join(f"{g:g}" for g in graded)
    if passes:
        return f"SOLVED {passes}/{len(graded)}{tail}", "solved"
    if len(graded) < 3:                      # pass@3 needs 3 graded failures
        return f"0/{len(graded)} so far, needs 3 [{scores}]{tail}", "open"
    return f"**failed 0/{len(graded)}** [{scores}]{tail}", "failed"


def main():
    rows = []
    for job in sorted(JOBS.iterdir()):
        if not job.is_dir():
            continue
        for trial in sorted(p for p in job.iterdir() if p.is_dir()):   # is_dir: see module doc
            if not (trial / "result.json").is_file() and time.time() - trial.stat().st_mtime < 3 * 3600:
                continue                                                # still running
            r = read_trial(trial)
            if r["task"] and model_key(r["model"]) and (ROOT / "tasks" / r["task"]).is_dir():
                rows.append(r)
    rows.sort(key=lambda r: (r["task"], r["model"], r["start_utc"]))

    OUT.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    with open(OUT / "trials.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join("" if r[c] is None else str(r[c]) for c in cols) + "\n")

    tasks = sorted({r["task"] for r in rows}, key=lambda t: (TRACK_ORDER[track_of(t)], t))
    full, onefail = [], []
    tainted = contaminated()
    decided = reviews()
    excl = excluded_runs()
    for t in tasks:
        cells = {}
        for key, _ in MODELS:
            cells[key] = cell([r for r in rows if r["task"] == t and model_key(r["model"]) == key],
                              task_limit(t), tainted, decided, excl)
        states = {k: s for k, (_, s) in cells.items()}
        if all(s == "failed" for s in states.values()):
            verdict = "**BREAKER candidate**"
        elif "solved" in states.values():
            who = [lab for k, lab in MODELS if states[k] == "solved"]
            verdict = "rejected (" + (" + ".join(who) + " solved" if len(who) < 2 else "both solved") + ")"
        else:
            verdict = "open"
        line = f"| {track_of(t)} | {t} | {cells['deepseek'][0]} | {cells['mimo'][0]} | {verdict} |"
        full.append(line)
        failed = [lab for k, lab in MODELS if states[k] == "failed"]
        if failed and "solved" in states.values():
            onefail.append(f"| {track_of(t)} | {t} | {cells['deepseek'][0]} | {cells['mimo'][0]} | {failed[0]} |")

    hdr = "| Track | Task | DeepSeek | MiMo | {} |\n|---|---|---|---|---|"
    md = [f"_Generated {datetime.now():%Y-%m-%d %H:%M} from {len(rows)} raw trials by common/audit/audit_results.py_", "",
          "## Tasks where one model failed (the other solved)", "", hdr.format("Who failed"), *onefail, "",
          "## All tasks", "", hdr.format("Verdict"), *full, ""]
    notes = ledger_notes()
    if notes:
        # bullet lines, no table pipes: readers of the "All tasks" table (taskstate.py, route.py, status_report.py)
        # skip them
        md += ["## Notes", "", "_Remarks from build/audit/ledger_notes.tsv; they do not change any verdict._", ""]
        for n in notes:
            run = f" (run {n['job']}/{n['trial']})" if n["job"] else ""
            md.append(f"- {n['task']} / {n['model']}{run}: {n['kind']}: {n['note']}".replace("|", "/"))
        md.append("")
    (OUT / "ledger.md").write_text("\n".join(md))
    with open(OUT / "timeout_reruns.tsv", "w") as f:    # input for the 3 h re-run queue
        f.write("task\tmodel\treward\tlimit_sec\tjob\ttrial\n")
        for r in TIMEOUT_RERUNS:
            f.write(f"{r['task']}\t{r['model']}\t{r['reward']}\t{r['limit_sec']}\t{r['job']}\t{r['trial']}\n")
    with open(OUT / "audit_carryover.tsv", "w") as f:  # audits carried over to unchanged-reward regrades
        f.write("job\ttrial\taudited_grading\tcurrent_grading\treward\n")
        for row in sorted(set(CARRYOVER)):
            f.write("\t".join(str(x) for x in row) + "\n")
    with open(OUT / "awaiting_audit.tsv", "w") as f:    # input for common/audit/postmortem.py pending
        f.write("task\tmodel\treward\tjob\ttrial\tgrading\n")
        for r in AWAITING:
            f.write(f"{r['task']}\t{r['model']}\t{r['reward']}\t{r['job']}\t{r['trial']}\t{r['grading']}\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
