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
import os
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = paths.ROOT
RUN = paths.RUN_TRIAL
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
sys.path.insert(0, str(paths.UTIL))
import evidence as ev  # noqa: E402  (full error evidence: common/util/evidence.py)
import diskguard  # noqa: E402  (disk-aware admission: common/util/diskguard.py)
# harvest_code, review_flags and postmortem (imported lazily below) live in common/audit/. Before the
# 2026-10-25 reorganisation they sat next to this file in build/, where the script directory made them importable.
sys.path.insert(0, str(paths.AUDIT_TOOLS))


def run_evidence(task, name, cause, trial=None, proc=None, extra=None):
    """Write the full evidence of a run that produced no usable result; return the file path.
    The runs log and trial_detail carry one line plus this path (never just a class name)."""
    try:
        return ev.write(ROOT / "build" / task / "evidence", f"trial-{name}", f"trial run {name}",
                        "run-error", cause, {**ev.collect(trial, proc), **(extra or {})})
    except Exception as e:                     # never lose the run record over its evidence
        print(f"[trial] could not write evidence ({type(e).__name__}: {e})", flush=True)
        return None


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
    # Evidence for the independent post-run audit (common/audit/postmortem.py). The run counts toward
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
    # Free Docker address pools left by kept containers. Skipped by default now that the daemon
    # has a 4096-network pool (172.16/12 /24); a concurrent prune would delete a sibling trial's
    # network. Set CWE_NET_PRUNE=1 to restore the old behaviour.
    if os.environ.get("CWE_NET_PRUNE") == "1":
        # until=10m keeps a fresh sibling compose network (seconds old) from being
        # pruned mid-up; fixes the concurrent network-not-found race under parallelism.
        subprocess.run(["docker", "network", "prune", "-f", "--filter", "until=10m"], capture_output=True)
    proc = subprocess.run(["bash", str(RUN), model, str(task_dir), "1",
                           "--job-name", name, "-n", "1", "-y"], capture_output=True, text=True)
    wall = round(time.time() - t0)
    rec = {"job": name, "wall_s": wall, "harbor_rc": proc.returncode, "reward": None, "cause": None}
    if proc.returncode == 3 and (ROOT / "build" / task_dir.name / f"hold_{model}").exists():
        # run_trial.sh refused: a hold file appeared mid-loop. Not a run, not an infra error.
        rec["cause"], rec["held"] = "held (build/<task>/hold_<model> exists)", True
        return rec
    # is_dir() is required: on Python <3.11, glob("*/") also returns FILES, and sorting put
    # config.json ahead of any task named after "c" — the reader then graded a file as the trial.
    job_dir = JOBS / name           # absent when the run never started (e.g. held, harbor error)
    trials = sorted(p for p in job_dir.iterdir() if p.is_dir()) if job_dir.is_dir() else []
    if not trials:
        err = proc.stderr.strip() or proc.stdout.strip()
        rec["harbor_stdout_tail"], rec["harbor_stderr_tail"] = proc.stdout[-20000:], proc.stderr[-20000:]
        cause = f"no-trial-dir (harbor never started a trial; exit {proc.returncode}): {ev.one_line(err, 300)}"
        rec["evidence_file"] = run_evidence(task_dir.name, name, cause, proc=proc, extra={"job_dir": str(job_dir)})
        rec["cause"] = cause + f" [full: {rec['evidence_file']}]"
        return rec
    trial = trials[0]
    res = trial / "result.json"
    agent_log = trial / "agent" / "claude-code.txt"
    has_result_event = agent_log.is_file() and '"type":"result"' in agent_log.read_text(errors="replace")
    if res.is_file():
        try:
            r = json.loads(res.read_text())
        except (ValueError, OSError) as e:
            r = {"exception_info": {"exception_type": "UnreadableResultJson",
                                    "exception_message": f"{type(e).__name__}: {e}"}}
        # A run cut at the agent timeout is still GRADED (grade-at-timeout); keep its reward.
        rec["reward"] = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        if r.get("exception_info"):
            exc = ev.harbor_exception(trial) or r["exception_info"]
            rec["exception"] = exc          # class + FULL message + FULL traceback, in trial_detail
            rec["cause"] = (f"exception:{exc.get('type') or exc.get('exception_type')}: "
                            f"{ev.one_line(exc.get('message') or exc.get('exception_message'), 300)}"
                            + (" (graded)" if rec["reward"] is not None else " (not graded)"))
    else:
        # No trial-level result.json. In shared mode the verifier still runs IN the
        # agent container and writes verifier/reward.json — that is the AUTHORITATIVE
        # graded score (incl. grade-at-timeout). Read it before calling anything a non-result.
        vr = trial / "verifier" / "reward.json"
        if vr.is_file():
            try:
                rec["reward"] = json.loads(vr.read_text()).get("reward")
                rec["cause"] = "graded-from-verifier/reward.json (no trial-level result.json; e.g. graded at timeout)"
            except Exception as e:
                rec["cause"] = f"verifier/reward.json unreadable ({type(e).__name__}: {e})"
        elif has_result_event:
            rec["cause"] = "result-event-but-no-verifier-reward (grader did not run)"
        elif wall < 1700:
            rec["cause"] = f"session-ended-early-no-result at {wall}s (cut/dropped/gave-up; NOT a timeout)"
        else:
            rec["cause"] = f"hit-agent-timeout (~{wall}s) and verifier produced no reward"
    # A session cut short (API/network error, rate limit, killed with exit 137, crashed without a
    # result event) is not a result even if the verifier graded the unfinished code (2026-10-16
    # 13:51 UTC DNS outage cut 5 runs at once). A genuine agent timeout is NOT a cut: it counts.
    # Same rule as review_flags.agent_cut, which audit_results.py applies to every past run.
    from review_flags import agent_cut
    cut = agent_cut(trial) if rec["reward"] is not None and rec["reward"] != 1.0 else None
    if cut:
        rec["graded_reward_ignored"] = rec["reward"]
        rec["reward"] = None
        rec["agent_cut"] = cut              # full reason
        rec["cause"] = f"agent-cut ({ev.one_line(cut, 300)}); not a result, retried"
    rec.update(extract_detail(trial))
    rec["trial_dir"] = str(trial)
    # Any run without a usable result, or with an exception, gets a full evidence file.
    if rec["reward"] is None or rec.get("exception"):
        rec["evidence_file"] = run_evidence(task_dir.name, name, rec["cause"], trial=trial, proc=proc)
        rec["cause"] = f"{rec['cause']} [full: {rec['evidence_file']}]"
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
    per_model = {m: {"pass": 0, "fail": 0, "error": 0, "held": False} for m in models}

    for model in models:
        for i in range(args.first_run, args.first_run + args.max_runs):
            # Disk-aware admission (2026-10-27): each run builds its own images; wait below the disk floor.
            diskguard.wait("DISK_MIN_FREE_GB_TRIAL", f"{args.slug} {model} run {i}")
            rec = one_run(model, task_dir, i)
            rec["model"], rec["run"] = model, i
            detail["runs"].append(rec)
            if rec.get("held"):
                per_model[model]["held"] = True
                print(f"[trial] {args.slug}: {model} held mid-loop; stopping this model (no verdict).", flush=True)
                break
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
                if reward is None:
                    per_model[model]["error"] += 1
            if reward == 1.0:
                per_model[model]["pass"] += 1
            elif reward is not None:
                per_model[model]["fail"] += 1
            if reward is None and i == args.first_run:
                # Infrastructure, not the model: two runs in a row produced no result. Stop spending
                # on this model now, but leave it INCOMPLETE (re-queued), never a final verdict.
                # (Until 2026-10-20 this was "INFEASIBLE" and the launcher never re-trialed it:
                # flowise-ds / hubuum-client-rust-ds after one compose burst.)
                print(f"[trial] {args.slug}: {model} INCOMPLETE (no result on run 1 x2: infrastructure); "
                      f"stopping this model, re-trial later.", flush=True)
                break
            if reward == 1.0 and not args.full:
                detail["verdict"] = f"{model} solved run {i} (early-exit)"
                detail["per_model"] = per_model
                detail_path.write_text(json.dumps(detail, indent=1))
                if not args.no_verdict:
                    set_verdict(args.slug, "rejected", "REJECTED: " + detail["verdict"])
                print(f"[trial] {args.slug}: {model} solved run {i}; stopping ({'verdict kept' if args.no_verdict else 'REJECTED'}).")
                return 0

    # per-model outcome: solved (>=1 pass); failed (EVERY one of the max-runs runs graded, none a
    # solve); otherwise incomplete (errors/cuts left fewer graded runs) or held. Until 2026-10-20
    # one graded fail plus two dropped errors read as "failed" and the task as ACCEPTED.
    outcomes = {}
    for m in models:
        pm = per_model[m]
        outcomes[m] = ("solved" if pm["pass"] > 0 else "failed" if pm["fail"] >= args.max_runs
                       else "held" if pm["held"] else "incomplete")
    summary = "; ".join(f"{m}: {outcomes[m]} ({per_model[m]['pass']}p/{per_model[m]['fail']}f/{per_model[m]['error']}e)"
                        for m in models)
    if any(o == "solved" for o in outcomes.values()):
        status = "rejected"
    elif all(o == "failed" for o in outcomes.values()):
        # BREAKER only when BOTH models were run and failed; a single-model run can
        # only say that model failed these runs (per-model verdicts: audit_results.py).
        status = "accepted" if len(models) > 1 else "model-failed-these-runs"
    else:
        status = "incomplete"    # a model has fewer graded runs than needed: re-trial, no verdict
    detail["verdict"] = f"{status.upper()}: {summary}"
    detail["per_model"] = per_model
    detail_path.write_text(json.dumps(detail, indent=1))
    if not args.no_verdict:
        set_verdict(args.slug, status, detail["verdict"])
    print(f"[trial] {args.slug}: {detail['verdict']}" + ("  (verdict not written)" if args.no_verdict else ""))
    # Exit 2 tells launchers the trial is not finished (re-queue it); 0 = a complete result.
    return 2 if status == "incomplete" else 0


if __name__ == "__main__":
    sys.exit(main())
