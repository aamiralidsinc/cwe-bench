#!/usr/bin/env python3
"""Scale-run queue: one pool for the builds AND trials of one batch (owner design, 2026-10-25).

  nohup python3 -I pipelines/router/scale_queue.py run --batch pipelines/router/out/batches/scale-b1.txt \
      > pipelines/router/out/queue/scale-b1.nohup 2>&1 &
  python3 -I pipelines/router/scale_queue.py status --batch pipelines/router/out/batches/scale-b1.txt

Batch file: one slug per line, priority order (`#` starts a comment). stk-* slugs build with
pipelines/stacking/3-build-gate/run_stack_pipeline.sh; *-s2 / *-s3 slugs with pipelines/sibling/6-build/run_pipeline.sh.
Slugs that are already .sound only get trials.

Scheduling (every 10 s):
  * --slots (60) is the total for builds + trials. Builds go first: while builds are waiting, free slots start
    builds; a freed slot takes the next job at once (no waves).
  * Trials start only once the build queue (running + waiting builds) is below --trial-threshold (20); they then
    fill every slot the builds leave: with 18 builds left, 42 trials can run.
  * A trial job is one (task, model): common/trial/trial.py <slug> --models <m>, early abort at the first solve,
    up to 3 graded runs, agent limit x CWE_AGENT_TIMEOUT_MULT (1.5: the 2 h tasks run at 3 h; a 3 h timeout counts as
    a model fail). New .sound tasks join as they appear; a task with a stale gate fingerprint is skipped.
  * First fill is staggered (15-40 s between starts, so container starts do not starve sshd); later starts 2-8 s.
State: pipelines/router/out/queue/<batch>.state.json (every 30 s); log: <batch>.log; job output: jobs/.
Post-run audits (failing runs only) and fairness are separate steps (pipelines/*/GUIDE.md).
"""
import argparse, json, os, random, subprocess, sys, threading, time
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402

ROOT = str(paths.ROOT)
QDIR = os.path.join(ROOT, "pipelines", "router", "out", "queue")
MODELS = ("deepseek", "mimo")
LOCK = threading.Lock()


def read_batch(p):
    return [s for s in (l.split("#")[0].strip() for l in open(p)) if s]


def bdir(s):
    return os.path.join(ROOT, "build", s)


def is_sound(s):
    return os.path.isfile(os.path.join(bdir(s), ".sound"))


def build_done(s):
    """True when this slug needs no (more) build work: sound, held at the listing check, or stopped."""
    b = bdir(s)
    if is_sound(s) or os.path.isfile(os.path.join(b, ".listing_fail")):
        return True
    for marker in (".unsound", ".gate_error"):
        if os.path.isfile(os.path.join(b, marker)):
            return True
    for logf in ("stack_pipeline.log", "pipeline.log"):
        p = os.path.join(b, logf)
        if os.path.isfile(p):
            t = open(p, errors="replace").read()
            if "STOP:" in t or "BUILD-INCOMPLETE" in t or "stopped/failed" in t:
                return True
    return False


def build_cmd(s):
    if s.startswith("stk-"):
        return ["bash", "pipelines/stacking/3-build-gate/run_stack_pipeline.sh", s]
    return ["bash", "pipelines/sibling/6-build/run_pipeline.sh", "deepseek", s]


def trial_state(s, m):
    r = subprocess.run([sys.executable, "-I", str(paths.TRIAL_STATE), s, m], cwd=ROOT, capture_output=True, text=True)
    state = (r.stdout.split() or ["none"])[0]
    kv = dict(x.split("=", 1) for x in r.stdout.split()[1:] if "=" in x)
    return state, int(kv.get("graded", 0) or 0), int(kv.get("ungraded", 0) or 0)


def fingerprint_ok(s):
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "common/gate/fingerprint.py"), "check", s],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode != 1                   # 0 current, 2 legacy (no fingerprint): allowed; 1 stale: not


