#!/usr/bin/env python3
"""Stacking queue (new; the sibling pipeline's queue, lanes and queue.json are not used or touched).

A pool of N slots (default 16): whenever a job finishes, the next one starts. Two phases, never mixed:
  build  : per stk- slug, `bash pipelines/stacking/3-build-gate/run_stack_pipeline.sh SLUG` (build, check, gates, blind fix,
           .sound markers). Slugs come from --slugs-file (one per line, in priority order).
  trial  : per (slug, model), `python3 common/trial/trial.py SLUG --models MODEL --no-verdict` (stop at the first
           solve; 3 runs only while the model keeps failing). Only slugs with build/<slug>/.sound.
           Stacked slugs first, their -control tasks last (lowest priority). Pairs already decided
           (common/trial/trial_state.py: solved, failed, stuck) are skipped; incomplete ones resume.
The trial phase refuses to start while any stacking build is running: builds take the CPU, and
CPU-starved trials hit the timeout (user rule, 2026-10-22). `all` runs build, then trial.

Starts are staggered (random 15-40 s apart while the pool fills) so a burst of container starts does
not starve sshd. Progress: pipelines/stacking/out/queue/<phase>.log (one line per start/finish) and
pipelines/stacking/out/queue/state.json (rewritten every 30 s: running jobs with elapsed time, waiting, done).

  nohup python3 -I pipelines/stacking/6-trial/stk_queue.py all --slugs-file pipelines/stacking/out/batch1.txt > pipelines/stacking/out/queue/nohup.log 2>&1 &
  python3 -I pipelines/stacking/6-trial/stk_queue.py status
"""
import argparse, json, os, random, subprocess, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
QDIR = os.path.join(str(paths.STACKING_OUT), "queue")
STATE = os.path.join(QDIR, "state.json")
MODELS = ("deepseek", "mimo")
LOCK = threading.Lock()


