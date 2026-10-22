#!/usr/bin/env python3
"""Offline re-run queue (2026-10-16): CWE-bench runs agents offline (arXiv 2610.17020), so every
pair left open after build/internet_use.py gets fresh runs in that setting.

    python3 build/queue_offline.py            # run until every listed pair is decided (detach it)
    python3 build/queue_offline.py --status   # print the state

Per (task, model) pair, using only runs that started after the task's switch
(build/audit/offline_since.tsv), numbered from r11:
  - a run scoring 1.0 settles the pair for the queue (the post-run audit still decides);
  - 3 graded non-solves that did NOT time out under 3 h settle it as a candidate failure;
  - a non-solve that timed out under 3 h earns a re-run with 3 h (CWE_AGENT_TIMEOUT_MULT=1.5);
  - an ungraded run is retried (at most 3 times per pair).
A task is started only once it is listed in offline_since.tsv. At most MAX_SLOTS queue runs at once,
at most MAX_HEAVY of them Go/Java/Rust builds, and a new one starts only while the Colima VM has at
least MIN_AVAIL_GIB of memory available (VM: 8 CPUs, 12 GB). Live runs are found by process, so a
restarted queue never doubles a pair.
Every launch and result is logged to build/audit/offline_queue.log.
"""
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
LOG = ROOT / "build/audit/offline_queue.log"
SINCE = ROOT / "build/audit/offline_since.tsv"
MAX_SLOTS, MIN_AVAIL_GIB, MAX_HEAVY, FIRST = 8, 3.5, 5, 11
# Go/Java/Rust builds peaked at 3.5-5.2 GB each (incl. page cache, measured 2026-10-16); the
# Python/PHP/Ruby tasks stayed under 0.4 GB.
HEAVY = {"argo-workflows", "rclone", "rclone-sib", "trigger-dev", "hickory-dns", "russh", "russh-sib",
         "cloudreve", "jackson-databind", "jackson-databind-sib", "jackson-sib7", "async-http-client",
         "actualbudget"}
PAIRS = [  # MAIN first (no open repair), RETRY last (tasks being repaired; capped, lower priority)
    ("argo-workflows", "deepseek"), ("argo-workflows", "mimo"), ("webob", "deepseek"), ("webob", "mimo"),
    ("ruby-saml", "mimo"), ("asyncssh", "deepseek"), ("asyncssh", "mimo"), ("ruby-saml", "deepseek"),
    ("hickory-dns", "deepseek"), ("russh", "deepseek"), ("actualbudget", "deepseek"),
    ("stigmem", "deepseek"), ("russh-sib", "deepseek"),
    ("filament", "deepseek"), ("filament", "mimo"), ("trigger-dev", "deepseek"), ("trigger-dev", "mimo"),
    ("rclone", "deepseek"), ("rclone", "mimo"), ("rclone-sib", "deepseek"), ("rclone-sib", "mimo"),
    # 2026-10-16 test repair: MiMo's only solve failed the new (fairness-reviewed) security test
    ("async-http-client", "mimo"),
]
# User, 2026-10-16: tasks under repair must not block the rest. They run from a separate retry lane:
# at most MAX_RETRY_SLOTS at once while a MAIN pair waits, and only after every ready MAIN pair has been served.
RETRY = {"filament", "trigger-dev", "rclone", "rclone-sib"}
MAX_RETRY_SLOTS = 2


def log(msg):
    line = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


HOLD = ROOT / "build/audit/repair_hold.txt"


def on_hold():
    """Tasks whose tests are being repaired right now: the queue starts no run on them."""
    if not HOLD.exists():
        return set()
    return {l.split("#")[0].strip() for l in HOLD.read_text().splitlines() if l.split("#")[0].strip()}


def offline_since():
    if not SINCE.exists():
        return {}
    return {l.split("\t")[0]: l.split("\t")[1].strip() for l in SINCE.read_text().splitlines()
            if l and not l.startswith(("#", "task\t"))}


# Tasks whose earlier offline runs no longer count (task repaired): their fresh runs start here and
# only runs from here are considered (rclone / rclone-sib proxy contract, 2026-10-16).
RESTART_AT = {"rclone": 21, "rclone-sib": 21}


