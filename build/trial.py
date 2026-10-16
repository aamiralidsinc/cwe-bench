#!/usr/bin/env python3
"""Trial runner for one built task. Two modes:

    trial.py <slug>                 production: sequential EARLY-ABORT
                                    (deepseek then mimo; reject on first solve)
    trial.py <slug> --full          experimental: run ALL runs on BOTH models,
                                    no early-abort, record per-model pass@3 and
                                    per-run detail (reward, finish reason, tokens,
                                    wall time) to build/<slug>/trial_detail.json

Verdict (both modes): a task is accepted (a breaker) only if NO run reaches
reward 1.0 on EITHER model. --full is for subjective+objective analysis of how
each model behaves and to find tasks where BOTH fail; early-abort is for cheap
production screening once we trust the signal.

    --models deepseek,mimo   which models, in order (default both)
    --max-runs 3             runs per model
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "harness" / "run_trial.sh"
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"


def extract_detail(trial_dir):
    """Pull finish reason + token usage from the agent's result event."""
    f = trial_dir / "agent" / "claude-code.txt"
    out = {}
    if f.is_file():
        for line in f.read_text(errors="replace").splitlines():
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("type") == "result":
                u = e.get("usage", {})
                out = {"finish": e.get("subtype") or e.get("terminal_reason"),
                       "is_error": e.get("is_error"),
                       "num_turns": e.get("num_turns"),
                       "in_tokens": u.get("input_tokens"),
                       "out_tokens": u.get("output_tokens"),
                       "duration_s": round(e.get("duration_ms", 0) / 1000)}
    return out


KEPT = ROOT / "build" / "audit" / "kept_containers.tsv"


def remove_container(container):
    """Delete a kept container and the image Harbor built for it, plus its netguard sidecar
    (never the shared cwe-netguard image)."""
    image = subprocess.run(["docker", "inspect", "-f", "{{.Config.Image}}", container],
                           capture_output=True, text=True).stdout.strip()
    subprocess.run(["docker", "rm", "-f", container], capture_output=True)
    subprocess.run(["docker", "rm", "-f", container.replace("-main-1", "-netguard-1")], capture_output=True)
    if image:
        subprocess.run(["docker", "rmi", image], capture_output=True)   # fails harmlessly if shared


def save_netguard_log(trial, container):
    """Copy the netguard sidecar's decision log (every allowed/refused request to a guarded host)
    into <trial>/netguard.log, for the post-run audit. No-op for tasks without netguard."""
    side = container.replace("-main-1", "-netguard-1")
    r = subprocess.run(["docker", "logs", side], capture_output=True, text=True)
    if r.returncode == 0:
        (trial / "netguard.log").write_text(r.stdout + r.stderr)
        blocked = sum(1 for l in r.stdout.splitlines() if '"netguard": "block"' in l)
        return f"netguard: {blocked} refused request(s) logged"
    return "netguard: none (task has no sidecar)"


def keep_or_release(trial, task, model, job, reward):
    """Save the agent's final code (always), then delete the container of a clean solve
    and keep every other one (failed, ungraded, needs review) for review/re-grading."""
    from harvest_code import harvest
    from review_flags import setup_flags
    container = f"{trial.name.lower()}__env-main-1"
    print(f"[trial] {save_netguard_log(trial, container)}", flush=True)
    code = harvest(trial, "after-run", container)
    # Evidence for the independent post-run audit (build/postmortem.py). The run counts toward
    # no verdict until an auditor sub-agent has judged it and `postmortem.py record` was run.
    if reward is not None:
        try:
            from postmortem import prepare
            print(f"[trial] post-run audit evidence: {prepare(trial)}", flush=True)
        except Exception as e:                       # never lose a run over the audit step
            print(f"[trial] post-run audit prepare failed: {e}", flush=True)
    flags = setup_flags(trial) if reward not in (None, 1.0) else []
    if reward == 1.0:
        remove_container(container)
        return {"final_code": code.get("files_changed", code), "container": "removed (clean solve)"}
    reason = "ungraded" if reward is None else ("needs review: " + "; ".join(flags) if flags else f"failed ({reward})")
    new = not KEPT.exists()
    with open(KEPT, "a") as f:
        if new:
            f.write("utc\taction\ttask\tmodel\tjob\ttrial\tcontainer\treason\n")
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\tkept\t{task}\t{model}\t{job}\t"
                f"{trial.name}\t{container}\t{reason}\n")
    return {"final_code": code.get("files_changed", code), "container": f"kept: {container} ({reason})"}