def log(phase, msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    with LOCK:
        print(line, flush=True)
        with open(os.path.join(QDIR, f"{phase}.log"), "a") as f:
            f.write(line + "\n")


def builds_running():
    r = subprocess.run(["pgrep", "-f", "pipelines/stacking/3-build-gate/run_stack_pipeline.sh"], capture_output=True, text=True)
    return [p for p in r.stdout.split() if p and int(p) != os.getpid()]


def build_jobs(slugs, retry):
    jobs = []
    for s in slugs:
        b = os.path.join(ROOT, "build", s)
        if os.path.isfile(os.path.join(b, ".sound")) or os.path.isfile(os.path.join(b, ".listing_fail")):
            continue                     # .listing_fail: built and gated; waits for an instruction rewrite
        plog = os.path.join(b, "stack_pipeline.log")
        if not retry and os.path.isfile(plog) and "STOP:" in open(plog, errors="replace").read():
            continue
        if not os.path.isfile(os.path.join(b, "BUILD-PROMPT.md")):
            print(f"[skip] {s}: no build/{s}/BUILD-PROMPT.md (run build_prepare_stack.py first)")
            continue
        jobs.append(dict(name=s, cmd=["bash", "pipelines/stacking/3-build-gate/run_stack_pipeline.sh", s]))
    return jobs


def trial_jobs():
    sound = sorted(d for d in os.listdir(os.path.join(ROOT, "build"))
                   if d.startswith("stk-") and os.path.isfile(os.path.join(ROOT, "build", d, ".sound")))
    order = [s for s in sound if not s.endswith("-control")] + [s for s in sound if s.endswith("-control")]
    jobs = []
    for s in order:
        for m in MODELS:
            r = subprocess.run([sys.executable, "-I", str(paths.TRIAL_STATE), s, m], cwd=ROOT,
                               capture_output=True, text=True)
            state = (r.stdout.split() or ["none"])[0]
            if state in ("solved", "failed", "stuck"):
                continue
            kv = dict(x.split("=", 1) for x in r.stdout.split()[1:] if "=" in x)
            graded = int(kv.get("graded", 0) or 0)
            tried = graded + int(kv.get("ungraded", 0) or 0)
            jobs.append(dict(name=f"{s}:{m}", cmd=[sys.executable, str(paths.TRIAL), s, "--models", m, "--no-verdict",
                                                   "--first-run", str(tried + 1), "--max-runs", str(max(1, 3 - graded))]))
    return jobs


def run_pool(phase, jobs, slots):
    if not jobs:
        log(phase, f"{phase}: nothing to run")
        return
    waiting, running, done = list(jobs), {}, []
    stop = threading.Event()

    def write_state():
        now = time.time()
        st = dict(phase=phase, updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), slots=slots,
                  running=[dict(job=n, minutes=round((now - t0) / 60, 1)) for n, (_, t0) in running.items()],
                  waiting=[j["name"] for j in waiting], done=done)
        tmp = STATE + ".tmp"
        json.dump(st, open(tmp, "w"), indent=1)
        os.replace(tmp, STATE)

    def heartbeat():
        while not stop.wait(30):
            with LOCK:
                write_state()

    threading.Thread(target=heartbeat, daemon=True).start()
    log(phase, f"{phase}: {len(jobs)} jobs, {slots} slots")
    filling = True
    while waiting or running:
        for n, (p, t0) in list(running.items()):
            rc = p.poll()
            if rc is not None:
                del running[n]
                done.append(dict(job=n, rc=rc, minutes=round((time.time() - t0) / 60, 1)))
                log(phase, f"[finish] {n} rc={rc} {(time.time() - t0) / 60:.0f} min")
        while waiting and len(running) < slots:
            j = waiting.pop(0)
            out = open(os.path.join(QDIR, "jobs", j["name"].replace(":", "__") + f".{phase}.out"), "a")
            p = subprocess.Popen(j["cmd"], cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
            running[j["name"]] = (p, time.time())
            log(phase, f"[start] {j['name']} pid={p.pid} ({len(running)} running, {len(waiting)} waiting)")
            with LOCK:
                write_state()
            if filling and waiting and len(running) < slots:
                time.sleep(random.uniform(15, 40))
            else:
                time.sleep(random.uniform(2, 8))
        if len(running) >= slots or not waiting:
            filling = False
        time.sleep(10)
    stop.set()
    with LOCK:
        write_state()
    log(phase, f"{phase}: all {len(jobs)} jobs finished")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["build", "trial", "all", "status"])
    ap.add_argument("--slugs-file", help="stk- slugs, one per line, in priority order (build phase)")
    ap.add_argument("--slots", type=int, default=16)
    ap.add_argument("--retry-stopped", action="store_true", help="re-run builds whose log has a STOP line")
    ap.add_argument("--dry-run", action="store_true", help="list the jobs and exit")
    a = ap.parse_args()
    os.makedirs(os.path.join(QDIR, "jobs"), exist_ok=True)
    if a.phase == "status":
        print(open(STATE).read() if os.path.isfile(STATE) else "no state yet")
        return
    if a.phase in ("build", "all"):
        if not a.slugs_file:
            sys.exit("--slugs-file is required for the build phase")
        slugs = [l.split("#")[0].strip() for l in open(a.slugs_file)]
        slugs = [s for s in slugs if s]
        bad = [s for s in slugs if not s.startswith("stk-")]
        if bad:
            sys.exit(f"not stk- slugs: {bad}")
        jobs = build_jobs(slugs, a.retry_stopped)
        if a.dry_run:
            print("\n".join(" ".join(j["cmd"]) for j in jobs) or "no build jobs")
        else:
            run_pool("build", jobs, a.slots)
    if a.phase in ("trial", "all"):
        if a.dry_run and a.phase == "all":
            print("(trial jobs are listed once the build phase has produced .sound markers)")
            return
        busy = builds_running()
        if busy:
            sys.exit(f"stacking builds still running (pids {' '.join(busy)}); trials wait for the build phase")
        jobs = trial_jobs()
        if a.dry_run:
            print("\n".join(" ".join(j["cmd"]) for j in jobs) or "no trial jobs")
        else:
            run_pool("trial", jobs, a.slots)


if __name__ == "__main__":
    main()