def log(name, msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    with LOCK:
        print(line, flush=True)
        with open(os.path.join(QDIR, f"{name}.log"), "a") as f:
            f.write(line + "\n")


def run(a):
    name = Path(a.batch).stem
    slugs = read_batch(a.batch)
    os.makedirs(os.path.join(QDIR, "jobs"), exist_ok=True)
    env = dict(os.environ, CWE_AGENT_TIMEOUT_MULT=str(a.timeout_mult))
    build_wait = [s for s in slugs if not build_done(s) and os.path.isfile(os.path.join(bdir(s), "BUILD-PROMPT.md"))]
    skipped = [s for s in slugs if not build_done(s) and s not in build_wait]
    for s in skipped:
        log(name, f"[skip] {s}: no BUILD-PROMPT.md")
    running, done, launches = {}, [], {}
    stop = threading.Event()

    def kinds():
        return (sum(1 for j in running.values() if j["kind"] == "build"),
                sum(1 for j in running.values() if j["kind"] == "trial"))

    def write_state():
        now = time.time()
        nb, nt = kinds()
        st = dict(batch=name, updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), slots=a.slots,
                  trial_threshold=a.trial_threshold, timeout_mult=a.timeout_mult,
                  builds_running=nb, builds_waiting=len(build_wait), trials_running=nt,
                  running=[dict(job=n, kind=j["kind"], minutes=round((now - j["t0"]) / 60, 1)) for n, j in running.items()],
                  waiting_builds=build_wait, done=done[-200:])
        tmp = os.path.join(QDIR, f"{name}.state.json.tmp")
        json.dump(st, open(tmp, "w"), indent=1)
        os.replace(tmp, os.path.join(QDIR, f"{name}.state.json"))

    def heartbeat():
        while not stop.wait(30):
            with LOCK:
                write_state()

    def start(job_name, kind, cmd):
        out = open(os.path.join(QDIR, "jobs", job_name.replace(":", "__") + f".{kind}.out"), "a")
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, start_new_session=True, env=env)
        running[job_name] = dict(p=p, kind=kind, t0=time.time())
        nb, nt = kinds()
        log(name, f"[start] {kind} {job_name} pid={p.pid} (builds {nb} running/{len(build_wait)} waiting, trials {nt})")

    def trial_candidates():
        out = []
        for s in slugs:
            if not is_sound(s) or not fingerprint_ok(s):
                continue
            for m in MODELS:
                jn = f"{s}:{m}"
                if jn in running or launches.get(jn, 0) >= a.max_launches:
                    continue
                state, graded, ungraded = trial_state(s, m)
                if state in ("solved", "failed", "stuck"):
                    continue
                out.append((jn, [sys.executable, str(paths.TRIAL), s, "--models", m, "--no-verdict",
                                 "--first-run", str(graded + ungraded + 1), "--max-runs", str(max(1, 3 - graded))]))
        return out

    threading.Thread(target=heartbeat, daemon=True).start()
    log(name, f"batch {name}: {len(slugs)} slugs, {len(build_wait)} to build; slots {a.slots}, trials when builds < "
              f"{a.trial_threshold}, trial limit x{a.timeout_mult}")
    filling, last_scan, cands = True, 0, []
    while True:
        for n, j in list(running.items()):
            rc = j["p"].poll()
            if rc is not None:
                del running[n]
                done.append(dict(job=n, kind=j["kind"], rc=rc, minutes=round((time.time() - j["t0"]) / 60, 1)))
                log(name, f"[finish] {j['kind']} {n} rc={rc} {(time.time() - j['t0']) / 60:.0f} min")
        nb, nt = kinds()
        started = False
        if build_wait and nb + nt < a.slots:
            s = build_wait.pop(0)
            start(s, "build", build_cmd(s)); started = True
        elif nb + len(build_wait) < a.trial_threshold and nb + nt < a.slots:
            if time.time() - last_scan > 60 or not cands:
                cands, last_scan = trial_candidates(), time.time()
            if cands:
                jn, cmd = cands.pop(0)
                launches[jn] = launches.get(jn, 0) + 1
                start(jn, "trial", cmd); started = True
        nb, nt = kinds()
        if not started:
            if not running and not build_wait:
                if not trial_candidates():
                    break
            filling = False if nb + nt >= a.slots else filling
            time.sleep(10)
            continue
        with LOCK:
            write_state()
        time.sleep(random.uniform(15, 40) if filling and nb + nt < a.slots else random.uniform(2, 8))
        if nb + nt >= a.slots:
            filling = False
    stop.set()
    with LOCK:
        write_state()
    log(name, f"batch {name}: all builds and trials finished")


def status(a):
    p = os.path.join(QDIR, f"{Path(a.batch).stem}.state.json")
    print(open(p).read() if os.path.isfile(p) else "no state yet")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run", "status"])
    ap.add_argument("--batch", required=True)
    ap.add_argument("--slots", type=int, default=60)
    ap.add_argument("--trial-threshold", type=int, default=20)
    ap.add_argument("--timeout-mult", type=float, default=1.5)
    ap.add_argument("--max-launches", type=int, default=3, help="trial jobs per (task, model) before giving up")
    a = ap.parse_args()
    os.makedirs(QDIR, exist_ok=True)
    {"run": run, "status": status}[a.cmd](a)


if __name__ == "__main__":
    main()