RUN_SEQ = [0]  # process-wide monotonic counter so run order is unambiguous


def one_run(model, task_dir, idx):
    RUN_SEQ[0] += 1
    # Name carries a human timestamp + a monotonic counter so the LATEST run is
    # obvious and never confused with an older job dir from a previous era.
    name = f"{task_dir.name}-{model}-r{idx}-{time.strftime('%Y%m%d-%H%M%S')}-n{RUN_SEQ[0]:03d}"
    t0 = time.time()
    proc = subprocess.run(["bash", str(RUN), model, str(task_dir), "1",
                           "--job-name", name, "-n", "1", "-y"], capture_output=True, text=True)
    wall = round(time.time() - t0)
    rec = {"job": name, "wall_s": wall, "harbor_rc": proc.returncode, "reward": None, "cause": None}
    # is_dir() is required: on Python <3.11, glob("*/") also returns FILES, and sorting put
    # config.json ahead of any task named after "c" — the reader then graded a file as the trial.
    job_dir = JOBS / name           # absent when the run never started (e.g. held, harbor error)
    trials = sorted(p for p in job_dir.iterdir() if p.is_dir()) if job_dir.is_dir() else []
    if not trials:
        rec["cause"] = "no-trial-dir (harbor never started a trial)"
        return rec
    trial = trials[0]
    res = trial / "result.json"
    agent_log = trial / "agent" / "claude-code.txt"
    has_result_event = agent_log.is_file() and '"type":"result"' in agent_log.read_text(errors="replace")
    if res.is_file():
        r = json.loads(res.read_text())
        # A run cut at the agent timeout is still GRADED (grade-at-timeout); keep its reward.
        rec["reward"] = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        if r.get("exception_info"):
            rec["cause"] = "exception:" + str(r["exception_info"].get("exception_type", "?")) + (
                " (graded)" if rec["reward"] is not None else " (not graded)")
    else:
        # No trial-level result.json. In shared mode the verifier still runs IN the
        # agent container and writes verifier/reward.json — that is the AUTHORITATIVE
        # graded score (incl. grade-at-timeout). Read it before calling anything a non-result.
        vr = trial / "verifier" / "reward.json"
        if vr.is_file():
            try:
                rec["reward"] = json.loads(vr.read_text()).get("reward")
                rec["cause"] = "graded-from-verifier/reward.json (no trial-level result.json; e.g. graded at timeout)"
            except Exception:
                rec["cause"] = "verifier/reward.json unreadable"
        elif has_result_event:
            rec["cause"] = "result-event-but-no-verifier-reward (grader did not run)"
        elif wall < 1700:
            rec["cause"] = f"session-ended-early-no-result at {wall}s (cut/dropped/gave-up; NOT a timeout)"
        else:
            rec["cause"] = f"hit-agent-timeout (~{wall}s) and verifier produced no reward"
    rec.update(extract_detail(trial))
    rec["trial_dir"] = str(trial)
    rec.update(keep_or_release(trial, task_dir.name, model, name, rec.get("reward")))
    # Append an ordered pointer so the LATEST run for this task/model is
    # unambiguous — read THIS, never a glob of all historical job dirs.
    ptr = ROOT / "build" / task_dir.name / f"runs_{model}.log"
    ptr.parent.mkdir(parents=True, exist_ok=True)
    with open(ptr, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\tn{RUN_SEQ[0]:03d}\treward={rec['reward']}\t"
                f"cause={rec.get('cause')}\t{name}\n")
    return rec