def runs_of(task, model):
    """Offline-era runs (r11+) of a pair, from the trial folders themselves."""
    out = []
    for job in JOBS.glob(f"{task}-{model}-r*-*"):
        m = re.match(rf"{re.escape(task)}-{model}-r(\d+)-", job.name)
        if not m or int(m.group(1)) < max(FIRST, RESTART_AT.get(task, FIRST)):
            continue
        trials = [p for p in job.iterdir() if p.is_dir()]
        res = None
        if trials:
            try:
                res = json.loads((trials[0] / "result.json").read_text())
            except (OSError, ValueError):
                res = None
        cfg = {}
        try:
            cfg = json.loads((trials[0] / "config.json").read_text()) if trials else {}
        except (OSError, ValueError):
            pass
        limit = int(((cfg.get("agent") or {}).get("env") or {}).get("CWE_AGENT_LIMIT_SEC", 7200))
        if res is None:
            out.append({"n": int(m.group(1)), "state": "running-or-lost", "job": job.name})
            continue
        reward = ((res.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        regs = sorted(trials[0].glob("regrade-*/REGRADE.json"))   # a regrade replaces the grading
        if regs:
            reward = json.loads(regs[-1].read_text()).get("reward", reward)
        exc = (res.get("exception_info") or {}).get("exception_type", "") or ""
        out.append({"n": int(m.group(1)), "state": "done", "reward": reward, "limit": limit,
                    "timed_out": "Timeout" in exc, "job": job.name,
                    "excluded": reward == 1.0 and solve_excluded(trials[0], (res.get("started_at") or "")[:16])})
    return sorted(out, key=lambda r: r["n"])


def live_pairs():
    """(task, model) of every trial.py run alive on this machine (queue-launched or not)."""
    r = subprocess.run(["pgrep", "-fl", "build/trial.py"], capture_output=True, text=True)
    out = set()
    for line in r.stdout.splitlines():
        # only real launches (python3 build/trial.py <task> --models <model>), not shells that mention it
        m = re.search(r"[Pp]ython3? build/trial\.py ([a-z0-9-]+) --models ([a-z]+)\b", line)
        if m:
            out.add((m.group(1), m.group(2)))
    return out


def solve_excluded(trial, start_utc):
    """A 1.0 that must not settle the pair: its post-run audit says untrusted, or it ran before the
    web tools were removed and called WebSearch (provider-side search worked through the API)."""
    sys.path.insert(0, str(ROOT / "build"))
    from internet_use import cached_hits
    import audit_results
    pms = sorted(trial.glob("postmortem-*/POSTMORTEM.json"))
    if pms:
        v = (json.loads(pms[-1].read_text()).get("verdict") or {})
        if v.get("trustworthy") is False:
            return True
    if start_utc < audit_results.WEB_TOOLS_OFF_UTC:
        return any(h.startswith("WebSearch") for h in cached_hits(trial))
    return False


def next_action(task, model, live):
    """None if the pair needs nothing now, else (run number, timeout multiplier or None)."""
    rs = runs_of(task, model)
    if any(r.get("reward") == 1.0 and not r.get("excluded") for r in rs):
        return None
    if (task, model) in live:
        return None                                   # one at a time per pair
    counted = [r for r in rs if r["state"] == "done" and r.get("reward") is not None
               and not (r["timed_out"] and r["limit"] < 10800)]
    if len(counted) >= 3:
        return None
    owed_3h = [r for r in rs if r["state"] == "done" and r.get("reward") is not None
               and r["timed_out"] and r["limit"] < 10800]
    ungraded = [r for r in rs if r["state"] == "done" and r.get("reward") is None]
    if len(ungraded) >= 3:
        return None
    n = max([r["n"] for r in rs], default=FIRST - 1) + 1
    if task in RESTART_AT:                             # task rebuilt: runs restart at a new number
        n = max(n, RESTART_AT[task])
    # a 3 h run is owed for each sub-3 h timeout not yet followed by a 3 h run
    three_h_done = sum(1 for r in rs if r.get("limit", 0) >= 10800)
    return (n, 1.5 if len(owed_3h) > three_h_done else None)


def vm_available_gib():
    r = subprocess.run(["colima", "ssh", "--", "free", "-b"], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("Mem:"):
            return int(line.split()[6]) / 2**30
    return 0.0


def mem_gib():
    r = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}"],
                       capture_output=True, text=True)
    total = 0.0
    for line in r.stdout.splitlines():
        v = line.split("/")[0].strip()
        m = re.match(r"([\d.]+)\s*([KMG]i?B)", v)
        if m:
            total += float(m.group(1)) * {"KiB": 1 / 1048576, "MiB": 1 / 1024, "GiB": 1, "kB": 1e-6, "MB": 1e-3, "GB": 1}.get(m.group(2), 0)
    return total


class _Adopted:
    """A run started before this queue process; 'finished' once its trial.py exits."""
    def __init__(self, task, model):
        self.task, self.model, self.returncode = task, model, None

    def poll(self):
        if (self.task, self.model) in live_pairs():
            return None
        self.returncode = 0
        return 0


def main():
    procs = {}                                          # job-name prefix -> Popen
    log(f"queue start: {len(PAIRS)} pairs, max {MAX_SLOTS} slots ({MAX_HEAVY} heavy), VM available >= {MIN_AVAIL_GIB} GiB")
    # adopt runs already alive (e.g. after a restart) so they count toward slots
    for task, model in live_pairs():
        procs[f"{task}-{model}-adopted-"] = _Adopted(task, model)
    while True:
        for k, p in list(procs.items()):
            if p.poll() is not None:
                log(f"finished {k} rc={p.returncode}")
                procs.pop(k)
        live = live_pairs()
        since = offline_since()
        pending = 0
        # the retry cap only protects MAIN pairs; once none is waiting, retry pairs may use every slot
        main_waiting = any(t in since and t not in RETRY and next_action(t, m, live) is not None
                           for t, m in PAIRS)
        for task, model in PAIRS:
            if task not in since:
                pending += 1
                continue
            act = next_action(task, model, live)
            if act is None:
                continue
            pending += 1
            if task in on_hold():
                continue
            if any(k.startswith(f"{task}-{model}-") for k in procs):
                continue
            heavy_now = sum(1 for k in procs if procs[k].task in HEAVY)
            if len(procs) >= MAX_SLOTS or vm_available_gib() < MIN_AVAIL_GIB:
                break
            if task in HEAVY and heavy_now >= MAX_HEAVY:
                continue
            if task in RETRY and main_waiting and sum(1 for k in procs if procs[k].task in RETRY) >= MAX_RETRY_SLOTS:
                continue
            n, mult = act
            # Kept (stopped) trials leave their compose networks behind; Docker's ~31 address
            # pools ran out on 2026-10-16. Remove networks no container uses before each launch.
            subprocess.run(["docker", "network", "prune", "-f"], capture_output=True)
            env = dict(**__import__("os").environ)
            if mult:
                env["CWE_AGENT_TIMEOUT_MULT"] = str(mult)
            logf = open(ROOT / "build" / task / f"offline-{model}-r{n}.log", "w")
            p = subprocess.Popen(["caffeinate", "-i", "python3", "build/trial.py", task, "--models", model,
                                  "--max-runs", "1", "--first-run", str(n), "--full", "--no-verdict"],
                                 cwd=ROOT, env=env, stdout=logf, stderr=logf, stdin=subprocess.DEVNULL)
            p.task, p.model = task, model
            procs[f"{task}-{model}-r{n}-"] = p
            log(f"launched {task}/{model} r{n}" + (" with 3 h limit" if mult else ""))
            time.sleep(30)                              # stagger image builds
        if not procs and pending == 0:
            log("queue done: every listed pair is settled for the queue")
            return
        time.sleep(60)


def status():
    since = offline_since()
    for task, model in PAIRS:
        rs = runs_of(task, model)
        print(f"{task:22} {model:8} {'ready' if task in since else 'not offline yet':16} "
              + " ".join(f"r{r['n']}:{r.get('reward', r['state'])}{'(TO)' if r.get('timed_out') else ''}{'(excluded)' if r.get('excluded') else ''}" for r in rs))


if __name__ == "__main__":
    status() if "--status" in sys.argv else main()