def set_verdict(slug, status, result):
    q = ROOT / "build" / "queue.json"
    d = json.loads(q.read_text())
    for item in d["queue"]:
        if item["slug"] == slug:
            item["status"] = status
            item["result"] = result
    q.write_text(json.dumps(d, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--full", action="store_true", help="run all runs on both models, no early-abort")
    ap.add_argument("--max-runs", type=int, default=3)
    ap.add_argument("--first-run", type=int, default=1,
                    help="number of the first run, so extra runs are labelled r4, r5... not r1 again")
    ap.add_argument("--models", default="deepseek,mimo")
    ap.add_argument("--no-verdict", action="store_true",
                    help="record detail only; do not change the queue verdict (for supplementary per-model runs)")
    args = ap.parse_args()
    task_dir = ROOT / "tasks" / args.slug
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    # A hold file blocks new launches for that task/model (e.g. it was already started
    # by hand while an orchestrator still had it queued). Delete the file to release.
    held = [m for m in models if (ROOT / "build" / args.slug / f"hold_{m}").exists()]
    if held:
        print(f"[trial] {args.slug}: held for {','.join(held)} "
              f"(build/{args.slug}/hold_<model> exists); not starting.")
        return 0
    # single-model runs write a model-suffixed detail file so parallel per-model
    # jobs for the same task do not clobber each other
    detail_path = ROOT / "build" / args.slug / (
        "trial_detail.json" if len(models) > 1 else f"trial_detail_{models[0]}.json")
    detail = {"slug": args.slug, "mode": "full" if args.full else "early-abort", "runs": []}
    per_model = {m: {"pass": 0, "fail": 0, "error": 0} for m in models}

    for model in models:
        for i in range(args.first_run, args.first_run + args.max_runs):
            rec = one_run(model, task_dir, i)
            rec["model"], rec["run"] = model, i
            detail["runs"].append(rec)
            reward = rec.get("reward")
            tail = f"cause={rec.get('cause')}" if reward is None else f"finish={rec.get('finish')} out_tok={rec.get('out_tokens')}"
            print(f"{model} run {i}: reward={reward} {tail} wall={rec.get('wall_s')}s rc={rec.get('harbor_rc')}", flush=True)
            if reward is None:
                per_model[model]["error"] += 1
                # retry an infra/truncation error once; a truncated run proves nothing
                rec2 = one_run(model, task_dir, i)
                rec2["model"], rec2["run"], rec2["retry"] = model, i, True
                detail["runs"].append(rec2)
                reward = rec2.get("reward")
                print(f"{model} run {i} retry: reward={reward} finish={rec2.get('finish')}", flush=True)
            if reward == 1.0:
                per_model[model]["pass"] += 1
            elif reward is not None:
                per_model[model]["fail"] += 1
            if reward is None and i == args.first_run:
                detail["verdict"] = f"{model} INFEASIBLE: run 1 produced no result twice (session/verify did not complete)"
                detail["per_model"] = per_model
                detail_path.write_text(json.dumps(detail, indent=1))
                print(f"[trial] {args.slug}: {model} INFEASIBLE (no result on run 1 x2); stopping this model.")
                break
            if reward == 1.0 and not args.full:
                detail["verdict"] = f"{model} solved run {i} (early-exit)"
                detail["per_model"] = per_model
                detail_path.write_text(json.dumps(detail, indent=1))
                if not args.no_verdict:
                    set_verdict(args.slug, "rejected", "REJECTED: " + detail["verdict"])
                print(f"[trial] {args.slug}: {model} solved run {i}; stopping ({'verdict kept' if args.no_verdict else 'REJECTED'}).")
                return 0

    # per-model outcome: solved (>=1 pass), failed (>=1 real completed non-solve),
    # or infeasible (only errors/None — run never produced a usable result).
    outcomes = {}
    for m in models:
        pm = per_model[m]
        outcomes[m] = "solved" if pm["pass"] > 0 else ("failed" if pm["fail"] > 0 else "infeasible")
    summary = "; ".join(f"{m}: {outcomes[m]} ({per_model[m]['pass']}p/{per_model[m]['fail']}f/{per_model[m]['error']}e)"
                        for m in models)
    if any(o == "solved" for o in outcomes.values()):
        status = "rejected"
    elif all(o == "failed" for o in outcomes.values()):
        # BREAKER only when BOTH models were run and failed; a single-model run can
        # only say that model failed these runs (per-model verdicts: audit_results.py).
        status = "accepted" if len(models) > 1 else "model-failed-these-runs"
    else:
        status = "infeasible"    # at least one model could not complete a run
    detail["verdict"] = f"{status.upper()}: {summary}"
    detail["per_model"] = per_model
    detail_path.write_text(json.dumps(detail, indent=1))
    if not args.no_verdict:
        set_verdict(args.slug, status, detail["verdict"])
    print(f"[trial] {args.slug}: {detail['verdict']}" + ("  (verdict not written)" if args.no_verdict else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
